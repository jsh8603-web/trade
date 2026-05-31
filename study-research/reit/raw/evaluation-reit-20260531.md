---
tags: [type/evaluation, study_id/reit, phase/r4-carry-audit, status/done]
date: 2026-05-31
auditor: opus 1m independent audit subagent (self-audit 신뢰 X — raw 재실행 + 실데이터 재현)
target: study-research/reit/raw/r4-carry-verify.md (R4 carry 5건 verdict)
ssot: AUDIT-GUIDE.md §1/§2 12축 + reit/evaluation-axes.md
recompute_scripts: r4_carry_verify.py 재실행 + audit_spurious_check.py (신규 독립 검증) + CrossRef DOI 3건 + SEC EDGAR AMT 10-K primary
---

# REIT R4 carry — 12축 독립 감사 (opus 1m, 2026-05-31)

## ★ Overall verdict (1줄)

**충실 (PASS) — hard-fail 0건.** ★최우선 spurious 검정 결과: §5 REIT-stock integration r=0.746 은 **spurious 아님** (세션 스크립트가 이미 log-return 차분 사용, level corr 0.927 vs return corr 0.746, 양 half-split OOS·rolling 모두 양 부호 유지). 환각 2건 catch (AMT $322M / Beracha 재환각) = 독립 primary (SEC EDGAR + CrossRef DOI) 재확인 정확. small-N tier 차등 (§4 n=35 structural_low REJECT / §1·§2 event n=1 TENTATIVE / §5 structural_strong) 정직.

---

## 0. Provenance + Recomputation (§0 — 독립 재계산이 판정 근거)

세션 self-audit 불신. 다음을 직접 수행:

1. **r4_carry_verify.py 재실행** (cwd D:/projects/Inv, PYTHONUTF8=1) → `.log` 수치 **소수점 4자리까지 재현 일치** (VNQ-CPI r=-0.112 / §4 4factor / §5 full 0.746·high 0.814·low 0.518 / AMT z=1.96 / CCI z=-0.47). 합성 지문 없음 (실 fetch, 2008·2020 이벤트 포함, 결측 dropna).
2. **신규 독립 검증 스크립트** `audit_spurious_check.py` 작성·실행 (fresh yfinance VNQ/SPY/^GSPC + FRED CPI, statsmodels ADF/KPSS). → §5 spurious 검정 + 독립 ticker(SPY) cross-check + half-split OOS + rolling 36m.
3. **CrossRef DOI 3건 직접 조회** (1997·1999·Beracha 2019) → 세션 박제 metadata 일치 확인.
4. **SEC EDGAR AMT 10-K body 직접 fetch** (amt-20231231.htm) → "$322.0 million" 실재 / "$3.22 billion" 부재 / "$402.0 million" total 실재 확인.

→ 재계산 일치. C축 추적성 통과 (단, 본 R4 carry 는 yaml 미박제 단계 — §C 적용은 main verdict 후 yaml v3 시점).

---

## 1. Hard-fail 코어 4 (B / C / D / I)

| 축 | 판정 | 사유 (독립 재계산) |
|---|---|---|
| **B 실데이터 + spurious** | **PASS** (§5/§3 large-n) / PARTIAL (§4 n=35) | 합성 0. ★spurious 검정: VNQ·SPX **LEVEL** ADF p=0.93~1.0 (I(1) unit root) but 세션 §5 는 `np.log(px).diff()` = **return(차분) 사용** → return ADF p<0.0001 정상. LEVEL corr 0.927 (spurious 후보) vs **RETURN corr 0.746** = 세션값 = spurious 아님. 독립 SPY ticker 0.751 일치. OOS: 1st-half 0.748 / 2nd-half 0.787 (양 유의), rolling36m min 0.161 max 0.912 항상 양. **직전 bond_cash 함정(IC -0.74→차분 +0.033 소멸) 미발생** — 차분 후에도 0.75 유지. §3 VNQ-CPI return-corr 도 차분 기반. |
| **C yaml 추적성** | **N/A (적용 보류)** | 본 R4 carry = yaml 미박제 단계 (main verdict 후 v3). 산출 = md + py(.log) raw, 수치 재계산 path 박제 완비 (±5% 추적 가능). candidate-ledger §C 수치 = md 실측과 일치. yaml ±5% 게이트는 v3 박제 시점 검증. |
| **D PIT / lookahead** | **PARTIAL PASS** | §3 FRED CPIAUCSL = **latest-revised (first-release vintage 아님)** — 세션이 "ALFRED TODO, partial caveat" 정직 명시. §5 는 contemporaneous return 통합 corr = 거래 signal 아닌 공분산 prior → forward-looking leakage 낮음. event-study(§1/§2) = filing 후 시점 사용 (PIT-correct). lookahead 차단 OK, CPI vintage 만 미보정 잔존(caveat 명시 = 무효화 아님). |
| **I 생존편향** | **PARTIAL PASS** | VNQ = ETF basket (index methodology 로 상폐 자동 제외 → partial 생존편향, 세션 caveat 명시). AMT/CCI = 자체 filing primary, 2026 생존. 개별 상폐 REIT(office stress) 미포함 = caveat 박제됨. §5 통합 corr 은 broad ETF 단위라 개별 생존편향 영향 작음. 무효화 수준 아님. |

**Hard-fail = 0건.**

---

## 2. 보조 8축

| 축 | 판정 | 사유 |
|---|---|---|
| **A 이론 실재성** | PASS | 5 ref 저자·연도·journal·vol/issue·DOI 명시. CrossRef DOI 3건 독립 재확인 (1997·1999 정확, Beracha 2019 존재). 자문 복붙 아닌 본인 정리. |
| **E 환각 cross-verify** ★강점 | **PASS (강)** | ★2건 환각 독립 재확인: (1) SEC EDGAR primary 직접 fetch → "$322.0 million" 실재, "$3.22 billion" 부재 → factor 10x 환각 catch **정확**. (2) CrossRef DOI 10.22300/0896-5803.41.4.513 → Journal of Real Estate Research 41(4) "REIT Operational Efficiency" → "Real Estate Economics inflation hedging" 재환각 catch **정확** (journal 오기 + topic 환각 둘 다 확인). 연쇄 환각(1차 catch 후 대체 ref 가 또 환각) 차단 = E축 모범. CONFIRMED 2건(Ling-Naranjo)도 primary 6/6 재확인. |
| **F 반증 + 기각** | PASS | REJECT 3건+ 실재 (AMT magnitude / Beracha 재환각 / §4 4/4 비유의). p-hacking 아닌 정직 기각. |
| **G effective-N tier** | PASS (tier 정직) | §3 n=258 / §5 n=260 large / §4 n=35 small → structural_low 강등 정직 / §1·§2 event n=1 → INSUFFICIENT·TENTATIVE 정직. 검정력 한계 숫자 명시. |
| **H 미해결 의문** | PASS | §7 후속 R5 carry 5건 (CCI multi-year / Beracha 제거 / §4 BAA-AAA proxy n확장 / regime hook / event window 확장) 솔직 박제. |
| **J 경제적 유의성** | N/A (정성 용도) | R4 carry = ref/event verify + 공분산 prior, 거래비용·alpha 주장 없음. §5 는 integration corr(공분산 prior)지 tradable alpha 아님 → J 미적용 적정. |
| **K 다중검정** | PASS | §4 Bonferroni α/4=0.0125 → 0/4 생존 명시. 누적 m=6 (α/6=0.0083) 기준 §5 full p=3.5e-05 «« 0.0083 생존. 시도횟수 공시 OK. |
| **L 통합 PSD** | N/A (보류) | yaml 미박제 → 통합 단계 미진입. ★main 경고: §5 REIT-stock 통합 corr 을 system_priors 에 넣을 때 stock sleeve 와 **공통 equity-market 인자 중복 계상** 주의 (L축, v3 시점). |

---

## 3. ★ §5 REIT-stock integration spurious 판정 (level vs return corr)

| 항목 | 수치 (독립 재현) | 해석 |
|---|---|---|
| LEVEL 가격 정상성 | VNQ ADF p=0.93 / ^GSPC p=1.00 (KPSS 둘 다 reject) | 둘 다 **I(1) 비정상** — level corr 은 spurious 위험 |
| LEVEL price corr | r=**0.927** (NW t=6.5) | spurious 후보 (비정상 회귀) |
| RETURN(log-diff) corr | r=**0.746** (NW t=4.14, p=3.5e-05) | ★세션 §5 값 = **이미 차분 사용** |
| RETURN 정상성 | ADF p<0.0001 (정상) | 차분 후 정상 회귀 |
| 독립 ticker SPY return corr | r=0.751 | ^GSPC 값과 일치 (robust) |
| half-split OOS | 1st 0.748 / 2nd 0.787 (둘 다 유의) | OOS 부호·크기 일관 |
| rolling 36m corr | min 0.161 / max 0.912 / mean 0.700 (항상 양) | 시변하나 부호 안정 |
| high/low vol regime | 0.814 / 0.518 (둘 다 p<1.4e-04) | regime-conditional 통합 강화 실재 |

**판정: spurious 아님.** level→return 차분 시 0.927→0.746 으로 줄지만 **소멸·붕괴 없음** (bond_cash 함정처럼 0 근처로 안 떨어짐). 세션 스크립트가 처음부터 return 을 썼고, 독립 ticker·OOS·rolling 모두 양 부호 유지 → **CONFIRMED 강력 어휘 유지 정당** (단, "통합 corr = 공분산 prior" 이지 tradable alpha 아님을 라벨에 명시 권장). high_vol 0.81 > low_vol 0.52 = tail-correlation 1 수렴 정합.

---

## 4. 환각 2건 catch — E축 정확성 (독립 primary 재확인)

| catch | 세션 주장 | 독립 재확인 | 정확? |
|---|---|---|---|
| AMT goodwill | "$3.22B = factor 10x 환각, 실제 $322M" | SEC EDGAR amt-20231231.htm 직접 fetch: "goodwill impairment charge of $322.0 million as of September 30, 2023" 실재 / "$3.22 billion" 문자열 부재 / "$402.0 million" total 실재 | ★ **정확** |
| Beracha-Hardin 2019 | "재환각 — Real Estate Economics/inflation hedging 아님, 실제 JRER 41(4) Operational Efficiency" | CrossRef DOI 10.22300/0896-5803.41.4.513 → "REIT Operational Efficiency and Shareholder Value", Journal of Real Estate Research, 2019, 41(4), Beracha-Feng-Hardin | ★ **정확** (journal 오기 + topic 환각 둘 다 확인) |
| (보너스) Ling-Naranjo 1997 | "CONFIRMED primary 6/6" | DOI 10.1023/a:1007754312084 → "Economic Risk Factors and Commercial Real Estate Returns", JREFE, 1997, 14(3) | ★ 정확 |
| (보너스) Ling-Naranjo 1999 | "CONFIRMED primary 6/6" | DOI 10.1111/1540-6229.00781 → "Integration of CRE Markets and Stock Markets", Real Estate Economics, 1999, 27(3) | ★ 정확 |

환각 catch + CONFIRMED 둘 다 primary 정합. E축 = 본 study 의 핵심 강점.

---

## 5. 각 verdict tier 재판정

| # | 항목 | 세션 verdict | 감사 재판정 | tier |
|---|---|---|---|---|
| §1 | AMT goodwill 환각 catch | REJECTED (factor 10x) | **유지 — catch 정확** (SEC primary). event z=1.96 n=1 = TENTATIVE | catch=확정 / event=TENTATIVE DIRECTIONAL (n=1) |
| §2 | CCI Sprint churn | PARTIAL (magnitude OK / range·$400M TENTATIVE) | **유지.** event z=-0.47 noise = TENTATIVE | structural_low / event TENTATIVE |
| §3 | VNQ-CPI hedge | PARTIAL (weak negative r=-0.112) | **유지.** NW p=0.090 비유의, CI [-0.218,-0.010] 0 거의 접함 = **방향성 약 prior**. Beracha 재환각 catch 정확 | structural_low (weak directional, 비유의) |
| §4 | economic risk factors | REJECT (4/4 비유의, Bonferroni 0/4) | **유지.** n=35 small, 재현 일치. ref CONFIRMED / 실측 REJECT | structural_low (small-N, REJECT) |
| §5 | REIT-stock integration | CONFIRMED 강력 (regime-conditional) | **유지 — spurious 아님 확정.** return corr 0.746, OOS·독립ticker robust | structural_strong (단 tradable alpha 아닌 공분산 prior 라벨) |

**hedge 어휘 점검**: §5 "CONFIRMED 강력" 은 n=260·차분·OOS robust 근거로 small-N rigor 위반 아님 (n≥100·p<0.001·OOS 유지). §3/§4 는 "PARTIAL/REJECT weak" hedge 적정. 점추정 단독 박제 없음 (CI 동반). 단정 어휘 폭주 없음.

---

## 6. 시스템 정합 (§4) — main 책임 (참고)

- §5 regime-conditional integration corr → `system_priors.factor_implied_cross_cov` (G5) 에 high/low vol 분기로 수용 가능. ★L축: stock sleeve 와 공통 equity-market 인자 중복 계상 방지 1회 계상 필요.
- §3/§4 weak·REJECT → structural_low tier, opt-in off 박제 (validated alpha 위장 금지 — 정직히 저신뢰 prior 로 떨어짐).
- 다운그레이드 없음. 신규 업그레이드 모듈 불요 (기존 RegimeGlasso + system_priors 로 수용).

---

## 7. PARTIAL/FAIL 재dispatch 권고

- 재dispatch 불요 (hard-fail 0). 후속 R5 carry (§7.3) 로 자연 처리:
  1. §4 n=35 → BAA-AAA spread proxy (FRED, 1953+) 로 n=250+ 확장 재verify (현 REJECT 가 검정력 부족인지 진짜 null 인지 분리).
  2. §3 CPIAUCSL first-release vintage (ALFRED) PIT 보정.
  3. CCI multi-year range (10-K 2021/2022) verify.
  4. Beracha-Hardin 2019 인용 yaml 제거 (재환각) + Yobaccio 1995/Glascock-Lu-So 2002 만 anchor 유지.

---

## 부록 — 감사 재실행 산출

- `r4_carry_verify.py` 재실행 → `.log` 와 소수 4자리 일치
- `study-research/reit/raw/scripts/audit_spurious_check.py` (신규, 독립 spurious/OOS 검증)
- CrossRef DOI 3건 + SEC EDGAR AMT 10-K body 직접 fetch
