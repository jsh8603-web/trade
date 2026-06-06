---
tags: [type/theory-notes, domain/inv, scope/equity-kr, sector/chemical]
date: 2026-06-05
owner: chem-analyst@kr-equity (opus 1m)
purpose: 화학(석유화학·정밀화학) cycle 이론 정독 + 가설 사전등록(부호 one-sided pre-commit). S1 산출.
note: 리서치 결론·목표가·투자의견·in-sample 백테스트 = 증거로 안 씀. 메커니즘·가설·팩터 후보만 추출 → 우리 PIT 데이터로 재검증.
---

# 화학(chemical) cycle 이론 + 가설 사전등록

> S1 = 측정 前 의무. 학술 논문 + 증권사 in-depth 정독 → 메커니즘·부호 추출. FDR family = 학습 가설 수 카운트.
> 리서치 source = Gemini Pro 종합(2026-06-05) + 학술 1차 ref(아래 §출처). 자문 결론 맹신 금지, 증거는 우리 측정.

## §0. archetype 배정 + universe

- **archetype = cyclical** (`core/structure/archetype.py` cyclical: primary_metric=P/B, value_trap=peak-EPS, cycle_drivers=capacity/spread).
  - 반도체·자동차와 동형(cyclical). 단 반도체=메모리cycle, 자동차=글로벌수요, 화학=에틸렌-납사 spread/유가/중국 cycle (driver 상이).
- **universe = 17종 명시 화이트리스트** (석유화학 commodity + 정밀/스페셜티 화학). 화장품/반도체소재/2차전지소재/정유 ⛔제외(별 archetype·별 capsule).
  - 석유화학 commodity: LG화학(051910) 롯데케미칼(011170) 한화솔루션(009830) 금호석유화학(011780) 대한유화(006650) 이수화학(005950)
  - 정밀/스페셜티: 한솔케미칼(014680) 이수스페셜티케미컬(457190) 후성(093370) OCI홀딩스(010060) OCI(456040) 롯데정밀화학(004000) TKG휴켐스(069260) 애경케미칼(161000) 유니드(014830)
  - 소재/섬유: 코오롱인더(120110) HS효성첨단소재(298050) 효성화학(298000) 국도화학(007690) 휴비스(079980) 코오롱플라스틱(138490)
  - 비료/농약: 남해화학(025860) 경농(002100)
  - ★floor-passed = 17종 (시총 1000억∧ADV 5억). small-n hedge 대상(telecom 13/auto 17 동급) — magnitude 50~70% haircut + 방향만 신뢰.
- ⚠️ **LG화학·한화솔루션 신사업 혼입 경계**: LG화학(2차전지)·한화솔루션(태양광) = 순수 화학 아닌 SOTP. 기초소재 부문은 cyclical이나 종목 forward return은 신사업 가치 영향. → factor IC 측정 시 noise. universe 유지하되 분석 시 인지.

## §1. 석유화학 cycle 메커니즘 (cyclical 본질)

```
[수요회복] 전방(자동차·건설·IT) 수요↑ → 에틸렌 수요↑ → 제품가 > 납사가 → 에틸렌-납사 spread 확대 → 이익↑ (가동률 max)
   ↓ (사이클 정점)
[과투자] spread 역사적 고점 + 가동률 ~100% → 경쟁적 대규모 증설(CAPEX, Capacity Addition) 발표. NCC 건설 3~4년 시차
   ↓ (사이클 하강)
[공급과잉] 증설 동시 완공 → 물량 쏟아짐 + 경기둔화 수요 꺾임 → 제품가 급락 → spread 축소 → 이익↓
   ↓ (사이클 저점)
[구조조정] spread → cash cost 하락 → 가동률↓/설비폐쇄 → 공급 감소 → 다음 cycle
```

- **핵심 수익성 지표 = 에틸렌-납사 spread**: 레벨보다 **모멘텀(변화율·turnaround)**이 주가 선행.
- **유가 영향 = spread 매개 (방향 모호)**: 유가↑ + 수요견조 → 전가 가능(+) / 수요둔화 → 원가부담만(-). 유가↓ → 단기 재고평가손(lagging, -) but 수요자극(+). ⇒ **유가 level 단독 부호 불명 = forward IC 약 prior**.
- **정점/저점 판별**: 정점 = spread 고점 + 경쟁증설 + peak-EPS(PER 低 함정) + 가동률 95%+. 저점 = spread cash-cost + 설비폐쇄 + PBR 역사적 저점.

## §2. ★★capex/asset growth anomaly (음, 최우선 검증 — auto 인계)

> 자동차에서 capex_ratio(유형자산/총자산)가 OOS robust + size독립(t=−3.38) + 단일FDR 생존(structural_prior_high_confidence) 확인.
> 화학 = 자산집약 장치산업(NCC 등 대형설비) → **동일 capex_ratio 신호 우선 검증**(prior 음).

- **Cooper-Gulen-Schill (2008) "Asset growth and the cross-section of stock returns" (JF)**: 자산성장률↑ → forward return↓ (강한 음). 메커니즘 = 과잉투자(overinvestment) + mispricing(시장이 투자를 초기 긍정 평가 → 초과공급 → ROIC 훼손 → 장기 하락).
- **Titman-Wei-Xie (2004) "Capital Investments and Stock Returns" (JFQA)**: abnormal capex↑ → 이후 3~5년 return↓. 대리인문제·정점 낙관론.
- **화학 적용 = 가장 잘 맞는 산업**: 정점 막대한 이익 → 대규모 증설(CAPEX↑, asset growth↑) → 2~3년후 공급과잉 → cycle 붕괴 → 장기침체. ⇒ **대규모 CAPEX 발표 = 중장기 매도 신호**.
- ★측정 지표: `capex_ratio = 유형자산(ppe)/총자산` (asset growth level, prior 음) + `ppe_yoy = 유형자산 yoy` (CAPEX cycle 변화, prior 음).
- ★검증 의무: (a) walk-forward OOS 부호 유지 (b) size 독립(시총 orthogonal — small-cap value 위장 점검) (c) 단일 FDR 생존 여부.

## §3. 중국 변수 (한국 화학 = 對중국 의존)

- **중국 자급률 상승 (구조적 음, -)**: 석탄화학(CTO)·메탄올화학(MTO)·에탄크래커(ECC) 대규모 증설 → 한국 수출물량/판가↓. 구조적 리스크. ⇒ 시계열 추세(forward IC라기보다 level shift), 측정 = regime/cycle 변수.
- **중국 PMI (선행, +)**: PMI>50 확장 → 중국 화학 수요↑ → 한국 수출(+). ★거시 regime 변수 후보(Macro regime 보강).
- **중국 화학제품 가격/수입가 (+)**: 중국=아시아 price setter. 중국 내수가↓ → 아시아 동반 하락 → 한국 수익성↓. 가격↑ → 판가↑(+).

## §4. valuation (cyclical = PBR○ PER✗)

- **PBR (primary, value premium 음 IC)**: 이익 변동성 큰데 자산(설비) 안정 → PBR = 청산가치 안정 잣대. 역사적 PBR 밴드 하단 매수. 저점 PBR 0.3~0.5배. ⇒ **저PBR(싸다) → forward 高 = IC<0** prior.
- **PER (✗ peak-EPS trap)**: 정점 EPS 최고 → PER 低 (싸 보이나 이익 꺾이기 직전). 저점 적자 → PER 무한대. ⇒ PER value premium **부호 반전/무효** prior (반도체·auto 동형 = cyclical 공통 peak-EPS).
- ★auto 결정적 입증(frame M.11): cyclical PER cross-sectional IC≈0 (peak-EPS 왜곡), PBR value premium 대체. **화학도 동일 prior 검증**.

## §5. 펀더멘털·거시 forward 지표

- **에틸렌-납사 spread 모멘텀 (+)**: spread 확대↑ → forward return↑. ★산업 cycle = 시점 공통(cross-sectional 아님) → regime/timing 변수 또는 종목 수출비중 가중. 종목 cross-sectional IC 부적합 → regime conditioning.
- **재고순환 inventory cycle (음, -)**: 재고 감소 → 수요>생산 → 가격상승 선행. `inv_ratio=재고자산/총자산` prior 음 (Chen-Novy-Marx-Zhang 2010 재고성장 anomaly). Kitchin(1923) 재고순환.
- **USDKRW 약세 (+)**: 화학 수출비중 高 → 원화약세 → 원화환산이익↑(+). Jorion(1990) FX exposure. ⇒ KRW regime conditioning.
- **외국인 순매수 (+, 선행성 의문)**: 외국인 경기민감주 수급 = turnaround 기대 반영. 단 주가상승 결과일 수도(선행성 의문). ⇒ flow regime conditioning.
- **momentum/reversal**: cyclical 정점 reversal 위험 (반도체 momentum 음 reversal). 화학도 cycle 정점 momentum 음 prior 가능 → 측정으로 판정.
- **저변동성 vol (음)**: 경기민감주 고베타 → low-vol anomaly 약할 수 있음. 측정.

## §6. ★가설 사전등록 (부호 one-sided pre-commit, 데이터 접촉 前 동결)

> ★FDR family = 본 가설 수 카운트. 측정 결과 본 후 family 재정의 ⛔금지(garden-of-forking-paths 차단).
> family 멤버십 = {신호 × horizon(y_5d/20d/60d) × powered regime cell} 전체 단일 BY-FDR alpha budget.

| # | 가설 | 신호 | 부호 prior | 근거 | 반증조건(falsifier) |
|---|---|---|---|---|---|
| H1 | ★capex 과투자 anomaly | `capex_ratio`(ppe/assets) | **음(-)** | CGS2008·TWX2004, auto 인계 | OOS 부호 반전 OR wc_p>0.10 |
| H2 | CAPEX cycle 변화 | `ppe_yoy`(유형자산 yoy) | **음(-)** | TWX2004 abnormal capex | OOS 부호 반전 |
| H3 | 재고순환 anomaly | `inv_ratio`(재고/assets) | **음(-)** | Chen-NMZ2010, Kitchin | OOS 부호 반전 |
| H4 | 재고 증가율 | `inv_yoy` | **음(-)** | 재고성장 음 | OOS 부호 반전 |
| H5 | R&D/기술 (정밀화학) | `rnd_ratio`(무형/assets) | **양(+)** | 기술경쟁력 | 비유의/반전 |
| H6 | ★PBR value premium | `pbr_z` | **음(-)** | cyclical PBR○ (저PBR→고forward) | OOS 반전 OR 비유의 |
| H7 | ★PER peak-EPS trap | `per_z` | **무효/반전**(약) | cyclical peak-EPS (auto IC≈0) | IC≈0이면 prior 확인 |
| H8 | momentum | `mom_6`,`mom_12_1` | **음(reversal)** 약 | cyclical 정점 reversal | 양이면 growth phase |
| H9 | 단기 reversal | `rev_1m` | **음(-)** | 단기 reversal | — |
| H10 | 저변동성 | `vol_60` | 불명(약) | 고베타 cyclical low-vol 약 | — |
| H11 | regime conditional: KRW약세 × 신호 | KRW_weak split | 신호 강화(수출+) | 원화약세 수익성↑ | 부호 무변화 |
| H12 | regime conditional: flow_strong_buy × 신호 | flow split | 신호 강화(수급+) | 외국인 turnaround | 부호 무변화 |

- ★H7 = "consistent with" only (auto와 동일 파이프라인 재측정 아님). cyclical peak-EPS prior 확인 용도.
- ★cross 축 (분석단위 간): 화학 ↔ (반도체·자동차 cyclical 군) 동시상관 / 화학 ↔ 유가·중국 cycle. common_factor β(oil/dollar/rate/credit) 보고 의무.
- ★family_2 interaction (G-B): family_1 부호 갈리면 ΔKRW×cs 등 interaction term 의무.

## §출처 (source URL — A축 이론 실재성)

- Cooper, Gulen, Schill (2008), "Asset Growth and the Cross-Section of Stock Returns", Journal of Finance 63(4). https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2008.01370.x
- Titman, Wei, Xie (2004), "Capital Investments and Stock Returns", JFQA 39(4). https://www.jstor.org/stable/30031881
- Chen, Novy-Marx, Zhang (2010), "An Alternative Three-Factor Model" (inventory/investment factor). SSRN.
- Kitchin (1923), "Cycles and Trends in Economic Factors", Review of Economics and Statistics.
- Jorion (1990), "The Exchange-Rate Exposure of U.S. Multinationals", Journal of Business 63(3).
- 증권사 in-depth (메커니즘 추출용, 결론 미사용): 키움 이동욱 "석유화학, 공급과잉은 맞지만"(2022-06) / 하나 윤재성 "석유화학/정유 Preview"(2023-04) / 신한 이진명 "화학/정유 산업분석"(2023-11, 중국 증설) / 교보 "화학, 바닥은 PBR이 알려준다"(2022-09).
- ★증권사 리포트 = 메커니즘·가설만 추출(목표가·투자의견·in-sample backtest 미사용). Gemini 종합(2026-06-05) cross-verify = 학술 ref 1차 확인.
