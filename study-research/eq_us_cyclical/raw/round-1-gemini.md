---
tags: [type/consult-response, study/eq_us_cyclical, round/1, source/gemini-pro-web]
date: 2026-05-30
model: GeminiPro
response_len: 5833
---
# Round 1 — Gemini Pro 응답

## v1 비판 (핵심)
2014-2023 반도체(SOX) 패널의 Rank-IC +0.658은 전통적 경기민감주 특성이라기보다 **제로금리 + Cloud/AI 구조적 성장(Secular Growth) multiple expansion 과대적합** 가능성. 일반 경기민감주(Materials/Energy/Industrials) 확장 시 맹점 보완 필요.

## ① 이론 수집 — 재구성 (필수 6)
1. **Capital Cycle Theory** (Edward Chancellor "Capital Returns") — ★최우선 추가. "수익성→자본 유입(Capex)→공급 과잉→수익성 파괴" 명제. v1 inventory/capex 역신호 IC=-0.31 완벽히 설명. peak_trap 감지 핵심 프레임워크.
2. **Merrill Lynch Investment Clock & Sector Rotation** — 성장(PMI)×인플레(CPI) 2x2. 방어주 대비 민감주 비중 조절 베이스라인.
3. **Damodaran on Valuation** (Cyclical Company Valuation 챕터) — **Normalized Earnings** 개념을 val_gap 산출에 이식 필수. peak에서 PER 낮고 trough에서 PER 높은(이익 붕괴) 반직관 처리.
4. **ISM PMI 세부 + NBER + Yield Curve** — 특히 **ISM 제조업 New Orders minus Inventories** 가 EPS revision에 3-6M 선행하는 가장 강력한 데이터.
5. **Operating/Financial Leverage** (Brealey-Myers) — 고정비(DOL proxy) → trough→recovery EPS 폭증, 부채(DFL proxy) → HY OAS 확대 국면 파산 위험.
6. **Credit Cycle Framework** (Howard Marks "The Most Important Thing", Ray Dalio Economic Principles) — XLY/XLI 신용 스프레드 극도 취약. 금리 인상 후반 차환 비용이 마진 압착.

**평가**: Fama-French / Ken French = 알파 원천 아니고 팩터 노출도 통제(neutralization) 도구. 후순위.

## ② 이론 검증 (각 기법 함정)
- **Lead-lag Rank-IC + Block-bootstrap autocorr 보정**: Forward 12M overlap → t-stat 부풀어. **Newey-West/Block-bootstrap 미적용 시 v1 IC=+0.658 신뢰구간 과소추정** 확률 매우 높음.
- **Regime-conditional partial correlation (glasso EBIC)**: regime 쪼개면 N 급감. EBIC 강하면 노드 다 끊김, 약하면 false positive. 국면 내 stationarity 가정 깨짐.
- **Anytime-valid e-process (Ville)**: Type-I 완벽 통제하나 Type-II 검정력 떨어질 수 있음(훌륭한 팩터인데도 늦게 반영).
- **Bai-Perron / BMA**: Bai-Perron은 retrospective → 백테스트 미래 참조 편향 치명적. 롤링 윈도우 OOS 엄격 필수.
- **MDE + Effective-n**: peak/trough 짧은 국면 소표본 Type-II 방어용.

## ③ 핵심 가설 7개 (반증조건 명시)

**H1 (valuation vs momentum — 국면 전반부)**
가설: trough/early-recovery에서 normalized valuation(P/B, 정상화 EPS 기준 fwd P/E) > price momentum 예측력.
반증: 사후 NBER trough 이후 12M 윈도우 block-bootstrap 통제 후 OOS Rank-IC(Momentum) - Rank-IC(Valuation) > 0 이 trough 표본의 30% 이상 발생.

**H2 (valuation vs momentum — 국면 후반부)**
가설: late-cycle/peak에서 earnings revision momentum + price momentum > valuation.
반증: peak 국면 Rank-IC(Valuation) anytime-valid e-process가 1.0(baseline) 이상 유지하며 단측 붕괴 X.

**H3 (Capital Cycle과 Peak Trap)**
가설: TTM Capex/Sales 증가율 상위 20% + Inventory/Sales 증가율 상위 20% (peak_trap) 종목은 val_gap 크더라도(저평가로 보여도) Forward 12M alpha 음수.
반증: peak 국면 Partial Rank-IC(Capex_Growth | Valuation_Gap) >= 0 (밸류에이션 통제 후에도 capex 늘어난 종목 수익률 양호)이 OOS 2개 윈도우 연속.

**H4 (매크로 선행성 — ISM과 이익 조정)**
가설: ISM 제조업 New Orders - Inventories 스프레드가 경기민감(XLI/XLB)의 EPS Revision Breadth에 3-6M 선행.
반증: Cross-correlation(ISM_Spread_lag(3to6), Revision_Breadth) p>0.05 또는 corr < +0.2.

**H5 (신용 주기와 멀티플 붕괴 — 공통원인)**
가설: contraction 국면 경기민감 multiple 축소는 개별 이익 변동 아닌 HY OAS 확대(공통 인자) 주도.
반증: contraction 국면 glasso EBIC에서 HY_OAS_diff ↔ Sector_Multiple_diff partial-corr edge 미생성 또는 DXY 등 통제 시 0 수렴.

**H6 (영업레버리지의 비대칭성)**
가설: Operating Leverage(proxy: Gross Margin/EBIT Margin 비율) 상위 그룹은 ISM 확장기 시장 대비 비대칭 양의 알파.
반증: ISM > 50 + 상승 추세 구간 [High DOL - Low DOL] anytime-valid e-process가 하한 임계(reject threshold, 예 < 0.1) 단측 붕괴.

**H7 (금리 민감도의 종목 특성 분리)**
가설: 10Y 금리 상승 → 고멀티플/early-cycle(SOX, XLY 일부) 부정 / value-cyclical(XLE/XLF) 긍정(NIM·인플레 헷지).
반증: 금리 상승 국면(3M 연속 금리 상승) Rank-IC(Rate_diff, Forward_Ret) 고멀티플 vs 저멀티플 그룹 간 통계 유의한 부호 반전(sign flip) 부재.

## Gemini 추가 질문 (Round 2 대상)
**regime 분류**: NBER(사후) vs 매크로/자산가격 기반 사전·실시간 확률 모델(HMM 등) 어느 쪽? 사후 데이터 사용 시 백테스트 vs 라이브 괴리 큼.
