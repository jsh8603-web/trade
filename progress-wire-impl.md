---
tags: [type/progress, domain/inv, topic/study-wire-impl, session/btn-Inv]
date: 2026-06-01
scope: study 산출 → 런타임 wire 실제 구현 (R9 수렴 IC1~IC8 코드화). 설계 SSOT=CONSULT-DECISIONS-wire-20260601.md §11/§12.
push: ⛔ 금지 (로컬 commit만)
model: opus (전 step — 설계 판단 포함 wiring)
gate: 각 IC = ① 지표 실데이터 시뮬 에러 0 ② opt-in off byte-identical 회귀(test_study_pipeline.py:58, test_sleeve_belief_cov.py:150) ③ 회귀 증거 기록
---

> 인계: [handoff-wire-impl-20260601.md](./handoff-wire-impl-20260601.md) (최신, IC10 measured + judge gap + 잔여 Track1/2) · [handoff-wire-process-20260601.md](./handoff-wire-process-20260601.md) (이전, 공정 재정립)
> [ckpt-202606012015:btn-Inv] 받아적기 정정 + 공정 P1~P5 SSOT + 누락검토 subagent(ae5e718a) 완료. framing=cross+regime 동적corr(agent전 배분레이어)·judge(부차). ★subagent 누락①②(cross 자산자문·regime 정의 자문)=**오판**, 이미 decisions §1.3/§1.4 + cross-and-regime-research 반영(철회, R13 게이트 불요). ★진짜 잔여 누락 3건=③ R12에 "자문 발사 전 자문대상 사용자 보고·승인" ④ P2에 "15축 요약카드 산출물(파일경로·hard축)" ⑤ P3↔judge "채택분 누락0 점검". 반영 완료 후 P4 IC0-R(coin_track_macro substrate=RegimeClassifier+build_sleeve_regime_ids→allocate). 진입=handoff §7. (★1M 컨텍스트=압축 강박 무시, hook 480k 경고=long-mode cap 기준일 뿐) ★IC0-R codify 완료(coin_track_macro substrate, off byte-identical, 회귀 446). ★★P1~P3 완료(2026-06-01 사용자 'ㄱㄱ' 실행, 단계 정정 거침): P1 1차(top5 한 agent)→**P1 재작업 2분할**(a03cf09f cross / a7d149b4 regime+crypto = 실측 완비·defensive 보충·crypto raw 재계산)→**독립 P2 audit 2분할**(a2c6af3b cross / a7c55f08 regime+crypto = 측정자와 **별도 감사관** raw 재현, 통과편향 차단)→**P3 ledger 확정**(study-research/_wire/cross-regime-ledger.md). ★단계 오류 정정: 처음 P2a/P2b 를 audit 라 라벨했으나 실제=P1 재작업(자기측정·자기판정=self-cert), 독립 audit 은 별도 감사관 2명 재발사. verdict: cross **충실 CONFIRMED hard-fail 0**(8 cross+defensive vol β=−0.66 adopted)·**DGORDER→XLE confirm adopted**(judge L2 down-only refinement)·**crypto INSUFFICIENT 보류**(B·C 2축 hard-fail, yaml 5건 정정 게이트)·financialization **UNTESTED**(yaml object mismatch)·**gold vol β:=0 lock**(NW-HAC p=0.077 비유의, 오염방어)·C7 hedge **reject**(tail서도 +0.29 동조). 산출=15axis-summary.md+cross-regime-ledger.md. ★L축 불변=VIX 1회 계상(SEED vol factor only, VIX-regime 별도 wire 금지). 다음=**P4 codify=IC10**. ★P4 방향 확정(사용자 2026-06-01): **shadow 운영 폐기 + magnitude 측정 판단**(magnitude FREEZE=small-n n<30 한정으로 좁힘, cross large-n batch β 측정 박제 OK). IC10 신설=adopted 9건→측정(sign+magnitude)→(a)SEED vol/oil/dollar cell 측정 magnitude(`factor_betas_seed.py SEED_CELLS`, NW-HAC, gold vol β:=0 lock)+(b)SLEEVE_AGG 매핑 확장(`regime_to_weights SLEEVE_AGG`+`sleeve_returns SLEEVE_TICKERS` reit/eq_intl/xle/defensive, ★배분차원=회귀민감)+(c)gold lock+(d)DGORDER judge L2. 관문=(a)(c)(d)자율·(b)배분차원 회귀점검. crypto=small-n UNKNOWN(yaml 5건 정정 후 IC9 복귀). IC10 ✅**(a)(c) 완료**: SEED batch multivariate measured 전면 교체(M3 등급값 폐기) + ★gold decoupling 발현(gold vol β:=0 reject → us_stock×gold corr 0.53→0.08) + measured-vs-yaml 검증(subagent: 충돌 0, 용도차 — SEED mv=corr_prior 직교분해용 / yaml=단일자산 univariate 해석, reit yaml W4 caveat) + 회귀 35<37 baseline. ⛔(b)=배분 구조 게이트(reit/eq_intl/xle 배분 sleeve 부재, 신규 추가=사용자 방향) / (d)=judge go-live 경계 / crypto=small-n UNKNOWN(yaml 5건 정정 후 IC9). ★사용자 최우선(agent 전 배분 레이어 measured 상관)=(a)(c)로 달성. P5 라이브=게이트.

# progress — study→wire 구현 (IC1~IC8, R9 수렴 코드화)

> 원칙: 신규 글루만 작성, 기존 메커니즘(eb_shrink·RegimeGlasso·James-Stein·5-AND·e-process·two-layer·facade·회귀테스트) 재사용. opt-in off=byte-identical. execute_trade SACRED 비접촉. go-live 경계(judge 소비·실거래) = 사용자 게이트, 범위 밖.
> SSOT: CONSULT-DECISIONS-wire-20260601.md §11(IC 결선) + §12(audit 15축). 코드맵 §8.

## ★합의 방향 (사용자 2026-06-01 정정 — 최상위 원칙)
> **ledger 통과(채택) 지표 + cross relationship 은 모두 agent(judge L2 qwen / L3 bge) 개입 전, 자동 코드 계산 배분 레이어에서 동작해야 한다.** 여기서 상관계수가 regime(국면) 따라 **동적으로 변하며 자동 산출**(RegimeClassifier→belief b(t)→RegimeGlasso regime별 학습+belief-mix→동적 Σ_eff→corr_prior). judge qwen/bge 는 그 *이후* down-only attenuator(부차 레이어).
>
> ★우선순위 정정: **agent 전 자동 경로(regime 동적 corr + 채택지표 weight 자동계산) 완성이 최우선**. judge qwen lens(구 W8)는 agent 레이어라 후순위 — main 이 framing 이탈했던 지점(2026-06-01).
> ★불변: ledger(채택/기각/후보+사유+리서치 링크)에서 **통과(채택)** 판정된 지표는 예외 없이 agent 전 자동 계산 단계에 반영돼 동작 (yaml 에만 있고 런타임 미동작 = 미완).

## ★P4 통합 방향 확정 (사용자 2026-06-01 — shadow 폐기 + magnitude 측정)
> 내가 제시한 3 갈래(sign-only / SLEEVE_AGG 매핑 / magnitude)를 **하나의 경로로 묶음**. 사용자 결정 2건:
> 1. **★shadow 운영 폐기**: 영구 shadow tier 로 미루지 않는다. adopted 관계는 **측정으로 즉시 activate/reject 결판**(large-n) 또는 **UNKNOWN 정직 라벨**(small-n). working facade 위장(작동 중인 척 대기) 금지. decisions §1.5/§2 "영구 shadow=회피" 와 정합.
> 2. **★magnitude = 측정으로 판단**: SEED cell β magnitude 를 shadow OOS population 으로 *키우지 않고*, **batch β large-n 실측(n≈5052 daily, NW-HAC SE/CI 동반)** 으로 박제. ★magnitude FREEZE 원칙은 **small-n(n<30) 한정**으로 좁힘 — cross large-n 은 측정 magnitude 박제 가능. crypto 등 small-n(eff_n<30)만 UNKNOWN/FREEZE.
> **→ 단일 경로**: adopted → 측정(sign + magnitude 둘 다) → SEED cell + SLEEVE_AGG 매핑 → corr_prior → 배분 레이어 자동 동작. shadow 대기 단계 제거. opt-in off byte-identical 유지.
> **L축 불변**: VIX(vol) 공통인자는 SEED vol factor **1회만** 계상. VIX-regime 별도 wire 금지(독립 audit 적발).
> **회귀 민감**: SLEEVE_AGG 매핑 확장 = 배분 % 자체 변경 → 매 변경 off byte-identical + on PSD + 신호이상 0 점검 의무.

## ★사용자 요구 충족 공정 (SSOT — 압축내성, 2026-06-01 논의 종합)
> 요구 = ledger 통과(채택) 지표 전부 **agent 개입 전 자동 배분 레이어**서 **regime 동적 corr** 로 동작. 공정 5단계 + ★손보는 곳(파일:함수).

**P1. 지표 도출(실측)** — 현황: 자산↔factor std β **실측됨**(`_factor_shadow/batch-std-beta-5sleeve` n=5052 same-day) / 자산↔자산 cross=**추론 후보**(`_wire/cross-and-regime-research` C1~C12) / 국면별=**PoC 1**(DGORDER→XLE).
  ★손보는 곳: `study-research/_factor_shadow/*.py` (batch β 확장: 자산↔자산 cross 직접실측 or factor추론 검증 + regime split 실측 스크립트). 신규 측정 작업.

> **★P1 subagent 작업 지시 템플릿 (cross/국면별 상관 검토 — 필요시 스폰, 사용자 2026-06-01 명시. 밑바닥 금지=기존 리서치 제공)**
> **입력 제공** (subagent-spawn-existing-research 원칙): (a) batch std β `_factor_shadow/batch-std-beta-5sleeve`(5sleeve×5factor n=5052 same-day) (b) cross 후보 `_wire/cross-and-regime-research`(C1~C12 + regime 정의표) (c) yaml relationships/weight_rules(블록3/4) × 8자산 (d) 15축 기준 `decisions §12` + `study-research/AUDIT-GUIDE.md`.
> **작업**: ① cross/국면별 상관 실측 검토(자산↔자산 직접 or factor 추론 검증, regime split = expanding-median PIT-safe) ② ★**코드 반영 계획(어디 손보는지 — 누락 금지)**: SEED vol cell(`factor_betas_seed.py:84`)? relationships→corr_prior 변환 경로? regime split substrate? **파일:함수:변경** 명시 ③ ★**15축 근거 판정**: 각 관계를 15축(특히 N cross-PSD / O leakage / B 실데이터)으로 activate/reject/UNKNOWN + 축별 근거.
> **출력 템플릿(채워 반환)**:
> ```
> | 관계(node_a↔node_b) | 채널(cross/regime) | 실측값[95%CI, n] | 코드 반영(파일:함수:어떻게) | 15축 판정(축별 근거) | verdict(activate/reject/UNKNOWN) |
> + 자산 요약: activate N/reject N/UNKNOWN N + n<30 hedge + PIT(naive vs live) 검증 + magnitude FREEZE 준수
> ```
> **금지**: 코드 직접 수정(main 몫), 밑바닥 재작업(기존 측정 위), self-certify(P2 audit 별도). magnitude 점추정 박제 금지.

**P2. audit(15축)** ← ★실측 도출 후 **의무**(사용자 2026-06-01). 12 study축(A~L) + 3 wire축(M wire충실/N cross PSD/O leakage), decisions §12.
  ★손보는 곳: 별도 opus subagent(self-certify 금지, P1 작성자와 독립) → 15축 평가 → 통과분만 P3 등록. (가)관문 = P1 15축 작성 → P2 15축 audit 평가 → 통과분 등록.
  ★**산출물(④ S0 명시)**: 15축 요약카드 = `study-research/_wire/15axis-summary.md`(decisions §12 압축본 — hard축 M wire충실/N cross-PSD/O leakage + B 실데이터/L 공통인자 필수 압축) 작성해 P1·P2 subagent 에 전달. 압축 후 §12 흩어짐 방지(subagent 지시 부실화 차단). ✅완료(2026-06-01 작성, P1 재작업·독립 audit 4 agent 전부 전달). ✅독립 audit 실행 완료(별도 감사관 2명, cross 충실 CONFIRMED hard-fail 0 / regime DGORDER confirm / crypto INSUFFICIENT 보류).
**P3. ledger 등록(통과분)** — 후보/채택/기각 + 사유 + 리서치 링크(재탐구 방지).
  ★손보는 곳: 신규 `core/study/indicator_ledger.py` `build_indicator_ledger(s)` → [{id, status(adopted/rejected/candidate), weight, reason, research_ref}] + `study_register.status()` 노출. ✅ **codify 완료(2026-06-01)**: `build_indicator_ledger`(adopted=weight_rules base_weight>0 / candidate=indicators만 / rejected=audit verdict 주입) + `ledger_summary`(카운트+adopted_ids 런타임 대조 기준). self-test PASS. + 8자산 통합 `study-research/_wire/indicator-ledger.md` 생성(adopted 71/candidate 54/rejected 0). + **CLAUDE.md "🗂️ 지표/관계 Ledger 기록 규칙" 박제**(4-state: adopted/candidate/rejected_provisional[보류·재평가]/rejected_permanent[영구폐기·class C], 갱신 의무 4시점). + **study_register.status() ledger 통합 ✅**(study_id→{adopted/candidate/rejected 카운트+adopted_ids}, 지연 import 순환회피, 22 passed). ★잔여: 영구/보류 실제 사유=P2 audit verdict 후 `rejected_ids` 주입(indicator_ledger.py — crypto 지표는 rejected_provisional 주입 대상) / cross-regime-ledger.md=✅**생성+독립 audit 확정**(2026-06-01: cross 8+DGORDER adopted / crypto·gold-hedge·gold-vol-β rejected_provisional 보류 / financialization·VIX-regime candidate) / 채택분 누락0 점검 wire(adopted_ids ↔ corr_prior/judge 대조)=P4 시.
  ★**채택분 누락0 점검(⑤ S0 명시)**: ledger adopted 지표가 (a) corr_prior/weight_card(배분, agent전) (b) judge lens_prompt(W2, bge/qwen) 코드경로에 **실제 반영됐는지 대조** — yaml adopted 인데 런타임 미반영 = 미완 플래그(yaml-runtime drift 감지).
**P4. codify(agent 전 자동 배분 레이어)** — opt-in off 무회귀:
  - corr_prior **부호**: ★**방향성 확정(2026-06-01)** — corr_prior=**sleeve 단위**, yaml 블록3 relationships=**indicator node 단위**(발견 D unit 불일치). 2-tier 라우팅: ① sleeve↔sleeve cross(`cross-and-regime-research` C1~C12, 자산쌍 factor 공유) → P2 audit 통과분 → corr_prior Σ off-diagonal **직접** 주입 ② indicator↔indicator relationships(블록3) → sleeve corr 직접 아님, **SEED betas factor 구조 경유**(`_ic_corr_prior`, IC1 이미). 코드 상세(주입 함수·sign 변환)=P2 audit 후 구현(자문 아닌 구현 영역).
  - corr_prior **크기**: ★`core/study/factor_betas_seed.py SEED_CELLS`에 batch β vol/oil/dollar cell 추가. magnitude=**측정 판단**(batch β large-n n≈5052 + NW-HAC SE/CI, ★**shadow population 폐기**). P2 audit 통과분(8 cross + defensive vol β=−0.66). gold vol=β:=0 lock(NW-HAC p=0.077 비유의). small-n(crypto eff_n<30)만 UNKNOWN 제외. magnitude FREEZE=small-n 한정으로 좁힘.
  - **regime 동적**: ★`core/coin_track_macro.py:60 collect_market_state`에 macro_view + sleeve_regime_ids 공급(=IC0-R). RegimeClassifier→classify + build_sleeve_regime_ids → allocate.
  - weight: `core/study/study_register.py:159 _build_card`(weight_rules→weight_card) = 됨.
**P5. 라이브 통합(Phase I)** ★go-live 게이트=사용자:
  ★손보는 곳: `CoinTrackWithMacro`→`agents/orchestrator.py`(run_agents 라이브) 연결. 현재 **테스트만** 인스턴스화.
**관문**: P2 통과=P3 등록자격 / P4=opt-in off 무회귀(자율) / P5=사용자 게이트. judge(qwen/bge L2/L3)=P4 후 agent 레이어 down-only **부차**(우선순위 역전 금지).
**세부 매핑**: P4=IC0-R·IC1~IC9·Phase W / P5 직전 자문=R12(목적=R12 섹션). 아래 IC/Phase/진단/흐름 = 본 공정 세부.

## ★현 동작 현황 (코드 전수확인 2026-06-01 — 받아적기 정정)
> **regime 동적 상관 = 현재 production 런타임 0 동작 (테스트에서만 산다).** 코드 사실:
> - 메커니즘 존재: `regime_to_weights`→`_belief_conditional_cov`→`RegimeGlasso(corr_prior=_ic_corr_prior)`→belief-mix Σ_eff→BL.
> - production `allocate` 호출 = `coin_track_macro.py:74` 단 1곳(나머지 tests). 거기 macro_view 無 → `allocate`가 `macro_view is None`(portfolio_orchestrator:168) → **`_fallback_hrp`로 regime_to_weights 자체 우회** → RegimeGlasso/corr_prior 진입 0.
> - ★`CoinTrackWithMacro`(배분 진입) 인스턴스화 = **전부 tests뿐**. `agents/orchestrator.py`(라이브 run_agents) 미연결 = progress.md 메인 **Phase I(통합 개통) 미완료** 영역.
> ★선결 정정: IC0-R(coin_track_macro 내부 substrate 공급)만으론 부족 — `CoinTrackWithMacro`→라이브(run_agents) 연결(Phase I)이 선결. coin_track_macro:74 고쳐도 그게 라이브에 안 불리면 무동작. wire=opt-in facade(default off) 설계라 의도적 미연결 상태였음.
> ★자문/decisions 누락: decisions=IC1(합성법)만, "라이브 통합·ledger통과 전부 agent전 자동" 일괄원칙 명시 약함(go-live로 미룸). 자문 raw=2레이어 구분만, 통합 주제 아님.
> ★decisions 방향성 정합 확인(2026-06-01): §1.1(judge=down-only read-only consumer / 단일카드→corr_prior view+lens view) + §1.2-1(static corr_prior=배분 WIRE) + §1.4(regime hardened-soft b(t) 동적) = **사용자 요구("채택 relationship→corr_prior 배분·agent전·regime동적=primary / judge=부차")와 정확히 정합**. main 이 W8(judge lens) 앞세운 건 우선순위 역전(decisions상으로도 judge=부차).

## 🔄 세션 운영 흐름 (compact/clear 기준 + 작업 배치, 사용자 2026-06-01)
**트리거 기준:**
- **compact(같은 세션)**: ctx warn + **같은 트랙 연속**(맥락 유지). 자율 코드 트랙=compact 로 이어감(judge gap·measured·shadow 폐기 맥락 보존). ★1M=자동압축 없음(long-mode cap 경고뿐) → 사용자 compact 지시 시 ckpt 박고 진행.
- **clear(새 세션)**: ① 주제 전환(자율 코드 → judge 재설계=claude 레이어 신규) ② 자율 트랙 일단락+핸드오프 완비 ③ framing drift 누적. clear=맥락 초기화라 핸드오프 md 필수.

**Track 1 — clear 전(compact 반복, 자율 코드):** IC8 FX 6th factor → IC4/IC9 **shadow-폐기 재조정**(graduation/reject-복귀 lifecycle 이 shadow 전제였음, "측정 즉시 결판"과 재설계) → Phase W1(defensive VIX·bond_cash v5 register)·W2(lag_routing 배선). opt-in off 무회귀, judge 무관=맥락 가벼움.

> ★compact후 조사(2026-06-01 Explore ag): **shadow tier 가 코드에 명시 상태로 없음**(운영 모드 개념일 뿐 — `factor_shadow.py`=순수함수 로깅만 / `study_register.status()`=adopted/candidate/rejected 3상태 / `update_controller.UpdateAction`=KEEP/RETIRE/TRANSITION/HUMAN_REVIEW, "SHADOW" 상태 없음). → "shadow 폐기"=폐기할 코드 거의 없음, **문서 모델 정정 위주**. Track 1 자율 코드가 게이트·큰설계·측정 의존에 대부분 막힘:
> - **IC8 placeholder 이상 불가**(코드근거 4): empirical(`sleeve_returns`)=USD ETF(EWY=FX섞임, "FX local-strip 후속" 주석 명시) / kr_stock=`SLEEVE_AGG` 미매핑(FX 주대상이 corr_prior 부재) / FX β measured 부재(batch 5factor만 → 새 측정=가관문 15축) / dollar(DTWEXBGS)↔USDKRW 공선(base currency KRW/USD 미결정). → **base currency 결정+측정 선행**(자율 범위 밖).
> - **IC4 graduation=이미 측정값 게이트**(`update_controller:99 step`→`hysteresis_and_gate` 5-AND: effect/fdr/dwell/k_window/same_regime). shadow population 통과 조건 아님 → shadow-폐기와 무관, owner 결선(누가 읽어 flip)만 신규=**go-live 인접**.
> - **IC9 reject 복귀=미구현 확정**(grep 0: E_for/reject_class/revival/re_risk). §14 설계만 존재. "재조정"이 아니라 **신규 인프라**(E_for 대칭 e-process + reject_class projection + RejectRecoveryGate + event_ledger 확장) = decisions §14 큰 설계 = **자문/사용자 방향 필요**(자율 막진행 부적합).
> - ★**자율 잔여 실질 = W1**(audit 충실분 register: defensive VIX risk-overlay·bond_cash v5)뿐. 나머지 전부 게이트/큰설계/측정.

**Track 2 — clear 후(새 세션, 큰 독립 주제):** judge 재설계 자문(claude 최종결정 레이어+qwen/bge 트리거+down-only 완화 여부+거시리포트/주식 묶음) → ★클로드 레이어 codify → **전체 테스트** → go-live(Phase I/P5). judge=claude 레이어 신규=깨끗 컨텍스트.

**현 위치**: ctx 457k 압축 임박 → 본 흐름 박제 후 **compact** → Track 1(IC8부터). 클로드+테스트는 Track 1 일단락 후 **clear**.

## 작업 흐름 (현→완성, 2026-06-01 합의)
**[현 위치]** 부품 메커니즘 대부분 완료 / 라이브 미연결(Phase I 미개통) → regime 동적 corr=테스트만 동작.
**[A. 자율 — opt-in off 무회귀, 라이브 무영향]**
1. IC0-R: coin_track_macro substrate(macro_view+sleeve_regime_ids) → opt-in on regime 동적 corr 진입
2. IC3 codify(✅) → IC4 graduation → IC8 FX → IC9 복귀 ledger
3. Phase W: W7 지표 ledger → W1 register(audit 충실분) → W2 lag_routing
4. opt-in on end-to-end 테스트: 채택지표→corr_prior→regime 동적 Σ_eff 동작 입증(테스트)
**[B. 사용자 게이트 — 라이브/실거래]**
5. ★Phase I 통합 개통: CoinTrackWithMacro→run_agents 라이브 연결(go-live 경계)
6. go-live: opt-in on 실라이브 + judge 소비
7. Phase V: 10년 백테스트
**[W8 judge qwen lens]** = agent 레이어, B 근처 후순위(우선순위 역전 정정).
→ 자율 범위 = A(부품+테스트 동작 입증). 라이브 실동작 = B(Phase I 게이트).

## 코드레벨 정합성 검토 (내 몫, 완료분)
- [x] eb_shrink 시그니처 = corr-only 확정(`conditional_correlation.py:207`). lam=n_eff 단일 → dual-uncertainty 신규.
- [x] RegimeGlasso(corr_prior=) 인터페이스 이미 존재(None=np.eye). 호출부(`regime_to_weights:197`)에서 미주입.
- [x] factor_implied_cross_cov production 호출 0 = 단순 미배선 확정. 시그니처 (betas dict, Λ)→PD cov, eigh clip PSD 보장.
- [x] prepare_corr_prior facade 이미 존재(`study_register:214`) — base 받아 firewall+flag. base 생성부가 빈 자리.

## Step (IC 순서 = 작고 검증 쉬운 것부터)

### IC0 — ★공통 선결: returns_history 공급 ✅ / ⚠️ regime substrate 누락 발견(→IC0-R)
- [x] 신규 `core/data/sleeve_returns.py`: `SLEEVE_TICKERS`(us_stock=SPY/kr_stock=EWY/commodity=DBC/gold=GLD/bond=BND/cash=BIL/coin=BTC-USD, 1차 USD ETF) + `fetch_sleeve_returns(as_of, lookback, source_fn=)` PIT 전일·log-return·source_fn 주입(mock/yfinance 분리)·실패 None.
- [x] `coin_track_macro.py` 주입: opt-in `is_r15_enabled()` 게이트 뒤 `allocate(returns_history=fetch_sleeve_returns(as_of))`. off/실패=None=fallback(무회귀).
- [x] 검증: end-to-end mock panel(150,7)→allocate on/off 무에러·weights sum 1.0. 회귀 20/20(belief_cov+study_pipeline). off byte-identical.
- 잔여: 실 yfinance fetch는 네트워크 의존 미검증(mock만). kr_stock=EWY(USD)는 IC8 FX local-return서 KRW 처리. 세분 sleeve(대안C)는 별도 티커 인프라 필요.

### IC0-R — ★regime 동적 corr substrate 런타임 공급 ✅ connectivity 완료(캐시 후속)
- [x] ★codify(2026-06-01): `coin_track_macro.collect_market_state` opt-in on 게이트 내 — `RegimeClassifier(usd_adapter=RealFredAdapter()).classify(as_of)`→macro_view + `build_sleeve_regime_ids(_clf, returns_panel, labels)`→sleeve_regime_ids → `allocate(macro_view=mv, returns_history=panel, sleeve_regime_ids=ids, as_of=as_of)`. off=macro_view/ids=None=byte-identical(allocate macro_view default None). **회귀 446 passed**. ★잔여: 무거움(매 사이클 classify+과거 전체 build) 배치 캐시 / FRED 키 graceful(키부재→UNAVAILABLE→abstain) / on+키 end-to-end regime 동적 Σ_eff 실동작 확인(라이브=P5 Phase I 게이트).
> ★IC0(returns_history)만으론 부족 발견(2026-06-01 사용자 정정): coin_track_macro 가 macro_view·sleeve_regime_ids 미공급 → regime/belief/corr_prior 체인 dormant → 정적 ic_prior. "agent 전 자동 regime 동적 corr"가 안 돈다.
- **Design intent**: ledger 통과 지표+cross 가 agent 전 배분 레이어서 regime 동적 동작(합의 방향). RegimeGlasso belief-mix 동적 Σ_eff 가 매 사이클 자동 산출.
- **현 구현**: `coin_track_macro.collect_market_state`(:60~74) = `allocate(returns_history=panel, as_of=as_of)` 만. macro_view 미생성·sleeve_regime_ids 미공급(grep 0).
- **에러 mechanism**: macro_view=None → `regime_to_weights(macro_view=None)` → ic_prior fallback(정적). sleeve_regime_ids=None → `_belief_conditional_cov` substrate 부족 → None → RegimeGlasso regime 동적 corr 미진입. 둘 다 dormant.
- **Fix 위치·내용** (coin_track_macro.collect_market_state, opt-in on 게이트 내):
  1. `RegimeClassifier(usd_adapter=RealFredAdapter())`(regime_classifier:73 `__init__` usd/krw_adapter) → `classify(as_of)` → macro_view.
  2. `build_sleeve_regime_ids(classifier, returns_panel, labels)`(regime_history:81) → sleeve_regime_ids.
  3. `allocate(macro_view=mv, returns_history=panel, sleeve_regime_ids=ids, as_of=as_of)`.
  - ★무거움(과거 전체 classify, regime_history:94 경고) → 배치 캐시 후속. 1차=connectivity(opt-in on 동작 검증).
  - ★FRED 키 부재 → classify None → macro_view UNAVAILABLE → graceful fallback(현 try 격리). off byte-identical.
- **효과 검증**: opt-in on → `belief_conditional_cov` 진입(caution 태그) + regime별 동적 Σ_eff corr_prior 자동 주입. off=정적 byte-identical. 회귀(sleeve_belief_cov + e2e allocate).
- **관문**: (나) 자동 배선=자율.

### IC1 — corr_prior 주입 (W2, 최소 글루) ✅ 배선+대안C+Λ주입(IC2) 완료
- [x] 정독: 호출부 = `_belief_conditional_cov`(`regime_to_weights:167`)의 `:197 RegimeGlasso(min_obs=10).fit(X,ids_v)`. cols=SLEEVES 순서 정렬됨(series_ids 일관성 확보). build_seed_betas → SeedBetas(betas/idio_var dict).
- [x] 시뮬(`.tmp-ic1-sim.py`): end-to-end **에러 0 + PSD 유지**(Sigma/corr_prior/결과 min eig>0) + prior 실효(idio=0.3×sys 시 off-diag 0.68~0.77, max|Δcorr|=0.059, lam=0.077). cov2corr corr-only 정합.
- [★발견 A] corr_prior 부호 = 현 SEED 정직 반영(전 sleeve rate/dollar 음동조 → 양상관). James-Stein 부호 보존.
- [★발견 B] gold decoupling 미표현 = 5 factor 중 rate/dollar/oil 3개만 실측, credit/vol=0(vol 전 자산 M5 미측정). → IC3 seed 보강(vol=VIX β) 후 N축 재평가.
- [★발견 C 설계정합] `_belief_conditional_cov`에 factor returns 없음 → **Λ_static 런타임 source 부재(=IC2 미결)**. magnitude FREEZE(§1.2-1)상 1차 corr_prior=**betas sign-only(Λ=단위)**가 정합. full B·Λ·Bᵀ magnitude=IC2 후 2차. §8 W2(sign-only)와 R9 IC1 수렴점.
- [x] 배선 작성: `_ic_corr_prior(cols)` 신규(regime_to_weights) = build_seed_betas → factor_implied_cross_cov(Λ=I, idio≈sys) → cov2corr, opt-in off=None. `:197 RegimeGlasso(corr_prior=cp)` 주입. static SEED라 firewall 불요.
- [x] 회귀: test_sleeve_belief_cov.py 7/7 통과(off 무회귀). on/off end-to-end 에러 0 + PSD(min eig 0.5/0.000126) + off cp=None byte-identical.
- [★발견 D 중대] cols=배분 SLEEVES[us_stock,kr_stock,commodity,gold,bond,cash] ≠ build_seed_betas sleeves[eq_us_cyclical,eq_us_defensive,eq_intl,reit,commodity,gold] = **다른 unit**(§1.6 분석unit↔portfolio label). 교집합 commodity/gold 2개만, 나머지 독립 → maxΔΣ_eff=6e-06 ≈ 무기여.
- **IC1 상태**: 배선 ✅ 안전(off 무회귀+on 무해, 신호이상 0). 단 실효=sleeve aggregate 매핑(IC3/§1.6) 후. 현재 §1.5 no-contribution 정직 라벨.
- [x] ★sleeve aggregate 매핑(대안C) ✅: `SLEEVE_AGG`{us_stock←cyclical0.5+defensive0.5, commodity←commodity, gold←gold} + `_ic_corr_prior` W roll-up(`Σ_alloc=W·Σ_fine·Wᵀ`, cov 공간 — beta 가중평균 금지로 sign-flip 방어). 미매핑(kr_stock/bond/cash/coin)=eye 독립, eq_intl/reit=drop(배분 부재). returns_history는 배분 유지(RegimeGlasso 입력 차원 불변=회귀 안전). IC8 layer-owner 정합(empirical=배분 / structural=세분 roll-up).
  - 검증: us_stock↔commodity 0.4372·gold 0.5260(발견D 해소, IC3 codify 후 순수 betas 값) / 미매핑 독립 / PSD 0.4705 / off=None byte-identical / 회귀.
  - 잔여: 전 자산 +0.5 양상관 = vol/credit factor 0(미측정) 탓(발견B) → IC3 seed 보강(vol=VIX β) 후 gold decoupling 부활. W 비중 eq→시총은 후속.

### IC8 — FX 6th factor (structural denomination) ✅ 완료 (2026-06-02, Track 1 자율)
> [ckpt-202606020530:btn-Inv IC8 착수전] ★사용자 지시: decisions=우리 코드 미인지 자문 → **정수만 취하고 실제 코드 유효성 별도 판정**(decisions 그대로 박지 말 것). 핸드오프/progress 이전 세션 코드맞춤 해석 우선 확인.
> ★확인 결과: handoff-wire-impl:93 IC8=decisions §11 요약 수준(코드맞춤 상세 부족). ★handoff-wire-consult:41-43 G6 FX 지적="USD자산 vol=기초+USDKRW+상관이 공분산행렬에 **이미 내재됐나 코드확인 필요**"(E97 중복구현 방지). progress-study-system:124 + eq_kr handoff="FX=`core/data/macro_market.py` FxStore USDKRW PIT" 존재.
> ★FX 코드 유효성 판정(E97 prior 검증 3건): (1) `macro_market.py` FxStore=USDKRW **환율 bitemporal PIT 저장**(get_rate, Yahoo)이지 **factor 공분산 아님** → factor_returns/SEED 에 fx factor 추가는 중복 아님(별 레이어). (2) self-test 9 측정: fx 추가가 gold×eq_us_cyclical Δcorr=0.0006(decoupling 보존). (3) fx_hedge=full → IC10 golden(us_stock×gold 0.0832) 정확 복원=toggle 작동.
> ★★판정 전환(이전 ckpt line 81 "placeholder 이상 불가" 4근거 기각): 그 4근거(empirical USD-ETF FX섞임 / kr_stock 미매핑 / FX β measured 부재=15축 관문 / dollar↔USDKRW 공선)는 **fx_β를 measured 회귀계수로 가정**한 제약. ★fx_β=**denomination 구조값**(자산 표시통화 회계, 측정 대상 아님)으로 재정식화하면 4근거 모두 우회 — USD 자산의 KRW 환노출은 자명(측정 불요), James-Stein 수축 우회(TIER_DENOMINATION), 15축 관문 비해당. base=KRW(decisions §11 확정). 이게 "decisions 정수+코드 유효성 별도 판정"의 적용.
- [x] FACTORS 5→6 (+fx), `factor_returns.FACTOR_SERIES` +fx=FRED **DEXKOUS**, `factor_cov_estimate.FACTOR_TRANSFORM` +fx=dlog(환율 로그수익)
- [x] ★TIER_DENOMINATION 신규(James-Stein 우회): SEED fx 셀=구조 denomination(USD full +0.30, gold 부분 +0.10). ★코드 유효성 판정=corr_prior magnitude FREEZE(Λ=eye 등분산·sign-only)에서 절대 환베타 1.0 은 measured β(±0.1~0.6) 대비 과대→fx 가 corr_prior 지배+gold decoupling 훼손. decisions "full≈+1"의 정수=부호·상대구조(USD>gold>0)이지 절대 1.0 아님 → measured β 대역 정규화(+0.30). 절대 1.0 은 향후 실 covariance gate 별도 layer.
- [x] `build_seed_betas(fx_hedge="none"|"full")` 토글: none=fx_β 원값(환노출), full=전 fx_β:=0(환헤지→fx 무기여=IC10 정확 복원, byte-identical). `_ic_corr_prior(..., fx_hedge=)` param 전달. 이중계상 0(empirical=FX-strip layer / structural=fx 단독 entry).
- [x] 시뮬: self-test 1~9 PASS(B·Λ·Bᵀ 6×6 PSD min eig 0.97, fx denomination 원값 보존·hedge=full→0·gold decoupling Δcorr 0.0006<0.25 게이트). factor_returns 6×6 PSD. golden 갱신(us_stock×commodity 0.2026→0.2642·×gold 0.0832→0.1298, USD 자산 공통 환채널 소폭 반영·gold 약동조). 회귀 134 passed, off byte-identical(_ic_corr_prior None).

### IC2 — Λ 라우팅 ✅ static→corr_prior / gate→risk_gate clamp 분리
- [x] 신규 `core/data/factor_returns.py`: `FACTOR_SERIES`(rate=DGS10/dollar=DTWEXBGS/oil=DCOILWTICO/credit=BAMLH0A0HYM2/vol=VIXCLS, 전부 FRED) + `fetch_factor_cov(halflife=250 static)` = to_factor_returns→estimate_factor_cov(재사용, 신규 0). self-test PASS(Λ 5×5 PSD min eig 2.4e-5).
- [x] ★함정 해소: `_default_fred_source` get_series 기반 재작성(`RealFredAdapter.get_series(sid, as_of=end)` first-release PIT 상한 + start 하한 슬라이스 + to_numpy). `fetch_series_levels`(부재) 의존 제거. fake adapter 검증=DGS10/DTWEXBGS 184행 정확, fetch_factor_cov(via fake) 5×5.
- [x] 연결: `_static_factor_lambda(nf, factors, as_of)` 신규(하루단위 `_STATIC_LAMBDA_CACHE`, 매 allocate fetch 회피) → `_ic_corr_prior`의 `np.eye(nf)` 대체. idio 도 βᵀΛβ 로 매칭(systematic 동일스케일, off-diag 죽음 방어=발견C). 실패/shape 불일치 → eye fallback(=IC1 동작, 무회귀).
- [x] gate-Λ 분리 확인: risk_gate 는 `cross_cov`를 **인자 주입** 받는 구조(`risk_gate.py:151`, 자체 Λ 추정 0, halflife/factor_cov grep 0건). `:133` "BL prior cov 누수 금지: gate 사이징 전용 — 되먹이지 않는다(이중계상 차단)" = 배분 corr_prior 와 의도적 격리. static Λ(HL250)는 배분 경로 전용, risk_gate 미접촉 → 윈도우 충돌 0.
- [x] 회귀(`.tmp-ic2-sim.py`): A off→None(byte-identical) / B on+eye fallback→PSD 0.4479·us_stock×commodity 0.5444·×gold 0.5296(**IC1 0.54/0.53 정확 재현**)·kr/bond/cash/coin 독립 0 / C on+mock Λ→PSD 0.4506·B↔C diff 0.0031(Λ 주입 경로 작동) / D get_series 재작성 정확. pytest corr_prior 7/7 + orchestrator/coin_track/risk_gate 501 passed 1 skipped 회귀 0.
### IC3 — seed tri-state ✅ codify 완료 (R9 오염차단 정수 반영) / vol·credit 실측 β=(가)관문
- [x] ★정정(초기 "기구현" 마킹 오판): tri-state 4-tier(validated/structural/reject/hold)는 build_seed_betas 에 있었으나 **R9 오염차단 정수(group-specific fallback·reject≠missing)는 미구현**이었음. 사용자 지적(2026-06-01: "코드 완료가 아니라 자문 정수가 녹았는지 / codify 는 너의 책임")으로 재검증.
- [x] ★codify(자문 글자 아닌 우리 코드 맥락): `_factor_pool` **grand(cross-group) fallback 폐기** → group-specific 만. **reject**(가설상 무관 확정)→β:=0 lock(group pool 노출도 차단). **missing/hold**(미측정)→group-specific 평균(없으면 0 — 미측정의 동일 경제군 추정=M4 게이트 가시성 의도 보존). group n==1→자기(원값 보존, magnitude FREEZE).
- [x] ★효과(gold 오염 root cause 제거): gold dollar b=**-0.328 순수**(이전 equity grand -0.408 상속 → 차단). eq_intl rate=**0.0**(reject lock, 이전 equity_risk pool 거짓 상속). eq_us_defensive dollar=-0.42(hold→equity group 평균, 가시성 유지). self-test 7/7(reject assert 의미 반전: pool노출→β:=0). corr_prior us_stock×commodity 0.5444→**0.4372**·×gold 0.5296→**0.5260**(오염 betas→순수). 회귀 414 passed.
- [ ] ⛔(가)관문 분리: vol(VIX β)·credit 실측 β SEED 박제 = 새 relationship 등록(15축 audit+small-n) → 자율 범위 밖. vol/credit=HOLD placeholder(노출 0, 게이트 차원 중립). gold decoupling 부활은 vol β 등록 후(발견B).
### IC4 — graduation 루프 ⬜ update_controller 5-AND owner, e-process=test, 사이클 경계 flip
### IC5 — byte-identical ✅ RNG 격리 확인 + golden test CI 게이트
- [x] RNG 격리(E97 코드검증): wire 핫패스(regime_to_weights→_ic_corr_prior→build_seed_betas→factor_implied_cross_cov→RegimeGlasso.fit→effective_precision→BL) **RNG 0건**. `conditional_correlation.py:60` "공용 통계 유틸 — RNG 미사용" 명시 / `block_bootstrap_se:487` seed=0 고정(§1.8 falsification 검정 전용, 핫패스 외) / self-test rng 는 `__main__` 영역. → on 경로 결정적.
- [x] FP order: dict 삽입순서 보장(Py3.7+) + cols=SLEEVES 고정 + SLEEVE_AGG/betas 순회 결정적 → 연산 순서 안정.
- [x] golden test CI 게이트: `test_ic_corr_prior_optin_off_none`(off→None) + `test_ic_corr_prior_golden_deterministic`(on+Λ=eye fallback → 결정성 replay `np.array_equal` + golden us_stock×commodity 0.4372/×gold 0.5260(IC3 codify 후) + 미매핑 독립 + PSD). 9/9 통과.
### IC7 — as_of 파라미터 ✅ valid-time(decision-time) resolve, transaction-time 누수 차단
- [x] 전파 체인: `coin_track_macro.allocate(as_of)` → `PortfolioOrchestrator.allocate(as_of)` → `regime_to_weights(as_of)` → `_belief_conditional_cov(as_of)` → `_ic_corr_prior(cols, as_of)` → `_static_factor_lambda(as_of)` → `fetch_factor_cov(as_of)`. 전 단계 default None(하위호환).
- [x] transaction-time 누수 차단: static Λ = `get_series` first-release PIT(발표시점값) + as_of 상한 causal mask. returns_history·sleeve_regime_ids 는 호출자가 as_of 로 이미 컷(IC0). `_STATIC_LAMBDA_CACHE` key=as_of 별 분리(과거 시점 Λ 격리).
- [x] 검증(`.tmp-ic7-sim.py`): as_of별 캐시 분리(2020 eye vs 2023 mock Λ → max|Δcorr|=0.0274, 둘 다 PSD) + as_of=None→today eye fallback→0.5444 golden 재현(하위호환). pytest wire 351 passed 회귀 0.
### IC6 — judge facade ✅ 기구현 확인 / 소비 wire=go-live 게이트
- [x] ★코드검증(E97): facade **이미 완전 구현**. `study_register.prepare_judge_call(study_id, regime_id)`(`:196-212`) → `{weight_card, lens_prompt, regime_pi}` judge() 인자 묶음 반환. `lens_store.render`(`:77-88`, INV_STUDY_LENS 게이트) lens_prompt 렌더. judge() 는 `lens_prompt` 인자 수용(`judge.py:166`) + lens 주입 opt-in 경로(`:223-228`) + down-only 불변식(`assert_ceiling_invariant`). self-test(`study_register:296-312`) off→lens_prompt=None / on→"판단 렌즈" 포함 PASS.
- [x] 형식 호환: prepare_judge_call 의 lens_prompt(str|None) = judge() lens_prompt 인자 타입 일치. weight_card off=None(무회귀).
- [ ] ⛔소비 wire=go-live 게이트: stock_track 이 prepare_judge_call → judge(**kwargs) 호출해 종목 *사이징* 적용 = 실거래 인접 → 자율 범위 밖(사용자 게이트). facade(준비)까지만 자율, 소비(실 사이징)는 go-live.
- **IC6 상태**: facade 3요소(prepare_judge_call/lens render/judge 수용) ✅ 완비. 소비=go-live.
### IC9 — reject 복귀 로직 + 기각 ledger ⬜ (R11 수렴, decisions §14) ★사용자 필수 구현 지시(2026-06-01)
> ★framing 정정(사용자 2026-06-01, R5): "production = reject 재진입이 **끝까지 자동 집행**(탐지→E_for 누적→5-AND gate 통과→자동 live flip). 운영자 개입 0. 수동 대기/logging-only = facade=불가". main 직전 오독("live flip=Human Gate 수동 승인")을 정정 — §14.1 "human surface 신설 X" + §14.7 "Human Gate"=사전 박제 5-AND 자동 정책(운영자=정책 상수 1회 확정뿐, 그 다음 무인). 사용자 완전 무인(confirm 0) 원칙 정합.
> ★구현 범위: 재진입 자동 집행 전체. opt-in off=byte-identical(§14.6 forward-compat fold) / on+go-live=자동 집행. 전체 실거래 ON(DRY_RUN→실주문)은 별개 시스템 스위치(재진입 로직에 수동 단계 끼우지 않음). 운영자 1회 확정=§14.9 false-revival budget+λ/threshold(n_regime 1~2 underdetermined→보수 초기값 박고 보고).
> ★자문 불요 판정: §14가 R11(gemini+claude 병렬) 수렴분으로 구현 설계 완비(14.1~14.10). 새 자문보다 §14 충실 구현.
> ★검증 방식(사용자 2026-06-01): 복귀 적절성 = **테스트로** — 실제 구현 기반 지표를 시계열 순서대로 주입하며 트레이딩 시뮬 → reject 가설 재진입 발생 관찰(Phase V 백테스트 성격, IC9 코드 완성 후).
> ★기반 코드검증 완료(2026-06-01, 부품 대부분 기구현): alpha-pricing=`online_fdr.LordPlusPlus/AlphaInvesting`(부활남용 wealth고갈 차단 이미 구현, §14.4) / e-process 폐형+as-of replay=`eprocess_backbone.MixtureSPRTEProcess.replay_value` / E_against=`weight_falsification.score_ic_breakdown_eprocess` / ledger=`event_ledger`(12 type bitemporal append-only+as-of resolve) / 5-AND=`update_controller.hysteresis_and_gate`. ★신규(§14.2 최소)=convex-leak mixing(Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ), E_against/E_for 공용)+reject_class/trigger projection+복귀 본체 모듈. ★선결(§14.9)=registry active/retired만(shadow tier 부재 Explore 확인)→live-격리 관찰 상태 빌드.
> ★구현 순서(작은것부터): **S1✅** reject_recovery.py 골격(`core/assume/reject_recovery.py` 신규: RejectClass/RevivalTrigger enum+RejectRecord §14.6 필드+content_address(cosmetic 충돌)+requires_overcoming/e_for_accrual_isolated/classify_reject, self-test PASS) → **S2✅** convex-leak e-process(`eprocess_backbone`: half_life_to_gamma/gamma_to_half_life/convex_leak_value/ConvexLeakEProcess/shift_lr — Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ), 증거소멸→1 누수=immortality·phoenix 방어)+E_for(`weight_falsification.score_ic_recovery_eprocess`=E_against 부호반전 대칭, self-test F·3b PASS) → **S3✅** event_ledger reject lifecycle(`event_ledger`: +4 EVENT_TYPES REJECT_RECORDED/REVIVAL_TRIGGERED/SHADOW_REENTERED/REVIVED + LedgerState.rejects projection + reject_status as-of, self-test 10 PASS: rejected→shadow→revived tt-cut 전이·random복원·off=rejects 빈 byte-identical) → **S4✅** RejectRecoveryGate(`reject_recovery.evaluate_recovery/RecoveryDecision`: §14.1 hysteresis_and_gate 재사용 + §14.3 burden 분기[regime_conditional=원gate / structural=overcoming E_for≥E_against_at_reject] + class C 격리[DATA_EVENT 전 차단], self-test 7~12 PASS) → **S5✅** alpha-pricing(`evaluate_recovery` alpha_account/p_value, online_fdr AlphaInvesting 재사용 §14.4, self-test 13 PASS: 약신호 60회 wealth 고갈 차단/강신호 통과) → **S6✅** trigger multiplex(`should_trigger_revival`: regime_draw 발화/n_regime_gated UNKNOWN 잔류/data_event/classC 격리)+chatter backoff(`ChatterBackoff` 지수 cooldown)+cohort falsification(`revival_cohort_falsified` E_against 재사용), self-test 14~16 PASS. ★관련 회귀 **106 passed**(event_ledger/eprocess/weight_falsification 수정 무영향) → **S7⏳** 통합 테스트(`tests/assume/test_reject_recovery.py`: end-to-end lifecycle + 시계열 IC 주입 재진입 관찰)+opt-in off byte-identical.
- [x] ★선결 코드검증: shadow tier 코드 부재 확인(Explore) → live-격리 관찰 상태 = `event_ledger.rejects` projection(status=shadow, risk 불변 paper read-model). 런타임 revive→live 비중 wire = `reject_recovery` 호출처 0 = **자동 격리**(go-live 시 wire).
- [x] E_for(복귀 e-process, E_against와 matched convex-leak) + reject_class projection — `eprocess_backbone.ConvexLeakEProcess/convex_leak_value/shift_lr`(Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ)) + `weight_falsification.score_ic_recovery_eprocess`(E_against 부호반전 대칭) + `reject_recovery.RejectClass/RejectRecord §14.6`.
- [x] event_ledger 확장(신규 ledger 금지) + reject event type 4(REJECT_RECORDED/REVIVAL_TRIGGERED/SHADOW_REENTERED/REVIVED) + materialized projection(`LedgerState.rejects`, `reject_status` as-of fold). 필드=§14.6.
- [x] 복귀 상태기계 REJECT→SHADOW(auto)→5-AND adoption — `reject_recovery.evaluate_recovery`(hysteresis_and_gate 재사용, **무인 자동**). burden=reject_class 분기(§14.3 regime_conditional 원gate / structural overcoming E_for≥E_against). alpha-pricing(online_fdr AlphaInvesting 인출, §14.4).
- [x] trigger typed multiplex(`should_trigger_revival`: regime_draw/data_event/n_regime_gated). class C(PIT-corrupt) E_for 격리(DATA_EVENT 전 차단).
- [x] chatter backoff(`ChatterBackoff` 지수 cooldown) + 복귀 cohort falsification(`revival_cohort_falsified` E_against 재사용, OOS random re-entry 구분).
- [ ] ⛔study 3건(eq_us_defensive H3·eq_intl China credit·reit H1 WALT) verdict 격상 = (가)등록 관문(15축, 별도 작업).
- **IC9 상태**: 코드(나)파이프라인 ✅ **S1~S7 완성**(`reject_recovery.py` 신규 + eprocess_backbone/weight_falsification/event_ledger 확장. 전 self-test PASS + 통합 `tests/assume/test_reject_recovery.py` 10 passed + 회귀 32 passed off byte-identical). 검증 방식=시계열 IC 주입 재진입 관찰(완비). 잔여=(가)study verdict 격상(15축)·런타임 live wire(go-live 경계).

### IC10 — ★P4 codify (measured magnitude, shadow 폐기) ⬜ ★사용자 최우선 = agent 전 배분 레이어
> P1~P3 완료(독립 audit 확정 ledger=cross-regime-ledger.md). 사용자 방향: shadow 폐기 + magnitude 측정. adopted 9건을 측정(sign+magnitude)으로 배분 레이어 corr_prior 에 코드화. opt-in off byte-identical.
- [x] **(a) adopted cross SEED cell 측정 magnitude 박제** ✅(2026-06-01): `factor_betas_seed.py SEED_CELLS` 전면 measured 교체 — batch multivariate std β(json n≈5052 HAC VIF≈1.0 직교)로 M3 등급값 폐기. vol(cyclical −0.687/intl −0.641/reit −0.565/commodity −0.141 validated)+dollar/oil/rate measured+tier=batch tier_suggest. ★발견(measured 정정): cyclical rate −0.07→+0.105(부호반전 growth) / eq_intl rate reject→validated +0.094 / **reit rate validated −0.45→reject**(univariate는 vol/dollar 공선, mv t=−0.166 비유의). self-test 7/7(test2/3/7 measured 수정). 회귀 35<37 baseline·신규 fail 0·golden 갱신. magnitude FREEZE=small-n 한정.
- [ ] **(b) SLEEVE_AGG 매핑 확장** ⛔**배분 구조 게이트(사용자 방향 논의 영역)**: 배분 SLEEVES(us_stock/kr_stock/commodity/gold/bond/cash/coin)에 **reit/eq_intl/xle sleeve 부재** → 매핑하려면 신규 배분 sleeve 추가=portfolio 구조 변경(자율 범위 밖). ★defensive 는 SLEEVE_AGG us_stock←cyclical+defensive 흡수로 **이미 반영**(measured vol −0.63 roll-up). 현 reit/eq_intl/xle 미매핑=무기여 정직라벨 유지. 배분 sleeve 확장은 사용자 게이트.
- [x] **(c) gold vol β:=0 lock 확인** ✅: gold vol batch p=0.66 + audit p_NW=0.077 비유의 → TIER_REJECT(β:=0 lock). ★결과=**us_stock×gold corr 0.526→0.083 급락 = gold decoupling measured 자연 발현**(audit gold↔cyclical +0.119 약양 정합). equity-vol pool 상속 차단=오염 root cause 방어 입증.
  - 회귀 확인: factor_betas_seed self-test 7/7 PASS + test_sleeve_belief_cov/study_pipeline 22 passed + 전체 35<37 baseline(신규 fail 0, factor/corr_prior 관련 0). off byte-identical 유지(opt-in off 테스트 통과).
  - ★measured vs yaml 정합 검증(subagent ad284aee, 사용자 지시 2026-06-01): **충돌 0, 전부 용도차**. SEED multivariate=corr_prior(factor 직교분해 Σ=BΛBᵀ)용 적합(univariate 넣으면 VIX 공통변동 중복=L축 이중계상). yaml verdict=단일자산 해석(univariate) 맥락 타당. **SEED 수정 권고 없음**(현 mv 유지). ★용도 라벨 분리: SEED β=직교 factor 조건부 loading(공분산 prior) / yaml β=단일자산 macro 민감도(해석·lens). reit yaml=Phase W4 caveat 추가 권고(univariate 단일사이클 rate-duration, factor 공분산엔 VIX 흡수=mv≈0). cyclical/eq_intl yaml=수정 불요(용도차).
- [ ] **(d) DGORDER→XLE judge L2 lag_routing** ⛔**judge 소비=go-live 경계**: lens_prompt 배선(prepare_judge_call)은 IC6 기구현이나 judge 소비 자체가 go-live(실 사이징 인접). 배선만 하면 dormant. judge=부차(사용자 framing). go-live 시 함께 활성. substrate=RegimeClassifier inflation 국면.
- [ ] **검증**: opt-in on end-to-end → adopted→corr_prior→regime 동적 Σ_eff 자동 산출. off byte-identical. 회귀(sleeve_belief_cov + study_pipeline + golden).
- **관문**: ✅**(a)(c) 완료**(measured 배분 레이어 박제 + measured-vs-yaml 검증 충돌 0, 회귀 35<37) / ⛔(b)=배분 구조 게이트(reit/eq_intl/xle sleeve 부재, 신규 배분 sleeve 추가=사용자 방향) / ⛔(d)=judge 소비 go-live 경계. magnitude=측정(shadow 폐기). crypto=small-n UNKNOWN(yaml 5건 정정 후 IC9 복귀).

## 미결 / 함정 박제
- IC1 corr_prior source = factor-space B·Λ·Bᵀ(R9) vs relationships sign-only(§8 W2 원안). 코드 정독 후 판단 — betas 있는 쌍=factor-space, 없는 쌍=relationships fallback 후보.
- e_value saturation(update_controller:28) ↔ convex-leak γ 상호작용(IC4 시).
- cholesky_ok fallback ↔ Higham-halt 충돌(IC1/N축): 기존 fallback 보존, opt-in 경계 안에서만 halt.

## ★관문 구분 (사용자 framing 2026-06-01)
- **(가) per-relationship 등록** = 15축 작성→audit 15축→통과분 등록(4관문). "어떤 관계를 카드로".
- **(나) 구현 파이프라인 (본 progress IC1~IC8)** = study 산출 런타임 배선. 검증 기준 = **자문 충실 이해 + 실제 매수/매도 신호 이상 초래 여부**(15축 audit 아님). 시뮬=무에러+PSD+배분 영향+off 무회귀.

## ★실현 가능성 진단 (yaml/리서치만으로 코드화 되나 — 사용자 질문 2026-06-01, 코드 전수확인)
> "codify 안 되고 yaml만 있는 지표 多 → 리서치+yaml만으로 코드화 가능? cross/regime(국면 의존) 추가 리서치 없이?"
**Q1 yaml만 코드화 — 부분 가능:**
- weight(L1 채택지표 가중) = `weight_rules`(base_weight/direction) yaml 有 → `_build_card` 이미 동작 ✅
- corr_prior 부호(cross) = `relationships`(블록3 prior_sign) yaml 有 but **→corr_prior 변환 경로 코드 부재**(study_loader 검증만). 신규 codify 필요.
- corr_prior 크기(β magnitude) = `SEED_CELLS` **하드코딩**(M3 verdict). yaml→SEED 자동변환 0. magnitude FREEZE라 yaml 점추정 박제 금지 → 측정(shadow).
**Q2 cross+regime 추가 리서치 없이 — ★실측/추론/후보 구분 (사용자 재질문 2026-06-01, 코드확인):**
- ★있는 작업: `_factor_shadow/batch-std-beta-5sleeve`(5 sleeve×5 factor **std β 실측** n=5052 daily) + `_wire/cross-and-regime-research.md`(cross 후보 C1~C12 + regime 정의표, **read-only enumerate 신규측정X**) + eq_us_cyclical regime PoC(DGORDER→XLE 1케이스).
- ✅ **자산↔factor 상관 = 실측**(batch β, **same-day contemporaneous**). dollar/vol 등 5 factor.
- ⚠️ **자산↔자산 cross = 직접 실측 안 함** — 공유 factor 노출서 **추론**(Σ=B·Λ·Bᵀ off-diag). hedge_note 명시 "직접 cross-corr 실측 아님". cross-and-regime-research 가 후보만.
- ⚠️ **국면별 상관 = 전면 실측 안 함** — PoC 1개(DGORDER→XLE) + 후보 정의표. regime split="정제 도구이지 생성 아님".
- ★`RegimeGlasso.fit` = **런타임 학습 메커니즘**(returns 주면 그때 학습)이지 "이미 검증된 상관 도출"이 아님 — main 이 "데이터 자동"으로 흐렸던 부분 정정.
- 신뢰성(국면의존 진짜?·small-n·lookahead) = audit 별도.
**Q3 계획(4갈래):**
1. [데이터 자동·리서치0] IC0-R substrate → RegimeGlasso 자산 국면별 동적 상관 (A 자율)
2. [yaml 코드화·리서치0] weight_rules→weight(됨) / **relationships 부호→corr_prior 변환 경로 신규 codify** (A 자율, 신규 글루)
3. [측정 필요] 절대 β magnitude(SEED 정밀화)+지표 국면별 β = J축 shadow OOS (Phase W3, 게이트)
4. [audit] 국면의존·cross 신뢰성 검증 (study audit, 추가)

## 자문 단계 R12 — 라이브 통합 + ledger 전수 agent전 자동 보장 (Phase I 진입 전) ★자문 목적=사용자 요구 방향 고정
> 사용자 2026-06-01: "자문 방향이 내 요구 방향과 명시되도록 자문 목적을 자문단계에 작성, progress 박제". 자문이 방향 이탈 못 하게 목적을 브리핑 §0 **제약(이 방향 벗어나는 답 기각)**으로 고정. 시점=통합경계 모호 해소 위해 A(부품) 진행과 병행 가능 / 늦어도 B(Phase I) 진입 전.
> **자문 목적 (사용자 요구 방향 — 브리핑 §0 제약):**
> 1. ★ledger 통과(채택) 지표 = 전부 agent(judge L2 qwen/L3 bge) 개입 전 자동 코드계산 배분 레이어서 동작 보장. **누락 0 점검 메커니즘**(yaml만 있고 런타임 미동작=미완 차단).
> 2. regime 동적 corr 가 라이브 매 사이클 자동 도는 구조 — `CoinTrackWithMacro→run_agents` 통합 경계: 어디까지 자율 배선(opt-in off 무회귀) / 어디부터 go-live 게이트(실거래).
> 3. decisions 약한 부분 보강: "전수 agent전 자동" 일괄원칙이 §7 go-live/4관문 분산 → 통합 단계 명시화.
> 4. judge(qwen/bge)=down-only 부차 확정(§1.1, 우선순위 역전 방지).
> **도구**: /gemini-web(참신) + /claude-web(실무) 병렬 default, 수렴까지 다회. ★**발사 전 게이트(③ S2 사용자 명시)**: 자문 대상 아이템 리스트를 **사용자 대화 보고·승인 후 발사**(자율다회는 승인 후). **산출**: 수렴 → decisions 신규 §(라이브 통합 원칙) 박제 → Phase I 진입 게이트.

## Phase W — study merit/verdict codify ((가)관문 등록 + 배선 정책) ★사용자 2026-06-01 지적 통합
> 이번 세션(bc9afbe0) study 리서치+yaml+audit 완료분의 런타임 codify. `handoff-study-merit-audit-20260601.md §4` + `progress-study-system.md` "다음 의도" 큐를 **main task 로 통합**(이전 = study-system 트랙에만 있고 wire-impl(현 main)엔 IC factor wire 만 있어 누락). IC(factor corr_prior=나관문)와 별개로 merit 지표 등록=(가)관문.
> ★자문 정수 codify 원칙(사용자 2026-06-01): 자문/verdict 글자 아닌 **우리 코드 맥락에 맞게** codify. 자문이 코드 못 본 부분 = main 책임 판단.

- [ ] W1 audit 충실분 register: defensive VIX term(★audit 충실 0d98a57) → vix_term family=risk **risk-overlay 라벨**(weight alpha tilt 아님) / bond_cash v5(★충실 51f3f26) → weight_card→yaml→AssumptionRegistry 배선. opt-in off 무회귀. (audit 통과분=자율 가능)
- [ ] W2 ★lag_routing 배선 정책 + 채택지표 레이어 라우팅 ("학습 기준화", §2 핵심발견 codify) — ★레이어 분석=L2 down-only 유리:
  - **Design intent**: study 채택지표를 judge 레이어에 배선. co-move 단단/forward 전멸 → contemporaneous·risk 지표=risk modulator 한정(weight alpha tilt 금지) / forward+validated=L1 alpha tilt.
  - **레이어 판정**: L1 weight_card(블록4 weight_rules→series_ids, `study_register._build_card:159`)=양방향 alpha tilt(forward용·거의 전멸+magnitude FREEZE) / **L2 lens_prompt(qwen)=down-only 감쇠 → contemporaneous·risk 지표에 유리**(down-only 불변식이 weight alpha tilt 금지를 구조 보장, judge.py `_qwen_attenuator` a2∈[0,1]) / L3 bge=유사사례.
  - **분기 로직**: `EdgeHypothesis.lag_routing`(study_loader:65) + `Indicator.family` → forward+validated→L1 weight_rules 유지 / contemporaneous·risk(VIX·credit coincident)→L2 lens_prompt 주목지표(W8 codify). PIT(naive vs live)가 동시신호 정당성 가름=배선 전 필수.
  - ((나) 배선정책=자율)
- [ ] W3 J축 정밀 β **측정** population (★shadow 폐기, magnitude=측정으로 판단): eq_us_defensive seed(rate H1 contemp validated·credit H4a industry split n=6588·VIX vol structural) + 각 sleeve raw 재실행 **절대 std β**(NW-HAC SE/CI 동반) 표준화 → seed 갱신 → OOS bias-stat **측정으로 즉시 결판**(shadow 대기 tier 운영 X). ⛔점추정 magnitude 박제 금지=**small-n(n<30) 한정**으로 좁힘 — cross large-n(n≈5052) batch β 는 측정 magnitude 박제 OK. (측정 OOS, 영구 shadow 폐기)
- [ ] W4 yaml verdict 반영: crypto cycle3(H11 prior 0.05+H9 walk-forward 게이트+H7/8/10/12 탈락) / eq_intl merit(credit coincident-PIT무효·fx exposure·REER structural·jgb reject) / defensive vix_term(prior≈0.14·risk-overlay) / cyclical DGORDER(ism_pmi_proxy XLE 정밀화).
- [ ] W5 cyclical merit 12축 audit (DGORDER→XLE TENTATIVE structural_low, 미dispatch).
- [ ] W6 eq_intl L축 DTWEXBGS full-sample(n=309~362) overlap 재검 (현 DXY n=59 hedge 해소).
- **관문**: W1/W4=verdict 반영((가)) · W2=배선 정책((나) 자율) · W3=shadow OOS 게이트((가)) · W5=audit dispatch · W6=실데이터 재검. audit 충실분(W1)은 등록 자율, 미audit/shadow분은 게이트.

## Phase V — 10년 백테스트 매매신호 일치성 검증 (자산별 subagent, ★최종 관문)
> ⛔ **자율주행 제외 — 사용자 방향 논의 게이트 (2026-06-01 사용자 지시)**: IC0~IC9 배선 완료 후, Phase V 착수 전 반드시 사용자와 방향(검증 범위·자산 우선순위·PnL 기준·subagent 스폰 수)을 논의하고 합의 후 진행. 자율로 바로 스폰 금지.
> IC0~IC9 배선 완료 후. 각 자산별로 "구현된 코드가 뽑는 매수/매도 타임 → 그대로 매매 시 이익 실현 가능?" 관점에서 코드/yaml/리서치 3자 일치성 검증. 문제 시 수정 차원 진단→메인 제출→메인 통합 최종 수정.

**입력 템플릿(subagent에 제공)**:
```
[자산]: {asset}
[구간]: 최근 10년 (PIT walk-forward — lookahead 차단, 익일시가 진입, 거시=first-release vintage)
[구현 파이프라인 경로]: core/brain/regime_to_weights.py · core/portfolio_orchestrator.py · core/coin_track_macro.py · core/study/study_register.py (wire된 상태, opt-in on)
[자산 산출]: study-research/{asset}/ (direction.md·study_session.yaml·raw/validation-*.md·theory-notes.md)
[작업]:
  1. 구현 코드로 {asset} 10년 매수/매도(비중변화) 타임 시계열 생성 (실제 파이프라인 호출, 재구현 금지)
  2. 그 신호대로 매매 시 PnL/누적수익 — 이익 실현 가능? (왕복 0.3% 차감, turnover·MDD 명시, Newey-West/block-bootstrap SE)
  3. 코드/yaml/리서치 3자 일치성: 리서치(가설·부호) ↔ yaml(base_weight·corr_prior) ↔ 코드(실제 신호) 한 줄로 흐르나? 신호가 리서치 의도대로 나오나(예: gold 디커플링 가설인데 코드가 eq 동조 신호 뽑으면 불일치)
[문제 진단 4차원]:
  (a) 분석 오류 — 리서치/가설 자체가 틀림 (실측 부실·spec drift)
  (b) 코드 신호추출 오류 — 가중치 결합이 이상해 잘못 당김 (corr_prior 부호 반대·정규화 버그·factor cancel)
  (c) yaml 칼리브레이션 오류 — base_weight/threshold가 실측과 괴리
  (d) 파이프라인 배선 오류 — 신호가 엉뚱한 모듈에 연결 (series_ids 정렬·firewall 오라우팅)
[python]: C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe + PYTHONUTF8=1
[금지]: 코드 직접 수정(메인 몫), self-certify, 재구현(실제 파이프라인 호출)
```
**출력 템플릿(subagent 반환)**:
```
[백테스트] {asset} — 10년 PnL: 누적 X% / MDD Y% / turnover Z / 비용後 알파 부호
- 매매신호 요약: 매수 N회 / 매도 M회 / 평균 보유
- 3자 일치성: 리서치↔yaml↔코드 (일치/부분/불일치 + 어디서 끊김)
- 문제 진단: (a~d) 어느 차원 + 구체 (예: "(b) corr_prior 부호 반대로 gold가 eq와 동조 매수")
- 수정 권고: 차원별 무엇을 어떻게 (메인 통합용)
```
**메인 통합**: 자산별 제출 취합 → 차원 교차(공통 패턴=파이프라인 결함, 자산 국한=칼리브레이션/분석) → 최종 수정. (가)등록·(나)배선 어느 쪽 회귀인지 판별.
