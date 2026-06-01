---
title: "J축 factor β shadow validation — batch 5 sleeve"
tags: [study/factor-beta, shadow-validation, J축, batch-stage]
date: 2026-06-01
stage: "batch (점추정 박제 아님 — shadow 검증 대상)"
scope: "core/study 미수정 · SEED_CELLS Edit 제안만 (main 일괄 적용)"
method: "z-score std β, HAC(Newey-West maxlag=5), univariate+multivariate(5 factor), VIF, ADF 사전"
factor_source: "eq_us_defensive/raw/fred (DGS10/DTWEXBGS/DCOILWTICO/BAA10Y-AAA10Y/VIXCLS) — sample-stage 와 동일 source"
price_source: "yfinance period=max auto_adjust (무료)"
sample: "일별 n≈5052, coverage 2006-01-03 ~ 2026-05-22 (DTWEXBGS broad dollar 2006-01 시작이 joint window 제약)"
bonferroni: "30 비교 (6 unit × 5 factor) → α/30 = 0.00167"
---

# J축 batch std β — 5 sleeve × 5 factor

## 0. 방법 메모 (sample-stage 일관)

- factor 시계열 = `eq_us_defensive/raw/fred` 캐시 그대로 재사용 (sample 과 동일 source → 방법 일관성).
  - Δrate = DGS10 first-diff (bp), Δlog dollar = DTWEXBGS, Δlog oil = DCOILWTICO (2020-04-20 음가 1일 제거),
    Δcredit = (BAA10Y−AAA10Y) first-diff (bp), ΔVIX = VIXCLS first-diff.
- **ADF 사전 (§1.7)**: 5 factor 전부 p_ADF=0.0 (stationary, level 회귀 아님 — diff/log-diff 단위). 각 sleeve return ADF 도 0.0.
- **VIF 공선성**: 전 factor VIF ≈ 1.0~1.14 (rate/dollar/oil/credit/vol 거의 직교, 다중회귀 안정).
- 표준화 회귀 (y·x z-score → std β), HAC(NW maxlag=5) SE+t. univariate + multivariate(5 factor 동시) 둘 다.
- **★vol(ΔVIX) factor 포함** — sample 에서 rate β 가 vol 통제 시 흡수되는 현상이 batch 에서도 재현 (특히 reit·equity).
- tier 제안 (multivariate HAC 기준): |t|≥2 + Bonferroni 생존(p≤0.00167)=validated / |t|≥1.6=structural / 그 외=reject.
  ⚠️ shadow 검증 대상 점추정이지 prior 박제 아님. hedge: 아래 값은 *잠정 std β*, n 크나 same-day contemporaneous 한정.

## 1. gold 재현 sanity (방법 신뢰성 게이트)

| factor | 기존 SEED β | batch multi β (t) | batch uni β (t) | 판정 |
|---|---|---|---|---|
| rate | −0.295 | −0.215 (−12.0) | −0.189 (−9.6) | 부호·크기대 일치 |
| dollar | −0.328 | −0.317 (−16.7) | −0.346 (−17.4) | ★거의 정확 일치 |
| oil | +0.230 | +0.121 (+4.4) | +0.153 (+4.9) | 부호·방향 일치 (크기 약간 작음) |

**판정 = [일치] PASS.** dollar 가 SEED −0.328 vs batch −0.317 로 거의 동일, dollar > rate 순서 보존. rate/oil 은 multivariate(vol·credit 추가 통제)에서 약간 축소되나 부호·order 일관. gold 의 credit/vol 은 둘 다 비유의(t<1, reject) — gold 가 credit·vol 채널에 직접 노출 없음을 확인 (SEED 의 credit=HOLD 와 부합).
→ **방법 신뢰 게이트 통과.** 동일 파이프라인을 나머지 sleeve 에 적용.

## 2. 5 sleeve × 5 factor multivariate std β 종합표

표기: **β (HAC t)** [tier]. n=5052 (commodity 5028), VIF 전 factor ≈1.0~1.14, ADF factor·return 전부 p=0.0.

| sleeve / unit | rate | dollar | oil | credit | vol |
|---|---|---|---|---|---|
| **gold** / GOLD (GLD) | −0.215 (−12.0) [val] | −0.317 (−16.7) [val] | +0.121 (+4.4) [val] | −0.014 (−0.8) [rej] | −0.011 (−0.4) [rej] |
| **eq_us_cyclical** / CYCLICAL_PRO (XLB·XLI·SOXX) | +0.105 (+6.5) [val] | −0.171 (−10.0) [val] | +0.036 (+1.6) [struct] | −0.004 (−0.3) [rej] | **−0.687 (−27.9) [val]** |
| **eq_us_cyclical** / XLE_ENERGY (XLE) ★별 unit | +0.121 (+6.6) [val] | −0.120 (−5.0) [val] | **+0.342 (+5.1) [val]** | −0.037 (−1.8) [struct] | −0.473 (−20.2) [val] |
| **eq_intl** / EQ_INTL (EFA·EEM) | +0.094 (+6.2) [val] | −0.295 (−16.6) [val] | +0.043 (+2.5) [struct] | −0.042 (−2.5) [struct] | −0.641 (−21.4) [val] |
| **reit** / REIT (VNQ) | −0.004 (−0.2) [rej] | −0.090 (−3.5) [val] | −0.004 (−0.2) [rej] | −0.025 (−1.2) [rej] | **−0.565 (−16.0) [val]** |
| **commodity** / COMMODITY (DBC) | +0.067 (+3.5) [val] | −0.205 (−9.0) [val] | **+0.613 (+6.2) [val]** | −0.034 (−2.0) [struct] | −0.141 (−8.8) [val] |

(uni β + se 는 json 참조. 위는 multivariate 5 factor 동시 std β.)

## 3. ★vol(ΔVIX) factor 흡수 현상 — sample 재현

sample-stage 에서 "rate β 가 vol 통제 시 흡수"가 batch 에서도 강하게 재현:

- **equity 전부 (cyclical/intl/reit)** vol β = −0.57~−0.69 강음, |t|=16~28. equity sleeve 가 VIX 채널에 압도적 노출.
- **REIT rate**: univariate +0.134 (t=4.3) 이던 것이 multivariate(vol 통제)에서 −0.004 (t=−0.2, **reject**)로 소멸.
  → REIT 의 단변량 rate 신호 상당부분이 risk-off(VIX) 공통인자의 위장. 직접 rate β 는 약함.
- **cyclical rate**: uni +0.279 → multi +0.105 (양으로 축소, 여전히 유의). vol 이 rate 의 절반 이상 흡수.
- → **vol factor pool 형성 가능 sleeve = 5개** (gold 제외 전부 vol validated): cyclical_pro, xle, eq_intl, reit, commodity. gold vol 만 reject.
  현재 SEED 는 전 sleeve vol=HOLD(노출 0) → 5 sleeve 채우면 pool 활성화 (VIX↑=cyclical−defensive excess contemp 채널이 게이트에 들어옴).

## 4. ★분석 unit 분리 권고 (§1.6)

- **XLE 별도 unit 필수** (이미 분리 산출). XLE oil β=+0.342 (val) vs cyclical_pro oil +0.036 (비유의). XLE 를
  cyclical_pro 에 eq-weight 합치면 oil loading 이 cancel/희석. XLE 는 oil-driven energy unit 으로 SEED 별 cell 권고.
  단 rate/dollar/vol 부호는 cyclical_pro 와 동일(anti-cyclical 이 아니라 같은 risk-on factor 구조, oil 만 특이) →
  "XLE=anti-cyclical 부호 반대" 라는 기존 framing 은 **rate/dollar/vol 차원에선 성립 안 함**, oil 차원만 특이. hedge.
- 나머지 sleeve 는 단일 unit 으로 부호 일관 (cyclical_pro 내 XLB/XLI/SOXX 동방향, eq_intl 내 EFA/EEM 동방향).

## 5. tier 제안 + 기존 SEED 대비 변화

| sleeve | factor | 기존 SEED (tier) | batch 제안 (tier) | 변화 메모 |
|---|---|---|---|---|
| gold | rate | −0.295 val | −0.215 val | 재현 일치, 유지 |
| gold | dollar | −0.328 val | −0.317 val | 거의 동일, 유지 |
| gold | oil | +0.230 val | +0.121 val | 부호 일치, 크기↓ |
| gold | credit | HOLD | **reject** (t=−0.8) | 측정됨, 비유의 — pool 노출만 |
| gold | vol | HOLD | **reject** (t=−0.4) | gold 는 vol 채널 없음 |
| eq_us_cyclical | rate | −0.07 struct | **+0.105 val** ★부호반전 | uni 도 +0.28. risk-on 시 금리상승 동반 |
| eq_us_cyclical | dollar | −0.55 val | −0.171 val | 부호 일치, **크기 크게↓** (multi 통제·std β 단위차) |
| eq_us_cyclical | oil | +0.10 struct | +0.036 struct | 부호 일치 |
| eq_us_cyclical | credit | HOLD | reject | 비유의 |
| eq_us_cyclical | vol | HOLD | **−0.687 val** ★신규 | 최강 노출, pool 형성 |
| eq_intl | rate | −0.03 reject | **+0.094 val** ★부호반전 | 기존 "rate-up 증폭 기각" 과 별개 차원(same-day co-move) |
| eq_intl | dollar | −0.41 val | −0.295 val | 부호 일치, 크기↓ |
| eq_intl | oil | +0.05 struct | +0.043 struct | 일치 |
| eq_intl | credit | HOLD | struct (t=−2.5) | 약 신호 |
| eq_intl | vol | HOLD | **−0.641 val** ★신규 | 강 노출 |
| reit | rate | −0.45 val | **−0.004 reject** ★소멸 | uni +0.13(부호도 반대). vol 흡수. ⚠️아래 caveat |
| reit | dollar | −0.30 val | −0.090 val | 부호 일치, 크기↓ |
| reit | oil | HOLD | reject | 비유의 |
| reit | credit | HOLD | reject | 비유의 |
| reit | vol | HOLD | **−0.565 val** ★신규 | 강 노출 |
| commodity | rate | HOLD | +0.067 val | n=12분기→5028일 확대, 약 양 |
| commodity | dollar | −0.45 struct (n=12) | −0.205 val (n=5028) | ★n 대폭 확대로 structural→validated 승격 가능, 크기↓ |
| commodity | oil | +0.40 struct | **+0.613 val** | n 확대, oil-driven 확인·승격 |
| commodity | credit | HOLD | struct (t=−2.0) | 약 신호 |
| commodity | vol | HOLD | **−0.141 val** ★신규 | 약하나 유의 |

### ⚠️ 핵심 caveat (박제 전 main 판단 필요)

1. **rate 부호 반전 (cyclical/eq_intl)**: batch same-day std β 에서 equity rate β 가 **양(+)**. 기존 SEED 음(−)은
   서로 다른 측정 axis(기존 = level/forward 또는 다른 spec). same-day daily diff 회귀에선 "risk-on 날 = 금리도
   오름" 의 co-move 가 잡힘. **spec/code axis 불일치** (§1.3) — 단순 덮어쓰기 금지, axis 명시 후 채택.
2. **reit rate 소멸**: 기존 SEED rate −0.45 (rate 직접 민감 = REIT 핵심 thesis) 가 batch daily multi 에서 −0.004
   (uni 는 +0.13, 부호 반대). 이건 **REIT rate thesis 가 lower-frequency/level 효과**임을 시사 (daily diff 로는 안
   잡히고 vol 에 흡수). ★기존 −0.45 를 daily std β 로 덮어쓰면 REIT 의 rate-duration 특성을 지움 — **유지 권고**
   (axis 다름). vol cell 만 신규 추가.
3. **dollar 크기 축소 일관**: 모든 sleeve dollar |β| 가 SEED 등급값보다 작음. 이유 = (a) SEED 가 univariate corr
   등급, batch 는 5-factor multivariate (vol 등 통제로 dollar 일부 흡수) (b) std β 단위. 부호·order 는 전부 일치.

## 6. SEED_CELLS 갱신 제안 (§7 별도 — main 일괄 Edit)

→ 별도 섹션 `## SEED_CELLS 갱신 제안` 참조. 보수적 원칙: **vol cell 5개 신규 채움(가장 깨끗·축적값) + commodity n 확대
승격** 우선, rate/dollar 덮어쓰기는 axis caveat 때문에 main 판단 보류 권고.

## SEED_CELLS 갱신 제안 (main 일괄 Edit)

원칙: (A) **vol cell 5개 신규** = 가장 안전·고가치 (현재 전부 HOLD=노출0, 측정값 깨끗 |t|=8~28, pool 활성화).
(B) **commodity** = n=12분기→n=5052일 대폭 확대로 structural→validated 승격 + oil/rate/credit 신규 측정.
(C) rate/dollar 덮어쓰기는 **axis caveat (§5)** 때문에 main 판단 보류 권고 — same-day daily std β 라 기존 등급값(다른 axis)과 의미 다름.

### Tier A — vol cell 신규 (강력 권고, 5 sleeve pool 형성)
```python
FactorCell("eq_us_cyclical", "vol", -0.687, se=0.025, t=-27.86, n=5052, tier=TIER_VALIDATED, note="J축 batch std β(CYCLICAL_PRO), 최강 risk-off 노출"),
FactorCell("eq_intl",        "vol", -0.641, se=0.030, t=-21.44, n=5052, tier=TIER_VALIDATED, note="J축 batch std β(EFA+EEM)"),
FactorCell("reit",           "vol", -0.565, se=0.035, t=-16.02, n=5052, tier=TIER_VALIDATED, note="J축 batch std β(VNQ)"),
FactorCell("commodity",      "vol", -0.141, se=0.016, t=-8.82,  n=5052, tier=TIER_VALIDATED, note="J축 batch std β(DBC), 약하나 유의"),
# gold vol = reject (t=-0.44) → HOLD 유지 권고 (gold 는 vol 채널 없음). 굳이 채운다면:
# FactorCell("gold", "vol", -0.011, se=0.024, t=-0.44, n=5052, tier=TIER_REJECT, note="J축 batch, gold vol 채널 없음"),
```
→ vol pool 형성 sleeve = 4개 validated (+ XLE 별 unit 시 5개). gold vol=reject. 전 sleeve HOLD 였던 vol 차원이
   pool 활성 → eq_us_defensive(HOLD) 도 equity_risk pool 통해 vol 노출 받게 됨 (VIX↑ contemp 채널 게이트 진입).

### Tier B — commodity n 확대 승격 (권고)
```python
FactorCell("commodity", "dollar", -0.205, se=0.023, t=-9.03, n=5052, tier=TIER_VALIDATED, note="J축 batch(DBC 일별), n=12분기→5052 승격, 기존 -0.45 structural"),
FactorCell("commodity", "oil",    +0.613, se=0.099, t=+6.20, n=5052, tier=TIER_VALIDATED, note="J축 batch(DBC), oil-driven 확인, 기존 +0.40 structural"),
FactorCell("commodity", "rate",   +0.067, se=0.019, t=+3.49, n=5052, tier=TIER_VALIDATED, note="J축 batch, 약 양(reflation), 기존 HOLD"),
FactorCell("commodity", "credit", -0.034, se=0.017, t=-1.99, n=5052, tier=TIER_STRUCTURAL, note="J축 batch, 약 신호"),
```

### Tier C — XLE 별 unit cell (신규 sleeve key, §1.6 unit 분리)
```python
# ★주의: SEED 에 'eq_us_cyclical_xle' 또는 'xle_energy' 신규 sleeve key 추가 시 POOL_GROUP 매핑도 필요
#   (equity_risk or commodity_real 판단은 main). 보류 시 cyclical 에 흡수되나 oil loading 희석 위험.
FactorCell("xle_energy", "oil",    +0.342, se=0.068, t=+5.05, n=5052, tier=TIER_VALIDATED, note="J축 batch(XLE), oil-driven energy"),
FactorCell("xle_energy", "vol",    -0.473, se=0.023, t=-20.24, n=5052, tier=TIER_VALIDATED, note="J축 batch(XLE)"),
FactorCell("xle_energy", "rate",   +0.121, se=0.018, t=+6.63, n=5052, tier=TIER_VALIDATED, note="J축 batch(XLE)"),
FactorCell("xle_energy", "dollar", -0.120, se=0.024, t=-5.01, n=5052, tier=TIER_VALIDATED, note="J축 batch(XLE)"),
FactorCell("xle_energy", "credit", -0.037, se=0.021, t=-1.76, n=5052, tier=TIER_STRUCTURAL, note="J축 batch(XLE)"),
```

### Tier D — rate/dollar 덮어쓰기 후보 (★axis caveat, main 판단 보류 권고)
same-day daily std β. 기존 SEED 등급값과 axis 다름 — 덮어쓰려면 study yaml spec axis 와 정합 확인 후.
```python
# eq_us_cyclical: rate 부호반전(+0.105, 기존 -0.07), dollar 크기축소(-0.171, 기존 -0.55)
# eq_intl:        rate 부호반전(+0.094, 기존 reject -0.03), dollar 크기축소(-0.295, 기존 -0.41)
# reit:           rate 소멸(-0.004, 기존 -0.45 ★유지 권고 — daily 로 안 잡히는 duration 효과), dollar(-0.090, 기존 -0.30)
# gold:           재현 일치 → 유지(rate -0.295/dollar -0.328/oil +0.230 그대로 둬도 batch 와 부호·order 정합)
```

### gold credit/vol 측정 결과 (참고, HOLD→reject 정정 후보)
```python
# gold credit = -0.014 (t=-0.78) → reject (측정됨, 비유의). vol = -0.011 (t=-0.44) → reject.
# 기존 HOLD 그대로 둬도 무방 (pool 노출만). 측정 사실 반영하려면 reject 로 갱신.
```

## 산출 파일
- `study-research/_factor_shadow/batch-std-beta-5sleeve.py` (스크립트)
- `study-research/_factor_shadow/batch-std-beta-5sleeve.json` (전체 수치: uni+multi+VIF+ADF+coverage)
- `study-research/_factor_shadow/batch-std-beta-5sleeve.md` (본 종합)

★core/study/ 미수정 · git 커밋 안 함. SEED_CELLS Edit 은 main 이 위 제안 검토 후 적용.
