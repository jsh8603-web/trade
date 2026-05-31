---
tags: [type/evaluation, study/crypto, cycle/2, audit/independent]
date: 2026-06-01
auditor: opus independent 12-axis subagent (self-certify 금지, raw 재실행 기반)
audit_target: crypto cycle 2 (H7-H12 신규 + cycle1 H1-H6 통합) + v3 draft (H9/H11 통합 후보)
verdict: 부분 (hard 코어 0 — 단 H11 통합 후보 over-claim 으로 격하 필요)
---

# crypto cycle 2 독립 12축 audit (2026-06-01)

> ★방의 self-audit-cycle2.md = 참고 자료. 본 평가 = raw data + scripts 독립 재실행 판정.
> 모든 cycle2 수치 (H7~H12) + cycle1 (H1~H6 + prior ladder) **재실행으로 ±0% 재현** (timestamp 외 diff 0).

---

## §0. Provenance + Recomputation (재실행 결과)

| 가설 | 방 보고 | 독립 재실행 | 일치 |
|---|---|---|---|
| H7 AdrActCnt IC | 0.0085 (n=3178) | **0.0085** β=0.0151 CI[-0.0028,+0.0347] | ✓ |
| H8 TxCnt IC | 0.0022 / partial -0.0042 | **0.0022 / -0.0042** | ✓ |
| H9 ANOVA | F=7.504 p=0.0006 / KW p=0.0002 | **F=7.504 p=0.0006 / p=0.0002** | ✓ |
| H10 risk-off corr | 0.1796 (N_eff=5) / post-ETF p=0.0002 | **0.1796 / 0.0002** | ✓ |
| H11 attn IC | 0.1117 (n=94) | **0.1117** | ✓ |
| H12 TVL partial | -0.0120 | **-0.0120** collin 0.1703 | ✓ |
| cycle1 H1 partial | -0.085 CI(-0.235,+0.073) | **-0.0847 CI(-0.2349,+0.0734)** | ✓ |
| prior ladder | onchain 1.27 > micro 0.97 > stable -0.43 | **1.275 / 0.970 / -0.431** | ✓ |

- **합성 지문 검사 PASS**: BTC daily kurtosis=15.69 (실측 fat tail), COVID 2020-03-12 일별 logret -0.50, FTX 2022-11 -0.15, LUNA 2022-05 -0.12 — 알려진 역사 이벤트 실재. 주말 갭 0 (BTC 365일 정상). 합성 흔적 없음.
- git diff = timestamp 5줄만, 통계 본문 byte-identical = **완전 결정론적 재현**.

---

## §1. 12축 verdict

| 축 | verdict | 근거 (재실행 수치 박제) |
|---|---|---|
| **A 이론** | PASS | H7 Pagnotta&Buraschi 2018 / H8 Catalini&Gans / H9 Baur 2018 / H10 Baur·Klein / H11 LTW 2021 / H12 Cong 2022. 점추정 magnitude 박제 X. ⚠️한계 자인: 원전 PDF 직접 접근 X (abstract+자문 압축) — soft. |
| **B 실데이터** ★ | **PASS** | 합성 0건. 모든 IC 재실행 ±0% 재현. Newey-West HAC + block bootstrap 적용 확인. B threshold (IC>0.03 & t>2.0): H7/H8/H10/H12 FAIL→REJECTED 합당. H9 continuous IC=-0.0027 (t=-0.12 null). ★H11 IC=0.1117 = magnitude 만, 아래 K축 참조. |
| **C 추적성** ★ | **PASS (yaml 미통합 단계)** | cycle2 결과 = v3 draft 단계, 현 study_session.yaml = v2 (cycle1). 통합 후보 H9 prior 0.15 / H11 prior 0.20 만 제안. 매직넘버 없음. cycle1 yaml 수치 (mvrv -0.085, ladder sharpe) 재실행 일치. |
| **D PIT/lookahead** ★ | **부분** | T+1 release 일관 (CoinMetrics 익일 02:00 / yfinance/FRED/PyTrends/DefiLlama T+1). fwd_ret close-to-close lookahead 회피. ⚠️**FRED first-release vintage 미적용** (M2SL/DFII10 revised 사용 — cycle3 ALFRED 의무, 방 자인). ⚠️H9 regime threshold(0.4/-0.1) + vol tertile = post-hoc in-sample (eff_n_gate 자인). hard 아님 (cycle2 macro 채널 미통합). |
| **E 자문 환각** | PASS | round-{1,2,3}-{gemini,claude}.md 인용 실재. 학술 점추정 (Pagnotta α 0.5~1.2, LTW +0.5~+0.7, Baur "corr~0") **박제 X, 본 표본 재현 우선** — StockToFlow류 반례도 본 표본 기각 처리. 환각 claim 0건. |
| **F 반증** | **PASS (강)** | REJECTED 4건 (H7/H8/H10/H12) = p-hacking 신호 0. 각 가설 falsifier 사전 명시 (spec-code-rationale §1-6). 기각 풍부 = F축 모범. |
| **G effective-N tier** | PASS | halving N=4 → standalone IC 금지, regime label only 유지 (validated alpha 위장 차단). H10 risk-off N_eff=5 ★INSUFFICIENT 라벨. H11 N_eff=61 → "structural prior(저신뢰)" 라벨, validated alpha X. tier 라벨링 정직. |
| **H 미해결** | PASS | self-audit §5 10항목 (weekly base / Granger endogeneity / VECM / paid tier / Deflated Sharpe / 거래비용 / tail-corr / ALFRED). 공란 아님. |
| **I 생존편향** ★ | **PASS (caveat)** | BTC only 명시. ⚠️Binance klines = surviving exchange (MtGox 등 상폐 거래소 미포함). ⚠️H12 DeFi TVL = surviving protocols only (TerraUSD/FTX 상폐 미포함 → 위기 TVL drop 약화, 방 자인). BTC 중심 + caveat 박제 = hard 아님. 멀티코인 확장 시 ICO 상폐 token universe PIT 별도 처리 의무. |
| **J 경제유의성** | 부분 (미적용) | cycle2 = 통계 유의만. 거래비용 (왕복 0.3%+funding) 차감 미수행 (cycle3 의무). H9 +4.35%/-3.46%, H11 +10.41%/month 는 정성 lens 용도 → 허용. alpha 주장 아님 → hard 아님. |
| **K 다중검정** ★ | **부분 (★H11 over-claim)** | 시도횟수 공시 O (K=174 = H7 24+H8 50+H9 36+H10 36+H11 16+H12 12). H9 ANOVA p=0.0006 = per-hyp K=36(α=0.00139) 생존하나 **full-family K=174(α=0.00029) 미생존**, KW p=0.0002 만 full-family 생존 = 경계. ★**H11 IC=0.1117 raw p=0.2837 — 무보정 유의성도 실패**. `|IC|>0.03` 게이트 = 유의성 검정 아님. **Deflated/Haircut Sharpe 미적용** (cycle3 의무). |
| **L 통합 정합** | PASS (보류) | H9 BTC-Nasdaq = global risk + USD funding 공통인자 1회 계상 박제 (gold/equity sleeve 중복 회피). H12 TVL↔stablecoin USD 공통인자. tail-corr regime (위기 corr→1) point estimate 박제 금지 명시. 중첩 윈도우 Newey-West/block 강제 확인. 미통합 단계 = PSD 게이트 통합 시 적용. |

---

## §2. Hard-fail 게이트 결과

- **코어 4 (B/C/D/I)**: 위반 **0건**. (D·I 는 cycle3 의무 caveat 부착, hard 미해당 — macro/멀티코인 미통합 + BTC caveat 명시).
- **조건부 hard**:
  - K 시도횟수 공시 = PASS (174 박제). Deflated Sharpe 미적용 = tier 강등 (차단 X).
  - J alpha 주장 = 없음 (정성 lens) → PASS.
  - E 환각 = 0건 → PASS.
  - F 기각 0건 = 아님 (4건) → PASS.
  - L PSD = 미통합, 차단 사유 없음.
- **★H11 PARTIAL CONFIRMED = over-claim (K축 격하 사유)**: hard-fail 아니나 verdict 라벨 무효.

→ **hard 코어 0 — register 가능 영역. 단 통합 후보 2건 중 H11 은 라벨 격하 필수.**

---

## §3. ★핵심 독립 발견 (방 self-audit 미포착)

### (1) H11 attention — PARTIAL CONFIRMED 은 over-claim. ★TENTATIVE DIRECTIONAL 로 격하 의무
독립 재계산:
- **IC=0.1117 의 raw Spearman p = 0.2837 (n=94)** — 무보정에서도 비유의. 방 script 는 IC p-value 를 산출/보고하지 않고 `|IC|>0.03` 게이트만 사용 = 유의성 근거 없음.
- **block-bootstrap IC CI95% = [-0.137, +0.302] → 0 포함** (block=6m, B=2000). 자기상관-robust SE 적용 시 0 과 구분 불가.
- **U-shape, 비단조**: attn_z>+1σ mean=+0.104 **AND** attn_z<-1σ mean=+0.105, mid=-0.010. 양 꼬리 모두 높음 = 방향성 attention 신호가 아니라 **변동성(분산) 효과**. verdict 의 근거 `extreme_diff = mean_high > mean_mid` 는 오도. LOO IC [0.086,0.140] 은 안정하나 이는 점추정 안정성일 뿐 유의성 아님.
- empirical-claim rule §1.2: n<30 아니나 n=94 monthly + raw p>0.10 = TENTATIVE DIRECTIONAL 상한. **PyTrends 'all' = monthly aggregate (median gap 31일)** = LTW 2021 weekly base 와 frequency drift (large) — spec-code §5 자인.
- → **H11 prior_strength 0.20 제안 = 과도. 0.05~0.10 observe-only (probation) 또는 weekly base 재검증 전 통합 보류 권고.**

### (2) H9 BTC-Nasdaq — TENTATIVE DIRECTIONAL 적정하나 full-family 경계
- ANOVA p=0.0006 은 per-hyp K=36 생존 but **full-family K=174 (α=0.00029) 미생존**. KW p=0.0002 만 생존 = 경계 신호.
- regime 전이 6.55/year (분기 1회 초과) = regime label 불안정 (방 자인). decoupled cell N_eff=5 (n=181 but 강 autocorr).
- regime threshold (0.4/-0.1) + vol tertile = post-hoc in-sample cut → walk-forward strict OOS 전 통합 = lookahead 위험 잔존.
- → H9 prior 0.15 = TENTATIVE structural prior 로 수용 가능하나 **walk-forward OOS 후 통합** 조건부 권고. digital-gold 정반대 방향(decoupled→BTC약) 은 자료 가치.

### (3) prior ladder on-chain 1.27 의 effective_n_raw=15.97
- mvrv base_weight 0.55 ("가장 강한 sleeve modulator") 의 근거 = on-chain rolling sharpe 1.275, 그러나 **n_windows=47 effective_n_raw=15.97** (180d 강 overlap). ~16 effective obs 위 sharpe 비교 = 점추정 신뢰 낮음. cycle1 yaml 사항이라 cycle2 범위 밖이나, 통합 시 mvrv 0.55 의 confidence tier 재고 권고.

---

## §4. 종합 verdict

**부분 (hard 코어 B/C/D/I = 0, F·E·G·A·L PASS — 단 H11 통합 후보 over-claim 격하 필수, H9 조건부)**

- cycle2 본체 = **충실 영역**: 재현 100%, 합성 0, 기각 4건 (p-hacking 0), 점추정 박제 없음, validated-alpha 위장 없음.
- 통합 후보 2건만 조치 필요 → 전체 verdict "부분".

---

## §5. yaml v3 통합 시 조치 (격하/보강)

| 항목 | 방 제안 | 독립 audit 조치 |
|---|---|---|
| **H11 attention** | indicator `pytrends_btc_attn_z` + prior 0.20 (PARTIAL CONFIRMED) | ★**격하**: verdict → TENTATIVE DIRECTIONAL. prior_strength **0.20 → 0.05~0.10 observe-only**. confirm_signal 에 IC p-value (현 raw 0.28) + block-boot CI(0 포함) 박제. weekly base 재검증 전 **probation 라벨**. U-shape(분산효과) caveat 명시. |
| **H9 regime** | indicator `btc_nasdaq_corr_60d_regime` + prior 0.15 (TENTATIVE) | **조건부 수용**: prior 0.15 유지 가능하나 **walk-forward strict OOS PASS 를 통합 게이트**로. full-family K=174 ANOVA 미생존(KW 만 생존) 박제. regime 전이 6.55/yr 불안정 + threshold post-hoc caveat. |
| H7/H8/H10/H12 | ledger 탈락 | ✓ 동의 (REJECTED 합당, candidate-ledger ❌탈락 박제 적정). |
| D축 FRED vintage | cycle3 ALFRED | 통합 전 first-release 적용 권고 (macro 채널 통합 시 hard 승격 가능). |
| K축 Deflated Sharpe | cycle3 | K=174 family 에 Deflated Sharpe 적용 후 H9/H11 재평가 의무. |

---

## §6. 결론 (main 보고용)

cycle2 = 기각 4 + 약신호 2 의 **정직한 산출**. hard 코어 4축 위반 0, 완전 재현, 합성/생존편향/환각 catch 무. validated-alpha 위장 차단(G축 tier) 정상 작동. 단 **통합 후보 H11 의 PARTIAL CONFIRMED 라벨이 IC p=0.28·block-boot CI 0포함·U-shape 로 over-claim** → TENTATIVE DIRECTIONAL + observe-only 격하 필수. H9 는 walk-forward OOS 조건부 수용. 두 조치 반영 시 register 가능.
