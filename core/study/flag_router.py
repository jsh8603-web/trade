"""core/study/flag_router.py — confidence_hooks(블록5) → 신뢰도 누적 → ★동적 가중치 재적합 (골격 G4).

STUDY-KIT §2 작업순서 3단계 + 사용자 확정 지시의 코드화:
  "flag 달고 끝이 아니다. flag(확신/거부) 누적 → 가정 신뢰도 누적 → (a) lens 는 agent 가 읽어
   반영하고, (b) **flag 에 따라 지표별 동적 가중치가 실제로 변경되는 건 신규 구현 코드**다."

이 모듈이 (b)의 신규 코드다. 두 입력 경로:
  1. on_trade(hyp, 'confirm'|'reject') — 매 거래마다 직접 flag 누적(라이브 judge 사후평가).
  2. emit_from_ic(hyp, scores, returns) — backtest outcome 배치 → weight_falsification(본체)으로
     Rank-IC·e-CUSUM 붕괴 자동 판정 후 flag 누적.

누적 = Beta(α,β) posterior(confirm→α++, reject→β++). 신뢰도 = posterior mean = α/(α+β).
★동적 가중치: `tilt_weights` 가 신뢰도로 base_weight 를 곱셈 변조(확신↑→가중↑, 거부↑→가중↓) 후
L1 합 보존 정규화 + cap clip. weight_falsification·weight_card **본체는 안 고친다**(wrap+post-hoc).

down-only 불변식과 무관: tilt 는 *학습 비중* 단계의 재적합이지 judge 의 사이징 천장이 아니다.
opt-in(study_register 가 INV_R15_WEIGHTS on 일 때만 tilt 적용). prior(0.5)면 tilt=1(무변동).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from core.assume.weight_falsification import rank_ic, score_ic_breakdown_eprocess
from core.study.study_loader import ConfidenceHook


_PRIOR_MEAN = 0.5            # Beta(1,1) prior mean = 중립(tilt 1.0)
_TILT_MIN, _TILT_MAX = 0.5, 2.0   # 가중 변조 범위(과도 leverage 제한)


# ---------------------------------------------------------------------------
# FlagAccumulator — 한 가설의 확신/거부 누적 + 신뢰도
# ---------------------------------------------------------------------------

@dataclass
class FlagAccumulator:
    """확신/거부 flag 누적기. Beta(α,β) posterior + IC 히스토리(e-CUSUM 입력)."""
    alpha: float = 1.0          # Beta prior α (confirm 누적)
    beta: float = 1.0           # Beta prior β (reject 누적)
    confirms: int = 0
    rejects: int = 0
    ic_history: list = field(default_factory=list)
    last_e_value: float = 1.0
    last_breakdown: bool = False

    def confirm(self, n: int = 1) -> None:
        self.alpha += n
        self.confirms += n

    def reject(self, n: int = 1) -> None:
        self.beta += n
        self.rejects += n

    def confidence(self) -> float:
        """posterior mean α/(α+β) ∈ (0,1). 0.5=중립, >0.5 확신 우세, <0.5 거부 우세."""
        return float(self.alpha / (self.alpha + self.beta))

    def credible_lo(self, z: float = 1.0) -> float:
        """Beta posterior 정규근사 하한(보수적 신뢰도). 표본 적으면 0.5 쪽으로 수축."""
        a, b = self.alpha, self.beta
        m = a / (a + b)
        var = (a * b) / ((a + b) ** 2 * (a + b + 1.0))
        return float(np.clip(m - z * np.sqrt(var), 0.0, 1.0))


# ---------------------------------------------------------------------------
# FlagRouter — 가설↔지표 연결 + outcome 라우팅 + 동적 가중치 재적합
# ---------------------------------------------------------------------------

class FlagRouter:
    """confidence_hooks 등록 → 거래 outcome → flag 누적 → 지표별 신뢰도 → 가중치 tilt."""

    def __init__(self):
        self._acc: dict = {}                 # hypothesis_id → FlagAccumulator
        self._hyp_indicator: dict = {}       # hypothesis_id → indicator_id (블록4 연결)
        self._hooks: dict = {}               # hypothesis_id → ConfidenceHook(블록5 메타)

    # --- 등록 (블록5 hook + 블록4 indicator 연결) ---
    def register(self, hook: ConfidenceHook, *, indicator_id: Optional[str] = None) -> None:
        hid = hook.hypothesis_id
        self._hooks[hid] = hook
        self._acc.setdefault(hid, FlagAccumulator())
        if indicator_id:
            self._hyp_indicator[hid] = indicator_id

    def _acc_of(self, hypothesis_id: str) -> FlagAccumulator:
        return self._acc.setdefault(hypothesis_id, FlagAccumulator())

    # --- 경로 1: 매 거래 직접 flag (라이브 judge 사후평가) ---
    def on_trade(self, hypothesis_id: str, signal: str, n: int = 1) -> None:
        """signal ∈ {'confirm','reject'}. 매 거래 outcome 으로 누적."""
        acc = self._acc_of(hypothesis_id)
        if signal == "confirm":
            acc.confirm(n)
        elif signal == "reject":
            acc.reject(n)
        else:
            raise ValueError(f"signal 은 'confirm'|'reject' (받음: {signal!r})")

    # --- 경로 2: backtest IC 배치 → weight_falsification 본체로 자동 판정 ---
    def emit_from_ic(self, hypothesis_id: str, scores: Sequence[float], returns: Sequence[float],
                     *, baseline_ic: float = 0.0, sd: float = 0.1, alpha: float = 0.05) -> str:
        """이번 배치의 Rank-IC 계산 → 히스토리 누적 → e-CUSUM 붕괴면 reject / 양 IC 면 confirm.

        weight_falsification.rank_ic + score_ic_breakdown_eprocess(본체) 를 그대로 사용.
        반환: emit 된 flag('confirm'|'reject'|'neutral').
        """
        acc = self._acc_of(hypothesis_id)
        ic, _ = rank_ic(scores, returns)
        acc.ic_history.append(ic)
        breakdown, e_value, _ = score_ic_breakdown_eprocess(
            acc.ic_history, baseline_ic=baseline_ic, sd=sd, alpha=alpha)
        acc.last_e_value = e_value
        acc.last_breakdown = breakdown
        if breakdown:                       # PRIMARY 붕괴 = 거부
            acc.reject()
            return "reject"
        if ic > baseline_ic:                # baseline 위 = 예측력 유지 = 확신
            acc.confirm()
            return "confirm"
        return "neutral"                    # baseline 근처 = 중립(누적 없음)

    # --- 신뢰도 조회 ---
    def confidence(self, hypothesis_id: str) -> float:
        return self._acc_of(hypothesis_id).confidence()

    def confidence_by_indicator(self, *, conservative: bool = False) -> dict:
        """indicator_id → 신뢰도. conservative=True 면 credible 하한(소표본 수축)."""
        out: dict = {}
        for hid, ind in self._hyp_indicator.items():
            acc = self._acc_of(hid)
            out[ind] = acc.credible_lo() if conservative else acc.confidence()
        return out

    # --- ★U1 flag→lens: 라이브 누적 신뢰도를 lens 주입용 한 줄 요약 ---
    def confidence_note(self, *, conservative: bool = False, max_items: int = 8) -> Optional[str]:
        """flag 누적 신뢰도를 lens(블록1) 주입용 요약 문자열로. 누적 0이면 None(무주입=무회귀).

        lens_store.render(confidence_note=...) 로 전달 → qwen(agent 판단)이 저신뢰 가설을 보수적으로
        읽는다. confirm/reject 가 1건이라도 있는 지표만 포함(prior 만 있는 지표는 제외).
        예: "mvrv=0.71(C8/R2); funding=0.33(C1/R4)".
        """
        items: list = []
        for hid, ind in self._hyp_indicator.items():
            acc = self._acc_of(hid)
            if acc.confirms or acc.rejects:
                c = acc.credible_lo() if conservative else acc.confidence()
                items.append(f"{ind}={c:.2f}(C{acc.confirms}/R{acc.rejects})")
        if not items:
            return None
        return "; ".join(items[:max_items])

    # --- ★동적 가중치 재적합 (신규 코드 — flag→weight) ---
    def tilt_weights(self, base_weights: Sequence[float], series_ids: Sequence[str],
                     *, cap: float = 0.40, conservative: bool = False) -> np.ndarray:
        """신뢰도로 base_weight 를 곱셈 변조 → L1 합 보존 정규화 → cap clip.

        tilt_i = clip(confidence_i / 0.5, 0.5, 2.0). 확신 누적(conf>0.5)→가중↑, 거부(conf<0.5)→↓.
        flag 가 없는(미등록) 지표는 tilt=1.0(무변동). prior 만 있으면 conf=0.5→tilt=1.0.
        ★이 함수가 "flag→동적 가중치 변경"의 신규 구현. 단순 기록 아님.
        """
        w = np.asarray(base_weights, dtype=float)
        n = len(w)
        if n == 0:
            return w
        conf = self.confidence_by_indicator(conservative=conservative)
        tilt = np.ones(n, dtype=float)
        for i, sid in enumerate(series_ids):
            c = conf.get(sid)
            if c is not None:
                tilt[i] = float(np.clip(c / _PRIOR_MEAN, _TILT_MIN, _TILT_MAX))
        w2 = w * tilt
        # L1 합 보존(원 비중 총량 유지) + cap — water-filling(클립 후 잔여를 미capped 에 분배 반복)
        return _cap_normalize(w2, float(np.sum(np.abs(w))), cap)

    # --- ★U2 flag→corr_prior: 저신뢰 가설 edge 의 상관 prior 를 약화(→독립) ---
    def corr_prior_shrink(self, base_corr_prior, series_ids: Sequence[str],
                          *, level: str = "micro", conservative: bool = False) -> np.ndarray:
        """저신뢰 가설이 가리키는 edge 의 corr_prior 를 신뢰도로 약화. flag→상관 prior 경로(U2).

        ★single-writer 불변식(자문 3R, CONSULT-DECISIONS-layering-20260530.md): belief 기반 shrink 는
        **_micro(within-sleeve 종목 상관)에만** 허용. level='macro'(cross-sleeve 거시 상관)면 belief 를
        차단(base 그대로 no-op). _macro 는 실현 cross-sleeve 수익률·regime 전이로만 갱신해야 reflexive
        loop(종목 flag→macro Σ→"리스크 극저" 오판→drawdown 직전 최대 베팅, pro-cyclical)가 구조적으로
        막힌다. 거시·채권 study(cross-sleeve driver)는 level='macro' 로 호출.

        edge 식별: hook.affects_edge=[a,b] 직접 우선 → 없으면 affects_indicator(node)가 닿는 모든 edge 를
        node 신뢰도로 근사(fallback). ratio=clip(conf/0.5, 0.5, 2.0): conf<0.5(거부 우세)→prior 0쪽 수축,
        conf>0.5(확신)→강화. 대각 1 유지, off-diag [-1,1] clip. base 미변경(copy). flag 누적 0 가설은
        무변동(무회귀). RegimeGlasso.fit(corr_prior=) 의 prior 로 주입 → eb_shrink target 이 신뢰도 추종.
        """
        P = np.array(base_corr_prior, dtype=float).copy()
        if str(level).lower() != "micro":       # ★belief→_macro 차단(single-writer, reflexive loop 방지)
            return P                             # cross-sleeve/거시 상관 prior 는 flag 미적용(실현 수익률 전용)
        if P.ndim != 2 or P.shape[0] != P.shape[1]:
            return P
        idx = {sid: i for i, sid in enumerate(series_ids)}
        for hid, hook in self._hooks.items():
            acc = self._acc_of(hid)
            if not (acc.confirms or acc.rejects):
                continue                                   # 누적 0 = 무변동(무회귀)
            c = acc.credible_lo() if conservative else acc.confidence()
            ratio = float(np.clip(c / _PRIOR_MEAN, _TILT_MIN, _TILT_MAX))
            edge = tuple(getattr(hook, "affects_edge", ()) or ())
            pairs = []
            if len(edge) >= 2 and edge[0] in idx and edge[1] in idx:
                pairs.append((idx[edge[0]], idx[edge[1]]))      # 정밀: 방이 명시한 edge
            else:                                                # 근사: affects_indicator node 의 전 edge
                ind = self._hyp_indicator.get(hid)
                if ind in idx:
                    i = idx[ind]
                    pairs = [(i, j) for j in range(len(series_ids)) if j != i]
            for (i, j) in pairs:
                P[i, j] *= ratio
                P[j, i] *= ratio
        np.clip(P, -1.0, 1.0, out=P)
        np.fill_diagonal(P, 1.0)
        return P


def _cap_normalize(w: np.ndarray, target_l1: float, cap: float, iters: int = 50) -> np.ndarray:
    """|w_i|≤cap 전부 만족 + Σ|w_i|=target_l1 보존(가능 시). 클립→잔여 비례분배 반복.

    cap clip 후 재정규화하면 다시 cap 초과 → 1회로 불가. capped 원소를 cap 고정하고 잔여 L1 을
    미capped 원소에 비례 분배하는 water-filling. n·cap < target_l1 이면 best-effort(합<target).
    """
    w = np.asarray(w, dtype=float).copy()
    if target_l1 <= 1e-12:
        return w
    cur = float(np.sum(np.abs(w)))
    if cur > 1e-12:
        w *= target_l1 / cur                      # 초기 정규화
    if not (cap and cap > 0):
        return w
    for _ in range(iters):
        over = np.abs(w) > cap + 1e-12
        if not over.any():
            break
        w[over] = np.sign(w[over]) * cap
        free = ~over
        free_l1 = float(np.sum(np.abs(w[free])))
        residual = target_l1 - float(np.sum(np.abs(w[over])))
        if free_l1 < 1e-12 or residual <= 0:
            break
        w[free] *= residual / free_l1             # 잔여를 미capped 에 비례 분배
    return w


# ===========================================================================
# self-test (실동작 — weight_falsification 본체 호출 + 가중치 실제 변화 입증)
# ===========================================================================

if __name__ == "__main__":
    # 1) Beta posterior 누적 — confirm/reject → 신뢰도 방향
    acc = FlagAccumulator()
    assert abs(acc.confidence() - 0.5) < 1e-9       # prior 중립
    for _ in range(8):
        acc.confirm()
    assert acc.confidence() > 0.5
    for _ in range(20):
        acc.reject()
    assert acc.confidence() < 0.5
    print(f"1) Beta posterior 누적 OK: 최종 conf={acc.confidence():.3f} (confirms=8 rejects=20)")

    # 2) 가설↔지표 연결 + on_trade 직접 flag
    hooks = [
        ConfidenceHook(hypothesis_id="h_val", confirm_signal="IC양", reject_signal="붕괴"),
        ConfidenceHook(hypothesis_id="h_mom", confirm_signal="IC양", reject_signal="붕괴"),
    ]
    fr = FlagRouter()
    fr.register(hooks[0], indicator_id="fwd_ep")
    fr.register(hooks[1], indicator_id="mom_12_1")
    for _ in range(10):
        fr.on_trade("h_val", "confirm")     # valuation 확신 누적
    for _ in range(10):
        fr.on_trade("h_mom", "reject")      # momentum 거부 누적
    cbi = fr.confidence_by_indicator()
    assert cbi["fwd_ep"] > 0.5 and cbi["mom_12_1"] < 0.5
    print(f"2) on_trade flag→지표 신뢰도 OK: fwd_ep={cbi['fwd_ep']:.3f} mom_12_1={cbi['mom_12_1']:.3f}")

    # 3) ★동적 가중치 재적합 — 확신 지표 ↑, 거부 지표 ↓ (신규 코드 입증)
    series = ["fwd_ep", "roe", "mom_12_1"]
    base = np.array([0.34, 0.33, 0.33])
    tilted = fr.tilt_weights(base, series, cap=0.40)
    assert tilted[0] > base[0], f"확신 지표 가중 안 올랐음: {tilted[0]} vs {base[0]}"
    assert tilted[2] < base[2], f"거부 지표 가중 안 내렸음: {tilted[2]} vs {base[2]}"
    assert abs(np.sum(np.abs(tilted)) - np.sum(np.abs(base))) < 1e-6, "L1 합 보존 실패"
    assert np.all(tilted <= 0.40 + 1e-9), "cap 위반"
    print(f"3) ★동적 가중치 재적합 OK: base={base.round(3)} → tilted={tilted.round(3)} "
          f"(fwd_ep↑ mom↓, L1합 보존, cap 준수)")

    # 4) flag 없는 지표(roe)는 tilt=1 무변동(상대적으로만 변함) — 미등록 graceful
    fr2 = FlagRouter()
    fr2.register(hooks[0], indicator_id="fwd_ep")
    only_one = fr2.tilt_weights(base, series, cap=0.40)
    # roe/mom 은 미등록 → tilt 1.0, fwd_ep 만 prior(0.5)→tilt 1.0 → 전부 무변동
    assert np.allclose(only_one, base, atol=1e-9), only_one
    print(f"4) 미등록/prior 지표 무변동(무회귀) OK")

    # 5) emit_from_ic — weight_falsification 본체로 confirm/reject 자동 판정
    fr3 = FlagRouter()
    fr3.register(ConfidenceHook(hypothesis_id="h_ic"), indicator_id="x")
    rng = np.random.default_rng(0)
    # 예측력 있는 배치: score 와 return 상관 양수 → confirm
    sc = rng.normal(size=30)
    rr = sc * 0.6 + rng.normal(size=30) * 0.5
    flag = fr3.emit_from_ic("h_ic", sc, rr, baseline_ic=0.0, sd=0.1)
    assert flag == "confirm", flag
    print(f"5) emit_from_ic 예측력 양 → '{flag}' OK (Rank-IC 본체 사용)")

    # 6) emit_from_ic 붕괴 시퀀스 → reject (e-CUSUM 본체)
    fr4 = FlagRouter()
    fr4.register(ConfidenceHook(hypothesis_id="h_bd"), indicator_id="y")
    flags = []
    for _ in range(12):
        s_neg = rng.normal(size=30)
        r_neg = -s_neg * 0.7 + rng.normal(size=30) * 0.3   # 음의 IC 지속 → 붕괴
        flags.append(fr4.emit_from_ic("h_bd", s_neg, r_neg, baseline_ic=0.0, sd=0.1))
    assert "reject" in flags, flags
    assert fr4.confidence("h_bd") < 0.5
    print(f"6) emit_from_ic 음 IC 지속 → reject 발생 OK (붕괴 conf={fr4.confidence('h_bd'):.3f})")

    print("\nflag_router self-test PASS "
          "(Beta 누적 + 지표 신뢰도 + ★동적 가중치 tilt(신규) + 무변동 무회귀 + IC/e-CUSUM 본체 연동)")
