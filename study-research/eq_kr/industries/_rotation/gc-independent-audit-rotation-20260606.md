<!-- G-C 독립 rotation audit (author != auditor). auditor = steel-audit teammate (opus 1m). 2026-06-06 -->
<!-- 근거 = measure_integration/measure_rotation_v2/measure_chem_rotation_v2 직접 재실행. self-audit 무비판 신뢰 X. -->

# rotation (12섹터 + cross-industry 결합) — G-C 독립 audit

> verdict: **충실 (PASS), hard-fail 0**. 코드화 자격 충족.
> 단 2건 minor 정직성 흠(결합 좀비 미마스킹 / semi_ppi_yoy 단위근) + 1건 over-claim 주의(chemical full +0.539 인용) + auto iron_ore borderline HARKing = **non-blocking 수정 권고**.

## hard-fail 축 (B·C·D·I + M·N·O)

| 축 | 판정 | 근거 (직접 재현) |
|---|---|---|
| **B** 실데이터/level-spurious | PASS | STRONG 2-3 byte-identical 재현: steel iron_ore_d3 +0.341(wc_p0.001), chemical spread_china_brent full +0.539/strict +0.427(wc_p0.001), battery lithium_yoy +0.274(wc_p0.01). 산업 월수익·d_usdkrw·foreign ADF stationary. ⚠️ semi_ppi_yoy ADF p=0.556 단위근(공통인자, minor). |
| **C** 추적성 | PASS | validation-integration-v1.json ↔ rotation-integration.md 전 값 일치(residual_N_eff 3.49/CI[2.77,4.48]/raw 2.98/pc1 0.506/mean_pair 0.449/battery~chem +0.812/k=4 sleeves). |
| **D** 좀비 carry-forward | PARTIAL | bio rotation = 좀비 마스킹 명시(코오롱티슈진950160 47.8%+케어젠214370 거래정지 carry-forward 제거). ⚠️ 단 **결합(measure_integration)은 bio prices.parquet 좀비 미마스킹** 사용 — eq-weight 집계로 영향 희석(bio 월수익 zero-return month=0)이나 정직성 흠. hard-fail 아님. |
| **I** 생존편향 | PARTIAL | universe = FDR 현존 스냅샷(전 산업 공통). refining strict override(가스9종 제거 = SK이노/S-Oil 2종)로 universe 오염 정정 = 정직. 생존편향 잔존(각 산업 동일 한계). |
| **M** wire 충실 | PASS | measure_integration opt-in 측정, WIRE5 production 미접촉. sleeve·hierarchical FDR = S7 supervisor 설계만(현 미배선 명시). |
| **N** cross PSD | PASS | residual corr 최소 eigenvalue=0.117>0 PSD. raw 0.108>0. 88개월×12산업 full-rank. PC1 6.08(분산비 0.506). |
| **O** leakage | PASS | forward shift PIT-safe. residualize OLS in-sample(rotation = timing 신호, lookahead 없음). |

**★hard-fail 코어 (B·C·D·I + M·N·O) = 0** (D·I = PARTIAL 정직 격하, hard-fail 아님).

## 핵심 검증 1: residual N_eff (false breadth)
- residual_N_eff = **3.49** [2.77, 4.48] byte-identical 재현. raw 2.98. 공통인자{d_usdkrw, foreign, semi_ppi_yoy} 제거 후 진짜 독립 ~3.5차원 = "12 베팅 아니라 ~3.5" 정직. 동시 active tilt 3 cap 합리적.
- residual N_eff > raw N_eff (3.49>2.98) = 정상(공통인자가 corr↑→N_eff↓, 제거 시 증가).

## 핵심 검증 2: L축 1회계상 (telecom 외국인flow 중복 차단)
- telecom 외국인flow rho=-0.396 well-powered(t_power 3.58>2.802) = 가장 강. 단 **MACRO 공통 인자**.
- telecom rotation-signals + integration §4/§7 모두 "flow=전산업 공통 L축 1회계상, telecom 고유 rotation 중복 금지, telecom 진짜 고유=semi_ppi 한정" 명시 = **설계 레벨 정직**. 실제 wire는 S7 supervisor(현 설계 차단만 검증).

## 핵심 검증 3: universe 오염 재검
- **refining crack 폐기 정당**: full 11종에 가스 9종 오염 → crack_d3 +0.241 가짜. strict2(SK이노/S-Oil)서 gasoline/diesel/jet/blended crack 전부 OOS flip 무신호 직접 재현 ✓. FDR family 측정 前 8가설 동결(재정의 금지) = HARKing 방지.
- steel/auto/battery/chemical = strict≈v2 확인(steel 종목audit서 iron_ore +0.348 strict 재현, auto global_auto_d3 +0.2613 byte-identical, chemical spread strict +0.427 robust).

## 핵심 검증 4: tradeable 판정 적정성 (under-claim 경향, 과대발굴 회피)
- **shipbuilding monitor-only 정직**: BDI 양 사전확약→실측 음(주가 6-12M 선행 입증). tanker/boat/lng 11후보 전부 반증/약 → tradeable 0 = 무리한 발굴 회피.
- **financial 비대칭 정직**: term_spread(NIM) 상대수익 이론 양인데 실측 음 → "시장 timing(cyclical beta) 채택불가" 분류 ✓. credit_spread(대손)만 tradeable 1(non-overlap/leave-year/placebo robust, OOS약화 underpowered=tentative). 처음 보수적 0개→재검 1개 신중.

## 핵심 검증 5: HARKing 점검
| 케이스 | 판정 | 근거 |
|---|---|---|
| **steel 철광석 부호** | ★HARKing 아님 | iron_ore_d3 사전확약 = "양 prior(수요 동행)" 측정 前 동결 → 측정 +0.348 양 = 사전등록 **일치**. iron_ore_yoy = "데이터판정(양/음)" 양면 동결. |
| **refining 배당 부호정정** | ★정직 자인 | prior 양(고배당=저평가)→실측 음 = 사전확약 위반 **명시** + peak-EPS trap 배당버전(Damodaran) 정정. |
| **auto iron_ore 부호반전** | ⚠️ borderline | prior 음(원가)→실측 양 → 사후 "리플레이션 사전이론" 보강. analyst "양면 명세 누락"으로 자인하나 **post-hoc rationalization 소지**. 단 (a)OOS강화 0.286→0.549 (b)multivariate iron t=3.14 독립 (c)투명 자인 → data-mining 기각 수준 아님. **"리플레이션 prior"를 사전등록처럼 취급 금지, tentative 라벨 적절**. |

## over-claim / under-claim
- **over-claim 1 (chemical)**: integration §1이 "spread(china−brent) +0.539 STRONG" 인용 = full panel 값. strict NCC 6종 실측 +0.427(여전히 robust OOS+mag). +0.539 인용은 magnitude inflation 소지 → **strict +0.427 병기 권고**(신호 본질·STRONG 판정 자체는 정당).
- **under-claim**: financial/shipbuilding tradeable 판정이 보수적(과대발굴 반대 경향) = 건전.
- 전반: integration이 "전 신호 underpowered(BY 미생존)=magnitude tentative, 부호·방향만" 일관 명시 = 정직.

## 수정 권고 (non-blocking)
1. **결합 좀비 마스킹**: measure_integration.py가 bio(+aitech 셀바스AI 108860 284일 frozen) prices.parquet 좀비 carry-forward 미마스킹. eq-weight 집계로 영향 희석되나 bio std(0.077) 약간 저하 → singleton 격리 판정 robust성 위해 마스킹 패널 병기 권고.
2. **semi_ppi_yoy 단위근**: 공통인자 중 semi_ppi_yoy ADF p=0.556 비정상. residualize OLS 회귀변수로 사용 시 잔차 minor 왜곡. Δ 또는 detrend 권고(rank-IC·residual corr 맥락서 영향 제한적).
3. **chemical +0.539 → +0.427 strict 병기**.
4. **auto iron_ore = tentative 라벨 + 리플레이션 prior 사후성 명시**.

## 판정
**코드화 자격 충족 (hard-fail 0)**. STRONG 4(chemical/steel/battery/auto)는 직접 재현으로 진짜 산업고유 cycle alpha 확인(residual 후 잔존). residual N_eff 3.5/L축 1회계상/PSD/universe 오염정정/tradeable 신중판정 모두 정직. 4건 non-blocking 수정 권고는 S7 통합 yaml 단계 반영.
