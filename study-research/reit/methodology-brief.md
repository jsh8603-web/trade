---
tags: [type/methodology-brief, study_id/reit, phase/v2-mirror-phase2]
date: 2026-05-30
study_id: reit
asset_scope: [reit]
mirrors: eq_kr/methodology-brief.md (v2 7-Phase 절차 baseline)
note: Phase 3 자문 input. eq_kr 검증 완료 v2 절차 미러링 — study_id/universe만 교체 + REIT 특화 sub-cluster + 거시 driver.
status: phase3_consult_input_ready
---

# REIT v2-mirror — methodology-brief (Phase 2)

> eq_kr v2 7-Phase 절차 (사용자 검증 완료) baseline. **study_id=reit, universe=REIT 9 sub-sector ETF + sub-cluster 분할**.
> 기존 reit v2 산출 (M3 실측 + validation H1~H5 + theory-notes + study_session.yaml v2) = **input 보존·재사용**.
> 본 brief = Phase 3 자문 R1~ 입력 (4-section: §A 분할 §B 거시 driver §C 기존 실측 §D 자문 Q1-Q12 §E 출력 의무).

## §0 SSOT 우선순위 (eq_kr methodology-final §0 mirror)
1. `D:/projects/Inv/CLAUDE.md` §"멀티에셋 스터디 워크플로"
2. `D:/projects/Inv/STUDY-ORCHESTRATION.md` — 5-Phase
3. `D:/projects/Inv/STUDY-KIT.md` — 작업방 작업 계약
4. `D:/projects/Inv/study-research/AUDIT-GUIDE.md` — ★12축 평가 SSOT
5. `D:/projects/Inv/study-research/eq_kr/methodology-final-for-main-dispatch.md` — v2 절차 baseline
6. 작업방 내부 SSOT (본 brief + direction.md + 신규 evaluation-axes.md)

## §A REIT sub-cluster 분할 후보 (자문 Q1)

기존 9 sub-sector ETF 매핑 → 거시 sensitivity 패턴별 cluster:

| Cluster | sub-sector | ticker | 핵심 거시 sensitivity | 본 brief 가설 |
|---|---|---|---|---|
| **C1. Residential (주거)** | Apartment, Healthcare (skilled nursing 일부) | AVB, WELL | 인구·이민·임금 / 단기 lease | M3 β_rate ~ −2~−4 중간 |
| **C2. Commercial-Retail (상업·리테일)** | Retail (mall + strip), Office | SPG, BXP | 소비·실업률 / WFH 트렌드 / long-lease | M3 retail β_rate −0.89 (낮은 유의성) / office −2.57 |
| **C3. Industrial-Logistics (산업·물류)** | Industrial | PLD | e-commerce 침투율 / 무역 / 수출 | M3 β_rate −4.51, t=−4.57 강함 |
| **C4. Datacenter-Infra (데이터센터·인프라)** | Datacenter, Tower | EQIX, AMT | AI capex 사이클 / 통신 5G / 전력·냉각 grid | M3 Tower β_rate −6.86 가장 음수, E4 −12.01 paradox |
| **C5. Healthcare-Long-WALT (헬스케어)** | Healthcare (MOB/senior housing/skilled nursing) | WELL | 인구 노령화 / Medicare / drug pipeline | M3 β_rate −2.08, +59.9% 전체 cum 최선 |
| **C6. Specialty (lodging/storage)** | Hotel, Storage | HST, PSA | 인플레 hedge / 이사 사이클 / 단기 demand | M3 Hotel β_rate +1.79 단독 양수 paradox |

**자문 Q1**: 이 6 cluster 분할이 적절한가? 누락 critical sub-sector (예: gaming/farm/cell phone tower 분리, single-family rental(SFR), timberland) 있는가? Healthcare 가 Residential 에 포함(C1)되는지 단독(C5)인지 학술 합의?

## §B 거시 driver 동적가중 후보 (자문 Q2)

eq_kr 의 (외국인 플로우 / 중국 credit impulse / USD/KRW / 수출) 미러링 → REIT 자산군 특화:

| Driver | 가설 | 측정 변수 | 기존 M3 박제 |
|---|---|---|---|
| **D1. Real rate (10y TIPS yield)** | NAV 할인율 직접 채널 — REIT 채권성 듀레이션 | DFII10 (FRED) | VNQ β_rate(nominal) = −3.82 bp, t=−5.65. real rate 분해 미실측. |
| **D2. Cap-rate spread** | Implied REIT cap rate (public NOI/EV) − private appraisal cap rate. mean-reverting. | Nareit T-Tracker | Q3 2022 peak 243bp / Q4 2023 = 123bp. spread proxy = VNQ relative valuation (2-2 confirmed via WebSearch). |
| **D3. Dollar (DXY)** | risk-on/off + foreign capital flow into US REITs | DXY 또는 DTWEXBGS | VNQ β_dollar = −0.841, t=−8.33. M1 us_stock −0.879 와 동일 강도. |
| **D4. Sector supply (CRE 건설 pipeline + 공실률)** | sector specific over/under-supply. Industrial: warehouse pipeline. Office: vacancy. | CBRE/CoStar — 4분기 lag | 미측정 (Phase 5 collector_plan). |
| **D5. (sub) Credit spread (HY OAS)** | risk premium risk-off | BAMLH0A0HYM2 (FRED) | 미측정. eq_kr 학설 reference 동일. |
| **D6. (sub) Inflation breakeven** | nominal rate − real rate = inflation expectation. lease escalator 가치. | T10YIE | 미측정. |

**자문 Q2**: D1~D6 6 driver 중 핵심 4 (사용자 지시 = real rate / cap-rate / dollar / sector supply) 가 적절한가? supply 측정의 best practice? credit spread / inflation breakeven 추가 의무성?

**자문 Q3**: D1 real rate 분해 — VNQ β_rate (nominal) = −3.82 bp 가 [real rate + inflation breakeven] 으로 어떻게 decompose 되는가? 학설 reference 와 실측 방법 (TIPS yield = FRED DFII10 2003-01 부터 daily continuous, M3 sample 2022-2024 fully available; 장기 TIPS 부재는 1997-2003 한정으로 본 sample 무관 ← R1 claude fact 정정 반영 2026-05-30)?

## §C 기존 reit v2 산출 박제 (재사용 input, ⛔폐기 X)

### C-1. M3 macro linkage 실측 (raw/m3-macro-linkage.md, 2026-05-30)
- 기간: 2022-01 ~ 2024-12, n=753 daily (yfinance auto_adjust + FRED DGS10)
- **VNQ β_rate = −3.82 bp, t=−5.65** ★M1 주식 ≈0 패턴 불일치 (REIT 채권성 듀레이션 실증)
- VNQ β_dollar = −0.841, t=−8.33 (M1 us_stock 동일 강도)
- M1 'rate-UP dollar 2배' 패턴 REIT 약화: |E1|/|E4| 1.11~1.52배 (M1 1.68배)
- within-sleeve mean ρ = 0.547 (M1 us_stock~tech 0.96 대비 낮음, sector effect)
- **Paradox**: Hotel β_rate=+1.79 단독 양수 (short-lease hedge), Tower E4 β_rate=−12.01 가장 음수 (pivot 임에도 cum +17%만)
- E1 (긴축충격) 9 sub-sector 일관 음수, E4 (pivot) 광범위 폭주 (Retail +70.04%, Healthcare +58.60%)

### C-2. validation 5건 (raw/validation-{H1..H5}.md, 2026-05-30)
- **H1 REJECT sign mismatch** — long-WALT cross-section Rank-IC = +0.240, z=+3.18 (long-WALT *outperform*, 학설 반대)
- **H2 PARTIAL** — mean-reversion VNQ proxy ρ=−0.361 CONFIRMED, but 2008 GFC 2 episode −35/−43% reject 사례 존재
- **H3 REJECT sign mismatch** — long-WAM Rank-IC = −0.117, z=−2.09 (long-WAM underperform, H1 과 부호 반대)
- **H4 CONFIRMED** — window flip Kendall τ=0.077 (non-monotonic ranking), swap rate 88%, n=77
- **H5 CONFIRMED falsification** — mean inter-regime ρ=+0.087 (random), Reflation Industrial avg rank 4.83 mid

### C-3. theory-notes (raw/theory-notes.md)
- pricing principle = DCF (P ≈ AFFO / (r_f + ERP_REIT + ΔCapRate − g_NOI))
- 4 approach (NAV / P/FFO / P/AFFO / DCF)
- 환각 검증: 2024 industrial -17.7% / 243bp Q3'22 = CONFIRMED. Q4'24 120bp = primary 미확인, baseline 제외.
- Q2 2023 sub-sector spread: Office 259 / Apt 194 / Retail 150 / Industrial 93 bp
- AFFO/FFO sector standard: triple-net 95-100% / industrial-multifamily 85-95% / office-retail-lodging 70-85%

### C-4. study_session.yaml v2 (861 lines, Tier = "structural prior (저신뢰)")
- 8 block (lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan / 12축 self-audit)
- raw/evidence-map.md = 모든 yaml 수치 → validation/script 추적표 (C축 hard pass)
- H1/H3 sign mismatch REJECT 기록 (F축)

## §D Phase 3 자문 Question 그룹 (R1~R7 분배)

### R1 (이론 수집방향 — sub-cluster 분할 + driver 동적가중)
- **Q1** §A 6 cluster 분할 정합? 누락 sub-sector? Healthcare 단독 cluster 의 학술/실무 합의?
- **Q2** §B 4 핵심 driver (real rate / cap-rate / dollar / sector supply) 충분? 추가 의무 driver (credit/inflation breakeven)?
- **Q3** real rate 분해 학설 + missing TIPS window 핸들링 best practice?

### R2 (이론 검증방향 — M3 결과 비판 + within ρ=0.55 sector effect)
- **Q4** REIT VNQ β_rate(nominal) −3.82 bp 의 학술/실무 cross-verify? M1 주식 ≈0 과 REIT 채권성 차이 정량화 references?
- **Q5** Hotel β_rate +1.79 양수 paradox — lodging short-lease 가 rate hedge 라는 가설의 학술 reference? counter-example?
- **Q6** within-sleeve mean ρ=0.547 의 sector decomposition — equity broad factor (Fama-French + Q-factor REIT 적용) vs sub-sector unique factor 분리 best practice?
- **Q7** Tower E4 β_rate=−12.01 paradox (rate-down 인데 가장 음수 강도) — long-duration NAV vs lease escalator pass-through 약함 가설 학술 reference?

### R3 (가설 + 반증조건 — H1/H3 REJECT 결과 위 신규 가설 N개)
- **Q8** H1 (long-WALT positive) REJECT + H3 (long-WAM negative) REJECT 모순 — 학술 어떻게 해석? (WALT vs Debt WAM 변별)
- **Q9** sub-cluster x rate regime cell-conditional weight 5게이트 (n / OOS / robustness / regime stability / economic significance) — REIT 자산군 한정 5게이트 임계 (eq_kr default 임계 그대로 사용 가능?)
- **Q10** 신규 가설 후보 (H6~H10) — 예: H6 "cap-rate spread > 200bp 진입 시 +12m mean-revert 75% confidence" (H2 reverse-shape), H7 "datacenter capex 사이클 lead REIT EQIX 6-9m" (AI capex proxy), H8 "Tower long-duration discount = lease escalator pass-through 약함", H9 "Healthcare β_rate 약함 = Medicare 정책 dominant", H10 "REIT broad ETF flow vs sub-sector divergence regime 진입 신호"

### R4~R7 (수렴 / 잔존 의문 처리)
- M3 dollar 채널 (β_dollar=−0.84) catch verification + cross-asset vs within-sleeve L축 1회계상 PSD 학설 cross-check
- supply pipeline 측정 (CRE construction starts, occupancy, completions) data source best practice
- 실거래 wiring 시 down-only 감쇠 적용 layer 5게이트 통과 후 confidence_hook 권고

## §E 자문 출력 의무 (eq_kr methodology-final §3 mirror)

⛔ **5 금지** (모든 자산군 공통, 본 자문 결과에 동일 적용):
1. **점추정 prior 박제 금지** — Rank-IC 점추정 → base_weight 직접 X. 분포 + CI + 게이트.
2. **합성·시뮬 데이터 금지** — random walk / 합성 panel / random IC. 실제 PIT 수집기만.
3. **자문 그대로 코드화 금지** — gemini/claude 답 → yaml 직접 X. supervisor 비판 + 환각 cross-verify 후 채택.
4. **Single-source 단정 금지** — 1 출처 "확정" X. 학술 + 실무 + 1차 데이터 3중.
5. **Small-N 단정 금지** — cell N<24 "유의" 주장 X. 5게이트 §N gate 우선.

추가 박제:
- ★ **supervisor 직접 평가 금지** — Phase 6 별 평가 subagent (opus 1m) 위임. main pass-bias 회피.
- ★ **analyst-level lens 다운그레이드 금지** — 시스템 못 받으면 파이프라인 업그레이드.
- ★ **opt-in off = byte-identical 무회귀**.
- ★ **reflexive loop 차단** (belief→_macro X, L축 1회계상 + PSD).
- ★ **tier 정직성** — REJECT/contemporaneous = structural prior(저신뢰) 라벨.

## §F 자문 진행 계획

| Round | Focus | 도구 | 산출 |
|:-:|---|---|---|
| R1 | Q1-Q3 (sub-cluster + driver + real rate) | /gemini-web + /claude-web 병렬 | raw/consult-round-1.md |
| R2 | Q4-Q7 (M3 비판 + within ρ + paradox) | 동일 | raw/consult-round-2.md |
| R3 | Q8-Q10 (가설 + 5게이트 + 신규 H6~H10) | 동일 | raw/consult-round-3.md |
| R4~R7 | 수렴 / 잔존 의문 / supply 측정 | 동일 (필요 시) | raw/consult-round-{4..7}.md |

**수렴 판정**: 두 모델 의미 일치 + 새 의문 비생성 + 사용자 충분 (정의: 3R 만에 critical gap 해소 가능 시 R4+ 생략).

**경합 fallback**: /gemini-web + /claude-web 9세션 경합 시 → WebSearch (`.allow-native-web` flag) + WebFetch (academic PDF / Nareit blog primary) 폴백 — 직접 1차 출처 우선.

## §G 산출 파일 reference

- direction.md (기존 v2 의 2-1 산출, Phase 3.5 갱신 대상)
- methodology-brief.md (본 파일)
- raw/consult-round-{1..N}.md (Phase 3 신규 자문 누적)
- evaluation-axes.md (Phase 1 산출, Phase 6 평가 SSOT, 후속)
- plan.md (Phase 4 산출, Phase 5-7 작업 계약, 후속)
- 기존 input (재사용): raw/m3-macro-linkage.md / raw/validation-{H1..H5}.md / raw/theory-notes.md / raw/round-{1,2,3}.md / study_session.yaml (v2) / raw/evidence-map.md
