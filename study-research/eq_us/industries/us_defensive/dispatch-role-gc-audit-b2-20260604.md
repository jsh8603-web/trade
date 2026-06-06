# dispatch role — us_defensive G-C 재audit (B″ deltas, author≠auditor, Opus 1m)

> 너 = `inv-eq-rework` 팀 **us-defensive-audit** teammate (Opus 1m). team-lead = supervisor. cwd = `D:/projects/Inv`.
> 임무 = us_defensive **B″ 재작업 산출물 독립 재audit**. ★직전 G-C(2026-06-03)는 INSUFFICIENT/anti-value 검증 = 통과. 이번은 **B″ delta만** 집중. self-audit 초안 검증 없이 믿지 마라 — raw 재현.

## 0. 정독
1. `study-research/_dispatch-gates.md` (G-A/G-C + ★G-F frame contract 7항)
2. `study-research/eq_us/REWORK-B2-adjustment-plan-20260604.md` (STEP 1~4)
3. `.consult-us-rework-3R-results.md` (자문 raw, 특히 R3 per-test calibration size-invalid)
4. `industries/us_defensive/raw-v3/`: `_payout_interaction.py` + `_b2_stats.py` + `_breadth_sweep.py` + `_payout_interaction.json` + `_step4_add.json` + `_breadth_sweep.json`
5. `industries/us_defensive/summary.yaml` + `15axis-audit.md`(G-A.7/G-A.8) + `candidate-ledger.md` + `research-log.md`

## 1. B″ delta 독립 재검증 (raw 재현, 초안 복붙 금지)

### ★1순위 — net_issuance PARTIAL_CONFIRMED 진위
- **직교화 incremental 재현**: net_issuance ⊥ ep_yield = partial IC +0.084 t3.71 / ⊥payout = +0.055 t2.41 잔존 독립 재현. ★둘 다 직교 후 fixed-b size-valid 유의인지 = buyback-aversion specific 채널인지 vs anti-value cluster redundancy인지.
- **단일 FDR family 생존**: 27 test M_eff=19, net_issuance raw_p 3e-05 < threshold 0.0015 재현. M_eff(eigenvalue) 정확한지.
- ★**부호 정직성**: IC 양 = anti-issuance = Pontiff-Woodgate(2008, 음) **반대**. sleeve anti-value와 정합 hedge가 over-claim 아닌지. comm_mature 4종 sign flip(small-n) 정직 박제됐는지.
- **fixed-b size-valid**: CV 2.09 통과 = NW asymptotic over-rejection artifact 아님 재확인.

### ★2순위 — payout NO_INTERACTION 진위 (split→interaction 사망)
- split QE −0.122 t−2.86 → B″ continuous interaction β0.028 t_asy0.43 / fixed-b CV 2.09 비유의 / wild-cluster p0.68 재현. ★FWL 직교화 β_dur t0.47(duration 미결합) 재현 = 직교화가 신호 죽인 게 아니라 split 자체가 garden-of-forking-paths + size-invalid artifact였음 확인.

### 3순위 — frame contract 7항 conformance + 인프라
- `_b2_stats.py` effective_n(n/(1+2Σρ_k)) / fixed_b_cv(Kiefer-Vogelsang) / wild_cluster_boot / ridge_lambda_pit 정확 구현인지. λ PIT expanding-window 동결(eval 미접촉) 확인.
- ★measure.py byte-identical(B″ = 별 파일) 확인. SUE 이연 사유(8-K furnish date) 박제 확인.

## 2. hard-fail (B/C/D/I+M/N/O = 0)
- B(실데이터): coverage 일자·n / per-test calibration size validity(★R3 핵심) / walk-forward.
- O(coverage): comm_mature 4종 small-n 정직.

## 3. 반환 (SendMessage to:"team-lead")
verdict: B″ delta CONFIRMED / CONDITIONAL(보강) / FAIL. net_issuance 직교화 독립 재현 일치/불일치 + 부호 hedge 적정성 + payout 사망 재현. self-audit 차이.
