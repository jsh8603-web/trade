---
tags: [type/handoff, session/btn-DA, date/2026-05-31]
date: 2026-05-31
session: btn-DA
study_id: eq_us_defensive
trigger: main 인계 우선 지시 (잔여작업·미해결 통합)
---

# Handoff DA — 2026-05-31

## 현황

세션 btn-DA = **eq_us_defensive 종목 스터디 작업방**. 직전 사용자 지시 = **v4 (sleeve 분리) + candidate-ledger 작성 → 정정 (merit 후보 식별 + collector 요청 우선)** → 다시 정정 = **인계 우선 + 작업 취소**.

작업 진척 단계:
- **v1**: 합성 시뮬 (lens-hypothesis-quickcheck) — 폐기 처리
- **v2**: 실데이터 검증 (FRED + Yahoo) — 3 결함 위에 calibrate (H3 위조·M3 과대·H1 spec/impl drift)
- **v3 (부분)**: 3-step gate 완수 (ERROR + rule + verify) — 코드/yaml 격하 fix 미수행
- **v4 (지시만)**: sleeve 분리 (DEFENSIVE_PURE/FINANCIALS) + 누락 지표 (earnings_stability·VIX_term·yield_curve_steepness·credit_beta) + subagent 분할 — 미착수
- **candidate-ledger (지시 취소)**: 작성 X. 대신 merit 후보 식별 + collector 요청 우선 (이것도 미착수)

## 다음 작업 (우선순위 순)

### Priority 1 — main 의 최신 정정 지시 (작업 큐로 전환)

1. **merit 후보 전수 식별**:
   - earnings_stability (Asness QMJ quality factor) — merit: H4 원안 검증 prerequisite
   - VIX term structure (VIX3M/VIX) — merit: defensive VRP carry 알파 원천 (R3 H9)
   - yield_curve_steepness 절댓값 — merit: financials NIM 핵심 (R3 H2 재정의 후)
   - credit_beta full historical — merit: H4a/H3 재검증 (현 표본 n=752 일 short)
   - real EDGAR fundamentals (ROE·FCF·D/E·dividend_safety·NIM·NPL·CET1) — merit: H4·H5·H10·H11 검증 prerequisite
   - TIPS yield (DFII10 vintage PIT) — merit: H1 predictive 재검증 (현재 spot only)
   - VIX3M / VIX1Y term structure — merit: H9 검증 prerequisite

2. **필요 collector + 무료 데이터소스 후보** main 보고:
   - VIX term structure → CBOE 직접 (^VIX3M Yahoo), 일별 무료
   - earnings_stability → EDGAR XBRL 자체 파싱, 무료
   - EDGAR 펀더멘털 → SEC EDGAR XBRL Facts API, 무료
   - HY OAS 일별 historical full → FRED ALFRED `BAMLH0A0HYM2` (2000-01 부터 가용), 무료
   - DFII10 ALFRED vintage → FRED ALFRED, 무료
   - 은행 NIM/NPL/CET1 → EDGAR + Y-9C 파싱 (난이도 上) 또는 FFIEC Call Reports API, 무료

3. **flow**: main collector 구현 → study (이론→실데이터→상관·Rank-IC) → 12축 audit subagent → yaml 반영

### Priority 2 — v3 코드/yaml 격하 fix (인계됨)

1. `run_validation.py` classify_regime: HY 누락 month → `OutOfSample` 라벨 (silent credit=False 금지)
2. H1 forward 3M return 옵션 추가 (`use_forward_3m` flag, contemporaneous vs predictive 동시 출력)
3. M3 Welch t-test β_dxy(E3) vs (E4) gap + Bonferroni 보정
4. validation-H1.md verdict 정정 — "★CONFIRMED 강력" → "contemporaneous co-movement CONFIRMED + predictive 3M FAILS"
5. validation-H3.md verdict 정정 — "★REVERSED" → "★INSUFFICIENT (37mo·실 위기표본 부재)"
6. m3-macro-linkage.md 정정 — "M1 강력 확인·2배" → "비유의 방향성 힌트" + Welch z 명기
7. study_session.yaml v3 재calibrate (base_weight·confidence_hooks 전면)

### Priority 3 — v4 sleeve 분리 + subagent 분할

1. sleeve 재정의: DEFENSIVE_PURE = {XLP, XLU, XLV, XLC mature} / FINANCIALS = {XLF} (독립)
2. 누락 지표 추가 (earnings_stability·VIX_term·yield_curve_steepness·credit_beta)
3. Agent 도구로 산업별 subagent 4 (staples·utility·healthcare·banks) 병렬
4. regime별 δ 두 sleeve 분리 측정
5. empirical-claim-presentation.md 5 의무 + §1.6 + §2 verdict 5단계 강제

## 재개 포인터

### 산출 파일 위치
- 본 방 root: `D:/projects/Inv/study-research/eq_us_defensive/`
  - `study_session.yaml` (v2, 328줄 — v3 재calibrate 대상)
  - `direction.md` (426줄, 2-1)
  - `summary.md` (138줄, v1)
- raw/: `D:/projects/Inv/study-research/eq_us_defensive/raw/`
  - `theory-notes.md` (523줄, 2-2)
  - `round-{1,2,3,4}.md` (자문 누적)
  - `run_validation.py` (353줄 — classify_regime KeyError 버그)
  - `m3_macro_linkage.py` (198줄 — Welch t-test 부착 대상)
  - `validation-H1/H2/H3/H4.md` (격하 수정 대상)
  - `m3-macro-linkage.md` (148줄 — 정정 대상)
  - `validation-metrics.json`, `m3-metrics.json`
  - `fred/` (9 시리즈), `yfinance/` (2 panel)
  - `handoff-bugfix-v3-20260530.md` (v3·v4 인계)
  - `_deprecated_lens-hypothesis-quickcheck-v1-synthetic.txt`, `_v1_lens-research-notes.md` (폐기 marker)

### 시스템 산출
- `~/.claude/memory/promotion-log.md` 상단 ERROR 2건:
  - `[ERROR-202605302245:btn-DA]` sleeve 정의 결함 (XLU+XLF 부호 cancel)
  - `[ERROR-202605302130:btn-DA]` M3 3중 결함 (커버리지 위조·spec/impl drift·multiple comparison)
- `~/.claude/rules/empirical-claim-presentation.md` (5 의무 + §1.6 분석unit↔portfolio 분리 + §2 verdict 5단계)
- `~/.claude/memory/MEMORY.md` ckpt marker 2건:
  - `ckpt-202605302145:btn-DA` (v3 bugfix 인계)
  - `ckpt-202605302245:btn-DA` (v4 sleeve 분리 인계)

### 참조
- `D:/projects/Inv/STUDY-KIT.md` §2 v2 흐름
- `D:/projects/Inv/study-research/macro/study_session.yaml` (7축 framework, 가설2 FAIL 결과)
- `D:/projects/Inv/study-research/macro/timeline.md` §4 (M3 가이드)
- `D:/projects/Inv/study-research/eq_us_cyclical/raw/run_validation.py` (정상 패턴 reference)
- archive: `~/.claude/docs/archive/research-raw/eq_us_defensive-round{1,2,3,4}-20260530.txt`

## 미해결 (open issues)

### 본 방 산출 결함 (확정)
1. **study_session.yaml v2 base_weight·confidence_hooks** = 격하 verdict (H1 contemp / H3 INSUFFICIENT / M3 힌트) 위에 calibrate된 상태 → v3 재calibrate 필요
2. **sleeve 정의** = XLU+XLF eq-weight 가 factor identification 죽임 (ERROR-202605302245) → DEFENSIVE_PURE/FINANCIALS 분리 필요
3. **분석 unit ↔ portfolio label** 두 라벨 명시 의무 (rule §1.6) 가 validation md 에 미적용 → 모든 validation md 첫 줄 수정 필요

### 데이터 결함
4. **HY OAS 일별 시리즈** = 2023-05~2026-05 (n=752) — pre-2023 280개월 부재 → ALFRED full historical fetch 필요
5. **EDGAR 펀더멘털 0** = ROE/FCF/D/E/dividend/NIM/NPL/CET1 미보유 → H4·H5·H10·H11 검증 불가
6. **VIX3M series** = 미보유 → H9 (VRP carry) 검증 불가
7. **DFII10 ALFRED PIT** = 미보유 (spot only) → H1 predictive 재검증 정확성 한계

### 방법론 결함
8. **multiple comparison 보정** = M3 4 sector × 2 epoch 8 비교에 Bonferroni 미적용 (격하만 인지, 코드 미수정)
9. **autocorr block bootstrap** = H3 Bootstrap IID 가정 → block bootstrap 변경 미수행
10. **신규 4 모듈 self-test** = factor_beta_decomp·structural_break·kci_test·normalize_kpi → 작성 0 (theory-notes §5.1 명세만)

### 자문 prior falsifier
11. **H2 Stigum 3-6M lag** = 실측 X (lag=0 만 강) → 가설 재정의 미적용 in yaml
12. **H3 BAB defensive outperform** = 본 데이터 (37mo) 로는 판정불가 (REVERSED 단정 철회 필요)
13. **자문 prior 13 가설** 중 검증 4 / 미검증 9 — 데이터 부재로 보류 (H5/H6/H7/H8/H10/H11/H13 미검증)

## 미커밋 변경 (commit 대상)

본 세션이 생성·수정한 파일 (git status 기준 추정):
- `D:/projects/Inv/study-research/eq_us_defensive/` 전체 (study_session.yaml + direction.md + summary.md + raw/*)
- `~/.claude/memory/promotion-log.md` 상단 2 ERROR
- `~/.claude/rules/empirical-claim-presentation.md` (신규)
- `~/.claude/memory/MEMORY.md` ckpt marker 2건
- `D:/projects/Inv/handoff-DA-20260531.md` (본 파일)

git status 별도 확인 후 commit 수행.

## 작업 흐름 권고 (main 측 진행)

1. **(즉시)** main 이 본 handoff Read 후 candidate 후보 list (Priority 1 의 merit list) 검토 → 무료 collector 우선순위 결정
2. **(collector 구현 후)** 본 방 재기동 → 실데이터 study (이론→실측→상관·Rank-IC) 12축 audit subagent
3. **(study 완료 후)** yaml v4 재calibrate + sleeve 분리 반영 + 누락 지표 통합

## 종료 사유

main 인계 우선 지시. ctx 92%+ critical (long-mode cap 500k 의 92%, 480k 강제 compact 임박).
