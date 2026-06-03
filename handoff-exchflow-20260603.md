---
name: handoff-exchflow-20260603
description: 거래소 reserve/flow 6단계 study + 폐기지표 현-프레임 재검 + candidate 16 논문대조 카탈로그 + SOPR false-prior 정정. 자기완결 재개.
type: project
date: 2026-06-03
tags: [handoff, crypto, exchange-flow, indicator-review, candidate-catalogue]
---

# 거래소 flow/reserve study + 폐기 재검 + candidate 카탈로그 (2026-06-03)

> 인계 체인: [handoff-coin-adopted-horizon-20260603.md](./handoff-coin-adopted-horizon-20260603.md)(직전) → 본 파일.
> ledger: [study-research/_wire/indicator-ledger.md](./study-research/_wire/indicator-ledger.md) crypto 섹션.
> ⛔ go-live=사람 게이트. push 금지. Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.

## 0. 이 세션 한 일 (요약)
1. **★false-prior 정정**: "SOPR·realized-cap·LTH/STH = CM Community 무료 자율가능"(직전 handoff §6·memory) = **FALSE**. CM Community btc.csv 32컬럼에 부재 + anonymous API 403 = 유료게이트(Glassnode/CQ/CM Pro). E97 latch가 fetch 착수 전 적발. promotion-log ERROR 박제.
2. **★대체 발견**: CM Community 무료에 **거래소 flow(FlowInEx/FlowOutEx)+reserve(SplyExNtv) 2011~2026** 존재 → 6단계 study.
3. **거래소 reserve→vol = candidate**(throttle), reserve→수익 = 기각, netflow 일별 = rejected_provisional.
4. **폐기/기존 지표 현-프레임 재검**: realized_vol/active_addr/netflow/funding/mvrv → 프레임 업그레이드에도 부활 안 함(기각 robust 재확인).
5. **candidate 16 논문대조 카탈로그**(§4).

## 1. 거래소 reserve→vol 6단계 (S2~S5 완주, S6 audit 잔여)
- **데이터**: CM Community `coinmetrics-btc-community.csv`(다운로드 완료), SplyExNtv(거래소잔고)·FlowInEx/OutEx 2011~2026 n=5790. ETH=`coinmetrics-eth-community.csv` 2015~.
- **신호**: resv_chg30(잔고 30d log변화)·resv_z(수준z). nf_z(netflow 상대 z).
- **2-신호 분리(자문 R1 만장일치)**:
  - ★**①잔고→수익(directional) = 완전기각**: BTC 약세 fwd30 −0.26(p0.001)이나 epoch decay E1 −0.37→E2 −0.31→**E3(2022-26) −0.09 효율화소멸**(AMH) + cross-asset ETH ≈0/양. 자문 "BTC 자체 시계열이 유죄, ETH 핑계 불필요".
  - ★**②잔고→변동성 = candidate(one-sided vol-throttle)**: +0.35(p0.000), 15년 안정, FDR 18/45 생존, walk-forward 부호일관, **주봉 비중첩 +0.32 p0.000 n780**.
- **S4 결정게이트 전부 PASS**(자문 지목 직접검증):
  - (a) ⊥HAR-RV +0.179 / ⊥GARCH(1,1) +0.183 = 정식 vol모델 중복 아님(claude '진짜 숫자').
  - (b) **cross-indicator(진짜 게이트)**: ⊥HAR+MVRV+mom+funding **+0.191 p0.016**. MVRV/모멘텀 무중복(1차vs2차 모멘트), funding만 부분감쇠(+0.150) 흡수 안 됨.
  - (c) **역인과 해소**: 주봉 lead-lag reserve 선행(lag−1주 +0.191 ≫ vol선행 +0.035). 일별 "vol 선행"은 빈도 artifact(claude '일별 부적절' 정확).
  - (d) **cross-asset-class(VIX)**: ⊥VIX 전체 +0.185·**ETF era +0.201 p0.036**(VIX 제거하니 ETF era 유의↑=약화 일부는 common-factor 오염). VIX→crypto vol +0.039 약 = crypto 고유, VIX throttle 대체불가=**build**.
- **★S6 15축 audit 완료(2026-06-03, 독립 subagent ac148e3f)=CONDITIONAL**: 수치 7/7 재현·fabrication 없음·claim1(+0.35·⊥HAR +0.18) 전축 견고·cross-asset ETH 붕괴=자산특수(BTC ETH기간서도 +0.31). 정정 2건: ①GARCH 통제=rv22 재탕(corr0.875) 독립증거 아님 ②claim3(+0.191)·claim4(ETF VIX +0.201) 다중비교 보정 후 탈락+ETF era ⊥HAR p0.14=라이브 약화 명시. → candidate(코어 robust/라이브·cross-indicator marginal). audit=.audit-exchflow.py.
- **caveat(승격 전 잔여)**: 라이브(ETF era 2022+) 약화 / CM 거래소라벨 커버리지(cross-measurement 타 provider=유료게이트 미검) / 메커니즘 매개(order-book depth) 미측정 / go-live 사람게이트.
- **용도**: one-sided throttle(고변동 예측시 노출축소 전용, 비용 bounded → cross 약증거 감내자격, 자문 양쪽 수렴). 엔진 gross=target_vol/realized_vol에 forward-looking reserve term 결합이 자연스런 배선점(go-live).
- **산물**: `.p2-exchflow.py`(그리드)·`.p2-exchflow-s4.py`(rv20 incremental·trend직교·epoch)·`.p2-exchflow-s4b.py`(HAR/GARCH·ETF era·lead-lag)·`.p2-exchflow-s4c.py`(funding/VIX/주봉)·`.p2-exchflow-cross.py`(BTC/ETH) + `-result.json`. 자문=`.consult-exchflow-briefing.md`·`.consult-exchflow-R2.md`(raw 응답 = 이 세션 transcript).

## 2. ★"cross/regime" 정의 (자문 R2 수렴 — 사용자 지시로 재정의, 일반 규칙화 가치)
사용자 정정: "cross는 코인 내부(BTC/ETH)가 아니라 타 자산군·타 지표". 자문 R2 수렴:
- **cross-indicator(지표교차) = 진짜 채택 게이트(1순위)**: 기존 코인신호(특히 funding=청산 한 사건의 그림자) 재포장 아닌 incremental인가.
- **cross-asset-class(자산군교차, VIX/MOVE) = 교란통제(2순위)**: common factor(글로벌 risk-off) 분리. 실패하면 "VIX throttle이 우위"(build-vs-buy).
- **cross-asset 내부(BTC/ETH) = 비진단적 강등**: 도구가 ETH선 staking/DeFi로 다른 잠재변수 측정 → 실패가 진단 안 됨. tie-breaker only.
- **cross-measurement(측정교차) = BTC/ETH 대체 1순위(claude)**: 같은 잠재변수를 다른 provider/방법(Glassnode vs CQ vs CM, netflow vs reserve, per-exchange)으로 재측정. 1 provider만 뜨면 측정 artifact.
- **regime**: vol-regime 분할은 순환/look-ahead(30d라벨이 t+1..t+30 타깃과 겹침) → **연속통제만**. 적합 ex-ante 축 = 유동성/microstructure·pre/post-ETF(구조이벤트≠달력컷)·긴축완화. ★**무조건부 신호 먼저 통과 후 regime은 sizing 정련만, 죽은 신호 부활 금지**.

## 3. 폐기/기존 지표 현-프레임 재검 (.p2-revisit.py)
프레임 업그레이드(vol축+FDR+cross-indicator+주봉)에도 **기존 기각 robust 재확인**:
| 지표 | 현-프레임 재검 결과 | verdict |
|---|---|---|
| realized_vol(vol-of-vol) | vol축 raw +0.30~0.36 강하나 **⊥HAR +0.008 완전흡수** | rejected_prov 유지(HAR 중복, sizing은 forecast 아닌 level scaling 별개) |
| active_addr | vol/return 강세 raw 유의하나 **⊥HAR+타지표 전부 흡수** | rejected_prov 유지(reserve/mvrv 중복) |
| netflow(일별) | 수익 ≈0, vol +0.05 약·흡수 | rejected_prov(일별 directional 무알파) |
| mvrv directional | +0.15~0.27 양(반전 아님) | 기존 "momentum proxy" 재확인(directional 아님) |
| **funding→vol 약세** | −0.151 ⊥HAR+타지표 생존(p0.017) | ★신규 marginal(n870·약세 only, 작은 후보) |
| **reserve→vol** | ⊥HAR+타지표 +0.17 p0.03·주봉 +0.32 | ✅ 유일 robust(§1) |

## 4. ★candidate 16 논문대조 카탈로그 (사용자 "20개 후보 + 참고논문 보고")
> 참고논문 SSOT: `study-research/crypto/raw/{crypto-factor-papers,crypto-regime-dependence-papers,measurement-methodology-papers}.md`.

### A. 측정 완료·현-프레임 적용됨 (재탐구 불요)
| candidate | 논문 ground | 상태 |
|---|---|---|
| coin_tsmom / btc_price | LTW 2022 JF·2021 RFS(TS momentum 주~월)·Han-Kang-Ryu(net-cost)·MOP TSMOM | net Sharpe 1.42, 단기트랙 유일 carrier. adopted후보(go-live). |
| coin_kimchi_premium | Economic Modelling(비선형)·Schmeling(분절) | throttle 확정. 잘 grounded. |
| coin_global_liquidity_m2 | factor-papers §7(기관, 동료심사 약·LTW 2021 null=시대) | single-episode artifact, throttle만. under-powered(6-24M=8~16 독립관측). |
| coin_real_rate | §7 | regime candidate(약세 −0.48), 셀별 under-powered. |
| coin_breadth_altseason | size-reversion | net-cost 탈락(실행불가). 저빈도 리밸런싱 부활조건. |
| coin_volprice_corr | 약 | momentum 변형(corr 0.51), 독립성 낮음. |
| coin_exchange_reserve | Chi-Chu-Hao(flow→vol robust) | ★이 세션 vol candidate(§1). |

### B. 데이터 게이트(유료·미측정, 논문 grounded — 부활=데이터 확보)
| candidate | 논문 ground | 게이트 |
|---|---|---|
| coin_sopr | factor-papers §5(실무 강합의·동료심사 약, regime 게이트로만) | ★CM 무료 미포함 확정. Glassnode/CQ/CM Pro 유료. |
| coin_perp_oi | Track D | Binance 30d 제한. Coinglass/Glassnode 유료. |
| coin_liquidation | Track D Tail-MR(Daniel-Moskowitz crash·2022 LUNA/FTX) | Coinglass 유료. event-study 가치. |
| coin_miner_flow | gemini(halving 공급) | Glassnode 유료. |
| coin_whale_flow | gemini | mempool 부분·PIT 미구축. |

### C. ★진짜 갭 (측정/grounding 가능한데 현-프레임 미적용 — 다음 우선순위)
| candidate/신호 | 논문 ground | 갭·다음 액션 |
|---|---|---|
| **btc_dominance** | ★ledger reason **공란**·미측정·미grounding | 진짜 미탐구. BTC.D = BTC mcap/total. alt-season regime(breadth와 중복?) 측정 필요. total mcap 데이터 확보 선결. |
| **★USDT 스테이블코인 거래소 netflow** | **Chi-Chu-Hao 2024(동료심사 robust, 수익+·변동성−), 우선순위 1순위** | 우리 미측정. 무료 일봉 API 없음(Dune SQL 자가구축=라벨caveat / intraday=유료). ★최우선 robust 신호인데 데이터 경로만 막힘. |
| **investor attention** | Liu-Tsyvinski 2021 RFS(attention→수익 robust) | `collect_pytrends.py` 보유. 미측정(6단계 미적용). external_bonus와 분리 측정 의무. |
| **IVOL(idiosyncratic vol)** | J Banking&Finance/JFE(crypto IVOL 양(+), 주식과 반대, mixed) | 미측정. 시장모델 잔차 vol→fwd return. |
| **소형 롱테일 size sort** | LTW 2022 JF size factor | 대형 20종 universe 밖. survivorship-free 확장 시(thin·상폐 caveat 강). |

## 5. 다음 세션 우선순위 (ROI순, 전부 자율 — go-live 제외)
1. **reserve→vol S6 15축 audit**(독립 subagent raw 재현) → candidate→채택 게이트 통과 확인. + cross-measurement(가능하면 무료 대체 provider) + mechanism 매개(order-book proxy=volume).
2. **btc_dominance 측정**(진짜 미탐구 candidate, reason 공란): total crypto mcap 확보 → BTC.D → alt-season/regime, breadth와 중복성.
3. **investor attention**(pytrends 보유, 자율 가능): attention z → fwd return/vol, external 직교, 6단계.
4. **기존 약신호 Bonferroni→FDR 재판정**(real_rate 약세·basis 약장 부활 스크리닝, .p2 result.json 재계산).
5. 데이터 게이트(SOPR/USDT netflow/청산): 유료 구독 OR Dune 자가구축 결정 = 사용자 게이트.

## 7. ★방법론 전체 감사 자문 (2026-06-03, gemini+claude 만장일치) — 프로세스 개선 의무
> 사용자 "regime/cross/horizon 적용+상관 정리해 자문, 잘못 적용 없나". briefing=`.consult-methodology-audit.md`. 결론: 프레임 건전(상위 10%)하나 오적용 다수.
### 잘못 적용한 것 (정정 의무)
1. **epoch pooling 유의 = 심슨의 역설** → btc_dominance candidate→**rejected_provisional 격하 완료**. 판별테스트 미실행이 근본: 다음부터 "전표본 유의·per-epoch 비유의" 패턴 = **epoch 고정효과(within-demean) slope 생존 + RE 메타분석(이질성 I²) + power 계산(per-epoch miss가 참효과 하 예상범위인가)** 3종 필수. reserve-수익·m2도 동일 미검.
2. **상관 클러스터 multiple-counting**: mvrv/fgi/mom/volprice 0.5~0.8 = 단일 "강세-추세-센티" latent. → cross-indicator 통제 시 **블록(PC1 또는 대표 mom30 1개)으로**, 개별 4개 순차통제 금지(다중공선성 SE 부풀림). "20지표" 독립검정 수 과장 금지. (reserve는 클러스터와 ≈0이라 무관·견고.)
3. **세션 family-wise MC 미보정**: per-harness FDR만으론 winner 선택편의 미보정. → **Deflated Sharpe Ratio(Bailey-LdP) + online-FDR(LORD++/SAFFRON) alpha-wealth를 세션 스코프로**(시스템에 이미 보유, 이 세션 미적용=불일치). 사전등록(격자 분모 고정)이 garden-of-forking-paths 차단.
4. **regime 180일 이진 = 거침/가격내생**: hysteresis band(±x%) 권고. 가격파생 클러스터 평가 시 regime↔신호 기계얽힘(reserve 등 가격직교엔 무해). 누락축=**stablecoin 시총증가율(온체인 달러유동성)·aggregate funding(시스템 레버리지)·BTC-SPX rolling corr regime**(VIX 정적통제는 시변beta와 불일치).
5. **★reserve PIT/vintage look-ahead = 최대구멍**(claude): provider가 거래소 주소라벨 **소급재배정**→백테스트가 오늘 라벨 사용=look-ahead. 우리 bitemporal/PIT 원칙을 이 세션 reserve에 미적용=불일치. → claude는 reserve도 "candidate 아닌 provisional 보류" 권고. 승격 hard조건=(a)PIT-정합 reserve(vintage 보존) (b)2nd provider cross-measurement (c)DSR.
6. **survivorship 방향규칙**(claude 정밀화): 편의방향=발견방향(long-only 프리미엄)이면 무효 / 발견이 불리한 편의 뚫으면 부호 강화. **IVOL 음(−0.067)=편의가 양으로 미는데 음=참 slope 더 음, 부호 견고**. magnitude는 PIT 유니버스(사망코인 포함) 전까지 불신.
### 옳게 한 것 (자문 인정)
vol신호 무분할/HAR 연속통제 ✅ / "regime으로 죽은 신호 부활 금지" ✅(최강 anti-mining) / FDR>Bonferroni ✅ / 주봉 비중첩 동반 ✅ / incremental rank-IC=게이트 ✅ / 독립 audit이 over-claim 2건 포착 ✅(SOP 작동).
### divergence
BTC/ETH 내부 cross 강등: gemini="too harsh, asset-specific로 해석" / claude="강등보다 사후합리화(unfalsifiable) 위험 — 메커니즘 사전등록 안 했으면 motivated reasoning". → 메커니즘 사전등록 의무화로 절충.

## 6. 불변 제약
- ⛔ go-live 배선·실 사이징·weight 변경 = 사람 게이트. push 금지. risk_gate 상수 무수정(env only). 엔진/부품(calculate_buy_score SACRED) 호출만.
- 6단계 SOP 의무(S1논문→S2 4게이트→S3 gemini+claude 병렬→S4 falsifier 직접검증→S5 역공격수렴→S6 15축 audit). FDR(Bonferroni 아님). NW HAC. 자문 언급 지표 누락 금지.
- crypto "전기간 불일치"는 rejected_permanent 사유 아님(instability=norm). S3 자문 없이 rejected_permanent 금지.
