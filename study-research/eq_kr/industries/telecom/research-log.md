---
tags: [type/research-log, domain/equity, sector/telecom]
date: 2026-06-05
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# telecom(통신) 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| universe | FDR KRX-DESC "전기 통신업" + "통신 및 방송 장비 제조업" | service strict 3종 + equipment strict 10종 | 분리 | ★service 3사 과점 = cross-sectional 불가. equipment 10종 = 가능하나 cyclical 이질 |
| KR 금리(배당주 duration) | FRED IRLTLT01KRM156N(KR10Y) + IR3TIB01KRM156N(KR3M) | 월별 2000~2026-04 OK | KR10Y | ★common_factors.parquet rate10y = US ^TNX(2020 0.56%) = 한국 배당주 discount rate 부적합 → KR10Y 별도 수집 |
| ARPU/5G 가입자 | MSIT/통계청 | 무료 clean time-series API 부재 | ❌ data-gate | ★통신 KPI 핵심이나 수동 스크랩 필요 = 미측정(이연 아님) |
| 배당수익률 | DART dart_financials | equity/net_income/assets 만(배당 line 미수집) | ❌ → 금리 duration 직접 | ★배당 직접 부재 → KR10Y 민감도로 duration 대리 |
| regime | refining regime_labels 복사 | 시장공통(FRED CLI/DEXKOUS + ECOS 외국인) | 복사 채택 | ★refining/raw-v3/data/regime_*.parquet 복사 = FRED/ECOS 재호출 절약 |
| equipment PBR/PER | DART equity/net_income + 주식수(현재 근사)×가격 | PBR avgN 9.2 OK, PER avgN 6.3(흑자만) | PBR 채택 | ★PER = 적자 빈발(138/215 흑자) KOSDAQ 소형 = underpowered |

## 막힘·해결 로그 (시계열)
- [2026-06-05 11:35] 막힘: 4시간+ 활동 멈춤(team-lead stuck 감지) → 진단: SSOT 6 + 옛 산출 정독 단계서 도구 호출 간 공백 → 해결: regime parquet 복사 후 재개, theory→측정→robustness→capsule 일괄 진행 → 교훈: ★정독·recon 길어질 때 중간 진행 보고(SendMessage)로 idle 오인 방지.
- [2026-06-05 11:36] 막힘: telecom raw-v3/data 에 regime_*.parquet 부재(common_factors 만 존재) → 진단: 6/3 옛 산출이 regime 미사용(통합 cross-sectional만) → 해결: refining regime 복사(시장공통) → 교훈: ★regime = 시장공통 = 한 산업서 만들면 복사. raw-v3/data 가 표준 위치.
- [2026-06-05 11:40] 막힘: common_factors rate10y = US ^TNX 판명(2020-08 0.56% = US, KR은 1.37%) → 진단: 6/3 collect 가 yfinance ^TNX 사용 → 해결: ★FRED IRLTLT01KRM156N(KR10Y) 별도 수집(배당주 duration = 한국 discount rate 필수) → 교훈: ★rate factor 출처 검증 의무(US vs KR). 배당주 duration = 자국 금리.
- [2026-06-05 11:50] 발견: equipment PBR value 60d IC -0.167 BY 생존(통신 유일) → ★S5 역공격 size confound 점검 → size-neutral IC -0.05(68% 축소) → 진단: 저PBR↔소형 상관 +0.554 = value premium 대부분이 소형주 효과 → 해결: TENTATIVE 격하 + size-neutral 권역 박제 → 교훈: ★G-A A-4 size 분리 의무. 소형 universe value 신호 = size confound 점검 없이 채택 금지(value≠순수).
- [2026-06-05 11:52] 발견: service 금리 duration = 부호 prior(음) 반대(대부분 양) + 전 horizon 비유의 → 진단: 2019-26 = 저금리→인상 single rate cycle = episode-poor + level I(1) spurious → 해결: ★INCONCLUSIVE 박제(deferral 아님, 현 데이터 verdict) + episode 누적 unblock 명시 → 교훈: ★이론 prior(배당주 duration) 강해도 표본서 미확인이면 단정 금지. episode-poor = 부호 불안정 정직 박제(§1.2).
- [2026-06-05 16:20] G-C 보강2: 막힘 — 옛 통합 cross-sectional 분리 근거를 "PBR 부호 cancel(defensive≠cyclical)"로 서술 → 진단: auditor 재현 = pool 14종/장비/service PBR 60d 셋 다 음(-0.16~-0.20) = cancel 없음, 옛 -0.542는 24M overlap horizon artifact(eff_N≈2.5 degenerate)지 cancel 아님 → 해결: ★분리 근거를 "측정축 차이(service 시계열 vs 장비 cross-sectional) + archetype driver 본질차(bond-proxy vs cyclical)"로 정정(yaml/ledger/research-log), 2 archetype 분리 결론은 유지 → 교훈: ★결론 맞아도 mechanism 서술 정밀화 의무(over-framing 차단). cancel 주장 전 양쪽 부호 실측 의무.
- [2026-06-05 16:18] G-C 보강1: 막힘 — size_neutral_ic source_id가 raw JSON 부재(inline bash 실측만, measure_robustness.py에 size 코드 없음) → 진단: 핵심 격하근거(size confound)가 raw 재현 불가 = C 추적성 PARTIAL → 해결: ★measure_robustness.py에 size-neutral 실측코드(B-R4) 추가 + ATK5 → validation-robustness-v3.json `equipment_pbr_size_neutral` 박제(corr 0.5535, raw -0.167→neutral -0.053, shrink 68.5%) → 교훈: ★inline 실측은 raw 코드+JSON에 반드시 박제(추적성 = 핵심 근거 raw 존재 의무).

## 측정 방법 결정 로그
- ★2 archetype 분리(frame §1.6): service(defensive 3사) ≠ equipment(cyclical 10종). ★분리 근거 = 측정축 차이(service 시계열 vs equipment cross-sectional) + archetype driver 본질차(bond-proxy 금리 duration vs cyclical 5G capex). ⛔"PBR 부호 cancel" 아님(셋 다 음 value, G-C 보강2 정정). → service=시계열 / equipment=횡단면 별도.
- service cross-sectional → 시계열 전환: 3사 과점 = Spearman IC 불가(정유 2종 패턴). frame M2(패널 시계열 vs KR금리 duration).
- KR10Y duration 직접 측정: 배당수익률 미수집 → 금리 민감도(level/Δ × forward)로 bond-proxy duration 직접. contemp vs forward 분리(frame §D).
- equipment value size-neutral 의무: 소형 universe value = size confound → raw IC + size-residualized IC 둘 다 보고(§1.6).
- eff-N 보정 + wild-cluster + ADF: small n + overlap → naive t 과대(§1.7). level I(1) spurious 점검.
- 단일 FDR family(m=24): service 시계열 + equipment 횡단면 통합 BY. survivor = eqp_y_60d_pbr_z 1개 = 약신호 정직.

## rotation 측정 로그 (2026-06-06, 업종 OW/UW)
- [2026-06-06] 막힘: 1차 rotation-analyst telecom mom_12_1 +0.284(y_60d) = data-mining? → 진단: strict service 3사(SKT/KT/LGU+) 단독 재현 = +0.063(wc_p=0.53, OOS flip) = 신호 소멸. 1차 broad telecom 패널(service+equipment) = equipment momentum 혼입 → 해결: ★패널구성 artifact 적발(rotation-signals.md §5), mom REJECTED + 패널 정의 strict 화이트리스트 의무 박제 → 교훈: ★1차 rotation 신호 = 패널 정의 검증 의무(broad vs strict). momentum은 equipment cyclical 혼입 = service defensive 본질 아님.
- [2026-06-06] 발견: rotation theory-backed tradeable 2개 = 외국인 flow -0.396(well-powered t_pow 3.58, OOS hold, leave-episode 불변) + semi_ppi -0.261(OOS hold, moderate) → 진단: 둘 다 ★defensive counter-cyclical 이론 정합(risk-on→통신 UW) → 해결: PASS-conditional 채택. carry tilt(자문 수렴)보다 counter-cyclical defensive가 데이터 본질 → 교훈: ★통신 rotation = risk-on/off defensive rotation. flow=전산업 공통(L축 1회계상 주의).
- [2026-06-06] 함정: cli_chg +0.433(BY 생존) + usdkrw_yoy -0.305 = ★부호 prior 위배 → 진단: cli_chg는 risk-on 지표(semi/flow)와 음상관(-0.31)이라 defensive 정합 가능하나 사전확약(음) 위배 → 해결: ★exploratory(채택보류) = HARKing 회피(사후 부호 합리화 금지) → 교훈: BY 생존이어도 prior 위배 = 채택 불가(사전확약 sacrosanct).

## 미해결 / 다음 세션 우선 작업
1. ★ARPU/5G 가입자 월별 time-series 확보(MSIT/통계청 스크랩) — service fundamental + rotation data-gate, collector high
2. ★배당수익률 직접 수집(DART 현금배당) — 배당주 duration 정밀화(금리 대리보다 직접), collector high
3. equipment PBR value size-neutral 추적 — 순수 value vs 소형주 효과 결정(live IC → 0 수렴 여부)
4. service 배당주 duration = 추가 rate cycle(금리 하락기) 누적 후 재측정 — episode-poor 해소
5. ★rotation semi_ppi = leave-episode 약화 → episode 누적 후 strong 승격 여부 재평가
6. G-G 최종판정: service 종목selection 0 + rotation tradeable 2(flow+semi_ppi) + equipment value conservative cap = supervisor 확정 대기
