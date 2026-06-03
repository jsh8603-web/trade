---
tags: [type/task, domain/inv, phase/II, track/T1, topic/assumption-lifecycle]
date: 2026-05-29
from: btn-Codlearn (T3 통합)
to: btn-Inv (T1 데이터·PIT)
ref-consult: [.consult-R1-gemini.txt, .consult-R1-claude.txt]
note: 가정(Assumption) 라이프사이클 — 데이터·PIT 계층 리서치+설계 과제. 코드 일부 X, 리서치+설계 깊이 요구.
---

# TASK(T1) — 가정 라이프사이클: 데이터·PIT 계층 리서치 + 설계

## 0. 배경 (왜 이 과제인가)
사용자가 한참 논의했으나 findings·이전 자문·코드에 **통째로 빠진 축** = **"가정(Assumption) 라이프사이클"**.
- 산업/자산별 가정을 표로 정리(예: "변동성 X구간 → 임계값 θ", "반도체는 공정주기로 PER 일시상승") →
  그 가정이 맞는지 **보고서/누적 데이터로 주기적 검증** → seed 기준을 가정에서 **도출** → 지표(feature)와 연결 →
  가정이 틀리면 **변경**(단 너무 자주 X, 합리적 이유가 누적 데이터로 설명 가능해야) → 변경 시 **의존 가정 재평가**.
- ★ scope = **거시(레짐-지표) / 주식(섹터·종목 valuation 상수·산업특성) / 상품(ETF·원자재 선물)** 3 도메인 전부.
- 기존 구현(seed_builder/consensus/promotion_gate 등)은 rule/signal 레이어(하류)만. 그 위 **가정 레이어(상류)** 부재.

⚠️ **사용자 명시 불만**: "기존에는 코드 일부만 만들고 끝냈네." → 이번엔 **prior art 실제 조사 + 깊은 설계 고민 + 우리 시스템 통합 방안**까지. 코드 스텁만 찍고 끝 금지.

## 1. 먼저 읽을 것 (외부 자문 2건 — 반드시 정독)
- `D:\projects\Inv\.consult-R1-claude.txt` (claude-web, 실무 — ATMS/SR 11-7/online FDR/regime-conditional/orphaned position/derivation seam. **핵심**)
- `D:\projects\Inv\.consult-R1-gemini.txt` (gemini-web, 참신 — SPRT/CUSUM, Great Expectations, SR 11-7, Alibi/Evidently, falsifiability, confidence sizing)
- 우리 코드 현황: `core/data/pit_query.py`, `stock/data/sector_multiples.py`, `core/structure/panel_schema.py`, `core/rules/seed_builder.py`

## 2. T1 도메인 = 데이터·PIT. 리서치 + 설계할 항목
### 2-A. prior art 실제 조사 (이름만 베끼지 말고, 우리 적용 가능성·라이선스·이식 비용 판정)
1. **data contract / expectation**: Great Expectations, Soda(SodaCL), Pandera, Deequ, dbt contracts.
   → 우리 PIT 패널에 "가정 검증 전 데이터 계약 게이트"로 쓸 수 있나? 무엇을 expect 로 선언? (멀티플 범위, null률, vintage 지연 등)
2. **lineage / provenance**: OpenLineage + Marquez.
   → seed.derived_from = {assumption_id, version, derivation_fn_version}[] 체인을 lineage 이벤트로 찍어 PIT 재현+감사 공짜로 얻는 경로?
3. **label 없는 성능추정 / drift**: NannyML(2025.6 Soda 인수), Evidently, whylogs, Alibi-Detect.
   → 가정의 holds 를 "ground truth 없이" 추정하는 알고리즘(KS/MMD/Mahalanobis) 중 우리가 이식할 것?
4. **online FDR**: R `onlineFDR`(Bioconductor) — LORD++/SAFFRON/ADDIS/alpha-investing.
   → 데이터 계층에서 "검정 시퀀스 + alpha-wealth 상태"를 어떤 스키마로 영속? (가정 재검정이 끝없어도 noise 추격 막는 핵심)

### 2-B. 설계 고민 (3 도메인 PIT 패널)
1. **생존편향 차단** (claude-basic A-1): 가정 검증 패널을 PIT 구성할 때 **이후 상장폐지/소멸 종목을 반드시 포함**(as-of 당시 살아있던 전체 모집단). 현 panel_schema 의 delist_flag/delist_ret 로 충분한가? 거시·상품도 동일 원칙(폐지된 ETF, 만기소멸 선물)?
2. **"가정 틀림 vs 측정 깨짐" 분리** (claude-basic C-측정): data contract 게이트가 AssumptionValidator **앞에** 서야. 계약 위반이면 검증 중단→측정 incident. 이 게이트를 pit_query 계층에 어떻게?
3. **3 도메인 데이터 소스 매핑**:
   - 거시: FRED vintage(ALFRED realtime), 레짐 참조지표(금리/CPI/유가/달러).
   - 주식: 섹터 멀티플 PIT(Damodaran/French cache — N-T1-SECTORMULT go-live), 상폐 포함 유니버스.
   - 상품: ETF NAV/iNAV, 원자재 선물 롤오버·컨탱고/백워데이션, 계절성, 재고(EIA/USDA 등) — **신규**. 어떤 무료 소스?
4. **derivation seam의 데이터 측** (claude-basic D): DerivedParameterSet{value, confidence_band, provenance[]} 를 PIT 로 재현하려면 knowable_from 합성 규칙(도출물 knowable_from ≥ max(입력 knowable_from)+계산지연) 을 데이터 계층에서 어떻게 강제?

## 3. 산출물 (코드 스텁 아님)
1. **리서치 노트** `RESEARCH-T1-assumption-data-20260529.md`: 2-A 각 prior art 의 우리 적용 가능성/라이선스/이식비용 표 + 권고.
2. **데이터 계층 설계** `DESIGN-T1-assumption-data.md`: 3도메인 PIT 패널 스키마 확장 + data contract 게이트 위치 + lineage(provenance) + online FDR 상태영속 + 생존편향 정책. 코드레벨(파일:함수:계약)로.
3. **구현 계획**: 위 설계를 progress 스텝으로. 무엇을 fixture 로, 무엇을 실데이터 go-live 로.
⚠️ 막히거나 확신 < 80%면 자문(`/gemini-web`+`/claude-web` 병렬) 후 진행. 단정 보고 금지.

## 4. 분담 경계 (중복 방지)
- T1(너) = **데이터·PIT·검증입력**. T2(btn-button) = **regime-conditional 검증 통계·구조모델**. T3(btn-Codlearn, 나) = **AssumptionCard/Registry/Validator/UpdateController + derivation seam + consensus 재사용 + orphaned position 안전정책 통합**.
- 겹치면 btn-Codlearn 에 SendKey 로 질의. 진행상황·완료 시 btn-Codlearn 에 보고.
