---
tags: [type/theory-notes, domain/inv, scope/equity-kr, sector/shipbuilding]
date: 2026-06-05
owner: shipbuilding teammate (kr-equity, opus 1m)
purpose: S1 리서치 정독 — 조선 cycle 메커니즘·가설·부호 사전확약 (측정 前 동결). 결론·목표가·in-sample 백테스트는 증거로 안 씀, 메커니즘만 추출.
---

# 조선(shipbuilding) cycle 이론 정독 + 가설 사전등록

> **S1 = 가설의 원천** (frame §3). 리서치 = 메커니즘·부호 사전확약. 증거는 우리 PIT 측정.
> source = ① Stopford "Maritime Economics" (해운-조선 cycle 표준) ② Cooper-Gulen-Schill 2008 JF (asset growth anomaly)
> ③ Damodaran (deep-cyclical valuation, normalized earnings) ④ Clarkson Research (수주/선가 표준 데이터)
> ⑤ 국내 증권사 in-depth (메리츠/NH/한투 조선 cycle 리포트, 운임→수주→선가 순서)
> ★Gemini API 리서치 종합 (2026-06-05, /tmp/ship-result1.txt) — sell-side 결론·목표가 X, 메커니즘만.

## 1. 조선 cycle 메커니즘 (실물 → 주가 선후관계)

조선 = **deep-cyclical** (극심한 경기민감). 핵심 = **주가가 실물지표(수주·선가)보다 선행**.

```
운임 상승(BDI/SCFI 추세반등, 최선행)  ← 선사 현금흐름↑ → 발주 여력
  → 주가 상승 시작 (기대 선반영, 6M~1Y 선행)
  → 신조선 수주 증가 (동행/소폭 후행, Clarkson)  ← "수주 서프라이즈" 아니면 주가 이미 반영
  → 신조선가 지수 상승 (후행, 도크 차고 협상력 우위 = 확산국면 확인)
  → 후판 가격 상승 (원가↑, 사이클 중후반 마진 압박)
  → 주가 하락 전환
```

★**측정 함의**: 운임·수주가 주가보다 **선행이 아니라 후행**(주가가 먼저 움직임) → 운임 lagged → 조선주 forward 예측력 ★약함 예상 (supply-chain alpha 후보 = §D forward-falsifier 작동 예상).

## 2. 가설 사전등록 (부호 one-sided pre-commit, 데이터 접촉 前 동결)

★FDR family = 학습 가설 수 카운트. 측정 結 본 후 재정의 금지.

| H | 가설 (메커니즘) | 부호 prior | 반증조건 | source |
|---|---|---|---|---|
| **H1** | 원화약세(USDKRW↑) → 조선 수출주 수익성↑ → forward 양 (KRW_weak regime 증폭) | KRW_weak서 **양 또는 신호증폭** | KRW_weak서 IC 약화/부호반전 | 증권사 환율 민감도 |
| **H2** | PBR value (저PBR=싸다) → forward 양 (저z→고return = IC 음). cyclical PBR 밴드 하단 진입 | **음 IC** (value premium) | PBR IC 0 근접 또는 양(역전) | Damodaran deep-cyclical |
| **H3** | ★PER = peak-EPS/적자 trap → cross-sectional 무효 (적자기 분모 음 / 정점기 저PER 함정) | **무효/불안정** (BY 미생존 예상) | PER이 안정적 음 IC | Damodaran value trap |
| **H4** | momentum = cyclical 정점 reversal (battery 양 momentum 과 반대, 반도체 동형) | **음 IC** (reversal) | momentum 양 (지속) | Daniel-Moskowitz 2016 |
| **H5** | ★capex/ppe asset growth = ★two-sided (사이클 후반 증설=음 과잉투자 / 초입 재가동=양 수주proxy) | **음 약 + 양 가능** (데이터 판정) | — (탐색) | Cooper-Gulen-Schill 2008 + 조선 특수성 |
| **H6** | 재고(inv_ratio) = ★조선 재공품/미인도선 → 수주호황기 재고↑=미래매출 = ★양 가능 (반도체 음 prior 반대) | **양 가능** (two-sided) | — (탐색) | 조선 회계 특수성 |
| **H7** | VIX 고베타 = risk-off 시 조선 최대 하락 (contemporaneous 음 β) | **음 β** (고베타) | VIX β 0 근접 | 증권사 고베타 |
| **H8** | 운임(BDI)/유가/글로벌조선 lagged → 한국 조선 forward (supply-chain alpha) | **양 (lead-lag)** but ★주가 선행이라 약 예상 | 전 lag 비유의 = REJECTED | Cohen-Frazzini 2008 |
| **H9** | ★산업 베타(슈퍼사이클 timing) 지배 → cross-sectional selection 신호 ★구조적 약함 | cross-sectional ★약 (산업 분산 낮음) | cross-sectional IC 강·BY 생존 | Maritime Economics §cycle |
| **H10** | ★업종 rotation: 신조선가/수주가 진짜 driver but ★주가가 6-12M 선행 = 후행지표 → rotation 신호 부적합. BDI=선종불일치(벌크 vs LNG/컨테이너/탱커) | rotation 후행지표 ★약/반증 | 신조선가 proxy IC 강·부호확약 일치 | 하나증권 최광식/메리츠 배기종/NH 2023 |

★**업종 rotation 이론 (team-lead 지시, Gemini 리서치)**: ① 신조선가(Clarksons) = ★주가가 6-12M 선행 = 후행지표 = rotation 선행신호 부적합(하나증권 최광식 다수 리포트). ② BDI 부적합 = ★선종 불일치(결정적): BDI=벌크선(철광석/석탄), 한국 조선=LNG/ULCS 컨테이너/VLCC 탱커. + 운임=해운사 수익(조선 수주 아님) + 18M lag + 주가 선행. ③ 신조선가 무료 proxy = 진짜 없음(Clarksons/SCFI 유료, 수주잔고=동행/후행). 후판가=이중성(원가-/수요+). 해운사 주가가 이론상 선행 proxy이나 실측 음(주가 선행 입증).

★**capex 일반화 가설 (team-lead 박제)**: 자동차/반도체 capex_ratio 음 prior(structural_prior_high)가 조선엔 ★two-sided.
조선은 orderbook 기반 → asset growth 가 (a) 과잉투자 음 (b) 수주확대 양 양쪽. H5/H6 = 부호 데이터 판정 (one-sided 단정 금지).

## 3. archetype 판정

- **archetype = cyclical** (orderbook 수주 cycle, deep-cyclical). valid_from 2019-01 사전선언.
- primary_metric = **ev_ebitda** (peak-EPS 경계, PBR 밴드 보조). PER ✗ (적자/정점 trap, H3).
- ★단 반도체(ASP cycle)·battery(EV growth)와 다른 cyclical sub-type = **수주잔고(orderbook)·운임 선행 cycle**.

## 4. ★정직 단서 (측정 前 예상 = HARKing 방지)

- 조선 universe ★협소 (시총 floor 통과 9종, 완화 후 16종 = 반도체 85종 대비 ★구조적 breadth 부족).
- 산업 베타 지배(슈퍼사이클 2022→2025 누적 5x) → cross-sectional selection 신호 ★약 예상 (H9).
- PER 적자 지배 (2021-22 적자 多) → cross-sectional valuation 왜곡 예상 (H3).
- = **tradeable selection 신호 약할 가능성 高** (사전 인지, G-G v2 FAIL 가능성 = 측정으로 확정).
