# progress — 약변별 sleeve → 테마 ETF fallback (2026-06-06)

## §진입 스냅샷
- **plan**: `plan-etf-fallback-weak-sleeve-20260606.md`
- **guide/핸드오프**: `handoff-etf-fallback-impl-20260606.md` (최신, 재개 지점)
- **현재 단계**: Phase A/0/1 + 3-1/4-1 완료(파이프라인 dispatch wire). ★재개=Phase 2 ETF 가격 PIT → 4-2 risk_gate look-through(core)
- **모델**: opus (설계 판단 — ETF instrument 아키텍처)
- ⛔ production byte-identical / go-live 미접촉 / look-ahead PIT 엄수

## 단계 체크

### 자문 3R (구현 착수 전) ✅ 완료
- [x] R1: D1~D5 브리핑 → gemini-web + claude-web 병렬 (양쪽 응답)
- [x] R2: cross-feed (D2 모멘텀폐기/D3 selector-dispatch 합의)
- [x] R3: 통합안 9개 → 양쪽 "수렴 확정" (Gemini N=5+Max-Lag / Claude 5보강)
- [x] reflection-verify: 자문 17항목 전수 매핑 — 16 R / 1 P(tax/FX 압축, 보완 완료) / 누락·역방향 0

### Phase A — Selector 프로토콜 골격 ★load-bearing ✅ (17 test pass, 회귀0)
- [x] A-1 `Selector` ABC `(SleeveInput,asof)→List[SelectionCandidate]` (stock/selector.py 신규)
- [x] A-2 `SelectionCandidate` 스키마 확장 (instrument_type/holdings_source/holdings_asof/pre_resolved 4 default, :431 keyword 생성부 무변경=byte-identical)
- [x] A-3 `CheapnessSelector` 강등 래퍼 (select_cross_sectional 1:1 위임, 로직 무변경)

### Phase 0 — 변별력 약 sleeve 식별 ✅
- [x] 0-1 한국 低9곳 회수 (n0=13.63 ic0=0.141 / 中3: semi0.34/steel0.27/aitech0.26 / 低8: consumer·financial·battery·bio·auto·chemical·telecom·shipbuilding / 불가1: refining)
- [x] 0-2 미국 등급 산출 (within_industry_residual_us.py 신규, 한국 패턴 이식 / cyclical ρ0.33 中·작동 / defensive ρ0.16 低·fallback후보 / mega_tech ρ0 불가 N_eff6.6≪11 basket)
- [x] 0-3 D1 판정 = measured capsule IC SSOT + N_eff breadth + gate(verdict 직접) → ρ_i 등급. ★LS-spread/cost-aware는 capsule BY/OOS/long-only-net(cyclical +10%) 검증에 흡수, posterior=계층베이즈(KR)/raw|IC|(US 3 sleeve τ²부적합)

### Phase 1 — KR N분류 + ETF 매핑/선정
- [x] 1-1 9 sleeve N분류 (etf-fallback-routing-ledger-20260606.md) — ETF: KR financial/battery/bio/shipbuilding/consumer/chemical/auto + US defensive / EW: telecom·refining(과점·ETF부재) / 현행: cyclical·mega_tech · model: opus
- [x] 1-2 ETF 선정 (build_etf_picks.py, FDR 1136개→테마매칭, MarCap=AUM근사·Amount=거래대금, ★리턴 배제, 레버리지·인버스·factor틸트·해외 제외 → etf-picks-20260606.json). KR 5개(은행/2차전지/바이오/조선/자동차) + US XLP/XLU/XLV/XLC. consumer·chemical AUM<500억→EW
- [~] 1-3 look-through 1차(active/factor tilt 휴리스틱 제외=passive broad) ✅ / 운용사 PDF passive 확정 + holdings PIT max-lag = deferred · model: opus

### Phase 2 — ETF 데이터 (PIT) ✅
- [x] 2-1 FDR(KR)+yfinance(US) 일별 종가/NAV/거래대금 — `stock/data/etf_pit.py` 신규(EtfPitProvider). 실 fetch 검증(091170 close=15355/XLP=82.04) · model: opus(PIT 민감)
- [x] 2-2 AUM PIT(공시>NAV×좌수>스냅샷 우선순위) + trailing 1M ADV + **1일 lag**(cutoff=asof-1영업일, AUM에도 적용) + jsonl 스냅샷 PIT 재구성(krx_universe 패턴). seed_aum_from_picks + assemble_etf_picks(Phase 2↔4 wire). self-test 6 PASS · model: opus

### Phase 3 — Selector 구현 + shadow dispatch
- [x] 3-1 EwBasketSelector + RepresentativeETFSelector 구현 (selector.py, capped-EW 재사용 / ETF pre_resolved 메타) · model: opus
- [~] 3-2 shadow/dry-run dispatch 검증 + 회귀0 bit-equality (✅ env off 25 test 회귀0 / assemble holdings_asof+pit_cutoff 로깅 = shadow asof 부분 진전 / 별도 shadow-EW 디커플링 = Phase 4-4) · model: opus

### Phase 4 — 포트폴리오 편입
- [x] 4-1 construction층 dispatch table (_ETF_FALLBACK_ROUTING + _resolve_etf_routing + _fallback_decisions, env ETF_FALLBACK off=byte-identical, dispatch smoke 통과) · model: opus
- [x] 4-2 risk_gate look-through ✅ — `core/risk_gate.py` helper 2개 신규(`etf_lookthrough_exposures`=섹터분해+단일발행체 direct+via-ETF 합산+미커버 잔차 보수 / `holdings_pit_stale`=max-lag 검증). **check() 한 줄 무변경**(cross_sleeve helper 선례=미배선 무동작 byte-identical). `stock/order_assembly.py` env gated wire(ETF decision→look-through gate_kwargs override: 최대섹터→sector_weight, 단일발행체→current_weight, stale/holdings부재→wrapper 통째 보수, proposed_size=tw ETF만). 신규 `tests/test_etf_lookthrough.py` 9 PASS + 광역 125 PASS(env off byte-identical). 검증: 종목cap=ETF/섹터=underlying/단일발행체 direct9%+via1.76%→REJECTED · model: opus
- [x] 4-3 admission ETF allowlist + valuation 우회 ✅ — `stock/admission.py` `classify_etf_tier(name)` 신규(레버리지/인버스/ETN 키워드→TIER2_DEFAULT_OFF 거절 / passive→CORE_ALLOWED, build_etf_picks EXCLUDE 정합). 미배선 무동작(check_admission tier 인자 유지=byte-identical). valuation 우회 = Phase 4-1 dispatch가 build_universe_candidates(value 2단) 자체를 안 탐 + value_trigger_bypassed=True. test_etf_lookthrough 11 PASS(실 etf-picks 6종 CORE_ALLOWED 전수 + 레버리지 거절). test_so2_admission 31 passed 회귀0. ⚠️pre-existing 무관 실패 1: test_so7_p4_golden_rule(`.harness2/audit-goldenrule-p4.md` 부재=과거 wf 임시산출물, admission import 안 함=인과 없음) · model: opus
- [x] 4-4 alpha→beta 4중 잠금 ✅ — `core/assume/etf_beta_lock.py` 신규(`EtfBetaLock`). ① expected_alpha=0 선언+falsification_metric ② shadow-EW e-CUSUM(잔차 RMS표준화→`_DirectionalE` 양방향 betting: ETF>EW=alpha_emergence 선언위반 / ETF<EW=te_drag, 임계 e≥20=Ville α0.05) ③ 대칭 promote-demote gate(ic≥0.45 promote/≤0.25 demote/hold deadband hysteresis) ④ return-rank counterfactual 로깅(채택X, divergence rate). `_DirectionalE` 재사용, 기존 assume 무변경. test_etf_beta_lock 6 PASS. ⚠️pre-existing 무관 24 fail(BATTERY yaml fixture 손상, etf_beta_lock 미참조=인과없음) · model: opus
- [x] 4-5 통합 회귀0 ✅ — env off bit-equality 전체: ETF fallback 신규 17 PASS(test_etf_lookthrough 11 + test_etf_beta_lock 6) + production 핵심 139 PASS(risk_gate SO1~4/gated_router/admission/order_assembly/construction/stock 트랙, 회귀0) + 전 모듈 import 무결성(순환참조·레이어역전 없음: etf_pit→없음 / etf_beta_lock→fhc만 / order_assembly→risk_gate helper / admission→contracts). core/stock production byte-identical 보존(env ETF_FALLBACK off) · model: opus

### Phase 5 — 백테스트 ✅(1 sleeve 실측) / 다sleeve OOS deferred
- [x] 5-1 ETF 시세 PIT + 슬리피지 ✅ — `etf_fallback_backtest.py` 신규(실 PIT만: 구성종목 prices.parquet EW vs ETF FDR 실 일별, backtest.engine.calculate_slippage 재사용). financial 실행: 2019-2026 n=1816일/34종 · model: opus
- [x] 5-2 fallback on/off + shadow-EW 디커플링 ✅(1 sleeve) — financial 실측: EW누적+230.6%/ETF+174.9%, 연환산 EW+18.0%/ETF+15.1%, MDD ETF우위(-47.4% vs -52.2%), **TE annual 14.65%(높음=KODEX은행 ETF가 광의 financial 34종 부분커버)**, 디커플링 월별집계 비유의(e_under 0.8<20, 약 under prior). ★일별 betting=variance drag→월별21일 집계로 검출력 회복. **다sleeve OOS + 밴드 정밀 캘리브 = deferred(small-n hedge, 외부 데이터)** · model: opus

## Working Notes
> [ckpt-202606061710:btn-button] **S4 능동루프 진입점 정렬 회신** — (1)마지막 결정: btn-Inv S4 LLM 소환 shadow 루프(7-step) 정렬. button 접점=step7 write-back(카드→Σ_signal 원장, meta=button §6 Y). 현재 Σ_signal 원장 미구현(go-live 영역)→shadow dry-run sink로 충돌0. S4=카드발권 / ETF fallback=sleeve 비히클 직교. (2)다음 의도: ★compact 후 button측 Σ_signal 원장 write-back sink 배선(probationary mint 카드 + INV-12 firewall go-live시). S4 본체=btn-Inv 진행. (3)동기화: git HEAD=cd77af97(FHC 봉인) 내 64e8bc0 위 선형 충돌0. ctx 92% 강제 compact 임박.
> [ckpt-202606061700:btn-button] **FHC 계약 §6 회신 완료** — (1)마지막 결정: btn-Inv .coord-fhc-contract-20260603.md §6 3항목 회신 박제(§6' 추가): (b)Y core=bonus소유+button construction이 bonus API 소비배선, ETF fallback도 동일 seam (c)ETA=go-live arming(날짜미정, dormant) (Σ_signal/INV-12)Y meta=button/basket LORD++=button내부/core=firewall만. (2)다음 의도: go-live 시 bonus plug-in 소비. ETF fallback 정밀화(상폐PIT/세금/capacity) handoff §next-action. (3)동기화: contract §6' + git HEAD 536b1b4(FHC 4커밋이 내 64e8bc0 위 선형, 충돌0).
> [ckpt-202606061645:btn-button] **커밋 완료 64e8bc0** — feat(stock) 약변별 sleeve ETF/EW fallback. (1)마지막 결정: 24파일 staged(selector.py/etf_pit.py/risk_gate look-through/etf_beta_lock.py/admission classify/fair_cost_backtest + construction 라우팅 bio ETF→EW + ledger/plan/progress/handoff), 민감파일(.kis-token-cache.json/.env) gitignore 배제. env off byte-identical 회귀0(84 passed). (2)다음 의도: 상폐 PIT universe(survivorship 정밀)+KR/US 세금분리(국내 직접 양도세≈0)+capacity 곡선 = handoff §next-action deferred. (3)동기화: 커밋됨, push 미실행(사용자 지시 대기).
> [ckpt-202606061830:btn-button] **자문 R1 + 공정 맞대결 백테스트 → 라우팅 재확정(자율)**. (1)마지막 결정: gemini+claude 자문 강수렴="EW>ETF는 survivorship+소형주 비용 착시, 시총ETF≠중립(IC=0 진짜중립=EW), sleeve별 하이브리드, capacity 1순위". 공정 백테스트(√임팩트+ADV캡+STT+haircut4%, AUM1억) = 비용보정이 EW우위 다수 뒤집음(financial/consumer/auto/chemical→ETF 우위 역전). 예외 bio=KODEX바이오 ETF+2% 트래커실패작→EW(net t2.6). construction 라우팅 bio ETF→EW 변경(회귀0). (2)다음 의도: 상폐 PIT universe(survivorship 정밀제거)+KR/US 세금분리+battery/ship 추가분석. consumer/chemical=수익ETF우위지만 ETF AUM<500억 청산리스크 보수적 EW유지. (3)동기화: ledger/construction/progress 갱신. 신규=fair_cost_backtest.py+selection_vs_etf_backtest.py+kis_etf_holdings.py. KIS holdings=Open API 요약만(상세 미제공). 자문 reflection-verify 진행.
> [ckpt-202606061700:btn-button] **ETF fallback 전 구현 Phase 완주(자율주행 1세션)**. (1)마지막 결정: Phase 2(etf_pit.py PIT provider)+4-2(risk_gate look-through helper, check 무변경)+4-3(admission classify_etf_tier)+4-4(etf_beta_lock.py 4중잠금)+4-5(통합 회귀0)+Phase 5(etf_fallback_backtest.py 실 PIT, financial TE14.65%) 완료. env off byte-identical 전구간 보존(신규17+production139 회귀0). (2)다음 의도: financial 라우팅 재검토(TE14.65%→은행협의/멀티ETF/EW 사용자 결정) + 다sleeve OOS + KR 운용사 PDF holdings 연결. (3)동기화: progress/README/ledger/handoff 일관 갱신완료. autopilot flag 제거(progress 완료). 6 deferred=외부데이터/시간/사용자결정 의존(자율 불가).
- 2026-06-06: 핸드오프 회수 → plan/progress 작성 → 자문 3R 수렴 확정(양쪽). 근본 재구성=소N EW/대N ETF + 리턴선정 폐기→대표성 치환. plan에 안전장치(risk_gate look-through·단일발행체 합산·alpha→beta 4중잠금) 반영. R3 순서조정=Selector ABC 골격 맨 앞.
- 2026-06-06: reflection-verify PASS(16R/1P tax/FX 보완). **Phase A 완료** — stock/selector.py 신규(Selector ABC + SleeveInput + CheapnessSelector 강등 래퍼) + SelectionCandidate 4 default 필드 확장. 17 test pass 회귀0 byte-identical.
- 2026-06-06: **Phase 0 완료** — 미국 등급 산출(within_industry_residual_us.py, cyclical 中/defensive 低/mega 불가). 한국 低9 회수. ledger 작성.
- 2026-06-06: **파이프라인 미연결부 연결 완료**(사용자 지시) — selector.py에 EwBasketSelector(capped-EW 재사용)+RepresentativeETFSelector(ETF pre_resolved) 구현 + construction.build_sleeve_decisions dispatch wire(_ETF_FALLBACK_ROUTING + env ETF_FALLBACK default off). dispatch smoke 통과(telecom EW w_sum=1.0/financial ETF pick→instrument/cyclical 현행) + 기존 17 test 회귀0(env off byte-identity). README.md "약변별 sleeve→ETF fallback" 섹션 추가(사용자 지시2). Phase 1-1/3-1/4-1 완료.
- 2026-06-06: **Phase 2 완료**(자율주행) — `stock/data/etf_pit.py` 신규(EtfPitProvider + seed/assemble). FDR(KR)+yfinance(US) 일별 시세 PIT(역사 가용) + AUM 우선순위(공시>NAV×좌수>스냅샷, jsonl 일별 적재 PIT 재구성) + 1일 lag(가격·AUM 공통) + trailing 1M ADV. self-test 6 PASS + 실 fetch 검증(8 sleeve 적격) + end-to-end(seed→assemble→construction dispatch=ETF 1 decision). env off 25 test 회귀0(construction/selection/stock 트랙). production 미import(provider 레이어) = byte-identical.
- 2026-06-06: **Phase 4-2 완료**(자율주행) — risk_gate look-through. core/risk_gate.py helper 2개(check 무변경, byte-identical) + order_assembly.py env gated wire. ★버그 발견·정정: order_assembly `_flag`("true"만)와 construction `_resolve_etf_routing`(off=비활성) 규칙 불일치 → `_etf_fallback_on()` 헬퍼로 통일. holdings 데이터(KR 운용사 PDF=Phase 1-3 deferred / US=us_etf.py broad)는 호출자 주입 — 부재 시 wrapper 통째 보수 graceful. 125 test 회귀0.
- 2026-06-06: **Phase 4-3/4-4/4-5 + Phase 5 완료**(자율주행 1세션 완주). 4-3 admission classify_etf_tier(레버리지 거절 보존). 4-4 etf_beta_lock.py 4중잠금(_DirectionalE 재사용, RMS표준화 디커플링). 4-5 통합 회귀0(신규 17 + production 139). Phase 5 etf_fallback_backtest.py 실 PIT(financial EW+230%/ETF+175% TE14.65% 라우팅신호). **모든 구현가능 Phase 완주** — env off byte-identical 전구간 보존.
- **자율주행 종료**: 핵심 구현 Phase(A/0/1-1·1-2/2/3-1/4-1~4-5/5-1·5-2) 완주. **남은 = 외부 데이터/시간 의존 deferred**(자율 진행 불가): ①1-3 운용사 PDF look-through passive 확정 ②3-2 shadow dispatch 완전 asof 로깅 ③5-2 다sleeve OOS + 디커플링 밴드 정밀 캘리브(small-n) ④슬리피지 종목별 amount.parquet 정밀화 ⑤US defensive sleeve통째 vs sub-sector(XLP/XLU/XLV/XLC) 미결 ⑥financial 라우팅 재검토(은행협의 vs 멀티ETF vs EW, TE14.65% 근거).
- **동기화**: plan/progress/README/ledger 일관. selector.py·construction.py·cross_sectional_selection.py 수정(env off byte-identical). production core/stock 무접촉(env flag gated).
- 아키텍처 삽입지점: cross_sectional_selection.py(CheapnessSelector 강등) / admission.py(CORE_ALLOWED+allowlist) / valuation.py:244(value_stock None 자연우회, type==EQUITY 게이트)
