"""SeonbiRang Coin Selector -- 5팩터 코인 순위 산정 + 진입/청산 대상 선별

5팩터 스코어링:
  1. 추세 일관성 (30%): 1h/4h/24h 다중 타임프레임 합의
  2. 거래량 서지 (20%): 7일 평균 대비 거래량 급증
  3. 기술적 건강도 (20%): RSI 과매수 차단, BB 위치 보정
  4. 가격 모멘텀 (15%): 적정 범위 우대, 추격매수 감점
  5. 분산도 (15%): BTC 상관도 낮을수록 우대
"""

import logging
from dataclasses import dataclass

from seonbirang.config import SeonbirangConfig, COIN_BLACKLIST
from seonbirang.data_feeder import CoinData

logger = logging.getLogger("seonbirang.selector")


@dataclass
class CoinScore:
    """코인 평가 점수"""
    symbol: str
    score: float
    funding_rate: float = 0.0
    momentum_score: float = 0.0
    volume_24h: float = 0.0
    reason: str = ""
    # 5팩터 분해
    trend_score: float = 0.0
    volume_score: float = 0.0
    tech_score: float = 0.0
    momentum_sub: float = 0.0
    diversity_score: float = 0.0


class CoinSelector:
    """코인 스크리닝 및 순위 산정"""

    def __init__(self, config: SeonbirangConfig):
        self.config = config

    def rank_by_funding(self, data: dict[str, CoinData]) -> list[CoinScore]:
        """펀딩비 4팩터 순위 - 소수 정예, 오래 보유할 안정적 코인 선별

        4팩터 스코어링:
          1. 현재 펀딩비 크기 (40%): 수익의 원천
          2. 펀딩비 안정성 (30%): 7일간 양수 비율 + 낮은 변동성
          3. 유동성 (15%): 진입/청산 슬리피지 최소화
          4. 현선물 스프레드 (15%): 진입 비용 최소화

        하드 필터:
        - 현재 펀딩비 > min_funding_rate
        - 7일 평균 펀딩비 > min_avg_funding_rate (일시적 급등 제거)
        - 양수 비율 >= 70% (안정적으로 양수 유지)
        - 연환산 수익률 >= 10% (수수료 제외 후 의미 있는 수익)
        - 현선물 스프레드 < 0.15% (헤지 비용 제한)
        - 유동성: 선물 $10M+, 현물 $1M+
        """
        cfg = self.config.funding
        min_vol = self.config.rotation.min_volume_usdt_24h
        min_spot_vol = self.config.rotation.min_spot_volume_24h
        scores = []
        f_low_rate = 0
        f_unstable = 0
        f_low_apr = 0
        f_spread = 0
        f_liq = 0

        for sym, coin in data.items():
            if sym in COIN_BLACKLIST:
                continue
            if coin.funding_rate < cfg.min_funding_rate:
                f_low_rate += 1
                continue
            if coin.quote_volume_24h < min_vol:
                f_liq += 1
                continue
            if coin.spot_price <= 0:
                continue
            if coin.spot_quote_volume_24h < min_spot_vol:
                f_liq += 1
                continue

            # 현선물 스프레드 필터
            if coin.futures_price > 0 and coin.spot_price > 0:
                spread_pct = abs(coin.futures_price - coin.spot_price) / coin.spot_price * 100
                if spread_pct > cfg.spread_max_pct:
                    f_spread += 1
                    continue
            else:
                spread_pct = 0.1  # 기본값

            # 펀딩비 히스토리 분석 결과 필터 (enriched일 때만)
            if coin.funding_enriched:
                if coin.funding_avg_7d < cfg.min_avg_funding_rate:
                    f_unstable += 1
                    continue
                if coin.funding_positive_ratio < cfg.min_positive_ratio:
                    f_unstable += 1
                    continue

                # APR 계산: 평균 펀딩비 × 3회/일 × 365일 × 100 - 수수료(~0.1%×2)
                gross_apr = coin.funding_avg_7d * 3 * 365 * 100
                fee_apr = 0.1 * 2 * 365 / 30  # 월 2회 교체 가정 수수료
                net_apr = gross_apr - fee_apr
                if net_apr < cfg.min_apr_pct:
                    f_low_apr += 1
                    continue
            else:
                # 히스토리 미분석 시 현재 펀딩비 기반 추정
                net_apr = coin.funding_rate * 3 * 365 * 100 - 2.0

            # === 4팩터 스코어링 ===

            # 팩터 1: 현재 펀딩비 크기 (0~10)
            rate_score = min(10.0, coin.funding_rate * 10000)  # 0.1% = 10점

            # 팩터 2: 안정성 (0~10)
            if coin.funding_enriched:
                stability = coin.funding_positive_ratio * 7  # 100% = 7점
                # 낮은 변동성 보너스 (std < avg의 50%이면 +3)
                if coin.funding_avg_7d > 0:
                    cv = coin.funding_std / coin.funding_avg_7d  # 변동계수
                    stability += max(0, 3.0 - cv * 3)
                stability = min(10.0, stability)
            else:
                stability = 5.0  # 기본값

            # 팩터 3: 유동성 (0~10)
            vol_score = min(10.0, coin.quote_volume_24h / 50_000_000 * 10)

            # 팩터 4: 스프레드 (0~10) - 작을수록 좋음
            spread_score = max(0.0, 10.0 - spread_pct / cfg.spread_max_pct * 10)

            total = (
                rate_score * cfg.funding_score_w_rate
                + stability * cfg.funding_score_w_consistency
                + vol_score * cfg.funding_score_w_volume
                + spread_score * cfg.funding_score_w_spread
            ) * 10

            reason_parts = [
                f"총={total:.1f}",
                f"FR={coin.funding_rate*100:.4f}%",
                f"APR={net_apr:.0f}%",
            ]
            if coin.funding_enriched:
                reason_parts.append(f"평균={coin.funding_avg_7d*100:.4f}%")
                reason_parts.append(f"양수={coin.funding_positive_ratio*100:.0f}%")
            reason_parts.append(f"스프레드={spread_pct:.3f}%")
            reason_parts.append(f"vol=${coin.quote_volume_24h/1e6:.0f}M")

            scores.append(CoinScore(
                symbol=sym,
                score=total,
                funding_rate=coin.funding_rate,
                volume_24h=coin.quote_volume_24h,
                reason=" | ".join(reason_parts),
            ))

        if f_low_rate + f_unstable + f_low_apr + f_spread + f_liq > 0:
            logger.info(
                f"펀딩 순위: 제외 - 저펀딩{f_low_rate} 불안정{f_unstable} "
                f"저APR{f_low_apr} 고스프레드{f_spread} 저유동성{f_liq}"
            )

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:cfg.max_coins * 3]

    def rank_by_momentum(self, data: dict[str, CoinData]) -> list[CoinScore]:
        """5팩터 모멘텀 순위 — AI 코인 선별의 핵심

        652개 코인 → 기본필터 → 50개 kline 심화분석 → 5팩터 종합점수 → TOP N
        """
        cfg = self.config.rotation
        min_vol = cfg.min_volume_usdt_24h
        min_spot_vol = cfg.min_spot_volume_24h
        max_change = cfg.max_change_24h_pct
        scores = []

        f_manip = 0
        f_stagnant = 0
        f_spot = 0
        f_rsi = 0

        for sym, coin in data.items():
            if sym in COIN_BLACKLIST:
                continue
            if coin.quote_volume_24h < min_vol:
                continue
            if coin.spot_price <= 0:
                continue
            if coin.spot_quote_volume_24h < min_spot_vol:
                f_spot += 1
                continue
            if abs(coin.price_change_pct_24h) > max_change:
                f_manip += 1
                continue
            # 하락 코인은 롱 로테이션 대상 아님
            if coin.price_change_pct_24h < 0:
                continue
            if coin.price_change_pct_24h < 1.0:
                f_stagnant += 1
                continue

            # === RSI 하드 필터: 과매수 진입 차단 ===
            if coin.kline_enriched and coin.rsi_14 > cfg.rsi_overbought:
                f_rsi += 1
                continue

            # === 팩터 1: 추세 일관성 (30%) ===
            trend = self._score_trend(coin, cfg)

            # === 팩터 2: 거래량 서지 (20%) ===
            volume = self._score_volume_surge(coin, cfg)

            # === 팩터 3: 기술적 건강도 (20%) ===
            tech = self._score_technical(coin, cfg)

            # === 팩터 4: 가격 모멘텀 (15%) ===
            momentum = self._score_momentum(coin, cfg)

            # === 팩터 5: 분산도 (15%) ===
            diversity = self._score_diversification(coin)

            # 종합점수 (0~10 스케일)
            total = (
                trend * cfg.w_trend_consistency
                + volume * cfg.w_volume_surge
                + tech * cfg.w_technical_health
                + momentum * cfg.w_price_momentum
                + diversity * cfg.w_diversification
            ) * 10

            scores.append(CoinScore(
                symbol=sym,
                score=total,
                momentum_score=total,
                funding_rate=coin.funding_rate,
                volume_24h=coin.quote_volume_24h,
                trend_score=trend,
                volume_score=volume,
                tech_score=tech,
                momentum_sub=momentum,
                diversity_score=diversity,
                reason=self._build_reason(coin, trend, volume, tech, momentum, diversity, total),
            ))

        if f_manip + f_stagnant + f_spot + f_rsi > 0:
            logger.info(
                f"모멘텀 순위: 제외 - 조작{f_manip} 정체{f_stagnant} "
                f"현물저유동성{f_spot} RSI과매수{f_rsi}"
            )

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:cfg.universe_size]

    # ── 5팩터 개별 스코어링 ──────────────────────────────

    @staticmethod
    def _score_trend(coin: CoinData, cfg) -> float:
        """팩터 1: 다중 타임프레임 추세 일관성 (0~10)"""
        if not coin.kline_enriched:
            # kline 미분석 → 24h 변동만으로 추정
            return 5.0 if coin.price_change_pct_24h > 2.0 else 3.0

        t1h = coin.trend_1h > 0
        t4h = coin.trend_4h > 0
        t24h = coin.price_change_pct_24h > 0

        if t1h and t4h and t24h:
            return 10.0   # 3개 타임프레임 모두 상승 — 강한 추세
        if t4h and t24h:
            return 7.0    # 4h+24h 상승, 1h 조정 — 건강한 pullback
        if t1h and t24h:
            return 6.0    # 1h+24h 상승 — 최근 반등
        if t24h:
            return 3.0    # 24h만 상승, 단기 하락 — 약세 전환 가능
        return 1.0         # 대부분 하락

    @staticmethod
    def _score_volume_surge(coin: CoinData, cfg) -> float:
        """팩터 2: 거래량 서지 비율 (0~10)"""
        ratio = coin.volume_surge_ratio

        if ratio >= cfg.volume_surge_ideal:
            return 10.0   # 3배+ 거래량 폭증 — 기관 관심
        if ratio >= cfg.volume_surge_min:
            # 1.5~3.0 → 5~10 선형
            return 5.0 + 5.0 * (ratio - cfg.volume_surge_min) / (cfg.volume_surge_ideal - cfg.volume_surge_min)
        if ratio >= 1.0:
            return 3.0    # 평균 수준
        return 1.0         # 거래량 감소 — 관심 이탈

    @staticmethod
    def _score_technical(coin: CoinData, cfg) -> float:
        """팩터 3: RSI + BB 기술적 건강도 (0~10)"""
        if not coin.kline_enriched:
            return 5.0

        rsi = coin.rsi_14
        bb = coin.bb_position
        score = 0.0

        # RSI 점수
        if cfg.rsi_sweet_low <= rsi <= cfg.rsi_sweet_high:
            score = 10.0   # 이상적 구간 (40~65)
        elif 30 <= rsi < cfg.rsi_sweet_low:
            score = 7.0    # 과매도 접근 — 매수 기회
        elif cfg.rsi_sweet_high < rsi <= cfg.rsi_overbought:
            score = 4.0    # 과매수 접근 — 주의
        elif rsi < 30:
            score = 5.0    # 극 과매도 — 낙하 중일 수 있음
        else:
            score = 2.0    # RSI > 70은 하드필터에서 이미 제거

        # BB 보정
        if bb < 0.2:
            score += 2.0   # 하단 밴드 근처 — 반등 기대
        elif bb > 0.9:
            score -= 3.0   # 상단 밴드 돌파 — 과열

        return max(0.0, min(10.0, score))

    @staticmethod
    def _score_momentum(coin: CoinData, cfg) -> float:
        """팩터 4: 가격 모멘텀 적정성 (0~10)

        3~10% 일간 상승이 최적, 너무 높으면 추격매수 위험.
        """
        ch = coin.price_change_pct_24h

        if cfg.momentum_sweet_low <= ch <= cfg.momentum_sweet_high:
            return 10.0   # 3~10% — 최적 구간
        if 1.0 <= ch < cfg.momentum_sweet_low:
            return 7.0    # 1~3% — 초기 움직임
        if cfg.momentum_sweet_high < ch <= cfg.anti_chase_threshold:
            return 5.0    # 10~15% — 강하지만 추격 주의
        if ch > cfg.anti_chase_threshold:
            return 2.0    # 15%+ — 추격매수 위험
        return 0.0         # 하락 (이미 필터됨)

    @staticmethod
    def _score_diversification(coin: CoinData) -> float:
        """팩터 5: BTC 상관도 역수 (0~10)

        상관도 낮을수록 포트폴리오 분산 효과 높음.
        """
        corr = abs(coin.btc_correlation)

        if corr < 0.3:
            return 10.0   # 독립적 — 최고 분산
        if corr < 0.5:
            return 7.0    # 낮은 상관
        if corr < 0.7:
            return 4.0    # 중간 상관
        return 1.0         # 높은 상관 — BTC 프록시

    @staticmethod
    def _build_reason(
        coin: CoinData, trend, volume, tech, momentum, diversity, total
    ) -> str:
        """스코어 사유 문자열 생성"""
        parts = [
            f"총={total:.1f}",
            f"추세={trend:.0f}",
            f"거래량={volume:.0f}(x{coin.volume_surge_ratio:.1f})",
        ]
        if coin.kline_enriched:
            parts.append(f"RSI={coin.rsi_14:.0f}")
            parts.append(f"BB={coin.bb_position:.2f}")
            parts.append(f"BTC상관={coin.btc_correlation:.2f}")
        parts.append(f"24h={coin.price_change_pct_24h:+.1f}%")
        parts.append(f"vol=${coin.quote_volume_24h/1e6:.0f}M")
        return " | ".join(parts)

    # ── 진입/청산 대상 결정 ──────────────────────────────

    def select_funding_targets(
        self,
        current_symbols: set[str],
        ranked: list[CoinScore],
        max_new: int = 3,
    ) -> tuple[list[CoinScore], list[str]]:
        """펀딩 전략 진입/청산 대상 결정"""
        enter = []
        for coin in ranked:
            if coin.symbol not in current_symbols and len(enter) < max_new:
                enter.append(coin)

        ranked_symbols = {c.symbol for c in ranked}
        exit_syms = [s for s in current_symbols if s not in ranked_symbols]
        return enter, exit_syms

    def select_rotation_targets(
        self,
        current_symbols: set[str],
        ranked: list[CoinScore],
        max_replace: int = 2,
    ) -> tuple[list[CoinScore], list[str]]:
        """로테이션 전략 진입/청산 대상 결정"""
        top_n = self.config.rotation.top_n
        top_symbols = {c.symbol for c in ranked[:top_n]}

        exit_syms = [s for s in current_symbols if s not in top_symbols]
        exit_syms = exit_syms[:max_replace]

        enter = []
        for coin in ranked[:top_n]:
            if coin.symbol not in current_symbols and len(enter) < len(exit_syms):
                enter.append(coin)

        remaining_slots = top_n - len(current_symbols) + len(exit_syms) - len(enter)
        if remaining_slots > 0:
            for coin in ranked[:top_n]:
                if coin.symbol not in current_symbols and coin not in enter:
                    enter.append(coin)
                    remaining_slots -= 1
                    if remaining_slots <= 0:
                        break

        return enter, exit_syms
