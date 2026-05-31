# raw/ 데이터 인벤토리 (2026-05-30, 2-3 진입 시점)

> direction.md ② 변수정의표 ↔ 실제 보유 데이터 매핑. ⛔ 합성·시뮬 데이터 절대 사용 금지 (§2.5 감사 B축). 실측 n·기간 명시.

| driver | 시리즈 | 파일 | 행수 | 기간 | 상태 | 비고 |
|---|---|---|---|---|---|---|
| real_rate_10y | FRED DFII10 | fred_dfii10.csv | 4279 | 2010-01-04~2026-05-29 | ✓ | TIPS 10Y CMT |
| breakeven_10y | FRED T10YIE | fred_t10yie.csv | 4280 | 2010-01-04~2026-05-29 | ✓ | DGS10 − DFII10 항등식 |
| nominal_10y | FRED DGS10 | fred_dgs10.csv | 4280 | 2010-01-04~ | ✓ | 항등식 게이트 검증용 |
| dollar_broad | FRED DTWEXBGS | fred_dtwexbgs.csv | 4276 | 2010-01-04~ | ✓ | broad TWI |
| dollar_eur | FRED DEXUSEU | fred_dexuseu.csv | 4276 | 2010-01-04~ | ✓ | SDR 합성 컴포넌트 |
| dollar_jpy | FRED DEXJPUS | fred_dexjpus.csv | 4276 | 2010-01-04~ | ✓ | SDR 합성 |
| dollar_cny | FRED DEXCHUS | fred_dexchus.csv | 4276 | 2010-01-04~ | ✓ | SDR 합성 |
| dollar_gbp | FRED DEXUSUK | fred_dexusuk.csv | 4276 | 2010-01-04~ | ✓ | SDR 합성 |
| gold_USD | Yahoo v8 GLD | try_yahoo_v8.json | ~4000 | 2010-01-04~2026-05-29 | ✓ | GLD ETF 일별 close (LBMA PM 직접 fetch 실패, GLD 가격 = ~LBMA 비례 프록시) |
| credit_hy_oas | FRED BAMLH0A0HYM2 | fred_hy_oas.csv | 795 | 2023-05-30~2026-05-28 | ⚠ | fredgraph.csv 3년치만 (cosd 무시 — alternative endpoint 미해결, 위기(2008·2020) 미포함 → H5 검증 부분적) |
| credit_baa | FRED BAA10Y | fred_baa10y.csv | 4279 | 2010-01-04~ | ✓ | Moody's BAA−10Y, HY OAS 부분 대체 |
| vix | FRED VIXCLS | fred_vix.csv | 4280 | 2010-01-04~ | ✓ | risk proxy (Caldara-Iacoviello GPR 와 보조) |
| gpr_index | Caldara-Iacoviello GPRD | gpr_daily.xls | 15121 | 1985-01-01~2026-05-26 | ✓ | Daily GPR Index (base 1985:2019=100). 컬럼 GPRD, GPRD_ACT, GPRD_THREAT, GPRD_MA7, GPRD_MA30 |
| cb_demand_proxy | WGC quarterly CB net purchase | — | — | — | ⛔ | 본 시점 미수집. H3 진행 시 WGC GDT public 수동 입력. 2010-2024 60 분기 × 톤수 |
| sdr_usd | IMF SDR/USD 합성 | — | — | — | ⚠ | FRED FX 4 시리즈 + 상수 가중치(43.38% USD, 29.31% EUR, 12.28% CNY, 7.59% JPY, 7.44% GBP, 2022 reweight) 로 합성 |

## 결손·제약
- **HY OAS 위기 데이터 부재**: BAMLH0A0HYM2 가 fredgraph.csv endpoint 에서 3년치만 반환되는 이상. 대안 (a) FRED ALFRED API key 발급 (b) Moody's BAA−10Y 대체 (이미 받음, 4279 lines, 위기 포함). H5 검증은 BAA10Y 1차 + HY OAS 보조.
- **gold 시리즈 = GLD ETF**: LBMA PM (FRED GOLDPMGBD228NLBM) 직접 fetch 실패 (HTML 반환). GLD 가격은 LBMA 의 ~1/10 oz 추적 → 변화율 단위 분석엔 동일 (R²↔scale 무관). 단 *수준 회귀* 의 절대값 해석 시 GLD price ≈ 1/10 LBMA fix 환산 필요.
- **cb_demand**: WGC 분기 톤수 = public 보고서 PDF·web. H3 진행 시 수동 입력으로 박제 (60 quarterly observations). 분기→일별 Kalman 보간 (R2 Q5 합의).

## 사용 가능 분석 라이브러리
- Python 3.12.10, pandas 2.2.3, numpy 2.4.2, statsmodels 0.14.6, xlrd 2.0.2
- statsmodels: cointegration (Johansen, Engle-Granger), VECM, MarkovRegression, structural break tests (recursive_olsresiduals + Bai-Perron via separate package or manual), Q-Reg

## §2.5 감사 B축 자가 체크 (본 인벤토리 시점)
- ✓ 모든 시리즈 = 외부 공인 출처(FRED official + Caldara-Iacoviello 학술 + WGC official)
- ✓ 합성·시뮬 데이터 0건 (단 SDR 합성은 IMF 공시 weight 의 상수 가중치 — 본 시스템의 정의된 결정론 변환임을 명시)
- ✓ n·기간 명시
- ⚠ 결손 항목 (HY OAS·cb_demand·SDR) 박제 + 대체 plan
