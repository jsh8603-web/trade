<!-- G-C 독립 audit (author != auditor). auditor = steel-audit teammate (opus 1m). 2026-06-05 -->
<!-- 근거 = raw-v3/*.py 직접 재실행 (Python312 PYTHONUTF8=1). self-audit 무비판 신뢰 X. -->

# steel — G-C 독립 audit (15축, hard-fail 0 = PASS)

> verdict: **충실 (PASS)**. hard-fail 코어 B·C·D·I 중 위반 0 (I=PARTIAL=정직 격하).
> 독립 재계산 일치 — self-audit 판정이 데이터로 뒷받침됨 + size 독립성은 독립 추가 검증.

## §4 evaluation-axes yaml

```yaml
evaluation_by: steel-audit (G-C independent teammate)
date: 2026-06-05
evaluator_model: opus-1m
axes_source:
  primary: D:/projects/Inv/study-research/AUDIT-GUIDE.md
  application: D:/projects/Inv/study-research/eq_kr/evaluation-axes.md
industries:
  - industry: steel
    verdict: 충실
    provenance:                                # §0 가장 중요 — 직접 재실행
      raw_scripts_rerun: true                  # measure_fundamentals_cycle/measure/measure_valuation 재실행 일치
      synthetic_fingerprint_check: true        # POSCO 2020-03 -37% 실재 / kurtosis 12.8 fat-tail / 주말갭342·결측 종목차등 = 실데이터
      yaml_to_raw_traceable: true              # capex -0.084 / mom -0.181 / pbr -0.16 전부 재현 일치
    axes_15:
      A: PASS    # Cooper-Gulen-Schill / Asness QMJ / Daniel-Moskowitz 실재 정독
      B: PASS    # ★hard — 합성 0, fat-tail kurtosis 12.8
      C: PASS    # ★hard — yaml↔raw 재현 오차 0
      D: PASS    # ★hard — DART rcept_dt lag≥40일(med 45), 음수 lag 0건
      E: PASS    # 자문 환각 무, 통합 m=180 BY 미생존 정직 보고
      F: PASS    # CPCV+embargo, capex walk-forward OOS 부호유지, per_z REJECT 기각기록
      G: PASS    # tier 강등 = Tentative(n_eff≈27, momentum n=65) / small-universe
      H: PASS    # collector_plan + candidate-ledger 미해결 명시
      I: PARTIAL # ★hard축이나 정직 격하 — 생존편향 잔존(FDR 현존), 단 철강 상폐 드뭄 = over-claim 회피, hard-fail 아님
      J: PASS    # spec↔code 1:1 match (capex "ppe/assets→forward 음" = code 동일, over-claim 0)
      K: PASS    # 분석 unit=23종 factor loading, sub-cluster 부호 cancel 없음
      L: PASS    # β 보고만, 통합 1회 = supervisor
      M: PASS    # opt-in core 직접 호출, production 미접촉
      N: "N/A"   # cross 조립 = supervisor
      O: PASS    # forward shift PIT-safe, reject≠missing
      P: PASS    # net marginal(small-universe·저유동성 caveat)
    hard_fail_count: 0                          # B·C·D PASS, I=PARTIAL(정직격하)
    tier: structural_prior_low_confidence       # 전체 PARTIAL, small-universe + capex BY 미생존
    system_fit:
      current_skeleton_fits: true               # cross-sectional IC + regime-conditional = 현 골격 수용
      pipeline_upgrade_needed: false
      upgrade_plan: ""
    remediation: []                             # PASS — 보강 불요
    flag_dynamic_path_check:
      affects_indicator_present: true
      affects_edge_present: true

summary:
  total_industries: 1
  verdict_counts: {충실: 1, 부분: 0, 불충분: 0}
  hard_fail_industries: []
  overall_recommendation: "통합 진행 (register 가능). tier=structural_prior_low_confidence(small-universe). capex=TENTATIVE monitor/min-weight."
```

## ★capex 재현 검증 (최우선) — 독립 재계산 결과

| 점검 | 주장 | 독립 재현 | 판정 |
|---|---|---|---|
| uncond IC y_60d | -0.084 | **-0.0839** (n=82) | ✓ 일치 |
| wc_p | 0.0005 | 0.0005(B=2k floor) → **0.00025**(B=100k 정밀) | ✓ floor지만 실제 더 강 |
| walk-forward OOS | IS-0.111→OOS-0.053 부호유지 | **IS-0.111→OOS-0.0526 sign_hold** | ✓ |
| KRW_neutral | 음 유의 | IC-0.111 wc_p=0.001 t=-3.11 | ✓ |
| Slowdown/flow_neutral | 음 | Slowdown-0.096 / flow_neutral-0.071 | ✓ |
| **size 독립(Fama-MacBeth)** | (self-audit 미수행) | **size-resid IC-0.088 t-2.68** = 오히려 강해짐 | ✓ size 위장 아님 |
| effective-N | n=82 | ACF lag1=0.65 → **n_eff≈27**, NW 이미 적용 t=-2.61 | ✓ 중첩 보정 정직 |
| 단일 FDR m=180 BY | 미생존 | precise p0.00025 > BY thresh 9.6e-05 = **미생존** | ✓ TENTATIVE 정확 |

**핵심 caveat (over-claim 주의, non-blocking)**: ppe_yoy(증설 변화율)는 IC≈0/wc_p>0.8/OOS반전 = 무신호. capex_ratio(자산집약도 *레벨*, 종목 내 std~0.03 거의 고정)만 작동. 따라서 신호 source = "asset growth(증설변화)"가 아니라 **자산집약도 레벨**(value/low-asset-turnover에 근접). "auto capex(증설cycle) 일반화 1보" framing은 **level-signal로 한정 해석 권고**. hard-fail 아닌 mechanism 라벨 문제.

## 그 외 핵심 신호 재현
- **momentum reversal**: mom_12_1 12M IC=**-0.181** t_NW=-4.42(lag12 overlap 충분 보정) n=65 CPCV1.00 BY생존 ✓. battery 양과 반대 = cyclical 판별.
- **PBR○ PER✗**: pbr_z 3/6/12M IC-0.10~-0.16 BY생존3 / per_z 전 horizon 비유의 BY미생존 (PER avgN16<PBR20.7 = 적자 trough-EPS trap).
- **vol_60 저변동 quality** BY생존 ✓.
- **small-universe haircut 일관**: avg N≈20. summary가 -0.181 literal 미인용, breadth-adj IR(-0.81≈내 -0.72) + 50% haircut 일관 적용.
- **화이트리스트 정당**: "1차 철강 제조업" 정밀매칭 + 발전설비/상사/전선/조선/2차전지 명시 제외.

## 판정
**register 가능 (충실)**. hard-fail 0. tier = structural_prior_low_confidence (small-universe + capex BY 미생존). capex는 진짜 신호(size 독립·PIT-safe·OOS 부호유지)이나 TENTATIVE DIRECTIONAL 라벨이 정확 = summary가 정직하게 격함.
