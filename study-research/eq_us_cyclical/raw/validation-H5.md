---
tags: [type/validation, study/eq_us_cyclical, hypothesis/H5]
date: 2026-05-30
verdict: REJECT (sign 분리 미입증 — 일별 데이터 marker beta 압도)
n_days: 6591
period: 2000-01 ~ 2026-05
---

# H5 검증 — rate_beta name-specific (long-duration 음, value-cyclical 양)

## 가설
"10Y 국채 금리 상승 → 고멀티플/early-cycle(SOXX, XLY 일부) 부정(multiple contraction) / value-cyclical(XLE, XLF) 긍정(NIM·인플레 헷지). 종목간 β 부호 분리(sign flip)."

## 데이터
- **종속**: 섹터 ETF 일별 수익률 (2000-2026, 6591일)
- **선행/동시**: ΔDGS10 일별 차분

## 결과 — full-sample β = cov(r_sector, ΔDGS10) / var(ΔDGS10)
| 섹터 | β | Rank-IC | n |
|---|---|---|---|
| **장기 가정 long-duration**: XLY (Consumer Disc) | **+0.0561** | +0.211 | 6591 |
| **장기 가정 long-duration**: SOXX (반도체) | **+0.0874** | +0.227 | 6207 |
| **장기 가정 value-cyclical**: XLE (Energy) | **+0.0820** | +0.244 | 6591 |
| **장기 가정 value-cyclical**: XLF (Financials) | **+0.0883** | +0.269 | 6591 |
| XLI (Industrials) | +0.0662 | +0.259 | 6591 |
| XLB (Materials) | +0.0630 | +0.215 | 6591 |
| Defensive XLP | +0.0239 | +0.110 | 6591 |
| Defensive XLU | +0.0147 | +0.010 | 6591 |
| Defensive XLV | +0.0366 | +0.159 | 6591 |
| 벤치 SPY | +0.0580 | +0.240 | 6591 |

## 평가
- ★ **모든 섹터 β > 0** (defensive 포함). **가설의 부호 분리(long-duration 음 vs value-cyclical 양) 완전 기각**.
- 가정 long-duration(XLY/SOXX)과 가정 value-cyclical(XLE/XLF)이 **둘 다 양수이고 XLF가 가장 큼**. 부호 flip 없음.
- defensive(XLU=+0.015) < cyclical 평균(β~0.07) — 단순 마켓 베타 양상.
- direction.md H5 반증 임계 = "rate_beta 횡단 분산이 멀티플/듀레이션 프록시로 설명 X" → 횡단 분산 자체가 작고 (0.015~0.088), 모두 양수라 듀레이션 부호 매핑 불가.

## 시변(60D rolling β std)
| 섹터 | mean β | std β | min | max |
|---|---|---|---|---|
| XLY | +0.056 | 0.073 | -0.187 | +0.295 |
| SOXX | +0.085 | 0.106 | -0.317 | +0.453 |
| XLE | +0.082 | 0.093 | -0.104 | +0.581 |
| XLF | +0.090 | 0.094 | -0.104 | +0.476 |
| XLU | -0.002 | 0.068 | -0.177 | +0.306 |

- 시변 큼 — 특정 sub-period(예: rate-shock 국면)에서 부호 flip 가능성 잔존.
- XLU(Utility, 강 long-duration defensive) full-sample β 거의 0 → 일부 sub-period 음 β 가능.

## 함정 / 한계
1. **일별 데이터의 마켓 베타 지배**: 일별 ΔDGS10이 상승할 때 = 보통 risk-on 환경(주가 동조 상승). 모든 위험자산 β > 0이 자연스러움. **rate-shock vs risk-on을 분리해야 H5 검증 가능**.
2. **섹터 ETF는 종목 단위 name-specific 검증이 아님**: H5는 본질적으로 종목 단위(고멀티플 종목 vs value 종목)인데 본 검증은 섹터 평균. **종목 단위 데이터(EDGAR 펀더 + 종목 가격) 적재 후 명확 결판**.
3. **rate 상승 자체가 두 채널 동시 작용**: (i) discount rate 상승 → multiple contraction (장기 dur 음) (ii) growth 신호 → 이익 상승 기대 (cyclical 양). 일별 데이터로 두 채널 분리 X. **regime/contextual conditioning(Fed surprise vs growth surprise)으로 분해 필요**.

## 시스템 코드화 결론
- **블록3**: `rate_beta ↔ fwd_ep` direct edge prior 0.5 → **재검토 (sign 미입증, 일별로 분리 어려움)**. 진정한 검증은 종목 단위 + Fed surprise/growth surprise 분리 후.
- **블록4**: `rate_beta` base 0.12 modulate_by [regime, name_specific] direction "rate-shock + long-duration → 가중↑"은 **현재 일반 데이터로 정당화 어려움**. base 0.08 이하 + 종목 단위 검증 (EDGAR 적재 후) 전까지 보류.
- **블록5**: hypothesis_id=rate_duration_namespecific → **(거부 후보) flag 우세** (현재 데이터). 종목 단위 검증 시 활성화 가능.

## 결론 — H5 verdict
**REJECT (현 검증 단계)**. 일별 섹터 데이터로는 부호 분리 미입증, 모든 cyclical/defensive 섹터 β > 0. 진정한 검증은 (i) 종목 단위 EDGAR 펀더 적재 (ii) rate-shock vs risk-on 분리(Fed surprise 변수) (iii) regime conditional 분해 후 가능. 현재 prior 하향 + name_specific 활성화 보류.
