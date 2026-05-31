---
tags: [type/progress, domain/inv, study/eq_us, phase/v2-7phase, session/btn-jpdf]
date: 2026-05-30
study_id: eq_us
session: btn-jpdf (eq_us 전담 슬롯, post /clear)
main_session: btn-Codlearn
baseline: study-research/eq_kr/methodology-final-for-main-dispatch.md
---

# progress — eq_us v2 7-Phase 진행

> baseline = eq_kr v2 7-Phase 미러링 (한국 → 미국 study_id·universe 교체). MAIN-DISPATCH.md + handoff-eq_us-bootstrap-20260530.md inject 후 진입.

## Phase 추적

- [x] **Phase 0**: handoff inject 수신, 6 SSOT 정독, eq_us_cyclical/defensive input 확인
- [x] **Phase 2**: methodology-brief.md (R1 brief 통합, 4섹션 자기완결)
- [x] **Phase 3**: R1+R2 자문 수렴 (gemini-web + claude-web 병렬, 4 raw + 환각 4건 정정 + 실측 권고 3건)
- [x] **Phase 3.4**: candidate-ledger.md 작성 (Phase 3 후보 1파일 집약) — ★사용자 후순위 정정 (2026-05-31, 본 progress.md ★박제 #3 참조)
- [x] **Phase 3.5-A**: collector-request-to-main.md 작성 (merit 후보 전수 + 무료 collector 매핑 + main 인계)
- [ ] **Phase 3.5-B** (★다음 세션 진입점, main collector 구현 대기): direction.md → ★main 승인 게이트
- [ ] **Phase 1+4**: evaluation-axes.md + frame.md (eq_us) + plan.md
- [ ] **Phase 5**: Tier 차등 subagent dispatch (T0 custom Mag7+AI / T1 macro-sleeve 3-4축 / T2 sub-archetype 8)
- [ ] **Phase 6**: 별 평가 subagent (★supervisor 직접 평가 금지)
- [ ] **Phase 7**: 통합 study_session.yaml + main 승인

★ **다음 세션 진입점 = `D:/projects/Inv/handoff-eq_us-phase3-complete-20260531.md`** (자기완결 handoff, direction.md 초안 §6 박제됨) + **`study-research/eq_us/collector-request-to-main.md`** (merit 후보 전수 + collector 인계).

## ★사용자 박제 #3 (순서정정 — 2026-05-31 mid-session 지시)

> 사용자 ★순서정정 (앞 메시지 truncate 재송신): "candidate-ledger 먼저 쓰지 마라. (1순위) merit 있는 후보 지표를 실제 추가하는 study 다시 하라 — collector 없으면 main 이 구현하니 'merit 근거 + 필요 collector + 무료 데이터소스 후보' 를 main 에 먼저 보고. 흐름 = main collector 구현 → 너 study (이론→실데이터→상관·Rank-IC) → 12축 audit (별도 subagent) → yaml 반영. collector 없음·후순위·이연은 탈락 사유 부적격. (2순위·마지막) 그러고도 빠지면 그때만 ledger 에 '왜 빠졌나 (merit 없음 OR 실측 무상관)' 기록. 지금 = merit 후보 전수 식별 + 필요 collector 를 main 에 요청. (이미 ledger 쓴 방은 그 후보목록을 작업큐로 전환해 merit 분부터 main 에 collector 요청)"

### 박제 (Phase 3.5 / direction.md / Phase 4+ 작성 시 의무)

1. **★ledger 카테고리 [채택/이연/미채택] 부적격**: collector 부재·후순위·이연 = 탈락 사유 X. 본 progress.md ★박제 #3 가 framing SSOT, ledger 는 단순 후보 집약본 (carryover).
2. **작업큐 SSOT 전환**: 이미 작성된 `candidate-ledger.md` 후보목록 → `collector-request-to-main.md` (작업큐 형태, merit 등급 A~E + 무료 collector + 실측 권고) 로 변환. 다음 세션 direction.md 작성 시 ledger 가 아닌 collector-request 참조.
3. **Phase 흐름 (사용자 박제)**: main collector 구현 → eq_us study 재실행 (이론 → 실데이터 → 상관·Rank-IC) → 12축 audit (★별도 subagent) → yaml 반영. ★supervisor 직접 평가 금지 (MAIN-DISPATCH §5 + 본 박제).
4. **defensive v2 P0 재검증 ★collector 우선순위 inject**: H1~H4 + M3 합성 의심 → 실데이터 재실행 의무 (FRED + yfinance 100% 가용 → main 우선 구현). small-N H3 (n=9) = Block Bootstrap (Politis-Romano) + LOO 의무.
5. **단정 어휘 / 점추정 박제 금지**: 모든 정량 claim = CI + p + n + hedge 어휘 (`~/.claude/rules/small-n-statistical-rigor.md` + `empirical-claim-presentation.md` 강제 적용).
6. **양식 박제 위치**: 본 progress.md + `collector-request-to-main.md` §사용자 박제 (출처 = 본 progress.md). direction.md 진입 시 본 박제 inject 의무.

## ★사용자 박제 (산업별 리서치 산출 양식 — 2026-05-30 mid-session 지시)

> 사용자 추가 지시: "각 산업별 리서치 한 내용은 Inv 에 미국 주식 폴더 지정해서, 너가 양식 알려주고 요약본이랑 raw 일부 저장하라고해. 이후에 비슷한 작업을 할때 해당 자료에서 스터디를 시작하기 위함."

### 박제 (Phase 4 frame.md / plan.md 작성 시 반영 의무)

1. **저장 위치 통일**: 각 산업 subagent 산출 = `study-research/eq_us/industries/{sector}/` (eq_kr frame.md §5 미러링)
2. **요약본 의무 산출** (재진입용 핵심):
   - `summary.yaml` — 통합용 sub-set (lens · indicators_passed · relationships_passed · weight_rule_candidates · confidence_hooks · collector_plan_industry · open_questions, frame §7 양식)
   - `12axis-audit.md` — 12축 self-audit PASS/PARTIAL/FAIL + 근거 (Hard-fail 4 = B·C·D·I 우선)
   - `summary.md` (사람용 1-2 페이지) — 산업 cycle 본질 1줄 / 통과 지표 top 5 / 5게이트 통과 표 / 미해결 의문
3. **raw 일부 저장 의무** (재진입 시 출처 추적):
   - `theory-notes.md` — 산업 cycle 이론 정독 (교과서·논문·증권사 in-depth, source URL 의무)
   - `validation-fundamental.md` / `validation-macro.md` / `validation-industry.md` — Layer 1/2/3 실측 (★raw + factor-neutralized IC 둘 다, regime cell 분해, 5게이트 통과 표)
   - `round-1.md` / `round-N.md` — 자문 라운드 원문 누적 (eq_kr 양식)
4. **재진입 contract** (핵심): 비슷한 작업 (미국 주식 종목 평가 / 같은 산업 재스터디 / Tier 재정렬 / regime 갱신 시) 진입 세션이 `industries/{sector}/summary.md` + `summary.yaml` + `theory-notes.md` 3 파일만 읽으면 즉시 작업 시작 가능해야 함. 의미 = **각 산업 폴더는 self-contained study capsule**.
5. **양식 박제 위치**: Phase 4 frame.md (eq_us 버전) §5 산출 양식 + plan.md dispatch prompt 양식. 사용자 지시 박제 출처 = 본 progress.md.

## ★사용자 박제 #2 (subagent spawn 후 모니터링 패턴 — 2026-05-30 mid-session 지시)

> 사용자 추가 지시: "agent 스폰하고 나서는, 5분 self wake 스킬 걸어두고, 멈춘 agent 있으면 재개 시키고 안되면 새로 스폰하고 반복."

### 박제 (Phase 3/5 dispatch 시 의무 적용)

1. **agent spawn 후 5분 self-wake 등록**:
   - psmux 본 세션 → `self-wake2` skill (in-process teammate haiku watchdog + SendMessage wake-ping) 또는 Bash background `nohup bash -c 'sleep 300 && psmux-send.sh message btn-jpdf "[self-wake] N분점검"' &`
   - Phase 5 산업 11+ subagent spawn 시 의무
   - Phase 3 자문 다회 라운드 사이 idle 보험으로도 적용
2. **멈춤 감지 패턴** (5분 wake 시 점검 step):
   - Agent: `TaskList` + `TaskGet` 으로 in_progress task 의 마지막 update 시각 점검 / `TaskOutput` 으로 진행 메시지 점검
   - psmux subagent: `psmux capture-pane -t {child}` 로 화면 정체 점검 (Calculating hang 또는 queued 입력란)
   - 자문 (Playwright Skill): chrome DevTools 로 로딩/응답 spinner 점검 또는 timeout
3. **재개 시도**:
   - Agent: `SendMessage` 로 "진행 상태 보고 + 막힌 점 1줄" 메시지 → 응답 도착 시 그 막힘 해소
   - psmux subagent: `psmux_send_message` 로 "현 step 보고 / 막힘 1줄" 또는 Enter/Escape 큐 정리
   - 자문: Skill 재호출 (`/gemini-web` 또는 `/claude-web`) 같은 4섹션 브리핑 동일 prompt
4. **재개 실패 시 새 스폰**:
   - Agent: 같은 prompt + 같은 schema 로 `Agent` 재호출 (이전 결과 raw/ 저장 후 폐기 또는 reference 로 inject)
   - psmux subagent: `psmux kill-session -t {child}` 후 `spawn-session.sh` 재spawn → 같은 dispatch prompt 재전송
   - 자문: 다른 채널 (gemini → claude 또는 그 반대) + WebSearch/WebFetch 폴백
5. **반복 무한루프 차단**: 같은 agent 3회 재spawn 실패 시 → main(btn-Codlearn) 보고 + 외부 자문 라우팅 (DA-20260427 ④ 단정 보고 직전 트리거)
6. **양식 박제 위치**: Phase 4 plan.md dispatch table 옆 §모니터링 패턴 + Phase 5 dispatch prompt 양식.

## Working Notes (압축 내성 + 핵심 finding 누적)

- **eq_us 의 미국 특화 본질** (eq_kr 12 가설과 다른 점, R1 자문 핵심 차이):
  - 외국인 flow ≠ driver (미국은 기축통화 자국시장) → 대안 driver 후보 = (a) Fed 금리 path (b) Mag7/AI capex 집중 (c) buyback yield (d) HY OAS regime
  - 반도체 50% 집중 (eq_kr) → 미국은 **Mag7 (AAPL/MSFT/GOOGL/AMZN/META/NVDA/TSLA) ≒ 30%+ S&P 500** 집중 (similar dominance but composition 다름)
  - Korea discount composition (R&D pos / PPE neg) ≠ 미국 (미국은 R&D 이미 reward, factor crowding 위험)
  - 거버넌스 → PBR n.s. (한국) → 미국은 buyback yield + governance score = Russell 1000 검증 다수 (반대)
- **이미 있는 미국 input 활용**:
  - eq_us_cyclical = M3 검증 (β_dxy ≫ β_rate, R²=0.215 cyclical), Tier1 산업 분할 (반도체/소재/산업재/에너지), δ_regime/δ_arch 정의, 5게이트 자체 정의. ★재작업 금지, 통합만.
  - eq_us_defensive = ⚠️ 합성 의심 (synthetic 240m seed 20260530), H1~H4 validation 재실행 검증 의무 (P0)
- **GICS 11 sector ↔ Tier 차등 후보** (MAIN-DISPATCH §2):
  - T1 = IT (XLK, AAPL/MSFT/NVDA) + Communication Services (XLC, GOOGL/META) — 시총 집중 50%+
  - T2 = Financials (XLF) + Health Care (XLV) + Consumer Disc (XLY) + Industrials (XLI) + Energy (XLE)
  - T3 = Consumer Staples (XLP) + Materials (XLB) + Utilities (XLU) + Real Estate (XLRE — reit study 중복 경계, 자문에서 확정)
- **사용자 박제 5금지 + supervisor 직접 평가 금지 + analyst-lens 다운그레이드 금지 + reflexive loop 차단 + tier 정직성** — 모든 Phase 에서 invariant
- **ckpt**: ckpt-202605301700-eq_us-phase0-grounded (6 SSOT 정독 + cyclical/defensive input 확인 + 사용자 추가 지시 박제 완료, Phase 3 R1 진입 준비)

## 보고 채널

```bash
bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[eq_us→main] 경로 + 1줄 요약"
```
