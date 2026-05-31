---
tags: [type/analysis, domain/inv, study/eq_us_cyclical]
date: 2026-05-30
source: data/fixtures/semiconductor_panel_v1.parquet (40 firms × 36Q, 2014-2023)
note: ⚠️ 합성(synthetic) 픽스처 — 실데이터 아님. 경기민감 반도체 사이클 구조를 담아 lens-지표 매핑 방향성 검증엔 유효. 실데이터(EDGAR 적재 후) 재검증은 confidence_hooks/collector_plan 으로.
---

# 데이터 대조 분석 — semiconductor panel (작업순서 2단계)

lens 가설(블록1)을 과거 실데이터로 대조. 패널 = 경기민감 IT 대표(반도체 = early/mid-cycle archetype).

## A. regime(cycle_phase)별 지표 분해
| phase | book_to_bill | capex_to_rev | inventory_qoq | gross_margin | rev_growth | multiple |
|---|---|---|---|---|---|---|
| peak | 1.122 | 0.263 | 0.166 | 0.451 | 0.164 | 6.782 |
| mid | 0.986 | 0.201 | 0.066 | 0.413 | 0.068 | 7.014 |
| trough | 0.973 | 0.204 | 0.073 | 0.408 | 0.058 | 6.699 |

→ **peak>mid>trough 순으로 펀더(rev_growth·book_to_bill·gross_margin) 강세** = lens "경기 확장기 이익 강세, 수축기 약세" 확인(확신).
→ 단 multiple 은 mid>peak>trough = **peak 에서 펀더 강해도 멀티플 디레이팅**(peak_trap 전조).

## B. 지표 → label_real(유망종목 252/1440) Rank-IC
| 지표 | IC |
|---|---|
| **val_gap(공정가-현재멀티플=저평가도)** | **+0.658** |
| **multiple** | **-0.427** |
| inventory_qoq | -0.311 |
| capex_to_rev | -0.305 |
| gross_margin | +0.077 |
| book_to_bill | +0.061 |
| rev_growth | +0.054 |

→ **valuation(저평가·낮은 멀티플)이 압도적 최강 알파.** momentum/growth(rev_growth +0.054) 약함.
→ **inventory_qoq·capex 과열 = 음의 신호(-0.31)** = 재고/투자 과열 = late-cycle 경계(역부호 활용).

## C. 선행성 (지표 → t+1 rev_growth, 종목내 shift)
inventory_qoq +0.133 / capex_to_rev +0.126 / gross_margin +0.084 / book_to_bill +0.074
→ book_to_bill 선행성 통념(반도체 선행지표)보다 약함 = **합성데이터 한계, 실데이터 재검증 필요(거부 보류)**.

## D. val_gap → Δmultiple(t+1) IC=+0.385
→ 저평가일수록 다음분기 멀티플 회복 = **mean-reversion 작동**. valuation 알파의 메커니즘 확인(확신).

## E. cycle_phase별 val_gap·유망비율 (peak_trap 검증)
| phase | val_gap_mean | real_rate |
|---|---|---|
| trough | 1.252 | 0.399 |
| mid | 0.502 | 0.150 |
| peak | 0.037 | **0.000** |

→ **trough(바닥): 저평가+유망 집중 / peak: val_gap≈0·유망 전무 = peak_trap 확정.**
→ valuation·contrarian 신호가 **regime conditional**: trough valuation 가중↑, peak 신규진입 차단.

## lens 갱신 결론 (작업순서 3단계 — flag → lens·weight 변동)
**(확신) flag:**
1. valuation(fwd_ep/val_gap)이 경기민감 반도체 최강 알파 → 블록4 fwd_ep base_weight 상향(0.22→0.28 검토), trough regime 에서 추가 가중.
2. inventory_to_sales·capex 과열 = 역신호 → 신규 지표 capex_to_rev 추가(음부호), inventory 부호 음.
3. peak_trap: peak 국면 valuation 신호 없음+유망 전무 → 블록4 "peak → 신규진입 deadzone 강화(floor↑)".
4. mean-reversion 메커니즘(val_gap→Δmultiple) = valuation 알파의 인과 채널.

**(거부/수정) flag:**
1. momentum(rev_growth/price_mom)의 직접 알파 약함(IC +0.05) → price_mom base_weight 하향(0.18→0.12), regime modulate 유지(early-cycle에서만).
2. book_to_bill 선행성 약함(합성 한계) → 실데이터 재검증 전까지 prior_strength 하향, confidence_hook reject 후보.

⚠️ 한계: 합성 픽스처. 실 EDGAR 펀더멘털 + XLY/XLI/XLB/XLE/XLF 구성종목 forward return 으로 재검증 필요(collector_plan + confidence_hooks 의 confirm/reject 가 라이브에서 이 IC 를 재측정).

---

## F. ★블록3 relationships 가설 검증 (5개 중 가능 항목만 — main self-check 보강)

### F.1 검증 가능 (semiconductor panel 내 proxy 존재)
**R5 (operating_leverage → fwd_eps_momentum, lagged, pos, prior 0.5 → 0.3 하향)**
- proxy: drv_gross_margin → t+1 drv_rev_growth
- IC = **+0.084 (약함)**
- partial IC | book_to_bill = **-0.013 (직접효과 사라짐)**: PMI/수주(book_to_bill)가 공통원인일 가능성.
- partial IC | inventory_qoq = +0.076 (재고 조건화 영향 미미)
- regime conditional: trough -0.022 / mid +0.055 / peak +0.035 — 모든 국면 약함.
→ **(거부 후보) flag**. 합성+proxy 한계. 실 DOL(ΔEBIT/Δ매출) 측정 후 재검증.

**R4 (rate_beta ↔ fwd_ep, direct, pos, prior 0.5) — 약식만**
- 약식: multiple ~ drv_gross_margin Rank-IC = **+0.370** (rate 조건화 부재 → 직접효과 분리 불가)
- 동조 방향 일치하나 "rate 효과" 자체 측정 안 됨 → 실 DGS10·종목벡터 적재 후 재검증.

### F.2 검증 불가 (거시지표 부재)
- R1 (ism_pmi → fwd_eps_momentum, prior 0.6): ISM 시계열 부재 → FRED NAPM 적재 후 라이브.
- R2 (credit_beta ↔ realized_vol, prior 0.55): HY OAS·종목벡터 부재 → FRED BAMLH0A0HYM2 + 가격 적재 후.
- R3 (dollar_beta ↔ oil_beta common_cause, prior 0.3): DXY·WTI·종목벡터 부재.

### F.3 결정
- yaml 블록3 R5 prior_strength 0.5 → **0.3 하향**, conditioning_set 에 book_to_bill 추가(직접효과 분리 시 더 약함 반영).
- glasso force-include 화이트리스트 ≤4 후보에서 R5 제외(prior 0.3 = 미강제). R1·R2 는 라이브 측정 후 재선정.
- R1~R4 라이브 재검증은 블록5 confidence_hooks 가 수행(블록6 collector 4건 적재 후).
