---
tags: [type/consult-decision, domain/inv, topic/layering-flag-dynamics]
date: 2026-05-30
note: 자문 3R(gemini-web Pro + claude-web Opus) 완전 수렴 — 멀티에셋 두 레이어(거시 게이트/종목 평가) + flag 동적조정(weight·lens·corr_prior) 설계 원칙. reflexive loop 차단·single-writer·regime-tag·soft gate·agreement consensus.
---

# CONSULT-DECISIONS-layering — 두 레이어 + flag 동적조정 (자문 3R 수렴)

> gemini-web(Gemini Pro) + claude-web(Opus 4.8) 병렬 3라운드, 완전 수렴.
> 자문 raw = `~/.claude/.gemini-web-last.md` / `~/.claude/.claude-web-basic-last.md`.

## 맥락
멀티에셋 두 레이어 — **(A) 포트폴리오 배분**: 거시 regime → belief b(t) → Black-Litterman sleeve % 배분(게이트 성격) / **(B) 매수·매도**: 종목 평가 → R15 weight_card → S_L1 사이징 → judge(L1∥DCF + L2 qwen/L3 BGE attenuating-only, down-only). study 시스템이 종목 weight_card 를 이론+실데이터로 산출(seed), 라이브 flag(확신/거부)가 weight·lens·corr_prior 동적 조정.

## ★영속 보관 원칙 (5 — 두 모델 수렴)
1. **Belief-Truth 격리** (1순위 불변식): belief(주관 판단)는 **식별**(regime tag·가설·gate 입력)에만 쓴다. ground-truth 층(macro 상관·실현 수익률 등 검증 층)엔 절대 직접 쓰지 않는다. 누수 = 설계 붕괴·silent 오염.
2. **Single-writer invariant**: 모든 상태 객체는 쓰기 경로 1개, **목적별 분리**(bifurcate by purpose). corr_prior 레벨 단방향 분리가 reflexive loop 를 코드 레벨에서 차단.
3. **희소 regime → pooled shrink**: n 작은 버킷을 그대로 신뢰하지 않는다. graceful degradation 이 기본값(hierarchical/partial-pooling, n→0 이면 pooled 로 수렴).
4. **Gate = hysteretic soft**(deadband+clamp), bang-bang(hard) 아님. hard 는 ramp 폭 0인 soft 의 degenerate 극한. 식별 confidence 와 action 크기는 항상 분리.
5. **Consensus = agreement-measurement**: 여러 독립 분류기의 regime 콜은 discrete 유지, 합의도를 confidence 로 사용(불일치 = regime 전이 조기경보). ⛔ averaging(boom+bust 평균=neutral, 정확히 틀림) 금지. 앙상블 가치 = 더 나은 점추정이 아니라 **측정된 불일치**. 다양성(직교 메커니즘) > 개수.

## reflexive loop 위험 (핵심 발견 — 내 U2 구현 직격)
종목 flag → corr_prior → macro Σ → macro 되먹임. 종목 확신은 하필 **drawdown 직전 최대**(pro-cyclical). 강세장 후반 대부분 종목이 매수 확신 → 단일 corr_prior 억눌림 → 거시 레이어가 "시장 리스크 극저" 오판 → 하락 전환 직전 **최대 위험예산 할당 = 재앙**.
→ **처방** (single-writer): corr_prior 를 `_macro`(sleeve×sleeve dense) / `_micro`(sleeve별 block-diagonal, security×security 같은 sleeve 내부만) **별개 객체·다른 인덱스 공간**으로. 종목 flag/belief 는 `_micro` 만 갱신(cross-sleeve 인덱스가 _micro 에 아예 없음). `_macro` 의 유일한 writer = 실현 cross-sleeve 수익률(EWMA blend) + regime 전이(macro_by_regime swap) — belief 변수를 인자로 받지 않음. cross-sleeve hypothesis edge = 런타임 가드 거부(ValueError).

## 수정 우선순위 (두 모델 동일 순서)
1. **corr_prior 레벨 분리** — 최상/즉시. **correctness 문제**(modeling quality 아님). belief 가 ground-truth 에 새면 silent 오염이라 디버깅도 안 되고 다운스트림 전부 편향. 나머지 둘이 이 분리를 전제하므로 안 고치고 진행 = 오염 위에 build.
2. **soft gate** — 단 "보수적 stub"으로만. live 전 blast radius bound 하는 circuit-breaker(floor/ceiling/deadband 안전쪽 박되 튜닝 X). 정교화는 live 이후.
3. **Beta regime-tag** — 후순위. 키잉 구조만 맞추고 파라미터 freeze. 진짜 calibration 은 live 분포 필요. 지금 정밀 맞추면 스터디 데이터 artifact 에 fit. 구현형 = belief-weighted soft update + pooled shrinkage fallback.

## 과설계 경고 (현 단계 = 실거래 전, 스터디 산출 통합 중)
- **robustness feature**(deadband, clamp, pooled shrinkage, graceful fallback) = 데이터 무관하게 옳음. 지금 넣어도 OK.
- **optimization/adaptation feature**(튜닝된 adaptation rate, 학습된 threshold, regime별 policy, dynamic path 선택) = **freeze**. live 분포에서만 가치.
- ★**flag 3경로(방금 구현)**: 메커니즘 존재(plumbing)는 OK. 시기상조: (a) 경로 임계값을 스터디 데이터로 튜닝 (b) 미관측 regime 분기 정교화 = YAGNI, default-off 뒤 (c) **baseline 없이 동적경로 실제 acting → shadow/log-only, 실제 개입 off** (static baseline 없으면 "동적조정이 도움 됐나" 측정 불가) (d) belief adaptation 을 belief 식별 위에 또 얹어 루프 닫기 = live 없이 두 adaptive loop 상호작용 attribution 불능.
- 종합: **skeleton + safety rail 까지만, 모든 knob 보수값 freeze, held-out live baseline 생기기 전엔 어떤 adaptive loop 도 닫지 마라.**

## 내 시스템 적용 함의 (TODO — progress 큐 연결)
- ★**U2 `flag_router.corr_prior_shrink`** = 현재 단일 corr_prior 약화 → reflexive loop 위험. **레벨 분리(_micro 한정) 필요 = 1순위 correctness**. 단 구조만, 파라미터 freeze. cross-sleeve edge 런타임 가드 추가.
- **`FlagAccumulator`** → regime-keyed Beta(belief-weighted soft + pooled shrink). 지금은 키잉 구조만, freeze.
- **flag 3경로** = `INV_R15_WEIGHTS` opt-in(이미 default-off). live baseline 전 shadow/log-only 유지(실제 개입 off).
- **`regime_to_weights`** gate = soft(deadband) 확인(이미 BL confidence-weighted Prior 근접). 
- **거시 consensus** = 직교 2nd regime view(시장가격 내재 regime 등) 1개 추가 후보 — 불일치 신호 생성용. 단 과설계 경고대로 최소부터, 합의 collapse 는 고신뢰일 때만.
