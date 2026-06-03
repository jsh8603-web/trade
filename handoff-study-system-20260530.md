---
tags: [type/handoff, domain/inv, phase/study-system]
date: 2026-05-30
note: 종목 스터디 시스템 + flag 동적조정 세션 핸드오프(btn-Codlearn). 압축 전 상세 인계.
---

# handoff-study-system-20260530 — 세션 인계 (btn-Codlearn)

> 진입: progress-study-system.md / plan-study-system.md / STUDY-KIT.md / study-research/AUDIT-GUIDE.md / CONSULT-DECISIONS-layering-20260530.md

## 현재 상태 (학습 레이어 = 방별 study)
- **6방 2-3 완료**(validation-*.md + study_session.yaml): macro, eq_intl, eq_us_cyclical, commodity, gold, reit
- **opus 독립 감사 충실 3방**(provenance 재계산·합성 지문 검사 통과): commodity(조건부 — G축 structural prior tier 강등, 3 라벨), eq_intl(China β 환각 직접 재계산 기각=E축 모범), macro(H2 FAIL p=0.348 정직·analysis_output.txt byte 동일)
- **eq_us_cyclical 감사 대기**: background agent a427f8643 — 압축 후 tasks/a427f8643*.output 확인
- 진행 중: crypto(2-3, yaml 미작성), bond_cash(validation 3, yaml 미작성), eq_us_defensive(★합성 시뮬 seed 적발→실데이터 보강 지시함), eq_kr(2-1 round-1만)
- raw 229파일 + 핵심정리(direction/theory-notes/validation/yaml/summary) 전부 보존

## 구현 완료 (flag 동적조정 = seed->라이브 진화, 전부 self-test PASS·무회귀)
- U1 flag->lens: lens_store.render(confidence_note=) + flag_router.confidence_note() + study_register.prepare_judge_call 연결. None=byte-identical.
- U2 flag->corr_prior: flag_router.corr_prior_shrink(base, series_ids, affects_edge 직접/node fallback). study_loader.ConfidenceHook.affects_edge 필드.
- U3 corr_prior level 가드: corr_prior_shrink(level='micro'|'macro'). macro=belief no-op 차단(reflexive loop 방지, single-writer). self-test: micro 0.6->0.3 / macro=base 그대로.
- flag->weight = 기존 G4 tilt_weights.
- ★U3 남은 wiring: study_register 가 corr_prior_shrink 호출 시 study scope 로 level 결정(거시·채권=macro, equity/commodity 종목지표=micro). 호출부 미연결(메서드만 존재).

## 자문 3R 수렴 (gemini+claude -> CONSULT-DECISIONS-layering-20260530.md)
영속 원칙 5: (1)Belief-Truth 격리(belief는 식별=regime tag·가설·gate 입력에만, ground-truth 층=macro 상관·실현 수익률엔 절대 안 씀) (2)Single-writer invariant (3)희소 regime->pooled shrink (4)hysteretic soft gate(deadband, hard 아님) (5)consensus=agreement-measurement(불일치를 confidence로, regime 전이 조기경보). 사용자 합의: 포트폴리오 배분=confidence-weighted soft gate / 거시=consensus.

## 미해결 결정 / 다음 작업 (우선순위)
1. eq_us_cyclical 감사(a427f8643) 결과 확인 -> 충실이면 4방(macro·eq_intl·eq_us_cyclical·commodity) 일괄 StudyRegister.register(경로, require_raw=True). ★L축: register 시 공통인자(USD·real_rate·글로벌유동성) 중복 계상 PSD 점검(eq_intl·macro·gold 겹침). system_priors.factor_implied_cross_cov 1회 계상.
2. U3 wiring: study_register 호출부 level 전달.
3. U4(후순위·키잉만 freeze): FlagAccumulator->regime-keyed Beta(belief-weighted soft + pooled shrinkage, n->0=pooled), soft gate stub(floor/ceiling+deadband). 파라미터 튜닝 금지(자문 과설계 경고).
4. 나머지 방: crypto/bond_cash yaml 작성, eq_us_defensive 실데이터 보강, reit yaml v2(819줄 v1 폐기), gold H3/H5/H8 잔여, eq_kr 2-1.
5. 과거데이터 학습 운영: flag 쌓기(emit_ic_outcome)는 항상(누락0), 쓰기(INV_R15_WEIGHTS)는 baseline(off) 먼저->on 비교. flag 3경로 live baseline 전 shadow/log-only.

## 운영 메모
- opt-in: INV_R15_WEIGHTS(weight tilt+corr), INV_STUDY_LENS(lens). default-off=무회귀. SACRED: DRY_RUN/execute_trade 불변, 실거래 flip=사용자 게이트.
- 신규: study-research/AUDIT-GUIDE.md, CONSULT-DECISIONS-layering-20260530.md. 수정: core/study/{lens_store,flag_router,study_loader,study_register}.py. README §종목 스터디 시스템 추가.
- 감사 = opus subagent, AUDIT-GUIDE 12축(hard 코어 B·C·D·I / G=tier 라벨), 방 self-audit 불신·독립 재계산.
- 세션<->study_id 매핑: progress 표(btn-button=macro ... btn-profile=crypto).
- ★btn-Inv peer commit 2f46607d(+469/-10) — 커밋 전 git pull --rebase 검토.
- 미커밋: core/study/* 신규·수정 + study-research/* + README + CONSULT-DECISIONS + progress/STUDY-KIT. 사용자 커밋 지시 대기.
