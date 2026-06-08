---
next-action: "eq_kr 12산업 배선(★데이터 완비·_KR_SUB 등록만 누락 실증): (1)_KR_SUB 7→12 확장(semiconductor/steel/aitech/refining/telecom 추가)+_KR_ETF_PICKS 5섹터 ETF 또는 EW fallback (2)sleeve_signals 한국부호 추가(study yaml 근거, ⛔미국식 cheapness 임의정의 금지) (3)_bt_kr_picks rotation 배선(분기 3M 리밸런싱, study active 1M평가 버그 회피) (4)백테스트→robust selection(semi/steel/aitech)+rotation alpha 실측. 이후 vol 미배선 candidate(vix_level/vix_term/macro_vol_transfer) 배선/측정. ⛔production stock/ 무단변경+off=byte-identical opt-in+go-live 미접촉."
session: btn-Inv (opus, long-mode ON2 750k)
date: 2026-06-08
tags: [type/handoff, topic/rotation-vol-kr12, domain/multiasset, tier/study-runtime]
related: cross-regime-ledger.md, indicator-ledger.md, .consult-rotation-brief.md, handoff-wiring-gap-20260608.md
---

# handoff — rotation 폐기·vol 생존·eq_kr 12산업 배선 (2026-06-08)

> ★이번 세션 핵심: (a)방어 종목선택 ETF우월 확정 (b)rotation 예측 폐기(US 신호0/KR 신호실재+구현버그) 자문 3R 수렴 (c)vol은 risk로 생존 (d)★eq_kr 12산업 데이터 완비·등록만 누락 실증 → 즉시 배선 경로 확보. 커밋 34aed37(코드)·02784ae(문서).

## §1 현재 상태 · 첫 행동

**현재 상태**: 방어/cyclical/rotation 진단·자문·ledger 완료. eq_kr 12산업 배선 경로 확보(데이터 완비 실증). 커밋 2건. push·go-live 미접촉.

**첫 행동(재개)**:
1. `_KR_SUB`(run_multiasset.py:364) 7→12 확장: `["financial","battery","bio","shipbuilding","consumer","chemical","auto"]` + `["semiconductor","steel","aitech","refining","telecom"]`. `_KR_ETF_PICKS`(:365)에 5섹터 ETF 추가 또는 `_ETF_FALLBACK_ROUTING`로 EW.
2. `stock/sleeve_signals.py` SLEEVE_SIGNS에 한국 섹터 부호 추가(study yaml 근거 — eq_kr selection IC 부호). ⛔미국식 cheapness 임의정의 금지(study가 섹터별 다른 신호).
3. `_bt_kr_picks` rotation 배선: 분기(3M) 리밸런싱으로 `_sleeve_rotation_kr.build_weights` 비중 주입. ★study active 1M평가 버그 회피(아래 §4-3).
4. 백테스트 재측정 → robust selection(semi/steel/aitech) + rotation alpha 실증. off=byte-identical opt-in(인자 None이면 기존 ETF/EW).

## §2 진행 맵

- **Task #1 방어 종목선택** ✅완료: ETF/EW 우월 확정.
- **Task #2 rotation 3R 자문** ✅수렴(예측폐기/base+동시/연구 사용처강등). 단 KR은 신호 실재+구현버그 발견으로 별도(아래).
- **Task #3 P8-A**: eq_kr 12산업 배선 경로 확보(데이터 완비). eq_intl/reit=SLEEVES 신설 사용자 결정.
- **Task #4 quality 구현 개편** ✅완료: ttm+tercile+12M도 약팩터라 음수, ETF 확정.

## §3 사용자 박제 (대화 고유)

1. **12개 vs 7개 의문**(★이번 세션 핵심): 백테스트 `_KR_SUB`=7섹터지만 study 디렉토리·데이터는 12산업 완비. production은 `krx_universe.py`(KRX 전체). → 백테스트만 sector별 7개 등록 누락(근거 주석 없음=단순 버그), 데이터 부재 아님. 5섹터 추가=즉시 배선.
2. **vol 살릴 신호 파악**: rotation(1차 모멘트=수익예측) 죽었지만 vol(2차 모멘트)은 예측가능→risk로 생존(§4-4).
3. **자문 무비판 금지**: study verdict("ROTATION_ACTIVE"=active share 기준 ≠ OOS 수익) 무비판 배선 금지. 횡단면/시계열 IC 구분·horizon 정합·cost 점검(promo-log K 2026-06-08).
4. **불변식**: production core/stock 무단변경 / off=byte-identical opt-in / push·go-live·실주문 미접촉 / 안전장치값 무단변경 금지 / ⛔폐기 금지(study 산물=사용처 강등).
5. **미국≠한국 결정적**: 미국 rotation 신호 자체 0(폐기 정당), 한국 신호 실재(구현 버그).

## §4 측정 데이터 (★핵심 — 다음 세션이 재측정 없이 인용 가능)

### §4-1 eq_kr 12산업 데이터 완비 실증 (12/12 로드 성공)
`_bt_load_kr` 12산업 전부 prices(1818일, 2019-01~2026-05)+universe 완비. **누락 5섹터**: semiconductor(189종)·steel(59종)·aitech(281종)·refining(16종)·telecom(77종). 등록 7섹터: financial(72)·battery(84)·bio(185)·shipbuilding(31)·consumer(211)·chemical(22)·auto(113). 데이터 파일: 각 `study-research/eq_kr/industries/{섹터}/raw-v3/data/{prices,universe,dart_financials,amount,common_factors,regime_*}.parquet`. ★등록 누락만 = `_KR_SUB`+`_KR_ETF_PICKS` 확장으로 즉시 12산업.

### §4-2 rotation 진단 — US vs KR 결정적 차이
- **US `_sleeve_rotation`**: predictive(1M)·active(1M) horizon 정합. 1M β−0.0006(t−0.31)/3M β−0.00297(t−0.58)/횡단면 1M 0.04·3M 0.0 = **1M·3M·횡단면 다 신호 0 = 진짜 신호부재**(폐기 정당). 변별력 안 키움(STATIC, 정직). AXIS: cyclical←baa_aaa(−)/defensive←dollar(+)/mega←real_rate(−).
- **KR `_sleeve_rotation_kr`**: 신호 실재 — 시계열 forward3M IC 평균 **0.231**(chemical 0.422/steel 0.347/refining 0.30), **횡단면 IC(Zcs vs fwd3M)=+0.086 t2.04 유의**(raw X +0.114 t3.33). 단 study OOS active IR=**−0.071**(음수).

### §4-3 ★KR active −0.071 = study 코드 버그 (사용자 "코드를 study와 다르게" 정확)
원인 2개: (a)**horizon mismatch** — `_sleeve_rotation_kr.py:236` active=`(w−base)@R.loc[nxt]`=**1M 수익**인데 신호는 3M 예측 → 1M active IR 0.056 vs **3M active IR +0.175**(3배). (b)**cost+hysteresis** — 한국 STT(매도세 0.18~0.23%) 매월 회전 잠식, cost 제외하면 1M도 +0.056. ★자문 IR 추정 0.18~0.25 ≈ 3M active 0.175 일치(consult-kr-rotation-variability C7). ⚠️ portfolio active t=0.59(비유의, n=63 소표본): 신호 방향 양수나 변별력 약 prior. 배선=분기(3M) 리밸런싱+cost절감.

### §4-4 vol 살릴 신호 (ledger 전수 정독 — rotation과 달리 생존)
- **adopted(배선)**: vol factor 공분산(cross +0.6~0.8: eq_cyc↔intl/reit/defensive, defensive vol β−0.660, SEED vol cell+FACTORS 7)·realized_vol(sleeve별 0.04~0.08)·**vix_beta 0.18**·cross_sector_mean_corr 0.05·**target_vol=0.15**(engine gross clip 배선).
- **candidate(미배선, 살릴 수 있음)**: **vix_level**(Tang-Xiong 2012 VIX급등→delevera throttle)·**vix_term_structure**(vol regime)·**macro_vol_transfer**(crypto S6 15축 CONFIRMED throttle-only VIX carrier)·gold_realized_vol·vix_proxy.
- **reject**: gold vol β:=0(gold만, NW p0.077)·MOVE/slope covariance(joint VIX 흡수, bond sleeve 편입 시 부활)·VIX regime split(L축 이중계상 게이트).
- ★**핵심**: vol=alpha 아닌 **risk(공분산/sizing/throttle)**로 생존. vol carry/vrp=crowding 무알파(crypto vrp_funding rejected). **L축 불변식**: VIX 공통인자=corr_prior 1회 계상(cross-corr·VIX-regime 추가 wire 금지).

### §4-5 eq_kr selection (3층 종목선택)
robust(BY생존+ρ≥0.25): **semi(cs_pbr_z_24m IC−0.114, N_eff53, ρ0.34)·steel(mom_12_1_reversal IC−0.181, ρ0.27)·aitech(cs_pbr_z IC−0.183, ρ0.26)**. 나머지 9곳 ρ<0.25 약, refining 불가. ★in-sample IC robust(OOS+실측경로 미검증). ⚠️미국 defensive 교훈(약팩터는 capped-EW에서 죽음) — semi(universe 189종, 강)만 가치. within_industry_residual_kr.py + validation-within-residual-v2.json.

### §4-6 defensive/cyclical 종목선택 (Task #1·#4 확정)
- **defensive=ETF/EW 확정**: study-정의 forecasting(ttm+sector-neutral+tercile, n=65)은 value t+3.33/DEF-2 quality(div×op_prof) t+3.41 유의지만, 실측 경로(_bt_us_picks, 6M/12M)는 음수 — 약팩터(net_iss/ep marginal·DEF-2 incremental+0.065)가 합성 composite+capped-EW(cap5%/floor$500M/히스테리시스/trap-veto) 못이김. ttm+tercile+12M+sector-neutral 다 적용해도 t−1.06.
- **cyclical=직접선택 채택**: cross-sector value(pbr/ev_ebitda) 분기/6M/12M 전부 양(+26.8% ann at 12M, t+1.96~2.25). sector-neutral 미적용(cross-sector가 alpha원). `_bt_us_sectors`=defensive 한정.

## §5 미해결·실패 (삽질 방지)

- **KR rotation portfolio 약**: 횡단면 t2.04 신호 실재나 portfolio active t0.59(n=63 소표본 비유의). 배선해도 미국 defensive처럼 capped 처리서 미미할 위험 → 배선 후 분기 백테스트 재측정 필수(게이트).
- **KR selection 미실증**: robust 3곳 in-sample IC만, 실측 경로(capped-EW) 미검증. semi 우선.
- **defensive quality 실패 확정**: 구현 개선(ttm/tercile/12M) 다 해도 음수. 약팩터 본질. 재부활=신규 강팩터.
- **eq_intl/reit DEFERRED**: SLEEVES(배분 차원) 신설=사용자 결정(go-live 인접).
- **production 한국 경로 미확인**: 백테스트=_KR_SUB sector별, production=krx_universe 전체. production이 sector 분해 selection 쓰는지 다음 세션 확인(stock track 경로).

## §6 자문 종합 (rotation 3R, gemini+claude 수렴)

raw: ~/.claude/.gemini-web-last.md + ~/.claude/.claude-web-basic-last.md. 브리핑: .consult-rotation-brief.md.
- **3자 수렴**: ①예측형 거시 rotation OOS 죽음=교과서(claude: Goyal-Welch2008 OOS실패·Asness2016 factor timing=숨은밸류·DeMiguel2009 1/N도 못이김). 2차 모멘트(vol)는 예측되나 1차(수익) 안 됨. ②base만(예측 tilt=엣지없는 tracking error). ③동시(contemporaneous)>>예측(US 부호뒤집힘 동시+0.0012/예측−0.0006=동시 리프라이싱 지문). ④⛔폐기금지 해소=**연구 사용처 강등**(예측 tilt 입력→동시 상태/레짐 컨텍스트). ⑤극단치 조건부(|z|≥1.5~2)=레짐 오버레이만.
- **변별력 키우기 실측 근거**(consult-kr-rotation-variability C7/C8/C51): "breadth3.5+IC0.2~0.4→IR0.18~0.25" 공식, "변별력(active share)≠TE/IR" 분리, "30% 천장초과 불가 정직전달". 억지 아님.
- **채택(consult-adoption-gate)**: US=예측 폐기 유효(신호0). KR=신호 실재(구현 버그)라 자문의 KR 부분(OOS−0.071 기반) 무효 → 구현 fix 후 배선.

## §7 파일 inventory (절대경로 D:/projects/Inv/)
- 측정 스크립트(.gitignore .p4-*): `.p4-defensive-quality.py`(forecasting)·`.p4-sector-pipe-verify.py`(파이프)·`.p4-kr-xsec.py`(횡단면 IC)·`.p4-kr-active.py`(1M vs 3M)·`.p4-us-horizon.py`(US 1M/3M)·`.p4-kr-contemp-ic.py`.
- 배선 대상: `scripts/run_multiasset.py`(_KR_SUB:364/_KR_ETF_PICKS:365/_bt_kr_picks:553/_bt_us_sectors/_bt_add_def_quality)·`stock/sleeve_signals.py`(SLEEVE_SIGNS 한국부호)·`stock/cross_sectional_selection.py`(tercile_enabled)·`study-research/eq_kr/industries/_rotation/_sleeve_rotation_kr.py:236`(active 1M평가).
- study: `study-research/eq_kr/study_session.yaml`+industries/_rotation/(_sleeve_rotation_kr·within_industry_residual_kr·rotation-study_session.yaml).
- ledger: `study-research/_wire/cross-regime-ledger.md`(rotation/defensive/cyclical 행)+`indicator-ledger.md`(vol 신호).
- 커밋: 34aed37(코드 11파일)·02784ae(문서 7파일). push 미접촉.
