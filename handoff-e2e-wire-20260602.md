---
tags: [handoff, inv, wire, e2e, factor-codify, autopilot]
date: 2026-06-02
session: btn-Inv
updated: 2026-06-02 (★e2e capstone + JM insufficient_data fix 완료 = §6 자율작업 2개 닫힘. commit 4658def/5cf8bb0. 다음=inflation_z 관찰 §6-(3))
---

# 핸드오프 — study→runtime wire e2e 통합 개통 (자기완결, /clear 후 이 파일만 읽고 재개)

> **이 파일 하나로 재개 가능하게 작성됨.** 순서: 이 파일 전체 → 필요 시 `progress-wire-impl.md`(Phase X-2/Y) → `study-research/_wire/cross-regime-ledger.md`(factor/cross verdict).

---

## 0. 환경 · 자율 범위 · 불변식 (먼저 읽기)

- **python**: `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + 환경변수 `PYTHONUTF8=1`. (`python` PATH 아님, 절대경로 필수)
- **FRED 키**: `.env`(`FRED_API_KEY`). `from dotenv import load_dotenv; load_dotenv("D:/projects/Inv/.env")` 후 `RealFredAdapter()` 자동 사용. heredoc 에서 `load_dotenv()` 인자 없으면 `find_dotenv` frame 에러 → **임시 .py 파일 + 명시 경로** 로 실행.
- **자율주행 ON**: flag `agent/.secretary/.autopilot-btn-Inv.flag`, long-mode ON(ctx cap 500k). 사용자 부재.
- ★**자율 범위 = Phase V(10년 백테스트) 게이트 전까지 전부**. 측정·audit·codify·wire 모두 자율.
- ⛔ **게이트(자율 밖)**: (1) **go-live** = `judge` 실 사이징 소비 · `execute_trade` 실주문 (2) **Phase V** = 10년 백테스트(사용자 방향 논의 선행).
- ⛔ **push 금지** (local commit 만).
- ★**불변식**: opt-in `INV_R15_WEIGHTS` **off → byte-identical**(무회귀). SACRED = execute_trade/DRY_RUN 비접촉. 슬리브 신설(reit/eq_intl/xle) 폐기(no new allocation sleeve). codify 는 15축 audit verdict 확정 후만.

---

## 1. 시스템 1분 요약

KRW 멀티에셋 자율배분. **배분 corr_prior = factor-implied covariance** Σ=B·Λ·Bᵀ + diag(idio) → cov2corr(**magnitude FREEZE**=상대 비율만). 전체 파이프라인:

```
거시지표 PIT fetch(fred_adapter) → RegimeClassifier(Investment Clock 4국면 + JumpModel stress/calm)
  → build_sleeve_regime_ids(시점별 regime substrate) → RegimeGlasso.fit(regime-conditional graphical lasso)
  → corr_prior(SEED β + static Λ) → belief-mix Σ_eff → BlackLitterman → max-Sharpe weights → (게이트) judge → execute_trade
```

opt-in(`INV_R15_WEIGHTS=true`) 일 때만 corr_prior/Σ_eff 활성. off=RegimeGlasso np.eye(byte-identical).

---

## 2. 이번 세션 완료 (누적, 전부 검증·version 기록)

| # | 항목 | 결과 | version |
|---|---|---|---|
| Y1 | fred_adapter first_release vintage fix | `_MARKET_PRICED_DAILY`+`_FIRST_RELEASE_BROKEN`→`_LATEST_FALLBACK` latest 직행. breakeven/curve/real/nfci 복구. PIT as_of mask 안전 | — |
| Y2 | NFCI/STLFSI4 stale fix | first_release 1976/2004 stale → latest. ★백테스트 vintage=Phase V TODO(NFCI revision mean 0.35) | — |
| Y3 | jumpmodels 0.1.1 설치 | requirements 등재. jm import OK | — |
| Y4 | corr_prior connectivity | coin_track_macro 가 substrate(fetch_sleeve_returns IC0 + build_sleeve_regime_ids IC0-R) 이미 배선. belief+ids+returns 3-AND → `_belief_conditional_cov(Σ_eff)` 발동 YES | — |
| Y4b | build 효율화 | `build_sleeve_regime_ids(monthly=True)` 월 최종거래일만 classify + PIT-safe ffill | — |
| **Y5** | **factor codify** | **아래 §3 상세** | **v1.36.0** |
| ★ | **weights 관찰 해소** | **아래 §4 상세** (배선 LIVE 확정) | — |
| ★ | **fetch 캐시** | `fred_adapter.get_series` raw(pre-mask) instance 캐시. build_sleeve_regime_ids **255s→29.2s(8.7x)**. PIT 보존(as_of mask 매 호출 fresh) | **v1.36.1** |

- **현 실 거시 국면**(Y1~Y2 반영): **STAGFLATION** growth_z −0.429 / inflation_z 0.548(breakeven 반영 후) / conf 0.45. fetch 캐시 후 실 regime-ids unique=[Reflation, Stagflation] 2종 검출.

---

## 3. ★Y5 factor codify 상세 (v1.36.0, 가장 큰 변경 — 새 세션 반드시 숙지)

### 무엇을 했나
- **FACTORS 6→7**: `("real", "dollar", "oil", "credit", "vol", "breakeven", "fx")`.
- rate(DGS10 명목)→**real(DFII10) 교체**(명목·실질 corr 0.914 공선, real=gold driver 경제적 정합) + **breakeven(T5YIE) 추가**(commod) + ★**MOVE/slope DROP**.

### 왜 MOVE/slope 를 뺐나 (★핵심 — 이 결정이 audit 을 뒤집음)
- P2 독립 audit(a8f746b2)이 MOVE/real/breakeven/slope 4축 adopted 판정. 헤드라인 β(MOVE us −0.213/slope commod +0.119)는 **univariate**였음.
- 통일 8-factor **joint multivariate** 재측정(`study-research/_factor_shadow/batch-std-beta-9factor.py/.json`, n≈5000, 2006~2026, MAX VIF 1.26 무공선) 결과: **MOVE/slope β→0 붕괴**(VIX 동시통제 시 risk-off 분산 완전 흡수). real만 joint 안정(gold −0.233=명목 rate −0.2155 재현), breakeven commod +0.117(t=3.1 structural 생존, univariate +0.33→약화).
- factor 공분산 prior B·Λ·Bᵀ 는 **joint β 가 정합**(B=Cov·Λ⁻¹). univariate 박으면 VIX 와 **이중계상**(L축 불변식 위반). univariate inflation (1+3ρ²)는 sleeve별로 달라 magnitude FREEZE/cov2corr 로도 못 씻음.
- **외부 자문 2모델(gemini/claude) 만장일치** Option A(drop). brief=`.consult-y5-jointbeta-briefing.md`.
- **re-scope framing**(번복 아님): audit verdict = marginal association(유효, ledger §6 보존) / covariance-incremental = rejected(VIX 조건부 redundant). FWL: joint β=MOVE⊥ 잔차계수, VIF 1.26→MOVE⊥ 분산 79% 보존=진짜 partialling(spec artifact 아님). **채택 게이트 업그레이드 권고**: covariance-prior factor 는 univariate screen 만으로 부족 → joint incremental 통과 필수.

### ⚠️ MOVE/slope 부활 트리거 (IC9 대상, rejected→revival)
- bond sleeve 가 corr_prior 소비 대상 편입(현 eye 독립) → MOVE=채권 IV 로 bond 전용 vol factor 가치 (option C).
- regime-conditional 분리(2022 rate-stress vs 2020 equity-stress 에서 MOVE↔VIX 결합 국면의존).
- 현 corr_prior 3 sleeve(us_stock/commodity/gold)=VIX-dominated 라 full-sample drop.

### 검증
- self-test PASS(gold decoupling Δ0.02 보존·reject β:=0 lock·idio conservation). corr_prior 7×7 PSD 발동, **off byte-identical(None)**. golden us×commodity 0.2951→**0.2880**/us×gold 0.249→**0.2721**.
- 회귀: 도메인(factor/study/regime/sleeve/portfolio/brain/fred) **273 passed 0 fail**. 전체 스위트 38 fail = ★test pollution(격리 63 passed) + working-tree-clean(미커밋 변경) + golden-meta 집계, **factor import 0=Y5 직교 확정**(task-discipline-c 3증거).

### 파일
- `core/study/factor_betas_seed.py` — FACTORS·SEED_CELLS(joint β 전면 교체)·self-test.
- `core/data/factor_returns.py` — FACTOR_SERIES(real=DFII10, +breakeven=T5YIE).
- `core/study/factor_cov_estimate.py` — FACTOR_TRANSFORM(real/breakeven=diff).
- `tests/test_sleeve_belief_cov.py` — golden(0.2880/0.2721) + Y4b monthly 회귀(`{-1,1,2}` 허용).
- `study-research/_wire/cross-regime-ledger.md §6 + §6-Y5 reconcile` — verdict + re-scope 박제.

---

## 4. ★weights 관찰 해소 (배선 LIVE 확정 — 중요)

이전 핸드오프 우려 "corr_prior 발동해도 weights≈BL prior(안 바뀜)" → **버그 아님**.
- mechanism live test(`.tmp-y5-weights-mech.py`): **stance 비움** 시 belief×regime·cov(0.1↔0.8) 극단 변화에도 weights **L1 Δ=0** = **BL reverse-optimization 항등식**(view 없으면 π=δ·Σ·w_prior 로 cov 상쇄=cov-invariant, 수학적 정상).
- **stance 포함**(us+0.6/gold−0.4/coin+0.3) 시 belief calm↔crisis 가 weights **L1 Δ=0.136** 이동(coin 0.305→0.246·commodity 0.008→0.048) → ★**배선 LIVE**.
- **함의**: corr_prior/Σ_eff(+Y5 factor 전체)는 **macro view(stance) 있을 때만** 배분에 작용(중립 macro=IC prior 유지=의도된 BL 설계). us_stock/gold/cash 는 bound(0.5cap/0.0floor) 라 불변, 비제약 sleeve(coin/commod/kr/bond)가 반응.
- ★e2e 테스트·weights 검증 시 반드시 **stance 있는 macro_view** 사용(없으면 cov 효과 0 으로 오인).

---

## 5. 핵심 아키텍처 맵 (코드 진입점)

### corr_prior 2경로 (`core/brain/regime_to_weights.py`)
1. **`_ic_corr_prior(cols, as_of, fx_hedge)` :228** — static SEED β → `factor_implied_cross_cov`(static Λ) → **W roll-up**(SLEEVE_AGG, cov 공간) → cov2corr. opt-in off→None(eye).
2. **`_belief_conditional_cov(returns, ids, belief, labels)` :278** — RegimeGlasso.fit(X, regime_ids, corr_prior=①) → effective_precision(belief-mix) → Σ_eff → BL `_bl_returns_path` cov_override.

### SLEEVE_AGG (`:172`) — ★측정 unit ↔ runtime sleeve 분리
- **runtime sleeve 7**: us_stock/kr_stock/commodity/gold/bond/cash/coin.
- **SEED 측정 unit 6**: gold/eq_us_cyclical/eq_intl/reit/commodity/eq_us_defensive.
- 매핑: `us_stock←{cyclical 0.5, defensive 0.5}`, `commodity←commodity`, `gold←gold`. **kr_stock/bond/cash/coin=eye 독립** / eq_intl·reit=drop(R10).
- ⟹ corr_prior 는 us_stock/commodity/gold 3 sleeve 만 영향. (그래서 MOVE 의 bond-IV 가치가 corr_prior 에 안 닿음 = drop 정당성 일부.)

### FACTORS 7 + SEED tier (`core/study/factor_betas_seed.py`)
- tier: validated(w 그대로)/structural(w≤0.25 강수축)/reject(β:=0 lock)/hold(pool)/denomination(fx 구조값).
- ★**gold vol β:=0 lock**(§3 audit, decoupling 방어). ★**real=gold only**(equity OOS sign-flip→reject). ★**fx=denomination +1.0**(James-Stein 우회, fx_hedge="full"→0).
- Λ: `_static_factor_lambda` :183 — FRED Λ fetch 실패(거의 항상) → eye fallback + **Λfx=0.15**(자문+falsification 확정).

### substrate 배선 (`core/coin_track_macro.py:53 collect_market_state`)
- `is_r15_enabled()` → fetch_sleeve_returns → RegimeClassifier(RealFredAdapter()) → build_sleeve_regime_ids → allocate(macro_view, returns, sleeve_regime_ids). **이미 e2e 배선됨**.

---

## 6. 다음 작업 (자율 진행, 우선순위 순)

### (1) 최종 e2e 통합 테스트 ✅완료(2026-06-02, v1.36.2, commit 4658def)
- 진입점 `collect_market_state`(coin_track_macro) capstone — `tests/test_e2e_collect_market_state_r15_wire.py` **3 passed**. **on**→substrate(returns+macro_view+sleeve_regime_ids 2국면) **allocate 실연결** + `belief_conditional_cov` 발동 + macro_weights 합=1. **off**→fetch 0회 정적(None) 경로 + r15_belief 미산출(무회귀). **graceful**→classify 예외 시 정적 fallback. 합성 patch(fetch_sleeve_returns·RegimeClassifier·RealFredAdapter) + CoinTrack override 4종 격리. orchestrator.allocate 내부=test_sleeve_belief_cov.py 분담.

### (2) jm 시계열 경로 ✅완료(2026-06-02, v1.36.3, commit 5cf8bb0)
- **근본원인(실측)**: `_build_jm_matrix` 빈도 불일치 — 월별 yoy(매월 1일)·resample ME diff(월말)·breakeven 일별 yoy(diff_list 누락→일별) 세 빈도 혼합 → `DataFrame(cols).dropna()` inner-join 교집합 ≈ 0 → X 0행 → **단발/시계열 무관 *항상* insufficient_data**(핸드오프 "단발만" framing 부정확).
- **fix**: 모든 시리즈 `ME.last()` 월말 통일 후 변환 + breakeven_5y diff_names 편입 + 변환후 60mo 미만(hy_oas 35mo) 컬럼 제외. 실측: X **(278,8)**, jm_status **insufficient_data→ok**, jm_state=calm. 회귀 242 passed + 신규 `tests/test_jm_matrix_freq_align.py` 3 passed.

### (3) ✅inflation_z 관찰 종결(2026-06-02, 코드 회귀 아님 = 데이터 변화 확정)
- classify infl_z **1.154** 분해 실측: core_cpi momentum_z(w3) **1.0896**(=핸드오프 "이전 core CPI 단독 1.09"와 일치, CPI yoy 2.67→**3.0** 반등) + breakeven_5y diff z(w12) **1.2465**(기대인플레 2.54 상승) → 가중평균(1.0/0.7) 1.154. **핸드오프 0.548**은 그 시점 breakeven diff z 가 낮아 평균을 끌어내린 측정 컨텍스트 — 지금은 breakeven 상승으로 둘 다 양. `_inflation_signal` 미접촉(diff 확정) + 현 거시(CPI 3.0/breakeven 2.54=인플레 가속)에 정합 → **STAGFLATION 판정 신뢰**. 코드 회귀 아님 종결.
- ✅부수 검토 종결(실측, 노이즈 가설 기각): breakeven 일별 12일 z vs 월별 12개월 z 36mo 비교 — 일별 std=0.714/부호전환 13 vs 월별 std=0.871/부호전환 19 → **일별이 오히려 안정적**(표본↑). JM 빈도버그(인덱스 0행)와 달리 작동 정상 + 설계 의도(일별 시장 선행성)대로. `_inflation_signal` breakeven z **현 설계 유지 정당**, 변경 불요.

---

## 7. 기각·주의 사항 (재탐구·재실수 방지)

- **MOVE/slope**: joint mv 무효로 DROP. 부활 트리거=§3 ⚠️. univariate β 박제 금지(이중계상).
- **weights ≈ BL prior**: 버그 아님(BL reverse-opt 항등식). stance 없으면 cov-invariant 정상(§4).
- **gold vol β:=0 lock**: §3 audit(p=0.077 비유의), decoupling 방어. 풀지 말 것.
- **real = gold only**: equity real 은 in-sample 유의해도 OOS sign-flip → reject.
- **test pollution**: 전체 `pytest tests/` -k 광역 실행 시 38 fail(so3/so4/so5/so6/so7) = FRED_API_KEY 환경 누수 + working-tree-clean(미커밋) + golden-meta. **격리 실행하면 통과**(63 passed). 도메인 회귀는 `-k "factor or study or regime or sleeve or belief or portfolio or brain or fred"` 로 확인(273 passed).
- **백테스트 vintage**: NFCI/STLFSI4 latest fallback 은 실시간 PIT 안전하나 백테스트 revision(NFCI mean 0.35)은 미반영 → **Phase V TODO**.
- **credit 측정 불일치**(pre-existing, Y5 무관): FACTOR_SERIES credit=BAMLH0A0HYM2(HY OAS) vs SEED β 측정=BAA10Y-AAA10Y. Λ 경로 eye fallback 이라 미사용. 건드리지 말 것.

---

## 8. 검증 명령어 모음

```bash
PY="C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
# self-test
PYTHONUTF8=1 $PY -m core.study.factor_betas_seed
PYTHONUTF8=1 $PY -m core.data.factor_returns
# 도메인 회귀(0 fail 기대)
PYTHONUTF8=1 $PY -m pytest tests/ -q -k "factor or study or regime or sleeve or belief or portfolio or brain or fred"
# corr_prior on/off + fx_hedge (재현)
PYTHONUTF8=1 $PY .tmp-y5-verify.py
# weights mechanism live (stance 효과)
PYTHONUTF8=1 $PY .tmp-y5-weights-mech.py
# fetch 캐시 PIT+속도
PYTHONUTF8=1 $PY .tmp-y5-cache-verify.py
# 9-factor 재측정(필요 시)
PYTHONUTF8=1 $PY study-research/_factor_shadow/batch-std-beta-9factor.py
```

---

## 9. 파일·문서 인덱스

- **진입**: 이 파일 → `progress-wire-impl.md`(Phase X-2/Phase Y, Y5/weights/캐시 체크박스) → `MEMORY.md` ckpt-202606021545.
- **코드(이번 변경)**: `core/study/factor_betas_seed.py`·`core/data/factor_returns.py`·`core/study/factor_cov_estimate.py`·`core/brain/fred_adapter.py`(캐시)·`tests/test_sleeve_belief_cov.py`.
- **아키텍처 read 지점**: `core/brain/regime_to_weights.py`(_ic_corr_prior:228·_belief_conditional_cov:278·SLEEVE_AGG:172·_static_factor_lambda:183)·`core/portfolio_orchestrator.py:113`·`core/coin_track_macro.py:53`·`core/brain/regime_history.py`(build_sleeve_regime_ids).
- **ledger/근거**: `study-research/_wire/cross-regime-ledger.md`(§6 factor verdict + §6-Y5 reconcile)·`15axis-summary.md`·`AUDIT-GUIDE.md`(15축).
- **측정 산출**: `study-research/_factor_shadow/batch-std-beta-9factor.{py,json}`(Y5)·`batch-std-beta-5sleeve.{py,json}`(이전 5f).
- **자문**: `.consult-y5-jointbeta-briefing.md`(joint vs univariate, 2모델 만장일치 응답은 turn 로그).
- **.tmp 검증(재사용 가능)**: `.tmp-y5-verify.py`·`.tmp-y5-weights-mech.py`·`.tmp-y5-cache-verify.py`·`.tmp-y5-gen-seed.py`(SEED 생성 헬퍼)·`.tmp-y5-probe.py`(데이터 가용성). 이전: `.tmp-y4b-verify.py` 등.
- **version 이력**: v1.36.0(Y5 codify)·v1.36.1(fetch 캐시). `python scripts/version_manager.py history`.
