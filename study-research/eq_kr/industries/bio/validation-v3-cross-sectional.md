# validation-v3-cross-sectional.md — bio(바이오) §M v3

> frame v3 §M.1~M.7. raw 재현: `raw-v3/{collect, measure, collect_dart, measure_valuation, measure_cross, exposure_card}.py`.
> ★event_driven 신호 구조 검증 (4번째 archetype). battery/financial/consumer 미러.

## §0. 데이터 + universe

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV | ✅ | 38종 (2019-2026, 1818일) |
| DART fnlttSinglAcntAll | ✅ 2019~ 완전 (948 rows) | ★net_income 적자 36%(270/741) = event_driven |
| FDR Industry | ✅ (의약품/기초의약물질/의약용품) | 신약/제약/바이오시밀러/CMO. 의료기기 제외 |

universe = 38종 (pharma 27 / novel_drug 6 / biosimilar_cmo 5). sanity check: 삼바/셀트리온/한미약품/유한양행 = 진짜 bio.

## §1. ★event_driven 특성 (net_income 적자 36%)

- DART 948 rows 中 net_income 음수 = **270/741 (36%)**. 적자 신약바이오(HLB/펩트론/에이비엘바이오/오름테라퓨틱) = 임상단계 burn-rate.
- → PER 측정 시 적자 17종 제외 = **PER avgN 21 vs PBR avgN 33**. = ★멀티플(PER) 단독 부적합 = event_driven 입증.

## §2. forward 횡단면 IC — ★변동성 신호 (momentum 무신호)

| signal__horizon | IC | t_NW | p_NW | CPCV | within | BY |
|---|---|---|---|---|---|---|
| **vol_60→1M_PEAD** | **-0.078** | **-3.02** | **0.003** | 0.87 | 0.75 | 미세 미달 |
| vol_60→3M | -0.079 | -1.93 | 0.057 | 0.87 | — | |
| vol_60→12M | -0.098 | -1.35 | 0.181 | 0.80 | — | |
| mom_6→12M | +0.001 | 0.03 | 0.975 | — | — | 무신호 |

- ★**저변동성 신호 강**: vol_60→1M IC=-0.078, t=-3.02, **block-boot CI [-0.125, -0.022] 0 배제**, cap-weighted **-0.107**(대형 바이오 더 강), hi-ADV -0.091.
- = 고변동성(임상 베팅 신약) forward 낮음 = **임상 risk 회피 신호**. 저변동성(안정 제약) 우위.
- BY 보정(α/16=0.00313) raw_p=0.00333 **미세 미달**(거의 생존) → PARTIAL.
- momentum 전부 무신호.

## §3. valuation 횡단면 (§M.7 — event_driven 부분 작동)

DART 948 rows(2019~) → PBR/PER cross-sectional z. PIT(rcept_dt). coverage PBR 2891 / PER 1781 cells.

| signal__h | IC | t_NW | p | n | CI_block | within | avgN | verdict |
|---|---|---|---|---|---|---|---|---|
| **per_z→6M** | -0.088 | -2.32 | 0.023 | 79 | [-0.152, -0.020] | 0.86 | **21** | value premium borderline 유의 |
| **per_z→12M** | -0.091 | -2.30 | 0.024 | 73 | — | **1.00** | 21 | within 100% |
| pbr_z→24M | -0.148 | -1.14 | 0.260 | 61 | — | 0.67 | 33 | value 방향, 비유의 |

- ★**PER avgN 21(흑자 한정) vs PBR avgN 33(전종목)** = 적자 신약 PER 무효 제외 = event_driven.
- 흑자 제약사 PER value premium 작동(borderline 유의, within 높음). PBR(전종목 24M)는 방향 음이나 비유의(자본잠식 왜곡 가능).
- BY 생존 0(borderline). ★멀티플 = 흑자 sub-group 한정 = event_driven 부분 적합.

## §4. cross (§M.3)

- ★**VIX β=+0.0109, t=6.03 (강유의)** = bio 고베타 성장주(risk-on 강세). dollar/oil/rate 비유의.
  - ★**산업별 risk factor 전부 상이**: battery=credit/oil, financial=무, consumer=dollar, **bio=VIX**.
- customer-supplier momentum = skip (임상=binary 이벤트, supply-chain 무관). bio dominant = 임상 이벤트 + biotech 유동성.
- regime-conditional (XBI yoy): mom_6 IC bull -0.064 / neutral +0.051 (n small).

## §5. PIT + 생존편향

- PIT: 가격 forward-shift safe, valuation rcept_dt 이후, regime ex-ante XBI.
- ★생존편향(I PARTIAL **강**): bio = 임상 실패→상폐·관리종목 잦음. universe = FDR 현재 스냅샷(생존) → delisted bio 누락 = **IC 상향 편의 우려 강**. 38종 中 7종 부분 이력. PIT 멤버십 collector_plan high.

## §6. exposure card (§M.7)

38종 peer-relative z. 상위 mom_6_z: 삼천당제약 +2.53 / 네이처셀 +1.71. 전체 = `raw-v3/exposure-card-v3.json`. ⛔ 조립 = supervisor.

## §7. net-cost (§M.4)

왕복 33bps / 월 16.5bps. 저변동성(1M) = 회전 높음 → net haircut 주의. 흑자 PER(중기) = 회전 낮음.

## §8. verdict

- ★**bio = event_driven 부분 입증** (4번째 archetype). 멀티플(PER) = 흑자 제약사 한정 + 적자 신약(36%) 무효 제외 = 멀티플 단독 부적합. ★진짜 신호 = 변동성(임상 risk, NW 유의) + 파이프라인/임상 이벤트(collector_plan high, 미측정).
- VIX 고베타. 생존편향 강(임상 실패→상폐).
- archetype event_driven 지지 (멀티플 부적합 입증). secondary cyclical(흑자 제약 value 성분).
- **verdict_label = PARTIAL** (저변동성 NW 유의 BY 미세미달 + 흑자 PER borderline).
- ★**4 archetype 분기 완성**: battery(momentum) / financial(regime-conditional) / consumer(valuation) / bio(변동성+이벤트, 멀티플 부분) = 동적가중 정당화 + event_driven 멀티플 부적합 데이터 입증.
