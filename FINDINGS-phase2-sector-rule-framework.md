---
tags:
  - type/findings
  - domain/inv
  - phase/II
date: 2026-05-29
session: btn-Codlearn
raw_archive: ./research-raw-phase2/
handoff: ./handoff-inv-phase2-research-20260529.md
---

# FINDINGS — Inv Phase 2 거시/퀀트 고도화 + 업종 rule 프레임워크

> 자문 raw 전문 = `research-raw-phase2/{gemini,claude}-web-raw-full-20260529.md` (gemini 22k줄·claude 20k줄).
> ⚠️ **claude 자문은 응답이 길면 스크레이퍼가 잘림** (R3 답변 = "Survivo…"에서 끊겨 사실상 유실, R1·D1표도 잘림). gemini는 전문 보존. 아래 claude 출처 항목은 회수분만 신뢰, 잘린 부분은 [claude-truncated] 표기.
> 진행상태 SSOT = handoff §6.x. 이 파일 = 종합 findings.

---

## 0. 한눈 요약

- **사용자 목적**: D1(open-ended 거시 레짐 발견) / D3(업종·기간별 valuation 적응) / D4(거시 기간정의+산업군 특성 LLM 학습 Book). 바닥구현은 최후, 기존 repo/데이터 우선.
- **핵심 결론**: D3(업종·기간 조건부 valuation)을 **업종 rule 프레임워크**로 구체화. 3층 = **L1 결정론 수치게이트 + L2 Qwen 맥락 + L3 BGE 사례검색**. rule=YAML 상수. 학습은 **데이터 우선·서사 검증**.
- **방법론**: golden rule 문서 검증(D1·D3·D4-산업 부재 확인) → GitHub/논문/데이터셋 위치 자문(gemini+claude 병렬, 4라운드 진행) → 우리 거시지표 판독 가능성 판정 → plan.

## 1. golden rule(IMPLEMENTATION_PROMPT.md) 커버리지 (subagent 검증)

| 방향 | 판정 | 비고 |
|---|---|---|
| D1 open-ended 레짐 | **ABSENT** | 고정-K(jumpmodels n_components 2~4)만. deferred prompt로만 박제 |
| D2 조건부 상관·레짐 재판정 | COVERED(미연결) | §5.8-H + indicator_event_correlation.py (WRITE/recall dead) |
| D3 업종·기간 valuation | **ABSENT** | sector_ev_ebitda hook 죽어있음, 상수 하드코딩 |
| D4 학습 Book | PARTIAL | 거시서사 정적 큐레이션만, 산업군·실데이터연동 ZERO |

→ D1·D3·D4-산업 = 외부 리서치 정당.

## 2. 리소스 맵 (실재 확인된 repo·데이터)

**D1 레짐 (gemini+claude 수렴)**:
- jumpmodels (`Yizhan-Oliver-Shu/jump-models`) = 현 baseline 정식 패키지(고정-K).
- **bnpy** (`bnpy/bnpy`) = D1 정답, sticky HDP-HMM + birth/merge(새 국면 가지치기). Hughes&Sudderth NIPS2015.
- sticky_hdp_hmm_var (`benja263/...`) = 금융 switching VAR, 레짐별 상관변화 → indicator_event_correlation 수학적 짝.
- pyhsmm (`mattjj/pyhsmm`) = HDP-HSMM dwell time. ruptures (`deepcharles/ruptures`) = 기간 분절(D4). bayesian_changepoint_detection (`hildensia/...`) = BOCPD online. giotto-tda = 구조붕괴(gemini). River = online changepoint(gemini).

**D3 데이터 (gemini+claude 수렴)**:
- US: **Damodaran Online** (pebv.xls/pbvdata.xls/vebitda.xls/margin.xls/wacc.xls/ctryprem.xls) — 무료, 연1회, **vintage 없음→현재 앵커로만, PIT 백테스트 부적합**.
- **Kenneth French Data Library** = 49산업 멀티플 시계열, GICS 대체 백테스트 즉시 가능.
- KR: KRX 정보데이터시스템(업종 PER/PBR) + pykrx/FinanceDataReader + OpenDART 재무. **KR 섹터 vintage 부재 → 자체 시계열 구축 필요(최대 난관)**.
- 적응 로직 repo = **없음**(faizancodes 상대백분위 채점·Geertsema2023 논문만) → 자체구현.

**D4 (gemini 확장)**:
- ruptures(기간분절) + Microsoft **GraphRAG**(Book을 시계열 지식그래프化, indicator_event_correlation 시너지) + GDELT(지정학 서사, NewsRang 직결) + Loughran-McDonald(10-K 감성) + **JST Macrohistory**(1870~ 전쟁·위기 선례) + FRED-MD/QD(정상성 변환완료).

## 3. 업종 rule 프레임워크 (R3 — 사용자 구상 + 자문 교정)

**사용자 구상**: 업종별 top5×10년 분기보고서 리서치(subagent 병렬)→업종 valuation 특성 카드(rule seed)→백테스트 조정(업종 subagent)→메인이 seed 박고 consensus로 rule 조정. rule=상수, 싼지/비싼지 판정=BGE/Qwen.

**자문 교정(gemini+claude 일치)**:
- ⛔ **BGE/Qwen 직접 수치판정 = 안티패턴**. 싸다/비싸다=분위/z-score 수치비교라 결정론 코드 몫.
- ✅ **3층 분리**: L1 결정론(분위/z-score, hard gate) / L2 Qwen(국면별 임계 가중·맥락) / L3 BGE(유사 과거사례 retrieval=근거 제시). 임베딩은 '어떤 rule 적용할지' 라우팅엔 OK.
- gemini "Calibrated Confidence 3층" = claude 3층과 동형.

**구현 대안**:
- A(추천): Python hard gate → 통과종목만 Qwen 맥락분석 최종승인. 설명가능성 최상.
- B(도전): LLM이 rule을 Python 코드로 작성→샌드박스 백테스트. 새 팩터 발굴.

**데이터 리서치 교정**: top5×10년 분기 = 노이즈·토큰·저작권 비현실 → **국면 전환기의 연간 사업보고서+어닝콜**로 압축. 추출 타겟 = 숫자 아닌 **밸류에이션 근거 키워드 + 밸류트랩 경고신호**. Damodaran/French를 LLM에 사전 context 주입(환각 방지). 유료 애널리스트 리포트 회피, DART/EDGAR 공시원문.

**consensus(Proposer-Challenger-Arbiter)**: 텍스트 토론으로 상수 변경 금지 → **백테스트 OOS Sharpe/IC 개선 증명 시만**. 드리프트 방지=분기1회 batch+변경폭 cap(±1std/±20%)+hysteresis+rule 버전관리(git/메모리뱅크).

**기존 학습데이터 처리(사용자 핵심)**: 버리지 않고 **versioned** — 과거판정=그시점 rule_version 박제(PIT), 백테스트는 당시버전 재현. '일시적 무용' 아니라 rule_version 차원 추가 → "이 rule이 이 국면에 통했나" 메타학습 자산.

**실패모드**: survivorship(상폐기업 포함 PIT universe) / GICS 재분류 시계열단절 / rule 과적합(업종×국면 자유도→그룹화) / look-ahead(LLM 사전학습 오염→기업명 익명화 블라인드) / **밸류트랩(업종전체 디레이팅→D3에 D4 거시국면 필수 결합)** / 실자산거래라 rule 자동변경=포지션변경→**shadow기간+사람승인 게이트 필수**.

[claude-truncated: R3 모듈경계(core/valuation/sector_rules.py 등) 세부는 claude 응답 유실로 미확정 — R5에서 재확인 필요]

## 4. ★ 평가 rubric 7축 (사용자 4축 + 메인 보강 3축)

라운드4~6 검증 기준:
- **A. 무엇을 학습** — 업종 드라이버·착시·밸류트랩·사이클.
- **B. 어떤 기준으로 규칙화** — 무엇이 상수 자격? 정량/정성→임계 변환.
- **C. 어떻게 주입** — YAML 외부화→L1 게이트, BGE 라우팅.
- **D. 언제 변경** — OOS 성과저하·국면전환·신규 anomaly + consensus.
- **E. 기존 데이터 처리** — versioned 보존+재계산, PIT.
- **F.(보강) 검증·관측가능성** — rule별 기여도 attribution, 실패 시 추적.
- **G.(보강) 거버넌스·안전** — 자동변경의 라이브 영향 통제(shadow·승인·rollback). Inv=실자산.

## 5. 라운드4 (A·B축 검증) — gemini 완료, claude 진행중

**gemini R4 핵심 — "데이터 우선·서사 검증"**:
- **A1 드라이버 식별 = 이중트랙**: 정량(패널회귀/SHAP로 멀티플 설명변수)+정성(LLM 키워드) → **둘 일치 시만 Confirmed Driver**. 불일치='내러티브 괴리'=별도검토(알파 원천 가능). ⛔ "LLM 서사를 rule로 착각" 최대 경계(사후 정당화 편향).
- **A2 메타구조 = 아키타입 하이브리드**: 인간검증 원형 부여 + 내부 파라미터는 데이터학습. **4 아키타입** — Cyclical(반도체·화학: P/B·EV/EBITDA·capex), Growth/Event(바이오·인터넷: P/S·파이프라인·MAU·이벤트), Stable/Yield(유틸·통신: DDM·배당·금리), Financials(은행·증권: P/B·ROE·금리/대손). 양극단(전부학습=과적합/전부수동=경직) 회피.
- **A3 학습단위 = Median 기준선** + 생존편향(상폐기업 포함 PIT) + 선두주자편향(cap-weighted vs equal-weighted 분리계산).
- **B4 rule 승격 4게이트**: 통계유의(IC) + 경제논리(LLM 인과검증) + 시간안정성(walk-forward 다국면) + 직교성(기존 rule과 중복 안 됨).
- **B5 정성→정량 anchoring = 매핑테이블**: '공정전환기'→`capex_to_revenue_ratio_change>0.15 AND inventory_change_qoq>0.3 → action: override_per_to_ev_ebitda` (YAML).
- **B6 rule 입도 = Ensemble of Weak Rules(추천)**: 5~7개 독립 단일룰, ∑발동≥4 트리거. Monolithic(단일복합)은 데이터 결측 하나로 영원히 미발동(경직). 앙상블=결측·노이즈 강건+추적 용이.
- gemini 역질문: subagent들이 쏟아내는 rule seed 검증의 **연산비용·병목을 오케스트레이터가 어떻게 스케줄링**?

**claude R4 핵심 — "estimand 분리 + cheap=잔차" 게임체인저** (전문=`research-raw-phase2/claude-R4-full-USER-PROVIDED-20260529.md`, 스크레이퍼 잘려 사용자 직접 제공):

★★★ **단일 최대 개선 — cheap_threshold를 raw percentile → 구조모델 잔차(residual)로**:
- 현 설계 `cheap = percentile within [sector,regime]` = **밸류트랩 양산기**. 멀티플 하위 분위는 "싸다"가 아니라 "P/E 낮다"일 뿐 — 낮은 이유가 드라이버(저성장·구조훼손·피크 EPS)로 다 설명되면 그게 밸류트랩.
- `cheapness_z = (E[multiple|drivers,sector,regime] − actual) / σ_resid`. 잔차 크게 음수=진짜 저평가, 잔차≈0=밸류트랩. → **value_trap_guard가 별도 필드가 아니라 cheap 신호의 dual로 구조에서 자동 도출**.

- **estimand 분리(선결)**: 구조모델(descriptive, 멀티플 수준 설명, 과적합↓, "동종 대비 싸다" 기준선) vs 오분류모델(prescriptive, forward return 예측, 과적합↑, 알파). 한 회귀에 섞지 말 것.
- **A1 드라이버**: SHAP 그대로 쓰면 공선성(반도체 capex·b2b·재고 다 상관→grouped importance)·타깃미정·국면의존(regime-stratified)·역인과(lead/lag) 4개 깨짐. ★ 정보 최대 = 합의 아닌 **불일치 2×2**(서사O통계X=folklore, 서사X통계O=미반영변수).
- **A2 archetype discriminated union**: 공통 core + 5 archetype(cyclical/event_driven/spread_driven/asset_stable/compounder) 별 schema. 현 percentile 설계는 cyclical 1개에 과적합 — event_driven은 멀티플 percentile 무의미, compounder는 트랩이 비싼 쪽. L1 게이트는 archetype dispatch.
- **A3 PIT 패널**: survivorship 치명(상폐 포함+delisting return Shumway −30~−100%). EW median+CW 둘 다, spread를 신호. filing-lag, content-hash 동결.
- **B4 승격 게이트(완전자동 반대)**: G0 사전등록→G1 effect floor+BH FDR→G2 국면안정→G3 purged+embargo walk-forward(결정타)→G4 PBO≤0.2 deflation→G5 shadow→G6 사람비준. **증거카드=자동, 돈 flip=shadow+비준**.
- **B5 anchoring**: LLM은 변수·방향·DSL술어만, **임계값 τ는 라벨 에피소드에 적합**, 검증=precision/recall. sector-conditional(book_to_bill=반도체, 조선=수주잔고/매출).
- **B6 입도**: 조립형 versioned signal + versioned 결합정책 + rule_resolver(sector,date)→EffectiveRule. 컴포넌트 승격/롤백·실패귀속·multiple testing 통제.
- **추가 4구멍**: regime를 PIT 가능 경제지표로 정의+버전 / KR·US 이질성(시장별 분리적합 or market FE) / L3 BGE↔적합 누출(disjoint or T이전 PIT) / 밸류트랩 구조도출.
- **다음 검증 요청**: cyclical 반도체에 라벨 에피소드로 structure_model 잔차의 밸류트랩 vs 진짜저평가 분별 precision/recall — 안 갈리면 잔차 reframe 재검토.

→ claude R4가 rubric A·B축을 사실상 재설계 수준으로 채움. **gemini R4(SHAP교차검증·archetype·앙상블 weak rules)와 claude R4(잔차 reframe·estimand분리·승격게이트)는 상보 — gemini=검증방법, claude=추정구조.**

## 5.6. 라운드6 (F·G축, 실자산 안전) — 양측 완전회수, 자문 종료

**gemini R6 — "Rule Stop-loss + 비대칭 거버넌스"**:
- **F1 attribution**: Trade Tagging(주문에 trigger_rule_version 태깅, rule별 가상 PnL) → 정밀판은 Shapley Value(중첩신호 한계기여).
- **F2 대시보드**: ①Rule Hit Ratio(최근 20건 승률) ②**잔차 분포 괴리(Live Z vs Shadow Z 확산폭)** ③Subagent Timeout/Fallback 비율(할루시네이션 빈도).
- **F3 조기감지 = Rule-level Stop Loss**: 룰 자체 누적 OOS 성과가 사전정의 MDD(-5%) 터치 시 그 rule 신호 **즉시 Mute**.
- **G4 = Grandfathering(추천)**: 진입은 V2.0, 기존 포지션 청산은 V1.0/하드코딩 익절손절만. Hold 유지(일괄 시장가 매도 폭주 방지).
- **G5 = Bitemporal Soft-delete**: rule DELETE 금지, invalidated_at 스탬프만. 과거시점 조회는 당시 사실 그대로(PIT 오염 방지).
- **G6 Kill-switch = Token Bucket Execution 하드리밋**: rule 엔진과 주문 실행기 사이 방화벽. 섹터당 일일 최대주문·일 최대턴오버(3%) 물리한도, 초과 시 주문기가 신호 100% Veto.
- **G7 = Asymmetric Governance**: 강등/정지=자동 즉시, 신규 투입=shadow+사람. "퇴출 자동·진입 수동".

**claude R6 — "divergence가 1차 방어선" + 4 불변식**:
- F1: PnL_rule = PnL_actual − PnL_baseline(floor/ceiling만), Shapley-lite. ⚠️ **veto가 entry 막으면 기여=음수(0 아님), opportunity cost 별도 계상**.
- F2 **RuleObserver**: ①decision agreement rate(shadow vs live) ②signal staleness(as_of−knowledge_date) ③residual drift pctile ④veto/force-include 빈도 ⑤archetype별 활성도. staleness 누적=PIT 누수 신호.
- F3: Page-Hinkley/CUSUM(잔차) + agreement-rate 급락 + abstention spike = 큐와 분리된 **fast-path alert**.
- G4 Grandfather: position이 entry rule_version 보유, 강제청산 금지(단 신 rule이 floor 위반 시만 unwind).
- G5 bitemporal rollback = 새 knowledge_date row로 revert(옛 row 불변), 재오염 0. ⚠️ 옛 row mutate=PIT 깨짐(금지).
- G6: 계층 강제 rule veto → gate floor/ceiling → emergency_stop(전역). **rule engine은 stop의 producer지 override 아님**. rule 오작동(주문율 spike·agreement 붕괴)→auto_emergency.json 자동발화.
- G7: 자동=G0~G5, 사람=신규 archetype·regime 전환·규모 임계 초과만. band 내 미세조정=자동승인, 만료(re-ratify)로 stale 승격 방지.
- **★ 공통 누락 지적**: shadow↔live **divergence(실행 괴리)가 안전 1차 방어선인데 R1~5에서 가장 약했음. drift(모델)보다 divergence(실행)가 라이브 사고에 선행**.
- **★ 4 불변식**: ①position은 항상 entry rule_version 고정 ②rollback은 row append만(mutate 0) ③rule engine은 emergency_stop 하위(우회불가) ④opportunity cost(veto 차단분) attribution에 명시 계상.
- **모듈 4분리**: RuleObserver(관측 read-only) / RuleAttributor(반사실 PnL) / RolloutController(승격·rollback bitemporal write) / 기존 emergency(불변 상위 차단). **관측이 제어를 직접 못 건드리게**.

**★ F·G 수렴**: rule attribution=Trade Tagging+Shapley(양측, claude가 opportunity cost 추가) / Rule-level Mute·Stop(양측) / Grandfather 기본(양측 동일) / bitemporal soft-delete rollback(양측 동일, 옛 row 불변) / Token Bucket = rule engine은 emergency_stop 하위(양측) / 비대칭 거버넌스 "퇴출자동 진입수동"(양측 동일). **claude 고유: divergence 1차 방어선·RuleObserver 5지표·4 불변식·모듈 4분리(관측≠제어)**.

## 6. 우리 거시지표 판독 가능성 판정 (사용자 §2-4단계)

- 거시 D1/D4: FRED ALFRED vintage 보유 → **PIT 판독 가능**.
- 업종 D3 KR: 섹터 멀티플 vintage 부재 → **자체 시계열 구축 선행 필요**.
- 서사 레짐: NewsRang 인프라로 데이터 측 가능.

## 7. 미해결 (라운드5~6 + 사용자 결정)

- C/D/E/F/G축 심화 (R5=C·D, R6=E·F·G 예정).
- claude R3·R4 잘림분 재확인.
- rule seed JSON/YAML 직렬화 스키마 확정(gemini 역질문).
- subagent rule검증 연산 스케줄링(gemini R4 역질문).
- **병렬 분할안**: 계획 확정 시 작업을 반반으로 잘라 별도 main에 던질 준비(기준+리서치 첨부) — §8.

## 5.7. 라운드7 — ⚠️ 양측 다 새 미수렴 축 제기 = 미수렴 (정정)

> ★ 사용자 통찰: "값진 게 자꾸 나오면 미완성 증거. 계속 라운드 돌려야." R7에서 양측이 또 새 실패모드를 냄 = 미수렴. 메인의 "수렴 종료" 판정은 성급한 오판(정정).

**gemini R7**: 빠진것=archetype 시변(엔비디아 과거 게임카드)→sector/archetype bitemporal / corporate action 전처리. 먼저깨질3=잔차모델 순환참조(패닉장 정상학습)→Robust/regime별σ / BH FDR 시점오류→Alpha Spending / 드리프트↔레짐 무한루프→Regime 먼저.

**claude R7 (실제 len1011)**: 6/7축 견고하나 3축 미수렴 — ①canonical as_of resolver 선행(transaction-time as_of 다르게 해석→reconcile 발산) ②rule끼리 상관 미고려 ③★LLM 제안 다중성→**제안 전체후보 FDR 분모 로깅** 안하면 G-게이트 무력화.

→ R8(구조모델 깊이+디테일 충돌·의존성) 진행 중.

## 8. ★ 7축 현황 (R7 시점 잠정 — 미수렴, R8+ 진행)

| 축 | 최종 충족 | 핵심 결론 |
|---|---|---|
| A 무엇을학습 | 🟢 | archetype 5종(cyclical/event/spread/asset_stable/compounder) discriminated union, 드라이버 서사×통계 2×2 교차검증, PIT 패널(survivorship+delisting), EW median+CW spread |
| B 규칙화기준 | 🟢 | **cheap=구조모델 잔차(cheapness_z)** 밸류트랩 dual / 승격 G0~G6(사전등록·BH FDR·purged WF·PBO·shadow·사람) / anchoring=LLM 변수·방향만+임계 적합 P/R / weak-rule 앙상블 |
| C 주입 | 🟢 | L1 결정론 게이트=불가침 veto floor, rule=soft scoring만, RuleProvider 추상화. PIT=bitemporal **knowable_from≤as_of** |
| D 변경트리거 | 🟢 | 잔차 drift(PSI+0근방질량, IC보다 빠름)→재검토큐(자동변경X). 토너먼트 가지치기(싼 필터→비싼 백테스트) |
| E 기존데이터 | 🟢 | 2-ledger(decision 불변/analysis 소급), version_basis 꼬리표, dormant rule 부활 매트릭스(regime_model_version 필수) |
| F 검증관측 | 🟢 | Trade Tagging+Shapley attribution(opportunity cost 포함), RuleObserver 5지표, **divergence(shadow↔live)=1차 방어선**, Rule-level Stop/Mute |
| G 거버넌스 | 🟢 | Grandfather(강제청산 금지), bitemporal soft-delete rollback, Token Bucket kill-switch(rule⊂emergency_stop), 비대칭 거버넌스(퇴출자동·진입수동) |

**4 불변식**: ①position=entry rule_version 고정 ②rollback=row append만(mutate 0) ③rule engine ⊂ emergency_stop(우회불가) ④opportunity cost attribution 명시.
**모듈 4분리**: RuleObserver(관측 RO) / RuleAttributor(반사실 PnL) / RolloutController(bitemporal write) / 기존 emergency(상위 차단). 관측≠제어.

## 9. ★ 병렬 분할 2트랙 (층 분할, ~반반)

도메인(거시/업종) 아닌 **층**으로 분할 — 업종 rule 프레임워크가 커서 그 안을 가름. 두 트랙 spec = 별도 파일:
- **트랙 A = 데이터·구조 기반층** → `SPEC-trackA-data-structure.md` (rule이 딛고 설 땅: PIT 패널·구조모델 잔차·archetype schema·데이터 수집)
- **트랙 B = rule·거버넌스 운영층** → `SPEC-trackB-rule-governance.md` (signal·승격게이트·consensus·RuleObserver·거버넌스)
- **분할 가능 근거**: A가 B의 전제지만 **인터페이스 3개**(panel parquet schema / `StructureModel.predict_multiple()` / archetype dataclass)만 먼저 합의하면 병렬. B는 A의 산출물을 mock으로 개발 가능.
- D1 비모수 레짐(bnpy)·D4 거시 Book은 트랙 A에 흡수(구조모델의 regime 입력+기간정의가 같은 데이터층).
