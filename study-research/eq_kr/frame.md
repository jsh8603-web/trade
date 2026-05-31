# frame — eq_kr 산업별 sub-study 통일 계약 (v2, 2026-05-30)

> 본 frame 은 **12 산업 subagent (Tier 1 반도체 / Tier 2 자동차·금융·2차전지 / Tier 3 8 산업)** 가 따라야 할 통일 작업 계약.
> SSOT 우선순위: 본 frame.md v2 > AUDIT-GUIDE.md (★12축 평가 SSOT) > STUDY-KIT.md §3 (yaml 7블록).
> ⛔ **점추정 prior 박제 금지** · ⛔ **합성/시뮬 데이터 금지** · ⛔ **자문 그대로 코드화 금지** · ⛔ **single-source 단정** · ⛔ **small-N 단정** · ✅ **실측 분포 + 5게이트 + 반증가능**.
> ★ **v1 → v2 갱신 항목 (6)**: §1 12 산업 Tier 분류 / §3 Layer 2 외국인 flow base 0.20+ + 신지표 4 / §M3 regime 12→36 cell / §M4 #5 skfolio CPCV / §M (신규) toraniko baseline / §6 8축→12축 (AUDIT-GUIDE 인용).

## §0. 미션

산업별 sub-study 의 목적 = **"이 산업의 종목 forward return 과 가장 상관 높은 지표는 무엇인가, 그것은 어떤 조건 (regime · 사이클 · 수출 사이클) 에서 강해지나"** 를 **실측 분포 + 게이트 통과 여부** 로 보인다.

⛔ 다음을 하지 마라:
1. 자문 결과를 그대로 yaml 에 옮기기
2. 점추정 IC = 0.4 → base_weight = 0.4 직접 박기 (분포 + CI + 게이트 없이)
3. 합성 panel · random walk · 가상 ticker 로 IC 산출
4. single-source 단정 (1 학술 또는 1 자문만으로 "확정")
5. 통계적 power 무시한 small-N 단정 (월간 N < 24 cell 에서 "유의" 주장)

✅ 다음을 하라:
1. 본 frame 정독 → §1 universe 확인 → §5 산출 양식 8 파일 생성
2. 실제 Inv 수집기 (DART/KRX/FRED/FxStore) 적재 또는 외부 무료 소스 (DRAM·LMC·리튬 가격) 명시 스크랩
3. 5게이트 (§M4) 통과 항목만 weight_rules 후보 등록
4. 8축 self-audit (§6) 통과 후 보고

---

## §1. 산업 정의 (KRX/WICS 매핑, ★v2 Tier 차등)

★ 12 산업 Tier 차등 분할 (R1 자문 finding = 반도체 50% 집중 → 균등 분할 기각).

### Tier 1 — 단독 (KOSPI ≥40%, opus 1m 500k 토큰)

| 산업 | 시장 | WICS 대분류 후보 | 대표 ticker | KOSPI 가중 | subagent 책임 |
|---|---|---|---|---|---|
| **반도체** | KOSPI 주 | 반도체·반도체장비 | 005930(삼성전자) 000660(SK하이닉스) 042700(한미반도체) | ★50.44% (2026-05) | DRAM/HBM cycle + 외국인 flow + sub-cluster (메모리/파운드리/장비) 옵션 |

★ Tier 1 sub-cluster 옵션 = 메모리 / 파운드리 / 장비 별 dispatch (3 sub-subagent, 각 200k). 본 작업방 권고.

### Tier 2 — 중간 (각 5-10%, opus 1m 300k 토큰)

| 산업 | WICS 대분류 후보 | 대표 ticker | subagent 책임 |
|---|---|---|---|
| **자동차** | 자동차·자동차부품 | 005380(현대차) 000270(기아) 012330(현대모비스) | 글로벌 수요 + USDKRW + 반도체 공급 |
| **금융** | 은행·보험·증권 | 055550(신한지주) 105560(KB금융) 086790(하나금융) 316140(우리금융) | 금리커브 + NIM + 부동산 PF + ★밸류업 Index event study |
| **2차전지** | 전기제품·이차전지 | 373220(LG에너지솔루션) 006400(삼성SDI) 247540(에코프로비엠) 003670(포스코퓨처엠) | EV cycle + 원자재 + IRA |

### Tier 3 — 경량 (각 2-5%, opus 1m 150-200k 토큰)

| 산업 | WICS 대분류 후보 | 대표 ticker (예시) | subagent 책임 |
|---|---|---|---|
| **AI tech** | IT 서비스·소프트웨어·SI | 035420(NAVER) 035720(카카오) 251270(넷마블) | AI capex + B2B SaaS + 광고 cycle |
| **화학** | 화학·정밀화학 | 051910(LG화학) 011170(롯데케미칼) 009830(한화솔루션) | 유가 + 중국 PMI + 글로벌 spread |
| **정유** | 석유·가스 | 010950(S-Oil) 096770(SK이노베이션) | 정제 spread + 유가 + 한국 가솔린 수요 |
| **조선** | 조선·기자재 | 009540(HD한국조선해양) 010140(삼성중공업) 042660(한화오션) | LNG carrier + container cycle + 해양 plant |
| **바이오** | 제약·바이오 | 207940(삼성바이오로직스) 068270(셀트리온) 326030(SK바이오팜) | CMO capacity + 신약 pipeline + FDA 이벤트 |
| **통신** | 통신서비스 | 017670(SKT) 030200(KT) 032640(LG U+) | ARPU + 5G capex + 배당 수익률 |
| **철강** | 철강·금속 | 005490(POSCO홀딩스) 004020(현대제철) | 중국 수요 + 철광석 spread + 자동차 강판 |
| **소비재** | 음식료·생활용품·유통 | 097950(CJ제일제당) 003230(삼양식품) 023530(롯데쇼핑) | K-food 수출 + 내수 소비심리 + 환율 |

★ universe = **시점별 PIT 동적** (`KrxSectorProvider.get_sector_map(as_of, market)` 사용). 정적 ticker list 는 round-1 참고용만.

★ subagent 가 추가 sub-cluster 발견 시 (예: AI tech → SaaS/광고/게임) 라운드 1 에서 명시 후 사용.

---

## §2. 종속변수 y (정의 통일)

종목 forward return:
- y_5d = P[t+5d] / P[t] - 1 (단기)
- y_20d = P[t+20d] / P[t] - 1 (1개월, **메인 측정**)
- y_60d = P[t+60d] / P[t] - 1 (분기)
- y_1Q = 분기 forward return (펀더멘털 lag align)

조정:
- t = 거래일 (KRX calendar via FDR)
- 액면분할·병합 = 수정주가 (FDR 자동)
- 상폐 = krx_universe.delisted 포함 (생존편향 차단, return = 청산가 또는 -100%)
- 거래정지 = krx_universe `is_paused` flag → 해당 날짜 excluded from forward return

---

## §3. 독립변수 = 3 Layer

### Layer 1 — 종목 펀더멘털 (DART 적재, vintage_policy=point_in_time)
- valuation: PER, PBR, PCR, EV/EBITDA, 배당수익률
- quality: ROE, ROA, 영업이익률 + yoy 추세, 부채비율, FCF/매출
- revision: EPS yoy, 매출 yoy, OP margin yoy
- size: 시가총액 (KrxUniverseProvider)
- growth (★e-KJFS finding): R&D/총자산, CAPEX/총자산, 무형자산/총자산, PPE/총자산, LnAge

### Layer 2 — ★거시 critical 4종 + 신지표 4 후보 (v2 강화)

**기본 4종 (v1 유지, 의무)**:

| 지표 | 소스 | Inv 매핑 | v2 base_weight 권고 |
|---|---|---|---|
| **USDKRW** | `core/data/macro_market.py` FxStore PIT (선구축 완료) | level + yoy | 0.15-0.20 |
| **외국인 순매수** | `stock/data/krx_flows.py KrxForeignFlowProvider` + `data/krx_flow_snapshots.jsonl` | 종목별 일별 net buy + 산업 평균 | ★0.20+ **잠정** (v2.1 정정: v1 0.18 → 방향성 강 prior, R1 finding 기반 (Roller-KOSPI 15세션 50조 매도 episode 1건 2025-05 BTIG cited single-source + Chae-Yang 2007 KAR 학술 baseline). ★산업 subagent 5게이트 통과 검증 의무 — 미통과 시 v1 0.18 fallback. 단정 어휘 "1순위 driver" → "방향성 강 prior, 정량 magnitude 잠정") |
| **중국 credit impulse** | PBOC TSF yoy - GDP yoy / BIS quarterly / FRED 미존재 → **collector_plan 신규 의무** | 분기 level | 0.10-0.15 |
| **월간수출 + 반도체 cycle** | 관세청 수출입통계 (data.go.kr 무료) + DRAM 현물가 (DRAMeXchange 부분공개 / $SMH·$SOXX yoy proxy) | 월별 yoy | 0.15-0.20 |

**★v2 신지표 4 후보 (R1 finding, subagent 검증 후 채택)**:

| # | 지표 | 정의 | 소스 | tier 위험 |
|---|---|---|---|---|
| 1 | **breadth_kospi** | return(가중 KOSPI) - return(동등가중 KOSPI) | KRX 종가 자체계산 | ★학술 baseline 부재 → tier 강등 가능성 (자체 정의, 5게이트 통과 필수) |
| 2 | **MSCI cap 초과 flag** | 종목 시총 / KOSPI 시총 비율이 MSCI Korea cap 임계 초과 시 1 | MSCI 공시 + KRX 시총 | 이벤트성, event study 형식 권고 |
| 3 | **ETF leverage flow** | KODEX/TIGER leveraged ETF 일별 순매수 | KRX ETF flow | 산업별 mapping 가능 시만 채택 |
| 4 | **외국인 flow regime** | 외국인 순매수 28일 누계 z-score 기반 강매수/매도/중립 분류 | krx_flow_snapshots 자체 분류 | ★frame §M3 regime 36 cell 확장의 핵심 |

★ 신지표 4 채택 게이트 = 5게이트 (§M4) 통과 + 학술 baseline 존재 (없으면 structural prior tier 강등) + sub agent round-1 정당화.

### Layer 3 — 산업 특화 cycle 지표 (subagent 자율 추가, 산업당 5개 이내)

**Tier 1+2 (v1 유지)**:
- **반도체**: DRAM 현물가 yoy / NAND 가격 / HBM 수요 proxy / EUV 신기술 disclosure 이벤트 / 가동률 / 재고일수
- **2차전지**: 리튬·니켈·코발트 가격 yoy (LME) / 글로벌 EV 판매대수 (LMC) / IRA 보조금 정책 이벤트 / GWh 출하 / 미국 EV tax credit 변경
- **자동차**: 글로벌 신차 판매 (LMC) / 국내 신차 등록 (KAIDA) / 반도체 공급 정상화 proxy / 인센티브 / 미국 신차 SAAR
- **금융**: 10Y-2Y 커브 / 한은 기준금리 / NIM (분기) / LCR / 부동산 PF 부실률 (금감원) / 신용카드 연체율 / KOSPI 대비 outperformance / ★밸류업 Index 편입 event study (2024-02 FSC 시행)

**Tier 3 (v2 신규, subagent 후보)**:
- **AI tech**: hyperscaler capex yoy (AWS/Azure/GCP 합산) / NAVER·카카오 광고 매출 yoy / DAU/MAU / 게임 매출 분기 / DataCenter GPU 수요 proxy
- **화학**: 유가 (Brent/WTI level + yoy) / 중국 PMI / 글로벌 ethylene-naphtha spread / 중국 화학제품 수입가
- **정유**: 정제 spread (휘발유/디젤 - Dubai) / 미국 SPR 잔량 / 한국 가솔린 수요 / 정유공장 가동률
- **조선**: 글로벌 신조선 수주 (Clarkson) / LNG carrier 수주 / container 운임지수 (SCFI/CCFI) / 후판 가격 / 한국 조선 시장 점유율
- **바이오**: CMO 가동률 / FDA 승인 이벤트 / 글로벌 임상 진행 단계 / 신약 pipeline IND/NDA 이벤트 / USDKRW (수출 비중 높음)
- **통신**: ARPU yoy / 5G 가입자 점유율 / capex 회수 진척도 / 배당수익률 vs 국채 yield spread
- **철강**: 중국 철강 수요 (조강 생산 yoy) / 철광석 가격 (Platts) / 자동차 강판 가격 / 후판 가격
- **소비재**: 한국 소매판매 yoy / K-food 수출 yoy (특히 삼양식품·CJ) / 글로벌 (미국·중국) 시장 진출 매출 / USDKRW

★ Layer 3 지표는 subagent 가 round-1 에서 산업 cycle 이론으로 정당화 + round-2 에서 무료 소스 가용성 검증 후 채택.

---

## §4. 측정 방법 (4 방법 모두 의무)

### M1. 횡단면 Rank-IC (월간)
- 매월 말 산업 universe 종목 z-score(지표) → forward return y_20d Spearman corr.
- IC 시계열 → mean / SD / SE = SD/√N / t-stat / IR (IC mean / IC SD).
- ⛔ 점추정 박제 금지 → **IC 분포 (mean ± 1.96·SE) + N + t-stat** 함께 보고.
- 코드: `core/assume/weight_falsification.rank_ic(scores, returns)` 직접 호출.

### M2. 시계열 lag-corr (산업 panel 평균)
- 산업 평균 return yoy vs 거시·산업 cycle 지표 lag 0/1/3/6M corr.
- Granger 인과 (선택, 95% CI 보고).

### M3. Regime별 분해 (★v2 12 cell → 36 cell)
- Macro regime: Reflation / Recovery / Overheat / Slowdown (`core/brain/regime_to_weights.py` 의 `sleeve_regime_ids` 또는 자체 분류 — 분류 근거 명시).
- KRW regime: 약세 (USDKRW yoy > +5%) / 중립 / 강세 (yoy < -5%).
- ★외국인 flow regime (v2 신규): 강매수 (28일 누계 z-score > +1) / 매도 (z < -1) / 중립.
- **36 cell (4 × 3 × 3)** 별 IC 측정. 각 cell N 검정 (M4 §gate 1).
- ★ N gate 강화: 36 cell 분할 시 cell 당 N≥24 충족 어려움 → cell collapse 가이드 권고:
  - 1단계: 36 cell 전부 측정 → N<24 cell 식별
  - 2단계: 인접 cell merge (예: KRW 약세+중립 / Macro Recovery+Reflation) → 합산 N 확보
  - 3단계: 외국인 flow 3 cell 만 분해 (Macro 무관) → fallback (cell 수 3)
- ★ regime classifier source 명시 의무 (raw .py 재실행 가능, AUDIT-GUIDE 축 C 추적성).

### M4. ★★ Small-N 5게이트 (모든 finding 통과 의무)

| # | 게이트 | 통과 조건 | 보고 양식 |
|---|---|---|---|
| 1 | **N gate** | effective N (cell 별) ≥ 24 (월간 2년) | `N=42, pass` |
| 2 | **SE gate** | IC SE = IC SD / √N → 95% CI 가 0 비포함 | `IC=0.12 [0.04, 0.20], pass` |
| 3 | **Power gate** | 사전 power calculation → detectable IC > 0.05 (α=0.05, power=0.80) | `MDE=0.04, pass` |
| 4 | **FDR gate** | Benjamini-Hochberg q < 0.10 (지표 수 × cell 수 multiple test 보정) | `q=0.06, pass` |
| 5 | **OOS gate** (★v2 skfolio CPCV) | IS (2015-2022) / OOS (2023-2026) split → OOS IC ≥ IS IC × 0.5. ★★ **skfolio CombinatorialPurgedKFoldSplit** 직접 매핑 (sklearn walk-forward). embargo 기간 = 5d (forward return overlap 차단). | `IS=0.12 / OOS=0.08, pass (ratio=0.67), CPCV n_splits=10/embargo=5d` |

5게이트 모두 통과 → **확신 finding** (weight_rules 후보).
1-4 통과, 5 미달 → **탐색적 finding** (점추정 prior 박제 금지, "관찰" 만 기록).
1-2 통과, 3-4 미달 → **시사적 finding** (다음 라운드 추가 검증 필요).
1 미달 → **N 부족 finding** (cell 분해 자체 보류).

### M5. ★★ toraniko factor model baseline (v2 신규, OSS 채택)
- **toraniko** = MIT license, numpy + polars, Barra vein factor model (value · size · momentum). https://github.com/0xfdf/toraniko
- 목적: 산업별 종목 forward return 의 systematic factor exposure 분해 → idiosyncratic alpha 식별 (Layer 1 IC 의 confounder 제거).
- 적용: 각 산업 subagent 의 universe 종목에 daily factor return 추정 → Layer 1 종목 IC 측정 시 factor-neutral 조정 옵션 (raw IC + neutralized IC 병행 보고).
- 한계: Korean KOSPI 직접 사례 X → eq_kr first mover. factor universe 정의 (KOSPI200 baseline 권고) + risk model fit window (60d rolling) 명시 의무.
- ★ subagent 가 toraniko 적재 막힘 발견 시 fallback = pandas/numpy 자체 factor 회귀 (Fama-French style) 허용. 단 raw IC 와 ★factor-neutralized IC 둘 다 보고 의무.

---

## §5. 산출 양식 (subagent 표준)

각 산업 subagent 가 만들 **8 파일** (`industries/{industry}/` 디렉토리):

1. `round-1.md` — 이론 + 가설 5-10개 (반증조건 포함) + Layer 3 cycle 지표 후보 list
2. `round-N.md` — 자문/웹 추가 라운드 (필요 시, 자문 채널 경합 자제)
3. `theory-notes.md` — 산업 cycle 이론 정독 정리 (교과서·논문·증권사 in-depth, source URL 의무)
4. `validation-fundamental.md` — Layer 1 펀더멘털 IC (★raw + factor-neutralized 둘 다) + regime 36 cell 분해 + 5게이트 통과 표
5. `validation-macro.md` — Layer 2 거시 4종 + 신지표 4 후보 lag-corr + regime + 5게이트
6. `validation-industry.md` — Layer 3 산업 cycle 실측 + regime + 5게이트
7. `summary.yaml` — 통합용 sub-set (lens·indicators·relationships·weight_rules subset, 본 frame §7 양식)
8. `12axis-audit.md` (★v2, v1 `8axis-audit.md` 대체) — A~L 자가감사 (PASS/PARTIAL/FAIL + 근거, Hard-fail 4 = B·C·D·I 우선)

⚠️ 모든 finding 에 **source ID 매핑** 의무 (validation-*.md 의 어느 cell·어느 IC 인지). yaml 추적성 (12축 C).
⚠️ raw .py 재실행 가능 의무 (12축 B·C). validation-*.md 각 finding 마다 (a) 데이터 source path (b) 분석 코드 snippet (c) 결과 numeric 명시.

---

## §6. ★12축 self-audit (★v2: AUDIT-GUIDE.md 인용 layer)

> ★ 본 §6 = `D:/projects/Inv/study-research/AUDIT-GUIDE.md` 12축 application. AUDIT-GUIDE 가 SSOT. 본 frame 은 subagent 단위 application layer.
> ★ Phase 6 평가 subagent (opus 1m, **별 작업방**) 가 본 12축으로 산업별 PASS/PARTIAL/FAIL 판정. ⛔ supervisor 직접 평가 금지.
> ★★ **Hard-fail 코어 4** = B(실데이터) · C(추적성) · D(PIT) · I(생존편향). 한 축 FAIL = 산업 전체 보고 거부.

### 핵심 8축 (v1 유지)

| 축 | 점검 | Hard-fail? |
|---|---|---|
| **A 이론 실재성** | 인용 학술/리포트가 실재하나 (URL·DOI 확인) — 환각 검증 |  |
| **★B 실데이터 검증** | n / 기간 / p-value / Rank-IC 명시 — ⛔ 합성·시뮬 금지 (raw .py 재실행 가능) | ★ |
| **★C yaml 도출 추적성** | summary.yaml 각 weight rule 의 근거가 validation-*.md 의 어느 finding ID 인지 매핑 | ★ |
| **★D PIT·OOS** | vintage_policy 명시 + IS/OOS split 결과 (5게이트 §M4, CPCV) | ★ |
| **E 자문 비판 + 환각 cross-verify** | 자문 그대로 받지 않고 환각·논리 검증 (별 source 교차) |  |
| **F 반증가능 + 기각 기록** | 가설마다 반증조건 + 실측에서 기각된 가설 명시 |  |
| **G 검정력 한계** | 5게이트 통과/탈락 명시 + statistical power 한계 |  |
| **H 미해결 의문** | 다음 라운드/세션 위임 항목 |  |

### 신규 4축 (★v2.1 정정 2026-05-30 14:20, AUDIT-GUIDE.md §1 신규 4축 1:1 정합)

> ★ 직전 v2 박제 (factor neutralization · regime classifier · within-industry 직교성) 가 AUDIT-GUIDE 실제 신규 4축 (거래비용 · 다중검정 · cross-sleeve 통합 PSD) 와 명칭·내용 불일치 → methodology-audit-202605301410 Axis 1 FAIL 결과 즉시 정정.

| 축 | 점검 | Hard-fail? |
|---|---|---|
| **★I 데이터 무결성·생존편향** | krx_universe.delisted 포함 + ★티커변경 + 액면분할 (FDR 자동 수정주가) + ★PIT universe (시점별 inclusion 동적 = `KrxSectorProvider.get_sector_map(as_of)`) | ★ (생존편향 데이터 = hard-fail, 결과 약화 아니라 무효화) |
| **★J 경제적 유의성·거래비용·capacity** | 한국 거래세 0.18-0.23% + 슬리피지 왕복 0.3% 차감 후 alpha (+) / KOSDAQ 소형주 일평균거래대금 capacity 명시 / lens·정성 용도 허용 | ★ 조건부 (비용 차감 후 음수인데 alpha 주장 = hard / capacity = soft) |
| **★K 다중검정 보정** | 산업 × 지표 × regime cell 시도횟수 공시 (hard) + Deflated/Haircut Sharpe > 1.0 + Bonferroni / BH FDR 명시 (frame §M4 #4 FDR 게이트 보강) | ★ 조건부 (시도횟수 미공시 = hard / haircut 미적용 = tier 강등) |
| **L 통합 상관행렬 정합성** | (★Phase 7 supervisor 통합 시) cross-sleeve 공통인자 (USDKRW · 외국인 flow · HY OAS) 1회 계상 + 통합 행렬 PSD eigh-floor 차단 / regime별 안정성 (tail-correlation 위기 시 1 수렴) / Newey-West / Block Bootstrap SE 강제 | ★ 통합 단계 차단 (같은 베팅 중복 / PSD 깨짐) |

★ **factor neutralization** (toraniko raw + neutralized IC 둘 다 보고) = **frame §M5 별도 게이트** (axis J 가 아님, AUDIT-GUIDE 와 정합).
★ **regime classifier 추적성** = **Hard-fail C (yaml 도출 추적성) sub-요건으로 흡수** (regime 분류 코드 path + 재실행 가능).
★ **within-industry 직교성** (Layer 1/2/3 지표 간 partial-corr ≤ 0.7) = **frame §3 Layer 다중공선성 sub-요건** (axis L 통합 정합성과 별도, within-industry 만).

★ 각 축 PASS / PARTIAL / FAIL 등급 `12axis-audit.md` 명시. Hard-fail 4 (B·C·D·I) 한 축 FAIL = 산업 보고 거부 + 재dispatch (Phase 6 판정). Hard-fail 조건부 (J alpha 주장 / K 시도횟수 / L PSD) = 위반 시 즉시 차단.

---

## §7. summary.yaml 양식 (통합용 sub-set)

각 산업 subagent 가 산출할 sub-yaml (메인 eq_kr study_session.yaml 의 하위 archetype 으로 통합됨):

```yaml
industry: semi | battery | auto | financial
asset_scope: [equity.kr]
as_of: "2026-05-30"

# 본 산업의 lens (정성, 본 frame §0 미션 답 — 어떤 지표가 어떤 조건에서 강한가)
lens:
  pricing_principle: str       # 본 산업 가격 결정 원리 (산업 cycle + 펀더멘털 + 거시)
  cycle_reading: str           # cycle 국면 (early/mid/late/down) × 거시 regime 매트릭스
  estimation_note: str         # 2026-05 현 시점 cycle 위치 추정 (data 근거 명시)

# 본 산업에서 통과한 (5게이트) 지표
indicators_passed:
  - id: str
    layer: 1 | 2 | 3
    family: enum
    ic_mean: float
    ic_ci_95: [float, float]   # [low, high] — 0 비포함
    n_effective: int
    oos_ratio: float            # OOS IC / IS IC
    cell_breakdown:             # regime 분해
      - {macro_regime: str, krw_regime: str, ic: float, n: int}
    source_id: str              # validation-*.md cell ID

# 본 산업에서 통과한 (5게이트) 관계 (lag-corr 또는 partial-corr)
relationships_passed:
  - node_a: ref
    node_b: ref
    lag_months: int
    corr: float
    corr_ci_95: [float, float]
    conditioning_set: [ref]
    n: int
    source_id: str

# 본 산업의 weight rule 후보 (점추정 prior 박제 금지 — 분포 + 게이트 통과 기록)
weight_rule_candidates:
  - indicator_id: ref
    base_weight_range: [float, float]   # IC mean ± SE 비례 (점추정 X)
    modulate_by: [regime, industry, name_specific, cycle_phase]
    direction: str
    granularity: enum
    confidence: "high(5게이트) | medium(1-4) | low(1-2)"
    gate_status: {n: pass, se: pass, power: pass, fdr: pass, oos: pass}
    source_ids: [str, ...]              # validation-*.md ID 리스트

# 본 산업의 confidence hook (라이브 갱신 경로)
confidence_hooks:
  - hypothesis_id: str
    confirm_signal: str
    reject_signal: str
    accumulate_in: str         # core/assume/weight_falsification.* 경로
    feeds_weight: str          # 갱신 경로

# 본 산업 부족 자료
collector_plan_industry:
  - missing: str
    source: str
    priority: enum

# 본 산업 미해결 (8축 H)
open_questions:
  - str
```

---

## §8. ⛔ 절대 금지 (재확인)

1. ★ 점추정 prior 박제 금지 — IC 점추정 → base_weight 직접 X. **반드시 분포 + CI + 게이트**.
2. ★ 합성/시뮬 데이터 금지 — random walk · 합성 panel · 가상 ticker · monte carlo (검정력 분석 외) X. 실제 DART/KRX/FRED/FxStore PIT + 외부 무료 소스 명시.
3. ★ 자문 그대로 코드화 금지 — gemini/claude 답을 받아 yaml 직접 작성 X. 본 분석가 시각 비판·검증 후 채택.
4. ★ Single-source 단정 금지 — 1 출처만 "확정" X. **학술 + 실무 + 1차 데이터 3중**.
5. ★ Small-N 단정 금지 — cell N < 24 에서 "유의" 주장 X. M4 §gate 1 우선 통과 확인.

---

## §9. 통신·dispatch 규칙

- 본 frame.md = SSOT. 모든 subagent 가 정독 후 시작.
- subagent 산출 = `industries/{industry}/` 내 파일. 메인 `eq_kr/` 디렉토리 (study_session.yaml 등) 직접 쓰기 ★금지★.
- 막힘 발생: subagent → main(이 작업방 = eq_kr supervisor) 에게 보고 (final message 로 8축 PARTIAL/FAIL 명시).
- 자문 채널 = subagent 자체 WebSearch/WebFetch 폴백 또는 claude-web/gemini-web (단일 자문씩, 채널 경합 자제).
- ★ 통합 책임 = eq_kr supervisor (본 작업방). subagent 통합 후 메인 `study_session.yaml` 작성.
- ⛔ **analyst-level lens 다운그레이드 금지** (사용자 박제) — 산업 cycle 분석 lens 가 toraniko factor model 또는 시스템 인프라에 안 맞으면 **fallback** (raw + neutralized IC 둘 다 보고, pandas/numpy 자체 factor 회귀 등) 또는 supervisor 에 **파이프라인 업그레이드 요청** (evaluation-axes §4 yaml `system_fit.upgrade_plan`). lens 깎으면 ★Phase 6 평가 FAIL.

---

## §10. 진행 체크리스트 (subagent 자가 점검)

- [ ] 본 frame.md v2 정독 (§0~§11 전부, 특히 §1 Tier / §3 신지표 / §4 M3·M4·M5 / §6 12축)
- [ ] §1 산업 universe 확인 + sub-cluster 추가 여부 결정 (Tier 1 반도체 = 메모리/파운드리/장비 옵션)
- [ ] §3 Layer 2 신지표 4 후보 채택 여부 + Layer 3 산업 cycle 지표 후보 list (이론 정당화 + 무료 소스)
- [ ] round-1.md 작성 (가설 5-10개 + 반증조건)
- [ ] Layer 1/2/3 별 실측 (Inv 수집기 + 외부 스크랩, ★raw + factor-neutralized 둘 다)
- [ ] M3 regime 36 cell 분해 (N gate 검정 + cell collapse fallback)
- [ ] M5 toraniko factor model baseline (적재 또는 fallback)
- [ ] 5게이트 통과 표 (validation-*.md, #5 = skfolio CPCV)
- [ ] summary.yaml 작성 (점추정 prior 박제 X, 분포·CI·게이트 기록)
- [ ] 12축 self-audit (12axis-audit.md, PASS/PARTIAL/FAIL 등급, Hard-fail 4 = B·C·D·I 우선)
- [ ] eq_kr supervisor 에 final message 보고 (★본문 ctx inject 회피 — industries/{name}/ 직접 박제, final message 는 요약만)

---

## §11. 진행 일정 가이드 (subagent 참고)

- 라운드 1 (이론·가설): 1-2 자문 호출 + theory-notes.md + round-1.md
- 라운드 2 (실측 준비): Inv 수집기 적재 점검 + 외부 스크랩 PoC + toraniko 적재
- 라운드 3 (실측): Layer 1/2/3 validation-*.md + 5게이트 + M3 36 cell + M5 factor neutralize
- 라운드 4 (통합·자가감사): summary.yaml + 12axis-audit.md (Hard-fail 4 우선)
- 라운드 5 (보고): eq_kr supervisor 에 final message

총 예상 (★Tier 차등, v2):
- **Tier 1 반도체**: 500k 토큰 (단독, sub-cluster 옵션 시 3 sub-subagent 각 200k)
- **Tier 2 자동차·금융·2차전지**: 300k 토큰 × 3 = 900k
- **Tier 3 8 산업**: 150-200k 토큰 × 8 = 1.2-1.6M
- **합계**: 2.6-3.0M 토큰 (12 산업 병렬 dispatch, run_in_background=true)

---

> frame v2 — 2026-05-30 갱신 (v1 → v2 6 항목: §1 Tier·§3 신지표 4·§M3 36 cell·§M4 #5 CPCV·§M5 toraniko·§6 12축).
> subagent 가 미흡 발견 시 supervisor 에 frame 보강 요청 (frame v2.1 갱신 후 재dispatch).
