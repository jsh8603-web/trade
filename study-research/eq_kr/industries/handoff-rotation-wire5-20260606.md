---
name: handoff-rotation-wire5-20260606
description: 한국 12산업 rotation WIRE5 변별력 해소 완료(자문 3R+audit PASS+보완). 압축 후 이 파일로 재개. 다음=README 갱신.
next-action: "README.md 갱신(현 세션 WIRE5 이해+작업분, 사용자 지시 '코드화 다끝나고'). + git working tree R15 production 변경(WIRE5 무관) 확인. 첫 행동=README.md rotation/WIRE5 섹션 추가 위치 grep 후 작성"
type: project
tags: [domain/eq-kr, type/handoff, topic/wire5-rotation-변별력, tier/study]
date: 2026-06-06
consult: .consult-kr-rotation-variability-RESULTS.md
---

# 한국 rotation WIRE5 변별력 해소 — 완료 핸드오프 (2026-06-06)

> ★WIRE5 변별력 해소 **완료** (자문 3R 수렴 + steel-audit PASS + 보완 3종). 남은 건 README 갱신 1개.

## §1. 현재 상태 + 첫 행동
- **WIRE5 코드화 완료**: 1차(STATIC_ONLY tilt 0.5%) → 사용자 "변별력+즉시발동 불변요구" → 자문 3R(gemini+claude 수렴) → fork v2 변별력(active 11%) + within v2 selection 등급 + steel-audit PASS + 보완 3종.
- **★첫 행동(재개)**: `README.md`(57KB, D:/projects/Inv/) 갱신 — 현 세션 WIRE5 이해 + 작업분. rotation/eq_kr 섹션 위치 grep 후 추가. (사용자 지시 "코드화 다 끝나고 종료지점에 readme 업데이트").
- ⛔ production(core/stock) 무접촉=byte-identical. go-live 사람게이트 미접촉.

## §2. 진행 맵 (3층)
- 1층 자산배분 regime_to_weights[기구현] / 2층 ★rotation tilt[WIRE5 v2 완료, study-research 실측] / 3층 종목 selection[capsule SSOT + within v2 메타].
- WIRE5 = 2층 rotation 실측 코드(미국 _sleeve_rotation.py fork). production 미배선(go-live 시 통합단계).

## §3. ★변별력 판정 (사용자 핵심 질문 "낮은 게 타당?")
- **2층 산업 간 rotation = 변별력 충분**: active share 11.4%(band 8~12%), 비중 13배 차등(chemical 0.8~10.5%/telecom 13~21%), κ통과 4산업(chemical/steel/refining/telecom IC≥0.29) 비대칭 고밀도. = 0.5% 해소.
- **3층 산업 내 selection = 낮음 (中 최고, 高 없음)**: ρ 반도체0.36/철강0.29/aitech0.28(中 BY생존) / 나머지 低 / 정유 불가.
- **★낮은 게 타당한 이유**: 한국 small market(종목 적음, 정유11/통신14) + 과점(chemical N_eff 4.4=LG화학 지배) + 소표본(88월) + breadth 3.5(FLAM IR=IC×√BR). 종목선택 alpha 천장 구조적으로 낮음. 억지로 키우면 overfit(자문 C7=변별력≠TE). EB 후 small-n IC 보수화=정직.
- **결론**: 한국은 "어느 업종 살지(2층 rotation)"가 변별력 주력, "업종 안 어느 종목까지(3층)"는 반도체/철강/aitech 3곳만 실효. 낮은 건 데이터 한계의 정직한 반영 = 타당.

## §4. 파일 inventory (절대경로)
- 코드 3: `_rotation/_sleeve_rotation_kr.py`(2층 fork v2) + `within_industry_residual_kr.py`(3층 capsule IC 메타) + `build_rotation_signal_panel.py`(Phase1 신호패널)
- 산출: `_sleeve_rotation_kr_results.json` + `validation-within-residual-v2.json` + `data/rotation_signals_panel.parquet`
- spec SSOT: `_rotation/rotation-study_session.yaml` §9(WIRE5 결과) + §보완_적용 + audit_verdict
- 검증: `_rotation/wire5-yaml-code-mapping.md`(전수대조) + `gc-audit-wire5-20260606.md`(steel-audit PASS)
- 자문: `D:/projects/Inv/.consult-kr-rotation-variability-RESULTS.md`(3R C1~C13) + briefing
- plan/progress: `plan-wire5-rotation-20260606.md` + `progress-wire5-rotation-20260606.md`(ckpt-202606060900)

## §5. 미해결·실패 (삽질 위험)
1. **★README 갱신 미착수** = 유일 잔여(사용자 명시 마지막 task). rotation/WIRE5 섹션을 README.md에 추가.
2. **git working tree R15 production 변경**: core/stock_track.py(+28)+value_trigger.py(+15) = WIRE5 무관 별개작업(5/30 stock-corr), 커밋 안됨 → 사용자 확인 필요(WIRE5 책임 아님).
3. **이연(통합단계, yaml 정합)**: 곱 결합 W_i×v_{j|i}(go-live 인접) / hierarchical FDR(yaml §4 통합단계 명시). 현 단계 미구현 정상.
4. 전수표 wire5-yaml-code-mapping.md ⚠️3은 보완 완료(bio defensive복귀/refining·financial sub-gating/C12 EB) — 표 본문은 보완 전 상태라 다음 세션 시 "보완 완료(yaml §보완_적용 참조)" 인지.

## §6. 자문 종합 (RESULTS C1~C13 전체 → 코드 매핑, 누락 0)
- C1 CS demean(expanding z 선행 보완) / C2 base sleeve-RP×EW / C3 silo폐기 cross-sleeve(k2유지) / C4 연속수축κ / C5 risk budget(N_eff cap 폐기) / C6 z비례 additive ±5%clip / C7 active cap15%band8~12% / C8 변별력≠TE / C9 독립베팅 / C10 v중립수축 / C11 ★N_eff 이중처벌방지(rotation κ에 N_eff없음, selection ρ에만 1회) / C12 EB shrinkage(보완 완료) / C13.
- 보완 3종(audit 후): C12 EB(부호보존) + bio defensive복귀(별도sleeve 32% 과대) + refining/financial sub-gating(|z|≥1 발현시만).
- audit PASS(hard-fail0): C11 이중처벌방지+double-count 직교(net~0)+OOS IR≈0 over-claim없음 핵심통과. minor2=C12(보완완료)/git R15(별개).
- 사용자 박제: "0.5% 거부, 변별력+즉시발동 불변" / "무비판 자문수용 금지(코드의도 고려 본인 판단+시뮬 검증)" / "줄자는 capsule이 업종별 맞는걸로 측정(SSOT)" / "산업내 변별력 낮은건 타당(small market 한계)" / KILL금지 teammate.
