---
tags: [type/handoff, domain/inv, topic/study-wire-gap, session/btn-Inv]
date: 2026-06-01
author: btn-Inv (재개 세션 후속)
scope: study merit 후속 탐구 + 12축 audit + J축 β + regime-conditional + ★study→코드 wire 전수조사(거시 ref)
predecessor: handoff-study-merit-audit-20260601.md
exclude: eq_kr / eq_us = stock.md 별도세션
push: ⛔ 금지 — 로컬 commit만 (coin.git peer 충돌 회피, 사용자 재확인 2026-06-01)
---

# Handoff — study wire gap 발견 + merit/audit/J축/regime (2026-06-01)

> **재개 읽기**: 본 파일 → progress-study-system.md → 각 산출.
> **★이번 세션 최대 발견 = study 산출이 런타임 매매결정에 미연결(설계상 opt-in facade 미개통). §3 필독.**

## 1. 이번 세션 완료 (커밋, push 금지=로컬만)

### 1-A. merit 후속 탐구 + 독립 12축 audit
- **cyclical merit audit** = 충실(hard0). DGORDER→XLE structural_low. (a2f4411 yaml v5)
- **crypto/eq_intl/defensive** audit verdict → yaml 반영 (b1ef5f4 / c17c874 / 7dc5263). defensive yaml 선재 파싱 결함(line 19 inline 콤마) 정정.
- **eq_intl L축 DTWEXBGS full-sample 재검** (d17af0d): DXY n=59 caveat 해소, partial −0.258, DTWEXBGS observation_start=2006 실측 정정(handoff '1996~' 오류).
- **지역연준 diffusion** (cc02158): Empire(NOCDISA)→SOXX 음 forward = ★cyclical merit 첫 Bonferroni 생존(2/84). 단 single-region(NY), Philly 비유의, cross-study pooled m=168 기준 k=6만 robust. 독립 audit 충실. 적시성(14d)≠예측력(census DGORDER→XLE 압도) REJECTED.
- **regime-conditional PoC** (커밋됨): DGORDER→XLE inflation高 +0.42 sharpen(Bonferroni 생존). NEWORDER(full 붕괴) 부활 실패. T10Y2Y→XLI full +0.02→infl高 −0.44 부호반전(Bonferroni 미생존·belief-weighted 소멸). ★결론 = regime은 신호 refinement 도구지 creation 아님. yaml 미반영(부분 입증 신중).

### 1-B. J축 factor β shadow validation (de2d44d, SEED 미반영)
- sample(eq_us_defensive) + batch(gold/cyclical/eq_intl/reit/commodity) raw 5 factor 표준화 회귀.
- ★vol(ΔVIX) 포함이 깨끗한 절대 std β 산출 관건. 전 equity vol −0.57~−0.69 validated. gold 재현 일치(dollar −0.317 vs SEED −0.328)=방법 신뢰.
- §1.6 unit 분리: DEFENSIVE_PURE(rate≈0 vol흡수) vs FINANCIALS(rate +0.162 NIM). XLE oil만 특이.
- factor_shadow OOS bias-stat 1.000 PASS, off-path 확인.
- ★SEED_CELLS 미반영 사유 = vol pool 활성 시 **gold(real_rate_currency 그룹) grand fallback cross-group 오염**(시뮬 −0.508 확인). build_seed_betas 로직 보완 선행 필요(§4).

### 1-C. credential 무료대체 probe (367d880)
- cushing 재고/roll_yield = ❌무료 불가(EIA/CME key 필요). fwd EPS = ⚠️부분(FINNHUB 무료key coarse). ISM/PMI = ✅무료(census + 지역연준 diffusion).

## 2. ★★ 이번 세션 최대 발견 — study→코드 wire 전수조사 (거시 ref, read-only)

**결론: study 산출(거시 regime·상관 prior·weight·merit 지표)이 런타임 매매결정에 미연결. 설계상 opt-in facade 미개통.**

| 경로 | 코드 연결 | 근거 |
|---|---|---|
| judge(qwen L2/BGE L3) lens·corr | **X** | judge() 런타임 호출 0(run_agents=코인봇 점수제). lens_prompt/_call_qwen_with_lens 기구현이나 미호출 |
| relationships→corr_prior | **X** | 런타임 RegimeGlasso() 전부 corr_prior= 생략→np.eye. 주입점(prepare_corr_prior)=study_register 미연결 |
| merit 지표(DGORDER/Empire/vix_term/fx_carry/ism_pmi) | **X 채택0** | yaml indicators·코드 grep 0. candidate-rationale.md에 "보류/측정대기/Phase A 후보"로만 |
| indicators→feature/weight_card | **X** | self-test + 오프라인 train_weights뿐, 라이브 0 |
| 거시 regime 지표→분류기/배분 | **부분** | fred_adapter:36~65 FRED_SERIES(HY OAS·T10Y2Y·DFII10·T5YIE·NFCI·DTWEXBGS) 등록 + RegimeClassifier→regime_to_weights 구현. **그러나** run_agents:857~881 INV_CORE_GATE on 시 classify() 결과 **로깅만**(decision 미반영). portfolio_orchestrator.allocate()=coin_track_macro.py:64만 호출, run_agents import 0 |
| factor seed/shadow→risk_gate | **X** | M5 범위 밖. self-test + raw 스크립트만 |

- **"언제부터 누락"** = 누락 아니라 **설계상 미개통**. register.py docstring "둘 다 off면 검증만, production 경로 미개통". prepare_judge_call(런타임 진입) 코드 호출 커밋 0건(348e7af=docs handoff뿐). run_agents 거시 chain = INV_CORE_GATE/INV_R15_WEIGHTS 게이트 하 "로깅 wire"만("결정 변경 없음(공급·로깅)" 주석).
- **사용자 우려 확정**: (a) BGE/qwen 상관 미주입 = judge 런타임 부재 + corr_prior 생략. (b) merit 발굴 지표 누락 = 채택 0(발굴은 문서, 등록 미실행).
- 조사 산출 = subagent ae1b71ee (read-only, 코드 미수정).

## 3. ★다음 세션 작업분 (사용자 자율주행 지시 — 우선순위 순)

### P1. 전 자산 wire 전수조사 (별건, 거시 ref 패턴 확장)
- 거시 ref 완료 → gold/cyclical/eq_intl/reit/commodity/bond_cash/crypto/defensive 각 study yaml 산출이 동일하게 미개통인지 전수. (거의 동일 패턴 예상이나 확인 의무 — E94)
- 산출 = 자산별 wire 현황 매트릭스 + 개통 우선순위.

### P2. Phase I 통합 개통 설계 (★go-live 경계 — SACRED·사용자 인지 필수)
- merit 지표 yaml indicators 등록 → build_indicator_matrix series_id 추가
- study_register/prepare_judge_call/prepare_corr_prior 를 런타임 진입점(orchestrator/judge)에서 호출 개통
- corr_prior 행렬에 relationships 주입 (RegimeGlasso corr_prior= 인자 wire)
- judge lens + 상관 prior → qwen L2/BGE L3 lens_prompt (down-only 불변식 보존)
- 게이트(INV_CORE_GATE 등) on 정책 — ⛔ DRY_RUN/execute_trade SACRED, belief→_macro 차단, opt-in off 무회귀 불변식 준수. 실거래 flip = 자율 범위 밖(autopilot scope).
- ★자문 ⑧(Risk 변경) 권장: 개통 순서·게이트 정책 gemini+claude.

### P3. J축 SEED 반영 + build_seed_betas 보완 (M5)
- ★grand fallback cross-group 오염 해결: (B) factor별 정책 — dollar/rate/oil/credit=cross-asset(grand OK) vs vol=group-specific(그룹 measured 없으면 0). ★cross 처리 가능 factor/자산을 외부 자문으로 확인 후 12축 audit하고 반영(사용자 지시).
- batch std β(de2d44d 산출)로 SEED_CELLS 갱신 + self-test #7(vol pool) 조정.

### P4. regime-conditional / cross 정책 (main 검토→자문→12축 audit→반영)
- regime-conditional = 신호 refinement 도구(PoC 입증). belief-weighted IC vs hard split. 검정력/다중비교/lookahead rigor.
- T10Y2Y→XLI 부호반전(infl高 −0.44) 추가 검증 가치(현 Bonferroni 미생존).

### P5. credential (key 발급 시)
- EIA(cushing)/CME(roll_yield)/FINNHUB(fwd EPS) — 사용자 key 발급 후.

## 4. 환경/불변
- python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` prefix 필수.
- audit=별도 opus subagent 12축 self-certify 금지. 점추정 magnitude 박제 금지·sign/direction prior 생존.
- ⛔ push 금지(로컬 commit만). DRY_RUN/execute_trade SACRED. belief→_macro 차단. 공통인자 1회 계상. opt-in off 무회귀.
- eq_kr/eq_us=stock.md 별도세션. local-db L3~L6=별도 트랙(sqlite.md).
