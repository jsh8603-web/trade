# plan — 최종 테스트 진입 정리 + e2e/백테스트/라이브 + 자기진화 (2026-06-07)

> # ⚑ 작업 분류 원칙 (사용자 명시 2026-06-08 — 모든 worker·phase 최우선 공통)
> **문제(저조·손실) 발견 시, 코드 손대기 전 md/yaml(`README`·`CODEMAP`·`indicator-ledger`·`cross-regime-ledger`·`study_session`·`summary`) grep 우선 → 분류:**
> 1. **스터디 있음 + 배선 안 됨 → 잇는다**(런타임 배선, 18축 ⑱). ⛔ 스터디한 걸 시총비례/EW로 **덮지 말 것** = **스터디 내용 기준 구현**.
> 2. **데이터(수익률 등)가 문제 말함 + 스터디·코드·md 근거 없음 → 신규 연구**(데이터로 실측해 보완, ⛔'없다'고 넘어가기 금지, 설계 복잡하면 자문).
> 3. **스터디 있는데 데이터가 어긋남 → 재검토**(스터디 falsify).

> ⛔⛔ **[명시 금지 — 사용자 직접 지시 2026-06-08, 최우선 불변식]** 백테스트·테스트는 **프로덕션 파이프라인 진입점(`scripts/run_multiasset.py` 또는 `backtest/engine.py`)을 보수해서 그 경로로 돈다.** 별도 백테스트 드라이버에서 회계 NAV·사이징·게이트 자체 계산 금지. risk_gate·judge(down-only)·gross·GatedOrderRouter·회계(PortfolioState)는 프로덕션 코드 호출(우회 금지). orphan 0(전 모듈 경유) 검증 의무. `scripts/run_multiasset_backtest.py`=위반물(흡수/대체 대상). 상세=progress 상단. 위반=R5 drift 재발(promotion-log 2026-06-08 ERROR).
>
> 진입 근거: 구현·실거래 연결 외 테스트 완료 상태. 한투 **모의계좌**라 e2e 실매매 자유(=실거래 연결 사용자 승인). 최종 테스트 직전 **정리** 후 테스트 2종 일괄 진행, 자기진화는 테스트 경험 입력받아 맨 뒤 배치.
>
> 사용자 확정: **1-a**(README 사용자용 신규 + CODEMAP 코드색인) / **2-b**(정리+e2e+테스트1·2 일괄) / **3=테스트 뒤**(자기진화 P5).

## 0. 목표 (한 줄)

각 파이프라인이 제대로 도는지 e2e로 확인 → 10년 백테스트 + 모의계좌 라이브 → 문제는 **L0~L3 수준으로 귀속 분류해 모두 본 세션이 수정**(타 세션 작업분이라도 회피 금지) → 운영할수록 자기진화하는 토대 마련.

## 1. 문제 수정 수준 — 5+1단계 (사용자 3단계 세분화)

| 레벨 | 정의 | 검토처 | 판별 신호 |
|---|---|---|---|
| **L0 배선(wiring)** | 모듈이 호출/연결 안 됨 (e2e "미연결") | CODEMAP | 스모크에서 None/skip/import-only |
| **L1 이론·yaml 오류** | 가설·관계·방향이 틀림 | ledger | 신호품질(rank-IC) 부호 역전 |
| **L2a 코드 로직 버그** | 계산식 구현 오류 | CODEMAP | off 결정론 단계 불변식 위반 |
| **L2b 데이터·PIT 문제** | 결측·vintage·lookahead·빈도불일치 | CODEMAP + PIT 레이어 | as-of 위반·X 0행·coverage 갭 |
| **L2c 파라미터·상수 미스매치** | 로직·데이터 맞는데 상수 부적합 | CODEMAP | scale-invariant 정상인데 NAV만 비정상 |
| **L3a LLM 계약 위반** | 출력 스키마/형식 파싱 실패 | judge/llm_provider | on 경로 예외·schema reject |
| **L3b LLM 판단 품질** | 요약·카드가 의미적으로 틀림 | judge/active_loop | off vs on checksum divergence + 품질 평가 |

핵심: 사용자 3단계에 **L0(배선)·L2b(데이터)·L2c(상수)** 가 빠져 있었음. L2c는 메모리의 `MAX_WEIGHT_SINGLE=0.10` 단일자산 NAV 압살 케이스, L2b는 JM matrix 빈도불일치 케이스가 실제 anchor.

## 2. 판별 방법 (어떻게 알 것인가 = 로깅 설계)

기존 인프라 재사용이 핵심 (신규 최소):
- **off=byte-identical 불변식 + per-bar state-vector checksum(SHA256) + golden master** (이미 구현, 메모리 W4).
  - LLM **on vs off** 결정론 비교 → L3 격리(차이=LLM 탓).
  - 단계별 **checksum divergence pinpoint** → L1/L2 위치 특정(어느 bar/단계).
- 신규: **stage-by-stage attribution 로그(JSONL)** + **단계 불변식 체크**(weights합=1, gross∈[lo,hi], regime_id 유효, PIT as-of 위반 0, X 행수>0).

### 진단 로깅 = top-down drill-down (사용자 2026-06-07)
- **로깅은 최대 분해로 깔아둔다**: 모든 레코드에 `bar × asset × stage × layer` 태그. stage = 데이터수집→지표→regime→가정통계→사이징→risk_gate→judge→주문. raw는 JSONL(env opt-in, off=byte-identical), 평소엔 자산별 집계만 산출.
- **검토 흐름 = 자산별 먼저, 문제 시 dive deep**:
  1. **1차(가벼움)**: 자산별(섹터까지) excess·rank-IC 집계표만 본다 → 음수/이상 자산 식별.
  2. **2차(drill-down)**: 이상 자산만 골라 그 자산의 stage별 attribution + bar별 checksum raw 조회 → 어느 단계에서 값이 틀어졌나.
  3. **3차(귀속)**: 그 단계의 시그널을 L0~L3 귀속표(§3)에 대입 → 원인 레이어 확정.
- 즉 항상 full raw를 읽지 않고, **자산별 집계 → 문제 자산 → 단계 raw → 레이어** 순으로 좁혀간다(토큰·시간 절약 + 추적성 보존).

## 3. 문제 정의·벤치마크 (단일 수익률 금지 — 상수 오염 위험)

4층 지표:
- (a) **연결성**: 에러율·미연결 단계 수
- (b) **신호품질**: rank-IC·hit rate (scale-invariant, NAV 상수오염 면역 — 메모리 교훈)
- (c) **리스크조정**: Sharpe/Sortino/MDD
- (d) **초과수익**: 코인=BTC buy&hold / 주식=KOSPI·S&P500 / 멀티에셋=60/40·동일가중

### ★자산별(per-asset) attribution — 전체 평균에 묻히지 않게 (사용자 핵심 2026-06-07)
**원칙: 멀티에셋 전체가 벤치를 상회해도, 개별 자산이 장기적으로 수익이 안 나면 그 자산의 신호가 잘못된 것.** 전체 합산에 가려지면 안 됨 → 자산별로 분해 측정 의무.
- **측정 granularity**: 코인(BTC·ETH·주요 알트 각각) / **주식 섹터·sleeve별**(eq_us sleeve·eq_kr 7산업까지) / 자산군(코인·주식·원자재·금·채권).
- **per-asset 벤치 = 각 자산의 [전략 수익] vs [그 자산 passive buy&hold]**. 전략이 자기 자산 passive조차 장기 못 이기면 = 그 신호 무가치/해로움(거래비용만 까먹음) → **L1(이론) 의심 → 해당 sleeve ledger 재검토(보류/기각) 또는 base_weight 0**.
- ⛔ **self-referential base 금지**(empirical-claim §1.8): per-asset excess의 base는 **외부**(각 자산 buy&hold 또는 시장지수)여야 함. 측정대상들의 가중평균을 base로 쓰면 ∑wᵢ·excessᵢ≡0 거울(자유도 N−1, 독립 발견 아님).
- 산출: 자산별 [전략 누적수익 / passive 누적수익 / excess / rank-IC / hit] 표. **장기 음수 excess 자산 = 우선 L0~L3 귀속 조사 대상.**

### 문제 시그널 확정 — 3차 게이트 (단일 측정 단정 금지, small-n rigor)
1. **발견**: 4층 지표 중 벤치 미달 또는 음수(역방향) 1개 이상.
2. **확정(우연 배제)**: ① p-value + n 명기 ② Newey-West HAC(시계열 자기상관 보정) ③ block-bootstrap CI(IID 금지) ④ **walk-forward 부호 일관**(10년 in-sample ↔ 최근 2년 OOS 동일 방향). 4개 중 미충족이면 "문제 의심"(단정 X). *메모리 anchor: coin rank-IC −0.10도 overlapping 자기상관 미보정 caveat였음.*
3. **귀속**: 아래 레이어 시그널표로 원인 레이어 특정.

### 레이어별 문제 시그널·귀속표 (진단인프라 .p2b-survey §2 기반)
| 레이어 | 확정 시그널 | 판별 도구 |
|---|---|---|
| **L0 배선** | on/off golden hash **동일**(배선 무효과) / 단계 None·skip / `bypassed_attempts>0` | checksum diff, ev 로그 |
| **L1 이론·yaml** | 단계 불변식 0위반 + on/off checksum 동일 + **LLM off에서도** rank-IC 부호역전 | ledger 대조 |
| **L2a 코드로직** | per-bar checksum **특정 bar divergence** + `triggered_rules` 라벨 + mutation-kill 실패 | checksum, `_reject_reasons` |
| **L2b 데이터·PIT** | `resolve_as_of` ValueError / staleness 누적 / `data_empty` 라벨 / X 행수 0 | as_of, RuleObserver |
| **L2c 파라미터상수** | **scale-invariant(IC/Sharpe) 정상인데 NAV만 비정상** | env 상수 토글 격리(`RISK_MAX_WEIGHT_SINGLE` 등) |
| **L3a LLM계약** | on경로 except → `llm_contract_fail` 라벨 | 라벨 |
| **L3b LLM판단** | on/off golden hash **diff** + 판단 품질 평가 | A/B 비교 |

## 4. Phase 구조

### P0 — 현황 진단 (병렬 2 teammate)
- **P0-1** 파이프라인 e2e 연결성 맵: 진입점→단계→미연결(L0) 목록 + LLM 호출 지점 카탈로그 (opus)
- **P0-2** 루트 untracked 분류 판정표: 보존(폴더+포인터)/아카이브/삭제 (sonnet)

### P1 — 문서 체계 재편 (테스트 전제)
- **P1-1** 사용자용 `README.md` 신규(개요·아키텍처·의존성·실행법·안전장치) (opus)
- **P1-2** `CODEMAP.md` — 현 README 내용 이관 + **파이프라인 순서**로 재편(레이어→모듈→핵심기능+설계의도+파일경로). L0~L3 디버깅 진입점 역할 (opus)
- **P1-3** `CLAUDE.md` 재작성: 코인 레거시 → 포인터 1줄, 멀티에셋 **운영기준**(지표탐구=ledger / 파이프라인수정=CODEMAP + 수정후 동기화 의무) (opus, 프로젝트 로컬=동의 불요)
- **P1-4** 루트 정리 집행: `archive/` 이동·삭제·필요 코드 폴더화+CODEMAP 포인터 (sonnet)

### P2 — e2e 연결성 점검 + 진단 인프라
- **P2-1** 파이프라인별 e2e 스모크 → 미연결(L0) 식별 → 수정
- **P2-2** stage attribution 로깅 + 단계 불변식 체크 (off/on checksum 재사용)
- **P2-3** 문제정의·벤치마크 확정 + 측정 스크립트

### P3 — 테스트1: 백테스트 (10년 in-sample + 1~2년 OOS 이중구조)
- **P3-0 데이터 coverage 검증(진입 latch)**: 코인(BTC 2014~·ETH)·주식 ETF·FRED 거시·KIS 일봉 **실 가용범위 실측**(empirical-claim §1.1 — silent default·위조 금지, 일자+n 명기). 10년 미달 시리즈는 OutOfSample 라벨, 단일 n으로 join 길이 보고 금지.
- **P3-1 LLM 처리 = 3층 분리** (사용자 동의 2026-06-07):
  - **1층 10년 풀 = 전부 off 결정론** — `MACRO_ENRICH`·`ACTIVE_LOOP_SHADOW`·`MACRO_CONSENSUS` off + `judge_hook=None`(a=1.0). off=byte-identical + adversarial_replay(hash-pinned) 보존. ★전략 결정론 실체 측정.
  - **2층 LLM 기여분 격리 = 레짐 대표구간 on/off A/B** — golden hash diff(L3b). enrich·consensus 각각 격리. ★**비용 통제 2의무**(사용자 우려 2026-06-07, 호출빈도 실측): (1) **응답 hash 재사용 필수** — 백테스트 입력=PIT 결정론이라 `(regime, macro_view)` 해시 동일 구간은 1회 호출 후 재사용(regime 불변 구간 실호출 ~90%↓). on/off golden hash diff 판별과 양립(재사용분도 동일 결과). (2) **전체 1~2년 매 bar 금지 — 강세/약세/횡보 각 1~2개월 대표구간만** A/B. 근거: `MACRO_ENRICH` on 시 매 collect 사이클(=매 bar) LLM 호출 → 일봉 1~2년 365~730회+주식 거래일 = 폭주. consensus(`is_high_stakes`=regime전환·배분>10%·누적>25%)·카드(주기성)는 본래 저빈도라 무관. 추산: 재사용+샘플 수십~수백회(≈$1~3) vs 무통제 매 bar 수천회(≈$15~30+).
  - **3층 카드생성·하이쿠 요약 동작검증 = 샘플 구간 실호출 or record-replay** — L0(배선) 확인. 거시 RAG 소스 미구축(L0-8)이라 종목뉴스 위주.
- **P3-2 10년 in-sample**: 결정론(1층) 멀티에셋 풀가동 → 4층 지표 vs 벤치 → **전략 생존성**(거시 추세 통과). per-bar checksum 생성.
- **P3-3 1~2년 OOS + 정밀**: (a) **최근 2년 walk-forward OOS** = 10년 in-sample과 **부호 일관** 확인(과적합 배제, 시그널 확정 게이트 2-④) (b) LLM **on/off A/B**(2층 — ★레짐 대표구간 한정 + 응답 hash 재사용, P3-1 비용 2의무) (c) 카드·하이쿠 **동작검증**(3층) (d) 현 레짐 적합성.
- **P3-4 문제 발생 시 3차 게이트**: 발견(4층 미달) → 확정(p·NW·bootstrap·walk-forward) → 귀속(레이어 시그널표) → L0~L3 수정 루프(L0/L2=메인 또는 harness2, L1=ledger 재검토, L3=LLM 경로).

### P4 — 테스트2: 모의계좌 라이브 매매
- **P4-1** 파이프라인 라이브 가동 + 실주문(모의) → 관측·로그
- **P4-2** 라이브 이슈 L0~L3 귀속 → 수정

### P5a — 자기진화 인제스트·관측 (shadow, P3 앞 배치)
> 근거: "도는가(A) vs 옳은가(B)" 분리. (A)는 당기면 이득, (B)는 테스트 경험 선행 필요. shadow 패턴(coin_shadow·promotion_gate_live)으로 측정오염·lookahead 차단.
- **P5a-1** 거래기록 인제스트 + 귀속·drift 계산 + **제안 출력 shadow-only**(자동 개입 X, 제안만 기록). attribution 로그(P2-2) 스키마 공유.
- **P5a-2** 진화 e2e 스모크(에러 없이 도는가 = L0). 10년 백테스트선 입력 as-of 강제 또는 라이브(P4)에서만 활성 → lookahead 원천 차단.

### P5b — 자기진화 판단 캘리브 + live 승격 (P4 뒤 배치)
> 테스트 중 사람이 매긴 수동 L0~L3 라벨 = 정답셋.
- **P5b-1** 거래별 L0~L3 자동 귀속 휴리스틱 캘리브레이션(정답셋 대조) + drift/복귀 트리거 검증
- **P5b-2** shadow 검증 통과 시 live 개입 승격(IC9 복귀/babyplace 발굴/코드수정 제안 → 기존 promotion_gate 패턴). CODEMAP·CLAUDE.md 운영기준에 프로세스 박제(코드수정=CODEMAP 의도참조+수정후 동기화)

### P6 — 멀티에셋 17축 attribution 개선 (6 worker, harness2 메커니즘만)
> 근거: P4 프로덕션 백테스트(`run_multiasset.py --backtest`) 17축 측정으로 자산·산업·층위별 저조 식별. **SSOT=[handoff-multiaxis-roadmap-20260608.md](./handoff-multiaxis-roadmap-20260608.md)**. 6 worker(opus 1m teammate, **Agent tool** + `run_in_background` + `SendMessage` 조종, harness2 프로토콜[상태머신·execution-log·SR debate] **미사용**) 각자 한 파일경계 전담, **healer=메인**, 검증=별도 teammate 1기(병목 2~3).
> ★**MANDATE 4** (모든 worker/검증 프롬프트 박제, 사용자 명시 2026-06-08): ①**의도 우선 읽기**(README/CODEMAP/해당 ledger에서 설계의도 먼저 → 코드부터 고치지 말 것) ②**검증도 의도정합 판정**(회귀+raw재현뿐 아니라 README/CODEMAP 의도 정합) ③**복잡설계는 메인 3R 자문**(계약변경·신규모듈/국면·A/B trade-off·임계추정 = worker 단독 확정 금지) ④**확정 스펙 worker 전달**(자문/설계 확정분을 명시 박제, worker 재구현 방지).
> ★★**작업 분류 원칙(사용자 명시 2026-06-08, P6·P7 공통)**: 문제(저조·손실) 발견 시 — ① **스터디 있음 + 배선 안 됨** → **잇는다**(런타임 배선, ⑱) / ② **데이터(수익률 등)가 문제 말함 + 스터디·코드·md 근거 없음** → **신규 연구**(데이터로 실측, ⛔'없다'고 넘어가기 금지, 설계 복잡하면 자문) / ③ **스터디 있는데 데이터가 어긋남** → 재검토(스터디 falsify). ⛔ **스터디 있는 걸 시총비례/EW로 덮지 말 것 — 스터디한 내용 기준 구현**(W3 ⑱ 누락 교훈).
- [x] **W2 regime** ✅DONE(2026-06-08): 절대 CPI 게이트(STAGFLATION_ABS_CPI_GATE=3.0)+SLOWDOWN 국면 신설 → 정렬 -0.91→Slowdown-0.19/Stagflation+0.10, NAV4.395/OOS↑, ⑯conf 추출(confidence_now) fix. coin throttle은 R1 분리로 해소. 상세=cross-regime-ledger §2.
- [ ] **W3 섹터 regime틸트** (P1, 진행중 spawn 2026-06-08): `decompose_weight`에 `regime=None` 인자(=regime 미주입 시 byte-identical)+anchor 시총비례 유지 regime-conditional 틸트, ⛔**EW 갈아엎기 금지**(소형주몰빵·과적합). `_bt_us_picks`/`_bt_kr_picks` 배선(호출처 regime_lbl 전달). 자문 Q3=regime뷰 섹터미도달 **배선갭(코드입증)**.
- [ ] **W6 측정정정** (P1): C1 선택alpha tautology 정정(선택종목 vs **업종 전체 universe EW**), ⑭survivorship haircut, 거래비용.
- [ ] **W4 한국선택** (P2): ρ 살아있는 ~3 sleeve만 개별선택 + **cheapness×quality/payout** 게이트(거버넌스 영구디스카운트 트랩 거름), 나머지 ETF/EW.
- [ ] **W1 종목비중** (최하): inverse-vol 근거 yaml 부재 → ⛔'없다'고 넘기지 말고 **데이터 실측**(inverse-vol이 우리 종목 데이터서 capped-EW 대비 Sharpe 개선하나, walk-forward) → 효과 있으면 신규 채택/없으면 현행 유지. 강도틸트는 ★반대(밸류트랩+과적합, 자문 Q4).
- [x] **W5 팩터데이터** ✅DONE(2026-06-09 검증): ⑬VIXCLS vintage 결측 해소 확인. VIXCLS ∈ `_MARKET_PRICED_DAILY` ⊂ `_LATEST_FALLBACK`(fred_adapter:76,85, W5 2026-06-08 추가) → pit_mode=first_release여도 `series_id in _LATEST_FALLBACK` → `get_series_first_release`(vintage 3864>2000 ValueError) 회피하고 **latest 직행**(market-priced 일별=revision≈0, DFII10 동성격 입증). as_of causal mask=observation-date 기준이라 PIT lookahead 없음. 코드경로 검증 PASS(VIXCLS in _LATEST_FALLBACK=True, first_release 분기 미진입). ⚠️실 FRED 라이브 왕복=FRED_API_KEY 부재(go-live N-P4-FRED 게이트)로 defer, 키 주입 시 ⑬ vol 차원 자동 충전.

### P7 — 분기별 손실 attribution 진단 (P6 완료 후, 사용자 지시 2026-06-08)
> 6 worker 수정 완료 후 진행. **분기별로 손실 제일 큰 분기**를 골라 원인을 찾는 phase. 추정 금지, `run_multiasset.py --backtest` 실측 로그(port_seq 등)로만 판정. ★처리 규칙(사용자 명시): 손실 분기에서 **수정/검토 필요사항 발생 시 즉시 plan/progress에 추가 반영** + 설계 복잡=**자문 3R(gemini+claude)** / 단순 버그=**즉시 수정** + README/CODEMAP 읽고 구현 후 **동기화**(P6 MANDATE 동일 적용). ★★**문제 발견 즉시 — 스터디 우선 검토(사용자 명시 2026-06-08)**: 코드 손대기 전 **yaml/md(`_wire/indicator-ledger.md`·`cross-regime-ledger.md`·각 `study_session.yaml`·`industries/*/summary.yaml`)에 관련 스터디 있나 grep 먼저** → ⓐ 있으면 "연구됨 = 런타임 배선 누락(⑱)" 판정(배선 작업) / ⓑ 없으면 "신규 연구 필요" 판정. ⛔ 스터디 확인 없이 일반론으로 코드화 금지(W3 1차 실패 교훈). 18축 ⑱가 이 검토를 강제하는 축.
- [x] **P7-1** ✅DONE(2026-06-09, `.p7-backtest-current.log` 현행 파이프라인 fresh run): NAV **4.647**(CAGR+18.6%) Sharpe 1.15 MDD−16.4% n=36분기. **worst 3분기**(실측 port): ①2022Q2 Overheat **−12.3%** ②2018Q4 Overheat **−12.0%** ③2020Q1 Slowdown **−10.7%**(코로나). 차순=2018Q1 Recovery −4.8%·2022Q3 Overheat −4.7%. 나머지 분기 전부 ≥−1.1%.
- [x] **P7-2** ✅DONE: 성분분해. ▸**regime별 손익=전부 양수**(Overheat Σ+0.423 평균+0.028/n15·Slowdown +0.058/n7·Stagflation +0.027/n5) → 순손실 regime 0. ▸worst 3분기 공통=**광범위 위험자산 동반하락**. 두 Overheat 손실(2018Q4·2022Q2)=**동일 정적 Overheat 비중 템플릿**(us0.26/kr0.16/bond0.16/commodity0.15/gold0.11/coin0.10/cash0.06, 위험자산~62%). 2022Q2=iz+1.06 인플레쇼크+코인붕괴+채권/주식 동반↓, 2020Q1=bond0.31 방어에도 위험자산~46% 코로나크래시. ▸②regime비중-수익 corr: Overheat −0.06/Slowdown −0.30/Stagflation −0.43(coin이 4/5 regime 최고수익이나 MAX_WEIGHT_SINGLE cap으로 w~0.06-0.10=cap이 winner 적재 차단, 단 의도적 분산). ▸⑱배선정합: eq_kr 12산업 ④축 출력(refining/telecom 포함 전산업 비중-수익), us알파 t2.65 유의=⑱ 누락 0. ⛔'스터디됐는데 런타임 미배선' 손실 검출 0.
- [x] **P7-3** ✅DONE: **L1(국면배분) 귀속, 코드버그 아님**(★E94 대안가설 전수 기각): 종목선택축 정상(orphan 0·judge a=1.0 무발동·gate REJECT 1회 max_weight_single·router.bypassed 0·us알파 t2.65 유의)+regime손익 전부 양수+IS Σ1.069/OOS Σ0.615 둘 다 양수(과적합 붕괴 없음). worst 분기=분산 위험자산 배분의 **내재 베타 드로다운**(순보상 +, NAV 4.647 회복). ★처리=**즉시수정 없음**(코드 결함 부재). 유일 후보 정제=Overheat를 인플레쇼크(iz↑)로 세분(2022Q2 growth-z+0.14로 Overheat 라벨 유지=coincident, 시장은 leading)이나 **2에피소드(2018Q4·2022Q2) 과적합 위험** → 자문3R/즉시수정 아닌 **관찰 등록**(향후 인플레쇼크 분기 누적 시 재평가). survivorship phantom haircut ~1.2%p/yr 동반 해석(⑭).

## 5. teammate 운용 규칙
- **동시 최대 5기** (2026-06-07 사용자 상향, 기존 2기→5기). sonnet=수집·분류·정리집행 / opus(1m)=배선진단·문서설계·진단인프라.
- 독립 작업만 병렬. 의존성 깨진 추측 작업 금지(의존 작업은 선행 결과 수령 후 투입).
- 설계 판단(entry 작성·judge)은 메인 owner, teammate 위임 부적합.

## 6. 불변식 / 금지
- 타 세션 작업분도 본 세션이 수정 (회피 금지).
- 코드 수정 시 CODEMAP 의도 참조 → 수정 후 CODEMAP 동기화 의무.
- go-live(실거래 환경)는 모의계좌 한정. 실서버 전환은 사용자 게이트.
- off=byte-identical 불변식 보존. 부품/엔진 무단변경 금지.
