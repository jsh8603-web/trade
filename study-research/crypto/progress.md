---
tags: [type/progress, study/crypto, phase/2-3-complete]
date: 2026-05-30
---

# crypto v2 progress

## Working Notes

> [ckpt-202605312355:btn-profile] crypto cycle 2 STUDY DONE
> (1) 마지막 결정: cycle 2 H7-H12 6 validation md 산출 + self-audit-cycle2.md + yaml v3 draft + git commit
> (2) 다음 의도: main 의 opus subagent 12축 audit 진입 신호 → cycle 3 (yaml v3 통합·walk-forward OOS·CoinMetrics paid tier·VECM·거래비용)
> (3) 동기화: main P0 unblock (2026-05-31) 수용 → 본 방 직접 fetch (CoinMetrics 4 + FRED 3 + yfinance 4 + PyTrends + DefiLlama 2)
> (4) cycle 2 verdict: REJ 4 (H7/H8/H10/H12) + TENT 1 (H9 ANOVA p=0.0006 Bonf-survive but digital-gold 정반대) + PARTIAL 1 (H11 attention IC=0.1117 post-2021 sign 일관) — F 기각 풍부 p-hacking 신호 0
> (5) 자료 가치: 자문 학술 prior (Pagnotta sub-Metcalfe / Catalini utility / Baur digital gold / Cong DeFi utility) 본 표본 ★기각, Liu&Tsyvinski attention monthly 부분 지지, ETF 시대 BTC-Gold 디커플 + digital-gold 서사 ★부정

> [ckpt-202605312355:btn-profile] crypto handoff + commit **STATUS**: resolved (cycle 2 시작 시점)
> (1) 마지막 결정: handoff-crypto-20260531.md 작성 + git add crypto/ + handoff
> (2) 다음 의도: commit "feat(crypto/study): v2 yaml+실측7validation+merit-queue+handoff" → main "HANDOFF DONE" 1줄 → compact
> (3) 동기화: main 의 collector 11종+모델 3종 구현 응답 대기. 인계 = D:/projects/Inv/handoff-crypto-20260531.md

> [ckpt-202605302322:btn-profile] crypto 2-3 완료 **STATUS**: resolved (2026-05-31 handoff 흡수)
> (1) 마지막 결정: 7 validation md 실측 → yaml v2 + summary.md + 8축 self-audit
> (2) 다음 의도: btn-Codlearn 에 [crypto→main] 보고 송신 + task #6 완료
> (3) 동기화: v1 폐기 (raw/study_session.v1.yaml.deprecated), v2 = study_session.yaml 302줄

## Phase 완료 체크

- [x] 2-1 자문 다회 (R1~R3, gemini+claude, 수렴) — direction.md 20KB, raw/round-{1,2,3}-{gemini,claude}.md 56KB
- [x] 2-2 이론학습 (5채널 11문헌 학술 압축 + 거시 transmission + 5도구) — raw/theory-notes.md 28KB
- [x] 2-3 실데이터 검증 (6 무료 API 실측, 7건 validation, ⛔합성 0건) — raw/validation-*.md 20KB + scripts/*.py 50KB
- [x] yaml v2 7블록 + 8축 self-audit — study_session.yaml 302줄, summary.md 166줄
- [x] cycle 2 P0-A CoinMetrics 4 metric 직접 fetch (AdrActCnt/TxCnt/HashRate/BlkCnt, paid tier 5종=403)
- [x] cycle 2 P0-B FRED 3 + yfinance 4 fetch (DFII10/DTWEXBGS/M2SL + IXIC/GSPC/VIX/GC=F Gold)
- [x] cycle 2 P0-C PyTrends + DefiLlama TVL/DEX 확장 fetch
- [x] cycle 2 H7-H12 6 신규 가설 검증 — raw/validation-h{7-12}-*.md 6건
- [x] cycle 2 self-audit-cycle2.md + spec-code-rationale-cycle2.md + yaml v3 draft (audit 통과분: H9 regime + H11 attention)
- [ ] cycle 3 진입 후속: walk-forward strict OOS / VECM stablecoin reflexive / CoinMetrics paid tier / 거래비용 차감 / Deflated Sharpe

## ★실측 정정 (자문 vs 실데이터)

- H1 MVRV: marginal trend (+22.9% fwd_30d at MVRV>2.4) vs partial conditional mean-revert (-0.085 CI 0 포함). 가설 "marginal mean-revert" → "conditional only"
- H2 funding cascade: ★REJECT (binomial p=0.68 at p95+long, p=0.97 at p99+long). 부호 반전 = trend follow
- H3 stablecoin: Granger lead 확인 but bidirectional reflexive 위험 + rolling sharpe -0.43
- H4 ETF: 1차 검증 (hit rate 56.7% p=0.006), probation 0.05 유지
- H5 halving: standalone X 박제, conditioning 효과 음 IC 일관성 확인
- prior ladder: ★역방향 (on-chain sharpe 1.27 > micro 0.97 > stablecoin -0.43)
- eff_n gate: 73% admit @ N>=100, hybrid 유지 가능
