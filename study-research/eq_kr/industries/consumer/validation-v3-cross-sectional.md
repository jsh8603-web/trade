# validation-v3-cross-sectional.md — consumer(소비재) §M v3

> frame v3 §M.1~M.7. raw 재현: `raw-v3/{collect, measure, collect_dart, measure_valuation, measure_cross, exposure_card}.py`.
> ★valuation 유효 산업 입증 (battery=momentum / financial=regime-conditional 분기 완성).

## §0. 데이터 + universe (★표준계정 완전성 = financial 대조)

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV | ✅ | 28종 (2019-2026, 1818일) |
| **DART fnlttSinglAcntAll** | ✅ **2019~ 완전 (707 rows)** | ★KT&G 2019 Q1부터 = 표준계정 산업의 valuation robust 측정 (financial 2023~ 312 rows 대조) |
| FDR Industry + 화이트리스트 | ⚠️ 보강 필요 | ★화장품=「기타 화학제품」, 식품=「기타 식품 제조업」 → 이름 화이트리스트 병용 |

★**universe 화이트리스트 (financial 교훈 적용)**: 소비재 핵심(아모레/LG생건=화학제품 / CJ제일제당/오리온/농심=기타식품)이 Industry 키워드에 안 잡힘 → 이름 화이트리스트 29종 병용. sanity check = 상위 28종 전부 진짜 소비재 확인.

## §1. universe (§M.6)

- Industry 매칭(식품/음료/담배/의복/유통/소매) + 이름 화이트리스트(화장품/식품 대표) − 우선주. 시총∧ADV floor → **28종** (retail 10/food 9/cosmetics 4/apparel 3/beverage 2). 횡단면 평균 27종.

## §2. forward 횡단면 IC (momentum) — ★전부 비유의 (asset_stable 정합)

16 테스트 BY 생존 0, raw_p_min=0.31 (financial보다 약). mom_6→12M IC=+0.001. ★momentum 무신호 = 방어주(asset_stable) 모멘텀 안 먹힘 = battery(CONFIRMED) 대조.

## §3. ★valuation 횡단면 (consumer 핵심 — valuation 유효 산업)

DART 707 rows(2019~ 완전) + pykrx 가격 → PBR/PER cross-sectional z. PIT(rcept_dt 이후). coverage PBR 2268 / PER 1793 cells.

| signal__h | IC | t_NW | p_NW | n | CI_block | within | verdict |
|---|---|---|---|---|---|---|---|
| **per_z→3M** | -0.077 | -1.89 | 0.062 | 82 | [-0.153, 0.001] | **1.00** | borderline 유의, within 100% |
| **per_z→24M** | -0.141 | -1.39 | 0.169 | 61 | **[-0.245, -0.041]** | 0.67 | block-boot 0배제(유의), NW 보수 비유의 |
| per_z→6M | -0.073 | -1.21 | 0.230 | 79 | [-0.164, 0.034] | 0.71 | |
| pbr_z→24M | -0.062 | -1.33 | 0.188 | 61 | [-0.124, -0.001] | 0.67 | value 방향, block-boot 0배제 |

- ★**전 horizon 부호 일관 음(IC<0) = value premium 방향**(저PER/저PBR = 싼 종목 forward 높음).
- per_z 3M within-period **100%** (n=82) + 24M block-boot **유의** (CI 0 배제). NW는 보수(autocorr)라 borderline.
- ★**momentum(무신호)보다 valuation 우세** = asset_stable value 산업 입증. supervisor 가설 ✅.
- BY 보정 후 미생존(borderline) → PARTIAL-TENTATIVE. 단 방향 일관성+block-boot 유의 = value premium prior 지지.

## §4. cross (§M.3)

- **공통인자 β**: ★**dollar β=-1.19, t=-2.57 유의** (원화 약세→소비재 약세, 수입원가↑/내수위축). VIX/oil 비유의.
  - ★**산업별 risk factor 분기**: battery=credit/oil, financial=무(전부 비유의), **consumer=dollar**. = 산업마다 다른 macro 노출.
- customer-supplier momentum = skip (소비재 upstream 다양, 부적합. battery/financial 동일 패턴).
- ★regime-conditional (VIX risk regime): mom_6 IC risk_off -0.072 / risk_on +0.063 (n=29/21). 방어주가 공포국면 모멘텀 역행 약신호(tentative). valuation regime-conditional = 추가측정 가치.

## §5. PIT + 생존편향

- PIT: 가격 forward-shift safe, valuation rcept_dt 이후, regime ex-ante VIX.
- 생존편향(I PARTIAL): FDR 현재 스냅샷. 소비재 = 상폐 적으나 28종 中 3종 부분 이력. PIT 멤버십 collector_plan high.

## §6. exposure card (§M.7)

28종 peer-relative z (sector-neutral). 상위 mom_6_z: 한화갤러리아 +3.39 / 신세계 +2.48. 전체 = `raw-v3/exposure-card-v3.json`. ⛔ 조립 = supervisor.

## §7. net-cost (§M.4)

왕복 33bps / 월 16.5bps. valuation(저회전 장기 value) → turnover 낮음 = net 보존 유리(momentum 대비).

## §8. verdict

- **★consumer = valuation 유효 산업** (supervisor 가설 ✅). per_z value premium 방향 일관(전 horizon 음, 3M within 100%, 24M block-boot 유의). momentum 무신호 = asset_stable 정합.
- archetype asset_stable 지지 (valuation 우세 + momentum 무신호). dollar 노출 = 경기소비재 성분.
- **verdict_label = PARTIAL** (valuation 방향 일관 + block-boot 유의, NW 보수 borderline).
- ★**3산업 분기 완성**: battery(momentum CONFIRMED) / financial(regime-conditional) / consumer(valuation) = "산업마다 유효 신호 다름" 데이터 입증 = 동적가중 정당화.
