---
tags: [type/study-summary, domain/inv, study/macro, topic/indicator-weight-study]
date: 2026-05-30
study_id: macro
note: macro(거시·FX) 스터디 방 사람용 요약 — study_session.yaml 7블록의 근거·결정·기각 사유.
---

# macro 스터디 요약 — 거시·FX (R15 가중학습)

## 0. macro 방의 특수성 (먼저 읽을 것)

macro 는 **매매 sleeve 가 아니라 regime 엔진**이다. 다른 주식/원자재/채권 방은 "그 자산군 종목을
어떻게 평가·사이징하나"를 산출하지만, macro 는 **Investment Clock 국면을 분류해 belief b(t) 를
만들고**, 그 belief 가 ③ inject 단계(`regime_to_weights._belief_conditional_cov`)에서 **모든 다른
sleeve 의 공분산 Σ_eff 를 조절**한다. 따라서 macro 의 weight_rules 는 두 층이다:
1. 어떤 거시지표가 어떤 국면 분류에 더/덜 기여하나 (`modulate_by: regime`)
2. 그 국면 belief 가 downstream sleeve 가중을 어떻게 흔드나 (Σ_eff 주입)

## 1. 일반론·보고서 핵심 (블록1 lens)

- **가격결정**: 거시 자산가격 = 성장·인플레·유동성·리스크프리미엄 4요인. 핵심 driver 4개 =
  real rate(할인율 본체) / inflation breakeven / credit-risk premium(HY OAS) / dollar(글로벌 유동성).
- **Investment Clock 4국면**(Reflation/Recovery/Overheat/Stagflation)은 성장×인플레 2축. 단 국면은
  **외생 조건키**이지 내생 추정 대상이 아니다 — HMM/DCC 기각(자문 §8). regime-conditional glasso 채택.
- **보고서가 엮는 관계도**: M2↔금리↔환율, 미-일 금리차↔엔캐리↔글로벌 유동성, 10Y-2Y 역전↔침체선행,
  HY OAS↔리스크오프. 이를 우리 FRED 17 시리즈로 번역(블록2).

## 2. ★실데이터 검증 (블록2~4, §2 작업순서 2단계) — 추상 단정 금지 충족

`data/historical_{2022,2023,2024}` 일별 6자산(sp500/nasdaq/dxy/gold/oil/us10y, **n=756일**)에
**내가 작성한 `RegimeGlasso`(core/structure/conditional_correlation.py)를 직접 적용**해 검증.
(raw/analysis_output.txt, raw/analyze_macro_relations.py)

### 발견 1 — regime-조건부 상관은 실재한다 (R15 핵심 thesis 입증)
rate-up(금리상승) vs rate-down 국면으로 분할 시 6쌍이 |Δ|>0.15:

| pair | full | rate-up | rate-down | Δ(up-dn) | 해석 |
|---|---|---|---|---|---|
| sp500~us10y | -0.10 | **-0.18** | **+0.09** | -0.26 | **2022 주식-채권 상관 부호 반전** — rate-up 에서 채권 분산효과 소멸 |
| gold~oil | +0.23 | +0.31 | +0.05 | +0.26 | rate-up(인플레) 국면 원자재 동조 강화 |
| nasdaq~us10y | -0.10 | -0.18 | +0.08 | -0.26 | 고듀레이션 tech 가 rate-up 에서 금리 페널티 |
| sp500~dxy | -0.36 | -0.43 | -0.19 | -0.24 | 달러-주식 역상관이 rate-up 에서 강화 |

→ **블록4 weight_rules 의 근거**: 국면별로 sleeve 분산가정·듀레이션 페널티를 재조정해야 한다.

### 발견 2 — glasso partial-corr 가 공통원인 매개를 분해한다 (자문 §8 입증)
전체상관(Pearson)과 partial-corr 차이로 "직접 vs 매개" 구분:

- **매개(공통원인)**: rate-up 국면 `nasdaq~dxy` Pearson **-0.40 → partial -0.04**(매개 0.36!),
  `sp500~dxy` -0.43 → -0.13(매개 0.31), `sp500~us10y` -0.18 → -0.01(매개 0.17).
  → 주식↔달러·주식↔금리 역상관은 **직접인과가 아니라 real-rate/dollar 공통원인 매개**.
- **직접 생존**: `dxy~us10y` partial +0.24~+0.27, `dxy~gold` -0.28~-0.31, `gold~us10y` -0.24~-0.29,
  `oil~us10y` +0.18~+0.27. → 이들이 **진짜 직접 엣지**(블록3 edge_type=direct, force-include 후보).

→ **블록3 의 conditioning_set 필수 명시**의 실증 근거. Block Matrix 가 아니라 conditional 모델이
맞다는 자문 §8 결론을 우리 데이터로 확인.

### 발견 3 — regime 신호는 평균이 아니라 공분산 구조에 있다
`effective_precision` belief-mix Σ_eff 데모: **dispersion=0, between_trace=0**. 일별 수익률은 양
regime 평균이 ≈0 이라 regime 간 *평균 이격*이 없다. 즉 macro regime 의 정보는 **공분산 구조(상관
반전)**에 있지 수익률 수준에 있지 않다. → 블록5 confidence_hooks 를 **DUAL**(score IC + Ω drift)로
설계한 이유. between-dispersion de-risk 는 level feature(금리·스프레드 수준)에서 활성화되지 daily
return 에선 약하다 — 이 한계를 블록7 inject 단계에 명시.

## 3. 4단계 코드 변경 계획 (블록7, §4 — 전부 Read 확인)

| 단계 | 파일 | 변경 핵심 | 무회귀 |
|---|---|---|---|
| learn | fred_adapter.py | real rate(DFII10)·JGB·M2 3시리즈 dict 추가 | 추가만 |
| learn | conditional_correlation.py | 블록3 direct 엣지를 corr_prior 주입(seam 이미 지원) | identity 폴백 |
| learn | train_weights.py | macro domain 배치 1건(forward return=downstream sleeve IC) | opt-in |
| card | weight_card.py | lens 정성필드(report_relations/regime_reading) 추가→judge 주입 | default 빈값 |
| inject | regime_to_weights.py | macro belief b(t)→_belief_conditional_cov wire (BL rf 스케일버그 ✅해소확인, 7/7 PASS) | opt-in |
| inject | judge.py | LLM judge 에 lens 주입, down-only 천장 불변식 보존 | 컨텍스트 추가만 |
| falsify | weight_falsification.py | 블록5 hook 5종 매핑(score IC e-CUSUM + Ω drift) | 함수 재사용 |
| falsify | update_controller.py | macro adopt dwell↑·K-window=2분기 | 파라미터만 |

## 4. confidence_hooks 핵심 (블록5 — 확신/거부 flag 코드화)

5개 가설 모두 **DUAL falsification** 에 매핑:
- PRIMARY(kill) = 합성 score OOS Rank-IC 의 anytime-valid e-CUSUM 단측 붕괴
  (`weight_falsification.score_ic_breakdown_eprocess`)
- SECONDARY(re-fit) = Ω 구조 drift(`omega_drift` + `needs_refit`)
- belief calibration = `conditional_correlation.TemperatureCalibrator`(내 모듈, frozen+hash-pin)

flag → 신뢰도(e-value/ECE) → 카드 `confidence_now` → `derive_weights` 재적합 → 동적 가중. 이 루프가
lens(estimation_note)까지 미세변동시킨다(§2 작업순서 3단계 = lens↔flag↔weight 한 루프).

## 5. 결정 / 기각 사유

- **채택**: regime-conditional glasso(conditional 모델). partial-corr 직접엣지 force-include.
  DUAL falsification. lens 카드 박제→judge 주입.
- **기각**: HMM/DCC(국면 외생, 자문 §8) / Block Matrix(소표본 과적합) / 일별 return 의 mean-dispersion
  de-risk(신호가 공분산에 있어 약함 — level feature 로 보완).

## 6. 막힌 점 / main 요청 (블록6)

- real rate(DFII10)·JGB·M2 시리즈 = FRED 무료, collector_plan 등록(즉시 가능).
- ECOS 한국 거시 = ECOS_API_KEY 대기(블록6).
- ✅ **inject 선결조건 해소 확인(2026-05-30)**: `regime_to_weights._bl_returns_path` 의 max_sharpe rf
  스케일버그(주기 return ↔ 연율 rf 불일치)는 이전 ④ 작업에서 `_periods_per_year` 연율화로 이미 해소됨
  (`tests/test_sleeve_belief_cov.py` 7/7 PASS 재확인). **추가 선결 없음 — macro belief wire production 가능.**
