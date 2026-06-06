# validation-cross-sectional.md — steel §M v3 측정 (cross-sectional)

> frame v3 §M.1~M.7 측정. raw 재현: `raw-v3/{collect, measure, measure_cross, measure_valuation, measure_conditional, measure_fundamentals_cycle, collect_dart, collect_dart_extended}.py`.
> semiconductor 미러. ★핵심 발견 = **철강 momentum forward IC = 음(reversal, -0.181)** = battery(양)와 반대 + **capex_ratio 음(asset growth anomaly)** = dispatch capex 일반화 입증.
> ★★small-universe(23종, avg cross-section ~20) = magnitude inflation 위험(frame §M.12) → point estimate literal 금지 + breadth-adj IR + 50% haircut.

## §0. 데이터 제약 + 해소

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV 개별종목 loop | ✅ 작동 | 23종 가격 패널 (2019-2026, 1818일) |
| pykrx 시장 스냅샷 | ❌ KRX 인증 차단 | valuation = DART 재구성 우회 |
| DART fnlttSinglAcntAll (자본/순이익/자산 + rcept_dt) | ✅ 563 rows/23종 | valuation PIT 재구성 (PBR/PER) |
| DART dart_extended (재고/유형/무형) | ✅ 592 rows, ppe 100% | ★capex/재고 cycle 지표 PIT |
| FDR KRX-DESC (Industry) | ✅ | universe 정밀 필터 ("1차 철강 제조업") |
| yfinance (SLX/VALE/VIX/factors) | ✅ | cross 공통인자 + 철강 cycle proxy + G1 regime |
| FRED/ECOS regime (반도체 재사용) | ✅ | Macro/KRW/flow regime (시장 공통) |

## §1. universe (§M.6) — ★협소 산업 화이트리스트

- ★FDR Industry **"1차 철강 제조업"** 정밀 매칭 + 명시 제외(발전설비/상사/전선/조선) + 태웅(단조) 화이트리스트.
- floor: Mc≥1000억 ∧ ADV≥1억 (★반도체 3000억/30억 완화 — 철강 협소·저유동성) → **23종**.
- ★avg cross-section ~20 = 반도체(73)의 1/4 = **small-universe** → magnitude inflation. POSCO홀딩스(005490) 시총 압도(universe 60%+) → cap-weighted IC 점검(아래 §4).
- ★sub-cluster: 고로(POSCO/현대제철) + 봉형강(동국제강/대한제강) + 강관(세아제강/휴스틸/넥스틸) + 도금(KG스틸/포스코스틸리온) + 특수강(세아베스틸) + 가공(태웅 단조 / 성광벤드·태광·하이록 피팅).

## §2. forward 횡단면 Rank-IC (horizon-tagged, §M.2) — measure.py

4 가격신호 (mom_6/mom_12_1/rev_1m/vol_60) × 4 horizon = 16 테스트. ★small-universe magnitude haircut 전제.

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV OOS hit | within | avg_N | BY 생존 |
|---|---|---|---|---|---|---|---|---|
| **mom_12_1 → 12M** | **-0.181** | **-4.42** | 65 | 0.000 | **1.00** | 1.00 | 20.5 | ✅ |
| **vol_60 → 12M** | -0.134 | -3.41 | 74 | 0.001 | 0.93 | 0.86 | 20.8 | ✅ |
| **vol_60 → 6M** | -0.117 | -3.52 | 80 | 0.001 | 1.00 | 1.00 | 21.0 | ✅ |
| vol_60 → 3M | -0.108 | -3.07 | 83 | 0.003 | 1.00 | — | 21.1 | ✅ |
| **mom_6 → 3M** | -0.095 | -2.75 | 80 | 0.007 | 1.00 | 1.00 | 21.0 | ✅ |
| vol_60 → 1M_PEAD | -0.085 | -3.18 | 85 | 0.002 | 1.00 | — | 21.1 | ✅ |
| mom_6 → 1M_PEAD | -0.085 | -3.06 | 82 | 0.003 | 1.00 | — | 21.0 | ✅ |
| rev_1m → 6M | -0.051 | -2.28 | 82 | 0.025 | 1.00 | 0.86 | 21.0 | ✗ |

- ★**momentum 부호 = 음(reversal)** = battery(양 +0.086)와 반대 = **cyclical archetype 핵심 증거**(theory M3).
- ★**vol_60(저변동) 전 horizon 음** = 저변동 종목 outperform = defensive quality(theory M6). hi_adv -0.13 / lo_adv +0.03 = 유동성 종목서 작동.
- multiple testing: m=16, BY factor=3.38, raw_p_min=4e-05(mom_12_1) → **BY 생존 7개**(momentum/vol). ★단 conditional+fundamentals 통합 m=180 에선 미생존(small-n hedge).
- ★★magnitude caveat: mom_12_1 -0.181은 avg 20종 small-universe inflation. **breadth-adj IR = IC·√breadth ≈ -0.81** + point estimate 50% haircut 권고. 방향·significance(t=-4.42, BY) robust.

## §3. valuation 횡단면 (§M.7) — measure_valuation.py (DART 재구성)

PBR/PER cross-sectional z → forward IC. PIT(rcept_dt 이후만). PBR coverage 1786 cells / PER 1408.

| signal__h | IC | t_NW | n_mo | p_NW | CPCV | within | BY 생존 |
|---|---|---|---|---|---|---|---|
| **pbr_z → 12M** | **-0.161** | -3.07 | 73 | 0.003 | 1.00 | 0.86 | ✅ |
| pbr_z → 6M | -0.130 | -2.64 | 79 | 0.010 | 1.00 | 0.71 | ✅ |
| pbr_z → 24M_value | -0.123 | -1.61 | 61 | 0.112 | 0.93 | 0.67 | ✗ (24M eff_N≈2.5 degenerate) |
| pbr_z → 3M | -0.100 | -2.68 | 82 | 0.009 | 1.00 | 0.88 | ✅ |
| per_z → 12M | -0.108 | -1.64 | 73 | 0.106 | 0.93 | — | ✗ |
| per_z → 3M/6M | -0.034 ~ -0.055 | <1.0 | — | >0.36 | — | — | ✗ |

- ★**PBR value premium 작동 = 3M/6M/12M 단조 일관**(BY 생존 3개, CPCV 1.00). 철강 = cyclical value 핵심. ★반도체보다 robust(단조 일관).
- ★**PER 전 horizon 비유의 = peak/trough-EPS trap**: 정점 peak-EPS(PER 低 착시) + 다운사이클 적자(trough, PER 무의미) 양방향 왜곡. PBR(자본 stock, EPS 면역) robust = 반도체/자동차 동형.
- ★24M_value = eff_indep_N≈2.5 degenerate(overlap) → primary 아님, 3M/6M/12M 사용(frame §M.12).

## §4. 유동성-티어 IC (size-bucket + cap-weighted) — ★POSCO 집중 점검

| 신호 | hi_adv | lo_adv | cap_weighted | 해석 |
|---|---|---|---|---|
| mom_12_1 12M | -0.233 | -0.093 | **-0.244** | ★cap-weighted(POSCO 지배)서 더 강 = microcap artifact 아님. 단 hi_adv -0.233 magnitude 큼(small-universe). |
| vol_60 6M | -0.133 | +0.026 | -0.180 | hi_adv 강 / lo_adv 약 = 유동성 종목서 작동 |

★momentum reversal = cap-weighted -0.244(대형주서 강) = small-universe + microcap 아티팩트 우려 일부 해소. 단 magnitude 자체는 haircut.

## §5. ★capex / cycle 펀더멘털 (§M.1, dispatch capex 가설) — measure_fundamentals_cycle.py

DART dart_extended PIT 재구성. ppe coverage 100%.

| 지표 | prior | y_60d IC | wc_p | walk-forward OOS | verdict |
|---|---|---|---|---|---|
| ★**capex_ratio** (유형/총자산) | 음 | **-0.0839** | **0.0005** | IS -0.111 → OOS -0.053 ✅ | ★TENTATIVE DIRECTIONAL (asset growth anomaly 입증) |
| ppe_yoy (유형 yoy) | 음 | +0.006 | 0.82 | IS +0.041 → OOS -0.024 ❌반전 | INSUFFICIENT (capex 수준만 작동) |
| inv_ratio (재고/총자산) | 음 | +0.047 | 0.18 | IS +0.003 → OOS +0.098 ✅(양) | ★prior 반증 (반도체 동형) |
| rnd_ratio (무형/총자산) | 양 | — | 0.38 | — | INSUFFICIENT (철강 R&D 미미) |

- ★★**capex_ratio = dispatch capex 일반화 핵심**: y_60d IC -0.084(wc_p=0.0005), walk-forward OOS 부호유지, prior 음 일치 = **asset growth anomaly**(과잉증설 종목 forward 약, Cooper-Gulen-Schill 2008). regime: Slowdown -0.096 / KRW_neutral -0.111 / flow_neutral -0.071 모두 음 유의.
- ★**자동차 capex_ratio(음, structural_prior_high_confidence)가 철강(초자산집약)서 재현** = 자산집약 4섹터(화학/정유/조선/철강) capex 일반화 1보(메인 종합 대상).
- ★단 BY 통합 family(m=180) 미생존 + y_20d 약(-0.030) = 장기 horizon·수준(ratio) 한정 + small-n hedge.

## §6. ★conditional IC surface (dispatch 본체) — measure_conditional.py

regime: Macro(CLI 4) × KRW(3) × flow(3). per-cell wild-cluster p + n_eff + block-boot CI.

★**KRW_neutral = 철강 증폭축** (반도체 KRW_weak 과 다름 = 철강 특수성: 중국 cycle dominant, 환율 부차):

| 신호 | horizon | regime | IC | wc_p | n |
|---|---|---|---|---|---|
| mom_6 | y_5d | KRW_neutral | -0.169 | 0.0015 | 38 |
| mom_6 | y_20d | KRW_neutral | -0.131 | 0.011 | 37 |
| vol_60 | y_20d | KRW_neutral | -0.121 | 0.011 | 37 |
| pbr_z | y_60d | KRW_neutral | -0.105 | 0.0115 | 36 |
| capex_ratio | y_60d | KRW_neutral | -0.111 | 0.001 | 37 |
| vol_60 | y_60d | uncond | -0.105 | 0.0005 | (BY top) |
| pbr_z | y_60d | uncond | -0.106 | 0.0005 | (BY top) |

- FDR family m=102, BY 생존 0(small-n), raw_p_min=0.0005 ≈ Bonferroni α 0.00049 = 경계.

### §6.1 family_2 interaction (G-B 의무) — KRW_neutral dummy

| 신호 | b_main(t) | b_interaction(t) | verdict |
|---|---|---|---|
| mom_6 | -0.031(-0.76) | -0.104(-1.63) | 비유의(방향 정합) |
| vol_60 | -0.026(-0.67) | -0.095(-1.58) | 비유의(방향 정합) |

★interaction term 부호 음(KRW_neutral서 증폭, 방향 정합)이나 t=-1.63/-1.58 비유의(small-universe + small-n). 반도체 KRW_weak(t=-2.95)보다 약. ★정직 보고: interaction 자체 비유의, walk-forward OOS가 verdict 근거.

### §6.2 ★walk-forward OOS (KRW_neutral conditional, verdict 근거) — IS 2019-22 / OOS 2023-26

| 신호 | IS IC | OOS IC | verdict |
|---|---|---|---|
| mom_6 y_20d | -0.084 | **-0.156** | ✅부호유지+강화 |
| mom_6 y_60d | -0.156 | -0.150 | ✅거의 동일 |
| vol_60 y_20d | -0.136 | -0.120 | ✅부호유지 |
| vol_60 y_60d | -0.045 | -0.153 | ✅강화 |
| pbr_z y_20d | -0.087 | -0.090 | ✅거의 동일 |
| pbr_z y_60d | -0.118 | -0.089 | ✅부호유지 |

★**전부 OOS 부호+magnitude 유지 = in-sample artifact 아님 = conditional CONFIRMED(tentative)**. interaction term 비유의는 small-n, walk-forward가 episode 종속 직접 반증.

## §7. cross 공통인자 (§M.3) — measure_cross.py (산업=보고만)

| factor | β | t | CI95 | 해석 |
|---|---|---|---|---|
| oil | +0.232 | **+2.09** | [0.015, 0.449] | ★유가 양 유의 (철강=원자재/경기 cyclical) |
| credit | -0.060 | **-2.11** | [-0.115, -0.004] | risk-off 시 철강 약 (US HY proxy, n=35) |
| dollar | -1.381 | -1.67 | [-3.00, 0.24] | 약 음(비유의), 강달러→철강 약 약 prior |
| VIX/rate | -0.006/+0.012 | <1.2 | — | 비유의 |

- **customer-supplier momentum (SLX/VALE)**: 전 lag(0-3) 비유의(p 0.18~0.49) = ★REJECTED as alpha. 한국 철강 = 글로벌 cycle/철광석 contemporaneous 동조지 forward 예측력 부재(§D falsifier, 반도체 동형). 동조성분 = RegimeGlasso Ω 흡수.
- PIT reporting delay: 사업보고서 median 108-120일(FY-end 후).

## §8. ★S5 역공격 실측 (최강 반증 직접 투척 → 수렴)

| 공격 | 검정 | 결과 | verdict |
|---|---|---|---|
| S5-A: momentum -0.181 = POSCO 단일종목 의존? | POSCO(005490) drop 후 재측정 | IC -0.181 → ex-POSCO **-0.165** | ★생존 (단일종목 아님, 대형주 reversal 일반) |
| S5-B: PBR value = size 위장? | Fama-MacBeth ret~PBR_rank+Size_rank | PBR\|Size b=-0.062 **t=-1.98** / Size\|PBR t=-1.67 비유의 | ★PBR 우위(size 위장 아님). ★단 t=-1.98 = small-universe 경계 = 완전 독립 입증 약(hedge) |
| S5-C: momentum = 2021 철강랠리 episode 종속? | leave-2021-out | IC -0.181 → ex-2021 **-0.161** | ★생존 (단일 episode 아님) |

★**수렴**: momentum reversal = POSCO/2021 episode 종속 모두 기각 = robust. PBR size 위장 = PBR 우위이나 small-universe 경계 hedge. walk-forward OOS(KRW_neutral) 전부 생존과 정합.

## §9. 종합 verdict

- 산업 전체 = **PARTIAL** (방향·significance robust, small-universe magnitude hedge + 통합 BY 미생존).
- ★핵심 4: (1) momentum 음(reversal) = cyclical archetype 지지 (2) ★capex_ratio 음 = asset growth anomaly = dispatch capex 일반화 입증(자동차 재현) (3) PBR○ PER✗(peak/trough-EPS trap) (4) vol_60 저변동 quality.
- ★★small-universe(23종) magnitude haircut + breadth-adj IR 일관. conditional 증폭축 = KRW_neutral(중국 cycle dominant).
