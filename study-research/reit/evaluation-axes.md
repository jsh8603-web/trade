---
tags: [type/evaluation-axes, study_id/reit, phase/v2-mirror-phase1, ssot/audit]
date: 2026-05-31
study_id: reit
asset_scope: [reit]
mirrors: eq_kr/evaluation-axes.md v2 (AUDIT-GUIDE 12축 application baseline)
note: Phase 6 별 평가 subagent SSOT. ★ supervisor 직접 평가 금지 (main pass-bias 회피 원리 미러).
status: phase1_ready_for_phase6_dispatch
---

# REIT v2-mirror — evaluation-axes (Phase 1, Phase 6 평가 SSOT)

> Phase 6 평가 subagent (opus 1m) 에게 dispatch 시 본 파일 + AUDIT-GUIDE.md 동시 정독 의무.
> 본 파일 = AUDIT-GUIDE 12축 + REIT 자산군 application layer + Hard-fail 코어 4 + Tier 라벨 + 평가 prompt 양식.

## §0 Provenance + Recomputation 의무 (AUDIT-GUIDE §0 mirror)

- yaml 의 모든 수치 = **사실 아닌 "주장 (claim)"** 으로 취급
- raw/ 원본 데이터 + 분석 .py 가 yaml 숫자 만드는 경로 추적 가능해야 함 (raw/evidence-map.md hard pass)
- ⛔ Phase 5 subagent 가 제공한 정량 수치 = supervisor 가 직접 검증 (재실행) 의무. 자문 그대로 박제 금지.

## §1 AUDIT-GUIDE 12축 (full, REIT application 명시)

### Hard-fail 코어 4 (B / C / D / I) — 위반 시 yaml block 자동 폐기

#### B축 — 실데이터 검증
- **요건**: ⛔ 합성·시뮬 데이터 금지. 모든 정량 수치 (β, Rank-IC, ρ, p-value, n, 기간) = 실측 수집기 (yfinance, FRED, Nareit, EIA, Census, CMS) 출처 표기.
- **REIT 적용**: M3 + validation H1~H5 + (Phase 5 신규) sub-cluster N subagent 산출의 모든 정량 = `raw/scripts/*.py` 또는 `raw/scripts/*.log` trace 가능.
- **검증 절차**: `raw/evidence-map.md` 의 매 row (수치 → script → data source → period → n) 누락 여부 점검. 누락 = B 축 FAIL.

#### C축 — yaml 도출 추적성
- **요건**: yaml 의 모든 수치/규칙 → raw/validation 또는 자문 cross-verify 직접 trace 가능.
- **REIT 적용**: study_session.yaml 의 lens (block 1) / corr_prior (block 3) / weight_rules (block 4) / confidence_hooks (block 5) 모든 수치 → `raw/evidence-map.md` row 1:1 매핑.
- **검증 절차**: yaml row N 개 vs evidence-map row N 개 일치. 누락 row = C 축 FAIL.

#### D축 — PIT (Point-in-Time) / OOS (Out-of-Sample)
- **요건**: 모든 회귀·signal 계산이 미래 정보 leakage X. lookahead bias 차단.
- **REIT 적용**:
  - DGS10/DFII10/T10YIE = daily ffill, signal 계산 시 next-day open 진입 (당일 close 가격 X).
  - CMBS Delinquency Rate / Census Construction = 발표일 기준 (mid-month lag), 진입 = lag 명시.
  - OOS = train (2018-2022) / test (2023-2024) split 또는 walk-forward.
  - CMS final-rule = event-day CAR (발표일 = anchor, 이전 close = baseline).
- **검증 절차**: 각 signal/회귀 코드의 `shift(1)` / `ffill` / lag 처리 점검. 누락 = D 축 FAIL.

#### I축 — 생존편향 (Survivorship Bias)
- **요건**: universe 가 현재 생존 ticker 한정이면 생존편향 caveat 명시. 가능 시 historical universe (상폐 포함) 사용.
- **REIT 적용**:
  - 9 sub-sector 대표 ticker (PLD/AVB/BXP/WELL/EQIX/PSA/SPG/HST/AMT) = 2018+ 모두 listed + 2026 생존. **본 기간 상폐 REIT 미포함** (특히 office sector stress 회사).
  - mREIT C8 (NLY/AGNC/MFA) 도 동일 caveat.
  - 가능 시 Compustat / WRDS REIT historical universe 사용 (Phase 5 collector_plan 의무).
- **검증 절차**: study_session.yaml block 8 self_audit § I축 명시 + universe row 의 "현재 생존 한정" caveat 박제. 누락 = I 축 FAIL.

### 보조 8축

#### A축 — 이론 실재성
- **REIT 적용**: 학설 ref (NAV 할인율 / cap-rate spread / lease escalator / cash-flow timing mismatch / He-Xiong 2012 rollover risk / Plazzi-Torous-Valkanov 2010 mean-revert / Coval-Stafford 2007 flow predictability) 가 yaml lens·rule 의 근거로 명시. ⛔ 환각 ref (Beracha-Krautz 2022 / Ling-Naranjo 2015 / Green Street citation) 박제 금지.

#### E축 — 자문 비판 + 환각 cross-verify
- **REIT 적용**: 자문 R1+R2+R3 응답이 yaml 에 직접 박제되지 않고, supervisor §5 cross-verify 후 채택만 박제. ⛔ Beracha-Krautz / Ling-Naranjo 2015 / Green Street primary citation = E 축 FAIL.

#### F축 — 반증가능 + 기각 기록
- **REIT 적용**: H1 (long-WALT positive 학설) REJECT sign mismatch / H3 (long-WAM Debt positive 학설) REJECT sign mismatch / H5 (regime-stable rank) CONFIRMED falsification = yaml block 8 F축에 명시 박제. H6-H10 신규 가설도 정량 반증조건 명시 (CI 하한, hit-rate binomial, CAR significance 등).

#### G축 — 검정력 한계
- **REIT 적용**: sub-cluster 9 × monthly anchor → cell n 작음 (SE 0.13 with n=60). per-cell 검정 폐기 → panel-level / pooled cross-section + Newey-West (★ R3 estimand 변경). 5게이트 임계 0.05 = panel/pooled 단위 적용. shrinkage (Ledoit-Wolf/Jorion) λ 분포 sweep.

#### H축 — 미해결 의문
- **REIT 적용**: R4 carry 3건 (Beracha-Feng-Hardin 2019 원문 / AMT VIL $3.22B 10-K / CCI-AMT churn schedule) + H3 confounding orthogonalize + C8 mREIT 전용 가설 신설 = yaml block 8 H축 박제. Phase 5 dispatch 시 collector_plan 의무.

#### J축 — 경제적 유의성
- **REIT 적용**: ES (Expected Excess return) > 3% annualized 가 panel/pooled 단위 적용 (★ R3 estimand 변경 정합). shrinkage 후 수축된 신호 기준 재계산.

#### K축 — 다중검정 보정
- **REIT 적용**: H1-H10 = 10 가설 + 8 sub-cluster × 6 driver = 48 회귀 = 다중검정. Benjamini-Hochberg FDR (q=0.10) 또는 Bonferroni (α/N) 의무. 본 보정 후 잔존 유의 가설만 yaml 박제.

#### L축 — 통합 상관 PSD (Positive Semi-Definite)
- **REIT 적용**:
  - cross-asset cov (REIT factor B Λ Bᵀ_cross) = M1 named factor (rate/dollar/oil) + 신규 (real rate/breakeven/cap-rate/HY OAS) — within-asset class 1회 계상.
  - within-sleeve cov (9 sub-sector pairwise ρ=0.547) = equity broad factor (Fama-French + Q-factor REIT) + sub-sector unique — 별도 처리 (R2 2-stage Ling-Naranjo).
  - Σ_full = B Λ Bᵀ_cross + W_within + Δ_idio PSD 검증 (eigvalsh > 0).
  - ⛔ belief→_macro reflexive loop 차단 (U3).

## §2 Tier 라벨 (REIT 자산군 한정 적용)

| Tier | 정의 | REIT 적용 (현 산출) |
|---|---|---|
| **validated alpha** | 정량 Rank-IC > threshold + OOS + multi-regime + economic significance + multi-test corrected | 현 v2 = 없음 (3R 자문 만으로 도달 불가) |
| **structural prior (저신뢰)** | 검증 시도 → REJECT 또는 inconclusive 학설 / contemporaneous 만 / multi-test 후 잔존 의문 | v2 yaml 현재 = **structural prior** Tier. validation H1~H5 = 5건 시도 (H1 REJECT, H2 PARTIAL, H3 REJECT, H4 CONFIRMED, H5 CONFIRMED falsification) |
| **opt-in off** | yaml 박제하되 default off, 추가 검증 후 on | INV_R15_WEIGHTS default-off 정합 |

★ **analyst-level lens 다운그레이드 금지** — yaml lens 가 시스템 (G1~G6 production wiring) 못 받으면 시스템 파이프라인 업그레이드 (lens 다운그레이드 X).

## §3 Phase 6 평가 subagent dispatch prompt (양식)

### 입력
- `study_session.yaml` (전체 8 block)
- `direction.md` (§1-§8 v2-mirror Phase 3.5 supplement)
- `raw/m3-macro-linkage.md` + `raw/validation-{H1..H5}.md` + `raw/theory-notes.md`
- `raw/consult-round-{1,2,3}.md` (Phase 3 자문 R1+R2+R3 supervisor cross-verify)
- `raw/evidence-map.md` (C 축 hard pass trace)
- 신규 Phase 5 산출: `industries/{cluster}/summary.yaml` + `industries/{cluster}/8axis-audit.md` × 8 cluster
- AUDIT-GUIDE.md (12축 SSOT) + evaluation-axes.md (본 파일)

### 평가 절차 (subagent 의무)

1. **§0 Provenance + Recomputation**: yaml 의 모든 수치 → raw .py 재실행 가능성 검증. raw/evidence-map.md trace 점검.
2. **Hard-fail 코어 4 (B/C/D/I)** 우선 평가. 하나라도 FAIL = yaml block 자동 폐기.
3. **보조 8축 (A/E/F/G/H/J/K/L)** PASS/PARTIAL/FAIL 평가.
4. **Tier 판정**: validated alpha / structural prior / opt-in off.
5. **시스템 정합 (§4)**: 다운그레이드 금지, 업그레이드 계획 (어떤 시스템 파이프라인 추가가 필요한가).
6. **PARTIAL/FAIL block** → 해당 sub-cluster subagent 재dispatch 권고 (최대 2회).

### 출력 양식

```markdown
# REIT Phase 6 평가 결과 (opus 1m subagent, {date})

## 1. Hard-fail 코어 4
| 축 | 판정 | 사유 |
|---|---|---|
| B 실데이터 | PASS/FAIL | ... |
| C 추적성 | PASS/FAIL | ... |
| D PIT/OOS | PASS/FAIL | ... |
| I 생존편향 | PASS/FAIL | ... |

## 2. 보조 8축
(동일 표)

## 3. Tier 판정
- 전체 yaml: structural prior / validated alpha / opt-in off
- block 별 차등 (필요 시)

## 4. 시스템 정합 (§4)
- 다운그레이드 여부:
- 업그레이드 계획:

## 5. PARTIAL/FAIL block 재dispatch 권고
- sub-cluster N: 재실행 이유 + 보강 지시
```

## §4 ★ supervisor 직접 평가 금지 (사용자 박제)

⛔ **본 작업방 supervisor (= 본 세션 btn-GCP) 는 Phase 6 평가 직접 수행 금지**. main pass-bias 회피 원리 (AUDIT-GUIDE §0) 미러:
- supervisor 가 평가 직접 시 = supervisor pass-bias 발생
- 별 opus 1m subagent (Agent tool, subagent_type=general-purpose, model: opus) dispatch 의무
- subagent prompt = §3 양식 그대로 + 입력 파일 list + 평가 절차 6 step
- subagent 결과 = 본 세션 supervisor 가 받아 main 보고 (단, supervisor 자체 평가 추가 금지)

## §5 산출 cross-ref

- AUDIT-GUIDE.md (12축 SSOT)
- eq_kr/evaluation-axes.md (v2 미러 baseline)
- methodology-brief.md (Phase 2, REIT specific 4-section)
- direction.md §8 (Phase 3.5 supplement)
- raw/evidence-map.md (C 축 hard pass trace)
- 신규 Phase 4 plan.md (Phase 5-7 작업 계약, dispatch table)
