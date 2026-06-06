---
tags: [type/candidate-ledger, domain/equity, sector/battery, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# battery(2차전지) 지표 후보 원장

> 측정 cross-section = 29종(시총≥3000억∧ADV floor). breadth 작음 → magnitude hedge 의무. n_months 50-83 (Tentative tier).
> ★반도체 파일럿 대조: 둘 다 cyclical archetype 이나 battery momentum = **양 continuation** (반도체 음=reversal). archetype 내 이질성 증거.

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| cs_mom_6m | momentum | PARTIAL | uncond y_60d IC +0.075 (wc_p=0.0125, n=80), flow_neutral cell +0.123 (wc_p=0.001, 최강). ★walk-forward OOS 부호+magnitude 유지(IS+0.078→OOS+0.072). ★단 BY 미생존(m=177). 양 continuation = 반도체와 반대 부호. |
| cs_mom_12_1 | momentum | PARTIAL | uncond y_60d IC +0.055 (wc_p=0.064), flow_neutral +0.106. OOS 강화(IS+0.048→OOS+0.170). BY 미생존. |
| flow_strong_buy interaction | conditional | PARTIAL | family_2 interaction: mom_6 b_inter=-0.157(t=-2.43), mom_12_1 -0.199(t=-3.20) 유의. = flow_strong_buy regime 에서 momentum 음 flip(passive 지배, Choe-Kho-Stulz). OOS: mom_12_1 t=-2.59 생존 / mom_6 t=-1.03 약화 → PARTIAL. |
| inv_ratio | inventory(★prior 반증) | TENTATIVE | uncond y_60d IC +0.112 (wc_p=0.0005, family 최강 raw_p). ★prior 음 → 측정 양 = 메커니즘 재해석(高재고/자산 = 성장·생산확대 종목 proxy). OOS 부호유지(IS+0.170→OOS+0.045 약화). 반도체 inv_ratio 와 동일 반증 패턴. |

## ⏳ 이연 (식별됐으나 미투입)

| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| 종목레벨 외국인 flow (순매수/시총 cs-rank) | theory M3 / Grinblatt-Keloharju 2000 | ★DATA-GATE(deferral 아님) — KRX 종목별 차단(인증). 시장레벨 flow regime 은 ECOS 로 측정완료. | KRX 인증 또는 종목별 ETF flow proxy |
| 리튬 price yoy (cost pass-through) | theory M4 / BNEF | regime/timing 변수(cross-sectional 부적합 = 산업 공통 시계열) + Trading Economics 유료 | FRED 리튬 PPI proxy 확보 시 regime conditioning 변수로 |
| GWh 출하 yoy | theory M4 / SNE Research | SNE Research 유료. 산업 timing(cross-sectional 아님) | 유료 data 확보 시 regime 변수 |
| EV-EBITDA (cyclical primary_metric) | summary.yaml v3 lens | DART 부채총계/현금성자산 추가 계정 필요(시점주식수 PIT 도) | DART fnlttSinglAcntAll BS 추가 fetch + 시점주식수 |
| KR HY credit spread | cross / theory | 현 = US BAML HY OAS proxy(n=35 small). KR 회사채 spread 유료(금투협/한신평) | KR credit data 확보 시 credit β 재측정 |
| 2축 merge regime cell (Macro×flow 등) | conditional 측정 | 36셀 full N≥24 = 0 (실측). 단일축만 powered. 2축 merge = 통합단계 power 부족 | breadth/표본 확대 또는 supervisor 통합 pooling |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| ppe_yoy (CAPEX) | OOS 부호반전(IS+0.128→OOS-0.149 artifact). prior 음과 in-sample 정합이나 OOS 붕괴 = INSUFFICIENT. |
| capex_ratio | uncond 비유의(IC-0.007) + OOS 부호반전. INSUFFICIENT. |
| inv_yoy | uncond 비유의(IC+0.008) + OOS 부호반전. INSUFFICIENT. |
| rnd_ratio | uncond y_20d IC+0.042 비유의 + OOS 부호반전(IS-0.023→OOS+0.172 불안정). prior 양과 약 정합이나 INSUFFICIENT. |
| customer momentum (리튬 upstream LIT/ALB) | REJECTED — forward 전 lag 비유의(p=0.441). 리튬=산업 공통 시계열 = cross-sectional alpha 부재. 동조성분은 RegimeGlasso Ω 흡수. |
| cs_pbr_z | INSUFFICIENT — IC≈0 무방향(y_60d +0.0002). 성장주 valuation 왜곡(theory M2) 정합. |
| cs_per_z | TENTATIVE→약 — 24M NW 비유의(p=0.17), conditional 도 비유의. trough-EPS trap. |
| sector-rotation business-cycle clock | 학술 myth(Molchanov 2024). 모멘텀 rotation 만 tentative. |
| asymptotic NW-HAC t (small cell) | size-invalid(Kiefer-Vogelsang fixed-b) → wild-cluster bootstrap p 로 대체(G-F §7). |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| cs_mom_6m 양 continuation | momentum crash(Daniel-Moskowitz) 위험 — 2차전지 2022-23 리튬붕괴 정점 crash 가능. 현 OOS(2023-26) 부호유지 = 부분 방어 | 2026년 이후 신규 OOS 에서 부호 유지 + flow_neutral cell 지속 |
| flow_strong_buy interaction | mom_6 OOS t=-1.03 약화 (mom_12_1 만 OOS 생존) — 두 momentum 중 하나만 OOS robust | 추가 flow_strong_buy episode 누적 후 t 안정성 재확인 |
| inv_ratio prior 반증(양) | 메커니즘 재해석(성장 proxy) = post-hoc 위험. 진짜 inventory cycle 신호인지 production-growth confound 인지 미분리 | size/growth 통제 후 inv_ratio 잔존 IC 측정(Fama-MacBeth) |
| 삼성SDI/LG엔솔 대형주 의존 | momentum cap-weighted vs eq-weight 부호 일관성 미점검(LOO 대형2사) | LG엔솔(2022상장)/삼성SDI 각각 제외 LOO IC |

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — BY 미생존, 단정 규칙 박제 금지) | 검증된 정량 규칙 |
| memory | inv_ratio prior 반증(음→양) = 다음 cycle 자문 prior 정정 입력 (반도체 inv_ratio 와 동일 반증 = 2차전지/반도체 공통 재고/자산 = 성장 proxy 패턴) | 자문 prior 정정 |
| observe-only | cs_mom_6m / flow_strong_buy interaction = OOS 부호유지 but BY 미생존 → N 누적 후 promotion | N 누적 후 결정 |
| evt | (G-B 자동자문 미발동 — family_2 interaction 살아있어 "약함" 단정 부적합 = supervisor 판단) | promotion-log ERROR 후보 |
| pointer | 다음 세션 SSOT: theory-notes §6 발굴표 + research-log 막힘로그 + 반도체 capsule 부호대조 | SSOT 정독 우선순위 |
