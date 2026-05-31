---
tags: [type/summary, domain/commodity, phase/study-system, version/v2]
date: 2026-05-30
note: v2 산출 요약 (사람용). direction.md + theory-notes.md + validation-summary.md 통합.
---

# commodity v2 스터디 요약 (사람용)

> **v2 산출 메타**: direction.md 591줄 (자문 3R × 2채널) + theory-notes.md 591줄 (학파 정독) + validation-summary.md (실데이터 검증) + study_session.yaml 7블록. raw/v1/ 에 이전 산출 보존.

## 1. 핵심 발견 5건 (실데이터 검증 결과)

| # | 발견 | 통계 | 의의 |
|---|---|---|---|
| 1 | **★Tang-Xiong 2012 financialization 압도적 재현** | pre-2004 cross-corr=0.045 → 2004-2010=0.296 (6배), Welch p≈0 | H5 outcome 강력 확인. risk-off 시 0.37 spike. 가설 prior 0.7→0.85 |
| 2 | **★Copper bellwether lag 12m optimal** | INDPRO YoY ↔ Cu spearman lag 12m=0.40 (p=1e-12) vs 3m=0.15 | H4 lag 3m → **12m 정정**. China demand → supply chain 1년 시차. prior 0.75→0.85 |
| 3 | **★Hamilton NOI threshold 정정** | NOI 30% = 25년 1건. **NOI 10% = 12건, 12m fwd CFNAI -0.46 vs normal -0.13** | H7 threshold 30% → **10% 정정**. threshold-conditional 작동 |
| 4 | **gold-real-rate weak partial corr** | 36m rolling partial-corr mean = -0.074 (강한 음수 X) | gold 방 결과 ("decoupling 기각, β 안정") 정합. H1 (참조) prior 0.9→0.55 |
| 5 | **DBC roll cost drag 약화** | mean DBC-WTI 12m = -3.6%/yr, fraction<0 = 50% | DBC = optimized contango-resistant. 진짜 H3 검증 = CME contract chain (Phase 2) |

## 2. v2 자문 라운드 요약 (R1+R2+R3)

**R1 (gemini Pro 8441자, claude-web 미완)**: 학파 8종 (Tang-Xiong/BGR/Hamilton/Kilian/Erb-Harvey/Baur-Lucey/KWB/HK) + 검증 통계 5종 (FIGARCH/Bai-Perron/Westerlund-H/Fama-MacBeth/Hamilton NOI) + 가설 8개 yaml.

**R2 (gemini 8511자, claude-web 미완)**: 구현 디테일 7개 — BGR basis_momentum 정확한 수식, FIGARCH weekly resample, Bai-Perron PELT 적용, e-CUSUM K adaptive, Tang-Xiong measure (MM net long/OI z), B matrix sub-sleeve 별 구조, ENSO ONI.

**R3 (gemini 6851자 + claude 14864자 — knowledge-only prefix 작동)**: claude 결정적 critique 7건:
1. ★**H5 ≠ H8 construct 분리** (financialization = CIT 인덱스 자금 vs MM = active speculator). Gemini measure 가 다른 가설로 혼동
2. ★**PELT ≠ Bai-Perron** 명명 오류 + 경제이벤트 ±3m confirm = HARKing (look-ahead bias). 진짜 Bai-Perron sup-F + break CI 가 이벤트 포함 시 confirmation
3. ★**Look-ahead bias** (R1·R2 침묵) — ALFRED real-time vintage 의무. CFNAI/WASDE revise 시 IC 부풀려짐
4. ★**Kilian 2009 SVAR** 누락 — Hamilton NOI 의 source-conditional sharpen (supply/demand/precautionary)
5. ★**Gorton-Hayashi-Rouwenhorst 2013** 통합 명제 — KWB+HK 가 inventory state variable 매개. H2/H3/BGR redundancy 가능성
6. ★**Two-speed**: Quarterly Bai-Perron + online e-CUSUM (monthly vs quarterly 이분법 폐기)
7. ★**SLEEVE_BLOC 3-group**: cyclical (energy+industrial) / defensive (precious) / idiosyncratic (agri). 2x2 대칭 거부 — agri 는 safe-haven 아님

## 3. 가설 11개 분류 (Phase 1/1.5/2/3)

### Phase 1 (즉시 검증, 자원 0):
- ✅ H1 gold_real_rate_nexus (gold 방 종결)
- ✅ H5 financialization_reflexivity outcome (★강력 확인)
- ✅ H4 china_demand_bellwether (★강력 확인, lag 12m)

### Phase 1.5 (collector 쉬움):
- H7-raw oil_macro_NOI (Hamilton, threshold 10% ★검증)
- H8 cot_momentum (MM net long/OI, ★H5 와 분리)

### Phase 2 (CME + EIA + USDA + Kilian SVAR):
- H2 theory_of_storage_backwardation
- H3 roll_cost_drag (진짜 검증, CME chain)
- H6 usda_surprise_jump (expectation 데이터 hardest)
- H7-K oil_macro_kilian_decomposition
- H9 storage_limit_nonlinearity ★신규 (Deaton-Laroque)
- H10 ghr_inventory_state_variable ★신규 (GHR 2013 통합)
- H5 driver (CIT/Barclays)

### Phase 3 (시스템 통합 후):
- H11 liquidity_storage_constraint_crash (kill switch composite)

## 4. Collector 우선순위 (양쪽 모델 합의)

1. **DFII10 (FRED)** — 1줄 추가, H1 gold 방 unlock 완료. real_rate 분리 효과
2. **CFTC COT (public API)** — 무료/주간/쉬움. H8 (speculative) 입력
3. **CME term structure** — H2/H3/BGR + H9 + H10 모두 unlock. ★effort 최고/value 최고
4. **EIA inventory** — H9 (Cushing 가동률) + days_of_supply. FRED WCESTUS1 404 → EIA Open Data 직접
5. **NOAA ONI** — agri sub-sleeve conditioning, revision 거의 없음
6. **USDA WASDE** — H6 expectation 데이터 hardest, ROI 가장 낮음

## 5. 학파 정독 (theory-notes.md Part A+B+C)

- **Part A 보편**: Theory of Storage (KWB), Hicks-Keynes backwardation, Erb-Harvey 3분해, GHR 2013 통합, Deaton-Laroque skewness
- **Part B SOTA**: Tang-Xiong financialization, BGR basis_momentum, AMP carry+momentum, Kilian SVAR, Szymanowska basis premium, Hamilton NOI
- **Part C sub-sleeve**: Energy (Kilian + shale + crack), Industrial (China + LME + Cu bellwether), Precious (silver/Pt — gold 방 분리), Agri (USDA + ENSO + bioenergy)
- **Part D 메타**: ALFRED vintage, deseasonalization (STL/X-13), HAC SE (Hansen-Hodrick)

## 6. weight_rules 핵심 ★검증 반영

| 지표 | base_weight | regime modulate | 검증 결과 |
|---|---|---|---|
| roll_yield | 0.20 | Cushing>85% → 0 (★H9) | term structure 필요 |
| bgr_basis_momentum | 0.15 | GHR conditioning | CME 필요 |
| indpro_yoy | 0.15 | YoY>+3% 시 industrial +0.05 (★lag 12m) | spearman 0.40 |
| convenience_yield_z | 0.10 | industrial 가중 ↑ | term structure |
| days_of_supply | 0.10 | oversupply flag → ↓ | EIA |
| real_rate_dfii10 | 0.10 | precious 강제 음 | gold 방 weak (-0.07) |
| dxy_index | 0.05 | risk-off 시 ↑ | FxStore |
| momentum_12_1 | 0.05 | trending 시 ↑ | AMP 2013 |
| realized_vol_60d | 0.05 | risk-off 시 ↑ (vol scale) | |
| cross_sector_mean_corr_60d | 0.05 | ★0.30 시 diversification 무효 | ★검증 완료 |

## 7. SACRED 영향 영기 (블록7 risk 종합)

- **반사성 게이트** (weight_panel._REFLEXIVE_WORDS): "inventory" 토큰 회피 → days_of_supply 명명. 코드 무변경
- **천장 불변식** (assert_ceiling_invariant): Judge lens 주입 = down-only attenuation. S_out ≤ S_L1 보존
- **registry append-only**: 새 카드 transition 만, 기존 카드 mutation 0
- **train_weights 회귀 0**: 신규 cron entry, 함수 본문 변경 없음
- **update_controller**: kwarg 추가만 (default = stock 동작)
- **Look-ahead bias 차단**: ALFRED real-time vintage 의무 (모든 신규 collector)
- **archetype pooling (부록 B)**: ticker 독립 학습 X, sub-sleeve archetype prior + soft membership
- **gold 방 조율**: gold = 별도 sleeve `precious_gold`, 본 방의 precious = `precious_non_gold` (silver/Pt/Pd)

## 8. main 요청 사항

1. Phase 1 가설 3개 (H1 gold-ref / H5-outcome / H4) 강력 확인 완료 → wiring 즉시 가능
2. Phase 1.5 collector (CFTC COT) 다음 우선 (H8 + H5 driver 일부)
3. ALFRED real-time vintage 의무 — 신규 collector 5개 모두 vintage_knowable_from 필드 필수
4. archetype pooling (4 sub-sleeve) → train_weights 신규 cron entry 사용
5. Kilian SVAR 분해 도입 (H7-K) — statsmodels VAR + structural identification 또는 별도 패키지
6. gold 방과 본 방 조율: gold 결과 (β 안정, decoupling 기각) → 본 방 H1 reference 통합 처리

## 9. 다음 행동 (main wiring 시 입력)

- `study_session.yaml` 7블록 → study_register 진입
- raw/round-*.md + theory-notes.md + validation-summary.md 모두 갖춤 → KIT v2 §2-3 raw 강제 통과
- v1 산출 (raw/v1/) = 보존 (폐기 X)
- Phase 2 collector (CME term structure) 도입 후 H2/H3 진짜/H9/H10/BGR 재검증 라운드 필요
