---
next-action: "★잔여 6과제 전부 해소(2026-06-09, 사용자 '끝까지 자율로 다해' 승인): (1)refining 확정(517e11e) (2)W5 VIXCLS 검증(f2cf157) (3)P8-C eq_us rotation 종결(f2cf157) (4)P7 손실 attribution(6f6ffc9, NAV4.647 worst3분기 L1베타) (5)P8-B=게이트보류(f038c63, 신호 미채택 consult-adoption-gate) (6)★eq_intl/reit 분산 sleeve 신설(4047b80, v1.39.1): falsify=drop은 중복 아닌 구조적, 둘다 factor-distinct→7→9 diversification base(neutral 레짐·SEED β 없음·회귀 80 passed). ▸**다음 가능 작업**: eq_intl/reit 완전 factor통합(SEED β+regime weight_rules+15축 audit, 신호졸업 후) / P8-B collector 빌드(신호 채택 후) / 9-sleeve 백테스트(사용자가 이번 '분기별 돌려보기 빼고' 지시로 skip, 다음 실행 시 EFA/VNQ 자동편입). ⛔production core/stock(엔진·부품) 무단변경+push·go-live·실주문 미접촉(BASE_WEIGHTS/SLEEVES=정책 파라미터라 수정 허용)."
session: btn-Inv (opus, long-mode ON2 750k)
date: 2026-06-09
tags: [type/handoff, topic/eq-kr-residual, domain/multiasset]
related: WHY-ROTATION-SELECTION-NOT-APPLICABLE.md, progress-final-test-20260607.md P8, cross-regime-ledger.md
---

# handoff — eq_kr 완결 + 잔여 배선/데이터게이트 과제 (2026-06-09)

> ★eq_kr 트랙 완결(산업간 alpha 0·산업내 음수=ETF/EW+소액 정적 시클리컬). WHY 문서 박제. 이 핸드오프 = 사용자 "한국 10년 이후 잔여 과제 모두 진행" 지시의 잔여 목록 + 재개 레시피. ctx 89% compact로 인계.

## §1 현재 상태 · 첫 행동

**현재 상태**: eq_kr 완결(커밋 dfbb071·a168aa5·229ca20·528fccd). 잔여 = 미배선 연결 + 데이터게이트. ★WHY-ROTATION-SELECTION-NOT-APPLICABLE.md 가 eq_kr 재시도 함정 6건 박제(다음 세션 재탐구 금지).

**첫 행동(우선순위 순, 자율 진행)**:
1. **refining 부호충돌 확정**(가장 작음, eq_kr 마지막 매듭): study `_sleeve_rotation_kr_results.json` signal_ic refining +0.30(sign_stable) vs 내 `.p4-kr-rotation-deep` deep IC −0.249. 측정 방식 차이(panel OW 정렬 vs 내 EW수익) 대조. 확정 시 ledger §41 refining 확정.
2. **W5 VIXCLS vintage**(데이터, 작음): `core/data/factor_returns.py:38 "vol":"VIXCLS"` 이미 배선. ⑬축 결측=ALFRED vintage 3864>2000 한도. first_release fallback 확인(데이터 L2b 정밀도).
3. **P8-C eq_us _sleeve_rotation**: 예측층 STATIC 종결(OOS gate 탈락=정상, 자문 modal), W3 real_rate 동시 조절 배선됨(`decompose_weight` defensive 보간). base(cap vs inverse-vol)=W1 의존. → progress P8-C 마킹 종결.
4. **P7 17축 분기별 손실 attribution**: `run_multiasset.py --backtest` port_seq에서 손실 최대 분기 top-N → 18축 분해(어느 자산/국면이 끌어내렸나). plan-final-test P7-1~3.
5. **P8-B collector 데이터게이트**(외부 수집, 큼): crypto 3(stablecoin_total_supply=DefiLlama·etf_net_flow=Farside·halving_phase=결정론) / commodity 10(CME term structure·EIA·BIS 등) / bond 5(FRED DGS10/FEDFUNDS/JGB). progress P8-B.
6. **eq_intl/reit SLEEVE_AGG**(배분 차원 신설=★사용자 결정): `regime_to_weights.py:177 SLEEVE_AGG`에서 eq_intl/reit 의도적 drop(R10, 배분 sleeve 부재). 살리려면 SLEEVES 7→9 신설(us/kr/gold/coin/commodity/bond/cash → +eq_intl/reit) = portfolio 구성 결정. factor β는 완비.

## §2 진행 맵 (eq_kr 완결분)
- 산업간 rotation: 신호 실재(t2.04)나 OW 키워도 portfolio alpha 0 → 소액 정적(0.04). WHY §A.
- 산업내 selection: 어떤 틀이든 저PBR 음수 → ETF/EW. WHY §B.
- 6대 재시도 함정 박제(WHY §E): 시총비례≠중립·폐기조건44년·타이밍순진·PCA k*=1·valband 조선붕괴·momentum flow재포장.

## §3 사용자 박제
1. "한국 10년 이후 잔여 과제 모두 진행" — 본 핸드오프 §1 목록.
2. ⛔production core/stock 무단변경 / off=byte-identical opt-in / push·go-live·실주문 미접촉.
3. 자문 raw→산출 변환 시 방향성 보존(비관 왜곡 금지, consult-raw-output-mapping §방향보존, 본 세션 ERROR).

## §4 파일 inventory
- eq_kr 완결: `study-research/eq_kr/WHY-ROTATION-SELECTION-NOT-APPLICABLE.md`(재시도 함정 SSOT), cross-regime-ledger §41-42, sleeve_signals.SLEEVE_SIGNS_SKIPPED_KR, _kr_rotation_apply(정적틸트 deep IC), _bt_kr_picks(horizon hold·거래비용⑮), SUB_SLEEVES 12산업.
- 잔여 대상: `core/data/factor_returns.py`(W5), `core/brain/regime_to_weights.py:177`(eq_intl/reit SLEEVE_AGG), `study-research/eq_us/_sleeve_rotation.py`(P8-C), `run_multiasset.py` port_seq(P7), progress P8-B(collector 목록).

## §5 미해결·실패
- refining 부호충돌 미확정(측정 방식 차이 가능, 보수적 제외 상태).
- eq_intl/reit = SLEEVES 신설 사용자 결정 대기.
- P8-B collector = 외부 데이터 수집 필요(API).

## §6 자문 종합
- claude-web 3R(.claude-web-basic-last.md L37246-37430·L38387-38560): eq_kr 종목선택 폐기·rotation 정적틸트·시총비례≠중립·타이밍순진·폐기조건. WHY §E에 전수 매핑(독립검증 a0ce85ee 누락0 보강).
- gemini-web 인프라 2회 실패(selector timeout).
