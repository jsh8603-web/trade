---
tags: [type/theory-notes, domain/equity, sector/auto, scope/equity-kr]
date: 2026-06-05
purpose: S1 학술 ground — 자동차 cycle 이론·증권사 in-depth 정독 → 메커니즘·부호 사전확약(HARKing 방지). 결론·목표가는 증거 아님, 메커니즘·가설만 추출.
sources: Gemini Pro 리서치(2026-06-05, /tmp/auto-search-result1.txt) + 기존 v3 측정(summary.yaml 2026-06-03, 측정 前 아님 = 비판검토용) + frame v3 §M.11~M.12 + 반도체 theory-notes 미러
---

# automobile(자동차) 산업 이론·메커니즘 정리

> ★**HARKing 방지 (반도체 미러 + team-lead 조건)**: 본 부호 사전확약은 자동차 cycle **이론으로 독립 수립** 후 기존 v3 측정(2026-06-03)과 대조한다. ★단 기존 v3 측정이 **측정 前 사전등록(round-1 류) 부재** = 자동차는 이론-우선 사전확약을 본 theory-notes 에서 처음 동결한다. 어긋나면 재검.
> ★증거 추적: 자동차는 반도체 round-1.md 같은 측정 前 가설 박제가 없음 → 본 theory-notes 의 §1 부호 사전확약이 1차 동결점. conditional IC 측정(measure_conditional.py)은 이 동결 후 실행.

## §0. 핵심 산업 특성 (cyclical archetype — 단 반도체와 다른 cycle 원천)

자동차(완성차/부품/타이어)는 **경기민감 cyclical** 산업. ★단 반도체와 **cycle 원천이 다름**:
- **반도체** = ASP(가격) cycle — 공급·수요 급격 불일치로 가격 수직 급등락 → **강한 reversal**.
- **자동차** = Volume(판매량) cycle — 거시(금리·소비심리)·인구·신차 사이클이 판매량을 **점진적**으로 움직임 → 반도체보다 **reversal 약/지속성 길 가능성**.

한국 자동차 = 현대차(005380)+기아(000270)+현대모비스(012330)가 산업 시총 ~70% (반도체 93% 보다 덜 극단, 부품주 분산 多) + 수출/해외 비중 80%+(현대차/기아) + 외국인 지분율 30-50%. 이 특성(cyclical-volume / 수출 / 외국인 / 해외생산 헤징 복잡)이 신호 부호·conditional 구조를 결정.

## §1. 메커니즘별 부호 사전확약 (★측정 前 이론 동결, conditional IC 측정 대상)

### M1. 가격 momentum → reversal prior (음), 단 반도체보다 약

- **메커니즘**: cyclical 산업 momentum 최강 시점 = 사이클 정점. 자동차는 판매량(volume) cycle = 점진적 둔화 → 반도체 ASP 급락보다 **reversal 약하고 continuation 지속 길 가능성**. Daniel-Moskowitz momentum crash 는 자동차에 적용 가능(고베타 경기민감주 = 약세장 후 급반등 시 momentum short-leg → crash 주요 구성).
- **부호 사전확약**:
  - 12M+ long-horizon momentum: ★**음(-) reversal prior** (단 반도체보다 약, 비유의 가능성 높음).
  - 3-6M short/medium: 양(+) continuation 가능(신차·실적 연속성, 자동차는 반도체보다 continuation 우세 prior).
  - ★자동차 momentum 은 **unconditional 약/비유의 prior** → conditional(regime)에서 발현 여부가 측정 핵심.
- **출처**: Daniel & Moskowitz (2016) "Momentum Crashes" JFE [ssrn 2371227] / 유진투자증권 "경기민감주 투자의 나침반"(2022, 변곡점 momentum 유효성 저하).
- **반도체 대조**: 반도체는 음 reversal robust(BY 미생존이나 방향 강). 자동차는 더 약할 prior(volume cycle).
- **반증조건(falsifier)**: 12M momentum IC ≥ +0.05 유의(continuation) → cyclical reversal 가설 기각 / IC ≤ -0.05 유의 → reversal 강(반도체급).

### M2. valuation: PBR(음, 작동) vs PER(무효, peak-EPS trap) — 반도체 동형

- **메커니즘**:
  - PER trap: 자동차 = peak-earnings trap **대표 산업**. 사이클 정점 판매량·EPS 극대 → PER 분모 팽창 → "저PER" 착시 → 매수 → 업황 둔화 EPS 급감 → 함정. 정점 직후 인센티브↑·재고↑·마진 희석 = 이익 하강.
  - PBR robust: BPS = 축적 자본 stock. 자동차 = 대규모 CAPEX 장치산업 → 유형자산 가치 중요 → PBR 밴드 하단 = 저평가 판단.
  - EV/EBITDA: PER보다 유용(자본구조·감가상각 배제)하나 EBITDA 도 이익 기반 → cyclical 변동. PBR 주지표 + EV/EBITDA 보조.
- **부호 사전확약**:
  - 저PBR(낮은 z) → forward 양 = **IC 음(-)** (value premium).
  - 저PER: cyclical peak-EPS trap → 무효/불일관. PER value premium **비유의 prior**.
  - PBR > PER robust.
- **출처**: Damodaran (2012) "Investment Valuation" cyclical firms 챕터 / Asness-Frazzini-Pedersen "Quality Minus Junk" RAS / 메리츠증권 "자동차: PBR 밸류에이션의 귀환"(2023).
- **반증조건**: PBR IC |ρ|<0.03 전 horizon → value premium 무효 / PER IC 유의(|ρ|>0.05 + p<0.05) → peak-EPS trap 가설 기각.

### M3. 외국인 flow → 양 + ★conditional (flow regime × 팩터 IC)

- **메커니즘**: 현대차/기아 = KOSPI 최상위 대형주 + 외국인 지분 30-50% + MSCI Korea passive 추종 → flow 민감. ★**conditional**: Regime별 팩터 IC 변조 — (1) Risk-on 펀더멘털 자금 유입 → value 선호 → value IC↑ (2) momentum 추종 자금 → momentum IC↑ (3) Risk-off 무차별 매도 → 팩터 IC 붕괴.
- **부호 사전확약**:
  - 외국인 순매수 강도 → forward 1-3M **양(+)**.
  - ★conditional: flow_strong_buy regime 에서 value IC↑ 가능(펀더멘털 자금) / flow_sell regime(risk-off) 에서 팩터 IC 붕괴. = 36셀 regime 외국인flow 차원이 신호 IC 변조 가설.
- **출처**: Bae-Chan-Ng (2004) "Investibility and return volatility" JFE / Morgan Stanley Quant "Factor Investing in EM: Role of Macro Regimes"(2022) / Grinblatt-Keloharju (2000) JFE.
- **반증조건**: 외국인 flow IC ≤ 0 → 정보우위·가격압력 가설 기각 / regime별 IC 차 <0.02 → conditional 무효.
- ⚠️ **데이터**: KRX 종목별 외국인 net buy 인증 차단 → 시장레벨 regime(ECOS 802Y001/0030000 외국인순매수 28d z)만 측정(반도체와 동일 해소). 종목레벨 cs-signal = data-gate(이연).

### M4. ★USDKRW 수출 베타(양) — 단 반도체보다 희석, KRW regime 축 본질

- **메커니즘**: 현대차/기아 수출+해외법인 비중 80%+ → 원화 약세(USDKRW↑) = 달러매출 원화환산 증가, 원화 원가 상대 고정 → 영업이익 구조적 증가. ★단 반도체와 차이 = **민감도 희석 요인 3종**: (1) 해외 현지생산(미국공장 = 매출·비용 모두 달러 → 환효과 상쇄) (2) 헤징(선물환 → 단기 급등락 100% 미반영) (3) 경쟁통화(엔 약세 시 일본 경쟁사 가격경쟁력 → 효과 일부 상쇄).
- **부호 사전확약**:
  - USDKRW yoy → 양(+) (수출주 베타, 단 반도체보다 약/희석).
  - ★KRW regime 자체가 conditional 축 → KRW_weak regime 에서 수출주 베타·신호 증폭 가설(반도체 family_2 KRW_weak 패턴 미러 검정 대상).
- **출처**: Jorion (1990) "exchange-rate exposure of US multinationals" J.Business / 하나증권(송선재) 자동차 환율 민감도 리포트.
- **반증조건**: USDKRW unconditional IC 음/무 → 수출주 가설 약(★단 KRW regime conditional 재검 의무) / KRW_weak interaction 비유의 → 환율 conditional 무효.

### M5. ★자동차 특화 cycle 변수 (SAAR / 인센티브 / 재고 / 반도체 공급 정상화) — 거시 timing

- **메커니즘** (자동차 고유 cycle 선행지표 = regime conditioning 후보):
  - 글로벌 신차판매(LMC)·미국 SAAR: 수요 강도 선행 → forward **양(+)** (수요 견조 = 판매·이익 기대).
  - 인센티브(dealer incentive): 증가 = 수요 둔화·재고소진 마케팅비 = 마진 악화 → forward **음(-)**.
  - 재고일수(dealer inventory days): 과잉재고 = 공급>수요 신호 → 생산감축·인센티브·중고차가 하락 → forward **음(-)**.
  - 반도체 공급 정상화(2021-22 부족→2023 정상화): 공급제약 해소 = 생산회복(판매량↑, 초기 양) → 정상화 후 공급과잉·마진 희석(후기 음). = 2023-24 표본 regime 변화 driver.
- **부호 사전확약**: SAAR/판매 양 / 인센티브·재고 음 / 반도체정상화 = 표본 내 양→음 전환.
- ★**데이터 현실**: SAAR/인센티브/재고는 ★종목 cross-sectional 신호 아님 = 산업 timing 변수. 본 S2 = **DART 재구성 펀더멘털 cycle**(재고/CAPEX/R&D)로 종목레벨 cross-sectional 측정 + 반도체 PPI(차량반도체 proxy 부재 → DRAM PPI 무관)는 자동차에 미적용. SAAR/인센티브 = 외부 데이터 fetch 후속(candidate-ledger).
- **출처**: Goldman Sachs "Global Autos: Gauging the Downturn"(2023) / Cooper-Gulen-Schill (2008) "Asset Growth Anomaly" JF / 삼성증권 "자동차: 공급 정상화, 그 이후"(2023).

## §2. ★사전확약 부호 요약표 (측정 前 동결, conditional IC 측정 대상)

| 신호 | unconditional 부호 사전확약 | conditional 가설 (36셀 축) | 학술 ground |
|---|---|---|---|
| price momentum 12M | ★음(reversal) prior, 반도체보다 약 | 침체진입·KRW regime 에서 reversal 강화? | Daniel-Moskowitz 2016 |
| price momentum 3-6M | 양 가능(continuation, 자동차 우세) | — | 유진투자 2022 |
| PBR value | ★음(저PBR→고forward) | flow_strong_buy(펀더멘털 자금) regime서 value premium 강? | Damodaran, 메리츠 2023 |
| PER value | 무효(peak-EPS trap) | 전 regime 무효 prior | Damodaran cyclical |
| 외국인 flow | ★양(forward 1-3M) | flow regime → value/momentum IC 변조 | Bae-Chan-Ng 2004, MS Quant 2022 |
| USDKRW yoy | ★양(수출 베타, 희석) | KRW regime 자체축 = conditional 본질, KRW_weak 증폭 | Jorion 1990, 하나증권 |
| SAAR/인센티브/재고 | 양/음/음 (산업 timing) | regime conditioning 변수(종목 cs 아님) | GS Autos 2023 |
| 재고/CAPEX/R&D (DART) | 음/음/양 (asset growth) | KRW·flow regime conditional | Cooper-Gulen-Schill 2008 |

## §3. conditional IC 본체 (dispatch 원의도)

★측정 대상 = `IC(지표, regime 36셀, horizon)`. regime = Macro 4 × KRW 3 × 외국인flow 3. horizon = y_5d / y_20d(메인) / y_60d.
- 출력 예: "원화 약세(KRW_weak) + 외국인 순매수 regime 에서 저PBR 자동차 20d 강세(부호 음, IC CI 0 제외)".
- ★사전확약 핵심 conditional 가설 2: (i) KRW_weak regime → 수출주 베타·value/momentum 증폭(M4, 반도체 family_2 미러 검정) (ii) flow regime → 팩터 IC 변조(M3 risk-on value↑ / risk-off 붕괴). N<24 cell collapse(frame §M3).

## §4. 정직 단서 (over-claim 회피)

- ★**기존 v3 측정 = in-sample, OOS 미검증**: 기존 auto v3(momentum 음·비유의 / PBR○ PER✗)는 in-sample 정합. OOS(2023-26 split) 미검증 → 모든 부호 = "in-sample 방향 일관, OOS pending" hedge 의무. CPCV OOS hit 도 in-sample 내 walk-forward(진짜 holdout 2026+ 아님).
- ★magnitude 단정 금지: PBR 24M t=-17.6 = eff_indep≈2.5 overlap inflation(§M.12 직접 지목). 부호만, magnitude 는 breadth-adj IR hedge.
- ★small-n: ★자동차 universe **17종**(반도체 73 / battery 26 보다 작음) = magnitude 과대 위험 더 큼. cell N<24 "유의" 금지. n<30 hedge 어휘.
- ★single-source 금지: 각 부호 = 학술 + 실무 + 우리 PIT 측정 3중. 증권사 목표가·투자의견 증거 아님(메커니즘만).

## §5. ★기존 v3 결과 비판 검토 (무비판 채택 금지)

> S1 리서치 = 방향 잡기. 기존 v3 결과를 학술·실무 근거로 **비판 검토** → 통과분만 채택. ★단 conditional IC 는 v3 미측정 = 본 S2 신규 측정 대상.

| 기존 v3 결과 | 비판 검토 | 판정 |
|---|---|---|
| momentum 음 -0.064 (3M reversal), 전 16 비유의 | Daniel-Moskowitz + 유진투자 = volume cycle = reversal **약** 이론 정합. unconditional 비유의 = 자동차 momentum 무효 prior 와 일치 | **채택(약/비유의)**: conditional 발현 측정이 본체(반도체처럼 KRW_weak interaction 검정 의무) |
| PBR 24M -0.463 t=-17.6 BY생존 | ★t=-17.6 = §M.12 직접 지목 사례 = eff_indep≈2.5 × universe 14종 이중 inflation. Damodaran/메리츠 = PBR robust 지지하나 magnitude 과대 | **부호 채택 / magnitude 격하**: 3M/6M/12M(eff_N 큼) 재배치, breadth-adj IR hedge |
| PER 무효 (IC≈0, peak-EPS trap) | Damodaran cyclical + 자동차 = peak-EPS trap **대표산업**. 이론·측정 정합 | **채택**: cyclical 정의 입증, E/P·EV-EBITDA 대체 권고 |
| customer momentum REJECTED (CARZ lag0 +0.22 유의, forward 부재) | GS Autos = 글로벌 자동차 수요 동조. forward null 정합(동조>예측) | **REJECTED 확정**: 동조성분 RegimeGlasso 흡수 |
| dollar β -0.084 비유의 (수출 가설 약) | ★unconditional 비유의 ≠ conditional. 자동차 환율 희석(해외생산·헤징) = 반도체보다 약 prior 정합. KRW regime 자체축 → KRW_weak 증폭 재검 의무 | **재검 후 conditional 측정**: unconditional 기각 성급, family_2 검정 |
| common factor 전부 비유의 (credit/oil 약 음) | 자동차 idiosyncratic = 반도체 credit 강과 대조. 단 unconditional only | **tentative 유지**: regime conditional 미측정 |

### §5.1 ★자동차 vs 반도체 cyclical 대조 (archetype 판별)

- 두 산업 모두 cyclical(PBR○ PER✗) 이나 **momentum 부호 강도 차이**: 반도체 = 음 reversal robust(ASP cycle 급락) / 자동차 = 음 reversal **약/비유의**(volume cycle 점진) = **같은 cyclical 도 cycle 원천(가격 vs 판매량)이 momentum 부호 강도를 가른다**는 가설.
- battery(양 momentum CONFIRMED, growth) / 반도체(음 reversal PARTIAL) / 자동차(음 reversal 비유의) = 3산업 momentum spectrum. 자동차는 cyclical 이지만 가격신호 가장 약 → **valuation·conditional 이 진짜 신호**일 prior.

## §6. ★추가 메커니즘·지표 발굴 (candidate-ledger 이연 등록, 부호 사전확약 + 학술 ground)

| 신규 지표 | 메커니즘 | 부호 사전확약 | 데이터 소스 | 학술 ground |
|---|---|---|---|---|
| **재고순환** (재고/총자산, 재고 yoy) | 완성차/부품 재고 peak→주가 bottom(업황바닥), 재고 bottom→peak(과잉우려). ★자동차 = 딜러재고 직접지표 부재, DART 기업재고 proxy | **음(-)**: 高재고→forward 양 | DART 재고자산(분기 재구성) | Chen-Novy-Marx-Zhang 2010, GS Autos 재고 |
| **CAPEX/총자산** (asset growth) | 전동화 과잉 capex→공급과잉→이익훼손 | **음(-)**: 高capex→forward 약 | DART 유형자산 yoy | Cooper-Gulen-Schill 2008 |
| **R&D/총자산** (무형자산) | 전동화·SDV 기술투자(미래경쟁력) | **양(+)**: 高R&D→forward 강 | DART 무형자산 | e-KJFS growth factor |
| **미국 SAAR yoy** | 미국 신차수요 선행 = 현대/기아 핵심시장 | **양(+)** (산업 timing, regime변수) | FRED TOTALSA(미국 차판매 SAAR) | GS Autos 2023 |
| **EV/EBITDA** (cyclical primary) | PER trap 회피 cash-flow value | 음(-) (저EV/EBITDA→양) | DART 부채/현금 + EBITDA | Damodaran cyclical |
| **종목레벨 외국인 flow** | 시장 regime(베타)과 별개 종목선별 알파 | **양(+)** forward 1-3M | KRX 종목별(차단)→대안 | Grinblatt-Keloharju 2000 |

- ★발굴 핵심: 재고/CAPEX/R&D = 자동차 내재 cycle(공급·전동화) 신규 후보, 가격·valuation 직교 가능. DART 재구성 가능 = 측정 가능 = **이연 금지(지금 측정)**.
- ★미국 SAAR(FRED TOTALSA) = 자동차 고유 timing 변수 = regime conditioning 또는 별 측정 후보(종목 cs 아님). 반도체 PPI 자리에 자동차는 SAAR.
- 본 S2 측정 = 가격(mom/rev/vol) + valuation(PBR/PER) + flow regime + DART cycle(재고/CAPEX/R&D). EV-EBITDA·SAAR·종목레벨 flow = candidate-ledger(후속/data-gate).
