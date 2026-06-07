"""
fred_adapter.py — FRED / ALFRED(vintage·PIT) 데이터 어댑터 경계.

설계 정합 (§5.8-A/C/F):
- §5.8-C: 지표 소스 = FRED(`fredapi`) + ALFRED vintage(PIT) · ECOS(한국) · OpenBB.
- §5.8-F: PIT 가드 ① lookahead → ALFRED vintage + 발표일 정렬로 완전 제거.
- §5.8-A: FRED-MD(1959:01~ 128시리즈) · FRED-QD 장기 훈련 가정 — vintage 처리(무료).
- §5.8-A 추가 피처: CFNAI·NFCI·STLFSI·ADS·금리커브 침체확률 (상당수 FRED 수신).

차용/참조:
- feedoracle-macro-mcp 의 신호셋 구조(86 FRED 시리즈, 7 가중신호) 차용 → FRED_SERIES 큐레이션.
- AlpacaTradingAgent Macro Analyst 의 FRED 연동 패턴(fredapi) 참조.

설계 원칙: 이 파일은 *경계* 다. 실제 네트워크 호출은 fredapi 가 하고, 본 모듈은
(a) 시리즈 ID 큐레이션 (b) PIT 정렬 계약 (c) 오프라인/테스트용 어댑터 인터페이스만 정의.
키 없거나 네트워크 불가 시 NullFredAdapter 로 graceful degrade (status=unavailable).

미해결 가정:
- fredapi 의 `get_series_first_release` / ALFRED `get_series_vintage_dates` 로 PIT 구현 가능하나,
  vintage 전수 처리는 비용 → 핫패스는 first-release(발표시점값) 만 쓰고, 백테스트는 full vintage.
- 한국(KRW) 거시는 ECOS API 키 별도 → KrEcosAdapter 인터페이스만, 미연동 시 KRW=USD 레짐 폴백.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, Protocol

import pandas as pd


# ---------------------------------------------------------------------------
# FRED 시리즈 큐레이션 — Investment Clock + macro.md 피처 (feedoracle 신호셋 차용)
# ---------------------------------------------------------------------------
# 분류기 코어 입력 (Investment Clock 성장×인플레 축).
FRED_SERIES = {
    # --- 성장축 (growth) ---
    "GDPC1": "real_gdp",                # 실질 GDP (분기, §5.8-A Investment Clock 성장).
    "A261RX1Q020SBEA": "real_gdi",      # 실질 GDI (GDP-GDI 크로스체크, macro.md 151~156).
    "PAYEMS": "nonfarm_payrolls",       # 비농업 고용 (XGBoost SHAP 1위, macro.md 110).
    "INDPRO": "industrial_production",
    "UNRATE": "unemployment_rate",      # Sahm/Michez 입력.
    "JTSJOL": "job_openings",           # JOLTS 구인 (Michez v̂ 입력).
    "CLF16OV": "labor_force",           # 구인율 = openings / labor_force.
    # --- 인플레축 (inflation) ---
    "CPILFESL": "core_cpi",             # 코어 CPI (§5.8-A 인플레축).
    "PCEPILFE": "core_pce",             # 코어 PCE (Fed 선호, macro.md 33).
    "T5YIE": "breakeven_5y",            # 5년 기대인플레 (시장 선행).
    # --- 선행/금융 피처 (§5.8-A) ---
    "T10Y2Y": "yield_10y_2y",           # 장단기 금리차 (macro.md 129~136).
    "NFCI": "nfci",                     # Chicago Fed 금융상황지수.
    "STLFSI4": "stl_financial_stress",  # St.Louis 금융스트레스.
    "BAA10Y": "credit_spread_baa",      # 신용스프레드 IG (macro.md 25 CP경색 프록시).
    "BAMLH0A0HYM2": "credit_spread_hy_oas",  # HY OAS (자문: 최고 risk-regime 지표. IG BAA10Y 보완).
    "RECPROUSM156N": "fred_recession_prob",  # Smoothed recession probability.
    "CFNAI": "cfnai",                   # Chicago Fed 국가활동지수.
    # --- cross-sleeve factor driver (M4/M6 — sleeve 거시연관 실측 1차 driver, 독립검증 통과) ---
    # ⛔Fisher 공선 주의: nominal_10y + real_rate_10y + breakeven_5y 를 한 회귀에 동시 투입 금지
    # (DGS10 ≈ DFII10 + T5YIE 항등 → 완전공선). factor 모델은 real / breakeven 중 택일.
    "DFII10": "real_rate_10y",          # 10Y TIPS 실질금리 (gold/reit/방어주 rate 채널, M3 1차 driver).
    "DTWEXBGS": "dollar_broad",         # broad TWI 달러 (전 sleeve cross-validated 1차 driver, M3).
    "DCOILWTICO": "oil_wti",            # WTI 유가 (commodity energy / gold inflation hedge).
    "DGS10": "nominal_10y",             # 명목 10Y (term structure level, T10Y2Y spread 보완).
    "DGS2": "nominal_2y",               # 명목 2Y (curve steepness level 분리).
}

# NBER 침체일자 — *학습 라벨 전용* (§5.8-A NBER lag 분리; 실시간 추론 금지).
FRED_NBER_RECESSION = "USREC"

# market-priced 일별 시리즈 — ALFRED first_release vintage 과다(3000+)로 ValueError → silent drop 되던 군.
# 이들은 시장가격 기반이라 revision≈0 (P2 독립 audit 2026-06-02: DFII10/T5YIE/T10Y2Y 2024 vintage
# revised=0, max spread=0.0000 실측 입증 → latest==first_release). first_release 대신 get_series(latest)로
# 직행해 vintage 호출 자체를 회피하되, as_of causal mask 는 observation-date 기준이라 PIT lookahead 없음.
_MARKET_PRICED_DAILY = frozenset({"DFII10", "T5YIE", "T10Y2Y", "DGS10", "DGS2", "BAA10Y"})

# first_release(ALFRED) 가 stale 에서 멈추는 군 — fredapi get_series_first_release 가 NFCI(1976-10)/
# STLFSI4(2004-11) 에서 최신 미반환(실측 2026-06-02: stale 값이 "최신"으로 silent 오염). 실시간 추론은
# latest 최신값이 정확(stale=명백 오류). ★단 revision 있음(NFCI |diff| mean 0.35·STLFSI4 0.05)→
# 백테스트 PIT 는 ALFRED vintage 필요(Phase V TODO: get_series_all_releases + as_of). 현 실시간 e2e=latest.
_FIRST_RELEASE_BROKEN = frozenset({"NFCI", "STLFSI4"})

# first_release 우회(latest 직행) 군 = market-priced(revision≈0) ∪ first_release-broken(stale).
_LATEST_FALLBACK = _MARKET_PRICED_DAILY | _FIRST_RELEASE_BROKEN


@dataclass
class SeriesPoint:
    """PIT-safe 단일 관측 — value + 발표일(release_date) 동봉 (§5.8-F freeze)."""
    value: float
    observation_date: pd.Timestamp   # 데이터가 가리키는 기간.
    release_date: pd.Timestamp       # 실제 공표일 (causal mask 기준).


# ---------------------------------------------------------------------------
# 어댑터 프로토콜 (인터페이스 경계)
# ---------------------------------------------------------------------------
class FredAdapter(Protocol):
    """거시 데이터 공급 계약. 구현체: RealFredAdapter(fredapi) / NullFredAdapter(폴백) / 테스트 fake."""

    def get_series(self, series_id: str, as_of: Optional[pd.Timestamp] = None) -> Optional[pd.Series]:
        """
        series_id 시계열 반환. as_of 지정 시 그 날짜까지 *발표된* 값만 (PIT causal mask).
        as_of=None 이면 최신 전체. 실패 시 None (호출측은 degrade).
        """
        ...

    def is_available(self) -> bool:
        ...


class NullFredAdapter:
    """키/네트워크 없을 때 폴백 — 항상 None. 분류기는 last-good stale / unavailable 로 degrade."""

    def get_series(self, series_id, as_of=None):
        return None

    def is_available(self):
        return False


# ★PD(2026-06-07): 모듈 전역 raw 캐시 — 백테스트 시계열(coin_track_macro 매 collect 신규 adapter)
#   가 같은 series 를 매 bar full-fetch(220개월×29s 폭주)하던 것을 인스턴스 무관 1회 공유로 차단.
#   키=(pit_mode, series_id). raw(pre-mask)는 as_of 무관 = 전역 안전. 마스킹은 매 호출 fresh(PIT 보존).
_GLOBAL_RAW_CACHE: dict = {}


class RealFredAdapter:
    """
    fredapi 래퍼. 핫패스는 first-release(발표시점값), 백테스트는 full vintage(ALFRED).
    실제 import 는 지연 — fredapi 미설치 환경에서도 모듈 로드 가능.
    """

    def __init__(self, api_key: Optional[str] = None, pit_mode: str = "first_release"):
        self.api_key = api_key
        self.pit_mode = pit_mode   # "first_release" | "vintage" | "latest"
        self._client = None
        # ★Y5 fetch 캐시: 같은 series_id 의 full fetch(client.get_series*)는 as_of 무관(as_of=이후 causal
        #   mask 만). build_sleeve_regime_ids 가 rep date N회 classify(as_of) → 같은 시리즈 N회 full-fetch
        #   (255s 주범). raw 시리즈를 series_id 별 1회 캐시 → mask 는 매 호출 fresh slice(PIT 보존).
        #   인스턴스 수명 = 단일 build/collect 사이클(coin_track_macro 매 collect 신규 adapter) → stale 0.
        self._raw_cache: dict = {}

    def _ensure_client(self):
        if self._client is None:
            try:
                from fredapi import Fred  # 지연 import.
                self._client = Fred(api_key=self.api_key)
            except Exception:
                self._client = False  # 영구 실패 마킹.
        return self._client

    def is_available(self):
        return self._ensure_client() not in (None, False)

    def get_series(self, series_id, as_of=None):
        client = self._ensure_client()
        if client in (None, False):
            return None
        try:
            _ck = (self.pit_mode, series_id)   # pit_mode 격리 — 전역 캐시 raw 오염 방지.
            s = _GLOBAL_RAW_CACHE.get(_ck)
            if s is None:
                if self.pit_mode == "first_release" and series_id not in _LATEST_FALLBACK:
                    # 발표시점값 = lookahead 없음 (§5.8-F).
                    s = client.get_series_first_release(series_id)
                else:
                    # latest. _LATEST_FALLBACK = market-priced 일별(revision≈0, vintage ValueError 회피)
                    # ∪ first_release-broken(NFCI/STLFSI4 stale). as_of mask(아래)가 observation-date 기준
                    # causal cut → 실시간 PIT lookahead 없음. ★단 broken 군 백테스트 revision 은 Phase V vintage.
                    s = client.get_series(series_id)
                _GLOBAL_RAW_CACHE[_ck] = s            # raw(pre-mask) 전역 캐시 — as_of 무관이라 안전
                self._raw_cache[series_id] = s        # 인스턴스 캐시도 유지(하위호환)
            if as_of is not None:
                s = s[s.index <= as_of]   # causal mask(매 호출 fresh slice, PIT 보존).
            return s.dropna()
        except Exception as _exc:  # C2: source_missing 라벨 — 동작 동일(None), silent 제거
            import logging as _log
            _log.getLogger(__name__).warning(
                "RealFredAdapter.get_series source_missing: series_id=%r [label=source_missing] exc=%r",
                series_id, _exc,
            )
            return None


# ---------------------------------------------------------------------------
# 거시 피처 번들 — 분류기 입력 단위 (한 시점 스냅샷)
# ---------------------------------------------------------------------------
@dataclass
class MacroFeatureBundle:
    """
    분류기가 한 사이클에 받는 피처 묶음. 시계열(JM 학습용) + 최신 스칼라(규칙용) 동봉.
    fetched_at = 적재 시각, data_as_of = 가장 최신 발표일 (status/age 산출).
    """
    series: dict = field(default_factory=dict)        # {logical_name: pd.Series}
    fetched_at: float = field(default_factory=time.time)
    data_as_of: Optional[pd.Timestamp] = None
    available: bool = True

    def latest(self, name: str) -> Optional[float]:
        s = self.series.get(name)
        if s is None or len(s) == 0:
            return None
        return float(s.iloc[-1])

    def ts(self, name: str) -> Optional[pd.Series]:
        return self.series.get(name)


def fetch_macro_bundle(
    adapter: FredAdapter,
    as_of: Optional[pd.Timestamp] = None,
    series_map: Optional[dict] = None,
) -> MacroFeatureBundle:
    """
    어댑터로 FRED_SERIES 를 일괄 적재해 MacroFeatureBundle 로 정규화한다.
    설계 §5.8-C 수집모드: 핫패스 retrieve only — 본 함수는 *이미 적재된 어댑터*에서 읽는 게 이상적이나,
    어댑터가 RealFredAdapter 면 라이브 fetch (백그라운드 Qwen pre-load 가 캐시를 채워두면 캐시 히트).
    """
    series_map = series_map or FRED_SERIES
    if not adapter.is_available():
        return MacroFeatureBundle(available=False)

    out, latest_dates = {}, []
    for fred_id, name in series_map.items():
        s = adapter.get_series(fred_id, as_of=as_of)
        if s is not None and len(s) > 0:
            out[name] = s
            latest_dates.append(s.index[-1])

    # 구인율 파생 (Michez v̂ 입력): job_openings / labor_force * 100.
    if "job_openings" in out and "labor_force" in out:
        jo, lf = out["job_openings"], out["labor_force"]
        common = jo.index.intersection(lf.index)
        if len(common) > 0:
            out["vacancy_rate"] = (jo[common] / lf[common] * 100.0).dropna()

    data_as_of = max(latest_dates) if latest_dates else None
    return MacroFeatureBundle(series=out, data_as_of=data_as_of, available=len(out) > 0)
