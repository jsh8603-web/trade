---
tags: [type/handoff, domain/inv, topic/study-wire-gap, session/btn-Inv]
date: 2026-06-01
author: btn-Inv (재개 세션 후속, clear 대비 상세본)
scope: study merit 탐구 + 12축 audit + J축 β + regime-conditional PoC + ★study→코드 wire 전수조사(거시 ref) + 다음세션 자문/코드화 방향 정립
predecessor: handoff-study-merit-audit-20260601.md
exclude: eq_kr / eq_us = stock.md 별도세션
push: ⛔ 금지 — 로컬 commit만 (사용자 재확인 2026-06-01)
---

# Handoff — study wire gap + 다음세션 자문/코드화 방향 (2026-06-01 상세본)

## 0. 이 문서 사용법 (clear 후 진입점)
- 본 파일 = 다음 세션 자율 진입점. 순서: §1 현황 → §2 wire gap(판단근거) → §3 코드화 lifecycle → §4 자문 3R 대상 5개 → §5 4관문 절차 → §6 15축 → §7 리서치 산출 → §8 실행계획.
- 다음 세션 첫 행동 = §4 자문 3R 대상으로 `/gemini-web` + `/claude-web` 병렬 3R (방향성 설정). 자문 전 사용자 보고는 이미 완료(2026-06-01 대화 확정).

## 1. 현재 상황 (이번 세션 한 일, 커밋·push금지)
이번 재개 세션 = handoff-study-merit-audit 후속. 커밋 체인(§9):
- cyclical merit 12축 audit 충실 → yaml v5 (a2f4411). crypto/eq_intl/defensive verdict→yaml (b1ef5f4/c17c874/7dc5263). defensive yaml 선재 파싱 결함(line19 inline 콤마) 정정.
- eq_intl L축 DTWEXBGS full-sample 재검(d17af0d): DXY n=59 caveat 해소, partial −0.258, DTWEXBGS observation_start=2006 실측 정정.
- 지역연준 diffusion(cc02158): Empire(NOCDISA)→SOXX 음 forward = cyclical merit 첫 Bonferroni 생존(2/84). single-region(NY) caveat. audit 충실. 적시성≠예측력 REJECTED.
- regime-conditional PoC(0700544): DGORDER→XLE inflation高 +0.42 sharpen(생존). ★결론 = regime은 신호 정제(refinement) 도구지 생성 아님.
- J축 factor β shadow(de2d44d): sample+batch std β. ★vol(ΔVIX) 포함이 깨끗한 절대 std β 관건. gold 재현 일치(방법 신뢰). factor_shadow OOS bias-stat 1.000 PASS. SEED 미반영(§3-J).
- credential probe(367d880): cushing·roll 무료불가(EIA/CME key), ISM/PMI 가능(지역연준 diffusion).
- wire 리서치(__wire/, 마지막 커밋): cross 후보 + 자산별 regime 정의 + wire codepath.

## 2. ★최대 발견 — study 산출이 런타임 매매결정에 미연결 (판단 근거 상세)
**전수조사(거시 ref, read-only subagent) 결론: study 산출 전부 런타임 미연결. "누락"이 아니라 설계상 opt-in facade 미개통.**

| 경로 | 상태 | 판단 근거 (파일:라인) |
|---|---|---|
| judge(qwen L2/BGE L3) lens·상관 | **X** | judge() 런타임 호출 0(run_agents=코인봇 점수제). lens_prompt/_call_qwen_with_lens 기구현이나 미호출. judge.py:9 "L2/L3=strictly attenuating-only", :166 lens_prompt 인자, :223 G3 lens opt-in |
| relationships→corr_prior | **X** | 런타임 RegimeGlasso() 전부 corr_prior= 생략 → np.eye. 호출처 regime_to_weights.py:197, weight_cycle.py:62. relationships→corr 변환기 코드 자체 부재(신규 글루 필요) |
| merit 지표(DGORDER/Empire/vix_term/fx_carry/ism_pmi) | **X 채택0** | core·yaml indicators grep 0. candidate-rationale.md에 "보류/측정대기"로만 |
| indicators→feature/weight_card | **X** | self-test + 오프라인 train_weights뿐 |
| 거시 regime 지표→분류기 | **부분** | fred_adapter.py:36~65 FRED_SERIES 등록 + RegimeClassifier→regime_to_weights 구현. 단 run_agents:857~881 classify() 결과 로깅만(INV_CORE_GATE 게이트 뒤), 코인 decision 미반영. portfolio_orchestrator.allocate()=coin_track_macro.py:64만 호출, run_agents import 0 |
| factor seed/shadow→risk_gate | **X** | M5 범위 밖. self-test+raw 스크립트만 |

- "언제부터" = register.py docstring "둘 다 off면 검증만, production 경로 미개통". prepare_judge_call 코드 호출 커밋 0. **의도적 opt-in facade로 머묾**.
- ★사용자 우려 둘 다 사실: (a) BGE/qwen 상관 미주입 (b) merit 발굴 지표 채택0.

## 3. ★코드화 = lifecycle 4단계 (사용자 핵심 — 고정 상수 박제 금지)
study yaml 블록5 confidence_hooks + 블록7(①learn②card③inject④falsify)이 이미 lifecycle 설계 보유. 코드화 = 이 4단계를 런타임 wire(상수 박제 X):

- **①학습(learn)**: 데이터→β/corr/weight 추정. `core/data/weight_panel.build_indicator_matrix` + `scripts/train_weights` + `core/study/factor_betas_seed`.
- **②기준 승격(adopt)**: 학습값이 언제 prior/기준이 되나. `core/assume/update_controller`(ADOPT=conjunctive 5조건 AND) + Bonferroni 생존 + shadow OOS bias-stat + n 충분. yaml confidence_hooks[confirm_signal].
- **③주입(inject)**: 기준을 런타임에. 배분=corr_prior(RegimeGlasso) / 종목=judge lens_prompt + weight_card. yaml code_change_plan[inject] + confidence_hooks[feeds_weight].
- **④약화/철회(falsify)**: 기준 무효화 조건. `core/assume/weight_falsification.score_ic_breakdown_eprocess`(e-CUSUM 단측) + update_controller RETRACT(disjunctive fast). yaml confidence_hooks[reject_signal][action_threshold].

### ★judge 단계 구조 (3R 대상 ⑤ — 설계 변경급)
judge.py(qwen L2/BGE L3)는 lifecycle 중 **inject만 인지** — lens_prompt 받고 down-only attenuator(final ∈ [0,L1_size], 증폭 구조적 부재). adopt(update_controller)·falsify(weight_falsification)는 **judge 밖 별도 모듈 사후 hook**. 그리고 ★**상관은 두 경로 분리**: 배분 레이어 corr_prior(상관 행렬, RegimeGlasso) vs 종목 judge lens_prompt(상관 서술 텍스트). judge는 corr 행렬 직접 인자 아님. → 이 구조를 어떻게 일관 wire 할지가 설계 결정(⑤).

## 4. ★자문 3R 대상 5개 (전부 "방향성 설정" — 코드화 직결 아님)
다음 세션 첫 작업 = gemini-web + claude-web 병렬 3R. 각 항목은 방향만 정함(§5 절차로 검증 후 등록).

**① 자산별 국면(regime-conditional) 정의** — 거시 inflation 외 8자산(gold/reit/crypto/eq_cyclical/eq_intl/commodity/bond_cash/defensive)
- 질문: (a) 국면 변수(PIT-safe) (b) 어느 관계가 국면 조건부 변하나 (c) hard split vs belief b(t) 확률가중 (d) n 쪼개짐·다중비교 대응. 근거: PoC=정제 도구(거시만 입증).

**② cross-asset 관계 + cross factor 정책**
- 후보: VIX risk-off 공통인자(eq_cyclical↔eq_intl/reit/defensive) 1차 / dollar pool 2차 / oil pool 3차 / gold↔equity 부의 공분산 / lead-lag(저순위, forward 전멸·reflexive 주의)
- 질문: (a) 어느 cross 코드화 가치 (b) ★cross factor 정책=grand fallback vs group-specific (J축 vol 채우면 gold −0.508 오염 — vol=group-specific인데 dollar=cross-asset?) (c) lead-lag 가치

**③ 코드화 lifecycle 4단계 자산별 구체화**
- 질문: (a) adopt 조건 조합(Bonferroni+shadow OOS+n+update_controller 5조건 중) (b) inject 방법(배분 corr_prior / 종목 lens_prompt) + down-only 보존 (c) falsify 조건(e-process? confidence decay? regime 전환?) (d) 자산별 차이(crypto halving=시간기반 vs gold factor=통계기반)

**④ 12축→15축 audit 확장 (M/N/O)** — §6. 질문: 3축 추가 적절성 + 판정 기준.

**⑤ judge/lifecycle 아키텍처 정합 (★설계 변경급)**
- judge가 inject만 인지, adopt/falsify 별도 모듈, 배분 corr_prior vs 종목 lens_prompt 두 경로 분리(§3).
- 질문: study 상관/lifecycle을 두 경로에 어떻게 일관 wire? judge가 inject만 보는 현 구조 적절한가, adopt/falsify까지 judge 사이클 통합? down-only/belief→_macro 차단 불변식 보존하며.

## 5. ★4관문 절차 (자문은 방향, 등록은 검증+audit 통과 후)
```
자문 3R (방향성 설정)  →  실데이터 15축 검증 (merit 탐구처럼 실측)  →  독립 audit (15축, self-certify 금지)  →  audit 충실(hard0)  →  비로소 등록(lifecycle 4단계 wire)
```
- ★자문이 "가치 있겠다" = 가설/방향일 뿐. 실측+audit 통과가 등록 게이트. decision-quality-protocol(자문=reference, 정량검증=verification) + GOLDEN RULE.
- 5개 대상 전부 이 4관문. 이번 세션 merit 지표 처리(실측→audit충실→yaml반영)와 동일.

## 6. 12축 → 15축 확장 (M/N/O)
기존 12축(A이론~L통합)=연구 검증 축. 코드화·cross·국면 설명성이 안 잡혀 누락. 3축 추가:
- **M축 코드화/wire 충실성**: study 산출이 실제 런타임 코드 연결됐나(indicators 등록/corr_prior 주입/judge lens/게이트). 미연결=설계 자산 분류.
- **N축 cross-asset 관계성**: 자산 간 cross 효과(factor 공유 공분산)가 측정·검증·코드화됐나. single-sleeve only=누락.
- **O축 regime-conditional 설명성**: 관계가 특정 국면서 변하는지(refinement) 검증됐나. full-sample pooling only=누락. PIT-safe + belief-weighted.
- ★AUDIT-GUIDE.md M/N/O 추가는 자문 ④ 방향 확정 후(framework 변경 신중).

## 7. main 초기 리서치 산출 (study-research/_wire/)
### cross-and-regime-research.md
- cross: 1차 VIX risk-off 공통인자, 2차 dollar, 3차 oil. C1 eq_cyclical↔eq_intl 최우선.
- regime 정의 8자산 PIT-safe: gold(real-rate+VIX) reit(rate cycle, daily소멸/monthly부활) crypto(FGI×halving) eq_cyclical(inflation clock=PoC입증) eq_intl(dollar강약) commodity(contango+financialization) bond(yield curve) defensive(VIX+credit n=9부족).
- 우선순위 top5: VIX pool→cross공분산 / cyclical inflation split / crypto FGI×halving / oil pool / dollar pool.
### wire-codepath-collection.md
- 개통순서: wire1 StudyRegister 부트스트랩(run_agents:870) → wire2 corr_prior(★relationships→corr 변환기 신규 글루 필요) → wire3 merit 지표(yaml indicators[].id or fred_adapter:64, ★FRED 가용범위 검증) → wire4 judge(go-live 경계).
- 불변식 보존: down-only(assert_ceiling_invariant judge.py:251), belief→_macro 차단(prepare_corr_prior macro no-op), opt-in off 무회귀(byte-identical), SACRED 비접촉(execute_trade 전 단계).

### J축 SEED 미반영 사유 (다음세션 ③/②와 함께)
batch std β 추출·shadow OOS PASS 했으나 SEED_CELLS 미반영. ★이유=vol 채우면 gold(real_rate_currency 그룹) grand fallback으로 −0.508 오염(시뮬 확인). build_seed_betas 보완(②cross factor 정책 자문 후) 선행 필요.

### ★jsonl 대조 누락 보완 — 실측 발견 3건 (다음세션 직접 활용)
1. **credential 유료 3종 후속 트리거**: cushing(EIA)·roll_yield(CME 다중만기)·fwd EPS revision(FINNHUB/IBES) = 무료 불가, ★키 발급 후 실데이터 forward 탐구로 진입(15축). 무료 ISM/PMI 대체(지역연준 diffusion)는 cc02158 진행 완료, 유료 3종만 키 대기 보류.
2. **J축 FINANCIALS sub-sleeve 분리** (sample stage 핵심 발견): FINANCIALS{XLF} rate **+0.162(t+6.94, NIM genuine)** vs DEFENSIVE_PURE{XLP/XLU/XLV} rate-NEG = rate dichotomy. eq-weight 시 β cancel → §1.6 분석 unit 분리(anchor ERROR-202605302245). ★SEED 매핑 = eq_us_defensive를 DEFENSIVE_PURE로, financials 별도 sub-sleeve 신설(POOL_GROUP 둘 다 equity_risk). VIF 1.01~1.14 직교, ADF stationary. DEFENSIVE_PURE rate≈0(vol 흡수)·vol −0.657·dollar −0.109.
3. **regime PoC T10Y2Y→XLI 부호반전** (regime=정제도구 2번째 증거): full 무신호(+0.02)가 inflation高 국면서 **−0.44 부호반전**(부호 반대 sub-regime이 full-sample서 cancel). 단 Bonferroni 미생존·belief-weighted 소멸 = tail fragility. ★§4-① 자산별 국면 자문의 추가검증 후보(현 잠정 directional, 박제 금지).

## 8. 다음 세션 실행 계획 (우선순위 + 판단 근거)
1. **자문 3R** (§4 5개 대상) → 방향성 설정. (autopilot ON이면 자율, 단 ⑤ 설계변경은 사용자 confirm 권장)
2. 방향대로 **15축 실데이터 검증** (우선순위 top5: VIX cross / cyclical inflation / crypto FGI×halving / oil·dollar pool).
3. **독립 audit 15축** (M/N/O 포함, self-certify 금지).
4. audit 충실분만 **등록(lifecycle 4단계 wire)** — 개통순서 §7. ★go-live 경계(judge 런타임/실거래 flip)는 자율 범위 밖, 사용자 게이트.
5. 전 자산 wire 전수조사(거시 ref 패턴 확장, 별건).

## 9. 환경/불변/제약 + 커밋 체인
- python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` prefix 필수.
- audit=별도 opus subagent self-certify 금지. 점추정 magnitude 박제 금지·sign/direction prior 생존.
- ⛔ push 금지(로컬 commit만). DRY_RUN/execute_trade SACRED. belief→_macro 차단. 공통인자 1회 계상. opt-in off 무회귀.
- eq_kr/eq_us=stock.md 별도. local-db L3~L6=별도 트랙(sqlite.md).
- 커밋 체인(이번 세션): a2f4411 b1ef5f4 c17c874 7dc5263 d17af0d de2d44d 367d880 cc02158 0700544 0e6dd45 + _wire 리서치.
