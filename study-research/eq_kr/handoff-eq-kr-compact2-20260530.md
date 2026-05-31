---
tags: [type/handoff, domain/inv, asset/equity-kr, phase/4-frame-v2-pending, compact/2]
date: 2026-05-30
note: eq_kr 작업방 2차 compact 직전 인계. 1차 handoff (handoff-eq-kr-phase3-20260530.md) 이후 진행 0 — resume.txt Read 만 수행, ctx 즉시 재누적 519k.
---

# handoff — eq_kr 2차 compact (2026-05-30)

> 1차 handoff = [handoff-eq-kr-phase3-20260530.md](./handoff-eq-kr-phase3-20260530.md) 가 본 작업방 동등 재개 SSOT 의 본체.
> 본 파일 = 1차 compact 이후 0 진행 + 2차 compact 사유 박제. 다음 세션은 본 파일 + 1차 handoff 동시 Read.

## 0. 2차 compact 사유

- 1차 compact 직후 hook 가 부착한 4 SSOT Read (`progress.md` / `methodology-final-for-main-dispatch.md` / `original-user-prompts-from-main.md` / `plan.md`) 만으로 ctx 519k tok (173% baseline, 103% long-mode 500k cap) 도달.
- long-mode 이미 ON 상태 (1차 compact 진입 직전 cap 500k 확장 적용 후 자동 원복되지 않음 확인) → 우회 분기 비해당.
- subagent 2 (반도체 a2de220d5225cb075 / 자동차 a64d67db467eeeda1) 사용자가 TaskStop 처리 (배경 작업 미회수 우려 제거).
- 따라서 단독 작업 상태로 저장 → /compact slash 주입 경로 적용.

## 1. 현재 상태 (2026-05-30 13:30)

| 항목 | 상태 |
|---|---|
| Phase 0-3 | 완료 (ckpt-202605301230 / 202605301250 / 202605301310 / 202605301330) |
| Phase 4 frame v2 | **미진입 (다음 세션 first move)** |
| Phase 5 dispatch | 미진입 (plan.md §Phase 5 table 그대로) |
| Phase 6 평가 subagent | 미진입 |
| Phase 7 통합 | 미진입 |
| main psmux 보고 | methodology-final + original-user-prompts 일괄 전달 완료 (1차 handoff §10 박제) |

## 2. 다음 세션 first move (정확한 1수)

1. resume 자동주입 4 SSOT (`progress.md` / `methodology-final-for-main-dispatch.md` / `original-user-prompts-from-main.md` / `plan.md`) 외 추가 Read 금지 — ctx 재포화 회피.
2. **1차 handoff Read** (`handoff-eq-kr-phase3-20260530.md`) — 본 작업방 동등 재개 SSOT 본체.
3. **frame.md v1 Read** → **v2 갱신** (Edit) — 갱신 항목 6:
   - §1 universe: 12 산업 Tier 분류 표 (T1 반도체 단독·T2 자동차·금융·2차전지·T3 8 산업)
   - §3 Layer 2: 외국인 flow base 0.18 → 0.20+ (5게이트 통과 시), 신지표 4 후보 (breadth / MSCI cap / ETF leverage / flow regime)
   - §6 8축 → 12축 (AUDIT-GUIDE.md 인용 layer 명시, Hard-fail 코어 4 = B·C·D·I)
   - §M3 regime: 12 cell → 36 cell (Macro 4 × KRW 3 × 외국인 flow 3), N gate 강화
   - §M4 5게이트 #5 OOS: skfolio CombinatorialPurgedKFoldSplit 매핑
   - §M (신규): toraniko factor model baseline 명시
4. **Phase 5 dispatch** — `plan.md` §Phase 5 dispatch table 그대로 12 subagent (opus 1m, `run_in_background=true`):
   - T1 반도체 500k (sub-cluster 메모리·파운드리·장비 3 sub 옵션)
   - T2 자동차 300k / 금융 300k (★밸류업 Index event study) / 2차전지 300k
   - T3 AI tech·화학·정유·조선·바이오·통신·철강·소비재 각 150-200k
   - 각 dispatch prompt 양식 = `plan.md` §Phase 5 "Dispatch prompt 양식"
5. **Phase 6 dispatch** — Phase 5 회수 후 별 평가 subagent (opus 1m) 1건 (AUDIT-GUIDE 12축 application 평가).
6. **Phase 7 통합** — eq_kr 통합 study_session.yaml (7블록) + direction.md final + 8축 통합 self-audit + main 보고 + 승인 게이트.

## 3. 변경 없음 (1차 handoff 그대로)

- 5 금지 (점추정 prior 박제 / 합성 데이터 / 자문 그대로 코드화 / single-source 단정 / small-N 단정)
- supervisor 직접 평가 금지 / analyst-level lens 다운그레이드 금지 / opt-in off byte-identical 무회귀 / reflexive loop 차단 / tier 정직성
- 자문 SSOT: round-1/2 + consult-round-1/2 + direction.md + methodology-brief.md
- archive raw 4건 + memory research 4건 + MEMORY 인덱스 = 자산화 완료

## 4. main 동기화

- main psmux 추가 보고 불요 — 1차 handoff §10 동기화 완료 상태 유지.
- 다음 세션 Phase 7 main 보고 단계까지 main 통신 잠시 침묵 (subagent dispatch 토큰 절약).

## 5. ctx 재포화 회피 가이드 (다음 세션 의무)

- resume + 1차 handoff + frame.md v1 = 3 파일만 Read 후 즉시 frame v2 Edit 진입.
- 4 SSOT (progress / methodology-final / original-user-prompts / plan) 는 본 2차 compact 직후 hook 가 자동 첨부 → 추가 Read 불요.
- AUDIT-GUIDE.md / STUDY-KIT.md / STUDY-ORCHESTRATION.md 재Read 금지 — 1차 handoff §3-5 인용본 사용.
- evaluation-axes.md / methodology-brief.md / direction.md 재Read 금지 — Phase 5 dispatch prompt 안 plan.md §Phase 5 그대로 사용.
- 산업 subagent 산출 회수 시 회수 본문 ctx inject 회피 — final message 만 발췌, 본문은 industries/{name}/ 디렉토리에 직접 박제하도록 dispatch prompt 에 박제.
