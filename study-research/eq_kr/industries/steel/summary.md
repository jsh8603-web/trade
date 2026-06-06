# steel(철강·금속) 산업 요약 — eq_kr conditional IC capsule

> capsule 산출물(_ledger-guide §1 필수). summary.yaml(exposure card) + theory-notes + round-1 + validation-cross-sectional + candidate-ledger + research-log + 15axis-audit + raw-v3/*.py 와 함께 산출.
> ★self-audit 참고용. 최종 verdict = G-C 독립 audit(별 세션).

## 한 줄 결론

철강 = **cyclical 초자산집약** 산업. 가격 momentum이 **음(reversal, IC -0.181)** = battery(양)와 반대 = archetype 판별. ★**capex_ratio 음(asset growth anomaly)** = dispatch capex 일반화 입증(자동차 재현). valuation = **PBR○ PER✗**(peak/trough-EPS trap). ★★small-universe(23종) magnitude haircut 의무.

## 핵심 발견 (4)

1. **momentum reversal (cyclical 증거)**: mom_12_1 → 12M forward IC **-0.181** (t=-4.42, CPCV 1.00, within 100%, leave-episode 생존, BY 생존). 사이클 정점 종목 되돌림 = cyclical archetype 핵심. battery(양 +0.086)와 부호 반대.

2. ★**capex_ratio asset growth anomaly (dispatch capex 일반화)**: 유형자산/총자산 → y_60d forward IC **-0.084** (wc_p=0.0005, walk-forward OOS 부호유지). 과 capex(과잉증설) 종목 forward 약 = Cooper-Gulen-Schill asset growth anomaly. ★자동차(high_confidence)가 철강(초자산집약)서 재현 = **자산집약 4섹터(화학/정유/조선/철강) 일반화 1보**.

3. **valuation PBR○ PER✗**: PBR cross-sectional 3M/6M/12M 단조 일관(IC -0.10~-0.16, BY 생존 3개, CPCV 1.00) = value premium 작동. PER 전 horizon 비유의 = peak/trough-EPS trap(정점 peak-EPS + 다운 적자 trough 양방향 왜곡). 반도체/자동차 동형.

4. **vol_60 저변동 quality**: 저변동 종목 outperform(IC -0.117 6M, BY 생존, conditional y_60d wc_p=0.0005). 철강 = 저성장·고배당 defensive 성격(theory M6).

## conditional IC surface (dispatch 본체)

- ★**KRW_neutral = 증폭축** (반도체 KRW_weak과 다름 = 철강은 중국 cycle dominant, 환율 부차). KRW_neutral regime서 mom_6/vol_60/pbr_z/capex 모두 증폭.
- ★**walk-forward OOS** (IS 2019-22/OOS 2023-26): KRW_neutral 핵심 신호 전부 OOS 부호+magnitude 유지 = **in-sample artifact 아님** = conditional CONFIRMED(tentative).
- family_2 interaction(KRW_neutral)은 방향 정합이나 t=-1.63 비유의(small-n) — walk-forward가 verdict 근거.

## S5 역공격 (실측)

- POSCO drop -> -0.165 생존 / leave-2021 -> -0.161 생존 (momentum 단일종목·episode 종속 아님).
- PBR size 위장: Fama-MacBeth PBR|Size t=-1.98(경계, PBR 우위이나 small-universe hedge).

## verdict 라벨

| 신호 | verdict | 비고 |
|---|---|---|
| cs_mom_12_1_reversal | PARTIAL->강 | BY 생존, magnitude small-universe hedge |
| cs_vol_60_lowvol | PARTIAL->강 | BY 생존, defensive quality |
| cs_pbr_z (3M/6M/12M) | PARTIAL->강 | BY 생존 3개, PBR value premium |
| ★cs_capex_ratio | TENTATIVE DIRECTIONAL | dispatch capex 가설 입증, 통합 BY 미생존 |
| per_z | REJECTED | peak/trough-EPS trap |
| customer momentum | REJECTED | forward 예측력 부재 |
| **산업 전체** | **PARTIAL** | 방향·significance robust, small-universe magnitude hedge |

## ★small-universe caveat (frame §M.12)

철강 universe = 23종(avg cross-section ~20) = 반도체(73)의 1/4. point estimate(momentum -0.181) literal 인용 금지, breadth-adj IR(-0.81) + 50% magnitude haircut 일관 적용. 방향·significance(t, BY)는 신뢰.

## 15축 self-audit 요약 (상세 = 15axis-audit.md)

- Hard-fail 4 (B·C·D·I): B PASS(합성0) / C PASS(추적성) / D PASS(PIT) / **I PARTIAL**(생존편향 — 현 스냅샷, 단 철강 상폐 드뭄).
- PARTIAL/주의 축: I(생존편향 잔존) / G(small-universe effective-N) / K(통합 BY 미생존) / J(net-cost marginal).
