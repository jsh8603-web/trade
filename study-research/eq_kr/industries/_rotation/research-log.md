---
tags: [type/research-log, domain/equity, sector/_rotation]
date: 2026-06-05
purpose: 12산업 rotation timing 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# 12산업 rotation timing 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 산업 패널 수익 | 각 capsule prices.parquet (종목 일간) | resample('ME').last().pct_change().mean(axis=1) = eq-weight 월수익 | ✅ | prices 컬럼 수 = pass_floor 통과 종목 수 (이미 산업 패널). 12산업 동일 구조 |
| 공통 macro regime | 각 capsule regime_series.parquet (cli_kr/usdkrw/semi_ppi/foreign_net_kospi) | 12산업 동일 (financial 만 금리커브 추가) | ✅ | ★cli_kr/semi_ppi = PIT lag **미적용 raw** (lag는 regime_labels 단계서만). measure 에서 직접 lag 의무 |
| 산업별 고유 cycle (유가/리튬/철광석) | yfinance/FRED 무료 proxy | 미수집(refining 만 collect_refining_cycle.py 보유) | ⏳ collector_plan | 현 측정 = 공통 macro + 산업 자체 momentum/rel_mom 로 완주. 산업 고유 cycle = 보강 여지 |
| cross-industry 상대모멘텀 | 12산업 패널 평균 대비 산업 상대수익 | rel = panel[s] − mean(all_panels) → 누적 모멘텀 | ✅ | ★rotation 본체 신호 (refining/consumer reversal 발현) |

## 막힘·해결 로그 (시계열)

- [2026-06-05 17:xx] 막힘: python PATH 부재 (`python: command not found`)
  → 진단: PATH에 python 없음, 직접 경로 필요
  → 해결: `PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"` 직접 호출
  → 교훈: Inv 프로젝트 = Python312 절대경로 사용 (battery/eq_kr 동일 환경)

- [2026-06-05 17:xx] 막힘: ★cli_chg 가 거의 모든 산업서 비현실적으로 강한 forward 예측(financial rho +0.555)
  → 진단: regime_series.parquet 의 cli_kr 는 PIT lag **미적용 raw** (collect_regime.py line 161 = reindex ffill만, lag는 build_regime_labels 안에서만 적용). measure 에서 raw cli 로 cli_chg 계산 = **lookahead leakage**
  → 해결: measure_rotation.py 에서 CLI_PUB_LAG=2 + SEMI_PPI_LAG=1 직접 shift 적용. rho 0.555→0.482 (leakage 제거 확인). usdkrw/foreign = 일별 실시간 lag불필요
  → 교훈: ★regime_series.parquet 의 월별 macro(cli/semi_ppi)는 PIT lag 미적용 = 사용 전 발표지연 shift 의무. regime_labels.parquet 는 lag 적용된 라벨만 보유. D축 자가검증으로 발견

- [2026-06-05 17:xx] 막힘: measure_rotation_robust.py 가 measure_rotation.py import 시 `ValueError: I/O operation on closed file`
  → 진단: mr 모듈이 module-level 에서 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer...)` 실행 → import 시 우리 stdout buffer 소유·닫음
  → 해결: import 후 `sys.stdout = io.TextIOWrapper(os.fdopen(os.dup(1),'wb'), encoding='utf-8')` = 새 fd(dup) 로 fresh wrapper
  → 교훈: module-level stdout 재할당 스크립트를 import 하면 stdout 닫힘. os.dup(1)로 복구

- [2026-06-05 v2] ★자문 2R 확정 spec + 사용자 파이프라인 재정렬 = 가격 momentum 중심(v1) → 고유 cycle 직접신호(primary) + 이론 부호 사전확약 보강
  → 진단: v1 = 가격통계부터 던짐 = 자문 A("고유 cycle=진짜 alpha, momentum=공통인자 재포장") + 사용자 "이론→통계검증" 파이프라인 미반영
  → 해결: (1) source 사전검증(yf.history period=max) → 6산업 cycle proxy 수집(collect_industry_cycle.py: TIO=F/LIT/CL=F/CARZ/BDRY/SOXX) (2) theory-notes.md 부호 사전확약 (3) measure_rotation_v2.py primary cycle + secondary momentum residualized (4) measure_selfcheck.py 36셀 collapse + residual N_eff
  → 교훈: ★측정 전 이론(부호 사전확약) 먼저 = data-mining 차단. momentum residualize 후 소멸=공통인자 재포장 입증(자문 A 정확). source 사전검증 = empirical-claim §1.1-ext 이행(전 yfinance 가용 확인)

- [2026-06-05 v2] 막힘: yfinance 결과 print 시 cp949 UnicodeEncodeError (이모지)
  → 해결: `sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')` 1줄. 이모지 대신 [OK]/[ERR] ascii 사용
  → 교훈: Windows cp949 콘솔 = 이모지 금지, ascii 마커 사용

## 측정 방법 결정 로그

- **forward 예측 primary (refining prototype 차이)**: refining/measure_timeseries.py 는 cycle driver vs 패널수익 **동조(contemporaneous)** 가 본체 + forward=falsifier(약할 것). ★rotation 임무는 반대 = forward 예측력(timing 신호 자격)이 본체 + walk-forward OOS 추가. = "지표 보고 산업 비중 미리 조정 가능한가".
- **산업 고유 vs macro 공통 분리**: 12산업 PC1 55% 지배 측정 → macro 신호는 12산업 거의 동일 = 시장 timing(N_eff 중복), 진짜 rotation = 산업 고유(momentum 부호 차이/상대모멘텀). G-G v2 N_eff orthogonality 정합.
- **G-G v2 게이트**: eligibility(OOS 부호+magnitude 유지) = 매매 자격 1차 / powered(t_obs≥2.802 MDE) + BY = conviction 2차. underpowered ≠ 신호부재(power artifact) → OOS 부호유지면 tradeable 후보. 자문 2R 수렴 반영.
- **non-overlap 교차검증**: 60d overlap → asymptotic t 과대. stride=3M non-overlapping sub-sample IC 로 부호 일관 확인 (overlap artifact 차단). chemical/refining 은 non-overlap 에서 강화 = 견고.
- **placebo + LOY**: 신호 shuffle → 우연 corr 분포(placebo) + 연도별 1개 제외(episode 종속). 전 채택 후보 LOY 부호 일관 + placebo<0.05 대부분.
- **gated 설계 박제**: 자문 gemini(sector timing overlay, 0~max long-only) + claude(default 0/hysteresis dead-band/cost-aware no-trade/live OOS attenuation, telecom=carry tilt) 수렴 → summary.yaml gated_design. ★sizing·배선 = supervisor 통합단계.
- **valuation-band 추가 (team-lead 명시 + 이연 금지)**: 산업 aggregate PBR(PIT rcept_dt) rolling z(24M) → forward. chemical +0.448(valuation+momentum 일관=추세) / steel·consumer 음(mean-reversion) OOS 견고 / telecom·aitech·auto OOS flip(valuation 부호 불안정) / financial INSUFFICIENT(은행 PBR 부적합). FDR 생존 0(underpowered) = ★momentum/rel_mom 의 보조 confirm(독립 primary 아님). shares_approx 근사 = z 상대값만 신뢰.

## 미해결 / 다음 세션 우선 작업
1. 산업별 고유 cycle 지표 직접 수집(yfinance crack/LME/SCFI) → forward 예측 추가 (현 = 공통 macro + 산업 momentum).
2. telecom dividend-carry tilt 측정 (자문 primary 권고, DART 배당).
3. 산업 aggregate valuation band(PBR z) → forward mean-reversion (capsule equity 재사용).
4. rotation(동적 tilt) ⊕ static PCA sleeve(plan §8 S6) 결합 = 2층 완성 (supervisor 통합).
5. underpowered 신호 live OOS 누적 추적 → powered 승격 (e-CUSUM).
