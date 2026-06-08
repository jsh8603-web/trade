---
next-action: 주식 밸류 게이트 설계 자문 3R(gemini-web+claude-web 병렬, 우리 파이프라인 브리핑) → 게이트 결정 → 다종목 + 전체자산 배분 entry → 풀가동
session: btn-Inv (opus)
date: 2026-06-07
---

# handoff — P3-2 주식 파이프라인 백테스트 (데이터레이어 보수 완료, 게이트 자문 대기)

## §1 현재 상태 · 첫 행동
- **완료**: P0/P1/P2(A1~A6+B1~B5)/P2-3(diagnostics)/P3-0(coverage)/P3-prep(C1~C6b) + **주식 시계열 PIT lookahead 보수**.
- **첫 행동(재개)**: 주식 밸류 **게이트 설계 자문 3R** — `gemini-web-consult` + `claude-web-consult` 병렬(Skill). 우리 밸류 파이프라인을 CIO 페르소나로 브리핑(아래 §6) → deep-value dip(현행) vs systematic value(bypass) 수렴 → 게이트 결정 → 다종목 배치 + 전체자산 배분 entry.

## §2 진행맵
- P3-2(테스트1 백테스트) 진행 중. 두 트랙(사용자 확정): **(1) 개별 주식**(프로덕션 stock_track) + **(2) 전체 자산 배분**(orchestrator). 소규모 검증 자유.
- ✅ 데이터레이어 보수 commit: **da5f85c**(EDGAR URL fix), **1b8a253**(시계열 PIT lookahead + EDGAR 캐시 + limit 60).
- ⏳ 게이트 결정 → 다종목 → 전체자산 entry(미구현) → 풀가동.

## §3 사용자 박제 (대화 고유 결정)
- **프로덕션 라인으로 테스트**(별도 우회 도구 금지). 개별 주식=run_stock_backtest(프로덕션 stock_track 경유), 전체 자산=orchestrator.allocate 시계열.
- **개별 주식 + 전체 자산 둘 다** 백테스트. 소규모 smoke는 재량.
- 게이트 설계(gate1 -10% dip 필수)는 **L1/ledger 영역** — 무단 변경 금지, 자문+사용자 결정.
- "태스크 위해 필요한 연결·보수 자율 진행"(데이터레이어 fix 승인). go-live·push 미접촉. LLM off 결정론(P3-2 1층).

## §4 파일 inventory (절대경로 D:/projects/Inv/)
- 보수: `core/stock_track.py`(collect_market_state(as_of) 매 bar 동적 PIT, _eff_quote/_eff_funds=override 우선·없으면 _dynamic, __init__ _fund_provider/_quote_provider/_region 주입), `stock/data/edgar_provider.py`(_ticker_to_cik URL=www.sec.gov fix + _TICKERS_CACHE 전역 + _FACTS_CACHE cik별), `stock/data/fundamentals_pit_provider.py`(모듈+클래스 메서드 limit 12→60), `scripts/run_stock_backtest.py`(provider 주입, override 폐기, _diag_fund/_diag_quote 진단라벨).
- 측정: `backtest/diagnostics.py`(four_layer_metrics·per_asset_attribution[self-ref base 금지]·confirm_gate[NW HAC·block-boot·walk-forward]).
- 게이트 SSOT: `stock/value_trigger.py`(passes_gate1:115 = price_drop_pct 0.10 + valuation_gap_min 0.25 동시, _bypass_gate1 면제), `stock/valuation.py`(value_stock=DCF+멀티플밴드).

## §5 미해결 · 실패 (삽질 방지)
- ★**거래 0 원인**: `passes_gate1`(value_trigger.py:131)이 **가격 -10% 급락 필수**(coin buy-the-dip 혈통). 평상시 저평가여도 매수 0 → 거래 희박. JPM 2년 smoke=0 trades(fund ok·lookahead 차단됨). _bypass_gate1=True 면 dip 게이트 면제(systematic value). **자문 3R로 결정**.
- **smoke 결과**: 코인 BTC 1년=NO_GO(sharpe-1.51, 본분석 대상). 주식 AAPL/JPM=fund ok·거래0(gate1).
- **fixture-PASS 사각지대 3연속**(EDGAR URL·pit limit·시계열 lookahead) → harness2 Verifier 가 실네트워크 과거 시계열 미검증. 메인 직접+실 smoke 로 전환함.
- **전체자산 배분 entry 미구현**: run_multiasset.py=라이브 1사이클(run_one_cycle). 시계열 백테스트 entry 신규 필요. collect_market_state(as_of) 내부 _macro_orch.allocate→macro_weights 시계열로 감싸면 됨(sleeve_returns × weights → NAV).
- **test_so7_p4_golden_rule::test_audit_document_covers_dart_edgar FAIL**=`.harness2/audit-goldenrule-p4.md` 부재(이전 P4 stale 문서, 내 변경 직교). 별도 정리 대상.
- DART(KR) graceful: 키 없으면 dart_key_missing→KR 밸류 unavailable→벤치베타 대체(C6b는 hold 처리=미완, P3-2서 검증).

## §6 자문 브리핑 (주식 밸류 파이프라인 — CIO 페르소나, 코드어 0)
**전략**: 내재가치(간이 다단계 DCF bear/base/bull 확률가중 + PER/PBR/EV-EBITDA 멀티플 밴드) 대비 저평가 종목 매수 = value investing(Damodaran story→numbers→value).
**2단 게이트**:
- **Gate1(진입 후보)**: ① 최근 윈도우 가격 -10%+ 하락 **AND** ② 내재가치 갭 ≥25%(가격<내재가치 75%) **동시** 충족. 의도="단순 buy-the-dip 금지"(가격만 빠진 게 아니라 가치 대비 싸야).
- **Gate2(trap veto)**: heavy agent(Claude/Damodaran 페르소나)가 "싸진 기회 vs thesis 붕괴(value-trap)" 판정 → 함정확률로 사이징 억제.
**쟁점(자문 질문)**: Gate1의 "가격 -10% 급락 필수"가 value 전략 진입으로 타당한가?
- A) **현행(deep-value contrarian)**: 급락+저평가 동시 = 역발상. 거래 희박, 보수적.
- B) **systematic value(bypass_gate1)**: 급락 무관, 저평가 rank면 상시 매수. 거래↑, 일반적 팩터.
- 로컬 의견: 백테스트 "value alpha 측정" 목적엔 B(표본 多)가 적합하나, A도 유효 전략(역발상). Gate1이 contrarian 모멘텀 조건을 value에 강결합 = 두 팩터 혼재. 분리(value 진입 + dip은 타이밍 보조)가 나을 수.

## §7 자문 후 작업 순서
1. 자문 3R 수렴 → 게이트 결정(A/B/분리) → (B/분리면) _bypass_gate1 경로 or gate1 재설계(ledger 박제, 무단변경 금지).
2. 개별 주식 다종목 배치(US EDGAR 무료 ~10종목, 2017~) → per_asset_attribution(passive 대비 excess).
3. 전체자산 배분 entry 신규(run_multiasset_backtest.py): collect_market_state(as_of) 시계열 → macro_weights × sleeve_returns → NAV + judge/risk_gate. 4층+per-asset.
4. 풀가동 2017~2026 → 수익성 판정(3차 게이트).
