---
next-action: "P8 미배선 전수 배선(최종테스트=study대로 돌게). 우선순위 A(eq_kr rotation/selection·eq_intl·reit SLEEVE_AGG=데이터완비 즉시배선) → B(crypto3·commodity10·bond5 collector) → C(보류). ⛔production core 무단변경 금지+off=byte-identical opt-in(W3 패턴)+study 덮어쓰기 금지(미국식 임의신호 X). 방어주 자문 t-stat 검증(bo3yvytt9) 결과로 ledger 박제 마무리."
session: btn-Inv (opus, long-mode ON2 750k)
date: 2026-06-08
tags: [type/handoff, topic/wiring-gap, domain/multiasset, tier/study-runtime]
related: progress-final-test-20260607.md(P8), cross-regime-ledger.md, handoff-multiaxis-roadmap-20260608.md
---

# handoff — study↔런타임 미배선 전수 배선 (2026-06-08)

> ★사용자 재방향(2026-06-08): 미배선 = "go-live 이연"이 아니라 **지금 최종테스트라 다 배선해야 함**. study의 "go-live 무접촉"은 라이브 매매 전제일 뿐, 백테스트는 study대로 측정해야 의미. **배선 안 된 채 도는 테스트 = study 미반영 = 무효**. 배선 최우선.
> 7개 read-only subagent로 전수 검토 완료(6라벨: WIRED/U-a정의부재/U-b dead/U-c미반영/DEFERRED/MISWIRED). 본 파일 = 그 결과 상세 박제.

## §1 현재 상태 · 첫 행동

**현재 상태**: W3(eq_us defensive weight_rules)·W6(C1 측정정정)·W5(VIXCLS) 완료. 미배선 전수 검토 완료. 방어주 종목선택 팩터 자문(gemini+claude) 수렴, t-stat 검증 백테스트(bo3yvytt9) 진행 중.

**첫 행동(재개)**:
1. bo3yvytt9(`.p4-tstat-verify.log`) 완료 확인 → defensive/cyclical selection alpha t-stat 추출. |t_defensive|<2면 "밸류 단독=신호부재" claude claim 채택→cross-regime-ledger 박제 / |t|>2면 기각·재검토.
2. **P8-A 즉시배선 착수**: eq_kr rotation/selection(아래 §4-3) → `_bt_kr_picks` + `sleeve_signals.py` 한국부호. ⛔study대로(거시 조건부 rotation), 미국식 cheapness 임의정의 금지.
3. 각 배선 = off=byte-identical opt-in(W3 패턴: 인자 None이면 기존 경로), production core 무단변경 금지.

## §2 진행 맵

- W2(regime)·W3(eq_us 업종배분)·W5(VIXCLS)·W6(C1 측정) = ✅ 완료(progress P6).
- **P8 미배선 배선** = 본 핸드오프 주제. A 즉시(데이터완비) → B collector → C 보류.
- 방어주 종목선택 = 자문 수렴, t-stat 검증 후 ledger(현행 ETF 유지 정당 방향).

## §3 사용자 박제 (대화 고유)

1. **미배선 = 최종테스트라 다 배선 필수**(go-live 이연 아님). 배선 안 된 테스트=무효.
2. **자문 무비판 수용 금지** — 데이터로 falsify 후 채택, 채택분만 ledger.
3. **study 덮어쓰기 금지** — W3 1차 실수(자문 일반론 부호표 임의박제) 재현 금지. study대로 배선(eq_kr=거시 조건부 rotation, 미국식 cheapness 임의정의 X).
4. **불변식**: production core/stock 무단변경 금지 / off=byte-identical opt-in(W3 factor_z=None 패턴) / push·go-live·실주문 미접촉 / 안전장치값(MAX_WEIGHT_SINGLE 0.10/SECTOR 0.30) 무단변경 금지.
5. **연결됨(WIRED) 기준**: ①정의존재(grep) + ②호출연결(호출처≥1 dead아님) + ③의사결정반영(logging 아닌 실제 비중/선택/공분산 영향) 3단 전부.

## §4 미배선 상세 (★배선 읽은 내용 전부 — subagent 7 결과)

> 각 항목: study 경로 → 런타임 진입점 → 라벨 → 배선법. subagent output = `C:\msys64\tmp\claude\D--projects-Inv\d23da8ed-6062-4394-82fe-8e420e96344e\tasks\{id}.output`.

### §4-1 gold (id=a23829fb8048dfd42) — 미배선 0 ✅
- WIRED 18건: SEED_CELLS(`core/study/factor_betas_seed.py:112-118` real−0.233/dollar−0.300/oil+0.108/credit reject/**vol β:=0 lock** self-test:344/breakeven reject/fx denom+1.0) · FACTOR_SERIES(`core/data/factor_returns.py:34-40`) · REGIME_DIRECTION(`core/brain/regime_to_weights.py:75-83`) · SLEEVE_AGG[gold]=1.0(:180) · corr_prior build_seed_betas(:252)+static Λ(:259, Λfx=0.15)+W roll-up(:270). **완전배선, 손댈 것 없음**.

### §4-2 eq_us (id=af52855db1f5ab086) — WIRED 11, 미배선은 전부 의도적
- WIRED: REGIME_DIRECTION(`regime_to_weights.py:74-85`)·defensive `_DEFENSIVE_BAND=(0.10,0.28)`(`portfolio_decompose.py:54`)·defensive real_rate z 보간(:108-154, W3)·mega_tech 고정 mid(:136)·cyclical cap(:127)·signs cyclical{pbr,ev_ebitda}(`sleeve_signals.py:27`)/defensive{net_issuance,ep_yield}(:31)·**DEF-2 interaction dividend_yield×op_profitability**(:54)·SEED(`factor_betas_seed.py:104`).
- **U-a `_sleeve_rotation.py`** — ⛔**폐기 금지. 압축 후 3R 자문으로 처리(사용자 2026-06-08).** us_stock 내부 cyclical/defensive/mega 비중을 경기 따라 조절하는 **파이프라인 핵심 중 하나**.
  - **코드**(`study-research/eq_us/_sleeve_rotation.py`, grep 0=미배선): base=shrunk inverse-vol(1/3 + inverse-vol 절반수축) + 예측 rotation tilt(cyclical←credit baa_aaa−/defensive←dollar+/mega←real_rate−, predictive single-slope `excess_{t+1}~β·x_t` expanding z, walk-forward OOS gate).
  - **현재 적용 중인 us 업종 코드**(별개 경로, 배선됨): `portfolio_decompose.decompose_weight`(cap 시총비례 base + defensive real_rate z 보간[W3] + cyclical cap + mega 고정), `_bt_us_picks` 경유.
  - **측정(2026-06-08 실행, _sleeve_rotation.py)**: 예측 rotation 층만 STATIC_ONLY(n=136, predictive β=−0.0006·OOS active IR 0.124 비유의) = "미래 예측해 미리 갈아타기"는 OOS 탈락. **이건 예측층 1개 결과지 폐기 아님.**
  - **★다음 세션 3R 자문 처리**: us 업종 base/조절 설계 확정 — (a) base = cap(W3 현재) vs inverse-vol(_sleeve_rotation 의도) (b) 조절 = W3 동시 real_rate vs _sleeve 예측(STATIC). gemini+claude 3R + 데이터 비교 후 배선. **두 study(eq_us weight_rules vs _sleeve_rotation)가 같은 us 업종을 다른 base·방식으로 설계한 정합성 미결.**
  - **경기별 조절 본체는 작동 중**: 자산군간 REGIME_DIRECTION + us 업종 W3 defensive real_rate. 예측층 죽음 ≠ 경기 조절 제거.
  - ★**실측 study 존중(사용자 2026-06-08)**: 슬리브간 비중 조절은 전부 실측 데이터 study(헤더 = 자문 3R 확정 spec). base=shrunk inverse-vol·기계론축 sign 고정(credit/dollar/real_rate)·predictive single-slope·walk-forward OOS gate 모두 실측 산물. STATIC_ONLY도 그 study가 walk-forward로 측정한 결론이지 임의 판단 X. ⛔다음 세션 처리 = study대로(미국식·임의 변경 금지). base는 study가 inverse-vol로 실측했고, W3 cap base와의 정합성을 3R 자문으로 가린 뒤 study 결과 존중해 배선.
  - **★다음 세션 1번 처리 레시피**(사용자 "코드 적용 방법 잘못됐을 수도 + 3R 자문 받고 처리"):
    (1) `_sleeve_rotation.py` 실행 → `_sleeve_rotation_results.json`(STATIC_ONLY, predictive β−0.0006/OOS IR 0.124) 재확인. ★"코드 적용(배선) 방법이 틀려서 STATIC 나왔나"도 점검(예: base/축/lag/expanding z 구현 오류 여부 — study spec vs 실행 1:1).
    (2) **3R 자문**(gemini+claude): "us 주식 안 3업종(경기민감/방어/메가) 비중을 ①시총비례 고정(cap) ②역변동성 base ③금리·신용·달러 동시조절(W3 류) ④예측 갈아타기(OOS 탈락) 중 base와 조절을 분리해 무엇이 최적인가? 실측 study가 inverse-vol base + 예측을 설계했고 예측은 OOS 죽었는데 base까지 버려야 하나?"
    (3) **데이터 비교**: 각 base(cap/inverse-vol)×조절(없음/W3 real_rate/예측) 조합 백테스트 → Sharpe·수익·MDD 비교. 우월 조합 채택.
    (4) **배선**: study 결과 존중해 `portfolio_decompose.decompose_weight`(base 로직) + `_bt_us_picks` + `_sleeve_rotation.py` base 함수 연결. off=byte-identical opt-in. ⛔폐기 금지.
- U-b confidence_hooks CP-EUS-1(eq_us yaml:260-268, fhc_adapter 진행중).
- U-c vix_term_structure·cyclical vix_beta(judge 하향전용 의도).
- MISWIRED cyclical hy_oas(yaml [0.08,0.22] hy_oas_sensitivity vs runtime cap 고정 → 부호충돌 동시−0.120/forward+0.460 OOS>IS 과적합, 자문수렴 cap유지 의도).
- ★defensive signs study 근거 = `eq_us_defensive/study_session.yaml` net_issuance IC+0.082/ep_yield IC−0.056, sleeve_signals.py:28-30 주석 1:1. **study대로 배선 확인됨**.

### §4-3 eq_kr (id=ae8ba6009206c7cd8) — 미배선 9건 ★P8-A 최우선
- study 완성: `eq_kr/study_session.yaml` + `eq_kr/industries/_rotation/`(_sleeve_rotation_kr.py 2층·within_industry_residual_kr.py 3층·rotation-study_session.yaml·candidate-ledger.md) + handoff-rotation-wire5-20260606.md(자문3R+audit PASS).
- **2층 rotation**(_sleeve_rotation_kr.py: active share 11.4%, 비중 13배 차등, κ통과 4업종 chemical/steel/refining/telecom IC≥0.29, 거시신호 dgs2/fedfunds/jpykrw) → `grep _sleeve_rotation_kr scripts/ core/ stock/ = 0`. **미배선**.
- **3층 selection**(within_industry_residual_kr.py: capsule IC + EB v3 계층베이즈, robust 中=반도체ρ0.36/철강0.29/aitech0.28만 실효, 9곳 약함=small market 구조 타당) → grep 0. **미배선**.
- **SLEEVE_SIGNS 한국부호**(`sleeve_signals.py:24-34` 미국만) → `signs_for("battery")={}` → ETF/EW fallback. **미배선**.
- build_universe_candidates 한국 우회(`construction.py:131-134` _ETF_FALLBACK_ROUTING). archetype pooling 한국 부재(regime_to_weights SLEEVES). e-CUSUM 한국 미dispatch(weight_falsification). 조건부 gating(financial credit-spread).
- DEFERRED: financial_cs_mom_rate_up(base_weight=0.0, 2nd Fed cycle 대기)·kr_quality_core/kr_revision_core(미측정).
- ★study가 "production core/stock 무접촉=byte-identical, go-live D1-D5 인간게이트 이연" 명시(handoff-rotation-wire5:12·22). **배선법(P8-A)**: `_bt_kr_picks`(scripts/run_multiasset.py:553)에 _sleeve_rotation_kr 호출 + `sleeve_signals.py` 한국부호 추가(off byte-identical opt-in). ⛔미국식 cheapness 임의정의 금지 = study가 거시 조건부 rotation으로 설계(미국 value와 다른 unit).

### §4-4 crypto (id=a8fe60b9ed560a4a0) — 미배선 3, 오배선 0
- WIRED: mvrv_btc(`instrument_source.py` CoinMetricsMvrvProvider)·fgi(`coin_track.py` _extract_fgi/_fgi_to_regime)·funding_rate(`coin_consensus_lens.py` CoinLensData).
- **미배선(collector 미구현)**: stablecoin_total_supply(adopted 0.2, DefiLlama /stablecoincharts/all)·etf_net_flow_usd(adopted 0.05, Farside HTML scrape)·halving_phase(adopted 0.1, 결정론 days_since_halving 함수).
- 오배선 0: rejected/candidate(coin_core_buyscore/tsmom/xs_momentum/realized_vol) 전부 grep 0(정당).

### §4-5 commodity (id=a195224707220e403) — 미배선 10 (대부분 collector)
- WIRED: FACTOR_SERIES/SEED commodity(real−0.003 reject/dollar−0.189/oil+0.597 본체/credit/vol−0.153/breakeven+0.117/fx+1.0)·SLEEVE_AGG[commodity]=1.0·REGIME_DIRECTION commodity top.
- **미배선**: roll_yield·bgr_basis_momentum_12m·convenience_yield_z(CME term structure collector 미구현, 연쇄)·days_of_supply(EIA Open Data)·china_credit_impulse_z(BIS)·wti_noi_1yr(H7 NOI 계산)·cit_long_position_z(financialization)·cross_sector_mean_corr_60d(commodity sub-sleeve 분리 미측정)·INDPRO 12m lag routing·mm_net_long_oi_z(CFTC 있으나 2026-05-31 audit validated_alpha=false 격하).

### §4-6 eq_intl+reit (id=a7798fa5bc35c9208) — 미배선 4 (sleeve 신설 이연)
- eq_intl factor β(dollar−0.297/vol−0.648 validated, `factor_betas_seed.py:129-136`) + cross-corr(eq_cyc↔eq_intl +0.838) measured.
- reit factor β(dollar−0.100/vol−0.583, :138-145) + cross-corr(↔eq_cyc +0.686, ↔defensive +0.678) measured.
- **미배선 root**: SLEEVE_AGG(`regime_to_weights.py:177-181`)에 eq_intl/reit 미등록 → corr_prior roll-up 0 기여. SLEEVES(:50) 7개만(us/kr/commodity/gold/bond/cash/coin). sleeve_returns SLEEVE_TICKERS 미등록.
- DEFERRED: sleeve 신설 = portfolio 구성 결정(SLEEVES 확장, go-live 인접). 배선법: SLEEVE_AGG 매핑만 추가하면 factor roll-up 활성(단 배분 차원 sleeve 신설은 사용자 결정).

### §4-7 bond_cash+macro (id=a14c67c44f7244d8c) — macro 8/9 WIRED, bond 5 미배선, 오배선 0
- macro WIRED: 물가2D(`regime_classifier.py` 절대CPI 게이트 STAGFLATION_ABS_CPI_GATE=3.0 + SLOWDOWN)·stock-bond glasso(`regime_to_weights.py:283-299` belief_conditional_cov)·REGIME_DIRECTION·real/breakeven(factor_returns)·M1물가/M5transition.
- macro 미배선 1: transition freq 관측지표(`indicator_event_correlation.py` RECESSION_ONSET만, 전환빈도 미명시).
- **bond 미배선 5**: DGS10/DGS2/FEDFUNDS/JGB(`fred_adapter.py` FRED_SERIES 미등록)·ETF가격 TLT/IEF/SHY(sleeve_returns 미적재). = 데이터 수집 게이트.
- 오배선 0: 유동성(NFCI/M2)·slope·MOVE rejected 정당차단(Y5/M3-M4 audit, L축 이중계상 방지).

## §5 미해결·실패 (삽질 방지)

- **배선 우선순위 판단**: A(eq_kr·eq_intl/reit=데이터완비 즉시) vs B(collector 필요) vs C(보류). eq_kr이 가장 큰 가치(rotation 2층 변별력 11%) + study 완비 → A 최우선.
- **eq_kr 배선 시 production core 경계**: sleeve_signals.py(stock/)·construction.py(stock/) 수정이 production 건드림 → off byte-identical opt-in(한국부호 추가해도 미주입 시 기존 ETF/EW fallback) 설계 필수. _bt_kr_picks(scripts/ 하네스)는 안전.
- **방어주 t-stat**: bo3yvytt9 결과 미수신. |t|<2면 신호부재 채택. EW>XLP는 defensive EW override 별도 측정 미완.
- **commodity/bond collector**: 외부 데이터(CME/EIA/BIS/FRED) 수집 = 코드만으론 안 됨. P8-B는 collector 작성 선행.
- **eq_us _sleeve_rotation**: 자문 폐기(predictive 소멸)라 배선 보류가 정당. 단 W3 defensive←real_rate와 factor 다름(_sleeve_rotation defensive←dollar) — 재배선 시 충돌 검토.

## §6 자문 종합 (방어주 종목선택 팩터, gemini+claude 3R)

- raw: `~/.claude/.gemini-web-last.md`(b5afpjv4x) / `~/.claude/.claude-web-basic-last.md`(b3nabupsc).
- **3자 수렴**: ① 밸류 −0.46%는 "역효과" 아니라 **신호 부재(claude: t≈−1, 0과 구별 안 됨)** — 밸류트랩 인과 불요. ② 밸류 프리미엄=경기·디스트레스 리스크 보상인데 방어 업종은 경기리스크 낮음="싸고 방어적"=형용모순(정상). ③ 디폴트=ETF 또는 **EW 바스켓**(claude: XLP 시총가중보다 49종 EW가 싸고 분산, 우리 실측 EW>XLP 정합). ④ 퀄리티-인컴(배당수익률×영업수익성)=**우리 DEF-2 interaction과 정확히 일치**(claude 강조), 단 ROE 금지(자사주매입 자기자본 왜곡). ⑤ n=36 과적합이라 백테스트로 팩터 못 고름 → 교체 근거는 외부증거·이론.
- **채택 검증(consult-adoption-gate, 진행중)**: t-stat(bo3yvytt9)로 "신호부재" falsify. EW>XLP는 defensive EW 경로 측정. 통과분만 ledger.
- **반영 방향**: 방어주 밸류 종목선택 OFF 유지(현행 ETF 정당) + DEF-2 퀄리티-인컴은 외부증거 기반 향후 + (검토)XLP→EW 바스켓.

## §7 파일 inventory (절대경로 D:/projects/Inv/)
- 측정: `scripts/run_multiasset.py`(_bt_us_picks:479/_bt_kr_picks:553/run_backtest:662, W6 universe alpha+t-stat 추가). 배선대상: `core/portfolio_decompose.py`·`stock/sleeve_signals.py`·`stock/construction.py`·`core/brain/regime_to_weights.py`(SLEEVE_AGG)·`core/data/factor_returns.py`·`core/brain/fred_adapter.py`.
- study: `study-research/{eq_kr,eq_us,crypto,gold,commodity,eq_intl,reit,macro,bond_cash}/study_session.yaml` + eq_kr/industries/_rotation/.
- 측정 로그: `.p4-w3-restore.log`(W3)·`.p4-w6-alpha.log`(W6 universe alpha)·`.p4-w5w6-final.log`·`.p4-defensive-cheapness.log`(etf_on=False)·`.p4-tstat-verify.log`(t-stat 진행중).
- subagent output 7: tasks/{a23829(gold)·af52855(eq_us)·ae8ba6(eq_kr)·a8fe60(crypto)·a195224(commodity)·a7798fa(eq_intl/reit)·a14c67(bond/macro)}.output.
- push·go-live·실주문 미접촉.
