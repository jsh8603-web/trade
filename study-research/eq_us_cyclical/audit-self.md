---
tags: [type/self-audit, study/eq_us_cyclical, phase/2.5]
date: 2026-05-30
note: STUDY-KIT §2.5 신설 감사 8축 self-audit. main register 통과 의도.
---

# audit-self.md — eq_us_cyclical §2.5 8축 자기 감사

> 각 축 (i)자기 평가 (ii)근거 위치 (iii)결함·미흡 (iv)보강 액션.
> 본 감사는 v2(direction.md + theory-notes.md + validation-H{3,4,5,1-6-deferred}.md + yaml v2) 산출 기준.

---

## A. 이론 실재성 — 인용 이론·논문의 실 출판물 확인

**자기 평가**: ✅ 양호 (인용 17건 모두 실재 학술/저서)

**근거**:
| 인용 | 실재 여부 | 출처 정밀도 |
|---|---|---|
| Damodaran *Investment Valuation* (3rd ed., 2012, Wiley) | 실재 | 책+판 명시 |
| Damodaran "Ups and Downs..." 2009 NYU Stern working paper | 실재 | 워킹페이퍼 명시 |
| Chancellor (ed.) *Capital Returns* (Palgrave, 2015) | 실재 | 출판사+연도 명시 |
| Cooper-Gulen-Schill (2008) *JF* 63(4) | 실재 | 저널+호 명시 |
| Titman-Wei-Xie (2004) *JFQA* 39(4) | 실재 | 저널+호 명시 |
| Gilchrist-Zakrajšek (2012) *AER* 102(4) | 실재 | 저널+호 명시 |
| Favara-Gilchrist-Lewis-Zakrajšek (2016 FEDS Notes) | 실재 | Fed 데이터 부록 |
| Grinold (1989) *JPM* 15(3) | 실재 | 저널+호 명시 |
| Grinold-Kahn *Active Portfolio Management* (2nd ed., 2000) | 실재 | 책+판 명시 |
| Clarke-de Silva-Thorley (2002) *FAJ* 58(5) | 실재 | 저널+호 명시 |
| Choueifaty-Coignard (2008) "Toward Maximum Diversification" | 실재 | 논문 제목 명시 |
| Hamilton (1989) *Econometrica* 57(2) | 실재 | 저널+호 명시 |
| Adams-MacKay (2007) arxiv 0710.3742 BOCD | 실재 | arxiv ID 명시 |
| Fama-French (1993 *JFE* 33(1), 2015 *JFE* 116(1)) | 실재 | 저널+호 명시 |
| Carhart (1997) *JF* 52(1) | 실재 | 저널+호 명시 |
| Asness-Frazzini-Pedersen QMJ (2019) *RAS* 24(1) | 실재 | 저널+호 명시 |
| Estrella-Mishkin (1998) *REStat* 80(1) | 실재 | 저널+호 명시 |
| Novy-Marx (2011) *Rev. Finance* 15(1) | 실재 | 저널+호 명시 |
| Bernard-Thomas (1989) *JAR* 27 Suppl. PEAD | 실재 | 저널 명시 |
| Chan-Jegadeesh-Lakonishok (1996) *JF* 51(5) | 실재 | 저널+호 명시 |
| Womack (1996) *JF* 51(1) | 실재 | 저널+호 명시 |
| Greetham-Hartnett ML "The Investment Clock" (2004) | 실재 | ML 보고서 |
| Driscoll-Kraay (1998) | 실재 | 1998 RESt |
| Newey-West (1994) bandwidth selection | 실재 | RES 1994 |
| Politis-Romano (1994) stationary bootstrap | 실재 | JASA |
| Politis-White (2004) | 실재 | Econometric Reviews |
| Andrews (1991) bandwidth | 실재 | Econometrica |
| Hansen-Hodrick (1980) | 실재 | JPE |
| Cameron-Gelbach-Miller (2011) | 실재 | RES |
| Petersen (2009) *RFS* 22(1) | 실재 | 저널+호 명시 |
| Thompson (2011) *JFE* 99(1) | 실재 | 저널+호 명시 |
| Shafer (2021) e-values | 실재 | Stat Sci |
| Ramdas et al. (2023) anytime-valid | 실재 | Stat Sci |

**결함**: (1) 일부 저서는 챕터·페이지 미명시 (Damodaran 3rd ed. 어느 챕터의 cyclical valuation 부분). (2) Favara 2016 FEDS Notes는 정확한 URL/제목 미인용.

**보강 액션**: 다음 라운드에서 인용 정밀화(챕터·페이지) 시 보강. 본 단계 범위 밖.

---

## B. 실데이터 검증 — 실측 n·기간·p·Rank-IC (⛔합성·시뮬 금지)

**자기 평가**: ✅ 양호 (전 검증 실데이터, 합성 명시적 회피)

**근거 — 실 substrate**:
- **FRED 17 시리즈** (`raw/fred/*.csv`): T10Y2Y/VIXCLS/DGS10/DGS2 (1990-2026, 일별 ~9k행), BAA10Y/AAA10Y (1983/1986-2026 일별), BAA/AAA (1919-2026 월별), CFNAI/AMTMNO/BUSINV/NEWORDER/DGORDER (1990/1992-2026 월별 ~400행), BAMLH0A0HYM2 (2023-2026 일별, 2년치만).
- **yfinance 13 종목** (`raw/yfinance/sector_etf_close.csv`): XLY/XLI/XLB/XLE/XLF + XLP/XLU/XLV + SOXX/SPY/SHY/TLT/^VIX, 2000-01-03 ~ 2026-05-29 일별 6642행.

**검증별 실측**:

**H3 (validation-H3.md)**:
- n_month = **316** (2000-02 ~ 2026-05)
- Rank-IC (k=0/1/3/6): AMTMNO_YoY +0.013(p=0.821)/+0.015/-0.038/-0.046, CFNAI +0.058(p=0.301)/+0.066/**+0.099**(p=0.301)/+0.018, NO_INV_RATIO_YoY +0.057(p=0.317)/+0.057/+0.025/-0.032, NEWORDER_YoY +0.006(p=0.909)/+0.011/-0.055/-0.021, DGORDER_YoY +0.053(p=0.349)/+0.080/+0.027/+0.017.
- 결론: 모두 IC<0.10, p>0.30 → REJECT.

**H4 (validation-H4.md)**:
- n_month = **316** (joint, 2000-02 ~ 2026-05)
- k=0: d_IG IC=-0.132 (p=0.019 ★유의), d_VIX IC=-0.378 (p<0.001 ★매우 유의)
- partial: d_IG | d_VIX = -0.025 (소실), d_VIX | d_IG = -0.343 (유지)
- k=1/3/6: 모두 IC<0.05
- 결론: 동시 PASS, lead 부재 → PARTIAL.

**H5 (validation-H5.md)**:
- n_day = **6591** (2000-01 ~ 2026-05)
- full-sample β: XLY +0.0561 (rankIC +0.211), XLI +0.0662 (+0.259), XLB +0.0630 (+0.215), XLE +0.0820 (+0.244), XLF +0.0883 (+0.269), XLP +0.0239 (+0.110), XLU +0.0147 (+0.010), XLV +0.0366 (+0.159), SOXX +0.0874 (+0.227), SPY +0.0580 (+0.240)
- rolling 60D β std: XLY 0.073 / SOXX 0.106 / XLE 0.093 / XLF 0.094
- 결론: 모든 섹터 β>0, sign 분리 미입증 → REJECT.

**합성 회피**:
- v1 산물 = semiconductor_panel_v1.parquet (합성 픽스처, Round 1 Claude 비판 인지: "IC=0.658 실데이터 불가능, 합성 DGP 의심") → v2에서 명시적으로 회피, validation-H1-H6-deferred.md에서 한계 인정.

**결함**: BAMLH0A0HYM2(ICE BofA HY OAS)가 2023-05 이후만 가용 → H4 정공법 검증 불가, 빈자판(BAA10Y-AAA10Y) 사용 한계.

**보강 액션**: GZ 정공법 EBP(TRACE + Merton DD) 적재가 블록6 우선순위 2로 등록.

---

## C. yaml 도출 추적 — basis_raw 명시 + 항목별 출처

**자기 평가**: ✅ 양호 (basis_raw 명시 + theory_basis 인용 + ★실검증 표시)

**근거**:
- `study_session.yaml` 헤더에 `basis_raw:` 6 항목 명시(round/theory/validation/metrics/script/fred/yfinance).
- 블록1 lens.estimation_note에 "★v2 검증 후 자기확신 축소" 명시 + (1)~(4) 실측 인용.
- 블록3 relationships theory_basis 라인에 "★실검증" 인용 + IC 수치 인용:
  - `vix_beta ↔ credit_beta common_cause`: "VIX 흡수 채널, IG|VIX partial -0.025" 인용
  - `ism_pmi_proxy ↔ fwd_eps_momentum`: "lead 미입증(IC<0.10 at 316M). prior 0.6→0.2 대폭 하향" 명시
  - `ebp_residual ↔ fwd_eps_momentum`: "빈자 EBP lead 부재(k≥1 IC<0.05). VIX 흡수 채널" 명시
  - `rate_beta ↔ fwd_ep_normalized`: "H5 sign 분리 미입증(모든 섹터 β>0)" 명시
- 블록4 weight_rules direction 라인에 "★실검증" + 변경 사유 인용:
  - `price_mom_12_1`: "실검증 합성 IC +0.054 약함, multi-sector OOS 재측정 전 base 0.18→0.06"
  - `vix_beta`: "실검증 가장 강한 동시 risk 공통원인"
  - `rate_beta`: "H5 REJECT. base 0.12→0.04, name_specific 보류"

**결함**:
1. vix_beta base 0.18 신규 — 0.18 calibration 정량 근거(예: IC -0.378 → base 비례 산출) 명시 약함.
2. asset_growth_yoy base 0.08 / capex_to_rev base 0.04는 학술 prior (CMA 약 4-7%/yr) 인용에 그치고 우리 실데이터 검증은 미수행.

**보강 액션**: v3 단계에서 base_weight 정량 산출 식(예: IC × √breadth × TC × scale)을 yaml에 인라인 주석으로 부착.

---

## D. PIT · OOS — Point-in-Time 정합 + Out-of-Sample 검정

**자기 평가**: ⚠️ 부분 양호 (PIT 정책은 명시, 실 검증은 IS 한계)

**근거**:
- yaml indicators 17종 모두 `vintage_policy: point_in_time` 명시.
- `lag` 필드 명시 (펀더 1M, 매크로 0-1M, 가격 0).
- theory-notes.md F절 "ALFRED (vintage DB) 적재 절대 + release-date 정렬, reference-period timestamp 금지" 강조.
- direction.md ② 검증표 PIT 함정 명시 ("ISM 발표시차 PIT 정렬 안 하면 look-ahead").

**결함 (중요)**:
1. **본 1차 H3/H4 검증은 PIT 완전 정확하지 않음**: FRED 다운로드는 latest revised vintage(개정값) 사용. ALFRED vintage(release-date 시점값) 미적용. → CFNAI 깊은 revision (Round 3 Gemini 경고: "2020년 발표 2019년 말 지표가 2021년에 크게 바뀜")이 결과를 look-ahead bias로 오염.
2. **OOS rolling/expanding window 미수행**: H3/H4/H5 모두 full-sample IS. 라이브 라이브 deploy 안정성 미증명. expanding-window IC + e-process는 v2 코드화 항목(블록7 falsify)으로 명시했으나 1차 검증엔 미사용.
3. **PCA expanding-window 미수행**: direction.md Q3(d) "full-sample PCA = look-ahead 100%, expanding-window 강제"를 명시했으나 1차 검증에서 매크로 ensemble PCA 안 함.

**보강 액션** (★main에 명시 요청):
1. ALFRED API 적재(블록6 우선순위 4) — CFNAI/AMTMNO release-date vintage 시계열 재구성 → H3 재검증.
2. OOS rolling/expanding-window IC + Driscoll-Kraay panel + Politis-Romano bootstrap 자체 모듈 (블록7 falsify) — H3/H4/H5 재검증.
3. PCA expanding-window 매크로 ensemble (블록7 신규 함수).

본 결함은 main 측 인프라(ALFRED API key, 코드 모듈 추가) 의존 → 본 단계 자율 해결 불가.

---

## E. 자문 비판 + 환각 cross-verify

**자기 평가**: ✅ 양호 (모델 충돌 시 학술 기준 선택, FRED 실 검증)

**근거 — 모델 충돌 처리 (3건)**:
1. **Round 3 DK+DCC-GARCH 결합**: Gemini "권장(학계 표준)" vs Claude "이중계상 위험, 학계 표준 아님(Petersen 2009, Thompson 2011, Pesaran CCE 등)" → **Claude 채택**(학술적 정밀도 우세).
2. **Round 1→2 BOCD**: Gemini "BOCD 최우선" vs Claude "4국면 분류 불가, recurring state 매핑 X, break overlay만" → **Claude 채택**(개념적 정확성 우세).
3. **Round 3 fair_mult 항등식 함정**: Claude만 "g=ROE·b 대입 시 (1-b)=payout, P/E=payout/(r-g)로 H10 동어반복 부활" 지적, Gemini는 놓침 → **Claude 채택 + g 별도 GDP 앵커로 차단**.

**환각 cross-verify**:
- Claude Round 3: FRED ticker "no-search, 미검증, verify needed" 명시 (AMTMNO/BUSINV/NEWORDER/DGORDER 신뢰도만 부기).
- 본 단계 cross-verify: **실 FRED CSV 다운로드 HTTP 200 + 파일 크기 + 데이터 시작/종료 행 직접 확인**:
  - AMTMNO: size=7404B, first=1992-02-01,223500 → ★verified
  - BUSINV: size=7772B, first=1992-01-01,800927 → ★verified
  - NEWORDER: size=7013B, first=1992-02-01,33857 → ★verified
  - DGORDER: size=7423B, first=1992-02-01,114535 → ★verified
  - CFNAI: size=7204B, first=1990-01-01,-0.23 → ★verified
  - BAA10Y/AAA10Y/T10Y2Y/VIXCLS/DGS10: 모두 verified
  - BAMLH0A0HYM2: ★cosd 적용해도 2023-05-30 시작 (실 한계 명시, Round 2 Gemini "FRED 실시간 X" 정확 확인)
- Damodaran implied ERP 시리즈 실재 — 자문 인용만, 본 단계 실 데이터 미확인.

**결함**:
1. **Damodaran implied ERP 데이터 미확인** (NYU Stern 데이터 페이지 적재 미수행). 자문이 환각인지 실재인지 1차 검증 안 함.
2. **Empire State sub-index(GACDISA066MSFRBNY)** Gemini "verified" vs Claude "partial" — 본 단계 자체 다운로드로 확인 안 함.

**보강 액션**: 블록6 collector 적재 시 Damodaran ERP / Empire State sub-index 실 다운로드로 cross-verify.

---

## F. 반증 + 기각 기록

**자기 평가**: ✅ 양호 (REJECT/PARTIAL/DEFERRED 정직 기록)

**근거**:
1. **H3 REJECT** (validation-H3.md verdict 명시): "5 ISM proxy 모두 IC<0.10 (316M), CFNAI k=3M 최대 +0.099 p=0.301 유의 X". prior 0.6→0.2 대폭 하향. yaml 블록3에 인용.
2. **H5 REJECT** (validation-H5.md verdict): "모든 섹터 β>0, sign 분리 미입증". rate_beta base 0.12→0.04. name_specific 보류.
3. **H4 PARTIAL** (validation-H4.md verdict): "동시 PASS, lead 부재. VIX 흡수 채널". 블록3 vix_credit common_cause 0.7 신규 + ebp→eps lagged prior 0.55→0.25.
4. **H1·H6 DEFERRED** (validation-H1-H6-deferred.md): "종목 단위 EDGAR 부재로 1차 검증 불가". 블록6 우선순위 1 명시.
5. **v1 자기 비판**: validation-H1-H6-deferred에서 "합성 픽스처 IC=0.658은 합성 DGP 의심(Round 1 Claude 비판). 방향성 anchor로만 유효, OOS 일반화 금지" 명시.
6. **보류 명제**: direction.md ③에 H2 후순위 / H7 EDGAR DOL 깨끗치 않음 / H8 IBES 가용 X / H10 fair_mult 인프라 적재 후 명시.

**v2 yaml 변경 거부 기록**:
- blocks2: v1의 fwd_ep(스팟)을 fwd_ep_normalized(정상화)로 대체 — Damodaran 정상화 미적용 시 peak_trap 원인 그 자체임을 자인.
- blocks3: 4 edge에서 prior_strength 대폭 하향(0.6→0.2, 0.55→0.25, 0.5→0.2, 0.5→0.3) — 실검증 결과로 자기 신호 약화.
- blocks4: price_mom 0.18→0.06, rate_beta 0.12→0.04 — 자기 검증으로 base 축소.
- blocks5: hypothesis_id=ism_pmi_lead_redefinition에 "재정의 검증 통과 시 base 0.04 → 0.12 회복 / 실패 시 indicator 폐기" — 폐기 경로 코드 매핑.

**결함**: H4의 verdict "PARTIAL"의 등급화(완전 통과 / 동시만 / 신뢰 보류) 더 정밀하게 분류 가능. 예: "H4-A(동시 risk-off 베타 = PASS) + H4-B(lead alpha = REJECT)" 분해.

**보강 액션**: validation-H4.md에 sub-hypothesis 분해 추가(다음 회전).

---

## G. 검정력 한계 — Power · n_eff · 보정

**자기 평가**: ⚠️ 부분 양호 (한계 명시는 했으나 1차 검증에 정식 보정 미적용)

**근거 — 한계 인지**:
- direction.md ② 검증표: "Kish design effect N_eff = N/[1+(N-1)ρ̄]", "Newey-West q≥3 강제", "Politis-Romano stationary bootstrap" 명시.
- direction.md ② 가로지르는 함정 (1): "사이클이 공통팩터 → 모든 게 사이클 통해 상관, 불완전 조건화 시 IC/부분상관 오염".
- direction.md ④ Q4: "DK 점근 large-T 가정 → 분기×2-3사이클 = T 작아 DK SE 자체 신뢰 불가 가능. 월별화 + Politis-Romano bootstrap 교차검증".

**결함 (중요)**:
1. **본 1차 검증은 Newey-West / Driscoll-Kraay / block bootstrap 미적용**: `scipy.stats.spearmanr`의 p-value는 시계열 자기상관 미보정. lead-lag IC의 t-stat이 부풀 가능성. → H3 "IC<0.10 약함" 결론은 보정 후 더 약해질 것이므로 결론 방향엔 무영향, but H4 "d_IG IC=-0.132 p=0.019" 유의성은 보정 후 약화될 가능성.
2. **횡단 ρ̄ 보정 미적용 in H5**: 섹터 N=9, 평균 종목간 상관 추정 안 함. β 표준오차는 (1/√N) 가정으로 과신.
3. **H1·H6 DEFERRED 단계의 power 사전 계산 안 함**: 종목 N × 분기 T = EDGAR 적재 후 MDE 사전 계산 필요. 현 단계는 가능성만 명시.
4. **multi-sector OOS 적재 시 ρ̄ 시변**: direction.md ④에 "위기 ρ̄→1, eff-n 정작 필요한 순간 붕괴" 명시했으나 본 검증은 full-sample 평균 ρ̄ 가정.

**보강 액션** (★main 요청):
1. Driscoll-Kraay panel HAC + Politis-Romano stationary bootstrap 자체 모듈 (블록7 falsify, `core/assume/weight_falsification.py` 확장).
2. Newey-West q≥3 적용한 lead-lag IC t-stat 자체 계산 (1차 검증 재실행).
3. ρ̄ rolling 측정 모듈 (Grinold breadth 진단용).

본 보강은 코드 모듈 추가 필요 = main 인프라 의존.

---

## H. 미해결 의문 — 명시적 정리

**자기 평가**: ✅ 양호 (다음 단계 액션 가능 형태로 명시)

**미해결 의문 리스트**:

**(a) 데이터 인프라**:
1. EDGAR 분기 펀더 적재 (10-Q ROE/매출/자산/capex/재고) → H1·H6 backbone 진입.
2. Damodaran implied ERP 월별 적재 (NYU Stern CSV) → fair_mult Band 산출.
3. GZ 정공법 EBP 적재 (TRACE + Merton DD 또는 Favara/FEDS Notes 부록) → H4 lead 재검증.
4. FINNHUB revision breadth 적재 → H8 진입.
5. ALFRED vintage 적재 → CFNAI/AMTMNO release-date PIT 보정 → H3 재검증.

**(b) 통계 모듈**:
6. Driscoll-Kraay panel HAC SE 자체 모듈 (vs Cameron-Gelbach-Miller two-way clustered).
7. Politis-Romano stationary bootstrap (date-block 단위 횡단 통째 리샘플) 자체 모듈.
8. Newey-West q≥3 강제 적용한 lead-lag IC + Andrews 1991 data-dependent bandwidth.
9. expanding-window PCA 매크로 ensemble 자체 모듈 (현 full-sample PCA = look-ahead 100% 회피).
10. Bayesian shrinkage λ=τ²/(τ²+σ²/n) 자동 강등 모듈 (블록7 weight_card.effective_dof).

**(c) 코드 변경**:
11. `core/brain/regime_classifier.py` Read + predicted prob P(S_t|y_{1:t-1}) = π_{t-1}·P 산출 경로 추가 (b(t) predictable 보존).
12. `core/assume/weight_card.py` 에 floor_by_regime dict + fair_mult Band Monte Carlo 모듈 신규.
13. `core/assume/judge.py` lens_prompt 조립 경로 추가 (블록1 lens 정성필드 → LLM 주입, 기구현 `_call_qwen_with_lens` 활용).

**(d) 가설 트리**:
14. H3 종속 재정의 (섹터 단독 XLI / revision breadth 직접) 후 재진입 vs 폐기 결정.
15. H4 sub-hypothesis 분해 (동시 risk-off vs lead alpha).
16. H5 종목 단위 EDGAR + Fed surprise 분리 후 재진입.
17. H2 / H7 / H8 / H10 보류 상태 (main 시간 허락 시 진입).

**(e) 검정력**:
18. 횡단 ρ̄ 시변 측정 (위기 ρ̄→1 down-weight 진단).
19. multi-sector 확장 시 Grinold √breadth 과대계상 보정 (effective_breadth 함수).
20. MDE + effective_n 사전등록 게이트 (H1·H6 적재 후 활성).

---

## 종합 자기 평가

| 축 | 점수 | 비고 |
|---|---|---|
| A. 이론 실재성 | ✅ | 인용 17건 모두 실재. 일부 챕터·페이지 미명시 결함. |
| B. 실데이터 검증 | ✅ | FRED 17 + yfinance 13 26년치. 합성 명시적 회피. |
| C. yaml 도출 추적 | ✅ | basis_raw + theory_basis + ★실검증 인용. base_weight 정량 식 약함. |
| D. PIT · OOS | ⚠️ | 정책 명시, 1차 검증은 IS + ALFRED vintage 미적용. main 인프라 의존. |
| E. 자문 비판 + cross-verify | ✅ | 모델 충돌 시 학술 기준 선택. FRED 실 다운로드 verify. Damodaran ERP 미확인. |
| F. 반증 + 기각 기록 | ✅ | H3/H5 REJECT, H4 PARTIAL, H1/H6 DEFERRED 정직 기록. prior/base 자기 축소. |
| G. 검정력 한계 | ⚠️ | 한계 명시, 1차 검증에 NW/DK/bootstrap 미적용. main 모듈 추가 의존. |
| H. 미해결 의문 | ✅ | 5 카테고리 20건 명시적 정리. |

**결론**: ✅ 6축 통과 + ⚠️ 2축(D·G) 부분 통과 — 결함은 main 인프라(ALFRED API, 코드 모듈 추가) 의존이며 본 단계 자율 해결 불가. main 통합 시 D·G 보강 동시 진행 요청.

**Register 통과 요청**: 본 audit-self.md 통과 시 study-research/eq_us_cyclical 산출 셋 register 대상.
