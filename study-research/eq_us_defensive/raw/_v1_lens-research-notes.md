# eq_us_defensive — lens research notes (Step 1: 이론/리포트로 lens 먼저)

## 0. 자산군 범위 (task spec)

study_id = eq_us_defensive = **미국 방어주 + 금융주** (사용자 명시).

- 방어주 코어: XLP(Staples), XLU(Utilities), XLV(Healthcare), XLC mature(VZ/T/CMCSA)
- 금융: XLF(Banks/Insurance/Financial services)
- 분류상 financials = NOT classical defensive 이지만 task spec 그대로 한 sleeve 로 묶음
- intra-sleeve dispersion 강함 → industry archetype 강제 분해 필요

## 1. 가격결정 일반론 (pricing principle)

### 1.1 방어주 (Staples/Utilities/Healthcare/Comm mature)

P_def = M(real_rate, credit_spread, regulatory_regime, dividend_yield_alt) × E(stable, low_growth)

**핵심 메커니즘**:
- 매출이 경기 비탄력: 필수소비(staples)·규제수요(utilities)·인구학적 healthcare. 경기변동 → EPS 변동 작음.
- 마진 안정: 낮은 operating leverage, 낮은 financial leverage(예외=일부 utilities 부채↑).
- **장기 cash flow 채권 대체재**: 안정 배당 + 낮은 성장 → 자기현금흐름의 듀레이션 길다.
- 듀레이션 = real rate 충격에 multiple 압박. 단순 명목금리보다 실질금리(=TIPS yield) 가 결정적.

### 1.2 금융주 (Banks, Insurance, BD/AM, Payments)

P_fin = E(NIM × earning_assets + fees - provisions - opex) × M(ROE/COE, NPL outlook)

**핵심 메커니즘 (은행)**:
- NIM (net interest margin) = 자산수익률 - 부채금리. 단기금리↑ 자산쪽 빠르게 반영, 부채(예금) lag → 단기금리상승 초기 NIM 확장.
- 2-10Y slope 양전환 → 장기대출 수익↑ + 단기조달 안정 → NIM 구조적 확장.
- **HY OAS / credit spread**: provisioning cycle 신호. 확대 = 부실예약↑ = EPS↓.
- 자본비율 (CET1, leverage ratio) regulatory floor → capital return 폭 결정.

**보험**:
- 부채(보험준비금) duration 길다 (연금/생보 30Y+) → 자산 매칭 채권 보유 → real rate ↑ 시 BV↑ 와 신규수익률↑(둘 다 호재).
- 손해보험: pricing cycle (premium hardening), 재해 손실 변동성.

**자산운용/결제**:
- AUM-leveraged earnings: 시장 베타 노출. 결제(V/MA): GDP × 카드사용률 + cross-border.
- 은행과 부호 다름 → financial sleeve 내 partial decoupling 필요.

## 2. 리포트가 엮어 보는 관계도 (report relations)

### 2.1 방어주 측

1. **Real rate ↑ → 방어주(특히 utilities) multiple 압박**: TLT-XLU 상관 +0.6~0.8. utilities/staples 듀레이션 ~15~25Y 자산.
2. **HY OAS 확대 → 리스크오프 → 방어주 *상대* outperform** (시장 베타 ↓, 베타 갭이 알파로 발현). 단, 절대 수익 음수 가능 — 베타 갭이 핵심.
3. **Inflation ↑ + 성장 ↓ (Stagflation) → 방어주 lead** (Investment Clock). 단, staples 는 input cost (commodity) 압박 받으므로 pricing power 가능 종목만 (KO/PG > 일반 식품주).
4. **달러 ↑ → multinational staples (PG/CL/KO/PEP/PM) 환산 매출 압박, 마진 ↓**. 반대로 utilities 는 도메스틱.
5. **유가 ↑ → utilities 연료비 ↑ (단기 마진 압박, 후속 요금승인으로 회복), staples 원자재 입력비 ↑** (KO sugar, PG palm oil). pricing power 있는 종목만 흡수.
6. **Healthcare regulatory regime**: drug pricing 정책 (IRA Medicare 협상) → pharma multiple 디레이팅. medical device·HMO 는 별개 (rate exposure 약함, 인구학적 tailwind).
7. **국채 yield curve** vs 방어주: 2-10Y 스티프닝 → 일부 자금 risk-on 으로 빠짐 → 방어주 underperform (rotation).

### 2.2 금융주 측

1. **2-10Y 스티프닝 → 은행 NIM ↑** (가장 단순 강한 신호). DGS10 - DGS2 → bank EPS 모멘텀 ↑ (3~6개월 lag).
2. **HY OAS 확대 → 은행 provision ↑ (지연), EPS ↓** (Q+1~Q+2 lag). 보험 손해보험은 자산 손실 위험.
3. **Real rate ↑ → 은행 deposit franchise value ↑** (저금리 비싼 예금 베이스의 가치), 보험 책임준비금 적정성 ↑.
4. **Recession (10Y-2Y 역전 → 12~18M lag) → 은행 NPL ↑** + provisioning ↑. 은행은 cyclical-leaning.
5. **DXY ↑** : 자산운용/IB 해외수익 압박, 결제(V/MA) cross-border 약화.
6. **신용카드·소비대출 (consumer finance, COF/AXP)**: 실업률 lag + saving rate trend. 경기침체 진입 = NPL spike (subprime auto, credit card).
7. **AUM 기반 자산운용 (BLK/SCHW)**: 시장 인덱스 베타 + flow trend. risk-off → AUM ↓ + flow outflow → 이중 타격.

### 2.3 방어주 vs 금융주 dispersion

> 이 sleeve 의 가장 중요한 분석 포인트.

| 국면 | 방어주 | 금융주 | 부호 |
|---|---|---|---|
| Real rate ↑ | -(util/staples 압박) | +(NIM/deposit franchise) | **반대** |
| Curve 스티프닝 | -(rotation out) | +(NIM 확장) | 반대 |
| HY OAS ↑ (risk-off) | +(상대 outperform) | -(provisioning) | **반대** |
| Recession 진입 | +(필수수요 방어) | -(NPL spike) | 반대 |
| Inflation ↑ + 성장 ↑ (Overheat) | -(rate 압박) | + 초기 → - 후기 (mix) | mix |
| Slowdown (Stagflation) | +(클래식 lead) | -(NPL+NIM 양쪽 압박) | 반대 |

→ **한 sleeve 안 두 sub-sleeve 가 거의 반대 신호**. 가중규칙 (블록4) 가 industry archetype 분리 필수.

## 3. 학습 깊이 — 거시 관계도 (M2 ↔ 미국채/일본채/금리/환율) 적용

거시 예시 동일 수준:
- **M2 확대 → 위험자산 선호 / 인플레 동반 → 미국채 금리 ↑**: 방어주 multiple 압박 (특히 util), 은행 NIM 확장 (긍정).
- **일본 국채 (BOJ YCC) → JGB 금리 ↑ → 일본 투자자 본국 회귀 (carry unwind) → 미국채/달러 자금 유출 → 미국 yield 상승**: 방어주 압박, 은행 NIM 호재.
- **달러 ↑**: 방어주 multinational 압박, 금융 IB·cross-border 결제 약화.
- **HY OAS 확대 (credit cycle)**: 방어주 상대 outperform, 은행 provision risk.

이 관계도가 lens 정성필드 (report_relations) 와 partial-corr prior (블록3) 에 직접 매핑.

## 4. Investment Clock 4국면별 방어주/금융주 리더십

```
                                  성장↑
                                    │
              Recovery (mid)        │     Overheat (late)
              -------------          │     ----------------
              ▶금융 선호 (NIM)        │     ▶ Energy/Materials (cyclical)
              방어 보합              │     ▶ 일부 staples (pricing power)
              real rate ↗            │     real rate 高, util 압박
                                    │
              inflation↓ ──────────┼────── inflation↑
                                    │
              Reflation (early)     │     Slowdown/Stagflation
              -----------------     │     ----------------------
              ▶ Tech/growth         │     ★▶ 방어주 lead ★
              방어 underperform      │     ▶ 금융 worst (NPL+NIM compress)
              금융 보합               │     real rate↓ → 일부 util 회복
                                    │
                                  성장↓
```

→ **Slowdown/Stagflation 사분면이 방어주의 모국**. 금융주는 동시 worst.

## 5. 추정 (estimation_note) — 2026-05 anchor

(macro 방 estimation 참조: 2024-Q4 커브 역전 해소 + HY OAS 안정 → Recovery 초입)

- Recovery 초입 → 방어주 **상대** underperform 단계. 절대수익은 valuation 리셋 후 안정.
- 금융주 (특히 banks) → 2-10Y 슬립 양전환 → NIM 확장 thesis 활성.
- 보험 → real rate 안정 → BV 호조 / 책임준비금 부담 완화.
- ★변동요인: regulatory regime (drug pricing IRA), Basel III endgame 자본요건, 금리 path 재현 (FFR 동결/인하 시점).
- 이 estimation 은 confidence_hooks 의 flag 누적으로 갱신.

## 6. 다른 방 (cyclical) 와 비교 — 무엇이 다른가

| 축 | cyclical (us_cyclical) | defensive (us_defensive 이 방) |
|---|---|---|
| 알파 우위 | valuation > momentum > revision (semi panel 검증) | quality + dividend safety + rate beta. valuation 부차 |
| 핵심 macro | ISM PMI, HY OAS, dollar, oil (positive cyclical) | real rate (negative for util/staples, positive for banks), curve slope |
| regime 베스트 | Reflation/Recovery/Overheat | Slowdown/Stagflation/Risk-off |
| operating leverage | 핵심 증폭계수 | 약 (방어주 마진 안정), 금융은 다른 leverage (financial leverage) |
| price momentum | early-cycle 효과 | 약. mean-reversion 우위 |
| dividend | 부차 | 핵심 thesis (payout sustainability) |

→ **두 방의 가중 카드는 거의 대칭**. main 이 두 카드를 regime 별로 dispatch.

