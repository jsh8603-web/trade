---
tags: [type/axis-audit, domain/equity, sector/refining, scope/equity-kr]
date: 2026-06-05
purpose: 정유 15축 self-audit 초안 (G-A 3컬럼 적용/측정경로/결과). ★최종 G-C 독립 audit = 별 세션(본 self-audit는 참고용).
note: ★data-gate 산업 — cross-sectional 측정 불가(strict 2종). B/C/D/I hard-fail self-check = summary.yaml.
---

# 정유(refining) 15축 self-audit 초안 (A~P)

> ★본 self-audit는 **참고용**. 최종 G-C 독립 audit = 별 세션(author≠auditor, supervisor 스폰). hard-fail 코어 B·C·D·I (+M·N·O wire).

## 핵심 8축 (A~H)

| 축 | ① 적용했나 | ② 측정 경로·코드·수치 | ③ 결과·판정 |
|---|---|---|---|
| **A 이론 실재** | ✅ | theory-notes.md §1 (Gemini 리서치 + 학술 ref: Cooper-Gulen-Schill 2008 / Deaton-Laroque 1992 / Fama-French 1992 / Lev 1974 / Damodaran) | PASS — 메커니즘 부호 사전확약(HARKing 방지). 측정 前 동결. |
| **B★ 실데이터** | ✅ | pykrx OHLCV(11종 1818일) + FRED Brent/Gulf crack/IP + DART(financials+extended) + regime(공통). 합성지문: 2020-04 Brent$19.8/2022-06 diesel crack$64/2024-09 정상화 실재 | **PASS** — 합성 0%, raw-v3/*.py 재현. |
| **C★ 추적성** | ✅ | summary.yaml 모든 수치 = validation-{timeseries,ts-robustness,capex-cycle,valuation-ts,cross-placebo}-v3.json key 매핑 | **PASS** — eff-N/OOS/family_2/ADF 재현. |
| **D★ PIT** | ✅ | 가격 forward shift(-h). 유가/crack 일별 spot. refinery_ip IP_PUB_LAG=2. DART rcept_dt 이후만 | **PASS** — lookahead·restatement 회피. |
| **E 자문 환각** | ✅ | Gemini 리서치 = 내 실측과 cross-verify(유가 동시+/예측-, capex 음, PBR○PER✗). 자문≠코드화(본인 측정 증거) | PASS — 자문 메커니즘만 추출, 측정으로 검증. |
| **F 반증+기각** | ✅ | falsifier 정의(theory §1 각 신호) + ★기각 다수: capex REJECTED(spurious) / PER 무효 / 가동률 OOS flip / crack 약 | PASS — 기각 4+건(p-hacking 아님). |
| **G 검정력·tier** | ✅ | ★cross-sectional = INSUFFICIENT(2종). 시계열 n_months 82~88, eff-N 보정 t. 유가 t=-1.96 marginal | PARTIAL — tier=structural_prior_low_confidence(유가), 나머지 TENTATIVE/INSUFFICIENT. |
| **H 미해결** | ✅ | candidate-ledger §이연/falsifier + research-log §미해결(싱가포르GRM/universe확대) | PASS. |

## 신규 4축 (I~L)

| 축 | ① 적용 | ② 측정 경로 | ③ 결과 |
|---|---|---|---|
| **I★ 생존편향** | ✅ | 정유 과점(SK이노/S-Oil 안정)=구조조정·상폐 적음. 현 스냅샷 universe(PIT 멤버십 미반영, collector low) | PASS_with_caveat — 생존편향 영향 작음(과점). ★단 2종 자체가 표본부재(생존편향 아닌 data-gate). |
| **J 거래비용·capacity** | ✅ | ★종목선택 신호 0 = 매매룰 미구성 → net-cost 무대상. 산업 timing(유가)=sleeve-level, 종목 turnover 없음 | PASS(조건부) — over-trade 차단(종목선택 weight 0). microcap 3종 floor 미달 = capacity 배제. |
| **K 다중검정** | ✅ | 단일 FDR family(theory §3, 7가설 사전고정). 시계열 FDR(m=6) survivors=0. wild-cluster bootstrap | PASS — FDR 보정 명시, survivors 0(약신호 정직). |
| **L 통합 PSD** | N/A(통합단계) | 공통인자 β(유가/usdkrw/crack) 보고 = supervisor 통합 1회계상 입력. directional_spillover 후보 보고(빈[] 금지 충족) | DEFER — 통합 supervisor 단계(L축 = Phase 7). |

## wire 3축 (M~O) — study 단계 N/A
| 축 | 결과 |
|---|---|
| M wire충실 | N/A — production 미배선(teammate scope = capsule까지). |
| N cross PSD | DEFER — supervisor 통합. |
| O leakage | PASS(study) — PIT-safe(D축) + reject≠missing(INSUFFICIENT vs 측정값 구분). |

## P net-cost robustness
- 종목선택 신호 0 = 매매 미구성. 산업 timing(유가 mean-reversion) = de-risk(turnover 없음). PASS(조건부, 매매룰 미구성).

## ★hard-fail 코어 self-check 종합
- **B/C/D = PASS** (실데이터·추적성·PIT). **I = PASS_with_caveat**(과점 생존편향 작음, 단 2종 data-gate).
- ★hard-fail 0 (B·C·D·I 통과). 단 **G(검정력) = PARTIAL** + ★전체 verdict = INSUFFICIENT(cross-sectional) + TENTATIVE(시계열).
- ★G-G(매매충분성) = FAIL~PASS-conditional 경계: tradeable cross-sectional 0, 산업 timing 1 marginal(risk-monitor).

## ★self-audit 한계 (정직)
- 본 self-audit = 참고용. G-C 독립 audit(별 세션)이 raw 재현으로 최종 판정.
- 핵심 리스크 = (1) 유가 forward 음 = eff-N marginal + level I(1) spurious 부분위험(alpha 단정 금지, risk-monitor 격하) (2) crack = Gulf proxy 한계(싱가포르GRM 미측정) (3) cross-sectional 영구 불가(과점) = 종목선택 매매 불능.
