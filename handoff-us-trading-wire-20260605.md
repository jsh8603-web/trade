---
tags: [type/handoff, domain/inv, scope/equity-us, topic/trading-wire-3layer, status/in-progress]
date: 2026-06-05
owner: main (btn-button, opus 1m)
next-action: "★[최신 2026-06-05 collector 종결] 다음 세션 첫 행동 = ②WIRE5 한국 sleeve 진입. collector 트랙 종결 = ERB self-snapshot collector 신규(`stock/data/erb_snapshot.py` yfinance eps_revisions+eps_trend forward-only bitemporal, `tests/test_erb_snapshot.py` 5pass+회귀0+실가동 116/117종 464행+sanity 타당 erb mean+0.302) + 현황 재파악으로 US collector 완비 확인(measure↔collect gap0=실데이터 완비 / survivorship Sharadar 불요=120종 상폐0 대형주 M&A프리미엄 bias반대 / PIT 엔진 core 구축됨 vintage.py+crypto reserve_snapshot / backfill 무료없음 리서치=Zacks·IBES 유료뿐 HF후보 환각적발 → ERB forward-only 확정). ★WIRE5 한국 = KRX peer median(french=미국전용 대체)+DART valuation+한국 STT net-alpha hard, broker=KisClient를 WIRE6 `stock/order_assembly.py` 주입. 재사용=`stock/data/krx_universe.py`(N-P3-1 완료 상폐 DelistingDate PIT+관리종목 jsonl)+DartXbrlProvider(본체완료 DART_API_KEY 대기)+erb_snapshot.py(한국 ERB 동일패턴). ★그 다음(한국끝)=③Gg′ 실 가치트랩 IC = LLM 세션(본 handoff §Gg-LLM-인계 상세, 인계 의무). go-live 미접촉. SSOT=progress §3 ckpt-202606051200. ↓↓아래는 모두 구식(완료됨)·무시: ★미국 주식 매매 = 완전형 3층(1층 regime_to_weights[기구현] / 2층 STATIC inverse-vol / 3층 cross_sectional_selection+selection_pipeline[WIRE1~4 + 배선 완료✅]). ★generate_candidate end-to-end 배선 완료(2026-06-04): (갭A) stock_track.generate_candidate value_stock 실연결(override 미주입+fundamentals+quote → 내재가치 산출, 신규 필드 _sector_ev_ebitda/_bypass_gate1/_heavy_agent_fail_reason 전부 default off) + (갭B) 신규 stock/selection_pipeline.py build_universe_candidates(selection top-K ⊕ per-ticker value_trigger, valuation 1회 캐시 공유, bypass_gate1=True로 가격게이트 우회). 회귀 53 passed(byte-identical) + wire smoke 5(tests/test_selection_pipeline_wire.py). 미국 selection 파이프 코드 닫힘 — 실 EDGAR/KIS universe 조립(dict 4종)은 호출자 책임. ★WIRE3.5 급수 wiring 완료(2026-06-05): Ga preset / Gb interaction / Gc yaml weights / Gd construction / Gf-C 12-vintage overlap[horizon mismatch 해소, 재검증 +6.20% CI[+0.067,+0.977] 유의] / Gi-A 결측 sector_min[sign-aware] / Gh-1 설계확정[점진 감쇠, monitoring wire는 라이브] / Gj DEF-2 등가중 hedge[×0.5]. + WIRE6 order_assembly 배선 flag(stock/order_assembly.py, DRY_RUN=True default=실주문0, GatedOrderRouter 강제경유, EMERGENCY_STOP). 레저↔배선 전수검증 UNDER/OVER/MIS/역방향 0건. ★작업순서(사용자 2026-06-05): ①collector 인프라(★한국 전 필수) → ②WIRE5 한국 → ③Gg′ 실 가치트랩 IC=★한국 끝 LLM 세션(본 handoff §Gg-LLM-인계). ★다음 세션 첫 행동=①collector 구현(EDGAR/I·B·E·S/Sharadar/FF5/ALFRED). ★구식 무시: 아래 'Gf/Gh/Gi 자문 R1 발사'는 이미 완료됨. ★다음 세션 첫 행동 = Gf/Gh/Gi 애매 설계 4종 묶음 자문 R1 발사: `bash ~/.claude/skills/gemini-web-consult/send.sh send "$(cat .consult-us-selection-design-gaps-brief.md) [§4 a~e 답]"` + claude-web 병렬 → 수렴 → main 재검증(advisory-protocol) → 적용. 브리핑=`.consult-us-selection-design-gaps-brief.md`. Gg(실 post-veto IC)=heavy_agent LLM 라이브 후속. ckpt-202606050900 참조. ★자문 3R+재검증 적용 = capped-EW feasibility(Σ0.5→1.0 결함수정) + interaction FWL잔차화(collinearity0.363) + MAD guard, 회귀 39 passed(ckpt-202606050730). 첫 행동 = 미적용 별 step 중 ★Gf horizon mismatch backtest(자문 최대결함, 12M신호↔월간정책 미검증) 또는 Gg trap-veto post-veto IC(무거운 시뮬) / Gc yaml weights·Gd 호출자(WIRE6) / 부호 e-process·net-alpha band(Gh). 그 후 WIRE5 한국. go-live 미접촉. 자문 raw=`.consult-us-selection-methods-brief.md` + `.gemini-web-last.md`/`.claude-web-basic-last.md`."
resume_priority: "WIRE1~4 + generate_candidate 배선 완료(미국 selection 파이프 닫힘). 다음 = WIRE5 한국 sleeve(KRX 데이터 수집 선행=무게큼) > WIRE6 order 조립. 2층 rotation=STATIC 확정(재측정 금지). mega 과소배분 딜레마 §5. selection 가이드: cyclical=demean_by_sector on 권장 / defensive=net_iss 단독 금지·ep 합성·on 필수. 배선 진입점=stock/selection_pipeline.py build_universe_candidates."
---

# handoff — 미국 주식 매매 완전형 3층 wire (2026-06-05)

## 1. 현재 상태 + 첫 행동

**미국 주식 매매 = 3층 구조 확정 + 구현 착수.** 이번 세션에서 자문 3회(selection 2R / rotation 3R / defensive-paradox 2채널) + 실측 3건으로 설계·검증.

```
1층 자산군      regime_to_weights.py [기구현]   us_stock 비중 (vs 채권/금/원자재/코인)
2층 sub-sleeve  실측 = STATIC          us_stock → cyclical 0.31/defensive 0.41/mega 0.28 (shrunk inverse-vol)
3층 종목선택    cross_sectional_selection.py [WIRE1 완료]  sleeve 안 robust z → top-K capped-EW → trap veto
```

**첫 행동 = WIRE3**: `stock/cross_sectional_selection.py`(작성됨, smoke PASS)를 `core/stock_track.py:155 generate_candidate` **상위** 레이어로 배선(현재는 종목 1개씩 처리, universe ranking 루프 없음). 실데이터(`industries/{sl}/raw-v3/data/prices.parquet` + `edgar_fundamentals.parquet`)로 cyclical/defensive 각 universe의 cross-sectional valuation z 산출 → top-K 픽이 우리가 검증한 IC(cyclical PBR/EV CONFIRM, defensive net_iss PARTIAL)와 정합하는지 1회 시뮬. risk_gate cap 10%/30% 안쪽. go-live 미접촉.

## 2. 진행 맵 (WIRE 트랙, SSOT = progress-stock-corr-layer-20260603.md §2.7)

| 단계 | 상태 | 핵심 |
|---|---|---|
| WIRE1 selection(3층) | ✅ | value_trigger.py bypass_gate1(byte-identical, 회귀16) + cross_sectional_selection.py 신규(smoke PASS) |
| WIRE2 rotation(2층) | ✅ STATIC | predictive t−0.31/OOS IR0.12 비유의 → inverse-vol base 고정 |
| 정설 검정 | ✅ 정정 | "불경기 방어주"는 down-capture **0.68**(`_downcapture.py` 영속, 0.57→정정)로 robust. 1차 excess 측정은 명세오류 |
| mega 과소배분 검토 | ✅ (딜레마, §5) | Sharpe 최고인데 비중 최저 = 과소 맞으나 교정=return 박제 |
| WIRE3 selection 정합 시뮬 | ✅ | cyclical top-K excess +0.087 IC정합 / defensive net_iss+ep +0.022(단독 음=PARTIAL) / sector-neutral 옵션(`_wire3_*_sim.py`) |
| generate_candidate 배선 | ⚠️ 배관만 | (갭A) value_stock 실연결 + (갭B) `stock/selection_pipeline.py build_universe_candidates`(selection ⊕ value_trigger, bypass_gate1 우회). 회귀 53 passed + smoke 5. ★**급수 미개통**(ckpt-202606050530 대조): metric_signs preset production 부재(sim/test만) + factor×factor interaction 미지원(DEF-2 robust 표현불가) + base_weight selection에 dead + 호출자 부재 |
| reflection-verify | ✅ | 자문 20항목 R16/S2/누락0/역방향0/정량일치 (foreground subagent) |
| WIRE4 net-alpha framework | ✅ | SelectionConfig net-alpha 파라미터+`_eligible` hard reject 게이트(default off=byte-identical). 검증: 한국 STT0.23% top-10→2 reject / 미국 soft 무영향. 회귀16. ★scale은 WIRE5서 한국 IC로 보정 |
| WIRE3.5 급수 wiring | ⬜ 다음(계획됨) | 연구지표→production 실투입 4 step(progress §2.5): Ga metric_signs preset(sonnet) / Gb ★interaction term=DEF-2 robust 살림(opus) / Gc summary.yaml base_weight→weights 연결(sonnet) / Gd 호출자=WIRE6 동반. 누락방지 매핑표 R0/P6/K4/S1→R |
| WIRE5 한국 sleeve | ⬜ | KRX 산업 peer median(french=미국전용) + STT + WIRE4 expected_alpha_scale 한국 보정. KRX 데이터 수집 선행=무게큼 |
| WIRE6 order 조립 | ⬜ | GatedOrderRouter→KisClient, DRY_RUN/EMERGENCY_STOP, go-live 사람게이트 D1~D5 |

## 3. 사용자 박제 (대화 고유 framing)

- "거시 정설(경기 따라 경기주/방어주) 있는데 1층 신호랑 묶으면?" → 묶어봤으나 rotation 여전히 미식별(자문 discrete regime overfitting 기각 + 항등식 artifact 확인).
- "불경기 방어주 사라가 틀린거냐?" (dispute) → ★아니다, 정설 맞음(down-capture 0.57). 내 1차 "정설 반대"가 측정 명세오류였음. 자문+재측정 정정.
- "다른 두 슬리브도 비중 조정되나?" → yes, inverse-vol이 셋 다 vol 기준 조정. defensive 많이/mega 적게.
- "메가 억울한 거 검토해봐" → §5 (Sharpe 최고인데 비중 최저, 단 교정 딜레마).
- ★**설명 선호**: 핵심 결론은 "쉽고 재미있게 예시(노점/동전/시험 비유)로" 요구 자주. 보고 시 비유 곁들일 것.
- 기존(이전 세션): "1-3 wire 다 해야지, 1 selection 필수 최우선 동의" / "기존 결과 깃허브보다 우수 류 결론 금지" / 합성 데이터 금지 / go-live 미접촉.

## ★Gg-LLM 세션 인계 (사용자 2026-06-05 "Gg는 한국 끝 LLM 세션, 다음 세션 인계 시 상세히 적어라")

> **⚠️ 다음 세션 → LLM 세션 전달 의무**: Gg′(실 가치트랩 IC 재측정)는 heavy_agent=LLM 실연결이 필요해
> 현 selection 세션에서 못 닫는다. **작업 순서상 ① collector → ② WIRE5 한국 끝난 뒤, ③ 그 다음 LLM 세션이 처리**.
> 이 섹션을 LLM 세션에 그대로 전달할 것.

### 무엇 (task)
`stock/cross_sectional_selection.py make_trap_veto` 의 trap veto 가 **value 와 상관**(싼 종목이 trap 잘 걸림)
→ 좌측꼬리 제거 → value alpha 잠식 여부를 **실 LLM 판정**으로 측정. measured IC ≠ traded(post-veto) IC 확인.

### 현 상태 (이미 측정된 것)
- **worst-case proxy 만 측정 완료**: `_wire35_heavy_reverify.py` Gg 블록 = full top-K excess +8.69% vs
  post-veto(최상위 cheapness **5% 무조건 제거**) +6.20% = **Δ−2.48pp**. ★이건 "가장 싼 종목을 무조건 제거"
  가정이라 **worst-case 상한** — 실 trap 은 LLM 이 "진짜 나쁜 종목"만 골라 제거하므로 실제 잠식은 < 2.48pp 예상.
- 현 mock heavy_agent = ABSTAIN → veto 0건 (실 판정 불가, 그래서 라이브 LLM 필요).

### 해야 할 것 (LLM 세션)
1. **heavy_agent LLM 연결**: `core/brain/llm_provider.py` 의 LLM provider 를 value-trap 판정기로 주입
   (judge_value_trap 인터페이스 = `stock/value_trigger.py:76 HeavyAgent` Protocol: `judge_value_trap(valuation,
   fundamentals, price_change_pct, context) → HeavyAgentVerdict(is_trap, confidence, reasoning)`).
2. **post-veto 재측정**: `make_trap_veto`(value_trigger.run_value_trigger bypass_gate1=True, heavy_agent=실LLM)로
   cyclical/defensive universe 각 종목 trap 판정 → trap 제거한 eligible set 에서 value IC(pbr/ev/net_iss) 재측정.
3. **비교**: full IC vs post-veto IC → 실제 잠식 폭(< worst-case 2.48pp 여야 trap 이 진짜 나쁜 종목만 제거 입증).
   잠식이 크면(≈2.48pp) trap veto 가 value 와 과상관 = veto 로직 재설계 필요.

### 코드 위치 / 데이터
- `stock/cross_sectional_selection.py` `make_trap_veto`(value_trigger 재사용 래퍼) + `select_cross_sectional(trap_veto=)`.
- `stock/value_trigger.py` `run_value_trigger(heavy_agent=, bypass_gate1=True)` — Gate2 만 적용.
- `core/brain/llm_provider.py` — LLM 연결(SACRED: DRY_RUN 기본값·API key 사용 금지 주석 준수).
- 데이터 = `study-research/eq_us/industries/{cyclical,defensive}/raw-v3/data/{prices,edgar_fundamentals}.parquet` (실 PIT).

### 주의
- ★LLM 비용: 종목 수 × 월 × judge 호출 = 큼. **샘플(소수 종목·일부 월)로 시작** 후 확대.
- go-live 무접촉 — 이건 **측정(IC 재검증)** 이지 실주문 아님. WIRE6 order_assembly DRY_RUN 과 별개.
- Gh-1′(부호 e-process monitoring wire)도 동일 라이브군 — 같은 LLM 세션에서 묶어 처리 가능.

## 4. 파일 인벤토리 (절대경로)

**구현 (이번 세션 작성/수정)**:
- `D:/projects/Inv/stock/cross_sectional_selection.py` — 신규. robust_z(median/MAD) + composite_cheapness_z + select_cross_sectional(top-K capped-EW + trap veto eligibility) + make_trap_veto(value_trigger 재사용 래퍼). 입력=universe {ticker→metrics}+market_caps+metric_signs. smoke PASS.
- `D:/projects/Inv/stock/value_trigger.py` — `bypass_gate1` 파라미터 추가(run_value_trigger, default False=byte-identical). −10% 1차게이트 우회, stage-2 trap veto만. 회귀 test_so4 16 passed.
- `D:/projects/Inv/study-research/eq_us/_sleeve_rotation.py` — 2층 실측(predictive single-slope + shrunk inverse-vol base + walk-forward OOS). 결과 `_sleeve_rotation_results.json`=STATIC.
- 검토 스크립트(/tmp, 재현용 핵심): regime-conditional 정설 검정 + down-capture(defensive 0.57) + mega Sharpe/Sortino. ★재실행 시 `_sleeve_rotation.py`의 load_sleeve_monthly_ret/load_macro_monthly/shrunk_inverse_vol/fixed_b_t 재사용.

**자문 raw (reflection-verify 대상)**:
- `D:/projects/Inv/.consult-us-selection-layer-brief.md` (selection 2R)
- `D:/projects/Inv/.consult-us-sleeve-rotation-brief.md` (rotation 3R)
- `D:/projects/Inv/.consult-us-defensive-paradox-brief.md` (정설 2채널)

**기존 파이프라인 (수정 금지, WIRE3 배선 대상)**:
- `core/stock_track.py:155 generate_candidate` (종목1개→value_trigger, universe 루프 없음=selection 자리) / `stock/valuation.py:244 value_stock`(valuation_gap=절대갭, :296-304 own-history fallback) / `core/risk_gate.py:47-49`(cap 10%/30%/turnover20%) / `core/brain/regime_to_weights.py`(1층, BASE_WEIGHTS us_stock 0.25, sub-sleeve 없음) / `stock/fhc_adapter.py:57`(cs_rank_IC outcome, valuation_cs_z mediator, "supervisor가 universe 확장") / `core/assume/weight_card.py:208 derive_weights`(Grinold Ω·IC) + `:258 synthesize_l1`.

**박제 문서**: `progress-stock-corr-layer-20260603.md` §2.7(wire 트랙+3층표) + ckpt-202606050305 / `~/.claude/memory/promotion-log.md` ERROR head + empirical-claim §1.8.

## 5. 미해결 · 실패 · 딜레마

### ★mega 과소배분 딜레마 (사용자 핵심 관심, 결론 = 교정 보류)
실측: mega tot_vol 7.29%(최고)·연수익 +36.5%(최고)·**Sharpe 1.45/Sortino 1.65 최고**인데 inverse-vol 비중 **0.23 최저**(shrunk 0.28). = inverse-vol이 risk-adjusted return 정보를 무시해 mega 과소배분 = "억울" 맞음.
- **단 교정 딜레마 3**: (1) downside-vol(Sortino) base로 바꿔도 mega 0.24로 **거의 안 변함**(mega는 up도 down도 둘 다 큼, down_dev 6.39%) = 변동 방향 교정으로 해결 안 됨. (2) mega 비중 올리려면 = return/Sharpe를 base에 넣어야 = ★**점추정 prior 박제 = 2015-26 mega(Mag7) 대세 베팅** = 자문·우리 원칙(small-n 점추정 금지) 위반. (3) 표본: mega Sharpe 전반 1.78→후반 1.20 = 우위 유지하나 약화 = mega 대세 영속 가정 위험.
- **결론**: mega 과소는 "억울하지만 정직한 보수성"(return 예측 안 믿고 risk만). 올리는 건 OOS 위험. → inverse-vol base 유지가 안전. mega 상승 잠재력은 **3층 selection(mega basket 통째 보유)에서 별도 관리**, 비중 박제로 추구하지 말 것. (재검 후보: risk-parity + 약한 momentum overlay = OOS gate 통과 시만, rotation과 동일 신중.)

### 기타 미해결
- **reflection-verify 미실행**: 자문 raw 3개 ↔ 구현(selection.py/value_trigger/_sleeve_rotation) 전수 매핑 subagent = WIRE3 후 일괄.
- **WIRE3~6 미구현**: selection 조립(실데이터 시뮬) → net-alpha → 한국 → order 조립.
- **한국 sleeve**: 3층 동일 구조, 단 3층 KRX 산업 peer median(french 미국전용) + 한국 STT net-alpha hard + 2층 한국 sleeve rotation 별도 실측. 한국 7산업 DART 연구는 완료.
- **2층 rotation 재측정 금지**: STATIC 확정(predictive 소멸 modal outcome). 차기 vintage/추가 데이터 전 재시도 금지. flip-register: predictive 생존·sign 안정성·base 분해.

## 6. 자문 종합 (3회, 원문=§4 brief)

- **selection 2R**(gemini+claude): −10% 게이트 제거(cross-sectional 픽 전멸) / sleeve-level demean(measured=traded IC) / trap veto pre-selection / robust z(median/MAD) / capped-EW(종목5%섹터20%, risk_gate 안쪽) / net-alpha 미국 soft 한국 hard.
- **rotation 3R**: discrete 4-regime overfitting 폐기 → 연속 predictive single-slope / per-sleeve 기계론축(sign 고정) / shrunk inverse-vol base(risk-neutral mandate) / walk-forward OOS gate binding / **predictive 소멸 = modal outcome** → 실측 STATIC 적중.
- **defensive paradox 2채널**: "정설 틀림" 과함. 내 측정 결함 3 = self-referential base 항등식(∑excess≡0, def음=mega양 거울) + predictive=rebound + credit≠침체. down-capture 재측정 = 정설 robust(def **0.68**, `_downcapture.py` 영속 / 하락월 n=37 / cyc1.22·mega1.24 공격). 정설은 inverse-vol base에 비중 내장, rotation 미식별 static. → ERROR + empirical-claim §1.8 자산화.
- **★reflection-verify (WIRE3 후, foreground subagent)**: 자문 raw 3개 ↔ 구현(selection.py/value_trigger/_sleeve_rotation/progress §2.7) 전수 매핑 = 20항목 R16 / S2(net-alpha 미국soft·한국hard 사유박제) / **누락 0 / 역방향 0**(기각항목 discrete 4-regime·MVO optimizer 코드 부재 확인) / 정량 magnitude(floor $500M·cap 0.05/0.20·base 0.31/0.41/0.28·AXIS sign) 전항목 일치. = 자문 누락 없이 구현 반영 확인.

### ★종합 결론
우리 연구가 실증한 alpha = **3층(sleeve 안 cross-sectional value/net_iss)**. 1층 거시 기구현, 2층 rotation 데이터 미지지(static), 정설은 비중으로 내장. mega 과소는 보수성(교정=표본 박제 위험). **★WIRE3 정합 시뮬 = cyclical value 강건(top-K excess +0.087)·defensive PARTIAL 재현(net_iss 단독 음→ep 합성 +0.022)·reflection PASS.** 다음 = WIRE4 net-alpha(turnover band) 또는 generate_candidate end-to-end 배선(valuation adapter 의존, WIRE 후반).
