---
tags: [type/validation, domain/inv, asset/bond, asset/cash, phase/study-2-3, hypothesis/H6]
date: 2026-05-30
study_id: bond_cash
hypothesis: H6 hy_oas_600bps_recession — HY OAS ≥ 600bps 진입 후 forward 12-18M bond-cash spread < 0
data-source: FRED API BAMLH0A0HYM2 + yfinance HYG/TLT/SHY/BIL (실데이터, 합성 0)
script: raw/_v2_analysis/run_validations.py (V1) + raw/_v2_analysis/results.json
result: 데이터 한계 발견 — full historical 미가용 → main 액션 필요
---

# V1. HY OAS 600bps Event Study (가설 H6)

## 검증 대상
가설 H6 (`hy_oas_600bps_recession`): HY OAS (BAMLH0A0HYM2) 가 600bps 이상 진입한 event 후 12~18개월 forward bond sleeve return − cash sleeve return < 0 (cash 우위 입증).

웹리서치 baseline (Round 3, Money365): 1996-2024 분석에서 600bps 돌파 → 12-18M 내 침체 ~85%.

## 데이터 실측
| 항목 | 값 |
|---|---|
| 시리즈 | BAMLH0A0HYM2 (ICE BofA US HY OAS) |
| 데이터 수신 | FRED REST API (api.stlouisfed.org, key 인증) |
| **n** | **786 obs** |
| **기간** | **2023-05-30 ~ 2026-05-28 (≈3년)** |
| 분포 | mean=3.25%, std=0.48, p50=3.15%, p95=4.26%, **max=4.69%** |
| **600bps 진입 event** | **0건** (전 기간 미돌파) |

## ★중요 발견: FRED BAMLH0A0HYM2 시계열 제한
- `fredapi` 와 직접 REST API 호출 둘 다 동일 결과: **count=794, 시작 2023-05-30**
- `observation_start=1996-12-01` 명시했으나 무시됨 (FRED 측 제한)
- 추정 원인: **ICE BofA index 라이센스 정책 변경** — historical 1996-12~2023-05 구간이 FRED 무료 endpoint 에서 비공개 전환된 것으로 보임 (정확한 사유는 ICE 공식 release note 추가 확인 필요)
- 우리 코드 (`fred_adapter.FRED_SERIES[BAMLH0A0HYM2]`) 도 동일 한계
- → 1996-12~2023-05 historical = main collector_plan 별도 확보 필요 (ICE 직접 라이센스 or 대체 source)

## 부분 검증 (가용 ETF panel)
600bps event 0건 → forward return panel 산출 불가. 단 ETF 가용성은 확인:
| ETF | 시작일 | n |
|---|---|---:|
| HYG | 2007-04-11 | 4815 |
| TLT | 2002-07~ | 5997 |
| SHY | 2002-07~ | 5997 |
| BIL | 2007-05~ | 4781 |

→ ETF 데이터는 풀 historical 가용. 만약 BAMLH0A0HYM2 historical 확보되면 즉시 event study 가능.

## 가설 H6 판정
- **상태**: **Inconclusive (데이터 한계)** — 검증 sample 에 600bps event 0건
- **반증 못 함, 지지도 못 함**
- 우회 검증 가능 (parc): 가용 3년 sample 의 *Z-score* spike (mean+2std ≈ 4.21%) 진입 event 로 가설 H7 (`hy_oas_widening_hyg_underperform`) 만 부분 검증 (별도 validation-hy-oas-spike.md 후속 작업 — 시간 제약으로 본 라운드 미작성)

## yaml 반영 (블록3/5)
- 블록3 relationships `credit_spread_hy_oas ↔ yield_10y_2y` prior_strength **0.55 유지** (검증 못 함, 변경 X)
- 블록5 confidence_hooks `hy_oas_credit_regime` 의 confirm/reject baseline_ic 사전등록 **보류** → 데이터 확보 후
- 블록6 collector_plan **신규 우선순위 1**: ICE BofA HY OAS 1996-12~2023-05 historical (대체 source 또는 main 라이센스)

## main 액션 요청
1. **BAMLH0A0HYM2 historical 확보 경로** 의사결정:
   - (a) ICE BofA 직접 라이센스 (유료)
   - (b) FRED 공식에 historical 비공개 확인 후 대체 시리즈 (BAMLC0A0CM = IG OAS, BAMLH0A1HYBB = HY-BB only 등)
   - (c) Bloomberg HY OAS / S&P U.S. HY Corporate Bond Index 등 outside source
2. 단순 alternative: **BAA10Y** (Moody's BAA - 10Y Tsy, 1986~) 는 풀 historical 가용 → IG 보완 시그널로 동시 사용 (이미 yaml block2 등록)
