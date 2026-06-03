# validation-v3-cross-sectional.md — battery §M v3 재산출 (cross-sectional)

> frame v3 §M.1~M.7 측정. raw 재현: `raw-v3/{collect, measure, measure_cross, exposure_card, collect_dart, measure_valuation}.py`.
> v2(`validation-fundamental/industry/macro.md`) = 4종목 시계열 lag-corr. 본 v3 = 29종목 **횡단면**.
> ★2026-06-03 갱신: valuation 횡단면 = DART 재구성으로 해소(§10 추가).

## §0. 데이터 제약 + 해소 (★pilot 핵심 발견)

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV 개별종목 loop | ✅ 작동 | 29종 가격 패널 (2019-2026, 1818일) |
| pykrx **시장 스냅샷** (get_market_cap / get_market_fundamental / sector_classifications) | ❌ KRX 인증 차단 (빈 응답) | PBR/PER/시총 횡단면 스냅샷 실측 불가 → **DART 재구성으로 우회 해소(§10)** |
| **DART fnlttSinglAcntAll** (자본총계/순이익/자산 + rcept_dt) | ✅ 작동 | ★valuation 횡단면 PIT 재구성(698 rows). PBR/PER cross-sectional z 산출 |
| FDR KRX-DESC (Sector/Industry) | ✅ 작동 | universe 멤버십 (단 현재 스냅샷 = PIT 아님) |
| FDR KOSPI/KOSDAQ listing (Marcap/Amount) | ✅ 작동 | 시총·ADV floor + 현재 주식수(시총 역산) |
| yfinance (LIT/ALB/VIX/factors) | ✅ 작동 | cross 공통인자 + upstream momentum |

★**§M.7 핵심(valuation 횡단면) = DART fnlttSinglAcntAll 로 해소**. pykrx 스냅샷 차단을 종목당 재무 fetch + PIT(rcept_dt) 재구성으로 우회. 잔여 = 시점별 주식수 정밀화(현재 주식수 근사) + EV-EBITDA = collector_plan medium.

## §1. universe 확장 (§M.6)

- FDR 섹터/산업/제품 키워드(`2차전지|배터리|양극|음극|전해질|분리막` 등) 매칭 = **84종**.
- 시총 floor(≥3000억) ∧ ADV floor(≥30억) = **29종** 통과.
- ★기존 v2 = 4종 정적(LG엔솔/삼성SDI/에코프로비엠/포스코퓨처엠). v3 = 29종 → **cross-sectional IC 평균 종목수 26** = 횡단면 측정 결정적 개선 (4종으로는 Spearman 횡단면 불가).

## §2. forward 횡단면 Rank-IC (horizon-tagged, §M.2)

4 신호 (mom_6 / mom_12_1 / rev_1m / vol_60, 전부 cross-sectional z-score) × 4 horizon (1M PEAD / 3M / 6M / 12M) = 16 테스트.

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV OOS hit | avg_N |
|---|---|---|---|---|---|---|
| **mom_6 → 12M** | **+0.086** | **3.87** | 71 | **0.0002** | **1.00** | 26.0 |
| mom_6 → 6M | +0.083 | 2.10 | 77 | 0.039 | 0.93 | 26.2 |
| rev_1m → 12M | +0.050 | 2.73 | 76 | 0.008 | 1.00 | 26.2 |
| mom_6 → 3M | +0.058 | 1.65 | 80 | 0.104 | 0.80 | 26.4 |
| vol_60 → * | -0.02~-0.04 | <\|1.2\| | — | >0.24 | — | — | (저변동성 effect 약·비유의) |

★**horizon 구조 = §M.2 정합**: 모멘텀 12M>6M>3M 단조 증가(3-12M 본진), 1M_PEAD/reversal 약 = 단기 reversal. value 3-5Y 장기 = valuation 데이터 부재로 미측정.

## §3. 4게이트 (§M.2)

**primary = mom_6 → 12M_mom**:
- **G1 ex-ante**: LIT yoy regime (neutral 44 / bull 31 / bear 14 month) = 진입시점 lithium ETF yoy 관측가능. 달력컷 아님.
- **G2 다중검정 (FDR/BY)**: 16 테스트, Benjamini-Yekutieli (신호 상관 → BH 금지, BY factor=3.38). raw_p_min=0.00024. **BY 생존 = mom_6__12M_mom 단 1개**. Bonferroni α/16=0.0031 도 통과.
- **G3 walk-forward CPCV purge+embargo**: 6 splits, n_test=2 → 15 fold combinations. purge=12M(forward 라벨 overlap), embargo=1. **OOS hit=1.00** (전 fold 부호 일관), OOS IC mean=0.086 = full-sample 무붕괴.
- **G4 Newey-West HAC**: lag=horizon=12 (overlapping forward 자기상관). se_nw=0.0223 (se_iid 0.0205 대비 보정), t_nw=3.87. NW CI [0.043, 0.130] 0 비포함.

block-bootstrap (block=3M, B=2000): CI [0.032, 0.132] = NW 와 정합 (둘 다 0 배제).

## §4. robustness (§M.1, §M.3)

- **leave-episode**: 최강 12M 윈도 제외 → ex-peak IC +0.067 (full +0.086), 부호·magnitude 생존 = single-episode artifact 아님.
- **within-period**: 연도별 IC 부호 일관 **100%** (2019:+0.048 / 2020:+0.045 / 2021:+0.119 / 2022:+0.090 / 2023:+0.023 / 2024:+0.174 / 2025:+0.086). 전 연도 양.
- **유동성-티어 IC (§M.1 ⑱)**: hi-ADV +0.070 / lo-ADV +0.096 / **cap-weighted +0.046**. lo-ADV 가 hi 보다 약간 강하나 cap-weighted 도 양 = Rank-IC 동일가중이 microcap 에 과의존 아님(투자가능성 확인).
- **e-process (§M.1 ⑪)**: score_ic_breakdown_eprocess(baseline=0.5×IC) — 강신호라 baseline 위 안정, live 모니터·placebo 용도. (붕괴 detector 는 baseline 미달 시 트리거 = 현재 무붕괴.)

## §5. cross 축 (§M.3 — 산업=보고만)

### (a) 공통인자 β (contemporaneous, HAC maxlags=3, n=35 month)
- **credit (US HY OAS proxy)**: β=-0.164, t=-2.48, CI [-0.294, -0.034] = 유의. credit risk-off → battery 약세.
- **oil**: β=+0.248, t=+2.06, CI [0.012, 0.484] = tentative (CI 하단 0 근접).
- VIX/dollar/rate = 비유의. R²=0.245.
- ⚠️ credit = US proxy (KR HY spread 부재), n=35 = small-n → hedge: tentative directional.

### (b) customer-supplier momentum (alpha 후보, §M.3)
- lithium upstream (LIT/ALB) 3M 모멘텀 lagged → battery forward 1M:

| lag | LIT corr (p) | ALB corr (p) |
|---|---|---|
| 0 | +0.003 (0.98) | +0.036 (0.75) |
| 1 | -0.019 (0.86) | -0.028 (0.80) |
| 3 | +0.086 (0.44) | +0.101 (0.37) |

→ **REJECTED as alpha**: 전 lag 비유의. forward 예측력 부재 (§D forward-alpha falsifier 작동, null result 정직 기록). 동조 성분은 통합 RegimeGlasso Ω 가 자동 흡수(이중 라우팅 회피).

## §6. PIT-fundamentals safety (§M.1 ⑯)

DART 사업보고서(A001) 제출일 rcept_dt vs fiscal year-end(12-31) gap = 보고지연:

| 연도 | n | median delay(일) | max(일) |
|---|---|---|---|
| 2021 | 9 | 120 | 120 |
| 2022 | 23 | 108 | 119 |
| 2023 | 20 | 114 | 118 |
| 2024 | 8 | 120 | 120 |

→ 사업보고서 median delay **~108-120일** (FY-end 후). 펀더멘털 신호는 rcept_dt 이후만 사용 의무 (미적용 시 lookahead → IC 가짜 부풀림). **본 v3 가격신호는 PIT-safe** (forward shift, 보고지연 무관).

## §7. cross-sectional exposure card (§M.7)

universe 29종 현 시점(2026-05-31) peer-relative z-score (sector-neutral 표준화 = subagent 담당, R2-1 own-history gap 메움). 상위 (mom_6_z):

| ticker | name | mom_6_z | mom_12_1_z | vol_60_z |
|---|---|---|---|---|
| 082920 | 비츠로셀 | +2.46 | +1.31 | +0.09 |
| 064290 | 인텍플러스 | +1.98 | +0.77 | +1.13 |
| 336260 | 두산퓨얼셀 | +1.66 | +0.96 | +1.29 |
| 126340 | 비나텍 | +1.24 | +3.37 | +1.26 |
| 006400 | 삼성SDI | +0.90 | +1.38 | -0.78 |

전체 = `raw-v3/exposure-card-v3.json`. ⛔ score→target weight·cap·Σ_signal mixing = supervisor 조립(dispatch 밖).

## §8. net-cost (§M.4)

KR 비대칭: 매수(spread/2+comm) + 매도(spread/2+comm+STT 0.20%) = 왕복 **33bps**. turnover 0.5/월 → 월 16.5bps. IC +0.086(breadth 26종 IR 누적) >> 16.5bps → net 보존. ⚠️ sqrt impact·size-tier 정밀화 = supervisor CPCV 캘리브레이션.

## §10. ★valuation 횡단면 (결함1 해소 — DART 재구성, 2026-06-03)

supervisor 지시로 DART fnlttSinglAcntAll 재무(698 rows) + pykrx 가격 → PBR/PER cross-sectional z → forward IC.

**PIT 엄수**: 각 재무 = `rcept_dt`(공시일) 이후 시점에만 적용(forward-fill from publication) = lookahead·restatement 회피. FY 보고지연 median 80일 실측. 시총 = Close × 현재주식수(시점별 주식수 정밀화 = collector_plan).

**cross-sectional 작동 = YES** (supervisor 질문 답): PBR 횡단면 평균 26종(전종목), PER 20종(순이익 양수). coverage PBR 2231 / PER 1664 cells.

| signal__horizon | IC | t_NW | n_mo | p_NW | CI_block_boot | CPCV | within | avgN |
|---|---|---|---|---|---|---|---|---|
| **per_z → 24M_value** | -0.116 | -1.38 | 61 | 0.174 | [-0.196, -0.042] | 0.80 | 0.67 | 19.7 |
| per_z → 12M | -0.068 | -0.94 | 73 | 0.352 | [-0.162, 0.013] | 0.67 | 0.57 | 20.0 |
| pbr_z → 24M_value | -0.019 | -0.12 | 61 | 0.907 | [-0.165, 0.128] | 0.47 | 0.50 | 25.2 |
| pbr_z → * | ≈0 | <\|0.2\| | — | >0.9 | 0 포함 | — | — | 26 |

- **부호 = 전부 음** (IC<0) = value premium 방향 일치(저PBR/저PER = 싼 종목 forward 높음).
- per_z 24M value = 가장 강(저PER value premium, 장기 3-5Y). 단 **NW CI [-0.281, 0.049]는 0 포함(비유의)** vs block-boot [-0.196, -0.042]는 0 배제 → NW 채택(n=61, 24M overlap 큰 자기상관, 보수적). **BY 보정(8테스트) 생존 0**.
- **verdict: per_z 24M = TENTATIVE DIRECTIONAL** (방향성 약 prior, CI 넓음, 추가 검증 필요) / **pbr_z = INSUFFICIENT**(무신호).
- ★결론: valuation 횡단면 **메커니즘 작동**(avgN 20-26) + **산출 구조 완성**(사용자 "PER/PBR 평균대비 골고루"). 단 battery 내 IC 약·비유의 → **momentum(cs_mom_6m CONFIRMED)이 battery dominant**. valuation IC 유효성은 산업별 상이 가능(6산업 batch 검증).

## §9. verdict

- **primary (cs_mom_6m → 12M)** = CONFIRMED (n=71, t=3.87 p<0.001, BY 생존, CPCV OOS 1.00, within-period 100%, leave-episode 생존, 유동성 robust). = battery dominant 신호.
- **valuation 횡단면** = 해소(DART 재구성, 메커니즘 작동) but battery 내 IC 약·비유의(per value premium TENTATIVE / pbr INSUFFICIENT).
- **산업 전체 = PARTIAL** — momentum CONFIRMED, valuation 약, customer momentum REJECTED.
- archetype = cyclical 지지 (모멘텀 3-12M 본진 패턴 정합).
