# Round 3 — claude-web (claude.ai basic)

as_of: 2026-05-30
model: Opus 4.8 High
response_len: 4858

---

남은 3개 + 부수 2개, 요청 형식대로.

결정 1 — partial-corr 학습 위치

(1) (다) hybrid 채택, 단 충돌 규칙 수정. "prefix 무조건 우선"이 아니라 prefix를 shrinkage target으로, glasso는 stability-gate 통과 + bounded envelope 내에서만 admit. "prefix 우선"은 불일치(=glasso가 정보를 더하는 바로 그 순간)에 glasso를 무력화하므로. 추가로 fwd_ret 노드 취급을 분리: 내부 glasso의 1차 가치는 indicator-indicator de-confounding이지 fwd_ret 예측이 아님 → indicator↔fwd_ret edge는 별도 heavier prior + wider gate, 예측 자체는 기존 IC machinery에 잔류 (A의 1D vs ND overfitting 우려를 구조적으로 해소).

(2) 신설 coin_track/internal_corr.py → conditional_correlation.RegimeGlasso(corr_prior=offline_partialcorr_table, regime_ids=vol⊗macro, npn=True). cross-asset 인스턴스와 물리 분리, coin_consensus_lens(§4③ sacred, weight_panel 진입 X) 불침범. offline 표 = warm-start prior 겸 shrinkage target (force-include 0.3 적용). modulator 출력 → _belief_conditional_cov 의 conditional-cov off-diagonal sink. admit 직전 stability gate: per-regime effective-N threshold + bootstrap edge stability.

(3) funding-limited(2020-9 start) + 일봉 autocorr로 per-regime effective N이 gate를 상시 못 넘으면 glasso는 "거의 안 터지는 비싼 보험". gate가 영구 폐쇄 아닌지 사전 검증 필요. envelope 폭 자체가 overfit 가능한 free param — 이건 다음 단계에서 sensitivity로 봐야 함.

결정 2 — macro break 처리

(1) (나) 채택 + 채널별 명시. macro 채널만 2020-03 one-sided fit start, on-chain 채널은 full history, 2024 ETF는 watch flag(fit split 아님). 근거 = 좁히는 기준의 핵심 질문에 대한 답: break 위치가 채널별로 다름. macro→crypto 구조 break는 2020-03에 실재(COVID 유동성·기관화)하나 on-chain(MVRV/SOPR/dominance)은 해당 break 없음 → 전역 2-split(다)은 오답. post-2024 1.5yr(~50-150 effective)는 fittable regime이 아니라 monitor 대상이고, 짧은 표본에 prior_strength를 상향(A)하는 건 shrinkage 방향과 무관히 위험.

(2) macro_orchestrator: macro 채널 rolling fit start_date=2020-03 (one-sided), on-chain 채널 lookback 무제한. 2024 ETF → confidence_hooks 에 regime label "post-ETF" baseline_ic 사전등록 + macro_orchestrator H29 abstain 게이트 연결(괴리 시 mis-weight 대신 abstain).

(3) 2020-03 cut은 judgment(점진 transition 가능). pre-2020 macro 완전 폐기는 미래 risk-off 국면이 pre-2020을 닮을 때 유일 표본 상실 → hard exclude 대신 low-weight prior 권고. 또 D1 내부 glasso가 macro 노드를 포함하면 joint window가 동일하게 post-2020로 수축 → effective-N 문제 D1과 compounding.

결정 3 — ETF net flow 신규 지표

(1) (가) ADD하되 prior는 B의 0.3-0.4가 아닌 observe-only(~0.05). collector는 지금 깔고 weight는 confidence_hooks가 벌게 함. 이미 auto prior_strength + rolling reject_signal이 존재하므로 calendar-gating(다, 2027)은 gating machinery 낭비 + 1.5yr live data 손실. A의 "추가 X"는 깨끗한 institutional-demand 신호를 버리는 것.

(2) 신설 coin_track/collectors/etf_flow.py(Farside daily net flow, post-2024). indicator panel 등록 prior_strength≈0.05(probation), consensus_lens 비침범. confidence_hooks probationary hypothesis + rolling IC monitor; reject_signal→auto down-weight, OOS IC 누적 시에만 prior ramp. exchange_reserve/whale 와 collinear → D1 internal glasso로 de-confound. 단 ETF_flow를 아직 glasso 노드로 넣지 말 것 — post-2024-only라 complete-case window를 post-2024로 수축시킴 → standalone gated indicator로만.

(3) Farside 단일 free source 취약성(스키마/티어 변동, 리던던시 없음). ETF flow ≠ total institutional demand (OTC·futures basis·non-US ETF 누락) → "깨끗한 대체"는 과대평가일 수 있음.

부수 1 — belief b(t) primary 축

(1) (가) FGI primary, macro·halving = low-dim parametric conditioning (tensor product 아님). (다) nested dict는 5×4×3=60-cell 폭발 = 차이5 instability 재현 → 기각. belief는 _fgi_to_belief soft-membership manifold(5-state)에 거주하고, macro·halving은 소수 shared param으로 cov를 modulate(macro=threshold shift, halving=magnitude scale).

(2) coin_track._fgi_to_belief → 5-state soft membership = primary. _belief_conditional_cov belief 인자는 FGI-state-keyed flat dict 유지(nested dict 확장 금지). macro/halving은 conditioning multiplier로 cov에 곱, dict 키 추가 아님. macro→macro_orchestrator regime, halving→합의된 N=4 label.

(3) FGI-primary는 sentiment 주도 가정 — macro-shock 국면(예 2022 rate shock)에선 macro가 주도하고 FGI는 lag. parametric conditioning이 shock 시 macro override 가능할 만큼 expressive해야 함(효과가 non-additive면 mis-spec). FGI 2018-2 start라 2013-2017 cycle belief 부재 → halving coverage가 ~2 FGI cycle로 제한.

부수 2 — confidence_hooks 첫 활성

(1) macro_abstain (H29) first. 신뢰도 데이터 부족 = 최대 risk가 "안 믿을 신호에 confident하게 act". abstain gate는 순수 downside protection(weight overfit 위험 0, coarse action)이라 데이터가 가장 없을 때 가장 가치 — circuit breaker를 먼저 켜야 나머지 hook의 phased rollout이 안전. Fork 명시: machinery 검증을 우선한다면 mvrv-first(최장·최청정 14yr 데이터)가 prior_strength path 검증엔 우월 → 그래서 즉시 second로 배치. 즉 "자본 손실 회피 > 기회 손실 회피"를 택한 결정.

(2) confidence_hooks: macro_abstain 활성 + macro_orchestrator H29 연결 + regime-conditional baseline_ic 사전등록. 나머지 4 hook은 등록만 dormant. phased: macro_abstain→(OOS)→mvrv→fgi→funding→halving.

(3) 신뢰도 데이터 없는 abstain은 과다/오발 abstain 가능하고 baseline_ic 사전등록 자체가 추정. "correct abstention"은 counterfactual이라 OOS 측정이 어려움 → abstained 구간 shadow-mode log로 calibrate 필요. 게다가 abstain은 macro 채널 의존이라 D2에 따라 2020-03~ 단기 history 위에 서 있음.

수렴. 추가 질문 없음. 단 두 곳만 menu를 넘은 refinement이므로 재논쟁 아닌 확인만 요함 — D1 충돌규칙(prefix-우선 → stability-gated bounded modulation), D3 prior(0.3-0.4 → observe-only 0.05). 이 둘 수용되면 수렴, 추가 round 불필요.