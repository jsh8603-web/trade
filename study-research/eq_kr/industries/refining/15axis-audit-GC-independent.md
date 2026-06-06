---
tags: [type/axis-audit, domain/equity, sector/refining, scope/equity-kr, audit/independent-GC]
date: 2026-06-05
purpose: 정유(refining) G-C 독립 audit (author≠auditor). refine-analyst self-audit 무비판 신뢰 X — raw-v3/*.py 직접 재실행이 유일 근거.
auditor: refine-auditor (opus 1m, team=kr-equity)
note: ★frame M2 시계열 패널 case (universe strict 2종 = cross-sectional 불가). raw 6개 .py 전수 재실행 + 독립 frame §1.7 재계산.
---

# 정유(refining) G-C 독립 audit — verdict: 충실(PASS)

> hard-fail 코어 B·C·D·I = 0. cross-sectional INSUFFICIENT = 정직(측정 불가, 위장 아님).
> capex INCONCLUSIVE 정정 = 통계적으로 정확. 유가 risk-monitor = G-G monitor-only 판정 동의.

## §0 Provenance + Recomputation (가장 중요)

| 항목 | 결과 |
|---|---|
| raw .py 직접 재실행 | ✅ 6개 전수 재실행 (measure_capex_cycle / measure_attack / measure_timeseries / measure_ts_robustness / measure_valuation_ts / measure_cross_placebo). PYTHONUTF8=1 Python312. |
| yaml↔raw 일치 | ✅ **완벽 일치**. capex rho=+0.474 t_eff=2.61 OOS HOLD / ATK-3 partial_on_brent=+0.2919 / 유가 동시+0.407 forward-0.368 Δbrent-0.049 / eff-N t=-1.96 / ADF brent I(1) p=0.173 / FDR survivors=0. 모든 점추정 재현. |
| 합성지문 검사 | ✅ **합성 0%**. Brent 2020-04 최저 $9.12(코로나 음수유가 근방) / 2022-06 최고 $133(우크라전 실제~$120) / kurtosis 1.21. prices 1818일 영업일만(토일=0) / SK이노 covid 최대낙폭 -19.2% / 일수익 kurtosis 10.06 fat-tail. DART rcept_dt 분기 28건 실재(2019-05~2026-03). |

## §1 15축 결과 (12 study축 A~L + wire M~O는 study단계 N/A)

| 축 | 판정 | 독립 재계산 근거 |
|---|---|---|
| A 이론실재 | PASS | theory §1 Cooper-Gulen-Schill 2008 / Deaton-Laroque 1992 / Fama-French. 부호 사전확약. |
| **B★ 실데이터** | **PASS** | 합성 0%(위 §0). raw 6개 .py 재실행 일치. |
| **C★ 추적성** | **PASS** | yaml 전 수치 = json key 재현. 오차 0%. |
| **D★ PIT** | **PASS** | forward shift(-h) + DART rcept_dt 이후만 + IP_PUB_LAG=2. lookahead·restatement 회피. 재무는 분기 공시일 사용(28건 실재). |
| E 자문환각 | PASS | Gemini 메커니즘만 추출, 본인 측정으로 검증(유가 동시+/예측-, capex 음 prior↔실측 양). 코드화≠복붙. |
| F 반증+기각 | PASS | 기각 다수(PER 무효 / 가동률 OOS flip / crack 약 / capex single REJECT 보류). p-hacking 아님. |
| G 검정력·tier | PARTIAL(tier 함수, 차단 아님) | cross-sectional INSUFFICIENT(2종) + 시계열 eff-N marginal. tier=structural_prior_low_confidence(유가) / 나머지 TENTATIVE·INSUFFICIENT. |
| H 미해결 | PASS | candidate-ledger §이연/falsifier + research-log 미해결(싱가포르GRM/universe). |
| **I★ 생존편향** | **PASS** | strict floor 통과 = SK이노/S-Oil 정확히 2종 검증(나머지 3종 floor 미달 microcap). 정유 과점 = data-gate(생존편향 아닌 표본부재). |
| J 거래비용 | PASS(조건부) | 종목선택 weight 0 = 매매룰 미구성 → net-cost 무대상. over-trade 차단. |
| K 다중검정 | PASS | 단일 FDR family(m=6) survivors=0. wild-cluster bootstrap. 약신호 정직. |
| L 통합PSD | DEFER(통합단계) | 공통인자 β + directional_spillover 후보 보고(빈[] 금지 충족). |
| M·N·O wire | N/A·DEFER·PASS(study) | production 미배선(teammate scope=capsule). O = PIT-safe + reject≠missing. |

→ **hard-fail 코어 B·C·D·I = 0**.

## §2 ★핵심1: cross-sectional INSUFFICIENT 정직성 — PASS

universe.parquet 직접 검증: refining core 5종 중 strict floor(시총3000억∧ADV30억) 통과 = **SK이노(096770)+S-Oil(010950) 정확히 2종**. 나머지 3종(한국쉘석유/미창석유/극동유화) = floor 미달 microcap.
- min 8종 필요한 Spearman IC → n=2 = **측정 자체 불가**(코드 `spearman_neff`가 n<8시 `INSUFFICIENT(n<8)` 강제 반환 = 측정값 산출 X).
- = "측정 후 약함" 위장이 아니라 **진짜 측정 불가**. 정직. 국내 정유 과점(2-3개) = 구조적 영구 불가.

## §3 ★핵심2: capex INCONCLUSIVE 정정 적정성 — 정정이 옳음(PASS)

refine-analyst가 처음 시계열 capex를 spurious REJECT(ADF I(1)+유가proxy collinear)했다가 S5 ATK-3로 INCONCLUSIVE로 격하한 정정을 **독립 frame §1.7 재계산**으로 검증:

**§1.7-A 단위근/잔차 stationary 독립 측정**:
- capex_level ADF p=0.859 = 강한 I(1) ✓(산출 일치)
- **★종속변수 fwd3_ret ADF p=0.019 = I(0) stationary** ← 결정적
- **★capex_level→fwd3 회귀 잔차 ADF p=0.0001 (강 stationary), DW=1.035 (>0.5 spurious 임계 미달)**

**판정 근거**: spurious regression(Granger-Newbold)은 **양쪽 다 I(1)**일 때 발생. 여기선 regressor I(1) → response I(0) + 잔차 I(0) = 전형적 spurious 패턴 아님. → 단순 "level I(1) spurious REJECT"는 **over-rejection이 맞고, INCONCLUSIVE 격하가 옳은 방향**. (오히려 산출 yaml이 "level I(1) spurious 위험 강"이라고 다소 과하게 깎은 면 있으나, 보수적이라 무해.)

**ATK-3 orthogonal 신호 다중통제 robustness(독립 재계산)**:
- brent 통제 +0.292(p=0.008) / brent+oil_yoy +0.349 / brent+crack +0.304 / brent+self_mom3 +0.354 — 모두 잔존, p<0.01. → **유가 proxy만은 아님(orthogonal 성분 실재)**.

**단 진짜 spurious도 단정 불가 + standalone 채택 불가 이유(INCONCLUSIVE 정당)**:
- capex_level lag-1 autocorr = **0.944**(분기 forward-fill). 진짜 독립 capex 관측 ~28개(공시 건수), 자산집약도 느린 추세 변동 고려 시 더 적음 → n_eff=25.5도 과대평가 가능.
- eff-N t=2.61 < single FDR breakeven 2.802 = **약간 underpowered**.
- cross-sectional 측정 불가(n=2) = capex의 본래 anomaly(횡단면 asset growth) 검증 불능.
- **결론**: 진짜 신호 죽일 뻔한 것을 ATK-3로 회피한 것이 옳음. 동시에 standalone alpha 채택도 불가. → **INCONCLUSIVE = 통계적으로 정확한 위치**(REJECT도 ACCEPT도 아님). §1.8 self-referential 함정 회피 + over-rejection 회피 둘 다 충족.

## §4 ★핵심3: 유가 mean-reversion risk-monitor — G-G monitor-only 판정 동의

eff-N t=-1.96 marginal + FDR 미생존이 noise인지 vs 진짜 신호인지 G-G v2 MDE/power로 판정:

- **G-G v2 ① eligibility(held-out OOS 부호+magnitude)**: IS=-0.39 → OOS=-0.60 **부호유지+강화** ✓ + leave-episode(covid+우크라 제외) -0.37→-0.25 survive ✓ + ATK-2 시장통제 후 partial -0.382 잔존 ✓ → **eligibility 충족**.
- **G-G v2 미생존 해석(MDE/power)**: |t_obs|=1.96 < breakeven 2.802 = **UNDERPOWERED**. = "본질 약"이 아니라 "검정력 부족" → OOS robust면 noise 아님, eligibility 자격은 있음. **단 conviction(sizing) 낮음**.
- **그러나 alpha 격하 정당**: Δ유가 forward 예측력=0(rho=-0.049, t_eff=-0.24) = level만 mean-reversion(momentum 아님) + level I(1) + FDR 미생존 + eff-N marginal. → **risk-monitor/de-risk(고유가 peak 회피)지 alpha generator 아님**. family_2 Slowdown interaction t=2.23 = 국면 conditional 확인.

→ **G-G = monitor-only/산업 timing sleeve, 종목선택 weight 0 = 동의**. eligible하나 low conviction → conservative cap + monitor 정합. over-trade 차단(약신호 강제투입 회피) 적절.

## §5 종합

- **verdict: 충실(PASS)** — hard-fail 코어 B·C·D·I = 0.
- cross-sectional INSUFFICIENT = 정직(측정 불가, 위장 아님). capex INCONCLUSIVE = 통계적으로 정확(over-rejection 회피 옳음, 동시에 진짜 신호도 단정 불가). 유가 risk-monitor = monitor-only 동의.
- self-audit(refine-analyst) 결론과 독립 재계산 결과 **일치** — 단 self-audit이 capex를 "level I(1) spurious 위험 강"으로 다소 과하게 표현했으나 보수 방향이라 무해.
- **G-G 판정**: PASS-conditional 경계 = 유가 1 eligible(low conviction, monitor-only) + cross-sectional 0. 매매 자격 신호는 산업 timing 1개뿐 → monitor-only sleeve 정합.
- register 가능(충실). 단 종목선택(L3) weight 0 박제 + 유가는 conservative cap/monitor.
