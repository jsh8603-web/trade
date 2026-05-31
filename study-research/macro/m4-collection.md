---
tags: [type/m4-collection, domain/inv, study/macro, phase/M4]
date: 2026-05-30
phase: "M4 수집판 — 6개 종목 세션 M3 거시연관 핵심 누적 → main 종합"
note: 상관 높아 거시 판단에 가치있는 지표를 거시 레이어 반영 판단. ★불변식 U3(belief→_macro 차단) + L축(factor_implied 공통팩터 1회계상) 유지.
---

# M4 수집판 — 종목별 M3 거시연관 핵심 (main 종합용)

> 6개 yaml 완료 세션 M3 답신 수집 → 상관 높은 지표를 거시 레이어(MacroView consensus / factor 베타 prior)에 반영 판단.
> ★종목 belief 가 _macro 에 직접 새지 않게 U3 level 가드 경유. cross-sleeve 공통팩터(rate/dollar/oil)는 factor_implied 1회계상.

## 수집 현황 (6/?)
| 세션 | study | 상태 | tier |
|---|---|---|---|
| btn-jsh86 | gold | ✅ 수신 | SUPPORTED |
| btn-common-task | eq_us_cyclical | ✅ 수신 | SUPPORTED (yaml v3 보강안 有) |
| btn-excel | eq_intl | ✅ 검증완료 | 부분충실 **B−→A−**(추론통계 Bonferroni 12/12 박제 이행, EM-idio·rate증폭 격하 완료. 수치 재확인=register L축 점검 시) |
| btn-jpdf | commodity | ✅ 완료 | yaml final, SLEEVE_BLOC A 확정(block7 박제), register 가능 |
| btn-DA | eq_us_defensive | ✅ 검증완료 | **불충실 Tier3**(H3 데이터 커버리지 위조급·dollar regime-switch 비유의 / seed HOLD 유지) |
| btn-GCP | reit | ✅ 수신(compact 재개) | 검증 중 |

---

## gold (btn-jsh86) ✅
- **경로**: study-research/gold/raw/macro-linkage-M3.md (+m3_result.json +analyze-m3-macro-linkage.py). 실데이터 n=1216(2021-10~2026-05), ⛔합성0, PIT/OOS, 12축 자가검증.
- **핵심 상관(Pearson)**: gold↔broad TWI **−0.378**(1차) > DXY −0.348 > Δus10y −0.281 > oil +0.103
- **driver loading(std β)**: dollar **−0.328** > rate −0.295 > oil +0.230 (M1 dollar 채널 우위 정합)
- **★epoch-conditional**: E4(2023Q4-2024Q4 인하) rate loading **−0.142** = 타 epoch(−0.30~−0.36)의 절반 = rate-gold 수준관계 epoch-한정 붕괴 = gold study **H2(level intercept shift)의 직접 mechanism**. dollar 채널은 유지(−0.306).
- **M1 가설 대비**: "rate-up 시 dollar 2배" gold 미발현(dollar −0.26 vs −0.28) → gold 국면조건성 = epoch(시간)이 본질, rate-direction 아님.
- **epoch ann return**: E1 −12.9%(Sharpe −0.90) / E2 +18.4% / E3 −15.1% / E4 +26.6%(Sharpe +1.82)
- **★M4 후보**: ①broad TWI(dollar 채널 대표, DXY보다 강) 거시 레이어 driver 채택 ②epoch-conditional rate loading(인하 epoch rate 약화) regime 식별 신호.
- **🔍 독립 검증 verdict(opus, raw 재실행)**: **충실**(provenance 100% 일치 소수점까지, 실데이터 확정 — kurtosis 7.1·이벤트 실재 2013-04-15 −9.2%). **validated**=dollar β −0.328>rate −0.295(t −10/−9 강건)·cross-asset 4건·epoch 수익/Sharpe. **structural prior**=E4 rate decoupling "절반"(점추정·다중검정 미보정→방향성만, 인과 단정 금지). DXY ffill 261행=2025-06 이후 상수(현 결론 무영향). **M4 반영=가: dollar 채널 즉시 안착, E4 decoupling은 약 라벨(OOS 진행중)**.

## eq_us_cyclical (btn-common-task) ✅
- **경로**: study-research/eq_us_cyclical/raw/m3-findings.md (+m3-metrics.json +m3_output.txt).
- **핵심 상관**: ★rate<dollar 1자리차 — β_dxy −0.58~−1.62 vs β_us10y ~0(XLE 제외). M1 dollar 채널 강하게 재확인.
- **국면조건부 dollar**: E1 R²0.21/β−1.34 · E2 0.29/−1.12 · E3 0.13/−0.40 · E4 0.07/−0.51 = 긴축·전환기 dollar 최강.
- **★L축 실측(2번째)**: Kish eff_N=**1.47**(within-cyc mean corr 0.617) = within-sleeve 거의 단일자유도 → cross-asset 차원만 거시 1회계상 유효. **M1 caveat 정량 확인(gold에 이어)**.
- **XLE 분리 권고**: oil rank-IC +0.602 압도, anti-cyclical hedge(E1 +47.9% · E3 +18.0% 역행) → XLE를 cyclical에서 별 archetype 분리.
- **Sharpe**: E1 −1.11 / E2 +1.63 / E3 −1.60 / E4 +1.75 (전환·완화 epoch 보상).
- **별도(main 검토 대기)**: yaml v3 보강안 §4 5건 + D·G축(ALFRED/Driscoll-Kraay) main 인프라 의존.
- **★M4 후보**: dollar 채널 1차 driver 재확인 + epoch별 dollar 강도(긴축·전환 최강) + XLE oil-driven 분리.
- **🔍 독립 검증 verdict(opus, raw 재실행)**: **충실 tier A−**(provenance byte-identical + 실데이터 + ★검정력 입증 **β_dxy t=−11.04, |t_dxy|≈4×|t_us10y|** → dollar≫rate, HAC 보정해도 생존 + Kish eff_N 1.47 독립 재계산 정합). 경미한 흠: period 표기 2024-12-31↔실제 macro end 2024-12-04(무영향), D축 OOS·K축 다중검정 미수행(정직 명시). **M4 반영=가(조건부: period 정정, D·K 미해결 상속 명기)**.

## eq_intl (btn-excel) ✅
- **경로**: study-research/eq_intl/macro-linkage.md (+raw/macro_linkage.py +output.txt). 5y daily, PIT 종가, 합성X.
- **핵심**: R² ETF별 — **europe 0.33 max**(DM Europe 거시 frame 1순위) / brazil·china ≤0.10(EM idio dominant, H5 재정의 정합).
- **★dollar 채널 dominance verified** — block5 새 hypothesis `m1_dollar_channel_dominance_verified`, block6 ^TNX 가용 추가.
- **★M4 후보**: DM(europe) = 거시 frame 강(1차) / EM(brazil·china) = idio dominant → 거시 레이어는 DM에 강하게, EM은 약하게 가중.
- **🔍 독립 검증 verdict(opus, raw 재실행)**: provenance **완전일치**(europe R²0.330·germany β_dollar−1.6824 bit-identical) + 합성0(yahoo 21CSV float64 실범위 DXY 89.8~114.1·^TNX 1.17~4.99). ★**EM idio dominance = REJECT(R²↔유의성 혼동 오해석)** — china/brazil 도 β_dollar robust **t=−9.0/−7.6 (p~1e-19/1e-14)** 전 12국 Bonferroni 생존, 낮은 R²=잔차분산 큼이지 "거시 안통함" 아님(commodity n=12 p=0.16 함정의 **반대** 케이스). ★**rate-up dollar 증폭 = REJECT** — up/dn β_dollar 차 **\|t\|<1.96 0/12 유의**, M1 "2배" 가설 eq_intl 서 순수 노이즈로 기각. **validated_alpha**=dollar dominance(sleeve β_dollar≈−1.26, corr −0.41, magnitude 107× rate). β_rate≈0 직접무력. **tier=B−**(실데이터·재현 A급 / md 가 t·p·CI **전무 보고**→R² 오해석 유발 = 추론통계 부재가 핵심결함). **판정=부분충실**. **M4 반영=조건부 가**: ①dollar=eq_intl 1차 driver 가(전 12국 robust) ②⛔**EM 약가중 박제하려면 R² 근거 폐기**(dollar β 는 DM 동급 유의 — "idio 비중 큼=잔차분산 큼" 별근거로만 정당화) ③⛔**rate-up 증폭 M4 박제 금지**(비유의 기각, dollar dominance 만 verified 등재) ④country별 점추정 β 개별 covariance prior 박제 금지, **sleeve-avg β_dollar≈−1.26 만 robust prior**.

## commodity (btn-jpdf) ✅
- **경로**: study-research/commodity/macro-linkage.md. n=12 분기.
- **핵심 dollar 채널**: industrial DXY corr **−0.643** / precious_non_gold **−0.432** (M1 dollar 채널 정합). energy = oil shock-driven(긴축 +10.93%, rate-UP +6.07% vs rate-DOWN −18.74%). agri R²=0.076(idiosyncratic 확정).
- **★cross-sleeve 발견**: industrial↔precious_non_gold **+0.756**(둘 다 dollar-sensitive) / energy↔industrial −0.145(음 → cyclical bloc 재검토).
- **yaml 3건 반영**: H4/H7 latest_vintage_provisional 라벨, H4 prior_tier=structural_low_confidence+validated_alpha=false, block7 archetype pooling 정정(sub_sleeve add-only). L축은 yaml 미수정(main PSD 점검).
- **★main 결정 대기**: SLEEVE_BLOC 옵션 A(유지+caveat) vs B(dollar_sensitive/supply_shock/idiosyncratic 3-bloc 재분류). register 진입 가능.
- **★M4 후보**: dollar-sensitive bloc(industrial+precious) 공통 driver / energy oil-driven 분리 / agri idio 제외.
- **🔍 독립 검증 verdict(opus, raw 재실행)**: provenance ✅ 완전일치(합성無). ★**precious↔DXY −0.432 = n=12 비유의**(p=0.16, CI[−0.81,+0.19] 0포함) → md "dollar 최강음" 단정 과대, **M4 전 "방향성 약 prior(비유의)"로 격하 필수**. industrial↔DXY −0.643만 유의(p=0.024, CI 거의 0까지). **+0.756 = Bonferroni 후 유일 생존**(p=0.0045), DXY 통제 후 부분상관 **+0.692 = dollar 잔차 공통(산업수요)** → factor 1회계상으로 흡수 안 됨. **tier=structural prior 저신뢰. 판정=부분충실. M4 반영=조건부(방향성만, ⛔점추정 계수 −0.643/−0.432/+0.756 을 covariance prior 로 박제 금지, 넓은 CI 약 prior 로만)**. ★**SLEEVE_BLOC: 검증관 B(재분류) 권고 — 내 잠정 A 는 차선**(energy↔industrial −0.145 = p=0.65 순수잡음, cyclical 묶음 통계근거 없음). M4 종합서 재결정.

## reit (btn-GCP) ✅ [검증 충실]
- **경로**: study-research/reit/raw/m3-macro-linkage.md (+scripts/m3_macro_linkage.py). yfinance VNQ+9 + FRED DGS10/DXY/WTI, n=753 daily, 합성無 U3준수.
- **🔍 독립 검증 verdict(opus, raw 재실행)**: **충실**(provenance 완전일치 + 독립 re-fetch OLS 재현 + 합성無). ★**3 driver(rate/dollar/oil) 정상 포함**(핸드오프 "rate-only 누락" 우려 기각, 스크립트 DXY+WTI fetch 확인). ★**VNQ rate 직접 loading −3.82(t−5.65, 9/10 음수 유의)=주식(rate≈0)과 명확히 다름**. dollar −0.84(주식 동급). within ρ=0.55=sector effect. tier=중신뢰(전체·E1·E4 headline 중~고, E2/E3 미세부호 저). **M4 반영=가**.
- **★M4 후보**: REIT rate 직접 민감(주식 차별) + dollar 채널 + sector 단위 sleeve 모델.

## eq_us_defensive (btn-DA) ✅ [검증 불충실 — 신뢰 못 함, seed HOLD 유지]
- **경로**: study-research/eq_us_defensive/raw/m3-macro-linkage.md (+validation-H1~H4.md, run_validation.py, fred 9+yfinance 2 panel).
- **🔍 독립 검증 verdict(opus, raw 재실행)**: provenance 완전일치(B/C 합격, 합성0·v1 `_deprecated_` 격리) **BUT 해석 불충실(Tier 3)**.
  - ★**H3 "REVERSED 2000-2026 / 2008 GFC" = 데이터 커버리지 위조급**: HY OAS CSV가 **2023-05~2026-05(37개월)뿐**인데 md 는 "n=317월·2008 GFC XLF−55%·308 Normal" 서사로 robustness 주장 = 허구. `classify_regime` 이 pre-2023(HY 없는 월)을 KeyError→credit=False 로 308월 "Normal" 오분류, 2008·2020·2022 신용위기 표본 **부재**. "n=9 credit"=2023-05~12 연속8월+2025-04 단발=episode 2개. 모수 t **p=0.0503(경계미달)**, bootstrap p=0.005 는 IID resampling(연속월 자기상관 무시), LOO **5/9월 제거 시 p>0.05 붕괴** → **reject**(commodity precious↔DXY p=0.16 동일 함정).
  - ★**dollar regime-switch(XLU β_dxy +0.57 E3 vs −0.18 E4) = 비유의**: z=1.34 **p_diff=0.18**, E3 n=63일 SE0.54 → 95%CI[−0.5,+1.6] 0포함. pooled interaction XLU p=0.22/XLP p=0.57/XLF p=0.30 n.s., XLV만 p=0.013(4중1=다중비교 노이즈) → reject(eq_intl rate증폭 0/12 기각 동일패턴). md "M1 강력확인·dollar 2배"=과대.
  - **H1 Real Rate Dichotomy(XLU −0.167/XLF +0.129, n=5844)**: 부호 split 재현 OK but ★**spec-impl 불일치** — 가설 text=predictive("향후 3M 선도수익"), 코드=same-day contemporaneous. predictive 재검증 시 **IC −0.004/−0.013 붕괴(p>0.3)** → validated_alpha 아님, 부호 방향만 structural.
  - **H2 Stigum lag**: lag=0만 유의, 3~6 무효 → reject 정당(동의). **H4a Credit Beta Split**: def +0.09/XLF −0.166 부호분기 방향성만(잔여 partial IC 0.08~0.17 약).
- **★M4 seed 반영=교체 불가(HOLD 유지 확정)**: 표본 2023-2026 짧은 구간 갇힘(HY/DXY/DFII10 join 한계) → 점추정 박제할 검정력 구조적 부재. ⛔**rate**=real rate XLU음/XLF양 **부호 제약(sign constraint)만**·크기 wide prior. ⛔**dollar**=단일 β·regime-switch β 둘 다 박제금지(switch 자체 비유의), XLF 양만 약prior·방어주 부호불확정. ⛔**credit**=H3 reject로 "credit regime 방어 underperform" 박제금지(2023 노이즈). **oil**=미포함 HOLD. → `factor_betas_seed.py` eq_us_defensive HOLD 셀 유지(pooled-prior+w=0).
