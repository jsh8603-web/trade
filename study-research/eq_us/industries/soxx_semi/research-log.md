---
tags: [type/research-log, domain/equity-us, sector/soxx_semi, phase/sector-granular]
date: 2026-06-08
purpose: SOXX 반도체 granular 파일럿 R1~R5 작업 로그 + 8파일 체계 매핑.
---

# SOXX 반도체 — research-log (R1~R5)

## 8파일 산출 매핑 (한국 동형)

| 파일 | 상태 | 비고 |
|---|---|---|
| round-1.md | ✅ | H1~H5 가설 + 반증조건 prereg + collector_plan |
| theory-notes.md | ✅ | 학술 ground(저자·연도 A축) + κ falsify + regime + E축 환각검증 + R1 15축 self-check |
| validation-fundamental.md | ✅ | R3 value+quality 결정실험(unconditional, 초기 freeze) |
| validation-conditional.md | ✅ | R3 재측정 conditional IC surface(지표×regime×horizon) + R4 보정(§5-bis) |
| ~~validation-macro.md~~ | △ 통합 | regime(rate/credit conditioner) = validation-conditional.md 에 통합(별 파일 불요) |
| ~~validation-industry.md~~ | △ 통합 | κ(book-to-bill/수출) = drop → theory-notes §2 에 박제(측정 대상 부재) |
| summary.yaml | ✅ | 7블록 + conditional_ic_surface + r4_correction + tier_final |
| 15axis-audit.md | ✅ | A~L 자가감사, hard-fail B·C·D PASS / I PARTIAL |
| candidate-ledger.md | ✅ | 6분류(채택/측정미달/data-gate/미채택/falsifier/flip-register) |

## 라운드별 로그

- **R1** (이론·가설): Gemini 2-Phase 리서치 4건 → theory-notes 신설. ★E축 환각 적발(FRED id 3건 날조). κ falsify 강화. 커밋 453e455, e9b1bb0.
- **R2** (실측준비): 인용 cross-verify(★R&D 부호 음→양 정정, Cohen-PV 연도). sub-industry MDE 재계산. EDGAR 재사용 확정(중복 회피). EW-semi=SOXX/ICE. 커밋 b0c8009.
- **R3** (실측): value+quality unconditional → 초기 (C) freeze 권고. 커밋 13ff976. → team-lead 정정(horizon 누락) → conditional IC surface 재측정 = FREEZE 철회. 커밋 2367ecd.
- **R4** (보정): overlapping NW-HAC + family-2 block-cluster + BY-FDR + AI episode. tier 확정 = value·low_vol PARTIAL_CONFIRMED. 커밋 6a7c459.
- **R5** (마무리): candidate-ledger 6분류 최종 + GUIDE §12 교훈 명문화 + research-log.

- **R5b** (자문 4게이트): value over-claim 정정 — leave-NVDA·AVGO retention 0.044 = 2-name position. low_vol = anti-BAB misspec KILL. 커밋 8786a1f.
- **R6** (코드화 확정): G1 lag PASS → ★G2 breadth FAIL(중소형 21종 추가 시 value IC 0.109→0.024 소멸) → G3 생존편향 data-gate → ★G4 value 코드화 불가(null result). 커밋 0b158a8/71a9c16.

## ★핵심 결과 (R6 최종)

- **value (저PBR/저EV-EBITDA)** = ★**코드화 불가 / NVDA·AVGO 2-name position** (factor 미입증). G1 lag artifact 아님(non-overlap t>2) BUT G2 breadth 확장 시 소멸(IC 0.109→0.024, retention −0.257). ⛔§방향보존: value 무효 아닌 범위한정.
- **low_vol/BAB** = REJECTED-as-constructed (anti-BAB misspec, KILL).
- quality·momentum·value+quality 결합 = REJECTED.
- ★SOXX selection = **null result** (코드화 가능 매도신호 수준 미달). ★사용자 가설(breadth 확장하면 살아난다) = 데이터 반박.
- ★승격 잔여 = CRSP 생존편향-free + 딥밸류 소형(XSD보다 광의) data unblock 후 재측정.

## ★자산화 교훈 (자문/사용자 가설 3건 falsify)
1. Novy-Marx value+quality 결합 강화 → quality 무신호로 희석(반증).
2. momentum 미국 작동 → OOS 부호반전(반증).
3. ★breadth 확장하면 value 살아난다 → 중소형 추가 시 소멸(반증). = value는 대형주 2-name position.

## data-gate (unblock 대기)

- 생존편향 SOXX/ICE historical membership (무료 부재, CRSP 유료)
- DFII10 실질금리 (sandbox network timeout)
- R&D intensity (EDGAR concept 부재)
