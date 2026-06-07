# progress — 최종 테스트 진입 정리 + e2e/테스트/자기진화 (2026-06-07)

> SSOT plan = [plan-final-test-20260607.md](./plan-final-test-20260607.md). 단일 세션(btn-Inv, opus) 오케스트레이션, teammate 동시 ≤5.
> 인계: [handoff-p3-stock-pipeline-20260607.md](./handoff-p3-stock-pipeline-20260607.md) (최신, P3-2 주식) / [handoff-final-test-p2-20260607.md](./handoff-final-test-p2-20260607.md)
>
> [ckpt-202606071540:btn-Inv] (1)마지막결정: P3-2 주식 시계열 PIT lookahead 보수 완료(commit 1b8a253·da5f85c — StockTrack collect_market_state(as_of) 매 bar 동적PIT, EDGAR URL/캐시/limit60). 거래0 원인=gate1 가격-10%dip 필수(value_trigger.py:131, coin 혈통). (2)다음의도: 주식 밸류 게이트 자문 3R(gemini+claude, deep-value dip vs systematic value) → 결정 → 다종목 + 전체자산 배분 entry(미구현, run_multiasset_backtest 신규) → 풀가동. (3)동기화: handoff §6 자문브리핑·§7 작업순서. 게이트=L1/ledger 무단변경 금지. fixture-PASS 사각지대 3연속→메인 직접+실smoke. push·go-live 미접촉.
>
> [ckpt-202606070116:btn-Inv] (1)마지막결정: P2 harness2 진입 — 팀 h2-Inv-p2 생성·SR Pre-Review(mode C) 완료. SR이 thin wiring 치명결함 3 적발(stock dict→무음hold line439·engine corr/sector 하드코딩 line489,493 게이트 미발동·drill-down 병합층) 전부 ACCEPT, harness2.md A2/A3 반영. (2)다음의도: harness2.md B2 "병합층 태깅" 마무리 → `teammate-spawn.sh spawn .harness2 h2-Inv-p2` PLAN으로 Worker/Verifier/watchdog dispatch → P2A 코드배선. (3)동기화: handoff §1 첫행동·§6 SR directive. plan/progress/CODEMAP/CLAUDE/README 박제 완료, 커밋 보류.
> 진입 스냅샷: README 542줄(이미 코드색인 성격)·CLAUDE.md 474줄(코인 레거시 대량)·ledger 충실·루트 untracked(.p2 176/.consult 126/.tmp 17/.audit 6/md 93).

## P0 — 현황 진단 (병렬) ✅
- [x] **P0-1** e2e 연결성 맵 — `.p0-connectivity-map.md` (라이브=레거시 코인봇만, core 트랙 호출처0, risk_gate/judge/KIS entry 미배선=L0 10건)
- [x] **P0-2** 루트 분류 판정표 — `.p0-root-cleanup-plan.md` (357항목)
+ [x] (추가) 진단인프라 조사 `.p2b-diag-infra-survey.md` / e2e스모크 `.p2-smoke-readiness.md` (replay 즉시가능·DRY_RUN 안전)

## P1 — 문서 체계 재편 ✅
- [x] **P1-1** 사용자용 README.md 신규 (교체 완료, 370줄)
- [x] **P1-2** CODEMAP.md 신설 (파이프라인 0~10단계+백테스트+인프라+부록A/B 디버깅색인, TODO 5건 반영)
- [x] **P1-3** CLAUDE.md 재작성 (운영기준+L0~L3+문서지도, 레거시→docs/legacy-coinbot.md 보존)
- [x] **P1-4** 루트 정리 — gitignore 추적차단(357→9) + 참고문서 archive 이동. ⚠️물리삭제(.p2 csv/json 105·자문브리핑 90)는 불가역이라 보류(gitignore로 충분, 디스크정리는 별도 확인)

## P2 — e2e 연결성 점검 + 진단 인프라
- [x] **P2-1** 파이프라인별 e2e 스모크 → L0 식별·수정 — ✅ P2A 배선 A1~A6(run_replay --risk-pipeline opt-in·run_multiasset.py entry·stock dict→Decision 어댑터·GatedOrderRouter 합산층 corr/sector·judge down-only·Upbit+KIS paper 주문). A1~A5 Verifier PASSED, A6=메인 독립검증 주입(commit없는 회귀SO=Verifier 구조적 픽업불가). git d2ca264
- [x] **P2-2** stage attribution 로깅 + 단계 불변식 체크 — ✅ P2B B1~B5(메인 직접, harness2 팀 사망 후 인계). B1 _sv 6→10필드 / B2 bar_attrib.jsonl env INV_DIAG_ATTRIB opt-in(bar×asset×stage×layer) / B3 _reject_reasons / B4 data_empty / B5 llm_contract_fail. 검증=golden9+wire24 passed, on 30줄·off 미생성(byte-identical). git **c49ba6d**
- [x] **P2-3** 문제정의·벤치마크 확정 + 측정 스크립트 — ✅ `backtest/diagnostics.py`(4층 지표 four_layer_metrics + per_asset_attribution[★self-ref base 금지=외부 buy&hold] + confirm_gate[NW HAC t·block-bootstrap CI·walk-forward 부호일관, 단정금지]). 재사용=common/metrics·rank_ic·_nw_lags. tests/test_diagnostics.py 9 passed. git **22b4c06**

### P3-prep — 주식 백테스트 데이터레이어 (harness2 PC, ✅ 완료)
- [x] **C1** credit BAA10Y splice(Δ단위, 2023-05 cutover) ✅ `d78a99d` / **C2** silent default 가드 5곳(source_missing/data_empty 라벨) ✅ `02f131f` / **C3** 주식 OHLCV provider(pykrx·yfinance+jsonl 캐시) ✅ `70023c4` / **C4** quote_at provider(pit.as_of 경유) ✅ `52443b1` / **C5** PIT 펀더(EDGAR/DART graceful) ✅ `7fb7078` / **C6a** 생존편향 PIT 유니버스(get_universe_at+상폐 코호트, SR 적발 버그 수정) ✅ `ab56e49` / **C6b** 주식 백테스트 entry(DRY_RUN 1사이클+4층 지표) ✅ `cb223f1`
- 검증: C1~C6b 전부 Verifier PASSED, 전체 도메인 회귀 42 passed(off byte-identical 보존). SR Pre-Review directive 4건 반영(Δ splice·pit.as_of·DART 벤치베타·C6a 생존편향).
- ⚠️ **caveat(C6b verdict)**: DART 부재 시 "벤치베타 대체"가 명시 미구현 → fundamentals=[] 시 StockTrack.hold(confidence=0.0) 처리. SR directive "비중0 금지=벤치베타" 부분 미충족 → **P3-2 실백테스트서 KR 종목 배분 편향 측정 의무**(액티브 숏 편향 잔존 가능).
- ★silent-death 2회(C3→C4 53분·C4→C5 28분, watch 비활성 사각지대)→Supervisor idle_notification+fallback 점검 복구. K 기록(promotion-log).

## P3 — 테스트1: 백테스트 (10년 in-sample + 1~2년 OOS)
- [x] **P3-0** 데이터 coverage 실측(Explore 인벤토리) — ✅ **중대 발견 3건**:
  - **(1) 10년(2016~) 불가**: 코인 BTC-KRW=Upbit **2017~**(2016 전무, RuntimeError=non-silent) / credit HY OAS(BAMLH0A0HYM2)=FRED **2023-05~**만(BofA 라이센스, 2016~2023-04 부재→BAA10Y proxy 1986~ 대체 가능) / **주식 KR/US=미구현**(stock_track 스켈레톤+override만, 실소스 부재). → **실질 백테스트=2017-01~2026(~9년), 주식 제외 or mock**.
  - **(2) 풍부**: sleeve SPY/EWY/DBC/GLD/BND/BIL=2007~ ✅ / factor real·dollar·oil·vol·breakeven·fx=2003~ ✅ / FRED 거시 대부분 1960s~ ✅.
  - **(3) ★silent default 위험 5곳**(plan §1.1 금지 대상): factor_returns.py:61-63 `except→None`(Λ=단위 fallback🔴) / sleeve_returns.py:71-73 `except→None`(IC0 skip🔴) / fred_adapter.py:168-169 `except→None`(cascade degrade🔴) / macro_market.py:60-61 `except→[]`🟡 / regime_classifier.py:108-112 stale 재사용🟡. → P3-2 풀가동 전 명시적 None 체크/라벨(B4 data_empty 연계) 가드 필요.
- [x] **P3-G 주식 밸류 게이트 설계 자문+검증** — ✅ 자문 2R(gemini-web+claude-web 병렬) + 데이터검증(`.p3-gate-consult-verify.py`, yfinance 10종목 2010~2026) 수렴. **결론**: A안(value+급락 -10% AND 강결합) 기각 / **측정=B**(다종목 횡단면 rank-IC·decile L/S, FWL 잔차화 size·sector·momentum) / **운용=분리안**(value 진입 + dip은 ceiling-bounded 사이징 변조 ×(1−trap_p), nested: dip-off=측정 베이스라인 B와 일치) / **단일종목=배관 스모크용**(alpha 측정 불가). ★검증 데이터(무비판 차단): **C2** 저평가(<0.75×200dMA) 독립에피소드 중앙값 **1.5개**(16년 일봉, 절반 종목 0)=단일종목 유효N 붕괴 **결정적 지지** / **C1** 21d수익 시장 R² 중앙값 **0.21**(idio 79%)=급락 '거의 전부 시장'은 **과장→자문 magnitude 정정**(잔차화 필요는 지지) / **C3** -10%급락 중 시장동반 **0.544**=idio 46% trap위험 지지. ★코드현황: `value_trigger.bypass_gate1` **이미 존재**(2026-06-04 자문 수렴 산물=cross-sectional 경로 -10% 면제+stage2 trap veto). 이번 자문=독립 재확인. dip overlay(분리안 사이징 변조)=미구현→P3-3. 산물=`.p3-gate-consult-verify.py`·`.p3-gate-verify-result.csv`·`.gemini-web-last.md`·`.claude-web-basic-last.md`.
- [ ] **P3-1** LLM 3층 처리(1층 10년 off 결정론 / 2층 ★레짐 대표구간 on·off A/B[비용 2의무=응답 hash 재사용+강세/약세/횡보 각 1~2개월만, 전체 매 bar 금지] / 3층 카드·하이쿠 샘플 동작검증) — `model: opus`
- [ ] **P3-2a 다종목 횡단면 측정(순수 B, overlay OFF)** — `stock/selection_pipeline.py`·`cross_sectional_selection.py`(이미 존재) → 백테스트 entry 배선 확인 → US EDGAR 무료 유니버스 rank-IC + decile L/S + FWL 잔차화. **value alpha 베이스라인 동결**(이게 load-bearing claim). — `model: opus`
- [x] **P3-2b 단일종목 스모크(배관 검증)** — ✅ AAPL 2020~2023 `run_stock_backtest --bypass-gate1 --stub-agent` → **n_trades=10, NAV 10M→12M, sharpe 0.74, MDD -8.3%** (EDGAR→value_stock→engine 체결 경로 작동). alpha 아닌 배관 검증(자문 결론=단일종목 alpha 측정 불가). ★**발견·수정 버그 4종**(메인 직접 실측, fixture-PASS 4번째 사각지대): ①`_SeriesQuoteProvider`(매 bar 단일일 yfinance fetch 실패→abstain 폭주, price_series 재사용으로 네트워크0·lookahead 안전) ②**value_stock market_cap 차단**(EDGAR는 shares만·시총 미제공→`edgar_provider` outstanding_shares/ebitda/book_value 매핑 보강[shares unit 허용+D&A 합성] + value_stock `outstanding_shares×price` fallback) ③**value_stock staleness**(fundamentals[0]=최古 가정인데 pit_provider는 ascending→가장 오래된 펀더로 밸류, 최신순 정렬 방어 추가) ④**engine L3a 계약**(`getattr(decision,"action")` — stock은 dict[key="decision"]→항상 hold→buy 전멸, dict/객체 양쪽 처리). ★회귀: baseline 63fail→45fail(새 회귀 0, off byte-identical 보존, _run_legacy 미접촉). 산물=`scripts/run_stock_backtest.py`(_SeriesQuoteProvider·_StubNonTrap·bypass/stub CLI)·`stock/data/edgar_provider.py`·`stock/valuation.py`·`backtest/engine.py`. — `model: opus`
- [ ] **P3-2c 전체자산 배분 entry(신규 구현)** — `run_multiasset_backtest.py`: `collect_market_state(as_of)` 시계열 → macro_weights × sleeve_returns → NAV + judge/risk_gate. 4층+per-asset(self-ref base 금지=외부 buy&hold). — `model: opus`
- [ ] **P3-2d 풀가동 통합** — 위 트랙 2017~2026 in-sample → 4층 지표 vs 벤치 + ★자산별(코인 개별·주식 횡단면·sleeve·자산군) passive 대비 excess attribution(장기 음수=신호결함) → 전략 생존성 1차 판정. — `model: opus`
- [ ] **P3-3** 1~2년 OOS(walk-forward 부호일관) + LLM A/B + 카드 동작 + 레짐 적합 + ★**dip overlay ON/OFF 증분**(Δ Sharpe·IC·turnover·MDD, 비용차감 후 양의 증분으로만 자기정당화, FDR·CPCV inner-fold 튜닝) — `model: opus`
- [ ] **P3-4** 문제 3차 게이트(발견→확정 p·NW·bootstrap·walk-forward→레이어 귀속) → 수정 루프 — `wf: harness2`(코드수정 시)
> 문제 시그널 확정·레이어 귀속표 = plan §3 (3차 게이트 + L0~L3 시그널표)

## P4 — 테스트2: 모의계좌 라이브
- [ ] **P4-1** 라이브 가동 + 실주문(모의) 관측 — `model: opus`
- [ ] **P4-2** 라이브 이슈 L0~L3 귀속 수정 — `model: opus`

## P5a — 자기진화 인제스트·관측 (shadow, P3 앞)
- [ ] **P5a-1** 거래기록 인제스트+귀속·drift+제안 shadow-only(attribution 스키마 공유) — `model: opus`
- [ ] **P5a-2** 진화 e2e 스모크(L0) + lookahead 차단(as-of/라이브한정) — `model: opus`

## P5b — 자기진화 판단 캘리브+승격 (P4 뒤)
- [ ] **P5b-1** L0~L3 자동귀속 휴리스틱 캘리브(수동 라벨 정답셋) + drift/복귀 검증 — `model: opus`
- [ ] **P5b-2** shadow→live 승격(promotion_gate) + CODEMAP·운영기준 박제 — `model: opus`

> Phase 실행순: P0→P1→P2→**P5a**→P3→P4→**P5b**

## ckpt 로그
- (2026-06-07) plan/progress 생성. 다음=P0 병렬 스폰(P0-1 opus 연결성맵 / P0-2 sonnet 루트분류).
