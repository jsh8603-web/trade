"""core/data/fx.py — PIT 환율 정규화 (IA-4 멀티통화 · IA-6 시점 무결성 substrate).

KR+US 멀티통화 유니버스에서 자산 가치를 단일 기준통화로 환산하려면 환율이 필요한데,
환율은 **두 시점**을 가진다: 적용 가치일(rate_date)과 우리가 그 환율을 알게 된 시점
(knowable_from). 백테스트에서 as_of 의사결정 시 **그 시점에 알 수 있던 환율**만 써야 한다
(최신 환율로 과거 가치를 환산 = lookahead).

PIT 규칙(다른 모듈과 동일 2중 게이트):
- 가치일 value_date 의 환율 = rate_date ≤ value_date 인 것 중 **가장 최근 rate_date**
  (주말/휴장 fill-forward — 토요일 가치는 금요일 환율). 단, knowable_from ≤ as_of
  AND sys_time ≤ as_of 인 row 만. 같은 rate_date 정정 다건이면 최신 sys_time.

환산 경로: 동일통화=1.0 / 직접쌍 / 역쌍(1/rate) / USD 매개 삼각환산. 신규 의존 0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Union

AsOfLike = Union[str, date, datetime]
_VEHICLE = "USD"  # 삼각환산 매개 통화


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class FxRecord:
    """bitemporal 환율 관측 1건. 1 base = rate quote (예: USD/KRW=1350 → 1 USD=1350 KRW).

    rate_date = 이 환율이 적용되는 가치일. knowable_from = 우리가 알게 된 시점.
    sys_time = 기록/정정 시점(정정 시 새 row + 최신 sys_time 채택).
    """
    base: str
    quote: str
    rate_date: date
    rate: float
    knowable_from: date
    sys_time: date


class FxStore:
    """bitemporal 환율 저장소 + PIT 환산. append-only."""

    def __init__(self) -> None:
        self._records: list[FxRecord] = []

    # --- 적재 (append-only) ---------------------------------------------
    def register(
        self,
        base: str,
        quote: str,
        rate_date: AsOfLike,
        rate: float,
        knowable_from: AsOfLike,
        *,
        sys_time: Optional[AsOfLike] = None,
    ) -> FxRecord:
        """환율 1건 적재. 1 base = rate quote. knowable_from 이전 as_of 에는 미가시."""
        if rate <= 0:
            raise ValueError(f"rate 는 양수여야: {base}/{quote}={rate}")
        kf = _d(knowable_from)
        rec = FxRecord(
            base=base.upper(),
            quote=quote.upper(),
            rate_date=_d(rate_date),
            rate=float(rate),
            knowable_from=kf,
            sys_time=_d(sys_time) if sys_time is not None else kf,
        )
        self._records.append(rec)
        return rec

    # --- PIT 직접쌍 조회 ------------------------------------------------
    def _direct(self, base: str, quote: str, value_date: date, as_of: date) -> Optional[float]:
        """base/quote 직접쌍의 PIT 환율. rate_date ≤ value_date fill-forward + 2중 게이트."""
        cands = [
            r for r in self._records
            if r.base == base and r.quote == quote
            and r.rate_date <= value_date
            and r.knowable_from <= as_of and r.sys_time <= as_of
        ]
        if not cands:
            return None
        # 가장 최근 rate_date, 동률이면 최신 sys_time
        best = max(cands, key=lambda r: (r.rate_date, r.sys_time))
        return best.rate

    # --- 환율 조회 (직접/역/삼각) ---------------------------------------
    def get_rate(
        self, base: str, quote: str, value_date: AsOfLike, as_of: AsOfLike
    ) -> Optional[float]:
        """value_date 시점 1 base = ? quote (as_of 에 알 수 있던 PIT 환율). 없으면 None."""
        b, q = base.upper(), quote.upper()
        if b == q:
            return 1.0
        vd, a = _d(value_date), _d(as_of)
        direct = self._direct(b, q, vd, a)
        if direct is not None:
            return direct
        inverse = self._direct(q, b, vd, a)
        if inverse is not None:
            return 1.0 / inverse
        # USD 매개 삼각환산: base→USD→quote
        if b != _VEHICLE and q != _VEHICLE:
            leg1 = self.get_rate(b, _VEHICLE, vd, a)   # 1 base = leg1 USD
            leg2 = self.get_rate(_VEHICLE, q, vd, a)   # 1 USD  = leg2 quote
            if leg1 is not None and leg2 is not None:
                return leg1 * leg2
        return None

    def convert(
        self, amount: float, base: str, quote: str, value_date: AsOfLike, as_of: AsOfLike
    ) -> Optional[float]:
        """amount(base 통화) → quote 통화, value_date 의 PIT 환율로. 없으면 None."""
        rate = self.get_rate(base, quote, value_date, as_of)
        return None if rate is None else amount * rate


if __name__ == "__main__":
    fx = FxStore()
    fx.register("USD", "KRW", "2024-06-03", 1380.0, knowable_from="2024-06-03")  # 월
    fx.register("EUR", "USD", "2024-06-03", 1.08, knowable_from="2024-06-03")

    # 1) 직접쌍 USD→KRW
    assert fx.get_rate("USD", "KRW", "2024-06-03", "2024-06-30") == 1380.0
    assert fx.convert(100, "USD", "KRW", "2024-06-03", "2024-06-30") == 138000.0
    print("1) 직접쌍 USD→KRW: 100 USD = 138,000 KRW OK")

    # 2) 역쌍 KRW→USD = 1/1380
    r = fx.get_rate("KRW", "USD", "2024-06-03", "2024-06-30")
    assert abs(r - 1.0 / 1380.0) < 1e-12, r
    print(f"2) 역쌍 KRW→USD = {r:.8f} (1/1380) OK")

    # 3) 동일통화 = 1.0
    assert fx.get_rate("KRW", "KRW", "2024-06-03", "2024-06-30") == 1.0
    print("3) 동일통화 KRW→KRW = 1.0 OK")

    # 4) PIT knowable_from: 미래에 알게 된 환율은 과거 as_of 에서 미가시
    fx.register("USD", "KRW", "2024-12-02", 1430.0, knowable_from="2024-12-02")
    # as_of 2024-06-30 < 2024-12-02 공표 → 12월 환율 안 보이고 6월 fill-forward
    assert fx.get_rate("USD", "KRW", "2024-12-31", "2024-06-30") == 1380.0, "공표 전 미가시"
    assert fx.get_rate("USD", "KRW", "2024-12-31", "2024-12-31") == 1430.0, "공표 후 가시"
    print("4) PIT knowable_from: 12월 환율 공표 전 미가시(6월 fill-forward)/후 가시 OK")

    # 5) 주말 fill-forward: 토요일 가치일 = 직전 금요일/평일 환율
    # 2024-06-08(토) 가치 → rate_date ≤ 토 중 최근 = 2024-06-03(월)
    assert fx.get_rate("USD", "KRW", "2024-06-08", "2024-06-30") == 1380.0
    print("5) 주말 fill-forward: 토요일 가치 = 직전 평일(06-03) 환율 OK")

    # 6) USD 삼각환산: EUR→KRW = (EUR→USD) × (USD→KRW) = 1.08 × 1380
    eur_krw = fx.get_rate("EUR", "KRW", "2024-06-03", "2024-06-30")
    assert abs(eur_krw - 1.08 * 1380.0) < 1e-9, eur_krw
    print(f"6) 삼각환산 EUR→KRW = {eur_krw:.2f} (1.08×1380) OK")

    # 7) sys_time 정정: 같은 rate_date 환율 정정 → 최신 sys_time 채택
    fx.register("USD", "KRW", "2024-06-03", 1399.0, knowable_from="2024-06-03", sys_time="2024-06-05")
    assert fx.get_rate("USD", "KRW", "2024-06-03", "2024-06-30") == 1399.0, "정정 후 최신값"
    # 정정 전 as_of(06-04)에는 원래값 — knowable_from 동일이나 sys_time 게이트
    assert fx.get_rate("USD", "KRW", "2024-06-03", "2024-06-04") == 1380.0, "정정 미가시"
    print("7) sys_time 정정: 06-05 정정 → 06-04 미가시(1380)/06-30 가시(1399) OK")

    # 8) 미존재 통화쌍 = None
    assert fx.get_rate("JPY", "KRW", "2024-06-03", "2024-06-30") is None
    print("8) 미존재 통화쌍(JPY→KRW) = None OK")

    print("fx (PIT 환율 정규화) self-test PASS")
