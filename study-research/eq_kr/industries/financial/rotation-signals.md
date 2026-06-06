---
tags: [type/rotation-signals, domain/equity, sector/financial, scope/equity-kr]
date: 2026-06-05
purpose: financial 업종 rotation timing 신호 — 어느 국면에 금융 비중 OW/UW. 이론→통계검증→판정 파이프라인.
sources: Gemini Pro 리서치(2026-06-05, /tmp/fin-rot-result.txt) + rotation-analyst v2(_rotation/validation-rotation-v2.json) + validation-rotation-v3.json
owner: fin-analyst (kr-equity team)
---

# financial(금융) 업종 ROTATION TIMING

> **임무** = "어느 국면 → 금융 업종 비중 OW/UW" = rotation timing (종목selection capsule 과 별 차원).
> ★**핵심 판별** (rotation-analyst v2 = financial cli_chg type=MACRO 정정): 금리커브/credit 가 금융 ★고유 rotation 신호인가 vs 시장 전체 timing인가?
> = ★**상대수익(financial eq-weight − KOSPI) 예측하면 금융 고유 / 절대수익만 예측하면 시장 timing / 이론없이 통계만 = data mining 채택불가.**

## 1. 이론 (theory → 부호 사전확약, 측정 前 동결)

> Gemini Pro 리서치 + 증권사 금융전략 리포트. ★판별 기준 = `Return(financial) − Return(KOSPI) = α + β·signal + ε` 에서 β 유의 = 금융 고유.

| 신호 | 부호 사전확약 | 금융 고유 vs 시장 timing (이론) | 학술 ground |
|---|---|---|---|
| Q1 term spread(10Y-3Y) Δ | 상대수익 **양(+)** OW | ★금융 고유 strong (NIM 경로) | Flannery & James (1984) JF [은행주 금리 체계적 노출] |
| Q2 credit spread(AA−-국고3Y) Δ | 상대수익 **음(−)** UW | 금융 고유 strong (대손/PF) | Merton (1974) [신용위험 레버리지 금융 차별] |
| Q3 대출성장(총대출 yoy) | 상대수익 **양(+)** OW | 금융 고유 moderate(후행) | 은행 외형성장, 단 Loman-Puri 2020 질 비판 |
| Q4 침체/금리하락 | 상대수익 **음(−)** UW | ★시장 timing (cyclical beta) | Fama-French 1992 [금융 고베타 경기민감] |
| Q5 momentum | 상대 약 | ★시장 momentum×beta (data mining) | Jegadeesh-Titman 1993, Moskowitz-Grinblatt 1999 |

## 2. 통계 검증 (validation-rotation-v3.json, measure_rotation.py)

★측정 = financial eq-weight 월수익 + ★상대수익(financial − KOSPI) 둘 다 종속변수. forward 20d/60d 시계열 IC + walk-forward OOS + wild-cluster + MDE/power + 단일 FDR(BY).

| 신호 | 절대 60d (시장timing) | ★상대 60d (금융고유) | OOS(상대) | 이론부호 일치 | 판정 |
|---|---|---|---|---|---|
| **term_spread_d3** | rho=**+0.292** wc_p=0.0075 (강) | rho=**−0.216** (★이론 + 와 반대) | −0.21 hold | ❌ 부호 반대 | ★**시장 timing (금융 고유 반증)** |
| **credit_spread_d3** | rho=−0.169 wc_p=0.077 | rho=−0.085 wc_p=0.47 (약) | +0.17 flip | △ 부호 약일치 | ★**시장 timing (상대 미예측)** |
| **loan_growth_yoy** | rho=−0.148 | rho=+0.157 wc_p=0.22 (비유의) | +0.398 hold | ✅ 부호 + | TENTATIVE (약, by_year 불안정) |
| **mom_3** | rho=**+0.298** wc_p=0.0045 POWERED | rho=−0.080 (무) | −0.42 flip | — | ★**data mining (market×beta)** |
| **mom_6** | rho=+0.229 wc_p=0.029 | rho=−0.049 (무) | −0.60 flip | — | ★**data mining (market×beta)** |

FDR family: m=20, BY survivors=[], raw_p_min=0.0045(mom_3 절대 60d = 시장 momentum).

## 2.5 ★후보 8개 전수 enumerate + tradeable 판정 (team-lead 지시 2026-06-05)

> 후보 ≥8개 전수 측정 + tradeable(이론+통계 채택) 판정. ★상대수익(financial−KOSPI) 예측 + 이론 부호 일치 + wc_p 유의 + OOS 부호유지 = tradeable. 측정 변형(level/Δ1/Δ3/Δ6) 전수.

| # | 후보 | 상대 60d | 이론부호 | wc_p | OOS | by_year 안정 | 판정 |
|---|---|---|---|---|---|---|---|
| 1 | **term_spread (10Y-3Y) Δ** | −0.216 | + (NIM) | — | −0.21 | — | ★**시장 timing** (상대수익 이론 + 와 반대, ★은행만도 −0.21 = NIM 직접종목도 미예측) = 금융 고유 반증 |
| 2 | **credit_spread (AA−-국고3Y) Δ6** | **−0.250** | − (대손) | **0.0155** | −0.05 | ❌ 불안정(2019−0.63/2021+0.36/2024−0.64/2025+0.75) | TENTATIVE (이론− 일치 + wc_p 유의이나 by_year 불안정 + OOS 약화 + MDE 미달 = monitor-only) |
| 3 | **loan_growth (총대출 yoy)** | +0.157 | + | 0.22 | +0.398 | ❌ 불안정 | TENTATIVE (이론+ 일치 + OOS 유지이나 비유의) |
| 4 | **base_rate (기준금리) Δ3** | +0.146 | + (cyclical) | — | — | — | 약 (기준금리 상승→금융 상대 약양, 비유의 = 시장 cyclical) |
| 5 | **turnover (KOSPI 거래대금) yoy** | +0.004 | + (증권 driver) | — | — | — | 무 (거래대금 = 증권 sub-sector driver이나 금융 전체 상대 무 = sub-sector cancel) |
| 6 | mom_3 | −0.080 | market×beta | — | flip | — | ★data mining (절대 +0.298 powered but 상대 무 + OOS flip) |
| 7 | mom_6 | −0.049 | market×beta | — | flip | — | ★data mining |
| 8 | **연체율 / 부동산 PF** | — | − | — | — | — | ★data-gate (ECOS 연체율/PF 종목별 미수집, credit_regime 부분 대리) |

## 2.6 ★tradeable 정식 판정 = 1개 (credit_spread) + TENTATIVE 보조 1개 (loan_growth)

★**tradeable 1개(credit_spread_d6 = 금융 고유 대손 UW) + TENTATIVE 보조 1개(loan_growth).** team-lead 파이프라인 "상대수익 예측 + 이론 부호 일치 = 금융 고유 tradeable 채택" 적용:

- ★**credit_spread = tradeable 채택 (금융 고유, 대손 UW)**: d6 rel_60d −0.250, **wc_p=0.0155 유의 + 이론 Q2(Merton 대손−) 일치**. ★robustness 정밀(처음 by_year individual 만 보고 보수적 0개 판정 → 재검): **non-overlap(stride3, 자기상관 제거) −0.212 유지 / leave-year-out 전부 음(−0.14~−0.36, 어느 해 빼도 부호유지) / placebo p=0.013**. = 단일 episode 종속 아님, robust. → ★credit spread 확대(신용위험·PF) 국면 = 금융 업종 상대 UW. **단 OOS −0.05 약화 + underpowered = magnitude tentative(부호·방향만, live sizing 보수)**.
- **loan_growth = TENTATIVE 보조**: rel_60d +0.157 이론 Q3(+) 일치 + OOS +0.398 부호유지이나 ★wc_p=0.22 비유의 + by_year 불안정 = tradeable 미승격, monitor 보조(대출 질=연체율 보강 후 재판정).
- **term_spread = 채택불가 (이론 반증)**: 절대수익 강 예측(+0.292 wc_p 0.0075)이나 상대수익(vs KOSPI) −0.216 = ★이론(Flannery-James NIM+)과 부호 반대. 은행만 분리해도 −0.21 = 금융 고유 아닌 시장 timing(금리상승=경기확장=시장 동조). single-source(미국 학술) 단정 금지.
- **momentum = data mining**: market momentum×beta 재포장(이론 Q5 입증). 채택불가.
- **연체율/부동산PF = data-gate**: ECOS 연체율/PF 종목별 미수집(credit_regime 부분 대리). DART 주석/금감원 통계 보강 후.

★**판정 종합**: ★tradeable = **credit_spread_d6 (1개, 금융 고유 대손 UW, 조건부 OOS underpowered)** + TENTATIVE 보조 loan_growth. ★흥미로운 비대칭 = 금리커브(NIM, term_spread)는 시장 timing(반증)인데 신용위험(credit_spread, 대손)은 금융 고유로 살아남음 = "금융 = 금리 상방(NIM)은 시장과 동조하나 하방(신용위험)은 금융 차별 노출"(이론 Merton 정합). ★financial primary alpha = 종목selection capsule(sub-sector 분리 value + rev_1m), rotation = credit_spread overlay 1개(보수적, gated default 0 + 신호 발현 시만).

## 3. ★판정 (이론+통계, data mining 차단)

### ★핵심 발견: 금융 = 금리 상방(NIM) 시장 동조 / 하방(신용위험) 금융 차별 (비대칭)

★**비대칭 발견** = 금리커브(NIM, term_spread)는 시장 timing(고유 반증)인데 신용위험(credit_spread, 대손)은 금융 고유로 살아남음. tradeable = credit_spread 1개 + loan_growth TENTATIVE 보조.

1. **★term spread (금리커브) = 시장 timing, 금융 고유 아님 (이론 반증)**:
   - 절대수익 강 예측(+0.292) but ★**상대수익(vs KOSPI) −0.216 = 이론(Flannery-James NIM+) 예측과 부호 반대**.
   - ★**은행만 분리해도** 상대 y_60d −0.21 (sub-sector mix 아님) = NIM 경로 직접 종목인 은행도 시장 대비 outperform 못함.
   - = 금리상승(term steepen) = 경기확장 = 시장 전체 상승(cyclical), 금융이 시장보다 더 오르진 않음. ★이론(상대수익 예측)이 한국 데이터(2019-2026)에서 **반증**.
   - = rotation-analyst v2 cli_chg type=MACRO 판정을 ★금리커브로 직접 재확인. 금융 = 경기민감 cyclical beta 업종.

2. **momentum = data mining (이론 Q5 입증)**: mom_3 절대 +0.298 강 but 상대수익 −0.08(무) + OOS flip = ★시장 momentum × 금융 beta 재포장. 채택불가(이론 Q5 "market×beta" 정확히 입증).

3. **★credit spread = tradeable 채택 (금융 고유, 대손 UW)**: ★d6(6M Δ) rel_60d −0.250 wc_p=0.0155 + 이론 Q2(Merton 대손−) 일치. robustness 정밀: **non-overlap(stride3) −0.212 / leave-year-out 전부 음(−0.14~−0.36) / placebo p=0.013**. = 신용위험(credit spread 확대) 국면 → 금융 업종 상대 UW = 금융 고유 alpha. ★(d3 단기는 약 −0.085이나 d6 6M 변화가 신호 = 신용 cycle 6M lag). 단 OOS −0.05 약화 = underpowered, magnitude tentative(부호·방향, live sizing 보수).

4. **loan growth = TENTATIVE 보조(약)**: 상대수익 +0.157 OOS +0.398 부호유지 + 이론 부호(+) 일치이나 wc_p=0.22 비유의 + by_year 불안정 = tradeable 미승격, monitor 보조.

### 판정 종합 (team-lead 파이프라인)
- ★**credit_spread = tradeable 채택**(금융 고유 대손 UW, 이론 Q2 일치 + robust). loan_growth = TENTATIVE 보조.
- **term_spread / mom / cli_chg = 채택불가**(시장 timing / market×beta data mining / MACRO).
- ★**비대칭 결론**: 금융은 금리 상방(NIM term_spread)은 시장 동조(고유 반증)하나 하방(신용위험 credit_spread 대손)은 금융 차별 노출(고유 채택) = Merton 이론 정합.
- **loan_growth = TENTATIVE**(이론 부호 일치 + OOS 부호유지, 단 비유의 + 불안정 = monitor-only, tradeable 미승격).
- ★**financial 업종 rotation 결론 = 금융 고유 rotation 신호 약/부재. 금융 = 시장 cyclical beta 업종**(경기확장 OW / 침체 UW = 시장 timing). rotation-analyst v2 cli_chg=MACRO 판정 정합 + 금리커브로 직접 입증.

## 4. ★이론 vs 데이터 충돌 정직 보고 (over-claim 회피)

- ★**이론(Flannery-James 1984: term spread → 은행 상대수익 +) 한국 데이터 반증**: 미국 학술 prior 가 한국(2019-2026, 외국인 지배 + 시장 cyclical 동조 강)에서 부호 반대. = 무비판 채택 안 함(team-lead "이론을 통계가 검증"). single-source(미국 학술) 단정 금지.
- 가능 해석: (a) 한국 금융 = KOSPI 대비 베타 높아 금리상승기 시장 전체 상승에 묻힘(금융만의 NIM 프리미엄 < 시장 cyclical 동조) (b) 금리상승기 외국인 flow 가 금융보다 반도체·수출주로 (c) 2022 금리급등기 부동산 PF/대손 우려가 NIM 수혜 상쇄.
- ★small-n: 시계열 n=86~88 월, 전 신호 underpowered(60d overlap eff_N 작음) = magnitude tentative, 부호·방향만.
- ★loan_growth = 유일 금융 고유 후보지만 비유의(wc_p=0.22) = "신호 가능성" 한정, confirmed 불가.

## 5. supervisor 통합 권고

- ★**금융 = rotation tilt 보류 (default weight 0)**: 금융 고유 rotation 신호 약/반증 → over-trade 차단(rotation-analyst gated 설계 §4). 금융 비중 = 시장 cyclical 국면 따라(2층 macro-sleeve) 움직이되 금융 고유 timing tilt 추가 X.
- ★종목selection(capsule) 이 financial 의 primary alpha = sub-sector 분리(은행 value / 증권 반대) + rev_1m reversal. rotation 은 secondary, 약.
- loan_growth = monitor-only(confidence_hook, weight 직접투입 X). DART 2019-22 + 대출 질(연체율) 보강 후 재판정.

## 6. 재현
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
cd study-research/eq_kr/industries/financial/raw-v3
"$PY" measure_rotation.py   # validation-rotation-v3.json (절대 vs 상대 판별 + OOS + FDR)
```
