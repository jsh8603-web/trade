# gold §2-2 이론 학습 정리 (theory-notes.md)

> **자료 출처**: direction.md ① 우선순위 5 + WGC GVF/GRAM. 본 노트 = 자문(R1/R2) 응답 + WebSearch 캡처(`raw/theory-fetched/native-websearch-20260530.txt` + `~/.claude/memory/research/gold-theory-foundations.md`) + 학술 지식 종합·소화.
> **주의**: ✓ = 출처 확정 / ◇ = 메모리 기반 고신뢰, 본문 인용 전 권호·페이지 재확인. Dalio narrative = 색채 anchor 만, 학술 anchor 절대 아님(R2 Claude 보수 판정 수용).

---

## §1 금 가격결정 메커니즘 — 이론적 母船 (Barsky-Summers 1988)

### 1-1 핵심 명제 (NBER w1680, JPE 96(3) 528–550, June 1988)
- **금의 균형 *상대가격* 은 실질 자본 생산성(real rate) 의 함수**. 실질수익률 상승 충격 → 금의 상대가격 하락. 금본위제 하 명목 금가격이 peg 됐을 때, 이것이 "가격수준 = 금 실질가격의 역수" 인 관계를 통해 가격수준 상승으로 발현 → **Gibson's Paradox**(가격수준-명목금리 정의 상관) 해명.
- 메커니즘 = 금의 **화폐적(monetary) vs 비화폐적(non-monetary) 사용 간 배분**. 금은 내구재 자산 → 실질 생산성 충격이 그 *상대가격* 을 체계적으로 흔든다. 동일 충격이 *실질금리* 도 결정 → 금↔실질금리 link 가 *level*(수준) 관계로 정립.
- **"opportunity cost effect" 프레임워크 개척**: 실질금리 상승 → 자본 재배분(금→이자자산) → 금 가격 억압. 후속 모든 매크로 금 모델(WGC GRAM 의 "opportunity cost" 카테고리 포함)의 직계 조상.

### 1-2 Inv 시스템 함의 (★H2 의 이론적 母船)
- 통설의 "2022-2024 real-rate decoupling" 이 *변화율 베타* 약화가 아니라 *수준 관계의 균형식 자체 이동* 일 때, 그 cointegrating vector 의 한 단자가 곧 Barsky-Summers level 관계: `ln_gold ~ α + b·real_rate + c·ln_dollar`.
- v1 실측(일별 변화율 16y -0.318/-0.310/-0.304 불변, rolling 252d 부호반전 0회)은 변화율 β 안정. RBC(2025.6) 의 TIPS-gold *level* R² 2005-2021 84% → 2022-23 3% → 2024+ 7% 붕괴는 *수준* 균형식 이동 — 두 사실의 양립 가능성을 Barsky-Summers level 관계가 제공한다.
- 따라서 H2(level intercept shift) 의 ★학술 anchor 1순위.

### 1-3 보완 학술
- **Erb-Harvey 2013** "The Golden Dilemma" FAJ 69(4) — "golden constant"(수세기 단위 실질가격 평균회귀, Jastram 1977 의 정량화), 인플레 헤지 horizon 의존성(짧은 horizon 에선 hedge 실패), 신흥국 보유 증가 → 실질가격 영구 상향 가능성 = cb_demand intercept shift 의 선구적 논의.
- **Jastram 1977** *The Golden Constant* (Leyland 2009 증보) — 1560-1976 영·미 금 실질가격 시계열. 수세기 구매력 불변 명제 원전.

---

## §2 산업표준 결정론 모델 — WGC GVF/GRAM

### 2-1 WGC Gold Return Attribution Model (GRAM) ✓
- **Multiple regression of monthly gold price returns**. ★본 시스템의 결정론 baseline 의 산업표준 대조군.
- **4 thematic driver categories**:
  1. **Opportunity cost** — real yields, dollar (Barsky-Summers 의 직계 후예)
  2. **Risk & uncertainty** — VIX, GPR(Caldara-Iacoviello 2022), credit spread 등
  3. **Economic expansion** — cyclical growth proxies (manufacturing PMI 등)
  4. **Momentum** — 가격 모멘텀(통상 t-1 ~ t-12)
- **방법론**: 월별 데이터, **5y rolling 추정창**. 각 driver 의 attribution 비중을 시계열적으로 추적.
- **사용**: WGC 정기 commentary·research(분기 Gold Demand Trends, Gold Outlook). driver-gold 관계 시변 추적 + 기존 driver 가 금 return 을 충분히 설명 못 하는 시기 식별 → *one-off circumstances · evolving dynamics · new effects* 진단 = 본 시스템의 "level residual / cb_demand 새 driver 부상" 판정의 산업표준 정합.

### 2-2 WGC Gold Valuation Framework (GVF) / Qaurum
- 수급(공급·산업수요·주얼리·투자·CB) 균형 기반 *implied return* 산출.
- Oxford Economics 시나리오와 결합해 향후 5-10년 시뮬레이션.
- 결정론(rule-based) 평가 + 시나리오 stress 의 정통 적용.

### 2-3 Inv 시스템 함의
- **dimensional reconciliation**: GRAM 은 *월별 다중회귀*. Inv 시스템은 *일별 신호*. 두 빈도 간 표준화 β 의 차이 (H4 dimensional gate) = 본 시스템의 sys_priors loading [-0.5/-0.8] 이 *월별 표준화 regime-conditioned* 평균 일 가능성(R2 Claude case-4 가설).
- **force_include ↔ GRAM 4범주 1:1 span**: 본 시스템 force_include={real_rate, ln_dollar, cb_demand, GPR} = GRAM {opportunity cost ×2, level-shifter(GRAM 외 신규), risk&uncertainty}. economic expansion 은 글로벌 cyclical 변수와 commodity 인덱스로 추가 가능하나 force_include 외(glasso 결정). momentum 은 별도 family.
- **WGC GDT(분기 Gold Demand Trends)** = cb_demand_proxy 의 1차 출처. 2024 년 CB 순매수 3년 연속 1,000톤+, 2024 Q4 333톤, 2024 전체 4,974톤(record).

---

## §3 Dollar 채널 + Numeraire Trap

### 3-1 Pukthuanthong-Roll 2011 "Gold and the Dollar (and the Euro, Pound, and Yen)" JBF 35(8) 2070-2083 ◇
- **핵심 통찰**: gold-dollar 관계는 **numeraire 선택에 본질적으로 의존**. ln(gold_USD) vs ln(dollar_index) 둘 다 USD 분모를 공유 → 기계적 음의 편향(mathematical artifact).
- 식별 전략: gold 를 비-USD numeraire (gold/EUR, gold/JPY, gold/GBP, gold/SDR) 로 표시 → numeraire artifact 분리 후 진성 dollar-hedge 채널 확인.
- 결과: 진성 채널은 존재(부호 보존)하나 USD-단독 numeraire 추정치는 *과대*.

### 3-2 Reboredo 2013 "Is gold a safe haven or a hedge for the US dollar?" JBF 37(8) 2665-2676 ✓
- Copula 기반 시변 의존구조 분석.
- gold 는 dollar **hedge**(상시 음의 의존)뿐 아니라 dollar 폭락 시 **safe haven**(꼬리 양의 의존 증폭)도 수행.
- 본 시스템 H6 의 dollar 채널 + H5 의 safe-haven 양면을 한 자산에서 관찰.

### 3-3 Capie·Mills·Wood 2005 "Gold as a hedge against the dollar" JIFMIM 15(4) 343-352 ✓
- 1971-2004 변동제 이후 시계열. dollar 헤지의 **시변·비선형성** 강조.
- 평시 약한 음의 상관 ↔ 위기 강한 음의 상관(safe-haven). Markov-switching 정식화의 전구.

### 3-4 Inv 시스템 함의 (Q4 numeraire trap 의 학술 근거)
- gold/SDR (IMF 일별 공시) 을 비-USD numeraire 1차 채택 → dollar β 의 진성 부분과 numeraire artifact 분리.
- gold/SDR 의 dollar β 는 gold_USD 대비 30~50% 약화 예상(SDR 바스켓 ~43% USD 잔존). USD-제외 바스켓(EUR/JPY/CNY/GBP)에선 50~70% 약화. 진성 채널 잔존 = 부호 보존(Reboredo).
- 즉 sys_priors β_dollar = -0.8 의 절댓값 일부는 numeraire artifact 로 설명되며, 보정 후 -0.40 ~ -0.55 수준 안정화 가능성(R2 합의).

---

## §4 Safe-haven 가설 + Caldara-Iacoviello GPR

### 4-1 Baur-Lucey 2010 "Is Gold a Hedge or a Safe Haven?" Fin Rev 45(2) 217-229 ✓
- **정의 분리**:
  - **Hedge**: 다른 자산과 상시 비양의 상관(평균적 양립).
  - **Safe haven**: 시장 극단 하락(crisis) 국면에서만 비양의 상관(꼬리 보호).
- 미·영·독 주식/채권 vs 금 분석. 금은 주식 hedge(주식과 평균 음의 상관) + crisis safe haven(주식 -2.5σ 하락 시 음의 상관 강화).
- 채권엔 safe haven 효과 없음(채권 자체가 위기 safe haven 이라).

### 4-2 Baur-McDermott 2010 "Is gold a safe haven? International evidence" JBF 34(8) 1886-1898 ◇
- 13개국 주식 vs 금. **국가·기간별 haven 속성 이질**: 선진국에선 강한 haven, 신흥국엔 약함. 1979-2009 기간 분석.
- 위기 정의에 따라 결과 민감 — Markov-switching 의 필요성 시사.

### 4-3 Caldara-Iacoviello 2022 "Measuring Geopolitical Risk" AER 112(4) 1194-1225 ◇
- **GPR Index**: 1900~ 현재, 일별 1985~. 1980 년 이후 11개 주요 지정학적 사건의 빈도·강도 기반.
- 무료, 일별 해상도, 외생적(시장 데이터 아님).
- Inv 시스템에서 **risk & uncertainty 의 tradeable 일별 프록시** — WGC GRAM 도 GPR 사용.

### 4-4 O'Connor·Lucey·Batten·Baur 2015 "The financial economics of gold — A survey" IRFA 41 186-205 ✓
- **★서베이 진입점**. 본 §1~§4 의 학술적 지도. 다루는 토픽:
  - 물리적 수급(공급·산업·주얼리)
  - 화폐적 채널(real rate, dollar)
  - safe-haven / hedge 분리
  - leasing rate / GOFO(Gold Forward Offered Rate)
  - 버블·행동재무
  - 투자수단(ETF, futures, options) 비교
- 후속 인용망의 허브. 신규 진입자가 가장 먼저 정독할 1 편.

### 4-5 Inv 시스템 함의 (H5 + H7 통합)
- H5 = safe-haven 부호 국면의존(Baur-Lucey 의 hedge vs haven 분리). 2-state Markov-switching 으로 위기 vs 평시 regime 분류, 두 state 에서 상관 부호 차이 |Δr| ≥ 0.20 검증.
- H7 = GPR 평균 채널(force_include 4번째) + tail-amplified(q90). q90 GPR 계수 ≈ OLS 계수면 safe-haven 선형(국면비의존) → H5 와 모순.
- Baur-Lucey 의 채널 분리가 R2 합의의 정식 출처.

---

## §5 De-dollarization + cb_demand Level Shift

### 5-1 Arslanalp·Eichengreen·Simpson-Bell 2023 "Gold as international reserves: A barbarous relic no more?" J Int Econ ◇
- 1999-2021 외환보유고 통화 구성 (IMF COFER) 분석. **USD 점유율 70.1%(1999) → 58.8%(2021), -11.3%p**.
- 단 그 자리를 차지한 것은 EUR/JPY 가 아닌 **비전통 reserve 통화(CAD, AUD, KRW, CNY 등) + 금**. 즉 "stealth erosion of dollar dominance".
- CB 금 보유 증가 메커니즘:
  - 미국 제재 무기화 우려(러시아 2022 자산 동결 사례) → 제재 대상국·잠재 대상국의 reserve 다변화 가속화.
  - 신흥국 CB 의 portfolio diversification 비중 (전통 안전자산 = US Treasury 의 정치적 위험 인식 상승).
- 본 시스템 H3(cb_demand level intercept 운반)의 ★실증 토대.

### 5-2 WGC Gold Demand Trends (분기) ✓
- 분기별 수요 4 구성: jewelry, investment(ETF + bar/coin), CB official sector, technology.
- 2024년 CB 순매수 3년 연속 1,000톤+ (2022-2024). 2024 전체 수요 4,974 톤(역대 최고).
- 매수 주체 상위(2022-2024): Türkiye, Poland, Singapore, China(공식), India. 중국은 2024-2025 PBoC 공식 갱신 휴지 후 재개 신호.

### 5-3 Inv 시스템 함의 (★H3 의 학술 + 실증)
- cb_demand_proxy = WGC 분기 CB 순매수 + IMF COFER reserve composition. 분기 → 일별 Kalman 보간(R2 Q5 합의).
- H3 = level 잔차의 smooth trend 가 누적 CB 순매수와 cointegrate / Granger. 정량 반증: |corr| < 0.5 OR Johansen trace 5% 미달 OR break > 2분기 선행.
- ★중요: cb_demand 가 *level intercept* 운반이지 *변화율 베타* 변경이 아님. R2 양 모델 합의 + 본 §1 Barsky-Summers level 관계와 정합.

---

## §6 지표 관계도 — gold 시스템 (거시 예시 동일 깊이)

### 6-1 거시 예시 reference (STUDY-KIT 부록 A 참조 톤)
"M2 ↔ 미·일 국채금리 ↔ 환율" 의 거시 정합 — 통화량 충격 → 명목금리 + breakeven → 실질금리 → 환율. 동등 깊이로 본 gold 시스템 관계도를 잡는다.

### 6-2 gold 시스템 지표 관계도 (5-driver core + 4 auxiliary)

```
                     [지정학 충격]                     [경기 cycle]
                          │                                 │
                          ▼                                 ▼
   [GPR] ──→ risk-off ──→ ───┐                         [WGC eco]
                              │                              │
                              ▼                              ▼
                          [credit OAS]               [breakeven]──(common cause via Fisher)
                              │                              │
                              ▼                              ▼
[CB official ─→ stealth ─→ [cb_demand]   ←─── opportunity cost path ───→  [real_rate]
   매수]   diversification  │  ─── level intercept α(t)  ───  ────→ [gold]
                              │                              ▲
                              ▼                              │
                          [dollar]  ←── numeraire artifact ──┘
                              │
                              ▼
                          [global Fed policy]
```

### 6-3 관계 명세 (★direction.md 블록3 의 학술 근거)
1. **real_rate → gold (-)**, Barsky-Summers level + Erb-Harvey opportunity cost. force_include 1.
2. **dollar → gold (-)**, Reboredo + Pukthuanthong-Roll(단 numeraire trap 으로 일부 artifact). force_include 2.
3. **cb_demand → gold (+, *level intercept 운반*)**, Arslanalp 2023 + WGC GDT. 변화율 단위 거의 직교, 수준 잔차에서만 작동. force_include 3.
4. **GPR → gold (+, 평균 + tail-amplified)**, Caldara-Iacoviello 2022 + Baur-Lucey safe-haven. force_include 4.
5. **breakeven → gold (≈0, common_cause via Fisher 항등식)**, real=nominal-BE → real_rate 조건화 시 직접 edge 소멸. ★force_include 아니지만 *항등식 basis* 외부 가드(`{real_rate, breakeven}` pin, VIF<5) 로 식별성 보장(main 의 옵션 (a) 채택).
6. credit_OAS → gold (국면 의존): 평시 양(safe-haven), 위기 초기 음(현금 확보). Markov-switching, glasso 결정.
7. eco_expansion → gold: GRAM 4번째. 일별 직접 영향 약함(분기), 별도 family 또는 manufacturer PMI 보조.
8. momentum (gold_mom_12_1) → gold: 자체 자기상관(family=momentum).
9. realized vol → gold: 일별 vol clustering, family=risk.

### 6-4 관계도 검증 매핑 (direction.md ② 통계기법 ↔ 본 §6 노드)
- real_rate↔gold(level): VECM γ/β 분해 + Gregory-Hansen
- real_rate↔gold(Δ): rolling Pearson + Bai-Perron
- dollar↔gold: numeraire ablation (gold_USD vs gold_SDR vs gold_basket)
- cb_demand↔gold(level intercept): Kalman smoothed residual trend + Johansen
- GPR↔gold(평균/tail): force_include + Quantile Regression q90
- breakeven↔gold(directness): partial-corr glasso conditioning_set={real_rate, dollar}

---

## §7 학술 vs Narrative 구분 — Bridgewater/Dalio 처리

### 7-1 Dalio Paradigm Shifts (2019) + The Changing World Order (2021) ◇
- 거시 narrative: 법정화폐 평가절하 사이클, 다극화 reserve 다변화, "the end of the dollar reserve currency era" 전망.
- 본 시스템 H2(level intercept shift) + H3(cb_demand 운반)의 **동기 부여 색채(color)** 로는 적합.

### 7-2 Claude R2 의 보수 판정 수용
- **Dalio narrative ≠ 학술 anchor**. peer-reviewed 아닌 실무/대중 서사. confirmatory/causal 인용 금지.
- H2 의 학술 anchor 는 (i) Barsky-Summers 1988 — level 관계 원전, (ii) Arslanalp 2023 — stealth dollar erosion 실증, (iii) WGC GDT 분기 official-sector demand 데이터, (iv) Caldara-Iacoviello 2022 — GPR.
- Dalio 는 audit trail 의 "color" 만, 결정/검정 인용 금지.

### 7-3 Bridgewater Daily Observations (금 시리즈) ◇
- 정기 발간 매크로 commentary. data-driven 이나 peer-reviewed 아님. 셀사이드 동급 취급(decoupling thesis 3문서 — T.Rowe/RBC/Apollo 와 정합).

---

## §8 시스템 wiring 함의 (direction.md ②③ → study_session.yaml 매핑)

### 8-1 lens(블록1) ← §1+§5+§7
- pricing_principle: Barsky-Summers level + opportunity cost + cb_demand level shift.
- report_relations: 위 6-3 의 9 항목 정제.
- regime_reading: Stagflation(real rate ↓ + inflation ↑) 강세, Recovery(real rate ↑ + risk-on) 약세 + 2022~ level intercept shift 단서.
- estimation_note: v1 실측 + RBC level R² 붕괴 + Arslanalp 실증 종합. H2 가 척추.

### 8-2 indicators(블록2) ← §2-3 + §3 + §4-3 + §5-2
- 7 지표 (실측 v1 산출 유지 + 정합 확인): real_rate_10y, dollar_index, breakeven_10y, credit_spread_hy_oas, gold_mom_12_1, gold_realized_vol, cb_demand_proxy. ★추가 검토: gpr_index(force_include 4번째 신규), gold_sdr(numeraire ablation).

### 8-3 relationships(블록3) ← §6-3
- 5 edges + conditioning_set 명시 + force_include 4 (BE 미포함, 항등식 basis 외부 가드).

### 8-4 weight_rules(블록4) ← §2-1 GRAM 4 카테고리 1:1
- {real_rate, dollar, cb_demand, GPR} sleeve 가중치 base + regime modulate. GRAM 의 정량 비중(2010-2025 평균) 을 prior 값으로 dispatch.

### 8-5 confidence_hooks(블록5) ← direction.md H1~H8
- 3 flag (real_rate_beta_holds, cb_demand_regime, safe_haven_holds) 의 confirm/reject_signal 을 §3-2(Reboredo)·§4-1(Baur-Lucey)·§1-1(Barsky-Summers) 학술 mechanism 으로 anchor.

### 8-6 collector_plan(블록6) ← §5-2 + §4-3
- 신규: FRED DFII10/T10YIE/DTWEXBGS(★검증 완료, v1 실측에 사용) + Caldara-Iacoviello GPR(matteoiacoviello.com 공식 페이지, 일별 free) + WGC quarterly GDT(public) + IMF SDR 일별 공시.

### 8-7 code_change_plan(블록7) ← R2 Q1·Q2·Q4·Q5·Q6·Q7
- ★항등식 collinearity gate (외부 가드 모듈): VIF<5, condition number<30, nominal 추가 시 발산 1회 검증.
- VECM/ECM (offline structure) + Bayesian State-Space α(t) (online monitor) sequential hybrid.
- gold/SDR numeraire ablation.
- Kalman smoother cb_demand 보간.
- 이중 e-process + ordering falsification (Δ-beta / level 잔차).
- 차원 스케일링 전처리 파이프라인 (glasso → partial/marginal 변환 → 표준화 → e-process).

---

## §9 미해결·재확인 항목 (2-3 진입 전 chk)
- ◇ Arslanalp·Eichengreen·Simpson-Bell 2023 의 정확한 J Int Econ 권호·페이지 (memory 표기 미확정 — 본문 인용 시 jstor/elsevier 직접 fetch 권장).
- ◇ Pukthuanthong-Roll 2011 페이지 마지막 자리 (2070-2083 vs 다른 표기) — JBF 공식 페이지 재확인.
- ◇ WGC GRAM 의 *정확한* 4 카테고리 변수 매핑 시계열 (2010 vs 2026 어떻게 갱신됐는지) — gold.org/goldhub 직접 fetch (현재 webfetch 404 — robust fetch 경로 필요).
- ◇ BIS 의 central bank gold WP 의 구체 제목 (R2 미확정) — bis.org 직접 검색 추후.
- 2-3 에서 우선 실데이터 검증 진입 후, 결정/인용 시 위 ◇ 항목 본문 인용 직전 확인.

---

## §10 자료 출처 박제 (감사)
- raw archive (글로벌): `~/.claude/docs/archive/research-raw/gold-theory-foundations-native-20260530.txt`
- memory 요약 (글로벌): `~/.claude/memory/research/gold-theory-foundations.md`
- study 방 raw: `study-research/gold/raw/theory-fetched/native-websearch-20260530.txt`
- 자문 raw (R1+R2): `study-research/gold/raw/round-{1,2}-{gemini,claude}.md`
- direction.md ① + ② + ③ 정합 매핑: 본 §1~§7 가 학술 anchor, §8 이 wiring 함의.
