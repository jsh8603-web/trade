---
tags: [type/summary, domain/inv, study/eq_us_defensive]
date: 2026-05-30
study_id: eq_us_defensive
as_of: "2026-05-30"
---

# eq_us_defensive — 스터디 요약 (사람용)

## 1. 범위 (task spec)

- **방어 코어**: XLP(Staples) · XLU(Utilities) · XLV(Healthcare) · XLC mature(VZ/T/CMCSA)
- **금융**: XLF(Banks · Insurance · BD/AM · Payments)
- 사용자 task 가 둘을 **한 sleeve** 로 묶었음. 분류상 financials = NOT classical defensive 이지만 그대로 따름.
- → intra-sleeve dispersion 가장 큰 sleeve. **industry archetype 강제 분해 없이는 신호가 cancel**.

## 2. 핵심 발견 (3가지)

### 2.1 한 sleeve 안에 sub-sleeve 가 부호 반대

|충격|util/staples|banks/insurance|
|---|---|---|
|real rate ↑ (TIPS yield)|**압박** (multiple 디레이팅)|**호재** (NIM 확장, deposit franchise value↑)|
|2-10Y 스티프닝|rotation out (-)|구조적 NIM 확장 (+)|
|HY OAS 확대 (risk-off)|상대 outperform (+)|provisioning Q+1~2 lag (-)|
|Slowdown/Stagflation|★lead (모국)|★worst (NPL+NIM 양쪽 압박)|
|DXY ↑|multinational staples 압박|자산운용·IB cross-border 약화 (혼합)|

→ **rate_beta·credit_beta·yield_curve_slope_beta 의 부호가 archetype 별로 반대**.
→ `weight_card.delta_arch_by_type` 에 5개 archetype 등록 (staples/utility/healthcare/bank/insurance) → composed_weights(pi) 의 ticker shrinkage 로 부호 흡수.

### 2.2 cyclical 방과 거의 대칭

|축|cyclical|defensive (이 방)|
|---|---|---|
|알파 우위|valuation > momentum > revision|**quality + dividend safety + rate beta**. valuation 부차|
|핵심 macro|ISM PMI · HY OAS · dollar · oil (positive cyclical)|**real rate** · curve slope · HY OAS|
|regime 최적|Reflation/Recovery/Overheat|**Slowdown/Stagflation/Risk-off**|
|operating leverage|핵심 증폭계수|약함 (마진 안정). 금융은 financial leverage 로 대체|
|price momentum|early-cycle 효과|**약함** (mean-reversion 우위) → base 0.12→0.06 강등|
|dividend|부차|**핵심 thesis** (payout sustainability)|

→ main 이 두 방의 카드를 regime 별로 dispatch 하면 자연스러운 sleeve 로테이션 형성.

### 2.3 lens 주입·composed_weights 인프라 이미 존재

- `core/assume/judge.py` L126~228 — lens_prompt 주입 메커니즘 **기구현** (`_qwen_accepts_lens` + `_call_qwen_with_lens`). 카드 lens 필드 추가 + lens_prompt 조립만 신규.
- `core/assume/weight_card.py` L115~135 — `composed_weights(pi)` soft archetype 보간 **기구현**. archetype 등록만 신규.
- `core/brain/regime_to_weights.py` SLEEVES — `us_stock` 기존재. **신규 sleeve 등록 불필요** (sub-panel).
- → 본 방 산출은 **데이터 공급 + archetype 등록 + lens 필드 조립** 으로 무회귀 구현 가능.

## 3. 결정 사유 (왜 이 가중·구조 채택)

### 3.1 rate_beta base 0.18 (sleeve 최우위) — 채택

- 학술/리포트 일관: real rate 가 본 sleeve 의 **1순위 macro driver**. dollar/oil 보다 우위.
- 합성 데이터 대조 (raw/lens-hypothesis-quickcheck.txt): market beta 흡수 후 partial corr util -0.334 / staples -0.304 / banks +0.020 / insurance +0.086 → 부호 분기 prior 정합.
- 신규성 없음 (cyclical 방도 rate_beta 보유) — 단 base_weight 가 더 큼 (0.12 vs 0.18) 이고 ticker shrinkage 의존도 더 큼.

### 3.2 price_mom_12_1 base 0.06 (cyclical 0.12 의 절반) — 강등

- 방어주는 mean-reversion 우위 (학술 정설). 트렌드 추종 < 가치 회귀.
- 금융은 NIM thesis 활성 시 모멘텀 강하지만, sleeve 평균으로는 약화.
- Reflation/Recovery 일부 구간만 약하게 적용. base 강등으로 noise 차단.

### 3.3 dividend_safety + earnings_stability — 신규 (방어 thesis 핵심)

- "방어주" 의 정의 자체 = 안정 배당 + 안정 EPS. is_core:false 이지만 sleeve 내 sub-thesis.
- payout coverage (FCF/배당) + 부채비율 + 5Y EPS CV 자체계산. EDGAR 파싱 확장 필요 (블록6 #1·#3).

### 3.4 yield_curve_slope_beta — 금융 한정 신규 (NIM thesis 신호)

- 은행 NIM 의 가장 강한 macro 신호. 슬립 양전환 → 3~6M lag 로 NIM 확장.
- industry=banks 마스크 적용. 보험 약·utilities 음 (이미 rate_beta 포함이라 dual-counting 회피).

### 3.5 industry archetype 5종 등록 — 핵심 구조 결정

- staples_archetype · utility_archetype · healthcare_archetype · bank_archetype · insurance_archetype.
- `weight_card.delta_arch_by_type` 에 등록. `composed_weights(pi)` 보간으로 ticker 단위 가중 흡수.
- → 종목별 가중을 개별 학습하지 않고 archetype prior 에서 shrink (부록B 권장 hierarchical pooling).

## 4. 기각 사유 (왜 채택 안 한 옵션)

### 4.1 신규 sleeve 등록 (us_defensive sleeve)

- regime_to_weights.py SLEEVES 에 추가 옵션 검토했으나 **회귀 위험**. us_stock 기존재 → sub-panel 로 충분.
- 신규 sleeve = SLEEVE_BLOC · _belief_conditional_cov · 가중 정규화 전반 동반수정 필요 → SACRED 저촉 가능.
- → cyclical 방과 동일 stance. main 통합 시 일관.

### 4.2 id 네임스페이스 분리 (`weight.equity.us_defensive.{regime}`)

- 가능하지만 `_resolve_weight_card` 동반수정 필수 → 회귀 위험.
- 권장 = 단일 `weight.equity.{regime}` 카드에 archetype 분기 (delta_arch_by_type) 등록.
- cyclical 방과 동일. main 합의 사항 (조립 시 확정).

### 4.3 individual ticker 단위 카드 학습

- 부록B 명시: "ticker 마다 독립 학습" 금지 (obs 부족 — regime 당 45). soft membership shrinkage 로만 가능.
- granularity=ticker = "산업 prior 에서 종목 shrink" 의미. 단일 ticker 카드 등록 X.

### 4.4 drug_pricing_overhang base_weight 0.02 (낮음 유지)

- 정책 이벤트 dummy = 구조적 데이터 결여 + 이벤트 산발적. 가중 키우면 노이즈.
- pharma 한정 보조신호. event-driven 가중↑은 hook (confidence_hooks #6) 가 조건부로만.

### 4.5 healthcare 별도 sub-sleeve 분리

- healthcare 내 pharma / medical device / HMO 가 macro 부호 다름. 본 방에서는 healthcare_archetype 단일 등록.
- 추후 confidence_hooks 가 archetype 부호 분기 신호 detect 시 sub-archetype 추가 검토 (main 단계).

## 5. 실데이터 대조 한계 (정직 명시)

- 본 방 **실 EDGAR/FRED 데이터 대조 미수행** — 사용자 hint ("Calculating 타이머 멈춤, 전체 적합 대신 상관·partial-corr 먼저") 에 따라 가벼운 synthetic 시뮬 (raw/lens-hypothesis-quickcheck.txt) 만 실행.
- partial-corr 부호 검증은 prior 와 일치 (방어 NEG / 금융 POS) — 그러나 effect size 는 실데이터에서 측정 필요.
- **블록5 confidence_hooks 6건이 라이브 운영 시 실IC·partial-corr 자동 측정·갱신** — lens.estimation_note 의 "Recovery 초입 · real rate 안정" anchor 가 1순위 검증 대상.

## 6. 막힌 점 / 보류 (main 에 보고)

- **EDGAR 은행 특화 파싱 (NIM·NPL·capital_ratio)** 자체구현 필요. SECEdgar 라이브러리 사용 + 10-K 텍스트 파싱 (block6 #5~#8).
- **TIPS yield (DFII10)** 적재 — fred_adapter 16 시리즈 미포함이면 추가 필요 (block6 #12).
- **GICS sub-industry 분류** — XLP/XLU/XLV/XLF/XLC mature 구성종목 mapping (main 선구축 ETF holdings 사용 가능 — block6 #11).
- **drug_pricing 정책 이벤트 캘린더** 수동 등록 필요 (block6 #10) — 구조적 데이터 부재.

## 7. 다음 단계 (main 측 진행 권고)

1. cyclical 방과 본 방 두 산출 정합성 확인 (id 네임스페이스 · archetype 등록 · sleeve 미변경 stance).
2. EDGAR 은행 파싱 인프라 추가 (block6 우선순위 #5~#8) — 본 방 sub-sleeve 신호 활성화 prerequisite.
3. TIPS yield (DFII10) 추가 — real rate 1순위 driver 활용 prerequisite.
4. 단일 `weight.equity.{regime}` 카드에 archetype 5종 등록 (cyclical 의 early/mid/late cycle 3종 + 본 방의 staples/utility/healthcare/bank/insurance 5종 = 총 8 archetype).
5. confidence_hooks 6건 (본 방) + cyclical 방 hook 통합 → weight_falsification.py 서브패밀리 등록.

## 8. 참조

- `study_session.yaml` — 7블록 계약 (인덱스에 사용)
- `raw/lens-research-notes.md` — 일반론·리포트 정제 노트
- `raw/lens-hypothesis-quickcheck.txt` — synthetic partial-corr 부호 검증
- 형제: `study-research/eq_us_cyclical/study_session.yaml` (대조)
- 코드: `core/assume/{weight_card,judge,registry,weight_falsification,update_controller}.py`, `core/structure/conditional_correlation.py`, `core/brain/regime_to_weights.py`, `core/data/weight_panel.py`, `core/stock_track.py`, `scripts/train_weights.py`
