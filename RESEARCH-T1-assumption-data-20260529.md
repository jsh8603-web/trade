---
tags: [type/research, domain/inv, phase/II, track/T1, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-Inv
task: ./TASK-T1-assumption-research-20260529.md
consult: [.consult-R1-claude.txt, .consult-R1-gemini.txt]
archive: ~/.claude/docs/archive/research-raw/assumption-priorart-phase1-20260529.txt
design: ./DESIGN-T1-assumption-data.md
note: 가정 라이프사이클 데이터·PIT 계층 prior art 실조사. 이름 베끼기 X — 라이선스·이식비용·우리 적용가능성 판정.
---

# RESEARCH-T1 — 가정 라이프사이클 데이터·PIT prior art 조사

> 조사 방법: Gemini Pro Phase1(라이선스/유지보수 실조사, archive 보존) + claude/gemini R1 자문 + 우리 코드 정밀 매핑(subagent). 기준 = **우리 시스템 실제 이식 가능성** (in-process pandas·Windows·credential-free·기존 모듈 재사용).

## 0. 결론 먼저 (TL;DR)
- **신규 의존 최소화**가 핵심 — 우리 PIT 패널이 이미 pandas DataFrame이고, `rule_observer.py`가 PSI/PageHinkley를, `bitemporal_store.py`가 append-only 이벤트를, `promotion_gate.py`가 BH FDR을 이미 보유. **대부분의 prior art는 "알고리즘/스펙만 차용"하고 본체는 우리 코드 재사용**이 최적.
- 채택 3: **Pandera(MIT)** = data contract 게이트 / **OpenLineage 스펙(Apache, 서버 없이)** = provenance jsonl / **onlineFDR 알고리즘**(논문서 직접 구현, Python 포트 부재).
- 기각: GE(heavy)·Soda(SQL지향)·PyDeequ(Spark)·Marquez(서버)·drift 라이브러리 전체(TF/PyTorch heavy, 알고리즘만 참조).
- **통합 OSS 부재 확정** — registry+governed-change+regime-conditional을 묶은 프로젝트 없음. 통합 자체가 우리 기여.

## 1. Data Contract / Expectation (2-A.1)

| 도구 | License | weight | Windows pip | 판정 | 근거 |
|---|---|---|:---:|---|---|
| **Pandera** | **MIT** | light | ✅ | ✅ **채택** | pandas/polars schema, 데코레이터·`DataFrameSchema`. 우리 패널이 DataFrame이라 in-process 0마찰. `Check`로 도메인 expect 선언(멀티플 범위·null률·vintage 지연). 의존 가벼움(pandas만). |
| Great Expectations | Apache-2.0 | medium-heavy | ✅ | ❌ 기각 | DataContext/datasource/checkpoint 등 무거운 추상. 별도 store·yaml config. **in-process pandas 검증엔 과함**. expect 어휘는 참조(`expect_column_values_to_be_between`). |
| Soda Core / SodaCL | Apache-2.0 | medium | ✅ | △ 보류 | SodaCL = SQL/warehouse 지향 DSL. 우리는 warehouse 없음(parquet/jsonl). |
| dbt contracts/tests | — | — | ❌ | ❌ 기각 | SQL/warehouse 전용, in-process pandas 아님. |
| PyDeequ | Apache-2.0 | heavy | ❌ | ❌ 기각 | **Spark JVM 필수**. 우리 스택(pandas/pyarrow) 무관. |

**무엇을 expect로 선언하나** (우리 PIT 패널 기준):
- 멀티플 범위: `per ∈ (0, 200)`, `ev_ebitda ∈ (0, 100)` — 음수/극단 = 측정 깨짐.
- null률: feature 컬럼별 null 비율 ≤ θ (벤더 파이프 단절 탐지).
- **vintage 지연**: `knowable_from - effective_from ≤ max_filing_lag`(섹터별) — 비정상 지연 = 데이터 소스 incident.
- bitemporal 단조성: `sys_time ≥ knowable_from`(정정 아닌데 역전 = 오류), `knowable_from ≥ effective_from`.
- **PIT 불변식**: 같은 (firm,date,sys_time)에 중복 row 0 (append 멱등성).

→ **권고**: `core/data/data_contract.py` 에 Pandera `DataFrameSchema` + 도메인별 `Check`. AssumptionValidator **앞단** 게이트(자문 C-측정: 계약위반=가정검증 중단+측정 incident).

## 2. Lineage / Provenance (2-A.2)

| 도구 | License | 판정 | 근거 |
|---|---|---|---|
| **OpenLineage** | Apache-2.0, light | ✅ **스펙만 채택** | RunEvent/Job/Dataset facet 스펙이 표준. **서버(Marquez) 없이** facet JSON을 우리 jsonl에 직접 기록 → PIT 재현+감사 공짜. python client는 emit 용이나 우리는 스펙 형태만 차용(파일 append). |
| Marquez | Apache-2.0, heavy | ❌ 기각 | **Java + Postgres 서버**. 운영 부담 과대, credential-free 원칙 위반. |

→ **권고**: `core/data/lineage.py` — `seed.derived_from = [{assumption_id, assumption_version, derivation_fn_version}]` 체인을 OpenLineage-호환 facet으로 jsonl append. `bitemporal_store.py` 패턴 재사용(별도 스트림). 자문 D-1/D-4 정합.

## 3. Online / Streaming FDR (2-A.3) — ★자문 TOP1

| 도구 | License | 판정 | 근거 |
|---|---|---|---|
| **onlineFDR** (R, Bioconductor) | Artistic-2.0 | ⚠️ **알고리즘 직접 구현** | LORD++/SAFFRON/ADDIS/alpha-investing. **유지되는 Python 포트 부재(2026 확인)**. R 의존 도입은 과함. 논문서 직접 구현(LORD++ ~30줄, SAFFRON ~40줄). |
| Python 포트 | — | ❌ 없음 | 2026 기준 canonical 유지 패키지 없음 확정. |

**왜 필수**(자문): 가정 N개 × 연속 모니터링 = 시간·가정 다중검정. `promotion_gate.py:bh_fdr()`는 **batch BH**(고정 family 가정) → 스트리밍에 틀림. online FDR = alpha-wealth 상태로 각 검정이 예산 소모, 기각 시 일부 회수 → **끝없이 재검정해도 noise 추격 차단** = 사용자의 "합리적 이유 없이 자주 바뀌면 안 됨"의 수학적 보장. **부활 가정의 다중검정 함정**(죽은 가정 50번 재검정→우연 통과)도 alpha-investing이 자동 차단.

→ **권고**: `core/data/online_fdr.py` — LORD++ + SAFFRON 구현 + **alpha-wealth 상태 영속**(가정 재검정 끝없어도 누적 예산 추적). 논문: Javanmard&Montanari 2018, Ramdas 2018(SAFFRON). 상태 스키마는 DESIGN 문서 §online_fdr.

## 4. Label-free Drift / Performance (2-A.3)

| 도구 | License | weight | 판정 | 근거 |
|---|---|---|---|---|
| NannyML | Apache-2.0 | medium-heavy | △ 알고리즘 참조 | CBPE/DLE = ground-truth 없이 성능추정. 개념 차용, 본체 무거움. (Soda 인수설=가설, Apache 유지). |
| Evidently | Apache-2.0 | medium-heavy | △ 참조 | drift report. 우리는 report UI 불필요. |
| whylogs | Apache-2.0 | medium | △ 참조 | 데이터 프로파일링/로깅. |
| Alibi-Detect | Apache-2.0 | **heavy(TF/PyTorch)** | ❌ 본체 기각 | KS/MMD/Mahalanobis 알고리즘만 참조. **TF/PyTorch 의존 과대**. |

**우리 현황**: `rule_observer.py`가 이미 `psi()`(Population Stability Index)·`PageHinkley`·`near_zero_mass` 보유. **drift 라이브러리 신규 도입 불필요** — KS test만 scipy로 추가(가정 holds의 label-free 추정).

→ **권고**: `rule_observer.py`의 detector(PageHinkley/psi)를 `core/observability/detectors.py` 공유 모듈로 추출(자문 D-6), AssumptionValidator가 가정 예측량 잔차에 재사용 + KS(scipy.stats.ks_2samp) 추가. drift 라이브러리 의존 0.

## 5. 통합 OSS 부재 (확정)
registry + governed change-control + quant regime-conditional validation을 묶은 단일 OSS = **없음**(Gemini+claude 양측 확인). 구성요소(Git=변경통제, GE=검증, 워크플로우 엔진=조건부)는 있으나 **퀀트 가정 거버넌스 통합은 우리 기여 영역**. SR 11-7(Fed/OCC 2011 모델리스크 거버넌스)이 철학적 표준 — Registry+Validator+UpdateController가 SR 11-7의 ongoing monitoring+outcomes analysis+change control에 거의 1:1 대응.

## 6. 이식 비용 종합 (신규 코드 vs 의존)
| 컴포넌트 | 신규 의존 | 신규 코드 | 재사용 |
|---|:---:|---|---|
| data contract 게이트 | Pandera(MIT, light) | `data_contract.py` schema+Check | pit_query 앞단 |
| lineage | 없음(스펙만) | `lineage.py` facet jsonl | bitemporal_store 패턴 |
| online FDR | 없음(논문 구현) | `online_fdr.py` LORD++/SAFFRON | promotion_gate bh_fdr 대체경로 |
| drift detector | scipy(기존) | KS 추가 | rule_observer detectors 추출 |
**총 신규 의존 = Pandera 1개(MIT, light)**. 나머지 전부 우리 코드 재사용 또는 논문 직접 구현. → 사용자 "코드 일부만 만들고 끝" 불만 대응: 깊은 통합(기존 5개 모듈에 seam) + 의존 최소.

## 7. 미해결 (다음 단계)
- **상품(commodity) 무료 데이터소스 미조사** — ETF NAV/iNAV, 선물 롤오버/컨탱고, 계절성, 재고(EIA/USDA). DESIGN 작성 시 Gemini Phase2 또는 자문 1회 추가(확신<80%).
- onlineFDR LORD++/SAFFRON 구체 수식 검증 = 구현 시 논문 재확인.
