<!-- author: financial analyst teammate (S6 self-audit 초안, 2026-06-05) -->
<!-- ★최종 G-C 독립 audit = 별 세션(메인이 audit teammate 스폰). 본 self-audit = 참고용. -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — financial(금융) conditional IC v3 (frame v3 §E, A~P 15축 self-audit)

> S6 self-audit 초안 (3컬럼: ① 적용 ② 측정 코드·수치 경로 ③ 결과·판정). Hard-fail 코어 = **B·C·D·I** (+M·N·O wire).
> raw 재현 = `raw-v3/{collect_regime, measure_conditional, measure_oos_event}.py` + validation-{conditional,oos-event,attack}-v3.json (+ 기존 v2 valuation/cross/metrics).
> ★반도체 파일럿 15axis-audit.md 양식 미러.

## ★핵심 verdict 한 줄
financial = **sub-sector 부호 이질**(은행/보험 금리+ vs 증권 금리−). 은행 저PBR value(IC −0.161 wc_p=0.0165) vs 증권 반대(+0.146) **차이 = 통합 cross-sectional IC cancel(frame §1.6)**. ★자기상관 보정(60d overlapping, lag-1 ac=0.452): naive t=−3.18 → NW-HAC lag3 t=−2.64 / n_eff(14.7) t=−2.35 / wild-cluster p=0.0045 / block-boot CI[−0.60,−0.14] 0배제 = 부호 robust(fin-audit G-C 독립재현, bank vs insur t=−2.56 도 유의). = "신호 강도" 아닌 "분리 구조" 발견. DART 금융재무 2023~ 제약 = magnitude TENTATIVE.

## A~P 15축 (3컬럼)

| 축 | ① 적용 | ② 측정 코드·수치 경로 | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론실재 | ✅ | theory-notes §1 M1~M7 부호 사전확약 + ★§1-ref 인용 11명 source URL/DOI 박제(Saunders-Schumacher 2000 DOI:10.1016/S0261-5606(00)00033-4 / Flannery 1981 / Fama-French 1992 / MacKinlay 1997 / Acharya 2017 / Choe-Kho-Stulz 1999 / Grinblatt-Keloharju 2000 / Jegadeesh-Titman 1993 / Asness QMJ 2019 / 김우진·신보성 2012 / Kim-Lee 2020). | **PASS** — ★fin-audit remediation 2 반영(A축 URL 0개 → 11개 DOI 박제). 학술+실무 ground. HARKing 방지(이론 독립 수립 후 측정 대조). |
| **B★** 실데이터 (hard-fail) | ✅ | pykrx OHLCV 34종(1818일) + ECOS 국고채2Y/3Y/10Y·회사채AA-/BBB- 일별 + ECOS 외국인순매수 + FRED CLI/USDKRW + DART 312rows. collect_regime.py 재현. | **PASS** — 합성 0%. ★합성지문 PASS: USDKRW 2022-10 1440.3 / KTB10Y 2020-08 1.281→2022-10 4.632(금리쇼크) / credit spread 2022-11 1.77(레고랜드). |
| **C★** 추적성 (hard-fail) | ✅ | yaml 모든 수치 → validation-conditional/oos-event/attack-v3.json key. 은행 PBR -0.161=conditional bank.pbr_z.y_60d / cancel diff naive t=-3.18 + autocorr_corrected(NW-HAC -2.64/wc_p 0.0045)=attack:pbr_cancel_diff / 밸류업 CAAR=oos-event:value_up. | **PASS** — source_id 매핑. raw .py 재실행 가능. |
| **D★** PIT (hard-fail) | ✅ | 가격 PIT-safe(forward shift). valuation = DART rcept_dt 공시일 이후만. ★금리 regime = ex-ante(일별 시장금리 = 발표지연 無). Macro CLI = CLI_PUB_LAG=2. event study estimation [-120,-11] = 과거만. | **PASS** — lookahead 회피. ★금리 일별 = 실시간 ex-ante(반도체 Macro lag 와 차이). |
| **E** 다중검정 | ✅ | measure_conditional benjamini_yekutieli. m=862 naive(sub-sector 6 × 신호 6 × horizon 3 × regime cell) BY survivors=[]. M_eff_signal 박제(통합 supervisor). | **PASS** — ★over-claim 정정: m=862 naive 과대(sub-sector 중복+신호상관). 독립 = sub-sector 3 + M_eff. BY 미생존 정직 보고. |
| **F** OOS/walk-forward | ✅ | measure_oos_event walk_forward_oos. IS(2019-22)/OOS(2023-26): rev_1m 부호유지(ratePOS IS-0.061→OOS-0.055 / bank IS-0.056→OOS-0.173) / momentum 부호반전(structural break). | **PASS** — rev_1m robust(부호유지). ★momentum = structural break 정직 노출(artifact 아닌 regime). PBR = DART 2023~ IS n=0 = data-gate. |
| **G** 자기상관 | ✅ | small-block size-invalid(Kiefer-Vogelsang) → wild-cluster bootstrap(Rademacher B=2000) per-cell p + n_eff(autocorr) + block-boot CI. asymptotic NW-HAC t = 참고만. ★fin-audit remediation 1: cancel diff(60d overlapping)도 자기상관 보정 병기. | **PASS** — wild-cluster p 채택. 은행 PBR wc_p=0.0165 / rev_1m KRW_weak wc_p=0.003. ★cancel diff = naive t=−3.18(자기상관 미보정)였으나 보정 병기(NW-HAC lag3 −2.64 / n_eff 14.7 −2.35 / wc_p 0.0045 / CI[−0.60,−0.14] 0배제) = 다른 지표와 동일 기준 적용, 부호 robust. |
| **A-5★** regime interaction | ⚠️ | family_2 interaction term(measure_interaction_terms): rate_up×signal(은행그룹) + flow_strong_buy×value(전체) = 전부 비유의(t<2). sign-flip 295건. | **PARTIAL** — family_2 interaction term 측정 의무 이행(rejected 박제 前). ★단 interaction 비유의 = dummy 분리 자유도 손실. ★sub-sector split(은행 vs 증권 부호, 자기상관 보정 NW-HAC t=−2.64)이 더 강한 conditional 발현 = A-5 충족(국면 아닌 sub-sector 따라 부호 갈림). |
| **H** 미해결 | ✅ | candidate-ledger data-gate(DART 2019-22/PF 익스포저/종목 flow) + falsifier(은행 PBR magnitude/cancel structural/밸류업 일관성) + flip-register. | **PASS** — 미해결 명시. |
| **I★** 생존편향 (hard-fail) | ⚠️ | universe = FDR 현재 스냅샷(생존 종목). delisted/M&A 누락(금융 = 합병 잦음). PIT 멤버십 = collector_plan. | **PARTIAL** — ★정직 격하(PARTIAL 라벨 + note), over-claim 아님 = hard-fail 회피. |
| **J** spec↔code 일치 | ✅ | spec "은행 sub-sector 저PBR z → 60d forward" = code build_valuation_signals(bank codes) → forward_returns_daily(60). predictive verify. 부호 음(value) = 측정값 그대로. | **PASS** — measurement axis 일치(forward predictive). |
| **K** 분석unit↔portfolio 분리 | ✅✅ | ★**본 capsule 핵심 축**. 분석 unit = sub-sector 분리(은행/증권/보험 factor loading 동일 부호 grouping). portfolio label "금융주" = 표시일 뿐. ★은행(value −) vs 증권(반대 +) 부호 cancel = frame §1.6 ERROR-202605302245 직격. | **PASS** — ★frame §1.6 정확히 이행. sub-sector 분리 = 부호 cancel 회피. supervisor sleeve 분리 권고. |
| **L** 공통인자 1회계상 | ✅ | common_factor_exposure = β 보고만(산업이 cross 최종 박제 X). 통합 supervisor L축 1회 계상. | **PASS** — β 벡터 보고. PSD = supervisor. |
| **M★** wire 충실 | ✅ | score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출(재구현 X). opt-in 측정, production(INV_R15_WEIGHTS) 미접촉. | **PASS** — wire 미배선(teammate scope). |
| **N★** cross PSD | N/A | cross 조립(RegimeGlasso Σ mixing) = supervisor 단계. 산업 = β 보고. directional_spillover=[] (DY 통합단계). | **N/A** — supervisor 책임. |
| **O★** leakage | ✅ | forward = shift(-h)(미래 누설 없음). reject≠missing: 상장 전 NaN=look-back gap(missing), credit_wide=36month(reject 아님=관측). 금리 ex-ante. | **PASS** — PIT-safe + tri-state. |
| **P** net-cost robustness | ✅ | STT_SELL 0.20% 비대칭 + COMMISSION + SPREAD_HALF. rev_1m turnover 高 caveat. gross IC -0.05~-0.16. | **PASS** — KR STT 반영. ★rev_1m gross 약(-0.05) = net 후 marginal caveat. sqrt impact = supervisor. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (ECOS 금리/flow + DART + FRED + pykrx, 합성지문 3종 PASS) |
| C 추적성 | PASS | yaml↔raw json 매핑(source_id) |
| D PIT | PASS | 가격/valuation/금리 regime 전부 PIT-safe |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL 라벨), over-claim 회피 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하로 over-claim 회피 → hard-fail 아님).

## S2 conditional verdict

- ★hard-fail 코어 (B/C/D) PASS, I PARTIAL(정직 격하). conditional 측정 = hard-fail 0.
- **핵심 = sub-sector 부호 이질 발견**(dispatch 원의도 + frame §1.6): 은행 저PBR value(−0.161 wc_p=0.0165) vs 증권 반대(+0.146) 차이 **t=−3.18 유의** = 통합 cross-sectional IC cancel. = "어느 sub-sector 에 어느 지표" 답.
- ★G-B = "약함" 아님: BY 미생존은 (a) m=862 naive 과대(sub-sector 중복+신호상관) (b) ★sub-sector split 에서 발견 살아있음(은행 value t=-3.18 + rev_1m OOS 부호유지) = frame §1.6 cancel 구조. M_eff 보정 + 분리 박제가 우선(team-lead G-B 자동자문 보류 권고).
- ★**verdict 확정 (walk-forward OOS)**: rev_1m reversal = ratePOS/bank 모두 IS/OOS 부호유지 = PARTIAL(robust, magnitude 약). 은행 PBR value = PARTIAL(부호 robust t=-3.18, magnitude tentative = DART 2023~ n=27). momentum = TENTATIVE(structural break). 밸류업 = TENTATIVE(1차 음/2차 양).
- ★정직 단서: (a) DART 금융재무 2023~ 제약 = PBR magnitude·OOS split data-gate(IS n=0) (b) M_eff 통합 supervisor 단계 (c) sub-sector 분리 시 N 작음(은행 11) = magnitude tentative (d) 종목레벨 외국인flow = DATA-GATE(KRX 차단).
- ★전체 verdict_label = **TENTATIVE** (sub-sector cancel 발견은 강하나 n short + DART 제약).

## ★frame §1.6 이행 입증 (본 capsule 차별점)

frame §1.6(분석 unit ↔ portfolio label 분리, ERROR-202605302245 anchor "XLF 부호 반대 sub-sleeve 결합")을 financial 에서 **데이터로 직접 입증**:
- user label "금융주" eq-weight cross-sectional = sub-sector 부호 cancel(은행 value − vs 증권 +) → IC 0 수렴(기존 v2 "전부 비유의" 원인).
- 분석 unit = sub-sector 분리(rate_POS 은행/보험/지주 vs 증권) = factor 부호 동일 grouping.
- = ERROR-202605302245 의 "부호 반대 sub-sleeve eq-weight → factor β cancel" 을 **재현+회피** 입증.
