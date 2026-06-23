"""storage.py 단위 테스트 — 임시 디렉토리 사용."""
from pathlib import Path

import pytest

from gh_traffic_monitor.exceptions import StorageError
from gh_traffic_monitor.models import TrafficRecord
from gh_traffic_monitor.storage import (
    append_or_update_csv,
    compute_cumulative_totals,
    ensure_log_dir,
    write_cumulative_csv,
)


def test_ensure_log_dir(tmp_path):
    target = tmp_path / "subdir" / "logs"
    ensure_log_dir(target)
    assert target.exists()
    assert target.is_dir()


def test_append_or_update_csv_writes_new(tmp_path):
    log_dir = tmp_path / "logs"
    records = [
        TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=10, clones=2, views=50, forks=1, stars=5),
        TrafficRecord(repo="sigco3111/b", date="2026-06-23", uniques=20, clones=4, views=80, forks=0, stars=10),
    ]
    n = append_or_update_csv(log_dir, records)
    assert n == 2
    csv_path = log_dir / "2026-06-23.csv"
    assert csv_path.exists()
    content = csv_path.read_text()
    assert "sigco3111/a" in content
    assert "sigco3111/b" in content


def test_append_or_update_csv_overwrites_same_repo(tmp_path):
    """같은 (repo, date)이면 새 값으로 덮어쓰기 — 14-day 롤링 갱신 시 필수."""
    log_dir = tmp_path / "logs"

    # 첫 수집
    first = [TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=10, clones=2, views=50, forks=1, stars=5)]
    append_or_update_csv(log_dir, first)

    # 같은 날 다시 수집 (값이 더 정확)
    second = [TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=12, clones=3, views=60, forks=1, stars=5)]
    append_or_update_csv(log_dir, second)

    # 값이 갱신됨
    totals = compute_cumulative_totals(log_dir)
    assert len(totals) == 1
    assert totals[0].total_uniques == 12  # 10이 아니라 12


def test_compute_cumulative_across_days(tmp_path):
    """여러 날 데이터 합산."""
    log_dir = tmp_path / "logs"
    append_or_update_csv(log_dir, [
        TrafficRecord(repo="sigco3111/a", date="2026-06-22", uniques=10, clones=2, views=50, forks=1, stars=5),
    ])
    append_or_update_csv(log_dir, [
        TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=15, clones=3, views=80, forks=1, stars=6),
    ])

    totals = compute_cumulative_totals(log_dir)
    assert len(totals) == 1
    t = totals[0]
    assert t.total_uniques == 25  # 10 + 15
    assert t.total_clones == 5  # 2 + 3
    assert t.total_forks == 1  # max(1, 1)
    assert t.first_seen == "2026-06-22"
    assert t.last_updated == "2026-06-23"


def test_compute_cumulative_multiple_repos(tmp_path):
    log_dir = tmp_path / "logs"
    append_or_update_csv(log_dir, [
        TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=10, clones=2, views=50),
        TrafficRecord(repo="sigco3111/b", date="2026-06-23", uniques=20, clones=4, views=80),
    ])
    totals = compute_cumulative_totals(log_dir)
    assert len(totals) == 2
    repos = {t.repo for t in totals}
    assert repos == {"sigco3111/a", "sigco3111/b"}


def test_write_cumulative_csv(tmp_path):
    log_dir = tmp_path / "logs"
    append_or_update_csv(log_dir, [
        TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=10, clones=2, views=50, forks=3),
    ])
    totals = compute_cumulative_totals(log_dir)
    out = write_cumulative_csv(log_dir, totals)
    assert out.exists()
    content = out.read_text()
    assert "sigco3111/a" in content
    assert "first_seen" in content
    assert "total_uniques" in content


def test_compute_cumulative_empty_dir(tmp_path):
    log_dir = tmp_path / "logs"
    # 디렉토리 없음
    totals = compute_cumulative_totals(log_dir)
    assert totals == []
