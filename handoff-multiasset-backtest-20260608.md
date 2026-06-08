---
next-action: KR(kr_stock) 9단계+ETF fallback 연결 — kr_stock_holdings 신설(us_stock_holdings 한국판, ETF/EW fallback 위주 펀더 불요) + SUB_SLEEVES["kr_stock"] 채우기 + KODEX ETF 가격 FDR fetch + 업종 Marcap 시총분해. 그후 전체(US 9단계 + KR 9단계 + ETF) 통합.
session: btn-Inv (opus)
date: 2026-06-08
tags: [type/handoff, topic/multiasset-backtest, domain/multiasset]
---

# handoff — 멀티에셋 백테스트 드라이버 + 손익 attribution + ETF fallback (2026-06-08)

> plan=plan-final-test-20260607.md / progress=progress-final-test-20260607.md (상단 ckpt-202606080030)

## §1 현재 상태 · 첫 행동
- **완료(US)**: 정식 멀티에셋 백테스트 드라이버 작동. 거시배분(orchestrator)→업종분해(portfolio_decompose 신설)→9단계 종목선택(construction)→회계 NAV. 자산/산업/종목/regime 손익 attribution + ETF fallback(defensive→XLP) 전부 작동.
- **첫 행동(재개)**: KR(kr_stock) 9단계+ETF 연결 — ★일부 진행됨. **완료**: `portfolio_decompose.SUB_SLEEVES["kr_stock"]`=7업종(financial/battery/bio/shipbuilding/consumer/chemical/auto) 채움 / 드라이버에 `IND_KR`·`KR_SUB`·`KR_ETF_PICKS`(financial 091170/battery 305720/shipbuilding 441540/auto 091180 KODEX) 상수 추가. **다음(미작성)**: `scripts/run_multiasset_backtest.py`에 (1)`load_kr_industry(name)`=eq_kr {업종}/raw-v3/data/{prices,universe}.parquet 로더 (2)`kr_stock_holdings(as_of,kr_data)`=us_stock_holdings:118 한국판(펀더 불요 ETF/EW, market_caps=universe Marcap, routing=_ETF_FALLBACK_ROUTING, ticker fallback=d.get("ticker") or trade_params.market) (3)`_kr_ticker_qret`=KR 종목(prices)+KODEX(FDR _etf) 가격탐색 (4)메인: kr_data 로드+KODEX FDR fetch(`FinanceDataReader.DataReader(코드,start,end)["Close"]`)+루프 port에 kr_stock=kr_ret(없으면 EWY passive) (5)MAB_ETF=on 시 KR 9단계 활성. 그후 전체 통합. ⚠️ US서 ticker/regime 등 4회 디버그 전례 — KR도 디버그 사이클 예상.

## §2 진행맵 (사용자 요구 순서: US 따로 → KR 따로 → 전체)
- **US 따로** ✅: 9단계(cyclical/defensive cheapness + mega_tech EW) + ETF fallback(defensive→XLP) + regime 트랙 작동.
- **KR 따로** ⏳: kr_stock_holdings 미신설(SUB_SLEEVES["kr_stock"]=[] 빈칸). = 다음.
- **전체** ⏳: 현재 KR=EWY passive 섞임. KR 9단계 연결 후 통합.

## §3 사용자 박제 (대화 고유 결정)
- ★사용자 흐름: 손익 성분분해 요구 → ticker버그 발견 → coin sacred 재고 → "모든 파이프라인 정상동작+에러수정이 너의 역할, 복잡하면 자문→데이터검증" 자율위임 → "US 따로/KR 따로/전체 순서" → "**ETF도 다 on**".
- ★코인 sacred ≠ 에러 면제. 현 백테스트 coin=BTC-USD passive(신호 미트랙, us_stock과 비대칭). coin 신호 트랙은 PortfolioState↔Orchestrator 동기화 난제(이전 세션)로 별도 과제. coin calculate_buy_score=mean-reversion 결함(rank-IC 음, 이전 세션).
- ★survivorship = US universe 정적(2026 스냅샷)=미래생존 누수. get_universe_at은 KRX 전용 → US 상폐 데이터 부재로 코드수정 불가 = caveat. 진짜신호 근사 = mega_tech(생존승자) 제외 측정.
- push·go-live·실주문 미접촉. DRY_RUN/KIS paper만. off=byte-identical(opt-in 측정 드라이버라 무관). 안전장치값 무단변경 금지.

## §4 파일 inventory (절대경로 D:/projects/Inv/)
- **신규·수정**: `scripts/run_multiasset_backtest.py`(드라이버, MAB_ETF env로 ETF on/off) / `core/portfolio_decompose.py`(업종분해 신설, SUB_SLEEVES["us_stock"]=[cyclical,defensive,mega_tech]·["kr_stock"]=[]) / `stock/selection_pipeline.py`(★`decision["ticker"]=cand.ticker` 명시노출 — W5 핵심수정).
- **데이터(US)**: study-research/eq_us/industries/{us_cyclical,us_defensive,us_mega_tech}/raw-v3/data/{prices,edgar_fundamentals,universe}.parquet. edgar=long format(concept 정규화: equity/net_income/op_income/dep_amort/cfo/capex/cash/lt_debt/st_debt/shares/revenues). prices 2015~2026(defensive 2010~).
- **데이터(KR, 다음)**: study-research/eq_kr/industries/{financial,battery,bio,auto,chemical,consumer,telecom,refining,semiconductor,shipbuilding,steel,aitech}/raw-v3/data/. prices.parquet(종목 2019~, code 기반), universe.parquet(★Marcap 컬럼 있음=시총직접, subcl), dart_financials.parquet(DART). KODEX ETF 가격=`FinanceDataReader.DataReader('091170',...)` 작동 확인.
- **결과 출력**: C:/msys64/tmp/claude/mab-{v2,v3,etf-full}.txt.

## §5 미해결·실패 (삽질 방지) + KR 연결 설계
- ★**KR 연결 설계** (kr_stock_holdings 신설):
  1. `core/portfolio_decompose.py` SUB_SLEEVES["kr_stock"] = etf-picks kr_picks 있는 7업종 우선(financial/battery/bio/shipbuilding/consumer/chemical/auto) → 확장 12.
  2. `kr_stock_holdings(as_of, kr_data, etf_picks_kr)` = us_stock_holdings 복제. 차이: (a) market_caps=universe.parquet Marcap(정적 caveat, 또는 prices기반 추정) (b) 펀더 불요(ETF/EW라 build_fundamentals skip, funds_by={}) (c) routing=_ETF_FALLBACK_ROUTING 한국(financial/battery/shipbuilding/auto→ETF, bio/consumer/chemical/telecom/refining→EW).
  3. KODEX ETF 가격: `FinanceDataReader.DataReader(ticker, start, end)` 7개(091170 등 etf-picks kr_picks). 드라이버 kr_data["_etf"]에 추가, _ticker_qret이 탐색.
  4. etf_picks_kr = {업종: {ticker: KODEX코드, aum:..., holdings_source:"FDR"}} (etf-picks-20260606.json kr_picks 변환, 또는 직접).
  5. KRX 종목 가격(EW basket용) = 업종 prices.parquet.
  6. kr_stock 시총분해: decompose_weight("kr_stock", kr_weight, 업종 Marcap 합).
  - ⚠️ KR은 US처럼 디버그 사이클 예상(US서 ticker/regime 등 4회). _ETF_FALLBACK_ROUTING 키 컨벤션(W3): 한국 업종은 prefix 無(financial 등)이라 매칭 OK(US defensive만 us_ prefix 불일치).
- ★**W3 ETF routing 컨벤션 불일치**: `_ETF_FALLBACK_ROUTING`/etf_pit.py/erb_snapshot.py = "us_defensive"(prefix), sleeve_signals = "defensive"(無). 통일=광범위 리팩토링→보류(사용자 결정). US 드라이버는 etf_fallback_routing override로 우회.
- ★**survivorship(US)**: universe 정적 2026 → 미래생존 누수. get_universe_at KRX전용. US 상폐데이터 부재 = caveat. us9 alpha +12.86%/yr 중 상당부분이 survivorship(상위종목 NVDA/AVGO/AMD/LRCX/ASML 죄다 생존 반도체).
- ★**coin 신호 미트랙**: 현 백테스트 coin=BTC-USD passive. coin_track.generate_candidate 미호출(us_stock과 비대칭). PortfolioState↔Orchestrator 동기화 난제(이전 세션)로 별도 과제.
- 거래비용(turnover) 미반영. sharpe 분기 ×√4 연율화(four_layer default 252는 과대).

## §6 결과 종합 (US 풀기간 2017~2026, 36 리밸런스)
- **ETF off(v3)**: 전체 CAGR +16.98% vs 60:40 +8.11% / us9 alpha +12.86%/yr(survivorship 잔존).
  - 산업: mega_tech +0.233(b&h+1523%), cyclical +0.172(+775%), defensive +0.058(+105%).
  - 종목: NVDA/AVGO/AMD/TSLA/LRCX/ASML/AAPL/GOOGL(반도체+테크 독식=survivorship).
  - regime: Stagflation us9-SPY +0.495(최강), Reflation +0.433, Recovery +0.138, Overheat +0.056(약). = value가 인플레/위기 강·과열장 약(정설 일치).
- **ETF on(brtyhrkgg, 도는 중)**: defensive→XLP. 2020~22 스모크 작동(us9 +18.9%/yr). 풀기간 결과 = mab-etf-full.txt.
- ★**버그 수정 이력**: ticker(selection_pipeline W5, alpha +25.6%→+12.86%), regime(W6 adapter주입), edgar/market_cap/staleness/engine(이전 세션 4버그).
- 이번 세션 외부 자문 없음(P3-G 게이트 자문은 이전: A기각/B측정/분리안 운용).
