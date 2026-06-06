---
tags: [type/theory-notes, domain/equity, sector/telecom, scope/equity-kr]
date: 2026-06-05
purpose: S1 학술 ground — 통신 cycle·배당주 duration 이론 정독 → 메커니즘·부호 사전확약(HARKing 방지). 결론·목표가는 증거 아님, 메커니즘·가설만 추출.
sources: frame v3 §3 통신 + refining/semiconductor theory-notes 미러(과점·시계열 패턴) + 학술 ref(Fama-French 1992, Cornell 2000 dividend duration, Cooper-Gulen-Schill 2008) + dispatch 통신 cycle 변수 인계
---

# telecom(통신) 산업 이론·메커니즘 정리

> ★**HARKing 방지**: 부호 사전확약은 통신 cycle·배당주 duration 이론으로 **독립 수립** 후 측정과 대조. 측정 前 동결점 = 본 §1. conditional/시계열 IC 측정은 동결 후 실행.
> ★★**CRITICAL 분석 unit 분리 (frame §1.6, 측정 前 박제)**: 통신 = **2개 이질 archetype** 혼재. ⛔한 풀로 cross-sectional pool 금지(★분리 근거 = 측정축 차이[service 시계열 vs equipment cross-sectional] + archetype driver 본질차[bond-proxy vs cyclical]. PBR 부호 cancel 아님 — G-C 보강2).
> - **통신서비스(service)**: SKT(017670)/KT(030200)/LGU+(032640) = ★3사 과점, strict floor(시총3000억∧ADV30억) pass = **3종**. → cross-sectional Spearman IC(min 8종) ⛔불가 = **INSUFFICIENT**. **frame M2 산업 시계열**로 측정. = defensive 고배당 bond-proxy archetype.
> - **통신장비(equipment)**: 한화비전/RFHIC/케이엠더블유 등 strict pass = **10종(≥8)** = cross-sectional 가능. = cyclical(5G capex cycle) archetype. ★service 와 별도 측정.
> ★6/3 옛 산출(summary.yaml v3 archetype=asset_stable) = service3+equipment11 을 한 풀(n=13) cross-sectional(IC -0.542) → ★24M overlap horizon artifact(eff_N≈2.5 degenerate)지 PBR 부호 cancel 아님(pool/장비/service PBR 60d 셋 다 음 value -0.16~-0.20). 분리 근거 = 측정축·driver 본질차. 본 재작업이 정정(G-C 보강2).

## §0. 핵심 산업 특성 (2 archetype)

### 통신서비스 = defensive 고배당 bond-proxy (반도체·정유와 cycle 원천 다름)
- 통신서비스(SKT/KT/LGU+) = 규제 과점 + 안정 현금흐름 + 고배당(배당수익률 4~7%). 경기방어주.
- ★cycle 원천 = **금리(배당주 duration)**: 통신=bond-proxy → 금리 상승 시 할인율↑ = 디레이팅(주가 약), 금리 하락 시 리레이팅. = defensive utility 와 동형 메커니즘(금융주 NIM 과 ★반대 — 금융은 금리↑ 수혜).
- ARPU/5G 가입자/capex = 펀더멘털 driver but ★3사 과점 = cross-sectional 분산 없음 → 종목선택 신호 아닌 산업 timing.
- ★archetype = asset_stable/defensive (배당·금리민감). primary valuation = 배당수익률·PER. trap = 금리쇼크·규제(요금인하).

### 통신장비 = cyclical (5G capex cycle, 소형 KOSDAQ)
- 통신장비(RF부품·중계기·안테나·광트랜시버) = 통신사 capex 사이클에 종속 = cyclical. 대부분 KOSDAQ 소형주.
- ★cycle 원천 = 5G/6G capex 투자 사이클 + 글로벌 통신장비 수요. valuation(저PBR value) + momentum 후보.

## §1. 메커니즘별 부호 사전확약 (★측정 前 이론 동결)

### M1. 통신서비스 금리 duration → forward 음(-) prior [service 시계열]
- **메커니즘**: 통신서비스 = defensive 고배당 = 장기 채권 유사(bond-proxy). DDM 상 P = D/(r−g) → 할인율 r(금리)↑ → 가치↓. 금리 상승기 = 성장주·배당주 디레이팅. = duration 음.
- **부호 사전확약**: KR 10Y 국채 yield(level/Δ)↑ → 통신서비스 패널 forward **음(-)** (duration). ★단 동시(contemp)는 금리쇼크 즉각 반영 = 음 가능, forward 예측력은 효율시장이면 약 가능(frame §D falsifier).
- **출처**: Cornell (2000) "Equity duration, growth options, and asset pricing" / DDM duration(Macaulay 채권 듀레이션 주식 확장). 한국 통신주 = 대표 고배당 defensive(증권사 실무 = 금리 peak 시 통신·유틸 비중확대).
- **반증조건(falsifier)**: KR10Y forward IC ≥ 0 + Δ도 양 → duration 가설 기각 / contemp 만 음 + forward 0 → "금리쇼크 동조(risk-monitor)" 격하. ★level I(1) → Δ(차분)도 음 유의해야 진짜(§1.7 ADF spurious 점검).
- ★**data 한계**: 배당수익률 직접 미수집(DART = equity/net_income/assets 만, 배당 line 부재) → ★KR10Y level/Δ 민감도로 duration **직접** 측정(배당수익률 대리 불요).

### M2. 통신서비스 ARPU / 5G 가입자 / capex → forward 양(+) prior [측정불가 data-gate]
- **메커니즘**: ARPU(가입자당 매출)↑ = 5G 전환·요금 상향 = 매출·마진 개선. 5G 가입자 점유율↑ = 시장지위. capex peak-out(5G 투자 회수기 진입) = FCF·배당 여력↑.
- **부호 사전확약**: ARPU yoy↑ / 5G 가입자↑ / capex peak-out → 통신 forward **양(+)**.
- **출처**: 통신 산업분석 실무(ARPU = 통신사 핵심 KPI) + capex cycle(투자→회수 전환 = 배당 매력).
- ★★**측정 결론 (data-gate)**: ARPU·5G 가입자 = MSIT/통계청 월별 공시, ★무료 clean time-series API ⛔부재 → **collector_plan data-gate**. + 3사 과점 = cross-sectional 분산 없음. → ARPU/5G = ★미측정(이연 아님 = 데이터 부재). 측정 가능한 금리 duration(M1) 우선.

### M3. 통신장비 valuation(저PBR value) → cross-sectional 음(-) prior [equipment]
- **메커니즘**: 저PBR 종목 = value premium(Fama-French 1992). 통신장비 = 자산기반(설비·재고) cyclical → PBR 밴드 valuation.
- **부호 사전확약**: 통신장비 cross-sectional PBR z 상위(고PBR) → forward **음(-)** (저PBR value premium = IC 음).
- **출처**: Fama-French (1992) JF (value premium). cyclical valuation = PBR(peak-EPS trap → PER 보다 PBR).
- **반증조건**: PBR IC ≥ 0 → value 기각. ★size confound 점검 의무(저PBR↔소형 상관 → size-neutral IC 잔존 확인, G-A A-4).

### M4. 통신장비 momentum → cross-sectional 양(+) prior [equipment]
- **메커니즘**: 12-1 momentum(Jegadeesh-Titman 1993). 소형 cyclical = momentum 후보.
- **부호 사전확약**: 통신장비 mom_12_1 z 상위 → forward **양(+)** (IC 양).
- **출처**: Jegadeesh & Titman (1993) JF.
- **반증조건**: mom IC ≤ 0 또는 비유의 → 무신호.

### M5. 통신장비 PER(흑자 한정) → cross-sectional 음(-) prior [equipment, 협소]
- **메커니즘**: 저PER value. 단 통신장비 = 적자 빈발(KOSDAQ 소형) → 흑자 종목만 = avgN 협소.
- **부호 사전확약**: 저PER → forward 양 = IC 음(-). ★단 흑자 한정 avgN 작음 → underpowered 위험.
- **출처**: Basu (1977) PER effect.
- **반증조건**: PER IC ≥ 0 또는 avgN<8 underpowered → 무효/INSUFFICIENT.

## §2. 측정 설계 (2 archetype 분리)

| # | 측정 | 방법 | unit | 가능성 |
|---|---|---|---|---|
| 1 | KR금리 duration → service forward | 산업 패널(3사 동일가중) 시계열 + regime conditional | service 시계열 | ✅ (frame M2) |
| 2 | service 동시 vs 예측 부호 대조 | contemp vs forward (frame §D falsifier) | service 시계열 | ✅ |
| 3 | ARPU/5G/capex → service forward | 시계열 | service | ❌ data-gate (ARPU/5G 무료부재) |
| 4 | PBR/momentum/PER cross-sectional | 횡단면 IC (10종) + size-neutral | equipment 횡단면 | ✅ |
| 5 | walk-forward OOS + leave-episode + ADF | IS19-22/OOS23-26 + 2020저금리/2022인상 제외 + 단위근 | 양쪽 robustness | ✅ |

## §3. 부호 사전확약 요약표 (측정 前 동결 = HARKing 방지)

| 신호 | 측정 unit | prior 부호 | 근거 |
|---|---|---|---|
| KR10Y 금리 (level/Δ) | service 시계열 forward | **음(-)** duration | Cornell 2000, DDM duration (bond-proxy) |
| ARPU / 5G / capex | service 시계열 forward | 양(+) — but 측정불가 | 통신 KPI 실무 |
| PBR cross-sectional | equipment 횡단면 | 음(-) value — ★size confound 점검 | Fama-French 1992 |
| momentum 12-1 | equipment 횡단면 | 양(+) | Jegadeesh-Titman 1993 |
| PER cross-sectional | equipment 횡단면 | 음(-) — but 흑자 협소 | Basu 1977 |

★FDR family = 위 5 가설(service 금리 duration + ARPU/5G data-gate + equipment value/mom/per). 측정 결과 본 후 family 재정의 ⛔금지.
