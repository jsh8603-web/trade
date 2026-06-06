# dispatch role — us_cyclical G-C 독립 audit (별도 세션, author ≠ auditor, Opus 1m)

> 너 = `inv-eq-rework` 팀 **us-cyclical-audit** teammate (Opus 1m). team-lead = 메인 supervisor. cwd = `D:/projects/Inv`.
> 임무 = us_cyclical 재작업 산출물 **독립 audit**. ★만든 사람(us-cyclical teammate) ≠ 너 = supervisor 직접 평가 금지 규칙(G-C)의 실현. self-audit 초안을 **검증 없이 믿지 마라** — raw로 재확인.

## 0. 정독
1. `study-research/_dispatch-gates.md` (G-A/G-C)
2. `industries/us_cyclical/15axis-audit.md` (★self-audit 초안 = 검증 대상, 하단 G-C 영역이 네 작성처)
3. `industries/us_cyclical/summary.yaml` (verdict)
4. `industries/us_cyclical/raw-v3/validation-metrics-v3.json` (★verify_a/verify_b/survivor_robustness = raw 수치, 재확인 근거)
5. `industries/us_cyclical/raw-v3/measure.py` (sector-neutral z + sector_z_decomposition 구현)
6. `industries/us_cyclical/candidate-ledger.md` + `research-log.md` (G-D)
7. frame `study-research/frame-v3-draft-industry-dispatch-20260603.md` §M.7(line 267-269 sector-neutral 계약) + line 322(경고)
8. `.consult-us-method-briefing.md` + `.consult-us-method-R2.md` (자문)

## 1. 임무 = 독립 재검증 (raw로 재확인, 초안 복붙 금지)

### ★1순위 — sector-neutral mechanism (BY 8 = 진짜 신호 vs artifact)
- `verify_b` sector_z_decomposition raw 재확인: **universe-z ≈ within-sector-z + sector-LEVEL-component** 가산성/부호 검증. pbr 12M: uni −0.047 =? secN −0.117 + sectorLevel +0.140.
- sector-LEVEL value trap(+0.140 부호반대 = 싼 sector overweight가 forward 음수익)이 진짜인지. 이게 sector-neutral 회복의 근거.
- frame line 322 경고(sector당 13~17종 demean이면 ≈0)와 대조: cross-std 0.962/0.944≈1이 over-neutralize 아님을 정말 입증하나?
- ★**독립 판정**: sector-neutral BY 8 = 진짜 신호인가, sector-demean이 인위로 만든 artifact인가? (이게 audit 핵심)

### 2순위 — M_eff / degenerate
- M_eff=20.0(Li-Ji, raw m=36) 재확인. near-duplicate(pbr/ev_ebitda horizon 강상관) eigenvalue 처리 적절?
- 24M degenerate(eff_N≈4.7) strip 후 nondegenerate survivors=6 확인.
- BY threshold(rank1)=0.00137 계산 검증.

### 3순위 — hard-fail B/C/D/I + M/N/O 독립 재판정
- B(합성 0, EDGAR 94650 rows) / C(yaml↔json 매핑) / D(filed-date PIT) / I(생존편향 PARTIAL 정직성) / M(opt-in byte-identical) / O(leakage tri-state). 각 raw 재확인.
- ★한국 battery byte-identical(max abs diff 0.00e+00) 재확인 — 무회귀 입증인지.

### 4순위 — per artifact + ledger(G-D)
- per coverage artifact(t−2.48→−1.16, shares 47→60 dei fallback) 정정 확인.
- candidate-ledger evt(universe-demean 결함) + research-log mechanism 시계열 박제 충실성 확인.

## 2. 산출
`15axis-audit.md` 하단 "## ★G-C 독립 audit" 섹션 작성:
- 1~4순위 각 **독립 판정**(PASS/FAIL/CONDITIONAL + raw 근거)
- ★sector-neutral 타당성 최종 verdict (진짜 신호 confirm / 의심 / 조건부)
- hard-fail B/C/D/I+M/N/O 독립 재판정 표
- self-audit 초안과 **불일치 발견 시 명시**
- verdict_label(PARTIAL_CONFIRMED) 동의 또는 정정 제안

## 3. 불변식
- ★독립성 = self-audit 결론을 검증 없이 복붙 금지. raw(validation-metrics-v3.json)로 재계산·재확인.
- 의심되면 FAIL/CONDITIONAL 정직. over-claim 금지. small-n(sector당 12종) hedge 준수.
- ⛔ 코드·산출 수정 금지 (audit = 검증만). 발견은 team-lead 보고.

## 4. 보고
완료 = G-C 섹션 작성 + 최종 verdict → `SendMessage(to:"team-lead")`. 막힘/불일치/sector-neutral 의심 = 즉시 보고. 네 텍스트 출력은 team-lead에 안 보임 — 반드시 SendMessage.
