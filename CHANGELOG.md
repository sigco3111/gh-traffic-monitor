# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-23

### Added
- 초기 릴리즈
- `collect` 명령: GitHub REST API로 모든 public repo의 트래픽 + 메타데이터 수집
- `data/logs/YYYY-MM-DD.csv` 일별 스냅샷 (같은 날 재실행 시 overwrite)
- `data/logs/_cumulative.csv` 평생 누적 통계 (first_seen, last_updated, totals)
- `status` 명령: 누적 통계 요약 출력
- `repos` 명령: 디버그용 public repo 목록
- stdlib only (의존성 0개)
- GitHub Actions workflow 예시
- 23개 단위 테스트 (models / exceptions / storage / CLI)
- README 한/영 병기 + 다층 옵션 (설치/옵션/시나리오/로드맵)
