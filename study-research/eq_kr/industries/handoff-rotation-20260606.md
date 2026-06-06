---
name: handoff-rotation-20260606
description: 한국 12산업 rotation timing 측정 자율주행 핸드오프. 다음 세션이 이 파일만으로 재개. batch 10완료/bio+보강 진행/통합·audit 남음.
next-action: "★rotation 분석 트랙 완성(S7 검수 PASS). 사용자 기상시 confirm 보고 → ⛔WIRE5 코드화=사람게이트(메인 직접진입 금지, 사용자 confirm 필수)"
type: project
tags:
  - domain/eq-kr
  - type/handoff
  - tier/study
date: 2026-06-06
---

# 한국 12산업 rotation timing 자율주행 핸드오프 (2026-06-06)

> 사용자 취침 중 자율주행. flag ON(`agent/.secretary/.autopilot-btn-button.flag`). SSOT = plan §10 S5.5/§8 + `.consult-kr-rotation-design-RESULTS.md` + 각 capsule `rotation-signals.md`.

## §0. 갱신 (06-06 05:00) — ★rotation 분석 트랙 완성 (WIRE5 사람게이트만 남음)
- ★**전 12섹터 + 결합 + audit + S6 + S7 완성**: 12섹터 tradeable≥1=11(STRONG4=chemical/steel/battery/auto + tradeable6 + tradeable_weak2=refining/financial) + shipbuilding monitor-only(weight0 정직).
- ★**S7 통합 study_session.yaml** = `_rotation/rotation-study_session.yaml`(검수 PASS). 2층 rotation(k=2 sleeve+gated)×3층 selection 배선식 + L축1회계상 + hierarchical FDR + N_eff 3.52 + minor4 반영. 검수 정정 1건(§2 멤버 표기 정합).
- ★**G-C 독립 audit PASS**(`gc-independent-audit-rotation-20260606.md`, hard-fail 0 = 코드화 자격).
- ★**S6 residual-PCA sleeve k=2**(외국인flow 단일지배 k*=1→보수 k=2, validation-pca-sleeve-v1.json).
- ⛔ **다음 = WIRE5 코드화 = 사람게이트**: cross_sectional_selection.py + sleeve_signals.py + metric_signs. monitor weight0, go-live·실주문 미접촉. **메인 직접진입 금지 — 사용자 confirm 필수**.
- ★자율주행 flag = rotation 분석 트랙 완성으로 해제(WIRE5는 사람게이트라 자율 범위 밖).

## §1. 현재 상태 + 첫 행동
- **rotation batch 10완료** (tradeable≥2 충족): semiconductor(2 cli_chg+export) / consumer(2 mom_6+곡물) / aitech(4 game_espo+rate_10y+global_sw+cloud) / chemical(3 china_mchi+spread+fxi) / auto(3 global_auto+cli_chg6+iron_ore사전이론) / battery(6 리튬multi-source) / steel(2 iron_ore_d3+china_fxi) / telecom(2 외국인flow+semi_ppi) / refining(1 유가, 보강중) / shipbuilding(0 REJECTED, 보강중).
- **진행/미완**: bio(macro overlay 1차측정 완료, composite로 tradeable≥2 판정 진행중) / refine·ship·financial(tradeable<2 보강 nudge 발송, 미반영).
- **★첫 행동**: `cd industries; for d in bio refining shipbuilding financial; do ls --time-style=+%H:%M -la $d/rotation-signals.md; done` mtime 점검 → tradeable≥2 갱신 확인. stuck이면 1개씩 nudge(rolling3). 구조빈약(ship 주가선행/refine 종목불가)은 monitor-only+사유박제 정직 허용.

## §2. 진행 맵
- 목표 = 12산업 ★업종 자체 rotation timing(어느 국면→어느 업종 OW/UW). 종목selection(3층, 완료)과 별 차원 = 2층 동적 rotation.
- 파이프라인 = ★이론(증권 리서치+논문 산업동향)을 통계가 검증. 이론+통계검증=채택 / 이론없이 통계만=data mining 채택불가.
- 규칙: 후보 ≥8개 전수 enumerate + tradeable(채택)≥2(미만 보강) + universe strict 화이트리스트(디렉토리 전체 패널 금지).
- ★전12 완료 → rotation-analyst 통합 → G-C 독립 audit → S6 PCA sleeve → S7 통합 study_session.yaml → WIRE5.

## §3. 사용자 박제 (이번 대화 고유)
- **batch rolling 3** (한번에 12개 X = rate limit 재발). 동시 활성 ≤3, stuck 1개씩 nudge.
- **tradeable(살아남은 채택 지표) ≥2** 미만 섹터 = 최소 2개까지 재발굴. 단 구조적 빈약(정유 종목불가·조선 주가선행)은 monitor-only+사유 박제 정직 허용(무리한 발굴=data mining 회피).
- **산업동향 본질** = 가격 momentum 통계도 유효하나 증권 리서치+논문 이론 베이스 위에서 검증. 사후 채택=HARKing → 사전이론 정당화(auto iron_ore 리플레이션 사례).
- **KILL 금지** = teammate 26 idle 정상, KILL X. **자율주행 flag ON** 유지(완료 시 `rm` 해제).
- **개별 analyst > rotation-analyst v2** = v2가 1명이 12산업 빨리 측정해 universe 오염(디렉토리 전체 패널). 개별 전문가가 strict 검증 = 사용자 의도 정당성 입증.

## §4. 파일 inventory (절대경로)
- plan: `D:/projects/Inv/plan-kr-equity-conditional-ic-20260605.md` §10 S5.5 + §8(2층/3층 regime nesting)
- progress: `D:/projects/Inv/progress-kr-equity-conditional-ic-20260605.md` (Working Notes ckpt 다수)
- 자문 raw: `D:/projects/Inv/.consult-kr-rotation-design-RESULTS.md` (6대 결론 A~F)
- 각 capsule: `D:/projects/Inv/study-research/eq_kr/industries/{섹터}/rotation-signals.md` (§1 부호사전확약 + §3 측정표 + §4 판정 + universe 오염검증)
- cross-industry: `industries/_rotation/` (rotation-analyst v2 baseline, validation-rotation-v2.json — ★universe 오염이라 STRONG 폐기, 개별 strict 사용)

## §5. 미해결·다음 작업
1. **bio** = macro overlay 살아있음(us_10y_d -0.244 growth duration + xbi/ibb 상대모멘텀). composite로 power 보강 + tradeable≥2 판정 진행중. 완료 검수.
2. **refine** = 유가 mean-reversion 1개만 → 보강(정제가동률/marker margin/배당) or monitor-only 정직(과점 구조빈약).
3. **shipbuilding** = v2 REJECTED 유지(주가가 운임·신조선가 6-12M 선행=후행지표 부적합) → 보강(후판/수주점유/LNG선) or monitor-only 정직.
4. **financial** = loan_growth TENTATIVE only(term/credit spread는 측정 결과 확인) → tradeable<2면 보강.
5. **★통합** (rotation-analyst, 전12 완료 후): v2 STRONG 중 refine 가스오염 폐기 / steel·auto·battery·chem·telecom strict 사용. residual N_eff(공통인자 residualize 후 participation ratio) + sleeve clustering + 2층×3층 결합(L3 within-industry macro-neutral demean) + hierarchical sleeve-gatekeeping FDR + gated(default 0+hysteresis+cost). ★telecom flow=전산업 공통(L축 1회계상 주의).
6. **G-C 독립 audit** (author≠auditor, hard-fail B·C·D·I+M·N·O) → 사용자 confirm.

## §6. 자문 종합 (RESULTS 6대 + 교훈)
- (A) 신호 = macro backbone + 산업별 idiosyncratic-cycle alpha, momentum 강등 / (B) residual-PCA N_eff(개별12=false breadth, ~3-4) / (C) base=sleeve residual risk-parity + additive-on-active-share+clip tilt / (D) 자본=곱·L3 macro-neutral로 double-count 회피 / (E) hierarchical sleeve-gatekeeping FDR+program DSR / (F) DSR미생존=adequate-power null→0/low-power→decaying small-κ.
- ★universe 오염 교훈(이번 세션 발견): rotation-analyst v2 `load_industry`=디렉토리 전체 패널 → 부수종목 오염(정유 crack=가스9종). 개별 analyst strict 화이트리스트 재현으로 섹터별 검증: refine만 오염(폐기) / steel·auto·battery·chem·telecom strict=v2 일치(진짜).
- 36셀 collapse 100%(L2 rotation underpowered) → single-axis+partial-pooling 정당. residual N_eff raw3.02→3.51.
