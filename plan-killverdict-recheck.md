# plan-killverdict-recheck — 자문 부당판정 재측정 + Q4 신규지표 발굴

> 2026-06-03 btn-Inv. 외부 자문(claude-web Opus + gemini-web Pro) 1R 수렴 결과를 실측으로 확정.
> 자문이 "기각 부당(false-kill)"이라 한 3건을 재측정해 생/사 판정 변동 확인 + Q4 신규지표 candidate 박제.

## 목표
1. 자문 수렴 = Bonferroni→FDR 전환, netflow/breadth 기각 철회 후보, 활성주소/글로벌momentum 死 유지.
2. 자문이 "부당"이라 한 3건을 **내가 직접 재측정**해 판정 확정(자문≠정답, 실측 게이트).
3. Q4 신규지표 6개 candidate ledger 박제 + 가용성 확인된 것 실데이터 1차 IC.

## SACRED (불가침)
- go-live 미접촉·push 금지·risk_gate 상수 무수정·calculate_buy_score SACRED.
- 측정 표준: rank-IC(Spearman) + NW-HAC(maxlags=45=1.5×30) + epoch 3분할.
- ★small-n rigor: 모든 정량 claim에 n·p·CI·hedge 어휘 + 다중비교 보정 명기.
- ★empirical-claim 5의무: data coverage 일자·spec↔code match·autocorr 보정·multiple comparison·verdict 라벨.
- 자문 prior 인용 시 우리 표본 재현 검증 후 박제(재현 실패=falsifier 명시).

## Steps (각 step = 측정 → 검증 subagent 독립 재현 → ledger 박제)
- [ ] **M1 netflow 극단치 threshold 재측정** · model: opus
  - 상위/하위 decile 조건부(극단 flow만) + 거래소별 FlowIn/FlowOut 분리 + 교호항 조건부 slope **직접검정**(평균 아닌 regime별 slope)
  - 판정변동: 약세=음(매도압)·강세=양(증거금) 조건부 유의 OR 극단치 decile 유의 → regime-conditional 生 / 무 → 死 확정
- [ ] **M2 breadth overlay marginal 재판정** · model: opus
  - standalone Sharpe 아닌 **BTC+breadth overlay의 한계기여**(MDD 축소·하방 tail·횡보 상방캡처). 2023-09+ 단일강세국면 caveat 명시
  - 판정변동: overlay가 BTC buy-hold 대비 MDD/tail 개선 → overlay 生(분산용) / 미달 → 死 유지
- [ ] **M3 FDR 재판정** · model: opus
  - BH-FDR(q=0.10) 전 신호 p값 일괄 재판정 + Upbit mom30 ⊥김프 p0.004 생존 복원 확인 + decay watch(2022+ p0.096 non-stationarity)
  - 판정변동: FDR 생존 신호 목록 + Bonferroni 대비 차이
- [ ] **M4 Q4 신규지표 candidate 박제 + 실데이터 1차** · model: opus
  - 6개: Coinbase premium(2020~)·Deribit DVOL(2021-04~)·VRP+펀딩극단치(2019~)·ETF flow(2024-01~)·VIX-MOVE(2011~)·스테이블 SSR(2018~)
  - 가용성 확인된 것(VIX-MOVE=장기 cross-era 가능, 펀딩=보유) 실데이터 1차 IC. 미보유는 collector_plan 등록
  - ⚠️ E3집중 신호=within-E3+경제prior+역인과통제 OOS-보류 등급, flow류=시차+동시수익 직교화
- [ ] **V 검증 subagent** — 측정 raw 독립 재현 + empirical-claim 5의무 + small-n rigor 감사 (over-claim/spec-code drift 차단)
- [ ] **L ledger/handoff 갱신** — indicator-ledger.md status·reason·research_ref + handoff §1 표 갱신

## 후속 — M4 Q4 신규지표 채택판정 = 코인 6단계 SOP 의무
> ★완료 기준 = **option 2 (5종 전부 풀 SOP S1~S6)** + **자문 배치**(나머지 4종 통합 자문). 자율주행 ON(2026-06-03). babyplace=논문발 NEW 지표 전담(M4 끝난 뒤 발송, progress 리마인더).
> candidate 박제(완료)는 탐구등록일 뿐. 채택/기각 = [plan-coin-indicator-review.md](./plan-coin-indicator-review.md) S1~S6 의무 적용(crypto=regime-conditional 자산 고정규칙). 거시신호는 sizing alpha 아닌 throttle overlay.
> **진행**: macro_vol_transfer S1~S4 완료(S5 ⊥DVOL+S6 잔여). 나머지 4종 S1~S2 → 통합 S3 → S4~S6.
- [ ] **S-Q4 6단계 SOP** — 우선순위순:
  1. **coin_macro_vol_transfer**(VIX-MOVE, ★유일 cross-era 가능=2011~ 3-era I² 게이트 통과 → S2부터 강) — 단 거시 M4 'MOVE=VIX 과잉통제 흡수' 전례 falsify 필요
  2. **coin_coinbase_premium**(directional 다변화, Upbit 직교 검정) — S2 ⊥upbit 잔존 IC
  3. **coin_dvol_iv**(vol carrier, ⊥reserve ensemble) — S2 reserve와 직교 IC
  4. **coin_vrp_funding_extreme**(tail, 펀딩 극단치 contrarian) — S2 청산 event-study
  5. **coin_ssr_oscillator**(stablecoin_total_supply와 분자/분모 중복 선점검 → S2)
  - 각 지표: **S1** 논문ground(subagent 3계층) → **S2** 실측 4게이트(ex-ante regime / Bonferroni→FDR / walk-forward OOS / NW-HAC) → **S3** 외부검토(gemini+claude 병렬 — 자문 Q4가 1차 완료, 지표별 깊이 보강) → **S4** 외부 falsification 다른데이터 재검증 → **S5** 역공격 수렴 → **S6** 15축 audit(hard-fail 0 후에만 status 확정·ledger 박제)
  - ⛔ 불변식: S3 자문 1회 없이 rejected_permanent 금지 / S6 hard-fail 0 전 adopted 확정 금지 / "전기간 불일치"는 영구폐기 사유 아님(crypto instability=norm)
