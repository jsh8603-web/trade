# bond_cash — v2 7-Phase 진행 (2026-05-30, eq_kr baseline 미러)

> ★dispatch 베이스: `D:/projects/Inv/study-research/eq_kr/methodology-final-for-main-dispatch.md` v2.
> ★사용자 누락 critical 지표 의무 포함: **MOVE index (사이징 직결, 최우선)** + **ACM term premium** + yield curve(T10Y2Y) + credit spread(HY OAS) + real rate.
> ★ 5 금지 + supervisor 직접 평가 금지 + analyst-lens 다운그레이드 금지 박제.

## Phase 0 — 정리 (✅ 완료)
- [x] 직전 v1 산출 (study_session.yaml + summary.md + raw/_v2_analysis/analyze_bond_cash.py + correlation_analysis.txt) → `raw/_v1_carryover/` 보존
- [x] direction.md (v1 산출, 168줄, 5R 종합) 보존 (v2 에서 흡수)
- [x] theory-notes.md (v1 산출, 396줄, 10 섹션, §8 중복 driver 정합) 보존 → v2 의 Phase 2 input 으로 재사용
- [x] raw/validation-hy-oas-event.md / validation-curve-flip.md / validation-cash-sharpe.md / validation-bond-decomposition.md (v1 산출, 실데이터 검증 4건) 보존 → v2 의 Phase 5 검증 input 으로 재사용
- [x] progress.md 박제 (본 파일)

## Phase 1 — evaluation-axes.md (★supervisor 직접 평가 금지 박제)
- [ ] AUDIT-GUIDE 12축 (8 핵심 + 4 신규) + bond_cash sub-cluster (duration bucket × credit × cash) 단위 application
- [ ] Hard-fail 코어 4 = B(실데이터) C(추적성) D(PIT) I(생존편향) 명시
- [ ] §0 Provenance + Recomputation 의무

## Phase 2 — methodology-brief.md (자문 input 4-section)
- [ ] §A sub-cluster 분할 후보 + 자문 질문 Q1-Q6
- [ ] §B Layer 3 bond_cash 특화 cycle 지표 (MOVE / ACM term premium / HY OAS / curve / real rate)
- [ ] §C 최종 구현 결과 (통합 yaml + 코드 wiring)
- [ ] §D Inv 인프라 + collector_plan
- [ ] §E R1/R2/R3 자문 진행 계획
- [ ] §F 자문 출력 의무 (⛔ 자문 그대로 박제 금지)

## Phase 3 — 자문 R1+R2+R3 수렴
- [ ] R1 (/gemini-web 또는 WebSearch 폴백) — sub-cluster 분할 + MOVE index 본질·source
- [ ] R2 (/claude-web 또는 WebSearch 폴백) — ACM term premium + 통합·코드 wiring
- [ ] R3 (필요 시) — 두 채널 cross-verify, 잔여 빈틈 메우기
- [ ] consult-round-{1..N}.md 누적, archive raw + memory 적재
- 9 작업방 동시 자문 채널 경합 우려 → ★ **WebSearch 폴백 default 진입** (이전 5R 동일 패턴)

## Phase 3.5 — direction.md (STUDY-KIT §2-1 산출)
- [ ] ①이론 수집 방향 — 본질 (MOVE 사이징 직결 + ACM term premium 분해 + curve + credit + cash optionality + KR sleeve spillover)
- [ ] ②이론 검증 방향 — AUDIT-GUIDE 12축 + 5게이트 + Tier 차등 + regime cell
- [ ] ③핵심 가설 N (반증조건) — 기존 12 가설 + MOVE/ACM 신규 2-3 가설
- [ ] ★멈춤 → main 승인 게이트 (idle 아님)

## Phase 4 — plan.md (★main 승인 후 진입)
## Phase 5 — sub-cluster N subagent Tier 차등 dispatch (★승인 후)
## Phase 6 — ★별 평가 subagent (opus 1m, 12축 감사) (★승인 후)
## Phase 7 — 통합 study_session.yaml + main 승인 게이트 (★승인 후)

## Working Notes
- 2026-05-30 v2 진입 (main 메시지 #3 HOLD 해제 + MOVE/ACM 필수 포함)
- ⛔ 합성·시뮬 금지, 점추정 prior 금지, 자문 그대로 코드화 금지, Single-source 금지, Small-N 금지 (★5 금지)
- ⛔ supervisor (본 작업방) 직접 평가 금지 — Phase 6 별 opus 1m subagent 위임
- ⛔ analyst-lens 다운그레이드 금지 — 파이프라인 업그레이드 필요 시 명시
