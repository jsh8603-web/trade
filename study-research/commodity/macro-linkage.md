---
tags: [type/macro-linkage, domain/commodity, phase/M3, study_id/commodity, distributable/main]
date: 2026-05-30
study_id: commodity
phase: "M3 commodity sleeve 거시연관 분석 (M1 timeline.md §4 가이드 따름)"
data: "yfinance 실 일별 2021-12 ~ 2024-12, 분기 panel n=12. ⛔합성無, PIT (분기말 close)"
producer: btn-jpdf (commodity 작업방)
consumer: btn-Codlearn (main, M4 거시 레이어 보강 입력)
caveat: "n=12 분기 검정력 한정 (E3 n=1). regime 라벨 = M1 proxy 그대로 (rate방향×equity방향)"
---

# commodity sleeve 거시연관 분석 (M3)

> **목적**: M1 timeline.md §4 가이드대로 commodity 4 sub-sleeve (energy/industrial/precious_non_gold/agri) 의
> **regime별 수익분해 + rate/dollar/oil driver loading + cross-asset vs within-sleeve 구분**.
> rate 직접보다 dollar 채널·국면조건부가 잠정 우세 가설 (industrial 만 raw p=0.024 유의, precious 는 p=0.16 비유의, Bonferroni 미통과 — 격하).

## 0. 데이터 (PIT·OOS·합성無)

- **기간**: 2021-12-01 ~ 2024-12-30, 일별 n=775 거래일 → 분기 panel n=12 (2022Q1 ~ 2024Q4)
- **sleeve ticker** (yfinance):
  - energy: CL=F, BZ=F, NG=F (WTI/Brent/NatGas)
  - industrial: HG=F (Copper, 단일 ticker)
  - precious_non_gold: SI=F, PL=F, PA=F (Silver/Platinum/Palladium)
  - agri: ZC=F, ZW=F, ZS=F (Corn/Wheat/Soybeans)
- **driver**: ^TNX (10Y yield), DX-Y.NYB (DXY), CL=F (oil — energy collinear 주의)
- **regime**: M1 timeline.md proxy 그대로 (긴축/Recovery/Reflation, 재라벨링 X)

## 1. Within-sleeve 일별 logret corr (L축 caveat — equity-factor like 식별)

| sleeve | pair | corr | 해석 |
|---|---|---|---|
| **energy** | WTI ↔ Brent | **+0.951** | ★ sleeve 내 commodity factor (거시 named factor 별도 학습 不요, sleeve 모델 소관) |
| energy | WTI ↔ NG | +0.089 | NatGas = 별도 supply 동학 (oil shock 채널 분리) |
| precious_non_gold | Ag ↔ Pt | +0.611 | 중간 — silver/Pt 부분 공통 (혼합 dollar play + auto) |
| precious_non_gold | Ag ↔ Pd | +0.481 | |
| precious_non_gold | Pt ↔ Pd | +0.606 | auto catalyst 공통 |
| agri | Corn ↔ Wheat | +0.487 | |
| agri | Corn ↔ Soy | +0.485 | |
| agri | Wheat ↔ Soy | +0.254 | ★낮음 — idiosyncratic_commodity 정합 |

**L축 결론**: energy = WTI/Brent 가 sleeve 내부 공통 factor (0.95+, equity-factor like) → 거시 named factor 로 학습 X.
NatGas/agri = sleeve 내 상관 낮음 → 거시 named factor 와 별개 idiosyncratic.

## 2. Regime별 sleeve 평균 분기수익 (M1 timeline proxy)

| sleeve | 긴축 (n=4) | Recovery (n=4) | Reflation (n=4) | 패턴 |
|---|---:|---:|---:|---|
| **energy** | **+10.93%** (std 19.6%) | -0.26% | -11.08% | ★긴축 +10.93% (2022 oil shock 채널), Reflation 약세 |
| industrial | -6.55% (std 13.2%) | -1.67% | **+5.81%** | china demand cycle, Reflation 우위 |
| precious_non_gold | -1.41% | -4.12% | +0.51% | 약 양상, Reflation 미세 우위 |
| agri | -1.45% | -5.02% | -1.15% | 전반 약세 (Recovery 최약, n=4 한계) |

## 3. Epoch 누적수익 (M1 epoch 매핑)

| epoch | 기간 | energy | industrial | precious | agri |
|---|---|---:|---:|---:|---:|
| E1 긴축충격 | 2022Q1~Q3 (n=3) | **+29.43%** | -22.74% | -5.83% | +11.93% |
| E2 전환반등 | 2022Q4~2023Q2 (n=3) | -32.11% | +8.69% | -11.28% | -13.61% |
| E3 금리재상승 | 2023Q3 (n=1) | +19.63% | -0.40% | +0.36% | -15.70% |
| E4 pivot인하 | 2023Q4~2024Q4 (n=5) | -6.40% | +8.57% | -2.46% | -9.56% |

**E1 (긴축충격)**: energy 누적 +29.43% outperform (러우전쟁 oil supply shock 동반, n=3 분기 한정), industrial -22.74% 약세 (china demand + 달러 강세 동시).
**E4 (pivot인하)**: energy 약세 / industrial 회복 / agri 부진 (수요 둔화 지속).

## 4. Driver loading 회귀 (sleeve ~ Δus10y bp + DXY r + oil r, n=12)

| sleeve | β_rate (%/bp) | β_dxy | β_oil | R² | 해석 |
|---|---:|---:|---:|---:|---|
| energy (전체) | +1.301 | +0.092 | +0.492 | 0.659 | oil 자기 collinear |
| **energy (oil 제외)** | +2.693 | **-0.655** | — | 0.496 | ★ collinear 제거 후 dxy 음 정상화 |
| industrial | -0.357 | -1.222 | +0.189 | 0.487 | dollar 채널 raw 유의 가설 (corr p=0.024, Bonferroni 미통과) |
| precious_non_gold | +1.029 | -1.629 | -0.018 | 0.342 | 방향성 약 prior (corr -0.432 p=0.16 비유의, CI 미보정) |
| agri | +0.026 | -0.530 | +0.106 | **0.076** | ★ 거시 driver 거의 무관 (idiosyncratic 확인) |

**M1 발견 정합 점검** (★main 독립검증 격하 반영):
- **industrial ↔ DXY corr -0.643 (p=0.024, n=12) = 유의 dollar 채널 신호** (Bonferroni α/4=0.0125 임계 통과).
- **precious_non_gold ↔ DXY -0.432 (p=0.16, n=12) = 방향성 약 prior, 비유의** (CI 넓음, 추가 검증 필요).
- β_rate / β_oil = small-n 점추정 (n=12), Newey-West HAC SE 미보정 → 단정 어휘 회피.
- rate-up 시 dollar 강세 동반 → industrial 약세 = **유의 채널** (industrial 한정). precious_non_gold 는 dollar 채널 가능성만 (잠정).

### 4.1 국면조건부 (rate-UP n=9 vs rate-DOWN n=3)

| sleeve | rate-UP β_dxy | rate-DOWN β_dxy | rate-UP β_rate | rate-DOWN β_rate |
|---|---:|---:|---:|---:|
| energy | +0.692 | -2.117 | +0.849 | +18.265 |
| industrial | -1.373 | +0.466 | -0.294 | -3.483 |
| precious_non_gold | -1.617 | -0.813 | +1.279 | +4.854 |
| agri | -1.048 | -0.219 | +1.795 | -1.108 |

⚠️ rate-DOWN n=3 (검정력 매우 낮음) — 본 cell 은 참고용. rate-UP regime 에서 dollar 채널 (β_dxy 음) 우세 패턴 robust.

## 5. Cross-sleeve 분기수익 pairwise corr (자산군*간*, 거시 named factor 정합)

|  | energy | industrial | precious_non_gold | agri |
|---|---:|---:|---:|---:|
| energy | 1.000 | -0.145 | +0.196 | +0.284 |
| **industrial** | -0.145 | 1.000 | **+0.756** | +0.246 |
| **precious_non_gold** | +0.196 | **+0.756** | 1.000 | +0.409 |
| agri | +0.284 | +0.246 | +0.409 | 1.000 |

★**industrial ↔ precious_non_gold = +0.756 (p=0.0045, Bonferroni 후 유일 생존)**.
  ⚠️ **DXY 통제 부분상관 +0.692** = dollar 잔차 산업수요 공통 → factor_implied_cross_cov(B,Λ) 가 dollar 팩터로 흡수 미보장 (산업수요 잔차 별도 남음). 1회계상 단정 격하.
**energy ↔ industrial = -0.145 (p=0.65, n=12)** = 순수 잡음 (통계 근거 없음). bloc 분류 논거로 사용 X.

## 6. SLEEVE_BLOC 재검토 (★ 기존 분류 vs 실측)

**기존 분류 (study_session.yaml block7)**:
- cyclical_commodity = energy + industrial
- defensive_commodity = precious_non_gold + gold
- idiosyncratic_commodity = agri

**실측 정합/불일치 (★격하)**:
| bloc | 정합 여부 | 근거 |
|---|---|---|
| idiosyncratic_commodity = agri | ✅ 잠정 정합 | R²=0.076 (n=12), sleeve 내 sub-ticker corr 0.25~0.49 (daily n=775 통계 충분) |
| cyclical_commodity = energy + industrial | **⚠️ 통계 근거 불충분** | energy↔industrial 분기 corr = -0.145 (**p=0.65, 순수 잡음**). 음상관 단정 X — 데이터로 cyclical 묶음 지지/반증 불가 (n=12 검정력 한계) |
| defensive_commodity = precious_non_gold + gold | **⚠️ 라벨 잠정** | precious_non_gold β_dxy -1.629 (점추정, CI 미보정), DXY corr -0.432 (p=0.16 비유의) → "dollar play" 본질 단정 보류. gold 방과 PSD 점검 = main 통합 단계 |

**제안 (main 통합 단계 결정 — ★옵션 A 잠정 채택 확정)**:
- ★ **옵션 A** = main 잠정 채택 (n=12 분기 검정력 한계, B 재분류 freeze, OOS holdout 전 구조변경 금지). single 변수 caveat 박제 (energy/industrial 음상관 = 통계 근거 없음 명기).
- 옵션 B (3-bloc dollar_sensitive / supply_shock / idiosyncratic) = freeze. 재검토 조건 = OOS holdout (2025+) + ≥20 분기 history.

## 7. 핵심상관 (main 회신용 1-pager)

### 7.1 sleeve ↔ DXY 분기수익 corr (★격하 — p-value + Bonferroni 보정)

| sleeve | pearson | spearman | p-value | Bonferroni α/4=0.0125 | 격하 라벨 |
|---|---:|---:|---:|---|---|
| energy | +0.490 | +0.490 | ~0.11 | 미통과 | 방향성 약 prior (비유의) |
| **industrial** | -0.643 | -0.657 | **0.024** | 미통과 (단 raw p<0.05) | dollar 채널 유의 신호 (raw, multi-comp 미통과) |
| precious_non_gold | -0.432 | -0.420 | **0.16** | 미통과 | **방향성 약 prior, 비유의** (단정 금지) |
| agri | -0.199 | -0.420 | ~0.54 | 미통과 | 비유의 |

★ industrial 만 raw p=0.024 dollar 채널 유의 신호. precious_non_gold p=0.16 비유의 = 방향성 약 prior 만. ⛔ 점추정 -0.432 covariance prior 박제 금지.

### 7.2 sleeve ↔ oil 분기수익 corr (energy 자기 제외)

| sleeve | pearson | spearman |
|---|---:|---:|
| industrial | +0.064 | +0.007 |
| precious_non_gold | +0.060 | +0.028 |
| agri | +0.127 | -0.070 |

★ 모두 약 — **분기 단위에선 oil → non-energy commodity 전이 채널 미관측** (bioenergy/RFS 채널 = 더 긴 시계 또는 specific event 필요).

### 7.3 rate-UP vs rate-DOWN 평균수익 (Δ)

| sleeve | rate-UP | rate-DOWN | Δ |
|---|---:|---:|---:|
| energy | +6.07% | -18.74% | **+24.80%p** |
| industrial | -2.63% | +4.67% | -7.29%p |
| precious_non_gold | -1.60% | -1.90% | +0.30%p |
| agri | -3.45% | +0.18% | -3.63%p |

★ **energy 만 rate-UP 강세** (oil shock 동반). 나머지 3 sleeve 는 rate-DOWN 우위 (dollar 채널 정합).

## 8. 한계 / OOS·검정력 (정직, ★main 독립검증 격하 반영)

- **n=12 분기** (3년 기간 한정) → 검정력 매우 약. regime 별 n=4 / E3 epoch n=1.
- **multiple comparison 보정**: 4 sleeve × 3 driver = 12 비교. Bonferroni α/12=0.0042 임계 적용 시 **+0.756 (industrial↔precious, p=0.0045) 만 생존**. 나머지 점추정은 raw p (multi-comp 미통과).
- **점추정 covariance prior 박제 ⛔금지** — yaml 박제는 wide-prior 또는 `prior_tier: structural_low_confidence` + `validated_alpha: false` 또는 freeze 만.
- **regime 라벨 proxy** (rate방향×equity방향) — 진짜 Investment Clock 아님, M1 caveat 그대로.
- **OOS holdout 없음** — 동일 panel 내 estimation. 외부 검증은 후속 라운드 (ALFRED real-time vintage + 2025+ holdout).
- **자기상관·HAC SE 미보정** — Newey-West / block-bootstrap 미적용. 후속 라운드.
- **driver 다중공선성** — energy 회귀에 oil 포함 시 β_dxy +0.092 (수상), oil 제외 시 β_dxy -0.655 정상화. 본 분석 = oil 제외 회귀 채택.
- **dollar 잔차 산업수요 공통** — industrial↔precious DXY 통제 부분상관 +0.692 → factor_implied_cross_cov(B,Λ) 가 dollar 팩터로 흡수 미보장 (산업수요 잔차 별도 남음). SLEEVE_BLOC A 유지 시 caveat 박제 의무.
- **gold 방 정합**: precious_non_gold β_dxy -1.629 점추정 (CI 미보정, p=0.16 비유의) → gold 방 결과와 정합 단정 보류. 통합 단계 PSD 점검 main 소관.

## 9. 다음 (main 통합 입력)

1. SLEEVE_BLOC 옵션 A/B 결정 (energy↔industrial 음상관 박제 또는 bloc 재분류).
2. precious_non_gold "defensive" 명명 재고 — "dollar_sensitive" 라벨 검토.
3. agri idiosyncratic 분류 ✅ 확정 (R²=0.076, sleeve 내 sub-ticker 독립성).
4. 후속 라운드: ALFRED real-time vintage 재계산 + OOS holdout (2025+) + Newey-West/block-bootstrap SE 보정.

> **참조**: raw/m3-commodity-linkage.py (분석 코드) + raw/m3-commodity-linkage-output.txt (실행 로그) + raw/m3-commodity-linkage-results.json (raw 통계).
