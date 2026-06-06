<!-- author: us-cyclical teammate (재작업 2026-06-03, sector-neutral z 정식) -->
<!-- ★본 파일 = G-A self-audit 초안 (author 작성). G-C 독립 audit = 별도 세션(author != auditor)이 하단에 추가 -->
<!-- audit_date: 2026-06-03 -->

# 15axis-audit.md — us_cyclical sleeve §M v3 (frame v3 §E, A~P 15축) — ★재작업 sector-neutral

> ★재작업 = (1) S1 신규 신호(EDGAR 12 concept) (2) 자문 R2 4수정 (3) ★방법 결함 교정(universe-demean → sector-neutral z, BY 0→8).
> raw 재현 = `raw-v3/{collect,measure}.py` → `validation-metrics-v3.json`. Hard-fail 코어: **B·C·D·I** + 조건부 J~P.

## G-A.1 — 15축 (A~P) 3컬럼 (① 적용했나 ② 측정법·코드/수치 경로 ③ 결과·판정)

| 축 | ① 적용 | ② 측정법·경로 | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론 실재 | YES | S1 학술 ground theory-notes.md. Cooper-Gulen-Schill(2008 JF)/Novy-Marx(2013 JFE)/Barbee-Mukherji-Raines(1996 FAJ)/Fama-French(1989 JFE) 환각검증 CONFIRMED. archetype valid_from 2015-01 사전선언. | **PASS** — peak-EPS-robust value(PBR/EV-EBITDA) 1차 문헌 ground. |
| **B**★ 실데이터 | YES | 합성 0%. yfinance 60종(2867일) + EDGAR XBRL **12 concept 94650 rows**(filed PIT, dei fallback) + FRED(HY/baa_aaa/rate/vix) + DXY. collect.py 재현. | **PASS** — assets 60/60, shares 60/60(dei). |
| **C**★ 추적성 | YES | yaml 수치 → validation-metrics-v3.json key 1:1. pbr_z__12M IC −0.1172 / ev_ebitda −0.1095 / verify_b sector_z_decomposition / src_concept 박제. | **PASS** — yaml↔raw 매핑·src_concept 추적. |
| **D**★ PIT | YES | 가격 forward-shift(shift(-h)) safe. valuation = EDGAR filing acceptance date(filed) 이후만(`_latest_pit`/`_ttm`/`_asset_yoy` filed_dt<=dt). 거시 FRED. | **PASS** — lookahead 회피(Large accel 60d/40d 자동). |
| **E** 자문 환각 | YES | S1 citation 7개 Gemini 교차검증: 6 CONFIRMED + 1 CORRECTED(Barbee "Jeong→Mukherji-Raines", "2008→1996"). archive raw 박제. | **PASS** — 환각 1건 정정 박제. |
| **F** 반증+기각 | YES | falsifier = reject_signal(e-CUSUM 부호반전). 기각 결과: **asset_growth REJECTED**(OOS 부호반전 decay −0.74, 문헌 2015~ crowding) / momentum·vol 약(sector-neutral 후 비유의). | **PASS** — falsifier 정의 + 실제 기각(asset_growth/mom/vol). |
| **G** 검정력·tier | YES | n_effective(125mo) + ts_eff_n(eff_N 이중보정 T/h) + breadth_ir. eff_n_tier=Validated. ★sector당 12종 = small-n hedge 라벨. | **PASS** — tier 라벨 + small-n hedge. |
| **H** 미해결 의문 | YES | collector_plan: survivorship(high) + ERB(high, IBES 유료) + HY OAS 장기(medium, Baa-Aaa proxy) + accruals(low). candidate-ledger 연결. | **PASS** — 미해결 ledger 연결. |
| **I**★ 생존편향 | YES | universe = 현 ETF holdings 큐레이션(생존 종목). 상폐/구성변경(GE 분할/셰일 파산) 누락. yfinance 단독 = 상폐 ticker 누락. | **PARTIAL** — 정직 격하, Sharadar/S&P historical = collector_plan high. |
| **J** 경제성·거래비용 | YES | US net-cost = commission 0.0005 + spread/2 0.0003 = 왕복 16bps(STT 없음). long_only_net = pbr 12M +10.0% / ev +8.4%(거래비용 차감 후). | **PASS** — long-only-implementable net IC. |
| **K**★ 다중검정 | YES | ★family_1 BY + M_eff(Li-Ji eigenvalue, test-stat 상관행렬). raw m=36 → M_eff=20.0. threshold 0.00137. ★survivors=8(pbr/ev_ebitda 전 horizon). nondegenerate strip=6. | **PASS** — M_eff BY 적용, 생존 8(degenerate strip 6). |
| **L** 통합 상관 PSD | YES(보고만) | common_factor_exposure = β 보고만(hy_oas/baa_aaa/rate/vix/dollar). 통합 supervisor L축 1회 계상. | **PASS** — sleeve=보고만. |
| **M**★ wire 충실 | YES | rank_ic/score_ic_breakdown_eprocess(confidence_hooks) = weight_falsification 호출. measure.py opt-in, production 미변경. cs_z(secmap) 단일산업=byte-identical. | **PASS** — opt-in, 단일산업 무회귀. |
| **N**★ cross PSD | N/A | cross 조립(RegimeGlasso/DY) = supervisor. directional_spillover=[]. | **N/A** — supervisor 몫. |
| **O**★ leakage | YES | forward=shift(-h). valuation=filed date 이후만. reject≠missing: 적자/결측 valuation NaN(missing) tri-state 정직 제외(silent default 0). | **PASS** — PIT-safe + tri-state. |
| **P** net-cost robustness | YES | US 왕복 16bps. pbr/ev 저회전(value 12M+) net 유리. long_only top-quintile net +8~10%. | **PASS** — net 후 신호 생존. |

→ **Hard-fail 코어 B·C·D = PASS, I = PARTIAL(정직 격하). M·O = PASS, N=N/A. hard-fail 0.**

## G-A.2 — 6단계 (S1~S6) 산출물 경로 + 1줄 결과

- **S1** 학술 ground: `theory-notes.md` + `candidate-ledger.md`(Gemini 2-Phase + citation 환각검증). → peak-EPS-robust value 발굴, asset_growth/Baa-Aaa 채택.
- **S2** 실측 4게이트: `measure.py` G1 ex-ante(valid_from 2015) / G2 **BY-FDR + M_eff**(family 3분리) / G3 CPCV(purge=h+embargo) / G4 NW-HAC(+block-boot). → pbr/ev_ebitda BY 생존 8.
- **S3** 외부검토: S1 자문(.consult-us-method R1/R2) + frame §M.7/§M.12 대조. → sector-neutral 계약 위반 발견.
- **S4** 재검증: leave-year(11연도) / within-period(0.91) / LOO-sector / OOS walk-forward / long-only net / sub-sector 부호 / sector-z 3분해. → pbr 전 robustness 통과.
- **S5** 역공격: line 322 경고(sector-neutral 13~17종 ≈0) 직접 투척 → 검증 b mechanism(sector-level value trap)으로 반박, BY 8 진짜 입증.
- **S6** ★15축 독립 audit = **G-C 별도 세션**(본 파일 = author self-audit 초안, 하단 G-C 미작성 = 독립 teammate 몫).

## G-A.3 — cross 3종 (sleeve=보고만)

- **동시 RegimeGlasso**: common_factor β 보고만(hy_oas −0.120/baa_aaa −0.113/vix −0.008/dollar −1.04/rate +0.003) → supervisor Σ_return.
- **방향성 Diebold-Yilmaz**: directional_spillover=[] (supervisor 통합).
- **구조 supply-chain**: AI capex→Mag7 = us_mega_tech(T0) 영역, skip(us_cyclical=macro regime+value dominant).

## G-A.4 — ★sub-sector 부호 일관성 (team-lead 신설 게이트)

| 신호 | semi | materials | industrials | energy | financials | 판정 |
|---|---|---|---|---|---|---|
| **pbr_z** (CONFIRMED) | −0.114 | −0.000 | −0.168 | −0.328 | −0.033 | ★전 5 음 일관(materials ≈0 약하나 cancel 아님). LOO 5sector −0.09~−0.18. **슬리브 유지** |
| **ev_ebitda** (CONFIRMED) | −0.068 | −0.080 | −0.185 | −0.355 | **+0.060** | financials만 양 = ★EV/EBITDA 은행 부적합 **개념차**(은행 EBITDA 무의미), cancel 아님 → financials sector-conditional 제외. **슬리브 유지** |
| per_z (TENTATIVE) | −0.014 | +0.003 | −0.026 | −0.117 | −0.176 | energy/financials만 음 강, semi/mat/ind ≈0 = per 자체 약(peak-EPS) |
| sales_yield (TENTATIVE) | +0.227 | +0.089 | +0.101 | +0.272 | +0.083 | 전 5 양 일관(방향), 단 unconditional 약·OOS 불안정 |

→ ★**부호 cancel 로 인한 슬리브 분리 트리거 없음**. financials EV/EBITDA 개념차만 sector-conditional 제외(A-4 단서 "개념차 vs cancel 구분"). cyclical = 슬리브 단위 유지 확정.

## G-A.5 — ★sector-neutral mechanism 입증 (검증 b, team-lead 핵심)

> frame line 322 "sector-neutral z가 13~17종 demean이면 중립화 ≈0" 경고 vs 본 발견(sector-neutral로 BY 0→8) 충돌 해소.

**sector-z 3분해** (measure.py `sector_z_decomposition`, validation-metrics-v3.json `verify_b`):

| 신호 | universe-z IC | sector-neutral-z IC | sector-LEVEL-component IC |
|---|---|---|---|
| pbr 12M | −0.047 | **−0.117 (진짜)** | **+0.140 (★부호 반대)** |
| pbr 24M | −0.077 | **−0.146** | **+0.157 (부호 반대)** |
| ev_ebitda 12M | −0.016 | −0.110 | **+0.252 (부호 반대 강)** |
| ev_ebitda 24M | −0.033 | −0.117 | **+0.331 (부호 반대 강)** |
| per 12M | −0.014 | −0.021 | −0.021 (셋 다 약 = per 무신호 일관) |

★**mechanism 규명**: within-sector value(싼 종목 overweight)=forward **양수익**(IC −0.117). 그런데 sector-LEVEL value(싼 sector overweight)=forward **음수익**(+0.140 = sector value trap). universe-demean z는 이 **두 반대 부호 성분을 섞어 신호 희석**(−0.047). sector-neutral z는 sector-level 반대성분을 제거 → within value 순수 추출.
→ ★frame line 322는 "sector 내 factor 없어 sector-neutral 무력(≈0)"인데, us_cyclical은 **부분 반박 + hedge 흡수**(★G-C 정밀화): line 322 over-neutralize(분산 소멸) 우려는 cross-std≈1(분산 보존)로 **기각**, 단 small-N(sector당 12종) 우려는 **여전히 적용 → hedge 흡수**(= "완전 반박" 아님). mechanism 방향(within value 강 + sector-level trap 상쇄)은 raw 지지. **BY 8 = 진짜 신호(G-C 독립 재현 raw_p 0.46→0.0018).**
> ★G-C hedge 의무: (1) "universe-z = within + sector-LEVEL **가산**" framing = ⛔IC 단순 가산 항등식 아님(Spearman IC 비선형, 부호 상쇄 직관). (2) sector-LEVEL trap magnitude(+0.140) 인용 시 **n_sector=5(매월 5점) = pbr sector-level t1.36~1.92 비유의~경계, ev_ebitda 만 강유의(t4.6~5.1)** 라벨 부착 = 방향만 신뢰, magnitude over-claim 금지.

**검증(a) sub-sector N**: 각 sector static 12종, pbr 월별 median 9~12종. within-sector z cross-std=0.962(pbr)/0.944(ev) ≈1 = over-neutralize 아님(line 322 신호소멸 미발생). financials EV/EBITDA median 4종 = 개념 부적합 + small-N → 제외. ★sector당 12종 = small-n hedge(magnitude 보수).

**검증(b 한국 무회귀)**: battery 단일산업 universe-z vs sector-neutral-z = max abs diff **0.00e+00 byte-identical** = 한국 7산업 sector-neutral 전환 무회귀 입증(INV_R15_WEIGHTS off=byte-identical 정합).

**검증(c per coverage artifact)**: shares 47종(dei 13종 결측) per_z 24M t−2.48 → 60종 보강 t−1.16 약화. 기존 "유의" = 누락 13종 artifact(candidate-ledger evt).

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (EDGAR 12 concept 94650 rows, dei fallback) |
| C 추적성 | PASS | yaml↔raw 매핑 + src_concept |
| D PIT | PASS | filed-date PIT + forward shift |
| I 생존편향 | PARTIAL | 현 holdings 큐레이션, 정직 격하 |
| M wire | PASS | opt-in, 단일산업 byte-identical |
| N cross PSD | N/A | supervisor 몫 |
| O leakage | PASS | PIT-safe + reject≠missing tri-state |

★**hard-fail 0** (B/C/D/M/O PASS, I PARTIAL=정직 격하, N=N/A).

## verdict (self-audit 초안)

- **status = PARTIAL_CONFIRMED** — 개별 PBR/EV-EBITDA = CONFIRMED(BY 생존 + 전 robustness), sleeve 종합 = sector당 12종 small-n + survivorship PARTIAL.
- ★핵심 = 미국 cyclical peak-EPS-robust value(PBR/EV-EBITDA) sector-neutral CONFIRMED = 한국 auto/반도체(PBR○ PER✗ peak-EPS) **정합**.
- ★방법 발견 = universe-demean(결함) → sector-neutral z(frame §M.7 계약) = BY 0→8 회복. mechanism = within value 강 + sector-level trap 상쇄 제거.
- asset_growth REJECTED(decay), per/sales_yield TENTATIVE.
- ★전 sleeve(us_defensive/us_mega_tech) sector-neutral 전환 필요(양식 자산).

---

## ★G-C 독립 audit (별도 세션 = author ≠ auditor, team-lead 스폰 예정)

> 본 섹션 = G-C 독립 teammate 작성 영역. author(us-cyclical)는 미작성.
> 1순위 검증 = sector-neutral mechanism(검증 b) 재확인 + M_eff/degenerate + line 322 대조 + hard-fail B/C/D/I+M/N/O = 0.
> 입력 = 본 self-audit 초안 + validation-metrics-v3.json(verify_a/verify_b/survivor_robustness) + measure.py.

<!-- author: us-cyclical-audit teammate (G-C 독립 세션, Opus 1m, 2026-06-03). author(us-cyclical)와 별개. -->
<!-- raw 재계산 = raw-v3/_gc_audit_recompute.py / _gc_audit2.py / _gc_audit3.py (stdout = _gc_audit_out{,2,3}.txt). measure.py 함수 재사용 + 결과 raw 재검증. ⛔ 산출 수정 0. -->

> **독립성 선언**: self-audit 초안 결론을 복붙하지 않고, validation-metrics-v3.json 의 모든 핵심 수치를 raw 데이터(prices/edgar/macro/universe.parquet)로 **재계산**해 대조함. measure.py 의 함수는 재사용하되, BY/M_eff/sector-z 분해/byte-identical/sector-LEVEL 유의성은 독립 스크립트로 재산출함.

### 0. 검증 방법 — author 수치 재현 여부 (선결)

| 항목 | author json | 독립 재계산 | 일치 |
|---|---|---|---|
| ic_universe_z (pbr 12M) | −0.0470 | **−0.0470** | ✓ |
| ic_sector_neutral_z (pbr 12M) | −0.1172 | **−0.1172** | ✓ |
| ic_sector_level (pbr 12M) | +0.1398 | **+0.1398** | ✓ |
| M_eff (Li-Ji) | 20.03 | **20.03** | ✓ |
| BY rank1_thr (M_eff) | 0.00137 | **0.00137** | ✓ |
| survivors_BY (M_eff) | 8 | **8** (동일 set) | ✓ |
| nondegenerate strip survivors | 6 | **6** (동일 set) | ✓ |
| cross-std (pbr/ev) | 0.962/0.944 | **0.961/0.944** | ✓ |
| battery byte-identical | 0.00e+00 | **0.00e+00** (semi 12종 단일산업) | ✓ |
| EDGAR rows | 94650 | **94650** (filed/val null=0) | ✓ |

→ ★**author 의 모든 핵심 정량 수치 = 독립 재현 성공.** 위조·날조 없음. self-audit 초안은 raw 와 정합.

---

### 1순위 — sector-neutral mechanism (BY 8 = 진짜 신호 vs artifact) → **CONFIRMED (진짜 신호, 단 1 hedge)**

**판정 = sector-neutral BY 8 회복은 진짜 신호다. sector-demean artifact 가설은 raw 로 기각된다.** 근거 5종:

1. **universe-demean → sector-neutral 전환 = BY 0→8 실측 재현** (★self-audit 핵심 주장 독립 확인).
   secmap=None(universe-demean) 으로 z 재계산 시 survivors_BY = **0** (raw_m=36, M_eff=18.01). secmap 전달(sector-neutral) 시 **8**. 핵심 신호 raw_p 대조:
   | 신호 | universe-demean p | sector-neutral p |
   |---|---|---|
   | pbr_z 12M | **0.4603** (완전 비유의) | **0.0018** |
   | ev_ebitda 12M | 0.7418 | 0.0009 |
   | pbr_z 24M | 0.4284 | 0.0005 |
   | ev_ebitda 24M | 0.4694 | 0.0000 |
   | pbr_z 3M | 0.1772 | 0.0004 |
   → z 표준화 방식 차이만으로 raw_p 가 0.46→0.0018 로 이동. 이건 코드 트릭이 아니라 **sector mixing 제거의 실측 효과**.

2. **sector-LEVEL value trap (+0.140 부호반대) 진짜** — cross-SECTOR IC 직접 재계산.
   5 sector 평균 z(싼정도) vs sector 평균 12M forward 의 cross-sectional IC = **+0.2072** (125개월). 양수 = 비싼 sector 가 더 오름 = 싼 sector overweight = forward 음수익 = **value trap 실재**. sector-LEVEL component NW t: **ev_ebitda 12M t=+5.05 / 24M t=+4.63 (강유의)**, pbr 12M t=+1.92 / 24M t=+1.36 (약유의~경계). → universe-demean 이 이 반대부호 forward 신호를 섞어 within value 를 희석한 게 맞음. sector-neutral 이 그걸 제거하는 것 = 정당.

3. **within-sector value 신호가 단일 sector 의존 아님 (LOO sector)**.
   pbr_z sector-neutral 12M IC, sector 하나씩 제외:
   semi −0.138 / materials −0.135 / industrials −0.102 / energy −0.068 / financials −0.146 → **전부 음, 부호 일관**. energy 제외 시 가장 약해지나(−0.068) 부호 유지 = 신호가 energy 한 sector 에 몰린 게 아님. ev_ebitda 도 동일(−0.072~−0.160 전부 음).

4. **OOS 견고** — pbr_z 12M CPCV oos_ic=−0.109 oos_hit=**1.0**, leave-year stable=True (range −0.099~−0.145). ev_ebitda 동일(oos_hit 1.0). in-sample overfit 아님.

5. **momentum/vol "인위 sector 신호" 주장 재현** — vol_60 3M universe IC +0.073(t=2.02) → sector-neutral +0.044(t=1.53), mom_6 3M universe +0.059(t=2.40) → sector-neutral +0.017(t=0.89). universe-demean 에서 유의하던 mom/vol 이 sector-neutral 후 비유의 = self-audit 의 "sector mixing artifact" 주장 실측 정합.

★**1 hedge (self-audit 미명시 약점)**: frame line 322 경고("sector-neutral 13~17종 demean 이면 ≈0")는 **over-neutralize(분산 소멸)** 우려인데, cross-std 0.961/0.944≈1 로 **이 우려는 기각됨** (분산 보존). 단 line 322 의 더 근본 맥락 = **sector 당 종목수가 작으면 within-sector 통계가 불안정**. us_cyclical 은 sector 당 12종으로 한국 단일산업(13~17종)보다 **오히려 더 작다**. 그리고 sector-LEVEL value trap 의 핵심 근거인 cross-sector IC(+0.207)는 **매월 단 5점(n_sector=5)** 으로 계산됨 = 통계적 근거가 극도로 얇음(pbr sector-LEVEL t=1.36~1.92 = 비유의~경계, ev_ebitda 만 강유의). → mechanism 의 **방향**(within value 강 + sector trap 상쇄)은 raw 로 지지되나, sector-LEVEL trap 의 **magnitude·유의성**은 n_sector=5 로 over-claim 위험. self-audit 이 이 n_sector=5 한계를 명시하지 않은 것 = CONDITIONAL 요소.

**1순위 verdict = CONFIRMED (sector-neutral BY 8 = 진짜 신호). 단 sector-LEVEL trap magnitude 는 n_sector=5 hedge 라벨 부착 권고.**

---

### 2순위 — M_eff / degenerate → **PASS**

- **M_eff=20.03 재현** (raw_m=36, Li-Ji eigenvalue, IC 시계열 상관행렬). near-dup(pbr/ev_ebitda horizon 강상관)을 36→20 으로 축소 = 적절. BY threshold (1/m)·q/cm 수식 독립 검증: m=20.03 → cm=3.6454 → rank1_thr=**0.00137** (json 일치).
- **degenerate strip 재현**: 24M_value 제외 → raw_m=27, M_eff=17.0, survivors=**6** (pbr 3/6/12M + ev_ebitda 3/6/12M, json 동일 set). 24M overlap(eff_N≈4.7) 강등은 frame §M.12 정합.
- BY q=0.10 사용(FDR level). 표준 BY-FDR. raw_m 기준이면 survivors=7, M_eff 기준 8 (ev_ebitda 3M 추가). M_eff 가 약간 관대하나 Li-Ji 의 정당한 적용 = PASS.

---

### 3순위 — hard-fail B/C/D/I + M/N/O 독립 재판정

| 축 | self-audit | 독립 재판정 | raw 근거 |
|---|---|---|---|
| **B** 실데이터 | PASS | **PASS** | EDGAR 94650 rows, filed/val null=0, 합성 0. assets 60/60·shares 60/60·equity 59/60 tickers. 12 concept 실재. |
| **C** 추적성 | PASS | **PASS** | yaml IC −0.1172/−0.1095 = json key 1:1 (재현). src_concept 박제. |
| **D** PIT | PASS | **PASS** | filed−end lag: min=7d median=221d max=1680d, **negative lag 0/94650 (0.00%)** = lookahead 위험 없음. 가격 forward-shift safe. |
| **I** 생존편향 | PARTIAL | **PARTIAL (정직, 동의)** | universe=현 ETF holdings 큐레이션 = 생존종목. 상폐 누락 정직 격하. collector_plan high 등록 확인. over-claim 아님. |
| **M** wire | PASS | **PASS** | 단일산업 byte-identical 0.00e+00 재현(semi 12종). opt-in, production 미변경. |
| **N** cross PSD | N/A | **N/A (동의)** | cross 조립=supervisor 몫, directional_spillover=[]. sleeve=보고만. |
| **O** leakage | PASS | **PASS** | forward=shift(−h), valuation=filed 이후만, reject≠missing tri-state(적자/결측 NaN). silent default 0 회피 확인. |

→ ★**hard-fail 코어 B·C·D·M·O = PASS, I = PARTIAL(정직), N = N/A. hard-fail = 0.** self-audit 와 일치.
★한국 battery byte-identical(0.00e+00) = 무회귀 입증 = **재현 확인** (단일산업이면 sector-neutral z 가 universe-demean z 와 수학적으로 동일 → 한국 7산업 sector-neutral 전환해도 결과 불변).

---

### 4순위 — per artifact + ledger(G-D) → **PASS**

- **per coverage artifact**: shares concept = **60/60 tickers** 가용(dei fallback 적용 후). net_income = 59/60 (per = mktcap/ttm_ni, ni>0 만 → avg_universe_n 47~48). self-audit 의 "shares 47→60 dei fallback, per_z 24M t−2.48→−1.16 약화" 서술 정합 — dei(EntityCommonStockSharesOutstanding) fallback 으로 13종 보강된 게 맞음. per 약화는 coverage artifact 정정 결과.
- **candidate-ledger**: evt 자산 2종(universe-demean 결함 + per coverage artifact) 박제 확인. S1 자문 raw→산출 매핑(factors 13 + macro 6축 누락 0) 박제. research-log mechanism 시계열 박제. G-D 충실.
- **sector-neutral 출처 검증**: 자문 R2 에 sector-neutral 언급 0 → 이건 자문 권고가 아니라 author 가 frame §M.7 line 267-269 계약을 읽고 발견한 것 = candidate-ledger evt 기록과 정합(S3 외부검토 frame 대조에서 발견). appeal-to-consult 오류 없음.

---

### ★sector-neutral 타당성 최종 verdict

**CONFIRMED — sector-neutral BY 8 회복은 진짜 신호다. artifact 가설은 raw 로 기각.**

- within-sector value 신호(pbr −0.117 / ev_ebitda −0.110)는 (a) LOO sector 전부 음 (b) CPCV oos_hit 1.0 (c) leave-year stable = 견고. universe-demean 에서 raw_p 0.46(비유의)이던 게 sector mixing 제거만으로 0.0018 로 = sector mixing 이 신호를 실제로 희석하던 것.
- ★단 **2 hedge 의무**: (1) sector-LEVEL value trap 의 magnitude/유의성은 **n_sector=5** 로 계산 = pbr 은 비유의~경계(t=1.36~1.92), ev_ebitda 만 강유의 → trap magnitude(+0.140) literal 인용 시 "n_sector=5, pbr 비유의" 라벨 의무. (2) sector 당 12종 = small-n, within-sector 통계 불안정 잔존 = magnitude 보수(self-audit 의 small-n hedge 라벨 유지 타당).
- mechanism 의 **방향**(within value 강 + sector-level trap 상쇄)은 raw 지지. **frame line 322 모순 아님** = 정합(line 322 는 over-neutralize 우려인데 cross-std≈1 로 분산 보존 입증). 단 line 322 의 small-N 우려 자체는 us_cyclical 에 **여전히 적용**(sector당 12종) = self-audit 이 이를 "정반대 mechanism" 으로 완전 반박했다고 한 건 약간 over-claim, 정확히는 "over-neutralize 우려는 기각, small-N 우려는 hedge 로 흡수".

---

### self-audit 초안과의 불일치

| 항목 | self-audit 초안 | 독립 audit 발견 |
|---|---|---|
| 가산성 framing | "universe-z ≈ within-sector-z **+** sector-LEVEL-component" (line 73, ledger) | ★IC 단순 가산 미성립(−0.117+0.140=+0.023 ≠ uni −0.047). Spearman IC 는 비선형이라 가산 안 됨 = **직관적 분해 framing 이지 수학적 항등식 아님**. 결론(sector mixing 희석)은 raw 지지되나, "가산" 표현은 오해 소지 → "두 반대부호 성분이 섞여 희석"(부호 상쇄 직관)으로 읽어야 정확. ⚠️ 격하 아님, framing 정밀화 권고. |
| sector-LEVEL trap n | self-audit 미명시 | ★cross-sector IC = **n_sector=5** 매월 계산. pbr sector-LEVEL t=1.36~1.92(비유의~경계). magnitude over-claim 위험 — hedge 라벨 누락. |
| line 322 반박 강도 | "정반대 mechanism, 모순 아님" | over-neutralize 우려는 기각(cross-std≈1) 정확. 단 line 322 small-N 우려는 us_cyclical(sector당 12종)에 **여전히 적용** = "완전 반박" 아닌 "부분 반박 + hedge 흡수". |

→ ★모든 불일치 = **framing 정밀화 수준** (정량 결론 격하 아님). 위조·날조·계산오류 0. self-audit 의 핵심 주장(BY 0→8 진짜, hard-fail 0, sector-neutral 정당)은 raw 로 전부 지지.

---

### verdict_label 판정

★**PARTIAL_CONFIRMED 동의.** 근거:
- 개별 PBR/EV-EBITDA sector-neutral = CONFIRMED 타당(BY 생존 + LOO + leave-year + CPCV oos_hit 1.0 + long-only net +8~10% 전부 재현).
- sleeve 종합 PARTIAL 격하 정당: (a) survivorship PARTIAL (현 holdings) (b) sector당 12종 small-n (c) sector-LEVEL trap n_sector=5 hedge.
- ⛔ **CONFIRMED 로 승격 불가** — survivorship 미보정 + small-n(sector당 12종 < frame line 322 경고 기준 13~17종) = PARTIAL 상한. self-audit 의 PARTIAL_CONFIRMED 가 정확.

★**G-C 추가 권고 (team-lead 전달, ⛔ 코드 수정은 안 함)**:
1. sector-LEVEL value trap 인용 시 "n_sector=5, pbr sector-LEVEL t=1.36~1.92 비유의~경계, ev_ebitda 만 강유의" hedge 라벨 부착 (summary.yaml `sector_z_mechanism` + 15axis G-A.5 의 "+0.140 부호반대" 옆).
2. "universe-z = within + sector-LEVEL **가산**" framing → "두 반대부호 성분 섞여 희석"(부호 상쇄 직관)으로 정밀화 (IC 가산 항등식 아님 명시).
3. line 322 "정반대 mechanism, 완전 반박" → "over-neutralize 우려 기각(cross-std≈1) + small-N 우려는 hedge 흡수" 로 정밀화.

→ 위 3종은 **정량 결론 격하가 아니라 hedge/framing 보강**. hard-fail 0, BY 8 진짜 신호 확정 = **G-C 독립 audit PASS (CONDITIONAL: hedge 라벨 3종 보강 권고).**
