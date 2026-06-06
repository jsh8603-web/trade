---
tags: [type/candidate-ledger, domain/equity, sector/shipbuilding, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# 조선(shipbuilding) 지표 후보 원장

> ★조선 = cross-sectional selection 신호 ★구조적 약 (산업 베타 슈퍼사이클 timing 지배, H9). 전 신호 BY 미생존.
> 채택 = vol_60(저변동) 방향 prior only (TENTATIVE). per_z BY 생존 = artifact 격하.

## ✅ 채택 (yaml 등록 + 검증 통과 — ★조선은 모두 TENTATIVE/약)
| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| cs_lowvol_60d | low_volatility | ★TENTATIVE DIRECTIONAL | IC -0.057, n=81. ★유일 OOS 부호유지(IS -0.065→OOS -0.049) + strict tier 강(-0.078, microcap 아님). ★단 block-boot CI [-0.129,+0.020] 0포함 + BY 미생존(wc_p 0.128) = magnitude 비유의, 방향 prior만 |

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| 글로벌 신조선 수주(Clarkson) | H1/H8, Maritime Economics | ★유료 데이터 부재. 조선 cycle 핵심 timing 변수(cross-sectional 아닌 regime conditioning) | Clarkson 구독 또는 무료 proxy |
| 신조선가 지수(Newbuilding Price Index) | H8, Clarkson | 유료 부재. 사이클 정점 확인 후행지표 | Clarkson 구독 |
| 운임(SCFI/CCFI 컨테이너/BDI 벌크) | H8, 증권사 | 직접지표 유료(SCFI 상하이항운교역소). BDRY ETF proxy 측정→forward 비유의 REJECTED | 운임 직접지표 + timing 용도 |
| 후판(steel plate) 가격 | 증권사 원가 cycle | yfinance 부재(POSCO 공시/철강협회) | 후판가 수집 → 원가 cycle regime |
| EV-EBITDA | archetype primary_metric | DART 부채/현금 계정 추가 필요(현 PBR/PER만) | DART BS 추가 수집 |
| 종목레벨 외국인 flow | frame 신지표 | ★DATA-GATE — KRX 종목별 차단(데이터 부재). 시장레벨 ECOS는 측정완료 | KRX 인증 또는 ETF flow proxy |
| 절대 PBR 레벨 mean-reversion (rolling z 아닌 절대밴드 0.5x/2x) | PBR밴드 timing 후속 | rolling z timing 측정완료=약(아래 ❌). 절대밴드 = in-sample cherry-pick 위험 | 다른 cycle 국면(슈퍼사이클 종료 후) OOS |

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|
| per_z (PER value) | ★ARTIFACT — 24M IC +0.204 BY 생존했으나 6M/12M OOS 부호반전 + avgN 6.9(흑자7종 small-universe) + 24M overlap eff_N 2.5 degenerate. 적자/peak trap(H3) 실증. tradeable 자격 X |
| pbr_z (PBR cross-sectional) | ★OOS 부호반전(IS value premium → OOS 역전, 슈퍼사이클 구간). cross-sectional 비유의(t=-0.39) |
| ★PBR 밴드 timing (시계열 섹터, team-lead 부활측정 2026-06-05) | ★측정했으나 약/불안정 (raw-v3/measure_sector_timing.py). 산업 합산 PBR(Σ시총/Σ자본 PIT) rolling36M z → 산업 forward. 12M IC +0.373(BY 생존)했으나 ★artifact (walk-forward IS 음(-0.58 mean-reversion)→OOS 양(+0.41 슈퍼사이클 trend) 부호반전). 1M/3M = OOS 부호유지(음=mean-reversion)하나 IS극단(-0.49/-0.66, n=27)→OOS 소멸(-0.026/-0.024). n_eff 10(PBR_z persistence). = ★부활 실패 (mean-reversion 가설이 슈퍼사이클 trend 에 반전). 현재 PBR 4.36x = 역사밴드 초과. ★per_z 24M 과 동일 BY생존≠tradeable artifact 패턴 |
| capex_ratio / ppe_yoy (asset growth) | ★무신호(IC≈0, 비유의). ★capex 일반화 가설 조선 미적용(two-sided→무신호). 자동차/반도체 음 prior 약하게도 미발현 |
| inv_ratio / inv_yoy (재고) | 비유의(약한 양=재공품 가설 방향이나 BY 미생존) |
| rnd_ratio (무형자산/R&D) | 비유의 (prior 양과 약하게 반대) |
| momentum (mom_6/mom_12_1/rev_1m) | OOS 소멸(IS -0.073→OOS -0.008) 또는 반전. cyclical reversal 방향이나 슈퍼사이클 momentum 전환 |
| customer-supplier momentum (운임/유가/조선ETF lagged) | REJECTED — 전 lag(0-3) 비유의(p>0.08). 주가가 운임 선행(H8) → 운임 lagged forward 예측력 부재 |
| sector-rotation business-cycle clock | 학술 myth(Molchanov 2024). 운임 momentum rotation 만 tentative |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| cs_lowvol_60d | block-boot CI 0 포함 + BY 미생존 = magnitude 비유의 (방향만) | 추가 데이터 N 누적 후 CI 0 배제 + BY 생존 시 승격. 또는 PBR 밴드 timing 과 결합 |
| H9 산업 베타 지배 | 슈퍼사이클(2023-25) 이후 정상화 구간에서 cross-sectional 신호 회복하나? | 슈퍼사이클 종료 후 OOS(미래 데이터) — ★현 검증 완료, 보너스 |
| ★tanker momentum 역방향(contrarian) | rotation 측정서 tanker_d3→조선 forward 60d IC -0.328(OOS 안정 음 IS-0.28→OOS-0.40) but ★사전확약 양 반증 + underpowered(t_mde 1.73) | ★사후 부호전환 = garden-of-forking-paths 위험. N 누적 + 신조선가 직접지표 확보 후 재평가. ⛔지금 tradeable 화 금지 |

## ★업종 rotation 신호 (team-lead 지시 측정, rotation-signals.md)
| 후보 | 부호확약 | 측정 IC | 판정 |
|---|---|---|---|
| tanker_basket (TNK/STNG/FRO) | 양(고객 발주여력 선행) | -0.328(d3→60d, wc_p 0.001) | ★REJECTED — 사전확약 양 반증(음) + underpowered. 운임/해운 고점=발주정점→조선 선반영후 되돌림(주가 선행 H8) |
| container_basket (GSL/DAC/ZIM) | 양 | +0.087(match) | 약/underpowered |
| boat_etf (BOAT) | 양 | -0.21(반증) | 약, 2021~ 짧음 |
| steel_plate (HRC 후판) | two-sided | +0.18(d3) | 약, 이중성(원가-/수요+) |
| lng_demand (LNG Cheniere) | 양 | -0.12(반증) | 약 |
| baltic_dry (BDI, v2) | 양 | -0.091(반증) | ★REJECTED(선종 불일치=벌크 vs LNG/컨테이너/탱커) |
| 신조선가 직접 (Clarksons) | — | ★무료 부재 | 측정 불가(유료) + 주가 6-12M 선행이라 후행지표 부적합 |
| 수주잔고 yoy | — | 정형 시계열 부재 | 동행/후행 지표(rotation 부적합, Gemini) |

## ★자문 3R 수렴 = monitor-only 정당화 (2026-06-06, .consult-kr-shipbuilding-rotation-RESULTS.md)

> "tradeable 0 = 구조부재 vs 측정한계" 재검 자문 3R. 원리적 불가능 아님(자본사이클) — **후행 펀더멘털 angle만 죽음**(운임·유가 정점=발주 정점→조선 주가 6-12M 선행 = forward를 trailing realized에 회귀하면 항등식적으로 무효).

| verdict 축 | 라벨 | 사유 |
|---|---|---|
| trailing_fundamental | ★**REJECTED** | oil+/tanker+/China− 후행펀더멘털 = 검정력O 반증(주가 선행 항등식) |
| overall | ★**INSUFFICIENT** | 전체 timing 신호 부재 = N≈1(88월=1 슈퍼사이클) 검정력 부족 = "못 잰 것"≠"없는 것" |
| contrarian | ★**LIVE_UNPROVEN** | 운임·유가 고점→조선 UW 역신호 OOS 음이나 forking-path 미해소(N≈1=OOS도 같은 사이클 꼬리) |

- ★**진짜 제약 = N≈1**: 한중일 newbuild 복제 = pseudo-replication(같은 글로벌 발주 사이클). 독립 N은 타 capital-cycle sleeve(offshore/반도체capex/민항) = **별도 후속과제 deferred**(cross-asset capital-cycle replication, revisit anchor로 침묵사 방지).
- ★**처리 = monitor-only(weight 0)** = trade 아닌 **사전등록 confirmation test 발화** + **anti-HARKing seal**(discovery_sample 88월=오염구간 void / valid_test_set disjoint / promotion_rule 사전등록만) + LORD++ FDR 등록(weight 0이어도 반복관찰=online-FDR 예산) + e-CUSUM 상대강도 + copper_gold down_only derisk(active view 뒷문 재유입 차단).
- ★**위험모형 유지**: factor exposure는 B·Λ·Bᵀ 공분산에 유지, idio active view만 0 (weight 0 ≠ 위험모형 제외, 자문 R3).
- ⛔ contrarian tradeable화 = 여전히 금지(N≈1 forking-path 미해소). reopen_trigger = S_pos>h AND supply_discipline_regime → candidate_view(NOT weight). SSOT = _rotation/rotation-study_session.yaml shipbuilding 블록.

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음) | ★조선 = validated 정량 규칙 0 (전 신호 BY 미생존) |
| memory | capex 일반화 = 조선 미적용 / 산업 베타 지배 H9 / per_z 24M artifact 패턴 | 다음 cycle(steel/refining 등 cyclical) 자문 prior 정정 입력 |
| observe-only | cs_lowvol_60d (방향 prior, BY 미생존) | N 더 누적 후 promotion 결정 |
| evt | ★G-B 트리거(BY 0 + 약신호) → team-lead 자문 발동 판정 대기 | promotion-log 후보 (자문 결과 = 방법 결함 vs 신호 본질) |
| pointer | PBR 밴드 timing 레이어 / Clarkson 수주·SCFI 운임 (collector_plan high) | 다음 세션 SSOT 정독 우선순위 |

## ★★capex 일반화 가설 결론 (team-lead 핵심 관심사)
- **질문**: 자동차 capex_ratio(asset growth anomaly, 음 prior, structural_high)가 조선처럼 자산집약 장치산업에도 적용되나?
- **조선 특수성**: orderbook(수주잔고) 기반 → asset growth 가 (a)과잉투자 음 (b)수주확대 양 = ★two-sided (one-sided 단정 금지).
- **측정 결과**: capex_ratio IC +0.0034(비유의), ppe_yoy IC -0.029(약한 음, 비유의). = ★무신호.
- **결론**: ★capex 일반화 가설은 ★조선에 미적용. asset growth anomaly 음 prior 가 조선엔 약하게도 미발현. 메커니즘 = 산업 베타(슈퍼사이클 timing) 지배(H9)로 capex 부호효과 압도. ★two-sided 로 one-sided 단정 회피한 게 정답(만약 음 prior 박았으면 데이터와 충돌).
