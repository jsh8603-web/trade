---
tags: [type/validation, domain/inv, scope/equity-kr, sector/shipbuilding, layer/cross]
date: 2026-06-05
---

# validation-cross — 조선 cross 축 (§M.3 3소비자 라우팅, 산업=보고만)

> raw 재현: `raw-v3/measure_cross.py` → validation-cross-v3.json

## (1) 공통인자 exposure β
→ validation-macro.md 참조 (VIX 고베타 t=-2.00 유의, 나머지 비유의).

## (2) customer-supplier momentum (alpha 후보, 조선 supply-chain 선행)
- proxy: BDRY(벌크운임) / CL=F(유가, 해양플랜트/탱커) / BOAT(글로벌 조선해운). lagged 3M momentum → 한국 조선 forward 1M.

| proxy | best lag | corr | p | 판정 |
|---|---|---|---|---|
| oil (유가) | lag1 | -0.190 | 0.084 | 비유의 |
| BDRY (벌크운임) | lag3 | -0.103 | 0.359 | 비유의 |
| BOAT (글로벌조선) | lag1 | -0.110 | 0.434 | 비유의 |

- ★REJECTED as alpha — 전 proxy 전 lag(0-3) 비유의(p>0.08). §D forward-falsifier 정상 작동.
- ★메커니즘(H8): 조선 = 주가가 운임·수주보다 ★선행 → 운임 lagged forward 예측력 부재. 동조성분은 RegimeGlasso Ω 흡수.
- ★직접 수주(Clarkson)/SCFI 운임 = 유료 → ETF proxy(collector_plan high).

## (3) directional_spillover / structural_linkage
- directional_spillover = [] (DY connectedness = supervisor 통합단계).
- structural_linkage = global_shipping_freight_cycle (BDRY/유가/BOAT, 정성 supply-chain. lagged forward 비유의 = REJECTED).

## PIT 보고지연 (§M.1 ⑯)
- DART 사업보고서 median delay 108-120일(FY-end 후). PIT: 펀더멘털 신호 = rcept_dt 이후만 사용(valuation 적용 완료).

## verdict
cross = VIX 고베타(유의)만 β 보고. supply-chain alpha = REJECTED(주가 선행 H8). 조립=supervisor(L축 1회 계상).
