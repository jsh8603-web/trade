---
tags: [type/validation, study/eq_us_cyclical, hypothesis/H1-H6, status/deferred]
date: 2026-05-30
verdict: DEFERRED (종목 단위 EDGAR 펀더 부재)
---

# H1·H6 검증 보류 — 종목 단위 EDGAR 펀더 부재

## H1 (정상화 E/P trough 최강 단일 예측자)
**필요 데이터**:
- 종목별 7-10년 ROE 시계열 (정상화 ROE 산출)
- 종목별 분기 EPS·매출·자산 (Damodaran 정상화 마진 회귀)
- 종목별 fwd 12M return (월말 가격)
- Damodaran implied ERP 월별 (자본비용 r_e)
- 종목별 D/E (bottom-up beta relever)

**가용 데이터**:
- ❌ EDGAR 펀더 캐시 부재 (`edgar_provider.py` 코드만 존재, 실 적재 없음)
- ❌ Damodaran implied ERP 적재 없음
- ✅ FRED T10Y (`DGS10`) 가용 (r_f용)
- ⚠️ 합성 픽스처(semiconductor_panel_v1.parquet)는 v1 분석에서 이미 사용 — IC=0.658이 합성 DGP 의심 (raw round-1-claude 비판)

**대응**:
- 블록6 collector_plan에 **EDGAR 분기 파싱 확장 (10-Q 재무제표 ROE/매출/자산)** + **Damodaran implied ERP 월별 적재** 우선순위 1로 등록.
- 라이브 적재 후 즉시 재검증 — H1·H6은 가설 트리의 backbone.

## H6 (peak_trap — 스팟-싼 거짓신호)
**가설**: peak 국면에서 스팟 P/E 저평가는 거짓신호. 정상화 val_gap≈0 + revision breadth=0. 스팟-싼 분위 OOS 수익 < 비싼 분위.

**필요 데이터**: H1 데이터 + 2국면 regime 라벨.

**부분 가능 검증 (sector ETF 단위)**:
- regime = high VIX 기간(상위 25%) vs 저 VIX 기간(하위 25%)으로 proxy
- sector ETF 가격 단위 → 스팟 P/E 추정 불가 (펀더 부재) → **종목 단위 EDGAR 필수**.

## 합성 픽스처로 H1·H6 보조 검증 한계
- v1 분석에서 합성 패널 40firm×36Q 사용. **합성 DGP 직접 인코딩 가능성** (Claude Round 1 비판: 실 단일팩터 IC 정상 0.02-0.08, v1의 0.658은 비현실적).
- 합성 패널의 cycle_phase / val_gap 발견은 **방향성 anchor**로만 유효, **OOS 일반화 금지**.

## 결론
- H1·H6 → **DEFERRED**. 블록6 collector_plan 우선순위 1 (EDGAR + Damodaran ERP).
- 본 2-3 단계의 실데이터 검증은 H3·H4·H5만 진행. 결과: 모두 약함/부분/기각 (H1·H6 backbone 미검증 상태에서 보조 신호도 약함).
- main 측 ETF holdings / 컨센서스 데이터 적재 완료 시 H8(revision breadth)도 즉시 재진입 가능.
