# validation-v3-cross-sectional.md — auto(자동차) §M v3 재산출 (cross-sectional)

> frame v3 §M.1~M.7 측정. raw 재현: `raw-v3/{collect, measure, measure_cross, exposure_card, collect_dart, measure_valuation}.py`.
> battery/반도체 pilot 미러. ★핵심 발견 = 자동차 가격 momentum/reversal 신호 = 약 음(reversal)·비유의 = 가격신호 무효.

## §0. 데이터 제약 + 해소

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV 개별종목 loop | ✅ 작동 | 17종 가격 패널 (2019-2026, 1818일) |
| pykrx **시장 스냅샷** | ❌ KRX 인증 차단 | PBR/PER 스냅샷 불가 → **DART 재구성 우회(§10)** |
| **DART fnlttSinglAcntAll** | ✅ 작동 | ★valuation 횡단면 PIT 재구성 |
| FDR KRX-DESC (Sector/Industry/Products) | ✅ 작동 | universe 멤버십 (현재 스냅샷 = PIT 아님) |
| yfinance (CARZ/SLX/VIX/factors) | ✅ 작동 | cross 공통인자 + customer momentum + G1 regime |

## §1. universe 확장 + ★화이트리스트 정밀화 (§M.6, supervisor 지시)

- FDR 자동차 키워드(`자동차|완성차|자동차부품|타이어|파워트레인|변속기` 등) 매칭 → ★**오염 다수**(자동차보험·해운·2차전지·유통·음료가 Products 부수 매칭).
- ★**Industry 화이트리스트 정밀화**: `자동차용 엔진 및 자동차 제조업`(완성차) + `자동차 신품 부품 제조업`(부품) + `고무제품 제조업 AND 타이어 Products`(타이어)만 통과. AND **명시 블랙리스트**(LG에너지솔루션/HMM/DB손보/현대해상/SK네트웍스/효성/세아베스틸/STX엔진/퍼스텍/롯데칠성 등 18종 배제).
- 시총 floor(≥3000억) ∧ ADV floor(≥30억) = **17종** 통과. 전부 진짜 자동차:
  - 완성차 3: 현대차(149조)/기아(66조)/KG모빌리티
  - 부품 12: 현대모비스(69조)/HL만도/현대위아/에스엘/삼현/SNT다이내믹스/성우하이텍/한라캐스트/명신산업/네오티스/디아이씨/화신
  - 타이어 2: 한국타이어/금호타이어
- ★현대차/기아/모비스 시총 압도(cap 70%+) → cap-weighted IC 점검 핵심. avg N 15종(battery 26·반도체 73 대비 작음 = small-n).

## §2. forward 횡단면 Rank-IC (horizon-tagged, §M.2)

4 신호 × 4 horizon = 16 테스트. ★전부 비유의:

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV OOS hit | avg_N |
|---|---|---|---|---|---|---|
| mom_6 → 3M | -0.064 | -1.69 | 80 | 0.096 | 0.87 | 14.9 |
| mom_6 → 6M | -0.062 | -1.18 | 77 | 0.242 | 0.73 | 14.9 |
| vol_60 → 12M | -0.033 | -0.52 | 74 | 0.602 | 0.60 | 14.9 |
| mom_6 → 12M | -0.023 | -0.26 | 71 | 0.794 | 0.60 | 14.8 |
| (나머지 12 신호) | \|IC\|<0.03 | \|t\|<1.0 | — | >0.37 | — | — |

★**핵심 발견 = 가격신호 무효**:
- 16 신호 중 가장 강한 mom_6→3M 도 t=-1.69, **p_NW=0.096 비유의**. NW CI [-0.138, 0.010] + block-boot [-0.141, 0.005] = **0 포함**.
- 부호 = 약 음(reversal 방향) = 반도체(-0.065 유의)와 **동부호이나 자동차는 비유의·절반 약**.
- 3산업 비교: battery(양 momentum +0.086 CONFIRMED) / 반도체(음 reversal -0.065 PARTIAL) / **자동차(음 reversal -0.064 비유의)** = 같은 cyclical 도 신호 강도 상이.

## §3. 4게이트 (§M.2)

**candidate primary = mom_6 → 3M** (그나마 강):
- **G1 ex-ante**: CARZ yoy regime (글로벌 자동차 cycle proxy, 진입시점 관측가능). 달력컷 아님.
- **G2 다중검정 (FDR/BY)**: 16 테스트, BY factor=3.381. raw_p_min=0.0958(mom_6__3M). **BY rank1 threshold ≈ 0.00185 → 생존 0**. Bonferroni α/16=0.00313 → 0.0958 ≫ 임계 = **미생존**. ★전 16 신호 비유의.
- **G3 CPCV purge+embargo**: OOS hit=0.87 (mom_6__3M, 부호 약 일관) — 게이트 통과하나 신호 자체가 약.
- **G4 Newey-West HAC**: lag=horizon. t_nw=-1.69. NW CI 0 포함 = 비유의.

★**게이트 종합**: G3 OOS 는 통과(부호 일관)하나 **G2·G4 비유의** = primary 신호 자격 미달. verdict = **TENTATIVE DIRECTIONAL / horizon forward alpha 부재**.

## §4. robustness (§M.1, §M.3)

- **유동성-티어 IC (§M.1 ⑱)**: mom_6→3M hi-ADV -0.058 / lo-ADV -0.012 / **cap-weighted -0.083**. mom_6→6M cap-weighted -0.124. ★cap-weighted 가 동일가중보다 강한 음 = 대형주(현대차/기아/모비스)에서 reversal 방향성 = 반도체 cyclical 패턴 유사. 단 CI 0 포함 = 비유의.
- **within-period**: mom_6→3M 0.75 / 6M 0.57 (경계, 약).
- **leave-episode / e-process**: 신호 약·비유의라 강건성 판정 무의미(약신호 placebo 수준).

## §5. cross 축 (§M.3 — 산업=보고만)

### (a) 공통인자 β (contemporaneous, HAC maxlags=3, n=35 month)
- credit (US HY OAS): β=-0.072, t=-1.58, CI [-0.162, 0.018] = 약 음 방향성 **비유의**.
- oil: β=-0.166, t=-1.47 = 약 음 비유의(원가 oil 노출 약). rate/dollar/VIX = 비유의. R²=0.175.
- ★**자동차 공통인자 노출 약 = idiosyncratic** (반도체 credit -0.190 t=-3.36 강 과 대조). 자동차는 글로벌 매크로보다 산업 고유 사이클 지배.

### (b) customer-supplier momentum (alpha 후보, §M.3)
- 글로벌 자동차 수요(CARZ) / 철강 원가(SLX) 3M lagged momentum → 한국 자동차 forward 1M:

| lag | CARZ corr (p) | SLX corr (p) |
|---|---|---|
| 0 | **+0.220 (0.043)** | **+0.231 (0.034)** |
| 1 | +0.170 (0.121) | +0.203 (0.064) |
| 2 | +0.128 (0.247) | +0.188 (0.088) |
| 3 | +0.140 (0.210) | +0.176 (0.114) |

→ **REJECTED as alpha**: ★lag0(contemporaneous) 유의(+0.22/+0.23 p<0.05) but **forward(lag1-3) 비유의**(p>0.06). = 글로벌 자동차 수요 contemporaneous 동조 강하나 forward 예측 부재(§D forward-alpha falsifier 작동). 동조성분은 RegimeGlasso Ω 흡수. ★반도체(lag0 +0.04)보다 contemporaneous 동조 훨씬 강 = 자동차가 글로벌 cycle 더 직접 동조.

## §6. PIT-fundamentals safety (§M.1 ⑯)

DART 사업보고서(A001) 제출일 rcept_dt vs FY-end gap: 2021-2025 median delay **~108-120일**. 펀더멘털 신호는 rcept_dt 이후만 사용 의무. **가격신호는 PIT-safe**.

## §7. cross-sectional exposure card (§M.7)

universe 17종 현 시점(2026-05-31) peer-relative z-score (sector-neutral). 상위 (mom_6_z):

| ticker | name | mom_6_z | mom_12_1_z | vol_60_z |
|---|---|---|---|---|
| 085910 | 네오티스 | +3.46 | +3.43 | +1.30 |
| 005380 | 현대차 | +0.97 | +0.37 | -0.21 |
| 012330 | 현대모비스 | +0.72 | -0.33 | +1.07 |
| 005850 | 에스엘 | +0.15 | -0.15 | +0.01 |
| 000270 | 기아 | -0.13 | -0.32 | -1.05 |

★signal 부호 주의: 자동차 momentum forward IC = 약 음·비유의 → mom_6_z 상위 종목이 forward 약(reversal 방향). 단 비유의라 selection 시 weight ~0. 전체 = `raw-v3/exposure-card-v3.json`. ⛔ score→target weight = supervisor 조립.

## §8. net-cost (§M.4)

KR 비대칭 왕복 33bps / 월 16.5bps. ★가격신호 비유의라 net Sharpe 무의미. valuation·regime 신호 확정 후 재평가.

## §10. ★valuation 횡단면 (§M.7 핵심 — DART 재구성)

> 결과는 measure_valuation.py 실행 후 본 절에 박제 (DART financials 수집 완료 의존).

**PIT 엄수**: 각 재무 = `rcept_dt`(공시일) 이후 시점에만 적용 = lookahead 회피. 시총 = Close × 현재주식수(collector_plan).

★**자동차 valuation = 진짜 신호** (가격신호 무효 → valuation 우위 가설 적중). DART 417 rows(2019~) → PBR/PER cross-sectional z. coverage PBR 1261 / PER 953 cells.

**측정 결과 (2026-06-03):**

| signal__h | IC | t_NW | p | n | within | avgN | BY |
|---|---|---|---|---|---|---|---|
| **pbr_z→24M** | **-0.463** | **-17.59** | 0.000 | 61 | **1.00** | 14.3 | ★생존 |
| pbr_z→12M | -0.216 | -2.76 | 0.007 | 73 | 0.71 | 14.5 | 생존 |
| pbr_z→6M/3M | -0.165/-0.122 | -2.6/-3.0 | 0.013/0.004 | 79/82 | 0.86/0.88 | 생존 |
| **per_z→3M/6M/12M** | **+0.003/+0.004/-0.007** | <\|0.1\| | >0.94 | — | 0.38-0.57 | ★무신호 |

- ★**PBR value premium 방향 강**: 전 horizon 음, **BY 4개 생존**, within 100%@24M, **LOO robust**(17종 각 제외 IC [-0.537, -0.395] 전부 음), block-boot CI [-0.336, -0.108] 0 배제.
- ★**PER 무신호 = peak-EPS trap 데이터 입증**: per_z IC ≈ 0 (전 horizon). cyclical 정점 EPS↑→PER↓ 왜곡 → PER 무효. PBR(자본 기반)은 안정적 value. = ★archetype.py cyclical 정의("primary=P/B, trap=peak-EPS") 정확.
- ★**BUT magnitude 과대**: PBR 24M IC -0.46, t=-17.6 = n=14 협소 Spearman 극단화. → 방향 신뢰/magnitude small-n hedge.
- ★PER 무효 → **EV/EBITDA 대체 권고**(cyclical primary, collector_plan high).

## §9. verdict

- ★**valuation(PBR) = 자동차 진짜 신호**: PBR value premium 방향 강(BY 4 생존, LOO robust, within 100%) = 가격 momentum 무효 대체(가설 적중). ★단 universe 17종 협소 → magnitude 과대(hedge).
- **PER = peak-EPS trap 무신호** = archetype.py cyclical 정의 데이터 입증 → EV/EBITDA 대체.
- **가격신호 (momentum reversal)** = 비유의 (BY 0, CI 0 포함). 반도체 cyclical 동형.
- **customer momentum** = REJECTED (contemporaneous 동조, forward 부재). **common factor** = 전부 비유의.
- **산업 전체 = PARTIAL** — PBR value 방향 강(robust)하나 magnitude 과대 + PER peak-EPS 무효. archetype cyclical 지지.
- ★**archetype별 metric 차등 입증**: cyclical(auto) = PBR○ PER✗(peak-EPS) / asset_stable(consumer/telecom) = PER value / event_driven(bio) = 멀티플 부적합 = §M 양식이 archetype별 valuation metric 적합도를 데이터로 구분.
