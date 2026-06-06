---
tags: [type/summary, domain/equity, sector/auto, scope/equity-kr]
date: 2026-06-05
purpose: 자동차 conditional IC capsule 사람용 요약. SSOT = summary.yaml + validation-*.json.
---

# automobile(자동차) conditional IC surface — 요약

## 한 줄 결론

자동차(cyclical, 판매량 cycle)는 ★가격 momentum/reversal 무효(walk-forward OOS flip = in-sample artifact)이고, 진짜 신호는 ★PBR value premium(y_60d OOS robust) + capex_ratio(asset growth, 신규 발견) 둘이다. PER은 peak-EPS trap으로 무신호. 통합 단일 FDR(m=168) 보정 후에도 survivors=5(PBR 2 + capex 3) 생존 = 반도체(0)보다 강한 결과. ★단 universe 17종 협소 = magnitude는 방향·권역만(점추정 금지), small-N hedge.

## 측정 본체 = conditional IC surface (dispatch 원의도)

측정 = IC(지표, regime 36셀, horizon) — "어느 국면에 어느 지표가 자동차 forward return을 예측하나".
- regime = Macro 4 × KRW 3 × 외국인flow 3 (36셀 full N>=24=0 → 단일축 + 2축 merge=supervisor).
- horizon = y_5d / y_20d(메인) / y_60d.
- regime 분포(2019~): Macro[Slowdown 31/Recovery 26/Reflation 22/Overheat 10] × KRW[neutral 41/weak 38/strong 10] × flow[neutral 48/sell 22/strong_buy 19].

## 핵심 발견 4

### 1. 가격신호 = REJECTED(OOS) — in-sample artifact
- mom_6/mom_12_1/rev_1m/vol_60 = unconditional 전부 비유의(wc_p > 0.4).
- ★walk-forward OOS(IS 2019-22 / OOS 2023-26): 가격신호 conditional cell 거의 전부 부호반전. 예: mom_6 KRW_weak IS=-0.098 → OOS=+0.150. rev_1m KRW_weak IS=-0.121 → OOS=+0.197.
- family_2 interaction(mom_12_1/vol_60 KRW_weak) t=2.18/2.75 유의하나 부호 양(+) = momentum continuation(반도체 reversal 음 증폭과 반대) + cell OOS flip = 보류(flip-register).
- ★자동차 momentum 무효 = 반도체보다 약(volume cycle 점진 vs ASP cycle 급락). weight ~0.

### 2. ★PBR value premium (y_60d) = PARTIAL CONFIRMED (OOS robust)
- uncond y_60d IC=-0.108, IS=-0.108 → OOS=-0.117 = ★OOS 부호+magnitude 유지.
- Slowdown regime wc_p=0.0005(raw_p_min) / flow_strong_buy regime서 강(theory M3 정합).
- ★size 통제 후 독립(Fama-MacBeth pbr t=-2.67, size t=-0.38) = size 위장 아님.
- ★단 universe 17종 = magnitude 과대(small-universe). 방향·breadth-adj 권역만. y_20d 약(t=-1.39).

### 3. ★capex_ratio (유형자산/총자산 = asset growth) = PARTIAL CONFIRMED (★자동차 신규 진짜 신호)
- uncond y_60d IC=-0.103 wc_p=0.0015. walk-forward IS=-0.044 → OOS=-0.172 = ★OOS 강화.
- ★통합 단일 FDR m=168 survivors=5 中 capex 3 cell 생존.
- size 통제 후 독립(t=-3.78). ★단 size factor 자체도 유의(t=-2.23) = small-cap effect 공존. multivariate서 capex 독립(t=-3.38).
- prior 음(Cooper-Gulen-Schill 2008 asset growth anomaly) 정합. ★자동차 = 자산집약 장치산업 = anomaly 강(반도체 신규지표 무신호와 차등).

### 4. PER = peak-EPS trap 무신호
- PER 횡단면 IC≈0(wc_p=1.00). 자동차 = peak-EPS trap 대표산업. cyclical archetype(PBR○ PER✗) 지지. E/P·EV-EBITDA 대체 권고.

## S5 역공격 (최강 반증 3종 → 전부 기각)

| 반증 | 검정 | 결과 |
|---|---|---|
| A1 capex = size 위장? | size-bucket 내 capex IC | ★대형(-0.168)·소형(-0.118) 양쪽 음 = size 위장 아님 |
| A2 PBR/capex = 전동화 episode 종속? | pre-2023 vs 2023+ | ★둘 다 부호 일관(pbr -0.105/-0.117, capex -0.044/-0.172). capex는 2023+ 강화(정직 명시) |
| A3 현대차/기아 대형주 의존? | 005380/000270 LOO | ★pbr·capex 부호 robust(ex둘다 pbr -0.106/capex -0.083) |

## verdict
- 산업 전체 = PARTIAL — 가격신호 무효, PBR value + capex asset growth = OOS robust.
- ★dispatch 원의도 답: 가격신호 conditional 전부 OOS flip(국면 무관 무효) / PBR Slowdown·flow_strong_buy서 강 / capex 전 regime robust. = "regime 변조보다 unconditional valuation+asset growth가 본질"(반도체 KRW_weak interaction 패턴과 다름).
- ★3산업 momentum: battery(양 CONFIRMED growth) / 반도체(음 reversal PARTIAL ASP) / 자동차(음 reversal OOS flip 무효 volume) = cycle 원천이 momentum 강도 가름.

## hard-fail self-check
- B 실데이터 PASS (합성지문: USDKRW 2022-10=1429, 현대차 2020-03=65,900→2024-07=286,000, DART ppe 30.5~48.7조)
- C 추적성 PASS / D PIT PASS (CLI_PUB_LAG=2 + DART rcept_dt + forward shift)
- I 생존편향 PARTIAL (쌍용차→KG모빌리티 구조조정 누락 = 정직 격하)
- ★hard-fail 0 (B/C/D PASS, I PARTIAL)

## 정직 단서 (over-claim 회피)
- ★universe 17종 협소 = 모든 magnitude hedge(방향+권역만). small-N TENTATIVE/PARTIAL. OOS 검증 완주. capex size 공존 정직 명시.
