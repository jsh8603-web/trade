---
tags: [type/validation, domain/inv, scope/equity-kr, sector/chemical, layer/fundamental]
date: 2026-06-05
owner: chem-analyst@kr-equity
purpose: Layer1 펀더멘털 + cycle 지표 forward IC 실측 (capex 일반화 검증 + valuation). raw 재현 = raw-v3/measure_*.py.
---

# 화학 validation — Layer1 펀더멘털 (capex/inventory/rnd + valuation)

## 0. 데이터 coverage (B/C/D 축)

- **prices**: `raw-v3/data/prices.parquet` 2019-01-02 ~ 2026-05-29, 1818 거래일, **17종** (화이트리스트 floor-passed).
- **dart_extended** (capex/inventory): `raw-v3/data/dart_extended.parquet` 442 rows, 17종, rcept_dt 2019-05-14 ~ 2026-04-02. coverage: inventory 97% / ppe 100% / intangible 83% / assets 98%.
- **dart_financials** (valuation): 419 rows, equity/net_income/assets, PIT rcept_dt 적용.
- ★PIT: 모든 펀더멘털 = rcept_dt(공시일) 이후만 적용 (lookahead 차단). DART median delay ~108-120일.
- ★universe n=17 = small-n (telecom 13/auto 17 동급) → magnitude 50~70% haircut + 방향만 신뢰 (frame M.12).

## 1. ★★capex 일반화 가설 (H1/H2 — auto 인계 최우선 검증) → **REJECTED (화학 미재현)**

> raw: `raw-v3/measure_fundamentals_cycle.py` → `validation-fundamentals-cycle-v3.json`. cross-sectional z(유형자산/총자산) → forward IC.

| 신호 | prior | y_20d uncond IC | wc_p | y_60d IC | size-orth IC(20d/60d) | WF OOS | verdict |
|---|---|---|---|---|---|---|---|
| **capex_ratio** (ppe/assets, H1) | 음(-) | +0.0017 | 0.957 | -0.011 | -0.002 / -0.011 | **flip(artifact)** | ★**REJECTED** |
| **ppe_yoy** (유형자산 yoy, H2) | 음(-) | +0.039 | 0.227 | +0.014 | — | y20 flip / y5 +0.059(wc_p 0.032 ★부호 양) | ★**REJECTED**(prior 반대) |

- ★**capex_ratio = auto와 정반대 결과**: auto capex_ratio = OOS robust 음 + size독립(t=−3.38) + 단일FDR 생존(high_confidence). **화학 = IC≈0 (size-orth도 ≈0), OOS flip → 신호 부재**.
- ★**진단 (정밀, archetype 내 이질성)**: 종목별 capex_ratio **분산은 존재**(cross-sectional CV 0.241, 범위 0.236~0.617, 최근분기 17종) — "측정 못함" 아니다. panel n_obs=1312 powered인데 **IC≈0 = forward 예측력 부재**(분산 있어도 종목 capex 차이가 forward return 못 가름). auto는 cross-sectional forward 유의(t=-3.38), steel은 within=0.96 selection 유효 — 화학은 분산 있어도 forward 무예측이 핵심 차이. ⇒ **capex anomaly 유효성 = 산업구조 단정 아니라 forward 예측력 실측 의존**(auto/steel 유효 / 화학 무예측). 시계열(산업 cycle timing) capex로는 유효한지 별 측정 필요.
- ppe_yoy = y_5d만 양(+) 유의(wc_p 0.032, prior 음과 반대) = 단기 증설 모멘텀(설비투자→단기 기대), 단 horizon 비단조·OOS flip → artifact 의심. **REJECTED**.
- ⇒ **capex 일반화 가설 = 화학에서 기각**. capex는 산업 cycle 변수(timing)로만 의미, 종목 selection 신호 아님.

## 2. inventory 재고순환 (H3/H4) → **regime-conditional 약신호 (PARTIAL)**

| 신호 | prior | y_20d uncond IC | KRW_neutral cell IC(wc_p) | verdict |
|---|---|---|---|---|
| **inv_ratio** (재고/assets, H3) | 음(-) | -0.003 (wc_p 0.94) | **-0.105 (wc_p 0.024)** y20 / -0.110 (wc_p 0.043) y60 | regime-conditional 음 (TENTATIVE) |
| **inv_yoy** (재고 yoy, H4) | 음(-) | -0.0005 (비유의) | +0.111 (wc_p 0.038, 부호 양) | REJECTED |

- inv_ratio = unconditional ≈0이나 **KRW_neutral 국면**에서 음(prior 정합, 재고↑→forward↓). 단 단일 FDR family BY 미생존(36셀 multiplicity) = regime-conditional 약신호. n=37~38.
- ★해석: 재고순환 가설은 KRW 중립 국면에서만 약하게 작동(원화 변동 없을 때 재고가 cycle 신호). KRW 약세/강세 국면엔 환율 효과가 dominant → 재고 신호 희석.
- inv_yoy = prior 반대 부호 + 비유의 = REJECTED.

## 3. R&D (H5) → **REJECTED (비유의)**
- `rnd_ratio` (무형/assets, prior 양): uncond IC +0.019~0.030 (wc_p 0.38~0.81), WF 일부 flip. 비유의. 화학(commodity 위주)에서 R&D/기술 차별화 약. REJECTED.

## 4. ★valuation (H6/H7) → **PER value premium 강 (★auto/반도체와 반대), PBR 약**

> raw: `raw-v3/measure_valuation.py` → `validation-valuation-v3.json`. PIT PBR/PER cross-sectional z → forward IC.

| 신호 | horizon | IC | t_NW | p_NW | CPCV oos_hit | within | size-orth IC | OOS sign | BY |
|---|---|---|---|---|---|---|---|---|---|
| **per_z** (H7) | 6M | **-0.218** | -3.87 | 0.000 | 1.00 | 0.86 | -0.110 | HOLD | ★생존 |
| per_z | 12M | -0.222 | -2.67 | 0.009 | 0.93 | 0.86 | -0.114 | HOLD | ★생존 |
| per_z | 3M | -0.152 | -3.57 | 0.001 | 1.00 | 0.88 | -0.065 | HOLD | ★생존 |
| per_z | 24M_value | -0.198 | -1.57 | 0.121 | 0.87 | 0.83 | — | — | (degenerate) |
| **pbr_z** (H6) | 12M | -0.123 | -2.41 | 0.018 | 0.93 | 0.86 | -0.098 | HOLD | 미생존 |
| pbr_z | 6M | -0.076 | -1.70 | 0.093 | 0.80 | 0.86 | -0.055 | HOLD | 미생존 |

- ★**핵심 발견 = PER value premium이 PBR보다 강함** (PER 6M IC -0.218 BY 생존 vs PBR 12M -0.123 미생존). **저PER(싸다)→forward 高 = value premium**. OOS HOLD(IS -0.135 / OOS -0.322).
- ★**auto/반도체와 정반대**: frame M.11에서 cyclical(auto/반도체) = PER✗(peak-EPS trap) PBR○. **화학은 PER○ = peak-EPS trap이 화학에선 약함**. 해석 = 화학은 적자/흑자 EPS 변동이 있어도 PER 횡단면 ranking이 forward 예측(반도체 메모리 정점 극단 peak-EPS와 다름). ⇒ ★archetype 내 valuation metric 이질성(시변 적합도) 추가 증거.
- ★**hedge**: (a) n≈12.5 small-n → magnitude 50~70% haircut (point estimate -0.22 literal 금지) (b) **size-orth IC가 절반 감소** (per_z full -0.22 → resid -0.11) = value premium 절반이 small-cap value 위장, size 독립분 -0.11 잔존 (c) 24M_value = eff_N≈2.5 degenerate → primary 근거 강등(3M/6M/12M만).

## 5. summary (Layer1)

- ★**tradeable (G-G eligibility 충족)**: per_z (value premium, size 독립분 -0.11) — 단 small-n haircut.
- **regime-conditional 약신호**: inv_ratio (KRW_neutral 음).
- ★**REJECTED**: capex_ratio (H1 auto 미재현), ppe_yoy (H2 prior 반대), inv_yoy (H4), rnd_ratio (H5).
- ⇒ capex 일반화 가설 화학 기각 = 정직 보고. valuation(PER)이 Layer1 주력 신호.
