# 핸드오프 — 코인 신호 자문 재측정 + ledger 박제 + PIT harness2 Phase 0a (자기완결)

> 2026-06-03 btn-Inv. 이 문서 1개로 재개. 두 트랙 = (A) crypto 신호 재측정·박제 완료 / (B) PIT harness2 Phase 0a 신설, Worker dispatch 대기.
> ⛔ go-live 미접촉·push 금지·risk_gate 상수 무수정.

## §1 이번 세션 한 일 (완료)
1. **외부 자문 2모델 1R 수렴**(claude-web Opus·gemini-web Pro, CIO 페르소나). 브리핑=.consult-killverdict-briefing.md, 응답=tasks/bbfdbv0yz.output(claude)·bnprfbrcp.output(gemini).
2. **자문 부당판정 3건 재측정**(.p2-killverdict-recheck2.py, .p2-upbit-self.py, .p2-breadth-monthly.py) + **독립검증 subagent**(audit a3c1b865, agentId a3c1b8658eb848e30).
3. **ledger 박제** + M4 신규지표 5개 candidate + sector_relative_multiple(eq_us).
4. **PIT harness2 Phase 0a(signal-power-first) 신설**(SR Pre-Review C ACCEPT 반영).

## §2 자문 수렴 결론 (Q1~Q4)
- **Q1 빈약함**: 부분 타당. 방향축 빈약=효율화 진짜 / vol "SPOF"=절반 측정 인공물(vol clustering 공선성, ensemble carrier 처방).
- **Q2**: 활성주소 死 타당(proxy 낡음→ETF flow 교체) / netflow·breadth 기각 부당 후보 / 글로벌momentum 死 타당.
- **Q3**: Bonferroni 부적절→FDR(BH q0.10/LORD++). Upbit mom30 복원(약).
- **Q4 신규지표**(실데이터 검증): Coinbase premium(2020~)·Deribit DVOL(2021-04~)·VRP+펀딩극단(2019~)·ETF flow(기존adopted)·VIX-MOVE(2011~ ★cross-era)·SSR(2018~). ⚠️대부분 E3집중=OOS-보류 등급, flow류 역인과 직교화.

## §3 재측정 최종 판정 (검증관 정정 반영)
| 신호 | 판정 |
|---|---|
| netflow | **死 확정** — 단일일·누적30d·regime 모두. 누적flow는 검증관이 **인공물 격하**(E3 +0.042 p0.69 부호반전·NW maxlags60서 p0.053·2011 outlier 의존). ledger coin_exchange_netflow falsifier 박제 |
| Upbit momentum | **약 directional 한정** — donch20 ⊥kimchi 死(p0.088, 이중계상)·mom30만 ⊥kimchi +0.150 p0.004 잔존(E3 p0.096 약화). BH-FDR(family≤13) 생존하나 **Bonf통과는 family 민감**(검증관 over-claim 격하). ledger coin_tsmom 정정 |
| breadth | **INSUFFICIENT** — 2023-09~ 강세 단일국면, overlay 판정불가 |
| FDR 전환 | 타당 — Bonferroni→BH. 단 family 정의(m) 정직추정 미박제 = 잔여 |

★검증관 5의무 위반 지적 3건(autocorr·regime 부호일관·family 의존) 전부 정정 완료.

## §4 ledger 박제 (study-research/_wire/indicator-ledger.md)
- **coin_exchange_netflow**(53): rejected_provisional + falsifier(死 확정)
- **coin_tsmom**(45): ⊥kimchi+FDR 정정 append
- **M4 신규 candidate 5**(halving_phase 뒤): coin_coinbase_premium·coin_dvol_iv·coin_vrp_funding_extreme·coin_macro_vol_transfer·coin_ssr_oscillator (전부 실측 미측정, 데이터원·가용기간 박제)
- **sector_relative_multiple**(eq_us, ism_pmi_proxy 뒤): Damodaran/French49 섹터 멀티플, PIT py 발견분 candidate
- ⚠️ crypto 헤더 "candidate 12" → 17 갱신 잔여(헤더 긴 줄)
- ★**M4 채택판정 = 코인 6단계 SOP 의무**(plan-coin-indicator-review.md S1~S6, plan-killverdict-recheck §후속): 우선순위 macro_vol_transfer(★cross-era 2011~)→coinbase_premium→dvol_iv→vrp_funding→ssr. 각 S1논문→S2실측4게이트→S3자문(Q4 1차완료)→S4재검증→S5역공격→S6 15축audit. ⛔ S6 hard-fail 0 전 adopted 금지 / S3 없이 rejected_permanent 금지. candidate 박제=탐구등록일 뿐, 채택 아님.

## §5 PIT harness2 (트랙 B) — Worker dispatch 대기
- **.harness2/harness2.md**: Phase 0a(signal-power-first 게이트) 신설 + Phase 0~7(electrs 온체인 재구성). team **h2wf-Inv** 생성됨. SR Pre-Review(C) ACCEPT(execution-log sr_review mode=C), SR teammate **idle 점유 중**.
- **SR 핵심 지적**(가정 3개 기각): lastmod≠knowability(release-tag pin) / 단일 epoch within-FE=predictive 불가(leave-one-event-out) / 공개 mempool.space balance replay=timeout(electrs self-host 필수, 군집 recall<10%).
- ⛔ **★순서 정정 (사용자 지적 2026-06-03)**: harness2 를 먼저 돌리려던 건 jumping the gun. SR 이 기각한 3가정은 전부 **electrs 온체인 재구성(Phase 0~7) 전제** = 그 비싼 빌드를 할지 결정하는 **Phase 0a(signal-power-first)는 메인 직접 측정**(CM 무료 flow IC, .p2 스크립트 30분, harness2 10-agent 불요).
- **★다음 = 메인 직접 Phase 0a 측정 (harness2 미사용)**:
  1. **메인 직접**: `.p2-corrected-frame.py` build() 재사용 → `reserve_z→fwd-vol` + `abs(netflow)→fwd-vol` 을 2022-11+ within incremental rank-IC + NW-HAC(maxlags≥horizon) + leave-one-event-out(FTX/SVB/ETF) 부호일관 측정. (reserve→vol 은 §1 TACTICAL-CONFIRMED 였으니 PIT-clean·라이브-epoch 재확인 성격)
  2. **GREEN**(IC>0 유의·event-LOO 부호일관) → 그때 electrs self-host PIT 온체인 재구성(Phase 0~7)을 harness2 로: `bash ~/.claude/skills/harness2-wf/lib/teammate-spawn.sh spawn .harness2 h2wf-Inv` → Worker/Verifier/watchdog Agent 스폰. (electrs·군집·vintage 복잡 = harness2 가치 발생 지점)
  3. **RED**(IC 죽음) → PIT 온체인 재구성 **폐기**, harness2 불요, open hypothesis 강등 + 사유 리포트만.
- team h2wf-Inv = **GREEN 후 재사용 대기**(현재 idle, SR shutdown 완료). harness2.md Phase 0~7 그대로 유효(0a 게이트 블록은 메인 측정 결과 기록용).

## §6 측정 산물 (.p2-*.py 임시)
killverdict-recheck2(M1 netflow threshold+M3 FDR) / upbit-self(②Upbit자체fwd) / breadth-monthly(④월간+틸트) / corrected-frame(capstone build()) / killverdict-recheck(첫 §7 재측정)

## §7 plan/progress
plan-killverdict-recheck.md + progress-killverdict-recheck.md (M1~M4·V·L 전부 [x], handoff 표 갱신만 잔여)
