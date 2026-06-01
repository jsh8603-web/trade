---
title: "Credential-gated 지표 무료 대체 가능성 probe (실 fetch 검증)"
date: 2026-06-01
tags: [study, commodity, eq_us_cyclical, credential-free, probe, fred, eia, finnhub, pmi]
phase: "handoff §4 잔여 — credential 게이트 4종 무료 대체 실데이터 probe"
scope: "cushing(EIA) / roll_yield(CME) / forward EPS revision breadth(FINNHUB·IBES) / ISM·PMI(FRED)"
method: "authenticated fredapi (FRED_API_KEY .env 보유) + yfinance 1-sample + EIA anon probe + FINNHUB anon probe. ★합성/추정 없음, 실 fetch 만."
verdict: "2 불가(cushing·roll_yield 무료 FRED 미러 부재) / 1 부분(fwd EPS = FINNHUB 무료 key 발급 시 가능, 무인증 401) / 1 가능(ISM·PMI = FRED 무료 확정, 기적재 + 지역연준 diffusion 추가 가용)"
---

# Credential-free 대체 probe — 4종 (2026-06-01)

> handoff §4 잔여 = "cyclical ISM/forward EPS(유료), commodity cushing(EIA)·roll_yield(CME) — 사용자 빌드 confirm 대기".
> 각 후보를 실 fetch 1-sample 로 무료 대체 가능 여부 판정. fetch 실패 = 사유 명시.
> **데이터 일자 = 2026-06-01 fetch 시점**. FRED 시리즈는 latest-revised (true vintage = ALFRED TODO, 본 probe 범위 밖).

## 0. 환경 / 검증 경로

- `FRED_API_KEY` = .env 보유 (32자), authenticated fredapi 정상 동작 (DCOILWTICO n=10168 확인).
- `EIA_API_KEY` = .env **미보유**. `FINNHUB_API_KEY` = .env **미보유**.
- ★fredgraph CSV(`fred.stlouisfed.org/graph/fredgraph.csv`) 무인증 endpoint = 본 네트워크에서 ReadTimeout(30s) 반복 → **authenticated API 경로로 전량 재검증**. (CSV 미러 권고 시 EIA/FINNHUB 무인증 대안은 별도 발급 필요로 귀결)
- fredapi rate-limit 주의: 시리즈당 throttle 2s + 429 retry 8s 적용해야 안정. (초기 무throttle batch = "Too Many Requests" cascade 발생 → throttle 후 전량 성공)

---

## 1. commodity cushing (Cushing 원유 재고) — ★불가 (FRED 미러 부재, EIA key 필요)

| 후보 series | 결과 | 사유 |
|---|---|---|
| `WCESTUS1` | ❌ | FRED "series does not exist" |
| `WCRSTUS1` | ❌ | FRED "series does not exist" |
| `WCSSTUS1` / `WCESTP21` / `WCESTP31` / `WTTSTUS1` | ❌ | 전부 FRED "does not exist" |
| `W_EPC0_SAX_YCUOK_MBBL` (EIA native code) | ❌ | FRED "Invalid series_id" (EIA 코드, FRED 미host) |

**FRED 검색 API 결과** (`search_text='Cushing'`): 가용 = **가격 시리즈만** —
`DCOILWTICO` (WTI Cushing 가격, D, 1986-01~2026-05, n=10168), `MCOILWTICO`/`WCOILWTICO`/`ACOILWTICO`.
**재고(inventory) 시리즈 = 부재.** `search_text='crude oil stocks'` → `M05F3AUSM387NNBR`(1918~1941 NBER 역사 데이터)만, 현행 weekly 재고 없음.

**EIA API 직접 probe**: `api.eia.gov/v2/petroleum/stoc/wstk/data/` 무인증 호출 → **HTTP 403 `API_KEY_MISSING`** ("Please register at eia.gov/opendata/register.php").

→ **판정: 불가 (무료 FRED 미러 없음). 단 EIA 무료 key 발급(즉시·무료) 시 가능.**
실 series = `PET.W_EPC0_SAX_YCUOK_MBBL.W` (Cushing OK ending stocks, weekly). commodity yaml(L178/273/650)이 이미 "FRED 404 → EIA 직접" 정확히 명시함 → ★본 probe 가 그 가정을 실측 확인.

---

## 2. commodity roll_yield (선물 만기구조 carry) — ★불가 (무료 term structure 부재)

| 경로 | 결과 | 사유 |
|---|---|---|
| yfinance `CL=F` (WTI front) | ✅ rows=5, last_close=89.64 (5d) | **front-month 연속물만**. back-month(F2/F3) 없음 → 만기구조 계산 불가 |
| yfinance `CLF26.NYM` / `CLZ25.NYM` (특정 월물) | ❌ rows=0 | Yahoo "Quote not found / delisted" — 개별 월물 미제공 |
| FRED `DCOILWTICO` (WTI spot) | ✅ n=10168, last=97.63 | 현물 1개 시리즈. 선물커브 아님 |
| FRED `DCOILBRENTEU` (Brent spot) | ✅ n=9898, last=102.75 | 현물 1개 시리즈 |

roll_yield = (F1−F2)/F1 류 term-structure carry → **최소 2개 만기 EOD 필요**. yfinance/FRED 무료 경로 모두 **단일 만기(front 또는 spot)** 만 제공 → 구조적으로 산출 불가.

→ **판정: 불가 (무료 다중만기 선물 EOD 부재).** commodity yaml(L147/151/635)이 명시한 "CME 지연 EOD collector 신규" 또는 OpenBB 경로가 정합. ★spot 1개로는 roll_yield proxy 불가 확정.
(참고: USO 같은 ETF의 roll-cost drag 를 역산하는 우회 proxy 는 noisy + 다단계 가정 → 본 probe 는 "직접 무료 대체 불가"로 판정.)

---

## 3. cyclical forward EPS revision breadth — ★부분 (FINNHUB 무료 key 발급 시 가능)

| 경로 | 결과 | 사유 |
|---|---|---|
| FINNHUB `/stock/recommendation`·`/eps-estimate` 무인증 | ❌ HTTP 401 `{"error":"Please use an API key."}` | 무인증 차단 |
| FINNHUB_API_KEY (.env) | ❌ 미보유 | 무료 가입 필요 |

FINNHUB 무료티어는 **API key 무료 발급(가입 즉시)** 시 `/stock/recommendation`(추천 trend) 제공. 단:
- 무료티어 rate-limit = 60 req/min. revision breadth 는 종목별 호출 누적 필요 → 섹터 breadth 산출 시 호출량 多 (XLI 30+종목 × 주기 = 분당 한도 압박).
- ★forward EPS estimate **revision** 시계열(상향/하향 breadth)은 무료티어 coverage 제약 — `/stock/eps-estimate`·`/stock/revenue-estimate` 일부 무료, 정밀 revision breadth(IBES/FactSet 급)는 유료.

→ **판정: 부분.** 추천/추정 trend 의 coarse proxy = FINNHUB 무료 key 로 가능. 정밀 fwd EPS revision breadth = 유료(IBES/FactSet). cyclical yaml(L95/281/284) "FINNHUB 무료티어 또는 EDGAR 8-K" 정합 — 무료 경로 존재하나 quality 격하 불가피.

---

## 4. cyclical ISM 신규주문/PMI — ★가능 (FRED 무료 확정, 기적재 + 지역연준 추가 가용)

### 4-A. 신규주문류 (ISM 신규주문 직접 무료 대체, 기적재 확인)

| FRED series | 의미 | n | range | last |
|---|---|---|---|---|
| `AMTMNO` | Mfg new orders | 410 | 1992-02~2026-03 | 630448 |
| `NEWORDER` | core capex 신규주문 ex-aircraft | 411 | 1992-02~2026-04 | 82426 |
| `DGORDER` | 내구재 신규주문 | 411 | 1992-02~2026-04 | 345956 |
| `ACOGNO` | consumer goods 신규주문 | 410 | 1992-02~2026-03 | 258816 |

→ eq_us_cyclical merit(validation-merit-cyclical-leading.md, yaml 블록9)에서 **이미 무료 FRED 대체 완료**. DGORDER→XLE forward = TENTATIVE DIRECTIONAL(★최강 후보, 단 Bonferroni 0/96 미생존 → 단정 금지). ★본 probe 가 4종 실 fetch 로 가용성·n 재확인.

### 4-B. 지역연준 diffusion PMI proxy (추가 무료 가용 — ISM diffusion 포맷에 가장 근접)

| FRED series | 의미 | n | range | last |
|---|---|---|---|---|
| `GACDISA066MSFRBNY` | Empire State 일반활동(diffusion) | 299 | 2001-07~2026-05 | 19.6 |
| `NOCDISA066MSFRBNY` | **Empire State 신규주문** | 299 | 2001-07~2026-05 | 22.7 |
| `GACDFSA066MSFRBPHI` | Philly Fed 일반활동 | 697 | 1968-05~2026-05 | -0.4 |
| `NOCDFSA066MSFRBPHI` | **Philly Fed 신규주문** | 697 | 1968-05~2026-05 | -1.7 |
| `BACTSAMFRBDAL` | Dallas Fed mfg 활동 | 264 | 2004-06~2026-05 | 0.4 |

★`NOCDISA066MSFRBNY`(Empire 신규주문) + `NOCDFSA066MSFRBPHI`(Philly 신규주문) = **diffusion-index 포맷**(ISM 50 기준선 류와 동형, ±부호 = 확장/수축)으로 ISM 신규주문의 무료 가장 근접 proxy. 발표시차 ≈ 당월(census 신규주문 56~64d보다 적시). Philly = 1968~ 장기(n=697)로 regime 분석에 유리.
**단 caveat**: 지역 한정(NY/PA/TX), seasonal-adj diffusion, n<30 regime split 시 small-n rigor 적용 의무. forward 예측력 = ★미검증(co-move 추정만, 본 probe 는 가용성만 확인 — 검증은 별도 latch 필요).

→ **판정: 가능.** ISM 신규주문/PMI = FRED 무료 완전 대체. census 신규주문류(기적재) + 지역연준 diffusion(NOCDISA/NOCDFSA 신규) 추가 가용.

---

## 5. 4종 종합 판정표

| 지표 | 판정 | series / source | n | 근거 |
|---|---|---|---|---|
| 1. cushing 재고 | ❌ **불가** | (FRED 미러 부재) `PET.W_EPC0_SAX_YCUOK_MBBL.W` = EIA 직접 | — | FRED 검색=가격만, EIA 무인증 403 API_KEY_MISSING. EIA 무료 key 발급 시 가능 |
| 2. roll_yield | ❌ **불가** | (무료 다중만기 부재) CME 지연 EOD 신규 collector 필요 | — | yf CL=F=front만, 개별월물 delisted, FRED=spot 1개. term structure 산출 불가 |
| 3. fwd EPS revision breadth | ⚠️ **부분** | FINNHUB 무료key(coarse) / IBES·FactSet(정밀=유료) | — | 무인증 401. 무료 key 시 추천trend 가능, 정밀 breadth=유료. rate-limit 60/min |
| 4. ISM 신규주문/PMI | ✅ **가능** | FRED `AMTMNO/NEWORDER/DGORDER/ACOGNO` + `NOCDISA066MSFRBNY`/`NOCDFSA066MSFRBPHI` | 299~697 | 무료 FRED 확정. census류 기적재 + 지역연준 신규주문 diffusion 추가 |

---

## 6. collector_plan 등록 권고 (★보고 한정 — yaml 직접 수정 안 함)

### 6-A. commodity/study_session.yaml (이미 정확히 명시됨 — 변경 불필요, 확인만)
- L644~651 `EIA crude/petroleum stocks` 항목: `credential: EIA_API_KEY (요청)` + "PET.WCESTUS1.W (FRED 404, EIA 직접)" → ★본 probe 가 FRED 404 실측 확인. **권고: 변경 없음. 단 series id 를 `PET.W_EPC0_SAX_YCUOK_MBBL.W`(Cushing-specific) 로 명확화 + "EIA 무료 key 발급 즉시 가능, FRED 미러 부재 실측 확인(2026-06-01)" 주석 1줄 보강 권장**.
- L635~641 `Commodity futures term structure` 항목: `credential: none (delayed EOD) 또는 OpenBB` → ★yfinance/FRED 무료 경로로는 불가 실측. **권고: "yf CL=F=front-only, FRED=spot-only → roll_yield 무료 직접 대체 불가 실측(2026-06-01). CME 지연 EOD 또는 OpenBB 필수" 주석 보강**.

### 6-B. eq_us_cyclical/study_session.yaml
- L281~284 forward EPS revision breadth(FINNHUB/IBES): **권고: "FINNHUB 무인증 401 실측, 무료 key 시 coarse 추천trend 가능 / 정밀 revision breadth=IBES·FactSet 유료. rate-limit 60/min(섹터 breadth 호출량 압박)" caveat 1줄 보강**.
- 블록9 merit_leading_vars(L550~): **권고: 신규 무료 후보 `NOCDISA066MSFRBNY`(Empire 신규주문, diffusion) + `NOCDFSA066MSFRBPHI`(Philly 신규주문, 1968~)를 `ism_pmi_proxy` candidates 에 추가 등록 후보로 표기**. diffusion 포맷 = census 신규주문류(level/yoy)보다 ISM 신규주문 직접 대응. ★단 forward 예측력 미검증 → in_our_system=false + structural_low_confidence + validated_alpha:false 로 등록 (small-n rigor: 가용성만 확인, IC 검증은 별도 latch 의무).

---

## 7. 산출물 / 검증 무결성

- probe 스크립트: `probe_credential_free.py`(1차, rate-limit cascade) → `probe_fredapi_throttled.py`(throttle 후 전량 성공) → `probe_cushing_search.py`(FRED 검색).
- 결과 json: `probe_fredapi_throttled_results.json`, `probe_cushing_search_results.json`, `probe_credential_free_results.json`.
- ★전량 실 fetch. 합성/추정 0. 실패 항목(cushing series, FINNHUB, 개별 월물) = 사유 박제(does-not-exist / 403 / 401 / delisted).
- FRED 시리즈 = latest-revised (true first-release vintage = ALFRED TODO, 본 probe 범위 밖).
- ★yaml 직접 수정·커밋 안 함. 등록 권고는 §6 보고 한정.
