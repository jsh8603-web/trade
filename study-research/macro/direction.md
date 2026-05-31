---
tags: [type/study-direction, domain/inv, study/macro, topic/indicator-weight-study, phase/2-1]
date: 2026-05-30
study_id: macro
phase: "2-1 방향성 (자문 3R 수렴 → main 승인 대기)"
rounds: [raw/round-1.md(수집방향), raw/round-2.md(검증방향), raw/round-3.md(가설+반증)]
consult_channel: "Gemini Pro API(gemini-search.js) 3R — /gemini-web·/claude-web 브라우저 채널은 9세션 동시경합으로 폴백(STUDY-KIT §2 폴백 규정). 각 round archive=~/.claude/docs/archive/research-raw/macro-*-20260530.txt"
note: macro(거시·FX) 애널리스트 방향성 — 자문을 *맹목 코드화하지 않고* 채택/기각/우선순위를 판단해 잡은 수집·검증·가설 방향. main 승인 후 2-2(이론학습)→2-3(실데이터 검증·코드화) 진입.
---

# macro 스터디 방향성 (2-1) — 거시·FX 애널리스트 종합

> v1 반성: 이전 산출은 자문을 그대로 yaml 로 코드화하고 끝냈다. 이번엔 **애널리스트로서 자문을
> 심사** — 무엇을 채택/기각/우선하는지, 확정설계와 충돌하는 자문은 어떻게 처리하는지를 명시한다.

## 0. 자문 3R 요약 (수렴 판정)

| R | 주제 | 핵심 산출 | raw |
|---|---|---|---|
| R1 | 이론 **수집방향** | 7-driver 분류, 6 프레임워크, 국면정의 5대안, 잠재인자 5종, 1차소스 | round-1.md |
| R2 | 이론 **검증방향** | PIT/vintage, EBIC·shrinkage·FDR, OOS e-process, 시계열함정, Ω-diff 검정, 정량게이트 | round-2.md |
| R3 | **핵심 가설+반증** | 가설 0~6(반증조건 정량), 취약가설 2 적대적 지목, 빠진축, 공분산구조 정식화 | round-3.md |

**수렴**: 3R 각각 실질·비중복. R3가 R1·R2·실데이터 위에서 일관된 가설 집합 + 자기비판에 도달 →
추가 라운드는 정제뿐(신규 substance 없음)이라 3R 종결(3~7R band 충족).

---

## 1. ① 이론 수집방향 (R1 심사 — 애널리스트 채택/보강)

### ✅ 채택 — v1 대비 보강 (★이게 v1 누락분)
- **driver 7축으로 확장** (v1 = real_rate/breakeven/credit/dollar 4축에 그침):
  1. **Growth** (분자! — v1 누락. 자산가격 = E[CF|성장]/할인율, 성장축 독립 포함 필수: PMI/PAYEMS/INDPRO/CFNAI)
  2. real rate (DFII10) 3. breakeven (T5YIE/T10YIE) 4. credit premium (HY OAS/BAA10Y)
  5. dollar/liquidity (DXY/DTWEXBGS/WALCL)
  6. **risk-premium·volatility** (v1 누락. VIX/MOVE — credit 과 별개의 자산시장 전반 위험선호)
  7. **supply/commodity shock** (v1 누락. 유가/금속 — stagflation 외생충격, 성장-인플레 2축 왜곡)
- **잠재 공통원인 proxy 통제** (R1 #4 — glasso partial-corr 의 "진짜 직접효과" 추출 전제):
  monetary-policy-shock(OIS 변동) / risk-on-off(VIX) / productivity / global-demand-supply / demographics.
  → VIX·OIS 를 패널에 넣어 통제하면 나머지 partial-corr 가 깨끗해짐 (v1 실데이터에서 stock~dollar 매개
  0.36 이 바로 이 미통제 잠재인자 흔적).

### ⚖️ 판단 — 국면 정의: Investment Clock 2축 → **growth-inflation-policy 3축** 권고 검토
- R1 권고 = 3축(중앙은행 반응함수 추가) + FCI 보조. 같은 stagflation 도 매파/비둘기 정책이면 자산반응 상이.
- **애널리스트 판단**: 3축은 8국면→국면당 N 급감(소표본 악화). **2-2에서 정량 비교**(2축 vs 3축 국면당
  effective-n + 분류 안정성) 후 결정. 기본은 확정설계(Investment Clock 4국면) 유지, policy 는 *조건키 보조*로.
- ⚠️ **FCI 기반 국면 = tautology 위험**(R1 명시): 시장가격 결과물로 국면 정의→자산가격 예측 = 동어반복.
  FCI 는 국면 정의가 아니라 *검증용 보조지표*로만.

### 수집 1차 소스 (블록2/6 입력)
FRED in-system 17 + 추가 무료: DFII10(real rate)·T10YIE·VIXCLS·DTWEXBGS·WALCL·MOVE·FRA-OIS proxy.
학술 프레임워크: Bernanke-Gertler(통화전달), BGG(financial accelerator), Rey 2013(GFC/dollar),
Ludvigson-Ng(macro factors), Fama-Bliss(term structure).

---

## 2. ② 이론 검증방향 (R2 심사 — ★확정설계 충돌 처리 핵심)

### ✅ 채택 (확정설계와 정합 — 우리 코드에 이미 존재)
- **PIT real-time vintage** (ALFRED, Croushore-Stark) → `core/data/vintage.py` VintageStore 이미 보유.
- **EBIC**(Foygel-Drton) → `conditional_correlation.fit_glasso_ebic` 이미 구현.
- **Ledoit-Wolf shrinkage** → `_lw_fallback` 이미 구현. **force-include prior** → `RegimeGlasso(corr_prior=)` 이미 지원.
- **OOS Rank-IC e-process / e-CUSUM 단측** → `weight_falsification.score_ic_breakdown_eprocess` 이미 구현.
- **n_eff(AR1) 보정** → `conditional_correlation.effective_n_ar1` 이미 구현. **MDE/검정력** → `mde`/`ic_power_gate` 이미.
- **FDR 다중검정** → `hierarchical_fdr` 이미 보유.

### ⛔ 기각(모델 채택) → ✅ 벤치마크로만 수용 (★v1 실수 방지 = 자문 맹목추종 회피)
- R2·R3가 **Markov-Switching(Hamilton)**, **DCC-GARCH(Engle)** 을 권고 — 그러나 **확정설계 §8 = 국면
  외생(regime exogenous), HMM/DCC로 국면 *내생추정* 금지**. 두 자문 모두 이 확정선과 충돌.
- **처리**: Markov/DCC 를 *모델*로 채택하지 않는다. 단 **검증 벤치마크**로는 수용 — "우리 외생 regime
  glasso 가 DCC 연속상관/Markov 내생국면보다 OOS 우월한가"(가설 1 보조조건)를 측정해 외생 가정의
  *정당성*을 데이터로 입증. (벤치마크 ≠ 채택.)

### ✅ 신규 채택 (우리에 없던 검증 primitive — 2-3에서 구현)
- **Ω_regime 차이 permutation test** (R2/R3): regime 라벨 셔플 1000회 → between-regime Ω거리가 상위 5%인가.
  = "regime-조건부성이 우연이 아님"의 통계적 게이트. (v1은 Δ상관만 봄, 유의성 검정 없었음 = 보강.)
- **비정상성 처리**: levels(금리·스프레드)는 I(1) → ADF/KPSS 후 차분 또는 nonparanormal rank(이미 보유).
  returns 는 정상(v1이 로그수익률 쓴 건 정합). spurious regression(Granger-Newbold) 회피.
- **구조단절 명시 검정**: Bai-Perron(다중) — 2022 러우전쟁·2023 SVB 가 regime 무관 네트워크 급변(가설2 실패모드).
- **baseline 3종**: 1/N 등가중 / PCA PC1 / 단일 최강지표 — 복잡모델이 단순대안 대비 우월 입증(López de Prado).
- **경제적 유의성**: 통계 IC 넘어 거래비용 후 초과수익(min-var/pair backtest) — 2-3 또는 통합단계.

---

## 3. ③ 핵심 가설초안 (R3 + 실데이터 + 애널리스트 우선순위)

> 반증조건 = 정량. ★표시 = v1 실데이터로 *이미 부분 입증*. ⚠️ = 적대적 취약(기각위험 큼).

| # | 가설 | 반증조건(기각 트리거) | 우선/판단 |
|---|---|---|---|
| **0** | **★공분산구조 국면의존**: 국면을 Σ에 조건부 반영한 모델이 μ에만 반영/미반영보다 압도적 우위 | LR test(Σ_regime vs Σ_static) p≥0.01 OR OOS PIT K-S 우월 실패 | **선결 GATE** (이게 깨지면 전체 무의미). v1 dispersion≈0 = 부분지지 |
| **1** | **국면조건부 glasso 예측우위**: 외생regime glasso가 static/rolling보다 partial-corr 예측 우위 | OOS Rank-IC e-CUSUM 126일 0.1 미회복 OR DCC대비 우위 50% 미만 | 핵심. DCC=벤치마크(채택X) |
| **3** | **희소성 정보가치**: EBIC sparse가 dense보다 OOS 우월 | 전기간 e-CUSUM(sparse)<e-CUSUM(dense) | 채택. 6자산 dense위험 주의 |
| **4** | **★핵심관계 내생발견**: force-include 없이도 dxy~us10y(+)/gold~us10y(−) 발견 | rate-up pcorr(dxy,us10y)≤0 OR stagflation \|pcorr(gold,us10y)\|<0.1 | 채택. v1 partial +0.24~+0.27/−0.24~−0.29 = **이미 입증** |
| **5** | **★단절 식별**: Reflation에서 sp500~us10y 직접 pcorr≈0 | Reflation \|pcorr(sp500,us10y)\| 부트스트랩 95%CI 0 미포함 | 채택. v1 mediated partial −0.006~−0.13 = **이미 입증** |
| **2** | ⚠️**국면 내 안정성**: between-regime Ω거리 > within-regime | permutation p>0.05(국면간≈국면내) | 취약(기각위험). 실패시 = 연속belief 폴백(belief-mix 이미 보유) |
| **6** | ⚠️**중심성 선도성**: US10Y 중심성이 VIX를 Granger-선도 | F-test p>0.1(선도 없음) | **scope 제외 권고**: glasso=무방향, 인과추론 한계 |

### ★ 가설 0 = 공분산구조 정식화 (사용자 핵심발견의 정당화)
"regime 신호가 평균 아닌 공분산구조에 있다"(v1 dispersion≈0) → **모델 A(Σ_regime) vs B(Σ_static)
vs C(μ_regime)** 3자 LR test + OOS density PIT/K-S. 이게 전체 접근의 선결 전제이자 가장 먼저·엄격히
검증할 GATE. 우리 belief-mix Σ_eff(between-dispersion) 가 바로 이 가설의 산물.

### 빠진 가설축 보강 (R3 지적)
- **유동성/자금조달 스트레스**(FRA-OIS, CP-Tbill): 위기국면 "상관→1 수렴"의 핵심동인. 7축에 추가 검토.
- **포지셔닝**(CFTC/CTA): 거시-시장 괴리 — 단기 왜곡. 우선순위 낮음(반사성 게이트와 충돌 주의: 포지션은 학습입력 금지).

---

## 4. 애널리스트 판단 종합 (채택/기각/우선순위 — v1과의 차별점)

1. **확정설계 사수**: regime 외생(§8) 고수. Markov/DCC 자문은 *벤치마크*로만(맹목채택 X). ← v1 실수 차단.
2. **driver 7축 + 잠재인자 proxy 통제**로 확장(Growth·Vol·Supply 추가). v1 4축은 불완전.
3. **가설 0(공분산구조 GATE)** 을 최우선 — 깨지면 전체 폐기. v1은 이 GATE를 명시 안 했음.
4. **가설 6 scope 제외**, **가설 2는 취약**(실패 시 연속 belief 폴백 — 이미 belief-mix 보유).
5. **신규 검증 primitive 3개 구현 필요**(2-3): permutation Ω-diff / Bai-Perron 구조단절 / baseline 3종.
6. v1 실데이터가 **가설 0·4·5를 이미 부분입증** — 2-3은 이를 정식 검정(LR/부트스트랩/permutation)으로 격상.

---

## 5. 2-2 / 2-3 실행계획 (승인 후)

- **2-2 이론학습** → `raw/theory-notes.md`: 6 프레임워크 정독노트(통화전달·term structure·financial
  accelerator·GFC dollar·carry·Fisher) + 국면정의 2축vs3축 정량비교 설계 + 7축 driver→FRED 시리즈 매핑.
- **2-3 실데이터 검증·코드화** → `raw/validation-*.md` + `study_session.yaml`:
  - validation-0: 가설0 LR test + OOS PIT/K-S (Σ_regime vs static vs μ_regime)
  - validation-1: 가설1 OOS Rank-IC e-CUSUM + DCC/Markov 벤치마크 비교
  - validation-2: permutation Ω-diff(가설2) + Bai-Perron 구조단절
  - validation-4-5: force-include 제거 ablation(가설4) + Reflation 부트스트랩 CI(가설5)
  - 7축 driver 패널 확장(VIX/OIS/DFII10 등) 후 partial-corr 재검증(잠재인자 통제)
  - → 검증결과로 study_session.yaml 7블록 갱신(v1 yaml은 raw 참고용 보존, 폐기X).

## 6. 완성도 공백 / main 요청

- FRED 무료 추가 시리즈(DFII10·T10YIE·VIXCLS·DTWEXBGS·MOVE·FRA-OIS): fred_adapter 확장 필요(통합단계 반영 예정).
- 2축 vs 3축 국면정의 결정 = 2-2 정량비교 후 (소표본 trade-off).
- ⛔ **2-1 종료 — main(btn-Codlearn) 승인 전 2-2 진입 금지** (STUDY-KIT v2 지시). 본 direction.md 검토 요청.
