---
tags: [type/validation, study/eq_us_cyclical, topic/merit-regional-fed-diffusion]
date: 2026-06-01
study_id: eq_us_cyclical
phase: "merit 후속 — credential probe 발견 지역연준 diffusion 신규주문(ISM 50-기준 포맷 무료 근접) forward 예측력 검증"
script: raw/validation-merit-regional-fed-diffusion.py
output_json: raw/validation-merit-regional-fed-diffusion.json
fetch_script: raw/fetch_regional_fed.py
pit_probe: raw/regional-fed-pit-probe.json
data_integrity: "합성·시뮬 無. FRED API 실데이터(NOCDISA066MSFRBNY/NOCDFSA066MSFRBPHI + DGORDER 참조). fetch 실패 raise."
verdict_overall: "지역연준 신규주문 → SOXX forward 음(-) = ★유일 Bonferroni 생존(2/84). 단 적시성(당월 발표) 이 census DGORDER→XLE 대비 XLE 예측 우위로는 이어지지 X — 다른 관계 발견(SOXX 음)이지 DGORDER→XLE 개선 X. PARTIAL CONFIRMED(SOXX) / DGORDER→XLE 적시성 우위 부정."
---

# merit 후속 — 지역연준 diffusion 신규주문 forward 예측력 검증

> credential probe(`commodity/raw/credential-free-substitute-probe-20260601.md` §4-B): ISM 신규주문(유료) 무료 대체로 **지역연준 diffusion 신규주문** 발견 — Empire State `NOCDISA066MSFRBNY`(2001-07~) + Philly `NOCDFSA066MSFRBPHI`(1968-05~). diffusion index = ISM 50-기준선 포맷에 가장 근접(0-centered, ±=확장/수축). 당월 발표라 census 신규주문(56~64d 시차)보다 적시.
> 본 검증 = 그 forward 예측력 실측 + **census DGORDER→XLE(기존 최강 후보) 대비 적시성 우위 여부** 판정. 방법 = `validation-merit-cyclical-leading.py` 와 동일.

## 데이터 coverage (§1.1 의무)

- **종속**: SOXX/XLB/XLI/XLE 월간 log-return. yfinance `sector_etf_close.csv`. 월말 2000-01-31 ~ 2026-05-31 (XLE/XLB/XLI n=317월, SOXX inception 2001-07 → join ~295월).
- **선행 후보** (FRED, 무료):
  | 후보 | series | 변환 | n(월) | 발표시차(ALFRED median) |
  |---|---|---|---|---|
  | Empire 신규주문 | NOCDISA066MSFRBNY | level / 12m-z | 299 / 288 | **14d** (min14/max17) |
  | Philly 신규주문 | NOCDFSA066MSFRBPHI | level / 12m-z | 697 / 686 | **17d** (min14/max20) |
  | Composite(평균) | (Empire+Philly)/2 | level / 12m-z | 299 / 288 | 17d(느린쪽=Philly) |
  | DGORDER_yoy (참조) | 내구재 신규주문 census | yoy | 399 | **56d** (기존 최강) |
- ★적시성 실측: ALFRED first-release probe(`regional-fed-pit-probe.json`) = 지역연준 **median 14~17d** vs census DGORDER **56d**. 지역연준이 약 40~42일 더 빠름 — diffusion 은 survey 월 중순 발표.
- 신규 fetch = `fetch_regional_fed.py`. 기존 DGORDER = cached(merit 단계).

## ★PIT — lookahead 정렬 (§1.3, eq_intl credit 재발 방지)

- **LIVE**: signal 을 first-release 가능일(기간말 + median 발표시차)로 shift, forward return 은 그 이후 매칭.
- **NAIVE**: survey 기간 정렬(발표 전 사용 = lookahead-prone). 양측 보고로 착시 정량.
- 지역연준 diffusion = 발표시차 14~17d 로 매우 짧음 → LIVE/NAIVE 차이 census 보다 작음(적시성의 부수효과).

## spec ↔ code 1:1 verify (§1.3)

- Spec "diffusion level/z 가 향후 k=1/3/6m 선도수익 예측" → Code `fwd = ret_m.rolling(k).sum().shift(-k)` (forward k-month sum). PASS.
- Spec "동월 co-move" → Code k=0 = `ret_m[target]` 동월. PASS.
- Spec "live PIT" → Code signal index = `(period_end + pub_lag).MonthEnd`, forward return 그 이후. PASS.
- transform: diffusion 은 이미 0-centered → **level** 직접 + own-history **12m rolling z**(regime-relative momentum) 두 변형.
- ADF: `adfuller(regression='c', autolag='AIC')` — 7/7 후보 I(0) stationary(level/z 모두 p<0.01, §1.7-A 통과). spurious 회귀 risk 없음.
- t-stat: rank-IC Newey-West HAC(overlapping → `maxlags=nw_lag+(k-1)`, §1.4). CI: block bootstrap(block=max(k,6), B=3000, §1.4).

## 결과 (LIVE PIT, rank-IC, n/p/95%CI)

★별표 = p<0.05 AND block-boot CI 비-cross-zero. **다중비교 보정 전(m=84).**

### ★SOXX — Empire 신규주문(level) = forward **음(-)** 예측 (유일 Bonferroni 생존)
| 후보·k | IC | NW t | p | n | 95% CI(block-boot) | cross0 |
|---|---|---|---|---|---|---|
| Empire_lvl → SOXX k=1 | -0.11 | -2.2 | 0.028 | ~294 | — | no |
| **Empire_lvl → SOXX k=3** | **-0.25** | -3.6 | **0.0003** | ~295 | [-0.391, -0.089] | no |
| **Empire_lvl → SOXX k=6** | **-0.30** | -3.9 | **0.0001** | ~295 | [-0.468, -0.125] | no |
| Composite_lvl → SOXX k=6 | -0.265 | -3.0 | 0.0027 | ~295 | [-0.437, -0.074] | no |

- 해석(★hedge): Empire State 신규주문 diffusion level ↑ → SOXX(반도체) 향후 3~6m **약세** 방향성. late-cycle 과열 reverse 가설과 정합(신규주문 고점 = 사이클 정점 근처 → 반도체 mean-reversion). 단 단일 지역(NY) 한정, 인과 미확정.
- naive k=3 -0.20 → live -0.25 (오히려 강화, 발표시차 짧아 착시 미미). revised-vintage 인공물 아님.
- half-split OOS k=3: Empire→SOXX h1 -0.26/h2 -0.17 = **부호 일치 MATCH**(both>0.1). Composite→SOXX h1 -0.30/h2 -0.14 MATCH. → OOS 일관 음부호.

### ★XLE — census DGORDER_yoy 가 여전히 우위, 지역연준은 약
| 후보·k=6 | IC | NW t | p | live cross0 |
|---|---|---|---|---|
| **DGORDER_yoy → XLE** | **+0.31** | +3.16 | 0.0016 | no |
| Empire_lvl → XLE | +0.16 | +1.56 | 0.12 | (약) |
| Philly_lvl → XLE | +0.08 | +0.69 | 0.49 | (무) |
| Composite_lvl → XLE | +0.12 | +1.04 | 0.30 | (무) |

- ★**적시성 우위 부정**: 지역연준이 40여일 더 빠름에도 XLE forward 예측은 census DGORDER 가 압도(k=6 +0.31/t=3.16 vs 지역연준 전부 |t|<1.6 비유의). 적시성≠예측력. 지역연준 신규주문은 XLE(에너지) 수요 모멘텀 채널을 census 만큼 담지 못함(지역 mfg 한정, 에너지 수요 대표성 약).

### co-move / 비유의
- z12 변형(Empire/Philly/Composite) = 전 섹터·전 horizon 거의 비유의(|t|<1.5). own-history z 가 level diffusion 보다 forward 신호 약 → **level 이 우월**.
- 지역연준 → XLB/XLI: 단발 음부호(Philly_lvl→XLB k=3 -0.16 p<0.05, Composite_lvl→XLI k=6 -0.22) — SOXX 와 동방향(신규주문↑→cyclical core 향후 약세)이나 Bonferroni 미생존.
- DGORDER_yoy → SOXX/XLB/XLI = 전부 비유의(XLE 전용 신호 재확인).

## ★다중비교 보정 (§1.5, K축)

- m = **84** forward predictive 비교(7후보 × 4섹터 × 3 horizon, LIVE k>0).
- Bonferroni α = 0.05/84 = 0.00060 → **생존 2/84**:
  - `Empire_lvl → SOXX k=3` p=0.0003
  - `Empire_lvl → SOXX k=6` p=0.0001
- BH-FDR q=0.05 crit p=0.00274 → **생존 5/84**: 위 2 + `Composite_lvl→SOXX k=6`(p=0.0027) + `DGORDER_yoy→XLE k=1`(p=0.0027) + `DGORDER_yoy→XLE k=6`(p=0.0016).
- ★결론: **본 검증의 지역연준 Empire→SOXX 음(-) forward 는 cyclical merit 전체에서 처음으로 Bonferroni 까지 생존한 cell**(직전 census-only 검증은 0/96 전멸). 단 n<30 아님(n~295)이라 verdict 격상 가능하나, 단일 지역·다른 다중비교 universe 와 합산 시 보수 유지.

## verdict (5단계, §2)

| 후보·관계 | verdict | 근거 |
|---|---|---|
| **Empire 신규주문(level) → SOXX forward(3/6m) 음(-)** | **PARTIAL CONFIRMED** | n~295·live 생존·OOS MATCH·★Bonferroni 2/84 생존·착시 미미. 단 단일 지역(NY)·인과 미확정·magnitude 박제 금지. 음(-) 방향 prior. |
| Composite(Emp+Phil) → SOXX forward 6m 음(-) | TENTATIVE DIRECTIONAL | BH-FDR 생존, Bonferroni 미생존. OOS MATCH. |
| Philly 신규주문 → 4섹터 | REJECTED / 비유의 | 장기 n=697 임에도 forward 전부 비유의(SOXX 음부호도 t<1.5). 지역연준 중 Empire 가 SOXX 신호 담지(NY=금융/tech 노출 큰 지역 효과 가능). |
| z12 변형 전체 | REJECTED | own-history z = forward 신호 거의 소멸. level 우월. |
| 지역연준 → XLE (적시성 우위 가설) | **REJECTED** | ★당월 발표 적시성에도 XLE forward 전부 비유의. census DGORDER_yoy→XLE(+0.31/t3.16) 가 압도. 적시성≠예측력. |
| DGORDER_yoy → XLE (참조 재확인) | TENTATIVE DIRECTIONAL(★최강 XLE) | live 생존·BH-FDR 생존. 기존 verdict 유지. |

**전체 = SOXX 음(-) forward 는 PARTIAL CONFIRMED(Bonferroni 생존), 단 적시성 가설은 REJECTED.** 지역연준 diffusion 의 가치 = "census DGORDER→XLE 개선"이 아니라 **별개 신호(반도체 late-cycle reverse)** 발견. ISM 신규주문 무료 대체로서 XLE 적시성 기대는 falsify.

## ★census DGORDER→XLE 대비 적시성 우위 판정 (작업 핵심 질문)

| 비교축 | 지역연준 diffusion | census DGORDER_yoy | 판정 |
|---|---|---|---|
| 발표시차(적시성) | **14~17d**(당월 중순) | 56d | 지역연준 ★우위 |
| XLE forward k=6 IC | Empire +0.16(t1.56, 비유의) | **+0.31(t3.16, 유의)** | census ★우위 |
| Bonferroni 생존(XLE) | 0 | BH-FDR k=1/k6 생존 | census 우위 |
| 다른 섹터 신호 | **SOXX 음(-) Bonferroni 생존** | 없음 | 지역연준 ★별개 신호 |

→ **적시성(당월 발표) 이점이 XLE 예측력 우위로 이어지지 X.** 지역연준은 더 빠르나 XLE 수요모멘텀을 census 만큼 담지 못함. 단 지역연준은 census 에 없는 **SOXX late-cycle reverse 음(-) forward** 라는 독립 신호를 제공 → 두 지표는 대체재 아닌 **보완재**.

## 12축 audit-ready

| 축 | 상태 | 근거 |
|---|---|---|
| A 이론 | PASS | 지역연준 diffusion 신규주문 = ISM 신규주문(50-기준) 무료 근접 proxy. SOXX 음(-) = late-cycle reverse, DGORDER→XLE = 에너지 수요모멘텀. |
| **B 실데이터** | PASS | FRED API 실측(Empire n=299/Philly n=697). 합성無(fetch raise). ADF 7/7 I(0). naive/live·OOS·head-to-head sub-check 수행. |
| **C 추적성** | PASS | yaml 미수정(verdict 단계). md↔json↔py 수치 일치. |
| **D PIT** ★ | **PASS** | ALFRED first-release probe 발표시차 실측(14~17d vs census 56d). LIVE shift + NAIVE 양측. 착시 미미 실증. |
| E 자문비판 | PASS | credential probe "지역연준 = ISM 신규주문 근접" 무비판 채택 X — 적시성 우위 가설 falsify(XLE 비유의), 대신 SOXX 음(-) 발견 보고. |
| **F 반증** | PASS | REJECTED 명시(적시성 가설·z12·Philly·지역연준→XLE). |
| G effective-N | PASS | n~295~686월. 거시 autocorr·overlapping → NW HAC + block-boot. tier=structural_low 권고. |
| H 미해결 | PASS | 아래 §미해결. |
| I 무결성 | PASS | ETF level. SOXX inception 2001-07 join 자동 정렬. diffusion = seasonally-adj 공식 시리즈. |
| J 경제적 | DEFERRED | turnover/비용 미차감(월간 rank-IC = lens/prior 용도). |
| **K 다중비교** ★ | **PASS** | m=84 공시, Bonferroni 2/84 + BH-FDR 5/84 명시(생존 cell 박제). |
| L 상관무결성 | PARTIAL | 아래 §L축. |

hard-fail(B/C/D/I) 없음.

## L축 — census 신규주문 family 중복 점검 (의무)

- 지역연준 신규주문 ↔ census 신규주문(DGORDER/AMTMNO/NEWORDER/ACOGNO) = **둘 다 "manufacturing new orders" family**. 동일 거시 인자(제조업 수요)의 다른 측정.
- ★단 **forward 신호의 타깃이 분리**됨: census DGORDER → **XLE**(양+), 지역연준 Empire → **SOXX**(음-). 부호·타깃이 다름 → factor β cancel 위험 없음, 중복 계상 아님.
- 통합 시 권고: 기존 yaml `ism_pmi_proxy`(AMTMNO/CFNAI 계열)에 지역연준 Empire neworders 를 **별도 affects_indicator(SOXX 한정, 음부호)** 로 추가하되, census new-orders family 와 **합산 가중 금지**(같은 인자 이중 계상). diffusion level 만(z12 drop).
- z12 변형은 family 내에서도 신호 소멸 → 통합 후보 제외.

## 미해결 의문

1. Empire(NY) 만 SOXX 음(-) 담고 Philly(PA) 는 약한 이유 — NY survey 의 tech/금융 섹터 노출 효과인가, 표본 우연(n 차이 299 vs 697)인가. regime-conditional split(2008/2020 제외) 필요.
2. SOXX 음(-) forward = late-cycle reverse 인가, 반도체 특유의 신규주문-재고 역사이클인가. SOX 자체 book-to-bill 과 cross-check 권고.
3. 적시성(14d) 이점이 XLE 외 다른 섹터·다른 horizon(k<1m, intramonth)에서는 살아날 여지 — 월간 rank-IC 해상도 한계. weekly/daily 재검은 본 phase 외.
4. 지역연준 → XLE 비유의가 "지역 대표성 부족"인가 "에너지가 신규주문 무선행"인가 — census DGORDER 가 XLE 잡는 것과 대비하면 전자 유력(census=전국 집계).
