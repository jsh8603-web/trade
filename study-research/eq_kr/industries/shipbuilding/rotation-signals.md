---
tags: [type/rotation-signals, domain/inv, scope/equity-kr, sector/shipbuilding]
date: 2026-06-05
owner: shipbuilding teammate (kr-equity, opus 1m)
purpose: 조선 업종 rotation 신호 측정 (team-lead 지시 = 신조선가 무료 proxy 재탐색 + BDI 부적합 이론). cross-sectional 종목선택 아닌 "어느 국면→조선 업종 OW/UW".
---

# 조선(shipbuilding) 업종 rotation 신호

> raw 재현: `raw-v3/measure_rotation_ship.py` → `validation-rotation-ship-v2.json` (cycle_shipbuilding_v2.parquet)
> 배경: rotation-analyst v2 = 조선 ★REJECTED (baltic_dry_yoy IC -0.091, 사전확약 양인데 실측 음).

## 결론 한 줄
★조선 rotation = 신조선가 proxy 재탐색했으나 ★여전히 약/반증 (v2 REJECTED 유지). 운임·해운 신호가 조선 forward 와 ★음 (주가가 운임/신조선가 6-12M 선행 = Gemini 입증). 신조선가 직접 = 무료 부재(Clarksons 유료) + 후행이라 부적합.

## 1. ★BDI(baltic_dry)가 조선 rotation에 안 맞는 이유 (이론 정리, team-lead 지시)

v2 baltic_dry_yoy IC -0.091 (사전확약 양인데 실측 음). ★Gemini 리서치(하나증권 최광식/메리츠 배기종/NH 2023) 정리:

1. **★선종 불일치 (결정적)**: BDI = ★벌크선 운임(철광석/석탄/곡물). 한국 조선 3사(HD현대중공업/삼성중공업/한화오션) 주력 = ★LNG선/초대형 컨테이너선(ULCS)/VLCC/친환경선. BDI 폭등 = 중국 철강수요(벌크) 반영이지 한국 LNG/컨테이너 발주와 무관. (오히려 BDI는 벌크 주력 중국 조선에 상관 높음.)
2. **운임 = 해운사 수익, 조선 수주 신호 아님**: 운임↑ → 해운사 매출↑이나 즉시 발주 X (부채상환/주주환원 선택지). 발주 = 별개 CAPEX 의사결정.
3. **18개월+ lag**: 운임급등 → 해운사 펀더 개선(1-2분기) → 발주결정 → 수주인식 → 건조(2-3년) → 매출인식. 단기 주가 예측 실패.
4. **주가 선행**: 주식시장이 BDI 상승 → 미래 발주 기대 선반영하나, 선종 불일치로 기대 강도 약 + 악재(원가/금리)에 무시.

→ ★BDI 대신 한국 조선 맞는 운임 = SCFI(컨테이너)/탱커(Worldscale)/LNG 스팟. 단 SCFI/Clarksons = 유료.

## 2. ★신조선가 무료 proxy 재탐색 (team-lead 지시)

신조선가(Clarksons Newbuilding Price Index) = ★유료 + ★주가가 6-12M 선행(후행지표) = rotation 선행신호 부적합(하나증권 최광식). → ★11 후보 대리 proxy (team-lead ≥8):

| # | proxy | 정의 | 부호확약 | 측정 IC(최강) | 판정 |
|---|---|---|---|---|---|
| 1 | **tanker_basket** (TNK/STNG/FRO) | 탱커 운영사(VLCC 발주 선행) | 양 | -0.328(d3→60d) | ★반증(음)+underpowered |
| 2 | container_basket (GSL/DAC/ZIM) | 컨테이너선(ULCS 발주) | 양 | +0.087(match) | 약(t_mde 0.34) |
| 3 | boat_etf (BOAT) | 글로벌 조선해운 ETF | 양 | -0.235(반증) | 약, 2021~ 짧음 |
| 4 | steel_plate (HRC 열연강판) | 후판 원가 | two-sided | +0.18(d3) | 약, 이중성 |
| 5 | lng_demand (LNG Cheniere) | LNG선 수요 | 양 | -0.12(반증) | 약 |
| 6 | **oil_wti** (CL=F 유가) | 해양플랜트/LNG선 수요 | 양 | ★-0.442(yoy→60d, wc_p 0.0025) | ★반증(음)+underpowered |
| 7 | usdkrw (환율) | 원화약세→수출 수익성(H1) | 양 | +0.095(match) | 약(OAS flip) |
| 8 | steel_etf (SLX 철강) | 후판 원가 cycle | two-sided | -0.271(yoy→60d) | 약 |
| 9 | iron_ore (TIO=F 철광석) | 후판 원료 | two-sided | -0.262(yoy→60d) | 약 |
| 10 | baltic_bdry (BDI 운임) | v2 REJECTED 재현 | 양 | -0.111(반증) | ★반증(선종불일치) |
| 11 | china_proxy (FXI 중국) | 중국조선 수주점유(경쟁) | 음 | +0.390(반증, wc_p 0.003) | ★반증(양)+INSUFFICIENT(n_eff 5.6) |

★신조선가 직접 무료 proxy = ★진짜 없음 (Clarksons/SCFI 유료, 수주잔고 공시 = 정형 시계열 부재 + 동행/후행). 후판가(HRC/SLX/TIO) = 이중성 약. ★고객 해운사 주가(tanker/container)·유가가 이론상 최선이나 실측 반증(주가 선행).

## 3. 측정 결과 (44 신호 = 11 proxy × 2변환 × 2horizon, 전 신호 약/반증)

- **★전 신호 underpowered** (t_mde < 2.802 breakeven). FDR powered cell 0, BY survivors 0.
- **강신호(|IC|>0.25)는 전부 ★부호확약 반증** (사후 부호전환 = garden-of-forking-paths 위험):
  - oil_wti yoy→60d IC -0.442(확약 양, 반증) / china yoy→60d +0.390(확약 음, 반증) / tanker d3→60d -0.328(확약 양, 반증).
  - = "유가/해운/탱커 momentum 高 → 조선 forward 하락" = 주가 선행(H8/H10).
- **부호확약 일치(match)+OOS 유지 = container_basket(+0.087)** 뿐인데 ★t_mde 0.34 (극도로 약, wc_p 0.31) = tradeable 부적격.
- **메커니즘 진단** (tanker contemporaneous vs forward):
  - 동시(t) rho +0.014(무관) / forward 3M rho -0.328(p=0.002) = ★해운사·유가 momentum 高 → 조선 forward 하락.
  - = ★운임/해운/유가 고점 = 발주 사이클 정점 신호 → 조선 주가 이미 선반영 후 되돌림(주가 6-12M 선행, Gemini 입증).
  - 조선↔탱커 동시상관 +0.145(약, p=0.18) = risk-on 동조 가설 약.

## 4. ★verdict = v2 REJECTED 유지 (이론+통계 정합, tradeable 0)

★조선 rotation = ★약/반증 (11 후보 전수 측정, tradeable 0). (1) 신조선가 직접 = 무료 부재 + 후행 부적합 (2) 해운사 주가/유가 proxy = BDI 처럼 조선 forward 와 음(주가 선행) = 사전확약 반증 (3) 전 신호 underpowered + FDR powered 0.
- ★이론 근거 = 명확 (주가가 운임/신조선가 6-12M 선행 = 후행지표 rotation 부적합 + BDI 선종불일치). ★data mining 아닌 이론 정합 REJECTED.
- ★부수 발견 (observe-only): tanker/oil momentum ★역방향(contrarian: 운임·유가 高→조선 UW)이 OOS 안정적 음(tanker IS -0.28→OOS -0.40). 단 ★사후 부호전환(one-sided 확약 위반) + underpowered = forking-path 위험 = candidate-ledger observe-only(N 누적+신조선가 직접지표 확보 후 재평가). ⛔ 지금 tradeable 화 금지(무리한 발굴=data mining 회피).

## 5. ★G-G v2 tradeable = 0 + monitor-only (사유 박제)

★조선 rotation tradeable = ★0 (사용자 "최소 2개" 규칙 미달 = ★구조적 빈약 사유 박제, team-lead 허용). 
- ★사유 = ★"주가 선행성" — 조선 주가가 운임·신조선가를 6-12M 선행 → 후행 fundamental cycle 신호(운임/유가/신조선가)는 rotation 예측력 ★무효 (Gemini = 하나증권 최광식/메리츠 배기종/NH 2023 정합). + BDI 선종불일치. + 신조선가 직접지표 무료 부재.
- ★조선 종합 = 종목선택 0 + 섹터 PBR timing 약 + ★rotation 0 = ★구조적 약 확정 (산업 베타 슈퍼사이클 timing 지배 H9 + 주가 선행 H10).
- **monitor-only**: 슈퍼사이클 정점 de-risk 참고(tanker/유가 momentum 高 = 조선 고평가 경계 contrarian, 단 tradeable 아님). ★신조선가/SCFI 직접지표(유료) = collector_plan high — 확보해도 주가 선행이라 timing 보단 "확인용".
