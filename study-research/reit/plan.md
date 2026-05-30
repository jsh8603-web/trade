---
tags: [type/plan, study_id/reit, phase/v2-mirror-phase4]
date: 2026-05-31
study_id: reit
asset_scope: [reit]
mirrors: eq_kr/plan.md v2 (Phase 4 작업 계약 baseline)
note: Phase 5-7 작업 계약. 8 sub-cluster Tier 차등 dispatch + 평가 subagent prompt + 통합 게이트.
status: phase4_ready_for_phase5_dispatch
---

# REIT v2-mirror — plan (Phase 4 작업 계약)

> direction.md §8 main 승인 후 Phase 5-7 작업 계약. ⛔ 본 plan.md = Phase 5 dispatch 직전 의무 정독.

## §0 Phase 5-7 SSOT 우선순위

1. `D:/projects/Inv/STUDY-KIT.md` §6 주식 통일 하드룰
2. `D:/projects/Inv/STUDY-ORCHESTRATION.md` 5-Phase
3. `D:/projects/Inv/study-research/AUDIT-GUIDE.md` 12축 SSOT
4. `D:/projects/Inv/study-research/reit/evaluation-axes.md` Phase 6 평가 SSOT
5. `D:/projects/Inv/study-research/reit/direction.md` §1-§8 (Phase 3.5 산출)
6. `D:/projects/Inv/study-research/reit/methodology-brief.md` (Phase 2)

## §1 Phase 5 — 8 sub-cluster Tier 차등 dispatch table

### Tier 1 (단독 cluster, 신호 강함, opus 풍부 토큰)

| Cluster | Universe | M3 β_rate (bp) | Tier 1 사유 | 산출 파일 |
|---|---|---|---|---|
| **C3 Industrial-Logistics** | PLD | −4.51 (t=−4.57) | trade volume + e-commerce + WALT 최단 (PLD ≈ 6y) — supply pipeline dominant | `industries/c3-industrial/{round-1, theory-notes, validation-fundamental, validation-macro, validation-industry, summary.yaml, 8axis-audit}.md/yaml` |
| **C4 Datacenter-Infra** | EQIX, AMT | EQIX −5.39 / AMT −6.86 (t=−7.43) | longest-duration REIT (R2/R3 합의) + AI capex 사이클 + 5G/Sprint-TMobile churn + AMT EM USD exposure. Tower-Datacenter 결합 vs 분리 검토 | `industries/c4-datacenter-infra/{...}` |
| **C8 mREIT (신규 별도 트랙)** | NLY, AGNC, MFA | (미측정) | asset-liability duration mismatch + yield curve slope + MBS OAS + prepayment convexity + book value MTM. equity REIT 와 driver set 분리. R3 carry: empirical duration gap × curve slope 가설 신설 의무 | `industries/c8-mreit/{...}` |

### Tier 2 (중간 신호 / 중간 토큰)

| Cluster | Universe | M3 β_rate (bp) | Tier 2 사유 | 산출 파일 |
|---|---|---|---|---|
| **C1 Residential** | AVB | −2.76 (t=−3.49) | 인구·이민·임금 + 단기 lease. SFR (INVH) Apartment 와 구분 driver 분리 가능성 검토 (R3 carry) | `industries/c1-residential/{...}` |
| **C5 Healthcare** | WELL | −2.08 (t=−2.47) | Medicare/Medicaid 정책 dominant 가설 H9 — event-study (CMS final-rule CAR + SNF-heavy [OHI/SBRA] vs senior-housing [WELL/VTR] cross-section). R3 anchor = Allen-Madura-Springer 2000 (mid). | `industries/c5-healthcare/{...}` |
| **C2 Commercial-Retail** | BXP, SPG | Office −2.57 / Retail −0.89 | ★ Office+Retail 병합 논쟁 (R1 critique) — 본 cluster 내부 Office-WFH (구조 공실) vs Retail-소비 (E4 +70.04%) 별도 lens 분기 가능성 검토 | `industries/c2-commercial-retail/{...}` |

### Tier 3 (경량 토큰 / paradox cluster)

| Cluster | Universe | M3 β_rate (bp) | Tier 3 사유 | 산출 파일 |
|---|---|---|---|---|
| **C6a Lodging** | HST | **+1.79 (t=+1.67)** | ★ 단독 양수 paradox — R2/R3 합의 = cyclical demand proxy (omitted-variable bias). orthogonalize 후 β 0 또는 음수 수축 expect. 2008/2020 RevPAR 붕괴 counter-example. | `industries/c6a-lodging/{...}` |
| **C6b Storage** | PSA | −4.74 (t=−5.50) | recession-resilient + 이사 사이클. C6 Specialty 병합 (Hotel+Storage) 비판 정합 → 별도 cluster. | `industries/c6b-storage/{...}` |

### Tier 미분류 (R4 carry universe 확장 검토)
- Gaming (VICI/GLPI) — Triple-net (NNN) + 긴 WALT + 인플레 전가
- SFR (INVH/AMH) — mortgage-rate inverse, residential sub
- Timberland (WY/RYN) + Farmland — C7 Alternative
- → Phase 5 본 시점 dispatch 안 함. Phase 7 통합 후 universe 확장 별도 plan.

## §2 Phase 5 subagent dispatch prompt 양식 (cluster 별)

각 cluster subagent (opus, run_in_background=true) dispatch 시 다음 prompt mailing:

```text
[v2-mirror Phase 5 cluster {NAME} dispatch]

너 = REIT sub-cluster {NAME} 담당 전문 애널리스트. universe = {TICKERS}. M3 β_rate = {VALUE} bp.

SSOT 정독 (의무):
1. ~/.claude/CLAUDE.md §"멀티에셋 스터디 워크플로"
2. D:/projects/Inv/STUDY-ORCHESTRATION.md 5-Phase
3. D:/projects/Inv/STUDY-KIT.md §6 주식 통일 하드룰
4. D:/projects/Inv/study-research/AUDIT-GUIDE.md 12축
5. D:/projects/Inv/study-research/reit/evaluation-axes.md (본 작업방 평가 SSOT)
6. D:/projects/Inv/study-research/reit/direction.md §8 (v2-mirror Phase 3.5)
7. D:/projects/Inv/study-research/reit/methodology-brief.md
8. D:/projects/Inv/study-research/reit/raw/m3-macro-linkage.md + raw/validation-{H1..H5}.md
9. D:/projects/Inv/study-research/reit/raw/consult-round-{1,2,3}.md (Phase 3 supervisor cross-verify §5)

작업 흐름 (eq_kr methodology Phase 5 mirror):
1. round-1.md — cluster 한정 자문 1R (필요 시 추가 R2/R3, /gemini-web + /claude-web 병렬)
2. theory-notes.md — cluster 한정 이론 정리 (sub-sector 특수 driver + WALT/Debt WAM)
3. validation-fundamental.md — 펀더멘털 (FFO/AFFO 추세, occupancy, NOI growth, leverage, WALT, debt WAM) 실측
4. validation-macro.md — cluster 한정 거시 회귀 (sub-sector ~ [real rate + breakeven + dollar + cap-rate spread + HY OAS + cluster-specific driver]) — ★ collinearity invariant (nominal 제외) + shrinkage (Ledoit-Wolf 2003/2004 또는 Ridge L2) + panel-level pooling (cell 단위 폐기) + Newey-West t-stat
5. validation-industry.md — cluster 내부 가설 (H1 재정식화 / H3 confounding / H6-H10 cluster-relevant)
6. summary.yaml — 7 block (lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan)
7. 8axis-audit.md — AUDIT-GUIDE 8축 자가감사 (Hard-fail 코어 4 우선)

⛔ 5 금지 (모든 자산군 공통):
1. 점추정 prior 박제 금지 — 분포 + CI + 게이트
2. 합성·시뮬 데이터 금지 — yfinance + FRED + Nareit + EIA + Census + CMS 실측만
3. 자문 그대로 코드화 금지 — supervisor 비판 + 환각 cross-verify 후 채택
4. Single-source 단정 금지 — 학술 + 실무 + 1차 데이터 3중
5. Small-N 단정 금지 — cell n<24 "유의" 주장 X, 5게이트 §G축 우선

★ 추가 박제:
- Fisher 항등식 collinearity invariant — nominal+real+breakeven 동시 금지, real+breakeven 만
- analyst-level lens 다운그레이드 금지 — 시스템 못 받으면 파이프라인 업그레이드
- opt-in off = byte-identical 무회귀
- ⛔ 환각 ref 박제 금지 (Beracha-Krautz 2022 / Ling-Naranjo 2014-2015 / Green Street citation)

자문 막힘 시 폴백: WebSearch / WebFetch (1차 학술 PDF · Nareit blog primary) — 직접 1차 출처 우선.

산출 = `industries/{NAME}/{7 파일}` + final message (supervisor 보고).
```

## §3 Phase 6 평가 subagent dispatch prompt (cluster 별 또는 통합)

⛔ **supervisor 직접 평가 금지** — 별 opus 1m subagent (Agent tool, subagent_type=general-purpose, model: opus) dispatch 의무.

### 평가 subagent prompt 양식

```text
[v2-mirror Phase 6 REIT 평가 subagent dispatch]

너 = REIT 자산군 v2 산출 (cluster {NAME} 또는 통합 yaml) 의 독립 감사관. main supervisor 와 분리된 별 평가 layer.

SSOT 정독 (의무):
1. D:/projects/Inv/study-research/AUDIT-GUIDE.md (12축 SSOT)
2. D:/projects/Inv/study-research/reit/evaluation-axes.md (REIT application + Phase 6 평가 절차 §3)

평가 절차 (의무 6 step):
1. §0 Provenance + Recomputation — yaml 수치 → raw .py 재실행 가능성 검증, raw/evidence-map.md trace 점검
2. Hard-fail 코어 4 (B/C/D/I) 우선 평가 — 하나라도 FAIL = block 자동 폐기
3. 보조 8축 (A/E/F/G/H/J/K/L) PASS/PARTIAL/FAIL
4. Tier 판정 (validated alpha / structural prior / opt-in off)
5. 시스템 정합 (§4) — 다운그레이드 금지, 업그레이드 계획
6. PARTIAL/FAIL block → 해당 sub-cluster subagent 재dispatch 권고 (최대 2회)

출력 양식 = evaluation-axes.md §3 의 markdown 표 5 section.

⛔ supervisor pass-bias 회피 — main 또는 본 작업방 supervisor 의 평가 추가 의견 무관, 12축 SSOT 와 §0 Provenance 만으로 평가. 합성 데이터 의심 / 환각 ref / 점추정 prior 박제 = 적극 catch.
```

## §4 Phase 7 — 통합 study_session.yaml + main 승인 게이트

### Phase 7 작업 흐름

1. 8 cluster summary.yaml 합산 → 통합 yaml (7 block):
   - block 1 (lens) — cluster 별 lens 합산 + 다운그레이드 금지
   - block 2 (indicators) — cluster 별 indicator 합산 (PIT 의무)
   - block 3 (relationships / corr_prior) — within-sleeve mean ρ=0.547 + cross-asset cov (Ling-Naranjo 1997/1999 2-stage) + Fisher collinearity 준수
   - block 4 (weight_rules) — cluster 차등 weight + epoch flip + shrinkage (Ledoit-Wolf/Jorion) + λ 분포 sweep
   - block 5 (confidence_hooks) — H6-H10 정량 반증조건 + H1 재정식화 + H3 confounding
   - block 6 (collector_plan) — R4 carry (Beracha-Feng-Hardin 2019 / AMT 10-K / CCI churn / CMS final-rule / Census Construction / CMBS Delinquency / DFII10 / T10YIE / HY OAS)
   - block 7 (code_change_plan) — system_priors.factor_implied_cross_cov 확장 (real rate / breakeven / cap-rate / HY OAS) + within-sleeve equity factor 별도 처리 + PSD 검증
   - block 8 (self_audit_12_axis) — supervisor 자가감사 (Phase 6 평가 subagent 의 결과 박제, supervisor 직접 평가 추가 금지)
2. 직교화 — L축 1회 계상 + PSD (Σ_full = B Λ Bᵀ_cross + W_within + Δ_idio, eigvalsh > 0)
3. 8축 통합 self-audit (supervisor) — block 8 박제 (subagent 결과 합산)
4. **main 보고 + 승인 게이트** — ⛔ 승인 전 register 진입 금지

### Phase 7 산출 파일

- `study_session.yaml` (현 v2 = 861 lines structural prior → 신규 v3 = 8 cluster + 6 driver + H6-H10)
- 현 v2 = `study_session.yaml.v2.bak` 백업 (폐기 X — raw 참고 보존)
- `summary.md` — 1-page 요약 (사용자 빠른 회수용)
- `raw/evidence-map.md` 갱신 (v3 yaml 수치 → script trace)
- `handoff-v2-mirror-completion-{date}.md` (다음 세션 인계)

## §5 coder-readiness 5항목 체크리스트 (DA-20260422-enhanced-planning-wf-phase3-coder-readiness)

| 항목 | 상태 | 박제 위치 |
|---|---|---|
| (1) 외부 의존성 (API/DB/파일/엔드포인트·스키마·경로) | **PASS** | FRED (DGS10/DFII10/T10YIE/BAMLH0A0HYM2) — `https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}` CSV public endpoint. yfinance (REIT 9 sub-sector + mREIT 3 + DXY 'DX-Y.NYB' + WTI 'CL=F') auto_adjust=True. Nareit T-Tracker (cap-rate spread, 분기). Census Bureau Construction Put in Place C30 (월별). CMS final-rule (SNF PPS / IPPS / physician fee schedule, 발표일 anchor). AMT/CCI 10-K (SEC EDGAR). |
| (2) 환경 설정 (env/config/secrets) | **PASS** | python = `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (Windows 절대경로). `sys.stdout.reconfigure(encoding='utf-8')` 의무 (cp949 회피). yfinance/pandas/numpy/scipy/scikit-learn = 기본 설치. shrinkage = scikit-learn Ridge (alpha grid) + arch library Newey-West. Bayesian = PyMC (선택). API key 무관 (FRED CSV public + yfinance public). |
| (3) 입출력 계약 (함수/API/이벤트 파라미터·응답 형식) | **PASS** | Phase 5 cluster subagent 산출 = `industries/{NAME}/summary.yaml` 7 block 양식 (eq_kr summary.yaml 미러). Phase 6 평가 subagent 출력 = evaluation-axes.md §3 markdown 표 5 section. Phase 7 통합 = `study_session.yaml` 8 block (block 1-8). |
| (4) 핵심 알고리즘·조건 (판단 기준·수치·예외 처리) | **PASS** | 5게이트 임계: n>30 (panel-level, cell 단위 폐기) / OOS Rank-IC>0.05 (pooled cross-section + Newey-West) / regime stable / ES>3% (shrinkage 후 수축 신호 기준) / robustness (posterior shrinkage 생존 95% CrI 0 제외 + prior-sensitivity λ grid). H6-H10 정량 반증조건 (CI 하한, hit-rate binomial, CAR significance, lead-lag CCF peak [6,9]m, partial corr). 다중검정 = Benjamini-Hochberg FDR q=0.10 또는 Bonferroni. ⛔ 환각 ref 박제 금지. ⛔ 자문 그대로 코드화 금지. |
| (5) 실행 환경 (스케줄·배포·런타임·트리거·실패 처리) | **PASS** | Phase 5 dispatch = `Agent` tool, subagent_type=general-purpose, model: opus, run_in_background=true. 8 cluster 병렬 dispatch 가능 (concurrency cap 인지 — sub-agent N≤16 default 정합). 막힘 시 WebSearch/WebFetch 폴백. ctx-warn long-mode ON (cap 500k) 의무. Phase 6 평가 = 각 cluster summary.yaml 도착 시 즉시 평가 subagent dispatch (sequential 또는 parallel). Phase 7 통합 = 8 cluster + Phase 6 평가 결과 합산 후 supervisor 직접 작성. main 보고 = psmux_send_message btn-Codlearn (SSOT 헬퍼). 실패 처리: PARTIAL/FAIL block 최대 2회 재dispatch, 3회 실패 시 H 축 (미해결 의문) 박제 + R5 carry. |

**모호 표현 점검**: "적절히"/"필요시" — 본 plan.md 사용 안 함. 모두 구체 수치/조건 명시.

## §6 진행 일정 가이드

| 단계 | 예상 시간 | 의존성 |
|---|---|---|
| Phase 5 dispatch (8 cluster 병렬) | 30-90분 (cluster 별, opus run_in_background) | direction.md §8 + evaluation-axes.md + 본 plan.md 정독 |
| Phase 5 결과 회수 + supervisor 자체 verify | 15-30분 | cluster 별 산출 도착 |
| Phase 6 평가 subagent dispatch (8 cluster, opus 1m) | 30-60분 | cluster summary.yaml 완료 |
| Phase 6 결과 회수 + PARTIAL/FAIL 재dispatch (필요 시) | 15-60분 | 평가 subagent 결과 도착 |
| Phase 7 통합 study_session.yaml v3 + supervisor 8축 self-audit | 60-120분 | 8 cluster + 평가 결과 합산 |
| main 보고 + 승인 게이트 | 5분 | Phase 7 완료 |
| **총 예상** | **3-6시간** | (ctx-warn long-mode ON 유지) |

## §7 산출 cross-ref

- methodology-brief.md (Phase 2)
- direction.md §1-§8 (Phase 3.5 v2-mirror supplement)
- raw/consult-round-{1,2,3}.md (Phase 3 자문 supervisor cross-verify)
- evaluation-axes.md (Phase 1 = Phase 6 평가 SSOT)
- 본 plan.md (Phase 4 작업 계약)
- 신규 Phase 5: `industries/{c1-c8}/{round-1, theory-notes, validation-*, summary.yaml, 8axis-audit}.md/yaml` × 8
- 신규 Phase 6: `industries/{c1-c8}/phase6-eval.md` × 8 (opus 1m subagent 산출)
- 신규 Phase 7: `study_session.yaml` v3 + `summary.md` + `raw/evidence-map.md` 갱신 + `handoff-v2-mirror-completion-{date}.md`
