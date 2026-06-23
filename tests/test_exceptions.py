"""exceptions.py 단위 테스트."""
import pytest

from gh_traffic_monitor.exceptions import (
    AuthError,
    GitHubAPIError,
    GTMError,
    RateLimitError,
    StorageError,
)


def test_all_gtm_errors_inherit_from_base():
    """모든 예외는 GTMError 서브클래스 — 사용자가 한 줄로 except 가능."""
    for cls in [AuthError, GitHubAPIError, RateLimitError, StorageError]:
        assert issubclass(cls, GTMError), f"{cls.__name__}이 GTMError 상속 안 함"


def test_rate_limit_message():
    e = RateLimitError(reset_at="2026-06-23T12:00:00+00:00")
    assert "rate limit" in str(e)
    assert "2026-06-23T12:00:00" in str(e)


def test_rate_limit_no_reset():
    e = RateLimitError()
    assert "rate limit" in str(e)


def test_auth_error_basic():
    e = AuthError("토큰 없음")
    assert "토큰 없음" in str(e)
    assert isinstance(e, GTMError)
