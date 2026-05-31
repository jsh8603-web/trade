---
tags: [type/study-research-raw, domain/inv, study/eq_intl, phase/2-1, round/1]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
round: 1
channel: WebSearch (폴백)
fallback_reason: "/gemini-web + /claude-web 9-session 경합 가능성, main v2 가이드 '1~2R 씩' 폴백 허용"
archive_raw: ~/.claude/docs/archive/research-raw/eq-intl-r1-native-20260530.txt
---

# eq_intl R1 — 이론 frame broad scope + 가설 후보 (반증조건)

## Q1: 국가지수 ETF 가격결정 frame (학술)

### 핵심 frame 채택 후보
1. **International CAPM (Dumas 1994 / Dumas-Solnik 1995)** — 글로벌 MSCI 벤치마크 + FX risk premium.
   - 시장 통합 가정. **eq_intl 가 unhedged USD ETF 라 FX risk channel = Adler-Dumas (1995)** 의
     currency exposure 그대로 적용.
2. **Market segmentation (2024 ScienceDirect ML paper)** — 법적 제한·repatriation·FX 규제 등
   direct barriers 가 World CAPM alpha 를 mis-specification 으로 보이게 함. **EM 일부 (china
   capital control) 가 segmented market 효과로 분류 가능** — 이전 H4 raw 발견과 일치.
3. **Country risk premium (Damodaran 류)** — sovereign default risk → cost of equity. EM 의
   country alpha 의 일부 흡수.
4. **ETF liquidity premium (RFS 2024)** — ETF 2차시장 유동성 ↔ fee 동시 결정. eq_intl 에선
   broad ETF (EFA/VEA/EEM/VWO) vs 단일국 ETF (EWZ/EWY 등) 의 liquidity tier 차이 → tracking error.

### Frame gap (R2 후보)
- **BIS dollar liquidity → EM 채널 분해** (real rate vs credit vs flow) 최신 review 필요.
- **carry trade / FX risk premium (Lustig-Verdelhan)** — unhedged ETF return 의 FX 부분 해석.
- **Country selection 실무 frame** (BlackRock / MSCI Country Factor Indexes) — 학술 외 실무 frame.

## Q3: 핵심 가설 초안 (반증조건)

### Pre-existing 가설 (이전 yaml + 5y Yahoo 실측 기반)
| ID | 가설 | 이론 근거 | 반증조건 |
|---|---|---|---|
| H1 | Dollar dominance: broad USD↑ → 모든 국가 ETF↓ (특히 unhedged) | Adler-Dumas FX risk + BIS dollar liquidity | dxy_β 5y rolling 부호 양수 전환 OR R²<0.05 지속 6m+ |
| H2 | Regime amplification: risk-off 시 dollar-EM coupling 강화 | flight-to-quality, Forbes-Warnock | risk-off (VIX>25) 와 risk-on 의 dxy-EM corr 차이 <0.10 |
| H3 | Cross-country momentum (12-1, AQR TSM): winner > loser | Moskowitz/Ooi/Pedersen 2012 + Asness | Rank-IC mean<0 in 5y OR IC-IR<0.10 in 10y rolling |
| H4 | Commodity exporter oil link | terms-of-trade + sectoral composition | brazil/uk/mexico oil corr <= 수입국 corr in 3y rolling |
| H5 | China partial decoupling (post-2018): china 의 dollar/risk β < EM broad avg | Capital controls, CNY peg, BoP 통제 | china 의 dxy_β / vix_β 가 EM broad avg 95% CI 내 |

### Frame 보완 가설 (R1 발견 기반 추가)
| ID | 가설 | 이론 근거 | 반증조건 |
|---|---|---|---|
| H6 | Country segmentation: World CAPM alpha 의 일부 = segmented market 효과 | 2024 ScienceDirect ML | unsegmented(KIIP·MSCI Quality 통과) DM 의 alpha 와 segmented EM alpha 차이 무 |
| H7 | TSM (time-series momentum) — 각 국가 ETF 의 자기 12m return → 다음 1m 양 predictor | AQR Moskowitz 2012 | self-12m 부호 ↔ next-1m 부호 hit ratio < 52% |
| H8 | ETF liquidity tier → tracking error : broad ETF (EFA) 이 단일국 ETF (EWA) 보다 tracking 안정 | RFS 2024 ETF liquidity | broad/단일국 tracking err 차이 < 5bp |
| H9 | Country momentum 의 regime 가변 — risk-on 만 양 IC, risk-off 시 무력화/반전 | momentum crash (Daniel-Moskowitz 2016 prior) | risk-on/off regime split Rank-IC 차이 < 0.05 |

## 다음 라운드 (R2) 질문 후보

수렴까지 보강 필요:
- **R2 Q1**: BIS dollar liquidity 분해 + Lustig-Verdelhan carry — EM/DM 채널 별 driver 분리
- **R2 Q2**: 실데이터 검증 methodology — partial correlation, regime switching, walk-forward Rank-IC 2020s empirical 표준
- **R2 Q3**: country momentum crash + 학술적 momentum crash 정의 (Daniel-Moskowitz 2016 update)
- **R2 Q4**: China decoupling 정량 evidence 2020s — capital flow, A-share H-share spread, CNY peg effectiveness

## 자가 점검 (수렴 판정)

- 이론 frame: International CAPM + segmentation + country risk + ETF liquidity = **부분 합리**.
  단 dollar liquidity 분해 + carry 부분 미흡 → R2.
- 가설 초안: 9개 (반증조건 포함) → broad coverage. 단 검증 방법 (R2) 미정 → R2 종료까지 확정.
- 수렴: **R2 필요**. 잠재 R3 = gap fill (specific data needs).
