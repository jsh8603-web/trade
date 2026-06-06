# dispatch role — us_defensive G-C 독립 audit (별도 세션, author ≠ auditor, Opus 1m)

> 너 = `inv-eq-rework` 팀 **us-defensive-audit** teammate (Opus 1m). team-lead = 메인 supervisor. cwd = `D:/projects/Inv`.
> 임무 = us_defensive 재작업 산출물 **독립 audit**. ★author(us-defensive teammate) ≠ 너 = supervisor 직접 평가 금지(G-C) 실현. self-audit 초안을 검증 없이 믿지 마라 — raw 재계산.

## 0. 정독
1. `study-research/_dispatch-gates.md` (G-A/G-B/G-C)
2. `industries/us_defensive/15axis-audit.md` (★self-audit 초안 = 검증 대상, 하단 G-C 영역이 네 작성처)
3. `industries/us_defensive/summary.yaml` (verdict = INSUFFICIENT)
4. `industries/us_defensive/raw-v3/validation-metrics-v3.json` + `_gb_verify.json` (★verify/regime split/leave-sub-sector = raw 수치 재확인 근거)
5. `industries/us_defensive/raw-v3/{collect,measure}.py + _gb_self_verify.py` (sector-neutral z + regime split + decomposition 구현)
6. `industries/us_defensive/candidate-ledger.md` + `research-log.md` (G-D)
7. `.consult-us-defensive-R1-results.md`(자문 수렴 요약) + `~/.claude/.gemini-web-last.md`·`.claude-web-basic-last.md` **tail(2026-06-04 항목)** (G-B 자문 raw 전문)
8. ★대조용: `industries/us_cyclical/15axis-audit.md`(G-C 통과 양식) — us_cyclical 은 sector-neutral 회복(BY 0→8), us_defensive 는 무회복 = 대조

## 1. 임무 = 독립 재검증 (raw 재계산, 초안 복붙 금지)

### ★1순위 — anti-value 본질 vs QE artifact (verdict 핵심)
- **regime split 재확인**(_gb_verify.json): ep_yield QE era(2010-21) −0.061 vs value-revival(2022-26) −0.040 부호 유지 / payout QE −0.122 → 2022+ +0.054 FLIP. raw 재계산해 부호·magnitude 재현.
- ★**독립 판정**: ep_yield anti-value = 부분 본질(regime-robust)인가, 전부 QE artifact 인가? payout/dividend = reach-for-yield QE artifact 확정 타당한가?
- **leave-sub-sector**(claude 지적 healthcare 지배): ep_yield ex_healthcare −0.062 = healthcare 비의존, sleeve-wide 재현?
- **quality partial-corr**: ep_yield raw −0.056 → gross_prof 통제 후 −0.051 독립 잔존 재확인(quality proxy 아님).
- **sector-neutral 무회복**: sector_z_decomposition pbr uni+0.021/secN+0.016/sectorLevel+0.009 세 성분 약·동부호 = sector-mixing 주범 아님 재확인(us_cyclical 과 대조 = defensive cross-sectional value 자체 약).

### 2순위 — BY / M_eff / G-B 트리거 + 자문 수렴 적절성
- M_eff=26.0(raw m=48, Li-Ji) 재현. BY threshold 0.000998. survivors=0(raw_p_min 0.0174 ep 3M > thr×2) = G-B 트리거 조건 충족 재확인.
- ★G-B 자문 수렴 verdict 타당성: sleeve INSUFFICIENT + ep_yield TENTATIVE_DIRECTIONAL(regime-conditional) + payout rejected_provisional(부활트리거) + duration QUALIFIED = 자문 raw(R1-results + last.md tail)와 산출 verdict 정합? over-claim/under-claim?

### 3순위 — hard-fail B/C/D/I + M/N/O 독립 재판정
- B(합성 0, EDGAR 111140 rows 17 concept) / C(yaml↔json+_gb_verify 매핑) / D(filed-date PIT negative lag 0) / I(생존편향 PARTIAL 정직) / M(opt-in byte-identical) / O(tri-state, utilities gross_prof NaN). raw 재확인.

### 4순위 — ledger(G-D) + cross-market + 자문 매핑
- candidate-ledger verdict 표 + falsifier + enum + ★G-B 자문 raw→산출 매핑(누락 0, consult-raw-output-mapping-checklist). research-log G-B~자문~verdict 시계열.
- ★cross-market 함의(미국 anti-value ≠ 한국 value premium = 묶음 시장 의존) 박제 타당성 — G-E 입력 정합성.

## 2. 산출
`15axis-audit.md` 하단 "## ★G-C 독립 audit" 섹션 작성:
- 1~4순위 각 독립 판정(PASS/FAIL/CONDITIONAL + raw 근거)
- ★anti-value verdict 최종(ep TENTATIVE 타당 / payout rejected 타당 / sleeve INSUFFICIENT 타당) 동의 또는 정정
- hard-fail 독립 재판정 표 + self-audit 불일치 명시
- ★자문 수렴 verdict 가 raw 와 정합한지(over/under-claim 점검)

## 3. 불변식
- ★독립성 = self-audit·자문 verdict 를 검증 없이 복붙 금지. raw(validation-metrics-v3.json + _gb_verify.json)로 재계산.
- small-n(sector당 12종, comm 4종) hedge 준수. 의심되면 FAIL/CONDITIONAL 정직. over-claim 금지.
- ⛔ 코드·산출 수정 금지(audit=검증만). 발견은 team-lead 보고.

## 4. 보고
완료 = G-C 섹션 작성 + 최종 verdict → `SendMessage(to:"team-lead")`. 막힘/불일치/anti-value 의심 = 즉시 보고. 네 텍스트 출력은 team-lead 에 안 보임 — 반드시 SendMessage.
