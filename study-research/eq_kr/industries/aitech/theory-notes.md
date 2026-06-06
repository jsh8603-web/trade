# theory-notes — AItech(인터넷·게임·소프트웨어) 산업 cycle 이론 (S1 학술 ground)

> SSOT = frame.md v2 §3 Layer 3 AItech + frame-v3 §M. as_of = 2026-05-31.
> ★S1 = 측정 前 이론·메커니즘·부호 가설 추출(자문/리서치 결론·목표가는 증거로 안 씀, 메커니즘만). source 명시.
> ★본 notes = 가설의 원천. 실측 증거 = validation-*.md / summary.yaml. 측정 결과와 이론 연결 1줄씩 박제.

## 1. archetype 분류 + ★momentum 부호 (team-lead 핵심 질문 = 데이터 판정 완료)

### 1.1 사전 가설 = growth (battery 동형, momentum continuation)
- team-lead 지시 = "성장주(growth) = battery 동형 momentum continuation 가능성, value 보다 growth metric".
- **이론 근거 (continuation)**: Jegadeesh-Titman(1993) 모멘텀 = 실적 성장 모멘텀 → 주가 연속. 성장주는 earnings revision momentum 강 → 12-1 momentum 양(+) prior.

### 1.2 ★실측 판정 = momentum REVERSAL (음, growth 가설 반증)
- **측정 결과 (validation-metrics-v3.json)**: mom_12_1 12M IC **−0.106** (t=−2.58), mom_6 12M **−0.103** (t=−2.48). 전 horizon 음. = ★momentum **reversal** (battery 양 +0.086 과 반대 부호).
- **walk-forward OOS**: mom_12_1 IS −0.077 → OOS −0.049 부호유지 / mom_6 OOS −0.064 = ★reversal 부호 OOS 견고(in-sample artifact 아님).
- **메커니즘 재해석 (reversal)**: ① 게임 event_driven = 신작 기대 급등(buy-the-rumor) → 출시 후 차익실현(sell-the-news) = ★Daniel-Hirshleifer-Subrahmanyam(1998) overreaction reversal. ② 2021 플랫폼/메타버스/P2E 버블 → 2022 폭락 = 큰 진폭 평균회귀. ③ 한국 모멘텀 약효(Cheema-Nartea 2017, NCBI PMC11023228) 위 성장주 변동성 reversal.
- ★**sub-cluster 분해 (validation-subcluster-v3.json)**: momentum reversal = **게임 dominant** (game −0.113 vs internet +0.003 무신호 vs saas −0.033). = 게임 event_driven 메커니즘 정합.
- → ★**결론: growth=battery 사전가설 반증. AItech = momentum reversal(음). archetype = growth continuation 아님.**

### 1.3 ★실측 = valuation premium 강 (asset_stable/value 작동, consumer/telecom 동형)
- **측정 (validation-valuation-v3.json)**: pbr_z 12M IC **−0.183** (t=−7.98), per_z 24M −0.129 = ★저PBR/저PER 종목 강세. ★BY 생존 7개(pbr 전 horizon + per 일부) = semiconductor(pbr 1개만 생존)·auto(PER 무효)보다 훨씬 강.
- **walk-forward OOS**: pbr_z y_60d IS −0.060 → OOS −0.123(강화) / per_z y_60d IS −0.010 → OOS −0.083(강화) = ★valuation primary tradeable OOS 견고.
- **메커니즘**: Fama-French(1992) value premium + Asness QMJ. ★AItech 성장주여도 2022 버블 붕괴 후 valuation dispersion 커짐 → 저평가(저PBR) 종목 mean-reversion 강. = asset_stable/value 작동.
- ★**archetype 정정**: 사전 growth/event_driven 가설 → 실측 = ★value premium 작동 + momentum reversal = **asset_stable + cyclical(peak reversal) 혼합**. growth(momentum continuation)는 데이터로 반증.

## 2. sub-cluster 이질성 (frame line 62 + A-4, ★측정 확인)

| sub-cluster | 펀더멘털 driver | archetype | ★momentum reversal | valuation |
|---|---|---|---|---|
| internet (NAVER/카카오) | 광고 cycle + 커머스 + 플랫폼 DAU | compounder/asset_stable | ★무신호(+0.003) | pbr −0.102 작동 |
| game (크래프톤/엔씨/넷마블/펄어비스) | ★신작 출시·매출 event_driven | event_driven/cyclical | ★dominant(−0.113) | pbr −0.108 작동 |
| saas (삼성SDS/더존/안랩) | B2B 구독 ARR + AI 수혜 | compounder | 약(−0.033) | pbr −0.095 작동 |

- ★**A-4 부호점검 결과**: valuation(pbr/per/vol) = 3 cluster **부호 일관**(전부 음) = cancel 없음, 통합 유지 가능. momentum reversal = game dominant(internet 무신호)이나 부호 cancel 아님 → ★통합 sleeve 유지(분리 트리거 미발동), 단 momentum 신호는 게임 비중 큰 종목군 한정 발현 명시.
- 출처: 미래에셋/삼성증권 인터넷·게임 in-depth(NAVER 광고 cycle, 게임 신작 파이프라인 커버리지), 메타/알파벳 광고 cycle 학술(Goldfarb-Tucker 2011 advertising).

## 3. 거시 노출 (성장주 = 금리·risk-off 민감, ★측정 확인)

- **측정 (validation-cross-v3.json common_factor β, HAC)**:
  - ★**credit β = −0.071 (t=−2.27 유의)** = HY spread 확대(risk-off) 시 AItech 약세. 성장주 고베타 = risk-off 민감 정합(bio 동형).
  - rate β = −0.036 (t=−1.44, 약 음 = 듀레이션 가설 방향 정합하나 비유의). VIX/oil 비유의. dollar 약 음(t=−1.16).
- **메커니즘**: 성장주 = 긴 듀레이션(미래 현금흐름 비중↑) → 금리·할인율 민감(Gordon growth model). 2022 금리인상기 멀티플 압축 폭락이 이를 입증. ★단 본 표본(2019-26 35개월 월간 β)에선 rate 비유의 = "방향성 약 prior".
- credit = US BAML HY OAS proxy(KR HY 부재, n=35 small) → tentative.
- ★**customer momentum (QQQ/NVDA forward)**: 전 lag 비유의(REJECTED) = §D forward-alpha falsifier 정상 작동. 한국 AItech = 글로벌 tech cycle contemporaneous 동조이나 forward 예측력 부재 → RegimeGlasso Ω 흡수.

## 4. conditional IC = regime 따라 발현 (dispatch 원의도, ★측정 확인)

- **★flow_strong_buy regime = reversal 증폭축**: 외국인 강매수기에 mom_12_1 −0.150(wc_p=0.0145), vol_60 −0.124(wc_p=0.01), pbr_z −0.114(wc_p=0.0155) 음 증폭(단 underpowered n=17-18). family_2 interaction mom_12_1 t=−2.71(유의) + walk-forward OOS t=−2.71 재현 = 견고.
  - 메커니즘: 외국인 강매수기 = passive/지수 매수 지배 → 개별 모멘텀 종목 차익실현 + 저평가 종목으로 rotation = reversal 증폭. Choe-Kho-Stulz(2005) 외국인 flow herding.
- **★per_z KRW_weak = conditional 최강 cell**: per_z y_60d KRW_weak wc_p=0.0025 (powered, n=34, IC −0.154). walk-forward IS −0.135 → OOS −0.159(강화). = 원화약세기(수출 게임 stress) value 증폭.
- ★단 ALL 36셀 BY 미생존(m=105, raw_p_min=0.0005) = M_eff 미통합 + small-n. KRW_weak interaction term은 비유의(t=−0.70) = pooled 자유도선 약. = 동적가중 정당화(unconditional 약신호가 regime 증폭).

## 5. Layer 1 펀더멘털 (R&D/무형자산 = SW·게임 개발비, 측정 예정)

- SW/게임 = R&D·개발비(무형자산) 집약. 게임 개발비 = 무형자산 자본화(자산화) → intangible/asset 비중 큼.
- ★Cooper-Gulen-Schill(2008) asset growth anomaly = 자산 급증 종목 forward underperform(음 prior). 단 SW는 R&D = 성장 prox(양 prior 경합).
- → measure_fundamentals_cycle.py 로 측정(이연 금지). 결과 = validation-fundamentals-cycle-v3.json 박제.

## 6. 정직 단서 + 한계

- ★universe 26종 small (game 13/saas 8/internet 5). cross-sectional avg N ~24/월 = 충분. sub-cluster 분해 시 internet 5종 = small-n hedge.
- ★게임 적자 비중 40%(net_income 양수 59.6%) = PER 산출 시 양수만 → 적자종목 제외 편의 가능(bio 동형). PBR(equity 100% 양수)은 면역.
- 24M_value horizon = overlap degenerate(eff_indep_N ≈ 61/24 ≈ 2.5, frame M.12) → primary 증거 = 3M/6M/12M, 24M 보조. 단 26종 small-universe → t 과대 가능(telecom/auto 동형 hedge).
- 생존편향 = FDR 현재 스냅샷(생존종목). delisted/M&A 누락 = PIT 멤버십 collector_plan high. ★게임주 상폐 多(P2E 붕괴기) → 생존편향 위험 상대적 큼.

## 7. 출처 (source URL/ref)

- Jegadeesh-Titman 1993 JF (momentum) / Daniel-Hirshleifer-Subrahmanyam 1998 JF (overreaction reversal)
- Fama-French 1992 JF (value premium) / Asness-Frazzini-Pedersen QMJ 2019
- Cheema-Nartea 2017 (Korea momentum weak) / NCBI PMC11023228 (한국 모멘텀 약효)
- Choe-Kho-Stulz 2005 RFS (외국인 flow herding Korea) / Cooper-Gulen-Schill 2008 JF (asset growth)
- Goldfarb-Tucker 2011 (online advertising) / 미래에셋·삼성증권 인터넷·게임 industry in-depth (커버리지 = 메커니즘만 추출, 목표가·투자의견 증거 미사용)
