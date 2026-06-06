---
name: progress-wire5-rotation
description: WIRE5 한국 rotation fork 실측 코드화 progress. 게이트=yaml spec 완전성 기준.
type: project
tags: [domain/eq-kr, type/progress, topic/wire5-rotation-fork]
date: 2026-06-06
plan: plan-wire5-rotation-20260606.md
---

# WIRE5 rotation fork 코드화 progress

> 인계: 압축 시 [handoff-rotation-wire5-20260606.md](./study-research/eq_kr/industries/handoff-rotation-wire5-20260606.md) + 본 progress Working Notes ckpt.
> SSOT spec = `study-research/eq_kr/industries/_rotation/rotation-study_session.yaml`.
> ⛔ production(core/stock) 무접촉=byte-identical. go-live 사람게이트 미접촉.

## Steps

- [x] **Phase 1 — 신호 통합 패널 동결** · `model: opus` ✅ 완료
  - `_rotation/build_rotation_signal_panel.py` → `_rotation/data/rotation_signals_panel.parquet` (shape 89×11) + `validation-rotation-signal-panel-v1.json`
  - ★완전성 게이트 G1 PASS: G1-a 11/11 산업 추출(누락0, ship monitor 제외) ✓ / G1-b 외국인flow·cli_chg 배제 ✓ / G1-c **fetch 0=전부 frozen parquet(재현성)** ✓ / G1-d shape 89×11(88~89mo 부합) ✓ / G1-e 월수익=measure_integration.panel_monthly() 재사용(Phase2)
  - 신호 OW 방향 부호 정렬(음 신호 telecom/financial/consumer/refining/bio금리 ×-1). aitech=4신호 합성, bio=full_overlay, chemical=z-spread(mom_3 폐기 미투입), consumer=mom_6_cosmetics(primary), refining=유가 yoy(배당 income-trap은 DART 미수집 caveat).
  - 회귀 확인: 신규 파일 study-research 내, production import 0(직교) ✓.

- [x] **Phase 2 — fork OOS 실측** · `model: opus` ✅ 완료
  - `_rotation/_sleeve_rotation_kr.py` → `_sleeve_rotation_kr_results.json`
  - ★완전성 게이트 G2 PASS: G2-a production import 0(measure_integration+_b2_stats=study-research 내) ✓ / G2-b sleeve k=2 export9/defensive3+bio+sub-gating ✓ / G2-c gated 5요소(base residual RP/additive+clip/over-trade 3중 hysteresis+expanding+STT/κ/monitor weight0) ✓ / G2-d N_eff floor3 cap(동시 active 최대 3) ✓ / G2-e walk-forward OOS+fixed-b t+verdict exit 0 ✓ / G2-f underpowered=tentative honest 박제 ✓
  - ★사용자 점검: (1) 신호 부호 11/11 OW정렬 forward 양 IC(강 chemical0.42/steel0.35/refining0.30/telecom0.27/auto0.26, 중 4, 약 aitech0.05/financial0.02) (2) 산업별 비중 base RP(defensive_it 0.16~0.17/cyclical 0.05~0.08/ship 0)+tilt 최대 ±0.3%p, max active share 0.5%(budget 30% 대비 극소)
  - ★결과: predictive β=+0.011 sig=True / **OOS active sig=False(t=0.58)** → verdict **STATIC_ONLY** + κ=0.58. = 신호 raw cycle은 예측하나 residual excess(산업 rotation)는 미약 → tilt 거의 0 = yaml §6 N_eff false breadth + §8 underpowered 실증, 미국 동형.
  - 회귀 확인: Phase 1 패널 입력 의존(직교, production 무접촉) ✓.

- [x] **Phase 2b — fork v2 변별력 (자문 3R 반영)** · `model: opus` ✅ 완료
  - 결과: active share mean 11.4%(band 8~12%), 비중 13배 차등(chemical 0.8~10.5%/telecom 13~21%), 즉시발동 κ통과 4산업(IC≥0.29) 비대칭 고밀도. double-count 직교 ✓(net 공통인자~0). OOS IR ≈0(변별력≠alpha, 자문 C7+yaml §8 실측). 버그수정 2: multiplicative→additive tilt / calib raw Δw 기준.
  - 무비판 검증: ①CS demean double-count=net~0 통과 ②rotation κ N_eff제거=yaml §6 변경 명시 ③active 천장=11% 운용 변별력 충족+OOS≈0 정직.
- [~] **Phase 2b 원본 (v1 STATIC_ONLY)** — 자문 전 버전, v2로 대체.
  - 자문 RESULTS=`.consult-kr-rotation-variability-RESULTS.md` (3R 수렴 C1~C13). 사용자 "0.5% 거부, 변별력+즉시발동 불변".
  - 설계: 신호 expanding z + cross-sectional demean(C1, 단 expanding z 선행=내 보정) / base sleeve-RP×within-EW(C2) / tilt κ_i(연속수축 |IC|/(|IC|+ic0))×s_rot×z_cs clip±5%(C4/C6) / active 컨트롤러 cap15%·band8~12%(C7) / N_eff cap 제거 risk budget(C5) / 즉시발동 robust gate(C4) / monitor weight0.
  - ★무비판 검증(사용자 지시): ①CS demean double-count=portfolio 공통인자 노출 실측 ②rotation κ N_eff제거=yaml §6 변경 명시 ③active 천장 15% vs 변별력=비대칭 고밀도 실측.
  - ★완전성 게이트 G2b: active share 8~15% 도달(변별력 ✓) / 산업별 비중 뚜렷 차등 / 부호 정합 유지 / 즉시발동(STATIC 탈출) / double-count 점검.
- [ ] **Phase 2c — 산업 내 잔차 per-industry 분석 (사용자 추가 요구)** · `model: opus`
  - C9~C13: W_i·v_{j|i} 독립베팅 / 산업내 잔차 불안정→v 산업중립 수축(ρ_i, L2 자르기 아님) / 소수종목=공통원인 N_eff,i(이중처벌 방지) / per-industry IC partial-pool(EB) 필수.
  - 각 산업 종목 cheapness z(미국 composite_cheapness_z 패턴) forward IC → partial-pool + N_eff PR(과점 sleeve 자동) → ρ_i → 산업별 selection 신뢰 高/低 표.
  - ★게이트 G2c: 12산업 selection IC partial-pool 산출 / N_eff PR(raw count 아님) / ρ_i / 소수종목 산업 식별.

- [x] **Phase 2c/2d — 산업 내 잔차 메타분석 (capsule IC SSOT)** · `model: opus` ✅ 완료
  - ★사용자 통찰: 줄자는 capsule analyst가 업종별 맞는 걸로 이미 측정(IC SSOT). v1 book-to-price 통일=실수 → v2 capsule IC 집계+N_eff PR로 정정.
  - within_industry_residual_kr.py v2 + validation-within-residual-v2.json. Explore가 12업종 capsule selection 지표 추출.
  - 결과: 中(반도체/철강/AI테크 BY생존) / 低(나머지) / 불가(정유 2종 과점). ★줄자오류 입증: 배터리 value -0.013→모멘텀+재고 +0.112 회복, 금융 0→은행pbr -0.161. ★IC≠실효: 화학 IC강(-0.142)이나 N_eff 4.4 과점→ρ 0.12.
  - 결합원칙 C10: 低 업종 v 산업중립 수축, rotation 독립. caveat: capsule IC horizon 제각각=상대비교용.
  - 회귀: v1(book-to-price) 보존, v2 별 산출(직교).

- [ ] **Phase 2d (구) — 폐기** (v2가 흡수: 새 측정 X, capsule IC 집계로 전환)
  - 사용자 지적: Phase 2c book-to-price 단일 잣대 = "줄자로 몸무게" 오류. 금융·배터리 "0"은 가치 잣대 부적합이지 selection 무효 아님(배터리=성장주 value 역신호, 은행=만년 저PBR).
  - ★판단: 메인 직접(12업종 통일 측정=일관성, teammate 12기는 신호정의 drift). Explore 1기로 업종별 대표 selection 지표 추출(ctx 보호).
  - 각 capsule summary.yaml 채택 selection 지표(steel cs_mom_12_1 reversal/battery momentum/financial 등) + 부호 + 계산법 → within_industry_residual_kr.py v2(업종별 신호 매핑) → per-업종 IC partial-pool + N_eff PR + ρ_i 재산출.
  - ★게이트 G2d: 12업종 적합신호 IC / 금융·배터리 등급 변화(低→中 가능) 확인 / 과점 N_eff 유지 / book-to-price 대비 개선 비교.
  - 회귀: Phase 2c(book-to-price)는 보존(상대비교용), v2는 별 산출.

- [x] **Phase 3 — 완전성 검증 (yaml↔코드 매핑 audit)** · `model: opus` (+ teammate audit author≠auditor) ✅ 완료
  - ★완전성 게이트 G3 PASS: G3-a `wire5-yaml-code-mapping.md` yaml §1~§9 전수→코드 1:1 매핑(누락0) ✓ / G3-b 범위밖(v_j|i 3층 곱결합·hierarchical FDR)=의도적 skip 박제(통합단계) ✓ / G3-c production 무접촉(git diff=study-research/만, core/stock·stock/는 R15 별개작업) ✓ / G3-d `gc-audit-wire5-20260606.md` steel-audit PASS(hard-fail0, C11 이중처벌방지+double-count 직교+OOS IR≈0 over-claim 없음) ✓
  - 회귀 확인: audit=읽기 전용, 무영향 ✓.

- [x] **종료 — README.md 업데이트** · `model: opus` ✅ 완료
  - README.md "주식 트랙 & 통합 백테스트" 섹션 끝에 `#### study-research/eq_kr — 한국 주식 산업 연구 트랙` 하위섹션 추가(3층 매매구조 + WIRE5 코드 3파일 + 변별력 판정 2층 충분/3층 낮음=타당 + production 미배선 경고). 디렉토리 맵에 `study-research/` 1줄 보강.
  - 회귀 확인: README=문서, 코드 무영향 ✓.

## Working Notes

> [ckpt-202606061330:btn-button] **한국주식 종료 — selection 자문+검증+타당한 방향 실행 완료**. (1)자문 1R(gemini+claude, .consult-kr-within-industry-weak-signal): 산업내 약신호 6질문. (2)검증(verify_weak_signal_severity): EB 부호보존|IC| 대평균 끌림이 약신호 부풀림(telecom 0.053→0.10). (3)★사용자 지적: "변별력=2층 지시인데 EB 버그냐" → 확인=변별력은 2층 rotation, EB는 3층 selection layer 다름. EB 대평균 끌림=자문 C12 spec 충실(결함 아님). "심각 버그" framing 정정, OBSERVE 기록. (4)★타당한 방향 실행: ✅battery primary(inv_ratio→cs_mom_6m IC-never-as-selector) ✅EB v3 계층베이즈(C12 대평균→정밀도 0-shrink s²=(1/(n-1))/T τ²=DL, telecom 0.16→0.07 부풀림제거+中3 BY생존 보존 반도체0.34/철강0.27/aitech0.26) / ⛔(f)종목별 수급=KRX API 차단 DATA-GATE(별 study) / ⏸(b)financial 은행분리·연속수축·pooled=통합단계. (5)커밋 4건: 1c589ac/8332bbf/affc49d/7c6f861. handoff §7 갱신. teammate semi-analyst(반도체 conditional IC 별plan) KILL금지 유지. production 무접촉.

> [ckpt-202606061100:btn-button] **steel-audit 2차 PASS(hard-fail0, 보완필수0) + 권고 3건 반영 + audit 착오 1건 정정**. (1)README.md 갱신 완료(study-research/eq_kr 하위섹션: 3층 매매구조+WIRE5 코드3+변별력판정+production 미배선, 디렉토리맵 1줄). (2)audit non-blocking 권고 3건 반영: ①active cap hysteresis 후 재적용 fix(_sleeve L223後, 천장 0.15 보존, 재실행 active max 0.156→0.150 mean 11.4→10.1%) ②yaml §9 OOS IR≈0→-0.07(cost+cap fix, tentative underpowered) ③대조표 갱신(sub-gating/financial ✅, EB ✅ 행추가, cap fix). (3)★무비판 검증: audit "bio_singleton 별도sleeve 추가(base0.322)" = 현코드 불일치(bio=defensive_it 멤버 base0.183 재실측). 별도sleeve化=32%과대 부작용이라 의도적 멤버유지. audit 착오 판단, 표 🔧(의도적)로 정정 + 무비판검증 메모 박제. (4)within ρ 재실측(EB반영): 반도체0.36/철강0.29/aitech0.28 = README 정확, yaml line170 부정확(0.31/0.30) → 정정. 코드 2재실행 검증(active max=0.150 cap 정확, double-count net~0 유지). production 무접촉. teammate steel-audit idle(KILL금지). 잔여: git R15(core/stock_track+value_trigger) 별개작업 사용자 확인.

> [ckpt-202606060900:btn-button] **WIRE5 변별력 해소 + audit PASS + 보완 완료**. (1)마지막 결정: 자문 3R 수렴(.consult-kr-rotation-variability-RESULTS.md C1~C13)→fork v2 변별력(active 11%, 비중 13배 차등, double-count 직교) + within v2 capsule IC 등급(中 반도체/철강/aitech). steel-audit PASS(hard-fail0, C11 이중처벌방지+double-count+OOS정직 통과). 보완 3종 완료=C12 EB shrinkage(부호보존, _within L곳)+bio defensive복귀(별도sleeve 32% 과대부작용)+refining/financial sub-gating(|z|≥1 발현시만, SUB_GATED/SUB_THRESH). (2)다음 의도: ★README.md 갱신(현 세션 WIRE5 이해+작업분, 사용자 지시 "코드화 다끝나고") + yaml §9 보완반영 1줄 + Phase3 progress 마킹. (3)동기화: yaml §9 layer2/3 = 코드 산출 일치. git working tree에 R15 production 변경(core/stock_track.py+value_trigger.py)=WIRE5 무관 별개작업(5/30) 커밋안됨 확인필요. 코드 3파일=_sleeve_rotation_kr.py/within_industry_residual_kr.py/build_rotation_signal_panel.py + wire5-yaml-code-mapping.md(전수대조) + gc-audit-wire5-20260606.md(audit). production 무접촉 byte-identical. go-live 사람게이트 미접촉. teammate steel-audit idle(KILL금지).

> [ckpt-202606060XXX:btn-button] WIRE5 ①(미국 _sleeve_rotation.py fork) 착수. 사용자 승인="정확 반영 가능하면 ①+plan progress 게이트 완전성 기준+ㄱ". handoff 가정(sleeve_signals.py/INV_R15) 코드 불일치 발견→정정: sleeve_signals.py=3층 종목선택, INV_R15=1층 belief, rotation tilt=2층 부재. 미국 2층=_sleeve_rotation.py(STATIC_ONLY 미배선)=한국 verdict 동형. ★데이터 현실: 12산업 신호 분산+일부 yfinance/ECOS fetch(PIT 비고정)→Phase1 통합패널 동결 선행 필수. 레저 보완 완료(chemical mom_3 hard-fail 폐기/consumer CSI tentative 격하+C축 추적불가/ship 자문3R 복합verdict/통합레저 최종12산업표). steel-audit teammate idle(KILL금지). 다음=Phase1 build_rotation_signal_panel.py 작성. long-mode ON(cap500k).
