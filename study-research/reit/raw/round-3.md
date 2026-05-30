---
tags: [type/raw-round, study_id/reit, round/3, source/synthesis]
date: 2026-05-30
round_focus: ③가설 초안 + 반증조건 종합 — R1+R2 합성
note: STUDY-KIT §2 v2 자문 라운드 3 (수렴 라운드). 새 검색 없이 R1+R2 발견을 가설로 정련.
---

# Round 3 — 가설 초안 + 반증조건 정련 (수렴 라운드)

## A. 라운드 목적

R1 (이론 수집) + R2 (이론 검증) 의 발견을 **반증가능 가설 + 반증조건** 형식으로 정련.
STUDY-KIT §2-1 의 ③ 산출 = 가설 초안 + 반증조건. 이 라운드 후 direction.md 종합 → main 승인 게이트.

## B. 수렴 판정 자가 점검 (다회 라운드 종료 기준)

- R1: REIT 가격결정 4 approach + 2024 sub-sector 실측 → 단순 매핑 반증 사례 식별 ✓
- R2: 학술 합의 inconclusive + 시변 자본구조 + window flip → v1 lens 단정 결함 식별 ✓
- R3 (본 라운드): 위 발견을 반증가능 가설로 reframe ✓

**더 물을 것 있나** (자가 체크):
- ✅ 가격결정 framework 4 approach (NAV/FFO/AFFO/DCF) 확보 — 2-2 정독 대상 명확
- ✅ Cross-sectional + time-series 검증 방법론 — academic refs 식별
- ✅ Window 길이 효과 — 2025 12월 데이터로 직접 검증
- ⚠️ Stagflation 1970s data — Round 1 빈틈 잔존 (2-2 단계 정독 시 채움)
- ⚠️ 환각 검증 미완 (243bp/120bp + 2024 industrial -17.7%) — 2-2 에서 cross-verify

→ 5R 까지 갈 만큼의 critical gap 없음. **3R 수렴 적정** (3~7R 범위 하단).

## C. 핵심 가설 5종 (H1~H5) + 반증조건

각 가설 = (a) 명제 (b) evaluation window (c) confirm signal (d) reject signal (e) v1 단정과의 차이.

### H1. Rate-shock window 내 long-WALT REIT cross-sectional underperformance
- **명제**: Rate-shock window (10Y 4w Δ > +50bp) 진입 후 90d 동안, long-WALT REIT (top tertile)
  가 short-WALT REIT (bottom tertile) 보다 cross-sectional total return 으로 낮다.
- **window**: 60-90d cumulative, rolling, rate-shock 라벨 conditional.
- **confirm**: 24m rolling cross-section Rank-IC (WALT_rank vs forward_60d_return) < -0.05 평균.
- **reject**: e-CUSUM 단측 (baseline -0.05 위로 mean-reversion) e-value ≥ 20 (Ville α 0.05).
- **v1 단정과의 차이**: v1 는 "β_rate -1.0 ~ -2.0" 정량 단정. H1 은 cross-section *부호*만 단정,
  정량은 데이터에 위임. WALT 가 검증 가능한 ticker-level stratifier (Round 2 학술 cross-section
  evidence 와 정합).

### H2. Implied-private cap rate spread mean-reversion (12m forward)
- **명제**: implied cap rate − private appraisal cap rate spread Z-score < -1.5 (압축) → 12m
  forward REIT total return Rank-IC > +0.15.
- **window**: 12m forward, Q-end 시그모이드 가중.
- **confirm**: 12m forward total return Rank-IC 양 + e-value 누적 > 20.
- **reject**: (a) OOS Rank-IC e-CUSUM 단측 붕괴, 또는 (b) deep discount (Z<-2) 가 6Q 이상 지속
  하며 미회복 → "새 normal anchor" 가설 (regime change).
- **v1 단정과의 차이**: v1 는 mean-reversion 단정. H2 는 reject 의 (b) 가 곧 가설 자체의 폐기로
  이어짐 — structural break (regime change) 도 명시.
- **★ 환각 의존**: Round 1 의 243bp/120bp 수치는 primary 미검증. 2-2 단계에서 cross-verify 후
  baseline 정수치 확정.

### H3. Debt maturity profile stratification (rate-shock attenuation)
- **명제**: debt weighted-average maturity > 5y REIT 가 rate-shock window 시 < 3y REIT 보다 *덜*
  떨어진다 (Round 2 학술 "pre-2022 debt extension → rate sensitivity 완화" 일관).
- **window**: rate-shock window 30-90d cumulative.
- **confirm**: cross-section debt-maturity_rank vs rate-shock 60d return Rank-IC > +0.05 평균.
- **reject**: 2022~2024 cross-section 에서 정반대 부호 (e-value ≥ 20).
- **v1 단정과의 차이**: v1 는 leverage_debt_ebitda 만 (자본구조 *량* 만). H3 는 자본구조의
  *기간 (term structure)* 도 stratifier 로 추가. Round 2 c-3 발견 직접 반영.

### H4. Window-conditional sector return flip (단일 매핑 무효)
- **명제**: REIT sub-sector ranking 은 evaluation window 길이 (1d/30d/12m/24m) 에 따라 flip.
  특정 sector 의 "regime → outperform" 단정 매핑은 multi-window 평균에서 무력화된다.
- **window**: 1d vs 30d vs 12m vs 24m 동시 산출 비교.
- **confirm**: 임의 sector 의 (YTD ranking) - (단일월 ranking) cross-tabulation 의 mean swap
  rate > 30% (즉 sector 의 1/3 이 단일월 vs YTD 에서 ranking 1+ tier flip).
- **reject**: window 길이 무관하게 sector ranking 일관 (Kendall τ > 0.7 across window 길이).
- **v1 단정과의 차이**: v1 의 "Reflation → industrial 강세 / Recession → healthcare 강세" 같은
  단일-window regime 매핑이 본질적으로 잘못된 frame 임을 직접 검증. Round 2 D-3 의 2025 Dec
  healthcare flip 이 confirm direct evidence.

### H5. Sub-sector × regime 단순 매핑 반증 가능성
- **명제**: v1 yaml 의 "Reflation → industrial 강세" 매핑은 2024 데이터 (industrial -17.7%) 로
  *반증*된다.
- **window**: 단일 regime 라벨 + 단일 calendar year (12m).
- **confirm**: regime 라벨 (Reflation/Recovery/Overheat/Stagflation/Recession) × sub-sector 9 종
  의 historical Rank-IC > 0.1 (해당 매핑이 데이터로 지지될 때).
- **reject**: ★ 이미 2024 데이터로 reject (industrial -17.7% in Reflation/Recovery-like 환경).
- **v1 단정과의 차이**: v1 의 sub-sector × regime 매핑은 *반증된 가설*. v2 lens 의 regime_reading
  은 "단정" 대신 "초기 prior, H4-conditional" 로 강등.

## D. 5 가설 우선순위 (검증 자원 배분)

| # | 가설 | 우선 | 사유 |
|:-:|---|:--:|---|
| H4 | Window flip | ★★★ | meta-가설 (다른 가설들의 evaluation window 결정 input) |
| H1 | Long-WALT cross-section | ★★★ | rate β 의 핵심, ticker-level granularity 직접 입력 |
| H2 | Cap rate spread mean-revert | ★★ | timing 모델의 anchor. 단 환각 검증 dependent |
| H3 | Debt maturity stratify | ★★ | 시변 β 의 핵심 stratifier (Round 2 발견 직접 반영) |
| H5 | Sub-sector regime 단순매핑 | ★ | 이미 부분 반증. 잔여 확인 의무만 |

→ 2-3 (실데이터 검증) 단계의 자원 배분 = H4 → H1 → H2/H3 → H5.
H4 가 먼저 정해져야 H1/H2/H3 의 window 가 정해짐.

## E. 다음 단계 미리보기

- direction.md (본 자문 사이클 종합) → main 승인 게이트.
- 2-2 (이론 학습): Shulman + Researchgate 350174334 + Green Street + CFA L2 chapter 정독,
  raw/theory-notes.md. 환각 검증 (243bp/120bp + 2024 industrial -17.7%) 동시 처리.
- 2-3 (실데이터 검증): H4 먼저 (단순 cross-tabulation) → H1 (cross-section Rank-IC) →
  H2/H3 → H5. 코드화: 각 가설 → block5 confidence_hook (emit_where / accumulate_in / store /
  feeds_weight 매핑).
