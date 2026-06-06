---
tags: [type/dispatch-gates, domain/inv, scope/equity-industry, status/active]
date: 2026-06-03
owner: main (btn-button, opus 1m)
purpose: |
  주식 산업 섹터 teammate dispatch 의 강제 게이트 SSOT. 각 섹터 teammate 는 본 4 게이트를
  모두 통과해야 "완료" 마킹 가능. supervisor 는 산출 검수 시 본 게이트로 PASS/FAIL 판정.
  속도보다 퀄리티 — 게이트 미통과 산출은 완료가 아니다.
consumer: 섹터 dispatch role 이 본 파일을 §게이트로 inline 참조. teammate 진입 시 필독.
---

# 주식 섹터 dispatch 강제 게이트 (4종)

> **확정 framing (2026-06-03)**: 한국 7산업 완료 후 미국 sleeve 재작업 진입. 이전에
> "섹터 퀄리티가 한국 대비 떨어진다 / 축을 인지만 하고 실제로 안 쓴다 / 신호 약하다고
> 자문 없이 단정한다" 는 지적이 반복됨 → 본 4 게이트로 강제화. **게이트 미통과 = 미완료.**

---

## G-A. 축 인지·이행 게이트 (★최우선)

**문제**: 15축·6단계·cross 를 "갖고는 있는데 실제 측정에 쓰는가" 가 불명확. 인지 ≠ 이행.

**의무**: 각 섹터 teammate 는 `15axis-audit.md` 에 아래 3종을 **축별 3컬럼**(① 적용했나 ② 어떻게 측정했나·코드/수치 경로 ③ 결과·판정)으로 명시. 미적용 축은 **사유 박제 의무** (빈칸 금지).

### A-1. 15축 (A~P) — 전수 명시
| 축 | 내용 | 명시 의무 |
|---|---|---|
| A | 이론 실재 | 학술 ground 문헌 1차 |
| B★ | 실데이터 검증 | PIT 수집기 실측 (합성 금지) |
| C★ | 추적성 | raw json/parquet 경로 |
| D★ | PIT-safe | 공시일 lag (DART rcept_dt / EDGAR accept ts) |
| E | 자문 환각 | 자문 인용 cross-verify |
| F | 반증+기각 | falsifier 정의 + 기각 결과 |
| G | 검정력·tier | n_effective + tier 라벨 |
| H | 미해결 의문 | candidate-ledger 연결 |
| I★ | 생존편향 | 상폐/임상실패 universe 보정 |
| J | 경제성·거래비용 | net-cost (US commission / KR STT 0.2%) |
| K | 다중검정 | **BY-FDR + M_eff (★자문 R2 반영)** |
| L | 통합 상관 PSD | L축 공통인자 1회 계상 |
| M★ | wire 충실 | opt-in off = byte-identical |
| N★ | cross PSD | cross 3종 상관행렬 PSD |
| O★ | leakage | PIT-safe + reject≠missing tri-state |
| P | net-cost robustness | sqrt 비용 모델 |

→ **Hard-fail 코어 = B·C·D·I (+M·N·O wire)**. 1개라도 결측 시 audit FAIL.

### A-2. 6단계 (S1~S6) — 각 단계 산출물 경로 + 1줄 결과
- **S1** 학술 ground (논문·증권사 정독, 자문 복붙 금지)
- **S2** 실측 4게이트: G1 ex-ante / G2 **Bonferroni·BY-FDR + M_eff** / G3 walk-forward CPCV(purge+embargo) / G4 Newey-West HAC
- **S3** 외부검토 (gemini-web + claude-web 병렬)
- **S4** 재검증 (cross / leave-episode / within-period / partial-corr / placebo / horizon sweep)
- **S5** 역공격 수렴 (최강 반증 직접 투척)
- **S6** ★**15축 독립 audit — 별도 세션 필수** (G-C 참조, supervisor 직접 평가 금지)

### A-3. cross 3종 — 분석 단위 간 상관 (within-industry 아님)
- **동시** RegimeGlasso (conditional_correlation.py) — sleeve = 공통인자 β 보고
- **방향성** Diebold-Yilmaz spillover — ★sleeve = **선행신호 후보 보고 의무**(frame line 85 (ii))
- **구조** supply-chain (customer-supplier momentum / I-O centrality) — ★sleeve = **후보 보고 의무**
- ⛔ **`directional_spillover=[]` 빈 채 제출 금지**(frame line 85: 산업 subagent = (i) 공통인자 β + (ii) DY/customer 선행신호 후보 보고). "cross=supervisor 몫"은 **조립/PSD 최종 박제**만 supervisor — **후보 발굴·보고는 sleeve 의무**. 빈 [] = FAIL 재지시.

### A-5. ★regime 정의 정합 (국면별 상관 살리기 = interaction term)
**정의**(frame line 209/323): regime-conditional = "국면 따라 IC·상호상관이 변하는 신호를 **살려** 동적가중"하는 작업. ⛔ "국면 무관 평균 0 → rejected" 로 죽이면 **regime 정의 위반**.
- 신호가 **family_1(unconditional) BY 미생존**이어도, **regime split 부호가 갈리면**(예: payout QE −0.122 유의 / 고금리 +0.054) → ★**family_2 regime-conditional interaction term**(ΔRate/Δcredit × cross-sectional, 자유도 보존) **테스트 의무**. rejected 박제 **전** family_2 선행.
- regime별 **block-boot CI 부착 의무**(frame line 323, 점추정만 = small-n §1.1c 미충족). regime당 independent episode <3 = hypothesis-generating only(confirmed 불가).
- ⛔ family_1 관점만으로 regime 신호 rejected = A-5 위반 → 재측정.

### A-6. ★supervisor 정의 대조 의무 (가이드·verdict 승인 전)
supervisor 가 teammate verdict 를 승인하거나 가이드 주기 **전**, frame §M 해당 축 정의를 **직접 Read 대조**한다. teammate framing("cross=supervisor 몫" 등)을 정의 확인 없이 수용 금지. ⛔ 정의 미확인 승인 = ERROR(promo-log 2026-06-04 supervisor-frame정의-미확인 anchor).

### A-4. sub-sector 부호 일관성 점검 (★슬리브 단위 vs 세분 = 데이터 판정)
**근거**: 발굴 지표는 archetype(cyclical 등) 공통 레벨 → 슬리브 단위 학습이 효율·통계력(N 큼) 양쪽 타당.
단 슬리브 내 sub-sector마다 신호 적합도가 다를 수 있어, **세분 여부를 데이터로 판정**한다.

- 슬리브 내 각 sub-sector(예: us_cyclical = 반도체/소재/산업재/에너지/금융)별로 채택 신호의 IC **부호** 점검.
- **부호 일관** → 슬리브 단위 유지 (분리 불필요).
- **한 sub-sector가 정반대 부호로 cancel** → 그 슬리브만 분리 트리거(별도 측정), team-lead 보고.
- ⚠️ valuation **개념 차이**(financials = 은행 interest income → Revenues/sales_yield 부적합)는 부호 cancel과 **구분** — 적합도 차이는 sector-conditional 흡수, 진짜 cancel만 분리. 한국 peak-EPS trap 의 sector별 강도 차이와 동형.

**supervisor 검수**: 15axis-audit 에서 위 3종(A-1~A-3) 누락 또는 A-4 부호 점검 결측 = **FAIL → teammate 재지시**. "축 보유" 만으로 PASS 불가, "축 이행" 입증 필요.

---

## G-B. 재자문 자동 트리거 게이트 (★신호 약함 단정 차단)

**문제**: 재측정 결과가 또 약하게 나오면 "신호 본질이 약하다" 고 자문 없이 단정 → 미국
3 sleeve 가 정확히 이 함정에 빠졌었음 (BY 생존 0 → 자문 결과 = 방법 결함 절반).

**트리거 조건** (재측정 후 자동 판정):
- BY 생존 = 0/m **AND** 최강 지표 raw_p > (BY_threshold × 2), 또는
- 전 지표 미생존 + regime-conditional 도 미생존

→ **자동으로 gemini-web + claude-web 병렬 자문** (이전 미국 method 자문과 **동일 양식**:
`.consult-us-method-briefing.md` R1 → R2 수렴 구조 미러. "방법 결함 vs 신호 본질" 5질문).

**규칙**:
- ⛔ 자문 거치기 전 "신호 약함 정직 보고" **단정 금지**.
- 자문 수렴 결론 박제 후에만 (a) 방법 수정 재측정 (b) 신호본질 약함 확정 — 둘 중 분기.
- 자문 결론 = 측정 코드(measure.py) 반영 + candidate-ledger `자산화 enum: evt` 기록.

---

## G-C. 독립 audit 게이트 (S6 = 별도 세션)

- 완료 마킹 전 **별도 세션(독립 teammate) audit 필수**. 만든 사람 ≠ 감사자.
- supervisor 직접 평가 ⛔ 금지 (inject bias 차단).
- hard-fail 코어 B·C·D·I + M·N·O = 0 확인. 1개라도 fail = 미완료, 재작업.
- audit 산출 = `industries/{sector}/15axis-audit.md` (독립 세션이 작성/검증).

---

## G-D. ledger 기록 게이트 (완료 조건)

- 섹터 "완료" = `candidate-ledger.md` + `research-log.md` 작성 완료 (둘 다, [_ledger-guide.md](./_ledger-guide.md) 양식 준수).
- 목적 = 다음 세션이 "뭐가 왜 빠졌나 / 어디서 막혔고 어떻게 풀었나" 를 코인 수준으로 재현.
- 미작성 시 = 미완료 (yaml 통합 진입 불가).

---

## G-E. 한국 진입 전 묶음-방식 자문 게이트 (★시장 간 grouping 단위 결정)

> **상태: ✅ 충족 (2026-06-05). 미국 완주(2026-06-04) 후 한국 묶음-방식 자문 3R(gemini+claude 병렬) 완료 = ★대안 C 하이브리드 확정(2층 macro-sleeve 배분 / 3층 12산업 granular conditional IC). 사용자 승인("그럼 진입!"). SSOT = plan-kr-equity-conditional-ic-20260605.md §1 + .consult-kr-sleeve-structure-brief.md. 아래 ⓐⓑⓒ 원안은 자문으로 대안 C(하이브리드=2층 묶음·3층 granular)로 수렴, sleeve 수·반도체 격리(name vs industry)는 12산업 PCA 실측(plan §8 D1~D7)으로 데이터 확정 예정.**

> (원안 박제, 이력) 잠정 채택 옵션 1 = 게이트화 + 미국 완주 후 자문. ⚠️ 미국 3 sleeve 완주 시점에 실제 자문 실행 전 team-lead 가 사용자 재confirm 의무.

**문제**: 미국 sector-neutral 발견(within-sector value vs sector-LEVEL value trap 분리) 후, 한국 7산업을 **어느 단위로 묶을지** 비자명. 미국(대형주·적자 3~16%) ≠ 한국(중소형·적자 多·외국인 flow·반도체 50% 집중) = 묶음 단위가 시장 의존. A/B/C 확신 < 80%.
- ⓐ 개별 7산업 유지 (현 KRX-WICS 12 Tier, teammate 7기)
- ⓑ archetype-sleeve 묶기 (cyclical 3=battery·반도체·auto → 1 sleeve, ~4기)
- ⓒ 시총-tier

**트리거**: 미국 3 sleeve(us_cyclical ✅ / us_defensive / us_mega_tech) 완주 직후, 한국 teammate spawn **전**.

**자문 설계** (gemini-web + claude-web 병렬, 미국 method 자문 양식 미러):
- 입력 = 미국 sector-neutral 발견(특히 회복 여부·sector-LEVEL trap mechanism) + 한국 기존 12 Tier prior(시총+외국인 flow regime 36cell+archetype 부호) + 한국 특수성.
- 질문 = "한국을 어느 단위로 몇 개씩 묶을지 + sector-neutral 한국 적용 타당성을 학술·실증 근거로".
- ★기존 Tier prior 재활용 → "기존 개별 Tier를 **sector-neutral 관점에서 재검토할 가치**" 로 좁힘 (기존 시총/flow 논의 재탕 아님 = 중복 회피).

**규칙**:
- ⛔ 자문 수렴 전 한국 묶음 단위 확정 금지.
- 자문 결론 → 한국 teammate 수(7기 vs ~4기) + 각 teammate scope 확정 → spawn.
- ★한국 단일산업은 sector-neutral = universe-demean **byte-identical**(battery 0.00e+00 검증) = 무회귀. 묶음(multi-sub-sector) 시에만 sector-neutral 효과 발생 = 자문 핵심 논점.

---

## G-F. ★Frame Contract 7항 (측정 前 선언 의무, 자문 3R B″ 확정 2026-06-04)

> **상태: 확정 (자문 3R = .consult-us-rework-3R-results.md). supervisor가 frame 정의 대조 없이 verdict 승인한 근본원인 = frame-contract 부재(명세실패). 선언적 contract를 sleeve별 동일 인스턴스화 + conformance check.**
> **SSOT 조정안**: [eq_us/REWORK-B2-adjustment-plan-20260604.md](./eq_us/REWORK-B2-adjustment-plan-20260604.md). 각 sleeve measure.py 헤더에 본 7항 선언 블록 + summary에 conformance 명시 의무.

정량 verdict 박제 직전 7항 전수 사전 선언 (미선언 = 검정 실행 불가):
1. **regime 선언규칙**: regime 변수·개수·effective-n(obs 아닌 **block 수**)·HAC lag(=regime persistence) 사전 기재. 산식 `n_eff = n/(1+2Σρ_k)`.
2. **interaction/split 사전확약 + 직교화**: conditioning을 interaction(pooled, power↑) vs split(clean, n-costly) **결과 보기 전 동결**, 사후 전환 ⛔금지. interaction항은 main effect 기지 beta에 **직교화** (예: payout = ΔReal_rate duration beta에 residualize 후 잔차). ★직교화 **order/basis 명시**.
3. **단일 FDR family**: sleeve별 family 정의, main+interaction+add가 **하나의 alpha budget** 공유 (e-process / LORD++ ledger). "공짜" interaction 검정 ⛔없음 (garden-of-forking-paths 차단).
4. **null + MDE/power 사전등록**: 모든 주장에 null·effective-n에서의 MDE·power 명시. power<threshold인 PASS = 자동 **"underpowered/inconclusive" 라벨** (PASS 아님). cross 빈 [] = measured-null+MDE로만 충족.
5. **PIT 동결 + 비대칭 search 금지**: λ·normalization 창·regime threshold·factor lag 전부 OOS 前 **expanding-window 동결**. 동결된 경우에만 OOS 게이트 유효. 가설 방향 사전선언으로 "PASS 찾기" 차단.
6. ★**Turnover / T-cost 제약** (R3 Gemini): Max Turnover 상한 OR **Net-Alpha 기반 MDE** (T-cost 차감 후). residual-mom+regime 동적가중+직교화 = 고회전 → Gross→Net alpha 침식(Spurious Strategy) 차단. (현 `long_only_net` cost 존재 → 본 항으로 승격·명문화.)
7. ★**per-test null calibration basis** (R3 Claude): effective-n=block 한자릿수 + NW-HAC = **size-invalid**(Kiefer-Vogelsang fixed-b). in-sample per-test calibration을 **fixed-b critical value / wild-cluster bootstrap**(또는 OOS와 통일=e-value)로 사전등록. asymptotic HAC t를 small-block regime 검정에 그대로 쓰면 alpha-budget이 무효 단위로 denominate = 거버넌스 붕괴.

**conformance check**: G-C 독립 audit이 7항 선언 누락·위반 점검 (hard-fail). sleeve별 이질 방법론(mega_tech만 interaction 등) 재발 차단.

---

## G-G. ★매매 신호 충분성 게이트 (tradeable signal sufficiency, 2026-06-05 사용자 지시)

**문제**: G-A~G-F는 **방법론 충실성**(hard-fail 0·FDR·PIT)만 본다. hard-fail 0 = "측정이 정직" ≠ "실매매에 쓸 신호가 충분". G-C 독립 audit PASS여도 전 신호가 INSUFFICIENT/REJECTED/OOS-flip이면 그 산업은 매매 근거 0 → WIRE5 코드화 무의미. 본 게이트 = **"실매매(L3 selection)에 투입할 필수 신호가 충분히 나왔나"** 를 별도 판정.

**필수 신호(tradeable signal) 정의** — 실매매 배선 투입 자격 = 아래 4조건 모두 충족:
- (a) **방향 확정**: walk-forward OOS에서 부호 유지 (OOS flip = 무효, in-sample artifact)
- (b) **tier ≥ structural_prior_low_confidence** (INSUFFICIENT/REJECTED 제외)
- (c) **net-alpha 양**: turnover·T-cost(KR STT 0.2% 비대칭) 차감 후 gross 신호 보존 (G-F §6 연계)
- (d) **regime 조건 명시**: 어느 국면에서 작동하는지 (conditional IC 본체 = "국면→지표→산업" 답 가능)

**판정 (산업당)**:
| 판정 | 조건 | 코드화 |
|---|---|---|
| **PASS-strong** | tradeable ≥1 + (tier high_confidence OR n≥30 OR FDR 생존) | 정상 weight |
| **PASS-conditional** | tradeable ≥1 but low confidence(small-n<30 / data-gate / net marginal) | conservative cap + monitor + ★보강 권고(non-blocking) |
| **★FAIL(부족)** | tradeable 0 (전부 REJECTED/INSUFFICIENT/OOS-flip/net 음) | ⛔코드화 보류 + 보강 의무 |

**보강 지시 (FAIL 필수 / PASS-conditional 약신호 권고)**:
1. 메인 gemini+claude 병렬 자문 (G-B 양식, "신호 본질 약 vs 지표·방법 부족" 5질문)
2. 자문 결론 → 추가 지표 발굴 + 해당 산업 teammate 재지시 (★지표 이연 금지, 측정가능 전부)
3. 재측정 후에도 tradeable 0 = 그 산업 **매매 제외**(L3 selection 비중 0 또는 monitor-only) 명시 = over-trade(약신호 강제투입) 차단

**weight 차등 (tier 반영, 충분해도 강도 차등)**:
- high_confidence → 정상 weight / low_confidence → conservative cap + hedge / tentative·PARTIAL → monitor-only(confidence_hook) 또는 최소 weight

### G-G v2 정밀화 (외부 자문 2R 수렴 + 원 설계 항목별 우열 검토, 2026-06-05)
gemini+claude 2R + 본인 정량검증(per-cell conditional wc_p 강 = BY 미생존은 36셀 multiplicity artifact) + 원 설계 대조 결론:
- **tradeable = 2축 분해**: ① eligibility(genuinely held-out OOS 부호+magnitude 유지, ★신호선택까지 walk-forward 안에 포함 + per-cell wc_p) = 매매 자격 1차 / ② conviction(empirical-Bayes shrunk IC = DerSimonian-Laird partial-pooling) = sizing 2차. net-alpha(turnover, G-F §6) gate 유지.
- **미생존 해석 = MDE/power**: t_obs=IC·√N/σ_IC ⋚ 2.802 (breakeven σ*=IC√N/2.802). t<2.802=underpowered=artifact(미생존 정보없음, OOS면 tradeable) / t>2.802=well-powered=본질약. ★단 **단일 FDR 엄격성 사수**(원 설계 우월) — MDE는 미생존 해석 보조일 뿐 FDR 완화로 survivor 인위증가 ⛔금지(자문도 "메타 forking-path" 경고).
- **regime = partial-pooling 추정 + ★국면 명시 출력**: 36셀 hard 폐기, hierarchical shrinkage(N작은 cell unconditional 수축, N큰 cell 유지). ★단 출력은 국면별 명시 라벨 유지(원 설계 사수 = "현재 국면→어느 지표→어느 종목군" 지도가 본 프로젝트 존재이유). 통합 S9.
- **충분성 = N_eff(effective independent bets, eigen-entropy) + orthogonality |ρ|<0.3**: count 아님. 한국 외국인flow dominant=상관 약신호 false breadth 위험 최대 → flow backbone 단일 bet 분리 + 직교 강신호 소수. N_eff≥~2(직교) OR strong-prior single(capex류).
- **program-level DSR**: 12 종목군 전체 forking-path(종목군/지표/regime축 선택) deflate. S9 통합 신규.
- ★실매매 구현 균형: 통계추정=자문(partial-pooling/N_eff/DSR, S9 통합단계) / 출력·sizing·국면지도=원 설계 단순성(tier별 conservative cap). measure 과적재로 배선 오류 방지.

→ supervisor(메인)가 통합 yaml(S8) 진입 **전** 본 게이트로 전 종목군 판정 의무. FAIL = 코드화 제외 + 보강. **G-C(hard-fail 0=방법)와 독립** — G-G는 매매 충분성. 둘 다 통과해야 정상 코드화.

---

## 게이트 통과 순서 (섹터 1기 lifecycle)
0. ★**S1 학술 리서치 우선** — 섹터 시작 = 측정 전에 관련 논문·리포트로 "어떤 지표가 연관있는지" 발굴 (candidate-ledger 초안 + theory-notes). team-lead 1차 확인 후 측정 진입. **리서치 없이 기존 지표 바로 재측정 금지.**
1. teammate spawn (Opus 1m) → S1 리서치 → ★**G-F frame contract 7항 사전 선언** (measure.py 헤더) → S2~S5 측정 → 15axis-audit 초안 (G-A 축별 3컬럼)
2. 재측정 결과 약함 판정 → **G-B 자동 자문** (해당 시) → 결론 반영
3. **G-C 독립 audit** (별도 세션) → hard-fail 0 확인
4. **G-D ledger** 작성 → 완료 마킹
5. supervisor 검수 (G-A 누락 0 확인) → yaml 통합 큐 등록
6. ★미국 3 sleeve 완주 직후 → **G-E 한국 묶음-방식 자문** (사용자 재confirm → gemini+claude 병렬) → 한국 묶음 단위 확정 → 한국 teammate spawn
