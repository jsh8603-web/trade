---
tags: [type/validation, study/eq_us_cyclical, topic/merit-leading-vars]
date: 2026-06-01
study_id: eq_us_cyclical
phase: "merit 변수 탐구 — M6 자문 cyclical 누락(ISM 신규주문·PMI·fwd EPS revision breadth) 무료 FRED 대체"
script: raw/validation-merit-cyclical-leading.py
output_json: raw/validation-merit-cyclical-leading.json
pit_probe: raw/merit-pit-probe.json
fetch_script: raw/fetch_merit_leading.py
data_integrity: "합성·시뮬 無. FRED API + yfinance 실데이터. fetch 실패 raise."
verdict_overall: "TENTATIVE DIRECTIONAL (Bonferroni/BH-FDR 0/96 생존). DGORDER→XLE forward = live PIT 생존 최강 후보(단 단정 금지)."
---

# merit 변수 탐구 — cyclical 무료 선행변수 (ISM 대체)

> M6 자문: "cyclical 누락 critical = ISM 신규주문·PMI 선행·forward EPS revision breadth". ISM/estimate 는 유료.
> 본 검증 = **무료 FRED 대체 선행변수**의 forward 예측력 탐구. 대상 = SOXX/XLB/XLI/XLE 월간 log-return.
> H3(2026-05-30)이 diluted cyclical-defensive excess 로 REJECT 한 것의 **종속 재정의(섹터 단독) + live PIT 정렬** 후속.

## 데이터 coverage (§1.1 의무)

- **종속**: SOXX/XLB/XLI/XLE 월간 log-return. yfinance `sector_etf_close.csv`. 월말 인덱스 **2000-01-31 ~ 2026-05-31** (XLE/XLB/XLI n=317 month, SOXX inception 2001-07 → 실제 join n=~298).
- **선행 후보** (FRED, 무료):
  | 후보 | series | 변환 | n(월) | 발표시차(ALFRED median) |
  |---|---|---|---|---|
  | NEWORDER_yoy | core capex 신규주문 ex-aircraft | yoy | 399 | **56d** |
  | AMTMNO_yoy | mfg 신규주문 | yoy | 398 | **64d** |
  | DGORDER_yoy | 내구재 신규주문 | yoy | 399 | **56d** |
  | ACOGNO_yoy | 소비재 신규주문 | yoy | 398 | **64d** |
  | PERMIT_yoy | 주택착공 허가 | yoy | 784 | **48d** |
  | T10Y2Y / T10Y3M | 수익률곡선 | level | 437 / 533 | 0 (시장가격) |
  | COPPER_GOLD_yoy | copper/gold 비율 (HG=F/GC=F) | yoy | 298 | 0 (시장가격) |
- 신규 fetch = `fetch_merit_leading.py` (PERMIT/T10Y3M/ACOGNO/PCOPPUSDM + copper_gold_ratio.csv). 기 적재 = NEWORDER/AMTMNO/DGORDER/T10Y2Y.

## ★PIT 핵심 — lookahead 착시 정량 (eq_intl credit 재발 방지)

FRED 월간 거시 = **revised + 발표시차 48~64일**. `observation_date` 는 *참조 기간*이지 *알 수 있던 시점*이 아님.
- **NAIVE 모드**: signal 을 observation 기간에 정렬 (revised, 발표 전 시점 사용 = lookahead-prone).
- **LIVE 모드**: signal 을 **first-release 가능일 (기간말 + median 발표시차)** 로 shift. forward return 은 그 이후에만 매칭.
- copper/gold·yield curve = 시장가격 일별 → PIT-clean (shift 불필요).

ALFRED first-release probe (`merit-pit-probe.json`) = median 48~64d / max 86~130d 발표시차 실측. caveat: median 시차만 적용(개별 vintage revision magnitude 미반영) — 보수적으로 라이브 부호/크기 더 약해질 여지 잔존.

## spec ↔ code 1:1 verify (§1.3)

- Spec: "후보 z/yoy 가 향후 k=1/3/6m 선도수익 예측" → Code: `fwd = ret_m.rolling(k).sum().shift(-k)` (forward k-month sum). PASS.
- Spec: "동월 co-move" → Code: k=0 = `ret_m[target]` 동월. PASS.
- Spec: "live PIT" → Code: signal index = `(period_end + pub_lag).MonthEnd`, forward return 그 이후 매칭. PASS.
- ADF: `adfuller(regression='c', autolag='AIC')` — 8/8 후보 I(0) stationary (yoy/level 변환으로 단위근 제거, §1.7-A 통과). 잔차 spurious 회귀 risk 없음.
- t-stat: rank-IC 의 Newey-West HAC (overlapping forward window → `maxlags = nw_lag + (k-1)`, §1.4 자기상관 보정). CI: block bootstrap (block=max(k,6), B=3000, §1.4).

## 결과 (LIVE PIT 모드, rank-IC, n/p/95%CI)

★별표 = p<0.05 AND block-boot CI 비-cross-zero. **단 다중비교 보정 전 (m=96).**

### XLE — DGORDER_yoy = forward 예측 생존 최강 (anti-cyclical 본성과 정합)
| k | IC | NW t | p | n | 95% CI(block-boot) | cross0 |
|---|---|---|---|---|---|---|
| 0 (동월) | +0.200 | +3.32 | 0.0009 | 317 | [+0.079, +0.314] | no |
| 1m fwd | +0.177 | +3.00 | 0.0027 | 316 | [+0.065, +0.293] | no |
| 3m fwd | +0.230 | +2.82 | 0.0048 | 314 | [+0.074, +0.384] | no |
| 6m fwd | **+0.311** | +3.16 | 0.0016 | 311 | [+0.120, +0.482] | no |

- ★**lookahead 착시 미미**: naive k=3 +0.296 → live +0.230 (소폭 하락, 부호·유의 유지). live k=6 가 오히려 최강 = revised-vintage 인공물 아님.
- half-split OOS k=3: h1 +0.12 / h2 +0.33 = **부호 일치 MATCH** (both>0.1).
- 해석: 내구재 신규주문 yoy ↑ → XLE 향후 6m 강세. XLE anti-cyclical hedge 본성(M3 E1/E3 sleeve 역행)과 도메인 정합(수요 모멘텀 = 원자재/에너지 수요 선행).

### SOXX — ACOGNO_yoy = forward **음**의 예측 (역방향, live 생존)
| k | IC | NW t | p | n | 95% CI | cross0 |
|---|---|---|---|---|---|---|
| 0 | -0.124 | -2.32 | 0.0207 | ~298 | — | no |
| 3m fwd | -0.214 | -2.34 | 0.0191 | 314 | [-0.386, -0.018] | no |
| 6m fwd | -0.250 | -2.23 | 0.0258 | 311 | [-0.451, -0.026] | no |

- 소비재 신규주문 yoy ↑ → SOXX 향후 약세 (역방향 = late-cycle 과열 신호로 reverse). naive 와 부호·크기 유사(착시 적음).
- OOS: SOXX 자체는 보고 안 됨(|IC|<0.1 한쪽), 단 ACOGNO_yoy → XLB(h1 -0.19/h2 -0.17)·XLI(-0.14/-0.14) 음부호 OOS MATCH = 소비재 신규주문이 cyclical-core(XLB/XLI)에도 음의 forward (역방향 일관).

### NEWORDER_yoy → XLE = ★lookahead 착시 명확 (live 붕괴)
| 모드 | k=3 IC | NW t | p | CI | cross0 |
|---|---|---|---|---|---|
| naive | +0.206 | +2.56 | 0.0106 | [+0.051, +0.357] | no |
| **live** | +0.137 | +1.65 | 0.0999 | [-0.032, +0.291] | **YES** |

- ★capex 선행 후보(M6 자문이 ISM 신규주문 대체로 가장 기대)인데 **live 정렬 시 유의성 붕괴 + CI cross-zero**. = eq_intl credit-impulse 동월 +0.41 → 라이브 붕괴 패턴 재현. 발표시차 56일이 forward 3m 신호 절반 잠식.
- AMTMNO_yoy → XLE 동월: naive +0.178(t=3.2) → live +0.124(t=2.3), 약화하나 동월은 생존(발표시차가 동월 co-move 일부만 잠식).

### co-move only (forward 미생존)
- COPPER_GOLD_yoy → XLE 동월 +0.151 (t=2.64, CI[+0.04,+0.26]) = co-move 유의, **forward 미생존**(k≥1 비유의). 시장가격이라 동월 동조 당연, 선행 아님.
- T10Y2Y / T10Y3M (수익률곡선) → 4 섹터 전부 |IC|<0.11, **전 horizon 비유의**. cyclical 섹터 월간수익에 선행 신호 부재(curve 는 침체 12-18M 선행이나 섹터 월수익 rank엔 약함).
- PERMIT_yoy → 4 섹터 전부 비유의 (주택 선행 채널이 이 4 섹터엔 무전달).

## ★다중비교 보정 (§1.5, K축)

- m = **96** forward predictive 비교 (8후보 × 4섹터 × 3 horizon, LIVE k>0).
- Bonferroni α = 0.05/96 = 0.00052 → **생존 0/96**.
- BH-FDR q=0.05 → **생존 0/96**.
- ★결론: 어느 cell 도 다중비교 후 유의 생존 X. DGORDER→XLE k=0 p=0.0009 가 최소이나 Bonferroni 임계 0.00052 미달.

## verdict (5단계, §2)

| 후보·관계 | verdict | 근거 |
|---|---|---|
| **DGORDER_yoy → XLE forward(1/3/6m)** | **TENTATIVE DIRECTIONAL (★최강)** | n>300·live 생존·OOS MATCH·착시 미미. 단 Bonferroni 0/96 → 단정 금지. 양(+) 방향 prior. |
| ACOGNO_yoy → SOXX/XLB/XLI forward | TENTATIVE DIRECTIONAL | 음부호 live 생존·OOS MATCH(XLB/XLI). 단 Bonferroni 미생존. 음(-) 방향 prior. |
| AMTMNO_yoy → XLE | TENTATIVE DIRECTIONAL (동월 한정) | 동월만 live 생존, forward 약. |
| NEWORDER_yoy → XLE forward | ★REJECTED (live) | naive 유의 → live 붕괴(p=0.10, CI cross0). lookahead 착시. |
| COPPER_GOLD_yoy → XLE | co-move only | 동월 유의, forward 미생존. |
| T10Y2Y / T10Y3M → 4섹터 | REJECTED | 전 horizon 비유의. |
| PERMIT_yoy → 4섹터 | REJECTED | 전 horizon 비유의. |

**전체 verdict = TENTATIVE DIRECTIONAL**. cyclical "선행" 기대가 큰 영역이나, 무료 FRED 신규주문류의 forward 예측력은 **다중비교 후 통계적 유의 부재**. 다만 DGORDER→XLE 와 ACOGNO→SOXX 는 live PIT·OOS 일관성을 갖춘 방향성 prior 로 가치 있음(structural_low, magnitude 박제 금지).

## 12축 audit-ready

| 축 | 상태 | 근거 |
|---|---|---|
| A 이론 | PASS | capex/신규주문 = ISM 신규주문 무료 대체, 수익률곡선 Estrella-Mishkin, copper/gold 성장게이지. |
| **B 실데이터** | PASS | FRED API + yfinance 실측 n>300월. 합성 無(fetch 실패 raise). ADF 8/8 I(0). |
| **C 추적성** | PASS | yaml 미수정(본 산출은 verdict 단계). md↔json↔py 수치 일치. |
| **D PIT** ★ | **PASS** | ALFRED first-release probe 발표시차 실측 → LIVE shift 적용. NAIVE vs LIVE 양측 보고로 lookahead 착시 정량(NEWORDER→XLE 붕괴 실증). |
| E 자문비판 | PASS | M6 자문(ISM/estimate) = 유료 → 무료 대체로 falsify. 자문 "신규주문 선행" 무비판 채택 X (NEWORDER live 붕괴 보고). |
| **F 반증** | PASS | REJECTED 4건(NEWORDER live·curve·PERMIT·copper forward) 기록. |
| G effective-N | PASS | n>300월. 단 거시 autocorr·overlapping window → NW HAC + block-boot. tier=structural_low. |
| H 미해결 | PASS | 아래 §미해결. |
| I 무결성 | PASS | ETF level(survivorship 비대상), copper/gold auto_adjust. SOXX holdings drift caveat 잔존. |
| J 경제적 | DEFERRED | turnover/비용 미차감(월간 rank-IC = lens·prior 용도). |
| **K 다중비교** ★ | PASS | m=96 공시, Bonferroni 0/96 + BH-FDR 0/96 명시. |
| L 상관무결성 | PARTIAL | **curve(T10Y2Y) ↔ credit(IG spread, 기존 블록3) 중복 risk** — 본 검증 curve 비유의라 중복 미발생. DGORDER↔기존 ism_pmi_proxy(AMTMNO) 동일 family 중복 주의(아래). |

hard-fail (B/C/D/I) 없음.

## L축 중복 점검

- DGORDER_yoy 와 기존 yaml `ism_pmi_proxy`(AMTMNO/CFNAI 계열) = **동일 new-orders family**. DGORDER→XLE 만 forward 살아있고 AMTMNO 는 동월 한정 → DGORDER 가 ism_pmi_proxy 의 **섹터별(XLE 한정) 정밀화**로 통합 권장(중복 계상 X).
- T10Y2Y(curve) ↔ credit_beta(IG spread) = 둘 다 침체/risk 채널이나 본 검증 curve 비유의 → 중복 베팅 미발생.

## 미해결 의문

1. NEWORDER live 붕괴 = 발표시차 56d 잠식인가, 본질적 무신호인가. ALFRED 개별 vintage revision magnitude 반영 시 재확인 필요(median 시차만 적용한 caveat).
2. DGORDER→XLE = anti-cyclical hedge(수요모멘텀)인가 단순 commodity-cycle co-trend인가. EDGAR energy 펀더(breakeven/reserves) 적재 후 분리.
3. ACOGNO→SOXX 음부호 = late-cycle 과열 reverse 가설. regime-conditional split 로 확인 필요(현 full-sample pooling).
4. 4 섹터 모두 Bonferroni 미생존 = "선행 기대 큰 cyclical"의 무료 데이터 한계. 유료 fwd EPS revision breadth(FINNHUB/IBES) 가 진짜 신호일 가능성 — 본 무료 대체는 prior 보강 수준.
