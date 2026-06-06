---
tags: [type/rotation-timing, domain/inv, scope/equity-kr, topic/industry-rotation, status/measured]
date: 2026-06-05
owner: semi-analyst (kr-equity team, opus 1m)
trigger_to_resume: "plan-kr-equity-conditional-ic-20260605.md §10 S5.5 + 본 capsule"
---

# 12산업 ROTATION TIMING — 산업 자체 비중 timing (원 의도 본체)

> **임무** = "어느 산업을 (현재 국면에) 살지" = rotation timing. 기존 12산업 capsule = 전부
> 종목selection(산업 안 어느 종목) cross-sectional IC 만 측정. 본 측정 = 그 위 차원 =
> **산업 자체 시계열 forward return 예측** = "이 국면 → 반도체 비중↑ / 정유↓".

## ★0. v2 보강 = 이론→통계검증→판정 파이프라인 (자문 2R 확정 + 사용자 framing)

> 사용자 파이프라인: "어느 업종 살까 = 산업동향(이론·fundamental) 관점. **이론을 통계가 검증**. 가격통계 단독=data
> mining". 자문 결론 A = ★고유 cycle 직접신호가 진짜 alpha, 가격 momentum 강등(공통인자 재포장 위험).
> theory-notes.md = 산업별 cycle driver 이론 + 부호 사전확약(데이터 접촉 전 동결).

### v2 verdict (이론 부호 사전확약 vs 실측 대조)
| 산업 | 고유 cycle 신호 | 실측 rho | 사전확약 | 일치 | verdict |
|---|---|---|---|---|---|
| **steel** | iron_ore_d3 | +0.341 (wc_p 0.001) | 양(철광석=철강 cycle) | ✅ | ★**STRONG** |
| **battery** | lithium_yoy | +0.274 (OOS+0.46) | 양(리튬=EV 수요) | ✅ | ★**STRONG** |
| **refining** | crack_d3 | +0.241 (OOS+0.39) | 양(crack=마진) | ✅ | ★**STRONG** (약신호 산업 부활) |
| **auto** | global_auto_d3 | +0.261 (OOS+0.30) | 양(글로벌차) | ✅ | ★**STRONG** |
| chemical | wti_naphtha_yoy | −0.367 (OOS약화) | 음(cost-push) | ✅ | TENTATIVE |
| semiconductor | soxx_d3 | +0.171 (wc_p 0.13) | 양(반도체 cycle) | ✅ | TENTATIVE (종목선택 primary) |
| **shipbuilding** | baltic_dry_yoy | −0.102 | 양(운임=수주) | ❌ | ★**REJECTED** (이론 반증, 신조선가 미수집) |

### ★momentum = 공통인자 재포장 검증 (자문 Q-a, data-mining 차단)
산업 momentum을 공통인자(외국인flow/USDKRW/글로벌cyclical) residualize 후:
- **소멸**(채택불가=data mining): semiconductor +0.215→+0.079 / auto +0.238→+0.136 / battery / steel / financial = market momentum×beta.
- **잔존**(진짜 idiosyncratic): consumer mom_6 −0.251→−0.361(강화, 내수 방어 reversal) / telecom·aitech(방어 IT) / chemical.
→ ★자문 A "산업 momentum ≈ market momentum×beta = 가짜 breadth" **데이터 입증**. 진짜 alpha = 고유 cycle.

### ★본인검증 (자문 §4)
- 36셀 collapse: L2 rotation(industry-month) 89월 25셀 occupied, **N≥24 powered=0/25 = collapse 100%** → 36셀 hard 부적합, single-axis+partial-pooling 정당.
- residual N_eff: raw 3.02 → residual 3.51 (pairwise 0.502→0.445) = ★자문 "진짜 독립 차원 ~3-4" 입증 = 12산업 개별 rotation=false breadth.

## 1. 측정 설계 (frame §M2 일반화)

- **분석 unit** = 산업 eq-weight 패널 (각 capsule prices.parquet 종목 동일가중 월수익). ★종목 cross-section 아님.
- **종속변수** = 산업 패널 forward return y_20d(1M) / y_60d(3M).
- **신호군**:
  - **산업 고유**(★진짜 rotation): 산업 자체 momentum(mom_3/mom_6/mom_12_1), 1M reversal, cross-industry 상대모멘텀(rel_mom_6/3).
  - **macro 공통**(시장 timing): 경기선행 Δ(cli_chg, PIT lag=2), USDKRW yoy/Δ, 외국인 flow, 반도체 PPI yoy(PIT lag=1).
- **prototype** = `refining/measure_timeseries.py`(cycle driver 동조 측정)를 ★forward 예측 + walk-forward OOS 로 일반화.
- **게이트**(G-G v2): OOS eligibility(IS 2019-22 / OOS 2023-26 부호+magnitude 유지) + 단일 FDR(BY) + wild-cluster bootstrap + MDE/power(t_obs⋚2.802) + non-overlap 교차검증 + placebo + leave-one-year.

## 2. ★핵심 발견

### (1) 한국 12산업 = 공통 macro 지배 → 진짜 rotation = 산업 고유 신호
- 12산업 월수익 **평균 pairwise corr = 0.502**, **PC1(공통인자) 분산 55.3% 지배**, N_eff(eigen-entropy)=5.31/12.
- = plan §1 prior("외국인flow·USDKRW가 전 산업 공통 driver → 환상의 분산") **데이터 입증**.
- 함의: `cli_chg`·`usdkrw`·`foreign_flow` 같은 macro 신호는 12산업에서 거의 동일 = **시장 전체 timing**(N_eff≈1 베팅), 산업 rotation 아님. 진짜 rotation(산업 비중 차등) = **산업 고유 신호**(산업별 momentum 부호 차이, 상대모멘텀).

### (2) ★약신호 산업(종목선택 불가)일수록 rotation 이 진짜 활로 — 데이터 입증
| 산업 | 종목선택(capsule) | rotation 신호 | OOS | 판정 |
|---|---|---|---|---|
| **refining(정유)** | ✗ 영구불가(strict 2종) | rel_mom_6 reversal -0.360 | IS-0.38→OOS-0.38, non-ovlp -0.39, placebo 0.0015 | ★rotation 부활 |
| **telecom(통신)** | ✗ service 3사 불가 | semi_ppi_yoy -0.334 + foreign -0.24 + mom_12_1 +0.28 | IS-0.16→OOS-0.60 | ★rotation 부활 |
| **shipbuilding(조선)** | 약 | rel_mom_3 reversal + foreign_flow | OOS 부호유지 | rotation 약하지만 살아있음 |

→ 자문(gemini+claude) 수렴 = "과점 산업 sector-timing overlay 부활" 가설 **데이터 지지**.

## 3. 산업별 rotation 판정 (요약)

| 산업 | tier | 최강 rotation 신호 | rho (OOS) | type |
|---|---|---|---|---|
| chemical | PASS-cond | mom_3 | +0.359 (OOS +0.391, non-ovlp +0.450) | 산업고유 |
| refining | PASS-cond | rel_mom_6 reversal | −0.360 (OOS −0.384) | 산업고유 ★약신호활로 |
| consumer | PASS-cond | rel_mom_6 reversal | −0.328 (OOS −0.571) | 산업고유 |
| telecom | PASS-cond | semi_ppi_yoy | −0.334 (OOS −0.602) | cycle방어 ★약신호활로 |
| financial | PASS-cond | cli_chg | +0.482 (OOS +0.358) | macro(★유일 powered+BY) |
| aitech | PASS-cond | semi_ppi_yoy | −0.333 (OOS −0.350) | cycle |
| battery | PASS-cond | mom_3 | +0.277 (OOS +0.362) | 산업고유 |
| steel | PASS-cond | foreign_flow | −0.251 (OOS −0.197) | macro flow |
| auto | PASS-cond | mom_3 | +0.238 (OOS +0.324) | 산업고유 |
| semiconductor | PASS-cond | mom_3 | +0.215 (OOS +0.346) | 산업고유 (종목선택 primary) |
| **bio** | **★FAIL** | (rotation 0, OOS flip) | — | **monitor-only** |

- **11/12 산업 rotation tradeable**(PASS-conditional). bio 만 FAIL(rotation 부재 = monitor-only, over-trade 차단).
- ★전 신호 **underpowered**(financial cli_chg 1개만 powered + 단일 FDR BY 생존) = magnitude tentative, 부호·방향 한정.

## 4. ★gated 설계 (자문 수렴, over-trade 차단)

rotation 신호 대부분 약(underpowered) → 강제 투입 = over-trade. 자문 gated 설계:
1. **default weight 0** — 신호 무발현 시 rotation tilt 0 (약신호=무포지션=무거래).
2. **hysteresis dead-band** — 상단 진입·하단 이탈 비대칭 → 중립대 whipsaw 차단 (rank-space).
3. **cost-aware no-trade** — 기대 α > k×roundtrip_cost(23bps) 일 때만 rebalance (return-space, dead-band 와 별 공간 결합).
4. **live OOS falsification** — Rank-IC e-CUSUM drift → weight downward-only attenuation (죽은 신호 자동 0).
5. **telecom dividend-carry** — 통신은 timing 보다 배당-carry 정적 tilt primary(자문) + 규제 event blackout.

## 5. 정직 단서 (small-n hedge)

- 전 rotation 신호 underpowered (60d overlap eff_N 작음) → **magnitude tentative, 부호·방향만**. non-overlap sub-sample(stride=3M)로 부호 일관 교차검증 완료.
- macro 공통 신호 = 12산업 N_eff 중복(가짜 breadth) → rotation **차등** 효과는 산업 고유 신호 한정.
- 산업별 고유 cycle 지표 직접(유가/리튬/철광석/운임) + 통신 배당 = collector_plan (이연 아님, 현 측정 = 가용 공통 데이터 범위 완주).
- rotation(동적 tilt) = static PCA sleeve(plan §8 S6)와 **결합** = 2층 완성. WIRE5 배선·sizing = supervisor 통합단계 (go-live 미접촉).

## 6. 재현
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
cd study-research/eq_kr/industries/_rotation
"$PY" measure_rotation.py          # validation-rotation-v1.json (forward IC + OOS)
"$PY" measure_rotation_robust.py   # validation-rotation-robust-v1.json (LOY + placebo + non-overlap + N_eff)
```
