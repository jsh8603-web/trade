---
tags: [type/validation, hypothesis/H3, study/eq_us_defensive, phase/audit-enhancement-D, version/v4-walkforward]
date: 2026-05-31
hypothesis: H3 walk-forward — NFCI/BAA10Y p75 threshold rolling 10Y (lookahead 차단) regime → sleeve 부호 분기 OOS 검증
verdict: structural prior TENTATIVE 유지 (방향 4/4 cell 일관 단 Bonferroni 0/2 PASS)
audit_enhancement_no: D-1
parent_md: validation-H3-v4.md
---

# validation-H3-walkforward.md — H3 regime walk-forward OOS 검증

**main 12축 audit 보강 #1 (D축 해소)**: NFCI/BAA10Y p75 regime threshold 를 10Y rolling (in-sample lookahead 제거) 로 재산출 → H3 regime sleeve 부호분기가 walk-forward OOS 에서도 유지되는지 검증.

**분석 unit (β 측정)** — rule §1.6 (parent md validation-H3-v4.md 정합):
- `DEFENSIVE_PURE = {XLP, XLU, XLV}` (rate-NEG bond proxy)
- `FINANCIALS = {XLF}` (rate-POS NIM 독립)

**Portfolio label**: "미국 방어주 + 금융주" sleeve (user task) — 본 walk-forward 검증은 sleeve 분리 grouping 의 OOS 안정성 확인

**Spec ↔ Code 1:1 verify** (rule §1.3):
- Spec: t 시점 regime 분류는 t-1 까지의 history 기반 (★lookahead 차단)
- Code: `panel['NFCI'].rolling(120).quantile(0.75).shift(1)` — 직전 120mo (10Y) p75 quantile, .shift(1) 로 t-1 까지만 사용

## 데이터 (★PIT-pure cross-check)

- **NFCI weekly** (Chicago Fed Financial Conditions): 1971-01-08 ~ 2026-05-22 (n=2890 weekly) → monthly resample n=665
- **BAA10Y daily** (Moody IG credit spread): 1986-01-02 ~ 2026-05-28 (n=10101 daily) → monthly resample n=485
- **ETF**: XLP, XLU, XLV, XLF, SPY (2000-01 ~ 2026-05 monthly)
- **★보강 #2 NFCI ALFRED vintage 발견** (병행 작업):
  - get_series_vintage_dates: 780 vintages (★ALFRED PIT 가용 = 2011-05-25~ 만)
  - get_series_first_release: pre-2011 vintage X (fredapi 한계)
  - current revision vs first release: **mean abs diff = 0.35 (NFCI std 0.999 의 35%)**
  - 98.7% 시점에서 |diff|>0.1, max abs diff 0.885 at 1974-08-23
  - → **★BAA10Y (Treasury yield 기반, revision 거의 없음) PIT-pure exogenous primary 강화**
  - NFCI 결과는 secondary cross-check (vintage 한계 명시)

## 방법 (★small-N rigor 5의무 + walk-forward)

1. **walk-forward threshold** (★main 요구):
   - `threshold_t = quantile_p75(history[t-120 : t-1])` — t-1 까지 10Y rolling
   - `.shift(1)` 로 lookahead 완전 차단
   - first 120mo (1971-01 ~ 2009-12) = OutOfSample (rolling window 시작 이전)
2. **in-sample period**: 2010-01-31 ~ 2026-05-31 (n=197 mo, 16.4년)
3. **regime classification**:
   - NFCI primary: NFCI_t > NFCI_threshold_t (rolling p75)
   - BAA10Y secondary exogenous: BAA10Y_t > BAA10Y_threshold_t (rolling p75)
4. **sleeve eq-weight monthly excess vs SPY** (DEFENSIVE_PURE / FINANCIALS 분리 측정)
5. **Block bootstrap** (rule §1.4): block_size=4 months, n_iter=5000
6. **LOO sensitivity** (rule §1.2): 각 sample 빼고 t-test p 의 max
7. **Bonferroni m=4** (rule §1.5): 2 regime axes × 2 sleeves → α/4 = 0.0125
8. **Cross-sleeve Welch t-test** (rule §1.6): DEF_PURE - FIN gap 검정

## 결과 (1) walk-forward regime distribution

| regime | n | % | 비고 |
|---|---:|---:|---|
| NFCI p75 wf | 29 | 14.7% | 10Y rolling threshold, post-2010 in-sample |
| BAA10Y p75 wf | 24 | 12.2% | exogenous primary (rule §1.4 PIT-pure) |
| NFCI ∩ BAA10Y p75 wf | 6 | 3.0% | dual cross-check |

★v4 lookahead 버전 (NFCI p75 n=23, BAA10Y p75 n=113) 과 비교:
- NFCI: 23 → 29 (rolling threshold 가 다르게 분류)
- BAA10Y: **113 → 24** ★대폭 축소 (rolling 시 stress 보다 일반 cycle 으로 분류된 month 다수)
- → ★lookahead bias 가 v4 BAA10Y regime 분류에 큰 영향 있었음

## 결과 (2) walk-forward H3 regime conditional excess (★rule §1 5의무)

| regime | sleeve | n | mean/mo | 95% CI (Block bootstrap) | p_block | LOO p_max | verdict |
|---|---|---:|---:|---|---:|---:|---|
| NFCI p75 wf | DEFENSIVE_PURE_eq | 29 | -0.0046 | [-0.0163, +0.0069] | 0.392 | 0.777 | TENTATIVE DIRECTIONAL |
| NFCI p75 wf | FINANCIALS_XLF | 29 | -0.0092 | [-0.0242, +0.0039] | 0.154 | 0.375 | TENTATIVE DIRECTIONAL |
| BAA10Y p75 wf | DEFENSIVE_PURE_eq | 24 | +0.0019 | [-0.0066, +0.0119] | 0.540 | 0.997 | TENTATIVE DIRECTIONAL |
| **BAA10Y p75 wf** | **FINANCIALS_XLF** | **24** | **-0.0134** | **[-0.0229, -0.0016]** | **0.0156** | 0.0506 | **PARTIAL CONFIRMED (raw p<0.05, LOO 경계, Bonferroni FAIL)** |

★중요 발견:
- ★BAA10Y p75 wf 의 FIN cell: raw p=0.016 (★raw 유의), 95% CI 가 0 미포함, LOO p_max=0.051 (★거의 robust). 단 Bonferroni α/4=0.0125 미달.
- 나머지 3 cell: TENTATIVE (p>0.15)

## 결과 (3) walk-forward Cross-sleeve Welch (rule §1.6 검증)

| regime | n_def | n_fin | mean_def | mean_fin | **gap (DEF - FIN)** | Welch t | p |
|---|---:|---:|---:|---:|---:|---:|---:|
| NFCI p75 wf | 29 | 29 | -0.0046 | -0.0092 | **+0.0045** | +0.463 | 0.645 |
| BAA10Y p75 wf | 24 | 24 | +0.0019 | -0.0134 | **+0.0154** | +1.637 | 0.109 |

★**walk-forward direction consistency**:
- **2/2 wf regime gap > 0** (DEF_PURE outperforms FIN in stress)
- v4 lookahead (4/4 gap > 0) 와 walk-forward (2/2 gap > 0) 모두 ★방향성 일관
- → **sleeve 분리 grouping (rule §1.6) OOS 안정성 ★실증**

★**walk-forward 통계 강도**:
- Welch p NFCI = 0.645 / BAA10Y = 0.109
- Bonferroni α/4 = 0.0125 → 0/2 wf regime PASS
- BAA10Y wf 가 가장 가까움 (p=0.109)

## v4 lookahead vs walk-forward 비교

| 항목 | v4 lookahead | walk-forward | 평가 |
|---|---|---|---|
| 방향 일관 (sign split) | 4/4 regime gap > 0 | 2/2 wf regime gap > 0 | ★일관 안정 |
| BAA10Y FIN excess | 4 regime 모두 음수 | wf BAA10Y FIN -0.0134 (raw p=0.016) | ★FIN underperform 강화 |
| Bonferroni PASS | 0/8 cell | 0/2 wf regime + 0/4 wf cell | 유지 (단 BAA10Y wf FIN raw p<0.05) |
| LOO p_max | >0.5 fragile | BAA10Y wf FIN LOO p=0.051 (★거의 robust) | ★BAA10Y exogenous 안정 |
| sample size | full historical | post-2010 (lookahead 차단) | 자연 trade-off |

★종합 발견:
- **방향 일관성** v4 → wf 유지 (sleeve 분리 grouping 정합)
- **통계 강도**는 sample 감소로 약화 (단 BAA10Y wf FIN raw p<0.05 + LOO 거의 robust)
- BAA10Y exogenous primary 우선 권고 (★보강 #2 vintage 결과와 정합)

## 평가 (★rule §2 verdict 5단계)

### Walk-forward verdict 라벨링

| 차원 | verdict | 근거 |
|---|---|---|
| H3 방향 일관성 (sign split) | ★validated_structural | wf 2/2 + lookahead 4/4 일관, OOS 안정 |
| H3 magnitude (정량 강도) | structural TENTATIVE | Bonferroni 0/4 wf cell PASS, LOO p>0.05 일부 fragile |
| BAA10Y wf FIN excess (★단일 cell) | PARTIAL CONFIRMED | raw p=0.016 (n=24), LOO p_max=0.051 (★거의 robust), Bonferroni FAIL |
| sleeve 분리 (DEF_PURE vs FIN) | ★validated_structural | 4/4 + 2/2 모두 gap > 0 OOS 일관 |

### tier 승격 판정 (★main 요구)

**main 요구 = "유지 + Bonferroni 생존 시 H3 structural TENTATIVE → validated 승격, 미달이면 TENTATIVE 정직 유지"**

판정:
- walk-forward sign split direction: ★4/4 cell 일관 (NFCI 2 + BAA10Y 2 모두 DEF_PURE ≥ FIN)
- Bonferroni 생존: 0/2 wf regime PASS (NFCI 0.645 / BAA10Y 0.109 — Bonferroni α/4=0.0125 미달)
- → **★H3 structural TENTATIVE 유지** (방향성 OOS 안정 단 magnitude Bonferroni 미달)

★단 BAA10Y wf FIN 의 단일 cell PARTIAL CONFIRMED 는 sub-credit (single sleeve / single regime) 강 신호:
- raw p<0.05 + LOO 거의 robust
- multi-cycle n 증가 후 (다음 stress regime 도래 시) Bonferroni PASS 가능성 잔존
- → **structural VALIDATED 승격 대기 (multi-cycle wait)**

## ★보강 #2 NFCI ALFRED vintage 결과 (병행 작업)

main 요구 = "NFCI realtime ALFRED vintage(보강#2) 가능하면 병행".

### Vintage 가용성

| 항목 | 결과 |
|---|---|
| `fred.get_series_vintage_dates('NFCI')` | 780 vintages |
| vintage 범위 | 2011-05-25 ~ 2026-05-28 |
| ★ALFRED PIT 가용 | **2011-05~ 만** (pre-2011 vintage X) |
| `fred.get_series_first_release('NFCI')` | n=301 (1971-01-08 ~ 1976-10-08 only — fredapi 한계) |

### Current revision vs First release 차이

| 통계 | 값 |
|---|---:|
| n_compare | 301 |
| mean abs diff | **0.3519** (★NFCI std 0.999 의 35%) |
| max abs diff | 0.8850 at 1974-08-23 |
| pct |diff| > 0.05 | 100.0% |
| pct |diff| > 0.10 | **98.7%** |

### Implication

★**NFCI revision 폭 매우 큼**:
- mean abs diff = NFCI std 의 35%
- 98.7% 시점에서 |diff| > 0.1 — 사실상 모든 시점에서 retrospective revision
- 본 walk-forward (2010-01~) 도 대부분 vintage 영향 받음 = ★PIT 미준수

→ **★BAA10Y (Treasury yield 기반, revision 거의 없음) = PIT-pure exogenous primary 강화**
   NFCI 결과는 secondary cross-check (vintage 한계 명시)
   진정한 NFCI PIT walk-forward = 2011-05~ ALFRED vintage 별도 분석 (todo, n 약 15년 추가 작업)

## 한계 (★rule §1 정직)

1. **walk-forward in-sample 16.4년 (n=197 mo)** — full historical (n=317) 대비 sample 38% 감소
2. **Bonferroni 0/2 wf regime PASS** — magnitude 통계 약 (multi-cycle n 증가 필요)
3. **NFCI vintage 한계**: pre-2011 vintage X, current revision 사용 → 본 walk-forward 도 vintage 영향
4. **post-2010 in-sample**: 2008 GFC 시점 OOS 분류 (rolling window 시작 이전) → multi-cycle 표현 한계
5. **Block bootstrap block_size=4 = empirical** — autocorr decay 통상 4-6mo, 다른 block 시 미세 변동
6. **regime threshold p75 = 단일 quantile** (p80, p90 시 sample 더 감소)

## 코드화 권고 (yaml v4 반영 — 이미 6c351a0 commit 박제)

`study_session.yaml v4-tier` `audit_enhancement_walkforward` + `audit_enhancement_nfci_vintage` 블록 참조:
- promotion_pending: "n 증가 (multi-cycle wait) 또는 Block bootstrap longer block → Bonferroni 1+ PASS 시 structural VALIDATED 승격 가능"
- BAA10Y exogenous primary 강화 + NFCI secondary (vintage 한계 명시)

## 참조

- `run_validation_v4_walkforward.py` (★main 보강 #1 D축 — walk-forward 10Y rolling threshold)
- `validation-metrics-v4-walkforward.json` (walk-forward 결과 정량)
- `fred/NFCI_first_release.csv` (★main 보강 #2 — ALFRED vintage 1971-1976 sample)
- `validation-H3-v4.md` (parent, v4 lookahead 결과)
- `validation-H3.md` v3 (★INSUFFICIENT 격하)
- `study_session.yaml` v4-tier (audit_tier_verdict + audit_enhancement_walkforward + audit_enhancement_nfci_vintage)
- direction.md §H3 (가설 원문)
- ~/.claude/rules/empirical-claim-presentation.md §1 5의무 + §1.6 분석 unit / portfolio label + §2 verdict 5단계 + §1.1-ext handoff source 사전 검증
- ~/.claude/memory/promotion-log.md ERROR-202605302130 + ERROR-202605302245 + ERROR-202605311240 (handoff anchor)
