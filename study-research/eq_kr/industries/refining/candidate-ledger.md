---
tags: [type/candidate-ledger, domain/equity, sector/refining, purpose/easy-review]
date: 2026-06-05
purpose: 정유 지표 후보 전체 + 채택/이연/미채택 + 사유. ★data-gate 산업(cross-sectional 측정 불가, strict 2종).
---

# refining(정유) 지표 후보 원장

## ✅ 채택 (시계열, monitor-only — cross-sectional 채택 0)
| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| 유가(Brent) level forward 음 | commodity_price | structural_prior_low_confidence | mean-reversion. fwd3 rho=-0.37, OOS HOLD(IS-0.39/OOS-0.60), leave-episode survive. ★eff-N t=-1.96 marginal + FDR 미생존 = risk-monitor(alpha 아님). validation-ts-robustness-v3.json |
| ★배당수익률 income trap 음 | income/value | structural_prior_low_confidence | ★2번째 tradeable(team-lead 보강). rho-0.41, eff-N t=-2.48 유의, OOS HOLD(-0.41/-0.44), leave-episode survive(-0.51). 고배당수익률=정점직후 peak-out(PER trap 배당버전). ★유가와 partial 독립(corr0.42, partial-0.24). ★부호 사전확약 정정(prior 양→실측 음). validation-dividend-signal-v3.json |

★종목선택(cross-sectional) 채택 = **0** (전부 INSUFFICIENT, strict 2종). ★rotation tradeable = **2개**(유가+배당, 부분상관 peak-out, conservative cap).

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| 정제마진(crack spread) | theory M1 | Gulf crack proxy 동시 marginal(wc_p>0.07)+forward 무. 한국=싱가포르GRM 미측정 → 약신호가 proxy 한계인지 진짜 약인지 불명 | 싱가포르 GRM(Platts/IR) 확보 후 재측정 |
| cross-sectional PBR/PER/capex | theory M4/M5 | ★strict 2종 = 횡단면 IC(min 8) 불가 | 정유 universe ≥8종(energy 광의 OR floor 완화 — 단 archetype 오염/J축 위험) |
| 한국 정유 가동률 | theory M3 | US IP proxy = OOS flip(한계). 한국 가동률 무료부재 | Petronet/IR 가동률 확보 |

## ❌ 미채택 / proxy 대체 / REJECTED
| 후보 | 사유 |
|---|---|
| ★capex_ratio 시계열 (양) | ★INCONCLUSIVE(ATK-3 반영) — level I(1) p=0.859 spurious 위험 + Δ약화(+0.20 marginal) + 유가proxy 부분(brent corr-0.44) ★but brent 통제 후 orthogonal 잔존(+0.29) = 단순 spurious 단정 과함. standalone 채택 불가(level I(1)+cross-sectional 불가) + REJECT 보류 = INCONCLUSIVE. ☞ 미채택 사유=채택 불가지 reject은 아님 |
| PER (cross-sectional·시계열) | 무효 확정 — 적자빈발(SK이노2024 -2.4조/S-Oil 2020·24·25)+FY만(연1회)=음수EPS·sparse. peak-EPS trap 전형 |
| 가동률(refinery IP) forward | OOS flip(IS-0.43/OOS+0.08) = 무효. US proxy 한계 |
| 가스유틸/LPG 종목 | archetype 이질(규제 유틸 ≠ 정제마진 cyclical) + floor-pass 0종. energy 광의는 supervisor 결정 |
| 화학(석유화학 25종) | chemical teammate(task#14) scope. frame§1.6 분석unit 오염 = 침범 불가 |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| 유가 mean-reversion | eff-N t=-1.96 marginal — risk-monitor지 alpha 아님. level I(1) spurious 부분위험 | 차기 vintage pristine OOS + Δ유가도 forward 음 유의 + eff-N |t|>2.5 |
| family_2 Slowdown interaction | t=2.23 유의(국면 conditional)이나 n 작음(small-block) | 2번째 commodity cycle까지 보류 |

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — cross-sectional 0, 시계열 marginal) | 검증된 정량 규칙 |
| memory | ★정유 = cross-sectional 측정 불가 산업(strict 2종). 국내 정유 과점(2-3개)이라 구조적. capex 일반화는 정유 검증불능 | 다음 cycle prior 정정 |
| observe-only | 유가 mean-reversion(risk-monitor), PBR 시계열(value 방향 비유의) | N 누적 후 promotion |
| evt | ★capex 시계열 양 = spurious(유가proxy) — dispatch 일반화 가설 정유 부적용 사례 | promotion-log 후보 (capex 일반화 한계 = 산업 universe 충분성 의존) |
| pointer | summary.yaml data_gate + collector_plan(싱가포르GRM/universe확대) | 다음 세션 SSOT 정독 우선 |

## ★data-gate 핵심 교훈
정유 = ★cross-sectional 측정 구조적 불가 산업(국내 정유사 과점 2-3개). dispatch가 경고한 "small breadth"가 극단 실현. capex 일반화 가설 = **universe 충분성에 의존**(자동차 17종 OK / 정유 2종 불가). over-trade 차단 = 종목선택 weight 0 + 산업 timing monitor-only.
