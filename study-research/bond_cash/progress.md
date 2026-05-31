# bond_cash — v2 7-Phase 진행 (2026-05-30, eq_kr baseline 미러)

> ★dispatch 베이스: `D:/projects/Inv/study-research/eq_kr/methodology-final-for-main-dispatch.md` v2.
> ★사용자 누락 critical 지표 의무 포함: **MOVE index (사이징 직결, 최우선)** + **ACM term premium** + yield curve(T10Y2Y) + credit spread(HY OAS) + real rate.
> ★ 5 금지 + supervisor 직접 평가 금지 + analyst-lens 다운그레이드 금지 박제.

## Phase 0 — 정리 (✅ 완료)
- [x] 직전 v1 산출 (study_session.yaml + summary.md + raw/_v2_analysis/analyze_bond_cash.py + correlation_analysis.txt) → `raw/_v1_carryover/` 보존
- [x] direction.md (v1 산출, 168줄, 5R 종합) 보존 (v2 에서 흡수)
- [x] theory-notes.md (v1 산출, 396줄, 10 섹션, §8 중복 driver 정합) 보존 → v2 의 Phase 2 input 으로 재사용
- [x] raw/validation-hy-oas-event.md / validation-curve-flip.md / validation-cash-sharpe.md / validation-bond-decomposition.md (v1 산출, 실데이터 검증 4건) 보존 → v2 의 Phase 5 검증 input 으로 재사용
- [x] progress.md 박제 (본 파일)

## Phase 1 — evaluation-axes.md (✅ 완료, 152줄)
- [x] AUDIT-GUIDE 12축 (8 핵심 + 4 신규) + bond_cash sub-cluster 단위 application
- [x] Hard-fail 코어 4 = B/C/D/I 명시
- [x] §0 Provenance + Recomputation 의무

## Phase 2 — methodology-brief.md (✅ 완료, 153줄)
- [x] §A sub-cluster 분할 후보 (7 sub-cluster) + Q1-Q6
- [x] §B Layer 3 cycle 지표 (MOVE/ACM/HY OAS/curve/real rate)
- [x] §C 최종 구현 + Q11-Q14
- [x] §D Inv 인프라 + collector_plan + Q15-Q17
- [x] §E R1/R2/R3 자문 진행 계획
- [x] §F 자문 출력 의무

## Phase 3 — 자문 R1+R2+R3 수렴
- [x] R1 (WebSearch native 폴백) — MOVE/ACM 본질·source → `raw/consult-round-1.md` (120줄)
- [x] R1 후속 검증 (2026-05-31, btn-powerbi) — NY Fed term-premia URL + FRED rid=209 MOVE series_id WebSearch + memory 박제 (`research/bond-cash-acm-move-collector-verify.md`)
- [ ] R2 (WebSearch native) — sub-cluster 분할 (Q1-Q6) + MOVE/ACM inject (Q13-Q14) + ACM 대안모델 (Kim-Wright) cross-verify + ICE 라이센스 대체
- [ ] R3 (필요 시) — 두 채널 cross-verify, 잔여 빈틈 메우기

## Phase 3.5 — direction.md (★main option A 승인 후 우선순위 격하)
- [ ] R2/R3 수렴 후 작성. **main 지시 (option A)**: collector self-fetch 즉시 + study 진입. direction.md = Phase 4-5 산출과 병행.

## Phase 4 — collector self-fetch + sub-cluster sample 검증 (★main option A, ★진행 중)
- main 메시지 (2026-05-31, btn-powerbi 세션): "P0 5건 자체 fetch+study → validation md → STUDY DONE 보고 → main 12축 audit". 옵션 A.
- 검증완 endpoint (main + 본 세션 cross-verify):
  - [x] C1 rates = fredapi + FRED_API_KEY (v1 검증완)
  - [x] C2 ETF = yfinance (즉시 가능)
  - [x] C4 MOVE = yfinance `^MOVE` (지연무료, 1988~)
  - [x] C5 ACM = `https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls` (200 OK 10.1MB ✅, 본 세션 curl HEAD 검증)
  - [x] C9 HY OAS = BAMLH0A0HYM2 FRED 2023-05~ 무료 + **pre-2023 대체** = BAA10Y (1986~) · NFCI (1971~) 무료 장기 (DA가 eq_us_defensive H3 검증·확립 경로 재사용). ICE 1996~ historical 유료분 탈락 (대체 확보로 merit 보존).
- [ ] Phase 4-1: fetch 스크립트 (`raw/_v2_analysis/fetch_p0.py`) — ACM xlsx + DGS 6종 + MOVE + 9 ETF + BAA10Y + NFCI parquet 적재
- [ ] Phase 4-2: forward return 계산 (5d/20d/60d × 7 sub-cluster ETF)
- [ ] Phase 4-3: Rank-IC + HAC SE + Bonferroni (small-N rigor 5 의무: data coverage 일자 / n + LOO / spec↔code 1:1 / autocorr 보정 / multiple comparison)

## Phase 5 — sub-cluster N validation-*.md 작성 (★main option A)
- [ ] tsy_long / tsy_mid / tsy_short / ig_credit / hy_credit / cash_tbill / tips 각 8 파일 (round-N + theory-notes + validation-yield-curve + validation-credit-spread + validation-vol-regime[★MOVE] + validation-term-premium[★ACM] + summary.yaml + 12axis-audit-self.md)
- main 지시: supervisor 직접 작성 (subagent dispatch 대신, 1 session 안에 처리). audit 만 main 별 subagent.

## Phase 6 — ★별 평가 subagent (main 별도 dispatch, 본 작업방 책임 외)
- main 이 evaluation-axes.md §5 prompt + bond_cash 산출로 opus 1m subagent dispatch
- 본 작업방은 "STUDY DONE 경로 + AUDIT-GUIDE §1 12축 자가 PASS 라벨" 만 보고

## Phase 7 — 통합 study_session.yaml + main 승인 게이트 (★Phase 6 통과 후)

## Working Notes
- 2026-05-30 v2 진입 (main 메시지 #3 HOLD 해제 + MOVE/ACM 필수 포함)
- 2026-05-31 (btn-powerbi resume) — handoff §4 보고 → main 회신 option A → Phase 4 진행 중
- ⛔ 합성·시뮬 금지, 점추정 prior 금지, 자문 그대로 코드화 금지, Single-source 금지, Small-N 금지 (★5 금지)
- ⛔ supervisor 직접 평가 금지 — Phase 6 별 main subagent 위임
- ⛔ analyst-lens 다운그레이드 금지 — 파이프라인 업그레이드 필요 시 명시
- K축 tries 누적 공시: {consult: 6+R2, websearch: 2+, webfetch: 2}
- small-N rigor 5 의무 (`~/.claude/rules/small-n-statistical-rigor.md` + `empirical-claim-presentation.md`) 적용 의무
