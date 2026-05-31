---
tags: [type/handoff, domain/inv, asset/equity-kr, phase/3-direction-pending]
date: 2026-05-30
note: eq_kr 작업방 Phase 3 R2 완료 직후 인계. 다음 세션 직진 — R3 skip + direction.md 작성 → frame v2 → plan → Phase 5 dispatch.
---

# handoff — eq_kr Phase 3 R2 → direction.md (2026-05-30)

> 다음 세션이 본 작업 동등 재개. 진행 내역·미해결·재개 포인트·자문 결과·열어본 파일 전부.

## 0. 현재 상태 (2026-05-30 12:30)

- ctx 86% (long-mode ON, cap 500k)
- Phase 3 R1+R2 완료 → R3 skip 권고 → **direction.md 직접 작성 진입 직전**
- 산업 12 Tier 분할 결정 / 외국인 flow 가중 강화 결정 / 신지표 4 후보 확정

## 1. 절차 v2 (사용자 박제 + Inv frame 정합)

| Phase | 상태 | 산출 |
|---|---|---|
| 0 dispatch 중단 + progress 박제 | ✅ | progress.md, raw/v1-superseded/ |
| 1 evaluation-axes (AUDIT-GUIDE 12축 application) | ✅ | evaluation-axes.md v2 |
| 2 methodology-brief | ✅ | methodology-brief.md (4-section 자문 input) |
| 3 자문 R1+R2 | ✅ | consult-round-1.md, consult-round-2.md |
| 3.5 direction.md (★다음 단계) | ⏳ | (작성 의무) |
| 4 plan.md + progress 갱신 | ⏳ |  |
| 5 frame.md v2 + 산업 subagent Tier 차등 dispatch (12개) | ⏳ |  |
| 6 평가 subagent (AUDIT-GUIDE 12축) | ⏳ |  |
| 7 통합 study_session.yaml + main 승인 | ⏳ |  |

## 2. R1+R2 자문 핵심 finding (direction.md 입력)

### 2.1 ★산업 12 Tier 분할 (R1)
- **Tier 1 (KOSPI 40%+, 단독 subagent opus 1m 500k)**: 반도체 (삼성전자 + SK하이닉스 = KOSPI 50.44% 2026-05). sub-cluster 권고 = 메모리·파운드리·장비 별 dispatch
- **Tier 2 (각 5-10%, 300k)**: 자동차 · 금융 · 2차전지
- **Tier 3 (각 2-5%, 150-200k)**: AI tech · 화학 · 정유 · 조선 · 바이오 · 통신 · 철강 · 소비재
- 12 균등 분할 ★기각★ (반도체 50% 집중 finding)

### 2.2 ★외국인 flow 가중 강화 (R1)
- frame v1 base 0.18 → 0.20+ 상향 (5게이트 통과 확인 후)
- 근거: Roller-KOSPI 15세션 50조 매도 (사상 극단)
- 신 차원: 외국인 flow regime (강매수/매도/중립) → frame §M3 regime cell 확장 (12 → 36 cell, N gate 강화 의무)

### 2.3 ★신지표 4 후보 (R1)
1. breadth_kospi = return(가중 KOSPI) - return(동등가중 KOSPI) — 반도체 dominance 측정 (자체 정의, R2 학술 baseline 부재 → tier 강등 가능성)
2. MSCI cap 초과 flag — 글로벌 패시브 flow 차단 이벤트
3. ETF leverage flow — KODEX 등 leveraged 순매수
4. 외국인 flow regime — 강매수/매도/중립 분류

### 2.4 ★일본 TSE baseline (R2)
- 2024-01 시행 → 2년 후 PBR<1 비율 Prime -23pt / Standard -15pt / 자사주 급증
- 한국 (2024-02 FSC) 동기 → 2-3년 후 동등 효과 예측 anchor
- 한계: disclosure 품질 mixed → 정책 fade 위험

### 2.5 ★OSS 채택 (R2)
- **toraniko** (MIT numpy+polars, Barra vein, value·size·momentum) + **skfolio** (sklearn walk-forward CPCV)
- frame §M4 5게이트 #5 (OOS) = skfolio CombinatorialPurgedKFoldSplit 직접 매핑
- Korean KOSPI 직접 사례 X = eq_kr first mover

### 2.6 e-KJFS 학술 (R0 round-2) 핵심 재인용
- 표본 2000-2022 (Value-Up 미포함, N=7443 KOSPI + 3021 KOSDAQ)
- G-score n.s. / R&D·CAPEX·Intangible pos p<0.01 / Payout neg sig KOSDAQ p<0.10
- 저자 결론: Korea discount = composition effect (성숙·tangible-asset value stocks 집중)

## 3. R3 잔여 빈틈 (Phase 5 산업 subagent 위임)

| # | 빈틈 | 위임 |
|---|---|---|
| 1 | KCGS 등급 KRX ESG 포털 무료 스크랩 PoC | 금융 또는 본 작업방 별 |
| 2 | arxiv 2401.00001 sector rotation 한국 IC | direction.md 작성 시 자체 baseline |
| 3 | 외국인 flow 가중 base 0.20+ power 추정 | 산업 subagent 실측 검증 |
| 4 | Tier 1 반도체 sub-cluster (메모리/파운드리/장비) 별 dispatch 필요성 | ★권고 = 분리 dispatch (3 sub-subagent, 각 200k) |

## 4. 다음 세션 직진 작업 (★순서)

1. **direction.md 작성** (Phase 3.5)
   - ①이론수집 = 한국 미시구조 (Korea discount, 밸류업 정책, 외국인 수급 지배, 반도체 50% 집중) + 일본 baseline + e-KJFS R&D/growth driver + toraniko/skfolio OSS
   - ②검증방향 = frame §M4 5게이트 (N/SE/Power/FDR/OOS, skfolio CPCV) + Macro 4 × KRW 3 × 외국인 flow 3 = 36 cell regime 분해 + Tier 1 (반도체 단독) / Tier 2 (3) / Tier 3 (8)
   - ③가설 반증조건 = 8 가설 (round-1 H1-H8) + R1/R2 finding 으로 갱신 (외국인 flow alpha, valueup re-rating, semi cycle turn, USDKRW × export 교호, breadth divergence)
2. **frame.md v2 갱신** (Phase 5 dispatch 전 의무)
   - §1 universe — 12 산업 Tier 분류 표 (R1 finding)
   - §3 Layer 2 — 외국인 flow base 강화 + 신지표 4 후보
   - §6 8축 → 12축 (AUDIT-GUIDE.md 인용)
   - §M4 5게이트 #5 — skfolio CPCV 매핑
   - §M3 regime — 36 cell + N gate 강화
3. **plan.md** (Phase 4) — Phase 5 dispatch 의 산업 12 + Tier 차등 토큰 명시
4. **Phase 5 dispatch** — 산업 12 subagent (Tier 차등 토큰)
   - Tier 1 반도체 (500k 단독 + sub-cluster 옵션 3) 
   - Tier 2 자동차/금융/2차전지 (각 300k)
   - Tier 3 8 산업 (각 150-200k)
5. **Phase 6 평가 subagent** dispatch (opus 1m, AUDIT-GUIDE 12축 application 으로 평가)
6. **Phase 7 통합** study_session.yaml + main 승인

## 5. 핵심 파일 경로 (열어본 + 작성한)

### 본 작업방 (D:/projects/Inv/study-research/eq_kr/)
- progress.md ★current
- evaluation-axes.md v2 (AUDIT-GUIDE 12축 application)
- methodology-brief.md (4-section 자문 input)
- frame.md v1 (v2 갱신 의무)
- raw/round-1.md (round-1, WebSearch 1)
- raw/round-2.md (round-2, e-KJFS + 3 WebSearch)
- raw/consult-round-1.md (Phase 3 R1)
- raw/consult-round-2.md (Phase 3 R2)
- raw/krx-infra-checklist.md (R0 인프라 점검)
- raw/lens-and-weight-rationale.md (R0 자체 분석)
- raw/v1-superseded/ (v1 자문코드화 시도)
- industries/{semiconductor,battery,auto,financial}/ (Phase 0 중단 후 빈 디렉토리, Phase 5 재사용)

### Inv frame (필수 SSOT)
- D:/projects/Inv/CLAUDE.md §"멀티에셋 스터디 워크플로"
- D:/projects/Inv/STUDY-KIT.md (각 작업방 작업 계약, §2 3흐름, §2.5 8축, §3 yaml)
- D:/projects/Inv/STUDY-ORCHESTRATION.md (5-Phase)
- D:/projects/Inv/study-research/AUDIT-GUIDE.md (★12축 평가 SSOT, opus subagent 용)

### Inv 인프라 (Phase 5 산업 subagent 사용)
- D:/projects/Inv/stock/data/dart_provider.py (DART_API_KEY 부재 시 graceful)
- D:/projects/Inv/stock/data/krx_universe.py + data/krx_snapshots.jsonl
- D:/projects/Inv/stock/data/krx_flows.py + data/krx_sector_snapshots.jsonl + data/krx_flow_snapshots.jsonl
- D:/projects/Inv/core/data/macro_market.py (FxStore USDKRW PIT)
- D:/projects/Inv/core/brain/fred_adapter.py (HY OAS, real rate)
- D:/projects/Inv/core/brain/regime_to_weights.py (kr_stock sleeve 기존재, SLEEVES L50)
- D:/projects/Inv/core/stock_track.py (_resolve_weight_card L220 'weight.equity.{regime}')
- D:/projects/Inv/core/assume/weight_card.py (WeightAssumptionCard L64, composed_weights L115)
- D:/projects/Inv/core/assume/weight_falsification.py (score_ic_breakdown_eprocess L66)
- D:/projects/Inv/core/structure/conditional_correlation.py (RegimeGlasso L237)
- D:/projects/Inv/_refs/dart-fss, _refs/OpenDartReader, _refs/FinanceDataReader

### Memory (R0 + Phase 3 R1+R2 적재)
- ~/.claude/memory/research/eq-kr-korea-discount-value-up.md (R0)
- ~/.claude/memory/research/eq-kr-r2-academic-validation-japan-kcgs-naver.md (R0 round-2)
- ~/.claude/memory/research/eq-kr-r3-r1-sector-concentration-2025.md (Phase 3 R1)
- ~/.claude/memory/research/eq-kr-r3-r2-japan-toraniko-breadth.md (Phase 3 R2)

### Archive raw (Phase 3 적재)
- ~/.claude/docs/archive/research-raw/eq-kr-korea-discount-value-up-native-20260530.txt
- ~/.claude/docs/archive/research-raw/eq-kr-r2-validations-native-20260530.txt
- ~/.claude/docs/archive/research-raw/eq-kr-r3-r1-sector-concentration-native-20260530.txt
- ~/.claude/docs/archive/research-raw/eq-kr-r3-r2-japan-toraniko-breadth-native-20260530.txt

## 6. main 통신 history (psmux btn-Codlearn)
- R0 round-1 보고
- R0 round-2 보고 (학술 반증)
- ★v2 절차 재정렬 통지
- 미국 주식 별 작업방 통지 (재전송 2/2 완료)
- Inv frame 정합 v2.1 통지
- Phase 3 R1 완료 통지
- Phase 3 R2 완료 통지 (★다음 세션 보고 의무)

## 7. 미해결 결정 (다음 세션 결정 필요)

1. ★ Tier 1 반도체 sub-cluster (메모리/파운드리/장비) 별 dispatch 여부 — 권고 = 분리 (3 sub-subagent)
2. ★ direction.md 의 가설 N — round-1 8 가설 유지 + R1/R2 finding 갱신 N = 10-12 권고
3. ★ Phase 5 dispatch 동시 vs 순차 — opus 1m 12 동시 = 4M+ 토큰 (사용자 명시 허용). 권고 = 동시 (run_in_background)
4. ★ frame.md v2 의 신지표 4 채택 — breadth (자체 정의 tier 강등 가능) / MSCI cap (event) / ETF leverage (Bloomberg 자료 필요) / 외국인 flow regime (자체 분류 가능)

## 8. 사용자 박제 (절대 금지)

- ⛔ 점추정 prior 박제 / 합성 데이터 / 자문 그대로 코드화 / single-source 단정 / small-N 단정 (5 금지)
- ⛔ 본 작업방 supervisor 직접 평가 — 평가 subagent (별 opus 1m) 위임 의무
- ⛔ analyst-level lens 다운그레이드 (시스템 못 받으면 파이프라인 업그레이드)
- ⛔ main pass-bias 회피 — opus 독립 audit subagent 만 판정 (raw 재계산 기반)
