---
next-action: 정식 멀티에셋 드라이버 작성 — orchestrator.allocate→업종 sleeve 시총비례 분해→construction.build_sleeve_decisions(ETF_FALLBACK=on, deterministic_no_llm=on)→A+B 종목선택/ETF fallback→회계 NAV. + orphan(multiple_band) value_stock 연결 + 업종분해 README/CODEMAP 박제.
session: btn-Inv (opus)
date: 2026-06-07
tags: [type/handoff, topic/final-test-pipeline, domain/multiasset]
---

# handoff — P3 최종테스트 파이프라인 wire 이음 (2026-06-07)

> plan=plan-final-test-20260607.md / progress=progress-final-test-20260607.md (상단 ckpt-202606072100)

## §1 현재 상태 · 첫 행동
- **완료**: P3-G(게이트 자문2R+검증) / P3-2a(횡단면 rank-IC 측정) / P3-2b(단일종목 배관 스모크) / P3-2c 단순화(거시배분 작동) / 배관4버그(commit c8d2b5b) / 9단계 결정론경로(commit f993915) / subagent 2회(설계출처·관계 + orphan 검토).
- **첫 행동(재개)**: 정식 멀티에셋 드라이버 작성(아래 §5 설계). 별도 .p3 측정스크립트(NAV 직접계산) 폐기 — **기존 모듈 호출만**(사용자 R5 정정). 단계: (1) study-research/eq_us sleeve별 종목 목록 확인 → (2) 드라이버: orchestrator.allocate→업종분해→construction→회계 → (3) ETF_FALLBACK=on·deterministic_no_llm=on.

## §2 진행맵 (progress P3 섹션)
- P3-G ✅ / P3-2a ✅ / P3-2b ✅ / P3-2c 단순화 ✅ / P3-구조검증 ✅ / **P3-2c-full 정식 드라이버 = 다음** / P3-3(OOS+dip overlay) / P3-4(3차 게이트).

## §3 사용자 박제 (대화 고유 결정)
- ★**프로덕션 라인으로 테스트, 별도 파이프라인 재구현 금지**(R5 2회 정정). NAV/배분/선택은 기존 모듈(orchestrator/construction/engine)이 수행, 드라이버는 시점루프+universe공급+회계만.
- ★**끊긴 wire 발견·연결이 테스트의 핵심 목적**(사용자 명시). 돌리면서 빠진 배선 잇기.
- 주식 노출 2층위: (a) 거시배분 sleeve(us_stock ETF 대표) (b) 개별종목 value selection(약변별→ETF fallback). 둘 다 백테스트.
- 게이트 설계=L1/ledger 무단변경 금지(자문+사용자 결정 거침). push·go-live·실주문 미접촉. DRY_RUN/KIS paper만.

## §4 파일 inventory (절대경로 D:/projects/Inv/)
- **수정·커밋됨**: `stock/value_trigger.py`(deterministic_no_llm param + L247 결정론 OPPORTUNITY 분기) / `core/stock_track.py`(_deterministic_no_llm_override) / `stock/selection_pipeline.py`·`stock/construction.py`(param 전달) / `stock/valuation.py`(market_cap fallback L262 + 최신순정렬 L259) / `stock/data/edgar_provider.py`(outstanding_shares/ebitda/book_value 매핑 L30·shares unit 허용) / `backtest/engine.py`(L461 dict action) / `core/brain/fred_adapter.py`(_GLOBAL_RAW_CACHE) / `core/data/sleeve_returns.py`(_YF_FULL_CACHE).
- **진단 스크립트(폐기예정·참고용)**: `.p3-gate-consult-verify.py`(게이트 검증) / `.p3-xsection-value.py`(횡단면 rank-IC) / `.p3-multiasset-backtest.py`(단순화 거시배분 — 우회 재구현, 폐기) / `.p3-construction-smoke.py`(9단계 호출 스모크).
- **핵심 모듈(읽음)**: `stock/construction.py`(build_sleeve_decisions:98, _ETF_FALLBACK_ROUTING:32) / `stock/selection_pipeline.py`(build_universe_candidates:39) / `stock/sleeve_signals.py`(SLEEVE_SIGNS: cyclical={pbr:-1,ev_ebitda:-1}/defensive={net_issuance:+1,ep_yield:-1}/mega_tech={}) / `core/portfolio_orchestrator.py`(allocate:114) / `core/coin_track_macro.py`(collect_market_state→allocate→macro_weights) / `stock/selector.py`(RepresentativeETFSelector:157/EwBasketSelector:125).

## §5 정식 드라이버 설계 (다음 세션 구현)
```
거시 orchestrator.allocate(as_of) → sleeve weights {us_stock:0.26, kr_stock, gold, bond, cash, commodity, coin}
  주식 sleeve(us_stock):
    → 업종 sleeve(cyclical/defensive/mega_tech) 시총비례 분해   ★끊긴 wire L0(문서·코드 미정의, grep 0)
    → 각 construction.build_sleeve_decisions(sleeve, metric_panel, ..., ETF_FALLBACK=on, deterministic_no_llm=on)
        → (A) cross_sectional cheapness rank (sleeve_signals 부호) = 상대선별 top-K
        → (B) value_trigger trap veto (heavy_agent 없으면 deterministic_no_llm→gate2 skip) = 절대검증
        → 종목 capped-EW  OR  변별력약(N<5/약변별 routing)→ETF fallback
  비주식 sleeve: gold=GLD, bond=BND, cash=BIL, commodity=DBC, coin=BTC (대표자산)
  → 선택종목/자산 다음기간 수익 × weight 합산 = 회계 NAV (이 회계만 드라이버, 의사결정은 기존모듈)
```
- metric_panel 산출: EDGAR fundamentals에서 pbr=시총/book_value, ev_ebitda=(시총+net_debt)/ebitda, ep_yield=net_income/시총, net_issuance=shares변화. (.p3-construction-smoke.py _metric_panel 참고)
- universe: study-research/eq_us/industries/{cyclical,defensive,mega_tech}/summary.yaml 또는 measure.py에 종목목록(확인필요).

## §6 미해결·실패 (삽질 방지)
- ★**업종분해 wire 부재**: orchestrator(sleeve)↔construction(업종) 단위 불일치. README/CODEMAP/코드 모두 미정의(grep 0)=진짜 L0. 시총비례 분해로 잇기 제안(사용자 답 미확정 — 직전 질문 "시총비례?" 보류).
- ★**ETF_FALLBACK=off 기본**: 스모크는 off라 ETF fallback 미적용. 전체백테스트엔 env on 필수. 약변별 sleeve만(financial/battery/bio/us_defensive).
- ★**orphan 핵심함수**(subagent): `value_stock`에 multiple_band(PER/PBR 밴드)·peg_ratio 정의됐으나 미호출(method_values=dcf/ev_ebitda/residual_income 3개만) → 연결가치 top. truflation_lead_signal=데이터 미연동.
- **풀기간 단순화 결론보류**: 주식=SPY(9단계 누락)+균등벤치 coin BTC 1/7 풀수혜(비현실). 적절벤치(60/40·coin제외)+정식selection 후 재판정.
- **sharpe 단위**: four_layer_metrics는 252(daily) 연율화 → 분기 NAV에 과대(7.x). 분기는 ×√4(.p3-multiasset _sharpe_q).
- **fhc 8 test fail**: baseline 동일(fhc yaml/네트워크), 내 변경 무관. test_so7/so8 golden = audit md 부재(기존 stale).

## §7 자문 종합 (gemini-web + claude-web 2R + 데이터검증)
- **A안(value+급락 -10% AND) 기각** / **측정=B 다종목 횡단면 rank-IC**(FWL 잔차화 size·sector·momentum, decile L/S) / **운용=분리안**(value 진입 + dip은 ceiling-bounded 사이징 변조 ×(1−trap_p), nested: dip-off=측정 베이스라인 B) / **단일종목=배관 스모크용**(alpha 측정 불가).
- 데이터검증(yfinance 10종목): C2 저평가 독립에피소드 중앙값 1.5개(16년)=단일종목 유효N 붕괴 결정적지지 / C1 21d수익 시장R² 0.21(idio 79%)=급락'전부시장' 과장→자문 magnitude 정정 / C3 -10%급락중 시장동반 0.544=idio trap위험.
- 횡단면 실측(P3-2a 24종목): 1Q rank-IC -0.005 비유의 / 1Y +0.016 비유의(CI 0포함, overlapping). value cheap 장기 약한 양(+) 경향이나 통계 비유의(검정력 부족). → 정식 selection(업종별·ETF fallback)으로 재측정 필요.
