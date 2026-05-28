# 거시지표 ↔ 거시이벤트 상관관계 배경 자료 (indicator_event_correlation.py 의 근거)

> 이 문서는 `core/brain/indicator_event_correlation.py` 의 상관 테이블·이상케이스·조건부 약화 로직의
> **출처·근거**다. 코드의 각 데이터 구조는 아래 항목과 1:1 로 연결된다 (코드 docstring 이 본 문서를 참조).
>
> 1차 출처 = `D:/projects/Inv/macro.md` (라인 번호 표기). 2차 보강 = 공신력 거시 방법론 (하단 §출처).
> 설계 정합 = `IMPLEMENTATION_PROMPT.md` §5.8-H (레짐 오판 피드백 루프), §5.8-A (NBER lag 분리), §5.8-F (PIT).

---

## 0. 핵심 명제

전통 거시 분석은 "이벤트 → 지표가 이렇게 움직인다"는 **정상 패턴(baseline 상관)** 에 기댄다.
그런데 포스트 팬데믹은 *같은 이벤트인데 동반 지표가 평소와 다르게 움직인* 사례가 반복됐고(macro.md 결론, 라인 211),
그때마다 **그 분기를 사전·동시에 sensing 할 수 있는 보조지표**가 존재했다.

→ 우리 모델은 (a) baseline 상관을 명시하고 (b) 이상 케이스를 인코딩하며
(c) 보조지표가 임계를 넘으면 baseline 상관의 confidence 를 동적으로 낮추는 **조건부 약화** 를 구현한다.
이는 López de Prado **메타라벨링**(§5.8-H R10 정정)을 거시 레짐 레이어에 어댑트한 것이다.

---

## 1. 정상 패턴 (baseline 상관) — `EVENT_BASELINE`

거시 이벤트 발생 시 *역사적으로* 동반하는 지표 거동. 비즈니스 사이클 동학에 근거 (macro.md 라인 105~126: 선행/동행/후행 지표 체계).

| 이벤트 | 금리커브(T10Y2Y) | 신용스프레드(BAA10Y) | DXY | 원자재 | 실업률 | VIX |
|---|---|---|---|---|---|---|
| **금리인상 사이클** | flatten ↓ | 안정/축소 → | 강세 ↑ | 후반 약세 ↓ | 유지 → | 소폭↑ |
| **인플레 쇼크** | flatten ↓ | 확대 ↑ | 강세 ↑ | 강세 ↑ | 유지 → | ↑ |
| **신용경색** | 역전후 스티프닝 | 급확대 ↑↑ | 강세(flight) ↑ | 급락 ↓↓ | 상승개시 ↑ | 급등 ↑↑ |
| **경기침체 진입** | 역전후 정상화 | 확대 ↑ | 강세/고점 ↑ | 약세 ↓ | 상승 ↑ | 고수준 ↑ |

근거: Estrella-Mishkin(1998) 금리커브 침체예측 (macro.md 라인 130); Gilchrist-Zakrajšek(2012) 신용스프레드-사이클;
macro.md 라인 106~109 (2008 선행/동행/후행 정량 거동); macro.md 라인 110 (XGBoost SHAP: dlogPAYEMS 1위, YC 2위).

---

## 2. 이상 케이스 (decoupling) — `ANOMALY_CASES`

각 케이스 = (이벤트, 기대 거동, 실제 거동, **이유**, **sensing 보조지표 + FRED ID + 임계 방향**).

### 2-1. 금리커브 역전 무력화 (2022~2024)
- **기대**: 10Y-2Y 역전 → 12~18개월 내 침체 (macro.md 라인 130, 191).
- **실제**: 2년+ 최장기 역전에도 연착륙 (macro.md 라인 131, 193).
- **이유**: 연준 QE 가 장기채 **term premium** 을 인위적으로 음(-)으로 억눌러 약한 신호에도 쉽게 역전 (macro.md 라인 132~134, 194). 대차대조표 크기와 잔차 스프레드 상관 거의 완벽 (라인 134).
- **보조지표**:
  - **Near-Term Forward Spread** (NY Fed): 18개월후 3M금리 - 현재 3M금리. QE 왜곡 장기금리 대신 *연준 정책경로 기대* 직접 반영. → 이게 음(-)일 때만 진짜 침체신호. 2022-23 에 T10Y2Y 보다 늦고 얕게 음전환. (보강 출처: NY Fed, FRBSF 2018)
  - **중앙은행 대차대조표** (FRED `WALCL`): QT 진행으로 축소 → term premium 복원 → 역전 신호 정상화. macro.md 라인 135~136: 2026 bear steepening 복귀.
  - **스티프닝 종류 구분**: bull(완화기대·단기↓) vs bear(재정우려·장기↑) (macro.md 라인 214).

### 2-2. Sahm Rule 오작동 (2024)
- **기대**: 실업률 3MA - 12M최저 ≥ 0.50%p → 기계적 침체 (macro.md 라인 158, 206).
- **실제**: 2024 트리거에도 침체 모면, 역사상 첫 시그널 실패 (macro.md 라인 159, 207).
- **이유**: 해고가 아니라 **이민 노동공급 충격** — 실업률 분모(노동력) 팽창으로 기계적 상승 (macro.md 라인 160, 208). 기업 구인은 정상 가동.
- **보조지표**:
  - **구인율 / V/U 비율** (FRED `JTSJOL`/`UNEMPLOY`): 구인 유지되면 노동 타이트. V/U 1.0 이하 급락이 진짜 둔화, 2023-24 는 1.2~1.5 에서 둔화 정체. (보강 출처: CBO 2024)
  - **Michez Rule** m(t)=min(û, v̂) (macro.md 라인 169~186): 구인율 하락속도 v̂ 를 실업률 û 와 대칭 결합 → 공급충격 자동 차단. 이중임계 0.29/0.81%p. **이게 Sahm 의 직접 대체 보조지표.**

### 2-3. M2 통화량 - 인플레 디커플링 (2008 vs 2020)
- **기대**: 피셔 방정식 M·V=P·Y → M2 급증 → 인플레 (macro.md 라인 3~4).
- **실제**: 2008 QE 로 본원통화 폭증했으나 인플레 無 / 2020 은 27% M2 급증 → 40년래 최악 인플레 (macro.md 라인 6~8).
- **이유**:
  - 2008: **IOER** 도입 → 은행이 유동성을 초과준비금에 묶음 → **통화승수 붕괴 + 유통속도 급락** (macro.md 라인 6, 19).
  - 2020: 지준율 상한 폐지 + **재정 직접이전**(은행 우회) → 유통속도 방어 + 보복소비 → 인플레 (macro.md 라인 7~8, 20, 23).
- **보조지표**:
  - **초과준비금** (FRED `EXCSRESNW`/`WRESBAL`): M2 증가 대비 준비금 급등 = 돈이 은행에 갇힘 → M2-인플레 상관 약화. (보강 출처: St.Louis Fed 2014 velocity)
  - **유통속도** (FRED `M2V`): 급락이면 통화량 인플레 전이 차단.
  - **재정이전/저축률** (FRED `PSAVERT`, `TOTALSL`): 저축률 급등후 급락 + 소비신용 증가 = 실물 유입 → 인플레 점화 (macro.md 라인 23).

### 2-4. 500bp 인상에도 연착륙 (2022~2023)
- **기대**: 명목 500bp 인상 → 신용붕괴·경착륙·실업폭등 (macro.md 라인 196).
- **실제**: 완전고용·탄탄소비 유지, 연착륙 (macro.md 라인 131, 197).
- **이유**: **모기지 락인** (30년 고정 저금리 고착 → 정책금리 올려도 월상환 불변) + **자산효과**(S&P+70%, 주택+50%) + **R* 구조적 상향(2.0%+)** → 5.33% 가 사실상 약한 긴축 (macro.md 라인 139~150, 198).
- **보조지표**:
  - **가계 부채상환부담** (FRED `FODSP`, `TDSP`): 금리 인상기에도 안정 유지 = 통화정책 파급 약화. (보강 출처: Dallas Fed R-star 2023)
  - **개인저축률** (FRED `PSAVERT`): 3.6% 까지 하강하며 소비 (macro.md 라인 143).
  - **R-star 추정** (Lubik-Matthes, Holston-Laubach-Williams): 상향 시 동일 명목금리의 긴축강도 약화.

### 2-5. CPI vs Truflation 괴리 (2026)
- **기대**: 공식 CPI 가 인플레 방향타.
- **실제**: 2026.02 CPI 2.4% vs Truflation 0.7% — 공식지표가 디스인플레를 과장 은폐 (macro.md 라인 50, 72~75).
- **이유**: 공식 OER 6~12개월 시차 + 셧다운으로 BLS 수집 붕괴 (macro.md 라인 47, 49). 트루플레이션은 실시간 호가·모기지 직접산입.
- **보조지표**:
  - **Truflation YoY** (고빈도): 공식 CPI 에 안정기 10~15일, 변동성국면 40~75일 선행 (macro.md 라인 48). 1%p+ 하방괴리 = 디스인플레 조기신호.
  - **모기지 호가/Freddie Mac 금리** (선행 주거비).

### 2-6. GDP-GDI 단절 (2022 상반기)
- **기대**: 2분기 연속 실질 GDP 마이너스 = 기술적 침체 (macro.md 라인 153, 202).
- **실제**: 동기 고용 역사적 호황, GDI 정상 확장 → NBER 침체 거부 (macro.md 라인 154~156, 203).
- **이유**: 지출측 GDP 가 무역수지 역조 + 재고보정으로 과소집계 (macro.md 라인 155).
- **보조지표**: **실질 GDI** (FRED `A261RX1Q020SBEA`), GDPplus(평균). GDP<0<GDI 면 침체 단정 보류.

---

## 3. 조건부 상관 약화 로직 — `conditional_attenuation()`

"보조지표 X 가 임계를 넘으면 → baseline 상관의 confidence·가중치를 낮춘다."

각 이상 케이스에 **trigger(보조지표·임계·방향)** 와 **attenuation(0~1 곱)** 를 부여.
보조지표가 trigger 충족 시 baseline 상관 신뢰도에 attenuation 을 곱해 약화 →
regime_classifier confidence 하향 + BL τ·Ω 확대(과도 tilt 자제) + §5.8-H caution 메모리.

정량 기법 근거 (보강 출처):
- **Conditional correlation**: 보조지표 조건부 데이터만으로 상관 재계산.
- **Regime-switching (Hamilton 1989)**: 체제별 파라미터 — 보조지표가 전환확률 변수.
- **Copula (tail dependence)**: VIX>30 시 Gaussian→Student-t 전환 (위기 동반하락).
- **Meta-labeling (López de Prado 2018)**: 1차 모델(레짐신호) 적중을 2차 모델이 판단 → 보조지표를 feature 로 신호 억제·사이징. ← **§5.8-H 핵심 메커니즘.**

---

## 4. 학습 데이터로서의 사용 (PIT 철칙)

상관 모델은 *정적 사전지식* 이 아니라 **보정 레코드로 갱신되는 학습 자산**이다 (§5.8-H ②③④).

```
보정 레코드 = (as_of, regime_realtime, confidence_realtime, regime_hindsight, anomaly_signature, lag)
```

- `hindsight` 라벨 = HMM smoothed state 또는 사후 NBER/실현 (§5.8-H ②).
- **PIT 철칙**: 보정 라벨은 **학습 신호로만**, 원래 실시간 결정에 *절대 backfill 금지* (§5.8-A NBER-lag 동형, §5.8-F).
- 갱신 경로: `ingest_correction()` → anomaly_signature 가 기존 ANOMALY_CASES 와 매칭되면 빈도/lag 통계 누적,
  미매칭이면 신규 candidate 케이스 등록 (보수적 — hard 재학습 아닌 caution 빈도).
- 조회 경로: `recall_similar(regime, signature, as_of_ts)` → as_of 이전 보정만 (causal mask) → macro_reasoning 에 surface.

**정직한 한계** (§5.8-H 정직):
- 구분되는 거시 레짐 에피소드는 드뭄(2018~2026 수 건) → 보정 수십개로 hard 재학습 = 심한 과적합(PBO/H23).
- 따라서 이 루프는 "훈련된 예측기"가 아니라 **"지표가 이상하면 덜 확신하라"는 caution 메모리**.
- 단 *분류기 자체*는 FRED-MD/QD(1959+)·JM/SJM 로 긴 역사 훈련 → sparse 아님 (§5.8-A R10). 라이브 오판 학습만 caution.

---

## 출처

### 1차 (macro.md, 본 프로젝트 리서치)
- `D:/projects/Inv/macro.md` 라인 3~8(M2-인플레), 33~51(CPI/PCE/Truflation), 105~126(선행/동행/후행),
  129~150(금리커브·R*·락인), 151~186(GDP-GDI·Sahm·Michez), 211~216(통합 프레임워크).

### 2차 (공신력 거시 방법론, 직접 리서치 보강 — Gemini Pro 검색 2026-05-28)
- Estrella & Mishkin (1998), *Predicting U.S. Recessions: Financial Variables as Leading Indicators* — NY Fed yield curve FAQ: https://www.newyorkfed.org/research/capital_markets/ycfaq.html
- Gilchrist & Zakrajšek (2012), *Credit Spreads and Business Cycle Fluctuations*, AER: https://www.aeaweb.org/articles?id=10.1257/aer.102.4.1692
- FRBSF Economic Letter (2018), *The Information in the Yield Curve about Future Recessions* (near-term forward spread): https://www.frbsf.org/economic-research/publications/economic-letter/2018/august/information-in-yield-curve-about-future-recessions/
- CBO (2024), *The Demographic Outlook: 2024 to 2054* (이민 노동공급): https://www.cbo.gov/publication/59823
- St. Louis Fed (2014), *What Does Money Velocity Tell Us about Low Inflation?*: https://www.stlouisfed.org/on-the-economy/2014/september/what-does-money-velocity-tell-us-about-low-inflation-in-the-us
- Dallas Fed (2023), *Global Factors Drive R-star*: https://www.dallasfed.org/research/economics/2023/1024.aspx
- Hamilton, J.D. (1989), *A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle* (Markov regime-switching).
- López de Prado, M. (2018), *Advances in Financial Machine Learning* (meta-labeling) — MlFinLab (Hudson & Thames).
