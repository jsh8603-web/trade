---
tags: [type/validation, domain/commodity, indicator/noaa-oni-enso, study/m3]
date: 2026-05-31
indicator: noaa_oni_3m_ma (ENSO)
status: structural_low_confidence (validated_alpha=false) — 독립 12축 audit 완료 (2026-05-31, Hard-fail 0)
---

# validation — NOAA ONI (ENSO) → agri commodity (M3 merit study)

## 0. 가설 / spec
- **가설 (predictive)**: ENSO (El Niño/La Niña, ONI 지수)는 농업 공급충격(가뭄·홍수)을 통해
  곡물·연질 commodity 가격을 **선행**한다. ONI(t) 가 향후 h개월 forward log-return 을 예측.
- **방향 prior**: 부호는 작물·지역별로 갈림(약 prior). 단조관계만 1차 검정 (spearman).

## 1. Data Coverage (의무 1.1)
- **ONI**: NOAA CPC `oni.ascii.txt`, 계절(DJF..NDJ) ANOM = ONI(3M SST anomaly), 중심월 매핑 → 월별.
  실 coverage 1950-01 ~ 2026 (916행 fetch). **공개 실시간 지수 = PIT clean** (vintage 개정 없음).
- **agri price**: IMF/PCPS via DBnomics (월), `M.W00.{code}.USD`. 패널 6종 검증:
  PMAIZMT·PWHEAMT·PSOYB·PRICENPQ·PSUGAISA·PCOCO — 전부 obs=426, **1990-01 ~ 2025-06**.
- **분석 표본**: ONI∩agri 월별, **n=423**(fwd3) / 420(fwd6) / 414(fwd12). silent default 없음
  (fetch 실패=raise, 합성 금지 준수).

## 2. Spec ↔ Code 1:1 Match (의무 1.3)
- Spec: "ONI(t) → 향후 h개월 forward log-return" (predictive).
- Code: `d["fwd"] = log(price).shift(-h) − log(price)` (forward h개월 누적), `spearman(oni, fwd)`.
- **Verify**: 시제=forward h(predictive), freq=monthly, transform=ONI level vs log-return, conditioning=unconditional. **PASS** (contemporaneous 아님, predictive 일치).

## 3. 결과 (스크립트 `m3-noaa-oni-enso.py` → `*-results.json`)

### Bonferroni + HAC + block-bootstrap 전관문 생존 (실질 유의)
| commodity | fwd_m | n | spearman ρ | raw p | NW-HAC t | HAC p | boot ρ CI95 |
|---|---|---|---|---|---|---|---|
| **wheat** | 3 | 423 | -0.2686 | ~0 | -3.675 | 0.00024 | [-0.39, -0.18] |
| wheat | 6 | 420 | -0.2198 | 1e-5 | -2.829 | 0.00467 | [-0.42, -0.05] |
| **maize** | 3 | 423 | -0.2109 | 1e-5 | -2.932 | 0.00337 | [-0.35, -0.07] |
| maize | 6 | 420 | -0.1765 | 0.00028 | -2.366 | 0.01799 | [-0.28, -0.05] |
| soybean | 3 | 423 | -0.1853 | 0.00013 | -2.235 | 0.02542 | [-0.34, -0.01] |

### 비유의 (HAC 탈락 or Bonferroni 탈락)
- soybean fwd6 (HAC p=0.14), rice(전 horizon HAC 비유의, 부호 양), sugar(HAC 비유의),
  cocoa(HAC 비유의), 전 commodity **fwd12 소멸**(maize/wheat/soybean fwd12 p>0.6).

## 4. 통계 안전장치 (의무 1.4 / 1.5)
- **Autocorr**: forward overlap → ① Newey-West HAC (maxlags=max(h,3)) ② block bootstrap
  (block=max(h, n/10), 4000회) CI 병행. 생존 = HAC p<0.05 AND boot CI 0 미포함.
- **Multiple comparison (의무 1.5)**: 6 commodity × 3 fwd = **18 비교**, Bonferroni α/18=0.002778.
  raw p<0.05 = 11건 / Bonferroni 생존 = 5건 (위 표). raw p 와 보정 p 분리 보고.

## 5. Verdict (preliminary — 독립 12축 audit 대기)
- **noaa_oni_3m_ma = CONFIRMED 후보** (cereals/oilseeds, 3-6개월 호라이즌):
  n=423(≥100), wheat/maize p<0.001, Bonferroni·HAC·bootstrap 전관문 생존 = 실질 유의.
- 신호 구조: **3-6개월 호라이즌 한정**(fwd12 소멸) = ENSO 공급충격 전파 물리적 타당.
- **부호 = 음**: El Niño(ONI↑) → 곡물 forward 수익률↓ (maize/wheat/soybean 일관). 경제 해석은
  후속(El Niño 시 주요 곡창 net 생산 영향·시장 선반영 가설) — 부호 일관성은 noise 아님.
- ⚠️ **격하 falsifier**: (a) 부호 경제 메커니즘 미확정(방향 prior만) (b) soybean fwd3 boot CI 상단 -0.01
  (경계) (c) ENSO 계절→월 매핑 look-through 미세 (d) 1990~ 표본(이전 ENSO epoch 미포함).
  → 채택 시 tier = **structural→validated 승격은 독립 audit + crop-region 메커니즘 확인 후**.

## 6. 미해결 의문 (의무 H)
- 부호 인과 메커니즘 (공급충격 방향 vs 시장 기대). lag 구조 (왜 3-6m 정점, 12m 소멸).
- rice 양(+) 부호 (ENSO 효과 작물별 상이) — 패널 평균화 시 상쇄 위험 → 작물별 분리 유지 권고.
- IMF/PCPS 2025-06 종료 → 최신 6개월 갱신 필요.

## 7. candidate-ledger 반영 (audit 후)
- `noaa_oni_3m_ma`: **이연 → 채택** (collector 무료 가용 + 실측 유의 + spurious 아님 확정). tier=**structural_low_confidence (validated_alpha=false)**.

## 8. 독립 12축 audit 결과 (2026-05-31, 별도 opus subagent)
- **재현성**: bit-identical (seed=11 결정론). C축 md↔json ±0%. **합성 지문 0** (2008 식량위기·2022 우크라이나·2012 가뭄 spike 실재, kurtosis 1.4).
- **★spurious 검정 = 아티팩트 아님 확정**: ONI stationary(ADF p=0.0003, I(0)) ↔ 수익률(차분) 정상회귀 → Granger-Newbold spurious 메커니즘 불가. detrend 후 ρ 불변(-0.2686→-0.2686). placebo(레벨 회귀 t=-0.99 비유의 / 수익률 회귀 t=-3.68 유의) = 공통추세였다면 정반대. **음의 부호 진짜.**
- **Hard-fail(B/C/D/I) = 0건** (활성화 차단 사유 없음, 채택 후보 자격 O).
- **tier 권고 = structural_low_confidence (validated_alpha=false)** — 승격 보류 근거 4:
  1. **D축 partial — "predictive" 라벨 과장**: ONI(t)가 *과거* 3m 수익률과도 동일 강도 음상관(wheat ρ-0.20 p<0.001) = ENSO regime co-movement 혼재. 단 strict-future(당월 제외 t+1→t+3)도 유의(wheat ρ-0.22 p≈0) → 선행성분 0 아님.
  2. **D축 partial — PIT 주장 부정확**: ONI는 잠정치 개정 + 30년 기준 재중심화로 **개정됨** ("개정 없음" 틀림). 계절라벨 DJF→Jan 매핑 = Feb SST embed(1-2mo look-ahead). 단 호라이즌 3-6m >> slip 이라 무효화 아님.
  3. **G축 — effective-N << 명목 423**: ONI acf(3m)=0.80 고지속성. block bootstrap 일부 흡수하나 tier 강등.
  4. 부호 경제 메커니즘 미확정 + 1990~ 단일표본(이전 ENSO epoch 미포함).
- **보강 권고 (후속)**: (a) PIT "개정 없음" 삭제 + ONI 1-2mo 추가 lag 보수 재측정 (b) predictive vs co-movement 분해(과거 3m placebo 명시 + strict-future 본결과 격상) (c) effective-N 박제.
- ★verdict: **채택(structural_low_confidence) — 실측 유의·spurious 아님이나 predictive 라벨·PIT·effective-N 한계로 validated 보류.** 후속 보강 3건 후 재평가 시 승격 후보.
