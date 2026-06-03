# validation-v3-cross-sectional.md — financial(금융) §M v3

> frame v3 §M.1~M.7. raw 재현: `raw-v3/{collect, measure, collect_dart, measure_valuation, measure_cross, exposure_card}.py`.
> ★battery 대조 + regime-conditional 핵심 발견. battery summary.yaml 양식 미러.

## §0. 데이터 제약 + universe 결함 (★batch 공통 교훈)

| 데이터 | 상태 | 영향 |
|---|---|---|
| pykrx OHLCV loop | ✅ | 34종 가격 패널 (2019-2026, 1818일) |
| **DART fnlttSinglAcntAll (금융업)** | ⚠️ **2023~만** | ★IFRS 보험/은행 별도양식 → 2019-2022 status 013(데이터 없음). valuation IC n 급감 |
| FDR KRX-DESC Industry | ⚠️ **부정확** | ★"기타 금융업"에 일반 지주사(CJ/GS/HD현대) = 금융지주와 혼입 → **이름 화이트리스트 필요** |
| FDR Marcap/Amount | ✅ | 시총·ADV floor |
| yfinance ^TNX/factors | ✅ | 금리 regime + 공통인자 β |

★**universe 화이트리스트 권고 (batch 공통)**: KRX 표준산업분류는 금융지주를 일반 지주사와 같은 "기타 금융업"에 둠 → 섹터 키워드 매칭만으론 노이즈 대량 혼입. **산업별 이름 화이트리스트**(은행/보험/증권 명시 + 금융지주 화이트리스트, 우선주 제거)로 정밀 필터 = 34종 깨끗. financial 이 가장 심하나 다른 산업도 키워드 부정확 가능 → 산업별 검증 의무.

## §1. universe (§M.6)

- 정밀 필터: 순수 금융 Industry(은행/보험/재보험/신탁) + 증권(이름) + 은행(이름) + 카드/캐피탈 + 금융지주(화이트리스트) − 우선주.
- 시총≥3000억 ∧ ADV≥30억 → **34종** (은행 11 / 증권 10 / 보험 9 / 기타 3 / 카드 1). 횡단면 평균 32종.

## §2. forward 횡단면 IC (unconditional) — ★전부 비유의 (battery 대조)

4 신호 × 4 horizon = 16 테스트.

| signal__horizon | IC | t_NW | p_NW | CPCV | BY |
|---|---|---|---|---|---|
| vol_60→12M | -0.055 | -1.00 | 0.321 | 0.73 | 미생존 |
| mom_12_1→12M | -0.051 | -0.61 | 0.543 | 0.60 | 미생존 |
| rev_1m→1M_PEAD | -0.042 | -1.54 | 0.126 | 1.00 | 미생존 |
| **mom_6→12M** | **-0.006** | -0.11 | 0.910 | 0.60 | 미생존 |

★**unconditional 신호 전부 비유의** (BY 생존 0, raw_p_min=0.126). mom_6→12M IC≈0. **battery(mom_6→12M CONFIRMED +0.086)와 정반대** = 산업별 신호 상이 = 동적가중 근거.

## §3. ★regime-conditional (financial 핵심 산출)

금리 regime (US 10Y 3M Δ, ex-ante, KR proxy): rate_up 22 / rate_down 21 / rate_flat 46 month.

**mom_6 → 12M forward IC, regime별**:

| regime | mom_6 IC | n |
|---|---|---|
| **rate_up** | **+0.102** | 21 |
| rate_down | -0.054 | 19 |
| rate_flat | -0.049 | 31 |

★**금리 상승 국면에서만 모멘텀 양전**(+0.102) = 은행 NIM 수혜 가설 정합. unconditional(-0.006)이 regime 부호 반전을 가린 사례.
- ★**동적가중(derive_weights regime-conditional IC) 정당화 직접 증거** + 사용자 "지표 상관 계속 변하는 그림" 입증.
- ⚠️ **small-n (n=21 rate_up)**: TENTATIVE DIRECTIONAL. 점추정 단정 금지. regime별 block-boot CI + 추가 표본 = 후속.

## §4. valuation 횡단면 (§M.7, 데이터 제약)

DART 금융재무 312 rows(★2023~만) + pykrx 가격 → PBR/PER cross-sectional z. PIT(rcept_dt 이후).

| signal__h | IC | t_NW | n | CI_block | verdict |
|---|---|---|---|---|---|
| pbr_z→12M | -0.019 | -0.43 | 19 | [-0.097, 0.102] | TENTATIVE(저PBR value 방향, 비유의) |
| pbr_z→6M | -0.028 | -0.60 | 25 | [-0.107, 0.059] | TENTATIVE |
| per_z→24M | +0.185 | 21.2 | **7** | [0.133, 0.222] | ★INSUFFICIENT (n=7 허수, within=0, CPCV=nan) |

- **PBR(primary_metric)** = 저PBR value premium 방향(음)이나 ≈0, 비유의. coverage PBR 933 / PER 668 cells (battery PBR 2231 대비 적음 = 2023~ 제약).
- **PER 24M t=21.2 = small-n 허수** (n=7, DART 2023~). small-n rule §2: n<10 단정 금지 → INSUFFICIENT.
- ★"금융=value 우세" 분기 검증 = **DART 금융재무 2023~ 제약으로 보류** → consumer(표준계정 value 산업)로 이관.

## §5. cross (§M.3 — 산업=보고만)

- **공통인자 β**: VIX/dollar/oil/rate/credit **전부 비유의** (credit t=-1.12 최강이나 무유의). battery(credit/oil 유의) 대비 약. R²=0.115.
  - ★contemporaneous rate level β 비유의 ≠ regime effect: regime-conditional(rate 3M Δ)에선 모멘텀 IC 부호 반전. level β 와 regime 효과는 다른 축.
- **customer-supplier momentum**: financial 부적합(upstream 정의 불명확) → skip(battery=null 동일 패턴). 금융 = macro(금리/credit) regime 의존이 supply-chain 보다 dominant.

## §6. PIT + 생존편향

- PIT: 가격 forward-shift safe. valuation = rcept_dt 공시일 이후만. regime = ex-ante 금리 Δ.
- 생존편향(I축 PARTIAL): universe = FDR 현재 스냅샷. ★금융 = 합병 잦음(외환은행/하나 등 delisted 누락) → 생존편향 잔존. 34종 中 3종 부분 이력. PIT 멤버십 = collector_plan high.

## §7. exposure card (§M.7)

universe 34종 현 시점(2026-05-31) peer-relative z (sector-neutral). 상위 (mom_6_z): 미래에셋증권 +3.14 / 삼성생명 +2.54 / SK증권 +2.37. 전체 = `raw-v3/exposure-card-v3.json`. ⛔ 조립 = supervisor.

## §8. net-cost (§M.4)

KR 비대칭 왕복 33bps / 월 16.5bps. ★단 financial 은 유효 신호(unconditional) 부재로 net IC 논의 = regime-conditional 한정.

## §9. verdict

- **★financial 핵심 = regime-conditional 모멘텀** (rate_up +0.102, NIM 가설, n=21 TENTATIVE). = 동적가중 정당화 직접 증거.
- **unconditional momentum 비유의** = battery(CONFIRMED) 대조 ✅ = 산업별 신호 상이.
- **valuation** = PBR TENTATIVE / PER INSUFFICIENT (DART 금융재무 2023~ 제약). "value 우세" 분기 = consumer 이관.
- archetype = spread_driven 지지 (regime-conditional 금리 의존 입증, tentative).
- **verdict_label = TENTATIVE** (regime-conditional 발견 의미있으나 n small + valuation 데이터 제약).
- ★batch 학습: 산업마다 (a) 유효 신호 다름 (b) 데이터 양식 다름 (c) universe 키워드 부정확 → 산업별 측정·화이트리스트 필수.
