---
tags: [type/research-log, domain/equity, sector/semiconductor]
date: 2026-06-05
purpose: 반도체 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용. append-only.
---

# semiconductor 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격 패널 | pykrx OHLCV 개별종목 loop | ✅ 작동 (85종, 1818일, 2019-2026) | ✅ prices.parquet | pykrx **시장 스냅샷** API(get_market_cap/fundamental/sector)는 KRX 인증 차단 → 빈 응답. 개별 OHLCV loop 는 작동 |
| valuation 횡단면 | pykrx 시장 fundamental | ❌ KRX 인증 차단 | DART 재구성으로 우회 | ★battery 와 동일 경로. DART fnlttSinglAcntAll(자본/순이익/자산 + rcept_dt) → PBR/PER cross-sectional z |
| 재무 PIT | DART fnlttSinglAcntAll | ✅ 작동 (2038 rows/85종) | ✅ dart_financials.parquet | CFS(연결)→OFS(별도) fallback = 소부장 OFS-only 종목 포함(가온칩스 등). rcept_dt(공시일) 이후만 적용 = lookahead 회피. FY 보고지연 median 108-120일 |
| 외국인flow (시장레벨) | pykrx get_market_trading_value_by_investor → ECOS 802Y001 | pykrx ❌ KRX 인증 차단(KeyError) / ECOS ✅ 일별 | ✅ ECOS 802Y001/0030000 (외국인 순매수 유가증권시장 일별 2003~2026) | ★team-lead 1순위 pykrx 투자자별 거래도 KRX_ID 차단(시장 스냅샷과 동일). ECOS 일별이 1순위 충족(EWY proxy 불필요). 단 시장레벨 regime 용 — 종목레벨 cs-signal 은 KRX 차단(이연) |
| 글로벌 cycle proxy | yfinance SOXX/SMH/NVDA | ✅ 작동 | ✅ G1 regime + cross | SOXX yoy = 반도체 글로벌 cycle 라벨(battery LIT yoy 대응). NVDA = AI/HBM sentiment |
| 외국인 flow | pykrx 외국인 net buy | ❌ KRX 인증 차단 | ⏳ 미해결 (이연) | ECOS 외국인 증권투자 OR EWY proxy OR KODEX 반도체 ETF flow = 후보. round-1 H5(Tier1 핵심)인데 미측정 |
| common factors | yfinance VIX/dollar/oil/rate/HY-OAS | ✅ 작동 (1898 rows) | ✅ common_factors.parquet | ★USDKRW(DEXKOUS)·Macro regime·외국인flow 시리즈는 **없음** → 36셀 regime 측정 시 신규 수집 필요 |

## 막힘·해결 로그 (시계열)

- [2026-06-05 14:00] 막힘: 반도체 capsule 진입 시 선행 산출물(2026-05-31 round-1 + 2026-06-03~04 v3 measure/summary/validation) 발견. dispatch role 은 "S1부터 신규" 지시. → 진단: 전면 재작성 = 검증 통과분 낭비(P2 pain). → 해결: 선행 산출 신뢰성 직접 검증(합성 지문 + 추적성) 후 team-lead 방향 확인. → 교훈: capsule 진입 시 기존 산출 존재 여부 먼저 점검(mtime + 내용), 무조건 재시작 금지.
- [2026-06-05 14:10] 합성 지문 검사: prices.parquet 에 2020-03 코로나 급락(삼성전자 일중 -6.39%, 49950→42950) + 2022 금리쇼크(연 -29.6%) 실재. 주말행 0, 신규상장 결측 12%. → 합성 아님 PASS. 교훈: AUDIT-GUIDE §0 합성 지문(역사적 이벤트 실재 + 주말공백)이 가장 빠른 1차 검증.
- [2026-06-05 14:15] 추적성 검사: summary.yaml PBR 24M IC -0.1142 / mom -0.065 가 raw json(validation-valuation-v3.json / validation-metrics-v3.json)에 실재 = C축 매핑 정상.
- [2026-06-05 14:20] ★발견(measure.py 점검): **conditional IC 36셀 측정이 통째로 누락**. 기존 soxx_regime_g1()은 SOXX yoy bull/bear/neutral **카운트만** 산출, regime별 IC 분해 없음. + horizon 이 frame §2(y_5d/20d/60d 일간)와 다름(월간 1M/3M/6M/12M_mom). → 진단: 이번 dispatch 본체(IC×regime×horizon surface)가 빠짐. 기존 = 가격신호 unconditional 횡단면 IC 까지만. → 해결: conditional IC 확장이 핵심 신규 작업(task #3). 교훈: dispatch 본체 축이 선행 산출에 있는지 = 진입 점검 1순위.
- [2026-06-05 14:25] §M.12 degenerate 재현: PBR 24M IC t=-4.23 은 eff_indep_N≈2.5(61개월/24M overlap). breadth-adj IR 로는 -1.52 = mom_6(-1.35)와 유사 수준. → 교훈: 24M_value 의 t-stat 은 overlap inflation. magnitude 단정 금지, 3M/6M 재배치(eff_N 큼).

- [2026-06-05 15:00] ★regime 데이터 소스 확정 + 수집 완료 (collect_regime.py): (1) Macro = FRED **KORLOLITOAASTSAM**(한국 OECD CLI **amplitude-adjusted**, 2026-04 가용) — 인계의 KORLOLITONOSTSAM(normalized)은 2024-01 중단이나 amplitude-adj 버전이 살아있어 대체 해소. (2) KRW = FRED DEXKOUS(USDKRW 일별). (3) 외국인flow = ECOS **802Y001/0030000** 외국인 순매수(유가증권시장) **일별** 2003~2026-06 — KRX 차단 우회, 종목데이터(2019~)와 정합. (4) 보조 DRAM cycle = FRED PCU334413334413(반도체 PPI). → 진단: 인계의 "외국인flow=ECOS/EWY proxy 경로"를 ECOS 일별 직접으로 해소(proxy 불필요). 교훈: ECOS StatisticItemList 로 항목코드 탐색 → 일별(802Y001) vs 월별(901Y055) 구분.
- [2026-06-05 15:05] ★★36셀 cell collapse 필수 = 데이터 입증: regime_labels 36셀 교차 → **N≥24 셀 = 0개**(최대 N=13, 중앙 N=2, N>0 셀 26/36). frame §M3 예측대로 36셀 full 분해는 small-N 불가. → 결정: conditional IC = **단일축 regime별 IC**(Macro 4 / KRW 3 / flow 3 각각 분해)로 측정 + 2축 merge 탐색. 36셀 full = INSUFFICIENT 라벨. 교훈: regime 설계 시 셀 N 먼저 측정(측정 전 collapse 전략 확정). 합성지문: 2022-10 USDKRW 1440.5 / CLI 2020 저점 99.13 / 외국인 대량매도 episode 실재 = 실데이터 PASS. ⚠️ CLI amplitude-adj 변동폭 작음(99~101) → Macro 100 기준선 민감, S2에서 quantile 기준 대안 검토.

- [2026-06-05 16:00] ★conditional IC surface 정식 측정 완료 (measure_conditional.py, G-F 7항 헤더 선언). 6신호(mom_6/mom_12_1/rev_1m/vol_60/pbr_z/per_z) × horizon 일간(y_5d/20d/60d) × regime 단일축(Macro4/KRW3/flow3). per-cell = wild-cluster bootstrap p(small-block size-invalid 회피) + n_eff(autocorr) + block-boot CI. → validation-conditional-v3.json.
  - ★발견1: **KRW_weak regime = 신호 증폭축**. pbr_z y_5d KRW_weak wc_p=0.0005(최강) / mom_6 y_20d KRW_weak IC=-0.096 wc_p=0.0055 / rev_1m KRW_weak 강화. 원화약세기 value/reversal 증폭(theory M4 정합).
  - ★발견2: **pbr_z value premium = 전 horizon robust**(y_5d wc_p=0.001/y_20d 0.0045/y_60d 0.0025, unconditional). 반도체 cyclical value premium horizon 무관.
  - ★발견3: **flow_strong_buy 에서 momentum 부호 반전/소멸**(mom_6 +0.0065) = theory M3 "외국인 강매수→passive 지배→IC 감소" 정합.
  - FDR family m=90(naive), BY survivors=[], raw_p_min=0.0005. ⚠️M_eff 미보정(pbr/per·mom_6/mom_12_1 강상관 → 유효검정수 <90) = G-F §3 의무 잔여.
- [2026-06-05 16:10] ★★family_2 interaction 측정 (G-B 의무, rejected 박제 前). pooled panel: ret_rank ~ sig_rank + sig_rank×KRW_weak_dummy, month-clustered SE.
  - **mom_6: b_inter(×KRW_weak)=-0.118, t=-2.95** 유의 / **rev_1m: b_inter=-0.081, t=-2.33** 유의. main effect 비유의(t=0.74/-0.44)인데 interaction 유의 = ★"국면 따라 신호 효과 갈림"(frame A-5 정의) 입증. 신호 약한 게 아니라 **conditional**. G-B "약함 단정" 부적합.
  - sign-flip 13건 = regime별 부호 갈림 다수.
- [2026-06-05 16:15] ★G-B 트리거 판정: BY 생존 0 AND raw_p_min(0.0005) > 2×BY_thresh(0.000437) = 트리거 충족(간발). ★단 Bonferroni alpha=0.00056 로는 pbr_z KRW_weak 1건 생존 + family_2 interaction 유의 = "conditional 살아있음" 쪽. → 내 판정 = "약함" 아니라 "m=90 과대 family + M_eff 미보정". 자문 전 M_eff 보정 + interaction 박제 우선, team-lead에 G-B 자동자문 발동 여부 확인.

- [2026-06-05 16:30] ★D축 PIT leakage 보강: OECD CLI(Macro regime)는 reference month 후 ~1-2M 지연 발표(vintage) → 그 월말 의사결정에 쓰면 lookahead. collect_regime.py 에 CLI_PUB_LAG=2(보수) 적용. ★KRW(DEXKOUS 일별)/flow(ECOS 일별)=실시간이라 lag 불필요. 1M lag 시 macro 라벨 9% 변경. → **재측정 후 핵심 발견 전부 유지**(KRW_weak mom_6 wc_p=0.0055 / rev_1m 0.0025 / Slowdown mom_6 -0.102 wc_p=0.032 powered / flow_strong_buy 소멸). = D축 보강 후에도 robust(over-claim 아님). 교훈: 거시 regime 라벨 = 발표지연 lag 의무(일별 시장데이터는 무관).

- [2026-06-05 17:00] ★S1 리서치 2차 (비판검토+발굴, team-lead "축만 달기 아님" 강조). Gemini Pro 2차 리서치 → 비판 Q5(momentum artifact)/Q6(PBR size 위장)/Q10(HBM episode 종속) + 발굴 Q7(재고순환)/Q8(CAPEX)/Q9(외국인 종목vs시장). 각 학술 반증조건 확보.
  - ★Q6 비판 = 데이터 직접 검정: Fama-MacBeth(ret ~ PBR_rank + Size_rank) → PBR\|Size 통제후 b=-0.043 t=-2.47 유의 유지 / Size\|PBR b=-0.018 비유의 = **PBR size 위장 기각**(독립 alpha). 출처 Asness 2013.
  - ★Q10 비판 = sub-period 검정: pre-HBM(2019-22) vs HBM(2023-26) 부호 = mom_6(-0.005/-0.055) rev_1m(-0.062/-0.025) pbr_z(-0.034/-0.071) = **3신호 부호 일관**(episode 종속 기각). 단 각 기간 단독 약 = full/conditional 적합. 출처 Bai-Perron 1998.
  - ★발굴: 재고순환(Chen-NovyMarx-Zhang 2010, 음)/CAPEX asset growth(Cooper-Gulen-Schill 2008, 음)/R&D(양)/종목레벨 외국인flow(Grinblatt-Keloharju 2000) = candidate-ledger 이연(DART 분기 재구성).
  - 교훈: "비판 = 데이터로 따지기"(team-lead). Q6/Q10 둘 다 "기존 견고" 판명 = 무비판 채택 아닌 검증된 채택. 리서치 반증조건이 측정 설계의 시작점.

- [2026-06-05 17:30] ★S5 역공격 (최강 반증 직접 투척, dispatch lifecycle). KRW_weak conditional(family_2 핵심)에 3 반증:
  - **반증1 "단일 원화약세 episode 종속?"**: KRW_weak 38개월 = 2019(7)/2020(3)/2021(2)/2022(12)/2023(4)/2024(4)/2025(5)/2026(1) = 여러 해 분산(2019-21도 12개월). 부분 기각.
  - **반증2 "stress regime 대리(risk-off)?"**: VIX KRW_weak 21.5 vs 전체 20.2 = 거의 동일 = stress 아님 = 진짜 환율 효과(theory M4). 기각.
  - **★반증3 leave-2022-out (결정적)**: 2022(원화약세 최대 12개월) 통째 제거 후 family_2 interaction: mom_6 t=-2.95→**-3.41(강화)** / rev_1m t=-2.73→-2.47 = **부호+유의 생존**. = 단일 episode 종속 결정적 기각.
  - ★종합: KRW_weak conditional = 3 반증 모두 방어 = robust(단 in-sample, OOS pending). = S5 수렴(신호 생존).
  - 교훈: conditional 신호의 최강 반증 = "regime이 단일 episode/다른 효과 대리?" → leave-episode-out + 교란변수(VIX) 대조로 직접 검정.

- [2026-06-05 18:00] ★walk-forward OOS (team-lead 지시 = verdict 확정 근거, 미래 데이터 불필요 지금). IS(2019-2022)/OOS(2023-2026) split, KRW_weak conditional:
  - **mom_6 KRW_weak**: IS -0.060(n=21) → OOS -0.155(n=13) = ✅부호유지+magnitude(강화)
  - **rev_1m KRW_weak**: IS -0.117(n=24) → OOS -0.064(n=13) = ✅부호유지+magnitude
  - **pbr_z KRW_weak**: IS -0.051(n=22) → OOS -0.050(n=13) = ✅부호유지(거의 동일)
  - **family_2 interaction IS/OOS**: mom_6 IS t=-2.09 → OOS t=-2.69(둘 다 유의) / rev_1m IS t=-2.26 → OOS t=-1.28(부호유지, OOS 약화).
  - ★verdict 확정: 3신호 KRW_weak conditional 전부 OOS 부호+magnitude 유지 + mom_6 interaction OOS 유의 = **in-sample artifact 아님** = conditional CONFIRMED(★tentative, OOS n=13 small-n magnitude hedge). rev_1m interaction OOS 약화 = PARTIAL.
  - 교훈: walk-forward = "in-sample 정합이 진짜 신호인가" 현 데이터 검증. IS/OOS 부호유지 = artifact 아님. n<30 = tentative 유지(magnitude 단정 금지). ★이것이 team-lead "미래 데이터 불필요 지금 가능" OOS.

- [2026-06-05 18:30] ★신규 cycle 지표 측정 (사용자 박제 "이연 금지" = 지금 측정). collect_dart_extended.py(재고/유형/무형자산 PIT 85종 2077rows, coverage inv 79%/ppe 100%/intangible 77%) → measure_fundamentals_cycle.py(3축 conditional + wild-cluster + 단일 FDR family).
  - ★막힘: collect background 프로세스 **2회 죽음**(30/85, 49/85 정체, parquet 미수정). DART API는 정상(0.1s 응답). → 진단: 장시간 background 불안정(P4 pain). → 해결: resume(done_codes skip incremental) + **foreground 청크**(timeout 280s)로 49→85 완주. 교훈: 장시간 수집 = foreground 청크 + resume 필수(background 단독 불가).
  - ★측정결과 (정직, over-claim 0): **ppe_yoy(CAPEX asset growth)** y_60d IC=-0.034 wc_p=0.0155 + OOS -0.028 부호유지 = TENTATIVE(prior 음 정합, Cooper-Gulen-Schill). **inv_ratio(재고/총자산)** y_60d IC=+0.045 = ★**prior 반증**(prior 음인데 양, OOS도 양 일관) = 재고순환 가설 반대(메커니즘 재해석: 재고/자산 高=성장 종목 prox). 나머지(inv_yoy/capex_ratio/rnd_ratio) 비유의.
  - ★통합 단일 FDR family(merge_fdr_family.py): m_total=183(cond 105 + fund 78) survivors=0. raw_p_min=0.0005(pbr_z KRW_weak + ppe_yoy 동률). = 신규지표 추가시 family 커져 BY 더 엄격(garden-of-forking-paths 차단 정확 작동).
  - ★종합: 신규지표 대부분 가격/valuation 보다 약. ppe_yoy만 tentative. = 정직 박제(약신호도 verdict). 사용자 박제 "이연 금지" 이행(불확실해도 측정+verdict).

- [2026-06-05 18:45] ★DRAM ASP + size-orth PBR 측정 (team-lead "측정 가능 지표 다 한다"). DRAM ASP = 반도체 PPI yoy → 산업 eq-weight forward (timing, ★cross-sectional 아님 = 산업 공통 시계열). 결과: forward 1M -0.073/3M -0.102/6M -0.205(p=0.071) / contemp -0.069 = INSUFFICIENT(timing forward 비유의, 6M 약 음 근접 = cyclical peak 되돌림 방향). → regime conditioning 변수로 더 적합. size-orth PBR = Q6 Fama-MacBeth(완료, PBR|Size t=-2.47 유의 = 독립 alpha). 교훈: 산업 cycle 지표(DRAM ASP)는 cross-sectional IC 부적합(종목 공통) → timing 또는 regime 변수로 측정. = 측정 가능 신규지표 전부 완료(재고/CAPEX/R&D/DRAM ASP/size-orth). 종목레벨 flow만 DATA-GATE.

## 측정 방법 결정 로그

- **regime conditional IC (신규)**: plan §2 + frame §M3 = 36셀(Macro 4 × KRW 3 × 외국인flow 3). horizon y_5d/y_20d(메인)/y_60d. N<24 cell collapse(1단계 36셀 측정 → 2단계 인접 merge → 3단계 외국인flow 3셀 fallback). ★측정 결과 보기 전 부호 사전확약(HARKing 방지, team-lead 조건2) = theory-notes.md.
- **momentum 부호 = 음(reversal)**: 기존 측정값(IC -0.065). ★단 team-lead 조건2 = 이 값을 보고 가설 맞추지 말고, cyclical 이론(peak reversal)으로 **독립 부호 사전확약** 후 대조. → theory-notes 에서 이론적 부호 먼저 박제.
- **valuation = PBR○ PER✗**: cyclical peak-EPS trap 이론(archetype.py primary=P/B). PER 무효는 이론 예측과 정합(측정으로 확인).
- **G-F 7항 헤더**: 기존 measure.py 미선언. fixed-b/wild-cluster per-test calibration = 36셀 한자릿수 block 에 NW-HAC asymptotic t 는 size-invalid(Kiefer-Vogelsang) → 재계산 의무(team-lead 조건4).
- **family-neutralized IC / partial-corr**: 산업 단계 = unconditional 까지(M.7 분담). 통합 단계로 이연.

## 미해결 / 다음 세션 우선 작업

1. ★conditional IC 36셀 × horizon(y_5d/20d/60d) 측정 확장 = dispatch 본체 (measure.py 신규 함수 + Macro/KRW/외국인flow regime 분류기 + 신규 데이터 수집).
2. theory-notes.md = 리서치 기반 부호 사전확약(HARKing 방지) → 기존 측정 대조.
3. G-F 7항 measure.py 헤더 선언 + fixed-b/wild-cluster per-test 재계산.
4. 외국인 flow regime 데이터 해소(ECOS/EWY proxy) — round-1 H5 Tier1 핵심.
5. G-B 판정: momentum family BY 생존 0 + raw_p 0.005 > 2×thresh 0.0037 → 트리거 가능. family_2 interaction(KRW regime × momentum) 점검 후 "약함" 단정 회피.
6. EV-EBITDA(cyclical primary_metric) DART 부채/현금 계정 추가 수집.

- [2026-06-05 23:00] ★반도체 업종 ROTATION timing 측정 (team-lead 지시 = 산업 전문가 자기산업 심화, rotation-analyst soxx 보강). 후보 8개(PPI yoy/PPI Δ3m/수출 yoy/재고 yoy/SOXX Δ3m/USDKRW/CLI chg/momentum). measure_rotation_semi.py → validation-rotation-semi-v1.json.
  - source 사전검증: 반도체 PPI(PCU334413334413 보유) / 수출(XTEXVA01KRM664S FRED) / 재고(dart_extended 산업합산) / SOXX(rotation-analyst cycle_semiconductor.parquet 재사용).
  - ★핵심: **SOXX = 동행 입증**(forward +0.161 vs contemp +0.476) = rotation-analyst soxx 약신호(wc_p 0.13) 정체 = 동행성, 선행 아님. **export_yoy 음(-0.255 wc_p 0.017)** = 수출 선행변곡(이론 정합). **cli_chg 양(+0.225 OOS +0.245)** = 경기선행, OOS 부호+magnitude 유지(유일 robust).
  - ★재고 yoy 부호 반증(음, prior 양 반대) = 종목 capsule inv_ratio 동일패턴(메커니즘 재해석). momentum residualize 잔존(+0.158)=공통인자 재포장 아님(단 약, rotation-analyst cross-industry 소멸과 unit 차이).
  - 판정 PASS-conditional: cli_chg+export TENTATIVE 채택(이론+OOS 부호유지), soxx=동행지표. 전신호 underpowered(t_obs<2.802)+BY 미생존(m=16)=magnitude tentative. = data mining 아님(이론 사전확약+OOS).
  - 교훈: rotation(업종 timing=경기·수출 cycle) ≠ selection(종목=환율 regime). SOXX 같은 가격지표는 동행≠선행 = forward IC로 판별. 산업 전문 fundamental(수출/CLI)이 rotation-analyst 가격지표보다 이론 정합.
