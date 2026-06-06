---
tags: [type/axis-audit, domain/equity, sector/telecom, scope/equity-kr]
date: 2026-06-05
purpose: 통신 15축 self-audit 초안 (G-A 3컬럼 적용/측정경로/결과). ★최종 G-C 독립 audit = 별 세션(본 self-audit는 참고용).
note: ★2 archetype 분리(frame §1.6) — service 3사 과점 시계열 / equipment 10종 cross-sectional. B/C/D/I hard-fail self-check = summary.yaml. (6/3 옛 통합 cross-sectional audit 대체)
---

# 통신(telecom) 15축 self-audit 초안 (A~P)

> ★본 self-audit는 **참고용**. 최종 G-C 독립 audit = 별 세션(author≠auditor, supervisor 스폰). hard-fail 코어 B·C·D·I (+M·N·O wire).
> ★핵심 = (A) service 배당주 duration INCONCLUSIVE + (B) equipment PBR value TENTATIVE(size confound 68%).

## 핵심 8축 (A~H)

| 축 | ① 적용했나 | ② 측정 경로·코드·수치 | ③ 결과·판정 |
|---|---|---|---|
| **A 이론 실재** | ✅ | theory-notes.md §1 (학술 ref: Cornell 2000 equity duration / Fama-French 1992 value / Jegadeesh-Titman 1993 momentum / Basu 1977 PER / DDM bond-proxy duration) | PASS — 메커니즘 부호 사전확약(HARKing 방지). 측정 前 동결. |
| **B★ 실데이터** | ✅ | pykrx OHLCV(14종 1818일) + FRED KR10Y/3M(IRLTLT01KRM156N/IR3TIB01KRM156N) + DART(357 rows 2019~) + regime(공통). 합성지문: 2020-08 KR10Y 1.37% 저금리/2022-10 4.27% 인상/2024-06 커브역전 -0.26 실재 | **PASS** — 합성 0%, raw-v3/*.py 재현. |
| **C★ 추적성** | ✅ | summary.yaml 모든 수치 = validation-{telecom,robustness}-v3.json key 매핑. ★size_neutral_ic_60d = measure_robustness.py B-R4 실측코드 + `equipment_pbr_size_neutral` JSON 박제(G-C 보강1, corr 0.5535/raw -0.167→neutral -0.053/shrink 68.5%) | **PASS** — LOO/size-neutral/OOS/ADF/family_2 raw 재현(size confound 실측코드 추가 완료). |
| **D★ PIT** | ✅ | 가격 forward shift(-h). KR 금리 FRED 월별(당월=익월 가용 ffill). DART rcept_dt 이후만(equipment 재무) | **PASS** — lookahead·restatement 회피. |
| **E 자문 환각** | ✅ | 자문 미사용(이론 = 학술 ref 직접). 부호 prior(배당주 duration 음 / value 음 / momentum 양) = 이론 독립 수립 후 측정 대조 | PASS — 이론 메커니즘만, 측정으로 검증(자문≠코드화). |
| **F 반증+기각** | ✅ | falsifier 정의(theory §1 각 신호) + ★기각 다수: service duration INCONCLUSIVE(부호 prior 반대) / momentum 무신호 / per underpowered / ★pbr value size confound(순수 value 약) | PASS — 기각 4+건(p-hacking 아님). |
| **G 검정력·tier** | ✅ | ★service cross-sectional INSUFFICIENT(3종). service 시계열 n_months 88, eff-N 보정 t. equipment avgN 9.2. ★pbr size-neutral t 약화 | PARTIAL — tier: equipment pbr=TENTATIVE(size-confounded) / service duration=INCONCLUSIVE / momentum·per=INSUFFICIENT. |
| **H 미해결** | ✅ | candidate-ledger §이연/falsifier(ARPU/5G data-gate, size confound) + research-log §미해결 | PASS. |

## 신규 4축 (I~L)

| 축 | ① 적용 | ② 측정 경로 | ③ 결과 |
|---|---|---|---|
| **I★ 생존편향** | ✅ | service 3사 과점 안정(상폐 적음). equipment KOSDAQ 소형(상폐 가능) but 현 스냅샷 universe(PIT 멤버십 미반영, collector low). 한화비전(489790) 최근상장 LOO 점검(outlier 아님) | PARTIAL — service 생존편향 작음. ★단 service 3종 자체가 표본부재(생존편향 아닌 data-gate). equipment PIT 멤버십 미반영. |
| **J 거래비용·capacity** | ✅ | ★service 종목선택 0 = net-cost 무대상. equipment pbr = KOSDAQ 소형 10종 = ★일평균거래대금 작음 = capacity 제약 + KR STT 0.2% 비대칭 net | PARTIAL — over-trade 차단(service 0 + equipment conservative cap). ★equipment 소형 capacity = 실매매 제한 flag. |
| **K 다중검정** | ✅ | 단일 FDR family(theory §3, 5가설 사전고정 → m=24 powered cell). BY survivors=[eqp_y_60d_pbr_z] 1개. wild-cluster bootstrap | PASS — FDR 보정 명시, survivor 1(약신호 정직). ★단 그 1개도 size-confounded. |
| **L 통합 PSD** | N/A(통합단계) | 공통인자 β(dollar/VIX/rate) 보고 = supervisor 통합 1회계상 입력. directional_spillover 후보 보고(빈[] 금지 충족) | DEFER — 통합 supervisor 단계(L축 = Phase 7). |

## wire 3축 (M~O) — study 단계 N/A
| 축 | 결과 |
|---|---|
| M wire충실 | N/A — production 미배선(teammate scope = capsule까지). |
| N cross PSD | DEFER — supervisor 통합. |
| O leakage | PASS(study) — PIT-safe(D축) + reject≠missing(service INSUFFICIENT vs equipment 측정값 구분, ARPU data-gate vs 측정 구분). |

## P net-cost robustness
- service 종목선택 0 = 매매 미구성. equipment pbr value = ★KOSDAQ 소형 = net-cost(STT 0.2% + 슬리피지) + capacity 제약 大 → conservative cap 의무. IC≠수익(직접 net 불가, 통합 backtest 단계). PARTIAL(조건부, 소형 capacity flag).

## ★hard-fail 코어 self-check 종합
- **B/C/D = PASS** (실데이터·추적성·PIT). **I = PARTIAL**(service 과점 생존편향 작음 + 3종 data-gate, equipment PIT 멤버십 미반영).
- ★hard-fail 0 (B·C·D 통과, I = PARTIAL 비FAIL). 단 **G(검정력) = PARTIAL** + ★전체 verdict = service INCONCLUSIVE + equipment TENTATIVE(size-confounded).
- ★G-G(매매충분성) = FAIL~PASS-conditional 경계: tradeable service 0(duration 미확인), equipment 1 conditional(pbr value, size-confounded → conservative cap).

## ★self-audit 한계 (정직)
- 본 self-audit = 참고용. G-C 독립 audit(별 세션)이 raw 재현으로 최종 판정.
- 핵심 리스크 = (1) ★equipment pbr value = raw BY 생존이나 size confound 68%(size-neutral -0.05) = 순수 value 약 = 사실상 소형주 효과(value 단정 금지) (2) ★service 배당주 duration = 부호 prior(음) 반대 + episode-poor(single rate cycle) + level I(1) = 미확인(bond-proxy 단정 금지) (3) ARPU/5G = data-gate(미측정) (4) service cross-sectional 영구 불가(3사 과점) = 종목선택 매매 불능.
- ★감사 주목점: G-C auditor 는 (a) size-neutral IC -0.05 재현(value vs size 분리) (b) service duration 부호 prior 반대 = episode-poor 정당성 (c) equipment per_z underpowered(avgN 6.3) 격하 정당성 검증 권고.
