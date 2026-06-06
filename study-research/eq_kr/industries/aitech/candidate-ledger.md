---
tags: [type/candidate-ledger, domain/equity, sector/aitech, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 AItech 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# AItech(인터넷·게임·소프트웨어) 지표 후보 원장

> ★핵심 발견: growth(battery 동형 momentum continuation) 사전가설 **데이터 반증** → momentum **reversal**(음) + ★valuation premium 강(pbr/per BY 생존 = primary tradeable). archetype = asset_stable/value 작동 + cyclical(peak reversal) 혼합.

## ✅ 채택 (검증 통과 — tradeable 후보)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| **pbr_z** (저PBR value) | value | ★VALIDATED_ALPHA | 12M IC −0.183 (t=−7.98), CPCV 1.00, within 1.00, ★BY 생존(m=8). walk-forward OOS y_60d −0.060→−0.123 강화. ★size 위장 아님(Fama-MacBeth t=−3.51) + LOO 전부 + ★좀비 면역(Δ=0.0 공시후진입). ★G-C audit = 12종목군 中 가장 강한 신호로 독립 재현, **코드화 자격 충족**. n=73, avgN 24 (24M overlap·26종 magnitude hedge). validation-valuation-v3.json |
| **per_z** (저PER value) | value | ❌격하(PARTIAL→격하) | 24M IC −0.129, BY 일부 생존이나 ★episode 종속(Q2 sub-period +0.044/−0.099 부호반전) + 게임 적자 40% 양수편의. → E/P 대체 권고. G-C audit 격하 유지. |
| **mom_12_1 / mom_6** (momentum **reversal**) | momentum | PASS-conditional | 12M IC −0.106/−0.103 (★좀비 마스킹 후 −0.0963, ~9% 과대 부호불변, t −2.58→−2.59). ★reversal(음=battery 반대). OOS 부호유지 + LOO 26종 전부 음. ★BY 미생존 + game dominant = 게임 종목 한정. low confidence. |
| **per_z × KRW_weak** (conditional) | value×regime | PASS-conditional | per_z y_60d KRW_weak wc_p=0.0025 (powered, n=34, IC −0.154). OOS IS −0.135→−0.159 강화. = 원화약세기 value 증폭. tentative(n<30 OOS=13). |
| **mom_12_1 × flow_strong_buy** (conditional) | momentum×regime | PASS-conditional | interaction t=−2.71 유의 + walk-forward OOS t=−2.71 재현. = 외국인 강매수기 reversal 증폭. tentative. |

## ⏳ 이연 (식별됐으나 미투입)

| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| EV/EBITDA | frame archetype primary(compounder) | DART 부채/현금 계정 추가 필요 (PBR/PER 만 산출) | DART fnlttSinglAcntAll 부채총계/현금성자산 + stockTotqySttus 주식수 |
| 종목레벨 외국인 flow | round-1 A4 | ★DATA-GATE = KRX 종목별 인증 차단(데이터 부재). 시장레벨 ECOS flow regime 은 측정완료 | KRX 인증 또는 ETF flow proxy |
| KR HY credit spread | cross common_factor | 현 = US BAML HY OAS proxy(n=35 small). KR 회사채 spread 유료 | 금융투자협회/한국신용평가 |
| DAU/MAU·광고매출 yoy·게임 신작 출시 ledger | frame Layer 3 AItech | 무료 정형 시계열 부재(각사 IR 수동), event study 형식 | 각사 분기 IR 수집 또는 앱애니/센서타워 유료 |
| hyperscaler capex yoy | frame Layer 3 AItech | AWS/Azure/GCP 합산 capex = 미국 클라우드, 한국 SaaS 간접수혜 mapping 불명확 | 분기 capex 수동 + mapping 검증 |
| PIT universe 멤버십 | 생존편향 I축 | FDR 현재 스냅샷만. ★게임주 상폐多(P2E 붕괴) = 생존편향 위험 큼 | KRX PIT 섹터분류 인증 |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| customer momentum (QQQ/NVDA forward) | ★전 lag 비유의(REJECTED). 한국 AItech = 글로벌 tech cycle contemporaneous 동조이나 forward 예측력 부재(§D falsifier 정상). RegimeGlasso Ω 흡수 |
| momentum **continuation**(양, growth 가설) | ★데이터 반증 — 실측 음(reversal). growth=battery 동형 사전가설 폐기 |
| VIX/oil/rate/dollar β (개별 tradeable) | 공통인자 β = 통합 supervisor Σ_return 입력(산업 보고만). rate 약 음(비유의), credit 만 유의 |
| macro Recovery interaction | 전 신호 interaction 비유의(main만 유의) = macro conditioning 약 |
| 24M_value magnitude literal | overlap degenerate(eff_indep_N≈2.5) + 26종 small-universe inflation → magnitude 보수 cap, 3M/6M/12M primary |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| pbr_z value premium | size factor 위장? (Asness 2013) 26종 small-universe t 과대? | Fama-MacBeth PBR\|Size 통제 후 유의 + breadth-adjusted IR |
| momentum reversal game dominant | internet 무신호 → 게임 비중 종목 한정 신호? 분리 필요? | sub-cluster 분리 측정 + game-only universe IC 재현 |
| per_z 적자종목 편의 | 게임 적자 40% 양수만 산출 = 생존 흑자종목 bias? | E/P(earnings yield, 음수익 처리) 대체 측정 |

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | ★pbr_z value premium = VALIDATED_ALPHA (G-C audit 독립 재현, BY 생존+size위장아님+LOO+좀비면역) | 검증된 정량 규칙 = 코드화 자격(conservative cap, small-universe hedge) |
| memory | ★growth≠momentum continuation (AItech 반증) = 성장주라도 momentum 부호는 데이터 판정 | 다음 cycle 자문 prior 정정 (battery growth 일반화 금지) |
| memory | ★AItech = 수출주 아니라 내수 성장주 (rotation usdkrw 부호 반증: 원화약세→AItech 약세 rho −0.364 wc_p 0.002) | 인터넷 NAVER/카카오 내수 + 게임 내수 + 원화약세=risk-off 외국인매도가 수출 환산효과 압도. 수출 수혜 가설 폐기 |
| observe-only | momentum reversal (BY 미생존, 좀비 마스킹 후 부호불변), per_z (episode 종속+적자 편의 격하), ★rotation game_espo(글로벌 게임 cycle +0.382 CI 0배제)+rate_10y(금리 음) 채택 | N 누적 후 promotion 결정 |
| evt | customer momentum REJECTED (§D forward falsifier 작동) / ★좀비 carry-forward(셀바스AI 284일) mom 오염 = G-C audit 정정 | 자문·audit 정정 사례 |
| pointer | frame M.11/M.12 (small-n haircut, peak-EPS, 24M degenerate) / ★거래정지 좀비 마스킹(amt==0/dup-price≥10일) = mom/vol 공통 오염원(bio·aitech 동일) | 다음 세션 SSOT 정독 우선순위 |
