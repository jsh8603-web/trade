<!-- author: auto teammate (kr-equity, opus 1m, 2026-06-05) — S6 self-audit 초안 -->
<!-- ★최종 G-C 독립 audit = 별 세션(메인이 audit teammate 스폰). 본 self-audit = 참고용 -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — auto(자동차) conditional IC v3 (frame v3 §E, A~P 15축 3컬럼)

> S6 self-audit. yaml↔raw 재현·hard-fail 0 확인. raw 재현 = raw-v3/{measure_conditional,measure_oos,measure_fundamentals_cycle,measure_critique,measure_attack,merge_fdr_family}.py. 반도체 15axis-audit.md 미러.
> Hard-fail 코어: B(실데이터)·C(추적성)·D(PIT)·I(생존편향) + 조건부 J/K/L/M/N/O.

## A~P 15축 (① 적용했나 / ② 어떻게 측정·코드/수치 경로 / ③ 결과·판정)

| 축 | ① 적용 | ② 측정 방법·코드/수치 경로 | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론실재 | YES | theory-notes §1 부호 사전확약(M1~M5) = Daniel-Moskowitz 2016/Damodaran cyclical/Cooper-Gulen-Schill 2008/Bae-Chan-Ng 2004/Jorion 1990. Gemini 리서치(/tmp/auto-search-result1.txt) source URL. | PASS — 이론 ground 1차. ★자동차는 round-1 류 측정前 박제 부재 → theory-notes §1 이 1차 동결점(측정前 이론 우선). |
| **B★** 실데이터 | YES | 합성지문 검사: USDKRW 2022-10=1429(실제 고점)/2020-03 covid=1234, CLI 2020-05=99.4, 현대차 2020-03=65,900→2024-07=286,000, DART ppe 30.5~48.7조. pykrx 17종(1818일)+FRED CLI/DEXKOUS+ECOS 외국인순매수+DART(extended 423rows, coverage inv0.92/ppe0.97/intangible0.95). | **PASS** — 합성 0%. raw-v3/*.py 재현. |
| **C★** 추적성 | YES | yaml 수치 → validation-conditional-v3.json(가격/PBR) + validation-fundamentals-cycle-v3.json(capex) + validation-critique-v3.json(size-orth) + validation-attack-v3.json(역공격) + validation-merged-fdr-v3.json(통합 FDR) key 매핑. | **PASS** — 모든 수치 source_id 추적. walk_forward_oos/family_2 재현. |
| **D★** PIT | YES | Macro CLI = 발표지연 ~1-2M → CLI_PUB_LAG=2(lookahead 회피, collect_regime.py). KRW(DEXKOUS)/flow(ECOS) 일별 실시간. DART valuation/capex = rcept_dt(공시일) 이후만(measure_conditional/fundamentals). forward=shift(-h). | **PASS** — PIT-safe. 시총=Close×현재주식수 근사(시점별 주식수 정밀화=collector_plan high 한계 명시). |
| **E** 자문환각 | YES | Gemini 리서치 결론 = 메커니즘·부호만 추출(목표가·투자의견 제외). 부호 사전확약 후 우리 PIT 측정으로 검증(자문=reference). | PASS — 자문 그대로 코드화 0. capex(prior 음) 측정으로 입증, dollar(자문 양)는 unconditional 비유의 = 자문 맹신 안 함. |
| **F** 반증+기각 | YES | S5 역공격(measure_attack.py) 3종: A1 size-bucket / A2 sub-period / A3 LOO. + falsifier(theory-notes 각 M). | PASS — 반증 전부 기각(capex/pbr 견고). 가격신호 = OOS flip 으로 REJECTED(falsifier 작동). |
| **G** 검정력·tier | YES | n_eff(autocorr) + wild-cluster p + powered/underpowered/INSUFFICIENT 라벨(N>=24 & n_eff>=6). ★[G-C remediation] capex/pbr y_60d IC AR(1)=0.426/0.494(60d 중첩) → effective-N=39.7/34.2(measure_neff_label.py). Fama-MacBeth NW-HAC t = eff-N 보정 시 capex -3.61→-2.52 / pbr -3.72→-2.40. | PASS — ★y_60d 중첩 자기상관 = eff-N 보정 t 병기 의무(naive t 과대 회피). 보정 후에도 유의(robust). tier=structural_prior_high_confidence(validated alpha 보류). |
| **H** 미해결 | YES | candidate-ledger ⏳ 섹션(EV-EBITDA/SAAR/종목flow/PIT멤버십/LOO) + research-log 다음세션 작업 6. | PASS — 미해결 명시. |
| **I★** 생존편향 | YES | universe=FDR 현재 스냅샷(생존종목). delisted/M&A 누락. ★자동차=쌍용차→KG모빌리티 구조조정 多. | **PARTIAL** — 정직 격하(PARTIAL 라벨+note). PIT 멤버십=collector_plan high. ★over-claim 아닌 격하 = hard-fail 회피. |
| **J** spec↔code | YES | spec "유형자산/총자산 cross-sectional z → forward IC" = code csz(ppe/assets)→forward_returns. PBR=mktcap/equity. 부호 측정값 그대로(over-claim 0). | PASS — predictive forward 동일. capex prior 음=측정 음 정합. |
| **K** 다중검정 | YES | ★단일 FDR family 측정前 사전고정(measure_conditional 헤더 §3). 통합 merge(merge_fdr_family.py) m=168 BY survivors=5. M_eff 통합=supervisor. ★[G-C remediation] survivors 5 wc_p 전부 0.0005 = wild-cluster floor(1/2001) censored. | PASS — garden-of-forking-paths 차단. survivors=5(pbr 2+capex 3) = BY 보정 후 생존. ★단 floor-censored = "생존 여부"만 산업 간 비교 가능, magnitude 비교 금지(meta.floor_censored_caveat). |
| **L** 공통인자 1회 | YES | common_factor_exposure = β 보고만(cross 최종 박제 X). 통합 supervisor L축 1회 계상. | PASS — β 벡터 보고. |
| **M★** wire 충실 | YES | score_ic_breakdown_eprocess = core/assume/weight_falsification 함수 직접 호출(confidence_hooks). opt-in 측정, production 미배선(INV_R15_WEIGHTS 미접촉). | PASS — production 코드 미변경. |
| **N★** cross PSD | 부분 | cross 조립(RegimeGlasso Σ mixing) = supervisor 단계. 산업 = β 벡터 + directional_spillover 후보(CARZ) 보고. | N/A(supervisor 책임) — directional_spillover=[] 아님(CARZ 후보 보고). |
| **O★** leakage | YES | forward return=shift(-h)(미래 누설 0). reject≠missing: 상장 전 NaN=missing, regime cell=관측(reject 아님). CLI_PUB_LAG vintage 보정. | PASS — PIT-safe + tri-state. |
| **P** net-cost | YES | gross\|IC\| capex 0.103/pbr 0.108 vs 월 16.5bps cost. KR STT sell 0.20% 비대칭. | PASS — gross 보존(저회전 valuation/capex = momentum 보다 turnover 낮음). sqrt impact=supervisor. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (합성지문 통과 + DART extended) |
| C 추적성 | PASS | yaml↔raw 5 json 매핑 |
| D PIT | PASS | CLI_PUB_LAG=2 + DART rcept_dt + forward shift |
| I 생존편향 | PARTIAL | 정직 격하(쌍용차→KG모빌리티 구조조정 누락), over-claim 회피 |

★**hard-fail 0** (B/C/D PASS, I = PARTIAL 정직 격하 = hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor). ★G-C 독립 audit 충실 PASS(hard-fail 0, 2026-06-05) — capex survivors=5 진짜(LOO 17종 전부 음 + PIT-safe + size 독립 3중 검증).
- **status = PARTIAL** — 가격신호 REJECTED(OOS flip) / ★PBR value(y_60d) + capex_ratio(asset growth) = PARTIAL CONFIRMED(OOS robust, size 독립, S5 역공격 기각, tier=structural_prior_high_confidence). ⛔validated alpha 단정 보류(차기 vintage pristine OOS 후 승격).
- ★핵심 검증 가치: ① 자동차 가격 momentum = OOS flip 무효(반도체보다 약 = volume cycle) ② ★capex_ratio 신규 발견(자산집약 장치산업 = asset growth anomaly, 통합 FDR 생존, ★자산집약 산업 일반화 후보) ③ PER peak-EPS trap = cyclical 정의 입증.
- archetype cyclical 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시 = ex-post hazard 회피.
- ★[G-C remediation, 결론 불변 hedge 강화]: (1) survivors 5 wc_p = wild-cluster floor(0.0005) censored → magnitude 산업 간 비교 금지(생존 여부만). (2) y_60d IC 중첩 자기상관(AR1 0.43-0.49) → eff-N 보정 t capex -3.61→-2.52/pbr -3.72→-2.40(여전 유의), t 박제 시 eff-N 병기.
- ★small-n hedge: universe 17종 = 모든 magnitude 방향+권역만(점추정 금지). PARTIAL/TENTATIVE 라벨 준수.

## ★dispatch 게이트 self-check

| 게이트 | 충족 | 근거 |
|---|---|---|
| G-A 축 이행 | ✅ | 15축 3컬럼 + 6단계 + cross(CARZ 후보) + A-5 family_2(KRW_weak interaction 검정) + A-6 supervisor 정의대조(메인) |
| G-B 재자문 | skip 정당 | 통합 FDR survivors=5 > 0 = "신호 약함" 조건 미충족 → G-B 미발동 (candidate-ledger §G-B 점검) |
| G-C 독립 audit | ✅ 충실 PASS | 별 세션 auto-audit teammate(author≠auditor) = hard-fail 0 확정(2026-06-05). raw-v3 .py 재실행 byte-identical 재현 + capex 3중 검증. remediation 2건(floor-censored + eff-N 보정) 반영 완료 |
| G-D ledger | ✅ | candidate-ledger.md + research-log.md 작성 완료 |
| G-F frame contract 7항 | ✅ | measure_conditional.py 헤더 7항 선언(regime/interaction/단일FDR/null-MDE/PIT/turnover/wild-cluster) |
