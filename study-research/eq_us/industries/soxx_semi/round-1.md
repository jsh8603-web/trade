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

### H5 신규 신호 후보 (★R1 추가, predicted_sign 사전고정 + 반증조건)
- value 4종(기 prior) + 신규: **R&D intensity**(R&D/Sales, 음, Chan-Lakonishok-Sougiannis 2001 ★R2 확인) /
  **capex intensity**(Capex/Assets, 음, Cooper-Gulen-Schill 하위) / **margin level+momentum**(양, Novy-Marx+QMJ) /
  **quality ROIC·low-lev**(양, QMJ 2019) / **momentum 12-1**(★양 = 한국 reversal 과 반대 가설, Jegadeesh-Titman 1993) /
  **low-vol/BAB**(음, Frazzini-Pedersen 2014).
- **공통 반증조건**: (1) 부호≠predicted+유의(|t_NW|>2) (2) CI 0 포함 (3) MDE |IC|<0.107 dead-on-arrival (4) OOS 부호반전.
- ★**momentum 부호 검정 = pilot 핵심 falsifier**: predicted 양 사전고정 → 한국처럼 음(reversal) 유의면 predicted 반대 = 기각.

### ⚠️ ★sub-industry 이질성 (측정 1급 오염 caveat, R1 신규)
- 팹리스(NVDA/AMD/QCOM/AVGO) / 메모리(MU) / 장비(LRCX/KLAC/AMAT) / 아날로그·IDM(TXN/ADI/INTC/MCHP) = 비즈니스모델 상이.
- ★Capex/Assets·R&D/Sales 신호 = "팹리스 vs non-팹리스 style bias" 대리 위험(alpha 아님). N≈12 자유도 부재 = sub-industry
  dummy 통제 사실상 불가 → 측정 시 style-bias 인지 + sub-industry-neutral z 시도 + 부분측정 small-N hedge 의무.

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

## §5. 데이터 plan (collector_plan) — ★R1 정정 (FRED id 실존검증 반영)

| 항목 | source | 상태 | unblock |
|---|---|---|---|
| 종목 펀더멘털(PBR/EV-EBITDA) | EDGAR 10-K/Q PIT | ✅ edgar_fundamentals.parquet (101k rows, filed PIT) | EV-EBITDA = 부채/현금 계정 추가 fetch |
| 신규 신호(R&D/Capex/Margin/ROIC/asset-growth) | EDGAR concept | △ Assets 전 universe ✅ / GP·Revenue 부분 | sub-universe 한정 fallback 태그 (us_cyclical 노트 §1) |
| 가격(생존편향) | yfinance | △ 현 holdings | **CRSP delisting / S&P semi historical membership 보강** |
| EW-semi universe | SOXX/ICE or S&P semi select(XSD) | ⏳ 미확정 | 사전등록 (횡단 자기일관) |
| 거시 rate10y(`DFII10`✅) / HY(`BAMLH0A0HYM2`✅ 37mo) / Baa-Aaa(`BAA`✅+`AAA`✅ 장기) / dollar(`DTWEXBGS`✅) | FRED vintage | ✅ macro.parquet (rate10y/hy_oas/baa_aaa/dollar/vix) | first-release vintage |
| ~~TW/한국 반도체 수출(κ)~~ | ~~FRED~~ | ⛔ FRED id 환각(404) | 관세청/대만 재정부 **직접** fetch 또는 drop. coincident = κ 약 |
| 반도체 PPI (regime conditioner) | FRED `PCU33443344` ✅ | 미fetch | timing conditioner 후보 (cross-sectional 신호 아님) |
| ~~book-to-bill~~ | ~~SEMI~~ | ⛔ **drop** | bookings 2016 종료 + billings 2022 무료단절 = 사망 확정 |

## §6. 미해결 의문 (H축) — ★R1 갱신

- 생존편향: 현 12종 = 현 holdings → CRSP delisting / S&P semi historical 필수(미보강 시 I축 hard-fail)
- ★**sub-industry 이질성**(팹리스/메모리/장비/아날로그): Capex·R&D 신호가 style-bias 대리 → sub-industry-neutral z 가능한가 (N=12 자유도 부재)
- EW-semi universe 정의(SOXX vs S&P semi select/XSD) — 횡단 자기일관
- eff_N 벽이 selection-value(N≈12~30)에도 작동하나 — DL EB pooling 완화 + MDE 사전판정. ★검정력은 시계열 IC 평균에서(단월 N=12 IC SE≈0.30)
- mega_tech 중복: NVDA/AVGO 등이 us_mega_tech basket 겹침 — L축 1회계상(double-count 차단)
- ★미검증 인용 R2 cross-verify: Lettau-Wachter(2007), Chan-Lakonishok-Sougiannis(2001), Asness-Porter-Stevens(2000 WP), Cohen-Polk-Vuolteenaho(2003) — 박제 전 확인
- ★AI capex reflexivity = episode-dependence(2023-26 표본지배) → OOS walk-forward 로 검정

## §7. R2 진입 체크리스트 — ★R1 갱신

- [ ] EW-semi universe 사전등록(SOXX/ICE vs S&P semi select/XSD 결정) — 횡단 자기일관
- [ ] CRSP delisting / S&P semi historical membership 가용성 확인(생존편향 I축 hard-fail)
- [ ] EDGAR 반도체 PBR/EV-EBITDA + 신규신호(R&D/Capex/Margin/ROIC/asset-growth) 계정 추출(기존 parquet 재사용 + fallback 태그)
- [ ] MDE 사전스크린 1회(value pool −0.117 → 섹터 분해 시 회복 |effect| > 0.107 추정)
- [ ] 미검증 인용 cross-verify(Lettau-Wachter / Chan-Lakonishok-Sougiannis / Asness-Porter-Stevens / Cohen-Polk-Vuolteenaho)
- [ ] ~~book-to-bill fetch~~ = drop 확정 / κ 대체 = PCU33443344(반도체 PPI) regime conditioner PoC + 관세청·대만수출 직접 fetch 검토
- [ ] regime 축 macro.parquet 컬럼 확인(DFII10/Baa-Aaa/HY/dollar) + 32셀 N≥24 collapse 사전점검
