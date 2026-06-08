---
tags: [type/15axis-audit, domain/equity-us, sector/soxx_semi, phase/sector-granular]
date: 2026-06-08
purpose: SOXX 반도체 capsule 15축 자가감사 (A~L study축 + M~O wire축). ★self-audit = 참고, 독립 audit subagent 최종 판정.
verdict: 부분 (hard-fail 코어 B·C·D PASS / I PARTIAL = TENTATIVE 상한). value·low_vol PARTIAL_CONFIRMED.
---

# SOXX 반도체 — 15축 자가감사 (R4)

> ★AUDIT-GUIDE §0 Provenance: yaml 수치 = "주장" → raw-v3/*.py + validation-*.json 재계산 추적 가능. 합성 0%.
> ★self-audit 는 통과편향 → 독립 audit subagent(opus) 가 최종 판정. 본 문서 = 캘리브레이션 참고.

## 핵심 8축 (A~H)

| 축 | 판정 | 근거 |
|---|---|---|
| **A 이론실재성** | ✅ PASS | theory-notes 저자·연도·저널 명시(FF1992/93, Novy-Marx2013 JFE, QMJ2019 JFE, Frazzini-Pedersen2014 JFE, Cooper-Gulen-Schill2008, Jegadeesh-Titman1993, Lettau-Wachter2007 JF62(1), Chan-LS2001 JF56(6), Cohen-PV2009 JF64(5)). R2 cross-verify 완료(R&D 부호 정정, Cohen-PV 연도 정정). 자문 복붙 아닌 본인 종합 |
| **B 실데이터** ★ | ✅ PASS | 합성 0%. yfinance prices(2867 daily, 2015~) + EDGAR(22,798 rows PIT) + FRED macro. raw-v3/measure_*.py 재현. ★OOS IC>0.03 AND NW-HAC t>2.0 = value y20 IC0.068 t3.24 / low_vol y20 −0.075 t−3.11 충족 |
| **C 추적성** ★ | ✅ PASS | 모든 IC = validation-{vq,conditional,r4-corrections}-v1.json key 매핑. base_weight range = IC CI 반영(점추정 박제 0) |
| **D PIT** ★ | ✅ PASS | EDGAR (ticker,concept,end) 최초 filed 이후만 + forward shift(t→t+h). macro ffill PIT. ★filed-end lag median 227d = 최초 filed 채택으로 lookahead 완화 |
| **E 환각** | ✅ PASS (적발) | ★FRED id 3건 날조 적발(TWNEXPCESEMIT/KORXTOTLSEMISME/SINI=404) + UMCSENT 라벨오류 제거. ★rate10y=nominal(NOT DFII10 실질) data 라벨 정정. 학술 인용 R2 cross-verify(R&D 부호·Cohen-PV 연도 정정) |
| **F 반증·기각** | ✅ PASS | predicted_sign 사전등록 + 반증조건 4종. ★기각 다수: book-to-bill(κ) drop / quality(ROIC) 무신호 REJECTED / value+quality 결합 희석(Novy-Marx 통설 반증) / momentum OOS 부호반전 / family-2 conditional overlapping 보정 후 붕괴. = p-hacking 아님 |
| **G eff-N tier** | ⚠️ tier | N=12 small-N → 검정력 시계열. ★y_60d overlapping = NW-HAC eff_N 겹침보정(/lag) 적용. value·low_vol = PARTIAL_CONFIRMED tier(CONFIRMED 불가 = 생존편향) |
| **H 미해결** | ✅ PASS | §6 = 생존편향/overlapping/DFII10 data-gate/FDR M_eff/sub-industry 솔직 기재 |

## 신규 4축 (I~L)

| 축 | 판정 | 근거 |
|---|---|---|
| **I 생존편향** ★ | ⚠️ **PARTIAL** | ★현 12종 = SOXX/ICE 현 holdings only. MRVL/NXPI 등 현 편입종목 누락 + 과거 편출/상폐 부재. historical membership 무료부재(CRSP/Compustat 유료, fetch 시도 실패). → ★**TENTATIVE 상한**(CONFIRMED 금지). 생존편향 = 결과 약화 아니라 잠재 무효화 위험 인지, 정직 라벨 |
| **J 거래비용** | ⚠️ soft | 왕복 비용 미차감(R5 의제). value/low_vol IC 0.07~0.12 = breadth 12종 IR 마진 좁음. capacity 미검토 |
| **K 다중검정** ★ | ✅ PASS | ★시도횟수 공시: 45셀 + family-2 10. ★BY-FDR(의존성 보정) q=0.10 → 10셀 생존(value·low_vol). M_eff 미통합(보수적 naive m). 우연 기대 2.3 vs 생존 10 = 신호 실재 |
| **L 통합 PSD** | ⏳ 통합단계 | partial-corr / 공통인자(rate·credit) 1회계상 = supervisor RegimeGlasso 통합. ★mega_tech 중복(NVDA/AVGO ↔ us_mega_tech) double-count 차단 의제 |

## wire 3축 (M~O) — study 단계 = N/A

- M wire충실 / N cross관계 / O leakage = study→코드 wire 작업 고유. ★현 = study 산출 단계 = wire 미진입 = N/A. 통합 시 적용.

## ★hard-fail 코어 4 (B·C·D·I) 종합

- **B 실데이터 PASS / C 추적성 PASS / D PIT PASS** = 3/4 통과.
- **I 생존편향 = PARTIAL** (현 holdings only, historical 무료부재) = ★통합 차단 아니나 **TENTATIVE 상한** 강제.
- → ★**hard-fail 무효화 0건** (합성·재계산불일치·lookahead 없음). I PARTIAL = 신뢰도 라벨 강등(격하 아님).

## ★최종 verdict

- **value (unconditional)** = PARTIAL_CONFIRMED (NW-HAC t3.24 + BY 생존 + pre-AI robust, 생존편향 상한).
- **low_vol/BAB (unconditional)** = PARTIAL_CONFIRMED (NW-HAC t−2.8~−3.1 + BY 생존, 생존편향 상한).
- **conditional (regime 증폭)** = TENTATIVE/격하 (family-2 overlapping 보정 후 붕괴, rate_high=AI episode 의존).
- **quality·momentum** = REJECTED/무신호.
- ★전체 = **부분(PARTIAL)**: hard-fail 무효화 0 + value·low_vol robust(PARTIAL_CONFIRMED) + 생존편향 PARTIAL = TENTATIVE 상한.
- ★독립 audit subagent 권고: value·low_vol register 가능(require_raw=True, TENTATIVE tier) / conditional 증폭은 보류.
  생존편향 보강(historical membership) + DFII10 재fetch 후 tier 재판정.
