---
tags: [type/consult-response, study/eq_us_cyclical, round/3, source/gemini-pro-web]
date: 2026-05-30
model: GeminiPro
response_len: 5544
---
# Round 3 — Gemini Pro 응답 (수렴 종결 의도)

## BLUF
- Q1: 계층 베이지안 부분 풀링 — 2국면 검정 + 4국면 배분 하이브리드 = 단일 최선.
- Q2: 정상화 ROE 70:30 blending(James-Stein), ERP=Damodaran Implied(historical 5% 금지), g=명목 GDP cap, fair_mult는 Band 산출.
- Q3: AMTMNO/BUSINV/CFNAI SOI verified, PCA 첫 주성분 우위. ALFRED vintage 절대.
- Q4: DK는 평균만 처리. **DCC-GARCH 결합으로 위기 윈도 down-weight**. Choueifaty-Coignard 2008.
- Q5: H1·H3·H4·H6 4개 우선순위 코어.

## Q1. 4국면 vs 2국면 — 계층 베이지안 부분 풀링
(a) 4→2국면 강등 = **인플레이션/성장률 2차 미분(모멘텀 변화) 정보 소실** (Reflation vs Recovery 금리 민감도 극명히 다름). 이론 = 4국면, 검정 = 2국면 풀링으로 base power 확보, 전략 배분 = 4국면 하이브리드 필수.

(b) **하이브리드 (사용자 제안 정확)**: 통계 유의성 = 2국면(group level), 4국면(sub-group) weight = 2국면 결과를 prior로 update.

(c) WeightAssumptionCard 강등 로직:
- **대안 1 (권장)**: 베이지안 부분 풀링. 4국면 OOS 관측 부족/분산 큼 → 2국면 평균으로 자동 shrink:
  ```
  β̂_4-regime = λ·β_2-regime + (1-λ)·β_4-regime    (λ ∝ 노이즈)
  ```
- 대안 2: hard fallback. 유효-n<10 OR p>0.1 → 2국면 100% 덮어쓰기.

## Q2. fair_mult 입력 산출 — Capping & Blending
(a) **정상화 ROE**: 7-10년 + 침체 1회 평균, **종목 자체 70% + 섹터 평균 30% blending (James-Stein 논리)**. 음 ROE = 섹터 하위 10% 또는 r_e로 cap (산식 붕괴 방지).

(b) **자본비용 r_e**:
- β: **60M rolling** (full-sample 과적합 회피)
- ERP: ★ **Damodaran Implied ERP (월별)**. Historical 5% 금지 — 주가 폭락 시 ERP 낮게 계산되는 치명적 오류.

(c) **지속가능 g**: `g = ROE·(1-b)` = 시클리컬 배당 변화 민감. PIT-safe = **장기 명목 GDP 4-5% cap 동기화**.

(d) **민감도**: 분모 `(r-g)` 0 근접 시 multiple 발산. **Monte Carlo (또는 ±10% 민감도) → fair_mult는 단일값 아닌 Band**.

## Q3. ISM 프록시 — verified
(a) **AMTMNO + BUSINV (Verified)**: FRED 실재. **ALFRED API release-date 맵핑 절대** (M3 advanced/revised 빈티지 차이 큼).

(b) **CFNAI SOI (Verified)**: 4 subindex 중 SOI(Sales/Orders/Inventories)가 ISM 신규주문 선행성과 가장 직결.

(c) **Empire State (Partially)**: 헤드라인 `GACDISA066MSFRBNY` verified, 하위지수는 FRED 일관 ticker 어려움 → **NY Fed 공식 마이크로데이터 CSV 직접 적재 권장**.

(d) **앙상블**:
- 대안 1 (권장): **PCA 첫 주성분** — 3개 지표 공통 매크로 모멘텀 추출, 개별 노이즈 소거.
- 대안 2: Z-Score 단순 평균 — 빠르나 상관관계 미고려 편향.

## Q4. 시변 ρ̄ 보정
(a) **DK 한계**: 횡단의존성 평균 구조 보정만. 위기 ρ̄→1 시변 극단성 자동 처리 X.

(b) **학계 표준 = DK + DCC-GARCH 결합**. DCC-GARCH로 위기 윈도 정보 가중치 명시 down-weighting.

(c) Grinold √breadth 보정식 출처: **Choueifaty & Coignard (2008) "Toward Maximum Diversification"** — effective breadth 표준 식. `N_eff = N/(1+ρ̄(N-1))` = 포트폴리오 분산 분해 고전식.

## Q5. H1-H10 우선순위 — 4개 코어
| H | 이름 | 적합 통계 | 필요 데이터 | 반증 임계 |
|---|---|---|---|---|
| **H1** | 정상화 E/P trough 최강 | Panel FE Regression + Decile Spread 백테스트 | EDGAR 7-10년 ROE + 월말 종가 | Trough에서 최상위 E/P(정상화) Excess Return이 0과 유의 X(p>0.05) |
| **H3** | ISM 선행 대체 Proxy 유효성 | Granger Causality + 교차상관함수(CCF) | FRED AMTMNO + CFNAI SOI + 과거 ISM 벤치 | 1-3M lag가 국면전환 hit ratio >60% 못 달성 |
| **H4** | EBP 공통원인 — 디폴트 사이클 | 직교화 회귀(EBP 잔차) + VAR | BAMLH0A0HYM2 + VIX | VIX 직교 후 EBP 잔차가 시클리컬 하위 20% 부도/어닝쇼크와 ρ>0.2 못 달성 |
| **H6** | Peak Trap 스팟-싼 거짓신호 | 이항 로지스틱 회귀 | H1 데이터 + regime 라벨 | 'Peak + Spot 저PER' 그룹의 차분기 하락 확률이 평균보다 유의하게 높지 않음 |

## § 추가 경고 (★수렴 종결을 위한 Final Traps)

### Trap 1: CFNAI vintage 깊은 개정
CFNAI는 개정폭 매우 깊고 잦음. **2020년 발표 2019년 말 지표가 2021년에 크게 바뀜**. 시카고 연은 제공 **Real-Time Vintage Data 엑셀** 적재 필수. 최신 릴리즈 값으로 과거 덮어쓰면 **Look-ahead Bias 100% 확정**.

### Trap 2: CFNAI-SOI × HMM 충돌 (이중 평활)
CFNAI는 이미 시카고 연은 내부에서 차원축소·필터링된 지표. **HMM 입력(observation)으로 넣으면 평활화 이중 → 국면 전환 신호 후행(lagging) 위험 큼**. 매크로 원천 데이터(M3 등) 직접 HMM에 넣거나, CFNAI 쓸 경우 HMM 단계 우회 고려.
