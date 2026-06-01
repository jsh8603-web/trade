"""core/rules/seed_builder.py — 리서치 데이터 → seed 확보 파이프라인 (S11, 사용자 핵심 누락).

사용자 요구(프롬프트 + cyclical.yaml 직접 메모): "메인이 seed 사전정의 + 파이프라인이
학습 시드 무한정 확장(다산업·다기간 무한대)". rule 엔진(S0~S9)에 넣을 **연료(seed)를
실데이터/리서치에서 뽑는 부분**. 자문 R4/R3 정합:
- (정량) τ 임계는 sector_multiples(Damodaran/French 실데이터) 로 **앵커링** — 큐레이션 상수
  하드코딩이 아니라 섹터 정상 멀티플 기준 상대값. "raw 분위가 아닌 구조적 기준선".
- (정성) 국면전환기 공시 → 밸류에이션 근거/밸류트랩 키워드 LLM 추출(v1=hook+큐레이션 시드).
  LLM 은 변수·방향·키워드만, τ 는 데이터 적합(R4 anchoring, 환각 방어).
- (무한확장) 새 산업·기간 카드 append → consensus(S9)·promotion_gate(S3)가 조정·승격.

파이프라인 3단:
  1. load_signal_seeds: config/sector_rules/*.yaml → sector 별 Signal (threshold_anchor resolve)
  2. extract_research_keywords: 공시/리포트 → 밸류에이션 근거·밸류트랩 키워드 (LLM hook)
  3. register_period_variant: 같은 산업 다른 기간의 seed 변형 등록 (무한확장, consensus 입력)
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

import yaml

from core.rules.signal import Signal
from core.pit.as_of import resolve_as_of, AsOfLike

# 실데이터 provider (cache 기반, go-live 전엔 빈 결과 → 큐레이션 fallback).
try:
    from stock.data.sector_multiples import DamodaranProvider
    _HAS_PROVIDER = True
except Exception:
    _HAS_PROVIDER = False

# 큐레이션 멀티플 시드 (Damodaran 2024 근사, findings R3 "LLM 사전 context 주입").
# ⛔ 실데이터 cache(data/sector_multiples/) 도착 시 _sector_multiple 이 자동 override.
_CURATED_MULTIPLE = {
    "semiconductor": {"ev_ebitda": 16.0, "pb": 4.0, "ps": 5.0},
    "chemicals":     {"ev_ebitda": 8.0, "pb": 1.2, "ps": 1.0},
    "steel":         {"ev_ebitda": 6.0, "pb": 0.8, "ps": 0.6},
    "biotech":       {"ps": 8.0, "pb": 5.0},
    "internet":      {"ps": 7.0, "ev_ebitda": 22.0},
}
# yaml metric → Damodaran metric 키 매핑
_DAMO_METRIC = {"ev_ebitda": "ev_ebitda", "pb": "pbv", "ps": "ps"}


def _sector_multiple(sector: str, metric: str, as_of) -> Optional[float]:
    """섹터 정상 멀티플: 실데이터 cache 우선 → 큐레이션 fallback (R3 사전주입)."""
    if _HAS_PROVIDER:
        try:
            damo_metric = _DAMO_METRIC.get(metric, metric)
            for snap in DamodaranProvider().fetch(damo_metric, as_of):
                if snap.sector == sector:
                    return float(snap.value)
        except Exception:
            pass
    return (_CURATED_MULTIPLE.get(sector) or {}).get(metric)


# ---------------------------------------------------------------------------
# 1) signal seed 로드 + 실데이터 threshold 앵커링
# ---------------------------------------------------------------------------

def _resolve_threshold(spec: dict, sector: str, as_of: AsOfLike) -> Optional[float]:
    """threshold(고정) 또는 threshold_anchor(sector_multiples × factor)를 실값으로."""
    if "threshold" in spec:
        return float(spec["threshold"])
    anchor = spec.get("threshold_anchor")
    if not anchor:
        return None
    base = _sector_multiple(sector, anchor["metric"], resolve_as_of(as_of))
    if base is None or (isinstance(base, float) and base != base):   # None/NaN
        return None
    return float(base) * float(anchor.get("factor", 1.0))


def load_signal_seeds(config_dir: Optional[str] = None,
                      as_of: AsOfLike = "2024-01-01") -> dict[str, list[Signal]]:
    """config/sector_rules/*.yaml → {sector: [Signal]}. threshold_anchor 는 실데이터 앵커.

    archetype YAML 1개가 여러 sector 를 커버 → sector 별로 τ 를 따로 앵커링해 Signal 분기.
    anchor resolve 실패(데이터 없음) signal 은 skip(경고 note) — 결측 강건(B6).
    """
    if config_dir is None:
        here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_dir = os.path.join(here, "config", "sector_rules")
    out: dict[str, list[Signal]] = {}
    for path in sorted(glob.glob(os.path.join(config_dir, "*.yaml"))):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        archetype = data["archetype"]
        for sector in data.get("sectors", []):
            sigs: list[Signal] = []
            for spec in data.get("signals", []):
                thr = _resolve_threshold(spec, sector, as_of)
                if thr is None:
                    continue   # 앵커 불가 → skip (결측 강건)
                sigs.append(Signal(
                    id=f"{spec['id']}__{sector}", version=spec.get("version", "v1"),
                    archetype=archetype, feature=spec["feature"], op=spec["op"],
                    threshold=thr, kind=spec.get("kind", "cheap"),
                    weight=float(spec.get("weight", 1.0)),
                ))
            out.setdefault(sector, []).extend(sigs)
    return out


# ---------------------------------------------------------------------------
# 2) 리서치 키워드 추출 (LLM hook, v1=큐레이션 시드)
# ---------------------------------------------------------------------------

@dataclass
class ResearchKeywords:
    sector: str
    valuation_basis: list[str] = field(default_factory=list)   # 싸다고 볼 근거 키워드
    trap_signals: list[str] = field(default_factory=list)      # 밸류트랩 경고 키워드
    source: str = "curated"                                    # curated | llm

# 큐레이션 시드 — 자문 R3/R4 의 "반도체 관점" + 변형. LLM 추출 전 베이스라인.
_CURATED_KEYWORDS = {
    "semiconductor": ResearchKeywords("semiconductor",
        ["book_to_bill 반등", "ASP 상승전환", "재고 정상화", "공정전환 capex 일단락"],
        ["peak EPS", "capex 정점", "사이클 고점 마진", "ASP 하락 시작"]),
    "chemicals": ResearchKeywords("chemicals",
        ["스프레드 회복", "가동률 상승", "원료가 안정"],
        ["증설 사이클 정점", "스프레드 고점", "수요 둔화"]),
    "biotech": ResearchKeywords("biotech",
        ["임상 3상 진입", "파이프라인 확장", "기술이전 계약"],
        ["현금소진 가속", "임상 실패 binary", "희석 증자"]),
}


def extract_research_keywords(
    sector: str,
    filings_text: Optional[str] = None,
    as_of: AsOfLike = "2024-01-01",
    llm_fn: Optional[Callable[[str, str], dict]] = None,
) -> ResearchKeywords:
    """국면전환기 공시 → 밸류에이션 근거·밸류트랩 키워드.

    v1: llm_fn 없으면 큐레이션 시드 반환. llm_fn 주면 (sector, filings) → dict 호출(미래 연결).
    ⛔ LLM 은 키워드·방향만 — 임계 τ 는 load_signal_seeds 의 데이터 앵커 몫(R4 환각 방어).
    """
    if llm_fn and filings_text:
        d = llm_fn(sector, filings_text)
        return ResearchKeywords(sector, d.get("valuation_basis", []),
                                d.get("trap_signals", []), source="llm")
    return _CURATED_KEYWORDS.get(sector, ResearchKeywords(sector))


# ---------------------------------------------------------------------------
# 3) 무한확장 — 같은 산업 다른 기간 / 새 산업 seed 변형 등록
# ---------------------------------------------------------------------------

@dataclass
class PeriodVariant:
    """같은 sector 의 특정 기간 seed 변형 (사용자: '다른 기간 추가 정의 무한대')."""
    sector: str
    period_label: str          # 예: "2016-17 메모리 슈퍼사이클"
    regime_id: int
    signal_overrides: dict = field(default_factory=dict)   # {signal_id: new_threshold}
    valid_from: Optional[date] = None


class SeedRegistry:
    """seed 의 무한확장 레지스트리. consensus(S9)·promotion_gate(S3) 입력."""

    def __init__(self):
        self._base: dict[str, list[Signal]] = {}
        self._variants: list[PeriodVariant] = []

    def load_base(self, config_dir: Optional[str] = None, as_of: AsOfLike = "2024-01-01"):
        self._base = load_signal_seeds(config_dir, as_of)
        return self

    def register_period_variant(self, variant: PeriodVariant) -> None:
        """새 기간/국면 seed 변형 추가 (무한확장). 실제 승격은 promotion_gate(S3) 통과 후."""
        self._variants.append(variant)

    def signals_for(self, sector: str, regime_id: Optional[int] = None) -> list[Signal]:
        """sector(+regime) 의 유효 signal = base + 해당 기간 변형 override 적용."""
        sigs = list(self._base.get(sector, []))
        if regime_id is None:
            return sigs
        ov: dict[str, float] = {}
        for v in self._variants:
            if v.sector == sector and v.regime_id == regime_id:
                ov.update(v.signal_overrides)
        if not ov:
            return sigs
        out = []
        for s in sigs:
            base_id = s.id.split("__")[0]
            if base_id in ov:
                out.append(s.model_copy(update={"threshold": ov[base_id]}))
            else:
                out.append(s)
        return out

    @property
    def variant_count(self) -> int:
        return len(self._variants)


if __name__ == "__main__":
    # 1) signal seed 로드 + 실데이터 앵커링
    seeds = load_signal_seeds(as_of="2024-01-01")
    assert "semiconductor" in seeds, list(seeds)
    semi = {s.id.split("__")[0]: s for s in seeds["semiconductor"]}
    # ev_ebitda threshold = sector median(16.0) × 0.7 = 11.2 (실데이터 앵커)
    assert abs(semi["cyc_ev_ebitda_disc"].threshold - 16.0 * 0.7) < 1e-6, semi["cyc_ev_ebitda_disc"].threshold
    print(f"1) seed 로드: semiconductor {len(seeds['semiconductor'])}개, ev_ebitda τ={semi['cyc_ev_ebitda_disc'].threshold:.2f} (median 16.0×0.7 앵커)")

    # 2) _margin_peak anchor(데이터 없음) → 해당 signal skip (결측 강건)
    assert "cyc_trap_margin_peak" not in semi, "앵커 불가 signal 이 skip 안 됨"
    print(f"2) 앵커 불가 signal skip: cyc_trap_margin_peak 제외(결측 강건) OK")

    # 3) 고정 τ signal 은 그대로
    assert semi["cyc_cheapz"].threshold == -1.0
    print(f"3) 고정 τ: cyc_cheapz={semi['cyc_cheapz'].threshold}")

    # 4) 리서치 키워드 (큐레이션)
    kw = extract_research_keywords("semiconductor")
    assert "peak EPS" in kw.trap_signals
    print(f"4) 키워드(반도체): 근거={kw.valuation_basis[:2]} 함정={kw.trap_signals[:2]} src={kw.source}")

    # 5) LLM hook 주입 (미래 연결 인터페이스)
    fake_llm = lambda sec, txt: {"valuation_basis": ["수주 급증"], "trap_signals": ["일회성 이익"]}
    kw2 = extract_research_keywords("steel", filings_text="...", llm_fn=fake_llm)
    assert kw2.source == "llm" and "수주 급증" in kw2.valuation_basis
    print(f"5) LLM hook: {kw2.valuation_basis} src={kw2.source}")

    # 6) 무한확장: 기간 변형 등록 → regime별 threshold override
    reg = SeedRegistry().load_base(as_of="2024-01-01")
    reg.register_period_variant(PeriodVariant(
        "semiconductor", "2016-17 메모리 슈퍼사이클", regime_id=0,
        signal_overrides={"cyc_cheapz": -1.5}))   # 슈퍼사이클엔 더 보수적
    base_sig = {s.id.split("__")[0]: s for s in reg.signals_for("semiconductor")}
    var_sig = {s.id.split("__")[0]: s for s in reg.signals_for("semiconductor", regime_id=0)}
    assert base_sig["cyc_cheapz"].threshold == -1.0 and var_sig["cyc_cheapz"].threshold == -1.5
    print(f"6) 무한확장: base τ={base_sig['cyc_cheapz'].threshold} → regime0 변형 τ={var_sig['cyc_cheapz'].threshold} (variant {reg.variant_count}개)")

    print("S11 seed_builder self-test PASS")
