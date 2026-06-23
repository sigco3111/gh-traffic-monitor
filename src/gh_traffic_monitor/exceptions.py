"""
예외 계층 — 모든 gh_traffic_monitor 예외는 GTMError 서브클래스.

사용자가 `except GTMError:` 한 줄로 잡을 수 있도록 베이스 클래스 통일.
"""


class GTMError(Exception):
    """gh-traffic-monitor 베이스 예외."""


class GitHubAPIError(GTMError):
    """GitHub API 호출 실패 (rate limit, 404, 500 등)."""


class RateLimitError(GitHubAPIError):
    """GitHub API rate limit 초과."""

    def __init__(self, reset_at: str | None = None):
        self.reset_at = reset_at
        msg = f"GitHub API rate limit 초과 (reset: {reset_at})" if reset_at else "GitHub API rate limit 초과"
        super().__init__(msg)


class AuthError(GTMError):
    """인증 실패 (토큰 누락, 권한 부족)."""


class StorageError(GTMError):
    """CSV 파일 읽기/쓰기 실패."""


class ConfigError(GTMError):
    """설정 오류 (잘못된 경로, 형식 등)."""
