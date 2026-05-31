# Round 2 — eq_us_defensive 이론 검증 방법론 (Gemini Pro 자문 원문)

**일시**: 2026-05-30
**자문 채널**: Gemini Pro (gemini-search.js promo, 2nd of day)
**아카이브**: `~/.claude/docs/archive/research-raw/eq_us_defensive-round2-20260530.txt`
**프롬프트**: `C:/Users/jsh86/AppData/Local/Temp/search-r2-eq-us-defensive.md`
**응답 길이**: 10661 chars, 159 lines

---

## 핵심 권고 (R2 요약)

### ① Regime 분류 axis — 두 축 결합 (위기 유형 × HY OAS z)

**위기 유형 3 분류** (PIT regime detection):
- **(a) 신용위기 (Credit-led)**: `BAMLH0A0HYM2` z>+1.5 **AND** `UNRATE` 3M 변화 > 0.3% (★Sahm's Rule 근사)
- **(b) 외생충격 (Exogenous Shock)**: `VIXCLS` z>+2.0 **AND** `GDPC1` FRED-MD nowcast 분기성장률 급락
- **(c) 인플레이션 충격 (Inflation-led)**: `T10YIE` z>+1.5 **AND** `FEDFUNDS` 6M 변화 > 100bp

**성과 측정**:
- Cross-section: `sleeve_return - SPY_return` window [t-3M, t+3M]
- 통계 검정: **Bootstrap t-test (10,000 resampling)** — N 작아도 (3~5 이벤트/유형) robust

**Regime axis 권고**: ★`(HY OAS z, 위기 유형 dummy)` 2D tuple — 상호작용 효과 모델링. `conditional_correlation.py` 의 `regime_history` 가 2D tuple 입력 받도록 확장.

**빈틈→R3**: regime threshold (+1.5z, 0.3%) 민감도 분석.

### ② NIM lag specification — CCF + 금리 사이클 분해 → 단일 robust lag

**Lag 탐색**:
1. **CCF (Cross-Correlation Function)** 0~12M lag, `(DGS10-DGS2)` ↔ `XLF return` (또는 KBW BKX)
2. **Partial-corr scan**: `k=0~12` 별 `p.corr(XLF_ret(t), slope(t-k) | SPY(t), HY_OAS(t))`
3. **금리 사이클별 분해**: 인상기 / 동결기 / 인하기 (NBER 또는 Fed 발표 기준). 가설: 인상기 단기 lag (2-3M) / 동결·인하기 장기 lag (5-7M) — 자산·부채 리프라이싱 속도 차

**NIM Proxy**: EDGAR 상위 10 은행 분기 NIM YoY → 월별 보간 → BKX 와 동행성 검증 (corr + Granger). BKX 는 시장 기대 노이즈 있지만 고빈도 장점.

**Lag Policy 권고**: ★**단일 robust lag `k*` 고정 (예: 4M)**
- 근거: `weight_falsification.py` e-process 가 *안정적인 null* (`baseline_ic`) 가정. Adaptive lag = null 시변성 → anytime-valid 보장 어려움
- 보완: 모델 IC 악화 → e-process alarm → `update_controller` 가 "NIM lag 구조 변경 가능성" `lens.estimation_note` 생성 → 분석가 개입 트리거
- 코드 매핑: `weight_falsification.py` input feature = `slope(t-4)` 고정

**빈틈→R3**: EDGAR Y-9C 파싱 자동화 난이도. 분기→월 보간 최적 기법.

### ③ Bond proxy 시간 가변성 — 120M rolling p.corr + Bai-Perron

**측정**:
- `p.corr(XLU(t), DFII10_change(t) | SPY(t))` 의 **120M rolling** (60M 노이즈, 240M 둔감, 120M 균형)
- **Bai-Perron test** for multiple structural breaks (시각적 아닌 통계 검증)
- 식별된 break date → `regime_detection` 사전 지식 ("QE_regime", "Post_QE", "ZIRP" 등)

**Regime-conditional Ω 확인**:
- 식별된 regime → `RegimeGlasso` 입력 → 각 regime 별 Ω off-diagonal `XLU-real_rate` 부호·값 통계 유의 차이 확인

**확신/거부 flag 발생** (`update_controller`):
- 조건: `(rolling_pcorr.sign() != historical_median_sign) AND (rolling_pcorr.abs() > threshold)` 6M 연속 (hysteresis)
- Frobenius drift e-process 와 **OR-gate** 연결 → 빠른 신호

**빈틈→R3**: bond proxy 변화의 근본 원인 — rate 자체 vs 인플레 기대 vs IRA 신재생 fundamental?

### ④ Partial-corr conditioning set — `{SPY_return, HY_OAS_change}` default

**결정 기준**: ★해석가능성 (interpretability) 최우선, AIC/BIC 보조.

**Default conditioning set**: `{SPY_return, HY_OAS_change}`
- `SPY_return`: systematic risk 통제 — 필수 전제
- `HY_OAS_change`: 신용 사이클·리스크 심리 통제 — 방어/금융 모두 영향
- `WTI/DXY` 는 *대체 모델* 또는 *스트레스 시나리오* 에서만 — multicollinearity 위험

**Partial corr 식** (glasso 결과 직결):
```
Ω = Σ⁻¹
p.corr(X, Y | Z) = -Ω_xy / sqrt(Ω_xx · Ω_yy)
```
→ `conditional_correlation.py` 의 force-include whitelist 와 직접 연동.

**Whitelist 등록 절차**:
1. 가설 검증: `p.corr(real_rate, XLU) < 0` AND `p.corr(real_rate, XLF) > 0` 전체기간 + 주요 regime p<0.05
2. 검증된 ≤4 엣지만 whitelist 등록

**빈틈→R3**: 비선형 관계 (Kernel-based / Copula) 도입 검토.

### ⑤ Rank-IC 측정 design — 3M forward + 2단계 정규화

**Forward return window**: ★**3M**
- 1M: 노이즈·단기 모멘텀 오염
- 12M: 사이클 변화 둔감
- 3M: 펀더멘털 반영 최소 시간 + regime 감응 균형

**Cross-sectional 범위**: ★sleeve 전체 N=80~120 (검정력 확보), normalization 단계에서 산업 특성 반영

**2단계 정규화 (★sub-archetype 부호 반대 문제 해결 핵심)**:
- **1단계 within-industry z**: 같은 GICS industry 내 종목 z-score, KPI 부호는 이론에 맞게 조정 (은행 NIM↑ +, util 부채비율↓ +)
- **2단계 sleeve-wide rank z**: 1단계 z 를 sleeve 전체 cross-sectional rank z 변환
- 효과: "은행 중 우수 NIM" 과 "util 중 우수 부채비율" 을 동등하게 '좋은' 종목으로 평가 — 각 산업 고유 성공 방정식 존중 + 통합 랭킹

**Regime-conditional Rank-IC**:
- Primary: sleeve 전체 단일 Rank-IC 시계열 → 검정력 최대화·multiple testing 회피
- Diagnostic: e-process alarm 발생 시 `(regime × archetype)` 분해 → 실패 원인 진단 ("인플레 충격기 은행 NIM IC 붕괴" 등)

**빈틈→R3**: 다중 KPI → 단일 팩터 score 결합 (단순 평균 vs 역변동성 가중).

### ⑥ Falsification e-process baseline calibration

**baseline_ic**: 장기간 (2000-2020) IC 시계열의 **median** (mean 은 outlier 민감)
- 의미: "과거 평균 작동했던 성능이 안 나옴" null hypothesis

**sd**: ★**`0.8 × rolling_std(IC, 60M)`** (보수적, 미세 IC 하락에도 민감)

**tau (alarm threshold)**: ★**standard `1/alpha=20` 유지**
- 근거: Likelihood Ratio 명확한 통계적 해석. 40 으로 높이면 Type II error 증가, power 손실
- 보수성은 sd 에 이미 반영

**Dual-trigger OR-gate**:
- ★Ω drift secondary 적극 활용
- 근거: 방어주 sleeve 처럼 개별 팩터 효과 약하고 천천히 변하는 경우, **종목간 '관계망' 붕괴가 IC 하락 *전에* 나타나는 조기 경보**. 예: 금리 상승기 util-bank 동반 하락 (상관 급등) = 개별 IC 하락 이전 위험 신호
- Ω drift = IC e-CUSUM 의 *훌륭한 보완재*

**Regime 서브패밀리 등록**:
- e-process 자체는 *단일 sleeve-wide IC* 만 (검정력 최대화)
- 15 sub-family (3 regime × 5 archetype) 는 ★`update_controller` 진단·리포팅 단계에서만

---

## R2 자가 점검 → R3 빈틈 메우기

**R2 완수**:
- ① Regime 2D axis (위기 유형 × HY OAS z) + Sahm's Rule 근사 + Bootstrap t-test
- ② 단일 robust lag k* (예 4M) + e-process anytime-valid 보장 + BKX proxy
- ③ 120M rolling p.corr + Bai-Perron + OR-gate
- ④ `{SPY, HY_OAS}` default + glasso 정밀도 식 직결
- ⑤ 3M forward + 2단계 정규화 (★sub-archetype 부호 반대 해결)
- ⑥ baseline median + sd 0.8×rolling + tau standard + Ω drift secondary

**R3 (가설 초안 + 반증조건) 가 메워야 할 빈틈**:
1. **Regime threshold 민감도** — +1.5z 가 너무 자주 trigger / 충분히 trigger 안 함?
2. **EDGAR Y-9C 파싱 난이도** — 자체 구현 가능성·우선순위 (블록6 영향)
3. **Bond proxy 변화 근본 원인** — rate 자체 vs 인플레 기대 vs IRA capex 사이클 어느 게 주된 driver?
4. **비선형 관계** — partial-corr 의 선형 가정 한계 (특히 위기 유형 별 dispersion)
5. **다중 KPI 결합** — 본 sleeve 처럼 sub-archetype 별 핵심 KPI 다른 경우 역변동성 가중 vs 단순 평균
6. **검증할 핵심 가설 5~8개** — R1+R2 종합해 falsifiable 형태로 정리

→ R3 자문에서 위 6 빈틈 메우기 + 가설 초안 도출.

---

## R2 → 코드 매핑 summary

| 권고 | 우리 시스템 코드 매핑 |
|---|---|
| 2D regime axis | `conditional_correlation.RegimeGlasso` 입력 확장 (현재 1D regime → 2D tuple) |
| 단일 robust lag k*=4M | `weight_falsification.py` feature = `slope(t-4)` 고정 |
| OR-gate IC + Ω drift | `weight_falsification.evaluate_weight_card` PRIMARY OR SECONDARY |
| 2단계 정규화 | `core/data/weight_panel.py` 또는 신규 normalize 모듈 |
| sub-family 진단 | `update_controller.py` reporting 단계 (e-process 외부) |
| Whitelist 4 엣지 | `conditional_correlation.RegimeGlasso(corr_prior, force_include=[...])` |
| Bond proxy break detection | 신규 `core/structure/structural_break.py` Bai-Perron (or external) |

---

## 원문 reference (전문)

전문 → `~/.claude/docs/archive/research-raw/eq_us_defensive-round2-20260530.txt`
