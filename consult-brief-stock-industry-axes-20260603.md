---
tags: [type/consult-brief, domain/inv, scope/equity-industry-dispatch]
date: 2026-06-03
purpose: claude-web + gemini-web 병렬 외부검토 brief — 산업 섹터 dispatch 양식 v3 (coin 측정 15종 + cross 3종 + 15축 audit). 과잉/과소 설계 점검.
---

# 외부검토 brief — 주식 산업 섹터 dispatch 양식 v3

> 페르소나: 멀티에셋 퀀트 리서치 디렉터. 코드어 0, 방법론·통계 타당성에 집중.
> ★검토 **제외**(확정 사항, 재론 불필요): 산업 분류 체계(미국 Mag7+macro-sleeve / 한국 12산업 = 다회차 외부검토 확정 결과물).

## §1. 맥락

Inv = 멀티에셋 동적가중 시스템(주식/코인/금/채권/원자재/매크로). 투자 가정을 yaml 7블록으로 박제 → 런타임 카드로 소모. 가정이 깨지면 e-CUSUM(anytime-valid)으로 청산하는 결정론 로직 보유.

**주식 트랙 = 산업(섹터)별 study가 1차 작업 단위.** 각 산업 subagent가 "이 산업 종목 forward return과 가장 상관 높은 지표가 무엇이고, 어떤 조건(regime·cycle)에서 강해지나"를 실측 분포 + 게이트로 채운다. 산출 = 산업별 self-contained capsule(summary.yaml + validation-*.md + **15축 audit**).

## §2. 뼈대 + 인프라 현황 (이미 있는 것)

- ★**진짜 척추 = `archetype.py` 5종 archetype**(cyclical / event_driven / spread_driven / asset_stable / compounder + commodity/crypto 변형). 코인·원자재·주식을 **하나의 추상으로 통일** — 각 archetype = primary_metric(싸다의 척도) + value_trap_guards + cycle_drivers, valid_from 시변(예: 엔비디아 cyclical→compounder). 산업 배정 단위 = 이 archetype.
- **측정 파이프라인 = coin 트랙이 먼저 정교화한 방법론 15종**(아래 §3 C1).
- **RegimeGlasso**: 거시국면별 조건부 상관 학습(nonparanormal + EBIC graphical lasso + EB shrinkage + belief-mix). SOTA 수준 — "산출만 한다, weight 주입은 별 단계".
- **derive_weights**: Grinold w∝Ω·IC + 1/N 블렌딩(DeMiguel) + capped-simplex. SOTA 충분 판단(보강 = z-score 1/N baseline ablation만).
- **weight_falsification**: e-CUSUM anytime-valid 청산. 산업↔측정 결선 완료(panel-score-IC 축, dead-hook 활성).
- 외부 레퍼런스(차용 후보): ai-hedge-fund(valuation 수식 — 일부 차용 완료) / Ken French FF5(factor) / Damodaran·French49(cheapness 데이터). ⚠️ 분류 taxonomy 소스로는 미채택(우리 분류 확정).

## §3. 검토 질문 (C1~C5)

### C1. 측정 방법론 15종 — 주식 이식 시 과잉/과소?
coin이 신호 1개에 적용하는 측정 방법론 = **15종**: ① Rank-IC(횡단면 Spearman) ② horizon sweep ③ cross-asset 재현 ④ regime 4게이트(G1 ex-ante / G2 Bonferroni·FDR / G3 walk-forward OOS / G4 Newey-West HAC) ⑤ leave-episode ⑥ within-period sub-split ⑦ partial-corr(공통원인 통제) ⑧ placebo(반증조건 사전등록) ⑨ effective-N tier(autocorr 보정) ⑩ net-cost ⑪ e-process(e-CUSUM) ⑫ block-bootstrap ⑬ within-family neutralize(FF5 직교) ⑭ cross-asset family ⑮ intraday.
- 주식 적용 = **14종 그대로**, **intraday(⑮)만 제외**(코인 1-6h microstructure는 주식 일중 체결구조와 다르고 우리는 일봉만 수신).
- net-cost는 0.30%→0.03%/side(기관), 다중검정은 Bonferroni→**FDR 우선**(주식 약신호 power 보존)으로 파라미터 조정.
- **질문**: 14종 이식이 과잉인가(주식엔 불필요한 게 더 있나)? 과소인가(주식 특유로 추가할 축 — 예: 회계 발생액 품질, 실적 서프라이즈 drift, 유동성/사이즈 조정)? intraday 제외가 옳나?

### C2. cross = 분석 단위 간 상관 — 분담 설계가 PSD·이중계상 막나?
cross 정의 = **분석 단위 간 상관**: (i) 다른 산업군 간 (ii) 다른 자산(금·채권·코인) 간. 코인 btc-eth 상관과 동형. within-industry 아님. 측정 3종:
- (a) 동시 상관(RegimeGlasso, 보유) (b) 방향성 spillover(**Diebold-Yilmaz connectedness**, generalized VAR FEVD — 신규) (c) 구조 linkage(**customer-supplier momentum** Cohen-Frazzini 2008 + **I-O centrality** Acemoglu 2012 — 신규).
- 분담: 산업 subagent = 자기 산업 공통인자 exposure β(VIX/dollar/oil/rate/credit) 보고 + DY/customer 선행신호 후보 보고. **통합 단계에서 cross 조립(1회 계상, PSD eigh-floor, L축)**. 산업이 직접 cross 최종 박제 금지(이중계상 차단).
- **질문**: 이 "산업=exposure 보고 / 통합=조립" 분담이 정말 PSD 위반·이중계상을 막나? DY connectedness + customer momentum이 RegimeGlasso(동시 상관)가 못 잡는 방향성·구조를 더하는 게 정당한가, 과잉인가?

### C3. forward alpha 부재 전제 — 주식에도 성립?
코인 교훈: cross-asset forward lead-lag 거의 전멸, contemporaneous risk-on/off가 dominant(11 PoC 중 1만 생존). → 우리는 "forward IC 약하면 단독 베팅 근거 X, contemporaneous risk monitor + valuation mean-reversion 중기 + event-driven으로 격하" 전제.
- **질문**: 이 forward-alpha-부재 전제가 **주식에도 성립**하나? 아니면 주식은 코인과 달리 (모멘텀·실적 drift·valuation 평균회귀로) forward IC가 살아있어, 산업 study가 forward 예측을 더 적극 추구해야 하나? 어느 horizon(1M/3M/6-12M)에서 주식 forward alpha가 실재하나?

### C4. 주식 6조정 타당성
coin→equity 이식 시 6개 조정: ① regime = macro-driven(inflation/VIX/curve/외국인flow, coin은 sentiment) ② intraday 제외 ③ net-cost 0.03%/side ④ 다중검정 FDR 우선 ⑤ family neutralize = FF5 자동화 ⑥ cross-asset family pool = FF5 6factor(MKT/SMB/HML/RMW/CMA/MOM).
- **질문**: 특히 ④ FDR 우선(Bonferroni 대신)과 ③ net-cost 0.03%가 타당한가? 한국 시장(거래세 0.18~0.23% + 외국인 수급)은 별도 조정이 더 필요한가?

### C5. 뼈대 vs 외부 차용 — 어디가 우월?
원칙: 뼈대 = 우리것(coin yaml 7블록 + 4게이트 + e-process + archetype.py 5종 척추 + RegimeGlasso + derive_weights). 외부는 **우월할 때만** 차용하고 **우리 데이터로 작동 검증** 후 박제.
- **질문**: 어느 외부 요소가 정말 우월해서 차용이 정당한가(ai-hedge-fund valuation 수식? FF5 factor 표준? skfolio CPCV? toraniko?)? 어디는 우리것이 이미 동등/우월해서 차용 불필요한가? archetype.py 5종 추상으로 주식 산업을 배정하는 게 GICS/French 같은 표준 분류 대비 타당한가, 아니면 한계가 있나?

## §4. 원하는 답

C1~C5 각각: (a) 내 전제·설계의 결함/반박 (b) 학술·실무 근거 (c) **dispatch 양식 v3에 추가/수정/삭제할 구체 항목**. 핵심 판정 = "새 레이어 추가 vs 기존 인프라 재사용" + **과잉설계 경계**(속도보다 퀄리티지만, 안 쓸 축을 넣는 것도 비용). 분류 체계는 확정이라 답하지 말 것.
