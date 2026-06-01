---
tags: [handoff, inv, wire, ic8, fx, graduation, audit]
date: 2026-06-02
session: btn-Inv
---

# 핸드오프 — IC8 FX denomination + IC4 graduation 완료 / fx 정밀화 잔여

> 진입: 이 파일 → `progress-wire-impl.md` IC8·IC4 섹션 → MEMORY.md ckpt-202606020900.
> python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1`.
> ⛔ push 금지(로컬 commit만). SACRED(DRY_RUN·execute_trade) 비접촉. opt-in off=byte-identical.

## 0. 이번 세션 완료 (commit 3개, push 안 함)
- **995c5e7** feat(wire): study→runtime 배선 IC0~IC10/IC9/IC8(A) + factor/stock 인프라 누적 75파일.
- **e9052eb** feat(wire): IC4 graduation 루프(candidate→adopted 5-AND, IC9 대칭).
- **fc112e5** refactor(wire): IC8 fx denomination A→B 전환.

### IC8 — FX 6th factor (denomination) ✅ B 채택
- **설계**: 한국(KRW base) 투자자가 USD-표시 자산(미국주식/금/원자재/리츠) 보유 시 공통 원/달러 환노출을 배분 공분산에 반영. fx를 6번째 factor로 추가.
- **코드**: `FACTORS=("rate","dollar","oil","credit","vol","fx")` (`factor_betas_seed.py:42`). `TIER_DENOMINATION`(James-Stein 수축 우회=구조값 보존). SEED_CELLS fx 셀 전부 `fx_β=+1.0`(절대 denomination, gold 포함 full). `build_seed_betas(fx_hedge="none"|"full")` — full이면 전 fx_β:=0. `factor_returns.FACTOR_SERIES +fx=DEXKOUS`(FRED USDKRW), `factor_cov_estimate.FACTOR_TRANSFORM +fx=dlog`. `_static_factor_lambda` eye fallback에서 fx 대각만 Λfx=0.09 축소(`regime_to_weights.py`). `_ic_corr_prior(fx_hedge=)` param.
- **A→B 전환 경위**: 최초 A안(fx_β=+0.30 measured 대역 정규화). 외부 자문 2모델(gemini-web/claude-web) **A 만장일치 기각**(denomination=추정 β 아닌 정확히 1.0 결정론 값). 코드검증=A/B는 corr_prior에서 `fx_β²·Λfx` 곱 등가(magnitude FREEZE cov2corr)라 차이는 실 Λ 경로뿐 → B(절대 1.0 + Λfx 축소) 채택. ★Claude "gold는 fx와 직교라 decoupling 안 깸"은 코드 반증(gold×cyclical 0.0637→0.1177 동조↑).
- **수치**: golden us_stock×commodity 0.2642 불변(USD 곱 1.0²·0.09 = A 0.30²·1.0 등가), us_stock×gold 0.1298→0.1994(gold full=KRW 환노출 현실), fx_hedge=full→IC10 0.0832 정확 복원. PSD min eig 0.69(none)/0.73(full).

### IC4 — graduation 루프 ✅ 통과
- `core/assume/graduation.py` 신규: `evaluate_graduation`(5-AND `assumption_stats.hysteresis_and_gate` 재사용 + StudyRegister 자가승격 가드 proposer==self_owner 차단) + `graduation_sweep`(사이클 경계 idempotent) + `make_ratify_events`. `event_ledger` CANDIDATE_PROPOSED→candidate/RATIFIED→ratified projection + `assumption_status` as-of. IC9 reject 복귀와 대칭.
- ★go-live wire 시 사이클 경계 호출자가 **self_owner 반드시 주입**해야 자가승격 방어 작동(graduation_sweep self_owner 옵션이라 누락 시 우회). 호출처 0=go-live 격리(의도).

### 독립 audit (general-purpose ab639df27606, 2026-06-02)
- **IC8 조건부통과** / **IC4 통과**. 전체 회귀 4435 passed / 36 failed(전부 KIS broker so5·so6·golden so7 기존 baseline, IC8/IC4 무관).
- ★audit 핵심 발견(main 자평 정정): eye-fallback(Λfx=0.09)에서 fx가 gold×cyclical 공분산의 **70.5% 지배**(+0.128 중 +0.090). main이 "dollar/vol 열 보존, fx는 별 레이어"라 한 건 부정확 — fx가 모든 USD sleeve에 +0.09 균일 floor를 까는 **새 지배 공통인자**. 배분 비정상은 아님(corr<0.3), fx_hedge=full 복원 가능.

## 1. ★fx 정밀화 잔여 (다음 세션 핵심 — 실측 + 표준 정합)

### 1-A. 문제 (근거 확보 현황)
- **fx_β=1.0 = 근거 확보됨**(결정론 denomination, 회계 정의 — 추정 아님).
- **Λfx=0.09 = 근거 미확보(추정)**. 현재 "(USDKRW dlog std / 자산 dlog std)² ≈ 0.3²" 어림 박제(`regime_to_weights.py` `_static_factor_lambda` eye fallback 주석). 실 USDKRW·자산 변동성 측정 안 함. ★이 값이 fx 지배도(70.5%)를 정하는 유일 손잡이.
- **더 깊은 단위 불일치(audit 지적)**: macro factor β는 **표준화 회귀**(z-score, factor var≈1 내부 정합)인데 fx_β=1.0은 **비표준화 구조값**. 같은 Λ=eye에 넣는 스케일이 안 맞음. Λfx=0.09는 그 단위를 맞추는 calibration 상수 — 단순 변동성 비율 이상의 정합 설계 필요.

### 1-B. 다음 세션 태스크 (정밀)
1. **실측 ①** — DEXKOUS(USDKRW) dlog 실변동성 + 배분 자산(SPY/sleeve_returns) dlog 변동성 측정. 기존 `core/data/factor_returns._default_fred_source`(DEXKOUS fetch 경로 이미 존재) 또는 yfinance. FRED 키 유무 확인 선행.
2. **표준 정합 설계** — macro factor가 표준화(var≈1) 공간이면 fx도 동일 공간으로. 2안 중 택:
   - (가) fx_β를 표준화 denomination(자산별 σ_fx/σ_asset)으로 → 단 A안(자문 기각)으로 회귀 위험.
   - (나) fx_β=1.0 유지 + Λfx = Var(USDKRW dlog)를 표준화 macro 스케일로 정규화한 값(실측 비율). ★권장 방향(B 유지하며 Λfx만 실측 근거화).
   - (다) corr_prior 전체를 표준화 공간 재정식(전 factor 동일 단위) — 가장 깨끗하나 IC1~IC10 영향 큼(회귀 위험).
3. **검증 ②** — 실 FRED Λ 경로(`fetch_factor_cov` 6 factor)에서 fx 기여가 실제 얼마인지 측정 → eye fallback 0.09 / 70.5% 지배가 실 Λ에서도 타당한지(audit 보완점 b). FRED 키 있으면 `_static_factor_lambda`가 실 Λ 자동 사용.
4. **fx 지배도 판정** — 실측 Λfx에서 fx가 USD sleeve corr의 몇 %를 차지하는지. 70%가 과하면(KRW 환노출 현실 대비) Λfx 보수 조정 or 표준 정합 재설계.
5. **반영** — `_static_factor_lambda` Λfx 실측값 + 주석 근거 박제, golden 재측정, self-test 9 갱신, 회귀 + off byte-identical.

### 1-C. 안전판 (그때까지)
- **fx_hedge="full"이 안전 기본** — fx 끄면 IC10(us×gold 0.0832) 정확 복원. Λfx 미확보 리스크를 토글로 회피.
- 관련 파일: `regime_to_weights.py` `_static_factor_lambda`(Λfx)·`_ic_corr_prior`(fx_hedge param) / `factor_betas_seed.py` SEED fx_β·build_seed_betas / `factor_returns.py` fetch_factor_cov(실 Λ) / `tests/test_sleeve_belief_cov.py` golden.

## 2. 잔여 태스크 (Track 1 + 후속)

### Track 1 W1/W2 (자율 실질 제한적 — 사용자 방향 확인 대기였음)
- **W1 defensive VIX risk-overlay**: vix_term이 yaml에서 `family:risk` + weight_rules 미포함 → `_build_card`가 자동 L1 제외. **이미 yaml 설계로 반영**(추가 코드 불요).
- **W1 bond_cash v5**: 현행 yaml 부재(v1_carryover만, v5 감사 진행 중) → 등록 선결 미충족 = 게이트((가)관문 study 작업).
- **W2 lag_routing**: L1(weight_rules)/L2 분리가 이미 yaml 설계로 표현. 신규는 lens 주목지표 라우팅(progress "W8 후속")+judge 소비(go-live). `family=="risk"` 일괄 제외는 bond_cash duration/credit_quality(risk지만 ticker-selector) 충돌 위험.

### (가)관문 (15축 audit·small-n rigor 동반, 자율 범위 밖)
- study 3건 verdict 격상: eq_us_defensive H3 · eq_intl China credit · reit H1 WALT.
- bond_cash v5 study_session.yaml 작성.

### Track 2 / go-live (사용자 게이트)
- **judge 재설계 자문**: claude 최종결정 경로가 코드에 없음(qwen/bge=down-only 감쇠 attenuator a∈[0,1], claude 호출 트리거 0). 사용자 의도(claude 최종+qwen 트리거+거시리포트 판단+강화/약화 flag) vs 코드(결정론 L1/DCF 최종+down-only 증폭 불가) gap. 강화 허용=down-only 불변식 완화 여부가 핵심 자문 대상.
- **IC9 런타임 live wire**: reject_recovery 호출처 0=자동 격리. go-live 경계.
- **IC4 go-live wire**: graduation_sweep 사이클 경계 호출 + self_owner 주입.
- **Phase I 통합 / Phase V 10년 백테스트**: ⛔ 사용자 방향 논의 게이트(자율 금지).

## 3. 외부 자문 결과 (IC8 fx, 2026-06-02)
- 브리핑: `.consult-ic8-fx-briefing.md`(임시, gitignore). 로그: `~/.claude/.gemini-web-last.md`·`.claude-web-basic-last.md`.
- **수렴**: A(+0.30) 만장일치 기각 / gold full / fx_hedge none 기본 / 스케일 B(우리 공분산→비중 구조상).
- **미반영**: Gemini의 대안 C(corr_prior 제외, risk_gate만) — 우리 시스템은 corr_prior가 배분 비중 형성 주체라 C면 fx 공통성이 비중에 안 보임 → B 채택. C는 향후 risk_gate가 비중 재형성하는 구조로 가면 재검토 후보.

## 4. 열어본 핵심 파일 (라인 근거)
- `core/study/factor_betas_seed.py` — FACTORS:42, TIER_DENOMINATION:49, SEED fx 셀, build_seed_betas denomination 분기(~230), _factor_pool denomination 제외(~176).
- `core/brain/regime_to_weights.py` — _ic_corr_prior(~209, fx_hedge param), _static_factor_lambda(~183, eye fallback Λfx=0.09), SLEEVE_AGG(~172).
- `core/data/factor_returns.py` — FACTOR_SERIES fx=DEXKOUS(:22), fetch_factor_cov, _default_fred_source(get_series PIT).
- `core/study/factor_cov_estimate.py` — FACTOR_TRANSFORM fx=dlog(:31).
- `core/study/factor_shadow.py` — self-test Lam 6 정합(:117, dead path지만 W3 OOS 도구).
- `core/assume/graduation.py` — 신규 전체. `core/data/event_ledger.py` — RATIFIED/CANDIDATE projection(~284), assumption_status(~221).
- `tests/test_sleeve_belief_cov.py` — golden(us×commodity 0.2642·us×gold 0.1994). `tests/assume/test_graduation.py` — 11 test.
