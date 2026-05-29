# Inv Brain — 의사결정 + 적응 학습 아키텍처

거시·주식·상품·crypto를 단일 asset-agnostic 코드 경로로 다루는 실거래 시스템의 **Brain**.
핵심: "지표로 상황(거시 국면)을 읽고, 지표가 정의대로 안 움직이면 감지·학습해 평가 기준을
조정"하는 의사결정 + 적응 학습 메타레이어.

> 본 문서는 **Brain 부분**(의사결정·학습 루프). 나머지(Data/PIT·Execution·Backtest·Risk Gate)는
> 별도 작성 예정. README.md는 현재 레거시 코인 봇 문서 — 통합본 교체는 사용자 확인 후.

---

## 1. 의사결정 파이프라인 (순서 불변식 = 안전의 핵심)

종목/자산 하나의 매수·매도·사이징은 **결정론 L1 → agent/LLM down-only 감쇠** 순서로 흐른다.
이 순서가 뒤집히면 LLM 환각이 베팅을 키우므로, 순서를 코드 구조로 박았다.

```
  [지표 벡터 z]                          ← FRED/KIS/DART (PIT vintage)
       │
   ┌───▼─────────────────────────────┐
   │ L1 (결정론, pre-LLM·pre-agent)    │  S_L1 = clamp_floor(Σ wᵢ(거시국면)·zᵢ)
   │  · 단일 cheapness_z  또는          │  ← R15 학습 비중 wᵢ (거시 국면·산업 archetype 조건부)
   │  · R15 다중지표 가중 합성 S_L1     │
   └───┬─────────────────────────────┘
       │  l1_size = sizing 상한 (천장)
   ┌───▼──────────┐   ┌──────────────┐
   │ DCF (절대가치) │ ∥ │ L1 floor veto │   disjunctive veto (하나만 죽여도 차단)
   │  = down-only   │   └──────────────┘
   │    veto/kill   │
   └───┬──────────┘
       │
   ┌───▼──────────────────────────────┐
   │ L2 (Qwen 맥락)  ×  L3 (BGE 사례)   │  a₂,a₃ ∈ [0,1]  (monotone-down attenuator)
   └───┬──────────────────────────────┘
       │
   final_size = l1_size · a₂ · a₃   ∈ [0, l1_size]   ← 천장 불변식: LLM/agent는 절대 증폭 못 함
```

- **BGE(L3)** = 임베딩 유사사례 검색. 부정 사례 다수 → 사이징 감쇠. 긍정/결측 = 감쇠 없음(증폭 X).
- **Qwen(L2)** = 경량 LLM 맥락. 현 정의가 S→S' 전환 정황이면 사이징 감쇠.
- **DCF(agent)** = 내재가치 절대축. `valuation_gap < -0.30` → veto(kill). **긍정 gap이 사이징을
  키우는 경로는 코드에 없음** = 이미 down-only.
- **fail-safe**: L2/L3가 제공됐는데 장애(timeout/error)면 `a=1.0`(fail-open)이 아니라
  **abstain(사이징 0)**. 장애 시 베팅을 키우는 역방향을 구조적으로 차단.

→ **핵심 불변식**: `final ≤ l1_size`. LLM/agent는 L1 결정론 사이징을 **깎기만** 한다. judge가
매 호출에서 `assert_ceiling_invariant`로 강제.

## 2. 적응 학습 루프 (지표 → 상황 → 정의 변화 학습 → 기준 조정)

```
  지표 관측 → 상황(regime) 읽기 → 정의대로 안 움직임 감지(decoupling)
     → 정의 S→S' 전환 학습 → 평가 기준(가정 카드) 조정 → 재적용
```

두 축으로 구현:

**(A) 가정 라이프사이클** (`core/assume/`) — 정의의 S→S' 전환을 버전드로 관리
- 모든 "가정"은 정량 **반증 조건(falsification_metric)** 필수. 반증 불가 = 가정 아님 → 등록 거부.
- 강한 반증 1개 → **즉시 retract**(live 노출 차단). 노이즈성 변화 → adopt 게이트(5조건 AND)로
  느리게 정의 전환. base-layer(regime 정의 등) → 사람 비준.

**(B) R15 가중 학습** (`core/assume/weight_card.py` + `core/structure/conditional_correlation.py`)
— "어떤 지표를 얼마나 볼지"(평가 기준 비중)를 **거시 국면·산업 사이클 조건부로 동적 조절**
- 거시 국면(regime)별로 지표 간 조건부 상관(sparse precision Ω)을 학습한다. **같은 지표라도
  거시 상황이 다르면 상관·비중이 달라진다** = 사용자 핵심 요구.
- belief b(t)(현재 거시 상황 확신도)에 따라 Ω가 동적으로 섞이고(`effective_precision`), 그
  비중으로 L1 합성 score `S_L1`을 만든다.
- production 흐름: **학습은 배치**(`scripts/train_weights.py`) → registry 영속, **적용은
  라이브 조회**(`stock_track`이 카드 조회 → sizing). 매 사이클 학습 금지(무겁고 반사성 위험).

## 3. 핵심 코드 (성격 + 왜 이렇게 짰는가 — 수정 전 필독)

| 파일 | 성격 | 판단 근거 (이유) |
|---|---|---|
| `core/assume/judge.py` | 3층 판정 결합 (L1∥DCF + L2/L3 attenuator) | LLM을 **safe-by-construction**으로. L1 결정론이 sizing 상한, LLM은 감쇠만 → 환각이 베팅 못 키움. |
| `core/assume/weight_card.py` | R15 가중 카드 + `derive_weights`(Ω·IC) + `synthesize_l1`(clamp_floor) | 정적 Investment Clock 표를 **거시 국면 조건부 동적 비중**으로 대체. floor는 학습과 **분리된 primitive**(학습 갱신이 진입 임계를 못 흔듦 = 지표별 falsifiability 보존). |
| `core/assume/weight_falsification.py` | DUAL 반증 (PRIMARY=score IC 붕괴 kill / SECONDARY=Ω drift re-fit) | Ω가 흔들려도 score 예측력이 견디면 비중은 robust → 구조 drift만으로 kill하면 과민. 분리. |
| `core/assume/weight_cycle.py` | 4단계 production 오케스트레이터 (학습→비중→주입→해제) | seam을 실코드로 잇는 누락 글루. `GlassoWeightLearner`가 통계 산출을 캡슐화. |
| `core/structure/conditional_correlation.py` | regime-conditional Graphical Lasso + belief-mix + calibration | HMM/DCC 기각(regime 외생·소표본 최악). EBIC glasso + nonparanormal(fat-tail) + EB shrinkage(소표본 과적합 방어, λ floor=self-confirming attractor 차단). |
| `core/brain/regime_belief_adapter.py` | 거시 상황(MacroView) → belief b(t) 분포 | confidence 높으면 국면 집중, 낮으면 평탄 → 모호할수록 자동 de-risk(transition 위험 흡수). |
| `core/brain/regime_history.py` | `classify(as_of)` PIT 반복 → 시점별 regime substrate | RegimeGlasso 학습 입력(어느 시점이 어느 국면이었나). FRED ALFRED vintage로 lookahead 차단. |
| `core/brain/regime_to_weights.py` | 자산 슬리브 배분 (Investment Clock + Black-Litterman) | **R15 가중(평가 지표)과 다른 레이어**(자산 배분). 혼동 금지. R15는 종목 *판정* 비중, 이건 *배분*. |
| `core/assume/registry.py` | 가정 카드 버전드 보관 + PIT 조회 + lifecycle emit | append-only. 과거 결정 재현(replay) = 정확 버전 고정. |
| `core/assume/update_controller.py` | adopt(느림)/retract(빠름) 비대칭 게이트 | 반증된 가정을 dwell 기다리며 live 노출하면 치명적 → retract는 disjunctive fast. |

## 4. 설계 원칙 (불변식 — 깨면 안 됨)

1. **down-only**: LLM/agent는 L1 결정론 사이징을 감쇠만, 증폭 절대 불가 (`final ≤ l1_size`).
2. **falsification 필수**: 모든 가정 카드는 정량 반증 조건 보유. 없으면 등록 거부.
3. **PIT replay**: 카드·비중·belief는 hash-pinned frozen. 과거 결정 정확 재현, lookahead 차단.
4. **floor 분리**: `clamp_floor` 진입 임계는 학습과 분리된 비학습 primitive.
5. **학습/적용 분리**: 학습은 배치(offline), 라이브는 조회만(down-only). 반사성 차단.
6. **opt-in off 기본**: 라이브 결정 경로 변경은 환경변수 flag(`INV_R15_WEIGHTS` 등) off 기본 =
   byte-identical 무회귀. `DRY_RUN`/`execute_trade`는 절대 미변경(go-live 사람 게이트).

## 5. R15 production 배선 상태

- ✅ ① regime 히스토리 substrate 빌더 (`regime_history.py`)
- ✅ ② 배치 학습 → registry 영속 (`scripts/train_weights.py`)
- ✅ ③ stock_track 라이브 조회 → 주식 판정 sizing (`stock_track._resolve_weight_card`/`_apply_r15_sizing`)
- ⏳ ④ 자산 배분(슬리브) belief 동적 공분산 — 슬리브 regime 히스토리 substrate + `regime_to_weights`
  BL cov 주입 필요(자문 §1.10). 주식 판정 핵심(①②③)과 별개 레이어.
- ⏳ go-live: 라이브 stock entrypoint 활성화(현 `run_agents`=coin 전용), `DRY_RUN=false` flip(사람 게이트).

> 전제: `.env`에 FRED/DART/ECOS/KIS 키 보유 시 production에서 substrate 정상 확보. (개발 샌드박스는
> 외부망 차단으로 실데이터 호출만 불가 = 검증 제약, 기능 부재 아님.)
