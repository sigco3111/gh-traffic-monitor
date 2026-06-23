"""
GitHub API 클라이언트 — stdlib only (urllib).

- gh CLI가 이미 인증되어 있으면 token 자동 추출
- repo 트래픽 / 메타데이터 / 포크 / 별 수집
- rate limit 자동 감지 + 예외 변환
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from .exceptions import AuthError, GitHubAPIError, RateLimitError
from .models import TrafficRecord, utc_today_date

GITHUB_API_BASE = "https://api.github.com"


def get_gh_token() -> str:
    """
    gh CLI 인증 토큰 추출.
    macOS keyring 또는 env var (GH_TOKEN / GITHUB_TOKEN) 지원.
    """
    # 1순위: env var
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(var, "").strip()
        if token:
            return token

    # 2순위: gh auth token (keyring)
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    raise AuthError("GitHub 토큰을 찾을 수 없습니다. `gh auth login` 또는 GH_TOKEN 환경 변수 설정 필요.")


def _api_get(path: str, token: str, params: dict | None = None) -> dict:
    """GitHub API GET 요청 — JSON 응답."""
    url = f"{GITHUB_API_BASE}{path}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"

    req = urlrequest.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gh-traffic-monitor",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 403:
            # rate limit 체크
            reset = e.headers.get("X-RateLimit-Reset", "")
            reset_iso = ""
            if reset:
                try:
                    reset_iso = datetime.fromtimestamp(int(reset), tz=timezone.utc).isoformat()
                except (ValueError, OSError):
                    pass
            raise RateLimitError(reset_iso) from e
        if e.code == 401:
            raise AuthError(f"인증 실패 (HTTP 401): {path}") from e
        raise GitHubAPIError(f"HTTP {e.code}: {path}") from e
    except URLError as e:
        raise GitHubAPIError(f"네트워크 오류: {e}") from e


def list_public_repos(owner: str, token: str, per_page: int = 100) -> list[str]:
    """owner의 public repo 목록을 페이지네이션으로 모두 가져오기."""
    repos: list[str] = []
    page = 1
    while True:
        data = _api_get(
            f"/users/{owner}/repos",
            token,
            params={"per_page": per_page, "page": page, "type": "public", "sort": "pushed"},
        )
        if not data:
            break
        for r in data:
            if not r.get("fork", False):  # fork 제외
                repos.append(r["full_name"])
        if len(data) < per_page:
            break
        page += 1
    return repos


def get_repo_traffic(owner: str, repo: str, token: str) -> tuple[int, int, int]:
    """
    단일 repo의 트래픽 데이터.
    Returns: (uniques, clones, views) — 14-day rolling window.
    """
    short = repo.split("/")[-1]

    # 1) visitors (uniques + views)
    try:
        visitors = _api_get(f"/repos/{owner}/{short}/traffic/visitors", token)
        uniques = sum(day.get("uniques", 0) for day in visitors.get("visitors", []))
        views = sum(day.get("count", 0) for day in visitors.get("views", []))
    except GitHubAPIError:
        uniques, views = 0, 0

    # 2) clones
    try:
        clones_data = _api_get(f"/repos/{owner}/{short}/traffic/clones", token)
        clones = sum(day.get("count", 0) for day in clones_data.get("clones", []))
    except GitHubAPIError:
        clones = 0

    return (uniques, clones, views)


def get_repo_meta(owner: str, repo: str, token: str) -> tuple[int, int]:
    """repo의 별/포크 cumulative 카운트."""
    short = repo.split("/")[-1]
    try:
        data = _api_get(f"/repos/{owner}/{short}", token)
        return (data.get("stargazers_count", 0), data.get("forks_count", 0))
    except GitHubAPIError:
        return (0, 0)


def collect_traffic_for_repos(
    repos: list[str],
    token: str,
    *,
    delay_seconds: float = 0.2,
) -> list[TrafficRecord]:
    """
    여러 repo의 트래픽 + 메타를 수집해 TrafficRecord 리스트 반환.
    """
    today = utc_today_date()
    records: list[TrafficRecord] = []
    for i, full_name in enumerate(repos):
        try:
            owner, short = full_name.split("/", 1)
            uniques, clones, views = get_repo_traffic(owner, short, token)
            stars, forks = get_repo_meta(owner, short, token)
            records.append(TrafficRecord(
                repo=full_name,
                date=today,
                uniques=uniques,
                clones=clones,
                views=views,
                forks=forks,
                stars=stars,
            ))
        except GitHubAPIError as e:
            # 한 repo 실패는 스킵, 로그만 stderr
            print(f"⚠️ {full_name}: {e}", file=__import__("sys").stderr)
        if delay_seconds > 0 and i < len(repos) - 1:
            time.sleep(delay_seconds)
    return records
