# validation-v3-cross-sectional.md — semiconductor §M v3 재산출 (cross-sectional)

> frame v3 §M.1~M.7 측정. raw 재현: `raw-v3/{collect, measure, measure_cross, exposure_card, collect_dart, measure_valuation}.py`.
> v2(`round-1.md` 이론 + 가설 8) = 3+1종목 시계열 lag-corr 가설. 본 v3 = **85종목 횡단면**.
> ★battery pilot 미러 산출. 핵심 발견 = **반도체 momentum forward IC 부호 = 음(contrarian)** = battery(양)와 반대.

## §0. 데이터 제약 + 해소

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV 개별종목 loop | ✅ 작동 | 85종 가격 패널 (2019-2026, 1818일) |
| pykrx **시장 스냅샷** (get_market_cap / get_market_fundamental / sector_classifications) | ❌ KRX 인증 차단 (빈 응답) | PBR/PER/시총 횡단면 스냅샷 실측 불가 → **DART 재구성으로 우회 해소(§10)** |
| **DART fnlttSinglAcntAll** (자본총계/순이익/자산 + rcept_dt) | ✅ 작동 | ★valuation 횡단면 PIT 재구성. PBR/PER cross-sectional z |
| FDR KRX-DESC (Sector/Industry/Products) | ✅ 작동 | universe 멤버십 (현재 스냅샷 = PIT 아님) |
| FDR KOSPI/KOSDAQ listing (Marcap/Amount) | ✅ 작동 | 시총·ADV floor + 현재 주식수(시총 역산) |
| yfinance (SOXX/NVDA/VIX/factors) | ✅ 작동 | cross 공통인자 + leading cycle momentum + G1 regime |

★pykrx 스냅샷 차단을 DART 종목당 재무 fetch + PIT(rcept_dt) 재구성으로 우회(battery 와 동일 경로). 잔여 = 시점별 주식수 정밀화 + EV-EBITDA = collector_plan.

## §1. universe 확장 (§M.6)

- FDR 섹터/산업/제품 키워드(`반도체|메모리|DRAM|파운드리|웨이퍼|장비|소재|후공정|패키징|식각|증착` 등) 매칭 = **189종**.
- 시총 floor(≥3000억) ∧ ADV floor(≥30억) = **85종** 통과.
- ★기존 round-1 = 3+1종(삼성전자/SK하이닉스/한미반도체/DB하이텍) 정적. v3 = 85종 → **cross-sectional IC 평균 종목수 ~73** = battery(26) 대비 약 3배 breadth, 횡단면 통계력 강.
- ★sub-cluster 혼재: 메모리(005930/000660/009150) + 파운드리(000990 DB하이텍/108320 LX세미콘) + 소부장(한미반도체/리노공업/원익IPS/솔브레인/동진쎄미켐 등 다수 KOSDAQ). **KOSPI 대형주(삼성+SK) 시총 50%+ 집중** → cap-weighted IC 로 microcap 지배 점검 의무 (§4).
- ⚠️ 키워드 매칭 잔여 오염: 천보(2차전지 전해질)·HD현대에너지솔루션(태양광) 등 일부 인접산업 → battery 와 동일 키워드 매칭 기준 유지(supervisor 통합 시 재분류 여지).

## §2. forward 횡단면 Rank-IC (horizon-tagged, §M.2)

4 신호 (mom_6 / mom_12_1 / rev_1m / vol_60, 전부 cross-sectional z-score) × 4 horizon (1M PEAD / 3M / 6M / 12M) = 16 테스트.

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV OOS hit | avg_N |
|---|---|---|---|---|---|---|
| **mom_12_1 → 12M** | **-0.068** | **-2.75** | 65 | 0.008 | 0.87 | 72.0 |
| **mom_6 → 12M** | **-0.065** | **-2.90** | 71 | 0.005 | **1.00** | 72.8 |
| mom_12_1 → 6M | -0.061 | -2.03 | 71 | 0.047 | 0.93 | 72.8 |
| vol_60 → 3M | -0.061 | -2.11 | 83 | 0.038 | 0.80 | 74.3 |
| rev_1m → 1M_PEAD | -0.043 | -2.86 | 87 | 0.005 | 1.00 | 74.8 |
| vol_60 → 1M_PEAD | -0.045 | -2.27 | 85 | 0.026 | 0.87 | 74.5 |

★**핵심 발견 = momentum forward IC 부호 전부 음(-)**:
- battery 는 cs_mom_6m → 12M = **+0.086**(모멘텀). 반도체는 **-0.065**(장기 reversal/contrarian).
- 해석: 반도체 = 강 cyclical 산업 → "많이 오른 종목이 다음 12M 되돌림"(peak reversal). **cyclical archetype 정합** (§9).
- horizon 구조 = 12M·6M 모멘텀 음(reversal 본진) + 1M reversal 음(단기 reversal). 절댓값 12M(0.065-0.068)>6M(0.051-0.061)>3M(0.034) = reversal 도 horizon 단조.

## §3. 4게이트 (§M.2)

**primary = mom_6 → 12M_mom** (CPCV hit 1.00 로 mom_12_1 보다 robust):
- **G1 ex-ante**: SOXX yoy regime (bull 49 / neutral 34 / bear 6 month) = 진입시점 반도체 ETF yoy 관측가능. 달력컷 아님. (battery 의 LIT yoy 대응 — 반도체 글로벌 cycle proxy.)
- **G2 다중검정 (FDR/BY)**: 16 테스트, Benjamini-Yekutieli (BY factor=3.381). raw_p_min=0.00498(mom_6__12M). **BY rank1 threshold=0.00185 → 생존 0**. Bonferroni α/16=0.00313 → 0.00498 > 0.00313 = **미생존**. ★battery 와 결정적 차이(battery raw_p=0.00024 BY 생존). = 효과 절반 + 보정 후 비유의.
- **G3 walk-forward CPCV purge+embargo**: 6 splits, n_test=2 → 15 fold. purge=12M, embargo=1. **OOS hit=1.00** (전 fold 부호 일관), OOS IC = full-sample 무붕괴.
- **G4 Newey-West HAC**: lag=horizon=12. se_nw 보정, t_nw=-2.90. NW CI [-0.109, -0.021] 0 비포함.

block-bootstrap (block=3M, B=2000): CI [-0.106, -0.028] = NW 와 정합 (둘 다 0 배제).

★**게이트 종합**: CI(NW+boot) 0 배제 + CPCV 1.00 + within 100%(§4) = 방향 robust. **단 multiple-testing(BY/Bonferroni) 미생존** = small-n rule hedge 의무 → verdict = **PARTIAL CONFIRMED** (battery momentum CONFIRMED 보다 한 단계 낮음).

## §4. robustness (§M.1, §M.3)

- **leave-episode**: 최강 12M 윈도 제외 → ex-peak IC -0.087 (full -0.065), 부호·magnitude 생존(오히려 강화) = single-episode artifact 아님.
- **within-period**: 연도별 IC 부호 일관 **100%** (2019:-0.138 / 2020:-0.010 / 2021:-0.006 / 2022:-0.127 / 2023:-0.011 / 2024:-0.135 / 2025:-0.067). 전 연도 음.
- **유동성-티어 IC (§M.1 ⑱)**: hi-ADV -0.021 / lo-ADV -0.040 / **cap-weighted -0.092**. ★cap-weighted 가 동일가중보다 강함(절댓값 0.092 > 0.065) = 대형주(삼성/SK)에서 reversal 더 강 = microcap 아티팩트 아님(투자가능성 확인, battery 와 반대 패턴이나 robust 동일).
- **e-process (§M.1 ⑪)**: score_ic_breakdown_eprocess(baseline=0.5×|IC|) reject=True(detector overflow) = 강신호라 baseline 위 안정. live 모니터·placebo 용도.

## §5. cross 축 (§M.3 — 산업=보고만)

### (a) 공통인자 β (contemporaneous, HAC maxlags=3, n=35 month)
- **credit (US HY OAS proxy)**: β=-0.190, t=-3.36, CI [-0.300, -0.079] = 유의. credit risk-off → 반도체 약세 (battery -0.164 보다 강함).
- dollar: β=-1.68, t=-1.26 = 비유의(CI 넓음, 약한 음 방향성 — 수출주 환율 노출 가설 H1 약).
- oil: β=+0.15, t=+1.15 = 비유의. VIX/rate = 비유의. R²=0.212.
- ⚠️ credit = US proxy (KR HY spread 부재), n=35 = small-n → hedge: tentative directional.

### (b) customer-supplier momentum (alpha 후보, §M.3)
- 글로벌 반도체 cycle(SOXX) / AI 수요(NVDA) 3M lagged momentum → 한국 반도체 forward 1M:

| lag | SOXX corr (p) | NVDA corr (p) |
|---|---|---|
| 0 | +0.042 (0.71) | -0.010 (0.93) |
| 1 | +0.031 (0.78) | +0.016 (0.89) |
| 2 | -0.014 (0.90) | -0.110 (0.32) |
| 3 | +0.009 (0.94) | -0.078 (0.48) |

→ **REJECTED as alpha**: 전 lag 비유의. forward 예측력 부재 (§D forward-alpha falsifier 작동, null result 정직 기록). ★해석: 한국 반도체 = 글로벌 cycle 과 contemporaneous 동조(round-1 H4 SMH/SOXX corr>0.7 가설)이지 **forward 예측은 없음**. 동조 성분은 통합 RegimeGlasso Ω 흡수(이중 라우팅 회피). battery(lithium upstream null)와 동일하게 customer momentum skip.

## §6. PIT-fundamentals safety (§M.1 ⑯)

DART 사업보고서(A001) 제출일 rcept_dt vs fiscal year-end(12-31) gap = 보고지연:

| 연도 | n | median delay(일) | max(일) |
|---|---|---|---|
| 2021 | 9 | 120 | 120 |
| 2022 | 23 | 108 | 119 |
| 2023 | 20 | 114 | 118 |
| 2024 | 8 | 120 | 120 |
| 2025 | 3 | 120 | 120 |

→ 사업보고서 median delay **~108-120일** (FY-end 후). 펀더멘털 신호는 rcept_dt 이후만 사용 의무. **본 v3 가격신호는 PIT-safe** (forward shift, 보고지연 무관).

## §7. cross-sectional exposure card (§M.7)

universe 84종 현 시점(2026-05-31) peer-relative z-score (sector-neutral, R2-1 own-history gap 메움). 상위 (mom_6_z):

| ticker | name | mom_6_z | mom_12_1_z | vol_60_z |
|---|---|---|---|---|
| 009150 | 삼성전기 | +5.02 | +2.54 | -0.47 |
| 017900 | 광전자 | +2.90 | +1.54 | +4.50 |
| 080220 | 제주반도체 | +2.44 | +0.60 | +0.96 |
| 000660 | SK하이닉스 | +1.82 | +2.18 | -0.63 |
| 440110 | 파두 | +1.55 | +3.08 | +0.26 |
| 005930 | 삼성전자 | +0.84 | +0.55 | -1.21 |

★**signal 부호 주의** (exposure card 핵심): 반도체 momentum forward IC = **음** → mom_6_z **상위** 종목이 forward **약**(reversal). selection 시 supervisor 가 IC 부호 반영 = **저 mom_z(많이 안 오른) 종목 overweight**. 전체 = `raw-v3/exposure-card-v3.json`. ⛔ score→target weight·cap·Σ_signal mixing = supervisor 조립(dispatch 밖).

## §8. net-cost (§M.4)

KR 비대칭: 매수(spread/2+comm) + 매도(spread/2+comm+STT 0.20%) = 왕복 **33bps**. turnover 0.5/월 → 월 16.5bps. ⚠️ momentum |IC| 0.065(breadth 73종 IR 누적) > 16.5bps 이나 battery(0.086) 대비 마진 좁음 + reversal turnover 높을 수 있음 → net 보존 marginal. sqrt impact·size-tier = supervisor CPCV 캘리브레이션.

## §10. ★valuation 횡단면 (§M.7 핵심 — DART 재구성)

> 측정 완료 (2026-06-04): DART fnlttSinglAcntAll 재무 수집 = **dart_financials 2038 rows / 85종** (CFS→OFS fallback = 소부장 OFS-only 종목 포함, 가온칩스 등). PBR panel coverage 6231 cells / PER 4866 cells. 양식·PIT 처리 = battery §10 미러.

**PIT 엄수**: 각 재무 = `rcept_dt`(공시일) 이후 시점에만 적용(forward-fill from publication) = lookahead·restatement 회피. 시총 = Close × 현재주식수(시점별 주식수 정밀화 = collector_plan).

★**반도체 cyclical valuation 경계** (§M.3 산업메타): 사이클 **정점**에 EPS 高→PER 低(싸 보임=value trap), 사이클 **저점**에 EPS 低/적자→PER 高·무의미. → PER value premium 부호가 battery 보다 불안정/반전 위험. primary_metric=ev_ebitda(peak-EPS 경계) 이나 EV-EBITDA 는 부채/현금 계정 추가 = collector_plan. 본 측정 = PBR/PER cross-sectional 우선.

### ★측정 결과 (DART PIT 재구성, 8 signal×horizon)

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV | within | avgN | BY |
|---|---|---|---|---|---|---|---|---|
| **pbr_z__24M_value** | **-0.1142** | -4.23 | 61 | 0.000 | 1.00 | 1.00 | 69.5 | ★**생존** |
| pbr_z__12M | -0.0679 | -1.78 | 73 | 0.079 | 0.80 | 0.71 | 71.6 | 미생존 |
| pbr_z__3M | -0.0565 | -2.17 | 82 | 0.033 | 0.93 | 0.88 | 72.9 | 미생존 |
| per_z__24M_value | -0.0464 | -1.13 | 61 | 0.265 | 0.80 | 0.67 | 57.9 | 미생존 |
| pbr_z__6M | -0.0457 | -1.46 | 79 | 0.149 | 0.80 | 0.71 | 72.5 | 미생존 |
| per_z__12M | -0.0386 | -1.66 | 73 | 0.102 | 0.67 | 0.71 | 57.0 | 미생존 |
| per_z__3M | -0.0315 | -1.26 | 82 | 0.210 | 0.80 | 0.75 | 57.0 | 미생존 |
| per_z__6M | -0.0240 | -0.96 | 79 | 0.339 | 0.80 | 0.71 | 57.0 | 미생존 |

> BY: m=8, factor 2.718, raw_p_min=0.0001 (pbr_z__24M_value), **survivors = [pbr_z__24M_value]** (유일).

- ★**PBR value premium 작동** = `pbr_z__24M_value` IC **-0.114** (block-boot CI [-0.152,-0.073] 0배제, NW CI [-0.167,-0.061], CPCV oos_hit 1.00 purge24M, within-period 100% = 2019-2024 전 연도 음, BY 유일 생존). 저 PBR(낮은 z) → 高 forward = value premium. ★**small-n hedge**: n=61 month, 24M overlapping → NW HAC + block-boot. magnitude 보수 cap(점추정 단정 회피).
- ★**PER 전 horizon 무신호** = peak-EPS trap 실증. per_z 3/6/12/24M 모두 IC -0.024~-0.046, **p_NW>0.10 전부 비유의**. 사이클 정점 EPS 高→PER 低 왜곡 → PER cross-sectional 예측력 소멸. = **`core/structure/archetype.py` cyclical 정의(primary=P/B, trap=peak-EPS) 실데이터 입증** (auto 동형 — auto 도 PER IC≈0 + PBR value).
- **PBR vs PER 대조** = ★cyclical valuation 핵심: PBR(자본총계 기준, EPS 왜곡 면역)은 작동, PER(EPS 기준)은 peak-EPS trap 으로 무효. = 멀티플 선택이 archetype 의존(가설 아닌 측정 사실).
- **EV-EBITDA** = cyclical primary_metric 이나 부채/현금 계정 추가 필요 = collector_plan high. PBR 가 현 시점 valuation 대표.

## §9. verdict

- **primary (mom_6 → 12M, 반도체 = reversal)** = **PARTIAL CONFIRMED**: IC -0.065 부호 robust(NW+boot CI 0 배제, CPCV 1.00, within 100%, leave-episode 생존, cap-weighted 강화). 단 **BY/Bonferroni 미생존**(raw_p 0.005 > 임계) = battery momentum(CONFIRMED) 보다 한 단계 낮음. small-n hedge.
- **부호 = 음(contrarian/cyclical reversal)** = battery(양 momentum)와 반대 = **cyclical archetype 지지**(peak reversal 패턴).
- **valuation 횡단면** = ★PBR value premium 작동(pbr_z 24M IC -0.114, BY 유일 생존, CPCV 1.00, within 100%) + PER 무효(peak-EPS trap, 전 horizon 비유의). cyclical = PBR○ PER✗ 실증(auto 동형). §10.
- **customer momentum** = REJECTED (글로벌 cycle contemporaneous 동조, forward 부재).
- **common factor** = credit 유의(US proxy n=35 tentative) / dollar 약 음(수출주 환율 가설 약).
- **산업 전체 = PARTIAL** — momentum reversal 방향 robust 하나 보정 후 비유의 hedge.
