---
name: audit-regime-conditional-20260602
description: crypto regime-conditional 측정 방법론(4게이트) + M2 긴축국면 -0.539 발견의 독립 감사. 15축(study 12 + wire 3). raw 재현 기반.
type: audit
date: 2026-06-02
auditor: opus independent subagent
target: regime-conditional-measurement-framework.md + .p2-macroliq*.py + .p2-walkforward-regime.py + .p2-regime-recheck.py
verdict: 부분 (PARTIAL) — 프레임워크 SSOT·ledger status는 충실, recheck json verdict는 over-claim
---

# 감사 보고서 — crypto regime-conditional 측정 방법론 + M2 긴축국면 발견

## §0. 재현 결과 (Provenance + Recomputation)

harness 4종을 직접 실행(`Python312` + `PYTHONUTF8=1`). **보고된 핵심 수치 전부 byte-level 재현됨**:

| 수치 | 보고값 | 재현값 | 일치 |
|---|---|---|---|
| M2 긴축국면 conditional IC | −0.539 | **−0.539** | ✓ |
| Newey-West HAC p (maxlags=12) | 0.006 | **0.006** (정확히 0.0061) | ✓ |
| eff_n | 3.4 | **3.4** (41/12) | ✓ |
| walk-forward 2-fold 부호 | 둘 다 음 | **−0.302 / −0.844** | ✓ |
| walk-forward 3-fold 부호 | 셋 다 음 | **−0.137 / −0.947 / −0.873** | ✓ |
| expanding OOS hit rate | 70% (n=30, p=0.043) | **70.0% (n=30, binom p=0.043)** | ✓ |
| M2 완화국면 IC | +0.047 비유의 | **+0.047 p=0.873** | ✓ |
| d_real BTC하락장 IC | −0.480 p=0.004 | **−0.480 p=0.004 n=34** | ✓ |

**합성 지문 검사(§0): 통과.** BTC 월봉 = Binance 실데이터, 실역사 이벤트 실재(2022-06 LUNA −47%, 2021-05 −44%, 2018 베어, 2020-12 불장 +38%). FRED M2SL/DFII10 실측(DFII10 −1.16~3.14 현실 범위). **합성 의심 없음.** 데이터는 진짜다 — 문제는 데이터가 아니라 **해석(verdict)이 표본의 한계를 넘어선 over-claim**이라는 점.

---

## §1. 핵심 판정 — M2 긴축국면 발견의 진위

> **결론: (a)진짜 robust regime alpha 아님 / (b)단일 대형 에피소드(2020-2022 COVID 유동성 supercycle) artifact 성격이 지배적 / (c)regime fishing 잔여 위험. 종합 = "(b)+(c) 우세, candidate 유지가 정당, '4게이트 통과=진짜 alpha' 라벨은 over-claim."**

### 근거 1 — within-regime 변동이 사실상 between-year 단일 swing (★가장 결정적)

긴축국면 41개월 중 **연도 내(within-year) IC가 계산 가능한 해는 2022 단 1개뿐**(IC=−0.936). 나머지 연도는 m2_yoy가 연중 거의 상수라 rank-IC가 `nan`. 즉 IC −0.539의 변동 원천은 cross-sectional이 아니라 **2020 m2_yoy 0.27(피크) → 2023 −0.04(바닥) → 2024-25 회복**이라는 거시 swing 1회. M2 12M성장이라는 느린 매크로 변수에 12M forward를 매칭하면 "유동성 슈퍼사이클이 한 번 반전했다"는 사실 하나가 41개 overlapping 표본으로 증폭된다.

### 근거 2 — eff_n=3.4

overlapping 12M forward → 독립 관측 ≈ 3.4개. p=0.006이 maxlags(0~24)에 robust하긴 하나(0.0006~0.022), **독립 표본 3~4개에서 나온 rank correlation에 "p=0.006"을 곧이곧대로 해석하면 안 됨**. small-n rigor §1.2 = n<10 단정 verdict 금지. recheck json의 "★진짜 regime alpha(fishing 아님)" 단정은 이 게이트 위반.

### 근거 3 — 2021-22 제외 시 붕괴 (단, 비단조)

직접 재측정:
- 긴축국면에서 **2021-22 제외** → IC −0.232 **p=0.407 (소멸)**
- 2022만 제외 → IC −0.423 p=0.051 (경계)
- 2020-22 전체 제외 → IC −0.582 p=0.007 (★복원)

2020-22를 빼면 오히려 살아나는 비단조 패턴 = 2023-25에 또 다른 (작은) M2-down→BTC-up swing이 있다는 뜻. block bootstrap(block=6, 5000) 95% CI=**[−0.910, −0.001]** — 0을 겨우 비껴남(frac<0=97.6%). 즉 "robust"가 아니라 "0 경계에서 흔들리는 약한 방향성"이다. detrend(선형 시간 제거) 후엔 −0.541 유지 → 순수 시간 추세 artifact는 아님(거시 swing 자체가 신호).

### 근거 4 — 문헌과의 직접 충돌 (E축)

자매 문헌 파일 `crypto-regime-dependence-papers.md` §6①은 **정확히 이 신호를 자가비판**한다:
> "2023+ subsample은 달력 컷 = ex-ante regime 아님 + 단일 상승사이클 + 유효 n 작음 → 주제5 게이트 1·2·3을 **전부 위반**. 이 상태의 −0.86을 '유효 신호'로 채택했다면 그게 오히려 in-sample regime fishing. → rejected_provisional."

Benigno-Rosa NY Fed SR1052(2017-2022 BTC macro-orthogonal)는 우리의 full-sample 비유의를 **동일 시대·동일 결론**으로 지지. 즉 동료심사 문헌은 "BTC-macro 연동은 검증 미달"쪽이고, regime-conditional −0.539는 2023+ 출현 **가능성**(산업 출처)에 불과하다. **recheck json verdict("4게이트 전부 통과 → 진짜 regime alpha")는 이 문헌 자가비판과 정면 모순.** over-claim.

---

## §2. 4게이트 spec-code match + 게이트별 판정

| 게이트 | 프레임워크 요구 | harness 구현 | 판정 |
|---|---|---|---|
| **G1 ex-ante regime** | 실시간 관측 상태변수, 달력컷 금지 | `tighten=(DFII10.diff(3)>0)` (.p2-walkforward-regime.py:20) — DFII10 일별 실질금리, 신호시점 same-day 관측가능 | **충실**. real rate 3MΔ 부호는 진짜 ex-ante. 달력컷 아님. (단, M2SL은 non-PIT revised — D축 caveat, regime 변수 자체는 깨끗) |
| **G2 multiple-testing** | regime×factor×horizon 격자 N 명시 → Bonferroni | rolling json=α/12, recheck json=α/32 | **부분/위반**. ★denominator 불일치 + 과소계상. `.p2-macroliq.py`가 regime split 이전에 이미 **7feat×3h×2sample=42 raw IC**를 같은 데이터로 탐색. true family ≈ 42+10(regime)+... → α/12는 정직하지 않음. M2 −0.539는 α/12=0.0042는 넘으나, 정직한 family(≈50+)면 α≈0.001 — p=0.006이면 **탈락 가능**. |
| **G3 walk-forward** | parameter lock + purge gap + OOS 분기 부호유지 | 2/3-fold 시간순 split + expanding one-step (lag=6) | **부분**. 부호는 OOS 유지(2023 hit 100%, 2024 71%, ex-2022 hr 79% = 2022 단독 의존 아님 = 긍정). BUT (a)**purge gap 없음** — 12M forward인데 fold 경계에 gap 0 → 인접 fold 표본 중첩 누수. (b)expanding 임계 `df.iloc[:i].median()`에 current i 미포함이라 leak은 경미하나 fold split은 purge 누락. (c)within-year IC nan = "OOS 분기 부호유지"가 cross-sectional 재현이 아니라 동일 swing 재관측. |
| **G4 Newey-West** | overlapping forward → eff_n + HAC | `cov_type=HAC, maxlags=12` (overlapping 12M에 적정 lag) | **충실(기법)** / **부분(해석)**. maxlags=12는 12M overlap에 맞음. p robust. BUT eff_n=3.4를 명시하고도 recheck json이 "p=0.006 → fishing 아님" 단정 = small-n rigor §1.2(n<10 단정금지) 위반. |

---

## §3. 15축 verdict 요약

| 축 | verdict | 근거 |
|---|---|---|
| A 이론 학습 | 충실 | crypto-regime-dependence-papers.md = 15논문 metadata 교차확인, ★미확인 표기 정직, 산업/동료심사 분리 |
| B 실데이터 검증 | **부분** | 실측 재현 ✓, 합성 아님. BUT eff_n=3.4 < t-stat>2.0 OOS 게이트 미달 → "validated alpha" 라벨 부적격, structural prior 강등 정당 |
| C yaml 도출 추적 | 충실 | ledger weight=0.0, status=candidate. 숫자 raw 재계산 일치. 가중치 박제 0 = 추적성 OK |
| D PIT/lookahead | **부분** | regime 변수(DFII10) same-day ex-ante OK. BUT M2SL **non-PIT(revised)** — caveat에 명시됐으나 forward IC에 revision bias 잔존 |
| E 자문비판+환각 | **부분(위반 1건)** | 문헌 자가비판(§6①=rejected_provisional 권고)을 recheck json이 "진짜 alpha" 로 뒤집음 = E축 cross-verify 실패. ledger는 정합(candidate) |
| F 반증+기각 | 충실 | falsifier 명시(글로벌 M2/PIT vintage/walk-forward). core_buyscore·funding·vol·basis 기각 기록 다수 |
| G effective-N | **tier 강등** | eff_n 3.4 명시됨(정직). → "validated alpha" 불가, "structural prior 저신뢰"로 자동 강등 = 의도된 동작 |
| H 미해결 의문 | 충실 | caveat에 단일사이클·regime fishing 잔여·non-PIT 솔직 기재 |
| I 생존편향 | 충실(N/A) | 단일자산(BTC) 시계열, universe 선택 없음 |
| J 경제유의·비용 | 충실(N/A) | weight=0.0, lens/prior 용도 — alpha 주장 아님, 비용 차감 불요 |
| K 다중검정 | **위반** | §2 G2 참조. 시도횟수(42+ raw IC) 미공시, Bonferroni denominator 과소(α/12) |
| L 통합행렬 | 충실(N/A) | 미배선(weight 0), 통합 차원 미진입 |
| **M wire충실** | 충실(N/A) | 코드 결선 0건(candidate, weight=0.0). off=현상태. orphan inject 0 |
| **N cross관계** | 충실(N/A) | corr_prior 미주입 |
| **O leakage** | **부분** | reject≠missing 정합(candidate 보류). BUT G3 purge gap 누락(transaction-time 인접누수) + M2 non-PIT = O축 약점 |

**hard-fail 여부**: B/C/D/I + M/N/O 코어 중 **hard-fail 0건**(B는 부분, D·O는 부분이나 무효화 수준 아님 — candidate라 차단 불요). **단 K(다중검정 시도횟수 미공시 = 조건부 hard)와 E(환각/over-claim verdict 1건)는 정정 의무.**

---

## §4. 발견된 결함 (구체)

1. **`.p2-regime-recheck-result.json:7` over-claim**: `"게이트": "G1✓G2✓G3✓G4✓ 전부통과", "verdict": "★진짜 regime alpha(fishing 아님)"`. → 문헌 §6①(rejected_provisional 권고)·eff_n=3.4·within-year nan·G2 denominator 과소와 모순. small-n rigor §2 단정어휘("진짜") 금지 대상. **정정: "candidate(walk-forward 부호 유지 but eff_n=3.4·단일 supercycle 지배·G2 family 과소계상 → fishing 잔여)".**

2. **G2 Bonferroni denominator 과소계상**: rolling json α/12 / recheck json α/32 불일치 + `.p2-macroliq.py`의 선행 42 raw IC 탐색 미포함. 정직한 family ≈ 50+ → α≈0.001. M2 p=0.006이면 보정 후 **탈락 가능**.

3. **G3 purge gap 부재** (`.p2-walkforward-regime.py:51-58`): 12M forward인데 fold 경계 gap=0 → 인접 fold forward 윈도우 중첩 누수. O축 약점.

4. **within-regime 변동 부재**: 긴축 41개월 중 연도 내 IC 계산가능 = 2022 1개뿐. "regime-conditional cross-sectional alpha"가 아니라 "거시 swing 1회의 overlapping 증폭". 프레임워크/json 어디에도 미명시.

5. **M2SL non-PIT**: caveat엔 있으나 forward IC 산출에 revision bias 잔존(D/O축).

---

## §5. 시스템 정합 (§4)

ledger status = `candidate`, weight=0.0, 코드 결선 0건. **현 상태가 정합적** — over-claim은 json verdict 텍스트에만 있고 실제 배선/가중치엔 전파 안 됨(C·M축 보호 작동). 별도 업그레이드 불요. **승격 게이트(adopted)는 정당하게 막혀 있음**: 프레임워크가 요구한 walk-forward OOS는 형식상 했으나 (a)purge gap (b)정직한 G2 family (c)eff_n 한계로 "validated alpha" 미달 → structural prior(저신뢰) 라벨이 맞다.

---

## §6. 최종 판정

**verdict: 부분(PARTIAL).**

- **프레임워크 SSOT(regime-conditional-measurement-framework.md)**: 충실. 4게이트 설계는 문헌 ground 정합, "crypto instability=norm" 원칙 타당. 단 G2 운영(denominator)·G3 purge gap을 강화해야.
- **ledger(coin_global_liquidity_m2 / coin_real_rate)**: 충실. candidate·weight 0.0·caveat·승격조건(walk-forward OOS) 정직.
- **`.p2-regime-recheck-result.json` verdict**: **over-claim(정정 의무)**. "4게이트 전부통과·진짜 alpha·fishing 아님"은 (a)eff_n 3.4 (b)within-year 변동 부재 (c)G2 family 과소 (d)문헌 자가비판 모순으로 지지 안 됨.

**M2 긴축국면 −0.539 진위 = (b) 2020-2022 COVID 유동성 supercycle 단일 에피소드 artifact가 지배 + (c) regime fishing 잔여**. (a) 진짜 robust regime alpha 아님. walk-forward 부호유지(2022 단독 의존 아님)는 약한 긍정 신호지만, eff_n=3.4·within-year nan·문헌 비판을 이기지 못함. **candidate 유지가 정답이고, recheck json의 승격성 verdict 텍스트만 candidate 수준으로 격하 정정하면 됨.**
