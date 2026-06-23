"""cli.py 단위 테스트 — main() 직접 호출."""
import json
import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    """패키지 설치 안 한 상태에서도 src/ 경로로 직접 실행."""
    cmd = [sys.executable, "-m", "gh_traffic_monitor", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def test_cli_version():
    result = _run_cli("--version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_cli_help():
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "GitHub" in result.stdout
    assert "--owner" in result.stdout


def test_cli_collect_requires_owner():
    """owner 없으면 에러."""
    result = _run_cli("collect")
    assert result.returncode != 0
    assert "--owner" in result.stderr or "required" in result.stderr.lower()


def test_cli_unknown_command():
    result = _run_cli("--owner", "sigco3111", "unknown_cmd")
    assert result.returncode != 0


def test_cli_status_no_logs(tmp_path, monkeypatch):
    """로그 디렉토리 없으면 안내 메시지."""
    log_dir = tmp_path / "nonexistent"
    result = _run_cli("--owner", "sigco3111", "--log-dir", str(log_dir), "status")
    # 디렉토리 없으면 stderr 메시지 + exit 1
    assert result.returncode == 1
    assert "로그 디렉토리" in result.stderr or "없음" in result.stderr


def test_cli_status_after_collect(tmp_path):
    """collect로 데이터 쌓은 후 status가 출력하는지 확인."""
    from gh_traffic_monitor.storage import append_or_update_csv
    from gh_traffic_monitor.models import TrafficRecord

    log_dir = tmp_path / "logs"
    append_or_update_csv(log_dir, [
        TrafficRecord(repo="sigco3111/a", date="2026-06-23", uniques=42, clones=5, views=120, forks=2, stars=10),
        TrafficRecord(repo="sigco3111/b", date="2026-06-23", uniques=99, clones=10, views=300, forks=5, stars=20),
    ])

    result = _run_cli("--owner", "sigco3111", "--log-dir", str(log_dir), "status")
    assert result.returncode == 0
    assert "sigco3111/a" in result.stdout
    assert "sigco3111/b" in result.stdout
    assert "총 repo 수: 2" in result.stdout
