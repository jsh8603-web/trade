# 통합 투자 시스템 (Inv) — 멀티에셋 자율매매

> 버전 `1.39.0` · Python 3.10+

---

## 한 줄 소개

암호화폐·주식·원자재·채권을 **단일 코드 경로**로 자율 운용하는 멀티에셋 투자 시스템이다.

---

## 뭐 하는 시스템인가

원래 BTC 단일 자산을 거래하던 코인 봇(`agents/`)을 출발점으로, **asset-agnostic 코어(`core/`)** 로 일반화하여 주식·상품·채권까지 동일 리스크 게이트로 다루는 시스템이다.

핵심 설계 철학은 두 가지다.

**첫째, 결정론이 기본값이고 LLM은 깎기만 한다.** 매 사이클마다 Python 결정론 코드가 먼저 사이징을 계산한다. LLM(로컬 Qwen / Claude OAuth)은 고-스테이크스 트리거에서만 호출되며, 사이징을 **줄이거나 유지**하는 방향으로만 작동한다(`final ≤ l1_size` 불변식). LLM이 베팅을 키우는 경로는 코드에 존재하지 않는다.

**둘째, 불확실하면 자동으로 위험을 줄인다.** 거시 국면 판단 신뢰도가 낮거나 데이터가 없으면, belief 분포가 평탄해지고 그 평탄함이 자산배분 단계에서 중립화·분산으로 흘러간다. 사람 개입 없이 수학이 위험을 줄인다.

> **현재 라이브 = 레거시 코인 봇** (`agents/` + `scripts/run_agents.sh`). 신규 `core/` 아키텍처는 환경변수 opt-in 방식으로 연결되며, 기본 off 상태에서는 레거시 경로가 byte-identical하게 유지된다. 실거래 전환(`DRY_RUN=false`)과 90일 무중단 검증은 **사람 게이트** (자율 범위 밖)다.

---

## 주요 기능

### 코인 트랙 (현재 라이브)
- 보수/보통/공격적 전략 3종을 **감독 에이전트가 자율 전환** (위험도·기회 점수 기반)
- 11개 소스 병렬 수집 (시세, FGI, 뉴스, 고래 추적, 소셜 감성 등)
- 자동 긴급정지 + 수동 EMERGENCY_STOP (감독도 수동 정지 해제 불가)

### 주식 트랙 (개발 중)
- 가치 2단 트리거: 1차 저비용 필터 → 2차 내재가치 검증 (value trap 분리)
- KIS(한국투자증권) 연동, 모의투자 우선
- KR/US 개별주 + ETF 지원

### 두뇌·거시 레이어
- FRED 지표 기반 Investment Clock 4분면 결정론 분류 (거시 국면 판단)
- LLM 라우팅: 평상시 로컬 Qwen → 위기 트리거 시 Claude OAuth deep 호출
- 오판 학습 루프: 지표가 예상과 다르게 움직이면 다음 판단의 신뢰도를 낮춤

### PIT(Point-in-Time) 안전
- 백테스트가 미래 정보를 참조하지 못하도록 bitemporal 이중 시간축 강제
- 생존편향 차단: 상폐 종목 포함 재현, 재작성(RESTATED) 데이터 거부

### 백테스트
- 코인·주식 동일 `AssetTrack` 계약으로 구동
- 거래대금 비례 슬리피지, 세금 반영
- PBO(과적합 정도) / DSR(deflated Sharpe) 정량 산출

---

## 아키텍처 개요

```
[Portfolio Orchestrator]        ← 슬리브 배분 (코인/주식/원자재/금/채권)
        │
  ┌─────┴─────┐
[Coin Track]  [Stock Track]     ← 자산별 신호 생성 (AssetTrack 공통 계약)
  레거시 흡수   가치 2단 트리거
        │
  [Shared Risk Gate]            ← 우회 불가, 결정론, LLM 미의존
  손실한도 / 상관캡 / 회전율 / kill switch
        │
  ┌─────┴─────┐
[Coin Exec]  [Stock Exec]       ← Upbit·바이낸스 / KIS
```

**흐름**: 트랙이 후보 결정 생성 → (고-스테이크스 시) consensus Judge → 공통 리스크 게이트 → 멀티에셋 사이징 → 주문

```
core/
  asset_track.py · coin_track*.py · stock_track.py   실행 트랙
  risk_gate.py · risk_sizing.py                       리스크·사이징
  consensus.py · portfolio_orchestrator.py            합의·배분
  brain/         두뇌 (거시 레짐·LLM 라우팅·학습 메모리·RAG)
  data/          데이터·PIT·event ledger·가중학습
  structure/     가정 통계·e-process·FDR·glasso
  assume/        가정 라이프사이클·judge·가중카드
  observability/ kill_switch·rule_observer
agents/          레거시 실행 (현재 라이브)
scripts/         데이터 수집·실행 파이프라인
stock/           주식 가치 트랙
backtest/        통합 백테스트 엔진
study-research/  연구 샌드박스 (production 미배선)
```

상세 코드 구조는 [CODEMAP.md](./CODEMAP.md) 참조. *(코드 색인·디버깅 진입점)*

---

## 설치 및 의존성

### Python 버전

Python **3.10 이상** 권장 (torch, gymnasium 등 의존성 기준).

### 가상환경 생성

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 패키지 설치

```bash
pip install -r requirements.txt
```

주요 의존성 그룹:

| 그룹 | 주요 패키지 | 용도 |
|---|---|---|
| 코어 | `requests`, `python-dotenv`, `PyJWT`, `pyyaml` | 공통 유틸 |
| 거래소 | `ccxt`, `python-kis` (pykis) | Upbit·바이낸스·KIS |
| 데이터 | `yfinance`, `fredapi`, `pykrx`, `finance-datareader`, `dart-fss` | 시세·FRED·KRX·DART |
| LLM | `google-generativeai`, `openai` | Gemini / OpenAI 연동 |
| 포트폴리오 최적화 | `cvxpy`, `PyPortfolioOpt`, `riskfolio-lib`, `scikit-learn` | 리스크·사이징 |
| 거시 레짐 | `jumpmodels`, `pandas-market-calendars` | JM stress 신호·휴장일 |
| 크롤링·자동화 | `playwright`, `twikit`, `feedparser` | 차트 캡처·X 수집·RSS |
| DB | `psycopg2-binary` (Supabase PostgreSQL) | 결정 기록·이력 저장 |
| 강화학습 | `gymnasium`, `stable-baselines3`, `torch` | RL 하이브리드 (Phase 2+) |

> Playwright 첫 설치 시 브라우저 실행파일 설치 필요:
> ```bash
> npx playwright@latest install chromium
> ```
> 브라우저 버전 오류 발생 시 동일 명령으로 재설치.

---

## 환경 설정

`.env.example`을 복사해 `.env`를 만들고 실제 키를 채운다.

```bash
cp .env.example .env
```

### 필수 환경변수

| 변수 | 용도 |
|---|---|
| `UPBIT_ACCESS_KEY` | 업비트 API 액세스 키 |
| `UPBIT_SECRET_KEY` | 업비트 API 시크릿 키 |
| `TAVILY_API_KEY` | Tavily 뉴스 검색 API |
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 롤 키 |
| `SUPABASE_DB_URL` | Supabase PostgreSQL 직접 연결 URL |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_USER_ID` | 텔레그램 수신 유저 ID |

### 선택 환경변수

| 변수 | 기본값 | 용도 |
|---|---|---|
| `GEMINI_API_KEY` | — | Gemini LLM 호출 (LLM-RL 모드) |
| `CRYPTOCOMPARE_API_KEY` | — | 소셜 감성 수집 |
| `X_USERNAME` / `X_PASSWORD` / `X_EMAIL` | — | X(트위터) 계정 (뉴스랑 확장 수집) |
| `BINANCE_API_KEY` / `BINANCE_API_SECRET` | — | 바이낸스 펀딩/롱숏 데이터 수집 |
| `MACHINE_NAME` | `pc128` | 다중 PC 운영 시 DB 중복 방지 식별자 |
| `MACHINE_ROLE` | `primary` | `primary` = DB 레코드 주체 / `worker` = 수집·실행만 |

### 단타 트레이더 설정

| 변수 | 기본값 | 용도 |
|---|---|---|
| `SHORT_TERM_BUDGET` | `500000` KRW | 단타 전체 예산 |
| `SHORT_TERM_MAX_TRADE` | `200000` KRW | 단타 1회 최대 매매액 |
| `SHORT_TERM_MAX_DAILY` | `10` | 단타 일 최대 매매 횟수 |
| `SHORT_TERM_STOP_LOSS` | `0.8` | 단타 손절 비율 |
| `SHORT_TERM_TAKE_PROFIT` | `1.5` | 단타 익절 비율 |
| `SHORT_TERM_MAX_HOLD_MIN` | `30` | 단타 최대 보유 시간(분) |

### 변동성 돌파 전략 설정

| 변수 | 기본값 | 용도 |
|---|---|---|
| `BREAKOUT_ENABLED` | `true` | 전략 활성화 |
| `BREAKOUT_DRY_RUN` | `true` | 시뮬레이션 모드 (첫 1달 검증 후 `false` 전환) |
| `BREAKOUT_K` | `0.7` | 돌파 K값 (0.5~0.7, 백테스트 최고 0.7) |
| `BREAKOUT_BUY_AMOUNT` | `300000` KRW | 1회 매수액 |
| `BREAKOUT_STOP_LOSS_PCT` | `-2.0` | 손절 임계 (%) |
| `BREAKOUT_TIME_EXIT_HOURS` | `24` | 자동 청산 시간 (h) |
| `BREAKOUT_TRADE_TIME_KST` | `10:00` | 매수/청산 기준 시각 (KST) |

### 바이낸스 서브봇(AltRang) 설정

| 변수 | 기본값 | 용도 |
|---|---|---|
| `SB_EXCHANGE` | `binance` | 거래소 선택 (`binance` 또는 `upbit`) |
| `SB_DRY_RUN` | `true` | 서브봇 시뮬레이션 모드 |
| `SB_EMERGENCY_STOP` | `false` | 서브봇 즉시 정지 |
| `SB_FUNDING_MIN_RATE` | `0.0005` | 펀딩 전략 최소 수익률 |
| `SB_FUNDING_MAX_COINS` | `5` | 펀딩 전략 최대 보유 종목 수 |
| `SB_FUNDING_POSITION_USDT` | `200` | 펀딩 전략 1종목 포지션 |
| `SB_FUNDING_MAX_TOTAL_USDT` | `1000` | 펀딩 전략 총 최대 포지션 |
| `SB_ROTATION_UNIVERSE` | `30` | 로테이션 전략 유니버스 크기 |
| `SB_ROTATION_TOP_N` | `5` | 로테이션 전략 보유 종목 수 |
| `SB_ROTATION_INTERVAL_MIN` | `240` | 로테이션 주기 (분) |
| `SB_ROTATION_POSITION_USDT` | `200` | 로테이션 1종목 포지션 |
| `SB_ROTATION_MAX_TOTAL_USDT` | `1000` | 로테이션 총 최대 포지션 |
| `SB_ROTATION_STOP_LOSS` | `5.0` | 로테이션 손절 (%) |
| `SB_ROTATION_TAKE_PROFIT` | `15.0` | 로테이션 익절 (%) |
| `SB_USE_BNB_FEE` | `true` | BNB로 수수료 차감 |

### 두뇌·LLM 고급 설정

| 변수 | 기본값 | 용도 |
|---|---|---|
| `GEMINI_TEMPERATURE` | `0` | LLM 결정성 (0 = 완전 결정론, 변경 비권장) |
| `GEMINI_DAILY_CAP` | `50` | 일일 LLM 최대 호출 횟수 (초과 시 휴리스틱 fallback) |
| `GEMINI_LATENCY_BUDGET` | `30` | LLM 응답 대기 상한 (초) |
| `R2_DRIFT_THRESHOLD` | `0.05` | 거래소↔DB 잔고 허용 차이 비율 (5%) |
| `ZMQ_MAIN_BRAIN_HOST` | `127.0.0.1` | ZeroMQ 두뇌 소켓 호스트 |
| `ZMQ_MAIN_BRAIN_PORT` | `5555` | ZeroMQ 요청 포트 |
| `ZMQ_PUB_PORT` | `5556` | ZeroMQ 브로드캐스트 포트 |
| `ZMQ_HEARTBEAT_INTERVAL` | `30` | 하트비트 주기 (초) |
| `ZMQ_REQUEST_TIMEOUT` | `30000` | 요청 타임아웃 (ms) |
| `RAG_EMBEDDING_MODEL` | `text-embedding-004` | RAG 임베딩 모델 |
| `RAG_EMBEDDING_DIM` | `768` | 임베딩 차원 |
| `RAG_TOP_K` | `5` | RAG 검색 상위 K개 |

---

## 실행

### 에이전트 모드 (권장)

```bash
bash scripts/run_agents.sh
```

파이프라인: 데이터 병렬 수집 → ExternalDataAgent → Orchestrator (전략 전환·매매 판단) → 매매 실행 → 텔레그램 알림 → Supabase 기록.

시뮬레이션 모드로 실행하려면:

```bash
DRY_RUN=true bash scripts/run_agents.sh
```

### LLM 프롬프트 모드 (레거시)

```bash
bash scripts/run_analysis.sh 2>/dev/null | claude -p --dangerously-skip-permissions
```

Claude가 데이터를 보고 자연어 전략(`strategy.md`)을 해석해 매매 결정을 내린다.

### cron 자동화

```bash
bash scripts/setup_cron.sh install   # cron 등록 (4h / 8h / 12h / 24h 선택)
bash scripts/setup_cron.sh status    # 등록 상태 확인
bash scripts/setup_cron.sh remove    # cron 해제
```

`cron_run.sh`가 에이전트 모드 우선 실행, 실패 시 `claude -p` fallback.

### 단타 트레이더 (별도)

```bash
bash scripts/run_short_term_24h.sh
```

뉴스·급등락·고래 감지 3전략 기반 단기 매매.

### 변동성 돌파 전략

```bash
# .env 에서 BREAKOUT_ENABLED=true, BREAKOUT_DRY_RUN=false 설정 후
bash scripts/setup_breakout_cron.sh
```

Larry Williams 변동성 돌파 (K=0.7), 매일 10:00 KST 자동 매수·24h 후 매도.

### 버전 기록 (코드 수정 후 필수)

```bash
python scripts/version_manager.py log \
  --severity minor \
  --category feature \
  --summary "변경 요약" \
  --files "file1.py,file2.py" \
  --verified
```

| severity | 버전 범프 |
|---|---|
| `critical` / `major` | minor (x.**Y**.0) |
| `minor` / `patch` | patch (x.y.**Z**) |

---

## 안전장치

| 파라미터 / 장치 | 기본값 | 설명 |
|---|---|---|
| `DRY_RUN` | `true` | `true` = 분석만 (실매매 0). 실거래 전환은 `false` (사람 게이트) |
| `EMERGENCY_STOP` | `false` | `true` 설정 시 즉시 중지. **감독도 해제 불가**. DRY_RUN보다 먼저 검사 |
| `MAX_TRADE_AMOUNT` | `100000` KRW | 1회 매매 금액 절대 상한 (모든 경로 통과 후에도 클램프) |
| `MIN_TRADE_AMOUNT` | `5000` KRW | 1회 매수 금액 하한 (Upbit 최소 주문 기준) |
| `MAX_DAILY_TRADES` | `3` | 일 최대 매매 횟수 |
| `MIN_TRADE_INTERVAL_HOURS` | `4` | 매매 간 최소 간격 |
| `MAX_POSITION_RATIO` | `0.5` | 총자산 대비 최대 투자 비율 |
| 자동 긴급정지 | — | 4h −10% 급락·연속손절 5회+ 등 발동 시 강제 전량 매도+매수 차단. 해제 조건: 12h 경과 + 급락 종료 + 공포 완화 |
| Risk Gate | — | `GatedOrderRouter` 우회 불가. 결정론 항상-on |
| Kill Switch | MDD −15% → HALTED | 자동 전량청산 금지 (사람 confirm 후에만). out-of-band 물리 분리 |

**실전 자금 전환 조건** (자율 범위 밖):
- DRY_RUN 상태로 90일 무중단 운영
- Kill Switch / EMERGENCY_STOP / reconciliation 실발동 기록 보유
- 라이브 신호가 백테스트 분포 내에 있을 것
- 통과 후에도 극소액부터 단계적 투입

---

## 문서 안내

| 문서 | 내용 |
|---|---|
| [README.md](./README.md) | 사용자용 개요·의존성·실행법·안전장치 (이 문서) |
| [CODEMAP.md](./CODEMAP.md) | 코드 색인·디버깅 진입점 |
| [architecture.md](./architecture.md) | 목표 아키텍처·Phase 로드맵·내구성 요구사항 |
| [ARCHITECTURE-brain.md](./ARCHITECTURE-brain.md) | 두뇌 의사결정·LLM 라우팅·학습 루프 설계 |
| [CLAUDE.md](./CLAUDE.md) | 운영 기준·안전장치·에이전트 아키텍처 |
| [STUDY-ORCHESTRATION.md](./STUDY-ORCHESTRATION.md) | 자산별 스터디 세션 오케스트레이션 |
| [STUDY-KIT.md](./STUDY-KIT.md) | 각 연구 세션 작업 지시·감사 기준 |
| [study-research/AUDIT-GUIDE.md](./study-research/AUDIT-GUIDE.md) | 독립 감사 12축 가이드 |
| `study-research/_wire/indicator-ledger.md` | 지표 채택·기각·보류 이력 (재탐구 방지) |
| `study-research/_wire/cross-regime-ledger.md` | 자산 간 상관·국면별 관계 이력 |

---

## 데이터 소스

| 소스 | 용도 | 인증 |
|---|---|---|
| Upbit REST API | 코인 시세·지표·매매 실행 | API Key (JWT) |
| 바이낸스 Futures API | 롱숏비율·펀딩비·OI | 없음 (무료) |
| Alternative.me | 공포탐욕지수 (FGI) | 없음 (무료) |
| Tavily | 뉴스 검색 | API Key |
| Yahoo Finance | S&P500·DXY·금·유가·국채 | 없음 (무료) |
| FRED / ALFRED | 거시 지표 (PIT vintage) | 없음 (무료) |
| mempool.space | 고래 추적·거래소 입출금 | 없음 (무료) |
| CoinGecko | 커뮤니티 감성 | 없음 (무료) |
| CryptoCompare | 뉴스 감성·소셜 통계 | API Key |
| RSS 피드 (16개) | 크립토+매크로 뉴스 | 없음 |
| X(트위터) | 7계정 모니터링·키워드 검색 | X 계정 로그인 |
| Supabase (PostgreSQL) | 결정 기록·이력·학습 | Service Role Key |
| KIS (한국투자증권) | 주식 매매 실행 (모의 우선) | API Key |
| DART / EDGAR | 공시 PIT 펀더멘털 | 없음 (무료) |
| KRX | 유니버스·일별 PIT 구성 | 없음 (무료) |

---

## 개발 환경

- OS: Windows 11 Pro (Git Bash / PowerShell)
- Shell: Git Bash (Unix 경로 사용)
- 인코딩: UTF-8 (`PYTHONUTF8=1`)
- 줄 끝: CRLF (`git config core.autocrlf true` 권장)
