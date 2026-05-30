---
tags: [type/validation, study_id/reit, hypothesis/H3, phase/2-3]
date: 2026-05-30
hypothesis_id: H3
verdict: REJECTED (sign mismatch, sector-WAM proxy)
note: Ticker-level WAM unavailable without EDGAR text NLP. Sector-average proxy used (range only 2.5y).
---

# H3 (Debt Maturity Profile Stratification) — 실데이터 검증

## §1. 가설

**명제**: debt weighted-average maturity > 5y REIT 가 rate-shock window 시 < 3y REIT 보다 *덜*
떨어진다. (locked-in low-rate debt 가 refinancing risk 완화)
- **confirm**: cross-section debt_WAM_rank vs rate-shock 60d return Rank-IC > +0.05 (long-WAM
  outperform).
- **reject**: 정반대 부호 (long-WAM underperform, Rank-IC < -0.05).

## §2. 데이터 (sector-average proxy, ticker-level NLP TODO)

- **WAM proxy** (sector-average, practitioner standard):
  - Healthcare 7y / Apartment 7y / Retail 6.5y / Specialty 6y / Office 6y / Industrial 6y /
    Storage 6y / Datacenter 5.5y / Hotel 4.5y
- WAM range: **4.5y ~ 7y (2.5y spread)** — H1 의 WALT range (1y~12y, 11y spread) 보다 훨씬 좁음 →
  검정력 약함 명시.
- Rate-shock entries: 23 (H1 과 동일)
- Forward window: 60 trading days

## §3. 결과 (★ verbatim from script output)

- Mean Rank-IC: **-0.117** (z = -2.09, marginal sig)
- Std: 0.268
- Median: -0.157
- Fraction negative: **78.3%** (18/23)

→ **H3 REJECTED with sign mismatch**: long-WAM REIT (Healthcare 7y, Apartment 7y) 가 rate-shock
시 *underperform*. 가설 가정 (long-WAM outperform via refinancing protection) 의 정반대.

## §4. ★ H1 과 H3 부호 mismatch — 흥미로운 발견

| 가설 | duration 변수 | 범위 | mean Rank-IC | 부호 |
|---|---|---|---:|---|
| H1 | WALT (lease duration) | 1y~12y | **+0.240** | long-WALT outperform |
| H3 | WAM (debt maturity) | 4.5y~7y | **-0.117** | long-WAM underperform |

**같은 "long-duration" 변수인데 부호가 반대**. mechanism 해석:

1. **WALT (lease) effect = defensive rotation**: long-WALT sector (Healthcare/Datacenter/Specialty)
   = secular growth + stable contractual cash flow → rate-shock 시 defensive bid.
2. **WAM (debt) effect = refinancing protection**: long-WAM = locked-in low rate → rate hike 시
   refinancing risk 적음 → outperform 이론적 예상.
3. **실측 H3 부호가 -**: long-WAM (Healthcare 7y + Apartment 7y) 가 underperform.
   - Healthcare 는 H1 에서 long-WALT 라 outperform 했지만, H3 의 long-WAM 으로는 underperform.
   - 같은 종목이 두 분류에서 다른 신호 — proxy 의 collinearity 문제.
4. **이게 시사하는 것**: sector-aggregate proxy 로는 cash-flow duration (WALT) 효과가 capital
   structure duration (WAM) 효과보다 dominant. 정확한 H3 검증은 같은 sector 안에서 ticker-level
   WAM 분산이 필요 (EDGAR text NLP TODO).

## §5. 8축 self-audit

| 축 | 평가 | 메모 |
|---|---|---|
| A 이론실재성 | ✓ | refinancing risk mechanism 학설 base |
| B 실데이터검증 | △ | 실측 n=23 entries, 단 sector-WAM proxy range 좁음 (2.5y) — 검정력 제한 |
| C yaml 도출추적성 | (다음) | block5 H3 reject 기록 + block4 leverage 규칙 재설계 |
| D PIT·OOS | ✓ | strict forward, lookahead 없음 |
| E 자문비판+환각cross-verify | ✓ | sector-WAM proxy 의 한계 명시, primary는 ticker-level NLP TODO |
| F 반증가능+기각기록 | ★★ | reject 명확 (mean -0.117, 78.3% negative) — 기각 기록 본 노트 |
| G 검정력한계 | ⚠⚠ | (a) WAM range 2.5y 좁음 (b) sector aggregate = within-sector 분산 무시 (c) WALT 와 WAM collinear |
| H 미해결의문 | ★ | (a) ticker-level WAM via EDGAR text NLP (b) within-sector cross-section 검증 (c) WALT vs WAM partial-corr 로 effect 분리 (block3 conditioning_set 보강) |

## §6. v2 yaml 반영

1. **block5 H3 hypothesis_id**: confirm_signal 부호 변경 — long-WAM outperform 가설 reject.
   reject_signal 이 trigger 된 기록 명시.
2. **block3 relationships**: WAM ↔ rate-shock return edge 의 prior_sign 을 v1 의 'pos' 에서
   'neg' 로 변경 (실측 부호). prior_strength 약함 (검정력 한계) 0.30 → 0.20.
3. **block2 indicators**: `debt_maturity_wam_years` 의 in_our_system = false, source_or_collector
   = "EDGAR 10-K debt schedule 텍스트 NLP (TODO)" 명시. 1차 차선 = sector-average proxy.
4. **block4 weight_rules**: H3 의 "rate-shock + long-WAM → 가중↑" 규칙 폐기. 대신 H1 의
   defensive rotation 가설 (long-WALT outperform) 잠정 등록.

## §7. 잔존 caveat / 다음 단계

- ticker-level debt WAM = EDGAR 10-K debt schedule NLP (별도 후속).
- WALT-WAM partial-corr = block3 conditioning_set 으로 분리 검증 (v2 yaml 작성 시 명시).
- within-sector cross-section = H1 의 sector membership 효과 분리 후 ticker-level WAM 효과 측정.

## §8. 산출 파일

- script: `raw/scripts/h3_h5_combined.py` (H3 + H5 합쳐)
- log: `raw/scripts/h3_h5.log`
- 본 분석: `raw/validation-H3.md`
