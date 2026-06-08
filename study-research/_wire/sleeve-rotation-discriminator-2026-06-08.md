---
name: sleeve-rotation-discriminator-2026-06-08
description: US+KR 산업슬리브간 %를 지표/국면/경기로 바꿔 수익 낼 변별 지표가 있나 — 포트폴리오 백테스트(IS/OOS·비용·정적벤치 대조). 결론=ledger와 수렴(robust 변별 지표 없음, 유일 wired=real_rate→defensive).
tags: [type/research, domain/inv, topic/sleeve-rotation, axis/2-allocation, status/concluded]
date: 2026-06-08
related: cross-regime-ledger.md §2(real_rate→defensive adopted, cyclical←HY rejected, eq_kr rotation candidate), portfolio_decompose.py
---

# 슬리브간 % 변별 지표 — US+KR 포트폴리오 백테스트

> 질문(사용자): 미국·한국 모두 **산업슬리브간 비중을 지표/국면/경기에 따라 바꿔 수익 낼 변별력 있는 지표**가 있나. ★ledger 기확립분 먼저 확인(삽질 방지) → 포트폴리오-레벨 IS/OOS·비용·정적벤치 대조가 본 측정의 신규분.

## ledger 기확립 (재측정 안 함)
- **eq_us defensive ← real_rate(DFII10) z = adopted/wired**(`portfolio_decompose._modulated_us_weights`, fwd12M rank-IC −0.334 walk-forward 일관). = US 산업슬리브 **유일 채택 변별 레버**.
- eq_us cyclical ← HY credit = **rejected_provisional**(동시 −0.120 vs forward +0.460 부호충돌). mega_tech ← real_rate = rejected(OOS flip).
- eq_kr rotation = **candidate, portfolio alpha 0**(cs t2.04 실재나 운용 0). 외국인 flow = **동시 price impact**(flow-revive 측정).

## 신규 측정 — 포트폴리오 백테스트 (정적벤치·IS/OOS·비용)

### US (cyclical/defensive/mega_tech, 월별 2015-2026, 132mo)
정적 벤치가 매우 높음(mega-tech 시대): EW(1/3) ann +23.5%/Sharpe 1.39, **static OW mega +29.8%, 100% mega +39.2%**.

| 변별 시도 | IR vs EW | IS→OOS | verdict |
|---|---|---|---|
| 신용국면(hy_oas↑→defensive) | +0.51 (net) | **+0.99→+0.22** | front-loaded, OOS 약 |
| 슬리브 모멘텀(6-12M) | +0.46, t2.2 | +0.94→**+0.15** | = **mega-tech 베타**(momentum=winner 추종), OOS 붕괴 |
| VIX 국면 | −0.25 | — | EW 미달 |
| real_rate 변화 | −0.55 | — | EW 미달 |
| **국면조건부 스프레드(직접)** | — | — | risk-off(hy↑) def>cyc **t=−0.92 p0.37** / highVIX t=−1.33 p0.19 / real_rate↑ cyc>def t=−1.17 = **전부 비유의** = 국면이 리더십 유의하게 못 바꿈 |

→ **US: robust 변별 지표 없음.** 겉보기 승자(신용·모멘텀)는 **mega-tech 모멘텀 베타**(static OW mega가 더 높음) + OOS 붕괴. ledger의 real_rate→defensive(약·wired) 외 추가 레버 미발견.

### KR (12 산업, 월별 2019-2026, 84mo)
EW ann +22.6%/Sharpe 1.01.

| 변별 시도 | 측정 | verdict |
|---|---|---|
| study rotation_signals_panel | cs rank-IC **+0.093 t=2.85**(신호 실재 재현) | 신호 O |
| → 포트폴리오 tilt | IR vs EW +0.20, **IS +0.81 → OOS −0.36** | **OOS 음전환 = alpha 0 확정** |
| 슬리브 모멘텀 | mom3M +0.29 / mom12M −0.01 | 단기만 약, robust X |
| 외국인 flow 국면조건부 | inflow +0.23%/mo vs outflow −0.04%/mo | 희미한 in-sample(inflow때만 tilt 작동), OOS 미검증 |

→ **KR: 변별 신호 실재(t2.85)하나 포트폴리오 OOS 붕괴**(ledger alpha 0 확정). flow-inflow 조건부가 유일 희미한 잔존.

## 종합 verdict
- **양국 수렴**: 산업슬리브간 %를 국면/경기/모멘텀으로 바꿔 **robust(OOS·비용 생존) 수익 내는 변별 지표 = 없음**. cross-sectional 신호는 양쪽 실재(US momentum t2.2/KR panel t2.85)하나 **포트폴리오 OOS서 붕괴**(US 모멘텀=mega 베타, KR tilt 음전환).
- **유일 생존 = eq_us defensive ← real_rate**(이미 adopted/wired, 약신호). 추가 코드화할 신규 변별 레버 미발견.
- ★삽질 방지: 본 결론은 ledger(cyclical←HY rejected / eq_kr rotation alpha 0)와 **정합** — 포트폴리오 IS/OOS·정적벤치 대조로 "왜 안 되는지"(mega 베타·OOS 붕괴) 메커니즘만 추가.
- **잔존 open**: KR flow-inflow 국면조건부 tilt(+0.23 vs −0.04/mo) = 유일 미검증 희미 잔존, OOS·비용 검증 시 판정(현 prior 낮음).

산물: `eq_us/_wire-verify/measure_us_sleeve_rotation.py`·`measure_us_rotation_timing_vs_static.py` / `eq_kr/flow-revive/measure_kr_sleeve_rotation.py`.

---

## 추가 sweep — "확신 설 때까지" (2026-06-08, 사용자 지시)

ledger의 정론충돌 단서(저변동 역전)부터 재측정 + 슬리브 변별 가능성 소진.

### ★측정방법 결함 발견 — 저변동성 anomaly "역전"은 raw-return IC artifact
ledger/내 1차에서 cyclical `vol_60` IC +0.068(고변동 우위)=BAB/저변동 정론 역전처럼 보임. **재측정(raw vs 위험조정)**:

| 슬리브 | low-vol IC vs **raw** fwd수익 | low-vol IC vs **위험조정**(fwd Sharpe) |
|---|---|---|
| cyclical | −0.107 (t=−4.49) | **−0.013 (t=−0.59 NULL)** |
| defensive | −0.033 (t=−1.56) | +0.014 (t=0.63) |
| mega_tech | −0.234 (t=−6.55) | −0.061 (t=−2.02) |

→ **"역전"은 측정 artifact**: raw-return rank-IC가 강세장서 베타를 보상해 고변동주를 띄움. 위험조정하면 소멸. ★**함의**: 시스템 횡단면 채택기준(raw-return rank-IC)이 저변동/방어/quality 신호를 구조적으로 불리 측정 = defensive selection "死"의 한 원인(신호 결함 아닌 줄자가 베타 보상). 별도 박제 → `indicator-ledger`/방법론.

### 슬리브 변별 가능성 소진 (5-sleeve, risk-adj, drawdown)
- **risk-adj/drawdown steelman 실패**: VIX 고국면 defensive de-risk = 수익 +20.1%(EW +23.5%↓) + MaxDD −21.1% 개선無(2020/22 광범위 하락엔 방어주도 동반). inverse-vol=Sharpe 불변(수익-DD 1:1). risk-adj 모멘텀 Calmar 1.19 vs 1.12 미미.
- **5-sleeve(semi/fin/ind/def/meg) 모멘텀**: OW-top mom3M IR vs EW +0.68(IS+0.66/OOS+0.72 일관!)처럼 보였으나 — ★**decisive: static OW meg(Sharpe 1.40/+30.5%)가 모멘텀 로테이션(NET Sharpe 1.29/+27.8%)을 이김**. EW 초과 IR=laggard(def/fin/ind) 제외하고 mega/semi로 기운 것뿐, 타이밍 시도(2022 방어전환)는 오히려 손해. = **진짜 슬리브 타이밍 가치 0, 작동분=후견지명 mega 정적 베타**.

### ★최종 확신 (scope 명시)
**가용 데이터(eq_us/eq_kr 주식 슬리브, 2015-2026)·이 단일 mega-tech 지배 국면에서: 산업슬리브간 %를 동적으로 바꿔 robust(OOS·비용·위험조정 생존) 수익 내는 변별 지표는 없다.** 시도 전부(신용/VIX/real_rate 국면·raw/risk-adj 모멘텀·reversal·inverse-vol·de-risk·KR rotation panel·foreign flow) = 비유의 or OOS붕괴 or static-beta. 유일 양(+)은 **mega 정적 OW(후견지명 세속베타, 변별 아님)** + 이미 wired된 real_rate→defensive(약).
- ⚠️**scope 한계(정직)**: ① 단일 국면 표본(2015-26, value 10년 2000-08 부재) ② 주식 슬리브만(시스템 top-level 자산로테이션=Investment Clock은 stock/bond/gold/commodity 횡단, 본 측정 범위 밖=ledger adopted 별건) ③ 라이브 데이터 차단(per-sector flow 등 미측정). → "변별 불가" 확신은 **이 범위 한정**, 다국면·다자산·라이브신호선 재론 가능.

산물 추가: `eq_us/_wire-verify/remeasure_lowvol_raw_vs_riskadj.py`·`measure_riskadj_drawdown_rotation.py`·`measure_5sleeve_rotation_sweep.py`·`measure_momentum_vs_static_decisive.py`.
