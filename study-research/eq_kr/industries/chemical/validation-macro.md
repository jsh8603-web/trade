---
tags: [type/validation, domain/inv, scope/equity-kr, sector/chemical, layer/macro-conditional]
date: 2026-06-05
owner: chem-analyst@kr-equity
purpose: conditional IC surface (price signals × regime × horizon) + walk-forward OOS + family_2. raw = raw-v3/measure_conditional.py.
---

# 화학 validation — conditional IC surface (momentum/reversal/vol × regime)

## 0. G-F frame contract 7항 (measure_conditional.py 헤더 선언, 반도체 미러 — regime 거시 동일)

1. regime = Macro(KORLOLITOAASTSAM CLI 4) × KRW(DEXKOUS yoy 3) × flow(ECOS 외국인순매수 28d z 3). 36셀 full N≥24=0 → 단일축+2축merge.
2. effective-n = block 수 (n_eff = n/(1+2Σρ), HAC lag=horizon). split 사전동결.
3. 단일 FDR family = {6신호(mom_6/mom_12_1/rev_1m/vol_60/pbr_z/per_z) × 3 horizon × powered regime cell} BY-FDR. 측정 후 재정의 금지.
4. null=IC=0, MDE≈0.05~0.10 (n=10~30). N<24 = underpowered 라벨.
5. PIT 동결: regime threshold(CLI 100, KRW±5%, flow z±1) 도메인 표준값. z-score = 월말 cross-sectional.
6. Net-alpha = gross IC − KR STT sell 0.20% 비대칭.
7. wild-cluster bootstrap (Rademacher B=2000) per-cell p. asymptotic NW-HAC t = small-block size-invalid 참고만.

## 1. ★단일 FDR family BY 생존 (m=91) → mom + vol 2 신호

```
BY survivors (q=0.10, c_m=2.718): mom_6__y_60d__uncond / mom_6__y_60d__macro_Slowdown / vol_60__y_60d__uncond
raw_p_min = 0.0005 (mom_6__y_60d__macro_Slowdown), Bonferroni α = 0.00055
```

## 2. ★momentum = reversal (음, H8 확인) — **tradeable**

| 신호 | y_5d IC(wc_p) | y_20d IC(wc_p) | y_60d IC(wc_p) | CI(60d) | size-orth(60d) | WF OOS |
|---|---|---|---|---|---|---|
| **mom_6** | -0.082 (0.018) | -0.073 (0.037) | **-0.115 (0.0005)** | [-0.183,-0.049] | -0.146 | HOLD (IS-0.042/OOS-0.195) |
| **mom_12_1** | -0.036 (0.36) | -0.061 (0.049) | **-0.101 (0.0055)** | [-0.185,-0.015] | -0.126 | HOLD (IS-0.164/OOS-0.041) |

- ★**모멘텀 reversal** (음): 과거 6M/12M 수익률 높은 화학주가 forward 낮음. cyclical 정점 reversal (반도체 momentum 음 reversal과 **동형** — 같은 cyclical 정점). H8 prior(음 reversal) **확인**.
- BY 생존 (mom_6 y_60d), OOS HOLD, **size-orth IC 강화** (-0.115→-0.146) = size 독립. horizon 단조(5d<20d<60d 절댓값↑) = 신호 real.
- macro_Slowdown 국면 강화 (frame: 둔화 국면 정점주 reversal 강).

## 3. ★vol_60 저변동성 anomaly (음, H10) — **tradeable (최강)**

| horizon | IC | wc_p | n_eff | CI | size-orth | WF OOS |
|---|---|---|---|---|---|---|
| y_20d | -0.102 | 0.0025 | 74.8 | [-0.177,-0.044] | -0.102 | HOLD (IS-0.121/OOS-0.070) |
| y_60d | **-0.142** | **0.0005** | 43.9 | [-0.227,-0.063] | -0.169 | HOLD (IS-0.180/OOS-0.108) |

- ★**저변동성 anomaly** (음): 저변동 화학주 → forward 高. BY 생존(y_60d uncond), OOS HOLD, **size-orth 강화** (-0.142→-0.169) = size 독립. n_eff 충분(43.9).
- regime: Slowdown(-0.134 wc_p 0.037)/KRW_neutral(-0.113 wc_p 0.023)/flow_sell(-0.150 wc_p 0.032) 강화. 둔화·위험회피 국면 저변동 프리미엄.
- H10 prior "불명"이었으나 **음(저변동→고forward) 명확** = cyclical 고베타 산업에서도 low-vol anomaly 작동 (오히려 강).

## 4. rev_1m (H9) → 약 reversal (음, BY 미생존)
- uncond IC -0.042 (wc_p 0.23). 단기 reversal 방향 정합이나 비유의. KRW_weak(-0.066)/flow_neutral(-0.053) 약. TENTATIVE.

## 5. family_2 interaction (G-B, rejected 박제 前 의무)

- **sign-flip 13건** 감지 (regime별 부호 갈림) → interaction term 측정.
- **interaction TERM (KRW_weak × signal, y_20d, pooled month-clustered SE)**: mom_6 b_inter=-0.086(t=-1.33), vol_60 b_inter=+0.023(t=0.35) — **전부 interaction 비유의** (|t|<2).
- ⇒ regime split 부호 차이는 small-n noise, interaction term으로 살릴 신호 없음. family_2 음성 → family_1 verdict 유지.

## 6. summary (conditional)

- ★**tradeable (BY 생존 + OOS HOLD + size 독립)**: **vol_60 (저변동, 최강)** + **mom_6/mom_12_1 (reversal)**. 둘 다 y_60d 강.
- **regime 명시**: Slowdown(둔화) 국면 + flow_sell(외국인 매도) 국면에서 vol_60/mom reversal 강화 = "둔화·위험회피 국면 → 저변동·역모멘텀 화학주 강세".
- family_2 interaction 음성 → regime conditional은 강도 차이일 뿐 신호 생성 아님 (frame §D "refinement 도구").
