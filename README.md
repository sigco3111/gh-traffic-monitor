# 📊 gh-traffic-monitor

> GitHub repo 트래픽을 **매일 누적 CSV**로 저장 — 14-day 롤링 윈도우의 한계를 넘어 **평생 방문자/클론/포크** 통계를 만든다.

<a id="english"></a>

**English summary** — A zero-deps Python CLI that walks your GitHub repos daily, fetches per-repo traffic (visitors · clones · forks · stars), stores it as append-only daily CSVs, and writes a lifetime `_cumulative.csv`. Built as the data backbone for [`Repolis`](https://github.com/hyeonsangjeon/Repolis)-style 3D city visualizations, but works standalone for any "show me my repo stats over time" use case.

---

## 🤔 왜 이게 필요한가? (`Why this exists`)

GitHub의 [Traffic API](https://docs.github.com/en/rest/metrics/traffic)는 **14일 롤링 윈도우**만 보여줍니다. 즉:

| 문제 | 영향 |
|---|---|
| 14일 넘은 방문자 데이터 사라짐 | "내 repo가 지금까지 몇 명 왔지?" 못 답함 |
| 14일 넘은 clone 데이터 사라짐 | "내 코드가 지금까지 몇 번 clone됐지?" 못 답함 |
| 14일 넘은 view 데이터 사라짐 | "내 README가 누적 몇 번 읽혔지?" 못 답함 |

`Repolis` 같은 3D 도시 시각화는 **누적 데이터로 건물의 크기·밝기·장식을 결정**합니다. 롤링 14일 데이터로는 도시가 매일 변해서 의미가 없어요.

`gh-traffic-monitor`는 이 갭을 메웁니다:
- 매일 1회 (또는 수동) 트래픽 수집
- `data/logs/YYYY-MM-DD.csv`에 일별 row append (overwrite on same date)
- `data/logs/_cumulative.csv`에 평생 누적 통계
- stdlib only (의존성 0개), zero-deps

## 📦 설치 (`Installation`)

```bash
# 시스템 Python 3.9+ 필요
git clone https://github.com/sigco3111/gh-traffic-monitor
cd gh-traffic-monitor
pip install -e ".[dev]"
```

또는 사용만 할 거면:
```bash
pip install gh-traffic-monitor  # PyPI 배포 시 (v0.2.0+)
```

## 🚀 빠른 시작 (`Quick start`)

### 사전 조건

`gh` CLI 인증 또는 `GH_TOKEN` / `GITHUB_TOKEN` 환경 변수 필요:
```bash
gh auth login                  # 1회만
# 또는
export GH_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 1️⃣ repo 목록 확인 (디버그)

```bash
gh-traffic-monitor --owner sigco3111 repos
# → 154개 public repo 목록 출력
```

### 2️⃣ 트래픽 수집

```bash
gh-traffic-monitor --owner sigco3111 --log-dir ./data/logs collect
```

진행:
```
[1/4] sigco3111의 public repo 목록 조회 중...
      → 154개 repo 발견
[2/4] 트래픽 수집 중 (rate limit 고려해 0.2s 간격)...
      → 154개 repo 데이터 수집 완료
[3/4] CSV 저장 중: ./data/logs
      → 154개 row 기록됨
[4/4] 누적 통계 계산 중...
      → 154개 repo 누적 통계 저장
```

결과 (stdout JSON):
```json
{
  "collected_at": "2026-06-23T00:16:53+00:00",
  "repos_processed": 154,
  "repos_failed": 0,
  "duration_seconds": 193.47
}
```

### 3️⃣ 누적 통계 확인

```bash
gh-traffic-monitor --owner sigco3111 --log-dir ./data/logs status
```

```
=== sigco3111 누적 트래픽 요약 ===

총 repo 수: 154

REPO                                     FIRST SEEN    UNIQUES   CLONES  FORKS
------------------------------------------------------------------------------
sigco3111/2048                           2026-06-23          0        4      0
sigco3111/3d-fractal                     2026-06-23          0        4      1
...
```

## 📊 생성되는 파일 (`Output files`)

### `data/logs/YYYY-MM-DD.csv` — 일별 스냅샷

```csv
repo,date,uniques,clones,views,forks,stars
sigco3111/2048,2026-06-23,0,4,0,0,0
sigco3111/3d-fractal,2026-06-23,0,4,1,1,0
sigco3111/dongne-today,2026-06-23,15,8,420,3,12
...
```

- 같은 날 두 번 실행하면 **덮어쓰기** (14-day rolling 갱신에 대비)
- 새 날짜면 새 파일 생성

### `data/logs/_cumulative.csv` — 평생 누적

```csv
repo,first_seen,last_updated,total_uniques,total_clones,total_forks
sigco3111/2048,2026-06-23,2026-06-23,0,4,0
sigco3111/dongne-today,2026-06-23,2026-06-23,15,8,3
...
```

- `first_seen`: 이 repo가 처음 데이터에 등장한 날 (도시에서 "입주일")
- `forks`: cumulative GitHub API 응답이라 **max** 사용

## ⚙️ 옵션 (`Options`)

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--owner` | (필수) | GitHub 사용자/조직명 |
| `--log-dir` | `./data/logs` | CSV 저장 디렉토리 |
| `--delay` (collect only) | `0.2` | API 호출 간 지연(초). rate limit 보호 |
| `--version` | — | 버전 출력 |

## 🎯 사용 시나리오 (`Use cases`)

### 1️⃣ Repolis 같은 3D 도시 시각화

`hyeonsangjeon/Repolis`를 sigco3111 버전에 맞게 fork할 때, `data/logs/`에 이 도구의 CSV를 넣으면 됩니다:
```bash
# 1. Repolis fork에서 scripts/build_repos.py가 _cumulative.csv를 읽도록 조정
# 2. GitHub Actions에서 매일 collect 실행 → repos.json 자동 갱신
# 3. GitHub Pages에 도시 자동 배포
```

### 2️⃣ "내 repo 인기도 추적" 대시보드

```python
import pandas as pd
df = pd.read_csv("data/logs/_cumulative.csv")
print(df.sort_values("total_clones", ascending=False).head(10))
```

### 3️⃣ 일별 diff로 "어제 vs 오늘" 분석

```bash
gh-traffic-monitor collect  # 매일 cron
diff data/logs/2026-06-22.csv data/logs/2026-06-23.csv
```

### 4️⃣ Rate-limit-safe 배치 수집

큰 조직 (1000+ repo) 도 `--delay 1.0`으로 안전하게:
```bash
gh-traffic-monitor --owner large-org collect --delay 1.0
```

## 🔄 다른 도구와 함께 (`Related tools`)

- **[`Repolis`](https://github.com/hyeonsangjeon/Repolis)** — 이 도구의 CSV를 읽어 3D 도시 렌더링
- **[GitHub Traffic API](https://docs.github.com/en/rest/metrics/traffic)** — raw 14-day 데이터 소스
- **pandas / DuckDB** — `_cumulative.csv` 분석용

## 🤖 자동화 (cron / GitHub Actions)

### cron (로컬/서버)

```bash
# 매일 새벽 3시 실행
0 3 * * * cd /path/to/gh-traffic-monitor && /usr/bin/python3 -m gh_traffic_monitor --owner sigco3111 --log-dir /var/lib/gtm/logs collect
```

### GitHub Actions

```yaml
name: Daily traffic collection
on:
  schedule:
    - cron: "0 */6 * * *"  # 6시간마다
  workflow_dispatch:        # 수동 트리거

jobs:
  collect:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e .
      - run: python -m gh_traffic_monitor --owner sigco3111 --log-dir ./data/logs collect
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/logs/
          git commit -m "chore: daily traffic snapshot $(date +%Y-%m-%d)" || exit 0
          git push
```

## 🗺️ 로드맵 (`Roadmap`)

| 버전 | 상태 | 내용 |
|---|---|---|
| **v0.1.0** | ✅ 2026-06-23 | 일별 CSV + 누적 CSV + CLI + 23 테스트 |
| v0.2.0 | 📋 예정 | PyPI 배포, repo 카테고리 분류, stars/views 누적 |
| v0.3.0 | 💭 | SQLite 백엔드 옵션 (CSV보다 빠른 쿼리) |
| v1.0.0 | 💭 | GraphQL batch API, rate limit 자동 백오프 |

## 🧪 테스트

```bash
python -m pytest tests/ -v
```

**23개 테스트 통과** (0.6초):
- 6개 models (frozen dataclass, CSV 헤더, ISO 포맷)
- 4개 exceptions (계층, 메시지)
- 7개 storage (append/overwrite/누적/멀티 repo)
- 6개 CLI (version, help, status, owner 누락, 알 수 없는 명령, status after collect)

## 📁 디렉토리 구조

```
gh-traffic-monitor/
├── src/gh_traffic_monitor/
│   ├── __init__.py
│   ├── __main__.py        # python -m gh_traffic_monitor 진입점
│   ├── cli.py             # argparse CLI
│   ├── core.py            # 오케스트레이터
│   ├── github_api.py      # stdlib urllib로 GitHub REST API 호출
│   ├── storage.py         # CSV 저장/누적
│   ├── models.py          # TrafficRecord, CumulativeTotals
│   └── exceptions.py      # GTMError 계층
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_exceptions.py
│   ├── test_models.py
│   └── test_storage.py
├── data/logs/             # gitignored, 실행 시 생성
├── .github/workflows/
├── pyproject.toml
└── README.md
```

## ⚠️ 주의사항

- **첫 24~48시간**: GitHub Traffic API가 익명 visitor 데이터를 노출하는 데 시간이 걸립니다. 첫 실행 후 uniques가 0이어도 정상이에요.
- **Rate limit**: 인증된 사용자 기준 시간당 5,000 요청. 154개 repo × 3 요청 = 462 요청이니 안전합니다.
- **14일 룰**: 14일 넘은 데이터는 GitHub이 자체 삭제하므로, **반드시 매일 실행**해야 평생 누적이 정확합니다.

## 🙏 감사의 말

- [hyeonsangjeon/Repolis](https://github.com/hyeonsangjeon/Repolis) — 이 도구가 만들어진 직접적인 동기. 14일 롤링 한계를 매일 누적으로 해결하는 패턴 차용.
- GitHub REST API 팀 — 깔끔하고 잘 문서화된 API.

## 📄 라이선스

MIT — `LICENSE` 파일 참고.
