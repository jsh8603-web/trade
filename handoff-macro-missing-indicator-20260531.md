---
tags: [type/handoff, domain/inv, study/macro, session/btn-button]
date: 2026-05-31
session: btn-button (macro 스터디 방)
note: macro 누락지표 코드화 커밋 후 main 독립감사 보강 3건+비대칭 1건 미해결 + 사용자 문서화 요청. compact 재개용.
---

# 핸드오프 — macro 누락지표 보강 (compact 재개)

## 완료
- **커밋 fabda53** (regime_classifier.py 단일, +9/−2): `_build_jm_matrix` 에 HY OAS(credit_spread_hy_oas)
  + real_rate_10y **활성 추가**, dollar_broad/oil_wti **보류**(`# 후보(OOS 검증 후 활성)` 주석, tautology+OOS미검증).
  append-only + len≥60 guard 무회귀, Fisher 공선 회피(nominal 10Y level 미포함), syntax/import OK.
- 산출 전체: study-research/macro/{study_session.yaml, direction.md, timeline.md, summary.md, audit.md,
  m4-factor-expansion.md, raw/(round-1~3, theory-notes, validation-*, m1-*, m4-*, self_audit_power)}.
- M1~M4: timeline.md(배포용 분기13) / m1-findings(factor B·Λ, M4선행) / m4-factor-expansion(VIF 직교, vol VIF1.00) / 누락지표 분류기 코드화.

## main 독립감사 verdict (2026-05-31)
부분충실, **Hard-fail 0, 활성화 차단 불필요**(append-only+sparse JM+falsification kill 안전망). 보류=정직(미검증을 미검증이라 함). 단 비대칭 1건 + 경미 보강 3건.

## ★★순서정정 (main, 2026-05-31, 최신·최우선)
candidate-ledger **먼저 쓰지 마라**. 우선순위 바뀜:
- **(1순위·진행중)** merit 후보 지표 실제 추가 study 재수행. collector없음·후순위·이연 = **탈락사유 부적격**. merit 기준 재평가.
- 흐름: main collector 구현 → 나 study(이론→실데이터→상관·Rank-IC) → 12축 audit(별도 subagent) → yaml 반영.
- **(2순위·마지막)** 그러고도 빠지면 그때만 ledger에 '왜 빠졌나(merit없음 OR 실측 무상관)' 기록.
- **상태**: merit 후보 전수 식별 + collector 보고 완료. main 회신 = B그룹 go-ahead 보류 + B·A study 는 main 재개(btn-button 진행 금지).
  보강 3건+비대칭+문서화 전부 종료(↓ ★보강 완료 섹션). 잔업셋 = ↓ ★잔업 섹션.
  - A.신규collector필요: ①VIX(FRED VIXCLS) ②copper/growth(FRED PCOPPUSDM, +0.692 잔차 흡수, 1순위) ③SOFR-OIS funding(FRED SOFR) ④RRP(FRED RRPONTSYD, 공선 의심=미측정→VIF후판정).
  - B.이미수집(eval/측정만): ⑤dollar/oil 분류기 JM(OOS harness 필요) ⑥real_rate/term_spread 분리(daily VIF 재측) ⑦credit β(HY OAS OOS 측정).
- **재개**: main 회신 = collector 구현분 + B 우선순위 → study 착수. B는 collector 대기 없이 가능.

## ★보강 완료 (보강 3건 + 비대칭 + 문서화 = 전부 종료)
1. ✅**비대칭 1건 = 보강 '비대칭 라벨'** (커밋 d3fd4b3): regime_classifier.py L331~338 주석 — "활성 2종(HY OAS/real_rate)도
   regime-OOS 미검증, 근거=비-tautology+factor-beta prior(M3), regime-IC OOS 아님. 보류 2종과 차이=tautology 안전뿐" 명시.
2. ✅**보강 'hook-wire 라벨'** (커밋 88a3fcb): study_session.yaml 블록5 confidence_hooks 주석 — hy_oas_risk_regime +
   real_rate_duration_penalty = **§4.5 dead-hook**. register+측정기계(flag_router.emit_from_ic→rank_ic→e-CUSUM)는 존재하나
   emit_where 의 "backtest engine" **실측경로 부재**(core 에 backtest 엔진 無 + emit_ic_outcome 호출자 0건, study_register L237 wrapper 만 존재)
   → regime-IC 미실측, confidence prior 고정. 활성조건=backtest 가 emit_ic_outcome(hid, hy_oas_scores, fwd_returns) 주입.
3. ✅**보강 'base_weight 라벨'** (커밋 88a3fcb): study_session.yaml 블록4 weight_rules 주석 — base_weight(0.25/0.22 등)은
   regime-IC 추적값 아니라 *이론 prior 라벨*. regime-eval harness 확보 후 IC-driven 재칼리 전까지 prior 고정.
4. ✅**문서화** (커밋 d3fd4b3): `study-research/macro/candidate-rationale.md` — JM feature 후보 4 + factor 후보 6 +
   collector A신규4/B이미수집3 + 미채택 0건. candidate-ledger(최종잔여물)와 분리.

## ★잔업 (main 이 재개 — btn-button 은 진행 금지, main 지시 2026-05-31)
> main 회신: "B그룹 go-ahead 보류, B·A 그룹 study 는 main 이 재개하니 너는 진행 말 것." → 아래는 **main 재개용 작업셋**.

**B 그룹 (collector 불필요, 이미수집 데이터)** — main 이 study 수행:
- (a) **dollar/oil 분류기 JM 활성**: regime_classifier.py L334~337 보류 주석 2종(dollar_broad/oil_wti). 활성조건 = OOS
  **regime-eval harness** 로 "분류 hit 실제 개선" 입증(tautology 우려는 testable). 데이터 = data/historical macro_yahoo_raw.json(dxy/oil daily) 가용.
- (b) **real_rate/term_spread rate축 분리**: factor_betas_seed.FACTORS rate→real_rate(DFII10)+term_spread(T10Y2Y) 2축.
  선결 = DFII10/T10Y2Y daily **VIF 재측**(Fisher: nominal+real+breakeven 동시 금지). fetch=DBnomics 경유(FRED host timeout).
- (c) **credit β 측정**: FACTORS credit 칸 전 sleeve None → HY OAS(BAMLH0A0HYM2) 로 각 sleeve OOS β 실측. ⛔점추정 박제 금지(James-Stein 수축).

**A 그룹 (신규 collector 필요)** — main collector 구현 후 study:
- ①VIX(FRED VIXCLS, 현재 sp500 20d 실현변동성 대용, VIF 1.00 직교) — Phase A factor 채택후보, β=None HOLD seed.
- ②copper/growth(FRED PCOPPUSDM, copper-gold ratio) — **1순위**, industrial↔precious +0.692 잔차(m4-collection) 흡수. CFNAI 이미수집.
- ③SOFR-OIS funding(FRED SOFR + OIS proxy) — tail-only, 3순위.
- ④RRP(FRED RRPONTSYD) — dollar/Fed BS 공선 **의심(미측정)** → VIF 실측 후 판정(자동기각 금지).

**공통 흐름**(main 프로그램): main collector 구현 → study(이론→실데이터→상관·Rank-IC, small-N rigor: n/p/Newey-West HAC/block bootstrap/Bonferroni) → 12축 audit(별도 opus subagent, AUDIT-GUIDE.md) → yaml 반영. ⛔합성無.

## 재개 포인터 (main)
- 등재 현황: collector-build 프로그램(handoff-collector-build-20260531.md §3.2 큐)엔 macro 후보 **미등재**. DISPATCH-TRACKER §6 엔 vol/VIX 만 'go-ahead 대기'. → main 이 A①~④ + B(a~c) 를 큐에 편입 필요.
- merit 맵 SSOT = `study-research/macro/candidate-rationale.md`. 미채택 0건 → candidate-ledger 아직 불필요(실검증 무상관 판명분만 사후 기록).
- 커밋 경계: core/brain/regime_classifier.py + study-research/macro/ 만(peer 미포함). 보강분 커밋 = d3fd4b3, 88a3fcb.

## 재개 포인터
- 먼저 `psmux capture-pane -p -S -55 -t btn-Codlearn | tail -40` 로 보강 3건 정확 내용 회수.
- regime_classifier.py L325~345 주석 수정(비대칭) → candidate-rationale.md 작성 → main 회신.
- ⛔ psmux 입력 충돌 주의: 보내기 전 입력란 점유 시 `psmux_send_key btn-Codlearn Escape` 후 전송(이번 세션 학습).
- 커밋 경계: core/brain/regime_classifier.py + study-research/macro/ 만(peer 변경 미포함).
