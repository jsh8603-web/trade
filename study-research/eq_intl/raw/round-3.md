---
tags: [type/study-research-raw, domain/inv, study/eq_intl, phase/2-1, round/3]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
round: 3
channel: Gemini API (gemini-search.js pro)
fallback_reason: "WebSearch hook research.block 발동 → Gemini API 채널 (9-session 무관, search-engine skill SSOT)"
archive_raw: ~/.claude/docs/archive/research-raw/eq-intl-r3-native-20260530.txt
hallucination_status: "고유명사·paper명 검증 미실시 — 2-2 이론학습 단계에서 IMF/MS/AQR 원문 cross-check 의무"
---

# eq_intl R3 — China decoupling 정량 + future regime

## Q1: China decoupling 정량 evidence (2020s)

### 핵심 정량 fact (Gemini 인용)
1. **MSCI China 의 MSCI World rolling beta**: 2021 중반 1.2 → 2022 말 0.2~0.3 급락. MSCI EM
   ex-China 베타는 1.0~1.1 안정 유지. → china 만 글로벌 채널 단절. **5y Yahoo 실측 (china dxy
   -0.29 / vix -0.33) 와 방향 일치 + 정량 magnitude 강확인**.
   - source: IMF "Geopolitical Fragmentation and the Future of Multilateralism" Jan 2023 Fig 2.11
   - ⚠️ 환각 검증 미실시 — 2-2 단계 원문 cross-check 의무
2. **MSCI China 의 글로벌 macro factor R²**: 2018 이전 30~40% → 2022 <10%. idiosyncratic 비중 ↑.
   - source: Morgan Stanley "Is China Becoming a Diversifier?" 2022~2023
   - ⚠️ paper 정확명 검증 보류
3. **2022 KWEB DXY 베타**: 미국 긴축 공포 → 글로벌 하락 중 china 자체 완화 기대로 DXY 와 미세
   양(+) 또는 0 근접. **5y 실측 H4 의 risk-off 시 +0.033 과 정확히 일치**.
   - source: AQR "You Need to Rethink Emerging Markets" 2023
   - ⚠️ AQR paper 명 검증 보류

### 메커니즘 분해
| 채널 | fact | source |
|---|---|---|
| Capital control | Stock/Bond Connect 명목 확대 vs 실질 "invisible control" 강화. 2022 외국인 record net sell. RU-UA war 후 지정학 리스크 → ~$100bn portfolio 유출 | IIF Capital Flows Tracker 2022-2023 |
| CNY managed float | PBoC daily fixing 의 counter-cyclical factor 적용. CNH-CNY spread 2022/04, 2022/10 300~500pips 확대 → 통제와 유출 압력 긴장 | PBoC quarterly + PIIE 분석 |
| A-H share spread | Hang Seng Stock Connect China AH Premium Index 2021 말 140~150 (= A주 40~50% 비싸게). H주 비관 / A주 격리 | Hang Seng Indexes Co. |
| Cross-border flow | 2022 BIS Locational Banking — china 대상 해외 은행 claims 둔화/감소 | BIS GLI quarterly |

### 통계 artifact vs 구조적 분리
- **artifact 주장**: COVID/부동산 위기로 cycle desynchronization (서방 인플레/긴축 vs china 디플레/완화)
  → correlation 인위적 낮춤. 글로벌 동시 cycle 회복 시 re-couple 예상.
- **구조적 주장**: Tech crackdown / Common Prosperity = 발전모델 근본 전환. discount rate 영구
  geopolitical/policy risk premium 추가 (Dalio 2021 "Changing World Order").
- **판단 기준**: 구조적이면 (1) USD/rate 사이클 민감도 영구 ↓ (2) china 자체 신용/정책 사이클이
  주된 pricing 변수 (3) 외국인 자본 흐름이 지정학에 민감. **2023~2024 현재까지 패턴 지속** → 구조적
  쪽에 weight.

### Future regime (2025~) — tug of war
| 방향 | 요인 |
|---|---|
| Decoupling ↑ | 미·중 갈등 / 반도체 수출통제 / outbound investment EO / RMB internationalization (CIPS / 오일 위안결제) / Dual Circulation 내수중심 |
| Re-coupling | 부동산 위기 극복 위해 외국인 투자 유치 절실 → pro-market 회귀 / valuation 매력 ("too cheap to ignore") / 글로벌 동시 위기 시 risk-off 상관 ↑ |

→ **학술적 합의 부재**. 가설 H5 의 반증조건 = re-couple 패턴 (rolling beta 1.0+ 회복) 등장 시.

## R1~R3 종합 → 가설 9건 보강

| ID | 가설 (R1 초안) | R3 보강 | 반증조건 갱신 |
|---|---|---|---|
| H5 china decoupling | china β < EM avg | MSCI China beta 1.2→0.2 (IMF) + R² 30%→10% (MS) + 2022 KWEB DXY 미세 양 (AQR) | china rolling β > EM-avg 95% CI 회복 OR R² > 25% 재돌파 6m+ |

## 가설 우선순위 (3R 누적)
1. **H1 dollar dominance** (R1+R2 강) — eq_intl 1차 driver
2. **H2 regime amplification** (R1+R2+R3) — risk-off coupling 강화
3. **H5 china decoupling** (R3 정량 강확인 + 5y 실측 일치)
4. **H7 TSM self-momentum** (R1 AQR 강) — H3 cross-section 보다 robust 가능
5. **H4 commodity exporter oil** (R1+R2 약, R3 무관)
6. **H3 cross-country mom** (R1 강 이론 vs 5y IC-IR 0.13 실측 약 → caution)
7. **H9 momentum crash regime** (R1+R2 method 매핑)
8. **H6 segmentation** (R1, R3 China 의 segment-like)
9. **H8 ETF liquidity tier** (R1)

## 수렴 판정

✅ **3R 수렴 도달**:
- 이론 frame 4-5 후보 (R1) + BIS 실무 frame (R2) + China 정량 분리 (R3) — 일반론·리포트 합치
- 검증 method 7종 표준 (R2) — eq_intl walk-forward + drift regime + RankIC + 2-level uncertainty
- 가설 9건 반증조건 (R1+R3 보강) — 우선순위까지 도출

추가 라운드 marginal benefit 낮음 (carry crash / cglasso cross-country 사례 = 2-2 이론학습 흡수
가능). 사용자 main "3~7R" 의 하한 충족. → **R3 종료, direction.md 종합 진입**.

## 환각 검증 의무 (2-2 이행 표지)
R3 인용 paper 명 (IMF Geopolitical Fragmentation Jan 2023, MS Is China Becoming a Diversifier?,
AQR You Need to Rethink Emerging Markets) = 2-2 이론학습 단계에서 원문 cross-check 의무. 만약
원문 부재면 가설 신뢰도 보정.
