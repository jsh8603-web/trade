---
name: plan-wire5-rotation
description: 한국 12산업 rotation-study_session.yaml(2층 rotation tilt) → 미국 _sleeve_rotation.py 패턴 fork 실측 코드화(옵션①). production 무접촉=byte-identical, go-live 미접촉 사람게이트.
type: project
tags: [domain/eq-kr, type/plan, topic/wire5-rotation-fork, tier/study]
date: 2026-06-06
consult: _rotation/rotation-study_session.yaml (SSOT)
---

# WIRE5 — 한국 rotation fork 실측 코드화 (옵션① 미국 패턴 fork)

> ★사용자 승인: "yaml 한 내용이 정확히 반영 가능하면 ①도 가능" + "plan progress 명시 게이트로 완전성 기준 포함, ㄱ".
> ★배선 방향 ① = 미국 `study-research/eq_us/_sleeve_rotation.py`(2층 sleeve rotation 실측, verdict STATIC_ONLY) 를 한국 12산업용으로 fork.
> ⛔ production(core/stock) 무접촉 = byte-identical 자명. go-live·실주문·push = 사람게이트(D1~D5) 미접촉.

## 핵심 유지 사항 (Immutable)
- production 코드(core/*, stock/*) 무접촉 = study-research/ 안에서만 작성 → byte-identical 자명.
- 곱 구조 `v_{j|i}`(3층 종목선택) = fork(2층) 범위 밖 (미국과 동일, supervisor 통합단계).
- §4 hierarchical sleeve-gatekeeping FDR = yaml 자체 "supervisor 통합단계" 명시 → fork 는 OOS active 측정까지.
- 점추정 박제 금지(분포+CI+gate, small-n hedge). 합성·시뮬 데이터 금지(실 PIT 만). teammate KILL 금지.
- fetch 신호(steel SLX/BTU·consumer ECOS 등) = 1회 fetch 후 parquet 동결 → 재현성 확보(PIT 비고정 완화).

## 배선식 정합 (yaml SSOT → fork 매핑)
- §1 곱 W_i×v_{j|i}: fork=W_i(sleeve+산업 tilt)까지 / v=3층(별 레이어).
- §1 L축 1회계상: telecom 외국인flow 제외, cli_chg 1층 분리 → 패널에서 빼고 조립.
- §2 sleeve k=2: export_cyclical(9)/defensive_it(3, bio·telecom·aitech), bio singleton, sub-singleton gating(refining/ship).
- §3 12산업 primary 신호+부호: 패널 컬럼.
- §5 gated: base=residual RP / tilt=additive+clip / over-trade 3중(hysteresis/persistence/cost) / κ=DSR×N_eff(floor3)×live-OOS / monitor weight0(ship).
- §6 N_eff: residual 3.52 → 동시 active tilt floor(3.5)=3 cap.
- §8: 전 신호 underpowered=magnitude tentative, 부호만 → verdict 사전확률 STATIC_ONLY.

---

## Phase 1 — 신호 통합 패널 동결
`_rotation/build_rotation_signal_panel.py` → `_rotation/data/rotation_signals_panel.parquet`

12산업 primary 신호(§3) + 12산업 월수익 패널을 한 parquet 으로 추출·동결.
- 신호: steel iron_ore_d3 / battery lithium_yoy / auto global_auto_d3 / chemical spread_china_naphtha /
  aitech 합성(game·rate·sw·cloud) / telecom semi_ppi_yoy / bio rate+bio_global / consumer mom_6_cosmetics(primary) /
  semiconductor soxx_d3(또는 export) / refining 유가_mean_rev / financial credit_spread_d6. shipbuilding=monitor(신호 미투입, weight0).
- 제외(§1): 외국인flow(L축 1회계상) / cli_chg(1층 timing).
- 월수익: measure_integration.panel_monthly() 재사용(strict universe + 좀비 마스킹 + refining strict2).

### ★완전성 게이트 G1 (다중 지표, 과락 1개라도 = FAIL)
- [ ] G1-a: 11산업 primary 신호 컬럼 추출 완료(shipbuilding=monitor 제외 정직 박제). 누락 0.
- [ ] G1-b: §1 제외 2건(외국인flow·cli_chg) 패널에서 배제 확인(grep/주석).
- [ ] G1-c: fetch 신호(SLX/BTU/ECOS 등) 1회 fetch 후 parquet 동결 = 재실행 시 동일값(재현성).
- [ ] G1-d: 패널 shape 검증(≈11 신호 col × 88~89 month, 2019-01~2026-05) + 각 신호 yaml §3 부호와 정합(부호 사전확약 일치).
- [ ] G1-e: 월수익 패널 12산업 = measure_integration 재사용(strict2 refining·좀비 마스킹 동일).

---

## Phase 2 — fork OOS 실측
`_rotation/_sleeve_rotation_kr.py` → `_rotation/_sleeve_rotation_kr_results.json`

미국 `_sleeve_rotation.py` 골격 fork + 한국 spec. 입력=Phase 1 패널.
- base = sleeve residual risk-parity(§5). sleeve k=2.
- 산업 tilt = predictive single-slope(신호 t → 산업 excess t+1) + cross-sleeve/N_eff demean → clip → re-demean(§5 additive+clip).
- over-trade 3중: hysteresis no-trade band + persistence + cost-aware(KR STT 0.23% 매도 비대칭).
- κ = program DSR × N_eff(3.5 floor 3) × live-OOS(Rank-IC e-CUSUM reject→κ decaying).
- N_eff cap: 동시 active tilt ≤ floor(3.5)=3.
- monitor weight0: shipbuilding active view 0(위험모형 공분산엔 유지).
- walk-forward OOS active return(fixed-b t) → verdict ROTATION_LIVE vs STATIC_ONLY.

### ★완전성 게이트 G2 (다중 지표, 가중 + 과락)
- [ ] G2-a(과락): production import 0 / study-research 안에서만 (byte-identical 자명). FAIL 시 전체 중단.
- [ ] G2-b: yaml §2 sleeve k=2 멤버 1:1(export 9 / defensive 3) + bio singleton + sub-gating 코드 반영.
- [ ] G2-c: §5 gated 5요소 전부 구현(base RP / additive+clip / over-trade 3중 / κ / monitor weight0).
- [ ] G2-d: §6 N_eff floor3 cap 코드 적용(동시 tilt ≤3).
- [ ] G2-e: walk-forward OOS active + fixed-b t + verdict 산출. 실행 exit 0 + json 산출.
- [ ] G2-f(정직): 전 신호 underpowered = magnitude tentative 박제(점추정 단정 금지). verdict STATIC_ONLY 여도 정상(미국 동형).

---

## Phase 3 — 완전성 검증 (yaml ↔ 코드 매핑 audit)
teammate(author≠auditor) 또는 메인 독립 검증.

### ★완전성 게이트 G3 (매핑 누락 0)
- [ ] G3-a: yaml spec 요소 전수(§1~§6) → fork 코드 반영 1:1 매핑표. 누락/skip 사유 박제(consult-raw-output-mapping 5단계).
- [ ] G3-b: 범위 밖 명시 항목(v_{j|i} 3층 / hierarchical FDR) = "통합단계 이연" 박제 확인(누락 아닌 의도적 skip).
- [ ] G3-c: production 무접촉 재확인(git diff = study-research/ 만). go-live 미접촉.
- [ ] G3-d: 결과 json verdict + caveat 가 yaml §8 honest_caveats 정합.

---

## 실행 엔진 확정
- Phase 1/2 = `model: opus` (메인 직접, 데이터 조립+설계 판단). Phase 3 = teammate audit(idle 중인 steel-audit 재활용 가능) 또는 메인 독립.
- 코딩 wf/harness 부적합(study-research 단일 트랙, 실측 스크립트, 회귀 위험 0=production 무접촉).

## 종료 작업 (사용자 지시)
- 코드화 완료 후 `README.md` 업데이트: 현 세션 이해 + 작업분(rotation 트랙 완성 + WIRE5 fork) 추가.
