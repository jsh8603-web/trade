---
tags: [type/research-log, domain/equity, sector/us_cyclical]
date: 2026-06-03
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# us_cyclical 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| PER/PBR | EDGAR companyconcept XBRL (equity/net_income/shares) | filed date PIT 적용 OK, 27637행 60종 | ✅ (재작업 대상) | near-duplicate horizon 강상관 → M_eff 보정 필요 |
| HY OAS regime | FRED BAMLH0A0HYM2 | ★실 가용 2023-05~ 37개월만 (BofA-FRED 라이센스) | ⏳ regime INSUFFICIENT | rate10y는 437개월 가용 — Baa-Aaa proxy 장기 대안 검토 |
| rate10y/vix/dollar | FRED CSV + yfinance DXY | OK, 장기 가용 | ✅ cross β | dollar β 비유의 (R2 Bruno-Shin US 도달 약) |
| EV-EBITDA | EDGAR (영업이익+감가상각+부채) | ★미수집 — 현 EDGAR concept 3개만(equity/NI/shares) | ❌ 데이터 부재 | collector_plan: OperatingIncomeLoss + D&A + debt concept 추가 필요 |

## 환경 함정 (★재발 방지)
- [2026-06-03] 막힘: `python`/`py`/`python3` 모두 PATH 부재 (bash·PowerShell 둘 다). → 진단: Python 미등록. → 해결: `PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"` 절대경로 직접 호출. → 교훈: 이 세션 모든 .py 실행은 이 절대경로 변수 경유.

## 막힘·해결 로그 (시계열)
- [2026-06-03 진입] dispatch-role-rework + 게이트 4종 + ledger 양식 + frame §M(M.10~M.12) + 자문 R1/R2 brief 정독 완료. 현 baseline = TENTATIVE / BY 생존 0. R2 4수정(family 3분리 / M_eff / eff_N 이중보정 / cyclical basket 불필요) 확인.

## 측정 방법 결정 로그
- [S1 리서치 2026-06-03] Gemini 2-Phase(Pro 광범위×2 + Flash 심층×2 + citation 환각검증). archive=~/.claude/docs/archive/research-raw/us-cyclical-*-20260603.txt.
- ★citation 환각검증: Cooper-Gulen-Schill(2008 JF)/Novy-Marx(2013 JFE)/Sloan(1996 AR)/Fama-French(1989 JFE)/Frazzini-Pedersen(2014 JFE)/Chen-Roll-Ross(1986 JoB) = CONFIRMED. Barbee-Mukherji-Raines(1996 FAJ) = CORRECTED(Phase1 "Barbee-Jeong-Mukherji 2008" 오류).
- ★EDGAR concept 실측(5 sector 대표): `Assets`=전종목 가용 / `GrossProfit`·`CostOfRevenue`=semi·industrials만(mat/energy/fin=0) / `Revenues`=일부(GS·LIN=0) / debt·cash·OpIncome·D&A=일부. → asset_growth 만 전 universe 깨끗, gross_prof/sales_yield 는 sector 커버리지 파편화.
- 측정 우선순위 결정: asset_growth(전 universe, peak-EPS 유발 cycle 직접) > sales_yield(peak-EPS robust value) > gross_profitability(부분 sub-universe). regime = Baa-Aaa 장기 proxy(HY 37mo 대체).
- 방법 4수정 = family 3분리(Harvey-Liu-Zhu: regime 사전지정 시 별 family 정당) / M_eff(Li-Ji 2005, test-stat 상관행렬) / eff_N 이중보정 / cyclical basket 불필요.

## 막힘·해결 로그 (시계열) [추가]
- [2026-06-03] WebSearch hook 차단(research.block) → search-engine 스킬(Gemini gemini-search.js pro/flash) 경유. node 풀패스 "/c/Program Files/nodejs/node.exe" 필수.
- [2026-06-03] EDGAR LongTermDebt 단일 concept 404(CAT) → LongTermDebtNoncurrent 사용. RevenueFromContractWithCustomerExcludingAssessedTax 404 → Revenues 표준.
- [2026-06-03] ★기존 edgar_fundamentals.parquet = equity/net_income/shares **3 concept만** 수집됨. asset_growth/sales_yield/gross_prof 측정하려면 collect.py 재실행으로 Assets/Revenues/GrossProfit/CostOfRevenue 추가 fetch 필수. → team-lead 질문(a) Baa-Aaa + EDGAR 추가 concept fetch 승인 필요.
- [2026-06-03] ★shares concept = 47/60종만(13 결측) = 기존 PBR/PER 일부 종목 누락 원인. CommonStockSharesOutstanding 외 fallback(EntityCommonStockSharesOutstanding / WeightedAverageNumberOfSharesOutstandingBasic) 추가 검토.
- [2026-06-03] python stdout cp949 인코딩 에러(유니코드 ★·— 출력 시) → 1-liner 도 measure.py 처럼 `sys.stdout=io.TextIOWrapper(...,encoding='utf-8')` 또는 ASCII 출력만.

## 막힘·해결 로그 [측정 단계]
- [2026-06-03] EDGAR 9 concept 추가 fetch foreground 완료(92075행). assets=60/60, revenues=59, gross_profit 직접=28(+cogs fallback 44), op_income/dep/debt/cash 부분. macro baa_aaa(1919~2026, 1288mo) 생성.
- [2026-06-03] ★shares 47/60 결측 root cause: 일부 종목(V/TXN/COP 등 13종)이 us-gaap 아닌 **dei:EntityCommonStockSharesOutstanding** + us-gaap WeightedAverageNumberOfSharesOutstandingBasic 에만 존재. EDGAR_CONCEPTS가 us-gaap만 + shares 첫 cache(47종)라 want 제외 → 재fetch 안 됨. → dei 네임스페이스 지원 + shares 강제 재수집 필요.
- [2026-06-03] ★asset_growth 버그: 자산 YoY = mktcap 불필요인데 build_pit_panels 가 shares 게이트(if isnan(shares):continue)로 13종 skip. asset_growth/gross_prof(GP/Assets) = shares 무관 → 게이트 밖 분리 필요.

## 측정 결과 1차 (shares 수정 전, ★BY 생존 0 유지)
- family_1 BY: raw m=36 → **M_eff=19.0**(Li-Ji 정확 절반 축소, near-dup 포착). raw_p_min=0.0145(per_z 24M) > threshold 0.00146 → ★survivors=0. nondegenerate strip(24M 제외)도 0.
- ★G-B 트리거: BY 생존 0 AND raw_p_min 0.0145 > threshold×2(0.00293) = ★G-B 충족.
- ★asset_growth OOS decay(보강1): IS +0.12 → OOS −0.058 **부호 반전 persist=False** = 2015~ decay/crowding 확인. 단 IS 부호 +(이론 음과 반대) = cyclical universe 에서 예측대로 작동 X.
- ★sales_yield sub-sector: 전 sector 일관 양(+0.07~+0.26) + 12M OOS persist=True. unconditional t 낮으나(0.66) sub-sector 부호 일관 강. per_z 도 전 sector 음 일관(energy −0.24/fin −0.20).
- family_2 regime(baa_aaa high-spread): per_z −0.21(vs lo −0.04)/vol +0.29/mom_6 −0.15(vs lo +0.09 부호반전) = risk-off 증폭.
- family_3 β: dollar −1.04 t−3.73(단독 회귀) / vix −9.71 / hy_oas −9.18(36mo) / baa_aaa −1.46 비유의(135mo).

## 측정 결과 2차 (shares 보강 60종 + ★sector-neutral z = 방법 결함 발견)
- ★universe-z(기존 방식, 60종 보강): family_1 BY 생존 0. raw_p_min=0.0178(mom_6 3M) > thr 0.00157 = ★G-B 트리거. 기존 per_z "유의"(47종 t−2.48)는 shares 13종 보강 시 약화(60종 t−1.16) = ★coverage artifact.
- ★★**sector-neutral z(sector 내 demean) = 방법 결함 발견 → BY 생존 0 → 8 회복**:
  - pbr secN: 3M/6M/12M/24M 전 horizon BY 생존(t−3.18~−3.65). ★nondegenerate strip 후에도 3M/6M/12M 생존.
  - ev_ebitda secN: 3M/6M/12M BY 생존(t−2.79~−3.39, peak-EPS-robust value).
  - per secN 3M t−2.14(약) / sales_yield secN 24M t+2.02(양).
  - M_eff=20.0(raw 36), threshold rank1=0.00137, raw_p_min=0(ev_ebitda 24M).
- ★진단: cyclical sleeve = sector 간 valuation 수준 차이 큼 → **universe-wide demean z 가 sector mixing 으로 신호 희석**. sector-neutral z(within-sector)가 진짜 cross-sectional value 포착. = ★자문 R2 "방법 결함 절반"의 us_cyclical 정체. ⛔frame §M.7 "peer-relative sector-neutral z" 계약과 정합 — 기존 measure.py 가 universe-demean 쓴 게 계약 위반/결함.
- ★robustness(sector-neutral): pbr OOS persist=True(decay>1 강화) within 0.73/0.91 + sub-sector 전5 음 일관 + LOO 5sector 안정(−0.09~−0.18) = CONFIRMED 후보. ev_ebitda OOS persist + within 0.82/0.91 + sub-sector 4 음(financials +0.06=EV/EBITDA 은행 부적합 개념차, A-4 게이트 "개념차 vs cancel 구분"). per/sales_yield OOS persist=False = TENTATIVE.
- = ★한국 cyclical(auto/반도체 PBR○ PER✗ peak-EPS) 정합: 미국 cyclical 도 PBR/EV-EBITDA(peak-EPS-robust) value 작동, PER 약.
- ★robustness 추가(보강, _probe_episode_cost.py): pbr secN **leave-year 11개 연도 각 제외해도 IC −0.099~−0.145 안정**(단일 episode 의존 X) + **long-only top-quintile spread 6M +4.6%/12M +10.2% gross, net(16bps) +4.4%/+10.0%** = 거래비용 후에도 강. ev_ebitda leave-year −0.090~−0.132 + long-only net +4.2%/+8.4%. → ★pbr = BY+OOS+within+LOO-sector+leave-episode+net-cost 전부 통과 = CONFIRMED 등급.

## ★team-lead 검증 의무 a/b/c 완료 (BY 8 진짜 신호 mechanism 입증)
- ★team-lead 확정(2026-06-03): (1) sector-neutral z 정식 전환 승인 (2) G-B 재자문 불필요(약함 단정 아닌 방법 교정 회복) (3) sector-neutral = G-C audit 1순위. 전 sleeve(defensive/mega_tech) sector-neutral 전환 필요.
- **검증(a) sub-sector N**: 각 sector static 12종, pbr 월별 median 9~12종. frame line 322 경고(13~17종 demean ≈0) 구간이나, within-sector z cross-std=0.962(pbr)/0.944(ev) ≈1 = over-neutralize 아님(신호 소멸 X). sector당 12종 = small-n hedge 라벨(magnitude 보수, 방향 신뢰).
- ★★**검증(b) sector-z mechanism 분해 = team-lead 핵심 입증 (measure.py sector_z_decomposition)**:
  - pbr 24M: universe-z IC=−0.077 / **sector-neutral-z=−0.146(진짜)** / **sector-LEVEL-component=+0.157(부호 반대!)**.
  - ev_ebitda 24M: uni=−0.033 / secN=−0.117 / sectorLevel=**+0.331(부호 반대 강)**.
  - ★해석: within-sector value(싼 종목)=forward 양수익(IC−0.146). sector-LEVEL value(싼 sector)=forward 음(+0.157=sector value trap). universe-z가 이 **두 반대 성분 mixing → 희석(−0.077)**. sector-neutral이 sector-level 반대성분 제거 → within value 순수 추출. = ★**line 322(sector 내 factor 없어 ≈0)와 정반대 mechanism — sector 간 level 차이가 forward 반대작용하는 걸 제거**. ⛒모순 아님, BY 8 = 진짜 신호. per은 uni/secN/sectorLevel 셋 다 ≈−0.02~−0.05 = per 무신호(peak-EPS) 일관.
- **검증(b 한국)**: battery 단일산업 universe-z vs sector-neutral-z = **max abs diff 0.00e+00 = byte-identical** = 한국 7산업 sector-neutral 전환 무회귀 입증.
- **검증(c) per_z coverage artifact**: shares 47종 per_z 24M t−2.48 → 60종 보강 t−1.16 약화. = 기존 "유의" = 누락 13종(dei) artifact. → summary.yaml 박제 + candidate-ledger evt + 본 로그.
- ★생존 robustness(measure.py 통합): pbr_z leave-year stable=True(ex-range −0.08~−0.15) + long-only net 6M+4.4%/12M+10.0%. ev_ebitda leave-year stable + net +4.2%/+8.4%. = pbr=BY+M_eff+OOS+within+LOO-sector+leave-episode+net-cost+mechanism 전부 통과 CONFIRMED.
- probe 파일 6종 → measure.py 통합 후 삭제(leave_year_ic/long_only_net/sub_sector_n/sector_z_decomposition 함수화). validation-metrics-v3.json 에 verify_a/verify_b/survivor_robustness 박제.

## ★★ 양식 자산 — sector_z_decomposition mechanism (다음 sleeve 재사용 의무, team-lead 지시)

> **us_defensive / us_mega_tech 도 같은 3분해 적용**. universe-demean → sector-neutral 전환 시 BY 회복 가능성 = 본 mechanism 으로 진위 판별.

### 1. 문제 패턴 (재발 감지)
- multi-sector sleeve(미국 = 5 sector × N)에서 measure.py `cs_z` 가 **universe-wide demean**(`panel.mean(axis=1)`) 쓰면 = frame §M.7 line 267-269 "within-industry peer-relative sector-neutral z" 계약 위반 버그.
- 증상: family_1 BY 생존 0 (신호 희석). 한국 단일산업에선 안 보임(universe=sector 1개 = byte-identical).

### 2. 진단 도구 = sector_z_decomposition (measure.py 함수, 재사용)
신호를 3개로 분해 측정:
- **universe-z IC**: 기존 방식(희석된 값).
- **sector-neutral-z IC**: 각 월 sector 내 demean/std (진짜 within-sector 신호).
- **sector-LEVEL-component IC**: 각 종목을 자기 sector 의 universe-z 평균으로 대체한 신호(sector 간 level 차이만).

### 3. 판별 규칙 (★진짜 신호 vs line 322 artifact)
- **sector-LEVEL-component 부호가 within과 반대 (또는 ~0)** + **sector-neutral IC > universe IC (절대값)** → ★sector-neutral 정당. universe-demean 이 sector-level 반대성분 섞어 희석한 것. (us_cyclical = 이 케이스: within value 음=양수익 / sector-level value 양=음수익 trap / universe 희석).
- **sector-LEVEL-component ≈ within 같은 부호 + sector-neutral IC ≈ universe** → sector-level 이 신호 주력 = sector-neutral 무력(frame line 322 = artifact 의심).
- **within-sector z cross-std ≈ 1** (0 아님) 확인 = over-neutralize(신호 소멸) 아님.

### 4. us_cyclical 실측 (양식 example)
- pbr 24M: uni −0.077 / secN −0.146 / sectorLevel **+0.157(반대)** → sector-neutral 정당.
- ev_ebitda 24M: uni −0.033 / secN −0.117 / sectorLevel **+0.331(반대 강)** → 정당.
- per: uni/secN/sectorLevel 셋 다 ≈−0.02~−0.05 (무신호 일관, 분해해도 약).
- ★경제적 해석 = "sector value trap": 싼 sector(저PBR sector)는 forward 저수익(sector-level value trap), 싼 종목(sector 내 저PBR)은 forward 고수익(within value). 둘이 반대라 universe-demean 이 상쇄.

### 5. 무회귀 보장
단일산업(한국) = sector 1개라 sector-neutral == universe-demean **byte-identical**(battery diff 0.00e+00). INV_R15_WEIGHTS off=byte-identical 정합. → 한국 7산업 소급 전환 무영향.

## 미해결 / 다음 세션 우선 작업
1~6. ✅ S1 리서치 / shares 재수집 / sector-neutral 발견 / team-lead 확정 / 검증 a/b/c / summary.yaml+15axis-audit+candidate-ledger 작성 완료
7. team-lead 완료 보고 → G-C 독립 audit teammate 별도 스폰(self-audit 초안 + validation-metrics-v3.json + mechanism 입력)
8. ★us_defensive/us_mega_tech 재작업 시 §양식자산 sector_z_decomposition 적용 의무
