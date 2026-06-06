---
tags: [type/validation, domain/equity, sector/refining, scope/equity-kr]
date: 2026-06-05
purpose: 정유 측정 상세 (frame M2 시계열 + cross-sectional INSUFFICIENT). raw = raw-v3/validation-*.json.
---

# 정유(refining) validation — 측정 상세

> ★cross-sectional(종목선택) = INSUFFICIENT(strict 2종). 산업 시계열(frame M2)이 측정 본체.
> raw 재현: raw-v3/{measure_timeseries, measure_ts_robustness, measure_capex_cycle, measure_valuation_ts, measure_cross_placebo}.py

## 1. data-gate (측정 前 박제)
- 정유 코어("석유 정제품 제조업") = 5종. strict floor(시총3000억∧ADV30억, battery/auto 동일) 통과 = **2종**(SK이노096770 ADV230억 / S-Oil010950 ADV69억).
- 나머지 3종 = microcap(한국쉘석유 ADV3.5억/미창석유 0.4억/극동유화 1.7억). 가스유틸/LPG = floor 0종 + archetype 이질.
- → cross-sectional Spearman IC(min 8종) ⛔불가. **산업 시계열(frame M2) 측정 + cross-sectional INSUFFICIENT 박제.**

## 2. 산업 시계열 측정 (정유 strict2 동일가중 패널수익 vs cycle driver)

### 2.1 유가(Brent) — 동시(+)/예측(-) 부호 갈림 (핵심)
| 측정 | rho | wc_p | n | eff-N | t_eff | 판정 |
|---|---|---|---|---|---|---|
| 동시(contemp) | +0.4068 | 0.0025 | 88 | 82.9 | — | ★강(재고평가이익) |
| forward 3M | -0.368 | 0.0015 | 86 | 26.5 | **-1.96** | marginal |
| Δ유가 forward | -0.049 | — | 86 | — | -0.24 | ★예측력0(level만) |

- walk-forward OOS: IS=-0.39 / OOS=-0.60 (HOLD, 강화).
- leave-episode(2020covid+2022우크라 제외): -0.37 → -0.25 (survive, 약화).
- ADF: brent level **I(1) p=0.173 비정상** / forward ret I(0) p=0.019. → level-on-level 부분 spurious 위험(단 ret I(0)라 순수 spurious 아님).
- family_2(A-5): macro=Slowdown interaction 유의(b_inter=+0.090, t=2.23) = 국면 conditional.
- **★verdict: TENTATIVE DIRECTIONAL** — mean-reversion(고유가 peak-out·수요파괴) OOS robust but eff-N marginal + FDR 미생존 + Δ예측력0 + level I(1) = **risk-monitor(alpha 아님)**. Deaton-Laroque(1992).

### 2.2 정제마진(crack spread) — 약 (Gulf proxy 한계)
- 동시: blended +0.136(wc_p=0.22 비유의) / gasoline +0.196(0.072 marginal) / diesel +0.101.
- common factor β: crack +0.004(t=2.16 marginal). forward 무.
- **verdict: TENTATIVE/약** — ★Gulf crack proxy(한국=싱가포르GRM 미측정) = under-claim 회피 위해 잠정.

### 2.3 가동률(refinery IP proxy) — INSUFFICIENT
- 동시 +0.026(비유의). forward -0.315 but OOS flip(IS-0.43/OOS+0.08). → 무효(US IP proxy 한계).

## 3. cross-sectional — INSUFFICIENT (전부)
| 신호 | cross-sectional | 시계열(참고) | verdict |
|---|---|---|---|
| capex_ratio | ★INSUFFICIENT(2종) | level +0.47 but **spurious** | REJECTED |
| PBR | ★INSUFFICIENT(2종) | -0.17(t=-0.85 비유의) | TENTATIVE |
| PER | ★INSUFFICIENT + 무효확정 | 적자빈발+FY만 | INSUFFICIENT |

### 3.1 ★capex 가설 (dispatch ★★최우선) — spurious REJECTED
정유 capex_ratio(유형자산/총자산) = SK이노 0.42 / S-Oil 0.55 = **초자산집약**(자동차 0.2~0.3의 2배). dispatch "초자산집약 장치산업" 정합.
- cross-sectional capex IC = INSUFFICIENT(2종, dispatch 음 prior 검증 불능).
- 시계열 capex level forward = +0.474(wc_p=0.0005, OOS HOLD) = dispatch 음 prior와 **반대**.
- ★spurious 증거: (1) ADF level p=0.859 강 I(1) (2) Δcapex +0.199(p=0.074 marginal) 약화 (3) capex_level↔brent_level corr=-0.435(유가국면 proxy 부분).
- ★S5 역공격(ATK-3) 반박: brent 통제 후 capex partial rho=**+0.292 잔존** = brent proxy ★만은 아님(orthogonal 성분). → 단순 spurious REJECT는 **over-rejection**.
- **verdict: ★INCONCLUSIVE** — standalone alpha 채택 불가(level I(1) + cross-sectional 2종 불가) + 단순 spurious REJECT 보류(ATK-3 잔존). dispatch 음 prior와 반대 부호(양+) 잔존 = 정유 특이(capex↓국면=유가高=forward약?), 차기 vintage+universe 확보 시 재검. §1.8 함정 회피 + over-rejection 회피.

### 3.2 PER 무효 확정
net_income 적자 빈발(SK이노 2024 -2.37조 / S-Oil 2020·2024·2025 적자) + FY만(연1회) = 음수EPS·sparse → PER 산출 불능. peak-EPS trap(정점EPS↑→저PER 함정) 정유 전형(2016-17 호황 PER 4~5배→장기하락).

## 4. cross 축 (A-3, 빈[] 금지 충족)
- common factor 동시 β: 유가+0.233(t3.56) / **usdkrw-1.432(t-3.26, 원유수입 달러비용→원화약세 마진압박, 수출주 반대 부호)** / crack+0.004(marginal) / natgas+0.055(비유의).
- directional_spillover: 유가 level lead 약 음(-0.19), crack lead 약. DY 정식분해=supervisor.
- structural_linkage: 원유시장 upstream. 유가 동시β 강(+) but forward alpha 부재(mean-reversion) = RegimeGlasso Ω 흡수.
- placebo: random rho=+0.165 p=0.128 비유의 = 측정 파이프 정상.

## 5. FDR family (단일, 7가설 사전고정)
시계열 FDR(m=6 powered cell) survivors=0(raw_p_min=0.166 blended_crack KRW_weak). = 약신호 정직(BY 미생존).

## 6. 종합 verdict
- ★cross-sectional 종목선택 = 전부 INSUFFICIENT(2종) = 매매룰 구성 불가, weight 0.
- 산업 시계열 = 유가 mean-reversion(TENTATIVE, risk-monitor) + crack 약(proxy 한계). capex spurious REJECTED.
- **G-G = FAIL~PASS-conditional 경계**: monitor-only/산업 timing(고유가 peak de-risk) sleeve, 종목선택 weight 0. supervisor 최종판정.
- ★over-claim 회피: universe 2종 = 모든 신호 방향만, n<30 hedge 극대, marginal=risk-monitor 격하.
