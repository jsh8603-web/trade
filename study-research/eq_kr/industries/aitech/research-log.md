---
tags: [type/research-log, domain/equity, sector/aitech]
date: 2026-06-05
purpose: AItech 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# AItech(인터넷·게임·소프트웨어) 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| universe | FDR KRX-DESC 키워드 매칭 | ★1차 305→50종에 비-AItech 대량 혼입(SK지주/KT통신/롯데쇼핑/captive SI/로봇/의료AI/결제HW) | ✅ EXCLUDE 화이트리스트 + 핵심종목 화이트리스트 → 26종 | ★frame M.11 = KRX 키워드 부정확. "소프트웨어/IT서비스" 매칭이 그룹 captive SI(현대오토에버/포스코DX)·로봇(로보티즈)·의료AI(루닛) 폭넓게 포섭 → 육안 sanity + EXCLUDE 의무 |
| 가격 패널 | pykrx OHLCV loop | 26종 1818일 2019-01~2026-05 OK | ✅ | semiconductor 동일. 종목별 0.3s sleep, background |
| regime (macro/KRW/flow) | semiconductor collect_regime 재사용 | ★KOSPI 전체 = 산업 무관 → regime_labels.parquet 복사 | ✅ | regime(FRED CLI/DEXKOUS + ECOS 외국인) = 시장레벨 = 산업 독립. 재수집 불필요(복사로 89개월 동일 검증) |
| valuation 횡단면 | pykrx 시장 스냅샷 API | KRX 인증 차단(빈 응답) | DART fnlttSinglAcntAll PIT 재구성 | battery/semi 동일 함정. DART BPS/EPS + pykrx 가격 → PBR/PER |
| valuation PER | DART net_income | ★게임 적자 40%(양수 59.6%) → 양수만 산출 | ⚠️ 편의 명시 | bio 동형 = event_driven 적자종목 PER 무효. E/P 대체 필요(collector_plan high) |
| R&D proxy | DART intangible/assets | coverage 93%, IC +0.004 무신호 | ❌ INSUFFICIENT | ★SW 개발비 자본화여도 cross-sectional 예측력 부재. 기대(양 prior)와 다름 |
| global cycle proxy | semiconductor SOXX → QQQ/NVDA 교체 | forward 전 lag 비유의(REJECTED) | proxy 교체 OK | AItech = NASDAQ(QQQ) cycle. 단 forward 예측력 부재(§D falsifier 정상) |

## 막힘·해결 로그 (시계열)

- [2026-06-05 11:35] 막힘: aitech 디렉토리 신규(없음) → 진단: collect부터 신규 수집 필요 → 해결: semiconductor 양식 미러(collect.py 키워드만 SEMI_KW→AITECH_KW) + regime_labels 복사 → 교훈: regime 은 시장레벨이라 산업 간 복사 가능(재수집 비용 절감).
- [2026-06-05 11:35] python 경로 함정: bash `/d/...` 경로를 python에 직접 주면 FileNotFoundError → 진단: python은 Windows 경로(`D:/...`) 필요 → 해결: `r'D:/...'` raw string → 교훈: PYTHONUTF8=1 + Windows 절대경로 일관 사용.
- [2026-06-05 15:59] 막힘: 1차 universe 50종에 비-AItech 혼입 → 진단: FDR 키워드 오분류(frame M.11) → 해결: EXCLUDE 화이트리스트 + 핵심종목 화이트리스트 26종 정제 → 교훈: ★육안 sanity check 의무, 키워드 단독 신뢰 금지.
- [2026-06-05 16:09] 막힘: measure_walkforward "I/O operation on closed file" → 진단: measure_conditional import 시 그 모듈 sys.stdout 래핑 + walkforward 자체 래핑 = 이중 TextIOWrapper 충돌 → 해결: json 은 정상 저장됨(print 전 완료) → json 직접 read → 교훈: 모듈 import 시 stdout 래핑 side-effect 주의, 결과는 json 박제로 회수.
- [2026-06-05 16:18] ★핵심 발견: momentum 부호 = 음(reversal) = team-lead growth=battery 가설 반증 → 진단: 게임 event_driven buy-the-rumor + 2022 버블붕괴 reversal → 해결: archetype 정정(growth→value+event_driven), candidate-ledger memory enum 기록 → 교훈: ★"성장주=momentum continuation" 사전 단정 금지, 부호는 데이터 판정.
- [2026-06-05 G-C audit] ★좀비 carry-forward 발견(audit): 셀바스AI(108860) 거래정지 284거래일 px=4155 고정+amt=0 → halt 기간 저모멘텀(=reversal 매수대상)+forward 음 = reversal IC 인공 증폭 → 진단: 거래정지 carry-forward 가격이 가짜 신호 → 해결: zombie(amt==0 OR 연속동일종가≥10일) NaN 마스킹(reject≠missing, measure_zombie_check.py, 2462 cells) 재측정 mom -0.1055→-0.0963(~9% 과대) t -2.58→-2.59 부호·유의 불변, pbr Δ=0.0(공시후 진입) → 교훈: ★mom/vol 신호는 거래정지 좀비 공통 오염원(bio 코오롱티슈진·케어젠 + aitech 셀바스AI 동일 패턴), 가격신호 측정 시 amt==0/dup-price 마스킹 의무. validated_alpha(pbr)는 좀비 면역.

## 측정 방법 결정 로그

- ★momentum 부호: team-lead 지시 = one-sided 미고정(양/음 둘 다 경제동기) → 부호 자체를 archetype 판별 측정 대상. 결과 음(reversal) = growth 반증. (battery 양 continuation 과 대조.)
- ★valuation primary 판정: measure_valuation 독립 BY family(m=8)에서 pbr 전 horizon 생존 → primary tradeable. ★conditional 36셀 통합 family(m=105)에선 미생존 = multiplicity 차이(M_eff 미통합). 둘 다 보고(over-claim 회피).
- ★size 위장 점검(Q1): 26종 small-universe → 저PBR=소형주 confound 우려 → Fama-MacBeth ret~PBR_rank+Size_rank 매월 회귀. PBR|Size t=-3.51 유의 = 독립 alpha 입증.
- ★flow_strong_buy = aitech 핵심 conditioning(semiconductor 의 KRW_weak 와 다름): measure_subcluster.py 로 flow interaction 정식 측정. mom_12_1 t=-2.71 유의 + walkforward OOS 재현. measure_conditional 기본 KRW_weak interaction 은 aitech 에선 비유의.
- ★per_z episode 종속 발견(Q2): sub-period 2019-21 +0.044 / 2022-26 -0.099 부호 불일치 → 격하. 버블기 고PER 강세 → 붕괴후 저PER. = robustness 검정이 over-claim 차단.
- 24M_value: overlap degenerate(eff_N≈2.5, frame M.12) + 26종 small-universe → t 과대(t=-7.70/-7.98) hedge. primary = 12M.

## 미해결 / 다음 세션 우선 작업

1. ★per_z E/P(earnings yield, 음수익 처리) 대체 측정 — 게임 적자 40% 양수편의 해소 (collector_plan high).
2. ★PIT universe 멤버십 — 게임주 상폐多(P2E 붕괴) = 생존편향 위험 큼 (collector_plan high, I축 PARTIAL→PASS).
3. DAU/MAU·광고매출·게임 신작 ledger event study (internet 광고/game 신작 직접지표, medium).
4. sub-cluster 분리 측정 — momentum reversal game-dominant 확정 시 game-only universe IC 재현.
5. EV/EBITDA (compounder primary) + KR HY credit spread (현 US proxy).
