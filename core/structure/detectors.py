"""core/structure/detectors.py — 공유 change/sequential detector 모듈 (가정 검증통계).

자문 수렴 (claude A-1 / gemini A-1): 가정 "맞다/틀리다" 판정 = 단일 기법 X, 다층.
rule_observer 의 PSI/near_zero_mass/PageHinkley 를 **공유 모듈로 추출**하고(중복 제거,
claude D-6), 가정 라이프사이클에 필요한 detector 를 더한다. 대상만 다르고(가정 예측량 잔차
vs rule 출력 divergence) 수학은 동일 → 양쪽(rule_observer · assumption_stats) import.

포함:
- PSI / near_zero_mass / PageHinkley : rule_observer 에서 re-export (SSOT 1곳).
- CUSUM (Page)       : 모수가정, 방향·크기 알 때 평균이동 누적합.
- SPRT (Wald)        : 가정 H0(성립) vs H1(깨짐) 로그우도비 순차검정 (gemini A-1).
- BOCPD (Adams&MacKay 2007): run-length posterior, 변화점 크기 사전지정 불필요 (claude A-1).
- prequential loss (Dawid): 가정=forecaster, 예측 시간순 채점 → 누적손실곡선 꺾임=증거.

numpy 만 사용 (ruptures/pymc 부재). 결정론(seed 무관, 스트리밍).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# rule_observer 의 detector primitive 를 SSOT 로 재노출 (중복 구현 금지, claude D-6).
from core.observability.rule_observer import psi, near_zero_mass, PageHinkley  # noqa: F401


# ---------------------------------------------------------------------------
# CUSUM (Page) — 모수가정 평균이동, 방향·크기 알 때
# ---------------------------------------------------------------------------

@dataclass
class CusumState:
    pos: float = 0.0
    neg: float = 0.0
    fired: bool = False
    fired_at: int = -1


class Cusum:
    """양측 CUSUM. target=H0 평균, k=허용 slack(보통 0.5σ), h=경보 임계(보통 4~5σ)."""
    def __init__(self, target: float, sd: float, k_sigma: float = 0.5, h_sigma: float = 5.0):
        self.target = target
        self.sd = sd if sd > 1e-9 else 1.0
        self.k = k_sigma * self.sd
        self.h = h_sigma * self.sd
        self.s = CusumState()
        self._n = 0

    def update(self, x: float) -> bool:
        self._n += 1
        d = x - self.target
        self.s.pos = max(0.0, self.s.pos + d - self.k)
        self.s.neg = min(0.0, self.s.neg + d + self.k)
        if (self.s.pos > self.h or self.s.neg < -self.h) and not self.s.fired:
            self.s.fired = True
            self.s.fired_at = self._n
        return self.s.fired


# ---------------------------------------------------------------------------
# SPRT (Wald) — 가정 H0(성립) vs H1(깨짐) 순차 로그우도비
# ---------------------------------------------------------------------------

@dataclass
class SprtResult:
    decision: str            # "accept_H0" | "accept_H1" | "continue"
    llr: float               # 누적 로그우도비
    n: int


class Sprt:
    """가우시안 SPRT. H0~N(mu0,σ), H1~N(mu1,σ). alpha=거짓기각, beta=거짓수용.

    가정 검증: H0 = 가정 성립 시 잔차/지표 평균(mu0), H1 = 깨졌을 때(mu1).
    LLR 가 상계 B 돌파 → reject H0(가정 깸), 하계 A 미만 → accept H0(가정 성립).
    """
    def __init__(self, mu0: float, mu1: float, sd: float, alpha: float = 0.05, beta: float = 0.20):
        self.mu0, self.mu1 = mu0, mu1
        self.sd = sd if sd > 1e-9 else 1.0
        self.A = np.log(beta / (1 - alpha))          # 하계 (accept H0)
        self.B = np.log((1 - beta) / alpha)          # 상계 (accept H1)
        self.llr = 0.0
        self.n = 0

    def update(self, x: float) -> SprtResult:
        self.n += 1
        # 가우시안 단일관측 로그우도비
        ll = (((x - self.mu0) ** 2) - ((x - self.mu1) ** 2)) / (2 * self.sd ** 2)
        self.llr += ll
        if self.llr >= self.B:
            return SprtResult("accept_H1", self.llr, self.n)
        if self.llr <= self.A:
            return SprtResult("accept_H0", self.llr, self.n)
        return SprtResult("continue", self.llr, self.n)


# ---------------------------------------------------------------------------
# BOCPD (Adams & MacKay 2007) — run-length posterior, 변화점 크기 사전지정 불필요
# ---------------------------------------------------------------------------

class Bocpd:
    """Bayesian Online Change-Point Detection. 가우시안 관측 + Normal-inverse-gamma 켤레.

    상수 hazard 1/lambda. 매 관측 후 run-length=0 사후확률 = 변화점 확률.
    크기/개수 사전지정 불필요 (claude A-1: BOCPD 장점). p(changepoint) 가 임계 초과 시 경보.
    """
    def __init__(self, hazard_lambda: float = 100.0,
                 mu0: float = 0.0, kappa0: float = 1.0, alpha0: float = 1.0, beta0: float = 1.0):
        self.h = 1.0 / hazard_lambda
        self.mu0, self.kappa0, self.alpha0, self.beta0 = mu0, kappa0, alpha0, beta0
        # run-length=0 초기 사후
        self.mu = np.array([mu0]); self.kappa = np.array([kappa0])
        self.alpha = np.array([alpha0]); self.beta = np.array([beta0])
        self.R = np.array([1.0])     # run-length 분포
        self.t = 0
        self.map_run_length = 0      # MAP run-length (★ 변화점 = 이 값의 급락)

    def _student_t_pdf(self, x):
        # 사후예측 = Student-t (NIG 켤레)
        df = 2 * self.alpha
        scale = np.sqrt(self.beta * (self.kappa + 1) / (self.alpha * self.kappa))
        z = (x - self.mu) / scale
        from math import lgamma
        coef = np.exp(np.array([lgamma(d/2 + 0.5) - lgamma(d/2) for d in df]))
        return coef / (np.sqrt(df * np.pi) * scale) * (1 + z**2 / df) ** (-(df + 1) / 2)

    def update(self, x: float) -> float:
        """관측 x 처리 → P(changepoint now) = R[0] (run-length 0 사후) 반환.

        ⚠️ 단일 step P(cp) 는 변화점에서도 ≈hazard prior 에 머문다(우도가 growth·cp 양쪽을
        동일 배율로 줄임). **실사용 변화점 신호 = self.map_run_length 의 급락** (run 이 reset →
        MAP run-length 가 0 근방으로 떨어짐). assumption_stats 는 map_run_length drop 을 본다.
        """
        self.t += 1
        pred = self._student_t_pdf(x)
        growth = self.R * pred * (1 - self.h)
        cp = float(np.sum(self.R * pred * self.h))
        new_R = np.concatenate([[cp], growth])
        s = new_R.sum()
        new_R = new_R / s if s > 0 else new_R
        # NIG 파라미터 업데이트 (run 확장) + run-length=0 reset prior 추가
        new_mu = np.concatenate([[self.mu0], (self.kappa * self.mu + x) / (self.kappa + 1)])
        new_kappa = np.concatenate([[self.kappa0], self.kappa + 1])
        new_alpha = np.concatenate([[self.alpha0], self.alpha + 0.5])
        new_beta = np.concatenate([[self.beta0],
                                   self.beta + (self.kappa * (x - self.mu) ** 2) / (2 * (self.kappa + 1))])
        self.mu, self.kappa, self.alpha, self.beta, self.R = new_mu, new_kappa, new_alpha, new_beta, new_R
        # 메모리 cap (run-length truncation)
        if len(self.R) > 500:
            self.R = self.R[:500]; self.R /= self.R.sum()
            self.mu, self.kappa = self.mu[:500], self.kappa[:500]
            self.alpha, self.beta = self.alpha[:500], self.beta[:500]
        self.map_run_length = int(np.argmax(self.R))
        return float(new_R[0])


# ---------------------------------------------------------------------------
# Prequential loss (Dawid) — 가정=forecaster, 누적 1-step 손실곡선 꺾임 = 증거
# ---------------------------------------------------------------------------

@dataclass
class PrequentialResult:
    cum_loss: float
    mean_loss: float
    n: int
    recent_slope: float          # 최근 윈도우 손실 기울기 (↑ = 가정 악화)
    kink_alert: bool             # 누적손실곡선 꺾임 감지


def prequential_loss(
    predictions: np.ndarray,
    outcomes: np.ndarray,
    recent_window: int = 12,
    slope_alert: float = 0.0,
) -> PrequentialResult:
    """가정의 시간순 1-step 예측 손실 (squared). purged WF 와 철학 동일(claude A-1).

    누적 손실 곡선의 기울기가 최근 윈도우에서 급증하면 가정 악화 = kink.
    """
    pred = np.asarray(predictions, float); out = np.asarray(outcomes, float)
    m = np.isfinite(pred) & np.isfinite(out)
    pred, out = pred[m], out[m]
    if len(pred) == 0:
        return PrequentialResult(0.0, float("nan"), 0, float("nan"), False)
    loss = (pred - out) ** 2
    cum = float(np.sum(loss))
    mean = float(np.mean(loss))
    # 최근 윈도우 vs 이전 평균 손실: 기울기(보고용) + 견고한 kink 판정.
    # kink = recent 가 prior 의 kink_ratio 배 초과 AND outcome 분산 대비 material(절대 floor).
    #   ★ 정상 메커니즘(loss≈0)에서 노이즈 slope 만으로 발화하지 않도록 floor 필수.
    kink_ratio = 2.0
    out_var = float(np.var(out)) if len(out) > 1 else 1.0
    floor = 0.05 * out_var                       # outcome 스케일 대비 material 손실 하한
    if len(loss) >= 2 * recent_window:
        recent = float(np.mean(loss[-recent_window:]))
        prior = float(np.mean(loss[:-recent_window]))
        slope = recent - prior
        kink = bool(recent > kink_ratio * max(prior, 1e-12) and recent > floor)
    else:
        slope = float("nan")
        kink = False
    return PrequentialResult(cum, mean, len(loss), slope, kink)


if __name__ == "__main__":
    rng = np.random.default_rng(7)

    # CUSUM: 60개 N(0,1) 후 40개 N(3,1) → 평균이동 감지.
    # k=1σ (≥1σ shift 만 추적 → 노이즈 누적 차단), h=5σ. ★ k=0.5σ 면 노이즈 excursion 도 발화
    #   = CUSUM 단독 false alarm → AND-gate(K-윈도우·online-FDR) 필요성의 근거(claude A-2).
    c = Cusum(target=0.0, sd=1.0, k_sigma=1.0, h_sigma=5.0)
    fired_at = None
    for i, x in enumerate(np.concatenate([rng.normal(0, 1, 60), rng.normal(3, 1, 40)])):
        if c.update(x) and fired_at is None:
            fired_at = i
    print(f"CUSUM 감지 @{fired_at} (변화점 60 이후여야)"); assert fired_at and fired_at >= 60

    # SPRT: H0=0 H1=2, 데이터가 H1 → accept_H1
    s = Sprt(mu0=0.0, mu1=2.0, sd=1.0)
    dec = None
    for x in rng.normal(2, 1, 100):
        r = s.update(x)
        if r.decision != "continue":
            dec = r.decision; break
    print(f"SPRT 판정={dec} (n={s.n})"); assert dec == "accept_H1"

    # BOCPD: 변화점에서 MAP run-length 급락 (run reset). P(cp) 단일값보다 신뢰.
    b = Bocpd(hazard_lambda=50.0)
    rls = []
    for x in np.concatenate([rng.normal(0, 1, 60), rng.normal(4, 1, 60)]):
        b.update(x); rls.append(b.map_run_length)
    rl_before = max(rls[55:60])          # 변화점 직전 run-length 누적 (큼)
    rl_after = min(rls[60:70])           # 변화점 직후 run-length (reset → 작음)
    print(f"BOCPD run-length 직전 max={rl_before} 직후 min={rl_after} (붕괴 = 변화점)")
    assert rl_before >= 40 and rl_after <= 5, (rl_before, rl_after)

    # Prequential: 후반 예측 악화 → kink
    pred = np.zeros(60); out = np.concatenate([rng.normal(0, 0.3, 30), rng.normal(3, 0.3, 30)])
    pr = prequential_loss(pred, out, recent_window=10)
    print(f"Prequential mean_loss={pr.mean_loss:.2f} slope={pr.recent_slope:.2f} kink={pr.kink_alert}")
    assert pr.kink_alert

    print("detectors self-test PASS (CUSUM/SPRT/BOCPD/prequential + PSI/PH re-export)")
