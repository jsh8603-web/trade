<!-- author: chem-analyst@kr-equity (1단계 산출, 2026-06-05) -->
<!-- ★ self-audit 초안 — 최종 G-C 독립 audit은 별 세션(author != auditor, 메인이 스폰) -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — chemical conditional IC (frame v3 §E, A~P 15축)

> self-audit 초안. raw 재현 = `raw-v3/*.py` + `validation-*.json`. semiconductor 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | ② 측정 코드·수치 경로 | ③ 결과 판정 |
|---|---|---|---|---|
| **A** | 이론 실재 | PASS | theory-notes.md §출처 (CGS2008 JF / TWX2004 JFQA / Chen-NMZ2010 / Kitchin1923 / Jorion1990) + 증권사 in-depth(메커니즘만). 가설 H1~H12 측정前 부호 사전등록(HARKing 방지) | 학술 ref 실재 URL/DOI. 자문 결론 미사용 |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 17종(1818일) + DART fnlttSinglAcntAll(equity/net_income/assets + 재고/유형/무형자산 442 rows) + FRED CLI/DEXKOUS + ECOS 외국인순매수 + yfinance(VIX/dollar/oil/credit). raw-v3/{collect,collect_dart,collect_dart_extended,collect_regime,measure_*}.py 재실행 가능 | 2020 코로나·2022 down-cycle 실재. 합성지문 부재 |
| **C** | ★추적성 (hard-fail) | **PASS** | summary.yaml IC = validation-{conditional,valuation,fundamentals-cycle,cross}-v3.json key 매핑(source_id). vol_60 -0.142=conditional.vol_60.y_60d / per_z -0.218=valuation.per_z__6M / capex 0.0017=fundamentals-cycle | yaml↔raw ±5% 매핑 |
| **D** | ★PIT (hard-fail) | **PASS** | 펀더멘털 = DART rcept_dt(공시일) 이후만(median delay 108-120일 실측). regime CLI_PUB_LAG=2(OECD 발표지연). 가격 forward=shift(-h) PIT-safe | lookahead 회피 |
| **E** | 다중검정 보정 | PASS | G-F §3 family 측정前 사전고정. conditional m=91 BY survivors=[mom_6 y60, vol_60 y60] / valuation m=8 BY survivors=[per_z 6M/3M/12M] / fundamentals m=78 survivors=[] | BY 생존 명시. capex/inv/rnd 미생존 정직 보고 |
| **F** | 반증+기각 | PASS | ★capex_ratio(H1) REJECTED + ppe_yoy(H2 prior반대) + inv_yoy(H4) + rnd_ratio(H5) 기각 명시. falsifier(OOS flip) 적용 | 기각 4건 = p-hacking 아님 |
| **G** | 검정력·tier | PASS | n_eff(autocorr 보정) 명시. t_obs(neff): vol 3.14 WELL / per 6.46 WELL / mom 2.48 under(OOS hold) / inv 2.16 under. n=17 small-n → Tentative tier | underpowered cell = inconclusive 라벨 |
| **H** | 미해결 | PASS | collector_plan(에틸렌-납사 spread high / 중국PMI / KR HY / PIT 멤버십 high) + open_questions 4건(capex 시계열/PER trap/spread/small-n) | candidate-ledger 연결 |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷(생존 17종), delisted/M&A 누락. 화학 상폐 적으나 보정 미완. PIT 멤버십=collector_plan high | ★정직 격하(PARTIAL+note), over-claim 회피 → hard-fail 아님 |
| **J** | 경제성·거래비용 | PASS | net_sharpe: per_z 0.80(value 저회전) / vol_60 0.65 / mom_6 0.55(중회전). KR STT sell 0.20% 비대칭. ★small-n no-trade band + CPCV 캘리브 필요 명시 | gross 보존 추정, sqrt impact=supervisor |
| **K** | 다중검정 보정(K) | PASS | conditional/valuation/fundamentals 3 family 시도횟수 공시(m=91/8/78). BY-FDR. ★over-claim 회피 = M_eff 통합 supervisor | 시도횟수 박제 |
| **L** | 통합 상관 PSD | N/A | common_factor β 보고만(산업이 cross 최종 박제 X). 통합 supervisor L축 1회 계상 | supervisor 책임 |
| **M** | wire 충실 | PASS | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출(재구현 X). production 미배선(INV_R15_WEIGHTS 미접촉) | opt-in 측정만 |
| **N** | cross PSD | N/A | cross 조립=supervisor. 산업=β 벡터 + directional_spillover(measured-null) 보고만 | PSD 책임 밖 |
| **O** | leakage | PASS | forward=shift(-h) 미래누설 없음. reject≠missing: 상장 전 NaN=missing(이수스페셜티/OCI 신규상장 729-730행), regime cell=관측 | PIT-safe |
| **P** | net-cost robustness | PASS | gross\|IC\| vs KR STT 0.20% 비대칭. value 저회전(gross 80%+) / vol·mom 중회전(60-70% 추정) | reversal turnover caveat 명시 |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 재무 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (source_id) |
| D PIT | PASS | DART rcept_dt 이후만 + CLI 2M lag |
| I 생존편향 | PARTIAL | 정직 격하(over-claim 회피) |

★**hard-fail 0** (B/C/D PASS, I=PARTIAL 정직 격하 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 PASS, L/N=N/A(supervisor).
- **status = PARTIAL** — tradeable 신호 3개(vol_60 저변동 / per_z value / mom_6 reversal) BY 생존 + OOS HOLD + size 독립. 단 ★n=17 small-n → magnitude 50-70% haircut 의무, point estimate literal 금지.
- ★**핵심 검증 결과 2 (정직 보고)**:
  1. ★**capex 일반화 가설 = 화학 REJECTED** (auto의 robust 음 신호 미재현). 진단(정밀) = 종목별 capex **분산은 존재**(CV 0.241)하나 panel n_obs=1312 powered인데 **IC≈0 = forward 예측력 부재**(측정 못함 아님). auto(t=-3.38)·steel(within=0.96) selection 유효와 근본 차이. ⇒ capex 유효성 = 산업구조 단정 아니라 **forward 예측력 실측 의존**. ★archetype 내 이질성.
  2. ★**PER value premium > PBR** (auto/반도체 peak-EPS trap과 반대). 화학은 peak-EPS trap 약 → PER 횡단면이 forward 예측. ★archetype 내 valuation metric 시변 적합도 추가 증거 (frame M.11 동적가중 지지).
- ★**부호 검증 = archetype 정합**: momentum 음(reversal) = cyclical 정점(반도체 동형). 저변동 음 = low-vol anomaly. cyclical 일관.
- ★**small-n 정직성** (frame M.12): n=17 cross-sectional, magnitude haircut + size-orth IC 병기(per_z full -0.218 → size-orth -0.110 절반). 24M degenerate 강등.

## ★G-G v2 tradeable 판정 (별 게이트)

- **verdict = PASS-conditional**: tradeable ≥1 (vol_60 + per_z + mom_6, OOS HOLD + WELL/under-but-hold + size 독립). but n=17 small-n low confidence → **conservative cap + monitor + magnitude haircut**.
- regime label: "Slowdown(둔화)+flow_sell(외국인매도) → 저변동·역모멘텀 화학주 / value(저PER) 전국면".
- rejected: capex_ratio/ppe_yoy/inv_yoy/rnd_ratio (매매 신호 아님).
