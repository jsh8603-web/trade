---
tags: [type/handoff, domain/inv, track/T2, topic/assumption-lifecycle-v2, session/btn-button]
date: 2026-05-29
session: btn-button
design: ./DESIGN-button-v2.md
progress: ./progress-T2-assumption-20260529.md
consult_decisions: ./CONSULT-DECISIONS-button-v2-20260529.md
consult_raw: [./.consult-button-R1.txt, ./.consult-button-R2.txt, ./.consult-button-R3.txt, ./.consult-button-R4.txt, ./.consult-button-R5.txt]
---

# 인계 — 가정 라이프사이클 v2 BB-1~5 (btn-button T2)

## 재개 한눈 (다음 세션 = 동등 수준 재개)
- **과제**: btn-Codlearn 디스패치, cwd=D:\projects\Inv (세션명 btn-button). BB-1~5 = 거시 학습·검증·판정 통계.
- **자문 5R saturation 완료** (gemini Pro + claude Opus 4.8). 설계 SSOT = `DESIGN-button-v2.md §10.1~10.7`. 결정요약 = `CONSULT-DECISIONS-button-v2-20260529.md` (btn-Codlearn psmux 전달 완료).
- **python**: `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (numpy/pandas/pydantic OK, **bnpy/ruptures 미설치**).

## 완료 (V0~V3, 전부 `python -m <mod>` self-test PASS)
| 파일 | 내용 |
|---|---|
| `core/assume/card_contract.py` | 공유 계약 AssumptionCardLike(Protocol)+BaseAssumptionFields(frozen)+assert_falsifiable. domain=macro/equity/commodity/crypto. ★btn-Codlearn 이 core/assume/ 병렬 작성중(judge.py 존재) — card_contract.py 만 내 소유 합의(그들 __init__.py 명시). |
| `core/brain/macro_assumption_card.py` (BB-1) | 6+1 AnomalyCase→MacroAssumptionCard 승격. FALSIFICATION_BY_CASE(케이스별 반증). anomaly↔card 어댑터. add_candidate_card(신규). MACRO_DECOUPLING_CARDS 상수. |
| `core/brain/correction_loop.py` (BB-2) | LiveCorrelationLoop. JM filter/smoother divergence→CorrectionRecord harvest→ingest_correction(live). recall_for_classify(PIT mask). attach_to_classifier(read+write 동일 model). |
| `core/structure/assumption_validation_engine.py` (BB-4) | AssumptionValidationEngine. card.kind dispatch→validate_*→holds_now + 가정별 LORD++ FDR(자산클래스 격리 키=(domain,id)) + 부활차단 + compile_falsification. ValidationVerdict. ledger 이벤트 주입식. |

## 남은 작업 (V4~V6)
- **V4 BB-3** `core/regime/regime_discovery.py`: numpy-only open-ended regime 발견. BOCPD(`core/structure/detectors.Bocpd`, 1-D 요약 timing) + **Hotelling T²/χ² novelty(full 다변량, σ 아님 — F=(n-p)/(p(n-1))·T²~F_{p,n-p}, n≥3p)** + 후보발행을 LORD++ 로 wrap + dwell·time-separation(과거1년 무재현)·economic-overlay. CandidateRegime(status=candidate, 자동승격 X). HumanApprovalGate.approve(사람만→regime_model_version bump)/reject. bnpy seam(try import, 미설치 graceful). 재현=booster(kill 아님). self-test: 기존 regime→candidate 0 / 신규 분포→candidate≥1 / approve 만 version bump.
- **V5 BB-5** `core/structure/archetype.py` 확장 + `config/archetypes/*.yaml` + `core/structure/commodity_assumptions.py`:
  - archetype 추가: CommodityCarryCard/SeasonalCard/InventoryCard + crypto MonetaryStoreCard/NetworkUtilityCard/SpeculativeFlowCard. ARCHETYPE_NAMES/_CARD_CLASSES/DEFAULT_SECTOR_ARCHETYPE 확장. (기존 equity 5 패턴 그대로.)
  - commodity_assumptions.py: carry(convenience-yield rolling-z + carry→fwd-return slope prequential) / seasonal(월dummy F-test + STL strength + OOS) / inventory(variance-ratio Lo-MacKinlay + threshold-regression Hansen, COT=companion 강등) / oversupply decoupling. crypto: MVRV mean-revert(realized-price), netflow guard=비활성 stub(유료 전, band 보수).
  - config yaml: commodity_carry/seasonal/inventory + crypto 3종. `load_cards_from_config` 검증.
- **V6**: 전 self-test + 기존 25 regression(`python -m core.structure.assumption_stats` 등) PASS + DESIGN/progress 최종화 + btn-Codlearn 재보고(완료 + 계약 표면).

## 미해결 / 교차세션 조율
- **event ledger 본체 = btn-Inv(T1) IA-1** (결정 PIT log + outcome join). 내 BB-4 = read-only 주입식 소비. schema 합의 필요(11 event type, (assumption_id,version) join, FDR decision_time 불변).
- **R5 맹점 1 cross-asset cascade**: FDR 스트림 분리가 거시 regime cross-asset 동시영향 무시 → 상위 regime 변화 시 하위 cascade reset = T3 ATMS 의존전파 조율.
- **R5 맹점 2 revision-drift**: 거시 사후수정 시 결정-vs-수정진실 괴리 monitor = btn-Inv vintage 연계.
- crypto on-chain(MVRV/realized-price/SOPR) 데이터 = CoinMetrics Community 무료, btn-Inv 데이터 도메인. proxy 금지(transition 체계오류).
- 구현 순서 R5 권고 = Walking Skeleton(ledger 배선 먼저) — ledger=btn-Inv 라 내 쪽은 카드/검증/발견 우선, ledger 주입식.
