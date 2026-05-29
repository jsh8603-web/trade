"""core/data/corp_action.py — 기업행위(corp action) 전처리 (Phase2 T1, WP-T1-D).

SPEC-T1 T1-4: 액면분할·자사주 멀티플 왜곡 → adjustment.

왜 필요한가:
- raw 멀티플은 aggregate market_cap 기반이라 **액면분할은 시총 불변 → 멀티플 중립**.
  단, per-share 가격 시계열은 분할 시 점프(왜곡) → 수정주가(back-adjusted)가 필요.
- 자사주 매입(buyback)은 equity·현금 실제 감소 → PBR 변화는 *실질*(artifact 아님).
  다만 outstanding_shares 가 줄어 per-share 비교 시 단절 → split-adjust 와 동일 처리.

본 모듈은 **순수 함수**(네트워크/credential 무관) — corp action 로그를 받아
(a) 누적 분할 계수, (b) 가격/주식수 back-adjustment, (c) 시총 연속성 검증을 제공.
패널 빌드 시 가격 시계열에 적용해 멀티플 시계열 단절을 제거한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Sequence, Union


class CorpActionType(Enum):
    SPLIT = "split"            # 액면분할 (1주 → ratio 주)
    REVERSE_SPLIT = "reverse"  # 액면병합 (ratio 주 → 1주)
    BUYBACK = "buyback"        # 자사주 매입 (shares 감소)


@dataclass(frozen=True)
class CorpAction:
    """단일 기업행위. ex_date 이후 가격/주식수 기준이 바뀐다."""
    firm: str
    ex_date: datetime
    action_type: CorpActionType
    ratio: float               # split=분할비(2:1→2.0), reverse=병합비(1:5→5.0), buyback=감소주식수


def split_factor(actions: Sequence[CorpAction], as_of: datetime) -> float:
    """as_of 시점 가격을 과거와 비교 가능하게 만드는 누적 분할 계수.

    as_of 이후(미래) 분할만 적용 — back-adjustment 는 "현재 기준 과거 가격 환산".
    PIT 안전: as_of 시점엔 미래 분할을 모르므로, 백테스트는 as_of 시점 raw 를 쓰고
    cross-time 비교 시에만 본 계수를 적용한다(호출자 판단).
    """
    factor = 1.0
    for a in actions:
        if a.ex_date <= as_of:
            continue
        if a.action_type == CorpActionType.SPLIT:
            factor *= a.ratio
        elif a.action_type == CorpActionType.REVERSE_SPLIT:
            factor /= a.ratio
    return factor


def adjust_price(raw_price: float, factor: float) -> float:
    """back-adjusted 가격 = raw_price / 누적분할계수 (분할 후 기준으로 환산)."""
    if factor == 0:
        return raw_price
    return raw_price / factor


def adjust_shares(raw_shares: float, factor: float) -> float:
    """back-adjusted 주식수 = raw_shares * 누적분할계수."""
    return raw_shares * factor


def market_cap_continuous(
    price_before: float, shares_before: float,
    price_after: float, shares_after: float,
    tol: float = 0.02,
) -> bool:
    """분할 전후 시총 연속성 검증 (분할은 시총 불변이어야 — artifact 탐지).

    tol = 허용 오차(2%, 가격 변동 노이즈). 초과 = 실질 가치변화(분할 artifact 아님).
    """
    mc_before = price_before * shares_before
    mc_after = price_after * shares_after
    if mc_before == 0:
        return False
    return abs(mc_after - mc_before) / mc_before <= tol


def detect_unflagged_split(
    shares_t0: float, shares_t1: float,
    actions: Sequence[CorpAction], firm: str,
    between: "tuple[datetime, datetime]",
    jump_threshold: float = 1.5,
) -> bool:
    """로그에 없는데 주식수가 급변 = 미기록 분할 의심(데이터 품질 경고).

    True = 주식수 점프가 jump_threshold 배 이상인데 해당 구간 corp action 로그 없음.
    """
    if shares_t0 <= 0:
        return False
    ratio = shares_t1 / shares_t0
    jumped = ratio >= jump_threshold or ratio <= (1.0 / jump_threshold)
    if not jumped:
        return False
    lo, hi = between
    logged = any(
        a.firm == firm and lo < a.ex_date <= hi
        and a.action_type in (CorpActionType.SPLIT, CorpActionType.REVERSE_SPLIT)
        for a in actions
    )
    return not logged


# ---------------------------------------------------------------------------
# 배당/분배 bitemporal ledger — Total Return 입력 (DESIGN-inv-v2 §2 corporate_action)
# ---------------------------------------------------------------------------
# 위 split-adjust 수학과 별개로, ETF/주식 **Total Return** 은 배당/분배를 알아야 한다.
# 분배는 bitemporal: 선언일에 알게 되고(knowable_from), **연말 1099 재분류**로 종류가
# 바뀐다(cash_dividend → return_of_capital 등) = 같은 ex_date + 늦은 sys_time append.
# ★back-adjust 금지(vendor Adj Close = lookahead): raw close + 이 ledger 로 forward-only TR.

_DistSrc = Union[str, date, datetime]


def _dd(x: _DistSrc) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class Distribution:
    """배당/분배 1건 (bitemporal). per-share 금액. 연말 재분류 = 같은 ex_date + 늦은 sys_time."""
    psid: str
    ex_date: date
    amount: float
    dist_type: str          # cash_dividend / stock_dividend / capital_gain / return_of_capital
    knowable_from: date     # 선언/공표
    sys_time: date          # 기록/재분류


class DistributionLedger:
    """배당/분배 bitemporal ledger + forward-only Total Return. append-only."""

    def __init__(self) -> None:
        self._dists: list[Distribution] = []

    def add(self, psid: str, ex_date: _DistSrc, amount: float, dist_type: str,
            knowable_from: _DistSrc, *, sys_time: Optional[_DistSrc] = None) -> Distribution:
        kf = _dd(knowable_from)
        d = Distribution(psid, _dd(ex_date), float(amount), dist_type, kf,
                         _dd(sys_time) if sys_time is not None else kf)
        self._dists.append(d)
        return d

    def distributions_as_of(self, psid: str, start: _DistSrc, end: _DistSrc, as_of: _DistSrc) -> list[Distribution]:
        """(start, end] ex_date 의 분배 중 as_of 에 알 수 있던 것. (ex_date,type)별 최신 sys_time.

        연말 재분류 반영: 같은 ex_date 의 dist_type 정정 시 최신 sys_time row 채택.
        """
        s, e, a = _dd(start), _dd(end), _dd(as_of)
        visible = [d for d in self._dists
                   if d.psid == psid and s < d.ex_date <= e
                   and d.knowable_from <= a and d.sys_time <= a]
        # (ex_date) 별 최신 sys_time (재분류는 같은 ex_date 1건으로 수렴)
        latest: dict[date, Distribution] = {}
        for d in visible:
            cur = latest.get(d.ex_date)
            if cur is None or d.sys_time > cur.sys_time:
                latest[d.ex_date] = d
        return sorted(latest.values(), key=lambda d: d.ex_date)

    def total_return(self, psid: str, t0: _DistSrc, t1: _DistSrc, price_t0: float, price_t1: float,
                     as_of: _DistSrc, *, withholding: float = 0.0,
                     income_types: tuple = ("cash_dividend", "capital_gain")) -> float:
        """forward-only TR = (price_t1 + Σ분배(소득성, net)) / price_t0 − 1. back-adjust 안 함.

        withholding = 원천징수율(Net TR convention; 0=Gross). return_of_capital 은 소득 아님
        (income_types 제외 — 원금환급은 cost-basis 감소, TR 분자 미포함). PIT: as_of 분배만.
        """
        if price_t0 <= 0:
            raise ValueError("price_t0 양수 필요")
        dists = self.distributions_as_of(psid, t0, t1, as_of)
        income = sum(d.amount * (1.0 - withholding) for d in dists if d.dist_type in income_types)
        return (price_t1 + income) / price_t0 - 1.0


if __name__ == "__main__":
    led = DistributionLedger()
    # ETF VOO: 분기 배당. 2024-03-15 $1.5(cash, 선언 03-01), 2024-06-15 $1.6(cash, 선언 06-01)
    led.add("VOO", "2024-03-15", 1.5, "cash_dividend", "2024-03-01")
    led.add("VOO", "2024-06-15", 1.6, "cash_dividend", "2024-06-01")

    # 1) ★forward-only TR (back-adjust 금지): (110 + 1.5+1.6)/100 - 1
    tr = led.total_return("VOO", "2024-01-01", "2024-07-01", 100.0, 110.0, "2024-07-15")
    assert abs(tr - ((110 + 3.1) / 100 - 1)) < 1e-9, tr
    print(f"1) forward-only TR: {tr:.4f} (가격 110 + 배당 3.1) OK")

    # 2) Net TR (원천징수 15%)
    tr_net = led.total_return("VOO", "2024-01-01", "2024-07-01", 100.0, 110.0, "2024-07-15", withholding=0.15)
    assert abs(tr_net - ((110 + 3.1 * 0.85) / 100 - 1)) < 1e-9, tr_net
    print(f"2) Net TR(원천 15%): {tr_net:.4f} OK")

    # 3) ★PIT: as_of 가 06 배당 선언(06-01) 前이면 06 배당 미포함
    tr_early = led.total_return("VOO", "2024-01-01", "2024-07-01", 100.0, 110.0, "2024-05-15")
    assert abs(tr_early - ((110 + 1.5) / 100 - 1)) < 1e-9, tr_early
    print(f"3) PIT TR(as_of 05-15, 06배당 선언前): {tr_early:.4f} (03배당만) OK")

    # 4) ★연말 재분류: 06-15 배당이 cash → return_of_capital 재분류(sys_time 12-31)
    led.add("VOO", "2024-06-15", 1.6, "return_of_capital", "2024-06-01", sys_time="2024-12-31")
    # 재분류 前 as_of(07-15): cash 로 보여 TR 소득 포함
    tr_b = led.total_return("VOO", "2024-01-01", "2024-07-01", 100.0, 110.0, "2024-07-15")
    assert abs(tr_b - ((110 + 3.1) / 100 - 1)) < 1e-9, tr_b
    # 재분류 後 as_of(2025-01-15): RoC 는 소득 아님 → 06배당 제외(03배당만)
    tr_a = led.total_return("VOO", "2024-01-01", "2024-07-01", 100.0, 110.0, "2025-01-15")
    assert abs(tr_a - ((110 + 1.5) / 100 - 1)) < 1e-9, tr_a
    print(f"4) 연말 재분류 bitemporal: 재분류前 TR={tr_b:.4f}(소득3.1) / 後 TR={tr_a:.4f}(RoC 제외) OK")

    print("corp_action (split-adjust + 배당 bitemporal TR) self-test PASS")
