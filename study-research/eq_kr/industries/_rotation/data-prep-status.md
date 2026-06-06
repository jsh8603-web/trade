---
tags: [type/data-prep, domain/inv, scope/equity-kr, topic/rotation-timing, status/ready-awaiting-spec]
date: 2026-06-05
owner: semi-analyst (kr-equity team, opus 1m)
note: team-lead 지시 — measure 본체 보류(설계 자문 3R 수렴 중), 데이터 준비만. 자문 확정 spec 대기.
---

# rotation timing 데이터 준비 상태 (자문 spec 대기)

> ★team-lead 2026-06-05: rotation **설계 자체**를 메인이 외부 자문 3R 수렴 중. measure 본체 진입 보류,
> 데이터 준비만. 측정 방법론(지표 선택·static PCA 결합·FDR·over-trade) = 자문 후 확정 spec 재전달.
> ★기존 측정 산출물(measure_rotation*.py + summary.yaml 등)은 **보존** — 자문 spec 확정 시 재사용/조정.

## ① 12산업 eq-weight 패널 (일간 + 월간) — ✅ READY

전 12산업 `industries/{sector}/raw-v3/data/prices.parquet` (pykrx OHLCV 실측). 일간/월간 구성 검증.

| 산업 | 종목수(pass_floor) | 일간 n | 월간 n (2019~) |
|---|---|---|---|
| semiconductor | 85 | 1817 | 88 |
| bio | 38 | 1817 | 88 |
| financial | 34 | 1817 | 88 |
| battery | 29 | 1817 | 88 |
| consumer | 28 | 1817 | 88 |
| aitech | 26 | 1817 | 88 |
| steel | 23 | 1817 | 88 |
| auto | 17 | 1817 | 88 |
| chemical | 17 | 1817 | 88 |
| shipbuilding | 16 | 1817 | 88 |
| telecom | 14 | 1817 | 88 |
| refining | 11 | 1817 | 88 |

- **eq-weight 패널 구성식**: 일간 = `prices.pct_change().mean(axis=1, skipna=True)` / 월간 = `prices.resample('ME').last().pct_change().mean(axis=1)`.
- ★prices 컬럼 = 이미 pass_floor 통과 종목 = 산업 패널 (별도 필터 불필요).
- 공통 window = 2019-01 ~ 2026-05 (88 월). 12산업 정렬됨.
- cross-industry: 12산업 평균 pairwise corr 0.502, PC1 분산 55.3% (공통인자 지배 = static PCA sleeve 입력).

## ② 공통 macro regime — ✅ READY

전 12산업 `regime_series.parquet`(일별 raw) + `regime_labels.parquet`(월말 라벨).

- **regime_series 컬럼(공통 4)**: `cli_kr`(OECD CLI amplitude-adj, FRED KORLOLITOAASTSAM) / `usdkrw`(DEXKOUS) / `semi_ppi`(반도체 PPI) / `foreign_net_kospi`(ECOS 외국인 순매수).
- **regime_labels(36셀)**: `macro_regime`(CLI level×6M Δ 4국면) × `krw_regime`(USDKRW yoy 3) × `flow_regime`(외국인 28d z 3) + 보조(cli_chg6/krw_yoy/flow_z).
- ★financial 만 금리커브 추가: `ktb10y` / `ktb3y` / `corp_aa3y`.
- ⛔★PIT 함정 박제: **regime_series.parquet 의 cli_kr/semi_ppi 는 발표지연 lag 미적용 raw** (lag 는 regime_labels 단계서만). 측정 시 직접 shift 의무 — CLI_PUB_LAG=2 / SEMI_PPI_LAG=1. usdkrw/foreign = 일별 실시간(lag 불필요). (기존 measure 에서 leakage 발견·수정 = research-log).

## ③ 각 산업 고유 cycle 지표 (capsule 회수) — ⚠️ 부분 (2/12)

| 산업 | cycle 지표 자산 | 상태 |
|---|---|---|
| refining | `refining_cycle.parquet`(blended/gasoline/diesel crack, brent, oil_yoy, refinery_ip, natgas) + collect_refining_cycle.py | ✅ 수집됨 |
| telecom | `telecom_cycle.parquet` + collect_telecom_cycle.py | ✅ 수집됨 |
| financial | regime_series 금리커브(ktb10y/ktb3y/corp_aa3y) = cycle 일부 대용 | △ 부분 |
| 나머지 9산업 (semi/auto/battery/chemical/shipbuilding/steel/bio/consumer/aitech) | ❌ 산업 고유 cycle 미수집 (공통 macro 4 + semi_ppi 만) | ⏳ 미수집 |

- frame §3 Layer3 산업 고유 cycle 후보 (자문 spec 확정 시 수집 대상):
  - battery: 리튬/니켈/코발트(LME) / EV 판매 / IRA
  - chemical: 유가 Brent/WTI / 중국 PMI / ethylene-naphtha spread
  - steel: 중국 조강 yoy / 철광석(Platts) / 후판가
  - shipbuilding: 신조선 수주(Clarkson) / SCFI·CCFI 운임 / 후판가
  - auto: 글로벌 신차(LMC) / USDKRW / SAAR
  - bio: FDA 승인 / 임상단계 / USDKRW
  - consumer: 소매판매 yoy / K-food 수출 / USDKRW
  - aitech: hyperscaler capex / 광고매출 yoy
  - semiconductor: DRAM 현물가 / SOXX·SMH yoy(=semi_ppi 일부 대용)
- ★수집 보류 사유: 자문 수렴이 "산업 고유 cycle 직접 vs 공통 macro+산업 momentum 만" 방법론을 가를 수 있음 → spec 확정 후 수집(무리한 선수집 회피). measure_fundamentals_cycle.py(각 산업 보유)는 DART 재고/CAPEX(종목 cross-sectional)지 산업 timing cycle 아님 = 구분.

## 다음
- ★자문 확정 spec 대기 (team-lead 재전달). spec 도착 시: ③ 산업 고유 cycle 수집 여부 결정 → measure 본체(또는 기존 measure_rotation*.py 조정) 진입.
- 기존 측정 산출물 보존: measure_rotation.py / measure_rotation_robust.py / measure_rotation_valband.py + summary.yaml + rotation-timing.md + candidate-ledger.md + research-log.md + 15axis-audit.md + validation json 3종.
