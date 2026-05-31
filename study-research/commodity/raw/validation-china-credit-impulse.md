---
tags: [type/validation, domain/commodity, indicator/china-credit-impulse, phase/m3-missing-indicator]
date: 2026-05-31
producer: main (btn-Codlearn) 직접 — commodity 세션(jpdf) eq_us 전환으로 부재
trigger: 사용자 정정 2026-05-31 "register≠지표추가, 최초 M3 흐름(이론→실데이터→상관계수→yaml) 그대로"
data_source: DBnomics (BIS·IMF 원천, 합성 아님). 스크립트 raw/m3-china-credit-impulse-v2.py
result_json: raw/m3-china-credit-impulse-results.json
---

# validation — China credit impulse → commodity(copper) 실데이터 검증

> **누락지표 배경**: `china_credit_impulse_z` 는 theory-notes.md(L401·L415) + 자문 R2/R3 에서
> industrial metals B-matrix 핵심 컬럼으로 이론화됐으나, 최종 검증에서 "Caixin 무료 데이터 없음"
> 이유로 INDPRO YoY proxy 로 대체 → 실 China 신용 데이터로 미검증 + yaml indicators 누락.
> 본 검증 = 그 공백을 최초 M3 흐름대로 메움.

## ① 이론 (theory-notes 정독 결과 요약)
- China credit impulse = 신규 신용 flow / GDP 의 변화(Biggs et al. 2009). 실물·원자재 수요 선행지표.
- 전달 채널: PBOC 신용 확대 → 인프라·부동산 투자 → industrial metals(copper/iron) 수요 → 가격.
- 학계·실무 통설 lead = **6-12m (2-4 분기)**. China = industrial metals 한계 수요자(전세계 ~50%).

## ② 실데이터 (DBnomics, FRED 호스트 timeout 회피, BIS·IMF 원천 = 비합성)
| 시리즈 | 코드 | n | 기간 |
|---|---|---|---|
| China 민간비금융 Credit-to-GDP % (break 조정) | BIS/WS_TC/Q.CN.P.A.M.770.A | 157 | 1985-10 ~ 2024-10 |
| China Credit-to-GDP **gap** (actual-trend, BIS 신용사이클) | BIS/WS_CREDIT_GAP/Q.CN.P.A.C | 117 | 1995-10 ~ 2024-10 |
| Global copper price USD/mt | IMF/PCPS/M.W00.PCOPP.USD | 426 | 1990-01 ~ 2025-06 |

**impulse 구성 3종** (spec/code 1:1):
- `flow4_creditgrowth` = R_t − R_{t−4} (4분기 신용/GDP 증분, loose impulse)
- `biggs_accel` = (R_t−R_{t−4})−(R_{t−4}−R_{t−8}) (Biggs 2009 정통 = 가속도)
- `bis_gap_level` = WS_CREDIT_GAP 직접 (BIS 공식 신용갭)

## ③ 측정 — copper forward 분기수익률과 Spearman / Rank-IC (small-N rigor)
forward 1~6분기 × 3 impulse = 18 test. n=113~116 분기(overlap).

| impulse | best fwd_q | Spearman ρ | raw p | **Newey-West HAC p** | block-boot ρ 95%CI |
|---|---|---|---|---|---|
| flow4_creditgrowth | 4-5q | +0.140~0.146 | 0.089~0.102 | **0.44~0.46** | [−0.15, +0.44] (0 포함) |
| biggs_accel | 6q | +0.176 | 0.041 | **0.26** | [−0.13, +0.43] (0 포함) |
| bis_gap_level | 1-6q | +0.02~0.08 | 0.40~0.80 | 0.61~0.85 | (0 포함) |

**다중비교 18 test**: Bonferroni α=0.0028 → 생존 **0** / Newey-West HAC p<0.05 → 생존 **0** / BH-FDR → 생존 **0**.

## ④ verdict (empirical-claim rule 5단계)
★**TENTATIVE DIRECTIONAL** (방향성 약 prior, 비유의):
- 부호는 이론 정합 — credit impulse ↑ → copper forward return ↑, 4-6분기 lead 에서 ρ 최대(이론 6-12m lead 와 정합).
- 그러나 **자기상관 보정(Newey-West HAC) + 다중비교 보정(Bonferroni/FDR) 후 전부 비유의**. block-bootstrap CI 모두 0 포함.
- raw p 만 보면 biggs 6q(0.041)·flow4 5q(0.089) "신호 같아" 보이나 = overlap 자기상관 인공산물.

★**INSUFFICIENT 격하 사유 (validated alpha 주장 금지)**:
- **데이터 proxy 한계**: BIS credit-to-GDP = **stock 비율** proxy. 정통 China credit impulse = **TSF(사회융자) flow/GDP** 인데 TSF 공개 API 부재 → BIS 비율로 대체. spec("TSF flow")↔code("BIS stock 비율 차분") drift 존재 → 진짜 impulse 보다 신호 희석 가능성.
- copper 단일 commodity (industrial sleeve 대표). 전 commodity 아님.

## ⑤ yaml 반영 방침 (★5금지 준수)
- ⛔ **점추정 박제 금지**(5금지 ①): ρ=+0.14/+0.18 등 covariance prior 박제 X.
- → `china_credit_impulse_z` indicator 등록하되 **prior_tier: structural_low_confidence + validated_alpha: false + wide-prior**.
- INDPRO YoY(기존 H4 copper bellwether) 와 **공통 trend(글로벌 산업수요) 매개** — 별 alpha 아니라 보강 conditioning.
- **재검증 falsifier**: TSF flow/GDP 실데이터 확보 시(OpenBB China extension 또는 PBOC scrape) 재측정. HAC p<0.05 + Bonferroni 생존 시 structural→validated 승격. 미생존이면 freeze 유지.
