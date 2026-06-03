---
tags: [type/consult-decision, domain/inv, topic/m4-factor-integration, phase/M4]
date: 2026-05-30
note: 자문 3R(gemini-web Pro + claude-web Opus 4.8 병렬) 완전 수렴 — M4 거시-종목 factor 통합 설계. cross-sleeve factor cov(B·Λ·Bᵀ)에 검증된 dollar driver 를 점추정 박제 없이 통합하는 7대 원칙 + M4/M5 범위 분할.
raw_consult: [~/.claude/.gemini-web-last.md, ~/.claude/.claude-web-basic-last.md]
---

# CONSULT-DECISIONS-M4 — 거시-종목 factor 통합 (자문 3R 수렴)

> gemini-web(Gemini Pro) + claude-web(Opus 4.8) 병렬 3라운드, 완전 수렴. Claude 가 일부 더 정밀한 교정 제공, Gemini 와 충돌 없음.
> 검증 SSOT = `study-research/macro/m4-collection.md`(5/6 sleeve verdict). 구현 대상 = `core/study/system_priors.py::factor_implied_cross_cov`(B·Λ·Bᵀ, production 호출부 0개 상태).

## 맥락
M3 = 8 sleeve 가 각자 거시연관 실데이터 검증. 5/6 verdict 확보: **dollar = cross-validated 1차 driver**(gold·eq_us_cyclical·eq_intl·reit·commodity 전부 robust 유의), rate 는 reit(VNQ −3.82)·gold 만 직접. M4 = 검증된 driver 를 거시 레이어(cross-sleeve factor cov)에 반영. ⛔점추정 회귀계수를 covariance prior 로 박제 금지(넓은 CI·다중검정 미보정).

## ★확정 7대 원칙

### 1. M4/M5 범위 분할 + shadow 격리
- **M4** = (a) `factor_betas_seed` 테이블 + (b) Λ(팩터 공분산) 추정 스크립트 + (c) **격리 shadow validation**(B·Λ·Bᵀ 계산·로깅만, 어떤 결정에도 미반영).
- **M5** = risk gate opt-in wiring(deadband+clamp down-only).
- ⛔ **"opt-in off → byte-identical"은 자동이 아니다**(Claude 교정): shadow 가 공유 RNG·cov 캐시·FP 연산순서·파일 IO 타이밍을 건드리면 off 여도 출력 미세 drift. → **shadow on/off diff=0 을 회귀로 박제**하거나 shadow 를 공유 상태에 write 없는 별도 read-only consumer 로 격리.

### 2. 검증관 3-tier → confidence 매핑 (★Claude 2곳 교정)
James-Stein shrinkage weight `w = τ_f²/(τ_f²+SE_{i,f}²)`, `b = w·β̂ + (1−w)·β_pool`, `τ̂² = max(0, S²_between − mean(SE²))`(MoM).
- **validated_alpha** → `w` 그대로(⛔강제 w=1 금지 — JS 최적성 깨고 과적합 재유입, 약한 ceiling 만).
- **structural_prior** → `w ≤ w_max ≈ 0.2~0.3` 캡(pool 강수축).
- **reject** → ⛔β=0 아님. 그 셀 β̂ 은 **pool 계산에서만 제외**(나쁜 셀의 β_pool 오염 방지), 노출은 `b = β_pool, w = 0` 부여 → Q2 게이트 사각지대(co-movement 증발) 회피. 완전 드롭은 구조적 미적용 팩터만.
- Bonferroni 생존 = 위에 곱하는 게이트 `w *= 1{|t|>t_crit}` 또는 sigmoid(|t|−t_crit).

### 3. dollar β 크기 보존 (sign-only 기각)
게이트가 집중도를 MRC(component VaR `(Σw)_i·w_i / wᵀΣw`)로 재므로 β 크기차(−0.6 vs −0.3)가 실질 영향(공분산 기여 = β_i·β_j·σ²). false precision 우려는 SE 가 크기차를 삼킬 때만 valid 하고, 해결은 크기 폐기가 아니라 confidence shrink(원칙 2). dollar 4×rate 상대강도는 수축 후에도 보존.

### 4. idio conservation form
`d_i = max(σ²_{i,total} − b_iᵀΛb_i, floor_i)`, `floor_i = κ·σ²_{i,total}`, κ≈0.1~0.2. σ²_total = 실현수익 EWMA 직접. 수축으로 b 작아지면 factor-explained 줄고 residual=idio 자동 증가(Barra/Axioma specific-variance 방식). b 에 `|β|` max clamp(단일 노이즈 loading 이 structured 분산 폭발 방지).

### 5. Λ(팩터 공분산) 추정
factor return 혁신으로 변환: **DGS10·HY OAS = Δbp**(near-unit-root 상태변수), **dollar(DTWEXBGS)·oil(WTI) = Δlog**. ADF+KPSS 둘 다(차분 정상 & 레벨 비정상 양쪽 확인, 단 모델링은 이론 우선). 비동기성(아시아·commodity sleeve 섞임 → contemporaneous 과소) = overlapping multi-day 또는 Newey-West 보정.
- **gate 용 Λ** = `EWMA(half-life 60~90d)` + **stress correlation floor** `ρ_ij ← max(ρ_ij^EWMA, ρ_ij^stress)`(상향 클램프만, 비대칭 = down-only 일관) → **Higham nearest-correlation PSD 재투영 필수**.
- **static 장기 Λ** = 나중 BL/Π(belief, 1차모멘트) 입력으로 보류(안정성 > 반응성). moment 분리(원칙 7)와 매핑.

### 6. shadow 합격 metric (사전 고정)
- **1차(합격판정)** = bias statistic on decision portfolios: 테스트 포트(dollar-mimicking·cross-sleeve 집중)의 `√(wᵀΣ_model w)` 대비 OOS 실현 vol 비, 12M rolling [0.9,1.1] 밴드(Barra B-stat — 게이트가 실제 소비하는 양 검증).
- **2차(구조)** = 지배 eigenvector cosine alignment `|v₁·v₁^OOS| > 0.9`(dollar dominance 직접 검정 — 안 맞으면 dominance 스토리 틀린 것).
- Frobenius / corr-of-corr = monitor 만(scale-dominated / decision-weight 없음, 합격선 부적합).

### 7. τ pooling + 짧은 히스토리 stress
- **group = a priori 경제 자산군**(⛔dollar-sensitivity 행태로 묶으면 순환참조 = endogenous, between-group 정밀도 가짜 부풀음). asset-class 를 경제 역할로 정련: **gold/precious 는 commodity 아니라 real-rate/currency 군**. commodity sub 4개는 sleeve→grand **2층**(3층 과설계, df 부족), 굳이면 precious vs (energy+industrial+agri) 2그룹까지.
- **stress floor 짧은 히스토리 방어**: sleeve 5년(2021-2026, 2008 없음)에 갇히지 말 것. **장기 팩터(rate/dollar/oil 은 2008+ 데이터 보유)로 Σ_stress = bᵀΛ_stress b 유도** ⊕ 보수 사전값의 max. exceedance 상관(Pearson 보다 floor 적합). ⛔0.7 일괄 박제는 거침(gold 위기 음상관 분산효과 오페널티).

## ★two-layer 분업 (이중계상 차단)
dollar 는 **모멘트당 1회**:
- **방향(1차모멘트)** = Layer A belief(regime tag·BL view). static 구조.
- **동조위험(2차모멘트)** = risk gate cov(B·Λ·Bᵀ). adaptive 보수.
- ⛔단방향: cov 는 절대 view 로 환류 금지(factor cov→BL Σ→Π=δΣw 누수가 유일 이중계상 경로).
- ⛔**Layer B(종목 매수·매도)에서 dollar 재진입 금지**(삼중계상) — macro dollar 는 sleeve 배분(A)에서 소화, B 는 받은 budget 위 idio 신호만.

## 잔여 불확실성 2 (구현 시 결정)
1. τ_f² MoM 이 sleeve 적으면 불안정 → a priori 2그룹 또는 grand 직 pool(commodity 4개 = 2층).
2. ρ_stress 출처 = 장기 프록시/팩터유도 ⊕ 보수 사전값의 max(둘 다 floor). shadow 에서 floor 가 실제 stress OOS 추종하는지 별도 검증 윈도우.

## 구현 매핑
| 원칙 | 코드 대상 |
|---|---|
| seed 셀 (β̂,SE,t,n,Bonf,tier) | 신규 `core/study/factor_betas_seed.py` |
| James-Stein + idio conservation | seed → betas/idio 빌더 함수 |
| Λ 추정 (Δbp/Δlog, EWMA+stress floor, Higham) | 신규 Λ 추정 스크립트 |
| shadow validation (bias-stat, eigenvector) | 신규 shadow 스크립트(격리, 로깅만) |
| B·Λ·Bᵀ 합성 | 기존 `system_priors.factor_implied_cross_cov`(재사용) |
| risk gate wiring | M5(opt-in, 본 M4 범위 밖) |
