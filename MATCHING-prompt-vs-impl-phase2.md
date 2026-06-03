---
tags: [type/audit, domain/inv, phase/II, track/T3]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-phase2-T3.md
progress: ./progress-phase2-T3.md
note: 사용자 프롬프트 요구 ↔ 구현 1:1 매칭 점검. seed 확보 누락 식별 + 구현 트리거.
---

# 매칭 점검 — 사용자 프롬프트 요구 vs 구현

> 사용자 지시(2026-05-29): "리서치 데이터로 seed 확보하는 거 구현했는지 점검. 프롬프트
> 요구 기능과 구현내용 1:1 매칭, 누락 확인 및 구현." cyclical.yaml 에 사용자 직접 메모
> 발견: "우리가 사전 정의 + 파이프라인 학습 시드 무한정 + 다른 산업·기간 추가 정의(무한대)".

## 1:1 매칭표

| # | 요구 | 담당 | 구현 | 판정 |
|---|---|---|---|---|
| 1 | 주식/거시 고도화 리서치+코드 | all | findings 8R + T1/T2/T3 | ✅ |
| 2 | macro.md/quant.md 보완 | T2/T3 | structure_model·valuation seam | 🟡 |
| 3 | **D4 거시·산업 기간 학습 Book(실데이터 연동, LLM 활용)** | — | **0개** | ❌ |
| 4 | golden rule 방법론 순서 | — | findings §1 + 리소스맵 | ✅ |
| 5 | 자문 리소스 탐색 | — | 8R 수렴 | ✅ |
| 6 | D1 open-ended 비모수 레짐 | T2 | pit_regime.py(고정-K) | 🟡 v2 |
| 7 | D3 업종·기간 valuation 상수 적응 | T2/T3 | cheapness_z+archetype+signal | ✅ 엔진 |
| 8 | 평가축 5(학습/규칙화/주입/변경/기존) | T3 | S1~S9 | ✅ |
| 9 | **산업별 투자보고서→반도체 관점 변형 추출** | — | archetype card 큐레이션만 | ❌ |
| 10 | 메인 seed 박기 + 파이프라인 consensus 조정 | T3 | consensus(S9) 골격, seed 생성 없음 | 🟡 |
| 11 | **리서치 데이터→seed 확보 파이프라인** | — | fixture seed 만 | ❌ |

## 핵심 누락 4 → 구현 대상

1. **signal seed YAML** (`config/sector_rules/*.yaml`): 업종별 weak-rule 상수. 현재 `make_cyclical_signal_set()` 하드코딩 fixture 만 → YAML 외부화 + 다업종.
2. **seed 추출 파이프라인** (`core/rules/seed_builder.py`): 
   - (정량) T1 `sector_multiples`(Damodaran/French 실데이터) → 멀티플 분위 기준선 → signal threshold τ 앵커링.
   - (정성) 국면전환기 공시→밸류에이션 근거/밸류트랩 키워드 추출 LLM hook(v1=인터페이스+큐레이션 시드).
   - 무한 확장: 새 산업·기간 카드 append → consensus(S9) 가 조정/승격. 사용자 메모 "무한대" 충족.
3. **D4 Book** (`core/book/`): 거시 기간정의(ruptures 분절+FRED vintage) + 산업 특성 카드(기간별, "반도체 공정전환기 PER 일시상승" 류) → LLM 지식베이스 schema.
4. **archetype card 정합화**: cyclical.yaml 등 value_trap_guards 미완("cnt...") + yaml 깨짐 정정. value_trap_guards 사전정의 채우기.

## 설계 원칙 (사용자 메모 반영)
- **메인(나)=seed 사전정의** (정량은 실데이터 앵커, 정성은 큐레이션+LLM): config 로 박는다.
- **파이프라인=무한 학습/확장**: consensus(S9) + promotion_gate(S3) 가 seed 를 조정·승격·신규 가지치기. config append-only.
- seed=상수(YAML τ), 싼지/비싼지 판정=cheapness_z(L1)+rule(soft). LLM 은 변수·방향·키워드만(임계 τ 는 데이터 적합, R4 anchoring).

## 담당 분담 (사용자: 만든이 vs 통합자)
- **나(통합 맥락)** 직접: seed_builder·sector_rules YAML·D4 Book·as_of wire(T1 set_as_of_resolver)·archetype 정합화.
- **btn-button(T2 만든이)** 위임: T2-7 실데이터 재검증(T1 패널 도착 후), pit_regime 비모수(D1) v2.
- **btn-Inv(T1 만든이)** 위임: sector_multiples 라이브 fetch(go-live), 패널 실데이터 빌드.
