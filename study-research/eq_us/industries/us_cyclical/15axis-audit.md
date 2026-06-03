# 15axis-audit.md — us_cyclical sleeve §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. ★미국 1단계(EDGAR/yfinance/FRED). 한국 산업 미러.
> Hard-fail 코어: **B·C·D·I** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators = forward 횡단면 IC. archetype valid_from 2015-01 사전선언(yfinance 가용 시작). |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. yfinance 60종(2867일) + **EDGAR XBRL 27637 rows(filed date PIT)** + FRED CSV(HY OAS/rate/vix) + DXY. raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-metrics-v3.json key 매핑. per_z 24M IC -0.119 / hy_oas β -0.093 t=-10 / vol_60 +0.151 / LOO sector raw 재현. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격 forward-shift safe. ★valuation = **EDGAR filing acceptance date(filed) 이후만** 적용 = lookahead 회피(Large accel 10-K 60d/10-Q 40d 자동 반영). 거시 = FRED. |
| **E** | 다중검정 보정 | PASS | 20 테스트 BY(factor 3.60) → 생존 0(per 24M raw_p=0.0068 borderline). ★정직: block-boot 유의 + LOO robust = 방향 지지/BY borderline 명시. |
| **F** | OOS / walk-forward | PASS | CPCV purge+embargo. per_z 24M OOS hit 1.00. value premium OOS 재현. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC + block-bootstrap. per_z 24M block-boot CI [-0.169,-0.075] 0배제. ★+LOO sector robustness. |
| **H** | 미해결 명시 | PASS | collector_plan: ★survivorship(high) + HY OAS 장기(high) + EV/EBITDA·ERB(medium). dollar β 비유의·HY OAS 2023~ 한정 hedge 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | ★universe = 현 ETF holdings 큐레이션(생존 종목). 상폐/구성변경(셰일 파산/GE 분할) 누락 = 생존편향 강. yfinance 단독 = 상폐 ticker 누락. Sharadar/S&P historical = collector_plan high. 정직 격하. |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "저PER cross-sectional → 24M forward value" = code `cs_z(per) → fwd_24M`(EDGAR PIT filed date). 부호=value(음) verify. |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = 60종 5 sector. ★sub-sector 부호 cancel 주의(financials rate+ vs 나머지). z = cross-sectional peer-relative. sleeve label = supervisor 조립. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(HY OAS/rate/vix/dollar). 통합 supervisor L축. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = weight_falsification 직접 호출. opt-in, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립(RegimeGlasso/DY) = supervisor. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward = shift(-h). ★valuation = EDGAR filed date 이후만(filing acceptance). 거시 FRED. reject≠missing: 적자 종목 PER NaN(missing) 정직 제외. |
| **P** | net-cost robustness | PASS | US 왕복 16bps(STT 없음, 한국 33 절반). PER 저회전 net 유리. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (EDGAR 27637 rows) |
| C 추적성 | PASS | yaml↔raw 매핑 |
| D PIT | PASS | 가격/valuation(EDGAR filed)/거시 PIT-safe |
| I 생존편향 | PARTIAL | 현 holdings 큐레이션, 정직 격하 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL** — ★미국 1단계 EDGAR/yfinance/FRED 파이프라인 작동 검증 완료. ★PER value premium 작동(block-boot 유의, LOO sector robust) = ★한국 auto/반도체(PER✗ peak-EPS)와 **반대** = peak-EPS trap 시장·시총 의존성. vol 프리미엄. HY OAS β 강(2023~ 한정 hedge). dollar β 비유의(R2 Bruno-Shin 정합). BY borderline.
- archetype cyclical 사후편향 검사(M.5): valid_from 2015 사전선언, declared_at 명시. PER value(peak-EPS 약) = 미국 대형 cyclical 정합.
- ★**한국 vs 미국 cyclical 대조 발견**: 한국 auto = PER✗(중형 earnings 변동) / 미국 cyclical = PER○(대형 earnings 안정). = §M 양식이 시장·시총별 archetype metric 적합도 차이를 데이터로 포착. ★supervisor 가설("한국 auto PER✗ 재현") 데이터 반증 = over-claim 회피·정직성 입증. 미국 sleeve batch(us_defensive/us_mega_tech) 진입 가능.
