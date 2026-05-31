# round-1 — eq_kr 방향성 자문 라운드 1 (2026-05-30)

> 본 라운드 = **자체 전문 애널리스트 능동 분석** + **WebSearch 1회 학술/실무 그라운딩**.
> 자문 스킬(/gemini-web · /claude-web) = 라운드 2 부터 사용 (9 세션 동시 자문 채널 경합 자제 지시 준수).
> 산출: round-1.md(본 파일). 다음 산출: round-2.md, ..., direction.md.

## 0. 라운드 1 질문 설계 (자기완결 brief)

```
[Q] 한국 상장주식(eq_kr, KOSPI+KOSDAQ 종목 단위) 알파 분석을 위해:
  ① 어떤 이론·교과서·리포트를 정독해야 하나 (수집 방향)
  ② 그 이론을 우리 수집기 데이터(DART·KRX·외국인 flow·FRED·FX)로 어떻게 시계열 검증하나 (검증 방향)
  ③ 검증할 핵심 가설 초안 + 각 가설의 반증조건은 무엇인가
```

## 1. 라운드 1 입력 (출처)

- **WebSearch 1회** (query: "Korean equity Korea discount value-up program 2024 2025 corporate governance low PBR academic empirical")
  - raw: `~/.claude/docs/archive/research-raw/eq-kr-korea-discount-value-up-native-20260530.txt`
  - memory: `~/.claude/memory/research/eq-kr-korea-discount-value-up.md`
- **본 분석가 (eq_kr 담당) 능동 분석** — 한국 시장 미시구조·정설·실무 지식 + Inv 시스템 인프라(stock/data, regime_to_weights, weight_card) 사실 점검 결과
- **v1 산출 (raw/v1-superseded/study_session.yaml)** — 참고용 (사용자 지시: 폐기 X)
- **eq_us_cyclical 본보기** — 다른 작업방 구조 참조

## 2. ① 이론 수집 방향 (초안)

### A. 일반 가격결정 이론 (모든 주식 공통 — 한국 적용 시 caveat 강조)

| 영역 | 정독 대상 |
|---|---|
| DCF/멀티플 분해 | Damodaran, *Investment Valuation* — 한국 적용 시 KRP(Korea Risk Premium) overlay |
| 횡단면 팩터 | Fama-French (1992, 2015) HML·SMB·QMJ·UMD. Asness QMJ(2014). Frazzini-Pedersen BAB(2014). |
| 모멘텀·반전 | Jegadeesh-Titman(1993). George-Hwang(2004) 52-week high. Lehmann(1990) short-term reversal — **한국 단기 반전 강함 정설** |
| 회계품질 | Sloan(1996) accruals. Piotroski F-score(2000). |
| 시장미시구조 | O'Hara *Market Microstructure Theory*. Korea-specific = 외국인 주도 가격형성 (Chae-Yang 2007 KAR 등 국내 학술) |

### B. 한국 특수 이론·정책 (한국 시장 본질)

| 영역 | 정독 대상 | 핵심 질문 |
|---|---|---|
| Korea discount 학술 | e-KJFS 2025 KJFS 54-5 ([DOI 10.26845](https://www.e-kjfs.org/journal/view.php?doi=10.26845/KJFS.2025.10.54.5.371)). 한국재무학회 KFA 저널. | 거버넌스·payout·성장성 중 진짜 driver |
| 정책 anchor (밸류업) | FSC "기업 밸류업 프로그램" 2024-02 발표, KRX Korea Value-Up Index 2024-09 출시. Wellington/Morgan Stanley/AMRO reports. | 정책 모멘텀 vs 일본 사례(2014~) 비교 |
| 거버넌스 할인 | 한국기업지배구조원(KCGS) 등급 vs 가격 / Jang-Kim 학술 (chaebol 할인) | 거버넌스 → 가격 인과 채널 |
| 외국인 수급 | 한국증권학회 학술, Kim-Wei(2002), Chae-Yang(2007 KAR) | 외국인 = 정보거래자 가설 강도 |
| 반도체 cycle | DRAMeXchange/TrendForce 메모리 cycle reports. SK증권·삼성증권 반도체 in-depth | KOSPI 이익의 ~25% (반도체 2사) → 종목 분석 ≠ KOSPI 평균 |
| 자동차·조선·화학 | 한국자동차산업협회/Clarksons/석화협회 + 증권사 in-depth | 글로벌 수요·원자재 cycle 연동 |

### C. 한국 시장 구조 이론 (제도·환경)

| 영역 | 정독 대상 |
|---|---|
| KOSPI/KOSDAQ 분절 | KRX 시장구조 보고서. KOSDAQ 개인 비중·테마 행태 학술 |
| 공매도 규제 레짐 | 금감원/KRX 공매도 통계 (2020-2021/2023-2024 부분 금지) → 백테스트 구간 분할 필수 |
| FX 의존성 | USDKRW 정책 (한은) + 수출비중. Carry trade 환경 (BOJ-FED 차) |

### ⚠️ ① 의 빈틈 (라운드 2 자문 필요)
- 한국 학술 1차 출처 (e-KJFS 본문 PDF) 직접 정독 필요 — round-2 WebFetch.
- KCGS 거버넌스 등급 vs 학술 결과 충돌 검증 — round-2/3.
- 일본 밸류업(2014 코퍼레이트 거버넌스 코드) 사례 한국 적용 가능성 — round-2 자문.

## 3. ② 이론 검증 방향 (시계열 검증 방법)

### Inv 수집기 가용 데이터 (사실 점검 결과)

| 데이터 | 위치 | 한국 적용 |
|---|---|---|
| 유니버스/상폐 | `stock/data/krx_universe.py` + `data/krx_snapshots.jsonl` | ✅ PIT 재구성 |
| 업종(WICS) | `stock/data/krx_flows.py KrxSectorProvider` + `krx_sector_snapshots.jsonl` | ✅ 적재중 |
| 외국인 순매수 | `stock/data/krx_flows.py KrxForeignFlowProvider` + `krx_flow_snapshots.jsonl` | ✅ 일별 PIT |
| 펀더멘털 | `stock/data/dart_provider.py DartXbrlProvider` | ⚠️ DART_API_KEY 부재 시 graceful empty |
| 가격 OHLCV | FDR (한국 calendar 포함) | ✅ |
| USDKRW | `core/data/macro_market.py` FxStore PIT | ✅ 선구축 |
| 거시 (FRED·HY OAS·real rate) | `core/brain/fred_adapter.py` | ✅ |

### 시계열 검증 방법 (지표·가설별 매핑)

1. **횡단면 IC**: 매 리밸런싱 시점 (월/주) z-score(지표) ↔ forward return(1m/3m) Spearman Rank-IC.
   - 코드: `core/assume/weight_falsification.rank_ic(scores, returns)` 직접 호출.
2. **Regime 별 partial-corr**: regime label(Reflation/Recovery/Overheat/Slowdown × KR-USD overlay) 분할 → `core/structure/conditional_correlation.RegimeGlasso.fit(X, regime_ids)`. ★main 권고 = "전체 적합 대신 상관·partial-corr 만 먼저" → `np.corrcoef` + `np.linalg.inv` 로 partial-corr 직접 산출 1차.
3. **외국인 flow → 가격 lag 회귀**: foreign_net_buy(t) → return(t+1, t+5, t+20) OLS lag, t-stat + IC.
4. **밸류업 event study**: 공시일(t=0) ± 60d CAR(누적초과수익) vs 매칭 종목군. 1차 시점·표본 정의가 핵심.
5. **USDKRW × 수출비중 교호항**: return = α + β1·USDKRW + β2·export_share + β3·(USDKRW × export_share). β3 의 유의성 = 교호항 alpha.
6. **반도체 cycle proxy 검증**: DRAM 현물가 yoy (DRAMeXchange 또는 $SMH proxy) → semi sub-sector fwd EPS revision lag-corr.
7. **공매도 레짐 분할**: 부분 금지 기간(2020-2021/2023-2024) vs 정상 기간 각 IC 분리 측정 — 레짐 의존성 확인.

### 무거운 분석 회피 (main 권고)
- ⛔ RegimeGlasso 전체 적합 = 컴퓨트 무거움.
- ✅ 1차 산출 = 상관행렬 + regime별 partial-corr (numpy 직접) + IC 시계열.
- Bash python 으로 직접 실행, 결과만 수집.

### ⚠️ ② 의 빈틈 (라운드 2 자문 필요)
- e-KJFS 학술과 실무 reports 충돌(거버넌스↔PBR) 을 어느 데이터로 결정적 판정?
- 한국 컨센서스 추정(earnings revision) 무료 소스 — Naver Finance 스크랩 가능성·신뢰도.
- 반도체 cycle proxy 의 한국 종목 IC 가 일반 모멘텀보다 강한지 — 검증 디자인 정밀화.

## 4. ③ 핵심 가설 초안 (반증조건 포함)

> 각 가설 형식: **(가설) / (예측 부호) / (측정 방법) / (반증조건 — falsifier)**

### H1. 외국인 순매수 1순위 alpha (대형 KOSPI 한정)
- 가설: foreign_net_buy(t) 가 KOSPI 대형주(시총 top 50) 의 forward return(t+1~t+20)에 양의 선행성.
- 측정: 일별 외국인 순매수 z-score → 5분위 long-short return, Rank-IC.
- 반증: Q5-Q1 long-short Rank-IC e-CUSUM 이 baseline +0.05 아래 단측 붕괴 (`weight_falsification.score_ic_breakdown_eprocess`).
- ⚠️ KOSDAQ 소형은 외국인 비중 낮음 → 본 가설은 sleeve(KOSPI 대형) 한정.

### H2. ★학술-실무 충돌 가설: 밸류업 = governance 가 아니라 growth 채널
- 가설(학술 e-KJFS 2025): Value-Up Index 편입 종목의 alpha 는 **거버넌스 개선이 아니라 성장성 신호** 가 driver.
- 측정: 편입 종목 vs 매칭(시총·산업·ROE) 종목군 CAR + 성장성 지표(fwd EPS growth) vs 거버넌스 등급(KCGS) 의 분해.
- 반증 (① 학술 가설 반증): CAR 차이가 거버넌스 등급 quintile 에 유의 → 거버넌스 채널 살아있음.
- 반증 (② 실무 가설 반증): payout(배당+자사주) 증가 종목의 PBR 변화 무의미 + Rank-IC 0 근처.
- ⚠️ **두 가설 양립 가능 — 시점·표본 분리 측정**: 학술 표본 (정책 시행 전) vs 정책 이후 (2024-2025) 분리.

### H3. USDKRW × 수출비중 교호항 (name_specific alpha)
- 가설: 종목 forward return = β·USDKRW + γ·(USDKRW × export_share), γ > 0 (수출주는 KRW 약세 호재).
- 측정: 종목 단위 패널 회귀 + interactions 항 t-stat. fixed effect: 종목·시점.
- 반증: γ t-stat < 1.96 또는 산업 평균 effect 만 살아있음 (name_specific 무효 → ticker→industry 강등).

### H4. 반도체 cycle proxy → 반도체 sub-sector EPS lead
- 가설: DRAM 현물가 yoy(t) → 반도체 sub-sector fwd EPS yoy(t+1~t+2 quarter) 정의 lead 관계.
- 측정: DRAMeXchange/$SMH yoy → SK하이닉스·삼성전자(+전기전자 sub) fwd EPS yoy 의 lag-corr (1Q, 2Q).
- 반증: lag-corr 의 baseline 0.2 아래 e-CUSUM 단측 붕괴 (반도체 sub-sector 한정).

### H5. 한국 모멘텀 약효 + 단기 반전 (price_mom_12_1 base 낮춤)
- 가설: 12-1 가격 모멘텀 Rank-IC = 한국이 US 대비 약함 (50~60% 수준), 1M 미skip 시 음의 IC (반전).
- 측정: KOSPI/KOSDAQ 각 sleeve 에 12-1 IC vs 12-0 IC 측정. US (eq_us_cyclical) 비교 baseline.
- 반증: 한국 12-1 IC ≥ US IC × 0.8 → 모멘텀 약효 가설 기각, base 상향.

### H6. KOSDAQ 개인 주도 = 모멘텀/테마 + 반전 동반
- 가설: KOSDAQ 개인 순매수 양 종목 = 단기(t+5d) 양 alpha + 중기(t+20d~) 음 alpha (반전).
- 측정: 개인 순매수 z 분위별 t+5d/t+20d return 분포. KOSPI 대조군.
- 반증: KOSDAQ 단기·중기 모두 같은 부호 → 반전 메커니즘 무효.

### H7. 글로벌 risk-off → 외국인 매도 + KRW 약세 + 한국 종목 디레이팅 동반
- 가설: HY OAS(t) ↑ → foreign_net_buy(t,t+5) 음 + USDKRW ↑ + KOSPI 대형주 return 음. 셋이 동시에 움직임.
- 측정: HY OAS rolling 60D 회귀 with 3 dependent vars + 상관 동조도.
- 반증: 셋 중 하나라도 동조 깨짐 (특히 외국인-가격 lag) → credit_beta 채널 무효.

### H8 (탐색적). 거버넌스 등급 → 가격 무관 (학술과 일치)
- 가설: KCGS ESG-G 등급 quintile 별 fwd return 차이 무의미.
- 측정: KCGS 등급 (라이센스 가용 시) 분위별 12M 후행 return 평균 + IC.
- 반증: G 등급 상위가 outperform → 거버넌스 → 가격 인과 존재 (학술 반박).
- ⚠️ 데이터 부재 (KCGS 라이센스 필요) — collector_plan D4. 가설은 등록 후 데이터 도착 시 검증.

### ⚠️ ③ 의 빈틈 (라운드 2/3 자문 필요)
- H2 (학술-실무 충돌) 해결 = 정책 시행 전후 시점 분리가 핵심 — 자문 1: e-KJFS 표본 기간 확인 + 정책 후 데이터 재측정 의견.
- H4 (반도체 cycle) — DRAM 현물가 무료 시계열 가용성·실제 lag (1Q? 2Q?) 자문 필요.
- H8 (거버넌스) — KCGS 대체 무료 거버넌스 proxy (이사회 독립성 공시 / 지배구조 보고서) 가능성.

## 5. 라운드 1 자기 점검 — 빈틈 정리 (다음 라운드 질문 입력)

| # | 빈틈 | 라운드 2 자문 채널 |
|---|---|---|
| 1 | e-KJFS 학술 표본 기간 + 정책 후 재측정 가능성 | /claude-web (학술 본문 직접 검토) |
| 2 | 일본 밸류업 사례(2014~) 한국 적용성 | /gemini-web (글로벌 비교 시각) |
| 3 | 거버넌스 → 가격 인과 채널 (학술 vs 실무 충돌 해결) | /claude-web + /gemini-web 양쪽 |
| 4 | DRAM 현물가 무료 시계열·lag 측정 디자인 | WebSearch 폴백 가능 (DRAMeXchange 공개 범위) |
| 5 | 한국 컨센서스 (Naver Finance) 스크랩 신뢰도 | WebSearch 폴백 |
| 6 | KOSDAQ 개인 행태 학술 reference | /gemini-web (한국 학술 검색) |

## 6. 라운드 1 결론·다음 단계

- ①②③ 1차 초안 완성. 8개 가설 + 반증조건 명시.
- **수렴 미달** — 학술-실무 충돌(H2), DRAM proxy(H4), 거버넌스(H8) 셋이 라운드 2/3 자문 필요.
- 라운드 2 권장 = `/claude-web` 단독 1회 (학술 본문 검토 중심), 자문 채널 경합 자제.
- 라운드 3 권장 = `/gemini-web` 단독 1회 (일본 사례·KOSDAQ 학술).
- 라운드 4 = 두 자문 응답 비교 + WebSearch 폴백 잔여 빈틈 메우기.
- 수렴 판정 후 direction.md 작성.

## 7. 라운드 1 산출물

- 본 파일: `raw/round-1.md` (이 문서)
- WebSearch raw: `~/.claude/docs/archive/research-raw/eq-kr-korea-discount-value-up-native-20260530.txt`
- WebSearch memory: `~/.claude/memory/research/eq-kr-korea-discount-value-up.md`
- MEMORY 인덱스: `~/.claude/memory/MEMORY.md` 에 한 줄 추가 (별 작업)

⚠️ 본 라운드는 본 분석가 능동 분석 비중 높음. 자문 채널이 라운드 2 부터 검증·반박·보완 수행. 수렴 후 direction.md.
