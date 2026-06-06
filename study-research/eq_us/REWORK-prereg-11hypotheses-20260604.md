---
tags: [type/pre-registration, domain/equity-us, phase/hypothesis-verification]
date: 2026-06-04
purpose: 미국 3-sleeve 다변량 조건부 가설 11종 pre-registration 카드. ★데이터 접촉 전 부호·게이트·family 경계 박제 (garden-of-forking-paths 차단). 검증 dispatch 의 SSOT.
source: .consult-us-hypothesis-collection-results.md (R1 강수렴 curated 11)
status: VERIFIED+OVERKILL-CORRECTED (2026-06-04) — 11 가설 전수 검증 후 ★over-kill 정정. 최종 = DEF-2(CONFIRM, rank-FM size-valid 복원) + CYC-1(TENTATIVE theory-pinned) + DEF-1(TENTATIVE PW). §over-kill 최종 정정 참조 (이전 §독립검증/§CYC전수의 "재-z artifact 격하" 는 discovery/kill 척도 불일치 = forking-paths 로 무효화).
fdr_family: us_equity_2way_v1
constraint: 합성 0 (yfinance/EDGAR/FRED PIT) · go-live 미접촉 · 점추정 prior 박제 금지
---

# 미국 3-sleeve 조건부 가설 11종 — Pre-Registration 카드

> ★**박제 시점 = 데이터 접촉 전**. predicted_sign 은 one-sided pre-commit. wrong-sign significant = 자동 폐기 (DEF-1 PW-tension 예외만 manual review).
> ★단일 FDR family = `us_equity_2way_v1` (11 가설 primary interaction test 전부 하나의 alpha budget). BY-FDR + M_eff(Li-Ji eigenvalue) threshold.
> ★검증 후 갱신 = `decision` 필드만 (CONFIRM/TENTATIVE/UNDERPOWERED/REJECT). spec/sign/floor 은 invariant.

## ★공통 계약 (11 카드 전부 적용)

```yaml
estimation: full-panel cross-sectional IC (월별 rank-IC), within-sub-sector demean (sector-neutral z)
primary_stat: fixed-b t (Kiefer-Vogelsang 2005) + wild-cluster bootstrap (B≥9999)
size_validity: effective_n = n/(1+2Σρ_k) 선행 산출 → fixed-b CV 적용 (small-block NW-HAC asymptotic 금지)
neff_gate: effective_n < neff_floor → ★"UNDERPOWERED" 분리 라벨 (REJECT 아님), t 보기 전 판정
fdr: 단일 family us_equity_2way_v1, Benjamini-Yekutieli, M_eff = Li-Ji eigenvalue(신호 상관행렬)
incremental: interaction 항은 main effect 둘 + 기존 confirmed(net_issuance) FWL 직교 후 incremental 양 (셋 다 통과해야 생존)
gatekeeping: Goeman-Solari 계층 — main → 2-way → (Tier2)regime-slope, 부모 통과 없이 자식 budget 금지
oos: e-CUSUM 누적(peeking 정직) + 2022-2026 hold-out lock-box (탐색 2010-2021만)
ledger: 매 가설 결과 = candidate-ledger.md 박제 (채택/UNDERPOWERED/REJECT + 사유)
```

---

## us_cyclical (peak-EPS trap 전담) — CYC-1 ~ CYC-6

### CYC-1 ★ (ROI #1)
```yaml
id: CYC-1
sleeve: us_cyclical
spec: EV/EBITDA(z, 저=cheap) × gross_profitability(z, 고), 2-way cross-sectional interaction
mechanism: Novy-Marx "other side of value" — cheap-junk=trap / cheap-quality=진짜 value. peak-EPS robust(book/EBITDA 분모)로 EPS-trap 필터
predicted_sign: +1   # one-sided (cheap×quality → positive forward IC)
tier: 1
neff_floor: 30
incremental_req: ⊥{ev_ebitda_main, gross_prof_main, net_issuance}
decision: PENDING
```

### CYC-2
```yaml
id: CYC-2
sleeve: us_cyclical
spec: PER-cheapness − (PBR·sales)-cheapness divergence (가공 single signal)
mechanism: peak-EPS trap 직접 측정 — PER만 싸고 PBR/PS 안 싸면 E가 정점에 부푼 것 (분모 E 과대)
predicted_sign: -1   # divergence 클수록(=PER만 싼 trap) forward 음
tier: 1
neff_floor: 30
incremental_req: ⊥{ep_yield_main, pbr_main, sales_yield_main}
decision: PENDING
```

### CYC-3 ★ (ROI #3)
```yaml
id: CYC-3
sleeve: us_cyclical
spec: op_profitability(z, 고) × asset_growth(z, 저), 2-way cross-sectional interaction
mechanism: q-factor(Hou-Xue-Zhang 2015) 순수형. ★단독 REJECTED asset_growth 를 profitability 조건부 부활 테스트
predicted_sign: +1   # high-prof × low-investment → positive
tier: 1
neff_floor: 30
incremental_req: ⊥{op_prof_main, asset_growth_main, net_issuance}
revival_test: true   # asset_growth 단독 decay 였음 — 조건부 부활 여부가 핵심
decision: PENDING
```

### CYC-4
```yaml
id: CYC-4
sleeve: us_cyclical
spec: ep_yield(z, 고) × residual_mom(12-1 sector·beta orth, +), 2-way cross-sectional interaction
mechanism: AMP value×momentum — cheap+turn 시작 = falling-knife 회피, mom=timing filter
predicted_sign: +1
tier: 1
neff_floor: 30
incremental_req: ⊥{ep_yield_main, residual_mom_main}
decision: PENDING
```

### CYC-5
```yaml
id: CYC-5
sleeve: us_cyclical
spec: ep_yield(z, 고) × idio_vol(z, 저), 2-way cross-sectional interaction
mechanism: distress filter — high-vol cheap=lottery/distress trap, low-vol cheap=진짜 value
predicted_sign: +1
tier: 1
neff_floor: 30
incremental_req: ⊥{ep_yield_main, idio_vol_main}
decision: PENDING
```

### CYC-6 (Tier 2, gatekept)
```yaml
id: CYC-6
sleeve: us_cyclical
spec: [capex_z × ep_yield] IC_t ~ Δbaa_aaa (연속 regime 1-slope, HAC interaction)
mechanism: ★§7 예시(불황 저PER 고capex)의 size-valid 버전. credit spread 확대(불황) 시 cheap·high-capex outperform
predicted_sign: +1   # Δbaa_aaa(스프레드 확대) → interaction IC 증가
tier: 2
neff_floor: 30
gatekeeper: capex×ep_yield 2-way (CYC-계열) 먼저 생존해야 budget 부여
incremental_req: slope ⊥ unconditional IC level
decision: PENDING
```

---

## us_defensive (rate-duration, net_issuance·anti-value 위) — DEF-1 ~ DEF-5

### DEF-1 ★ (ROI #2)
```yaml
id: DEF-1
sleeve: us_defensive
spec: net_issuance × ep_yield, 2-way cross-sectional interaction
mechanism: ★확인된 net_issuance PARTIAL_CONFIRMED 확장 — buyback-aversion 이 valuation-state 의존인지. 비쌀 때(low ep_yield) anti-issuance 강 가설
predicted_sign: +1   # AMP 방향 prior (비쌀수록 buyback-aversion penalty 강화)
two_sided_review: true   # ★PW(Pontiff-Woodgate) tension — wrong-sign = PW-consistent reversal, 자동폐기 아닌 manual review
tier: 1
neff_floor: 30
incremental_req: ⊥{net_issuance_main(confirmed), ep_yield_main}
base_status: net_issuance 단독 = PARTIAL_CONFIRMED (IC+0.082, ⊥ep +0.084 t3.71, raw_p 3e-05) → marginal risk 최저
decision: PENDING
```

### DEF-2
```yaml
id: DEF-2
sleeve: us_defensive
spec: dividend_yield(z, 고) × op_profitability(z, 고), 2-way cross-sectional interaction
mechanism: yield-trap 분리 — 고DY×저quality=배당컷 trap, 고DY×고quality=sustainable covered yield
predicted_sign: +1   # quality 가 DY 를 positive 로 moderate
tier: 1
neff_floor: 30
incremental_req: ⊥{dividend_yield_main, op_prof_main}
decision: PENDING
```

### DEF-3
```yaml
id: DEF-3
sleeve: us_defensive
spec: earnings_cv(z, 저) × vol_60(z, 저), 2-way cross-sectional interaction
mechanism: bond-proxy stability — 두 stability proxy 교집합으로 측정오차 감소. asset_stable 본질=cashflow 안정
predicted_sign: +1
tier: 1
neff_floor: 30
incremental_req: ⊥{earnings_cv_main, vol_60_main}
m_eff_note: earnings_cv·vol_60 near-duplicate 가능 → M_eff Li-Ji 중복 제거 확인
decision: PENDING
```

### DEF-4 (Tier 2, gatekept)
```yaml
id: DEF-4
sleeve: us_defensive
spec: ep_yield IC_t ~ ΔDFII10 (연속 regime 1-slope, HAC interaction)
mechanism: duration-adjusted value — defensive long-duration, real_rate 하락서 cheap outperform. anti-value puzzle 을 rate-state 분해
predicted_sign: -1   # ΔDFII10(금리상승) → ep_yield IC 하락 (=금리하락서 cheap +)
tier: 2
neff_floor: 30
gatekeeper: ep_yield main(anti-value TENTATIVE) 방향 확인 후 slope budget
incremental_req: slope ⊥ unconditional ep_yield IC level
decision: PENDING
```

### DEF-5
```yaml
id: DEF-5
sleeve: us_defensive
spec: ep_yield(z) × gross_profitability(z, 고), 2-way cross-sectional interaction
mechanism: anti-value 원인 진단 — cheap·low-quality 가 anti-value(음) 만드나, cheap·high-quality 는 정상(양)인가
predicted_sign: +1   # quality 가 anti-value attenuate (음→0/양)
tier: 1
neff_floor: 30
incremental_req: ⊥{ep_yield_main, gross_prof_main}
diagnostic: true   # defensive anti-value puzzle 의 quality-decomposition 진단
decision: PENDING
```

---

## us_mega_tech
```yaml
status: NO_CROSS_SECTION   # n≈8~11 → cross-sectional interaction 불가
verdict: exposure overlay (real_rate duration 노출, alpha sleeve 승격 ⛔)
# ★표현 정정 (2026-06-04 자문 수렴, 점추정 박제 금지): "alpha=0 확정" 아님 →
#   "N=11 검출불능(상호상관 高 → 독립 bet ~3-4) + 무료 forward EPS = PIT 불가(yfinance snapshot-only=look-ahead)
#    → 현 데이터·제약 하 cross-sectional alpha 탐색 종료. exposure overlay 유지. 유료 vintage consensus(IBES/Zacks) 확보 시에만 재개."
#   absence of evidence ≠ evidence of absence. alpha CI 너무 넓어 0 기각 불가 = 점추정 박제 X.
low_priority_note: real_rate β 시변성 ~ VIX state = hedge ratio 입력(risk-mgmt), 신호 아님
```

---

## ★검증 dispatch 계획 (사용자 지시: Top5 아닌 전체 11)

| sleeve | 가설 | 검증 주체 | 우선 |
|---|---|---|---|
| us_cyclical | CYC-1~6 (6) | us-cyclical teammate | CYC-1 → CYC-3 → CYC-2 → CYC-4 → CYC-5 → CYC-6(gatekept) |
| us_defensive | DEF-1~5 (5) | us-defensive teammate | DEF-1 → DEF-5 → DEF-2 → DEF-3 → DEF-4(gatekept) |

- ★N 적은 subset = 단일 FDR family 내 exhaustive OK (사용자 "N 적은건 다해봐도 된다").
- 11 가설 전부 1개 family budget → BY-FDR M_eff threshold 후 생존 판정.
- 사후 안전장치 8: 부호 one-sided pre-commit / n_eff hard gate / Goeman-Solari gatekeeping / FWL incremental / e-process OOS / placebo factor 1~2 / Harvey-Liu haircut / 2022-26 hold-out.
- ★결과 = candidate-ledger.md 박제 + progress BW8 + 본 카드 decision 필드 갱신.

---

## ★검증 결과 (2026-06-04, 전수 11 가설)

> 방법: cross-sectional 2-way interaction (raw IC + ★FWL incremental IC, ⊥main들) / Tier2=연속 slope. fixed-b CV(KV) + wild-cluster B=9999 + n_eff(floor30). 단일 FDR family `us_equity_2way_v1` BY q=0.10 (m=11 보수적, M_eff<11이면 완화). one-sided pre-commit: wrong-sign 유의=부호탈락(추격금지, HARKing 방지). 실행=team-lead 직접(teammate echo-stall unblock). 산출 json: cyclical `_b2_cyclical_interactions_results.json` / defensive `_b2_defensive_interactions_results.json`.
> 데이터: cyclical 2015-01~2026-05 60종(~137mo) / defensive 2010-01~2026-05 48종(185mo). H=12M.

| id | incr/slope IC | wild p | 부호 | BY | decision |
|---|---|---|---|---|---|
| **DEF-2** dividend_yield(고)×op_prof(고) | +0.065 t3.43 | **0.0005** | OK | ★생존(r1) | **CONFIRM** — yield-trap 분리 입증(고DY×고quality=sustainable covered yield, incremental+size-valid) |
| **DEF-1** net_issuance×ep_yield | −0.076 t−3.01 | **0.0055** | X→two_sided | ★생존(r2) | **TENTATIVE** — 유의·incremental·⊥{net_issuance confirmed, ep} but ★PW방향(발행페널티 cheap 집중)=AMP prior(+1)와 반대. two_sided_review 예외=자동폐기 아닌 manual review. 뒤집은 부호 신규 pre-reg+OOS 필요 |
| CYC-3 op_prof(고)×asset_growth(저) | −0.039 t−2.62 | 0.013 | X(pred+) | 부호탈락 | **REJECT(wrong-sign)** — 유의하나 역부호. 경제적=고수익·저투자=사이클정점 reversal→하락. 추격금지(HARKing), flip-sign 신규 pre-reg 후보 |
| CYC-4 ep_yield×residual_mom | −0.048 t−2.25 | 0.038 | X(pred+) | 부호탈락 | **REJECT(wrong-sign)** — cheap+momentum=정점 reversal 가능. 동상 |
| DEF-3 earnings_cv(저)×vol_60(저) | raw+0.048 p0.006 / incr+0.029 | 0.110 | OK | 미생존 | **NOT_INCREMENTAL** — raw size-valid이나 incr 소멸=두 stability proxy 중복(M_eff near-dup 예측 적중). main 각각이 이미 포착 |
| CYC-5 ep_yield×idio_vol(저) | −0.026 | 0.174 | 혼재 | 미생존 | **NULL** |
| DEF-5 ep_yield×gross_prof | −0.014 | 0.591 | X | 미생존 | **NULL** — anti-value의 quality-decomposition 무 |
| CYC-1 ev_ebitda(저)×gross_prof(고) | +0.019 | 0.680 | OK | 미생존 | **NULL** — Novy-Marx value×quality 방향 맞으나 비유의 |
| CYC-6 [capex×ep_yield]~Δbaa (Tier2) | slope−0.076 t−0.51 | 0.649 | — | 미생존 | **NULL** — capex EDGAR fetch 성공(2way+slope 둘다 n.s.) |
| DEF-4 ep_yield~Δreal_rate (Tier2) | slope+0.015 t0.27 | 0.792 | X(pred−) | 미생존 | **NULL** — anti-value의 rate-state 의존 없음 |
| CYC-2 PER-cheap divergence | raw−0.035 p0.15 / incr+0.005 | 0.881 | incr소멸 | 미생존 | **NULL** — peak-EPS divergence raw 약신호이나 incr 소멸 |

### ★종합 결론
1. **11 가설 中 BY 생존 = DEF-2(CONFIRM) + DEF-1(TENTATIVE) 2개**. cyclical interaction 6개 = 전부 null 또는 wrong-sign-reject (★value pbr/ev[#7 CONFIRM] 위 incremental factor×factor 0). defensive = DEF-2 신규 발견 + DEF-1 reversal.
2. **DEF-2 = 사용자 "지표간 관점(capex 높은데 PER 높을때 산다 류)"의 정당성 입증 사례** — 단일 dividend_yield(yield-trap 혼재)가 op_prof 조건부로 sustainable yield 분리 = factor×factor 가 단일보다 나은 실증.
3. **DEF-1 = breadth net_issuance(PARTIAL_CONFIRMED) 의 valuation-state 의존성 확인** — 단 PW방향(AMP prior 반대). 정직 TENTATIVE.
4. **CYC-3/4 wrong-sign 유의 = noise 아닌 신호(사이클정점 reversal)지만 사전박제 부호 위반→추격금지**. flip-sign 신규 가설은 cycle 추가 진행 시 후보(별 pre-reg+OOS).
5. ⚠️ M_eff=m_raw 미축소 구현 점검 의제(#7 동일) — 단 보수적 m=11 BY 에서도 DEF-2/DEF-1 생존이라 결론 불변.

### 사후 안전장치 잔여 (생존 2개 DEF-1/DEF-2 한정 후속)
- e-process OOS (2022-2026 hold-out) / placebo factor / Harvey-Liu haircut / turnover Net-alpha = G-C 재audit(BW7) 또는 별 cycle.

---

## ★split-sample 견고성 (2026-06-04, OOS 게이트 마감)

> pre-reg 가 약속한 2022-26 OOS 가 interaction full-sample run 에서 누락 → 마감. ★정직: full-sample 부호 旣관측 = "pristine pre-reg OOS" 아닌 **split-sample 방향지속성/견고성**(in-sample ≤2021-12 / OOS 2022-01~, H=12M). 유의 4개(DEF-2/DEF-1/CYC-3/CYC-4) 한정. json: `_b2_cyc_oos_results.json` / `_b2_def_oos_results.json`.

| 가설 | in-sample IC (wildP) | OOS IC (wildP) | 방향지속 | 견고성 등급 |
|---|---|---|---|---|
| **DEF-2** (+) | +0.053 fb_sig p0.019 | +0.106 fb_sig p0.013 | ✅ | ★★★ **robust CONFIRM** (양분 둘 다 fixed-b 유의, 정방향) |
| **DEF-1** (− PW) | −0.065 p0.042 | −0.112 fb_sig p0.005 | ✅ | ★★ **robust PW-reversal** (양분 둘 다 음=PW, OOS 유의). pred(+)와 반대지만 신호 진짜·지속 |
| **CYC-3** (− rev) | −0.038 p0.062 | −0.042 p0.084 | ✅ | ★★ **지속 reversal** (양분 부호+크기 안정, marginal). flip-sign 강후보 |
| CYC-4 (− rev) | −0.032 p0.253 약 | −0.066 p0.088 | ✅(부호) | ★ **구간의존** (in-sample 약, OOS 주도). flip-sign 약후보 |

### ★flip-sign register (wrong-sign 유의 → 추격금지 but 낭비방지)
> one-sided 사전박제 부호 위반(CYC-3/4)은 in-sample 발견으로 추격 금지(HARKing). 단 split-sample 안정=진짜 신호 가능 → **뒤집은 부호 신규 pre-reg 카드로 박제 + pristine OOS(차기 data vintage / 신규 종목·기간)에서만 1회 검증**. 본 split 은 견고성 진단일 뿐 확정 아님.

```yaml
# flip-register (차기 cycle pristine OOS 대상, 데이터 旣관측이라 현 vintage 확정 금지)
- id: CYC-3-flip
  spec: op_profitability(고) × asset_growth(저), predicted_sign: -1   # 뒤집음
  mechanism: 사이클 정점 reversal — 고수익·저투자 = late-cycle peak, 향후 mean-revert 하락
  evidence_insample: incr IC −0.038(p0.06) / OOS −0.042(p0.08), 방향+크기 split 안정 (★강후보)
  gate: 차기 vintage pristine OOS 1-shot + placebo + Harvey-Liu. 현 vintage 확정 ⛔
- id: CYC-4-flip
  spec: ep_yield(고) × residual_mom, predicted_sign: -1
  mechanism: cheap+momentum = 이미 반등한 정점, reversal 하락
  evidence_insample: in-sample 약(p0.25) OOS 주도(p0.09) = 구간의존 (약후보)
  gate: 동상. 우선순위 CYC-3 < CYC-4
- id: DEF-1-PW
  spec: net_issuance × ep_yield, predicted_sign: -1   # PW 방향 확정 prior 로 재등록
  mechanism: 발행 페널티가 cheap 종목에 집중(Pontiff-Woodgate value 교호). AMP 아님
  evidence: 양분 둘 다 음 + OOS fixed-b 유의 = robust. ★two_sided 였으므로 HARKing 아님, PW 로 prior 확정 가능
  status: TENTATIVE → PW-direction 으로 격상 후보 (pristine OOS 후 CONFIRM)
```

---

## ★자문 검증 (2채널 수렴) + curvature confound 결정검정 (2026-06-04)

> /gemini-web(Pro) + /claude-web(Opus) 병렬 R1 강수렴. brief=`.consult-us-methodology-validation-brief.md`. raw=`~/.claude/.gemini-web-last.md`/`.claude-web-basic-last.md` tail.

### 양채널 수렴 (방법론 판정)
1. **a2 wild-cluster intercept = valid** / **a3 M_eff raw m=11 = 보수적이라 OK**(Li-Ji 추가시 이중보정 위험) / **a4 n_eff floor30 ≠ fixed-b 와 모순**(floor=power gate, fixed-b=size; OOS n_eff15서 fixed-b sig=효과가 넓힌 bar 돌파, 모순아님. 단 floor=cliff 아닌 gradient).
2. **★가장 큰 결함(Claude, 양채널 정합)=own-curvature confound**: z1·z2 는 선형직교화 후에도 z1²·z2² 와 상관 → 선형 main 에만 직교화하면 단일인자 곡률을 교호로 흡수. 생존 DEF-2/DEF-1 직격. ★결정검정=basis 에 z²추가.
3. **FWL 선형직교화+Spearman rank = 불일치**(robustness 진단일뿐 "순수 교호계수" 아님) → FM 전체회귀(fwd~z1+z2+z1·z2) 병기 권고.
4. **b spec-modulation**: CYC-1 p0.68 = 약신호 아니라 **NULL**(정보~0). cherry-pick=p-hacking 금지. 합법=① pre-reg grid 전수+단일FDR ② specification curve/multiverse joint inference(승자줍기 아닌 증거체 vs null) ③ 이론고정 1발+pristine OOS. ★**메타경고=wrong-sign엔 엄격 right-sign-null엔 관대=bias amplifier, 동일 엄격도**.
5. **c wrong-sign REJECT+flip+pristine OOS=옳음**. CYC-3 reversal=★thin-demeaning artifact 의심(60종/12sub=sub당 ~5종, idio 노이즈 지배 spurious sign-flip). "q-factor 반증" billing 금지, 가설생성용만.
6. **d DEF-1 CONFIRM 시기상조, TENTATIVE 유지** + two_sided_review commit 시점 정직기록 + VIF/공선성 점검.

### ★curvature confound 결정검정 결과 (json `_b2_def_curvature_results.json`)
| 가설 | incr IC 선형 | incr IC +곡률 | FM coef 선형 | FM coef +곡률 | VIF | ★판정 |
|---|---|---|---|---|---|---|
| **DEF-2** div_yield×op_prof | +0.065 sig p0.0005 | +0.059 **sig** p0.007 | +0.012 **sig** t3.23 | +0.020 **sig** t3.54 | 1.3/2.4 | ★**REAL CONFIRM** — 곡률통제+FM 전부 생존, 저VIF |
| **DEF-1** net_iss×ep_yield | −0.076 sig p0.0055 | −0.085 sig p0.0001 | **−0.0095 t−1.66 비유의** | −0.006 t−0.87 비유의 | 1.4/1.9 | ★**WEAK/rank-artifact 격하** — rank-IC만 유의, FM 선형계수 비유의 |

### ★verdict 갱신 (자문 반영)
- **DEF-2 = CONFIRM 확정**(곡률+FM 이중통제 생존). 11 가설 中 유일 robust 발견.
- **DEF-1 = TENTATIVE → WEAK_RANK_ARTIFACT 격하**. Spearman rank-IC 유의가 FM 선형계수서 사라짐(t−1.66) = 자문 경고 "FWL+rank 불일치" 실증. PW-reversal 은 rank척도/꼬리 주도 가능성. ★net_issuance **단독** PARTIAL_CONFIRMED 는 유지(별 검정), 단 ep_yield 와의 교호는 미입증.
- CYC-3/4 = REJECT 유지(+thin-demeaning artifact 의심 가중, flip 우선순위 하향).
- **방법론 codify 반영(차기)**: ① interaction primary=FM 전체회귀 계수(rank-IC 병기, 불일치시 비선형 진단) ② 직교화 basis 에 z² 곡률 항 의무 ③ n_eff floor=gradient(fixed-b 가 size 담당) ④ right-sign-null 도 동일 엄격(spec-search 금지) ⑤ spec-modulation=SCA/multiverse joint OR 이론고정+pristine OOS only.

### ★최종 (11 가설 + 자문검증 후)
- **robust CONFIRM 1개 = DEF-2**(dividend_yield×op_prof, yield-trap 분리, 곡률+FM+양분OOS 전부 생존).
- net_issuance 단독 PARTIAL_CONFIRMED(별), value(pbr/ev) 단독 CONFIRM(#7) 유지.
- 나머지 = null / wrong-sign-reject / rank-artifact. ★사용자 "지표간 관점" = DEF-2 1건이 정당화(factor×factor>단일), 나머지는 정직 기각.

---

## ★자문 적용 타당성 독립검증 (2026-06-04, 사용자 지적 = "자문은 이론만, 적용은 별도 검증")

> 자문이 권고한 curvature/FM 검정을 내가 코드로 옮긴 게 ★구현 artifact 인지 독립 방법으로 재확인. json `_b2_def_verify_results.json`. 방법 = (1) 2×2 double-sort diff-in-diff(직교화·rank·회귀 안 씀) (2) hand-built FM(raw 곱 z1·z2, 별 함수) (3) 진단(월별n·조건수·outlier trim).

| 가설 | rank-IC(기존) | double-sort DiD | hand-built FM(raw곱) | trim5% | ★재판정 |
|---|---|---|---|---|---|
| **DEF-2** | +0.065 p0.0005 | +0.022 t1.65 **p0.11 n.s.** | +0.012 t1.82 **p0.083 n.s.** | t1.45 n.s. | ★**CONFIRM→TENTATIVE 격하** |
| **DEF-1** | −0.076 p0.0055 | −0.028 t−1.9 p0.079 | −0.0075 t−1.56 p0.148 | t−1.71 | ★**WEAK 유지** |

### ★구현 결함 발견 (사용자 지적 적중)
- 내 원래 interaction 드라이버 `interaction_z = cs_z(z1*z2)` = 교호항 **sector-neutral 재-z** → 표준 FM(raw 곱)보다 유의도 인플레. curvature-script FM t3.23(재-z) vs hand-built FM t1.82(raw) 불일치의 원인.
- DEF-2 quadrant fwd: HH0.120/HL0.122/LH0.131/**LL0.154** = 저배당·저quality 가 최고수익 = 깔끔한 "고×고 초과" 구조 아님. DiD 양수는 LH<LL 차이서 나옴.
- ★**DEF-2 "robust CONFIRM"은 (a)Spearman rank + (b)교호 재-z 두 구현 선택이 부풀린 것**. 자문 권고 표준 FM(raw)+double-sort 로는 marginal(방향 신뢰, p0.08~0.11).

### ★최종 재판정 (독립검증 후)
> ⚠️ **SUPERSEDED — 본 절 DEF-2 격하 = over-kill 오류**: discovery(재-z rank-IC)/kill(raw FM) 척도 불일치 = forking-paths. ★최종 = §over-kill 최종 정정 (rank-FM 척도 통일 → DEF-2 CONFIRM 복원). 아래는 정정 전 기록 보존.
- **DEF-2 = TENTATIVE** (CONFIRM 아님): 방향 4방법 전부 +로 일관(yield-trap 분리 방향성 신뢰), 유의도 spec 의존(rank 강·linear/portfolio marginal). robust CONFIRM 조건(전 spec 유의) 미충족.
- **DEF-1 = WEAK**: rank-IC 유의가 표준 FM/double-sort 전부서 비유의(t−1.5~−1.9).
- ★**11 가설 中 robust CONFIRM = 0개**. DEF-2 가 최강이나 "방향 신뢰·유의 marginal". value(pbr/ev #7 단일)·net_issuance 단독(PARTIAL)은 별 검정이라 영향 없음(단일 신호는 재-z 이슈 무관).
- **codify 추가(차기 의무)**: ⑥ ★interaction 검정 = 교호항 재-z 금지(raw 곱), primary=double-sort DiD + hand-built FM(raw) 병기, rank-IC 는 보조(불일치=비선형/rank-artifact 플래그). ⑦ 모든 신규 발견 = 자문 차용 후 ★구현 독립 검증(double-sort 등 assumption-light) 의무.

---

## ★국면 조건부 재검 (2026-06-04, 사용자 "국면 섞어 본 것 아니냐 / 어떤 국면서도 유의 X?")

> 교호 검정은 전 국면 pooled(unconditional). 특정 국면 집중 희석 확인. 방법=월별 double-sort DiD_t 를 macro 국면에 (1)연속 slope=size-valid (2)상위40%vs하위40% split=비-size-valid 진단. json `_b2_def_regime_results.json`.

| 가설 | 연속 regime slope (size-valid) | split 진단 (★비-size-valid 참고) |
|---|---|---|
| **DEF-2** | ★**dollar +0.0027 t2.22 fixed-b sig wild p0.044** / vix·credit·real_rate n.s. | dollar 상위 +0.063 vs 하위 −0.001 Welch p0.0001 / credit 상위 +0.042 vs −0.005 p0.003 |
| **DEF-1** | ★dollar −0.0034 t−2.48 fixed-b sig wild p0.034 / 나머지 n.s. | dollar 상위 −0.045 vs 하위 +0.008 Welch p0.005 |

### 해석 + ★caveat
- **DEF-2 교호 = 강달러(risk-off/긴축) 국면 집중**: unconditional marginal 의 원인 = 약달러서 희석. 경제적 정합(강달러=긴축=yield-trap 분리 중요). 2022 긴축·강달러 = DEF-2 OOS 2배 증폭(0.053→0.106)과 겹침.
- ★**over-claim 금지 3 caveat**: (1) 다중비교(regime 4×가설 2=8) — dollar 만 살았으나 Bonferroni **α/8=0.00625** (★정정: 비교수 8 → α/8, 기존 α/4 오기) 적용 시 wild p0.044 > 0.00625 = **보정 후 탈락**(suggestive). (2) regime 검색 자체 post-hoc = forking-paths → dollar-conditional 은 신규 pre-reg + pristine OOS 필요. (3) split p0.0001 = small-block 함정 참고용.
- **결론**: "국면 희석" 의심 부분 적중 = DEF-2 교호는 **dollar-conditional size-valid slope 존재**(t2.22), 단 다중비교·forking-paths 미보정 → 현 vintage 여전히 TENTATIVE, **dollar-conditional DEF-2 = 차기 vintage pristine OOS 신규 가설 후보**(flip-register 와 동격 처리).

---

## ★CYC 교호 전수 독립검증 + regime (2026-06-04, 사용자 "11개 중 볼 가치 다 봐봐")

> ★cyclical 드라이버도 교호항 재-z(`cs_z(z1*z2)`) 동일 결함 → CYC-1/3/4/5 를 raw double-sort + hand-FM + 연속 regime 으로 재판별. json `_b2_cyc_verify_regime_results.json`.

| 가설 | double-sort DiD(raw) | hand-FM(raw) | 방법일치 | regime size-valid | 판정 |
|---|---|---|---|---|---|
| **CYC-1** ev(저)×gross_prof(고) | +0.092 t1.63 p0.13 | +0.042 t1.75 p0.11 | ✅ 둘다 marginal **정방향** | rate10y t3.44 p0.014 / dollar t2.48 | ★**THEORY-PINNED 후보** |
| CYC-3 op_prof×asset_gr(저) | −0.042 t−0.98 p0.34 null | −0.057 t−2.39 p0.028 | ✗ 불일치 | vix t−3.84 p0.0009 | UNSTABLE(re-z artifact 일부) |
| CYC-4 ep×residual_mom | −0.109 t−4.03 p0.0003 | −0.006 t−0.33 p0.77 null | ✗ DS강 FM null | dollar t−3.16 | UNSTABLE(nonlinear/꼬리) |
| CYC-5 ep×idio_vol(저) | −0.042 p0.13 | +0.009 부호반전 | ✗ 부호flip | vix t−4.98 p0.0018 | NULL(부호 불안정) |

### ★메타 발견 + 판정
1. **재-z rank-IC 양방향 불신**: DEF-2/CYC-4 인플레 ↔ ★CYC-1 억압(rank-IC p0.68 null → 깨끗한 double-sort+FM 둘 다 marginal 정방향 p0.11). = 원래 interaction 드라이버 전체 신뢰 불가, 깨끗한 raw 재검 의무.
2. **방법 불일치=신호 불안정**: CYC-3(FM sig/DS null), CYC-4(DS sig/FM null), CYC-5(부호flip). double-sort↔linear-FM 갈리면 nonlinear/꼬리 = robust 아님.
3. regime slope = 16검정(4×4) forking-paths. Bonferroni α/16=0.003 시 vix(CYC-3 p0.0009/CYC-5 p0.0018)만 생존하나 unstable base 위 = 무의미.
4. ★**볼 가치 = CYC-1 단 하나**: Novy-Marx 확립이론 + double-sort·FM **둘 다 정방향 일치**(method 안정) + rate10y regime. marginal(p0.11)이라 현 vintage 결론 X → **이론고정 단일 pre-reg + 차기 vintage pristine OOS**(자문 합법경로 ③, dollar-conditional DEF-2 동격).

> ⚠️ **부분 SUPERSEDED**: 본 절은 DEF-2 를 §독립검증서 격하한 상태 전제 → ★최종 §over-kill 정정서 DEF-2 = CONFIRM 복원. CYC-1 = TENTATIVE theory-pinned 유지(rank-FM full fixed-b 미통과 = over-kill 아님, 정직 marginal). CYC-3/4/5 = REJECT/NULL 유지(CYC-4 라벨 "stably wrong-signed" 교정).
5. DEF-3(stability 교집합) = raw 유의하나 incremental 소멸 = main 각각이 포착, 신규 신호 아님. CYC-2/6·DEF-4/5·mega = 명백 null.

### ★pristine-OOS 후보 register (차기 vintage 1-shot, 현 vintage 확정 금지)
- **CYC-1** ev_ebitda(저)×gross_prof(고), pred +1, Novy-Marx value×quality. method-안정 marginal. theory-pinned 최우선.
- **DEF-2 dollar-conditional** dividend_yield×op_prof | dollar 高, pred +1. regime-interaction.
- (flip-register: CYC-3-flip/CYC-4-flip/DEF-1-PW — UNSTABLE 판명으로 우선순위 최하향)

---

## ★over-kill 검증 자문 R1 (2026-06-04) — Gemini: "내 결론=과잉 제거 판정"

> 사용자 "다 죽었다 over-kill 아닌가". Gemini Pro R1 = ★**robust 0개 결론 = 과도한 보수성 누적 false-negative(Type-II 폭증), 명백한 over-kill** 판정. (Claude 채널·G-C audit 수렴 확인 후 정정 확정)

- **(a) ★재-z 방향 거꾸로**: `cs_z(z1*z2)` 가 일관된 sector-neutral 교호항 정답. raw 곱 z1·z2 = sub-sector cross-product 평균 잔존 = confound. ★내가 DEF-2 를 confound 잣대로 평가절하한 것 = 격하 방향 오류.
- **(b) median-split over-kill**: 이분화 검정력 36% 손실 + sub당 4~12종 → quadrant 1~3종 = idiosyncratic 노이즈 측정. DS t1.65 로 rank-IC p0.0005 뒤집기 부당.
- **(c) rank-IC vs linear 불일치 = rank-IC 신뢰**: small-n OLS 는 outlier 1~2개로 slope 붕괴. Spearman 은 outlier-robust + monotone-nonlinear 포착. 불일치 = 신호가 비선형이지 불안정 아님.
- **(d) 이중보수성 누적**: fixed-b + wild + Bonferroni + one-sided + FDR 직렬 = Type-II 폭증. n_eff≈15서 fixed-b CV>2.5 인데 전 관문 통과 요구 = size-control 강박.
- ★**권고 fix = Rank-based Fama-MacBeth**(sub-sector 내 수익·팩터 rank 정규화 후 FM = outlier-robust+연속정보) / 대안=continuous interaction FM F-test / pooled panel FE. DEF-2 부터 재평가.
- **함의**: ★§자문검증·§독립검증·§CYC전수의 "재-z artifact / double-sort 격하" 결론 = 잠정 무효화 후보. Rank-based FM 으로 11개(특히 DEF-2/CYC-1) 재평가 의무. ⏳Claude 채널 + G-C audit 수렴 후 verdict 일괄 정정.

---

## ★over-kill 최종 정정 (2채널 수렴 + rank-FM 결정 중재, 2026-06-04)

> Gemini Pro + Claude Opus 4.8 병렬 over-kill 자문 + ★Rank-based Fama-MacBeth(discovery·kill 척도 통일) 결정 중재. raw=`~/.claude/.gemini-web-last.md`/`.claude-web-basic-last.md` tail. json: `_b2_def_rankfm_results.json`(DEF) / `_b2_cyc_rankfm_results.json`(CYC).

### 양채널 수렴 (over-kill 진단)
1. **Gemini**: robust 0 결론 = 과도 보수성 누적 false-negative(Type-II 폭증) = 명백 over-kill. rank-FM 으로 DEF-2 부터 재평가 권고.
2. **Claude Opus 4.8 (더 정밀)**: "단순 over-kill 도 clean-null 도 아님 — n_eff~15 = **판별 불능(underpowered/uninformative)**". 정직 라벨 = "내 검정력에서 어느 것도 null 기각 못 함; 진짜 부재와도 IC~0.05–0.08 real effect 와도 모두 정합". ★**robust 0 을 부재의 증거로 박제 = 점추정 prior 박제 금지 위반**.
3. ★**핵심 구멍 (양채널 정합) = discovery/kill 척도 불일치**: 발견은 재-z rank-IC 로, 사살은 raw 곱 FM 으로 = specification 을 중간에 바꾼 **garden-of-forking-paths**. 더 보수적 구성이 매번 이기게 설계됨. sector-neutral mains 와 정합적인 건 재-z 교호(또는 FM+sector FE). 하나를 a-priori 고정해 균일 적용해야 공정.
4. **재-z 방향 = 균일 inflator 아님 (내 전제 자기-반증)**: DEF-2 는 재-z 가 **강화**(rank-IC 강 → raw FM marginal), CYC-1 은 재-z 가 **억압**(rank-IC null → raw FM marginal). 신호마다 방향 반대 = "재-z 가 유의도 인플레, raw 가 정답" 단정 틀림. → DEF-2 를 confound 잣대(raw)로 격하한 것 = ★방향 오류.
5. ★**가장 의심스러운 단일 결정 (Claude) = DEF-2 격하**: 근거(재-z inflate)가 CYC-1 로 자기-반증 + p0.0005→TENTATIVE 뒤집기가 진단 아닌 가정 + discovery/kill 불일치 대표 사례.

### ★rank-FM 결정 중재 (척도 통일 = 발견·사살 모두 rank, outlier-robust + 연속정보 보존)
> 매월 횡단면: fwd·z1·z2 → rank(pct) → OLS rank(fwd)~r1+r2+(r1−.5)(r2−.5) → 교호계수 시계열 → fixed-b CV(KV) + wild-cluster B=9999. median 2×2 double-sort 의 검정력 36% 손실 회피 + Claude 지적 "통일 척도" 충족.

| 가설 | full coef | full t | fixed-b | wild p | n_eff | OOS t | ★최종 판정 |
|---|---|---|---|---|---|---|---|
| **DEF-2** div_yield×op_prof | +0.193 | 2.68 | **sig** | **0.0105** | 57.9 | 3.13 (sig, ★n_eff14.1 UNDERPOWERED) | ★**CONFIRM 복원** |
| **DEF-1** net_iss×ep_yield | −0.207 | −2.15 | sig | 0.0494 | 50.8 | −2.39 (n.s.) | **TENTATIVE PW** (wrong-sign 유의·지속) |
| **CYC-1** ev(저)×gross_prof | +0.416 | 2.28 | **미통과** | 0.0463 | 31.3 | 5.1 (sig) | **TENTATIVE theory-pinned** (full fixed-b 미통과, OOS 주도) |
| CYC-3 op_prof×asset_gr(저) | −0.154 | −1.90 | 미통과 | 0.0876 | 37.2 | −2.6 (wrong-sign sig) | REJECT(wrong-sign) 유지 |
| CYC-4 ep×residual_mom | −0.190 | −1.75 | 미통과 | 0.109 | 28.5 | −0.64 n.s. | REJECT/NULL 유지 |
| CYC-5 ep×idio_vol(저) | −0.077 | −1.16 | 미통과 | 0.249 | 44.1 | −0.56 n.s. | NULL 유지 |

### ★최종 verdict (over-kill 정정 후)
- **DEF-2 = CONFIRM 복원** (이전 §독립검증 "CONFIRM→TENTATIVE 격하" = ★over-kill 오류, 무효화). 근거 = rank-FM(척도 통일) full n_eff57.9 fixed-b sig wild p0.0105 + OOS 방향일치. hedge 유지: (i) OOS n_eff13.9<30 = UNDERPOWERED(방향 정합이나 OOS 단독 결론 금지) (ii) dollar-conditional 집중(강달러 국면) (iii) sub당 4~12종 thin-demean 잔존 (iv) 단일 2010-26 표본. = "CONFIRM (rank-FM size-valid, small-n 적정 방법). robust 강 단정 금지, dollar regime·thin-demean caveat".
- **CYC-1 = TENTATIVE theory-pinned** (over-kill 아님 — rank-FM full fixed-b **미통과** = 진짜 marginal). Novy-Marx value×quality 이론 + 부호+ 일치 + OOS t5.1 강하나 in-sample t0.84 = 표본 후반 주도. 차기 vintage pristine OOS 1-shot 후보 유지.
- **DEF-1 = TENTATIVE PW** (이전 WEAK_RANK_ARTIFACT 격하 → 정정: rank-FM 척도 통일서도 wrong-sign 유의·지속 = artifact 아닌 PW-reversal 진짜 신호. 단 pred(+) 반대라 flip-register DEF-1-PW 로 차기 OOS).
- CYC-3/4/5 = REJECT/NULL **유지** (rank-FM 척도 통일서도 wrong-sign 또는 비유의 = over-kill 아님). ★단 CYC-4 라벨 교정(Claude): "UNSTABLE" → "**stably wrong-signed**"(rank+DS 강하게 음, linear 만 못 봄 = 노이즈 아닌 가설 방향 오류 정보).
- value(pbr/ev #7 단일) CONFIRM + net_issuance 단독 PARTIAL = 재-z 무관, 유지.

### ★audit 즉시수정 5 (independent G-C audit 발견)
1. **re-z 서술 정정**: 이전 §독립검증 "재-z 가 유의도 인플레" = 부정확. 정확 = 재-z(교호항 per-month rescaling)는 **FM 선형계수 시계열 SE 를 ~1.70× 축소 → t 만 인플레**. magnitude(IC 점추정) 불변. **rank-IC 는 monotone-rescale-invariant 라 재-z 와 무관**(audit 확인). → "재-z 가 DEF-2 robust 를 부풀림" 은 FM-t 한정, rank 척도엔 적용 안 됨 = DEF-2 격하 근거 붕괴.
2. **Bonferroni 정정**: §국면조건부 caveat α/4=0.0125 → **α/8=0.00625** (regime 4×가설 2=8 비교). 본문 정정 완료.
3. **DEF-2 OOS UNDERPOWERED 라벨**: OOS n_eff=14.1<30 = floor 미달. OOS t3.13 fixed-b sig 이나 ★UNDERPOWERED(방향 정합 증거일 뿐 OOS 단독 size-valid 결론 금지). full-sample(n_eff57.9)이 primary 근거.
4. **원 interaction JSON superseded**: `_b2_cyclical_interactions_results.json`/`_b2_defensive_interactions_results.json`(재-z `cs_z(z1*z2)` 기반 FM-t)는 ★FM-t 인플레 포함 = **superseded by rank-FM**. rank-IC 점추정·BY 생존 판정은 유효(rank 무관), FM 선형 t 만 무효.
5. **DEF-2/DEF-1 thin-demean caveat**: defensive sub당 4~12종 within-sub-sector demean = thin = idio 노이즈 잔존. rank-FM 이 outlier-robust 로 완화하나 완전 제거 X. 차기 vintage 또는 GICS level 상향 grouping 으로 재검 권고.

### ★방법론 codify (차기 의무, ⑥ 정정)
- ⑥ ★**interaction 검정 primary = Rank-based Fama-MacBeth**(discovery·kill 동일 rank 척도, outlier-robust + 연속정보). median 2×2 double-sort = **보조 진단만**(검정력 36% 손실, sub당 셀 1~3종 = sail 도구로 부적격). 이전 codify⑥ "double-sort+hand-FM primary, rank 보조" = ★역전 정정.
- ⑦ discovery/kill ★**척도 a-priori 고정** = forking-paths 차단(발견 척도로 사살). 재-z 교호 vs raw 곱 중 하나를 사전 선언 후 균일 적용.
- ⑧ ★**robust 0 = 부재 증거로 박제 금지**(점추정 prior 박제 금지 정합). n_eff<30 영역 = "UNDERPOWERED/미결" 라벨, "REJECT/부재" 단정 금지. underpowered ≠ null.
- ⑨ rank-IC vs linear-FM 불일치 = 자동 demote 금지. 판별 4종(decile 단조성·LOO/jackknife·tail vs middle·Kendall τ vs Spearman ρ) 으로 nonlinear-real vs rank-artifact 구분 후 판정.

---

## ★Phase W — 약신호 보강 (2채널 자문 수렴 + 실측, 2026-06-04)

> 사용자 "약한 부분 중심 추가 탐구 + 사망 판정 다른 각도 재검". /gemini-web(Pro) + /claude-web(Opus 4.8) 병렬 R1 강수렴. brief=`.consult-us-weak-signal-revival-brief.md`. ★exploratory FDR family `us_equity_exploratory_v1`(value confirmatory 와 별 family = 기존 value 유의성 오염 차단). 등가중 stacking(weight 표본추정 금지=overfitting). json=`_b2_quality_single_results.json`(cyclical/defensive).

### 자문 수렴 (양채널 일치)
1. ★**quality(gross_prof) 단일축이 1순위 정공 후보** — value 음상관 → 등가중 stacking 결합 IR ↑ 잠재(이론 Sharpe √공식 ρ−0.3 시 ~70%↑). interaction(CYC-1) marginal 은 sub-bucket 자유도 증발 탓 = 단일과 별 질문.
2. **기존데이터(A) >> 신규수집(B)**. 신규 축을 value 와 같은 BY family 투입 금지(임계 상승 → 기존 robust 위협). exploratory family 분리 의무.
3. **mega = "alpha=0 확정" 아님** → 검출불능(N=11) + 무료 forward PIT 불가 → 탐색 종료(표현 교체, §us_mega_tech).
4. **payout QT 재검 = 시간낭비**(calendar/autocorr). **low-vol/BAB = sector-neutral design 이 cross-sector low-vol 제거 → 구조적 약화**(Claude). **asset_growth/NOA = regime confound**(2021-22 supercycle capex, proxy 로 안 풀림). **SUE/PEAD = fast-decay → 연rebal net≈0**(별 고빈도 sleeve 아니면 부적합).
5. **value 저회전 = net-alpha 생존 prior 강**. 등가중만(DeMiguel 1/N, weight 추정=overfitting). 2-3축 max, 각 축 단독 exploratory-BY 선통과 후 stacking.

### ★W1 실측 결과 (quality 단일축 + stacking, 자문 prior 검증)
| 신호 | cyclical IC (t, wildP) | defensive IC (t, wildP) | 판정 |
|---|---|---|---|
| quality(op_prof) 단일 | −0.054 (t−1.71, p0.13) **음·비유의** | −0.012 (t−0.59, p0.57) **null** | ★quality 단독 alpha 부재 (양 sleeve) |
| gross_prof 단일 | (composite 포함) | +0.002 (t0.06) null | 무신호 |
| value/net_iss primary | value IC+0.117 t3.91 IR **4.16** | net_iss IC+0.082 t3.31 IR 3.514 | 기존 robust 재확인 |
| value↔quality 직교성 | cross-corr **−0.023 ≈0** | net_iss↔quality **−0.042 ≈0** | ★자문 "QMJ 강음상관" 미실현 |
| **등가중 stacking** | IR 4.16 → **1.475 희석** ❌ | IR 3.514 → **4.128 (+17%)** ✅ (단 IC 0.082→0.070 하락) | cyclical 무익 / defensive 약한 분산효과(alpha 추가 아님) |

★**W1 결론**: quality 단일축 = 미국 cyclical/defensive **robust alpha 아님**(자문 "검출 prior 중" 데이터 반증, advisory-protocol §1 본인 시뮬 verification). value↔quality 음상관 ≈0 = 직교 stacking 이론이득 미실현. defensive net_iss+quality 등가중만 IR 소폭↑(IC 하락 동반 = alpha 신규 아닌 약 분산). = ★**value 1축 편중은 측정 누락 아닌 데이터 본질**. ⛔ quality 점추정 prior 박제 금지.

### Phase W 잔여 (진행 순서)
- [x] **W1 quality 단일 + stacking** = ★reject(양 sleeve alpha 부재). exploratory family. json `_b2_quality_single_results.json`.
- [x] **W2 accruals horizon** = ★null(3/6/12/24M 전부 fixed-b 미통과 wild p>0.25, 24M 부호 flip). Sloan anomaly 미검출 = 완전성 마감. json `_b2_w2_accruals_results.json`.
- [x] **W4 low-vol/BAB** = ★null/역방향(3~24M IC 음=저vol→저forward=BAB 반대, 전부 비유의, 12/24M UNDERPOWERED). Claude "within-demean 이 BAB 죽임" + cyclical risk-on 적중. json `_b2_w4_lowvol_results.json`.
- [~] **W3 정규화 PER** — ★ROI 낮음 판단(진단용 + PBR collinearity 강 + COVID 처리 부담). value축 성격(earnings vs asset)은 이미 known(cyclical peak-EPS=PER약/PBR강). 사용자 확인 후 강행 여부 결정.
- **보류**: SUE/PEAD(별 고빈도 sleeve 필요) / mega forward(유료 PIT consensus 확보 시 재개).

### ★Phase W 종합 결론 (W1/W2/W4 실측)
- ★**value 외 독립 alpha 축 = 미국 cyclical/defensive 전부 robust 신호 부재**: quality(W1 음/null) + accruals(W2 null) + low-vol(W4 null/역방향). 모두 fixed-b 미통과.
- ★**value 1축 편중 = 측정 누락 아닌 데이터 본질** 실측 확인. 자문 prior("quality 검출 가능 + 직교 stacking ~70%↑") = ★데이터 반증(advisory-protocol §1: 본인 시뮬 verification). value↔quality 음상관 ≈0(직교 이득 미실현).
- defensive net_iss+quality 등가중만 IR 소폭↑(3.514→4.128, IC 하락 동반=약 분산효과, alpha 신규 아님) = 유일한 marginal 부산물.
- ⛔ quality/low-vol/accruals 점추정 prior 박제 금지(전부 null). exploratory family `us_equity_exploratory_v1` 에 생존 0.
- ★**미국 최종(Phase W 후 불변)**: robust alpha = value(pbr/ev cyclical CONFIRM) 1축 + net_issuance(defensive PARTIAL) + DEF-2 interaction(frozen). 독립 다양화 축 부재 = portfolio 분산은 value 단일 + net_iss 보조 한정.
