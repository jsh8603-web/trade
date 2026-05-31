# consult-round-2 — eq_kr Phase 3 R2 (2026-05-30)

> v2 절차 라운드 2. R1 잔여 빈틈 7 중 1·3·5 우선 처리. WebSearch 폴백 3건.
> 3계층 적재: archive raw (eq-kr-r3-r2-japan-toraniko-breadth-native-20260530.txt) + memory (eq-kr-r3-r2-japan-toraniko-breadth) + MEMORY 인덱스.

## 1. R2 입력 (WebSearch 3건)

### 1.1 일본 TSE 2023 PBR reform 효과 (★R1 잔여 빈틈 1 해결)
- 2024-01 시행 (2021 거버넌스 코드 후속). Prime 공시율 90%+ (2025-03 이후).
- PBR<1 비율: Prime 27% (-23pt), Standard 49% (-15pt) (2026-02, 2년 후)
- 2024 자사주 매수 급증
- 한계: disclosure 품질 mixed (perfunctory 우려, Pzena/BNY)

### 1.2 toraniko + skfolio OSS (R1 잔여 빈틈 3)
- toraniko (MIT, numpy+polars only): Barra/Axioma vein, market/sector/style 3 factor (value·size·momentum), custom factor + factor cov 추정. Rust port.
- skfolio (sklearn 확장): walk-forward + ★combinatorial purged CV + leakage-safe.
- ★Korean KOSPI 직접 사례 X = eq_kr first mover.

### 1.3 KOSPI breadth indicator (R1 잔여 빈틈 5)
- 학술 baseline 부재 (Multifractal/scaling 만)
- 실무: equal-weight 비교 = "시장 health 필수". Advance-Decline 학술 정설.
- ★ 자체 정의: `breadth_kospi = return(가중 KOSPI) - return(동등가중 KOSPI)`

## 2. R2 답 (자체 분석)

### A1 일본 적용 baseline (한국 밸류업 정량 예측)
- 동기 시행 (일본 2024-01 vs 한국 2024-02 FSC). 모델 유사.
- 정량 anchor: 2년 후 한국 PBR<1 비율 -15~25pt 감소 가능성 (일본 데이터 기반).
- ★단 disclosure 품질 mixed = 한국도 정책 fade 시 mean-reversion 위험.
- frame v1 H2 (valueup_low_pbr_rerating) 가설 reinforcement — 그러나 자체 cycle 분리 측정 의무.

### A2 OSS 채택 권고
- ★ toraniko (factor) + skfolio (CV) 결합 = 산업 subagent baseline.
- frame §M4 5게이트 #5 (OOS) = skfolio CombinatorialPurgedKFoldSplit 직접 매핑.
- frame.md v2 갱신 시 §M4 implementation 절에 OSS 라이브러리 명시.

### A3 breadth indicator frame 등록
- 자체 정의: `breadth_kospi = w_return - ew_return`
- R1 finding (반도체 50%) 정량 backing.
- Layer 2 신지표 등록 (외국인 flow 와 함께 한국 미시구조 핵심 지표 2종).
- ★단, 5게이트 통과 확인 후 weight_rule 등록 (자체 정의 = 학술 baseline 부재 → tier 강등 가능성).

## 3. R1+R2 종합 → R3 잔여 빈틈

R1 빈틈 7 중 R2 해결 = 3건 (#1 일본, #3 OSS, #5 breadth). 잔여 4:

| # | 빈틈 | R3 처리 방법 |
|---|---|---|
| 2 | KCGS 등급 KRX ESG 포털 실제 PoC | 산업 subagent (Phase 5) 가 실 스크랩 시연 위임 |
| 4 | arxiv 2401.00001 sector rotation 한국 IC | WebFetch 본문 (R3) 또는 자체 baseline |
| 6 | 외국인 flow 가중 power 추정 | 자체 추정 (Phase 5 산업 subagent 실측 검증) |
| 7 | Tier 1 반도체 sub-cluster 별 dispatch | 본 분석가 결정 — 메모리·파운드리·장비 3 sub-dispatch 권고 |

## 4. R2 12축 self-audit

| 축 | 등급 | 비고 |
|---|---|---|
| A 이론 실재 | PASS | JPX/FSA 공식 + GitHub repo + skfoliolabs 도메인 일치 |
| B 실데이터 | N/A | source 인용, eq_kr 실측 Phase 5 이후 |
| C yaml 추적성 | N/A |  |
| D PIT | N/A | reports 2024-2026 최신 |
| E 자문 비판·환각 | **PASS** (R1 의 E PARTIAL 보강 — Pzena/BNY/JPMAM/JPX 다중 source cross-verify) |
| F 반증·기각 | PASS | R1 12 균등 가설 기각 유지 + R2 자체 정의 breadth 의 tier 강등 가능성 명시 |
| G 검정력 | N/A |  |
| H 미해결 | PASS | 4 항목 명시 |
| I-L | N/A |  |

R2 종합 verdict: 일본 baseline 강신뢰 / OSS 권고 강신뢰 / breadth 자체 정의 tier 강등 가능성 명시.

## 5. R2 → R3 (또는 direction.md 직접 작성)

R3 진입 시 잔여 4 빈틈 처리. 직접 작성 시 빈틈 4 = open_questions 명시 + 산업 subagent (Phase 5) 위임.

권고: R3 skip + 직접 direction.md 작성 (R1+R2 = 산업 분할 Tier 결정 + frame v2 input 충분, 잔여 4 = subagent 위임 의무).

## 6. R2 산출

- 본 consult-round-2.md
- archive: `~/.claude/docs/archive/research-raw/eq-kr-r3-r2-japan-toraniko-breadth-native-20260530.txt`
- memory: `~/.claude/memory/research/eq-kr-r3-r2-japan-toraniko-breadth.md`
- MEMORY 인덱스 1줄 추가
