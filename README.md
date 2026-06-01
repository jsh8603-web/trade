# 통합 투자 시스템 (Inv) — 암호화폐 + 주식 자율매매

> 기존 단일자산(BTC) 코인 봇을 **asset-agnostic 코어**로 일반화하고 주식 트랙을 얹은 멀티에셋 자율매매 시스템.
> 매매 로직을 코드로 하드코딩하지 않고, **결정론 baseline + LLM down-only 감쇠 + 우회 불가 리스크 게이트**로 안전을 코드 구조에 박았다.

이 문서는 `architecture.md`(목표 아키텍처·Phase 로드맵)와 `ARCHITECTURE-brain.md`(두뇌 의사결정·학습 루프)를 베이스로, 구현된 전체 코드의 핵심 모듈·속성·**설계 결정 이유**를 기능 영역별로 정리한 통합 레퍼런스다.

---

## 📌 개요

crypto·주식·상품·채권을 **단일 코드 경로**로 다루는 실거래 시스템이다. 핵심 설계 철학 두 가지:

1. **결정론이 baseline, LLM은 enrich/감쇠만.** 평상시 무료 결정론 점수가 깔리고, LLM(Qwen 로컬/Claude deep)은 고-스테이크스 트리거 때만 호출되며, **사이징을 키우지 못하고 깎기만** 한다(`final ≤ l1_size` 천장 불변식). LLM 환각이 베팅을 키우는 경로가 코드에 존재하지 않는다.
2. **불확실하면 자동 de-risk.** confidence가 낮거나 데이터가 없으면 belief 분포가 평탄해지고, 그 평탄함이 자산배분·사이징 단계에서 분산·중립화로 흘러간다(수학이 위험을 줄이고 사람 개입 0).

> **현재 라이브 = 레거시 코인 봇**(`agents/` + `scripts/run_agents.sh`). 신규 `core/` 아키텍처는 `INV_CORE_GATE` 옵트인 백스톱으로 연결되며, 기본 off에서는 레거시 경로가 byte-identical하게 유지된다. 실거래 전환(`DRY_RUN=false`)과 90일 무중단은 **사람 게이트**(자율 범위 밖)다.

---

## 🏛️ 목표 아키텍처

```
                  [Portfolio Orchestrator]   ← 자산배분 (코인/주식/현금 비중)
                  레짐 + 상관도 기반, 트랙 간 자본 한도 배분
                          │
        ┌─────────────────┴─────────────────┐
   [Coin Track: 기존 흡수]            [Stock Track: 신규]
   AssetTrack 구현체                  AssetTrack 구현체
   - 모멘텀/심리/레짐 트리거(기존)      - 가치기반 2단 트리거(신규)
   - BTC 단일                          - KR/US 개별주 + ETF
        │                                      │
        └─────────────────┬─────────────────┘
              [Shared Risk Gate]   ← 우회 불가, hard rule
              포트폴리오 손실한도 / 상관도 캡 / 회전율 / kill switch
                          │
        ┌─────────────────┴─────────────────┐
   [Coin Exec: 기존]                 [Stock Exec: 신규]
   업비트 / 바이낸스                  한국투자증권(KIS)
```

흐름은 한 방향으로 고정된다 — **자산-불가지 트랙(AssetTrack)이 후보 결정 생성 → (고-스테이크스 시) consensus Judge → 우회 불가 공통 리스크 게이트 → 멀티에셋 사이징 → 주문**. 최상위에 슬리브(US주/KR주/원자재/금/채권/현금/코인) 배분을 책임지는 포트폴리오 오케스트레이터가 있다.

---

## 🧭 설계 철학 / 핵심 불변식

**6대 보존 원칙** (전 트랙 유지·확장 — `architecture.md` §0):
점수 투명성(score breakdown) · 자연어 전략(`strategy.md`) · JSON 결정 스키마 · 감사 테이블 · DRY_RUN 게이팅 · 수동 EMERGENCY_STOP 우회 불가.

**두뇌·결정 6대 불변식** (`ARCHITECTURE-brain.md` §4):

1. **down-only**: LLM/agent는 L1 결정론 사이징을 감쇠만, 증폭 절대 불가(`final ≤ l1_size`).
2. **falsification 필수**: 모든 가정 카드는 정량 반증 조건 보유. 없으면 등록 거부.
3. **PIT replay**: 카드·비중·belief는 hash-pinned frozen. 과거 결정 정확 재현, lookahead 차단.
4. **floor 분리**: 진입 임계(`clamp_floor`)는 학습과 분리된 비학습 primitive.
5. **학습/적용 분리**: 학습은 배치(offline), 라이브는 조회만(down-only). 반사성 차단.
6. **opt-in off 기본**: 라이브 결정 경로 변경은 환경변수 flag off 기본 = byte-identical 무회귀. `DRY_RUN`/`execute_trade`는 절대 미변경(go-live 사람 게이트).

---

## 🧠 두뇌(Brain) 레이어

두뇌 레이어(`core/brain/`)는 "지금이 어떤 거시 국면이고, 그 판단을 얼마나 믿을지"를 결정하는 메타 추론 계층이다. crypto·주식·상품·채권을 단일 asset-agnostic 경로로 다루며 세 가지 일을 한다 — (1) **LLM 호출 라우팅**(평상시 로컬 Qwen, 위기 트리거 시 Claude deep), (2) **거시 레짐 판단**(FRED 지표로 Investment Clock 4분면을 매 사이클 결정론으로 산출), (3) **학습 메모리**(지표가 정의대로 안 움직이는 decoupling을 감지·기록해 다음 판단의 신뢰도를 보수화).

핵심 철학은 둘이다. 첫째, **결정론 baseline이 항상 깔리고 LLM은 enrich만 한다** — 매 사이클 `RegimeClassifier`가 무료·결정론으로 `MacroView`를 채우고, LLM은 macro-trigger가 있을 때만 stance를 덧붙인다(freshness ≠ liveness). 둘째, **불확실하면 자동 de-risk** — confidence가 낮거나 데이터가 없으면 belief 분포가 평탄해지고, 그 평탄함이 자산배분 단계에서 분산·중립화로 흘러간다.

#### macro_schema
거시 출력의 공통 계약(SSOT). `MacroView`(per-bloc `RegimeEstimate` dict + stance + status + age + 근거)를 정의한다.
- **불변식**: `RegimeLabel`은 정확히 Investment Clock 4분면(REFLATION/RECOVERY/OVERHEAT/STAGFLATION). `regime_now`(classifier)와 `regime_forecast`(forecaster)를 명시 분리 — 둘이 다르면 `is_disagreement()`가 레짐 전환 임박 신호.
- **신선도 3단계**: `FRESH/STALE/UNAVAILABLE`. 소스 outage 시 `degrade_to_stale()`로 last-good 재사용(청산·리밸런싱은 계속), 없으면 `unavailable()`(빈 view → 하류 중립 Prior degrade).

#### macro_indicators
`macro.md` 리서치의 정량 법칙·임계를 **순수함수**로 코드화. PIT-safe(발표일 정렬, 미래 미참조).
- `michez_rule(u, v)` — Michaillat-Saez `m(t)=min(û,v̂)`, 이중 임계로 expansion/probable/certain 3단. 이민 공급충격으로 실업률만 치솟아도 구인 하락폭이 작으면 오경보 차단(Sahm 직접 대체).
- `gdp_gdi_divergence` — GDP<0<GDI면 기술적 침체 오경보로 단정 보류. `yield_curve_signal` — 역전/스티프닝 구분(역전=침체 직행 아님). `investment_clock_quadrant(growth, infl)` — 4분면 라벨 + `tanh(√|g·i|)` 신뢰도(경계 근처면 낮게 → reasoning 에스컬레이션).

#### fred_adapter
FRED/ALFRED vintage 데이터의 경계(실제 호출은 `fredapi`, 본 모듈은 큐레이션·PIT 계약·인터페이스).
- **PIT 불변식**: `get_series(id, as_of)`는 as_of까지 *발표된* 값만(causal mask). `first_release`(핫패스) / `vintage`(백테스트). `USREC`(NBER)는 학습 라벨 전용(실시간 추론 금지).
- graceful degrade: `NullFredAdapter`(키/네트워크 없음 → None) → 분류기가 stale/unavailable로 강등.

#### regime_classifier
결정론 거시 레짐 분류기 — brain의 매 사이클 무료 baseline.
- 파이프라인: 피처 적재 → Investment Clock 4분면 baseline → **JM/SJM 2상태(calm/stress) overlay** → Michez/Sahm/금리커브/GDP-GDI override → 선행지표 forecaster(classifier와 분리).
- **핵심 신호**: `_jump_model_overlay`가 JM **filter(online) vs smoother(insample)** 발산으로 confidence를 깎는다 — "실시간 판정 ≠ 사후정답" 신호로, 학습 루프가 harvest한다.
- `_apply_correlation_attenuation`이 `IndicatorEventCorrelation` 주입받아 보조지표 trigger 시 confidence 동적 하향. JM 미설치 → 규칙 단독 degrade.

#### indicator_event_correlation
"정상 상관 / 그 패턴이 깨진 이상 케이스 / 보조지표 임계 넘으면 상관 동적 약화"를 구현한 오판 피드백 루프. `MACRO_CORRELATION_BACKGROUND.md`와 1:1 연결.
- `EVENT_BASELINE`(이벤트별 지표 기대 방향) + `ANOMALY_CASES`(6+1 decoupling: 금리커브 역전 무력화·Sahm 오작동·M2-인플레 디커플링·500bp 연착륙·CPI-Truflation 괴리·GDP-GDI 단절). 각 케이스에 `SupplementarySignal`(임계·방향) + `attenuation`(0~1 곱).
- `conditional_attenuation` — 보조지표 trigger 시 attenuation 발동(바닥 0.1). López de Prado **메타라벨링**을 거시 레짐에 어댑트.
- **학습 자산**: `CorrectionRecord`(PIT-safe: `as_of_ts`=causal mask, hindsight 라벨은 학습 신호로만) + `ingest_correction`(빈도/lag 통계만, hard 재학습 금지) + `recall_similar`(as_of 이전 보정만).

#### correction_loop
`indicator_event_correlation`의 dead였던 학습 쓰기 경로를 live 루프로 배선.
- `harvest_from_jm` — classifier가 버리던 JM filter/smoother 발산을 harvest trigger로 재사용, realtime vs hindsight regime 비교해 misjudgment만 `ingest`.
- `attach_to_classifier(clf)` — read(`score_confidence`)와 write(`harvest→ingest`)가 동일 model 인스턴스 공유 → 즉시 반영. harvest 시 `HOLD_REMEASURED` 이벤트 dict 반환(ledger I/O는 호출자).

#### regime_belief_adapter
`MacroView`(거시 판정)를 R15 가중 학습의 **belief 분포 b(t)**로 변환.
- `belief_from_macro_view(view)` — `regime_now`에 `confidence_now` 질량, 나머지 균등 + floor, 합=1. **confidence 高 → 집중, 低 → 평탄**(= between-dispersion 자동 inflate → transition de-risk).
- `belief_vector` — 고정 순서 tuple 박제(replay 불변). `calibrated_belief` — frozen TemperatureCalibrator 주입. unavailable → uniform(최대 불확실 = 자동 de-risk).

#### regime_history
`RegimeClassifier.classify(as_of=과거)`를 패널 각 행 날짜에 PIT 반복 호출해 "각 시점이 어느 국면이었나" 재구성(`RegimeGlasso.fit` 입력).
- `build_regime_history(clf, dates)` → `{as_of: label}`. ALFRED vintage라 lookahead 차단. `regime_id_series`/`valid_mask` — label→int, 미지 regime(None)은 -1로 완전관측 행만 학습.

#### regime_to_weights
레짐 → 슬리브 % 배분(Black-Litterman 메인, IC-prior 폴백). **⚠️ R15 가중(종목 판정 비중)과 다른 레이어(자산 배분) — 혼동 금지.**
- `weight_tilt`(견고, Prior + α·(View−Prior)) / `bl_returns`(PyPortfolioOpt BL 정통). confidence 낮을수록 Prior 근접, Ledoit-Wolf로 고변동 슬리브 tilt 억제, long-only 클립+재정규화, 합=1 보장.

#### macro_reasoning / llm_provider / embedder / memory_layer / rag_pit
- **macro_reasoning**: macro-trigger 시에만 baseline enrich(평상시 비용 0). thesis + 최강 반대 thesis + stance(JSON) 요청, LLM 실패/확신 부족 시 baseline 유지(C2 abstain).
- **llm_provider**: `OllamaQwenProvider`(quick) / `ClaudeProvider`(deep, **Max OAuth만 — api 키 금지**) / `GeminiProvider`(fallback). `LLMRouter.route`로 평상시 quick, 트리거 시 deep. **C2 서킷브레이커**(일일 캡·지연 예산·degrade), **B3 결정성**(`model_id`·`prompt_hash`·`temperature` 실주입). 매수 degrade = abstain(관망).
- **embedder**: da 8787 서비스 재사용(BGE-m3 1024-dim). 신규 ollama BGE 금지(임베딩 공간 보존).
- **memory_layer**: FinMem식 계층 메모리. 점수 = recency(반감기 감쇠) + relevance + importance. `update_with_outcome`로 결과 반영, 500개 초과 시 하위 20% evict.
- **rag_pit**: RAG recall에 PIT causal-mask(`created_at < as_of` + 열린 포지션 제외). `RAGPipeline` 본체 미변경, 래핑만.

#### 두뇌 레이어 설계 결정 이유
- **왜 LLM down-only·결정론 baseline**: `ARCHITECTURE-brain.md` §1·§4 — "순서가 뒤집히면 LLM 환각이 베팅을 키우므로 순서를 코드 구조로 박았다". `regime_classifier` 무료 baseline + `macro_reasoning` 트리거 enrich + `llm_provider` degrade=abstain이 구현.
- **왜 belief를 soft 분포로**: `CONSULT-DECISIONS-weight-20260529.md` §1.6 — "hard argmax는 transition에서 비중 점프·common-cause 오염", "regime 모호 시 risk 자동 inflate = transition 자동 de-risk". 모호할수록 사람 개입 없이 수학이 위험을 줄이게 한 의도.
- **왜 오판 학습이 caution 메모리(hard 재학습 아님)**: `MACRO_CORRELATION_BACKGROUND.md` §4 — "구분되는 거시 레짐 에피소드는 드뭄(2018~2026 수 건) → 보정 수십개로 hard 재학습 = 심한 과적합(PBO). 이 루프는 '훈련된 예측기'가 아니라 '지표가 이상하면 덜 확신하라'는 caution 메모리".
- **왜 HMM 대신 Investment Clock + JM/SJM**: HMM/DCC는 regime 외생·소표본 최악. NBER 라벨 후행 문제로 4분면 직접 JM 학습은 라벨 매핑 모호 → 규칙 우선 + JM 2상태 stress 메타신호 보강.

---

## 🗄️ 데이터·PIT·실거래 안전 레이어

`core/data/`는 시스템의 **데이터 substrate**다. 단 하나의 책임을 진다 — **"그때 우리가 실제로 알 수 있었던 것"만 보게 한다**. 백테스트가 미래 정보를 한 톨이라도 먹으면(미래 개정값·미래 휴장·미래 유니버스·재사용 ticker) 에러 없이 통과하고 라이브 하회로만 드러나는 silent alpha 누수가 된다. 이 레이어는 그 누수 경로를 **bitemporal 시간축**으로 전수 차단한다.

세 기둥 — ① **append-only event ledger**(`event_ledger`, 진실원) ② **PIT 데이터 substrate**(`pit_panel`/`pit_query`/`vintage`/`identity`/`calendar`/`fx`/`universe_membership`/`corp_action`/`instrument_source`/`lineage`/`data_contract`) ③ **가중학습 데이터 계층 R15**(`weight_panel`/`weight_card_store`/`cv_split`/`cold_start_ood`). 관통 검증하는 **적대적 replay 게이트**(`adversarial_replay`)와 실거래 승급 **사람 게이트**(`promotion_gate_live`)가 경계를 친다. 전 모듈이 동일 PIT 2중 게이트 규약 + append-only 불변식을 공유하고 각자 `__main__` self-test로 증명한다(전수 19 PASS / 0 FAIL).

#### event_ledger — 가정 라이프사이클 진실원 (L1)
- **12 event type**: `ASSUMPTION_CREATED`/`PREDICTION_MADE`/`OUTCOME_OBSERVED`/`REVISION_OBSERVED`(★12번째)/`FDR_DECISION`/`DATA_CONTRACT_VIOLATION` 등. `REVISION_OBSERVED`는 사후 정정을 **새 bitemporal fact**(동일 vt·새 tt·`supersedes`)로 — OUTCOME mutate 안 함.
- **3 typed timestamp 강제**: `tt`(transaction, append 불변·seq total order) / `dt`(decision) / `vt`(valid). reduce는 tt순, FDR replay는 dt순, Brier는 vt 재계산.
- **CQRS**: log=진실원 / snapshot=tt-cut reduce projection + watermark(seq). reducer 결정론 → byte-identical. frozen 이벤트, seq monotonic, crc32 변조 탐지, jsonl append+fsync, snapshot `.tmp→os.replace`.

```python
def make_event(event_type, *, tt, dt, vt, seq, ...) -> LedgerEvent  # ULID+crc 자동
def reduce_events(events, tt_cut=None) -> LedgerState
class LedgerState:
    def resolve_fact(series_key, vt, as_of) -> Optional[Fact]   # REVISION 반영 as-of
    def fdr_replay() -> list                                    # dt순 immutable
```

#### data_contract — Pandera 계약 게이트 + ingestion checksum
가정 validator **앞단**. 핵심 원칙: **계약 위반 = 측정 incident이지 "가정이 틀림"이 아니다**. 위반 시 검증 중단 + `DATA_CONTRACT_VIOLATION` emit + HOLD_SUSPENDED. PENDING(미실현)과 incident(무결성 사고)는 절대 안 섞음.
- PIT 단조성 `sys_time ≥ knowable_from ≥ effective_from`, per-series cadence-aware staleness.
- **ingestion checksum**: 벤더가 REVISION 통지 없이 과거를 덮어쓰면(`silent_rewrite`) 스키마·범위 다 통과 → (series,vt) fingerprint 보관·재대조. 정상 정정은 `REVISION_OBSERVED` 동반으로 구분.
- **WeightCard 스키마 게이트**(R15): scope 키·weight finite/cap·PIT 단조·embargo·hash 무결성.

#### pit_query / pit_panel — AS OF 조회 + bitemporal 패널
T2/T3은 **이 인터페이스로만** 조회(raw parquet 직접 필터 = PIT 우회 = 금지). DB가 PIT 강제.
- **PIT 2중 게이트**: `knowable_from ≤ as_of`(filing-lag) ∧ `sys_time ≤ as_of`(silent revision 방어). (firm,date)별 최신 sys_time = "그때 알던 값".
- **계약0 seam**(`as_of_resolver`): canonical as_of를 1곳에서 wire(track마다 갈리면 reconcile 발산). `synth_knowable_from` = max(입력)+compute_delay(입력보다 이른 가시=lookahead).
- **pit_panel**: 기존 provider(DART/EDGAR·KRX·UniverseManager)를 조립(바닥부터 X). rollback=append만(옛 row mutate 금지). `build_record`의 sys_time 기본=knowable_from(build 시각 쓰면 백테스트가 전부 막힘).

#### vintage / identity / calendar / fx / universe_membership / corp_action — PIT 소스
- **vintage**: 거시 사후 revision을 open-sequence append. `realtime(as_of)` vs `final()`(backtest에 쓰면 lookahead). `revision_drift`로 누수 정량. 자문 R1 #1 "가장 silent한 결함" 직격.
- **identity**: ticker는 안정 키 아님(recycling·합병·변경). 내부 **PSID**(재사용 금지)를 단일 join 키, `resolve_psid(id, type, as_of)` PIT. 합병은 splice 안 하고 CA 그래프 링크만.
- **calendar**: 거래소 세션을 단일 UTC 환원(tz+DST). 긴급 휴장은 knowable_from 있어 미래 휴장 foreknowledge 차단. crypto=24x7.
- **fx**: rate_date·knowable_from 2시점 PIT 환산(직접/역/USD 삼각) + 주말 fill-forward.
- **universe_membership**: 현재 구성으로 과거 조회 = 생존편향 → 시점마다 구성 append, `members_as_of`로 상폐 포함 재현.
- **corp_action**: 액면분할 back-adjust + 배당 bitemporal ledger. ★vendor Adj Close = lookahead → raw close + ledger로 **forward-only Total Return**. 연말 재분류(cash→return_of_capital)는 같은 ex_date+늦은 sys_time append.

#### instrument_source / lineage — crypto PIT provider + provenance replay
- **instrument_source**: CoinMetrics Community MVRV PIT provider + 최소 closed-loop(PREDICTION→OUTCOME→FDR). on-chain도 vintage 있어 realized-cap 재계산=REVISION. 결정일마다 as_of에 알 수 있던 최신 MVRV(미래 vt 차단)만 emit.
- **lineage**: 파생값 출처(`ProvenanceRef`) append-only + `replay(output_id, as_of)`로 그 시점 도출 체인 재구성(IA-3). **write-time 동결**: knowable_from·config_hash는 도출 시점 materialize, replay에서 재계산 금지. 순환 탐지. 가중카드 provenance도 동일 재사용.

#### weight_panel / weight_card_store / cv_split / cold_start_ood — 가중학습 데이터 (R15)
regime-conditional Graphical Lasso 학습기에 PIT-correct 입력 공급. 추정(glasso·shrinkage)은 범위 밖, 데이터 공급·무결성·누수 차단만.
- **weight_panel**: as_of 시점 지표 매트릭스(`VintageStore.realtime`, 개정 누수 차단). ★**반사성 게이트** — 과거 포지션/체결/PnL 컬럼 배제(자기 거래 결과 학습=self-confirming attractor). word-boundary 매칭으로 `book_value`·`trade_volume` over-reach 방지.
- **weight_card_store**: WeightCard bitemporal 영속 + `V(T)` selector. ★**이중 시간축**: `knowledge_time`(학습 PIT 경계) vs `decision_time`(시스템 반영). `V(T)` = 둘 다 ≤ T & embargo 충족 최신. ★**hash-pin frozen** — re-fit(신규 버전) 와도 과거 T replay byte-identical. embargo emit-time + select-time 이중 방어.
- **cv_split**: purged + embargo CV. 라벨 horizon 겹침 누수 → purge(overlap 제거) + embargo(test 직후 자기상관 차단). PurgedKFold + CPCV(다중 OOS path). ⛔ mlfinlab 금지(독점 라이선스) → 순수 numpy 자체구현.
- **cold_start_ood**: 신규 지표/국면 OOD 2축 — calibrated max-belief < θ ∨ Mahalanobis > χ²(p,1−α). ★live override 아님 — 감지 boolean만, belief 기계가 de-risk(사람 결정 0).

#### adversarial_replay — 적대적 PIT replay 1급 CI 게이트
reducer 결정론보다 강한 **시간적 결정론**을 증명. OUTCOME/REVISION에 taint-tag(sentinel)를 달고 전 seam 관통.
- **2축**: ① taint isolation(미래 REVISION이 as-of-A 산출에 0건) ② 물리부재 byte-identical(`reduce(전체, cut=A) == reduce(미래 제거, cut=A)` — cut이 실제로 미래를 안 봄 증명).
- 시나리오: 지연개정·동일 vt 다중개정·결정창 중간도착·이미소비 fact 개정 + closed-loop seam 격리.

#### promotion_gate_live — shadow→live 사람게이트 + ramp
모의(shadow)→실거래(live) 승급은 **사람 승인 필수, 자동 금지**.
1. **사람 게이트**: `approver` 서명 + incident/coverage 통과. kill_switch 해제는 사람만(`reset_emergency(by_human=True)`).
2. **로직 분기 금지·sink만 분기**: shadow/live 같은 로직, `execution_mode`만 다름(분기하면 검증 무의미).
3. **shadow→live ramp**: 사전등록 geometric ladder(rung FIX·"전진 여부"만 data-dependent=size-as-peeking 차단) + 전용 e-process(Ville anytime-valid). net edge 부호반전=capacity ceiling, realized impact>band=OOB breaker(즉시 halt).
4. **crypto-only 비의존**: equity halt 시 self-flatten 무의미 → `freeze_and_alert`.

#### 데이터·PIT 레이어 설계 결정 이유
- **왜 12 event type + 3 typed timestamp**: `CONSULT-DECISIONS-whole-20260529.md` — bitemporal append-only가 PIT 형식만이 아니라 실제 미래 차단을 보장하려면 transaction-time(저장 순서)과 valid-time(데이터 날짜)을 분리해야 한다.
- **왜 REVISION_OBSERVED가 OUTCOME mutate 안 함**: append-only 위반 + tt-order 손실 = revised lookahead alpha 누수. 정정을 새 fact(동일 vt·새 tt)로 표현해야 "각 vt에서 tt ≤ as_of 최신"이 정확 재현.
- **왜 반사성 게이트·purged CV·mlfinlab 회피**: `CONSULT-DECISIONS-weight-20260529.md` §1.8·§3 — 자기 거래 결과를 학습에 넣으면 self-confirming attractor, 라벨 horizon 겹침은 학습-평가 누수, mlfinlab은 독점 라이선스 페이월(skfolio 개념 자체구현).
- **왜 adversarial replay가 1급 게이트**: `CONSULT-DECISIONS-whole-20260529.md` — "as-of-A 산출에 tainted 0건 + revision 물리부재 oracle과 byte-identical". 코드 정합성이 유일하게 남은 직교 리스크라는 자문 수렴.

---

## 📐 가정 라이프사이클·통계 검증 레이어

이 레이어(`core/structure` + `core/assume` + `core/regime` + `core/pit` + `core/rules`)는 매매 의사결정의 밑바탕 **가정(criteria)**을 코드 상수가 아니라 **반증 가능한 카드**로 다루고, 그 카드가 "지금도 유효한가"를 anytime-valid하게 검증한다. 문제의식 둘 — 가정은 여럿이고 연속 모니터링되므로 본질적으로 **시간·가정 다중검정**이고(배치 BH·단발 t-검정으론 "regime 보일 때까지 본다"는 false-discovery 엔진 못 막음), 금융 regime은 자기상관이 강해 p값 online FDR이 가정하는 독립성이 깨진다. 그래서 **e-value/e-process 백본**으로 마이그레이션했다 — Ville 부등식 `P(sup_t E_t ≥ 1/α) ≤ α`가 임의 정지·임의 의존에 모두 robust하기 때문이다.

레이어는 관측·산출만 하고 **결정은 하지 않는다**(관측≠제어). 거시 regime은 graphical lasso로 조건부 상관을 학습하되 regime 자체는 **외생 정의**해 소표본·라벨불안정을 회피한다. 5+종 자산 아키타입이 "싸다/위험하다"를 각자 다르게 정의하고, PIT 안전성은 단일 `as_of` resolver가 강제한다.

#### e-process / online FDR / cascade 백본
- **MixtureSPRTEProcess**: 정규 mean-shift mixture martingale(Robbins-Siegmund 폐형). E₀=1, reorder-invariant, `(dt,vt)` 키 로그로 as-of 재현. `update(x) -> EDecision`, `replay_value(...)`.
- **ELOND / LordPlusPlus**: 동일 e-substrate 두 번째 readout. `ELOND`(Wang-Ramdas)는 e평균≤1+Markov만으로 임의의존에서 FDR≤α(p값 LOND 독립가정 불요). `LordPlusPlus`는 p값 fallback + alpha-wealth로 "죽은 가정 부활 남용" 차단.
- **HierarchicalFDRCascade**: 거시 부모가 **독립 substrate**에서 통과해야 자식 family 예산 해금(Benjamini-Bogomolov post-selection 차단). false-positive 1개가 3도메인 동시 false discovery되는 것 방지. **de-risking bypass** — 노출 축소 보호액션만 부모게이트 우회(per-stream α/2), 신규진입은 절대 금지.
- **EProcessSpender**: p값을 VS calibrator로 e값화 후 누적 운용, 기각 시 리셋(alpha-spending). per-domain decay(crypto 0.90~macro 0.99).
- **falsification POWER 게이트**: 형식상 falsification_metric 있어도 검정력 없으면 보호 0 → `falsification_protectable`이 power<floor면 차단("형식만 있고 power=0 = 노이즈 추격" 방지).
- **SpecSentinel**: e-process는 고른 null 상대로만 valid → PIT uniformity + exchangeability 두 model-free martingale로 wrong-H0 방어, 돌파 시 abstain.
- **ReverseEProcess + e_cusum**: economic decay vs regime 판별. 다수 sibling 동기화+exchangeability 점화면 regime(부모 freeze), node 특이·monotone이면 decay(node de-risk). `GraphEAllocation`이 DAG e-wealth 배분.

#### RegimeGlasso + effective_precision (조건부 상관 학습, R15 통계 본체)
- 파이프라인: **nonparanormal rank-transform**(fat-tail robust) → **EBIC graphical lasso**(γ=0.5 고정 grid argmin, CV 회피 → 결정론) → **EB shrinkage**(λ floor가 self-confirming attractor 차단) → 원공간 재스케일.
- `effective_precision(models, belief)` = §1.6 **cov-space belief-mix**: `Σ_eff = Σ_r b_r·Σ_r + Σ_r b_r(μ_r−μ̄)(μ_r−μ̄)ᵀ`를 **1회만 역행렬**. 둘째 between-dispersion 항이 regime 모호 시 risk 자동 inflate(transition de-risk). **이중 mix(Σ도 Ω도) 금지**(double-count).

#### assumption_stats / structure_model / archetype
- **assumption_stats**: `kind` dispatch — `validate_parametric`(CUSUM+PSI) vs `validate_structural`(prequential kink+BOCPD). **holds는 레짐별**(`by_regime`, 거래엔 `holds_now`). **hysteresis AND-gate**: ChangeRequest 승격 = online-FDR 유의 ∧ Cohen's d≥0.5 ∧ dwell ∧ K-윈도우 ∧ 동일 regime ∧ falsifiable 전부. base-layer는 사람 비준.
- **structure_model**: "싸다" = raw 분위가 아니라 **구조모델 잔차** `cheapness_z`. 잔차≈0이면 밸류트랩(drivers가 낮은 멀티플을 설명). 계층 부분풀링(RLM + James-Stein), purged/expanding OOS, delisted 포함.
- **archetype**: pydantic discriminated union 11종(cyclical=peak-EPS trap, compounder=비싼 쪽 trap, commodity_carry/seasonal/inventory, monetary_store/network_utility 등). `valid_from` 시변 교체.

#### 라이프사이클 (core/assume) + regime/pit
- `registry`(append-only 버전 + PIT 조회 + lifecycle emit), `validator`(**측정깨짐≠정의틀림**: data_contract 위반 시 SKIP), `update_controller`(**비대칭 게이트**: RETRACT=disjunctive fast / ADOPT=conjunctive 5조건 AND slow / base-layer=human), `dag`(ATMS 의존전파), `judge`(L1∥DCF + L2/L3 attenuating-only `final = L1·a2·a3 ∈ [0, L1]`). 가중학습은 `weight_card`/`weight_cycle`/`weight_falsification`이 Ω·IC → derive → synthesize_l1 → DUAL falsification.
- `pit_regime`: 수익률곡선·PMI로 K=3 결정론 분류 + `regime_model_version` 태깅. `regime_discovery`: open-ended 신규 regime을 BOCPD+Hotelling T²로 발견하되 **발견 자동·승격 사람**(`HumanApprovalGate`) + **sequestered stream** e-process 사전 threshold 통과 필수(사후 튜닝 차단). `as_of`는 canonical resolver(미래·None 거부).

#### 종목 스터디 시스템 (core/study) — R15 가중치를 종목별로 학습·감사·주입
자산군별(거시·미국주식·한국주식·국가지수ETF·리츠·원자재·금·채권·암호화폐) 스터디가 지표 가중치·상관 prior·정성 렌즈를 **이론 학습 + 실데이터 시계열 검증**으로 산출하고, 공유 코드를 안 고치는 **데이터 주도 플러그인**(`study_session.yaml` 7블록)으로 4단계 파이프(학습→규칙화→주입→해제)에 주입한다. 각 방은 "자문 그대로 코드화"가 아니라 담당 종목 전문 애널리스트가 되어 가설을 실데이터로 confirm/reject 한다.
- **study_loader / study_register**: yaml 7블록 로드·스키마 검증 → `panel_manifest`(G2)·`lens_store`(G3)·`flag_router`(G4)·`system_priors`(G5)를 묶어 weight_card 등록 + judge 호출 facade(G6). opt-in(`INV_R15_WEIGHTS`/`INV_STUDY_LENS`) off = byte-identical 무회귀. 본체(`weight_card`/`judge`/`RegimeGlasso`)는 wrap만, 미변경.
- **raw 완비 게이트 + 독립 감사**: `round-*`(자문 다회)·`theory-notes`(이론)·`validation-*`(실데이터 검증) 형식 게이트 + **opus 감사관이 `AUDIT-GUIDE` 12축으로 내용 감사**(main 통과편향 배제). ★**provenance + recomputation** — yaml 숫자를 신뢰 안 하고 raw 의 분석 스크립트를 직접 재실행·대조 + 합성데이터 지문 검사(결측·갭·역사적 이벤트 부재)로 "이론을 숫자로 둔갑"을 차단. hard-fail 코어(실데이터·추적성·PIT·생존편향) / **effective-N 은 차단이 아니라 tier 라벨**(저신뢰 가설=structural prior, validated alpha 위장 차단 — 암호화폐 N=4 halving 이 거시 60년 데이터인 척 못 함).
- **flag→동적 3경로** (seed→라이브 진화): 산출 yaml 은 고정값이 아닌 **prior(seed)**. 라이브 (확신/거부) flag 누적 → `Beta(α,β)` 신뢰도 → ① **weight**(`tilt_weights` 곱셈변조 + L1 보존 cap) ② **lens**(`confidence_note`→qwen 판단 보수화) ③ **corr_prior**(저신뢰 edge 를 독립 쪽 약화). `weight_falsification` e-CUSUM 붕괴=폐기, flag 누적=연속 조정. 블록5 `affects_indicator`/`affects_edge` 가 어느 weight·edge 에 연결되는지 명시(미명시 시 node 신뢰도 결합 근사).
- **factor-implied cross-sleeve 공분산**(`system_priors`): 방별 partial-corr 를 이어붙일 때 공통인자(USD·실질금리·글로벌 유동성)의 **중복 계상·PSD 붕괴 차단**(Σ=BΛBᵀ+diag(idio), PD 보장). regime obs floor shrink(n<floor→global shrink-fallback)로 소표본 regime 과적합 회피.
- **거시-종목 factor 통합 (M4)**(`factor_betas_seed`/`factor_cov_estimate`/`factor_shadow`): 각 방의 M3 거시연관 실데이터 검증(dollar=전 sleeve cross-validated 1차 driver, rate 는 리츠·금만 직접)을 위 cross-sleeve betas 로 변환한다. ★**점추정 박제 금지** — 셀을 `(β̂,SE,t,n,tier)` 분포로 저장하고 **James-Stein 수축**(`w=τ²/(τ²+SE²)`, a priori 경제 자산군 pool)으로 신뢰도에 비례해 pool 쪽으로 당긴다. opus 독립 검증관 3-tier 매핑 — `validated`=w 그대로 / `structural`=w≤0.25 캡(pool 강수축) / `reject`=pool 계산 제외하되 노출 `b=β_pool·w=0`(β=0 금지=게이트 사각지대 회피) / 미검증 sleeve=pooled-prior+live hold. idio conservation `d=max(σ²−bᵀΛb, κσ²)`. **Λ**=factor 혁신(rate/credit=Δbp·dollar/oil=Δlog, ADF+KPSS)→EWMA(HL 60~90d)+stress corr floor(상향 클램프)+Higham PSD 재투영. **shadow validation**(bias statistic[0.9,1.1] + 지배 eigenvector cosine>0.9)은 **순수함수 로깅 전용**이라 production 상태를 안 건드림(off-path byte-identical). risk gate wiring 은 후속(M5, BL prior cov 누수 차단). two-layer 분업 = dollar 방향은 belief(1차모멘트)·동조위험은 risk gate cov(2차모멘트), 모멘트당 1회. 자문 3R SSOT=`CONSULT-DECISIONS-M4-factor-integration-20260530.md`.

#### 가정·통계 레이어 설계 결정 이유
- **왜 e-value/e-process**: `CONSULT-DECISIONS-whole-20260529.md` §R4 — 연속 모니터링 = optional-stopping false-discovery 엔진 + 금융 regime 자기상관으로 p값 독립가정 깨짐. e값은 임의의존 robust로 둘 다 해결. 단일 substrate라 e-process(regime 변경)와 e-LOND(발견율) readout이 정합.
- **왜 HMM 기각·regime 외생화**: `CONSULT-DECISIONS-weight-20260529.md` §1.1 — "HMM/DCC 기각 — regime 외생 정의됨(소표본·라벨불안정 최악)". endogenous partition은 소표본 라벨 불안정 + 반사성. 남은 schema 불확실성은 accepted bounded residual로 문서화(saturation).
- **왜 graphical lasso**: L1 sparse precision이 소표본에서 spurious 상관을 0으로 눌러 다중공선 차단. λ는 EBIC 고정 grid(CV fold는 소표본에서 λ 분산 폭주 → 결정론 경로).
- **왜 cascade vs 격리 FDR 둘 다**: 횡단면=cascade(부모 독립 substrate 통과해야 자식 해금, post-selection 차단), 자산클래스별=격리 스트림(crypto가 macro α 예산 독식·exchangeability 붕괴 방지). 직교 보완.
- **왜 채택/기각 비대칭**: 같은 AND-gate면 반증된 가정이 dwell 채울 때까지 live 노출. RETRACT=fast(즉시 retire), ADOPT=slow(노이즈 추격 차단).

---

## ⚙️ 실행 결정 레이어

`core/` 루트는 자산 종류와 무관하게 동작하는 실행 결정 레이어다. 핵심 불변식은 `architecture.md` §6 "위험주문은 반드시 막힌다 + 우회 불가"를 코드로 강제한 것 — LLM·트랙은 **후보 제안까지만**, 매매 실행 권한은 risk_gate 통과분에 한정. risk_gate 규칙은 LLM이 호출하는 함수가 아니라 그 위의 inviolable wrapper이며, kill switch는 관측·룰 엔진과 물리 분리된 out-of-band 차단기다.

#### asset_track / coin_track / coin_track_macro / stock_track
- **asset_track**: Directional 계열 공통 계약. `MarketState`는 수집 raw 4종 무손실 보존, 파생은 읽기전용 프로퍼티. `collect_market_state(as_of)`(None=라이브, datetime=PIT 재구성) / `generate_candidate(state)` / `recommended_next_check(state)`.
- **coin_track**: 기존 `Orchestrator`+`ExternalDataAgent`를 import+위임으로 감싸 계약에 맞춤(본체 미변경). `coin_track_macro`는 macro 레이어 추가 wire — `allocate()` 결과 주입, **H29 macro abstain** 시 buy→hold 보수 처리.
- **stock_track**: `value_stock → run_value_trigger(2단) → Decision`. R15 weight_card 주입 시 거시국면·archetype 조건부 `S_L1` 산출, value_trigger confidence는 **down-only attenuator**로만 곱해져 천장 불변식 강제(`assert_ceiling_invariant`).

#### consensus / coin_consensus_lens — 고-스테이크스 2단 Judge
레짐 flip·배분 변경·누적 포지션 임계 초과 시에만 LLM Judge 호출(비용 게이팅). `is_high_stakes()`가 False면 즉시 stub(비용 0). Layer1(LLM 구조화) → Layer2(**risk_gate 항상-on 백스톱**, 거부 시 approve여도 hold 강제). `coin_consensus_lens`는 코인 전용 렌즈(on-chain/funding) + **DCF 미사용**.

#### risk_gate — 공통 리스크 게이트 (우회 불가 백스톱)
전 트랙 거래의 최종 안전 게이트. consensus/LLM과 무관 **항상-on**, 결정론(LLM import 0).
- **fail-closed**: 알 수 없는 action·비정상 NAV·NaN/inf → 즉시 REJECTED.
- **hard rule**: per-position soft −5%/hard −10%, 일일 손실 −5% NAV halt, 단일 10%·섹터 30% max weight, turnover 20%, min_holding.
- **상관캡**: corr>0.7 신규 차단, ≥0.8→0.7x, 0.6~0.8→0.85x 축소.
- **GatedOrderRouter(우회불가)**: `submit(order, via_gate=...)`에서 **`via_gate=False`(우회 시도)는 즉시 REJECTED + near_miss_veto + bypass 카운트**. `via_gate=True`만 `RiskGate.check()`. LLM/실행 프로세스는 이 wrapper로만 주문 접근.
- **KillSwitch(H27)**: MDD −15% → HALTED + alert. **자동 전량청산 금지** — `request_liquidation()`(CONFIRM_PENDING) → `confirm()` 후에만 청산(플래시크래시 footgun 방지). EMERGENCY_STOP과 독립.
- **Precedence 격자**: kill switch > 안전 스톱 > 포트폴리오 캡 > 세금/보유 > 리밸런스 순 단일 verdict 해소.

#### risk_sizing / coin_sizing — 멀티에셋 사이징
- **risk_sizing**: Ledoit-Wolf 공분산 → 변동성 타깃 역변동성. ill-conditioned(cond>1e6) 또는 raw 평균 corr>0.80 시 Riskfolio **HRP tail-codependence fallback**(w_max 0.10). 단일자산=1.0.
- **coin_sizing**: 단일 BTC는 `risk_sizing`에 위임(Kelly/LW 재작성 금지). 멀티코인만 tail HRP. **H25 crisis**: 상관 과열(코인 0.75) 시 BTC cap 0.40. `risk_gate.check()` 경유 필수.

#### portfolio_orchestrator / fallback_policy / budget_ledger / strategy
- **portfolio_orchestrator**: `regime→macro→weights` 체인 후 BL 슬리브 배분, 실패 시 HRP→IC 중립 prior. 슬리브 합=1.0 검증. **Drift Monitor**가 `SLEEVE_BANDS` 이탈 감시(near_miss_veto+리밸런스). **H26 FX**: 야간 stale 시 직전 마감율 고정. **H29**: macro unavailable → 신규매수 차단.
- **fallback_policy**: H27 `H27BoundedFallback`(confirm 타임아웃 시 시간분산 축소만, 전량청산 금지) / H26 FX guard / H29 macro abstain(청산·리밸런싱은 정상=liveness 디커플링).
- **budget_ledger**: LLM 예산 회계(soft limit 초과호출 기각, e^|Drop| 지수증폭 금지). 3버킷(NORMAL/RETRY_RESERVE/DEGRADE) thread-safe + `N3RetryPolicy`(max_retries=3 백오프 + RPM 10/min).
- **strategy**: `StrategyFamily`(DIRECTIONAL/MARKET_NEUTRAL/HFT) 3계열 + `Strategy` ABC. scalp_ml·kimchirang 미변경 독립 유지(import 0).

#### coin_memory / coin_shadow / observability / book
- **coin_memory**: `MemoryLayer` 상속, decay 반감기 단축(코인 4h). 코인 이벤트(halving·hack·depeg) importance 강화.
- **coin_shadow**: **shadow-live(H19)** — DRY_RUN 경로에서 실주문 0건 `OrderState` FSM만. identifier=uuid4(H9 멱등성). **SACRED: `execute_trade.py` diff=0**.
- **observability**: `kill_switch`(rule↔실행기 물리 방화벽, **불변식: rule은 한도의 producer지 override 아님**, emergency 해제 사람만), `rule_attributor`(반사실 PnL Shapley-lite, veto가 막은 상승=음수 기여), `rule_observer`(5지표 + **divergence shadow↔live = 안전 1차 방어선**, **관측 read-only — alert/mute 신호만, 집행은 외부**).
- **book**: `d4_book`(거시 국면·산업 특성 append-only PIT, `to_context(sector, as_of)`로 그 시점 지식만 L2 judge 주입), `d4_wire`(PIT substrate→book knowable_from 전파).

#### 실행 결정 레이어 설계 결정 이유
- **왜 리스크 게이트 우회불가**: `architecture.md` §6(:258·:493) — "LLM이 절대 우회 못한다", risk_gate는 "그 위의 inviolable wrapper". `GatedOrderRouter.submit`이 `via_gate=False`를 즉시 REJECTED + bypass 카운트해 LLM 직접 execute 경로 물리 차단. 결함 주입 판정 "⑤ LLM이 게이트 우회 시도 → 실패".
- **왜 asset-agnostic**: `architecture.md`:4 — "재작성하지 말고 asset-agnostic 코어로 일반화". `AssetTrack` ABC가 공통 계약만 정의, 트랙은 기존 본체를 위임으로 감싸 6대 보존 원칙 유지.
- **왜 consensus·사이징 분리**: consensus는 고-스테이크스 LLM 비용 게이팅, 사이징은 LLM 의존 0 결정론. 합치면 사이징에 LLM 비결정성이 새고 routine마다 비용 발생.
- **왜 out-of-band kill switch**: 관측(rule_observer read-only)·귀속(attributor)·차단(kill_switch 물리 방화벽) 분리. rule 오작동해도 스스로 한도 못 풀고, emergency 해제는 사람만.

---

## 🤖 레거시 실행 시스템 & 데이터 파이프라인

현재 **라이브로 도는** 암호화폐 자동매매 실행 계층(`agents/` + `scripts/`)이다. 감독·전략 에이전트가 데이터를 점수화해 매수/매도/관망을 자율 판단하고, 수집기들이 시세·심리·뉴스·온체인·매크로를 모은다. 핵심 철학 — **매매 로직을 LLM 프롬프트로 떠넘기지 않고 Python 에이전트가 직접 결정**(빠르고 저렴, 근거가 코드로 추적). 신규 `core/`와는 **옵트인 백스톱** 관계(`INV_CORE_GATE=true`일 때만 매매 직전 RiskGate 한 번 더 거름, 기본 off=레거시 byte-identical).

#### Orchestrator (감독 에이전트)
시장을 점수화해 보수/보통/공격 에이전트를 **사용자 승인 없이 자율 전환**.
- **두 점수**: `_calculate_danger_score`(0~100 — 연속손절·BTC 과다·급락·김치P 과열·롱 과밀·매크로 약세·뉴스 부정), `_calculate_opportunity_score`(0~100 — 극공포 FGI≤25·RSI 과매도·반등·Data Fusion strong_buy·음수 펀딩비·김치 디스카운트).
- **전환 규칙**: danger≥70→보수 직행, opportunity≥60 & danger<30→공격 직행. FOMO 방지(24h −5%↓ 급락 시 공격 차단, FGI≤20+−8% 이내 예외).
- **쿨다운**: 기본 2h, 당일 3회+ 4h, danger≥70/−7%↓ 긴급 면제. **워밍업 소프트 전환**: 30분 선형 블렌딩. **DB 학습**: 같은 전환 성공률 40% 미만+3건+ → −10점.
- **자동 긴급정지**: 발동 시 강제 전량 매도+매수 차단. 수동 EMERGENCY_STOP은 감독이 해제 불가.

#### BaseStrategyAgent + 전략 3종
- **점수제 매수**(`calculate_buy_score`): FGI(30)+RSI(25)+SMA(25)+뉴스(20)+MACD/외부 보너스. 하락추세 감점. **하이브리드 매도/손절**(`evaluate_sell`): 분할매도 → v6 매도 점수제 → 레짐 트레일링 → 강제 손절 → 하이브리드 DCA 안전망(캐스케이딩 위험·바닥 충족·외부 약세 보고 손절/물타기 분기). **레짐 5단계**(bull~crisis 포지션 비율 차등). **Kelly 사이징**(confidence 배수×Half-Kelly, `MAX_TRADE_AMOUNT` 절대 상한).

| | 🛡️ Conservative | ⚖️ Moderate | 🔥 Aggressive |
|---|---|---|---|
| 매수 임계 | 60점 | 50점 | 40점 |
| FGI / RSI | 35 / 35 | 45 / 40 | 60 / 50 |
| 손절 / 강제 | -5% / -10% | -5% / -10% | -3% / -7% |
| 1회 / 일 한도 | 10% / 3회 | 15% / 5회 | 20% / 7회 |

AI 거부권: 매수 점수 충족이어도 `ai_composite_signal.score`<0이면 보류(극공포 예외).

#### ExternalDataAgent (뉴스랑/NewsRang)
11소스 **병렬 수집(에러 격리)** + Data Fusion 종합. 기본 8(FGI·뉴스·온체인 고래·바이낸스 심리·ETH/BTC z·매크로·CoinGecko 이상·Data Fusion) + 확장 3(RSS 16피드·X 7계정·소셜 감성). `collect_all()` ThreadPoolExecutor, 하나 실패해도 나머지 정상.

#### 데이터 수집 + 실행 + 운영
- 수집(`collect_*.py`/`get_portfolio.py`): Upbit 시세+지표, FGI, Tavily 뉴스, AI 복합 시그널, 포트폴리오.
- **`execute_trade.py`**: Upbit 시장가. 안전장치 **우회 불가 순서**: EMERGENCY_STOP → auto_emergency → DRY_RUN → MAX_DAILY_TRADES → MIN_TRADE_INTERVAL → MAX_POSITION_RATIO → 보유량 검증 → MAX_TRADE_AMOUNT. PID 파일락 이중 주문 방지.
- `short_term_trader.py`(단타 3전략), `notify_telegram.py`(MarkdownV2), `version_manager.py`(changelog+VERSION 범프).
- 파이프라인: `run_agents.sh`(권장, 6 Phase) / `run_analysis.sh`(레거시 LLM) / `cron_run.sh`(4h 간격, Python PRIMARY + claude -p FALLBACK).

#### 레거시 실행 레이어 설계 결정 이유
- **왜 점수제+하이브리드 손절**: 단일 규칙은 노이즈 취약 → 여러 약한 신호 가중 합산으로 거짓 트리거 감소 + score breakdown 감사 가능. 손절도 일시 급락 손절 후 반등 손실과 추세 하락 물타기 손실을 동시에 줄이는 하이브리드.
- **왜 감독 자율 전환**: 고정 전략 하나로는 폭락·횡보·불장 중 한쪽에서 손해 → 위험도/기회 정량화로 자동 전환. 부작용 가드(쿨다운·워밍업·DB 페널티·FOMO 차단) 동반.
- **왜 DRY_RUN/EMERGENCY_STOP**: 실자산 거래라 버그=금전 손실. DRY_RUN 기본값 + EMERGENCY_STOP을 DRY_RUN보다 먼저 검사 + 감독도 수동 STOP 해제 불가 = 최종 통제권 사람. `MAX_TRADE_AMOUNT`는 모든 경로 통과 후에도 적용되는 절대 상한.

---

## 📈 주식 트랙 & 통합 백테스트

주식 트랙(`stock/`)은 "가격이 빠진 종목 중 진짜 싸진 것만 사고 value trap은 거른다"는 bottom-up 트랙이다. 모멘텀 코인 트랙과 달리 **내재가치 대비 저평가**를 신호로 삼는다. 핵심은 `value_trigger.py`의 **가치 2단 트리거** — 1차 저비용 필터(가격 하락+가치 갭)로 후보를 모으고, 2차 heavy agent(Claude/Damodaran)가 "기회 vs thesis 붕괴"를 가린다. 통과분만 risk_gate로, 체결은 `kis_client.py`(모의투자 우선). 통합 백테스트(`backtest/`)는 코인·주식을 동일 `AssetTrack` 계약으로 구동하며 거래대금 비례 슬리피지·세금을 반영하고 PIT/생존편향/PBO로 백테스트 환상을 차단한다.

#### stock/ — 가치 트랙
- **contracts**: SSOT 타입. `Fundamentals`는 **announcement-date PIT 3-튜플**(`fiscal_period`·`filing_timestamp`·`source`). `is_pit_clean()`은 DART/EDGAR XBRL+as_reported만 True, RESTATED(pykrx/FDR 재작성) 거부. `ValueVerdict`(OPPORTUNITY/VALUE_TRAP/PRICE_ONLY/REJECT/ABSTAIN), `RunMode`(BACKTEST/FORWARD=H22 경계).
- **valuation**: bear/base/bull 밴드 확률가중(DCF 0.45+EV/EBITDA 0.30+RIM 0.25) → `valuation_gap`. ai-hedge-fund 수식 어댑트하되 입력을 PIT Fundamentals로 재설계.
- **value_trigger**: 1차(가격 −10% ∧ 갭 ≥0.25) → 2차 trap 판정. **단순 buy-the-dip 금지**(가격↓+내재가치↓ = 매수 아님). H22: BACKTEST는 heavy-agent ABSTAIN stub, FORWARD만 실판정. MetaLabeler 함정확률로 사이징 억제.
- **admission**: coarse(상품 Tier) + fine(KRX 상태) + 지역 3단. 선물·옵션·마진 영구 금지, 레버리지/인버스 ETF allowlist 없으면 거절, 관리/경고/위험/정지/상폐우려 거절. `requested_by_llm=True` 즉시 차단(LLM 유니버스 확장 불가).
- **kis_client**: pykis 래핑(모의 우선). `_check_safety`(DRY_RUN·EMERGENCY_STOP 선검사), `_clamp_to_balance`(과매도 차단), `KisRateLimiter`. modify `original_number` 체인(H15), `check_price_limit`(±30% H17), `convert_usd_to_krw`(H18).
- **factor_attribution**: 종료 거래를 market-β+섹터+idio 회귀로 분해해 `FailureReason`(MACRO_REGIME_WRONG/SECTOR_THEME_WRONG/VALUE_TRAP/EXECUTION_SLIPPAGE). 저신뢰는 `UNATTRIBUTED`. triple-barrier 메타라벨로 함정확률 주입.
- **stock/data/**: `PITFundamentalsAdapter`(filing_timestamp≤as_of+non-RESTATED, `pit_clean_ratio`), DART/EDGAR provider(정정공시도 원본 접수일), `krx_universe`(FDR/pykrx 실연결 jsonl 일별 PIT), `macro_vintage`(ALFRED), `sector_multiples`(Damodaran/French), `rate_tier`(토큰버킷).

#### backtest/ — no-lookahead 통합 엔진
- **engine**: `AssetTrack` 계약 경유 코인·주식 동일 코드. 슬리피지(H1) `impact_factor × (trade_value/market_volume)` 거래대금 비례(고정상수 아님), `compare_slippage`로 drag 정량. 비용(Upbit 0.05%/KIS, KR 거래세 0.20%, US 환전·양도세). nautilus `OrderState` FSM + `FillModel` 부분체결. `coin_engine`은 24/7·얇은 알트 임팩트 2배 변형.
- **walk_forward**: skfolio `CombinatorialPurgedCV` IS/OOS 분리 + purge+embargo(부재 시 gap fallback). `filter_pit_fundamentals`(is_pit_clean+visible_at), **생존편향(H5)**: `UniverseManager`가 백테스트엔 상폐 **포함**, 라이브만 제외.
- **pbo**: 다중검정 과적합(H23) 정량. `calculate_pbo_cscv`(Bailey & López de Prado CSCV logit-rank 정통식), `calculate_deflated_sharpe_ratio`(trial-count 보정 DSR>0.95), `build_go_nogo_card`(GO/MARGINAL/NO_GO JSON). `capacity`(주문 ≤ 일거래대금 1%, 자기충격 Sharpe 부풀림 차단).

#### 주식·백테스트 레이어 설계 결정 이유
- **왜 가치 2단 트리거(기회 vs 함정)**: `architecture.md`:262 "가격 빠진 종목 중 진짜 싸진 것만". 단일 게이트는 buy-the-dip → 실적쇼크·구조적 악재로 내재가치 동반 하락한 종목 매수. 1차 저비용 필터 + 2차 heavy agent 내재가치 재산출로 trap 판별. 일시 패닉셀(매수) vs 실적쇼크(매수 안 함) 혼동행렬 검증.
- **왜 filing-lag PIT + 생존편향 차단**: H5(:381) — "현재 재작성값"은 그 시점에 알 수 없던 정보로 과거 평가 = lookahead. announcement-date 정렬 PIT만, RESTATED 거부. 생존편향 짝 — 상폐 종목 빠지면 "0으로 간 진짜 value-trap" 통째로 빠져 인위적 호성능.
- **왜 PBO**: H23(:463) — walk-forward·생존편향까지 가도 "몇 개 전략 시도?" 보정 없으면 수십~수백 trials 중 하나가 우연 통과. DSR·PBO(Bailey/López de Prado)로 trial-count deflate.
- **왜 forward-only(back-adjust 금지)**: 미래 정보로 과거 시점 값을 덮어쓰면 lookahead → 시점별 가시성(`visible_at`) 보존, "그때 알 수 있던 것"만 forward. heavy-agent는 LLM 학습데이터 미래 오염(H22)으로 BACKTEST=ABSTAIN stub. *(back-adjust 금지 명시 SPEC 문구는 grep 미발견 — H16/H22 lookahead 원칙 + `visible_at`/`filter_pit_fundamentals` 구현에서 도출.)*

---

## 🔢 Phase 진화 (구현 단계 — `architecture.md` §2)

각 Phase는 독립 PR + 테스트 + DRY_RUN 검증 후 진행. **가장 치명적 갭(멱등성·reconciliation·스키마강제·결정성·서킷브레이커)은 미래 주식 트랙이 아니라 지금 라이브 코인 경로에 있어 Phase -1로 선반영**.

| Phase | 내용 | 운영 합격 판정(§2.9) |
|---|---|---|
| **-1** | 라이브 코인 안전 하드닝(E2 멱등성·R2 reconciliation·B1 스키마·B3 결정성·C2 서킷브레이커) | 결함 주입 통과 |
| **0** | 코어 추상화(`AssetTrack` ABC, 기존 동작 100% 보존) | 래핑 전후 의미적 동치(회귀 0) |
| **1** | 두뇌 마이그레이션(Gemini→Qwen 로컬+Claude, 임베딩→BGE-m3) | 평상시 Claude 호출 0, 트리거 시만 |
| **2** | 공통 리스크 게이트(우회 불가) | 5종 결함 주입 전부 차단 |
| **3** | 주식 트랙 + 가치 2단 트리거 | 기회 vs value-trap 구분(혼동행렬) |
| **4** | 데이터 레이어 + KIS 실행 | KIS 모의 왕복·분당 한도·reconciliation |
| **5** | 통합 백테스트(2018+) | 슬리피지 정량·패리티 ≥95%·PBO/DSR |
| **6** | Portfolio Orchestrator(최상위) | 분산효과 + 90일 무중단 |

---

## 🛡️ 안전장치 요약

| 파라미터 / 장치 | 기본값 / 동작 |
|---|---|
| `DRY_RUN` | `true`(분석만). 실거래 = `false` flip(사람 게이트) |
| `EMERGENCY_STOP` | `true`면 즉시 중지. 감독도 해제 불가, **DRY_RUN보다 먼저 검사** |
| `MAX_TRADE_AMOUNT` | 1회 상한(모든 경로 통과 후 절대 클램프) |
| `MAX_DAILY_TRADES` / `MIN_TRADE_INTERVAL_HOURS` | 일 횟수·최소 간격 |
| `MAX_POSITION_RATIO` | 총자산 대비 최대 투자 비율 |
| auto_emergency | 감독 권한 자동 긴급정지(4h −10%·연속손절 5회+ 등), 해제는 12h+급락종료+공포완화 |
| Risk Gate | `GatedOrderRouter` 우회 불가(`via_gate=False`→REJECTED), 결정론 항상-on |
| Kill Switch | MDD −15%→HALTED, 자동 전량청산 금지(사람 confirm), out-of-band 물리 분리 |

**🚦 실전 자금 전환 게이트**: Phase 0~6 운영 판정 전부 통과 + KIS 모의·코인 DRY_RUN 합산 90일 무중단(급락/급등 1회 사고 없이) + 라이브 신호가 백테스트 분포 안 + kill switch/EMERGENCY_STOP/reconciliation 실발동 기록 + 통과 후에도 극소액부터. (자율 범위 밖, 사람 게이트.)

---

## 📂 디렉토리 맵

```
core/                  ← asset-agnostic 신규 아키텍처
  asset_track.py·coin_track*.py·stock_track.py   실행 트랙
  risk_gate.py·risk_sizing.py·coin_sizing.py     리스크/사이징
  consensus.py·portfolio_orchestrator.py         합의/배분
  budget_ledger.py·fallback_policy.py·strategy.py
  brain/            두뇌(레짐·LLM 라우팅·학습 메모리·RAG)
  data/             데이터·PIT·event ledger·가중학습(R15)
  structure/        가정 통계·e-process·FDR·glasso·archetype
  assume/           가정 라이프사이클·judge·가중카드
  regime/·pit/·rules/  외생 regime·PIT resolver·룰
  observability/    kill_switch·rule_observer·rule_attributor
  book/             d4_book·d4_wire(거시·산업 학습 Book)
agents/              레거시 실행(감독·전략 3종·뉴스랑) — 현재 라이브
scripts/             데이터 수집·실행·파이프라인(run_agents.sh)
stock/               주식 가치 트랙(valuation·value_trigger·KIS·data/)
backtest/            통합 백테스트(engine·walk_forward·pbo·capacity)
supabase/            DB 마이그레이션(decisions·embeddings·감사 테이블)
```

---

## 🚨 무인(Unattended) 자동운영 안전 아키텍처

**목표**: 운영자 개입 0의 완전 무인 자동운영을 안전하게 실행. 핵심은 fail-safe 자동 de-risk와 사람 confirm 경로 제거(de-risk는 이미 의사결정, resume만 남김).

### 신규 불변식
- **보호행동(de-risk) 경로는 LLM 완전 독립**: 심한 손실/급락 시 자동으로 position을 단계적으로 축소하되, 이 경로는 LLM 출력·가용성과 무관. LLM은 줄이거나 veto만, 보호행동 trigger를 요구하거나 suppress 불가.
- **자동 de-risk-to-floor**: 기존 "자동 전량청산 금지(사람 confirm 대기)" → **"자동 단계청산(IOC) + frozen bag 상한"**으로 재정의. 시장 충격 회피 + 무인운영 가능 양립.

### 안전 계층 (4단)

#### 1. KillSwitch (MDD −15%)
- `core/risk_gate.py` 상태기계: NORMAL → HALTED
- HALTED 도달 시 ⚠️ **`derisk_executor` 자동 호출**(사람 confirm 대기 X)
- confirm()은 *resume*(재무장)에만 잔존

#### 2. DeriskExecutor (자동 단계청산)
스테이트풀 자동 de-risk 집행기, LLM/Orchestrator 비의존:
- **tier 2단**:
  - **soft-halt** (−10% ~−15%): IOC 주문, board-matched 우선
  - **hard-derisk** (< −15% 또는 MDD): 시장가 제한 + frozen-bag(상한 고정) 모드
- **상태 자동전이**: NORMAL → SOFT_HALT → HARD_DERISK → COOLDOWN(지수 backoff: 2^n 시간) → RE_ARM_EVAL
  - **Hysteresis**: 진입 ≠ 해제 임계(오픈→클로즈 히스테리시스로 whipsawing 차단)
  - 일일 hard re-arm 한계 3회 초과 시 PERMANENT_FREEZE(수동 resume만 가능)
- **거래소 truth-authoritative**: 실시간 보유 query → ledger와 대사 → 불일치 시 soft-halt 강화

#### 3. Watchdog + Dead-Man's Switch
- **Liveness monitor**: 메인 루프 heartbeat를 주기적 확인
- **Heartbeat loss**: derisk_executor 자동 호출 + 순회 모든 위치에서 soft-halt 천정
- **거래소 native 보험**: Upbit/KIS 고급 stop-loss(GTC 타입) 병용 — 로컬 장애 시에도 flash crash floor 보호

#### 4. Reconciliation + Thin-Book Escalation Ladder
- **3-way 대사**: intended(계획) / ledger(로컬 기록) / 거래소 truth → truth authoritative overwrite
- **Thin-book escalation** (IOC 크기 확대):
  - −1%: band-1 IOC 시도
  - −3%: band-2 IOC 시도  
  - −5%: band-3 IOC 시도
  - 슬리피지 상한 도달 시 → FROZEN_BAG(매매 중단 상태 고정)
- **Tolerance & tolerance break**: 네트워크 지연/transient stale 허용, 지속 delta(신뢰 유실) 시 hard-derisk 강화

### 최소 사람 게이트 (자율 범위 밖)
⛔ **절대 자동화 금지** (자문 수렴, 2026-05-29):
1. **실거래 전환**: `DRY_RUN=false` flip (α/β 테스트 후, 사람 승인)
2. **자본 상향**: Base Capital 배포 (수동, 내부 감사 거쳐야 함)
3. **API 출금권한**: air-gap 설정 (물리 분리, 사람이 명시적으로 enable)

무인 go-live 시:
- `DRY_RUN=true`(분석+모의 시뮬) 최소 90일 무중단 운영 ✓
- KillSwitch/DeriskExecutor/Watchdog 실발동 기록 ✓  
- 레거시 경로 & core 모의 신호 일치율 ≥95% ✓
- 백테스트 분포 내 ✓

---

> **문서 베이스**: `architecture.md`(목표 아키텍처·Phase·내구성 H1~H32), `ARCHITECTURE-brain.md`(두뇌 의사결정·학습 루프), `plan-unattended-ops.md`(U1~U7 무인운영 패치), `CONSULT-DECISIONS-whole/button-v2/weight-20260529.md`(3세션 통합 자문), `macro.md`·`MACRO_CORRELATION_BACKGROUND.md`(거시 정량 법칙). 각 모듈 상세는 해당 `.py` docstring과 `__main__` self-test 참조.
