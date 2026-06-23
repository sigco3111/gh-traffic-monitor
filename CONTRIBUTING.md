# Contributing to gh-traffic-monitor

작은 도구라 PR은 가끔만 와도 충분해요. 큰 변경은 먼저 issue로 의도를 알려주세요.

## 개발 환경

```bash
git clone https://github.com/sigco3111/gh-traffic-monitor
cd gh-traffic-monitor
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## 테스트

```bash
pytest tests/ -v
```

## 새 기능 추가

큰 변경 (`storage 백엔드 추가`, `GraphQL 지원` 등) 은 **issue로 먼저** 의도 공유. 작은 버그 수정은 바로 PR.

## 스타일

- stdlib only 원칙 유지 (의존성 추가는 issue로 논의)
- `models` / `exceptions` / `storage` / `github_api` / `core` / `cli` 6계층 분리 유지
- 새 예외는 `GTMError` 서브클래스로
- 새 함수는 타입 힌트 필수 (`from __future__ import annotations` 사용)

## 커밋 메시지

- `feat:` 새 기능
- `fix:` 버그
- `docs:` 문서만
- `test:` 테스트만
- `chore:` 빌드/CI/잡일

## 라이선스

기여 시 MIT 라이선스 동의로 간주.
