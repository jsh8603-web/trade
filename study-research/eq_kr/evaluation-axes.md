# evaluation-axes — eq_kr 산업 subagent 평가 (AUDIT-GUIDE 12축 application, v2, 2026-05-30)

> v1 (본 작업방 자체 8축+5게이트) 폐기 — Inv frame `study-research/AUDIT-GUIDE.md` 12축 (8 핵심 + 4 신규) 정독 후 SSOT 재정렬.
> ★ 본 evaluation-axes.md = AUDIT-GUIDE.md 의 **산업 subagent 단위 application layer**. 12축 자체는 AUDIT-GUIDE.md 가 SSOT.
> 본 작업방 (eq_kr supervisor) frame 이 main frame 과 동형 — 개별 산업 작업방에게 시키고 별 sub 가 12축으로 감사.

## §0 사용 주체와 동형 frame 매핑

| Main frame (STUDY-ORCHESTRATION) | 본 작업방 (eq_kr) micro frame |
|---|---|
| Phase A — 10 자산군 작업방 spawn | Phase A' — N 산업 subagent dispatch (opus 1m) |
| Phase B — 3흐름 (이론·검증·코드화) | Phase B' — 산업 subagent 가 frame.md 따라 3흐름 |
| Phase C — opus subagent AUDIT-GUIDE 12축 감사 | Phase C' — **별 평가 subagent (opus 1m)** 가 본 evaluation-axes (=12축 application) 로 감사 |
| Phase D — main register 게이트 통합 | Phase D' — eq_kr supervisor 통합 study_session.yaml (산업별 summary.yaml 합산) |
| Phase E — flag·연관 (live) | Phase E' — 라이브 거래 outcome → flag → lens·corr·weight 진화 |

⛔ 본 작업방 (eq_kr supervisor) 직접 평가 ★금지★ — Phase C' 의 평가 subagent 위임 (main pass-bias 회피 원리 미러).

## §1 평가 대상 (산업 subagent 산출 8 파일 — frame.md §5)

| 파일 | 평가 포커스 (12축 매핑) |
|---|---|
| round-1.md / round-N.md | A (이론 실재성) · E (자문 비판·환각) · F (반증조건) |
| theory-notes.md | A (이론 정독, source URL 의무) |
| validation-fundamental.md | B (실데이터 IC) · C (yaml 추적성) · D (PIT) · G (effective-N) |
| validation-macro.md | B · C · D · G · L (cross-sleeve 중복) |
| validation-industry.md | B · C · D · G · K (다중검정) |
| summary.yaml | C (추적성) · J (거래비용) · K (다중검정) · L (통합 PSD) |
| 8axis-audit.md | 산업 subagent 자가감사 (평가 subagent cross-check, self-audit 신뢰 X) |

## §2 평가 12축 (AUDIT-GUIDE §1 그대로, 산업 단위 적용 표기)

### 핵심 8축 (STUDY-KIT §2.5 = AUDIT-GUIDE §1 핵심)

| 축 | 본 작업방 산업 단위 적용 |
|---|---|
| **A 이론 실재성** | 한국 산업 cycle 이론 (반도체 = Mauldin · Goldman Sachs Semi reports / 2차전지 = BloombergNEF EV Outlook / 자동차 = LMC / 금융 = 한은 금융안정보고서) 실재 정독 — 자문 복붙 금지. 날조 인용 = **hard** |
| **B 실데이터 검증 ★** | 산업 universe (KrxSectorProvider PIT) × DART/KRX/FRED 실측. OOS Rank-IC > 0.03 AND t-stat > 2.0 (Newey-West SE). 합성·시뮬 발견 = **hard-fail** |
| **C yaml 도출 추적성 ★** | summary.yaml 의 base_weight·prior_strength·corr_prior 가 validation-*.md 실측 IC 와 ±5% 매칭. flag→weight·corr·lens 경로 (§4.5 affects_indicator/affects_edge) 명시 = **hard** |
| **D PIT / lookahead ★** | DART 공시일+45-90일 지연 / 가격 익일시가 / 거시 first-release vintage / 거래정지·상폐 PIT. 발표 전 시점 사용 = **hard-fail** |
| **E 자문 비판 + 환각 cross-verify** | round-N.md 의 자문 답이 1차 source (학술 DOI / 증권사 in-depth) 로 cross-verify. 환각 1건 = 그 claim hard-fail |
| **F 반증 가능 + 기각 기록** | 가설 5-10개에 반증조건 (e-value · Rank-IC 임계 · CI) + 기각 1건 이상. 기각 0 = p-hacking 경고 |
| **G effective-N / 검정력 ★tier** | 산업당 종목 N + regime cell N. N 부족 시 차단 아님 = **structural prior(저신뢰) 라벨**. validated 위장 금지 |
| **H 미해결 의문** | confound (예: 한국 시장 외국인 자본 유입 effect 의 결합) + bias 솔직 기재. 공란 = red flag |

### 신규 4축 (AUDIT-GUIDE §1 신규)

| 축 | 본 작업방 산업 단위 적용 |
|---|---|
| **I 데이터 무결성·생존편향 ★** | KRX 상폐·관리·티커변경·액면분할 반영 (krx_universe `delisted_universe`). 생존편향 = **hard-fail** (결과 약화 X, 무효화) |
| **J 경제적 유의성·거래비용·capacity** | 한국 거래세 매도 0.18~0.23% + 슬리피지 (왕복 0.3%+) 차감 후 양(+) 알파. KOSDAQ 소형주 capacity (일평균거래대금) 명시 |
| **K 다중검정 보정** | 산업 × 지표 × regime cell 시도횟수 공시 (hard) + Deflated/Haircut Sharpe > 1.0. 시도 미공시 = hard |
| **L 통합 상관행렬 정합성 ★시스템** | N 산업 partial-corr 를 eq_kr 통합 시 공통인자 (USDKRW · 외국인 flow · 글로벌 risk) 1회 계상. 통합 PSD eigh-floor. 같은 indicator_id 다 산업 중복 = **통합 차단** |

> L 보충: 위기 시 tail-correlation → regime 별 안정성. 중첩 forward-return → **Newey-West / block-bootstrap SE 강제** (B 의 t-stat 게이트 전제).

## §3 Hard-fail vs Soft vs Tier (AUDIT-GUIDE §2 그대로)

- **Hard-fail 코어 4** (통합 차단 — 숫자가 잘못): **B · C · D · I**. 위반 = 잘못된 것, 약한 게 아니다.
- **조건부 hard**: K (시도횟수 공시) · J (alpha 주장 시 비용 차감 후 양) · E (환각 claim) · F (기각 0) · L (PSD·중복).
- **Tier 강등** (차단 X, 신뢰도 라벨): **G (effective-N)**. 같은 임계 + 출력 라벨만 분리 = "validated alpha" vs "structural prior(저신뢰)".
- **Soft/정보성**: A (날조 인용만 hard) · H (공란 red flag) · J capacity.

## §4 평가 산출 양식 (평가 subagent → supervisor)

```yaml
evaluation_by: evaluator-subagent-{id}
date: 2026-MM-DD
evaluator_model: opus-1m
axes_source:
  primary: D:/projects/Inv/study-research/AUDIT-GUIDE.md  # 12축 SSOT
  application: D:/projects/Inv/study-research/eq_kr/evaluation-axes.md  # 본 application
industries:
  - industry: semiconductor   # 또는 ai_tech, chemical, refining, shipbuilding, ...
    verdict: 충실 | 부분 | 불충분  # AUDIT-GUIDE §5 양식 그대로
    provenance:                                # §0 가장 중요
      raw_scripts_rerun: bool                  # raw/ .py 직접 재실행 일치
      synthetic_fingerprint_check: bool        # 결측·갭·이벤트 실재 확인
      yaml_to_raw_traceable: bool              # yaml 수치 → raw 추적 가능
    axes_12:
      A: PASS | PARTIAL | FAIL
      B: PASS | PARTIAL | FAIL  # ★hard
      C: PASS | PARTIAL | FAIL  # ★hard
      D: PASS | PARTIAL | FAIL  # ★hard
      E: PASS | PARTIAL | FAIL
      F: PASS | PARTIAL | FAIL
      G: PASS | PARTIAL | FAIL  # tier 강등
      H: PASS | PARTIAL | FAIL
      I: PASS | PARTIAL | FAIL  # ★hard
      J: PASS | PARTIAL | FAIL
      K: PASS | PARTIAL | FAIL
      L: PASS | PARTIAL | FAIL  # 통합 단계
    hard_fail_count: int        # B·C·D·I 위반 수
    tier: validated_alpha | structural_prior_low_confidence
    system_fit:                                # §4 정합 판단
      current_skeleton_fits: bool
      pipeline_upgrade_needed: bool
      upgrade_plan: str                        # 다운그레이드 ★금지★
    remediation:                               # 부분/불충분 시 구체 (어느 축 왜)
      - str
    flag_dynamic_path_check:                   # §4.5
      affects_indicator_present: bool
      affects_edge_present: bool

summary:
  total_industries: int
  verdict_counts: {충실: int, 부분: int, 불충분: int}
  hard_fail_industries: [str]                  # B·C·D·I 위반 산업
  overall_recommendation: "통합 진행 | N 산업 재dispatch | 파이프라인 업그레이드 필요 (modul · plan)"
```

## §5 평가 subagent dispatch prompt 양식 (Phase C' 진입 시)

```
너는 한국 주식 (eq_kr) 산업 sub-study **평가 (Audit) subagent (opus 1m)** 다.

## SSOT (정독 의무)
1. D:/projects/Inv/study-research/AUDIT-GUIDE.md — 12축 평가 SSOT (★먼저 정독)
2. D:/projects/Inv/study-research/eq_kr/evaluation-axes.md — 본 application layer
3. D:/projects/Inv/study-research/eq_kr/frame.md — 산업 subagent 작업 계약 (cross-check 용)

## 평가 대상
D:/projects/Inv/study-research/eq_kr/industries/{각 산업}/ 8 파일

## 너의 책임 (AUDIT-GUIDE §0 + §5 그대로)
1. ★Provenance + Recomputation★ — yaml 숫자 = 주장. raw/ .py 직접 재실행 (또는 정독 후 재현 가능성 추적) 으로 검증. 합성 지문 (kurtosis·이벤트 실재) 검사.
2. 12축 평가 (PASS/PARTIAL/FAIL) — Hard-fail 코어 4 (B·C·D·I) 우선.
3. tier (validated alpha vs structural prior) 라벨.
4. 시스템 정합 (§4) — 현 파이프라인 표현 가능? 못 받으면 ⛔다운그레이드 금지⛔, 업그레이드 계획.
5. 평가 산출 = evaluation-axes.md §4 양식 yaml + AUDIT-GUIDE §5 보고 양식.

## ⛔ 평가 책임 범위
- 산업 subagent 산출 평가만. 본 작업 재수행 X. self-audit 신뢰 X (참고만, 독립 재계산이 판정 근거).

## 최종 final message
§4 양식 yaml + AUDIT-GUIDE §5 보고 통째로 + supervisor 즉시 의사결정 가능한 1-2 sentence 요약.
```

## §6 본 evaluation-axes 의 사용자 직접 지시 박제

- 본 작업방 (eq_kr supervisor) 직접 평가 ★금지★ (v2 지시 2026-05-30)
- AUDIT-GUIDE.md 12축 = 평가 SSOT (v2 갱신 2026-05-30, Inv frame 정합)
- 5-Phase frame (STUDY-ORCHESTRATION.md §2) 정합 — 본 작업방 = main frame 의 micro-orchestration

## §7 evaluation-axes 자체 갱신 트리거

- AUDIT-GUIDE.md 갱신 시 = 즉시 application 재정렬
- 3R 자문 결과 (Phase 3) 에서 산업 단위 적용 보강 필요 → v2 갱신
- 사용자 추가 지시 → 즉시 박제
