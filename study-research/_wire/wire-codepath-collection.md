---
title: Phase I 통합 개통 — wire 코드패스 수집 (read-only)
date: 2026-06-01
scope: study 산출(yaml) → 런타임 매매결정 연결 6 wire 경로
status: 코드 미수정 (수집 md만). 실제 스니펫 + 파일:라인 + 변경안 + 불변식 보존
sacred: DRY_RUN / execute_trade / 실거래 flip = 비접촉 (go-live 게이트 = 자율 범위 밖)
invariants:
  - down-only (judge size ≤ l1_size, monotone-down)
  - belief→_macro 차단 (reflexive loop, scope→level macro=no-op)
  - opt-in off = byte-identical 무회귀 (INV_R15_WEIGHTS / INV_STUDY_LENS / INV_CORE_GATE default-off)
---

# Phase I wire 코드패스 수집

## 0. 현황 요약 (wire 전수조사 결론 — 코드 확인 완료)

| wire | 메커니즘 구현 | 런타임 호출 | 게이트 |
|---|---|---|---|
| 1. study yaml 로더 진입 | ✅ `StudyRegister` (study_register.py) | ❌ run_agents/orchestrator import 0 | INV_R15_WEIGHTS / INV_STUDY_LENS |
| 2. corr_prior 주입 | ✅ `prepare_corr_prior` + `RegimeGlasso(corr_prior=)` | ❌ 호출처 전부 `corr_prior=` 생략 → np.eye | INV_R15_WEIGHTS |
| 3. indicators 등록 | ✅ `build_indicator_matrix` + `from_study_session` | ❌ merit 지표 FRED_SERIES/panel 등록 0 | (게이트 무관, fetch 경로) |
| 4. judge lens/corr wire | ✅ `judge(lens_prompt=, weight_card=)` + `_call_qwen_with_lens` | ❌ `judge()` 런타임 호출 0 (run_agents=코인 점수제) | INV_STUDY_LENS |
| 5. 게이트 | ✅ `is_r15_enabled()` + run_agents:831 INV_CORE_GATE | 부분 (거시 chain = 로깅만) | 위 3개 + INV_CORE_GATE |
| 6. 개통 순서 | — | — | shadow→opt-in→active 점진 |

핵심: 메커니즘은 **전부 기구현 + self-test PASS**. 미연결 = **런타임 진입점에서 facade 호출이 0건**(설계상 opt-in facade, register.py docstring "둘 다 off면 검증만, production 경로 미개통").

---

## wire 1 — study yaml 로더 진입 (StudyRegister → 런타임)

### 현재 코드

**`core/study/study_register.py:107` StudyRegister 클래스 + facade 시그니처**
```python
class StudyRegister:
    def __init__(self, *, assumption_registry=None): ...

    def register(self, source, *, panel_instance_id=None, require_raw=True) -> ValidationReport:
        # G1 로드+검증 → G2 panel → G3 lens → G4 flag → (opt-in on) weight_card 등록
        ...
        if is_r15_enabled():
            card = self._build_card(s)
            if card is not None:
                self.cards[s.study_id] = card
                if self.reg is not None:
                    self.reg.register(card)
        return rep

    def prepare_judge_call(self, study_id, *, regime_id=None, refresh_tilt=True) -> dict:
        # → {weight_card, lens_prompt, regime_pi}. 둘 다 None 이면 judge 무회귀.
        ...
        return {"weight_card": card, "lens_prompt": lens_prompt, "regime_pi": None}
```

**호출 예시 (STUDY-ORCHESTRATION.md:70 + self-test 검증된 패턴)**
```python
from core.study.study_register import StudyRegister
from core.assume.registry import AssumptionRegistry

reg = AssumptionRegistry()
sr = StudyRegister(assumption_registry=reg)
sr.register("study-research/gold/study_session.yaml", require_raw=True)   # 10방 yaml 일괄
jc = sr.prepare_judge_call("gold", regime_id="overheat")  # → judge() 인자
```

### 런타임 개통 위치

런타임 진입점은 **둘**이고, study yaml 은 둘 다에서 미연결:
- `scripts/run_agents.py:831` INV_CORE_GATE 블록 — 코인 점수제 + 거시 chain (로깅만). `StudyRegister` import 0.
- `core/portfolio_orchestrator.py:120` `allocate()` — regime_to_weights wire. `StudyRegister` import 0.

★개통 = **프로세스 1회 부트스트랩**(register)을 진입점에 추가 + 결정 직전 `prepare_judge_call`/`prepare_corr_prior` 호출.

**변경안 (run_agents.py — INV_CORE_GATE 블록 내 모듈 레벨 1회 부트스트랩, 870 근처 거시 chain 안)**
```python
# wire1: study 산출 부트스트랩 (INV_R15_WEIGHTS on 시 1회). 결정 변경 없음(공급).
if os.environ.get("INV_R15_WEIGHTS", "false").lower() == "true":
    try:
        from core.study.study_register import StudyRegister
        from core.assume.registry import AssumptionRegistry
        if not hasattr(_run_agents_state, "study_reg"):     # 모듈 캐시 1회
            _sr = StudyRegister(assumption_registry=AssumptionRegistry())
            for _y in _glob.glob("study-research/*/study_session.yaml"):
                try: _sr.register(_y, require_raw=True)
                except Exception as _ye: log(f"[wire1] {_y} register skip: {_ye}")
            _run_agents_state.study_reg = _sr
        log(f"[wire1] study 등록: {_run_agents_state.study_reg.status()}")
    except Exception as _w1e:
        log(f"[wire1] study 부트스트랩 예외(무시): {_w1e}")
```

### 불변식 보존

- **opt-in off 무회귀**: `is_r15_enabled()` off → `register()` 가 검증만, `self.cards == {}`, `prepare_judge_call` 의 weight_card/lens_prompt 둘 다 None (self-test case 1, study_register.py:288-298). 부트스트랩 자체가 INV_R15_WEIGHTS 게이트 뒤 → off 면 import 도 안 됨 = byte-identical.
- **belief→_macro 차단**: register 단계는 정적 yaml 만 본다 (belief 미개입). corr 누수는 wire 2 에서 처리.
- **SACRED 비접촉**: register/status 는 순수 등록 — execute_trade/DRY_RUN 미접촉.

---

## wire 2 — corr_prior 주입 (relationships → RegimeGlasso)

### 현재 코드

**`core/structure/conditional_correlation.py:244` RegimeGlasso.__init__(corr_prior=)**
```python
def __init__(self, gamma=0.5, n0=10.0, lam_floor=0.05,
             corr_prior: Optional[np.ndarray] = None, n_grid=30,
             transform=True, min_obs=10):
    self.corr_prior = corr_prior     # Investment Clock 사전상관 (None=독립 prior I)
```
**conditional_correlation.py:260 fit() 내부 — None 일 때 np.eye 폴백**
```python
prior = self.corr_prior if self.corr_prior is not None else np.eye(p)
...
corr_hat, lam = eb_shrink(g_corr, prior, n_eff=len(Xr), n0=self.n0, lam_floor=self.lam_floor)
```
→ `corr_prior` 형식 = **(p×p) 상관행렬** (series_ids 순서 정렬, 대각 1.0, PD). prior 미주입 시 `np.eye(p)` = study relationships 무시.

**`core/study/study_register.py:215` prepare_corr_prior facade (study relationships → 약화 corr_prior)**
```python
def prepare_corr_prior(self, study_id, base_corr_prior, series_ids, *, conservative=False):
    if not is_r15_enabled():
        return base_corr_prior                         # opt-in off = base 그대로
    s = self.sessions.get(study_id)
    scope = (s.asset_scope[0] if (s and s.asset_scope) else study_id)
    level = _corr_level_of(scope)                      # macro/bond=macro(belief차단), 그외=micro
    return self.flags.corr_prior_shrink(
        base_corr_prior, series_ids, level=level, conservative=conservative)
```

### 런타임 RegimeGlasso 호출처 (corr_prior 전부 생략)

**호출처 A — `core/brain/regime_to_weights.py:197`** (배분 레이어, 슬리브 공분산)
```python
# 현재 (corr_prior 생략 → np.eye)
rg = RegimeGlasso(min_obs=10).fit(X, ids_v)
```
**호출처 B — `core/assume/weight_cycle.py:62`** (offline 학습, GlassoWeightLearner)
```python
# 현재
self._rg = RegimeGlasso(lam_floor=self.lam_floor).fit(self._X, np.asarray(regime_ids))
```

### 변경안

**호출처 A (regime_to_weights.py:197) — base_corr_prior 를 study relationships 에서 받아 주입**
```python
# wire2: relationships → corr_prior (opt-in). study_register facade 로 belief 약화 거쳐 주입.
base_cp = np.eye(len(cols))          # study relationships → 상관 prior 행렬 (없으면 eye)
if _study_reg is not None:           # 부트스트랩된 StudyRegister (wire1)
    base_cp = _study_reg.prepare_corr_prior("macro", base_cp, cols)   # macro scope=belief차단 no-op
rg = RegimeGlasso(min_obs=10, corr_prior=base_cp).fit(X, ids_v)
```

**relationships → corr_prior 행렬 변환** (현 코드엔 변환기 없음 — 신규 글루 필요, study_register 안 추가 권장):
```python
# study_register.py 신규 메서드 (제안 — relationships edge → prior 상관행렬)
def relationships_to_corr_prior(self, study_id, series_ids, default_rho=0.3):
    s = self.sessions.get(study_id)
    n = len(series_ids); idx = {sid: i for i, sid in enumerate(series_ids)}
    M = np.eye(n)
    for rel in (s.relationships if s else []):
        i, j = idx.get(rel.node_a), idx.get(rel.node_b)
        if i is None or j is None: continue
        rho = default_rho * (1.0 if rel.edge_type == "direct" else -1.0)
        M[i, j] = M[j, i] = rho
    return M    # PD 보정은 호출측 또는 eb_shrink floor 가 흡수
```

### 불변식 보존

- **belief→_macro 차단 (reflexive loop 가드 — 핵심)**: `prepare_corr_prior` 가 `_corr_level_of(scope)` 로 level 자동결정. macro/bond scope → level='macro' → `flags.corr_prior_shrink` 가 **belief 차단(no-op)** = base 그대로. self-test case 6 (study_register.py:338-354): `cp_macro == base_cp` assert, micro 직접호출만 flag 반영. 종목 flag 가 거시 Σ 에 새는 pro-cyclical 재앙(강세장 과신→리스크 극저 오판) 구조적 차단.
- **opt-in off 무회귀**: `is_r15_enabled()` off → `prepare_corr_prior` 가 `base_corr_prior` 를 `is` 그대로 반환 (study_register.py:224-225, 352 `is base_cp` assert). 호출처 변경도 `_study_reg is None` 가드 → off 면 np.eye 유지 = byte-identical.
- **SACRED 비접촉**: 공분산 학습 = 배분 % 산출 전 단계, execute_trade 미접촉.

---

## wire 3 — indicators 등록 (merit 지표 series_id)

### 현재 코드

**`core/data/weight_panel.py:140` build_indicator_matrix (지표 패널 본체)**
```python
def build_indicator_matrix(provider, series_ids, periods, as_of) -> IndicatorPanel:
    assert_no_reflexive_series(series_ids)          # 반사성 게이트
    ...
    for i, period in enumerate(periods):
        for j, sid in enumerate(series_ids):
            v = provider.realtime(sid, period, a)   # PIT vintage 조회
            if v is not None: mat[i, j] = float(v)
    return IndicatorPanel(matrix=mat, periods=..., series_ids=list(series_ids), as_of=a)
```

**`core/study/panel_manifest.py:69` from_study_session (yaml indicators → 패널 series)**
```python
def from_study_session(s, *, panel_instance_id=None) -> PanelManifest:
    pid = panel_instance_id or f"panel.{s.study_id or 'unknown'}"
    return PanelManifest(panel_instance_id=pid, study_id=s.study_id,
                         indicators=list(s.indicators), as_of=s.as_of)
```
→ series_id 는 **yaml indicators[].id** 에서 자동 추출 (panel_manifest.py:44 `series_ids`). 변환 불필요 — yaml 에 indicator 등록만 하면 패널이 자동 인지.

**`core/brain/fred_adapter.py:36` FRED_SERIES (거시 분류기 입력 큐레이션)**
```python
FRED_SERIES = {
    "GDPC1": "real_gdp", "PAYEMS": "nonfarm_payrolls", ...
    "DFII10": "real_rate_10y", "DTWEXBGS": "dollar_broad",
    "DCOILWTICO": "oil_wti", "DGS10": "nominal_10y", "DGS2": "nominal_2y",
}
```

### merit 지표 등록 현황 (grep 확인)

DGORDER / Empire / vix_term / fx_carry / ism_pmi (NOPMI/VIX3M 류) = **core/*.py 등록 0건**. study-research yaml/md 에만 존재. 두 등록 경로:

**(a) PIT 패널 경로 (weight_panel)** — yaml indicators 에 id 만 추가하면 from_study_session 이 자동 인지. provider(VintageStore) 가 그 series 를 realtime 으로 못 주면 NaN 열 (graceful, weight_panel.py:214 self-test). → fetch 가 별도 필요.

**(b) 거시 FRED 경로 (fred_adapter)** — DGORDER 등 FRED 가용 series 면 FRED_SERIES dict 에 1줄 추가:
```python
# wire3 변경안 (fred_adapter.py:64 근처 추가 — FRED 가용 merit driver)
"DGORDER": "durable_goods_orders",   # 내구재 주문 (cyclical→XLE forward, eq_us_cyclical merit)
"NOPMI": "ism_mfg_pmi",              # ISM 제조업 PMI (cyclical 선행) — ※FRED series_id 가용 사전검증 의무
"VIXCLS": "vix",                     # VIX (vix_term 구조 입력)
"VXVCLS": "vix_3m",                  # VIX 3M (vix_term = vix_3m/vix)
```
★`empirical-claim-presentation.md §1.1-ext`: FRED series_id 가용범위 박제 전 `fred.get_series_info(series_id)` 검증 의무 (DGORDER/NOPMI/VXVCLS 가용 범위 미검증 — 등록 전 1차 검증 latch).

### 불변식 보존

- **반사성 게이트**: build_indicator_matrix 가 `assert_no_reflexive_series` 강제 (weight_panel.py:152) — merit 지표가 포지션/PnL 유래면 ValueError. DGORDER/Empire 등 외부 거시 = 통과.
- **opt-in off 무회귀**: indicator 등록은 패널 조립 단계(학습 입력). FRED_SERIES 추가는 거시 chain(INV_CORE_GATE) 안에서만 소비 → off 면 미사용. yaml indicator 추가도 register(INV_R15_WEIGHTS) 게이트 뒤 → off 면 카드 미생성 = 무회귀.
- **SACRED 비접촉**: 데이터 공급만, 주문 경로 무관.

---

## wire 4 — judge lens/corr wire (qwen 정성 렌즈 + 학습비중)

### 현재 코드

**`core/assume/judge.py:147` judge() 시그니처 (lens_prompt/weight_card 인자 이미 존재)**
```python
def judge(firm, sector, date_, as_of, *, model, features, signals,
          cards=None, cfg=None, valuation=None, rag=None, qwen_hook=None,
          derived_confidence=None, derived_band_halfwidth=None,
          weight_card=None, indicator_z=None, regime_pi=None,
          lens_prompt=None) -> JudgeVerdict:
```

**judge.py:223-228 — lens 주입 (G3, opt-in)**
```python
l2 = _call_qwen_with_lens(qwen_hook, firm, sector, a, lens_prompt) or {}
if lens_prompt and _qwen_accepts_lens(qwen_hook):
    reasons.append("L2 lens 주입(정성 렌즈 컨텍스트)")
```
**judge.py:140-144 _call_qwen_with_lens (시그니처 검사 후 lens 전달)**
```python
def _call_qwen_with_lens(qwen_hook, firm, sector, a, lens_prompt):
    if lens_prompt and _qwen_accepts_lens(qwen_hook):
        return qwen_hook(firm=firm, sector=sector, as_of=a, lens=lens_prompt)
    return qwen_hook(firm=firm, sector=sector, as_of=a)
```

**judge.py:200-251 — 학습비중 합성 S_L1 + down-only 천장**
```python
if weight_card is not None and indicator_z is not None:
    zc = _align_indicator_z(indicator_z, weight_card.series_ids)
    w = weight_card.composed_weights(regime_pi)
    s_l1_synth = synthesize_l1(zc, w, floor=weight_card.floor)   # clamp_floor(Σ w·z)
    ...
    point = s_l1_synth
...
size_mult = l1_size * a2 * a3                  # ∈ [0, l1_size] (monotone-↓)
assert_ceiling_invariant(size_mult, l1_size)   # ★down-only 강제 (judge.py:251)
```

### judge() 를 런타임 호출하려면

`judge()` 런타임 호출 = **0건** (run_agents = 코인 점수제 agents/orchestrator.py, judge import 없음). judge 호출 caller = stock_track(테스트/백테스트 functional, 라이브 entrypoint 부재 = go-live 경계, progress.md:55). ★**wire 4 의 라이브 활성화 = stock entrypoint 필요 → autopilot 범위 밖**. 본 수집 범위 = facade 결선까지 (judge 가 prepare_judge_call dict 를 받게).

**변경안 (judge caller 가 prepare_judge_call 결과를 주입 — stock_track 결선 시 패턴)**
```python
# wire4: study facade → judge 인자 (caller 측, opt-in). lens_prompt/weight_card 둘 다 None 이면 무회귀.
jc = _study_reg.prepare_judge_call(study_id, regime_id=regime_id) if _study_reg else \
     {"weight_card": None, "lens_prompt": None, "regime_pi": None}
v = judge(firm, sector, date_, as_of,
          model=model, features=features, signals=signals, cards=cards,
          valuation=valuation, rag=rag, qwen_hook=qwen_hook,
          weight_card=jc["weight_card"], indicator_z=indicator_z,
          regime_pi=jc["regime_pi"], lens_prompt=jc["lens_prompt"])
```

### 불변식 보존 (★down-only — judge 의 핵심)

- **down-only (monotone-down) 보존**: L2/L3 = strictly attenuating-only. `a2, a3 ∈ [0,1]` (judge.py:94-123), `size_mult = l1_size * a2 * a3 ∈ [0, l1_size]`. `assert_ceiling_invariant(size_mult, l1_size)` (judge.py:251) 가 어떤 lens/L2/L3 입력도 size > l1_size 불가 강제. self-test case 7 (judge.py:331-338)·case 10 (366-374): 모든 L2/L3 + weight 조합 전수 `size ≤ l1_size`. lens_prompt 는 attenuator 입력 컨텍스트일 뿐 — 천장 불변식과 무관 (judge.py 주석 226 라인).
- **L1·a2·a3 ∈ [0,L1]**: lens 주입이 a2/a3 를 늘리는 경로 구조적 부재 — lens 는 qwen_hook 의 입력이고, qwen_hook 결과(definition_match)는 `_qwen_attenuator` 가 max 1.0 로 clamp (judge.py:99). 증폭 불가.
- **opt-in off 무회귀**: lens_prompt=None(INV_STUDY_LENS off → render None) + weight_card=None(INV_R15 off → _build_card 미호출) → judge 가 단일 cheapness_z 경로 (judge.py:210-211). self-test case 11 (judge.py:377-380): weight 미제공 = case1 과 size 동일 (무회귀). case 6b (324-328): L2 absent = L1 단독 baseline.
- **fail-safe**: lens 주입 중 qwen 장애 = abstain(방향노출 0), fail-open 아님 (judge.py:238-242). 장애 시 사이징 증가 역방향 차단.
- **SACRED 비접촉**: judge 는 순수 판정(I/O 없음, judge.py:23 docstring). 주문 미접촉.

---

## wire 5 — 게이트 (환경변수 + opt-in off 무회귀)

### 환경변수 위치

| 게이트 | 정의/판정 위치 | 역할 |
|---|---|---|
| `INV_CORE_GATE` | `scripts/run_agents.py:831`, `run_agents.sh:263` | core/ 백스톱(RiskGate)·거시 chain·로깅 라이브 연결. buy/sell 시만. |
| `INV_R15_WEIGHTS` | `core/study/study_register.py:34,37` `is_r15_enabled()` / `portfolio_orchestrator.py:155` / `run_agents.py:872` | weight_card 등록 + flag tilt + corr_prior 약화 + belief 공급. |
| `INV_STUDY_LENS` | `core/study/lens_store.py:22` `_ENV_FLAG` | lens 주입 (lens_store.render 내부 게이트). |
| `INV_UNATTENDED_FSM` | `run_agents.py:891` | 무인 de-risk FSM (별 트랙). |

**`study_register.py:37` is_r15_enabled() — 판정 SSOT**
```python
def is_r15_enabled() -> bool:
    return str(os.environ.get(_ENV_R15, "")).strip().lower() in ("1", "true", "on", "yes")
```

### opt-in off 무회귀 (byte-identical) 패턴

**현 INV_CORE_GATE 패턴 (run_agents.py:831 — 개통 시 모방할 골격)**
```python
if os.environ.get("INV_CORE_GATE", "false").lower() == "true" and decision in ("buy", "sell"):
    try:
        # ... 신규 core/ 연결 ...
    except Exception as _ge:
        log(f"[core-gate] 예외 → 레거시 경로 유지: {_ge}")   # 라이브 절대 미크래시
```
패턴 3요소: (1) env 게이트 default-off (2) try/except 로 예외 시 레거시 경로 유지 (3) 결정 변경 없는 위치(로깅·공급)부터.

### 개통 시 게이트 on 방법

```bash
# shadow (로깅만, 결정 비반영) — 현 상태
INV_CORE_GATE=true bash scripts/run_agents.sh

# opt-in (study facade 공급 + corr_prior 주입, 결정 영향 down-only)
INV_CORE_GATE=true INV_R15_WEIGHTS=true bash scripts/run_agents.sh

# + lens 정성 렌즈
INV_CORE_GATE=true INV_R15_WEIGHTS=true INV_STUDY_LENS=true bash scripts/run_agents.sh
```

### 불변식 보존

- **opt-in off 무회귀 검증 (테스트 박제)**: `tests/test_study_pipeline.py:58-72` (R15/LENS off→on toggle), `tests/test_sleeve_belief_cov.py:150-167` (R15 off=정적 배분 무회귀 / on=belief 동적 공분산 connectivity). 게이트 off = import 자체 안 일어남 → byte-identical.
- **SACRED 비접촉**: 모든 게이트가 execute_trade 호출 전 단계(결정·사이징·공급). DRY_RUN/실거래 flip 미접촉.

---

## wire 6 — 개통 순서 (점진 rollout)

### 안전 순서 (shadow → opt-in → active)

```
[Stage 0 — 현 상태] INV_CORE_GATE=true 만 (거시 chain 로깅, 결정 비반영)
        ↓ wire1: StudyRegister 부트스트랩 추가 (register + status 로깅만)
[Stage 1 — shadow] INV_R15_WEIGHTS=true + wire1
        - register() 카드 등록 + prepare_judge_call/prepare_corr_prior **호출하되 로깅만**
        - 결정엔 미반영 (jc 결과를 log, judge/regime_to_weights 엔 아직 미주입)
        - 검증: 카드 N개 등록, corr_prior macro=no-op 확인, lens render 확인
        ↓ wire2: regime_to_weights corr_prior= 주입 (배분 레이어 — 종목 판정보다 안전)
[Stage 2 — opt-in 배분] wire2 active
        - corr_prior 가 실제 RegimeGlasso.fit 에 들어가 슬리브 공분산 변경
        - belief→_macro 차단(macro scope=no-op) 으로 reflexive loop 무위험
        - 검증: 배분 % 변화 + caution=belief_conditional_cov, OOS shadow 비교
        ↓ wire3: merit 지표 fetch + 패널 등록 (데이터 공급, 결정 무관)
[Stage 3 — 지표 확장] wire3 (FRED_SERIES + yaml indicators)
        - NaN 열 graceful, 반사성 게이트 통과 확인
        ↓ wire4: judge facade 결선 (★종목 판정 — go-live 경계, stock entrypoint 필요)
[Stage 4 — judge active] INV_STUDY_LENS=true + judge(weight_card=, lens_prompt=)
        - ⚠️ stock_track 라이브 entrypoint 부재 = autopilot 범위 밖 (별 게이트)
        - down-only 천장 불변식이 안전 보장 (size ≤ l1_size)
```

### 순서 근거

1. **배분(wire2) 먼저, 판정(wire4) 나중**: 배분 레이어는 macro scope=belief 차단(no-op)이라 reflexive 무위험 + 슬리브 % 만 변경(개별 종목 사이징 아님). judge 는 stock entrypoint 부재 = go-live 경계.
2. **shadow(로깅) → active**: Stage 1 에서 facade 를 호출하되 결과를 로깅만 → 카드/corr/lens 산출 검증 후 Stage 2 에서 실주입.
3. **wire3(데이터) 직교**: 지표 fetch 는 결정 무관 — 언제든 안전. 단 FRED series_id 가용범위 사전검증 의무.

### DRY_RUN / execute_trade SACRED 비접촉 확인 (코드 검증)

- 모든 wire 가 **execute_trade 호출 전** 단계: wire1~3=공급/등록, wire4=순수 판정(I/O 없음). 실주문은 `run_agents.py:929` `subprocess.run([..., "scripts/execute_trade.py", "bid", ...])` — 어느 wire 변경안도 이 라인 미접촉.
- `decision = "hold"` 차단 경로(run_agents.py:884 RiskGate REJECTED)는 기존 INV_CORE_GATE 백스톱 — wire 개통은 결정 로직(공급·사이징)까지만, 주문 flip 제외.
- DRY_RUN flag = execute_trade.py 내부 (CLAUDE.md 안전장치) — wire 변경 0.

---

## 종합 — 불변식 보존 매트릭스

| wire | down-only | belief→_macro 차단 | opt-in off 무회귀 | SACRED 비접촉 |
|---|---|---|---|---|
| 1 yaml 로더 | N/A (등록만) | 정적 yaml (belief 무) | is_r15 off → cards={} | 순수 등록 |
| 2 corr_prior | N/A | ★macro scope=no-op (self-test c6) | prepare_corr_prior `is base` 반환 | 공분산 산출 |
| 3 indicators | N/A | 반사성 게이트(포지션 거부) | 게이트 뒤 미소비 | 데이터 공급 |
| 4 judge | ★assert_ceiling (c7/c10) | lens=attenuator 입력만 | weight/lens None=무회귀 (c11) | 순수 판정 I/O 0 |
| 5 게이트 | — | — | env default-off, test 박제 | execute_trade 전 단계 |
| 6 순서 | 배분→판정 | 배분 macro=no-op 먼저 | shadow→opt-in 점진 | 주문 flip 제외 |
