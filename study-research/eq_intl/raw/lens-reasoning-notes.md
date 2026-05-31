# eq_intl lens 도출 raw 노트 (2026-05-30)

자문 채널(gemini-web/claude-web) = 9세션 경합 가정 → §2 폴백 규정대로 도메인지식+코드Read 기반
직접 도출. lens 는 글로벌 매크로/횡단면 투자 표준 이론(AQR cross-country momentum·value,
dollar-EM 관계, China credit impulse, Investment Clock)에 근거. 향후 IC 대조는 블록6 데이터 필요.

## 자산 정의
국가/지역 지수 ETF. 예시 유니버스:
- DM broad: EFA, VEA, IEFA. EM broad: EEM, VWO, IEMG.
- 단일국 DM: EWJ(일본) EWG(독일) EWU(영국) EWA(호주) EWC(캐나다).
- 단일국 EM: EWZ(브라질) INDA(인도) FXI/MCHI(중국) EWY(한국) EWT(대만) EWW(멕시코) EZA(남아공).
- 지역: VGK(유럽) AAXJ(아시아ex일본).

## 핵심 통찰 (왜 단일종목과 다른가)
1. unhedged USD ETF 의 TR = 현지지수 + 환. 환을 빼면 절반 누락 → macro_sensitivity 1차축 승격.
2. 국가 = 한 자산. 종목단위 obs 부족 → archetype soft membership(부록B hierarchical pooling).
3. 국가 archetype 6종: commodity_exporter / tech_exporter / domestic_demand / dm_europe /
   dm_japan / em_china. 한 국가가 복수에 soft 소속(π).
   - 브라질=commodity_exporter 0.8. 대만/한국=tech_exporter 0.7. 인도=domestic_demand 0.7.
   - 일본=dm_japan(엔inverse) 1.0. 독일=dm_europe 0.8+manufacturing. 중국=em_china 1.0.

## 코드 Read 로 확인한 사실 (블록7 근거)
- `fred_adapter.FRED_SERIES`(L36-57): 16 시리즈, growth/inflation/financial 만. **dollar·oil·real
  yield 부재** → eq_intl 1차 driver 가 데이터에 없음(블록6+블록7 learn 1순위).
- `weight_panel.build_indicator_matrix`(L140): series_ids PIT 행렬. 반사성 게이트(L53 _REFLEXIVE_WORDS)
  = position/holding/own/strategy 등 차단 → 'dollar_beta'/'mom_12_1'/'country' 토큰은 통과(시장지표).
- `weight_card.composed_weights(pi)`(L115): w_global+δ_regime+δ_arch+δ_inter. delta_arch_by_type
  + π → soft archetype 혼합(L135-144). = 국가 archetype 매핑 지점.
- `weight_card.derive_weights`(L208): w∝Ω·IC Grinold + 1/N blend + capped-simplex. cap=0.40 기본.
- `stock_track._apply_r15_sizing`(L242): S_L1=clamp_floor(Σwᵢzᵢ), composed_weights(_regime_pi),
  천장 불변식(down-only). _resolve_weight_card(L208)=weight.equity.{regime} 조회 → intl scope 분기 필요.
  _extract_indicator_z(L224)=raw feature 키매칭 → 국가지표 키 확장 필요.
- `regime_to_weights.SLEEVES`(L50)=[us_stock,kr_stock,commodity,gold,bond,cash,coin]. **intl 부재**
  → intl_stock sleeve 신규(자산배분 회귀 민감, BASE_WEIGHTS 재정규화 필요).
- `weight_falsification.score_ic_breakdown_eprocess`(L66): e-CUSUM 단측, IC 붕괴만 kill(개선 floor).
  Ville 거짓kill≤alpha. = confidence_hooks reject_signal 매핑 지점. weight_card_verdict(L109) →
  update_controller.step(L90, PRIMARY→RETIRE/SECONDARY→KEEP+refit).

## 미해결/main 판단 필요
- fx sleeve 승격(unhedged 환 부당캡) — 3-test + uncapped IC 유의 시.
- 지수집계 펀더멘털 소스(MSCI 유료 vs ETF 구성종목 프록시) — 비용 판단.
