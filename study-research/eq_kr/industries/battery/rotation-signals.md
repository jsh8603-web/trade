---
tags: [type/rotation-signals, domain/equity, sector/battery, scope/equity-kr]
date: 2026-06-06
purpose: 2차전지 업종 자체 rotation timing (어느 국면→배터리 OW/UW). 이론→통계검증→판정. 종목selection(summary.yaml conditional_ic) 위 차원.
owner: bat-analyst (kr-equity team, opus 1m)
---

# battery(2차전지) 업종 ROTATION 신호

> ★측정 = "어느 국면 → 2차전지 업종 비중↑↓" = 업종 eq-weight forward return 예측 (종목 cross-section 아님).
> 파이프라인 = **이론(증권사)→통계검증(forward IC+OOS+G-G)→판정**. 가격통계 단독 = data mining 채택불가.
> baseline = rotation-analyst v2(`_rotation/validation-rotation-v2.json`, lithium_yoy +0.274). 본 capsule = ★universe 오염 검증 + 이론검증 + driver 심화.

## §0. ★universe 오염 검증 (refine-analyst CRITICAL 대응)

> refine-analyst 가 v2 가 디렉토리 전체 prices.parquet 패널 사용 → 부수종목 오염 적발(정유 crack = 가스 9종 오염). ★battery 동일 체크.

### strict 화이트리스트 정의 (29종 → 19 strict)
- **포함 19종 (진짜 2차전지 셀/소재/장비, EV Li-ion)**: LG엔솔·삼성SDI·LG화학(셀) / 포스코퓨처엠·에코프로비엠·에코프로·에코프로머티·엘앤에프·코스모신소재·피노(양극/전구체) / 대주전자재료(음극) / SKIET·WCP(분리막) / 엔켐·천보(전해질) / SKC(동박) / 피엔티·에스에프에이·씨아이에스(장비).
- **제외 10종 (오염 후보)**: 포스코인터내셔널(가스trading) / 두산(전자·IT·지게차) / 두산퓨얼셀(연료전지) / 비츠로셀(리튬1차전지) / 세방전지(연축전지 lead-acid) / 신성이엔지(태양전지) / 인텍플러스(반도체 검사장비) / 솔브레인홀딩스(지주) / 비나텍(슈퍼커패시터) / DN오토모티브(자동차 일반배터리).

### ★검증 결과 = NO 오염 (steel 동형, refining 과 반대)
| universe | n종목 | rho (y_60d) | OOS IS→OOS | eligible |
|---|---|---|---|---|
| v2 전체 29종 | 29 | +0.274 | +0.23→+0.46 | ✅ |
| **STRICT 19종** | 19 | **+0.285** | +0.20→+0.36 | ✅ |
| **CORE 8 (셀+양극)** | 8 | **+0.338 (강화)** | +0.18→+0.39 | ✅ |
| 제외 10종만 | 10 | +0.141 (약화) | +0.09→+0.49 | ✅ |

- ★**결론 = 오염 없음**. STRICT(+0.285) ≈ v2(+0.274), CORE 셀+양극(+0.338) **강화**. 제외 10종만 = rho 약화(+0.141) = 부수종목이 신호를 **희석**(생성 X).
- = refining(부수종목이 신호 생성)과 **반대**. 이론 정합: 양극재 makers(리튬 원가 60-70%)가 리튬 민감도 최고 → strict 화이트리스트일수록 신호 강화 = 진짜 2차전지 신호.
- ★측정 채택 = **STRICT 19종 패널**(부수종목 제거, 신호 보존). 이하 §3 = STRICT 패널 기준.

## §1. 부호 사전확약 (★측정 前 이론 동결)

| 신호 | 부호 사전확약 | 메커니즘 (증권사 이론) | 출처 |
|---|---|---|---|
| **리튬 price yoy** | ★**양(+)** | 리튬↑→양극재/셀 판가연동(cost pass-through)+재고평가이익(래깅), 3-6M lag. 리튬↓=역래깅 손실(2023 실적악화). 변곡점=1-2분기 후 실적+주가 6M 선반영 | KB증권 2023.10 / 신한투자 2023.11 / 삼성증권 2024.01 |
| 니켈/코발트 yoy | 양(+) | NCM 양극재 = 리튬 동일 메커니즘(판가연동+재고평가) | 증권사 종합 |
| 전기차 침투율/판매 | 양(+) 약 | 구조성장(장기 Q변수) > 단기 timing. 침투율 둔화 우려시 업종 밸류 하락 | 하나증권 2024.02 |
| 중국 EV | 양(+) | 전방 EV 수요 시그널(글로벌 배터리 cycle) | 증권사 종합 |
| IRA/FEOC 정책 | 양(+) event | 중국배제 구조적 해자(moat)→밸류 프리미엄. 정량 cross-sectional 신호 아님(event) | 키움증권 2023.08 |
| USDKRW 환율 | 음(-) 가설 | 수출주 베타이나 ★공통 macro(전 산업 동일) = rotation 아닌 시장 timing 의심 | — |
| 업종 self-momentum | 양(+) 약 | continuation 가능하나 ★공통인자(외국인flow×beta) 재포장 의심 = data mining 위험 | 자문 A |

- ★**핵심 가설**: 리튬/cathode-metal cycle = 2차전지 rotation 진짜 driver(fundamental). momentum/환율 = 공통인자 재포장 의심(검증 대상).
- ★증권사 nuance(부호 정밀화): "리튬 **바닥→완만 상승 전환**"이 최강(역래깅 종료+래깅 시작=실적 턴어라운드). 급등 cost-push = 단기 부정 가능. → yoy 가 변곡 포착하나 급등/급락 비대칭 미분리(후속).

## §2. 측정 설계 (G-G v2)

- **분석 unit** = STRICT 19종 eq-weight 월수익 패널 forward (종목 cross-section 아님).
- **종속변수** = 업종 패널 cumulative return y_20d(1M) / y_60d(3M 본진).
- **신호** = driver yoy(12M pct_change) → forward Spearman IC.
- **게이트** = wild-cluster bootstrap p + walk-forward OOS(IS<2023-01 / OOS≥2023-01, 부호+magnitude≥0.5×IS) + t_power_mde(≷2.802) + leave-2022-out.
- **데이터** = LIT/ALB/REMX/NIO/TSLA/DRIV/BATT/XLB = yfinance(source 사전검증 history(period=max)) / usdkrw = regime_series. ★리튬 LIT = ETF proxy(실 carbonate spot 아님) → ALB(순수 리튬광산)로 보강.

## §3. ★측정표 (STRICT19 패널, y_60d 본진, ★후보 10개 전수)

| 후보 driver | rho | IS→OOS | eligible | type | 이론 |
|---|---|---|---|---|---|
| **LIT_yoy (리튬/배터리)** | +0.285 | +0.20→+0.36 | ✅ | primary cycle | 판가연동+재고평가 |
| **ALB_yoy (리튬 pure-play)** | +0.281 | +0.12→+0.35 | ✅ | primary cycle | ★순수 리튬광산 확인 |
| **REMX_yoy (니켈/코발트)** | +0.220 | +0.07→+0.37 | ✅ | NCM metal | 삼원계 양극재 |
| **NIO_yoy (중국 EV)** | +0.250 | +0.25→+0.27 | ✅ | EV 수요 | 전방 수요 시그널 |
| BATT_yoy (배터리 ETF) | +0.122 | +0.02→+0.24 | ✅ | 광의 cycle | 배터리 산업 |
| self_mom_3 (업종 momentum) | +0.198 | +0.06→+0.31 | ✅ | momentum(2차) | ★공통인자 재포장 의심 |
| TSLA_yoy (테슬라) | +0.265 | +0.41→-0.04 | ❌ flip | EV 단일명 | OOS 붕괴(fragile) |
| DRIV_yoy (EV ETF) | +0.151 | +0.17→+0.04 | ❌ | EV 광의 | 침투율=구조성장>timing |
| usdkrw_yoy (환율) | -0.274 | -0.41→-0.01 | ❌ | macro 공통 | ★시장 timing(rotation 아님) |
| XLB_yoy (광의소재) = ★control | -0.131 | +0.08→-0.52 | ❌ flip | control | ★specificity 검증 실패=정상 |

- ★**후보 = 10개 전수 검토 / tradeable(eligible) = 6개** (≥2 충족).
- ★**control(XLB) 실패 = specificity 입증**: 광의 소재섹터는 부호반대+OOS flip = battery 신호가 generic 소재베타 아님.

### ★multi-source 수렴 (리튬 cycle = 진짜 driver)
- 리튬/cathode-metal 직접 proxy **3종(LIT +0.285 / ALB +0.281 / REMX +0.220) 전부 eligible 양** = 단일 LIT proxy 의존 아님. ALB(순수 리튬광산)도 한국 배터리 업종 예측 = 리튬 cycle 본질.
- NIO(중국EV +0.250) = 수요측 확인. = primary(공급측 리튬) + demand(중국EV) 양면 정합.

### ★momentum = data mining 검증 (자문 A)
- self_mom_3 eligible(+0.198)이나 rotation-analyst residualize(공통인자 d_usdkrw/foreign/semi_ppi 제거) 후 battery momentum = **소멸**(market×beta) = 공통인자 재포장. ★리튬은 momentum 아닌 fundamental cycle 직접신호 = **잔존** → primary 채택, momentum 강등.

## §4. 판정 + S5 역공격

### ★S5 역공격 (2022 리튬붕괴 episode 종속?)
| 반증 | test | 결과 | verdict |
|---|---|---|---|
| 2022 리튬 hyper-cycle 붕괴 종속? | leave-2022-out rho | full +0.274 → ex-2022 +0.337(강화) | ★기각 — 2022 제거시 강화 |
| 가격 momentum 재포장? | residualize 소멸 | 리튬 cycle 직접신호 잔존 | ★기각 — fundamental cycle |
| universe 오염(부수종목)? | STRICT vs 전체 | STRICT 강화(+0.285), 제외종목 약화 | ★기각 — 오염 없음(steel 동형) |

### ★최종 판정
- ★**battery rotation = STRONG (tentative, underpowered)**. primary = **lithium_yoy** rho +0.285(STRICT), wc_p≈0.01, y_60d, OOS+0.36~0.46 강화 eligible.
- **이론+통계 둘 다 채택**: 증권사 cost pass-through+재고평가+선행지표 이론 + multi-source(LIT/ALB/REMX/NIO) 수렴 + XLB control 실패 + leave-2022-out 강화 + 오염 없음.
- **tradeable 신호 ≥2 충족** = lithium(LIT/ALB) primary + 니켈코발트(REMX) + 중국EV(NIO) = 4 robust + BATT/self_mom 2 보조 = **6 eligible**.
- **강등**: momentum(공통인자 재포장) / 환율(시장 timing) / TSLA·DRIV(OOS 약화).
- **y_20d(1M) 비유의** = cycle 분기 lag(3-6M) 메커니즘 정합 = 60d/3M 본진.

### ★gated 설계 (over-trade 차단)
- underpowered(t_power 1.5 < 2.802) → **default weight 0** + hysteresis dead-band + cost-aware no-trade(α > k×23bps) + live e-CUSUM falsification.
- rotation tilt(동적) = static PCA sleeve(plan §8)와 **결합** = 2층. sizing·WIRE = supervisor(go-live 미접촉).

### ★정직 단서 (small-n hedge)
- 전 신호 underpowered(60d overlap eff_N 29.8) → **magnitude tentative, 부호·방향만**.
- 리튬 LIT = ETF proxy(배터리tech 혼합), ALB(순수 리튬광산)로 보강. 실 리튬 carbonate spot(Trading Economics 유료) = collector_plan.
- 급등 cost-push 비대칭(증권사 nuance) = level yoy 변곡 포착하나 급등/급락 미분리 = 후속.
- IRA/FEOC = event(정량 cross-sectional 신호 아님) = 정성 prob~0.3 / EV 침투율 = 구조성장(timing 약).

## §5. 재현
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
cd study-research/eq_kr/industries/_rotation
"$PY" measure_rotation_v2.py   # v2 baseline (battery lithium_yoy +0.274)
# STRICT 화이트리스트 재현 + driver 10 sweep = 본 capsule 측정 (summary.yaml rotation_signal source)
```
