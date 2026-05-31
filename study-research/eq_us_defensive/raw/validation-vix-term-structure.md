# validation — VIX term structure (H-VIXTS)

> **worker**: eq_us_defensive merit 지표 탐구 (M6 자문 "방어주 누락 critical 지표" = VIX term structure)
> **date**: 2026-06-01
> **재현**: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python raw/validation-vix-term-structure.py`
> **metrics**: `raw/validation-metrics-vix-term-structure.json`
> **rule**: `~/.claude/rules/empirical-claim-presentation.md` §1 5의무 + `small-n-statistical-rigor.md` + AUDIT-GUIDE 12축

---

## §0. spec ↔ code 1:1 명시 (5축 매칭)

| 축 | spec | code | verify |
|---|---|---|---|
| 신호 | term ratio = VIX3M / VIX (backwardation<1 = 스트레스) | `ts['ratio_3m_vix'] = VIX3M / VIX`, own-history 252d z-score `ratio_z` | PASS |
| 시제 | (b) 동시 + 예측(forward 5d/20d) **분리** 측정 / (c) regime split=동시 분류 | contemp `y=def_excess` / fwd `shift(-1).rolling(h).sum()` / regime `ratio<1` 당일 mask | PASS — ★동시·예측 분리 명시 |
| frequency | daily | daily log-return `np.log(close).diff()` | PASS |
| transform | ratio z-score (level 비정상 risk → §1.7-B index z) | `ratio_z = rolling 252d z`. ADF level 도 I(0) 확인 (아래) | PASS |
| conditioning | 상대수익 = sleeve − SPY (벤치 차감) / regime split | `def_excess = DEF_PURE_logret − SPY_logret` | PASS |
| regime | full sample + backwardation/contango split + half-split OOS | regime mask + half-split | PASS |

**부호 prior 정합**: backwardation(ratio_z↓) → 방어주 outperform ⇒ `corr(ratio_z, def_excess)` = **음**.
실측 contemp RankIC = **-0.141** → prior 부호 생존(음 확인).

---

## §1. 데이터 coverage (rule §1.1)

| 시리즈 | source | n | 범위 | 비고 |
|---|---|---|---|---|
| VIX (30d) | FRED VIXCLS | 9196 일 | 1990-01-02 ~ 2026-05-28 | — |
| VIX3M (3m) | yfinance ^VIX3M | 4651 일 | 2007-12-03 ~ 2026-05-29 | ★binding window (term ratio 시작점) |
| VIX9D (9d) | yfinance ^VIX9D | 3874 일 | 2011-01-03 ~ 2026-05-29 | 보조 ratio |
| term ratio VIX3M/VIX | derived | **4650 일** | 2007-12-03 ~ 2026-05-28 | 분석 표본 |
| ETF (XLP/XLU/XLV/XLF/SPY) | yfinance sector_etf_close | 6642 일 | 2000-01-03 ~ 2026-05-29 | DEF_PURE eq-weight |
| (b) 패널 (ratio_z 결측 제거 후) | inner join | **~4398 일** | 2008-12 ~ 2026-05 | 252d z window 손실 반영 |

★합성 지문 검사 (AUDIT-GUIDE §0) PASS: VIX 알려진 위기 실재 — COVID 2020-03-16 **82.69** / 2008 GFC 2008-10-24 **79.13** / 2018 Volmageddon 2018-02-05 **37.32**. backwardation 478일(10.3%)이 위기 클러스터에 집중(2008/2011/2018/2020/2022) — 합성 아님.

★단위 정직 명시: VIX3M 가 2007-12~ 만 가용이라 **2008 GFC 부분만 포함**(2007-12 이후). 2008-09 Lehman 직후는 표본 내, 그 이전 펀더멘털 위기는 부재. backwardation regime n=478 일은 **소수 독립 에피소드 클러스터**(2008-10/2011-08/2015-08/2018-02/2020-03/2022)로 autocorr 강함 → Block bootstrap(block=10d) + Welch 로 보정.

---

## §2. verdict (empirical-claim §2 5단계)

### ★핵심 결론: VIX term structure = 방어주에 **동시(contemporaneous) 신호 CONFIRMED / 예측(forward) REJECTED**

| 측정 | RankIC / gap | n | NW HAC t / p | Bonferroni (m=6, α/6=0.0083) | verdict |
|---|---|---|---|---|---|
| **DEF_PURE 동시(contemp)** | **-0.141** | 4398 | t=-9.60, p<1e-5 | ★PASS | **CONFIRMED** (동시 한정) |
| DEF_PURE 예측 fwd 5d | +0.023 | 4391 | t=+0.82, p=0.41 | FAIL | **REJECTED** (부호도 반전·비유의) |
| DEF_PURE 예측 fwd 20d | -0.011 | 4376 | t=-0.23, p=0.82 | FAIL | **REJECTED** |
| FIN 동시(contemp) | +0.034 | 4398 | t=+2.39, p=0.017 | FAIL (raw only) | PARTIAL (약 양, 방어주 반대 부호) |
| FIN 예측 fwd 5d/20d | +0.021 / +0.069 | — | p=0.46 / 0.14 | FAIL | REJECTED |

**regime split (Welch, 동시 분류)**:
- DEF_PURE: backwardation +0.246%/d [+0.150, +0.328] vs contango -0.038%/d [-0.056, -0.020]. gap **+0.283%/d**, Welch t=+4.93, **p<1e-5** → 방어주는 backwardation 국면 동시 아웃퍼폼. CONFIRMED (동시).
- FIN: backwardation -0.231%/d [-0.414, -0.068] p_block=0.007 vs contango +0.005%/d (p=0.63). gap **-0.236%/d**, Welch t=-2.25, p=0.025 → 금융주는 backwardation 국면 동시 언더퍼폼 (방어주와 부호 반대 = rule §1.6 sleeve 분리 정합 재확인). raw 유의, n_bw=478 단일클러스터 의존 hedge.

### ★verdict 라벨
- **동시 채널 = CONFIRMED** (n=4398, p<1e-5, Bonferroni PASS, half-split OOS 부호 일치 -0.134/-0.150, NW HAC 보정 후 t=-9.6). 단 ★이는 **동시(mechanical co-movement)** — backwardation = 급성 변동성 스파이크 시점에 방어주가 같은 날 SPY 대비 덜 빠지는 구조(저베타 방어 특성의 거울). VIX term structure 가 방어주 상대강세를 **일으킨다**기보다 **동시 반영**한다.
- **예측 채널 = REJECTED** (fwd 5d/20d 전부 비유의, DEF/FIN 양쪽. eq_intl lead 비유의 패턴 동형). term ratio z 가 **미래** 방어주 상대수익을 예측하는 알파 = **없음**.

**종합**: `structural prior (동시 신호) — validated alpha 아님`. 동시 RankIC 강하나 forward 예측력 null → 매매 **선행 신호로는 부적격**, regime **동시 진단/risk overlay** 용도 한정.

---

## §3. 12축 audit-ready 표

| 축 | 결과 | 판정 |
|---|---|---|
| **A 이론 실재성** | VIX term structure backwardation = stress (CBOE/VIX 문헌 표준). spec 부호 prior 실측 부합 | PASS |
| **B 실데이터 시계열** | FRED VIXCLS + yfinance VIX3M/VIX9D + ETF, 합성 0. 동시 IC -0.141 t=-9.6. **단 forward OOS IC<0.03 + t<2 = 예측 채널 B 게이트 FAIL** | 동시 PASS / 예측 FAIL |
| **C yaml 추적성** | 본 md = validation 단계. yaml 박제는 main verdict 후 (worker 범위 밖) | N/A (deferred) |
| **D PIT/lookahead** | VIX/VIX3M/VIX9D = 종가, revision 없음(시장 관측치) = PIT-pure. forward 윈도우 shift(-1) 진입 = lookahead 없음. z-score = rolling past 252d (causal) | PASS |
| **E 자문 cross-verify** | M6 자문 "방어주 critical 지표" 주장 = **동시 한정 부분 확인**, 예측 알파 주장은 실측 기각. 환각 0 | PASS (자문 over-claim 부분 격하) |
| **F 반증+기각** | 반증조건 = forward IF|>0.05+p<0.10. **예측 채널 REJECTED 1건 + FIN 동시 부호 반대 = 기각 기록 존재** | PASS |
| **G effective-N** | backwardation 478일 = ~6 독립 에피소드 클러스터(2008/2011/2015/2018/2020/2022). autocorr Block bootstrap 보정. contemp n=4398 충분, regime gap 은 episode 의존 hedge | tier: 동시 validated / regime structural |
| **H 미해결** | §4 기재 | PASS |
| **I 무결성·생존편향** | ETF(XLP/XLU/XLV/XLF/SPY) = 존속 sector ETF, 상폐 없음. VIX 지수 = 생존편향 무관 | PASS |
| **J 경제적 유의성·거래비용** | 동시 신호라 **거래 alpha 검증 불가(선행 아님)** — forward null. lens/risk overlay 정성 용도 한정 (J 허용 범위) | N/A (alpha 주장 안 함) |
| **K 다중검정** | ★시도횟수 공시: 2 sleeve × 3 horizon = m=6. Bonferroni α/6=0.0083. contemp DEF_PURE 만 생존 | PASS |
| **L 통합 상관 중복** | ★ratio_z vs ΔBAA10Y(credit) corr=-0.147 (p<1e-5, 약 중복) / vs ΔDFII10(real-rate) corr~0 (중복 없음). vs VIX level corr=-0.656 (term ratio 는 vol level 과 부분 동조하나 별 정보). **credit 채널과 약 overlap — 통합 시 중복계상 주의** | 부분 overlap 경고 |

**§1.7-A ADF 사전검정**: ratio level ADF=-8.27 p<1e-5 / ratio_z ADF=-10.4 p<1e-5 / VIX level ADF=-5.53 → **전부 I(0) stationary**. level/z 회귀 spurious risk 없음. PASS.

---

## §4. 미해결 의문 (H축)

1. **동시 vs 예측 인과**: 동시 IC -0.141 강하나 forward 전부 null. backwardation = VIX 스파이크 당일이라 방어주 저베타 특성의 동시 거울일 가능성 높음 (VIX level corr=-0.66). term structure 가 **선행 정보**를 담는지 = 본 데이터로 기각(예측 REJECTED).
2. **L축 credit overlap**: ratio_z ↔ ΔBAA10Y corr=-0.147. backwardation 과 credit-widening 이 같은 stress 국면 동조 → 통합 상관행렬에서 VIX term + credit_beta 동시 베팅 시 **중복계상 risk**. main 통합 시 공통 stress factor 1회 계상 필요.
3. **regime n=478 episode 의존**: backwardation 일수가 6개 위기 클러스터에 집중. 특정 episode(예 2020-03 COVID) 제거 시 gap 약화 가능 — LOO/episode-drop robustness 미수행(daily n 크나 effective episode≈6).
4. **2007-12 이전 부재**: VIX3M binding 으로 2008 GFC 초기·dot-com 위기 표본 부재. pre-2008 backwardation 거동 미검증.

---

## §5. main 인계 (yaml 반영 제안 — worker 직접 수정 X)

- yaml `confidence_hooks` H9 VRP carry todo 와 연결: VIX term structure 는 **H9 backwardation regime** 의 실측 anchor. 단 ★verdict = "동시 CONFIRMED / 예측 REJECTED" → **선행 알파 아닌 risk-overlay/regime 진단** indicator 로 등록.
- 제안 indicator: `vix_term_structure` family=risk, transform=own_history_z(252d), lag=0, **lag_routing=contemporaneous 한정** 명시.
- 제안 relationship: `{node_a: vix_term_ratio_z, node_b: def_pure_excess, lag_routing: contemporaneous, prior_sign: neg, prior_strength: 0.14, theory_basis: "동시 RankIC -0.141 (NW t=-9.6, n=4398, Bonferroni PASS). ★예측 fwd5d/20d REJECTED. credit(ΔBAA10Y) corr=-0.147 약 overlap — 통합 중복 주의"}`.
- base_weight 보수: 예측 null 이라 선행 신호 가중 부적격. risk-regime modulator (defensive tilt during backwardation) 용도 약 가중 권고.
