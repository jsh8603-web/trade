# validation-v3-cross-sectional.md — us_mega_tech sleeve §M v3 (★재작업 2026-06-03, basket화)

> frame v3 §M.1~M.12 + 자문 R2 ★수정4(basket화). raw 재현: `raw-v3/{collect,measure}.py` + validation-metrics-v3.json.
> ★재작업 핵심 = (1) ★basket-level time-series factor timing 우선(N=11 cross-sec 통계력 약, Grinold breadth) (2) cross-sec small-basket hedge
>   (3) ★real_rate(duration) primary 발굴(Gormsen-Lazarus, 기존 −0.030 비유의 = 측정 부족 정정) (4) ⛔ sector-neutral 비적용(단일 archetype, 15axis G-A.5).

## §0. 데이터

| 데이터 | 상태 | 비고 |
|---|---|---|
| yfinance 11종 OHLCV | ✅ | Mag7+AVGO/AMD/ORCL/ASML, 2015-2026, 2867일 |
| EDGAR XBRL (equity/net_income/shares/★capex) | ✅ | 6630 rows, 11종, filed PIT |
| FRED CSV (real_rate DFII10/rate DGS10/dollar DTWEXBGS/VIX VIXCLS) | ✅ 실데이터 | eq_us_defensive/raw/fred 재사용 |

## §1. universe + ★측정 단위 (자문 R2 수정4)

- sleeve = Mag7 custom basket 11종 (GICS 파편화로 sector ETF 합산 불가 = SSOT basket).
- ★**N=11 small-basket → cross-sectional rank-IC 통계력 약** (Grinold IR=IC√breadth, breadth 11 × ρ̄=0.429 보정 시 cross_eff_n=2.08).
- → ★**basket-level time-series factor exposure timing 우선** (family_1b) + cross-sectional 은 small-basket hedge (breadth-IR ρ̄ 보정 + magnitude 50~70% haircut, §M.12), 단독 verdict 금지.
- ⛔ **sector-neutral z 비적용** = 단일 archetype(compounder) basket, peer 구조 없음 (universe-demean = sector-neutral 동치). 15axis G-A.5.
- survivorship 약(상폐 거의 없음) but PIT 멤버십(NVDA pre/post-AI, TSLA 2020 편입) = collector_plan. n=136개월(2015~).

## §2. ★family_1b basket-level factor exposure timing (★primary, 자문 수정4 신규)

basket EW 월수익 ~ 거시 Δ (HAC maxlags=3). ★real_rate = team-lead 코멘트1 최우선 검증.

### (a) 단독 β
| factor | β | t_NW | n | R² | CI95 |
|---|---|---|---|---|---|
| **real_rate (DFII10 Δ)** | **−0.1543** | **−4.90** | 136 | 0.192 | [−0.2161, −0.0926] |
| **vix (Δ)** | **−0.0073** | **−6.79** | 136 | 0.309 | [−0.0095, −0.0052] |
| dollar (%) | −1.8293 | −4.89 | 136 | 0.158 | [−2.56, −1.10] |
| rate (DGS10 Δ) | −0.0542 | −1.43 | 136 | 0.031 | [−0.129, 0.020] |

### (b) ★multivariate (real_rate+vix+dollar+rate, R²=0.445)
| factor | β | t | CI95 |
|---|---|---|---|
| **real_rate** | **−0.2096** | **−5.14** | [−0.2895, −0.1297] |
| vix | −0.0053 | −5.45 | [−0.0072, −0.0034] |
| rate | +0.1057 | +2.76 | [0.031, 0.181] |
| dollar | −0.2533 | −0.81 | [−0.87, 0.36] (비유의, real_rate collinear) |

★**핵심 발견 — duration (real-rate) primary**:
- ★**real_rate Δ β = −0.154 단독 / −0.210 multivariate(t−5.14)** = 강 음 = **Gormsen-Lazarus(2023) JF 78(3) duration 정합**: long-duration growth = 할인율(real rate) 민감 강.
- ★**us_defensive real_rate β −0.066(t−6.78) 대비 3배 강 음** = 이론대로 mega-tech(고duration) > defensive. = team-lead 코멘트1 입증.
- ★**기존 cross-v3 −0.030 비유의 = 단일회귀 측정 부족** → multivariate 로 −0.210 회복 (S5 역공격).
- vix β −0.0073 t−6.79 = 고베타 risk-on (★risk overlay, alpha 아님).
- rate(nominal) multivariate +0.106 t+2.76 = real_rate 통제 후 inflation 성분 양(단독 −0.054 무). real_rate(duration)가 본질.

### (c) ★real_rate robustness (코멘트1 최우선)
- **sub-basket**: mag7 β −0.148 t−4.57 / **ai_semi β −0.175 t−3.73** = 둘 다 음(ai_semi 더 강 = 고duration). 부호 일관.
- **leave-year**: all_negative=True, range [−0.169, −0.098] = 단일 연도 의존 X.
- ★**level vs Δ**: level β −0.003 t−0.54 (무) vs **Δ β −0.154 t−4.90** = ★duration 메커니즘(할인율 **변화**)이 신호, level 아님 (Gormsen-Lazarus 할인율 변화 메커니즘 정확).

### (d) forward timing (시계열 IC)
| factor__h | ts_IC | p | n |
|---|---|---|---|
| real_rate 6M | −0.191 | 0.032 | 126 (약 유의) |
| rate 3M | −0.190 | 0.029 | 132 (약 유의) |
| real_rate 3M | −0.136 | 0.119 | 132 |
| vix (전 horizon) | ≈0 | >0.6 | — (동시 risk factor, timing 무) |

→ real_rate/rate 상승이 basket forward 수익 음 예측(약 유의). VIX는 동시 risk factor(timing 무).

## §3. family_1 cross-sectional (★small-basket hedge, 단독 verdict 금지)

30 테스트(6 신호 × 5 horizon). ρ̄=0.429 보정 (cross_eff_n 11→2.08).

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV | within | crEffN | bIR(ρ̄보정) |
|---|---|---|---|---|---|---|---|---|
| vol_60 → 24M_value | +0.286 | 3.58 | 111 | 0.001 | 1.00 | 0.80 | 2.08 | 0.88 (★DEGEN tsEffN 4.6) |
| **vol_60 → 12M** | **+0.241** | **3.10** | 123 | 0.002 | 1.00 | 0.73 | 2.08 | 1.11 |
| vol_60 → 6M | +0.171 | 2.57 | 129 | 0.011 | 0.93 | 0.91 | 2.08 | 1.14 |
| pbr_z → 3M | −0.087 | −1.92 | 134 | 0.056 | 0.67 | 0.58 | 2.01 | −0.82 (borderline) |
| **per_z → 3M/6M/12M** | **≈0** (−0.001/+0.026/+0.013) | \|t\|<0.5 | — | >0.67 | — | — | — | ≈0 (★EXPECTED NULL) |
| capex_z → 12M | −0.087 | −0.99 | 125 | 0.325 | 0.67 | 0.55 | 2.01 | −0.40 |

★**핵심**:
- **vol_60 → 12M** (저변동성 quality) = IC +0.241 t3.10 CPCV 1.00 leave-episode 생존. ★**BY 미생존**(nondegenerate strip survivors=[]) + ★ρ̄ 보정 breadth-IR **1.11**(기존 미보정 2.56 = 과대 정정). magnitude 50~70% haircut. **★단독 verdict 금지** = basket-level real_rate/vix 보완.
- ★**per_z ≈0 = EXPECTED NULL**(expensive_trap 정합 = 고PER 정상, value premium 부재). ★측정 완료(생략 X, 코멘트2). archetype 지지, REJECT 아님.
- ★**capex_z 양방향 판정**(코멘트3): full −0.087 비유의. **pre-AI IC +0.009(n96 무) vs post-AI(2023~) IC −0.404(n29 강 음)** = over-investment penalty(Cooper-Gulen-Schill 2008 정합), productive growth(양) 아님. ★n=29 small hedge(단일 regime, observe-only).
- pbr_z 약 value 음 비유의(borderline 3M raw_p 0.056). n=8 small-basket.

## §4. M_eff + BY (자문 R2 수정 2)

- ★**M_eff (Li-Ji 2005 eigenvalue, test-stat 상관행렬)**: raw m=30 → **M_eff=19.0** (near-dup vol/mom/per/pbr horizon 상관 포착). nondegenerate(24M strip) M_eff=16.0.
- threshold(rank1) = 0.001484 (M_eff). raw_p_min=0.0005 (vol_60 24M_value, degenerate).
- survivors_BY(M_eff) = [vol_60 24M, vol_60 12M] but ★**nondegenerate(24M strip) survivors=[]** = small-basket BY 미생존(기존과 동일).

## §5. family_2 regime-conditional (VIX 사전지정)

high-VIX(상위 40% risk-off) vs low-VIX cross-sec IC 차 (12M):
| signal | hi-VIX IC | lo-VIX IC | diff |
|---|---|---|---|
| vol_60 | +0.176(n40) | +0.273(n83) | −0.098 |
| capex_z | −0.197(n41) | −0.033(n84) | −0.164 |
| per_z | −0.088(n39) | +0.067(n73) | −0.156 |

→ risk-off(high-VIX)에서 신호 약화 경향. ★family_2 별 m(small-n hedge, block-boot CI). hypothesis-generating only.

## §6. ★reflexivity monitor (H9 risk overlay = 신호 아님)

- intra-Mag7 60d rolling corr: full 0.45 / **recent 0.355** / p75 0.534. n_high_corr(>0.70) = 36 month.
- breadth EW-top3 3M spread: recent **+0.081**(양 = breadth 넓음).
- ★**현재 정점 아님**(corr<0.70 AND breadth 양) = cap-down 미발동.
- ★cap-down rule: intra-corr>0.70-0.75 AND breadth<−3~−5%p 동시 → supervisor gross cap-down(de-risk throttle, §M.3 DY). ★return-predicting alpha 아님 = risk overlay.

## §7. valuation (§M.7 — EDGAR PIT, expensive_trap 직접 검증)

- ★**PER 무신호 = compounder expensive_trap 정합**(per_z 3M −0.001 p0.987 / 12M +0.013 p0.872 ≈0 = 고PER 정상, value premium 부재). Gormsen-Lazarus duration 으로 설명. ★EXPECTED NULL(REJECT 아님).
- PBR 약 value 음 비유의(12M −0.167 t−1.58). capex post-AI over-investment 음. 24M_value eff_N 4.7 degenerate.
- value premium 부재 = archetype compounder 입증. ★primary = basket-level real_rate(cross-sec valuation 아님).

## §8. net-cost (§M.4)

US mega-cap 최저(STT 없음, 왕복 14bps / 월 7bps). basket-level timing = turnover 낮음(regime 전환 시만). cs_lowvol |IC| 0.241 >> 7bps.

## §9. ★sleeve_type = exposure_timing_overlay (★B″ 3R STEP 0/5 재분류, verdict 폐기)

- ★**B″ STEP 0(⑧) 재분류**: us_mega_tech = cross-sectional factor ranking sleeve **아님** = ★verdict 없는 macro **exposure/timing overlay**. 유효 cross-section n≈8 = factor 추정 통계적 void(강제 시 spurious factor). → cross-sectional family_1(vol_60/per/capex) = ★DIAGNOSTIC ONLY(참고 지표, PASS/FAIL/verdict 없음).
- ★**보고 3종 (verdict 아님)**:
  1. **factor exposure 한계기여**: basket_real_rate_beta = duration **노출** β −0.154 단독 / −0.210 multivariate(t−5.14). Gormsen-Lazarus(defensive 3배). ⛔ 노출(contemporaneous β) ≠ alpha(예측, ts_IC −0.191 약) = ★supervisor RegimeGlasso/macro overlay 입력. + basket_vix_beta 고베타 risk-on(t−6.79, L축).
  2. **concentration/crowding**: reflexivity(현 정점 아님, intra-corr 0.355<0.70).
  3. **regime-conditional beta 안정성**: capex×VIX interaction = ★B″ STEP 2 fixed-b 재검정 ★MIXED → post-AI 사망(전체 n=125 t 2.43>CV 2.19 p_wild 0.044 SURVIVE but ★post-AI n=29 신호 구간 t 1.94<CV 2.86 p_wild 0.234 ★DIE = payout 동일 size-invalid artifact). ⛔ timing 신호 자격 미달 = diagnostic(size-valid 미입증).
- ★**diagnostic 참고치**: cs_lowvol +0.241(유효 n≈8 void = weight 0, 참고만) / per ≈0(expensive_trap 참고) / capex post-AI −0.404(n=29 underpowered 참고).
- ★**STEP 5(⑨) spillover**: 기존 +0.69 contemporaneous = ★Cohen-Frazzini 오용(동조). CF 정합(고객 hyper_t→공급사 semi_{t+1}) lead 1-3m 비유의(−0.07~−0.09) + ★UNDERPOWERED(power 0.13, MDE|ρ|=0.238). semi↔hyperscaler 한정. 증거부재≠부재증거.
- ★**F-score/net-issuance 측정 폐기**(설계 mismatch). ⛔ sector-neutral 비적용(단일 archetype, G-A.5).
- ★**sleeve 본질** = exposure overlay(supervisor 통합 입력) = cross-sectional alpha sleeve 아님. ★verdict_label 폐기(③ PASS-search 압력 제거 = capex×VIX inflate 자동 해소).
