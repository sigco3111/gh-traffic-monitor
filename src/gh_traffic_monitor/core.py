"""
오케스트레이터 — collect → append → summarize 한 사이클 실행.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from . import github_api, storage
from .exceptions import GTMError
from .models import CollectionResult, utc_now_iso


def run_collection(
    owner: str,
    log_dir: Path,
    *,
    token: str | None = None,
    delay_seconds: float = 0.2,
) -> CollectionResult:
    """
    메인 워크플로:
      1) 토큰 확보
      2) owner의 public repo 목록 조회
      3) 각 repo 트래픽 수집
      4) 오늘자 CSV로 저장 (merge)
      5) 전체 누적 통계 계산 + _cumulative.csv 갱신

    Returns: CollectionResult.
    Raises: GTMError (모든 예외의 베이스).
    """
    started_at = time.monotonic()
    failed_repos: list[str] = []

    try:
        token = token or github_api.get_gh_token()

        # 1) repo 목록
        print(f"[1/4] {owner}의 public repo 목록 조회 중...", file=sys.stderr)
        repos = github_api.list_public_repos(owner, token)
        print(f"      → {len(repos)}개 repo 발견", file=sys.stderr)

        # 2) 트래픽 수집
        print(f"[2/4] 트래픽 수집 중 (rate limit 고려해 {delay_seconds}s 간격)...", file=sys.stderr)
        records = []
        for rec in github_api.collect_traffic_for_repos(repos, token, delay_seconds=delay_seconds):
            records.append(rec)
        processed = len(records)
        print(f"      → {processed}개 repo 데이터 수집 완료", file=sys.stderr)

        # 3) 오늘 CSV 저장
        print(f"[3/4] CSV 저장 중: {log_dir}", file=sys.stderr)
        written = storage.append_or_update_csv(log_dir, records)
        print(f"      → {written}개 row 기록됨", file=sys.stderr)

        # 4) 누적 통계 계산 + 저장
        print(f"[4/4] 누적 통계 계산 중...", file=sys.stderr)
        totals = storage.compute_cumulative_totals(log_dir)
        out_path = storage.write_cumulative_csv(log_dir, totals)
        print(f"      → {len(totals)}개 repo 누적 통계 저장: {out_path}", file=sys.stderr)

        duration = time.monotonic() - started_at
        return CollectionResult(
            collected_at=utc_now_iso(),
            repos_processed=processed,
            repos_failed=len(repos) - processed,
            duration_seconds=round(duration, 2),
            failed_repos=failed_repos,
        )

    except GTMError as e:
        print(f"❌ {e}", file=sys.stderr)
        raise
