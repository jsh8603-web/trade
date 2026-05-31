# R1 자문 프롬프트 — Gemini Pro Web (gold lens 다회 수렴)

## §0 자문 맥락
- 라운드: R1 / 총 3~7R 수렴 예정. 이전 자문 없음(v2 첫 라운드, v1 산출은 자문 없이 만들어 main 거부).
- v1 실측 발견(인용): real_rate↔gold 16년 일별 Pearson 전체 -0.318, pre2020 -0.310, 2022-26 -0.304(불변). rolling 252d 부호반전 0회(median -0.349, max -0.009). dollar↔gold 도 -0.310→-0.377 강화. breakeven↔gold 직접 +0.04.
- 가설 reframe: 통설의 "2022-2024 real-rate decoupling" 은 *변화율 베타* 약화가 아니라 *수준(level) intercept shift* (real rate 상승에도 금 신고가)일 가능성. v1 실측은 변화율 단위 decoupling 가설을 기각.
- sys_priors gold factor loading `[-0.5 rate, -0.8 dollar, 0 oil, -0.2 credit]` 절댓값이 실측 일별 Pearson corr(-0.32/-0.33) 대비 약 2배 — factor-model standardized β 라면 정합 가능, 아니면 과추정.

## §1 문제 정의
gold(금) 단일 자산을 partial-corr glasso prior + e-process anytime-valid + Bayesian regime 기반 자율 트레이딩 시스템에 편입. 설계 산출 = lens(블록1 정성 anchor) + 5-driver 관계(블록3) + 동적 가중치(블록4) + flag 갱신 경로(블록5). 결정론 baseline + LLM down-only 감쇠(가중치 깎기만, 키울 수 없음). 본 R1 의 1차 목표 = 이론 수집방향·이론 검증방향·핵심 가설초안(반증조건 포함) 의 완전성 향상.

## §2 제약·요구사항
- partial-corr 필수, conditioning_set 명시(빈 셋이어도), force_include ≤ 4
- 변수 정의 + 시계열 해상도·기간 + 통계기법 + 식별전략 모두 구체
- 정량 임계 필수(반증조건은 숫자)
- "변화율 베타 안정 vs level intercept shift" 분해 가설 필수 — 둘은 다른 관계, 분리 검증
- sys_priors β 절댓값 reconciliation(factor-model standardized vs 일별 corr 의 차이 해명)
- 학술/공식문서 인용은 제목·저자·연도까지 구체

## §3 검토 중인 대안 (Claude 의 잠정안 — 반박/확장 환영)
- **A: 5-driver 변화율 패널** (real_rate · dollar · breakeven · credit · cb_demand) — v1 방향
- **B: level 회귀 분해** — ln_gold ~ a + b·real_rate + c·ln_dollar + residual_trend, residual_trend ↔ cb_demand 누적순매수
- **C: standardized factor β reconciliation** — Grinold IC·Ω 정합 vs 일별 Pearson corr 사이의 dimensional consistency 게이트(production wiring 전 필수)

## §4 질문 (3축 — 각 축당 충분한 depth, mock 거부)

### ① 이론 수집 방향
금 가격결정 메커니즘을 이해하려면 반드시 정독해야 할 자료(우선순위 + 구체 제목/저자/연도):
- (a) 학술논문 5~10개 — SSRN/NBER/JF/RFS 등에서. 예: Erb & Harvey "The Golden Dilemma" 류
- (b) 교과서·monograph 3~5개 — 저자·관련 장
- (c) 공식 보고서 5~10개 — IMF/BIS/Fed staff papers/World Gold Council(분기 Gold Demand Trends)/LBMA 구체 시리즈명
- (d) 셀사이드·매크로 리서치 — Bridgewater Daily Observations(금 관련)/GMO/HSBC/Goldman commodities/State Street 의 금 시리즈

### ② 이론 검증 방향
위 이론의 핵심 명제를 시계열로 어떻게 검증?
- **변수 정의**: real rate = TIPS 10Y(DFII10) vs ex-ante survey(Michigan/SPF) vs realized; gold = LBMA spot vs GLD ETF vs GC futures front-month vs CFTC speculative net long; dollar = DXY vs DTWEXBGS vs BIS NEER; cb_demand = WGC quarterly net purchases vs IMF IFS reserves data
- **시계열 해상도·기간**: 일/주/월, 1971 변동제 이후 vs post-1999 ECB 매도 이후(Washington Agreement) vs post-2008 vs post-2022(중앙은행 대거 매수 국면)
- **통계기법**: rolling Pearson/Spearman, cointegration(Johansen), Granger, regime-switching(Markov), Bayesian SVAR, structural breaks(Bai-Perron/QLR), rolling beta with TVP-VAR, partial-corr glasso, e-process anytime-valid 등 — 각 기법이 어떤 가설에 적합한지 매핑
- **식별전략**: common factor 분리(real_rate ↔ dollar 동조), 내생성 차단, 잠재변수(cb_demand 분기 데이터의 일/주 보간), level vs change 분해

### ③ 핵심 가설 초안 (반증조건 포함, 5~8개)
형식 = `{명제·변수·기간·통계반증조건(정량)}`. 반드시 포함할 것:
- H1: 변화율 베타 가설 — Δreal_rate ↔ Δgold 음의 상관 유지 (반증: 252d rolling Pearson 부호반전 또는 |r|<0.10 비율 베이스라인 3.1% × 3 초과)
- H2: level intercept shift 가설 — ln_gold = a(t) + b·real_rate + c·ln_dollar + ε, intercept a(t) 가 시기별 단계적 상승, 그 변화가 cb_demand 누적순매수와 양의 상관
- H3: dollar↔gold 관계의 강화 — 16y 첫 절반 -0.310 vs 후반 -0.377(★실측). 통계적 유의?
- H4: breakeven↔gold 직접 효과 부재(common_cause 분해) — partial-corr(conditioning_set={real_rate}) 가 0 근처
- H5: sys_priors β [-0.5/-0.8] 의 derivation — factor-model standardized 라면 합당한지, 일별 corr 와의 reconciliation 게이트
- H6: safe-haven 가설 부호의존성 — HY OAS↔gold 가 평시 양, 유동성위기 초기 음(부호 국면의존)
- H7+: 추가 가설 자유 제안

(질문 끝)
