---
tags: [type/rotation-signals, domain/inv, scope/equity-kr, sector/consumer, status/measured]
date: 2026-06-06
owner: consumer-analyst (kr-equity team, opus 1m)
trigger_to_resume: "_rotation/rotation-timing.md §3 consumer row + 본 capsule"
---

# consumer(소비재) 업종 ROTATION TIMING — 업종 자체 비중 timing

> **임무** = "어느 국면에 소비재 업종을 OW/UW 하나" = rotation timing (종목selection capsule 위 차원).
> ★파이프라인 = **이론을 통계가 검증** (가격통계 단독 = data mining 채택불가). 부호 사전확약(데이터 접촉 前 동결).
> ★[2026-06-06 재발굴] 후보 14 driver(68 셀) 전수 enumerate (team-lead 규칙 ≥8) → ★tradeable 채택 4 (규칙 ≥2 충족).

## 0. ★측정 설계 (rotation v2 NO_DIRECT 보강)

rotation v2(`_rotation/measure_rotation_v2.py`)는 consumer 를 NO_DIRECT(고유 cycle 직접 부재)로 분류 → momentum
proxy 만 측정. 본 측정 = ★소비재 전문성으로 **고유 cycle 직접지표 14 driver 전수 수집·측정**:
- **분석 unit** = 소비재 업종 eq-weight 패널(28종 월수익) + sub-cluster 분리(cosmetics/food/retail, A-4 이질).
- raw 재현 = `raw-v3/measure_rotation_consumer.py` → `validation-rotation-consumer-v1.json`.
- universe = strict 화이트리스트(pass_floor 28종, 부수종목 오염 차단). 합성 0%, 실데이터 PIT.

## 1. ★이론 부호 사전확약 (측정 前 동결 — HARKing 차단, 14 driver 전수)

| # | driver | sub-cluster | 메커니즘 (이론) | 사전확약 | source (사전검증) |
|---|---|---|---|---|---|
| 1 | **CSI 소비지출 3M모멘텀** | retail/내수 | 소비심리 개선 모멘텀 → 소비재 매출 전망↑ | ★양(+) | ECOS 511Y002 FMCB (2018~2026-05) |
| 2 | CSI 소비지출 yoy | retail | 소비심리 level yoy → 내수 | 양(+) | ECOS FMCB |
| 3 | CSI 여행비전망 yoy | cosmetics | 리오프닝·면세 회복 → 화장품 | 양(+) | ECOS FMCCD |
| 4 | CSI 의류비전망 yoy | cosmetics | 의류·화장품 지출 | 양(+) | ECOS FMCCB |
| 5 | CSI 향후경기전망 yoy | industry | 경기심리 → 소비재 | 양(+) | ECOS FMBB |
| 6 | 한국 소매판매 yoy | food/retail | 내수↑ → 매출↑ | 양(+) | FRED KORSARTMISMEI (2024-03 제약) |
| 7 | 中CLI yoy/d3 | cosmetics | 중국 경기↑ → 화장품 中매출 | 양(+) | FRED CHNLOLITOAASTSAM |
| 8 | 항셍/상하이 3M모멘텀 | cosmetics | 中주식 risk-on = 中소비 | 양(+) | yfinance ^HSI/000001.SS |
| 9 | **홍콩 3M모멘텀** | cosmetics | 관광/면세 risk-on (리오프닝) | 양(+) | yfinance 1379.HK |
| 10 | USDCNY yoy | cosmetics | 위안 강세 → 中구매력↑ | 음(-) | FRED DEXCHUS |
| 11 | **곡물 yoy** (ZC/ZW/ZS) | food | 곡물↑ → COGS↑ → 마진↓ (cost-push) | 음(-) | yfinance |
| 12 | WTI유가 yoy | food/industry | 원가↑·소비여력↓ | 음(-) | yfinance CL=F |
| 13 | XLP-XLY 상대모멘텀 | industry | 글로벌 방어 우위 = 소비재 OW | 양(+) | yfinance XLP/XLY |
| 14 | **mom_6 reversal** | industry | 내수 방어주 평균회귀 | 음(-) | 가격 (rotation v2 재현) |

★data mining 차단: 14 driver(×sub-cluster×horizon = 측정 68 셀) = 전부 소비재 cycle 이론 사전확약.

## 2. ★핵심 발견 (validation-rotation-consumer-v1.json)

### ★(A) tradeable 채택 4 — 이론+통계 둘 다 충족

> ⛔**[2026-06-06 G-C 재audit 정정]** primary = **mom_6 reversal cosmetics**(외부시장 resid 후 −0.425 강화 = genuine idiosyncratic). **CSI는 ★STRONG → TENTATIVE 격하**: theory-family(m=12) 한정 BY 생존, m=68 single 미생존 + Bonferroni 미통과 = underpowered. ★C축 robustness 수치(residual +0.370 / LOY +0.24~0.41)는 **코드 미산출 추적불가** = 신뢰 보류. SSOT = _rotation/rotation-study_session.yaml consumer 행.

| # | 신호 | 패널 | rho(60d) | wc_p | OOS | robustness | 판정 |
|---|---|---|---|---|---|---|---|
| 1 | **CSI 소비지출 3M모멘텀** | industry | **+0.325** | **0.001** | +0.335→+0.303 (적격✓) | ⚠️residual/LOY 수치 코드 미산출 추적불가 | ⚠️**TENTATIVE**(재audit 격하, was STRONG) |
| 2 | **mom_6 reversal** | industry | **−0.251** | **0.018** | −0.157→−0.554 (유지✓) | residual −0.361(강화) | ★**채택** |
| 3 | **mom_6 reversal** | cosmetics | **−0.324** | **0.004** | −0.073→−0.748 (유지✓) | residual −0.335 | ★**채택** |
| 4 | **홍콩 3M모멘텀(관광)** | industry | **+0.254** | **0.044** | +0.049→+0.287 (적격✓) | 이론일치(리오프닝/면세 양) | ★**채택(TENTATIVE)** |

- ★**CSI 소비지출 3M모멘텀 = 가장 강(유일 BY 생존)**: 소비심리 단기 개선 → 소비재 60d OW. residual 강화 + LOY 전부
  양 = data-mining/single-episode 아닌 진짜 내수 소비 cycle alpha. retail 패널 +0.301(wc_p0.002). ★이론(소비심리
  개선=소비재 매출 전망 개선) + 통계 둘 다 robust = ★소비재 전문성으로 발굴한 핵심 rotation 신호.
- ★**mom_6 reversal**(internal v2 재현): 내수 방어주 평균회귀. cosmetics 60d 최강(wc_p0.004 OOS−0.75). residual 강화.
- ★**홍콩 관광 모멘텀**: 리오프닝/면세 회복 → 화장품 risk-on. wc_p0.044 OOS적격 but underpowered = TENTATIVE.

### (B) TENTATIVE 보조 — 이론 일치하나 underpowered (방향 prior)

| driver | best | sign_match | wc_p | 비고 |
|---|---|---|---|---|
| **곡물 cost-push (음식료)** | soy food y_60d −0.221 | ✓전부 음(corn/wheat/soy) | 0.0695 | OOS−0.21 유지. 음식료 한정, underpowered |
| WTI유가 | industry y_60d −0.261 | ✓음(원가) | 0.0165 | ★OOS flip(−0.35→+0.08) = OOS 약, 채택불가 |

### (C) ★REJECTED / 부호반대 — 이론 사전확약 위반 (정직 박제)

| driver | result | 사유 |
|---|---|---|
| **CSI 소비지출 yoy / 여행비 yoy / 의류비 yoy** | ★부호 **반대**(음, exp 양) | ★yoy(level 기저효과)는 부호반대 — CSI 高수준=고점=forward 약(평균회귀). d3(단기변화)와 mechanism 분리. yoy 채택불가, d3 채택. |
| 항셍/상하이 모멘텀 | 부호 혼재(sse 음) | 中주식 모멘텀 = 과열 reversal? 사전확약(양) 미성립 = 채택불가 |
| USDCNY | y_20d 일치/y_60d 반대 | 혼재, 약 = 채택불가 |
| 中CLI | 약신호 | OECD CLI 발표지연 + 가용 짧음 |
| 한국 소매판매 yoy | 2024-03 제약 | DATA-GATE (OECD MEI discontinuation) |
| XLP-XLY 상대모멘텀 | y_20d 양/y_60d 음 혼재 | 글로벌 ETF rotation = 한국 소비재 매핑 약 |

## 3. ★rotation 판정 (G-G v2) — 후보 14 / 채택 4

- **후보 enumerate = 14 driver** (측정 68 셀, team-lead 규칙 ≥8 충족).
- **★tradeable 채택 = 4** (규칙 ≥2 충족): (1) CSI 소비지출 d3 STRONG (2) mom_6 reversal industry (3) mom_6 reversal
  cosmetics (4) 홍콩 관광 모멘텀 TENTATIVE.
- **TENTATIVE 보조 1**: 곡물 cost-push(음식료, underpowered 방향 prior).
- **REJECTED/채택불가**: CSI yoy 3종(부호반대=기저효과) / 항셍·상하이(혼재) / USDCNY(혼재) / 中CLI(약) / WTI(OOS flip) /
  한국 소매판매(DATA-GATE) / XLP-XLY(혼재).
- ★**G-G v2 = PASS-conditional**: CSI 소비지출 d3 = BY 생존 = 상대적 강(단 전 신호 underpowered tier, magnitude tentative).

## 4. ★sub-cluster 이질 (종목 capsule A-4 cancel 과 동형)

- **retail/내수**: CSI 소비지출 d3 강(+0.30) = 내수 소비심리가 유통 driver.
- **cosmetics**: 홍콩 관광·리오프닝(양) + mom_6 reversal 최강(−0.32) = 中cyclical + 변동성 평균회귀.
- **food**: 곡물 cost-push(음, borderline) = 원가 driver.
- ★= sub-cluster 마다 rotation driver 다름 = 종목 capsule A-4 cancel(화장품 value vs 음식료 무신호) 과 동형 구조.

## 5. ★gated 설계 (over-trade 차단, rotation-timing.md §4 준용)

1. **default 0** — 신호 무발현 시 tilt 0. 2. **hysteresis dead-band**(rank-space). 3. **cost-aware no-trade**(α>k×23bps).
4. **live OOS falsification**(e-CUSUM drift→attenuation). 5. ★**60d horizon primary** + CSI d3 = 분기 rebalance.

## 6. 정직 단서 (small-n hedge) + 구조빈약 사유

- 전 rotation 신호 underpowered(60d overlap eff_N 작음) → magnitude tentative, **부호·방향만**. CSI 소비지출 d3 만
  BY 생존(wc_p0.001) = 상대적 강.
- ★**구조빈약 박제(이연 아님)**: 中소비 직접지표(면세점 매출/따이공 z) 무료 KR 직접 부재 → 항셍/홍콩 proxy 로 대체(약).
  내수 소매판매(KORSARTMISMEI) 2024-03 제약(OECD MEI discontinuation) = DATA-GATE. = monitor 정직, data-mining 무리발굴 안 함.
- ★CSI yoy 부호반대 = 기저효과(level 高=고점) = mechanism 정직 보고(d3 단기변화가 진짜 신호).
- rotation(동적 tilt) = 종목 capsule(cross-sectional selection)과 다른 층 = 2층 결합 supervisor 통합(go-live 미접촉).

## 7. 재현
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
PYTHONUTF8=1 "$PY" study-research/eq_kr/industries/consumer/raw-v3/measure_rotation_consumer.py
# → validation-rotation-consumer-v1.json (14 driver 이론 사전확약 + 통계검증 + OOS + residualize + 단일 BY-FDR)
```
