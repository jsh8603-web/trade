---
name: progress-coin-indicator-review
description: 코인 지표 6단계 검토 진행. plan-coin-indicator-review.md 추적.
type: project
date: 2026-06-02
tags: [progress, crypto, indicator-review]
---

# Progress — 코인 지표 6단계 검토

> plan = [plan-coin-indicator-review.md](./plan-coin-indicator-review.md). 6단계 = S1 논문ground / S2 실측가설(4게이트) / S3 외부검토(gemini+claude) / S4 다른데이터 재검증 / S5 역공격 수렴 / **S6 15축 audit 최종검증**.
> ⛔ go-live=사람 게이트. push 금지. Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`.

## §진입 스냅샷 (2026-06-02)
측정 함정 2종(full-sample 상쇄 기각 / single-episode 즉시채택)을 5단계로 차단. M2 거시유동성이 1회전 완결 사례. 측정 SSOT=regime-conditional-measurement-framework.md(4게이트). ledger=indicator-ledger.md crypto.

## 지표별 5단계 진행

| 지표 | S1 ground | S2 실측 | S3 외부검토 | S4 재검증 | S5 수렴 | S6 audit | status |
|---|---|---|---|---|---|---|---|
| **coin_xs_momentum** | ✅ Liu-Tsyvinski-Wu | ✅ net Sharpe long 1.40/결합 1.86, 보존74% | ✅ gemini(순환매 의심)+claude(size베타·졸업3관문) | ✅ 다팩터 직교 t3.69→0.75·hazard20%→1.11·Binance8년OOS·co-draw 꼬리90%·dollar-vol 1.21 | ✅ **size 팩터 베타·졸업3관문 전실패** | ✅ 15축 (a)정당·재현0실패·CI[-0.10,3.81] 보강 | **rejected_provisional** |
| **M2 거시유동성** | ✅ regime-deps-papers | ✅ 긴축 −0.54 4게이트 | ✅ gemini+claude (b)candidate | ✅ cross-asset/episode/horizon/NASDAQ | ✅ **3중수렴+audit**: single-episode artifact | ✅ 15축(b)artifact CI[−0.91,−0.001] | **candidate**(throttle만, sizing금지) |
| real_rate | ✅ | ✅ BTC하락장 −0.48 | (M2와 동반) | △ 부분(walk-forward 미완) | ⏳ | candidate |
| net_liquidity(BS−TGA−RRP) | ✅ | ✅ nl_yoy 무·nl_3m긴축 −0.38 | ✅ gemini낙관/claude엄격 | ✅ within-period 무·구간부호반전·partial(nl\|m2)+0.11 | ✅ **claude 수렴**: M2와 동일 single-episode artifact | **rejected_provisional**(M2 대비 승격 없음, throttle gate 조건부) |
| funding directional | ✅ BIS carry | ✅ 전 regime 무 | ✅ (직전 R) | ✅ regime split 무 | ✅ | rejected_provisional |
| funding crowding gate | ✅ P9 BIS | ❌ 미측정(극단 de-risk 재정식화) | - | - | - | **큐** |
| basis | ✅ | ✅ 약장 −0.11 | - | △ Bonferroni 탈락 | ⏳ | rejected_provisional |
| realized_vol | ✅ | ✅ vol-sizing 차원 | - | ✅ regime 무 | ✅ | rejected_provisional |
| 온체인(SOPR/netflow/청산/miner/whale) | ✅ | ❌ 유료 데이터 게이트 | - | - | - | candidate(데이터 게이트) |
| active_addresses | ✅ | ✅ 무신호+metcalfe lookahead | - | - | ✅ | rejected_provisional |
| BTC momentum | ✅ TSMOM | ✅ net Sharpe 1.42 | ✅ (직전 R 수렴) | ✅ net-cost+OOS | ✅ | **adopted 후보**(go-live 게이트) |
| kimchi throttle | ✅ | ✅ risk-adj 개선 | ✅ | ✅ 독립성 확증 | ✅ | candidate(throttle) |
| breadth | ✅ | ✅ alt-BTC MR −0.13 | ✅ | ✅ net-cost 탈락 | ✅ | candidate(실행불가) |
| **coin_exchange_reserve→vol** | ✅ Chi-Chu-Hao flow→vol | ✅ +0.35 15년 FDR | ✅ gemini+claude 2R 수렴(2-신호분리) | ✅ ⊥HAR/GARCH/VIX/MVRV/funding·주봉·역인과 전부 PASS | ✅ 자문 수렴 | ⏳ **S6 잔여** | **candidate**(vol-throttle) |
| coin_exchange_netflow(일별) | ✅ | ✅ 수익 ≈0 | - | - | - | - | rejected_provisional |
| coin_volprice_corr | ✅ | ✅ | - | ✅ 새프레임 ⊥mom 흡수 | ✅ | - | rejected_provisional(격하) |

## ★M2 완결 사례 상세 (5단계 1회전, 다음 지표 템플릿)
- **S5 수렴 verdict**: gemini((b)candidate·shadow) ∩ claude((b)candidate·throttle·sizing금지·BL격리) ∩ audit 15축((b)single-episode artifact·(c)fishing 잔여·CI[−0.91,−0.001]·연도내IC 2022 1개뿐) ∩ 내 데이터(2021-23 제외 −0.16 무·ETH −0.13·NDX/ARKK 공유) = **한 점 수렴**.
- **메커니즘**(claude): M2=과열 noisy proxy, 진짜 채널=실질금리 할인율. 주류 M2-BTC 양(+)인데 −0.54=반전꼬리. 2025Q4 OOS 붕괴(M2+12%/BTC−12%).
- **졸업 게이트**(candidate→adopted-throttle): ①50년 equity cross-asset 다수 에피소드 생존 ②2022-drop placebo 견고 ③net-liquidity conditioner 비교 ④BL view 격리 유지.
- **audit 정정 반영**: E(recheck json verdict 격하 완료) / K(다중검정 denominator = regime×factor×horizon 전체 격자로 재계산 필요, α/12 과소).

## 다음 (2026-06-03 새-프레임 sweep 후 — plan §3b ⏳ 동기화)
1. **reserve→vol S6 15축 audit**(독립 subagent raw 재현) → candidate→채택 게이트. + cross-measurement(타 provider)·mechanism(order-book proxy=volume).
2. **btc_dominance**(★ledger reason 공란=완전 미탐구): total crypto mcap 확보 → BTC.D alt-season/regime.
3. **investor attention**(collect_pytrends.py 보유): attention z → fwd return/vol, external 직교.
4. **Bonferroni→FDR 재판정**(기존 .p2 result.json 재계산, real_rate 약세·basis 부활 스크리닝).
5. **데이터 게이트(사용자 결정)**: USDT netflow(Chi-Chu-Hao 1순위)·SOPR·청산 = 유료/Dune.
- ⛔ 거시·온체인 신호 = throttle overlay만(현물·무레버리지). go-live=사람게이트. push 금지.
- ★완료(새-프레임): 거래소 reserve/flow 6단계(S6 잔여)·폐기 5종 재검·candidate 재측정(volprice 격하·kimchi/m2 노트). = handoff-exchflow-20260603.md.

## Working Notes

> ★인계(2026-06-03 clear 대비): [handoff-coin-killaudit-20260603.md](./handoff-coin-killaudit-20260603.md) — 자기완결. 다음 세션=측정부터 시작(§0 Python경로)→§1 생/사 판정표 재현→§7 자문 정정 재측정(1순위 ②Upbit⊥kimchi·③addr 4결함=판정 뒤집힐 후보). corrected frame=§2(C1~C6). 자문 박제=§3. audit 2/6+pending=§4. 보조문서 .frame-change-corrected-20260603.md.

> [ckpt-202606040230:btn-Inv] ★배선 adopted 재측정 + vol-throttle 후보 정리완료 (사용자 "배선된 것도 현프레임으로·다음자율")
> **(1) 결과**: ▶**배선 adopted 현프레임(.p2-adopted-reframe.py)**: mvrv(0.55) ⊥잔여클러스터 p0.085 marginal·fgi(0.1)/funding(0.15)/stablecoin(0.2) 수익 directional 전부 0 = **배선 weight들이 방향알파로 정당화 안 됨, risk/regime gate 용도만**(weight 과대 재확인, ⛔변경=go-live). ▶**vol-throttle 후보 정리완료**: epoch-FE within이 진짜 판별자 — **reserve만 within +0.31 생존=단독 carrier 확정** / stablecoin→vol(.p2-stablecoin-vol.py) ⊥reserve 독립생존 +0.17이나 **within p0.70 NULL=between-epoch 인공물** / hashrate→vol reserve에 흡수(⊥reserve p0.10) / volofvol E3 사망. ▶real_rate 일별 null(p0.56)=저빈도 월별 신호 확정. ▶hashrate 신규후보 철회(reserve 중복).
> **(2) 다음**: ①PIT path2(raw chain 직접재구성) 타당성 — 사용자가 자문 가져오는 중(라벨 vintage=first-seen 날짜 확보 가능여부가 핵심 블로커, 없으면 세션 띄워도 오염 재생산). 녹색이면 psmux Opus 1M 세션. ②forward-logging path1(CM Community as-of 적재)은 사용자 path2 우선이라 보류.
> **(3) 동기화**: ledger 헤더(adopted 재측정+vol-throttle 단독carrier 결론)+mvrv(⊥클러스터 marginal)+coin_real_rate(일별 null)+coin_miner_flow(hashrate reserve흡수)+stablecoin_total_supply(vol축 between-epoch 인공물) 갱신. 산물=.p2-{adopted-reframe,stablecoin-vol}.py. long-mode ON.

> [ckpt-202606040130:btn-Inv] ★미탐구 무료 온체인 4종 + 미배선 거시 현프레임 재측정 + PIT 검토결과 반영
> **(1) 마지막 결정**: 사용자 "유료 skip·PIT는 내가 자문·미탐구 무료 탐구·미배선 거시 현프레임 재측정". ▶**무료 온체인 4종(.p2-freeonchain.py)**: CM Community 32컬럼 중 미측정분(HashRate 컬럼15·AdrBalCnt·FeeTotNtv·TxCnt — 직전 miner "미수집"은 오류, 무상 존재). ★해시리본(miner capitulation 바닥신호 실무명성)→수익 within p0.94 **사망**, holder성장/tx/nvt count proxy 사망, fee 약신호(within p0.011 but 세션MC 탈락). ★★유일 발견=**hashrate momentum→forward vol** raw +0.246·⊥HAR(full) +0.131 p0.001·**E3 +0.106 p0.016**(volofvol과 달리 최근 생존)=reserve류 vol-throttle 신규후보(잔여=⊥reserve 중복검정+S3~S6). ▶**미배선 거시(.p2-macro-reframe.py 월봉 n107)**: real_d3m→fwd3 **−0.401 p<0.001·⊥mom3 −0.403·긴축완화 부호일관**=미배선 거시 최강(candidate 강화), m2 vol축만 +0.24 regime반전·dxy −0.19 약일관·netliq 사망. ★월별=epoch-FE under-power 원천. ▶**PIT(사용자 자문)**: 무료 historical 많아도 무료 PIT 완제품 없음(라벨 소급재배정), 길1=오늘부터 무료피드(CM Community API·CoinGecko proof-of-reserves) as-of 적재→forward OOS만 가능, reserve provisional 유지.
> **(2) 다음 의도**: ①hashrate_mom→vol ⊥reserve 중복검정(둘 다 miner/공급계열) → 독립이면 vol-throttle 2번째 후보 ②reserve forward-OOS PIT 적재 파이프(길1, 무상 피드) ③real_rate 일별표본 재측정(월별 under-power 해소). go-live=사람게이트, push금지.
> **(3) 동기화**: ledger 헤더(6/12/15)+coin_miner_flow(HashRate 측정·hashrate_mom→vol candidate)+coin_real_rate(강화)+coin_exchange_reserve(PIT 길1 경로)+신규 3행(coin_holder_growth/coin_fees/coin_tx_nvt rejected_provisional). 산물=.p2-{freeonchain,macro-reframe}.py. long-mode ON.

> [ckpt-202606040030:btn-Inv] ★감사관 검토 전체를 전 지표 적용 → verdict 델타 확정 + 잔여 doable 전부 실행 (감사관 원문 박제 .consult-methodology-audit-RESPONSE.md)
> **(1) 마지막 결정**: 사용자 흐름 "자문 박제대로 프레임 재적용해 전체 지표 확인 → 클로드 자문 그대로 박제+전체 적용 맞나 → 16개 지표 맞나 → 달라지는 거 있나 → 미적용 다 해". ▶정직 점검: 직전 "전체 지표 완료"는 over-claim(allframe 9개 일별만, 자문 원문 미저장, DSR/online-FDR/누락regime축/PIT 미적용)이었음 — 사용자 추궁으로 시정. ▶**감사프레임 전체 적용 .p2-allframe.py + .p2-allframe-audit.py + .p2-audit-remaining.py**: epoch-FE within/between + 클러스터 PC1 블록통제(설명분산68%) + VIX cross-asset + 세션 전역MC(Bonferroni m≈200) + 누락 regime축 4개(BTC-SPX corr·스테이블 유동성·trend·epoch) + online-FDR LORD++. ▶★**핵심 델타**: ①**btc_dominance rejected_provisional→candidate**(감사관 보류근거 2테스트 epoch-FE[within +0.14 RE I²=0%]·VIX[contemp corr +0.001=risk-off proxy 아님, ⊥VIX 강화]·+regime 4축 부호일관 = 3중 falsify) ②**세션 전역 Bonferroni(m200) 생존 단 2개**=reserve_within·volofvol_within(p<0.0001), 나머지 cross-indicator 증분 전부 세션-fishing 탈락=감사 Q5 적중 ③**reserve→vol** 코어 robust(4 regime 부호일관)지만 증분 marginal+**PIT가 binding**=candidate 상한 ④**volofvol 불일치 해소**=E3-only ⊥HAR +0.078 p0.49(초기era 구동)→rejected_provisional 확정 ⑤클러스터 묶음→30d수익 p0.15 무유의=mvrv/fgi/addr 개별 수익알파는 다중카운트 인공물. ▶데이터게이트 측정불가 4종 명시=DSR(백테스트단계)·ETH staked supply·cross-venue reserve·reserve PIT/2nd provider.
> **(2) 다음 의도**: ①reserve PIT-정합 재현+2nd provider(유일 binding 승격조건, 데이터게이트=사용자결정) ②btc_dominance full-universe dominance(top-7 proxy 한계) ③volofvol vol-managed overlay study(forecast 아닌 level scaling) ④거시 일별표본 재측정(월별 epoch-FE n<120 under-power). go-live=사람게이트, push금지.
> **(3) 동기화**: ledger crypto 헤더(6/12/12 카운트 정정+6-03c 감사프레임 노트)+btc_dominance(candidate)+coin_exchange_reserve(세션MC 분리+regime 4축)+coin_realized_vol(volofvol 불일치 해소)+coin_kimchi_premium(regime 부호일관+magnitude 집중) 갱신. 산물=.p2-{allframe,allframe-audit,audit-remaining,dominance-epochfe}.py + .consult-methodology-audit-RESPONSE.md. long-mode ON(compact 후 재활성).

> [ckpt-202606032030:btn-Inv] ★방법론 전체 감사 자문 + 미탐구 candidate sweep 완료 (상세=handoff-exchflow-20260603.md §7)
> **(1) 마지막 결정**: 사용자 "새프레임 안 본 거 다 봐 → regime/cross/horizon 적용+상관 정리해 자문(잘못 적용 없나)". ▶미탐구 측정: **btc_dominance**(BTC.D=BTC/Σtop7) BTC fwd수익 ⊥mom +0.155 but epoch 전부 비유의 / **investor attention** 수익 무재현(Liu-Tsyvinski 무, vol +0.22 약) / **IVOL** cross-sectional −0.067(주식형, crypto-양 논문 반대) / **지표 상관행렬**(mvrv↔fgi 0.80·mom클러스터 0.5~0.8, reserve 전부와 ≈0 독립). ▶★방법론 감사 자문 2모델 만장일치 격하: ①**epoch pooling 유의=심슨역설→btc_dominance candidate→rejected_provisional**(epoch-FE within/between+RE+power 판별 미실행) ②**상관 클러스터 multiple-counting**=블록통제 의무(개별 독립증거 4배 과장 금지) ③**세션 family-wise MC 미보정**=DSR+online-FDR 의무 ④regime 180일 거침/가격내생→hysteresis+누락축(유동성·미시구조·BTC-SPX corr) ⑤**reserve PIT/vintage look-ahead=최대구멍**(주소라벨 소급재배정, bitemporal 원칙 미적용)→claude는 reserve도 provisional 보류 권고, 승격조건 PIT+2nd provider+DSR ⑥survivorship: IVOL 음(−0.067)은 부호 오히려 강화(편의 불리 뚫음). ▶옳게 한 것(자문 인정): vol 무분할/HAR 연속통제·죽은신호 regime부활금지·FDR>Bonferroni·주봉비중첩·incremental IC 게이트·독립 audit over-claim 포착.
> **(2) 다음 의도**: ①reserve PIT-정합 재현+2nd provider cross-measurement(승격 hard조건) ②btc_dominance epoch-FE 판별테스트(부활 조건) ③클러스터 PCA 블록통제 재측정 ④세션 DSR/online-FDR 적용 ⑤데이터게이트(USDT netflow 등)=사용자결정. 전부 자율, go-live=사람게이트.
> **(3) 동기화**: ledger crypto 대량갱신(exchange_reserve candidate+PIT조건·exchange_netflow/volprice/attention/IVOL rejected_prov·btc_dominance candidate→rejected_prov·kimchi/m2 노트·헤더). 산물=.p2-{exchflow*,revisit,revisit2,dominance,corr-ivol}.py + .audit-exchflow.py + .consult-{exchflow-briefing,exchflow-R2,methodology-audit}.md + handoff-exchflow-20260603.md. push금지.

> [ckpt-202606031900:btn-Inv] ★거래소 flow/reserve 6단계 + 폐기 재검 + candidate 카탈로그 + SOPR false-prior 정정 (상세=handoff-exchflow-20260603.md)
> **(1) 마지막 결정**: ①**SOPR/realcap/LTH=CM무료 자율가능 주장 FALSE**(community 32col 부재·API 403=유료게이트, E97 latch 적발, promo-log ERROR). ②대체발견=CM Community 무료 거래소 flow(FlowInEx/OutEx)+reserve(SplyExNtv) 2011~. ③**reserve→vol = candidate(one-sided throttle)**: +0.35, ⊥HAR/GARCH +0.18·⊥VIX/MVRV/funding 잔존(cross-indicator 게이트 PASS)·주봉 비중첩 +0.32·역인과 주봉서 reserve 선행. reserve→수익=기각(ETF era −0.09 효율화+ETH불일치). netflow 일별=rejected_prov. ④자문 R1+R2 수렴(gemini+claude): 2-신호 분리·cross 재정의(지표교차=진짜게이트/자산군교차=교란통제/코인내부=비진단강등/측정교차=대체1순위)·regime(vol분할 순환→연속통제, 무조건부 먼저). ⑤폐기 현-프레임 재검(.p2-revisit.py): realized_vol(⊥HAR 흡수)·active_addr(⊥타지표 흡수)·netflow·mvrv(momentum proxy) 전부 기각 robust 재확인, funding→vol 약세 −0.151 marginal 신규. ⑥candidate 16 논문대조 카탈로그(handoff §4): A측정완료7·B데이터게이트5·C진짜갭(btc_dominance reason공란 미측정/USDT netflow Chi-Chu-Hao robust지만 데이터게이트/investor attention pytrends보유/IVOL/소형size).
> **(2) 다음 의도**: ①reserve→vol S6 15축 audit(독립 subagent)→채택게이트 ②btc_dominance 측정(진짜 미탐구) ③investor attention(pytrends) ④Bonferroni→FDR 재판정. 전부 자율, go-live=사람게이트.
> **(3) 동기화**: ledger crypto 갱신(exchange_reserve candidate·netflow rejected_prov·sopr 유료게이트확정·realized_vol/active_addr 재검·헤더 rejected_prov 7→8). MEMORY.md measurement-methodology entry 정정. handoff §6 5곳 정정. promo-log ERROR. 산물=.p2-exchflow{,-s4,-s4b,-s4c,-cross}.py + .p2-revisit.py + result.json + .consult-exchflow-{briefing,R2}.md + handoff-exchflow-20260603.md. push금지.

> [ckpt-202606031200:btn-Inv]
> **(1) 마지막 결정**: ①xs_momentum 6단계 완주=rejected_provisional(size 팩터 베타, 다팩터 직교 t3.69→0.75, 졸업3관문 전실패, S6 audit 통과). ②6단계 SOP(S6=15축 audit) 박제=프로젝트 CLAUDE.md §코인6단계+plan+framework+progress+handoff. ③호라이즌 확장(.p2-horizon.py)=BTC TSMOM 30-60일 sweet spot·90일+ 약화, XS 단기전용. ④adopted 재검토(자문 gemini+claude 수렴+S6 audit): MVRV 0.55 과대(momentum 공선성+강세편중, 직교화 순효과 -0.10[realcap 순환참조 정정])·stablecoin in-sample 환상(외생분해 소멸·OOS eff_n 비유의)·funding/ETF 제거·반감기 label. ⑤거시 grid(.p2-macro-grid.py) M2 NW후 0셀·real under-powered=point forecast 알파 아님. ⑥harness 2결함 S6 audit 적발 정정(grid NW미적용·MVRV realcap 순환참조)=promo-log ERROR. ⑦★사용자 지적 "다 봐도 무신호=측정 한계"=빠진축 5종(데이터[USDT netflow]·변동성예측·intraday·비선형·carry) 식별. 변동성예측 측정(.p2-vol-forecast.py)=우리 지표 약(funding 약세장 -0.149.만, netflow 미측정).
> **(2) 다음 의도**: subagent **a3c789bc**(측정방법론 빠진축 + USDT netflow/SOPR 무료 데이터 소스 리서치) 결과 대기→빠진축 메우기. 자율 가능=비선형/임계 조합·intraday(Binance 1h fetch). 데이터 게이트=USDT netflow/SOPR/청산(무료 소스 subagent 조사중). carry/vol drop 매트릭스(plan §3b) 잔여. adopted 비중 재배분=사용자 Q1 "권고만 박제, weight=go-live 게이트"(미확정).
> **(3) 동기화**: ledger crypto 전부 갱신(xs rejected_prov·mvrv/funding/stablecoin/m2/real S4+audit 정정 4곳). 산물=.p2-{xs-netcost,xs-diagnose,xs-binance,xs-binance-oos,xs-factor,xs-survivorship,xs-codrawdown,mvrv-s4,stablecoin-s4,macro-grid,horizon,vol-forecast}.py + result.json. 자문=.consult-{xs,adopted}-R1-{gemini,claude}.txt. handoff=handoff-coin-adopted-horizon-20260603.md.
