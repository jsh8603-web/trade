---
tags: [type/split-index, domain/inv, phase/II]
date: 2026-05-29
note: Phase2 업종 rule 프레임워크를 3 main agent에 분할 위임. 각 트랙 spec이 자기완결이지만 공통 리소스/리서치는 여기로 포인터.
---

# SPLIT-INDEX — Phase2 3분할 위임 인덱스

## 공통 리소스/리서치 (모든 트랙 필독)
- **리서치 종합**: [FINDINGS-phase2-sector-rule-framework.md](./FINDINGS-phase2-sector-rule-framework.md) — 8라운드 자문 종합, 7축, 구현 디테일.
- **구현 청사진**: [IMPL-OUTLINE-phase2.md](./IMPL-OUTLINE-phase2.md) — 3층 런타임, 9모듈, v1/v2, 불변식 4, 디테일 체크리스트.
- **자문 raw 전문**: [research-raw-phase2/](./research-raw-phase2/) — gemini/claude 8라운드 원문 + claude R4 사용자 제공분.
- **세션 인계**: [handoff-inv-phase2-research-20260529.md](./handoff-inv-phase2-research-20260529.md) — 진행맥락·미해결.
- **기존 시스템 감사**: [audit-integration-findings-20260529.md](./audit-integration-findings-20260529.md) — core/* 0% 라이브 도달 등.
- **golden rule**: [IMPLEMENTATION_PROMPT.md](./IMPLEMENTATION_PROMPT.md).

## 불변식 4 (전 트랙 공통, 위반 금지)
①position=entry rule_version 고정 ②rollback=row append만(mutate 0) ③rule engine⊂emergency_stop(우회불가) ④opportunity cost(veto 차단분) attribution 계상.

## 3분할 (층 분할)
| 트랙 | 범위 | spec | 의존 |
|---|---|---|---|
| **T1 데이터·PIT 기반** | bitemporal 패널·silent revision·corp action·survivorship·데이터수집(Damodaran/French/DART/ALFRED) | [SPEC-T1-data-pit.md](./SPEC-T1-data-pit.md) | 없음(최선행) |
| **T2 구조모델·archetype·regime** | cheapness_z 잔차·structure model·archetype 5종·regime PIT·D1/D4 | [SPEC-T2-structure-model.md](./SPEC-T2-structure-model.md) | T1 패널 schema |
| **T3 rule·승격·거버넌스·관측** | signal·resolver·G0~G6·consensus·RuleObserver·kill-switch | [SPEC-T3-rule-governance.md](./SPEC-T3-rule-governance.md) | T2 cheapness_z·archetype |

## 병렬 가능 근거 (인터페이스 3 계약 — 먼저 합의)
1. **패널 schema** (T1→T2,T3): `panel/{market}/{vintage}.parquet` cols: sector(as-of), date, firm, features(filing-lagged), multiple, delist_flag, delist_ret, regime_id, knowable_from.
2. **`StructureModel.cheapness_z(firm,sector,date,as_of)->float`** (T2→T3): 음수 클수록 저평가.
3. **`ArchetypeCard`** dataclass (T2→T3): archetype tag + primary_metric + companion_signals + value_trap_guards.
T2·T3는 T1/T2 산출을 mock/fixture로 개발 가능 → 3트랙 병렬.

## 구 SPEC (2분할, 폐기 — 3분할로 대체)
~~SPEC-trackA-data-structure.md, SPEC-trackB-rule-governance.md~~ → T1/T2/T3로 재분할.

## ★ ref repo 코드 차용 결과 (subagent, 2026-05-29)

⚠️ **mlfinlab refs = 전부 stub(`pass`) + 독점 라이선스** → API 참조만, 코드 복사 금지.

진짜 차용 가능(body 검증):
| 모듈 | repo/경로 | 라이선스 | 트랙 |
|---|---|---|---|
| fixed-K regime | _refs/jumpmodels JumpModel(predict_online) | Apache-2.0 | T2 |
| DCF/EV-EBITDA/RIM/WACC | _refs/ai-hedge-fund/src/agents/valuation.py | MIT | T2·T3 floor |
| CPCV/purged CV/PBO | _refs/skfolio _combinatorial.py (mlfinlab stub 대체!) | BSD-3 | T3 G3/G4 |
| BH FDR | statsmodels multipletests(fdr_bh) | BSD-3 | T3 |
| PSR/DSR | rubenbriones/Probabilistic-Sharpe-Ratio(~40줄) | MIT | T3 G4 |
| KR 데이터 | _refs/pykrx(real)·FinanceDataReader·OpenDartReader·dart-fss | — | T1 |
| 기간분절/BOCPD | ruptures·bayesian_changepoint_detection·river | BSD/MIT | T2 |
| HDP-HMM open-K | pyhsmm·bnpy(reference-only, 무거움) | MIT/BSD | T2 후순위 |
| Damodaran | xls pandas read_excel(URL직접) | free | T1 |

바닥부터(차용없음): cheapness_z 구조모델(R4핵심)·archetype·rule resolver/G0~G6/consensus·RuleObserver/kill-switch·KR 섹터멀티플 vintage(최난, pykrx 스냅샷 자체구축).
top3: ①skfolio CPCV(stub 대체) ②ai-hedge-fund valuation ③jumpmodels.
