---
tags: [type/rotation-signals, domain/inv, scope/equity-kr, sector/chemical, topic/industry-rotation]
date: 2026-06-05
owner: chem-analyst@kr-equity (opus 1m)
purpose: 화학 업종 자체 rotation timing 신호 (어느 국면 → 화학 OW/UW). 종목 selection capsule과 별 차원. 이론(증권 리서치)→통계검증→판정.
---

# 화학(chemical) 업종 ROTATION 신호 — 업종 비중 timing

> **임무** = "어느 국면에 화학 업종 비중↑↓" = rotation timing (업종 eq-weight 시계열 forward 예측).
> 종목 selection(summary.yaml = 화학 안 어느 종목)과 **별 차원**. _rotation v2 baseline(naphtha) 심화.
> 파이프라인: 이론(증권 리서치) → 통계 검증 → 판정 (이론+통계=채택 / 이론없이 통계만=data mining 불가).

## 0. ★이론 부호 사전확약 (데이터 접촉 前 동결)

- **naphtha_yoy → forward: 음(-)** [cost-push: 납사 원가↑→마진↓→비중↓]
- **china_demand(FXI/MCHI yoy) → forward: 양(+)** [demand-pull: 중국 전방수요↑→화학↑]
- **spread(china demand − naphtha cost) → forward: 양(+)** [margin = 수요 전가력 − 원가 부담]
- ★**team-lead 가설**: naphtha 단독(v2 -0.367 cost-push)보다 China demand 또는 spread(margin)가 본질.

## 1. ★이론 검증 (증권 리서치 — 이론을 통계가 검증)

> Gemini Pro 종합(2026-06-05) + 증권사 컨센서스. theory-notes §1·§3 보강.

증권사 컨센서스 (키움 이동욱 / NH 윤재성 / 신한 이진명) = **명확히 "중국 수요(demand-pull)가 본질"**:
1. **본질 = 중국 수요**: 글로벌 석유화학 ~40% 소비하는 중국 수요가 제품(에틸렌)가격 = 사이클 방향 결정. 키움 이동욱 "화학 시황 본질은 수요, 중국 실물경기 회복 확인돼야 반등".
2. **나프타 = cost-push (변동성, 방향 못 바꿈)**: 유가에 100% 연동 외생변수. NH 윤재성 "유가 상승이 중요한 게 아니라 원가를 판가에 전가할 수 있는 수요 환경이 핵심".
3. **스프레드(마진) = 통합 지표**: "수요 전가력 − 원가 부담" 결과물, 주가와 가장 직접 연동. 수요 강하면 유가↑여도 전가 가능(2016-17 슈퍼사이클) / 수요 약하면 유가↑ = 마진 급락(2022 하반기).
4. **rotation 실무 규칙**: 중국 PMI>50 상승 + 부양책 + 스프레드 BEP($250-300/톤) 상회 = OW / 중국 PMI 하락 + 긴축 + 스프레드 피크아웃 = UW.

## 1-bis. ★strict universe (화이트리스트, 디렉토리 전체 금지)

- **full = 17종 명시 화이트리스트** (석유화학 commodity + 정밀/스페셜티, 화장품/반도체소재/2차전지/정유 ⛔제외). KSIC/키워드 디렉토리 매칭 금지(frame M.11 교훈).
- **★strict NCC 코어 = 6종** = LG화학(051910)·롯데케미칼(011170)·한화솔루션(009830)·금호석유화학(011780)·대한유화(006650)·이수화학(005950) = 순수 NCC 석유화학(신사업·정밀화학 제외). robustness 대조용.

## 2. ★통계 검증 — 후보 8개 + strict NCC robustness (이론과 일치)

> raw: `raw-v3/rotation/measure_chem_rotation_v2.py` → `validation-chem-rotation-v2.json` (+ v1 = naphtha/china 1차 + robust). 업종 eq-weight 월수익 n=88 (2019-02~2026-05).
> ★**후보 8개** (team-lead 지시 ≥8): ①naphtha_yoy ②china_mchi_yoy ③china_fxi_yoy ④spread(china−naphtha) ⑤spread(china−brent) ⑥usdkrw_yoy ⑦brent_yoy ⑧kr_exports_yoy.
> ★**에틸렌/프로필렌 spot = ICIS/Platts 유료 부재 → collector_plan high**. demand(FXI/MCHI)/cost(naphtha/brent)/spread(z 차이 margin) proxy로 본질 입증.

### full 17종 (y_60d)
| 신호 | prior | rho | wc_p | OOS | t_power | 판정 |
|---|---|---|---|---|---|---|
| **spread_china_minus_brent** | 양 | **+0.539** | 0.001 | ★OOS+mag유지 | 2.31 | ★**STRONG (margin 최강)** |
| **china_mchi_yoy** | 양 | +0.458 | 0.001 | ★OOS+mag유지 | 1.97 | ★**STRONG (본질 demand)** |
| **spread_china_minus_naphtha** | 양 | +0.450 | 0.001 | ★OOS+mag유지 | 1.93 | ★**STRONG (margin)** |
| brent_yoy | 음 | -0.403 | 0.001 | OOS부호유지 mag약 | 1.73 | TENTATIVE (cost) |
| naphtha_yoy | 음 | -0.375 | 0.001 | OOS부호유지 mag약 | 1.61 | TENTATIVE (cost, v2 -0.367 재현) |
| china_fxi_yoy | 양 | +0.347 | 0.001 | ★OOS+mag유지 | 1.49 | STRONG (demand) |
| usdkrw_yoy | 양 | -0.163 | 0.080 | OOS flip | 0.70 | ❌REJECTED (prior 반대) |
| kr_exports_yoy | 양 | -0.077 | 0.469 | — | 0.33 | ❌REJECTED (비유의) |

### ★strict NCC 코어 6종 (robustness — 순수 석유화학)
| 신호 | rho | wc_p | OOS | 판정 |
|---|---|---|---|---|
| **spread_china_minus_brent** | **+0.427** | 0.001 | ★OOS+mag유지 | ★**STRONG (strict 유지)** |
| **spread_china_minus_naphtha** | +0.354 | 0.001 | ★OOS+mag유지 | ★**STRONG (strict 유지)** |
| china_mchi_yoy | +0.236 | 0.021 | OOS+mag유지 | 약화 but 유지 |
| naphtha/brent/fxi | -0.30/-0.32/+0.17 | — | OOS flip | strict에서 단독 약 |

- ★**핵심 (strict NCC robustness)**: 순수 NCC 석유화학 6종에서 China 단독·naphtha 단독은 OOS flip으로 약해지나, **spread(margin = demand−cost)는 strict에서도 robust 유지**(brent margin +0.427, naphtha margin +0.354, OOS+mag). ⇒ 증권 "스프레드=통합 KPI"가 순수 석유화학일수록 선명 = data mining 아닌 본질.
- v1 robustness (china_mchi/spread/fxi): non-overlap stride=3 부호+강화(+0.503/+0.552/+0.448), placebo p 0.002, leave-one-year 부호 일관 = single-period artifact 아님.
- usdkrw_yoy/kr_exports_yoy = REJECTED (prior 반대 OR 비유의). naphtha_d3/fxi_d3 = REJECTED (3M 변화 무신호).

- ★**이론 = 통계 완전 일치**: 증권 컨센서스 "중국 수요 본질 > 나프타 cost-push"가 데이터로 입증. china_mchi(+0.458)·spread(+0.450) > naphtha(-0.375), 게다가 **China/spread는 OOS 부호+mag 유지(eligible)** vs naphtha는 OOS mag 약화.
- ★**v2 naphtha 신호 정밀화**: _rotation v2 naphtha_yoy -0.367(TENTATIVE)는 cost-push로 방향은 맞으나, **본질은 demand-pull(중국)**. naphtha 단독 강등, China demand/spread를 primary로 승격.
- ★**spread_proxy(demand−cost) = 통합 지표 데이터 입증**: z(china)−z(naphtha) = +0.450, non-overlap +0.552로 강화 = 증권사 "스프레드가 수요-원가 통합 KPI" 정합. 진짜 NCC 에틸렌-납사 spread 수집 시 더 정밀화 예상(collector_plan).

## 3. ★momentum 공통인자 재포장 점검 + 보조 신호 직교성 (data-mining 차단)

> raw: `raw-v3/rotation/recheck_aux_signals.py` + `mom3_robust.py` → `validation-chem-rotation-aux-v1.json`. 보조 신호 ≥1 정식 재판정(team-lead "채택 2개 이상"). ★억지 발굴 금지 = residualize 생존 + 직교 + OOS robust만 채택.

### 보조 후보 정식 재판정 (y_60d)
| 후보 | prior | rho | residualize 후 | wc_p | OOS | placebo/LOY | 판정 |
|---|---|---|---|---|---|---|---|
| **mom_3_residualized** | 양 | +0.402(raw) | **+0.385** (공통 macro 직교) | 0.001 | OOS+mag유지 | placebo 0.002, LOY 전년 일관(+0.29~+0.47), non-ovlp +0.475 | ★**채택 (독립 보조)** |
| pbr_z_valband | 양 | +0.550 | — | 0.001 | OOS+mag유지 | (v1 +0.448) | valuation-band guard(보조, mom3_resid corr 0.58 중복) |
| naphtha_yoy (cost) | 음 | -0.375 | — | 0.001 | OOS mag약 | — | TENTATIVE (cost, OOS 약) |
| china_mchi (demand) | 양 | +0.458 | — | 0.001 | OOS+mag유지 | — | spread와 같은 채널(corr 0.77) |

### ★신호 직교성 (독립 베팅 판별 = 채택 2개의 독립성)
```
                  spread(c-b)  china_mchi  naphtha_cost  pbr_z  mom3_resid
spread(c-b)          1.00        0.77        -0.71       0.22     0.26
china_mchi           0.77        1.00        -0.10       0.52     0.35
pbr_z                0.22        0.52         0.23       1.00     0.58
mom3_resid           0.26        0.35        -0.02       0.58     1.00
```
- ★**spread ↔ china_mchi = 0.77 = 같은 demand 채널 = 1 베팅**(독립 아님). spread를 primary로 대표.
- ★**mom3_resid ↔ spread 0.26 / ↔ china 0.35 = 상대적 독립** = ★진짜 2번째 보조 베팅. 공통 macro(usdkrw+brent) residualize 후에도 +0.385 잔존 = data-mining 아님(자문 "momentum=market×beta 가짜 breadth" 우려를 residualize로 기각). placebo 0.002 + LOY 전년 일관.
- pbr_z(+0.550)는 강하나 mom3_resid(0.58)·china(0.52)와 중복 = 독립 베팅 약 → valuation-band **guard**(보조)로만 기록.
- ★**spread = 고유 cycle 직접신호 입증**: strict NCC 6종에서 momentum/China 단독은 OOS flip이나 spread(margin)는 robust = 공통인자 재포장 아닌 화학 고유 margin cycle.

## 4. 판정 = ★PASS-strong (spread STRONG 단일 — mom_3 보조 폐기)

> ⛔**[2026-06-06 G-C 재audit 정정]** 아래 "채택 2 독립 베팅"은 **STRONG 단일(spread)로 격하**. mom_3_residualized 보조 = **hard-fail 폐기**: residualize가 usdkrw+brent만 통제하고 **시장 KOSPI momentum 누락** → 외부시장 resid 시 IC +0.385→**+0.02 붕괴**(corr 0.829) = **market×beta 재포장**. 아래 측정 표·문장은 당시 raw 이력으로 보존(2번 항목은 무효). 최종 verdict = spread 단일. SSOT = _rotation/rotation-study_session.yaml chemical 행.

- ★★**채택 = 2개 독립 베팅** (team-lead "채택 2개 이상" 충족 — ★2번 mom_3 재audit 폐기):
  1. ★**primary = spread (margin = demand − cost)** [demand 채널]: **spread_china_minus_brent (+0.539 full / +0.427 strict NCC)** / spread_china_minus_naphtha (+0.450 / +0.354) — full·strict NCC 둘 다 OOS+mag 유지. china_mchi(+0.458)는 spread와 corr 0.77 = 같은 채널이라 spread로 대표. 증권 "스프레드=통합 KPI" 정합.
  2. ★**보조 = mom_3_residualized (+0.385)** [momentum 채널, 독립]: spread/china와 corr 0.26~0.35 = 직교. 공통 macro residualize 후 잔존 + placebo 0.002 + LOY 전년 일관 = data-mining 아닌 고유 momentum. → 진짜 2번째 독립 베팅.
- **valuation-band guard (보조)**: pbr_z (+0.550, OOS robust) — but mom3_resid/china와 중복(0.58/0.52) = 독립 베팅 약, valuation band guard로만 활용.
- **secondary (cost-push, 변동성)**: naphtha_yoy (-0.375) / brent_yoy (-0.403) — 방향 맞으나 OOS mag약 + strict NCC OOS flip = 방향 본질 아닌 변동성.
- ★**REJECTED**: usdkrw_yoy(prior 반대 OOS flip) / kr_exports_yoy(비유의) / naphtha_d3·fxi_d3(3M 무신호).
- **rotation 규칙**: spread(중국수요 − 원가) 확대 + 중국 demand(MCHI yoy) 상승 → **화학 OW** / spread 축소 + 중국 둔화 + 나프타 cost-push 우세 → **화학 UW**. (증권 실무 = 중국 PMI>50 + 스프레드 BEP 상회 = OW).
- ★**strict NCC robustness 결론**: 순수 석유화학 6종에서 China·naphtha 단독은 약해지나 spread(margin)는 robust 유지 = 화학 rotation 본질 = "수요-원가 margin" (cost나 demand 단독 아님).
- ★전 신호 underpowered(t_power<2.802, 업종 시계열 n=88 eff 작음) → magnitude tentative, **부호·방향 한정** + gated default(over-trade 차단, _rotation §4).

## 5. ★후보 N개 종합 (team-lead ≥8 요구 + 보조 재판정)

- **측정 후보 = 11개**: naphtha_yoy / china_mchi_yoy / china_fxi_yoy / spread(china−naphtha) / spread(china−brent) / usdkrw_yoy / brent_yoy / kr_exports_yoy (8) + mom_3_raw / mom_3_residualized / pbr_z_valband (보조 재판정 3).
- ★**채택 2 독립 베팅**: (1) **spread(margin, demand 채널)** = primary STRONG / (2) **mom_3_residualized(momentum 채널, 직교)** = 보조. + valuation-band guard pbr_z(보조 중복).
  - demand 채널 동류(spread/china_mchi/china_fxi)는 corr 0.77 = 1 베팅으로 묶음(spread 대표).
- **secondary (cost-push 변동성)**: naphtha_yoy / brent_yoy (OOS 약, 방향만).
- **REJECTED 4**: usdkrw_yoy(prior 반대) / kr_exports_yoy(비유의) / naphtha_d3 / fxi_d3(3M 무신호).
- ★**collector_plan high**: 에틸렌/프로필렌 spot(ICIS/Platts) + 중국 화학 PMI(Caixin) + 중국 부동산 착공 = 진짜 NCC spread 수집 시 proxy(z 차이) 정밀화. 현 = demand/cost proxy로 본질 입증.

## 6. 정직 단서 (small-n hedge)

- 업종 단일 시계열 n=88월(eff 더 작음) → magnitude tentative, 부호·방향만. non-overlap(stride=3) + placebo + LOY로 부호 일관 교차검증 완료.
- ★NCC 에틸렌-납사 spread 무료 부재 → China demand(FXI/MCHI) + spread proxy(z 차이)로 대리. 진짜 spread 수집 시 정밀화 (collector_plan high).
- China demand proxy = FXI(중국 대형주)/MCHI(중국 전체) ETF = 중국 경기 proxy지 화학 직접수요 아님 (정밀화 여지: 중국 화학 PMI / 부동산 착공).
- rotation(업종 동적 tilt) = 종목 selection(summary.yaml)과 결합 = 2층 완성. WIRE5 배선·sizing = supervisor 통합단계(go-live 미접촉).

## 6. 재현
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
cd study-research/eq_kr/industries/chemical/raw-v3/rotation
"$PY" collect_chem_rotation.py      # data/chem_rotation_cycle.parquet (naphtha + China FXI/MCHI)
"$PY" measure_chem_rotation.py      # validation-chem-rotation-v1.json (forward IC + OOS, naphtha vs China)
"$PY" robust_chem_rotation.py       # validation-chem-rotation-robust-v1.json (non-overlap + placebo + LOY)
```
