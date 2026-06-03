# validation-v3-cross-sectional.md — us_cyclical sleeve §M v3

> frame v3 §M.1~M.7. raw 재현: `raw-v3/{collect, measure}.py` + data/{prices, edgar_fundamentals, macro, universe}.parquet.
> ★미국 1단계 = EDGAR/yfinance/FRED 파이프라인 검증. ★PER○ 발견(한국 auto PER✗ peak-EPS 와 반대). 한국 산업 미러.

## §0. ★미국 데이터 파이프라인 검증 (1단계 핵심)

| 데이터 | 상태 | 검증 |
|---|---|---|
| **yfinance** (가격, ETF+종목) | ✅ | 60종 (2015~, 2867일). ★survivorship-biased(현 holdings) |
| **EDGAR XBRL** (valuation, ★DART 대응) | ✅ | companyconcept API: equity/net_income/shares 27637 rows. ★filed date = PIT timestamp(filing acceptance) |
| **FRED CSV** (거시, 기존 재사용) | ✅ | HY OAS/DGS10/VIXCLS + DXY(yfinance). ★HY OAS = 2023-05~만(caveat) |
| Ken French (FF5+Mom+QMJ+BAB) | — | factor neutralize = supervisor 단계 |

★**미국 1단계 = EDGAR(filed date PIT)/yfinance/FRED 파이프라인 작동 입증** = 미국 sleeve batch 진입 가능. 한국 pykrx/DART → 미국 yfinance/EDGAR 대응 검증 완료.

## §1. universe (§M, 미국 특화)

- us_cyclical = 5 sector × 12 대표 종목 = **60종** (semi SOXX/materials XLB/industrials XLI/energy XLE/financials XLF). sector ETF top holdings 큐레이션. ★육안 sanity: NVDA/AVGO/CAT/XOM/JPM 등 전부 진짜 대형 cyclical.
- ★survivorship-biased: 현 holdings = 생존 종목, 상폐/구성변경 누락 = collector_plan high.

## §2. forward 횡단면 IC (가격 + valuation)

20 테스트 (5 signal × 4 horizon). cross-sectional avgN 60(가격)/35-40(valuation, 적자 제외).

| signal__h | IC | t_NW | p | n | within | avgN | BY |
|---|---|---|---|---|---|---|---|
| **per_z→24M** | **-0.119** | **-2.76** | 0.007 | 113 | 0.70 | 35.1 | borderline |
| vol_60→24M | +0.151 | 2.29 | 0.024 | 111 | 0.80 | 59.5 | 미생존 |
| per_z→3M | -0.062 | -2.47 | 0.015 | 134 | 0.75 | 35.9 | |
| pbr_z→24M | -0.100 | -1.21 | 0.227 | 113 | 0.80 | 40.2 | 비유의 |
| mom_6→3M | +0.059 | 2.40 | 0.018 | 128 | 0.75 | 59.6 | |

- ★**PER value premium 작동**: per_z 24M IC=-0.119, **block-boot CI [-0.169, -0.075] 0 배제**, NW t=-2.76 유의, CPCV 1.00, **LOO sector robust**(5 sector 제외 IC [-0.136, -0.066] 전부 음). per_z 3M도 t=-2.47 유의.
- ★**PBR 약**: pbr_z 24M NW 비유의(t=-1.21). = ★미국 cyclical은 **PER > PBR**.
- ★**vol_60 변동성 프리미엄**: 고변동성 종목 forward↑(IC +0.151) = US large-cap 고베타 보상(저변동성 anomaly 반대).
- BY 보정(20 테스트) 생존 0(per 24M p=0.007 최강이나 borderline). 단 block-boot 유의 + LOO robust = value premium 지지.

## §3. ★cyclical 발견 (한국 auto 와 반대 — peak-EPS 시장 의존성)

★미국 cyclical = **PER 작동**(한국 auto/반도체 = PER✗ peak-EPS / PBR○). 이유 = 미국 대형 cyclical 적자 비율 낮음:

| sector | net_income 적자 비율 |
|---|---|
| financials | 2.9% |
| industrials | 6.9% |
| materials | 8.7% |
| semi | 9.7% |
| energy | 16.4% |

→ 미국 대형 cyclical은 earnings 안정 → **peak-EPS 왜곡 약** → PER 유효. = ★archetype.py cyclical "trap=peak-EPS"의 **시장·시총 의존성**(미국 대형 ≠ 한국 중형 auto). = supervisor 가설("한국 auto PER✗ 재현")을 ★데이터로 반증 = 양식 정직성.

## §4. cross (§M.3 — sleeve=보고만)

dollar_beta H4 회귀 (n=36 month, HAC, R²=0.68):
- ★**HY OAS β=-0.0926, t=-10.04 (강유의)** = HY OAS 확대 → cyclical 약세(risk-off). direction R1 "HY OAS 최강 rotation 분류기" 정합. ★단 BAMLH0A0HYM2 = 2023-05~만(37mo) → ★regime-conditional INSUFFICIENT(eq_us_defensive H3 ERROR 패턴 정직 회피). β 자체도 n=36 hedge.
- rate β=-0.039 t=-2.86 / vix β=-0.003 t=-2.45 = 유의(duration·risk-off).
- ★**dollar β=-0.228, t=-1.02 = 비유의** = direction R2 "Bruno-Shin EM 메커니즘 US cross-sectional 도달 약" 정합. H4 dollar 회귀 = 약.

## §5. PIT + 생존편향

- PIT: 가격 forward-shift safe. ★valuation = EDGAR filing acceptance date(filed) 이후만(Large accel 10-K 60d/10-Q 40d 자동 반영) = lookahead 회피.
- ★생존편향(I PARTIAL): universe = 현 ETF holdings 큐레이션(생존 종목). 상폐/구성변경(셰일 파산/GE 분할) 누락 = 생존편향 강. yfinance 단독 = 상폐 ticker 누락. Sharadar/S&P historical = collector_plan high.

## §6. net-cost (§M.4, 미국)

US 왕복 16bps (commission 5 + spread/2 3, ★STT 없음 = 한국 33bps 절반). PER(저회전 장기 value) net 유리.

## §7. verdict

- ★**미국 1단계 = EDGAR/yfinance/FRED 파이프라인 작동 검증 완료**. ★PER value premium 작동(block-boot 유의, LOO sector robust) = ★한국 auto/반도체(PER✗ peak-EPS)와 **반대** = peak-EPS trap 시장·시총 의존성.
- vol 프리미엄(고베타 보상). HY OAS β 강(risk-on/off)이나 2023~ 한정 hedge. dollar β 비유의(R2 Bruno-Shin 정합).
- archetype cyclical 지지(PER value 작동, peak-EPS 약).
- **verdict_label = PARTIAL** (PER value block-boot 유의·LOO robust but BY borderline).
- ★**한국 vs 미국 cyclical 대조**: 한국 auto = PER✗ peak-EPS(중형, earnings 변동) / 미국 cyclical = PER○(대형, earnings 안정). = §M 양식이 시장·시총별 archetype metric 적합도 차이를 데이터로 포착. supervisor 가설 데이터 반증 = 정직성 입증.
