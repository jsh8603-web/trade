---
tags: [type/direction, study/eq_us_cyclical, phase/2-1]
date: 2026-05-30
note: 2-1단계 산출 — 외부 의견 3 라운드(Gemini Pro Web + Claude Opus 4.8 Web 병렬) 수렴 결과. 이론 수집·검증 방향 + 가설 10개(우선순위 4 + 보류 6) + 결정사항 정리. ★main 검토 후 2-2 진입 허가 받기 전까진 멈춤.
---

# direction.md — eq_us_cyclical 2-1 산출

> 산출 raw: `raw/round-{1,2,3}-{gemini,claude}.md` (6개). 라운드별 누적 질문은 `raw/round-{N}-question.md`. 두 모델 응답 모두 자기완결 충실.

## 0. 합의 요약 (BLUF)
- v1 분석의 IC=+0.658은 합성 DGP/look-ahead 강한 신호. 실제 단일팩터 횡단 Rank-IC 정상 = 0.02-0.08. 라이브에서 대폭 shrink 각오 + "valuation 압도" 결론은 순환적 가능.
- 경기민감주 알파의 원천 = **Capital Cycle Theory + Asset Growth Anomaly + Credit Cycle**. peak_trap의 본질 = **스팟 P/E 멀티플의 사이클 역방향성 → Damodaran 정상화 이익으로 해결**.
- 통계 = **유효-n(Kish design effect + 횡단 동조성) 살해**. 횡단 ρ̄≈0.5에 N=40 → eff-n ≈ 2. 분기×fwd 12M overlap = MA(3) 구조 → Newey-West q≥3, Driscoll-Kraay SE 단독, Politis-Romano block bootstrap.
- regime = **2국면 검정 + 4국면 sub-overlay shrinkage (Bayesian partial pooling)** — 4슬롯 카드 보관해도 OOS power 없으면 수학적으로 자동 2국면 붕괴.
- v1 → multi-sector 확장은 ρ̄ 시변(위기 →1) + Grinold √breadth 과대계상 + TVP-VAR 또는 섹터 더미 교호항 통제 필요.

---

## ① 이론 수집 방향 — 필수 우선순위

### 최상위 (시스템 골격 결정 — 빠지면 시스템 자체가 잘못됨)
1. **Damodaran — Investment Valuation (2012) + "Ups and Downs: Valuing Cyclical and Commodity Companies" (working paper 2009)**
   - 정상화 이익(Normalized Earnings) = peak_trap 본질 해결. 스팟 P/E는 trough에 높고 peak에 낮은 역설.
   - ★중기 정상화 마진 회귀(섹터 평균 EBIT × 자체 매출) > 7-10년 평균 EPS(구조성장 잠식).
   - ★ bottom-up beta (산업 무차입 베타 → 종목 D/E relever) > 회귀 베타.
   - implied ERP (월별 vintage) > historical 5%.
2. **Edward Chancellor — "Capital Returns" (Capital Cycle Theory)**
   - "수익성→자본 유입(Capex)→공급 과잉→수익성 파괴" 명제.
   - v1 inventory/capex 음 IC = 이 이론과 정합 (peak 정점에서 과잉투자가 미래 수익률 잠식).
3. **Cooper-Gulen-Schill (2008 JF) "Asset Growth and the Cross-Section of Stock Returns" + Titman-Wei-Xie (2004 JFQA)**
   - Asset Growth Anomaly = capex/inventory 음 IC의 학술적 정본. CMA의 사촌.
   - 섹터 특수 X — Capital Cycle의 다른 표현.
4. **Gilchrist-Zakrajšek (2012 AER) "Credit Spreads and Business Cycle Fluctuations"**
   - EBP (Excess Bond Premium) = 단순 HY OAS보다 경기 선행성 훨씬 강함. 디폴트 위험 제거한 잔차.
   - 자체 산출: HY OAS(`BAMLH0A0HYM2`)를 기대디폴트율+VIX(`VIXCLS`) 직교화 (빈자판, DD 정제 부재).
5. **Grinold & Kahn — Active Portfolio Management (2000, Ch.6) + Grinold (1989, JPM) "Fundamental Law" + Clarke-de Silva-Thorley (2002, FAJ) Transfer Coefficient**
   - IR = IC × √breadth. ★ effective breadth = N/[1+(N-1)ρ̄] (Choueifaty-Coignard 2008 보완).
6. **Hamilton (1989, Econometrica) Markov-switching + Adams-MacKay (2007) BOCD**
   - 국면 식별. **predicted prob P(S_t|y_{1:t-1}) = π_{t-1}·P 가 b(t) predictable 보존**. BOCD는 break overlay만(recurring 4국면 분류 불가).

### 보완 티어
7. **Greetham-Hartnett ML Investment Clock (2004)** — 4국면 매핑 출처. **단일 휴리스틱이지 검증 모델 X — 가설 생성기로만, ground truth 금지**.
8. **Fama-French (1993, 2015) + Carhart (1997) + Asness-Frazzini-Pedersen "QMJ" (2019)** — 팩터 동물원 통제군. ★QMJ 초기 회복기 정크 랠리 → quality 상호작용 결정적.
9. **Estrella-Mishkin (1998)** 수익률곡선 침체 선행 + NBER + ISM(new orders - inventories).
10. **Novy-Marx (2011 Rev. Finance) "Operating Leverage"** — 교과서 DOL(Brealey-Myers)보다 학술 정밀. gross_margin proxy 한계 정당화.
11. **Chan-Jegadeesh-Lakonishok (1996) + Womack (1996) + Bernard-Thomas (1989) PEAD** — revision breadth 전환점 알파 근거.
12. **Damodaran Stable-Growth Cap**: `g ≤ 장기 명목 GDP (~3.5-4%)` — 영구 성장 상한.

### 후순위 (실무 휴리스틱, 검증 대상이지 전제 X)
- Sector rotation (Fidelity/Stovall 1996), Ned Davis Research, Howard Marks·Ray Dalio (영감용).

---

## ② 이론 검증 방향 — 기법 × 명제 × 함정

| 기법 | 적합 명제 | 잘못 쓰면 |
|---|---|---|
| Lead-lag Rank-IC + Block-bootstrap | 예측력(선행→t+k) | 중첩 함정. **fwd 12M = 75% 중첩 → t-stat 폭증. Newey-West q≥3 필수 + Politis-Romano 1994 stationary block bootstrap(블록≥중첩 4Q, date-block 단위 횡단 통째 리샘플) + Politis-White 2004 자동 최적블록.** ISM 발표시차 PIT 정렬 안 하면 look-ahead. |
| glasso (EBIC) 부분상관 | 조건부 의존구조 (인과 X) | 가우시안 가정 → 팻테일에 **nonparanormal(Liu-Lafferty-Wasserman 2009)/rank 기반**. 국면 조건화 유효-n 붕괴. **부분상관 ≠ 인과** — 사이클 자체가 숨은 공통원인. |
| e-process / anytime-valid | 순차검정 type-I robust | type-I 통제하나 Type-II 검정력 약함. **martingale 증분 유효 → 비중첩 윈도 필요 → n 급감**(Shafer 2021; Ramdas et al. 2023). |
| Bai-Perron / CUSUM | 구조변화 탐지 | **사후 탐지 break는 실시간 거래 불가** — 라벨 미래정보. "탐지" ≠ "예측". |
| Markov-switching / BMA | 국면 식별 | **smoothed 확률은 미래 누설 — 예측엔 filtered 아닌 predicted(1 lag)만**. label-switching 주의(평균성장률 순서제약 고정). |
| Driscoll-Kraay (1998) SE | panel HAC + 횡단의존 (★단일 최선) | **★Round 3 정정: DK 점근론 = large-T 가정**. 분기×2-3사이클 = T 작아 DK SE 자체 신뢰 불가 가능. 대응 = **월별화 + DK SE × Politis-Romano bootstrap 교차검증**. **DCC-GARCH 결합은 이중계상 → 금지**. |
| Cameron-Gelbach-Miller (2011) / Petersen 2009 / Thompson 2011 | two-way clustered SE | firm×time 클러스터 — DK 보조. |
| Pesaran CCE 공통인자 | 강한 횡단의존 | 명시적 공통 사이클 인자 추출 — multi-sector 확장 시 권장. |
| MDE + Effective-n 사전등록 | 검정력 게이트 | **40firm×36Q=1440 같지만 횡단 ρ̄≈0.5 → eff-n ≈ 1.95**. ρ̄ 시변(위기 →1). |
| Kish design effect | 횡단 보정식 | `N_eff = N/[1+(N-1)ρ̄]`. ★Choueifaty-Coignard 2008 effective breadth 정본. |
| Newey-West (1994) lag 선택 | HAC bandwidth | 4Q 중첩 → q ≥ h-1 = 3 강제. **Andrews (1991) data-dependent bandwidth 더 엄밀**. |
| Bayesian partial pooling | 계층 shrinkage | λ=τ²/(τ²+σ²/n). n=3-4·σ²↑ → λ→0 → 4국면 자동 2국면 붕괴. |
| Expanding/rolling PCA | 매크로 프록시 앙상블 | **full-sample PCA = look-ahead 100%**. expanding-window 강제. |

### 가로지르는 함정
1. **사이클이 공통팩터** → 모든 게 사이클 통해 상관. "고립된" 팩터 IC와 부분상관은 불완전 조건화 시 오염.
2. **CFNAI/매크로 vintage 깊은 개정** → ALFRED vintage 적재 절대. release-date 기준 PIT 정렬, reference-period timestamp 금지.
3. **CFNAI × HMM 이중 평활화** — CFNAI는 이미 차원축소+필터링된 지표 → HMM 입력 시 이중 평활 → 후행. 원천(M3 등)을 HMM에, CFNAI 쓸 땐 HMM 우회.
4. **fair_mult 항등식 함정**: P/E=(1-g/ROE)/(r-g)에 g=ROE·b 대입 → P/E=payout/(r-g) 동어반복 부활. g는 별도 GDP 앵커로 강제 차단.
5. **(r-g) 하한 ≥ 2% guardrail 강제** — 분모 0 근접 시 multiple 폭주.
6. **단일·고동조 섹터 모멘텀 약함 일반화 금지** — 분산 부재로 횡단 모멘텀 IC 구조적 약함.

---

## ③ 핵심 가설 초안 — 우선순위 (반증조건 명시)

### 우선순위 4 + 1 (2-3단계 즉시 검증)
| H | 이름 | 적합 통계 | 데이터 | 반증 임계 |
|---|---|---|---|---|
| **H1** | 정상화 E/P trough 최강 (★스팟 아님) | **Fama-MacBeth + DK SE**, 2국면 더미, Decile Spread 백테스트 | EDGAR 7-10년 ROE + 월말 종가 | trough에서 최상위 E/P(정상화) Excess Return이 0과 유의 X (DK t<2 또는 부호 역전), 또는 스팟 E/P가 정상화 E/P 이김 |
| **H6** | peak_trap 스팟-싼 거짓신호 (★H1과 쌍) | E/P × (quality/revision) **교호항**, 이항 로지스틱 | H1 데이터 + 2국면 라벨 | 교호항 무의미 → H1 단독 충분 / 또는 peak에서 스팟-싼 분위 OOS 수익 ≥ 비싼 분위 |
| **H4** | EBP 공통원인 — 디폴트 사이클 (★전략적 가지치기: 참이면 H3·H5 일부 파생 붕괴) | EBP를 common factor 회귀, 직교화 잔차, VAR | `BAMLH0A0HYM2` + `VIXCLS` + (자체 EBP 잔차) | EBP 로딩이 횡단 분산 설명 못 함, 또는 EBP IC < ISM IC OOS |
| **H5** | rate_beta name-specific (롱듀레이션 vs value-cyclical 부호 분리) | rolling 종목 rate-beta → 횡단 분산 검정 | FRED 금리(DGS10/실질) + 종목 수익률 | 횡단 분산이 멀티플/듀레이션 프록시로 설명 X, 또는 종목간 beta 분산이 섹터 더미로 전부 흡수 |
| **H3** | ISM 선행 — cyclical-defensive 상대수익 k=1~3M | **Granger Causality + CCF** (HY OAS·곡선 통제 후 partial IC) | FRED AMTMNO/CFNAI SOI/지역 연은 PCA | partial IC(ISM) ≤ 동시 IC, 또는 ≤ IC(HY OAS)(=credit이 ISM 흡수), hit ratio < 60% |

### 보너스 가설 (시스템 leverage 낮으나 가용성 즉시)
| H9 | CMA 섹터무관 (Asset Growth Anomaly) | FF 스타일 팩터, Decile Spread | EDGAR 자산 성장 + 가격 | 반도체 밖에서 IC ≥ 0 = 반도체 인공물 |

### 보류 (가용성 또는 power 탈락 — 2-3단계 후에 재검토)
- **H2** (val↔mom 위상교차): regime/배수 노이즈 의존, 후순위.
- **H7** (DOL EPS 증폭): EDGAR에서 고정/변동비 분해 깨끗치 않음(데이터 난도). gross_margin proxy 검증부터.
- **H8** (revision breadth 전환점): IBES 추정치가 EDGAR+FRED+ETF holdings로 즉시 적재 불가(가용성 탈락). FINNHUB 무료티어 적재 후 재진입.
- **H10** (val_gap → Δmultiple re-rating): **fair_mult를 multiple-independent하게 펀더멘털만으로 산출**해야 동어반복 회피. 산출 인프라(정상화 ROE + bottom-up beta + GDP cap g + Monte Carlo 민감도) 적재 후.

---

## ④ 핵심 결정사항 (Q1-Q5)

### Q1. Regime 분류 — 계층 정합
- **2국면(확장/수축) = testable layer**: stat test power 확보. Fama-MacBeth + DK SE 2국면 더미.
- **4국면(Reflation/Recovery/Overheat/Slowdown) = structured prior overlay**: shrinkage λ=τ²/(τ²+σ²/n)로 자동 강등. 4슬롯 보관해도 OOS power 없으면 수학적으로 2국면 붕괴.
- **카드(WeightAssumptionCard)**: delta_regime 4슬롯 유지 + **effective-DoF 필드 병기** (4국면 검증됨 거짓 확신 차단).
- **방법**: **룰베이스 BMA(주) + filtered HMM(교차검증) + BOCD(break overlay)**. HMM 핵심 = **predicted prob P(S_t|y_{1:t-1}) = π_{t-1}·P** (b(t) predictable 보존, mixture e-process supermartingale).
- **입력 3-4개 절제**: T10Y2Y + EBP/proxy + ISM proxy(SOI 또는 AMTMNO-BUSINV) + (선택) DTWEXBGS. 변수↑ = 국면당 유효관측↓.
- **검증**: Brier score + Log-predictive density + OOS lead time. ★진짜 검증 = regime-conditional 팩터 timing이 unconditional을 OOS에서 이기는가.

### Q2. Damodaran 정상화 — 동어반복 차단
- **정상화 이익 = 중기 정상화 마진 회귀** (섹터 평균 EBIT × 자체 매출), 윈도 7-10년 + NBER 침체 1회 강제 expand.
- **fair_mult = (1-g/ROE)/(r-g) 펀더멘털만**:
  - 정상화 ROE: 종목 자체 + 섹터 평균 credibility weighting `ω=n_own/(n_own+k)`. 음 ROE = **operating margin 정상화 → 자산회전율·레버리지로 ROE 재구성** (Damodaran 정석).
  - r_e: **★bottom-up beta (산업 무차입 → D/E relever) > 회귀 베타**. ERP = **Damodaran implied (월별 vintage)** > historical 5%.
  - g: **★g = min(ROE·(1-b), 장기 명목 GDP 3.5-4%)** Damodaran stable-growth cap. **GDP 앵커로 동어반복 차단**.
- **(r-g) ≥ 2% guardrail 코드 강제** (분모 폭주 방지). **Monte Carlo → fair_mult Band** (단일값 X).
- **검증**: Var(정상화 E/P)/Var(스팟 E/P) ≪ 0.5. 정상화 E/P↔regime 상관 ≈ 0 (탈사이클). 스팟 E/P는 peak에서 부호 역전(peak_trap 직접검증), 정상화는 유지.

### Q3. EBP·ISM 적재 — verified/unverified 명시
- **EBP**: FRED 클린 ticker **verify needed** (Favara/FEDS Notes 데이터부록). 자체 프록시 = `BAMLH0A0HYM2` 직교화 (기대디폴트율 + `VIXCLS`) — DD 정제 부재 열등 명시.
- **ISM 대체** (FRED 재배포 중단):
  - **AMTMNO** (Manufacturers' New Orders, Verified by Gemini, Claude unverified) — M3 advance/revised vintage ALFRED 절대.
  - **BUSINV** (Total Business Inventories) + AMTMNO = monthly NO-Inv 직접 (★ orders flow vs inventories stock 시점 불일치 보정).
  - **CFNAI SOI** (Verified) — 4 subindex 중 SOI가 ISM 선행 직결.
  - **지역 연은**: `GACDISA066MSFRBNY` Empire State 헤드라인만 verified. 하위지수 = NY Fed CSV 직접.
  - **DGORDER / NEWORDER** (Claude unverified) — 내구재 + core capex 보조.
- **PIT**: ★ ALFRED vintage + release-date 정렬. reference-period timestamp 금지.
- **앙상블**: **PCA 첫 주성분 (expanding-window 강제!)**. full-sample PCA = look-ahead 100%.
- **★CFNAI × HMM 이중 평활 위험**: CFNAI는 이미 차원축소된 지표 → HMM 입력 시 후행. 원천(M3 등) 직접 HMM, CFNAI 쓸 땐 HMM 우회.
- **최소 시계열**: 25년 (Dot-com/GFC/코로나 3사이클).

### Q4. 유효-n + 중첩 — DK 단독 + 보조 진단
- **횡단**: `N_eff = N/[1+(N-1)ρ̄]` (Kish design effect, Choueifaty-Coignard 2008). 반도체 ρ̄≈0.5 + N=40 → eff-n ≈ 1.95.
- **시계열**: AR(1) `T_eff = T(1-ρ)/(1+ρ)` 식은 **fwd 12M = MA(3) 구조에 보정 과소**. Hansen-Hodrick(1980) GMM SE 또는 lag ≥ h-1 Newey-West.
- **결합**: 곱셈 1차 근사 낙관적. ★ **Driscoll-Kraay (1998) 단일 최선**. ★Round 3 정정: DK 점근론 = large-T → **분기 데이터 + 짧은 사이클 = DK SE 자체 신뢰 불가 가능**. 대응 = **월별화로 T 확보 + DK SE × Politis-Romano stationary bootstrap 교차검증** (갈리면 T 부족 신호).
- **DCC-GARCH 결합 = 이중계상 → 금지** (학계 표준 아님, Gemini Round 3 의견 정면 반대 Claude 채택).
- **NW q**: 4Q 중첩 → q ≥ 3 강제. Andrews (1991) data-dependent bandwidth 더 엄밀.
- **Bootstrap**: Politis-Romano 1994 stationary (블록 평균 ≥ 4Q, 기하분포). Politis-White 2004 자동 최적블록. ★ 종목별 독립 리샘플 금지, **date-block 단위 횡단 통째 리샘플**.

### Q5. 가설 우선순위
- 위 ③ 참조. **H1·H6·H4·H5·H3 순서로 검증**. H4를 빨리 가지치기해 H3·H5 의존 트리 정리.

---

## ⑤ v1 분석 함정 — 정정 메모
1. **IC=+0.658**: 실데이터 불가능 (정상 0.02-0.08). 합성 DGP 직접 인코딩 또는 look-ahead 강한 신호 → 라이브 shrink 각오.
2. **val_gap ↔ multiple 동어반복**: H10 mean-reversion이 정의적 순환 → fair_mult 비순환 정의로 차단(④ Q2).
3. **단일 섹터 (반도체) + 진짜 침체 부재 (2020 = V자/정책왜곡)**: trough 샘플 실질 없음, peak_trap 극소수 에피소드 의존. **multi-sector 확장 + 25년 시계열 필수**.
4. **momentum IC=+0.054 일반화 금지**: 단일·고동조 섹터 분산 부재 효과. **multi-sector OOS 재측정 전까진 momentum 약함 결론 보류**.
5. **multi-sector 확장 함정**: 헬스케어/유틸리티는 CMA 민감도 다름 → TVP-VAR 또는 섹터 더미 교호작용 통제 필수. ρ̄ 시변(위기 →1).

---

## ⑥ 라운드별 raw 인덱스
| 라운드 | 질문 | Gemini | Claude | 핵심 발견 |
|---|---|---|---|---|
| 1 | round-1-question.md | round-1-gemini.md (5833자) | round-1-claude.md (5319자) | Damodaran/Capital Cycle/CMA/EBP, 가설 7-10개 초안 |
| 2 | round-2-question.md | round-2-gemini.md (4812자) | round-2-claude.md (5100자, 재송신) | BOCD vs HMM-predicted-prob, fair_mult 정당화 배수 비순환, AMTMNO/CFNAI SOI 검증, DK 결합 |
| 3 | round-3-question.md | round-3-gemini.md (5544자) | round-3-claude.md (5366자) | 계층 베이지안 부분 풀링, fair_mult 항등식 함정, bottom-up beta, DK 점근 large-T 자기모순, H 우선순위 4+1 |

## ⑦ 2-2 진입 전 main 결정 요청
- 본 direction.md ①②③④⑤ 채택/수정/거부.
- 우선순위 H1·H6·H4·H5·H3 외 추가/대체 권장 여부.
- EBP 자체 산출(GZ 정공법 vs 빈자판) 및 ALFRED vintage 적재의 main 측 인프라 일정.
- ⛔ 승인 전까지 2-2(이론학습 → raw/theory-notes.md) 진입 금지(STUDY-KIT §2 v2 강제).
