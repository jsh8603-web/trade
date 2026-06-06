---
tags: [type/rotation-signals, domain/equity, sector/refining, scope/equity-kr]
date: 2026-06-05
purpose: 정유 업종 rotation(섹터 비중 타이밍) 신호 — 이론 부호 사전확약 + 통계검증 + 판정. ★crack_d3 패널오염 적발.
sources: theory-notes §M1~M3 + Gemini 리서치(2026-06-05) + rotation-analyst v2 baseline 검증 + measure_rotation_refining.py
---

# 정유(refining) 업종 rotation 신호

> ★rotation = 업종 자체 비중 타이밍(OW/UW). 정유는 종목selection(cross-sectional) 영구불가(2종 과점) → rotation이 유일 활로.
> ★★CRITICAL: rotation-analyst v2 "crack_d3 +0.241"은 ★정유 아닌 가스 오염 신호(아래 §5). 정유 2종 단독 = crack 무신호.

## §1. 부호 사전확약 (측정 前 이론 동결, HARKing 방지)

| # | 신호 | 이론 부호 | 메커니즘·근거 |
|---|---|---|---|
| 1 | 정제마진(crack) d3 모멘텀 | 양(+) | crack 개선추세 → 애널리스트 실적추정 상향 사이클(PEAD). Bernard-Thomas 1989/1990, Chan-Jegadeesh-Lakonishok 1996 |
| 2 | 정제마진 level | 약(즉시반영) | crack level = 효율적 즉시반영(forward 약 prior). Damodaran DCF |
| 3 | 유가(brent) level | 음(-) | 고유가 = peak-out + 수요파괴 → 정유 forward 약. Deaton-Laroque 1992 commodity mean-reversion |
| 4 | 유가 동시 | 양(+) | 재고평가이익(holding gain). 1~2M lag |
| 5 | 가동률(refinery util) | 양(+) | 수급 타이트 → pricing power. Lev 1974 영업레버리지 |
| 6 | Brent-WTI 스프레드 | 중립/약 | 원유 차별(두바이 proxy). 한국 중동산 수입 |
| 7 | 디젤 크랙 > 가솔린 크랙 | 디젤 우위 | ★한국 정유 수출 ~40% 경유. Fesharaki-Wu 2018, S-Oil 사업보고서 |
| 8 | rel_mom (가격 momentum) | 음(-) reversal | 단기 가격반전(fundamental momentum과 분리). Jegadeesh 1990 |

★OW(비중확대) = crack_d3 음→양 전환 사이클 초기 + 유가 안정. UW(비중축소) = crack_d3 양→음 peak-out + 유가 급등/급락.
★FDR family = 위 8 가설(폐기분 포함). 측정 후 family 재정의 금지.

## §2. ★crack_d3 이론 검증 (data mining vs 이론 정당)

Gemini 리서치 결론: crack_d3는 **이론적으로 정당한 신호**(data mining 아님):
- crack **level** = 즉시 반영(효율적 시장) / crack **변화율(d3)** = 애널리스트 실적추정 상향 점진반영(underreaction) → 주가 forward drift.
- = PEAD(Post-Earnings Announcement Drift) 메커니즘. crack_d3가 실적발표 前 펀더멘털 모멘텀 포착.
- crack_d3(+) vs rel_mom(-) 부호반대 = fundamental momentum vs price reversal **분리**(모순 아님). "펀더멘털 개선되나 주가 미반영 = 싸고 좋은" 조합.
★단 이론 정당 ≠ 정유 데이터 입증. 통계 검증 필수(§3).

## §3. 측정 결과 (★정유 2종 단독 = SK이노/S-Oil, 가스 제외)

### 후보 13개 enumerate (team-lead 목록 완전 반영) × {d3 모멘텀, level} × y_60d (rho, OOS_rho)
| # | 후보 | d3 (rho, OOS) | level (rho, OOS) | 판정 |
|---|---|---|---|---|
| 1 | gasoline crack | -0.014, **-0.234 flip** | -0.124, -0.05 | 무신호 |
| 2 | diesel crack | -0.024, -0.145 flip | -0.214, -0.149 | 무신호(이론 디젤우위 미입증) |
| 3 | **항공유(jet) crack** | -0.039, -0.14 flip | -0.274, -0.255 | 무신호(리오프닝 미입증) |
| 4 | blended crack(3-2-1) | +0.048, **-0.239 flip** | -0.179, -0.099 | 무신호 |
| 5 | Brent-WTI 스프레드(원유차별) | +0.027, +0.258 | -0.251, +0.115 flip | 약/불안정 |
| 6 | refinery util(IP) | +0.297, +0.165 약화 | -0.279, +0.18 flip | TENTATIVE(약) |
| 7 | **brent level(유가절대)** | -0.113, -0.217 | **-0.364, -0.618 강화** | ★TENTATIVE(robust 음) |
| 8 | oil_yoy(유가모멘텀) | +0.164, +0.431 | -0.302, -0.241 | 불안정(d3/level 부호반대) |
| 9 | **usdkrw(환율)** | -0.095, +0.09 | +0.067, +0.455 불안정 | 무신호(rotation timing 무관) |
| 10 | natgas | +0.042, +0.198 | -0.022, +0.416 | 무신호(정유 무관) |
| 11 | wti level | -0.149, -0.321 | -0.349, -0.639 강화 | ★유가 음 재확인 |
| 12 | **원유/제품 재고** | — 측정불가 | — | data-gate (EIA 재고 FRED ID 불안정) |
| 13 | **OPEC 감산** | — 이벤트성 | — | enumerate (brent level로 대리 반영) |

★= **후보 13개 검토** (11개 측정 + 재고/OPEC 2개 data-gate enumerate, team-lead 목록 gasoline/diesel/항공유/Dubai-WTI/가동률/재고/OPEC/유가절대/환율 반영). ★항공유 crack = 가솔린/디젤과 동일 무신호 = 제품별 차별 미입증.

### 핵심 결과
- ★**crack_d3 (가솔린/디젤/종합) = 전부 무신호 + OOS flip** (정유 2종 단독). 이론(PEAD)은 정당하나 정유 데이터 미입증.
- ★**유가 level(brent/wti) = 음 mean-reversion 가장 robust** (-0.36, OOS -0.62 강화). = 유일하게 일관된 정유 rotation 신호.
- refinery_util d3 +0.30 but OOS 약화. oil_yoy 불안정.
- ★FDR family(m=38) survivors=0(BY 미생존). raw_p_min=0.0015(brent_level).

## §4. 판정

| 신호 | 판정 | 사유 |
|---|---|---|
| **crack_d3 모멘텀** | ★REJECTED(정유 단독) | 이론 정당(PEAD)하나 정유 2종 단독 무신호+OOS flip. v2 +0.241 = ★가스 오염(§5) |
| **유가 level mean-reversion** | ★TENTATIVE(tradeable #1) | brent/wti 음 OOS robust(-0.36→-0.62) but eff-N t=-1.96 marginal = risk-monitor(고유가 peak UW) |
| **★배당수익률 income trap** | ★PARTIAL(tradeable #2) | 음(-) eff-N t=-2.48 유의 + OOS HOLD(-0.41/-0.44) + leave-episode survive(-0.51) + 유가 partial 독립. §tradeable |
| 가동률/Brent-WTI/oil_yoy | TENTATIVE/약 | OOS 약화·불안정 |
| 디젤>가솔린 우위 | ★미입증 | 이론(수출40%)은 맞으나 정유2종 단독 둘 다 무신호 |

## §4-tradeable. ★tradeable 신호 (사용자 규칙 최소 2개, team-lead 지시 보강)

★정유 = 종목선택 영구불가(2종 과점)지만 **rotation(섹터 OW/UW) tradeable 2개 확보**:

| # | tradeable | 부호 | rho/t_eff/OOS | 메커니즘 | tier |
|---|---|---|---|---|---|
| 1 | **유가 level mean-reversion** | 음(-) | rho-0.36, t_eff-1.96, OOS-0.62 강화 | 고유가=peak-out+수요파괴(Deaton-Laroque 1992). 고유가→UW | structural_prior_low_confidence |
| 2 | **★배당수익률 income trap** | 음(-) | rho-0.41, **t_eff-2.48 유의**, OOS-0.44 HOLD | ★고배당수익률=전년호황 DPS/하락주가=정점 직후→forward약(PER peak-EPS trap의 배당버전, Damodaran cyclical). 고배당수익률→UW | structural_prior_low_confidence |

★**2 tradeable 직교성 정직 박제**: 둘 다 음 부호 + **peak-out 공통 테마**(유가 정점 / 배당 정점) → 경제적 연관(brent corr +0.42, G-G v2 |ρ|<0.3 직교 미달). ★단 배당은 유가 통제 후 partial -0.241 잔존 = **부분 독립**(완전 재포장 아님, 배당정책+valuation 정보 추가). = N_eff < 2 (단일 "peak-out" bet에 가까움) → conservative cap + hedge 강.
★**부호 사전확약 정정(HARKing 정직)**: 배당 prior = 양(고배당=저평가) 사전확약했으나 실측 음(-) = 정유 cyclical income trap으로 메커니즘 정정. 사전확약 위반 명시 + 이론(peak-EPS trap 배당버전) 근거.

★**rotation 종합 (team-lead 박제 + 2 tradeable 보강)**:
- crack_d3(가솔린/디젤/항공유/종합) = 이론 정당(PEAD)하나 정유 2종 단독선 가스 오염 제거 시 소멸 = REJECTED. v2 +0.241 = 가스 오염(§5).
- ★tradeable 2개 = (1) 유가 mean-reversion + (2) 배당 income trap. 둘 다 음(peak-out UW) + 부분 상관 = conservative cap.
- ★정유 = 종목선택 0(2종 과점) + rotation 2 tradeable(peak-out monitor, 부분 독립) = **conservative monitor 약신호 산업**. 무리한 발굴 아닌 데이터+이론 정당 2개(배당 t=-2.48 유의가 유가 t=-1.96 marginal 보강).

## §5. ★★CRITICAL: crack_d3 +0.241 패널 오염 적발

rotation-analyst v2 `load_industry('refining')` = 정유 디렉토리 prices.parquet **전체 11종**(정유2 + 가스9) 동일가중 = ★energy 광의 패널(frame§1.6 오염, supervisor가 기각한 것).

★패널별 gasoline_crack_d3 y60d 재현:
- 정유 strict2(SK이노/S-Oil) = **-0.014 (OOS -0.234 flip)** = 무신호
- 가스유틸만 = **+0.248 (OOS +0.263)** = ★신호 출처
- 에너지11종(v2) = +0.242

→ ★crack_d3 신호 = **가스/LPG 종목의 에너지가격 베타**(SK가스/E1 트레이딩), 정유 정제마진 아님. frame§1.6 분석unit 오염. 정유 단독 통합 시 ★제외 또는 "energy 광의" 재라벨 필요(supervisor).

## §6. rotation 시사 (정유 OW/UW)
- ★유가 level 높을 때(고유가 peak) → 정유 **UW**(forward mean-reversion 음). 유가 안정·바닥 → OW 고려.
- crack 모멘텀 = 정유 단독 신호 아님(가스 오염) → rotation 근거 불가.
- ★정유 rotation = 약신호 산업. 유가 peak de-risk monitor-only. 종목selection 0(2종 과점).
