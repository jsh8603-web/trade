---
tags: [type/research-log, domain/equity, sector/auto]
date: 2026-06-05
purpose: 자동차 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용. (★자동차 산업만, _ledger-guide 양식)
---

# automobile(자동차) 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격(mom/rev/vol) | pykrx OHLCV 17종 1818일 | 기존 v3 prices.parquet 재사용 | ✅ | universe 17종(반도체 73·battery 26 대비 작음) = magnitude 과대 위험 최대 |
| PBR/PER | DART fnlttSinglAcntAll(equity/net_income) + 시총 | dart_financials.parquet(417 rows) 재사용 | ✅ PBR / per_z 무신호 | PER peak-EPS trap(자동차 = 대표산업). rcept_dt PIT |
| ★capex_ratio/inv/rnd | DART fnlttSinglAcntAll(재고/유형/무형자산) | collect_dart_extended.py 신규 수집(423 rows, coverage inv 0.92/ppe 0.97/intangible 0.95) | ✅ capex_ratio | ★cogs coverage 0.26(매출원가 계정명 불안정) — 무시하고 자산 계정만 사용 |
| regime(Macro/KRW/flow) | FRED CLI/DEXKOUS + ECOS 외국인순매수 | ★반도체 regime_labels.parquet **시장공통 재사용**(재수집 불필요) | ✅ | regime = 시장 전체(종목무관) → 반도체 산출 복사. 분포 Macro[Slow31/Rec26/Refl22/Over10]×KRW[neu41/weak38/str10]×flow[neu48/sell22/buy19] |
| 글로벌 자동차 수요 | yfinance CARZ/SLX | 기존 v3 측정(contemporaneous +0.22 유의, forward 부재) | ❌ REJECTED as alpha | 동조>예측 = RegimeGlasso Ω 흡수 |
| 미국 SAAR | FRED TOTALSA | 미수집(종목 cs 아닌 산업 timing) | ⏳이연 | 반도체 PPI 자리 = 자동차 SAAR. regime 변수 후보 |
| 종목레벨 외국인 flow | KRX 종목별 net buy | ★인증 차단(pykrx KeyError) | ⏳DATA-GATE | 시장레벨 regime(ECOS)은 측정완료. 종목 cs-signal 은 차단 |

## 막힘·해결 로그 (시계열)

- [2026-06-05 08:20] 진입 점검: 기존 6/3 auto 산출물(summary.yaml 20KB/measure.py/validation-*) 발견 → 진단: v3 **unconditional cross-sectional**(momentum 비유의 / PBR primary / PER peak-EPS)만 측정, ★conditional IC surface(36셀×horizon) = 미측정 = dispatch 본체 누락 → 해결: 기존 v3 부분활용(prices/dart/PBR-PER 검증 결과는 비판검토용으로 보존) + conditional IC 신규 측정 → 교훈: "기존 산출물 = 축 다름(v3 cross-sectional ≠ conditional surface). 점검 후 본체부터".

- [2026-06-05 08:29] regime 데이터 부재(auto/raw-v3/data 에 regime_labels.parquet 없음) → 진단: collect_regime.py 미실행 → 해결: ★regime = 시장 전체(종목무관) = 반도체 regime_labels/series.parquet 그대로 복사(재수집 불필요, FRED/ECOS 동일) → 교훈: "regime 라벨은 시장공통 = 산업 간 재사용. 12산업 각자 재수집 불필요(API 부하 절감)".

- [2026-06-05 08:35] WebSearch 차단(research.block hook) → 진단: WebSearch/WebFetch 기본 차단, Gemini API 권장 → 해결: gemini-search.js pro 로 자동차 cycle 이론 6질문 리서치(free key 429 → promo fallback, 8241 chars 산출) → 교훈: "native WebSearch 금지 환경. gemini-search.js 경유".

- [2026-06-05 09:10] measure_oos.py I/O error("operation on closed file") → 진단: measure_conditional.py import 시 `sys.stdout = io.TextIOWrapper(...)` 가 stdout 재설정+close → 재import 후 print 불가 → 해결: import 후 `sys.stdout = io.TextIOWrapper(io.FileIO(os.dup(1),"w"),...)` 로 fd 1 직접 재개방 → 교훈: "module-level stdout wrap 하는 .py 를 import 하면 stdout 닫힘. os.dup(1) 로 복구".

- [2026-06-05 09:30] ★핵심 발견: walk-forward OOS 측정 결과 가격신호 cell 대부분 FLIP → 진단: 자동차 momentum = volume cycle(점진) = in-sample artifact, OOS 부호 불안정 → 해결: 가격신호 REJECTED(OOS) 박제 + PBR/capex(OOS robust)만 채택 → 교훈: "★unconditional 약 + conditional 유의해도 OOS flip 이면 무효. walk-forward OOS 가 in-sample artifact 거름망. 반도체는 OOS 유지였으나 자동차는 flip = 산업별 다름".

- [2026-06-05 09:45] ★핵심 발견: capex_ratio(asset growth) = 자동차 진짜 신규 신호 → 진단: 반도체는 신규지표 무신호(ppe_yoy TENTATIVE만)였으나 자동차 capex_ratio = wc_p 0.0015 + OOS 강화 + 통합 FDR 생존 → 해결: capex_ratio 채택(PARTIAL CONFIRMED OOS robust) → 교훈: "★자동차 = 자산집약 장치산업 = asset growth anomaly 강. 산업별 신규지표 차등(반도체 ASP cycle vs 자동차 capex cycle)".

- [2026-06-05 ~01:00] ★G-C 독립 audit 충실 PASS(hard-fail 0). capex survivors=5=진짜(LOO 17종 전부 음 + PIT-safe + size 독립 3중 검증). team-lead remediation 2건(결론 불변, hedge 강화) → 진단+해결: (1) survivors 5개 wc_p 전부 0.0005 = wild-cluster floor(1/(B+1)=1/2001) censored → 검증(merge_fdr json 직접 확인, 5개 동률) → "반도체/battery survivors=0보다 강" = 방향성 우위만 맞고 magnitude 비교는 floor-censored 라벨 추가(meta.floor_censored_caveat). (2) capex/pbr y_60d AR(1)≈0.43-0.49(60d 중첩) → eff-N 보정 측정(measure_neff_label.py): capex t_naive=-3.61→t_eff=-2.52, pbr -3.72→-2.40 = ★여전 유의 → eff-N 보정 라벨 병기(effective_n_label) + tier=structural_prior_high_confidence(validated alpha 단정 보류) → 교훈: "★wild-cluster survivor wc_p가 floor면 magnitude 비교 금지(생존 여부만). ★60d 중첩 IC t는 eff-N 보정 의무(AR1 강하면 naive t 과대). 결론(유의 여부) 불변, hedge 강화".

## 측정 방법 결정 로그

- **conditional IC**: measure_conditional.py(반도체) universe-agnostic(universe.parquet pass_floor 자동) → 코드 복사만, 자동차 데이터로 실행. 36셀 full N≥24=0 → 단일축(Macro4/KRW3/flow3) 측정 + 2축 merge=supervisor.
- **wild-cluster bootstrap**: ★small-block asymptotic NW-HAC t = size-invalid(Kiefer-Vogelsang) → Rademacher B=2000 per-cell p. asymptotic t 참고만(G-F §7).
- **walk-forward OOS**: IS 2019-22 / OOS 2023-26 split(team-lead 의무). 진짜 holdout 아님(2026+ = pristine OOS, flip-register). 부호+magnitude 유지 = in-sample artifact 판별.
- **단일 FDR family**: ★측정 前 멤버십 사전고정(6신호×3h×regime cell). 통합 merge(merge_fdr_family.py): cond 90 + fund 78 = m=168 survivors=5. garden-of-forking-paths 차단.
- **size-orthogonal(Q6)**: Fama-MacBeth 1973 month-by-month rank 회귀(ret~pbr+capex+size). ★자동차 size factor 도 유의(t=-2.2~-2.5) = small-cap effect 공존 정직 명시(capex 독립 t=-3.38 유지).
- **family_2 interaction**: pooled panel month-clustered SE(rejected 박제 前 G-B 의무). mom_12_1/vol_60 KRW_weak 유의(t=2.18/2.75) but 부호 양(반도체 reversal 음 증폭과 반대) + OOS flip = 보류.

## 측정 결과 요약 (정직 박제)

| 신호 | unconditional | best conditional | walk-forward OOS | verdict |
|---|---|---|---|---|
| 가격(mom/rev/vol) | 비유의 | KRW_weak interaction 유의(t=2.18/2.75) | ★대부분 FLIP | REJECTED(OOS) |
| ★PBR value (y_60d) | IC=-0.108 | Slowdown wc_p=0.0005 | IS-0.108→OOS-0.117 ✅ | PARTIAL CONFIRMED(OOS robust) |
| ★capex_ratio (y_60d) | IC=-0.103 wc_p=0.0015 | Recovery/neutral 생존 | IS-0.044→OOS-0.172 ✅강화 | PARTIAL CONFIRMED(OOS robust, 신규) |
| PER | IC≈0 (wc_p=1.0) | — | — | INSUFFICIENT(peak-EPS trap) |
| 통합 FDR | m=168 survivors=5 | pbr 2 + capex 3 | — | ★반도체(0)보다 강 |

## 미해결 / 다음 세션 우선 작업

1. **EV-EBITDA 측정** (cyclical primary_metric) — DART 영업이익+감가상각 재구성. PBR·capex 진짜신호 입증되어 우선순위 일부 완화되나 archetype primary 보강 의무.
2. **미국 SAAR(FRED TOTALSA) fetch** — 자동차 고유 timing 변수 = regime conditioning. 반도체 PPI 자리.
3. **현대차/기아 LOO** — PBR·capex 대형주 의존 점검(특히 capex의 size collinear 분리). size-bucket 내 IC.
4. **종목레벨 외국인 flow** — KRX 인증 또는 증권사 API unblock 시 (현 DATA-GATE).
5. **PIT universe 멤버십** — 쌍용차→KG모빌리티 등 생존편향 보정(I축 PARTIAL).
6. **차기 vintage(2026+) pristine OOS** — flip-register cell 재현 점검 + PBR/capex OOS robust 재확인.
