"""models.py 단위 테스트."""
from datetime import datetime, timezone

from gh_traffic_monitor.models import (
    CSV_HEADER,
    CumulativeTotals,
    TrafficRecord,
    utc_now_iso,
    utc_today_date,
)


def test_traffic_record_to_dict():
    r = TrafficRecord(
        repo="sigco3111/repo1",
        date="2026-06-23",
        uniques=42,
        clones=5,
        views=120,
        forks=2,
        stars=10,
    )
    d = r.to_dict()
    assert d["repo"] == "sigco3111/repo1"
    assert d["uniques"] == 42
    assert d["forks"] == 2


def test_traffic_record_is_frozen():
    r = TrafficRecord(repo="a/b", date="2026-01-01", uniques=1, clones=1, views=1)
    try:
        r.uniques = 99  # type: ignore[misc]
        assert False, "frozen dataclass은 변경 불가"
    except Exception:
        pass


def test_cumulative_totals_to_dict():
    t = CumulativeTotals(
        repo="sigco3111/repo1",
        first_seen="2026-01-01",
        last_updated="2026-06-23",
        total_uniques=1000,
        total_clones=200,
        total_forks=15,
    )
    d = t.to_dict()
    assert d["total_uniques"] == 1000
    assert d["total_forks"] == 15


def test_csv_header_format():
    """CSV 첫 줄 헤더가 고정 — Repolis 빌더가 의존."""
    assert CSV_HEADER == "repo,date,uniques,clones,views,forks,stars\n"


def test_utc_today_date_format():
    today = utc_today_date()
    assert len(today) == 10
    assert today[4] == "-" and today[7] == "-"


def test_utc_now_iso_is_iso8601():
    iso = utc_now_iso()
    # ISO 8601 파싱 시도
    datetime.fromisoformat(iso.replace("Z", "+00:00"))
    assert "T" in iso
