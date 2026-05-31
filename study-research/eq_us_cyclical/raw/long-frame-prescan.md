---
tags: [type/prescan, study/eq_us_cyclical, phase/post-M3, topic/long-frame-robustness]
date: 2026-05-31
study_id: eq_us_cyclical
phase: "item7 사전조사 — 장기 frame robustness: 가용 epoch 길이 + GFC/COVID 포함 + 추가 epoch 정의"
session: btn-common-task (eq_us_cyclical workspace)
deliver_to: btn-Codlearn (main, item7 합의 대기)
inputs:
  - raw/yfinance/sector_etf_close.csv (XLB/XLE/XLI/SOXX 가용 시작 확인)
  - raw/fred/ 17 시리즈 (DGS10 1990- / CFNAI 1990- / NEWORDER 1992- / BAMLH0A0HYM2 2023-)
  - raw/m3-findings.md (M3 frame 2021-12 ~ 2024-12, 4 epoch)
  - raw/industry-delta-synthesis.md §8.8 frame 한정 미해결
note: |
  ★사용자 inject 지시 — main 회신 대기 중 idle 금지로 item7 사전조사.
  결과 1줄 보고 후 main 합의 시 장기 frame 확장 계획 확정.
data_integrity: "⛔ 합성 無. 기존 raw/ 데이터 인벤토리 + M1 timeline 확장 후보 식별."
---

# Pre-scan: Long-Frame Robustness

> 현재 M3 frame = 2021-12~2024-12 (3년 4 epoch). 장기 frame 확장 시 검증할 robustness 시나리오 + 가용 epoch 인벤토리. 결론: **4 산업 공통 가용 시작 = 2001-07-13 (SOXX 출시일) → 24.8년 frame 가능 (GFC+COVID+shale revolution 다 포함)**. 가용 epoch 추가 ~7-8 개 식별. ★주요 risk = ETF holdings drift (sector composition 시간변화).

---

## §1. 가용 frame 인벤토리

### 1.1 ETF 4 산업 공통 가용 시작

| ETF | 가용 시작 | 가용 종료 | 가용 기간 |
|---|---|---|---|
| XLB | 2000-01-03 | 2026-05-29 | 26.4년 |
| XLE | 2000-01-03 | 2026-05-29 | 26.4년 |
| XLI | 2000-01-03 | 2026-05-29 | 26.4년 |
| **SOXX** | **2001-07-13** ★ | 2026-05-29 | **24.8년** ← bottleneck |
| **공통** | **2001-07-13** | 2026-05-29 | **24.8년** |

★ **결론 1**: SOXX (iShares Semiconductor) 2001-07 출시일이 4 산업 공통 frame 의 bottleneck. **24.8년 (≈ 297 months ≈ 6242 daily)** frame 가능.

### 1.2 거시 driver 가용 시작

| Driver | 가용 시작 | M3 frame 24.8년 cover 가능 |
|---|---|---|
| DGS10 (us10y) | 1990-01 | ✅ |
| dxy (yfinance) | 1990s ~ (확인 필요) | ✅ 추정 |
| oil WTI (yfinance) | 1990s ~ | ✅ |
| VIXCLS | 1990-01 | ✅ |
| CFNAI (H3) | 1990-01 | ✅ |
| NEWORDER (ISM) | 1992-02 | ✅ |
| AMTMNO | 1992-02 | ✅ |
| BUSINV | 1992-01 | ✅ |
| DGORDER | 1992-02 | ✅ |
| T10Y2Y | 1990-01 | ✅ |
| **BAMLH0A0HYM2 (HY OAS)** | **2023-05** ★ | ⛔ **3년 only** — 장기 frame 활용 불가 |
| BAA10Y / AAA10Y / BAA / AAA / BAAFFM / AAAFFM | (확인 필요, 일별 yield) | ✅ 추정 |

★ **결론 2**: 거시 driver 대부분 24.8년 frame cover 가능. **유일 예외 = HY OAS (2023-05~)** → 장기 frame 활용 불가, AAA/BAA spread 또는 다른 credit signal 대체 검토.

---

## §2. 추가 epoch 정의 후보

### 2.1 24.8년 frame 가운데 macro epoch 인벤토리 (M1 timeline 확장 후보)

| # | Epoch label (후보) | 기간 | 길이 | 특징 |
|---|---|---|---|---|
| L1 | dotcom 후폭풍 + 9/11 + 이라크전 | 2001-07 ~ 2003-03 | 21M | rate 저점 (Greenspan 1%) + risk-off |
| L2 | pre-GFC bull + 중국 super-cycle | 2003-04 ~ 2007-09 | 54M | rate 정상화 + commodity boom |
| L3 | GFC bear market | 2007-10 ~ 2009-03 | 18M | risk-off + credit crisis + dollar surge |
| L4 | GFC 회복 + QE1/2 + 중국 4조위안 | 2009-04 ~ 2011-04 | 25M | risk-on + commodity rally + USD 약세 |
| L5 | 중국 둔화 + shale revolution + euro debt + Taper Tantrum | 2011-05 ~ 2016-01 | 57M | mixed regime, oil −60% (2014-15) |
| L6 | Trump pre-trade-war + Goldilocks | 2016-02 ~ 2018-01 | 24M | low vol bull + synchronized growth |
| L7 | Powell hike + trade war | 2018-02 ~ 2019-12 | 23M | rate 정상화 + 미중 갈등 |
| L8 | COVID 충격 | 2020-01 ~ 2020-03 | 3M | acute shock (★n=63 daily, G1 fail) |
| L9 | COVID V-shape + 무한QE | 2020-04 ~ 2021-12 | 21M | risk-on + commodity rally + 인플레 태동 |
| **L10 (M3 E1)** | **긴축충격** | **2022-01 ~ 2022-09** | **9M (n=188)** | (현 M3) |
| **L11 (M3 E2)** | **전환·반등** | **2022-10 ~ 2023-06** | **9M (n=187)** | (현 M3) |
| **L12 (M3 E3)** | **금리재상승** | **2023-07 ~ 2023-10** | **4M (n=85)** | (현 M3) |
| **L13 (M3 E4)** | **pivot·인하** | **2023-11 ~ 2024-12** | **14M (n=275)** | (현 M3) |
| L14 | post-M3 | 2025-01 ~ 2026-05 | 17M | post-Trump 2 + Fed 추가 cut + AI |

★ **결론 3**: 4 epoch (M3) → **~13 epoch (M3 4 + 추가 9)** 확장 가능. M1 timeline layer 의 epoch 정의 확장 필요 (배분레이어 책임).

### 2.2 historical analog (M3 E1~E4 의 long-frame 유사 epoch)

| M3 epoch | Type | Historical analog (long-frame) |
|---|---|---|
| E1 긴축충격 | rate hike + risk-off + dollar surge | L3 GFC (2008-09) / L7 Powell hike (2018-Q4 단기) |
| E2 전환·반등 | pivot 기대 + risk-on + multiple expansion | L4 GFC 회복 (2009-Q2) / L9 COVID V-shape (2020-Q2) |
| E3 금리재상승 | rate 재상승 + 약화 | L5 Taper Tantrum (2013-Q3) / L7 trade war 일부 (2018-Q4) |
| E4 pivot·인하 | rate cut 기대 + AI/secular | L1 dotcom 후 rate cut (2002-2003) / L4 QE1/2 |

★ **결론 4**: 4 epoch type 각각 ≥2 historical analog 존재 → δ_regime regime tag 의 transferability 검증 가능 (epoch type 별 β 추정 reproducibility).

---

## §3. Robustness 시나리오 (Verify stage 후보)

### 3.1 시나리오 A — 전체 frame 단일 회귀 (2001-07 ~ 2026-05)

```
y_sleeve ~ Δus10y + r_dxy + r_oil  (daily, n=6242)
```

★ R² + 모든 cell β 시간평균. M3 frame 한정 β 와 비교 → frame-specific bias 정량화.

**예상 결과** (도메인 prior):
- β_dxy 가 sleeve 전반 음의 부호 유지 (다양한 epoch 평균)
- R² 가 0.10~0.15 (긴 frame 의 noise 평균)
- M3 frame β 와 차이 = epoch heterogeneity 의 신호

### 3.2 시나리오 B — Rolling 60M window

```
for t in 2006-07 ~ 2026-05:
    fit β_t on [t-60M, t]
    record β_dxy_t, β_oil_t, β_us10y_t
```

★ β 시계열 → structural break / regime transition 식별. 2008-09 / 2014-15 (shale) / 2020-Q2 / 2022-Q1 같은 transition 시점 visualize.

**예상 발견**:
- β_oil 의 secular 감소 (oil-equity decoupling, post-2014 shale)
- β_dxy 의 epoch-conditional 가변 (긴축 epoch 강 / 완화 epoch 약)
- β_us10y 의 일시 음수 전환 (rate re-rise epochs)

### 3.3 시나리오 C — Leave-one-epoch-out CV

```
for hold_epoch in [L1, L2, ..., L14]:
    fit on other 12 epochs (avg β, R²)
    predict hold_epoch sleeve return
    record R²_OOS / R²_IS / residual pattern
```

★ R²_OOS << R²_IS → epoch heterogeneity dominant → δ_regime 의 epoch-conditional 적합. R²_OOS ≈ R²_IS → epoch heterogeneity 약 → δ_regime saturation 의 epoch-invariant interpretation.

**예상 발견** (M3 E1~E4 가운데 어느 epoch 가 prediction OOS 견고한지):
- E4 (R²=0.070, n=275) = OOS holdout 견고할 가능성 (긴 frame + 약한 driver R²)
- E3 (R²=0.131, n=85) = OOS holdout 분산 큼 (n 작음 + 일시 rate 재상승)
- E1/E2 = supply shock / pivot 의 idiosyncratic 큼 → OOS 분산

### 3.4 시나리오 D — Regime-conditional β transferability

```
group_E1_like = {L3 GFC, L7 Powell hike (subset), L10 M3 E1}
group_E2_like = {L4 GFC 회복, L9 COVID V-shape, L11 M3 E2}
group_E3_like = {L5 Taper Tantrum, L7 trade war subset, L12 M3 E3}
group_E4_like = {L1 dotcom cut, L4 QE1, L13 M3 E4}

for group:
    fit β by group (within-group regime tag)
    compare M3 epoch β vs group avg β
```

★ M3 frame β 가 group 평균 β 와 일치 → δ_regime 의 transferability 확인 (장기 frame 보강). 차이 큼 → M3 frame 특수성.

**예상 발견**:
- E1 group: β_dxy 강함 + R² 높음 (긴축충격 공통 pattern)
- E4 group: R² 약함 + idiosyncratic narrative dominant (AI / dotcom cut 의 사례별 다름)

### 3.5 시나리오 E — Structural break test (Chow / Bai-Perron)

```
H0: 모든 epoch β 동일
H1: epoch 별 break
test: Chow F-statistic / Bai-Perron multiple break detection
```

★ break point 자동 식별 → M1 timeline epoch 경계 와 비교. 일치 → M1 timeline 신뢰. 불일치 → M1 timeline 재검토.

---

## §4. ★주요 risk — ETF holdings drift

### 4.1 산업 ETF 구성 변화 (sector composition drift)

| ETF | 초기 (출시) | 현재 (2026) | drift 영향 |
|---|---|---|---|
| **SOXX** | Intel/TXN/AMD (2001) | NVDA dominant 30%+ (2026 AI rally) | 가격 vs 펀더멘털 mix 시간변화 큼 |
| **XLE** | XOM/CVX heavy (2000) | shale-pure-play (EOG/PXD/FANG) 비중 증가 post-2014 shale | upstream/downstream mix 변화 |
| **XLB** | mining + 화학 + 건설 mix | rare earth/lithium (Albemarle) 신규 등장 post-2010 | secular sub-archetype 변화 |
| **XLI** | classic capital goods + 운송 | defense (LMT/NOC) 비중 변동 | 비교적 안정 (mature sector) |

★ **risk**: 장기 frame β 추정 시 sector composition 시간변화가 cycle β 변화와 mixing → frame-conditional β 의 해석에 주의.

### 4.2 완화 방법

1. **etf-level analysis 한정 명시** (synthesis 12축 audit I 축 "ETF level survivor bias 작음" 와 정합).
2. **holdings 시점별 boundary 분리** = 주요 holdings 변화 시점 (예: SOXX NVDA 30%+ 시점 = 2023 Q4) 을 epoch boundary 로 추가 검토.
3. **individual stock cohort analysis** = EDGAR 적재 후 sub-archetype 별 종목 cohort 추적 (R15.8 sub_archetype_weights).

---

## §5. 권고 — 장기 frame 확장 계획

### 5.1 단기 (collector 적재 전, 즉시 가능)

- **시나리오 A 시도** (전체 frame 단일 회귀) — M3 driver 3종 (us10y/dxy/oil) raw/fred + yfinance 기존 데이터로 즉시 가능.
- M3 frame β 와 장기 frame β 비교 → frame-conditional bias 정량화.

### 5.2 중기 (M1 timeline epoch 확장 후)

- **시나리오 B/C/D** (rolling 60M + LOEO CV + regime-conditional transferability) — M1 timeline 의 epoch 확장 (14 epoch) 후 실행 가능.
- 사용자가 명시한 "장기 frame robustness" 의 본격 진입.

### 5.3 장기 (Verify stage 통합)

- **시나리오 E** (Bai-Perron break detection) — Verify stage 의 Tier 1 측정 일부로 통합. M1 timeline 의 자동 검증.

---

## §6. main 합의 요청 (item7 회신 candidate)

```
[item7 사전조사 결과]
- 4 산업 공통 가용 = 2001-07-13 ~ 2026-05-29 (24.8년, SOXX 출시일 bottleneck)
- GFC (L3 2007-10~2009-03) / COVID (L8/L9 2020-01~2021-12) / shale revolution (L5 2014-15) 다 포함
- 추가 epoch 정의 후보 ~9 개 (L1 dotcom 후폭풍 ~ L14 post-M3, 현 M3 E1~E4 = L10~L13)
- robustness 시나리오 A~E 식별 (전체회귀 / rolling 60M / LOEO CV / regime-conditional transferability / Bai-Perron break)
- ★주요 risk = ETF holdings drift (SOXX NVDA dominant post-2023 / XLE shale-pure-play post-2014)
- ★예외 = HY OAS 2023-05 부터 가용, 장기 frame 활용 불가 (item6 결론 5 일관)
- 단기 즉시 가능 = 시나리오 A (전체 frame 단일 회귀, M3 frame β 와 비교)
```

---

## §7. 한계·미해결

1. **M1 timeline 확장 = M1 layer 책임** (배분레이어). 14 epoch label 정의 + 경계 시점 = M1 분석 별도 round.
2. **ETF holdings 시점별 데이터** = iShares/SSGA 공시 historical holdings 필요 (10-K 또는 ETF.com archive).
3. **dxy yfinance 가용 시작** = 본 prescan 미확인 (1990s 추정). 시나리오 A 진입 전 확인 필요.
4. **시나리오 B 60M window** = 시작 시점 t-60M ≥ 2001-07 이려면 t ≥ 2006-07. 2001-07 ~ 2006-06 frame = rolling 진입 X (initialization period).
5. **시나리오 C LOEO CV** = 14 epoch 의 길이 불균등 (L8 COVID 3M ~ L5 shale 57M). epoch length-weighted CV 권고.
6. **시나리오 E Bai-Perron** = epoch 사전 정의 없이 자동 break detection → M1 timeline 의 break point 와 일치 검증 가능 (M1 timeline 자체 audit).
7. **regime-conditional transferability (시나리오 D)** = group 분류의 subjectivity (예: trade war 2018-Q4 가 E1-like 인가 E3-like 인가?). domain expertise 필요.
8. **장기 frame 확장 시점** = item6 (ALFRED) + collector 적재 (EDGAR / FINNHUB) 와 직교 → main 우선순위 결정 필요.
