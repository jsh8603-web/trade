---
tags: [type/design-draft, domain/inv, topic/equity-dynamic-weight, phase/M6]
date: 2026-05-30
note: 주식 sleeve 산업×regime 동적 평가지표 가중 설계 초안. ★출처=main opus subagent 1회 산출(사용자 의도=주식 담당 세션이 산업별 subagent로 작업이므로 본 초안은 각 세션 검증의 출발점·참고자료로만, main 확정 아님). 핵심=①sleeve 버그 코드 레벨 미해결(regime_to_weights.SLEEVES 단일) ②FRED 1차 driver 미등록 ③lead 주장 대부분 reject→contemp risk-gate만.
status: draft — 세션 검증 대상(eq_us_cyclical/defensive/intl/kr 담당 세션이 산업별 실데이터로 confirm/reject)
---

# 주식 sleeve 산업×regime 동적 평가지표 가중 — 설계 초안 (세션 검증용 참고)

> ★본 초안은 main subagent 1회 산출이다. 사용자 의도대로 **각 주식 담당 세션이 산업별 subagent로 실데이터 검증·구현**한다. 점추정 박제 금지, 검증관 3-tier+James-Stein 전제. 살아남는 건 세션의 OOS 실측을 통과한 것만.

## 0. 핵심 진단 (코드·yaml 실측 후)
weight_card 구조(`composed_weights = w_global + δ_regime + δ_arch + δ_inter` + soft archetype π + Grinold Ω·IC + capped-simplex)는 구조적으로 충분. 문제는 **충전 상태 비대칭**.

| sleeve | δ_regime/δ_arch 실측 충전 | sleeve 분류 정확성 | critical 지표 완전성 |
|---|---|---|---|
| eq_us_defensive | 실측 anchor 충전(H1 IC −0.167/+0.129 n=5844, M3 dollar) | **버그**(방어+금융 한 sleeve) | quality/VIX term 누락 |
| eq_us_cyclical | 부분(H4 VIX −0.378 실측, backbone H1/H6 DEFERRED) | sleeve 미정의(us_stock sub-panel) | revision breadth 누락 |
| eq_intl | 강(dollar Bonferroni 12/12, China R² gap +0.466) | archetype 분해 정밀 | carry/credit impulse 미수집 |
| eq_kr | **미충전**(v2 yaml 부재, round-1만) | 정의 안 됨 | 다수 collector 의존 |

★가장 중요 — **자문 #1 sleeve 버그가 코드 레벨 미해결**. `regime_to_weights.py` SLEEVES=`us_stock` 단일, eq_us_defensive yaml이 XLP·XLU·XLV·XLF·XLC를 한 study sleeve로 묶고 `delta_arch_by_type`(5 archetype)로만 분해. yaml은 H1 sign-split 실측으로 잡았으나(XLU rate IC −0.167 vs XLF +0.129) sleeve 자체는 미분리. δ_arch 분해는 한 카드 내 archetype별 δ만 다르게 줄 뿐, sleeve 레벨 거시 부호 상쇄(XLU rate-음 + XLF rate-양)를 카드 합성 단계에서 못 막음.

## 1. 산업 사이클별 거시 민감도 — robust vs 과적합

### 1.1 robust (실증·학술 동시 지지 → δ 충전 우선)
| 효과 | 증거 | 판정 |
|---|---|---|
| rate(real yield) → bond-proxy 음 / banks 양 | XLU −0.167 / XLF +0.129 (n=5844, p<1e-4) + Ilmanen·Boyd-Gertler | ★validated. δ_arch sign-split anchor |
| dollar → ex-US equity 음 | eq_intl Bonferroni 12/12 (\|t\|=9.87~23.96), ratio 107x | ★validated 강 |
| VIX/risk-shock → cyclical−defensive excess(동시) | VIX\|IG IC −0.343, cyclical excess −0.378 | ★validated, 단 lead 부재=contemp risk-gate only |
| Asset Growth/CMA → fwd return 음 | Cooper-Gulen-Schill 2008 JF, Titman-Wei-Xie 2004 | structural(학술 강, OOS 미검증) |
| country momentum 12-1 | AQR — 단 5y IC +0.015, IC>0 50% | 과적합 경계: base 축소+regime gate |

### 1.2 reject / 과적합 (실측이 깸 → δ 충전 금지)
- Investment Clock ground truth 금지(배분 prior로만, 자문·yaml 강등 확정).
- ISM/PMI sector lead(cyclical): H3 REJECT(lead IC<0.10 at 316M). base cap 0.04.
- Yield-curve → NIM 3-6M lag(Stigum): H2 REJECT, contemp lag=0만 유효.
- HY OAS → defensive outperform(BAB): H3 REVERSED(Credit regime sleeve excess −1.5%/월, p=0.005, 단 n=9 소표본). modern QE 무효 → Credit regime 시 *축소*.
- rate_beta name-specific sign split(cyclical): H5 REJECT(모든 섹터 β>0), EDGAR 적재 전 보류.

★원칙: lead 주장(거시→종목 미래예측)은 대부분 깨짐. 살아남은 건 contemporaneous risk-gate(VIX·credit·dollar 동시 베타) + cross-sectional 펀더 anomaly(CMA·quality). 자문 #3 정합(거시=배분 A 전담, 종목 B=펀더멘털+down-only risk-gate).

## 2. sleeve별 산출 (요약 — 상세는 세션이 실측)

### 2A. eq_us_defensive → ★financials 독립 분리 권고
- 누락 보완: quality/earnings_stability(EDGAR), VIX term structure(yfinance ^VIX/^VIX3M), rate/dollar/slope FRED 등록.
- **sleeve 재분류**: `eq_us_financials` 신설(XLF를 defensive에서 분리, rate 양·credit 음·pro-cyclical). 근거: H1에서 XLF만 rate 부호 반대, H4a gap +0.257=sleeve 평균 상쇄로 식별력 죽음. breadth 충분(은행·보험·자산운용·결제) → 독립 IR 손실 없음. 잔여 defensive=XLP·XLU·XLV(rate 부호 동일 음, δ_arch 3종 유지로 충분).
- 코드: `regime_to_weights.SLEEVES`에 `us_financials` 추가(BASE_WEIGHTS 재정규화=회귀 민감, opt-in+무회귀 self-test).
- 과적합: δ_regime 2국면(rate-up/down + credit-stress overlay)으로 제한, 4국면은 shrinkage overlay. n<30(Credit n=9, epoch n=4) Bootstrap+CI 필수.

### 2B. eq_us_cyclical → sleeve 정의 + backbone 적재 병목
- VIX(−0.378 최강 실측)·CMA·valuation backbone 충전, 누락=forward EPS revision breadth(FINNHUB/EDGAR). ism_pmi cap 0.04(H3 REJECT).
- sleeve=팩터노출 정의(GDP 탄력+레버리지+dollar/oil/credit 양 베타). us_stock을 cyclical/defensive/financials 3-way 분할.
- 과적합: δ_inter 희소화(빈 tuple=0 강등), Grinold Ω 다중공선 감액, 1/N 0.30, cap 0.40, backbone DEFERRED 동안 fwd_ep base=0 잠금.
- 우선순위: collector=EDGAR 분기 펀더+Damodaran ERP(우선순위 1, 없으면 cyclical 골격 미입증).

### 2C. eq_intl → 잘 설계됨, sleeve 추가만
- 누락=상대 이익모멘텀·forward PE갭·carry·china credit impulse(대부분 미수집). archetype(commodity_exporter/tech_exporter/dm_europe/em_china/domestic) × regime, soft π 혼합으로 hard 분할 회피.
- `intl_stock` sleeve 신규(regime_to_weights 부재, opt-in). dollar=DTWEXBGS/oil=DCOILWTICO/real=DFII10 FRED 등록 + 국가 ETF TR(FinanceDataReader). China AH Premium(무료 ★★★).
- ★R²↔유의성 혼동 금지: EM 낮은 R²=잔차분산 큼, "EM 약가중" R² 근거 금지.

### 2D. eq_kr → v2 yaml 미작성, 실측 0, 최하 우선순위
- 자문 지표(USD/KRW>외국인 flow>중국 credit impulse>수출/반도체)는 **가설 단계**, 실측 전 박제 금지. 데이터: USDKRW(FxStore✅), 외국인 flow(KrxForeignFlowProvider✅), DART(key 부재 graceful), DRAM proxy($MU/SOX).
- 즉시 가능=H1(외국인 flow→fwd return IC)/H5(momentum 약효)/H7(risk-off 동조), numpy 직접. 공매도 레짐 분할 백테스트 구간 분리 필수.
- KOSPI(외국인주도) vs KOSDAQ(개인주도) archetype 분해(sleeve 분리보다).

## 3. 공통 구현 우선순위
**즉시(데이터 보유+무회귀)**: ①FRED_SERIES에 DFII10·DTWEXBGS·DCOILWTICO·DGS10·DGS2 추가(`fred_adapter.py`, 무료 ALFRED, dict 추가만) ②eq_us_financials sleeve 분리(회귀 민감, opt-in+self-test) ③eq_kr H1/H5/H7 실측 IC(numpy).
**collector 의존**: ④EDGAR 분기 펀더+Damodaran ERP(cyclical backbone) ⑤국가 ETF TR+China AH ⑥revision breadth·EPFR·MSCI(유료→프록시).

## 4. 차원 폭발 통제 (자문 #4)
weight_card 내장 방어: hierarchical partial pooling(δ_inter 얇으면 0 강등), James-Stein shrinkage(4국면→2 testable+shrinkage overlay, OOS power 없으면 2국면 붕괴), Grinold Ω 다중공선 감액, 1/N 0.30+cap 0.40, 검증관 3-tier(validated/structural/reject, 점추정 금지·anytime-valid e-process falsifiable).

★미해결 리스크: eq_us_defensive yaml은 H1 sign-split 잡았으나 sleeve 분리는 yaml 권고만, `regime_to_weights.SLEEVES` 코드 미반영. **financials sleeve 코드 분리가 버그의 유일 근본 해결**(단 sleeve 분리 OOS IR 비교 검증 전까지 단정 아님).
