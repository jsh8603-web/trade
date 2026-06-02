---
title: "Cross / Regime 관계 Ledger — P1 실측 + P2 독립 audit verdict (재탐구 방지)"
tags: [study/wire, ledger, cross-asset, regime-conditional, audit-verdict]
date: 2026-06-01
scope: "top5 cross/regime 관계의 P1 실측 + P2 15축 독립 audit 결과 집결. 다음 리서치가 동일 탐구 반복 안 하도록 status·사유·근거·실측값 기록."
process: "P1 1차(a1aa7c1b top5) → ★P1 재작업 2분할(a03cf09f cross / a7d149b4 regime+crypto = 실측 완비·defensive 보충·crypto raw 재계산) → ★독립 P2 audit 2분할(a2c6af3b cross / a7c55f08 regime+crypto = 측정자와 **별도 감사관**, raw 재현·통과편향 차단) → 본 ledger 확정(P3). ★단계 정정(사용자 2026-06-01): P2a/P2b 는 audit 아닌 P1 재작업이었고, 독립 audit 은 별도 감사관 2명이 수행."
priority_rule: "규칙=핸드오프/plan/progress 우선, decisions=상세 참고. 본 ledger = CLAUDE.md '🗂️ 지표/관계 Ledger 기록 규칙' 4-state 준수."
status_legend: "adopted=배분 레이어 코드화 대상(activate) / candidate=후보(미검증·탐구대기) / rejected_provisional=보류(재평가 트리거 시 부활) / rejected_permanent=영구폐기(부활금지)"
---

# Cross / Regime 관계 Ledger

> ★핵심 목적: 다음 리서치가 **이미 한 탐구를 반복하지 않게** 한다. P1 실측 + P2 독립 audit(15축, raw 재계산) verdict 를 status·사유·근거·실측값[CI,n]으로 집결.
> ★최우선 framing(사용자 2026-06-01): adopted 관계는 **agent 개입 전 결정론적 배분 레이어**(RegimeClassifier→RegimeGlasso 학습→corr_prior→BL)에서 코드화. judge(bge/qwen)=그 이후 down-only 부차. "학습부터 전체 파이프라인" 적용.

## 1. Cross-asset 공분산 관계 (channel = 공유 factor)

| 관계(node_a↔node_b) | status | channel | 실측값[95%CI, n, p] | reason (P2 verdict) | 배분 wire 상태 | research_ref |
|---|---|---|---|---|---|---|
| eq_cyclical↔eq_intl | **adopted** | vol+dollar cross | r=+0.838 [.830,.845] n=6224 p<1e-300 | P2a confirm. large-n, hard-fail 0, sign-stable. VIX partial 제거 후도 +0.644 잔차 | SEED vol cell → corr_prior W roll-up (자동 off-diag). 둘 다 SLEEVE_AGG 매핑(us_stock←cyclical+defensive) | cross-and-regime-research C1, p2a-audit-recompute.py |
| eq_cyclical↔reit | **adopted** | vol cross | r=+0.686 [.672,.700] n=5450 p<1e-300 | P2a confirm. VIX partial 후 +0.459 잔차 | ★reit SLEEVE_AGG 미매핑 = 현 배분 무기여(정직라벨). 매핑 확장 시 활성 | C2, p2a |
| commodity↔xle_energy | **adopted** | oil cross | r=+0.650 [.633,.665] n=5109 p<1e-300 | P2a confirm. regime-stable(riskOFF+0.666/ON+0.635) | ★xle 별 unit SEED + SLEEVE_AGG 미매핑 게이트 | C4, p2a |
| gold↔commodity | **adopted** | dollar cross | r=+0.367 [.343,.391] n=5109 p=1.1e-162 | P2a confirm. 둘 다 dollar 음 노출 | ★배분 진입 O (gold·commodity 둘 다 SLEEVE_AGG 매핑). us_stock×commodity 0.44 기측정 | C5, p2a |
| gold↔eq_intl | **adopted(sign)** | dollar>vol net | r=+0.189 [.163,.214] n=5414 p=1.7e-44 | P2a confirm. net 양(dollar 채널 > vol 분기). magnitude 약 | ★eq_intl SLEEVE_AGG drop(R10) = 배분 직접 진입 X | C6, p2a |
| xle↔eq_cyclical | **adopted** | vol+oil cross | r=+0.639 [.625,.653] n=6899 p<1e-300 | P2a confirm (C9 proxy) | xle 미매핑 게이트 | C9 proxy, p2a |
| **defensive↔eq_cyclical** | **adopted** | vol cross | r=+0.697 [.685,.709] n=6899 p<1e-300 | ★P2a 신규 측정(P1 미측정분). defensive vol β=−0.660 강노출 | defensive=us_stock SLEEVE_AGG 일부(cyclical+defensive 0.5/0.5). vol cell 채우면 활성 | p2a 보충 |
| **defensive↔reit** | **adopted** | vol cross | r=+0.678 [.663,.692] n=5450 p<1e-300 | ★P2a 신규 측정 | reit 미매핑 게이트 | p2a 보충 |
| gold↔eq_cyclical | **adopted(sign, weak)** | dollar | r=+0.119 [.092,.145] n=5414 p=1.9e-18 | 관계 자체 약 양. ★단 "risk-off hedge" 가설은 **rejected**(아래 §3) | gold·defensive(us_stock) 약 연결 | C7, p2a |
| commodity financialization spike | **candidate** | regime(VIX>30 cross-sector) | ★미검증 (P1 object mismatch) | P2a: P1 이 commodity↔xle 페어만 봄, yaml `cross_sector_mean_corr_60d`(commodity 내부 섹터 평균상관) 미측정 → "reject" 부적격, UNTESTED | 측정 시 commodity 구성 섹터 시계열 fetch 필요 | C4 financialization, p2a |

## 2. Regime-conditional 관계

| 관계 | status | channel | 실측값[CI, n, p] | reason (P2 verdict) | 배분/judge 레이어 | research_ref |
|---|---|---|---|---|---|---|
| DGORDER_yoy→XLE (highInfl regime) | **adopted** | regime/forward (inflation clock) | IC=+0.423 [.161,.617] n=97 NW-t=3.83 p=0.0001 | P2b 충실 confirm. full +0.311 이미 유의 → 국면서 sharpen(정제, 생성 아님). m=40 Bonferroni α=0.00125 유일생존 + BH-FDR 생존. expanding-median PIT-safe | judge **L2 down-only refinement**(weight alpha tilt 아님). substrate=RegimeClassifier inflation 국면 | eq_us_cyclical regime-poc, p2b |
| crypto MVRV→fwd × (FGI×halving 20-cell) | **rejected_provisional** | regime (FGI×halving) | raw IC −0.65~−0.05 (★eff_n 전 cell 3.1~14.6 <30, distinct episode 2~3개) | ★독립 audit 확정 **INSUFFICIENT hard-fail 2축**: **C**(cell-label 강·약 뒤바뀜 — markup raw −0.065 ↔ yaml "−0.03 약" / post_18_24m raw −0.487 vs yaml −0.51/−0.61/−0.65 3중 불일치 + 점추정 박제) / **B**(eff_n<30 전 cell, n≥30 claim 무효). K축=완화("p 자체는 존재, **보고 누락+Bonferroni 미보정**"). e-CUSUM max_R 2.1e189=heuristic baseline_ic=0/sd=0.15 산물 spurious | ★배분/judge 진입 차단. **재평가 트리거=yaml 5건 정정**(label 강약·점추정 철회·per-cell p+Bonferroni·eff_n/episode 박제·e-CUSUM empirical baseline). 보류(이론·부호 일관성 살아있음, 영구폐기 아님) | crypto h1_mvrv.py, p2b+독립audit a7c55f08 |
| VIX regime split (자산별) | **candidate** | regime(VIX state) | (cross 의 vol factor 와 중복 위험) | P2b: 현 read-only 문서 단계 가드 OK. ★코드화 시 vol factor 와 별도 3번째 소비자로 wire 하면 **L축 이중계상 hard-fail**. SEED vol factor 와 1회 계상 합산 필수 | 코드화 게이트(L축 1회 계상 가드 박제 후) | cross-and-regime §2, p2b |

## 3. 기각 가설 (관계는 살아도 특정 *기능/라벨* 은 기각)

| 가설 | status | reason | 재평가 |
|---|---|---|---|
| gold = risk-off equity hedge (부의 공분산) | **rejected_provisional** | 독립 audit: tail(VIX>q99) gold↔eq_cyc +0.29(p=0.017, n=69)·gold↔eq_intl +0.31 = **패닉일수록 동조 강화**(panic-sell, gold H5 TENTATIVE 정합). clean hedge 아님 | gold decoupling regime(자체 monitor) 발동 시 재평가. 관계 자체(+0.12)는 adopted(§1) |
| gold vol(VIX) 노출 = β:=0 lock | **rejected_provisional** | ★독립 audit 신규: corr(gold ret, dVIX)=−0.0485 **NW-HAC p=0.077 비유의**. batch β −0.011[rej] 와 정합 | ★SEED vol cell **gold β:=0 lock**(O축 reject≠missing) — equity-vol pool β 상속 차단(gold −0.508 오염 root cause 방어). gold decoupling/safe-haven regime 발동 시 재평가 |

## 4. 종합 + 다음 (P4 codify 방향)

- ★**독립 P2 audit 확정**(측정자와 별도 감사관 2명, raw 재현, 통과편향 차단): cross **충실 CONFIRMED hard-fail 0** / regime DGORDER→XLE **confirm adopted** / crypto **INSUFFICIENT 보류**(B·C 2축 hard-fail) / financialization **UNTESTED**. 측정자 verdict 대체로 confirm + 정밀화 2건(gold β:=0 lock·crypto K축 "p 존재, 보고/보정 누락"으로 완화).
- **adopted 9건**(cross 8 + regime DGORDER 1) = P4 배분 레이어 corr_prior 코드화 대상. ★단 reit/eq_intl/xle 는 SLEEVE_AGG 미매핑 = 현 배분 무기여(정직라벨), 매핑 확장이 선결.
- **rejected_provisional 2건**(crypto 20-cell, gold hedge 가설) = 보류, 재평가 트리거 명시.
- **candidate 2건**(financialization, VIX regime split) = 측정/가드 후 재검.
- **L축 불변식**(★최우선 가드): VIX(vol) 공통인자는 corr_prior 의 SEED vol factor **1회만** 계상. cross-corr·VIX-regime 으로 추가 wire 금지(P2a/P2b 공통 적발).
- **P4 codify 경로**(progress-wire-impl.md P4): adopted cross → SEED vol/oil/dollar cell sign-only 채움(magnitude FREEZE, shadow OOS 게이트 후 magnitude) → `factor_betas_seed.py SEED_CELLS` + SLEEVE_AGG 매핑 확장 → `_ic_corr_prior` W roll-up 자동 off-diag. DGORDER→XLE = judge L2 lag_routing(W2).
- **crypto yaml 정정**(Phase W4, 게이트): cell-label·magnitude·eff_n·Bonferroni·점추정 박제 철회 = study yaml 작업(별도).

## 5. 향후 리서치 항목 (ledger 성격 아니나 배경 박제 — 재탐구 방지, 사용자 2026-06-01)

### 5.1 sleeve 신설 (reit/eq_intl/xle) — 자산 study 선행 필요
- **왜 화두가 됐나**: IC10 measured cross-corr 에서 reit/eq_intl/xle 가 VIX(risk-off) pool 에 강하게 묶이는 adopted 관계(eq_cyclical↔eq_intl +0.838·↔reit +0.686·commodity↔xle +0.650). 그러나 런타임 할당 차원 SLEEVES(us_stock/kr_stock/commodity/gold/bond/cash/coin)에 이 sleeve 들이 **부재** → SLEEVE_AGG 매핑 불가 → measured 됐으나 런타임 무기여(정직라벨). "넣으려면?"에서 sleeve 신설 화두 발생.
- **신설 시 선행 작업**: sleeve 추가 = portfolio 구성 변경. 해당 자산(reit/eq_intl/xle)의 지표 study(상관·국면·factor β·weight_rules) + 티커 인프라(`sleeve_returns SLEEVE_TICKERS`) + study yaml + 독립 audit(15축) 전부 선행 의무. ★defensive 는 us_stock 흡수(SLEEVE_AGG us_stock←cyclical+defensive)로 예외 — 이미 measured vol −0.63 반영.
- **게이트**: 사용자 방향 논의(portfolio 구성 = 설계 결정). 자율 범위 밖. **나중 리서치 큐**.
- **status**: 보류(cross 관계는 adopted 측정 완료, sleeve 진입은 신설 게이트 대기 — 재평가 트리거=사용자 portfolio 구성 확장 결정).

## 6. Factor 축 확장 — P1 실측 + P2 독립 opus audit (2026-06-02)
> series 공백 발굴(subagent afd5bb1) → ROI 선별(MOVE/A/FRA-OIS 3축, PMI·reit분리·외국인순매수·copper-gold·crypto-onchain 제외) → P1 실측(a656b5d5) → P2 독립 opus audit(a8f746b2, raw 재계산 ±0.005 일치, hard-fail 0). 잣대=배분 sleeve 실제 영향 + 일별 동적.

| factor | source | status | sign / sleeve | reason (P2 verdict) | 실측[CI, n] | codify |
|---|---|---|---|---|---|---|
| **MOVE** (국채 IV) | Yahoo `^MOVE` 2002-11~ (FRED 미존재) | ★**Y5 covariance-DROP** (marginal=confirmed) | (joint 무효) | marginal CONFIRMED(univariate 음). ★**covariance-incremental REJECTED**: Y5 통일 joint mv(VIX 동시통제) 시 전 sleeve β→0(t=0.0~2.2 잡음). VIX가 risk-off 분산 완전 흡수 | univariate us −0.22/gold −0.07 ↔ **joint ≈0** | ★**factor set 미포함**(Y5). univariate −0.21 박으면 VIX와 이중계상(L축) |
| **real** (DFII10 Δ) | FRED 2003~ | **adopted** | **gold−**(bond 매핑 부재) | 충실 CONFIRMED. Y5 joint 안정(gold −0.233 t=−11, univariate −0.249 대비 거의 불변). ★주식 양상관 OOS sign-flip→제외(재현됨) | gold −0.233[joint], n=4999 | ★**FACTOR_SERIES rate→real 교체 완료**(Y5, VIF 0.914 공선 회피). gold cell adopt |
| **breakeven** (T5YIE Δ) | FRED 2003~ | **adopted** | commod+ | Y5 joint +0.117(t=3.1 유의, univariate +0.33 → 약화하나 생존). p=0.0018>Bonferroni α/40 → structural | commod +0.117[joint] (univariate +0.33), n=4975 | ★**FACTOR_SERIES +breakeven(diff) 완료**(Y5). commod structural cell(James-Stein 강수축) |
| **slope** (T10Y2Y Δ=DGS10−DGS2) | FRED | ★**Y5 covariance-DROP** (marginal=candidate) | (joint 무효) | marginal 부분(univariate commod +0.13). ★**covariance-incremental REJECTED**: Y5 joint commod +0.015(t=1.2 비유의). MOVE와 동일 univariate-only attenuation | univariate commod +0.13 ↔ **joint +0.015** | ★**factor set 미포함**(Y5) |
| **funding** (SOFR−EFFR Δ) | FRED 2018~ | **rejected_provisional** | (uncond 무효) | 불충분. uncond Bonferroni 0생존. stress한정 us/kr +0.19 약신호 | <0.03 전 sleeve, n2037 | 차단. ★재평가 트리거=repo발작/QT 가속(distinct stress regime 누적)=IC9 부활 대상 |

### §6-Y5 reconcile (2026-06-02 — codify 완료, 외부자문 2모델 만장일치 수렴)
- ★**핵심 발견**: P2 audit 헤드라인 β(MOVE us −0.213·slope commod +0.119)는 **univariate**였다. factor 공분산 prior B·Λ·Bᵀ 는 **joint(multivariate) β** 가 정합(B=Cov(r,f)·Λ⁻¹) — univariate 박으면 VIX와 risk-off 채널 **이중계상**(L축 불변식 위반). univariate inflation (1+3ρ²)는 sleeve별로 달라 magnitude FREEZE/cov2corr 로도 못 씻음(상대 corr 왜곡, Claude 미니증명).
- ★**re-scope framing**(번복 아님): audit verdict = **marginal association**(유효, 위 표 보존) / **covariance-incremental** = 별도 더 엄격 게이트. MOVE/slope = marginal 통과 / covariance-incremental 실패(VIX 조건부 redundant). FWL: joint β = MOVE⊥ 잔차계수, VIF 1.26 → MOVE⊥ 분산 79% 보존 = 진짜 partialling(spec artifact 아님).
- ★**채택 게이트 업그레이드**(governance): covariance-prior factor 는 univariate screen 만으로 부족 → **joint incremental 통과 필수**(기존 factor set 조건부 생존 + cross-sleeve 공분산 증분). 향후 factor 채택 시 적용.
- **재평가 트리거(MOVE/slope 부활)**: ① bond sleeve 가 corr_prior 소비 대상에 편입(현 eye 독립) → MOVE=채권 IV 로 bond 전용 vol factor 가치 발생(option C) ② regime-conditional 분리(2022 rate-stress vs 2020 equity-stress 에서 MOVE↔VIX 결합 국면의존) — 현 corr_prior 3 sleeve(equity/commod/gold)는 VIX-dominated 라 full-sample drop.
- **codify 결과**(measure=batch-std-beta-9factor.json, n≈5000, MAX VIF 1.26): FACTORS 6→**7**(real/dollar/oil/credit/vol/breakeven/fx). golden us×commodity 0.2951→**0.2880** / us×gold 0.249→**0.2721**. opt-in off byte-identical ✓ + self-test/회귀 통과 ✓.
- **L축 가드**(★유지): rate 공통인자(real)는 1회 계상. slope drop 으로 bond 중복 우려 자동 해소.
