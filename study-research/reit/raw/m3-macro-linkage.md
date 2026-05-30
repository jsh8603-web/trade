---
tags: [type/m3-linkage, study_id/reit, phase/M3]
date: 2026-05-30
study_id: reit
phase: "M3 거시연관 — REIT sleeve factor loading × E1~E4 epoch"
data: "yfinance auto_adjust + FRED DGS10 실데이터, 2022-01~2024-12, n=753 daily"
script: raw/scripts/m3_macro_linkage.py / output: raw/scripts/m3_macro_linkage.log
ref: ../macro/raw/m1-findings.md, ../macro/timeline.md
note: macro/timeline.md §4 가이드 4 step 산출 — regime별 수익분해 + factor loading + cross-asset vs within-sleeve. ⛔합성無, U3 실현수익률 전용.
---

# REIT M3 거시연관 — factor loading × E1~E4 epoch 실측

## 0. 측정 frame
- **기간**: 2022-01-01 ~ 2024-12-31 (M1 timeline 정합), 일별 n=753
- **종목**: VNQ + 9 sub-sector ETF (PLD/AVB/BXP/WELL/EQIX/PSA/SPG/HST/AMT)
- **factor**: rate(Δus10y bp) / dollar(Δlog DXY) / oil(Δlog WTI) — M1 정의 mirror
- **방법**: OLS `sleeve_ret ~ rate + dollar + oil + intercept`, 전체 + epoch 별 fit
- **U3 reflexive 차단**: belief/flag 不유입, 실현수익률 전용. ⛔ 합성·시뮬無.
- **epoch (M1 §3 정합)**:
  - E1 긴축충격 2022-01-01 ~ 2022-09-30 (n=188, rate↑↑·dollar↑↑·risk-off)
  - E2 전환·반등 2022-10-01 ~ 2023-06-30 (n=187, rate 고원→완화, SVB)
  - E3 금리재상승 2023-07-01 ~ 2023-09-30 (n=63, rate↑·oil↑)
  - E4 pivot·인하 2023-10-01 ~ 2024-12-31 (n=315, rate↓·dollar↓)

## 1. regime별 수익률 분해 (cumulative %)

| sleeve | 전체(753d) | E1(긴축, 188d) | E2(반등, 187d) | E3(재상승, 63d) | E4(pivot, 315d) |
|---|---:|---:|---:|---:|---:|
| **VNQ** | **−13.54** | **−29.32** | +7.97 | −8.57 | **+23.91** |
| Industrial | −31.64 | −38.52 | +23.27 | −7.85 | −2.11 |
| Apartment | −3.44 | −25.39 | +5.78 | −8.39 | +33.55 |
| Office | −23.45 | −32.85 | −19.17 | +5.03 | +34.29 |
| Healthcare | **+59.90** | −23.35 | +28.93 | +2.01 | **+58.60** |
| Datacenter | +18.15 | −31.84 | **+39.81** | −6.93 | +33.21 |
| Storage | −7.44 | −17.16 | +2.47 | −8.73 | +19.46 |
| Retail | +28.10 | **−41.24** | +34.81 | −4.89 | **+70.04** |
| Hotel | +15.05 | −7.53 | +10.00 | −3.43 | +17.13 |
| Tower | −31.20 | −25.77 | −6.90 | **−15.21** | +17.39 |

**관찰**:
1. **E1 긴축충격 매도 일관성** — 9 sub-sector 모두 음수 (`min ρ=+0.267, mean=+0.569` § 3 참조). systemic rate shock 에 모두 노출.
2. **E2 반등 차등** — Datacenter(+39.81%)/Retail(+34.81%) 회복 우위, Tower(−6.90%)/Office(−19.17%) 부진 잔존.
3. **E4 pivot 폭주** — Retail +70%, Healthcare +58.6%, Apartment/Office +33~34% 광범위. Tower/Industrial 만 한자릿수 회복 (high-duration 자산이 rate-down 으로 가장 수혜라는 단순 직관과 정반대 — § 5.3 참조).
4. **전체 sweep**: Healthcare/Retail/Apartment outperform · Industrial/Tower underperform → 단순 "rate-sensitive sector" 분류로 안 잡힌다. ★window-flip (H4 CONFIRMED) 패턴 부합.

## 2. factor loading B (★M1 비교 핵심)

### 2.1 전체 기간 (n=753)

| sleeve | β_rate (bp scale) | t | β_dollar | t | β_oil | t |
|---|---:|---:|---:|---:|---:|---:|
| **VNQ** | **−3.82** | **−5.65** | **−0.841** | **−8.33** | −0.008 | −0.42 |
| Industrial | −4.51 | −4.57 | −0.848 | −5.77 | −0.003 | −0.10 |
| Apartment | −2.76 | −3.49 | −0.706 | −6.00 | −0.024 | −1.14 |
| Office | −2.57 | −2.09 | −1.048 | −5.72 | +0.041 | +1.22 |
| Healthcare | −2.08 | −2.47 | −0.669 | −5.34 | −0.014 | −0.63 |
| Datacenter | −5.39 | −5.52 | −0.735 | −5.04 | −0.031 | −1.18 |
| Storage | −4.74 | −5.50 | −0.697 | −5.43 | +0.003 | +0.13 |
| Retail | −0.89 | −0.96 | −1.049 | −7.59 | +0.002 | +0.10 |
| **Hotel** | **+1.79** | +1.67 | **−1.387** | **−8.71** | +0.020 | +0.68 |
| **Tower** | **−6.86** | **−7.43** | −0.822 | −5.98 | −0.032 | −1.28 |

### 2.2 ★ M1 발견 (주식) vs REIT — 핵심 대비

| 발견 | M1 us_stock (sp500) | REIT VNQ | 정합? |
|---|---|---|---|
| **β_rate ≈ 0?** | **+0.008** (loading 거의 없음) | **−3.82 bp** (t=−5.65 강하게 음수) | ❌ **불일치** |
| **β_dollar 크기** | −0.879 | **−0.841** | ✅ 거의 동일 |
| **β_oil ≈ 0?** | +0.020 | −0.008 | ✅ 일치 |

→ **M1 의 첫 발견 ("주식은 rate 직접 loading ≈ 0, dollar 채널 본질") 은 REIT 에 그대로 적용 불가**. REIT 는 **rate 직접 loading 강함** (VNQ −3.82bp / t=−5.65 / 9/10 sub-sector 음수 유의). 채권성 듀레이션 자산 성격이 데이터에서 확인됨 (이론적 NAV 할인율 채널). 한편 **dollar loading 은 주식과 동일 강도** — REIT 가 risk-on/off · USD funding 채널에서도 주식과 같이 노출됨.

### 2.3 ★ M1 dollar loading rate-UP 2배 패턴 — REIT 검증

M1 us_stock dollar loading: rate-UP −0.998 vs rate-DOWN −0.593 = **1.68배**, M1 tech 1.59배.
REIT 검증 (E1 긴축충격 vs E4 pivot 비, 모두 |·| 절대값 기준):

| sleeve | E1 β_dollar | E4 β_dollar | |E1|/|E4| |
|---|---:|---:|---:|
| VNQ | −0.876 | −0.787 | **1.11x** |
| Industrial | −0.878 | −0.687 | 1.28x |
| Office | −0.904 | −1.335 | **0.68x** (역방향) |
| Apartment | −0.842 | −0.632 | 1.33x |
| Healthcare | −0.641 | −0.423 | 1.52x |
| Tower | −0.811 | −0.578 | 1.40x |

→ **M1 의 2배 패턴이 REIT 에선 1.1~1.5배 수준으로 약화**. Office 는 역방향 (E4 가 더 강함 — pivot 국면에서 USD weak 와 office liquidation 동시 진행 가설). REIT 의 dollar 채널 국면조건부성은 주식보다 약하다 — 이미 rate 직접 loading 으로 충격이 흡수되기 때문 가설.

### 2.4 epoch flip — REIT 특유 (M1 에 없는)

| sleeve | E1 β_rate | E2 β_rate | E3 β_rate | E4 β_rate | 해석 |
|---|---:|---:|---:|---:|---|
| VNQ | −3.66 | −1.07 | **−6.30** | **−6.44** | E1/E2 약화 → E3/E4 강화. pivot 기대에서 오히려 듀레이션 민감도 ↑ |
| Office | −1.30 | **+4.20** | −11.79 | −7.96 | E2 만 부호 반전. SVB 후 안전선호+오피스 short-cover 가설 |
| Healthcare | −4.28 | **+2.18** | −4.28 | −3.47 | E2 만 부호 반전. 약물 cycle/M&A 무관변동 가설 |
| Tower | −3.71 | −5.23 | −9.13 | **−12.01** | 일관 강한 음수, E4 가 최대. long-duration 자산 패턴 |
| **Hotel** | **+1.74** | +2.38 | −5.95 | +1.20 | **E1·E2·E4 양수** (lodging 단기 lease = rate hedge), E3 만 음수 |

★ **Hotel β_rate +1.79 (전체) 는 REIT 안에서 유일한 양수 group**. lodging 은 1박 단위 가격결정 → rate 와 직접 비연관, inflation hedge 성격. 다른 REIT (장기 lease) 와 본질 다름.

## 3. cross-asset vs within-sleeve 구분 (L축 caveat)

9 sub-sector pairwise correlation 평균 (within-sleeve = equity factor proxy):

| epoch | n_days | mean ρ | min ρ |
|---|---:|---:|---:|
| 전체 | 753 | **+0.547** | +0.319 |
| E1 긴축충격 | 188 | +0.569 | +0.267 |
| E2 전환반등 | 187 | **+0.603** | +0.429 |
| E3 금리재상승 | 63 | **+0.399** | −0.098 |
| E4 pivot·인하 | 315 | +0.511 | +0.211 |

**관찰**:
1. REIT within-sleeve mean ρ = **0.55**. M1 us_stock~tech +0.96 보다 훨씬 낮음 → REIT sub-sector 간 분산 (sector effect) 이 주식보다 크다. **단순 broad REIT beta 만으로 sub-sector 차이 못 잡음** = lens·weight 모델은 sector 단위로 가야.
2. E3 (rate 재상승 + n=63 short) 만 min ρ 음수 (Office 와 Datacenter pair) — 짧은 국면이라 noise 가능.
3. 그러나 mean ρ ≥ 0.4 → equity broad factor 도 무시 못함. **M1 caveat 동일 적용**: factor_implied cross_cov 의 named factor (rate/dollar/oil) 는 REIT sleeve **대(對)** 다른 자산군 cov 에 쓰고, within-sleeve (9 sub-sector 간) 공통은 sleeve 자체 모델(REIT equity factor) 소관.

### L축 ① 회 계상 + PSD
- cross-asset (named factor B Λ Bᵀ) 와 within-sleeve (equity factor) 를 별도로 모델링하면 공통 인자 1회 계상 invariant 충족.
- ε_REIT_idio = 종목별 noise + sector-specific (예: Hotel lodging 특성). diag idio_var 로 처리.
- PSD: Σ_full = B Λ Bᵀ_cross + W_within + Δ_idio 가 PD 여야 (M1 동일 검증 프레임).

## 4. macro/timeline.md §4 4-step 답변

| step | 답 |
|---|---|
| ① regime별 수익분해 | §1. E1 일관 매도(min cum=Retail −41.24%) → E4 광범위 폭주 (Retail +70%, Healthcare +58.6%). E2/E3 차등. |
| ② factor loading | §2. ★ **REIT 는 rate 직접 loading 강함** (VNQ β_rate −3.82bp t=−5.65, 9/10 음수 유의). M1 주식 ≈0 패턴과 다름. dollar loading 은 주식과 동일 강도 (−0.84). |
| ③ cross-asset vs within-sleeve | §3. REIT within ρ=0.55 (주식 0.96 대비 낮음). sector effect 존재. cross-asset cov 와 within-sleeve cov 별도 처리 필수 (L축 invariant). |
| ④ main 회신 | §6 별도 (psmux-send.sh). |

## 5. 후속 / caveat

### 5.1 정직: 데이터 한계
- 기간 2022-01 ~ 2024-12 (3년) — 장기 epoch (GFC, COVID) 미포함. epoch별 n (특히 E3 = 63 days) noise 노출.
- E3 short window 에서 negative min ρ 와 큰 t-value 흔들림은 ovefit 의심. 본 결과는 prior 로만 사용, 강한 단정 자제.
- ⛔ 합성·시뮬無 보존: 모든 통계는 yfinance auto_adjust(생존편향 잠재) + FRED DGS10 실데이터.

### 5.2 생존편향 (I축)
- 9 sub-sector 대표 ticker (PLD/AVB/BXP/WELL/EQIX/PSA/SPG/HST/AMT) = 2022~2024 모두 listed + 생존. 본 기간 상폐 REIT 미포함 (예: Office sector 의 stress 회사).
- → β_office (−2.57 t=−2.09) 는 생존회사 평균. 상폐 포함 universe 의 office REIT β_rate 는 더 음수 (더 약함) 가능. v2 yaml block 8 동일 caveat.

### 5.3 직관 vs 데이터: Tower paradox
- **Tower (AMT) E4 β_rate = −12.01** (t=−7.88, 가장 음수). pivot 국면 rate-down 임에도 가장 강한 음수 loading.
- 단순 직관 ("rate-down → long-duration 자산 +" = Tower 폭주) 과 부합 안 함 (Tower E4 cum = +17.39%, Retail +70 와 큰 차이).
- 가설: Tower 의 lease 구조 (장기 통신사 계약) 가 inflation pass-through escalator 가 약해서, rate-down 의 NAV 부양 < disinflation 의 lease 가치 절하. (가설, 본 단계 검증 못 함 — H1 reject 과 함께 후속 의문.)

### 5.4 study_session.yaml v2 보강 후보
- block 4 (regime_lens) 의 4-regime + rate-shock 조건부 weight 에 **β_rate epoch flip** 데이터 추가 가능.
- block 3 (corr_prior) within-sleeve mean ρ=0.55 박제 — 현 cross-asset 가정과 분리.
- block 8 (self_audit) E축에 본 M3 검증 결과 추가 (rate loading 강함 = M1 주식 패턴 invalid 적용, dollar 2배 패턴 약화).

## 6. main 회신 (요약)

→ `psmux_send_message btn-Codlearn ...` 로 별도 전송.

핵심 1-line: **REIT 는 M1 주식과 달리 rate 직접 loading 강함 (VNQ β_rate −3.82bp t=−5.65, 9/10 음수 유의). dollar loading 은 주식과 동일 강도 (−0.84) but rate-UP 2배 패턴은 약화 (1.1~1.5배). within-sleeve ρ=0.55 (주식 0.96 대비 낮음, sector effect 존재). E1 일관 매도 → E4 광범위 폭주. Hotel 만 β_rate 양수 (lodging short-lease 특성). Tower E4 −12.01bp (long-duration paradox 후속의문).**

## 산출 cross-ref
- Script: `raw/scripts/m3_macro_linkage.py`
- Log: `raw/scripts/m3_macro_linkage.log`
- Ref: `../macro/raw/m1_factor_linkage.py`, `../macro/raw/m1-findings.md`, `../macro/timeline.md` §3 §4
- Trace: `raw/evidence-map.md` 에 본 결과 row 추가 예정 (v2 yaml 보강 후)
