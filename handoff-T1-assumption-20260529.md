---
tags: [type/handoff, domain/inv, phase/II, track/T1, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-Inv
task: ./TASK-T1-assumption-research-20260529.md
consult: [.consult-R1-claude.txt, .consult-R1-gemini.txt]
note: 가정(Assumption) 라이프사이클 데이터·PIT 계층 리서치+설계. 다음 세션 동등 재개용.
---

# 인계 — 가정 라이프사이클 T1(데이터·PIT) 리서치+설계

## 0. 과제 (TASK-T1-assumption-research-20260529.md)
btn-Codlearn(T3)이 던진 신규과제. 사용자가 논의했으나 findings·코드에 통째 빠진 축 = **가정(Assumption) 라이프사이클**. 산업/자산별 가정을 표로 정리 → 데이터로 주기 검증 → seed 기준을 가정에서 도출 → 틀리면 변경(잦으면 안 됨, 누적데이터로 합리적 이유) → 변경 시 의존 가정 재평가.
- scope = **거시(레짐-지표)/주식(섹터 valuation 상수)/상품(ETF·원자재 선물)** 3 도메인 전부.
- **내 담당 T1 = 데이터·PIT·검증입력**. (T2=regime-conditional 검증통계·구조모델 / T3=AssumptionCard/Registry/Validator/UpdateController+derivation seam+orphaned position 안전).
- ⚠️ 사용자 불만: "코드 일부만 만들고 끝 금지" → **prior art 실조사 + 깊은 설계 + 통합방안 3산출물**.

## 1. 산출물 3종 (요구사항)
1. `RESEARCH-T1-assumption-data-20260529.md` — 2-A prior art 적용가능성/라이선스/이식비용 표 + 권고.
2. `DESIGN-T1-assumption-data.md` — 3도메인 PIT 패널 확장 + data contract 게이트 위치 + lineage(provenance) + online FDR 상태영속 + 생존편향 정책. 코드레벨(파일:함수:계약).
3. 구현 계획 — progress 스텝, fixture vs 실데이터 go-live 구분.

## 2. ★ prior art 라이선스 실조사 결과 (Gemini Phase1, archive=~/.claude/docs/archive/research-raw/assumption-priorart-phase1-20260529.txt)
| Prior art | License | 판정 |
|---|---|---|
| **Pandera** | MIT, light | ✅ **채택** — in-process pandas, PIT 패널이 이미 DataFrame. data contract 게이트 본체 |
| Great Expectations | Apache-2.0, heavy | ❌ 과함(datasource/context 무거움) |
| Soda Core | Apache-2.0, medium | △ SQL/warehouse 지향, in-process 아님 |
| PyDeequ | Apache-2.0 | ❌ Spark JVM 필요 |
| **OpenLineage** | Apache-2.0, light | ✅ **스펙만 차용**(서버 없이 jsonl 이벤트). Marquez 서버는 불필요 |
| Marquez | Apache-2.0 | ❌ Java/Postgres 서버 |
| **onlineFDR** (R) | Artistic-2.0 | ⚠️ **Python 포트 없음 확정 → 논문서 직접 구현** (LORD++/SAFFRON/ADDIS/alpha-investing, ~수십 줄) |
| NannyML/Evidently/whylogs/Alibi-Detect | 전부 Apache-2.0, heavy(TF/PyTorch) | △ **알고리즘만 참조**(KS/MMD/Mahalanobis/PSI). rule_observer 가 PSI/PageHinkley 이미 보유 |
| 통합 OSS (registry+governed change+quant) | — | ❌ **없음 확정** → 통합 자체가 기여 영역 |

## 3. ★ 코드 현황 (subagent 정밀 조사 — 설계 통합 지점)
- **계약0 충족**: `core/pit/as_of.py:resolve_as_of(x, now=)` = canonical resolver 이미 존재(T3 산출). None→ValueError, tz정규화, 미래 reject. + `core/data/pit_query.py:set_as_of_resolver()` seam 으로 wire 가능.
- `core/data/pit_query.py`: PIT 2중 gate (① knowable_from≤as_of ② sys_time≤as_of), `PitPanel.as_of()`/`query()`.
- `core/data/pit_panel.py`: PANEL_COLUMNS 48, bitemporal 3축, `PanelAssembler`, sys_time 기본=knowable_from.
- `core/structure/panel_schema.py`: `validate_panel()` 필수컬럼 + `drv_*` 드라이버 prefix + MultipleDefinition registry(R8 정의버전).
- `core/rules/seed_builder.py`: `Signal`(id/version/archetype/feature/op/threshold/kind/effective_from/knowable_from), `SeedRegistry`, `load_signal_seeds`. **provenance/derived_from 필드 없음** → 가정 seam 추가 지점.
- `core/consensus.py`: `ConsensusJudge.run(ctx)` — high_stakes 분기, LLM+risk_gate. **object type 파라미터화 안 됨** → UpdateController 가 재사용하려면 일반화 필요(자문 D-5: fork 금지, caps 빡세게).
- `core/rules/bitemporal_store.py`: `BitemporalRuleStore.publish/invalidate/rollback/as_of_query` append-only. **assumption 별도 스트림으로 재사용**(자문 D-4).
- `core/observability/rule_observer.py`: `PageHinkley(delta,threshold).update(x)`, `psi(expected,actual,bins)`, `near_zero_mass`. **공유 detectors 모듈 추출 후보**(자문 D-6).
- `core/rules/promotion_gate.py`: G0~G6, `bh_fdr()`=**batch** statsmodels fdr_bh, PBO/PSR/DSR. **online FDR 부재 = 자문 TOP1 지적 정확**.
- `stock/data/sector_multiples.py`: Damodaran/French49 (N-T1-SECTORMULT go-live).
- `assumption` 참조 = **0건(greenfield)**.

## 4. ★ 자문 핵심 (둘 다 정독 완료, 원문=.consult-R1-{claude,gemini}.txt)
**claude(핵심)**: 4축 = "거버넌스 하의 belief revision" = ATMS + SR 11-7 + online FDR 3분야 1:1 매핑.
- A-0: 가정 종류 분리 — structural(메커니즘=regime detection) vs parametric(모수=drift/change-point). validator dispatch.
- A-1: 판정 3층(change-point 조기경보 + prequential loss 지속 + posterior 누적). ★**regime-conditional 검증 필수**(pooled 금지). 생존편향=상폐 포함 PIT.
- A-2: hysteresis = AND-gate(online-FDR ∧ effect-size ∧ dwell-time ∧ K-윈도우 ∧ regime). 
- A-3: 의존전파 = 무효화(재계산 X)+epoch topological single-pass+graph rate-limit→사람.
- ★내 데이터측 직결(D): seam = 버전드 derivation fn + provenance ref(assumption_id/version/derivation_fn_version 리스트=bipartite). **knowable_from 합성: 도출물 knowable_from ≥ max(입력 knowable_from)+계산지연**(lookahead 차단). 교차일관성 불변식(read-time): 활성 seed의 derived_from은 그 as_of 활성 assumption 가리켜야. assumption 이벤트는 bitemporal_store 라이브러리 재사용해 별도 스트림.
- C-측정: data contract 게이트가 AssumptionValidator **앞에**(계약위반=측정 incident, 가정검증 중단). ← **내 pit_query 계층 직결**.
- TOP3: (1)online FDR (2)orphaned position 정책 (3)regime 모델을 base-layer 가정 승격.

**gemini(참신)**: SPRT/CUSUM 우도비, Great Expectations 패턴, SR 11-7, Alibi/Evidently(KS/MMD), **falsifiability 메타데이터 의무**(kill_condition·falsification_metric 없으면 진입 금지), confidence→사이징.

## 5. 다음 세션 재개 포인트
1. `RESEARCH-T1-assumption-data-20260529.md` 작성 (§2 표 + 권고: Pandera 채택근거·onlineFDR 직접구현 범위·drift 재사용).
2. `DESIGN-T1-assumption-data.md`: (a) 3도메인 PIT 패널 확장 — 거시(FRED vintage)/주식(상폐포함)/상품(ETF NAV·선물 롤오버/컨탱고·계절성·재고 EIA/USDA, **신규 무료소스 조사 필요**) (b) `core/data/data_contract.py`(Pandera schema, pit_query 앞단 게이트) (c) `core/data/lineage.py`(OpenLineage 스펙 jsonl, derived_from provenance) (d) `core/data/online_fdr.py`(LORD++/SAFFRON alpha-wealth 상태영속 스키마) (e) knowable_from 합성규칙 강제 위치 (f) 생존편향 정책(거시=폐지 ETF/만기소멸 선물까지).
3. 구현계획 progress 스텝화.
4. ⚠️ 상품(commodity) 무료 데이터소스 = 미조사 → Gemini Phase2 또는 자문 1회 추가 권장(확신<80% 구간).
5. 완료/막힘 시 btn-Codlearn 에 psmux 보고(현재 DOWN이면 파일 핸드오프).

## 6. 분담 경계 (중복 방지)
T1(나)=데이터·PIT·검증입력 / T2=regime-conditional 검증통계 / T3=Card/Registry/Validator/UpdateController+derivation seam+orphaned position. 겹치면 btn-Codlearn 질의.
