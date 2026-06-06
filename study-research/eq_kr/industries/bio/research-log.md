---
tags: [type/research-log, domain/equity, sector/bio]
date: 2026-06-05
purpose: bio 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용. append-only.
---

# bio(제약·바이오) 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격 패널 | pykrx OHLCV 개별종목 | ✅ 38종 floor-pass(2019-2026, 1818일) | ✅ prices.parquet | pykrx 시장 스냅샷 API 차단(반도체 동일) → 개별 OHLCV loop 작동 |
| universe | KrxSectorProvider + floor(Mcap∧ADV) | ✅ 185종 → floor 38종(pharma27/novel6/biosimilar5) | ✅ universe.parquet | ★floor 38종 ≥8 = cross-sectional 가능(시계열 전환 불필요) |
| 재무 PIT (PER/PBR) | DART fnlttSinglAcntAll | ✅ 948 rows(2019~) | ✅ dart_financials.parquet | ★net_income 적자 26/38종 = event_driven. PER = 흑자(ni>0) 한정 계산(적자 신약 제외) |
| Macro regime | FRED KORLOLITOAASTSAM (CLI amplitude-adj) | ✅ 월별 2026-04 | ✅ regime_labels.parquet | ★반도체 collect_regime.py 재사용(종목 독립). normalized 버전 중단 → amplitude-adj 대체 |
| KRW regime | FRED DEXKOUS (USDKRW) | ✅ 일별 | ✅ | yoy ±5% 3구간 |
| 외국인flow regime | ECOS 802Y001/0030000 일별 | ✅ 2003~2026 | ✅ | ★bio 핵심 증폭축으로 판명. KRX 종목별 차단 → ECOS 시장레벨 일별 |
| common factors (VIX등) | yfinance | ✅ (기존 6/3) | ✅ common_factors.parquet | ★VIX β=+0.011 t=6.03 = bio 고베타 성장주(산업 risk factor 분기) |
| 임상/파이프라인 | KFDA/clinicaltrials.gov | ❌ monthly facet 부재(yearly만) | ⏳ DATA-GATE | ★bio event_driven primary인데 미측정 = collector_plan high |
| PIT universe 멤버십 | FDR/KRX delisted | ❌ 현 스냅샷만 | ⏳ collector_plan high(최우선) | ★bio 생존편향 최악 |

## 막힘·해결 로그 (시계열)

- [2026-06-05 11:28] 막힘: bio capsule 진입 시 6/3 v3 선행 산출 발견(unconditional cross-sectional IC + summary.yaml + 15axis). dispatch role = "방향부터 재정독, 축만 달기 아님". → 진단: 선행 = unconditional(vol_60 저변동성 + per_z 흑자한정 = event_driven 입증)까지, ★conditional IC surface(dispatch 본체) + OOS + ledger 2종 전부 누락. → 해결: 반도체 검증양식(summary/ledger/15axis) 정독 후 누락분 측정. 교훈: 진입 시 기존 산출 신뢰성 점검 + dispatch 본체 축(conditional)이 있는지 확인 1순위.
- [2026-06-05 11:30] universe 충분성 점검: floor 38종(≥8) = cross-sectional 가능. net_income 적자 26/38종 = event_driven 확정. → 시계열 전환(frame M2) 불필요. 교훈: 측정 전 universe floor 통과 수 + 적자 비율 먼저 확인.
- [2026-06-05 11:35] regime 데이터 수집: 반도체 collect_regime.py 그대로 재사용(FRED+ECOS, 종목 독립). 36셀 N≥24=0(실측, 최대 N=15) → 단일축 regime + family_2 interaction 전략(반도체 동형). 교훈: regime 설계 = 셀 N 먼저 측정 후 collapse 전략 확정.
- [2026-06-05 11:36] ★막힘: measure_conditional.py 복사 직후 Read 없이 Edit 시도 → harness "File has not been read" 에러. → 진단: 복사한 파일은 Edit 전 Read 의무(harness 제약). → 해결: Read 1줄 후 Edit. 교훈: cp 직후 Edit 금지, Read 선행. (4시간 멈춤 원인 = 이 지점에서 turn 종료)
- [2026-06-05 15:30] ★conditional IC surface 측정(measure_conditional.py, G-F 7항 헤더). 6신호 × horizon(y_5d/20d/60d) × regime 단일축. per-cell wild-cluster bootstrap p + n_eff + block-boot CI.
  - ★발견1: **unconditional 약** — vol_60(IC -0.066 wc_p=0.012)·rev_1m(-0.047 wc_p=0.025) 만 유의, momentum/valuation 비유의.
  - ★발견2: **flow_sell(외국인 순매도) = 증폭축** — 전 신호 flow_sell 국면서 강하게 음(mom_6 -0.149/mom_12_1 -0.134/per_z -0.092/vol_60 -0.093). 단 n=18~20 underpowered.
  - ★발견3: **KRW_weak interaction 비유의** = 반도체(KRW_weak 증폭축)와 대조. → bio 증폭축 = flow 로 재판단.
- [2026-06-05 15:40] ★interaction dummy 재설정: sign-flip 이 flow_regime 에 집중 → measure_conditional.py 수정(flow_sell 을 primary dummy, KRW_weak 보존 측정, all_sigs 사용=vol_60/per_z 포함). 재측정 결과: **mom_6 t_inter=-2.90/mom_12_1 t_inter=-2.92/per_z t_inter=-2.29 유의** = flow_sell 국면 신호 효과 갈림(frame A-5). 교훈: interaction dummy = sign-flip 분포 보고 산업별로 결정(반도체 KRW vs bio flow).
- [2026-06-05 16:00] ★walk-forward OOS + S5 역공격(measure_oos.py, team-lead 지시 = 현 데이터 verdict 확정). IS(2019-22)/OOS(2023-26):
  - ★unconditional OOS 붕괴: vol_60/rev_1m 부호유지하나 magnitude 약화(-0.119→-0.008), mom_6/pbr_z/per_z **OOS 부호반전(artifact)**. = unconditional 가격/valuation 은 in-sample artifact.
  - ★flow_sell conditional OOS 생존: 5신호 전부 부호+magnitude 유지(mom_6 -0.141→-0.156, vol_60 -0.042→-0.135). interaction t OOS 강화(mom_6 IS -1.26→OOS -2.95, vol_60 IS +1.21→OOS -3.06).
  - ★S5 역공격 3종 방어: (a) flow_sell 8개해 분산(단일 episode 아님) (b) VIX 21.9≈20.1(risk-off 대리 아님) (c) leave-2021-out mom_6 t=-2.94 생존(rev_1m/vol_60 약화).
  - ★정직 hedge: IS t 약→OOS t 강 = "지속 신호"가 아니라 "최근(2023+) regime shift 발현" 가능성 = magnitude tentative. cell n<24 underpowered.
  - 교훈: unconditional vs conditional 의 OOS 거동이 정반대(unconditional artifact / conditional 생존) = "동적가중" 정당화 핵심 데이터. ★단 conditional 도 IS약→OOS강이면 regime shift hedge 의무.
- [2026-06-05 16:30] ★생존편향(I축) 정량 점검: 현 universe = FDR 2026-05 스냅샷. prices 거래 끊긴 종목 0종 = ★delisted 완전 누락. 신규상장 7종(2020+)=look-back gap. → ★bio 최악: 임상실패 상폐(코오롱티슈진 인보사·신라젠·헬릭스미스 등)가 누락 = 대부분 고변동성 신약 → vol_60(고변동성 회피) 신호 과대평가 우려. 교훈: bio 생존편향 = 단순 PARTIAL 라벨 아니라 "어느 신호가 어느 방향으로 편의되나"(vol 과대) 명시.
- [2026-06-05 G-C audit 후] ★★거래정지 좀비 carry-forward 누설(bio-audit 발견, D축 remediation). 막힘: G-C 독립 audit이 D축 누설 발견 — 초안 measure 가 거래정지 종목 직전종가 flat carry 를 그대로 사용 → 거래정지 월말 forward 20d = +0.0000(가격 안 변함)으로 IC 오염 + vol_60(저변동성) 인위적 오측정. 정량: 코오롱티슈진(950160) 인보사 사태(2019-06 -80%) 후 841일 연속 16050 flat carry = 47.8% / 케어젠(214370) 277일 19%. → 진단: KRX 가 거래정지 종목을 직전종가 carry 하는데 이를 "정상 가격"으로 취급 = reject(거래없음)를 valid 로 오인(reject≠missing 위반). → 해결: `mask_trading_halt(min_run=10)` = 연속 동일종가 ≥10거래일 run = 거래정지 판정 → NaN. measure_conditional.py + measure_oos.py 양쪽 load() 적용. 마스킹 1163셀(950160 842일+214370 289일, 정상종목 유한양행 0일/동국제약 14일 = over-mask 없음). → ★재측정 = **핵심 결론 robust 불변**(team-lead 예측 정확): flow_sell interaction mom_6 t=-2.90→-2.85/mom_12_1 -2.92→-2.83/per_z -2.29→-2.27 유의 유지 + flow_sell OOS 5신호 부호유지 불변 + vol_60 uncond -0.066→-0.069 안정(저변동성=좀비 artifact 아님) + S5 leave-2021 t=-2.93 생존. → ★D=PASS "거래정지 처리" 박제 미흡 = D PARTIAL 격하 후 재측정 PASS. 교훈: ★한국 주식 = 거래정지 carry-forward 가 IC/vol 오염원(bio 임상사태·관리종목 잦음). 연속 flat run 탐지 NaN 마스킹 = reject≠missing 필수. 8 PASS 종목군(조선/철강 적자빈발)도 통합 시 점검(team-lead 박제).
- [2026-06-06] ★bio 업종 ROTATION 신호 측정 (v2 data-gate 재검, team-lead 지시). v2 rotation-analyst = bio NO_DIRECT_CYCLE + momentum OOS flip = FAIL/data-gate. → 진단: v2 가 momentum 만 측정, ★거시 overlay(금리 duration/글로벌바이오 ETF 상대) 미측정 = 핵심 누락. bio = growth/long-duration 이론상 금리 민감인데 v2 가 안 봄. → 해결: 거시 overlay 10개 후보 측정(measure_rotation.py). 데이터 = common_factors(rate10y/VIX/credit) + regime_series(usdkrw) + ★신규 fetch XBI/IBB/NDX/SPY(global_bio_etfs.parquet) + KR 10Y(IRLTLT01KRM156N, kr_rates.parquet) + macro_daily(us_10y/us_2y) + FDA csv. ★좀비 마스킹(89개월 패널). → ★결과: 이론 부호 일치 8/10 + OOS 부호유지 다수 = data-mining 아님. us_10y_d y_60d rho=-0.244 wc_p=0.028(growth duration 입증) + xbi_rel_mom/ibb_rel_mom 양(글로벌바이오 전이). composite(measure_rotation_composite.py): rate_overlay y_60d +0.274 wc_p=0.018 + full_overlay y_20d +0.180 OOS elig. leave-2022 부호유지(단일 episode 아님). → ★판정 = PASS-conditional(tradeable 2 = 금리 duration + 글로벌바이오 상대), v2 FAIL 뒤집음. 단 underpowered + IS약→OOS강(regime shift) = monitor/macro overlay. 교훈: ★rotation = momentum 만 보면 안 됨. 산업 archetype 이론(bio=growth duration)에서 1차 driver(금리/글로벌섹터) 도출 후 측정 = v2 누락 보완. ★stdout 함정 = measure_rotation import 시 stdout 재래핑 → composite 에서 중복 래핑하면 buffer 닫힘(I/O closed). import 후 재래핑 금지.

## 측정 방법 결정 로그

- **conditional IC (신규)**: plan §2 + frame §M3 = 36셀(Macro4×KRW3×flow3). 36셀 full N≥24=0 → 단일축 regime별 IC + family_2 interaction. 부호 사전확약(theory §6, HARKing 방지) 후 대조.
- **bio 증폭축 = flow_sell (반도체 KRW_weak 과 대조)**: sign-flip 분포가 flow_regime 집중 + interaction t<-2.3(flow_sell) vs 비유의(KRW_weak). bio 고베타 성장주 → 외국인 risk-off 매도 국면이 증폭축(이론 §6.2 정합).
- **unconditional vs conditional 분리 보고**: unconditional OOS artifact(부호반전) ≠ conditional OOS 생존. = "약함" 단정 회피(frame A-5/G-B). conditional 채택 + unconditional 격하.
- **per_z 흑자 한정**: `if net_income>0` 만 PER 계산(적자 26/38 제외). event_driven = 멀티플 부적합.
- **G-F 7항 헤더**: measure_conditional.py 선언. wild-cluster bootstrap(small-block size-invalid 회피).
- **생존편향 방향성 명시**: 단순 PARTIAL 아니라 "상폐된 고변동성 임상실패 신약 누락 → vol 신호 과대평가" 메커니즘 박제(team-lead 강조 I축 정직).

## 미해결 / 다음 세션 우선 작업

1. ★파이프라인/임상 단계 데이터(event_driven primary) — KFDA/clinicaltrials.gov monthly. 현 측정 = 변동성 proxy 까지.
2. ★PIT universe 멤버십(delisted 포함) — bio 생존편향 최악, 최우선. delisted 포함 시 vol 신호 재평가(약화 예상).
3. conditional(flow_sell) 차기 vintage pristine OOS — IS약→OOS강이 regime shift 인지 지속 신호인지 판별.
4. 종목레벨 외국인 flow(KRX 차단) — flow_sell 증폭이 종목레벨이면 더 정밀.
5. M_eff 통합 FDR 보정(supervisor) — naive m=105 과대(pbr/per·mom 강상관).
6. R&D 비용/매출(적자 burn-rate) DART 추가 — event_driven 보조 신호.
