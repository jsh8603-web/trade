---
tags: [type/validation, domain/inv, study/macro, group/B, audit/12-axis]
date: 2026-05-31
study_id: macro
session: btn-button (macro 스터디 방)
purpose: B그룹(collector 불필요·이미수집) 3 study 실데이터 검증 — (a)dollar/oil regime harness (b)real_rate/term_spread VIF 분리 (c)credit β per sleeve. 12축 audit-ready.
scripts: [bgroup_vif_rate_split.py, bgroup_credit_beta.py, bgroup_regime_harness.py]
note: "small-N rigor 준수(n/p/HAC/block-bootstrap/Bonferroni). 점추정 covariance prior 박제 금지 — (β,SE,t,n,tier) 분포 + James-Stein 권고."
---

# validation — B그룹 거시 누락지표 실데이터 검증

> **재현**: `raw/bgroup_{vif_rate_split,credit_beta,regime_harness}.py` 3 스크립트가 실 FRED CSV +
> sector ETF + eq_intl yahoo_cache 를 직접 읽어 산출. 아래 수치 전부 재실행 가능(audit §0 provenance).
> **소스 일자/n 전부 박제**(empirical-claim §1.1). 합성데이터 無 — 모두 실측.

## 0. 종합 verdict 표

| study | 대상 | verdict | 핵심 근거 | tier |
|---|---|---|---|---|
| **B(b)** rate축 분리 | real_rate(DFII10)+term_spread(T10Y2Y) | **CONFIRMED** | VIF 1.14, cond# 1.4, n=5854 (2003-2026, 위기포함) | validated |
| **B(c)** credit β cyclical | eq_us_cyclical | **CONFIRMED(방향)** | β≈−0.62 HY(t−8.7,Bonf) + BAA 26yr 위기포함 corroborate | structural(크기) |
| **B(c)** credit β defensive | eq_us_defensive_pure | **PARTIAL** | β≈−0.22(t−3.2,Bonf) 약, XLP 비유의, crisis −0.28 | structural |
| **B(c)** credit β gold/reit/commodity | — | **INSUFFICIENT** | 데이터 공백(reit/commodity) / overlap 1.5yr(gold) | hold |
| **B(a)** dollar/oil regime 활성 | JM feature 추가 | **REJECTED** | OOS Rank-IC 게이트 4/4 FAIL, 증분 Δ−0.095(악화) | 보류 유지 |

---

## 1. B(b) — real_rate / term_spread rate축 분리 (VIF 재측)

**가설**: 현 단일 `rate` factor 축을 real_rate + term_spread 2축으로 분리 가능 (Fisher 공선 회피 조건).

**데이터**: DFII10(real, 2003~) · T10Y2Y(term, 1990~) · T10YIE(breakeven) · DGS10(nominal). daily Δ(레벨차분).
**Coverage**: 2003-01-03 ~ 2026-05-28, **n=5854 거래일** (2008 GFC / 2020 COVID / 2022 금리쇼크 포함).

| 변수 set | VIF | corr | condition# | 판정 |
|---|---|---|---|---|
| **{real_rate, term_spread}** ★target | 1.14 / 1.14 | +0.351 | **1.4** | ✅ 무공선, 분리 가능 |
| {nominal, real, breakeven} (Fisher 위반) | **∞ / ∞ / ∞** | — | **1.8e14** | ⛔ 구조적 완전공선 |
| {real, term, breakeven} | 1.23 / 1.27 / 1.14 | — | 1.7 | ✅ (nominal 제외 시 OK) |

- **Fisher 항등 실측 확인**: `nominal − real − breakeven` mean=**+0.0000**, std=**0.0000** (FRED breakeven=nominal−real
  로 정의 → 정확 항등). 3종 동시투입 = VIF=∞ = 구조적 금지(measure-not-assume 확인).
- Δreal_rate lag-1 autocorr=+0.035, Δterm_spread=−0.009 → 거의 iid → block bootstrap block 작게 가능.

**verdict B(b) = CONFIRMED (validated)**: real_rate + term_spread 는 daily 직교(VIF 1.14, corr 0.35).
단일 rate 축을 2축으로 분리해도 공선 폭발 없음. **단 {nominal, real, breakeven} 동시투입은 금지**
(Fisher 정확항등 ∞). → `factor_betas_seed.FACTORS` rate→{real_rate, term_spread} 분리 안전(append-only).

> ⚠️ 본 study 는 공선성 **구조 진단**(VIF)이지 예측 claim 아님 → Rank-IC/게이트 비대상. 분리 *가능성* 입증이
> 목적이며, 각 축의 *예측가치* 는 별도(reit rate β / gold real-rate β 는 기존 sleeve study 가 측정).

---

## 2. B(c) — credit factor β per sleeve (Δ HY OAS)

**가설**: `factor_betas_seed` credit 칸(전 sleeve None=HOLD)을 채울 표준화 contemp β. credit stress↑
(ΔHY OAS>0) → 위험자산↓ → β<0 기대.

### 2.1 ★Coverage 정직 명시 (small-N rigor §1.1 / audit axis G·D)

- **PRIMARY HY OAS (BAMLH0A0HYM2)**: 2023-05-31 ~ 2026-05-28, **n=750 거래일(~36개월)**.
  ⚠️**위기표본 부재** — 2008 GFC, 2020 COVID, 2022 금리쇼크 credit 급확대 전부 윈도우 밖. **tail credit β 미관측**.
  (ERROR-202605302130 HY 37개월 위조 앵커와 동형 구조 — 본 study 는 그 한계를 verdict tier 로 정직 반영.)
- **ROBUSTNESS BAA10Y (Moody's BAA−10y, IG credit)**: 2000-01-04 ~ 2026-05-27, **n=6586**.
  HY 대용 아니나 credit 채널 동형 + **GFC/COVID/2022 위기 관측** → regime-conditional β + 방향 corroborate.

### 2.2 PRIMARY 결과 (Δ HY OAS, 표준화 β, Newey-West HAC L=10, block-bootstrap CI)

시도횟수 공시(axis K): **11 sleeve × 1 spread = 11 검정. Bonferroni α/11 → |t|>2.84 생존임계.**

| sleeve | β | NW-HAC t | 95% CI(block) | Bonf | walk-fwd (tr→te) | 판정 |
|---|---|---|---|---|---|---|
| **cyclical**(XLB,I,Y,F,E) | **−0.622** | −8.74 | [−0.74,−0.50] | ✅ | −0.55→−0.69 | CONFIRMED |
| XLY | −0.569 | −14.85 | [−0.64,−0.50] | ✅ | −0.48→−0.66 | CONFIRMED |
| XLI | −0.580 | −9.73 | [−0.68,−0.47] | ✅ | −0.50→−0.65 | CONFIRMED |
| XLF | −0.567 | −9.17 | [−0.67,−0.46] | ✅ | −0.48→−0.65 | CONFIRMED |
| XLB | −0.479 | −7.98 | [−0.58,−0.37] | ✅ | −0.43→−0.53 | CONFIRMED |
| XLE | −0.349 | −3.65 | [−0.50,−0.18] | ✅ | −0.32→−0.38 | CONFIRMED |
| **SPY(mkt)** | −0.621 | −9.87 | [−0.74,−0.52] | ✅ | −0.53→−0.70 | (참조) |
| XLV | −0.261 | −4.74 | [−0.36,−0.16] | ✅ | −0.21→−0.30 | CONFIRMED |
| **defensive_pure**(XLP,U,V) | **−0.224** | −3.21 | [−0.34,−0.10] | ✅ | −0.16→−0.28 | PARTIAL(약) |
| XLU | −0.158 | −2.57 | [−0.27,−0.05] | ·raw5%만 | −0.10→−0.24 | TENTATIVE |
| XLP | −0.117 | −1.89 | [−0.23,−0.00] | ✗ 비유의 | −0.11→−0.12 | **REJECTED**(F축 기각) |

- 전 sleeve **음(−) β** = credit stress↑ → 위험자산↓ (경제적 정합). walk-forward 부호 100% 안정,
  크기 te 가 tr 보다 약간 큼(최근 credit 민감도↑).
- **cyclical ≫ defensive** 위계 명확: cyclical −0.62 vs defensive_pure −0.22 (약 3배). XLP(staples)는
  **비유의**(t−1.89, CI 상단 −0.00) → credit 무차원 가설 **기각 1건**(F축, p-hacking 아님 입증).

### 2.3 ROBUSTNESS + ★tail-correlation (Δ BAA10Y, 위기포함, axis L)

| sleeve | full β(2000-2026) | t | **crisis β**(ΔBAA 상위10%, n=499) | normal β(n=6087) | tail 증폭 |
|---|---|---|---|---|---|
| cyclical | −0.238 | −7.71 | **−0.36** (t−5.1) | −0.17 (t−9.6) | **2.1×** |
| SPY | −0.240 | −8.97 | −0.37 (t−5.9) | −0.17 (t−10.0) | 2.2× |
| XLF | −0.206 | −6.74 | −0.31 (t−4.4) | −0.15 (t−8.4) | 2.1× |
| defensive_pure | −0.169 | −5.26 | **−0.28** (t−3.9) | −0.10 (t−5.9) | **2.8×** |

- BAA 절대크기 < HY(IG 가 risk-sensitivity 낮음·표준화 척도 차) 이나 **방향·위계 동일** → HY 결과
  corroborate(위기 26yr 포함). **crisis β ≈ normal β 의 2~2.8배** = tail-correlation 실측.
  방어주가 **위기에 더 크게 증폭**(2.8×, 쿠션 상실) → 점추정이 tail risk 과소표현.

### 2.4 verdict B(c)

- **방향(sign)**: **CONFIRMED** — HY(n=750,Bonf) + BAA(n=6586, 위기포함) 양 spread·전 regime 일관 음.
- **크기(magnitude) tier = STRUCTURAL(저신뢰)**: HY 점추정(−0.62 cyclical)은 **위기부재 윈도우** 산물 →
  validated alpha 위장 금지. covariance prior 박제 시 **crisis-conditional β 또는 James-Stein 수축**
  적용 의무(`factor_betas_seed` 가 structural tier → w≤0.25 강수축으로 이미 안전망).
- **defensive_pure = PARTIAL**, **XLP = REJECTED(credit 무차원)**.
- **gold/reit/commodity = INSUFFICIENT**: reit(VNQ)·commodity(DBC) 가격 데이터 공백 → collector 필요.
  gold(macro_yahoo 2021-2024) ∩ HY(2023-05~) overlap ~1.5yr → 단정 verdict 부적격(skip).

---

## 3. B(a) — dollar/oil regime-eval harness (활성 검정)

**가설(보류 2종 활성조건)**: dollar_broad/oil_wti 를 JM feature 추가 시 regime 분류 hit 개선되는가.
**조작화**: risk-off = forward 21d SPY ret(음). "분류 개선" = OOS 예측 Rank-IC. ⚠️동시상관은 tautology
(시장가격=risk 동시반영) → **PREDICTIVE(forward) OOS 만 인정**.
**게이트(axis B)**: |OOS Rank-IC|>0.03 AND |NW-t|>2.0. 시도횟수(K)= 신호2 × 자산2 = **4 검정**.

| 신호 | IS-IC | **OOS-IC** | NW-t | 95% CI(block=21) | 게이트 |
|---|---|---|---|---|---|
| dxy.level_z (2006-2026, 위기포함) | +0.075 | **−0.056** | −0.88 | [−0.167,+0.083] | ✗ FAIL **+부호반전** |
| dxy.mom20 | −0.006 | −0.009 | −0.16 | [−0.115,+0.106] | ✗ FAIL |
| oil.level_z (2021-2026) | −0.161 | −0.002 | −0.01 | [−0.351,+0.273] | ✗ FAIL |
| oil.mom20 | −0.054 | −0.238 | −1.80 | [−0.497,+0.039] | ✗ FAIL(CI 0포함) |

**증분 검정** (baseline 대비 순수 추가가치):
- baseline(real_rate Δ, term_spread, VIX) OOS-IC = **+0.206**
- + dxy/oil momentum → OOS-IC = **+0.111** → **Δ증분 = −0.095 (악화)**

**verdict B(a) = REJECTED (보류 유지)**:
- 4/4 신호 OOS 게이트 FAIL. dxy.level 은 IS+→OOS− **부호반전**(IS 과적합), 전 신호 CI 가 0 포함.
- dollar/oil 추가가 baseline OOS-IC 를 **−0.095 악화** → 노이즈. **tautology 우려가 데이터로 입증**:
  시장가격은 risk 를 *동시* 반영할 뿐 *예측* 력 없음. → `regime_classifier.py` L334~337 보류 주석이
  **데이터로 정당화**. 활성화 금지 유지. (F축 기각 1건, deprecation-evidence: null result 첨부 ✅.)
- ⚠️한계: 본 harness 는 **predictive** regime 가치 검정. JM 의 *contemporaneous nowcasting* 사용은
  미검정이나, tautology 위험이 정확히 거기 있으므로 OOS 예측증거 부재 시 활성 부당(보수적 유지).

---

## 4. 12축 self-audit 체크리스트 (감사관 cross-check 용)

| 축 | 본 study 대응 | 상태 |
|---|---|---|
| **A 이론실재성** | factor-beta prior(M3) + Fisher 항등 + tautology(FCI) 이론 근거 명시 | ✅ |
| **B 실데이터** ★ | FRED CSV + sector ETF 실측, n 박제. credit 방향 게이트 통과, 크기 tier 강등 | ✅(tier 정직) |
| **C 추적성** ★ | §5 yaml 매핑 — β 점추정→structural tier w≤0.25 수축 경로 명시 | ✅ |
| **D PIT/walk-forward** ★ | daily 시장가격(vintage 개정 無) + walk-forward OOS train→test 분리 | ✅ |
| **E 환각 cross-verify** | 외부 자문 수치 인용 0 (전부 본인 실측) | ✅ N/A |
| **F 반증+기각** | XLP credit β 기각 + dollar/oil 활성 기각 = **기각 2건** (p-hacking 아님) | ✅ |
| **G effective-N** ★ | HY 36개월 위기부재 → credit 크기 STRUCTURAL 강등(validated 위장 X) | ✅ |
| **H 미해결** | §6 confound 기재 | ✅ |
| **I 생존편향** ★ | sector ETF=상장유지 broad ETF(종목선택 無), 상폐편향 해당약. reit/commodity 공백 정직 flag | ✅ |
| **J 경제유의성** | credit β = 공분산 prior(거래신호 아님) → 거래비용 비대상. dollar/oil 활성 기각으로 J 무관 | N/A |
| **K 다중검정** ★ | 시도횟수 공시: credit 11검정/harness 4검정. Bonferroni α/11 적용 | ✅ |
| **L 통합정합** ★ | tail-correlation 실측(crisis β 2~2.8×), 중첩윈도우 NW-HAC/block-bootstrap SE 강제 | ✅ |

**Hard-fail 코어(B·C·D·I) 위반 0건.** 합성데이터 지문 無(실 FRED 결측·주말공백·2008/2020 이벤트 실재).

---

## 5. yaml/코드 반영 제안 (C축 추적성 — main 결정)

1. **`factor_betas_seed.FACTORS` rate 분리** (B(b) 근거): `("rate",...)` → `("real_rate","term_spread",...)`.
   append-only(중간삽입 금지, β=None HOLD). VIF 1.14 무공선 근거. **단 nominal+real+breakeven 동시 금지** 주석.
2. **`factor_betas_seed` credit 칸 채움** (B(c) 근거) — ⛔점추정 박제 금지, (β,SE,t,n,tier) 분포로:
   - `eq_us_cyclical` credit: β=−0.62, t=−8.74, n=750, **tier=STRUCTURAL**(위기부재→w≤0.25 수축),
     note="ΔHY OAS contemp, BAA 위기 corroborate, crisis β≈−0.36(2.1× tail)".
   - `eq_us_defensive` credit: β=−0.22, t=−3.21, n=750, tier=STRUCTURAL, note="약 credit β, crisis −0.28".
   - gold/reit/commodity credit: **HOLD 유지**(데이터 공백/overlap 부족).
3. **dollar/oil JM feature 보류 유지** (B(a) 근거): `regime_classifier.py` L334~337 보류 주석 **존치**.
   candidate-rationale.md 보류 2종 status → "OOS regime harness FAIL(증분 −0.095) → 보류 확정, 미채택 사유=실측 무상관" 갱신 가능.

---

## 6. 미해결 의문 (axis H)

- HY OAS 36개월 위기부재 → credit β tail 크기는 BAA proxy 외삽. **HY 장기시리즈(1996~) DBnomics fetch 시
  credit β 직접 위기측정 가능** → structural→validated 승격 후보(후속).
- reit(VNQ)/commodity(DBC) credit β 미측정 → collector 후 보강(A그룹과 별개, 가격 데이터만 필요).
- B(a) contemporaneous nowcasting 사용은 미검정(predictive 만 기각). JM 이 동시상태 추론에 dollar/oil 을
  쓸 경우의 가치는 별도 harness 필요 — 단 tautology 위험으로 보수적 보류가 안전.
- credit β = univariate(ΔHY 단일). market-beta 통제 후 partial credit β 는 eq_us_defensive study(XLF −0.166)
  와 별 측정값 — 공분산 prior 용도(univariate)와 신호 IC 용도(partial)는 다른 unit(§1.6 분리).
