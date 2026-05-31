---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/L-axis-integration]
date: 2026-06-01
study_id: eq_intl
sleeve: equity.intl
session: btn-eq_intl-L-axis-fullsample
raw_source: raw/validation-L-axis-dtwexbgs-fullsample.py + raw/merit_cache/
principles: [PIT 종가, 합성 금지(실 캐시), monthly log-return, partial-corr, Fisher-z CI, Bonferroni, ADF 사전, hedge 어휘(n<300)]
scope: "L축 재검 — fx_carry↔β_dollar overlap 을 DXY n=59 window 에서 DTWEXBGS broad-dollar full-sample(n=171~244)로 재측정. 직전 n=59 caveat(짧은 window) 해소 판정"
indicators: [fx_carry_momentum, dollar_beta_country]
supersedes_caveat: "validation-L-axis-fx-dollar-overlap.md §5.4 (DXY window 한정 caveat)"
---

# eq_intl L축 재검 — fx_carry↔β_dollar overlap **broad-dollar full-sample**

> **게이트**: 직전 L축 측정(`validation-L-axis-fx-dollar-overlap.md`)의 dollar proxy = DXY(yahoo)
> 가용 2021-06~ → **monthly n=59 로 짧음**. handoff §3 가 "DTWEXBGS broad-dollar full-sample(n=309~362)
> 재검 의무" 로 명시. 본 산출이 그 재검 → caveat 해소 / 재조정 판정.

## §0. 데이터 provenance + 검증 (재계산 가능)

| 변수 | 소스 | 정의·단위 | 가용 범위 (★실측 검증) | 빈도 |
|---|---|---|---|---|
| dollar 채널 (broad) | FRED `DTWEXBGS` | Nominal Broad USD Index, Δlog | **2006-01-02 ~ 2026-05-22** (daily n=5112) | D→M |
| fx_carry | FRED `DEX{BZ,KO,IN,MX}US` | USD/local 3m(63bd) log-mom (merit §4 Bonferroni 생존 채널). 상승=local 약세 | brazil 1995~ / korea 1981~ / india 1973~ / mexico 1993~ | D→M |
| 국가 ETF | merit_cache `yf_{EWZ,EWY,INDA,EWW}.json` | monthly adjclose(TR) log-return | EWZ 2000-07 / EWY 2000-05 / INDA 2012-02 / EWW 1996-03 | M |

- **★handoff 추정 정정**: handoff §3 가 "DTWEXBGS full-sample n=309~362, 1996~ 가용" 로 추정했으나
  **FRED `series` 메타 실측 = observation_start 2006-01-02** (BIS broad-dollar 라이센스, narrow DTWEXM 과 별개).
  → broad-dollar 2006 시작이 **하한 binding**. full-sample n = ETF·FX·DTWEXBGS 교집합.
- **실 full-sample n**: brazil/korea/mexico **244mo** (2006-02~2026-05), india **171mo** (2012-03~, INDA 상장 제약).
  → DXY window n=59 대비 **3~4배**. n=309~362 추정은 broad-dollar 2006 시작으로 미달이나, robustness 판정엔 충분.
- **합성 지문 검사**: 전 시리즈 실 fetch(merit_cache JSON). 2008 GFC·2015 dollar surge·2022 금리쇼크 실재 cover.
- **측정 axis = monthly contemporaneous** (n=59 DXY 측정과 **동일 axis** → 1:1 비교). fx_carry = mom_3m.
- **ADF 사전(merit §1.7-A)**: broad-dollar monthly **level t=-1.04 (> -2.88 → I(1) 단위근)**,
  **Δlog t=-6.58 (< -2.88 → I(0) 정상)** → 회귀 단위 = Δlog. spurious level 회귀 회피 PASS.
- **★n<300 hedge**: india n=171, 그 외 244 — n=59 보다 robust 하나 still 단일 epoch(2006~) → 단정 금지, 방향성 prior + CI.
- 재현: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python raw/validation-L-axis-dtwexbgs-fullsample.py`

## §1. 직접 overlap — fx_carry ↔ broad-dollar(DTWEXBGS Δlog)

| 국가 | n | coverage | r(fx, broad$) | 공통 R²(%) | p |
|---|---:|---|---:|---:|---:|
| brazil | 244 | 2006-02~2026-05 | +0.413 | 17.0 | 1.8e-12 |
| korea | 244 | 2006-02~2026-05 | **+0.492** | **24.2** | 1.5e-18 |
| india | 171 | 2012-03~2026-05 | +0.253 | 6.4 | 6.8e-04 |
| mexico | 244 | 2006-02~2026-05 | +0.392 | 15.3 | 3.6e-11 |
| **평균** | | | | **15.7%** | |

★ broad-dollar full-sample 직접 overlap 평균 R² **15.7%** (DXY n=59 = 8.7%). 부호 동일(양 = USD/local
약세↔broad$ 강세). broad-dollar 가 narrow DXY 보다 EM 통화를 더 담아 overlap 이 다소 큼(예상 방향).
korea 최대(24.2%)·india 최소(6.4%) 의 **국가별 순위는 n=59 와 동일**(korea > brazil/mexico > india).

## §2. partial correlation — dollar 통제 후 ETF↔fx 잔존 (★핵심)

| 국가 | raw r(ETF,fx) | r(ETF,fx \| $) | 95% CI | p | r(ETF,$ \| fx) |
|---|---:|---:|---:|---:|---:|
| brazil | −0.497 | **−0.323** | [−0.431, −0.205] | 1.2e-07 | −0.611 |
| korea | −0.392 | **−0.090** | [−0.213, +0.037] | 0.16 (n.s.) | −0.609 |
| india | −0.384 | **−0.309** | [−0.439, −0.167] | 2.5e-05 | −0.434 |
| mexico | −0.481 | **−0.310** | [−0.420, −0.192] | 4.0e-07 | −0.667 |
| **평균** | | **−0.258** | | | **−0.580** |

★ **dollar 통제 후 ETF↔fx_carry 잔존 partial-corr 평균 −0.258** (DXY n=59 = −0.315). **부호·크기대 일치**
(둘 다 −0.25~−0.32 영역, CI 겹침). brazil/india/mexico 는 dollar 통제 후에도 유의 잔존(p<1e-4, Bonferroni
생존) = **fx_carry 가 broad-dollar 와 별개의 독립 환 정보 보유** — n=59 결론과 동일.
★ **korea 만** dollar 통제 시 −0.39→−0.09 (p=0.16, 비유의) = KRW 환이 broad-dollar 와 강 중첩 — **n=59 와
정확히 같은 예외 패턴**(KRW 의 broad-dollar 베타 높음, 반도체·수출 cyclical).
★ 반대로 fx 통제 후 ETF↔dollar 는 강 유지(−0.43~−0.67, 평균 −0.580, Bonferroni 생존) = dollar 도 독립 robust.

## §3. ETF 설명분 commonality decomposition

| 국가 | R²(both) | unique_$ | unique_fx | common | common/both(%) |
|---|---:|---:|---:|---:|---:|
| brazil | 0.528 | 0.281 | 0.055 | 0.193 | 36.4 |
| korea | 0.468 | 0.314 | 0.004 | 0.149 | 31.9 |
| india | 0.308 | 0.161 | 0.073 | 0.075 | 24.2 |
| mexico | 0.573 | 0.342 | 0.046 | 0.186 | 32.4 |
| **평균** | | | | | **31.2%** |

★ ETF 설명분의 **약 31% 가 dollar·fx 공유분(중복)** (DXY n=59 = 25.1%). full-sample 에서 dollar·fx 공통
비중이 다소 커짐(broad-dollar 가 EM 통화 더 포함). dollar **unique 가 fx unique 를 크게 상회**(unique_$
평균 0.27 vs unique_fx 0.04) = **이 4 EM 의 ETF 분산은 dollar 가 1차 driver, fx 는 dollar 위 incremental**.
★주의: 직전 n=59 md §5.1 의 "fx 독립 기여 ~75%" 표기는 partial-corr(−0.315)을 share 로 환산한 느슨한
표현이었음. commonality 정식 분해로는 **fx 의 ETF-설명 unique share 는 작음(~11%)**, 대신 **dollar 통제
후 partial-corr 가 −0.26 으로 유의 잔존** = "fx 가 독립 신호를 갖되 ETF 분산 설명력 자체는 dollar 우위"
가 정직한 서술. 이중계상 회피의 근거는 partial-corr 잔존(orthogonal residual 유효)이지 share 크기가 아님.

## §4. 다중비교 (Bonferroni)

12 비교(4국 × {ETF↔fx\|$, ETF↔$\|fx, fx↔$ overlap}): α/m=0.0042. raw p<0.05 = 11/12, **Bonferroni 생존
= 11/12** (korea ETF↔fx\|$ 만 비유의 — §2 KRW-broad$ 중첩 예외). n=59(8/12 생존) 대비 full-sample 에서
유의성 강화 = 표본 확대 효과.

## §5. verdict — **CAVEAT 해소 (PARTIAL OVERLAP robust)**

### 5.1 DXY n=59 ↔ DTWEXBGS full-sample 대비

| 지표 | DXY n=59 (직전) | DTWEXBGS full (재검, n=171~244) | 일치 |
|---|---:|---:|:---:|
| fx↔dollar 직접 overlap R² | 8.7% | 15.7% | ≈ (broad$ 가 narrow 보다 큼, 방향 예상대로) |
| ETF 설명분 common share | 25.1% | 31.2% | ≈ |
| dollar 통제 후 ETF↔fx 잔존 partial | −0.315 | **−0.258** | ★부호·크기대 일치 (CI 겹침) |
| korea 예외 (dollar 통제 후 비유의) | 있음 (−0.30→−0.12) | 있음 (−0.39→−0.09 p=0.16) | ★동일 패턴 |
| Bonferroni 생존 | 8/12 | 11/12 | 강화 |

### 5.2 판정 — **★CAVEAT 해소**

- 직전 n=59 의 "DXY window 한정" caveat = full-sample(n 3~4배, 2008/2015/2022 dollar cycle 포함)에서
  **핵심 정성 결론(부분 중복·대체로 독립·korea 예외)이 robust 하게 재현**. partial-corr 부호·크기대 일치,
  국가별 순위 동일, korea 예외 동일.
- broad-dollar overlap 이 narrow DXY 보다 다소 큼(8.7→15.7%, common 25→31%)은 **DTWEXBGS 가 EM 통화를
  직접 담아서** = 경제적으로 타당한 방향(spurious 아님), 결론을 뒤집지 않음.
- ★단정 금지(n<300 + 단일 epoch 2006~): "robust 한 방향성 prior" 로 hedge. magnitude 점추정 박제 X.

### 5.3 J축 통합 권고 (변동 없음 — 재검으로 강화)

1. **β_dollar(broad, daily)** 와 **fx_carry(local-FX 3m mom, monthly)** = 별도 entry 유지 정당
   (dollar 통제 후 fx partial −0.258 유의 잔존, brazil/india/mexico Bonferroni 생존).
2. **공통 broad-dollar 인자(≈31% 공유분)는 1회만 계상** — fx_carry 는 **dollar-orthogonalized 잔차**로
   entry(partial −0.258 이 그 잔차 신호). PSD 보존 + 중복 제거 동시. 단순 가산(중복 반영) 지양.
3. **korea 예외 유지**: KRW↔broad$ overlap 최대(24%), dollar 통제 후 fx 비유의(p=0.16) → korea
   sub-archetype 한정 1회 계상(택1) 또는 강 orthogonalize. 다른 3국은 별도 유지 안전.

### 5.4 잔여 caveat (해소 후)

- DTWEXBGS 2006 시작 → 1980s/1990s dollar cycle 미cover (FRED broad-dollar 자체 한계, 대안 없음).
  더 긴 history 필요 시 narrow DTWEXM(1973~) 로 보조 가능하나 broad 채널 본 측정이 1차.
- india n=171 (INDA 상장 2012) → 다른 3국 244 보다 짧음. 단 부호·partial 일치로 약 prior 충분.
- 본 재검은 직전 md §5.4 "DXY window 한정 → DTWEXBGS 재검 의무" caveat 를 **충족·해소**.
