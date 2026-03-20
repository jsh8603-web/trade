"""AltRang 설정 -- 환경변수 + 시스템 파라미터

모든 API 키는 .env에서 로드한다. 직접 하드코딩 금지.
"""

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class UpbitConfig:
    access_key: str = field(default_factory=lambda: os.getenv("UPBIT_ACCESS_KEY", ""))
    secret_key: str = field(default_factory=lambda: os.getenv("UPBIT_SECRET_KEY", ""))
    rest_url: str = "https://api.upbit.com/v1"


@dataclass(frozen=True)
class BinanceConfig:
    api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    spot_rest_url: str = "https://api.binance.com"
    futures_rest_url: str = "https://fapi.binance.com"
    futures_ws_url: str = "wss://fstream.binance.com/stream"
    spot_ws_url: str = "wss://stream.binance.com:9443/stream"
    exchange_info_refresh_hours: int = 6  # exchangeInfo 캐시 갱신 주기


@dataclass
class FundingParams:
    """펀딩비 수확 전략 파라미터 (SB_FUNDING_ENABLED=true 시 활성화)"""
    enabled: bool = field(
        default_factory=lambda: os.getenv("SB_FUNDING_ENABLED", "false").lower() == "true"
    )
    min_funding_rate: float = field(
        default_factory=lambda: float(os.getenv("SB_FUNDING_MIN_RATE", "0.0002"))
    )
    exit_funding_threshold: float = 0.0001
    max_coins: int = field(
        default_factory=lambda: int(os.getenv("SB_FUNDING_MAX_COINS", "3"))
    )
    position_size_usdt: float = field(
        default_factory=lambda: float(os.getenv("SB_FUNDING_POSITION_USDT", "300"))
    )
    max_total_usdt: float = field(
        default_factory=lambda: float(os.getenv("SB_FUNDING_MAX_TOTAL_USDT", "1000"))
    )
    leverage: int = 1
    rebalance_interval_min: int = 120   # 2시간마다 리밸런스 (느린 전략)
    min_hold_hours: int = 24            # 최소 24시간 보유 (안정성)
    # --- 고급 펀딩비 분석 ---
    history_lookback: int = 21          # 과거 펀딩비 조회 횟수 (21 = 7일)
    min_avg_funding_rate: float = 0.00005  # 7일 중앙값 최소 펀딩비 (0.005%)
    min_positive_ratio: float = 0.6     # 7일간 양수 비율 최소 60%
    min_apr_pct: float = 3.0            # 최소 연환산 수익률 3% (수수료 제외, 현실적)
    spread_max_pct: float = 1.5          # 현물-선물 스프레드 최대 1.5% (저가 코인 허용)
    funding_score_w_rate: float = 0.40  # 현재 펀딩비 가중치
    funding_score_w_consistency: float = 0.30  # 안정성(양수비율) 가중치
    funding_score_w_volume: float = 0.15  # 유동성 가중치
    funding_score_w_spread: float = 0.15  # 스프레드 가중치


@dataclass
class RotationParams:
    """알트코인 로테이션 전략 파라미터"""
    universe_size: int = field(
        default_factory=lambda: int(os.getenv("SB_ROTATION_UNIVERSE", "30"))
    )
    top_n: int = field(
        default_factory=lambda: int(os.getenv("SB_ROTATION_TOP_N", "5"))
    )
    rotation_interval_min: int = field(
        default_factory=lambda: int(os.getenv("SB_ROTATION_INTERVAL_MIN", "240"))
    )
    lookback_hours: int = 24
    min_volume_usdt_24h: float = 10_000_000
    position_size_usdt: float = field(
        default_factory=lambda: float(os.getenv("SB_ROTATION_POSITION_USDT", "200"))
    )
    max_total_usdt: float = field(
        default_factory=lambda: float(os.getenv("SB_ROTATION_MAX_TOTAL_USDT", "1000"))
    )
    stop_loss_pct: float = field(
        default_factory=lambda: float(os.getenv("SB_ROTATION_STOP_LOSS", "5.0"))
    )
    take_profit_pct: float = field(
        default_factory=lambda: float(os.getenv("SB_ROTATION_TAKE_PROFIT", "15.0"))
    )
    max_replace_per_cycle: int = 2
    min_hold_hours: int = 4
    min_spot_volume_24h: float = 1_000_000  # 현물 최소 거래대금 ($1M)
    max_change_24h_pct: float = 50.0  # 펌프앤덤프 필터 (50% 초과 변동 제외)

    # --- 고급 5팩터 스코어링 가중치 (합 = 1.0) ---
    w_trend_consistency: float = 0.30   # 다중 타임프레임 추세 일관성
    w_volume_surge: float = 0.20        # 거래량 서지 (7일 평균 대비)
    w_technical_health: float = 0.20    # RSI/BB 기술적 건강도
    w_price_momentum: float = 0.15      # 적정 모멘텀 (과도하면 감점)
    w_diversification: float = 0.15     # BTC 상관도 (낮을수록 우대)

    # --- 기술적 임계값 ---
    rsi_overbought: float = 70.0        # RSI 과매수 → 진입 차단
    rsi_sweet_low: float = 40.0         # RSI 이상 구간 하한
    rsi_sweet_high: float = 65.0        # RSI 이상 구간 상한
    anti_chase_threshold: float = 15.0  # 추격매수 감점 기준 (%)
    momentum_sweet_low: float = 3.0     # 이상적 일간 수익 하한
    momentum_sweet_high: float = 10.0   # 이상적 일간 수익 상한
    volume_surge_min: float = 1.5       # 최소 서지 배율
    volume_surge_ideal: float = 3.0     # 이상적 서지 배율
    enrichment_top_n: int = 50          # kline 심화 분석 대상 수


@dataclass
class SafetyParams:
    """안전장치"""
    dry_run: bool = field(
        default_factory=lambda: os.getenv("SB_DRY_RUN", os.getenv("DRY_RUN", "true")).lower() == "true"
    )
    emergency_stop: bool = field(
        default_factory=lambda: os.getenv("SB_EMERGENCY_STOP", "false").lower() == "true"
    )
    max_daily_trades: int = 50
    max_position_ratio: float = 0.8
    use_bnb_fee: bool = field(
        default_factory=lambda: os.getenv("SB_USE_BNB_FEE", "true").lower() == "true"
    )
    min_bnb_reserve: float = 0.05
    portfolio_drawdown_pct: float = 10.0


@dataclass(frozen=True)
class DBConfig:
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))


# Blacklist: 스테이블코인, 래핑토큰 등 로테이션 제외
COIN_BLACKLIST_BINANCE = {
    "USDCUSDT", "BUSDUSDT", "TUSDUSDT", "USDPUSDT", "FDUSDUSDT",
    "DAIUSDT", "EURUSDT", "GBPUSDT",
}
COIN_BLACKLIST_UPBIT = {
    "KRW-USDT", "KRW-USDC", "KRW-DAI",
}
# 런타임에 거래소별 선택
COIN_BLACKLIST = COIN_BLACKLIST_BINANCE  # 기본값, AltrangConfig에서 재설정


class AltrangConfig:
    """전체 설정 컨테이너"""

    def __init__(self):
        self.exchange_name: str = os.getenv("SB_EXCHANGE", "binance").lower()
        self.binance = BinanceConfig()
        self.upbit = UpbitConfig()
        self.funding = FundingParams()
        self.rotation = RotationParams()
        self.safety = SafetyParams()
        self.db = DBConfig()

        # 거래소별 블랙리스트 설정
        global COIN_BLACKLIST
        if self.exchange_name == "upbit":
            COIN_BLACKLIST = COIN_BLACKLIST_UPBIT
            # 업비트는 선물 없음 → 펀딩비 강제 비활성화
            if self.funding.enabled:
                self.funding.enabled = False
        else:
            COIN_BLACKLIST = COIN_BLACKLIST_BINANCE

    @property
    def is_upbit(self) -> bool:
        return self.exchange_name == "upbit"

    @property
    def quote_currency(self) -> str:
        """기축통화: Binance=USDT, Upbit=KRW"""
        return "KRW" if self.is_upbit else "USDT"

    @property
    def min_order_amount(self) -> float:
        """최소 주문 금액"""
        return 5000.0 if self.is_upbit else 12.0

    def validate(self) -> list[str]:
        errors = []
        if self.is_upbit:
            if not self.upbit.access_key:
                errors.append("UPBIT_ACCESS_KEY 미설정")
            if not self.upbit.secret_key:
                errors.append("UPBIT_SECRET_KEY 미설정")
        else:
            if not self.binance.api_key:
                errors.append("BINANCE_API_KEY 미설정")
            if not self.binance.api_secret:
                errors.append("BINANCE_API_SECRET 미설정")
        if self.funding.leverage > 5:
            errors.append(f"레버리지 {self.funding.leverage}x 과다 (최대 5x)")
        if self.funding.max_total_usdt + self.rotation.max_total_usdt > 50000:
            errors.append("총 투자 한도 $50,000 초과")
        return errors

    def summary(self) -> str:
        def mask(s: str) -> str:
            return f"{s[:4]}...{s[-4:]}" if len(s) > 8 else "***"

        exchange_str = self.exchange_name.upper()
        if self.is_upbit:
            api_str = f"Upbit: {mask(self.upbit.access_key)}"
        else:
            api_str = f"Binance: {mask(self.binance.api_key)}"

        funding_status = "ON" if self.funding.enabled else "OFF"
        currency = self.quote_currency

        lines = [
            f"=== AltRang (알트랑) Config [{exchange_str}] ===",
            f"DRY_RUN: {self.safety.dry_run}",
            f"{api_str}",
        ]

        if not self.is_upbit:
            lines.extend([
                f"--- 펀딩비 수확 [{funding_status}] ---",
                f"  Min Rate: {self.funding.min_funding_rate*100:.2f}%",
                f"  Max Coins: {self.funding.max_coins}",
                f"  Position: ${self.funding.position_size_usdt:,.0f}",
                f"  Budget: ${self.funding.max_total_usdt:,.0f}",
            ])

        lines.extend([
            f"--- 알트코인 로테이션 ---",
            f"  Universe: {self.rotation.universe_size}개",
            f"  Top N: {self.rotation.top_n}",
            f"  Interval: {self.rotation.rotation_interval_min}분",
            f"  Position: {self.rotation.position_size_usdt:,.0f} {currency}",
            f"  Budget: {self.rotation.max_total_usdt:,.0f} {currency}",
            f"  SL: {self.rotation.stop_loss_pct}% / TP: {self.rotation.take_profit_pct}%",
            f"--- 안전장치 ---",
            f"  Daily Trades: {self.safety.max_daily_trades}",
        ])

        if not self.is_upbit:
            lines.append(f"  BNB Fee: {self.safety.use_bnb_fee}")

        return "\n".join(lines) + "\n"
