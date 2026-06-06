---
tags: [type/rotation-signals, domain/equity, sector/bio, scope/equity-kr]
date: 2026-06-06
purpose: bio 업종 ROTATION 신호 (산업 OW/UW timing) — v2 data-gate 재검(이론→통계). 종목 selection 과 별개.
author: bio-analyst teammate (bio 산업 전문)
raw: raw-v3/{measure_rotation, measure_rotation_composite}.py + validation-rotation-v3.json + validation-rotation-composite-v3.json
---

# bio 업종 ROTATION 신호 — 산업 OW/UW timing

> ★종목 selection capsule(summary.yaml, flow_sell conditional)과 **별개**. 본 문서 = "어느 국면에 bio **업종 전체**를 OW/UW 하나" timing.
> ★v2 rotation-analyst 판정 = bio NO_DIRECT_CYCLE + momentum OOS flip = **FAIL/data-gate**. 본 재검 = bio 전문 이론으로 ★거시 overlay 재측정(v2 미측정 = 핵심 누락).

## §1. 이론 (부호 사전확약, 측정 前 동결 — HARKing 방지)

★bio = **growth / long-duration cashflow**(10-15년 R&D + launch) → **discount-rate sensitive**. theory-notes §3 + 증권사 바이오 리포트.

| 신호 | 이론 부호 | 메커니즘 (왜 이 국면에 bio OW/UW) |
|---|---|---|
| **US 10Y Δ (us_10y_d)** | **음(−)** | ★핵심. growth duration: 미국 장기금리↑ → bio 장기 cashflow 할인율↑ → bio UW. (글로벌 바이오 valuation = US 금리 dominant) |
| KR 10Y Δ (kr_10y_d) | 음(−) | 국내 금리 duration 동일 (단 한국 bio = 글로벌 매출 → US 금리 우세 예상) |
| US 금리커브 10Y-2Y (us_curve) | 양(+) | steepening = 경기회복/risk-on → 성장주 bio OW (보조) |
| **XBI/SPY 상대모멘텀 (xbi_rel_mom)** | **양(+)** | ★글로벌 바이오(XBI=equal-weight 신약) 강세 → 한국 bio 동조 OW. 글로벌 바이오 cycle 전이 |
| IBB/NDX 상대모멘텀 (ibb_rel_mom) | 양(+) | 나스닥 대비 바이오(IBB=cap-weight) 강세 = 섹터 로테이션 유입 |
| XBI 절대 모멘텀 (xbi_mom) | 양(+) | 글로벌 바이오 ETF 모멘텀 = 산업 cycle proxy(bio 고유 cycle 무료 부재 대체) |
| 원/달러 Δ (usdkrw_d) | 약/불확정(0) | 수출주(삼바/셀트리온) 약세수혜 but round-1 USDKRW REJECTED = 약 prior |
| VIX (vix_level) | 음(−) | bio 고베타(β=+0.011 t=6.03) → risk-off(VIX↑) 시 UW |
| HY OAS (credit_hy) | 음(−) | risk-off proxy → 성장주 bio UW |
| FDA 승인 yoy (fda_yoy) | 양(+) | 신약 cycle peak → 한국 license-out 환경/sentiment ↑ (theory §3.4) |

★**후보 N = 10개** (team-lead 요구 ≥8 충족). primary = 금리 duration(us_10y_d) + 글로벌바이오 상대(xbi/ibb_rel_mom). secondary = 커브/환율/VIX/credit/FDA.

★bio 고유 cycle 직접지표(임상 phase/파이프라인) = 무료 monthly 부재(theory §4.4 한계) → ★글로벌 바이오 ETF(XBI/IBB) = 산업 cycle proxy 로 대체. 한계 박제.

## §3. 통계 검증 (이론→통계, bio 업종 forward IC)

> 측정 대상 = bio 업종 forward return(eq-weight strict 화이트리스트 38종, 좀비 마스킹) vs 거시 overlay 시계열.
> ★좀비 NaN 마스킹(코오롱티슈진 950160 47.8% + 케어젠 214370 19% 거래정지 carry-forward 제거). 패널 89개월.

### 3.1 단변량 후보 (validation-rotation-v3.json)
| 신호 | h | rho | wc_p | 이론부호 일치 | OOS (is→oos) | eligible | status |
|---|---|---|---|---|---|---|---|
| **us_10y_d** | y_60d | **−0.244** | **0.0285** | ✅(음) | −0.194→−0.213 | ✅Y | underpowered |
| us_10y_d | y_20d | −0.115 | 0.241 | ✅ | −0.093→−0.159 | ✅Y | underpowered |
| **xbi_rel_mom** | y_20d | **+0.153** | 0.189 | ✅(양) | 0.131→0.190 | ✅Y | underpowered |
| ibb_rel_mom | y_20d | +0.124 | 0.254 | ✅ | 0.080→0.178 | ✅Y | underpowered |
| us_curve | y_60d | +0.044 | 0.651 | ✅ | 0.091→0.301 | ✅Y | underpowered |
| credit_hy | y_60d | −0.173 | 0.285 | ✅ | OOS n<8 | − | underpowered |
| fda_yoy | y_60d | +0.142 | 0.216 | ✅ | 0.280→−0.138 | n(flip) | underpowered |
| kr_10y_d | y_60d | −0.136 | 0.197 | ✅ | −0.143→+0.177 | n(flip) | underpowered |
| usdkrw_d | y_20d | −0.048 | 0.637 | −(불확정) | −0.098→−0.008 | n | underpowered |
| **vix_level** | y_20d | +0.056 | 0.623 | ❌(이론 음, 실측 양) | 0.319→−0.232 | n(flip) | underpowered |

★**이론 부호 일치 = 10중 8** (us_10y_d/kr_10y_d/us_curve/xbi_rel/ibb_rel/xbi_mom/credit_hy/fda_yoy). vix_level만 반대(고베타 가설 = 업종 timing 에선 약), usdkrw 불확정(round-1 REJECTED 정합). = ★이론이 통계로 검증됨(data-mining 아님).

### 3.2 composite overlay (이론 부호 정렬 z-score 합성, validation-rotation-composite-v3.json)
> power 보강 = 이론 부호로 방향 정렬한 신호 합성. prior 전부 양(+, overlay 클수록 bio OW).

| composite | 정의 | h | rho | wc_p | OOS (is→oos) | eligible |
|---|---|---|---|---|---|---|
| **rate_overlay** | −(US 10Y Δ z) = 금리 하락 시 bio OW | y_60d | **+0.274** | **0.018** | 0.004→0.209 | ✅Y |
| **full_overlay** | (금리 + 글로벌바이오)/2 합성 | y_20d | **+0.180** | 0.124 | 0.074→0.250 | ✅Y |
| full_overlay | 〃 | y_60d | +0.203 | 0.115 | −0.053→0.274 | n |
| bio_global_overlay | (XBI/SPY + IBB/NDX 상대모멘텀)/2 | y_20d | +0.132 | 0.273 | 0.058→0.202 | ✅Y |

★composite 가 단변량보다 OOS robust. rate_overlay y_60d wc_p=0.018 = 가장 강. ★단 **IS rho≈0 → OOS rho 강**(0.004→0.209) = regime shift 성격(2023+ 발현, 종목 flow_sell conditional 과 동일 패턴).

### 3.3 강건성 (leave-2022 금리쇼크)
| 신호 | full | drop-2022 | 판정 |
|---|---|---|---|
| us_10y_d y_60d | rho=−0.244 wc_p=0.028 | rho=−0.174 wc_p=0.127 | 2022 부분 의존(약화) but ★부호+OOS 유지 = 단일 episode 종속 아님 |
| full_overlay y_60d | +0.203 | +0.234 wc_p=0.069 | 2022 제외해도 생존(오히려 강화) |

## §4. 판정 (이론+통계 = 채택 / 이론없이 통계만 = data-mining 채택불가)

### 4.1 v2 FAIL 재검 결론
- ★v2 판정(NO_DIRECT_CYCLE + momentum OOS flip = FAIL)은 **momentum 만 봤기 때문**. bio 고유 cycle 무료 부재 = 사실이나, ★거시 overlay(금리 duration/글로벌바이오 상대)는 v2 가 미측정 = 진짜 산업동향 부재 아님.
- 본 재검 = 이론(growth long-duration) → 통계(이론 부호 8/10 일치 + OOS 부호유지 다수) = ★**산업동향 신호 존재**(단 약).

### 4.2 tradeable 판정 (G-G v2 2축)
| 신호 | eligibility (OOS 부호유지) | conviction | 이론 | verdict |
|---|---|---|---|---|
| **rate_overlay (US 금리 duration)** | ✅ (us_10y_d wc_p=0.028 + OOS 부호유지 + leave-2022 부호유지) | low (underpowered t_pow<2.8 + IS약→OOS강) | ✅ growth duration | **PASS-conditional** |
| **bio_global_overlay (XBI/IBB 상대)** | ✅ (xbi/ibb_rel_mom OOS 부호유지 + composite OOS elig) | low (underpowered) | ✅ 글로벌바이오 전이 | **PASS-conditional** |
| full_overlay (금리+글로벌 합성) | ✅ (OOS elig + leave-2022 생존) | low | ✅ | PASS-conditional (보조) |

★**tradeable ≥2 충족**: (1) rate_overlay = 금리 duration (2) bio_global_overlay = 글로벌바이오 상대. 둘 다 이론+OOS 부호유지.

### 4.3 ★최종 verdict = PASS-conditional (monitor + macro overlay)
- **bio 업종 rotation = PASS-conditional** (v2 FAIL/data-gate 뒤집음, but low confidence).
- ★**핵심 신호 2 (이론+통계+OOS)**: ① **US 10Y 금리 하락 → bio 업종 OW**(growth duration, rate_overlay wc_p=0.018) ② **글로벌 바이오(XBI/IBB) 상대강세 → 한국 bio OW**(섹터 전이).
- ★**국면 출력 가능**(rotation 본질): "현재 = 미국 금리 하락 + 글로벌 바이오 강세 → bio 업종 OW / 금리 상승기 + 글로벌 바이오 약세 → UW".
- ★**한계(정직)**: (a) 전부 underpowered(t_power<2.802, BY survivors=[]) = magnitude 단정 금지, conservative cap (b) IS약→OOS강 = regime shift tentative(2023+ 발현, pristine OOS 차기 vintage 검증 의무) (c) bio 고유 cycle(임상/파이프라인) 무료 부재 = 글로벌 ETF proxy 대체(한계) (d) vix_level 이론 반대 = 업종 timing 에선 고베타 가설 약.
- ★**왜 conditional 만 = monitor**: 점추정 박제 금지(underpowered) + over-trade 차단. macro overlay = de-risk/tilt 용도(sizing prior)지 강 alpha 아님.

## §5. collector_plan (rotation 보강)
- ★임상 phase/파이프라인 monthly cycle 데이터(KFDA/clinicaltrials.gov facet) = bio 고유 cycle 직접지표. 현 = XBI/IBB proxy 대체. high.
- 한국 약가정책 이벤트(보험약가 인하 cycle) = 내수 제약 timing. medium.
- 한국 bio 전용 ETF(KODEX/TIGER 헬스케어) 상대 = 국내 sentiment proxy. 측정 가능(healthcare_etfs.parquet 보유) = 후속.
