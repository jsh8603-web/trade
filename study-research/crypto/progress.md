---
tags: [type/progress, study/crypto, phase/2-3-complete]
date: 2026-05-30
---

# crypto v2 progress

## Working Notes

> [ckpt-202605302322:btn-profile] crypto 2-3 완료
> (1) 마지막 결정: 7 validation md 실측 → yaml v2 + summary.md + 8축 self-audit
> (2) 다음 의도: btn-Codlearn 에 [crypto→main] 보고 송신 + task #6 완료
> (3) 동기화: v1 폐기 (raw/study_session.v1.yaml.deprecated), v2 = D:/projects/Inv/study-research/crypto/study_session.yaml 302줄

## Phase 완료 체크

- [x] 2-1 자문 다회 (R1~R3, gemini+claude, 수렴) — direction.md 20KB, raw/round-{1,2,3}-{gemini,claude}.md 56KB
- [x] 2-2 이론학습 (5채널 11문헌 학술 압축 + 거시 transmission + 5도구) — raw/theory-notes.md 28KB
- [x] 2-3 실데이터 검증 (6 무료 API 실측, 7건 validation, ⛔합성 0건) — raw/validation-*.md 20KB + scripts/*.py 50KB
- [x] yaml v2 7블록 + 8축 self-audit — study_session.yaml 302줄, summary.md 166줄

## ★실측 정정 (자문 vs 실데이터)

- H1 MVRV: marginal trend (+22.9% fwd_30d at MVRV>2.4) vs partial conditional mean-revert (-0.085 CI 0 포함). 가설 "marginal mean-revert" → "conditional only"
- H2 funding cascade: ★REJECT (binomial p=0.68 at p95+long, p=0.97 at p99+long). 부호 반전 = trend follow
- H3 stablecoin: Granger lead 확인 but bidirectional reflexive 위험 + rolling sharpe -0.43
- H4 ETF: 1차 검증 (hit rate 56.7% p=0.006), probation 0.05 유지
- H5 halving: standalone X 박제, conditioning 효과 음 IC 일관성 확인
- prior ladder: ★역방향 (on-chain sharpe 1.27 > micro 0.97 > stablecoin -0.43)
- eff_n gate: 73% admit @ N>=100, hybrid 유지 가능
