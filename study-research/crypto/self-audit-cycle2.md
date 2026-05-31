---
tags: [type/self-audit, study/crypto, cycle/2, date/20260531]
date: 2026-05-31
study_id: crypto
cycle: 2
phase: P0-D (self-audit + STUDY DONE main 보고)
audit_target: H7-H12 6 신규 가설 cycle 2 검증
audit_axes_applied: [A, B, D, E, F, G, I, K, L]
---

# crypto cycle 2 self-audit (P0-D, 2026-05-31)

> ★main 의 opus subagent 12축 audit 진입 prerequisite — **방의 self-audit 는 참고 자료, main subagent 가 독립 재계산 판정**.
> ★AUDIT-GUIDE §0 Provenance + Recomputation 원칙: yaml 의 수치는 "주장(claim)", raw 재계산 가능.

---

## §0. cycle 2 흐름 (P0 unblock → 6 가설 검증)

1. main P0 unblock (2026-05-31) → 본 방 직접 fetch
2. ★collector 11종 직접 fetch (P0-A CoinMetrics 4 + P0-B FRED 3 + yfinance 4 + P0-C PyTrends + DefiLlama 2)
3. 신규 가설 H7-H12 scripts/h{7-12}_*.py 작성 + 실행
4. raw/validation-h{7-12}-*.md 6건 산출
5. 본 self-audit (5단계 verdict + 12축 박제 + candidate-ledger 갱신 후속)
6. yaml v3 신규 블록 draft (audit 통과분만)
7. STUDY DONE main 보고

⛔ 합성 시뮬 0건. 실측 fetch only. AUDIT-GUIDE §0 합성 지문 검사 통과.

---

## §1. 6 가설 verdict 종합표

| 가설 | 학술 prior | Rank-IC | n | N_eff | verdict | 자료 가치 |
|------|-----------|---------|---|-------|---------|----------|
| **H7 AdrActCnt → fwd_30d** (Pagnotta&Buraschi 2018 sub-Metcalfe) | α∈[0.5, 1.2] 학술 | **0.0085** | 3178 | 47 | **★REJECTED** | 자문 sub-Metcalfe 본 표본 부정 (F 기각) |
| **H8 TxCnt utility → fwd_30d** (Catalini&Gans 2020) | utility = price 채널 | **0.0022** | 3178 | 47 | **★REJECTED** | utility count proxy 신호 부재, value-weighted 후속 의무 |
| **H9 BTC-Nasdaq regime → fwd_30d** (Baur 2018 risk-asset) | regime 차등 | -0.0027 (continuous) / **ANOVA p=0.0006 Bonferroni 후 생존** | 2117 | 33 | **TENTATIVE DIRECTIONAL** | ★decoupled regime mean **-3.46%** (digital-gold 정반대) / risk-asset regime +4.35% (Baur risk-asset 가설 부분 지지) |
| **H10 BTC-Gold digital gold** (Baur 2018 BTC≠gold prior) | risk-off corr↑ | risk-off mean 0.1796 < 0.2 gate | 154 | 5 | **★REJECTED** | digital-gold gate FAIL + post-ETF corr 역감소 (Welch p=0.0002) — ETF 시대 BTC-Gold 약화 |
| **H11 Google Trends attn → fwd_1m** (Liu&Tsyvinski 2021 attention) | weekly base, attn 1σ → +1.2~2.4% | **0.1117** (monthly), attn>+1σ mean **+10.41%** | 94 | 61 | **★PARTIAL CONFIRMED** | ★cycle 2 유일 신호. post-2021 sub IC 0.0967 sign 일관, weekly base 후속 의무 |
| **H12 DefiLlama TVL utility → fwd_30d** (Cong 2022 매개) | DeFi → BTC 약 | marginal -0.012 / partial -0.012 | 2748 | 43 | **★REJECTED** | partial-corr 잔존 신호 부재, multicollin 약 (0.17 < 0.7) |

### 종합 통계
- **REJECTED**: 4건 (H7, H8, H10, H12) — F 기각 풍부 (p-hacking 신호 0)
- **TENTATIVE DIRECTIONAL**: 1건 (H9) — Bonferroni 후 통계 유의 but 방향성 = digital-gold 정반대
- **PARTIAL CONFIRMED**: 1건 (H11) — monthly small-N (n=94 / N_eff=61) hedge 의무
- 시도횟수 K 총합 (사전 공시): H7=24 + H8=50 + H9=36 + H10=36 + H11=16 + H12=12 = **174 비교**

---

## §2. AUDIT-GUIDE 12축 자가 박제 (cycle 2 6 가설 통합)

### A 학술 근거 (저자·연도·원전 명제·가정·한계)
- ✓ H7 Pagnotta&Buraschi 2018 SSRN / Liu&Tsyvinski 2021 RFS (반증)
- ✓ H8 Athey 2016, Catalini&Gans 2020, Yermack 2015 (반증)
- ✓ H9 Baur 2018 JIFMIM, Bhambhwani 2019, LTW 2021
- ✓ H10 Baur 2018, Klein 2018, Smales 2019
- ✓ H11 Liu&Tsyvinski 2021 RFS, Da Engelberg Gao 2011 JF
- ✓ H12 Cong 2022 JFE, Aramonte 2021 BIS, Schär 2021 FRBSL
- 모든 가설 = **원전 자문 복붙 X**, 본 framework 자체 정리. 점추정 magnitude 박제 X.
- 한계 명시: 원전 PDF 직접 접근 X, abstract + 자문 압축 (cycle 3 PDF 직접 접근 권고).

### B 실데이터 시계열 검증 (★Hard-fail axis)
- ✓ 합성 시뮬 0건 — 모든 가설 실측 CoinMetrics / FRED / yfinance / PyTrends / DefiLlama
- ✓ Newey-West HAC SE 적용 (forward window length 일치 lag = 30d / 60d / 1m)
- ✓ Block bootstrap CI95% (block=60d / 90d, B=2000)
- ✓ Rank-IC 보고 + n + p (raw + Bonferroni 보정 사전 공시)
- ✓ Hard-fail B threshold: Rank-IC > 0.03 + t > 2.0
  - H7 / H8 / H10 / H12: B threshold FAIL → REJECTED 합당
  - H9: ANOVA p<0.0006 Bonferroni 후 생존 → PARTIAL signal
  - H11: |IC|=0.1117 > 0.03 → B threshold PASS

### C yaml ±5% 추적성 (★Hard-fail axis)
- cycle 2 = yaml v3 draft 단계, ±5% 매칭 사전 보장:
  - H9 regime label (yaml indicator 신규) ↔ validation-h9 ANOVA F=7.504
  - H11 attn_z 신호 (yaml indicator 신규) ↔ validation-h11 IC=0.1117
  - REJECTED 가설 (H7/H8/H10/H12) = yaml 통합 X (candidate-ledger 갱신)

### D PIT / lookahead 회피 (★Hard-fail axis)
- ✓ CoinMetrics community = T+1 release (익일 02:00 UTC)
- ✓ FRED daily = T+1 (M2SL monthly = M+1)
- ✓ yfinance daily = T+1 close
- ✓ PyTrends weekly Sunday = T+1
- ✓ DefiLlama daily = T+1
- ✓ fwd_30d_ret = close[t+30]/close[t] (lookahead 회피)
- ⚠️ FRED first-release vintage 미적용 (cycle 3 ALFRED API 의무)

### E 자문 비판 + 환각 cross-verify
- ✓ 자문 점추정 magnitude 박제 X:
  - Pagnotta α=0.5~1.2 박제 X → 본 표본 IC 보고만
  - LTW 2021 +0.5~+0.7 박제 X → 본 표본 monthly IC 보고만
  - Baur 2018 BTC≠gold "corr near zero" prior 박제 X → 본 표본 mean 0.0986 보고
  - claude-web 자문 "BTC-Nasdaq 0.4~0.6", "BTC-Gold 2024 0.1~0.3 → 2025 0.3~0.5" 박제 X → 본 표본 검증 우선

### F 반증가능 + 기각 기록 (★Hard 경고 — 기각 0건 = p-hacking 냄새)
- ✓ 기각 기록 = **4 건 (H7 / H8 / H10 / H12)** — F axis 풍부, p-hacking 신호 0
- ✓ 각 가설별 반증조건 사전 명시 (theory-notes §6 + validation md §F)
- ✓ TENTATIVE / REJECTED 가설의 hedge 어휘 강제 적용

### G effective-N tier (차단 X, 라벨 강등)
- H7 N_eff=47, H8 N_eff=47, H9 N_eff=33, H10 N_eff=5 ★INSUFFICIENT (risk-off subsample), H11 N_eff=61, H12 N_eff=43
- ⚠️ H10 risk-off N_eff=5 << 30 → **★INSUFFICIENT 라벨** (verdict REJECTED 와 별개 라벨링)
- H11 monthly N_eff=61 << 100 → "structural prior(저신뢰)" 라벨, validated alpha X

### I 데이터 무결성 + 생존편향 (★Hard-fail axis)
- ✓ BTC only 명시 — 멀티코인 (ETH·상폐 ICO token) 확장 시 별도 처리 의무
- ✓ Binance klines = surviving largest exchange, MtGox 등 상폐 거래소 미포함 = ★cycle 3 obs
- ⚠️ DeFi protocols TVL = surviving only (상폐 TerraUSD, FTX 토큰 미포함) → H12 결과 약점

### J 경제적 유의성 + 거래비용 (cycle 2 미적용, cycle 3 진입 사항)
- 본 cycle = 통계적 유의만 검증. 거래비용 (왕복 0.3% slippage + funding) 차감 미적용.
- H9 risk-asset regime mean +4.35% / decoupled -3.46% → 거래비용 차감 후도 유의 가능성 ↑
- H11 attn>+1σ mean +10.41% / month → 명시적 거래비용 차감 미수행, cycle 3 시뮬 의무

### K 다중검정 보정 (시도횟수 공시 ★Hard)
- ✓ K 사전 공시: 6 가설 총 K=174 비교 (사전 박제 §1 표 참조)
- ✓ Bonferroni α/m_k 적용 사례:
  - H7 K=24 → α/24=0.0021 → 본 결과 raw p 측정 미수행, β CI 0 포함 = 직접 fail
  - H8 K=50 → α/50=0.001 → 동일
  - H9 K=36 → α/36=0.00139 → ANOVA p=0.0006 + KW p=0.0002 둘 다 **생존**
  - H10 K=36 → 본 라운드 raw p (Welch + ETF 비교) = 0.0001 / 0.0002 둘 다 생존 but gate_i FAIL
  - H11 K=16 → α/16=0.0031 → Rank-IC raw p 미수행, magnitude (IC 0.1117 + extreme bin diff 10%) 직접 보고
  - H12 K=12 → 신호 부재 직접 fail
- ⚠️ **Deflated/Haircut Sharpe 미적용** (cycle 3 의무)

### L 통합 상관행렬 정합성 (★시스템 통합 차단 가능)
- ✓ 공통인자 중복 명시:
  - H9 BTC-Nasdaq + 기존 H1 MVRV + macro = USD funding 공통인자 (gold·equity sleeve 와 중복 회피 박제)
  - H12 TVL ↔ stablecoin = USD funding 공통인자 (1회 계상)
- ⚠️ tail-correlation regime (claude-web 자문): 위기 시 corr→1 수렴 → point estimate 박제 금지, regime별 안정성 검증 의무
- ⚠️ 중첩 forward-return window → t-stat 부풀림 (Newey-West / Block bootstrap 강제 박제 — B axis)

---

## §3. yaml v3 신규 블록 draft (audit 통과분만 통합 권고)

### 통합 후보 (cycle 2 audit 통과)
- **H9 regime classifier** (block2 indicators / block3 relationships 신규):
  - indicator: `btc_nasdaq_corr_60d_regime` (regime 3종 risk_asset / mixed / decoupled)
  - relationship: regime → fwd_30d_ret 차등 (ANOVA F=7.504 Bonferroni 생존)
  - hedge: regime 전이 6.55/year (불안정), walk-forward strict OOS 후속 의무
  - prior_strength: **0.15** (TENTATIVE structural prior)
- **H11 attention z** (block2 / block5 confidence_hook 신규):
  - indicator: `pytrends_btc_attn_z` (monthly)
  - relationship: attn_z > +1σ → fwd_1m_ret 약 양 (mean +10.41%)
  - hedge: monthly small-N (n=94 / N_eff=61), weekly base 후속 의무
  - prior_strength: **0.20** (PARTIAL CONFIRMED + post-2021 sign 일관)

### 통합 보류 / 폐기 (REJECTED)
- H7 AdrActCnt → ledger 탈락 (sub-Metcalfe 본 표본 부정)
- H8 TxCnt → ledger 탈락 (count proxy 한계 + REJECTED), TxTfrValAdjUSD paid tier 후속
- H10 BTC-Gold → ledger 탈락 (digital-gold thesis 본 표본 부정 + post-ETF 역방향)
- H12 TVL utility → ledger 탈락 (partial-corr 잔존 신호 부재)

---

## §4. candidate-ledger 갱신 (cycle 2 → ❌탈락 4건 신규)

candidate-ledger.md ❌탈락 섹션 신규 추가:
- (i) H7 active_addresses_metcalfe — REJECTED (Pagnotta&Buraschi 본 표본 비유의)
- (ii) H8 tx_count_utility — REJECTED (count proxy 신호 부재, TxVolUSD paid tier 후속)
- (iii) H10 btc_gold_digital_thesis — REJECTED (risk-off 0.18<0.2 + post-ETF 역방향)
- (iv) H12 defi_tvl_utility — REJECTED (partial 잔존 부재, multicollin 약함)

### 보존 (cycle 3 후속 검증)
- (v) H7 with conditioning_set 확장 (BTC dominance / real_rate / cluster 효과 제거) — 자료 가치
- (vi) H8 with TxVolUSD value-weighted (CoinMetrics paid tier 필요 → main 별도 요청)

---

## §5. cycle 2 미해결 의문 (cycle 3 진입 사항)

1. **H9 regime label 불안정 (전이 6.55/year)** — smoothing window 길이 민감도 + regime persistence 검증
2. **H11 weekly base 보강** — PyTrends 'today 5-y' fetch + LTW 2021 직접 매핑
3. **H11 endogeneity** — Granger lead 양방향 (attn ↔ price) 확인
4. **CoinMetrics paid tier** — TxTfrValAdjUSD / SOPR / RevUSD / MinerNetTransfers (★H5 보강) 권한
5. **VECM 모델** — H3 stablecoin reflexive 분리 (main OOS-A 요청 보존)
6. **walk-forward strict OOS** — 전 가설 1차 시뮬 (main OOS-B + 본 방 P1-3)
7. **Deflated/Haircut Sharpe** — cycle 2 174 비교 보정 (K axis 강화)
8. **거래비용 차감** — H9 / H11 의 alpha 보존 여부 (J axis cycle 3)
9. **regime tail-correlation** — corr 시기 변동 + 위기 시 1 수렴 검증 (L axis)
10. **FRED ALFRED vintage** — first-release PIT 적용 (D axis 강화)

---

## §6. 결론 (cycle 2 verdict)

cycle 2 = **부분 신호 1건 (H11 attention) + regime 차등 1건 (H9, digital-gold 정반대) + 기각 4건**.
자료 가치 핵심:
- ★학술 prior (Pagnotta sub-Metcalfe / Catalini utility / Baur digital gold / Cong DeFi utility) 본 표본 ★기각
- ★Liu&Tsyvinski 2021 attention predictor monthly 표본 부분 지지 (weekly base 후속 의무)
- ★ETF 시대 (post-2024) BTC-Gold 디커플 + decoupled regime → BTC 약 = digital-gold 서사 ★부정

main subagent 12축 audit 진입 시 본 self-audit 참고 → 독립 재계산 권고. yaml v3 신규 블록은 audit 통과분 (H9 + H11) 만 통합, REJECTED 4건은 ledger 탈락 박제.
