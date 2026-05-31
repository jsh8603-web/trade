---
tags: [type/consult-response, study/eq_us_cyclical, round/2, source/gemini-pro-web]
date: 2026-05-30
model: GeminiPro
response_len: 4812
---
# Round 2 — Gemini Pro 응답

## BLUF
- Q1: **BOCD (Bayesian Online Change Detection, Adams-MacKay 2007)** 최우선. 실무 안정성 원하면 BMA 룰베이스.
- Q2: 중기 정상화 마진 회귀(섹터 평균 EBIT × 자체 매출). **Fair Multiple은 절대 가치평가(할인율 모형) 역산**으로 순환 차단.
- Q3: EBP 원본 = Fed 공식 비정기. **실시간은 HY OAS 잔차 자체 추정**. ISM은 유료화 장벽 → 지역 연은 1차 PCA 프록시.
- Q4: 단순 곱 위험. **Cameron-Gelbach-Miller (2011) 이원 군집 SE**가 표준. Newey-West q≥4 + Politis-Romano stationary bootstrap.

## Q1. Regime — Ex-ante Filtered
| 대안 | 추천 |
|---|---|
| HMM Filtered (Hamilton 1989 Forward only) | 기본 대안 |
| **BOCD (Adams-MacKay 2007)** | ★최우선. Run-length 사후확률 업데이트 → b(t)가 과거 확률 수정 X → e-process supermartingale 정확 부합 |
| BMA + Rule-based | 백업, OOS 방어 |

(b) 입력 변수: T10Y2Y, 신용(EBP 프록시), 지역 연은 신규주문-재고 스프레드, DTWEXBGS(달러), **OFR FSI (글로벌 금융스트레스)** — multi-sector 확장 시 강건성↑.

(c) 함정: HMM label-switching 치명. 매크로 발표 lag 무시한 reference date 정렬 = look-ahead 바이어스.

(d) Metric: **Brier Score + Log-predictive density**. Regime Hit Rate는 이진화 정보손실로 보조만.

## Q2. Normalized Earnings
(a) **중기 정상화 마진 회귀(섹터 평균 EBIT × 자체 매출)**. 매출은 하방 경직성 → 1주기 평균 EPS는 구조 성장 과소평가(역 peak_trap) → 매출×섹터 마진이 현실적.

(b) 윈도 7-10년 롤링 + **NBER 침체 최소 1회 포함되도록 동적 확장(Expand) 하이브리드**.

(c) ★동어반복 회피: Fair Multiple을 피어 그룹 상대가치로 산출 금지. **내재 자본비용 모형 역산**:
```
Fair P/E = (1 - b) / (r_e - g)
b=유보율, r_e=내재 자본비용, g=장기 성장률
```
스팟 P/E와 **완벽히 독립된 축**.

(d) 검증: σ(P/E_norm)/σ(P/E_spot) < 0.5. fwd 12M Rank-IC가 스팟 역전 현상에서 양 유지.

## Q3. EBP·ISM 실무 경로
(a) **EBP**: FRED 실시간 X (Fed 연구 섹션 비정기). **자체 프록시 = HY OAS(BAMLH0A0HYM2)를 BAA-AAA spread + VIX(VIXCLS)로 직교화한 잔차**.

(b) **ISM**: NAPMNOI 무료 삭제. **대체 = Philly Fed(BOSNO 신규주문) + Empire State 제조업 1차 PCA**.

(c) PIT: 모든 매크로 = **Release Date 기준 t 인덱싱** (3월 reference, 4/15 발표 → 4/15 종가 매핑).

(d) 최소 시계열: **300개월(25년, Dot-com/GFC/코로나 3사이클)**.

## Q4. Effective-N + 중첩 보정
(a) 횡단:
```
N_eff = N / (1 + (N-1)·ρ_c)
```
반도체 ρ_c≈0.5, N=40 → **N_eff ≈ 1.95** (★급감).

(b) 시계열 (AR(1)):
```
T_eff = T·(1 - ρ_s) / (1 + ρ_s)
```
fwd 12M overlap → ρ_s 매우 높음.

(c) **결합 단순 곱 X** (꼬리 두께 미반영) → **Cameron-Gelbach-Miller (2011) Double-clustered SE by firm and time** 표준.

(d) Newey-West q: 기본 `q=⌊4(T/100)^(2/9)⌋` + **fwd 12M 분기 → q≥4 강제** (월간 → q≥12). Overlap MA 구조 필연.

(e) **Politis-Romano (1994) Stationary Bootstrap** (블록 길이 기하분포, 정상성 보장). 평균 블록 길이 λ^(-1) ≥ 12M.

## ⚠️ Multi-sector 확장 함정 (★v1→v2)
반도체 자본 사이클이 헬스케어/유틸리티에 기계적으로 안 맞음. 섹터별 β 고정 시 **CMA 민감도 극적 변화** → 전체 IC 0 수렴(shrinkage). **TVP-VAR 또는 섹터 더미 교호작용** 필수.
