---
tags: [type/handoff, domain/inv, topic/study-wire-consult, session/btn-Inv]
date: 2026-06-01
scope: study→wire 자문(설계 6R 수렴 + 코드검증 정정 + 부재 8 + 구현핵심 IC) 진행 인계
push: ⛔ 금지 (로컬 commit만)
predecessor: handoff-study-wire-gap-20260601.md
---

# Handoff — study→wire 자문 진행 (2026-06-01, btn-Inv)

## 0. 진입점 / 현재 위치
- 직전 핸드오프 `handoff-study-wire-gap-20260601.md` §4 자문 5대상 → 본 세션이 자문 실행.
- **자문 채널**: `/gemini-web`(Pro) + `/claude-web`(Opus 4.8) 병렬. raw=`.consult-wire-R{1..9}*.md`(브리핑) + task output(`C:/msys64/tmp/claude/D--projects-Inv/<sid>/tasks/*.output`) + `~/.claude/.gemini-web-last.md`·`.claude-web-basic-last.md`.
- **산출 문서**: `CONSULT-DECISIONS-wire-20260601.md` (설계 결정 SSOT, §1~10 작성됨 — 단 §11 정정 필요, 아래 3).

## 1. 설계 자문 6R 수렴 (R1~R6) — `CONSULT-DECISIONS-wire-20260601.md` §1~7
- R1 독립→R2 교차검증→R3 Red Team(확증편향 적발)→R4 파이프라인 주입→R5 lock→R6 terminal+"shadow=회피"(사용자 반박).
- 핵심 결정: 단일 SSOT derive-on-read / judge=read-only down-only attenuator / 3채널(static corr_prior WIRE·belief→Σ_eff firewall·exogenous flag de-risk-only) / VIX pool 단독(C9/C8 NO-GO) / reject≠missing+factor-space PSD / hardened-soft b(t) / full-sample-gate→FDR / empirical-Bayes λ / 3-tier falsify(convex-leak immortality 방어) / 2-level cost budget(KillSwitch override) / down-only는 attenuator만.
- ★shadow=회피 결론: 경계="unconditional vs regime-conditional". unconditional 20년 large-n=즉시 activate/reject(영구shadow 금지), regime-conditional small-n=UNKNOWN 라벨+재평가. **모든 lifecycle state는 reachable exit 必(black-hole 금지)**.

## 2. ★★최대 발견 — 코드 검증으로 자문 상당부분 정정 (사용자 2회 개입이 정확)
사용자 지시로 H1~H8을 코드 grep 전수확인 → **자문이 "신규"라던 것 대부분 이미 구현+이미 M4 자문(`CONSULT-DECISIONS-M4-factor-integration-20260530.md`, 3R)**:
- 이미 구현(file:심볼): EWMA recency(`core/study/factor_cov_estimate.py _ewma_cov` hl75d) / stress-corr floor `ρ←max(EWMA,stress)` 상향클램프 / `higham_nearest_corr` PSD / James-Stein betas(`factor_betas_seed.build_seed_betas`) / B·Λ·Bᵀ(`system_priors.factor_implied_cross_cov`, ★production 호출부 0=미wired) / shadow OOS(`factor_shadow`) / vol_target 0.15(`risk_sizing`) / Kelly(`coin_sizing`) / regime JM·SJM·HMM(`regime_classifier`) / FX(`core/data/fx.py`+per-bloc) / staleness(`dag` grace+`data_contract _CADENCE_DAYS`) / drift e-CUSUM(`weight_falsification.score_ic_breakdown_eprocess`+`eprocess_backbone.e_cusum`) / 청산netting(`orphan_guard`) / retract비대칭(`update_controller.retract_now`+`hysteresis_and_gate`) / firewall(`flag_router.corr_prior_shrink` level='macro' no-op).
- ★결론: **진짜 gap = runtime 연결뿐**(원 핸드오프 맞음). E97 위반(코드 확인 없이 "빠졌다" 단정) — promotion-log ERROR 대상.
- ★recency 질문(사용자) 답=이미 **two-layer**(gate-Λ EWMA reactive / static-Λ stable) 아키텍처로 존재.

## 3. ★CONSULT-DECISIONS-wire 문서 정정 필요 (다음 세션 우선)
`CONSULT-DECISIONS-wire-20260601.md` §1~10이 **이미-구현된 걸 신규처럼 기술**한 곳 다수. M4 doc+코드와 대조해 "이미 있음(미wired)/진짜 신규/정당 deferral" 3분류로 §11 reconcile 추가 또는 §8 wiring맵 수정. (예: item A Higham=이미 있음, item B stress-swap=이미 stress floor, H1 recency=이미 EWMA, empirical-Bayes λ=이미 James-Stein).

## 4. 코드검증 부재 8항목(G1~G8) + Gemini R8 분류 (`.consult-wire-R8-shared.md`)
grep 0/한정으로 확인된 부재:
- **G1 배분 optimizer turnover/tcost항**(regime_to_weights·risk_sizing prev_weight·cost 0) — Gemini=★Shadow 필수보완(마찰없는 OOS=진공환상수익).
- **G2 weight-level no-trade band**(deadband=상관용) — Gemini=★Shadow 필수보완. 최소표현 `if max|w_target-w_prev|<0.02: return w_prev` 또는 L1 페널티 `−c‖w−w_prev‖₁`.
- **G3 liquidity/ADV** — Gemini=불요(Upbit BTC 초유동).
- **G4 scenario/stress P&L**(stress_corr floor만) — Gemini=go-live 연기. 표현 `np.dot(R_stress,w)`.
- **G5 total portfolio risk 집계**(coin+MA 통합 0) — Gemini=go-live 연기.
- **G6 cash/funding(KRW-USD)** — Gemini=go-live 연기(논리적 accounting까진).
- **G7 inflation/real-return** — Gemini=불요(algo는 명목 표준).
- **G8 ★MA 체결 레이어**(`execute_trade`=Upbit KRW-BTC 전용, 비코인 sleeve 체결 0) — Gemini=go-live 연기, **BrokerInterface 추상화만 선반영**.
- §3 present 보완여부: recency two-layer 충분 / downside stress-floor 충분(semi-cov는 추정오차↑) / ★**regime classifier live debounce 보완필요** / multi-period 충분.
- ★Gemini §4 신규 맹점 3: (1) **Clock Drift Guard**(coin 8h cron vs 월별 macro as-of mismatch) (2) **★FX 노출 공분산**(fx.py 있어도 USD자산 vol=기초+USDKRW+상관이 공분산행렬에 내재됐나? 코드확인 필요) (3) Shadow 현금회계(잉여 KRW 무위험 이자).
- ✅ **Claude R8 읽음**(`bj91n1qgu`): Gemini와 분류 일치 + 더 깊음. ★**G8 broker interface=최우선 lynchpin**(ports-adapters: ExecutionVenue protocol+UpbitVenue(execute_trade refactor)+PaperVenue → G1/G3/G5 동시해결+shadow를 live와 구조동형). G1=shadow P&L round-trip cost차감 필수+optimizer L1 turnover penalty `λ‖w−w_prev‖₁`(권장, double-duty error-shrink). G2=G1 L1에 subsumed(별도 band 不要, Davis-Norman). G4=named scenario 4~6 dated window(GFC/COVID/2022/USDKRW) replay diagnostic(shadow-now). G6=★FX→KRW P&L net 필수+per-sleeve fx_hedge:{none|full} 결정(gold가 KRW투자자엔 USD hedge라 diversification role 좌우=gold decoupling 직결). G5=shared position ledger interface+통합노출 리포트(BTC track A↔crypto sleeve B 이중소유 netting, orphan_guard는 cross-track 아님). G7=optimizer 不要(8h~월 horizon서 inflation=noise), reporting옵션. ★§4 신규(shadow-now correctness): (a)**비동기 cross-session 가격**(coin24/7 vs KIS09-15:30 vs US overnight→단일 timestamp 공분산 Epps bias 0쪽, 공통 cutoff/overlapping window 필요) (b)commodity roll-yield/total-return(futures/rolling ETF면 price≠total) (c)inverse-product daily-reset decay. live-now: (d)position reconciliation(system vs exchange balance 대사) (e)cron dead-man/heartbeat(8h silent fail→KillSwitch도 못 돔). design-now: (f)lot/min-notional rounding이 소액AUM서 invariant 깸. §3: recency two-layer 충분(static prior **periodic refit cadence**만 확인) / semi-cov defer / regime debounce 경량보완(live regime_now flip을 allocation 소비시 min-dwell/confirm-N) / multi-period 不要(G1 L1이 cheap proxy).
- ★**3분류 양모델 수렴**: shadow-now={G1 cost,G4 scenario,G6 FX P&L+hedge,G8 broker interface(최우선),regime debounce,§4abc} / go-live defer={G2 hard band,G3 MA,G5 limit,G6 plumbing,G8 KIS routing,§4def} / 不要={G7 optimizer,G3 coin,EWMA추가,semi-cov,multi-period}. 근거=shadow 본질="go-live 결정 bias없이 측정"→측정정직성(cost·FX·fill·scenario·return correctness)=now, capital-at-risk 늘리는 limit·routing=go-live.
- ✅ decisions 연결: `CONSULT-DECISIONS-wire-20260601.md` frontmatter+H1에 "R1~R6까지만, R8/R9 미반영" 범위 명시 박제 완료(사용자 지시).
- 폐기: R7(`bj1nv606h`+`bz6mcer6v`)=false-gap 브리핑 기반, 무시.

## 5. ⏳ R9-core 미발사 (다음 세션) — `.consult-wire-R9-core.md` 작성됨
구현 핵심(load-bearing) 7결정. **Claude R8 읽은 뒤 R9-core를 양쪽 발사**(브라우저 CDP 충돌 방지 위해 R8 완료 후):
`bash ~/.claude/skills/gemini-web-consult/send.sh send "$(cat /d/projects/Inv/.consult-wire-R9-core.md)"` + claude-web 동일.
- IC1 ★corr_prior 합성(B·Λ·Bᵀ structural이 eb_shrink corr_prior=prior, glasso=likelihood인가) / IC2 gate-Λ vs static-Λ 라이브 라우팅 / IC3 B betas 런타임 source(SEED 미반영·grand-fallback 오염) / IC4 shadow→active graduation owner(update_controller vs StudyRegister) / IC5 opt-in off byte-identical(공유 RNG/cache/FP order 격리) / IC6 judge 결선 go-live 경계 / IC7 version pin 필요성.

## 6. 다음 세션 실행 순서
1. Claude R8(`bj91n1qgu`) Read → Gemini R8과 비교(§4).
2. **FX 공분산 내재 여부 코드 확인**(`core/data/fx.py` + regime_to_weights 공분산이 통화환산 vol 포함하나) — Gemini §4-2 맹점.
3. R9-core 양쪽 발사 → 수렴까지 종합→질의 루프(사용자 프로토콜: 두 모델 수렴+치명결함/변경 0까지).
4. CONSULT-DECISIONS-wire §11 정정(이미있음/신규/deferral 3분류) + G1/G2 shadow-now 반영.
5. 그 후 4관문 2단계(실측 배터리 ①~⑧, 자산별 subagent에 기존 yaml/validation 제공).
- ★보완 최종결정=코드 보는 main이 함(자문은 advisory). 기존 10R 코드 deference(폐기≠보완). go-live=사용자 게이트.

## 7. 환경/제약
- python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + PYTHONUTF8=1.
- push 금지. DRY_RUN/execute_trade SACRED. opt-in off byte-identical.
- 자문 브라우저: gemini=CDP9222, claude=CDP9223(둘 다 로그인됨). send 동시발사는 같은 Chrome서 충돌 — 순차.
- 메모리: `subagent-spawn-existing-research`·`existing-code-deference-10r` 신규 저장됨.
