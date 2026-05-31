---
tags: [type/consult, domain/inv, asset/bond, asset/cash, phase/study-v2-phase3, round/1]
date: 2026-05-31
round: 1
topic: ★MOVE index / ★ACM term premium / sub-cluster 분할 검증
source: WebSearch native (자문채널 경합 default 폴백)
channels: 1자문씩 진행 (9 작업방 동시 점유 방지)
---

# Consult Round 1 — MOVE / ACM term premium / sub-cluster

## 검색어 (2건 병렬)
- `MOVE index ICE BofA bond volatility methodology download FRED 2025`
- `Adrian Crump Moench ACM term premium NY Fed Treasury yield decomposition xlsx`

## 원천 (URL hyperlink)

### MOVE index
- [ICE BofA Indices | FRED (rid=209, 192 시리즈)](https://fred.stlouisfed.org/release?rid=209)
- [MOVE Index [MOVE] | MacroMicro](https://en.macromicro.me/charts/35584/us-treasury-move-index)
- [ICE BofA US Bond Market OVE Index (.MOVE) — CNBC realtime](https://www.cnbc.com/quotes/.MOVE)
- [ICE BofAML MOVE Index (^MOVE) — Yahoo Finance](https://finance.yahoo.com/quote/%5EMOVE/)
- [ICE Data Indices — MOVE Index | ICE Developer Portal](https://developer.ice.com/fixed-income-data-services/catalog/ice-data-indices-move-index)
- [ICE BofAML MOVE Index Today | Investing.com](https://www.investing.com/indices/ice-bofaml-move)
- [V-Lab: ICE BofAML MOVE GARCH Volatility Analysis (NYU Stern)](https://vlab.stern.nyu.edu/volatility/VOL.MOVE:VIND-R.GARCH)

### ACM term premium
- [Treasury Term Premia: 1961-Present (Liberty Street Economics)](https://libertystreeteconomics.newyorkfed.org/2014/05/treasury-term-premia-1961-present/)
- [Treasury Term Premia | FEDERAL RESERVE BANK of NEW YORK (data tabs)](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs)
- [Robustness of long-maturity term premium estimates (Fed FEDS Notes 2017)](https://www.federalreserve.gov/econres/notes/feds-notes/robustness-of-long-maturity-term-premium-estimates-20170403.html)
- [The Treasury Tantrum of 2023 (Fed FEDS Notes 2024-09)](https://www.federalreserve.gov/econres/notes/feds-notes/the-treasury-tantrum-of-2023-20240903.html)
- [The Sterling Capital VAULT: Return of the Term Premium](https://sterlingcapital.com/insights/the-sterling-capital-vault-return-of-the-term-premium/)
- [The Term Premium Conundrum (Neuberger Berman)](https://www.nb.com/-/media/NB/Article-Assets/u0064_0319_wp_the_term_premium_conundrum.ashx)
- [Term premia: models and some stylised facts (BIS QR 2018-09)](https://www.bis.org/publ/qtrpdf/r_qt1809h.pdf)
- [Yield Curve 2026 | Sovereign Term Structure Tracker (Central Bank Watch)](https://centralbank.watch/tools/yield-curve/)
- [US — ACM 10Y Treasury Term Premium Estimates (MacroMicro)](https://en.macromicro.me/charts/45452/us-10-treasury-term-premium)

## 핵심 정제

### 1) ★MOVE Index — 사이징 직결 (사용자 메시지 #3 최우선)

- **정의** (CNBC/ICE): "ICE BofA U.S. Bond Market Option Volatility Estimate Index"
- **본질**: "the leading indicator of fixed-income market volatility and measures U.S. bond market yield volatility by tracking a basket of **over the counter options on U.S. interest rate swaps**"
- 즉 **MOVE = bond 의 VIX 등가**, 단 swaption (interest rate swap option) 기반
- **버전**: MOVE 외 3-month / 6-month basket 버전 있음 (별도 시리즈)

#### 가용 endpoint
| Source | 인증 | 빈도 | historical | 비고 |
|---|---|---|---|---|
| **FRED (rid=209)** | API key (이미 보유) | daily | 가능 (192 series 중 정확한 ticker 확인 필요) | ★최우선 — 기존 fredapi 경로 활용 |
| **Yahoo Finance ^MOVE** | 무료 | daily | 가능 | yfinance 로 즉시 가능 (`^MOVE`) |
| **ICE Developer Portal** | API key (유료/검증) | realtime | 풀 | 본격 인프라화 시 |
| **MacroMicro** | 무료 chart | daily | 차트만 | 시각 검증용 |
| **CNBC .MOVE** | 무료 web | realtime | 제한 | reference |

#### ★ 액션 (Q7 자문 답)
- **MOVE 가용 ✅** — yfinance `^MOVE` 즉시 사용 + FRED rid=209 안에서 정확한 series_id 확인 필요
- 본 작업 즉시 검증 가능: `yf.Ticker("^MOVE").history(start="1988-01-01")` (MOVE inception 1988)
  - **★ 2026-05-31 (btn-powerbi) Phase 4-1 fetch 실측 정정**: yfinance `^MOVE` 실제 가용 시계열 = **2002-11-12 ~ present (5,821 rows)**. MOVE 지수 inception 자체 (1988) 와 yfinance 무료 historical 가용 (2002-11~) 분리. 1988-2002 historical 필요 시 Bloomberg / ICE 별도 (유료 검토). E축 환각 정정 박제.
- → 별 Phase (Phase 5 sub-cluster 검증) 에서 실측 후 yaml block2 indicators 등록

#### MOVE 사용 layer (Q13 자문 답 직접 가능)
- 사용자 명시 "사이징 직결" → **sleeve-level risk gate** + **sub-cluster duration penalty**
- 구체: MOVE Z↑ 시 (1) 전 bond sleeve 가중 down-only attenuate (cash floor↑) (2) long-duration sub-cluster 추가 페널티 (3) HY credit 페널티 (4) cash optionality 가중↑
- → `core/assume/judge.py synthesize_l1` 호출부에서 MOVE Z 반영 down-only multiplier 추가 (R15 사이징 천장 불변식 보존)

### 2) ★ACM Term Premium — 누락 critical (사용자 메시지 #3)

- **정의 (Liberty Street Economics 2014, NY Fed)**:
  > "Treasury yields can be decomposed into two components: **expectations of the future path of short-term Treasury yields** and the **Treasury term premium**"
  > "The term premium estimates are obtained from a **five-factor, no-arbitrage term structure model**"
- **원전 논문**: Adrian, Crump, Moench (2013) — "Pricing the Term Structure with Linear Regressions" (JFE)
- **데이터 source**: Gurkaynak, Sack, Wright (2007) zero-coupon yields from Board of Governors
- **시계열**: 1-10Y maturities, **daily frequency, 1961-06-14~**

#### 가용 endpoint
- **공식 endpoint**: NY Fed `newyorkfed.org/research/data_indicators/term-premia-tabs`
- xlsx/csv download (정확한 URL 은 페이지 상호작용 필요 — 다음 호출에서 WebFetch 로 직접 확인)
- 갱신 빈도: monthly (Liberty Street 인용)
- 무료 ✅

#### ★ 액션 (Q8 자문 답)
- **ACM 가용 ✅** — NY Fed 공식 endpoint, 무료
- 가능한 collector_plan 구현:
  ```python
  # core/brain/fred_adapter.py 와 별개로 NY Fed ACM adapter 신설 권고
  class NyFedAcmAdapter:
      URL = "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls"
      # daily 1961~, 10Y 별 4 series (ACMY01 ~ ACMY10 = yield, ACMTP01 ~ ACMTP10 = term premium)
  ```

#### ACM 분해 layer (Q14 자문 답)
- DGS10 = ACM_expected_short_rate_10Y + ACM_TP_10Y (회계항등 분해)
- **본질적 분기**:
  - expected_short_rate 변화 → Fed expectations 변화 → cash/short-Tsy sub-cluster 가중 trigger
  - term_premium 변화 → 수급/duration risk premium 변화 → long-duration sub-cluster 가중 trigger
- → 블록4 weight_rules 에 ACM 항 분리:
  ```yaml
  - {indicator_id: acm_tp_10y, base_weight: 0.10, modulate_by: [regime],
     direction: "TP↑ → long-duration penalty (수급악화) / TP↓ → long-duration 가중↑",
     granularity: sub_cluster}
  - {indicator_id: acm_expected_rate_10y, base_weight: 0.08, modulate_by: [regime, fed_phase],
     direction: "expected rate↓ → cash carry trade-off (rate-cut optionality 활성)",
     granularity: sub_cluster}
  ```

### 3) 추가 발견 (자문 출력)

#### "Treasury Tantrum 2023" (Fed FEDS Notes 2024-09)
- 2023 hike cycle 에서 term premium 이 *재출현* (이전 ZIRP era 에는 negative 였음)
- → **ACM TP regime-conditional 행동** (rate-up vs rate-down 별 부호 다름) 검증 대상

#### Sterling Capital "Return of the Term Premium"
- post-2022 term premium 부활 = bond 가중 정책 재설계 필요
- → 우리 v1 산출 (Investment Clock 4국면) 외에 *term premium regime* sub-state 추가 가능

#### BIS QR 2018-09 "Term premia: models and some stylised facts"
- ACM 외 대안 모델 (Kim-Wright, Joslin-Singleton-Zhu) — robustness check
- → 학술 cross-verify (E축) 시 ACM 단독 = single source risk → BIS Kim-Wright 보완

#### Central Bank Watch — 9 countries 추적
- US 외 영국·캐나다·호주·일본 등 sovereign term premium → KR sleeve 확장 시 KTB term premium 추정 가능

## 본 분석가 비판 (★자문 그대로 코드화 금지)

### 채택
- ✅ MOVE FRED rid=209 — 즉시 검증 가능 (yfinance `^MOVE` 우선)
- ✅ ACM term premium NY Fed 공식 endpoint — collector_plan P0 등록
- ✅ ACM 분해 → expected_short_rate vs term_premium 분리 → weight_rules block4 분기

### 기각 / 보류
- ⚠️ ACM TP 의 *유일* 출처 = single source risk (E축 위반). BIS Kim-Wright 또는 Joslin-Singleton-Zhu cross-verify 의무 (R2 자문 후속)
- ⚠️ MOVE 의 "사이징 직결" 구체 mechanism — 사용자 명시 외 학술 근거 추가 필요 (R2 자문에서 MOVE-based risk parity / vol targeting 논문 확인)
- ⚠️ NY Fed ACM endpoint URL 정확성 미검증 — 다음 호출에서 WebFetch 로 실제 다운로드 가능성 확인

### 환각 cross-verify
- "5-factor no-arbitrage term structure model" — Adrian-Crump-Moench (2013) JFE 원문 vs 자문 인용 일치 (검증 가능)
- "1961-06-14~ daily" — Gurkaynak-Sack-Wright (2007) zero-coupon yield 시작일과 일치 (검증 가능)
- "MOVE = OTC swaption basket" — ICE 공식 methodology 와 일치 (CBOE VIX 의 SPX option 등가)

## 다음 라운드 (R2) 질문

1. **MOVE-based risk parity / vol targeting** 학술 논문 — 채권 strategy 에서 MOVE 사이징 mechanism 정량화
2. **ACM 대안 모델** (Kim-Wright, Joslin-Singleton-Zhu) cross-verify — single source risk 회피
3. **sub-cluster 분할 7개 vs 4개** trade-off — subagent 토큰 비용 (Q1)
4. **TIPS sub-cluster 별도 vs 통합** (Q3) 학술 baseline
5. **bond sleeve 통합 yaml block3 corr_prior force-include** 우선순위 — 본 R1 의 ACM 분해 결과 반영
6. **BAMLH0A0HYM2 1996-2023 historical 대체 source** — ICE 직접 라이센스 vs S&P U.S. HY Corporate Bond Index 가용성
