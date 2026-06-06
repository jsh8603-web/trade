---
tags: [type/research-log, domain/equity, sector/us_defensive]
date: 2026-06-03
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# us_defensive 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| PBR/PER | EDGAR companyconcept XBRL (equity/net_income/shares) | 현 us_defensive = 3 concept만 수집(equity/ni/shares), PBR/PER 만 측정됨 | ⏳ (재작업: 12 concept 확장 필요) | ★현 PBR 24M IC +0.062 역방향 = buyback book 왜곡 noise-trap(문헌) + universe-demean 결함 의심 |
| gross_profitability | EDGAR GrossProfit/CostOfRevenue+Assets | 미수집(현 3 concept만) | ⏳ collect.py 확장 | us_cyclical 실측 = semi/industrials 직접, mat/energy/fin fallback. defensive 가용성 측정 의무 |
| payout_yield | EDGAR PaymentsOfDividendsCommonStock/PaymentsForRepurchaseOfCommonStock/ProceedsFromIssuanceOfCommonStock | 미수집 | ⏳ collect.py 확장 | ★utilities 거의 buyback 안 함 → dividend_yield subset 으로도 가능 |
| ev_ebitda/fcf | EDGAR OpIncome+D&A+debt+cash (+CFO) | 미수집 | ⏳ collect.py 확장 | us_cyclical collect.py 12 concept 재사용 |
| HY OAS regime | FRED BAMLH0A0HYM2 | ★2023-05~ 37mo만(us_cyclical 동일) | ⏳ Baa-Aaa proxy | eq_us_defensive raw/fred/ 에 BAMLH0A0HYM2.csv 존재(기존 m3). Baa-Aaa = BAA/AAA fetch |
| rate10y/real_rate | FRED DGS10/DFII10 + DXY | 기존 m3 보유(real_rate β −0.171 강) | ✅ family_3/regime | ★rate-duration = unconditional cross-sectional IC≈0(risk factor), sleeve common factor |

## 환경 함정 (★재발 방지)
- [2026-06-03] 막힘: WebSearch/WebFetch hook 차단(research.block). → 해결: search-engine 스킬(Gemini gemini-search.js pro/flash) 경유. node 풀패스 `/c/Program Files/nodejs/node.exe` 필수.
- [2026-06-03] 막힘: Write 도구의 `/tmp/X.md` 가 msys2 `C:\msys64\tmp\` 와 다른 경로로 매핑 → node 가 ENOENT. → 해결: 프롬프트 파일을 프로젝트 디렉토리(raw-v3/.s1tmp/)에 작성 후 node 에 절대경로 전달.
- [2026-06-03 예상] python stdout cp949 인코딩 에러(★·— 출력) → `sys.stdout=io.TextIOWrapper(...,encoding='utf-8')` (us_cyclical measure.py 패턴). python = `PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"` 절대경로(research-log us_cyclical 교훈).

## ★EDGAR concept 가용성 사전 probe (2026-06-03, dispatch §1.1-ext 의무 — fetch 전 검증)
4 sub-sector 대표(PG staples/NEE utilities/JNJ healthcare/VZ telecom) companyconcept probe 결과:
- **dividends**: `PaymentsOfDividends` = PG/NEE/VZ OK, ★JNJ 404 → `PaymentsOfDividendsCommonStock`/`Dividends` 둘 다 404. JNJ 는 별 tag(추가 fallback 필요). 후보 순서 = [PaymentsOfDividends, PaymentsOfDividendsCommonStock, Dividends, PaymentsOfDividendsCommonStockMember...] → JNJ 실측 시 추가 탐색.
- **repurchase**: `PaymentsForRepurchaseOfCommonStock` = 전 4종 OK ✅
- **issuance**: `ProceedsFromIssuanceOfCommonStock` = NEE/VZ OK, PG/JNJ 404 (자사주 재발행 적음 = 0 처리 가능)
- **CFO**: `NetCashProvidedByUsedInOperatingActivities` = 전 4종 OK ✅ (accruals/fcf 가능)
- **Assets/OpIncome**: 전 4종 OK ✅
- **GrossProfit**: ★JNJ만 OK. PG/NEE/VZ 404 → fallback Revenues−COGS. ★NEE(utilities 대표 probe 1종) = `CostOfGoodsAndServicesSold`/`CostOfRevenue` 둘 다 404 = NEE 측정 불가. ★단 ★**실측 시 utilities 5종(DUK/PEG/SO/WEC/XEL) 203obs + comm 3종(T/TMUS/VZ) 111obs COGS fallback 채워짐**(NEE 1종 probe 일반화 = 오류, G-C 정정). gross_prof = staples/healthcare 주력 + utilities/comm 일부 partial-coverage = A-4 게이트.
- **COGS**: PG/JNJ/VZ `CostOfGoodsAndServicesSold` OK, NEE 404 but ★utilities 다른 종목(DUK/PEG/SO/WEC/XEL) 일부 가용(NEE 1종 ≠ utilities 전부).
- **D&A**: `DepreciationDepletionAndAmortization` = PG/JNJ OK, NEE/VZ 404 → EV/EBITDA D&A fallback 필요(`DepreciationAndAmortization` 등).
- **Revenues**: PG/NEE/VZ OK, JNJ 18 obs만(`RevenueFromContractWithCustomerExcludingAssessedTax` 124 = JNJ 주 tag).
- **shares**: ★`dei:EntityCommonStockSharesOutstanding` = 전 4종 OK ✅ → 현 shares 30/48 → dei fallback 으로 보강(us_cyclical 동형 47→60 패턴).
★결론: payout_yield 측정 가능(div fallback 다층 + repurchase 전종목). gross_prof = staples/healthcare 주력 + ★utilities/comm 일부 COGS fallback partial-coverage(NEE 1종 probe 로 "utilities 부재" 일반화는 오류, 실측 utilities 5종·comm 3종 채워짐 = G-C 정정). EV/EBITDA = D&A fallback 필요. accruals/fcf = CFO 전종목 가용.

## ★FRED 가용성 사전 검증 (2026-06-03, dispatch §1.1-ext)
- us_defensive raw/fred/: BAMLH0A0HYM2(HY OAS, ★2023~ 제약)/DGS10/**DFII10**(real_rate, defensive 듀레이션 핵심)/VIXCLS/DTWEXBGS/BAA10Y/AAA10Y/T10YIE 등. ★`BAA.csv`/`AAA.csv` **부재**(BAA10Y/AAA10Y = Treasury-spread 형태만).
- us_cyclical raw/fred/: ★`BAA.csv` + `AAA.csv` **있음** → Baa-Aaa default spread(Fama-French 1989) 계산 가능. collect.py 가 CYC_FRED fallback 으로 읽음(설계 완료).
- cik_map = us_cyclical cik_map.json 재사용 = 전 defensive ticker 포함 확인 ✅.
- ★Baa-Aaa = family_2 credit regime proxy(HY OAS 37mo 대체). DFII10(real_rate) = family_3 듀레이션 β + regime tilt(unconditional cross-sectional IC≈0).

## 막힘·해결 로그 (시계열)
- [2026-06-03 진입] dispatch-role-rework + 게이트 4종 + ledger 양식 + frame §M.7(line 267-269 sector-neutral 계약 + line 320-322 24M degenerate/small-n/sector-neutral 경고) + us_cyclical 완성 산출(★양식 정답지: summary.yaml/measure.py sector_z_decomposition/candidate-ledger/research-log/15axis-audit) 정독 완료.
- [2026-06-03] ★현 us_defensive 진단: (a) cs_z/cross_sectional_zscore = universe-demean = us_cyclical 발견 결함과 동일 (b) EDGAR 3 concept만(equity/ni/shares) = valuation 확장 필요 (c) PBR 24M +0.062 역방향 = noise-trap+sector-mixing 의심 (d) universe 49종 4 sub-sector(staples 15/utilities 15/healthcare 15/comm_mature 4). ★comm_mature 4종 = sector-neutral 시 small-n 심각 주의.

## 측정 방법 결정 로그
- [S1 리서치 2026-06-03] Gemini 2-Phase: Pro 광범위(result1.txt 19811 chars, 9 signals) + Flash 심층(result2.txt 측정·EDGAR 가용성) + citation 환각검증(citecheck-result.txt). archive=raw-v3/.s1tmp/.
- ★citation 환각검증: Frazzini-Pedersen(2014 JFE)/Baker-Bradley-Wurgler(2011 FAJ)/Ang(2006 JF)/AFP-QMJ(2019 ★RAS 정확)/Novy-Marx(2013 JFE)/Boudoukh(2007 JF)/Basu(1977 JF)/Lakonishok(1994 JF)/Sloan(1996 AR)/Gormsen-Lazarus(2023 JF)/Dechow-Sloan-Soliman(2004 RAS)/Jegadeesh(1990 JF)/Fama-French(1989 JFE)/FF(1988 JFE) = CONFIRMED. ★CORRECTED 2: Ball-Gerakos-Linnainmaa-Nikolaev = "Deflating Profitability" JFE 117(2) 225-248 (NOT "Defensive Equity JFE 119"). Greenwood-Vayanos(2014 RFS) = "Bond Supply/Excess Bond Returns"(duration/supply) ≠ reach-for-yield 1차 출처 → reach-for-yield claim 약화 라벨.
- ★측정 방법 4수정(us_cyclical 미러): family 3분리(Harvey-Liu-Zhu) / M_eff(Li-Ji 2005 test-stat 상관행렬) / eff_N 이중보정 / defensive basket 불필요.
- ★sector-neutral z 정식(최우선): us_cyclical pilot 발견(universe-demean 결함, BY 0→8) + ★자문 명시(dividend-yield sub-sector sign flip = staples/healthcare alpha vs utilities risk → universe-demean cancel) = defensive 동일 결함 가능성 높음.
- ★핵심 가설 차이(cyclical 반대): defensive EPS 안정 → PER/E-P value 정상 작동 예상. 단 문헌 caveat 3 = PBR noise-trap(buyback) / E/P>PER(negative earnings) / FCF/EV>E/P(CAPEX). → 측정에서 직접 검증.

## ★team-lead 1차 보고 대기 (§1 완료 → §2 진입 전 확인)
- §1 리서치 완료 = 발굴 지표 목록 + candidate-ledger 초안 + theory-notes. team-lead 확인 후 §2(sector-neutral 측정 + EDGAR 12 concept 수집 + 자문 R2 4수정) 진입.
- ★team-lead 질문 후보: (a) EDGAR 12 concept 추가 fetch(payout 3 tag 포함) + Baa-Aaa fetch 승인 (b) us_cyclical collect.py/measure.py 재사용 + payout_yield/earnings_stability 신규 추가 방향 확인.

## 측정 결과 1차 (sector-neutral z, ★BY 생존 0 = G-B 트리거)
- [2026-06-03] team-lead §2 승인(코멘트 5종). collect.py 완료: EDGAR 111140 rows 48종. coverage: assets/cfo/cash/st_debt 48, net_income/revenues 48, dividends 47, repurchase 45, shares 47(dei fallback 30→47), gross_profit 직접 22(+cogs 37 fallback), capex 46. macro baa_aaa 1919~ n1288, real_rate 2003~, hy_oas 2023~(37mo).
- [2026-06-03] measure.py(sector-neutral) 완료: ★family_1 BY 생존 **0/48**(M_eff=26.0, raw_p_min 0.0174 ep_yield 3M > threshold 0.000998). nondegenerate strip 도 0. raw_p_min 0.0174 > threshold×2(0.002) = **G-B 트리거 충족** → team-lead 보고(단정 ⛔).
- ★★**핵심 발견 = defensive 강한 anti-value/anti-yield (cyclical 정반대, sector-neutral 으로도 회복 X)**:
  - **value 역방향**: ep_yield(E/P) IC 음 일관(3M −0.038 t−2.4 / 6M −0.048 / 12M −0.056 t−2.2), per_z 양(+0.038 t2.28) = 고E/P(싼)→저forward = value premium 완전 역방향. OOS persist=True(ep 12M IS−0.027→OOS−0.085 강화).
  - **payout/dividend crowding falsifier 실현**: payout_yield 음 일관(6M −0.063 t−2.28 / 12M −0.083 / 24M −0.113), OOS persist. = 고배당→저forward = reach-for-yield distress proxy(자문 예측 적중).
  - **earnings_cv 양**(3M +0.040 t2.3, OOS persist): 불안정→고forward = stability 역방향(Ball et al. tail-risk≠평균수익 + 위험보상).
  - gross_prof ≈0(staples +0.059/health −0.081 약), vol_60 약 양(저변동성 프리미엄 약), rev_1m 약 음.
- ★**PBR 역방향 주범 분리(검증 b)**: pbr 12M uni +0.021 → secN +0.016 → sectorLevel +0.009 = 세 성분 모두 약·동부호 = ★sector-mixing 주범 아님(us_cyclical 과 다름). PBR 자체가 defensive 약/역방향 = buyback noise-trap 부분 지지. ★sector-neutral 무회복 = defensive 는 us_cyclical 방법결함 패턴 아님.
- ★**A-4 sub-sector**: ep_yield/payout 전 4 sub-sector 음 일관(cancel 아님, comm_mature −0.165/−0.153 small-n hedge). = 진짜 일관 역방향, 슬리브 분리 아님. gross_prof = staples/healthcare 주력 + utilities 5종(IC+0.036)·comm 3종 COGS fallback partial-coverage(NaN tri-state).
- ★**family_3 β(정상)**: real_rate −0.066 t−6.78(듀레이션 강) / vix −12.94 / dollar −5.45 / hy_oas n36 비유의 / baa_aaa 비유의.
- [2026-06-03] team-lead G-B 보고 송부: (A) 자문 분기 vs (B) anti-value 역방향 채택 판정 요청 대기.

## ★G-B 1차 자체 검증 (team-lead 지시, 자문 전 — 본질 vs artifact 판별, _gb_self_verify.py → _gb_verify.json)
- [2026-06-03] team-lead 판정 = (B) anti-value 즉시채택 ⛔보류(BY 미생존+단일 QE 표본 regime overfit 위험). 자문 전 자체검증 3종 의무.
- ★**1. regime split (QE 2010-2021 vs value-revival 2022-2026, 핵심 falsifier)**:
  - **ep_yield**: QE −0.061(t−1.95) → 2022+ −0.040(t−1.29) = ★sign_consistent **True**(부호 유지, 약화). 6M 도 True. = ★**anti-value 부분 본질**(value-revival era 에서도 역방향 유지).
  - **payout/dividend_yield**: QE −0.122/−0.120(t−2.86/−2.67) → 2022+ **+0.054/+0.096** = ★sign **FLIP 역전**(consist False). 6M 동일(QE −0.093/−0.060 → 2022+ +0.029/+0.055). = ★**payout anti-yield = QE/reach-for-yield regime artifact 강력 증거**. value-revival 에서 고배당 다시 outperform.
  - per_z: QE +0.051 → 2022+ −0.013 = flip. earnings_cv: QE +0.054(t2.16) → 2022+ +0.034 = consist True(약).
- ★**2. quality partial-corr (anti-value vs quality 재해석)**:
  - ep_yield raw −0.056(t−2.2) → gross_prof 통제 partial **−0.051(t−1.55)** = ★거의 잔존(quality proxy 아님, anti-value 독립). t 약화.
  - payout raw −0.083 → partial **−0.059(t−0.99)** = 약화(일부 quality 흡수).
- ★**3. LOO-year**: ep_yield/payout 둘 다 sign_stable=True(특정 연도 의존 아님, 2020 COVID 의존 X). ep ex-range[−0.070,−0.044], payout ex-range[−0.101,−0.063].
- ★**자체검증 결론(team-lead 자문 입력용)**:
  - **ep_yield anti-value = 부분 본질**: regime 부호 유지(consist True) + quality 독립(partial 잔존) + LOO 안정. 단 약함(BY 미생존, t≈2).
  - **payout/dividend anti-yield = QE regime artifact 강력**: 2022+ 부호 역전 = reach-for-yield 가 QE era 특수(자문 falsifier 정확 실현). value-revival 에서 소멸.
  - per_z = 불안정(flip). earnings_cv = 약 위험보상(consist 약).
- [2026-06-03] team-lead 보고 송부 → team-lead 가 G-B 자문(gemini-web+claude-web) 설계·실행.

## ★G-B 자문 수렴 verdict (team-lead 전달, .consult-us-defensive-R1-results.md) + leave-sub-sector
- [2026-06-03] team-lead G-B 자문(gemini-web+claude-web 병렬) 1R 수렴. 두 모델 일치:
  - **us_defensive sleeve = ★INSUFFICIENT** (cross-sectional factor-tilt 부적절: BY 0/48 + 단일 QE 표본 + small-n). sleeve alpha = macro overlay.
  - **ep_yield anti-value = ★TENTATIVE_DIRECTIONAL (regime-conditional)** (regime-robust + yield-trap 부분 구조). ⛔unconditional 채택 금지, hedge. quality축 미통제 한계 명시.
  - **payout/dividend = ★rejected_provisional (regime-conditional reserve, 현재 PROHIBITED)** (reach-for-yield artifact, 저금리 interaction reserve, 부활트리거 Fed<2%/VIX>25/HY>300bp).
  - per_z/earnings_cv = INSUFFICIENT (regime flip). duration/credit overlay = ★QUALIFIED (real_rate β−0.066 robust = family_3 driver, supervisor overlay 몫).
- ★**leave-sub-sector 추가 검증(claude 지적 = healthcare 지배 점검)**: ep_yield 12M FULL −0.056 → ex_healthcare **−0.062**(오히려 강) / ex_staples −0.060 / ex_utilities −0.059 / ex_comm −0.051 = ★**healthcare 의존 아님, sleeve-wide anti-value 확인**(4 sub-sector 음 일관 정합). claude healthcare 지배 가설 ★기각. payout 도 ex_healthcare −0.075 유지(full-period).
- ★**자문 raw 경로 정정(team-lead, 2026-06-04)**: `.gemini-web-last.md`/`.claude-web-basic-last.md` = append 방식 → head=2026-04 옛 항목(내가 본 것), ★실제 us_defensive 자문 = **tail(mtime 18:58/19:00, 2026-06-04 항목)** 정상 저장(grep anti-value/ep_yield/payout 매칭 확인). 무관 자문 아님. 수렴 SSOT = `D:/projects/Inv/.consult-us-defensive-R1-results.md`. 15axis G-A.2 S3 경로 정정 완료.
- ★**자문 추가 지적**: (claude) power analysis n=48 t−2.2 → power ≈0.53 = BY 미생존 통계 근거 / 누락축(interest coverage·regulated asset base·quality-adjusted value·explicit duration) = collector_plan. (gemini) sector-neutral 무회복 = defensive cross-sectional peer-relative value 자체가 초과수익 원천 아님(개별 펀더멘털 절대적). → 15axis G-A.6 보강 완료.

## ★STEP 1~3 (B″ 조정안, lock-blocking 게이트, 2026-06-04) — payout split→interaction 전환
- [2026-06-04] team-lead 지시 = REWORK-B2-adjustment-plan STEP 1~3 (자문 3R B″). 현 `regime_conditional()`(baa_aaa quintile split) = frame line 323 위반 → 신규 `_payout_interaction.py` 구현(measure.py 미변경, 별 파일 = byte-identical 보존).
- **STEP 1 (④ duration-orthogonalize → credit interaction)**: payout-premium return R_payout,t(long-short) → FWL 직교화(duration 먼저: R~ΔReal_rate β_dur=0.016 t0.47 비유의) → ΔReal_rate continuous interaction(split 아님, mega_tech regime_interaction 이식) → credit(baa_aaa) 적층.
- **STEP 2 (②⑤⑦)**: effective_n = n/(1+2Σρ_k) NW VIF + ★per-test calibration = fixed-b CV(Kiefer-Vogelsang 2005 Bartlett) + wild-cluster(block) bootstrap = size-valid. 단일 FDR family.
- **STEP 3 (⑥)**: Ridge λ = expanding-window PIT 동결(train 60% CV → eval 40% 미접촉) + λ∈{0.1λ*,λ*,10λ*} 3점 hedge table.
- ★★**핵심 결과 (B″ size-valid)**:
  - payout 12M: ΔReal_rate interaction β=0.028 **t_asy=0.43** / fixed-b CV 2.09(b=0.022) → ★**size-valid 비유의** / wild-cluster p=0.68. **NO_INTERACTION** 판정(직교 전부터 비유의).
  - dividend 12M: β=−0.038 t−0.52 비유의. payout 6M 동일(t0.26 비유의).
  - effective_n: n=185 → n_eff 44~57(VIF 3.4~4.2, ρ1 0.78~0.88 고지속). regime block.
  - Ridge λ PIT: 3점 격자 전부 sign_stable=True(coef 음 일관, eval_corr 동결).
- ★★**split vs interaction 대조 (자문 R3 Claude size-invalid 경고 실증)**:
  - regime **split**(직전): QE −0.122 **t−2.86**(유의해 보임) → 2022+ +0.054(FLIP). = asymptotic NW t.
  - B″ **continuous interaction**: payout IC~ΔReal_rate t_asy 0.43, ★**fixed-b CV 기준 비유의**, wild-cluster p0.68.
  - = ★**split 의 "QE 강한 신호"가 size-valid continuous interaction 에서 소멸** = split 이 (a) garden-of-forking-paths(사후 가설) + (b) small-block NW asymptotic over-rejection(size-invalid) artifact. ΔReal_rate continuous 변동에 payout IC 가 size-valid 반응 안 함.
- ★**verdict = payout rejected 유지(B″ 후 강화)**: 자문 prediction "회생 가능"과 다르게 NO_INTERACTION = armed-pending("조건부 PASS")조차 진입 불가. ★split→interaction + fixed-b 전환이 payout 을 더 엄격히 기각. STEP 4 add(idio-vol/residual-mom) = 게이트 미통과라 진입 보류(오염 추론 위 factor 적층 금지 정합).
- ★측정 인프라(effective_n/fixed-b CV/wild-cluster/Ridge λ PIT) = STEP 2/3 게이트 정상 작동, 타 sleeve 재사용 가능.
- [2026-06-04] team-lead 승인(payout NO_INTERACTION 결과 + 내부 정합) + STEP 4 add GO + 공용 모듈화 GO.
- ★**STEP 4 add (idio-vol/residual-mom, 단일 FDR family, `_step4_add_factors.py`)**: payout 죽었으니 sleeve 다른 신호 확인(payout 게이트 무관 독립 채널 = 적층 정당).
  - ep_yield 3M/6M/12M = ★**fixed-b size-valid 유의**(t−2.4~−2.6 > CV 2.08~2.09) = anti-value 가 small-block NW over-rejection artifact ★아님 입증(power 우려 부분 반박). 단 FDR family 미생존.
  - residual_mom 12M = IC+0.039 t2.55 fixed-b size-valid 개별 유의(price-based, sector·beta 직교). 단 6M t1.82/3M t1.76 약 + FDR 미생존 = TENTATIVE(observe-only). idio_vol 무신호(t0.46~0.73).
  - ★단일 FDR family BY(ep+idio+rmom 9 test, M_eff=7.0) 생존 0(raw_p_min 0.0122 ep12M > threshold 0.0053). size-valid survivors 0. = ★sleeve INSUFFICIENT 유지.
- ★**공용 모듈화 (`_b2_stats.py`, team-lead 지시)**: effective_n/fixed_b_cv/wild_cluster_boot/persistence_block/ridge_lambda_pit/ic_size_valid_test 추출. `_payout_interaction.py` 리팩토링(import _b2_stats, 별칭 + 위임) → 재실행 회귀 0(payout 12M β0.028 t0.43 NO_INTERACTION 동일). ★cyclical/타 sleeve import 재사용 가능.
- ★**산출**: summary.yaml(b2_gate 블록 + cs_residual_mom 추가 + payout NO_INTERACTION + ep fixed-b size-valid 박제) + 15axis G-A.7 + candidate-ledger(payout/residual_mom/idio_vol + evt split size-invalid + memory). ★measure.py 미변경(B″=별 파일, byte-identical 보존). YAML valid.

## ★breadth 전수 B″ size-valid sweep (2026-06-04, 사용자 지적 = 우선순위만 측정 갭) — `_breadth_sweep.py`
- [2026-06-04] team-lead 전달 사용자 지적 = "변경된 B″ 프레임으로 후보 전수 검토했나" → residual_mom/idio_vol 만 했고 나머지 breadth 미측정. `_b2_stats.py` 재사용 + 신규 6 후보 전수 측정(fetch 0, 보유 concept/price/volume).
- **측정 6종**: net_issuance(Pontiff-Woodgate 2008) / high_52w(George-Hwang 2004) / amihud(Amihud 2002) / op_profitability(FF 2015) / roe / accruals(Sloan 1996). + 기존 ep/idio/rmom = 27 test 단일 FDR family.
- ★★**핵심 발견 = net_issuance 단일 FDR family BY 생존 (defensive 첫 생존 신호)**:
  - net_issuance 3M IC+0.082 t4.40 / 6M +0.073 t4.18 / 12M +0.082 t3.31 = ★fixed-b size-valid + **단일 FDR family(27 test, M_eff=19.0) BY 생존**(raw_p_min 3e-05 < threshold 0.0015). 전 3 horizon.
  - ★부호 = **양**(순발행 (issuance−repurchase)/mktcap 高 → forward 高) = ★문헌 Pontiff-Woodgate(음, 발행→저수익) **반대** = anti-issuance/buyback-aversion(defensive 자사주 매입 종목 = 비싼값 자사주 = 가치파괴 = anti-value/anti-payout cluster 정합).
  - ★robustness: regime split QE +0.087 → 2022+ +0.067 = ★**부호+magnitude 유지**(payout 의 FLIP 과 ★다름 = net_issuance 는 payout 단순 재포장 아님) + LOO-year stable(range +0.066~+0.099) + sub-sector staples+0.117/util+0.081/health+0.064 양 일관, comm_mature −0.121(반대, 4종 small-n hedge).
  - ★payout 상관: net_issuance vs payout cross-sec corr −0.531(자사주 채널 부분 중복 but 완전 동일 아님, 단일 FDR family 안 함께 측정 = 이미 보정). vs ep_yield −0.06(독립).
- **나머지 breadth**: amihud 12M t1.98(개별 약, FDR 미생존) / high_52w·op_profitability·roe·accruals 무신호. ep(3종)+residual_mom 12M = size-valid 개별 유의(FDR 미생존, 기존 확인).
- ★**이연 (ledger 사유)**: SUE-PEAD = 8-K Item 2.02 furnish date anchor 필요 = EDGAR 8-K 파싱 별도 작업(데이터게이트) = 이번 sweep 제외.
- ★**sleeve verdict 변동**: INSUFFICIENT → ★**PARTIAL**(net_issuance 1개 FDR 생존, size-valid + regime-robust + LOO + sub-sector 3/4). 단 ★부호 반대(anti-issuance) 해석 + payout −0.53 중복 hedge + comm_mature small-n.
- ★measure.py 미변경(`_breadth_sweep.py` 별 파일, byte-identical). 산출 `_breadth_sweep.json`.
- [2026-06-04] ★**net_issuance 직교화 검증 (team-lead advisory §1, 채택 전 자체 시뮬 의무, redundancy vs incremental)**:
  - ⊥ep_yield(anti-value 직교): partial IC 12M +0.084 t3.71 / 6M +0.071 t4.03 / 3M +0.062 t4.40 = ★**fixed-b size-valid 잔존**(오히려 강화) = ep 와 독립.
  - ⊥payout(자사주 채널 직교): partial IC 12M +0.055 t2.41 / 6M +0.055 t3.18 / 3M +0.052 t3.41 = ★**size-valid 잔존**(약화되나 유의) = payout −0.53 중복 제거 후에도 살아남음.
  - = ★**INCREMENTAL 확정**: net_issuance 가 anti-value cluster(ep) + buyback 채널(payout) 모두 직교 후 size-valid 잔존 = **buyback-aversion/anti-issuance specific 채널** = PARTIAL_CONFIRMED 자격. (redundancy 아님 = "breadth 안 쟀으면 놓쳤을 신호" 사용자 직관 적중).
  - ★부호 정직 박제: IC 양 = anti-issuance(Pontiff-Woodgate 음 ★반대) = defensive 자사주 비싼값 매입=가치파괴→저forward. ★문헌 반대지만 sleeve 내 ep anti-value 와 ★부호 정합(cluster 일관) = hedge 박제. 직교화 결과 _breadth_sweep.json `net_issuance_orthogonalize` 박제.
- ★**verdict 확정 = PARTIAL_CONFIRMED**(net_issuance incremental FDR 생존). hedge 3: 부호 vs 문헌 반대 / comm 4종 small-n sign flip / OOS·cross-market 미검증. ⛔confirmed 강력 금지. candidate-ledger(rule=net_issuance + sleeve PARTIAL + observe-only OOS) + summary/15axis 반영.

## 미해결 / 다음 세션 우선 작업
1. ✅ S1 리서치 / theory-notes / candidate-ledger / research-log
2. ✅ §2 측정(collect 17 concept + measure sector-neutral) → BY 0 + anti-value 발견 → G-B 보고
2b. ✅ G-B 자체검증 3종(regime split + quality partial + LOO) → ep=부분본질 / payout=QE artifact
2c. ✅ G-B 자문 수렴(sleeve INSUFFICIENT / ep TENTATIVE_DIRECTIONAL regime-cond / payout rejected_provisional) + leave-sub-sector(healthcare 비의존)
3. ✅ 4 산출물: summary.yaml(verdict INSUFFICIENT + cross_market_implication G-E) + 15axis-audit(G-A.1~G-A.6 3컬럼+S3 자문+A-4+G-B 섹션, G-C 비워둠) + candidate-ledger 최종(verdict 확정+enum+G-B 자문 매핑) + research-log
   - ★C축 추적성 검증: summary.yaml 수치 = validation-metrics-v3.json + _gb_verify.json 1:1 일치 확인(ep −0.056 t−2.2 / payout −0.083 / BY [] M_eff 26.0 / real_rate β−0.066 / regime split).
4. ✅ team-lead 완료 보고 → G-C 독립 audit 스폰됨(15axis line 138~ 작성). ★G-C PASS (CONDITIONAL: 박제 정정 4종).
5. ✅ ★G-C 박제 정정 4종 반영 완료(2026-06-04, 정량 격하 아님 = 정직성/coverage 정정):
   - (1) D축 negative PIT lag 1건/111140(WMT cash end 오태깅, filed 기준 노출이라 직접 lookahead 아님, us_cyclical 0건 대조) → 15axis D축 + summary C/D 박제.
   - (2) O축/G-A.4 gross_prof coverage: "utilities/comm COGS 부재 N/A" 부정확 → utilities 5종(DUK/PEG/SO/WEC/XEL 203obs IC+0.036)·comm 3종(T/TMUS/VZ 111obs) COGS fallback partial-coverage 정정(staples/healthcare 주력). gross_prof INSUFFICIENT 결론 불변. research-log line 31/36/68 "측정 불가"(NEE 1종 probe 일반화 오류) 정정.
   - (3) ep hedge 어휘: "regime-robust" → "sign 일관(consist True), value-revival epoch n=41 t−1.29 block-boot CI[−0.075,+0.006] 0포함 비유의 = magnitude robust 아닌 sign robust" (summary hedge_note/notes/verdict + 15axis author 본문).
   - (4) power framing: "n=48 power 0.53"(종목 단면) 옆 "n_months=185 post-hoc power 0.59" 병기.
   - ★verify: WMT lag −279 1건 + utilities COGS 5종 203obs + ep value-revival CI[−0.075,+0.006] raw 재확인 완료.
6. ⏳ (후속) collector_plan: survivorship/PIT 멤버십 high + quality 통제 다요인(FF5+QMJ neutralize, ep anti-value 잔존 정밀) + cross-market 검증 medium
