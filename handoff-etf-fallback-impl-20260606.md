---
name: handoff-etf-fallback-impl-20260606
description: 약변별 sleeve→테마 ETF fallback 구현. 자문 3R 수렴 + 파이프라인 dispatch wire 완료(env off byte-identical). 남은=ETF 데이터 PIT + risk_gate look-through(core) + alpha→beta 잠금 + 백테스트.
next-action: "★자문 R1(gemini+claude 강수렴)+공정 비용백테스트+attribution 완료(9/9 반영). 결론: EW>ETF는 비용 착시(financial/consumer/auto/chemical ETF우위 역전), 예외 bio=ETF트래커 부실(size_β≈0 구조적)→EW 전환(라우팅 반영,회귀0). 남은 정밀화(가정 넘어): (a)상폐 PIT universe(survivorship 차선 haircut4% 대체중, 자문C2a 우선책=상폐종목 FDR fetch) (b)KR/US 세금분리(국내 직접 양도세≈0 vs ETF 배당15.4%,자문C6) (c)capacity 곡선(현 AUM1억 단일점) (d)battery/ship 추가. ⛔ production byte-identical(env off) 회귀0 검증완료."
type: project
tags: [domain/eq-kr, domain/eq-us, type/handoff, topic/etf-fallback-impl]
date: 2026-06-06
---

# 약변별 sleeve → 테마 ETF fallback 구현 핸드오프 (2026-06-06)

> 인계: 직전 = `handoff-etf-fallback-weak-sleeve-20260606.md`(작업량 검토). 본 핸드오프 = 자문 3R + 파이프라인 연결 후.
> plan=`plan-etf-fallback-weak-sleeve-20260606.md` / progress=`progress-etf-fallback-weak-sleeve-20260606.md` / ledger=`etf-fallback-routing-ledger-20260606.md`

## §1. 현재 상태 + 첫 행동
- **상태**: 자문 3R 수렴 확정 + plan/progress 반영 + **파이프라인 dispatch wire 완료**(selector.py→construction). env `ETF_FALLBACK` off=기존 17 test 회귀0 byte-identical. EW 경로 end-to-end 동작, ETF 경로는 etf_picks 주입 시 instrument 1개.
- **★첫 행동(재개)**: Phase 2 ETF 가격 PIT fetch(yfinance ETF 일별 + FDR NAV, etf-picks-20260606.json ticker). 그 후 Phase 4-2 risk_gate look-through.
- ⛔ production `core/`·`stock/` byte-identical(env off). risk_gate/assume 수정은 env gated. go-live·실주문 미접촉. look-ahead PIT 엄수.
- **자율주행 flag ON**: `D:/projects/button/agent/.secretary/.autopilot-btn-button.flag` (progress 끝까지 자율, 완료 시 rm).

## §2. 진행 맵
| Phase | 작업 | 상태 |
|---|---|---|
| A Selector 골격 | Selector ABC/SleeveInput/CheapnessSelector 강등 + SelectionCandidate 4필드 | ✅ 17 test 회귀0 |
| 0 변별력 식별 | KR 低9 회수 + US 등급 산출(within_residual_us.py) | ✅ cyclical中/defensive低/mega불가 |
| 1-1 N분류 | ledger 라우팅 | ✅ |
| 1-2 ETF 선정 | build_etf_picks.py (FDR, 리턴배제, AUM/유동성) | ✅ KR5+US defensive |
| 1-3 look-through | 1차 휴리스틱(factor tilt 제외) ✅ / PDF passive 확정 | ~ deferred |
| 3-1 selector 구현 | EwBasket/RepresentativeETF | ✅ |
| 4-1 dispatch wire | construction _ETF_FALLBACK_ROUTING + env flag | ✅ smoke 통과 |
| **2 ETF 데이터 PIT** | etf_pit.py(FDR/yfinance 시세 + AUM 우선순위 공시>NAV×좌수>스냅샷 + 1일lag + ADV + seed/assemble wire) | ✅ self-test 6 + 실fetch 8 sleeve |
| **4-2 risk_gate look-through** | risk_gate.py helper 2개(check 무변경) + order_assembly env gated wire | ✅ 단일발행체 direct+via 합산 REJECTED 실증, 125 회귀0 |
| **4-3 admission allowlist** | admission.py classify_etf_tier(레버리지 거절 보존) | ✅ 미배선 무동작 |
| **4-4 alpha→beta 4중잠금** | etf_beta_lock.py(_DirectionalE 재사용, RMS표준화 디커플링 + 대칭 gate + counterfactual) | ✅ self-test + 6 test |
| **4-5 통합 회귀** | env off bit-equality | ✅ 신규17 + production139 회귀0 |
| **5 백테스트** | etf_fallback_backtest.py 실 PIT(financial EW+230%/ETF+175% TE14.65%) | ✅ 1 sleeve / 다sleeve OOS deferred |

## §3. 사용자 박제
- "골고루 담는 수준 변별력 없으면 = 종목 selection 포기, 수익률 높고 AUM 큰 테마 ETF 매수." 한국+미국.
- 추가 지시(2026-06-06): (1) "파이프라인 따라가보며 미연결부위 연결" = selector.py dispatch wire ✅ (2) "README 업데이트 페이스 끝에 추가" = 단계 끝마다 README 갱신 ✅(주식트랙 섹션) (3) "progress 끝낼때까지 자율주행 flag on".
- ★자문 핵심 통찰(사용자 질문 "레버리지 빼고 수익률 높은거=운영 잘한거 아냐?"에 답): 동테마 ETF 수익률차=숨은 베팅/운빨, 운영실력은 TE·TER에 박혀있음 → 리턴 배제하고 대표성/유동성/저비용 선정.

## §4. 파일 inventory (절대경로 = D:/projects/Inv/)
**수정(env off byte-identical)**:
- `stock/cross_sectional_selection.py` — SelectionCandidate 4 default 필드(instrument_type/holdings_source/holdings_asof/pre_resolved) + datetime import. :431 keyword 생성부 무변경.
- `stock/selector.py` (신규) — Selector ABC + SleeveInput + CheapnessSelector(강등 래퍼) + EwBasketSelector(capped-EW) + RepresentativeETFSelector(ETF pre_resolved).
- `stock/construction.py` — build_sleeve_decisions dispatch(_ETF_FALLBACK_ROUTING + _resolve_etf_routing + _fallback_decisions + _candidate_to_decision). env ETF_FALLBACK off=기존 경로.
**신규 산출**:
- `study-research/eq_us/industries/_rotation/within_industry_residual_us.py` + `validation-within-residual-us-v1.json` (미국 등급)
- `study-research/eq_us/industries/_rotation/build_etf_picks.py` + `etf-picks-20260606.json` (ETF 선정)
- `etf-fallback-routing-ledger-20260606.md` (라우팅) / `plan-*` / `progress-*`
- `README.md` "약변별 sleeve→ETF fallback" 섹션 추가(주식 트랙)
**입력**: KR `study-research/eq_kr/industries/_rotation/validation-within-residual-v2.json` / US 각 sleeve `summary.yaml`(measured IC SSOT)
**python**: `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (PATH 부재, 풀패스. PYTHONPATH=.). FDR 0.9.202 + yfinance 가용.

## §5'. 완료 요약 (2026-06-06 자율주행 1세션)
- **신규 파일**: `stock/data/etf_pit.py`(EtfPitProvider + seed/assemble) · `core/assume/etf_beta_lock.py`(4중잠금) · `study-research/eq_kr/industries/_rotation/etf_fallback_backtest.py` · `tests/test_etf_lookthrough.py`(11) · `tests/test_etf_beta_lock.py`(6)
- **수정 파일(env off byte-identical 회귀0 검증)**: `core/risk_gate.py`(helper 2개, check 무변경) · `stock/order_assembly.py`(env gated look-through wire + `_etf_fallback_on()`) · `stock/admission.py`(classify_etf_tier) · `stock/construction.py`·`stock/cross_sectional_selection.py`·`stock/selector.py`(Phase A/3/4-1, 직전 세션) · README
- **핵심 실측**: financial KODEX은행 ETF TE annual **14.65%** = 광의 sleeve(34종) 부분커버 → 라우팅 재검토 필요(ledger 박제)
- **버그 정정 3**: (1) etf_pit AUM 1일 lag(seed는 cutoff 이전 날짜) (2) order_assembly `_flag`("true"만) vs construction(off≠) 규칙 불일치→`_etf_fallback_on()` 통일 (3) 디커플링 일별 variance drag→월별 집계
- **남은 deferred(외부데이터/시간/사용자결정)**: ↓ §5

## §5. 미해결·실패 (삽질 위험)
1. **risk_gate look-through = production core 접촉** (core/risk_gate.py). ETF 1포지션의 섹터 cap을 underlying으로 + 단일발행체 direct+via-ETF 합산. ★env gated 필수, byte-identical 회귀(test_so1_risk_gate.py). 자문 "최대 작업량".
2. **alpha→beta 4중잠금 = core/assume 접촉** (WeightAssumptionCard). shadow-EW basket 수익 계산 + e-CUSUM 디커플링. core 수정 신중.
3. **AUM floor 임계 500억 = 잠정**. consumer(160)/chemical(360) EW 재분류 근거. 자문은 "floor=청산리스크 필터"만, 정확 임계 미정. 운용사 공시 순자산으로 정밀화.
4. **look-through PDF 미확정**: 1차는 이름 휴리스틱(factor tilt 제외). KODEX 바이오 등 실제 passive 여부 = 운용사 PDF holdings 확인 필요(자문: 2차전지/바이오 active 내장 주의).
5. **US defensive = sleeve 통째 1 ETF vs sub-sector(XLP/XLU/XLV/XLC)**: defensive 등급은 pooled(48종), sub-sector별 변별력 미산출. 현 ledger=sub-sector 4 ETF 나열. sleeve 통째냐 sub-sector별이냐 미결정.
6. **shadow dispatch 로깅(3-2) 미완**: asof별 어느 selector fire 로깅 → live cutover 전 검증.
7. **ETF candidate→decision dict 키 호환**: _candidate_to_decision이 최소 키(verdict=opportunity/value_trigger_bypassed). risk_gate 실제 소비 키 호환은 4-2에서 확인 필요.

## §6. 자문 종합 (gemini-web + claude-web 3R, 양쪽 "수렴 확정")
- **D1 판정**: raw ρ 폐기 → posterior LS-spread cost-aware + breadth(Grinold) + PIT expanding-window 라벨 + dwell-debounce. (구현=measured capsule IC SSOT + N_eff + gate, LS-spread는 capsule BY/OOS/long-only-net 흡수)
- **D2 선정**: ★과거 리턴(모멘텀) 배제(레버리지 ETF 선택→거절정책 모순 + value 헤지) → 대표성+유동성(거래대금/AUM)+저비용(TER/realized-TE)+tax/FX(원천징수·양도세·FX드래그), 레버리지/인버스 제외.
- **D3 아키텍처**: z=+99.9 mock 기각(poison) → construction층 selector-dispatch, ETF score=None(pre_resolved) ranker bypass. value '우회' 아니라 '안 부름'.
- **D4 부재산업**: 정유/통신 EW 직접(소N·과점 EW dominant). 인접테마/시장ETF 거부.
- **D5 AUM**: 공시 절대값 PIT 우선 > NAV×과거좌수 > 현재스냅샷(look-ahead). trailing 1M+1일 lag. ADV 병행.
- **라우팅**: N≥5(비용proxy) ∧ 적격passive-ETF ∧ look-through(hard) ∧ holdings PIT max-lag → RepresentativeETF / 그 외 EW.
- **안전장치**: risk_gate look-through(섹터cap=underlying / 단일발행체 합산) + ETF look-through(active tilt 검사) + alpha→beta 4중잠금(선언/shadow-EW e-CUSUM/대칭 gate/counterfactual) + down-only 비용허들.
- **순서**: Selector 골격→US IC등급→KR N분류→shadow dispatch→live. (A~1 완료, 2~5 남음)
