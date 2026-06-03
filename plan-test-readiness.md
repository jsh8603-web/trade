---
tags: [plan, inv, test-readiness, master, multi-session]
date: 2026-06-02
session: btn-Inv
status: active
supersedes_none: true
note: 기존 plan.md / progress-wire-impl.md 와 별개 — 수익률 테스트 준비 마스터 플랜
---

# 마스터 플랜 — 수익률 테스트 준비 + 단계적 검증

> **사용자 결정(2026-06-02)**: 권고안 전부 수행 + **judge 재설계·재테스트**를 계획에 포함 +
> **주식 트랙 full build·재테스트**도 동일하게 포함. (Q1=결정론 먼저, Q2=주식 돌아가는지 먼저, 둘 다 후속 단계로 박음)

## 0. 핵심 원리 (왜 이 순서인가)

- **목표**: 시뮬에서 수익이 안 나면 "방법론 결함"인지 "코드(상수/가중치) 결함"인지 **원인 분리**.
- **Test 1(둔갑 자문)** = 방법론 OK를 먼저 박는 단계. **Test 2(실파이프라인 시계열 주입)** = 코드 진단.
- ★**발견(코드 확인)**: 지금 Test 2가 돌릴 파이프라인의 **결정→사이징→게이트 체인이 미배선**
  (`backtest/engine.py`: risk_gate 미호출 / 사이즈 고정 `capital*0.95` engine.py:250 / `judge()` production 호출 0).
  → 지금 돌리면 뼈대를 테스트 = 진단 불가. **배선이 진짜 선결.**
- ★**judge 재설계(클로드 최종결정·consensus·강화)는 결정론 Test 2 *후*에**: LLM을 루프에 넣으면
  "LLM 판단 결함"이라는 제3 교란변수가 추가돼 방법론 vs 코드 진단을 오염. 결정론 경로로 먼저 깨끗이 진단 →
  그 다음 judge 재설계 → 재테스트(증분 효과 측정)가 올바른 순서.
- **불변식 유지**: opt-in off byte-identical / down-only 천장(judge 재설계 단계에서만 분기 검토) /
  go-live(DRY_RUN=false·execute_trade) = 사람 게이트, 자율 범위 밖.

---

# ★Tier 체계 (2026-06-02 재구성)

> T1 자문(gemini+claude 2R 수렴) + T0 실측이 **거시 신호 결함**을 짚었다 → 그걸 먼저 고치는 게 Tier 1.
> 기존 마스터 플랜(P0~P5 = 배선·judge·주식·리포트)은 Tier 2로 강등. **Tier 1 완료 후 Tier 2 진입.**
> 근거: 결함 있는 거시 신호 위에 Test 2를 돌리면 손실 원인이 "신호 결함"인지 "배선/상수"인지 또 섞인다.
> T0가 찾은 2022 momentum-miss = 자문이 지목한 단일점 실패 지점과 일치 → Tier 1이 그 뿌리를 제거.

## Tier 1 — 거시 신호 보강 (자문 수렴 산물, 최우선)

### 핵심 원리
- 자문 합의: 현 거시 분류기가 (a) 물가를 momentum-only로 봐 지속 고물가 국면을 놓치고(2022 실측 오분류),
  (b) 주식-채권 동조의 부호를 vol 하나로 잡아 거꾸로 읽을 위험, (c) 유동성 driver 누락.
- 한 잠재변수(물가 국면)가 stock-bond·정책반응·분류에 동시 전파 = **단일점 실패** → 우선 보강 + 안정성 모니터.
- 불변식: opt-in off byte-identical, small-n rigor, 점추정 박제 금지. 모든 신규 driver = 15축 audit 필수.

### M1. 물가 신호 2D 화 (level × momentum) — ★1순위, 2022 miss 직접 해소
- 현: `_inflation_signal`(regime_classifier.py:203) = `_momentum_z(yoy core_cpi, 3)` 단독 → 가속 0이면 "낮음".
- 목표: level 항(core PCE/CPI − 목표 2%, σ 정규화) + momentum 항 결합. 목표 이탈 시 level 가중↑(페널티).
- 검증: 2022 재분류(Recovery→Overheat/Stagflation 복원) + 전 구간 회귀(타 국면 무회귀) + off byte-identical.
- 자문 근거: 양 모델 합의 "momentum-only 비표준, level×change 2D 표준".

### M2. stock-bond 상관 = 물가 국면 연동 state — 부호 교정
- 현: vol 평온/위기 2상태 오버레이만 → 2008형(상관 더 음)·2022형(상관 양전환) 동일 처리.
- 목표: vol=상관 크기, 물가국면=상관 부호로 분리. 고/상승 물가 → 양 prior, 저/안정 → 음 prior.
  M1 산출(물가 국면)을 그대로 조건변수 재사용(신규 변수 X = 과적합 절약).
- 반증 테스트(채택 전): rolling 실현 stock-bond 상관을 vol더미·물가국면더미·둘다 회귀 →
  물가국면이 vol 위에 부호 증분 설명력 + 2021-22 부호전환 선행(granger). 증분 없으면 폐기.

### M3. 유동성 factor 탐색 (Net Liquidity·NFCI) — 신규 driver 후보
- 후보: Net Liquidity = WALCL − WTREGEN − RRPONTSYD / NFCI·ANFCI / HY·IG OAS(BAMLH0A0HYM2·BAMLC0A0CM).
- ⛔ 무비판 추가 금지: indicator-ledger·factor 7종과 이중계상 대조(NFCI는 분류기 기사용, factor엔 부재 = gap).
- 15축 audit 기반 subagent 스폰 → magnitude·regime·조건부성·통계신뢰도 실측 → tier 판정(점추정 금지).

### M4. 폐기 신호 재판 (slope→regime / bond vol 조건부)
- slope(T10Y2Y): daily indicator 아니라 regime layer state로 재배치 검토(월·분기 forward 회귀).
- bond vol(MOVE): rate-tantrum 더미(|Δ10y| 상위decile ∧ equity-vol 중앙값 이하) 안에서 조건부 증분 베타 재측정.
- 결과: 살아나면 부활(rejected_provisional→), 조건부도 0이면 폐기 확정 + ledger 기각사유 보강.

### M5. 레짐 분류기 transition 안정성 모니터 — 단일점 실패 방어
- M1·M2·정책반응이 물가 국면 하나에 의존 → 오분류 동시 전파. transition 빈도·오분류율 모니터 지표 신설.

### Tier 1 게이트
- 각 M = 15축 audit 필수(별도 감사관 subagent, main 통과편향 차단) + off byte-identical + ledger 갱신.
- M1·M2는 코드 변경(구현) / M3·M4는 탐색·측정 우선(구현은 audit 후) / M5는 관측 지표.
- ★자문 prior 코드화 시 본인 정량 시뮬 ≥1회 + null result 첨부(decision-quality-protocol).

---

## Tier 2 — 기존 마스터 (배선→Test 2→judge→주식→리포트)

> Tier 1 완료 후 진입. 아래 P0~P5 = 원래 계획 그대로 강등.

## Phase P0 — 방법론 검증 트랙 (즉시·병렬, Test 2 배선과 비충돌)

### T0. 거시 파이프라인 과거 설명력
- **무엇**: `regime_classifier.classify(as_of=과거시점)`을 과거 여러 시점 반복 → 국면 타임라인
  (reflation/recovery/overheat/stagflation 전환) vs 실제 침체/회복 시점 대조.
- **predictive 지표만**: 기대인플레·금리커브·신용스프레드·실질금리(forward-looking). 후행 제외.
- ⚠️ **caveat**: vintage 미반영(latest-fallback) = 발표시점 값 ≠ 최종개정치. 과거 설명력 약간 낙관 편향 명시.
  진정 PIT vintage backtest = Phase V TODO(범위 밖).
- **산출**: 국면 타임라인 표 + 실제 매크로 이벤트 대조 + 설명력 정성 평가.
- **진입**: `core/brain/regime_classifier.py` classify + `regime_history.build_sleeve_regime_ids`.

### T1. 투자 일반론 둔갑 자문
- **무엇**: 우리 거시→지표→배분 로직을 코드 흔적 제거·투자 일반론 번역 → gemini-web + claude-web 병렬 자문.
- **목적**: (a) 표준 방법론에 맞는 프레임인지 (b) 누락 지표·방법론 없는지.
- **자료**: `handoff-test-prep-20260602.md` §1 4축(magnitude/regime/조건부성/통계신뢰도) + §2 카탈로그 + §5 샘플.
- **페르소나**: CIO/멀티에셋 PM. 3~7R 수렴.
- **누락 피드백 처리**: ledger 대조(§4) — rejected 사유 타당성 / 미검토면 15축 audit, **무비판 추가 금지**.
- **산출**: 자문 수렴 요약 + ledger 반영(배제 유지 / 신규 탐구 큐).

---

## Phase P1 — Test 2 선결 배선 (결정론 경로, LLM no-op)

> 목표: `backtest/engine.py` 시계열 루프가 **진짜 설계 경로**(사이징·게이트·judge)를 타게. LLM은 기본 no-op(a=1.0).

> ★W0 자문 확정 (2026-06-02, gemini-web + claude-web 수렴 + 코드 falsify 2건 통과).
> 브리핑=`.consult-wire-w0-briefing.md`. falsify: ① `ledoit_wolf_weights` 합≈1 정규화(gross 미내장→이중적용 없음) ② production order-path(`portfolio_orchestrator.py:191` 주석) 미구현→REJECT skip 의미론을 백테스트가 선정의(go-live 일관성 유지).
> **opt-in 토글 = naked boolean 금지**. 진입점 1회 hard-branch `if not use_risk_pipeline: return self._run_legacy(...)` + 현재 코드 verbatim 동결(회귀 oracle). 신규 bookkeeping이 off 경로 float 누산순서/dict 순회 건드리는 silent drift 차단.

### W1. 사이징 연결 (gross × weight 합성, 95% 제거)
- **합성 한 줄로 통일**(2-트랙 코드 분기 X, n=1 특수케이스 자연 흡수):
  ```
  window  = rolling_returns(asset)        # 엔진 deque 신규 상태 (현재 없음 — 추가)
  weights = size_portfolio(window)        # n=1→{a:1.0}, n>1→HRP. 무수정 호출
  gross   = clip(target_vol / realized_vol(window), lo, hi)   # gross=엔진 책임
  trade_value = capital * gross * weights[asset]   # ← capital*0.95 대체
  ```
- 측정("사이징 탔다"): `var(gross)>0` ∧ `gross≠0.95` ∧ gross가 `1/realized_vol` 추종.
- 경계: `execute_trade.py`·`coin_shadow` SACRED diff=0. 부품(`size_portfolio`) 무수정. off byte-identical.

### W2. risk_gate 루프 내 호출 (PortfolioState 회계객체)
- `PortfolioState`(toggle off 시 미실행) 신설로 게이트 입력 산출: `nav=cash+Σ(qty·price)` / `daily_loss_pct`(prev_nav 1개) / `holding_days=bar_idx−entry_bar` / `ytd_realized_pnl_pct`(실현손익 누산) / `current_weight=MTM/nav` / `sector_weight`(단일주식≈current_weight, coin=0) / `proposed_size=gross·weight` / `avg_correlation=0.0`(단일자산 비활성=정상).
- 매 buy/sell → `router.submit(order, via_gate=True, **gate_kwargs)` → `.approved`면 체결, 아니면 **skip + 거절사유(rule_id) 카운트**(거절률 높으면 finding). ⛔ 엔진이 cap 추정 재시도 금지(SACRED·drift).
- 경계: risk_gate 규칙 상수 미변경(관측만 추가).

### W3. judge() production 호출지점 연결 (공통 hook + fail-open)
- **공통 hook은 매 bar 호출·카운트**(현 production call=0 대비 ≠0). 정책은 트랙별: stock_track=실 firm/sector/valuation 전달 / coin_track=firm·valuation 부재 → **명시적 bypass `a=1.0`**(hook 자체는 호출=live).
- 결정론 단계 valuation/rag/qwen=None → fail-open `a=1.0` → `final=L1×1.0=L1`. **천장 불변식 `final≤L1` 항상 유지**(증폭 경로 신설 금지=P3).

### W4. 통합테스트 + golden-master + verifier 7관문
- **golden-master**: 변경 전 고정 seed+fixture로 현 엔진 출력(equity curve·trade log·per-bar fill·final NAV) 골든파일 캡처. off가 이걸 해시 동일 재현.
- **verifier 게이트 = "실제로 돌아가는가" 실행검증** (코드 완성 판정 X):
  - **G1** off=byte-identical: `hash(off)==hash(golden)`
  - **G2** on≠off: position fraction 변동 ∨ ≥1 거절 ∨ size≠0.95 중 하나 이상 (같으면 배선 실패)
  - **G3** sizing live: `size_portfolio`/gross 스칼라 ≥1회 호출(spy) ∧ `var(position_fraction)>0` ∧ `≠0.95`
  - **G4** gate live: 모든 fill에 `submit(via_gate=True)` ∧ `via_gate=False→REJECTED` assert ∧ 조작 시나리오(daily_loss cap 돌파)로 거절경로 ≥1회 발화
  - **G5** judge sensitivity(liveness falsifier·최중요): 호출수≠0 ∧ ∀bar `final≤L1` ∧ no-op 단계 `a==1.0∧final==L1`(엄격등호) ∧ 합성 valuation 주입 시 `a<1.0 ∧ final<L1`(죽은 stub 구별)
  - **G6** no-leverage: `Σgross≤1`
  - **G7** on 결정성: on 동일 seed 2회 해시 동일
- 회귀: 도메인 전체 pass 유지.

### 배선 순서
W1 합성 → W2 PortfolioState+Router → W3 judge hook(동시 가능). 멀티에셋 포트폴리오-bar 트랙은 진단이 요구할 때까지 인터페이스 stub만.

---

## Phase P2 — Test 2a 실행 (결정론 경로)

- **무엇**: 코인/거시 substrate on, 과거 시계열 주입 → 거래 시뮬 → equity_curve / 수익률 / MDD.
- **진단**: 수익 미발생 시 (a) 방법론(P1 자문서 OK 받은) vs (b) 코드 상수/가중치 과도.
- **산출**: 결정론 경로 성능 리포트 + 진단(어느 상수·가중치가 의심인지 attribution).

---

## Phase P3 — judge 재설계 + 재테스트 (별건 세션, 후속)

> ★사용자 결정으로 계획에 포함. down-only 안전 불변식 **완화 여부**가 핵심 분기.

### J1. judge 재설계 자문 (3R+)
- **분기**: 클로드 최종결정 / consensus 국면전환 / 강화(증폭) flag를 허용하면 `final ≤ L1` 천장이 깨짐.
  → 안전 vs 표현력 trade-off. 자문으로 "완화하되 어떻게 가드할지"(예: 증폭 상한·증거 요건) 설계.
- **하위 질문**: qwen 트리거 조건 wire / 클로드 평가 기준(거시 리포트·지표 flag) / confidence 쌍방향.

### J2. 구현
- is_high_stakes() 트리거 wire(regime_changed 등) + 클로드 호출 경로 활성 + (분기 결과 시) 제한적 증폭 가드.

### J3. Test 2b 재테스트
- LLM judge 포함 경로로 재시뮬 → **결정론 baseline(P2) 대비 증분 효과** 측정. 환각·비용·비결정성 점검.

---

## Phase P4 — 주식 트랙 full build + 재테스트 (별건 세션, 후속)

> ★사용자 결정으로 계획에 포함. 검증된 공유 substrate(P1) 위에 올림.

### S1. 주식 레이어 자문 (3R)
- 주식 일반론(가정 보관·청산 트리거·섹터 상관 국면조정) vs 우리. 거시 파이프(regime/factor/corr_prior) 공유 여부.
- 거시에서 한 작업이 주식에 그대로 적용 가능한지 / 별도 패치 필요한지. stock.md 연구방향 → 코드 템플릿화.

### S2. 구현
- DART/EDGAR provider(현 빈 stub) + heavy-agent(FORWARD) + 거시 레이어 wire(현 수동주입만) + study 주입.
- 경계: PIT(filing-lag)·생존편향·H22 lookahead 유지.

### S3. Test 2c 재테스트
- 주식 포함 통합 백테스트(코인+주식 동일 AssetTrack). 슬리피지·세금·PBO/DSR.

---

## Phase P5 — 리포트 통합 (별건 세션, 최후)

> 현 0% 구현(`to_context` dead, `ReportStore` Protocol만). Test 2와 무관 → 가장 뒤.

### R1. 자문 (3R, 거시·주식 공통)
- 리포트 가설→가점→falsify 회수 토대. 일일 LLM 요약/indexing vs grep vs BGE-DB. agent 읽는 시점.

### R2/R3. 구현 + 재테스트.

---

## 의존성 / 게이트

```
P0(T0,T1) ──병렬──┐
                  ├─→ P1 배선 ─→ P2 Test2a(결정론 진단) ─→ P3 judge재설계 ─→ Test2b
P1 (T0/T1 무관)──┘                                      └─→ P4 주식 full ─→ Test2c
                                                        └─→ P5 리포트 ─→ Test2c+
```

- **자율 범위**: P0~P5 구현·측정·자문·codify·테스트. ⛔ **go-live(DRY_RUN=false·execute_trade·자본배포) = 사람 게이트.**
- **자문 강제**: P1 배선 방식(W축, 회귀민감) / J1 / S1 / R1 = 외부 자문(gemini+claude 병렬).
- **불변식**: opt-in off byte-identical, SACRED(execute_trade/coin_shadow) diff=0, small-n rigor(자문 prior codify 시).
