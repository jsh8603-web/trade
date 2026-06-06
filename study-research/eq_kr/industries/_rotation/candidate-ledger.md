---
tags: [type/candidate-ledger, domain/equity, sector/_rotation, purpose/easy-review]
date: 2026-06-05
purpose: 12산업 rotation timing 신호 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# 12산업 rotation timing 신호 후보 원장

> 분석 unit = 산업 eq-weight 패널 forward return (종목 cross-section 아님). 신호 = 산업 자체 시계열 예측.

## ★★★최종 12산업 rotation verdict 현황 (S7 통합 + G-C 재audit + 조선 자문 3R, 2026-06-06)

> ★SSOT = `_rotation/rotation-study_session.yaml §3`. 아래는 한눈 요약. tier = 신호 강도 / 채택수 = 독립 베팅 개수(사용자 "채택 ≥2" 규칙 점검용).

| 산업 | tier | 채택수 | primary 신호 | 비고 (단일/구조 사유) |
|---|---|---|---|---|
| chemical | ★STRONG | **1** | spread(china−naphtha margin) | ★단일 — mom_3 보조 G-C 재audit hard-fail 폐기(market×beta 재포장). cyclical momentum=시장베타 분리불가 = 단일 정직 |
| steel | ★STRONG | **1** | iron_ore_d3 | ★단일 dominant driver — 후보 전수 iron 통제 후 incremental t<1.1 중복(억지발굴 금지) |
| battery | ★STRONG | 6 | lithium_yoy (multi-source) | LIT/ALB/REMX/NIO 6신호 EV 수요 cycle |
| auto | ★STRONG | 1~2 | global_auto_d3 | iron_ore=post-hoc tentative(사전등록 격상 금지) |
| aitech | tradeable | 4 | game/rate_10y/global_sw/cloud | IT 성장 + 금리 duration |
| telecom | tradeable | **1** | semi_ppi_yoy(음) | ★외국인flow=L축 1회계상(전산업 공통 중복차감), telecom 고유=semi_ppi 한정 |
| bio | tradeable | 2 | rate_overlay + bio_global | singleton 격리 |
| consumer | tradeable | 4 | **mom_6_reversal_cosmetics** | ★재audit: cosmetics reversal=primary(genuine idio). CSI=tentative 격하(theory-family 한정 BY, C축 추적불가). 관광 tentative |
| semiconductor | tradeable | 2 | cli_chg + export | 종목선택(capsule)이 primary, rotation 보조 |
| refining | tradeable_weak | 2 | 유가 mean-rev + 배당 income-trap | ★crack=가스9종 오염 폐기(strict2 무신호). peak-out 2신호 conservative cap |
| financial | tradeable_weak | **1** | credit_spread_d6(음) | ★비대칭 — term_spread NIM=시장timing 채택불가 / credit_spread 대손=금융 고유 |
| shipbuilding | **monitor_only** | **0** | (weight 0) | ★자문 3R 복합: trailing=REJECTED / overall=INSUFFICIENT / contrarian=LIVE_UNPROVEN. N≈1 + anti-HARKing seal |

★**단일 채택 4산업(chemical/steel/telecom/financial)** = 모두 구조 사유 박제(억지 2개 발굴 회피 = garden-of-forking-paths 차단). ★**채택 ≥2 = 7산업**(battery/auto/aitech/bio/consumer/semiconductor/refining). ★**monitor 1**(shipbuilding).

---

## ★★v2 PRIMARY = 산업 고유 cycle 직접신호 (이론 부호 사전확약 + 통계검증, 자문 A 본체)

> ★사용자 파이프라인: 이론(산업동향 fundamental)→통계검증→판정. theory-notes.md 부호 사전확약. data-mining 차단.

| 산업 | cycle 신호 | source | rho (OOS) | 사전확약 부호 | verdict |
|---|---|---|---|---|---|
| steel | iron_ore_d3 | TIO=F | +0.341 (OOS+0.40, wc_p 0.001) | 양(철광석 cycle) ✅ | ★STRONG |
| battery | lithium_yoy | LIT | +0.274 (OOS+0.46) | 양(EV 수요) ✅ | ★STRONG |
| refining | ~~gasoline_crack_d3~~ → 유가 mean-rev / 배당 income-trap | refining_cycle | ~~+0.241~~ **폐기**(가스9종 패널오염, strict2=SK이노/S-Oil 단독 OOS flip 무신호) → 유가level −0.36 / 배당 t=−2.48 | 음(peak-out / income-trap) | ❌crack 폐기 → **tradeable_weak 2신호**(S7/audit 정정) |
| auto | global_auto_d3 | CARZ | +0.261 (OOS+0.30) | 양(글로벌차) ✅ | ★STRONG |
| chemical | wti_naphtha_yoy | CL=F | −0.367 (OOS약화) | 음(cost-push) ✅ | TENTATIVE |
| semiconductor | soxx_d3 | SOXX | +0.171 (wc_p 0.13) | 양(반도체 cycle) ✅ | TENTATIVE(종목선택 primary) |
| **shipbuilding** | baltic_dry_yoy | BDRY | −0.102 (wc_p 0.34) | 양(수주 cycle) ❌ | ★REJECTED(후행펀더멘털) → **monitor-only**(자문 3R 복합 verdict, 상단 현황 참조) |

## ★SECONDARY = momentum residualized (공통인자 재포장 검증, data-mining 차단)

| 산업 | raw → resid | 판정 |
|---|---|---|
| consumer mom_6 | −0.251 → −0.361(강화) | ★잔존=진짜 idiosyncratic(내수 방어 reversal). 채택 |
| telecom/aitech mom_6 | 잔존(방어 IT) | 잔존. telecom=carry tilt primary(자문) |
| chemical mom_6 | +0.296 → +0.211 | 잔존(추세, cycle 와 일관) |
| semiconductor/auto/battery/steel/financial mom_3 | 소멸(절반↓) | ❌ data-mining 의심(market momentum×beta=공통인자 재포장). 채택불가 |

## ✅ (v1) 채택 — momentum/rel_mom (★v2 에서 secondary 강등, 보조 confirm)

> ⚠️ v1 채택했으나 v2 자문 A 에서 강등: 공통인자 residualize 후 소멸 산업 = data-mining 의심. 아래는 v1 기록 보존.

| 산업 | 신호 | type | rho (OOS) | tier | 근거 |

| 산업 | 신호 | type | rho (OOS) | tier | 근거 |
|---|---|---|---|---|---|
| chemical | mom_3 | 산업고유 | +0.359 (OOS+0.391) | PASS-cond | non-ovlp +0.450 강화, placebo 0.0005, BY미생존(small-n) |
| refining | rel_mom_6 | 산업고유(reversal) | −0.360 (OOS−0.384) | PASS-cond | ★약신호활로, non-ovlp −0.388, placebo 0.0015 |
| consumer | rel_mom_6 | 산업고유(reversal) | −0.328 (OOS−0.571) | PASS-cond | OOS 강화, non-ovlp −0.333 |
| telecom | semi_ppi_yoy | cycle방어 | −0.334 (OOS−0.602) | PASS-cond | ★약신호활로, non-ovlp −0.422 |
| financial | cli_chg | macro(시장timing) | +0.482 (OOS+0.358) | PASS-cond | ★유일 powered+BY생존, non-ovlp +0.565 |
| aitech | semi_ppi_yoy | cycle | −0.333 (OOS−0.350) | PASS-cond | non-ovlp −0.455 |
| battery | mom_3 | 산업고유 | +0.277 (OOS+0.362) | PASS-cond | non-ovlp +0.146 약화(magnitude hedge) |
| steel | foreign_flow | macro flow | −0.251 (OOS−0.197) | PASS-cond | non-ovlp −0.282, cli_chg는 OOS flip 기각 |
| auto | mom_3 | 산업고유 | +0.238 (OOS+0.324) | PASS-cond | non-ovlp +0.144 약화 hedge |
| semiconductor | mom_3 | 산업고유 | +0.215 (OOS+0.346) | PASS-cond | 종목선택 primary, rotation 보조 |
| shipbuilding | rel_mom_3/foreign_flow | 산업고유/macro | −0.21/−0.24 | PASS-cond(약) | OOS 부호유지, wc_p 경계 |
| chemical | pbr_z(valuation-band) | valuation | +0.448 (OOS+0.58) | PASS-cond(보조) | ★valuation+momentum 일관(양)=추세산업. underpowered |
| steel | pbr_z(valuation-band) | valuation | −0.145 (OOS−0.29) | PASS-cond(보조) | valuation mean-reversion(음). underpowered |
| consumer | pbr_z(valuation-band) | valuation | −0.092 (OOS−0.14) | PASS-cond(약·보조) | 내수 valuation reversion. underpowered |

## ✅ 측정완료 (team-lead "valuation밴드" 명시 + plan "이연 금지" 이행)

| 항목 | 결과 | 산출 |
|---|---|---|
| 산업 aggregate valuation band (PBR z rolling 24M → forward) | ★4산업 OOS 견고(chemical 양/steel·consumer 음/battery 양), 나머지 OOS flip. FDR 생존 0(underpowered). momentum/rel_mom 의 보조 confirm 용도 | measure_rotation_valband.py → validation-rotation-valband-v1.json |

## ⏳ 이연 (식별됐으나 미투입 = collector_plan)

| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| 산업별 고유 cycle 지표 직접 (유가/crack=refining, 리튬/EV=battery, 철광석/중국조강=steel, SCFI 운임=shipbuilding) | frame §3 Layer3 + 자문 | 현 측정 = 공통 macro + 산업 자체 momentum/rel_mom + valuation-band. 산업 고유 cycle 미수집(refining만 collect_refining_cycle.py 보유) | yfinance/FRED 무료 proxy 수집(crack ETF/LME/SCFI) → forward 예측 추가 검증 |
| telecom dividend-carry tilt | 자문(claude) primary 권고 | 통신 = timing 보다 배당-carry 정적 tilt 가 방어가능. 배당데이터 미수집 | DART 배당 + 시총 → 배당수익률 시계열 |
| 통신 규제 event blackout overlay (요금인하 결정 window) | 자문(claude) | discrete event, 연속 timing 부적합 | 규제 발표 일자 수집 + event study |
| PIT shares (valuation-band 정밀화) | measure_rotation_valband.py caveat | shares_approx=Marcap/최근종가 근사(자사주/증자 미반영) | DART stockTotqySttus 시점별 발행주식수 |

## ❌ 미채택 / 기각

| 후보 | 사유 |
|---|---|
| bio rotation 전 신호 | ★FAIL = tradeable 0. cli_chg OOS flip(0.29→0.01), d_usdkrw wc_p>0.10. bio = 임상 idiosyncratic 지배 → 산업 timing 부재 = monitor-only |
| steel cli_chg | OOS flip(IS+0.33 → OOS−0.30) = eligible=False. 게이트 작동(기각) |
| aitech usdkrw_yoy / cli_chg | OOS flip/약화 = eligible=False 기각. semi_ppi 만 견고 |
| bio cli_chg / financial usdkrw_yoy / financial mom_3 | OOS flip = walk-forward 기각 |
| cli_chg (raw, PIT lag 미적용) | ★lookahead leakage — regime_series.parquet 의 cli_kr 는 PIT lag 미적용 raw. lag=2 적용 후 rho 0.555→0.482 (leakage 제거). 초기 버그 → D축 수정 |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| 전 rotation 신호 underpowered | 60d overlap eff_N 작음 → magnitude tentative (부호만) | 데이터 누적 OR non-overlap n 증가 → t_obs≥2.802 powered 승격 |
| macro 공통 신호(cli_chg/foreign/semi_ppi) | 12산업 N_eff 중복 = 가짜 breadth. rotation 차등 vs 시장 timing 구분 | N_eff orthogonality 분해(통합단계) → 산업 고유 직교 성분만 conviction |
| chemical/battery/auto mom_3 | non-overlap에서 일부 약화(0.45→strong / 0.15→weak) = overlap inflated 가능 | live OOS forward 추적 (e-CUSUM) |
| refining rel_mom_6 reversal | 정유 outperform=유가 끝물 mechanism = 유가 직접 지표로 재확인 필요 | collect_refining_cycle.py crack/oil 과 rel_mom 교차검증 |

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | 11/12 산업 rotation PASS-cond + gated 설계(default 0/dead-band/cost-aware/OOS-attenuation) | 검증된 rotation tilt 규칙 (conservative cap, supervisor 통합) |
| memory | "한국 12산업 PC1 55% 지배 → macro 신호=시장timing, 산업고유=진짜rotation" + "약신호산업 rotation 부활(refining/telecom)" | 다음 cycle 자문 prior |
| observe-only | underpowered rotation 신호 전체(financial cli_chg 외) | live OOS 누적 후 powered 승격 결정 |
| evt | cli_chg PIT-lag leakage 수정(rho 0.555→0.482) | promotion-log 후보 (regime_series raw=lag미적용 함정) |
| pointer | measure_rotation.py + summary.yaml = 산업 rotation SSOT / refining/measure_timeseries.py = prototype | 다음 세션 정독 우선순위 |
| memory | "한국 3층 selection robust=반도체 1곳(steel/aitech 경계). EB 대평균 끌림=약신호 끌어올림 = C12 설계 부작용(결함 아님). (f)종목별 수급=약신호 직교 레버" | 다음 selection cycle prior |
| observe-only | EB 약신호 부작용 정교화(계층 베이즈 half-Cauchy + noise-floor) + grade cut→convex 연속수축 | 통합단계 selection 코드 정식화 시 |
| pointer | verify_weak_signal_severity.py/.json = selection 약신호 심각도 SSOT / .consult-kr-within-industry-weak-signal-RESULTS.md = 자문 1R | 다음 세션 |

## 🧩 3층 산업 내 selection 약신호 — 자문 1R + 본인 검증 판정 (2026-06-06)

> 입력: 자문(gemini+claude 병렬 = `.consult-kr-within-industry-weak-signal-RESULTS.md`) + 본인 시뮬(`verify-weak-signal-severity.json`).

**layer 구분 (핵심)**: 사용자 "변별력 올려라" = **2층 rotation** active share(정상 작동, mean 10.1% / 비중 13배 차등). **3층 selection ρ**는 capsule IC 신뢰도 측정 = 다른 layer. selection 등급은 변별력 조절 대상 아님(측정).

**EB(C12) 정상성 판정**: within EB(부호보존 |IC| DerSimonian-Laird, 대평균 0.128 끌림) = **자문 C12 설계 그대로 = 결함 아님** ("소표본=대평균 끌림" C12 원문). 단 |IC|<대평균인 약신호(telecom 0.053→0.10)를 끌어올리는 부작용 = C12 미예견, 이번 자문 발견 = 방법 한계(통합단계 정교화 의제).

**selection 실효 보수 판정** (verify 시뮬, ρ 방식별):
| EB 방식 | 中 등급(ρ≥0.25) | 비고 |
|---|---|---|
| ①현행 부호보존 \|IC\| | 반도체·steel·aitech (3) | 약신호 대평균 끌림 포함 |
| ②zero-mean / ③noise-floor | **반도체만 (1)** | steel/aitech 中→低 강하 |
→ **robust 中 = 반도체 1곳**(ρ0.36, N_eff53, IC-0.114 BY생존). steel/aitech = 경계(방법 의존). 나머지 9곳 低/불가. selection 변별력은 약 = 억지 키우면 overfit.

**타당한 방향 (우선순위)**:
1. **규율 고정** — selection IC = capsule **primary**만(IC-never-as-selector). battery inv_ratio(+0.112 TENTATIVE) → cs_mom_6m(+0.075). 등급 영향 LOW(0.214→0.189 둘 다 低)지만 정직.
2. **(f) 종목별 수급**(외국인·기관 순매수·공매도 잔고) = 약신호 업종 직교 레버(최우선 별 study). breadth 직교(과점 업종도 flow는 시계열 변동). 검증 의무 = mom 직교(cs_mom residualize)·size 중립·공매도 regime-gate(2020-03~2021-05·2023-11~2024 금지 공백).
3. **(b) financial sub-sector 분리**(은행만 pbr -0.161 value) = capsule 이미 진단(통합 cancel), 분리 베팅은 통합단계.
4. **통합단계 정교화**: EB → 계층 베이즈(half-Cauchy) + noise-floor 보정 / grade cut → convex 연속수축 / cross-industry pooled selection(breadth 파편화 복구).

**현 단계 결론**: 연구단계 selection = 측정 정직성 확보 완료(EB는 C12 spec 충실). 변별력 주력 = 2층 rotation. 3층 = 반도체 중심 + 약신호 산업중립 바스켓. (f) 수급이 약신호 살릴 유일 잠재 레버(미실측).
