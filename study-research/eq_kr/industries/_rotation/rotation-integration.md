---
tags: [type/rotation-integration, domain/inv, scope/equity-kr, topic/rotation-sleeve, status/integrated]
date: 2026-06-06
owner: rotation-analyst (kr-equity team, opus 1m) — ★역할: cross-industry 통합 조율
trigger_to_resume: "plan §10 S5.5 + S6 residual-PCA sleeve / 12산업 rotation-signals.md 취합"
---

# cross-industry rotation 통합 (12산업 analyst 취합 → sleeve 구조 + 2층×3층 결합)

> ★역할 전환(team-lead): 개별 산업 cycle 리서치·측정 = 12 analyst 위임. 나 = **cross-industry 통합**.
> 입력 = 12산업 `{sector}/rotation-signals.md` (각 analyst 이론→통계 verdict). RESULTS 6대 결론 B~F 통합.
> ★점추정 박제 금지 — participation ratio + bootstrap CI. WIRE5 배선·sizing = supervisor 통합단계(go-live 미접촉).

## 0. ★universe 오염 정정 (refining-analyst 적발 = critical)

★내 v1/v2 = 산업 디렉토리 prices.parquet **전체** 패널 사용 → 부수종목 오염(frame §1.6 분석unit 오염).
- **refining**: v2 "crack_d3 +0.241 STRONG" = ★**가스 9종 오염**(SK가스/E1 에너지베타). 정유 strict2(SK이노/S-Oil) 단독 = crack 무신호(-0.014 OOS flip). → ★**폐기**. 진짜 refining = 유가 mean-reversion + 배당 income trap (둘 다 음, peak-out).
- **steel/auto/battery/chemical/telecom**: strict universe ≈ v2 (오염 없음, 각 analyst 재현 확인) = 진짜 신호.
- → 통합 패널 = refining strict2 교체, 나머지 prices.parquet 유지.

## 1. 12산업 rotation tradeable 취합 (각 analyst 이론→통계 verdict)

| 산업 | tier | tradeable 신호 (이론 driver) | 통계 | type |
|---|---|---|---|---|
| **chemical** | ★STRONG | spread(china−brent) +0.539 / china_mchi +0.458 / spread(china−naphtha) +0.450 (margin+demand) | wc_p 0.001, OOS robust | 산업고유(중국 margin) |
| **steel** | ★STRONG | iron_ore_d3 +0.348 (중국 수요 cycle proxy, Bonferroni 간발) | wc_p 0.0025, OOS 유지 | 산업고유(중국 수요) |
| **battery** | ★STRONG | lithium_yoy +0.285 (multi-source LIT/ALB/REMX/NIO 6신호) | wc_p 0.01, OOS 강화 | 산업고유(EV 수요) |
| **auto** | ★STRONG | global_auto_d3 +0.261 (+cli_chg6 + iron_ore 3개) | wc_p 0.025, OOS 강화 | 산업고유(글로벌 판매) |
| **aitech** | tradeable≥2 | game_espo + rate_10y + global_sw + cloud | OOS 유지 | 산업고유(IT/성장) |
| **telecom** | tradeable 2 | 외국인flow(음, well-powered t 3.58) + semi_ppi(음, defensive) | OOS robust | ★MACRO공통(flow) + cycle |
| **bio** | tradeable 2 | rate_overlay(US금리 duration) + bio_global(글로벌바이오 상대) | OOS 유지 | 산업고유(금리 duration) |
| **consumer** | tradeable≥2 | mom_6 reversal(내수 방어) + 곡물 | OOS 강화 | 산업고유(방어 reversal) |
| **semiconductor** | tradeable≥2 | cli_chg + export (SOXX 선행) | OOS 유지 | 산업고유+MACRO |
| **refining** | ★약(monitor 경계) | 유가 mean-rev(음, t -1.96 marginal) + 배당 income trap(음, t -2.48) | OOS robust | 산업고유(peak-out) |
| **financial** | ★tradeable 1 | ★credit_spread d6(음, 대손 UW): rel −0.250 wc_p 0.0155, non-ovlp −0.212, leave-year 전부음, placebo 0.013 | OOS −0.05 약화(underpowered) | 산업고유(신용위험) |
| **shipbuilding** | ★monitor-only | tradeable 0 (BDI/신조선가 = 주가 선행, 사전확약 반증 REJECTED) | OOS flip | — |

- **tradeable≥1 (11산업)** + **monitor-only (1산업: shipbuilding)**.
- ★STRONG 4(chemical/steel/battery/auto) = 산업 고유 cycle 직접신호 + 이론 부호 사전확약 일치 + OOS 견고.
- ★financial(02:22 갱신) = monitor-only → **credit_spread 1 tradeable**. ★비대칭: 금리커브 NIM(term_spread)=시장 timing 채택불가 / 신용위험(credit_spread 대손)=금융 고유. 신용 spread 확대 국면 → 금융 상대 UW(gated overlay, default 0). loan_growth=TENTATIVE 보조(미승격).
- ★전 신호 underpowered(small-n, BY 미생존) = magnitude tentative, 부호·방향만 (자문 F).

## 2. (B) ★residual N_eff = false breadth 정량 (자문 Q-b)

12산업 strict 패널 ~ 공통인자{d_usdkrw, foreign_flow, semi_ppi_yoy} residualize:

| 측정 | raw | residual |
|---|---|---|
| N_eff (participation ratio) | 2.98 [2.42, 3.90] 95%CI | **3.49 [2.77, 4.48]** |
| PC1 분산비 | 0.558 | 0.506 |
| mean pairwise corr | 0.508 | 0.449 |

- ★**residual N_eff ≈ 3.5** = 자문 Q-b "진짜 독립 차원 ~3-4" **데이터 입증**. 12산업 개별 rotation = **false breadth**(12 베팅이 아니라 ~3.5 독립 베팅).
- ★**동시 active tilt 수 = floor(N_eff) = 3 cap**. bet sizing = N_eff(3.5)에 scale (n=12 아님). = over-diversification 환상 차단.
- 공통인자 제거해도 N_eff 3.5 = 외국인flow/USDKRW 잔여 + 산업 cyclical 공통 = 한국 rotation 의 구조적 한계.

## 3. (B) sleeve clustering (residual 상관 hierarchical, raw-PCA 아님)

residual 상관 → 1-corr distance → average linkage:

| k | sleeve 구성 |
|---|---|
| **k=2 (★S6 PCA 확정, 데이터 직접 지지)** | ①[수출 cyclical 9] ②[bio, telecom, aitech 방어·IT 3]. parallel·MP k*=1 → 보수적 2블록만 통계 정당 |
| k=4 (clustering 참고, spurious 위험) | ①[telecom, aitech] ②[financial, consumer] ③[수출 cyclical 7] ④[bio]. ★PC2+ noise선 미달 = 채택 보류, sub-gating 으로 대체 |

- ★**S6 PCA(§3.5) k*=1 → sleeve = k=2 채택**. k=4 hierarchical 은 PC2+ 가 parallel95 미달 = spurious 위험 → sleeve 잘게 쪼개기보다 k=2 sleeve 안 sub-singleton gating 으로 granularity.
- residual 상관 상위: battery~chemical +0.79, semi~battery +0.77, chemical~steel +0.69 = ★수출 cyclical 강하게 묶임(외국인flow 잔여 + 글로벌 수요 cyclical 공통).
- residual 상관 하위: bio~전산업 <0.27 = ★bio singleton 격리 자명(임상 idiosyncratic).
- ★**자문 권고 vs 데이터 텐션**: 자문 = "idiosyncratic-cycle 산업(refining/shipbuilding) thin sleeve/singleton 보존(대형 cyclical 희석 시 residual alpha 죽음)". 단 데이터 = refining~steel +0.632 / ship~steel +0.684 = 수출 cyclical 에 묶임 = ★refining strict2 도 외국인flow 잔여 노출 강. → **운영 권고**: 수출 cyclical sleeve 안에서 refining/shipbuilding = **sub-singleton gating**(sleeve 멤버지만 고유 cycle 신호 발현 시만 독립 tilt, 평소 sleeve risk-parity).

## 3.5 ★S6 residual-PCA sleeve 실측 (plan §8 D1~D7) — ★flat 경향 결정적 발견

> ★audit minor 1 반영: 좀비 종목 마스킹(obs_ratio<0.5 OR nonzero<0.3 제외, bio 케어젠/aitech 셀바스AI 류 신규상장·거래정지).
> N_eff 거의 불변(residual 3.49→3.52) = 좀비는 eq-weight 희석만, 구조 영향 미미 = 결론 robust.

| D | 측정 | 결과 |
|---|---|---|
| **D1 eigenvalue spectrum** | residual corr 고유값 + parallel analysis + MP edge | ★PC1=6.04(분산 50.4%), PC2=1.15/PC3=1.03 < parallel95(1.83/1.59). **k*(parallel)=1, k*(MP)=1** |
| **D2 PC1 loading** | 12산업 PC1 부하 | 동부호 광역(외국인flow 잔여 공통) |
| **D3 varimax 블록 (k=2)** | PC1=[수출cyclical 9산업] / PC2=[bio, telecom, aitech 방어·IT 3] | 깨끗한 2블록 분리 |
| **D7 외부앵커 회귀** | PC score ~ 공통인자 | PC1~foreign +0.168(잔여 flow), PC2~공통인자≈0(방어 idiosyncratic) |
| **D7b subsample 안정성** | PC1 loading 前後半 rank corr | 0.755 = 안정(spurious 아님) |

★**결정적 발견**: residual(공통인자 제거)에서도 **PC1이 분산 50.4% 지배 + k*=1**(parallel·MP 둘 다) = 한국 12산업은
residualize 후에도 단일 공통인자 지배 = **깨끗한 sleeve 분리 데이터상 약함**(plan §8 rule "1→flat"). residual N_eff 3.5
(participation ratio)와 정합 = "독립 차원 ~3.5지만 그 중 1개가 압도적". → **운영 권고**:
- **보수적 k=2** (데이터 직접 지지): [수출 cyclical 9] vs [방어·IT 3=bio·telecom·aitech]. D3 varimax 깨끗 분리 + D7 anchor 부호 정합.
- k=4(hierarchical clustering 권장)는 PC2+ 가 noise선 미달 = **spurious 위험** → ★sleeve=k=2 채택, 그 안 산업별 gating 으로 granularity 확보(sleeve 잘게 쪼개기보다 sub-singleton gating).
- ★bio singleton 격리 일관(residual 상관 <0.27 + PC2 방어 블록). refining/shipbuilding=수출 sleeve 묶임(strict2도 flow 잔여)=sub-singleton gating.

## ★audit minor 2~4 반영 (non-blocking)
- **minor 2 (semi_ppi 단위근)**: semi_ppi_yoy ADF p=0.556(단위근 의심). ★단 measure 에서 yoy(=12M diff)로 이미 차분 변환 적용 = level 회귀 아님 → spurious 영향 제한적. residualize 공통인자로만 사용(forward 예측 신호 아님) = 영향 추가 제한. 잔존 risk = caveat 박제.
- **minor 3 (chemical magnitude)**: chemical "spread +0.539"는 ★full panel = magnitude inflation. ★strict NCC 6종 +0.427 병기 (chemical-analyst). STRONG 판정 자체는 strict 에서도 정당(+0.427 OOS robust). 통합 시 strict +0.427 사용.
- **minor 4 (auto iron_ore)**: auto 의 iron_ore 신호 = ★tentative 라벨 + "리플레이션 prior 사후보강(post-hoc)" 명시. ⛔사전등록 신호로 격상 금지. auto primary = global_auto_d3(사전등록 STRONG), iron_ore = post-hoc 보조.

## 4. (D) 2층×3층 결합 (double-counting 회피)

- ★**자본 = 곱**: w_j = W_i(산업비중 L2 rotation) × v_{j|i}(산업내 종목비중 L3 selection, Σ=1) = fund-of-sleeves.
- ★**double-counting 회피 = L3 within-industry macro-neutral demean**: L3 selection 신호를 산업 내 demean → 산업 자체 KRW/flow beta 제거. macro exposure 전부 L2 소유, L3 = idiosyncratic selection alpha 만.
- ★**telecom 외국인flow = 전산업 공통 L축 1회계상**(중복 차감): telecom tradeable "외국인flow" = MACRO 공통 인자 = 2층 sleeve 배분에서 이미 계산 → telecom 고유 rotation 으로 ★중복 계상 금지(L축 1회). telecom 진짜 고유 = semi_ppi(반도체 cycle 방어) 한정.
- 검증: 조립 후 portfolio net common-factor(KRW/flow/export) exposure → 의도 L2 tilt 와 대조. 실현 KRW beta > 의도면 L3서 neutralize.

## 5. (E) hierarchical sleeve-gatekeeping FDR (flat BY 금지)

- ★flat BY(12×K) = power 학살(N_eff~3.5인데 12K 평탄보정). → **2단계**:
  1. **sleeve-level FDR**(4 sleeve × K, 고power) 먼저 test → 통과 sleeve 만,
  2. 통과 sleeve 내 **within-sleeve local FDR**(Yekutieli 2008 conditional).
- **program-level DSR/PSR**: 12산업 × 신호 × regime축 전체 시도 config = forking-path → 단일 deflated SR = "rotation 프로그램 켤지" conviction gate (per-sleeve FDR 와 별개).
- ★현 단계 = sleeve 미확정(S6 PCA 후 확정) → 본 통합은 sleeve 구조 **제안**(k=4) + hierarchical FDR **설계**. 실제 sleeve-gatekeeping 적용 = S7 통합 yaml.

## 6. (C) base + tilt + gated 설계 (자문 수렴)

- **base = sleeve-level residual risk-parity** (각 sleeve 등위험, singleton bio 도 한 sleeve몫 risk budget = 자연 floor). 등위험 ≠ 등weight.
- **tilt = additive-on-active-share + clip 병행**: per-name clip(Δmax, 단일종목 blowup) + active-share budget(Σ|Δw|≤τ, τ≈20-40%, aggregate active risk). ★multiplicative 금지(low-base singleton refining 서 gate 열려도 tilt≈0 구조적 함정).
- **over-trade 3중 차단**: ① hysteresis no-trade band(|s_new−s_cur|>band 일 때만) ② persistence(regime k개월 지속/EWMA) ③ cost-aware gate(기대 tilt benefit > turnover cost, KR STT 0.2% 비대칭). 소형시장 sector-timing = cost gate 가 주 필터.
- **κ(공격성) = program DSR × N_eff(3.5) × live-OOS falsification**. 약신호 sleeve κ→0 default. tilt capacity = standalone IC/Sharpe 신뢰도(base weight 비례 금지).
- **monitor-only 1산업(shipbuilding) = default weight 0** (rotation tilt 0, tradeable 0). financial = credit_spread 1 tradeable(약, gated overlay default 0, 신용 spread 확대 시만 UW tilt).

## 7. ★공통 macro 분리 (시장 timing vs 산업 고유 rotation)

| 신호 | 분류 | 처리 |
|---|---|---|
| cli_chg(경기선행) | ★MACRO 공통 (12산업 거의 동일, N_eff≈1) | 시장 전체 timing(1층 자산배분 성분). 산업 rotation 차등 아님 |
| 외국인 flow | ★MACRO 공통 (L축 1회계상) | 2층 sleeve 배분에서 1회. telecom/steel 고유 rotation 중복 계상 금지 |
| semi_ppi yoy | 반(半)공통 (반도체 cycle, IT/통신 방어 분기) | telecom/aitech 고유 rotation 으로 인정(부호 분기 = 진짜 차등) |
| 산업 고유 cycle (철광석/리튬/유가/글로벌차/중국margin) | ★산업 고유 rotation | 진짜 sleeve tilt 신호 (residual alpha) |

## 8. verdict (통합)

- ★STRONG 4(chemical 중국margin / steel 철광석 / battery 리튬 / auto 글로벌차) = 산업 고유 cycle 직접신호 = ★진짜 rotation alpha. residual 후 잔존.
- tradeable≥1 7산업(aitech/telecom/bio/consumer/semiconductor + refining 약 + financial credit_spread) = 이론+통계 채택하나 underpowered = conservative cap.
- monitor-only 1(shipbuilding) = default 0.
- ★residual N_eff 3.5 = 동시 3 sleeve tilt cap. ★S6 PCA k*=1 → sleeve=k=2([수출cyclical 9]/[방어·IT 3=bio·telecom·aitech]). bio singleton 격리. refining/shipbuilding = 수출 sleeve 내 sub-singleton gating.
- 정직단서: 전 신호 underpowered(magnitude tentative) / ★S6 residual-PCA = k*=1 flat 경향(공통인자 지배 극심, k=2 보수 채택) / hierarchical FDR·2층×3층 배선=S7 supervisor / WIRE5 go-live 미접촉.

## 재현
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
cd study-research/eq_kr/industries/_rotation
"$PY" measure_integration.py   # validation-integration-v1.json (residual N_eff + sleeve clustering)
```
