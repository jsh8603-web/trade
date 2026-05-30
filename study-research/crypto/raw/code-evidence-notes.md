---
tags: [type/notes, domain/inv, phase/study-system, topic/crypto-evidence]
date: 2026-05-30
---

# crypto 스터디 — 코드 사실 출처 노트

> study_session.yaml 의 각 블록 작성에 사용한 Read-한 파일과 핵심 발견. 외부 자문 미수행
> (main 지시: "무거운 분석 말고 가볍게", 9세션 자문 채널 경합 우려) — 본 노트가 자문 raw
> 대체. 직접 코드 fact 기반.

## 1. coin 예외 근거 (STUDY-KIT §4 ③)

> "coin 은 예외: 지표가중 부적합 → core/coin_track.py 에서 belief→사이징 조절만. ①②③ 미적용."

→ 블록7 의 stage=learn / weight_panel·conditional_correlation·train_weights 전부 미적용.
   stage=inject / coin_track·coin_consensus_lens·coin_sizing 만 본체 변경.

## 2. 코인 SACRED 본체 (재작성 금지 모듈)

| 파일 | 핵심 SACRED | 출처 |
|------|------------|------|
| core/coin_track.py | Orchestrator.run() / BaseStrategyAgent.decide() / _evaluate_market_state() 본체 위임만 | L36~50 docstring |
| core/coin_sizing.py | execute_trade.py 실주문·run_cycle 미변경 + risk_sizing.py 본체 미변경 + risk_gate.check() 우회금지 | L11~17 docstring |
| core/coin_consensus_lens.py | consensus.py 본체 미변경 (subclass만) + risk_gate 항상-on + execute_trade 미변경 | L18~22 docstring |
| core/coin_shadow.py | execute_trade.py 실주문(:457)·nonce uuid(:153)·live_trader.run_cycle 절대 미변경 | L8~12 docstring |
| core/coin_memory.py | memory_layer.py 본체 미변경 (subclass로 변형만) | L15~18 docstring |

## 3. 기존 crypto 가정카드 (이미 lifecycle 운영)

- `crypto.mvrv_mean_reverts` (parametric, scope=asset, domain=crypto) — commodity_assumptions.py L327
- `crypto.speculative_flow_overheat` — commodity_assumptions.py L331
- MVRV closed-loop: `core/data/instrument_source.run_mvrv_closed_loop` — mvrv_hi=2.4, horizon=7d, FDR_DECISION binomial p<0.05 → reject. fixture 검증 OK.

## 4. coin 전용 데이터 인터페이스 (블록2 indicators 출처)

| Indicator | 출처 | 비고 |
|-----------|------|------|
| MVRV | instrument_source.CoinMetricsMvrvProvider (CapMVRVCur) | PIT vintage·knowable_from 지원 |
| FGI | agents/external_data.ExternalDataAgent.collect_all() → raw_external_data.sources.fear_greed.current.value | coin_track._extract_fgi 추출 |
| funding_rate | coin_consensus_lens.CoinLensData.funding_rate | perpetual swap 8h |
| OI change | coin_consensus_lens.CoinLensData.open_interest_change_pct | — |
| whale_inflow_usd | coin_consensus_lens.CoinLensData.whale_inflow_usd | 음수=유출 |
| exchange_reserve | coin_consensus_lens.CoinLensData.exchange_reserve_change_pct | — |
| RSI(14) | scripts/collect_market_data.py | Upbit 캔들 30일 입력 |
| 24h 가격 변화 | scripts/collect_market_data.py | Upbit ticker |
| SMA deviation | BaseStrategyAgent.detect_regime 입력 | orchestrator drop_context |

## 5. FGI 5단계 regime 매핑 (블록1 regime_reading 근거)

`core/coin_track.py` L217~226 `_fgi_to_regime`:
- <=20 → extreme_fear (next-check 120m)
- <=35 → fear (240m)
- <=60 → neutral (480m)
- <=80 → greed (480m)
- 그 외 → extreme_greed (240m)

`_REGIME_INTERVALS` L27~33 의 next-check 분 단위.

## 6. coin_sizing 정량 상수 (블록4 weight_rules · 블록7 inject 근거)

`core/coin_sizing.py` L29~33:
- COIN_COND_THRESHOLD = 1e6 (cov condition number 임계 → HRP)
- COIN_CORR_THRESHOLD = 0.75 (코인 crisis 상관 임계)
- COIN_HRP_W_MAX = 0.10 (HRP 단일 비중 상한)
- BTC_CRISIS_CAP = 0.40 (H25: crisis 상관 과열 시 BTC 비중 상한)

→ 블록7 inject 의 belief modulator 가 이 상수들을 regime-conditional 로 0.65 / 0.30 으로
   tighten 하는 경로 제안.

## 7. coin_memory 변동성 정합 (블록5 dwell 단축 근거)

`core/coin_memory.py` L27~29:
- COIN_HALF_LIFE_HOURS = 4.0 (vs 주식 24h, 거시 168h)
- 코인 이벤트 태그 7종: halving / exchange_hack / delisting / depegging / regulatory /
  whale_move / listing

→ 블록7 falsify 의 update_controller dwell 단축(주식 대비 50%)·K-window 1주 근거.

## 8. CoinConsensusLens 의 DCF 미사용 명시

`core/coin_consensus_lens.py` L164~166:
```python
@staticmethod
def dcf_not_used() -> bool:
    """DCF 미사용 확인 — 코인 특성 명시."""
    return True
```

→ STUDY-KIT §4 ③ coin 예외의 코드 레벨 근거. 펀더멘털 cash flow 없음.

## 9. belief 경로 (블록7 inject 의 coin belief wire)

`core/brain/regime_to_weights.py`:
- L112: belief 인자 (opt-in)
- L167: `_belief_conditional_cov(returns_history, sleeve_regime_ids, belief, labels)` — RegimeGlasso Σ_eff
- coin 적용: coin_track 의 `_fgi_to_belief(fgi)` 신규 추가 → MarketState.raw_external_data['coin_belief'] → coin_track_macro → macro_orchestrator.allocate(coin_belief=...) forwarding

## 10. macro 방 yaml 참조 (포맷·깊이 정합)

`study-research/macro/study_session.yaml` 의 6 블록 구조·lens 정성필드·confidence_hooks
포맷을 참조해 crypto 도 동일 schema 로 작성. 단 블록7 의 "지표가중 적용" 부분은 coin
예외로 학습/카드 단계가 "미적용 사유 명시" 로 대체됨.

## 외부 자문 미수행 사유

- main 지시 "무거운 분석 말고 가볍게 진행"
- 9세션 동시 자문 채널 경합 가능성 (STUDY-KIT §2 ⚠ 명시)
- 코드 사실 기반으로 block 작성에 충분한 정보 확보
- 추후 main 통합 시점에서 partial-corr 검증 / N=4 사이클 검정력 등 자문 필요

→ 자문 raw 확보 시 본 raw/ 디렉토리에 archive 누적 예정.
