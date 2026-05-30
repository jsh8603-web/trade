---
tags: [type/candidate-rationale, domain/inv, study/macro, program/collector-build]
date: 2026-05-31
study_id: macro
session: btn-button (macro 스터디 방)
purpose: 거시 누락지표 후보 전수 맵 — 채택/보류/미채택 + 사유 + collector 필요분. candidate-ledger(최종 잔여물)와 분리된 merit 작업맵.
note: "★규칙(main 프로그램): collector없음·후순위·이연 = 탈락사유 부적격. 미채택은 오직 '실데이터 무상관'(실검증 후)만 정당. ⛔합성無."
---

# 거시 누락지표 후보 rationale (merit 작업맵)

> **두 종류 문서 구분**:
> - **본 문서 (rationale)** = merit 있는 후보 전수 + 현 status(채택/보류/측정대기) + collector 필요분. **작업맵**.
> - **candidate-ledger** = 최종 잔여물. study·실검증 다 한 뒤에도 빠지는 후보만 '왜(merit없음 OR 실측 무상관)' 기록. 아직 미작성(첫 작업 아님).
>
> **★탈락 부적격 사유**(main 확정): collector 미구축 / 후순위 / 이연. 이건 전부 "구현하면 됨" → 미채택 근거 안 됨.
> **유일한 정당 미채택** = (a) merit 자체 없음 OR (b) 실데이터 상관 실측 후 무상관.

---

## A. regime classifier JM feature 후보 (`core/brain/regime_classifier.py::_build_jm_matrix`)

현 활성 10종: industrial_production, core_cpi, yield_10y_2y, nfci, credit_spread_baa,
**credit_spread_hy_oas**, **real_rate_10y**, unemployment_rate, breakeven_5y, cfnai.

| 후보 | merit 근거 | status | 사유 |
|---|---|---|---|
| **HY OAS** (credit_spread_hy_oas) | 최강 risk-regime 신호, IG(BAA10Y) 보완 | ✅**활성**(커밋 fabda53) | 비-tautology + factor-beta prior(M3). ⚠️regime-OOS hit 개선은 *미검증* (비대칭 주의: 보류 2종과 동일하게 OOS 미검증, 차이=tautology 안전뿐) |
| **real_rate_10y** (DFII10) | M3 1차 driver, gold anti-real-rate 채널 | ✅**활성**(커밋 fabda53) | 〃 (Fisher 회피: nominal level 미포함→정확공선 아님) |
| **dollar_broad** (DTWEXBGS) | risk-regime 매개(주식 dollar β 우세) | ⏳**보류**(주석 보존, 코드 미삭제) | 시장가격→regime 분류 **tautology 위험**(R1 FCI 경고 동형). ⛔미채택 아님 — OOS regime-eval harness 로 분류개선 입증 시 활성. **testable** |
| **oil_wti** (DCOILWTICO) | 인플레/성장 mixed 신호 | ⏳**보류**(〃) | 〃 dollar/oil 동일 게이트 |

**보류 2종 활성 조건**: FRED 실데이터(VIXCLS 류 아님, DTWEXBGS/DCOILWTICO daily) + **OOS regime-eval harness** 로 "분류 hit 실제 개선" 입증. tautology 우려는 **테스트 가능**(OOS 평가)이지 자동기각 아님.

---

## B. cross-sleeve factor 후보 (`core/study/factor_betas_seed.py::FACTORS`)

현 FACTORS=(rate, dollar, oil, credit) 4종. 직교성 VIF 실측 = raw/m4_factor_vif.py (n=737, data/historical 실 일별).

| 후보 | merit 근거 (실측) | 직교성 | status | collector |
|---|---|---|---|---|
| **vol** (VIX/MOVE) | risk-regime(위기 상관→1 수렴) | ✅**VIF 1.00**(corr~0 실측, 완전직교) | ⏳**Phase A 채택후보**(β=None HOLD seed) — 사용자 go-ahead 후 실 VIX collector→study→audit | 신규: FRED **VIXCLS** (현재 sp500 20d 실현변동성 대용) |
| **growth/industrial-demand** (copper-gold·CFNAI) | ★industrial↔precious **+0.692 잔차**(dollar 통제 후, m4-collection) = rate/dollar/oil 로 못 잡는 *실측 확인된 유일* 공통분산 | 미측(collector 후) | ⏳**1순위** | 신규: FRED **PCOPPUSDM** (copper-gold ratio). CFNAI 는 이미 수집 |
| **credit β** (HY OAS) | 전 sleeve credit 칸 현재 None(M3 미측정). risk-on 베타 prior | — | ⏳**측정대기**(collector 불필요) | 이미수집: BAMLH0A0HYM2 → 각 sleeve OOS β 실측 |
| **rate→real_rate+term_spread 분리** | REIT=명목/커브(β−3.82) vs gold=real rate vs 주식=dollar매개 — 단일 rate축이 3 반응 못 담음 | ⚠️{nominal,real,breakeven} 동시=Fisher 공선 / {real,term} 은 직교 추정 | ⏳**측정대기**(collector 불필요) | 이미수집: DFII10 + T10Y2Y → daily VIF 재측 후 분리 |
| **funding stress** (SOFR-OIS·xccy) | 위기 한정 sparse 신호 | 추정 직교(tail) | 3순위 | 신규: FRED **SOFR** + OIS proxy |
| **RRP/준비금** (유동성) | 느린 추세 | ⚠️dollar·Fed BS 공선 **의심**(미측정) | ⏳**보류**(자동기각 아님) | 신규: FRED **RRPONTSYD** → ⛔공선 "의심"은 미측정 → **VIF 실측 후 판정**(measure-not-assume) |

**parsimony 단계**(F≤7): Phase A=`+vol`(VIF 1.00 즉시) / Phase B(collector)=`rate→real_rate+term_spread` 분리 + `credit` β + `+growth`. append-only(중간삽입 금지, β=None HOLD) → 무회귀.

---

## C. collector 필요분 → main 요청 (psmux 전송 완료, 회신 대기)

| 그룹 | 후보 | collector | 무료 소스 |
|---|---|---|---|
| **A. 신규 collector 필요** | ①VIX ②copper/growth(1순위) ③SOFR-OIS funding ④RRP | main 구현 요청 | FRED VIXCLS / PCOPPUSDM / SOFR / RRPONTSYD (전부 무료, FRED host timeout→DBnomics 경유) |
| **B. collector 불필요(이미 수집)** | ⑤dollar/oil 분류기 JM ⑥real_rate/term_spread 분리 ⑦credit β | **대기 없이 study 착수 가능** | data/historical macro_yahoo_raw.json + DTWEXBGS/DCOILWTICO/DFII10/T10Y2Y/BAMLH0A0HYM2 |

**흐름**(main 프로그램): main collector 구현 → 나 study(이론→실데이터→상관·Rank-IC, small-N rigor) → 12축 audit(별도 opus subagent) → yaml 반영.
**B 그룹은 collector 대기 없이 study 착수 가능** — 사용자/main go-ahead 시 즉시.

---

## D. 미채택 후보 (현재 0건)

> ⛔ **아직 genuine 탈락 0건**. 위 후보 전부 merit 보유 → study·실검증 대상. 실측 후 무상관으로 판명되면 그때 candidate-ledger 에 사유 박제.
> "collector 없음/후순위/이연"으로 빠진 후보는 본 표에 미기재(부적격 사유).
