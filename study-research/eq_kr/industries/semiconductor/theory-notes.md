---
tags: [type/theory-notes, domain/equity, sector/semiconductor, scope/equity-kr]
date: 2026-06-05
purpose: S1 학술 ground — 반도체 cycle 이론·증권사 in-depth 정독 → 메커니즘·부호 사전확약(HARKing 방지). 결론·목표가는 증거 아님, 메커니즘·가설만 추출.
sources: Gemini Pro 리서치(2026-06-05) + round-1.md 가설 사전박제(2026-05-31, 측정 前) + frame v3 §M.11~M.12
---

# semiconductor(반도체) 산업 이론·메커니즘 정리

> ★**HARKing 방지 (team-lead 조건2)**: 본 부호 사전확약은 **이론 기반 독립 수립** 후 기존 v3 측정(2026-06-03)과 대조한다. 어긋나면 재검.
> ★증거 추적: round-1.md(2026-05-31) = **측정 前** 작성된 가설 H1~H8 (부호 사전박제 = HARKing 아님의 1차 증거). 본 theory-notes 는 그 위에 학술 ground + conditional 가설 추가.

## §0. 핵심 산업 특성 (cyclical archetype)

반도체(특히 메모리 DRAM/NAND)는 **강 cyclical 산업**. ASP(평균판매가) 사이클이 capex·재고·수요로 2-3년 주기 진동. 한국 = 삼성전자(005930)+SK하이닉스(000660)가 반도체 시총 93% 집중(Mag7보다 극단) + 외국인 시총비중 50%+ + 수출 95%+. 이 4 특성(cyclical / 집중 / 외국인 / 수출)이 신호 부호·conditional 구조를 결정.

## §1. 메커니즘별 부호 사전확약 (★측정 前 이론 동결)

### M1. 가격 momentum → long-horizon reversal (음)

- **메커니즘**: cyclical 산업에서 12M 누적수익 momentum 최강 시점 = 사이클 **정점**. 정점에선 공급과잉·이익추정 하향 → 급격한 되돌림. 투자자 extrapolative bias(과거 강성과 연장 기대 → 고점 매수) → 사이클 전환 시 최대 손실. = "momentum crash" 와 동형.
- **부호 사전확약**:
  - 12M+ long-horizon momentum: ★**음(-) reversal** (많이 오른 종목 → forward 약).
  - 3-6M short/medium: 양(+) continuation 가능(뉴스·실적 연속성). horizon 따라 부호 전환 가능.
- **출처**: Daniel & Moskowitz (2016) "Momentum Crashes" JFE [ssrn 2371227] / Grinblatt & Moskowitz (2004) "Predicting stock returns using industry-relative firm characteristics" JF / Bernstein "The Semi Handbook" (실무, 사이클 정점 되돌림 패턴 반복).
- **round-1 대조**: round-1 H6 = "12-1 momentum 한국 약효, 반도체 한정 검증"(부호 미확약, 탐색적). 본 theory 는 cyclical 이론으로 **음 reversal 사전확약** 강화.
- **반증조건(falsifier)**: 12M momentum IC ≥ +0.03 (continuation) → cyclical reversal 가설 기각.

### M2. valuation: PBR(음, 작동) vs PER(무효, peak-EPS trap)

- **메커니즘**:
  - PER trap: 사이클 정점 EPS 극대 → PER=P/EPS 분모 팽창 → "저PER" 착시 → 매수 → 업황 둔화 EPS 급감 → 함정. EPS = 민감 flow 변수.
  - PBR robust: BPS = 축적 자본 stock 변수, 사이클 둔감 → EPS 왜곡 면역. 청산가치 안정 기준점.
- **부호 사전확약**:
  - 저PBR(낮은 z) → forward 양 = **IC 음(-)** (전통 value premium).
  - 저PER: cyclical 에선 부호 불일관 또는 무효(역발상). PER value premium **비유의 prior**.
  - PBR value premium 이 PER보다 robust.
- **출처**: Asness, Frazzini, Pedersen "Quality Minus Junk" RAS (이익 질 = cyclical 정점이익 저품질 → book-value 기반 우월) / Lazard (2016) "The P/E Ratio: A Poor Measure of Value for Cyclical Stocks" / Bernstein "Peak Earnings Are A Trap"(PER=반도체 최악 지표, PBR/EV-Sales 대안).
- **round-1 대조**: round-1 H8 = OP margin yoy(펀더멘털). 본 theory 가 PBR vs PER 부호 차등을 archetype 이론으로 사전확약 추가.
- **반증조건**: PBR IC |ρ|<0.03 전 horizon → value premium 무효 / PER IC 유의(|ρ|>0.05 + p<0.05) → peak-EPS trap 가설 기각.

### M3. 외국인 flow → 양 + ★conditional (flow regime × 팩터 IC)

- **메커니즘**: 외국인 = 정보우위(글로벌 산업 통찰) OR 가격압력(거대자금 수급불균형). 삼성/SK = 외국인 지분율 50%+ → flow 민감. ★**conditional**: passive(ETF) 자금 강할 때 = 시장전체 이동 → 개별 종목신호(value/momentum) IC **약화**. active(롱숏) 자금 강할 때 = 팩터 신호 강화.
- **부호 사전확약**:
  - 외국인 순매수 강도 → forward 1-3M **양(+)**.
  - ★conditional: 외국인 강매수 regime 에서 value/momentum IC **감소**(passive 지배). = 36셀 regime 축의 외국인flow 차원이 신호 IC 변조한다는 가설.
- **출처**: Choe, Kho, Stulz (2005) "Do domestic and foreign investors behave differently?" JFQA (외국인 거래 주가영향 大, positive feedback + loss-realizing) / Grinblatt & Keloharju (2000) JFE (외국인 성과우위 = 정보우위 가설) / 국내 증권사 수급분석 리포트.
- **round-1 대조**: round-1 H5 = "외국인 flow regime → 메모리 sub"(Tier1 핵심, 부호 미확약). 본 theory 가 **양(+) + conditional IC 감소** 사전확약.
- **반증조건**: 외국인 flow IC ≤ 0 (forward 음/무) → 정보우위·가격압력 가설 기각 / regime별 IC 차 <0.02 → conditional 무효.
- ⚠️ **데이터 막힘**: KRX 인증 차단 → ECOS 외국인 증권투자 OR EWY proxy OR KODEX 반도체 ETF flow 로 해소 필요(현 미측정 = candidate-ledger 이연).

### M4. DRAM cycle + USDKRW(양) + 글로벌 동조(contemporaneous>forward)

- **메커니즘**:
  - 메모리 4국면: 회복(가격 바닥·주가 선반등) → 호황(이익 극대·주가 고점) → 둔화(가격 꺾임·주가 선하락) → 침체(적자·주가 저점). ★주가가 실적보다 선행.
  - USDKRW 강세(원화 약세) → 달러매출 95% 원화환산 자동 증가. 환헤지 100% 아님 → 환율 상승 = 긍정.
  - SOXX/NVDA = 글로벌 수요·투자심리 반영 → 한국 반도체와 **contemporaneous corr 매우 높음**(동행), forward 예측력 **약**(동일 정보 동시 반응).
- **부호 사전확약**:
  - DRAM ASP 변화율 → 양(+).
  - USDKRW yoy → 양(+) (수출주 베타).
  - SOXX/NVDA lagged → forward 예측력 **약/무**, contemporaneous 동조 강.
- **출처**: Morgan Stanley "Memory Market Tracker"/"Blue Paper on Semiconductors" / 삼성·SK증권 환율 민감도 리포트(환율 10원↑ → 분기 영업이익 ΔOOO억) / Bloomberg SOXX-삼성/SK corr 시계열.
- **round-1 대조**: round-1 H1(USDKRW→메모리 outperform, 양) + H2(NVDA→SK/한미반도체) + H3(수출 yoy→메모리) + H4(SMH/SOXX→산업평균, corr>0.7) = **측정 前 박제됨**. 본 theory 가 ★"SOXX forward 예측력 약"(contemporaneous만)을 사전확약 = §D forward-alpha falsifier 와 정합.
- **반증조건**: USDKRW unconditional IC 음/무 → 수출주 가설 약 (★단 KRW regime conditional 재검 의무) / SOXX forward corr >+0.30 유의 → 동행 아닌 선행 (가설 기각).

## §2. ★사전확약 부호 요약표 (측정 前 동결, conditional IC 측정 대상)

| 신호 | unconditional 부호 사전확약 | conditional 가설 (36셀 축) | 학술 ground |
|---|---|---|---|
| price momentum 12M | ★음(reversal) | KRW약세·flow강매수 regime 에서 reversal 강화? | Daniel-Moskowitz 2016 |
| price momentum 3-6M | 양 가능(continuation) | — | Grinblatt-Moskowitz 2004 |
| PBR value | ★음(저PBR→고forward) | down-cycle(SOXX bear) regime 에서 value premium 강? | Asness QMJ, Lazard 2016 |
| PER value | 무효(peak-EPS trap) | 전 regime 무효 prior | Bernstein |
| 외국인 flow | ★양(forward 1-3M) | flow강매수 regime → value/momentum IC 감소 | Choe-Kho-Stulz 2005 |
| USDKRW yoy | ★양(수출 베타) | KRW regime 자체축이라 conditional 본질 | 증권사 환율민감도 |
| SOXX/NVDA lagged | forward 약/무 (동행만) | — | MS Memory Tracker |

## §3. conditional IC 본체 (dispatch 원의도)

★측정 대상 = `IC(지표, regime 36셀, horizon)`. regime = Macro 4 × KRW 3 × 외국인flow 3. horizon = y_5d / y_20d(메인) / y_60d.
- 출력 예: "DRAM down-cycle(SOXX bear) + 외국인 순매도 regime 에서 저PBR 반도체 20d 강세(부호 음, IC CI 0 제외)".
- ★사전확약 핵심 conditional 가설 2: (i) 외국인 강매수 regime → value/momentum IC 감소(M3 passive 지배) (ii) KRW 약세 regime → 수출주 베타 강화(M4). N<24 cell collapse(frame §M3).

## §4. 정직 단서 (over-claim 회피)

- ★**측정값 정합 ≠ HARKing, 단 OOS 확증 아님 (team-lead 정정 2026-06-05)**: 본 부호(음 momentum / PBR○ PER✗ / 외국인 양 / SOXX 동행)는 round-1(측정 前) + 학술 이론으로 독립 수립 → 기존 v3 측정과 정합 = HARKing(post-hoc 가설맞춤) 아님. ⛔**단 동일 in-sample 데이터라 "이론이 데이터로 확인된 강한 증거"는 over-claim** — 이론이 데이터로 '확인'되려면 OOS 필요. **현 = in-sample 정합(tentative), OOS 미검증**. CPCV OOS hit 도 in-sample 내 walk-forward이지 진짜 holdout 아님(2026년 이후 신규 데이터 = 진짜 OOS). → 모든 부호 = "in-sample 방향 일관, OOS pending" hedge 의무.
- ★단 magnitude 단정 금지: PBR 24M t=-4.23 은 eff_indep≈2.5 overlap inflation(§M.12). 부호는 robust, magnitude 는 breadth-adj IR(-1.52) 로 hedge.
- ★small-n: cell N<24 "유의" 금지. n<30 hedge 어휘(방향성 약 prior / 비유의 / CI 넓음 / tentative).
- ★single-source 금지: 각 부호 = 학술 + 실무 + 우리 PIT 측정 3중. 증권사 목표가·투자의견은 증거 아님(메커니즘만 추출).

## §5. ★기존 결과 비판 검토 (team-lead 강조: 무비판 채택 금지)

> S1 리서치 = 방향 잡기. 기존 v3/round-1 결과를 학술·실무 근거로 **비판 검토** → 통과분만 채택, 미달분 재검/격하.

| 기존 결과 | 비판 검토 | 판정 |
|---|---|---|
| momentum 음 -0.065 (reversal) | Daniel-Moskowitz 2016 + Bernstein = cyclical peak reversal 이론 강력 지지. ★단 BY 미생존 = magnitude 약 → conditional(KRW_weak interaction t=-2.95)로 발현이 본질 | **채택(conditional)**: unconditional 약, regime-conditional 강 |
| PBR 24M -0.114 t=-4.23 BY생존 | ★t=-4.23 = eff_indep≈2.5 overlap inflation(§M.12). Asness QMJ/Lazard = PBR robust 지지하나 magnitude 과대평가 | **부호 채택 / magnitude 격하**: y_5d/20d/60d(eff_N 큼) 재배치 = pbr robust 재확인(wc_p 0.001~0.0045) |
| PER 무효 (peak-EPS trap) | Bernstein "Peak Earnings Are A Trap" + Lazard 직접 지지. 이론·측정 정합 | **채택**: cyclical 정의 입증 |
| credit β -0.190 (US HY proxy) | KR HY 부재 → US proxy n=35. single-source 위험(학술 근거 약) | **tentative 유지**: KR credit spread 확보 전 격하 |
| customer momentum REJECTED | MS Memory Tracker = SOXX contemporaneous>forward 지지. forward null 정합 | **REJECTED 확정**: 동조성분 RegimeGlasso 흡수 |
| dollar β 비유의 (수출 가설 약) | ★unconditional 비유의 ≠ conditional. KRW regime 자체가 conditional 축 → KRW_weak에서 신호 증폭 발견 = 수출 메커니즘 conditional 발현 | **재검 후 conditional 채택**: unconditional 기각은 성급 |

### §5.1 ★비판 2종 = 데이터로 직접 검증 (2차 리서치 반증조건 실측, team-lead "틀렸을 수 있다는 전제")

> 2차 리서치(Gemini Pro)가 제기한 핵심 비판 2종을 **데이터로 직접 검정**. 둘 다 "기존 결과 견고"로 판명 = 무비판 채택 아닌 검증된 채택.

- **★Q6 비판 "PBR = size factor 위장 아닌가?"** → **기각**(PBR 독립 alpha 입증):
  - Fama-MacBeth(Return ~ PBR_rank + Size_rank, y_20d): PBR univariate b=-0.051(t=-3.15) → **Size 통제후 b=-0.043(t=-2.47) 유의 유지**. Size|PBR 통제후 b=-0.018(t=-0.99) 비유의.
  - = PBR value premium 이 size 통제 후에도 살아있음 = small-cap 위장 아님. 출처 = Fama-French 1992/1993, Asness-Moskowitz-Pedersen 2013 "Value and Momentum Everywhere"(size 통제 후 value robust).
- **★Q10 비판 "HBM/AI cycle(2023-26)이 표본 지배 → episode 종속?"** → **기각**(sub-period 부호 일관):
  - pre-HBM(2019-2022) vs HBM(2023-2026) sub-period IC: mom_6(-0.005/-0.055) / rev_1m(-0.062/-0.025) / pbr_z(-0.034/-0.071) = **3신호 모두 부호 일관**(structural break 없음).
  - = 단일 mega-episode 종속 아님. 단 각 기간 단독 약(small-n) = full-sample/conditional 이 더 적합. 출처 = Bai-Perron 1998 structural break, Hansen 2001.
- **★Q5 비판 "momentum reversal = small-sample/대형주 의존?"**: 기존 leave-episode(ex-peak 생존) + cap-weighted IC -0.092(대형주서 더 강) = 이미 부분 점검. ⏳ 삼성/SK 각각 제외 LOO = 후속 의무(candidate-ledger falsifier). 출처 = Hou-Xue-Zhang 2020 "Replication Crisis", De Bondt-Thaler 1985.

## §6. ★추가 메커니즘·지표 발굴 (team-lead 강조: 발굴이 방향잡기)

S1 리서치(1차+2차)로 식별된 **미측정 지표·메커니즘** (candidate-ledger 이연 등록). ★부호 사전확약 + 학술 ground 명시:

| 신규 지표 | 메커니즘 | 부호 사전확약 | 데이터 소스 | 학술 ground |
|---|---|---|---|---|
| **재고순환** (재고자산/매출, 재고일수) | 재고 peak→주가 bottom(업황바닥 선반영), 재고 bottom→주가 peak(공급과잉 우려) = 역상관 | **음(-)**: 高재고→forward 양 | DART 재고자산(분기 재구성) | Chen-Novy-Marx-Zhang 2010(investment factor), GS/MS 재고 cycle |
| **CAPEX/총자산** (asset growth) | 과잉 capex→1-2Y 후 공급과잉→이익훼손 (과잉투자의 저주) | **음(-)**: 高capex→forward 약 | DART CAPEX/PP&E 증가율 | Cooper-Gulen-Schill 2008 "Asset Growth Anomaly", Titman-Wei-Xie 2004 |
| **R&D/총자산** | 미래 기술경쟁력 투자(단순 설비와 다름) | **양(+)**: 高R&D→forward 강 | DART 무형자산/R&D | e-KJFS growth factor |
| **DRAM ASP proxy** (반도체 PPI yoy) | 메모리 4국면 가격 driver. ASP↑→주가 양 | **양(+)** contemporaneous | FRED PCU334413334413(수집완료) | MS Memory Tracker |
| **종목레벨 외국인 flow** (순매수/시총 cs-rank) | 시장레벨 regime(베타)과 별개 = 종목선별 알파(α). MSCI rebal 기간 제외 시 강화 | **양(+)** forward 1-3M | KRX 종목별(인증 차단)→대안 탐색 | Grinblatt-Keloharju 2000, Barber-Odean-Zhu 2009(기관 net buy 예측력) |
| **size-orthogonal PBR** | PBR value 가 size 위장인지 직교 점검 | PBR 독립 음(-) | DART(측정완료 §5.1) | Fama-MacBeth 1973, Asness 2013 |

- ★발굴 핵심: 재고순환·CAPEX = **반도체 산업 내재 cycle**(공급사이드)을 잡는 Layer 1/3 신규 후보. 가격·valuation 신호와 직교 가능성 높음(별 메커니즘). DART 재구성 가능 = 측정 가능.
- ★시장레벨 vs 종목레벨 외국인 flow 구분(Q9): 본 S2 = **시장레벨 regime**(ECOS 외국인순매수 28d z)으로 flow regime 축 측정 완료. **종목레벨 cs-signal**(개별 외국인 순매수)은 KRX 종목별 차단 → 미측정(이연). 둘은 다른 신호(regime vs alpha).
- 본 S2 측정 완료 = 가격(mom/rev/vol) + valuation(PBR/PER) + flow regime + size-orthogonal PBR. 펀더멘털 cycle(재고/CAPEX/R&D) = candidate-ledger 이연(DART 분기 재구성 후속).
