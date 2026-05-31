---
tags: [type/tracker, domain/study-orchestration, owner/main-btn-Codlearn]
date: 2026-05-30
purpose: main(btn-Codlearn)이 각 세션에 내린 dispatch·지시 현황판. 누락·중복 추적용. 지시마다 갱신.
---

# DISPATCH-TRACKER — main 세션별 지시 현황판

> ★매 dispatch·회신마다 이 표를 갱신한다. 상태 = `진행중` / `완료` / `HOLD` / `대기(회신)` / `오판-정정`.
> 세션↔study 매핑: button=macro / common-task=eq_us_cyclical / DA=eq_us_defensive / diary=eq_kr / excel=eq_intl / GCP=reit / jpdf=commodity / jsh86=gold / powerbi=bond_cash / profile=crypto(원래).

## 1. 현재 활성 dispatch (2026-05-30)

| # | 세션 | study_id | main 최근 지시 | 상태 | 마지막 회신 | 다음 액션(main) |
|---|---|---|---|---|---|---|
| D1 | btn-diary | eq_kr | 방법론+원본프롬프트 main 전송 요청 | ✅완료 | "요청 2건 처리 완료" (methodology-final + original-user-prompts 박제) | eq_kr 12산업 자문/dispatch 자율 — 모니터링 |
| D2 | btn-profile | crypto(복귀) | eq_us 오판→crypto 복귀 | ✅**crypto 완료·감사대기** | "2-3 검증+yaml v2(302줄)+8축 완료, 합성0(CoinMetrics/Binance/FGI/DefiLlama 실수집), H2 funding ★REJECT 부호반전, H3 stablecoin reflexive sharpe-0.43, prior ladder 역방향 재캘리(on-chain1.27>micro0.97>stable-0.43)" | ★main 12축 background 감사 진행중 |
| D3 | btn-GCP | reit | v2 baseline 적용 → HOLD → 해제 | 🔄진행중 | "M3 verdict 대기 idle 맞음, baseline 재사용. HOLD 해제 ack" | direction.md 도착 시 승인 게이트 |
| D4 | btn-powerbi | bond_cash | v2 baseline 적용 → HOLD | ⏸️대기(회신) | (HOLD 보냄, idle 여부 회신 대기) | 회신 보고 idle이면 baseline 재개 |
| D5 | **eq_us** | eq_us(jpdf 슬롯) | MAIN-DISPATCH.md → jpdf 전환 | ✅**안착 확인(capture 검증)** | jpdf /clear→idle(resume inject 실패)→main 재전송→capture: MAIN-DISPATCH+handoff Read, 6 SSOT 병렬정독, Phase3 TaskCreate, 작업중 | direction.md 산출 보고 시 승인 게이트 |

## 2. 이전 단계 지시 (M1~M6, 회신 수령분)

| # | 세션 | 지시 | 상태 | 비고 |
|---|---|---|---|---|
| P1 | btn-button | M1 거시 이벤트·지표 요약 | ✅완료 | 전 세션 배포 완료(M2) |
| P2 | btn-common-task | M6 산업×regime δ 매트릭스(경기민감 4산업) | 🔄진행중 | capture: "2/4 agents done" — busy |
| P3 | btn-DA | M3 보수(합성 의심 재검증) | 🔄진행중 | bugfix v3, ctx 468k 한계 |
| P4 | btn-excel | M3 보수(eq_intl) | 🔄진행중(추정) | Bonferroni 12/12 박제, em_china P1 |
| P5 | btn-jpdf | M3 보수(commodity) | ⏳register 대기 | rule 생성+register 가능 회신, **main이 register 미처리** |
| P6 | btn-jsh86 | M3(gold) | 🔄**미완(정정)** | ★capture: M3 완료했으나 4 open(H5/H8·yaml v2·8축 audit) = 큐 有 → eq_us 부적합 |

## 3. main 자체 track (study-system progress)

| # | 항목 | 상태 |
|---|---|---|
| M4 | 거시-종목 factor 통합(factor_betas_seed/cov_estimate/shadow) | ✅완료 |
| M5 | factor Phase A(vol) + risk gate wiring helper | ✅helper 완료, 실배선=사용자 게이트 보류 |
| M6 | 주식 sleeve 산업×regime(세션 위임) | 🔄세션 진행중 |

## 4. ★미해결·누락 위험 (점검)

1. **D5 eq_us 재배정** — profile 오판 회수, 진짜 idle 방 미확정. 자산군 방 모두 작업 큐 있음(§5 P0~P2) → 조건부 dispatch(세션 자기판단 수락/거절)로 profile 재발 방지.
2. **D4 bond_cash HOLD 회신** — idle 여부 미확인. 회신 도착 시 처리.
3. **P5 commodity register** — jpdf "register 가능" 회신했으나 main이 register 미실행. 처리 필요.
4. **capture=화면 idle ≠ 작업 큐 없음** — profile 오판 근본 원인. 이후 idle 판단은 **세션 회신**으로 확정(capture 단독 금지).

## 5. 갱신 로그

- 2026-05-30: 초기 생성. D1~D5 + P1~P6 박제. eq_us 재배정 PENDING.
- 2026-05-30: ★pane capture 검증(사용자 지시). gold(jsh86)=M3 완료여도 4 open(H5/H8·yaml v2·8축) 발견 → 내 "충실 완료" 판단 **오류 정정**, eq_us 부적합. commodity(jpdf)=M3 4단계 완결 후 idle(open task 패널 0) 확인 → eq_us 조건부 dispatch(jpdf, 수락/거절 자기판단). 교훈=capture 화면+task 패널 교차 확인이 idle 판단의 근거(빈 프롬프트 단독 금지).
- 2026-05-31: ★주식 고도화 중단(subagent 장애)→stock.md 재개세트. 누락지표 study→코드화 dispatch: macro(HY OAS+real_rate 커밋 fabda53, dollar/oil 보류)·gold(CFTC+실질금리 디커플링)·reit(이미포함)·eq_kr(산출 저장)·commodity(China impulse main 직접 완료). pane 대조 11/11. killable=DA/jpdf/profile/button.

## 6. ★누락지표 추가 → 종목별 12축 audit (사용자 지시 2026-05-31)

> 규칙: 누락지표 추가는 **종목별 완료마다 실데이터 상관관계가 실제로 맞는지 12축 audit**(기준=일반 study와 동일, AUDIT-GUIDE.md). 별도 opus subagent 위임(supervisor 직접평가 금지).

| 종목 | 추가 지표 | 추가 상태 | audit 상태 |
|---|---|---|---|
| commodity | china_credit_impulse_z | ✅ 완료(실측 비유의→structural 격하) | ✅ **충실**(재실행 bit-identical, 비유의 격하 정직 확인, Hard-fail 0). 보강2 적용(hook affects 필드 + PIT note) |
| eq_intl | DM/EM dollar β archetype + JGB-UST + ToT | ✅ 완료(yaml 갱신) | 🔄 audit subagent 실행중 |
| macro | HY OAS + real_rate (regime classifier) | ✅ 커밋 fabda53(dollar/oil 보류) | ✅ **부분**(append-only·Fisher 회피·보류정직 충실 / 활성2종 regime-OOS 미검증=factor-beta prior로만 정당화, 비대칭 1건). 보강3 macro 전달(비대칭 라벨/hook wire/base_weight 라벨). Hard-fail 0 |
| macro(후속) | vol/VIX (실현변동성 대용→실 VIXCLS) | ⏳ factor 직교검증✓(VIF 1.00)·M5 factor placeholder(β=None HOLD) / 분류기 미투입·실 collector 미적재 | ⏳ 사용자 go-ahead 후 study→code→audit (dollar/oil과 같은 OOS 게이트) |
| gold | CFTC speculative + 실질금리 디커플링 | 🔄 study 진행중 | ⏳ 완료 시 audit |
| bond_cash | MOVE + ACM term premium | 🔄 v2 진행중 | ⏳ 완료 시 audit |
| reit | (2항목 이미 포함) | ✅ 기존 yaml 포함 | ⏳ v2 Phase6 audit서 확인 |
