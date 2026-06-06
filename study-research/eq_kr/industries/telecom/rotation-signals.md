---
tags: [type/rotation-signals, domain/equity, sector/telecom, scope/equity-kr]
date: 2026-06-06
purpose: 통신 업종 rotation(섹터 비중 OW/UW 타이밍) 신호 — 이론 부호 사전확약 + 통계검증 + 판정. ★1차 mom_12_1 +0.284 패널구성 artifact 적발.
sources: theory-notes(통신 defensive 배당주) + rotation-analyst v1/v2(_rotation/validation-rotation-v{1,2}.json) baseline 검증 + measure_rotation_telecom.py
---

# 통신(telecom) 업종 rotation 신호

> ★rotation = 업종 자체 비중 타이밍(OW/UW). 통신은 종목selection(cross-sectional) 불가(service 3사 과점 INSUFFICIENT) → rotation이 활로.
> ★패널 = 통신서비스 strict 화이트리스트 **SKT(017670)/KT(030200)/LGU+(032640) 동일가중** (team-lead 지시, n_months=88).
> ★★CRITICAL: 1차 rotation-analyst "mom_12_1 +0.284(y_60d)"은 ★패널구성 artifact(아래 §5). strict service 3사 단독 = mom 무신호+OOS flip.

## §1. 부호 사전확약 (측정 前 이론 동결, HARKing 방지)

★통신 = **defensive 고배당 bond-proxy**. 이론 framework 3축:
- (1) **defensive counter-cyclical rotation**: 경기/위험선호 cycle 강세 → 자금이 defensive 통신서 cyclical로 이탈 → 통신 UW. (risk-on/off defensive rotation, Asness et al. defensive factor)
- (2) **배당 duration**: 금리↓ → 통신 OW(bond-proxy 리레이팅). 금리 cycle rotation (Cornell 2000).
- (3) **dividend-carry persistence**: 고배당 defensive carry/flow 누적 → momentum. (★검증 필요)

| # | 신호 | 이론 부호 | 메커니즘·근거 |
|---|---|---|---|
| 1 | semi_ppi yoy (반도체 PPI=경기/risk-on proxy) | 음(-) | defensive counter-cyclical: 반도체/경기 cycle↑ → 자금 cyclical 이탈 → 통신 UW |
| 2 | cli_chg (경기선행 Δ) | 음(-) | 경기개선 → defensive 통신 UW (semi_ppi 동형 risk-on) |
| 3 | KR10Y 금리 level Δ | 음(-) | 배당 duration: 금리↑ → bond-proxy 디레이팅 → 통신 UW |
| 4 | d_KR10Y (금리 Δ) | 음(-) | 금리 상승 → 통신 UW (duration) |
| 5 | KR 커브(10Y-3M) Δ | 음(-) | 커브 스티프닝(경기회복) → 통신 UW |
| 6 | 외국인 flow (순매수) | 음(-) | risk-on flow↑ → low-beta defensive 통신 UW |
| 7 | usdkrw yoy (환율) | 양(+) | 원화약세(risk-off) → 방어주 통신 OW (방향 약 prior) |
| 8 | d_usdkrw (환율 동시) | 양(+) | 원화약세 동시 → 통신 상대강세 (약) |
| 9 | mom_12_1 (12-1 가격 momentum) | 양(+) | dividend-carry persistence: 고배당 carry 누적 → momentum (★검증 필요) |
| 10 | mom_6 (6M momentum) | 양(+) | carry momentum (약) |
| (data-gate) | ARPU / 5G 가입자순증 / 마케팅비 / 주파수경매 | 양(+) ARPU·5G / 음 마케팅비 | ★MSIT/통계청 무료 time-series 부재 = 미측정(한계 박제) |

★OW(비중확대) = risk-off 국면(semi_ppi↓ + flow 순매도 + 금리하락). UW(비중축소) = risk-on(경기/반도체 cycle↑ + flow 순매수 + 금리상승).
★FDR family = 위 10 측정 가설(폐기분 포함). 측정 후 family 재정의 금지.

## §2. ★mom_12_1 이론 검증 (data mining vs 이론 정당) — team-lead 핵심 지시

1차 rotation-analyst = telecom mom_12_1 y_60d **+0.284**(wc_p=0.0115, OOS hold) 발견. = "통신 업종 12M momentum이 forward 양". 이론 근거 약(가격통계).

★검증 1 — **이론 설명력**: mom_12_1을 공통인자{semi_ppi, flow, rate}에 residualize → 공통인자 설명 R²=**0.07**(약, mom은 공통인자 재포장 아님). 단 이건 mom이 살아있을 때만 의미.

★검증 2 — **strict service 3사 패널서 재현**: ★mom_12_1 60d = **+0.063(wc_p=0.53, OOS flip)** = 비유의 + OOS 부호불안정. → ★1차 +0.284는 **패널구성 artifact**(broad telecom 패널 = equipment 혼입 추정, §5). service 3사 defensive 단독 = momentum 무신호.

★결론: dividend-carry persistence 이론 = ★**service sector서 미입증**. mom_12_1 raw 자체가 비유의+OOS flip = 신호 부재. = **data-mining 채택불가**(이론 R² 검증 이전에 신호 자체 소멸).

## §3. 측정 결과 (★service 3사 strict 단독 × y_60d)

후보 10개(8 측정 + data-gate 4) × {level Δ / momentum} × y_60d (rho, wc_p, OOS, t_power):

| # | 후보 | rho (60d) | wc_p | OOS | t_power(2.802 breakeven) | prior 부호 | 판정 |
|---|---|---|---|---|---|---|---|
| 1 | **외국인 flow** | **-0.396** | **0.001** | -0.31 hold | **3.58 (well-powered)** | 음 ✅ | ★PASS-conditional |
| 2 | **semi_ppi yoy** | -0.261 | 0.027 | -0.37 hold | 1.29 | 음 ✅ | ★PASS-conditional(moderate) |
| 3 | cli_chg | +0.433 | 0.0005 | +0.12 hold | 2.36 | 음 ✗(반대) | exploratory(prior 위배) |
| 4 | usdkrw yoy | -0.305 | 0.008 | -0.02 | 1.79 | 양 ✗(반대) | exploratory(prior 위배) |
| 5 | KR 커브 Δ | +0.201 | 0.065 | +0.13 | 1.86 | 음 ✗ | 약/비유의 |
| 6 | KR10Y Δ | +0.117 | 0.299 | +0.15 | 0.94 | 음 ✗ | 비유의(duration 미확인) |
| 7 | d_usdkrw | -0.073 | 0.491 | flip | 0.68 | 양 ✗ | 무신호 |
| 8 | mom_12_1 | +0.063 | 0.529 | flip | 0.44 | 양 | ★data-mining(§2) |
| 9 | mom_6 | +0.072 | 0.472 | flip | 0.53 | 양 | 무신호 |
| 10 | ARPU/5G/마케팅비/주파수 | — data-gate | — | — | — | — | ★미측정(무료 부재) |

★= **후보 10개 검토**(8 측정 + ARPU/5G/마케팅비/주파수 4종 data-gate enumerate). y_20d도 측정(kr_curve +0.237 wc_p=0.014 + foreign_flow -0.189) but y_60d가 rotation 본 horizon.

### 핵심 결과
- ★**외국인 flow -0.396** = 가장 강 + well-powered(t_pow 3.58) + OOS robust(-0.31) + leave-episode 불변(-0.39, NOT episode-driven) + semi 통제 partial -0.39 독립. = ★이론(risk-on flow→defensive UW) 정합 strong.
- ★**semi_ppi -0.261** = OOS hold(-0.37) but leave-episode 약화(-0.16, 부분 episode-driven) + flow 통제 partial -0.21 잔존. = 이론(defensive counter-cyclical) 정합 moderate.
- ★FDR family(m=20) survivors = **[cli_chg, foreign_flow]**(raw_p_min=0.0005). semi_ppi BY 경계.
- ★mom_12_1 = data-mining(service 패널 비유의+OOS flip).

## §4. 판정

| 신호 | 판정 | 사유 |
|---|---|---|
| **외국인 flow (음)** | ★PASS-conditional (tradeable 1) | well-powered(t_pow 3.58) + OOS robust + leave-episode 불변 + 이론(risk-on→defensive UW) 정합. ★단 flow = 전산업 공통 driver(통신 고유 아님, L축 1회계상 주의) |
| **semi_ppi yoy (음)** | ★PASS-conditional (tradeable 2, moderate) | OOS hold + 이론(defensive counter-cyclical) 정합 but leave-episode 약화 + flow보다 약 |
| cli_chg (양) | exploratory(채택보류) | BY 생존이나 ★prior(음) 위배 = HARKing 회피. risk-on 지표와 음상관(-0.31) 통해 defensive 정합 가능하나 사전확약 위배 |
| usdkrw yoy (음) | exploratory | prior(양) 위배. 원화약세→통신 음 = 방어주 prior 반대(원화약세=수출 risk-on 통신 UW 가능) |
| KR 금리 duration | 미확인/INCONCLUSIVE | duration(음) prior 위배 + 비유의(15axis 본측정과 일치) |
| **mom_12_1** | ★data-mining REJECTED | service 단독 비유의+OOS flip. 1차 +0.284 = 패널구성 artifact(§5). dividend-carry 이론 미입증 |

★**rotation 종합 (team-lead 박제) = "통신 = defensive counter-cyclical rotation 본질, tradeable 2개(flow + semi_ppi), mom_12_1 = 패널 artifact REJECTED"**:
- ★통신 rotation 본질 = **risk-on/off defensive rotation**(외국인 flow + 반도체 PPI = risk-on 강세 → defensive 통신 UW / risk-off → OW). carry tilt(자문 수렴)보다 ★counter-cyclical defensive timing이 데이터 입증 본질.
- ★tradeable ≥2 충족: **외국인 flow(strong, well-powered) + semi_ppi(moderate)** = 이론+통계 양립 채택. 
- ★mom_12_1(1차 핵심) = **data-mining REJECTED**(service 단독 소멸, 패널 artifact).
- ★배당 duration(금리) = 미확인(INCONCLUSIVE, 본 capsule 일관). ARPU/5G = data-gate.
- ★주의: flow는 전산업 공통 driver(통신 고유 아님) = 통합 L축 1회계상 + 통신 = "defensive sleeve, risk-on UW" 라벨이 본질.

## §5. ★★CRITICAL: mom_12_1 +0.284 패널구성 artifact 적발

1차 rotation-analyst v1 telecom 패널 = mom_12_1 y_60d **+0.284**(OOS +0.36). ★strict service 3사(SKT/KT/LGU+) 단독 재현 = **+0.063(wc_p=0.53, OOS flip)** = 무신호.

★차이 = 패널 구성. 1차 패널 = telecom 디렉토리 broad 패널(service 3 + equipment 11 추정, frame §1.6 혼입). equipment(통신장비 KOSDAQ 소형 cyclical)는 momentum 보유 가능 → broad 패널 mom = ★equipment momentum 혼입.

→ ★mom_12_1 신호 = service defensive 본질 아님(패널구성 artifact). strict service 3사 = momentum 무신호 = dividend-carry 이론 미입증. ⛔통합 시 mom_12_1 채택 금지(패널 정의 = strict service 화이트리스트 의무).

## §6. rotation 시사 (통신 OW/UW)
- ★**risk-on 국면**(반도체/경기 cycle 강세 + 외국인 순매수 강) → 통신 **UW**(defensive 자금이탈). 
- ★**risk-off 국면**(반도체 cycle 둔화 + 외국인 순매도) → 통신 **OW**(defensive 방어). = 2026 현재 = 반도체 강세 국면 → 통신 상대 UW 신호.
- 배당 duration(금리) = 미확인(episode-poor single rate cycle). ARPU/5G = data-gate.
- ★통신 rotation = tradeable 2개(flow + semi_ppi) = defensive counter-cyclical timing. 종목selection 0(3사 과점). mom_12_1 = 패널 artifact 제외.
