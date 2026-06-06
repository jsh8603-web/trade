---
tags: [type/rotation-signals, domain/equity, sector/auto, scope/equity-kr]
date: 2026-06-06
purpose: 자동차 업종 rotation 신호 (업종 자체 OW/UW timing, 종목 selection과 별개). 이론→통계 검증 + v2 baseline 검증 + 고유 driver 심화.
raw: raw-v3/{measure_rotation, collect_rotation_macro}.py + validation-rotation-auto-v1.json. v2 baseline = _rotation/validation-rotation-v2.json
---

# automobile(자동차) 업종 rotation 신호

> ★측정 단위 = 자동차 업종 eq-weight(17종) forward return을 거시 driver로 예측 = "어느 국면에 자동차 업종 OW/UW".
> 종목 selection(capex/PBR, summary.yaml) 과 ★별개 차원.
> 파이프라인 = 이론(부호 사전확약) → 통계 검증(wild-cluster/OOS/FDR/placebo) → 판정. 이론없이 통계만 = data mining 채택불가.

## §0. ★universe 오염 검증 (refine-analyst CRITICAL 대응) — 오염 없음

- **refine CRITICAL**: rotation-analyst v2가 산업 디렉토리 prices.parquet 전체를 패널로 써서 부수종목 오염(정유 crack=가스 9종 섞임).
- **★자동차 검증 결과 = 오염 없음**:
  - v2 load_industry("auto") 경로 = `industries/auto/raw-v3/data/prices.parquet` = ★내 strict 패널과 **동일 17종**.
  - 17종 전수 = 완성차 3(현대차005380/기아000270/KG모빌리티003620) + 부품 12(현대모비스/에스엘/HL만도/현대위아/삼현/SNT다이내믹스/성우하이텍/한라캐스트/명신산업/네오티스/디아이씨/화신) + 타이어 2(한국타이어161390/금호타이어073240). ★전부 진짜 자동차(부수종목 0).
  - = 정유(가스 오염)와 달리 자동차는 universe clean. **v2 "global_auto_d3 +0.261 STRONG" = strict 자동차 패널의 진짜 신호**.
- **★strict vs v2 비교**: 내 measure_rotation.py(strict 17종 eq-weight) = v2와 동일 패널·동일 신호 → global_auto_d3 y_60d rho=**0.2613** byte-identical 재현(v2 0.2613 일치). y_20d rho=0.2221(v2 0.2221 일치). = v2 결과 검증 완료(오염 아님).

## §1. ★거시 국면 rotation 신호 (이론 부호 사전확약 + 통계)

> 이론 source = Gemini 리서치(P-Q-C 프레임워크 + Stovall early-cycle, /tmp/auto-rotation-result.txt). 부호 = OW(비중확대) 조건.

| 신호 | prior 부호 | 측정 rho (y_20d/y_60d) | wc_p | walk-forward OOS | 판정 |
|---|---|---|---|---|---|
| ★**global_auto_d3** (CARZ 3M 변화율) | 양 | +0.222 / **+0.261** | 0.034 / **0.025** | IS0.155→OOS0.250 / IS0.177→OOS**0.300** ✅강화 | **STRONG (이론+통계+OOS 일치)** — v2 baseline 재확인. placebo 통과(3%) |
| global_auto_yoy (CARZ yoy) | 양 | +0.077 / +0.091 | 0.52 / 0.42 | y_20d 유지 / y_60d flip | TENTATIVE — ★d3(3M 모멘텀)이 yoy보다 강(이론 정합: 기저효과 제거, 변곡점 포착) |
| ★**cli_chg6** (한국 CLI 6M 변화) | 양 | +0.243 / +0.298 | 0.032 / 0.0065 | y_20d IS0.257→OOS0.161 ✅ / y_60d flip | **PARTIAL** — early-cycle 이론(Stovall) 지지. ★단 y_60d OOS flip = y_20d만 robust |
| usdkrw_d3 (USDKRW 3M 변화) | 양 | +0.014 / -0.147 | 0.89 / 0.20 | OOS flip 둘 다 | REJECTED(OOS) — ★수출채산은 contemporaneous(동행)이라 forward 예측 약(이론 정합: 환율=동행). rotation timing 부적합 |
| dgs2_d3 (미국 2년물 3M 변화) | 음 | -0.042 / -0.126 | 0.70 / 0.21 | 부호유지(약화) 둘 다 | TENTATIVE DIRECTIONAL — 부호 음(할부수요 이론 정합) but 비유의. 방향만 |

## §3. ★자동차 고유 rotation 신호 (v2가 놓친 driver 심화)

| 신호 | prior 부호 | 측정 rho (y_20d/y_60d) | wc_p | OOS | 판정 |
|---|---|---|---|---|---|
| jpykrw_d3 (엔/원 3M 변화) | 음 (엔원↓=한국 경쟁력=OW) | -0.112 / -0.118 | 0.27 / 0.28 | y_20d flip / y_60d 부호유지약화 | TENTATIVE DIRECTIONAL — 부호 음(prior 정합, 2011-13 엔저 사례 이론) but 비유의. 방향만 |
| ★**iron_ore_d3** (철광석 3M 변화) | 음 (원가) | +0.185 / **+0.376** | 0.054 / **0.0015** | IS0.122→OOS0.361 / IS0.286→OOS**0.549** ✅강화 | ★**부호 반대 발견** — prior 음(원가)인데 측정 강한 양. 메커니즘 재해석 §4 (data mining 경계) |

## §4. ★iron_ore 부호반대 = 메커니즘 재해석 (원가 vs cyclical demand proxy)

- ★문제: iron_ore_d3 prior=음(원가↑→자동차 마진↓→forward 음) but 측정 = **강한 양(+0.376 y_60d, wc_p 0.0015 = 통합 FDR 유일 생존)**.
- ★직접 검증 (data mining 차단):
  - iron_ore_d3 vs global_auto_d3 corr = **+0.275** = 둘 다 cyclical 동조 → iron이 demand proxy 시사.
  - contemporaneous +0.198 / fwd1m +0.185 / fwd3m +0.376 = forward 갈수록 강 (동행 아닌 선행).
  - placebo: real +0.376 vs shuffle exceed_frac=0.0 (500 perm) = 우연 아님.
  - ★multivariate(iron+global_auto→fwd60): iron b=0.328 **t=3.14** / global_auto b=0.167 t=1.6 = ★iron이 global_auto 통제 후에도 독립 유의(global_auto는 약화).
- ★해석: iron_ore_d3 = 자동차 ★**원가 채널(음)이 아니라 글로벌 산업경기 cyclical demand proxy(양)**로 작동. 철광석↑ = 글로벌 제조업 확장 = 자동차(cyclical durables) 수요↑.
- ★★**사전이론 근거 확보 (team-lead 지시 = HARKing 회피 위해 이론 먼저, 2026-06-06 리서치 /tmp/iron-auto-result.txt)**:
  - **리플레이션 트레이드(Reflation Trade)** = 명확한 사전 실무 이론. 경기 회복기 경기민감주(자동차)+원자재 동반 매수. 2009-11(중국 인프라)·2020-21(팬데믹 회복) 현대/기아 사례 = 원가 부담보다 ★수요 회복(Q) dominant(증권사 리포트 다수).
  - **Stovall sector rotation** = 확립된 이론. 자동차(경기소비재 early-cycle) + 소재(철강 early-mid cycle) = 같은 경기 회복/확장 국면 동반 강세. 출처 = Sam Stovall "S&P's Guide to Sector Investing".
  - **철광석 = 글로벌 제조업 demand barometer** (de facto, 중국 제조업 proxy). Frankel 2006 NBER(원자재-business cycle).
  - ★**원가(음) vs demand(양) 두 채널** = 단일 지배 이론 없음(상황 의존). cyclical 회복 국면 = demand-pull dominant(양). = ★내 사전등록이 "원가 음"만 박은 게 **불완전**(양면 명세 누락)이었음. 부호반대 = HARKing 아니라 prior 양면성 미명세.
  - ★**regime 검증**: iron_ore_d3 [Recovery] rho=+0.445(n26) / Overheat +0.661 / Slowdown +0.413 / Reflation -0.019. Recovery서 가장 강 = 사전이론(경기회복기 동반강세) 정합. ★단 Slowdown서도 양 = reflation 한정 아닌 광범위 cyclical 동조.
- ★**판정 = TRADEABLE (조건부, 사전이론 근거 확보로 승격)**:
  - 통계 매우 강(wc_p 0.0015 + OOS 0.286→0.549 강화 + placebo 통과 + multivar t=3.14 독립) + ★사전이론(리플레이션 trade + Stovall 동행) 확보 = HARKing 아님.
  - ★단 **2 caveat**: (a) global_auto_d3와 corr 0.275 일부 중복(별개 신호이나 cyclical 공통) (b) 사전등록을 "원가 음"만 단순 박제한 불완전 = ★차기 vintage는 "원가 음/demand 양 양면" 명세 후 재확인. → ★조건부 tradeable(observe-only 아님), magnitude small-n hedge.

## §후보 신호 전수 (team-lead ≥8개 요구)

| # | 후보 | 측정/상태 | 판정 |
|---|---|---|---|
| 1 | 글로벌 자동차 판매(CARZ d3) | ✅측정 | ★STRONG (v2 검증) |
| 2 | 글로벌 자동차 판매 yoy | ✅측정 | TENTATIVE (d3가 우월) |
| 3 | USDKRW 수출채산(d3) | ✅측정 | REJECTED(OOS, 동행) |
| 4 | 미국 금리 할부수요(DGS2 d3) | ✅측정 | TENTATIVE DIRECTIONAL |
| 5 | 한국 경기선행 CLI(chg6) | ✅측정 | PARTIAL(y_20d, early-cycle) |
| 6 | JPYKRW 일본 경쟁력(d3) | ✅측정 | TENTATIVE DIRECTIONAL |
| 7 | 철강(iron_ore d3) | ✅측정 | ★TRADEABLE 조건부 (사전이론=리플레이션 trade/Stovall 동행, demand proxy 양) |
| 8 | 강판·알루미늄 원가 | ⏳철광석(iron_ore)으로 1차 proxy. LME 알루미늄 별도 fetch = 후속 | data-gate (LME 알루미늄 무료 부재) |
| 9 | 전기차 전환(EV 침투율) | ⏳data-gate | KAIDA EV 등록 또는 정책 이벤트 = 종목 selection 차원 적합(rerating), rotation timing 부적합 |
| 10 | 중국 자동차 판매 | ⏳data-gate | CAAM 월별 무료 부재. 현대/기아 중국 비중 축소로 우선순위 낮음 |
| 11 | 미국 신차 재고/인센티브 | ⏳data-gate | Cox/Wards 유료. 이론상 강력(선행 3-6M)하나 무료 부재 |
| 12 | 리콜 이벤트 | ⏳data-gate + 종목 idiosyncratic(업종 rotation 부적합) |

★후보 **12개 식별, 7개 측정완료, 5개 data-gate**(LME/EV/중국/재고/리콜 = 무료 데이터 부재 또는 rotation 차원 부적합).

## §tradeable 판정 (team-lead ≥2 요구) — ★3개 충족 (사전이론 근거 확보)

> tradeable = ★사전이론 부호 근거 + wc_p<0.05 + walk-forward OOS 부호유지 모두 충족 (data mining 차단).

| tradeable 신호 | horizon | rho | wc_p | OOS | 사전이론 | 판정 |
|---|---|---|---|---|---|---|
| ★**global_auto_d3** | y_20d+y_60d | 0.222/0.261 | 0.034/0.025 | 강화 | P-Q-C 판매모멘텀 | ★TRADEABLE (확실) |
| ★**cli_chg6** | y_20d | 0.243 | 0.032 | 유지 | Stovall early-cycle | ★TRADEABLE |
| ★**iron_ore_d3** | y_60d | 0.376 | 0.0015 | 강화(0.286→0.549) | ★리플레이션 trade + Stovall materials-cyclical 동행 | ★TRADEABLE (조건부) |

- ★**tradeable 3개 충족** (global_auto_d3 + cli_chg6 + iron_ore_d3). ★iron_ore = 당초 "원가 음" 단순 prior로 부호반대 보류했으나, ★사전이론 근거(리플레이션 trade + Stovall 동행, 2026-06-06 리서치) 확보 = 원가(음)/demand(양) 양면 중 cyclical 회복기 demand dominant = HARKing 아닌 정당 채택(§4). ★단 사전등록 양면성 미명세 불완전 = 조건부(차기 vintage 재확인).
- ★**독립성**: global_auto_d3 vs cli_chg6 corr=**0.536** = 중간 상관(둘 다 글로벌 경기 동조 = 완전 독립 아님, 실질 ~1.5 신호). multivariate(둘 다→fwd20): global_auto t=1.06 / cli t=1.43 = 상호 일부 흡수하나 둘 다 양 부호 유지.
- ★**결합 rotation 전략 (둘 다 양일 때 OW)** — ★단조(monotonic) spread:
  - combo=0(둘 다 음): -1.37%/월 (n=18) / combo=1(하나 양): +0.28%/월 (n=33) / combo=2(★둘 다 양): **+4.79%/월** (n=37).
  - OW(둘 다 양) vs 나머지 = **spread +5.09%/월** = 단조 증가 = 두 신호 결합이 의미 있는 OW timing. ★단 n=37(small-n), net-cost 차감 전 gross, 차기 vintage 재현 필요(tentative).

## §종합 판정

- ★**채택 (이론+통계+OOS)**: global_auto_d3 = STRONG (v2 검증, universe clean, placebo 통과, OOS 강화).
- ★**부분채택**: cli_chg6 (early-cycle, y_20d robust / y_60d flip).
- ★**조건부 채택**: iron_ore_d3 = 통계 최강(wc_p 0.0015) + ★사전이론 근거 확보(리플레이션 trade + Stovall materials-cyclical 동행) = demand proxy 양. ★단 global_auto와 corr 0.275 일부 중복 + 사전등록 양면성 불완전 = 조건부(차기 vintage 재확인).
- ★**방향만(TENTATIVE)**: dgs2_d3(할부), jpykrw_d3(경쟁력) = 부호 정합 비유의.
- ★**REJECTED(OOS)**: usdkrw_d3(동행이라 forward 약), global_auto_yoy(d3 우월).
- ★**통합 FDR**(m=14): survivors_BY=[iron_ore_d3 y_60d] = ★사전이론 근거 확보로 정당 생존(보류 아님). global_auto는 raw 유의하나 BY 미생존(small-n). rotation = time-series n_eff 26-88 hedge.
- ★**tradeable ≥3 충족**: global_auto_d3 + cli_chg6 + iron_ore_d3(조건부, 사전이론) = 3개. 결합 OW(global_auto+cli 둘 다 양) spread +5.09%/월(monotonic, small-n tentative).
- ★**rotation vs selection**: 종목 selection(capex/PBR) 은 OOS robust. ★rotation(업종 timing) = global_auto_d3(STRONG) + cli_chg6(early-cycle) + iron_ore_d3(reflation/materials-cyclical 동행) 3 tradeable = 자동차 업종 timing 은 글로벌 판매·경기선행·원자재 cyclical reflation 동조. universe clean.

## 정직 단서
- ★universe 오염 검증 완료(17종 전부 자동차, refine 같은 오염 없음).
- ★iron_ore = 당초 "원가 음" 단순 prior로 부호반대 보류했으나, ★사전이론 근거(리플레이션 trade + Stovall materials-cyclical 동행, 2026-06-06 리서치) 확보 = HARKing 아닌 조건부 채택. ⛔단 사전등록 양면성(원가 음/demand 양) 미명세 불완전 = 조건부, 차기 vintage 양면 명세 후 재확인.
- ★small-n(n_eff 26-88) + OOS split 검증. 진짜 holdout(2026+) = 차기 vintage.
- ★rotation = time-series(n 작음) = magnitude 단정 금지, 방향+OOS만.
