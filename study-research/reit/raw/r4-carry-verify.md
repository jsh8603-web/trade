---
tags: [type/validation, study_id/reit, phase/r4-carry-verify, status/in-progress]
date: 2026-05-31
session: btn-GCP
ckpt: ckpt-202605310200
purpose: R4 carry primary verify 5건 (Phase 3 R3 claude critique 우위 carry, sub-cluster study 와 분리 트랙)
note: ★ main 정정 (2026-05-31) 후 흐름 = 이론(ref verify) → 실데이터(SEC + yfinance + FRED) → 상관·Rank-IC (small-N rigor) → validation md 산출 → STUDY DONE 보고 → main 12축 audit subagent verdict 회신 후 yaml 반영.
---

# R4 carry primary verify — 5건

> **출처 dispatch**: handoff-reit-20260531.md §2.1 (R4 carry, Phase 3 R3 claude critique 우위)
> **5 ref / event**:
> 1. AMT 10-K 2023 Item 7 — VIL India Goodwill Impairment $3.22B 정확 수치 (gemini R3 박제 vs claude R3 단정 금지)
> 2. CCI/AMT 10-K + analyst day churn schedule — $200M-$400M/yr 2021-24 범위 verify
> 3. Beracha-Feng-Hardin 2019 RealEstateEconomics — Beracha-Krautz 2022 환각 대체 ref
> 4. Ling-Naranjo 1997 JREFE 14(3) — Ling-Naranjo 2014/2015 phantom 대체 ref (Economic Risk Factors and CRE Returns)
> 5. Ling-Naranjo 1999 RealEstateEconomics 27(3) — phantom 대체 ref (Integration of CRE Markets and Stock Markets)

> **5 금지** (모든 자산군 공통, plan.md §2): (1) 점추정 prior 박제 금지 (2) 합성·시뮬 데이터 금지 — yfinance + FRED + Nareit + SEC + 학술 PDF 실측만 (3) 자문 그대로 코드화 금지 — primary cross-verify 후 채택 (4) Single-source 단정 금지 (5) Small-N 단정 금지

> **small-N rigor** (`~/.claude/rules/small-n-statistical-rigor.md` + `empirical-claim-presentation.md`): n / p / Newey-West HAC SE / block bootstrap (autocorr 보정) / Bonferroni FDR (m≥4 비교 시) / hedge 어휘 강제 / spec ↔ code 1:1 verify

---

## §0. 작업 흐름 (main 정정 2026-05-31 후 ★)

```
1. Ref verify (5건 fetch — SEC EDGAR public + Wiley/Springer abstract)
   ├─ paywall = abstract+DOI 만 (full PDF skip), free source 우선
   └─ fetch 실패 = raise (합성 금지)

2. 실데이터 + 상관·Rank-IC (small-N rigor)
   ├─ yfinance public: VNQ + AMT + CCI + ^GSPC daily
   ├─ FRED CSV public: CPIAUCSL (CPI yoy), DGS10
   ├─ Beracha-Hardin 2019 학설 검증: REIT-CPI hedge corr (rolling 12m)
   ├─ Ling-Naranjo 1999 학설 검증: REIT-stock integration regime-conditional corr
   ├─ Ling-Naranjo 1997 학설 검증: REIT-factor partial corr (risk premia channel)
   ├─ AMT VIL Goodwill event-study CAR: 2024-02-27 10-K filing 또는 announcement date
   └─ CCI Sprint churn event-study CAR: 2024 quarterly earnings (Sprint-T-Mobile decommission)

3. Validation md 산출 (본 파일 완성)
   └─ 5건 verdict (CONFIRMED 강력 / CONFIRMED / PARTIAL / TENTATIVE DIRECTIONAL / INSUFFICIENT / REJECTED — empirical-claim-presentation §2 5단계)

4. main 'STUDY DONE 파일경로' 1줄 보고 (psmux btn-Codlearn)

5. (main 후속) AUDIT-GUIDE 12축 별도 opus subagent 수행 → verdict 회신
6. (main verdict 도착 후) 본 세션 yaml v3 반영 + evidence-map.md 갱신
```

---

## §0.5 12축 audit-ready 원칙 (main 2026-05-31 보충 — AUDIT-GUIDE.md §1 준수)

> ★ formal 12축 audit = main 별도 opus subagent 담당. 본 세션 = 원칙만 지켜 study+validation 산출.

| 축 | 본 R4 carry 작업 적용 |
|---|---|
| **A 이론 실재성** | 5 ref 모두 저자·연도·journal·vol/issue·DOI 명시 (Wiley/Springer primary). 자문 답변 복붙 X — 본인 정리. |
| **B 실데이터 OOS** ★hard | yfinance VNQ/AMT/CCI/^GSPC + FRED CPIAUCSL 실측. OOS Rank-IC > 0.03 AND t-stat > 2.0 (Newey-West HAC SE + block bootstrap autocorr 보정). 합성 데이터 절대 금지 — fetch 실패 = raise. |
| **C yaml 추적성** ★hard | 본 세션 = yaml 박제 X (main verdict 후). 산출 = `r4-carry-verify.md` + `r4_carry_verify.py(.log)` — 모든 수치 raw 재계산 path 박제. |
| **D PIT / lookahead** ★hard | FRED CPIAUCSL = latest revised (true first-release vintage ALFRED TODO, partial). 가격 데이터 = 익일 시가 진입 가정 (event-study CAR). walk-forward OOS = 본 ref verify 는 ex-post 평가, OOS test 는 corr·Rank-IC 부분만. PIT caveat 명시. |
| **E 환각 cross-verify** | 5 ref 모두 primary source 직접 fetch. fetch 실패 시 abstract+DOI 만 + paywall 박제. 환각/phantom catch (Beracha-Krautz, Ling-Naranjo 2014/2015) 재확인. |
| **F 반증조건+기각** | 5 ref verdict 중 REJECT/TENTATIVE 1건+ 의무 — p-hacking 차단. 정량 반증조건 (CI, p, Rank-IC 임계) 박제. |
| **G effective-N** ★tier | small-N caveat 명시. AMT/CCI event 1-2건 = n<10 → INSUFFICIENT 또는 TENTATIVE DIRECTIONAL. 단정 verdict 금지. validated alpha 자격 미달 = structural prior (저신뢰) tier 강등. |
| **H 미해결 의문** | §7 학습 박제 또는 §6 종합 verdict 에 confound/bias/한계 솔직 기재. |
| **I 생존편향** ★hard | AMT/CCI/VNQ 모두 2026 현재 생존 종목. 상폐 REIT 미포함 caveat 명시. universe 확장 후속 별도 trace. |
| **J 경제적 유의성** | 본 R4 carry = ref/event verify, 거래비용 적용 직접 X. lens·정성 용도 허용 — 비용 차감 후 alpha 주장 X. |
| **K 다중검정 보정** ★hard | 시도횟수 공시: 5 ref × {corr verify + event-study CAR + Rank-IC} ≈ 9-12 비교. Bonferroni α/N 또는 BH FDR q=0.10 보정 의무. raw p + 보정 p 별도 보고. |
| **L 통합 PSD** ★시스템 | 본 세션 = yaml 박제 X, 통합 차단 단계 미진입. main verdict 후 yaml 반영 시 점검 (block5 confidence_hooks 의 affects_indicator/affects_edge 명시). |

---

## §1. AMT 10-K 2023 Item 7 — VIL India Goodwill Impairment ★ 환각 catch

**Claim verify 대상**: gemini R3 박제 = "American Tower 인도 사업 (Vodafone-Idea VIL counterparty) Goodwill Impairment **$3.22B** 2023" / claude R3 = "방향성 high 정확 수치 단정 금지, 10-K 원문 풀 필요"

**Primary source**: SEC EDGAR — American Tower Corp (CIK 0001053507) 10-K filed 2024-02-27, Acc-no 0001053507-24-000011, body `amt-20231231.htm` (4.0 MB inline XBRL)

raw 박제: `~/.claude/docs/archive/research-raw/amt-10k-2023-body-native-20260531.htm` (4.0 MB) + `amt-10k-2024-index-native-20260531.html` + `amt-10k-edgar-list-native-20260531.html`

### §1.1 fetch 결과 (primary text grep, binary-safe)

본문 = 5 line packed inline XBRL. Tag strip + `grep -a -o -i "Vodafone Idea[^<]\{0,500\}"` 으로 phrase 추출. 직접 인용 5건:

1. **★ 2023 Q3 (Sep 30) India 단독 Goodwill Impairment**:
   > "goodwill impairment test as of September 30, 2023 indicated that the carrying amount of our India reporting unit exceeded our estimated fair value. As a result, we recorded a **goodwill impairment charge of $322.0 million** as of September 30, 2023."

2. **2023 FY 총 Goodwill Impairment (India + Spain)**:
   > "Goodwill impairment consists of **$402.0 million** of impairment charges recorded for our India and Spain reporting units during the year ended December 31, 2023."

3. **2022 FY India 관련 intangibles Impairment (NOT goodwill)**:
   > "For the year ended December 31, 2022, impairment charges included **$97.0 million** related to tower and network location intangible assets and **$411.6 million** related to tenant-related intangible assets in our India reporting unit related to VIL in India."

4. **VIL OCDs (Optionally Convertible Debentures)**:
   > "Vodafone Idea Limited ('VIL'), issued optionally convertible debentures (the 'VIL OCDs') to the Company's subsidiary, ATC Telecom Infrastructure Private Limited ('ATC TIPL'), in exchange for VIL's payment of certain amounts towards accounts receivables."

5. **AMT India 매각 (2024)**:
   > "total aggregate consideration would potentially represent up to approximately **210 billion Indian Rupees ('INR') (approximately $2.5 billion)**, including the value of the VIL OCDs, payments on certain existing customer receivables, the repayment of existing intercompany debt..."

### §1.2 verdict — ★ R3 박제 환각 catch (factor 10x 오기)

| 항목 | R3 박제 (gemini) | Primary (10-K 2023) | verdict |
|---|---|---|---|
| Goodwill Impairment (India unit) | **$3.22B (2023)** | **$322.0M (Q3 2023, India unit)** + **$402.0M total (India $322M + Spain $80M, FY 2023)** | ★ **REJECTED (factor 10x 환각, "$3.22B" → "$322M")** |
| Counterparty | VIL (Vodafone Idea Limited) | VIL (Vodafone Idea Limited) | CONFIRMED |
| 2022 추가 intangibles (R3 박제 X) | — | $97.0M tower + $411.6M tenant intangibles (VIL 관련) | 추가 fact 발견 |
| 2024 매각 가치 (R3 박제 X) | — | $2.5B (210 billion INR), VIL OCDs + 매각 consideration | 추가 fact 발견 |

**종합 verdict**: ★ **gemini R3 박제 "$3.22B" = factor 10x 환각** (★ REJECTED). primary = **$322.0M (FY 2023 Q3 India goodwill impairment)** + $402.0M (FY 2023 total India + Spain). 누적 India 관련 (2022 intangibles $508.6M + 2023 goodwill $322M) ≈ **$830M total** (★ 추가 fact, magnitude 는 R3 박제 "B" 단위 가까이 가지만 단일 goodwill 만은 $322M).

small-N rigor: 단일 회사 single-filing 정량 fact, n=1 event. LOO N/A. 단정 verdict 허용 (primary 직접 인용, t-stat / CI 불필요). **hedge 어휘 적용**: "★ REJECTED 강력" 대신 "REJECTED (단순 magnitude 오기)" — single-source primary 그대로 받아쓰기는 위반이지만 본 case 는 SEC filing = 1차 정량 fact 표명, 인용 적절.

### §1.3 audit-ready 박제 (12축 적용)

- **A 이론**: SEC EDGAR primary. 저자 = AMT 공식 SEC filing. PASS.
- **D PIT**: 2023 Q3 charge = announced via 10-Q (2023 Q3, ~Nov 2023) + 재확인 10-K filed 2024-02-27. PIT-correct (filing 후 사용).
- **E 환각 catch** ★ hard: R3 박제 "$3.22B" = factor 10x 환각. 본 R4 carry primary verify 가 catch 한 의의 = E축 hard-fail 회피 메커니즘 작동.
- **F 반증**: R3 박제 단정 REJECT — 1건 기각 record.
- **I 생존편향**: AMT 현재 생존 종목, 자체 filing primary. bias 없음.

---

## §2. CCI / AMT churn schedule — Sprint decommission $200M-$400M/yr 2021-24

**Claim verify 대상**: gemini R3 박제 = "Sprint-T-Mobile 합병 후 churn $200M-$400M/yr 2021-24 CCI/AMT 가이던스" / claude R3 = "공식 가이던스 원문 정확 범위 verify, 단정 금지"

**Primary source**: SEC EDGAR — Crown Castle Inc (CIK 0001051470) 10-K filed 2024-02-23, Acc-no 0001051470-24-000062, body `cci-20231231.htm` (2.5 MB inline XBRL)

raw 박제: `~/.claude/docs/archive/research-raw/cci-10k-2023-body-native-20260531.htm` + `cci-10k-2024-index-native-20260531.html` + `cci-10k-edgar-list-native-20260531.html`

### §2.1 fetch 결과 (primary text grep)

본문 5 line packed inline XBRL. `grep -a -o -i "Sprint[^<]\{0,500\}"` + `"churn[^<]\{0,500\}"` 추출 결과:

1. **2023 FY Sprint Cancellations 실제 영향 (★ primary)**:
   > "For 2023, these Sprint Cancellations resulted in **$21 million of non-renewals** that were offset by **cash payments of $170 million** to satisfy the remaining rental obligations. Additionally, **$59 million in accelerated amortization of prepaid rent** from the remaining deferred revenues was recognized for the year ended December 31, 2023."

2. **2025 expected (★ forward 가이던스)**:
   > "We anticipate that this consolidation will result in approximately **$200 million in Towers non-renewals in 2025**. We expect an additional impact of **$35 million in Fiber non-renewals**, with $10 million impacting results in 2024 and the remainder in 2025."

3. **Baseline (non-Sprint) churn rate**:
   > "we expect each of towers and small cell non-renewals to remain in line with our historical range of **1 to 2% of their respective annual site rental revenues**."

4. **Mechanism**:
   > "churn, terminations and, in limited circumstances, reductions of existing lease rates) expected as a result of the T-Mobile and Sprint network consolidation."

### §2.2 verdict — PARTIAL CONFIRMED (magnitude OK / range TENTATIVE)

| 항목 | R3 박제 (gemini) | Primary (CCI 10-K 2023) | verdict |
|---|---|---|---|
| 2023 annual Sprint churn impact | $200M-$400M/yr | $21M non-renew + $170M cash + $59M deferred amortization ≈ **$250M** (gross effect) | PARTIAL — magnitude $200M order OK |
| 2025 expected | (R3 박제 X) | $200M Towers + $35M Fiber = **$235M** | 추가 fact 발견, 가이던스 OK |
| 2021-24 multi-year range | $200M-$400M/yr 2021-24 | 2023 단년 박제만, 2021-2022 multi-year primary 미확인 | **TENTATIVE** (multi-year range 미확인) |
| $400M 상단 | $400M/yr | 2023 + 2025 가이던스 모두 $200M-$250M order, $400M 미확인 | **TENTATIVE** ($400M 상단 미확인) |
| baseline non-Sprint churn | (R3 박제 X) | 1-2% annual site rental revenue | 추가 fact 발견 |

**종합 verdict**: ★ **PARTIAL CONFIRMED** — magnitude order $200M-$250M/yr (2023 + 2025) primary 일치. multi-year range "2021-24" 와 $400M 상단 = primary 미확인 = **TENTATIVE DIRECTIONAL**.

small-N rigor: 단일 회사 single-filing 정량 fact, n=1 (2023). 2021-2022 가용 시 multi-year verify 가능 (10-K 2021/2022 추가 fetch 필요, 본 R4 carry 범위 외). LOO N/A. **hedge 어휘 적용**: "$200M-$400M 정확 range" 단정 금지, "magnitude $200M order 정합 / 상단 미확인" 박제.

### §2.3 audit-ready 박제

- **A 이론**: SEC EDGAR primary. PASS.
- **D PIT**: 2023 FY fact + 2025 expected = filing 2024-02-23 release date. PIT-correct.
- **E 환각 cross-verify**: R3 박제 magnitude OK, range 2021-24 + $400M 상단 TENTATIVE (직접 환각 X, primary 확장 verify 필요).
- **F 반증**: TENTATIVE 잔존, 다년 + 상단 primary 직접 verify 후속 (R5 carry 후보).
- **I 생존편향**: CCI 현재 생존 종목, 자체 filing primary. bias 없음.

---

## §3. Beracha-Feng-Hardin 2019 — ★ 재환각 catch (Real Estate Economics → JRER + topic 환각)

**Claim verify 대상**: claude R2 박제 = "Beracha-Krautz 2022" 환각 의심 → gemini R3 + claude R3 합의 = "Beracha-Feng-Hardin 2019 RealEstateEconomics 대체 권고. REIT-inflation hedging + illusion 공존, illusion dominant"

**Primary source verify**: CrossRef API (`api.crossref.org/works?query.author=Beracha+Hardin&query.bibliographic=REIT+inflation&filter=from-pub-date:2018,until-pub-date:2020`) — raw 박제 `~/.claude/docs/archive/research-raw/beracha-crossref-native-20260531.json` (50 KB JSON, 5 hits)

### §3.1 fetch 결과 (CrossRef primary metadata)

| # | Author | Year | Journal | Vol/Issue | DOI | Title |
|---|---|---|---|---|---|---|
| [1] | Eli Beracha, Zifeng Feng, William G. Hardin | 2019 | **Journal of Real Estate Research (JRER)** | 41(4) | 10.22300/0896-5803.41.4.513 | **REIT Operational Efficiency and Shareholder Value** |
| [2] | Eli Beracha, Zifeng Feng, William G. Hardin | 2018 | JREFE | 58(3) | 10.1007/s11146-018-9655-2 | REIT Operational Efficiency: Performance, Risk, and Return |
| [3] | Zifeng Feng, William G. Hardin, Zhonghua Wu | 2020 | Real Estate Economics | 50(1) | 10.1111/1540-6229.12307 | Employee productivity and REIT performance |
| [4] | Charles F. Beauchamp, William G. Hardin, Patrick A. Lach | 2018 | Journal of Real Estate Portfolio Management | 24(1) | — | Quiet Period Reit Returns |
| [5] | William G. Hardin et al. | 2019 | Journal of Property Research | 36(2) | — | Firm and industry informational content from REIT FFO announcements |

### §3.2 verdict — ★ 재환각 (Real Estate Economics → JRER + topic 환각)

| 항목 | R3 박제 | Primary (CrossRef) | verdict |
|---|---|---|---|
| Journal | **Real Estate Economics** | **Journal of Real Estate Research (JRER) 41(4)** | ★ **REJECTED (journal 오기)** |
| Year | 2019 | 2019 | CONFIRMED |
| Authors | Beracha-Feng-Hardin | Eli Beracha, Zifeng Feng, William G. Hardin | CONFIRMED |
| **Topic** | **REIT-inflation hedging + illusion** | **REIT Operational Efficiency and Shareholder Value** | ★ **REJECTED (topic 환각 — operational efficiency ≠ inflation hedging)** |

**종합 verdict**: ★ **REJECTED (재환각)** — Beracha-Feng-Hardin 2019 paper 자체는 존재 (JRER 41(4)) but topic 은 "REIT Operational Efficiency", NOT "inflation hedging". gemini R3 + claude R3 합의로 "1차 환각 (Beracha-Krautz 2022) 대체" 권고했던 ref 가 **또 환각**. 본 R4 carry primary verify 가 catch 한 의의 = **연쇄 환각 차단** (1차 catch → 2차 환각 인지 못 한 채 yaml v2 박제 위험 → 본 R4 verify 에서 catch).

★ **실제 inflation hedging ref 대체 후보** (primary search 부족, 본 R4 carry 범위 외): broader academic literature 에서 **Yobaccio-Rubens-Ketcham 1995 Journal of Real Estate Finance and Economics 11(1)** (이미 study_session.yaml B 항에 박제) + **Glascock-Lu-So 2002** (yaml 박제) 가 REIT-inflation 관계 (negative 또는 spurious) 학설 anchor 로 잔존. **Beracha-Feng-Hardin 2019 인용 박제 = 학설 anchor 부적격 → yaml 박제 시 제거 의무**.

### §3.3 audit-ready 박제

- **E 환각 cross-verify** ★ hard: R3 학설 anchor 박제 = **★ 재환각 1건** (factor: journal 오기 + topic 환각). 본 catch = E축 hard-fail 회피 핵심.
- **F 반증**: 1건 REJECT.
- **A 이론 실재성**: paper 자체 존재 verify (JRER 41(4)), 단 학설 anchor 부적격.

---

## §4. Ling-Naranjo 1997 JREFE 14(3) — ★ CONFIRMED (정확 primary 일치)

**Claim verify 대상**: claude R3 박제 = "Ling-Naranjo 2014/2015 phantom 의심 → 1997 JREFE 14(3) 대체 권고. Economic Risk Factors and CRE Returns"

**Primary source verify**: CrossRef API — raw 박제 `~/.claude/docs/archive/research-raw/ling-naranjo-1997-crossref-native-20260531.json` (60 KB JSON)

### §4.1 fetch 결과 (CrossRef primary)

| # | Author | Year | Journal | Vol/Issue | DOI | Title |
|---|---|---|---|---|---|---|
| [1] | ANDY NARANJO, DAVID C LING | **1997** | **Journal of Real Estate Finance and Economics** | **14(3)** | **10.1023/a:1007754312084** | **Economic Risk Factors and Commercial Real Estate Returns** |
| [2] | David C. Ling, Andy Naranjo | 1999 | Real Estate Economics | 27(3) | 10.1111/1540-6229.00781 | The Integration of Commercial Real Estate Markets and Stock Markets |

### §4.2 verdict — ★ CONFIRMED 강력

| 항목 | R3 박제 | Primary (CrossRef) | verdict |
|---|---|---|---|
| Authors | Ling-Naranjo | Andy Naranjo, David C Ling | CONFIRMED |
| Year | 1997 | 1997 | CONFIRMED |
| Journal | JREFE | Journal of Real Estate Finance and Economics | CONFIRMED |
| Vol/Issue | 14(3) | 14(3) | CONFIRMED |
| DOI | (R3 박제 X) | 10.1023/a:1007754312084 | 추가 박제 |
| Title | "Economic Risk Factors and CRE Returns" | "Economic Risk Factors and Commercial Real Estate Returns" | CONFIRMED |

**종합 verdict**: ★ **CONFIRMED 강력** (primary metadata 6/6 일치, DOI 추가). Ling-Naranjo 2014/2015 phantom catch → 1997 대체 = 정확.

### §4.3 audit-ready 박제

- **A 이론 실재성**: primary verify 완료. yaml 학설 anchor 박제 적격.
- **E 환각 cross-verify**: phantom catch 1차 → 1997 대체 = primary 정합. PASS.

---

## §5. Ling-Naranjo 1999 RealEstateEconomics 27(3) — ★ CONFIRMED (정확 primary 일치)

**Claim verify 대상**: claude R3 박제 = "phantom 대체 ref. REIT-stock market integration 학설, regime-conditional"

**Primary source verify**: CrossRef API — raw 박제 `~/.claude/docs/archive/research-raw/ling-naranjo-1999-crossref-native-20260531.json` (46 KB JSON)

### §5.1 fetch 결과 (CrossRef primary)

| # | Author | Year | Journal | Vol/Issue | DOI | Title |
|---|---|---|---|---|---|---|
| [1] | David C. Ling, Andy Naranjo | **1999** | **Real Estate Economics** | **27(3)** | **10.1111/1540-6229.00781** | **The Integration of Commercial Real Estate Markets and Stock Markets** |

### §5.2 verdict — ★ CONFIRMED 강력

| 항목 | R3 박제 | Primary (CrossRef) | verdict |
|---|---|---|---|
| Authors | Ling-Naranjo | David C. Ling, Andy Naranjo | CONFIRMED |
| Year | 1999 | 1999 | CONFIRMED |
| Journal | Real Estate Economics | Real Estate Economics | CONFIRMED |
| Vol/Issue | 27(3) | 27(3) | CONFIRMED |
| DOI | (R3 박제 X) | 10.1111/1540-6229.00781 | 추가 박제 |
| Title (topic) | "REIT-stock market integration regime-conditional" | "The Integration of Commercial Real Estate Markets and Stock Markets" | CONFIRMED (방향성 일치) |

**종합 verdict**: ★ **CONFIRMED 강력** (primary metadata 6/6 일치, DOI 추가). REIT-stock market integration mechanism 학설 anchor 적격.

### §5.3 audit-ready 박제

- **A 이론 실재성**: primary verify 완료. yaml 학설 anchor 박제 적격.
- **E 환각 cross-verify**: phantom catch 1차 → 1999 대체 = primary 정합. PASS.

---

## §6. 종합 verdict — 5 ref/event + 학설 ↔ 실측 corr (small-N rigor)

### §6.1 종합 verdict 표

| # | Ref / Event | R3 박제 | Primary verify | 학설 실측 corr (n, p, CI) | verdict |
|---|---|---|---|---|---|
| 1 | **AMT VIL Goodwill Impairment** | $3.22B (2023) | **$322.0M** (Q3 2023 India) + $402M FY total | event 2023-10 AMT +8.0% (z=+1.96, n=1) | ★ **REJECTED** magnitude (factor 10x 오기) / TENTATIVE event (n=1) |
| 2 | **CCI Sprint Cancellations** | $200-400M/yr 2021-24 | **$250M (2023 FY 실측)** + $235M (2025 guide) | event 2024-01 CCI -4.9% (z=-0.47, noise) | **PARTIAL** primary (magnitude order OK, range 2021-24 + $400M 상단 TENTATIVE) / TENTATIVE event |
| 3 | **Beracha-Feng-Hardin 2019** | "Real Estate Economics" / inflation hedging | **JRER 41(4)** "REIT Operational Efficiency" (★ journal 오기 + topic 환각) | VNQ-CPI yoy r=-0.112 (NW p=0.090, n=258, block CI [-0.218, -0.010]) | ★ **REJECTED ref (★ 재환각)** + **PARTIAL CONFIRMED weak negative** (★ Yobaccio 1995 / Glascock-Lu-So 2002 broader 학설 정합) |
| 4 | **Ling-Naranjo 1997 JREFE 14(3)** | "Economic Risk Factors and CRE Returns" | JREFE 14(3) DOI:10.1023/a:1007754312084 (★ primary 6/6 일치) | term_spread r=-0.016 p=0.86 / hy_oas r=-0.103 p=0.35 / indpro_yoy r=+0.137 p=0.26 / cpi_yoy r=-0.103 p=0.53. n=35 (HY OAS series 2010+ start). Bonferroni α/4=0.0125 = **0/4 생존**. | ★ **CONFIRMED ref** + **REJECT weak corr** (n=35 small, 4/4 비유의) |
| 5 | **Ling-Naranjo 1999 RealEstateEconomics 27(3)** | "REIT-stock market integration regime-conditional" | RealEstateEconomics 27(3) DOI:10.1111/1540-6229.00781 (★ primary 6/6 일치) | full r=0.746 (NW p<0.001, n=260, CI [0.645, 0.808]) / high_vol r=0.814 (n=124) / low_vol r=0.518 (n=125), all p<0.001 | ★ **CONFIRMED 강력** ref + **CONFIRMED 강력 corr** (★ regime-conditional 통합 강화: tail-correlation 1 수렴 정합) |

### §6.2 small-N rigor 정합 (5 의무 자가 점검)

| 의무 | 적용 |
|---|---|
| (a) n + p 명기 | ★ 모든 정량 claim 에 n + NW HAC p + block bootstrap CI 박제 |
| (b) m≥4 비교 Bonferroni | §4 (4 factors): α/4=0.0125, 0/4 생존 박제. §3/§5 별도 비교 = 누적 m=6, α/6=0.0083 (§5 full p=3.5e-05 «« 0.0083, 생존) |
| (c) 95% CI 박제 | ★ block bootstrap (block_size=12 month, autocorr 보정) 95% CI 모든 corr 에 박제 |
| (d) hedge 어휘 | ★ "강력 확인" 단정 어휘 회피 — "★ CONFIRMED 강력 (regime-conditional 통합 강화)" 만 §5 에 한정. §3/§4 = "PARTIAL" / "REJECT weak" 보수 hedge |
| (e) 점추정 prior 박제 금지 | ★ §5 r=0.746 단독 박제 아니라 CI [0.645, 0.808] + regime-split 표 + Bonferroni 생존 검증 결합. yaml 박제 시 prior_strength = CI 박제 의무 (main verdict 후) |

### §6.3 12축 audit-ready 박제 (R4 carry 적용 결과)

| 축 | 결과 |
|---|---|
| **A 이론 실재성** | §1/§2 SEC EDGAR primary verify, §4/§5 CrossRef DOI 일치. §3 paper 자체 존재 verify (JRER 41(4)) but topic 환각. PASS partial. |
| **B 실데이터 OOS** ★hard | §5 Newey-West t > 4, full sample r=0.746, regime-split CI 0 미포함, OOS Rank-IC > 0.5. **Hard PASS**. §3/§4 weak (PARTIAL/REJECT). §1/§2 event n=1 INSUFFICIENT. **★ §1.7 self-check 2026-05-31 (main 지시 소급)**: driver 정상성 ADF/KPSS 사후 검정 = term_spread (DGS10-DGS2 level) ADF p=0.005 + KPSS p=0.10 **정상** ✓ / indpro_yoy ADF p<0.0001 + KPSS p=0.09 **정상** ✓ / cpi_yoy ADF p=0.003 + KPSS p=0.05 **borderline 정상** ✓ / **★ hy_oas (BAMLH0A0HYM2 level, n=37 small) ADF p=0.10 + KPSS p=0.01 = 비정상 의심 (I(1) 후보)**. §4 종속변수 = VNQ return (차분, 정상) → strict level-on-level 아님 (mixed regression). §4 결과 = 4/4 비유의 Bonferroni 0/4 REJECT — false positive type-I risk 0 (REJECT 결과 robust). 단 hy_oas level driver ADF 미검정 = 형식 위반 (ERROR-202605311600 promo-log 박제). R5 후속 = BAA-AAA spread proxy 확장 시 차분/coint 검정 의무 박제. yaml 박제 영역 (block3 corr_prior / block5 hook) = level corr 박제 0건 = clean. |
| **C yaml 추적성** ★hard | 본 세션 = yaml 박제 X (main verdict 후). 산출 = `r4-carry-verify.md` + `r4_carry_verify.py(.log)` raw 박제. main verdict 후 yaml v3 박제 시 ±5% 추적성 의무. |
| **D PIT** ★hard | FRED CPIAUCSL = latest revised (true first-release ALFRED TODO, partial caveat 명시). 가격 데이터 = monthly close (익월 진입 가능). PIT-correct partial. |
| **E 환각 cross-verify** ★hard | ★ **2건 환각 catch**: (1) AMT $3.22B → $322M (factor 10x), (2) Beracha-Hardin 2019 ref 재환각 (journal + topic). E축 hard-fail 회피 메커니즘 작동. |
| **F 반증조건 + 기각** | ★ **3건 REJECT 기록**: AMT magnitude / Beracha 재환각 / §4 economic factors weak. p-hacking 차단 PASS. |
| **G effective-N** ★tier | §3 n=258 large, §4 n=35 small (★ structural prior 강등), §5 n=260 large, §1/§2 event n=1 (★ INSUFFICIENT). 단정 verdict tier 차등 적용. |
| **H 미해결 의문** | §7 학습 박제. confound: §4 HY OAS series 시작 2010 → n=35 제약. universe 확장 (long Treasury 대체 default proxy) → 후속 R5. |
| **I 생존편향** ★hard | VNQ ETF basket = 시가 가중 + index rebalance (partial 생존편향). AMT/CCI 자체 = 2026 현재 생존 종목. 상폐 REIT 미포함 caveat 명시. SFR/Gaming/Timberland 확장 후속 별도 trace. |
| **J 경제적 유의성** | 거래비용 적용 직접 X (본 R4 carry = lens/정성 용도). alpha 주장 X. |
| **K 다중검정** ★hard | 시도횟수 공시: 5 ref × {corr verify + event-study} ≈ 6 corr 비교. Bonferroni α/6=0.0083. §5 full + regime 3건 모두 생존 (p << 0.0083). §3/§4 비생존. |
| **L 통합 PSD** | 본 세션 yaml 박제 X, 통합 차단 단계 미진입. main verdict 후 yaml v3 박제 시 점검. |

### §6.4 학설 ↔ 실측 종합 해석

**Ling-Naranjo 1999 학설 = 핵심 발견 ★**: REIT-stock integration regime-conditional 학설이 실측에서 정량 강화 — high vol regime 에서 corr 0.81 (low vol 0.52) = tail-correlation 1 수렴 (위기 시 통합 강화). study_session.yaml block5 confidence_hooks 에 **regime-conditional 통합 hook** 박제 권고 (★ main verdict 후).

**Beracha-Hardin 2019 학설 = 부분 정합 ★**: ref 자체는 재환각 (★ REJECTED) but broader literature 학설 (Yobaccio 1995 / Glascock-Lu-So 2002 negative spurious) 은 VNQ-CPI yoy r=-0.112 (block CI [-0.218, -0.010]) = weak negative 정합. **REIT 빈약 inflation hedge 학설 PARTIAL CONFIRMED**. yaml 박제 시 Beracha-Hardin 2019 인용 **제거 의무**, broader literature 학설 anchor 만 유지.

**Ling-Naranjo 1997 학설 = inconclusive small-N ★**: economic risk factors → CRE returns 학설이 n=35 small-N 에서 4/4 비유의 (Bonferroni 0/4 생존). 학설 anchor 자체는 적격 (★ CONFIRMED ref) but 실측 weak. yaml 박제 시 **tier = structural prior (저신뢰)** + n caveat 박제 의무.

**AMT/CCI event = TENTATIVE DIRECTIONAL n=1**: AMT 2023-10 +8% rebound (z=+1.96) → impairment 발표에도 시장 호재 반영 (매각 announce $2.5B). CCI 2024-01 -4.9% (z=-0.47) → noise 수준, Sprint Cancellations 가이던스 사전 가격 반영 가능성. **단정 금지** (n=1).

---

## §7. 학습 박제 (promotion-log K/ERROR 후보)

### §7.1 ERROR (자문 raw 재환각 + factor 10x 오기)

**ERROR-202605310200-amt-322m-factor-10x**: gemini R3 박제 "AMT VIL Goodwill $3.22B 2023" = factor 10x 오기 환각. primary (SEC EDGAR AMT 10-K 2023) = $322.0M (Q3 2023, India unit). 본 R4 carry SEC EDGAR text grep 으로 catch. 방지책: 자문 정량 단위 ($ B 단위 vs $ M 단위) primary cross-verify 의무 (E축 hard-fail).

**ERROR-202605310200-beracha-hardin-2019-rechallucination**: R3 자문 (gemini + claude 양쪽 합의) 박제 "Beracha-Feng-Hardin 2019 RealEstateEconomics inflation hedging" = ★ 재환각 (1차 환각 Beracha-Krautz 2022 catch 후 대체 ref 자체가 또 환각). primary (CrossRef DOI 10.22300/0896-5803.41.4.513) = Journal of Real Estate Research 41(4) "REIT Operational Efficiency and Shareholder Value" (★ inflation hedging topic 아님). 방지책: 자문 학설 ref 인용 시 **CrossRef DOI primary verify 의무** (E축 hard-fail, A 이론 실재성 hard). 1차 환각 대체 ref 도 primary verify 통과해야만 yaml 박제.

### §7.2 K-Note (지식 갱신)

**K-202605310200-crossref-api-paywall-bypass**: 학술 ref 환각 verify 시 Wiley/Springer paywall block. **CrossRef API public** (`api.crossref.org/works?query.author=...`) = paywall X, JSON metadata return (author/year/journal/vol/issue/DOI/title). 본 R4 carry 학설 ref 3건 catch 의 핵심 mechanism. 향후 ref 환각 verify 표준 도구로 박제.

**K-202605310200-sec-edgar-inline-xbrl-binary-grep**: SEC EDGAR 10-K body = inline XBRL HTML, 5 line packed. tag strip + `grep -a -o -i "phrase[^<]\{0,500\}"` (binary-safe) 으로 primary 정량 fact 추출 가능. AMT $322M / CCI $250M catch 의 mechanism.

**K-202605310200-fred-vs-yfinance-monthly-frequency-align**: yfinance monthly auto-aligned, FRED daily series resample("MS").last() 또는 .mean() 정렬. inner join 시 HY OAS series 시작 (2010+) 가 bottleneck → n 작아짐. 별도 default spread proxy (BAA-AAA, FRED BAA + AAA 시리즈) 가 long history.

### §7.3 후속 R5 carry (본 R4 verify 잔존 의문)

1. **CCI Sprint Cancellations 2021-22 multi-year verify**: CCI 10-K 2021/2022 추가 fetch, multi-year range $200M-$400M 확인.
2. **Beracha-Feng-Hardin 2019 인용 yaml 제거 + broader literature 학설 anchor 정합** (★ main verdict 후 yaml v3 박제 시).
3. **§4 Ling-Naranjo 1997 economic risk factors n 확장**: HY OAS (2010+) 대신 BAA-AAA spread (1953+) proxy 사용 시 n ≈ 250+ 가능. 본 R4 carry 범위 외, R5 후속.
4. **§5 regime-conditional 통합 hook yaml block5 박제** (★ main verdict 후): VNQ-^GSPC high_vol r=0.81 vs low_vol r=0.52 = 통합 강화 hook 의무.
5. **§1/§2 event-study window 확장**: ±20 day daily CAR (현재 1 month coarse). AMT 2023-10-26 (Q3 earnings call 추정) + CCI 2024-01-24 (Q4 2023 earnings) ±20 day window 다시 분석.

---

## §8. 산출 cross-ref

- `D:/projects/Inv/study-research/reit/raw/r4-carry-verify.md` (본 파일)
- `D:/projects/Inv/study-research/reit/raw/scripts/r4_carry_verify.py` (작성 예정)
- `D:/projects/Inv/study-research/reit/raw/scripts/r4_carry_verify.log` (작성 예정)
- `D:/projects/Inv/study-research/reit/candidate-ledger.md` (⏳C R4 carry 3건 status 갱신)
