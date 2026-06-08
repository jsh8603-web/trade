---
name: wiring-integrity-eq_us-2026-06-08
description: eq_us adopted 신호의 ⑱축(yaml↔런타임 배선 정합) 직접 검증 — 루프(ledger 주장→런타임 SSOT 확인→repo데이터 재현→verdict). 쓸만한 발견 3건.
tags: [type/research, domain/inv, topic/eq-us, axis/18-wiring, status/concluded]
date: 2026-06-08
related: indicator-ledger.md, eq_us/industries/*/summary.yaml, stock/sleeve_signals.py, core/portfolio_decompose.py
---

# eq_us ⑱축 배선 정합 검증 — 발견 3건

> 루프 = ledger adopted 주장 → 런타임 SSOT(summary.yaml + sleeve_signals.py) 확인 → repo 데이터(edgar+prices) 직접 재현 → verdict. 측정 산물=flow-revive/equs_*.py(임시 /tmp), 본 문서=결론 박제.

## 핵심: 런타임 코드는 규율있게 정확하다. 불일치는 auto-gen ledger 쪽이다

`stock/sleeve_signals.py`(런타임 SSOT)는 **CONFIRMED 신호만 배선**하고 tentative는 **사유 명시 skip**:
- `cyclical`: {pbr −1, ev_ebitda −1} (value CONFIRMED)
- `defensive`: {net_issuance +1, ep_yield −1} + interaction(dividend_yield×op_profitability +1, DEF-2 quality)
- `mega_tech`: {} (11종 basket 통째 보유, selection 대상 아님)
- skip 박제: `cyclical.sales_yield`(CI 0포함+OOS persist=False), `defensive.residual_mom`(BY 미생존)

---

## 발견 1 — cyclical value 배선 정상 + sales_yield 미채택 정당 (재탐구 차단)

| 신호 | 내 직접 재현 IC (sector-neutral, fwd12M) | 배선 | verdict |
|---|---|---|---|
| pbr (value) | **+0.078** p<1e-4 (n=6344) | wired ✓ | CONFIRMED 재현 |
| ev_ebitda (value) | **+0.062** p=3e-4 (n=3381) | wired ✓ | CONFIRMED 재현 |
| sales_yield | 단독 +0.043 / **⊥(pbr,ev) = +0.019 p=0.29** (corr 0.4~0.5) | skip(정당) | **redundant value** — incremental 무. study skip 사유("CI 0포함+OOS persist=False")와 정확히 일치 |

→ **action 불요**. sales_yield 강해 보이는 24M IC(+0.083)는 pbr/ev와 공선, 직교 incremental 비유의. 재탐구 차단.

## 발견 2 — indicator-ledger.md "adopted" 과대보고 (⑱ 정합성 ACTIONABLE)

`indicator-ledger.md`(자동생성)는 **stale `study_session.yaml` v1 가설**을 읽어 adopted 라벨. v3 재작업(`summary.yaml` = 런타임 SSOT)이 confirm 안 한 신호가 adopted 로 표기됨:

| 신호 (ledger adopted, weight) | 내 직접 재현 IC | 런타임 wired? | 실태 |
|---|---|---|---|
| eq_us_cyclical `mom_12_1` (0.06) | **+0.004 p=0.76** (null) | ❌ summary.yaml 부재 | adopted 표기 오류 |
| eq_us_cyclical `asset_growth_yoy` (0.08) | **~0** (validation +0.004) | ❌ | adopted 표기 오류 |
| eq_us_cyclical `fwd_ep_normalized` (0.3) | (cs value=pbr/ev로 대체 구현) | ❌ 이 id 직접 부재 | study_session.yaml 가설, 런타임=pbr/ev |

→ **런타임 코드는 정확**(pbr/ev만 배선=데이터 정합). **ledger가 코드를 잘못 표현**. action = indicator-ledger 를 summary.yaml(런타임 SSOT) 기준 재생성 OR adopted 행에 "study_session.yaml 가설 / 런타임 미배선" 주석. ★ledger header가 "adopted=weight_rules base_weight>0"라 했으나 그 base_weight 는 미확정 study_session.yaml v1 값 → v3 summary.yaml 와 분리 필요.

## 발견 3 — mega_tech cs_lowvol 부호 fragility (drift 플래그)

| | summary.yaml | 내 직접 재현 (2017-2024, 11종) |
|---|---|---|
| cs_lowvol IC | **+0.241** (low-vol 우위) | **−0.168** p<1e-4 (high-vol 우위, NVDA/TSLA/AMD) |

→ **부호 뒤집힘**. 2017-2024 mega-tech 는 고변동주가 최고수익 = low-vol anomaly 역전. ★단 study 가 이미 **stock-pick weight=0**(overlay 전용, "factor 노출 β, n≈8 factor void") 으로 중립화 → **selection 무해**(study 신중함 vindicated). 그러나 summary.yaml `+0.241` magnitude·부호는 **period-fragile** = 이 β를 de-risk overlay 부호로 쓰는 소비자는 불안정 취급 필요(low-vol=defensive 가정이 mega-tech 에선 깨짐). action = overlay 소비 시 sign-robustness 가드 or 재측정.

---

## 종합

- **런타임 selection 배선(sleeve_signals.py)은 건전**: CONFIRMED만 wire, tentative skip 사유 박제, 내 재현이 verdict 일치(pbr/ev value O, sales_yield redundant). = ⑱ **selection 레이어 PASS**.
- **결함은 auto-gen indicator-ledger 표현층**: study_session.yaml v1 가설을 adopted 로 과대보고(mom_12_1/asset_growth null인데 adopted). 코드 버그 아님, 문서 정합 이슈.
- **fragility 1건**: mega_tech lowvol +0.241 → 실측 −0.168 부호 flip(weight=0이라 무해하나 magnitude 신뢰 금지).
