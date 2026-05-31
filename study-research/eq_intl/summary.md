---
tags: [type/study-summary, domain/inv, study/eq_intl, phase/study-system]
date: 2026-05-30
study_id: eq_intl
asset_scope: equity.intl
note: 국가/지역 지수 ETF 스터디 요약 — study_session.yaml 7블록의 사람용 해설.
---

# eq_intl (국가지수 ETF) 스터디 요약

## 한 줄 결론

국가지수 ETF 는 **단일 종목 펀더멘털이 아니라 "국가 = 한 자산"의 매크로 민감도**로 평가한다.
unhedged ETF(EEM/EFA 등 대부분)의 달러표시 총수익은 `현지지수수익 + 환수익`이라, **환(달러
방향)이 1차 driver**다. 그래서 §6 단일종목 하드룰(valuation·quality 중심)을 그대로 쓰지 않고,
**macro_sensitivity(dollar·oil·rate·credit beta) 축에 더 큰 base 가중**을 두는 게 eq_intl 의 핵심 차별점.

## ① 투자 일반론 (lens 의 뿌리)

가격결정 직관식:
```
R_usd(국가i) ≈ β_global·(글로벌 risk-on) − β_usd·ΔDXY + β_commod·Δ원자재
              + β_rate·Δ(US real yield) + 국가 alpha(밸류·모멘텀·revision)
```
- 글로벌 위험선호가 **공통인자**, 거기에 국가별 (통화레짐 × 섹터구성 × 거시)이 곱해진다.
- 국가지수마다 섹터구성이 달라 같은 글로벌 사이클에도 반응이 다르다(대만·한국=반도체,
  브라질=원자재·금융, 인도=IT서비스·금융, 독일=산업재·자동차, 일본=수출).

## ② 투자 리포트가 엮어 보는 관계 (report_relations)

가장 강한 순서:
1. **달러(broad DXY)↑ → EM↓** (외화부채·자본유출·원자재압박). US real yield 고정해도 직접효과 잔존.
2. **US 10Y real yield↑ → EM 압박** + 달러강세의 공통원인(real yield→DXY→EM 매개).
3. **China credit impulse → 6~12m lag 원자재·원자재수출국 선행** (EM 사이클 marginal demand).
4. **risk-on/off(VIX·HY OAS) → EM 고베타** (risk-off 시 EM 이 가장 먼저·크게 하락).
5. **원자재가격 ↔ 수출국 terms-of-trade** (LatAm·자원국 양 / 인도·한국·일본 반대).
6. **엔 약세 → 일본 수출주 EPS↑ but unhedged USD 투자자 환손실** (헤지/언헤지 분기).
7. **cross-country value(CAPE 스프레드)** + **cross-country momentum(12-1, AQR 최강 횡단면)** 병용.

## ③④ 우리 자료로 번역 + 과거 대조 (정직한 데이터 상태)

⚠️ **추상 단정 금지 원칙 준수**: lens 가설의 실제 IC 대조는 **국가-ETF TR 수익 패널이 있어야**
가능한데, 이건 현재 우리 시스템에 **없다**(블록6 1순위 요청). 그래서 블록3 관계는 IC 로 확정된
것이 아니라 **이론 prior(theory_basis 부착)** 로 제출했다. 데이터 도착 후 블록5 flag 로 검증된다.

현재 가용 substrate 와 갭:
- **있음**: FRED macro(T10Y2Y·HY OAS·real_gdp 등 16종), main 선구축 DXY/USDKRW(FxStore 일부),
  UniverseStore(ETF holdings 골격).
- **★갭 발견(중요)**: `core/brain/fred_adapter.py` FRED_SERIES 에 **broad dollar index(DTWEXBGS)
  도, oil(DCOILWTICO)도, 10Y real yield(DFII10)도 없다.** eq_intl 1차 driver 가 데이터에 부재 →
  블록6 요청 + 블록7 learn 단계에서 FRED_SERIES dict 에 3줄 추가가 첫 작업.
- **없음→블록6**: 국가ETF TR 패널, 다국가 환율(FxStore 확장), 지수집계 펀더멘털(forward E/P·ROE·
  revision breadth), China credit impulse, terms-of-trade, EM flow, sovereign CDS.

## 핵심 설계 결정 (그리고 기각/보류)

- **결정: dollar_beta base_weight 를 0.22 로 최상위** (단일종목 §6 코어셋엔 macro beta 가 보조축인데,
  eq_intl 은 환 지배 anchor 때문에 macro_sensitivity 를 1차축으로 승격). 이 anchor 는 박제가 아니라
  블록5 `dollar_dominance_anchor` flag 로 검증 — 달러지배가 풀리면 모멘텀/밸류로 base_weight 재배분.
- **결정: 국가 archetype soft membership** (commodity_exporter / tech_exporter / domestic_demand /
  dm_europe / dm_japan / em_china). 한 국가가 복수 archetype 에 soft 소속(π). 부록B hierarchical
  pooling 으로 `composed_weights(pi)` 의 `delta_arch_by_type` 에 매핑 — 종목(국가)단위 obs 부족을 회피.
- **보류→main 요청: fx(환) sleeve 승격**. unhedged ETF 에서 환은 1차 driver 인데 is_core:false cap(0.04)
  으로 부당캡된다. §6 3-test(부호상충/조건부상관 decoupling/신호스택 발산) 중 1+ 통과 AND uncapped
  IC 유의 시 main 에 `intl_fx` sleeve 승격 요청(블록5 fx_sleeve_promotion hook + 블록6 fx 확장 선행).
- **결정: momentum 은 regime 가변** — risk-on 추세에 가중↑, risk-off 전환점에 가중↓(momentum crash 회피).
- **아키텍처(§8 준수)**: cglasso 조건부 모델. 거시 named 채널 = **dollar/real_rate/oil/credit**(eq_intl
  은 단일종목 대비 dollar·oil 채널 비중을 키움). 관계는 partial-corr(공통원인 분해): EM-dollar 는
  real yield 공통원인 분해 후 잔차, oil-수출국지수는 China 공통원인 분해 후 잔차.
- **force-include 후보(이론 최강 ≤4)**: dollar_beta↔momentum(음), credit_beta↔realized_vol(양).

## §4 4단계 코드 연결 (블록7 요약 — 실제 Read 근거)

| 단계 | 파일:심볼 | eq_intl 변경 핵심 |
|---|---|---|
| learn | `fred_adapter.FRED_SERIES` | DTWEXBGS·DCOILWTICO·DFII10 3줄 추가(현재 부재) |
| learn | `weight_panel.build_indicator_matrix` | 국가지표 series_ids 등록(반사성 게이트 통과 확인) |
| learn | `conditional_correlation.RegimeGlasso(corr_prior)` | 블록3 partial-corr prior 주입, ≤4 force-include |
| card | `weight_card.composed_weights(pi)` | 국가 archetype → delta_arch_by_type soft 혼합 + lens 정성필드 |
| card | `registry` | id 규약 `weight.equity.intl.{regime}` |
| inject | `stock_track._extract_indicator_z/_resolve_weight_card` | 국가지표 z 추출 + scope 분기 + _regime_pi archetype |
| inject | `regime_to_weights.SLEEVES` | ★`intl_stock` sleeve 신규(현재 부재) — 자산배분 회귀 민감, opt-in 도입 |
| inject | `judge` | LLM 컨텍스트에 lens 주입(down-only 보존) |
| falsify | `weight_falsification.score_ic_breakdown_eprocess` | confidence_hooks 매핑(IC유지/e-CUSUM붕괴), archetype 서브패밀리 분해 |
| falsify | `update_controller.step` | 환 anchor=느린 adopt dwell / momentum crash=빠른 retract |

## §5 실측 대조 결과 (2026-05-30, Yahoo 5y daily)

> raw: `study-research/eq_intl/raw/yahoo_cache/{symbol}.csv` (18 series × 1255 daily obs) + `raw/analysis-output.txt`.
> 분석 스크립트: `raw/analyze.py`. universe: SPY + 12 국가ETF + DXY/WTI/VIX. monthly_obs=59.

### H1. DXY ↔ 국가 ETF 일별 log-return 상관 (prior: 음수)

| group | country | pearson | spearman |
|---|---|---:|---:|
| baseline | us_spy | -0.233 | -0.265 |
| DM broad | dm_exus | **-0.541** | -0.557 |
| DM broad | europe | **-0.569** | **-0.570** |
| DM single | japan | -0.381 | -0.415 |
| DM single | germany | **-0.548** | -0.536 |
| DM single | uk | -0.523 | -0.522 |
| EM broad | em_broad | -0.426 | -0.447 |
| EM single | brazil | -0.286 | -0.307 |
| EM single | india | -0.302 | -0.328 |
| EM single | china | -0.294 | -0.309 |
| EM single | korea | -0.390 | -0.407 |

**결론**: 부호 prior 강확인. **단 통념 부분 기각** — DM Europe(germany/uk/europe/dm_exus, |corr|>0.52)이 EM(brazil/india/china, |corr|~0.29)보다 dollar-sensitive **더 강함**. → block5 `dollar_dominance_anchor` EARLY_ADOPT + 새 발견 `dm_europe_dollar_dominance_strongest`.

### H2. VIX ↔ 국가 ETF 일별 (prior: 음수, EM 더 강함)

| group | country | pearson |
|---|---|---:|
| baseline | us_spy | **-0.764** |
| DM broad | dm_exus | -0.651 |
| DM broad | europe | -0.608 |
| EM broad | em_broad | -0.571 |
| EM single | china | -0.331 |
| EM single | brazil | -0.432 |
| EM single | korea | -0.487 |

**결론**: 부호 강확인, **EM 더 강함 prior 부분 기각**. SPY(-0.76)가 mechanical 1위(VIX=SPX 옵션 IV). EM 의 risk-off 베타는 DM Europe 보다 오히려 약함. → 새 발견 `em_partial_decoupling_2021_2026`. ★ caveat: VIX proxy 한계 — HY OAS(BAMLH0A0HYM2) 직접 시험 필요.

### H3. WTI ↔ 국가 ETF 일별 (commodity exporter 양수 prior)

| country | pearson | archetype prior |
|---|---:|---|
| brazil | **+0.123** | commodity_exporter (양수 prior ✓) |
| uk | +0.123 | dm_europe + 에너지섹터 |
| mexico | +0.059 | commodity_exporter (약하게 양수) |
| germany | -0.031 | dm_europe + 수입국 (음수 부분 일치) |
| india | -0.064 | domestic_demand + 수입국 (음수 ✓) |
| korea | -0.046 | tech_exporter + 수입국 (음수 ✓) |

**결론**: 부호는 archetype prior 부분 일치, **강도는 미미** (|corr|<0.15). → block5 `commodity_exporter_oil_link` NEEDS_DATA. ★ FRED DCOILWTICO + 월별 lag 분석 + China credit impulse 결합 후 재평가.

### H4. Regime 분해 (VIX>25 risk-off / ≤25 risk-on, 월별 DXY↔국가 ETF)

| country | risk-on (n=51) | risk-off (n=8) | regime amplification |
|---|---:|---:|---|
| em_broad | -0.640 | **-0.796** | ✓ 강화 |
| japan | -0.608 | **-0.901** | ✓ 강화 |
| korea | -0.405 | **-0.770** | ✓ 강화 |
| brazil | -0.506 | -0.456 | 변화 미미 |
| china | -0.541 | **+0.033** | ★ **반전** (capital controls?) |
| europe | -0.769 | -0.755 | 안정 (regime 무관) |

**결론**: regime-conditional dollar-EM coupling **강확인**. ★ china 의 risk-off 시 dollar-coupling **소실**(+0.033) = china 별도 sub-archetype 가치. japan/korea/em_broad 는 prior 일치 강화. → block4 regime_conditional modulators (risk_off_amplification) 강한 지지.

### H5. Cross-country macro betas (월별 univariate OLS, n=59)

| country | dxy_β | R² | oil_β | vix_β |
|---|---:|---:|---:|---:|
| korea | **-2.305** | 0.22 | -0.102 | -0.176 |
| germany | -2.151 | 0.57 | -0.071 | -0.154 |
| brazil | -1.840 | 0.24 | +0.083 | -0.094 |
| europe | -1.808 | 0.57 | -0.038 | -0.136 |
| china | -1.714 | 0.19 | +0.006 | -0.040 |
| mexico | -1.692 | 0.31 | -0.026 | -0.132 |
| dm_exus | -1.663 | 0.58 | -0.042 | -0.124 |
| india | -0.803 | 0.17 | -0.094 | -0.072 |

**결론**: dxy_β 압도적 1순위 driver (R² mean ~0.30, DM 0.55+). oil_β/vix_β 미미. → block4 `dollar_beta_country base_weight=0.22` 유지/강화. `oil_beta_country` 0.12→**0.08 하향**.

### H6. 12-1m momentum → next-month return Rank-IC (cross-country, n_months=46)

| metric | value |
|---|---:|
| mean IC | +0.0149 |
| median IC | 0.0000 |
| std | 0.398 |
| IC>0 ratio | 50.00% |
| IC-IR (ann.) | +0.13 |

**결론**: 5y 기간 cross-country momentum **무력화**. AQR prior(IC-IR 0.5+ 통상)와 큰 격차. 기간 의존성 큼 (2021-2026 = 코비드/인플레/금리 cycle 3개 = regime 안정성 낮음). → block4 `mom_12_1_country base_weight` 0.18→**0.12 하향** + block5 `momentum_crash_regime` CAUTION. ★ regime 가변 anchor 의 검증은 별도 데이터 필요 (risk-on 만 분리한 momentum IC 미실시).

### H7~H8. Force_include 후보 cross-section 검증

| 가설 | prior | 실측 (pearson / spearman, n=12) | 판정 |
|---|---|---:|---|
| H7. dxy_beta ↔ mom (force_include #1, neg) | -0.50 | **-0.265 / -0.105** | 부호 ✓ 강도 약 → prior_strength 0.50→**0.30** |
| H8. vix_beta ↔ realized_vol (force_include #2, pos) | +0.60 | **+0.055 / -0.098** | 거의 0 → prior_strength 0.60→**0.35** (vix_beta 분해능 부족, HY OAS 직접 시험 필수) |

### 종합 prior 갱신 표

| 항목 | 변경 전 | 변경 후 | 근거 |
|---|---|---|---|
| block4 mom_12_1 base_weight | 0.18 | **0.12** | H6 IC-IR +0.13 |
| block4 oil_beta base_weight | 0.12 | **0.08** | H3 일별 |corr|<0.15 / H5 월별 R²<0.06 |
| block3 dollar-mom prior_strength | 0.50 | **0.30** | H7 -0.27 (강도 약) |
| block3 credit-vol prior_strength | 0.60 | **0.35** | H8 +0.06 (vix proxy 5y 분해능 부족) |
| block4 dollar_beta base_weight | 0.22 | **유지** | H1/H5 강확인 |
| block5 dollar_dominance_anchor | (초기) | **EARLY_ADOPT** | H1+H4+H5 강확인 |
| block5 momentum_crash_regime | (초기) | **CAUTION** | H6 무력화 |
| block5 commodity_exporter_oil_link | (초기) | **NEEDS_DATA** | H3 약·부호만 일치 |
| block5 fx_sleeve_promotion | (초기) | **PENDING** | FxStore 다국가 미확장 |
| 새 발견 dm_europe_strongest | — | **추가** | H1+H5 DM Europe dxy 최강 |
| 새 발견 em_partial_decoupling | — | **추가** | H2/H4 china risk-off 반전 |

## main 에 넘기는 3가지

1. **데이터 요청(블록6 우선순위)**: ① 국가ETF TR 패널(무료, FinanceDataReader) ② FRED 3시리즈
   추가(dollar/oil/real yield, 무료) ③ 다국가 FxStore 확장. 이 셋이 있어야 lens IC 대조가 가능.
2. **sleeve 의사결정**: `intl_stock` sleeve 신규 등록(SLEEVES 회귀 민감 — BASE_WEIGHTS 재정규화).
   + 조건부 `intl_fx` sleeve 승격(3-test 통과 시).
3. **검증 보류 명시**: 블록3 관계·블록4 가중은 **이론 prior** 단계. 데이터 도착 후 블록5 flag 루프로
   IC 검증해야 production 확정. 지금은 "있다 전제로 멈추지 않고" 설계까지 완성한 상태.
