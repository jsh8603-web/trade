---
tags: [type/handoff, domain/inv, phase/II, track/T3, topic/weight-learning, session/btn-Codlearn]
date: 2026-05-29
session: btn-Codlearn
scope: 조건부 상관 학습 → 평가기준 지표 비중 국면·산업 조건부 조절 (R15)
rounds: 3 (saturation 확정)
models: [gemini-2.5-pro-web, claude-opus-4.8-web]
raw_prompts: [.consult-weight-R1-prompt.txt, .consult-weight-R2-prompt.txt, .consult-weight-R3-prompt.txt]
raw_responses: [.gemini-web-last.md, .claude-web-basic-last.md (diagnostic, 최신 호출)]
oss_research: [~/.claude/memory/research/regime-glasso-portfolio-repos.md, ~/.claude/docs/archive/research-raw/regime-glasso-portfolio-repos-native-20260529.txt]
note: 사용자 명시 누락축(R15) — "관계있는 지표 함께 학습(조건부 상관) → 평가기준 지표 비중을 거시 국면·산업 사이클 조건부로 조절". 3R 자문 saturation. 본 문서=확정 설계 + 워커 분담 SSOT.
---

# 자문 결정 — 가중 학습(R15) 조건부 상관 → 비중 → L1 주입 (gemini+claude 3R saturation)

> 사용자 2회 명시 강조한 누락축. 현 구현(정적 Investment Clock 표·정적 attenuation·additive regime 더미)은 "학습 기반 조건부 비중 조절"이 아님. 3R 자문으로 설계 확정·saturation.

## 1. 확정 설계 (R1+R2+R3 통합, 양모델 강수렴)

### 1.1 조건부 상관 학습 (추정)
- **regime-conditional Graphical Lasso** (L1 정규화 sparse precision Ω). HMM/DCC **기각** — regime 외생 정의됨(소표본·라벨불안정 최악).
- **nonparanormal rank-transform** 전처리(Kendall/Spearman → Gaussianize) = fat-tail robust. within-regime kurtosis 높으면 t-glasso 옵션. fat-tail 상당부는 regime mixture artifact → regime 조건화가 이미 일부 해소.
- 추정은 **hard-per-regime** 유지(각 regime 데이터에 EB shrink). belief-mix는 application 시점에만(추정 희석 0).

### 1.2 shrinkage (소표본 과적합 방어)
- `Σ̂ = λ·Σ_prior + (1−λ)·Σ_glasso`, `λ = n0/(n0+n_eff)` empirical-Bayes + **floor**(prior 완전제거 불가 = self-confirming attractor 차단). prior = Investment Clock 사전상관.

### 1.3 상관 → 비중
- 표본 공분산 역행렬 **금지**. Ω(precision) 직접 사용. `w ∝ Ω·IC`(Grinold 최적결합 — 상관 높은 지표 자동 감액 = 다중공선 해소) + **1/N 블렌딩**(DeMiguel: 최적화가 1/N에 짐 방어) + max-cap.

### 1.4 ★적용 지점 (사용자 핵심 제약 = L1, LLM·agent 이전)
- 학습 비중은 **L1 결정론 합성 단계**에 주입: `S_L1 = clamp_floor( Σ_i w_i(regime) · z_i )`. (claude (c)안 채택 — floor primitive를 학습객체와 분리, 지표별 falsifiability 보존. gemini (b)안=cheapness_z 계수 직접은 floor가 학습 갱신마다 흔들려 기각.)
- **순서 불변식**: `S_out = S_L1 · ∏_k a_k` (a_k ∈ [0,1]). L2(Qwen)/L3(BGE)/agent(DCF) = **down-only attenuator**, S_L1과 자기 증거만 수신(지표벡터·비중 비가시). 천장 불변식 `S_out ≤ S_L1` ∀asset. DAG topological seal로 강제.
- ★★**judge 설계 변경 필수**(claude 지적): 현 `L1 ∥ DCF` 병렬 가법이 천장 불변식을 깬다 → **DCF(agent)도 down-only gate로 재캐스팅**. L1-cheap을 intrinsic value로 veto/할인은 OK, L1-expensive 승격은 불가.

### 1.5 비중의 카드화 (WeightAssumptionCard)
- 기존 registry **서브타입**. baseline=비중 벡터, scope=regime×archetype×period.
- **DUAL falsification**: PRIMARY(kill) = 합성 score OOS Rank-IC의 anytime-valid(e-process) 붕괴 → 기존 e-process·hierarchical FDR 재사용(scoring을 FDR 부모노드 서브패밀리로). SECONDARY(re-fit 트리거, kill 아님) = 상관구조 drift `‖ΔΩ‖`·logdet divergence > τ. 분리 이유 = Ω 흔들려도 score IC 견디면 비중 robust(구조drift로 kill하면 과민).
- **hierarchical partial pooling**: `w = w_global + δ_regime + δ_arch + δ_interaction`, 각 항 부모로 수축. 교호항 데이터 얇으면 0 → 소표본 자동 가법 강등. archetype 단위(경기민감/방어/성장), sector는 archetype prior 공유. period=PIT+recency.
- **soft time-varying archetype membership** `π_i(regime,t)`: hard label 금지. `δ_arch(i)=Σ_a π_{i,a}·δ_a`. π는 cheapness **결과 아닌 구조 feature**(마진·성장·beta·레버리지)로 학습(순환·누수 차단), PIT 버전드. 재배정=카드 re-fit.

### 1.6 ★regime soft-belief (R3, claude 정밀)
- 외생 hard regime → **soft belief b(t)**. hard argmax는 transition(불확실성 최대 지점)에서 비중 점프·common-cause 오염.
- ★**cov-space 혼합**(Ω-혼합 아님): `Σ_eff = Σ_r b_r·Σ_r + Σ_r b_r(μ_r−μ̄)(μ_r−μ̄)ᵀ`. 둘째 항=between-regime dispersion → regime 모호 시 risk 자동 inflate(=transition 자동 de-risk, feature). cov-space mix → **1회 역행렬** → Ω_eff → `w ∝ Ω_eff·IC` → cap. **이중 mix(Ω도 w도) = incoherent double-count 금지**.
- nowcast lag = **PIT vintage로 enforce**(별도 belief-transition kernel 금지 = 이중 hysteresis 금지).
- classifier confidence **직접 사용 불가** → **calibration 필수**(temperature/isotonic, OOS regime-label offline fit, ECE 검증, frozen+hash-pin, drift 감시 대상). raw softmax는 boundary 과신 → soft 옷 입은 hard.
- b(t) **frozen 박제** = necessary(predictable convex combo = mixture e-process supermartingale 보존, lookahead면 type-I 깨짐). replay엔 b벡터+model/calibration hash 둘 다 pin.

### 1.7 결정론·replay·bitemporal
- WeightCard hash-pinned frozen. 이중 시간축: `knowledge_time`(학습 데이터 PIT 경계) vs `decision_time`(시스템 반영). `V(T)=knowledge_time≤T & purge+embargo 충족 최신 카드`. replay 경계 = S_L1/attenuator 이음새(이하 결정론 재계산, 이상 확률 LLM은 seed+model-hash fixture). re-fit=신규 버전(기존 불변).

### 1.8 반사성·안정성
- purged+embargo CV(전이구간 embargo로 누수 차단), λ floor, hysteresis(e-process 임계 AND 이탈폭), 과거 포지션/체결 데이터 **배제**(외부 지표 시계열만 학습).
- ★**교정채널 분리**(claude): LLM/agent는 live score 못 올림(down-only). 대신 "L1 저평가 의심+증거"를 emit→**offline falsification/re-fit 입력으로만**(purge+embargo 게이트), live 불변. live=down-only / 교정=offline-validated-only. (이 채널에 예산 안 쓰면 silent FN 출혈 = down-only 실제 비용.)
- IC falsification 검정력: e-process가 type-I 해결, 잔여=type-II → **MDE+effective-n>N_min 사전등록**(block-bootstrap 자기상관 보정), 미달 카드=unfalsified 보호관찰. 계층 검정력 차용(leaf는 자기 검정력 전까지 parent status 상속).

### 1.9 cold-start governance (R3)
- 신규 지표/국면 = regime 불확실성 극단 → **belief 기계로 통합**(별도 override path 아님). high-entropy belief → between-cov 폭발 → Σ_eff inflate → w 분산·shrink → floor와 1/N 자연 강등(수학이 de-risk, 사람 결정 0 = default (a)).
- override (b) = **offline·pre-registered·prior-space만**(기존 EB shrink 채널). 사람이 "신규지표→기존 feature proxy" 등록, MDE/eff-n 게이트 통과 후 양의 weight. LLM=proxy 저작 금지(read-only "미지 regime 의심" flag만). live score 미접촉.

### 1.10 최소 통합 (adapter, 갈아엎지 말 것)
- `structure_model`: 기존 OLS에 **지표×regime 교호항** 컬럼 + ridge/계층 수축(가법 baseline 보존, 교호=학습 델타). 이게 scoring 맥락 조건부상관 경량 proxy(glasso는 portfolio/risk full 공분산 한정).
- `indicator_event_correlation`: 정적 attenuation 상수 → 비중카드 lookup으로 교체(호출부 동일, 백킹만 데이터화).
- `regime_to_weights` BL: 학습 Σ̂를 BL의 **view**로 주입(정적표=prior). 새 파이프 0.
- 신규 = registry 내 WeightCard 서브타입 + 기존 anytime-valid 모니터 재사용.

## 2. accepted bounded residual (saturation 근거)
- **남은 1축 = regime partition/schema 불확실성**("한 regime이라 부른 게 실은 Ω 다른 둘", structural meta-uncertainty). 단 R1에서 **의도적으로 scope 밖**(regime 외생화=소표본·반사성 회피)으로 둠 → open hole 아닌 **accepted bounded residual**. 닫으려면 기각한 HMM/endogeneity 재유입 → **문서화된 가정경계로 명시**.
- **메타 판정**(양모델): telescoping 수렴(점추정→주입점→추정불확실성→conditioning불확실성→schema불확실성, 영향 단조감소). "새 축이 build 가능이 아니라 assume/document해야 할 때 = 바로 지금" → **saturation 확정, ship**. falsification layer가 prior 불완전성을 경험적으로 표면화하므로 모든 축을 a priori 예상 불필요(over-engineering=researcher DOF↑=overfitting 반사성 risk).

## 3. OSS 백본 (차용, GitHub 리서치 subagent)
- **skfolio** (BSD, ⭐2k 활발) = GraphicalLassoCV+LW shrinkage+Combinatorial Purged CV+Walk-Forward+BL 한 곳 = **최우선 백본** (조각 1·2·3·5).
- **skggm** (MIT, QUIC glasso·EBIC) = 조각1 정밀. **PyPortfolioOpt**(MIT, BL Idzorek)·**Riskfolio-Lib**(BSD, BL 3종) = 조각3.
- WeightCard 카드화·falsification·regime분리·EB블렌딩 = **자작**(OSS 부재). nonparanormal copula glasso = rank-transform 전처리 자작(arxiv 1202.2169).
- ⛔ **mlfinlab 차용 금지**(독점 라이선스 페이월) → purged CV는 skfolio로. Riskfolio LICENSE-XL 상업제약 확인 필요.

## 4. 워커 분담 (3세션, R15 구현)
| 세션 | 담당 (자문 §매핑) | 산출 |
|---|---|---|
| **btn-button** (통계 core/structure) | §1.1 regime-conditional glasso(skggm/skfolio) + nonparanormal rank-transform + §1.2 EB shrinkage(λ floor) + §1.6 cov-space belief-mix(Σ_eff between-dispersion, 1회 역행렬→Ω_eff) + classifier confidence **calibration**(temperature, frozen) + §1.8 IC falsification 검정력(MDE+eff-n 사전등록) | `core/structure/conditional_correlation.py`(신규) + structure_model 지표×regime 교호항+ridge 확장 + assumption_stats 검정력 게이트 |
| **btn-Inv** (데이터/PIT core/data) | 지표 패널 PIT 공급(as_of vintage) + §1.7 WeightCard event_ledger 영속(knowledge_time/decision_time 이중축) + §1.8 purged+embargo CV 데이터 분할 + 과거포지션/체결 배제 데이터 게이트 + §1.9 cold-start OOD 감지(max-belief<θ, Mahalanobis 밖) 데이터 | data_contract WeightCard 스키마 + lineage 비중 provenance + CV split provider |
| **btn-Codlearn** (오케스트레이션 core/assume, 나) | §1.5 WeightAssumptionCard(registry 서브타입) + §1.3 `w∝Ω·IC+1/N+cap` derivation 확장 + §1.4 L1 합성 주입(S_L1=clamp_floor(Σ w·z)) + ★judge DCF down-only 재캐스팅 + DUAL falsification(validator/update_controller 재사용) + §1.5 soft archetype membership + hierarchical partial pooling + §1.6 b(t) frozen 박제 적용 | `core/assume/weight_card.py` + derivation/judge/validator 확장 + closed-loop GATE 확장 |

> 통합 = btn-Codlearn(나). 각 세션 ≤3R 자기 자문 허용하되 본 §1 확정 설계는 고정(자문으로 누락 발견 시 btn-Codlearn 제안).
