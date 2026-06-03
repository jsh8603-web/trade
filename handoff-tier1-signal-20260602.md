---
tags: [handoff, inv, tier1, macro-signal, test-readiness, self-contained]
date: 2026-06-02
session: btn-Inv
commit: f0d1880 (v1.37.0)
purpose: Tier1(거시 신호 보강) 완료 핸드오프 — clear 후 이 파일만으로 재개. 다음=Tier2(P1 배선→Test2)
entry: 이 파일 1독 → progress-test-readiness.md → plan-test-readiness.md
---

# 핸드오프 — Tier1 거시 신호 보강 완료, 다음 Tier2 배선 (자기완결)

> **clear 대비 자기완결**: 이 파일만 읽고 재개 가능. 상세는 §끝 포인터. **push 금지**(사용자 지시 유지).

## 0. 한 줄 현황
수익률 테스트 준비 마스터플랜에서 **Tier1(거시 신호 보강, M1~M5) 완료·커밋(f0d1880 v1.37.0)**. 다음 = **Tier2 = 원래 P1 배선**(engine 사이징·risk_gate·judge 결정론 연결)→Test2a. 사용자가 "Tier2는 새 세션" 선택해 여기서 clear.

## 1. 큰 그림 — 왜 이 작업을 하나 (전체 흐름)
- **목표**(사용자): 수익률 시뮬에서 손실 나면 "방법론 결함"인지 "코드(상수/가중치) 결함"인지 **원인 분리**.
- **Test1(둔갑 자문)**=방법론 OK 박기. **Test2(실파이프라인 시계열 주입)**=코드 진단.
- ★발견: Test2가 돌릴 파이프라인의 **결정→사이징→게이트 체인이 미배선**(engine.py risk_gate 미호출·사이즈 고정 95%·judge production 호출 0) → 배선이 선결.
- ★judge 재설계(클로드 최종결정·consensus·강화 flag)는 **결정론 Test2 후**에 — LLM을 먼저 넣으면 "LLM 판단 결함"이 제3 교란변수로 진단 오염.
- **불변식**: opt-in off byte-identical / down-only 천장(`final≤L1`) / go-live(DRY_RUN=false·execute_trade)=사람 게이트(자율 범위 밖).

## 2. Tier 체계 (plan-test-readiness.md 재구성)
- **Tier1**(완료): 거시 신호 보강 = T1 자문+T0 실측이 짚은 거시 분류기 결함 먼저 제거. 결함 신호 위에 Test2 돌리면 손실 원인이 또 섞이므로.
- **Tier2**(다음): 원래 마스터 P0~P5 = 배선→Test2a→judge 재설계+재테스트→주식 full+재테스트→리포트.

## 3. ★Tier1 완료 내역 (M1~M5)

### M1 — 물가 신호 2D ✅ (유일 코드 변경, commit f0d1880)
- **무엇**: `core/brain/regime_classifier.py` `_inflation_signal`(203~) 이 `_momentum_z(_yoy(core,12),3)` 단독 = 물가 가속도만 → 2022 CPI 9.1% peak 가속 0 → "물가 낮음" → Recovery 오분류.
- **수정**: `_level_z(yoy, target=2.0, window=36)` helper(485~ 근처) 추가. `_inflation_signal` = level(목표 2% 대비 편차/σ, w1.0) + momentum(w0.5) + breakeven(w0.7).
- **검증**: 2022 복원(Recovery→Overheat/Stagflation, inflation_z −0.04→+1.02). 전구간 26/82 변화=다수 개선(2013-15 저물가→Recovery 정정).
- **독립 audit**(general-purpose, raw FRED 재현): **verdict 채택, hard-fail 0**. 과적합 아님(w 0.7~2.0 전부 2022 양), PIT lookahead 0. 2008-10만 경계취약(회귀 아님).
- **회귀**: regime/macro/brain 139 passed. 4 fail=`test_so3_p4_macro_vintage` ECOS credential stub(M1 직교, 메모리 E94 기존).
- **상수**=advisory prior(backtested=false) docstring 명시. ★분류기=항상on baseline이라 byte-identical 아님(출력 변경이 의도).

### M2 — stock-bond 상관 ✅ (M1 전파로 닫음, 코드 0)
- **반증 실측**(`.m2-stockbond.py`): 2x2 corr 저vol·고물가 +0.081/고vol·고물가 +0.038 → vol 같아도 물가로 부호 반대. OLS infl_high +0.439(p<1e-4) vs vol_high −0.139 = 물가가 부호 지배(자문 확증).
- **검증**(`.m2-verify.py`): M1 후 regime label별 — 고물가 −0.223 vs 저물가 −0.356, 차 +0.133(t=16.3 p=6e-58).
- **verdict**: regime-conditional glasso(`_belief_conditional_cov` regime_to_weights.py:278)가 M1 분류로 **방향 자동 학습**. 명시적 prior 미추가(점추정 박제 회피+실데이터 우월).
- **잔여**: 2022형 극단 양상관은 4분면 거칠어 약반영 → Test2 belief-cov 실효 확인 + 극단 고물가 분리=후속 후보.

### M3 — 유동성 factor ✅ (reject 이중계상, 코드 0)
- **subagent 실측**(frequency-matched): NFCI/Net Liq/M2 **전부 reject**. NFCI=MOVE/slope 패턴(univ t=−6 강유의→joint β→0 t=−0.26, credit HY OAS 흡수 monthly corr +0.62/VIF 2.51).
- ★자문 "유동성 1순위" framing 데이터가 막음. credit factor 이미 유동성 포착.
- **부수**: frequency-axis 함정 선제 차단(일별 ffill=zero-inflation spurious) / coin·NFCI weekly만 structural(coin-only·Bonferroni 미생존, 부활=repo발작 IC9) / ★credit HY OAS FRED 2023-06~만=live 커버리지 빈약(별도 인프라 이슈).
- 산출: `study-research/_factor_shadow/liq-incremental-freq.py`+json.

### M4 — slope·MOVE 재판 ✅ (폐기 확정, 코드 0)
- **subagent 실측**: ★자문 반박이 정답. slope 월/분기 forward Bonferroni 생존 0/40 + USREC probit 재현실패(TIPS-era 2003~서 yield-curve 선행력 죽음). MOVE rate-tantrum 조건부도 equity 비유의(t<1.9), "VIX 과잉통제" 주장 코드 반증(tantrum 안 MOVE↔VIX corr +0.30=redundancy).
- **verdict**: 둘 다 폐기 확정(horizon/조건 바꿔도 증분 0). rejected_provisional 유지(부활=IC9 data-event/sleeve 신설 게이트).
- 산출: `slope-regime-incremental.py`·`move-tantrum-conditional.py`+json.

### M5 — transition 모니터 ✅ (기존 방어 확인, 코드 0)
- **단일점 방어 기존 존재**: `is_disagreement()`(macro_schema.py:86, now≠forecast 전환임박) + `regime_belief_adapter` confidence 低→belief 평탄→between-dispersion inflate=자동 transition de-risk.
- **baseline**(M1 후): 분기전환 32/81=39.5%, 전환임박 13.4%. <50%=과도 불안정 아님.
- **잔여**: 39.5% 전환이 Test2서 과도 회전율 유발하는지=Test2 모니터 항목.

### ★Tier1 메타 성과
- **순 코드 변경 = M1 하나**. M2~M5는 측정·판정으로 "이미 있다/이중계상/폐기" 데이터 확정 = **무비판 추가 0**. 자문 제안 4개 중 3개를 데이터로 반박(M3 reject·M4 폐기·M2 자동).
- **2022 단일점 실패 뿌리 제거**(M1) → Test2서 2022 손실 나도 "momentum-miss"는 용의선상 제외.

## 4. ★다음 = Tier2 P1 배선 (착수점)
> progress-test-readiness.md "Tier 2" 섹션. 목표: backtest 루프가 **진짜 설계 경로**(사이징·게이트·judge)를 타게. LLM 기본 no-op.

- **W0**: 배선 방식 자문 1R(결정→사이징→게이트 연결) — `model: opus`
- **W1**: `backtest/engine.py` 루프에 `risk_sizing.size_portfolio`/`coin_sizing` 연결(고정 `capital*0.95` engine.py:250 제거) — `wf: harness2`(회귀민감)
- **W2**: `RiskGate.check()` 루프 내 호출(GatedOrderRouter 우회불가 경유) — `wf: harness2`
- **W3**: `core/assume/judge.py judge()` production 호출지점 연결(qwen/bge attenuator 기본 a=1.0 no-op, 천장 `final≤L1` 유지) — `wf: harness2`
- **W4**: 다기간 시계열 통합테스트(현 단발·mock만) — `model: sonnet`
- 이후 **P2 Test2a 실행**(결정론 경로 수익률→방법론 vs 코드 진단).
- ★코드 사실(P1 진입 전 필독): 현 `backtest/engine.py`는 risk_gate 미호출·사이즈 고정 95%·judge production 호출 0. judge()는 down-only 감쇠(qwen/bge attenuator a∈[0,1], final=L1·a2·a3≤L1). 클로드 최종결정 경로 코드에 없음(=Tier2 P3 judge 재설계 대상).

## 5. 자문 수렴 결과 (T1, ledger §7 박제됨 — 재인용용)
- 채택: 물가 level+momentum(M1✅), stock-bond 물가연동(M2✅).
- reject/폐기: 유동성 factor(M3 이중계상), slope·MOVE(M4).
- 인정(우리 강점): crypto 0차단 아님(IC9 evidence 부활)·copula 불필요(동적상관 우수)·TIPS 기반영(breakeven/real)·PIT/이중계상/다중비교=표준 이상.
- 후속 후보(ledger §7): Fed put(물가국면 파생), 극단 고물가 분리, crypto yaml prior/cap 표현 분리.

## 6. 환경·주의
- Python: `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (msys `python` 없음, 절대경로 필수).
- 임시 측정파일: `.t0*.py`/`.m2*.py`/`.consult-disguise-*.md`/`_factor_shadow/_liq_cache/` = 미커밋(필요시 참고, GC 대상).
- 커밋됨: regime_classifier(M1)·ledger·plan/progress·_factor_shadow 측정 .py/.json. **push 안 함**.
- claude-web 자문 세션 만료 상태(R2는 사용자가 직접 붙여줌). 재사용 시 `bash ~/.claude/skills/claude-web-consult/send.sh setup` 필요.

## 7. 진입 (다음 세션)
1. 이 파일 → 2. `progress-test-readiness.md`(Tier1 [x]·Tier2 체크리스트) → 3. `plan-test-readiness.md`(Tier1/Tier2 상세) → 4. `cross-regime-ledger.md` §6·§7(측정 SSOT).
- **첫 작업 = Tier2 W0**(배선 방식 자문) 또는 사용자 방향 확인. ⛔ go-live=사람 게이트.
