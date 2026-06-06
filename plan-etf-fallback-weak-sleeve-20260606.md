# 약변별 sleeve → 테마 ETF fallback 코드화 plan (2026-06-06)

> **진입 포인터**: guide=핸드오프 `handoff-etf-fallback-weak-sleeve-20260606.md` / progress=`progress-etf-fallback-weak-sleeve-20260606.md`
> **사용자 의도(박제)**: "골고루 담는 수준으로 종목 selection 변별력이 없으면 → 운영규모(AUM) 큰 해당 테마 ETF를 사도록 코드화." **한국+미국 모두**.
> ⛔ production(core/stock) byte-identical 보존 · go-live·실주문 사람게이트 미접촉 · look-ahead PIT 엄수.

---

## ★자문 3R 수렴 결론 (gemini-web + claude-web, 2026-06-06 양쪽 "수렴 확정")

### 근본 재구성 (핵심 통찰)
위험 단어는 'ETF'가 아니라 **'과거 리턴 높은'**. selection 포기의 본질 = **의도한 테마 노출은 유지하되 변별력 없는 selection에 회전비용을 쓰지 않기**. 노출 그릇이 ETF일 필요는 없음 — **소N(과점)은 EW 직접보유가 dominant**, ETF는 대N sleeve의 운영 최적화 옵션. 리턴-랭크 선정만 **대표성-랭크 선정**으로 치환하면 사용자 ETF 의도 100% 보존하며 오염 회피.

### 설계 결정 확정표

| # | 결정 | 확정 (자문 수렴) |
|---|---|---|
| **D1** 약변별 판정 | raw ρ 컷 폐기 → within v2 계층베이즈 **posterior LS-spread cost-aware 손익분기**(P(비용차감 top-K−EW spread>0)>c) + breadth(Grinold IR≈IC·√N) + **PIT expanding-window 라벨**(weak↔strong 전이 허용, **dwell-time/debounce**로 thrash 방지) |
| **D2** ETF 선정 | **과거 리턴(모멘텀) 배제** — 동테마 ETF 리턴차 = 보수/집중도/레버리지(=거절정책 모순)·운빨. → **대표성(추종충실)+유동성(거래대금/AUM floor)+저비용(TER, realized-TE-history 공시TE 아님)+tax/FX(KR-listed vs US-listed: **원천징수·양도소득세·FX 드래그 3축**)**, 레버리지/인버스 제외 단일 선정 |
| **D3** 아키텍처 | z=+99.9 mock **기각(poison: dispersion/breadth 통계 오염)** → construction층 **Selector-dispatch**, ETF는 `score=None`/`pre_resolved` ranker **bypass**. `cross_sectional_selection.py`=CheapnessSelector 구현체로 강등 |
| **D4** 부재산업 | 정유(2)/통신(3) = **EW 직접보유**(소N에 TER 드래그 불필요, EW dominant). 인접테마/시장ETF 거부(basis risk·테마노출 소실) |
| **D5** AUM 소스 | 공시 절대값(KOFIA 전자공시/운용사 일별) **PIT 우선** > NAV×과거상장좌수 복원 > 현재스냅샷(백테스트 부적합). 상장좌수 PIT 위험, **trailing 1M + 1일 lag**, **ADV 별도 병행** |

### 라우팅 조건식 (정책)
```
RepresentativeETFSelector  ⟸  N ≥ 5 (비용 proxy: cost(EW)>cost(ETF) v1 stand-in, 추후 TE/비용 직접비교로 대체)
                              ∧ 적격 passive-ETF 존재
                              ∧ look-through 통과 (hard constraint = 진짜 대표성 시험)
                              ∧ holdings PIT max-lag 이내 (낡은 PDF → 실패)
EwBasketSelector           ⟸  그 외 (소N OR 적격ETF부재 OR look-through 실패 OR PIT-stale)
CheapnessSelector          ⟸  strong sleeve (기존 robust-z, 무변경)
```
> look-through = hard / N = 비용 proxy일 뿐. N을 축으로 취급하면 폐기한 "N이 축" 전제가 뒷문 재유입.

### 안전장치
- **risk_gate look-through**: 종목 10% cap=ETF 자체 / 섹터 30% cap=**look-through된 underlying** / **단일발행체 합산**(direct + ETF내부비중, 예 삼성 직접4%+ETF10%×내부20%=6% 숨은 노출)
- **ETF look-through 의무**: KR 2차전지/바이오 ETF는 active/momentum 내장 多 → 보유 전 passive basket vs active bet 분류
- **alpha→beta 4중 잠금** (selection alpha→sector beta 조용한 전환 방지):
  1. **선언**: WeightAssumptionCard에 "expected selection alpha=0, beta 표현" 명시 (이후 여기서 alpha 잡히면 버그/look-ahead)
  2. **측정**: shadow EW basket 수익 계속 계산 → e-CUSUM으로 `ETF_ret − EW_ret` 디커플링 감시 (factor 밀반입 falsification, baseline 품질 단서)
  3. **가역**: 대칭 promote/demote gate — IC 재검정, flat→ETF 강등 / 유의→selection 승격 (일방통행 금지)
  4. **반사실**: 리턴-랭크 선정 counterfactual 로깅 (gap 지속·유의 시 진짜 momentum 신호 → 명시 의사결정으로 표면화)
- **down-only 비용 허들**: ETF 표현은 EW shadow 대비 (TER+TE+spread) 허들 초과해야 정당. 못 넘으면 EW 회귀
- **인터페이스 계약**: `SelectionCandidate`가 ETF 메타(holdings source+asof) 운반 → risk_gate 분해 가능. weighter는 `score=None`을 0/worst 아니라 **sleeve-target weight 직접배정**으로 처리

---

## Phase 순서 (R3 재조정 — load-bearing 추상 우선)

### Phase A — Selector 프로토콜 골격 ★맨 먼저 (반나절, load-bearing)
- [ ] A-1 `Selector` ABC 정의: `(constituents, features, asof) → List[SelectionCandidate]`
- [ ] A-2 `SelectionCandidate` 스키마 확장: ETF 메타(`instrument_type` EQUITY/ETF, `holdings_source`, `holdings_asof`, `score: Optional` None=pre_resolved) + weighter 계약(`score=None`→sleeve-target 직접배정)
- [ ] A-3 `cross_sectional_selection.py`를 `CheapnessSelector` 구현체로 강등 (기존 로직 byte-identical, ABC만 implements)

### Phase 0 — 변별력 약 sleeve 식별
- [ ] 0-1 한국: `validation-within-residual-v2.json` 低9곳 회수
- [ ] 0-2 미국: `eq_us` selection within IC 등급 **산출** (한국 within v2 패턴 이식) · model: opus
- [ ] 0-3 D1 판정: posterior LS-spread cost-aware + breadth + PIT 라벨 (+ dwell debounce)

### Phase 1 — KR 9-sleeve N분류 + ETF 매핑/선정
- [ ] 1-1 9 sleeve를 N으로 분류 (정유2/통신3=소N → EW / 반도체54/2차18/바이오17=대N → ETF 후보)
- [ ] 1-2 산업↔테마 ETF 테이블 + 선정 (대표성+거래대금+TER+realized-TE+tax/FX[원천징수·양도세·FX드래그], 레버리지 제외, **리턴 배제**)
- [ ] 1-3 look-through 분류 (passive vs active) + holdings PIT max-lag 정책

### Phase 2 — ETF 데이터 (PIT)
- [ ] 2-1 FDR NAV/시세 + 미국 yfinance
- [ ] 2-2 AUM = 공시절대값 PIT 우선, trailing 1M + 1일 lag, ADV 병행

### Phase 3 — Selector 구현 + shadow dispatch 검증
- [ ] 3-1 `EwBasketSelector` + `RepresentativeETFSelector` 구현 (env flag default off)
- [ ] 3-2 **shadow/dry-run dispatch**: asof별 어느 selector fire 로깅 → 직관 검증(US strong→Cheapness, 과점→EW, broad→ETF) → 회귀 0(flag off byte-identity, golden/characterization 해시 assert)

### Phase 4 — 포트폴리오 편입 (risk_gate / weighter 통합)
- [ ] 4-1 dispatch table을 construction층 선언적 config에 (bitemporal versioned event)
- [ ] 4-2 risk_gate look-through (종목cap=ETF / 섹터cap=underlying / 단일발행체 합산)
- [ ] 4-3 admission ETF allowlist 경로 + valuation 우회(type==EQUITY 게이트)
- [ ] 4-4 alpha→beta 4중 잠금 (선언/shadow-EW e-CUSUM/대칭 gate/counterfactual)
- [ ] 4-5 통합 회귀 0 테스트 (flag off bit-equality)

### Phase 5 — 백테스트 (live cutover 전)
- [ ] 5-1 ETF 시세 PIT + 슬리피지 패리티
- [ ] 5-2 fallback on/off 성과 비교 + shadow-EW 디커플링 밴드 캘리브(2차전지/바이오 active tilt SNR 확인)

## Gate
- 각 Phase 회귀: flag off 시 production 종목 경로 **bit-equality**(golden 해시 assert)
- ⛔ live cutover 전 shadow dispatch 검증 필수
- ⛔ ETF 보유 전 look-through 통과 + PIT max-lag + 비용 허들 초과 3조건 AND
