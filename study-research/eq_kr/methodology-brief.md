# methodology-brief — eq_kr 산업 분할 · 방법론 · 최종 구현 결과 (v1, 2026-05-30)

> Phase 2 산출. 3R 자문 (Phase 3 — /gemini-web R1 + /claude-web R2 + 수렴 R3) 의 자기완결 입력.
> 자문 채널에 본 brief 통째로 전달 → 자문 답 → 본 분석가 비판·검증 → consult-round-{N}.md 누적.

## §A 산업 분할 (자문 핵심 질문)

### 현재 잠정 결정 (frame v1, 4 산업)
반도체 / 2차전지 / 자동차 / 금융

### ★사용자 추가 지시 (2026-05-30) — 메인 섹터 놓치지 말 것
AI tech / 화학 / 정유 / 조선 / 바이오 / 통신 / 철강 / 소비재 등.

### 산업 분할 후보 (12 산업) — 자문 검증 대상

| # | 산업 | KOSPI/KOSDAQ 가중 (대략) | 대표 ticker (3-4) | 사이클 driver |
|---|---|---|---|---|
| 1 | 반도체 | ~25% | 005930 삼성전자, 000660 SK하이닉스, 042700 한미반도체, 240810 원익IPS | DRAM/NAND cycle, HBM 신기술, 가동률 |
| 2 | AI tech / 플랫폼 | ~7% | 035420 NAVER, 035720 카카오, 376300 디어유, 053800 안랩 | AI capex, 모바일 광고 cycle, SaaS, AGI 사이클 |
| 3 | 2차전지 | ~5% | 373220 LG에너지솔루션, 006400 삼성SDI, 247540 에코프로비엠, 003670 포스코퓨처엠 | EV cycle, 리튬·니켈, IRA |
| 4 | 자동차 | ~6% | 005380 현대차, 000270 기아, 012330 현대모비스, 011210 현대위아 | 글로벌 수요, ★USDKRW, 반도체 공급 |
| 5 | 금융 | ~10% | 055550 신한지주, 105560 KB금융, 086790 하나금융, 316140 우리금융 | 금리 cycle, NIM, ★밸류업 핵심 수혜 |
| 6 | 화학 | ~3% | 051910 LG화학, 011170 롯데케미칼, 009830 한화솔루션, 285130 SK케미칼 | 중국 수요, 유가, 에틸렌 스프레드 |
| 7 | 정유 | ~3% | 096770 SK이노베이션, 010950 S-Oil, 078930 GS, 005880 대한해운 | 유가, 크랙스프레드, 환율, OPEC+ |
| 8 | 조선 | ~2% | 329180 HD현대중공업, 010140 삼성중공업, 042660 한화오션 | 글로벌 신조선 cycle, LNG 수요, 환율 |
| 9 | 바이오·헬스케어 | ~3% | 207940 삼성바이오로직스, 068270 셀트리온, 028300 HLB, 326030 SK바이오팜 | FDA 승인, 임상 단계, NIH 예산 |
| 10 | 통신·미디어 | ~2% | 017670 SKT, 030200 KT, 032640 LG U+ | 5G·6G capex, ARPU, 콘텐츠 |
| 11 | 철강·소재 | ~2% | 005490 POSCO 홀딩스, 004020 현대제철, 010130 고려아연 | 중국 철강 가격, 철광석·연료탄, PMI |
| 12 | 식음료·소비재 | ~2% | 097950 CJ제일제당, 005180 빙그레, 004990 롯데지주, 097230 한진중공업홀딩스 | 내수 cycle, 환율 (원재료), 농산물 |

총 KOSPI 가중 추정: ~70%. 나머지 ~30% = 건설·유통·기타.

### 자문 질문 (산업 분할)

**Q1** — 4 → 12 산업 분할이 적절한가? subagent 토큰 비용 (12 × opus 1m 200~500k = 2.4~6M 토큰) vs coverage trade-off.

**Q2** — 산업 외 다른 차원 분할이 더 나은가? — (a) size (large/mid/small) (b) style (value/growth) (c) foreign-holding (high/low) (d) 밸류업 편입 여부.

**Q3** — AI tech 와 반도체 분리할지 통합할지? NAVER·카카오 (광고 cycle) 와 SK하이닉스 (메모리 cycle) 매우 다름.

**Q4** — 바이오 = 한국 변동성 최강 + 임상 단계별 매우 이질적. 별도 처리 (sub-cluster 분할 — 합성신약/바이오시밀러/CMO/CDMO) 필요한가?

**Q5** — KOSDAQ 작은 sub-cluster (테마·소형 바이오 caps) 어떻게 처리? 단독 sub-study 또는 sleeve 단위 잔여처리?

**Q6** — 12 산업 중 우선순위 (Tier 1 = 즉시 dispatch / Tier 2 = 후속) 어떻게 분류?

## §B Layer 3 산업 cycle 지표 후보 (산업별 5개 이내)

frame.md §3 Layer 3 에 4 산업 (반도체·2차전지·자동차·금융) 이미 명시. 본 brief 에 신규 8 산업.

| 산업 | Layer 3 cycle 지표 후보 (5개 이내) | 무료 source 후보 |
|---|---|---|
| AI tech / 플랫폼 | 모바일 광고 시장 yoy · Cloud capex (Big 3 합산) · AI 모델 발표 이벤트 · NAVER·카카오 DAU · 광고주 수 | 닐슨·메리츠/하이투자 분기 reports / 글로벌 Cloud capex Bloomberg / Tracker |
| 화학 | 에틸렌 스프레드 · NCC 가동률 · 중국 PE·PP 수요 · 유가 lag · 환율 | 한국석유화학협회 / KORES |
| 정유 | 크랙스프레드 (3:2:1) · 정제 가동률 · OPEC+ 감산 · SPR · 항공유 수요 | EIA (미국) / OPEC reports / IATA |
| 조선 | Clarksons 신조선 수주 · 유조선·LNG선 수주잔고 · SCFI 컨테이너 운임 · 환율 | Clarksons (유료 일부 무료) / SCFI 공개 |
| 바이오 | FDA 승인 건수 · 임상 단계 (1/2/3) 분포 · 라이센스 아웃 deals · NIH 예산 · 미국 보험 | FDA 공시 / clinicaltrials.gov / NIH 공개 |
| 통신·미디어 | 5G 가입자 · ARPU · capex cycle · 콘텐츠 매출 · 정부 통신비 정책 | 과기정통부 통계 / KT·SKT·LGU+ 분기보고서 |
| 철강·소재 | 중국 철강 가격 (HRC) · 철광석 (62% Fe) · 연료탄 · 글로벌 PMI · 환율 | Steel Home / TradingEconomics 무료 / S&P Global |
| 식음료·소비재 | 내수 매출 yoy · 환율 (원재료 수입) · 농산물 가격 (옥수수·밀·대두) · 인플레 | 통계청 소비자물가 / CME 농산물 |

### 자문 질문 (Layer 3)

**Q7** — 산업별 Layer 3 지표 무료 시계열 가용성 — 특히 Clarksons / NCC 가동률 / NIH / Big 3 Cloud capex 무료 출처 검증 필요.

**Q8** — 산업 cycle 지표 lag 패턴 (1Q/2Q/4Q) 어떻게 frame 박제? 산업마다 lag 다름 (반도체 1Q, 조선 4Q+).

**Q9** — Layer 3 지표 중복 (예: 화학·정유 모두 유가) 어떻게 처리? 산업별 sub-correlation 분해?

## §C 최종 구현 결과 (자문 출력 기대)

### 통합 산출
- **eq_kr 통합 study_session.yaml** (frame §3 7블록 — lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan + STATUS)
- **N 산업별 summary.yaml** (frame §7 양식 — 각 산업 lens·indicators_passed·relationships_passed·weight_rule_candidates·confidence_hooks·collector_plan_industry·open_questions)
- **코드 wiring**: stock/data (provider) + core/assume/weight_card (archetype 등록) + core/stock_track (사이징) 경로 (frame §code_change_plan 양식)

### 평가 게이트 (Phase 6)
- 평가 subagent (별, opus 1m) 가 evaluation-axes.md 기준 평가
- N 산업 모두 PASS → 통합 yaml 작성 진입 (Phase 7)
- PARTIAL/FAIL → 해당 산업 재dispatch (frame 부분 보강 가능)
- 최대 2회 재dispatch (3회 시 사용자 보고 + 자문 추가)

### 미국 주식 (eq_us) — ★main 책임 통지
- 사용자 추가 지시 (2026-05-30): eq_us 별 작업방 dispatch 필요
- 본 작업방은 eq_kr 만 처리. eq_us 자문 라운드도 별도.
- main 에 통지 의무 (psmux 보고 완료).

### 자문 질문 (최종 구현 결과)

**Q10** — 산업별 summary.yaml → eq_kr 통합 yaml 합산 시 archetype 충돌 처리 방법? 같은 종목이 2 산업에 걸치는 경우 (예: 포스코퓨처엠 = 2차전지·화학 + 철강).

**Q11** — 평가 subagent PARTIAL/FAIL 산업 재dispatch 회수 한계? 자문 인터벤션 임계?

**Q12** — 미국 주식 (eq_us) 산업 분할은 한국과 같은 N? GICS 11 sector 기반 vs 한국식 12 산업?

## §D Inv 인프라 + collector_plan

### 가용 인프라 (frame §3 + round-1/2 finding)
- **DART**: `stock/data/dart_provider.py` DartXbrlProvider — DART_API_KEY 부재 시 graceful empty
- **KRX 유니버스·상폐**: `stock/data/krx_universe.py` + `data/krx_snapshots.jsonl` (PIT)
- **KRX WICS·외국인 flow**: `stock/data/krx_flows.py` + `data/krx_sector_snapshots.jsonl` + `data/krx_flow_snapshots.jsonl`
- **FX**: `core/data/macro_market.py` FxStore (USDKRW PIT, 선구축 완료)
- **FRED**: `core/brain/fred_adapter.py` (HY OAS BAMLH0A0HYM2, real rate, DGS10/DGS2)
- **OSS refs**: `_refs/dart-fss`, `_refs/OpenDartReader`, `_refs/FinanceDataReader`
- **sleeve**: `core/brain/regime_to_weights.py` SLEEVES = [us_stock, **kr_stock**, commodity, gold, bond, cash, coin] — kr_stock 기존재
- **lens 주입**: `core/assume/judge.py` _call_qwen_with_lens 기구현
- **falsification**: `core/assume/weight_falsification.py` score_ic_breakdown_eprocess (e-CUSUM, alpha=0.05)

### collector_plan_industry (산업 추가 후보, 우선순위)
| ID | 항목 | 우선순위 | 자문 검증 |
|---|---|---|---|
| D1 | DART_API_KEY 발급 + 라이브 fetch | **P0** | 즉시 진행 |
| D2 | DART 사업의내용 지역별매출 + 중국 매출 비중 파싱 | P1 | 자문 후 |
| D3 | 한국 컨센서스 EPS (Naver Finance 역공학 또는 KIS API) | P1 | 자문 후 |
| D4 | ★KCGS 등급 (KRX ESG 포털 esg.krx.co.kr 무료) | **P1 격상** (round-2 finding) | 즉시 PoC |
| D5 | 공매도 잔고·규제 레짐 (KRX) | P2 | 자문 후 |
| D6 | DRAM 현물가 yoy (DRAMeXchange / $SMH proxy) | P1 | 자문 후 |
| D7 (신규) | Clarksons 신조선 수주 (조선) | P2 | 자문 — 무료 가용 여부 |
| D8 (신규) | 에틸렌·NCC 스프레드 (화학) | P2 | 자문 |
| D9 (신규) | 크랙스프레드 (정유) | P2 | 자문 |
| D10 (신규) | FDA 승인 + clinicaltrials.gov (바이오) | P2 | 자문 |
| D11 (신규) | Big 3 Cloud capex + 모바일 광고 시장 (AI tech) | P2 | 자문 |
| D12 (신규) | 중국 HRC 철강·철광석 (철강) | P2 | 자문 |

### 자문 질문 (Inv 인프라)

**Q13** — 추가 collector (D7-D12) 무료 source 우선순위? 어떤 산업이 데이터 가용성 최강 / 최약?

**Q14** — D4 KCGS 등급 KRX 포털 무료 접근 진짜 가능한가? (round-2 finding 검증 의무)

**Q15** — 거시 critical 4종 중 중국 credit impulse 무료 source (PBOC TSF / BIS quarterly) 가용 — 빈도·lag·신뢰도?

## §E 자문 라운드 진행 계획

| Round | 채널 | 목적 |
|---|---|---|
| R1 | /gemini-web (참신·다른 모델) | 산업 분할 · 분할 차원 · Layer 3 지표 후보 검증 (Q1-Q9) |
| R2 | /claude-web (fresh Opus 실무) | 최종 구현 · 통합 · 미국 비교 · Inv 인프라 (Q10-Q15) |
| R3 | 두 채널 응답 비교 + 수렴 또는 잔여 빈틈 메우기 | direction.md 작성 직전 |

자문 채널 경합 자제 — 1 자문씩, 응답 후 다음. WebSearch/WebFetch 폴백 가능 (round-2 사용 패턴).

## §F 자문 출력 의무 (자문 채널 응답에서 받을 것)

각 라운드 자문 답을 받으면:
1. 답을 그대로 yaml 박제 ★금지★
2. 본 분석가 (eq_kr supervisor) 비판·환각 검증·교차 cross-check
3. consult-round-{N}.md 에 (a) 자문 원문 quote (b) 본 분석가 비판 (c) 채택/기각 결정 (d) 다음 라운드 질문 명시
4. 수렴 후 direction.md 작성

⛔ 자문 그대로 받으면 evaluation-axes §L1.5 위반 (자문 그대로 코드화 = Layer 1 FAIL).
