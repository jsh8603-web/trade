---
tags: [type/consult-brief, domain/inv, study/eq_us, phase/3-R2]
date: 2026-05-31
study_id: eq_us
round: 2
target_channels: [gemini-web, claude-web]
prior_rounds: [R1 (raw: consult-round-1-{gemini,claude}.md)]
---

# eq_us Phase 3 R2 자문 브리핑 (빈틈 보충 + 환각 cross-verify)

## §0 이전 자문 맥락 (R1 결론 계층 — fresh session 매번 새 대화 대응)

본 자문 = eq_us 평가 시스템 설계 R2. R1 결과 (gemini-web 9k chars + claude-web 14k chars) 종합:

**R1 합의 (두 채널 일치)**:
- Q2 1순위 = Earnings Revision Breadth (ERB), 2순위 = Total Shareholder Yield (TSY)
- Q6 XLRE 분리 (eq_us = GICS 10 sector)
- Q8 skfolio CPCV + alphalens + Ken French FF5 (Claude 가 QMJ + BAB + BH + deflated Sharpe 추가)
- Q9 핵심 가설 = ERB / TSY / HY OAS regime / Mag7-AI capex 공통

**R1 ★disagree (R2 핵심 토픽)**:
| Q | Gemini 입장 | Claude 입장 |
|---|---|---|
| Q1 | Mag7 분리 + 10 GICS (단순) | Mag7 = GICS 3 파편화 (XLK=AAPL/MSFT/NVDA / XLC=GOOGL/META / XLY=AMZN/TSLA), 관측 = GICS 11 / 가중 = Mag7 격리 + macro-channel |
| Q2 3순위 | Fed funds path expectation | HY OAS regime (Fed/AI = regime conditioner) |
| Q3 | cyclical dollar 우위 = 구조적 (Bruno-Shin 2015) | ★표본 한정 (2022-24 collinearity artifact, ρ(rate,dollar) 0.7-0.8). R2 decay 0.21→0.07 = collinearity 깨지면 dollar 설명력 붕괴 증거 |
| Q5 | (c+d) Regime Cap (AI capex 30%+ regime Mag7 weight 상승) | ★(d) 명시 기각 (reflexive trap). (a)+(b)+(c) + reflexivity monitor (intra-Mag7 corr↑ + breadth 협소화 동시 = cascade flag → concentration 축소) |

**Claude R2 권고 3** (자체 제시):
1. Q3 2015-2019 sub-sample 재검 (dollar 구조성 판정)
2. Q5 reflexivity monitor 구체 spec
3. Q1 PCA-eff_N 실측 (Tier vs macro-sleeve 결정)

---

## §1 R2 빈틈 보충 6 질문

### QR2-1. cyclical dollar 채널 = 구조 vs 표본 한정 (R1 Q3 ★disagree)

Claude 가설: 2022-24 ρ(Δrate, Δdollar) 약 0.7-0.8 collinearity → dollar 가 rate 분산 흡수. epoch R² decay (E1 긴축 0.21 → E4 완화 0.07) = collinearity 깨지면 dollar 설명력 붕괴 증거. **2015-2019 sub-sample (rate ↔ dollar decoupled period)** 재검 시 β_dxy 가 -0.5 ~ -1.6 유지하면 구조적 (Gemini 가설 확인), 사라지면 표본 한정 (Claude 가설 확인).

검증 질문:
- (a) 2015-2019 sub-sample β_dxy 추정 — 학술 paper / 실무 리서치에서 보고된 값 있나? (예: Pedersen-Frazzini AQR, GS Macro Quant)
- (b) Bruno-Shin (2015) cross-border banking 메커니즘이 sector-level cross-sectional alpha 에 실제 도달하나, 또는 sovereign/bank balance sheet 수준만?
- (c) "dollar weight = ρ(Δrate, Δdollar) 조건부" 구체 구현 = sleeve weight 산정에 ρ 어떻게 입력? regime tag (예: low-ρ vs high-ρ 2 cell)?

### QR2-2. Mag7 regime cap 방향 (R1 Q5 ★정반대 disagree)

Gemini: AI capex yoy 30%+ regime = Mag7 weight **상승** (c+d). Claude: 그 (d) **기각** (reflexive trap), 대신 reflexivity monitor (intra-Mag7 corr↑ + breadth 협소화 → cascade flag → concentration **축소**).

검증 질문:
- (a) reflexivity monitor trigger 구체 spec: intra-Mag7 corr threshold (예: rolling 60d mean corr > 0.7)? breadth 정의 (NYSE A/D? S&P 500 EW vs CW return spread? % of stocks > 200dma?)? 동시 발생 의무?
- (b) 2023-2024 Mag7 dominance regime 에서 (d) cap-up vs (d) cap-down OOS Sharpe 어느 쪽 우월한 실측 또는 학술 사례?
- (c) **Mag7 concentration factor** 추출 가능? Mag7-등가중 vs S&P 493-등가중 return spread = Mag7 factor exposure. toraniko 의 "characteristic" 으로 추가 가능?

### QR2-3. PCA eff_N 실측 (R1 Claude Q1 H8 + R2 권고 #3)

가설: PCA on 11 sector returns 80% 분산에 >7 PC 필요 → Tier 11 GICS 독립 인정. ≤5 PC → macro-sleeve 우월.

검증 질문:
- (a) yfinance 11 sector ETF (XLB/C/E/F/I/K/P/U/V/Y + XLRE) 일별 return 2015-2024 PCA — 학술 baseline 또는 실무 리서치에서 보고된 eigenvalue/explained variance 가용?
- (b) Gemini Q1 의 "팩터 모델 R² 0.3-0.4 vs GICS 더미 R² 0.1-0.15" 주장 — robust 학술 source? (Asness 2000 이라 인용 — 실제 = Asness-Moskowitz-Pedersen 2013 JoF, ★연도 환각 의심)
- (c) 사용자 M3 measurement (within-cyclical mean corr 0.617, Kish eff_N 1.47) 가 cross-cyclical-defensive 차원까지 확장하면 eff_N 가 더 작아지나, 또는 cyclical-defensive 가 진짜 2 axis?

### QR2-4. shareholder yield + revision breadth crowding/decay 정량 (R1 Claude Q10 #4)

검증 질문:
- (a) McLean-Pontiff (2016) JF "Does Academic Research Destroy Stock Return Predictability?" decay 추정 ~58% — 정확? full 표본 N? 어느 factor 평균?
- (b) shareholder yield post-2010 decay 정량 — Boudoukh-Michaely-Richardson-Roberts (2007) JF "payout yield" 의 원본 alpha 대비 최근 실측 (BofA / JPM / GS 2020+ 리서치)?
- (c) revision breadth IC 0.03-0.06 post-2015 decay 여부 — Refinitiv/FactSet 데이터 retroactive 수정 영향?

### QR2-5. Mag7 GICS 3 sector 파편화 사실 확인 (R1 Claude Q1 ★finding)

Claude 주장: AAPL/MSFT/NVDA = XLK / GOOGL/META = XLC (2018 GICS Communication Services 신설 후) / AMZN/TSLA = XLY (Consumer Discretionary).

검증 질문:
- (a) 2018 GICS Comm Services 신설 정확한 날짜? (MSCI/S&P 공식 발표 시점)
- (b) 현재 Mag7 GICS 분포 + S&P 500 weight 별 정확한 percentage (2024-Q4 또는 2025-Q1 기준)?
- (c) 사용자 의도 "T1 = XLK + XLC = 시총 50%+" 가 사실상 깨지면, T1 재정의 = **Mag7 + AI 인접 large cap** (예: AVGO, ORCL, ASML US ADR) 으로 재구성 가능?

### QR2-6. R1 reference 환각 cross-verify (DA-20260422 hallucination-check 의무)

각 reference 의 (a) 실재 여부 (b) 정확한 저자/연도/저널 (c) 본 자문 주제 직접 관련성 확인. 환각 발견 시 정정 + 대체 reference 권고.

**Gemini R1 cited references** (★환각 의심 우선):
1. **Asness et al. (2000) "Value and Momentum Everywhere"** → 실제 = Asness, Moskowitz, Pedersen (2013) JoF? Gemini 연도 오류?
2. **Ben-David et al. (2021) "Do ETFs Increase Volatility?"** → 실제 = Ben-David, Franzoni, Moussawi (2018) JoF? Gemini 연도 오류?
3. Novy-Marx (2013) "The Other Side of Value: The Gross Profitability Premium" JFE — 실재 확인
4. Bruno & Shin (2015) "Cross-border banking and global liquidity" Review of Economic Studies — 실재 확인 + 본 주제 관련성?
5. Fama & French (1997) "Industry costs of equity" JFE — 실재 확인
6. Ling & Naranjo (1999) "Real Estate Returns and the Macroeconomy" Real Estate Economics — 실재 확인
7. Elton et al. (1996) "Survivorship Bias and Mutual Fund Performance" RFS — 실재 확인
8. Marcos López de Prado (2018) Advances in Financial Machine Learning (Wiley) CPCV — 실재 확인
9. Brogaard et al. (2023) "The Impact of 0DTE Options on Stock Market Quality" — 실재 확인 (working paper)

**Claude R1 cited references** (★tentative 라벨 자체 정직):
1. Chan-Jegadeesh-Lakonishok (1996) JF (momentum/revision) — 정확한 제목?
2. Boudoukh-Michaely-Richardson-Roberts (2007) JF "payout yield" — 정확한 제목?
3. McLean-Pontiff (2016) JF "Does Academic Research Destroy Stock Return Predictability?" — 정확한 제목·decay 추정?
4. Weber (2018) JFE "cash flow duration & term structure of equity returns" — 실재 확인? 저자명 정확?
5. Gormsen-Lazarus equity yield — 실재 확인? 저자 (Gormsen Niels Joachim, Lazarus Eben)? 연도/저널?
6. Asness-Frazzini-Pedersen (2019) "Quality Minus Junk" — 실제 저널 = RAS? RFS? JoF?
7. Frazzini-Pedersen (2014) "Betting Against Beta" JFE — 실재 확인 + 정확한 저널
8. VanderWeele-Ding (2017) "E-value" Annals Intern Med — 정확한 제목 ("Sensitivity Analysis in Observational Research: Introducing the E-Value")?
9. Stickel (1991) analyst revision — 정확한 제목·저널?

---

## §2 출력 양식 (R1 과 동일)

각 QR2-1 ~ QR2-6 에 5 필드 응답:
- 답변 (1-3 paragraph, 결론 먼저, R1 결론 인지 기반)
- 근거 (학술 + 실무 + 1차 데이터 3중, 환각 우려 시 tentative 라벨)
- 정량 magnitude (range/CI 포함, 점추정 단독 X)
- 반증조건 (가설 답변 시)
- confound confidence (low/medium/high)

각 QR2 200-400 단어. QR2-6 환각 cross-verify 는 reference 별 1-2 sentence 답 + (a)(b)(c) 명시.

## §3 R2 핵심 메시지 (외부 모델 인지)

- 본 R2 = R1 disagree 해소 + 환각 cross-verify. 두 채널 비교 → R3 수렴 또는 direction.md 진입.
- 5 금지 R1 동일 적용 (점추정 X, 합성 X, 자문 그대로 X, single-source X, small-N X)
- R1 의 Claude epistemic discipline (tentative 라벨, hedge 어휘) 우선 — Gemini 도 동일 frame 채택 권장
