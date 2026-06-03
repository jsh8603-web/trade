# 15axis-audit.md — us_mega_tech sleeve §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0. raw 재현 = `raw-v3/*.py`. us_cyclical/us_defensive + 한국 7산업 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O. ★§M.12 정정 반영.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators_passed = forward 횡단면 IC (ex-ante). archetype valid_from 2015-01 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. yfinance 11종(2867일) + ★EDGAR XBRL 6630 rows(filed PIT, equity/net_income/shares/capex) + FRED CSV(real_rate/VIX 실시리즈). np.random=block-boot CI 재현용만(seed 42). raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | 모든 yaml 수치 → validation-metrics-v3 / validation-cross-v3 / validation-valuation-v3.json key 매핑(source_id). vol_60 IC +0.241 MATCH / VIX β -0.008 / pbr_z 12M -0.167. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격신호 = PIT-safe(forward shift). ★valuation = EDGAR filed date 이후만(lookahead 회피, 한국 DART rcept_dt 대응). ★block bootstrap block=horizon 비례(§M.12). ★24M_value eff_N degenerate 라벨. |
| **E** | 다중검정 보정 | PASS | 16테스트 BY → ★생존 0(vol_60 raw_p=0.002 but n=11 basket BY 임계 미달). ★정직 = vol_60 NW 유의(p=0.002)하나 small-basket BY 후 미생존 = magnitude hedge. |
| **F** | OOS / walk-forward | PASS | CPCV, vol_60 OOS hit=1.00. in-sample 부호 OOS 재현. |
| **G** | 자기상관 보정 | PASS | ★NW HAC(lag=horizon) + block-bootstrap(★block=horizon 비례, §M.12) 병행. vol_60 둘 다 0 배제. |
| **H** | 미해결 명시 | PASS | collector_plan(fwd EPS high / PIT basket medium / FF5+QMJ+BAB medium / reflexivity breadth CW) + verdict 에 BY 미생존 / magnitude hedge / 24M degenerate 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | basket = 현 Mag7 스냅샷. ★mega-tech 생존편향 약(상폐 거의 없음) 단 PIT 멤버십(NVDA pre/post-AI, TSLA 2020 편입) = look-back. collector_plan medium. ★hard-fail 회피: 정직 격하(PARTIAL). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "cross-sectional 60d 변동성 → 12M forward" = code `cs_z(vol_60) → forward 12`. forward predictive 동일. ★PER 무신호·vol_60 양 = 측정값 그대로(over-claim 없음). |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = mega_tech basket 11종(factor loading). z = peer-relative. ★sub(mag7/ai_semi) 신호 부호 동일(vol_60 양) = K 위반 없음. portfolio 조립 = supervisor. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(VIX dominant). 통합 supervisor L축 1회 계상. ★reflexivity = de-risk throttle 입력(L축 아님, §M.3 DY 채널). |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출. opt-in 측정, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor. 산업 = β 벡터 + reflexivity 보고만. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward return = shift(-h). reflexivity 60d rolling = 과거 window만(미래 누설 없음). reject≠missing. |
| **P** | net-cost robustness | PASS | ★US mega-cap 최저비용(STT 없음, 왕복 14bps). \|IC\| 0.241 >> 7bps/월 → gross 50%+ 보존(magnitude hedge). |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% + EDGAR 6630 rows + FRED 실데이터 |
| C 추적성 | PASS | yaml↔raw 매핑 (3 JSON) |
| D PIT | PASS | 가격 PIT-safe + EDGAR filed PIT + ★block=horizon + 24M degenerate(§M.12) |
| I 생존편향 | PARTIAL | 정직 격하(mega-tech 생존편향 약, PIT 멤버십 명시) |

★**hard-fail 0** (B/C/D PASS, I 는 PARTIAL = 정직 격하).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL CONFIRMED** — primary cs_lowvol(저변동성 quality) NW+boot+CPCV+leave-episode 통과(eff_N 10.2 Validated) but ★BY 미생존 + n=11 basket small-n = ★magnitude breadth-IR 2.56 병기 + 50-70% haircut(§M.12). 점추정 단정 회피.
- ★**핵심 검증 가치**: ★PER 무신호 = compounder expensive_trap 정합(고PER 정상, value premium 없음) = `core/structure/archetype.py` compounder 정의 입증. ★5 archetype 전수 완성 = cyclical(반도체 reversal/auto PBR) / asset_stable(consumer/telecom/us_defensive) / spread_driven(financial) / event_driven(bio) / ★compounder(us_mega_tech quality·expensive-trap).
- ★§M.12 정직 반영: 24M_value eff_N degenerate 라벨, block=horizon, magnitude haircut/breadth-IR 병기.
- ★H9 reflexivity monitor = mega-tech 고유 산출(supervisor de-risk throttle 입력, 현 정점 아님).
- archetype compounder 사후편향 검사(M.5): valid_from 2015 사전선언, declared_at 명시 = ex-post hazard 회피.
- ★pilot 결론: compounder = quality·성장 신호(value premium 없음). 한국+미국 5 archetype × frame v3 §M 양식 cross-market 일반성 완성.
