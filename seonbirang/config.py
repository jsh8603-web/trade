"""SeonbiRang 설정 -- 환경변수 + 시스템 파라미터

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
class BinanceConfig:
    api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    spot_rest_url: str = "https://api.binance.com"
    futures_rest_url: str = "https://fapi.binance.com"
    futures_ws_url: str = "wss://fstream.binance.com/stream"
    spot_ws_url: str = "wss://stream.binance.com:9443/stream"


@dataclass
class FundingParams:
    """펀딩비 수확 전략 파라미터"""
    min_funding_rate: float = field(
        default_factory=lambda: float(os.getenv("SB_FUNDING_MIN_RATE", "0.0005"))
    )
    exit_funding_threshold: float = 0.0001
    max_coins: int = field(
        default_factory=lambda: int(os.getenv("SB_FUNDING_MAX_COINS", "5"))
    )
    position_size_usdt: float = field(
        default_factory=lambda: float(os.getenv("SB_FUNDING_POSITION_USDT", "200"))
    )
    max_total_usdt: float = field(
        default_factory=lambda: float(os.getenv("SB_FUNDING_MAX_TOTAL_USDT", "1000"))
    )
    leverage: int = 1
    rebalance_interval_min: int = 60
    min_hold_hours: int = 8


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
COIN_BLACKLIST = {
    "USDCUSDT", "BUSDUSDT", "TUSDUSDT", "USDPUSDT", "FDUSDUSDT",
    "DAIUSDT", "EURUSDT", "GBPUSDT",
}


class SeonbirangConfig:
    """전체 설정 컨테이너"""

    def __init__(self):
        self.binance = BinanceConfig()
        self.funding = FundingParams()
        self.rotation = RotationParams()
        self.safety = SafetyParams()
        self.db = DBConfig()

    def validate(self) -> list[str]:
        errors = []
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

        return (
            f"=== SeonbiRang (선비랑) Config ===\n"
            f"DRY_RUN: {self.safety.dry_run}\n"
            f"Binance: {mask(self.binance.api_key)}\n"
            f"--- 펀딩비 수확 ---\n"
            f"  Min Rate: {self.funding.min_funding_rate*100:.2f}%\n"
            f"  Max Coins: {self.funding.max_coins}\n"
            f"  Position: ${self.funding.position_size_usdt:,.0f}\n"
            f"  Budget: ${self.funding.max_total_usdt:,.0f}\n"
            f"--- 알트코인 로테이션 ---\n"
            f"  Universe: {self.rotation.universe_size}개\n"
            f"  Top N: {self.rotation.top_n}\n"
            f"  Interval: {self.rotation.rotation_interval_min}분\n"
            f"  Position: ${self.rotation.position_size_usdt:,.0f}\n"
            f"  Budget: ${self.rotation.max_total_usdt:,.0f}\n"
            f"  SL: {self.rotation.stop_loss_pct}% / TP: {self.rotation.take_profit_pct}%\n"
            f"--- 안전장치 ---\n"
            f"  BNB Fee: {self.safety.use_bnb_fee}\n"
            f"  Daily Trades: {self.safety.max_daily_trades}\n"
        )
