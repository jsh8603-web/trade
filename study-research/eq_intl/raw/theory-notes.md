---
tags: [type/study-theory-notes, domain/inv, study/eq_intl, phase/2-2]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
phase: 2-2-theory
status: "2-2 종결 — 2-3 시계열 검증 진입 준비"
references:
  - raw/round-1.md  # frame 5 + 가설 9
  - raw/round-2.md  # BIS dollar 채널 + 검증 method 7
  - raw/round-3.md  # China decoupling 정량 (★ 환각 검증 의무 완료)
  - raw/china-cross-check.txt  # MCHI/KWEB/EMXC rolling β + multi-R² 5y 직접 재현
  - raw/analyze_china.py
  - raw/yahoo_cache/  # 22 ticker × 1255 daily (MCHI/KWEB/EMXC/ACWI 추가)
hallucination_check_result: |
  IMF Jan 2023 "MSCI China β 1.2→0.2": ★기각★ (5y 실측 MCHI β vs ACWI = 0.84~1.26, 2022-12 = 1.01)
  MS 2022-2023 "MSCI China R² 30%→10%": 부분 지지 (5y 실측 multi-R² 0.10~0.40, magnitude/timing 차이)
  AQR 2023 "KWEB DXY β ≈ 0 in 2022": ★기각★ (5y 실측 KWEB DXY β 2022-12 = -2.48, 5y mean = -1.65)
  → R3 paper 인용 정량치 환각 가능성 강함. WebSearch hook block 으로 원문 cross-check 불가.
  → H5 신뢰도 ★★★ → ★★ 하향. 가설 정의 재정의 ("β 약화" → "idiosyncratic 비중 ↑").
---

# eq_intl 2-2 theory-notes — 가격결정 원리 + 지표 관계도 + China cross-check

## §1. 가격결정 원리 (R1 frame 정독 종합)

### 1.1 핵심 등식 (International CAPM 분해)

unhedged USD ETF 의 총수익 분해:

```
R_usd(국가 i, t) = R_local(i, t) + R_fx(i→USD, t) + d_yield(i, t)

여기서:
  R_local(i,t)  = α_i + β_world,i · R_world(t) + β_local_factor · F_local(t) + ε_i(t)
  R_fx(i→USD,t) = − β_dxy,i · ΔDXY(t) + carry_i + δ_fx(t)
  d_yield       = 분기·반기 배당 (1~3%/년)
```

### 1.2 frame 별 채택 / 기각 (R1 학술)

| frame | seminal | 채택 / 기각 | 근거 |
|---|---|---|---|
| **International CAPM** | Dumas 1994, Dumas-Solnik 1995 | ✓ 채택 | unhedged ETF 분해의 base axis. global MSCI = ACWI proxy. 우리 5y 실측 EMXC β vs ACWI = 0.89 mean (일관성). |
| **Adler-Dumas FX risk** | Adler-Dumas 1995 | ✓ 채택 | unhedged ETF 환 채널 핵심. 5y H1 실측 DXY ↔ 모든 국가 ETF 음수 강확인. |
| **Market segmentation** | 2024 ScienceDirect ML | ✓ 채택 (China-한정) | 우리 5y 실측 MCHI multi-R² 0.23 vs EMXC 0.68 = china segmentation 정량 확인. |
| **Country risk premium** | Damodaran | △ 보조 | DM 에 정보 적음. EM (brazil/india/mexico) 의 country α 잔차 해석에 활용. |
| **ETF liquidity premium** | RFS 2024 Vol 37 #10 | △ 우선순위 낮음 | broad vs 단일국 ETF tier 차이는 tracking 분석 필요. 우리 수집기에 index reference data 부재. |

### 1.3 실무 frame (R2 BIS 정독)

#### BIS Quarterly Sep 2024 "US dollar and capital flows to EMEs" 핵심 frame
- **20y 구조 변화**: EM external financing = 외화 bank lending → local currency bonds/equities.
  GFC 이후 portfolio inflow > bank lending.
- **broad USD 채널 (10y importance ↑)**: USD 강세 ↔ EM local currency bond/equity flow.
  매개 = global investor risk appetite.
- **interest rate differential 축소** → EM capital flow 압박 (carry shrink).

#### BIS GLI (Global Liquidity Indicators) 활용
- 분기별, USD-denominated foreign-currency credit to non-bank EMDEs.
- end-Mar 2024 +1% (post-2y decline 종료).
- 우리 시스템 잠재 indicator: **BIS data portal 무료** → 블록6 collector_plan 추가 가치.

#### Frame 채택 결론
**eq_intl 가격결정 = "global factor (ACWI) + USD 채널 (DXY) + risk regime (VIX/HY OAS) + idio".**
fundamentals (forward E/P, ROE) 는 종속변수 (price → fundamentals 가 아니라 fundamentals 가 alpha 의
일부) — 우리 수집기 부재 시 무차원 prior 만 가능.

### 1.4 TSM 자기-modular frame (R1 AQR)

Moskowitz-Ooi-Pedersen 2012: country equity indices 포함 58 futures, 12m self-return → 1m future
의 양 predictor. AQR dataset (1985~) 가용. **H7 = TSM self-momentum** 검증 직접 입력.

## §2. 지표 의미 + 관계도

### 2.1 거시 indicator 의미 (FRED + Yahoo)

| indicator | 우리 수집기 | 의미 (eq_intl 한정) | 1차 영향 가설 |
|---|---|---|---|
| **DXY (DX-Y.NYB)** | Yahoo daily | broad USD 강도. **모든 unhedged ETF return 의 환 부분 1차 driver** | H1 dollar dominance |
| **VIX (^VIX)** | Yahoo daily | SPX 옵션 IV. **글로벌 risk regime indicator** (SPY 와 mechanical 상관 -0.76) | H2 regime amplification |
| **WTI (CL=F)** | Yahoo daily | 원자재 cycle. **terms-of-trade** (수출국 양, 수입국 음) | H4 commodity exporter oil |
| **T10Y2Y (FRED)** | fred_adapter | yield curve. **침체 신호** + global risk premium | H1/H2 conditioning |
| **BAMLH0A0HYM2 (FRED)** | fred_adapter | HY OAS. **신용 risk regime** — VIX 보다 채권 채널 직접 | H2 regime + H9 momentum crash |
| **BAA10Y (FRED)** | fred_adapter | IG credit spread. **모더리트 risk regime** | H2 risk regime conditioning |
| **STLFSI4 (FRED)** | fred_adapter | St.Louis financial stress. **종합 stress indicator** | H2 regime label |
| **(부재) DTWEXBGS** | (block6 요청) | broad USD index (trade-weighted). **DXY 보다 더 정확한 USD 강도** | H1 정밀화 |
| **(부재) DCOILWTICO** | (block6 요청) | WTI 직접 FRED 시리즈. **PIT vintage 보존** | H4 PIT 정밀화 |
| **(부재) DFII10** | (block6 요청) | 10Y real yield. **flight-to-quality 직접 측정** | H1/H2 분해 |

### 2.2 indicator 관계도 (partial correlation 우선, §8 cglasso 직결)

```
                 ┌─── (common cause) ─── US real yield ──────────────────┐
                 │                          ↓                            │
                 │                         DXY (broad USD)               │
                 │                          ↓                            │
                 │              ┌────── 직접 채널 ────┐                   │
                 ↓              ↓                     ↓                   ↓
            HY OAS        EM equity ETF       DM Europe equity ETF   carry trade
              │               ↓                     ↑                   ↓
              ↓               ↓               (terms-of-trade)        FX vol
            VIX              flow ←─── (BIS GLI) ────┘                   │
              ↑               ↑                                            │
              └── risk-on/off regime label ──── (분기 conditioning) ───────┘
```

핵심 partial-correlation (이전 블록3 v1 의 prior 갱신):

| edge | type | sign | strength | conditioning |
|---|---|---|---|---|
| DXY ↔ EM equity | common_cause (US real yield 매개) + direct | neg | **0.55** (실측 일치) | BAMLH0A0HYM2, T10Y2Y |
| DXY ↔ DM Europe | direct | neg | **0.60** (실측 강확인, DM Europe > EM) | T10Y2Y |
| HY OAS ↔ EM equity | direct (risk-off 채널) | neg | **0.50** | VIX (서로 노이즈) |
| VIX ↔ EM equity | direct (mechanical via SPY) | neg | 0.45 | HY OAS 고정 후 잔차 평가 |
| WTI ↔ commodity exporter | direct (terms-of-trade) | pos | **0.20** (5y 실측 약: brazil +0.12) | China credit impulse (block6) |
| WTI ↔ importer | direct | neg | 0.15 | (동) |
| **MCHI ↔ global factor** | **idio dominant** (R² 0.23 vs EMXC 0.68) | n/a | **idio 비중 ↑** | DXY/VIX/SPY 모두 |

### 2.3 regime conditioning

```
risk-off regime (VIX>25 OR HY OAS>400bp OR T10Y2Y<0 지속):
  - DXY↔EM coupling 증폭 (5y 실측: -0.640 → -0.796)
  - momentum (H3) 무력화 또는 반전
  - carry crash (FX vol 급등)
  - China decoupling 일시 소실 가능 (re-couple, H5b)

risk-on regime:
  - momentum (H3, H7) 활성화 (단 5y IC-IR 약함 +0.13)
  - carry trade 유리
  - DXY↔EM 약화
```

## §3. China cross-check 결과 (★ main 의무 이행)

### 3.1 원논문 cross-check 시도
- WebSearch (IMF Jan 2023 / MS / AQR paper 명) **hook research.block 차단**.
- → 원문 verification 불가. 직접 재현 으로 대체.

### 3.2 직접 재현 (Yahoo 5y daily, raw/analyze_china.py)

#### CC1: MCHI β vs ACWI (12m rolling, 47 months)
| metric | value |
|---|---|
| min | 0.84 (2025-08) |
| max | 1.26 (2025-12) |
| mean | 1.00 |
| range | 0.41 |
| 2022-12 ("IMF 0.2" 시점) | **+1.01** |
| 2026-05 | +1.01 |

→ **IMF claim "1.2 → 0.2" 강력 기각**. 실제 MCHI β vs World 는 1.0 안팎 안정. IMF Fig 2.11 의 ticker
spec / window / benchmark 가 다를 가능성 (예: World ex-China, idiosyncratic 분리 후 잔차 β 등).
WebSearch 차단으로 원문 cross-check 불가 → **MCHI=Fig 2.11 직접 매핑 의문, IMF 정량치 신뢰도 ↓**.

#### CC2: EMXC β vs ACWI (12m rolling)
| metric | value |
|---|---|
| min | 0.75 |
| max | 1.44 |
| mean | 0.89 |
| 2022-12 | +0.77 |
| 2026-05 | +1.44 |

→ EMXC β 도 안정 (0.75~1.44). MCHI 와 비슷한 변동성.

#### CC3: KWEB β vs DXY (12m rolling)
| metric | value |
|---|---|
| min | -2.48 (2022-12) |
| max | -0.37 |
| mean | **-1.65** |
| 2022-12 ("AQR ≈0" 시점) | **-2.48** |

→ **AQR claim "KWEB DXY β ≈ 0 in 2022" 강력 기각**. 12m rolling 으로 측정 시 -1 ~ -2.5 의 강한
음수 β. AQR claim 이 특정 1~2 month window 일 가능성 (12m 평활화 후 사라짐).

#### CC4: MCHI multi-factor R² (DXY+VIX+SPY)
| metric | value |
|---|---|
| min | 0.10 (2025-02 ~ 2025-03) |
| max | 0.40 |
| mean | 0.23 |
| 2022-12 ("MS 10%" 시점) | 0.24 |
| 2026-05 | 0.35 |

→ **MS claim "30%→10%" 부분 지지** (5y 측정 0.10~0.40, low end 가 10% 도달). 단 timing 차이
(MS=2022, 우리=2025). MS 의 factor set 가 우리 (DXY+VIX+SPY) 와 다를 가능성.

#### CC5: EMXC multi-factor R² (baseline 비교)
| metric | value |
|---|---|
| min | 0.60 |
| max | 0.74 |
| mean | **0.68** |

→ **MCHI R² 0.23 vs EMXC R² 0.68 = 압도적 차이 (3배)** = china 가 글로벌 macro factor 로 설명되는
비중이 EMXC 보다 훨씬 작음 → **idiosyncratic 비중 ↑**. **이게 진짜 China decoupling 의 ground truth.**

### 3.3 H5 가설 재정의 + 신뢰도 보정

#### 원 H5 (R3 기반)
- 정의: "MSCI China β vs MSCI World < MSCI EM ex-China β"
- 정량 prior: MSCI China β 1.2 → 0.2 (IMF)
- 반증: china rolling β > EM-avg 95% CI 회복

#### 직접 재현 결과
- MCHI β vs ACWI 와 EMXC β vs ACWI 가 **유사** (mean 1.00 vs 0.89) → **원 H5 정의 기각**.

#### 보정 H5
- **새 정의**: "MSCI China 의 multi-factor R² (DXY+VIX+SPY) < MSCI EM ex-China multi-R² — china 의
  idiosyncratic 비중이 EM 평균보다 훨씬 큼 (정책·지정학 driven)"
- **정량 ground truth**: MCHI R² mean **0.23** vs EMXC R² mean **0.68** (5y 직접 재현)
- **반증조건 (재정의)**: MCHI rolling multi-R² > 0.50 지속 6m+ OR EMXC R² 와 차이 < 0.15
- **신뢰도**: ★★★ → **★★** (정량 magnitude 환각 가능성 확인됨, 단 방향성·idio 비중 차이는 강확인)

### 3.4 R3 paper 인용 신뢰도 보정 표
| paper / claim | cross-check 결과 | 신뢰도 |
|---|---|---|
| IMF Jan 2023 "MCHI β 1.2→0.2" | 기각 (5y 실측 1.0 안팎 안정) | **N/A — 환각 또는 다른 spec** |
| MS 2022-2023 "MCHI R² 30%→10%" | 부분 지지 (factor set 차이 가능) | ★★ |
| AQR 2023 "KWEB DXY β ≈ 0" | 기각 (5y 실측 -1.65 mean, -2.48 in 2022) | **N/A — 환각 또는 1m window** |
| Hang Seng A-H Premium 140~150 in late 2021 | (보류, Hang Seng API 없음) | △ |
| IIF $100bn outflow in 2022 | (보류, IIF 무료 partial) | △ |

★ 결론: **R3 정량치는 신뢰도 낮음**. 단 China decoupling 의 **방향성** (idio 비중 ↑) 은 직접 재현으로
강력 지지. H5 가설은 "정의 변경 + 신뢰도 ★★" 로 살아있음.

## §4. 가설 9건 → H5 재정의 반영

| ID | 가설 | 우선순위 (재조정) | 검증 가능 |
|---|---|---|---|
| H1 | Dollar dominance | ★★★ (유지) | ✓ |
| H2 | Regime amplification | ★★★ (유지) | ✓ (이미 5y 확인) |
| **H5 (재정의)** | **China idiosyncratic dominance: MCHI R²<<EMXC R²** | **★★** (하향, 단 강확인) | ✓ (5y 0.23 vs 0.68) |
| H7 | TSM self-momentum | ★★ | ✓ (Yahoo monthly) |
| H4 | Commodity exporter oil link | ★★ | ✓ (5y 부분 부호) |
| H3 | Cross-country momentum | ★★ | ✓ (5y IC-IR 0.13 caution) |
| H9 | Country momentum crash regime | ★★ | △ (walk-forward 필요) |
| H6 | Country segmentation | ★ | △ |
| H8 | ETF liquidity tier | ★ | △ |

### 보강 가설 (R3 + cross-check)
| ID | 가설 | 정량 prior | 반증조건 |
|---|---|---|---|
| **H5a (재정의)** | em_china sub-archetype 분리 가치: MCHI multi-R² (0.23) < 0.4 OR EMXC multi-R² (0.68) > 0.55 — 두 ETF 가 다른 factor 구조 | ✓ 5y 직접 확인 | MCHI R²와 EMXC R² 의 6m 평균 차이 < 0.15 |
| H5b | Decoupling 가역성: 글로벌 동시 위기 시 MCHI R² 일시 ↑ (re-couple) | (미관측, future) | 1y 내 MCHI R² > 0.50 도달 시 reformulation |

## §5. 2-3 시계열 검증 진입 시 의무

1. **이전 5y 실측 (summary.md §5 + raw/analysis-output.txt + raw/china-cross-check.txt) 활용**:
   H1/H2/H5 1차 확인 → walk-forward OOS 적용. 추가 fetch 없이 검증 가능.
2. **walk-forward 권장 setup**: train 24m / test 1m / refit 1m (drift) OR 3m (안정).
3. **regime split**: VIX>25 binary + HY OAS>400bp binary + T10Y2Y<0 binary.
4. **block 6 신규 요청 우선순위** (main 동의받음):
   - ★★★ FRED DTWEXBGS / DCOILWTICO / DFII10 — fred_adapter.FRED_SERIES dict 3줄 추가
   - ★★★ 다국가 FxStore 확장 (BRL/JPY/EUR/INR/TWD/KRW)
   - ★★★ Hang Seng A-H Premium Index — H5 직접 지표
5. **raw/validation-{지표}.md 작성** (시계열 검증 근거 + 도표):
   - validation-h1-dollar-dominance.md
   - validation-h2-regime-amplification.md
   - validation-h5-china-idio-dominance.md (★ 재정의 후 새 가설)
   - validation-h7-tsm.md
   - validation-h4-commodity-oil.md
6. **study_session.yaml 갱신**:
   - block3 relationships prior_strength 보정 (실측 magnitude 반영)
   - block4 weight_rules base_weight 보정 (mom/oil 하향 + dollar 유지)
   - block5 confidence_hooks initial_flag (H5 ★★→★★ + H5a sub-archetype)
   - block6 collector_plan 신규 3건 추가

## §6. eq_intl 전문 애널리스트 관점 — 최종 lens

unhedged 국가지수 ETF 는 단일종목과 본질적으로 다르다. 단일종목의 가치는 미래 cash flow 의 PV
이지만, 국가지수는 **(글로벌 위험선호 × 환 채널 × archetype 별 거시 베타)** 의 곱. **눈여겨볼 것**:

1. **DXY 1순위 driver** — 모든 unhedged ETF 의 환 부분이 broad USD 방향에 종속. 5y 실측 강확인.
2. **DM Europe 이 EM 보다 dollar-sensitive** (5y 실측 + R1 Frame 일치). 통념과 반대.
3. **China 는 글로벌 factor 로 설명되지 않는 비중이 EMXC 보다 3배 많다** (R² 0.23 vs 0.68) —
   policy/geopolitical idio dominant. R3 의 "β 1.2→0.2" 같은 정량 claim 은 환각 가능성, 단 방향성은
   ground truth.
4. **momentum 은 regime 가변** — risk-on 만 활성, risk-off 시 carry crash 와 함께 무력화.
5. **fundamentals (forward E/P, ROE) 는 미수집** — 인용 시 prior 만 가능, 실측 검증은 block6 대기.

이게 2-3 시계열 검증의 전제. 다음 단계는 가설별 walk-forward 시뮬레이션으로 lens 와 가중치를 코드화.
