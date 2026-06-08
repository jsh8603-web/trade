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
