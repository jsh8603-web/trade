---
tags: [type/consult-question, study/eq_us_cyclical, round/3]
date: 2026-05-30
---
# Round 3 질문 (마지막 라운드 — 수렴 종결 의도)

## §0 이전 라운드 결론 (Round 1+2 합의)
- v1 IC=+0.658 = 합성 DGP/look-ahead 의심. 실제 단일팩터 IC 0.02-0.08.
- Damodaran **중기 정상화 마진 회귀** (사이클/구조 분리), **fair_mult = (1-g/ROE)/(r-g)** multiple-independent 산출로 H10 동어반복 차단.
- EBP = HY OAS(BAMLH0A0HYM2)를 기대디폴트율+VIX 직교화 빈자판(GZ 정본은 verify).
- ISM = 라이선스로 FRED 재배포 중단 → CFNAI + 지역 연은(GACDISA066MSFRBNY) + Census AMTMNO 대체.
- 유효-n: 횡단 ρ̄≈0.5 → eff_n≈2. 결합 = Driscoll-Kraay (1998) 단일 최선책.
- Block: Politis-Romano stationary, 4Q 이상 블록, date-block 단위 횡단 통째 리샘플.
- ALFRED vintage + release-date PIT 정렬 절대 필수.
- HMM filtered가 아니라 **predicted prob (1 lag) P(S_t|y_{1:t-1})** 가 b(t) predictable·e-process supermartingale 보존.
- ★★★ Q1×Q4 충돌: regime 4국면 분할 시 국면당 유효관측 3-4개 → 통계 무모. **2국면(확장/수축) pooling** 권장(Claude).
- multi-sector 확장 시 ρ̄ 시변(위기시 →1) + Grinold √breadth 과대계상 + TVP-VAR 또는 섹터 더미 교호항 필요.

## §1 Round 3 의뢰 — 마지막 5개 (구현 확정용)

### Q1. 4국면 vs 2국면 — 시스템 호환 (★Q1×Q4 충돌 해결)
저희 yaml `study_session.yaml` 블록3 `relationships.relations[].lag_routing` + 블록4 `weight_rules.modulate_by` 가 regime 차원 단일 필드를 가정합니다.
- (a) **4국면(Reflation/Recovery/Overheat/Slowdown) → 2국면(확장/수축) 강등** 시 어떤 정보 손실이 발생하나요? Investment Clock 이론을 데이터로 검증 시 4국면 권장 vs 통계 검정력으론 2국면 — 어떻게 정합합니까?
- (b) **계층 구조 권장**: 2국면 pooling으로 power 확보 + 4국면 sub-overlay로 weight modulation 미세조정 — 이 하이브리드가 옳은가요? 아니면 regime label은 4개로 출력하되 stat test는 2국면 group?
- (c) 우리 카드 시스템(WeightAssumptionCard.delta_regime)이 4개 regime 델타를 보관하는데 OOS power 부족 시 어떻게 강등(shrink)? Bayesian partial pooling 권장?

### Q2. fair_mult 입력 산출 — 정상화 ROE / r / g
Claude Round 2의 정당화 배수 `P/E = (1-g/ROE)/(r-g)` 산출에 필요한 3 입력 각각:
- (a) **정상화 ROE**: 회귀 윈도 = 7-10년 + 침체 1회 강제 — 종목 자체 vs 섹터 평균 blending 가중치 권장(섹터 fixed effect 강도)? 음의 ROE 처리?
- (b) **자본비용 r_e**: CAPM r = r_f + β·ERP — β 산출 윈도 vs 60M rolling vs full-sample? ERP 추정(Damodaran implied vs historical 5%)?
- (c) **지속가능 g**: 잔여이익 모형 g_sus = ROE·(1-b) 또는 산업 장기 명목 GDP 동기화 — 어느 쪽이 PIT-safe?
- (d) 입력 노이즈가 fair_mult를 얼마나 흔드나? (입력 sensitivity analysis 권장 — Monte Carlo?)

### Q3. ISM 프록시 정확 ticker 검증 + 활용
- (a) FRED `AMTMNO` (Manufacturers' New Orders, Total Manufacturing) 가 실재하고 PIT release ~5-6주 lag, M3 advanced vs revised vintage 정확한가요? `BUSINV` (Total Business Inventories)와 monthly NO-Inv 직접 산출 가능한가요?
- (b) **CFNAI subindex 분해**: PI(production/income), EUH(employment), PCO(personal cons/orders), SOI(sales/orders/inventories) 4개 중 **SOI가 H3(ISM 선행) 대체로 가장 직결**인가요?
- (c) Empire State (`GACDISA066MSFRBNY`) New Orders/Inventories subindex 직접 FRED 접근 가능 ticker가 있나요(전체 헤드라인 외 하위지수)?
- (d) **CFNAI vs 지역 PCA vs Census AMTMNO-재고** — 3개를 ensemble하면 가산 vs 첫 PCA 우위?

### Q4. 시변 ρ̄ 보정 — 위기 시 eff-n 붕괴
Round 2 Claude 맹점: "ρ̄ 스트레스에서 →1, eff-n 정작 필요한 순간 붕괴".
- (a) **Driscoll-Kraay (1998) SE가 시변 횡단의존성을 자동 처리**하나요(공식적으로 cross-sectional dependence가 시변이어도 robust)? 아니면 별도 GARCH-style rolling ρ̄ 추정 필요?
- (b) **stress 윈도 down-weight 가중치**(eff-n 명시 축소) — DUR (Driscoll-Kraay) + GARCH 결합이 학계 표준인가요?
- (c) **Grinold √breadth 과대계상 보정**: 섹터 추가 시 effective_breadth = N_sectors·(1-avg_sector_corr)/(1+...) — 이런 보정식의 출처?

### Q5. 가설 H1-H10 우선순위 — 2-3단계 검증 순서
다음 라운드(2-2 이론학습 + 2-3 실데이터 검증) 진입을 위해, **반드시 먼저 데이터로 가려야 할 핵심 H 3-5개**를 우선순위로 선정해 주세요:
- 후보: H1(정상화 E/P trough 최강), H2(val↔mom 위상교차), H3(ISM 선행), H4(EBP 공통원인), H5(rate_beta name-specific), H6(peak_trap 스팟-싼 거짓신호), H7(DOL EPS 증폭), H8(revision breadth 전환점), H9(CMA 섹터무관), H10(re-rating Δmultiple).
- 기준: (i) 통계 power(eff-n 가능 여부) (ii) 데이터 가용성(EDGAR+FRED+ETF holdings 즉시 적재 가능) (iii) 시스템 코드화 leverage(블록4 weight_rules 직접 영향).
- 추천: 우선순위 3-5개 + 각각 (적합 통계 기법·필요 데이터·예상 결과·반증 확정 임계).

## §2 응답 기대 양식
- 한국어, 섹션별(Q1-Q5) 명확 구분.
- Q3 ticker는 verified/unverified 명시.
- 모순·반론 환영. 길이 2500-4500자.
- **이번 라운드로 수렴 종결 예정** — 마지막 명시적 의문이나 결정적 함정 있으면 끝에 별도 §추가경고로.
