"""core/structure/panel_schema.py — T2 패널 schema 계약 + R8 바닥 2 선결.

이 모듈은 두 가지를 고정한다.

1. **인터페이스 계약 #1** (T1 → T2/T3): bitemporal 패널 parquet 의 컬럼 스키마.
   T1(btn-Inv)이 실제 패널을 생산하기 전까지 T2/T3 는 이 스키마의 fixture 로 병렬 개발.

2. **R8 바닥 2** (claude R8, 안 풀면 cheapness_z 가 허상이 되는 최하층):
   - ① 종속변수 비정상성: multiple 정의(GAAP/non-GAAP)가 40분기에 걸쳐 drift →
     `MultipleDefinition` 버전 고정 + 각 row 가 어느 정의로 계산됐는지 `multiple_def_version` 기록.
   - ② 생존편향: 상장유지 기업만으로 적합하면 "정상 multiple" 이 생존-조건부가 되어
     value_trap_guard 가 추정기와 정합하지 않는 사후패치가 된다 → delisted/M&A/파산 기업을
     **적합 표본에 포함**(delist_flag + delist_ret). 구조모델이 "죽음"을 봐야 한다.

★ cheapness_z 의 부호 규약: `(E[multiple] − actual) / σ_resid` 가 아니라 본 시스템은
  `(actual − E[multiple]) / σ_resid` 를 쓴다 → **음수 클수록 저평가** (actual 이 기대보다 낮음).
  SPEC 의 `(E−actual)` 는 부호만 반대인 동치 표기이며, T3 소비 계약은 "음수=싸다" 로 고정.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. 패널 컬럼 스키마 (계약 #1)
# ---------------------------------------------------------------------------

# 식별·시간 (bitemporal)
COL_FIRM = "firm"                    # 종목 식별 (ticker)
COL_SECTOR = "sector"                # as-of 섹터 (GICS/French industry, PIT — 재분류 시점 반영)
COL_DATE = "date"                    # 관측 분기말 (valuation as-of 후보)
COL_KNOWABLE_FROM = "knowable_from"  # 이 row 가 알 수 있게 된 시점 (filing_timestamp). PIT: knowable_from ≤ as_of
COL_REGIME = "regime_id"             # regime PIT id (T2-5 / regime_classifier 산출)

# 종속변수 (R8 ①)
COL_MULTIPLE = "multiple"            # 종속변수 멀티플 (정의는 multiple_def_version 으로 고정)
COL_MULT_DEF_VER = "multiple_def_version"  # 어느 MultipleDefinition 으로 계산됐는지 (drift 추적)

# 생존편향 (R8 ②)
COL_DELIST_FLAG = "delist_flag"      # 이 시점 이후 상폐/M&A/파산 했는가 (bool)
COL_DELIST_RET = "delist_ret"        # 상폐 수익률 (Shumway, 파산 −30~−100%; 생존이면 NaN)

# 드라이버 (filing-lagged features) — 섹터·archetype 마다 다름. 패널엔 prefix "drv_" 로.
DRIVER_PREFIX = "drv_"

# 필수 비-드라이버 컬럼
REQUIRED_COLUMNS = (
    COL_FIRM, COL_SECTOR, COL_DATE, COL_KNOWABLE_FROM, COL_REGIME,
    COL_MULTIPLE, COL_MULT_DEF_VER, COL_DELIST_FLAG, COL_DELIST_RET,
)


def driver_columns(panel: pd.DataFrame) -> list[str]:
    """패널에서 드라이버 컬럼(prefix DRIVER_PREFIX)만 추출."""
    return [c for c in panel.columns if c.startswith(DRIVER_PREFIX)]


def validate_panel(panel: pd.DataFrame) -> list[str]:
    """패널이 계약 #1 + R8 을 충족하는지 검사. 위반 메시지 리스트(빈 리스트=PASS)."""
    problems: list[str] = []
    for col in REQUIRED_COLUMNS:
        if col not in panel.columns:
            problems.append(f"필수 컬럼 누락: {col}")
    if not driver_columns(panel):
        problems.append(f"드라이버 컬럼(prefix '{DRIVER_PREFIX}') 0개 — 구조모델 입력 없음")
    # R8 ②: 적합 표본에 상폐 기업이 포함돼야 함 (전부 생존이면 생존편향)
    if COL_DELIST_FLAG in panel.columns and not panel[COL_DELIST_FLAG].any():
        problems.append("R8② 위반 의심: delist_flag 가 전부 False — 생존편향 (상폐 표본 부재)")
    # R8 ①: 멀티플 정의 버전이 기록돼야 함
    if COL_MULT_DEF_VER in panel.columns and panel[COL_MULT_DEF_VER].isna().all():
        problems.append("R8① 위반: multiple_def_version 전부 NaN — 정의 drift 추적 불가")
    return problems


# ---------------------------------------------------------------------------
# 1b. 멀티자산 확장 컬럼 (IA-4 — equity 계약에 ★추가만, 기존 불변)
# ---------------------------------------------------------------------------
# 기존 REQUIRED_COLUMNS(equity 중심)는 그대로 두고, 멀티자산(ETF/commodity/crypto/macro/fx)
# 패널이 실어야 할 자산 메타데이터를 별도 옵션 컬럼 + 별도 검증으로 추가. 기존 T2 equity
# 경로는 byte-동일(이 함수 호출 안 하면 영향 0).

COL_INSTRUMENT_KIND = "instrument_kind"   # {equity,etf,commodity,crypto,macro_series,fx}
COL_LIFECYCLE_STATUS = "lifecycle_status" # {active,delisted,expired,discontinued,liquidated}
COL_TRADABILITY = "tradability"           # bool — AUM/volume floor 충족(직교: zombie/halt 분리)
COL_COVERAGE_START = "coverage_start"     # 데이터 커버리지 시작(생존편향/backfill 경계)
COL_INCEPTION_DATE = "inception_date"     # 상품 출시일(coverage_start 와 구분)
COL_LIVE_TRACKED = "live_tracked"         # bool — 실시간 추적 vs index_backfilled
COL_TICK_SIZE = "tick_size"               # 호가 단위(gemini R3)
COL_MULTIPLIER = "multiplier"             # 계약 승수(선물/옵션)

INSTRUMENT_KINDS = frozenset(
    {"equity", "etf", "commodity", "crypto", "macro_series", "fx"})
LIFECYCLE_STATUSES = frozenset(
    {"active", "delisted", "expired", "discontinued", "liquidated"})

INSTRUMENT_COLUMNS = (
    COL_INSTRUMENT_KIND, COL_LIFECYCLE_STATUS, COL_TRADABILITY,
    COL_COVERAGE_START, COL_INCEPTION_DATE, COL_LIVE_TRACKED,
    COL_TICK_SIZE, COL_MULTIPLIER,
)


def validate_instrument_columns(panel: pd.DataFrame) -> list[str]:
    """멀티자산 메타 컬럼 검증(있을 때만). instrument_kind/lifecycle 값 범위 + tradability⊥lifecycle.

    equity 전용 패널엔 이 컬럼들이 없을 수 있다 → 없으면 skip(빈 리스트). 있으면 값 검증.
    tradability(거래가능)는 lifecycle(존속)과 **직교** — active 인데 거래불가(zombie/halt) 가능.
    """
    problems: list[str] = []
    if COL_INSTRUMENT_KIND in panel.columns:
        bad = set(panel[COL_INSTRUMENT_KIND].dropna().unique()) - INSTRUMENT_KINDS
        if bad:
            problems.append(f"instrument_kind 미정의 값: {sorted(bad)} (허용={sorted(INSTRUMENT_KINDS)})")
    if COL_LIFECYCLE_STATUS in panel.columns:
        bad = set(panel[COL_LIFECYCLE_STATUS].dropna().unique()) - LIFECYCLE_STATUSES
        if bad:
            problems.append(f"lifecycle_status 미정의 값: {sorted(bad)} (허용={sorted(LIFECYCLE_STATUSES)})")
    # coverage_start ≤ knowable 경계 권고(backfill 경계): coverage_start 가 inception 보다 빠르면 의심
    if COL_COVERAGE_START in panel.columns and COL_INCEPTION_DATE in panel.columns:
        cs = pd.to_datetime(panel[COL_COVERAGE_START], errors="coerce")
        inc = pd.to_datetime(panel[COL_INCEPTION_DATE], errors="coerce")
        if (cs < inc).any():
            problems.append("coverage_start < inception_date 행 존재 — backfill 경계 의심(상장 前 데이터)")
    return problems


# ---------------------------------------------------------------------------
# 2. R8 ① — multiple 정의 버전 고정
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MultipleDefinition:
    """멀티플의 회계 정의를 버전으로 고정 (R8 ①, GAAP/non-GAAP drift 방지).

    같은 "EV/EBITDA" 라도 EBITDA 가 stock-comp 을 빼는지(adjusted/non-GAAP) 여부가
    40분기에 걸쳐 바뀌면 종속변수가 비정상이 된다. 각 패널 row 는 자신이 어느 정의로
    계산됐는지(version)를 기록하고, 구조모델은 **단일 정의 버전 내에서만** 적합하거나
    버전을 명시적 fixed-effect 로 흡수한다.
    """
    version: str                     # 예: "ev_ebitda_gaap_v1", "ev_ebitda_adj_v2"
    name: str                        # 사람이 읽는 이름 (예: "EV/EBITDA (GAAP)")
    numerator: str                   # 예: "enterprise_value"
    denominator: str                 # 예: "ebitda_gaap"
    adjusts_stock_comp: bool = False # non-GAAP 조정 여부 (drift 의 주범)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    notes: str = ""

    def covers(self, d: date) -> bool:
        if self.valid_from and d < self.valid_from:
            return False
        if self.valid_to and d > self.valid_to:
            return False
        return True


# 반도체(cyclical) 검증용 표준 정의 레지스트리.
# 40분기 중 후반에 non-GAAP(adj) 로 drift 한 현실을 두 버전으로 박제.
EV_EBITDA_GAAP_V1 = MultipleDefinition(
    version="ev_ebitda_gaap_v1",
    name="EV/EBITDA (GAAP)",
    numerator="enterprise_value",
    denominator="ebitda_gaap",
    adjusts_stock_comp=False,
    valid_to=date(2018, 12, 31),
    notes="2019Q1 이전: GAAP EBITDA (stock-comp 비조정).",
)
EV_EBITDA_ADJ_V2 = MultipleDefinition(
    version="ev_ebitda_adj_v2",
    name="EV/EBITDA (adjusted, non-GAAP)",
    numerator="enterprise_value",
    denominator="ebitda_adjusted",
    adjusts_stock_comp=True,
    valid_from=date(2019, 1, 1),
    notes="2019Q1 이후: adjusted EBITDA (stock-comp 환입) — 정의 drift. fixed-effect 흡수 필요.",
)
MULTIPLE_DEFINITION_REGISTRY = {
    d.version: d for d in (EV_EBITDA_GAAP_V1, EV_EBITDA_ADJ_V2)
}


def definition_for(d: date) -> MultipleDefinition:
    """관측일에 유효한 멀티플 정의 반환 (drift 시점 분기)."""
    for defn in MULTIPLE_DEFINITION_REGISTRY.values():
        if defn.covers(d):
            return defn
    return EV_EBITDA_ADJ_V2


# ---------------------------------------------------------------------------
# 3. 반도체(cyclical) 라벨 fixture — T2-7 검증용 (DGP)
# ---------------------------------------------------------------------------

@dataclass
class FixtureSpec:
    """반도체 사이클 fixture 생성 파라미터. DGP 가 trap/real 을 어떻게 심는지 통제."""
    n_firms: int = 40
    n_quarters: int = 40            # 2014Q1 ~ 2023Q4
    start_year: int = 2014
    delist_frac: float = 0.15       # 생존편향 검증용 상폐 비율 (R8 ②)
    mispricing_sd: float = 0.0      # 0 이면 mispricing 없이 노이즈만 (구조적 trap/real 만)
    seed: int = 20260529


# 반도체 cyclical 드라이버 (gemini R4: P/B·EV/EBITDA·capex / claude B5: book_to_bill)
SEMI_DRIVERS = ("book_to_bill", "capex_to_rev", "inventory_qoq", "gross_margin", "rev_growth")


def make_semiconductor_fixture(spec: FixtureSpec | None = None) -> pd.DataFrame:
    """반도체(cyclical) 라벨 에피소드 패널 fixture 생성 (2016-17·2020-21 사이클).

    ★ DGP = claude R4 의 밸류트랩 메커니즘을 *그대로* 인코딩한 adversarial 설계.
    claude R4: "멀티플 하위 분위는 '싸다'가 아니라 'P/E 낮다'일 뿐 — 낮은 이유가
    드라이버(저성장·구조훼손·피크 EPS)로 다 설명되면 그게 밸류트랩."

    그래서 fair_mult = E[mult|drivers,regime] 은 **노출된 드라이버의 선형함수**(모델이 회복
    가능)로 두고, 각 firm-quarter 에 4 type 중 하나를 부여한다:

      - structural_trap : 드라이버 *나쁨*(book_to_bill↓·capex↑·margin↓·growth−) → fair_mult 낮음
                          → actual ≈ fair (mispricing≈0) → **낮은 raw 멀티플** but 잔차≈0. label=0.
      - peak_trap       : 정점 regime, EBITDA 부풀어 분모팽창 → 낮은 EV/EBITDA, 드라이버가 설명
                          → 잔차≈0. label=0.
      - real_undervalued: 드라이버 *정상~양호* → fair_mult 중간, actual = fair − 큰 mispricing
                          → **raw 멀티플은 trap 과 겹침** but 잔차 강한 음수. label=1.
      - fair            : 드라이버 정상, actual ≈ fair. label=0.

    핵심: structural_trap 과 real_undervalued 의 **raw 멀티플 분포가 겹치게** 만들어
    (trap=낮은 fair / real=중간 fair−mispricing), raw 분위는 둘을 못 가르고 **잔차만** 가른다.
    이것이 raw 가 못 보는 곳에서 잔차가 이기는지를 보는 non-circular head-to-head.

    노이즈·미관측 질·정의 drift(R8①)·상폐(R8②)·유한표본을 모두 넣어 trivially separable 회피.
    """
    spec = spec or FixtureSpec()
    rng = np.random.default_rng(spec.seed)

    quarters = pd.period_range(f"{spec.start_year}Q1", periods=spec.n_quarters, freq="Q")
    q_dates = [q.end_time.date() for q in quarters]

    t = np.arange(spec.n_quarters)
    cycle = np.sin(2 * np.pi * (t - 4) / 14.0)           # 약 3.5년 주기
    regime = np.where(cycle > 0.5, 0, np.where(cycle < -0.5, 1, 2))  # 0=peak 1=trough 2=mid

    n_delist = max(1, int(spec.n_firms * spec.delist_frac))
    delist_firms = set(rng.choice(spec.n_firms, size=n_delist, replace=False).tolist())

    rows = []
    for fi in range(spec.n_firms):
        firm = f"SEMI{fi:03d}"
        firm_quality = rng.normal(0.0, 0.35)             # 미관측 질 (잔차로 새는 노이즈, 소량)
        delist_q = None
        if fi in delist_firms:
            trough_qs = np.where(regime == 1)[0]
            delist_q = int(rng.choice(trough_qs)) if len(trough_qs) else spec.n_quarters - 1

        for qi in range(spec.n_quarters):
            if delist_q is not None and qi > delist_q:
                continue
            reg = int(regime[qi])
            phase = "peak" if reg == 0 else ("trough" if reg == 1 else "mid")

            # --- firm-quarter type 부여 (위상별 확률) ---
            u = rng.random()
            if phase == "peak":
                # 정점: peak_trap 다발, real 거의 없음
                ftype = "peak_trap" if u < 0.55 else ("structural_trap" if u < 0.75 else "fair")
            elif phase == "trough":
                # 저점: real 다발 + structural_trap(구조훼손) 공존 → raw 가 헷갈리는 핵심 구간
                ftype = "real" if u < 0.40 else ("structural_trap" if u < 0.70 else "fair")
            else:  # mid
                ftype = "real" if u < 0.15 else ("structural_trap" if u < 0.40 else "fair")

            # --- type 별 드라이버 생성 (★ trap 은 나쁜 드라이버로 낮은 fair 유도) ---
            if ftype == "structural_trap":
                book_to_bill = rng.normal(0.78, 0.05)     # 수요 약함
                capex_to_rev = rng.normal(0.27, 0.02)     # capex 과중 (부담)
                inventory_qoq = rng.normal(0.16, 0.04)    # 재고 누적
                gross_margin = rng.normal(0.33, 0.02)     # 마진 훼손
                rev_growth = rng.normal(-0.04, 0.04)      # 역성장
            elif ftype == "peak_trap":
                book_to_bill = rng.normal(1.28, 0.05)     # 정점 과열
                capex_to_rev = rng.normal(0.30, 0.02)     # 정점 capex
                inventory_qoq = rng.normal(0.22, 0.04)
                gross_margin = rng.normal(0.50, 0.02)
                rev_growth = rng.normal(0.26, 0.05)
            else:  # real / fair: 정상~양호 드라이버
                book_to_bill = rng.normal(1.05, 0.06)
                capex_to_rev = rng.normal(0.18, 0.02)
                inventory_qoq = rng.normal(0.04, 0.04)
                gross_margin = rng.normal(0.44, 0.02)
                rev_growth = rng.normal(0.10, 0.05)

            # --- fair_mult = E[mult|drivers,regime]: 노출 드라이버의 선형함수 (모델이 회복 가능) ---
            fair_mult = (
                4.5
                + 3.5 * book_to_bill        # 수요 모멘텀 → 높은 멀티플
                - 9.0 * capex_to_rev        # capex 부담 → 낮은 멀티플
                + 4.0 * gross_margin        # 마진 → 멀티플
                + 5.0 * rev_growth          # 성장 → 멀티플
                - 1.5 * inventory_qoq
                + 0.9 * firm_quality        # 미관측 (잔차 노이즈)
                + (0.5 if reg == 1 else (-0.3 if reg == 0 else 0.0))  # regime 효과
            )
            # peak_trap: EBITDA 분모 팽창 → 관측 멀티플 추가 하향 (드라이버로 설명됨)
            if ftype == "peak_trap":
                fair_mult -= 1.2

            # 정의 drift (R8 ①): 2019+ adjusted EBITDA → 멀티플 ~12% 낮게
            defn = definition_for(q_dates[qi])
            drift_factor = 0.88 if defn.adjusts_stock_comp else 1.0
            fair_mult_observed = fair_mult * drift_factor

            # --- type 별 mispricing (real 만 actual ≪ fair) ---
            label_real = 0
            if ftype == "real":
                label_real = 1
                mispricing = -rng.uniform(2.5, 4.0)       # actual 이 fair 보다 크게 낮음 = 진짜 쌈
            else:
                mispricing = rng.normal(0, 0.25)          # trap/fair = 거의 fair-priced

            noise = rng.normal(0, 0.55)
            actual_mult = max(fair_mult_observed + mispricing + noise, 1.0)

            is_delist_row = (delist_q is not None and qi == delist_q)
            delist_ret = -rng.uniform(0.6, 0.95) if is_delist_row else np.nan

            rows.append({
                COL_FIRM: firm,
                COL_SECTOR: "semiconductor",
                COL_DATE: q_dates[qi],
                COL_KNOWABLE_FROM: q_dates[qi],
                COL_REGIME: reg,
                COL_MULTIPLE: actual_mult,
                COL_MULT_DEF_VER: defn.version,
                COL_DELIST_FLAG: (delist_q is not None),
                COL_DELIST_RET: delist_ret,
                f"{DRIVER_PREFIX}book_to_bill": book_to_bill,
                f"{DRIVER_PREFIX}capex_to_rev": capex_to_rev,
                f"{DRIVER_PREFIX}inventory_qoq": inventory_qoq,
                f"{DRIVER_PREFIX}gross_margin": gross_margin,
                f"{DRIVER_PREFIX}rev_growth": rev_growth,
                # fixture 전용 라벨 (실패널엔 없음)
                "label_real": label_real,
                "label_cycle_phase": phase,
                "label_type": ftype,
                "label_fair_mult": fair_mult_observed,
            })

    panel = pd.DataFrame(rows)
    panel[COL_DATE] = pd.to_datetime(panel[COL_DATE])
    panel[COL_KNOWABLE_FROM] = pd.to_datetime(panel[COL_KNOWABLE_FROM])
    return panel


def fixture_label_columns() -> tuple[str, ...]:
    """fixture 전용 라벨 컬럼 (실패널에는 없음 — 누수 방지로 모델 입력에서 제외)."""
    return ("label_real", "label_cycle_phase", "label_type", "label_fair_mult")


if __name__ == "__main__":
    df = make_semiconductor_fixture()
    print(f"패널 shape: {df.shape}")
    print(f"검증: {validate_panel(df) or 'PASS'}")
    print(f"드라이버: {driver_columns(df)}")
    print(f"상폐 기업 row 수: {int(df[COL_DELIST_FLAG].sum())} / 전체 {len(df)}")
    print(f"정의 버전 분포:\n{df[COL_MULT_DEF_VER].value_counts()}")
    print(f"라벨 real 분포:\n{df['label_real'].value_counts()}")
    print(f"phase 분포:\n{df['label_cycle_phase'].value_counts()}")

    # 멀티자산 확장(IA-4) 검증 — clean / 위반 케이스
    multi = pd.DataFrame({
        COL_INSTRUMENT_KIND: ["etf", "crypto", "macro_series"],
        COL_LIFECYCLE_STATUS: ["active", "active", "discontinued"],
        COL_TRADABILITY: [True, True, False],
        COL_INCEPTION_DATE: pd.to_datetime(["2010-01-01", "2015-01-01", "1990-01-01"]),
        COL_COVERAGE_START: pd.to_datetime(["2010-01-01", "2015-01-01", "1990-01-01"]),
    })
    assert validate_instrument_columns(multi) == [], validate_instrument_columns(multi)
    bad = multi.copy(); bad.loc[0, COL_INSTRUMENT_KIND] = "nft"
    probs = validate_instrument_columns(bad)
    assert any("instrument_kind" in p for p in probs), probs
    print(f"멀티자산 확장: clean PASS / 미정의 kind('nft') 탐지={len(probs)}건 OK")
