---
tags: [progress, inv, test-readiness, master]
date: 2026-06-02
session: btn-Inv
plan: plan-test-readiness.md
---

# Progress — 수익률 테스트 준비 마스터

> plan = `plan-test-readiness.md`. 각 step = `model:` 또는 `wf:` 정확히 하나.
> 자율 범위 = Tier1(M1~M5) + Tier2(P0~P5). ⛔ go-live = 사람 게이트.
> ★2026-06-02 재구성: T1 자문 수렴 → 거시 신호 보강 = **Tier 1(최우선)**. 기존 P0~P5 = Tier 2 강등.

## Tier 1 — 거시 신호 보강 (자문 수렴, 최우선)

- [x] **M1** 물가 신호 2D(level×momentum) — `model: opus` ✅ 완료 (2026-06-02)
  - 구현: `_level_z(yoy, target=2.0, window=36)` helper 추가 + `_inflation_signal` level(w1.0)+mom(w0.5)+bei(w0.7)
  - ★2022 복원: Recovery→Overheat/Stagflation (inflation_z −0.04→+1.02 @CPI9.1% peak). forecaster도 개선
  - 전구간 26/82 변화 = 다수 개선(2013-15 저물가→Recovery 정정, 2011 momentum 잡음 교정)
  - ★독립 audit(general-purpose af651d4c, raw FRED 재현): **verdict=(a) 그대로 채택, hard-fail 0**.
    과적합 아님(w 0.7~2.0 전부 2022 양 일관), PIT lookahead 0, 2008-10만 경계취약(회귀 아님)
  - 회귀 확인: regime/macro/brain 139 passed. 4 fail=test_so3_p4_macro_vintage ECOS credential stub
    (M1 직교, 메모리 E94 기존 확인). M1 관련 회귀 0
  - 상수=advisory prior(backtested=false) docstring 명시. byte-identical 아님(분류기=항상on baseline, 변경 의도됨)
- [x] **M2** stock-bond 상관 물가국면 연동 — `model: opus` ✅ 완료 (2026-06-02, M1 전파로 닫음)
  - 반증(`​.m2-stockbond.py`): 2x2 corr 저vol·고물가 +0.081/고vol·고물가 +0.038 (vol 같아도 물가로 부호 반대).
    OLS infl_high +0.439(p<1e-4) vs vol_high −0.139 = 물가가 부호 지배(자문 확증)
  - 검증(`​.m2-verify.py`): M1 후 regime label별 — 고물가 −0.223 vs 저물가 −0.356, 차 +0.133(t=16.3, p=6e-58)
  - ★verdict: **방향성 M1 자동 전파**(glasso regime-conditional). 명시적 prior 미추가(점추정 박제 회피+실데이터 우월)
  - 잔여: 2022형 극단 양상관은 4분면 거칠어 약반영 → Test 2 belief-cov 실효 확인 + 극단 고물가 분리=후속 후보
  - 회귀 확인: 코드 변경 0(메커니즘 기존) = byte-identical 유지 → 직교
- [x] **M3** 유동성 factor 탐색 — `model: opus` + 15축 subagent ✅ 완료 (2026-06-02)
  - subagent(ac7f54aa, frequency-matched): **3후보 전부 reject**. NFCI=MOVE/slope 패턴(univ t=−6 강유의→
    joint β→0 t=−0.26, credit HY OAS가 흡수 monthly corr +0.62/VIF 2.51). Net Liq/M2=joint 노이즈
  - ★자문 "유동성 1순위" framing을 데이터가 막음(무비판 차단). credit factor 이미 유동성 포착
  - 부수: frequency-axis 함정 선제 차단(일별 ffill=zero-inflation spurious) / coin·NFCI weekly만 structural
    (coin-only·Bonferroni 미생존, factor 미추가, 부활=repo발작 IC9) / ★credit HY OAS FRED 2023-06~만=live 커버리지 빈약(별도 인프라)
  - 산출: `study-research/_factor_shadow/liq-incremental-freq.py`+`.json`. ledger §7 M3=rejected_provisional 갱신
  - 회귀 확인: factor 미추가=코드 변경 0 → 직교. adopt 아니라 별도 audit 불요(subagent raw+LOO+Bonferroni=독립검증)
- [x] **M4** 폐기 신호 재판(slope·MOVE) — `model: opus` + subagent ✅ 완료 (2026-06-02, 둘 다 폐기 확정)
  - subagent(aae420cf): ★자문 반박이 정답. slope 월/분기 forward Bonferroni 생존 0/40 + USREC probit 재현실패
    (TIPS-era 2003~서 yield-curve 선행력 죽음). MOVE rate-tantrum 조건부도 equity 비유의(t<1.9),
    "VIX 과잉통제" 주장 코드 반증(tantrum 안 MOVE↔VIX corr +0.30=redundancy)
  - verdict: 둘 다 폐기 확정(horizon/조건 바꿔도 증분 0). rejected_provisional 유지(부활=IC9/sleeve 게이트)
  - 산출: `_factor_shadow/slope-regime-incremental.py`·`move-tantrum-conditional.py`+json. ledger §6/§7 갱신
  - 회귀 확인: factor 미추가=코드 변경 0 → 직교. Bonferroni 생존 0=폐기 verdict(통과편향 배제)
- [x] **M5** 레짐 transition 안정성 모니터 — `model: opus` ✅ 완료 (2026-06-02, 기존 방어 확인+baseline)
  - ★단일점 방어 기존 존재: `is_disagreement()`(now≠forecast 전환임박) + `regime_belief_adapter`
    confidence 低→belief 평탄→between-dispersion inflate=자동 transition de-risk(수학이 위험 축소)
  - baseline(M1 후): 분기전환 32/81=39.5%, 전환임박 13.4%. <50%=과도 불안정 아님, confidence가 경계 흡수
  - 별도 모니터 코드 추가=observability/go-live 단계(현 over-engineering) → baseline 기록으로 닫음
  - 잔여: 39.5% 전환이 Test 2서 과도 회전율 유발하는지 = Test 2 모니터 항목
  - 회귀 확인: 코드 변경 0(기존 메커니즘) → 직교

## Tier 2 — 기존 마스터 (P0~P5, Tier 1 후 진입)

## Phase P0 — 방법론 검증 (즉시·병렬)

- [x] **T0** 거시 과거 설명력 — `model: opus` ✅ 완료 (2026-06-02)
  - 산출: `.t0-regime-explain.py`(now 타임라인 82분기) + `.t0b-forecaster.py`(forecaster+z 실측)
  - **강점**: IC 4분면 이론 정합(침체=Reflation), GFC/COVID/2021전환 변곡점 포착, 분포 균형
  - ★**약점 확정(데이터)**: `inflation_z=_momentum_z(yoy,3)` = 인플레 momentum 기반 → 2022 CPI 9.1% peak에
    inflation_z≈0(가속 멈춤=낮음으로 오독) → Recovery 오분류. forecaster도 동일 miss(level 못 고침).
  - ★**Test 2 진단 가설**: 2022 구간 손실 시 "momentum-miss(방법론 선택)" 1순위 용의자 = 방법론 vs 코드 분리 첫 사례
  - caveat: vintage 미반영(latest-fallback) 낙관편향 / regime_now=동행후행 혼합(predictive=forecaster)
  - 후속 후보: indicator-ledger에 인플레 level 지표 candidate 대조(무비판 추가 금지) → T1 자문 질문화
  - 회귀 확인: 읽기 전용 분석, 코드 미변경 → 직교
- [x] **T1** 둔갑 자문 — `model: opus` ✅ 완료 (2026-06-02, gemini 2R + claude 2R 수렴)
  - 자료: `.consult-disguise-R1.md`/`R2.md`(CIO 페르소나, 코드어 0)
  - 수렴: 물가 level+momentum(3중확인)·stock-bond 부호=물가국면(vol은 크기)·slope/bondvol horizon 분리·
    유동성 1순위(Net Liq/NFCI)·copula 불필요(stock-bond 예외)·crypto 베이지안 건전(코드 evidence 기반 확인)
  - 인정: PIT/이중계상/다중비교 = 표준 이상. TIPS는 대부분 기반영(breakeven_5y·real DFII10)
  - ★단일점 실패 경고: 물가 국면 1변수가 3곳 전파 = T0 2022 miss와 일치 → Tier 1 M1~M5로 codify
  - 반영: 위 수렴 → **Tier 1(M1~M5)** 신설(사용자 승인 1). 구현은 Tier 1에서

## Phase P1 — Test 2 선결 배선 (결정론, LLM no-op)

- [ ] **W0** 배선 방식 자문 1R (결정→사이징→게이트 연결) — `model: opus`
- [ ] **W1** engine 사이징 연결 (고정 95% 제거) — `wf: harness2` (회귀민감·코어 결정경로)
- [ ] **W2** risk_gate 루프 내 호출 — `wf: harness2`
- [ ] **W3** judge() production 호출지점 (결정론 no-op) — `wf: harness2`
- [ ] **W4** 다기간 시계열 통합테스트 — `model: sonnet` (테스트 작성)

## Phase P2 — Test 2a 실행 (결정론)

- [ ] **P2** 시계열 주입 거래 시뮬 → 수익률/MDD → 방법론 vs 코드 진단 — `model: opus`

## Phase P3 — judge 재설계 + 재테스트 (별건, 후속)

- [ ] **J1** judge 재설계 자문 3R (down-only 완화 분기) — `model: opus`
- [ ] **J2** 구현 (트리거 wire + 클로드 경로 + 증폭 가드) — `wf: harness2`
- [ ] **J3** Test 2b 재테스트 (결정론 baseline 대비 증분) — `model: opus`

## Phase P4 — 주식 full build + 재테스트 (별건, 후속)

- [ ] **S1** 주식 레이어 자문 3R (일반론 vs 우리 + 거시 공유) — `model: opus`
- [ ] **S2** DART/EDGAR + heavy-agent + 거시 wire + study — `wf: coding`
- [ ] **S3** Test 2c 재테스트 (코인+주식 통합) — `model: opus`

## Phase P5 — 리포트 통합 (별건, 최후)

- [ ] **R1** 자문 3R (가설→가점→falsify 회수) — `model: opus`
- [ ] **R2** 구현 — `wf: coding`
- [ ] **R3** 재테스트 — `model: opus`

---

## 진행 로그

- 2026-06-02 btn-Inv: plan/progress 작성. 코드 실태 확인(subagent 4건) — judge=down-only 감쇠/claude dead path,
  Test 2 배선 미완(사이즈 고정·게이트 미호출·judge 미연결), 주식 BACKTEST=ABSTAIN·DART/EDGAR stub, 리포트 0%.
  다음 착수 = P0(T0/T1 병렬).
