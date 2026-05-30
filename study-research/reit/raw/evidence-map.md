---
tags: [type/evidence-map, study_id/reit, phase/2-3]
date: 2026-05-30
note: AUDIT-GUIDE §0 Provenance + C축 (yaml 도출 추적성) hard-pass 보강. v2 yaml 수치 → raw/validation/script 직접 trace.
audit_target: study_session.yaml (v2)
---

# Evidence Map — v2 yaml 수치 → raw artifact 추적표

> AUDIT-GUIDE.md §0: "yaml 의 숫자를 사실이 아닌 주장(claim)으로 취급. raw/ 원본 데이터 +
> 분석 .py 가 yaml 숫자 만드는 경로 추적 가능해야 함." 본 표 = 그 추적 명문화.

## 1. 데이터 source 무결성 (I축 — 생존편향)

| Data | Period | n | Source | 생존편향 caveat |
|---|---|---:|---|---|
| FRED DGS10 | 1962-01-02 ~ 2026-05-28 | 16086 daily | `fred_csv('DGS10')` in h1/h3 scripts | n/a (rate index, no survivor) |
| FRED GDPC1 (real GDP) | 1947-Q1 ~ 2025-Q4 | 313 quarterly | `fred_csv('GDPC1')` | n/a |
| FRED CPIAUCSL (CPI-U) | 1947-01 ~ 2026-04 | 939 monthly | `fred_csv('CPIAUCSL')` | n/a |
| 9 REIT representative ticker prices | 2018-01-02 ~ 2026-05-28 | 2112 daily | yfinance auto_adjust=True | **★ 생존편향**: 9 종목 모두 2018+ listed + 2026 현재 생존. 2018-2026 상폐 REIT 미포함. v2 에서 명시 |
| VNQ (broad REIT ETF) | 2005-01-03 ~ 2026-05-28 | 5384 daily | yfinance | ETF survivorship = n/a (broad index reconstitution) |
| Nareit cap rate spread (sparse) | Q3'22 / Q4'23 / Q2'24 / Q3'24 | 4 quarter | Nareit market commentary article × 2 (verbatim) | primary verified; Q4'24 120bp 미확인 → baseline 제외 |
| Nareit Q2 2023 sub-sector spread | Q2 2023 single snap | 1 | Nareit "Office and Apartment Sectors" article | primary verified |
| 2024 industrial -17.7% | 2024 calendar year | 1 | Nareit webinar recap | primary verified |

## 2. Validation script → yaml 수치 추적 (C축 — hard pass 의 핵심)

### 2-A. H4 (window flip) — block4 modulate_by 'window_length' 의 근거

| yaml 수치 / 정성 결정 | Validation evidence (file:line) | 실측 |
|---|---|---|
| block1 lens.regime_reading: "regime → sub-sector 단순매핑 무효" | `raw/validation-H4.md` §3-1 | Mean Kendall τ (short vs long pairs) = **+0.077** ← n=77 anchor |
| block4 modulate_by enum 에 'window_length' 포함 | `raw/scripts/h4_window_flip.log` | swap rate (1+ tier) = **88.0%** mean across short-long pairs |
| block5 H4 confirm_signal: swap > 30% AND τ < 0.7 | direction.md / round-3.md | 실측 swap 88.0% > 30%, τ 0.077 < 0.7 → CONFIRM |

### 2-B. H1 (long-WALT rate-shock cross-section) — block4 rate-shock 가중 규칙의 근거

| yaml 수치 / 정성 결정 | Validation evidence | 실측 |
|---|---|---|
| block1 lens.regime_reading: "rate-shock 후 long-WALT *outperform*" (v1 정반대) | `raw/validation-H1.md` §3-2 | Mean Rank-IC = **+0.240** (z=+3.18), n=23 rate-shock entries, 17.4% negative |
| block3 WALT ↔ rate-shock_return prior_sign = neg (v1 = pos) | validation-H1.md §6 | prior_strength = 0.50 → 0.30 강등 (single-regime sample) |
| block4 rate-shock + long-WALT → 가중 정책: 잠정 *long-WALT* 우선 (defensive rotation) | validation-H1.md §4 | mechanism 가설 (defensive rotation, secular growth confounding) 명시 |
| block5 H1 reject_signal: 실측 sign mismatch trigger 됨 | validation-H1.md §6 | v1 가설 "long-WALT underperform" reject 기록 |

### 2-C. H2 (cap rate spread mean-revert) — block5 H2 baseline 의 근거

| yaml 수치 / 정성 결정 | Validation evidence | 실측 |
|---|---|---|
| block5 H2 baseline = Q3 2024 60bp (est) / Q2 2024 130bp; Q4 2024 120bp **제외** (E축) | `raw/validation-H2.md` §2-1 + archive raw cap-spread-timeseries | Nareit primary 4 quarter; Q4'24 120bp = Q4'23 123bp 혼동 의심 |
| block5 H2 confirm_signal: VNQ proxy z<-1.5 → 12m fwd Rank-IC > +0.15 (proxy 부호) | `raw/validation-H2.md` §3-1, §3-2 | deep-discount 275 obs mean fwd 12m = **+32.5%**, Spearman ρ=-0.361 p<<0.001 |
| block5 H2 reject_signal (b) "deep discount 6Q+ 지속 미회복" 실사례 | validation-H2.md §3-3 | 2008-01-04 z=-1.71 fwd -35.4% / 2008-06-27 z=-1.55 fwd -43.0% |
| block2 implied_cap_rate_spread 의 source = "Nareit T-tracker + NCREIF ODCE quarterly (primary, sparse)" | validation-H2.md §6 | TODO: Excel direct download for full series |

### 2-D. H3 (debt maturity stratify) — block4 leverage 규칙 폐기 근거

| yaml 수치 / 정성 결정 | Validation evidence | 실측 |
|---|---|---|
| block5 H3 reject_signal trigger 명시 (v1 가설 정반대) | `raw/validation-H3.md` §3 | Mean Rank-IC = **-0.117** (z=-2.09), 78.3% negative, n=23 |
| block3 WAM ↔ rate-shock_return prior_sign = neg (v1 = pos), strength 0.20 (검정력 한계) | validation-H3.md §6 | sector-WAM proxy range 4.5y~7y (2.5y 좁음) |
| block4 "rate-shock + long-WAM → 가중↑" 규칙 폐기 | validation-H3.md §4, §6 | H1 (long-WALT outperform) 과 H3 (long-WAM underperform) 부호 mismatch — proxy collinearity 명시 |
| block6 EDGAR 10-K debt schedule NLP TODO | validation-H3.md §7 | ticker-level WAM 직접 확보 path |

### 2-E. H5 (sub-sector × regime 단정 반증) — block1 regime_reading 단정 제거 근거

| yaml 수치 / 정성 결정 | Validation evidence | 실측 |
|---|---|---|
| block1 lens.regime_reading: v1 의 "Reflation → industrial 강세" 매핑 **모두 제거** | `raw/validation-H5.md` §3-2 | Reflation regime 12 quarter 의 Industrial avg rank = **4.83 / 9** (mid, 단정 반증) |
| block3 regime ↔ sub-sector edge prior_sign = unsigned, strength 0.30 | validation-H5.md §6 | Mean inter-regime ρ = +0.087 (essentially random) |
| block4 modulate_by 의 regime 단독 규칙 폐기, joint modulate 만 | validation-H5.md §6 | regime 6종 × 9 sub-sector 의 ranking 분산 입증 |
| block1 estimation_note: Recession-Stagflation cluster (ρ=0.768) 명시 | validation-H5.md §3-3 | 침체 계열 일관성 partial |

## 3. PIT / lookahead (D축 — hard pass 의 핵심)

| Script | PIT 보장 mechanism | lookahead 검증 |
|---|---|---|
| `h4_window_flip.py` | `window_ret(anchor_idx, w)` = anchor_idx − w lookback only | strict lookback (앵커 시점 이전만 사용) |
| `h1_long_walt_cross_section.py` | `shock_entry` = DGS10 4w Δ on rolling lookback (no future), forward = anchor+FWD strict | ✓ |
| `h2_mean_revert_proxy.py` | z = rolling 24m lookback / fwd_ret = anchor → +252d strict forward | ✓ |
| `h3_h5_combined.py` | shock_entry + Q-end regime label (GDP/CPI YoY) lookback only | GDP/CPI = FRED `first-release` 가 표준이나 실제로 latest-revised 가능 (cavat) |

★ caveat (D축 partial): FRED `fredgraph.csv` 는 **latest revised** 시계열 — true first-release
vintage (ALFRED) 가 아님. macro 자료 (GDP YoY, CPI YoY) 의 D축은 partial. 본 study 는 sector
return 의 cross-section 이라 직접 lookahead 영향 작지만, regime label 의 vintage 정확도는 한계.
주의: 진정한 PIT 검증은 ALFRED vintage 사용 후속 필요. v2 yaml 명시.

## 4. 합성·시뮬 데이터 부재 (§0 합성지문 검사)

- ★ 모든 데이터 = Yahoo Finance (실가격) + FRED (실거시) — 합성 seed 없음.
- 2020-03 COVID shock: VNQ 2020-03-16 z=-2.28 fwd 12m +46.4% — 실역사 이벤트 확인
- 2022 rate shock: H1 23 entries 중 15개가 2022 — 실역사 이벤트 확인
- 결측 패턴: prices.dropna() 후 2112 trading days (~8.4y) — 주말/공휴일 정상 갭, 미국 시장 영업일 일관
- VNQ kurtosis: log return 의 fat-tail 확인 (실데이터 indicator)
- 8 distinct deep-discount episode 식별 (2008-01, 2008-06, 2018-02, 2018-12, 2020-03, 2022-09, 2023-03, 2023-09) — 실역사 매핑

→ 합성 지문 없음, §0 PASS.

## 5. 시도횟수 (K축 — 다중검정 보정)

본 study 에서 시도한 hypothesis = **5개** (H1, H2, H3, H4, H5).
- Bonferroni α/5 보정 시 5% → 1% (z > 2.81 필요)
- H1 z=+3.18 > 2.81 → 보정 후도 sig
- H2 proxy p<<0.001 (Spearman) → 보정 후 sig
- H3 z=-2.09 < 2.81 → **borderline / Bonferroni 보정 시 not sig at 1%**
- H4 swap 88% on n=77 (binomial 0.5) p<<1e-10 → 보정 후 sig
- H5 Recession-Stagflation ρ=0.768 p=0.016 → 보정 후 borderline

★ H3 의 결론 = Bonferroni 보정 시 marginal. v2 yaml block5 H3 confidence 약함 명시.

추가 시도 (스크립트에서):
- Window pair 7종 (H4) — H4 자체 internal multiplicity, 모두 strong → 영향 적음
- Forward window 60d (H1/H3) — 단일 선택, 30d/90d 추가 검증 시 추가 보정 필요 (TODO)
- Rate-shock threshold 50bp (H1/H3) — 단일 선택, 30bp/100bp sensitivity TODO

→ 5 hypothesis × 1 window × 1 threshold = 5 tries 단정. K축 부분 PASS, 단 sensitivity TODO 명시.

## 6. 통합 상관행렬 정합성 (L축 — system 단계)

REIT scope 는 us_stock sleeve sub-panel. rate β / credit β / dollar β 가 **macro, bond, commodity
방과 공통 factor**. 통합 단계에서 중복 계상 주의:

- ★ rate factor (DGS10) — REIT (block2 beta_rate) + macro (block2 yield_10y_2y / dgs10) + bond (block2 duration) 중복 위험
- ★ credit factor (HY OAS BAMLH0A0HYM2) — REIT (block2 beta_credit) + macro + bond 중복 위험

v2 block3 의 conditioning_set 에 위 factor 명시 → 통합 단계에서 main 의 `factor_implied_cross_cov`
에 공통 인자 1회 계상. block6 collector_plan 에 통합 시 PSD projection 게이트 의무 명시.

## 7. 검정력 한계 (G축 — tier 강등)

- H1/H3: rate-shock 23 entries 모두 2018-2025 single Fed hike cycle. effective N << 23 (autocorr).
  → tier = **"structural prior (저신뢰)"** 라벨. "validated alpha" 라벨 아님.
- H2 proxy: n=4629 일별 → 일별 autocorr 강함 (overlapping 12m fwd). 일별 t-stat 신뢰 보수화 필요.
- H4: n=77 monthly anchor 의 autocorr (인접 month 간 cumulative return overlap) — effective N << 77.
  → 단 swap rate 88% 의 effect size 가 매우 커서 effective N 보정 후도 sig.
- H5: n=33 quarter (Stagflation 2, Recession 3, Mid 3 극소수) → tier 강등. regime 별 추세 라벨만.

→ v2 yaml 의 모든 정량 결과는 "structural prior" tier 라벨. main 의 통합 단계에서 합법적 weight 로
승격은 별도 평가 필요.

## 8. 미해결 의문 (H축 — 솔직 기재)

1. ticker-level WALT / debt WAM via EDGAR 10-K text NLP (TODO).
2. 다른 rate cycle (1994/2004/2013 taper tantrum) 의 H1/H3 검증 (Yahoo 2018+ 한계).
3. Nareit T-tracker Excel direct download → cap rate spread full quarterly series.
4. NCREIF ODCE membership 또는 free aggregate (block6).
5. FRED ALFRED vintage 로 진정한 PIT regime labeling (D축 partial 개선).
6. WALT × WAM partial-corr (H1/H3 부호 mismatch 의 정확한 source 분리).
7. K축 sensitivity: 30bp/100bp rate-shock threshold + 30d/180d forward window.
8. survivorship: 2018-2026 상폐 REIT (e.g. 2020 ARL, MNR mergers) 의 영향.
9. archetype clustering (silhouette) 정량 — block5 H4-related hypothesis 의 mechanism.
10. global REIT (Japan JREIT, UK REIT) 의 cross-country 일반화.

## 9. 산출 파일 cross-ref

- direction.md (2-1)
- raw/round-1.md, round-2.md, round-3.md (2-1)
- raw/theory-notes.md (2-2)
- raw/validation-H1.md ~ H5.md (2-3)
- raw/scripts/h4_window_flip.py, h1_long_walt_cross_section.py, h2_mean_revert_proxy.py, h3_h5_combined.py
- raw/scripts/*.log (verbatim stdout, replay 검증 가능)
- raw/lens-rationale.md, data-availability-audit.md (v1 참고용)
- study_session.yaml.v1.bak (v1 백업, raw 참고용)
- ~/.claude/docs/archive/research-raw/reit-*.txt (6건 archive)
- ~/.claude/memory/research/reit-pricing-theory.md / reit-validation-methodology.md / reit-theory-notes-2-2.md
- study_session.yaml (v2, 본 evidence-map 의 추적 대상)
