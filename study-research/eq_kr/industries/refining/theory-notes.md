---
tags: [type/theory-notes, domain/equity, sector/refining, scope/equity-kr]
date: 2026-06-05
purpose: S1 학술 ground — 정유 cycle 이론·증권사 in-depth 정독 → 메커니즘·부호 사전확약(HARKing 방지). 결론·목표가는 증거 아님, 메커니즘·가설만 추출.
sources: Gemini Pro 리서치(2026-06-05, /tmp/refining-result1.txt) + frame v3 §M.11~M.12 + auto/semiconductor theory-notes 미러 + dispatch capex 인계
---

# refining(정유) 산업 이론·메커니즘 정리

> ★**HARKing 방지**: 본 부호 사전확약은 정유 cycle **이론으로 독립 수립**(Gemini 리서치 + 학술 ref) 후 측정과 대조한다. ★측정 前 동결점 = 본 §1. conditional/시계열 IC 측정은 이 동결 후 실행.
> ★★**CRITICAL data-gate (측정 前 박제)**: 정유 코어("석유 정제품 제조업") = 5종, 시총3000억∧ADV30억 floor 통과 = **2종(SK이노096770 / S-Oil010950)뿐**. → **cross-sectional Spearman IC(min 8종) 측정 ⛔불가**. 본 산업 = frame §0 미션("어떤 지표가 forward return 예측")을 **종목 횡단면 대신 산업 시계열(frame M2)** 로 답한다. 종목선택(L3 cross-sectional)은 INSUFFICIENT 정직 박제.

## §0. 핵심 산업 특성 (cyclical archetype — spread/oil-driven, 반도체·자동차와 cycle 원천 다름)

정유(석유 정제)는 **경기민감 cyclical** 산업. ★cycle 원천:
- **반도체** = ASP(메모리 가격) cycle → 강한 reversal.
- **자동차** = Volume(판매량) cycle → 점진적.
- **정유** = ★**정제마진(crack spread) + 유가 cycle** — 원유(투입)와 제품(휘발유/디젤, 산출)의 **spread**가 마진을 결정. 유가 자체는 재고평가손익(holding gain/loss)을 통해 단기 이익에 직접 충격. = **spread-driven + 원자재 가격 노출** cyclical.

한국 정유 = SK이노베이션(096770) + S-Oil(010950)이 floor-pass universe 전부(시총 ~3조/1.3조). 수출 비중 50%+ → **싱가포르 복합정제마진(GRM)** 이 실적 바로미터. 원유 100% 수입(주력 = 두바이유), 도입~판매 1~2개월 lag = 재고손익 변동성 극대. ★universe 2종 = small breadth 최악 → 점추정 금지, 방향+권역만, n<30 hedge 강화.

★**archetype = cyclical (spread_driven 성격 강)**: archetype.py cyclical 'primary=P/B, trap=peak-EPS' 적용 (자동차와 동형 = 자산기반 valuation). 단 정유는 spread/원자재 노출이 valuation보다 단기 주가 driver.

## §1. 메커니즘별 부호 사전확약 (★측정 前 이론 동결)

### M1. 정제마진(crack spread) → forward 양(+) prior

- **메커니즘**: crack spread = 제품가(휘발유/디젤) − 원유가 = 정유사 매출총이익 직결 → 영업현금흐름 핵심 변수 → DCF 상 기업가치 선행 반영. crack 확대 = 분기 실적 개선 기대 → 주가 선반영.
- **부호 사전확약**: 정제마진(level/Δ)↑ → 정유주 forward **양(+)**. ★단 효율적 시장이면 spot crack 은 이미 동시 반영 → forward 예측력 약 가능(동시 동조가 본질, frame §D falsifier 대상).
- **출처**: Damodaran "Investment Valuation" 산업분석/DCF 기본원리 (정제마진=gross profit driver). 한국 = 싱가포르 GRM 표준(증권사 실무, 수출 50%+).
- **반증조건(falsifier)**: crack spread forward IC ≤ 0 + contemp 도 비유의 → 정제마진 무신호 / contemp 만 유의 + forward 0 → "동조성분(risk-monitor)" 격하(alpha 아님).
- ★**데이터 한계**: 싱가포르 GRM 무료 부재 → **US Gulf Coast crack(gasoline/diesel − Brent) proxy** 사용(글로벌 정제마진 동조 prior, 단 proxy 한계 = magnitude hedge).

### M2. 유가(Brent/Dubai) → ★동시 양(+) / 예측 음(-) (재고평가이익 + commodity mean-reversion)

- **메커니즘 (★2-leg)**:
  - **동시(contemporaneous) 양(+)**: 유가 급등 시 1~2개월 전 싸게 산 원유 재고가치 상승 → 재고평가이익(inventory/holding gain) → 단기 주가 강세. 비영업적·일시적(지속성 낮음).
  - **예측(forward) 음(-)**: 역사적 고유가($100+) = peak-out 신호 → (1) 유가 하락 시 대규모 재고평가손실 위험 (2) 글로벌 경기둔화·수요파괴(demand destruction). 시장이 peak 인식 → forward 약. commodity 가격 장기 평균회귀.
- **부호 사전확약**: 유가 동시 = **양(+)** / 유가 level forward = **음(-)** (mean-reversion). ★동시·예측 부호 반대 = §1.8-4 rebound 패턴 (정상 메커니즘, artifact 아님 — 이론적으로 분리됨).
- **출처**: Deaton & Laroque (1992) "On the behaviour of commodity prices" RES (commodity mean-reversion) / 재고평가손익 = 회계원칙(평균법) 실무. 한국 두바이유 1~2M lag.
- **반증조건**: 유가 동시 IC ≤ 0 → 재고평가이익 가설 기각 / 유가 forward IC ≥ 0 → mean-reversion 가설 기각 / ★Δ유가(차분)도 forward 음 유의해야 진짜 (level만 음 = spurious 의심, §1.7 ADF 점검 의무).

### M3. 정유 가동률(refinery utilization) → forward 양(+) prior

- **메커니즘**: 가동률↑ = 전방수요 강·수급 타이트 → 가격결정력↑ + 고정비 분산 → 수익성. 영업레버리지 高(Lev 1974) = 호황기 이익 극대.
- **부호 사전확약**: 가동률↑ → 정유주 forward **양(+)**.
- **출처**: Lev (1974) "Operating Leverage and Risk" JFQA. 한국 = 고도화설비(HOU) 경쟁력 + 아시아 역내 가동률 선행지표.
- **반증조건**: 가동률 IC ≤ 0 또는 OOS flip → 무신호. ★데이터 = US 석유·석탄제품 IP(IPG32411S) proxy (한국 가동률 무료 부재, proxy 한계).

### M4. ★capex / asset growth (dispatch ★★최우선) — cross-sectional 음(-) 이론 / 정유 측정불가

- **메커니즘**: asset growth anomaly(Cooper-Gulen-Schill 2008) = 총자산/유형자산 증가율 高 종목 → forward 수익 저조(과잉투자·비효율 자본배분). 정유 = **초자산집약 장치산업**(capex_ratio 0.42~0.55 실측 = 자동차 0.2~0.3의 2배). 호황기 동시다발 증설(RFCC/HOU) → 2~3년 후 공급과잉 → 정제마진 급락 = ★정유 CAPEX 사이클.
- **부호 사전확약 (cross-sectional)**: capex_ratio(유형자산/총자산) 상위 종목 → forward **음(-)** (과잉투자의 저주). = 자동차 capex_ratio(OOS robust 음) 일반화 가설.
- **출처**: **Cooper, Gulen & Schill (2008) "Asset growth and the cross-section of stock returns" JF**. 한국 2010s 초 정유 동시증설 → 공급과잉 마진약세 실증.
- ★★**측정 결론 (data-gate)**: cross-sectional capex IC = **INSUFFICIENT** — 정유 코어 strict 2종, 횡단면(min 8종) ⛔불가. dispatch 음 prior 일반화는 **정유선 검증 불능**(측정 자체 불가). 시계열 capex level forward 양(+) 발견됐으나 ★spurious(ADF I(1) + 유가국면 proxy collinear ρ=-0.44 + Δ약화) → REJECTED. = capex 함정 회피(§1.8 spurious).
- **반증조건**: (cross-sectional 측정 가능해질 시) capex IC ≥ 0 유의 → asset growth anomaly 기각.

### M5. valuation: PBR(음, 작동) vs PER(무효, peak-EPS trap) — cyclical 동형

- **메커니즘**:
  - PER trap: 정유 = peak-earnings trap **전형**. 사이클 정점 정제마진·EPS 극대 → 저PER 착시 → 매수 → 마진 하강 EPS 급감 → 함정. 2016-17 호황 PER 4~5배 → 이후 장기 하락(실무 실증).
  - PBR robust: 정유 = 대규모 유형자산(정제설비) → BPS 안정 → PBR 밴드 하단 = 사이클 바닥 판단. 실무 = PBR 밴드 차트가 핵심 valuation 도구.
- **부호 사전확약**: 저PBR → forward 양 = **IC 음(-)** (value premium). 저PER = peak-EPS trap → 무효/불일관 prior.
- **출처**: Fama-French (1992) JF (value premium) / Damodaran cyclical valuation (peak-earnings). 한국 정유 PBR 밴드 실무.
- ★**측정 결론 (data-gate)**: cross-sectional PBR/PER IC = **INSUFFICIENT**(2종). 시계열 valuation(정유2종 평균 PBR cycle 위치 신호)은 측정 시도 → 박제.
- **반증조건**: (측정 가능 시) PBR IC ≥ 0 → value premium 기각 / PER IC 유의 음 → peak-EPS trap 기각.

## §2. 측정 설계 (data-gate 대응 = 시계열 우선)

| # | 측정 | 방법 | 가능성 |
|---|---|---|---|
| 1 | crack spread / 유가 / 가동률 → 정유 forward | 산업 패널(2종 동일가중) 시계열 lag-corr (frame M2) + regime conditional | ✅ 측정 (시계열) |
| 2 | 유가 동시 vs 예측 부호 대조 | contemp vs forward (frame §D falsifier, §1.8-4) | ✅ |
| 3 | capex cross-sectional 음 anomaly | 횡단면 IC | ❌ INSUFFICIENT (2종) |
| 4 | PBR/PER cross-sectional value | 횡단면 IC | ❌ INSUFFICIENT (2종) |
| 5 | walk-forward OOS + leave-episode + ADF | IS19-22/OOS23-26 + 2020/2022 제외 + 단위근(§1.7) | ✅ (시계열 robustness) |

## §3. 부호 사전확약 요약표 (측정 前 동결 = HARKing 방지)

| 신호 | 측정 unit | prior 부호 | 근거 |
|---|---|---|---|
| crack spread (정제마진) | 시계열 forward | 양(+) 단 동조>예측 prior | Damodaran DCF, 싱가포르 GRM |
| 유가 (Brent) 동시 | 시계열 contemp | **양(+)** | 재고평가이익 |
| 유가 (Brent) level 예측 | 시계열 forward | **음(-)** mean-reversion | Deaton-Laroque 1992 |
| 가동률 (refinery IP) | 시계열 forward | 양(+) | Lev 1974 영업레버리지 |
| capex_ratio cross-sectional | 횡단면 | 음(-) — but 측정불가 | Cooper-Gulen-Schill 2008 |
| PBR cross-sectional | 횡단면 | 음(-) value — but 측정불가 | Fama-French 1992 |
| PER cross-sectional | 횡단면 | 무효 peak-EPS — but 측정불가 | Damodaran cyclical |

★FDR family = 위 7 가설 (학습 가설 수 = family 크기, 폐기분 포함). 측정 결과 본 후 family 재정의 ⛔금지.
