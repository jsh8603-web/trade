---
tags: [type/design, domain/inv, phase/II, track/T1, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-Inv
research: ./RESEARCH-T1-assumption-data-20260529.md
task: ./TASK-T1-assumption-research-20260529.md
note: 가정 라이프사이클 데이터·PIT 계층 설계. 코드레벨(파일:함수:계약). T2/T3 분담경계 준수.
---

# DESIGN-T1 — 가정 라이프사이클 데이터·PIT 계층 설계

> 범위 = **데이터·PIT·검증입력**(T1). 가정의 *판정통계*(T2)·*Card/Registry/Validator/UpdateController*(T3)는 경계 밖 — 이 문서는 그들이 딛고 설 "검증 가능한 PIT 데이터 + 측정 무결성 게이트 + 도출 provenance"만 설계.

## 0. 계층 위치 (자문 D 하향의존 — 데이터측만)
```
L_assume (T3)  AssumptionCard/Registry/Validator/UpdateController/DAG
   │ seam: 버전드 derivation fn + provenance ref
L_derive (T3)  f:{assumption_refs}→DerivedParameterSet
   ▼ (T1 데이터측이 떠받침 ↓)
─────────────────────────────────────────────
[T1] data_contract 게이트 → pit_query(AS OF) → 검증패널(생존편향 포함) → lineage(provenance jsonl) → online_fdr 상태영속
   ▼
L_signal  seed_builder/signal (기구현)
```
T1 산출은 **read-side 데이터 무결성 + provenance 영속**. validator 로직(holds 판정)은 T2/T3.

## 1. data contract 게이트 — `core/data/data_contract.py` (신규, Pandera MIT)

**위치**: pit_query AS OF 조회 **직후, AssumptionValidator 입력 직전**(자문 C-측정: 계약위반=가정검증 중단+측정 incident, "가정 틀림"과 분리).

```python
# core/data/data_contract.py
import pandera as pa
from pandera import Check, Column, DataFrameSchema

class ContractResult:        # 게이트 산출 (T3 validator 가 소비)
    passed: bool
    incidents: list[dict]    # {column, check, n_failed, sample} — 측정 incident
    as_of: datetime

PANEL_CONTRACT = DataFrameSchema({
    "knowable_from": Column("datetime64[ns]", nullable=False),
    "sys_time":      Column("datetime64[ns]", nullable=False),
    "effective_from":Column("datetime64[ns]", nullable=False),
    "per":       Column(float, Check.in_range(0, 200), nullable=True),
    "ev_ebitda": Column(float, Check.in_range(0, 100), nullable=True),
    # ... (도메인별 멀티플 범위)
}, checks=[
    Check(lambda df: (df.sys_time >= df.knowable_from).all(), name="sys_time_monotone"),
    Check(lambda df: (df.knowable_from >= df.effective_from).all(), name="knowable_after_effective"),
    Check(_vintage_lag_ok, name="vintage_lag"),     # knowable-effective ≤ max_filing_lag(sector)
    Check(_null_rate_ok, name="null_rate"),          # feature null률 ≤ θ
    Check(_pit_dedup, name="pit_append_idempotent"), # (firm,date,sys_time) 중복 0
])

def check_contract(panel: pd.DataFrame, as_of: datetime,
                   domain: str) -> ContractResult:   # domain∈{macro,equity,commodity}
    """게이트. passed=False 면 T3 validator 는 가정검증 중단 → 측정 incident 로그."""
```
- **domain별 schema 분기**: 거시(레짐지표 범위)·주식(멀티플)·상품(NAV괴리·롤수익률) 각자 Check 집합.
- 산출 `ContractResult.incidents` → T3 가 "측정 incident"로 분류(가정 기각 아님). gemini "expect_X_to_Y" 어휘 차용.

## 2. 3도메인 PIT 검증패널 (자문 A-1 생존편향, claude A-3)

**원칙**: 검증패널 = **as_of 당시 살아있던 전체 모집단**(이후 소멸 포함). 살아남은 것만 보면 가정이 실제보다 안정해 보임.

| 도메인 | 모집단 PIT 소스 | 생존편향 차단 | knowable_from |
|---|---|---|---|
| **거시** | FRED ALFRED vintage(`macro_vintage.py`) + 레짐 참조지표(금리/CPI/유가/달러) | **폐지 ETF·만기소멸 선물 시리즈 포함**(중단된 지표도 그 시점엔 유효) | ALFRED realtime_start |
| **주식** | `pit_panel`(이미 delist_flag/delist_ret/UniverseManager) | ✅ 기구현(상폐 포함) | filing_timestamp |
| **상품** | ETF NAV/iNAV, 선물 롤오버/컨탱고·백워데이션, 계절성, 재고 | **상장폐지 ETF·만기소멸 선물 계약 포함** | 공시/마감 시점 |

**현 panel_schema 충분성 판정**:
- 주식 = `delist_flag/delist_date/delist_ret` 충분.
- 거시·상품 = **부족** → 패널 스키마 확장 필요:
  - `instrument_kind` (equity|etf|future|macro_series) — 도메인 분기 키.
  - `lifecycle_status` (active|delisted|expired|discontinued) — 만기소멸/지표중단 표현(delist_flag의 일반화).
  - `lifecycle_date` (소멸/만기/중단일) — delist_date 일반화.
  - 상품 전용: `roll_yield`, `contango_flag`, `front_back_spread`, `seasonality_idx`, `inventory_level`(EIA/USDA).
  - 거시 전용: 기존 regime_id + `series_discontinued_at`.
- → **권고**: `panel_schema.py`에 `instrument_kind`/`lifecycle_status`/`lifecycle_date` 추가(delist_* 의 상위 일반화, 주식은 기존 매핑 보존=하위호환).

**상품 무료 소스(조사 필요·잠정)**: EIA(원유/가스 재고, 무료 API key)·USDA(농산물, 무료)·yfinance(ETF NAV 근사)·선물 롤오버는 연속물 합성 필요. → **확신<80%, Gemini Phase2 또는 자문 1회 추가 권장**(이연: N-T1-COMMODITY-SRC).

## 3. lineage / provenance — `core/data/lineage.py` (신규, OpenLineage 스펙)

**목적**: `seed.derived_from = [{assumption_id, version, derivation_fn_version}]` 체인을 PIT 재현+감사 가능하게 영속.

```python
# core/data/lineage.py
class ProvenanceRef:                 # 값객체 (자문 D-1, bipartite 다대다)
    assumption_id: str
    assumption_version: str
    derivation_fn_version: str

class LineageEvent:                  # OpenLineage facet 호환
    derived_id: str                  # seed/파라미터 id
    inputs: list[ProvenanceRef]      # 단수 아닌 리스트 (한 threshold가 멀티 가정 의존)
    knowable_from: datetime          # ★합성규칙 §4
    sys_time: datetime
    derivation_fn_version: str

def emit_lineage(event: LineageEvent, store_path: str) -> None:
    """jsonl append (서버 없이). bitemporal_store 패턴 재사용, 별도 스트림."""

def replay_provenance(derived_id: str, as_of: datetime) -> list[ProvenanceRef]:
    """as_of 시점 도출물의 입력 가정 체인 재구성 (PIT 감사)."""
```
- **seed_builder seam(additive)**: `Signal`에 `derived_from: Optional[list[ProvenanceRef]] = None` 추가 — 없으면 오늘과 100% 동일(하위호환). 자문 D-1.
- bitemporal_store.py를 라이브러리로 재사용(이벤트 섞지 않음, 별도 stream).

## 4. ★ knowable_from 합성규칙 (자문 D-4, lookahead 차단) — `pit_query` 강제

**규칙**: 도출물 `knowable_from ≥ max(입력들의 knowable_from) + 계산지연(Δ)`.
- 가정에서 도출한 파라미터는 "입력 가정들을 다 알게 된 시점 + 계산 시간" 이후에만 알 수 있음. 입력보다 일찍 knowable 하면 lookahead.

```python
# core/data/pit_query.py 에 추가
def synth_knowable_from(input_refs: list[ProvenanceRef],
                        input_knowables: list[datetime],
                        compute_lag: timedelta = timedelta(0)) -> datetime:
    return max(input_knowables) + compute_lag

# 교차일관성 불변식 (read-time, 자문 D-4):
def assert_referential_pit(seed, as_of, assumption_store) -> None:
    """활성 seed 의 모든 derived_from 은 그 as_of 에 활성이던 assumption 가리켜야.
    위반 = PIT 오염(미래/소멸 가정 참조) → ValueError."""
    for ref in seed.derived_from or []:
        if not assumption_store.is_active(ref.assumption_id, ref.assumption_version, as_of):
            raise ValueError(f"PIT 위반: seed {seed.id} → 비활성 assumption {ref}")
```
- 이 검사는 T3 assumption_store(있어야)에 의존 → T3와 **인터페이스 계약**: `assumption_store.is_active(id, version, as_of) -> bool`. T1은 검사 로직만, store는 T3.

## 5. online FDR 상태영속 — `core/data/online_fdr.py` (신규, 논문 구현)

**왜 데이터층**: "검정 시퀀스 + alpha-wealth"가 끝없는 재검정에도 noise 추격을 막는 상태 → **영속 필수**(세션 넘어 누적). 데이터 계층이 소유.

```python
# core/data/online_fdr.py
class AlphaWealthState:              # 영속 (jsonl, append-only, PIT)
    test_seq: int                    # 검정 시퀀스 번호
    alpha_wealth: float              # 현재 예산 (LORD++/SAFFRON)
    rejections: list[int]            # 기각된 검정 인덱스 (예산 회수용)
    as_of: datetime
    assumption_id: str               # 가정별 분리 (또는 전역 family)

def lord_pp(p_values: list[float], alpha: float, state: AlphaWealthState) -> list[bool]:
    """LORD++ (Javanmard&Montanari 2018). 기각 시 일부 예산 회수."""

def saffron(p_values: list[float], alpha: float, lambda_: float,
            state: AlphaWealthState) -> list[bool]:
    """SAFFRON (Ramdas 2018). candidate 기반 적응 예산. 부활 가정 다중검정 차단."""

def persist_state(state: AlphaWealthState, path: str) -> None:  # append-only
def load_state(assumption_id: str, as_of: datetime, path: str) -> AlphaWealthState:  # PIT
```
- **promotion_gate.bh_fdr 대체경로**: batch BH = 고정 family. online = 스트리밍. T3 UpdateController가 `lord_pp/saffron` 호출, T1은 알고리즘+상태영속 제공.
- **부활 가정**(자문 C): 죽은 가정 재검정도 alpha 예산 소모 → 50번 재검정 우연통과를 SAFFRON이 자동 차단.

## 6. 분담 경계 인터페이스 (T1↔T2↔T3)
- **T1→T3**: `ContractResult`(측정게이트), `replay_provenance()`(감사), `AlphaWealthState`+`lord_pp/saffron`(FDR), `synth_knowable_from`/`assert_referential_pit`(PIT 합성·검사).
- **T1←T3**: `assumption_store.is_active(id,ver,as_of)->bool`(referential PIT 검사용 — T3 제공).
- **T1↔T2**: 검증패널(생존편향 포함 DataFrame) 제공 → T2가 regime-conditional 판정통계(SPRT/CUSUM/prequential) 수행. T1은 패널+contract까지.
- **detector 공유**(자문 D-6): `rule_observer.py`의 PageHinkley/psi → `core/observability/detectors.py` 추출, T1 contract(KS)·T2 validator 양쪽 import.

## 7. 신규/확장 파일 요약
| 파일 | 신규/확장 | 내용 |
|---|---|---|
| `core/data/data_contract.py` | 신규 | Pandera schema + domain별 Check + ContractResult |
| `core/data/lineage.py` | 신규 | ProvenanceRef/LineageEvent + emit/replay (OpenLineage 스펙) |
| `core/data/online_fdr.py` | 신규 | LORD++/SAFFRON + AlphaWealthState 영속 |
| `core/data/pit_query.py` | 확장 | synth_knowable_from + assert_referential_pit |
| `core/structure/panel_schema.py` | 확장 | instrument_kind/lifecycle_status/lifecycle_date (delist_* 일반화) |
| `core/rules/seed_builder.py` | 확장(additive) | Signal.derived_from (Optional, 하위호환) |
| `core/observability/detectors.py` | 신규(추출) | PageHinkley/psi/KS 공유 |

**신규 의존 = Pandera(MIT) 1개.** 나머지 우리 코드 재사용 + 논문 구현.
