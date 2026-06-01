---
study: eq_us_cyclical
artifact: validation-regime-conditional-poc
kind: proof-of-concept (regime-conditional vs full-sample forward IC)
date: 2026-06-01
stage: sample (no yaml/code edit, no commit)
data_integrity:
  source: FRED (DGORDER, NEWORDER, T10Y2Y, CPIAUCSL, T5YIE), yfinance (sector ETF close)
  synthetic_data: none
  ret_range: 2000-01-31 .. 2026-05-31 (monthly log-returns)
  cpi_pub_lag_probe: ALFRED first-release median ~12d (this session)
  signal_pit: live first-release alignment (DGORDER/NEWORDER pub-lag 56d; T10Y2Y/T5YIE market-priced same-day)
  regime_pit: expanding-median threshold + availability-month ffill (no full-sample median lookahead)
verdict: regime-conditional value PARTIALLY demonstrated (1 signal/regime survives Bonferroni; the most dramatic "rescue" does NOT survive correction)
---

# Regime-Conditional PoC — full-sample pooled IC vs regime-split forward IC

## 0. 가설 / 무엇을 검증했나

**검증 가설**: "full-sample pooled forward IC 가 비유의/약해도, 특정 거시 국면(인플레 高/低 등)으로
나눠보면 해석력(상관)이 살아날 수 있다."

이걸 cyclical 신호로 proof-of-concept 했다. 일부러 full-sample 강도가 다른 3종 신호를 골랐다:

| 신호 → 타깃 | full-sample LIVE (parent study) | 선정 이유 |
|---|---|---|
| DGORDER_yoy → XLE | k6 IC +0.31 (p=0.0016) **유의** | 이미 유의 — 국면별로 더 강/약해지나? |
| NEWORDER_yoy → XLE | k3 IC +0.137 (p=0.10), k6 (p=0.055) **경계 붕괴** | ★특정 국면서 부활하나? (가장 흥미) |
| T10Y2Y → XLI / SOXX | 전 horizon p>0.5 **전멸** | 국면서 살아나나? |

## 1. Regime 정의 (★전부 공시 — data-snooping 투명성)

시도한 regime 정의 = **3종 (전부 보고, 사후 cherry-pick 아님)**:

| ID | regime | 분류 변수 | PIT 처리 |
|---|---|---|---|
| R1 | CPI inflation 高/低 | CPIAUCSL yoy, **expanding median** split | pub-lag ~12d 후 availability month 부착 |
| R2 | breakeven 高/低 | T5YIE 5yr 기대인플레, expanding median split | 시장가 daily = same-day knowable |
| R3 | growth (curve) | T10Y2Y 부호 (>0 정상 / <0 역전) | 시장가 = same-day knowable. ★curve 신호 자체엔 미적용 (self-conditioning 금지) |

★lookahead 회피 핵심:
- 신호 = first-release availability month 부착 (revised 값을 사후 시점에 쓰지 않음).
- regime label = **expanding median** (해당 시점까지 history 만으로 임계 산출 → full-sample median lookahead 차단) + availability month ffill.
- ADF (regime driver): CPI_yoy p=0.0029, T5YIE p=0.0013, T10Y2Y p=0.008 — 전부 I(0), level split 사용 적격.

## 2. 결과표 — full-sample vs regime-split (HARD)

`★` = Bonferroni 생존 (m=40, α=0.00125). `INSF` = n<30 격하. CI = block-bootstrap 95%.

### DGORDER_yoy → XLE (full = 유의 신호)

| horizon | regime | bucket | n | IC | p | 95% CI | 보정 후 |
|---|---|---|---|---|---|---|---|
| **full** | — | — | 311 | **+0.311** | 0.0016 | [0.125, 0.478] | (parent m=24 생존) |
| k6 | CPI | highInfl | 97 | **+0.423** | **0.0001** | [0.161, 0.617] | **★Bonferroni+BH 생존** |
| k6 | CPI | lowInfl | 214 | +0.280 | 0.0319 | [0.032, 0.498] | 미생존 |
| k6 | BE | highBE | 103 | +0.298 | 0.0148 | [0.02, 0.523] | 미생존 |
| k6 | BE | lowBE | 149 | +0.182 | 0.224 | [-0.107, 0.449] | 미생존 |
| k6 | curve | normal | 262 | +0.311 | 0.0042 | [0.095, 0.497] | 미생존 |
| k6 | curve | inverted | 49 | +0.270 | 0.0347 | [-0.085, 0.6] | 미생존 (CI 0 횡단) |
| k3 | CPI | highInfl | 99 | +0.318 | 0.0038 | [0.091, 0.507] | 미생존 |
| k3 | CPI | lowInfl | 215 | +0.191 | 0.073 | [0.002, 0.359] | 미생존 |

→ **high-inflation 국면서 +0.42 로 sharpen** (full +0.31 보다 강). 유의 신호가 국면 조건화로 더 또렷해짐.

### NEWORDER_yoy → XLE (full = 경계 붕괴 신호 — ★가장 흥미로운 케이스)

| horizon | regime | bucket | n | IC | p | 95% CI | 보정 후 |
|---|---|---|---|---|---|---|---|
| **full** | — | — | 314 | +0.137 | 0.100 | [-0.024, 0.298] | 미유의 |
| k3 | CPI | highInfl | 99 | +0.197 | 0.055 | [-0.041, 0.409] | 미생존 |
| k6 | CPI | highInfl | 97 | +0.242 | 0.098 | [-0.073, 0.519] | 미생존 |
| k6 | curve | inverted | 49 | +0.280 | 0.126 | [-0.18, 0.551] | INSF (n>30이나 CI 넓음) |
| (전 bucket) | — | — | — | best p=0.055 | — | — | **부활 실패** |

→ ★NEWORDER 는 **어느 regime 으로 쪼개도 부활 안 함**. 가장 좋은 bucket 도 p=0.055 (보정 전), 보정 후 전멸.

### T10Y2Y → XLI (full = 완전 전멸 — ★가장 극적으로 달라진 신호)

| horizon | regime | bucket | n | IC | p | 95% CI | 보정 후 |
|---|---|---|---|---|---|---|---|
| **full** | — | — | 311 | +0.017 | 0.865 | [-0.179, 0.21] | **완전 무신호** |
| k6 | CPI | highInfl | 97 | **−0.439** | 0.0056 | [-0.649, -0.125] | 미생존 (>0.00125) |
| k6 | CPI | lowInfl | 214 | +0.097 | 0.410 | [-0.147, 0.32] | 미생존 |
| k3 | CPI | highInfl | 99 | −0.319 | 0.034 | [-0.557, -0.027] | 미생존 |
| k6 | BE | highBE | 103 | −0.258 | 0.047 | [-0.5, 0.039] | 미생존 (CI 0 횡단) |

→ ★full-sample +0.017 (완전 0) 이 **high-inflation 국면서 −0.439 (강한 음)**. 이게 PoC 핵심 발견:
**부호 반대 sub-regime 이 full-sample 에서 서로 cancel → pooled IC=0 으로 위장**. 국면 분리하니 강한 음의 관계
(인플레 高 + curve 역전/평탄 → XLI 향후 6M 약세)가 드러남. **단 Bonferroni 미생존** (p=0.0056 > 0.00125).

### T10Y2Y → SOXX (full 전멸 → 국면서 약한 음의 힌트, 비유의)

full k6 IC −0.04 (p=0.71). high-inflation k6 IC −0.350 (p=0.041, n=97) — 같은 방향(음) 이나 보정 후 전멸.

## 3. Belief-weighted IC (soft regime 확률 가중) — ★hard split 대비 중요

시스템이 hard split 이 아니라 belief b(t) 확률 mix 이므로, soft membership (logistic of expanding-z) 로
가중 rank-corr 재계산. **highTilt vs lowTilt gap 이 hard split 보다 훨씬 작다**:

| 신호→타깃 k | regime | BELIEF highTilt | BELIEF lowTilt | hard split gap (참고) |
|---|---|---|---|---|
| DGORDER→XLE k6 | CPI | +0.348 | +0.282 | hard +0.423 vs +0.280 |
| T10Y2Y→XLI k6 | CPI | **−0.036** | **+0.049** | hard **−0.439 vs +0.097** |
| T10Y2Y→SOXX k6 | CPI | −0.067 | −0.028 | hard −0.350 vs −0.049 |

★해석: T10Y2Y→XLI 의 극적 hard-split 효과(−0.44 vs +0.10)가 belief-weighted 에선 거의 소멸(−0.04 vs +0.05).
즉 **그 효과는 인플레 극단 tail 의 소수 관측에 집중**돼 있고, 확률 mix 하면 씻겨나감 → **fragile / snooping 의심**.
DGORDER→XLE 의 inflation tilt 는 belief 에서도 +0.35 vs +0.28 로 방향 유지 = 상대적으로 robust.

⚠️ belief p-value 는 Kish n_eff 기반 Fisher-z 로, **HAC 자기상관 보정 미적용 → 낙관적**. 방향·gap 비교용으로만 사용,
유의성 단정 근거로 쓰지 않음.

## 4. 다중비교 보정 (★full-sample 보다 큰 penalty)

- m = **40** hard regime-conditional forward 검정 (parent full-sample m=24 보다 큼 — 국면×신호×bucket×horizon 폭증).
- Bonferroni α = 0.05/40 = **0.00125** → 생존 **1개**: `DGORDER_yoy|XLE|k6|CPI highInfl` (p=0.0001).
- BH-FDR q=0.05 crit p = 0.00013 → 생존 **1개** (동일).
- ★T10Y2Y→XLI highInfl (p=0.0056) = 가장 극적이나 **Bonferroni 미생존**.

## 5. lookahead verify (★측정 axis 1:1)

- (a) 시제: signal = forward k=3/6M sum return (predictive). regime label = signal availability month 시점 known. PASS.
- (b) frequency: 전부 monthly. PASS.
- (c) transform: signal yoy / curve level; regime = expanding-median split (history-only). PASS.
- (d) conditioning: regime subset(hard) + belief-weight(soft) 둘 다. PASS.
- (e) regime: 본 분석 자체가 regime-conditional. expanding threshold 로 full-sample median lookahead 차단 verify. PASS.

★self-conditioning 금지: T10Y2Y 신호를 GROWTH_curve regime 으로 조건화 안 함 (코드 skip). PASS.

## 6. rigor 경고 (발동한 것)

1. **검정력**: hard split 시 high-inflation bucket n=97~99 (충분), 그러나 inverted-curve bucket n=49 (n>30 이나 CI 매우 넓음, 단정 금지). lowBE bucket 등 일부 CI 0 횡단.
2. **★data-snooping**: regime 정의 3종 시도 → 그 중 inflation split 이 가장 잘 "작동". 3종 전부 공시했으나, T10Y2Y→XLI 극적 효과가 belief-weighted 에서 소멸 = tail 집중 = snooping fragility 신호. **단정 금지**.
3. **lookahead**: expanding median + availability ffill 로 차단. 위반 없음.
4. **belief p HAC 미보정**: §3 낙관적, 방향 비교용 한정.

## 7. ★Proof-of-Concept 판정

**regime-conditional 가치 = PARTIALLY 입증 (조건부)**:

- ✅ **방향 1 입증**: 이미 유의한 신호(DGORDER→XLE)는 inflation 국면 조건화로 **+0.31 → +0.42 sharpen**, Bonferroni+BH 생존. "국면 조건화가 신호를 또렷하게 한다"는 명제는 robust 케이스 1건 확보.
- ⚠️ **방향 2 (dead 신호 부활)는 입증 못 함 (보정 후)**: T10Y2Y→XLI 는 full=0 → high-inflation −0.44 로 **극적으로 달라지나** Bonferroni 미생존 + belief-weighted 에서 소멸 → "검정력/snooping 한계, full-sample 결론(무신호) 유지" 쪽이 정직.
- ❌ **NEWORDER→XLE 부활 실패**: 어느 regime 도 보정 후 못 살림.

**종합**: "full 약하면 regime split 으로 무조건 살아난다"는 ★아니다. 이미 신호 있는 곳은 국면이 sharpen 하지만(가치 有),
완전 dead 신호의 "부활"은 대부분 다중비교/tail-snooping 산물 (T10Y2Y→XLI 가 경고 사례). regime-conditional 은
**신호 정제(refinement) 도구이지 신호 생성(creation) 도구 아님** 이 본 PoC 의 결론.

## 8. full-sample 대비 가장 달라진 신호 1개

★**T10Y2Y → XLI (k=6M)**: full IC **+0.017 (p=0.87, 완전 무신호)** → high-inflation 국면 IC **−0.439 (p=0.0056, n=97)**.
부호 자체가 0 → 강한 음으로 반전. 부호 반대 sub-regime cancel 이 full-sample 에서 신호를 위장한 전형. ★단 보정 후 미생존 → 잠정(tentative) directional, 박제 금지.

## 9. 12축 audit-ready 체크

- A 합성: synthetic none, FRED/yfinance 실데이터.
- B 시계열: ADF 사전(I(0) 확인), expanding-median PIT, half-split 은 bucket n 부족으로 보류(향후 OOS TODO).
- C 다중비교: m=40 Bonferroni+BH 명시, 생존 1.
- D autocorr: NW-HAC (overlapping forward window lag inflation), block-bootstrap CI.
- E lookahead: §5 5-axis verify + self-conditioning skip.
- F hedge: 단정 금지, "잠정/CI 넓음/snooping 의심" 어휘. 점추정 박제 안 함 (sample stage).
- belief vs hard 이중 보고로 over-claim 차단.
