---
tags: [type/research-log, domain/equity, sector/battery]
date: 2026-06-05
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# battery(2차전지) 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격 momentum/rev/vol | pykrx OHLCV (prices.parquet 29종 1818일) | 정상 (2019-01~2026-05) | ✅ | cross-section 29종 = breadth 작음(반도체 85종 1/3). magnitude hedge 의무 |
| PBR/PER | DART fnlttSinglAcntAll (equity/net_income/assets) + 시총=Close×현재주식수 근사 | 정상 (698 rows) | ✅(약) | 시점주식수 PIT 미정밀(증자 잦은 종목). 성장주 적자 多 → PER 양수만(coverage 작음) |
| 재고/유형/무형자산 | DART fnlttSinglAcntAll BS (collect_dart_extended.py) | ★신규 fetch 정상 (747 rows, coverage inv 90%/ppe 100%/intangible 83%/cogs 19%) | inv_ratio✅ 나머지❌ | cogs(매출원가) coverage 19% 낮음 = 정규화 분모 회피(자산 기준 사용). PIT rcept_dt 적용 |
| regime (Macro/KRW/flow) | FRED KORLOLITOAASTSAM + DEXKOUS + ECOS 802Y001/0030000 | ★반도체 collect_regime.py 재사용(market-level=sector-independent) → parquet byte-identical 복사 | ✅ | regime = 시장공통 = 산업 무관. 재수집 불필요, 반도체 산출 직접 복사(traceability=collect_regime.py 병치) |
| 외국인 종목별 flow | KRX 종목별 순매수 | ★차단(인증) | ❌ data-gate | 시장레벨 flow regime(ECOS)은 측정완료. 종목 alpha 는 data-gate(deferral 아님) |
| 리튬 price | Trading Economics | 유료 + 산업 공통 시계열 | ❌ 이연 | cross-sectional 부적합 = regime 변수로만. FRED 리튬 PPI proxy 후속 |
| common factor β | yfinance + FRED (common_factors.parquet VIX/dollar/oil/rate/credit) | 기존 6/3 산출 재사용 | ✅(tentative) | credit=US HY OAS proxy(KR 부재, n=35 small). single-source hedge |

## 막힘·해결 로그 (시계열)

- [2026-06-05 08:24] 막힘: battery raw-v3 에 conditional IC 엔진(measure_conditional/fundamentals_cycle/merge_fdr)·regime 데이터·collect_dart_extended 부재. 6/3 옛 exposure-card batch(summary.yaml/measure_valuation/dart_financials)만 존재.
  → 진단: battery 산출이 conditional-IC pivot(2026-06-05) 이전 라운드. 반도체 파일럿이 신규 양식 SSOT.
  → 해결: 반도체 raw-v3 엔진 4종 + regime parquet + collect_dart_extended.py = battery 로 미러 복사. 엔진은 sector-agnostic(battery data/ 직접 read) = 코드 수정 0.
  → 교훈: regime 데이터는 market-level = 전 산업 byte-identical. 11산업 확장 시 collect_regime 재실행 불필요, 산출 복사로 충분(단 collect_regime.py 병치 = traceability).

- [2026-06-05 08:25] 막힘: measure_conditional.py 의 family_2 interaction 이 KRW_weak 하드코딩 = battery 에선 비유의(t<1).
  → 진단: 반도체 sign-flip 축 = KRW_weak. battery sign-flip 축 = flow_regime(momentum 양→음 flip, flow_strong_buy/flow_sell vs flow_neutral). 산업별 conditioning 축이 다름.
  → 해결: battery measure_conditional.py 에 flow_strong_buy interaction 을 primary 로 추가(measure_interaction_terms dummy_regime 인자 활용), KRW_weak 는 cross-sector 비교용 병행(family_2_interaction_krw).
  → 교훈: 엔진 미러 시 conditioning 축은 산업별 sign-flip 데이터로 재선택 의무(하드코딩 맹목 복사 금지). detect_signflip 출력으로 축 판정.

- [2026-06-05 08:27] 막힘: measure_walkforward.py 가 measure_conditional import 시 sys.stdout TextIOWrapper 이중 wrap → "I/O operation on closed file" (print 단계).
  → 진단: 두 .py 모두 `sys.stdout = io.TextIOWrapper(...)` 헤더 → import 시 첫 wrapper close.
  → 해결: JSON 은 정상 저장됨(에러는 print 단계만). 별도 python -c 로 JSON read 출력. 영향 없음(산출물 무결).
  → 교훈: import 하는 측은 stdout re-wrap 회피하거나, 산출물(JSON)이 print 전에 저장되게 설계. 본 케이스는 저장 후 print 라 무해.

- [2026-06-05 08:29] DART extended fetch = background incremental(resume 내장, dart_ext_done.json). 29종 × 7년 × 4분기 ≈ 수분, exit 0 완주. 747 rows.
  → 교훈: collect_dart_extended 는 done.json+parquet 증분 저장 → 중단/재개 안전(반도체서 죽음 2회 겪은 패턴 회피).

## 측정 방법 결정 로그

- **momentum 부호 = 양(continuation) 사전확약**: 반도체(음=reversal)와 반대. 이론(Jegadeesh-Titman + EV S-curve 성장 + 종목 차별화) 근거. 측정 정합(+0.075) = HARKing 아님(이론 독립 수립 후 대조). 단 OOS 로 확증.
- **conditioning 축 = flow_regime primary**: detect_signflip 41건 중 momentum×flow 가 가장 일관(flow_neutral 양 / flow_strong_buy 음). KRW_weak(반도체 축)은 battery momentum 에서 약. = 산업별 driver 다름(반도체=수출환율, 2차전지=외국인 passive flow).
- **walk-forward OOS = team-lead 지시**: IS(2019-22, 리튬붕괴 포함)/OOS(2023-26). momentum 양 + flow_neutral cell 모두 OOS 부호유지 = 2022 단일 episode 종속 아님. inv_ratio 도 OOS 부호유지(약화).
- **단일 FDR family m=177**: 가격/valuation conditional 99 + 신규 펀더멘털 78 합산(garden-of-forking-paths 차단). BY 생존 0 = 다중검정 후 비유의. 정직 박제 — 방향·conditional 은 살아있으나 BY-robust 아님. M_eff 통합보정 = supervisor.
- **inv_ratio prior 반증 박제(이연 금지)**: 측정 양(+0.112, family 최강) ≠ prior 음. "나중에 보자" 금지 = 지금 verdict 박제(메커니즘 재해석: 성장 proxy). 반도체와 동일 반증 = memory enum(공통 패턴).

## 막힘·해결 로그 — ROTATION 신호 추가 (2026-06-06)

- [2026-06-06] ★rotation 신호 추가 (종목selection capsule 위 차원 = 업종 OW/UW timing). team-lead 지시 = v2 lithium_yoy +0.274 검증·심화.
  → 진단: rotation-analyst v2(`_rotation/measure_rotation_v2.py`)가 LIT(Global X Lithium ETF) yoy → 업종 eq-weight forward 측정. battery lithium_yoy y_60d rho +0.274 OOS+0.46 STRONG.
  → 해결: 독립 재현 PASS(rho/OOS 일치). 엔진 sector-agnostic = cycle_battery.parquet(LIT 1컬럼, source 사전검증 ticker=LIT) read.
  → 교훈: rotation = 업종 시계열 forward(종목 cross-section 아님). 종목selection(flow×momentum)과 다른 차원.

- [2026-06-06] ★CRITICAL universe 오염 체크 (refine-analyst 적발 = v2 디렉토리전체 패널 부수종목 오염).
  → 진단: battery 패널 29종에 비-2차전지 10종(포스코인터=가스 / 두산=전자IT / 두산퓨얼셀=연료전지 / 비츠로셀=1차전지 / 세방전지=연축 / 신성이엔지=태양 / 인텍플러스=반도체검사 / 솔브레인홀딩스=지주 / 비나텍=슈퍼캡 / DN오토모티브=차배터리) 혼입.
  → 해결: STRICT 19종(진짜 셀/양극/음극/분리막/전해질/동박/장비) 화이트리스트 재현. ★결과 = 오염 없음 — STRICT +0.285(v2 +0.274 동등) / CORE 셀+양극 8종 +0.338(강화) / 제외10종만 +0.141(약화). 부수종목이 신호 희석(생성 X).
  → 교훈: ★refining(부수종목이 신호 생성)과 반대 = battery 는 양극재 makers(리튬원가 60-70%) 민감도 최고 → strict일수록 강화. steel 동형(오염無). ★채택 패널 = STRICT 19종.

- [2026-06-06] ★이론 검증(증권사) = data mining 차단. Gemini 리서치(WebSearch 차단 → gemini-search.js helper).
  → 결과: KB증권/신한투자/삼성증권/하나증권/키움증권 리포트 = 리튬→양극재/셀 cost pass-through(판가연동 3-6M lag) + 재고평가손익(래깅/역래깅) + 선행지표(변곡점→주가 6M 선반영). 삼성증권 "리튬 반등=주가 반등 트리거" 직접 업종 타이밍 지표 사용.
  → 교훈: 이론+통계 둘 다 채택 = data mining 아님. OOS 2023-26 = 리튬 바닥→반등 = 증권사 "최강 신호" 국면 정합 → OOS+0.46 강화 설명.

- [2026-06-06] ★driver ≥8 전수(STRICT 패널) + multi-source. 후보 10개 / tradeable 6.
  → eligible: LIT +0.285 / ALB +0.281(★순수 리튬광산) / REMX +0.220(니켈코발트) / NIO +0.250(중국EV) / BATT +0.122 / self_mom_3 +0.198(★공통인자 재포장 의심=강등).
  → rejected: TSLA(OOS flip) / DRIV(EV광의 약화) / usdkrw(★macro 공통=시장timing) / XLB(★control 실패 = specificity 입증).
  → 교훈: 리튬/cathode-metal 3종(LIT/ALB/REMX) 수렴 + XLB control 실패 = 리튬 cycle = 진짜 driver. momentum=residualize 소멸(자문 A 정합) → 강등.

## 미해결 / 다음 세션 우선 작업

1. **EV-EBITDA 산출** (cyclical primary_metric, DART 부채/현금 + 시점주식수 PIT) — collector_plan high.
2. **종목레벨 외국인 flow** (KRX 인증 또는 ETF flow proxy) — 시장 regime 과 다른 종목 alpha.
3. **리튬 price regime 변수** (FRED 리튬 PPI proxy) — Macro 축 보강.
4. **대형2사 LOO** (LG엔솔/삼성SDI 각각 제외 momentum IC) — 대형주 의존 falsifier.
5. **inv_ratio size/growth 통제** (Fama-MacBeth) — 성장 confound 분리.
6. **KR HY credit spread** (credit β US proxy 대체).
7. **rotation: 실 리튬 carbonate spot** (LIT ETF proxy 대체, Trading Economics 유료) + 급등/급락 비대칭 분리.
