# consult-round-1 — eq_kr Phase 3 자문 R1 (2026-05-30)

> v2 절차 라운드 1. methodology-brief.md §A~D 의 자문 질문 Q1-Q15 중 산업 분할 핵심 (Q1-Q6) 우선.
> R1 채널 = WebSearch 폴백 2회 (gemini-web/claude-web 9 작업방 동시 자문 채널 경합 회피).
> 3계층 적재 완료: archive raw (eq-kr-r3-r1-sector-concentration-native-20260530.txt) + memory (eq-kr-r3-r1-sector-concentration-2025) + MEMORY 인덱스.

## 0. R1 질문 (Q1-Q6 산업 분할 우선)

| Q | 본문 |
|---|---|
| Q1 | 4 → 12 산업 분할 적절한가? 토큰 비용 vs coverage |
| Q2 | 다른 차원 분할 (size · style · foreign-holding · 밸류업 편입) 우월? |
| Q3 | AI tech 와 반도체 분리할지 통합할지 |
| Q4 | 바이오 별 처리 (sub-cluster) 필요? |
| Q5 | KOSDAQ 소형 처리 방법 |
| Q6 | 12 산업 Tier 분류 |

## 1. R1 입력 (WebSearch 2건 + 자체 분석)

### 1.1 WebSearch A — Korean equity quant factor sector partition (학술/OSS)
- NCBI PMC11023228 (2024): GARCH-MIDAS + macro factor × size/style/sector heterogeneous (한국 2009-2022)
- arxiv 2601.07131 (2026 추정): Korean equity ML 2020-2024 2.79M obs 2,439 종목 패널
- arxiv 2401.00001: Sector rotation factor model + 모멘텀·반전 유의
- toraniko OSS (MIT): multi-factor equity risk model

### 1.2 WebSearch B — KOSPI 반도체 집중 (실무 reports 2026-05 최신)
★ **핵심 발견**: 삼성전자 + SK하이닉스 = KOSPI 시총 50.44% (3,394조원)
- 5월 초 42.2% → 월말 50.44% 단기 급등
- 9 of 10 stocks decline = 반도체 2사 dominance + breadth divergence
- 외국인 15세션 50조원 매도 = 'Roller-KOSPI swift reversal' BTIG 경고
- KODEX AI Semiconductor ETF = 삼성·SK 각 25% cap (AI tech + 반도체 ETF 단일화)
- MSCI Korea index 가중 미국 diversified 규제 cap 초과 (Goldman Sachs)

### 1.3 자체 분석 (eq_kr 담당 분석가 시각)
이 finding 이 methodology-brief.md §A 12 균등 분할 가설을 ★기각★ 시킨다 — R1 의 가장 큰 산출.

## 2. Q1-Q6 R1 답 (자문 + 자체 비판)

### Q1 — 4 → 12 산업 분할 적절성
**R1 결정**: 12 산업 명시 OK, 그러나 **균등 분할 ★기각★** — 가중 비례 Tier 분할.
- Tier 1 (KOSPI 40%+, 단독 sleeve) = 반도체
- Tier 2 (각 5-10%) = 자동차 · 금융 · 2차전지
- Tier 3 (각 2-5%) = AI tech · 화학 · 정유 · 조선 · 바이오 · 통신 · 철강 · 소비재
- subagent 토큰 비용 = Tier 1 깊이 dispatch (opus 1m 500k+) / Tier 2 중간 (300k) / Tier 3 경량 (150-200k)
- 근거: WebSearch B finding (KOSPI 50% 반도체 단일 집중)

### Q2 — 다른 차원 분할
**R1 결정**: 산업 분할 + size/foreign-holding 결합 **2 축 분할** 권고.
- 1축 = 산업 (12 Tier)
- 2축 = 외국인 보유율 (high/low) — R1 finding (Roller-KOSPI 15세션 50조) 으로 외국인 flow 가 단기 가격 driver 1순위 확정
- 밸류업 편입 = ★별 flag (Tier 2 금융이 핵심 수혜 → financial subagent 가 event study 의무)
- size = Tier 와 부분 겹침 (Tier 1 = 대형 / Tier 3 = 소형 다수) — 별 차원 불필요

### Q3 — AI tech 와 반도체 분리 vs 통합
**R1 결정**: **분리 sleeve + cross-link 명시**.
- 시장 인식 통합 (KODEX AI Semi ETF 25% cap 각) — finding 자체
- 그러나 driver 다름 = NAVER·카카오 (광고 cycle) vs SK하이닉스 (DRAM cycle)
- 분리하되 cross-correlation 분석 필수 (AI tech 종목의 SOX/DRAM proxy beta 측정)
- AI tech sub-cluster = (a) 플랫폼·광고 (NAVER·카카오) (b) SaaS·서비스 (안랩·디어유) — driver 더 다름

### Q4 — 바이오 별 처리
**R1 결정**: 별 처리, sub-cluster 분할 명시.
- 바이오 sub-cluster: (a) 합성신약 (대웅·유한양행) (b) 바이오시밀러 (셀트리온) (c) CMO·CDMO (삼성바이오로직스) (d) 백신·진단 (SK바이오사이언스·씨젠) (e) 임상 단계 별
- driver = FDA 승인 시점 + 임상 단계 + NIH 예산 → ★event study 중심 (Rank-IC 시계열 약함)
- 5게이트 통과 어려울 가능성 — structural prior (저신뢰) tier 우선

### Q5 — KOSDAQ 소형 처리
**R1 결정**: KOSDAQ 소형 = 별 sub-sleeve, 각 산업 Tier 내 sub-cluster.
- 반도체 Tier 1 → KOSPI 대형 vs KOSDAQ 소형 분할 (장비·부품 = KOSDAQ 다수)
- 2차전지 → KOSPI (LG에솔·삼성SDI) vs KOSDAQ (에코프로비엠·엘앤에프)
- 외국인 신호 약함 (size cap 0.05) — frame v1 명시 유지
- 개인 주도 모멘텀 + 반전 = KOSDAQ retail beta 신지표 (frame v1 indicators §B 일치)

### Q6 — Tier 분류 (Q1 답과 통합)
- **Tier 1 (단독 dispatch · opus 1m 500k+)**: 반도체 (sub: 메모리 / 파운드리 / 장비)
- **Tier 2 (중간 dispatch · 300k)**: 자동차 · 금융 · 2차전지
- **Tier 3 (경량 dispatch · 150-200k)**: AI tech · 화학 · 정유 · 조선 · 바이오 · 통신 · 철강 · 소비재
- 총 12 subagent dispatch — Tier 별 토큰 차등

## 3. R1 신규 발견 (frame.md 갱신 입력)

### 3.1 외국인 flow 가중 ★강화 (frame v1 0.18 → 0.20+)
- R1 finding: 15세션 50조 매도 = 일 3조원+ = 사상 극단
- 5게이트 통과 확인 후 base_weight 상향 — IC 분포 + CI + OOS 의무

### 3.2 신지표 후보 추가 (frame Layer 2 또는 신 Layer)
- **breadth indicator** = (가중 KOSPI return) - (동등가중 KOSPI return) — 반도체 dominance 측정
- **MSCI cap 초과 flag** = 글로벌 패시브 flow 차단 시점 (이벤트 변수)
- **ETF leverage flow** = KODEX 등 leveraged ETF 순매수 → 반도체 2사 가격 영향
- **외국인 flow regime** = 강매수 / 매도 / 중립 신규 cell 차원 (frame §M3 macro regime + flow regime 추가)

### 3.3 frame §M3 regime 차원 확장
- v1: Macro 4 (Reflation/Recovery/Overheat/Slowdown) × KRW 3 (강세/중립/약세) = 12 cell
- v2 (R1 반영): Macro 4 × KRW 3 × **외국인 flow 3 (강매수/매도/중립)** = 36 cell
- ⚠️ cell N 부족 우려 → effective-N 게이트 우선 (frame §M4 N gate ≥ 24 의무 강화)

## 4. R1 잔여 빈틈 (R2 입력)

| # | 빈틈 | R2 채널 |
|---|---|---|
| 1 | e-KJFS 본문 일본 비교 (round-2 internal error 1건 미수령) | /gemini-web 또는 WebSearch |
| 2 | KCGS 등급 KRX ESG 포털 무료 스크랩 실제 PoC | /claude-web 또는 코드 검증 |
| 3 | toraniko OSS vs skfolio 한국 적용 비교 | /claude-web 실무 |
| 4 | arxiv 2401.00001 sector rotation 한국 IC 인용 | WebFetch 본문 |
| 5 | breadth indicator 학술 baseline (US-Korea 비교) | /gemini-web 학술 |
| 6 | 외국인 flow 가중 5게이트 통과 가능성 사전 power 추정 | 자체 추정 |
| 7 | Tier 1 반도체 sub-cluster (메모리/파운드리/장비) 의 별 dispatch 필요성 | /claude-web 실무 |

## 5. R1 8축 자기 점검 (AUDIT-GUIDE 12축 application 사전)

| 축 | 등급 | 비고 |
|---|---|---|
| A 이론 실재 | PASS | 8 URL 실재 + PMC ID + arxiv ID 매칭 |
| B 실데이터 | N/A | R1 = source 인용, eq_kr 실측 R2-3 이후 |
| C yaml 추적성 | N/A | yaml 미작성 |
| D PIT | N/A | 외부 reports 2026-05 최신 |
| E 자문 비판·환각 | **PARTIAL** | Goldman cap·BTIG reversal·외국인 50조 단일 source — R2 cross-source 필요 |
| F 반증·기각 | **PASS** | 12 균등 가설 → 50% 집중 finding 으로 기각 |
| G 검정력 | N/A | source 인용만 |
| H 미해결 | PASS | 7 항목 명시 (§4) |
| I 생존편향 | N/A |  |
| J 비용 | N/A |  |
| K 다중검정 | N/A |  |
| L 통합 PSD | N/A |  |

**R1 종합 verdict**: 산업 분할 12 Tier 결정 강신뢰 / 외국인 flow 가중 강화 강신뢰 / 단일 source 일부 finding (E PARTIAL) 은 R2 cross-source 의무.

## 6. R1 → R2 계획

- R2 채널 = /claude-web 단발 (1 자문씩 채널 경합 자제) 또는 WebSearch 추가 폴백
- R2 우선 = 빈틈 1·2·6 (e-KJFS 일본·KCGS PoC·외국인 flow power 추정)
- R3 = R1+R2 종합 + 잔여 빈틈 → direction.md (①이론수집 ②검증방향 ③가설 반증조건) 작성 → main 보고

## 7. R1 산출 파일

- 본 consult-round-1.md
- archive: `~/.claude/docs/archive/research-raw/eq-kr-r3-r1-sector-concentration-native-20260530.txt`
- memory: `~/.claude/memory/research/eq-kr-r3-r1-sector-concentration-2025.md`
- MEMORY 인덱스: 한 줄 추가 완료
