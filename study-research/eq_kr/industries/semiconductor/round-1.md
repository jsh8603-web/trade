# round-1 — 반도체 산업 이론·가설 (2026-05-31, Tier 1 subagent)

> SSOT = frame.md v2 §1 Tier 1 / §3 Layer 3 / §M4 5게이트. as_of = 2026-05-31.
> 본 라운드 = 이론 정리 + 가설 8 + Layer 3 cycle 지표 후보 list. round-N 은 자문 추가 시 (필요 시만).

## §1. universe (frame §1 Tier 1, ★KOSPI 50.44% 집중)

| ticker | 회사명 | sub-cluster | 시총 비고 |
|---|---|---|---|
| 005930 | 삼성전자 | 메모리 + 파운드리 통합 | KOSPI 시총 1위 (~25% 단독, 우선주 포함 30%+) |
| 000660 | SK하이닉스 | 메모리 (HBM 1위) | KOSPI 시총 2-3위, HBM3E 엔비디아 단독공급 (2024-2026) |
| 042700 | 한미반도체 | 후공정 장비 (TC Bonder for HBM) | KOSDAQ → KOSPI 이전, HBM capex 직접 수혜 |
| 000990 | DB하이텍 (참고) | 파운드리 8인치 specialty | 보조 universe, sub-cluster 검증용 |

★ 동적 universe = `KrxSectorProvider.get_sector_map(as_of, market='KOSPI'/'KOSDAQ')` WICS 매핑 시점별. 정적 3+1 = round-1 분석 기준.

★ sub-cluster 3 분할 명시 (Tier 1 frame §1 권고):
- **메모리** = 005930 (삼성전자, 메모리 비중 ~50%), 000660 (SK하이닉스, 메모리 100%) — DRAM/NAND/HBM cycle 직접 노출
- **파운드리** = 005930 (삼성 파운드리 비중 ~15%), 000990 DB하이텍 — TSMC capex follow + 비메모리 cycle
- **장비** = 042700 (한미반도체) + 비universe (원익IPS, 피에스케이, 이오테크닉스 등) — capex cycle 후행 1-2Q

★ 본 라운드 핵심 분석 unit = **메모리 (005930 + 000660)** + **장비 (042700)** 2 sub-cluster. 파운드리는 005930 내부 segment + DB하이텍 (시총 작음) → 별도 측정 시도 + N gate 한계 명시.

★ frame §1.6 분석 unit ↔ portfolio label 분리: "반도체" sleeve = 005930+000660+042700 eq-weight 가 user label 이지만, factor β 측정 시 메모리 sub (005930+000660) 와 장비 sub (042700) 부호 다를 가능성 (HBM capex cycle 의 reverse exposure) → sub-cluster 별 β 측정 의무.

## §2. 산업 cycle 이론 (theory-notes.md 후속 정독)

### 2.1 DRAM/NAND 메모리 cycle (4 phase, 2-3년 주기)

- **Phase 1 회복** = 감산 종료 + 재고 정상화 → ASP yoy 반등 (예: 2024-Q1 DRAM ASP +18% qoq)
- **Phase 2 호황** = AI capex 가속 + 데이터센터 수요 → ASP yoy 30-60% 상승, 가동률 95%+
- **Phase 3 둔화** = 신규 capa 가동 → 공급 과잉 우려, ASP yoy peak-out
- **Phase 4 침체** = 재고 축적 + ASP yoy 음전환 → 감산 결정 → Phase 1 재진입
- **이론 출처**: DRAMeXchange, Gartner DRAM Quarterly, 삼성/SK 분기 컨퍼런스콜 (CEO commentary)
- **2024-2026 단계**: AI HBM 수요 폭증 → 일반 DRAM 까지 spillover → 2024-Q3 ~ 2026-Q2 호황 진입. 일반 DRAM ASP yoy +40% (TrendForce 2026-Q1).

### 2.2 HBM (High Bandwidth Memory) sub-cycle (★2024-2026 핵심)

- **HBM3E** = 12-Hi stack, 36GB/cube, 9.6Gbps. 엔비디아 H200/GB200/B200 에 단독 채택 (SK하이닉스 2024-Q1 entry, 삼성 2025-Q1 follow).
- **HBM4** = 2026-2027 양산 (16-Hi, 64GB/cube). 삼성-엔비디아 quality 이슈 (2024-2025) → 2025-Q4 통과 → 2026-Q3 mass production 진입.
- **시장 규모** = 2023 $4B → 2024 $14B → 2025 $30B → 2026 $40B+ (Yole Group 2026 forecast).
- **CAPEX cycle** = HBM 1B GB 당 capex ~$25B (DRAM 일반 $8B). 한미반도체 TC Bonder = HBM 후공정 핵심 장비, 2024-2026 capex 직접 수혜.

### 2.3 파운드리 cycle (TSMC follow)

- **TSMC 2024-2026 capex** = $30-35B/년 (3nm/2nm 가속). 삼성 파운드리 추격 → 2025 2nm 양산, 수율 70%+ 목표.
- **글로벌 점유율** = TSMC 60% / 삼성 11% / GF 6% / UMC 5%. 삼성 점유율 횡보 (2022-2025).
- **이론 가설**: 삼성 파운드리 segment 매출 = TSMC capex 의 leading 1-2Q follow (장비 동조).

### 2.4 외국인 flow + 한국 cluster dynamic

- **외국인 시총 비중** = 삼성전자 ~54%, SK하이닉스 ~52% (2026-05 기준, 가장 높은 종목군).
- **MSCI Korea cap** = 삼성전자 cap 25% 초과 risk (2024-2025). MSCI 분할 편입 (보통주/우선주) 이력.
- **외국인 flow 1순위 driver** = frame §3 신지표 4 #4 (외국인 flow regime, 28일 z-score) → 메모리 sub 직접 측정 의무.

### 2.5 환율 노출 (USDKRW)

- **수출 비중** = 삼성전자 메모리 95%+ 해외, SK하이닉스 95%+. USDKRW 강세 → 원화 환산 매출 직접 +.
- **다만**: 삼성/SK 환헤지 비율 30-40% (장기 contract) → USDKRW yoy +10% 시 매출 환산 +6-7% (산술 +10% 아님).
- **2차전지 H1 (USDKRW 강세 → 셀 outperform) 와 동일 메커니즘**. 단 반도체 수출 비중 더 큼.

## §3. Layer 3 cycle 지표 후보 list (frame §3 Tier 1 권고)

| # | 지표 | 정의 | 무료 소스 | 5게이트 통과 가능성 |
|---|---|---|---|---|
| **S1** | SOXX ETF yoy | iShares Semiconductor ETF yoy (반도체 글로벌 cycle proxy) | yfinance SOXX | ★★★ 2001~ 표본 충분, 한국 메모리 corr > 0.7 알려진 사실 |
| **S2** | SMH ETF yoy | VanEck Semiconductor (TSMC/NVDA 가중치 높음) | yfinance SMH | ★★★ TSMC 가중치 높아 파운드리 sub 직접 proxy |
| **S3** | NVDA price yoy | 엔비디아 yoy (AI capex / HBM 수요 sentiment proxy) | yfinance | ★★★ HBM cycle 직접 proxy, 2023~ |
| **S4** | USDKRW yoy | 환율 yoy (frame Layer 2 기본 4종) | FxStore PIT | ★★★ 자동, 수출 비중 95%+ |
| **S5** | 월간 한국 반도체 수출 yoy | 관세청 수출입통계 반도체 HS 코드 (8542) | data.go.kr 무료 | ★★★ frame Layer 2 기본 4종 (월간수출), 직접 매핑 |
| **S6** | DRAM 현물가 proxy | DRAMeXchange 부분공개 → SMH/SOXX yoy 대체 (1차) → DB하이텍 매출 yoy (2차) | yfinance + DART | ★★ proxy, 직접 측정 부재 |
| **S7** | TSMC capex yoy | TSMC 분기 보고 capex (10-K, ARS) | 수동 입력 | ★ 분기 데이터, N=20-30 한계 |
| ★S8 | KRW × foreign_flow regime | (USDKRW yoy) × (외국인 28일 z) 교호 | FxStore + krx_flows | ★★ direction.md H3 매핑, 외국인 flow + KRW 결합 |
| ★S9 | HBM 이벤트 ledger | NVDA H100/H200/B200 출시 / SK HBM3E entry / 삼성 HBM4 양산 | 수동 event ledger | ★ event study, N=4-6 |

★ 채택 우선순위 = S1, S2, S3, S4, S5 (★★★) + S6, S8 (★★) → 7 지표 실측 시도. S7 (TSMC capex), S9 (HBM event) = N 부족, 탐색적 finding.

★ DRAM 현물가 직접 무료 API 부재 (DRAMeXchange 유료, TrendForce 유료). SMH/SOXX yoy + DB하이텍 매출 yoy proxy (correlation > 0.7 알려진 사실, round-N 검증 의무).

## §4. 핵심 가설 8 (frame §10 — H1~H8)

### H1. USDKRW 강세 → 메모리 sub (005930, 000660) outperform (수출주 베타)

- **메커니즘**: 메모리 매출 95%+ 해외 (US, 중국, EU). 원화 환산 매출 증가 → 영업이익 확대. 환헤지 30-40% → 효과 70%만 통과.
- **측정**: 메모리 sub 평균 (005930 + 000660 eq-weight) y20d vs USDKRW_yoy lag 0/1/3M, monthly. β > 0 prior.
- **반증조건**: lag-corr 모든 lag |ρ| < 0.10 OR 부호 음 → 가설 기각 (수출 베타 무효).
- **5게이트 prior**: N 충분 (월간 90+ months, 2018-2026) / SE OK / Power high / FDR 적용 (7 가설) / OOS 2023-2026.

### H2. AI HBM cycle (NVDA proxy) → SK하이닉스 (000660) + 한미반도체 (042700) outperform

- **메커니즘**: NVDA = AI capex / HBM 수요 1순위 sentiment proxy. SK하이닉스 HBM3E 단독공급 (2024-2026) + 한미반도체 TC Bonder 핵심 장비.
- **측정**: 000660 + 042700 각각 y20d vs NVDA_yoy lag 0/1/3M corr. 005930 도 측정 (HBM 후발 → corr 약함 prior).
- **반증조건**: corr < +0.30 → NVDA proxy 무효, alternative (S2 SMH) 사용.
- **5게이트 prior**: ★ NVDA AI 사이클 시작 2023-Q2 → 표본 36 months (n<48). Tentative tier 격하 가능성.

### H3. 한국 반도체 수출 yoy → 메모리 sub 동조 (lag 0-1M)

- **메커니즘**: 한국 월간 반도체 수출 (HS 8542) = 글로벌 메모리 수요 leading indicator. 삼성/SK 매출 직접 mapping.
- **측정**: 메모리 sub 월간 평균 return yoy vs 반도체 수출 yoy lag 0/1/3M.
- **반증조건**: lag-corr 모든 lag |ρ| < 0.20 → 수출 cycle 무관 (의외 결과, multi-source 재확인).
- **5게이트 prior**: 월간 데이터 96 months (2018~) / SE OK / power 높음 / 단 수출과 주가 자기상관 강함 → Newey-West HAC SE 의무 (frame §M4 §1.4 자기상관 안전장치).

### H4. SMH/SOXX cycle → 반도체 산업 평균 동조 (글로벌 cycle spillover)

- **메커니즘**: SMH/SOXX = 글로벌 반도체 cycle proxy (TSMC/NVDA/AMD 가중치 높음). 한국 반도체 산업 = correlation > 0.7 알려진 사실.
- **측정**: 3종 평균 y20d vs SMH_yoy lag 0/1M, monthly. SOXX 도 측정 (control).
- **반증조건**: corr < +0.50 → 한국 반도체 글로벌 cycle 분리 (의외, 한국 idiosyncratic).
- **5게이트 prior**: N 96 months, SE OK, power 매우 높음, FDR pass, OOS 2023-2026.

### H5. 외국인 flow regime → 메모리 sub (frame §3 신지표 #4) ★Tier 1 핵심

- **메커니즘**: 메모리 = 외국인 시총 비중 50%+ (KOSPI 최상위). 외국인 28일 z-score 강매수 regime → 메모리 sub 동조 매수.
- **측정**: foreign_net_buy 28일 z-score regime (강매수/매도/중립) × 메모리 sub y20d Rank-IC.
- **반증조건**: regime 차이 < 0.05 IC OR p > 0.10 → flow 무효 (의외, Tier 1 가설 핵심).
- **5게이트 prior**: ★ pykrx KRX_ID/PW 인증 부재 → fallback = ETF flow (KODEX 반도체 091160 또는 TIGER Fn반도체TOP10 등) 사용.

### H6. 12-1 모멘텀 (한국 약효, direction.md H5 baseline) — 메모리 sub 한정

- **메커니즘**: 한국 시장 12-1 모멘텀 = US 대비 약효 (NCBI PMC11023228). 메모리 sub 한정 효과 검증.
- **측정**: 3종 월간 t-12 ~ t-1 cumulative return → 분위별 t+20d Rank-IC. universe 작음 (n=3) → 한계 명시.
- **반증조건**: IC > 0.05 → 한국 약효 통설 반박 (반도체 한정 모멘텀 alpha).
- **5게이트 prior**: N=3 종목 × 96 months = 288 obs. 산업 sub 한정 단정 위험 → "탐색적" + LOO 의무.

### H7. 메모리 sub vs 장비 sub spread (sub-cluster 분리 검증)

- **메커니즘**: HBM capex cycle ↑ 시 장비 (042700) outperform vs 메모리 (005930+000660). lead-lag 1-2Q.
- **측정**: spread (042700 y20d - 메모리 평균 y20d) vs NVDA_yoy lag 0/1/3M corr.
- **반증조건**: corr < +0.30 OR 부호 반대 → spread 무효, sub-cluster 분할 무의미.
- **5게이트 prior**: ★ frame §1.6 분석 unit vs portfolio label 분리 의무 → sub-cluster 별도 측정 본질.

### H8. PIT 펀더멘털 (Layer 1) — 메모리 OP margin yoy

- **메커니즘**: 005930/000660 분기 OP margin yoy = ASP cycle 직접 mapping. yoy 양극 → 다음 1Q forward return outperform.
- **측정**: 2 종목 분기 OP margin (DART vintage_policy=PIT) → t+1Q forward return Rank-IC (n=2 종목 × 32 분기).
- **반증조건**: IC < 0.05 OR 부호 음 → OP margin lookahead 무효.
- **5게이트 prior**: N=64 obs (작음). DART API 필요 → fallback = 매출 yoy (분기 공시).

## §5. 막힘 처리 plan (frame §11 라운드 가이드)

| # | 막힘 케이스 | 처리 |
|---|---|---|
| 1 | pykrx 외국인 flow KRX 인증 필요 | KODEX 반도체 ETF (091160) flow 대체 → ETF flow yoy proxy |
| 2 | DRAMeXchange 유료 | SMH/SOXX yoy proxy (correlation > 0.7) + DB하이텍 매출 yoy 보조 |
| 3 | DART API 키 부재 | DART 공시검색 수동 fallback (분기별 OP margin 4-5개만 입력) |
| 4 | toraniko 한국 KOSPI universe 적용 어려움 | numpy/pandas Fama-French 회귀 fallback (frame §M5 허용, raw IC + neutralized IC 둘 다 보고) |
| 5 | regime 36 cell N<24 cell collapse | 외국인 flow 3 cell 만 분해 (Macro 무관) → 3 cell fallback (frame §M3) |
| 6 | NVDA AI cycle 표본 36 months | Tentative tier 격하 + LOO p-value 의무 (frame `small-n-statistical-rigor.md`) |

## §6. 진행 다음 라운드

- ★ round-1 → 데이터 수집 (FDR + yfinance) → 실측 (Layer 1/2/3 validation-*.md) → 5게이트 → summary.yaml → 12axis-audit.md
- ★ 자문 필요 시점: H4 IRA event study N 부족 또는 H2 NVDA 36 months 한계 시 → claude-web/gemini-web 1회 폴백
- ★ 본 round-1 = 이론 + 가설 + Layer 3 후보 list 완성. round-N.md = 검증 라운드에서 데이터 부족 시만 생성.
