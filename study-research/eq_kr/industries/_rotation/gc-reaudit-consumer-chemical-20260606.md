<!-- G-C 재audit (author != auditor). auditor = steel-audit teammate (opus 1m). 2026-06-06 -->
<!-- 근거 = measure_rotation_consumer/recheck_aux_signals/mom3_robust 직접 재실행 + 독립 market-residualize 검증. -->

# consumer 신규4 + chemical 보조1 — G-C 재audit

> verdict: **chemical mom_3 = ★hard-fail 소지(market×beta 재포장) / consumer = 부분(C축 robustness 추적불가 + CSI mild HARKing, 단 핵심신호 진짜)**.

## ★★chemical mom_3_residualized = market×beta 재포장 (hard-fail 소지)

| 검증 | 결과 |
|---|---|
| raw IC(60d) 재현 | +0.385 wc_p0.0005 OOS+mag유지 ✓ (aux json 일치) |
| placebo/LOY/non-ovlp 재현 | mom3_robust.py 재실행: non-ovlp +0.475, placebo p0.0020, LOY 0.291~0.471 전부 양 ✓ |
| residualize 대상 | **usdkrw + brent (공통 macro)만** (코드 line 58-60). ★**시장(KOSPI) momentum 누락** |
| ★독립 검증: 외부시장(7산업 평균) momentum residualize | **IC 0.385 → 0.02 붕괴** |
| corr(chem mom3, 외부시장 mom3) | **0.829** (매우 높음) |

★**결론**: mom_3_residualized는 진짜 직교 독립 베팅이 **아니라 market momentum × beta 재포장**. analyst가 usdkrw+brent에만 residualize해 +0.385 유지했으나, 진짜 공통인자(시장 momentum)에 residualize하면 0.02로 붕괴. corr 0.829 = chemical 업종 momentum ≈ 시장 momentum.
- spread와 corr 0.26(낮음)은 spread와의 직교일 뿐, **시장과의 직교가 아님**. "독립 2번째 베팅" 주장 부적절.
- 코드 주석 line 52 자체가 "시장(KOSPI proxy=전종목 평균)+USDKRW로 residualize" 라 적었으나 **실제 코드는 usdkrw+brent만** = 주석↔코드 불일치 + mechanism 결함.
- ★team-lead 질문 "직교 독립 vs market×beta 재포장" → **market×beta 재포장이 맞음**. chemical 보조신호로 채택 금지 권고(spread/china_mchi STRONG는 유효, mom_3만 폐기).

## consumer 신규 채택 4 — 검증

### B축 (재현) — PASS
- csi_spend_d3 industry y_60d = **+0.325 wc_p0.001** OOS적격(0.335→0.303) n=86 n_eff=52.9 t_power2.36 ✓
- mom_6 reversal industry -0.251 wc_p0.018 / cosmetics -0.324 wc_p0.004 OOS+mag유지 ✓
- 홍콩 관광 +0.254 wc_p0.044 TENTATIVE ✓
- 전부 byte-identical 재현.

### ★C축 (추적성) — 부분 결함
- rotation-signals.md 핵심 robustness 주장 "**residual +0.370, LOY 전부 양(+0.24~+0.41)**" (csi) + "residual -0.361/-0.335"(mom_6)이 **measure_rotation_consumer.py / json 어디에도 없음** = 추적 불가.
- 코드에 residualize/leave-one-year 함수 전무. → ★C축 부분 결함(핵심 IC는 재현되나 robustness 보강 수치 추적불가). 보강: residual/LOY 코드 추가 또는 주장 삭제.

### ★HARKing #1 (CSI yoy 부호반대 기각 정당성) — mild 소지
- csi_spend_d3 = +0.325 양(일치) / csi_spend_yoy = -0.289 음(반대). 둘 다 사전확약 "양".
- analyst: "yoy=level 기저효과(高수준=고점=평균회귀), d3=단기변화" mechanism 분리 → d3만 채택.
- ★판정: **mild HARKing 소지**. 같은 CSI 지표 두 변환(d3/yoy) 중 부호 맞는 것만 선택. yoy도 "변화율"이지 level 아님 — "기저효과" 설명은 d3(3M)/yoy(12M) 시간구조 차이의 사후 라벨. 단 (a)d3/yoy 둘 다 측정前 사전등록 (b)d3 OOS적격+이론일치 (c)yoy 부호반대를 (C)REJECTED 섹션에 정직 박제 → data-mining 기각 수준 아님. **d3 = tentative 유지, "yoy 기저효과" mechanism은 사후성 명시 권고**.

### ★HARKing #3 (cosmetics reversal 사전확약) — PASS
- mom_6 reversal 사전확약 = "음(-, mean-reversion)" (line 39, code expected_sign=-1). 측정 industry -0.251/cosmetics -0.324 음 = **일치**. HARKing 아님.
- ★독립 검증: consumer mom_6 reversal을 외부시장 residualize → IC **-0.425 강화** (chemical mom_3와 정반대) = consumer-specific reversal alpha 진짜(market 재포장 아님). robustness "강화" 방향 주장은 데이터로 뒷받침(수치는 추적불가하나 방향 맞음).

### CSI 단일 BY 생존 주장 — family 선택 주의
- csi_spend_d3 p=0.001: **m=12 theory-driver family(이론일치+OOS적격 셀만)서 BY 생존** / **m=68 single family서 BY 미생존**(thresh 0.000306, Bonferroni 0.000735도 미통과).
- ★theory-driver family = 결과(부호일치+OOS적격) 본 후 필터 = post-selection으로 multiplicity 인위축소 소지(garden-of-forking-paths). G-G v2 "FDR 완화로 survivor 인위증가 금지"에 저촉 소지.
- 단 analyst가 fdr_all_single(m=68, survivors=[]) 병기 + §6 "전 신호 underpowered, magnitude tentative, 부호·방향만" 격하 → validated 과장 안 함. "단일 BY 생존"은 **theory-family 한정 명시 필요**(single-family 미생존).

## D축 (좀비) — PASS
consumer 28종 / chemical 17종 모두 frozen>120일 0건. 좀비 carry-forward 없음(bio/aitech와 다름).

## hard-fail 종합
| 대상 | B | C | D | HARKing | 판정 |
|---|---|---|---|---|---|
| chemical mom_3 | PASS | PASS(aux json+robust 재현) | PASS | ★**market×beta 재포장 = 채택 부적절** | **보조 폐기 권고** |
| consumer csi_d3 | PASS | ★부분(robustness 추적불가) | PASS | mild(yoy 기저효과 사후성) | tentative 유지, family 한정 명시 |
| consumer mom_6 reversal | PASS | 부분(robustness 추적불가) | PASS | PASS(사전확약 음 일치) | ★채택 정당(market resid 강화 입증) |
| consumer 홍콩관광 | PASS | — | PASS | PASS | TENTATIVE 유지 |

## 수정 권고
1. ★**chemical mom_3_residualized 보조 채택 폐기** = 시장 momentum residualize 시 0.02 붕괴(market×beta 재포장). spread/china_mchi STRONG은 유효 유지.
2. ★consumer robustness 코드(residual/LOY) 추가 또는 rotation-signals.md robustness 수치(+0.370/LOY) 삭제 = C축 추적성.
3. consumer "CSI 단일 BY 생존" → "theory-driver family 한정(m=68 single 미생존)" 명시.
4. consumer CSI yoy "기저효과" mechanism = 사후성 명시(d3만 채택의 사전이론 근거 약).
