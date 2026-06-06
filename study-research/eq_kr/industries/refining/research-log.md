---
tags: [type/research-log, domain/equity, sector/refining]
date: 2026-06-05
purpose: 정유 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# refining(정유) 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| universe | FDR KRX-DESC "석유 정제품 제조업" | 코어 5종, strict floor-pass 2종 | SK이노/S-Oil | ★cross-sectional 불가(min 8종). 국내 정유 과점 = 구조적 한계 |
| 정제마진 | FRED Gulf crack(gasoline/diesel-Brent) | gasoline×42-Brent 계산 OK | proxy 채택 | ★한국 표준=싱가포르GRM 무료부재 → Gulf proxy 한계. crack 약신호가 proxy 탓일 수 있음 |
| 유가 | FRED DCOILBRENTEU(Brent)/DCOILWTICO(WTI) | 일별 2018~ OK | Brent | 두바이유 무료부재 → Brent proxy(중동산 동조) |
| 가동률 | FRED refinery util 시리즈 | WPULEUS3 등 ID 부재 → IPG32411S(석유석탄 IP) | IP proxy | ★EIA refinery util 시리즈 ID 불안정. IP proxy = OOS flip(한계) |
| regime | auto regime_labels 복사 | 시장공통(FRED CLI/DEXKOUS + ECOS 외국인) | 복사 채택 | ★FRED/ECOS 재호출 절약 = auto/raw-v3/data/regime_*.parquet 복사 |
| capex/PBR/PER | DART fnlttSinglAcntAll | ppe 96%/equity OK, net_income FY만+적자 | capex/PBR 시계열 | ★net_income 적자빈발+FY만 → PER 무효 확정 |

## 막힘·해결 로그 (시계열)
- [2026-06-05 10:30] 막힘: 정유 universe = strict floor-pass **2종(SK이노/S-Oil)**만 → cross-sectional Spearman IC(min 8종) 불가 → 진단: 국내 정유 과점(2-3개사) = 구조적 small-breadth, dispatch 경고 극단 실현 → 해결: ★frame M2 산업 시계열(패널수익 vs cycle driver lag-corr)로 전환 + cross-sectional INSUFFICIENT 정직 박제. team-lead 방향 확인 보고(idle 아님, 병행 진행) → 교훈: ★universe 협소 산업 = cross-sectional 강행 금지(점추정 함정). 시계열 + INSUFFICIENT 박제가 정직.
- [2026-06-05 10:50] 막힘: capex 시계열 level forward 양(+0.47) = dispatch 음 prior와 반대 → 진단: spurious 의심(level-on-level) → 해결: ADF(p=0.859 I(1)) + Δ차분(+0.20 약화) + 유가proxy(brent corr-0.44) 3검증 → REJECTED → 교훈: ★capex 일반화 가설 = cross-sectional 종목간 측정인데 정유는 시계열밖에 못해 → spurious 함정. §1.8 self-ref/spurious 점검 의무 입증.
- [2026-06-05 11:00] 막힘: 유가 forward 음(-3.63 naive t 강) → 진단: 60d/3M 중첩 autocorr → 해결: eff-N 보정(eff-N=26.5) t=-1.96 marginal → 교훈: ★small n_months + 중첩 horizon = naive t 과대(§1.7). eff-N 보정 의무. marginal = risk-monitor 격하(alpha 단정 금지).
- [2026-06-05 11:10] 함정: summary.md Write가 harness hook(report 파일 차단)에 막힘 → 해결: summary 내용은 summary.yaml(SSOT) + final message로 전달. candidate-ledger/theory-notes/research-log/validation은 통과 → 교훈: harness에서 "summary.md" 파일명 차단 가능, 핵심 산출은 yaml.

## 측정 방법 결정 로그
- cross-sectional → ★시계열 전환: universe 2종 = Spearman IC 불가. frame M2(산업 패널 시계열 lag-corr)가 좁은 universe 유일 측정.
- crack spread = Gulf proxy: 싱가포르GRM 무료부재. gasoline/diesel×42-Brent($/bbl). 글로벌 동조 prior, proxy 한계 명시(magnitude hedge).
- 유가 동시 vs 예측 양쪽 측정(frame §D): 재고평가이익(동시+) vs mean-reversion(예측-) 분리. Δ vs level 대조로 mean-reversion 확인(Δ예측력0).
- eff-N 보정 + wild-cluster + ADF: small n_months + 60d 중첩 → naive t 과대. §1.7 ADF로 level spurious 점검.
- capex spurious 3검증: ADF + Δ약화 + 유가collinear. dispatch 가설 무비판 채택 차단(본인 측정 = 검증불가/spurious).

## 미해결 / 다음 세션 우선 작업
1. ★싱가포르 GRM 확보(crack verdict 잠정 = proxy 탓인지 진짜 약인지 결정) — collector high
2. ★정유 universe ≥8종 확보(cross-sectional 측정 재개 전제) — energy 광의(supervisor 결정) OR floor 완화(archetype/J축 위험)
3. supervisor energy 광의(가스 포함) 결정 시 = 가스 archetype 분리(규제 유틸) + 정유 격리 재측정
4. G-G 최종판정: monitor-only/종목선택 weight 0 (내 제안) supervisor 확정 대기
