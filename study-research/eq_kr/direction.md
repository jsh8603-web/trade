# direction — eq_kr Phase 3.5 (R1+R2 종합, 2026-05-30)

> STUDY-KIT §2-1 산출. R1+R2+R0 round-2 자문폴백 (e-KJFS · 일본 TSE · KOSPI 집중도 · OSS · breadth) 종합.

## ① 이론 수집 방향

- **Korea discount 본질** = composition effect (e-KJFS 2025 KJFS 54-5 학술): R&D/CAPEX/Intangible pos p<0.01 / PPE/LnAge neg / G-score n.s. — 거버넌스 → PBR 무관. 성장산업 구조전환 필수.
- **일본 TSE 2024-01 reform anchor** = 2년 후 Prime PBR<1 27% (-23pt) + 자사주 급증. 한국 (2024-02 FSC 밸류업) 동기 → 2-3년 후 동등 baseline. 단 disclosure 품질 mixed (정책 fade 위험).
- **반도체 50% 집중 (2026-05)** = 한국 시장 본질. 삼성+SK하이닉스 KOSPI 50.44%. 9 of 10 stocks decline 동안 견인 = breadth divergence.
- **외국인 수급 가격 driver 1순위** = Roller-KOSPI 15세션 50조 매도, BTIG swift reversal 경고.
- **이론 정독 list**: Damodaran, Fama-French, Asness QMJ, Jegadeesh-Titman, BloombergNEF EV Outlook, LMC 자동차, 한은 금융안정보고서, 한국 학술 NCBI PMC11023228 (GARCH-MIDAS heterogeneous), arxiv 2401.00001 sector rotation, toraniko/skfolio OSS, JPX/FSA 일본 reform.

## ② 이론 검증 방향

- **AUDIT-GUIDE 12축** (8 핵심 + 4 신규) = 평가 SSOT. Hard-fail 코어 4 = B(실데이터) C(추적성) D(PIT) I(생존편향).
- **frame §M4 5게이트** (N≥24 / SE CI 0 비포함 / Power MDE>0.05 / FDR q<0.10 / OOS≥IS×0.5).
- **OSS**: toraniko (factor model, MIT numpy+polars) + skfolio (CombinatorialPurgedKFoldSplit = OOS 매핑).
- **regime cell**: Macro 4 (Reflation/Recovery/Overheat/Slowdown) × KRW 3 (강세/중립/약세) × 외국인 flow 3 (강매수/매도/중립) = 36 cell. N gate 강화 의무.
- **Tier 차등 분할**: T1 반도체 단독 (KOSPI 40%+, 500k subagent) / T2 자동차·금융·2차전지 (5-10%, 300k) / T3 8 산업 (2-5%, 150-200k).
- **PIT**: DART 공시일 + 45-90일 지연 / 가격 익일시가 / FRED first-release vintage / krx_universe.delisted 포함.
- **거래비용**: 한국 매도세 0.18-0.23% + 슬리피지 (왕복 0.3%+) 차감 후 alpha.
- **breadth 자체 정의**: `breadth_kospi = return(가중 KOSPI) - return(동등가중 KOSPI)`. 학술 baseline 부재 → tier 강등 가능.

## ③ 핵심 가설 12 (반증조건 포함)

| ID | 가설 | 측정 | 반증조건 |
|---|---|---|---|
| H1 | 외국인 순매수 → 대형 KOSPI t+5~20d return 양 선행 (★1순위 alpha) | foreign_net_buy z → Q5-Q1 Rank-IC | e-CUSUM baseline +0.05 단측 붕괴 |
| H2 | 밸류업 Index 편입 종목 re-rating (일본 baseline 2-3년) | 편입 종목 vs 매칭 CAR | 12M+ Rank-IC 평탄화 = 정책 fade |
| H3 | USDKRW × export_share 교호항 (수출주 양·내수주 음) | 종목 패널 회귀 β3 t-stat | β3 < 1.96 (name_specific 무효) |
| H4 | 반도체 cycle (DRAM yoy/$SMH) → fwd EPS lag 1-2Q | 반도체 sub IC lag-corr | lag-corr baseline 0.2 단측 붕괴 |
| H5 | 한국 모멘텀 약효 (12-1 IC < 0.03) | KOSPI/KOSDAQ 12-1 IC | IC ≥ US × 0.8 = 가설 기각 |
| H6 | KOSDAQ 개인 주도 = 단기 + / 중기 - 반전 | retail z 분위 t+5d vs t+20d return | 단기·중기 같은 부호 = 반전 무효 |
| H7 | HY OAS↑ → 외국인 매도 + KRW 약세 + 대형주 디레이팅 (3 동조) | 60D 회귀 + corr | 1+ 동조 깨짐 = credit_beta 채널 무효 |
| H8 | G-score → 가격 무관 (e-KJFS 학술 baseline 한국) | KCGS 등급 분위 12M fwd return | G 상위 outperform = 학술 반박 |
| ★H9 | breadth_kospi 음 = 반도체 dominance 단기 alpha (자체 정의) | breadth 시계열 IC | tier 강등 (학술 baseline 부재) |
| ★H10 | 일본 baseline 한국 적용 시차 2-3년 | 한국 Prime PBR<1 비율 yoy | 2년 후 -10pt 미달 = 시차 무효 |
| ★H11 | R&D·Intangible 종목 (Tier 3 AI tech·바이오) outperform (e-KJFS R&D 양 p<0.01) | R&D/TA quintile fwd return | 양극 무차이 = 학술 가설 한국 무효 |
| ★H12 | 외국인 flow regime × 산업 Tier 교호 (T1 효과 강) | regime × Tier cell Rank-IC | Tier 차등 무효 (모든 Tier 동일) |

각 가설 = Phase 5 산업 subagent 가 5게이트 통과 시 weight_rule_candidates 등록.
