---
tags: [type/rotation-signals, domain/inv, scope/equity-kr, sector/aitech, status/measured]
date: 2026-06-05
owner: aitech-analyst (kr-equity team, opus 1m)
trigger_to_resume: "본 capsule + summary.yaml rotation 섹션"
---

# AItech 업종 ROTATION 신호 — 업종 자체 비중 timing (어느 국면 → AItech OW/UW)

> **임무** = 종목selection capsule(어느 AItech 종목)과 별개로 ★**AItech 업종 자체 시계열 forward return 예측**.
> ★team-lead 재보강(2026-06-05) = 후보 ≥8-10개 enumerate 후 전수 이론+통계 검증 (1개 조기종료 금지).
> **★후보 13개 검토 완료**. 파이프라인 = 이론(부호 사전확약) → 통계(forward 20d/60d IC + OOS) → 채택판정(data-mining 차단).
> verdict: TENTATIVE채택(이론+통계 powered/underpowered) / REJECTED(이론반증 or OOS flip) / data-mining(이론없이 통계).

## §1. AItech rotation 후보 ≥13개 enumerate + 부호 사전확약 (데이터 접촉 前 동결, PIT)

증권 IT/AI/게임 리포트의 AItech 업종 driver 망라. AItech = growth/long-duration + AI capex + 게임 event + 글로벌 tech 동조.

| # | 후보 (driver) | 이론 (산업동향 메커니즘) | ★사전확약 부호 | source |
|---|---|---|---|---|
| 1 | **rate_10y (금리)** | ★growth long-duration: 금리(할인율)↑ → 멀티플 압축 (Gordon growth, 2022 실증) | **음** | ^TNX |
| 2 | **nasdaq_qqq (글로벌 tech)** | 글로벌 인터넷/AI/SW cycle 동조 | 양 | QQQ |
| 3 | **ai_capex_nvda (AI capex/GPU)** | AI 투자 cycle 수혜 (데이터센터 GPU) | 양 | NVDA |
| 4 | **soxx_semi (반도체)** | 반도체 cycle 연동 (AI capex) | 양 | SOXX |
| 5 | **hyperscaler_capex (클라우드 capex)** | MSFT/GOOGL/AMZN(Azure/GCP/AWS) capex↑ → SaaS 수혜 | 양 | MSFT+GOOGL+AMZN eq-w |
| 6 | **power_demand_xlu (AI 전력수요)** | AI 데이터센터 전력수요↑ = AI 인프라 cycle (유틸리티 proxy) | 양 | XLU |
| 7 | **global_sw_igv (글로벌 SW)** | 글로벌 SW/SaaS 업황 = 한국 SW 동조 | 양 | IGV |
| 8 | **game_espo (게임 cycle)** | ★글로벌 게임/e스포츠 cycle = 게임 신작·흥행 (크래프톤/펄어비스 글로벌) | 양 | ESPO |
| 9 | **vix (위험선호)** | growth 고베타: risk-off(VIX↑) → AItech 약세 | 음 | ^VIX |
| 10 | **cloud_skyy (클라우드 인프라)** | 클라우드 인프라 cycle = SaaS/AI 수혜 | 양 | SKYY |
| 11 | **soxx_qqq_spread (반도체 상대강도)** | SOXX/QQQ↑ = tech 위험선호 risk-on = growth 강세 | 양 | SOXX/QQQ |
| 12 | **usdkrw (환율)** | 원화약세 → 수출 SW/게임(크래프톤·펄어비스) 환산매출↑ | 양 | regime_series |
| 13 | **rel_mom_kr (업종 모멘텀)** | AItech 업종 자체 momentum = reversal (종목selection reversal 정합) | 음 | 업종 cum |

★이론 근거: Gordon growth(듀레이션-금리), Stovall sector rotation, Molchanov(2024) business-cycle clock myth(기계적 rotation 한계→fundamental driver 우선).

## §2. 측정 결과 — 후보 13개 전수 (forward 20d/60d IC + OOS + 부호 사전확약 대조)

> 측정 = raw-v3/{collect_aitech_cycle(_ext), measure_rotation(_ext)}.py → validation-rotation-ext-v1.json.
> 업종 = eq-weight 26종 월수익(★좀비 마스킹 셀바스AI 284일). n=88 month. wild-cluster B=2000 + block-boot + OOS(2023 split). 금리/VIX = level Δ, 나머지 = pct_change.

### ★채택 (TENTATIVE) — 이론+통계 부호일치 + OOS + wc_p<0.10

| 후보 | best signal | rho | 부호(obs/prior) | wc_p | CI95(prod) | OOS (IS→OOS) | t_power | verdict |
|---|---|---|---|---|---|---|---|---|
| **game_espo** | yoy y_60d | **+0.382** | 양/양 ✓ | **0.002** | **[0.005, 0.059] 0배제** | +0.287→+0.415 ★강화 | 1.96 | ★**TENTATIVE 채택 (최강)** — 게임 글로벌 cycle, CI 0배제(유일) |
| **rate_10y** | yoy y_60d | −0.273 | 음/음 ✓ | 0.014 | [−0.049, 0.002] | −0.218→−0.290 유지 | 1.56 | ★TENTATIVE 채택 — 금리 growth duration |
| **global_sw_igv** | yoy y_60d | +0.255 | 양/양 ✓ | 0.018 | [−0.005, 0.045] | +0.243→+0.261 유지 | 1.42 | ★TENTATIVE 채택 — 글로벌 SW 업황 |
| **cloud_skyy** | yoy y_60d | +0.220 | 양/양 ✓ | 0.041 | [−0.009, 0.044] | +0.242→+0.196 유지 | 1.18 | ★TENTATIVE 채택 — 클라우드 cycle |

### 약-TENTATIVE (부호일치+OOS but wc_p>0.10)

| 후보 | best | rho | wc_p | OOS | verdict |
|---|---|---|---|---|---|
| nasdaq_qqq | yoy y_60d | +0.161 | 0.123 | 유지 | 약 (tech 동조, wc_p>0.10 + ★공통인자 재포장 의심) |
| hyperscaler_capex | yoy y_60d | +0.162 | 0.124 | 유지 | 약 (클라우드 capex 동조, 약) |

### ★REJECTED (부호 사전확약 반증 or OOS flip)

| 후보 | best | rho | 부호(obs/prior) | OOS | verdict |
|---|---|---|---|---|---|
| **ai_capex_nvda** | d3 y_60d | −0.211 | 음/양 ✗ | OOS flip(+0.067→−0.606) | ★REJECTED (반증+flip) — AI capex Δ forward 예측력 부재 |
| **soxx_semi** | d3 y_60d | −0.174 | 음/양 ✗ | OOS flip | ★REJECTED (반증+flip) |
| **power_demand_xlu** | yoy y_20d | −0.134 | 음/양 ✗ | OOS flip | ★REJECTED (전력=유틸리티 방어 → AItech와 역, 반증) |
| **rel_mom_kr** | yoy y_20d | +0.115 | 양/음 ✗ | OOS flip | REJECTED (업종 raw momentum 무신호, ★residualize 후만 reversal) |
| **vix** | yoy y_60d | +0.164 | 양/음 ✗ | 유지 | REJECTED (★부호 반증 — VIX↑ 시 AItech 강세?? = risk-off 회복 rebound artifact 의심, 이론 반증) |
| **soxx_qqq_spread** | d3 y_60d | −0.186 | 음/양 ✗ | 유지 | REJECTED (반증 — 반도체 상대강 시 AItech 약, 이론과 반대) |
| **usdkrw** | yoy y_60d | **−0.364** | 음/양 ✗ | −0.439→−0.196 | ★REJECTED(통계강·이론반증) — 원화약세→AItech ★약세(음). 사전확약(수출 수혜 양) 반대. wc_p=0.002 통계 강하나 이론 반증 → 부호 재해석(memory) |

## §3. 판정 종합 (★후보 13개 전수 검토)

★**채택(TENTATIVE) 4개**: game_espo(최강, CI 0배제) > rate_10y(금리) > global_sw_igv(SW) > cloud_skyy(클라우드).
- 공통 = ★글로벌 tech/게임/SW/클라우드 yoy 모멘텀(양) + 금리(음) = AItech 업종 = ★글로벌 성장 cycle 동조 + 금리 민감 = growth/long-duration archetype 정합.
- ★game_espo(+0.382) = 가장 강 = 게임 신작·글로벌 흥행 cycle (게임 sub-cluster 13/26종 = 업종 dominant driver). CI 0배제 = 4 후보 中 유일.

★**REJECTED 7개**:
- ai_capex_nvda/soxx Δ = forward 예측력 부재(OOS flip) = ★종목selection customer momentum REJECTED 정합 (글로벌 tech = contemporaneous 동조이지 forward Δ 예측 아님).
- power_demand_xlu(전력=유틸리티 방어주 → AItech와 역), soxx_qqq_spread, vix = 이론 반증 정직 기각.
- ★**usdkrw = 통계 강(wc_p 0.002)하나 부호 반증**(원화약세→AItech 약세) = ★중요 발견: AItech = 수출주 아니라 ★내수 성장주(인터넷 NAVER/카카오 내수 + 게임 내수 비중) + 원화약세=risk-off 외국인매도 효과가 수출 환산효과 압도. → memory 자산화(수출 수혜 가설 반증), rule 아님.

★**약 2개**: nasdaq/hyperscaler = tech 동조 양이나 wc_p>0.10 + 공통인자 재포장 의심.

★**data-mining 차단**: 채택 4개 = 이론(글로벌 cycle/금리 duration) 명확 + 부호 사전확약 일치 = data mining 아님. REJECTED = 이론 있으나 통계 반증(OOS flip or 부호반대) = 정직 기각. raw momentum(rel_mom_kr) 무신호 → residualize 후만 reversal = 공통인자 재포장 점검 통과.

★**전 후보 underpowered**(t_power < 2.802, n=77-88, n_eff 25-33, BY 미생존 m=52 raw_p_min 0.002=game_espo) = TENTATIVE 상한. small-n rule = magnitude 보수, 부호·방향만 신뢰.

## §4. G-G v2 매매 충분성 (rotation tradeable)

| 신호 | eligibility(OOS) | conviction | net_alpha | 국면 | verdict |
|---|---|---|---|---|---|
| **game_espo yoy** | PASS (OOS +0.287→+0.415 강화, CI 0배제) | low-mid (underpowered t 1.96, wc_p 0.002) | rotation 저회전 = 양 | 글로벌 게임 cycle 상승기 OW | ★PASS-conditional (TENTATIVE 최강, primary rotation) |
| rate_10y yoy (금리 음) | PASS (OOS 유지) | low (t 1.56, wc_p 0.014) | 양 | 금리 하락기 OW / 상승기 UW | PASS-conditional (TENTATIVE) |
| global_sw_igv / cloud_skyy | PASS (OOS 유지) | low (wc_p<0.05) | 양 | 글로벌 SW/클라우드 상승기 OW | PASS-conditional (TENTATIVE, game와 상관 높음 = 중복) |
| nasdaq/hyperscaler | PASS but wc_p>0.10 | very low | - | tech bull | monitor-only |
| ai_capex/soxx/power/vix/spread/usdkrw | fail (flip or 부호반증) | - | - | - | REJECTED (rotation 제외) |

★rotation industry_verdict = ★**TENTATIVE-PASS** — tradeable ≥1: ★**game_espo(글로벌 게임 cycle, 최강 CI 0배제)** + rate_10y(금리 음) + global_sw/cloud(SW/클라우드, game와 상관). = ★글로벌 tech/게임 성장 cycle 상승 + 금리 하락 국면 → AItech 업종 OW. 단 underpowered=TENTATIVE → conservative macro tilt + monitor.
★종목selection(pbr validated_alpha) = primary, rotation(게임 cycle + 금리 tilt) = 보조 overlay.
국면지도: "글로벌 게임/SW cycle 상승 + 금리 하락 국면 → AItech 업종 비중↑ + 그 안 저PBR 종목 overweight".

## §5. 정직 단서 + 한계

- ★전 후보 underpowered (n=77-88, t<2.802, BY 미생존 m=52) = magnitude 보수, 부호·방향만. game_espo만 CI 0배제(가장 견고).
- ★채택 4개(game/SW/cloud/nasdaq) = ★상호 상관 높음(전부 글로벌 tech yoy) = 독립 4 신호 아님 = ★1 글로벌 tech/게임 factor + 금리(직교) = N_eff ~2 (통합단계 residualize 의무).
- cycle proxy = yfinance US-listed(글로벌, KR 직접 아님). rate=US 10Y(KR 국고채 후속). game_espo=글로벌 게임(한국 KODEX 게임 직접 = 후속).
- ★usdkrw 부호 반증 = 수출 수혜 가설 반증(memory). vix 부호 반증 = rebound artifact 의심(추가 검토).
- game 신작 직접 ledger(출시 일정·매출)/광고매출/SaaS ARR = 무료 정형 부재(각사 IR 수동) = collector_plan.
- 좀비 마스킹(셀바스AI 284일) 적용.

## §6. source / 근거
- Gordon growth model / Stovall (1996) sector rotation / Molchanov (2024) business-cycle clock myth.
- ★종목selection capsule = summary.yaml (pbr validated_alpha + momentum reversal). rotation = 업종 timing overlay.
- raw 재현 = raw-v3/{collect_aitech_cycle, collect_aitech_cycle_ext, measure_rotation, measure_rotation_ext}.py → validation-rotation-v1.json + validation-rotation-ext-v1.json.
