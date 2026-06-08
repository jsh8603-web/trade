---
tags: [type/round-1, domain/equity-us, sector/semiconductor, phase/sector-granular]
date: 2026-06-08
sector: soxx_semi
purpose: 미국 반도체 섹터 granular 파일럿 — 이론·가설(반증조건)·measurement 설계 R1 초안. SECTOR-GRANULAR-GUIDE §10 자문 3R 수렴 반영. ★사용자 점진 1번 파일럿(1→수정→3→티어).
ssot: [eq_us/SECTOR-GRANULAR-GUIDE.md §10, AUDIT-GUIDE.md(15축), eq_kr/industries/semiconductor/summary.yaml(템플릿)]
status: R1 보강 완료 (2026-06-08) — theory-notes.md 신설 + 가설 정련 + ★E축 환각검증(FRED id 3건 날조 적발). 메인 검수 후 R2 진입
---

> ★R1 보강 로그 (2026-06-08): Gemini 2-Phase 리서치 4건 + 인용 환각검증 + FRED id 실존검증 → `theory-notes.md` 박제.
> 핵심 = (1) value premium = within-semi 에선 value+quality 결합 필수(value-trap 위험) (2) ★H2(κ) falsify 강화:
> book-to-bill 류 = 주가가 선행(지표 후행) + SEMI bookings 2016 종료·billings 2022 무료단절 + 대체 lead(대만/한국수출)도
> coincident (3) 미국 regime = 실질금리(DFII10)×credit(Baa-Aaa) 2축 재설계, KRW_weak 이식불가, AI capex reflexivity 함정
> (4) ★sub-industry 이질성(팹리스/메모리/장비/아날로그) = style-bias 1급 오염 (5) ★E축 환각 적발 = §6.

# SOXX(미국 반도체) — round-1 이론·가설·measurement 설계

> ★진입 맥락: 자문 3R 수렴(`SECTOR-GRANULAR-GUIDE §10`). **방향 = primary는 within-sector value-selection(ρ), rotation은 회의적(~30%)으로 falsify 대상**. 한국 반도체(Tier1)와 대칭 비교하되 지표는 미국 고유 재설계.

## §0. 핵심 설계 결정 (자문 수렴 박제)

| 결정 | 내용 | 근거(자문) |
|---|---|---|
| 측정 단위 | rotation=EW-semi 시계열 / selection=종목 cross-section | 2-Tier 직교(κ⊥ρ) |
| ★벤치마크 | **EW-semi**(cap-weight SOXX 금지) | NVDA 단일베팅 위장 분리(claude) |
| Primary | within-sector **value-selection** forward excess(ρ) | selection-value = 미국 엣지 |
| Secondary | book-to-bill-family **κ 타이밍** 강등 | rotation ~30%, 데이터 의문 |
| 통제변수 | 관측가능 사전지정, PCA 기각 | PC1=EW-semi 내생성 |
| 결정실험 | within-sector predictive decomposition | γ null→(C) freeze |

## §1. 섹터 정의 + universe

**현 raw-v3 universe (SOXX_semi 12종)**: NVDA/AVGO/AMD/QCOM/TXN/MU/ADI/LRCX/KLAC/AMAT/INTC/MCHP.
- ⚠️ **생존편향(I축 hard-fail 위험)**: 현 holdings 큐레이션 = 상폐·편입제외(예: XLNX 피인수, 구 반도체 종목) 누락. **CRSP delisting return 보강 의무**(collector_plan).
- ⚠️ **EW-semi universe 정의 미확정**: SOXX/ICE(~30종) vs S&P Semiconductor Select(~46종, XSD 추종). 횡단검정 universe = EW 구성 universe **자기일관**(claude 권고). 12 constituent 부분집합 직접선정 = selection DOF → 사전등록 필요.

## §2. 가설 (반증조건 포함, prereg)

### H1 ★primary (ρ, value-selection)
- **spec**: 반도체 내 저PBR/저EV-EBITDA(z, sector-neutral) → forward excess 양(cheap→+).
- **predicted_sign**: −IC(저밸류 = forward +, 한국 반도체 pbr_z −0.114 대응).
- **반증**: γ_value CI 0 포함 or wrong-sign significant → H1 기각 → (C) freeze 발동.
- **pooling**: DL EB partial pooling(half-Cauchy between-sector SD), N≈12~30 small-N 대응.
- **gate**: MDE_IC≈0.107 사전스크린(value pool −0.117 = 경계, 통과 시 진행).

### H2 secondary (κ, semi cycle timing) — ★R1 보강: falsify 방향 강화
- **spec**: TW/한국 반도체 수출 YoY(lagged) → EW-semi forward excess.
- **predicted_sign**: +(수출↑ = 업황↑ → forward +).
- **반증**: predictive t<2(fixed-b) or eff_N<벽(3MMA 평활 시 ≈1) → κ 폐기.
- ★**R1 실증(theory-notes §2)**: book-to-bill 류 업황지표는 **주가가 선행**(지표 coincident-to-lagging) = predicted
  "lagged→forward" 선행성 자체 의심. SEMI bookings **2016-12 공개중단**(book-to-bill 계산 불가) + billings **2022 월별
  무료단절** = 데이터 가용성 사망 확정(round-1 caveat 해소 = drop). 대체 lead(대만수출/TSMC매출/한국수출 관세청)도
  **leading 아니라 coincident**(자문 다수 수렴). hyperscaler capex guidance 도 주가 coincident(leading 아님).
- ★**R2 의무**: 위는 자문 통설 수렴 = 본인 forward-IC 실측으로 **재확인**(single-source 단정 금지). κ 단독 graduation
  금지(GUIDE §10.7 Freeze default). 단 contemporaneous 신호의 **regime conditioner** 가치는 별도 검토(반도체 PPI
  `PCU33443344` ✅실존, 한국 dram_asp_ppi regime 재배치 패턴 대응).
- ⛔ **환각 id 제거**: TW/한국 수출 반도체-특정 FRED id 무료 부재 확정(`TWNEXPCESEMIT`/`KORXTOTLSEMISME` = **404 날조**).
  fetch 시 관세청/대만 재정부 직접 또는 drop.

### H3 ★decomposition (결정실험, (C) vs (D))
- **spec**: `R_{i,t+1}−R_f = α + Σβ_macro·F_t + γ·Signal^within_{i,t} + ε`.
- γ 유의(within 비-null) → (D) granular 정당 / γ null → **(C) freeze**.
- ★예측 기준(lagged → forward), 노출 β 차등 아님.

### H4 control (exposure, alpha 아님) — ★R1 보강: regime 축 재설계
- 실질금리(DFII10/rate10y) duration — semi growth-duration 노출. overlay 입력(sleeve weight 아님). 한국 aitech rate duration 대응.
- ★**미국 regime 축 (KRW_weak 이식불가)**: primary = (i) **실질금리 DFII10**(long-duration growth 할인율, Lettau-Wachter
  2007 ★R2 재확인) (ii) **HY credit / Baa-Aaa**(risk-on/off, Fama-French 1989). secondary = dollar(약, Bruno-Shin US
  large-cap 도달 약, 기존 us_cyclical β=−0.228 t=−1.02 비유의). 사전 가설 conditioning 축 = 실질금리×credit 2축(M3 32셀).
- ★**AI capex reflexivity 함정**: 2023-26 AI 랠리 표본지배 = episode-dependence → IS(2010-21)/OOS(2022-26) walk-forward 필수.

### H5 신규 신호 후보 (★R1 추가, predicted_sign 사전고정 + 반증조건. ★R2 cite 검증 후 정정)
- value 4종(기 prior) + 신규:
  - **R&D intensity** — ★**R2 정정**: predicted_sign = **양(+)** (R1 초안 "음" 오류). Chan-Lakonishok-Sougiannis (2001)
    JF 56(6) = 시장이 R&D 미래가치 **과소평가**(underreaction) → R&D intensity 高 = forward **양**. ★단 논문 정의 = R&D/
    **market-equity**(value 성격 = 저밸류+R&D高) → R&D/Sales 와 다름. R&D/market-cap = value 와 엉킴(독립성 R3 점검).
    ⚠️ **EDGAR R&D concept 부재 = data-gate** (별도 fetch 또는 측정 보류).
  - **capex intensity**(Capex/Assets, 음, Cooper-Gulen-Schill 하위 ✅) / **margin level+momentum**(양, Novy-Marx+QMJ ✅) /
  - **quality ROIC·low-lev**(양, QMJ 2019 ✅) / **momentum 12-1**(★양 = 한국 reversal 과 반대 가설, Jegadeesh-Titman 1993 ✅) /
  - **low-vol/BAB**(음, Frazzini-Pedersen 2014 ✅).
- **공통 반증조건**: (1) 부호≠predicted+유의(|t_NW|>2) (2) CI 0 포함 (3) **MDE 미달**(아래 ★재계산) (4) OOS 부호반전.
- ★**momentum 부호 검정 = pilot 핵심 falsifier**: predicted 양 사전고정 → 한국처럼 음(reversal) 유의면 predicted 반대 = 기각.

### ⚠️ ★sub-industry 이질성 + MDE 재계산 (측정 1급 오염 caveat, ★R2 정량화)
- 팹리스(NVDA/AMD/QCOM/AVGO, n=4) / 메모리(MU, n=1) / 장비(LRCX/KLAC/AMAT, n=3) / 아날로그·IDM(TXN/ADI/INTC/MCHP, n=4).
- ★Capex/Assets·R&D 신호 = "팹리스 vs non-팹리스 style bias" 대리 위험(alpha 아님).
- ★**R2 MDE 재계산** (지시 1, sub-industry-neutral 자유도 감소 정량화):
  - 단월 cross-section IC SE: full N=12 = 0.302 → sub-industry-neutral(그룹내 demean, G=4 평균 소비) N_eff=8 = **0.378 악화**.
  - ★**memory n=1 (MU) = demean 시 신호=0** (정보 완전소실) → 유효 11종 추가 감소.
  - **시계열 누적 MDE_IC (80% power, α=0.05)**:

    | 기간 | full N=12 | ★sub-industry-neutral N_eff=8 |
    |---|---|---|
    | IS 2015-2021 (~84mo) | 0.092 | **0.116** (>0.107) |
    | full 2015-2026 (~137mo) | 0.072 | **0.091** (<0.107) |
    | OOS 2022-2026 (~53mo) | 0.116 | **0.146** (검정력 매우 약) |

  - ★**판정**: 한국 value pool prior(|IC|≈0.11~0.12)가 미국 재현 시 — full-sample neutral(MDE 0.091)은 **통과 가능**,
    단 **IS-only neutral(0.116)·OOS(0.146)는 MDE 미달** → walk-forward 에서 freeze 위험. = sub-industry-neutral 채택 시
    full-sample 만 검정력 충분 = OOS 검증력 약함을 사전 인지. ★value+quality **결합 신호**로 |IC| 강화 못 하면 (C) freeze 근거.
  - sub-industry-neutral 자체 불가(memory n=1 등) → 그 자체가 freeze 근거(team-lead 지시 1).

## §3. measurement 설계 (M1~M5, GUIDE §4)

- **단위**: rotation = EW-semi 시계열 / selection = 종목 cross-section
- **통제변수(사전지정)**: {SPY excess(market), EW-semi return, rate10y vintage, credit OAS, broad dollar}. PCA 기각(secondary robustness만).
- **M1** Rank-IC 월간 횡단면(IC mean±1.96·SE + N + t_nw)
- **M2** lag-corr(EW-semi forward vs 수출 driver lag 0/1/3/6M, Granger 95% CI)
- **M3** regime cell 32 = Macro4 × HY OAS4 × dollar2 (N≥24 gate, collapse fallback)
- **M4** 5게이트: N≥24 / SE(CI 0 제외) / Power(IC>0.05) / FDR BH q<0.10 / **OOS skfolio CPCV**(IS 2010-2021 / OOS 2022-2026, embargo 5d)
- **M5** factor neutralize = FF5+Mom+QMJ+BAB(Ken French + AQR)
- ★**fixed-b size-valid 의무**: effective_n = n/(1+2Σρ_k) 선행 → fixed-b CV(small-block NW asymptotic 금지)

## §4. Entry gate 사전약정 (GUIDE §10.7, ★forking-paths 방화벽)

1. MDE 사전스크린(|effect| > 0.107 미달 섹터 skip)
2. decomposition-first(within null → 즉시 (C) 수용)
3. Korea-grade(predictive + fixed-b + walk-forward OOS, regime 사전지정)
4. FDR 원장 과금(BY/LORD++ 1 family, 미생존 시 재실행 금지)
5. ★**Freeze default**: H1(value-selection) MDE 미달 → rotation-granular 영구폐기 + 3슬리브 value-selection 집중. H2(κ) 단독 graduation 금지.

## §5. 데이터 plan (collector_plan) — ★R2 fetch 결과 (실측 확인)

★**중복 fetch 회피 확정**: 기존 `us_cyclical/raw-v3/data/edgar_fundamentals.parquet` 에 **SOXX 12종 전부(22,798 rows) +
concept 13종** 보유 = R3 대부분 재사용 가능. prices.parquet 도 12종 전부 보유(단 2015~).

| 항목 | source | ★R2 실측 상태 | unblock |
|---|---|---|---|
| value(PBR) = equity | EDGAR ✅ 재사용 | ✅ equity 12종 (66~270 obs) | 시총=Close×shares (shares 12종 ✅) |
| EV-EBITDA = op_income+dep_amort+lt_debt+st_debt+cash | EDGAR ✅ 재사용 | ✅ 전 계정 존재 (단 dep_amort: ADI/TXN/QCOM=0 → EBIT proxy fallback) | 계정 조합 계산 (추가 fetch 불요) |
| asset growth = assets | EDGAR ✅ | ✅ 12종 (66~150 obs) | YoY 계산 |
| capex intensity = capex/assets | EDGAR ✅ | ✅ 12종 (55~156 obs) | ★메모리/IDM 쏠림 = style bias |
| gross profitability = gross_profit/assets | EDGAR ✅ | △ 11종 (QCOM=0 → revenues−cogs fallback) | fallback 태그 |
| margin = gross_profit/revenues, op_income/revenues | EDGAR ✅ | △ revenues 부족(ADI/KLAC/LRCX/MU <25 obs) | revenues 태그 fallback 또는 부분측정 hedge |
| **R&D intensity** | EDGAR | ⛔ **R&D concept 부재 = data-gate** | 별도 fetch(`ResearchAndDevelopmentExpense`) 또는 측정 보류 |
| ROIC = op_income/(equity+debt) | EDGAR ✅ | ✅ 계정 존재 | 계산 |
| 가격(생존편향) | yfinance | △ 12종 ✅ but ★**2015-01~2026-05 only** = IS 2010-2021 가정 불가(2015~) + **현 holdings = 생존편향(I축)** | CRSP delisting / S&P semi historical membership (R3 전 hard-fail 방지) |
| EW-semi universe | SOXX/ICE or S&P semi select(XSD) | ⏳ §7 사전등록 결정 | 횡단 자기일관 |
| 거시 rate10y(`DFII10`✅) / HY(`BAMLH0A0HYM2`✅ 37mo) / Baa-Aaa(`BAA`✅+`AAA`✅ 장기) / dollar(`DTWEXBGS`✅) | FRED | ✅ macro.parquet (1919~2026, baa_aaa 3468 / hy_oas 805 / dollar 3025 obs) | first-release vintage 확인 |
| 반도체 PPI (regime conditioner) | FRED `PCU33443344` ✅ | 미fetch | timing conditioner (cross-sectional 아님) |
| ~~TW/한국 수출(κ)~~ | ~~FRED~~ | ⛔ id 환각(404) | 관세청/대만 직접 또는 drop |
| ~~book-to-bill~~ | ~~SEMI~~ | ⛔ **drop** (데이터 사망) | — |

## §6. 미해결 의문 (H축) — ★R1 갱신

- 생존편향: 현 12종 = 현 holdings → CRSP delisting / S&P semi historical 필수(미보강 시 I축 hard-fail)
- ★**sub-industry 이질성**(팹리스/메모리/장비/아날로그): Capex·R&D 신호가 style-bias 대리 → sub-industry-neutral z 가능한가 (N=12 자유도 부재)
- EW-semi universe 정의(SOXX vs S&P semi select/XSD) — 횡단 자기일관
- eff_N 벽이 selection-value(N≈12~30)에도 작동하나 — DL EB pooling 완화 + MDE 사전판정. ★검정력은 시계열 IC 평균에서(단월 N=12 IC SE≈0.30)
- mega_tech 중복: NVDA/AVGO 등이 us_mega_tech basket 겹침 — L축 1회계상(double-count 차단)
- ★미검증 인용 R2 cross-verify: Lettau-Wachter(2007), Chan-Lakonishok-Sougiannis(2001), Asness-Porter-Stevens(2000 WP), Cohen-Polk-Vuolteenaho(2003) — 박제 전 확인
- ★AI capex reflexivity = episode-dependence(2023-26 표본지배) → OOS walk-forward 로 검정

## §7. R2 진입 체크리스트 — ★R1 갱신

- [x] ★**EW-semi universe 사전등록 결정 (R2)**: **SOXX/ICE(~30종) 채택** (XSD/S&P semi select 46종 미채택).
  - 근거: (1) 횡단검정 universe = EW 구성 universe **자기일관**(claude 권고) — 현 raw(EDGAR/prices) = SOXX 핵심 12종
    보유 → SOXX/ICE 확장이 데이터 연속성 ○ (2) XSD = equal-weight ETF 라 sanity anchor 만, universe 정의는 SOXX/ICE 멤버십
    (3) ★단 12종 = 현 holdings only → SOXX/ICE 30종으로 확장 시 **PIT historical membership fetch 필수**(생존편향 I축).
  - ★R3 전 unblock: SOXX/ICE historical constituent (편입/편출 시점) + delisted 종목 → EW 직접구성. 미확보 시 12종 부분
    EW + small-N hedge(부분측정 명시). 12 constituent 부분집합 직접선정 = selection DOF → ⛔ 사전등록된 SOXX/ICE 멤버십만.
- [ ] ★**regime 축 재정의 (R2, dollar 약 반영)**: round-1 §4(H4) = 32셀(Macro4×HY4×dollar2) → ★**실질금리×credit 2축
  (4×4=16셀) 우선** + dollar 는 2차 robustness lens (β 비유의 us_cyclical −0.228 t=−1.02 = primary 축 부적합). N≥24
  collapse 사전점검 의무(한국 36셀 full 0개 전례) → 2축 16셀이 셀당 N 확보 유리.
- [ ] CRSP delisting / S&P semi historical membership 가용성 확인(생존편향 I축 hard-fail)
- [ ] EDGAR 반도체 PBR/EV-EBITDA + 신규신호(R&D/Capex/Margin/ROIC/asset-growth) 계정 추출(기존 parquet 재사용 + fallback 태그)
- [ ] MDE 사전스크린 1회(value pool −0.117 → 섹터 분해 시 회복 |effect| > 0.107 추정)
- [ ] 미검증 인용 cross-verify(Lettau-Wachter / Chan-Lakonishok-Sougiannis / Asness-Porter-Stevens / Cohen-Polk-Vuolteenaho)
- [ ] ~~book-to-bill fetch~~ = drop 확정 / κ 대체 = PCU33443344(반도체 PPI) regime conditioner PoC + 관세청·대만수출 직접 fetch 검토
- [ ] regime 축 macro.parquet 컬럼 확인(DFII10/Baa-Aaa/HY/dollar) + 32셀 N≥24 collapse 사전점검
