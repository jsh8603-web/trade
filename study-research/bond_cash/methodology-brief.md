# methodology-brief — bond_cash sub-cluster 분할 · 방법론 · 최종 구현 결과 (v2, 2026-05-30)

> Phase 2 산출. Phase 3 자문 (/gemini-web R1 + /claude-web R2 + 수렴 R3) 의 자기완결 입력.
> 자문 채널에 본 brief 통째로 전달 → 자문 답 → 본 분석가 비판·검증 → consult-round-{N}.md 누적.
> 9 작업방 동시 자문 채널 경합 우려 → ★ **WebSearch native 폴백 default 진입** (이전 5R 동일 패턴).

## §A sub-cluster 분할 (자문 핵심 질문)

### 현재 잠정 결정 (사용자 메시지 명시, 7 sub-cluster)
국채 duration bucket 3종 (2Y / 10Y / 30Y) + credit 2종 (IG / HY) + 현금 2종 (MMF / 단기 T-Bill)

### sub-cluster 분할 후보 (7 sub-cluster) — 자문 검증 대상

| # | sub-cluster | 대표 ETF | duration | credit | regime sensitivity | cycle driver |
|---|---|---|---:|---|---|---|
| 1 | tsy_long | TLT, TLH, EDV | ≈17 (TLT)~25 (EDV) | AAA (Tsy) | rate-down + flight-to-quality | DGS10, real rate, MOVE |
| 2 | tsy_mid | IEF, GOVT | ≈8 (IEF) | AAA | curve belly + Fed expectations | DGS10, DGS5 |
| 3 | tsy_short | SHY, VGSH | ≈2 (SHY) | AAA | rate-cut optionality | DGS2, FEDFUNDS |
| 4 | ig_credit | LQD, IGSB | ≈8 (LQD) | A-/BBB+ | credit spread + Tsy duration | BAA10Y, HY OAS proxy |
| 5 | hy_credit | HYG, JNK | ≈4 (HYG) | B+/BB | credit cycle + recession lead | HY OAS, NFCI |
| 6 | cash_tbill | BIL, SHV | ≈0.1~0.5 | AAA (T-Bill) | carry + Fed cut optionality | FEDFUNDS, DGS3MO |
| 7 | tips | TIP, VTIP, STIP | ≈7 (TIP) | AAA (TIPS) | inflation hedge + real rate | DFII10, T5YIE |

총 ETF 가중 추정: ~95% (USA 채권 시장 주요 sleeve 커버). 나머지 ~5% = international bond / EM bond / MBS (별도 sleeve 가능).

### 자문 질문 (sub-cluster 분할)

**Q1** — 7 sub-cluster 분할이 적절한가? subagent 토큰 비용 (7 × opus 1m 200~500k = 1.4~3.5M 토큰) vs coverage trade-off.

**Q2** — sub-cluster 외 다른 차원 분할이 더 나은가? — (a) credit quality (Tsy/IG/HY) 단축 (b) duration bucket 만 (long/mid/short/cash) (c) **regime-conditional 분기** (rate-up vs rate-down 별 카드 분리).

**Q3** — TIPS sub-cluster 별도 처리할지 IG/Tsy 와 통합할지? — TIPS 는 real rate 분리 채널이라 명목 듀레이션과 다른 archetype.

**Q4** — Cash sleeve (MMF + T-Bill) 단일 처리 또는 분리? — MMF (PIMCO style) vs SHV (1Y T-Bill) 의 rate-cut optionality 패턴 다름.

**Q5** — international bond (BNDX) / EM bond (EMB) sub-cluster 추가 우선순위? 자국 USD 채권만 vs 글로벌.

**Q6** — 7 sub-cluster 중 우선순위 (Tier 1 = 즉시 dispatch / Tier 2 = 후속) 어떻게 분류?
   - Tier 1 후보: tsy_long (KOSPI 의 반도체 대응 = 채권 시장 50% 비중) + hy_credit (recession lead 신호 본체) + tips (inflation hedge 분리 채널)
   - Tier 2: tsy_mid, tsy_short, ig_credit, cash_tbill

## §B Layer 3 bond_cash 특화 cycle 지표 후보 (★MOVE / ACM term premium 의무 포함)

### ★사용자 누락 critical 지표 (의무 추가)
| 지표 | 본질 | source | 우리 시스템 |
|---|---|---|---|
| **★ MOVE index** | 채권 변동성 (= 주식의 VIX 등가). 사이징 직결 — 리스크게이트. | CBOE / Bloomberg / FRED `MOVE` (가용 여부 검증) | **미보유** → collector_plan |
| **★ ACM term premium** | Adrian-Crump-Moench 모델 분해. Treasury yield = expected short rate + term premium. NY Fed 공개. | NY Fed Staff Reports 599 (2008-) + 갱신 시계열 | **미보유** → collector_plan |
| HY OAS (BAMLH0A0HYM2) | credit cycle 본체 (이미 in-system, 단 최근 3년 한계 발견) | FRED (ICE 라이센스) | ✅ (제한) |
| Yield curve (T10Y2Y) | recession lead time 본체 | FRED | ✅ |
| Real rate (DFII10) | 명목 듀레이션과 분리축 | FRED | ❌ (요청) |

### sub-cluster 별 Layer 3 지표 후보 (5개 이내)

| sub-cluster | Layer 3 cycle 지표 후보 | 무료 source |
|---|---|---|
| **tsy_long** | DGS10 변화 · ACM term premium 10Y · MOVE · QE flow · 외국인 Tsy holding | FRED + NY Fed + 미 재무부 TIC |
| **tsy_mid** | DGS5 · DGS10-DGS5 belly · curve 형태 (butterfly) · Fed dot plot · 채권 펀드 flow | FRED + Fed dot plot |
| **tsy_short** | DGS2 · FEDFUNDS · OIS spread · Fed funds futures implied rate · T-Bill 발행량 | FRED + CME FedWatch |
| **ig_credit** | BAA10Y · LQD spread · investment-grade default rate · 회사채 발행 supply | FRED + Moody's 공개 |
| **hy_credit** | HY OAS · NFCI · HY default rate · loan covenant index · CLO equity tranche return | FRED + S&P LCD 일부 무료 |
| **cash_tbill** | FEDFUNDS · DGS3MO · CB reserves · RRP usage · T-Bill auction yield | FRED + 미 재무부 |
| **tips** | DFII10 · T5YIE · TIPS auction breakeven · 5Y5Y forward · oil price | FRED + 미 재무부 |

### 자문 질문 (Layer 3)

**Q7** — ★MOVE index FRED 가용성 검증 — `MOVE` 시리즈 직접 다운로드 가능한가? 다른 source (Bloomberg / ICE) 필요?

**Q8** — ★ACM term premium NY Fed 공식 시계열 갱신 빈도·릴리즈 lag·다운로드 endpoint? historical 1961~ 가용?

**Q9** — sub-cluster cycle 지표 lag 패턴 (1d/1w/1Q) 어떻게 frame 박제? sub-cluster 마다 lag 다름 (tsy_long 즉시 vs hy_credit 4-8주 lead).

**Q10** — Layer 3 지표 중복 (예: tsy_long·tsy_mid 모두 DGS10) 어떻게 처리? sub-cluster 별 sub-correlation 분해?

## §C 최종 구현 결과 (자문 출력 기대)

### 통합 산출
- **bond_cash 통합 study_session.yaml** (STUDY-KIT §3 7블록 — lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan + STATUS)
- **N sub-cluster summary.yaml** (frame.md §7 양식 — 각 sub-cluster lens·indicators_passed·relationships_passed·weight_rule_candidates·confidence_hooks·collector_plan·open_questions)
- **코드 wiring**:
  - `core/brain/fred_adapter.py` (FRED_SERIES 추가 6+2종 = DGS10/DGS2/DGS3MO/DFII10/FEDFUNDS/MORTGAGE30US + ★MOVE + ★ACM term premium)
  - `core/assume/weight_card.py` (archetype = duration bucket × credit quality)
  - `core/brain/regime_to_weights.py` (BASE_WEIGHTS bond/cash dynamic floor)
  - `etf_track.py` (신설, sleeve 내부 ETF 사이징 — direction.md ★요청 #4)

### 평가 게이트 (Phase 6)
- 평가 subagent (별, opus 1m) 가 evaluation-axes.md 12축 기준 평가
- N sub-cluster 모두 PASS → 통합 yaml 작성 진입 (Phase 7)
- PARTIAL/FAIL → 해당 sub-cluster 재dispatch (frame 부분 보강 가능)
- 최대 2회 재dispatch (3회 시 사용자 보고 + 자문 추가)

### 자문 질문 (최종 구현 결과)

**Q11** — sub-cluster summary.yaml → bond_cash 통합 yaml 합산 시 archetype 충돌 처리 방법? 같은 ETF 가 2 sub-cluster 에 걸치는 경우 (예: LQD = ig_credit + mid-duration).

**Q12** — 평가 subagent PARTIAL/FAIL sub-cluster 재dispatch 회수 한계? 자문 인터벤션 임계?

**Q13** — ★MOVE 사이징 적용 — sleeve-level 가중 vs sub-cluster 가중 (예: hy_credit 만 MOVE 적용 vs 전 sub-cluster 동일 사이징). 어디 layer 가 본질?

**Q14** — ★ACM term premium 분해를 듀레이션 cycle 카드 (블록4 weight_rules) 에 어떻게 inject? expected short rate 항 vs term premium 항 분리 가중?

## §D Inv 인프라 + collector_plan

### 가용 인프라 (frame §3 + v1 산출 finding)
- **FRED**: `core/brain/fred_adapter.py` (17 시리즈, 채권 본체 6종 부재 — collector_plan)
- **fredapi**: D:/projects/Inv/.env FRED_API_KEY 사용 가능 ✅ (v1 V1-V4 검증에서 확인)
- **yfinance**: ETF 일별가 풀 historical 가용 ✅ (TLT/IEF/SHY/BIL/HYG/LQD/TIP/SPY 등)
- **sleeve**: `core/brain/regime_to_weights.py` SLEEVES = [us_stock, kr_stock, commodity, gold, **bond**, **cash**, coin]
- **lens 주입**: `core/assume/judge.py` _call_qwen_with_lens (eq_kr 와 공유)
- **falsification**: `core/assume/weight_falsification.py` score_ic_breakdown_eprocess (e-CUSUM, alpha=0.05)

### v1 산출 finding (collector_plan 기존 + 신규)
| ID | 항목 | 우선순위 | 사유 |
|---|---|---|---|
| C1 | DGS10/DGS2/DGS3MO/DFII10/FEDFUNDS/MORTGAGE30US | **P0** | 채권 본체. v1 yaml block6 등록 |
| C2 | ETF 일별가 (TLT/IEF/SHY/BIL/HYG/LQD/TIP) PIT VintageStore | **P0** | sub-cluster forward return 본체 |
| C3 | ICE BofA US Treasury Index TR (BAMLCC0A0CMTRIV) | P1 | 장기 OOS 백테스트 |
| C4 | **★MOVE index** (BBG / CBOE / FRED 가용성 검증) | **P0** | 사이징 직결 (사용자 메시지 #3) |
| C5 | **★ACM term premium** (NY Fed 공식, 10Y) | **P0** | term premium 분해 (사용자 메시지 #3) |
| C6 | VIX (VIXCLS) | P1 | 3-signal warning 합성 (v1 R3) |
| C7 | EPU (USEPUINDXD) | P2 | Fed spillover 증폭 (v1 R5) |
| C8 | KTB ETF (KOSEF 국고채) | P2 | KR sleeve 확장 |
| C9 | BAMLH0A0HYM2 1996-12~2023-05 historical (ICE 라이센스) | **P0** | 600bps event study 가능 (v1 V1 발견) |
| C10 | RRP usage / T-Bill auction yield | P2 | cash sleeve 보강 |

### 자문 질문 (Inv 인프라)

**Q15** — ★MOVE index 무료 source 진짜 가용한가? FRED `MOVE` 또는 ICE `ICE BofA MOVE Index` 직접 다운로드 endpoint 검증 필요.

**Q16** — ★ACM term premium NY Fed `https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls` 같은 공식 endpoint 가용? CSV/XLSX update 빈도?

**Q17** — BAMLH0A0HYM2 historical 1996-12~2023-05 ICE 라이센스 — 합리적 단일 라이센스 비용 추정? 또는 대체 시리즈 (S&P U.S. HY Corporate Bond Index TR) 가용?

## §E 자문 라운드 진행 계획

| Round | 채널 | 목적 |
|---|---|---|
| R1 | /gemini-web 또는 WebSearch | sub-cluster 분할 (Q1-Q6) + Layer 3 지표 (Q7-Q10) + ★MOVE/ACM 본질·source (Q15-Q16) |
| R2 | /claude-web 또는 WebSearch | 최종 구현 (Q11-Q14) + ICE 라이센스 대체 (Q17) + 통합 yaml 구조 |
| R3 | 두 채널 응답 비교 + 수렴 또는 잔여 빈틈 메우기 | direction.md 작성 직전 |

자문 채널 경합 자제 — 1 자문씩, 응답 후 다음. **WebSearch/WebFetch 폴백 default 진입** (이전 5R 패턴, 9 작업방 동시 점유 우려).

## §F 자문 출력 의무 (자문 채널 응답에서 받을 것)

각 라운드 자문 답을 받으면:
1. 답을 그대로 yaml 박제 ★금지★
2. 본 분석가 (bond_cash supervisor) 비판·환각 검증·교차 cross-check
3. consult-round-{N}.md 에 (a) 자문 원문 quote (b) 본 분석가 비판 (c) 채택/기각 결정 (d) 다음 라운드 질문 명시
4. 수렴 후 direction.md 작성

⛔ 자문 그대로 받으면 evaluation-axes §L1.5 위반 (자문 그대로 코드화 = Layer 1 FAIL).
