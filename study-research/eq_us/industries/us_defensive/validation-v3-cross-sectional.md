# validation-v3-cross-sectional.md — us_defensive sleeve §M v3 (cross-sectional)

> frame v3 §M.1~M.7 측정. raw 재현: `raw-v3/{collect, measure, measure_cross, exposure_card, (collect_edgar, measure_valuation)}.py`.
> 한국 consumer/auto + battery pilot 미러 (pykrx→yfinance, DART→EDGAR). ★EDGAR valuation §10 = #15 us_cyclical 파이프라인 후.
> ★핵심 = momentum 무효(asset_stable) + 단기 reversal 유의 + 저변동성 프리미엄 + real_rate 듀레이션 민감.

## §0. 데이터 + ★합성 P0 재검증 (§1.7-D synthetic check)

| 데이터 | 상태 | 비고 |
|---|---|---|
| yfinance 개별종목 OHLCV | ✅ 작동 | 48종 가격 패널 (2010-2026, 4125일) |
| 기존 sector_etf_close.csv (2000~) | ✅ **실데이터** | §1.7-D 통과: 2000-01-03~ 실거래일, SHY/SOXX/TLT 2000 미상장 NaN = 역사 정확(합성 아님) |
| FRED CSV 14종 (DGS10/DFII10/HY OAS/DXY/VIX) | ✅ 실데이터 | BAMLH0A0HYM2.csv.v2-backup 버전이력 = 실작업 흔적 |
| EDGAR XBRL (PER/PBR/배당) | ⏳ #15 후 | valuation §10 = us_cyclical 파이프라인 검증 후 |

★**합성 P0 재검증 결과 (supervisor 의무)**:
- ★진짜 synthetic = `raw/_deprecated_lens-hypothesis-quickcheck-v1-synthetic.txt`(v1) = **이미 _deprecated 격리** = 폐기 확정, 참조 안 함.
- `raw/run_validation.py` line 311 `np.random.default_rng(20260530)` = ★합성 데이터 생성 **아님**, IID bootstrap CI 재현용 seed(XLP+XLU+XLV+XLF 실데이터 resampling). ★단 IID = autocorr 미보정 = small-n rule §1.4 위반 → 본 v3 = **block bootstrap(block=6M) 교체**.
- 현 raw 데이터(sector_etf_close/FRED) = §1.7-D 결측·갭·역사 이벤트 실재 확인 → **실데이터 확정**.

## §1. universe (§M.6, asset_stable)

- ★sleeve = XLP/XLU/XLV/XLC-mature 대표 대형주 48종(yfinance holdings). 한국 종목 universe ≠ ETF holdings.
  - staples 15 (PG/KO/PEP/COST/WMT 등) / utilities 15 (NEE/DUK/SO/D 등) / healthcare 15 (JNJ/UNH/LLY/MRK 등) / comm_mature 3 (VZ/T/CMCSA/TMUS).
- avg N 47종 = 한국(battery 26·반도체 73) 대비 우수. ★survivorship-biased: 현재 대형주 스냅샷 = 상폐/M&A 누락(collector_plan high).
- n=183-195개월(2010~) = 한국(71-88개월) 대비 ★장기 표본 = Validated tier(≥100).

## §2. forward 횡단면 Rank-IC (horizon-tagged, ★block-boot)

4 신호 × 4 horizon = 16 테스트:

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV hit | block-boot CI | avg_N |
|---|---|---|---|---|---|---|---|
| **vol_60 → 12M** | **+0.076** | 1.71 | 183 | 0.090 | 0.87 | **[0.006, 0.144]** | 47.4 |
| vol_60 → 6M | +0.058 | 1.65 | 189 | 0.101 | 0.80 | [-0.006, 0.128] | 47.5 |
| **rev_1m → 3M** | **-0.045** | **-2.70** | 193 | **0.008** | 0.93 | **[-0.081, -0.014]** | 47.5 |
| rev_1m → 6M | -0.037 | -2.32 | 190 | 0.022 | 0.93 | [-0.067, -0.007] | 47.5 |
| mom_12_1 → 12M | +0.037 | 1.28 | 173 | 0.204 | 1.00 | — | 47.4 |
| (mom_6/mom_12_1 나머지) | \|IC\|<0.03 | \|t\|<1.3 | — | >0.2 | — | 0 포함 | — |

★**핵심 발견 — asset_stable 정합**:
- **rev_1m → 3M (단기 reversal) = 유의**: IC -0.045, t=-2.70 p=0.008, ★NW+block-boot CI 둘 다 0 배제. = 가장 robust 가격신호.
- **vol_60 → 12M (저변동성 프리미엄) = TENTATIVE**: IC +0.076, block-boot 0 배제 but NW CI 0 포함(t=1.71 p=0.090). 한국 bio cs_lowvol 동형.
- ★**momentum(mom_6/mom_12_1) 무효**: 전부 약·비유의 = **한국 consumer/telecom asset_stable 동형** = 방어주는 momentum 신호 없음.

## §3. 4게이트 (§M.2)

**primary = rev_1m → 3M**:
- **G1 ex-ante**: HY OAS regime (normal 28 / stress 9 month, >p75=3.55) = credit stress ex-ante, defensive 적합. 달력컷 아님.
- **G2 BY-FDR**: 16 테스트, BY factor=3.381. raw_p_min=0.0077(rev_1m__3M). ★BY rank1 임계 미달 → 생존 0. = 방향 유의(NW p=0.008)하나 다중검정 보정 후 미생존 = small-n hedge.
- **G3 CPCV purge+embargo**: OOS hit=0.93(rev_1m). in-sample 부호 OOS 재현.
- **G4 Newey-West HAC**: lag=horizon. t_nw=-2.70. NW CI [-0.077, -0.012] 0 배제 + block-boot 0 배제.

★**게이트 종합**: NW+boot+CPCV+leave-episode 모두 통과(rev_1m) but BY 미생존 → **PARTIAL CONFIRMED**.

## §4. robustness (§M.1, ★block-boot)

- **rev_1m → 3M**: leave-episode 생존(ex-peak -0.053), within 0.647, cap-weighted -0.041(대형주 일관), n=193 Validated.
- **vol_60 → 12M**: leave-episode 생존(ex-peak +0.052), within 0.625, cap-weighted +0.079(대형주 강), block-boot 0 배제/NW 0 포함.
- ★**block bootstrap (block=6M)** = IID 아님(small-n rule §1.4, 월간 regime persistence autocorr 보정). 기존 IID 결과 격하.
- 유동성-티어: rev_1m hi-ADV -0.044/lo-ADV -0.031/cap-weighted -0.041 = 일관(microcap 아티팩트 아님).

## §5. cross 축 (§M.3 — 산업=보고만, ★sub-sector β 분기)

### (a) DEFENSIVE_ALL 공통인자 β (contemporaneous, HAC maxlags=6, n=36 month)
- **real_rate (DFII10) β = -0.171, t=-4.1, CI [-0.255, -0.087]** = ★유의. 실질금리 상승 시 방어주 약세 = **듀레이션 민감(채권 대용)** = H2(TSY long duration) 정합.
- rate (DGS10) β = +0.038 t=1.6 약 양 비유의 (명목금리 약, real_rate가 진짜 채널).
- dollar/hy_oas/vix = 비유의. R²=0.613.

### (b) ★sub-sector rate 민감도 분기 (H5, asset_stable 핵심)
| sub-sector | real_rate β | t | rate β | 해석 |
|---|---|---|---|---|
| **utilities** | **-0.213** | **-2.9** | +0.070 | ★최강 듀레이션 = 채권 대용 (H5 utility rate−) |
| staples | -0.154 | -3.1 | +0.051 | 듀레이션 민감 |
| comm_mature | -0.197 | -1.8 | +0.036 | 배당주 듀레이션 |
| healthcare | -0.137 | -1.9 | -0.007 | 약 (방어적이나 성장 성분) |

→ ★utilities = 최강 듀레이션(real_rate -0.213) = 채권 대용. H5(utility rate−) 부분 정합. ★bank rate+(H5)는 XLF가 us_cyclical/financial sleeve = 본 defensive 밖. ⚠️ n=36 small-n hedge.

### (c) customer-supplier momentum / sector-rotation
- defensive = supply-chain lead-lag 약 → structural_linkage 측정 skip. sector-rotation business-cycle clock = 학술 myth(Molchanov 2024) → 미보고.

## §6. exposure card (§M.7)

universe 48종 현 시점(2026-05-31) peer-relative z (저변동성 상위 = defensive value):

| ticker | sector | vol_60_z | rev_1m_z | mom_6_z |
|---|---|---|---|---|
| DUK | utilities | -1.39 | -0.48 | -0.09 |
| JNJ | healthcare | -1.23 | +0.29 | +0.84 |
| KO | staples | -1.20 | +0.47 | +0.73 |
| ED | utilities | -1.16 | -0.51 | +0.41 |
| SO | utilities | -1.13 | -0.46 | +0.05 |

★signal 부호: vol_60 IC 양(저변동성→고forward) → 저변동성 종목(utilities/대형 staples) overweight. rev_1m IC 음 → 1M 하락 종목 overweight. 전체 = `raw-v3/exposure-card-v3.json`.

## §7. net-cost (§M.4)

★US 비대칭 없음(STT 없음): 왕복 16bps / 월 8bps(turnover 0.5). 한국(33bps) 대비 낮음. |IC| rev 0.045 > 8bps → net 보존 양호.

## §10. ★valuation 횡단면 (§M.7 핵심 — EDGAR XBRL PIT, 박제 완료)

EDGAR companyconcept XBRL(StockholdersEquity/NetIncomeLoss/shares) 21149 rows + yfinance 가격 → PBR/PER cross-sectional z → forward IC. us_cyclical 검증 파이프라인 미러.

**PIT 엄수**: 재무 = filed date(filing acceptance) 이후만(forward-fill) = lookahead 회피(Large accel 10-K 60d/10-Q 40d, 한국 DART rcept_dt 대응). 시총 = Close × shares(EDGAR, filed PIT).

**cross-sectional 작동 = YES**: PBR cov 5150 / PER cov 5108 cells. avg_N 26종(30종 valuation 가용). 사용자 "PER/PBR 평균대비 골고루" 산출 구조 완성.

| signal__horizon | IC | t_NW | n_mo | p_NW | CI_block_boot | CPCV | within | avgN |
|---|---|---|---|---|---|---|---|---|
| pbr_z → 24M_value | +0.062 | 0.91 | 173 | 0.366 | [-0.019, 0.148] | 0.67 | 0.53 | 25.9 |
| per_z → 24M_value | -0.025 | -0.41 | 173 | 0.681 | [-0.106, 0.049] | 0.53 | 0.47 | 25.8 |
| pbr_z → 12M | +0.028 | 0.54 | 185 | 0.591 | — | 0.60 | 0.50 | 26.0 |
| (per_z 나머지) | ≈0 | \|t\|<0.2 | — | >0.9 | 0 포함 | — | — | 26 |

- ★**per_z = value premium 방향(음, -0.025)** but 약·비유의(NW+boot CI 0 포함). **pbr_z = 역방향(양, +0.062)** = 저PBR→저forward = ★방어주 저PBR value trap 가능(싸 보이는 방어주가 부진).
- **BY 보정(8테스트, factor 2.72) 생존 0**. raw_p_min=0.366. = 전 valuation 지표 비유의.
- **verdict: per_z/pbr_z 둘 다 INSUFFICIENT** — 메커니즘 작동하나 us_defensive 내 IC 약·비유의.
- ★결론: 한국 consumer/telecom 강 value premium **미재현** = battery valuation 약 패턴 동일. cf. us_cyclical PER 작동 = ★sleeve 별 valuation IC 상이(동적가중 정당화). ★us_defensive dominant = rev_1m 단기 reversal(유의) + real_rate 듀레이션, valuation 보조 약.

## §9. verdict

- **primary (cs_rev_1m → 3M, 단기 reversal)** = **PARTIAL CONFIRMED**: IC -0.045, t=-2.70 p=0.008, NW+block-boot CI 0 배제, CPCV 0.93, leave-episode 생존, n=193 Validated. ★BY 미생존(raw_p 0.0077) = small-n hedge.
- **cs_lowvol → 12M (저변동성)** = TENTATIVE DIRECTIONAL (block-boot 0 배제, NW 0 포함). 한국 bio 동형.
- **momentum** = 무효 (asset_stable, 한국 consumer/telecom 동형).
- **common factor** = ★real_rate 듀레이션 민감 dominant(β -0.171 t=-4.1, 채권 대용, H2 정합). utilities 최강(-0.213, H5).
- **valuation** = ★메커니즘 작동(EDGAR PIT cov 5150) but IC 약·비유의(per_z value 방향만 약 -0.025, pbr_z 역방향 +0.062 value trap). BY 미생존. 한국 consumer/telecom 강 value premium 미재현 = battery 약 패턴 동일.
- **sleeve 전체 = PARTIAL** — reversal 유의 + 저변동성 TENTATIVE + real_rate 듀레이션 강, momentum·valuation 약. archetype asset_stable 지지(가격 reversal/저변동성/rate 듀레이션이 신호).
