---
tags: [type/guide, domain/inv, phase/study-system, topic/indicator-weight-study]
date: 2026-05-30
note: 종목 스터디 시스템 — 각 psmux 작업방이 읽는 통일 지시서(자기완결 킷). main(btn-Codlearn)이 조립 가능하도록 산출 계약을 고정한다.
---

# STUDY-KIT — 종목 스터디 시스템 통일 지시서

> 당신은 하나의 자산군을 맡은 **스터디 작업방**이다. 이 킷을 끝까지 읽고, 자기 자산군을 깊이
> 스터디한 뒤 **§3 의 6-블록 산출 계약(study_session.yaml)** 을 채워서 main 에게 돌려준다.
> 모든 작업방이 같은 계약을 채워야 main 이 조립할 수 있다. 계약을 벗어나지 말 것.

---

## §0. 작업방 행동 규칙 (필독 — 너는 자율 에이전트다)

- **사용자(인간)는 이 방에 없다.** subagent 처럼 **자율 행동**한다. 스스로 판단해 끝까지 진행.
- ⛔ **idle 금지.** 대기·확인요청으로 멈추지 말 것. 막히면 다음 순서로 스스로 푼다:
  ① 코드·문서 직접 Read → ② `/gemini-web` + `/claude-web` 병렬 자문 → ③ 그래도 막히면 main 에 질문.
- **질문·보고는 main(btn-Codlearn) 세션에만** psmux SSOT 헬퍼로(raw send-keys 금지):
  ```bash
  bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[{study_id}→main] 질문/보고 내용"
  ```
- ★**2-1단계(방향성) 완료 시 반드시 main 에 direction.md 보고 후 승인 대기**(필수 게이트 — 승인 전 2-2 금지).
  이 멈춤은 idle 아님. 그 외엔 막바지 산출 완료/진행 불가 시 보고하고, 나머지는 자율로 해결한다.
- 자문·검색 결과, 중간 산출은 `study-research/{study_id}/raw/` 에 계속 누적(유실 방지).

## §1. 목적 (무엇을 위해 스터디하나)

이 시스템은 **평가 지표의 가중치를 거시 국면·산업·종목 특성에 따라 동적으로 바꾼다**(R15).
지금까지 그 지표·가중치는 일회성 리서치로 정해졌다. 이제 자산군마다 깊이 스터디해서:

**최종 산출 = "이 자산군의 종목을 평가할 때, 어떤 지표의 가중치를 어떤 상황에서 어떻게
바꿀지"를 종목 단위까지 잘게 쪼갠 규칙** (= §3 블록4 weight_rules).

이 규칙은 학습→규칙화→주입→해제 4단계 파이프(§4)로 코드에 들어간다. 당신의 산출이 그 입력이다.

---

## §2. 스터디 흐름 (v2 — 담당 종목 전문 애널리스트가 되는 과정)

> ⛔ **자문 내용을 그대로 yaml 에 옮기고 끝내지 마라.** 너는 담당 종목의 **전문 애널리스트**가 된다.
> 아래 3단계를 순서대로 밟고, **각 단계의 바탕 raw 를 반드시 남긴다**(셋 중 하나라도 없으면 산출 불인정).

```
2-1 [방향성·자문 다회]  3~7R 수렴 → ①이론 수집방향 ②이론 검증방향 ③가설 초안
        ↓  direction.md + raw/round-{N}.md   ★여기서 멈춤 → main 승인 게이트
2-2 [이론 학습]        승인된 방향대로 정독·정리 → raw/theory-notes.md
        ↓
2-3 [실데이터 시계열 검증→코드화]  가설을 실데이터로 시계열 검증(상관·regime·Rank-IC)
                       → lens·상관계수·가중치가 어떻게 코드화되는지 → raw/validation-*.md + yaml
```

### 2-1단계 [방향성 — 자문 다회 라운드] ★끝나면 멈추고 main 승인 대기
- `/gemini-web` + `/claude-web` 을 **다회(3~7라운드 수렴)** 돌려 완전성을 올린다:
  ① **이론 수집 방향** — 이 종목을 이해하려면 무슨 이론·교과서·리포트를 봐야 하나
  ② **이론 검증 방향** — 그 이론을 우리 수집기 데이터로 시계열상 어떻게 검증하나
  ③ **핵심 가설 초안** — 검증할 가설(반증조건 포함). 다회 라운드로 빈틈을 메운다
- 매 라운드 직후 자가 점검: "두 모델에 더 물을 것 없나" → 다음 라운드 질문 설계(수렴까지).
- 산출: `direction.md`(①②③ 정리) + `raw/round-{N}.md`(라운드별 원문 누적).
- ⛔ **여기서 멈춘다.** main(btn-Codlearn)에 direction.md 를 보고하고 **승인받기 전 2-2 진입 금지**.
  (이 멈춤은 idle 아님 — 승인 대기는 정당. main 이 승인 또는 보완요청을 보낸다.)

  자문 폴백: gemini/claude-web 채널 경합·타임아웃 시 `WebSearch`/`WebFetch` 직접 리서치 허용.
  결과도 raw/ 저장·출처 명시. 자문이 막혀도 진행한다(단 2-1 완료 후엔 승인 대기).

### 2-2단계 [이론 학습] — 승인된 방향대로
- 승인된 ①②③ 대로 이론을 정독·정리. 교과서 원리 + 리포트 관계도.
- 산출: `raw/theory-notes.md`(강제) — 가격결정 원리, 지표 의미·관계도(거시 예: M2↔미·일 국채금리↔환율).

### 2-3단계 [실데이터 시계열 검증 → 코드화]
- 우리 수집기(§7) **실데이터로 가설을 시계열별 검증**한다: 상관·regime 분해·Rank-IC 로 가설이
  **언제 성립/붕괴하는지** 데이터로 보인다(추상 단정 금지). 무거운 분석 .py 는 Bash 로 직접 실행.
- 그 검증 결과로 **lens·상관계수(블록3 prior)·가중치(블록4)가 어떻게 코드화되는지** 도출한다.
  (lens 는 가변 — 블록5 flag 누적이 lens·가중치를 갱신하는 경로까지 남긴다.)
- 산출: `raw/validation-{지표}.md`(강제 — 시계열 검증 근거·도표) + `study_session.yaml`(§3 7블록).

### ★바탕 raw 강제 (없으면 산출 불인정)
main 이 통합할 때 `raw/` 에 `round-*.md`(자문 다회) + `theory-notes.md`(이론) + `validation-*.md`
(실데이터 검증)가 전부 있는지 검사한다. **셋 중 하나라도 없으면 yaml 거부** — 바탕 없는 코드화 차단.

### 학습 깊이 (거시 예시 = 모든 종목 동일 수준)
거시: 일반론 → 보고서 거시 지표의 의미·관계도(통화량에 미·일 국채·금리가 어떻게 얽히나) → 실데이터
시계열 검증. 당신 종목도 이 깊이로.

---

## §2.5 main 검수 감사 기준 (★8축 체크리스트 — 압축돼도 잊지 않게 박제)

> main(btn-Codlearn)이 각 방 산출을 통합 전 이 8축으로 감사한다. **너(방)도 보고 전 이 기준으로
> self-audit** 하고 미달 항목을 보강하라. 한 축이라도 미달이면 '불충분' → 보강 요청 대상.
> (동기: eq_us_defensive 방이 실데이터 검증을 건너뛰고 합성 시뮬로 yaml 을 채운 사건 — 사용자
> 정정 "이론 + 실데이터 검증이 모두 생략됐다". 이 기준은 그 재발을 막는 영속 게이트다.)

### 핵심 3축 (사용자 요구 = 이론 + 실데이터를 이용한 검증)
- **A. 이론 학습 실재성**: raw/theory-notes.md 가 실제 교과서·논문·리포트 정독 흔적인가.
  자문 답변 복붙이 아니라 가격결정 원리·지표 의미·관계도를 본인이 정리했나. 출처(저자·연도) 명시.
- **B. 실데이터 시계열 검증** (★가장 중요): raw/validation-*.md 에 실측 근거 — 데이터 소스·기간·
  관측수(n)·상관계수·p값·Rank-IC·regime 분해 — 가 있나. 가설이 실데이터로 시계열별 confirm/reject
  됐나. ⛔ **합성·시뮬 데이터로 때우기 금지**("synthetic"/"seed"/"prior-consistent simulation"
  = 자동 불충분). 무거운 분석 .py 는 Bash python 실제 실행, 출력을 raw 에 저장.
- **C. yaml 도출 추적성**: 블록3 corr_prior·블록4 base_weight·블록1 lens·블록5 hook 가 B 의
  실측에서 도출됐나. yaml 숫자가 validation 실측과 추적 연결되나(자문/이론 복붙 아님). v1→v2 에서
  실측으로 prior 가 하향·조정된 흔적이 정상(예: cyclical IC 0.658 합성 → <0.10 실측 하향).
  ★**flag 연결 추적**(seed→라이브 진화): 블록5 confidence_hooks 가 `affects_indicator`(→weight tilt)·
  `affects_edge`(→corr_prior shrink)를 명시해 flag→가중·상관 동적 경로를 추적 가능케 했나. 미명시 시
  flag 누적이 weight/상관/lens 로 전달 안 됨("정의만 하고 작동 안 함" = 사용자가 막으려는 패턴).

### 완전성 향상 5축 (★사용자 지시 추가 기준)
- **D. PIT / lookahead 차단**: 모든 검증이 vintage point_in_time + knowable_from 기준인가.
  OOS walk-forward(train/test/refit 분리)로 in-sample 과적합을 걸렀나.
- **E. 자문 비판심사 + 환각 cross-verify**: 자문·리포트의 정량 수치를 primary 소스로 교차검증했나
  (예: reit cap rate spread 243bp/2024 industrial -17.7% Nareit 원본 확인). 맹목추종·반례 무시
  회피. 자문이 인용한 학술 claim 도 실데이터로 재검증했나(예: eq_intl China β 환각 기각).
- **F. 반증가능성 + 기각 기록**: 가설마다 정량 반증조건(임계·e-value·CI)이 있나. ★기각된 가설도
  raw 에 남겼나(예: cyclical H3/H5 REJECT, macro 가설2 FAIL). reject 은 실패가 아니라 정상 산출.
- **G. effective-N / 검정력 한계 명시**: 관측수 부족·regime 자기상관·N=4 등 검정력 한계를 숫자로
  밝혔나. "신호가 풍부할수록 독립 관측이 적다"는 점을 prior_strength 보수화로 반영했나.
- **H. 미해결 의문 솔직 기재**: confound·selection bias·데이터 한계를 §미해결로 남겼나(예: crypto
  8 의문, gold numeraire trap). "전부 검증됨" 단정 회피.

### 감사 판정 + main 처리
- 판정 = [**충실**(8축 통과) / **부분**(핵심 3축 일부 미달) / **불충분**(B 실데이터 검증 부재 또는 합성)].
- **불충분·부분이면 보강 요청** — 어느 축이 왜 미달인지 구체 명시. **충실만** register(require_raw) 통합.
- raw 완비 게이트(round-*/theory-notes/validation-*)는 형식 검사, 본 8축은 내용 검사. 둘 다 통과해야 함.
- ★상세 감사 절차(**provenance + 재계산**: yaml 숫자를 raw 에서 독립 재계산·합성 지문 검사)·신규 4축
  (I 생존편향·데이터무결성 / J 거래비용·capacity·경제적유의성 / K 다중검정 보정 / L 통합 상관행렬 PSD·
  공통인자 중복)·hard/soft/tier 분류 = **AUDIT-GUIDE.md**(opus 독립 감사관 SSOT, gemini+claude 자문 반영).
  너(방)는 보고 전 그 12축으로 self-audit 하라. ⛔ main 은 통과편향 배제 위해 opus subagent 가 독립 감사한다.

---

## §3. 산출 계약 (study_session.yaml — 6 블록 고정, 애매함 금지)

작업 폴더에 `study_session.yaml` 한 개. 6 블록 전부 채운다. 빈 칸은 사유 명시.

```yaml
study_id: str            # 예: eq_us_cyclical
asset_scope: [str]       # equity.us / equity.kr / equity.intl / reit / commodity / gold / bond / macro / coin 중
as_of: "2026-05-30"      # PIT 기준점

# 블록1: LENS (정성 렌즈 — LLM 주입용. 일반론+리포트의 정제 결과)
# ★가변: 이 lens 는 고정이 아니다. 블록5 flag 누적(확신/거부)→신뢰도→이 필드(특히 estimation_note·
#   regime_reading)와 블록4 가중치가 미세 변동한다(§2 작업순서 3단계). lens=초안, flag=갱신 경로.
lens:
  pricing_principle: str       # 이 자산이 왜 오르내리나(원리/방정식)
  report_relations: [str]      # 보고서가 엮어 보는 관계(예: "M2↔미·일 국채금리↔환율")
  regime_reading: str          # "X 국면에선 이 지표를 이렇게 읽는다"
  estimation_note: str         # "이 시각 이후 이런 의미일 수 있다"(추정 — 국면전환 anchor)

# 블록2: INDICATORS (정량 지표 — 우리 시스템 자료로 귀결)
indicators:
  - id: str
    family: enum            # valuation|quality|momentum|revision|macro_sensitivity|risk|macro_driver
    is_core: bool           # 주식이면 통일 하드룰 코어셋 여부(§6)
    in_our_system: bool     # 우리 시스템에 이미 있나
    source_or_collector: str# 있으면 어느 수집기 / 없으면 끌어올 소스(§7 참조)
    transform: str          # own_history_z | rank | level | yoy
    vintage_policy: enum    # point_in_time | final_revised  (학습 입력은 point_in_time 강제)
    lag: int                # 발표 지연(periods)

# 블록3: RELATIONSHIPS (관계 가설 — glasso prior. partial-corr 기준!)
relationships:
  - node_a: ref            # indicator id
    node_b: ref
    edge_type: enum         # direct | common_cause | undetermined  (기본 undetermined)
    conditioning_set: [ref] # 무엇을 고정한 partial-corr 인가(필수 명시. 빈 셋이어도)
    lag_routing: enum       # contemporaneous | lagged
    prior_sign: enum        # pos | neg | unsigned
    prior_strength: float   # 0~1
    theory_basis: str       # 1줄 경제 근거(감사 추적)

# 블록4: WEIGHT_RULES (★최종 산출 — 종목별 가중치 동적 변경)
weight_rules:
  - indicator_id: ref
    base_weight: float
    modulate_by: [enum]     # regime | industry | size | name_specific (무엇에 따라 바꾸나)
    direction: str          # 예: "rate-shock 국면 + long-duration 종목 → rate beta 가중↑"
    granularity: enum       # sleeve | industry | ticker (어디까지 잘게)

# 블록5: CONFIDENCE_HOOKS (신뢰도 누적 — 확신/거부 flag를 *코드로 구현*할 계획)
# ★사용자 핵심: 매 거래마다 (확신)/(거부) flag 누적 → 가정 신뢰도 누적 → 렌즈 미세변화 → 동적 가중치.
# 단순 정의 금지. 어느 코드에서 어떻게 발생·누적·저장·작동하는지 구현 계획까지 적는다(블록7 falsify 와 연결).
confidence_hooks:
  - hypothesis_id: ref       # 블록3 edge 또는 블록1 lens 가설
    affects_indicator: ref   # ★이 flag 신뢰도가 변조할 indicator id(블록4 weight tilt 연결, G4 flag_router)
    affects_edge: [ref, ref] # ★이 flag 가 약화/강화할 corr_prior edge(블록3 node_a,node_b). flag→상관 prior
                             #   shrink 연결. 없으면 main 이 node 신뢰도 결합으로 근사(정밀도↓)
    confirm_signal: str      # (확신) flag 발생 조건(예: "이 카드로 산 종목 outcome 의 Rank-IC 양 유지")
    reject_signal: str       # (거부) flag 발생 조건(예: "score OOS Rank-IC e-CUSUM 단측 붕괴")
    emit_where: str          # flag 를 거래마다 어디서 발생시키나(예: judge 사후평가 / backtest engine SELL outcome)
    accumulate_in: str       # 누적 코드(예: core/assume/weight_falsification.score_ic_breakdown_eprocess)
    confidence_metric: str   # 신뢰도 수식(예: e-value anytime-valid 누적 / Beta(α,β) posterior)
    store: str               # flag·신뢰도 저장처(예: registry 카드 confidence_now / RulePerformance)
    action_threshold: str    # 임계 동작(예: "e-value>K → adopt 강화 / 붕괴 → retract live 차단")
    feeds_weight: str        # 신뢰도→가중치 미세변동 경로(예: "derive_weights 재적합 trigger")

# 블록6: COLLECTOR_PLAN (부족 자료 수집기 추가 계획)
collector_plan:
  - missing: str            # 없는 자료
    source: str             # FinanceDataReader | FRED 시리즈 | ECOS | DART | ...
    interface: enum         # VintageProvider | FundamentalsProvider | FxStore | new
    credential: str|none    # 필요 키(있으면 main 에 요청)

# 블록7: CODE_CHANGE_PLAN (★§4 4단계 코드를 어디를 어떻게 바꿀지 — 구체)
# 4단계(learn/card/inject/falsify) 각각 최소 1개. §4 표를 실제 Read 한 뒤 작성.
code_change_plan:
  - stage: enum            # learn | card | inject | falsify
    file: str              # 정확한 파일 (예: core/data/weight_panel.py)
    symbol: str            # 함수/클래스 (예: build_indicator_matrix)
    current: str           # 현재 동작 1줄 (Read 해서 확인한 사실)
    change: str            # 이 자산군 때문에 바꿀 내용 (구체적·실행 가능)
    risk: str              # SACRED 저촉 여부 + 무회귀 방법(추가만/opt-in/self-test)
```

추가로 `summary.md`(사람이 읽는 요약: 일반론·보고서 핵심 + 결정·기각 사유) 1개.

---

## §4. 4단계 파이프라인 코드 — 정확히 읽고, 단계별 변경 계획을 가져온다

⛔ 추상 금지. 아래 4단계 각각에 대해 **(a) 지정 파일·함수를 실제로 Read** 하고, **(b) 당신
자산군 때문에 무엇을 바꿀지 §3 블록7 code_change_plan 에 파일:함수:변경내용으로** 적는다. 4단계
전부 채운다(해당 없으면 사유 명시). 4단계는 정확히 4개다 — 학습 / 규칙화 / 주입 / 해제.

### ① 학습 (learn) — regime 조건부 상관·비중을 데이터에서 추정
| 파일 | 핵심 심볼 | 현재 동작 | 당신이 바꿀 것(예시) |
|---|---|---|---|
| `core/data/weight_panel.py` | `build_indicator_matrix(store, series_ids, periods, as_of)` (L100~), `_REFLEXIVE_WORDS` 반사성 게이트(L53~83) | series_ids 로 시점×지표 PIT 행렬 조립. 포지션/체결/PnL 단어 차단 | **블록2 indicators 의 id 들을 이 자산군 series_ids 로 등록**. 반사성 게이트 통과 확인 |
| `core/structure/conditional_correlation.py` | `RegimeGlasso.fit(X, regime_ids)` (L237~), `effective_precision(models, belief)` (L318~), `fit_glasso_ebic` | nonparanormal→EBIC glasso→EB shrink→Ω_eff. 단일 λ | **블록3 relationships(partial-corr prior)를 corr_prior 로 주입**. 이론 강한 ≤4 엣지는 force-include 후보 |
| `core/assume/weight_cycle.py` | `GlassoWeightLearner.fit / omega_eff(belief) / ic(returns)` (L46~82) | 학습 래퍼: Ω_eff·Rank-IC 산출 | 이 자산군 forward return 정의(ic 입력). 종목/산업 단위 패널 분할 시 fit 호출 단위 |
| `scripts/train_weights.py` | `train_weight_cards(...)` (L79~131) | 배치: 패널→regime_history→glasso→카드 등록 | 이 자산군 scope/series_ids 로 배치 1건 추가(domain, scope 인자) |

### ② 규칙화 (card) — 학습 결과를 평가 규칙 카드로 박제
| 파일 | 핵심 심볼 | 현재 동작 | 당신이 바꿀 것 |
|---|---|---|---|
| `core/assume/weight_card.py` | `WeightAssumptionCard`(L64~), `derive_weights(omega, ic, blend_1n, cap)`, `composed_weights(pi)`(L115~), `synthesize_l1(z, w, floor)` | w∝Ω·IC + 1/N + cap. regime별 비중 카드 | **카드 scope 를 regime별 → industry/ticker 로 세분**(블록4 granularity). **블록1 lens(정성 렌즈)를 카드 필드로 추가**(③에서 LLM 주입). 이 자산군 cap/floor 정책 |
| `core/assume/registry.py` | `AssumptionRegistry.register / get(id, as_of)` | 카드 버전드 보관 + PIT 조회 | 이 자산군 카드 id 규약(`weight.{scope}.{regime}` → 종목 단위 키) |

### ③ 주입 (inject) — 카드 비중으로 종목 사이징 + 렌즈 LLM 주입
| 파일 | 핵심 심볼 | 현재 동작 | 당신이 바꿀 것 |
|---|---|---|---|
| `core/stock_track.py` | `_apply_r15_sizing`, `_resolve_weight_card(state)`, `_extract_indicator_z` | 종목 buy 때 S_L1=clamp_floor(Σwᵢzᵢ) 사이징, 천장 불변식 | **`_extract_indicator_z` 가 이 자산군 지표 z 를 뽑게 확장**. **블록4 modulate_by(regime/industry/size/ticker)를 사이징에 반영**. 렌즈를 LLM judge 입력으로 |
| `core/assume/judge.py` | `synthesize_l1` 호출부, 천장 불변식(`assert_ceiling_invariant`) | L1 결정론 사이징 + LLM down-only 감쇠 | LLM 평가 시 블록1 lens 주입 경로(judge 컨텍스트). down-only 보존 |
| `core/brain/regime_to_weights.py` | `regime_to_weights`, `_belief_conditional_cov` | belief 동적 공분산 BL 배분(sleeve) | 이 자산군이 신규 sleeve(예: intl)면 SLEEVES/SLEEVE_BLOC 등록 |

> coin 은 예외: 지표가중 부적합 → `core/coin_track.py` 에서 belief→사이징 조절만. ①②③ 미적용.

### ④ 해제 (falsify) — 예측력 붕괴 시 카드 약화·폐기 (확신/거부 flag 누적)
| 파일 | 핵심 심볼 | 현재 동작 | 당신이 바꿀 것 |
|---|---|---|---|
| `core/assume/weight_falsification.py` | `rank_ic`(L51~), `score_ic_breakdown_eprocess`(L66~ e-CUSUM 단측), `omega_drift`(L89~) | PRIMARY=score IC 붕괴 kill / SECONDARY=Ω drift re-fit | **블록5 confidence_hooks 를 여기 매핑**: confirm_signal=IC 유지 / reject_signal=e-CUSUM 단측 붕괴. 이 자산군 임계 |
| `core/assume/update_controller.py` | `retract_now`(L50~), `UpdateController.step`(L90~) | retract=빠름(disjunctive) / adopt=느림(5조건 AND) | 이 자산군 가정의 adopt dwell·K-window 파라미터 |

> **종목별로 잘게가 핵심**: 현재 카드는 regime별이다. 당신 산출은 이를 industry/ticker 까지
> 세분화해 "어떤 지표 가중치를 어떤 상황(국면×산업×종목특성)에서 어떻게 바꿀지"(블록4) +
> 그걸 위 4단계 어디를 어떻게 고칠지(블록7)를 모두 담아야 main 이 코드로 조립한다.

---

## §5. 작업 폴더 규칙

모든 방의 raw + 요약을 한 곳에 모은다:
```
study-research/
  {study_id}/              # 예: study-research/eq_us_cyclical/
    direction.md           # ★2-1 방향성(①이론수집 ②검증방향 ③가설초안) — main 승인 대상
    study_session.yaml     # 7블록 산출 계약(2-3 완료 후)
    summary.md             # 사람용 요약
    raw/
      round-{N}.md         # ★2-1 자문 다회 라운드 원문(누적, 강제)
      theory-notes.md      # ★2-2 이론 정리(가격결정 원리·지표 관계도, 강제)
      validation-{지표}.md # ★2-3 실데이터 시계열 검증 근거(상관·regime·Rank-IC, 강제)
```

---

## §6. 주식 통일 하드룰 (equity.* 자산군 공통 — 통일성 강제)

모든 주식 방(us/kr/intl/reit)은 아래 **코어셋을 동일하게** emit(is_core: true). 비교 가능성 보장:
- **Valuation**: forward E/P (자기 히스토리 z)
- **Quality**: ROE·margin trend
- **Revision/Growth**: earnings revision breadth, fwd EPS momentum
- **Momentum**: 12-1 가격 모멘텀
- **Macro sensitivity**: rate / dollar / oil / credit beta
- **Risk**: realized vol

자산군 특화 지표(예: REIT 의 FFO·cap rate)는 추가하되 `is_core: false` + weight cap. 단 REIT 의
native 지표가 부당하게 캡되면 main 에 sleeve 승격을 요청하라(부호 상충/조건부상관 decoupling/신호
스택 발산 = 3-test 중 하나).

---

## §7. 자료 수집 현황 (있는 것 / 끌어올 것)

**이미 있음**(그대로 쓰면 PIT 자동 보호 — VintageStore/FxStore/IdentityStore 3중 게이트):
- 거시: FRED 86 시리즈 + ALFRED vintage (`core/brain/fred_adapter.py`)
- 주식 펀더멘털: DART(한국, `dart_provider.py`) / EDGAR(미국, `edgar_provider.py`)
- KRX 상태: 관리/상폐/거래정지 일별 (`krx_universe.py`)
- coin: Upbit 가격 + CoinMetrics MVRV

**main 이 선구축 중**(무료·즉시): WICS 업종 분류, 외국인 순매수(pykrx), HY OAS 스프레드(FRED
`BAMLH0A0HYM2`), Ken French 팩터, US ETF holdings, DXY/USDKRW(FxStore PIT 적재).

**없음 → 당신이 블록6 에 적어 요청**: ECOS 한국 거시(키 대기), REIT FFO/cap rate(유료 소스),
국가지수 ETF NAV/TR, 그 외 자산군 특화 자료.

**새 수집기 인터페이스**: `VintageProvider.realtime(series_id, period, as_of)` 또는
`FundamentalsProvider.fetch_filings(ticker, limit)` 구현 → 자동 PIT 보호.

### §7-1. 자산군별 리서치 소스 (자문 추천 — 종목마다 다르다. 다 쓴다)

①② 일반론·리포트 = **`/gemini-web` + `/claude-web` 병렬 자문**으로 정리(공개 repo 없는 Investment
Clock·M2-금리 관계도 등은 자문 지식으로). 웹 보고서 원문은 `raw/` 저장. ③ = 우리 DB(아래).

| study_id | 자문 추천 OSS·외부 소스 | 우리 시스템 DB(수집기) |
|---|---|---|
| `macro` | fredapi/FRED ALFRED, ECOS(한은), MarketMoodRing(MIT regime), Investment Clock(지식) | `fred_adapter`(17종+HY OAS), +DXY/USDKRW(선구축), VintageStore |
| `eq_us_cyclical` / `eq_us_defensive` | GICS 11 sector, Damodaran 멀티플, Ken French 팩터, FinanceDatabase(MIT) | EDGAR 펀더멘털, +French·ETF(선구축), `sector_multiples` |
| `eq_kr` | WICS(FnGuide), pykrx, FinanceDataReader(MIT), FinanceData/stock_master | DART, KRX 유니버스, +WICS·외국인순매수(선구축) |
| `eq_intl` | FinanceDataReader(국가지수 ETF), FinanceDatabase(DM/EM) | +US/국가 ETF holdings(선구축), UniverseStore |
| `reit` | GICS RealEstate, NAREIT/리포트(FFO·cap rate 공개치) | EDGAR 일부 → 부족분 블록6 요청 |
| `commodity` | FRED(real rate/재고/PMI), 리포트(carry·backwardation) | Yahoo(`collect_macro`), `commodity_assumptions` |
| `gold` | FRED real rate, monetary/FX hedge(지식) | Yahoo, FRED |
| `bond_cash` | FRED 금리커브·HY OAS, 듀레이션(계산), 리포트 | `fred_adapter`+HY OAS(선구축) |
| `crypto` | CoinMetrics on-chain, CoinMarketCap, Upbit | Upbit, MVRV, CMC |

각 방은 **자기 행의 외부 소스 + 우리 DB 를 둘 다 명시적으로** 블록2 `source_or_collector` /
블록6 `collector_plan` 에 적는다. 자문 raw 메모리: `~/.claude/memory/research/multiasset-taxonomy-regime-oss.md`.

---

## §8. 자문 설계 결론 (3R saturation — 따를 것)

- **아키텍처 = 조건부 모델(cglasso)**: `asset_core | macro ~ N(B·macro, Ω_asset⁻¹)`. 거시+자산을
  한 행렬에 다 넣는 Block Matrix 는 금지(소표본 N≈45 과적합). 거시 driver 2-4개(credit/real
  rate/dollar/oil)만 named 채널, 나머지 거시는 regime 조건키.
- **관계는 partial-corr(직접효과)로**: 공통원인 C 로 매개된 A-B 는 edge=0, C→A·C→B 로 분해
  (블록3 edge_type, conditioning_set 필수).
- **prior 주입**: EBIC + EB shrinkage 가 기본. 이론 강한 ≤4 엣지만 force-include 화이트리스트.
- **REIT**: 지금은 equity sub-panel(승격은 측정 기준 충족 시).

---

## §9. 작업 종료 시
1. `study_session.yaml`(7블록) + `summary.md` + `raw/` 완성.
2. main(btn-Codlearn)에 **방향성 보고**(§0 psmux 헬퍼): 핵심 발견 + 제안 + 막힌 점.
3. main 이 전체 통합 후 3R 자문 → 이상 없으면 각 방이 코드 구현 착수.

---

## 부록 A. 완전 예시 (`macro` 자산군) — 이걸 본떠 채운다

> lens 가 무슨 내용을 담는지, flag 를 어떻게 코드화하는지 구체 예시. 당신 자산군에 맞게 변형.

```yaml
study_id: macro
asset_scope: [macro]
as_of: "2026-05-30"

# 블록1 LENS — 정성 렌즈(일반론+리포트의 정제. LLM 평가 시 주입됨)
lens:
  pricing_principle: >
    거시 자산가격 = 성장·인플레·유동성·리스크프리미엄의 조합. Investment Clock 4국면
    (Reflation/Recovery/Overheat/Stagflation)이 자산군 우위를 가른다.
  report_relations:
    - "통화량 M2 확대 → 위험자산 선호. 단 인플레 동반 시 미국채 금리↑ → 멀티플 압박"
    - "일본 국채(BOJ 정책금리/YCC) ↔ 엔캐리 ↔ 글로벌 유동성 ↔ 신흥국·위험자산"
    - "10Y-2Y 역전 → 경기침체 선행(12~18개월 lag)"
    - "HY OAS 확대 → 리스크오프 regime 신호(주식·크레딧 동반 약세)"
  regime_reading: >
    Reflation(성장↑인플레↓): 주식·원자재 우위, 채권↓. Stagflation(성장↓인플레↑): 금·현금·단기채 우위.
  estimation_note: >
    2024-Q4 이후 커브 역전 해소 + HY OAS 안정 → Recovery 초입 추정(확신도 중). 이 시각 이후
    재평가 anchor 로 표시.

# 블록2 INDICATORS
indicators:
  - {id: yield_10y_2y, family: macro_driver, is_core: true, in_our_system: true,
     source_or_collector: "fred_adapter FRED_SERIES[T10Y2Y]", transform: level, vintage_policy: point_in_time, lag: 0}
  - {id: credit_spread_hy_oas, family: macro_driver, is_core: true, in_our_system: true,
     source_or_collector: "fred_adapter[BAMLH0A0HYM2] (main 선구축)", transform: own_history_z, vintage_policy: point_in_time, lag: 0}
  - {id: usdkrw, family: macro_driver, is_core: false, in_our_system: false,
     source_or_collector: "main 선구축 FxStore", transform: yoy, vintage_policy: point_in_time, lag: 0}

# 블록3 RELATIONSHIPS (partial-corr 기준)
relationships:
  - {node_a: credit_spread_hy_oas, node_b: yield_10y_2y, edge_type: direct,
     conditioning_set: [real_gdp], lag_routing: contemporaneous, prior_sign: pos, prior_strength: 0.6,
     theory_basis: "리스크오프 시 HY 스프레드 확대 + 커브 베어 플래트닝 동반"}

# 블록4 WEIGHT_RULES (최종 산출 — 종목/sleeve별 동적 가중)
weight_rules:
  - {indicator_id: credit_spread_hy_oas, base_weight: 0.25, modulate_by: [regime],
     direction: "리스크오프 국면 → HY OAS 가중↑(방어 강화)", granularity: sleeve}

# 블록5 CONFIDENCE_HOOKS (flag 코드화)
confidence_hooks:
  - hypothesis_id: hy_oas_risk_regime
    confirm_signal: "HY OAS 확대 시 위험자산 축소가 OOS outcome 에서 수익 방어(Rank-IC 양)"
    reject_signal: "HY OAS 신호 Rank-IC e-CUSUM 단측 붕괴"
    emit_where: "backtest/engine SELL outcome + 라이브 judge 사후평가"
    accumulate_in: "core/assume/weight_falsification.score_ic_breakdown_eprocess"
    confidence_metric: "e-value anytime-valid 누적"
    store: "registry 카드 confidence_now + RulePerformance"
    action_threshold: "e-value>K → adopt 강화 / 붕괴 → retract(live 차단)"
    feeds_weight: "신뢰도 변화 → derive_weights 재적합으로 base_weight 미세조정"

# 블록6 COLLECTOR_PLAN
collector_plan:
  - {missing: "ECOS 한국 M2/거시", source: "ECOS API", interface: VintageProvider, credential: ECOS_API_KEY}
  - {missing: "일본 국채 금리(JGB)", source: "FRED IRLTLT01JPM156N", interface: VintageProvider, credential: none}

# 블록7 CODE_CHANGE_PLAN (4단계 전부)
code_change_plan:
  - {stage: learn, file: core/brain/fred_adapter.py, symbol: FRED_SERIES,
     current: "16 시리즈(HY OAS main 추가)", change: "JGB 등 관계도 노드 추가", risk: "dict 추가만 무회귀"}
  - {stage: card, file: core/assume/weight_card.py, symbol: WeightAssumptionCard,
     current: "regime별 정량 비중 카드", change: "lens(report_relations) 정성필드 박제→judge 주입", risk: "필드 추가, 미제공시 무회귀"}
  - {stage: inject, file: core/assume/judge.py, symbol: synthesize_l1 호출부,
     current: "L1 사이징+LLM down-only", change: "카드 lens 를 LLM 컨텍스트 주입", risk: "opt-in, down-only 보존"}
  - {stage: falsify, file: core/assume/weight_falsification.py, symbol: score_ic_breakdown_eprocess,
     current: "e-CUSUM 단측 kill", change: "HY OAS regime flag confirm/reject 누적 연결", risk: "추가만 self-test"}
```

## 부록 B. 종목 단위 세분화 = hierarchical pooling (obs 부족 회피)

종목별 카드를 따로 학습하면 obs 가 절대 부족하다(regime당 45 도 빠듯). 그래서 종목 세분화는
**`weight_card.composed_weights(pi)` 의 계층 풀링**으로 한다:
`종목 가중 = w_global(전체) + delta_regime(국면) + delta_arch(산업 archetype) + ticker shrinkage`.
블록4 `granularity: ticker` 는 "ticker마다 독립 학습"이 아니라 "산업 prior 에서 종목으로 shrink"를
뜻한다. 산업(archetype) 레벨에서 학습하고 종목은 soft membership(pi)로 보간한다.
