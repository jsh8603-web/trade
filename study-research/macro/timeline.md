---
tags: [type/macro-timeline, domain/inv, study/macro, phase/M1, distributable]
date: 2026-05-30
study_id: macro
phase: "M1 배포용 거시 timeline (M2가 전 종목 세션에 배포)"
data: "data/historical 실 일별 n=756, 2021-12~2024-12 (분기 13). ⛔합성無"
consumer: "M2→전 종목 세션(eq_us/eq_kr/eq_intl/reit/commodity/gold/bond_cash/crypto). M3에서 각 종목이 본 timeline에 자기 종목 매핑→거시연관 상관."
note: 기간별 거시 이벤트·지표 요약 공통 기준선. 종목 세션은 자기 종목 수익률을 본 분기 regime·driver에 정렬해 거시연관 분석.
---

# M1 배포용 거시 Timeline — 공통 기준선 (2021Q4~2024Q4)

> **용도**: 전 종목 세션이 자기 종목/sleeve 를 **이 분기별 거시 국면·driver 에 정렬**해 거시연관(M3 상관)
> 분석. 모든 세션이 같은 timeline 을 쓰면 cross-sleeve 비교가 가능(L축 1회계상 정합).
> ⛔ **belief/flag 不유입**(U3 reflexive 차단) — 본 timeline 은 *실현 지표·이벤트*만.

## 1. 분기별 거시 지표 (실데이터, raw/m1-timeline.csv)

| 분기 | us10y(말) | Δus10y(bp) | DXY(말) | sp500% | nasdaq% | gold% | oil% | regime(proxy) |
|---|---|---|---|---|---|---|---|---|
| 2021Q4 | 1.51 | +8 | 95.7 | +5.6 | +2.6 | +2.6 | +14.7 | Recovery(성장>긴축) |
| **2022Q1** | 2.33 | **+70** | 98.3 | −5.5 | −10.2 | +8.3 | **+31.8** | 긴축/리스크오프 |
| **2022Q2** | 2.97 | +59 | 104.7 | **−16.7** | **−22.7** | −6.0 | +6.5 | 긴축/리스크오프 |
| **2022Q3** | 3.80 | **+91** | **112.1** | −6.3 | −5.0 | −7.6 | −26.7 | 긴축/리스크오프 |
| 2022Q4 | 3.88 | +23 | 103.5 | +4.4 | −3.2 | +7.5 | −4.0 | Recovery |
| 2023Q1 | 3.49 | **−30** | 102.5 | +7.5 | +17.7 | +7.0 | −1.6 | Reflation/Recovery |
| 2023Q2 | 3.82 | +39 | 102.9 | +7.9 | +13.1 | −3.2 | −12.2 | Recovery |
| **2023Q3** | 4.57 | +71 | 106.2 | −3.8 | −4.3 | −3.8 | **+30.1** | 긴축/리스크오프 |
| **2023Q4** | 3.87 | **−82** | 101.3 | **+11.2** | +12.8 | **+12.7** | −19.3 | Reflation/Recovery |
| 2024Q1 | 4.21 | +26 | 104.6 | +10.8 | +10.9 | +7.4 | +18.2 | Recovery |
| 2024Q2 | 4.34 | +1 | 105.9 | +4.1 | +8.1 | +4.1 | −2.6 | Reflation/Recovery |
| **2024Q3** | 3.80 | **−68** | 100.8 | +5.2 | +1.7 | **+13.3** | −18.2 | Reflation/Recovery |
| 2024Q4 | 4.18 | +44 | 106.3 | +6.6 | +10.2 | −0.5 | −1.8 | Recovery |

★regime(proxy) = rate방향(Δus10y)×equity방향(sp500). ⚠️ 진짜 Investment Clock 은 CPI·성장 펀더멘털
필요(collector 이연) — 본 라벨은 가용 데이터 proxy. 종목 세션은 이 라벨을 *참고*하되 자기 데이터로 재검증 권장.

## 2. 거시 이벤트 박제 (팩트 — 분기 정렬)

| 시기 | 거시 이벤트 | 지배 driver |
|---|---|---|
| 2022Q1 | Fed liftoff(3월 첫 인상) + 러-우 전쟁(2월) + 인플레 급등 | rate↑·oil↑(공급충격) |
| 2022Q2~Q3 | 공격적 75bp 연속 인상, CPI peak ~9%(6월), DXY ~114 급등(9월), 베어마켓 | rate↑·dollar↑(긴축) |
| 2022Q4 | peak 매파, 10월 저점 후 반등 | rate 고원 |
| 2023Q1 | **SVB/지역은행 위기(3월)** → 금리 급락(−30bp), 안전선호 | credit/risk-off→rate↓ |
| 2023Q2~Q3 | 견조한 성장 + AI 랠리(nasdaq), 금리 ~5% 재상승(10월), 유가 급등(Q3 +30%) | growth + rate↑·oil↑ |
| 2023Q4 | pivot 기대 → 금리 급락(−82bp), 전 자산 랠리 | rate↓(완화기대) |
| 2024 | **Fed 인하 사이클 개시(9월 −50bp)**, 금 사상최고 랠리 | rate↓·dollar↓→gold↑ |
| 2024Q3 | 인하기대 금리 −68bp, 금 +13% | rate↓→gold↑ |

## 3. Regime epoch 요약 (종목 매핑용 구간)

| epoch | 기간 | 성격 | 종목 함의(거시전이) |
|---|---|---|---|
| **E1 긴축충격** | 2022Q1~Q3 | rate↑↑·dollar↑↑·risk-off | 고듀레이션(tech)·달러민감 최대 타격. dollar loading 최대 |
| **E2 전환·반등** | 2022Q4~2023Q2 | rate 고원→완화초입, AI 성장 | 성장주 회복, SVB 후 안전선호 단발 |
| **E3 금리재상승** | 2023Q3 | rate↑·oil↑ | 듀레이션 재압박, 에너지 우위 |
| **E4 pivot·인하** | 2023Q4~2024 | rate↓·dollar↓ | 금·고듀레이션 우위, 위험선호 |

## 4. 종목 세션 사용법 (M3 거시연관 분석 가이드)

각 종목 세션은 자기 sleeve/종목 수익률을 위 분기·epoch 에 정렬해:
1. **regime별 종목 수익률 분해** — 각 regime(proxy 또는 자기 재검증)에서 종목의 평균수익·변동성.
2. **거시 driver loading** — 종목 ~ [rate(Δus10y), dollar(DXY r), oil] 회귀로 factor 민감도(M1 방법론
   raw/m1_factor_linkage.py 참조). ★rate 직접 loading 보다 **dollar 채널·국면조건부**가 본질일 수 있음
   (M1 발견: 주식 rate loading≈0, dollar loading rate-up 2배).
3. **cross-asset-class vs within-sleeve 구분** — 거시 named factor 는 자산군*간* linkage 용. within-sleeve
   공통(예: 종목간 0.9+ 상관)은 거시 아닌 equity factor — 자기 sleeve 모델 소관(M1 caveat).
4. 결과를 main 에 회신 → M4 거시 레이어 보강.

## 5. 한계 (정직)
- regime 라벨 = rate×equity proxy(진짜 Investment Clock 아님, CPI·성장 collector 이연).
- 기간 2021Q4~2024Q4(3년, 13분기) — 장기 epoch(GFC·코로나) 미포함, 현 데이터 범위 한정.
- 거시 이벤트 = 공개 팩트 박제(날짜 정렬), 종목별 영향은 M3에서 각 세션 실측.
- 참조: M1 factor 발견(raw/m1-findings.md) = M4 선행 근거(거시→종목 dollar 채널·국면조건부 전이).
