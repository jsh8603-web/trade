# ETF Fallback 라우팅 ledger (Phase 1, 2026-06-06)

> Phase 0 등급(KR within v2 + US within-residual-us-v1) → 약변별(低/불가) sleeve 라우팅 1차.
> 라우팅 = `N≥5(비용proxy) ∧ 적격passive-ETF존재 ∧ look-through통과 ∧ PIT max-lag` → RepresentativeETF / 그 외 EW.
> ★ETF 적격성(look-through·AUM·TER) 최종 확정 = Phase 2 (FDR/yfinance fetch) 후. 본 ledger = 1차 분기.

## 한국 (within v2 低9 + refining 불가)

| sleeve | n종 | N_eff | 등급 | FDR ETF(검증분) | 1차 라우팅 | 근거 |
|---|---|---|---|---|---|---|
| financial | 34 | 18.5 | 低 | 은행 7 | **ETF** | 大N + ETF 풍부 |
| battery | 29 | 19.3 | 低 | 2차전지 18 | **ETF** | 大N + ETF 풍부 |
| bio | 38 | 17.4 | 低 | 바이오 17 | **ETF** | 大N + ETF 풍부 |
| shipbuilding | 16 | 11.7 | 低 | 조선 7 | **ETF** | 大N + ETF 존재 |
| consumer | 28 | 9.6 | 低 | 소비재(확인要) | **ETF**(잠정) | 大N, ETF 적격성 Phase2 |
| chemical | 17 | 4.4 | 低 | 화학 3 | **ETF**(과점주의) | N_eff 4.4 과점 but ETF 존재 |
| auto | 17 | 7.3 | 低 | 자동차 3 | **ETF**(소수ETF) | ETF 3개 中 적격 1 선정 |
| telecom | 14 | 8.1 | 低 | 통신 1 부적합 | **EW** | ETF 부적합 + 실질 3종 과점(SKT/KT/U+) |
| refining | 11 | 7.6 | 불가 | 정유 0 | **EW** | ETF 부재 + 2종 과점(SK이노/S-Oil) |

## 미국 (within-residual-us-v1)

| sleeve | n종 | N_eff | 등급 | ETF | 1차 라우팅 | 근거 |
|---|---|---|---|---|---|---|
| us_cyclical | 60 | 36.8 | 中 | — | **selection 유지**(fallback X) | PBR/EV-EBITDA CONFIRMED 작동 |
| us_defensive | 48 | 35.4 | 低 | XLP/XLU/XLV/XLC | **ETF**(sub-sector별) | 大N, value/quality 약 |
| us_mega_tech | 11 | 6.6 | 불가 | — | **basket 유지**(이미 11종) | N_eff 6.6≪11 과점, custom basket 자체 보유 |

## 라우팅 요약 (Phase 1-2 ETF 선정 + AUM floor 반영)
- **ETF fallback** (AUM≥500억 passive broad, etf-picks-20260606.json): KR {financial=KODEX은행 6143억, battery=KODEX 2차전지산업 20452억, bio=KODEX바이오 2454억, shipbuilding=HANARO Fn조선해운 875억, auto=KODEX자동차 5650억} + US defensive {XLP/XLU/XLV/XLC sub-sector}
- **EW 직접보유**: KR {consumer(AUM 160억<floor), chemical(360억<floor), telecom(ETF부적합), refining(ETF부재·과점)}
- **현행 유지**: US cyclical(selection 작동) + US mega_tech(이미 basket)

## Phase 1-2 선정 결과 (1차, look-through 휴리스틱)
- ★active/factor tilt 제외(고배당·TOP10·플러스·동일가중·해외추종) = passive broad 우선 = look-through 1차.
- ★리턴(EarningRate) 배제, AUM(MarCap 근사)·거래대금(Amount) 기준 선정 = 자문 D2 정합.
- ⛔ 미완(Phase 1-3/2): 운용사 PDF look-through(passive 확정) + realized-TE + TER + tax/FX + AUM floor 임계 정밀(현 500억 잠정).

## Phase 5 백테스트 실측 (실 PIT, 2026-06-06)

| sleeve | ETF | 표본 | EW누적 | ETF누적 | MDD(EW/ETF) | TE annual | 디커플링 | 라우팅 함의 |
|---|---|---|---|---|---|---|---|---|
| financial | 091170 KODEX은행 | 2019-2026 n=1816/34종 | +230.6% | +174.9% | -52.2%/-47.4% | **14.65%** | 비유의(약 under) | ⚠️**TE 큼** = 은행 ETF가 광의 financial(은행+증권+보험) 부분커버 |

- ★**financial 라우팅 재검토 신호**: KODEX 은행 ETF는 sleeve 34종(은행/증권/보험/지주) 중 은행만 → 일별 TE 14.65%. 대안 (a) sleeve를 "은행 협의"로 좁혀 ETF 정합 (b) "증권/보험 포함 광의 금융 ETF"(KODEX 보험·증권 별도) 멀티-ETF (c) EW 유지. ★small-n: 단일 sleeve·기간 한정 방향성 prior, 다sleeve OOS 후 확정.
- MDD는 ETF 우위(-47% vs -52%, 34종 EW가 변동성↑). 디커플링 월별 비유의 = "지속 알파/드래그 신호 없음"(단 일별 추종은 부정합).
- ⛔슬리피지 floor clip(EW=ETF 1.72% 동일) = 비현실 — amount.parquet 종목별 거래대금 정밀화 미해결.

## SELECT(우리 경로) vs EW vs ETF 3자 실측 (가격 signal sleeve, 2026-06-06)

> capsule 측정 signal(within_residual_kr SSOT)로 top-K 월리밸 = 우리 selection 동형. 가격기반 signal만(PBR=시총 시계열 부재 제외).

| sleeve | signal | SELECT | EW | ETF | SELECT−EW 알파(연,t) | 판정 |
|---|---|---|---|---|---|---|
| battery | mom_6 | +1808% | +772% | +159% | **+16.8%/yr (t=1.87)** | 종목선택 우위(약유의) + ETF 최악 |
| steel | mom_12_1 rev | +225% | +272% | (없음) | -0.5% (t=-0.07) | 종목선택 무의미(≈EW) |
| chemical | vol_60 | +176% | +163% | +74% | -0.3% (t=-0.05) | 종목선택 무의미 + ETF 하회 |
| shipbuilding | lowvol_60 | +192% | +300% | +231% | -1.4% (t=-0.19) | 종목선택 무의미 + ETF 하회 |

### 사용자 가설 검증 결과
- **"선별 효과 있으면 종목선택 유리"** → **부분 참**: battery만 EW 대비 알파 +16.8%/yr(t=1.87 약유의). 나머지 3개는 selection이 EW 대비 무의미(t<0.2). ★capsule IC(상대 변별, long-short)와 top-K 절대수익(long-only vs EW)은 다른 측정 — IC -0.18(steel)이어도 top-K가 EW 못 이김.
- **"선별 효과 없으면 ETF 유리"** → **반박**: selection 무의미한 sleeve에서도 ETF가 EW·SELECT 모두 하회(chemical ETF+74% vs EW+163%, ship ETF+231% vs EW+300%). ETF는 어느 경로에서도 수익 최선 아님.
- **함의**: ETF fallback의 가치 = 수익이 아니라 **거래비용·유동성·운영단순**. 수익만 보면 EW basket(또는 가능 sleeve의 top-K) > ETF.

### ⛔ 강한 caveat (단정 금지, E94/small-n)
- EW·SELECT = survivorship(상폐 미포함) + 거래비용/소형주 슬리피지 과소 → **과대평가**. ETF는 실거래(편향 없음, 비용 내재).
- battery SELECT +1808% = 극단치(소수 종목 집중) 의심. t=1.87 = p≈0.06 약유의(autocorr 미보정 IID 상한).
- 따라서 "EW>ETF 무조건"이 아니라 **"테마 ETF가 구성종목 직접보유 대비 수익 부진 경향 + 편향 보정 시 축소 가능"**까지가 방어선.

## 공정 맞대결 (자문 R1 반영 비용 보정, AUM 1억, 2026-06-06)

> 자문(gemini+claude) = "EW>ETF는 survivorship+소형주 비용 착시". √임팩트+ADV캡+STT+haircut4% 반영 net 재대결.

| sleeve | EW_gross | EW_net | ETF | net−ETF(연,t) | 판정 |
|---|---|---|---|---|---|
| financial | +190% | +44% | +164% | -8.4%(t=-2.2) | **ETF 우위(유의)** |
| consumer | +54% | -23% | +58% | -11.5%(t=-1.6) | ETF 우위 |
| auto | +255% | +62% | +222% | -9.9%(t=-1.6) | ETF 우위 |
| chemical | +149% | +19% | +65% | -4.2%(t=-0.6) | ETF 약우위 |
| bio | +383% | +138% | +2% | +11.1%(t=2.6) | **EW 우위(유의)** |
| battery | +732% | +301% | +133% | +5.6%(t=0.9) | EW 약(비유의) |
| shipbuilding | +300% | +172% | +231% | -1.9%(t=-0.2) | 무승부 |

### 핵심 결론 (자문 검증)
- ★**비용 보정이 EW 우위를 다수 뒤집음** = 자문 "착시" 가설 확인. EW_net이 gross 대비 폭락(consumer +54%→-23%). financial/consumer/auto/chemical = ETF 우위로 역전.
- ★**예외 bio**: KODEX 바이오 ETF +2% = ETF 자체가 실패작(트래커 부실, 특정종목 집중). EW 비용 보정 후에도 우위(t=2.6). 자문 사전("bio 붕괴")과 반대 = ETF 종목 mismatch가 size/비용보다 큼.
- ★자문 "sleeve별 하이브리드" 권장은 맞음. 단 어느 게 ETF/EW인지는 자문 사전과 다름 — **데이터가 답**.

### 라우팅 반영 (비용 net + t 기준)
- **bio ETF→EW** 변경(KODEX바이오 +2% 실패작, EW net t=2.6 유의). ★단 EW survivorship 잔존 — 정밀은 상폐 PIT 후.
- financial/auto/battery/shipbuilding = ETF 유지(net ETF 우위 or 무승부+운영단순).
- consumer/chemical = EW 유지(net ETF 우위지만 ETF AUM 작음<500억=청산리스크 floor, 수익↔청산 상충 → 보수적 EW).

### attribution 회귀 (자문 C9 — (EW_net−ETF) ~ market + size(EW−VW) OLS)
| sleeve | R² | size_β | 잔차 α(연) | 해석 |
|---|---|---|---|---|
| bio | 0.19 | **+0.05(≈0)** | +10.7% | ★size 아님 → ETF 트래커 부실 구조적 → EW행 정당(size-ETF 대체 불가) |
| battery | 0.31 | +0.56 | +10.8% | size 틸트 기여 + 구조 혼합 |
| financial | 0.15 | +0.25 | -8.3% | ETF 우위(잔차 음) |
| auto | 0.08 | +0.63 | -2.9% | size 일부 but ETF 우위 |
- ★bio 격차는 size_β≈0 = 순수 size 틸트 아닌 **ETF 자체 부실**(잔차 α가 전부) → bio EW 전환은 더 싼 size-ETF로 대체 불가능 = 정당. battery는 size_β 큼 → EW 우위 일부 size(ETF 유지 무난).

### ⛔ caveat (단정 금지)
- haircut 4% + AUM 1억 + survivorship 잔존(상폐 backfill 불가, haircut 차선) = 가정 의존. AUM↑ 시 EW 비용 초선형↑ → ETF 우위 확대.
- 정밀 확정 = 상폐 PIT universe + KR/US 세금 분리(국내 직접 양도세≈0 vs ETF 배당소득15.4%) 후. 자문 Q3.

## 미해결 (Phase 2 fetch 확정)
1. consumer 소비재 ETF 적격성(KODEX 필수소비재 등) 실재 확인
2. chemical 과점(N_eff 4.4) — ETF vs EW 재판정 (look-through 통과 시 ETF / 실패 시 EW)
3. auto ETF 3개 적격성 (TIGER 자동차 등 passive 여부)
4. US defensive = sleeve 통째 1 ETF vs sub-sector(XLP/XLU/XLV) 4개 — sub-sector별 변별력 미산출(sleeve pooled)
5. telecom/refining 인접테마 EW 종목 확정 (정유=SK이노/S-Oil, 통신=SKT/KT/U+)
