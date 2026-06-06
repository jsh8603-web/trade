---
tags: [type/findings, domain/equity-us, phase/rework-b2]
date: 2026-06-04
purpose: 미국 3 sleeve B″ 재작업 종합 결과 — 사용자 원질문("미국 시그널 약함 = 방법결함 vs 진실") 답 + yaml 통합 입력. SSOT 조정안=REWORK-B2-adjustment-plan / 자문=.consult-us-rework-3R-results.
status: mega_tech ✅ / defensive ✅ / cyclical ⏳(측정 중)
---

# 미국 3 sleeve B″ 재작업 종합 findings

> ★사용자 원질문 = "미국 시그널 약함이 방법결함인가 진실인가" + "후보 breadth 편중 의심" + "국면서 산다던 지표 frame 후 살았나".
> 답 = **둘 다 + 직관 적중**. 아래 sleeve별 정리.

## ★핵심 발견 2 (방법론)

### 발견 1 — "국면 survivor" 대부분 small-block NW over-rejection artifact
B″ R3(Claude) per-test calibration 경고(effective-n=block 한자릿수 + NW-HAC = Kiefer-Vogelsang size-invalid)가 **실증으로 정확히 적중**:
| 신호 | 구 방법(asymptotic/split) | B″ fixed-b size-valid | 판정 |
|---|---|---|---|
| defensive payout | split QE −0.122 **t−2.86** | continuous interaction fixed-b CV 2.09 비유의 | ★사망(artifact) |
| mega_tech capex×VIX | family_2b **t+2.34**(구 HAC) | post-AI n=29 신호구간 t1.94<CV2.86 wild p0.234 | ★사망(artifact, 전체 n=125 survive=pre-AI 희석) |
| cyclical family_2(vol_60/mom_6) | split diff +0.219/−0.211(block-boot CI) | ⏳fixed-b 진행 중 | ⏳(같은 패턴) |
→ ★"특정 국면서 산다"던 신호 = 대부분 small-block 검정 artifact. size-valid(fixed-b)에서 죽음. = 사용자 두 번째 직관 적중.

### 발견 2 — "약함"은 부분적으로 breadth 미측정(방법결함)
기존 "미국 시그널 약함" 판정은 valuation 기본 지표만 측정한 탓. B″ breadth 전 후보 sweep(net_issuance/52w/Amihud/op-prof/ROE/accruals, size-valid FDR family)하니:
- ★defensive **net_issuance FDR 생존**(직전엔 미측정) = "약함"이 breadth 편중 방법결함이었음 입증. = 사용자 첫 직관 적중.

## sleeve별 결과

### mega_tech ✅ — exposure overlay (alpha 신호 0, duration 노출만)
- sleeve_type = exposure_timing_overlay (verdict 폐기). cross-sectional factor = diagnostic(유효 n≈8 void).
- **real_rate β −0.210 t−5.14** = duration **EXPOSURE**(alpha 아님, n=185 time-series, fixed-b 무관). Gormsen-Lazarus expensive_trap.
- capex×VIX = ★diagnostic(size-valid 미입증, post-AI 사망). spillover CF lagged = underpowered null(MDE 0.24). breadth 11종 = 구조적 void(n≈8).
- ★결론 = compounder는 cross-sectional alpha 부재(archetype 정합) + duration 노출만 = supervisor macro overlay 입력(sleeve weight 아님).

### defensive ✅ — PARTIAL_CONFIRMED (net_issuance buyback-aversion)
- **net_issuance** = ★PARTIAL_CONFIRMED. IC+0.082 t3.31~4.40, 단일 FDR family 생존(raw_p 3e-05), regime-stable, LOO, fixed-b size-valid, ★직교화 incremental(⊥ep +0.084 t3.71 / ⊥payout +0.055 t2.41). buyback-aversion specific 채널.
  - hedge: 부호 anti-issuance(Pontiff-Woodgate 반대지만 sleeve anti-value 정합) / comm 4종 small-n sign flip / OOS·cross-market 미검증.
- ep_yield = TENTATIVE_DIRECTIONAL (anti-value, fixed-b size-valid 개별 유의 but FDR 미생존).
- payout/dividend = ★rejected(B″ NO_INTERACTION = split artifact). residual_mom = TENTATIVE. idio_vol = 무. real_rate = QUALIFIED(duration overlay).
- ★결론 = sleeve = anti-value/anti-buyback tilt(net_issuance가 cleanest size-valid 표현). breadth 안 쟀으면 놓쳤을 신호.

### cyclical ⏳ — 측정 중
- 기존(asymptotic): pbr IC−0.117 t−3.19 / ev_ebitda −0.110 CONFIRMED (sector-neutral, BY 8).
- ⏳ **fixed-b 재검정 핵심 관전**: pbr/ev_ebitda가 fixed-b size-valid에서도 CONFIRMED 유지하는지(유지=미국 최강 진성 신호 / 사망=cyclical도 흔들림). family_2 fixed-b. residual-mom. breadth sweep(net_issuance류).
- (결과 채울 자리)

## yaml 통합 입력 (재작업 후)
- mega_tech: exposure overlay = base_weight 0(cross-sectional), real_rate β = macro overlay 입력(supervisor L축).
- defensive: net_issuance PARTIAL = base_weight 소(hedge 반영), ep_yield TENTATIVE = observe-only.
- cyclical: (측정 후 확정).
- ★점추정 prior 박제 금지, small-n hedge, BY-FDR+M_eff, OOS observe-only. go-live 미접촉.
