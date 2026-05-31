# H6 검증 — breakeven common-cause + 항등식 게이트

> **명제**: gold↔breakeven 직접 효과는 항등식 매개 간접효과 (Fisher: nominal = real + BE). real_rate 조건화 후 partial corr ≈ 0.
> **★결정적 평가**: **SUPPORTED**. gold-BE partial = -0.054 (< 0.20), gold-real partial = -0.291 (> 0.20). + 항등식 collinearity 게이트의 절대 필요성 실증 (nominal 추가 시 VIF 1.04 → 12996).
> **데이터**: FRED DFII10·T10YIE·DGS10·DTWEXBGS + GLD. n=4279 일. ⛔ 합성·시뮬 0건.
> **스크립트**: `raw/analyze-h6.py`. **산출**: `raw/h6_result.json`.

---

## ★핵심 결과

### (1) 항등식 확인 — nominal ≈ real + breakeven
| 통계 | 값 |
|---|---:|
| mean(d_nominal − d_real − d_be) | -0.001 bp |
| std | 0.046 bp |
| max\|diff\| | 3.00 bp |
> Fisher 항등식 거의 정확 (소수점 round-off + intraday timing 차).

### (2) basis A partial-corr (Q2 채택 = {real_rate, breakeven, dollar, gold})

|  | d_real_bp | d_be_bp | r_dollar | r_gold |
|---|---:|---:|---:|---:|
| **r_gold** | **-0.291** | **-0.054** | -0.306 | 1.000 |
| d_real_bp | 1.000 | -0.121 | +0.030 | -0.291 |
| d_be_bp | -0.121 | 1.000 | -0.163 | -0.054 |
| r_dollar | +0.030 | -0.163 | 1.000 | -0.306 |

★ **gold-BE partial = -0.054** (< 0.20 임계) → BE 의 직접 효과 부재(common_cause 매개) ✓
★ **gold-real partial = -0.291** (> 0.20 임계) → real_rate 의 직접 효과 강함 ✓
- gold-dollar partial = -0.306 (real_rate 와 거의 동일 magnitude — H4 와 일관)

### (3) 항등식 collinearity 게이트 — basis B (위반) 검증

basis B = {nominal, real, BE, dollar, gold} (Fisher 항등식 위반):
- cov condition number = **5.33e+06** (보통 1e10 임계 미달이지만, 실제 partial-corr 결과로 영향 노출됨)
- partial corr matrix:
  - d_nom ↔ d_real = **+0.9999** (perfect collinearity)
  - d_nom ↔ d_be = **+0.9999** (perfect collinearity)
  - d_real ↔ d_be = **-0.9998** (perfect collinearity, opposite sign)
  - gold ↔ d_nom = **-0.017** (★숫자 의미 상실 — perfect collinearity 결과)
  - gold ↔ d_real = +0.014 (★숫자 의미 상실)
  - gold ↔ d_be = +0.016 (★숫자 의미 상실)
- ★ **gold 의 partial-corr 가 항등식 collinearity 로 인해 *artifact 한자릿수* 로 압축됨** → 식별 불가.

### (4) VIF 비교 — 항등식 게이트의 결정적 검증

| basis | regressors | VIF |
|---|---|---|
| **A (Q2 채택)** | {d_real_bp, d_be_bp, r_dollar} | **[1.036, 1.043, 1.048]** ✓ |
| **B (위반)** | {d_nom_bp, d_real_bp, d_be_bp, r_dollar} | **[12996.5, 10460.0, 4329.1, 1.048]** ★ |

★ basis B 의 d_nom·d_real·d_be VIF 가 4000~13000 = **1만 배 증가** (basis A 의 1.04 대비). Q2 합의 (VIF<5 게이트) 압도적 위반.

★ ★ basis A 의 r_dollar VIF (1.048) 는 basis B 와 동일 = dollar 가 항등식 변수와 직교. Q4 numeraire trap 보정 후 dollar β 가 독립 채널.

---

## §A 이론 실재성
- Fisher 항등식: nominal = real + breakeven (정의). 본 시스템 데이터에서 max|diff| 3 bp = 항등식 거의 정확.
- Barsky-Summers 1988: 금↔real rate level 관계. BE 는 nominal·real 매개. 본 검증의 gold-BE partial ≈ 0 = Barsky-Summers 의 직계 결과.
- WGC GRAM opportunity cost: real yield + dollar 4-driver category. BE 미포함 — 본 H6 결과와 정합.

## §B 실데이터 검증
- n=4279 일 (16y), 4 시리즈 + gold
- ⛔ 합성·시뮬 0
- partial-corr 매트릭스 + VIF + condition number 3 통계
- ★Q2 basis (real, BE) 결정의 ★empirical justification = 본 검증의 직접 산출

## §C yaml 도출 추적성
- direction.md ⑥ Q2 합의: basis = {real_rate, breakeven}, nominal 제외 → 본 검증의 partial-corr 매트릭스로 직접 정당화.
- 옵션 (a) (BE force_include 미포함, 항등식 basis 외부 가드): 본 검증으로 정당화 — BE 의 직접 효과 미미하므로 force_include 에 넣을 필요 없음. 단 basis 안에 두어 항등식 게이트 검증·common_cause 분해 보장.
- 블록3 relationships:
  - real_rate↔gold: prior_strength 강 (force_include) — direct edge
  - breakeven↔gold: prior_strength 약 (force_include 미포함) — undetermined 또는 common_cause via real_rate
  - conditioning_set: 일별 Δ공간 gold-real_rate edge 시 {ln_dollar, GPR} (R2 합의), breakeven 제외 (항등식 자명)
- 블록7 code_change_plan: 외부 항등식 가드 모듈 (VIF<5, condition number<30, nominal 추가 발산 검증 1회).

## §D PIT / OOS
- 본 검증 = 16y full sample IS.
- PIT 위반 없음 (DFII10·T10YIE·DGS10·DTWEXBGS 모두 실시간 daily).
- OOS plan: subsample partial-corr (pre-2022 vs 2022+) ablation — 본 검증의 결과가 시기 무관 안정인지 확인. (현 분석 미실시)

## §E 자문 비판 + 환각 cross-verify
- R2 Q2 합의 (Claude 안 {real_rate, breakeven}, Conf 5) → 본 실측의 VIF 1.04 vs 12996 으로 ★압도적 confirm.
- R2 H6 정량 임계 (gold-BE |partial|>0.20 AND gold-real |partial|<0.20 → 기각): 실측은 *역방향* — gold-BE = 0.054 < 0.20 AND gold-real = 0.291 > 0.20 → ★기각 미발생 = H6 SUPPORTED.
- 환각 검증: Fisher 항등식은 정의에 의한 등식 (학술 의문 없음). Barsky-Summers + Erb-Harvey + Reboredo 의 real_rate 단일 driver 강조와 정합.

## §F 반증 가능 + 기각 기록
- 반증 시나리오:
  - gold-BE partial > 0.20 (BE 직접 효과) → H6 기각, BE force_include 승격 정당
  - gold-real partial < 0.20 (real 직접 효과 부재) → H6 기각, BE common-cause 가설 흔들림
  - 항등식 게이트 collinearity 미발현 → VIF 시스템 무의미
- 본 검증: 모든 반증 시나리오 미발생 → H6 SUPPORTED + 항등식 게이트의 절대 필요성 실증.

## §G 검정력 한계
- ★condition number basis B = 5.33e+06 (1e10 임계 미달) — Python np.cov 의 noise 처리가 perfect collinearity 를 finite condition 으로 변환. 단 partial corr (±0.9999) + VIF (12996) 가 collinearity 의 직접 신호 → condition number 만 가지고 게이트하면 부족, VIF + partial 매트릭스 visual 검사 병용 권고.
- regime-conditional partial corr 미수행 (pre-2022 vs 2022+).
- log return numeraire (gold_USD) 만 — gold_SDR 도 partial corr 별도 추정 가능.
- ★nominal/real/BE 외에 명목 5Y (DFII5/T5YIE) 의 항등식 별도 미검증 (curve term structure).

## §H 미해결 의문
- breakeven 의 *국면 의존* 인플레 헤지 채널 (예: deflation 위험 강한 시기 BE 약화 + gold 추가 driver) — 본 검증의 평균 partial 만 측정. Markov-switching partial corr 별도 (H5 와 통합 가능).
- 정확한 Fisher 항등식 (DGS10 vs DFII10+T10YIE) 의 3 bp 차이 발원: TIPS 의 liquidity premium + intraday timing + minor rounding — Barsky-Summers level 관계의 noise 추가 처리?
- ★condition number 게이트 임계 (1e10 vs VIF 5) 의 mathematical 정합성: VIF=5 ↔ condition number ≈ 25 (대략). 본 시스템 게이트는 VIF<5 채택, condition number 보조.

---

## 결론
H6 = ★SUPPORTED. gold-BE partial = -0.054, gold-real partial = -0.291 → BE common-cause 매개 + real_rate 직접. Fisher 항등식 게이트의 절대 필요성 실증 (VIF 1.04 → 12996 if nominal 추가).

★main 의 옵션 (a) 채택 (BE force_include=4 외, 항등식 basis 외부 가드 pin) = 본 실측으로 직접 정당화.

★yaml 블록3 relationships: breakeven_10y↔gold 의 edge_type=common_cause, prior_sign=undetermined, prior_strength 약 (≈0.05), conditioning_set={real_rate_10y}, force_include=false.
