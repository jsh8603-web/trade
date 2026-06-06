---
tags: [type/research-log, domain/equity, sector/shipbuilding]
date: 2026-06-05
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# 조선(shipbuilding) 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| universe | FDR KRX-DESC 키워드 | "조선/선박/해양/플랜트/기자재" 단독 = 오분류 大 | ★Industry "선박 및 보트 건조업" + 화이트리스트 | ★현대모비스(자동차)/두산에너빌리티(발전)/한국전력/HMM(해운)/포스코인터(상사)/GS건설(건설) 혼입 — 블랙리스트 필수(frame §M.11) |
| 가격 패널 | pykrx OHLCV loop | 16종 1818일 OK | ✅ | 신규상장 多(HD현대중공업 2021 재상장 1146행/대한조선 200행/현대힘스 567행/티엠씨 110행) = look-back gap |
| valuation | DART fnlttSinglAcntAll | 356 rows/16종 OK | ✅ PBR/PER | ★조선 적자 多(2021-22) → PER 계산가능 종목 시기별 5~13종 변동 = small-universe |
| capex/재고/R&D | DART dart_extended | 371 rows, coverage inv 92%/ppe 100% | ✅ 측정 | ppe 100% coverage(조선 = 유형자산 큰 장치산업) |
| regime | 반도체 collect_regime.py 재사용 | FRED CLI/USDKRW + ECOS 외국인flow | ✅ (시장 공통) | regime = 종목 무관 시장 변수 → 반도체것 복사 정당 |
| 운임/유가 supply-chain | yfinance BDRY/CL=F/BOAT | 측정 OK but forward 비유의 | ❌ REJECTED | ★주가가 운임 선행(H8) → 운임 lagged forward 예측력 부재 |
| Clarkson 수주/SCFI 운임 | 유료 | 미시도(유료) | ⏳ 이연 | collector_plan high — 조선 cycle 핵심 timing 변수 |

## 막힘·해결 로그 (시계열)
- [2026-06-05 10:30] 막힘: 조선 키워드 universe = 비조선 6종 혼입(현대모비스/두산에너빌리티/한국전력/HMM/포스코인터/GS건설) → 진단: "해양/플랜트/기자재" 키워드 폭넓음 → 해결: KRX Industry "선박 및 보트 건조업" core + 조선기자재 화이트리스트 + 명백 비조선 블랙리스트 → 교훈: frame §M.11 화이트리스트 의무 = 육안 sanity check 필수.
- [2026-06-05 10:35] 막힘: 시총 floor 3000억(반도체/battery 동일) 통과 = 9종, ADV 30억 = 4종뿐 = 횡단면 IC 측정 불가능 수준 → 진단: 조선 = 소수 대형 + 영세 기자재 구조 → 해결: floor 완화(시총 1000억/ADV 5억) → 16종 확보 + tier_strict 라벨(유동성-티어 IC 점검) → 교훈: ★산업별 universe breadth 본질적 차이, floor 는 frame §M.6 CPCV 캘리브레이션 대상이라 산업 특성 반영 정당. ★small breadth hedge 명시 의무.
- [2026-06-05 11:00] 막힘: per_z 24M IC +0.204(t=4.47, BY 생존) — 부호가 양(역방향)? → 진단: PER 적용 = 흑자 종목만(avgN 6.9), 조선 적자기(2021-22)엔 분모 음 → 흑자전환+슈퍼사이클 급등이 표본 지배 → 해결: walk-forward OOS 검정(6M/12M 부호반전 확인) + within-period(2020-21 적자전환기 IC +0.16~0.33) → ★artifact 확정 격하(frame §M.12 24M degenerate + small-universe inflation) → 교훈: ★BY 생존이 곧 tradeable 아님. degenerate horizon + small-universe + 구조전환 표본 = over-claim 함정.
- [2026-06-05 11:15] 발견: vol_60(저변동성)이 ★유일하게 walk-forward OOS 부호유지(IS -0.065→OOS -0.049) + strict tier(고유동성 9종)서 더 강(-0.078) = microcap artifact 아님 → 진단: low-vol anomaly(bio 동형)가 조선에도 약하게 작동 → 결론: TENTATIVE DIRECTIONAL(방향 prior, BY 미생존 + CI 0포함 = magnitude 비유의).
- [2026-06-05 11:30] 종합: ★전 신호 BY/Bonferroni 미생존(통합 m=165 survivors=0). family_2 interaction(KRW_weak) 전부 비유의(반도체와 차이) → G-B 트리거 충족 → ★단 Gemini 리서치(산업 베타 지배 H9) = "방법 결함 아닌 신호 본질 구조적 약" 근거. team-lead G-B 자문 발동 판정 보고.

## 측정 방법 결정 로그
- **universe floor 완화**: 시총 1000억/ADV 5억 (반도체 3000억/30억 대비). 이유 = 조선 협소 universe(strict 9종) = 측정 불가 → 완화 후 16종. 대안(strict 9종 고수) 기각 = 횡단면 IC 통계력 0. tier_strict 라벨로 유동성-티어 별도 점검(frame §M.1 ⑱).
- **capex 부호 prior = two-sided**: team-lead 박제(capex 일반화) = 조선 orderbook 특수성. 자동차/반도체 음 prior(asset growth) one-sided 그대로 적용 금지 → two-sided(음약+양가능) 표기 후 데이터 판정. 결과 = 무신호 → ★one-sided 단정 회피가 정답(음 prior 박았으면 데이터 충돌).
- **per_z 24M artifact 격하**: BY 생존했으나 frame §M.12(24M degenerate eff_N≈2.5 + small-universe inflation) + walk-forward OOS 6M/12M 부호반전 = artifact 확정. tradeable 자격 박탈. over-claim 회피.
- **supply-chain proxy = BDRY/CL=F/BOAT**: 반도체 SOXX/NVDA → 조선 운임/유가/글로벌조선. 직접 수주(Clarkson)/운임(SCFI) 유료라 ETF proxy. forward 비유의 = REJECTED(§D falsifier 정상 작동, 주가 선행 H8 정합).

## 미해결 / 다음 세션 우선 작업
1. ★PBR 밴드 timing 레이어 측정 (cross-sectional 무효지만 시계열 PBR 밴드 = 별개 유효 가능, 증권사 표준). 산업 eq-weight PBR 밴드 → 산업 forward timing 신호.
2. Clarkson 신조선 수주 + SCFI 운임 직접지표 (collector_plan high) — 조선 cycle 핵심 timing 변수(cross-sectional 아닌 regime conditioning).
3. EV-EBITDA (DART 부채/현금 추가) — cyclical primary_metric.
4. PIT universe 멤버십 (신규상장 多 = look-back gap 큼, 생존편향 보정).
5. ★G-B 자문 발동 여부 = team-lead 판정 (산업 베타 지배 = 신호 본질 약 근거 강하나, 묶음방식 자문 양식으로 "cross-sectional 약 + timing 레이어 보강" 방향 확인 가치).

## [추가] PBR 밴드 timing 부활 측정 (team-lead 지시 2026-06-05)
- [2026-06-05 12:30] 지시: cross-sectional 약신호 → ★섹터 timing(PBR 밴드 시계열) 부활 측정. candidate-ledger 이연분 측정.
- [2026-06-05 12:45] 구현: measure_sector_timing.py — 산업 합산 PBR(Σ시총/Σ자본 PIT rcept_dt) rolling36M z → 산업 eq-weight forward IC. wild-cluster + walk-forward + regime conditional.
- [2026-06-05 13:00] 결과: ★부활 실패. (a) 12M IC +0.373 BY 생존했으나 ★artifact — walk-forward IS 음(-0.582 mean-reversion 정상)→OOS 양(+0.412) 부호반전 = 슈퍼사이클 trend 가 mean-reversion 뒤집음(2024-06 PBR_z +1.88 高밴드→12M_fwd +104.6%). (b) 1M/3M = OOS 부호유지(음)하나 IS 극단(-0.49/-0.66 n27)→OOS 소멸(-0.026/-0.024). (c) n_eff 10(PBR_z persistence) = 통계력 약.
- 진단: ★per_z 24M cross-sectional artifact 와 동일 패턴(BY생존≠tradeable, 슈퍼사이클 구간 부호반전). PBR_z 강한 persistence(n=85 → n_eff 10)로 단일 시계열 통계력 본질적 약.
- 교훈: ★조선 = cross-sectional 도 섹터 timing 도 약. 슈퍼사이클(2023-26)이 mean-reversion·value 신호를 전부 trend 로 반전. = "측정했으나 약" 정직 기록(deferral 아님). 섹터 timing sleeve 격상 불가.
- 결정 로그: 절대 PBR 레벨 mean-reversion(rolling z 아닌 0.5x/2x 밴드)은 in-sample cherry-pick 위험 → 미측정(walk-forward 가 이미 rolling z 로 답 줌). 슈퍼사이클 종료 후 OOS = 미래 보너스(현 검증 완주).
