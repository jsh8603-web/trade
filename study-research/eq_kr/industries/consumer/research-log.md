---
tags: [type/research-log, domain/equity, sector/consumer]
date: 2026-06-05
purpose: 소비재 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# consumer(소비재) 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격 (28종 OHLCV) | pykrx | prices/amount.parquet 1818일×28종 (2019~2026-05) | ✅ | universe pass_floor=True 28종 (시총·거래대금 floor). ★분류노이즈 잔존(코웨이/큐렉소 오분류) |
| 재무 (PBR/PER) | DART fnlttSinglAcntAll | dart_financials.parquet 707 rows (2019~2026-03) | ✅ | ★표준계정 2019~ 완전(financial 2023~ 제약 대조). rcept_dt = mediator.compute_delay (보고지연 median ~85일). 음수 equity/net_income 처리(eq>0/ni>0 조건) |
| regime (Macro/KRW/flow) | FRED CLI+DEXKOUS + ECOS 외국인 | ★반도체 collect_regime.py 재사용 (산업무관 KOSPI 전체) → regime_labels.parquet 101 months | ✅ | CLI_PUB_LAG=2 (OECD vintage). 36셀 N>=24 = 0 cell → 단일축+2축merge. semi_ppi 컬럼=미사용(무해) |
| common factor | yfinance (VIX/dollar/oil/rate) + FRED credit | common_factors.parquet 1898행 | ✅ | credit = US HY OAS proxy (KR HY 부재) n=35 tentative |
| 종목별 외국인 flow | KRX | ★login 차단 = DATA-GATE | ❌ proxy | theory §5 H5 INSUFFICIENT. regime KOSPI 전체 flow(ECOS)로 대체. ⛔deferral 아닌 data-gate |
| K-food 수출/소매판매/CCSI | 관세청·통계청·ECOS | 미수집(macro 시계열) | ⏳ 이연 | cross-sectional 종목선택 아닌 산업평균 driver = forward IC 약 prior. KRW regime 으로 부분 흡수 |

## 막힘·해결 로그 (시계열)

- [2026-06-03] 6/3 1차 산출(v3): unconditional valuation(per_z value premium) + cross(dollar β -2.57) + momentum 무신호
  까지 완료. ★but S2 conditional IC 36셀 / A-4 sub-sector / walk-forward OOS / ledger 2종 / G-G v2 누락 → 미완.
- [2026-06-05 진입] 막힘: cwd 리셋 환경(PowerShell 셸 상태 비유지) → 상대경로 parquet 로드 실패.
  → 진단: Bash tool 매 호출 cwd 리셋. → 해결: **절대경로 강제**(data/ → D:/projects/Inv/.../data/). 교훈 = teammate
  thread cwd 비유지 = 모든 .py 경로 절대화.
- [2026-06-05] regime 재사용: 반도체 collect_regime.py 그대로 복사 실행 → FRED/ECOS 실데이터 fetch 성공
  (CLI 100 / USDKRW 2100 / ECOS 외국인 2065). 산업무관 KOSPI 전체 regime = 12산업 공통 재사용 자산.
- [2026-06-05] ★A-4 발견: subsector_sign_check 측정 → **전 6 신호 부호 CANCEL 검출**. per_z 화장품 -0.258 vs
  음식료 -0.019 vs 유통 +0.035 = financial XLF cancel 교훈 실증. → 화장품 per_z deep-dive: horizon/OOS/leave-episode
  robustness 측정 → leave-episode 비유의(single-episode 의존) = TENTATIVE DIRECTIONAL 격하(over-claim 회피).
- [2026-06-05] FDR family BY survivors=0 (m=105). ★[audit 정정] G-G v2 well-powered cell = **5개**(초기 "0개" 서술 오류).
  → G-B 판정: family_2 interaction rev_1m KRW_weak t=-2.36 **살아있음** = "신호 약함" 단정 불가(conditional 본질). 재자문 미발동.
- [2026-06-05 G-C audit PASS + 정정 4건] audit 충실 PASS(hard-fail 0, A-4 cancel 독립재현). non-blocking 정정 4 반영:
  (1) ★well_powered_cells "0"→**5개** (vol_60 KRW_neutral t-3.46 / per_z Slowdown t+3.40 / vol_60 Recovery t-3.24 /
      rev_1m Slowdown t+2.89 / pbr_z flow_neutral t-2.89, 전부 wc_p<0.01). 코드 플래그는 정확, yaml/15axis 서술 "0"이 오류
      → "5개 존재하나 105 multiplicity 단일 BY 못넘음(전부 underpowered 아님)" 정정.
  (2) rev_1m caveat "episode<3" 부정확 → KRW_weak 38개월·12 episode 재측정 → "overfit 우려 완화" 정정.
  (3) ★measure_cross.py battery 잔재(load_battery_index/lithium) → load_consumer_index + 곡물 upstream(ZC/ZW/ZS) 정정.
      ★dollar β -1.19 재현 동일(함수명만 battery, 산출=consumer prices). 곡물 null(전 lag p>0.12) = §D falsifier 정상 = skip.
  (4) 화장품 universe 확장 권고 구체화(코스맥스엔비티/콜마비앤에이치/애경산업/클리오 n_codes 4→7+).
  verdict(PARTIAL) 유지. 교훈 = self 측정 통계는 정확하나 yaml 서술 라벨("0")·코드 잔재(battery fork)가 정정 대상 = latch.

## 측정 방법 결정 로그

- **conditional IC**: 반도체 measure_conditional.py 양식 미러(G-F 7항 헤더 + wild-cluster bootstrap + n_eff + block-boot CI).
  소비재 특수 3종 추가 = (a) subsector_sign_check (A-4 부호 cancel, 소비재 핵심) (b) walk_forward_oos (IS2019-22/OOS2023-26)
  (c) G-G v2 t_obs_eff = IC·√n_eff/σ ⋚ 2.802 (eligibility/power).
- **A-4 sub-sector**: universe `subcl` 컬럼(food9/cosmetics4/retail10/apparel3/beverage2) 기반 sub-cluster별 횡단면 IC.
  n_codes<3 = INSUFFICIENT(beverage 2). ★화장품(中cyclical) vs 음식료(defensive) 부호 갈림이 측정 본질 = sub-sleeve 분리 판정.
- **small-n haircut (§M.12)**: 화장품 n_codes=4 = 횡단면 spearman 협소 artifact → magnitude 50-70% haircut + leave-episode
  의무. 점추정 박제 금지. verdict = TENTATIVE DIRECTIONAL(방향만 신뢰, magnitude 보수).
- **per-test calibration**: small cell block 한자릿수 → asymptotic NW-HAC t = size-invalid → wild-cluster bootstrap
  (Rademacher B=2000) per-cell p. asymptotic t = 참고만.
- **FDR**: 단일 family(BY) 측정前 멤버십 사전고정(6신호×3h×powered cell). M_eff 통합 supervisor 단계. garden-of-forking-paths 차단.

## 미해결 / 다음 세션 우선 작업

1. ★화장품 sub-sleeve 분리 검증: universe 확장(중소형 화장품 추가 n_codes≥8) + 中소비 regime(면세/따이공) 분리.
   현 n_codes=4 leave-episode 비유의 = single-episode 의존 → universe 충분성 확보가 promotion 전제.
2. K-food 수출 yoy 산업평균 forward lag-corr (이연 → 통합단계). 음식료 sub-cluster cost pass-through(곡물 ZC=F).
3. size-orthogonal per_z (화장품 small-cap value 위장 점검, §M.12 누락축). 통합 register.
4. PIT universe 멤버십 (delisted/M&A) — 소비재 상폐 적으나 잔존. collector_plan high.
5. 분류 화이트리스트 정밀화: 코웨이/큐렉소/실리콘투 오분류 정정 (§M.11). 현 결론 영향 없으나 통합 전 정정.
