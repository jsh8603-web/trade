# evaluation — VIX term structure audit (독립 12축)

> **auditor**: opus 독립 audit subagent (탐구자 self-certify 회피, raw 직접 재실행 검증)
> **date**: 2026-06-01
> **대상**: `validation-vix-term-structure.md` / `.py` (seed=20260601) / `validation-metrics-vix-term-structure.json`
> **방법**: §0 Provenance — py 독립 재실행 + forward-shift 로직 + z-score causality + PIT + 부분상관 추가 검증
> **참조**: AUDIT-GUIDE 12축, empirical-claim-presentation §1, small-n-statistical-rigor

---

## §0. Provenance + Recomputation (★제1원리)

**독립 재실행 완전 재현** — md/json 수치가 raw 재계산과 100% 일치:

| 항목 | md 주장 | 독립 재실행 | 일치 |
|---|---|---|---|
| DEF_PURE 동시 RankIC | -0.141 (t=-9.6) | -0.1407 (t=-9.597) | ✓ |
| fwd 5d / 20d | +0.023(p=0.41) / -0.011(p=0.82) | +0.0232 / -0.0105 동일 | ✓ |
| FIN 동시 | +0.034 (p=0.017, raw) | +0.0337 (t=2.386) | ✓ |
| regime gap (DEF_PURE) | +0.283%/d (Welch t=4.93, p<1e-5) | +0.002831/d t=4.930 | ✓ |
| regime gap (FIN) | -0.236%/d (t=-2.25, p=0.025) | -0.002357/d t=-2.253 | ✓ |
| half-split OOS | -0.134 / -0.150 부호일치 | -0.1344 / -0.1504 YES | ✓ |
| credit overlap | -0.147 | -0.1471 | ✓ |
| real-rate overlap | ~0 | +0.0028 (p=0.85) | ✓ |
| ADF (ratio/z/VIX) | 전부 I(0) | -8.27/-10.37/-5.53 p=0 | ✓ |

**합성 지문 검사 PASS**: COVID 2020-03-16 VIX=82.69 / 2008 GFC 2008-10-24=79.13 / 2018 Volmageddon=37.32 실재. VIXCLS 데이터 지문 = 1일 간격 7598개 + 3일(주말) 1899개 = 실거래일 분포. backwardation 478일이 18개 연도(2008=118/2011=51/2018=53/2020=53)에 위기 클러스터 집중 = 합성 불가능 패턴.

---

## §1. 12축 verdict

| 축 | 결과 | 판정 |
|---|---|---|
| **A 이론 실재성** | VIX term backwardation=stress (CBOE 표준). 부호 prior 실측 부합 | PASS |
| **B 실데이터 ★hard** | FRED VIXCLS + yfinance VIX3M/VIX9D + ETF, 합성 0. **동시** IC=-0.141 t=-9.6 (validated) / **예측** fwd IC<0.03 t<2 = B 게이트 FAIL(정직히 REJECTED 라벨) | 동시 PASS / 예측 REJECTED |
| **C 추적성 ★hard** | md ↔ json ↔ 재계산 오차 0%. ★동시/예측 라벨 정직 — 동시 -0.141 을 forward로 over-claim 안 함(명시적 REJECTED) | PASS |
| **D PIT/lookahead ★hard** | VIXCLS=CBOE 실시간 종가, **무개정 시장 관측치**(revised-vintage 함정 X — credit impulse/NFCI 와 본질 다름). z-score=rolling(252) closed-right(과거만, causal). forward=shift(-1) t+1..t+h 누적(당일 미포함, lookahead 0). 동시=같은날 정의상 미래정보 없음 | PASS |
| **E 자문 cross-verify** | M6 자문 "방어주 critical 지표" = 동시 한정 부분 확인, 예측 알파 주장은 실측 기각. 환각 0 | PASS (자문 over-claim 격하) |
| **F 반증+기각** | 예측 채널 REJECTED + FIN 동시 부호반대 = 기각 기록 실재 | PASS |
| **G effective-N ★tier** | backwardation 478일=위기 클러스터 의존. contemp n=4398 충분 → 동시=validated. regime=episode 의존 → structural prior(저신뢰) 라벨. validated 위장 없음 | tier 정직 PASS |
| **H 미해결** | §4 인과/credit overlap/episode 의존/pre-2008 부재 4건 솔직 기재 | PASS |
| **I 무결성·생존편향 ★hard** | ETF 5종 전부 2000-01-03~ 전기간 존속, 상폐 0, 가격 ETF split 무관. universe 고정 = point-in-time 무의미. VIX 지수=생존편향 무관 | PASS |
| **J 경제유의·거래비용** | 동시 신호라 alpha 주장 안 함(forward null). risk overlay 정성 용도 한정 = J 허용 범위 | N/A |
| **K 다중검정** | 시도횟수 공시 m=6(2×3). Bonferroni α/6=0.0083, DEF_PURE 동시만 생존 | PASS |
| **L 통합 중복 ★시스템** | credit(ΔBAA10Y) corr=-0.147 = **R²=2.2% 약 overlap**. ★credit 통제 후 동시 IC -0.137→-0.121 거의 유지 = 대부분 독립. real-rate(ΔDFII10) R²~0 무관 | 약 overlap (통합 시 공통 stress factor 1회 계상 권고) |

**§1.7 ADF**: ratio/z/VIX 전부 I(0) stationary 재확인. level/z 회귀 spurious 없음. PASS.

---

## §2. Hard-fail 4 코어 (B·C·D·I) 결과

| 코어 | 결과 |
|---|---|
| **B 실데이터/합성금지** | 동시 PASS(validated) / 예측 정직 REJECTED. 합성 0. |
| **C 추적성·재현** | 오차 0%, 동시/예측 라벨 정직. PASS |
| **D PIT/lookahead** | ★VIX 무개정 PIT-pure 확인, z-score causal, forward 미래누적. PASS |
| **I 생존편향·무결성** | ETF 전기간 존속, 생존편향 무관. PASS |

**hard-fail 0건.**

---

## §3. ★핵심 쟁점 — 동시 vs 예측 정직성 (eq_intl credit 함정 재확인)

eq_intl credit 이 동시 over-claim 으로 직전 격하된 직후라 동일 함정 집중 검증:

- 본 산출은 **동시(contemp)와 예측(forward 5d/20d)을 코드 레벨에서 분리 측정**하고, 동시 -0.141(강) 을 forward 알파로 **둔갑시키지 않았다**. forward 전부 비유의(p=0.41~0.82)를 명시적으로 **REJECTED** 라벨.
- verdict 종합 = "structural prior (동시 신호) — validated alpha 아님 / 매매 선행신호 부적격 / regime 동시 진단·risk overlay 한정". 정직.
- ★eq_intl 함정과 정반대 처리 — eq_intl 은 동시를 예측력으로 over-claim 했으나, 본 산출은 동시/예측 분리 + 예측 null 명시 + 용도를 동시 modulator 로 정확히 한정.

→ **동시 CONFIRMED 의 PIT-pure 정당성**: VIX=무개정 실시간 종가라 credit impulse 같은 revised-vintage artifact 부재. 동시 측정이 lookahead 없고(같은날), z-score 가 causal. 따라서 동시 modulator 로 **정당 수용 가능**.

---

## §4. yaml 인계 적정성 (family=risk, contemporaneous only, prior≈0.14)

탐구 §5 인계 제안 검토:

- `family=risk` ✓ 적정 (volatility regime indicator).
- `lag_routing=contemporaneous 한정` ✓ ★필수 — 예측 REJECTED 라 forward 라우팅 금지. 정확.
- `prior_sign=neg, prior_strength=0.14` ✓ 동시 IC -0.141 부합. 단 ★**validated alpha 아닌 risk-overlay/regime 진단** 라벨 의무 — base_weight 는 선행 신호 가중 부적격, defensive tilt during backwardation modulator 로 약 가중.
- L축 credit overlap 주석 ✓ 명시 권고 — 통합 상관행렬에서 VIX_term + credit_beta 공통 stress factor 1회 계상(R²=2.2% 약하나 통합 시 명시).

---

## §5. 종합

```
[감사] eq_us_defensive VIX term structure — verdict: 충실 (동시 modulator 한정)
- Provenance(§0): 재실행 100% 재현, 합성 지문 PASS
- 12축: 통과 10 / tier 1(G) / 약경고 1(L overlap) / hard-fail 0
- Hard-fail B·C·D·I: 전부 통과 (D=VIX 무개정 PIT-pure 확인)
- Tier(G): 동시=validated / regime·예측=structural prior(저신뢰) 정직 라벨
- 시스템 정합(§4): 현 골격 수용 가능 (risk family contemporaneous indicator + L축 공통 stress factor 1회 계상)
- 판정: register 가능 (family=risk, contemporaneous only, prior≈0.14, ★validated alpha 아닌 risk-overlay 라벨 의무)
```
