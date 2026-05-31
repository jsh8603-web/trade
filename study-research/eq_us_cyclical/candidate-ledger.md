---
tags: [type/candidate-ledger, study/eq_us_cyclical, purpose/easy-review]
date: 2026-05-31
purpose: 그동안 자문·이론·M3·workflow 에서 나온 지표·이론·가설 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
note: |
  direction.md (자문 9R) / theory-notes.md (이론 6+5) / validation-H{3,4,5,1-6-deferred}.md (실측) /
  yaml v2 7블록 / audit-self.md (8축) / m3-findings.md (epoch driver) / plan-industry-regime-delta.md 
  (산업×regime δ) — 6 파일에 흩어진 후보를 1파일로 집약.
basis_raw:
  - raw/round-{1,2,3}-{question,gemini,claude}.md (자문 9R)
  - raw/theory-notes.md (이론 11+1)
  - raw/validation-H{3,4,5,1-6-deferred}.md + validation-metrics.json (실측)
  - study_session.yaml v2 (basis_raw 명시)
  - audit-self.md (8축 self-audit)
  - raw/m3-findings.md (epoch × sector driver)
  - plan-industry-regime-delta.md (현 차수 산업×regime δ)
---

# eq_us_cyclical 지표·이론·가설 후보 원장 (candidate ledger)

## ✅ 채택 — yaml v2 indicators 등록 (17종, 9 in_system + 8 collector 대기)

| 지표 id | family | in_system | base | tier | 근거 |
|---|---|---|---|---|---|
| **price_mom_12_1** | momentum | ✅ | 0.06 | core | v1 합성 IC +0.054 약함, multi-sector OOS 재측정 전 0.18→0.06 |
| **rate_beta** | macro_sens | ✅ | 0.04 | core | H5 REJECT (모든 섹터 β>0), name_specific 보류, 0.12→0.04 |
| **dollar_beta** | macro_sens | ✅ | 0.08 | core | M3 β_dxy −0.58~−1.62 dominant 채널 (cyclical 전 sector) |
| **oil_beta** | macro_sens | ✅ | 0.04 | core | XLE rank-IC +0.602 압도, 별도 채널 |
| **credit_beta** | macro_sens | ✅ | 0.08 | core | H4 VIX 흡수 (partial −0.025), 0.10→0.08 |
| **realized_vol** | risk | ✅ | 0.08 | core | Slowdown 방어 가중 |
| **vix_beta** | macro_sens | ✅ | 0.18 | v2 신규 | H4 동시 IC=−0.378 가장 강한 risk 공통원인 ★ |
| **yield_curve_10y_2y** | macro_driver | ✅ | — | v2 신규 | Estrella-Mishkin 1998 침체 선행 12-18M |
| **ism_pmi_proxy** | macro_driver | ✅ | 0.04 | core | H3 REJECT (lead IC<0.10), 종속 재정의 후 재진입 hook |
| **fwd_ep_normalized** | valuation | ⏳ collector | 0.30 | ★core | H1 backbone, Damodaran 정상화 (EDGAR 적재 후) |
| **roe_margin_trend** | quality | ⏳ collector | 0.10 | core | Damodaran 정상화 인풋 + QMJ 교호항 |
| **earnings_revision_breadth** | revision | ⏳ collector | — | core | FINNHUB 또는 EDGAR 8-K 파싱 |
| **fwd_eps_momentum** | revision | ⏳ collector | — | core | EDGAR fwd EPS 변화율 |
| **ebp_residual** | macro_driver | ⏳ collector | — | v2 신규 | GZ TRACE+Merton DD 정공법 (현 BAA10Y-AAA10Y 빈자판) |
| **asset_growth_yoy** | quality | ⏳ collector | 0.08 | v2 신규 | Cooper-Gulen-Schill 2008 CMA 음부호 |
| **capex_to_rev** | quality | ⏳ collector | 0.04 | v2 신규 | Chancellor Capital Cycle 보조 |
| **operating_leverage_nm** | quality | ⏳ collector | 0.04 | v2 신규 | Novy-Marx 2011 정밀 (gross_margin proxy 약함) |

## ✅ 채택 — yaml v2 relationships (9 edge)

| edge | sign·strength | 통과 여부 | 근거 |
|---|---|---|---|
| vix_beta ↔ credit_beta common_cause | pos·**0.7** | ★PASS | H4 실측 partial IG\|VIX=−0.025 (VIX 흡수) |
| vix_beta → realized_vol direct | pos·0.6 | PASS | risk-off 동시 채널 |
| asset_growth_yoy → fwd_eps_momentum (neg) | neg·0.6 | 학술 prior | CMA 정본 (multi-sector OOS 대기) |
| capex_to_rev → fwd_eps_momentum (neg) | neg·0.55 | 학술 prior | Capital Cycle (AG 조건화 잔차) |
| credit_beta → realized_vol direct (vix 조건) | pos·0.35 | 약화 | partial 약함 (VIX conditioning 필수) |
| op_leverage → fwd_eps_momentum | pos·**0.3** | 약화 | gross_margin proxy IC +0.084, 정밀 proxy 대기 |
| ism_pmi_proxy → fwd_eps_momentum | pos·**0.2** | 대폭 하향 (0.6→0.2) | H3 REJECT, lead 부재 |
| ebp_residual → fwd_eps_momentum (neg) | neg·**0.25** | 대폭 하향 (0.55→0.25) | 빈자 EBP lead 부재 |
| rate_beta → fwd_ep_normalized | unsigned·**0.2** | 대폭 하향 (0.5→0.2) | H5 REJECT sign 분리 미입증 |

## ✅ 채택 — confidence_hooks (블록5, 5 hypothesis)

| hypothesis_id | 상태 | mechanism |
|---|---|---|
| vix_credit_common_risk_factor | H4 부분 통과 | regime contemp IC e-process |
| ism_pmi_lead_redefinition | H3 재진입 hook | 종속 재정의 (sector 단독·revision breadth) |
| normalized_ep_trough_backbone | H1 DEFERRED 활성 | EDGAR 적재 후 trigger |
| peak_trap_no_entry | H6 DEFERRED, mechanism 정의 | weight_card.floor_by_regime |
| capital_cycle_overcapex | 신규 | CMA spread Rank-IC e-process |

---

## ⏳ 이연 — Collector 미적재 (블록6 우선순위 1-4, 데이터 인프라 의존)

| 후보 | priority | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| **EDGAR 분기 펀더 (10-Q ROE/매출/자산/capex/재고)** | **1** | edgar_provider.py 코드만, 실 적재 없음 | edgar_provider.py 확장 + sec.gov EDGAR API (무료) |
| **Damodaran implied ERP 월별 시계열** | **1** | NYU Stern 데이터 페이지 (월간 CSV) 미적재 | NYU Stern 월간 CSV scraper |
| **GZ EBP 정공법** (TRACE+Merton DD) | 2 | TRACE 유료, Favara/FEDS Notes 부록 미적재 | TRACE_API_KEY 또는 Favara 부록 |
| **FINNHUB revision breadth** | 3 | 무료티어 API key 미발급 | FINNHUB_API_KEY (무료) |
| **GICS 정확 섹터 분류 + ETF holdings** | 4 | FinanceDatabase(MIT) 적재 미수행 | FinanceDatabase scraper + XLY/XLI/XLB/XLE/XLF holdings |
| **ALFRED vintage DB** (CFNAI/AMTMNO release-date) | 4 | FRED ALFRED API key 미발급 → look-ahead bias 잔존 | FRED_API_KEY (무료) + ALFRED endpoint |
| **IBES 컨센서스 추정치** (H8 revision breadth) | — | 유료 (Refinitiv) — FINNHUB 무료티어로 대체 시도 | FINNHUB 가용 시 적재 |
| **rig count BKR** (XLE δ_arch 경계) | TBD | M3 § 권고, 미적재 (FRED 가용) | FRED `BKRRIGUSTOTAL` 또는 BKR 페이지 |
| **book-to-bill (SEMI 협회 월별)** | TBD | semi δ_arch — 무료 가용, 미적재 | SEMI 협회 월별 CSV scraper |
| **CIT long position / CFTC DCOT** | — | 본 study 범위 외 (commodity 관련) | — |

## ⏳ 이연 — 코드 미적용 (블록7 stage 명시, 자문/이론 합의됐으나 실 코드 미투입)

| 후보 | 위치 (블록7 stage·file·symbol) | 사유 | unblock 조건 |
|---|---|---|---|
| **Damodaran 정상화 E/P + fair_mult Band** | card · `core/assume/weight_card.py` · fair_mult Band Monte Carlo | EDGAR 적재 후 활성 (지금 = 코드 모듈 미작성) | EDGAR + (1-g/ROE)/(r-g) 산출 모듈 신규 |
| **(r-g) ≥ 2% guardrail** | card · weight_card.py | fair_mult 분모 폭주 차단 미적용 | weight_card.py 분모 floor 추가 |
| **g = min(ROE·(1-b), 명목 GDP 3.5-4%) cap** | card · weight_card.py | Damodaran stable-growth cap 미적용 | 위 동일 |
| **bottom-up beta (산업 무차입 → D/E relever)** | card · 신규 모듈 | Damodaran > 회귀 베타, 산업분류 + D/E 데이터 필요 | EDGAR D/E + 산업 분류 (블록6 P4) |
| **Damodaran implied ERP (월별)** | card · ERP source | NYU Stern 적재 미수행 | 블록6 P1 |
| **GZ EBP 잔차 자체산출** | learn · 신규 모듈 | HY OAS ⊥ {기대디폴트, VIX} → DD 정제 부재 | BAMLH0A0HYM2 ≥ 2010 풀시계열 + Merton DD |
| **Driscoll-Kraay panel HAC SE** | falsify · `weight_falsification.py` | 자체 모듈 미작성 (현 spearmanr 단순) | DK SE 자체 모듈 작성 |
| **Politis-Romano stationary bootstrap** | falsify · weight_falsification.py | date-block 단위 횡단 통째 리샘플 미적용 | Politis-Romano + Politis-White 2004 자동 블록 |
| **Newey-West q≥3 (4Q overlap)** | falsify · 신규 함수 | overlapping window SE 미보정 (lead-lag IC t-stat 부풀 위험) | Andrews 1991 data-dependent bandwidth |
| **Bayesian shrinkage λ=τ²/(τ²+σ²/n)** | card · weight_card.effective_dof | 4슬롯 delta_regime 자동 강등 모듈 미작성 | effective_dof 필드 + shrinkage 계산 |
| **expanding-window PCA 매크로 ensemble** | learn · 신규 함수 | full-sample PCA = look-ahead 100% 회피 명시했으나 expanding window 코드 X | expanding window iterator |
| **Kish design eff-n / effective_breadth** | falsify · 진단 함수 | N_eff = N/[1+(N-1)ρ̄] (Choueifaty-Coignard 2008) 미계산 | ρ̄ rolling 측정 + breadth 계산 |
| **predicted prob P(S_t\|y_{1:t-1}) = π_{t-1}·P** | inject · `core/brain/regime_classifier.py` | b(t) predictable 보존 위해 filtered → predicted 변경 필요 | regime_classifier.py 정밀화 |
| **룰베이스 BMA + filtered HMM + BOCD overlay 계층** | inject · regime_classifier.py | 단일 평활 X, 계층 prob 모듈 미작성 | 위 동일 |
| **weight_card.floor_by_regime dict** (peak_trap 차단) | card · weight_card.py | H6 peak entry 차단 mechanism 정의만, 코드 X | dict 확장 + judge buy gate 연결 |
| **judge lens_prompt 조립 경로** | inject · `core/assume/judge.py` · `_call_qwen_with_lens` | 시그니처 검사 기구현, lens 정성필드 → 문자열 조립 X | lens_prompt 빌더 함수 신규 |
| **QMJ quality 교호항** | learn · weight_panel.py | early-recovery 정크 랠리 정밀 매핑 미적용 | F-F 5-factor + QMJ 추가 |
| **종속 재정의 (섹터 단독·revision breadth)** | falsify · validation 재실행 | H3 재진입 hook mechanism 정의만, 재검증 X | sector-split 종속 + IBES/FINNHUB 적재 |
| **DK + Politis-Romano 교차검증** | falsify · weight_falsification.py | DK SE × bootstrap 갈리면 T 부족 신호 | 두 모듈 모두 작성 후 cross-check |

## ⏳ 이연 — 가설 보류 (direction.md ③ 6건)

| H | 명제 | 우선순위 사유 | unblock 조건 |
|---|---|---|---|
| **H2** | val ↔ mom 위상교차 | regime/배수 노이즈 의존, 후순위 | regime 분류기 정밀화 후 |
| **H7** | DOL EPS 증폭 | EDGAR 고정/변동비 분해 깨끗치 않음 (데이터 난도) | EDGAR 적재 + Novy-Marx 정밀 proxy |
| **H8** | revision breadth 전환점 | IBES 가용 X (EDGAR+FRED+ETF 즉시 적재 X) | FINNHUB 무료티어 적재 |
| **H10** | val_gap → Δmultiple re-rating | fair_mult 비순환 정의 필요 (동어반복 차단 후) | 정상화 ROE + bottom-up beta + GDP cap g + Monte Carlo Band 적재 |
| **H9** | CMA 섹터무관 (Asset Growth Anomaly) | 보너스 검증 — multi-sector OOS 필요 | EDGAR + 헬스케어/유틸리티 패널 |

## ⏳ 이연 — 본 차수 진행 중 (Workflow wf_9ce20415-0d2)

| 차원 | 산출 예정 | 상태 |
|---|---|---|
| δ_regime[E1~E4] × 4 산업 (semi/materials/industrials/energy) | shrunk 매트릭스 + λ | Workflow 진행 (research → 3-tier verify → synthesis) |
| δ_arch 후보 (산업별 펀더멘털) | book-to-bill/capex_to_rev/backlog_to_rev/oil_curve 등 식별 | 위 동일 |
| 5게이트 (G1~G5) 자체 정의 | SSOT 부재 → plan §3 자체 정의, main 검토 받음 | 위 동일 |
| 검증관 3-tier (Tier1 측정 / Tier2 James-Stein / Tier3 도메인) | epoch별 λ + recommend | 위 동일 |
| yaml R15 weight_card 보강안 5-8건 | block3 NEW edge + block4 base 조정 + block1 lens XLE 분리 | 위 동일 |
| XLE 분리 vs cyclical 통합 최종 결정 | M3 outlier + Tier3 권고 | 위 동일 |

## ⏳ 이연 — M3 보강 후보 (m3-findings §4, yaml v3 권고만 박제, 코드 미투입)

| 후보 | 권고 | 사유 |
|---|---|---|
| `dollar→cyclical_eps` prior 0.3→**0.4** 상향 | block3 | E1·E2 R²=0.21/0.29 가장 강함 |
| **NEW** `oil→XLE_eps` prior **0.7** | block3 | rank-IC +0.602 압도적 검증 |
| **NEW** `dollar→{soxx/xlb/xly}_eps` prior 0.5 | block3 | β_dxy −1.12~−1.62 sector-specific |
| **NEW** `dxy_beta_sector_1y` indicator | block2 | per-sector dollar loading, 252d rolling |
| **NEW** `oil_beta_xle_1y` indicator (별도) | block2 | XLE oil-driven 분리 트랙 |
| **NEW** epoch regime tag 매크로 (E1/E2/E3/E4) | block3 | belief b(t) 입력, Belief-Truth 격리 준수 |

---

## ❌ 미채택 / proxy 대체 (자문 충돌·환각·proxy 가용성)

| 후보 | 사유 |
|---|---|
| **IC=+0.658 (v1 합성 픽스처)** | 합성 DGP 또는 look-ahead 강신호 (Round 1 Claude 비판). 실 26년 검증에서 모두 <0.10 → REJECT (라이브 shrink 각오) |
| **fair_mult = (1-g/ROE)/(r-g)에 g=ROE·b 대입** | P/E=payout/(r-g) 항등식 함정 (Round 3 Claude 만 지적, Gemini 놓침). g 별도 GDP 앵커로 차단 |
| **DK + DCC-GARCH 결합** | Gemini "권장(학계 표준)" vs Claude "이중계상 위험" → **Claude 채택**. Petersen 2009 / Thompson 2011 / Pesaran CCE 학술 정밀도 우세 |
| **BOCD 4국면 분류** | Gemini "BOCD 최우선" vs Claude "recurring state 매핑 X, break overlay 만" → **Claude 채택**. BOCD = break only, Hamilton predicted prob 가 recurring 분류 |
| **smoothed Markov-switching prob** | look-ahead 누설 → predicted prob P(S_t\|y_{1:t-1}) = π_{t-1}·P 만 사용 |
| **full-sample PCA** | look-ahead 100% → expanding-window 강제 |
| **reference-period timestamp** | look-ahead 위험 → release-date 기준 PIT 강제 |
| **CFNAI × HMM 입력** | 이중 평활 (CFNAI = 이미 필터링된 지표) → 원천(M3) 직접 HMM, CFNAI 쓸 땐 HMM 우회 |
| **Greetham-Hartnett Investment Clock = ground truth** | 단일 휴리스틱, 가설 생성기로만 — 4국면 분류 검증 모델 X |
| **30% NOI threshold (Hamilton 원안)** | commodity 범위 — 본 study 무관 |
| **gross_margin proxy** | IC +0.084 약함 → Novy-Marx 2011 (fixed_costs/book_assets) 정밀 proxy 로 대체 (collector 대기) |
| **회귀 베타** | Damodaran bottom-up beta (산업 무차입 → D/E relever) > 회귀 베타 |
| **historical ERP 5%** | Damodaran implied ERP (월별 vintage) > historical |
| **smoothed HMM full-sample 라벨** | 라이브 거래 불가 (미래정보) — predicted (1 lag) 만 |
| **Bai-Perron / CUSUM 사후 탐지 break** | 라이브 거래 불가 — "탐지" ≠ "예측" |
| **Sector rotation (Fidelity/Stovall 1996), Ned Davis Research** | 후순위, 실무 휴리스틱 (검증 대상이지 전제 X) |
| **Howard Marks · Ray Dalio** | 영감용, 검증 X |
| **StockToFlow 류** | commodity 범위 — 본 study 무관 |
| **scipy.stats.spearmanr 단순 p-value** | 시계열 자기상관 미보정 — NW q≥3 강제 (G축 결함, 코드 모듈 작성 대기) |
| **단일 섹터 (반도체) trough 샘플** | 2020=V자/정책왜곡, peak_trap 극소수 → multi-sector 25년 시계열 확장 의무 |
| **HMM smoothed prob → judge buy_gate** | b(t) predictable 보존 위반 — predicted (1 lag) 만 |

## 🚫 환각 회피 / 함정 박제 (정직 명시)

| 위험 | 회피 방식 |
|---|---|
| FRED ticker 환각 | 실 CSV 다운로드 HTTP 200 + 파일 크기 + 데이터 시작/종료 행 직접 확인 (AMTMNO/BUSINV/NEWORDER/DGORDER/CFNAI/BAA10Y/AAA10Y/T10Y2Y/VIXCLS/DGS10 모두 verified) |
| BAMLH0A0HYM2 가용 X | cosd 적용해도 2023-05-30 시작 — Round 2 Gemini "FRED 실시간 X" 정확. 빈자판 BAA10Y-AAA10Y (1986+) 대체 + GZ TRACE 적재 대기 |
| Damodaran implied ERP 환각 위험 | NYU Stern 데이터 페이지 실 다운로드 미수행 — 자문 인용만, 1차 verify X (블록6 P1 적재 시 cross-verify) |
| Empire State sub-index 충돌 | Gemini "verified" vs Claude "partial" — 본 단계 자체 다운로드 안 함 (NY Fed CSV 직접 필요) |
| v1 IC=+0.658 자기 확신 | validation-H1-H6-deferred.md "합성 DGP 의심, 방향성 anchor만 유효, OOS 일반화 금지" 정직 박제 |
| ALFRED vintage 미적용 | CFNAI 깊은 revision (Round 3 Gemini 경고: 2019년 말 지표가 2021년에 크게 바뀜) look-ahead bias 잔존 — D축 결함 명시 |

---

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 지표/가설 | 현 상태 | 재검증 trigger |
|---|---|---|
| **vix_beta 동시 IC −0.378** | 채택 (base 0.18) | regime contemp IC e-CUSUM 단측 붕괴 시 base 하향. baseline −0.20 이상 회복 시 partial 복권 |
| **ism_pmi_proxy** (H3 REJECT 이후) | base 0.04 cap | 종속 재정의 (sector 단독 XLI / revision breadth) 후 IC ≥ 0.15 → 0.04→0.12 회복 / 실패 → 폐기 |
| **fwd_ep_normalized** (H1 DEFERRED) | base 0.30 (collector 대기) | EDGAR 적재 후 trough Rank-IC ≥ +0.10 (FM+DK SE) → 활성 / 실패 → 스팟 fallback |
| **peak_trap_no_entry** (H6 DEFERRED) | mechanism 정의 | peak Win-Rate < 30% → floor 상향 / ≥50% → 완화 |
| **capital_cycle_overcapex** | 신규 hook | 반도체 밖 multi-sector long-short CMA spread IC e-process |
| **rate_beta** (H5 REJECT) | base 0.04 + name_specific 보류 | 종목 EDGAR + Fed surprise 분리 후 sign 분산 재측정 |
| **EBP 빈자판** | base 약함, prior 0.25 | GZ TRACE+Merton DD 정공법 적재 후 lead 재검증 |
| **operating_leverage gross_margin proxy** | IC +0.084 약함, prior 0.3 | Novy-Marx 정밀 proxy (fixed_costs/book_assets) 적재 후 |
| **asset_growth_yoy / capex_to_rev** | base 0.08 / 0.04, 학술 prior | EDGAR 적재 후 multi-sector OOS decile spread |

---

## 🔁 audit-self.md 미해결 의문 20건 (5 카테고리 cross-ref)

**(a) 데이터 인프라 (5)**: EDGAR / Damodaran ERP / GZ EBP / FINNHUB / ALFRED → 블록6 P1-P4

**(b) 통계 모듈 (5)**: DK SE / Politis-Romano / NW q≥3 / expanding PCA / Bayesian shrinkage → 블록7 falsify·card

**(c) 코드 변경 (3)**: regime_classifier.py predicted prob / weight_card.floor_by_regime + fair_mult Band / judge.lens_prompt → 블록7 inject

**(d) 가설 트리 (4)**: H3 종속 재정의 / H4 sub-분해 / H5 종목 단위 / H2/H7/H8/H10 보류 → confidence_hooks·재검증

**(e) 검정력 (3)**: 횡단 ρ̄ 시변 / effective_breadth 보정 / MDE+effective_n 사전등록 → falsify·진단

★ 모두 main 인프라 의존 (자율 해결 불가). main 통합 시 동시 진행 요청.

---

## 📊 출처 cross-ref

| 후보 출처 | 파일 | 정보 |
|---|---|---|
| 자문 9R | raw/round-{1,2,3}-{question,gemini,claude}.md | Gemini Pro + Claude Opus 4.8 병렬, 라운드별 누적 |
| 이론 정리 | raw/theory-notes.md | 6 최상위 + 5 보완 + 1 비판적 자각 |
| 실측 검증 | raw/validation-H{3,4,5,1-6-deferred}.md + validation-metrics.json | H3/H5 REJECT, H4 PARTIAL, H1/H6 DEFERRED |
| v2 yaml | study_session.yaml | 7블록 + basis_raw 명시 |
| self-audit | audit-self.md | 8축 (6 PASS + 2 PARTIAL D·G) |
| M3 결과 | raw/m3-findings.md + m3-metrics.json | 4 epoch × 9 sector + L축 caveat |
| 산업×regime δ | plan-industry-regime-delta.md (현 차수) | 4 산업 subagent + 5게이트 + 3-tier (workflow 진행 중) |

---

## TL;DR — 다음 세션 한 줄 인계

- **채택 17 indicators (9 in_system + 8 collector 대기)** + 9 relationships + 5 confidence_hooks 박제
- **이연 코드 미적용 19건** = Damodaran/fair_mult Band/DK SE/NW/Politis-Romano/Bayesian shrinkage/regime predicted prob/lens_prompt 등 — main 인프라 의존
- **가설 보류 6 (H2/H7/H8/H10 + H9 보너스)** — EDGAR/FINNHUB/multi-sector 적재 후
- **미채택 21 (자문 충돌·환각·항등식 함정·proxy)** — 정직 박제, 재발 차단
- **본 차수 진행 중**: Workflow `wf_9ce20415-0d2` (4 산업 × regime δ + James-Stein + yaml R15 보강안)
