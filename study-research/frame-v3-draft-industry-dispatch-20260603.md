---
tags: [type/frame-draft, domain/inv, scope/equity-industry-dispatch, status/draft-for-consult]
date: 2026-06-03
purpose: 산업 섹터 subagent dispatch 양식 v3 초안 — coin 측정 15종(주식 적용 14) + 15축 audit + 6프로세스 + 레퍼런스 통합. 자문 3R 검토 대상.
base: study-research/eq_kr/frame.md (v2) — 본 v3 는 v2 대비 델타. v2 §0~§11 base 유지.
---

# frame v3 초안 — 산업 섹터 dispatch 양식 (coin 측정 방법론 15종 그대로 이식, 주식 적용 14 — intraday만 제외)

> **사용자 지시**: "cross 등등은 예시고 더 있다. 코인에서 쓰고있는 방법론을 그대로 가져와라(within/family 등). 15축으로 기준 변경, 6단계로 검토."
> **범위**: eq_kr(v2) → eq_kr + eq_us 범용. 산업(섹터)이 1차 작업 단위, 거시국면/산업분위기 = 렌즈.
> **본 문서 = v2 대비 델타만**. 미변경 부분(§1 Tier, §2 y정의, §3 Layer, §5 8파일, §7 yaml)은 v2 SSOT 유지.

---

## 0. 뼈대 선언 (★사용자 박제 2026-06-03, 최우선)

- ★**뼈대 = 우리 것**: (1) **stock.md 산업 study 계획** (2) **coin 코드 구조** — `study_session.yaml` 7블록 + 측정 파이프라인(`.p2-*.py`: rank_ic_nw / walkforward-regime 4게이트 / netcost) + `weight_falsification.py` e-process falsification + `conditional_correlation.py` RegimeGlasso. 이 구조가 산업 주식 dispatch 의 뼈대.
- ★★**진짜 산업구분 척추 = `core/structure/archetype.py` 5종 archetype**(cyclical/event_driven/spread_driven/asset_stable/compounder + commodity/crypto). coin(`crypto_btc→monetary_store`)·commodity·equity 를 **하나의 추상으로 통일** = 사용자 "coin 프레임=뼈대"의 실체. 각 archetype = primary_metric(싸다의 척도)+value_trap_guards(함정)+cycle_drivers, `valid_from` 시변(엔비디아 cyclical→compounder) 설계. **"산업 구분 적다"의 정체 = `DEFAULT_SECTOR_ARCHETYPE` equity 10key(@187-209)만 + `archetype_for_sector` 미등록→cyclical fallback(@214)**. provider(French49/KRX)/GICS = 그 위 cheapness 데이터 층(계층, 경쟁 아님). → 보강 작업 = sector→archetype 매핑을 **stock.md 산업구분에 맞춰** 전수 + valid_from 카드. ⚠️ **미국 = GICS 11 sector 표준 아님** — stock.md eq_us 가 다회차 확정한 **Mag7 custom basket(T0=Mag7+AVGO/ORCL/AMD) + macro-sleeve 2-4축(PCA eff_N 실측)** 구분이 SSOT, GICS sector 는 하위 라벨. 한국 = eq_kr 12산업 구분 그대로. 즉 archetype 배정 단위 = stock.md sleeve/산업.
- ★**외부 = "더 축이나 우월한 측면이 많을 경우에만" 차용** (ai-hedge-fund / FF5 / French49). 무조건 차용 금지. 우리 stock.md+coin 구조가 이미 동등/우월하면 우리 것 사용.
- ★**차용 검증 의무**: 차용한 분류·방법론이 실제 우리 데이터(미국/한국 주식)에서 **작동하는지 데이터로 검증** (S2 실측 + S4 재검증). "French49 가 미국 주식 산업 흐름을 실제로 잡나", "이 산업 분류가 미국/한국에서 유효한가" 같은 검증 없이 차용 박제 금지. = "차용인 이유" 자체를 데이터로 정당화.

---

## A. 6 프로세스 (S1~S6) — coin 표준 명시 [v2: 산출물 8파일만 있고 프로세스 단계 암묵]

각 산업 subagent 가 신호 1개를 검증하는 단계 (coin crypto study 표준 그대로):

| 단계 | 정의 | 산출 |
|---|---|---|
| **S1 논문 ground** | 산업 cycle 학술·증권사 in-depth 정독 (자문 복붙 금지, URL/DOI) | theory-notes.md |
| **S2 실측가설 (4게이트)** | G1 ex-ante / G2 Bonferroni·FDR / G3 walk-forward OOS / G4 Newey-West HAC | validation-*.md |
| **S3 외부검토** | gemini+claude 병렬 자문, 자문이 제시한 falsification 검토 | round-N.md |
| **S4 다른데이터 재검증** | cross-asset / leave-episode / within-period / partial-corr / placebo / horizon sweep | validation 보강 |
| **S5 역공격 수렴** | 가장 엄격한 반증 직접 투척 → 생존 or 다관점+내데이터 1점 수렴 | self-audit |
| **S6 15축 audit** | 독립 감사관 raw 재현 (hard-fail 0 확인) → status 확정 | 12axis-audit.md → 15axis |

★ v2 의 "라운드 1~5 일정 가이드"(§11)를 S1~S6 으로 재정렬. S4 가 v2 에 가장 부족했던 단계.

---

## B. 측정·robustness 15종 (coin 그대로 이식, 주식 적용 14) — [v2 M4 5게이트 → 확장]

> coin 이 신호 1개에 적용하는 측정 방법론 전체 = 15종(아래 1~14 + intraday). v2 의 5게이트(N/SE/power/FDR/OOS)는 이 중 일부. 주식 적용 = intraday(코인 1-6h microstructure) 1개만 제외, 나머지 14 충실 이행(net-cost·cross·family = 수치·대상만 주식 조정, 빼는 것 아님).

### B.1 핵심 측정 (4)
1. **Rank-IC** (횡단면 Spearman, 신호→forward return) — v2 M1
2. **Horizon sweep** (5d/20d/60d/1Q/6-24M lead-lag, 최적 lead-time) — v2 §2 + ★falsifier(D 절)
3. **Cross-asset** (다른 자산/섹터 재현, 부호 일관 ±0.15) — ★v2 부재
4. **Regime-conditional 4게이트** (아래 B.2)

### B.2 Regime 4게이트 [v2 M3 36cell + 게이트 명시]
- **G1 ex-ante**: 신호 진입 시점에 이미 관측가능한 상태로 라벨 (달력컷·사후분할 금지)
- **G2 Bonferroni/FDR**: 시도 N 공시 → α/N. ★주식 조정: 약신호 power 위해 **FDR 우선**(coin은 Bonferroni)
- **G3 walk-forward OOS**: regime 룰 in-sample 고정 → rolling fold 부호 일관 (hit>55%). skfolio CPCV
- **G4 Newey-West HAC**: overlapping forward → 자기상관 보정 SE (lag=horizon). block-bootstrap 병행

### B.3 Robustness 재검증 (8) — ★v2 대부분 부재 = 핵심 이식
5. **leave-episode**: 최강 기간 제외 후 생존 (single-episode artifact 판별)
6. **within-period**: 동일 regime 내 sub-split(분기/월) 부호 일관 ≥50% (between-episode level shift vs within 추세 구분) ← 사용자 "within"
7. **partial-corr**: 공통원인 통제 후 직교 잔존 (partial-IC > 0.5×marginal). graphical lasso conditioning
8. **placebo**: 반증조건 사전 명시 (e-CUSUM 붕괴 등)
9. **effective-N tier**: autocorr 보정 n_eff → Validated(≥100)/Tentative(50-100)/Weak(30-50)/INSUFFICIENT(<30)
10. **net-cost**: gross IC → net Sharpe (거래비용 차감). ★주식 조정: 기관 0.03%/side (coin 0.30%, 100배 차이)
11. **e-process**: e-CUSUM anytime-valid (e-value≥20 retract) — weight_falsification.score_ic_breakdown_eprocess
12. **block-bootstrap**: block=60-90d, B=2000, 95% CI 0 포함→비유의

### B.4 Factor family (2) ← 사용자 "family"
13. **within-family neutralization**: 같은 factor family(value/momentum/quality/size) 직교화 → 독립 alpha vs 기존 factor β 구분 (Ken French FF5 + toraniko)
14. **cross-asset family**: 섹터가 gold/equity와 공유하는 factor(VIX/dollar/oil/rate) 노출 → L축 1회 계상

---

## C. cross 축 — 분석 단위 간 상관 [v2 부재, 사용자 핵심 요구]

> ★**cross 정의 (사용자 박제 2026-06-03)**: cross = **분석 단위 간 상관관계** = (i) 다른 산업군 간 (ii) 다른 자산(금·채권·코인 등) 간. coin 의 **btc-eth 상관**처럼 단위 쌍의 관계다. ⛔ within-industry 지표 상관·다른 의미의 상관이 **아니다**. (혹시 이견 = 없음. 단 아래 측정 3종으로 확장.)

**그 "단위 간 관계"의 측정 3종** (산업.py·GitHub 에 지표 소스 부재 → 학술 리서치 a5d1c8bc 결과):
- **(a) 동시 상관** (contemporaneous): coin btc-eth 식. 인프라 = `RegimeGlasso`(conditional_correlation.py) + belief-mix Σ_eff. **보유**.
- **(b) 방향성 spillover** (lead-lag): ★신규 = **DY connectedness index**(Diebold-Yilmaz 2009/2012, generalized VAR FEVD, 11 GICS rolling → total/net/pairwise). 선행 섹터 식별. 무료=Yahoo 섹터 ETF. 보유 인프라(동시 상관)와 직교 = 사각지대.
- **(c) 구조 linkage** (supply-chain): ★신규 = **customer-supplier momentum**(Cohen-Frazzini 2008 JF, I-O 가중 lagged 섹터 수익 선행, ~88bps/월) + **I-O network centrality**(Acemoglu 2012 Econometrica, Leontief inverse 중심성). 무료=BEA I-O table + SEC EDGAR.

**신규 우선순위 = (b) DY + (c) customer momentum/centrality** (보유 RegimeGlasso 가 못 잡는 방향성·구조). ⚠️ 보강만: 섹터 macro-beta 벡터(cross pool VIX/dollar/oil/rate 와 부분 중복). ⚠️ 거의 중복: Factor Graphical Lasso(RegimeGlasso 와 동일 메커니즘). ⛔ **sector rotation business-cycle clock = 학술 "myth"**(Molchanov 2024) — 모멘텀 rotation 만 tentative.

**분담**: 산업 subagent = (i) 자기 산업 공통인자 exposure β(VIX/dollar/oil/rate/credit) 보고 + (ii) DY/customer 선행 신호 후보 보고. supervisor 통합 = cross 조립(1회 계상, PSD eigh-floor, L축). 산업이 직접 cross 상관 최종 박제 금지(L축 중복).
⚠️ DY·glasso 모두 VAR/표본 의존 → rolling window n 명시 + 추정오차 CI 의무.

---

## D. horizon falsifier — forward alpha 부재 [v2 부재]

> coin 교훈: cross-asset forward lead-lag 전멸, contemporaneous risk-on/off dominant.

- 모든 산업 finding 에 **forward vs contemporaneous 양쪽 측정 의무**. 부호 다르면 mechanism 재해석.
- forward IC 약하면 단독 베팅 근거 X → (a) contemporaneous risk regime 모니터 (b) valuation mean-reversion 중기(value_trigger 게이트) (c) event-driven.
- ★regime-conditional 의 정직성: "refinement 도구이지 creation 아님"(coin PoC 11중 1 생존) 명시. 거시국면 상관조정 = **risk 관리(sizing/prior/de-risk)이지 alpha 생성기 아님**.

---

## E. 15축 audit (A~P) [v2 12축 A~L → 15축]

v2 12축(A~L) + coin 3축:
- **M 코드충실(wire)**: opt-in off = byte-identical (golden test tobytes)
- **N cross관계 PSD**: read-time PSD 합성 + 공통인자 1회계상
- **O leakage**: PIT-safe(as_of) + reject≠missing tri-state
- (+ **P net-cost robustness**: gross 50% 보존 — B.3 #10 과 연동, audit 항목화)

Hard-fail 코어: B(실데이터)·C(추적성)·D(PIT)·I(생존편향) + 조건부 J/K/L/M/N/O.

---

## F. 뼈대 vs 보강 (★우리것 우선 / 외부는 우월할 때만 + 차용 검증)

| 기능 | **뼈대 (우리것)** | 외부 옵션 | 차용 조건 (우월시만) | 차용 검증 (S2/S4) |
|---|---|---|---|---|
| 측정 파이프라인 | **coin `.p2-*.py`** (rank_ic_nw / walkforward 4게이트) | — | 뼈대 그대로 | 자체 |
| yaml 구조 | **coin study_session.yaml 7블록** | — | 뼈대 그대로 | 자체 |
| falsification | **weight_falsification e-process** | — | 뼈대 그대로 | self-test PASS |
| 거시국면 상관 | **RegimeGlasso** (conditional_correlation.py) | — | 뼈대 그대로 | self-test PASS |
| valuation 수식 | **우리 valuation.py** (ai-hedge 수식 차용 완료) | ai-hedge-fund | 이미 차용(우월) | ★미국 데이터 DCF 작동 검증 의무 |
| factor neutralize | 자체 회귀 (fallback) | **FF5 / toraniko** | 표준 factor = 외부 우월 | ★FF5 가 우리 universe 에서 유효 검증 |
| 산업 cheapness 데이터 | — | **French49 / Damodaran** | 데이터 소스만(분류 아님) | ★PIT + 미국 산업 cheapness 작동 검증 |
| 산업 분류 | §I 참조 | §I | §I | §I |

★ 기존자산 4: frame v2 / RegimeGlasso / value_trigger / battery·bio·consumer 완성샘플. **산업 study = 우리 뼈대 위에 검증된 외부만 끼우는 작업**(외부 차용 ≠ 무검증 신뢰).

---

## I. 산업 분류 = stock.md SSOT (★이미 다회차 외부검토 확정 — 재검토 불필요)

> 사용자 박제 2026-06-03: "stock.md 의 산업구분은 이미 다회차 외부검토를 거친 결과물." → **신규 taxonomy 선택 폐기**. 외부 GICS/ICB/GitHub 분류 채택 검토 불필요.

**섹터 구분 = stock.md (+ eq_us/eq_kr direction·frame) 확정**:
- **미국 (eq_us)**: GICS 11 sector + Mag7 custom basket (T0=Mag7+AVGO/ORCL/AMD), macro-sleeve 2-4축.
- **한국 (eq_kr)**: 12 산업 Tier (반도체 / 자동차·금융·2차전지 / Tier3 8산업).

**지표 소스/조합 (←검토 대상, 사용자 질문)**:
| 시장 | 지표 소스 | 방법 |
|---|---|---|
| **미국** | 산업.py (French49Provider cheapness 등) | ★French49 → stock.md GICS 11 sector 로 **매핑**(우리 구분 들어가는 산업만 차용) + 데이터 검증 후 사용 |
| **한국** | 산업.py 한국 지표 부재 (French49=미국) | ★stock.md 계획대로 **리서치** (battery LIT yoy 식 산업 cycle 지표 신규 발굴) |

★ 위 표 = **잠정 가설(결정 아님)**. 사용자 = "저게 맞는지 검토해서 알아봐 달라"는 질문. 리서치(외부 지표소스·매핑 타당성) 진행 중 → 결과로 아래 질문 답 후 확정.

**검토 질문 (사용자 물음 = 답할 대상)**:
- Q-i: 산업.py(French49 등) 지표를 검증 후 차용하는 게 옳나? (통째 vs 우리 구분 들어가는 산업만 매핑)
- Q-ii: 미국 지표 소스 = French49가 최선인가, GitHub/외부에 더 나은 산업 지표 소스가 있나?
- Q-iii: 한국은 지표 소스 부재 시 stock.md 계획대로 리서치가 옳나, 다른 길이 있나?
- Q-iv: 가져온 지표를 산업 신호로 어떻게 조합하나 (우리 derive_weights 충분 vs 보강)?

---

## G. 주식 특화 6조정 (coin → equity 이식 시)

1. regime = macro-driven (coin sentiment-driven). FGI/halving → inflation/VIX/curve/외국인flow.
2. intraday 불필요 (coin 1-6h microstructure 제외).
3. net-cost = 기관 0.03%/side (coin 0.30%, 100배).
4. 다중검정 = FDR 우선 (coin Bonferroni strict, 주식 약신호 power 보존).
5. family neutralization = FF5 자동화 (toraniko/자체 회귀 fallback).
6. cross-asset family pool = 6 factor(MKT/SMB/HML/RMW/CMA/MOM) (coin 3: vol/dollar/oil).

---

## H. summary.yaml 신규 필드 (v2 §7 양식 + 델타)

```yaml
# [신규] cross 축 — 섹터 공통인자 exposure (통합 단계 cross 조립 입력)
common_factor_exposure:
  - factor: VIX | dollar | oil | rate | credit
    beta: float
    beta_ci_95: [float, float]
    contemporaneous: bool   # forward 아닌 동시 노출
    source_id: str

# [신규] robustness(측정 15종) 통과 기록 (지표별)
robustness_checks:
  indicator_id: ref
  leave_episode: pass | fail        # single-episode 아님
  within_period: pass | fail        # sub-split 부호 일관
  partial_corr_ratio: float         # partial/marginal
  net_sharpe_ratio: float           # net/gross (≥0.5)
  forward_vs_contemp: str           # 부호 일치 여부
  family_neutralized_ic: float      # FF5 직교 후 잔존 alpha

# [신규] horizon falsifier
horizon_verdict:
  best_horizon: str
  forward_alpha_present: bool       # false 면 risk-monitor 용도로 격하
```

---

## J. dispatch 규칙 (★사용자 2026-06-03)

- **agent spawn = teammate** (하네스2wf transport): `TeamCreate` + `Agent(team_name, name, run_in_background)` + `SendMessage` 조종. ⛔ 일반 teamless background Agent 금지. 이유 = native auto-compact(자동 압축) + 장수명 + mid-flight 양방향 조종. 이번 세션 WireSmith(결선)가 검증한 패턴.
- **순차 dispatch = 한 시장씩 완주**: **한국(eq_kr) 12산업 전체 완료 → 그 다음 미국(eq_us)**. ⛔ **한번에 다(한국12+미국11 동시) 금지**. 한국 다 돌려 끝내고 미국, 또는 시장 단위 순차. (산업 내부는 Tier 차등 병렬 가능하나 시장 경계는 순차.)
- 각 산업 teammate = `industry-capsule-template-v3` 양식 + `frame-v3` 정독 → 8파일 산출 → SendMessage 보고.

## K. 실행 레이어 — cross-sectional 종목 선택 (★사용자 박제 2026-06-03, 핵심)

> ★사용자 박제: "산업별 어떤 지표가 의미있나로 끝나면 안 된다. **실제 매매가 일어나려면** 시총 몇 위 안 universe 에서 해당 지표가 평균 대비 얼마나 차이 나는지로 골고루 산다든지가 있어야. 그리고 PER·PBR 등 지표들의 상관계수가 계속 변하는 그림이다."

산업 study 산출이 "지표 IC 유효성"에서 끝나면 실매매가 안 일어난다. 검증된 지표를 **실제 종목 매수 룰**로 변환하는 레이어 필수. 측정 15종(C1)은 "이 지표가 유효한가"까지, §K 가 "유효 지표로 어느 종목을 사나"를 채운다.

- **입력**: 측정 15종으로 검증된 유효 지표(valuation/quality/momentum) + 그 regime별 IC.
- **universe**: 시총 top-N(또는 섹터 내 시총 랭크). 보유 = `core/data/universe_membership.py` + `stock/data/krx_universe.get_universe`.
- ★**cross-sectional spread**: universe(또는 섹터) 내 각 종목의 지표를 **횡단면 z-score/percentile**(universe 평균 대비 편차)로 랭크. ⚠️ **gap**: 현 `stock/valuation.py` = own-history 시계열 분위(자기 과거 PER 대비)지 cross-sectional 아님 → universe-relative z-score 산출 신규 필요.
- **selection**: archetype primary_metric 기준 싼 종목을 **분산 매수**(concentration cap = "골고루"). `value_trigger` 게이트로 value-trap 종목 배제(싸 보이지만 구조 붕괴).
- ★**지표 유효성 시변**(사용자 "상관계수 계속 변하는 그림"): PER/PBR/EV-EBITDA 등 valuation 지표의 IC·상호상관이 regime 따라 변함 = regime-conditional IC(C1 ④)가 측정, `derive_weights`(w∝Ω·IC)가 **시변 IC 로 지표 가중을 동적 조정** → "어느 valuation 지표를 지금 믿나"가 regime 함수. 이게 동적가중 시스템의 주식 적용 본체.
- **산출 양식**: summary.yaml 에 `selection_rule`(universe 정의 + cross-sectional 지표 + concentration cap) + `indicator_validity_regime`(지표별 regime IC 시계열) 블록 추가.

---

## 자문 3R 검토 질문 (이 초안 대상)
1. coin 측정 15종을 **그대로 이식**(주식 적용 14, intraday만 제외)하는 게 맞나, 주식 특유로 더 빠지거나 추가할 항목은? (과잉/과소)
2. cross 축의 "산업 보고 → 통합 조립" 분담이 PSD/이중계상을 정말 막나?
3. 6조정(특히 FDR 우선, net-cost 0.03%)이 타당한가?
4. forward alpha 부재 전제가 주식에도 성립하나(coin은 성립), 아니면 주식은 forward IC가 살아있나?
5. ★[분류] 미국 = GICS 11(거시연동) + French49(cheapness 세분) 병용 / 한국 = KRX-WICS 12 — granularity 타당? **차용 검증**(분류가 산업 cycle/상관을 데이터로 잡는지) 구체 방법?
6. ★[뼈대] 우리 coin 코드 구조(study_session.yaml 7블록 + 4게이트 + e-process)를 뼈대로, 외부는 우월시만 — 어느 외부 요소가 정말 우월해서 차용 정당한가(ai-hedge valuation? FF5 factor?), 어디는 우리것이 충분한가?

---

## M. ★외부검토 R1+R2 확정 반영 (2026-06-03, claude-web + gemini-web 2R 수렴 — dispatch 계약 SSOT)

> 두 모델(Opus 4.8 + Gemini Pro) 2라운드 수렴 결과. 산업 subagent + 통합 supervisor 의 **확정 작업계약**. 위 §A~§L 중 충돌 부분은 본 §M 이 우선.

### M.1 측정축 (C1 확정)
- **추가 3종 (주식 비협상, 측정축)**: ⑯ **PIT-fundamentals safety**(재작성·보고지연 stamp + 시점복원 — coin 엔 없는 문제, 미적용 시 IC 가짜 부풀림) / ⑰ **생존편향+delisting-return**(폐지·M&A 종목 최종수익 포함 + PIT universe 멤버십) / ⑱ **유동성-티어 IC**(size-bucket별 IC + cap-weighted IC — Rank-IC 동일가중이 microcap 지배 방지, 측정축이자 투자가능성 필터 이중역할). → 주식 측정 = **17종**(14 + 3, intraday 제외).
- **측정축 아님 → 신호 라이브러리로 이동**: PEAD(실적 서프라이즈 drift) / 발생액 품질(Sloan) = 검증 대상 신호지 검증 방법 아님. summary.yaml indicators_passed 후보로.
- **강등**: ⑭ cross-asset family = 산업 study 저수율 → 통합 supervisor 단계로(산업별 매번 X).

### M.2 forward alpha = primary (C3 확정)
- 산업 study 1차 산출물 = **forward 횡단면 IC**(coin 의 "부재→fallback" 프레이밍 폐기). breadth(주식 수백 종목)가 작은 IC(0.02-0.05)도 IR 누적.
- **horizon-tagged 강제**: PEAD 1-3M / 모멘텀 3-12M(본진) / value 3-5Y **장기**(★"중기 평균회귀" 라벨 삭제 — value 는 다년). 1M = 단기 reversal 음(-).
- 모든 forward 신호에 **사후감쇠 메타**(발견연도 + post-pub OOS 기대감쇠, McLean-Pontiff).

### M.3 cross = 3소비자 라우팅 (C2+R2-2 확정, §C 대체)
"3측정"을 한 cross 구조로 조립 금지(PSD 붕괴). 각 객체를 올바른 소비자로:
| 객체 | 소비자 | 경로 |
|---|---|---|
| RegimeGlasso(동시 조건부 의존) | 포트 리스크 공분산 **Σ_return** 단독 | derive_weights 리스크 |
| Diebold-Yilmaz spillover(FEVD 비대칭, 공분산 아님) | **de-risk throttle**(attenuation-only, gross 곱셈 축소) + **regime feature**(→Ω conditioning) 2채널 | 공분산·alpha 직접진입 금지 |
| customer-supplier momentum(forward 예측) | **alpha 신호** → 측정 17종 검증 후 IC→weight | 동조 성분은 RegimeGlasso Ω 자동 흡수(이중 라우팅 X) |
| I-O centrality(정적 특성) | optional 저빈도 특성(우선순위 최하) | 연 1회 갱신 |

### M.4 비용·검정 (C4 확정)
- **net-cost 모델 교체**: flat 3bps → `spread/2 + commission + sqrt_impact(order/ADV) + (KR: sell-side STT 0.18-0.23%)`, size-tier별. 한국 = 매도과세 비대칭(왕복 ~15-25bps).
- **다중검정**: e-process(LORD++) 주력 + **BY**(factor 상관 → BH 금지) batch 교차. Harvey-Liu-Zhu t-허들 ~3.0.
- **factor 정렬**: neutralize pool = pooling pool = 6factor(MKT/SMB/HML/RMW/CMA/MOM). **KR-local factor**(US factor 직교화 region mismatch). **공매도 제약 → long-only-implementable IC**(top-quantile vs benchmark spread, decile long-short 아님).

### M.5 차용 (C5 확정)
- **차용 ○**: skfolio **CPCV purge+embargo**(forward 라벨 horizon overlap → 현 walk-forward leakage 차단 + PBO) — G3 게이트 업그레이드. **characteristic factor model**(toraniko류 Barra식 횡단면 회귀 = equity risk 분해 native 우월, RegimeGlasso 는 cross-asset/regime 전담 = both). FF = region-matched benchmark/neutralizer만.
- **차용 X (우리것 유지)**: derive_weights(z-score 1/N ablation 검증) / e-process·e-CUSUM(SOTA) / yaml 7블록·card lifecycle(bespoke) / ai-hedge·Damodaran valuation = commodity(차용해도 "검증된 edge" 박제 금지, sector-relative z-score 정규화).
- **archetype**: GICS 우월(time-varying behavioral state). ★단 **valid_from 사후편향 hazard** = "엔비디아 compounder 됐다"는 ex-post → **PIT 사전선언 attestation 필드** 필수 + **soft/probabilistic 배정**(primary+secondary 확률). audit 15축이 archetype transition 사후편향 1순위 검사.

### M.6 §K 실행 레이어 확정 (R2-1 확정)
- **construction seam 신설**: score → target weight(선택집합 내 score-proportional + per-name cap + per-sector cap) → **target portfolio + rebalance trigger**. §K 산출 = raw order 아님, 기존 **IOC 5밴드 엔진**이 슬라이싱(seam 분리).
- **Σ 이중정의 해소(★사용자 "지표 상관 변하는 그림")**: **Σ_signal**(지표 간 공분산 = PER·PBR·EV-EBITDA scores 상호상관, regime-conditional, mixing 단계 — Glasso precision Θ_signal native) ≠ **Σ_return**(자산 수익 공분산 = RegimeGlasso, 리스크·sizing). derive_weights 지표가중 = w∝Θ_signal·IC. **시변 IC 만으론 불충분 → 시변 Σ_signal 까지**(empirical Bayes shrinkage, 표본 부족 시 시변 IC + 정적 Σ_signal degrade fallback).
- **rebalance** = archetype 파라미터, 신호 horizon 종속: value 3-5Y → 분기/반기 + no-trade band(매도측 더 넓게 = STT 비대칭), PEAD 1-3M → 월간.
- **concentration cap** = breadth 보존형: per-name 1-3%, 목표 50-150종목, per-sector ±X% vs bench. 타이트 캡 금지(IR 붕괴).
- **universe** = 시총 floor **∧** ADV 참여율 cap(microcap 은 ADV 로 배제). **long-only**(공매도 제약, 음의 뷰 = 벤치 비중까지 underweight + value-trap gate 가 숏측 대리).
- ⚠️ cap 수치(1-3%/50-150종목)·throttle 임계·no-trade band 폭 = 방법론 방향, **CPCV 백테스트로 캘리브레이션 필요**(점추정 박제 금지).

### M.7 ★분담 — 산업 subagent vs 통합 supervisor (R2-3 확정, 과잉설계 해소)
§K·cross 라우팅은 universe 횡단 포트폴리오 관심사 → 산업 subagent 에 못 넣음(자기 슬라이스만 봄). **중앙집중형**(두 모델 강력 권고):
- **산업 subagent (per-industry, 측정 전용 = study room)**: 17종 배터리를 자기 산업 내 측정(regime-conditional IC, PIT-safe, 생존편향 보정, 유동성-티어). 산출 = **YAML exposure card** {신호별 forward-IC, archetype, primary_metric, value-trap 파라미터, **within-industry peer-relative cross-sectional z-score**(sector-neutral 표준화 = subagent 담당, R2-1 gap 메움), PIT/생존/유동성 메타}. ⛔ 주문·Ω 조립·throttle 안 함.
- **통합 supervisor (single-writer = assembler/trader)**: 전 산업 card 수집 → universe 조립 → Σ_signal mixing + RegimeGlasso Σ_return + DY throttle → §K construction(score→target weight, caps, ADV cap, rebalance) → target portfolio → IOC 엔진. selection budget(종목수·비중) global. 자본위험 증가 transition = supervisor 만(human-gate).
- 표준화 **local**(peer-relative sector-neutral) / construction **global** 명문화.

### M.8 dispatch 영향
- 산업 subagent 양식(template-v3) = **M.7 exposure card 계약**으로 산출 범위 bound(측정만 → 과부하·PSD 위험 없음). §K·cross 조립·실행은 dispatch 산출 아님 = 통합 단계(별 작업).
- 즉 **이번 dispatch = M.1~M.2 측정 17종 + M.3 customer momentum alpha 후보 + peer-relative z-score card** 까지. supervisor 조립·실행 wire 는 dispatch 완료 후.

### M.9 ★거시 FHC 통합 조율 (btn-Inv ↔ btn-button, 2026-06-03)
양 트랙(거시 judge/리서치 + 주식 산업)이 **같은 primitive 독립 발견** → 인프라 단일화 합의. SSOT(거시) = `.consult-judge-report-RESULTS.md`(C1~C16, 5R 수렴) + `plan-judge-report-arch.md`(INV-1..16, S0~S6). 조율 = `.coord-macro-stock-fhc-20260603.md`.
- **겹침**: 메타카드=Σ_signal(§M.6) / FHC(반증가능 가설카드)=exposure card / bonus 채널+INV-8 IOC recall=construction seam(§M.6) / outcome reject leg(e-CUSUM)=wire_falsification(WireSmith 배선완료) / mediator+INV-9 regime breaker=RegimeGlasso.
- **exposure card = 주식판 FHC**. ★**2-leg 보강**: 현 confidence_hooks = outcome leg(forward IC + e-CUSUM reject)만 → **mediator leg**(전제 관찰량, 미성립=**vacate**=가점 회수·보류 ≠ reject=영구근접) 추가 = battery pilot 검증 후 schema 통합(한국 6+미국 확장 전).
- ★**[2026-06-03 사용자 확정 — 분담 역전]** **FHC core(자산무관) 단일 소유·구현 = 거시(btn-Inv)** (`core/assume/`: schema + 2-leg + 5-state lifecycle + bonus 채널(L1+bonus≤C) + INV-1..16 집행). ⛔ **주식(button)은 core 짓지 말 것**(2벌 차단). 이유 = 주식 리서치가 길어 거시가 core 먼저 짓는 게 사용자 결정.
- **주식 = Equity 인스턴스**(`stock/`): exposure card = **FHC `scope.type=sector` 어댑터**(outcome.metric=**cs_rank_IC**, mediator=섹터 펀더멘털 restatement·compute_delay PIT, e_process/cusum=wire_falsification 매핑, state 5-state) + Σ_signal mixing + construction seam(core **`emit_bonus` API 소비**, 직접 사이징 X). ★**별 schema 만들지 말 것** — template-v3 summary.yaml = FHC 한 인스턴스로 어댑트. `w_final=clip(L1+Σbonus, ceiling=C)`, C=cap per-name 1-3%.
- **INV 핵심4 정합**: INV-11(OFF byte-identical)=INV_R15_WEIGHTS off / INV-1(w≤C)=cap per-name 1-3% / INV-3 fail-closed / INV-12 alpha-wealth firewall(Σ_signal 원장=button 소유, core는 firewall만 강제). INV-9 breaker = button 소유 RegimeGlasso transition 구독.
- ★**연결시점 = 거시 core 완성 + bonus API 시그니처 통지 받으면** WireSmith가 construction seam을 그 API 소비로 plug-in. wire_falsification(현 임시 배선)도 그때 재배선. 그때까지 주식 = 산업 리서치/exposure-card(FHC sector 어댑트)/Σ_signal/construction **독립 진행**(core 의존 0). 거시는 독립 S0(P2 Test2a) 선행. 계약 SSOT = `.coord-fhc-contract-20260603.md`(§2 schema/§3 lifecycle/§4 bonus API/§5 INV).
- ★**[2026-06-03 core API 준비완료 — btn-Inv 통지]** core 구현·검증 끝(tests/assume 58 passed, 회귀 0). construction 이 소비할 API:
  - `core/assume/fhc.py`: `eval_mediator(spec, observable_value=None, *, posterior_holds=None)→MediatorState` / `update_outcome(state, signal_z, mediator_holds)` / `transition(card, state, *, mediator_state=None, graduation_decision=None)→FHCState` / `bonus_from_evalue(card, state)→float`
  - `core/assume/bonus_channel.py`: `size_with_bonus(l1_weights, card_states, ceilings, *, breaker_tripped=False)→{asset: AssetSizing}`
  - **equity 어댑트** = `FHCard(scope='sector', outcome=OutcomeSpec('cs_rank_IC'), targets=(종목들,), bonus_cap=per-name천장−L1, mediator=MediatorSpec(섹터펀더멘털, compute_delay=publication lag))`. 2-leg = mediator(holds/fails/unknown) + outcome(cs_rank_IC e-process).
  - **내 소유 유지**: Σ_signal mixing(layer 내부, core는 INV-12 firewall만) / breaker=RegimeGlasso transition→`size_with_bonus(breaker_tripped=)` / IOC ladder=construction(INV-8). ⛔ core schema·lifecycle·bonus 로직 안 짐.
  - ★**wire 시점 = battery card 산출 후 supervisor 조립부**: exposure card→`FHCard` 어댑터(`stock/`) + construction 이 `size_with_bonus` 소비 + pytest.

### M.10 ★battery pilot 결과 + 결함 처리 (2026-06-03)
- **pilot = cross-sectional 메커니즘 작동 입증 ✅**: cs_mom_6m(6M 모멘텀 z)→12M forward = CONFIRMED(IC +0.086, t_NW=3.87, p=0.0002, block-boot CI[0.032,0.132], CPCV purge12M+embargo OOS hit=1.00, within-period 2019-2025 부호일관 100%, leave-episode 생존, BY 16테스트 유일 생존). universe 4종(정적)→**29종**(FDR 섹터매칭 84→시총3000억∧ADV30억 floor), 횡단면 avg 26종. horizon §M.2 정합(12M>6M>3M). archetype cyclical 지지(valid_from 2019 PIT).
- ★**결함1 valuation 횡단면 (CRITICAL)**: pykrx 시장 스냅샷 API(get_market_fundamental/cap/sector)가 KRX 인증 차단으로 빈 응답 → PBR/PER cross-sectional 불가. **해소 경로 = DART fnlttSinglAcntAll PIT 재구성**(DART_API_KEY .env 존재 확인). 재무제표(BPS/EPS) + pykrx 무료 가격 → PBR/PER/EV-EBITDA, rcept_dt lag(=mediator.compute_delay). **6산업 공통 경로**.
- ★**결함2 customer momentum**: battery null(lithium upstream lag 비유의, §D forward-alpha falsifier 정상 작동). **§M.3 보강 = 산업별 저비용 1회 측정 + null이면 skip 기록**(통합단계 재검토 여지). battery=skip.
- 생존편향 I축 PARTIAL = collector_plan high(PIT 멤버십 delisted/M&A 포함). credit β = US HY proxy(KR HY 부재) n=35 tentative.
- ★**6산업 batch = battery valuation(DART) 완료 + 양식 완전 작동 확인 후** 진행. valuation cross-sectional 성립이 확장 전제.

### M.11 ★한국 batch 성과 — 6산업(+auto 진행) 신호 구조 상이 = 동적가중 데이터 입증 (2026-06-03~04)
| 산업 | archetype | 유효 신호(방향) | valuation 적합 | risk factor | verdict | 경계 케이스 |
|---|---|---|---|---|---|---|
| battery | cyclical(growth) | **momentum** 양(+0.086, BY생존) | 약 | credit/oil | CONFIRMED | — |
| 반도체 | cyclical(peak) | **momentum 음 reversal**(−0.065, BY미생존) + **PBR value**(24M −0.114, BY생존) | ★**PER✗(peak-EPS) PBR○** | credit(−0.190 강) | PARTIAL | 다중검정 momentum 미생존, valuation BY생존 |
| financial | spread_driven | **regime-conditional**(rate_up +0.102 vs rate_down −0.054) | 데이터 제약 | 무(전부 비유의) | TENTATIVE | ★DART 2023~ 제약 |
| consumer | asset_stable | **valuation**(value premium 방향일관, block-boot 유의) | per_z 작동 | dollar(−2.57) | PARTIAL | — |
| bio | event_driven | **변동성**(cs_lowvol −0.078, NW 유의) + 이벤트 | ★흑자 한정(적자 36% PER 무효) | VIX(+0.011 강, 고베타) | PARTIAL | ★멀티플 부적합 |
| telecom | asset_stable | **valuation 재현**(pbr/per 음, BY 6생존, LOO robust) | value premium(방향) | n 협소 비유의 | PARTIAL | ★universe 13종 magnitude 과대 |
| auto | cyclical(peak) | ★**PBR value**(momentum 무효 대체, BY 4생존, LOO robust) | ★**PER✗(peak-EPS) PBR○** | 공통인자 비유의 | PARTIAL | n=17 magnitude 과대(small-n hedge) |
- ★**산업별 (a)유효 신호 (b)부호 (c)valuation 적합도 (d)risk factor (e)데이터 양식 전부 상이 = 동적가중**(regime/산업 conditional IC, `derive_weights w∝Θ_signal·IC`) **정당화 데이터 입증** = 사용자 "지표 상관 계속 변하는 그림" 실증. 7산업이 momentum/reversal/regime-conditional/valuation(×3 재현)/변동성 각 대표 = **4 archetype 전수 커버**(cyclical/spread_driven/asset_stable/event_driven).
- ★**archetype별 valuation metric 적합도 데이터 입증(auto 결정적)**: auto = PER cross-sectional IC≈0(per_z 3/6/12M = +0.003/+0.004/−0.007) = **사이클 정점 EPS↑→PER↓ 왜곡 → PER 무효**, PBR value premium 이 대체(IC −0.46 방향 robust). = ★`core/structure/archetype.py` cyclical 정의("primary=P/B, trap=peak-EPS") 를 **실데이터로 정확히 입증**. 정리: cyclical=PBR○ PER✗(peak-EPS) / asset_stable=PER value○(consumer·telecom) / event_driven=멀티플 부적합(bio 적자). = §M·§K 의 산업별 valuation metric 차등(시변 적합도)이 가설 아닌 측정 사실.
- ★**부호 검증 = archetype 판별 결정적**(battery 양 momentum growth vs 반도체 음 reversal cyclical — 같은 cyclical라도 growth/peak 구분). consumer↔telecom 둘 다 asset_stable value premium 재현 = 산업 분기 robust.
- ★**event_driven 추가 발견(bio) = 멀티플 보편성 반증**: PER/PBR 이 모든 산업에 적합한 게 아니다. 적자 비중 큰 event_driven(bio 적자 36%)은 멀티플 무효 → 별 신호(변동성/파이프라인 이벤트) 필요. = §M 양식이 archetype별 신호 차등을 잡아냄 + §K execution 의 지표 적합도 시변성 근거.
- ★**3 양식 경계 케이스(over-claim 회피 정직 격하)**: (1) 데이터 부재 = financial DART 2023~ (2) 멀티플 부적합 = bio 적자 지배 (3) universe 협소 = telecom 13종 → small-n magnitude hedge(방향 신뢰, magnitude 보수 cap). n<5(telecom service sub 3종) = INSUFFICIENT, ~13종 = 방향만.
- ★**universe 화이트리스트 필수(공통 결함)**: KRX FDR Industry 키워드 부정확(금융지주↔일반지주 CJ/GS 혼입, 화장품 아모레=「기타화학」·식품 CJ제일제당=「기타식품」 누락, 삼성/LG전자=「통신방송장비」 오분류). 산업별 이름 화이트리스트 + 상위 종목 육안 sanity check 의무.
- ★**생존편향 산업차**: bio = 임상실패→상폐 잦음 = delisted 누락 IC 상향편의 최악 → PIT 멤버십 우선순위 high. 전 산업 현 스냅샷=생존종목 한계 공통.
- **DART 양식 제약**: 금융업 2023~만(IFRS 별도양식 PER 허수), 표준계정(제조/소비재/바이오) 2019~ 완전 → 산업별 valuation 측정 가용성 상이.

### M.12 ★S3 외부검토(gemini+claude 수렴) + 독립 audit + 24M overlap 점검 = 측정 방법론 정정 (2026-06-04)

> 6단계 S3(외부검토) 누락분(auto/financial/telecom) 사후 자문 + S6 독립 cross-audit + 24M overlap 코드 점검 종합. ★전 산업 공통 정정 = 감사 방어 의무.

- ★**24M_value horizon = degenerate 증거 (전 산업 강등)**: 24M forward를 월간 샘플링하면 창이 **23/24 겹침** → **eff_indep_N = n_months/24 ≈ 2.5**(financial n=7 → 0.3). NW lag=24(충족)여도 t는 구조적 과대(auto pbr t=−17.6 / telecom −12 = small-universe[13~17종] × 24M overlap **이중 inflation**, 역설 = t 최대인데 증거 최약). block-bootstrap block=3(전 산업 고정)도 ≥24 미달이나 IC 극단 case엔 부차적(telecom block3 vs block24 CI 둘 다 0배제). → ★**조치: 24M_value를 primary verdict 근거에서 강등, 3M/6M/12M(eff_N 10~45) primary 재배치**. 24M 인용 시 "eff_N≈2.5 degenerate, 방향만·magnitude+significance 둘 다 overlap inflation" 라벨 의무.
- ★**peak-EPS trap 메커니즘 정정**: 1차 원인 = 적자 아니라 **earnings cycle 진폭**(흑자 기업도 peak EPS 高→저PER trap 작동). 적자비율은 2차 증폭기. ⛔**시총에 인과 귀속 금지**(size factor 혼동 — 시총은 earnings 안정성 proxy일 뿐). PER → **E/P(earnings yield, 음수익 연속 처리)** 또는 Gross Profitability/PCFR 대체 권고. 미국 us_cyclical PER○ = "consistent with"(동일 파이프라인 재측정 아님, ⛔"explained by" 아님). ★**peak-EPS = 시장·시총 의존**(한국 중소형 적자多 PER✗ vs 미국 대형 흑자 PER○) = 동적가중·metric 적합도 시변 증거.
- ★**small-n magnitude 정직성**: n<20 cross-sectional Spearman t는 협소 universe artifact. 점추정 magnitude **50~70% haircut**(EB/James-Stein shrinkage: ρ−0.46 → posterior −0.12~−0.20 권역) 또는 **breadth-adjusted IR**(IR=IC·√breadth, breadth=종목수×독립기간) 병기 의무. ⛔24M magnitude literal 인용 금지. ★sector-neutral z-score가 13~17종 demean이면 중립화 효과 ≈0(별 sector factor 제거 아님).
- ★**financial regime-conditional = hypothesis-generating only**: 37개월 rate_up/down split = regime당 ~18개월, independent episode ≈2 = overfit. NIM ex-ante prior 강 → 탐색 가설 방어 가능, ⛔**confirmed 불가·live 제외**(2번째 금리 cycle까지 보류). regime split 대신 **interaction term**(ΔRate × cross-sectional, 자유도 보존). regime별 block-boot CI 부착 의무(현 점추정만 = small-n §1.1c 미충족, S6 audit 권고).
- ★**누락 측정축 (collector_plan + 후속 의무)**: breadth-adjusted IR / net-of-cost(13~17종 illiquid long-short, KRX 공매도 규제·turnover) / **size-orthogonal PBR**(small-cap value 위장 점검) / IC term-structure 단조성(premium이면 horizon 단조, artifact면 들쭉) / 음수 EPS·음수 book 처리 규칙 명시 로깅 / survivorship-delisting(13~17 universe에서 1~2종 탈락이 결과 좌우).
  - ★**[skip 사유 박제 — reflection-verify 2026-06-04 불일치 해소]**: 위 6축 中 survivorship-delisting 만 8 산업 collector_plan 전수 등록(R), net-of-cost 3/8(battery/semi/auto). **breadth-adjusted IR / size-orthogonal PBR / IC term-structure 단조성 / 음수EPS-book 로깅 4축 = 본 frame §M.12(dispatch SSOT)에 1차 등록, 산업 카드 미하강은 ★의도** — Phase 7 통합 단계에서 8 산업 collector_plan 일괄 하강(breadth-IR·net_cost 5산업 보강 telecom illiquid 우선 포함). 이유 = 4축은 sleeve 횡단 공통 측정 인프라(breadth/size factor/term-structure)라 산업별 분산 등록보다 통합 register 가 SSOT 정합. ⛔ 통합 시 미하강 = 누락 = 감사 대상.
- **block-boot block 코드 수정**: block=3 → horizon 비례(≥horizon_months) = 부차적 개선(근본은 eff_N, 코드 수정으로 독립표본 안 늘어남).
