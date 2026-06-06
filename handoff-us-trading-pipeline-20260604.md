---
tags: [type/handoff, domain/inv, scope/equity-us, topic/trading-pipeline, status/in-progress]
date: 2026-06-04
owner: main (btn-button, opus 1m)
next-action: "★미국 주식 매매 = factor 트랙 종료(value+net_issuance 본질, Phase W 약축 보완 0=전부 null) + 매매 파이프라인 검토 완료(이미 구현, 중복무) → ★'매매 불가' 실체 = 실행 wire 3갭. 사용자 '1-3 전부' 지시 = wire 갭 메우기. ★1순위(필수 동의) = cross-sectional selection 레이어(연구 value spread→종목픽 변환부, consult-brief-r2-execution-layer §1 gap). 2 = sector_multiples French49 라이브 fetch(Ken French 49industry CSV 무료 1회 검증 가능). 3 = GatedOrderRouter→KisClient 조립부(연결 시 거래 시작, DRY_RUN/EMERGENCY_STOP kis_client.py:35 로 on/off). go-live 경계(README-unattended-safety D1~D5 사람게이트). 잔여: mega sleeve yaml 표현교체 + 한국 G-E 게이트(사용자 재confirm)."
resume_priority: "wire 3갭 selection 레이어(1순위)부터. factor 연구는 Phase W로 종료(보완 0=value 본질)."
---

# handoff — 미국 주식 매매 파이프라인 검토 + factor 트랙 종료 (2026-06-04)

## 1. 현재 상태 + 첫 행동

**미국 주식 factor 연구 트랙 = 종료.** value(PBR/EV cyclical CONFIRM) + net_issuance(defensive PARTIAL) + DEF-2 interaction(frozen metadata-only)이 robust 전부. ★over-kill 정정(DEF-2 CONFIRM 복원, rank-FM)·Phase W 약축 보완(quality/accruals/low-vol 전부 null)·G-C audit PASS 전부 닫힘. **"축 부실→보완" = 추가 보완 0 = value 1축은 측정 누락 아닌 데이터 본질**.

**매매 파이프라인 = 이미 구현(중복 개발 무).** 3-subagent 검토 결론. "매매 불가" 실체 = factor 부족이 아닌 ★**실행 wire 3갭**.

**첫 행동**: 사용자 "1-3 전부" 지시 = wire 3갭 메우기. ★1순위 = **cross-sectional selection 레이어**(우리 연구 value spread → universe top-N 종목 픽 변환부). consult-brief-r2-execution-layer-20260603.md §1 = "현 코드 own-history 시계열분위만, cross-sectional gap" 박제. 착수 전 사용자 진행 confirm.

## 2. 진행 맵 (ckpt 체인)

| 단계 | 결과 | ckpt (progress-stock-corr-layer-20260603.md) |
|---|---|---|
| 11가설 검증 | BY 생존 DEF-2 + DEF-1 | BW8 |
| over-kill 정정 | DEF-2 TENTATIVE→**CONFIRM 복원**(rank-FM 척도통일) | ckpt-040420 |
| frozen_register | metadata-only(base_weight=null) | study_session.yaml |
| BW7 G-C audit | **PASS**(author≠auditor, hard-fail 0) | ckpt-040510 |
| Phase W 약축 보완 | quality/accruals/low-vol **전부 null** | ckpt-040530 |
| ★매매 파이프라인 검토 | 이미 구현+중복무, wire 3갭 | ckpt-040610 |
| 레저 박제 | candidate-ledger §Phase W + §매매연결 | ckpt-040625 |

## 3. 사용자 박제 (대화 고유 framing)

- "이대로는 매매 불가, 그냥 넘어갈 수 없다" → 매매 파이프라인 검토 발단.
- "1-3 다 해야지" = wire 3갭 전부 메우기. **"1은 필수 최우선 동의"**.
- "3은 연결하면 거래 바로? on/off 못 하나" → 답: 연결 시 거래 시작, DRY_RUN/EMERGENCY_STOP 으로 on/off 가능.
- "2는 실사용 가능 수준? 빠른 검증법?" → 답: Ken French 49industry CSV 무료 1회 fetch 검증.
- "1-3 넘어가기 전 레저 박제 안 한 거 충실 업데이트" → ✅ candidate-ledger Phase W + 매매연결 완료.
- "기존 결과 깃허브보다 우수해서 참고없음/논문이 낫다 류 결론 ★금지. 내용 부족해도 매매 타이밍 방식 검토" (subagent 제약).
- "축 부실→보완 이후 추가 보완 없나" → 답: Phase W 3시도 전부 null = 보완 0.

## 4. 파일 인벤토리 (절대경로)

**연구 산출 (factor 트랙)**:
- `D:/projects/Inv/study-research/eq_us/REWORK-prereg-11hypotheses-20260604.md` — 11가설 + §over-kill 최종정정 + §Phase W (SSOT)
- `D:/projects/Inv/study-research/eq_us/candidate-ledger.md` — §Phase W + §매매 파이프라인 연결 박제
- `D:/projects/Inv/study-research/eq_us/study_session.yaml` — frozen_register(DEF-2/CYC-1/DEF-1 metadata-only) + mega 표현교체
- driver: `industries/us_cyclical/raw-v3/_b2_{cyclical_interactions,def_rankfm 대응 cyc_rankfm,quality_single,w4_lowvol}.py` + `us_defensive/raw-v3/_b2_{def_rankfm,quality_single,w2_accruals}.py`
- 자문 brief: `D:/projects/Inv/.consult-us-weak-signal-revival-brief.md` + `.consult-us-overkill-check-brief.md`

**매매 파이프라인 (subagent 검토 대상)**:
- `D:/projects/Inv/architecture.md` (:52-84 _refs 매핑, :90 "coin 재사용·새로 만들지 말 것", :209-217 value_trigger 2단게이트)
- `D:/projects/Inv/stock/value_trigger.py` (Gate1Thresholds :55, passes_gate1 :115/:130, judge_value_trap :289)
- `D:/projects/Inv/stock/fhc_adapter.py` (exposure_card_to_fhc :22 — 연구 indicator → FHCard.outcome)
- `D:/projects/Inv/core/assume/fhc.py` (transition :254, confirm e≥20 :293) + `bonus_channel.py` (size_with_bonus :44)
- `D:/projects/Inv/core/risk_gate.py` (GatedOrderRouter.submit :577, 우회불가)
- `D:/projects/Inv/core/stock_track.py` (generate_candidate :155, _apply_r15_sizing :242, _NEXT_CHECK_MINUTES :42)
- `D:/projects/Inv/stock/kis_client.py` (order NAS/NYS :234, DRY_RUN/EMERGENCY_STOP :35, check_price_limit :565)
- `D:/projects/Inv/stock/data/french_factors.py` (FF5 PIT vintage, _knowable_from lookahead 차단) + `sector_multiples.py` (French49Provider 49산업 peer 상대저평가)
- `D:/projects/Inv/consult-brief-r2-execution-layer-20260603.md` (§1 cross-sectional selection gap)
- `D:/projects/Inv/README-unattended-safety.md` (:104-113 go-live D1~D5 사람게이트)
- reference: `_refs/` 22 repo (TradingAgents/ai-hedge-fund/jumpmodels/nautilus_trader/skfolio/Riskfolio-Lib/PyPortfolioOpt 등) + 원본 github `jsh8603-web/coin` (`agents/base_agent.py` calculate_buy_score :220/detect_regime :757)

## 5. 미해결 · 실패 · 삽질 위험

- **wire 3갭 (미구현, 핵심 미해결)**: ①cross-sectional selection 레이어 부재 ②sector_multiples French49 라이브 fetch 이연(N-T1-SECTORMULT, Damodaran xls URL+French49) ③GatedOrderRouter→KisClient 조립부 미배선(construction).
- **삽질 위험**: cross-sectional selection 신규 작성 시 기존 `value_trigger.py` 2단게이트(단일종목 value-trap, 이미 구현)를 모르고 종목 스코어링 재구현 = 중복 위험(현재 미발생). selection 레이어는 "universe spread→픽" 변환만, trap 판정은 기존 게이트 재사용.
- **Phase W 실패 기록**: quality 단일(자문 "검출 가능" prior가 데이터 반증, value↔quality 음상관≈0=직교 stacking 이론이득 미실현) / accruals null / low-vol within-demean이 BAB 죽임. ★재시도 금지(전부 null 확정). 미시도 보류 = W3 정규화PER(ROI낮음) / SUE-PEAD(8-K 데이터게이트) / mega forward(유료 IBES).
- **mega 표현교체 잔여**: REWORK 반영 완료, us_mega_tech/summary.yaml + study_session.yaml mega block 미반영("alpha=0"→"검출불능+무료PIT불가 탐색종료").
- **한국 G-E 게이트**: 미국 완주 후 한국 7산업 묶음 자문 = 사용자 재confirm 의무(RW5). 미진입.
- **★연구 의미 정정 (사용자 질문 2026-06-04)**: 우리 factor 연구 = selection 레이어를 "더한" 게 아니라 = value_trigger 게이트 valuation 입력(cyclical PBR/EV·defensive net_iss 中 어느 factor가 sector-relative robust한지) 검증/캘리브레이션. ★selection 레이어 자체는 wire 갭(미구현).
- **★한국 매매 연결 점검 (미확인, 다음 세션 항목)**: french(FF5/French49)=★미국 전용(Ken French US 데이터). 파이프라인(value_trigger/risk_gate/sizing/kis_client)=★자산무관 한·미 공유, KIS=한국 native+미국(NAS/NYS) 둘 다. ★한국 sector-relative valuation은 French49 아닌 KRX 산업분류 필요 — 구현 여부 코드 재확인 미완. 한국 7산업 DART valuation 연구는 완료(매매 연결은 미국 wire 우선).

## 6. 조사 종합 (subagent 3 원문 포인터 + 핵심)

> ★원문 = task transcript (세션 휘발 가능, 핵심 박제). task ID 명시.

### #1 우리 매매 파이프라인 (task `a8905df1dfe59dd4b`)
- **매매 로직 실재**: signal→sizing→risk_gate→order→breaker 전 체인 구현, go-live(실주문)만 stub.
- **타이밍 = 달력 rebalance 아닌 다단 트리거**: ①entry threshold cross(가격-10% AND 가치갭≥0.25, value_trigger.py:130)+value-trap veto ②factor confirm = anytime-valid e-process e≥20(fhc.py:293, 누적증거) ③재평가 동적 8~24h(stock_track.py:42) ④exit = risk_gate hard stop(-5/-10%)+regime-break breaker(classify_decay_vs_regime)+MDD/vol kill-switch FSM(-8/-15%).
- **sizing 3겹**: L1 baseline(factor가중) × value_trigger down-only attenuator × FHC bonus(min(L1+Σbonus, C)). risk_sizing Ledoit-Wolf→HRP fallback.
- **risk_gate**: RiskGate.check() hard rule 순차(일손실-5%/per-pos-10%/상관캡0.7/maxweight10%·섹터30%/turnover20%), GatedOrderRouter 우회불가, LLM import 0.
- **갭**: 실주문 ExchangeAdapter 구현 0(FakeExchange만), net-alpha(turnover/tcost) factor IC 게이트 미반영, FHC live 루프 미배선(INV-11 off=byte-identical), mediator 실데이터 미연결.

### #2 reference repo + french (task `a7402c7b89595ba4c`)
- **reference = `jsh8603-web/coin`**(BTC 자동매매 v1.29.0). `D:/projects/Inv` 자체가 일반화 트리. architecture.md:90 "새로 만들지 말 것". 외부 보조 22 repo = `_refs/` 하위.
- **coin 타이밍 = 점수제+5단계 레짐적응형**: 매수 calculate_buy_score≥70(base_agent.py:220) / detect_regime bull~crisis(:757) / 매도 sell_score 8시그널 레짐차등(bull85↑억제·bear40↓즉시, :389) / 트레일링 레짐별(-15%~-1.5%, :448) / 이중손절(-5/-10%) / Kelly+레짐상한.
- **주식 일반화 = value_trigger.py 2단게이트**(가격급락 AND margin-of-safety→Claude/Damodaran value-trap 판정).
- **french 2파일** (`stock/data/`): `french_factors.py` = FF5(MKT/SMB/HML/RMW/CMA) PIT vintage, _knowable_from 공표시차(월35일/일2일) lookahead 차단, build_indicator_matrix 소비. `sector_multiples.py`(French49Provider) = ★Ken French 49산업 → 섹터 상대 저평가 → value_trigger "내재가치갭" 입력 = ★언제 사는지 valuation 타이밍 신호. indicator-ledger sector_relative_multiple candidate(:127) 직결. 라이브 fetch 이연(Damodaran xls+French49).

### #3 미국 매매 + 중복 점검 (task `a22e12ec3621a4ee0`)
- **미국 경로**: factor(_b2_*.py)→summary.yaml indicators_passed→fhc_adapter:22→value_trigger 2단→sizing→GatedOrderRouter:557→kis_client.order(NAS/NYS, FX 환산 :595). KIS pykis 래퍼 US 마켓 지원.
- **타이밍**: 이벤트 진입(가격-10%+가치갭) + 슬리브 밴드(us_stock 0.10~0.45) 이탈 리밸런스(portfolio_orchestrator:233) + regime 월간 갱신. ★정기 월간 일괄 rebalance 스케줄러 미구현.
- **factor→매매 연결점**: value 연구 = FHCard.outcome leg(metric=cs_rank_IC) + R15 weight 합성. mediator=섹터 펀더멘털(valuation_cs_z), 부재 시 fail-closed.
- **★중복개발 = 무**: 연구는 IC 측정→summary.yaml indicator 산출, sizing/timing/order 재구현 0. 문제는 중복 아닌 wire 미완(selection 레이어 + GatedOrderRouter→KisClient 조립부 2갭).

### ★종합 결론
- 매매 타이밍 메커니즘 = coin 레짐적응형 점수제 + 주식 value_trigger 2단게이트 + French49 sector-relative valuation. ★이미 설계·구현.
- value 1축 연구 = French49 sector-relative valuation 신호 robust 입증 = value_trigger 게이트 입력 정당화/캘리브레이션.
- "value 1축이라 매매 불가" = ★구조 오해. 매매 막힌 건 wire 3갭(selection/sector_multiples 라이브/order 조립). factor 다양성(Phase W)은 sizing tilt 문제지 타이밍과 별 레이어.
