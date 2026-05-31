---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/L-axis-integration]
date: 2026-06-01
study_id: eq_intl
sleeve: equity.intl
session: btn-eq_intl-L-axis
raw_source: raw/validation-L-axis-fx-dollar-overlap.py + raw/merit_cache/ + raw/yahoo_cache/
principles: [PIT 종가, 합성 금지(실 캐시), daily/monthly log-return, partial-corr, Fisher-z CI, Bonferroni, hedge 어휘(n<60)]
scope: "L축 선행측정 — fx_carry 환 채널 ↔ macro β_dollar 채널 이중계상(double-count) 위험 정량화. J축 통합 상관행렬 진입 전 게이트(merit audit §6.4 미해결 의문 4)"
indicators: [fx_carry_momentum, dollar_beta_country]
---

# eq_intl L축 — fx_carry 환 채널 ↔ β_dollar 채널 overlap (partial-corr)

> **게이트**: merit audit `validation-merit-eq_intl-20260601.md` §6.4·§5(L축) 가 지목한 미해결 의문 —
> "EM fx momentum(Rank-IC −0.43)과 macro-linkage β_dollar(−1.1~−1.4)는 같은 환 채널 — 통합 시 이중계상
> 위험. partial-corr(dollar 고정 후 local-fx 잔차) **미측정**." 본 산출이 그 측정을 채운다.
> **목적**: J축 통합 상관행렬에서 dollar 를 두 번 세는지(중복) 판별 → 1회 계상 vs 별도 유지 권고.

## §0. 데이터 provenance (재계산 가능)

| 변수 | 소스 | 정의·단위 | 가용 범위 | 빈도 |
|---|---|---|---|---|
| dollar 채널 | yahoo_cache `dxy.csv` | DXY Δlog (macro_linkage_v2 β_dollar 와 **동일 driver**) | 2021-06 ~ 2026-05 | D / M |
| fx_carry | FRED `DEX{BZ,KO,IN,MX}US` | USD/local 63영업일(=3m) log-momentum (merit §4 Bonferroni 생존 채널=mom_3m. 상승=local 약세) | 1973~1995 ~ 2026-05 | D→M |
| 국가 ETF | yahoo_cache `{brazil,korea,india,mexico}.csv` | daily/monthly log-return | 2021-06 ~ 2026-05 | D / M |

- **측정 단위 = DXY window(2021-06~) 한정.** DXY(yahoo) 가 2021-06 부터만 가용 → β_dollar 측정 window 와 동일하게 맞춤. daily n=1177 / monthly n=59.
- **합성 지문 검사**: 전 시리즈 실 fetch(merit_cache JSON + yahoo_cache CSV). 합성 시드 아님. 2022 금리쇼크·2025 dollar regime 실재.
- **★측정 axis 명시(E97·merit §1.3)**: 두 단위 병행 — (1) **daily** = β_dollar 가 측정된 단위, ETF return 의 dollar 노출이 dominant. (2) **monthly** = fx_carry 의 Rank-IC(−0.43)가 측정된 단위(merit §4 contemporaneous mom_3m). **fx_carry 의 본질 신호는 monthly 축에 있으므로 monthly 가 1차 판정 단위**, daily 는 보조.
- **★n<60 hedge 의무**: monthly n=59 (DXY window 한정). 단정 어휘 금지, 방향성 prior + CI 보고.
- 재현: `PYTHONUTF8=1 python raw/validation-L-axis-fx-dollar-overlap.py`

## §1. 직접 overlap — fx_carry ↔ dollar driver 자체

두 driver 가 같은 정보인가. (USD/local momentum) ↔ (DXY momentum 또는 Δlog).

### 1.1 monthly (1차 판정 단위)

| 국가 | n | r(fx, DXY Δlog) | fx↔dollar 공통 R²(%) |
|---|---:|---:|---:|
| brazil | 59 | +0.222 | 4.9 |
| korea | 59 | **+0.442** | **19.5** |
| india | 59 | +0.260 | 6.8 |
| mexico | 59 | +0.186 | 3.5 |
| **평균** | | | **8.7%** |

### 1.2 daily (보조)

| 국가 | n | r(fx mom, DXY 3m mom) | 공통 R²(%) | p |
|---|---:|---:|---:|---:|
| brazil | 1177 | +0.276 | 7.6 | 6.3e-23 |
| korea | 1177 | **+0.820** | **67.3** | ~0 |
| india | 1177 | +0.476 | 22.7 | 6.2e-77 |
| mexico | 1177 | +0.316 | 10.0 | 2.8e-30 |
| **평균** | | | **26.9%** |

★ 두 driver 는 **양의 상관**(USD/local 약세 ↔ DXY 강세, 부호 정합). overlap 은 **국가별 분산 큼**: **korea 최대**(monthly 19.5%, daily 67.3% — KRW 가 broad dollar 와 강 동조), brazil/mexico/india 낮음(monthly 3.5~6.8%, idiosyncratic FX 비중 큼). daily 67% 는 두 momentum 이 같은 시계(3m)·강 자기상관이라 과대 — monthly Δlog overlap(8.7%)이 보수적·정직.

## §2. partial correlation — 다른 채널 통제 후 ETF 잔존 부분상관 (★핵심)

### 2.1 monthly (n=59, 1차 판정)

| 국가 | raw r(ETF,fx) | r(ETF,fx \| dol) | raw r(ETF,dol) | r(ETF,dol \| fx) |
|---|---:|---:|---:|---:|
| brazil | −0.421 | **−0.367** | −0.488 | −0.446 |
| korea | −0.301 | **−0.118** | −0.470 | −0.394 |
| india | −0.399 | **−0.331** | −0.414 | −0.350 |
| mexico | −0.467 | **−0.445** | −0.555 | −0.538 |

★ **dollar 통제 후 ETF↔fx_carry 잔존 partial-corr 평균 −0.315** (raw −0.40 → partial −0.315, 약 21% 만 축소). brazil/india/mexico 는 거의 안 줄음(−0.42→−0.37 등) = **fx_carry 가 dollar 와 별개의 독립 환 정보 보유**. **korea 만** dollar 통제 시 −0.30→−0.12 로 크게 축소 = KRW 환이 broad dollar 와 강 중첩(§1 정합).
★ 반대로 fx 통제 후 ETF↔dollar 도 거의 유지(−0.47~−0.55→−0.39~−0.54) = dollar 도 독립 기여 유지.

### 2.2 daily (n=1177, 보조 — 시계 불일치 caveat)

daily ETF return(빠름) vs 3m momentum(느림) = 시계 불일치 → fx 의 daily ETF 기여 과소(raw r −0.05~−0.07). dollar(Δlog) 통제 후도 거의 동일(partial −0.04~−0.07). **daily 는 fx_carry 신호를 담는 단위가 아님**(fx 는 monthly Rank-IC 채널). dollar partial 은 강 유지(−0.28~−0.39, p<1e-23, Bonferroni 생존) = daily ETF 변동의 dollar 노출은 robust·독립.

## §3. ETF 설명분 commonality decomposition

ETF 분산 중 dollar·fx 가 **공유**하는 설명분(common) vs 각 **독립**(unique).

### 3.1 monthly (1차)

| 국가 | R²(both) | common/both(%) = 중복 비중 |
|---|---:|---:|
| brazil | 0.270 | 21.8 |
| korea | 0.290 | **34.4** |
| india | 0.230 | 26.0 |
| mexico | 0.380 | 18.2 |
| **평균** | | **25.1%** |

★ ETF 설명분의 **약 25% 가 dollar·fx 공유분(중복 위험 실재)**, **약 75% 는 unique(독립)**. korea 중복 최대(34%), mexico 최소(18%).

### 3.2 daily (보조)

daily common/both = 평균 0.8% (fx 가 daily ETF 거의 미설명 → 중복도 0). → daily 는 판정 근거 부적격(시계 불일치).

## §4. 다중비교 (Bonferroni)

daily 12 비교(4국 × {ETF↔fx\|dol, ETF↔dol\|fx, fx↔dol overlap}): α/m=0.0042. raw p<0.05 = 10/12, Bonferroni 생존 = **8/12** (dollar partial 4/4 + overlap 4/4 생존, fx partial 은 daily 시계불일치로 비유의 — §2.2 caveat).

## §5. verdict + J축 통합 권고

### 5.1 종합 수치

| 지표 | monthly(1차) | daily(보조) |
|---|---:|---:|
| fx_carry ↔ dollar 직접 overlap R² | **8.7%** (korea 19.5 / 나머지 3.5~6.8) | 26.9% (korea 67) |
| ETF 설명분 common share(중복 비중) | **25.1%** (korea 34 / mexico 18) | 0.8% |
| dollar 통제 후 ETF↔fx 잔존 partial-corr | **−0.315** (독립분 큼) | −0.05 (시계불일치) |

### 5.2 verdict — **PARTIAL OVERLAP (부분 중복, 대체로 독립)**

- precedent VIX↔credit R²=2.2%(거의 독립→별도) 대비, 본 fx_carry↔dollar 는 **직접 overlap R² 8.7%(monthly) / ETF 공유분 25%** = VIX↔credit 보다 중복 큼, but **dollar 통제 후 ETF↔fx 잔존 partial −0.315** 가 살아있어 **같은 베팅이 아님**(독립 환 정보 약 75% 잔존).
- **핵심**: fx_carry 와 β_dollar 는 "같은 dollar 정보" 라기보다 **broad-dollar 공통분(≈25%) + 국가별 local-FX 고유분(≈75%)의 혼합**. korea 만 broad dollar 와 강 중첩(중복 34%)이라 1회 계상에 가까움.
- ★n<60(monthly) + DXY window(2021-06~) 한정 → **방향성 prior(부분 중복) tentative**. CI 넓음, full-sample(merit fx n=309~362) 재측정 시 변동 가능.

### 5.3 J축 통합 권고

**(b) 별도 유지 — 단 공통 dollar 인자 1회 계상 + korea 예외 처리**:

1. **β_dollar(daily, broad)** 와 **fx_carry(monthly, local-FX momentum)** 는 **다른 축·다른 정보** → 통합 상관행렬에 **별도 entry 유지** 정당(독립분 ≈75%, partial −0.315 생존).
2. ★단 **공통 dollar 인자(≈25% 공유분)는 1회만 계상** — AUDIT-GUIDE L축 "공통인자 중복 계상 X". 통합 시 두 채널을 단순 가산하면 dollar 분산 25% 이중 반영 → **공통 dollar factor 를 한 번 추출(예: DXY) 후, fx_carry 는 그 잔차(dollar-orthogonalized local-FX residual)로 entry** = partial −0.315 가 그 잔차 신호. 이러면 PSD 보존 + 중복 제거 동시.
3. **korea 예외**: KRW 환↔broad dollar overlap 최대(monthly 19.5% / daily 67% / common 34%). korea 는 fx_carry 와 β_dollar 가 거의 같은 베팅 → **korea sub-archetype 한정 1회 계상(택1)** 또는 더 강한 orthogonalize. 다른 3국(brazil/india/mexico)은 별도 유지 안전.
4. **PSD 전제**: orthogonalized residual 방식은 공통인자 제거라 PSD 깨짐 위험 낮음. 단순 두 채널 가산(중복 반영)은 상관행렬 near-singular 위험 → 지양.

### 5.4 caveat

- DXY window 한정(2021-06~, monthly n=59). merit fx 의 full-sample(n=309~362) overlap 은 미측정 — DGS/full DXY(FRED DTWEXBGS 등) 로 확장 시 재검 의무.
- daily overlap(26.9% / korea 67%)은 3m momentum 자기상관 과대 산물 → monthly(8.7%) 가 정직한 직접 overlap.
- fx_carry 는 merit §4 에서 **예측(lead) REJECTED, 동시(contemporaneous) CONFIRMED** = 현재 환노출 사이징용. β_dollar 도 동시 채널 → 둘 다 contemporaneous exposure 축에서 비교됨(시제 정합 PASS).
- korea overlap 이 큰 건 KRW 의 broad-dollar 베타가 높아서(반도체·수출 cyclical) — 경제적으로 타당(spurious 아님).
