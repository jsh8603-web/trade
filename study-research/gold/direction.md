---
tags: [type/direction, domain/inv, study/gold, phase/2-1]
date: 2026-05-30
study_id: gold
asset_scope: commodity
note: 2-1 방향성 자문 다회 수렴(R1+R2, gemini-web + claude-web 병렬) → ①이론 수집 ②이론 검증 ③가설 초안(반증 정량). main 승인 게이트.
raw: [round-1-gemini.md, round-1-claude.md, round-2-prompt.md, round-2-gemini.md, round-2-claude.md, round-1-gemini-prompt.md, round-1-claude-prompt.md]
---

# gold 스터디 방향성 (direction.md) — v2 §2-1 수렴 결과

> **자문**: gemini-web (Gemini Pro) + claude-web (Opus 4.8 High) 병렬, R1·R2 = 2 라운드.
> **수렴**: 양 모델 모두 **R3 불필요** 자체 선언. 본 direction.md 가 R2 최종 합의 spec. R3 은 "조건부 결과 조정 트리거" 로 재정의(§5).

---

## ① 이론 수집 방향 (합의)

### (a) 학술논문 (양 모델 합의 + 우선순위)
1. **Barsky & Summers 1988** "Gibson's Paradox and the Gold Standard." JPE 96(3) — 금↔real rate 의 *level(상대가격) 관계* 정식화 원전. **level intercept shift 가설의 이론적 母船**. (Claude 검증)
2. **Erb & Harvey 2013** "The Golden Dilemma." FAJ 69(4), 10–42 — "golden constant" 실질가격 평균회귀, horizon 의존 헤지, 신흥국 보유 증가가 실질가격을 영구히 높일 가능성(cb_demand intercept shift 의 선구). (양 모델)
3. **Baur & Lucey 2010** "Is Gold a Hedge or a Safe Haven?" Fin Rev 45(2) — hedge(상시 음) vs haven(위기시 음) 정의 분리. H5 의 정식 출처. (양 모델)
4. **Baur & McDermott 2010** "Is gold a safe haven? International evidence." JBF 34(8) — 국가·국면별 haven 속성. (양 모델)
5. **O'Connor·Lucey·Batten·Baur 2015** "The financial economics of gold — A survey." IRFA 41, 186–205 — ★서베이 진입점. leasing/GOFO, 물리적 수급, inflation/rate, 버블, 행동재무 지도. (Claude 추가)
6. **Reboredo 2013** "Is gold a safe haven or a hedge for the US dollar?" JBF 37(8) — dollar 채널 + copula 꼬리의존. dollar β reconciliation 직결. (Claude 추가)
7. **Pukthuanthong & Roll 2011** "Gold and the Dollar (and the Euro, Pound, and Yen)." JBF 35(8) — **numeraire endogeneity trap 의 출처**. (Claude 추가, Q4 핵심)
8. **Caldara & Iacoviello 2022** "Measuring Geopolitical Risk." AER 112(4), 1194–1225 — **GPR index**(일별·무료). risk channel tradeable 프록시. (양 모델)
9. **Arslanalp·Eichengreen·Simpson-Bell 2023** "Gold as international reserves: A barbarous relic no more?" J Int Econ — **cb_demand intercept-shift(H3)의 실증 토대**. (Claude 추가)
10. Capie·Mills·Wood 2005 (JIFMIM 15(4)) — dollar 헤지 시변·비선형성. (Claude)

### (b) 교과서·monograph
- **Grinold & Kahn 2000** *Active Portfolio Management* (2nd ed.) — ★sys_priors β reconciliation dimensional gate 의 이론적 정의 (Fundamental Law, IC·breadth, alpha = IC·σ·score). (Claude)
- Ang 2014 *Asset Management: A Systematic Approach to Factor Investing* — factor loading 정의·추정·해석.
- Jastram 1977 *The Golden Constant* (Leyland 2009 증보) — 수세기 구매력 불변 원전.
- Geman 2005 *Commodities and Commodity Derivatives* — convenience yield, lease rate/GOFO 이론.
- **Ilmanen 2011** *Expected Returns* Ch.18 — 원자재 + 인플레 방어 (Gemini).

### (c) 공식 보고서 (양 모델 합의)
- **WGC Gold Valuation Framework (GVF) & Qaurum** — 수급 균형 implied return.
- **WGC Gold Return Attribution Model (GRAM)** — 월별 return 4범주 다중회귀 (opportunity cost / risk & uncertainty / economic expansion / momentum). ★**산업 표준 대조군 prior**.
- **WGC Gold Demand Trends** (분기) — cb_demand 톤수 1차 출처. 2024년 3년 연속 1,000톤+ 매수.
- IMF IFS & COFER — de-dollarization 검증.
- BIS WP (central bank gold/reserve management).
- LBMA precious metals statistics, Gold Price PM 벤치마크.
- Fed H.15 (DGS10, DFII10, T10YIE).

### (d) 셀사이드·매크로 (날짜 검증된 decoupling thesis, Claude R1 격상 → R2 양 모델 인정)
- **T. Rowe Price (de los Reyes, 2024.11)** "What is driving gold prices to all-time record highs?" — fiscal/debasement·cb_demand·geopolitics 귀인.
- **RBC Wealth Management (2025.6)** "Gold's regime change?" — **TIPS-gold level R² 2005-2021 84% → 2022-23 3% → 2024+ 7%** 시계열. ★level 현상 외부 corroboration.
- **Apollo (Torsten Sløk)** "Gold and Rates Correlation Breakdown" — regime 의존성 명시.
- Bridgewater / Dalio (Paradigm Shifts 2019, The Changing World Order 2021) — **narrative 적합, 학술 근거 아님**(Claude 보수 판정). H2 의 동기 부여 색채로만, confirmatory/causal 인용 금지.
- HSBC / Goldman Sachs Commodities / SocGen Cross-Asset 분기 outlook.

---

## ② 이론 검증 방향 (합의)

### 변수 정의표 (R2 양 모델 합의)

| driver | 1차 시리즈 | 변환 | 빈도 | 비고 |
|---|---|---|---|---|
| gold | **LBMA Gold PM USD/oz** + **gold/SDR** (numeraire trap 대응 1차) + USD-제외 바스켓(robustness) | ln, Δln | 일 | ★비-USD numeraire 별도 구축 필수(Q4) |
| real_rate | DFII10 (10Y TIPS CMT) + DFII5 robustness | level, Δ(bp) | 일 | TIPS 2003~. pre-2003 = nominal − survey 기대인플레 bridge |
| breakeven | T10YIE (= DGS10 − DFII10 항등식) | level, Δ | 일 | ★Q2 항등식 게이트: {real_rate, BE} 고정, nominal 제외 |
| dollar | **DTWEXBGS broad TWI** (1차) + DXY (단기 robustness) | ln, Δln | 일 | DXY EUR 편중. de-dollar 서사엔 broad TWI 우선 |
| credit | BAMLH0A0HYM2 (HY OAS) + BAMLC0A0CM (IG OAS) | level/Δ | 일 | + MOVE(채권 vol) 별도 regime 변수 |
| cb_demand | WGC 분기 순매수(톤) + IMF COFER | level/누적 stock | 분기 | **latent — Kalman 보간 (Q5), 일별 Δ 금지** |
| risk | **GPR (Caldara-Iacoviello 일별, 무료)** + VIX | level/Δ | 일 | force_include 5번째 (Q8, Claude 안) |

### 식별상 결정적 두 함정 (실무 구현)

1. **항등식 collinearity gate** (Q2 합의: Claude 안 채택)
   - real = nominal − breakeven 완전 항등식. nominal·real·BE 셋 동시 포함 시 precision matrix 발산.
   - basis 고정: **{real_rate, breakeven}** (nominal 제외). 이유: 금의 정준 driver 는 real yield (Erb-Harvey 2013), {nominal, BE} 는 nominal 내 real+inflation 혼합으로 통계적으로 지저분.
   - 정량 게이트: VIF(real_rate, breakeven) < 5 (실측 2~3 예상), 2변수 design condition number < 30. 검증: nominal 추가 시 VIF > 10 발산 1회 확인.

2. **gold-USD numeraire endogeneity** (Q4 합의)
   - ln(gold_USD)·ln(dollar) USD 분모 공유 → 기계적 음의 편향. 단 전부 artifact 아님 — 진성 dollar 헤지 채널 + 분모 효과 중첩.
   - 비-USD numeraire 별도 구축: gold/SDR (IMF 일별 공시 → 자명) 1차, USD-제외 바스켓(EUR/JPY/CNY/GBP) robustness.
   - dollar β 약화 예상: gold/SDR 30~50%, USD-제외 바스켓 50~70%. **식별 성공 기준**: 양쪽에서 dollar β 동일 부호·동일 자릿수 수렴(부호 역전·소실 시 trap 지배).

### 시계열 해상도·기간 (합의)
- **일별** = Δ-beta(트레이딩 신호), partial-corr glasso, e-process
- **주별** = CFTC COT positioning, ETF flows
- **월별** = cointegration / level 회귀, GRAM 대조
- **분기** = cb_demand 톤수 validation

**기간 사전 분할 금지** — endogenous break 로 찾기. 후보(pre-2003 / 2003–07 / 2008–12 / 2013–19 / 2020–21 / 2022–26)는 검증 대상이지 가정 아님. **결정적 falsification 설계**: level intercept 데이터-주도 break 가 2022Q3~2024 + Δ-beta break 그 시점 없음 → "beta-stable, level-shifted" 확정.

### 통계기법 → 가설 매핑 (R2 합의)

| 기법 | 답하는 질문 | 공간 | 역할 |
|---|---|---|---|
| rolling Pearson/Spearman (Δ) | Δ-beta 안정성 | 변화율 | H1 진단 layer 1 |
| recursive/rolling OLS β, Bai-Perron / QLR sup-F | Δ-beta break | 변화율 | H1 진단 layer 2 |
| Johansen + **Gregory-Hansen** (regime-shift cointegration) | level 균형·break | 수준 | ★H2 핵심 |
| **VECM/ECM** | level 균형항 + 단기 Δ 동시 분해 (γ vs β) | 교량 | ★H2 vs H7 분리 |
| Bayesian State-Space (α(t)=RW latent) | online intercept shift 모니터 | 수준 | VECM 통과 후 monitor |
| Granger (Δ) | 선행성 (구조인과 아님) | 변화율 | H3 보조 |
| Bayesian SVAR (sign restriction) | monetary shock vs haven shock 구조분리 | 둘 다 | 식별 |
| Markov regime-switching (Hamilton 1989) | safe-haven 부호 국면전환 | 변화율 | H5 |
| TVP-VAR (SV) | β·γ 연속 시변 | 둘 다 | robustness |
| partial-corr glasso | 직접 edge vs 공통요인 매개 | 변화율(빈도매칭) | H4·H6 |
| e-process / test martingale (이중) | 온라인 break 탐지 | 둘 다 | ★H8 ordering |

### VECM/ECM 분해 (Q1 합의: 1차 구조 프레임)

```
Δln_gold_t = γ·(ln_gold_{t-1} − [α + b·real_rate_{t-1} + c·ln_dollar_{t-1}])
             └────────── 장기균형(level) 오차수정 ──────────┘
           + Σ β_i·Δx_{t-i} + ε_t
             └─ 단기 Δ-beta ─┘
```
- β = 변화율 베타 (실측 v1 안정).
- γ = 오차수정속도 = "금이 금리·달러가 함의하는 균형수준으로 되돌아가려는 힘."
- **decoupling 두 flavor 분리**: (i) 균형식 자체 이동 (α/cointegrating vector break) = H2 vs (ii) γ 붕괴 (균형 회귀 X) = H7.

### Q1 sequential hybrid (합의)
- **Offline calibration & falsification**: VECM + Gregory-Hansen — break 시점 확정, β cointegrating vector 추정. decoupling falsifiability 거주.
- **Online monitoring**: Bayesian State-Space — VECM 의 cointegrating vector 를 prior 로 주입, α(t)=random walk latent 로 켤레/Kalman 업데이트. posterior α(t) → e-process(Q6) level 잔차 채널 직결.
- **논리적 선결조건**: State-Space 단독으로는 "진성 cointegration + 1회 break" 와 "spurious regression 에서 α(t) 가 단위근을 흡수" 를 구분 못함 → VECM 먼저 구조 검증.

### 식별전략 (합의)
- **common factor 분리**: {real_rate, front-end, dollar} 1st PC = "US monetary factor" → gold = factor + 잔차 회귀 → glasso partial edge 교차검증.
- **내생성 차단**: 비-USD gold + SVAR sign restriction (monetary shock: real↑·dollar↑·gold↓ / haven shock: gold↑·GPR↑·dollar 불명).
- **잠재변수 보간 Kalman 채택** (Q5): cb_demand = state-space/Kalman smooth + 분기 WGC validate (= 원래 alt B 의 latent 정식화). spline 은 look-ahead 위배 — robustness ablation 에서만 허용.

### Q7 차원 스케일링 전처리 파이프라인 (필수)
**glasso → partial/marginal 변환 → 표준화 → e-process** — 다요인 prior 를 marginal pairwise 에 맨몸으로 섞는 것 금지. Claude 의 정밀안:
- glasso 정밀행렬(Q2) 으로 factor 공분산 구조 확보 → prior 를 marginal 공간에 사영(또는 partial 그대로 유지하되 e-process 의 귀무도 partial 량으로 정의)
- 전 factor 를 rolling window 단위분산 표준화 (dimensional scaling)
- level 검정 = VECM 다변량 잔차 1개 e-process / Δ-beta 검정 = 각 factor 의 partial innovation e-process

---

## ③ 핵심 가설 H1~H8 (반증조건 정량, R2 합의)

### H1 — 변화율 베타 안정
- **명제**: Δln_gold 의 Δ(DFII10) 민감도 β(Δln_dollar 통제) 가 2003–2026 구조적 안정
- **3-layer 통합 반증 (Claude H8 + Gemini H1)**:
  - (진단) 252d rolling Pearson 이 음부호 유지·반전 없음 (실측 v1 16y 0회)
  - (형식 순차검정) Bai-Perron / QLR sup-F β break p<0.05 AND post-break |β| pre-2022 대비 30%↑ 차이
  - (분해 검증, H8) Δ-beta e-process 가 level e-process 보다 후행 돌파
- 위 셋 중 어느 하나라도 위배 → H1 재해석 트리거.

### H2 — level intercept shift (★ v1 reframe 의 척추)
- **명제**: ln_gold ~ α + b·real_rate + c·ln_dollar 의 절편 α 가 2022Q3~2024 상향 break, Δ-beta 불변
- **반증**: Gregory-Hansen 미기각(level break 없음); 또는 Δα 95% CI 0 포함; 또는 Bai-Perron 주 break 가 절편 α 아닌 기울기 b
- **정량 기대**: {real_rate, dollar}로 설명 안 되는 gold-level 재평가 ≥15% (2022-2025)

### H3 — cb_demand 가 절편을 운반
- **명제**: level 잔차의 smooth trend (Kalman) 가 누적 CB 순매수(WGC 분기 톤수 stock)와 cointegrate / Granger
- **반증**: Kalman-smoothed residual_trend ↔ 누적 톤수 corr < 0.5 (2010–2025); 또는 Johansen trace 5% 미달; 또는 residual_trend break 가 CB 매수 가속(2022)보다 >2분기 선행 → 원인이 fiscal/debasement 등 다른 채널

### H4 — sys_priors β reconciliation dimensional gate
- **명제**: prior β_rate=−0.5, β_dollar=−0.8 의 객체 정의(빈도·표준화·numeraire) reconciliation. 양 모델 가설 갈림 → 실측으로 종결:
  - Claude case-4: 월/분기 표준화 regime-conditioned loading (저빈도 noise 감소·관계 강한 국면 평균)
  - Gemini case-1: 일별 표준화 다중 로딩 (공선성 통제 partial)
- **공통 정량 게이트**: 빈도·numeraire 일치 재추정 후 일별 표준화 다중회귀에서 |β̂_rate| < 0.40 AND |β̂_dollar| < 0.55 → prior 크기 기각 → posterior shrink
- **dollar β numeraire trap 보정 후 감쇠 예상**: 30~50% (-0.8 → -0.40~-0.55)
- **실측으로 닫는 항목** (자문 아닌 구현으로)

### H5 — safe-haven 부호 국면의존
- **명제**: gold credit/equity-risk partial corr 가 risk-off 음 / risk-on ≈0~양 (Baur-Lucey 2010)
- **반증**: 2-state Markov-switching 두 state 동부호(전환 없음); 또는 smoothed regime prob 위기(2008·2020·2022) prob>0.6 정렬 실패

### H6 — breakeven common-cause / 항등식 게이트
- **명제**: real=nominal−BE 항등식 → 명목금리·기대인플레 채널 상쇄
- **반증**: basis {real_rate, breakeven}(nominal 제외) partial-corr 에서 gold-BE |partial|>0.20 AND gold-real |partial|<0.20 → "real rate 추종·BE 무차별" 구조 기각, 독립 인플레기대 채널 지지
- **edge case**: glasso 가 nominal+real+BE 동시 포함 시 무효 — 사전 차단

### H7 — 오차수정속도 γ 가 decoupling 운반 (베타 아님) + 지정학 평균·tail 비선형 통합
- **명제 (γ 분해)**: VECM 에서 decoupling 이 단기 Δ-beta 아닌 γ 하락으로 발현
- **반증 (γ)**: rolling γ 유의 하락 없음(|Δγ|/γ<30%) AND cointegration 유지 → 대신 "균형식 자체 이동(새 cointegrating vector)" H2 flavor 우세
- **명제 (지정학 통합)**: GPR 이 force_include 5번째로 평균 채널(safe-haven 평균) 담당 + tail-amplified
- **반증 (지정학)**: q90 GPR 계수 ≈ OLS GPR 계수 (유의 차이 없음) → safe-haven 선형(국면비의존)·H5 와 모순

### H8 — anytime-valid 이중 e-process + ordering falsification
- **명제**: Δ-beta e-process (귀무 "Δ-beta=pre-2022 calibration") + level 잔차 e-process (귀무 "균형식 안정"). e>20 (α=0.05).
- **분해 확정 조건**: level e-process > 20 돌파하는 동안 Δ-beta e-process < 5 유지
- **분해 falsified**: Δ-beta e-process 가 level e-process 보다 먼저 20 돌파 → "beta-stable·level-shifted" 순서 모순 → H1·H2 분해 재해석 트리거

---

## ④ R2 수렴 결정 8항목 (정량 임계 박제)

| Q | 결정 | Confidence | 정량 임계 |
|---|---|:---:|---|
| Q1 | VECM(offline) + State-Space(online) sequential hybrid | 4 | Gregory-Hansen p<0.05 AND break 시점 ∈ [2022Q3, 2024]; State-Space α(t) posterior +3σ 이탈 → level-shifted 확정 |
| Q2 | **basis = {real_rate, breakeven}**, nominal 제외 (Claude 안) | 5 | VIF(real, BE) < 5, condition number < 30; nominal 추가 시 VIF>10 발산 1회 확인 |
| Q3 | sys_priors case-1 vs case-4 갈림 → **실측으로 종결** | 3 | 빈도·numeraire 일치 후 \|β̂_rate\|<0.40 AND \|β̂_dollar\|<0.55 → prior 기각·shrink. dollar β 감쇠 30~50% |
| Q4 | **gold/SDR 1차 채택**, USD-제외 바스켓 robustness | 5 | gold/SDR vs USD-제외 바스켓에서 dollar β 동일 부호·동일 자릿수 수렴 시 식별 성공 |
| Q5 | **Kalman smoother 채택** (spline = robustness ablation 만) | 4 | Kalman 평활 일별 누적 vs 분기 WGC 실측 오차 < 5%; residual_trend ↔ 누적 톤수 \|corr\| > 0.5 (4 보간법 robust ±0.1) |
| Q6 | **이중 e-process + ordering falsification 채택** | 5 | e > 20 (α=0.05); 분해 확정 = level e>20 + Δ-beta e<5; falsified = Δ-beta 선돌파 |
| Q7 | **차원 스케일링 전처리 파이프라인 채택** (glasso → partial/marginal 변환 → 표준화 → e-process). 다요인 prior + pairwise 맨몸 혼용 금지 | 4 | 표준화 후 factor partial β scale 단위분산 일치; marginal 사영 전후 e-value 동결론(>20 / <5) robust |
| Q8 | **force_include = {real_rate, breakeven, ln_dollar, cb_demand, GPR}** = 5개 (Claude 안). oil 명시 제외. credit = glasso 결정 | 4 | BE 탈락 시 real β > 20% 변화 → 승격 정당. credit: GPR 통제 후 partial \|β\|<0.10 OR edge 소멸 → 탈락 확정 |

### Q2·Q8 갈림 처리 결정 (Claude 안 채택 사유)
- **Q2**: Claude {real_rate, BE} (Conf 5, Erb-Harvey 이론 정합 + VIF 정량 + nominal 추가 시 발산 검증 1회) vs Gemini {nominal, BE} (Conf 4). → Claude 안. **이론적 anchor 가 결정적** (real rate 가 금 학술의 정준 driver).
- **Q8**: Claude {real_rate, BE, dollar, cb_demand, GPR} 5개 (BE common-cause 통제 목적 force_include 승격) vs Gemini {nominal, BE, dollar, cb_demand} 4개 (GPR 조건부 regime-switching). → Claude 안. **Q2 basis 결정과 정합**.

---

## ⑤ R3 진입 → "조건부 결과 조정 트리거" 로 재정의

양 모델 R3 design advisory 라운드 **불필요** 자체 선언. 본 direction.md 가 R2 최종 spec. **R3 는 조건부 트리거** (3 발동 조건 중 하나 발생 시 소집):
1. **Gregory-Hansen 이 2022Q3~2024 window 에서 break 미탐지** → H2 자체 재해석 필요
2. **이중 e-process ordering 위배** (Δ-beta 가 level 보다 선돌파) → H1·H2 분해 자체 재해석
3. **numeraire 보정 후에도 dollar β 감쇠 < 20%** → numeraire trap 가설 강도 재조정

위 셋 모두 불발 시 R2 합의 = 최종 설계 spec, 자문 종결.

---

## ⑥ 2-2/2-3 진행 가이드 (main 승인 후)

main 승인 시 본 direction.md 의 ①②③ 따라 다음 단계 진행:

### 2-2 [이론 학습]
- raw/theory-notes.md 작성. 우선순위:
  1. **Barsky-Summers 1988** 전문 (level 관계 이론 母船)
  2. **WGC GVF/GRAM** 방법론 백서 (산업표준 대조군)
  3. **Erb-Harvey 2013** + **O'Connor 2015 survey** (효율적 진입)
  4. **Pukthuanthong-Roll 2011** + **Reboredo 2013** (numeraire trap)
  5. **Arslanalp 등 2023** + **Caldara-Iacoviello 2022** (de-dollarization + GPR)
- **Dalio narrative** 은 색채로만, 학술 anchor 아님 (피인용 금지).

### 2-3 [실데이터 시계열 검증→코드화]
- raw/validation-{지표}.md 강제. 각 H1~H8 별로 별도 검증 산출:
  - validation-H1-beta-stability.md (rolling β, Bai-Perron, 3 layer)
  - validation-H2-level-intercept.md (VECM, Gregory-Hansen)
  - validation-H3-cb-demand-trend.md (Kalman + Johansen)
  - validation-H4-sys-priors-reconciliation.md (4 case 결판 — 핵심)
  - validation-H5-safe-haven-regime.md (Markov-switching)
  - validation-H6-breakeven-common-cause.md (partial-corr glasso)
  - validation-H7-gamma-decomposition.md (VECM γ + GPR q90)
  - validation-H8-dual-eprocess.md (anytime-valid ordering)
- 위 검증 후 study_session.yaml (7블록) 작성. blocks:
  - 블록1 lens: 본 direction.md ①②③ 정제 (level intercept shift 척추, R2 합의 narrative)
  - 블록3 relationships: 5 force_include + glasso 결정 변수. force_include ≤ 4 제약은 **★재검토** (R2 합의는 5개 — main 협의 필요 또는 cb_demand·GPR 중 하나 강등)
  - 블록4 weight_rules: WGC GRAM 4범주 + breakeven confounder
  - 블록5 confidence_hooks: H1·H2·H4·H8 매핑 (이중 e-process + Bai-Perron + dimensional gate)
  - 블록6 collector_plan: gold/SDR 시리즈, GPR Index, WGC 분기 톤수 Kalman 잠재변수
  - 블록7 code_change_plan: VECM 모듈, Bayesian State-Space monitor, glasso 항등식 게이트, e-process 이중 분해, 차원 스케일링 전처리

### ⚠ force_include ≤ 4 제약 vs R2 합의 5개 — main 협의 사항
- study_loader.py MAX_FORCE_INCLUDE=4 제약. R2 합의 = 5개 ({real_rate, BE, dollar, cb_demand, GPR}).
- 옵션 (a) BE 를 force_include 아닌 항등식 basis 만 pin (yaml 외부 처리), force_include = 4 유지
- 옵션 (b) GPR 을 conditional regime 변수 (Gemini 안) 로 강등, force_include = 4
- 옵션 (c) MAX_FORCE_INCLUDE 상향 (코드 변경)
- → main 의 판정 필요. 본 direction.md 는 (a) 또는 (b) 권고 — Q2 basis 핵심 제약은 외부 항등식 가드로 보장 가능.

---

## ⑦ 자문 메타 (감사)
- 자문 채널: gemini-web (Gemini Pro) + claude-web (Opus 4.8 High via claude.ai/new) 병렬
- 라운드 수: 2 (R1 광범위 brainstorm + R2 수렴 결정)
- 토큰 비용: R1 = 5439 + 12964 chars, R2 = 5361 + 8476 chars
- 자문 종결 사유: 양 모델 R3 불필요 자체 선언 + 핵심 8 Q 합의·정량 임계 결정
- raw 보존: round-1-{gemini,claude}.md + round-2-{gemini,claude}.md + 각 prompt 4 파일. 폴백 트리거 미발생.
- **다음 게이트**: main 승인 → 2-2 이론 학습 → 2-3 실데이터 검증 → study_session.yaml.
