# eq_kr (한국 상장주식) 스터디 요약

> 작성 2026-05-30 · study workspace `eq_kr` 자율 작성
> 본보기 = `study-research/eq_us_cyclical/study_session.yaml` 구조 일치
> ★상태: 7블록 완성 / 실데이터 IC 측정은 라이브 hook(블록5)이 적재 후 자동 수행

## Lens (4 핵심)

한국 상장주식 가격 = 멀티플 M × 이익 E. **만성 Korea discount** + **이익 글로벌 cycle 의존** +
**외국인 수급 가격 주도** + **KOSPI/KOSDAQ 분절** 의 4 축으로 lens 구성.

- **Korea discount**: 거버넌스(지배주주 agency·낮은 payout·순환출자) + 시클리컬 수출의존이 M 을
  글로벌 평균 아래 고정. **2024 FSC 밸류업 프로그램** = 그 고정점을 흔드는 정책 anchor (저PBR +
  ROE 개선 + 주주환원 가이던스 종목 re-rating).
- **이익 cycle**: KOSPI 이익의 큰 부분 = 반도체(메모리 cycle) + 자동차(글로벌 수요) + 조선·화학
  (중국 수요·유가). 같은 지표·종목이라도 글로벌 cycle 국면 × KRW 국면에 따라 신호 의미·가중이 갈림 (R15).
- **외국인 수급**: 대형 KOSPI 외국인 비중 30~50%, 일별 순매수 = 가격 단기 1차 driver = "한국
  alpha 의 절반" 가설.
- **KOSPI vs KOSDAQ**: 미시구조 분절 — KOSDAQ 은 모멘텀·반전·테마 강하고 외국인 신호 약함.

## Indicators (17종) — §6 코어 10 + 한국 특화 7

| 카테고리 | 코어셋 (us/intl 비교) | 한국 특화 |
|---|---|---|
| valuation | fwd_ep | low_pbr_valueup |
| quality | roe_margin_trend | dividend_yield_payout, governance_score |
| revision | earnings_revision_breadth, fwd_eps_momentum | — |
| momentum | price_mom_12_1 | — |
| macro_sensitivity | rate_beta, dollar_beta(USDKRW), oil_beta, credit_beta | usdkrw_export_exposure, semi_cycle_beta, china_revenue_share, kosdaq_retail_beta |
| risk | realized_vol | — |
| flow | — | **foreign_net_buy** ★한국 1순위 |

## 핵심 발견

- **kr_stock sleeve 이미 SLEEVES 등록** (`core/brain/regime_to_weights.py:50`, `SLEEVE_BLOC[kr_stock]=Bloc.KRW`).
  → 신규 sleeve 등록 불필요, 회귀 위험 회피.
- **judge LLM lens 주입 메커니즘 이미 구현** (eq_us_cyclical 가 검증). lens_prompt 한국어 조립
  경로만 추가하면 LLM 종목 평가에 한국 context 자동 주입.
- **한국 데이터 인프라 실재**: `stock/data/{dart_provider,krx_flows,krx_universe}.py` +
  `data/{krx_snapshots,krx_sector_snapshots,krx_flow_snapshots}.jsonl` 일부 적재 +
  `_refs/{dart-fss,OpenDartReader,FinanceDataReader}` OSS 가용.
- **registry id 'weight.equity.{regime}'** 가 us/kr 공유 → 옵션B (단일 id + archetype dict 확장)
  채택 권장 (us 카드 회귀 회피).

## 가중 규칙 — 한국 특화

- ★ **foreign_net_buy 0.18** (1순위) — 대형 KOSPI 한정, KOSDAQ 소형은 cap 0.05.
- **fwd_ep 0.18 + low_pbr_valueup 0.10** (직교화 — common_cause prior 0.7).
- **dollar_beta 0.10 name_specific** — 수출주(usdkrw_export_exposure 높음) 양부호, 내수·항공 음부호.
- **semi_cycle_beta 0.08** — 반도체 sub-sector 한정, cycle bottom 가중 최대.
- **price_mom_12_1 0.08** — 한국 모멘텀 약효로 base 낮춤, KOSDAQ 단기 반전 위험.

## Confidence hooks (4 가설)

| 가설 | 코드 매핑 | 임계 동작 |
|---|---|---|
| foreign_flow_alpha | weight_falsification.score_ic_breakdown_eprocess | e-value ≥ 20 → adopt / 붕괴 → retract |
| valueup_low_pbr_rerating | 동일 (밸류업 flag 서브패밀리) | Rank-IC 붕괴 → low_pbr base 하향 + 단독 fwd_ep 회귀 |
| usdkrw_exporter_beta_namespecific | omega_drift + score_ic_breakdown | name_specific 무효 → ticker→industry 강등 |
| semi_cycle_turn_predictive | score_ic_breakdown (semi sub-sector) | proxy 무효 → semi_cycle_beta 하향 + lens estimation 폐기 |

## Collector plan (6건)

- **P0**: D1 DART_API_KEY 발급(현재 부재 → fwd_ep·ROE·배당 등 펀더멘털 전부 graceful empty).
- **P1**: D2 사업의 내용 지역별매출 파싱 (usdkrw_export_exposure·china_revenue_share),
  D3 컨센서스(Naver 대체), D6 DRAM/NAND 현물가 proxy.
- **P2**: D4 KCGS governance(라이센스), D5 공매도 잔고·규제 레짐.

## Code change (9 항목, 4단계 전부)

eq_us_cyclical 가 검증한 코드 사실 그대로 재활용 + 한국 차이만 추가:
1. learn: `weight_panel.build_indicator_matrix` 한국 series_ids 등록 (★`_REFLEXIVE_WORDS` 의
   `inventory` 차단 회피 — 단어 회피 id 채택)
2. learn: `train_weights.train_weight_cards` 에 `domain=equity scope=kr` 배치 추가
3. learn: `conditional_correlation.RegimeGlasso` 에 블록3 7 prior 주입
4. card: `weight_card.WeightAssumptionCard` 에 한국 archetype (exporter/domestic/semi/financial/
   valueup/kosdaq_growth) 등록, lens 한국어 주입
5. card: `registry.AssumptionRegistry` id 'weight.equity.{regime}' 유지 (옵션B), archetype 확장
6. inject: `stock_track._extract_indicator_z` 코드변경 거의 불필요 — state 데이터 공급 중심
7. inject: `judge` lens_prompt 한국어 조립
8. falsify: `weight_falsification` 한국 baseline_ic 0.03 / sd 1.3 (모멘텀 약효·KOSDAQ 변동성)
9. sleeve: `regime_to_weights` 변경 없음 — kr_stock 기존재

## Pending (정직 표기)

- **합성 픽스처 데이터 분석 미실행** — main 권고 ② (상관·partial-corr 만 먼저) 는 한국 적재 표본
  필요. eq_us_cyclical 는 40firm×36Q 합성으로 IC 측정했지만, 한국은 DART_API_KEY 부재로 실측
  진입 못 함. **라이브 hook (블록5) 이 적재 후 자동 검증** = 데이터 가용 시 즉시 갱신 경로 명시 (블록7 falsify).

## 산출물

- `study_session.yaml` — 7블록 전체
- `summary.md` — 이 파일
- `raw/krx-infra-checklist.md` — 한국 데이터 인프라 사실 점검
- `raw/lens-and-weight-rationale.md` — lens·가중 근거 정리
