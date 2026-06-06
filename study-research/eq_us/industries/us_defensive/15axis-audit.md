<!-- author: us-defensive teammate (재작업 2026-06-03, sector-neutral z + G-B 자문 수렴) -->
<!-- ★본 파일 = G-A self-audit 초안 (author 작성). G-C 독립 audit = 별도 세션(author != auditor)이 하단에 추가 -->
<!-- audit_date: 2026-06-03 -->

# 15axis-audit.md — us_defensive sleeve §M v3 (frame v3 §E, A~P 15축) — ★재작업 sector-neutral + anti-value

> ★재작업 = (1) S1 신규 신호(EDGAR 17 concept: payout/CFO 포함) (2) 자문 R2 4수정 (3) sector-neutral z (4) ★G-B 트리거(BY 0/48) → 자체검증 + G-B 자문 수렴 = sleeve INSUFFICIENT.
> raw 재현 = `raw-v3/{collect,measure}.py + _gb_self_verify.py` → `validation-metrics-v3.json + _gb_verify.json`. Hard-fail 코어: **B·C·D·I** + 조건부 J~P.

## G-A.1 — 15축 (A~P) 3컬럼 (① 적용했나 ② 측정법·코드/수치 경로 ③ 결과·판정)

| 축 | ① 적용 | ② 측정법·경로 | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론 실재 | YES | S1 학술 ground theory-notes.md. Frazzini-Pedersen(2014 JFE)/Novy-Marx(2013 JFE)/Boudoukh(2007 JF)/Basu(1977 JF)/Gormsen-Lazarus(2023 JF)/Ball et al.(2015 JFE)/Fama-French(1989 JFE) 환각검증 CONFIRMED 14. archetype valid_from 2010-01 사전선언. | **PASS** — defensive 신호(low-vol/quality/payout/value/duration) 1차 문헌 ground. |
| **B**★ 실데이터 | YES | 합성 0%. yfinance 48종(2010~) + EDGAR XBRL **17 concept 111140 rows**(filed PIT, dei fallback) + FRED(HY/baa_aaa/real_rate/rate/vix) + DXY. collect.py 재현. | **PASS** — cfo/assets 48/49, dividends 47, repurchase 45, shares 47(dei). |
| **C**★ 추적성 | YES | yaml 수치 → validation-metrics-v3.json + _gb_verify.json key 1:1. ep_yield 12M IC −0.056 / payout −0.083 / regime split(QE −0.061→2022+ −0.040) / sector_z_decomposition / src_concept 박제. | **PASS** — yaml↔raw 매핑·regime split·src_concept 추적. |
| **D**★ PIT | YES | 가격 forward-shift(shift(-h)) safe. valuation/payout/CFO = EDGAR filing acceptance date(filed) 이후만(`_latest_pit`/`_ttm` filed_dt<=dt). 거시 FRED. ★negative filed−end lag = **1건/111140**(WMT cash end 2012-12-31 vs filed 2012-03-27 lag−279 = end 오태깅 quirk). | **PASS** — lookahead 회피(Large accel 60d/40d 자동). ★코드는 filed 기준 노출(filed_dt<=dt)이라 negative lag 1건도 직접 lookahead 아님(us_cyclical 0건과 대조, data quirk 박제). |
| **E** 자문 환각 | YES | S1 citation 16개 Gemini 교차검증: 14 CONFIRMED + 2 CORRECTED(Ball et al. "Defensive Equity JFE 119"→**"Deflating Profitability" JFE 117(2)** / Greenwood-Vayanos reach-for-yield 출처 약화). archive raw 박제. | **PASS** — 환각 2건 정정 박제. |
| **F** 반증+기각 | YES | falsifier = reject_signal(e-CUSUM). 기각 결과: **payout/dividend rejected_provisional**(regime FLIP QE −0.122→2022+ +0.054 = reach-for-yield QE artifact) / per/earnings_cv/gross_prof INSUFFICIENT / momentum 무효. | **PASS** — falsifier 정의 + 실제 기각(payout regime flip / per unstable). |
| **G** 검정력·tier | YES | n_effective(185mo) + ts_eff_n(eff_N 이중보정 T/h) + breadth_ir. ★comm_mature 4종 = within-sector small-n hedge 라벨. ★BY 0/48 = 검정력 충분하나 신호 약. | **PASS** — tier 라벨 + small-n hedge + BY 0 정직. |
| **H** 미해결 의문 | YES | collector_plan: survivorship(high) + PIT 멤버십(high) + quality 통제 다요인(medium, ep anti-value 잔존 정밀) + cross-market 검증(medium) + accruals(low). candidate-ledger 연결. | **PASS** — 미해결 ledger 연결. |
| **I**★ 생존편향 | YES | universe = 현 ETF holdings 큐레이션(생존 종목). 상폐/M&A(staples/utility 합병) 누락. yfinance 단독 = 상폐 ticker 누락. | **PARTIAL** — 정직 격하, SSGA historical = collector_plan high. |
| **J** 경제성·거래비용 | YES | US net-cost = commission 0.0005 + spread/2 0.0003 = 왕복 16bps(STT 없음). ★단 cross-sectional 신호 BY 미생존 = factor-tilt 부적절 → long-only net 미산출(채택 신호 없음). | **PASS** — net-cost 모델 정의, 단 채택 alpha 부재(INSUFFICIENT). |
| **K**★ 다중검정 | YES | ★family_1 BY + M_eff(Li-Ji eigenvalue, test-stat 상관행렬). raw m=48 → M_eff=26.0. threshold 0.000998. ★survivors=0(raw_p_min 0.0174 ep 3M > thr×2 = G-B 트리거). nondegenerate strip=0. | **PASS** — M_eff BY 적용, 생존 0 정직(G-B 트리거 발동). |
| **L** 통합 상관 PSD | YES(보고만) | common_factor_exposure = β 보고만(real_rate/vix/dollar/rate/hy_oas/baa_aaa). 통합 supervisor L축 1회 계상. | **PASS** — sleeve=보고만. |
| **M**★ wire 충실 | YES | score_ic_breakdown_eprocess(confidence_hooks) = weight_falsification 호출. measure.py opt-in, production 미변경. cs_z(secmap) 단일산업=byte-identical. | **PASS** — opt-in, 단일산업 무회귀. |
| **N**★ cross PSD | N/A | cross 조립(RegimeGlasso/DY) = supervisor. directional_spillover=[]. | **N/A** — supervisor 몫. |
| **O**★ leakage | YES | forward=shift(-h). valuation/payout=filed date 이후만. reject≠missing: 적자/결측 valuation NaN(missing) tri-state 정직 제외. ★gross_prof = staples/healthcare 주력 + **utilities 5종(DUK/PEG/SO/WEC/XEL 203obs)·comm 3종(T/TMUS/VZ 111obs) COGS fallback partial-coverage**(NaN tri-state, silent 0 아님). | **PASS** — PIT-safe + tri-state. ★gross_prof partial-coverage(전부 부재 아님). |
| **P** net-cost robustness | YES | US 왕복 16bps. ★채택 unconditional 신호 부재(BY 0) = net 후 생존 신호 없음. ep anti-value = regime-conditional only. | **PASS** — net robustness 평가, INSUFFICIENT 정합(채택 alpha 부재). |

→ **Hard-fail 코어 B·C·D = PASS, I = PARTIAL(정직 격하). M·O = PASS, N=N/A. hard-fail 0.**

## G-A.2 — 6단계 (S1~S6) 산출물 경로 + 1줄 결과

- **S1** 학술 ground: `theory-notes.md` + `candidate-ledger.md`(Gemini 2-Phase Pro+Flash + citation 환각검증). → low-vol/quality/payout/value/duration 발굴, ep_yield/payout/Baa-Aaa 채택.
- **S2** 실측 4게이트: `measure.py` G1 ex-ante(valid_from 2010) / G2 **BY-FDR + M_eff**(family 3분리) / G3 CPCV(purge=h+embargo) / G4 NW-HAC(+block-boot). → ★BY 생존 0/48(G-B 트리거).
- **S3** 외부검토: S1 자문(consult-us-method R1/R2) + ★**G-B 자문(gemini-web+claude-web 병렬, 2026-06-04)** + frame §M.7/§M.12 대조. → sleeve INSUFFICIENT + ep TENTATIVE regime-conditional 수렴(G-A.6 참조).
  - 자문 수렴 SSOT = `D:/projects/Inv/.consult-us-defensive-R1-results.md` (수렴 요약 + verdict 표).
  - 자문 raw 전문 = `~/.claude/.gemini-web-last.md` + `.claude-web-basic-last.md` 의 **tail(2026-06-04 항목, append 방식 = head 는 옛 항목)**.
- **S4** 재검증: ★regime split(QE vs value-revival, 핵심 falsifier) / quality partial-corr / LOO-year / leave-sub-sector / sector-z 3분해. → ep anti-value sign 일관(value-revival 비유의), payout QE artifact.
- **S5** 역공격: "anti-value = QE regime artifact" 최강 반증 직접 투척 → regime split(2022+ 부호 유지) + leave-sub-sector(healthcare 비의존)로 ep 는 부분 본질 입증, payout 은 QE artifact 확정.
- **S6** ★15축 독립 audit = **G-C 별도 세션**(본 파일 = author self-audit 초안, 하단 G-C 미작성 = 독립 teammate 몫).

## G-A.3 — cross 3종 (sleeve=보고만)

- **동시 RegimeGlasso**: common_factor β 보고만(real_rate −0.066/vix −0.0039/dollar −0.58/rate −0.028/hy_oas −0.018/baa_aaa −0.005) → supervisor Σ_return. ★real_rate 듀레이션 = QUALIFIED sleeve 본질.
- **방향성 Diebold-Yilmaz**: directional_spillover=[] (supervisor 통합).
- **구조 supply-chain**: defensive = macro(duration/credit) regime dominant, skip(AI capex = us_mega_tech T0).

## G-A.4 — ★sub-sector 부호 일관성 (team-lead 신설 게이트, ★dividend-yield sign flip 점검)

| 신호 | staples | utilities | healthcare | comm_mature | 판정 |
|---|---|---|---|---|---|
| **ep_yield** (TENTATIVE anti-value) | −0.074 | −0.033 | −0.072 | −0.165 | ★전 4 음 일관(anti-value). comm −0.165 = small-n hedge(4종). LOO leave-sub-sector ex_health −0.062(healthcare 비의존). **슬리브 유지** |
| **payout_yield** (rejected) | −0.079 | −0.091 | −0.091 | −0.153 | ★전 4 음(full-period) but ★regime FLIP(2022+ 양 역전) = QE artifact. cancel 아닌 regime artifact |
| **dividend_yield** (rejected) | −0.067 | −0.051 | −0.102 | −0.254 | 전 4 음(full) but regime FLIP. ★sub-sector cancel 아님 = sign flip 은 regime(시간) 축이지 sector 축 아님 |
| per_z (INSUFFICIENT) | +0.076 | +0.020 | +0.069 | +0.085 | 전 4 양(value 역방향 일관) but regime unstable |
| **gross_prof** (INSUFFICIENT) | +0.059 | +0.036(n76) | −0.081 | (comm 4종<min, sub_sector_sign 제외) | ★partial-coverage(COGS fallback): utilities 5종 203obs(IC +0.036)·comm 3종 111obs 실측 + staples/healthcare 주력. staples +0.059/util +0.036/health −0.081 = 약·부호 불일치 = INSUFFICIENT 불변 |
| vol_60 (약) | +0.062 | −0.004 | +0.032 | +0.190 | comm +0.190(저변동성 프리미엄, small-n) but unconditional 약 |

→ ★**dividend-yield sub-sector sign flip 점검 결과 = cancel 아님**. payout/dividend 의 sign 역전은 ★**regime(시간) 축**(QE −0.122 → 2022+ +0.054)이지 sub-sector 축 아님(전 4 sub-sector full-period 동부호). = **슬리브 분리 트리거 없음**. gross_prof 는 partial-coverage(COGS fallback, staples/healthcare 주력 + utilities 5종·comm 3종 일부 실측, NaN tri-state) = INSUFFICIENT 무신호(부호 불일치). defensive = 슬리브 단위 유지 확정. ★ep anti-value = leave-sub-sector(ex_health −0.062) = healthcare 의존 아닌 sleeve-wide.

## G-A.5 — ★sector-neutral mechanism (검증 b, ★us_cyclical 와 대조 = 무회복)

> us_cyclical 은 sector-neutral 으로 BY 0→8 회복(sector-mixing 결함교정). us_defensive 는 ★무회복(BY 0 유지) = 신호 본질이 약/역방향.

**sector-z 3분해** (measure.py `sector_z_decomposition`, validation-metrics-v3.json `verify_b`):

| 신호 | universe-z IC | sector-neutral-z IC | sector-LEVEL-component IC | cross-std |
|---|---|---|---|---|
| pbr 12M | +0.021 | +0.016 | +0.009 | 0.959 |
| pbr 24M | +0.035 | +0.043 | +0.034 | 0.959 |
| per 24M | +0.019 | −0.005 | +0.062 | 0.961 |
| ep_yield 12M | −0.057 | −0.056 | −0.041 | 0.963 |
| payout 12M | −0.069 | −0.083 | −0.055 | 0.962 |

★**mechanism 규명 (us_cyclical 와 대조)**: us_cyclical 은 within-sector value(−0.117) vs sector-LEVEL value(+0.140 부호반대) = universe-demean 이 두 반대성분 mixing 희석 → sector-neutral 이 sector-level trap 제거로 BY 0→8 회복. ★us_defensive PBR = uni +0.021 / secN +0.016 / sectorLevel +0.009 = **세 성분 모두 약·동부호** = sector-mixing 희석 아님 = PBR 자체가 within-sector 도 약/역방향(buyback book 왜곡 noise-trap, 문헌). ep_yield 도 uni −0.057 ≈ secN −0.056 = sector-neutral 효과 미미(anti-value 가 within·universe 동일). cross-std 0.959~0.963≈1 = over-neutralize(신호 소멸) 아님.
→ ★**sleeve별 sector-neutral 효과 상이 = us_cyclical(결함교정 회복) ↔ us_defensive(무회복, 본질 약)**. = sector-neutral 은 다중-sector sleeve 공통 의무이나, 효과(회복 여부)는 신호 구조 의존.
> ★G-C hedge: comm_mature 4종 = within-sector z 가 매월 4점 = small-n(magnitude over-claim 금지, 방향만). sector-LEVEL component 도 n_sector=4 (매월 4점) = magnitude 약 근거. cross-std≈1 로 over-neutralize 우려는 기각, 단 small-N 우려 잔존(hedge).

**검증(a) sub-sector N**: staples/utilities/healthcare 각 static 15종(월별 median 10~13), ★comm_mature 4종(within-sector small-n hedge). gross_prof = staples/healthcare 주력 + utilities 5종(203obs)·comm 3종(111obs) COGS fallback partial-coverage.

**검증(b 한국 무회귀)**: 단일산업 = sector-neutral == universe-demean byte-identical (us_cyclical battery diff 0.00e+00 입증, 동일 코드 cs_z). 한국 7산업 sector-neutral 전환 무회귀.

## G-A.6 — ★G-B 트리거 + 자체검증 + 자문 수렴 (team-lead 신설)

> ★BY 0/48 = G-B 트리거. 단정 ⛔ → 자체검증(본질 vs artifact) → G-B 자문(gemini+claude) 수렴.

**G-B 트리거**: family_1 BY 생존 0/48 AND raw_p_min 0.0174(ep 3M) > threshold×2(0.002) = 충족. ⛔ "약함 단정" 안 함.

**자체검증 3종** (_gb_self_verify.py → _gb_verify.json):
1. **regime split (핵심 falsifier, QE 2010-2021 vs value-revival 2022-2026)**:
   - ep_yield: QE −0.061(t−1.95) → 2022+ −0.040(t−1.29) = ★**sign 일관**(consist True, 부호 유지) = anti-value 부분 본질. ★단 value-revival epoch n=41 block-boot CI [−0.075, +0.006] = **0 포함 비유의** = magnitude robust 아닌 **sign robust**(epoch 짧아 magnitude 약 hedge).
   - payout/dividend: QE −0.122/−0.120(t−2.86/−2.67) → 2022+ **+0.054/+0.096** = ★FLIP 역전 = reach-for-yield QE artifact.
2. **quality partial-corr**: ep raw −0.056(t−2.2) → gross_prof 통제 partial −0.051(t−1.55) = 거의 잔존(quality proxy 아님, anti-value 독립). t 약화(quality 미통제 한계).
3. **LOO-year + leave-sub-sector**: ep sign_stable=True(2020 COVID 비의존) + leave-sub-sector ex_health −0.062(healthcare 비의존, sleeve-wide).

**G-B 자문 수렴 (gemini-web + claude-web 병렬, team-lead 실행)**:
| 대상 | 등급 | 근거 |
|---|---|---|
| **us_defensive sleeve** | ★INSUFFICIENT | cross-sectional factor-tilt 부적절(BY 0/48 + 단일 QE 표본 + comm small-n). sleeve alpha = macro overlay |
| **ep_yield anti-value** | ★TENTATIVE_DIRECTIONAL (regime-conditional) | ★sign 일관(consist True, magnitude 비유의=sign robust) + yield-trap 부분 구조. ⛔unconditional 금지. quality축 미통제 한계 |
| **payout/dividend** | ★rejected_provisional (PROHIBITED) | reach-for-yield artifact, 부활 트리거 Fed<2%/VIX>25/HY>300bp |
| per_z/earnings_cv | INSUFFICIENT (unstable) | regime flip |
| **duration/credit overlay** | ★QUALIFIED = sleeve 본질 | real_rate β−0.066 robust = family_3 driver, supervisor regime overlay |

★**자문 추가 지적 반영**:
- (claude) **power analysis**: ★종목 단면 n=48 t−2.2 → power ≈0.53 / ★측정 단위 n_months=185 post-hoc power ≈0.59 (병기) = BY 미생존의 통계적 근거(검정력 부족). = sleeve INSUFFICIENT 정합.
- (claude 단독) **healthcare 40% 지배 위험** → ★leave-sub-sector 자체검증으로 **기각**(ex_healthcare −0.062 = 오히려 강, sleeve-wide). author 의 sub-sector 음 일관 보고가 정확.
- (양 모델 공통) **누락 측정축**: interest coverage / regulated asset base(utilities) / ★quality-adjusted value(ep anti-value 의 quality 50% 미설명) / explicit duration = collector_plan(quality 통제 다요인 medium).
- (gemini) sector-neutral 무회복 = "defensive 내 cross-sectional peer-relative value 자체가 초과수익 원천 아님"(cyclical=외부 macro로 sector 이익 요동→secN 유효 / defensive=개별 펀더멘털 절대적) = G-A.5 mechanism 정합.

## G-A.7 — ★B″ lock-blocking 게이트 (STEP 1~3 + STEP 4 add, 자문 3R 대안 B″)

> 현 `regime_conditional()`(baa_aaa quintile split) = frame line 323 위반 → `_payout_interaction.py`(split→continuous interaction) + 공용 `_b2_stats.py`(effective_n/fixed-b CV/wild-cluster/Ridge λ PIT) + `_step4_add_factors.py`(단일 FDR family). measure.py 미변경(byte-identical 보존).

**STEP 1 (④ duration-orthogonalize → credit interaction)**: payout-premium return → ★FWL 직교화(order=duration 먼저: payout~ΔReal_rate β_dur=0.016 t0.47 비유의) → ΔReal_rate **continuous interaction**(split 폐기, mega_tech regime_interaction 이식) → credit(baa_aaa) 적층.
**STEP 2 (②⑤⑦)**: effective_n = n/(1+2Σρ_k) NW VIF(n=185 → n_eff 44~83) + ★per-test calibration = fixed-b CV(Kiefer-Vogelsang 2005) + wild-cluster(block) bootstrap = size-valid + 단일 FDR family.
**STEP 3 (⑥)**: Ridge λ = expanding-window PIT 동결(train 60% CV → eval 미접촉) + λ∈{0.1λ*,λ*,10λ*} 3점 hedge → sign_stable=True.

**★핵심 결과 — payout interaction (split→continuous + size-valid)**:
| | regime split (G-A.6) | B″ continuous interaction |
|---|---|---|
| payout 12M | QE −0.122 t−2.86(유의해 보임) → 2022+ +0.054 FLIP | IC~ΔReal_rate β0.028 t_asy0.43 / ★**fixed-b CV 2.09 비유의** / wild-cluster p0.68 |
| 판정 | rejected_provisional | ★**NO_INTERACTION**(직교 전부터 비유의) |

→ ★split 의 QE t−2.86 이 size-valid continuous interaction 에서 소멸 = (a) garden-of-forking-paths(사후 가설) + (b) small-block NW asymptotic over-rejection(size-invalid) artifact = ★**자문 R3 Claude "size-invalid" 경고 정확 실증**. payout rejected **강화**(armed-pending 미진입, 자문 prediction "회생 가능"과 다른 정직 결과).

**★STEP 4 add (단일 FDR family: ep_yield + idio_vol + residual_mom, 9 test, M_eff=7.0)**:
| 신호 | IC | t | fixed-b size-valid | FDR family |
|---|---|---|---|---|
| ep_yield 3M/6M/12M | −0.039~−0.056 | −2.4~−2.6 | ★**유의**(CV 2.08~2.09) = anti-value artifact 아님(power 우려 반박) | ❌ 미생존 |
| residual_mom 12M | +0.039 | +2.55 | ★유의(개별) | ❌ (6M/3M 약) |
| idio_vol 전 horizon | +0.01~+0.02 | 0.46~0.73 | 무신호 | ❌ |

→ ★STEP 4(9 test) 단일 FDR family BY 생존 0. 단 ep_yield fixed-b size-valid 개별 유의 = TENTATIVE 등급 지지. residual_mom = 신규 TENTATIVE. ★단 breadth 전수 미측정 = G-A.8 보강(사용자 지적).

## G-A.8 — ★breadth 전수 sweep + net_issuance (사용자 지적 = 우선순위만 측정 갭, verdict 격상)

> 사용자 지적 "변경된 B″ 프레임으로 후보 전수 검토했나" → residual_mom/idio_vol 만 측정 = 갭. breadth 6 신규 전수 측정(`_breadth_sweep.py`, fetch 0). 신규 6 + 기존 ep/idio/rmom = 27 test 단일 FDR family.

**측정 6종 (Pontiff-Woodgate/George-Hwang/Amihud/FF2015/Sloan)** + 직교화 검증:
| 신호 | IC(12M) | t | fixed-b size-valid | 단일 FDR family(27test M_eff19) |
|---|---|---|---|---|
| ★**net_issuance** 3M/6M/12M | +0.082 | 3.31~4.40 | ★유의 | ★★**생존**(raw_p 3e-05 < threshold 0.0015) |
| amihud 12M | +0.078 | 1.98 | 경계 | ❌ |
| high_52w/op_profitability/roe/accruals | ~0 | <1.1 | 무신호 | ❌ |

**★net_issuance robustness + 직교화(advisory §1, 채택 전 자체 시뮬)**:
- regime split QE +0.087 → 2022+ +0.067 = ★부호+magnitude 유지(payout FLIP 과 다름) + LOO stable(+0.066~+0.099) + sub-sector staples+0.117/util+0.081/health+0.064 양, comm_mature −0.121(4종 small-n).
- ★**직교화 = INCREMENTAL**: ⊥ep_yield(anti-value) partial IC 12M+0.084 t3.71 size-valid 잔존 / ⊥payout(자사주 채널) partial IC 12M+0.055 t2.41 size-valid 잔존 = ★anti-value cluster(ep) + buyback 채널(payout) 모두 직교 후 잔존 = **buyback-aversion specific 채널**(redundancy 아님).
- ★부호 hedge: IC 양 = anti-issuance(Pontiff-Woodgate 2008 음 ★반대) = defensive 자사주 비싼값 매입=가치파괴→저forward. 문헌 반대지만 sleeve 내 ep anti-value 와 ★부호 정합(cluster 일관). payout corr −0.53(직교 후 잔존).

→ ★**verdict INSUFFICIENT → PARTIAL_CONFIRMED 격상**(net_issuance incremental FDR 생존). hedge: 부호 vs 문헌 반대 / payout 중복 / comm small-n / OOS·cross-market 미검 = ⛔confirmed 강력 금지. ★SUE-PEAD 이연(8-K Item 2.02 furnish date anchor = EDGAR 8-K 파싱 데이터게이트). ★"breadth 안 쟀으면 놓쳤을 신호" = 사용자 직관 적중.

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (EDGAR 17 concept 111140 rows, payout/CFO, dei fallback) |
| C 추적성 | PASS | yaml↔raw 매핑 + regime split + src_concept |
| D PIT | PASS | filed-date PIT(valuation/payout/CFO) + forward shift |
| I 생존편향 | PARTIAL | 현 holdings 큐레이션, 정직 격하 |
| M wire | PASS | opt-in, 단일산업 byte-identical |
| N cross PSD | N/A | supervisor 몫 |
| O leakage | PASS | PIT-safe + reject≠missing tri-state(gross_prof partial-coverage, utilities/comm COGS fallback 일부) |

★**hard-fail 0** (B/C/D/M/O PASS, I PARTIAL=정직 격하, N=N/A).

## verdict (self-audit 초안)

- **status = PARTIAL_CONFIRMED** (★breadth sweep 후 격상, 직전 INSUFFICIENT) — net_issuance 단일 FDR family BY 생존 + incremental(직교 후 잔존) = cross-sectional alpha 존재. 단 net_issuance 1개 + 부호 문헌 반대 + payout 중복 + OOS 미검 = PARTIAL.
- ★핵심 = 미국 defensive cross-sectional value/quality/payout 약·역방향(cyclical PBR value 반대) but ★net_issuance(anti-issuance/buyback-aversion) = 첫 FDR-생존 신호.
- **net_issuance = PARTIAL_CONFIRMED (primary)** — anti-issuance(IC+0.082 t3.31~4.40, 단일 FDR family BY 생존 + fixed-b size-valid + incremental ⊥ep/⊥payout 잔존 + regime 유지 + LOO). hedge: 부호 vs Pontiff-Woodgate 반대 / payout −0.53 중복 / comm small-n / OOS 미검.
- **ep_yield anti-value = TENTATIVE_DIRECTIONAL(secondary)** — ★sign 일관 + LOO + leave-sub-sector 안정, fixed-b size-valid 개별 유의 but FDR 미생존 + quality 미통제.
- **payout/dividend = rejected (B″ NO_INTERACTION)** — reach-for-yield QE artifact + split size-invalid 입증. residual_mom = TENTATIVE(STEP 4 add).
- ★dominant = real_rate 듀레이션 β−0.066(family_3, QUALIFIED) = macro overlay. ★sector-neutral 무회복(us_cyclical 대조).
- ★cross-market = 한국 value premium 정방향과 불일치 = 묶음 단위 시장 의존(anti-value 이식 불가, duration/payout-regime 이식 가능).

---

## ★G-C 독립 audit (별도 세션 = author ≠ auditor, team-lead 스폰 예정)

> 본 섹션 = G-C 독립 teammate 작성 영역. author(us-defensive)는 미작성.
> 1순위 검증 = ★anti-value regime-conditional 정직성(BY 0 + regime split consist) + sector-neutral 무회복(us_cyclical 대조) + payout QE artifact regime FLIP + hard-fail B/C/D/I+M/N/O = 0.
> 입력 = 본 self-audit 초안 + validation-metrics-v3.json + _gb_verify.json(regime split/quality partial/LOO/leave-sub-sector) + measure.py + _gb_self_verify.py.

<!-- author: us-defensive-audit teammate (G-C 독립 세션, Opus 1m, 2026-06-03). author(us-defensive)와 별개. -->
<!-- raw 재계산 = raw-v3/_gc_audit_recompute.py + _gc_audit2.py (measure.py 함수 재사용 + raw parquet 재산출). ⛔ 산출 수정 0. -->

> **독립성 선언**: self-audit 초안 결론 + G-B 자문 verdict 를 검증 없이 복붙하지 않고, validation-metrics-v3.json + _gb_verify.json 의 핵심 정량(IC/NW-t/BY/M_eff/regime split/leave-sub-sector/quality partial/sector-z 분해/family_2·3/byte-identical/EDGAR rows/PIT lag)을 raw 데이터(prices/edgar/macro/universe.parquet)로 **재계산**해 대조함. ⛔ 코드·산출 수정 0 (별 스크립트 stdout 만).

### 0. 검증 방법 — author 핵심 수치 재현 여부 (선결)

| 항목 | author json/yaml | 독립 재계산 | 일치 |
|---|---|---|---|
| ep_yield 3M IC / t / p | −0.0385 / −2.40 / 0.0174 | **−0.0385 / −2.40 / 0.0174** | ✓ |
| ep_yield 12M IC / t | −0.0560 / −2.20 | **−0.0560 / −2.20** | ✓ |
| payout 12M IC / t | −0.0828 / −2.10 | **−0.0828 / −2.10** | ✓ |
| per_z 3M IC / t | +0.0381 / +2.28 | **+0.0381 / +2.28** | ✓ |
| raw_m / M_eff (Li-Ji) | 48 / 26.0 | **48 / 26.00** | ✓ |
| BY rank1_thr (M_eff) | 0.000998 | **0.000998** | ✓ |
| survivors_BY (M_eff) | [] (0/48) | **[]** | ✓ |
| raw_p_min > thr×2 (G-B trigger) | 0.0174 > 0.002 = True | **True** | ✓ |
| regime split ep 12M (QE / 2022+ / consist) | −0.0607 / −0.0396 / True | **−0.0607 / −0.0396 / True** | ✓ |
| regime split payout 12M (QE / 2022+ / consist) | −0.1217 / +0.0538 / False | **−0.1217 / +0.0538 / False** | ✓ |
| regime split dividend 12M (QE / 2022+) | −0.1202 / +0.0961 | **−0.1202 / +0.0961** | ✓ |
| leave-sub-sector ep 12M ex_healthcare | −0.062 (강) | **−0.0624** | ✓ |
| quality partial ep 12M (raw / partial) | −0.056 / −0.0508 (t−1.55) | **−0.056 / −0.0508 (t−1.55)** | ✓ |
| sector-z ep_yield 12M (uni / secN / sectorLvl) | −0.057 / −0.056 / −0.0411 | **−0.0570 / −0.0560 / −0.0411** | ✓ |
| sector-z pbr 12M (uni / secN / sectorLvl) | +0.021 / +0.016 / +0.009 | **+0.0209 / +0.0159 / +0.0086** | ✓ |
| family_2 ep high/low spread | −0.1038 / −0.0402 | **−0.1038 / −0.0402** | ✓ |
| family_3 real_rate β / t | −0.0655 / −6.78 | **−0.0655 / −6.78** | ✓ |
| EDGAR rows (filed/val non-null) | 111140 | **111140** | ✓ |
| 단일 sub-sector byte-identical | 0.00e+00 | **0.00e+00** (healthcare 15종) | ✓ |

→ ★**author 의 모든 핵심 정량 수치 = 독립 재현 성공.** 위조·날조·계산오류 0. self-audit 초안은 raw 와 정합. **단 2건 미세 불일치 발견**(아래 §3 D축·O축) = 정량 결론 격하 아닌 **박제 정정 권고**.

---

### 1순위 — anti-value 본질 vs QE artifact → **CONDITIONAL (verdict 정직, under-claim 방향 = 안전)**

**판정 = self-audit 의 anti-value verdict 3종(ep TENTATIVE_DIRECTIONAL / payout rejected_provisional / sleeve INSUFFICIENT)은 raw 와 정합하며 over-claim 없음.** 근거 5종:

1. **ep_yield anti-value = 부분 본질(regime-robust) 주장 = raw 지지, 단 "robust" 어휘 hedge 필요**.
   - regime split 재현: QE −0.0607(t−1.95, n144) → 2022+ −0.0396(**t−1.29, n41**) = 부호 유지(consist True). ★핵심: 2022+ epoch 의 t=−1.29 + block-boot CI **[−0.075, +0.006] = 0 포함 = 비유의**. → "regime-robust" 는 **부호 일관성**이지 **유의성 유지가 아님**. self-audit 이 verdict 를 CONFIRMED 가 아닌 **TENTATIVE_DIRECTIONAL** 로 격하한 것 = small-n rule §2 정합 (정직). yaml notes 의 "regime-robust" 표현에 "(부호만 유지, value-revival epoch n=41 비유의)" hedge 부착 권고.
   - LOO-year sign_stable=True (ex-range [−0.0703, −0.0444], 2020 COVID 비의존) = 재현.

2. **payout/dividend = reach-for-yield QE artifact = raw 강력 지지**.
   - payout regime FLIP: QE −0.1217(**t−2.86 유의 음**) → 2022+ +0.0538(t1.27, 비유의 양) = QE era 한정 유의. dividend FLIP QE −0.1202(t−2.67) → 2022+ +0.0961(t1.15). → full-period 음(−0.0828)은 QE era 가 표본 73%(144/185)를 차지해 끌어낸 것. **rejected_provisional(PROHIBITED) + 부활 트리거(Fed<2%/VIX>25/HY>300bp) verdict 타당.** over-claim 없음 (오히려 QE era 유의 음을 "확정 음 신호"로 박제하지 않고 regime artifact 로 격하 = 정직).

3. **leave-sub-sector = healthcare 지배 위험 기각 = raw 재현**.
   - ep_yield 12M full −0.056 → ex_healthcare −0.0624 / ex_staples −0.0600 / ex_utilities −0.0591 / ex_comm −0.0508 = **4 leave 모두 음, ex_healthcare 가 오히려 약간 강**. claude 자문의 "healthcare 40% 지배" 가설을 raw 로 기각 = author 의 "sleeve-wide anti-value" 주장 정확. (6M 도 동일 패턴: full −0.0484 → ex_healthcare −0.0458, 4 leave 전부 음).

4. **quality partial-corr = anti-value 독립 잔존 = raw 재현, 단 t 약화 정직**.
   - ep 12M raw −0.056(t−2.2) → gross_prof 통제 partial −0.0508(**t−1.55, 비유의**) = quality proxy 아님(거의 잔존) but t 약화. ep 6M 은 raw −0.0484(t−2.03) → partial −0.0645(t−2.46) 오히려 강화. payout 12M partial −0.0588(t−0.99) = 약화(일부 quality 흡수). → self-audit 의 "quality 독립 잔존 but quality축 미통제 한계" = 정직. ★자문 공통 지적(quality-adjusted value 축 미통제, ep anti-value 의 quality 50% 미설명)이 collector_plan medium 으로 박제됨 = 정합.

5. **sector-neutral 무회복 = us_cyclical 대조 raw 재현**.
   - ep_yield 12M: uni −0.0570 ≈ secN −0.0560 ≈ sectorLvl −0.0411 = **세 성분 모두 약·동부호** = sector-mixing 희석 아님(us_cyclical pbr uni −0.047 / secN −0.117 / sectorLvl +0.140 부호반대와 ★대조). pbr 12M: uni +0.0209 / secN +0.0159 / sectorLvl +0.0086 = 세 성분 모두 약·동부호. cross-std 0.959~0.963 ≈ 1 = over-neutralize(신호 소멸) 아님. → author 의 "defensive 는 within-sector 도 약/역방향 = sector-mixing 주범 아님 = 신호 본질이 약" = raw 정합. gemini 자문의 "defensive cross-sectional peer-relative value 자체가 초과수익 원천 아님" 과 정합.

★**1순위 verdict = CONDITIONAL (anti-value verdict 정직, hedge 어휘 1종 보강 권고).**
- ep TENTATIVE_DIRECTIONAL / payout rejected_provisional / sleeve INSUFFICIENT 모두 raw 정합 + over-claim 없음. 오히려 verdict 격하가 보수적(under-claim 방향 = small-n rule 안전).
- ⚠️ hedge 권고: yaml `regime_split_consistent: true` 옆 ep_yield notes 의 "regime-robust" → "**부호 일관(consist True), 단 value-revival epoch n=41 t−1.29 비유의 = magnitude robust 아닌 sign robust**" 명시.

---

### 2순위 — BY / M_eff / G-B 트리거 + 자문 수렴 적절성 → **PASS**

- **M_eff=26.00 재현** (raw_m=48, Li-Ji eigenvalue, IC 시계열 상관행렬). BY rank1_thr(M_eff)=0.000998, raw_p_min=0.0174(ep_yield 3M). survivors=0/48 재현. nondegenerate strip(24M 제외)도 0. **G-B 트리거 조건**(BY 0 AND raw_p_min 0.0174 > thr×2=0.002) = **True 재현**.
- ★**G-B 자문 수렴 verdict over/under-claim 점검** (자문 raw tail = `.gemini-web-last.md` + `.claude-web-basic-last.md` 2026-06-04 항목 직접 대조):
  - **자문 등급 불일치 정직 처리 확인**: gemini 자문 (c) 는 sleeve 등급을 명시적으로 "**TENTATIVE_DIRECTIONAL (Regime-Conditional) 부여 타당, INSUFFICIENT 를 피해야 (Type II Error 위험)**" 로 권고함(관대). claude 자문은 sleeve INSUFFICIENT(보수). `.consult-R1-results.md` line 22 가 이 불일치를 정직 박제하고 "종합 = sleeve INSUFFICIENT (보수 우선, small-n rule 정합)" 채택 = ★**under-claim 방향 (안전). over-claim 아님.** gemini 의 관대한 등급을 채택하지 않은 것 = small-n rule §2 (n<30 단정 회피) 정합.
  - ep TENTATIVE_DIRECTIONAL = 양 모델 공통(claude L2 INSUFFICIENT+연구보존, gemini 부분본질+표본특수 50/50). 산출 정합.
  - payout rejected_provisional + 부활 트리거(Fed<2%/VIX>25/HY>300bp) = claude L1 ARTIFACT/kill + gemini "영구폐기 X, regime-conditional interaction term 보존" = 산출 정합.
  - duration QUALIFIED = 양 모델 "macro regime overlay(duration β−0.066 robust)" = family_3 real_rate t−6.78 재현 + 산출 정합.
- **power analysis(claude n=48 t−2.2 → power 0.53) 점검**: claude 의 "n=48" 은 종목 단일 단면 가정 = 측정 단위(시계열 IC 평균 t, n_months=185)와 다른 layer. 측정 t-stat 자체의 post-hoc power(α=0.05, ncp=|t_obs|=2.2) 재계산 = **0.59**. 자문 0.53 과 layer 는 다르나 결론(검정력 부족 → BY 미생존 정합) 방향 일치 = self-audit 이 이를 "BY 미생존 통계 근거" 로 흡수한 것 적절. ⚠️ 단 자문 "n=48" framing 을 측정 검정력으로 직접 등치하지 않도록 주의(현 박제는 "power≈0.53" 인용만 = 경미).

---

### 3순위 — hard-fail B/C/D/I + M/N/O 독립 재판정

| 축 | self-audit | 독립 재판정 | raw 근거 |
|---|---|---|---|
| **B** 실데이터 | PASS | **PASS** | EDGAR 111140 rows (filed/val non-null) 재현. 17 concept 실재(assets/capex/cash/cfo/cogs/dep_amort/dividends/equity/gross_profit/issuance/lt_debt/net_income/op_income/repurchase/revenues/shares/st_debt). 합성 0. panel cov 9종 재현(ep_yield 8380 등). |
| **C** 추적성 | PASS | **PASS** | yaml IC = json key 1:1 (ep −0.056 / payout −0.083 / BY [] / M_eff 26.0 / real_rate −0.0655 / regime split 전부 재현). |
| **D** PIT | PASS | **★CONDITIONAL** | 가격 forward-shift safe. valuation/payout/CFO = filed_dt<=dt 필터(lookahead 회피 mechanism 정상). ★단 **negative lag 1건 발견** = WMT cash end=2012-12-31 / filed=2012-03-27 (lag −279일, end 가 filed 보다 미래). self-audit/yaml 의 "lookahead 회피" 는 mechanism 상 맞으나 us_cyclical G-C(negative 0/94650) 와 달리 **"negative lag 0" 함의가 부정확**. 영향: _latest_pit 가 filed 기준이라 직접 lookahead 는 아님(filed 시점 노출), 단일 row(cash, ep/payout 핵심 신호 무관) = 영향 경미. **정정 권고**: D축 note 에 "negative lag 1건(WMT cash, EDGAR end 오기 추정, filed 기준 노출이라 lookahead 직접 아님)" 박제. |
| **I** 생존편향 | PARTIAL | **PARTIAL (정직, 동의)** | universe=현 ETF holdings 큐레이션=생존 종목. 상폐/M&A 누락 정직 격하. collector_plan high 등록 확인. over-claim 아님. |
| **M** wire | PASS | **PASS** | 단일 sub-sector(healthcare 15종) byte-identical 0.00e+00 재현. opt-in, production 미변경. |
| **N** cross PSD | N/A | **N/A (동의)** | cross 조립=supervisor 몫, directional_spillover=[]. |
| **O** leakage | PASS | **★CONDITIONAL** | forward=shift(−h), valuation=filed 이후만, reject≠missing tri-state(적자/결측 NaN). ★단 **gross_prof "utilities/comm COGS 부재 = NaN/N-A" 박제가 부정확**: raw 에 utilities **5종(DUK/SO/XEL/PEG/WEC) 459 obs** + comm **2종(VZ/TMUS) 372 obs** 실재(COGS fallback 으로 채워짐). G-A.4 sub-sector 표 "utilities N/A(COGS 부재)" + verify_b/sub_sector_sign 의 utilities IC=+0.0355(n76) 누락 = **tri-state 정직성 박제 정정 필요**(silent default 아닌 partial-coverage). 결론(gross_prof INSUFFICIENT 무신호)은 불변. |

→ ★**hard-fail 코어 B·C·M = PASS, D·O = CONDITIONAL(박제 정정 권고, 정량 영향 경미), I = PARTIAL(정직), N = N/A. hard-fail 실질 = 0** (D·O 의 CONDITIONAL = 위조/누락 아닌 박제 부정확 = framing 정정 수준, 핵심 신호 결론 불변).

---

### 4순위 — ledger(G-D) + cross-market + 자문 매핑 → **PASS**

- **candidate-ledger**: §측정결과 verdict 표(ep TENTATIVE / payout rejected_provisional / sleeve INSUFFICIENT) + falsifier 표(가설→기각 결과) + enum 5분류(rule 없음 / memory / observe-only / evt / pointer) 박제 확인. ★G-B 자문 raw→산출 매핑 "누락 0건"(verdict 6 + claude healthcare 1 + cross-market 1) = consult-raw-output-mapping-checklist 정합.
- **research-log**: G-B 트리거→자체검증→자문 수렴 시계열 박제. EDGAR/FRED 가용성 사전 probe(dispatch §1.1-ext) 박제. ★단 line 31/36 의 "utilities gross_prof 측정 불가(NEE 대표 probe)" 가 실측(5종 일부 채워짐)과 부분 불일치 = O축 정정과 연동.
- **cross-market 함의(G-E 입력)**: yaml `cross_market_implication` = "미국 anti-value ≠ 한국 value premium = 묶음 단위 시장 의존" + transferability(real_rate_duration YES / payout_regime_split PARTIAL / ep_anti_value NO). ★자문 raw 대조: gemini "한국 = LLY/COST 류 compounder 부재 = deep value/value trap = anti-value 이식 불가, Value-Up 으로 전통 value 작동 가능 / duration·payout regime 이식 가능", claude "한국 적용 연기 권장(n<20)" = **산출 매핑 정합, over-claim 없음**. G-E 묶음 자문 입력으로 타당.

---

### ★anti-value verdict 최종 (G-C 동의/정정)

★**ep TENTATIVE_DIRECTIONAL 타당 / payout rejected_provisional 타당 / sleeve INSUFFICIENT 타당 = 3종 모두 G-C 동의.**

- **over-claim 점검 통과**: anti-value verdict 가 raw 보다 강하게 박제된 곳 0. 오히려 (a) gemini 의 관대한 sleeve TENTATIVE 권고를 보수 INSUFFICIENT 로 채택 (b) ep_yield QE-era 유의 음을 CONFIRMED 아닌 TENTATIVE 로 격하 (c) payout QE-era t−2.86 유의 음을 "확정 신호" 아닌 regime artifact 로 격하 = **전부 under-claim 방향 = small-n rule 안전**.
- **under-claim 점검**: ep_yield 가 BY 미생존 + value-revival epoch 비유의인데 TENTATIVE_DIRECTIONAL(observe-only) 유지 = 과소 폐기도 아님(관찰 보존 + unconditional 금지 hedge = 적정).

---

### self-audit 초안과의 불일치

| 항목 | self-audit/yaml 박제 | 독립 audit 발견 | 등급 |
|---|---|---|---|
| **D축 negative PIT lag** | "negative lag 0" 함의(D PASS, lookahead 회피) | ★negative lag **1건**(WMT cash end 2012-12-31 / filed 2012-03-27, lag −279) = EDGAR end 오기 추정. filed 기준 노출이라 lookahead 직접 아님 = 영향 경미, 단 "0" 박제 부정확. | 박제 정정 (격하 아님) |
| **O축 gross_prof N/A** | "utilities/comm COGS 부재 = NaN tri-state, staples/healthcare 한정 sub-universe" (G-A.4 표 utilities/comm = N/A) | ★utilities **5종 459 obs** + comm **2종 372 obs** 실재(COGS fallback). utilities sub_sector_sign IC=+0.0355(n76) 측정됨 = "N/A" 부정확(partial-coverage). gross_prof INSUFFICIENT 결론은 불변. | 박제 정정 (격하 아님) |
| **regime-robust 어휘** | ep_yield notes "regime-robust" | ★value-revival epoch(2022+) n=41 t−1.29 + block-boot CI [−0.075, +0.006] 0 포함 = 비유의. "robust" = sign 일관이지 magnitude/유의성 robust 아님. | hedge 어휘 보강 권고 |
| **power 0.53 framing** | claude "n=48 t−2.2 → power 0.53" 인용 | ★n=48(종목 단면) ≠ 측정 단위(n_months=185, post-hoc power 0.59). 결론(검정력 부족) 방향은 정합. | framing 주의 (경미) |

→ ★모든 불일치 = **박제 정정 / hedge 보강 수준** (정량 결론 격하 0). 위조·날조·계산오류 0. self-audit 의 핵심 주장(BY 0/48 = G-B 트리거, anti-value verdict 3종, sector-neutral 무회복, hard-fail 코어)은 raw 로 전부 지지.

---

### verdict_label 판정 + G-C 추가 권고

★**INSUFFICIENT 동의 (G-C 독립 audit PASS, CONDITIONAL: 박제 정정 4종).** 근거:
- sleeve cross-sectional alpha 부재(BY 0/48 + M_eff 26.0 재현 + 단일 QE 표본 + comm 4종 small-n) = INSUFFICIENT 정당.
- ep_yield anti-value = TENTATIVE_DIRECTIONAL(observe-only) = regime consist True + LOO + leave-sub-sector 안정 but BY 미생존 + value-revival epoch 비유의 + quality 미통제 = 격하 정합.
- ⛔ TENTATIVE_DIRECTIONAL(sleeve) 로 승격 불가 — gemini 의 관대 권고에도 불구 claude 보수 + small-n rule 채택이 정확. INSUFFICIENT 가 상한.

★**G-C 추가 권고 (team-lead 전달, ⛔ 코드·산출 수정은 G-C 가 안 함)**:
1. **D축 정정**: hard_fail_self_check.D_pit.note + 15axis D축 ③ 에 "negative lag 1건(WMT cash, EDGAR end 오기 추정, filed 기준 노출이라 lookahead 직접 아님)" 박제. us_cyclical(0건)과 대조.
2. **O축/G-A.4 정정**: gross_prof "utilities/comm = N/A COGS 부재" → "utilities 5종(DUK/SO/XEL/PEG/WEC) 459obs + comm 2종(VZ/TMUS) 372obs 부분 coverage(COGS fallback), 나머지 NaN tri-state. utilities IC=+0.0355(n76) 측정됨" 정정. research-log line 31/36 의 "측정 불가" → "NEE 대표 probe = 측정 불가, 실측 시 일부 종목 COGS fallback 채워짐" 정정. (gross_prof INSUFFICIENT 결론 불변).
3. **hedge 어휘**: ep_yield notes/yaml `regime_split_consistent` 옆 "regime-robust" → "sign 일관(consist True), value-revival epoch n=41 t−1.29 비유의 = magnitude robust 아닌 sign robust" 명시.
4. **power framing**: "n=48 power 0.53" 인용 시 "(종목 단면 가정, 측정 시계열 n_months=185 post-hoc power 0.59)" 병기 권고.

→ 위 4종은 **정량 결론 격하가 아니라 박제 정정 / hedge 보강**. hard-fail 코어 실질 0, anti-value verdict 3종 정직(over-claim 없음, under-claim 방향 안전), BY 0/48 = G-B 트리거 확정 = **G-C 독립 audit PASS (CONDITIONAL: 박제 정정 4종 권고).**
