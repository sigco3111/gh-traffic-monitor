"""
CSV 저장/누적 — data/logs/*.csv 관리.

GitHub Actions 워크플로에서 매일 한 번 실행되며, 같은 repo/date 조합이
이미 있으면 새 값으로 덮어쓰고 없으면 append.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from .exceptions import StorageError
from .models import CSV_COLUMNS, CSV_HEADER, CumulativeTotals, TrafficRecord


def ensure_log_dir(log_dir: Path) -> None:
    """로그 디렉토리 생성 — parents=True, exist_ok=True."""
    log_dir.mkdir(parents=True, exist_ok=True)


def append_or_update_csv(log_dir: Path, records: list[TrafficRecord]) -> int:
    """
    오늘 날짜 기준 CSV 파일에 records 저장.
    같은 (repo, date) 조합이 이미 있으면 새 값으로 덮어쓰기.

    Returns: 기록된 row 수.
    """
    if not records:
        return 0
    today = records[0].date
    csv_path = log_dir / f"{today}.csv"

    # 기존 데이터 로드 (있으면)
    existing: dict[str, TrafficRecord] = {}
    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get("repo"):
                        continue
                    existing[row["repo"]] = TrafficRecord(
                        repo=row["repo"],
                        date=row["date"],
                        uniques=int(row.get("uniques", 0)),
                        clones=int(row.get("clones", 0)),
                        views=int(row.get("views", 0)),
                        forks=int(row.get("forks", 0)),
                        stars=int(row.get("stars", 0)),
                    )
        except (OSError, ValueError) as e:
            raise StorageError(f"CSV 읽기 실패: {csv_path}: {e}") from e

    # 새 데이터 머지
    for rec in records:
        existing[rec.repo] = rec

    # 정렬 후 저장
    ensure_log_dir(log_dir)
    sorted_records = sorted(existing.values(), key=lambda r: r.repo)
    try:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for rec in sorted_records:
                writer.writerow(rec.to_dict())
    except OSError as e:
        raise StorageError(f"CSV 쓰기 실패: {csv_path}: {e}") from e

    return len(sorted_records)


def compute_cumulative_totals(log_dir: Path) -> list[CumulativeTotals]:
    """
    모든 일별 CSV를 합산해 repo별 평생 누적 통계 계산.
    """
    if not log_dir.exists():
        return []

    # repo → (first_date, last_date, total_uniques, total_clones, total_forks)
    agg: dict[str, dict] = {}
    for csv_path in sorted(log_dir.glob("*.csv")):
        try:
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    repo = row.get("repo")
                    date = row.get("date")
                    if not repo or not date:
                        continue
                    if repo not in agg:
                        agg[repo] = {
                            "first_seen": row["date"],
                            "last_updated": row["date"],
                            "total_uniques": 0,
                            "total_clones": 0,
                            "total_forks": 0,
                        }
                    a = agg[repo]
                    a["first_seen"] = min(a["first_seen"], row["date"])
                    a["last_updated"] = max(a["last_updated"], row["date"])
                    a["total_uniques"] += int(row.get("uniques", 0))
                    a["total_clones"] += int(row.get("clones", 0))
                    # forks는 cumulative (GitHub API 응답 자체가 누적)이므로 마지막 값 사용
                    a["total_forks"] = max(a["total_forks"], int(row.get("forks", 0)))
        except (OSError, ValueError) as e:
            raise StorageError(f"CSV 집계 실패: {csv_path}: {e}") from e

    return [
        CumulativeTotals(repo=repo, **data)
        for repo, data in sorted(agg.items())
    ]


def write_cumulative_csv(log_dir: Path, totals: list[CumulativeTotals]) -> Path:
    """누적 통계를 단일 CSV로 저장 — Repolis 빌더가 이걸 읽음."""
    ensure_log_dir(log_dir)
    out = log_dir / "_cumulative.csv"
    try:
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["repo", "first_seen", "last_updated", "total_uniques", "total_clones", "total_forks"])
            for t in totals:
                writer.writerow([
                    t.repo,
                    t.first_seen,
                    t.last_updated,
                    t.total_uniques,
                    t.total_clones,
                    t.total_forks,
                ])
    except OSError as e:
        raise StorageError(f"누적 CSV 쓰기 실패: {out}: {e}") from e
    return out
