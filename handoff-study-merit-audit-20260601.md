---
tags: [type/handoff, domain/inv, topic/study-merit-audit, session/bc9afbe0]
date: 2026-06-01
author: bc9afbe0 (신 main, 단일세션)
scope: handoff-reboot-recovery 재개 — 미완 study 마무리 + merit 지표 실데이터 탐구 + 자산별 12축 audit + J축 통합 검증
predecessor: handoff-reboot-recovery-20260601.md
exclude: eq_kr / eq_us = stock.md 별도세션 (사용자 확정 제외)
---

# Handoff — study merit 탐구 + 12축 audit + J축 (2026-06-01)

> **재개 읽기**: 본 파일 → `progress-study-system.md`(ckpt-202606010600/0300) → 아래 각 산출.
> **사용자 지시 요약**: ①모든 작업·audit = 12축 기준 ②핵심 = "추가하기로 검토한 지표를 실데이터로 읽어 탐구" ③자산별 audit ④subagent 병렬 가속 ⑤"다하자"(완주).

## 1. 이번 세션 완료 (커밋 14건, push 보류=로컬만, study-research 미커밋 0)

### 1-A. 미완 study 마무리 + 커밋 (핸드오프 스냅샷은 보수적, 실제는 완료+미커밋이었음)
- eq_us_cyclical d80d148 — yaml v4 격하(δ_regime sign-only + magnitude freeze, verify-delta 근거)
- reit 98237ec — R4 carry verify 5건 + §1.7 소급 self-check
- gold e1c4b48 — yaml v3 + §1.7 H2/H7/H8 ADF·coint 사전검정
- bond_cash 88c5961+e21eea0 — ★Phase7 옵션A 구현(phase7_walkforward_kw.py 실행): P0-1 walk-forward + P0-2 Kim-Wright

### 1-B. merit 지표 실데이터 탐구 (block6 collector_plan "검토만·미탐구" 해소, 무료 FRED+yfinance)
- eq_intl 4지표 23cca11 — JGB-UST / REER / China credit impulse / fx_carry
- defensive VIX term c300902 — VIX3M/VIX ratio
- eq_us_cyclical 선행변수 (commit 직후) — NEWORDER/AMTMNO/DGORDER/ACOGNO/curve/copper-gold (ISM 유료 대체)
- eq_intl L축 92cce9b — fx_carry↔β_dollar 이중계상 측정

### 1-C. 자산별 12축 독립 audit (별도 opus subagent, self-certify 회피)
- bond_cash v5 = ★충실(hard0) 51f3f26 — register 가능. D축 표현 정정(daily/revision-lag)
- crypto cycle2 = 부분(hard0) 58f2184 — ★H11 over-claim 적발→TENTATIVE 격하(prior 0.20→0.05). H7/H8/H10/H12 ledger 탈락, H9 walk-forward 조건부
- eq_intl merit = 부분 e841b37 — ★credit impulse 동시 +0.41=revised-vintage lookahead 착시 적발(Q+1 정렬 시 +0.05 붕괴)→structural_low 격하. fx=PIT-safe exposure 수용
- defensive VIX = ★충실(hard0) 0d98a57 — PIT-pure 정당, over-claim 없음, register 가능

## 2. ★핵심 발견 (cross-cutting, 5연속 재현)
**co-move(동시) 채널은 단단 / forward(예측) 채널은 거의 전멸** — eq_intl credit·fx, bond_cash regime IC, defensive VIX 전부 forward REJECTED. **유일 예외 = cyclical DGORDER_yoy→XLE forward(k=6 live IC +0.311, lookahead 착시 미미, TENTATIVE)**.
→ 시스템 자화상 = "예측 alpha 머신 아님, 레짐 동시진단 + risk-overlay + 방향 prior 머신".
**★PIT 검증이 동시 신호 정당성 가름**: credit impulse=revised-vintage 착시(격하) vs VIX=무개정 PIT-pure(정당). lag_routing=contemporaneous 지표는 weight alpha tilt 금지·risk modulator 한정 배선. NEWORDER→XLE 도 naive→live 붕괴(발표시차 56일 잠식).

## 3. J축 system_priors 통합 — 기계 검증 완료, 정밀 β = shadow TODO
- ★기계 완성·PASS: `core/study/factor_betas_seed.build_seed_betas()`(James-Stein 수축 + tier 매핑 + idio conservation) → `core/study/system_priors.factor_implied_cross_cov()`(B·Λ·Bᵀ + eigh PSD floor). self-test end-to-end PD✓(min eig 0.986), study pipeline 13/13 무회귀.
- ★L축 1회 계상 = 구조적 보장: FACTORS=(rate,dollar,oil,credit,vol) 각 1회. overlap 측정 박제:
  - fx_carry↔β_dollar: monthly R² 8.7%(ETF 공유 25%), dollar 통제 후 partial -0.315 = ~75% 독립 → 별도 유지+fx 를 dollar-orthogonalized 잔차 entry. korea 예외(34%→1회). caveat: DXY window n=59, DTWEXBGS full-sample 재검 의무.
  - VIX_term↔credit(ΔBAA10Y): R² 2.2% = 거의 독립, 통제 후 -0.137→-0.121 유지.
- ⛔ **정밀 β seed 셀 population = shadow-validation TODO (의도적 미수행)**: eq_us_defensive 셀이 전부 TIER_HOLD. 이번 세션 검증분(rate H1 contemp validated·credit H4a industry split validated n=6588·VIX vol structural sign-neg)을 seed 에 넣으려면 cross-sleeve **절대 std β** 가 필요하나, 이번 발견은 sleeve-내부 coincident(VIX=상대수익 RankIC, credit=industry split)라 깨끗한 절대 β 미산출. ★"점추정 magnitude 박제 금지"(제1 SACRED) 원칙상 추측 loading 을 covariance prior 에 박지 않음. → 각 sleeve raw 재실행 표준화 std β 추출(shadow validation 단계)에서 채울 것. James-Stein 이 structural 셀을 pool 로 수축하므로 seed 정밀도는 shadow OOS 에서 보정(점진 rollout).

## 4. 잔여 (다음 세션)
- [ ] cyclical merit 12축 audit (DGORDER→XLE TENTATIVE structural_low, hard0 self-report — 미dispatch, 저우선)
- [ ] J축 정밀 β shadow population: eq_us_defensive(rate/credit/vol) + 각 sleeve raw 재실행 std β 표준화 → seed 갱신 → shadow OOS bias-stat 검증 (factor_shadow.py)
- [ ] eq_intl L축 DTWEXBGS 광폭 dollar full-sample(n=309~362) overlap 재검 (현 DXY n=59 hedge)
- [ ] 잔여 미탐구 지표(credential 게이트): cyclical ISM/forward EPS(유료), commodity cushing(EIA)·roll_yield(CME) — 사용자 빌드 confirm 대기
- [ ] yaml 반영(audit verdict→yaml): crypto cycle3 통합 시 H11 prior 0.05+H9 walk-forward 게이트+H7/8/10/12 탈락 / eq_intl merit(credit coincident-PIT무효·fx exposure·REER structural·jgb reject) / defensive vix_term(family=risk·contemporaneous·prior≈0.14·risk-overlay 라벨) / cyclical DGORDER(ism_pmi_proxy XLE 정밀화 통합)
- [ ] 별도 트랙: local-db L3~L6 (progress-local-db-migration.md, 사용자 'L3 새 세션' 지시 시)

## 5. 환경/원칙
- python = `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + ★`PYTHONUTF8=1 PYTHONIOENCODING=utf-8` prefix 필수(Windows cp949 em-dash crash).
- study 스크립트 raw 캐시 = commit / 대용량 binary(parquet 28MB) = .gitignore + fetch 재실행 복원.
- audit = 별도 opus subagent 12축, self-certify 금지(§5.5). raw 재실행+ADF+half-split+PIT(naive vs live) 독립검증.
- 불변: 점추정 magnitude 박제 금지·sign/direction prior 생존 / belief→_macro 차단 / 공통인자 1회 계상 / push 금지(로컬 commit만) / DRY_RUN SACRED.
- ★ground truth 교차검증: 핸드오프 스냅샷 "미완" 단정 신뢰 금지, git status+yaml grep 으로 실상태 재확인(E97).
