"""
CLI — argparse 기반. 서브 명령 없이 단일 진입점.

Usage:
  gh-traffic-monitor collect --owner sigco3111 [--log-dir ./data/logs]
  gh-traffic-monitor status --owner sigco3111 [--log-dir ./data/logs]
  gh-traffic-monitor repos --owner sigco3111
  gh-traffic-monitor --version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import core, github_api, storage
from .exceptions import GTMError

__version__ = "0.1.0"


def _cmd_collect(args: argparse.Namespace) -> int:
    """collect: 트래픽 수집 + 누적 통계 갱신."""
    log_dir = Path(args.log_dir).expanduser().resolve()
    try:
        result = core.run_collection(
            args.owner,
            log_dir,
            delay_seconds=args.delay,
        )
        # JSON 결과 stdout 출력 (cron에서 파싱 가능)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0
    except GTMError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def _cmd_status(args: argparse.Namespace) -> int:
    """status: 현재 누적 통계 요약 출력."""
    log_dir = Path(args.log_dir).expanduser().resolve()
    if not log_dir.exists():
        print(f"로그 디렉토리 없음: {log_dir}", file=sys.stderr)
        return 1
    totals = storage.compute_cumulative_totals(log_dir)
    if not totals:
        print("누적 통계 없음. 먼저 `collect` 실행하세요.", file=sys.stderr)
        return 0

    print(f"=== {args.owner} 누적 트래픽 요약 ===\n")
    print(f"총 repo 수: {len(totals)}\n")
    print(f"{'REPO':<40} {'FIRST SEEN':<12} {'UNIQUES':>8} {'CLONES':>8} {'FORKS':>6}")
    print("-" * 78)
    for t in totals:
        print(f"{t.repo:<40} {t.first_seen:<12} {t.total_uniques:>8} {t.total_clones:>8} {t.total_forks:>6}")
    return 0


def _cmd_repos(args: argparse.Namespace) -> int:
    """repos: 현재 GitHub에서 보이는 public repo 목록 (디버그용)."""
    token = github_api.get_gh_token()
    repos = github_api.list_public_repos(args.owner, token)
    print(f"=== {args.owner} public repos ({len(repos)}) ===")
    for r in repos:
        print(r)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gh-traffic-monitor",
        description="📊 GitHub repo 트래픽을 매일 누적 CSV로 저장 (Repolis 등 도시화에 사용)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--owner", required=True, help="GitHub 사용자/조직명 (예: sigco3111)")
    parser.add_argument("--log-dir", default="./data/logs", help="CSV 저장 디렉토리 (기본: ./data/logs)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = subparsers.add_parser("collect", help="트래픽 수집 + 누적 통계 갱신")
    p_collect.add_argument("--delay", type=float, default=0.2, help="API 호출 간 지연(초) (기본: 0.2)")
    p_collect.set_defaults(func=_cmd_collect)

    # status
    subparsers.add_parser("status", help="누적 통계 요약 출력").set_defaults(func=_cmd_status)

    # repos
    subparsers.add_parser("repos", help="GitHub에서 보이는 public repo 목록 (디버그용)").set_defaults(func=_cmd_repos)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except GTMError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
