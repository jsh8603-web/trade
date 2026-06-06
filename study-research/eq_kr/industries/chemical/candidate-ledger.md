---
tags: [type/candidate-ledger, domain/equity, sector/chemical, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# chemical 지표 후보 원장

## ✅ 채택 (yaml 등록 + 검증 통과/tradeable)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| **vol_60** (저변동성) | low_volatility | medium (Tentative) | conditional y_60d IC -0.142, wc_p 0.0005, BY 생존, OOS HOLD, size-orth -0.169, t_obs(neff) 3.14 WELL. ★최강 tradeable |
| **per_z** (저PER value) | value | medium-low (Tentative) | valuation 6M IC -0.218, t_NW -3.87, BY 생존(6M/3M/12M), OOS HOLD, CPCV 1.00. ★size-orth 절반(-0.110)+small-n haircut. ★auto/반도체와 반대(peak-EPS trap 화학 약) |
| **mom_6** (역모멘텀 reversal) | momentum_reversal | low-medium | conditional y_60d IC -0.115, wc_p 0.0005, BY 생존, OOS HOLD, size-orth -0.146. cyclical 정점 reversal(반도체 동형) |

## ⏳ 이연 (식별됐으나 미투입)

| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| inv_ratio (재고순환) | H3 theory §5 | unconditional ≈0, KRW_neutral 국면만 음(-0.105 wc_p 0.024), 단일 FDR BY 미생존(36셀 multiplicity) | regime-conditional만 활용 OR n 확대 후 재측정 |
| mom_12_1 (12-1M momentum) | H8 | y_60d IC -0.101 BY 생존이나 mom_6과 강상관(중복) | mom_6 대표로 충분, 별 등록 불필요 |
| 에틸렌-납사 spread | theory §1·§5 | ★데이터 미수집 (ICIS/Platts 유료) — 화학 cycle 핵심 timing 변수 | collector_plan high → spread 모멘텀 regime 변수로 vol/mom 강화 측정 |
| 중국 화학 PMI / 수입가 | theory §3 | 데이터 미수집 (구조적 역풍 변수) | Caixin PMI 무료 + 관세청 수입가 수집 후 regime 변수 |

## ❌ 미채택 / 기각 (REJECTED)

| 후보 | 사유 |
|---|---|
| **capex_ratio** (H1 ★auto 인계 최우선) | ★**REJECTED** — uncond IC ≈0(+0.0017 wc_p 0.96), size-orth도 ≈0, OOS flip. **auto의 robust 음 신호(t=-3.38) 화학 미재현**. 진단(정밀) = 종목별 capex **분산은 존재**(cross-sectional CV 0.241, 범위 0.236~0.617)하나 **forward 예측력 부재**(panel n_obs=1312 powered인데 IC≈0 = 측정 못함 아니라 예측력 없음). steel은 within=0.96 selection 유효(근본 차이). ⇒ capex 유효성 = 산업 동시 cycle 단정 아니라 **forward 예측력 실측 의존**(auto/steel 유효 / 화학 무예측) |
| **ppe_yoy** (H2 유형자산 yoy) | REJECTED — prior 음인데 y_5d +0.059(부호 반대), horizon 비단조, y20 OOS flip. artifact |
| **inv_yoy** (H4 재고 yoy) | REJECTED — prior 반대 부호(+0.111 KRW_neutral) + 비유의 |
| **rnd_ratio** (H5 무형/assets) | REJECTED — 비유의(+0.019~0.030 wc_p 0.38~0.81). 화학 commodity 위주 R&D 차별화 약 |
| **rev_1m** (H9 단기 reversal) | 약 reversal(uncond -0.042 wc_p 0.23) but BY 미생존 = TENTATIVE, 미등록 |
| **pbr_z** (H6) | 12M IC -0.123(BY 미생존), per_z보다 약 → per_z 대표(화학은 PER value 우위). 단 pbr_z 12M size-orth -0.098 잔존 = 약 보조 |
| oil/global-materials cycle 선행 (DY) | measured-null (lead-lag corr<0.1 p>0.3). 유가-화학 spread 매개라 직접 선행 약. skip 기록 |
| customer-supplier momentum | null (frame M.10 battery 패턴) — skip 기록 |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| vol_60 (저변동) | n=17 small-n magnitude 신뢰 낮음. cyclical 고베타인데 low-vol anomaly 강함이 의외 | PIT universe 확장 + 2번째 down-cycle OOS 재현 |
| per_z (value) | size-orth IC 절반 = small-cap value 절반 위장. peak-EPS trap 화학 약 mechanism 미확정 | size-double-sort + 화학 EPS 변동 진폭 vs 반도체 비교 |
| mom_6 (reversal) | t_obs(neff) 2.48 underpowered (OOS hold로 tradeable이나 약) | n 확대 후 재측정 |

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | vol_60 / per_z / mom_6 (PASS-conditional, conservative cap) | 검증된 정량 규칙 (small-n cap) |
| memory | ★capex 일반화 가설 화학 기각 (분산 존재 CV 0.241하나 forward 무예측, steel within=0.96 유효와 대비) | 다음 cycle prior 정정: capex anomaly 유효성은 산업구조 단정 아니라 forward 예측력 실측 의존(auto/steel○ 화학✗) |
| memory | ★PER value premium > PBR (화학 peak-EPS trap 약) | archetype 내 valuation metric 이질성 — cyclical도 PER 적합도 산업별 상이 |
| observe-only | inv_ratio (regime-conditional KRW_neutral) | N 더 누적 후 promotion |
| evt | (G-B 재자문 미발동 — BY 생존 신호 있어 트리거 X) | — |
| pointer | 에틸렌-납사 spread 수집 = 다음 화학 세션 SSOT 정독 우선 | cycle timing 변수 부재가 최대 gap |

## 🔄 ROTATION 신호 (업종 비중 timing, 종목 selection과 별 차원)

### 채택 1 STRONG 단일 (★mom_3 보조 G-C 재audit hard-fail 폐기, 2026-06-06)
| 신호 | 채널 | 방향 | rho(y60d) | 직교성 | 판정 | 근거 |
|---|---|---|---|---|---|---|
| spread(china−brent/naphtha) | demand(margin) | 양(margin↑→OW) | +0.539/+0.450 (strict NCC +0.427/+0.354) | china와 0.77(대표) | ★STRONG primary 단일 | full+strict OOS+mag. 증권 "스프레드=통합 KPI". margin=demand-cost |
| ~~mom_3_residualized~~ | ~~momentum~~ | ~~양(추세)~~ | ~~+0.385~~ | — | ❌**폐기(hard-fail)** | ★G-C 재audit(2026-06-06): residualize가 usdkrw+brent만, **시장 KOSPI momentum 누락** → 외부시장 resid 시 IC +0.385→**+0.02 붕괴**(corr 0.829)=**market×beta 재포장**(공통인자 재포장). "공통macro residualize 생존" 주장은 시장 momentum 미통제 artifact. 사용자 "둘다해"(보조 채우기) 지시에도 audit hard-fail 우선 = 정직 폐기 |

### 보조/미채택 (사유 박제)
| 후보 | rho | 사유 |
|---|---|---|
| china_mchi/china_fxi | +0.458/+0.347 | OOS robust이나 spread와 같은 demand 채널(corr 0.77) = spread로 대표(중복 베팅 회피) |
| pbr_z_valband | +0.550 | OOS robust 강하나 mom3_resid(0.58)/china(0.52) 중복 = 독립 베팅 약 → valuation-band guard(보조)로만 |
| naphtha_yoy / brent_yoy | -0.375/-0.403 | cost-push 변동성(v2 -0.367 재현), OOS mag약 + strict NCC OOS flip = 방향 본질 아님. secondary |
| mom_3_raw | +0.402 | residualize 전 = 공통인자 재포장 의심 → residualized(+0.385)로 채택(raw는 미사용) |
| usdkrw_yoy | -0.163 | ❌REJECTED — prior(양) 반대 + OOS flip |
| kr_exports_yoy | -0.077 | ❌REJECTED — 비유의(wc_p 0.47) |
| naphtha_d3 / china_fxi_d3 | ~0 | ❌REJECTED — 3M 변화 무신호/OOS flip |

★rotation 결론(2026-06-06 G-C 재audit 반영): 화학 업종 비중 timing = **STRONG 단일(spread)**. mom_3_residualized 보조는 market×beta 재포장(시장 momentum 미통제 artifact)으로 **폐기** = 채택 2 → 채택 1. 후보 11개 측정 / 채택 1(+valuation-band guard 1) / REJECTED 4 / secondary 2 / **폐기 1(mom_3)**. spread는 이론(증권 "스프레드=통합 KPI")+통계+OOS 견고로 단일이라도 robust. ⛔구조 사유 박제: cyclical 화학의 momentum은 시장 베타와 분리 불가 = 단일 채택이 정직(억지로 2개 맞추려다 artifact 박제 회피). rotation-signals.md.
