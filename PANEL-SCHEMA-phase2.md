---
tags: [type/contract, domain/inv, phase/II, track/T1]
date: 2026-05-29
owner: T1 (inv 세션)
consumers: [T2 button, T3 btn-Codlearn]
status: 확정 v1 (계약 동결 — 변경 시 3트랙 합의 필요)
split_index: ./SPLIT-INDEX-phase2.md
spec: ./SPEC-T1-data-pit.md
---

# PANEL SCHEMA — Phase2 bitemporal PIT 패널 계약 (T1 산출)

> T1(데이터·PIT) 이 T2·T3 에 제공하는 **데이터 계약 SSOT**. 두 트랙은 이 schema 를 fixture parquet 으로 mock 해 병렬 개발한다.
> ⛔ 계약 동결 — 컬럼명/dtype/PIT 의미론 변경은 T1·T2·T3 3트랙 합의 필요. (불변식 ②: append-only, mutate 0)

## 0. 계약 의존 그래프 (4 계약)

| # | 계약 | producer | consumer | 상태 |
|---|---|---|---|---|
| **계약0** | `as_of_resolver(...)` canonical as_of 의미론 | **T3** (btn-Codlearn) | T1·T2·T3 공통 | ⏳ T3 구현 대기 — T1 은 seam 만 비워둠 |
| **계약1** | `panel/{market}/{vintage}.parquet` (본 문서) | **T1** (inv) | T2·T3 | ✅ 확정 v1 |
| 계약2 | `StructureModel.cheapness_z(firm,sector,date,as_of)->float` | T2 | T3 | (T2 spec) |
| 계약3 | `ArchetypeCard(archetype,primary_metric,companion_signals[],value_trap_guards[])` | T2 | T3 | (T2 spec) |

**⚠️ 계약0 선결 의존 (T3 R7 보완, 2026-05-29)**: bitemporal store 의 AS OF 쿼리 + 패널의 `knowable_from <= as_of` 필터는 **T3 이 제공할 canonical `as_of_resolver` 시그니처를 경유**한다. transaction-time as_of 해석이 트랙마다 갈리면 reconcile 발산(claude R7). T1 은 as_of 해석을 자체 확정하지 않고, `core/data/pit_query.py` 에 **adapter seam**(`_resolve_as_of` 주입점)만 두고 T3 resolver 도착 시 wire 한다. 그 전까지는 잠정 식별 함수(`lambda x: x`, naive `<=` 비교)로 동작하되 **모든 호출이 단일 seam 경유**라 교체 1곳.

---

## 1. 파일 레이아웃

```
panel/
  KR/{vintage}.parquet      # 한국 (KRW, KRX 종목)
  US/{vintage}.parquet      # 미국 (USD, EDGAR 종목)
  _manifest/{vintage}.json  # content-hash·row수·소스 vintage·빌드시각
```

- `market` ∈ {`KR`, `US`} — 시장별 분리(T1-5 이질성: French49 섹터 ≠ 한국, market FE 는 T2 몫).
- `vintage` = 패널 빌드 산출의 **content-hash**(sha256[:16]). 동일 입력 → 동일 vintage(재현성). manifest 에 소스별 vintage(FRED ALFRED realtime, DART rcept 최대일 등) 기록.
- ⛔ 통화 환산 없음 — `currency` 컬럼 표기만, FX 는 상위(H26) 책임.

## 2. 컬럼 스펙 (parquet, pyarrow)

행 단위 = **(firm, date)** 관측 1개. date=월말(month-end) 관측 그리드 기본.

### 2.1 bitemporal 3축 (PIT 핵심)
| 컬럼 | dtype | 의미 |
|---|---|---|
| `effective_from` | `timestamp[us]` | 회계기간/사실이 **적용되기 시작한** 시점 (fiscal period end 기준) |
| `knowable_from` | `timestamp[us]` | 그 사실을 **알게 된** 시점 = filing/공시 시각. **PIT 게이트 키** (`Fundamentals.filing_timestamp` 매핑) |
| `sys_time` | `timestamp[us]` | 이 **값 버전이 알려진/기록된** 시점. 기본 = `knowable_from`(정정 없으면 알게된 즉시 기록). **silent revision 방어**(R8): DART/EDGAR 과거 조용한 수정 시 정정본은 `sys_time = 정정 시점 (≠ knowable_from)`, 옛 row 불변 + 새 sys_time row append. ⚠️ build 시각을 쓰면 안 됨(2026 빌드 패널로 2024 백테스트 전부 막힘) |

> **silent revision 시나리오**: 기업이 과거 재무를 조용히 정정 → knowable_from(원 공시일)은 같지만 값이 다른 새 row 가 다른 sys_time 으로 들어옴. AS OF 쿼리가 `sys_time <= as_of` 중 최신을 골라야 "as_of 시점에 우리가 실제로 알던 값"이 재현된다. sys_time 분리 안 하면 미래 정정값이 과거로 누수(PIT 오염).

### 2.2 식별/분류 (시변)
| 컬럼 | dtype | 의미 |
|---|---|---|
| `firm` | `string` | ticker (KR=6자리 코드, US=심볼) |
| `date` | `timestamp[us]` | 관측 기준일(월말) |
| `sector` | `string` | as-of 섹터 분류값 |
| `sector_scheme` | `string` | `GICS` \| `KRX` \| `FRENCH49` |
| `sector_valid_from` | `timestamp[us]` | 이 섹터 분류가 유효해진 시점 (GICS 재분류 시계열 단절 방어 — 시변) |

### 2.3 features (filing-lagged, `Fundamentals` 매핑)
모두 `double` nullable. `knowable_from` 이 이미 filing-lag 반영(공시일 기준).

`revenue`, `operating_income`, `net_income`, `ebit`, `ebitda`, `free_cash_flow`, `depreciation_amortization`, `capital_expenditure`, `interest_expense`, `total_debt`, `cash_and_equivalents`, `shareholders_equity`, `book_value`, `working_capital`, `outstanding_shares`, `earnings_growth`, `revenue_growth`, `book_value_growth`, `return_on_invested_capital`, `beta`

| 메타 컬럼 | dtype | 의미 |
|---|---|---|
| `fiscal_period` | `string` | "2023Q4" / "2023FY" |
| `filing_source` | `string` | `dart_xbrl` \| `edgar_xbrl` (⛔ `restated` 는 패널 적재 거부 — `filter_pit_fundamentals` 로직 재사용) |
| `currency` | `string` | `KRW` \| `USD` |
| `is_pit_clean` | `bool` | `Fundamentals.is_pit_clean()` 결과 (as_reported + DART/EDGAR XBRL) |

### 2.4 multiple (raw — T2 가 cheapness_z 로 변환)
| 컬럼 | dtype | 의미 |
|---|---|---|
| `per` / `pbr` / `ev_ebitda` / `ps` | `double` nullable | raw 멀티플 (price/quote × fundamentals). **싸다 판정 아님** — T2 structure model 잔차 입력 |
| `multiple_def_version` | `string` | 멀티플 정의 버전 (GAAP/non-GAAP 40분기 drift 고정, R8 바닥). 예: `gaap_2023a` |

### 2.5 survivorship (T1-3, 상폐 포함 PIT)
| 컬럼 | dtype | 의미 |
|---|---|---|
| `delist_flag` | `bool` | 상장폐지 여부 |
| `delist_date` | `timestamp[us]` nullable | 상폐일 (`UniverseManager` 백테스트 universe 포함 근거) |
| `delist_ret` | `double` nullable | 상폐 수익률 (Shumway −0.30~−1.00, look-ahead 없이 마지막 거래일 기준) |

### 2.6 regime (T2 producer — T1 은 자리만)
| 컬럼 | dtype | 의미 |
|---|---|---|
| `regime_id` | `int32` nullable | 거시 레짐 id. **T1 은 NULL 로 발행**, T2 가 regime_classifier 산출을 PIT-join |
| `regime_model_version` | `string` nullable | 레짐 모델 버전 (dormant rule 부활 매트릭스 키, E축) |

### 2.7 상태 플래그 (KR 전용 PIT, US 는 NULL)
| 컬럼 | dtype | 출처 |
|---|---|---|
| `is_watchlist`, `is_invest_warn`, `is_invest_risk`, `is_halt`, `is_delisting_risk`, `is_qualified_audit` | `bool` | `KrxStatusProvider.get_status_snapshot(ticker, as_of)` (jsonl PIT 재구성) |

---

## 3. PIT 조회 규약 (T2·T3 필독)

```python
# core/data/pit_query.py (T1 제공)
def query_as_of(panel, firm, date, as_of) -> Row | None:
    """as_of 시점에 알 수 있었던 단 하나의 row 를 반환.
    AS OF 의미론 = 계약0 (T3 as_of_resolver) 경유.
    """
    resolved = _resolve_as_of(as_of)           # ⏳ 계약0 seam (T3 wire 전까지 항등)
    rows = panel[(panel.firm == firm)
                 & (panel.date == date)
                 & (panel.knowable_from <= resolved)   # ① filing-lag PIT 게이트
                 & (panel.sys_time <= resolved)]        # ② silent revision 방어
    return rows.sort_values("sys_time").iloc[-1]        # 최신 sys_time = "그때 알던 값"
```

- **T2/T3 는 반드시 `query_as_of` (또는 동급 AS OF 인터페이스) 만 통해 패널 조회.** raw parquet 직접 필터링 = PIT 우회 = 금지. DB 가 PIT 강제.
- **불변식 매핑**: ②rollback=row append만 → `sys_time` 신규 row(옛 row mutate 0). ①position=entry version 고정 → `multiple_def_version`+`regime_model_version` 동결.

## 4. T1 빌드 파이프라인 (구현 대상, Phase 2)

```
[기존 provider 재사용]
DartXbrlProvider / EdgarXbrlProvider → Fundamentals (filing_timestamp, RESTATED 거부)
KrxStatusProvider / KrxUniverseProvider → 상태 플래그 + universe (상폐 포함)
MacroVintageProvider (FRED ALFRED) → regime 입력 보조 (T2 가 소비)
Damodaran xls / French49 → US 섹터 멀티플 vintage (T1 신규 수집)
corp action 전처리 → 액면분할·자사주 멀티플 보정 (T1 신규)
          │
          ▼
core/data/pit_panel.py (T1 신규 조립층)
  · filter_pit_fundamentals(as_of) 재사용 (RESTATED 제외, knowable_from<=as_of)
  · UniverseManager 재사용 (survivorship: 상폐 포함)
  · bitemporal 3축 부여 (sys_time = build time, append-only)
  · → panel/{market}/{vintage}.parquet + _manifest
```

## 5. T1 미구현 → 잠정 동작 (mock 안내)
- **계약0 as_of_resolver**: T3 도착 전 = naive `<=` 항등. T2/T3 fixture 개발엔 영향 없음(동일 의미).
- **regime_id / regime_model_version**: T1 = NULL 발행. T2 가 채움.
- **Damodaran/French49 US 멀티플 vintage**: 미수집 구간은 `per/pbr/...` NULL. KR(pykrx 스냅샷 자체구축)이 1차.
