---
name: handoff-coin-indicator-review
description: 코인 지표 5단계 검토 세션 인계 — 거시유동성/funding 종결, 측정 방법론 정립
date: 2026-06-02
tags: [handoff, crypto, indicator-review, regime-conditional]
---

# 핸드오프 — 코인 지표 5단계 검토 (2026-06-02)

> 진입: [plan-coin-indicator-review.md](./plan-coin-indicator-review.md) → [progress-coin-indicator-review.md](./progress-coin-indicator-review.md)
> 측정 SSOT: [study-research/_wire/regime-conditional-measurement-framework.md](./study-research/_wire/regime-conditional-measurement-framework.md) (4게이트)
> ⛔ go-live=사람 게이트. push 금지. 자율주행 flag ON(agent/.secretary/.autopilot-btn-Inv.flag). Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`.

## 1. 세션 핵심 — 측정 방법론 정립 + 거시/funding 종결

사용자가 정의한 **5단계 검토 흐름** 박제: S1 논문 ground → S2 실측 가설(4게이트) → S3 외부검토(gemini+claude) → S4 외부검토를 다른 데이터로 재검증 → S5 역공격 수렴. 측정 함정 2종(full-sample 상쇄 기각 / single-episode 즉시 채택) 교정.

## 2. 검토 완결 지표 (5단계 1회전씩)

- **M2 거시유동성**: 긴축국면 −0.54 4게이트 표면 통과 BUT gemini+claude+15축 audit+cross-asset **3중 수렴 = 2020-22 COVID supercycle single-episode artifact**(연도내 IC 2022 1개뿐·CI[−0.91,−0.001]·2021-23 제외 −0.16 무·ETH −0.13). → candidate(throttle only, sizing 금지). audit 정정 2건(E over-claim·K Bonferroni denominator) 반영.
- **net_liquidity(BS−TGA−RRP)**: claude 제안 검증. nl_yoy 무·nl_3m 긴축 −0.38·2021-23 제외 +0.37/ETH +0.70 BUT **within-period 전부 무(2018-19 −0.21/2020 −0.20)=between-episode level shift 1회·구간부호반전(2018-20 +0.59/2021-23 −0.83)**. claude "제외=cherry-pick, M2와 collinear 0.74, partial +0.11 incremental 없음, M2보다 falsification 더 실패" → **rejected_provisional**(M2와 동일 artifact). gemini 낙관은 within/contemp-forward/partial 누락(역공격 반박).
- **funding**: directional 무 + 역추세 게이트 무 + **crowding risk-gate 무**(극단 |z|>2 forward drawdown 오히려 작음 −6.5% vs −7.7%). 전 각도 무알파 확정. 부활=intraday/청산 event-study.
- (직전) breadth alt-BTC MR −0.13(net-cost 탈락), active_addr(무신호), realized_vol(vol-sizing 차원), basis(약장 약힌트 Bonferroni 탈락) 전부 rejected_provisional.

## 3. 누적 결론
- **거시 유동성(M2·net liq·real) 트랙 = 전부 single-episode artifact, 안정 forward alpha 없음**. 거시는 contemporaneous comovement는 실재하나(claude reframe) forward 예측은 에피소드 swing 의존.
- **단기 트랙 = BTC momentum 단일 carrier + kimchi throttle**(직전 R 확정, net Sharpe 1.42).
- 거시/미시구조 비대칭(거시 생존처럼 보임 / 미시구조 죽음)은 검정력 인공물과 축퇴(claude Q4) — cross-asset으로만 판별.

## 4. 다음 자율 큐
1. **real_rate walk-forward** (M2와 동일 single-episode 예상, 빠른 확인 후 종결).
2. **온체인 유료 데이터**(SOPR/exchange netflow/청산) = 데이터 게이트, 자율 불가(collector_plan).
3. 자율 측정 가능 후보 거의 소진 — 남은 건 단기 트랙 코드 배선(go-live 게이트) + 유료 온체인.

## 5. 산출물
- harness: .p2-macroliq*.py, .p2-walkforward-regime.py, .p2-regime-recheck.py, .p2-netliq.py, .p2-funding-crowding.py, .p2-funding-gate.py, .p2-breadth.py, .p2-onchain-addr.py, .p2-overheat-indep.py
- 결과: .p2-*-result.json (각 지표)
- 자문 raw: .consult-regime-validity-{gemini,claude}.txt, .consult-netliq-{gemini,claude}.txt, .consult-cointrack-R1-*.txt
- 논문: study-research/crypto/raw/crypto-regime-dependence-papers.md, crypto-factor-papers.md, audit-regime-conditional-20260602.md
- ledger: study-research/_wire/indicator-ledger.md (crypto: adopted 6/candidate 17/rejected_provisional 6)
