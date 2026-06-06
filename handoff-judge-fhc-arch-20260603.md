---
tags: [handoff, inv, judge, fhc, architecture]
date: 2026-06-03
session: btn-Inv
plan: plan-judge-report-arch.md
progress: progress-judge-report-arch.md
consult-ssot: .consult-judge-report-RESULTS.md
next-action: "button(주식 S6) 회신 확인 → S2 mediator 합류 가능 여부 판정. 단독 진행 시 = 코인 Markov ex-ante 또는 core 정교화(reject_recovery 트리거 통합). ⛔ S2/S4/S5 = button RegimeGlasso 합류 + go-live 게이트 선결로 단독 불가."
---

# Handoff — judge 재설계 + 리서치 통합 의사결정 아키텍처 (FHC)

> 이 파일만 읽고 재개 가능하게 작성. 대화 로그 없이 §1부터 진행.
> ⛔ go-live = 사람 게이트. push 금지. 결정론 코어·risk_gate 상수 무수정(오버레이만 additive).

## §1. 현재 상태 + 첫 행동

**한 줄**: "결정론 위에 Claude를 배치하는" 설계 = **FHC(Falsifiable Hypothesis Card) 아키텍처**. 5R 자문(gemini+claude) 수렴 완료(`design-confirmed`), **자산무관 core 3모듈 빌드+회귀 전부 닫힘**(63 passed). 나머지 단계(S2/S4/S5)는 button(주식 세션) 합류 + go-live 게이트가 선결이라 대기.

**현재 완료**:
- S0 결정론 baseline(judge off) ✅ — coin 단일자산, on≫off로 "코드결함" 가설 역전(손실원=SMA whipsaw 방법론, 코드 사이징은 방어 오버레이). INV-11 off=byte-identical 기준선 확보.
- S1 FHC 안전 인프라 ✅ `core/assume/fhc.py`(FHCard·5-state·2-leg mediator·_DirectionalE 단측 e-process).
- S3a breaker + fail-closed ✅ / S3b bonus emission((B)강화: L1 초과·천장C cap) ✅ `core/assume/bonus_channel.py`.
- INV-12 FDR firewall ✅ `core/assume/fhc_fdr.py`(per-layer ELOND·고정분할). **2026-06-03 `pytest tests/assume/ → 63 passed` 회귀 편입 완결**.

**첫 행동 (택1)**:
1. `bash ~/.claude/scripts/lib/psmux-send.sh ...`로 btn-button 진행 확인 → RegimeGlasso/exposure card 합류 가능하면 **S2 mediator wiring** 착수(state-space filtered-only 구독).
2. button 미회신 시 단독 잔여: **코인 Markov coupling-state ex-ante 레짐**(macro_vol_transfer 승격 마지막 관문, 별 트랙) 또는 **core 정교화**(reject_recovery 트리거를 FHC transition에 통합, _DirectionalE 정밀화).
3. 사용자가 커밋 지시 시 = ssr 정정 + FHC core 3모듈을 분리 커밋(push 금지).

## §2. 진행맵 (S0~S6, RESULTS C14)

| 단계 | 상태 | 산출/블록 |
|---|---|---|
| S0 결정론 baseline(judge off) | ✅ | `.p2-test2a.py`, coin baseline. substrate on variant=button 연결 후 |
| S1 FHC 안전 인프라 | ✅ | `core/assume/fhc.py` (self-test 10/10) |
| S2 mediator wiring | ⏸ **블록** | study state-space = button RegimeGlasso 공유, button 진행 후 |
| S3a breaker+fail-closed | ✅ | `bonus_channel.py` breaker_tripped + fail-closed |
| S3b bonus emission | ✅ | `bonus_channel.py` size_with_bonus·AssetSizing (self-test 7/7) |
| INV-12 FDR firewall | ✅ | `core/assume/fhc_fdr.py` (63 passed 편입) |
| S4 능동 애널리스트 루프(7-step) | ⏳ | go-live 경계(LLM 소환). 존재이유=C9 6유형 |
| S5 리서치 통합(2-stage RAG) | ⏳ | VaultVoice BGE/LanceDB 재사용, go-live |
| S6 종목 바스켓(KIS) | → button | 룰코어 스크린+딥모델 비교선택+메타카드 |

**매 단계 게이트** = INV-11(off byte-identical 무회귀) + INV-3(fault-injection fail-closed).

## §3. 사용자 박제 (대화 고유 framing)

- **핵심 의도**: 결정론 코어(L1 risk_gate·DCF·BL) 위에 Claude 최종판단을 얹되, **down-only 감쇠기**에 머물던 LLM 레이어를 **반증생존 카드에 한해 천장까지 강화(陽, L1 초과)** 허용하는 actuator로 전환. "강화 flag" 의도 = (B)안 채택(C3).
- **거시=현 세션(btn-Inv) / 주식 구현=button 세션**(동일 FHC 틀 공유, C15). btn-Inv가 `core/assume/` FHC core **단일 소유**(사용자 "주식 리서치 한세월이니 너가 먼저"). button=core 짓지 말 것 + 산업 리서치 계속 + 나중 bonus API plug-in. button 회신 "정렬 동의·2벌 회피 합의" 받음.
- **go-live = 전 구간 사람 게이트**. coin bot부터 incremental arming → 종목 바스켓(KIS) 최후. push 금지. 결정론·risk_gate 상수 무수정.
- **plan-test-readiness P3(judge)/P5(리포트)는 본 plan으로 흡수**(과소명세 정정).

## §4. 파일 inventory (절대경로)

**core 산출(완료, additive·호출처 0)**:
- `D:\projects\Inv\core\assume\fhc.py` — S1, FHCard/FHCState·eval_mediator·update_outcome·bonus_from_evalue·transition(5-state)·_DirectionalE
- `D:\projects\Inv\core\assume\bonus_channel.py` — S3, size_with_bonus·AssetSizing·breaker
- `D:\projects\Inv\core\assume\fhc_fdr.py` — INV-12, FDRFirewall·_layer_of·test_confirm·per-layer ELOND
- `D:\projects\Inv\tests\assume\test_fhc_core.py` (+ fhc_fdr 5 케이스) — 63 passed

**재사용 기존 인프라(2벌 회피, 작성 전 Read 필수)**:
- `core/assume/reject_recovery.py`(IC9 부활: RejectClass·evaluate_recovery·ChatterBackoff) / `core/assume/graduation.py`(5-AND=confirm 전이) / `core/assume/weight_falsification.py`(e-CUSUM kill=outcome reject leg) / `core/structure/online_fdr.py`(LORD++) / `core/structure/eprocess_backbone.py`(ELOND·e-value) / `core/structure/hierarchical_fdr.py`(sector sub-family) / `core/assume/card_contract.py`(AssumptionCardLike Protocol)

**설계·자문 문서**:
- `plan-judge-report-arch.md`(구현 명세) / `progress-judge-report-arch.md`(진행) / `.consult-judge-report-RESULTS.md`(자문 SSOT C1~C16) / `.gemini-web-last.md` / `.claude-web-basic-last.md`

**조율 문서(button 계약)**:
- `.coord-macro-stock-fhc-20260603.md`(겹침 5구역 매핑) / `.coord-fhc-contract-20260603.md`(단일 FHC 계약 §2 schema·§3 5-state·§4 bonus API·§5 INV)

## §5. 미해결 · 실패한 시도 (삽질 방지)

- **S2/S4/S5 = button 블록**: 단독 진행 불가(RegimeGlasso 공유 + go-live 게이트). button 회신·합류 전 착수 금지 — 2벌 구현 위험.
- **_DirectionalE 단측 e-process**: 양측 MixtureSPRTEProcess는 2-leg(vacate≠reject)에 부적합 → 단측으로 정정함(설계 확정). 양측으로 되돌리지 말 것.
- **harness2 야간 미감독 위험**: S1/S3는 harness2 계획이었으나 direct opus 빌드로 전환(야간 ctx 보존 + 신규 additive + INV-11 자명). S4/S5는 harness2 유지.
- ~~**코인 Markov ex-ante(별 트랙)**: macro_vol_transfer candidate 승격 마지막 관문 = 달력컷 E3를 관측 레짐(Markov coupling-state/CME OI)으로 대체.~~ **STATUS: resolved (2026-06-04) — ex-ante Markov 경로 닫힘**(.p2-m4-voltransfer-markov.py): VIX 2-state Markov 3방식 전부 degenerate·수렴실패 + VIX 분위수 split이 stress-조건화 가설 반증(신호는 calm-VIX서 발생, 극단 stress서 소멸 = throttle 메커니즘 spec↔실측 drift). candidate 유지(structural-prior tier, bw=0). 승격 잔여 = CME OI/기관보유(데이터게이트) 또는 2022+ 시대전환 구조 인정뿐. ledger 박제 완료.
- **커밋 미실행**: working tree에 ssr 정정 + FHC core 3모듈 + reserve parquet(cron 자동) 혼재. equity 세션 변경과 섞이지 않게 분리 커밋 필요(사용자 게이트). push 금지.

**미서명 Open items (plan §5, S3b/S5 구현 시 [측정] 대상)**:
- **τ_in/τ_out 구체 수치** + cost gate turnover 비용 모델 소스(실측 슬리피지 vs 가정) — C11 whipsaw dead-band 파라미터 미확정.
- **realized_bonus e→bonus map 곡률** per-card-type 확장(현 base=단일 곡선) — S3b bonus emission monotone map.
- **bonus baseline 초과 = (B) 확정**(사용자 의도)이나, **천장 C 독립산출 4조건(RESULTS C5) 구현 시 증명 의무** — C가 bonus/judge와 진짜 독립·PIT-safe임을 코드로 입증 안 하면 INV-1 hard cap 무효.
- **FHC 명칭 정리**: S1="안전 인프라"(safety machine) / "FDR Hierarchy Controller"는 S3b·S5 내부 — 두 개념 혼용 금지.
- ~~**core 정교화 잔여**(btn-Inv 단독 가능): reject_recovery.py 트리거(IC9 부활)를 FHC transition revive 경로에 통합 + _DirectionalE episode-LOO 정밀화.~~ **STATUS: resolved (2026-06-04)** — `transition(chatter_backoff=, now_tick=, require_loo_robust=)` opt-in 주입 완료. `_DirectionalE.e_value_loo`+`FHCState.e_value_loo` 노출. tests/assume **67 passed**(63+4), None/False fallback byte-identical 입증. ckpt-202606040XXX 참조.

## §6. 자문 종합 (RESULTS C1~C16 핵심)

> SSOT = `.consult-judge-report-RESULTS.md`. plan §1 = D1~D11이 C1~C12 매핑.

### §6.0 정보파이프라인 자문 (2026-06-04, gemini-web+claude-web 병렬 1R 수렴)
> raw = `.gemini-web-last.md` / `.claude-web-basic-last.md`. plan §3 S4/S5 반영. 대상 = S5 리서치 통합 정보파이프라인(리포트→RAG→발권) 세부. **한 원칙 수렴: "텍스트는 가설 생성만, 잔차 수익률 공간이 가설을 판정"**.
- **Q2 호출빈도(★최강 공통 권고, 현 설계 약한고리)**: "daily batch" **폐기** → ①수집·인덱싱=상시 ②가설 생성=시계 아닌 **정보델타(retrieval 임베딩 novelty 임계초과) 트리거**(안 바뀌면 standing hypothesis) ③승격·사이징=의사결정주기(주/국면)+e-value, **up 지연/down 즉시 비대칭**(down-only 정합) ④이벤트=가격점프 OR 정보신규성 dual-key. 효과=유령회전 제거 + FDR(LORD++ α-spending) 절약 + 비용절감 3마리. ★**재검토 정정(2026-06-06)**: 순수 델타 트리거는 빈도 상한 없음(새 글마다 임베딩 거리 미세차 → 게이트 계속 통과 → daily보다 발권 폭증 가능). → **시계 rate-cap(상한) AND 델타 게이트(빈 슬롯 skip) 결합**(batch=폐기 아닌 상한 유지). '주간배치↔임계값'=다른 축(시계 vs 이벤트), 직전 설명 오류 정정. 자문 무비판 수용 교정.
- **Q1 리포트 편향**: 별도모듈 X → 불변식 흡수. level 금지·surprise/revision만 / **한국 매도희소→down-only 매핑**(희소 Sell=정보 비대칭 큼) / 톤 2회 디민(애널리스트 FE + 횡단면) / 선반영=발간 CAR통제+bitemporal PIT(RAG stale 누수 차단) / **잔차 톤**(감성에서 과거수익·변동성 설명분 회귀제거, gemini 대안2=Ke-Kelly-Xiu 2019, 2단계 도입). Loughran-McDonald 2011·Michaely-Womack 1999·Womack 1996·Easterwood-Nutt 1999.
- **Q3 직교성 발권게이트**: 텍스트 신규성 믿지 말고 스패닝 회귀 r_c=α+βᵀF+ε → **"잔차공간 α≠0 못 보이면 가설 아님"**(MOVE⊥VIX 흡수 공식화). 국면 interaction(무조건부0/조건부 알파=최고가치, regime conditional-IC 정합) + 팩터타이밍 vs 종목선택 분해. GRS 1989·Kelly-Pruitt-Su 2019. ★두 모델 분기(보완)=claude 생성단 발권게이트 / gemini 1순위 사이징단 팩터중립 옵티마이저 제약(양립, bonus_channel 옵션).
- ★사용자 논의(대부분 기존 설계 일치): 정보소스 정량(EDGAR/pykrx)+정성(리포트 RAG) / 카드 3겹 기준(사전 study룰+정성 촉매+사후 e-value) / 7팩터=바닥좌표계 vs HBM류=잔차 테마. 사용자 RAG 구상=S5 수렴.


- **C1 primitive=FHC**: LLM은 카드 mint(발권)만, 미등록 카드=사이징 영향 0.
- **C2 2-leg**: mediator vacate(전제 미성립→보너스 회수·보류) ≠ outcome reject(전제성립·무수익→영구근접).
- **C3 (B)강화**: L1 초과 가능, 천장 C가 hard cap(신규 파라미터 0). 진짜 불변식 = capital-at-risk ≤ C.
- **C4 5중봉인**: 확정카드 / 천장cap / 시간감쇠 / 게이트하위 / regime-primary breaker.
- **C5 confidence 방화벽**: self-conf→attention만 / e-value→capital. gate=AND, size=log-additive.
- **C6 종목 가치평가**(사용자 핵심 refinement): 룰코어 분산바스켓 스크린 → 딥모델 **비교선택**(ordinal, 바스켓 틸트 카드). universe 밖 종목 못 끌어옴(스크린 통과분 내 상대 비중만). = S6(button).
- **C7 메타카드 vs 바스켓카드 2-leg**: 메타카드=시변 지표중요도(upstream 스크린 성형) / 바스켓카드=downstream tilt. 원장 분리 + alpha-wealth 고정분할.
- **C8 리서치 통합 = 2-stage**: 매일 카드발권 LLM + 임베딩검색 RAG(VaultVoice BGE/LanceDB 재사용). grep=fallback. ⛔별도 consensus 엔진 금지. = S5.
- **C9 결정론이 못 푸는 6유형**(LLM 우위 유일 영역, S4 존재이유): ①regime-break 구조모델 무효 ②value-trap 판별 ③cross-source 합성 ④신규 가설 생성 ⑤이산 이벤트 ⑥instrument 선택.
- **C10 mediator state-space 구독**: study room posterior를 mediator gate가 직접 구독(DRY). ①**filtered-only**(smoother=look-ahead 금지) ②versioned(모델 bump=[측정]-gated 재검증) ③point estimate 아닌 **posterior covariance/entropy 노출**(저신뢰 트리거용). = S2.
- **C11 whipsaw = evidence-gated**(달력 기각): τ_in/τ_out dead-band hysteresis + cost gate(turnover 비용 못 갚는 미세 IC 금지) + min dwell backstop. turnover 예산 분리(메타=universe 느리게 / 바스켓 tilt=잦게).
- **C12 alpha-wealth 분배 = INV-12**: meta↔basket **고정분할 firewall**(cross-boundary transfer 금지 = confirmation-cascade 통로 차단). LORD++ 동적은 layer 내부만(basket=sequential stream, meta=작은 고정 reserve).
- **D4 headroom**: per-asset headroom = (C−L1). 전역 풀 기각(BL 이중배분 방지).
- **C13 INV-1..16** (load-bearing core = **INV-1·3·11·16**):
  - INV-1 Hard cap(w_final ≤ C, C는 bonus 독립·PIT-safe) ★top
  - INV-3 Fail-closed(오류/staleness/desync/breaker → bonus=0, w→L1 이하) ★core
  - INV-11 Deterministic replayability(judge/bonus OFF=byte-identical) ★전단계 회귀 게이트
  - INV-16 Monotone safety authority(감소=무승인 자동, 증가만 human-gate) ★메타-불변식
  - (그 외: INV-2 no-leverage·4 bounded augmentation·5 confirmed-only·6 time-decay·7 gate-subordinate·8 recall IOC·9 regime breaker·10 PIT·12 FDR firewall·13 pre-mint 반대증거·14 backtest-divergence human gate·15 mediator 2PC)
- **C16 최종 변환 한 문장**: 기존(L1=침범불가 천장 + consensus=미배선 순수 감산 damper)을 → L1=보수 movable anchor·독립천장 C=진짜 불변식·그 아래 확정/반증생존 카드만 e-value비례·시간감쇠·게이트하위·즉시회수·regime breaker **5겹 우리에 갇혀 양의 확신을 천장까지 표현하는 load-bearing actuator**로 전환. 안전보증 = "모델은 절대 상향 override 불가"(강하지만 signal 버림) → "capital-at-risk ≤ 독립천장 + 모든 상향은 가역·감쇠·증거한정·fail-closed".
