---
tags: [type/candidate-ledger, domain/equity, sector/telecom, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# telecom(통신) 지표 후보 원장

> ★2 archetype 분리(frame §1.6): (A) 통신서비스 3사 = 시계열(과점) / (B) 통신장비 10종 = cross-sectional(cyclical).

## ✅ 채택 (yaml 등록 + 검증 통과)
| 지표 | unit | family | tier | 근거 (source·n·검증) |
|---|---|---|---|---|
| equipment PBR z (저PBR value) | 장비 횡단면 | value | ★TENTATIVE (conservative cap) | 60d IC -0.167 wc_p=0.0005 BY 생존(통신 유일) + LOO robust 10종 전부 음 + OOS 강화. ★단 size confound 68%(size-neutral -0.05) = 소형주 효과. |
| ★rotation 외국인 flow (음) | service 업종 timing | rotation/defensive | ★PASS-conditional (strong) | 60d rho -0.396 wc_p=0.001 ★well-powered(t_pow 3.58) + OOS hold + leave-episode 불변(-0.39) + 이론(risk-on flow→defensive UW) 정합. ★flow=전산업 공통(L축 1회계상). |
| ★rotation semi_ppi yoy (음) | service 업종 timing | rotation/defensive | ★PASS-conditional (moderate) | 60d rho -0.261 wc_p=0.027 + OOS hold + 이론(defensive counter-cyclical) 정합. ★leave-episode 약화(-0.16, 부분 episode-driven) + underpowered. |

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| service 배당주 금리 duration | M1 이론(Cornell 2000) | ★시계열 측정 INCONCLUSIVE(부호 prior 반대 + 비유의 + episode-poor) = 미확인 | 추가 rate cycle(금리 하락기 재진입) episode ≥2 누적 후 forward 음 유의 |
| ARPU / 5G 가입자 / capex peak-out | M2 이론(통신 KPI) | ★data-gate — MSIT/통계청 무료 clean time-series API 부재 | ARPU/5G 월별 series 확보(수동 스크랩 or API) |
| 배당수익률 직접 | M1 보완 | DART dart_financials 배당 line 미수집 | DART 현금배당 공시 수집 → 배당수익률 vs 국채 spread |

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|
| service cross-sectional (PBR/PER/value 종목선택) | ★INSUFFICIENT — 3사 과점(SKT/KT/LGU+), Spearman IC min 8종 불가. 정유 2종 패턴 동형 |
| equipment momentum 12-1 | 무신호 — 전 horizon 비유의(wc_p>0.14) + 부호 prior(양)와 반대 약 |
| equipment PER z | underpowered — avgN 6.3<8(흑자 138/215, 적자 빈발 KOSDAQ 소형). y_60d 음 힌트나 단정 불가 |
| US 10Y(^TNX) duration | ★한국 배당주 discount rate 부적합 → KR 10Y(IRLTLT01KRM156N)로 대체. US는 대조용만 |
| 6/3 옛 v3 통합 cross-sectional(service+equipment n=13, IC -0.542) | ★24M overlap horizon artifact(eff_N≈2.5)지 PBR 부호 cancel 아님(pool/장비/service 셋 다 음 -0.16~-0.20). 분리 근거 = 측정축 차이 + driver 본질차 → 2 archetype 분리로 정정(G-C 보강2) |
| ★rotation mom_12_1 (1차 +0.284) | ★data-mining REJECTED — strict service 3사 단독 +0.063(wc_p=0.53, OOS flip) = 신호 부재. 1차 +0.284 = ★패널구성 artifact(broad telecom 패널, equipment momentum 혼입). dividend-carry 이론 service서 미입증 |
| ★rotation cli_chg (양) / usdkrw_yoy (음) | exploratory(채택보류) — BY 생존/유의이나 ★prior 부호 위배(HARKing 회피). cli_chg는 risk-on 지표 음상관 통해 defensive 정합 가능하나 사전확약 위배 |
| ★rotation KR 금리 duration | INCONCLUSIVE — duration(음) prior 위배 + 비유의(본측정 일치). episode-poor single rate cycle |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| equipment PBR value | ★size confound 68% — 순수 value인가 소형주 효과인가 | live size-neutral IC < 0 유지 (→ 0 수렴 시 순수 size effect 확정 = reject) |
| equipment PBR value | KOSDAQ 소형 capacity — 실매매 가능 규모 | long_short backtest net-cost(KR STT 0.2% + 슬리피지) 후 양 |
| service rate duration | episode-poor(single rate cycle) — 부호 prior 반대가 진짜인가 표본 한계인가 | 금리 하락기 재진입 시 KR10Y↑→forward 음 전환 여부 |

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — equipment PBR = size-confounded TENTATIVE, rule 승격 보류) | 검증된 정량 규칙 |
| memory | ★통신 = 2 archetype 분리 필수(service defensive 3사 과점 ≠ equipment cyclical 10종). 한 풀 cross-sectional 금지 | 다음 cycle 자문 prior 정정 |
| memory | ★배당주 duration = 한국 통신 2019-26 표본서 미확인(episode-poor). bond-proxy 단정 금지 | 동적가중 prior 정정 |
| memory | ★통신 rotation 본질 = defensive counter-cyclical(risk-on flow/semi_ppi↑→통신 UW), carry tilt 아님. flow=전산업 공통 | 다음 cycle rotation prior |
| observe-only | equipment PBR value (size-neutral IC 추적) | N/size-neutral 누적 후 promotion 결정 |
| observe-only | rotation semi_ppi (leave-episode 약화, episode 누적 후 재평가) | episode 누적 후 strong 승격 여부 |
| evt | ★rotation mom_12_1 패널구성 artifact = 1차 +0.284(broad) vs strict service +0.063(소멸). 패널 정의(strict 화이트리스트) 의무 | promotion-log ERROR 후보(broad 패널 momentum 혼입 함정) |
| evt | ★pbr value size confound 68% = G-A A-4 size 분리 의무(소형주↔value 오염) | promotion-log ERROR 후보(value 단정 함정) |
| evt | ★G-C 보강2: "통합 cross-sectional = PBR 부호 cancel" framing 오류 — 재현 시 pool/장비/service PBR 셋 다 음(cancel 없음), 옛 -0.542는 24M overlap artifact. archetype 분리 근거 = 측정축·driver 본질차지 cancel 아님 | promotion-log ERROR 후보(분리 근거 over-framing — 결론 맞아도 mechanism 서술 정밀화 의무) |
| pointer | refining theory-notes/summary.yaml = 과점→시계열 패턴 reference. 다음 협소산업 진입 시 정독 | 다음 세션 SSOT |
