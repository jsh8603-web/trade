---
tags: [type/handoff, domain/inv, asset/bond, asset/cash, phase/study-v2, session/btn-powerbi]
date: 2026-05-31
study_id: bond_cash
session: btn-powerbi
status: v2 7-Phase 진행 중 (Phase 0→1→2→3 R1 완료, R2/R3/3.5 미진행)
next-session-entry: Phase 3 R2 자문 또는 main 메시지 #3 merit 후보 식별 작업
---

# bond_cash 세션 핸드오프 (2026-05-31, btn-powerbi)

> main 지시: "현재 잔업·다음작업·재개포인터·미해결 전부 기록 + 미커밋 commit + HANDOFF DONE 1줄 보고".
> 본 문서 = 다음 세션이 cold-start 로 즉시 재개 가능한 모든 정보.

## §1 작업 history 5행 표 (handoff-plan-wf 표준 포맷)

| 항목 | 내용 |
|---|---|
| **마지막 완료** | v2 Phase 3 R1 자문 (MOVE + ACM term premium 가용성·source 확인). `raw/consult-round-1.md` 작성 완료. |
| **다음 작업** | (A) main 메시지 #3 — "merit 후보 전수 식별 + collector main 에 요청" / (B) v2 Phase 3 R2 자문 (sub-cluster 분할 검증 + ACM 대안 모델 + ICE 라이센스 대체) |
| **그 다음** | Phase 3 R3 cross-verify → Phase 3.5 direction.md (v2) → ★멈춤 → main 승인 게이트 → Phase 4 plan.md → Phase 5 sub-cluster subagent dispatch → Phase 6 별 평가 subagent (opus 1m) → Phase 7 통합 yaml |
| **중단 시점** | 2026-05-31 00:17 — Phase 3 R1 consult-round-1.md 작성 직후 main 의 handoff 지시 도착 |
| **skip 된 것** | (a) v1 산출 → raw/_v1_carryover/ 격리 보존 (메시지 #1 "raw 참고용 보존" 준수). (b) /gemini-web + /claude-web 직접 호출 — 채널 경합 우려로 WebSearch native 폴백 default (이전 5R 동일 패턴, 사용자 폴백 허용 명시). (c) Phase 3 R2/R3 자문 미진행. (d) Phase 3.5 direction.md (v2 버전) 미작성. (e) Phase 4~7 미진입. |

## §2 착수 전 확인 사항 (다음 세션 재개 시 정독)

1. **main 우선순위 재확인**: 메시지 #4 (handoff) 가 최우선. 메시지 #3 (merit 후보 식별 + collector 요청) 이 다음. v2 Phase 3 R2 는 그 후.
2. **★사용자 박제 5 금지** (모든 자산군 공통):
   - 점추정 prior 박제 금지 (IC 점추정 → base_weight 직접 X. 분포 + CI + 게이트)
   - 합성·시뮬 데이터 금지 (random walk / 합성 panel / 가상 ticker / random IC. 실제 수집기 PIT 만)
   - 자문 그대로 코드화 금지 (gemini/claude 답 → yaml 직접 X. supervisor 비판·환각 cross-verify 후 채택)
   - Single-source 단정 금지 (1 출처 "확정" X. 학술 + 실무 + 1차 데이터 3중)
   - Small-N 단정 금지 (cell N<24 "유의" 주장 X. 5게이트 §N gate 우선)
3. **★추가 박제**:
   - ★ supervisor (bond_cash 본 작업방) 직접 평가 금지 — Phase 6 별 opus 1m subagent 위임 의무
   - ★ analyst-level lens 다운그레이드 금지 — 시스템 못 받으면 파이프라인 업그레이드
   - ★ opt-in off = byte-identical 무회귀 (INV_R15_WEIGHTS default-off)
   - ★ reflexive loop 차단 (belief→_macro 차단, L축 공통인자 1회 계상 + PSD)
   - ★ tier 정직성 (검증 통과 ≠ validated alpha. REJECT·contemporaneous = structural prior 저신뢰 라벨)
4. **★ 핵심 누락 critical 지표** (사용자 메시지 #3, 의무 포함):
   - MOVE index (★사이징 직결, 최우선) — yfinance `^MOVE` (1988~) + FRED rid=209 가용
   - ACM term premium (Adrian-Crump-Moench) — NY Fed `newyorkfed.org/research/data_indicators/term-premia-tabs` 1961~ daily

## §3 산출 파일 전수 목록 (절대 경로 + 역할)

### v2 산출 (현 세션 신규)
| 파일 | 라인 | 역할 |
|---|---:|---|
| `D:/projects/Inv/study-research/bond_cash/progress.md` | ~50 | v2 7-Phase 진행 박제 |
| `D:/projects/Inv/study-research/bond_cash/evaluation-axes.md` | ~150 | AUDIT-GUIDE 12축 application (bond_cash sub-cluster 단위) |
| `D:/projects/Inv/study-research/bond_cash/methodology-brief.md` | ~155 | Phase 3 자문 input 4-section + Q1-Q17 |
| `D:/projects/Inv/study-research/bond_cash/raw/consult-round-1.md` | ~120 | Phase 3 R1 (MOVE + ACM, WebSearch 폴백) |

### v1 산출 (보존, v2 후속 phase 에서 흡수)
| 파일 | 역할 | v2 에서 어떻게 흡수 |
|---|---|---|
| `direction.md` (168줄) | v1 STUDY-KIT §2-1 산출 (5R 종합 ①②③) | Phase 3.5 v2 direction.md 작성 시 입력 자료 |
| `raw/theory-notes.md` (396줄, 10 섹션) | v1 STUDY-KIT §2-2 산출 + ★§8 중복 driver 정합 (macro/eq_us_defensive 와) | Phase 2 methodology-brief §A/B/D 검증 input |
| `raw/round-1~5.md` | v1 STUDY-KIT §2-1 자문 5R (URL 46건) | Phase 3 R2/R3 자문에서 cross-reference |
| `raw/validation-hy-oas-event.md` | v1 §2-3 V1 (★FRED BAMLH0A0HYM2 최근 3년만 발견, 600bps event 0건) | Phase 5 sub-cluster 검증 input |
| `raw/validation-curve-flip.md` | v1 §2-3 V2 (T10Y2Y 50년 풀, inversion 44건, lead time median 19개월, bull/bear steepening 분기 필요) | Phase 5 검증 input |
| `raw/validation-cash-sharpe.md` | v1 §2-3 V3 (★Cash Sharpe 0.55 > SPY 0.20, Duffee fact 강 지지) | Phase 5 검증 input |
| `raw/validation-bond-decomposition.md` | v1 §2-3 V4 (TLT R²=0.81, IEF R²=0.93, implied D 이론치 -10~-18% / convexity β2 음수 기각) | Phase 5 검증 input |
| `raw/_v2_analysis/run_validations.py` | 검증 4건 통합 스크립트 (실데이터, 합성 0) | Phase 5 sub-cluster 별 검증 baseline |
| `raw/_v2_analysis/results.json` | 검증 4건 JSON snapshot | Phase 6 audit raw recomputation 입력 |
| `raw/_v1_carryover/study_session.yaml` | v1 STUDY-KIT §3 7블록 (블록7 code_change_plan 까지) | 폐기 X, v2 통합 yaml (Phase 7) 작성 시 참고 |
| `raw/_v1_carryover/summary.md` | v1 8섹션 요약 | 참조용 |
| `raw/_v1_carryover/analyze_bond_cash.py` + `correlation_analysis.txt` | v1 §2-3 부분 분석 (Fisher 분해 검증) | 참조용 |

### 외부 archive 사본 (hook 의무)
| 파일 | 위치 |
|---|---|
| `bond-cash-round1~5-native-20260530.txt` | `~/.claude/docs/archive/research-raw/` |

### memory
| 파일 | 역할 |
|---|---|
| `~/.claude/memory/research/bond-cash-fixed-income-research.md` | v1 5R 종합 (frontmatter 완비) |
| `~/.claude/memory/MEMORY.md` | 인덱스 한 줄 추가 완료 |

## §4 ★ main 메시지 #3 — merit 후보 식별 + collector 요청 작업 (다음 세션 1순위)

> 메시지 #3 인용: "(1순위) merit 있는 후보 지표를 실제 추가하는 study 를 다시 — collector 없으면 main 이 구현하니 'merit 근거 + 필요 collector + 무료 데이터소스 후보' 를 main 에 먼저 보고. 흐름 = main collector 구현 → 너 study(이론→실데이터→상관·Rank-IC) → 12축 audit(별도 subagent) → yaml 반영."

### 식별된 merit 후보 (v1 + v2 자문 통합) — 전수 목록

| # | 후보 | merit 근거 | 필요 collector | 무료 source 후보 | 우선순위 |
|--:|---|---|---|---|:--:|
| 1 | **★MOVE index** | 사용자 메시지 #3 "사이징 직결 최우선". 채권 변동성 본체 (= VIX 등가). risk gate + sleeve down-only attenuate | yfinance + FRED adapter | yfinance `^MOVE` (1988~) / FRED rid=209 (정확 series_id 확인 필요) | **P0** |
| 2 | **★ACM term premium 10Y** | 사용자 메시지 #3. DGS10 = expected_short_rate + term_premium 분해. weight_rules block4 분기 (TP↑ → long-dur penalty / expected↓ → cash carry trade-off) | NY Fed ACM adapter 신설 | NY Fed `newyorkfed.org/research/data_indicators/term-premia-tabs` xlsx | **P0** |
| 3 | DGS10 (10Y nominal) | 채권 가격 1차 driver, 듀레이션 baseline. v1 V4 검증에서 implied D 이론치 -10~-18% 일치 (R²=0.81~0.93) | fred_adapter FRED_SERIES dict 추가 | FRED DGS10 (fredapi key 보유) | **P0** |
| 4 | DGS2 (2Y nominal) | term structure expectations, 커브 단기 wing, Fed phase 전달 경로 | 동상 | FRED DGS2 | **P0** |
| 5 | DGS3MO (3M T-Bill) | cash sleeve carry 대용 | 동상 | FRED DGS3MO | **P0** |
| 6 | DFII10 (10Y TIPS real rate) | Fisher 분해 (nominal = real + breakeven), 듀레이션 vs 인플레 분기축. macro 방과 공유 (중복 추가 금지) | 동상 | FRED DFII10 | **P0** |
| 7 | FEDFUNDS | 정책금리 anchor, 2Y 전달, cash carry 본체 | 동상 | FRED FEDFUNDS | **P0** |
| 8 | MORTGAGE30US | long Tsy + credit 잔차 채널 | 동상 | FRED MORTGAGE30US | P1 |
| 9 | **채권 ETF 일별가 (TLT/IEF/SHY/BIL/SHV/HYG/JNK/LQD/TIP/VTIP/STIP/EDV/TLH/VGSH)** | sub-cluster 본 forward return, weight_rules granularity=ticker 의 본질 | VintageStore PIT 적재 + yfinance fetch | yfinance (즉시 가능, ETF inception 부터) | **P0** |
| 10 | ICE BofA US Treasury Index TR (BAMLCC0A0CMTRIV) | 장기 OOS 백테스트 (1973~) | fred_adapter | FRED BAMLCC0A0CMTRIV | P1 |
| 11 | **BAMLH0A0HYM2 1996-12~2023-05 historical** | v1 V1 발견: FRED 무료가 최근 3년만 (ICE 라이센스 변경). 600bps event study 필수 | 외부 source — ICE Direct 라이센스 또는 S&P U.S. HY Corporate Bond Index 대체 | (유료/대체 검증 필요) | **P0** |
| 12 | VIX (VIXCLS) | 3-signal warning 합성 (HY OAS + curve + VIX), 4-8개월 lead time | fred_adapter | FRED VIXCLS | P1 |
| 13 | USEPUINDXD (Baker-Bloom-Davis EPU) | Fed spillover 증폭 효과 (compound shock), KR sleeve 확장 시 핵심 | fred_adapter | FRED USEPUINDXD | P2 |
| 14 | T-Bill 공급량 (MTSTOTUS 등) | curve flattening 외력 모니터 | fred_adapter | FRED MTSTOTUS or 미 재무부 | P2 |
| 15 | KTB ETF (KOSEF 국고채) | KR sleeve 확장 — 3 driver (Fed + BoK + WGBI) | KrxEtfProvider 신설 | 한국거래소 daily | P2 |
| 16 | JGB 10Y (IRLTLT01JPM156N) | 엔캐리 채널 — macro 방과 공유 | fred_adapter | FRED IRLTLT01JPM156N | P2 |
| 17 | M2 yoy (M2SL) | 유동성 채널 (macro 방 공유) | fred_adapter | FRED M2SL | P2 |
| 18 | **DGS5** (5Y nominal) | 커브 belly, butterfly trade | fred_adapter | FRED DGS5 | P1 |
| 19 | Fed Funds futures implied rate | Fed 기대 정확 시그널 (cash sleeve carry trade-off 판정) | CME FedWatch API | CME FedWatch (무료, scraping) | P2 |
| 20 | OIS spread (TED 대체) | 금융 stress 보조 (NFCI 와 중복 위험) | FRED | FRED 가용성 확인 필요 | P3 |
| 21 | T-Bill auction yield | cash sleeve carry calibration | 미 재무부 fiscal data | treasurydirect.gov | P3 |
| 22 | CB Reserves / RRP usage | cash sleeve 유동성 환경 | FRED RRPONTSYD | FRED RRPONTSYD | P3 |

### main 요청 액션 (다음 세션이 메시지 보낼 내용)

**P0 (즉시 구현 요청)**:
- (a) **fred_adapter.FRED_SERIES dict 에 6 항목 추가**: DGS10/DGS2/DGS3MO/DFII10/FEDFUNDS/MORTGAGE30US (macro 방 DFII10 와 union 통합)
- (b) **NyFedAcmAdapter 신설** — NY Fed ACM term premium xlsx fetch + 10Y series (ACMY10/ACMTP10) parse
- (c) **MoveIndexAdapter 신설** — yfinance `^MOVE` daily fetch + FRED rid=209 정확 series_id 확인 후 매핑
- (d) **BondEtfProvider 신설** — yfinance multi-ticker 일별 Close PIT 적재 (TLT/IEF/SHY/BIL/SHV/HYG/JNK/LQD/TIP 최소 9종)
- (e) **BAMLH0A0HYM2 historical 확보 의사결정** — ICE 직접 라이센스 비용 추정 또는 S&P U.S. HY Corp Bond Index TR 대체 source 검증

**P1 (후속)**: VIX (VIXCLS), MORTGAGE30US, DGS5, BAMLCC0A0CMTRIV
**P2~P3**: EPU, T-Bill 공급량, KTB, JGB, M2, Fed Funds futures, OIS, RRP

### 흐름 명시 (사용자 메시지 #3)
1. **main collector 구현** (P0 5건 우선)
2. **bond_cash study** = 이론 정독 → 실데이터 수집 → 상관·Rank-IC 검증
3. **12축 audit** (별도 evaluator subagent opus 1m, evaluation-axes.md §5 prompt)
4. **yaml block 2/3/4/5/7 반영** (Phase 7)

⛔ 메시지 #3 명시: "collector 없음·후순위·이연은 탈락 사유 부적격". 본 표의 모든 P0 후보는 collector 구현 필수 (탈락 사유 = merit 없음 OR 실측 무상관 만 인정).

## §5 v2 Phase 3 R2/R3 자문 미진행 — 다음 세션 자문 시 query

자문은 **WebSearch native 폴백 default** (9 작업방 동시 점유 우려). `touch ~/.claude/.allow-native-web` 토글 5분 expire 가능 — 매 호출 직전 재발동.

### R2 자문 query 후보 (methodology-brief.md §E)
1. **MOVE-based risk parity / vol targeting** 학술 논문 — 채권 strategy MOVE 사이징 mechanism 정량화
2. **ACM 대안 모델** (Kim-Wright, Joslin-Singleton-Zhu) — single source risk 회피
3. **sub-cluster 분할 7개 vs 4개** trade-off (subagent 토큰 비용)
4. **TIPS sub-cluster 별도 vs 통합** 학술 baseline
5. **bond sleeve corr_prior force-include** 우선순위 (R1 ACM 분해 결과 반영)
6. **BAMLH0A0HYM2 1996-2023 historical 대체 source** (ICE 라이센스 비용 / S&P 대체)

### R3 cross-verify query (R1 + R2 종합 후)
- ACM TP regime-conditional 부호 검증 (rate-up vs rate-down)
- MOVE Z 와 HY OAS Z 의 partial-corr (둘 다 사이징 직결 — 중복 신호 위험)
- sub-cluster 7개 별 baseline Sharpe / IC 사전 등록 (Phase 5 검증 baseline_ic)

## §6 v2 Phase 3.5 direction.md 작성 가이드 (R2/R3 수렴 후)

v1 direction.md (168줄) 베이스 + R1 (MOVE/ACM) + R2 + R3 통합. 구조:
```markdown
# bond_cash direction (v2 Phase 3.5, R1+R2+R3 종합)
## ① 이론 수집 방향
  - A. 채권 가격결정 (Fabozzi, Carr NYU)
  - B. Investment Clock 4국면 (Greetham)
  - C. Credit cycle (HY OAS 600bps)
  - D. Curve 역전 lead time (median 19개월, 본 작업방 실측)
  - E. Cash optionality (Duffee, Sharpe 0.55 vs SPY 0.20 실측)
  - F. KR / Fed spillover (KTB 3 driver, EPU compound)
  - G. ★MOVE index (사이징 직결, R1 신규)
  - H. ★ACM term premium (TP vs expected rate 분해, R1 신규)
## ② 이론 검증 방향
  - AUDIT-GUIDE 12축 + 5게이트 + Tier 차등 + regime cell
## ③ 핵심 가설 N+ (반증조건 포함)
  - v1 12 가설 + MOVE/ACM 신규 3 가설
  - H13: MOVE Z↑ → 전 bond sleeve forward 20d Rank-IC < 0 (사이징 penalty 검증)
  - H14: ACM TP↑ → long-duration sub-cluster forward 60d Rank-IC < 0 (TP 외생 충격)
  - H15: ACM expected rate↓ → cash sleeve forward 5d Rank-IC > 0 (rate-cut option)
```

★ Phase 3.5 후 멈춤 → main 승인 게이트 (idle 아님).

## §7 v2 Phase 4~7 미진입 (★main 승인 후)

- Phase 4 — plan.md (Phase 5-7 dispatch table, sub-cluster N × Tier 차등 토큰)
- Phase 5 — sub-cluster N subagent dispatch (opus 1m, run_in_background)
  - Tier 1: tsy_long, hy_credit, tips (3 sub-cluster, ★MOVE/ACM 본격 적용)
  - Tier 2: tsy_mid, tsy_short, ig_credit, cash_tbill (4 sub-cluster)
  - 산출 = `sub-clusters/{name}/` 8 파일 (round-1 + round-N + theory-notes + validation-yield-curve + validation-credit-spread + validation-vol-regime[★MOVE] + validation-term-premium[★ACM] + summary.yaml + 12axis-audit.md)
- Phase 6 — ★별 평가 subagent (opus 1m, evaluation-axes.md §5 prompt 그대로)
- Phase 7 — 통합 study_session.yaml + main 승인 게이트

## §8 미해결 항목 (해소 책임 = 다음 세션)

1. **NY Fed ACM xlsx URL 정확성 미검증** — `https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls` 추정만, 실제 다운로드 확인 필요 (WebFetch 1회)
2. **FRED rid=209 안의 정확한 MOVE series_id** — 192 시리즈 중 정확한 ticker 확인 필요 (WebFetch 또는 FRED REST API series_search)
3. **BAMLH0A0HYM2 historical 비공개 시점·사유** — ICE 공식 release note 확인 필요 (v1 V1 발견의 정확한 원인 검증)
4. **MOVE 사용 layer** (sleeve vs sub-cluster vs ticker) — 학술 baseline 없으면 본 작업방 실측 (Phase 5)
5. **ACM expected rate 와 fed funds 의 redundancy** — 정보량 중복 (블록4 weight_rules base_weight 조정 필요)
6. **TIPS sub-cluster 의 ACM 적용** — TIPS yield 자체 분해 (real_TP 별도 추정 필요)
7. **REGIME_DIRECTION[Overheat][cash]="down" 재분류** — v1 V3 결과 (Cash Sharpe 0.55 > SPY 0.20) 정당성 vs 코드 현재 값 모순
8. **etf_track 신설 vs stock_track 분기** — v1 direction.md ★요청 #4, 미회신
9. **TIPS 분리 archetype 신설** — v1 direction.md ★요청 #2, 미회신
10. **VIX / EPU collector_plan 추가 의사결정** — v1 direction.md ★요청 #3, 미회신

## §9 ckpt + main 보고 가이드

### 다음 세션 cold-start 첫 5 액션
1. **본 핸드오프 정독** (이 파일 전체)
2. progress.md Read (v2 Phase 진행 박제)
3. `methodology-brief.md` §E 자문 라운드 계획 + `evaluation-axes.md` §5 evaluator prompt 확인
4. main 메시지 #3 의 "merit 후보 + collector 요청" 우선 처리 (§4 표 그대로 main 에 송신)
5. main 회신 후 v2 Phase 3 R2 자문 진입 또는 Phase 4 plan.md 진입

### main 보고 양식 (다음 세션이 사용)
```
[bond_cash→main] ✅ §4 merit 후보 22종 + 필요 collector 5건 (P0) 보고
  P0 collector: (a) FRED 6종 추가 (b) NyFedAcmAdapter (c) MoveIndexAdapter
                (d) BondEtfProvider (e) BAMLH0A0HYM2 historical 라이센스 결정
  P1/P2: VIX/MORTGAGE/EPU/KTB 등
  v2 Phase 3 R1 자문 완료 → R2/R3 → Phase 3.5 direction.md 진행 의향
```

## §10 미커밋 변경 commit (현 세션 마무리)

```
git add study-research/bond_cash/ handoff-bond_cash-20260531.md
git commit -m "docs(bond_cash): v2 Phase 0-3 R1 진행 + handoff 작성"
```

⚠️ 비밀번호·API key 절대 포함 금지 (`.env` 는 .gitignore 확인).

---

**STATUS**: pending (Phase 3 R2 자문 또는 main 메시지 #3 merit 식별 작업 재개 대기)
