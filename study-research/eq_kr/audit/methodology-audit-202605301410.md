---
tags: [type/audit, domain/inv, asset/equity-kr, phase/methodology]
date: 2026-05-30
auditor: opus-1m subagent (독립 감사, supervisor 와 분리)
audit_target: eq_kr v2 방법론·계약 산출물 (frame v2 + plan + direction + evaluation-axes + methodology-brief + methodology-final + handoff 2건 + progress + raw round 4건)
ssot_reference:
  primary: D:/projects/Inv/study-research/AUDIT-GUIDE.md   # 12축 SSOT
  application: D:/projects/Inv/study-research/eq_kr/evaluation-axes.md
  contract: D:/projects/Inv/study-research/eq_kr/frame.md  # v2 (2026-05-30)
note: Phase 5 산업 12 subagent dispatch (run_in_background ~30분 진행) 와 병렬 진행된 방법론 감사. dispatch 결과물 (industries/{name}/) 은 본 감사 대상 외 — Phase 6 별 평가 subagent 책임.
---

# methodology-audit — eq_kr v2 방법론·계약 8 axis 독립 감사 (2026-05-30 14:10)

> 본 감사 = **방법론 layer** 만 (frame v2 + 절차 산출물). 실데이터 산출 (industries/{name}/) 은 Phase 6 평가 subagent 책임.
> 본 감사관 = eq_kr supervisor 와 독립. supervisor 의 self-audit (frame §6, consult-round-{1,2} self-check) 는 참고만, 신뢰 X.
> 본 감사 자체 = 5 금지 준수 (자기참조 — 자문 그대로 인용 X, single-source 단정 X, 정량 prior 박제 X).

---

## §1. 8 axis 각 PASS/PARTIAL/FAIL 판정

### Axis 1 — AUDIT-GUIDE 12축 application 정확성 → **FAIL**

**근거**: frame.md §6 (`12axis-audit`) 의 신규 4축 (I/J/K/L) **이름·내용이 AUDIT-GUIDE §1 신규 4축과 불일치**. evaluation-axes.md §2 는 정확하지만, frame.md §6 가 산업 subagent 가 따를 SSOT 라서 axis 명칭 drift = 산업 subagent self-audit 단계 오염.

| 축 | AUDIT-GUIDE.md (SSOT) | frame.md §6 (audit target) | 매칭? |
|---|---|---|---|
| I | "데이터 무결성·생존편향" (상폐·티커변경·split·PIT universe) | "생존편향 차단" (krx_universe.delisted 포함) | ⚠️ frame 좁힘 — split·티커변경 누락 |
| **J** | **"경제적 유의성·거래비용·capacity"** (왕복 0.3% 차감 alpha) | **"factor neutralization"** (toraniko raw+neutralized IC) | ❌ **완전 불일치** (frame J = AUDIT-GUIDE 어느 축도 아닌 신축) |
| **K** | **"다중검정 보정"** (Bonferroni·FDR·Deflated Sharpe) | **"regime classifier 추적성"** (regime 분류 코드 path 재실행) | ❌ **완전 불일치** (frame K = AUDIT-GUIDE 어느 축도 아닌 신축. 다중검정 보정은 frame §M4 #4 FDR gate 로만 처리) |
| **L** | **"통합 상관행렬 정합성"** (cross-sleeve PSD·공통인자 중복) | **"직교성"** (Layer 1/2/3 partial-corr ≤0.7, 다중공선성) | ❌ **개념 불일치** (frame L = within-industry 직교성, AUDIT-GUIDE L = 통합 시 cross-sleeve PSD) |

**영향**:
1. **거래비용·capacity** (AUDIT-GUIDE J, 조건부 hard) — frame §6 에서 누락. industry subagent self-audit 12axis-audit.md 에서 거래비용 0.3% 차감 후 alpha 검증 강제 메커니즘 부재 → REJECT 조건 누락 위험. (※ direction.md §② "거래비용 한국 매도세 0.18-0.23% + 슬리피지 (왕복 0.3%+) 차감 후 alpha" 박제 있지만, frame §6 axis 누락이라 subagent self-audit 에서 빠질 수 있음.)
2. **다중검정 보정** (AUDIT-GUIDE K, hard) — frame §6 K 가 "regime classifier 추적성" 으로 잘못 박제. 시도횟수 공시·Haircut Sharpe 등 다중검정 보정 의무가 frame §6 self-audit 에 없음. (frame §M4 #4 FDR gate q<0.10 만 존재 — Deflated Sharpe·시도횟수 공시·BH vs Bonferroni 명시 누락.)
3. **통합 PSD** (AUDIT-GUIDE L, 조건부 hard) — frame §6 L 이 within-industry 직교성으로 잘못 박제. Phase 7 eq_kr supervisor 통합 단계 (산업 summary.yaml 합산) 에서 공통인자 (USDKRW·외국인 flow·HY OAS) 중복 계상 + PSD eigh-floor 차단 메커니즘 누락 위험.

evaluation-axes.md §2 (J/K/L 정확) 와 frame.md §6 (J/K/L 잘못) 사이 **이중 SSOT 충돌**. Phase 6 평가 subagent 가 AUDIT-GUIDE primary + evaluation-axes application 으로 평가하는 한 통합 단계는 보호되나, **산업 subagent 의 12axis-audit.md 자가감사는 frame §6 따라 J/K/L 오해석 박제 가능성 높음**.

**판정 근거**: AUDIT-GUIDE.md §1 신규 4축 표 vs frame.md §6 신규 4축 표 1:1 비교. 4축 중 3축 (J·K·L) 불일치 → **FAIL**.

---

### Axis 2 — 5 금지 박제 검증 → **PARTIAL**

**5 금지 박제 격자** (모든 산출물 cross-check):

| 산출물 | 점추정 prior | 합성 데이터 | 자문 그대로 | single-source | small-N |
|---|---|---|---|---|---|
| frame.md §0+§8 | ✅ (§0 #2 + §8 #1) | ✅ (§0 #3 + §8 #2) | ✅ (§0 #1 + §8 #3) | ✅ (§0 #4 + §8 #4) | ✅ (§0 #5 + §8 #5) |
| plan.md | ❌ (Phase 5 dispatch table 5 금지 명시 X — "frame.md v2 정독 의무" 만, 5 금지 inline 박제 부재) | ❌ | ❌ | ❌ | ❌ |
| direction.md | ⚠️ (§② "거래비용 차감 후 alpha" 만) | ✅ (§② "krx_universe.delisted 포함") | ❌ | ❌ | ⚠️ (§② 5게이트 인용) |
| evaluation-axes.md | ✅ (§3 "hard-fail" + §0 "5 금지 미러") | ✅ (§2 B) | ✅ (§6 cite) | ✅ (§3 F) | ✅ (§3 G tier) |
| methodology-brief.md §F | ✅ (§F #2) | ✅ (§F #3) | ✅ (§F #1) | ⚠️ (§F #1 자문 그대로 박제 금지로 cover) | ⚠️ |
| methodology-final §2 | ✅ (#1) | ✅ (#2) | ✅ (#3) | ✅ (#4) | ✅ (#5) |
| handoff phase3 §8 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Phase 5 dispatch prompt 양식 (plan §Phase 5) | ❌ inline 박제 X | ❌ | ❌ | ❌ | ❌ |

**위반 N=1 (구조적)**: Phase 5 dispatch prompt 양식 (plan.md §Phase 5 "Dispatch prompt 양식") 이 5 금지 inline 박제 없이 "frame.md v2 정독 의무" 만 명시. 12 산업 subagent 가 frame.md v2 정독을 skip 하거나 부분 정독 시 5 금지 자가 적용 누락 가능. frame.md §0+§8 박제 강건성 의존도 100%.

**정정 권고**: plan.md §Phase 5 "Dispatch prompt 양식" 에 **5 금지 inline 박제 5줄 추가** (점추정 prior 박제 X / 합성 데이터 X / 자문 그대로 코드화 X / single-source 단정 X / small-N 단정 X). Phase 5 dispatch 가 이미 진행 중이라 (progress.md 14:00 항목) 회수 후 Phase 6 evaluation-axes 평가 시 5 금지 위반 검출 의무 (대안 cover 경로).

**판정 근거**: 8 산출물 중 6 산출물 박제 충분, 2 산출물 (plan + dispatch prompt) 박제 누락 → **PARTIAL**.

---

### Axis 3 — supervisor 직접 평가 금지 박제 → **PASS**

**박제 위치**:
- evaluation-axes.md §0 "⛔ 본 작업방 (eq_kr supervisor) 직접 평가 ★금지★" (§17)
- evaluation-axes.md §6 "본 작업방 (eq_kr supervisor) 직접 평가 ★금지★ (v2 지시 2026-05-30)" (§141)
- progress.md Phase 6 "★별 평가 subagent (본 작업방 직접 평가 ★금지★)" (§68)
- progress.md L10 "별 평가 subagent 가 평가 (본 작업방 직접 평가 금지)" (v2 절차 재정렬 박제)
- plan.md §Phase 6 "★본 작업방 직접 평가 ★금지★" (§45)
- frame.md §6 "★ Phase 6 평가 subagent (opus 1m, **별 작업방**) 가 본 12축으로 산업별 PASS/PARTIAL/FAIL 판정. ⛔ supervisor 직접 평가 금지" (§203)
- methodology-final §3 "★ supervisor 직접 평가 금지" (§84)
- methodology-final §1 Phase 6 "★별 평가 subagent (★supervisor 직접 평가 금지)" (§60)
- handoff-eq-kr-phase3-20260530.md §8 (§160)
- raw/original-user-prompts §C "★ supervisor 직접 평가 ★금지★" (§111)

**판정**: 10+ 박제 위치 일관 + Phase 6 별 평가 subagent dispatch prompt 양식 (evaluation-axes §5) 명시 완비 → **PASS**.

---

### Axis 4 — analyst lens 다운그레이드 금지 박제 → **PARTIAL**

**박제 위치**:
- AUDIT-GUIDE §4 "★단, 애널리스트 수준의 분석 렌즈 코드를 다운그레이드 금지" (사용자 지시 원문)
- evaluation-axes.md §4 yaml `system_fit.upgrade_plan: str # 다운그레이드 ★금지★` (§98)
- plan.md §Phase 6 "시스템 정합 (§4) — 다운그레이드 금지, 업그레이드 계획" (§54)
- methodology-final §3 "★ analyst-level lens 다운그레이드 금지 — 시스템 못 받으면 파이프라인 업그레이드" (§85)
- methodology-final §1 Phase 6 "시스템 정합 (§4) — 다운그레이드 금지, 업그레이드 계획" (§65)
- handoff §8 "⛔ analyst-level lens 다운그레이드" (§161)
- progress.md = **누락** (§ Phase 6 / Phase 7 모두 명시 없음)
- frame.md = **누락** (§9 통신·dispatch 규칙, §6 12축 어디에도 명시 없음)

**위반 영향**: frame.md 가 산업 subagent SSOT 인데, subagent 가 산업 cycle 분석 lens 가 toraniko factor model 에 안 맞아 깎는 (downgrade) 결정 시, frame §6 self-audit·§5 산출 양식·§9 dispatch 어느 부분도 차단하지 못함. 산업 subagent 회수 후 Phase 6 평가 subagent 가 evaluation-axes §4 yaml `system_fit.upgrade_plan` 으로 검출하는 경로만 의존. **사후 검출** 경로만 있고 **사전 차단** 경로 부재.

**정정 권고**: frame.md §9 통신·dispatch 규칙 끝에 "⛔ analyst-level lens 다운그레이드 금지 — 시스템·factor model 못 받으면 fallback (raw + neutralized 둘 다 보고) 또는 supervisor 에 파이프라인 업그레이드 요청" 박제 추가. progress.md Phase 6 "다운그레이드 금지, 업그레이드 계획" 1줄 추가.

**판정 근거**: 박제 7 위치 중 4 위치만 명시 (frame·progress 누락) → **PARTIAL**.

---

### Axis 5 — Inv frame 정합 v2.1 (5-Phase mirror) → **PASS**

**5-Phase mirror 표 (evaluation-axes §0 + progress.md §Inv frame 정합)**:

| Main frame (STUDY-ORCHESTRATION §2) | eq_kr supervisor micro frame |
|---|---|
| Phase A — 세션 스폰 (psmux-send 헬퍼) | Phase A' — N 산업 subagent dispatch (opus 1m, run_in_background) ✅ |
| Phase B — STUDY-KIT 3흐름 (theory / validation / 코드화) | Phase B' — frame.md §5 8 파일 (round-N / theory-notes / validation-*/summary.yaml) ✅ |
| Phase C — opus subagent AUDIT-GUIDE 12축 감사 | Phase C' — 별 평가 subagent (opus 1m) evaluation-axes 12축 application ✅ |
| Phase D — main register 게이트 (require_raw=True) | Phase D' — eq_kr supervisor 통합 study_session.yaml (Phase 7) ✅ |
| Phase E — flag·연관 (live 진화) | Phase E' — 라이브 flag → lens/corr/weight 진화 ✅ |

**일관 박제 확인**: evaluation-axes §0 (§7-17) + progress.md §"Inv frame 정합 v2.1" (§12-25) + methodology-final §1 Phase 0-7 (§16-72). 3 산출물 5-Phase mirror 박제 일관 + 차이 0.

**micro-orchestration 정확성**: STUDY-ORCHESTRATION.md §2 Phase A-E 와 eq_kr Phase 1-7 매핑 OK. 단 micro Phase 0 (직전 v1 폐기 정리) + Phase 1-3.5 (평가축·brief·자문·direction) = Main frame 의 Phase A "세션 스폰" + Phase B "STUDY-KIT" 진입 전 supervisor preparation 단계로 이해 가능. 5-Phase mirror 자체 깨짐 없음.

**판정**: 5-Phase mirror 표 + micro-orchestration 진입 sequence 정합 → **PASS**.

---

### Axis 6 — 자문 finding cross-verify → **PARTIAL**

**자문 finding × cross-verify 3채널 (학술 / 실무 / 1차 데이터) 표**:

| Finding | 학술 (DOI·논문) | 실무 (증권사·자문) | 1차 데이터 (실측) | 3채널 충족? |
|---|---|---|---|---|
| **산업 12 Tier 분할 (반도체 50%+)** | ❌ (R1 학술 = NCBI PMC11023228 GARCH-MIDAS / arxiv 2401.00001 sector rotation — 한국 50% 집중 미언급) | ✅ R1 WebSearch B (Goldman cap / BTIG reversal) | ⚠️ R1 finding "50.44% 2026-05" = 단일 시점 snapshot, KOSPI 일간 시계열 IC·CI 부재 | **PARTIAL** (학술 backing 부재, 실무 1 channel + 1 snapshot 만) |
| **외국인 flow base 0.20+ (1순위 alpha)** | ⚠️ (R1 학술 = Kim-Wei 2002 / Chae-Yang 2007 KAR — direction §② 인용, 그러나 base_weight 0.20+ 정량 magnitude 학술 backing 없음) | ✅ R1 "Roller-KOSPI 15세션 50조 매도" (BTIG 단일) | ❌ frame §M4 5게이트 통과 = Phase 5 subagent 실측 위임 (현재 미수령) | **PARTIAL** (방향성 ✅, 정량 magnitude single-source) |
| **신지표 #1 breadth_kospi** | ❌ (R2 자체 명시 "학술 baseline 부재 → tier 강등 가능성") | ⚠️ R2 "Advance-Decline 학술 정설" (산업 baseline 1차로만) | ❌ 실측 부재 | ⚠️ **자체 명시 tier 강등 = HEDGE OK** (frame §3 "structural prior tier 강등" 박제) |
| **신지표 #2 MSCI cap 초과 flag** | ❌ | ✅ R1 Goldman Sachs cap | ❌ | **PARTIAL** (event study 형식 권고 hedge) |
| **신지표 #3 ETF leverage flow** | ❌ | ⚠️ R1 KODEX cap finding (event 1건) | ❌ | **WEAK** (frame §3 "산업별 mapping 가능 시만 채택" hedge) |
| **신지표 #4 외국인 flow regime** | ❌ | ⚠️ R1 R2 모두 자체 분류 | ❌ | **WEAK** (frame §3 "★frame §M3 regime 36 cell 확장의 핵심" — 자체 정의) |
| **toraniko·skfolio OSS** | ✅ R2 GitHub repo + MIT license URL 실재 | ✅ R2 Barra/Axioma vein (정설) | ❌ Korean KOSPI 적용 사례 X | **PASS hedge** (frame §M5 "eq_kr first mover" 명시) |
| **일본 TSE 2년 후 -23pt baseline** | ⚠️ R2 "Prime PBR<1 27% (-23pt) 2026-02" — JPX·FSA 공식 (R2 §1.1) | ✅ Pzena/BNY/JPMAM (R2 §1.1) | ⚠️ 단일 시점 (2026-02 vs 2024-01 baseline = 25개월) | **PARTIAL** (multi-source 실무 ✅, 단일 시점 측정 — n=1 event) |
| **e-KJFS R&D p<0.01** | ✅ R2 §1 본문 정독 (DOI 10.26845, 표본 2000-2022 N=7443+3021) | ❌ | ✅ 학술 자체가 1차 데이터 분석 | **PASS** (학술 N 큼) |

**위반 N=4-5**: 산업 12 Tier 분할 + 외국인 flow 0.20+ + 신지표 #2/#3/#4 = R1 단일 source (Goldman/BTIG/Roller-KOSPI 같은 실무 channel) 만 + R2 cross-verify 부재 (R2 §1.2 toraniko/skfolio + §1.3 breadth 만 처리, Tier 분할·외국인 flow magnitude 의 학술 cross-verify 없음). 모두 frame v2 §1 (Tier 표) + §3 (외국인 flow base 0.20+) + §3 (신지표 4) 박제됨.

⚠️ 단 frame §3 신지표 표 "tier 위험" 컬럼에 각각 hedge 박제 ("학술 baseline 부재 → tier 강등 가능성", "event study 형식 권고", "산업별 mapping 가능 시만 채택", "frame §M3 regime 36 cell 확장의 핵심") → small-N rigor §2 "단정 어휘 금지" 준수 (다만 "★0.20+ (v1 0.18 → 상향, R1 finding: Roller-KOSPI 15세션 50조 매도 driver 1순위)" 의 "★1순위" 는 단정 어휘에 가까움).

**정정 권고**:
1. frame §3 "외국인 flow base 0.20+" 옆 (★) 박제 "★ R1 single-source (Roller-KOSPI 1 episode), 학술 cross-verify 부재 → 산업 subagent 5게이트 통과 후만 채택, 미통과 시 v1 0.18 유지". "1순위 driver" 단정 어휘 → "방향성 강 prior, 정량 magnitude 잠정 (5게이트 검증 위임)".
2. consult-round-3.md 또는 산업 subagent dispatch prompt 에 R3 학술 cross-verify 의무 추가: "외국인 flow alpha magnitude 의 한국 학술 baseline (Chae-Yang 2007 KAR / Kim-Wei 2002 정량 magnitude) 산업 subagent 가 round-N 에서 검증 의무".

**판정 근거**: 9 finding 중 2 PASS (toraniko/e-KJFS) + 4 PARTIAL (Tier / 외국인 / MSCI / 일본) + 2 WEAK (ETF leverage / 외국인 flow regime) + 1 자체 HEDGE (breadth). 학술 + 실무 + 1차 3채널 충족 finding = 1 (e-KJFS 만) → **PARTIAL**.

---

### Axis 7 — small-N statistical rigor → **PASS**

**rule §1 5게이트 (a-e) vs frame §M4 5게이트 (#1-#5) 매핑**:

| rule §1 | frame §M4 |
|---|---|
| (a) p-value 명기 | #2 SE gate (95% CI 0 비포함 = p<0.05 함의) ✅ |
| (b) ≥4 비교 시 Bonferroni / FDR | #4 FDR gate (BH q<0.10) ✅ |
| (c) 95% CI 박제 의무 | #2 SE gate (CI 박제) + frame §5 yaml `ic_ci_95: [low, high]` ✅ |
| (d) hedge 어휘 강제 | frame §M4 verdict 라벨 4단 ("확신/탐색적/시사적/N 부족") ✅ |
| (e) 점추정 covariance prior 박제 금지 | frame §0 #2 + §8 #1 점추정 prior 박제 금지 + frame §7 yaml `base_weight_range: [float, float]` (점추정 X) ✅ |

**rule §M3 36 cell N gate 점검**:
- frame §M3 36 cell (Macro 4 × KRW 3 × 외국인 flow 3) + N gate ≥24 명시.
- 월간 데이터 OOS 2023-2026 = ~36개월, IS 2015-2022 = ~96개월. 36 cell 분할 시 cell 당 평균 N = (96+36)/36 ≈ 3.7개월. **N gate 통과 거의 불가능** (cell collapse 의무 발생).
- frame §M3 cell collapse 가이드 3단계 (1단계 36 cell → 2단계 인접 merge → 3단계 외국인 flow 3 cell fallback) **명시** → 사전 차단 메커니즘 충분.

**autocorrelation 안전장치 (rule §1.4)**:
- direction.md §② "거래비용 한국 매도세 0.18-0.23% + 슬리피지 (왕복 0.3%+) 차감 후 alpha" 박제, 그러나 **Newey-West HAC SE / Block Bootstrap 명시 부재**. evaluation-axes.md §2 L 보충에 "★Newey-West / block-bootstrap SE 강제" 박제 (§55) — **PASS via evaluation-axes**.
- frame §M4 #5 OOS 게이트 skfolio CombinatorialPurgedKFoldSplit + embargo 5d (forward return overlap 차단) ✅.

**verdict 라벨 5단계 (rule §2)**:
- frame §M4 4단 verdict ("확신 finding / 탐색적 / 시사적 / N 부족") + evaluation-axes §3 tier "validated alpha / structural prior(저신뢰)". rule §2 5단 (★CONFIRMED 강력 / CONFIRMED / PARTIAL CONFIRMED / TENTATIVE DIRECTIONAL / ★INSUFFICIENT / ★REJECTED) 와 1:1 매핑 아니나 의도 동일. **PASS** (semantic equivalence).

**판정 근거**: 5게이트 (a-e) 매핑 완비 + cell collapse fallback 명시 + autocorr 보정 evaluation-axes §2 L 보충 박제 + verdict 라벨 hedge → **PASS**. (개선 권고: frame §M4 에 Newey-West HAC SE / Block Bootstrap inline 박제 추가 권고.)

---

### Axis 8 — empirical-claim-presentation 5 의무 → **PARTIAL**

**direction.md §① 정량 claim 자가 점검**:

| Claim | (1.1) coverage 일자 | (1.2) n + LOO | (1.3) spec/code match | (1.4) autocorr | (1.5) 다중 비교 | 판정 |
|---|---|---|---|---|---|---|
| "e-KJFS R&D pos p<0.01" | ⚠️ direction inline = "(e-KJFS 2025 KJFS 54-5 학술)" — 일자 OK, **표본 기간 누락** (raw/round-2.md L18 "2000-2022 N=7443+3021" 별 파일 참조 필요) | ⚠️ direction inline 누락 (round-2.md 만) | ✅ (학술 본문 정독, R&D/TA pos 1:1) | n/a (학술 panel) | ⚠️ direction inline 명시 X | **PARTIAL** |
| "일본 TSE 2년 후 PBR<1 -23pt" | ✅ direction §① "2년 후 Prime PBR<1 27% (-23pt) + 자사주 급증" — 일자 implicit 2024-01 vs 2026-02 | ❌ n 명시 없음 (단일 시점 measurement = n=1 event) | ✅ (R2 §1.1 본문 검증) | n/a | n/a | **PARTIAL** (n=1 event, hedge "disclosure 품질 mixed" 박제됨) |
| "반도체 50% 집중 (2026-05)" | ✅ "삼성+SK하이닉스 KOSPI 50.44%" — 일자 명시 | ❌ n=1 snapshot, 시계열 IC 없음 | ✅ (R1 WebSearch B 인용) | n/a | n/a | **PARTIAL** (단일 시점 snapshot) |
| "외국인 수급 가격 driver 1순위" | ⚠️ "Roller-KOSPI 15세션 50조 매도" — 일자 implicit | ❌ n=1 episode (15세션), 시계열 IC·CI 없음 | n/a | n/a | n/a | ⚠️ **단정 어휘 "1순위"** = rule §2 금지 list (n=1 event 에 단정 verdict 금지) → **FAIL** |

**direction.md §③ 가설 12 정량 claim**:
- 가설 H1-H12 = "(반증조건 포함)" + falsifier 명시 (예: "e-CUSUM baseline +0.05 단측 붕괴") — 5게이트 통과 시 weight_rule 등록 위임 박제 → 가설 형식 자체는 OK.
- ⚠️ ★H9 breadth_kospi "음 = 반도체 dominance 단기 alpha (자체 정의)" — frame §3 "tier 강등 가능성" hedge 박제 ✅.

**1.6 분석 unit ↔ portfolio label 분리** (small-n rigor §1.6):
- frame §1 Tier 표 = portfolio label (산업) + 펀더멘털·거시·산업 cycle 지표 = β 측정 unit (Layer 1/2/3). 두 라벨 분리 명시 ✅ (frame §5 산출 양식 8 파일 = `validation-fundamental.md` / `validation-macro.md` / `validation-industry.md` Layer 별 분리).

**정정 권고**:
1. direction.md §① 정량 claim 4개 모두 (a) coverage 일자 inline + (b) n inline + (c) hedge 어휘 ("driver 1순위" → "방향성 강 prior, 단일 episode 잠정") 박제.
2. frame §3 "외국인 flow base 0.20+ (v2 상향, R1 finding: Roller-KOSPI 15세션 50조 매도 driver 1순위)" → "★0.20+ (v2 잠정, R1 finding: Roller-KOSPI 15세션 50조 매도 episode 1건 기반. 산업 subagent 5게이트 통과 검증 위임. 미통과 시 v1 0.18 fallback)".
3. consult-round-{1,2}.md 자가감사 (E축) 가 R1 PARTIAL → R2 PASS 라고 박제했으나, R2 자가감사가 cross-source 한 finding 은 일본 TSE·toraniko 만. 외국인 flow magnitude·산업 Tier 50% snapshot 은 cross-verify 안 됨 → R2 E축 PASS 박제는 **자가 과대평가**.

**판정 근거**: 4 정량 claim 중 1 PARTIAL + 3 FAIL (n / hedge 어휘 / 단정) → **PARTIAL** (※ direction.md inline 박제 누락 + frame.md "1순위 driver" 단정 어휘 위반).

---

## §2. 5 금지 위반 N건

**위반 1건 (Axis 2 결과)**:

**위반 #1 — plan.md §Phase 5 "Dispatch prompt 양식" 5 금지 inline 박제 누락**
- 파일 path: `D:/projects/Inv/study-research/eq_kr/plan.md` §37-43
- 인용: "Dispatch prompt 양식 (각 subagent) / - frame.md v2 정독 의무 (SSOT) / - universe = KrxSectorProvider PIT 동적 ... / - 5게이트 (frame §M4) + 12축 (evaluation-axes v2)"
- 정정 권고: dispatch prompt 양식에 5 금지 inline 박제 5줄 추가 (점추정 prior X / 합성 데이터 X / 자문 그대로 코드화 X / single-source 단정 X / small-N 단정 X). 현재 Phase 5 12 산업 dispatch 진행 중 (progress.md 14:00) — 회수 후 Phase 6 평가 subagent 가 evaluation-axes §4 양식으로 5 금지 위반 검출 의무 (구조적 fallback).

**잠재 위반 (Axis 8 결과, 직접 5 금지 위반 아님)**:
- direction.md §① "외국인 수급 가격 driver 1순위" 단정 어휘 = small-n rigor §2 단정 어휘 금지 list 위반 (n=1 episode). 5 금지 #5 (small-N 단정 금지) 의 정신과 부합 — 단 5 금지 #5 는 "cell N<24 유의 주장" 직설 표현이라 단정 어휘 자체 차단 메커니즘은 small-n rigor rule 이 강함. **간접 위반 1건**.

**총 직접 위반 = 1건 (Axis 2 plan dispatch prompt) + 간접 위반 1건 (Axis 8 direction "1순위" 단정 어휘)**.

---

## §3. 자문 finding cross-verify 표 (R1+R2)

Axis 6 표 그대로 재인용:

| Finding | 학술 | 실무 | 1차 | 3채널 ? |
|---|---|---|---|---|
| 산업 12 Tier 분할 | ❌ | ✅ | ⚠️ | PARTIAL |
| 외국인 flow base 0.20+ | ⚠️ | ✅ | ❌ | PARTIAL |
| 신지표 #1 breadth | ❌ | ⚠️ | ❌ | WEAK (자체 hedge) |
| 신지표 #2 MSCI cap | ❌ | ✅ | ❌ | PARTIAL |
| 신지표 #3 ETF leverage | ❌ | ⚠️ | ❌ | WEAK |
| 신지표 #4 flow regime | ❌ | ⚠️ | ❌ | WEAK |
| toraniko·skfolio OSS | ✅ | ✅ | ❌ | PASS (hedge: first mover) |
| 일본 TSE 2년 후 -23pt | ⚠️ | ✅ | ⚠️ | PARTIAL |
| e-KJFS R&D p<0.01 | ✅ | ❌ | ✅ | PASS |

3채널 충족 finding = 1 (e-KJFS) + 1 hedge PASS (toraniko, first mover 명시) = 2 / 9.

---

## §4. frame v2 6 갱신 항목 의미·정합 검증

| 갱신 항목 | 의미 | 정합성 검증 |
|---|---|---|
| §1 12 산업 Tier 분류 | T1 반도체 500k / T2 자동차·금융·2차전지 300k / T3 8 산업 150-200k | ✅ R1 finding (50.44% 집중) + plan §Phase 5 dispatch table 일관 |
| §3 Layer 2 외국인 flow base 0.20+ + 신지표 4 | 외국인 flow 가중 강화 + breadth/MSCI cap/ETF leverage/flow regime 신지표 | ⚠️ "★0.20+" 단정 / "driver 1순위" 단정 어휘 — small-n rigor 위반. 신지표 4 hedge 박제 OK ("tier 강등 가능성") |
| §M3 12 cell → 36 cell | Macro 4 × KRW 3 × 외국인 flow 3 + cell collapse fallback 3단계 | ✅ N gate 강화 + cell collapse 의무 명시 (3단계: 36 → merge → 외국인 flow 3 fallback) |
| §M4 #5 OOS = skfolio CombinatorialPurgedKFoldSplit | embargo 5d (forward return overlap 차단) | ✅ R2 §1.2 OSS 채택 finding 직접 매핑. ✅ AUDIT-GUIDE §1 D축 OOS walk-forward 의무 충족 |
| §M5 (신규) toraniko factor model baseline | MIT numpy+polars, Barra vein, raw + neutralized IC 둘 다 보고. Korean KOSPI first mover. fallback = pandas/numpy 자체 factor 회귀 | ✅ R2 §1.2 finding 직접 매핑. ⚠️ first mover 인정 hedge OK, 단 frame §6 J 축 ("factor neutralization") = AUDIT-GUIDE J 와 불일치 (Axis 1 FAIL) |
| §6 8축 → 12축 (AUDIT-GUIDE 인용) | Hard-fail 4 (B·C·D·I) 명시, 신규 4축 I/J/K/L | ❌ I 좁힘 + J/K/L AUDIT-GUIDE 와 명칭·내용 불일치 (Axis 1 FAIL) |

**종합**: 6 갱신 항목 중 4 OK + 1 단정 어휘 위반 (외국인 flow §3) + 1 axis 명칭 drift (§6 J/K/L AUDIT-GUIDE 불일치). 갱신 자체는 R1+R2 finding 정직 반영, 다만 §6 axis 명칭 drift 가 산업 subagent self-audit 단계 오염 위험 → **개선 우선순위 #1**.

---

## §5. Hard-fail 4 (B·C·D·I) 우선 검증

| 축 | 현 단계 (방법론 layer) | 위반? | 사유 |
|---|---|---|---|
| **B 실데이터 검증** | frame §0 #3 합성/시뮬 데이터 금지 + 실제 DART/KRX/FRED/FxStore PIT + 외부 무료 소스 명시 + frame §M4 5게이트 + frame §5 raw .py 재실행 의무 | ✅ **NO** | 방법론 layer 박제 충분. 실측은 Phase 5 산업 subagent 위임 — Phase 6 평가 시 검증 |
| **C yaml 도출 추적성** | frame §7 yaml `source_ids: [str, ...]` + `gate_status: {n: pass, ...}` + `base_weight_range: [float, float]` (점추정 X) + frame §5 ⚠️ "모든 finding 에 source ID 매핑 의무" | ✅ **NO** | yaml template 추적성 메커니즘 박제 충분 |
| **D PIT / lookahead** | frame §2 "거래정지 = krx_universe `is_paused` flag" + frame §3 Layer 1 "vintage_policy=point_in_time" + direction §② "DART 공시일+45-90일 지연 / 가격 익일시가 / FRED first-release vintage" | ✅ **NO** | PIT vintage policy 박제 + 직접 시점 정의 |
| **I 생존편향** | frame §2 "상폐 = krx_universe.delisted 포함 (생존편향 차단, return = 청산가 또는 -100%)" + frame §6 I 축 "krx_universe.delisted 포함" | ⚠️ **PARTIAL** | 상폐 ✅, 그러나 **티커변경·액면분할·PIT universe (시점별 inclusion 동적)** 박제 부재. AUDIT-GUIDE I 정의 "상폐·티커변경·액면분할 반영, 살아남은 종목만 테스트 안 했나" 완전 매칭 X — frame §2 "액면분할·병합 = 수정주가 (FDR 자동)" 박제 있으나 frame §6 I 축에서 명시 X |

**Hard-fail 4 종합**: **위반 0건 (FAIL 없음)**. ⚠️ I 축 partial (frame §6 정의 좁힘) — Axis 1 FAIL 결과와 같은 root cause (frame §6 신규 4축 명칭·내용 drift). 정정 권고: frame §6 I 축 정의를 "krx_universe.delisted 포함 / 티커변경·액면분할·PIT universe 동적 inclusion 명시" 로 확장.

---

## §6. 개선 권고 top 5

### #1 (★최우선) — frame.md §6 12축 J/K/L AUDIT-GUIDE 정합 정정 [Axis 1 FAIL 근본 원인]

**위치**: frame.md §6 (§200-228)

**정정**:
- **J 축**: "factor neutralization" → "**경제적 유의성·거래비용·capacity**" (한국 거래세 0.18-0.23% + 슬리피지 왕복 0.3% 차감 후 alpha + KOSDAQ 소형주 일평균거래대금). factor neutralization 은 frame §M5 toraniko baseline 으로 별도 분리 (axis J 가 아닌 §M5 게이트로 처리).
- **K 축**: "regime classifier 추적성" → "**다중검정 보정**" (산업 × 지표 × regime cell 시도횟수 공시 hard + Deflated/Haircut Sharpe > 1.0 + Bonferroni / BH FDR 명시). regime classifier 추적성 은 Hard-fail C (yaml 도출 추적성) 의 sub-요건으로 흡수.
- **L 축**: "직교성" (within-industry partial-corr ≤0.7) → "**통합 상관행렬 정합성**" (Phase 7 통합 시 cross-sleeve 공통인자 USDKRW·외국인 flow·HY OAS 1회 계상 + PSD eigh-floor 차단). within-industry 직교성은 frame §3 Layer 1/2/3 다중공선성 sub-요건으로 흡수.
- **I 축** (Axis 5 결과): "krx_universe.delisted 포함" → "krx_universe.delisted 포함 + **티커변경 / 액면분할 / PIT universe 동적 inclusion**" (AUDIT-GUIDE I 완전 매칭).

**효과**: 산업 12 subagent self-audit `12axis-audit.md` 가 J/K/L 정확하게 self-audit → Phase 6 평가 subagent 와 일관. 거래비용·다중검정·통합 PSD 사전 차단 메커니즘 회복.

### #2 — plan.md §Phase 5 dispatch prompt 양식 5 금지 inline 박제 추가 [Axis 2 PARTIAL]

**위치**: plan.md §Phase 5 "Dispatch prompt 양식" (§37-43)

**정정**: 5줄 inline 박제 추가.
```
- ⛔ 5 금지 (frame §8 의무 박제):
  1. 점추정 prior 박제 금지 (IC → base_weight 직접 X, 분포+CI+게이트 필수)
  2. 합성/시뮬 데이터 금지 (실제 DART/KRX/FRED/FxStore PIT + 외부 무료 소스만)
  3. 자문 그대로 코드화 금지 (gemini/claude 답 → yaml 직접 X, 본 분석가 비판·환각 cross-verify 후 채택)
  4. Single-source 단정 금지 (학술 + 실무 + 1차 데이터 3중 cross-verify 의무)
  5. Small-N 단정 금지 (cell N<24 "유의" 주장 X, 5게이트 §M4 N gate 우선)
```

**효과**: Phase 5 산업 subagent 가 frame.md v2 정독 skip 시도 안전망. 현재 Phase 5 dispatch 진행 중 (progress.md 14:00) 이라 회수 후 Phase 6 평가 subagent fallback 검출 의존 — 다음 자산군 (eq_us 등) baseline 적용 시는 본 정정 의무.

### #3 — direction.md §① + frame §3 단정 어휘 hedge 정정 [Axis 8 PARTIAL]

**위치**:
- direction.md §① "외국인 수급 가격 driver 1순위 = Roller-KOSPI 15세션 50조 매도" (§9)
- frame.md §3 Layer 2 "★0.20+ (v1 0.18 → 상향, R1 finding: Roller-KOSPI 15세션 50조 매도 driver 1순위)" (§97)

**정정**:
- direction §① → "외국인 수급 = 한국 미시구조 핵심 driver (Chae-Yang 2007 KAR 학술 baseline / Roller-KOSPI 15세션 50조 매도 episode 2025-05 BTIG cited single source). 정량 magnitude 잠정 — 산업 subagent 5게이트 통과 검증 위임."
- frame §3 → "★0.20+ (v2 잠정 상향. v1 0.18 → R1 finding (Roller-KOSPI episode 1건 + Chae-Yang 학술) 기반 방향성 강 prior. 산업 subagent 5게이트 통과 검증 의무. 미통과 시 v1 0.18 fallback)"
- direction §① "Korea discount 본질 = composition effect (e-KJFS 2025 KJFS 54-5 학술): R&D/CAPEX/Intangible pos p<0.01" → "★ Korea discount = composition effect 방향성 (e-KJFS 2000-2022 N=7443 KOSPI + 3021 KOSDAQ panel, R&D/CAPEX/Intangible pos p<0.01)" — 표본 기간·n inline 박제.

**효과**: small-n rigor §2 단정 어휘 금지 list 회피 + empirical-claim-presentation §1.1-§1.2 coverage·n 인라인 의무 충족.

### #4 — frame.md + progress.md 다운그레이드 금지 박제 추가 [Axis 4 PARTIAL]

**위치**:
- frame.md §9 통신·dispatch 규칙 끝 (§313-318)
- progress.md Phase 6 (§68-74)

**정정**:
- frame §9 끝에 "⛔ analyst-level lens 다운그레이드 금지 — 시스템·factor model 못 받으면 fallback (raw + neutralized 둘 다 보고) 또는 supervisor 에 파이프라인 업그레이드 요청. subagent 가 시스템 못 받는다고 lens 깎으면 ★Phase 6 평가 FAIL." 1줄 박제.
- progress.md Phase 6 "본 작업방 = 평가 결과 수령 + 통합 책임만, 평가 자체는 위임" 끝에 "★다운그레이드 금지, 업그레이드 계획 의무 (evaluation-axes §4 yaml `system_fit.upgrade_plan`)" 1줄 추가.

**효과**: 사전 차단 + 사후 검출 양방향 메커니즘 회복.

### #5 — consult-round-3.md 학술 cross-verify 보강 또는 Phase 5 dispatch prompt 에 R3 의무 위임 [Axis 6 PARTIAL]

**위치**: 신규 `raw/consult-round-3.md` 작성 또는 plan §Phase 5 dispatch prompt 에 위임

**정정**:
- 외국인 flow alpha magnitude 의 한국 학술 baseline (Chae-Yang 2007 KAR / Kim-Wei 2002 정량 magnitude) 산업 subagent (특히 Tier 1 반도체 + Tier 2 금융) round-N 학술 cross-verify 의무 박제.
- 산업 50% 집중 (반도체) 의 학술 baseline (한국 학술 KFA / NCBI PMC11023228 GARCH-MIDAS 등) cross-source 산업 subagent 위임.
- 신지표 #2 MSCI cap / #3 ETF leverage 의 1차 데이터 (KRX flow snapshots 시계열) Phase 5 subagent 검증 의무.

**효과**: 자문 finding 의 학술 cross-verify 부재 (3채널 중 1채널만 충족) → 산업 subagent layer 에서 보강 → Phase 6 평가 시 E축 PASS 가능성 회복.

---

## §7. 종합 등급 + 사유

### 종합 등급: **PARTIAL**

**사유**:

1. **Hard-fail 4 (B·C·D·I) FAIL 없음** — 방법론 layer 박제 충분 (5게이트 + 추적성 + PIT + 생존편차). I 축 partial (정의 좁힘) 있으나 frame §2 "상폐 + 액면분할" 박제로 보강.

2. **Axis 1 FAIL** (frame §6 12축 명칭·내용 drift, AUDIT-GUIDE J/K/L 불일치) = **본 감사의 가장 critical 결함**. evaluation-axes §2 정확 vs frame §6 잘못 = 이중 SSOT 충돌. 산업 12 subagent self-audit (12axis-audit.md) 오염 위험. 단 Phase 6 별 평가 subagent 가 AUDIT-GUIDE primary + evaluation-axes application 으로 평가하는 한 통합 단계 차단 효과는 회복 가능 — **사후 검출 가능, 사전 차단 부재**.

3. **Axis 4 / Axis 2 / Axis 6 / Axis 8 PARTIAL** — 박제 일관성 부족 (lens 다운그레이드 / 5 금지 dispatch prompt / 자문 cross-verify 학술 channel 부재 / direction inline coverage·n 누락 + 단정 어휘). 정정 권고 §6 #2-#5 로 회복 가능.

4. **Axis 3 / Axis 5 / Axis 7 PASS** — supervisor 직접 평가 금지 박제 견고 + 5-Phase mirror 일관 + small-N rigor 5게이트 매핑 + cell collapse fallback 명시.

**판정 기준 적용**:
- AUDIT-GUIDE §5 양식: 충실 (8축 통과) / 부분 (핵심 일부 미달) / 불충분 (B·C·D·I hard-fail).
- 본 감사: Hard-fail 4 = NO + 8 axis 중 3 PASS + 5 PARTIAL + 1 FAIL (Axis 1) → **부분 (PARTIAL)**.

**다음 단계**:
1. 본 감사 결과를 supervisor 에 final message 회수.
2. Supervisor 가 §6 정정 권고 #1-#4 적용 결정 (Phase 5 dispatch 진행 중이라 frame.md v2.1 in-place Edit 가능).
3. Phase 6 평가 subagent dispatch 시 본 audit 결과 input 으로 제공 (evaluation-axes §5 dispatch prompt 양식 + 본 audit 결과 cross-reference).
4. consult-round-3.md (Axis 6 §5 정정) = 시간 여유 없으면 산업 subagent round-N 위임으로 fallback.

---

> 본 audit 자체 5 금지 자가 점검:
> 1. 점추정 prior 박제 X — frame v2 박제값 그대로 cite 없이 정정 권고 (X)
> 2. 합성 데이터 X — 모든 인용 = frame/plan/direction 실제 파일 직접 Read
> 3. 자문 그대로 인용 X — R1+R2 finding 의 자가 cross-verify 가설 검정 (학술/실무/1차 3채널 표)
> 4. single-source 단정 X — 본 audit 결론 = 8 axis × 8 산출물 cross-reference 후 종합 (single source 금지)
> 5. small-N 단정 X — Axis 7 PASS 박제도 frame §M4 5게이트 + cell collapse fallback "사전 차단 메커니즘 충분" hedge

> 본 audit 가 supervisor 와 독립: supervisor 의 self-audit (consult-round-{1,2} self-check, frame §6) 신뢰 X, 본 audit 결과는 independent finding. Axis 1 FAIL = supervisor self-check 가 frame §6 12축 명시 cite 했으나 AUDIT-GUIDE 와 1:1 정합 검증 누락 — supervisor 자가 점검 미통과 영역.
