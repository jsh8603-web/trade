---
tags: [type/plan, domain/inv, scope/equity-kr, topic/conditional-ic-sleeve, status/active]
date: 2026-06-05
owner: main (btn-button, opus 1m)
trigger_to_resume: "본 plan §10 단계 + progress-kr-equity-conditional-ic-20260605.md 첫 미체크 step"
---

# plan — 한국 주식 conditional IC 측정 + sleeve 구조 (대안 C 하이브리드)

> 진행추적 = [progress-kr-equity-conditional-ic-20260605.md](./progress-kr-equity-conditional-ic-20260605.md)
> 자문 raw = [.consult-kr-sleeve-structure-brief.md](./.consult-kr-sleeve-structure-brief.md) + `~/.claude/.gemini-web-last.md` + `.claude-web-basic-last.md` (3R 수렴)
> 재사용 자산 = `study-research/eq_kr/frame.md`(v2.1) + `industries/{12산업}/`(battery·bio·consumer 완성분 = template-v3 재산출 대상) + `stock/data/krx_universe.py`(N-P3-1) + DartXbrlProvider

## 0. 목표 (사용자 원 의도 = 시스템 최종 출력)

> "지금 같은 거시 상황에서 **어떤 신호 보고 어느 산업에 투자**해야 하나"에 자동으로 답하는 시스템.

```
입력: 현재 국면 (강달러 + 외국인 순매도 + 금리인상기 ...)
  ↓
출력: "이 국면 → 내수·방어 산업 비중↑, 그 안 고배당·저변동 신호 강세 → 매수
        / 수출주(반도체·화학) 약세 → 비중↓"
```

= **국면 × 산업 × 신호 conditional IC surface** 가 시스템의 본질 산출물.

## 1. 구조 = 대안 C 하이브리드 (자문 3R 수렴, 2026-06-05, gemini+claude 만장일치)

| 층 | 역할 | 단위 | 비고 |
|---|---|---|---|
| 1층 거시 | 자산군 배분 (us_stock vs 채권/금/코인) | regime | [기구현] regime_to_weights |
| 2층 배분 | sleeve 비중 | **macro-sleeve** | PCA로 묶음 (신호측정 후 판정). STATIC inverse-vol 기본 |
| 3층 신호·선택 | 국면별 지표 → 종목 | **12산업 granular** | ★본체 (사용자 원 의도) |

- **왜 묶나(2층)**: 한국은 외국인flow·USDKRW·수출이 전 산업 공통 driver → 12산업 독립배분 = 환상의 분산(eff_N 낮음). 미국이 11 GICS → 3-4 sleeve로 간 논리(eff_N 1.47, within-corr 0.617)가 한국엔 **더 강하게** 적용될 prior.
- **왜 안 버리나(3층)**: 산업 cycle 이질성(DRAM≠NIM≠K-food)은 collapse 막는 근거가 아니라 **3층 granular 살리는 근거**. 12산업 다회 자문 산물 = 폐기 아닌 **L3 selection + neutralization 단위로 재배치**(변경비용 최소).
- **반도체 = 한국의 Mag7**: 삼성+SK하이닉스 KOSPI 50% → 격리. name(대형2사)만 vs 산업 전체(장비·소부장 포함)는 **데이터(Pass A loading + Pass B 잔차 co-move)가 판정**.

## 2. 3층 = conditional IC surface (사용자 원 의도 본체)

- 측정 대상 = `IC(지표, 산업, regime, horizon)` 4차원.
- **regime** = 36셀 (Macro 4 × KRW 3 × 외국인flow 3), N<24 cell collapse (frame §M3).
- **horizon** = y_5d / y_20d(메인) / y_60d (frame §2).
- 출력 = "저PBR이 강달러+외국인매도 국면 20d에서 반도체에 강세(부호+, IC CI 0 제외)" 식의 국면별 인기지표 지도.
- ★정직 단서(미국 실측): "어느 산업(rotation)" = 미국 약함(STATIC) / "어떤 신호(selection)" = 미국 강함(value/net_iss). 한국은 외국인flow·수출 regime이 산업을 강하게 가르니 rotation 신호 **살아있을 가능성** = 측정 대상 (사전 단정 금지).

## 3. ★리서치 정독 필수 (S1 = 가설의 원천)

> 자문(d) 진의 = "리서치 보지 마라"가 아님. **리서치는 읽되 결론·목표가·투자의견·in-sample 백테스트는 증거로 안 쓰고, 메커니즘·가설·팩터 후보만 뽑아 우리 PIT 데이터로 재검증**.

- S1 = 교과서·논문·증권사 in-depth 정독 → 메커니즘·가설 추출 (부호 사전확약 = one-sided pre-commit) → `theory-notes.md`(source URL 의무).
- 자문/리서치 결론 맹신 금지(권위의존·sell-side bias 차단). 증거는 우리 측정.
- ★FDR family = 학습 가설 수 카운트: 논문 N편→가설 M개면 검정 family=M(폐기분 포함). 리서치 정독은 가설을 "이론 근거 있는 소수"로 추려 family 축소 효과.

## 4. 방법론 = 15축 audit + 6단계 (★사전 고정, 도중 변경 금지)

- **6단계** (신호 1개 검증 흐름): S1 학술·증권사 정독 → S2 4게이트(G1 ex-ante / G2 Bonferroni·BY FDR / G3 walk-forward OOS skfolio CPCV embargo / G4 Newey-West HAC) → S3 외부검토(gemini+claude) → S4 재검증(cross=단위간상관 / leave-episode / within-period / partial-corr / placebo / **horizon sweep**) → S5 역공격(최강 반증 투척) → S6 15축 audit(hard-fail 0).
- **15축** (A~P): A이론실재 B★실데이터 C★추적성 D★PIT E자문환각 F반증+기각 G검정력·tier H미해결 I★생존편향 J경제성·거래비용 K다중검정 L통합PSD + M★wire충실 N★cross-PSD O★leakage(PIT-safe + reject≠missing tri-state) P net-cost robustness. Hard-fail 코어 = **B·C·D·I**.
- 산출양식 = template-v3 (frame-v3-draft + industry-capsule-template-v3). 12산업 capsule 통일.

## 4.5 ★강제 게이트 4종 + ledger 2종 (SSOT = `_dispatch-gates.md` / `_ledger-guide.md`)

> 섹터 teammate는 본 게이트 전수 통과해야 "완료". supervisor가 산출 검수 시 게이트로 PASS/FAIL.

- **G-A 축 인지·이행**: 15축(A~P) **3컬럼**(적용/측정 코드·수치 경로/결과 판정) + 6단계 산출물 경로 + cross 3종(동시 RegimeGlasso / 방향성 DY spillover / 구조 supply-chain — ⛔`directional_spillover=[]` 빈 채 제출 금지, 선행신호 후보 보고 의무) + A-5 regime interaction(family_1 BY 미생존이어도 regime split 부호 갈리면 **family_2 interaction term 테스트 의무**, rejected 박제 전) + A-6 supervisor 정의대조.
- **G-B 재자문 자동트리거**: BY 생존 0/m AND 최강 raw_p > 2×thresh → **gemini+claude 병렬 자문 자동**. ⛔자문 거치기 전 "신호 약함" 단정 금지(미국 sleeve가 빠진 함정).
- **G-C 독립 audit**: 별 세션(author≠auditor), hard-fail B·C·D·I + M·N·O = 0. supervisor 직접평가 금지.
- **G-D ★ledger 2종** (섹터 완료 조건, 미작성=미완료): `candidate-ledger.md`(채택/이연/미채택/falsifier/자산화 enum=rule·memory·observe-only·evt·pointer) + `research-log.md`(탐구 시계열·막힘→진단→해결→교훈 append-only·측정방법 결정 로그). 목적 = 같은 삽질 재발 방지(코인 수준). ★**산업별 독립** — 각 산업 capsule(`industries/{sector}/`)에 자기 ledger 2종(12산업 = 12쌍). teammate는 자기 산업 것만 작성, 메인 통합 시 합산(사용자 "산업별로 쪼개서 ledger 등록" 박제).
- **G-F frame contract 7항** (measure.py 헤더 사전선언, 미선언=검정 불가): ①regime 선언(effective-n=block 수·HAC lag) ②interaction/split 사전확약+직교화 order ③단일 FDR family(alpha budget) ④null+MDE/power(underpowered=PASS 아님) ⑤PIT 동결+비대칭 search 금지 ⑥turnover/T-cost(Net-alpha) ⑦per-test fixed-b/wild-cluster calibration. = 미국 11시나리오 교훈 코드화.
- **lifecycle** (섹터 1기): S1 리서치 정독(측정 前, candidate-ledger 초안) → G-F 7항 선언 → S2~S5 측정 → G-B(약함 시 자동자문) → G-C 독립 audit → G-D ledger → supervisor 검수.

### ★산출 분담 (teammate vs 메인)
- **teammate** = 산업 capsule 전체: summary.yaml(**sub-set**, 점추정 박제X = `weight_rule_candidates` base_weight_range+gate_status+confidence) + summary.md + theory-notes + validation-* + 15axis-audit + **candidate-ledger + research-log** + raw-v3/measure.py(코드는 짜되 production 미배선).
- **메인(supervisor)** = Phase 6 평가(별 audit teammate, 직접평가 금지) → Phase 7 **통합 study_session.yaml**(산업별 합산 + L축 1회계상 + PSD) → **일괄 코드화 = WIRE5 배선**(INV_R15_WEIGHTS off=byte-identical, go-live 미접촉).

## 5. 교호 = 단변량 먼저 + factor×regime만 (미국 11시나리오 교훈)

- 미국 factor×factor 2-way 11종 pre-reg 전수검증 = robust CONFIRM **1/11**(DEF-2). 단변량 value가 더 견고.
- 한국은 표본·종목 더 적음 → 교호 power 더 나쁨 + FDR family 폭발. → **단변량 factor IC 먼저 확정**, 교호는 factor×factor 보류, **factor×regime만 조건부**(36셀이 그 grid, 경제동기 명확·셀 ex-ante).
- factor×factor 굳이 시도 시 조건 5: 단변량 confirm 이후만 / confirmed factor만 / 셀 N 충분 / one-sided pre-reg / OOS incremental(FWL)로 단변량 초과.

## 6. ★사용자 PAIN 분석 + 해결책 (과거 coin/eq_us/eq_kr 실증 — 한번에 성공 못해 수십번 지시한 원인)

| # | PAIN (실증 출처) | 근본원인 | 해결책 (본 plan 내장) |
|---|---|---|---|
| P1 | **자문 그대로 코드화 후 종료 → 전면 재작업** (eq_kr A3 "다시 하라") | teammate가 자문을 yaml에 박고 본인 측정 0 | S1(리서치=가설) → S2~S6(우리 PIT 측정=증거). 자문=reference, 본인 정량 ≥1 의무(advisory-protocol) |
| P2 | **measure 후 framing/양식 틀림 발견 → 재산출** (미국 sleeve 재편·11시나리오 1/11·over-kill·universe-demean 버그 1기 후 발견 / battery 구버전 양식 재산출) | 방법론·구조·가설 사전 미확정 | ★방법론 15축/6단계/template-v3 **사전 고정** + 가설 **사전등록**(부호확약·데이터 접촉 전 동결) + 대안 C·conditional IC **본 plan 박제** |
| P3 | **teammate idle/완료 보고 누락** (§5-B "SendMessage 안 하고 텍스트만 → idle 반복") | 완료 신호 불명 | supervisor가 **파일 mtime/내용 직접 검수**로 완료 판정 + self-wake2 watchdog(멈춤 감지→재개→3회 실패 main 보고) |
| P4 | **Calculating hang** (eq_kr A2 generation 멈춤) | 무거운 .py를 generation 안에서 실행 | 무거운 분석 = **Bash python 직접 실행, 결과만 수신**. generation 내 무거운 연산 금지 |
| P5 | **subagent 기능 장애** (stock.md 18 agent stuck, Agent internal error) | 인프라 불안정 | ★**반도체 1기 파일럿 먼저**(progressive rollout) — 작동 확인 후 확장. 장애 시 main 직접 순차 |
| P6 | **supervisor 정의 미대조 승인** (§5-C ERROR) | supervisor가 frame 정의 대조 없이 verdict 승인 | **G-C 독립 audit**(별 세션, author≠auditor opus 1m) + supervisor 정의대조 게이트 + supervisor 직접평가 금지 |

## 7. ★반도체 파일럿 우선 ("테스트 후 방향" = progressive rollout, 사용자 박제)

- 반도체 1기를 **끝까지** 돌림: (a) 데이터 사전점검(universe/prices/DART 실재) → (b) S1 리서치 정독 → (c) 가설 사전등록(부호확약) → (d) S2~S5 측정 → (e) S6 15축 + G-C 독립 audit.
- 파일럿 깨끗(hard-fail 0 + 양식·데이터·게이트 작동) 확인 후에만 **나머지 11산업 확장**. 양식·데이터·방법 결함을 1기서 차단(P2/P5 방지).
- 반도체 선정 이유 = KOSPI 비중 최대 + driver 명확(DRAM cycle·외국인flow·환율) + 격리 대상이라 구조 결정에도 직결.

> ★**2층 = 2 요소** (사용자 지적 2026-06-05): (a) **static 묶음**(PCA sleeve, §8 D1~D7 = 어느 산업끼리 묶나) + (b) ★**동적 rotation timing**(S5.5 = 현재 국면에 어느 산업 비중↑↓). 기존 §8은 (a) static만 명시했고 (b) 동적 rotation = line 45 "rotation 측정 대상"인데 단계 누락 → S5.5 신설로 보강. 원 의도("이 국면→어느 산업 투자") = (b) rotation이 직접 답, 종목selection(3층)은 그 다음.

## 8. 2층 PCA sleeve 실측 (D1~D7, 신호측정과 병렬 또는 후행)

12산업 월간수익 2-pass PCA (Pass A full-12 + Pass B 반도체 residualized). deliverable+decision rule:

| # | 산출물 | decision rule |
|---|---|---|
| D1 | eigenvalue spectrum + MP edge/parallel-analysis (Pass A corr) | k*=noise선 넘는 PC 수. 1→flat / 2~3→sleeve / ≥4 표본짧으면 spurious |
| D2 | PC1 loading 12산업 | 동부호·유사크기→PC1=공통(flow), 분할은 PC2+ |
| D3 | PC2+ varimax 블록 | 깨끗 군집→sleeve 수 / 분산→flat-12 |
| D4 | 반도체 블록 loading (Pass A) | 대형2사+소부장 동일 PC→산업격리 / 대형2사만→name |
| D5 | Pass B 소부장 잔차 co-move | 잔차상관 잔존→산업격리 / 붕괴→name, 소부장 L3 |
| D6 | k*-팩터 제거 후 잔차 대각성 | idiosyncratic→L3 alpha 깨끗 / 고유값 잔존→L3 오염 flag |
| D7 | subsample 안정성 + 외부앵커 회귀(PC~USDKRW/flow/수출, 부호) | 안정 블록만 채택 + 부호 경제직관 일치 시 라벨 |

★caveat: 반도체 산업series가 cap-weight면 대형2사와 collinear → Pass B degenerate → name vs 산업 식별 불가. **eq-weight 또는 소부장-only 서브지수 + 공통 max-overlap window 필수**. correlation-PCA 우선(구조), covariance 병행(격리 변동분). 부호=외부앵커 규약 + Procrustes 정렬 + eigenvalue-gap gating.

★sleeve 구성 일반원칙(자문 정밀화2): **within-corr 낮고 신호 발산하는 산업은 같은 sleeve 금지 = 격리.** 같은 export-cyclical이라도 신호가 갈리면(DRAM↑인데 정유↓) sleeve-level 배분이 둘을 net 해서 못 표현 → 분리(반도체 격리 논리 동일). corr 높은 산업만 묶을 것(묶어도 손실 없음, 독립배분이 애초 환상이었으니).

★**2층/3층 regime 해상도 nesting** (rotation 자문 R2 수렴, RESULTS Q2): 3층 종목 measure가 쓴 **36셀(Macro4×KRW3×flow3)을 atomic partition으로 고정**, 2층 rotation regime = **36셀→6 state surjection 명시 정의**(독립정의 비일관·Simpson 역설 방지). 다른 해상도 자체는 정당(estimand별 effective sample: L3=stock×month 큼 / L2=industry-month 작음 → L2 coarse 통계적으로 옳음). L2 통계 = coarse state 내 fine cell **표본가중 pooling = empirical-Bayes 상향집계**(재추정 불필요). ★aggregation map = **ex-ante PIT 고정(prior, fitting 금지** = multiple-testing 재유입 차단). **비대칭 coarsening**(KRW/flow는 selection 적합 → L2서 더 뭉갬, export-cycle macro 축 보존). 공짜 audit gate: L2 coarse 부호 = 내부 fine cell pooled 부호 일치(불일치=prior 오류 or 집계 artifact flag). ★단 Gemini는 "36셀 자체가 n=85서 과적합(셀당 2.3개월)" 주장 → measure 단계 **본인 검증 의무**(36셀 실제 N<24 collapse 비율 + 셀당 종목×월 표본 = cross-sectional 차원 포함 실측, Claude estimand 논리 확인).

## 9. invariant (5금지 + 박제)

**5금지** (위반=FAIL): ① 점추정 prior 박제 금지(분포+CI+게이트, n<30 hedge) ② 합성·시뮬 데이터 금지(실 DART/KRX/FRED PIT만) ③ 자문 그대로 코드화 금지(본인 측정 후 채택) ④ single-source 단정 금지(학술+실무+1차 3중) ⑤ small-N 단정 금지(cell N<24 "유의" X).
**박제**: supervisor 직접평가 금지(G-C 별 세션) / analyst-lens 다운그레이드 금지(시스템 못받으면 업그레이드) / go-live·실주문·push 미접촉(D1~D5 사람게이트) / 속도보다 퀄리티(자율주행 on).

★**스폰한 teammate/agent KILL 금지** (사용자 박제 2026-06-05): 한 번 spawn한 agent는 작업·자원 손실 때문에 함부로 stop·kill 금지. 재구성이 필요해도 **살려서 SendMessage로 조종**(mid-flight 지시), 정 안 되면 사용자 확인 후에만 stop. 특히 audit teammate는 결과 회수 전 kill 금지.
★**메인 '완료' 단정 금지** (사용자 박제 2026-06-05): 메인이 "작업 다 끝났다"고 판단해도 **사용자는 아닐 수 있다.** ⓐ G-C audit 결과를 **반드시 보고 수정**(audit FAIL/PARTIAL → 재작업) ⓑ 완료 마킹·다음 단계 진입 전 **사용자 confirm 게이트**. 메인 단독 "완료" 선언 금지.
★**사용자 지시 임의변경 금지** (사용자 박제 2026-06-05): 사용자가 도구·방식을 명확히 지정하면(예: **teammate / harness2wf / 특정 wf**) 그대로 따른다. 멋대로 다른 것(Agent background 등)으로 대체 금지. ★**teammate ≠ Agent background** — teammate(harness2wf/TeamCreate)는 **자동압축(장수명)** + 역할체계 + protocol 보유, Agent background는 그게 없어 다르다. 변경이 필요하면 사용자 확인 선행.
★**불확실성 deferral 금지** (사용자 박제 2026-06-05): teammate 스폰·측정 중 불확실한 결과·판정이 나와도 **"불확실하니 나중에 보자" 식 미루기 ⛔절대 금지.** 지금 끝까지 판정(tentative/PARTIAL/INSUFFICIENT verdict라도 박제) + 현 데이터로 가능한 검증(walk-forward OOS·family_2·placebo 등) 전부 수행. "미래 데이터 필요"는 현 가능한 검증을 완주한 뒤에만 명시. flip-register/pristine OOS = 현 검증 완주 후 **추가 보너스**지 deferral 핑계 아님. 11산업 각 teammate 스폰 시 동일 적용.

## 10. 단계 (progress 동기)

- [ ] **S0. plan/progress 작성 + reflection-verify** (이번 논의·자문 3R 누락 0 매핑) + 사용자 승인
- [ ] **S1. 반도체 데이터 사전점검** — universe/prices/amount/DART 실재 + cap vs eq series 구성 결정 (Bash python 직접, P4 방지)
- [ ] **S2. 반도체 파일럿 dispatch** — teammate(하네스2wf/Agent opus 1m) role: S1 리서치 정독→가설 사전등록(부호)→S2~S5 측정→S6 15축. supervisor 파일 검수(P3) + self-wake2 watchdog
- [ ] **S3. 반도체 G-C 독립 audit** (별 세션, author≠auditor) → hard-fail 0 확인 (P6 방지)
- [ ] **S4. 파일럿 검증 게이트** — 양식·데이터·게이트 작동 + conditional IC surface 산출 확인 → 사용자 보고 + 확장 승인
- [ ] **S5. 나머지 11산업 확장** (Tier 차등 dispatch) — 파일럿 양식 미러 ✅(12산업 G-C PASS 완료, 종목선택 selection 차원)
- [ ] **S5.5. ★12산업 rotation timing 측정 (산업 자체 매수 평가 = 원 의도 본체, 2026-06-05 사용자 지적 보강)** — "현재 국면에 **어느 산업 비중↑↓**"(line 45 rotation = 종목selection S5와 별 차원). 종목selection 불가 약신호 산업(정유2/조선/통신3사/금융 data-gate)일수록 rotation이 진짜 활로. 종목선택 PASS-strong 산업도 rotation 병행. **rotation 설계 자문 2R 수렴 (gemini+claude, raw=[`.consult-kr-rotation-design-RESULTS.md`](.consult-kr-rotation-design-RESULTS.md))** 구현 스펙:
  - **(A) 측정 신호** = macro-regime backbone + ★산업별 idiosyncratic-cycle alpha(정유 crack / 조선 backlog·newbuild / 철강 China PMI·property / 반도체 memory×KRW / bio pipeline×flow-sell). momentum **강등**(flow dominant → market momentum 재포장, short-horizon reversal에 깨짐 = overlay만). valuation band = structural-break guard 한정(조선 슈퍼사이클 = stationarity 붕괴). ★부호 = **공통인자 residualize 후 재측정**(intermediate momentum = flow persistence 오염).
  - **(B) N_eff = residual-PCA** : ① 각 산업 ~ {수출증가율, USDKRW, 외국인순매수, global cyclical} 회귀로 공통 driver 제거 → ② **residual** cross-section clustering(raw-PCA는 PC1 분산 60-70% 흡수=무의미). N_eff = residual 상관 participation ratio (Σλ)²/Σλ². ★**비대칭 sleeve**: flow-beta redundant 산업 묶고 / idiosyncratic-cycle 산업 **thin sleeve/singleton 보존**(대형 sleeve 희석 시 alpha 죽음). ★singleton(잔차 직교)은 **N_eff에 ~1 온전 계상**(진짜 independent bet, participation ratio서 down-weight 금지 = diversifier 보존이 목적). 동시 active tilt = floor(N_eff) cap.
  - **(C) base+tilt** : base = sleeve-level **residual risk-parity**(각 sleeve 등위험). tilt = ★**additive-on-active-share(Σ|Δw|≤τ≈20-40%) + per-name clip(Δmax) 병행**(multiplicative는 low-base singleton서 gate 열려도 tilt≈0 구조적 함정). ★tilt 용량 = base weight 비례 금지, standalone IC/Sharpe 신뢰도로(high-vol singleton은 등위험 base weight 작아도 tilt 용량 별도). ★**floor = weight floor 금지(RP 왜곡 + singleton 지정 overfit 유인) → sleeve당 최소 risk allocation floor**(singleton sleeve도 한 sleeve몫 risk budget = 자연 floor, 단 capacity gate가 floor override = thin name은 floored도 못 받을 수 있음). over-trade 3중(hysteresis no-trade band + persistence + cost-aware gate=주필터). κ = program DSR × N_eff × live-OOS.
  - **(D) 2층×3층 결합** : 자본=곱 w_j=W_i×v_{j|i}. ★double-count 회피 = **L3 within-industry macro-neutral(demean)** = macro exposure 전부 L2 소유, L3=idiosyncratic alpha만 → KRW factor 정확히 1회(L2). 검증=조립 후 net common-factor exposure vs 의도 L2 tilt 대조.
  - **(E) multiplicity** : ★**flat BY 버리고 hierarchical sleeve-gatekeeping FDR**(sleeve-level 5×K 고power 먼저 → 통과 sleeve만 within local FDR). program DSR(별개 conviction gate). MDE/power t≈2.802. ★**continuous gating** κ_sleeve=κ_max×g(FDR·DSR·power·live-OOS 하향전용). 약신호 산업 default-0, idiosyncratic 신호 극단+확인+cost통과 시만 small-κ.
  - **(F) DSR 미생존 fallback** (R1 "전체 off" 완화) : ★①adequate-power confident-null(tight CI 0주변)=정직 **0** / ②low-power(wide CI straddle)=mechanistic PIT-prior 하 **decaying small-κ**(4조건: prior+κ DSR전 PIT등록 / causal prior / κ hard-cap data-fit금지 / live falsification e-CUSUM reject 시 κ→0). rotation 전체 끄지 않고 의도 절반 보존.
  - ★**measure 본인검증 의무**(advisory §1, RESULTS §4): 36셀 N<24 collapse 비율 실측(Gemini "과적합" claim vs Claude estimand 논리) + residual N_eff vs raw 비교 + residual 생존 산업 + sleeve DSR 생존.
- [ ] **S6. 12산업 PCA sleeve 실측** (D1~D7) — 2층 구조 데이터 확정 (static 묶음 + S5.5 동적 rotation 결합 = 2층 완성)
- [ ] **S7. Phase 6 평가 + Phase 7 통합 study_session.yaml** → WIRE5 한국 배선 인계
