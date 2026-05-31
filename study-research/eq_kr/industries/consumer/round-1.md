# round-1 — 소비재 산업 (consumer) 이론·가설 초안

> Tier 3, opus 1m 200k budget. frame v2 §1 Tier 3 / §3 Layer 3 소비재 directive.
> universe: 097950(CJ제일제당), 003230(삼양식품), 023530(롯데쇼핑) + 확장 후보.
> 본 round-1 = 이론 + 가설 5-10 (반증조건 포함) + Layer 3 cycle 지표 후보 (자문 없이 자체 정독·정당화 후).

## §1. 산업 구조 — 3 sub-cluster (sub-cluster 메모 frame §1 따름)

### 1.1 sub-cluster 정의

| sub-cluster | 핵심 ticker | 사이클 driver |
|---|---|---|
| **A. 음식료 내수형** | 097950(CJ제일제당), 271560(오리온), 005180(빙그레), 004370(농심) | 한국 소매판매 yoy, 농산물 원재료 (옥수수·밀·대두 CME), USDKRW (수입), 인플레 |
| **B. K-food 수출형** | 003230(삼양식품 - 불닭볶음면), 097950(CJ - 비비고/만두), 271560(오리온 - 중국) | K-food 수출 yoy (특히 미국·중국), USDKRW (수출 마진), 글로벌 라면·간식 시장 점유율 |
| **C. 유통·생활용품** | 023530(롯데쇼핑), 139480(이마트), 282330(BGF리테일), 007070(GS리테일) | 한국 소매판매 yoy, 가계 가처분소득, e-commerce 침투율, 임대료/인건비 |

★ 본 작업방 universe = 3 대표 ticker 중심 + 확장 6개 (총 9개) — sub-cluster A/B/C 각 3개. small-N 게이트 (frame §M4 #1) 위해 universe 확장 의무.

**최종 universe (n=9)**:
- A 음식료 내수: 097950 (CJ제일제당), 271560 (오리온), 004370 (농심)
- B K-food 수출: 003230 (삼양식품), 005180 (빙그레), 035250 (대상)
- C 유통: 023530 (롯데쇼핑), 139480 (이마트), 282330 (BGF리테일)

### 1.2 가격 결정 원리 (간략)

소비재 (특히 음식료) 의 가격 결정 = (a) **원재료 (commodity) cost pass-through** — 농산물 가격 yoy 가 마진 압박 → 분기 lag (60-90일) 후 판매가 인상 (b) **수출 수요 cycle** — 글로벌 K-food 트렌드 (라면·만두·아이스크림) + USDKRW (수출 마진 +/-) (c) **내수 소비심리** — 가처분소득 + 인플레 (가격 저항) (d) **유통 채널 변화** — 오프라인 (대형마트) vs e-commerce (쿠팡·네이버) (e) **environmental shocks** — AI cycle 무관, 외국인 flow 영향 상대적 약함 (소비재 = defensive sleeve 경향).

★ 본 산업 = **방어주 성격** (반도체·2차전지 대비 cycle 변동 작음) + **K-food 수출형은 성장주 성격** (삼양식품 = 2024-2025 stock price 4-5x). sub-cluster 별 mixed pricing principle 인식 의무.

---

## §2. 가설 5-10 (반증조건 포함)

### H1 — K-food 수출 yoy ↑ → sub-cluster B 종목 forward 3M return ↑
- **이론**: 관세청 수출입통계 농식품 수출 yoy 가 sub-cluster B 종목 (삼양·CJ·오리온) 분기 매출과 lead 관계 (1-3M lag). 매출 surprise → forward return.
- **반증조건**: M1 횡단면 Rank-IC < +0.05 (월간 N=24 cell) OR M2 lag-corr 모든 lag 에서 p>0.10 OR M3 K-food 수출 강세 regime 12 cell 내 OOS IC ratio < 0.5.
- **검증 source**: 관세청 농식품 yoy (월간), FDR ticker daily.

### H2 — USDKRW yoy ↑ → sub-cluster B (수출형) forward return ↑ + sub-cluster A (내수형) forward return ↓
- **이론**: USDKRW 약세 (KRW 강세) → 수출 마진 - / 수입 원재료 cost +. 반대로 강세 (KRW 약세) → 수출형 마진 +, 내수형 원재료 cost +. 부호 분리 가설 (sub-cluster 간 reversal).
- **반증조건**: M1 sub-cluster B 와 sub-cluster A 모두 동일 부호 OR partial-corr (controls = KOSPI return) 후 부호 약화 (|corr|<0.1).
- **검증 source**: FxStore USDKRW PIT, FDR ticker daily, sub-cluster eq-weight 평균.

### H3 — 한국 소매판매 yoy ↑ → sub-cluster A + C (내수형) forward 1M return ↑
- **이론**: 통계청 소매판매 지수 (월간, lag ~25일) 가 내수 소비재 매출 동행지표. 소비심리 → fwd return 약한 lead.
- **반증조건**: M1 Rank-IC < +0.03 (월간) OR M3 regime 분해 (소비호조 vs 둔화) IC gap < 0.05.
- **검증 source**: 통계청 OpenAPI 또는 KOSIS 무료 (수동 다운로드 폴백).

### H4 — CME 농산물 가격 yoy ↑ (옥수수·밀·대두 weighted avg) → 음식료 (sub-cluster A) forward 3M return ↓
- **이론**: cost pass-through lag 60-90일 → margin 압박 → 분기 후 가격 인상 (regulatory delay) → 단기 fwd return -. classical 원재료 → 마진 압박 메커니즘.
- **반증조건**: M1 lag-corr 3M lag 에서 p>0.10 OR M3 cost shock regime (yoy>+20%) 에서 IC<-0.05 미달.
- **검증 source**: Yahoo Finance CME tickers (ZC=F 옥수수, ZW=F 밀, ZS=F 대두) — yfinance 무료.

### H5 — 외국인 flow (소비재 산업 평균) ↑ → 다음 5d/20d forward return ↑
- **이론**: frame v2 §3 Layer 2 외국인 flow base_weight 0.20+ 권고 (R1 finding). 소비재 외국인 비중 (특히 CJ·삼양·오리온) 30-40% → flow driver 강함.
- **반증조건**: M1 5d fwd Rank-IC < +0.05 OR M3 외국인 flow regime 3 cell 분해 IC gap < 0.05.
- **검증 source**: `data/krx_flow_snapshots.jsonl` (있다면) 또는 KRX API 폴백.

### H6 — sub-cluster 간 spread 변동성 가설: B (수출형) - A (내수형) eq-weight return spread → USDKRW + K-food 수출 yoy 의 partial-corr 후 잔차 = idiosyncratic
- **이론**: sub-cluster 간 부호 분리 (H2) 가 macro factor 통제 후에도 살아남는지. 살아남으면 산업 내 sub-cluster routing rule 의 근거.
- **반증조건**: partial-corr (USDKRW + 수출yoy + KOSPI return controls) 후 |spread β| < 0.05.
- **검증 source**: 위 데이터 + linear regression.

### H7 — KOSPI 대비 outperformance regime (월간) — 소비재 sleeve 가 KOSPI 대비 outperform 하는 regime = 변동성 + defensive 수요
- **이론**: 소비재 = defensive sleeve 경향. KOSPI 변동성 ↑ + 외국인 매도 regime 에서 소비재 sleeve outperformance.
- **반증조건**: M3 regime 분해 (KOSPI vol regime × 외국인 flow regime, 9 cell) 에서 outperformance 차이 < 200bp/월.
- **검증 source**: KRX 시총 가중 KOSPI vs 소비재 eq-weight return.

### H8 (★기각 후보, p-hacking 차단용 가설) — Layer 1 펀더멘털 PER → forward return 음의 관계 (value premium)
- **이론**: low PER → value premium → forward return ↑. classic Fama-French.
- **반증조건**: M1 Rank-IC > -0.03 (즉 약한 가설 — 음의 의미 IC 가 -0.05 이하여야 confirm).
- **검증 source**: DART (PER 계산 어려움 — TTM EPS 필요) → 본 라운드에서 **자료 부족시 skip 명시** (★frame §6 H 미해결로 기록).

---

## §3. Layer 3 산업 cycle 지표 후보 (frame v2 §3 directive)

| # | 지표 | 정의 | 무료 source | 우선순위 | 이론 정당화 |
|---|---|---|---|---|---|
| L3-1 | **한국 소매판매 yoy** | 통계청 소매판매액지수 (불변, 월간) yoy | KOSIS 무료 다운로드 또는 OpenAPI | P0 | sub-cluster A/C 내수 매출 동행지표 |
| L3-2 | **K-food 수출 yoy** | 관세청 농식품 수출액 (월간, 라면·만두·아이스크림 breakdown 가능) yoy | 관세청 무역통계 (data.go.kr 무료) | P0 | sub-cluster B 매출 lead 지표 |
| L3-3 | **USDKRW yoy** | FxStore daily → 월말 → yoy | `core/data/macro_market.py` FxStore PIT | P0 | sub-cluster A/B 부호 분리 driver (frame v2 권고 base 0.15-0.20) |
| L3-4 | **CME 농산물 가격 yoy** | 옥수수(ZC=F) + 밀(ZW=F) + 대두(ZS=F) eq-weight yoy | yfinance 무료 (Yahoo Finance) | P1 | sub-cluster A 원재료 cost pass-through |
| L3-5 | **한국 가처분소득 / 소비심리지수** | 한국은행 BSI/CCSI 또는 통계청 가계동향 | KOSIS / ECOS 무료 | P2 | H3 보조 (단독 IC 약할 가능성) |

★ 최대 5개 (frame §3 산업당 5개 이내). P0 3개 (필수) + P1 1개 + P2 1개.

★ **무료 source 가용성 검증 (round-2 후)** — 관세청 OpenAPI 인증·KOSIS 다운로드 PoC. 막힘 시 fallback = WebSearch/WebFetch 직접 fetch + raw/ 저장.

---

## §4. 막힘 처리 가이드 (subagent 자율)

1. **데이터 부족 (Layer 3 무료 source 막힘)**: WebSearch + WebFetch 1-2R → raw/ 저장 + 출처 명시. small-N 시 verdict 격하 (frame §M4 #1 fail = N 부족 finding).
2. **toraniko 적재 실패**: pandas/numpy 자체 Fama-French style 회귀 fallback (frame §M5 명시 허용). raw IC + factor-neutralized IC 둘 다 보고.
3. **5게이트 (frame §M4) 부족**: verdict 격하 — confirm → partial → tentative → insufficient. ★점추정 박제 금지 (frame §0 ⛔1).
4. **regime 36 cell 분할 N<24**: cell collapse fallback (frame §M3) — 36 → 12 → 9 → 3 cell merge.

---

## §5. 다음 단계 (round-1 후)

1. theory-notes.md 작성 (소비재 산업 cycle 이론 정독 — 음식료 cost pass-through, K-food 수출 cycle, 유통 e-commerce shift, source URL 명시)
2. validation-fundamental.md, validation-macro.md, validation-industry.md 작성 — 실측 IC + 5게이트
3. summary.yaml + 12axis-audit.md
4. ★ small-N + 점추정 박제 금지 + factor-neutralized IC 의무

> round-1 작성: 2026-05-30, 자체 정독 (자문 미사용 — round-2 에서 필요 시 호출).
