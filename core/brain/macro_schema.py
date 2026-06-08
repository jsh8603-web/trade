"""
macro_schema.py — `macro_view` 공통 계약 + 거시 enum/dataclass (brain 단일 SSOT).

설계 정합 (IMPLEMENTATION_PROMPT §5.8):
- §5.8 스키마: macro_view = regime(per-bloc) + stance + 근거 + 인용ID + status(fresh/stale/unavailable) + age.
- §5.8-A: classifier(현재)≠forecaster(선행) → regime_now + regime_forecast(+horizon) 필드 분리.
- §5.8-A: per-bloc 레짐 (KRW/USD 독립 키잉; US overheat + KR recovery 가능).
- §5.8-D/B1: present·well-formed만 검증. outage 시 last-good stale로 degrade (H29) — 청산·리밸런싱 가능.

코드화한 macro.md 리서치:
- Investment Clock 4분면 (성장×인플레) = macro.md "성장/인플레 동학" + §5.8-A Investment Clock.
- Regime enum = §5.8-B 표(Reflation/Recovery/Overheat/Stagflation).

미해결 가정:
- 5번째 레짐("Slowdown/Disinflation") 은 도입 안 함 — 설계 §5.8-B 표가 정확히 4분면이라 그에 정박.
  필요 시 RegimeLabel 확장 + IC_TARGET_WEIGHTS 행 추가만으로 확장 가능.
"""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Optional


# ----------------------------------------------------------------------------
# Enums — Investment Clock 4분면 (성장축 × 인플레축)
# ----------------------------------------------------------------------------
class RegimeLabel(str, enum.Enum):
    """
    Merrill Lynch Investment Clock 4분면. (macro.md 거시 동학 + §5.8-B 표)

      성장 \\ 인플레 |   하락(disinflation)   |   상승(inflation)
      ---------------+------------------------+----------------------
      상승 (growth↑) |   RECOVERY             |   OVERHEAT
      하락 (growth↓) |   REFLATION            |   STAGFLATION

    - REFLATION : 성장↓·인플레↓ → 채권 최우위 (중앙은행 완화 기대).
    - RECOVERY  : 성장↑·인플레↓ → 주식 최우위 (골디락스).
    - OVERHEAT  : 성장↑·인플레↑ → 원자재 최우위.
    - STAGFLATION: 성장↓·인플레↑ AND **절대 고물가** → 실물/원자재/금 (진짜 스태그플레이션).
    - SLOWDOWN  : 성장↓·인플레↑(상대 z) BUT **절대 물가 modest** → late-cycle/연착륙.

    ★절대 CPI 게이트(2026-06-08, R1~4 자문+실측 검증): 상대 z 4분면만으로는 저물가 시대의
    둔화기를 STAGFLATION 으로 오라벨(2017-26 "Stagflation" 실현 CPI +2.57%=고물가 아님,
    진짜 고물가 2021-22는 이미 OVERHEAT). regime_classifier 가 STAGFLATION 분면에 절대 CPI
    게이트를 걸어 미달 시 SLOWDOWN 분리. 임계=외부 수입(AQR 주식-채권 상관전환~3% / Neville>5%).
    """
    REFLATION = "Reflation"
    RECOVERY = "Recovery"
    OVERHEAT = "Overheat"
    STAGFLATION = "Stagflation"
    SLOWDOWN = "Slowdown"


class Bloc(str, enum.Enum):
    """통화권(bloc) — per-bloc 레짐 분리 (§5.8-A). FX(H26) = 두 bloc 잇는 다리."""
    USD = "USD"
    KRW = "KRW"


class ViewStatus(str, enum.Enum):
    """macro_view 신선도 상태 — freshness ≠ liveness (C3). degrade 경로 (H29)."""
    FRESH = "fresh"            # 이번 사이클에 새로 계산됨.
    STALE = "stale"           # last-good 재사용 (소스 outage / 데이터 만료) — 그래도 사용 가능.
    UNAVAILABLE = "unavailable"  # last-good 조차 없음 — Prior(IC표)만으로 degrade.


# ----------------------------------------------------------------------------
# 단일 bloc 레짐 추정 결과
# ----------------------------------------------------------------------------
@dataclass
class RegimeEstimate:
    """
    한 bloc 의 레짐 추정. classifier(now) 와 forecaster(forecast) 를 명시 분리한다 (§5.8-A).
    """
    bloc: Bloc

    # classifier — 현재 레짐 (실시간 PIT 피처로만 추정; NBER lag 미사용).
    regime_now: RegimeLabel
    confidence_now: float          # [0,1] — JM proba 또는 규칙 일치도.

    # forecaster — 선행 레짐 (선행지표 기반 N개월 후 추정). classifier 와 별개여야 한다.
    regime_forecast: Optional[RegimeLabel] = None
    forecast_horizon_months: Optional[int] = None
    confidence_forecast: Optional[float] = None

    # 근거 — 어느 지표/방법이 이 판정을 만들었는가 (감사·메타라벨링용).
    method: str = ""               # "investment_clock" | "jump_model" | "hmm" | "ensemble"
    evidence: dict = field(default_factory=dict)   # {growth_z, infl_z, sahm, michez, yield_curve, ...}
    citation_ids: list = field(default_factory=list)  # FRED 시리즈 id, NBER, 리포트ID 등.

    def is_disagreement(self) -> bool:
        """classifier vs forecaster 발산 — 레짐 전환 임박 신호 (§5.8-G②)."""
        return (
            self.regime_forecast is not None
            and self.regime_forecast != self.regime_now
        )


# ----------------------------------------------------------------------------
# macro_view — AssetTrack / portfolio_orchestrator 가 소비하는 최종 계약
# ----------------------------------------------------------------------------
@dataclass
class MacroView:
    """
    brain 의 거시 출력. 매 사이클 regime_classifier 가 결정론 baseline 으로 채운다 (C3).
    macro_reasoning(LLM) 은 macro-trigger 시에만 stance/근거를 enrich.

    portfolio_orchestrator 계약 (§5.8-D):
      - regime_to_weights 는 per-bloc regime_now 를 BL Prior 선택에 사용.
      - B1 은 present·well-formed 만 검증 (status/age 필드 존재 + regimes 비어있지 않음).
    """
    # per-bloc 레짐 (USD / KRW 분리).
    regimes: dict                  # {Bloc: RegimeEstimate}

    # 정성 stance (LLM enrich 시 채워짐; 평상시 빈 dict).
    # {asset_sleeve: float} — IC Prior 대비 tilt 편차 (-1=강한 underweight, +1=강한 overweight).
    stance: dict = field(default_factory=dict)

    # 신선도 (§5.8 status/age).
    status: ViewStatus = ViewStatus.FRESH
    as_of_ts: float = field(default_factory=time.time)   # 이 view 가 계산된 시각.
    data_as_of_ts: Optional[float] = None                # 근거 데이터의 최신 발표일 (PIT).

    # 근거/감사.
    rationale: str = ""            # thesis 요약 (LLM enrich 시).
    counter_thesis: str = ""       # 최강 반대 thesis (§5.8-D) — LLM enrich 시.
    citation_ids: list = field(default_factory=list)
    caution_flags: list = field(default_factory=list)    # §5.8-H 메타라벨링 caution.

    @property
    def age_seconds(self) -> float:
        return time.time() - self.as_of_ts

    def regime(self, bloc: Bloc) -> Optional[RegimeEstimate]:
        return self.regimes.get(bloc)

    def is_well_formed(self) -> bool:
        """B1 게이트 — present·well-formed 검증 (§5.8-D). 내용 정확성은 검증 안 함."""
        if not self.regimes:
            return False
        if self.status not in ViewStatus:
            return False
        for est in self.regimes.values():
            if not isinstance(est, RegimeEstimate):
                return False
            if not isinstance(est.regime_now, RegimeLabel):
                return False
            if not (0.0 <= est.confidence_now <= 1.0):
                return False
        return True

    def degrade_to_stale(self) -> "MacroView":
        """소스 outage 시 last-good 을 stale 로 마킹해 재사용 (H29). 청산·리밸런싱은 계속 가능."""
        self.status = ViewStatus.STALE
        return self

    @classmethod
    def unavailable(cls) -> "MacroView":
        """last-good 조차 없을 때 — 빈 view. regime_to_weights 는 IC 중립 Prior 로 degrade."""
        return cls(regimes={}, status=ViewStatus.UNAVAILABLE)
