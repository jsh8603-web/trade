<!-- author: battery teammate (bat-analyst, opus 1m, S6 self-audit 초안, 2026-06-05) -->
<!-- ★최종 G-C 독립 audit = 별 세션(author != auditor) — 본 self-audit 은 참고용 -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — battery(2차전지) §M v3 conditional IC (frame v3 §E, A~P 15축)

> self-audit: yaml↔raw 재현·hard-fail 0 점검. raw 재현 = `raw-v3/*.py`. 반도체 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★3컬럼(① 적용했나 ② 어떻게 측정·코드/수치 경로 ③ 결과·판정) — G-A 게이트.

## A~P 15축 (unconditional + conditional 통합)

| 축 | ① 적용 | ② 측정·코드/수치 경로 | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론실재 | YES | theory-notes §1 부호 사전확약(M1~M4) = Jegadeesh-Titman 1993(momentum)/LSV 1994(value)/Choe-Kho-Stulz 2005(flow)/BNEF·SNE Research(리튬). 측정前 동결. | **PASS** — 학술 ground 1차 + 부호 one-sided 사전확약(HARKing 방지). |
| **B** ★실데이터 (hard-fail) | YES | 합성 0%. pykrx OHLCV 29종(1818일) + yfinance(VIX/dollar/oil/rate/credit) + DART(financials 698 + extended 747rows) + FRED CLI/DEXKOUS + ECOS 외국인순매수. raw-v3/{collect,collect_dart,collect_dart_extended,collect_regime,measure_*}.py 재현. | **PASS** — 실 PIT 데이터만. |
| **C** ★추적성 (hard-fail) | YES | 모든 yaml 수치 → validation-{conditional,fundamentals-cycle,merged-fdr,walkforward,cross,valuation,metrics}-v3.json key 매핑(source_id). mom_6 +0.075=mom_6.y_60d / inv_ratio +0.112=fundamentals.inv_ratio.y_60d / interaction t=-3.20=family_2_interaction. | **PASS** — yaml↔raw 매핑 완전. |
| **D** ★PIT (hard-fail) | YES | 가격신호 = PIT-safe(forward shift, 일간). valuation/펀더멘털 = DART rcept_dt(공시일) 이후만(measure_conditional.build_valuation_signals + measure_fundamentals_cycle.build_fundamental_panel `av=cf[cf.rcept_dt<=dt]`). Macro CLI = 발표지연 2M lag(collect_regime CLI_PUB_LAG=2). KRW/flow 일별 실시간. | **PASS** — lookahead 회피. 시총=현재주식수 근사(시점주식수 = collector_plan high 한계 명시). |
| **E** 다중검정 | YES | ★G-F §3 family 측정前 사전고정(6신호×3h×regime cell 단일 BY-FDR). conditional m=99 + fundamentals 78 = **merged m=177 BY survivors=[]**(merge_fdr_family.py). M_eff_signal=3.0(Li-Ji) 박제. | **PASS** — naive m 과대 = M_eff 통합 supervisor. 정직 보고(BY 미생존). |
| **F** OOS/walk-forward | YES | ★walk-forward IS(2019-22)/OOS(2023-26) split(measure_walkforward.py): mom_6 uncond +0.078→+0.072 / flow_neutral +0.132→+0.113 / mom_12_1 flow_neutral +0.048→+0.170 = 전부 OOS 부호+magnitude 유지. interaction mom_12_1 IS t=-1.91→OOS t=-2.59 생존. | **PASS** — in-sample artifact 아님. (진짜 holdout 2026+ = pristine OOS 별개 미래 보너스.) |
| **G** 자기상관 | YES | ★small-block size-invalid(Kiefer-Vogelsang) → wild-cluster bootstrap(Rademacher B=2000) per-cell p + n_eff(autocorr) + block-boot CI(measure_conditional). asymptotic NW-HAC t = 참고만. | **PASS** — G-F §7 준수. |
| **H** 미해결 명시 | YES | collector_plan(EV-EBITDA high / 종목 flow high / 리튬·GWh medium / PIT 멤버십 high) + candidate-ledger ⏳이연 6 + 🔬falsifier 4. | **PASS** — 미해결 명시(ledger 연결). |
| **I** ★생존편향 (hard-fail) | YES | universe=FDR 현재 스냅샷(생존종목만), delisted/M&A 누락. 29종 中 일부 부분이력(LG엔솔 2022상장). PIT 멤버십=collector_plan high. | **PARTIAL** — 정직 격하(PARTIAL 라벨 + note), over-claim 회피 → hard-fail 아님. |
| **J** 측정 axis 일치 (spec↔code) | YES | spec "cross-sectional 6M 모멘텀 → 60d forward" = code `csz(mom_6) → forward_returns_daily(60)`. forward predictive 동일. ★부호 양(continuation) = 측정값 그대로(over-claim 없음). | **PASS** — spec↔code 1:1. |
| **K** 분석 unit ↔ portfolio label 분리 | YES | 분석 unit = battery universe 29종(factor loading). z-score = peer-relative(sector-neutral). portfolio 조립 = supervisor(§M.7 분담). ⚠️ sub-cluster(셀/소재/장비) 부호 점검 = momentum 전 cell 양(flow_strong_buy 제외 = regime conditional, 부호반대 sub-sleeve 아님). | **PASS** — K 위반 없음(flow_strong_buy 음 flip = regime 효과지 sub-sector cancel 아님). |
| **L** 공통인자 1회 계상 | YES | common_factor_exposure = β 보고만(credit -0.164/oil +0.248). 통합 supervisor L축 1회 계상. | **PASS** — 산업이 최종 박제 X. |
| **M** 코드 충실 (wire) | YES | rank_ic / interaction / e-process hook = 측정 함수 직접. opt-in 측정, production(INV_R15_WEIGHTS) 미접촉. | **PASS** — production 미배선(분담 준수). |
| **N** cross 관계 PSD | N/A | cross 조립(RegimeGlasso Σ mixing) = supervisor. 산업 = β 벡터 보고만. directional_spillover=[](DY 통합단계). | **N/A** — PSD 책임 supervisor. |
| **O** leakage (PIT-safe) | YES | forward return = shift(+h)(미래 누설 없음). reject≠missing: 상장 전 NaN = look-back gap(missing) / regime cell N<24 = underpowered(관측됨, reject 아님). | **PASS** — tri-state 구분. |
| **P** net-cost robustness | YES | gross \|IC\| 0.075 vs 월 16.5bps cost. breadth 29종 = IR 침식 + momentum turnover → net 보존 marginal. KR STT 비대칭. sqrt impact = supervisor. | **PASS** — marginal caveat 명시. |
| **A-5** ★regime interaction | YES | ★family_2 의무 충족(rejected 박제 前). flow_strong_buy interaction: mom_6 t=-2.43 / mom_12_1 t=-3.20 유의(main 양). rev_1m/vol_60 비유의(정직). KRW_weak 축 비유의(cross-sector 비교). regime별 wild-cluster CI. | **PASS** — "국면 따라 부호 갈림"(flow_strong_buy momentum 음 flip) 입증. |
| **A-6** supervisor 정의대조 | N/A | self-audit(author=teammate). ★최종 G-C 독립 audit = 별 세션 의무. | — |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART financials 698 + extended 747 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (7 json source_id) |
| D PIT | PASS | 가격 PIT-safe + valuation/펀더멘털 DART rcept_dt + CLI 2M lag |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL 라벨), over-claim 회피 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하로 over-claim 회피 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor), A-5 PASS.
- **status = PARTIAL CONFIRMED** — primary cs_mom_6m(momentum→continuation) 방향 robust(wc_p 0.0125 + flow_neutral wc_p=0.001 + OOS 부호+magnitude 유지 + leave-2022-out 강화) but ★merged BY 미생존(m=177) = 다중검정 후 비유의.
- ★**핵심 검증 가치**: momentum forward IC 부호 = **양(continuation)** = 반도체(음 reversal)와 반대 = **cyclical archetype 내 이질성**(2차전지 성장단계 + 종목차별화). 부호 검증이 산업별 archetype 판별에 결정적.
- ★**conditional 본체(dispatch 원의도)**: flow regime 이 momentum IC 변조 핵심축 = flow_neutral 증폭(+0.123) / flow_strong_buy 음 flip(interaction t=-3.20). ★battery conditioning 축 = flow(반도체 KRW_weak 과 다름) = 산업별 driver 이질성.
- ★**S5 역공격 수렴**: momentum continuation = 반증 3종(leave-2022-out 강화 + flow_strong_buy 7년분산 + walk-forward OOS) 모두 방어 = in-sample artifact 아님.
- ★**신규 cycle 지표 측정완료(이연 금지 이행)**: inv_ratio = prior 반증(양 +0.112, family 최강 wc_p=0.0005, 성장 proxy 재해석, 반도체 동형 = memory enum) / ppe_yoy·capex_ratio·inv_yoy·rnd_ratio = OOS artifact 또는 비유의 = INSUFFICIENT. 정직 박제(over-claim 0).
- archetype cyclical 사후편향(M.5): valid_from 2019 사전선언, declared_at 명시. ★단 measured momentum 양=growth-like = archetype 라벨(cyclical)과 cycle 위상 차이 noted(성장단계). transition 없음.

## ★G-B 판정 (재자문 트리거)

- trigger: BY 생존 0 AND raw_p_min(0.0005) > 2×BY_thresh = 충족(간발).
- ★verdict: "약함" 부적합 = (a) flow_strong_buy interaction 유의(t=-3.20) (b) momentum uncond wc_p<0.05 + OOS 부호유지 + leave-2022-out 강화 (c) merged m=177 과대(M_eff 미통합). → G-B 자동자문 발동 여부 = **supervisor 판단**(보고). 산업 판정 = "conditional 강함(flow modulation), unconditional+naive-FDR 약" = 동적가중 정당화.

## ★정직 단서 (over-claim 회피)

- (a) OOS n=19 small-n + breadth 29종(반도체 85종 1/3) → magnitude tentative(부호·방향만).
- (b) M_eff 통합보정 = supervisor 통합단계(naive m 박제).
- (c) inv_ratio prior 반증 = 성장 proxy 재해석(post-hoc) + size/growth confound 미분리 = TENTATIVE.
- (d) 종목레벨 외국인flow·리튬 price·GWh = DATA-GATE(KRX 차단/유료, deferral 아님).
- (e) flow_strong_buy interaction = mom_6 OOS t=-1.03 약화(mom_12_1 만 OOS 생존) = PARTIAL.
