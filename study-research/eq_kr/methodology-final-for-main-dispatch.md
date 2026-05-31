# methodology-final — eq_kr v2 절차 7+α Phase 정리본 (★v3 2026-05-31, 다른 자산군 dispatch baseline)

> 사용자 지시 (2026-05-30 B4): main 이 본 작업방 방법론을 다른 idle 세션 (eq_us 등) 에 적용 가능하도록 정리.
> ★v3 갱신 (2026-05-31): methodology audit 회수 + frame v2.1 정정 9항목 + Phase 6 평가 dispatch prompt 양식 + Phase 7 통합 spec + 산업 dispatch prompt 양식 + 사용자 framing 13건 추가.
> 사용자 원본 prompt = `raw/original-user-prompts-from-main.md`.

## §0 SSOT 우선순위

1. `D:/projects/Inv/CLAUDE.md` §"멀티에셋 스터디 워크플로"
2. `D:/projects/Inv/STUDY-ORCHESTRATION.md` — 5-Phase
3. `D:/projects/Inv/STUDY-KIT.md` — 작업방 작업 계약 (§2 v2 3흐름, §2.5 8축, §3 yaml 7블록)
4. `D:/projects/Inv/study-research/AUDIT-GUIDE.md` — ★12축 평가 SSOT (산업 subagent self-audit + Phase 6 평가 subagent 공통 SSOT)
5. 작업방 내부 SSOT (eq_kr: frame.md v2.1 정정 후 + evaluation-axes.md v2 + audit/methodology-audit-202605301410.md)

## §1 v2 절차 7+α Phase

### Phase 0 — 정리 (v1 폐기 시)
- 직전 v1 산출 → `raw/v1-superseded/` 보존
- progress.md 박제 (v2 절차 명시)
- main psmux 보고 (v2 진입 통지)

### Phase 1 — evaluation-axes.md (★supervisor 직접 평가 금지 박제)
- AUDIT-GUIDE.md 12축 (8 핵심 + 4 신규) **그대로 인용** + 자산군 단위 application layer
- ★ Hard-fail 4 = B(실데이터) C(추적성) D(PIT) I(생존편향) 명시
- §0 Provenance + Recomputation 의무
- 평가 subagent dispatch prompt 양식 포함 (§7 참조)

### Phase 2 — methodology-brief.md (자문 input 4-section)
- §A 산업/sub-cluster 분할 + 자문 질문 (Q1-Q6)
- §B Layer 3 자산군 cycle 지표 후보
- §C 최종 구현 결과
- §D Inv 인프라 + collector_plan
- §E R1/R2/R3 자문 계획
- §F 자문 출력 의무 (⛔ 자문 그대로 박제 금지)

### Phase 3 — 자문 R1+R2+R3 수렴
- /gemini-web (참신) + /claude-web (fresh Opus) 다회
- 9 작업방 동시 자문 채널 경합 자제 — **1자문씩**
- 경합 시 WebSearch/WebFetch 폴백
- 각 라운드 = `raw/consult-round-{N}.md` 누적 + 3계층 적재 (archive raw + memory + MEMORY 인덱스)
- 수렴 판정: 두 채널 일치 + 새 의문 무 + 사용자 충분

### Phase 3.5 — direction.md (STUDY-KIT §2-1)
- ①이론 수집 방향 (자산군 본질, hedge 어휘 + coverage·n inline 의무)
- ②이론 검증 방향 (AUDIT-GUIDE 12축 + frame §M4 5게이트 + skfolio CPCV + Tier 차등 + regime cell)
- ③핵심 가설 N (반증조건 포함)

### Phase 4 — plan.md (Phase 5-7 작업 계약)
- Phase 5 산업/sub-cluster N subagent Tier 차등 dispatch table (토큰 명시)
- Phase 6 평가 subagent dispatch prompt
- Phase 7 통합 + main 승인 게이트
- 진행 일정 가이드

### ★Phase 4.5 — methodology audit (★v3 신규, eq_kr 경험 박제)

> 사용자 명시 "완료된 내용 감사도 돌려야지" (2026-05-30) — supervisor 직접 평가 금지 박제 따라 별 opus 1m audit subagent dispatch 의무.

- 입력: frame + plan + direction + evaluation-axes + methodology-brief + methodology-final + handoff + progress + raw round 4건 + AUDIT-GUIDE + STUDY-KIT + STUDY-ORCHESTRATION + small-n-statistical-rigor + empirical-claim-presentation
- 감사 8 axis: (1) 12축 application 정확성 (2) 5 금지 박제 (3) supervisor 직접 평가 금지 (4) lens 다운그레이드 금지 (5) Inv frame 정합 (6) 자문 cross-verify (학술+실무+1차 3중) (7) small-N rigor (8) empirical-claim 5 의무
- 산출: `audit/methodology-audit-YYYYMMDDHHMM.md` (★신규 디렉토리)
- 결과 = 종합 PASS/PARTIAL/FAIL + Hard-fail 4 + 개선 권고 top 3-5
- ★ frame §6 12축이 AUDIT-GUIDE 와 1:1 매핑 검증 의무 (eq_kr Axis 1 FAIL 사례: J/K/L 명칭·내용 drift = 산업 subagent self-audit 오염)
- 정정 후 frame 버전 → v2.1 / v2.2 ...

### Phase 5 — 산업 N subagent Tier 차등 dispatch (opus 1m, run_in_background)

- frame v2.1 (정정 후) 정독 의무
- universe = 동적 PIT
- Tier 차등 토큰 (T1 단독 500k / T2 중간 300k / T3 경량 150-200k)
- 산출 = `industries/{name}/` 8 파일 (round-1 + round-N + theory-notes + validation-{fundamental, macro, industry} + summary.yaml + ★`12axis-audit.md` (v2.1, 기존 8axis-audit 대체))
- ★ 5 금지 inline 박제 (audit 권고 #2): dispatch prompt 5 금지 5줄 + 다운그레이드 금지 + Hard-fail 4 우선 보고 (§10 양식)
- 막힘 = WebSearch/WebFetch 폴백 → final message supervisor 보고 (5-10줄, ctx inject 회피)

### Phase 6 — ★별 평가 subagent (★supervisor 직접 평가 금지)

- SSOT 정독: AUDIT-GUIDE.md (12축 primary) + evaluation-axes.md (application) + frame v2.1 §6 (정정 후)
- §0 Provenance + Recomputation = raw .py 재실행
- 합성 지문 검사 (kurtosis · 이벤트 실재 · 주말 공백)
- 12축 PASS/PARTIAL/FAIL + Hard-fail 4 (B·C·D·I) 우선
- tier (validated alpha vs structural prior)
- 시스템 정합 (§4) — 다운그레이드 금지, 업그레이드 계획
- ★ methodology-audit 결과 cross-reference (산업 subagent 12axis-audit J/K/L 항목이 frame §6 v2.0 기반이면 오해석, frame v2.1 재평가 의무)
- PARTIAL/FAIL 산업 → 해당 산업 subagent 재dispatch (최대 2회)
- 산출 = evaluation-axes §5 yaml 형식 보고
- dispatch prompt 양식 = §7 참조

### Phase 7 — 통합 study_session.yaml + main 승인 게이트

- 7블록 spec = §8 참조
- 산업 summary.yaml 합산 → 직교화 → L축 공통인자 1회 계상 + PSD eigh-floor 차단 (AUDIT-GUIDE L 통합 차단)
- direction.md final + N 산업 summary.yaml 합산
- 8축 통합 self-audit (supervisor)
- ★ memory 적재 N건 (`~/.claude/memory/research/{study_id}-industry-{name}.md`) + MEMORY.md 인덱스 (사용자 명시 "이후 스터디 활용")
- main 보고 + 승인 게이트 (★승인 전 register 진입 금지)

## §2 ★ 5 금지 (사용자 박제, 모든 자산군 공통)

1. **점추정 prior 박제 금지** — IC 점추정 → base_weight 직접 X. 분포 + CI + 5게이트.
2. **합성·시뮬 데이터 금지** — random walk / 합성 panel / 가상 ticker. 실 수집기 PIT 만.
3. **자문 그대로 코드화 금지** — gemini/claude 답 → yaml 직접 X. supervisor 비판·환각 cross-verify 후 채택.
4. **Single-source 단정 금지** — 1 출처 "확정" X. 학술 + 실무 + 1차 데이터 3중.
5. **Small-N 단정 금지** — cell N<24 "유의" 주장 X. 5게이트 §N gate 우선.

## §3 ★ 추가 박제 13건 (사용자 + Inv frame)

1. ⛔ supervisor 직접 평가 금지 — 평가 subagent (별 opus 1m) 위임 의무
2. ⛔ analyst-level lens 다운그레이드 금지 — 시스템 못 받으면 파이프라인 업그레이드
3. ⛔ opt-in off = byte-identical 무회귀 — INV_R15_WEIGHTS default-off
4. ⛔ reflexive loop 차단 — belief→_macro 차단, L축 공통인자 1회 계상 + PSD
5. ⛔ tier 정직성 — 검증 통과 ≠ validated alpha. structural prior(저신뢰) 라벨 분리
6. ⛔ 통신 main psmux send 만 (btn-Codlearn 향한, 사용자 명시 2026-05-30)
7. ⛔ 점추정 prior 박제 금지 (§2 #1)
8. ⛔ 합성 데이터 금지 (§2 #2)
9. ⛔ 자문 그대로 코드화 금지 (§2 #3)
10. ⛔ Single-source 단정 금지 (§2 #4)
11. ⛔ Small-N 단정 금지 (§2 #5)
12. ★ 핵심 산업군 다 커버 — 사용자 명시 2026-05-30 (eq_kr = 12 산업 Tier 차등)
13. ★ industries/{name}/ 영구 보존 — raw 일부 + 요약 둘 다 박제, 이후 스터디 활용 의도 (사용자 명시)

## §4 ★ eq_kr 산출 파일 reference (다른 자산군 baseline)

| 파일 | 역할 |
|---|---|
| progress.md | Phase 0-7+α 절차 + ckpt + Working Notes |
| frame.md v2.1 | 산업 subagent 작업 계약 (12축 정합 정정 후, ★v2.1 = audit 회수 후) |
| methodology-brief.md | Phase 2 자문 input (4-section + Q1-Q15) |
| evaluation-axes.md v2 | Phase 6 평가 SSOT (AUDIT-GUIDE 12축 application) |
| direction.md | Phase 3.5 ①②③ (12 가설) |
| plan.md | Phase 4-7 작업 계약 + dispatch table |
| ★ audit/methodology-audit-202605301410.md | Phase 4.5 methodology audit (PARTIAL, Axis 1 FAIL = frame §6 J/K/L AUDIT-GUIDE 불일치, 개선 권고 top 5) |
| handoff-eq-kr-phase3-20260530.md | 1차 인계 (Phase 3 R2 직후) |
| handoff-eq-kr-compact2-20260530.md | 2차 인계 (2차 compact 직전) |
| ★ handoff-eq-kr-system-stall-20260530.md | 3차 인계 (Anthropic 서버 stall 발견, 재개 SSOT) |
| raw/round-1.md, round-2.md | Phase 0 자문 (R0) |
| raw/consult-round-1.md, consult-round-2.md | Phase 3 자문 (v2) |
| raw/krx-infra-checklist.md, lens-and-weight-rationale.md | R0 분석 |
| raw/v1-superseded/ | v1 폐기 보존 |
| raw/original-user-prompts-from-main.md | 사용자 원본 prompt 시퀀스 |
| industries/{name}/ × N | 산업 subagent 산출 (8 파일 × N, ★eq_kr = 12 산업 Tier 차등) |

## §5 ★ 자산군별 dispatch 우선순위 (Inv §1 매핑 + v2 재실행)

| study_id | v1 yaml | v2 우선순위 | 사유 |
|---|---|---|---|
| eq_us_defensive | ✅ (★합성 의심) | **P0** | Hard-fail B 위반 가능성 |
| reit | ✅ (v2 미산출) | **P0** | v2 직접 진입 |
| crypto | ✗ 미산출 | **P0** | v2 직접 진입 |
| bond_cash | ✗ (v1만) | **P0** | v2 직접 진입 |
| eq_kr | ✗ (v1 폐기) | **★대기 (system stall, 3차 handoff 재개 의무)** | 본 작업방 |
| eq_us_cyclical | ✅ | P1 | structural prior 재라벨 |
| eq_intl | ✅ | P1 | em_china archetype 분리 확장 |
| commodity | ✅ | P2 | structural prior 명시 |
| gold | ✅ | P2 | VECM 업그레이드 계획 추가 |
| macro | ✅ | P2 | belief→_macro 차단 점검 |
| **eq_us (신규)** | ✗ | **P0** | 사용자 추가 지시 (B2), GICS 11 sector 적용 |

## §6 ★ main 의 dispatch action (사용자 B4 baseline 응용)

1. **7 SSOT 묶음 전달** (★v3 갱신):
   - 본 methodology-final-for-main-dispatch.md (v3)
   - frame.md (v2.1 정정 후, eq_kr 사례)
   - evaluation-axes.md (application layer 양식)
   - STUDY-KIT.md
   - STUDY-ORCHESTRATION.md
   - AUDIT-GUIDE.md (★12축 primary SSOT)
   - ★ audit/methodology-audit-*.md (eq_kr 사례 = Axis 1 FAIL 정정 권고)
2. **사용자 원본 prompt** (`raw/original-user-prompts-from-main.md` §A1+A3+A4+B1+B2+B3+B4) = dispatch prompt 템플릿
3. **대상 idle 세션** = Inv §1 매핑 표 미산출/재실행 작업방 (eq_us / crypto / bond_cash / reit / eq_us_defensive 등)
4. dispatch 시 study_id + universe + 자산군 특화 Layer 3 지표만 교체
5. ★ **사용자 framing 박제 13건 의무** (§3)

## §7 ★ Phase 6 평가 subagent dispatch prompt 양식 (★v3 신규)

```
[supervisor → Phase 6 평가 subagent]

너는 {study_id} 작업방 산업 N subagent 산출물 (industries/{각 산업}/ 8 파일) 을 **독립 평가** 하는 별 opus 1m subagent. supervisor 와 분리. supervisor 의 self-audit 신뢰 X.

## SSOT 정독 (Read 의무)
1. D:/projects/Inv/study-research/AUDIT-GUIDE.md (★12축 primary, 신규 4축 I/J/K/L 정확 정의 기준)
2. D:/projects/Inv/study-research/{study_id}/evaluation-axes.md (application layer)
3. D:/projects/Inv/study-research/{study_id}/frame.md v2.1 (정정 후 SSOT, §6 12축 AUDIT-GUIDE 정합)
4. D:/projects/Inv/study-research/{study_id}/audit/methodology-audit-*.md (방법론 audit 결과, frame §6 J/K/L cross-reference 의무)
5. D:/projects/Inv/STUDY-KIT.md §6 (주식 통일 하드룰, 해당 시)

## 평가 대상
industries/{각 산업}/ 8 파일 × N (round-1 / round-N / theory-notes / validation-fundamental / validation-macro / validation-industry / summary.yaml / 12axis-audit.md)

## 평가 절차 (§0 Provenance + Recomputation)
1. raw .py 재실행 (또는 정독 추적) 으로 yaml 숫자 = raw 재계산 일치 검증
2. 합성 지문 검사 (kurtosis · 이벤트 실재 · 주말 공백 · 알려진 역사 이벤트 부재)
3. 12축 PASS/PARTIAL/FAIL 판정 (Hard-fail 4 = B·C·D·I 우선)
4. tier 분류 (validated alpha vs structural prior 저신뢰)
5. 시스템 정합 (§4 AUDIT-GUIDE) — 다운그레이드 금지, 업그레이드 계획
6. ★ 산업 subagent 12axis-audit.md J/K/L 항목 = AUDIT-GUIDE J/K/L 정확 정의 (거래비용·다중검정·통합PSD) 기준 재평가 (산업 subagent 가 frame §6 v2.0 기반이면 오해석 가능)

## 산출 = evaluation-axes §5 yaml 형식
```yaml
industry: str
12axis_results:
  A: PASS|PARTIAL|FAIL (근거 1줄)
  # ... B~L
hard_fail_4:
  B: pass|fail
  C: pass|fail
  D: pass|fail
  I: pass|fail
tier: validated_alpha | structural_prior_low
system_fit:
  current_pipeline_fits: bool
  upgrade_plan: str | null
verdict: register_ok | partial | insufficient
re_dispatch_required: bool
re_dispatch_reason: str | null
```

## 재dispatch 규칙
- PARTIAL/FAIL 산업 → 해당 산업 subagent 재dispatch (frame 부분 보강 가능, 최대 2회)
- 3회 시 사용자 보고 + 자문 추가

## ★ final message (supervisor 회수, 5-10줄, ctx inject 회피)
- 종합 verdict (모든 산업 register_ok / partial 산업 N / insufficient 산업 N)
- Hard-fail 4 (B·C·D·I) FAIL 산업 식별
- 재dispatch 필요 산업 list
- 시스템 업그레이드 권고 (있으면)
- 평가 파일 경로

본문은 evaluation-results-YYYYMMDD.md 박제. final message 본문 인용 금지.

자율 진행, idle 금지.
```

## §8 ★ Phase 7 통합 study_session.yaml 7블록 spec (★v3 신규)

```yaml
study_id: str
asset_scope: [equity.{geo}, ...]
as_of: "YYYY-MM-DD"

# 블록 1: lens (정성, 자산군 본질 N 핵심)
lens:
  pricing_principle: str
  cycle_reading: str
  estimation_note: str  # 현 시점 cycle 위치 추정, data 근거 명시

# 블록 2: indicators (산업/sub-cluster indicators_passed 합산, 직교화)
indicators:
  - id: str
    layer: 1|2|3
    family: enum
    ic_mean: float
    ic_ci_95: [float, float]  # 0 비포함
    n_effective: int
    oos_ratio: float
    cell_breakdown: [...]
    source_id: str  # validation-*.md cell ID
    factor_neutralized: bool  # toraniko 또는 fallback 적용

# 블록 3: relationships (partial-corr prior + conditioning_set)
relationships:
  - node_a: ref
    node_b: ref
    lag_months: int
    corr: float
    corr_ci_95: [float, float]
    conditioning_set: [ref]
    n: int
    autocorr_safe: bool  # Newey-West / Block Bootstrap 적용
    source_id: str

# 블록 4: weight_rules (Tier 차등, 점추정 prior X)
weight_rules:
  - indicator_id: ref
    base_weight_range: [float, float]  # IC mean ± SE 비례
    modulate_by: [regime, industry, name_specific, cycle_phase]
    direction: str
    granularity: enum
    confidence: high|medium|low
    gate_status: {n: pass, se: pass, power: pass, fdr: pass, oos: pass}
    cost_adjusted_alpha: float  # 거래비용 차감 후 (AUDIT-GUIDE J)
    source_ids: [str, ...]

# 블록 5: confidence_hooks (라이브 진화 경로)
confidence_hooks:
  - hypothesis_id: str
    confirm_signal: str
    reject_signal: str
    accumulate_in: str  # core/assume/weight_falsification.*
    feeds_weight: str   # 갱신 경로
    affects_indicator: str | null  # flag → weight 매핑
    affects_edge: [node_a, node_b] | null  # flag → corr_prior 매핑

# 블록 6: collector_plan (D1-DN 부족 자료 통합)
collector_plan:
  - missing: str
    source: str
    priority: enum

# 블록 7: code_change_plan (sleeve 확장 + lens 주입)
code_change_plan:
  - module: str  # core/brain/regime_to_weights.py 등
    change: str
    backward_compat: bool  # INV_R15_WEIGHTS default-off
    self_test: str

# 통합 단계 검증 (AUDIT-GUIDE L 통합 정합성)
integration_audit:
  cross_sleeve_common_factors: [USDKRW, foreign_flow, HY_OAS, ...]
  common_factor_counted_once: bool  # L 위반 = 통합 차단
  psd_eigh_floor_passed: bool
  newey_west_se_applied: bool
```

## §9 ★ audit 회수 후 정정 절차 (★v3 신규, eq_kr 경험 박제)

eq_kr methodology audit (2026-05-30 14:10-14:20) = 종합 PARTIAL + Axis 1 FAIL (frame §6 J/K/L AUDIT-GUIDE 명칭·내용 불일치). 정정 9건:

| # | 정정 항목 | 위치 | 효과 |
|---|---|---|---|
| 1 | frame §6 12축 v2.1 (I 확장 + J 거래비용 + K 다중검정 + L cross-sleeve PSD) | frame.md §6 | 산업 subagent self-audit J/K/L 정확 정의 |
| 2 | frame §3 Layer 2 외국인 flow "★0.20+ 잠정" hedge | frame.md §3 | small-n rigor 단정 어휘 회피 |
| 3 | frame §9 다운그레이드 금지 박제 | frame.md §9 | analyst lens 다운그레이드 사전 차단 |
| 4 | plan §Phase 5 dispatch prompt 5 금지 inline | plan.md §Phase 5 | subagent frame 정독 skip 시 안전망 |
| 5 | progress §Phase 6 다운그레이드 금지 + AUDIT-GUIDE primary input | progress.md §Phase 6 | Phase 6 평가 추가 검증 |
| 6 | progress timeline audit 회수 박제 | progress.md timeline | 인계 SSOT |
| 7 | progress ckpt-202605301420 | progress.md Working Notes | 다음 세션 인계 |
| 8 | direction §① "외국인 driver 1순위" → "방향성 강 prior 잠정" hedge | direction.md §① | empirical-claim §1.1 의무 |
| 9 | direction §① e-KJFS coverage·n inline 박제 | direction.md §① | empirical-claim §1.1-1.2 의무 |

★ 다른 자산군 적용 시 9항목 checklist 그대로 적용 + 자산군 특화 추가 발견 시 보강.

## §10 ★ 산업 dispatch prompt 양식 (★v3 신규, frame v2.1 정정 후)

```
[supervisor → {industry} subagent]

너는 {study_id} 산업 sub-study 의 **{industry}** 산업 담당 전문 애널리스트. opus 1m, 토큰 budget {N}k. Tier {T}.

## SSOT 정독 (Read 의무)
1. D:/projects/Inv/study-research/{study_id}/frame.md (★v2.1, 정정 후 SSOT, §6 12축 AUDIT-GUIDE 정합)
2. D:/projects/Inv/STUDY-KIT.md §6 (주식 통일 하드룰, 해당 시)
3. D:/projects/Inv/study-research/AUDIT-GUIDE.md (Hard-fail 4 = B·C·D·I, 신규 4축 I/J/K/L 정확 정의)

## Tier {T} — {industry}
- universe: {dynamic PIT provider} 대표 = {ticker list}
- sub-cluster 메모: {sub-cluster}
- Layer 3 cycle 지표 후보: frame §3 Layer 3 {industry} 참조

## 산출 (industries/{industry_path}/ 디렉토리, 8 파일 frame §5)
1. round-1.md — 가설 5-10 + 반증조건
2. round-N.md — 추가 라운드 (필요시)
3. theory-notes.md — 산업 cycle 이론 + source URL 의무
4. validation-fundamental.md — Layer 1 raw IC + factor-neutralized IC + M3 36 cell + 5게이트
5. validation-macro.md — Layer 2 기본 + 신지표 후보 + 5게이트
6. validation-industry.md — Layer 3 5게이트
7. summary.yaml — frame §7 양식 (점추정 prior X)
8. 12axis-audit.md — A~L 12축 PASS/PARTIAL/FAIL (Hard-fail 4 = B·C·D·I 우선)

## ⛔ 5 금지 inline (★v2.1 정정 후 dispatch prompt 의무 박제, audit 권고 #2)
1. 점추정 prior 박제 금지 (IC → base_weight 직접 X, 분포 + CI + 5게이트 필수)
2. 합성·시뮬 데이터 금지 (실 PIT 수집기 + 외부 무료 소스만, kurtosis·이벤트 부재 = 합성 의심)
3. 자문 그대로 코드화 금지 (gemini/claude 답 → yaml 직접 X, 분석가 비판·환각 cross-verify 후 채택)
4. Single-source 단정 금지 (학술 + 실무 + 1차 데이터 3중 cross-verify 의무)
5. Small-N 단정 금지 (cell N<24 "유의" X, 5게이트 §M4 N gate + cell collapse fallback 우선)

## ⛔ analyst lens 다운그레이드 금지
시스템·factor model 못 받으면 fallback (raw + neutralized 둘 다) 또는 supervisor 에 업그레이드 요청 (lens 깎으면 Phase 6 평가 FAIL).

## 막힘 처리 + final message
막힘 = WebSearch/WebFetch 폴백 (1-2R) → final message supervisor 보고.
toraniko 막힘 = pandas/numpy fallback (★raw + neutralized IC 둘 다 의무).
5게이트 부족 = "탐색적 / 시사적" finding 격하.

★ final message (5-10줄, ctx inject 회피)
- 12축 PASS/PARTIAL/FAIL (★Hard-fail 4 = B·C·D·I 우선)
- 핵심 finding 2-3 (5게이트 통과 indicator + IC + CI + N + regime)
- 막힘 1-2
- 8 파일 산출 경로

본문은 industries/{industry_path}/ 박제. final message 본문 인용 금지. 자율 진행, idle 금지.
```

---

> ★v3 갱신 history:
> - 2026-05-30 (v2): eq_kr Phase 4 직후, 사용자 B4 baseline 응용
> - 2026-05-31 (v3): Phase 4.5 methodology audit + frame v2.1 정정 9항목 + Phase 6 평가 dispatch prompt 양식 + Phase 7 통합 yaml 7블록 spec + 산업 dispatch prompt 양식 + 사용자 framing 박제 13건 + 3차 handoff 박제
