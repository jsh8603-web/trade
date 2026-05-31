---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/2-3, hypothesis/h5-redefined]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
hypothesis: "H5 (재정의) — China idiosyncratic dominance: MCHI multi-R² << EMXC multi-R² (factor=DXY+VIX+SPY 고정)"
raw_source: raw/walkforward.py + raw/walkforward-output.txt + raw/china-cross-check.txt
factor_set_frozen: [DXY, VIX, SPY]
walkforward_setup: "Train 24m rolling, multi-factor OLS R², factor set 절대 고정 (DXY+VIX+SPY 만)"
note: "★H5 원 정의 (MCHI β < EMXC β) 는 R3 paper cross-check 에서 기각 후 재정의. R²-기반 spec 에 대해 OOS 일관성 검증."
---

# H5 (재정의) walk-forward 검증 — China idio dominance

## §1. 재정의 + 반증조건

- **재정의**: factor set (DXY+VIX+SPY) 으로 회귀 시 MCHI 의 multi-R² 가 EMXC 보다 현저히 낮다 (China = idiosyncratic dominant, EMXC = systematic). 차이 > 0.15.
- **반증조건**: 24m rolling window 중 EMXC R² > MCHI R² 가 **<70%** OR mean diff < 0.15 in 6m+ rolling.

## §2. Walk-forward setup

- Train: 매 월 t 의 직전 504 daily obs (≈24m).
- 매 월 refit, 절대 factor set 고정 (DXY+VIX+SPY 변경 금지 — 잠재 인자 통제).
- OOS = 34 months (2023-06 ~ 2026-03).

## §3. 결과 — ★ 강력 확인 (100% windows)

### 3.1 6m 간격 sample (raw/walkforward-output.txt)
| month_t | MCHI R² | EMXC R² | diff (EMXC−MCHI) | flag |
|---|---:|---:|---:|---|
| 2023-06 | 0.209 | 0.688 | **+0.478** | ✓ |
| 2023-12 | 0.244 | 0.713 | +0.468 | ✓ |
| 2024-06 | 0.230 | 0.666 | +0.436 | ✓ |
| 2024-12 | 0.163 | 0.635 | +0.472 | ✓ |
| 2025-06 | 0.189 | 0.698 | +0.509 | ✓ |
| 2025-12 | 0.173 | 0.656 | +0.484 | ✓ |

### 3.2 전체 34 windows summary
| metric | value |
|---|---:|
| **MCHI R² mean** | **0.205** (min 0.152, max 0.250) |
| **EMXC R² mean** | **0.671** (min 0.600, max 0.715) |
| **mean diff (EMXC − MCHI)** | **+0.466** |
| consistency (EMXC > MCHI) | **100.0% of windows** |
| strong (diff > 0.15) | **100.0% of windows** |

## §4. 판정

**★ 강력 확인 (재정의 후)**. OOS walk-forward 로도 EMXC R² > MCHI R² 가 100% windows 에서 성립.
factor set 고정 후에도 robust. 즉:
- **China 는 글로벌 factor 로 설명되는 비중이 EM avg 대비 3배 작음** (0.205 vs 0.671).
- 잔여 0.795 의 비중 = idiosyncratic (policy/geopolitical/CNY/사이클 desync).
- 이게 R3 의 "China decoupling" 의 진짜 ground truth.

★ **R3 paper 인용 정량 (IMF "β 1.2→0.2" / AQR "≈0") 는 환각 가능성. 단 방향성·R²-기반 idio dominance 는 강확인** (cross-check 의무 이행 결과).

## §5. yaml 갱신 표지

- block3 새 edge: `mchi_r2_vs_emxc_r2_gap (factor=DXY+VIX+SPY)`, prior_sign:pos, prior_strength:0.85 (실측 100% windows 지지).
- block4 새 weight rule: em_china archetype 의 macro_beta 가중을 EMXC 와 별도 책정. modulate_by:[archetype].
- block5 confidence_hook H5 (재정의): EARLY_ADOPT (5y + OOS walk-forward 양쪽 강확인).
- block5 confidence_hook H5a (em_china sub-archetype): NEEDS_DEPLOY → 코드화 가치 명확.
- block6 신규 collector: MCHI/EMXC 가격 panel (이미 Yahoo fetch). + FXI/KWEB.

## §6. 향후 개선

- China sub-segmentation (state-owned vs private, A-share vs H-share) — Hang Seng A-H Premium.
- HY OAS 직접 추가 factor set → MCHI R² 변화 측정 (factor 보강 후에도 idio dominance 지속하는가?).
- 글로벌 동시 위기 simulate (H5b decoupling 가역성) → MCHI R² 일시 ↑ 시 reformulation.
