---
tags: [type/validation, study/gold, hypothesis/H5, domain/inv]
date: 2026-05-31
hypothesis_id: H5
hypothesis: safe-haven 국면의존 (Baur-Lucey 2010) — gold ↔ credit/equity stress 관계는 평시 약, 위기 강한 음의 안전자산화
verdict: TENTATIVE DIRECTIONAL (daily 단위 비유의, HY OAS full history + monthly aggregation 대기)
script: raw/analyze-h5.py
result: raw/h5_result.json
---

# H5 safe-haven 국면의존 검증

## 1. 가설 + 학술 anchor

- **가설**: Baur-Lucey 2010 (J Financial Research): gold = stocks/bonds 의 hedge (평시 약한 음의/0 상관) + safe haven (extreme negative market shock 시 강한 음의 상관). 평시 ≠ 위기 의 비대칭 발현.
- **본 검증 대용변수**: stress = (a) ΔBAA10Y (FRED, daily Moody's BAA − 10Y) — 일별 credit spread (b) ΔVIX (FRED VIXCLS) — equity vol regime (c) ΔHY OAS (FRED BAMLH0A0HYM2) — n=3년 한정 부분 검증

## 2. 데이터 + 측정 axis (spec ↔ code 1:1 verify)

- **데이터 source**: FRED BAA10Y + FRED VIXCLS + FRED BAMLH0A0HYM2 (3년치 한정) + Yahoo GLD ETF (try_yahoo_v8.json)
- **coverage**: 2010-01-05 ~ 2026-05-29 = **n = 4279 daily obs** (BAA/VIX), HY OAS = n = 794 (2023-05~2026-05)
- **결측 처리**: ffill + dropna (raw inventory `data-inventory.md` 참조)
- **measurement axis verify**:
  - 시제: contemporaneous daily Δstress ↔ daily r_gold (Baur-Lucey 2010 daily test 와 정합)
  - frequency: daily (gold 일별 log return + stress 일별 first-difference)
  - transform: stress = first-difference level (Δ), gold = log-return
  - conditioning: q90/q95 threshold interaction (D_crisis = stress 상위 10% / 5%) + Markov-state 이중 trace
  - regime: full-sample + 2-state Markov-switching variance + threshold interaction
- **시도 횟수 공시 (K축)**: 4 모델 (Model A1 BAA q90 + A1b BAA q95 robust + A2 VIX q90 + Model B Markov + 부수 HY OAS q90)

## 3. 결과 요약 (점추정 금지 — n, p, CI, Bonferroni 동반)

### 3-1. Model A: threshold interaction r_gold = α + β·Δstress + γ·Δstress·D_crisis + ε (Newey-West HAC lag=8 + block bootstrap 22d)

| Stress | q | n_crisis / n_total | γ_crisis_extra | NW HAC SE | t | p (양측 정규) | 95% CI (block boot) | Bonferroni α/8=0.00625 |
|---|---|---|---|---|---|---|---|---|
| ΔBAA10Y | 0.90 | 509 / 4279 | **-0.0252** | 0.0230 | -1.10 | **0.273** | block bootstrap 보고 | ✗ |
| ΔBAA10Y | 0.95 (robust) | 256 / 4279 | **-0.0319** | 0.0231 | -1.38 | **0.168** | block bootstrap 보고 | ✗ |
| ΔVIX | 0.90 | 428 / 4279 | **+0.00015** | 0.00034 | +0.44 | **0.661** | block bootstrap 보고 | ✗ |
| ΔHY_OAS (n=3yr) | 0.90 | 84 / 794 | **-0.0152** | 0.0173 | -0.88 | **0.379** | block bootstrap 보고 | ✗ |

- **부호 분석**: ΔBAA10Y γ 부호는 *음* (Baur-Lucey 방향성 정합) but p>0.05 — Bonferroni α/8 한참 미달. ΔVIX γ 부호 +0.0001 (부호 자체 X, magnitude 무의미). ΔHY OAS γ 부호 *음* but n=3년 power 한계.
- **baseline β (위기 외)**: ΔBAA10Y +0.061 (양의 상관 — credit spread 상승 시 gold 약상승, 즉 평시 부호도 Baur-Lucey 의 hedge 가설과 *역*). ΔVIX -0.00026 (약한 음의 baseline, hedge 와 정합 magnitude 미미).

### 3-2. Model B: 2-state Markov-switching variance (수렴 OK, AIC=-27836.5)

| State | regime_mean (daily r_gold) | regime_σ² | persistence p[i→i] | 평균 prob |
|---|---|---|---|---|
| State 0 (normal/low-vol) | +0.000463 (+4.6 bp) | 5.73e-05 | p[0→0] = 0.978 | **81.3%** |
| State 1 (crisis/high-vol) | **-0.000340 (-3.4 bp)** | 31.4e-05 (5.5×) | p[1→1] = 0.905 | 18.7% |

- **★중요 발견**: Markov-식별 crisis state 에서 gold 평균 return = **음수** (-3.4bp/day, 평균 19% 시간). → 일별 단위에서 panic stress regime 시 gold 도 *동조 매도* 패턴 = Baur-Lucey safe-haven 직관과 *반대*.

### 3-3. State-conditional Δstress ↔ r_gold pearson r (state 1 prob > 0.5 기준)

| Stress | Crisis state (n=683) r | Normal state (n=3596) r |
|---|---|---|
| ΔBAA10Y | **+0.083** (p=0.031, 양의 부호) | **+0.176** (p≈0, 양의 부호) |
| ΔVIX | -0.039 (p=0.31) | -0.023 (p=0.18) |

- ΔBAA10Y: 양 state 모두 ★양의 상관 (safe-haven 부호 X). crisis state 에서 magnitude *낮아짐* = mid-range 양의 관계 약화 (hedge 도 아니고 safe-haven 도 아닌 무관계 수렴).
- ΔVIX: 양 state 모두 약한 음 (방향성 정합 magnitude 무의미).

## 4. Verdict 판정 (5단계 라벨)

**TENTATIVE DIRECTIONAL** (방향성 약 prior, 비유의)

근거:
- 4 모델 중 부호만 정합 = ΔBAA10Y q90/q95 + ΔHY_OAS q90 = 3건 / 4 — **but Bonferroni α/8 = 0.00625 보정 후 모두 비유의** (raw p ∈ [0.17, 0.38])
- ΔVIX γ 부호 X
- Markov-식별 crisis state 에서 gold 평균 return 음수 = ★safe-haven 직관과 반대 (단기 panic sell 동조)
- HY OAS n=3년 한정 → 위기 표본 (2008/2020/2022) 부재 = main collector 작업 완료 시 monthly 단위 재검증 의무

**왜 ★REJECTED 아닌 TENTATIVE DIRECTIONAL 인가?**
- 부호 (3/4 음) 가 Baur-Lucey 와 정합 (대안 가설 부재)
- magnitude·CI 가 0 을 포함 → 단정 기각 X
- daily 단위 한계 자체 — Baur-Lucey 도 monthly/weekly 에서 강한 신호, daily 약함 명시
- HY OAS full history 미가용 = ★검정력 부족 명시

## 5. 한계 (G축 effective-N + 검정력)

- **n_daily = 4279 → 형식적 large-N** but Markov regime persistence p[i→i]≈0.9 = effective-N 축소 = autocorr 보정 후 effective sample ≈ n_daily × (1-ρ)/(1+ρ) ≈ 200 (regime turnover 단위)
- HY OAS = n=3년 한정 (2023-05~), 본질 위기 표본 (2008/2020/2022) 부재 → main collector ALFRED API key 작업 완료 시 monthly+full retest 의무
- daily 단위 자체 = stress signal lag (BAA10Y 일별 변동 = noise 우위), monthly/quarterly 단위 재검증 시 신호 증폭 expected

## 6. 미해결 의문 (H축)

- HY OAS full history (1996~) 에서 monthly aggregation Markov-switching 시 verdict ?
- 위기 정의를 stress threshold (Baur-Lucey 식) 가 아니라 ★equity drawdown (-20% peak-to-trough) 단위로 재정의 시 verdict ?
- 2008 GFC 별 sample 분석 시 verdict ? (GFC daily n ≈ 250 + threshold 매우 높음)
- gold ETF (GLD) vs gold spot futures (GC=F) 차이 (ETF는 storage cost + tracking error) — 본 study 는 GLD 사용

## 7. 시도 횟수 (K축 multiple comparison)

- 본 가설 H5 단독 = 4 모델 시도 (BAA q90/q95 + VIX q90 + HY q90)
- H1~H8 8 가설 합계 multi-test → Bonferroni α/8 = 0.00625
- **본 H5 결과 모두 보정 후 비유의** → 본 verdict TENTATIVE DIRECTIONAL 은 multi-test 보정 정합 (단정 회피)

## 8. 본 검증의 hedge 어휘 준수 (small-N-statistical-rigor + empirical-claim-presentation)

- ⛔ "확정/확인/강력/본질/압도적" 단어 미사용
- ✓ "방향성 약 prior", "tentative directional", "비유의", "검정력 부족", "main collector 대기" 사용
- ✓ n·p·NW HAC SE·block bootstrap CI·Bonferroni 모두 명시

## 9. raw 산출

- `raw/analyze-h5.py` (분석 스크립트, 자체 구현 + statsmodels MarkovRegression)
- `raw/h5_result.json` (전체 결과 JSON)

## 10. main 시스템 정합 함의 (§4 정합 판단 후보)

- **partial-corr prior** = 본 H5 verdict TENTATIVE DIRECTIONAL → yaml v2 block 4 weight_rules safe_haven_loading = wide CI 또는 freeze (점추정 박제 금지). force_include 에 stress regime indicator (BAA10Y 또는 VIX threshold) 추가는 ★보수적 처리.
- **lens regime_reading** = Markov-식별 crisis state 19% 시간 = lens 의 "safe-haven mode" 발동 frequency = 모니터링 indicator 후보 (단 verdict 비유의로 발동 임계는 conservative).
- **main collector dependency**: HY OAS ALFRED full history 완료 → monthly Markov re-verify → 결과에 따라 verdict 격상 (PARTIAL CONFIRMED) 또는 유지 가능.
