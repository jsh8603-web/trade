---
tags: [type/validation, domain/inv, scope/equity-kr, sector/shipbuilding, layer/conditional]
date: 2026-06-05
---

# validation-conditional — 조선 conditional IC surface (S2 본체)

> raw 재현: `raw-v3/measure_conditional.py` (G-F 7항 헤더 선언) → `raw-v3/validation-conditional-v3.json`
> regime: Macro(FRED CLI amplitude-adj 4) × KRW(DEXKOUS yoy 3) × flow(ECOS 외국인순매수 28d z 3)

## 측정 = IC(지표, regime, horizon)
- horizon = y_5d / y_20d(메인) / y_60d 일간 forward.
- per-cell = wild-cluster bootstrap p(Rademacher B=2000) + n_eff(autocorr) + block-boot CI.
- ★36셀 full N≥24 = 0개(최대 N=18) → INSUFFICIENT. 단일축(Macro 4 / KRW 3 / flow 3) + family_2 interaction.

## 핵심 결과 (각 수치 = validation-conditional-v3.json key)

| 신호 | y_20d uncond IC | wc_p | n | OOS(IS→OOS) | 판정 |
|---|---|---|---|---|---|
| **vol_60** (저변동) | -0.0568 | 0.1284 | 81 | -0.065→-0.049 ✅부호유지 | ★TENTATIVE(유일 OOS 생존) |
| mom_6 | -0.0416 | 0.2874 | 81 | -0.073→-0.008 소멸 | INSUFFICIENT |
| mom_12_1 | -0.0291 | 0.5232 | 75 | 소멸 | INSUFFICIENT |
| rev_1m | -0.0386 | 0.2464 | 81 | -0.096→+0.024 ★반전 | INSUFFICIENT |
| pbr_z | -0.0119 | 0.7531 | 81 | -0.038→+0.016 ★반전 | INSUFFICIENT |

- **FDR family (단일, G-F §3)**: m=87, BY survivors=[], raw_p_min=0.065(mom_6 y_5d) = ★전 신호 비유의.
- **vol_60 regime cell**: Reflation IC -0.155(wc_p=0.03, underpowered) / flow_neutral -0.088(wc_p=0.088) = 증폭.

## family_2 interaction (G-B 의무, rejected 박제 前)
- method: pooled panel ret_rank ~ sig_rank + sig_rank×KRW_weak_dummy, month-clustered SE.
- ★전 신호 interaction 비유의 (mom_6 t=1.14 / rev_1m t=0.14 / vol_60 t=0.87). = 반도체와 차이(반도체 mom_6 t=-2.95 유의).
- = "국면 따라 신호 효과 갈림"(A-5)이 ★조선엔 미입증. sign-flip 28건 있으나 정식 interaction 전부 비유의.

## verdict
★조선 conditional = 약. vol_60 방향만 OOS 생존(BY 미생존+CI 0포함=magnitude 비유의). = 산업베타 지배(H9) 정합.
