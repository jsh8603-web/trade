---
tags: [type/dispatch, study/eq_us, phase/v2-7phase, source/eq_kr-baseline]
date: 2026-05-30
study_id: eq_us
session: btn-profile (eq_us 전담 슬롯)
baseline: study-research/eq_kr/methodology-final-for-main-dispatch.md
---

# eq_us (미국주식 전체) — main dispatch 지시서

> 너는 종목 스터디 작업방이다. **study_id = eq_us (미국주식 전체, GICS 11 sector)**.
> 작업디렉토리 = `D:/projects/Inv` (모든 경로 이 기준). 산출 = `study-research/eq_us/`.
> ★eq_kr(한국주식)이 **사용자 검증 완료한 v2 7-Phase 방법론을 그대로 미러링**한다. 한국→미국 study_id·universe만 교체.

## 0. 먼저 정독 (6 SSOT)

1. `study-research/eq_kr/methodology-final-for-main-dispatch.md` ★**v2 7-Phase 절차 baseline (최우선)**
2. `study-research/eq_kr/raw/original-user-prompts-from-main.md` (원본 지시 시퀀스 + §C 미국주식 dispatch 권고)
3. `STUDY-ORCHESTRATION.md` (5-Phase)
4. `STUDY-KIT.md` (작업 계약 §2 v2 3흐름 · §2.5 8축 · §3 yaml 7블록)
5. `study-research/AUDIT-GUIDE.md` ★**12축 평가 SSOT** (Hard-fail 코어 4 = B실데이터·C추적성·D PIT·I생존편향)
6. `study-research/eq_kr/{frame.md, evaluation-axes.md, direction.md, plan.md}` (양식 참고 — 그대로 미국판으로 복제·교체)

## 1. 기존 미국 자료 = input (재사용, 중복 회피)

- `study-research/eq_us_cyclical/` — 경기민감 4산업(반도체 SOXX/소재 XLB/산업재 XLI/에너지 XLE) `plan-industry-regime-delta.md` + M3 실측(β_dxy≫β_rate) + `raw/industry-semi-delta.md`/`industry-industrials-delta.md`. ★현재 btn-common-task가 cyclical δ 매트릭스 작업 중 → **그 산출을 input으로 수용**(cyclical 4산업 재작업 금지, 통합만).
- `study-research/eq_us_defensive/` — 방어(XLP/XLU/XLV/XLC) direction + validation. ★단 **합성 의심 P0 재검증 대상**(eq_kr §5) — H1~H4 validation 재실행 검증 의무.

## 2. 과제

미국주식 **GICS 11 sector Tier 차등 분할 × regime(Investment Clock epoch × dollar × credit/rate) 동적가중**.

- **Tier 후보(자문으로 확정)**: T1=IT(반도체+SW)·Communication Services(빅테크) 시총 집중 / T2=Financials·Health Care·Consumer Disc·Industrials·Energy / T3=Consumer Staples·Materials·Utilities·Real Estate(★reit study 중복 경계 — 분리 또는 input 수용).
- sleeve = **팩터노출 정의**(GICS 멤버십 아님 — XLU rate-음 bond-proxy vs XLF rate-양 pro-cyclical 부호상쇄 버그 회피). 거시 = 배분레이어 전담 · 종목 = 펀더멘털. 순수 down-only.
- regime cell N gate 의무(eq_kr 36 cell 미러 — epoch × dollar × credit). cell N<24 = small-N 5게이트.

## 3. ★지금 Phase 3(자문)부터 자율 시작

`/gemini-web` + `/claude-web` 다회(3~7R 수렴)로 ①이론 수집방향 ②이론 검증방향 ③핵심 가설(반증조건 포함) 완성:
- 산출 = `study-research/eq_us/direction.md` + `raw/consult-round-{N}.md` 누적(3계층 적재: archive raw + memory + MEMORY 인덱스)
- ★끝나면 **멈추고 main(btn-Codlearn) 승인 대기**(이 멈춤은 idle 아님 — direction.md 보고 후 승인 전 Phase 3.5 진입 금지)
- 자문 경합·타임아웃이면 WebSearch/WebFetch 폴백(과도한 동시 자문 자제, 1~2R씩)

승인 후 → Phase 2 methodology-brief → Phase 4 plan → Phase 5 산업 subagent Tier 차등(opus 1m) → Phase 6 별 평가 subagent → Phase 7 통합 yaml + main 승인.

## 4. ★5 금지 (사용자 박제, 위반=Layer 1 FAIL)

1. **점추정 prior 박제 금지** — IC 점추정 → base_weight 직접 X. 분포 + CI + 게이트.
2. **합성·시뮬 데이터 금지** — random walk / 합성 panel / 가상 ticker / random IC. 실제 수집기 PIT만.
3. **자문 그대로 코드화 금지** — gemini/claude 답 → yaml 직접 X. supervisor 비판·환각 cross-verify 후 채택.
4. **Single-source 단정 금지** — 1 출처 "확정" X. 학술 + 실무 + 1차 데이터 3중.
5. **Small-N 단정 금지** — cell N<24 "유의" 주장 X. 5게이트 §N gate 우선.

## 5. ★추가 박제

- ★**supervisor(너) 직접 평가 금지** — Phase 6 별 평가 subagent(opus 1m) 위임 의무(main pass-bias 회피 미러).
- ★**analyst-level lens 다운그레이드 금지** — 시스템 못 받으면 파이프라인 업그레이드(다운그레이드 X).
- ★**opt-in off = byte-identical** — INV_R15_WEIGHTS default-off, register 검증·등록만.
- ★**reflexive loop 차단** — belief→_macro 차단, L축 공통인자 1회 계상 + PSD.
- ★**tier 정직성** — 검증 통과 ≠ validated alpha. REJECT·contemporaneous = structural prior(저신뢰) 라벨.

## 6. 보고 채널

질문·완료보고는 btn-Codlearn(main)에만:
```bash
bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[eq_us→main] 내용"
```

★지금 Phase 3 자문부터 자율 시작. direction.md 산출 후 main 승인 대기.
