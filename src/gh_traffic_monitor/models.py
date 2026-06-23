"""
도메인 모델 — 순환 import 방지의 핵심.

모든 다른 모듈은 models만 직접 import 가능. core ↔ github_api ↔ storage
순환 방지 위해 분리.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal


@dataclass(frozen=True)
class TrafficRecord:
    """한 날짜에 한 repo에 대해 수집된 트래픽 스냅샷."""
    repo: str  # "owner/name"
    date: str  # "YYYY-MM-DD" UTC
    uniques: int  # 👁 unique visitors (14-day window)
    clones: int  # ⬇ clones
    views: int  # 📈 views (14-day window, cumulative-ish)
    forks: int = 0  # ⑂ forks (cumulative)
    stars: int = 0  # ★ stars (cumulative)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CumulativeTotals:
    """평생 누적 통계 — first_seen부터 지금까지 합산."""
    repo: str
    first_seen: str  # "YYYY-MM-DD"
    last_updated: str  # "YYYY-MM-DD"
    total_uniques: int = 0
    total_clones: int = 0
    total_forks: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CollectionResult:
    """한 번의 collection 실행 결과."""
    collected_at: str  # ISO 8601 UTC
    repos_processed: int
    repos_failed: int
    duration_seconds: float
    failed_repos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# CSV 컬럼 순서 — 첫 줄 헤더 고정
CSV_HEADER = "repo,date,uniques,clones,views,forks,stars\n"
CSV_COLUMNS = ["repo", "date", "uniques", "clones", "views", "forks", "stars"]


def utc_now_iso() -> str:
    """현재 UTC 시각을 ISO 8601 형식으로."""
    return datetime.now(timezone.utc).isoformat()


def utc_today_date() -> str:
    """현재 UTC 날짜를 YYYY-MM-DD 형식으로."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
