---
tags: [type/theory-notes, domain/inv, study/macro, phase/2-2]
date: 2026-05-30
study_id: macro
phase: "2-2 이론학습 (main 2-1 승인 후)"
source: [raw/round-1.md, raw/round-2.md, 분석가 도메인지식]
note: macro 6 프레임워크 정독노트 + 7축 driver→FRED 매핑 + 국면정의 2축vs3축 정량비교 설계(driver×국면 vs obs 게이트). 2-3 validation 입력.
---

# macro 2-2 이론학습 노트

> main 보강 반영: (a) 7축 확장 시 driver차원↑→regime당 effective-n 악화 → 'driver수×국면수 vs obs'
> 게이트를 국면비교에 명시 + regime obs floor(<floor→global shrink, RegimeGlasso.min_obs) 연결.
> (b) 가설0 GATE 먼저 깨지면(LR/PIT) 2-3 나머지 중단·즉시 보고.

## 1. 6 거시 프레임워크 정독노트 (각: 핵심명제 → glasso 매핑 → 우리 함의)

### F1. 통화정책 전달경로 (Monetary Transmission — Bernanke-Gertler 1995)
- **핵심**: 정책금리 변경이 (금리·신용·자산가격·환율) 채널로 실물·자산에 파급. 국면별로 *작동 채널이
  다름* — 긴축 초기=금리채널(장기금리 반응), 후기=신용채널(스프레드 반응).
- **glasso 매핑**: 같은 (real_rate, credit_spread) 엣지라도 국면별 partial-corr 강도가 달라야 한다.
  긴축초기 regime → real_rate 가 hub / 긴축후기·위기 regime → credit_spread 가 hub. = regime-conditional Ω 의 직접 근거.
- **함의**: 블록3 relationships 의 `lag_routing` + regime별 엣지 강도 prior. credit↔yield 엣지를 국면조건부로.

### F2. 금리 기간구조 (Term Structure — Fama-Bliss 1987, 기대가설+기간프리미엄)
- **핵심**: 장기금리 = E[미래 단기금리] + term premium. 커브 형태(기울기·곡률)가 국면 신호.
  10Y-2Y 역전 = 침체 12~18M 선행.
- **glasso 매핑**: yield_10y_2y 는 *국면 분류 입력*이자 노드. 역전→해소 전환이 regime transition anchor.
- **함의**: 블록2 yield_10y_2y(level) + 블록4 "커브 전환 시 가중↑"(가설 5 transition). term premium 분해
  (ACM/Kim-Wright)는 우리 데이터 부재 → collector_plan 후보(우선순위 中).

### F3. 신용사이클·금융가속기 (Financial Accelerator — BGG 1999)
- **핵심**: 자산가격↑↔신용팽창 상호강화 → 위기 시 급격 디레버리징. 위기국면에서 부채·부도·스프레드
  관계가 *폭발적*으로 강해짐(비선형).
- **glasso 매핑**: 위기 regime 에서 credit_spread_hy_oas 가 네트워크 전체를 지배하는 hub(중심성↑).
  = 가설 6(중심성)의 이론근거 — 단 glasso 무방향이라 인과는 주장 X(scope 제외 유지).
- **함의**: 위기 regime 의 Ω 는 dense(상관→1 수렴) — 가설 3(희소성) 실패모드와 연결. 위기국면은 sparse
  가정이 깨질 수 있음 → 국면별 EBIC λ 가 위기에서 작게(dense 허용) 나오는지 2-3 점검.

### F4. 글로벌 유동성·달러 사이클 (Global Financial Cycle — Rey 2013 "Dilemma not Trilemma")
- **핵심**: 미 연준·달러 위상이 전세계 자본흐름·신용 좌우. 달러강세(risk-off)에서 EM통화·원자재·글로벌
  주식 상관이 급등 — *달러 유동성 공통원인* 때문.
- **glasso 매핑**: ★이게 v1 실데이터의 `stock~dollar 매개 0.36`의 정체 — dollar(또는 그 배후 real
  rate/risk) 가 공통원인이라 stock~dollar 전체상관은 크나 partial 은 죽음. **dollar/VIX 를 패널에 넣어
  통제하면** 나머지 partial-corr 정화(R1 #4 잠재인자 proxy 통제).
- **함의**: 블록2에 dollar_dxy + (신규)VIX 추가 = 잠재인자 명시 통제. 블록3 stock 관계는 edge_type=common_cause.

### F5. FX 캐리·위험선호 (Carry & Risk Appetite)
- **핵심**: 저금리 조달→고금리 투자. 캐리 성과/청산 = 글로벌 위험선호 proxy. 미-일 금리차↔엔캐리↔
  글로벌 유동성. 미-일 차 축소 = 엔캐리 청산 압력(위험자산 충격).
- **glasso 매핑**: jgb_10y 노드 + (real_rate - jgb_10y) 금리차 조건. 캐리청산 regime 에서 위험자산
  상관 급등.
- **함의**: 블록2 jgb_10y(collector_plan) + 블록3 jgb~dollar lagged 엣지. carry 지수는 데이터 부재.

### F6. Fisher 분해 (명목 = 실질 + 기대인플레)
- **핵심**: 명목금리 = real rate + breakeven. 자산은 두 성분에 *다르게* 반응 — 주식은 낮은 real rate
  선호, 높은 breakeven 은 비용우려. "금리상승"도 real 주도 vs breakeven 주도면 주식-채권 상관이 완전 상이.
- **glasso 매핑**: ★중요 — us10y(명목) 단일노드는 정보손실. **real_rate(DFII10) + breakeven(T5YIE)로
  분해**해야 regime별 정확. v1은 명목 us10y만 써서 이 분해를 못함(2-3 보강 핵심).
- **함의**: 블록2 real_rate_10y + breakeven_5y 분리(이미 indicators에 있음). 블록3 real~breakeven =
  common_cause(성장/Fed 기대 매개, conditioning_set=[recession_prob]).

## 2. 7축 driver → FRED 시리즈 매핑 (블록2 입력 확정)

| 축 | driver | FRED 시리즈 | in-system | transform |
|---|---|---|---|---|
| 1 Growth | cfnai / payems / indpro | CFNAI·PAYEMS·INDPRO | ✅ (fred_adapter) | level/yoy |
| 2 Real rate | real_rate_10y | **DFII10** | ❌ collector | level |
| 3 Breakeven | breakeven_5y | T5YIE (+T10YIE) | ✅ | level |
| 4 Credit | credit_spread_hy_oas / baa | BAMLH0A0HYM2·BAA10Y | ✅ | own_history_z |
| 5 Dollar/Liq | dollar_dxy / wgs | **DTWEXBGS**·WALCL +DXY(Yahoo) | ❌ collector | own_history_z |
| 6 Risk/Vol | vix / move | **VIXCLS**·**MOVE** | ❌ collector | level |
| 7 Supply | oil / metals | (Yahoo oil 보유) | △ | own_history_z |
| 잠재 proxy | monetary-shock / risk | OIS변동·VIX | ❌/△ | level |

→ **신규 collector_plan**: DFII10·DTWEXBGS·VIXCLS·MOVE (FRED 무료). 잠재인자 통제용 VIX 가 핵심.

## 3. 국면정의 2축 vs 3축 정량비교 설계 (★main 보강 a — driver×국면 vs obs 게이트)

### 비교 대상
- **2축**: Investment Clock 4국면 (growth × inflation) — 확정설계 기본.
- **3축**: + policy(매파/비둘기) = 최대 8국면 (R1 권고).

### ★게이트: driver수(p) × 국면수(K) vs 가용 obs(N)
- glasso 안정 Ω 경험칙: regime당 **n_r ≳ 3p** (공분산 추정 안정). p=7~10(7축+잠재), 
  - 2축 4국면: 월별 ~20년 240obs / 4 ≈ **60/regime** ≥ 3×10=30 → ✅ 대부분 충족
  - 3축 8국면: 240 / 8 ≈ **30/regime** ≈ 경계 (일부 희소국면 stagflation-hawkish 등 <30 빈번) → ⚠️
- **결정 규칙**: 국면당 effective-n(AR1 보정, `effective_n_ar1`) 측정 → **n_eff < floor(=30) 국면은
  regime-specific Ω 미적합, global 로 수축** (RegimeGlasso.min_obs floor 상향 검토: 10→~30 when p↑).
  composed_weights 가 δ_regime 부재 시 w_global 로 자동 가법강등(이미 구현) = 부족국면 graceful.
- **2-3 측정**: 2축/3축 각각 (a) 국면별 n_eff 분포 (b) <30 국면 비율 (c) global-shrink 발동 빈도
  (d) 가설0 LR/PIT 성능 → 3축이 정보이득 > 소표본손실인지 데이터로 판정. 기본=2축 유지, policy는 조건키 보조.

### regime obs floor ↔ G5 연결 (main 보강 a)
- 메커니즘: `RegimeGlasso.fit` L264 `if len(Xr) < min_obs: continue`(스킵) → 해당 regime 카드 δ_regime
  부재 → `composed_weights` w_global 수축. 즉 obs floor = **자동 global shrink 트리거**.
- 보강: p(driver) 증가 시 min_obs 를 max(10, 3p) 로 동적 설정(2-3 파라미터). 희소국면 노이즈 Ω 차단.

## 4. 2-3 진입 준비 (validation 설계 — 가설0 GATE early-stop 포함)

- **validation-0 (선결 GATE)**: 가설0 — Σ_regime vs Σ_static vs μ_regime. LR test(p<0.01) + OOS PIT/K-S.
  ⛔ **main 보강 b: 가설0 실패(LR p≥0.01 AND PIT 우월 실패) 시 validation-1~5 중단·즉시 main 보고**
  (선결 전제 붕괴 = 자원 절약). v1 dispersion≈0 이 부분지지라 통과 기대하나 정식 검정 필수.
- validation-1: 가설1 OOS Rank-IC e-CUSUM + DCC/Markov 벤치마크(채택X, 비교용).
- validation-2: permutation Ω-diff(가설2, regime셔플 1000회) + Bai-Perron 구조단절(2022/2023 이벤트).
- validation-4-5: force-include 제거 ablation(가설4) + Reflation 부트스트랩 CI(가설5).
- 7축 패널 확장(DFII10/VIX 등) 후 partial-corr 재검증(F4·F6 잠재인자 통제·명목→실질 분해).
- → 결과로 study_session.yaml 7블록 갱신(v1 yaml raw 참고용 보존).

### 핵심 학습 요약 (애널리스트)
1. **F6 Fisher 분해가 v1 최대 누락** — 명목 us10y 단일노드 → real+breakeven 분리 필수(국면별 주식-채권 부호 결정).
2. **F4 GFC/dollar 가 v1 매개 0.36의 정체** — dollar/VIX 잠재인자 통제로 partial-corr 정화.
3. **F3 위기국면 dense** — 가설3(희소성) 위기서 실패 가능 → 국면별 λ 점검.
4. **3축 국면은 소표본 게이트로 판정** — 정보이득 vs n_eff 손실, global-shrink 폴백 연결.
