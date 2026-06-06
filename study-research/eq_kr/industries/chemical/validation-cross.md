---
tags: [type/validation, domain/inv, scope/equity-kr, sector/chemical, layer/cross]
date: 2026-06-05
owner: chem-analyst@kr-equity
purpose: cross 축 (공통인자 β + cycle 선행 spillover) + PIT 보고지연. raw = raw-v3/measure_cross.py → validation-cross-v3.json.
---

# 화학 validation — cross (분석 단위 간 상관 + 공통인자)

## 1. common_factor_exposure (동시 β, HAC maxlags=3, n=35)

| factor | β | t | CI95 | 해석 |
|---|---|---|---|---|
| VIX | -0.0013 | -0.12 | [-0.022, 0.020] | 비유의 |
| dollar | -1.452 | -1.01 | [-4.27, 1.37] | 음 방향(약) — 강달러→화학↓ (수출주, theory 정합이나 비유의) |
| **oil** | +0.111 | +0.97 | [-0.114, 0.335] | **양 방향(약)** — 유가↑→화학↑ (spread 매개, 수요견조 전제, 비유의) |
| rate | -0.044 | -0.50 | [-0.214, 0.127] | 비유의 |
| credit | -0.082 | -1.38 | [-0.199, 0.035] | 음 방향(약) — 신용스프레드↑→화학↓ (cyclical risk-off, 비유의) |

- ★전부 비유의 (n=35 작음). 방향성: oil(+)·dollar(-)·credit(-) = 화학 = 경기민감 수출주 prior 약 정합.
- ★credit β = US HY OAS proxy (KR HY 부재) → collector_plan. r2=0.168.
- ⇒ 통합 supervisor Σ_return 입력 = oil/dollar/credit 약 노출 보고 (1회 계상, L축).

## 2. cycle 선행 spillover (directional_spillover 후보, G-A 빈 [] 금지)

> 화학 cycle 선행 = 유가(원재료 납사)·글로벌 화학/소재 cycle lagged 3M momentum → 한국 화학 forward 1M.

| 선행 변수 | lag0 corr(p) | lag1 | lag2 | lag3 | verdict |
|---|---|---|---|---|---|
| oil_wti (납사 원재료) | +0.034 (0.76) | -0.008 | -0.047 | -0.100 (0.37) | **null** |
| global_materials (VAW) | +0.006 (0.96) | +0.038 | +0.088 (0.43) | +0.036 | **null** |
| us_materials (XLB) | -0.025 (0.82) | +0.031 | +0.089 (0.42) | +0.021 | **null** |

- ★**cycle 선행 spillover = 전부 null** (corr <0.1, p>0.3). 유가/글로벌 소재 cycle lagged → 한국 화학 forward 예측력 부재.
- ★해석 (frame M.10 battery 패턴): 유가-화학 = spread 매개라 직접 lead-lag 약 (theory-notes §1 부호 모호 prior 정합). 동조 성분은 contemporaneous(common factor oil β)로만, forward 선행 신호 X. **null → skip 기록** (통합 단계 재검토 여지).
- ⇒ directional_spillover 후보 = 보고했으나 **측정 null** (빈 [] 아님, measured-null + 후보 3종 명시).
- ★supply-chain structural linkage(I-O centrality) = frame M.3 optional 최하위 → skip (산업별 매번 X, 통합 단계).

## 3. PIT 보고지연 (O축 leakage 차단)

- DART 사업보고서 median delay: 2021~2025 **108~120일** (FY-end 후). → 펀더멘털 신호 rcept_dt 이후만 적용 (measure_*.py 전부 PIT).
- 가격 신호(mom/vol)는 PIT-safe (보고지연 무관).

## 4. summary (cross)

- common factor = oil(+)/dollar(-)/credit(-) 약 노출 (비유의, n=35). 통합 cross 조립 입력.
- directional_spillover = 유가/글로벌소재 cycle 선행 **null** (후보 3종 보고 + measured-null).
- ⇒ 화학 = 공통인자 노출·cross 선행 모두 약 → 종목 selection 신호(vol/mom reversal/per value)가 capsule 본체. cross는 risk 노출 보고용.
