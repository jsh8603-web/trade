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

## ★핵심 결과

- **value (저PBR/저EV-EBITDA)** = PARTIAL_CONFIRMED (NW-HAC y60 t=2.73 + BY 생존 + pre-AI robust, 생존편향 상한).
- **low_vol/BAB** = PARTIAL_CONFIRMED (신규 발견, NW-HAC t=−2.8~−3.1 + BY 생존).
- quality·momentum = REJECTED. value+quality 결합 = REJECTED(Novy-Marx 통설 반증).
- conditional 증폭 = TENTATIVE/격하(overlapping 보정 후 붕괴).
- ★SOXX = PARTIAL_CONFIRMED 확정(freeze 아님). CONFIRMED 승격 = 생존편향 historical + DFII10 unblock 후.

## data-gate (unblock 대기)

- 생존편향 SOXX/ICE historical membership (무료 부재, CRSP 유료)
- DFII10 실질금리 (sandbox network timeout)
- R&D intensity (EDGAR concept 부재)
