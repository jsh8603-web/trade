---
tags: [type/research, domain/inv, phase/study-system, topic/crypto-lens]
date: 2026-05-30
study_id: crypto
asset_scope: [coin]
phase: 2-3 완료
version: v2 (v1 deprecated, raw/study_session.v1.yaml.deprecated)
---

# crypto 스터디 v2 — 요약 + 8축 self-audit

> STUDY-KIT v2 §2 통일 흐름. 2-1 자문 다회 (R1~R3 수렴) → 2-2 이론학습 → 2-3 실데이터 검증 → yaml 코드화.
> ★main 추가 박제 (8축 §2.5 self-audit + 합성/시뮬 금지 + 자문 그대로 코드화 금지 + N=4 standalone 금지).

## 0. 산출 파일 inventory

| 파일 | 역할 | 크기 |
|------|------|------|
| `direction.md` | Phase 2-1 산출 (자문 3R 수렴, 5결정+6가설+8미해결의문) | 20KB |
| `raw/theory-notes.md` | Phase 2-2 산출 (5채널 11문헌 학술 압축 + 거시 transmission + 5 도구) | 28KB |
| `raw/round-{1,2,3}-{gemini,claude}.md` | 자문 6회 원본 | ~52KB |
| `raw/data/{6 sources}.csv/json/html` | ★실측 무료 API 수집 (CoinMetrics 5795 / Binance funding 7363 / FGI 3037 / DefiLlama 3105 / Farside 613 / klines 3209) | ~2.5MB |
| `scripts/{collect_data, lib_common, h1_mvrv, h2_funding, h3_stablecoin, h4_etf, h5_halving, prior_ladder, eff_n_gate, collect_coinmetrics}.py` | ★검증 분석 스크립트 (모두 Bash python 직접 실행) | ~50KB |
| `raw/validation-{h1, h2, h3, h4, h5, prior-ladder, eff-n-gate}.md` | ★실측 검증 결과 (7건) | ~20KB |
| `study_session.yaml` v2 | 7블록 완성 (★실측 기반 prior 재캘리브) | ~25KB |
| `summary.md` (본 파일) | 8축 self-audit + main 보고용 | — |

## 1. ★실측 핵심 발견 — 자문 가설 vs 실데이터 정정

### H1 MVRV mean-revert — ⚠️ 부분 정정 (자문 marginal 가설 → conditional only)
- **자문 (R1~R3)**: MVRV>2.4 → 7d/30d mean-revert 하락, prior 0.4
- **★실측**:
  - n=5795 (14년 daily). MVRV>2.4 일수 = 1154 (19.9%)
  - marginal: MVRV>2.4 진입 후 fwd_30d 평균 = **+22.9%** (양!), fwd_7d=+5.9% — **trend 지속** (cycle 평균 상승 confound)
  - partial corr (FGI×halving_phase conditioning) = **-0.085**, p<0.001, BB95%CI=(-0.235, +0.073) → CI 0 포함 = direct edge 약
  - regime-conditional 20 cell 모두 음 IC (-0.06 ~ -0.65) = **conditioning 후 mean-revert 잔존**
- **정정**: 가설 = "MVRV → marginal mean-revert" → "MVRV → **conditional (FGI×phase) mean-revert only**". prior 0.4 → **0.55** (상향, on-chain rolling IC sharpe 1.27 실측)
- 카드명 변경: `crypto.mvrv_mean_reverts` (v1) → `crypto.mvrv_conditional_mean_revert` (v2)

### H2 Funding cascade — ★REJECT (가설 부호 정반대)
- **자문**: |funding|>0.05%/8h → 7d cascade 하락, prior 0.6
- **★실측**:
  - n=7363 (8h funding, 2019-09~). |funding|>0.0005 일수 4.7%
  - extreme LONG funding (p99, n=24) 진입 후 fwd_3d 평균 = **+1.92%** (양!) t=+1.42 p(<0)=0.92
  - extreme LONG funding (p95+long, n=118) 진입 후 fwd_3d = +0.80% (양)
  - cascade hit rate (fwd_3d<0) at p95+long = **48.3%** binomial p=0.68 (REJECT)
  - Rank-IC funding→fwd_3d = -0.041 BB95%CI=(-0.11, +0.02) = 0 포함
- **정정**: cascade 가설 ★REJECT. 부호 반전 = **funding trend follow**. prior 0.6 → **0.15** (대폭 하향, 신호 자체는 보존하되 부호 반전)
- 카드명 변경: `crypto.funding_cascade` (v1) → `crypto.funding_trend_follow` (v2)

### H3 Stablecoin lead-lag — ✓ 부분 검증 (reflexive 위험)
- **자문**: stablecoin growth → 7-30d 가격 양 (dry powder), prior 0.3
- **★실측**:
  - n=3105 (2017-11~)
  - ADF: log_supply level 정상 (∵DeFi 성장 trend), growth 정상 ✓
  - Granger supply→BTC: lag 7d p=0.0005, lag 14d p=0.0022 ✓ (lead 확인)
  - **★Granger BTC→supply: lag 7d p=0.0138, lag 14d p=0.0000** → **bidirectional (reflexive)**
  - CCF: supply→BTC peak abs lag=19d corr=-0.09 / BTC→supply peak=25d corr=-0.06 → supply→BTC 우세 (역인과 위험 LOW)
  - Rank-IC supply_g7d→fwd_30d = +0.075, CI=(-0.07, +0.19) → 0 포함
  - **★rolling Rank-IC sharpe = -0.43** (음, 부호 반전 시기 다수)
- **정정**: Granger lead 확인 but reflexive 위험 + rolling 시기 부호 반전. prior 0.3 → **0.20**. lead-lag-validity gate 의무
- 카드명: `crypto.stablecoin_lead_with_reflexive_guard`

### H4 ETF flow probation — ✓ 1차 검증
- **자문 (claude r3 정정)**: ETF net flow → digital-gold demand, prior **observe-only 0.05** (probation)
- **★실측**:
  - n=613 (post-2024-01)
  - 5d cum flow > 0 후 fwd_30d > 0 hit rate = **56.7%**, binomial p=**0.006** ✓
  - Rank-IC = +0.057 BB95%CI=(-0.16, +0.23) = 0 포함
- **유지**: prior 0.05 probation 유지 (CI 넓음 = N 부족 명시)
- 카드명: `crypto.etf_flow_probation`

### H5 Halving phase — ✓ standalone 금지 박제 (N=4 power 0)
- 사용자/claude r3 박제: N=4 검정 불가 → standalone IC 산출 금지
- **★실측 (conditioning 효과만)**:
  - phase 별 H1 MVRV→fwd_30d IC 모두 음 (-0.03 post_6_18m markup ~ -0.61 post_18_24m distribution)
  - phase 별 BTC fwd_30d 단순 평균: post_0_6m +6.6% / post_6_18m +8.5% / post_18_24m -7.5% / post_24_36m +1.1%
  - effective N 모두 < 20 (autocorr 강) → small-N tier 강등
- **유지**: regime label only, prior 0.10
- 카드명: `crypto.halving_phase_conditional`

### 우선 1 Prior ladder backtest — ★ladder 역방향
- **자문 D1 ladder**: micro 0.5-0.7 / on-chain 0.3-0.5 / macro 0.2-0.4 / halving 0.1-0.2
- **★실측 rolling Rank-IC sharpe**:
  - micro_funding (H2): sharpe **+0.97** (n_windows=75, mean IC=+0.131)
  - on-chain_mvrv (H1): sharpe **+1.27** (n_windows=47, mean IC=+0.271) — **★가장 강**
  - macro_stablecoin (H3): sharpe **-0.43** (n_windows=45, mean IC=-0.085) — **★음수!**
  - halving: standalone X
- **정정 ladder**: on-chain **0.55** (상향, sharpe 최대) > micro **0.45** (하향, cascade REJECT 반영) > stablecoin **0.20** (대폭 하향, 음 sharpe) > halving 0.10 (유지)
- ★자문 prior ladder 와 실측이 어긋남 → yaml prior 재캘리브 의무 (C축 추적성 강화)

### 우선 2 Effective N gate — ✓ hybrid 권고 유지 가능 (영구폐쇄 위험 LOW)
- **검증 대상**: D4 hybrid 의 internal glasso (FGI 5단계 × vol regime 3 = 15 cell) effective N
- **★실측**:
  - 전체 일수 3209, complete-case 2453 (76.4%, 2019-09-10~ funding 합류 제약)
  - 15/15 cell N≥24 = **100%** admit
  - 11/15 cell effective N≥100 = **73%** admit
  - 5/15 cell effective N≥200 = 33% admit (WARN)
  - 0/15 cell effective N≥500 = 0% (HIGH 위험)
- **결론**: gate threshold = 100 사용 시 73% admit 통과 → **hybrid 권고 유지**. 영구폐쇄 위험 LOW.

---

## 2. ★8축 self-audit (STUDY-KIT §2.5)

> ⛔ supervisor (본인) self-audit 는 참고용. main 의 opus subagent 가 AUDIT-GUIDE 12축 독립 감사 (Provenance + Recomputation) 한다. 본 self-audit 는 그 입력.

### A 이론 학습 실재성
- **상태**: ✓ PASS
- 근거: `raw/theory-notes.md` 28KB, 5채널 11문헌 학술 정리 (Carter & Le Calvez 2018 realized cap, Glassnode SOPR/NUPL, PlanB 2019 S2F 반례, Pagnotta&Buraschi 2018, Liu&Tsyvinski 2021 null, Howell 2020 Capital Wars, Makarov&Schoar 2020, Liu/Tsyvinski/Wu 2022, BitMEX/Alexander funding, Baur 2018, Biais 2023). 자문 raw 6회 + 학술 표준 정의 압축. 거시 transmission 관계도 자체 정리.
- 약점: 원전 PDF 직접 접근 불가 (WebFetch 차단) → 자문 raw + 학술 표준 정의 압축. 일부 미세 수치 abstract 수준.

### B 실데이터 시계열 검증 ★Hard-fail 코어
- **상태**: ✓ PASS (실측 핵심 통과)
- 근거: 7건 `raw/validation-*.md`. 실측 입력: CoinMetrics MVRV 5795 / Binance funding 7363 / FGI 3037 / DefiLlama 3105 / Farside 613 / klines 3209. ⛔합성·시뮬 0건. 각 가설 통계: n, t-stat (Welch), binomial p, Rank-IC + block-bootstrap CI, ADF, Granger, CCF, e-CUSUM.
- 약점: OOS 분리 검증 미수행 (in-sample 전체 fit). post-2017 만 (~9년 daily, MVRV 만 14년).

### C yaml 도출 추적성 ★Hard-fail 코어
- **상태**: ✓ PASS
- 근거: yaml 의 모든 prior_strength·base_weight·partial-corr 값이 raw/validation-*.md 의 실측 통계 인용 (yaml 블록3 theory_basis 에 명시). 분석 .py 재실행 가능 (lib_common.py + 각 가설 .py).
  - 예: 블록3 mvrv_btc edge: "marginal -0.071 / partial -0.085 p<0.001 BB95%CI=(-0.235,+0.073)" → validation-h1-mvrv.md §4 직접 인용
  - 예: 블록4 funding_rate base_weight 0.15: prior_ladder.md §5 의 micro sharpe 0.97 + h2_funding.md REJECT 종합
- 약점: 일부 lens 정성 텍스트는 학술적 압축이라 직접 numeric 매핑 부분만 가능.

### D PIT / lookahead ★Hard-fail 코어
- **상태**: △ PARTIAL
- 근거: 수집 시 PIT 원칙 (knowable_from / 익일 진입 / 결측·정정 유지). 분석 시 forward_return 함수가 t+h 미래 사용 (검증 목적, 정상). raw 수집 ts 모두 UTC ISO 8601.
- 약점: ⚠️ rolling Rank-IC window 의 walk-forward strict 분리 일부 미수행 (rolling 자체는 forward fit 후 IC 산출, OOS 1:1 매칭 미강제). 실 라이브 진입 시점은 lib_common.forward_return 비사용 (검증 단계만). 후속 OOS strict 분리 권고.

### E 자문 비판 + 환각 cross-verify
- **상태**: ✓ PASS
- 근거: 자문 R1-R3 의 가설 5종 중 3종 (H1 marginal, H2 cascade, H3 단방향) 이 ★실측에서 정정·기각. yaml 블록3 theory_basis 에 자문 vs 실측 명시. 자문 인용 원전 문헌 (Carter & Le Calvez 등) 은 학술 표준 정의로 cross-verify.
- 약점: 자문 raw 의 일부 specific 수치 (예: Liu&Tsyvinski 2021 회귀 R² 등) 는 원전 미접근 → cross-verify 가능한 부분만 표시.

### F 반증 가능 + 기각 기록
- **상태**: ✓ PASS (기각 명시 2건 + 부분 정정 1건)
- 근거: ★기각 2건 = H2 funding cascade 가설 REJECT (binomial p=0.68, 0.97), H3 stablecoin 단방향 가설 부분 기각 (bidirectional reflexive 발견). ★정정 1건 = H1 marginal mean-revert → conditional only. 모두 yaml + summary 에 정정 사유 + 실측 통계 명시. F축 hard 경고 (기각 0건 = p-hacking 의심) 회피.

### G effective-N / 검정력 tier
- **상태**: ✓ PASS (tier 강등 적용)
- 근거: 각 가설 effective N 산출. H1 MVRV 14yr but 독립 cycle 3~4쌍 → tier structural prior. H2 funding eff_n 234 (daily aggregate) → tier validated 후보 but REJECT. H3 stablecoin eff_n 225 → tier 후보. H4 ETF eff_n 197 (1.5yr, probation). H5 halving eff_n=4 → tier 차단 (standalone X). 우선 2 gate 분석으로 hybrid 영구폐쇄 위험 LOW 확인.

### H 미해결 의문
- **상태**: ✓ PASS (각 validation 6번 섹션 + summary §3)
- 근거: 모든 validation-*.md 의 "6. 미해결 의문" 섹션 + direction.md §5 8건 + 본 summary §3. 솔직한 인정.

---

## 3. ★미해결 의문 (자문 + 실측 결합, 후속 작업 필요)

1. **MVRV partial-corr CI 0 포함** — direct edge 약. conditioning_set 확장 (BTC dominance·real_rate·stablecoin) 필요
2. **funding cascade 가설 부호 반전 원인** — daily aggregate 정보 손실 가능 (intra-day cascade 미포착). 8h 또는 분 단위 재검증 권고
3. **stablecoin reflexive (BTC→supply 도 lag 7d 유의)** — VECM / 동시 방정식 모델로 분리 권고
4. **ETF flow 1.5yr 짧음** — 후속 누적 후 prior 0.05 → 0.15 promotion 가능
5. **halving N=4 + macro epoch confound** — 채굴자 압력 (hashrate / miner outflow) 연속 보조 지표 collector 추가
6. **prior ladder 재캘리브** — backtest 누적 후 micro/on-chain 사이 정확한 비율 결정
7. **internal glasso effective N>=200 = 33% admit (WARN)** — threshold 100 사용 권고, FGI 5단계 → 3단계 통합 옵션 검토
8. **rolling Rank-IC window 의 walk-forward strict 분리** — 후속 OOS 검증 권고
9. **post-2024 ETF 시대 realized cap (MVRV) 의미 변화** — custodian 이동 → realized cap 의 "최종 보유자 취득" 의미 약화
10. **macro_abstain 가설은 우리 시스템 emit log 부재** — 외부 macro proxy (예: VIX>30 + DXY z>1) 로 시뮬 검증 권고

---

## 4. main 보고용 1줄 요약

> crypto v2 (v1 deprecated). ★실측 7건 validation 으로 자문 가설 정정 — H1 marginal trend (conditional only mean-revert), H2 cascade ★REJECT (trend follow 정정), H3 reflexive guard, H4 probation 1차 검증, H5 conditioning only. prior ladder 역방향 (on-chain sharpe 1.27 > micro 0.97 > stablecoin -0.43). hybrid gate 영구폐쇄 위험 LOW (73% admit @ N>=100). yaml 7블록 + 코드 변경 plan 6 인젝트 + 2 falsify + 1 신규 (coin_track/internal_corr.py). SACRED coin_consensus_lens 불침범.
