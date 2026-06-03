# 15axis-audit.md — bio(바이오) §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. battery/financial/consumer 미러.
> Hard-fail 코어: **B·C·D·I** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators = forward 횡단면 IC. regime = ex-ante XBI yoy. archetype valid_from 2019 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 38종 + yfinance(XBI/VIX/factors) + **DART 948 rows(2019~)** + FDR. raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-metrics-v3 / valuation-v3 / cross-v3.json key 매핑. vol_60 IC -0.078 = indicators.vol_60__1M_PEAD. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격 forward-shift safe. valuation = DART rcept_dt 공시일 이후만. regime = ex-ante XBI yoy. |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY → vol_60 raw_p=0.0033 미세 미달(α/16=0.0031). valuation 8테스트 BY → 생존 0. raw p 보고. |
| **F** | OOS / walk-forward | PASS | CPCV purge+embargo. vol_60 CPCV 0.87, per_z 0.80-0.87. value/저변동성 OOS 재현. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC + block-bootstrap. vol_60 block-boot CI 0배제. per_z 6M block-boot 0배제. |
| **H** | 미해결 명시 | PASS | collector_plan: ★파이프라인/임상 데이터(event_driven primary, high) + R&D burn / PIT 멤버십(상폐 강). |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | ★bio = 임상 실패→상폐·관리종목 잦음 = 생존편향 ★강. FDR 현재 스냅샷(생존) → delisted bio 누락 = IC 상향 편의 우려. 38종 中 7종 부분 이력. PIT 멤버십=collector_plan high. 정직 격하. |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "저변동성 → 1M forward / 흑자 저PER → 6M" = code `vol_60 z → fwd_1M` / `per_z(흑자) → fwd_6M`. 부호=저변동성/value(음) verify. |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = bio 38종(pharma/novel_drug/biosimilar). ★novel_drug(적자, 멀티플 무효) vs pharma(흑자, value) = 2 sub-group 부호 분리 = §1.6 정합. z = peer-relative. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(VIX 유의). 통합 supervisor L축. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = weight_falsification 직접 호출. opt-in, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward = shift(-h). valuation rcept_dt 이후. regime ex-ante XBI. reject≠missing 구분. ★적자 종목 PER = NaN(missing) 정직 제외. |
| **P** | net-cost robustness | PASS | 왕복 33bps. ★저변동성(1M) 회전 높음 → net haircut 주의 명시. 흑자 PER(중기) 회전 낮음. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 948 rows) |
| C 추적성 | PASS | yaml↔raw 매핑 |
| D PIT | PASS | 가격/valuation/regime PIT-safe |
| I 생존편향 | PARTIAL | ★bio 상폐 잦음, 생존편향 강, 정직 격하 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하 → hard-fail 아님). ★단 bio 생존편향은 타 산업보다 심함 명시.

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL** — ★event_driven 부분 입증: 멀티플(PER) 흑자 한정 작동 + 적자 신약(36%) 무효 = 멀티플 부적합. 저변동성(임상 risk) NW 유의(BY 미세 미달). 진짜 신호 = 파이프라인/임상(미측정, collector_plan).
- archetype event_driven 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시. 멀티플 부적합이 event_driven 정합.
- ★**4 archetype 분기 완성**: battery(cyclical momentum) / financial(spread_driven regime-conditional) / consumer(asset_stable valuation) / bio(event_driven 변동성+이벤트, 멀티플 부분) = 산업별 유효 신호·risk factor·데이터 양식 전부 상이 = 동적가중 정당화 + event_driven 멀티플 부적합 데이터 입증. ★생존편향은 bio 가 산업별 최악(임상 실패 상폐) — 6산업 batch 시 bio universe PIT 멤버십 우선순위.
