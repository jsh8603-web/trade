---
tags: [type/study-audit, domain/inv, study/eq_intl, phase/merit-indicators-audit]
date: 2026-06-01
audit_target: raw/validation-merit-eq_intl-20260601.md
auditor: opus 독립 12축 audit subagent (self-certify 회피, raw 직접 재실행)
verdict_종합: 부분 (B/C/I 통과, D 조건부 격하 — credit 동시 CONFIRMED = lookahead artifact)
---

# eq_intl merit 4지표 — 독립 12축 audit

> 방의 self-audit 신뢰 X. validation-merit-indicators.py 전체 독립 재실행 + merit_cache JSON 직접 검사 +
> 동시 CONFIRMED 의 PIT-lag 재정렬 독립 재계산으로 판정.

## §0. Provenance + Recomputation (★제1원리)

**재실행 결과**: `PYTHONUTF8=1 python validation-merit-indicators.py` 독립 재실행 → output.txt 와 **전 수치 bit-exact 일치**.
- jgb contemp Rank-IC +0.047 / credit china contemp +0.413 / fx brazil mom3 −0.432 등 전부 재현.
- §5 다중비교: jgb 0/4, reer 0/20, credit 3/15(전부 contemp), fx 5/30 Bonferroni 생존 — 재현.

**합성 지문 검사 = PASS (실데이터 확정)**:
- merit_cache 21개 JSON (FRED 13 + yfinance 7 + EWT), 파일 크기 realistic (DGS10 1.7MB daily, REER 40KB monthly).
- FXI worst-month 검사: 2008-10 −31.5%, 2011-09 −22.6%, 2022-10 −21.1%, 2008-09 −20.0% = **실 역사 이벤트(GFC·2011·2022 China selloff) 실재**. 합성 시드 아님.
- 결측·갭 실재(`value in ('.','')` skip 분기 작동), ETF n=171~362 실 거래월.

## §1. 12축 verdict

| 축 | 판정 | 근거 (독립 재계산) |
|---|---|---|
| **A 이론** | 부분(soft) | 본 md 는 실측 전담, 이론은 lens/direction.md 위임 — 정상 분업. 날조 인용 0 |
| **B 실데이터 ★** | **충족(hard 통과)** | 전 시리즈 실 fetch, n=83~448, HAC-t/p/95%CI/Rank-IC 박제. 독립 재실행 bit-exact. 합성 아님 |
| **C 추적성 ★** | **충족(hard 통과)** | md 표 수치 = output.txt = 독립 재실행, 오차 0%. 매직넘버 0. (yaml 미수정 상태 — 정상) |
| **D PIT/lookahead ★** | **★조건부 격하** | ↓ 아래 §2 집중 분석. credit 동시 CONFIRMED = revised-vintage + same-Q artifact. md 가 caveat 는 박았으나 **"robust" 라벨이 over-claim** |
| **E 자문비판+환각** | 충족 | primary FRED/yfinance 직측, 외부 prior 인용·환각 ref 0 |
| **F 반증+기각** | **충족** | jgb INSUFFICIENT, reer lead 비유의, credit lead REJECTED(spec drift), fx lead REJECTED = 기각 다수. p-hacking 냄새 없음 |
| **G effective-N** | 충족(tier) | credit quarterly n=83~101(자기상관·effective↓), monthly n=171~362. tier 라벨 처리됨 |
| **H 미해결** | 충족 | §6 5건(동시 vs 예측 분리, credit revised 오염, brazil 부호반전, fx-dollar 중복, JGB regime) 솔직 기재 |
| **I 무결성·생존편향 ★** | **충족(hard 통과)** | ↓ §3. 단, ETF universe 생존편향 부분 caveat 필요 |
| **J 경제유의성** | N/A | 탐구 단계 — 비용·turnover 는 sleeve 승격 시 (정당) |
| **K 다중검정 ★** | 충족 | 지표별 Bonferroni α/m + BH-FDR + raw count 박제. 시도횟수 m=4/20/15/30 공시 |
| **L 통합 상관 ★** | 충족(caveat) | ↓ §4. fx 환(−0.43) vs β_dollar 중복 risk 명시됨 |

## §2. ★D축 집중 — 동시 CONFIRMED 는 lookahead artifact 인가? (최우선)

### 2.1 Vintage 검사 (merit_cache realtime_start)
- QCNPAMUSDA: 전 obs `realtime_start=2026-05-31` 단일 스냅샷 = **완전 revised(최종개정치), first-release vintage 아님**.
- RBCNBIS/RBBRBIS REER: 단일 vintage(2026-05-30/31), 최종 obs 2025-07(credit)·2026-04(REER) = **분기/월 후행발표 + 사후개정**.
- ALFRED first-release vintage **미적용** 확정.

### 2.2 ★결정적 재계산 — same-Q vs PIT-lag(Q+1) 재정렬
credit impulse(Q) 를 **같은 분기 Q ETF return** 이 아니라 **publication-lag 반영 Q+1** 으로 재정렬해 독립 측정:

| 대상 | contemp(same-Q) Rank-IC | **PIT-lag(Q+1) Rank-IC** | 붕괴율 |
|---|---:|---:|---:|
| china (FXI) | +0.413 | **+0.054** | −87% |
| brazil (EWZ) | +0.303 | **+0.010** | −97% |
| korea (EWY) | +0.427 | **−0.046** | −111%(부호반전) |

★**동시 CONFIRMED(+0.30~+0.43) 가 라이브-tradeable 정렬(Q+1)에서 전부 ≈0 으로 붕괴**.

### 2.3 판정 = **lookahead artifact (over-claim)**
- QCNPAMUSDA(Q) 는 분기 종료 후 ~1Q 지연 발표 + 사후개정. **분기 Q 진행 중에는 Q 의 credit impulse 를 알 수 없다.** 동분기 ETF return 과의 +0.41 상관은 "분기 마감 후에야 알게 되는 credit 값" 을 그 분기 수익과 맞춘 것 = 전형적 contemporaneous-PIT 위반.
- Q+1 재정렬 시 신호 소멸(0.05/0.01/−0.05) = **라이브 가치 0**. revised vintage 가 동분기에 미래정보를 스며들게 한 artifact 확정.
- ★md 는 §3 caveat·D축 "부분"·H#2 로 **위험을 정직히 박았으나**, verdict 라벨을 "동시 ★CONFIRMED(robust)" 로 유지 = **over-claim**. AUDIT-GUIDE §2 "통계적 유의 ≠ 라이브 유의", D hard 원리상 **격하 의무**.
- ★대비: **fx 동시 CONFIRMED 는 정당**. FX 일별(DEXxxUS) 단일관측·무개정, unhedged ETF = 현지지수×환율 동월 mechanical 반영. md 가 이를 "예측 alpha 아님 — 현재 환 노출 사이징" 으로 정확히 라벨 → PIT-safe exposure 측정으로 수용 가능.

## §3. I축 — 생존편향·무결성

- ETF = 단일국 대형 ETF(EWJ/FXI/EWZ/EWY/INDA/EWW/EWT), auto_adjust=True(split·배당 TR 반영) = 가격 무결성 PASS.
- ★단 universe 자체가 **생존 ETF only** — FXI/INDA 등은 출시 후 현존하는 대형 펀드. 개별 종목 생존편향은 아니나(지수추종 ETF 라 구성종목 편입·퇴출은 지수가 흡수), **ETF 출시일 이전 기간 부재**(FXI 2004~, INDA 2012~)로 표본이 bull-market 시작점에 편향될 수 있음. I-hard 아님(지수 ETF 는 무효화 수준 생존편향 없음) — soft caveat.
- China credit n=83~101 분기 = effective-N 낮음(자기상관 강). credit impulse 자기상관 → IID 가정 부적. md 가 HAC-t 적용은 했으나 **quarterly regime persistence 미보정** → G tier 라벨 적정.

## §4. L축 — fx 환 vs β_dollar 이중계상

- fx contemp EM(−0.28~−0.43) = USD/local 모멘텀 채널. macro-linkage β_dollar(−1.1~−1.4) = 동일 dollar 채널.
- ★**같은 베팅 중복 risk 실재**. md §6#4 가 "partial-corr(dollar 고정 후 local-fx 잔차) 미측정" 으로 정직히 표기 — 통합 시 공통인자 1회 계상 의무(통합 차단 아님, 통합 단계 게이트).

## §5. spec↔code drift 판정 (E97·§1.3)

- **credit "6-12m 선행 → coincident" 격하 = 타당**. yaml line 159/25 spec="lag=2 선행(예측)" vs 실측 lead 1-4Q 전부 비유의(부분 음 부호반전), 독립 재현. coincident 라벨 정정 정당. **단 §2 에 따라 coincident 조차 라이브 PIT 무효 — "동시 co-move 관측은 가능하나 revised-vintage 이므로 라이브 사이징 불가" 까지 격하 필요**.
- **fx "예측 alpha → exposure 사이징" 격하 = 타당**. lead 전부 비유의 재현, 동시 mechanical exposure 는 PIT-safe → exposure 사이징 용도 정확.

## §6. Hard-fail 종합 (B/C/D/I)

| hard 코어 | 결과 |
|---|---|
| B 실데이터/합성금지 | ✅ 통과 (실 fetch, 합성 지문 0) |
| C 추적성·재현 | ✅ 통과 (오차 0%) |
| **D PIT/lookahead** | ⚠️ **조건부 격하** — credit 동시 "robust" = revised-vintage same-Q artifact(Q+1 붕괴 −87~−111%). fx 동시는 PIT-safe exposure 로 수용 |
| I 생존편향 | ✅ 통과 (지수 ETF·split 조정, ETF 출시일 편향만 soft caveat) |

## §7. 종합 verdict = **부분(PARTIAL)** — register 조건부

- **B/C/I/E/F/K 충족, hard 코어 3/4 통과**. 합성·재현불일치·생존편향 무효화 없음 → 즉시 불충분 아님.
- **D 가 credit 동시 CONFIRMED 의 "robust/CONFIRMED" 라벨을 격하시킴** → 전면 불충분 아니나 **해당 claim 격하 후 register**.

### yaml 반영 격하/보강 항목
1. **`china_credit_impulse`**: lag=2(선행) 박제 격하 = 타당(이미 방이 인지). ★추가 — **coincident 라벨조차 `validated_alpha:false` + `prior_tier:structural_low_confidence`** 로 강등. 동시 Rank-IC 점추정(+0.41) **박제 금지**(Q+1 정렬 시 0). collector_plan 에 **ALFRED first-release vintage 재측정 의무** 명시 — 재측정 후에도 동시상관 잔존해야 라벨 복원.
2. **`fx_carry_momentum`**: 동시 EM exposure = robust 수용. 단 `validated_alpha:false`(예측 alpha 아님), 용도=**현재 환 노출 사이징(exposure beta)** 명시. lead/native 예측 신호 박제 금지.
3. **`real_exchange_rate_valuation`**: structural_low_confidence + validated_alpha:false 유지 적정. brazil +상관 = commodity-통화 동시성(valuation 아님) caveat 유지.
4. **`jgb_ust_spread`**: INSUFFICIENT — base_weight 미부여, line 274 caveat="누락이 결함 아님" 해소 수용.
5. **L축 통합**: fx 환 ↔ β_dollar partial-corr(dollar 고정 후 잔차) 통합 전 측정 의무. 미측정 시 공통인자 중복 계상 → 통합 게이트 보류.
