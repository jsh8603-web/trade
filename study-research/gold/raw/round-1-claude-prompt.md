# R1 자문 — Claude Web (gold lens v2, 기본 옵션)

## §0 자문 맥락
- 라운드: R1 / 총 3~7R 수렴 예정. 이전 자문 없음(v2 첫 라운드, v1 산출은 자문 없이 만들어 main 거부).
- v1 실측 발견(인용): real_rate↔gold 16년 일별 Pearson 전체 -0.318, pre2020 -0.310, 2022-26 -0.304(불변). rolling 252d 부호반전 0회(median -0.349, max -0.009). dollar↔gold 도 -0.310→-0.377 강화. breakeven↔gold 직접 +0.04.
- 가설 reframe: 통설의 "2022-2024 real-rate decoupling" 은 *변화율 베타* 약화가 아니라 *수준(level) intercept shift* (real rate 상승에도 금 신고가)일 가능성.
- sys_priors gold factor loading `[-0.5 rate, -0.8 dollar, 0 oil, -0.2 credit]` 절댓값이 실측 일별 Pearson corr(-0.32/-0.33) 대비 약 2배 — factor-model standardized β 라면 정합 가능, 아니면 과추정.

## §1 문제 정의
gold(금) 단일 자산을 partial-corr glasso prior + e-process anytime-valid + Bayesian regime 기반 자율 트레이딩 시스템에 편입. 설계 산출 = lens(블록1 정성 anchor) + 5-driver 관계(블록3) + 동적 가중치(블록4) + flag 갱신 경로(블록5). 결정론 baseline + LLM down-only 감쇠(가중치 깎기만, 키울 수 없음). 본 R1 의 목표 = 이론 수집방향·이론 검증방향·핵심 가설초안(반증조건 포함) 의 완전성 향상.

## §2 제약·요구사항
- partial-corr 필수, conditioning_set 명시(빈 셋이어도), force_include ≤ 4
- 변수 정의 + 시계열 해상도·기간 + 통계기법 + 식별전략 모두 구체
- 정량 임계 필수(반증조건은 숫자)
- "변화율 베타 안정 vs level intercept shift" 분해 가설 필수
- sys_priors β 절댓값 reconciliation
- 학술/공식문서 인용은 제목·저자·연도까지

## §3 검토 중인 대안
- A: 5-driver 변화율 패널 (real_rate · dollar · breakeven · credit · cb_demand) — v1 방향
- B: level 회귀 분해 — ln_gold ~ a + b·real_rate + c·ln_dollar + residual_trend, residual_trend ↔ cb_demand
- C: standardized factor β reconciliation — Grinold IC·Ω 정합 vs 일별 Pearson corr 의 dimensional consistency 게이트

## §4 질문 (3축)

### ① 이론 수집 방향
금 가격결정 메커니즘을 이해하려면 반드시 정독해야 할 자료 우선순위 + 구체 제목/저자/연도:
- (a) 학술논문 5~10개
- (b) 교과서·monograph 3~5개
- (c) 공식 보고서 5~10개 (IMF/BIS/Fed/WGC/LBMA)
- (d) 셀사이드·매크로 리서치 (Bridgewater/GMO/HSBC/Goldman commodities)

### ② 이론 검증 방향
- 변수 정의 (real_rate · gold · dollar · cb_demand · breakeven · credit 의 구체 시리즈)
- 시계열 해상도·기간 (일/주/월, 구조파괴 구간 분할)
- 통계기법 (rolling Pearson/Spearman, Johansen cointegration, Granger, Markov regime-switching, Bayesian SVAR, Bai-Perron/QLR, TVP-VAR, partial-corr glasso, e-process anytime-valid 의 가설별 매핑)
- 식별전략 (common factor 분리, 내생성 차단, 잠재변수 보간)

### ③ 핵심 가설 초안 (반증조건 포함, 5~8개)
형식 = {명제·변수·기간·통계반증조건(정량)}.
- 변화율 베타 안정 vs level intercept shift 분해 필수
- sys_priors β reconciliation 가설 포함
- safe-haven 부호 국면의존, breakeven common_cause 분해, 추가 자유 제안

Claude Web 의 강점: fresh Opus + 실무 구현 관점. Gemini 와 의도적으로 독립 — 다른 가설·다른 자료·다른 통계기법을 제시해도 환영(둘의 차이가 R2 수렴 재료).
