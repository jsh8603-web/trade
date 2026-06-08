---
tags: [type/validation-fundamental, domain/equity-us, sector/soxx_semi, phase/sector-granular]
date: 2026-06-08
purpose: SOXX 반도체 R3 Layer1 펀더멘털 forward-IC 실측 — within-sector value+quality 결합 sector-neutral z. ★primary 결정실험.
source: raw-v3/measure_value_quality.py → validation-vq-v1.json (재현 가능)
data: us_cyclical/raw-v3/data/{prices,edgar_fundamentals}.parquet (SOXX 12종, prices 2015~, EDGAR PIT filed)
verdict: ★(C) FREEZE 권고 (value+quality 결합 MDE 미달 + decomposition γ null). value 단독만 약 robust.
---

# SOXX 반도체 — R3 validation-fundamental (value+quality 결정실험)

> ★결론 선언: **(C) FREEZE 권고**. value+quality 결합 IC=0.030 < MDE 0.107 + within-sector decomposition γ null(t=0.71).
> 단 value **단독**은 약하게 robust(IC 0.068, wc_p 0.008, IS/OOS 부호 일관). = "rotation-granular 폐기 + value-selection
> 집중"의 부분 근거. ★자문 통설(Novy-Marx value+quality 결합 강화)을 우리 데이터가 **falsify**(quality 가 value 희석).
> ★tier = TENTATIVE 상한 (생존편향 I축 PARTIAL + small-n + value 단독만 marginal). 점추정 박제 금지(CI+wc_p+OOS+tier).

## §0. 측정 설계 (M1~M5 + fixed-b)

- **단위**: SOXX 12종 monthly cross-section. 신호 = sector-neutral(universe-relative) z-score → t+1 forward 1M return Rank-IC(Spearman).
- **신호**:
  - value = 저PBR(자본잠식 제외) + 저EV/EBITDA z 평균 (cheap = +z). PBR=mcap/equity, EV/EBITDA=(mcap+debt−cash)/(op_income+D&A).
  - quality = ROIC z = op_income/(equity+debt) (고품질 = +z).
  - value+quality = 두 z 평균 결합 (★primary, value-trap 회피 Novy-Marx).
  - momentum 12-1 = (P_{t-1}/P_{t-12}−1) z (부호 falsifier).
- **PIT**: EDGAR (ticker,concept,end) **최초 filed** 이후만 ffill (restatement/lookahead 차단). 시총=Close×PIT shares.
- **split**: full 2015-2026(137mo) / IS 2015-2021(84mo) / OOS 2022-2026(52mo). ★prices 2015~ = IS 2010 가정 불가.
- **추정**: block-bootstrap CI(block=3, B=2000) + wild-cluster bootstrap p(block Rademacher) + eff_N(자기상관 보정, fixed-b 정신) → t_fixedb.

## §1. ★핵심 결과 (점추정 박제 금지)

| 신호 | split | IC | 95% CI (block-boot) | wc_p | t_fixedb | eff_N | n_mo | 판정 |
|---|---|---|---|---|---|---|---|---|
| **value(clean)** | full | **+0.068** | [+0.014, +0.120] | **0.008** | — | — | 136 | ★방향 robust(0배제), but \|IC\| ~ MDE 0.072 경계 미달 |
| value(clean) | IS 2015-21 | +0.051 | — | — | — | — | 84 | 부호 양 유지(약) |
| value(clean) | OOS 2022-26 | +0.096 | — | — | — | — | 52 | 부호 양 유지(강화). ★OOS underpowered(MDE 0.146) = 정직 라벨 |
| value (raw, 자본잠식 포함) | full | +0.075 | [+0.018, +0.132] | 0.0035 | 2.5 | 124 | 136 | (clean 과 유사) |
| **quality (ROIC)** | full | +0.020 | [−0.039, +0.077] | **0.47** | 0.63 | 96 | 136 | ★무신호 (CI 0 포함) |
| **★value+quality 결합** | full | **+0.030** | [−0.023, +0.081] | **0.23** | 1.1 | 117 | 136 | ★**비유의 + MDE 0.107 미달** = freeze 조건 |
| value+quality | OOS | +0.019 | [−0.073, +0.094] | 0.61 | 0.44 | 47 | 52 | OOS 약화 |
| **momentum 12-1** | full | +0.009 | [−0.050, +0.063] | 0.76 | 0.29 | 124 | 124 | 비유의 |
| momentum 12-1 | IS | **−0.030** | [−0.10, +0.049] | 0.45 | −0.7 | 56 | 72 | 음(reversal 방향) but 비유의 |
| momentum 12-1 | OOS | **+0.063** | [−0.019, +0.139] | 0.021 | 1.2 | 52 | 52 | 양 but eff_N 보정 t<2 |
| value+quality (sub-neutral) | full | +0.059 | [+0.011, +0.109] | 0.0125 | 2.32 | 125 | 136 | ★robustness only (memory n=1 소실, N_eff=8) |

### value 컴포넌트 분해 (일관성)
- PBR(clean) IC=+0.059 / EV/EBITDA IC=+0.060 → 두 value 컴포넌트 **부호·크기 일관**(양, value premium robust). 자본잠식(MCHP equity<0) = 3개월만 = 오염 미미.

## §2. ★decomposition 결정실험 (GUIDE §10.6, (C) vs (D))

- spec: within-month demean(시장공통 제거 = within-sector 성분) → forward ~ value+quality, month-clustered SE.
- **결과**: γ = **+0.0028**, t_clustered = **0.71** (n_obs=1591, n_months=136). ★**null** (t<2, CI 0 포함).
- **판정**: within-sector 예측성분 무 → **(C) freeze** (GUIDE §10.6: γ null → granular 폐기). ★rotation 도 회의(~30%) = (C) 우세 확정.

## §3. ★momentum 12-1 부호 falsifier

- predicted_sign = **양**(미국 momentum 작동 가설, 한국 reversal 반대). 결과: full +0.009(비유의), IS −0.03(음=reversal 방향), OOS +0.063(양).
- ★**판정**: 부호 **불안정**(IS 음 ↔ OOS 양, 둘 다 eff_N 보정 후 비유의). = predicted 양 미입증 + 한국 reversal(음) 도 미입증.
  = momentum 신호 자체 미작동. ★falsifier 작동(predicted 양 사전고정 → 입증 실패, over-claim 회피).

## §4. ★freeze 판정 (GUIDE §10.7)

| 조건 | 결과 | 판정 |
|---|---|---|
| value+quality full \|IC\| ≥ MDE 0.107 | 0.030 < 0.107 | ★**미달 = freeze** |
| decomposition γ within-sector 유의 | t=0.71 null | ★**null = freeze** |
| quality(ROIC) 신호 기여 | IC 0.02 무신호 | value 희석(결합 역효과) |

→ ★**(C) FREEZE 권고**: rotation-granular 영구폐기 + 3슬리브 value-selection 집중(GUIDE §10.7 Freeze default).
- ★단 **value 단독은 약 robust**(IC 0.068, wc_p 0.008, CI 0배제, IS/OOS 부호 일관) = value-selection 집중의 부분 정당.
- ★자문 통설 falsify: Novy-Marx "value+quality 결합 강화"가 우리 SOXX 12종에선 **역효과**(quality 무신호 → 희석). =
  empirical-claim §3 자문 prior 재현 실패 → 정직 박제(over-claim 0).

## §5. ★한계 (hard-fail 축 self-check)

- **I 생존편향 = PARTIAL**: 현 12종 = 현 SOXX holdings only. ★MRVL/NXPI 등 현 SOXX 편입종목 누락 + 과거 편출/상폐 종목
  부재. historical membership = 무료 부재(CRSP/Compustat 유료). → ★**TENTATIVE 상한**(CONFIRMED 금지). I축 PARTIAL.
- **D PIT = PASS**: EDGAR 최초 filed 이후만 + forward shift. ★단 filed-end lag median 227d = 중복 filing 영향, (ticker,
  concept,end) 최초 filed 채택으로 완화.
- **B 실데이터 = PASS**: 합성 0%. pykrx 아닌 yfinance prices(2867 daily) + EDGAR(22,798 rows) 실측. raw-v3 .py 재현.
- **C 추적성 = PASS**: 모든 IC = validation-vq-v1.json key 매핑.
- **G eff_N tier**: N=12 small-N → 검정력 시계열에서. eff_N 자기상관 보정 적용. OOS 52mo = underpowered 명시.
- **K 다중검정**: 신호 4종(value/quality/vq/momentum) × split 3 = R4 FDR 의무 (현 = raw wc_p, BY 보정 R4).
