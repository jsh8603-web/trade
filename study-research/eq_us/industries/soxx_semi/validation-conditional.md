---
tags: [type/validation-conditional, domain/equity-us, sector/soxx_semi, phase/sector-granular]
date: 2026-06-08
purpose: SOXX 반도체 conditional IC surface — 한국 conditional_ic_surface 양식 복제. IC(지표×regime×horizon) + family-2 interaction + walk-forward OOS. ★unconditional 단일 horizon 누락 보완.
source: raw-v3/measure_conditional.py → validation-conditional-v1.json (재현 가능)
verdict: ★FREEZE 철회 — conditional×horizon×family-2×OOS 로 value/low_vol 살아남. (D) granular 부분 정당(TENTATIVE).
---

# SOXX 반도체 — conditional IC surface (지표×regime×horizon)

> ★결론 선언: **FREEZE 철회**. R3 unconditional 단일 horizon(y_20d)에서 약했던 신호가 **y_60d + regime conditional +
> family-2 interaction + walk-forward OOS** 로 살아남. (a) **value** = y_60d +0.104(wc_p 0) + rate-extreme conditional +
> OOS +0.085 robust (b) **low_vol(BAB)** = y_60d −0.118(wc_p 0) + credit_high conditional + OOS −0.071 robust = ★새 발견.
> = team-lead 지적("통짜로 죽은 신호가 regime×horizon으로 살아난다") **실증 재현**. (D) granular 부분 정당.
> ★tier = TENTATIVE (생존편향 I축 PARTIAL + overlapping horizon inflation 주의). 점추정 박제금지(CI+wc_p+n+OOS).

## §0. ★데이터 라벨 정정 (E축, spec↔code match)

- ★**round-1 "실질금리 DFII10" = 데이터 라벨 오류**. macro.parquet `rate10y` 컬럼 실값 = **0.52~4.98, 음수 0개** =
  **nominal 10y Treasury(DGS10)**, NOT DFII10(실질 TIPS, 2015-21 음수 다수). regime 축 해석 = "nominal 금리 국면"
  (valuation 압박 proxy 로는 유효하나 "실질금리 duration" 메커니즘 라벨은 부정확). ★R4 summary 에 정정 박제 + DFII10 재fetch 시 재측정.
- credit = `baa_aaa`(Baa-Aaa, 0.51~1.70 정상) ✅. HY OAS(2023-05~ 37mo)는 단기라 baa_aaa 채택.

## §1. ★unconditional × horizon (★단일 horizon 누락 보완 = 핵심)

| 지표 | y_5d | y_20d | y_60d | horizon 구조 |
|---|---|---|---|---|
| **value** | +0.032 (wc_p 0.004) | +0.068 (wc_p 0.002) | ★**+0.104** (wc_p 0.0, CI[0.054,0.154]) | ★**단조 증가** = 장기 horizon value premium. y_60d MDE 0.107 근접 통과 |
| quality (ROIC) | +0.014 (0.225) | +0.016 (0.405) | +0.009 (0.709) | ★전 horizon 무신호 |
| mom_12_1 | +0.034 (0.027) | +0.027 (0.25) | +0.022 (0.423) | y_5d만 약 유의(단기), 장기 감쇠 |
| rev_1m | +0.000 (0.99) | −0.000 (0.99) | **−0.060** (wc_p 0.002) | ★y_60d 장기 reversal(음) |
| **low_vol (BAB)** | −0.049 (wc_p 0.0) | −0.075 (wc_p 0.001) | ★**−0.118** (wc_p 0.0, CI[−0.169,−0.064]) | ★**단조 강화** = BAB 작동(저변동→fwd+). 강신호 |

★**핵심**: R3 가 본 y_20d unconditional 만으론 value(+0.068) 약·결합 희석으로 freeze 보였으나, **y_60d 로 보면 value +0.104,
low_vol −0.118** 명확 발현. ★단일 horizon 누락이 freeze 오판 원인. ⚠️ y_60d overlapping = 자기상관 inflation 주의(eff_N 보정).

## §2. conditional: regime × 지표 (y_20d, tercile)

### rate regime (nominal 10y tercile)
| 지표 | rate_low | rate_mid | rate_high | 패턴 |
|---|---|---|---|---|
| **value** | +0.103 (wc_p 0.0) | −0.004 (0.917) | +0.105 (wc_p 0.001) | ★**U자**: rate 극단(고/저)서 value 증폭, mid 소멸 |
| low_vol | −0.106 (0.003) | −0.007 (0.853) | −0.112 (0.006) | ★동일 U자 (극단 regime서 BAB 강) |
| mom_12_1 | −0.024 (0.48) | +0.032 (0.47) | +0.071 (0.078) | rate_high서 momentum 발현 근접 |
| quality | +0.025 | +0.015 | +0.008 | 전 regime 무신호 |
| rev_1m | −0.033 | +0.024 | +0.009 | 비유의 |

### credit regime (Baa-Aaa tercile)
| 지표 | credit_low | credit_mid | credit_high | 패턴 |
|---|---|---|---|---|
| value | +0.086 (0.029) | +0.052 (0.119) | +0.066 (0.023) | credit 무관 비교적 안정(main effect) |
| quality | +0.092 (0.01) | −0.039 (0.219) | −0.002 (0.94) | ★credit_low(양호)서만 quality 발현 |
| low_vol | −0.056 (0.179) | −0.052 (0.265) | ★**−0.117** (0.001) | ★credit_high(스트레스)서 BAB 강화 |
| rev_1m | +0.013 | −0.066 (0.017) | +0.055 (0.105) | credit_mid 단기 reversal |

## §3. ★family-2 interaction (signal × regime_high dummy, pooled panel, day-clustered)

| 지표 | rate_high b_inter (t) | credit_high b_inter (t) | 판정 |
|---|---|---|---|
| **value** | **+0.059 (t=4.61)** | −0.001 (t=−0.11) | ★rate_high서 value 증폭 유의 (main t=6.66 강) |
| **mom_12_1** | **+0.069 (t=4.48)** | +0.033 (t=2.07) | ★rate_high서 momentum 발현(uncond 비유의 → conditional 유의) |
| **low_vol** | −0.056 (t=−3.73) | **−0.064 (t=−4.21)** | ★rate·credit 극단서 BAB 강화 |
| **rev_1m** | +0.013 (t=0.92) | **+0.082 (t=5.82)** | ★credit_high서 단기 reversal 발현 |
| quality | −0.011 (t=−0.9) | −0.023 (t=−1.86) | interaction 비유의 (main만 약) |

★**해석**: value·mom_12_1·low_vol·rev_1m = main effect 약/비유의여도 **interaction 유의** = "국면 따라 신호 발현"(한국 frame A-5
동형). unconditional 약신호가 conditional 로 명확. ★quality 만 interaction 도 비유의 = 진짜 무신호.

## §4. ★walk-forward OOS (y_20d, IS 2015-2021 / OOS 2022-2026)

| 지표 | IS IC | OOS IC | OOS wc_p | 판정 |
|---|---|---|---|---|
| **value** | +0.057 | **+0.085** | 0.019 | ★**부호+magnitude 유지(강화)** = in-sample artifact 아님 |
| **low_vol** | −0.077 | **−0.071** | 0.10 | ★**부호+magnitude 유지** (OOS wc_p 0.10 경계) |
| mom_12_1 | −0.012 | +0.080 | 0.042 | ★**IS/OOS 부호 반전**(IS 음↔OOS 양) = unstable, conditional only |
| quality | +0.020 | +0.009 | 0.79 | 무신호 유지(IS/OOS 일관 무) |
| rev_1m | −0.016 | +0.024 | 0.46 | 부호 반전, 비유의 |

## §5. ★freeze 재판정 (GUIDE §10.7, conditional surface 전체 본 뒤)

| 지표 | unconditional | conditional(regime×horizon) | family-2 | OOS | ★종합 |
|---|---|---|---|---|---|
| **value** | y_60d +0.104 ✅ | rate-extreme U자 ✅ | rate_high t=4.61 ✅ | +0.085 robust ✅ | ★**살아남 (D 정당)** |
| **low_vol(BAB)** | y_60d −0.118 ✅ | credit_high ✅ | t=−4.21 ✅ | −0.071 robust ✅ | ★**살아남 (신규 발견)** |
| mom_12_1 | y_5d 약 | rate_high conditional | t=4.48 ✅ | ★OOS 부호반전 ✗ | conditional only, unstable |
| rev_1m | y_60d −0.060 | credit_high | t=5.82 ✅ | 부호반전 ✗ | conditional/단기, OOS 약 |
| quality | 무 | 무 | 비유의 | 무 | ★진짜 무신호 |

→ ★**FREEZE 철회**: value + low_vol 가 conditional×horizon×OOS 로 robust = (D) granular **부분 정당**. R3 unconditional 단일
horizon freeze 는 **측정 축 부족(horizon 누락) 오판**. ★단:
- **tier = TENTATIVE** (CONFIRMED 금지): (a) I 생존편향 PARTIAL(현 holdings, MRVL/NXPI 누락, historical 무료부재)
  (b) ★y_60d overlapping 자기상관 inflation(eff_N 보정했으나 한국 24M degenerate 전례 = magnitude hedge) (c) ★FDR 미보정
  (지표 5 × regime 6 × horizon 3 + family-2 = 다중검정 R4 BY 의무).
- ★value·low_vol = **방향·존재 tentative 확인**, magnitude 는 hedge.

## §5-bis. ★R4 보정 (FDR BY + overlapping + AI episode, tier 확정)

> team-lead R4 지시 4 보정. ★#3 DFII10 재fetch = sandbox 네트워크 timeout(fredgraph/stooq/FRED data page 모두 실패)
> → **data-gate 등록**, rate10y=nominal 유지 + 라벨 정직. 나머지 3 보정 완수. source=raw-v3/validation-r4-corrections.json.

### §5-bis.1 ★overlapping 자기상관 보정 (Newey-West HAC, lag=horizon)
| 지표 | y_20d NW_t | y_60d NW_t | 판정 |
|---|---|---|---|
| **value** | **+3.24** | **+2.73** | ★보정 후 유의 유지 (eff_N 겹침보정 y60d=46.8) |
| **low_vol** | **−3.11** | **−2.83** | ★보정 후 유의 유지 |
| quality | +0.78 | +0.24 | 비유의(일관) |
| mom_12_1 | +1.11 | +0.55 | 비유의 |
| rev_1m | −0.01 | **−2.52** | y_60d만 유의(장기 reversal) |
→ ★**value·low_vol unconditional = NW-HAC overlapping 보정 후도 유의** (t>2.7). magnitude robust.

### §5-bis.2 ★family-2 interaction overlapping 보정 (60d block-cluster)
| interaction | day-cluster t (§3) | ★60d block-cluster t | 판정 |
|---|---|---|---|
| value × rate_high | 4.61 | **1.31** | ★**붕괴 → 비유의** (day-cluster 가 overlap 미흡, t 부풀림) |
| mom_12_1 × rate_high | 4.48 | **1.38** | ★붕괴 비유의 |
| low_vol × credit_high | −4.21 | **−1.42** | ★붕괴 비유의 |
| rev_1m × credit_high | 5.82 | **2.07** | 유의 유지(유일) |
→ ★**중대 정정**: §3 family-2 t(4~6)는 day-clustering 이 60d overlapping 자기상관 미흡 = **t 부풀림 artifact**. 60d
block-cluster 보정 시 value/mom/low_vol interaction **모두 비유의**(rev_1m만 생존). = ★"regime conditional 증폭"은 약화 =
conditional 효과는 TENTATIVE. ★단 unconditional value/low_vol 은 §5-bis.1 NW-HAC 유의 = main effect 는 robust.

### §5-bis.3 ★FDR BY 보정 (Benjamini-Yekutieli, 45셀, q=0.10)
- m=45, c(m)=4.39 (의존성 보정), 우연 기대 45×0.05≈2.3. → ★**10셀 생존**:
  - value: rate_low(p=0) / rate_high(0.001) / uncond y60(0.001) / uncond y20(0.002)
  - low_vol: uncond y60(0) / y5(0.001) / credit_high(0.001) / y20(0.002) / rate_high(0.004)
  - rev_1m: uncond y60(0.004)
→ ★**value·low_vol = BY 생존**(우연 아님). quality·mom = 미생존(전 셀). ★M_eff 미통합(보수적 naive m).

### §5-bis.4 ★AI capex episode 교란 점검 (pre-AI 2015-2022 vs AI 2023-2026)
| regime cell | pre-AI 2015-2022 | AI 2023-2026 | 판정 |
|---|---|---|---|
| value rate_low | IC=0.104 (n=958, p=0.003) | n=0 | ★rate_low=거의 전부 pre-AI → value **pre-AI robust** |
| value rate_mid | IC=−0.004 (p=0.93) | n=0 | 무신호(일관) |
| value rate_high | IC=0.057 (n=103, p=0.58 비유의) | IC=0.111 (n=833, p=0.008) | ★rate_high=거의 AI 시기 → **AI episode 의존 의심** |
| low_vol credit_high | IC=−0.080 (p=0.082) | IC=−0.229 (p=0.0) | AI 강하나 pre-AI 방향 유지(약) |
→ ★**해석**: value premium 은 **pre-AI(rate_low p=0.003) + AI(rate_high p=0.008) 양 시기 발현** = episode-specific regime
분리되나 value 자체는 **pre·post robust**(AI 단일 artifact 아님). 단 ★"rate_high 증폭"은 AI 시기 한정 = U자 high 다리는
AI episode 의존. low_vol = AI 강화나 pre-AI 방향 유지.

### §5-bis.5 ★tier 재판정 (R4 보정 후)
- **value (unconditional)** = NW-HAC y20 t=3.24/y60 t=2.73 + BY 생존 + pre-AI(rate_low p=0.003) robust → ★**PARTIAL_CONFIRMED**
  (단 생존편향 I축 PARTIAL = CONFIRMED 불가).
- **low_vol/BAB (unconditional)** = NW-HAC t=−2.8~−3.1 + BY 생존 + pre-AI 방향유지 → ★**PARTIAL_CONFIRMED** (생존편향 상한).
- **conditional (family-2 regime 증폭)** = ★overlapping block-cluster 보정 후 비유의(붕괴) → **TENTATIVE/격하** (rev_1m만 잔존).
  rate_high 증폭 = AI episode 의존. = ★"regime conditional 증폭" over-claim 금지.
- quality·mom = REJECTED/무신호.

## §6. 한계 (hard-fail 축 self-check)

- **I 생존편향 PARTIAL**: 현 12종 holdings only → TENTATIVE 상한.
- **D PIT PASS**: EDGAR 최초 filed + forward shift. regime(macro)도 ffill PIT.
- **B/C PASS**: 합성 0%, validation-conditional-v1.json 매핑.
- ★**K 다중검정 미보정**: 셀 45 + family-2 10 = R4 단일 FDR family BY 의무(현 raw wc_p). garden-of-forking-paths 주의.
- ★**overlapping horizon**: y_60d = 60거래일 overlap → 자기상관 강, eff_N 보정 적용했으나 magnitude inflation 잔존(hedge).
- ★**data 라벨**: rate10y = nominal(NOT DFII10 실질). regime 해석 = nominal 금리 국면(R4 정정 + DFII10 재fetch 의제).
