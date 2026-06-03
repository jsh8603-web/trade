---
name: handoff-coin-adopted-horizon
description: 코인 지표 6단계 검토 세션 인계 — xs_momentum 격하·6단계 SOP 고정·호라이즌 확장·adopted 재검토·빠진축 식별
date: 2026-06-03
tags: [handoff, crypto, indicator-review, adopted, horizon, missing-axis]
---

# 핸드오프 — 코인 지표 6단계 검토 (2026-06-03, btn-Inv)

> 진입: [plan-coin-indicator-review.md](./plan-coin-indicator-review.md) §3b 재검토 매트릭스 → [progress-coin-indicator-review.md](./progress-coin-indicator-review.md) Working Notes
> 측정 SSOT: [regime-conditional-measurement-framework.md](./study-research/_wire/regime-conditional-measurement-framework.md)
> ⛔ go-live=사람 게이트·push 금지·자율주행 ON·Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`·`PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 의무

## 0. 세션 핵심 (6단계 SOP 고정 + 3대 검토)

사용자 지시 흐름: ①xs_momentum 6단계 검토 → ②"15축 audit 포함해 **6단계 SOP**로 고정"(S6 신설) → ③"호라이즌 길게(15일/한달) 보면?" → ④"adopted(mvrv·stablecoin·fgi·halving·etf·funding) 재검토" → ⑤"drop한 것 다 regime×horizon×cross로 다시 계획" → ⑥"속도보다 퀄리티" → ⑦"horizon×cross×regime 다 봐도 무신호? 논문 ref로 측정 방법/빠진 축 검토".

## 1. 6단계 SOP 고정 (★규칙)
S1 논문 ground → S2 실측(4게이트 G1 ex-ante regime·G2 Bonferroni·G3 walk-forward·G4 Newey-West) → S3 외부검토(gemini+claude 병렬) → S4 자문 falsification 다른 데이터 재검증 → S5 역공격 수렴 → **S6 15축 audit 독립 subagent raw 재현(hard-fail 0 후 status 확정)**.
박제: 프로젝트 `CLAUDE.md §코인 6단계 SOP` + `plan-coin-indicator-review.md §1` + `regime-conditional-measurement-framework.md §4b` + `progress §6단계` + 본 handoff.

## 2. 완결 검토 (verdict 확정)

### 2a. coin_xs_momentum → rejected_provisional (S1~S6 완주, audit 통과)
- **독립 알파 아님 = 크립토 size 팩터 베타**(Liu-Tsyvinski-Wu 2022 JF). 다팩터 직교화(`.p2-xs-factor.py`) winner alpha t: MKT단독 +3.69 → MKT+SMB **+0.75** → +VOLF +0.44 붕괴(SMB=거래량 size).
- 생존편의 hazard 20%/yr → Sharpe 1.40→1.11(BTC 1.13 하회). Binance 8년 OOS(`.p2-xs-binance-oos.py`) 진짜OOS long 1.41 robust=한국 기생 기각이나 size라 당연, 2022크래시 결합 -0.72·momentum-crash반등 -1.04(Daniel-Moskowitz, in-sample 타이밍 fragile). co-drawdown(`.p2-xs-codrawdown.py`) carrier 최악5%일 XS 음수 90%+(satellite 분산효과 소멸). dollar-vol weight 1.34→1.21.
- claude 졸업 3관문(다팩터 t>3·survivorship 후 유의·co-draw 낮음) **전실패** → BTC momentum carrier 단일 유지. 부활=size 팩터 명시 sleeve 채택 OR survivorship-free+momentum-crash 견디는 타이밍.
- 통계 hedge(small-n): 결합 Sharpe 1.86 95%CI [-0.10,3.81]·non-overlap thin t=1.42(<2). S6 audit(agentId 완료) verdict (a)정당·재현0실패.

### 2b. adopted 6개 재검토 (자문 gemini+claude 수렴 + S6 audit, weight 변경=go-live 게이트)
- **MVRV(0.55)**: full-sample 고MVRV>2.4 후 fwd30 +22.9%는 **momentum 공선성+강세편중** 합작(단변량). 직교화 순효과 **-0.10**(약 mean-revert, ★원 -0.13은 realcap_g 순환참조 정정). decile +0.64(D9 67% pre-2017 편중). partial CI 0포함=FGI 매개. → **0.55 과대, risk/regime gate 용도변경 권고**. `.p2-mvrv-s4.py`.
- **stablecoin(0.2)**: Granger 유의는 **in-sample 환상**(rank-IC NW p=0.38 비유의), exogenous 분해 시 소멸(내생/reactive), redemption 비대칭(강세편향), OOS hit 53.6% eff_n 보정 비유의. → throttle 강등. `.p2-stablecoin-s4.py`.
- **funding(0.15)**: cascade 가설 정반대 재확인 → **방향 제거(0), risk gate+carry 용도변경**. **ETF(0.05)**: CI 0포함 → 제거/watchlist. **반감기(0.1)**: N=4 → label만. **FGI(0.1)**: MVRV와 병합(센티먼트 단일).
- ★claude 핵심: adopted 6개 = "독립 6베팅 아니라 **강세-추세 1팩터 6번 측정**"(MVRV+FGI+funding 0.8 집중) → 직교 3팩터 재발행 권고(가격추세 BTC TSMOM + 외생유동성 stablecoin잔차+거시 + tail/regime overlay).

### 2c. 거시 regime×horizon×cross grid (`.p2-macro-grid.py`)
- 144셀 Bonferroni 생존: M2 긴축 BTC fwd6/12M raw-p 2셀 BUT **NW HAC 보정 시 0셀**(audit 정정)·ETH cross 불일치. real_rate 약세장 BTC/ETH 동부호(방향 일관)이나 under-powered. → **거시=point forecast 알파 아님, risk overlay/prior만**.

## 3. ★빠진 축 (사용자 ⑦ 지적 — "무신호=측정 한계") — 미완 핵심
우리 측정="가격/거시·rank-IC 선형·일봉↑·수익예측" 한정. 논문 robust 미측정:
1. **데이터 축**: USDT 거래소 net inflow(Chi-Chu-Hao 2024 arxiv 2411.06327, ✅동료심사 robust=수익+/변동성- 예측)·SOPR·청산 = 유료 게이트. ★최우선.
2. **측정 대상 축**: 변동성 예측(`.p2-vol-forecast.py` 측정=우리 지표 약, funding 약세장 fvol30 -0.149.만, 자기 rv20만 +0.54 GARCH).
3. **intraday 축**: 최소 일봉. 논문 1-6h서 robust(funding/netflow), 일봉 전이 시 약화. Binance 1h fetch 가능.
4. **함수형 축**: rank-IC 선형만. 비선형/임계/조합(MVRV high+SOPR↓+inflow↑ ML) 미.
5. **carry 축**: funding directional만. carry 수익(시장중립) 미(무레버리지 실행 제약).

## 4. 진행 중 / 다음 (자율)
- **★subagent a3c789bc 완료** (`study-research/crypto/raw/measurement-methodology-papers.md` SSOT): rank-IC = 수익×선형×일봉×횡단면 4중 제약 → robust 신호 구조적 누락, momentum 생존도 측정 편향. ①**Chi-Chu-Hao = intraday 1-6h 전용**, 일봉 기각=horizon 미스매치 false-neg(★USDT netflow 일봉으로 죽이면 안 됨) ②~~SOPR/realized-cap/LTH-STH = CM Community 무료~~ ★**2026-06-03 probe 정정: FALSE**. CM Community btc.csv 32컬럼에 SOPR·CapRealUSD·SplyAct 전부 부재, anonymous API도 403 = 유료게이트(Glassnode/CQ/CM Pro). ★대체: CM Community 무료=**거래소 flow(FlowInEx/FlowOutEx)+reserve(SplyExNtv) 2011~** → exchange_reserve→vol 6단계 candidate 완료(.p2-exchflow, handoff-exchflow-20260603.md) ③**Bonferroni가 false-neg 증폭** → crypto 약신호 **FDR(Benjamini-Hochberg)** 전환 power 보존 ④false-neg top3=USDT netflow(intraday)·변동성 예측·funding intraday crowding/regime 부호반전.
- **빠진축 메우기 우선순위(자율 측정 가능)**: ①변동성 예측축(최ROI, .p2-vol-forecast.py 확장=지표→forward RV, flow 포함) ②regime 조건부 Sharpe·지표 조합 interaction·funding-z 게이트 ③event-study(반감기/ETF/규제 전후 누적수익) ④~~SOPR/realized-cap(CM무료)~~ → **거래소 reserve→vol(CM 무료 SplyExNtv) 6단계 완료 2026-06-03**, SOPR/realcap은 유료게이트 ⑤기존 약신호 Bonferroni→FDR 재판정.
- **데이터 게이트(유료 가능성, fetch 전 가용범위 검증 의무 empirical-claim §1.1-ext)**: USDT exchange inflow intraday·funding intraday. "free chart view ≠ free API 시계열" 주의.
- 자율 측정 가능: 비선형/임계 조합·intraday(Binance 1h)·carry 묶음.
- 데이터 게이트: USDT netflow(무료 소스 subagent 조사중)·SOPR·청산.
- drop 매트릭스(plan §3b) 잔여 우선순위: carry+vol regime×horizon → breadth 저빈도 → dxy/active_addr.
- **미해결 결정**: adopted 비중 재배분 = 사용자 Q1 "권고만 박제, weight=go-live 게이트"(권고 ledger 박제 완료, 실제 weight 미변경). Q2 다음 우선순위 미답(carry/거시studyroom/직교재발행/나머지drop 중).

## 5. 산물
- harness: `.p2-{xs-netcost,xs-diagnose,xs-binance,xs-binance-oos,xs-factor,xs-survivorship,xs-codrawdown,mvrv-s4,stablecoin-s4,macro-grid,horizon,vol-forecast}.py` + 각 `-result.json`
- cycle2 재실행: `study-research/crypto/scripts/h{1,2,3,4,5}_*.py` → `validation-h*.md` 갱신
- 자문 raw: `.consult-{xs,adopted}-R1-{gemini,claude}.txt` + 브리핑 `.consult-{xs,adopted}-R1-briefing.md`
- ledger: `study-research/_wire/indicator-ledger.md` crypto(adopted 6/candidate 16/rejected_provisional 7)
- promo-log ERROR: harness 2결함(grid NW미적용·MVRV realcap 순환참조)

## 6. ★지표별 상세 — 확실히 본 것 / 빠진 축(논문) / 측정 설계 / confidence
> 사용자 요구(2026-06-03): "지표별 확실히 본 것 어디까지·빠진 축은 논문에 있는 뭐·어떻게 측정하고 싶은지·확실vs미심쩍 자세히, 다음 세션 동등 수준". confidence = ✅확실 / ◐중간 / ❓미심쩍(측정 한계) / ▢미측정.

### ✅ 확실 (결론 신뢰 높음, 재측정 불요)
- **BTC TSMOM (momentum)** ✅ candidate→adopted후보: **본것**=6단계 완주, net Sharpe 1.42(거래비용후), 30-60일 sweet spot(.p2-horizon.py lb60=1.11), 2022 OOS 방어(-37% vs BH -63%), Binance 8년 robust. **빠진축**=거의 없음(intraday는 capacity 이슈). **측정**=donch20/tr30-60 long-flat. **confidence**=확실(MOP2012 TSMOM + Liu-Tsyvinski 2021 RFS 주~월 horizon 정합). go-live 배선만 남음(사람 게이트).
- **xs_momentum** ✅ rejected_provisional: **본것**=6단계+S6 audit, 다팩터 직교 alpha t 3.69→0.75=크립토 size 팩터(LTW 2022 JF) 베타. survivorship/co-drawdown/momentum-crash 다 봄. **빠진축**=소형 롱테일 size sort(우리 대형 20종만), survivorship-free universe(상폐 PIT). **측정**=size 팩터 명시 sleeve 채택 시 부활. **confidence**=독립 알파 아님 확실.
- **funding directional** ✅ reject: **본것**=3각도(directional/역추세gate/crowding risk-gate) 일봉 전부 무알파 + 자문 + 거시 grid. **빠진축**=★intraday 1-6h crowding(데이터 게이트). **측정**=intraday funding-z 극단→unwind(유료). **confidence**=일봉 확실 reject / intraday 미측정.
- **MVRV 0.55 과대** ✅: **본것**=S4 직교화(순효과 -0.10, momentum 공선성+강세편중)+S6 audit. **빠진축**=SOPR 보완 cycle 진동(★CM 유료게이트 정정). **측정**=regime z-gate(방향 아닌 down-sizing). **confidence**=0.55 과대 확실 / 약한 valuation gate 잔존은 ◐.

### ◐ 중간 (일부 신호 잔존, 추가 측정 가치)
- **stablecoin 0.2** ◐: **본것**=S4 in-sample 환상(rank-IC NW p0.38, exogenous 분해 소멸, redemption 비대칭) BUT OOS hit 53.6%·partial +0.06 미약 잔존. **빠진축**=PIT 재스탬프(mint 관측시점), exchange netflow 결합, VECM 인과방향. **측정**=Dune 자가구축 USDT netflow + redemption 대칭 재확인. **confidence**=0.2 과대·throttle 강등 확실 / 완전 0은 ❓.
- **kimchi** ◐ candidate(throttle): **본것**=level→Upbit fwd10d -0.211, breadth와 독립, net-cost throttle 개선. **빠진축**=비선형 동학(Economic Modelling S0264999324000828). **측정**=비선형 임계(spline). **confidence**=throttle 역할 확실.

### ❓ 미심쩍 (측정 한계로 판정 불확정 — 빠진 축이 결론 좌우)
- **거시 M2/real_rate** ❓ candidate: **본것**=regime×horizon×cross grid(.p2-macro-grid.py), M2 NW보정후 0셀·cross불일치, real_rate 약세장 BTC/ETH 동부호이나 셀별 under-powered. **빠진축**=★6-24M horizon이 본질적 under-powered(8년=8~16 독립관측, claude "약함≠부재"). **측정**=장기는 point forecast 불가→prior/risk overlay만. 일별 real rate + 장기표본. **confidence**=단기 무 확실 / 장기 검정력 부족이라 ❓(있는데 못 보는지 진짜 없는지 불확정).
- **변동성 예측축** ❓ ★빠진 측정 대상: **본것**=.p2-vol-forecast.py 우리 지표(mvrv/fgi/funding)→forward RV 약(funding 약세 -0.149.만, 자기 rv20만 +0.54 GARCH). **빠진축**=★flow→RV(Chi-Chu-Hao netflow가 vol -예측 robust). **측정**=★**거래소 reserve→fwd RV 측정 완료 2026-06-03**(+0.35, ⊥HAR/GARCH/VIX 잔존=candidate). SOPR/realcap은 유료게이트. **confidence**=거래소 reserve→vol robust 확실(candidate) / SOPR 미측정.
- **realized_vol** ❓ rejected_prov: **본것**=directional rank-IC cross-asset 부호 불일치 reject. **빠진축**=vol-managed sizing(Moreira-Muir 2017 JF). **측정**=position=base/realized_vol ablation+net-cost(directional 아닌 sizing layer). **confidence**=directional 확실 reject / sizing layer 미측정 ❓.

### ▢ 미측정 (데이터 게이트 vs 자율 가능 구분)
- **SOPR/realized-cap/LTH-STH** ▢ ★**유료게이트 확정(2026-06-03 정정)**: ~~CM Community 무료~~ FALSE — community btc.csv 32col 미포함·API 403. Glassnode/CQ/CM Pro 유료만. **빠진축**=cost-basis regime band. **측정**=유료 구독 후. **confidence**=미측정(데이터게이트).
- **거래소 reserve→vol** ◐→candidate (2026-06-03 신규, ★CM Community 무료 SplyExNtv): 잔고변화→forward realized vol +0.35, ⊥HAR/GARCH +0.18·⊥VIX/MVRV/funding 잔존·주봉 reserve 선행·15년. one-sided vol-throttle candidate. caveat=ETF era raw 약화(VIX통제 후 회복)·CM 라벨커버리지·S6 audit 잔여. **confidence**=vol예측 robust 확실 / 수익 directional은 효율화 reject. 상세=handoff-exchflow-20260603.md.
- **USDT exchange netflow** ▢ 데이터 게이트: Chi-Chu-Hao robust(intraday 1-6h) BUT 일봉 견고 무료 API 없음(Dune SQL 자가구축=거래소 라벨링 caveat / intraday=유료). **confidence**=논문 robust지만 우리 측정 경로 제한(★일봉 rank-IC로 죽이면 false-neg).
- **perp OI/liquidation/exchange reserve/miner/whale** ▢ 유료 미탐색: Coinglass/Glassnode. 청산캐스케이드(Track D Tail-MR)는 2022 LUNA/FTX event-study 가치.

### ★ 측정 방법 자체의 빠진 축 (방법론 = 다음 세션 최우선)
1. **Bonferroni→FDR(Benjamini-Hochberg)**: Bonferroni가 약신호 power 죽임(false-neg 증폭). 기존 raw-p<0.05였다 Bonferroni 탈락한 신호(real_rate 약세장·breadth·basis 약장) FDR 재판정 = 부활 가능성.
2. **event-study**: 반감기/ETF승인/규제 전후 누적수익(CAR). rank-IC가 못 보는 이벤트 신호.
3. **regime 조건부 Sharpe + 지표 조합 interaction**: 선형 단일 rank-IC 아닌 비선형/조합(MVRV high+SOPR↓+inflow↑ = 리스크 게이트).
4. **intraday horizon(Binance 1h fetch)**: funding/netflow 진짜 robust 영역(일봉 전이 시 소멸 정상).

### 다음 세션 실행 순서 (ROI순, 전부 자율)
1. **변동성 예측 + SOPR**(CM 무료 fetch → forward RV·regime gate) — 최ROI, 데이터 자율.
2. **Bonferroni→FDR 재판정**(기존 .p2 result.json 재계산) — 빠른, 부활 스크리닝.
3. **event-study**(반감기/ETF, BTC daily 보유).
4. **regime 조건부 Sharpe/조합 interaction**.
5. **intraday**(Binance 1h fetch, funding/momentum) — 데이터 fetch 필요.
6. carry 묶음·drop 매트릭스 잔여(plan §3b).
※ 각 6단계(S1~S6) 준수, FDR 적용, NW HAC 의무(grid 결함 재발 방지), 자문 falsifier 직접 검증.

### ★논문 추가 축 (crypto-factor-papers.md 재대조 — §6 본문 누락분 보완, 2026-06-03 사용자 "다 기재했나" 점검)
- **investor attention** ❓미측정 [논문 robust]: Liu-Tsyvinski 2021 RFS(✅저자 verified) "investor attention forecasts returns". Google Trends 검색량/소셜 sentiment. `study-research/crypto/scripts/collect_pytrends.py` 보유. ★external_bonus(뉴스/소셜/X)와 겹칠 수 있어 분리 측정 의무. **측정**=attention z-score→fwd return rank-IC + external 직교. confidence=논문 robust지만 우리 미측정.
- **IVOL (idiosyncratic volatility)** ❓미측정 [mixed]: factor-papers §3, J Banking&Finance/JFE — crypto IVOL이 기대수익과 **양(+)**(주식 anomaly와 반대) 보고하는 논문 존재(★미확인 다수, mixed). **측정**=시장모델 잔차 vol→fwd return. confidence=부호 불확정(주식과 반대 가능), 검토 가치 중.
- **value/NVT/network value** ◐cycle2만 [LTW C-4]: LTW 2022 JF 후속 C-4 모델 value 팩터=price-to-active-address(온체인 의존). cycle2 `h7_network_value.py`/`h8_tx_utility.py` 측정했으나 6단계(S3 자문·S4) 미적용. **측정**=NVT/network value→fwd return 6단계. confidence=cycle2 12축만, 재검토 필요.
- **소형 롱테일 size sort** ▢ [LTW size]: LTW 2022 JF size factor=소형 코인 프리미엄. 우리 대형 20종 universe 밖(xs는 대형 내 측정→size 베타로 흡수 확인). **측정**=소형 롱테일 포함 cross-sectional size sort(★실거래성·유동성·survivorship caveat 강). confidence=universe 확장 시만, 실행 가치 낮음(thin·상폐).
- **low-vol anomaly** ✅채택말것: FRL 2021 crypto서 유의 프리미엄 부재(반박). vol을 directional alpha로 쓰지 말 것(우리 vol β:=0 lock 정합) — 이미 결론, 재검토 불요.
- **momentum-crash tail** ◐: Springer FMPM 2025(★미확인) momentum severe crash 노출. xs에서 2022 반등 -1.04로 확인됨(Daniel-Moskowitz). BTC carrier에도 적용 가치(반등기 down-gate).
