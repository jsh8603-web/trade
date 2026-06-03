---
tags: [type/handoff, domain/inv, topic/study-wire-impl, session/btn-Inv]
date: 2026-06-01
scope: study→wire IC10 measured β 코드화 완료 + measured-vs-yaml 정합 검증 + judge 아키텍처 gap 발견 세션 인계. 잔여 작업 Track1(자율 코드)/Track2(clear후 judge+claude+테스트)/게이트 전수 정의.
push: ⛔ 금지 (로컬 commit만)
session_arc: P1 1차(top5) → P1 재작업 2분할 → 독립 P2 audit 2분할 → P3 ledger 확정 → IC10(a)(c) measured 코드화 → measured-vs-yaml 정합 → judge 코드 전수확인 → 잔여 정의 + 운영 흐름
---

# Handoff — study→wire IC10 measured + judge gap 발견 (2026-06-01, btn-Inv)

> **재개 순서**: 본 파일(전체 맥락) → `progress-wire-impl.md`(공정 SSOT P1~P5 + IC step + 🔄 세션 운영 흐름 + ★합의 방향 + ★P4 통합 방향) → `study-research/_wire/cross-regime-ledger.md`(관계 verdict 4-state) → `study-research/_wire/15axis-summary.md`(audit 기준 자기완결) → `CONSULT-DECISIONS-wire-20260601.md`(설계 상세 §11 IC1~IC8/§12 15축/§14 reject복귀).
> **규칙 우선순위**(사용자 2026-06-01): 핸드오프/plan/progress 가 우선, decisions 는 상세 참고.

---

## 0. 이 세션의 framing (사용자 다회 정정 — 압축 내성)

- **최우선 요구**: ledger 통과(채택) 지표·관계는 **agent(judge L2 qwen/L3 bge) 개입 전, 결정론 코드 계산 배분 레이어**(RegimeClassifier→RegimeGlasso 학습→corr_prior→BL)에서 **regime 동적 상관**으로 동작. judge=그 이후 down-only **부차**. "학습부터 전체 파이프라인 적용."
- **shadow 운영 폐기**(이 세션 신규 결정): 영구 shadow tier 로 미루지 않는다. adopted=측정으로 즉시 activate/reject 결판(large-n) 또는 UNKNOWN 정직 라벨(small-n).
- **magnitude=측정으로 판단**: shadow OOS population 아닌 batch β large-n 실측 직접 박제. magnitude FREEZE=small-n(n<30) 한정으로 좁힘.
- **단정 금지·받아적기 금지**: measured 를 "진실"·yaml 을 "충돌/틀림"으로 단정한 것 사용자 교정 → 측정 axis 용도차로 재정립(subagent 검증).
- **단계 엄격 구분**: P1 재작업(실측) ≠ P2 audit(독립 감사). 처음 섞은 것 정정.

---

## 1. 이번 세션 완료 (상세)

### 1.1 P1 재작업 (2분할) → 독립 P2 audit (2분할)
- **P1 1차**(agent a1aa7c1b, top5 한 agent): cross-and-regime top5 실측. ★작업량 과부하로 crypto 재현 0·defensive 미측정 = 부실 → 사용자 "2분할 재작업" 지시.
- **P1 재작업 2분할**(self-측정): a03cf09f(cross-corr 직접 실측, defensive 신규 측정 +0.697/vol β−0.66) / a7d149b4(regime+crypto raw 재계산, crypto hard-fail 발견). ★산출 스크립트 `study-research/_wire/p1-cross-direct-corr.py`+`.json`, `p2a-audit-recompute.py`.
- **독립 P2 audit 2분할**(측정자와 별도 감사관, raw 재현, 통과편향 차단): a2c6af3b(cross-corr) / a7c55f08(regime+crypto). ★산출 `p2-indep-audit.py`. 9개 점추정 소수 4자리 일치 재현, 합성 지문 0(2020-03/2022 이벤트 실재 확인).
  - ★단계 오류 정정: 처음 P2a/P2b 를 "audit"이라 라벨했으나 실제=P1 재작업(자기측정·자기판정=self-cert). 독립 audit 은 측정 안 한 별도 감사관 2명이 재발사(사용자 "audit 안한거 아냐? p1 재작업" 교정).

### 1.2 verdict (독립 audit 확정)
| 관계 | 실측[CI,n] | verdict | 채널 |
|---|---|---|---|
| eq_cyclical↔eq_intl | +0.838[.830,.845] n=6224 | **adopted** | vol+dollar cross |
| eq_cyclical↔reit | +0.686[.672,.700] n=5450 | **adopted**(reit 미매핑) | vol cross |
| commodity↔xle_energy | +0.650[.633,.665] n=5109 | **adopted**(xle 미매핑) | oil cross |
| gold↔commodity | +0.367[.343,.391] n=5109 | **adopted**(배분 진입 O) | dollar cross |
| gold↔eq_intl | +0.189[.163,.214] n=5414 | **adopted(sign)** | dollar>vol net |
| xle↔eq_cyclical | +0.639[.625,.653] n=6899 | **adopted** | vol+oil |
| defensive↔eq_cyclical | +0.697[.685,.709] n=6899 | **adopted**(P2 신규측정) | vol cross |
| defensive↔reit | +0.678[.663,.692] n=5450 | **adopted**(P2 신규측정) | vol cross |
| defensive vol β | −0.660[−.673,−.647] NW-HAC p=1.2e-75 | adopted | vol 노출 |
| gold↔eq_cyclical (C7) | +0.119[.092,.145] n=5414 | adopted(sign weak) / **hedge 가설 reject** | dollar |
| DGORDER_yoy→XLE highInfl | IC +0.423[.161,.617] n=97 NW-t=3.83, Bonferroni 유일생존+BH-FDR | **adopted**(judge L2 down-only refinement) | regime/forward |
| crypto MVRV×(FGI×halving) | raw IC −0.65~−0.05, eff_n 3~14.6 전 cell<30 | **rejected_provisional**(INSUFFICIENT, B·C 2축 hard-fail) | regime |
| financialization spike | (object mismatch) | **UNTESTED→candidate** | regime |

- **C7 gold hedge reject 근거**: tail(VIX>q99) 에서 gold↔eq_cyclical +0.29(p=0.017, n=69) = 패닉일수록 동조 강화(panic-sell, gold H5 TENTATIVE 정합). clean risk-off hedge 아님. ★관계 자체(+0.12)는 adopted, hedge **기능**만 reject.
- **crypto hard-fail 4건**(독립 audit 재현 confirm): (a) yaml cell-label 강약 뒤바뀜(markup raw −0.065 vs yaml "−0.03 약" / post_18_24m raw −0.487 vs yaml −0.51/−0.61/−0.65 3중 불일치) (b) magnitude 점추정 박제 (c) eff_n<30 전 cell(distinct episode 2~3개, n≥30 claim 무효) (d) e-CUSUM max_R 2.1e189=heuristic baseline_ic=0/sd=0.15 spurious. ★K축 완화: "per-cell p 0"이 아닌 "보고 누락+Bonferroni 미보정".

### 1.3 P3 ledger 확정
`study-research/_wire/cross-regime-ledger.md`: §1 cross 공분산(8 adopted) / §2 regime(DGORDER adopted, crypto rejected_provisional, VIX-regime candidate) / §3 기각 가설(gold hedge·gold vol β:=0) / §4 P4 codify 방향 + 독립 audit 확정 / §5 sleeve 신설 배경(향후 리서치). status 4-state(CLAUDE.md 규칙 준수). 자동생성 보조=`indicator_ledger.py`(P3 codify 완료, study_register.status() 통합).

### 1.4 IC10 (a)(c) — measured magnitude 배분 레이어 코드화 ✅
- **(a)** `core/study/factor_betas_seed.py SEED_CELLS` **batch multivariate measured 전면 교체**. source=`study-research/_factor_shadow/batch-std-beta-5sleeve.json`(5f multivariate, HAC NW=5, n≈5052, 2006-01~2026-05, VIF 1.0~1.14 직교). 이전 M3 등급값(강0.5/중0.3/약0.1 verdict-derived) 폐기. tier=batch tier_suggest. reject 셀=build_seed_betas β:=0 lock. defensive=batch 미포함→HOLD(equity_risk pool 노출 −0.63).
  - vol cell measured: cyclical −0.687/intl −0.641/reit −0.565/commodity −0.141(validated), gold −0.0106(reject β:=0), defensive(pool −0.63).
  - ★measured 발견(study verdict 정정 함의, Phase W4): **reit rate validated −0.45→reject**(univariate +0.13은 VIX 단독 흡수, mv t=−0.166 비유의) / eq_cyclical rate −0.07→+0.105(부호반전 growth) / eq_intl rate reject→validated +0.094.
  - self-test 7/7 PASS(test2=validated vs structural을 equity_risk dollar/oil로 변경, test3=reit rate reject, test7=vol measured pool). 
- **(c)** gold vol β:=0 lock(batch p=0.66 + 독립 audit p_NW=0.077 비유의). ★결과=**us_stock×gold corr 0.526→0.083 급락 = gold decoupling measured 자연 발현**(독립 audit gold↔cyclical +0.119 약양 정합). equity-vol pool 상속 차단=오염 root cause 방어 입증.
  - 회귀: factor_betas_seed self-test 7/7 + test_sleeve_belief_cov/study_pipeline 22 passed + 전체 **35<37 baseline**(신규 fail 0, factor/corr_prior 관련 0). off byte-identical 유지. golden 갱신(us_stock×commodity 0.4372→0.2026, ×gold 0.5260→0.0832, PSD 0.729).

### 1.5 measured vs yaml 정합 검증 (subagent ad284aee, 사용자 지시)
- verdict: **충돌 0, 전부 용도차**. SEED multivariate=corr_prior(factor 직교분해 Σ=BΛBᵀ)용 정합(univariate 넣으면 VIX 공통변동 중복=L축 이중계상). yaml verdict=단일자산 해석(univariate) 맥락 타당.
- reit rate: univariate +0.134[t+4.29] → vol(VIX) 단독 흡수(rate+vol −0.008), corr(rate,vol)=−0.24 → 공선 아닌 omitted-variable/suppressor 구조. 2022-24 subwindow reit rate(5f) −0.265[t−6.36] = yaml rate-duration 은 단일사이클 자산특성으로 실재.
- **SEED 수정 권고 없음**(mv 유지). 반영 2건: SEED reit rate note 정확화("vol 단독 흡수, omitted-var") + reit yaml W4 caveat 권고. 용도 라벨 분리(SEED β=직교 factor 조건부 loading / yaml β=단일자산 macro 민감도).

---

## 2. ★핵심 발견 (재개 시 반드시 인지 — 설계 결정 직결)

### 2.1 judge 코드에 claude 최종결정 경로 없음 (judge.py 전수확인)
현 `core/assume/judge.py judge()` 구조:
- **L1 ∥ DCF = 둘 다 결정론**. L1=상대축(`l1_verdict` cheapness_z, 또는 `weight_card`+indicator_z → `synthesize_l1` S_L1=clamp_floor(Σw·z)) → sizing. DCF=절대축 veto(valuation_gap < −0.30). 병렬·disjunctive, 결합 안 함.
- **L2(qwen LLM)·L3(bge RAG)=down-only 감쇠**. `_qwen_attenuator`(definition_match False→0.5) a2∈[0,1] / `_bge_attenuator`(부정 유사사례→↓) a3∈[0,1]. `size_mult=l1_size·a2·a3`, **증폭 구조 불가**(`assert_ceiling_invariant`, monotone-down). fail-safe: 미제공=a1.0 baseline / 장애=abstain(방향노출 0).
- ★**claude(LLM) 최종결정 경로 = 코드에 없음**. qwen_hook=qwen LLM 직접 호출(attenuator 입력만). claude 소환 트리거 0. judge 소비=stock-track 전용, 라이브 미연결(go-live, IC6).
- **사용자 의도 vs 코드 gap**: 사용자=claude 최종결정 + qwen/bge 트리거(넛지) + claude가 결정론 기본 기준 + 거시리포트 판단 + 지표 유용성 flag + 결정론 강화/약화. 코드=결정론 L1/DCF 최종 + claude 없음 + down-only(약화만, 강화 차단).
- ★**핵심 결정축**: "강화 허용"=down-only 불변식(LLM safe-by-construction, 자문 R1 수렴 핵심) 완화 여부. 거시리포트/주식 묶음 제안(judge=자산무관 결합 틀, 입력만 거시=리포트/주식=지표). = **Track 2 judge 재설계 자문 의제**.

### 2.2 shadow 폐기가 IC4·IC9 흔듦
- IC4 graduation(`update_controller:99 step` 5-AND, shadow→active flip)·IC9 reject복귀(decisions §14 REJECT→SHADOW→live) 둘 다 **shadow lifecycle 전제**. 사용자 "shadow 운영 폐기 + 측정 즉시 결판" 방향과 재설계 필요. Track 1 진입 전 방향 정리 선결.

### 2.3 measured=corr_prior용 multivariate 정합 + L축 1회 계상
- corr_prior=Σ=BΛBᵀ → 직교 factor 조건부 loading(multivariate)이 정의상 맞음. ★L축 불변=VIX(vol) 공통인자 SEED vol factor **1회만** 계상. VIX-regime 별도 wire 금지(독립 audit 가드, 이중계상 hard-fail).

---

## 3. 잔여 작업 정의 (file:function:변경)

### Track 1 — clear 전 (compact 반복, 자율 코드, opt-in off byte-identical)
- **IC8 — FX 6th factor** ⬜: `factor_betas_seed.py FACTORS`(rate/dollar/oil/credit/vol → +USDKRW) + `SEED_CELLS`에 sleeve별 fx_β. glasso=local(FX-stripped) return 전제 확인(`regime_to_weights` returns_history). `fx_hedge:{none|full}`→fx_β:=0/live 토글. 이중계상 0(empirical=FX제거 / structural=FX 유일진입, layer당 owner 1). gold=KRW 투자자 부분 USD hedge(decoupling 직결). decisions §11 IC8.
- **IC4/IC9 shadow-폐기 재조정** ⬜(★방향 선결): IC4=graduation owner(`update_controller` 5-AND, e-process pass=1 AND, 사이클 경계 flip) / IC9=reject복귀(decisions §14: E_for convex-leak `Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ)` 대칭, event_ledger 확장, reject_class별 burden, alpha-pricing). 둘 다 shadow 전제 → "측정 즉시 결판"과 재설계(자문 가능).
- **Phase W1 — audit 충실분 register** ⬜: defensive VIX term(family=risk, ★risk-overlay 라벨=weight alpha tilt 아님) / bond_cash v5 → `study_register._build_card` weight_card→yaml→AssumptionRegistry 배선. opt-in off 무회귀. audit 통과분=자율.
- **Phase W2 — lag_routing 배선 정책** ⬜: `study_loader EdgeHypothesis.lag_routing` + `Indicator.family` → forward+validated→L1 weight_rules / contemporaneous·risk(VIX·credit coincident)→L2 lens_prompt 주목지표. PIT(naive vs live) 동시신호 정당성 가름. (나) 배선=자율.

### Track 2 — clear 후 (새 세션, 큰 독립 주제 = claude 레이어, 깨끗 컨텍스트)
1. **judge 재설계 자문**(claude-web+gemini-web 병렬, §2.1 코드 사실 브리핑 박제): claude 최종결정 레이어 얹기 / qwen/bge→claude 트리거 기준(어떤 이상신호) / claude 판단 기준(결정론 기본 + 추가 시각) / down-only 완화 여부(강화 flag 허용?) / 거시리포트 vs 주식·지표 묶음 / claude가 "왜 소환됐는지" 결정론 컨텍스트 주입.
2. **클로드 레이어 codify**: 자문 수렴 후 judge 에 claude 소환 경로 + 트리거 + 결정론 기준 view + flag 역할. judge 소비=go-live 경계라 배선/소비 분리.
3. **전체 테스트**: 회귀 baseline 37 이하 + golden byte-identical + opt-in off.
4. **go-live 게이트(사용자)**: Phase I/P5 라이브 통합(`CoinTrackWithMacro`→`agents/orchestrator.py` run_agents), judge 소비(실 사이징), Phase V 10년 백테스트.

### 게이트 (자율 밖, 사용자 방향)
- **IC10 (b) sleeve 신설**(reit/eq_intl/xle): 배분 SLEEVES(us_stock/kr_stock/commodity/gold/bond/cash/coin) 부재 → 신규 sleeve 추가=portfolio 구성 변경. 해당 자산 study(상관·국면·factor β·weight_rules)+티커 인프라(`sleeve_returns SLEEVE_TICKERS`)+study yaml+독립 15축 audit 선행 의무. defensive=us_stock 흡수 예외. `cross-regime-ledger §5`. ★나중 리서치 큐.
- **crypto yaml 5건 정정**(W4): cell-label 강약·점추정 철회(sign-only+structural_low_confidence)·per-cell p+Bonferroni(m=16~20)·eff_n/episode 박제·e-CUSUM empirical baseline. 정정 후 IC9 복귀 경로.
- **W3** J축 측정 population(게이트)·**W4** verdict 반영(crypto/eq_intl/defensive/cyclical)·**W5** cyclical 12축 audit·**W6** eq_intl L축 재검.

---

## 4. 세션 운영 흐름 (compact/clear 기준)
- **compact(같은 세션 압축)**: ctx warn + 같은 트랙 연속(맥락 유지). Track 1=compact 로 이어감. ★1M 모델=자동압축 없음(long-mode cap 경고뿐) → 사용자 compact 지시 시 ckpt 박고 진행.
- **clear(새 세션)**: ① 주제 전환(자율 코드→judge 재설계=claude 레이어 신규) ② Track1 일단락+핸드오프 완비 ③ framing drift 누적. clear=맥락 초기화라 본 핸드오프 필수.
- **현 위치**: ctx 471k 압축 임박 → compact → Track 1(IC8부터 / IC4·IC9는 shadow-폐기 방향 정리 후) → Track 1 일단락 → **clear** → Track 2(judge+클로드+테스트+go-live).

---

## 5. 환경 / 제약 / 코드맵
- **환경**: python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1`. long-mode ON(cap 500k). push 금지(로컬 commit만). DRY_RUN/execute_trade SACRED 비접촉. opt-in off byte-identical(`INV_R15_WEIGHTS`/`INV_STUDY_LENS`/`INV_CORE_GATE`/`INV_UNATTENDED_FSM` 전부 default-off). go-live(judge 소비·실거래)=사용자 게이트.
- **회귀 baseline**: pytest 37 fail 이하(credential/network/playwright/async 환경 실패, factor/corr_prior 관련 0). 현 35 passed-fail.
- **이 세션 수정 파일**: `core/study/factor_betas_seed.py`(SEED measured 전면 + self-test) / `tests/test_sleeve_belief_cov.py`(golden 갱신) / `progress-wire-impl.md`(공정+IC10+운영흐름+ckpt) / `study-research/_wire/`(15axis-summary.md·cross-regime-ledger.md 신규).
- **임시 아티팩트**(read-only, 삭제 가능): `study-research/_wire/p1-cross-direct-corr.py`·`.json`·`p2a-audit-recompute.py`·`p2-indep-audit.py`(audit 재계산).
- **completed IC**: IC0(returns_history)·IC0-R(substrate)·IC1(corr_prior+대안C)·IC2(static Λ)·IC3(tri-state codify)·IC5(RNG격리+golden)·IC6(judge facade)·IC7(as_of PIT)·IC10(a)(c)(measured).

## 6. 다음 세션 첫 행동 (compact 후 또는 clear 후)
- **compact 후(Track 1)**: progress 🔄 운영 흐름 확인 → IC8 FX 착수(또는 IC4·IC9 shadow-폐기 방향 정리 먼저). opt-in off 무회귀 게이트 매 step.
- **clear 후(Track 2)**: 본 핸드오프 §2.1 + §3 Track 2 읽고 judge 재설계 자문 브리핑 작성(claude 코드 사실 박제) → claude-web+gemini-web 병렬.
