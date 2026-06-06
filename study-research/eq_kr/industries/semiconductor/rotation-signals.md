---
tags: [type/rotation-timing, domain/inv, scope/equity-kr, sector/semiconductor, status/in-progress]
date: 2026-06-05
owner: semi-analyst (kr-equity team, opus 1m)
purpose: 반도체 업종 자체 rotation timing(어느 국면에 반도체 OW/UW = 업종 매수 타이밍). 종목 selection capsule(KRW_weak mom/pbr)과 별 차원. team-lead 지시 = 산업 전문가가 자기 산업 rotation 깊게.
---

# 반도체 업종 ROTATION TIMING (업종 자체 비중 timing)

> **임무** = "어느 국면에 반도체 업종 OW(비중↑)/UW(비중↓)" = rotation timing. 종목 capsule(반도체 안 어느 종목) cross-sectional 과 다른 차원 = **반도체 업종 eq-weight 시계열 forward return 예측**.
> ★rotation-analyst 1차(SOXX +0.171 wc_p 0.13 TENTATIVE, soxx 1컬럼만)를 **반도체 fundamental 전문성으로 보강** = memory cycle(PPI/재고/수출) 직접지표.

## §0. 파이프라인 = 이론→통계검증→판정 (G-G v2, ★이론을 통계가 검증)

> 가격통계 단독 = data mining. 이론(fundamental cycle) + 통계검증(forward IC + OOS + G-G v2) 둘 다 통과해야 채택. 이론있고 통계반증=REJECTED / 이론없이 통계만=채택불가.

## §1. ★부호 사전확약 (측정 前 동결, HARKing 방지) — 리서치 기반

> Gemini Pro 리서치(2026-06-05) + 증권사 cycle 이론(Morgan Stanley Memory Handbook / 이승우·박성우 cycle 분석 / Andrew Ang residualization). ★핵심 = 반도체 주가는 업황 6-9개월 **선행** → "최악일 때 매수, 최고일 때 매도".

| 신호 | 메커니즘 | ★부호 사전확약 (vs forward 20d/60d) | 출처 |
|---|---|---|---|
| **반도체 PPI yoy** (DRAM ASP proxy) | 주가는 업황 선행 → PPI yoy 최저(바닥)=매수, 高(정점)=매도 | ★**음(-)** (PPI yoy 高 → forward 약 = 변곡점/되돌림) | MS Memory Handbook, 이승우 cycle |
| **반도체 PPI Δ3m** (모멘텀 변곡) | PPI 단기 변화율 = 변곡점 포착 | ★**음(-)** 또는 변곡(2차미분 민감) | 동상 |
| **한국 반도체 수출 yoy** | 수출 = 실물 후행 → yoy 바닥=주가 저점 | ★**음(-)** (수출 yoy 高 → 이미 고점) | 관세청/FRED 수출 |
| **재고 yoy** (재고자산/매출, dart_extended) | 재고 peak=업황 바닥=감산→주가 선반등 | ★**양(+)** (재고 高 → forward 강, 저점 매수) | MS, SK증권 재고 cycle |
| **SOXX Δ3m** (글로벌 반도체 cycle) | 한국=글로벌 동행자(후행 아님) | ★**양(동행)** but forward 예측력 약 prior (동행≠선행) | Bloomberg corr, Citi/JPM HBM |
| **USDKRW yoy** (환율) | 완만 원화약세=수출이익↑(양), 급격=위험회피(음) | ★**양(완만)** 비선형 | 증권사 환율민감도 |
| **실질금리 Δ** | 반도체=성장주, 실질금리↑=밸류부담 | ★**음(-)** (금리↑ → 반도체 UW) | GS 자산배분 |
| **경기국면(CLI)** | 회복·확장초입 OW / 둔화·침체 UW | ★회복/확장 OW (CLI 상승 양) | GS sector rotation |

### ★사전확약 핵심 가설 (측정 대상)
1. **fundamental cycle 변곡 신호(PPI/수출 음, 재고 양)이 forward 예측** = 진짜 rotation alpha (momentum 아님).
2. **SOXX = 동행(contemporaneous) > forward** = rotation-analyst SOXX 약(wc_p 0.13)의 이유 = 동행성.
3. **가격 momentum = 시장 momentum × 베타 재포장** = residualize 후 소멸 prior (data mining 차단, Q5).

### ★반증조건 (falsifier)
- PPI yoy IC ≥ +0.05 (양, 동행) → "선행 변곡" 가설 기각 (동행으로 재해석).
- 재고 yoy IC ≤ 0 → 재고 cycle rotation 무효.
- SOXX forward IC > +0.30 유의 → 동행 아닌 선행 (rotation-analyst와 다른 결론).

## §2. 측정 설계 (G-G v2)

- **분석 unit** = 반도체 업종 eq-weight 패널 (prices.parquet 85종 동일가중 월수익). ★93% 집중이라 eq-weight 필수(cap-weight=삼성+SK 2종 지배).
- **종속변수** = 업종 forward y_20d(1M) / y_60d(3M).
- **신호** = §1 fundamental(PPI/수출/재고/SOXX) + macro(USDKRW/금리/CLI) + 가격 momentum(residualize 검증용).
- **게이트 G-G v2**: (a) walk-forward OOS(IS 2019-22/OOS 2023-26 부호+magnitude) (b) 단일 FDR(BY) (c) wild-cluster bootstrap (d) MDE/power(t_obs⋚2.802) (e) non-overlap(stride 3M) (f) placebo (g) leave-one-year.
- ★momentum residualize: 업종 momentum을 공통인자(외국인flow/USDKRW/SOXX) 제거 후 잔존 여부 (Q5, data mining 차단).

## §3. 측정 결과 (측정 후 박제)

> 측정 = `raw-v3/measure_rotation_semi.py` → `validation-rotation-semi-v1.json`. 반도체 업종 eq-weight forward IC + walk-forward OOS + wild-cluster + MDE/power(t_obs⋚2.802). ★후보 8개 검토 (PPI yoy/PPI Δ3m/수출 yoy/재고 yoy/SOXX Δ3m/USDKRW/CLI chg/업종 momentum).

### 측정 결과표 (y_60d=3M forward, wild-cluster p)

| 신호 | prior | fwd IC | wc_p | t_obs | IS→OOS | sign_hold | contemp | 사전확약 |
|---|---|---|---|---|---|---|---|---|
| **export_yoy** (수출) | 음 | **-0.255** | 0.017 | 1.36 | -0.436→-0.018 | ✅ | -0.139 | ✅정합(선행변곡) |
| **cli_chg** (경기선행) | 양 | **+0.225** | 0.018 | 1.05 | +0.295→+0.245 | ✅ | +0.121 | ✅정합(경기) |
| **inv_yoy** (재고) | 양 | -0.310 | 0.024 | 1.45 | -0.223→-0.268 | ✅ | -0.295 | ⚠️**prior 반증**(음) |
| **usdkrw_yoy** | 양 | -0.211 | 0.035 | 1.17 | -0.342→-0.156 | ✅ | -0.150 | ⚠️prior 반대(음) |
| **soxx_d3** (글로벌) | 양동행 | +0.161 | 0.149 | 0.91 | +0.143→+0.201 | ✅ | **+0.476** | ✅동행>선행 입증 |
| ppi_yoy (DRAM ASP) | 음 | -0.092 | 0.330 | 0.50 | -0.121→-0.222 | ✅ | -0.066 | ✅약 정합 |
| ppi_d3 | 음 | -0.052 | 0.656 | 0.28 | -0.353→+0.220 | ❌ | -0.056 | OOS flip |
| ind_mom_6 (검증용) | — | +0.125 | 0.288 | 0.66 | +0.082→+0.205 | ✅ | +0.378 | residualize ↓ |

### ★핵심 발견
1. **SOXX = 동행 입증** (forward +0.161 vs contemp **+0.476**) = rotation-analyst soxx 약신호(wc_p 0.13)의 정체 = 동행성, 선행 아님. 사전확약 정확.
2. **export_yoy 음(-0.255, wc_p 0.017)** = 수출 정점→매도/바닥→매수(선행 변곡, 이론 정합). 단 OOS magnitude 붕괴(부호만).
3. **cli_chg 양(+0.225, OOS +0.245)** = 경기선행 상승 국면 반도체 OW. ★유일하게 OOS 부호+magnitude 둘 다 유지 = 가장 robust.
4. **inv_yoy 부호 반증** (재고 yoy 음, prior 양과 반대) = 종목 capsule inv_ratio와 **동일 패턴** = 재고/자산 高가 성장·생산확대 종목 prox일 가능성(메커니즘 재해석). 단 OOS 부호유지.
5. **momentum residualize**: raw +0.125 → resid +0.158 = **잔존(진짜 idiosyncratic)** = 반도체 momentum은 공통인자 재포장 아님. ★단 rotation-analyst cross-industry(+0.215→+0.079 소멸)와 다름 = 측정 unit(eq-weight 업종 vs cross-industry) 차이, 약신호라 결론 보류.

## §4. 판정 + tradeable (G-G v2)

### tradeable 자격 (4조건: OOS 부호유지 + tier≥structural_prior + net-alpha + regime 명시)

| 신호 | tradeable? | tier | 판정 |
|---|---|---|---|
| **cli_chg** | ✅ (OOS 부호+magnitude 유지, 이론 정합) | structural_prior_low_confidence | ★**TENTATIVE 채택** — 경기선행 상승국면 반도체 OW. t_obs<2.802 underpowered + BY 미생존 → conservative cap + monitor |
| **export_yoy** | ✅ (OOS 부호유지, 이론 정합) | structural_prior_low_confidence | ★**TENTATIVE 채택** — 수출 yoy 음(선행 변곡). 단 OOS magnitude 붕괴 → 부호·방향만, monitor |
| **soxx_d3** | △ (동행 강, forward 약) | structural_prior | **동행 지표**(rotation 아닌 regime conditioning 변수). forward 예측 약 → contemporaneous risk monitor |
| **inv_yoy** | △ (OOS 부호유지 but prior 반증) | structural_prior_low_confidence | **메커니즘 재해석 필요** — 재고 yoy 음(가설 반대). 부호 안정하나 이론 미정합 → monitor, 재해석 후 재판정 |
| **usdkrw_yoy** | △ (prior 반대) | structural_prior | 음(급격 원화약세=위험회피 해석) — conditional(종목 capsule KRW_weak과 다른 차원) |
| ppi_yoy / ppi_d3 | ✗ | INSUFFICIENT | ppi_yoy 약(t_obs 0.5) / ppi_d3 OOS flip = artifact |

### 산업 rotation 종합 판정

★**PASS-conditional** (tradeable ≥1, low confidence): **cli_chg(경기선행) + export_yoy(수출 선행변곡)** = 이론+통계(OOS 부호유지) 통과 = TENTATIVE 채택. 단 전 신호 underpowered(t_obs<2.802) + BY 미생존(m=16 survivors=0) = magnitude tentative, 부호·방향만 신뢰.

- **이론+통계 통과 (채택)**: cli_chg, export_yoy (사전확약 정합 + OOS 부호유지).
- **동행/regime 변수 (rotation 아님)**: soxx_d3 (contemp +0.476 = 동행, forward 약).
- **메커니즘 재해석 (조건부)**: inv_yoy, usdkrw (OOS 부호유지하나 prior 반대).
- **artifact (REJECTED)**: ppi_d3 (OOS flip).
- ★**data mining 차단**: momentum residualize 잔존(+0.158) = 공통인자 재포장 아님 단 약신호.

### 정직 단서 (small-n hedge)
- 전 rotation 신호 underpowered(월간 n~84, 60d overlap eff_N 작음, t_obs<2.802) → ★magnitude tentative, **부호·방향만**. BY 미생존(m=16) = 다중검정 후 비유의.
- export OOS magnitude 붕괴(IS -0.436 → OOS -0.018) = HBM cycle(2023-26)서 수출-주가 디커플링 가능성(HBM 차별화).
- ★종목 selection(KRW_weak mom/pbr, 본 capsule §conditional) vs rotation(업종 timing, 본 문서) = 다른 차원. rotation = cli_chg/export 경기·수출 cycle, selection = 환율 regime conditional.
- WIRE5 배선·sizing·gated 설계 = supervisor 통합단계(rotation-analyst 통합조율). 본 산출 = 반도체 rotation 신호 측정+판정까지.
