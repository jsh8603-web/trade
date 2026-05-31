# plan — eq_kr Phase 4-7 실행 (2026-05-30)

> 인계: [handoff-eq-kr-phase3-20260530.md](./handoff-eq-kr-phase3-20260530.md)
> 입력: [direction.md](./direction.md) ①②③ + [methodology-brief.md](./methodology-brief.md) Q1-Q15 + [evaluation-axes.md](./evaluation-axes.md) AUDIT-GUIDE 12축 application + [frame.md](./frame.md) v1 (v2 갱신 의무)

## Phase 4 (현 단계) — frame v2 + plan 박제
- [ ] frame.md v1 → v2 갱신
  - §1 universe: 12 산업 Tier 분류 표 (T1 반도체 단독·T2 3·T3 8)
  - §3 Layer 2: 외국인 flow base 0.18 → 0.20+ (5게이트 통과 시), 신지표 4 후보 (breadth/MSCI cap/ETF leverage/flow regime) 추가
  - §6 8축 → 12축 (AUDIT-GUIDE.md 인용)
  - §M3 regime: 12 cell → 36 cell (Macro 4 × KRW 3 × 외국인 flow 3), N gate 강화
  - §M4 5게이트 #5 OOS: skfolio CombinatorialPurgedKFoldSplit 매핑
  - §M (신규): toraniko factor model baseline 명시
- [x] plan.md 박제 (본 파일)

## Phase 5 — 산업 12 subagent Tier 차등 dispatch

### Dispatch table (frame.md v2 정독 의무)

| Tier | 산업 | 토큰 (opus 1m) | sub-cluster |
|---|---|---|---|
| **T1** | 반도체 | 500k | 메모리·파운드리·장비 3 sub (옵션 분리) |
| **T2** | 자동차 | 300k | 완성차·부품·타이어 |
| **T2** | 금융 | 300k | 은행·보험·증권·카드 + ★밸류업 Index event study |
| **T2** | 2차전지 | 300k | 셀·양극재·소재 |
| **T3** | AI tech | 150-200k | 플랫폼·SaaS |
| **T3** | 화학 | 150-200k | NCC·전문화학 |
| **T3** | 정유 | 150-200k | 정제·화학·해운 |
| **T3** | 조선 | 150-200k | 컨테이너·LNG·해양 |
| **T3** | 바이오 | 150-200k | 합성신약·바이오시밀러·CMO·백신·임상단계 별 |
| **T3** | 통신 | 150-200k | 통신·미디어 |
| **T3** | 철강 | 150-200k | 철강·비철 |
| **T3** | 소비재 | 150-200k | 식음료·내수·생활 |

총 약 3.4M 토큰 (T1 500k + T2 900k + T3 1.6M + T1 sub-cluster 옵션 400k).

### Dispatch prompt 양식 (각 subagent)
- frame.md v2 정독 의무 (SSOT)
- universe = KrxSectorProvider PIT 동적 (§1 매핑 + Tier 명시)
- 산출 = industries/{industry}/ 8 파일 (frame §5)
- 5게이트 (frame §M4) + 12축 (★AUDIT-GUIDE.md §1 SSOT primary + evaluation-axes v2 application)
- ⛔ **5 금지 inline 박제 (★v2.1 사용자 framing 의무, 2026-05-30 14:20 정정)**:
  1. 점추정 prior 박제 금지 (IC → base_weight 직접 X, 분포 + CI + 5게이트 필수)
  2. 합성·시뮬 데이터 금지 (실제 DART/KRX/FRED/FxStore PIT + 외부 무료 소스만, kurtosis·이벤트 부재 = 합성 의심)
  3. 자문 그대로 코드화 금지 (gemini/claude 답 → yaml 직접 X, 본 분석가 비판·환각 cross-verify 후 채택)
  4. Single-source 단정 금지 (학술 + 실무 + 1차 데이터 3중 cross-verify 의무)
  5. Small-N 단정 금지 (cell N<24 "유의" 주장 X, 5게이트 §M4 N gate + cell collapse fallback 우선)
- ⛔ **analyst lens 다운그레이드 금지** — 시스템·factor model 못 받으면 fallback (raw + neutralized 둘 다) 또는 supervisor 에 업그레이드 요청 (lens 깎으면 Phase 6 평가 FAIL)
- 막힘 = WebSearch/WebFetch 폴백 (9 작업방 동시 자문 경합 자제) → final message 로 12축 PARTIAL/FAIL + **Hard-fail 4 (B·C·D·I) 우선** 보고
- run_in_background = true (12 동시 dispatch)

## Phase 6 — 평가 subagent (별 opus 1m, ★본 작업방 직접 평가 ★금지★)

### Dispatch prompt
- SSOT 정독: AUDIT-GUIDE.md (12축 primary) + evaluation-axes.md (application)
- 평가 대상: industries/{각 산업}/ 8 파일 × 12 산업
- §0 Provenance + Recomputation = raw .py 직접 재실행 (또는 정독 추적) 으로 검증
- 합성 지문 (kurtosis·이벤트 실재·주말 공백) 검사
- 12축 PASS/PARTIAL/FAIL + Hard-fail 코어 4 (B·C·D·I) 우선
- tier (validated alpha vs structural prior)
- 시스템 정합 (§4) — 다운그레이드 금지, 업그레이드 계획
- 산출 = evaluation-axes.md §4 양식 yaml + AUDIT-GUIDE §5 보고

### 재dispatch 규칙
- PARTIAL/FAIL 산업 → 해당 산업 subagent 재dispatch (frame 부분 보강 가능)
- 최대 2회 재dispatch. 3회 시 사용자 보고 + 자문 추가.

## Phase 7 — 통합 + main 승인 게이트

- [ ] eq_kr 통합 study_session.yaml (frame §3 7블록)
  - lens (정성, 4 핵심 — Korea discount composition · 반도체 dominance · 외국인 flow · KOSPI/KOSDAQ 분절)
  - indicators (산업 subagent indicators_passed 합산, 직교화)
  - relationships (partial-corr prior, conditioning_set, 12 산업 통합)
  - weight_rules (Tier 차등, modulate_by regime/industry/name_specific, 점추정 박제 X)
  - confidence_hooks (라이브 진화 경로, affects_indicator/affects_edge 명시)
  - collector_plan (D1-D12 통합)
  - code_change_plan (kr_stock sleeve 기존재 + archetype 확장 + lens 주입)
- [ ] direction.md final + 12 산업 summary.yaml 합산
- [ ] 8축 통합 self-audit (eq_kr supervisor)
- [ ] main 보고 + 승인 게이트 (★승인 전 register 진입 금지)

## 진행 일정 가이드

- Phase 4: 본 작업방 1 응답 (frame v2 + plan 박제 완료)
- Phase 5: 12 subagent 병렬 dispatch (run_in_background) — 각 5-15분, 동시 종료 약 30분
- Phase 6: 평가 subagent 1 dispatch — 약 10-20분
- Phase 7: 통합 + 보고 — 본 작업방 1-2 응답

총 예상: 본 작업방 5-7 응답 + subagent 13 (12 산업 + 평가 1) opus 1m.
