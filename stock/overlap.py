# -*- coding: utf-8 -*-
"""WIRE3.5-Gf-C: N-vintage overlapping portfolio (horizon mismatch 해소).

자문 R1 만장일치(2026-06-05, Claude+Gemini) + 본인 재검증(_wire35_gfc_overlap_results.txt):
  신호 horizon=12M 인데 월간 full-rebal+band 정책은 +4.38%/yr CI[-0.001,+0.757]=0포함 비유의.
  12-vintage overlap = 매월 1/12 트랜치 12M 보유 → 실현 +6.20%/yr CI[+0.067,+0.977]=0불포함 유의,
  12M signal(+6.687%)과 괴리 0.49pp 수렴, turnover 3.8%/월. = horizon mismatch 해소.
  점추정 파라미터(MA window·turnover 목적함수) 불필요 = small-n OOS robust (자문 핵심 근거).
  ★small-n hedge: CI 하한 +0.067 = 0 근처, overlapping 12M = effective n 작음 → "유의하나 marginal".

설계 (go-live 무접촉):
  빈티지 큐 관리(매월 신규 진입·12M 만기 청산)는 호출자(백테스트/거래 루프) 책임.
  본 모듈 = 순수 합성 함수 — 활성 빈티지 weight map 들 → overlap weight. default 미사용=byte-identical.
  각 빈티지가 이미 capped-EW(종목 cap c)면 동일비중 합성은 볼록결합 → 종목 weight ≤ c 유지
  (cap 초과 불가, risk_gate 안쪽 보존). 호출자가 추가 cap 재적용 불필요하나 안전상 권장.
"""
from __future__ import annotations

from typing import Mapping, Sequence


def overlap_portfolio_weights(
    vintage_weight_maps: Sequence[Mapping[str, float]],
    n_vintages: int = 12,
) -> dict[str, float]:
    """활성 빈티지 weight map 들을 동일비중(1/N) 합성. 각 빈티지 Σw=1 → 합성도 Σw=1.

    vintage_weight_maps: 오래된→최신 순 빈티지별 {ticker: target_weight}. 최근 n_vintages 만 활성.
      각 빈티지 = 그 달 build_sleeve_decisions / selection_pipeline 의 종목별 target_weight.
    n_vintages: 활성 트랜치 수 = 신호 horizon(월). 12M 신호 → 12. <=0 이면 전체 사용.
    종목이 여러 빈티지에 중복되면 weight 가산(신호 지속 종목 비중 자연 누적).
    빈 입력 / 전부 빈 map → {}.

    반환 {ticker: overlap_weight}. 각 빈티지 capped-EW 이면 볼록결합 → 종목 cap 유지.
    """
    active = list(vintage_weight_maps)
    if n_vintages > 0:
        active = active[-n_vintages:]
    active = [vm for vm in active if vm]
    if not active:
        return {}
    frac = 1.0 / len(active)
    out: dict[str, float] = {}
    for vm in active:
        for t, w in vm.items():
            out[t] = out.get(t, 0.0) + frac * float(w)
    return out


def overlap_turnover(
    prev_weights: Mapping[str, float],
    curr_weights: Mapping[str, float],
) -> float:
    """두 시점 overlap weight 간 단방향 turnover = Σ max(0, curr−prev) (매수측 합).

    overlap 의 핵심 이점(매월 1/N 만 교체 → 저 turnover) 모니터·검증용. 0~1.
    """
    tickers = set(prev_weights) | set(curr_weights)
    buys = sum(max(0.0, float(curr_weights.get(t, 0.0)) - float(prev_weights.get(t, 0.0)))
               for t in tickers)
    return buys
