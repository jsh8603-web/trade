"""core/data/weight_panel.py — 가중학습(R15) 지표 패널 PIT 공급 + 반사성 게이트.

CONSULT-DECISIONS-weight-20260529.md §4-1·§4-4 (btn-Inv 분담).

regime-conditional Graphical Lasso(§1.1, btn-button 추정) 의 **학습 입력**을 PIT-correct
하게 공급한다. glasso 는 지표 간 sparse precision Ω 를 추정하므로 입력 = 시점(행)×지표(열)
매트릭스. 각 셀은 **그 학습 시점(knowledge_time as_of)에 알 수 있던 값**(VintageStore.realtime)
이어야 한다 — 개정 누수 차단(자문 R1 #1: revised lookahead alpha).

★PIT 경계 의미(§1.7): 학습은 knowledge_time T 까지 알려진 데이터만 본다. 같은 period 라도
as_of 가 다르면 다른 vintage 값(개정 반영). build_matrix(as_of=T) = ∀(series,period)
vintage_knowable_from ≤ T 중 최신 = "T 시점에 학습기가 볼 수 있던 시계열".

★반사성 게이트(§1.8·§4-4): 학습 입력에서 **과거 포지션/체결/PnL 유래 컬럼을 배제**한다.
자기 거래 결과를 학습에 넣으면 self-confirming reflexivity(전략이 만든 가격충격을 다시
학습 → attractor). 외부 지표 시계열만 허용. 반사성 series 발견 시 거부(ValueError).

⛔ 추정(glasso·shrinkage·belief-mix)은 본 모듈 범위 밖(btn-button). 여기는 PIT 공급만.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Protocol, Sequence, Union

import numpy as np

AsOfLike = Union[str, date, datetime]


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


# ---------------------------------------------------------------------------
# 반사성 게이트 — 과거 포지션/체결/PnL 유래 series 배제 (§1.8·§4-4)
# ---------------------------------------------------------------------------
# 학습 입력은 *외부 지표 시계열*만. 자기 거래가 만든 흔적(포지션·체결·실현손익·노출·
# 보유비중)을 넣으면 reflexivity 누수 — 전략이 유발한 가격충격을 학습이 다시 먹어 self-
# confirming attractor 형성.
#
# ★word-boundary 토큰 매칭(substring 아님): series_id 를 snake/kebab/공백/.으로 쪼개
# 단어 집합과 교집합. substring 매칭은 "own"⊂"unknown", "book"⊂"book_value"(정당한
# 펀더멘털), "trade"⊂"trade_volume"(시장 거래량=외부) 를 오탐한다. self-거래 특화 단어만
# 차단하고 시장/펀더멘털 지표는 통과시킨다.

_REFLEXIVE_WORDS: frozenset = frozenset({
    "position", "holding", "fill", "executed", "pnl", "unrealized",
    "exposure", "portfolio", "inventory", "slippage", "turnover",
    "my", "own", "strategy",
})

_TOKEN_SPLIT = re.compile(r"[_\-\s.]+")


def _series_words(series_id: str) -> set:
    return set(t for t in _TOKEN_SPLIT.split(series_id.strip().lower()) if t)


def is_reflexive_series(series_id: str) -> bool:
    """series_id 가 자기 거래 유래(반사성) 단어를 포함하면 True (word-boundary 매칭)."""
    return bool(_series_words(series_id) & _REFLEXIVE_WORDS)


def assert_no_reflexive_series(series_ids: Sequence[str]) -> None:
    """학습 입력 series 에 반사성(포지션/체결/PnL) 컬럼이 섞이면 거부.

    §1.8: 과거 포지션/체결 데이터 배제 — 외부 지표 시계열만 학습 입력. 하나라도
    매칭되면 ValueError(어떤 series 가 왜 막혔는지 명시).
    """
    bad = [s for s in series_ids if is_reflexive_series(s)]
    if bad:
        raise ValueError(
            f"반사성 게이트 위반: 과거 포지션/체결/PnL 유래 series 는 학습 입력 금지 "
            f"(외부 지표 시계열만) — 차단 {bad}"
        )


# ---------------------------------------------------------------------------
# vintage provider 계약 (duck-typed) — VintageStore 가 충족
# ---------------------------------------------------------------------------

class VintageProvider(Protocol):
    """realtime(series, period, as_of) PIT 조회를 제공하는 store (VintageStore 호환)."""

    def realtime(self, series_id: str, period: str, as_of: AsOfLike) -> Optional[float]: ...


# ---------------------------------------------------------------------------
# 지표 패널 (PIT 매트릭스)
# ---------------------------------------------------------------------------

@dataclass
class IndicatorPanel:
    """as_of 시점 PIT-correct 지표 매트릭스. glasso 학습 입력.

    matrix[i, j] = series_ids[j] 의 periods[i] 값(as_of 기준 realtime). 미공표=np.nan.
    행=관측 시점(period), 열=지표(series). knowledge_time=as_of(학습 PIT 경계).
    """
    matrix: np.ndarray            # (n_periods, n_series) float, NaN=미공표
    periods: list                 # 행 라벨 (측정 기간)
    series_ids: list              # 열 라벨 (지표)
    as_of: date

    @property
    def shape(self) -> tuple:
        return self.matrix.shape

    def complete_rows(self) -> "IndicatorPanel":
        """NaN 이 하나도 없는 완전관측 행만 남긴 패널(glasso 는 결측 불가).

        호출자(btn-button)가 impute 대신 완전관측만 쓰고 싶을 때. effective-n 은
        이 행 수 기준(자문 §1.8 eff-n 게이트 입력).
        """
        if self.matrix.size == 0:
            return IndicatorPanel(self.matrix.copy(), list(self.periods),
                                  list(self.series_ids), self.as_of)
        keep = ~np.isnan(self.matrix).any(axis=1)
        return IndicatorPanel(
            matrix=self.matrix[keep],
            periods=[p for p, k in zip(self.periods, keep) if k],
            series_ids=list(self.series_ids),
            as_of=self.as_of,
        )

    @property
    def n_complete(self) -> int:
        """완전관측 행 수(effective-n 후보)."""
        if self.matrix.size == 0:
            return 0
        return int((~np.isnan(self.matrix).any(axis=1)).sum())


def build_indicator_matrix(
    provider: VintageProvider,
    series_ids: Sequence[str],
    periods: Sequence[str],
    as_of: AsOfLike,
) -> IndicatorPanel:
    """as_of 시점 PIT 지표 매트릭스 조립(glasso 학습 입력).

    각 셀 = provider.realtime(series, period, as_of) — as_of 에 알 수 있던 vintage 값.
    같은 period 라도 as_of 가 늦으면 개정값 반영(학습은 knowledge_time 까지 전부 본다).
    미공표 = np.nan. ★반사성 게이트 통과 필수(포지션/체결 series 거부).
    """
    assert_no_reflexive_series(series_ids)
    a = _d(as_of)
    n_p, n_s = len(periods), len(series_ids)
    mat = np.full((n_p, n_s), np.nan, dtype=float)
    for i, period in enumerate(periods):
        for j, sid in enumerate(series_ids):
            v = provider.realtime(sid, period, a)
            if v is not None:
                mat[i, j] = float(v)
    return IndicatorPanel(matrix=mat, periods=list(periods),
                          series_ids=list(series_ids), as_of=a)


if __name__ == "__main__":
    from core.data.vintage import VintageStore

    vs = VintageStore()
    # 3 지표 × 3 period. CPI/PMI 는 개정 있음, RATE 는 즉시 확정.
    vs.add("CPI", "2024-01", 3.0, "2024-02-15")
    vs.add("CPI", "2024-01", 3.2, "2024-03-20")   # 개정(늦은 vintage)
    vs.add("CPI", "2024-02", 2.8, "2024-02-28")
    vs.add("CPI", "2024-03", 2.5, "2024-04-15")
    vs.add("PMI", "2024-01", 51.0, "2024-02-01")
    vs.add("PMI", "2024-02", 49.5, "2024-03-01")
    vs.add("PMI", "2024-03", 50.2, "2024-04-01")
    vs.add("RATE", "2024-01", 5.5, "2024-01-31")
    vs.add("RATE", "2024-02", 5.5, "2024-02-29")
    vs.add("RATE", "2024-03", 5.25, "2024-03-31")

    periods = ["2024-01", "2024-02", "2024-03"]
    series = ["CPI", "PMI", "RATE"]

    # 1) as_of 2024-04-30: 전 period 가시, CPI 2024-01 = 개정값 3.2
    p = build_indicator_matrix(vs, series, periods, "2024-04-30")
    assert p.shape == (3, 3), p.shape
    assert abs(p.matrix[0, 0] - 3.2) < 1e-9, "CPI 2024-01 개정값(3.2) 반영"
    assert p.n_complete == 3, p.n_complete
    print(f"1) as_of 04-30 매트릭스 {p.shape}, CPI[01]=개정 3.2, 완전행={p.n_complete} OK")

    # 2) ★PIT 누수 차단: as_of 2024-03-01 엔 CPI 2024-01 = 속보 3.0 (개정 03-20 미가시)
    p2 = build_indicator_matrix(vs, series, periods, "2024-03-01")
    assert abs(p2.matrix[0, 0] - 3.0) < 1e-9, "개정 前 = 속보 3.0"
    # 2024-03 period 는 03-01 엔 미공표 → NaN, 완전행 2개(01,02)
    assert np.isnan(p2.matrix[2, 0]), "2024-03 CPI 미공표=NaN"
    cr = p2.complete_rows()
    assert cr.shape[0] == 2 and cr.periods == ["2024-01", "2024-02"], cr.periods
    print(f"2) PIT 누수 차단: as_of 03-01 → CPI[01]=속보 3.0, 03 period=NaN, 완전행 2개 OK")

    # 3) ★반사성 게이트: 포지션/체결/PnL series 거부
    for bad in ["my_position_btc", "realized_pnl", "portfolio_weight_kospi", "fill_price"]:
        try:
            build_indicator_matrix(vs, [bad], periods, "2024-04-30")
            raise AssertionError(f"반사성 series 통과: {bad}")
        except ValueError as e:
            assert "반사성" in str(e), e
    assert not is_reflexive_series("CPI") and is_reflexive_series("my_position_x")
    # ★over-reach 방지(word-boundary): 정당한 펀더멘털/시장 지표는 통과해야 함
    for ok_series in ["book_value", "trade_volume", "unknown_series", "downtown_index", "PBR"]:
        assert not is_reflexive_series(ok_series), f"오탐: {ok_series}"
    print("3) 반사성 게이트: 포지션/체결/PnL 거부 / book_value·trade_volume 등 외부지표 통과(over-reach 방지) OK")

    # 4) 미공표 series 전체 = NaN 열 (graceful)
    p4 = build_indicator_matrix(vs, ["CPI", "UNKNOWN_SERIES"], periods, "2024-04-30")
    assert np.isnan(p4.matrix[:, 1]).all(), "미존재 series = 전부 NaN"
    assert p4.complete_rows().shape[0] == 0, "완전행 0(미존재 열 때문)"
    print("4) 미공표 series = NaN 열, 완전행 0 (graceful) OK")

    print("weight_panel (지표 패널 PIT 공급 + 반사성 게이트) self-test PASS")
