---
tags: [type/round-1, domain/equity, sector/steel, scope/equity-kr, phase/hypothesis-preregister]
date: 2026-06-05
purpose: S1 가설 사전등록 — 부호 one-sided 사전확약(데이터 접촉 前 동결, HARKing 방지). 측정 family 크기 = 가설 수.
---

# steel(철강) 가설 사전등록 (측정 前 동결)

> ★본 문서 = **측정 前** 작성. 부호 사전확약 = HARKing 방지 1차 증거. 학습 가설 수 = FDR family 카운트(폐기분 포함).
> theory-notes.md §1 메커니즘 기반. archetype = cyclical (초자산집약 commodity 장치산업).

## 가설 list (부호 사전확약)

| H | 가설 | 신호 | 사전확약 부호 | 우선순위 | falsifier |
|---|---|---|---|---|---|
| **H1** ★ | **capex_ratio asset growth anomaly**: 高 유형자산/총자산 종목 = 과잉증설 → forward 약 | capex_ratio | ★음(-) | ★최우선 (dispatch capex 가설) | IC ≥ +0.03 (高 capex→강) |
| **H2** ★ | **ppe_yoy 증설 가속**: 유형자산 yoy ↑ = 사이클 정점 증설 → forward 약 | ppe_yoy | ★음(-) | ★최우선 | IC ≥ +0.03 |
| **H3** | **PBR value premium**: 저PBR(청산가치 저평가) → forward 강 | pbr_z | 음(-) | 高 | PBR IC \|ρ\|<0.03 전 horizon |
| **H4** | **PER 왜곡(cyclical EPS)**: 정점 peak-EPS / 다운 trough → PER 무효 | per_z | 비유의/무효 | 中 (점검) | PER IC 유의(\|ρ\|>0.05 p<0.05) |
| **H5** | **momentum reversal**: 12M 누적수익 최강 = 사이클 정점 → 되돌림 | mom_12_1/mom_6 | 음(-) (cyclical 완만→약 prior) | 中 | IC ≥ +0.03 (continuation) |
| **H6** | **단기 reversal**: 1M 단기수익 → 1M forward 음 | rev_1m | 음(-) | 中 | IC ≥ 0 |
| **H7** | **저변동 quality**: 저성장·고배당 철강 = defensive demand, 저변동 outperform | vol_60 | 음(-) (저vol→강) | 中 | IC ≥ +0.03 |
| **H8** | **재고순환**: 재고/총자산 高 → forward 약 (재고peak→주가bottom 선행) | inv_ratio | 음(-) prior (반도체서 반증된 바 有) | 中 | IC 일관 양 |
| **H9** | **R&D**: 무형/총자산 (철강 R&D 미미) | rnd_ratio | 양(+) 약 | 低 | — |
| **H10** | **외국인 flow conditional**: 외국인 강매수 regime서 팩터 IC 약화 (철강 외국인 비중 < 반도체) | flow regime 축 | conditional 약 | regime 변수 | regime IC 차 <0.02 |
| **H11** | **중국 철강 cycle / 철광석 (timing)**: 산업 공통 시계열 = cross-sectional 부적합 | SLX/VALE | forward 약 (동행 dominant) | regime/timing 변수 | 산업 forward IC \|ρ\|>0.10 p<0.05 |

## measure family (단일 FDR, 사전 고정 = garden-of-forking-paths 차단)

cross-sectional 측정 가능 신호 = {capex_ratio, ppe_yoy, pbr_z, per_z, mom_6, mom_12_1, rev_1m, vol_60, inv_ratio, inv_yoy, rnd_ratio} × horizon × powered regime cell.
- timing/regime 변수 (SLX/VALE/외국인 flow) = cross-sectional 신호 아님 → regime conditioning 또는 산업 timing 측정.
- ★family 멤버십 = 측정 결과 본 후 재정의 금지(momentum만 떼서 보기 등).

## archetype 사전선언 (PIT attestation)

- archetype = **cyclical** (초자산집약 commodity 장치산업). valid_from = 2019-01-01 (구조적 cyclical 일관, transition 없음).
- primary_metric = **PBR** (peak/trough-EPS 왜곡으로 PER 무효 prior). secondary = asset_stable (배당/저변동, prob~0.2).
- ★실측 검증: momentum 음(reversal) → cyclical 지지 / capex_ratio 음 → asset growth anomaly = 자산집약 정합.

## ★dispatch capex 일반화 가설 (최우선)

자동차 capex_ratio(음, high_confidence) = structural_prior. 철강 = 자산집약 더 극단 → H1/H2 재현 시 자산집약 4섹터(화학/정유/조선/철강) 일반화 1보. 반증(양)이면 산업 특수성(capex=capacity 성장 신호) 보고 = 메인 종합 대상.

## ★small-breadth 주의 (frame §M.12)

철강 universe = 23종(avg cross-section ~20) = small-universe. cross-sectional IC magnitude 과대 위험. breadth-adjusted IR(IC·√breadth) 병기 + magnitude haircut 의무. significance(t)는 신뢰하되 point estimate 보수 cap.
