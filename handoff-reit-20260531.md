---
tags: [type/handoff, study_id/reit, phase/v2-mirror-phase4-completed, status/awaiting-main-collector]
date: 2026-05-31
session_origin: btn-GCP
session_ckpt: ckpt-202605310140:btn-GCP
note: main 통합 재개 entry point. 본 파일 첫 Read 후 study-research/reit/ 산출 + raw + archive 정합 회수.
---

# REIT 자산군 통합 재개 인계 (btn-GCP, 2026-05-31)

## 0. 현재 상태 한눈

| Phase | 상태 | 산출 |
|---|---|---|
| 2-1 자문 다회 (R0 3R 수렴) | ✅ 승인 완료 | `direction.md §1-§7` + `raw/round-{1,2,3}.md` |
| 2-2 이론 학습 + 환각 검증 | ✅ 승인 완료 | `raw/theory-notes.md` (243bp Q3'22 + 2024 industrial -17.7% CONFIRMED. Q4'24 120bp baseline 제외 E축) |
| 2-3 실데이터 5 validation | ✅ 승인 완료 | `raw/validation-{H1..H5}.md` + `raw/scripts/h{1..5}*.py` |
| study_session.yaml v2 (861 lines) | ✅ 작성 완료 | tier=structural prior, `raw/evidence-map.md` 추적성 박제, block8 self_audit_12_axis |
| M3 macro linkage 분석 | ✅ 완료 | `raw/m3-macro-linkage.md` + `raw/scripts/m3_macro_linkage.py(.log)` |
| v2-mirror Phase 2 methodology-brief | ✅ 작성 완료 | `methodology-brief.md` (165 lines, REIT 6 sub-cluster + 6 driver + Q1-Q12) |
| v2-mirror Phase 3 자문 R1+R2+R3 | ✅ 3R 수렴 (R4-R7 생략) | `raw/consult-round-{1,2,3}.md` + archive 6 파일 |
| v2-mirror Phase 3.5 direction.md §8 supplement | ✅ main 승인 완료 | `direction.md §8` (8 cluster + 6 driver + H6-H10 + estimand 변경 + R4 carry 3건) |
| v2-mirror Phase 1 evaluation-axes.md | ✅ 작성 완료 | AUDIT-GUIDE 12축 + REIT application + Phase 6 평가 SSOT, ★supervisor 직접 평가 금지 박제 |
| v2-mirror Phase 4 plan.md | ✅ 작성 완료 | 8 sub-cluster Tier 차등 dispatch table + Phase 5/6/7 prompt + coder-readiness 5항목 PASS |
| v2-mirror Phase 5 sub-cluster opus subagent dispatch | ⛔ **보류 (main 지시)** | subagent 기능 장애 확인 (eq_kr 18 agent 2시간+ stuck) — main verdict 대기 |
| candidate-ledger.md 작성 | ✅ 작성 완료 (main 정정 후 merit 작업큐 전환) | 4 section: 채택 + 이연 (merit 작업큐 전환) + 미채택 + falsifier |
| merit 후보 19종 collector 요청 main 송신 | ✅ ret=0 송신 완료 | main 의 collector 우선순위 verdict 대기 |

## 1. 다음 작업 (재개 시 시작 포인트)

### A. 우선 1순위: main 의 collector 구현 우선순위 verdict 확인
- 본 세션 송신 = REIT merit 후보 19종 + 필요 collector list (FRED public + Census + SEC EDGAR + yfinance public).
- main 의 통합 재개 정책 = "merit 있는 후보 실제 추가 study 다시 하라 — collector 없으면 main 이 구현. 흐름 = main collector 구현 → 본 study (이론→실데이터→상관·Rank-IC) → 12축 audit (별도 subagent) → yaml 박제. 'collector 없음 / 후순위 / 이연' = 탈락 사유 부적격."
- main 의 verdict = 어느 collector 부터 구현하는지, 본 세션은 그 도착 통보 기다림.

### B. 우선 2순위: collector 도착 시 sub-cluster study 재개
- 본 작업방의 8 sub-cluster (C1 Residential / C2 Commercial-Retail / C3 Industrial-Logistics / C4 Datacenter-Infra / C5 Healthcare / C6a Lodging / C6b Storage / C8 mREIT) 별 study (이론 → 실데이터 → 상관·Rank-IC) 작업.
- 흐름:
  1. main collector path/script 수신 → 본 study 진행
  2. cluster 별 산출 = `industries/{NAME}/{round-1, theory-notes, validation-{fundamental,macro,industry}, summary.yaml, 8axis-audit}.md/yaml` 7 파일 (plan.md §1 dispatch table 양식)
  3. 별도 12축 audit subagent (main dispatch) 통과
  4. yaml v3 박제

### C. 우선 3순위: study 후 잔존 후보 candidate-ledger 박제
- main 정정 (2순위) = "study 후도 빠진 것만 ledger 에 '왜 빠졌나 (merit 없음 or 실측 무상관)' 기록"
- 현 candidate-ledger.md = work in progress, ❌미채택 section 만 일부 완성 (환각 catch 4종 + Fisher collinearity + estimand 변경 + primary 미확인 + 자문 그대로 금지). ⏳이연 section = merit 작업큐 전환 (status 갱신).

## 2. 미해결 의문 (R4 carry 3건 + 후속)

### R4 carry (Phase 3 R3 claude critique 우위)
1. **c2/c3/c6 원문 검증**:
   - Beracha-Feng-Hardin 2019 RealEstateEconomics primary PDF (Beracha-Krautz 2022 환각 catch 대체 ref)
   - AMT 10-K 2023 Item 7 VIL Goodwill Impairment 정확 수치 ($3.22B 가설, gemini 박제 vs claude 단정 금지)
   - CCI/AMT 10-K + analyst day churn schedule ($200M-$400M/yr 가설)
2. **H3 sign reversal sector/leverage orthogonalize 재검** — long-WAM 표본의 sector/leverage 와 H3 Rank-IC partial out. He-Xiong 2012 JF Rollover Risk 이론은 long-WAM protective (positive) 여야 함, M3 negative = mechanism 아닌 confounding 의심.
3. **C8 mREIT 전용 가설 신설** — empirical duration gap × curve slope (NLY/AGNC asset-liability mismatch 본질). R3 = equity REIT 9 한정, C8 별도 트랙.

### M3 후속
- VNQ β_rate=−3.82 [real β + breakeven β] 분해 — DFII10 + T10YIE 다중회귀 (Fisher collinearity invariant). R2 expect = real β ≈ −4~−6 / breakeven β ≈ 0~소폭 양수.
- 1990-2020 long-run β_rate 추정 — 2022-2024 epoch 상한 추정치 가설, 장기 시계열 확장 시 |β| 더 작음 expect (학설 inconclusive).

### 가설 후속
- H1 재정식화 ("long-WALT + escalator option = conditional outperform") — Phase 5 validation-fundamental 에서 escalator 구조 (CPI-linked vs fixed) cross-section 검증
- Hotel β_rate +1.79 orthogonalize 후 0 또는 음수 수축 expect (cyclical proxy 확정 vs hedge 가설)
- Tower H8a (organic revenue ~ CPI 계수<1) + H8b (가격 rate 통제 후) 분할 검증
- 다중검정 보정 (Benjamini-Hochberg FDR q=0.10 또는 Bonferroni) — H1-H10 10 가설 + 8 sub-cluster × 6 driver = 48 회귀

## 3. merit 후보 19종 (main collector 요청 list)

### A. 거시 driver 6종 (Fisher collinearity invariant 정합)
| # | 변수 | collector | 우선순위 |
|---|---|---|---|
| 1 | **DFII10** (10y TIPS yield, 실질금리) | FRED CSV `fredgraph.csv?id=DFII10`, 2003-01~ daily | 최우선 (M3 분해 의무) |
| 2 | **T10YIE** (10y breakeven inflation) | FRED `id=T10YIE` | 최우선 (Fisher invariant) |
| 3 | **BAMLH0A0HYM2** (HY OAS) | FRED `id=BAMLH0A0HYM2` | 우선 (REIT 고leverage refinancing) |
| 4 | **Cap-rate spread** (implied REIT NOI/EV − private appraisal) | Nareit T-Tracker 분기 free CSV (reit.com) | 우선 (H2 + H6 anchor) |
| 5 | **Census Construction Put in Place (C30)** | Census Bureau API `api.census.gov/data/timeseries/eits/cn` | 중 (sector supply leading) |
| 6 | **DRSREACBS** (CMBS Delinquency Rate) | FRED `id=DRSREACBS` | 중 (credit channel) |

### B. mREIT C8 별도 driver 4종
| # | 변수 | collector | 우선순위 |
|---|---|---|---|
| 7 | **mREIT 3-ticker** (NLY/AGNC/MFA) | yfinance auto_adjust | 우선 (C8 별도 cluster universe) |
| 8 | **Yield curve slope** (T10Y2Y, T10Y3M) | FRED `id=T10Y2Y`, `id=T10Y3M` | 우선 (mREIT asset-liability mismatch) |
| 9 | **ICE BofA US MBS OAS** | FRED 후보 `id=BAMLC0A0CMOAS` 또는 인접 series 확인 | 중 (mREIT spread risk) |
| 10 | **Book value MTM 시계열** | SEC EDGAR 10-Q 자동 추출 (Annaly 10-Q Item 1) | 하 (4분기 단위) |

### C. R4 carry primary verification 4종
| # | 변수 | collector | 우선순위 |
|---|---|---|---|
| 11 | **AMT 10-K 2023 Item 7** (VIL Goodwill Impairment $3.22B 가설) | SEC EDGAR public | 중 (R4 carry verify) |
| 12 | **CCI/AMT 10-K + analyst day churn schedule** | SEC EDGAR public | 중 (R4 carry verify) |
| 13 | **Beracha-Feng-Hardin 2019 RealEstateEconomics primary PDF** | 학술 무관 (정독) | 하 (학설 ref verify) |
| 14 | **Ling-Naranjo 1997 JREFE 14(3) + 1999 RealEstateEconomics 27(3) primary PDF** | 학술 무관 | 하 (학설 ref verify) |

### D. Universe 확장 후보 4종
| # | 변수 | collector | 우선순위 |
|---|---|---|---|
| 15 | **Gaming REIT** (VICI, GLPI) | yfinance public | 중 (NNN + 긴 WALT + 인플레 전가) |
| 16 | **SFR REIT** (INVH, AMH) | yfinance public | 중 (mortgage-rate inverse) |
| 17 | **Timberland** (WY, RYN) + Farmland (LAND, FPI) | yfinance public | 하 (C7 Alternative cluster) |
| 18 | **Healthcare 세분화** (OHI, SBRA, VTR) | yfinance public | 우선 (H9 event-study cross-section) |

### E. H7 AI capex proxy 1종
| # | 변수 | collector | 우선순위 |
|---|---|---|---|
| 19 | **AI capex proxy** (Nvidia revenue + MSFT/GOOGL/META quarterly capex) | SEC 10-Q quarterly + Nvidia IR | 하 (H7 검증) |

## 4. 재개 포인터 (file paths)

### v2-mirror Phase 1-4 산출 (본 세션 작업방 작업방 작성)
- `D:/projects/Inv/study-research/reit/methodology-brief.md` (Phase 2)
- `D:/projects/Inv/study-research/reit/direction.md` §1-§8 (Phase 2-1 + Phase 3.5)
- `D:/projects/Inv/study-research/reit/raw/consult-round-{1,2,3}.md` (Phase 3 자문 supervisor cross-verify §5)
- `D:/projects/Inv/study-research/reit/evaluation-axes.md` (Phase 1, Phase 6 평가 SSOT)
- `D:/projects/Inv/study-research/reit/plan.md` (Phase 4 작업 계약)
- `D:/projects/Inv/study-research/reit/candidate-ledger.md` (main 정정 후 merit 작업큐)
- `D:/projects/Inv/study-research/reit/progress.md` (ckpt 누적)

### 이전 v2 산출 (직전 세션)
- `D:/projects/Inv/study-research/reit/raw/round-{1,2,3}.md` (Phase 2-1 R0 자문)
- `D:/projects/Inv/study-research/reit/raw/theory-notes.md` (Phase 2-2)
- `D:/projects/Inv/study-research/reit/raw/validation-{H1..H5}.md` + `raw/scripts/h{1..5}*.py`
- `D:/projects/Inv/study-research/reit/raw/m3-macro-linkage.md` + `raw/scripts/m3_macro_linkage.py(.log)`
- `D:/projects/Inv/study-research/reit/raw/evidence-map.md` (C 축 hard pass)
- `D:/projects/Inv/study-research/reit/study_session.yaml` (v2 = 861 lines structural prior tier)
- `D:/projects/Inv/study-research/reit/study_session.yaml.v1.bak` (v1 폐기 X 보존)
- `D:/projects/Inv/study-research/reit/handoff-m3-macro-linkage-20260530.md` (직전 인계)

### archive (외부 자문 raw 6건)
- `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r1-gemini-20260530.txt` (R1-G 4217 chars)
- `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r1-claude-20260530.txt` (R1-C 3921 chars)
- `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r2-gemini-20260530.txt` (R2-G 3466 chars)
- `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r2-claude-20260530.txt` (R2-C 4041 chars, retry with no-search prefix)
- `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r3-gemini-20260530.txt` (R3-G 6282 chars)
- `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r3-claude-20260531.txt` (R3-C 11091 chars, 가장 풍부)

### memory research
- `~/.claude/memory/research/reit-pricing-theory.md`
- `~/.claude/memory/research/reit-validation-methodology.md`
- `~/.claude/memory/research/reit-theory-notes-2-2.md`

### 관련 SSOT
- `D:/projects/Inv/CLAUDE.md` §"멀티에셋 스터디 워크플로"
- `D:/projects/Inv/STUDY-ORCHESTRATION.md` (5-Phase)
- `D:/projects/Inv/STUDY-KIT.md` (§2 v2 + §2.5 8축 + §6 주식 통일 하드룰)
- `D:/projects/Inv/study-research/AUDIT-GUIDE.md` (12축 SSOT)
- `D:/projects/Inv/study-research/eq_kr/methodology-final-for-main-dispatch.md` (v2 7-Phase baseline)
- `D:/projects/Inv/study-research/macro/timeline.md` (M1 분기·epoch)
- `D:/projects/Inv/study-research/macro/raw/m1_factor_linkage.py` (M3 방법론 ref)
- `D:/projects/Inv/study-research/macro/raw/m1-findings.md` (M1 발견 = 주식 rate≈0, dollar 2배)

## 5. 외부 자문 결과 핵심 (3R 수렴, claude critique 우위 누적 12건)

### claude critique 우위
- **R1**: ① C6 Specialty (lodging+storage) 병합 비판 → C6a Hotel / C6b Storage 분리 ② mREIT C8 누락 catch (duration profile 근본 다름) ③ Fisher 항등식 collinearity 경고 ("nominal + real + breakeven 동시 금지, real+breakeven 만") ④ shrinkage/hierarchical Bayes 권고 (over-parameterization risk) ⑤ TIPS missing window fact 정정 (DFII10 2003-01~ daily continuous, M3 sample fully available)
- **R2**: ⑥ β_rate inconclusive 정직성 ("정량 통일 범위 인용 불가, spec/sample 의존")
- **R3**: ⑦ Liu-Mei 1992 정량 β range 오귀속 risk catch ⑧ Ling-Naranjo 2014/2015 phantom catch (1997/1999 대체) ⑨ Green Street citation 부적합 (proprietary, mechanism 자기완결) ⑩ 5게이트 threshold 완화 (0.05→0.03) 금지, estimand 변경 (per-cell → panel-level / pooled cross-section + Newey-West) ⑪ H6 반증 "2 episode" 부적합 (n=2 power 0), episode dwell + Hansen-Hodrick + hit-rate CI 하한 ⑫ H8 분할 (H8a organic revenue ~ CPI / H8b 가격 rate 통제 후) ⑬ H9 event-study (CMS final-rule CAR + cross-section)

### 환각 catch 3건
- Beracha-Krautz 2022 = 환각 → Beracha-Feng-Hardin 2019 RealEstateEconomics 대체
- Ling-Naranjo 2014/2015 = phantom → Ling-Naranjo 1997 JREFE 14(3) + 1999 RealEstateEconomics 27(3) 대체
- Green Street tower longest-duration citation = proprietary, 학술 citation 부적합 → mechanism 자기완결 박제

## 6. 학습 박제 (promotion-log)

- **K-202605301815**: claude-web-consult 호출 시 "DO NOT USE WEB SEARCH OR THINKING" prefix 의무 (search 도중 stop 절단 회피, K-202605291822 학습 정합)
- **K-202605310135**: psmux_send_message body 에 backtick (`https://...`) 직접 X — bash command substitution 으로 잘림 (FRED series ID 살아있어 실해 작음, but 방지책 = backtick 제거)
- **ERROR-202605301740**: psmux_send_message 1차 silent stdout 을 송신실패로 오판 → 2차 retry 송신 = main "중복답신 2회" 라벨 유발. 방지책 = ret=0 = 성공, 자동 retry 금지

## 7. 미커밋 변경 (commit 의무)

본 세션 작업방의 미커밋 변경 = `study-research/reit/` 전체 directory (untracked, single entry git status). 다른 작업방 (commodity, eq_intl, eq_us 등) 변경과 분리 commit 필요 (K-202605300825 multisession-shared-git-index-race 패턴).

다른 세션 변경 = 본 handoff 와 무관, 본 commit 범위 = `study-research/reit/` + `D:/projects/Inv/handoff-reit-20260531.md` (본 파일) 만.

## 8. 본 세션 (btn-GCP) 다음 action

⛔ `/clear` 금지 (main 이 보냄). main 의 통합 재개 dispatch 대기.

main 의 통합 재개 prompt 도착 시:
1. 본 handoff-reit-20260531.md 첫 Read (re-entry)
2. main 의 collector 구현 path/script 확인
3. sub-cluster study 재개 (plan.md §1 Tier 차등 dispatch table 양식)

### 본 세션 결정 / 현재 상태 / 다음 구현 / 경계 (4 필드)

- **결정**: v2-mirror Phase 1-4 자율 완료 + Phase 3.5 main 승인 + Phase 5 보류 (subagent 장애 main 지시) + merit 후보 19종 collector 요청.
- **현재 상태**: idle, main 의 collector 구현 우선순위 verdict 대기. ctx-warn long-mode ON (cap 500k).
- **다음 구현**: collector path/script 수신 후 sub-cluster study (이론 → 실데이터 → 상관·Rank-IC) → 12축 audit subagent (별도 dispatch) → yaml v3.
- **경계**: ⛔ /clear 금지 / supervisor 직접 평가 금지 / 자문 그대로 코드화 금지 / 점추정 prior 박제 금지 / Fisher collinearity invariant / 환각 ref 박제 금지 / multisession shared git index race 회피 (pathspec commit).
