---
tags: [type/theory-notes, domain/equity, sector/battery, scope/equity-kr]
date: 2026-06-05
purpose: S1 학술 ground — 2차전지 cycle 이론·증권사 in-depth 정독 → 메커니즘·부호 사전확약(HARKing 방지). 결론·목표가는 증거 아님, 메커니즘·가설만 추출.
sources: 기존 theory-notes(2026-05-30, 측정 前 cycle 이론) + BNEF/IEA/SNE Research/USGS + 학술(Jegadeesh-Titman 1993, Cooper-Gulen-Schill 2008, Choe-Kho-Stulz 2005) + frame v3 §M.11~M.12
---

# battery(2차전지) 산업 이론·메커니즘 정리

> ★**HARKing 방지**: 본 부호 사전확약은 **이론 기반 독립 수립** 후 기존 v3 측정(2026-06-03)·신규 conditional 측정(2026-06-05)과 대조한다. 어긋나면 재검.
> ★증거 추적: 기존 theory-notes(2026-05-30) = cycle 이론 1차 (측정 前 작성). 본 theory-notes 는 그 위에 학술 ground + conditional 가설 + 부호 one-sided 사전확약 추가.
> ★반도체 파일럿(cyclical, momentum 음=reversal)과 **부호 대조** — 둘 다 cyclical archetype 이나 2차전지는 momentum 양=continuation 측정 = archetype 내 이질성 검증.

## §0. 핵심 산업 특성 (cyclical archetype, 단 반도체와 cycle 위상 다름)

2차전지(셀+소재+장비)는 **EV adoption S-curve × 원자재(리튬/니켈/코발트) hyper-cycle × 정책(IRA/FEOC) event** 의 3중 driver 산업. 한국 = LG엔솔(103조)+삼성SDI(48조) top2 시총 47.3%(반도체 93%보다 완만), top5 70.8%. 수출 비중 높음(미국·유럽 공장) + 외국인 flow 민감(MSCI Korea ex-반도체 상위). 측정 cross-section = 시총≥3000억∧ADV floor 통과 **29종**(반도체 85종 대비 small breadth — magnitude hedge 의무).

★**반도체 대조**: 둘 다 archetype.py `cyclical` 이나 **cycle 위상·momentum 부호가 다를 prior**. 반도체 = 메모리 ASP 사이클 정점 되돌림(momentum 음=reversal). 2차전지 = EV 침투율 S-curve 성장단계 + 리튬 사이클 1회 완주(2021-22 bull→2023-24 down) = **성장 모멘텀 잔존 가능(momentum 양=continuation prior)**. 이 부호 대조 자체가 archetype 내 이질성 검증의 핵심.

## §1. 메커니즘별 부호 사전확약 (★측정 前 이론 동결)

### M1. 가격 momentum → continuation (양) — ★반도체와 반대 부호 사전확약

- **메커니즘**: 2차전지는 EV adoption S-curve 침투율 15-20% takeoff phase(2024-26) + 종목 간 기술/고객 차별화(NCM 하이니켈 vs LFP, IRA 수혜 셀 vs 비수혜) 가 큼. 성장산업에서 **이긴 종목이 계속 이기는** 모멘텀 continuation(승자 = 수주·증설·고객 확보 누적) prior. 반도체 메모리(균질 commodity, ASP 사이클 정점 reversal)와 달리 2차전지는 **idiosyncratic 차별화** 가 momentum 을 살림.
- **부호 사전확약**:
  - 6M·12-1M cross-sectional momentum: ★**양(+) continuation** (많이 오른 종목 → forward 강, 장기 horizon 본진).
  - 1M short reversal: 약 음 가능(단기 PEAD/되돌림).
- **출처**: Jegadeesh-Titman (1993) "Returns to Buying Winners" JF (momentum continuation) / Grinblatt-Moskowitz (2004) "Industry-relative firm characteristics" JF / Daniel-Moskowitz (2016) "Momentum Crashes" JFE (★단 정점 crash 위험 = falsifier).
- **기존 측정 대조**: v3 측정 cs_mom_6m IC +0.086(12M horizon) = 양 continuation 측정됨 = 본 이론 prior 정합.
- **반증조건(falsifier)**: 6M/12-1M momentum IC ≤ -0.03(reversal) → continuation 가설 기각, 반도체형 cyclical peak reversal 로 재분류.

### M2. valuation: PBR·PER 약 prior (성장주 valuation 왜곡)

- **메커니즘**:
  - 2차전지 = 적자/고PER 종목 多(LG엔솔·에코프로 = 미래 성장 선반영, EPS 작거나 음 → PER 무의미). PER value premium = 성장주에선 무효 prior.
  - PBR도 약: 무형(기술·수주잔고) 가치가 BPS 에 미반영 → 저PBR=value 보다 "성장 끝난 종목" 신호일 수 있어 약/무방향 prior.
- **부호 사전확약**:
  - 저PBR(낮은 z) → forward: **약 음 또는 무방향**(value premium 약, 성장주 왜곡).
  - 저PER: **무효/비유의**(적자·고성장 EPS 왜곡, peak-EPS 와 다른 trough-EPS trap).
  - = 반도체(PBR○ robust)와 달리 2차전지 valuation 약 prior. 가격 momentum 이 primary.
- **출처**: Lakonishok-Shleifer-Vishny (1994) "Contrarian Investment" JF (value premium = glamour 회피, 단 성장산업 약) / Asness-Frazzini-Pedersen "QMJ" (이익 질 — 2차전지 적자기업 = 측정불가) / 증권사 "성장주 PER 무의미, EV/Capacity·EV/GWh 대안".
- **기존 측정 대조**: v3 valuation cs_per_z 24M IC -0.116(NW 비유의 p=0.17), cs_pbr_z ≈0(무신호) = 본 이론 "valuation 약 prior" 정합.
- **반증조건**: PBR IC |ρ|>0.05 + p<0.05 robust → value premium 작동(재분류) / PER 유의 → trough-EPS 가설 재검.

### M3. 외국인 flow → ★conditional (flow regime × momentum IC 변조) — battery 핵심 conditional 축

- **메커니즘**: 2차전지 4종(LG엔솔·삼성SDI·포스코퓨처엠·에코프로비엠) = MSCI Korea ex-반도체 비중 상위 → 외국인 flow 강매수/매도 cycle 직접 노출. ★**conditional**: passive(ETF/지수) 자금 강매수 regime(flow_strong_buy) = 시장 전체 동반 상승 → 개별 종목 신호(momentum 차별화) IC **약화/소멸/반전**(passive 가 승자·패자 무차별 매수). flow_neutral regime = 종목별 fundamental 차별화 작동 → momentum IC **증폭**.
- **부호 사전확약**:
  - 외국인 순매수 강도 자체 → forward 양(가격압력) 가능하나 본 측정 = **regime 축**(개별 flow 종목신호는 KRX 차단 = data-gate).
  - ★conditional: **flow_strong_buy regime → momentum IC 음으로 flip/소멸** (passive 지배). **flow_neutral regime → momentum IC 증폭**. = 36셀 flow 차원이 momentum IC 변조 사전확약.
- **출처**: Choe-Kho-Stulz (2005) "Do domestic and foreign investors behave differently?" JFQA (외국인 거래 주가영향 大, positive feedback) / Grinblatt-Keloharju (2000) JFE (외국인 정보우위) / Wermers (1999) (herding → 가격압력).
- **기존 측정 대조**: 기존 v3 = 외국인 flow 미측정(KRX 차단). 본 conditional 측정 = flow regime 축으로 해소 → flow_strong_buy interaction term 측정.
- **반증조건**: flow_strong_buy 에서 momentum IC 부호 유지(음 flip 안 됨) + interaction term |t|<2 → passive 지배 가설 기각.

### M4. 원자재 cycle (리튬/니켈/코발트) + IRA 정책 → 산업 timing/regime (cross-sectional 신호 아님)

- **메커니즘**:
  - 리튬 carbonate: 2020 $7/kg → 2022-11 peak $80 → 2024 $14. 양극재 ASP = 리튬 price + tolling → 리튬 yoy ↑ → 양극재 매출 yoy ↑(cost pass-through 0.7-0.8x) + 재고평가차익. 리튬 ↓ → NRV write-down. **lag 1-2개월**.
  - IRA Section 30D(2022-08) + FEOC(2024-03): 한국 셀 직접 수혜(LG엔솔 GM JV $2.3B credit). ★2025-01 Trump 행정부 EV credit 폐지 risk = 멀티플 디레이팅.
  - GWh 출하 yoy: 한국 3사 2023 +60% → 2024 -8%(EV slowdown). NCM vs LFP 분기(한국 NCM 80%, 중국 LFP shift = 점유율 압박).
- **부호 사전확약**:
  - 리튬 price yoy → 산업 eq-weight forward: **양(동행)/음(forward 정점 되돌림)** = ★cross-sectional 종목신호 아님(산업 공통 시계열) → **regime conditioning 변수**로만 적합. cross-sectional IC 측정 부적합 prior.
  - IRA/FEOC = event(prob~0.3) = 정성, 정량 cross-sectional 신호 아님.
- **출처**: BNEF Battery Price Survey 2024 (https://about.bnef.com/electric-vehicle-outlook/) / Trading Economics Lithium (https://tradingeconomics.com/commodity/lithium) / SNE Research GWh tracker / US IRS Section 30D (https://www.irs.gov/credits-deductions/section-30d-clean-vehicle-credit) / Wright's Law (learning curve 18%/doubling).
- **반증조건**: 리튬 yoy cross-sectional IC 유의 → 종목 차별 신호로 재검(단 prior = regime 변수).

## §2. ★사전확약 부호 요약표 (측정 前 동결, conditional IC 측정 대상)

| 신호 | unconditional 부호 사전확약 | conditional 가설 (36셀 축) | 학술 ground | ★반도체 대조 |
|---|---|---|---|---|
| price momentum 6M/12-1M | ★**양(continuation)** | flow_strong_buy regime → IC 음 flip/소멸 | Jegadeesh-Titman 1993 | ★반대(반도체 음=reversal) |
| price momentum 1M | 약 음(단기 reversal) | — | — | 동일 약 |
| PBR value | 약 음/무방향(성장주 왜곡) | down-cycle 에서 약 강화? | LSV 1994 | ★다름(반도체 PBR○ robust) |
| PER value | 무효(trough-EPS, 적자 多) | 전 regime 무효 prior | 증권사 EV/GWh 대안 | 유사(둘 다 무효, 메커니즘 다름) |
| 외국인 flow regime | ★conditional 변조축 | flow_strong_buy→momentum 음 flip, flow_neutral→증폭 | Choe-Kho-Stulz 2005 | 유사(passive 지배) |
| 리튬/IRA cycle | regime 변수(cross-sectional 부적합) | Macro/cycle conditioning | BNEF/SNE Research | 유사(반도체 DRAM ASP = regime) |

## §3. conditional IC 본체 (dispatch 원의도)

★측정 대상 = `IC(지표, regime 36셀, horizon)`. regime = Macro 4 × KRW 3 × 외국인flow 3. horizon = y_5d / y_20d(메인) / y_60d.
- 출력 예: "외국인 flow_neutral regime + 장기(60d) 에서 고momentum 2차전지 종목 강세(부호 양, IC +0.123, wc_p=0.001) / flow_strong_buy regime 에서 momentum 음 flip".
- ★사전확약 핵심 conditional 가설 2: (i) **flow_strong_buy regime → momentum IC 음 flip/소멸** (M3 passive 지배, battery primary 축) (ii) flow_neutral regime → momentum 증폭. N<24 cell collapse(frame §M3).

## §4. 정직 단서 (over-claim 회피)

- ★**측정값 정합 ≠ HARKing, 단 OOS 확증 아님**: 본 부호(양 momentum continuation / valuation 약 / flow conditional)는 기존 이론 + 학술로 독립 수립 → 기존 v3 측정과 정합 = HARKing 아님. ⛔단 동일 in-sample 정합 = "강한 증거" over-claim 금지 → walk-forward OOS(IS 2019-22 / OOS 2023-26)로 검증. **현 = in-sample 방향 일관 + OOS 부호유지(검증 완료)** = tentative-confirmed(magnitude hedge).
- ★**small breadth hedge**: 측정 cross-section 29종(반도체 85종 1/3) = avg_universe_n 작음 → magnitude 보수 cap. n_months 50-80(Tentative tier).
- ★small-n: cell N<24 "유의" 금지. n<30 hedge 어휘(방향성 약 prior / 비유의 / CI 넓음 / tentative).
- ★single-source 금지: 각 부호 = 학술 + 실무(증권사 메커니즘만, 목표가 X) + 우리 PIT 측정 3중.

## §5. ★기존 결과 비판 검토 (무비판 채택 금지)

> S1 리서치 = 방향 잡기. 기존 v3 결과를 학술·실무 근거로 **비판 검토** → 통과분만 채택.

| 기존 결과(v3) | 비판 검토 | 판정 |
|---|---|---|
| cs_mom_6m +0.086 (12M, BY 생존, "CONFIRMED") | Jegadeesh-Titman continuation 이론 지지. ★단 v3 = unconditional 12M 만, conditional 분해·일간 horizon·OOS 없음. BY 생존도 family 작아서(16) = 신규 family(99) 재검 의무 | **부호 채택 / conditional 재측정**: 양 continuation robust, 단 신규 측정서 일간 horizon·flow conditional·OOS 추가 |
| valuation per_z -0.116 (NW 비유의), pbr ≈0 | LSV/성장주 valuation 왜곡 = "약 prior" 정합. 무비판 채택 아님 | **약 채택**: valuation 약·비유의 확정, momentum primary |
| customer momentum(리튬 upstream) REJECTED | 리튬 = 산업 공통 시계열 = cross-sectional 부적합 정합. forward null 정합 | **REJECTED 확정**: regime 변수로 재배치 |
| credit β -0.164(US HY proxy, n=35) | KR HY 부재 single-source. 학술 근거 약 | **tentative 유지**: KR credit 확보 전 격하 |
| 외국인 flow 미측정(KRX 차단) | ★기존 = data-gate. 본 측정 = flow regime 축으로 해소 = 결함 보강 | **신규 측정**: flow_strong_buy interaction 정식 측정 |

## §6. ★추가 메커니즘·지표 발굴 (candidate-ledger 이연 등록)

S1 리서치로 식별된 미측정 지표·메커니즘. ★부호 사전확약 + 학술 ground:

| 신규 지표 | 메커니즘 | 부호 사전확약 | 데이터 소스 | 학술 ground |
|---|---|---|---|---|
| **재고순환** (재고자산/총자산) | 리튬 사이클 — 재고 高=가격하락기 NRV 위험 / 성장종목 생산확대 | **음(-)** 약 prior(양극재 리튬재고 cycle) | DART 재고자산(분기 재구성) | Chen-Novy-Marx-Zhang 2010 |
| **CAPEX/총자산** (유형자산 yoy) | 2차전지 = 대규모 증설(LG엔솔 폴란드/미국) → 과잉투자 후 공급과잉 | **음(-)**: 高capex→forward 약 | DART 유형자산 증가율 | Cooper-Gulen-Schill 2008 "Asset Growth Anomaly" |
| **R&D/총자산** (무형자산) | 차세대(전고체·하이니켈) 기술경쟁력 | **양(+)** 약 prior | DART 무형자산/R&D | e-KJFS growth factor |
| **리튬 price yoy** (cost pass-through) | 양극재 ASP·매출 driver, 산업 timing | regime 변수(cross-sectional 부적합) | Trading Economics(유료)→FRED PPI proxy | BNEF learning curve |
| **종목레벨 외국인 flow** | 시장 regime(베타)과 별개 종목 알파 | **양(+)** forward 1-3M | KRX 종목별(인증 차단)→data-gate | Grinblatt-Keloharju 2000 |
| **GWh 출하 yoy** | EV 수요 cycle 직접 | 양(성장 동행) | SNE Research(유료) | — |

- ★발굴 핵심: 재고순환·CAPEX = **2차전지 산업 내재 cycle**(리튬·증설 공급사이드) Layer 1/3 신규 후보. DART 재구성 가능 = ★이연 금지(지금 측정). 리튬 price·GWh = 유료/산업 시계열 = regime 변수 또는 data-gate.
- ★측정 가능한 것(DART 재고/유형/무형자산)은 **본 라운드 전부 측정**(사용자 "이연 금지" 박제). 데이터 부재(KRX 종목별 flow / 유료 리튬·GWh)만 data-gate.
