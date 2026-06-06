---
tags: [type/research-log, domain/equity, sector/steel]
date: 2026-06-05
purpose: 철강 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션(특히 자산집약 협소 산업) 재현용.
---

# steel(철강) 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| universe | FDR KRX-DESC 키워드(STEEL_KW) | ★키워드만 = 발전설비(두산에너빌리티)·상사(포스코인터)·전선(대한전선)·조선(SK오션) 혼입 | ✅ Industry "1차 철강 제조업" 정밀 필터 + 명시 제외 + 태웅(단조) 화이트리스트 | ★frame §M.11 화이트리스트 의무. "기타 금속 가공제품"은 절삭공구·방산·공작기계 多 = 제외. |
| floor | 반도체 floor(Mc 3000억 ∧ ADV 30억) | ★3~5종 = breadth 붕괴 (POSCO/현대제철/대한전선만 통과) | ✅ Mc 1000억 ∧ ADV 1억 완화 → 23종 | ★철강 = 협소·저유동성 산업(dispatch 경고). floor 산업별 조정 필수. 그래도 반도체 85종의 1/4. |
| 가격 | pykrx OHLCV loop | 23종 1818일 OK | ✅ | semi 동일 (pykrx 개별종목 loop 작동, 시장 스냅샷 API는 인증 차단) |
| valuation | DART fnlttSinglAcntAll (equity/net_income/assets) | 563 rows/23종 OK, PBR 1786 cells | ✅ rcept_dt PIT | FY 보고지연 median 108-120일. CFS→OFS fallback |
| capex/재고 | DART dart_extended (inventory/ppe/intangible) | 592 rows, ppe coverage **100%** | ✅ rcept_dt PIT | ★철강 = 유형자산 계정 안정적(장치산업) = capex 측정 최적. cogs 8%(매출원가 계정명 불안정, 비핵심) |
| regime | 반도체 collect_regime.py 재사용 | regime_labels.parquet 복사 | ✅ | ★시장 공통(CLI/USDKRW/외국인flow) = 산업 무관. 재수집 불필요 |
| 산업 cycle proxy | SLX(글로벌 철강 ETF) / VALE(철광석) | yfinance fetch OK, regime bull32/neutral51/bear6 | ✅ G1 regime + customer momentum | ★반도체 SOXX 대응. SLX = VanEck Steel ETF = 글로벌 철강 cycle |

## 막힘·해결 로그 (시계열)

- [2026-06-05 10:30] 막힘: universe 키워드 매칭 floor-passed 5종 中 3종 비철강(두산에너빌리티=발전설비/포스코인터=상사/대한전선=전선). → 진단: FDR 키워드(STEEL_KW)가 "주단조품·강관" 등으로 비철강 본질 종목 오염(frame §M.11 화이트리스트 결함 정면). → 해결: Industry "1차 철강 제조업" 정밀 필터 + EXCLUDE_CODES 명시 제외 + 태웅(자유형단조품=철강 단조) INCLUDE_EXTRA. → 교훈: ★협소 산업은 키워드 매칭 위험. Industry 컬럼 정밀 필터 + 육안 화이트리스트 sanity check 의무.
- [2026-06-05 10:37] 막힘: 반도체 floor(ADV 30억) 적용 시 5종(breadth 붕괴). → 진단: 철강 = 저유동성(POSCO 외 ADV 작음). → 해결: floor 완화(Mc 1000억 ∧ ADV 1억) → 23종. → 교훈: ★floor는 산업 유동성 분포에 맞춰 조정. 단 small-universe 라벨 + magnitude haircut 의무(frame §M.12).
- [2026-06-05 10:45] 함정: python3 별칭 없음. → 해결: Python312 절대경로(C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe) 사용. PYTHONIOENCODING=utf-8 PYTHONUTF8=1.
- [2026-06-05 11:00] 발견: conditional 증폭축 = KRW_neutral (반도체는 KRW_weak). → 진단: 철강은 중국 cycle dominant라 환율 stress(KRW_weak)보다 안정기(KRW_neutral)에 cyclical 신호 명확. → 해결: measure_conditional interaction dummy를 KRW_weak→KRW_neutral 변경 + walk_forward_oos(KRW_neutral) 추가. → 교훈: ★interaction dummy는 산업별 증폭축에 맞춰야 함(반도체 코드 hardcoded KRW_weak 그대로 쓰면 철강 mismatch).
- [2026-06-05 11:10] 발견: DART filings(collect.py [3/3]) 빈 응답(pblntf_ty 필터). → 진단: list.json pblntf_ty="A" 필터가 종목 무관 전체 조회라 부적합. → 해결: PIT lag는 measure_cross.dart_reporting_delay(median 108-120일 실측) + dart_extended rcept_dt로 직접 측정. collect.py filings는 비핵심 skip.

## 측정 방법 결정 로그

- **capex 가설 (dispatch 최우선)**: capex_ratio(유형/총자산) + ppe_yoy(증가율) 둘 다 측정. prior 음(asset growth anomaly). 결과: capex_ratio y_60d만 강(-0.084 wc_p=0.0005 + OOS 생존), ppe_yoy OOS 반전. ★수준(ratio) 채택, 증가율(yoy) 기각. 장기 horizon(y_60d)서만 발현 = Cooper-Gulen-Schill(asset growth = 연간 신호) 정합.
- **valuation PBR vs PER**: 둘 다 측정. PBR 3M/6M/12M 단조 일관(BY 생존 3개), PER 전 horizon 비유의. ★cyclical PER 양방향 왜곡(정점 peak-EPS + 다운 trough 적자) = PBR robust 확인.
- **conditional 증폭축**: 단일축 conditional 측정 후 KRW_neutral이 wc_p 최강 식별 → interaction dummy 그것으로 + walk-forward OOS로 episode 종속 직접 검증(interaction term 비유의는 small-n, walk-forward가 verdict 근거).
- **S5 역공격 실측**: (A) POSCO drop → -0.165 생존 (B) Fama-MacBeth PBR|Size t=-1.98 경계 (C) leave-2021 → -0.161 생존. ★small-universe라 S5-B size 위장 완전 입증은 약(t<2 경계), hedge 박제.
- **small-universe haircut**: avg 20종 = magnitude inflation. point estimate(momentum -0.181) literal 금지, breadth-adj IR(-0.81) + 50% haircut 일관. 방향·significance(t, BY)는 신뢰. frame §M.12 telecom/auto 동형 처리.

## 미해결 / 다음 세션 우선 작업

1. ★**capex 일반화 = 자산집약 4섹터(화학/정유/조선/철강) cross-sector 일관성** — 메인 종합(철강 capex_ratio 음 = 자동차 재현 입증, 화학/정유/조선 결과와 합산).
2. **small-universe magnitude 확정** — universe 확장(소형주 floor 완화) 또는 N 누적 후 momentum/PBR magnitude 재측정 + size 위장 t>2 확정.
3. **2축 merge conditional + M_eff 통합 FDR** — supervisor 통합단계.
4. **EV-EBITDA / KR HY spread / 중국 조강생산·철광석 직접 지표** — collector_plan.
5. **PIT universe 멤버십(생존편향)** — 철강은 상폐 드물어 영향 작으나 high.
