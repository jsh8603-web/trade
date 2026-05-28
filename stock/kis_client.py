"""stock/kis_client.py — pykis 어댑트 KIS 집행 클라이언트 (SO-5/P4).

WHY: 코인 execute_trade.py 와 완전 별개 파일. coin 본체 import/위임 없음.
     pykis(python-kis) 의 order/modify/cancel/pending/_clamp/_poll_and_amend/ws/token 을
     모의투자(paper) 우선 모드로 래핑. EMERGENCY_STOP/DRY_RUN 선검사 경유.

SACRED:
- 코인 실거래 경로 미변경
- pykis 재코딩 금지 — 어댑터 래퍼만 (from_number, domestic_modify_order, cancel_order,
  _run_forever, _restore_subscriptions, PINGPONG 그대로 채택)
- 모의투자(paper) 우선 기본값
- admission + risk_gate 경유 후만 실주문 (이 파일에서는 경유 검사만)
- DRY_RUN / EMERGENCY_STOP 선검사 필수

CREDENTIAL 부재: KIS appkey/secret 없으면 pykis 어댑터 본체 작동, 실 네트워크 왕복 이연.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("stock.kis_client")


# ---------------------------------------------------------------------------
# 안전장치 — DRY_RUN / EMERGENCY_STOP 선검사 (coin과 동일 패턴)
# ---------------------------------------------------------------------------

def _check_safety(dry_run: bool, emergency_stop: bool) -> Tuple[bool, str]:
    """EMERGENCY_STOP / DRY_RUN 선검사. 실행 불가 시 (False, reason) 반환."""
    if emergency_stop:
        return False, "EMERGENCY_STOP=True — 모든 KIS 매매 차단"
    if dry_run:
        return False, "DRY_RUN=True — 실주문 미발송"
    return True, "OK"


# ---------------------------------------------------------------------------
# 주문번호 — pykis KisOrderNumber 3-튜플 어댑터
# 재코딩 금지: from_number 패턴(order.py:392-417) 을 래퍼로만 사용
# ---------------------------------------------------------------------------

@dataclass
class KisOrderRef:
    """KIS 주문번호 3-튜플 (branch, number, account_no).

    pykis KisOrderNumber.from_number 대응 — credential 부재 시 직접 생성.
    ORGN_ODNO: 원번호 추적 체인(이중정정 방지) — modify 시 신규번호를 원번호에 매핑.
    """
    branch: str
    number: str
    account_no: str
    symbol: str = ""
    market: str = "KRX"
    client_order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_number: Optional[str] = None  # ORGN_ODNO — 이중정정 방지

    def to_pykis_order_number(self, kis_client=None):
        """pykis KisOrderNumber 로 변환 (credential 있을 때)."""
        if kis_client is None:
            return None
        try:
            from pykis.api.account.order import KisOrder
            return KisOrder.from_number(
                kis=kis_client,
                symbol=self.symbol,
                market=self.market,
                account_number=self.account_no,
                branch=self.branch,
                number=self.number,
            )
        except Exception as exc:
            logger.debug("pykis from_number 변환 실패: %s", exc)
            return None


# ---------------------------------------------------------------------------
# 레이트리밋 — E1 KIS 초당 레이트리밋 (데이터 rate_tier 와 별개)
# ---------------------------------------------------------------------------

class KisRateLimiter:
    """E1 KIS API 초당 레이트리밋. 주문>조회 우선순위 큐(H4 참조).

    KIS 공식: 초당 10~20req (모의/실계좌 다름). 기본 보수값 10/s.
    """

    def __init__(self, requests_per_second: float = 10.0):
        self._min_interval = 1.0 / requests_per_second
        self._next_available = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        # slot 예약만 lock 내부, sleep 은 lock 밖 — 동시 호출(주문 sleep 중 cancel/modify) 우선순위 역전 방지
        with self._lock:
            now = time.monotonic()
            scheduled = max(now, self._next_available)
            self._next_available = scheduled + self._min_interval
        wait = scheduled - now
        if wait > 0:
            time.sleep(wait)


# ---------------------------------------------------------------------------
# KisClient — 메인 집행 어댑터
# ---------------------------------------------------------------------------

class KisClient:
    """pykis 어댑트 KIS 집행 클라이언트.

    모의투자(paper) 우선. credential 부재 시 본체 작동 + 실 왕복 이연.
    """

    def __init__(
        self,
        appkey: Optional[str] = None,
        appsecret: Optional[str] = None,
        account_no: Optional[str] = None,
        paper: bool = True,  # 모의투자 우선 기본값
        dry_run: Optional[bool] = None,
        emergency_stop: Optional[bool] = None,
        rate_limit_per_sec: float = 10.0,
    ):
        self._appkey = appkey or os.environ.get("KIS_APPKEY", "")
        self._appsecret = appsecret or os.environ.get("KIS_APPSECRET", "")
        self._account_no = account_no or os.environ.get("KIS_ACCOUNT_NO", "")
        self._paper = paper
        self._dry_run = dry_run if dry_run is not None else (
            os.environ.get("DRY_RUN", "true").lower() == "true"
        )
        self._emergency_stop = emergency_stop if emergency_stop is not None else (
            os.environ.get("EMERGENCY_STOP", "false").lower() == "true"
        )
        self._rate_limiter = KisRateLimiter(rate_limit_per_sec)
        self._pykis = None
        self._token_refresh_thread: Optional[threading.Thread] = None
        self._ws_thread: Optional[threading.Thread] = None

        # 원번호 추적 체인 {new_number: original_number} (ORGN_ODNO 이중정정 방지)
        self._order_chain: Dict[str, str] = {}
        self._chain_lock = threading.Lock()

        # 미체결 주문 목록 {client_order_id: KisOrderRef}
        self._pending: Dict[str, KisOrderRef] = {}
        self._pending_lock = threading.Lock()

    # ------------------------------------------------------------------
    # pykis 클라이언트 초기화
    # ------------------------------------------------------------------

    def _ensure_pykis(self):
        """pykis PyKis 인스턴스 획득. credential 부재 시 None."""
        if self._pykis is not None:
            return self._pykis
        if not (self._appkey and self._appsecret and self._account_no):
            logger.warning("KIS credential 부재 — 실 네트워크 이연 (deferral-pinning)")
            return None
        try:
            from pykis import PyKis
            self._pykis = PyKis(
                appkey=self._appkey,
                appsecret=self._appsecret,
                account_number=self._account_no,
                virtual=self._paper,  # 모의투자 우선
            )
            logger.info("pykis 초기화 완료 (paper=%s)", self._paper)
            return self._pykis
        except Exception as exc:
            logger.error("pykis 초기화 실패: %s", exc)
            return None

    @property
    def is_paper(self) -> bool:
        return self._paper

    # ------------------------------------------------------------------
    # _clamp_to_balance — polymarket trader.py:283-289 패턴 (재코딩 금지)
    # ------------------------------------------------------------------

    def _clamp_to_balance(self, ticker: str, side: str, amount: float) -> float:
        """과매도 차단 — min(req, free_balance).

        polymarket trader.py:283-289 clamp 패턴 그대로 채택.
        SELL: 보유량 초과 주문 차단. BUY: KRW 잔고 초과 차단.
        """
        try:
            kis = self._ensure_pykis()
            if kis is None:
                return amount  # credential 없으면 그대로 (경계 스텁)

            if side.upper() == "SELL":
                # 보유 수량 조회
                balance = kis.account.balance()
                for pos in getattr(balance, "positions", []):
                    code = getattr(pos, "symbol", "") or getattr(pos, "code", "")
                    if str(code).zfill(6) == str(ticker).zfill(6):
                        free = float(getattr(pos, "qty", 0))
                        if free < amount:
                            logger.warning(
                                "_clamp_to_balance: SELL %s req=%s free=%s → clamp",
                                ticker, amount, free
                            )
                        return min(amount, free)
            elif side.upper() == "BUY":
                # KRW 잔고 조회
                balance = kis.account.balance()
                krw = float(getattr(balance, "krw", getattr(balance, "cash", amount)))
                return min(amount, krw)
        except Exception as exc:
            logger.debug("_clamp_to_balance 조회 실패: %s", exc)
        return amount

    # ------------------------------------------------------------------
    # order — 현물 매수/매도
    # ------------------------------------------------------------------

    def order(
        self,
        ticker: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        market: str = "KRX",
    ) -> Optional[KisOrderRef]:
        """현물 매수(BUY)/매도(SELL) 주문.

        Args:
            ticker: 종목코드 (예: "005930")
            side: "BUY" | "SELL"
            qty: 주문 수량
            price: 지정가 (None=시장가)
            market: "KRX" | "NAS" | "NYS" (H18 US FX 입력)

        Returns:
            KisOrderRef(주문번호 3-튜플) | None (DRY_RUN/EMERGENCY_STOP/실패)
        """
        ok, reason = _check_safety(self._dry_run, self._emergency_stop)
        if not ok:
            logger.info("order 차단: %s ticker=%s side=%s qty=%s", reason, ticker, side, qty)
            return None

        # _clamp_to_balance 경유 (과매도 차단)
        clamped_qty = self._clamp_to_balance(ticker, side, qty)
        if clamped_qty <= 0:
            logger.warning("order: clamp 후 수량 0 — 주문 취소 ticker=%s", ticker)
            return None

        self._rate_limiter.acquire()

        kis = self._ensure_pykis()
        if kis is None:
            # credential 없음 — 스텁 주문번호 반환
            return self._stub_order(ticker, side, clamped_qty, market)

        try:
            if side.upper() == "BUY":
                result = kis.stock(ticker).buy(price=price, qty=int(clamped_qty))
            else:
                result = kis.stock(ticker).sell(price=price, qty=int(clamped_qty))

            order_ref = KisOrderRef(
                branch=getattr(result, "branch", ""),
                number=getattr(result, "number", ""),
                account_no=self._account_no,
                symbol=ticker,
                market=market,
            )
            with self._pending_lock:
                self._pending[order_ref.client_order_id] = order_ref
            logger.info("order 완료: %s %s %s qty=%s", side, ticker, order_ref.number, clamped_qty)
            return order_ref
        except Exception as exc:
            logger.error("order 실패: %s", exc)
            return None

    def _stub_order(self, ticker: str, side: str, qty: float, market: str) -> KisOrderRef:
        """credential 없음 — 스텁 주문번호 (경계 계약 테스트용)."""
        ref = KisOrderRef(
            branch="000",
            number=str(uuid.uuid4())[:8].upper(),
            account_no=self._account_no or "TEST_ACCT",
            symbol=ticker,
            market=market,
        )
        with self._pending_lock:
            self._pending[ref.client_order_id] = ref
        logger.info("[STUB] order %s %s qty=%s → %s", side, ticker, qty, ref.number)
        return ref

    # ------------------------------------------------------------------
    # modify — H15 ORGN_ODNO 원번호 추적 (이중정정 방지)
    # ------------------------------------------------------------------

    def modify(
        self,
        order_ref: KisOrderRef,
        new_price: float,
        new_qty: Optional[int] = None,
    ) -> Optional[KisOrderRef]:
        """주문정정. H15 domestic_modify_order — ORGN_ODNO 원번호 추적 체인.

        이중정정 방지: 이미 정정된 주문의 원번호를 체인에 유지.
        """
        ok, reason = _check_safety(self._dry_run, self._emergency_stop)
        if not ok:
            return None

        self._rate_limiter.acquire()

        kis = self._ensure_pykis()
        if kis is None:
            return self._stub_modify(order_ref, new_price)

        pykis_order = order_ref.to_pykis_order_number(kis)
        if not pykis_order:
            return None

        try:
            # pykis order_modify.py:103/521 domestic_modify_order 그대로 사용
            from pykis.api.account.order_modify import domestic_modify_order
            result = domestic_modify_order(
                self=kis,
                order=pykis_order,
                price=new_price,
                qty=new_qty,
            )
            new_ref = KisOrderRef(
                branch=getattr(result, "branch", order_ref.branch),
                number=getattr(result, "number", order_ref.number),
                account_no=self._account_no,
                symbol=order_ref.symbol,
                market=order_ref.market,
                original_number=order_ref.number,  # ORGN_ODNO 체인 유지
            )
            # 원번호 체인 등록
            with self._chain_lock:
                orig = self._order_chain.get(order_ref.number, order_ref.number)
                self._order_chain[new_ref.number] = orig
            logger.info("modify 완료: %s → %s (orig=%s)", order_ref.number, new_ref.number, orig)
            return new_ref
        except Exception as exc:
            logger.error("modify 실패: %s", exc)
            return None

    def _stub_modify(self, order_ref: KisOrderRef, new_price: float) -> KisOrderRef:
        new_ref = KisOrderRef(
            branch=order_ref.branch,
            number=str(uuid.uuid4())[:8].upper(),
            account_no=self._account_no or "TEST_ACCT",
            symbol=order_ref.symbol,
            market=order_ref.market,
            original_number=order_ref.number,
        )
        with self._chain_lock:
            orig = self._order_chain.get(order_ref.number, order_ref.number)
            self._order_chain[new_ref.number] = orig
        logger.info("[STUB] modify %s → %s (orig=%s)", order_ref.number, new_ref.number, orig)
        return new_ref

    def get_original_number(self, number: str) -> str:
        """원번호 체인 조회 (ORGN_ODNO 이중정정 방지)."""
        with self._chain_lock:
            return self._order_chain.get(number, number)

    # ------------------------------------------------------------------
    # cancel — order_modify.py:607
    # ------------------------------------------------------------------

    def cancel(self, order_ref: KisOrderRef) -> bool:
        """주문취소. pykis cancel_order(:607) 그대로 사용."""
        ok, reason = _check_safety(self._dry_run, self._emergency_stop)
        if not ok:
            return False

        self._rate_limiter.acquire()

        kis = self._ensure_pykis()
        if kis is None:
            logger.info("[STUB] cancel %s", order_ref.number)
            with self._pending_lock:
                self._pending.pop(order_ref.client_order_id, None)
            return True

        pykis_order = order_ref.to_pykis_order_number(kis)
        if not pykis_order:
            return False

        try:
            from pykis.api.account.order_modify import cancel_order
            cancel_order(self=kis, order=pykis_order)
            with self._pending_lock:
                self._pending.pop(order_ref.client_order_id, None)
            logger.info("cancel 완료: %s", order_ref.number)
            return True
        except Exception as exc:
            logger.error("cancel 실패: %s", exc)
            return False

    # ------------------------------------------------------------------
    # pending — KisOrderNumber 3-튜플 from_number 서버주문번호
    # ------------------------------------------------------------------

    def pending(self) -> List[KisOrderRef]:
        """미체결 주문 목록. pykis order.py:346-358 KisOrderNumber 3-튜플 기반."""
        self._rate_limiter.acquire()
        kis = self._ensure_pykis()
        if kis is None:
            with self._pending_lock:
                return list(self._pending.values())

        try:
            pending_orders = kis.account.pending_orders()
            result = []
            for po in pending_orders:
                ref = KisOrderRef(
                    branch=getattr(po, "branch", ""),
                    number=getattr(po, "number", ""),
                    account_no=self._account_no,
                    symbol=getattr(po, "symbol", ""),
                    market=getattr(po, "market", "KRX"),
                )
                result.append(ref)
            return result
        except Exception as exc:
            logger.error("pending 조회 실패: %s", exc)
            return []

    # ------------------------------------------------------------------
    # _poll_and_amend — polymarket trader.py:314-337 패턴 (3×poll→cancel)
    # ------------------------------------------------------------------

    def _poll_and_amend(
        self,
        order_ref: KisOrderRef,
        new_price: float,
        poll_count: int = 3,
        poll_interval_sec: float = 2.0,
    ) -> Optional[KisOrderRef]:
        """미체결 → 정정 3회 → 취소. polymarket trader.py:314-337 poll-then-amend 채택.

        H15: 스마트주문 정정 — 체결 확인 후 미체결이면 가격 정정, 3회 실패 시 취소.
        """
        for attempt in range(poll_count):
            time.sleep(poll_interval_sec)
            # 미체결 확인
            pending_list = self.pending()
            is_pending = any(p.number == order_ref.number for p in pending_list)
            if not is_pending:
                logger.info("_poll_and_amend: 체결 확인 attempt=%d", attempt + 1)
                return order_ref  # 체결됨

            # 정정 시도
            modified = self.modify(order_ref, new_price)
            if modified:
                order_ref = modified
                logger.info("_poll_and_amend: 정정 attempt=%d → %s", attempt + 1, order_ref.number)
            else:
                logger.warning("_poll_and_amend: 정정 실패 attempt=%d", attempt + 1)

        # 3회 실패 → 취소
        logger.warning("_poll_and_amend: %d회 후 미체결, 취소", poll_count)
        self.cancel(order_ref)
        return None

    # ------------------------------------------------------------------
    # 토큰 갱신 — 24h(6h 보수 갱신 스케줄)
    # ------------------------------------------------------------------

    def start_token_refresh(self, interval_sec: float = 6 * 3600) -> None:
        """토큰 갱신 스레드 시작 (6h 보수 갱신, 1분당 1회 공유캐시 확인).

        pykis 토큰은 24h 유효. 6h 주기 갱신으로 만료 전 갱신.
        """
        if self._token_refresh_thread and self._token_refresh_thread.is_alive():
            return

        def _refresh_loop():
            while True:
                time.sleep(interval_sec)
                kis = self._ensure_pykis()
                if kis is None:
                    continue
                try:
                    # pykis 는 token.ensure() 또는 refresh() 로 갱신
                    token = getattr(kis, "token", None)
                    if token and hasattr(token, "refresh"):
                        token.refresh()
                        logger.info("KIS 토큰 갱신 완료")
                    elif hasattr(kis, "auth"):
                        kis.auth()
                        logger.info("KIS 토큰 재인증 완료")
                except Exception as exc:
                    logger.warning("KIS 토큰 갱신 실패: %s", exc)

        self._token_refresh_thread = threading.Thread(
            target=_refresh_loop, daemon=True, name="kis-token-refresh"
        )
        self._token_refresh_thread.start()
        logger.info("KIS 토큰 갱신 스레드 시작 (interval=%.0fh)", interval_sec / 3600)

    # ------------------------------------------------------------------
    # WebSocket — _run_forever / _restore_subscriptions / PINGPONG 그대로
    # pykis client/websocket.py:358/411/456 재코딩 금지 — 래퍼만
    # ------------------------------------------------------------------

    def start_websocket(self) -> bool:
        """pykis websocket 재연결 스레드 시작.

        _run_forever(reconnect=True, interval=5s) / _restore_subscriptions /
        PINGPONG 처리 = pykis 본체 그대로 위임.
        """
        kis = self._ensure_pykis()
        if kis is None:
            logger.info("[STUB] WebSocket 시작 스킵 (credential 없음)")
            return False

        try:
            # pykis websocket 클라이언트 참조
            ws_client = getattr(kis, "rtc", getattr(kis, "websocket", None))
            if ws_client is None:
                logger.warning("pykis WebSocket 클라이언트 없음")
                return False

            # reconnect=True 로 설정 후 _run_forever 위임
            if hasattr(ws_client, "reconnect"):
                ws_client.reconnect = True

            def _ws_loop():
                if hasattr(ws_client, "_run_forever"):
                    ws_client._run_forever()
                elif hasattr(ws_client, "connect"):
                    ws_client.connect()

            self._ws_thread = threading.Thread(
                target=_ws_loop, daemon=True, name="kis-websocket"
            )
            self._ws_thread.start()
            logger.info("KIS WebSocket 스레드 시작")
            return True
        except Exception as exc:
            logger.error("WebSocket 시작 실패: %s", exc)
            return False

    # ------------------------------------------------------------------
    # H17 — 가격제한폭/거래정지/하한가잠김 체크
    # ------------------------------------------------------------------

    def check_price_limit(
        self,
        ticker: str,
        price: float,
        ref_price: float,
        side: str,
    ) -> Tuple[bool, str]:
        """H17: 가격제한폭 ±30% / 거래정지 / 하한가잠김 매도불가 체크.

        Returns:
            (ok, reason): ok=True 이면 주문 가능.
        """
        if ref_price <= 0:
            return True, "ref_price 불명 — 스킵"

        upper = ref_price * 1.30
        lower = ref_price * 0.70

        if price > upper:
            return False, f"H17: 가격제한폭 상한 초과 ({price:.0f} > {upper:.0f})"
        if price < lower:
            if side.upper() == "SELL":
                return False, f"H17: 하한가잠김 매도불가 ({price:.0f} < {lower:.0f})"
            return False, f"H17: 가격제한폭 하한 미달 ({price:.0f} < {lower:.0f})"
        return True, "OK"

    # ------------------------------------------------------------------
    # H18 — US FX (KRW/USD)
    # ------------------------------------------------------------------

    def convert_usd_to_krw(self, usd_amount: float, fx_rate: float) -> float:
        """H18: US 종목 주문 시 KRW/USD FX 환산."""
        return usd_amount * fx_rate
