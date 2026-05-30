---
tags: [type/work-queue, domain/crypto, purpose/collector-request]
date: 2026-05-31
purpose: candidate-ledger 의 "이연/후속/미채택일부" 전수 → merit 평가 → main 에 collector 구현 요청 (1순위 작업큐)
note: main 흐름 = collector 구현 → study(이론→실데이터→corr/Rank-IC) → 12축 audit subagent → yaml 반영. "collector 부재" = 탈락 사유 부적격 박제.
---

# crypto merit 후보 작업큐 (main 에 collector 요청)

> ★사용자 박제 (2026-05-31): "collector 없음·후순위·이연 = 탈락 사유 부적격". merit 있는 후보 전수 → main collector 구현 → 본 방 재study (이론→실데이터→corr/Rank-IC) → 12축 audit → yaml 반영.
>
> 본 큐는 candidate-ledger.md 의 ⏳이연(14) + 🔬후속재검증(5) + ❌미채택중 일부(Google Trends/활성주소/liquidation) 에서 merit 평가 후 추출.

---

## 🔥 P0 — 강한 merit, 무료 collector 즉시 가능 (main 에 1순위 요청)

### 1. CoinMetrics Community 확장 5종 (단일 API 키 불필요, page_size=1000 metric별 분리 호출)

| metric | merit 근거 | 본 가설 연결 |
|---|---|---|
| **MinerNetTransfers (BTC)** | claude r3 직접 권고: "halving N=4 standalone 검정 불가, but 연속 채굴자 매도 압력은 검증 가능. miner_outflow 가 daily 신호". theory-notes §1(ii) | H5 halving conditioning 보강. confound (macro epoch) 분리 |
| **HashRate (BTC)** | 동상. halving 후 marginal miner capitulation 직접 측정 가능 | H5 보조 지표 |
| **AdrActCnt (BTC 활성주소)** | Pagnotta&Buraschi 2018 Metcalfe-like 네트워크 가치 직접 proxy. theory-notes §1(ii)/(iv) | 신규 가설 H7: network value → fwd 60d (Pagnotta&Buraschi 균형해 검증) |
| **SOPR (가능여부 확인)** | Glassnode framework realized-value cycle indicator. MVRV 와 잠재인자 같으나 SOPR 는 *flow* (실현이익률), MVRV 는 *stock* (미실현). 정보량 독립 | H1 MVRV + SOPR 합성 cycle 신호. partial-corr 직교화 |
| **TxCnt / TxVolUSD** | on-chain 거래량 = 유틸리티 + speculative 합성. 후속 검증 필요 | 신규 가설 H8 후보 |

**Collector 요청**: `core/data/instrument_source.py` 의 `CoinMetricsMvrvProvider` 동일 패턴으로 5 metric 확장. 단일 keyless community endpoint, metric 분리 호출 (anonymous tier 묶음 403 우회 — 검증 완료 by 본 방 scripts/collect_coinmetrics.py).

### 2. FRED 무료 거시 3종 (이미 macro 방 일부 보유, crypto sleeve 와 wire 필요)

| series | merit 근거 | 본 가설 연결 |
|---|---|---|
| **DFII10 (10Y TIPS real rate)** | Howell 2020 Capital Wars + Liu&Tsyvinski 2021 macro null post-2020 fit start. theory-notes §1(iii) 거시 transmission 관계도 핵심 | post-2020 macro 채널 fit. real_rate ↑ → BTC 멀티 압박 검증 |
| **DTWEXBGS (Broad USD index)** | Howell framework 의 dollar funding cost. theory-notes §1(iii) | DXY ↑ → BTC funding 압박 채널 검증 |
| **M2SL (USD M2)** | 거시 유동성 lead. theory-notes §1(iii) → stablecoin transmission | M2 → stablecoin demand → BTC 매개 검증 |

**Collector 요청**: 우리 시스템 `fred_adapter.py` 에 DFII10 / DTWEXBGS / M2SL 추가 (이미 BAMLH0A0HYM2 등 17 series 등록 패턴 존재). macro 방 산출 wire 와 coordination 필요.

### 3. yfinance 무료 cross-asset 2종 (BTC 디커플 검증의 직접 입력)

| ticker | merit 근거 | 본 가설 연결 |
|---|---|---|
| **^IXIC (Nasdaq Composite) daily close** | Baur 2018 + post-2024 ETF 디커플. theory-notes §1(v): "BTC-Nasdaq 일별 상관 2024 0.4~0.6 → 2025 0.2~0.5 (하향)" | 신규 가설 H9: BTC-Nasdaq rolling 60d corr → digital-gold vs risk-asset regime 분류 |
| **^GSPC (S&P 500)** 또는 FRED **SP500** | risk-on/off macro regime 의 표준 베이스라인 | H9 보강 + macro regime 분류 입력 |

**Collector 요청**: yfinance 무료 라이브러리 사용 (이미 commodity sleeve 가 yfinance 사용 중 — `collect_macro` 함수 패턴 재사용 가능).

### 4. World Gold Council 또는 FRED 금 가격 1종

| series | merit 근거 | 본 가설 연결 |
|---|---|---|
| **GOLDAMGBD228NLBM (London Gold AM Fixing)** | Baur 2018 + theory-notes §1(v): "BTC-Gold 상관 2024 0.1~0.3 → 2025 0.3~0.5 (digital gold 서사 강화)" | 신규 가설 H10: BTC-Gold rolling 60d corr → digital-gold 채택 정도 정량 측정 |

**Collector 요청**: FRED `gold_pm_fixing` adapter. 무료 keyless.

### 5. Binance public 매일 archive 누적 pipeline (collector 자체 구축)

| 신호 | merit 근거 | 본 가설 연결 |
|---|---|---|
| **OI history daily archive** | Binance public 30d max only → daily 매일 snapshot ingest 누적 시 1년 후 ~365 records. funding/OI 조합 cascade 검증 필수 | H2 funding_trend_follow 재검증 보강 (daily aggregate 정보 손실 해소 일부) |
| **liquidation aggregated 24h** | Binance public force-order websocket stream → daily aggregate archive. funding 자문 cascade 가설의 직접 신호 | H2 자문 정정 재확인 (intra-day cascade 직접 측정) |

**Collector 요청**: `core/data/binance_archive_ingest.py` 신규 — 매일 cron 으로 OI + liquidation aggregate 적재. 1년 후 365 records 누적 시 의미 있는 검증 가능. *현재는 deferred build*, **archive 누적 즉시 시작 권고** (시간 지연 = 데이터 손실).

---

## 🟡 P1 — 중간 merit, 무료 가능 (collector 부담 작음, 후속 우선순위)

### 6. PyTrends (Google Trends) — Liu&Tsyvinski 2021 attention predictor

| 신호 | merit 근거 | 본 가설 연결 |
|---|---|---|
| **'bitcoin' 검색 트렌드 weekly** | LTW 2021 Review of Financial Studies main predictor (자체 momentum + investor attention 지배). MVRV·funding 외 독립 정보량 | 신규 가설 H11: attention z → fwd 30d (regime-dependent) |

**Collector 요청**: PyTrends 무료 라이브러리 (rate-limit 주의). weekly aggregate.

### 7. DefiLlama 확장 — bridge / DEX 무료

| 신호 | merit 근거 | 본 가설 연결 |
|---|---|---|
| **stablecoin bridge inflow (chain별)** | DefiLlama 무료 endpoint. 거래소向 stablecoin inflow proxy (CryptoQuant 유료 대체). 진짜 'dry powder' 보강 | H3 stablecoin reflexive guard 재검증 — bridge inflow 만 분리 추출 시 reflexive 제거 가능 |
| **TVL (Total Value Locked)** 또는 **DEX volume** | DeFi 활동도 = on-chain utility 보강 | 신규 가설 H12: DeFi utility → BTC (proxy via ETH 또는 sleeve) |

**Collector 요청**: 현재 `defillama-stablecoin-total.csv` collector 의 endpoint 확장. 추가 fetch 함수 5종 (bridges, TVL, DEX volume) 동일 패턴.

### 8. CoinGecko 또는 매일 archive — BTC dominance 일별 시계열

| 신호 | merit 근거 | 본 가설 연결 |
|---|---|---|
| **BTC dominance daily** | 현재 snapshot only (CoinGecko /global). 일별 시계열 = CoinMarketCap historical (유료) 또는 매일 snapshot archive (1년 후 365 obs) | yaml 블록2 btc_dominance 검증 정량화 (현재는 snapshot 1건만) |

**Collector 요청**: 매일 snapshot ingest (Binance archive 와 동일 패턴) 또는 CoinGecko Pro (유료 검토).

---

## 🟢 P2 — 약한 merit / 후속 검토 (지금 collector 요청 X, 본 방 재study 단계서 검토)

### 9. NUPL / MVRV-Z (MVRV 회계 동치 / σ 정규화)
- merit: MVRV 와 같은 잠재인자. 별도 정보량 입증 필요.
- 현재: 직접 계산 가능 (mvrv_z = (mvrv - rolling_mean) / rolling_std). collector 불필요, lib_common 함수 추가만.
- **후속 study 단계서 자체 산출 + partial-corr 직교화 검증**.

### 10. exchange_reserve_change 시계열
- merit: ETF 이후 의미 약화 (claude r3: custodian 이동). CryptoQuant 유료.
- **대안**: CoinMetrics community 가능 여부 확인 (P0 #1 SOPR 와 함께 점검). 가능 시 P0 승격.

### 11. ETH on-chain (MVRV / SOPR / TxCnt)
- merit: 멀티코인 확장 시점에. 현재 BTC 단일 sleeve focus.
- **deferred**: 본 cycle 미요청. 멀티코인 결정 후 P0 승격.

### 12. ECOS 한국 거시 (KOSPI / KRW / KR M2)
- merit: Upbit BTC 의 한국 프리미엄 / discount. BTC 전역 가격 영향 약 (Makarov&Schoar 2020).
- **deferred**: 한국 BTC 시장 specific 시. 본 cycle 미요청.

---

## 🔬 OOS / 모델 업그레이드 요청 (collector 외 시스템 구현)

main 에 collector 외 추가 시스템 구현 요청:

### A. VECM / 동시방정식 모델 (H3 stablecoin reflexive 분리)
- 현재 univariate Granger / CCF 만 사용. supply ↔ BTC bidirectional 인과 분리 불가.
- 요청: `core/structure/vecm_adapter.py` 신규 (statsmodels VECM). Johansen cointegration test + 충격반응함수 (IRF). reflexive regime 분류 자동화.

### B. walk-forward strict OOS 분리 (rolling Rank-IC PIT 강화)
- 현재 rolling window 가 forward fit + IC 산출 동시. OOS strict 1:1 매칭 미강제.
- 요청: `core/structure/walkforward_oos.py` 신규. CombinatorialPurgedKFoldSplit (skfolio) 또는 expanding-window OOS.

### C. CoinMetrics MVRV PIT provider 의 라이브 fetch 활성화
- 현재 `core/data/instrument_source.CoinMetricsMvrvProvider` 는 fixture 기본. live mode = "go-live PC 검증" stub.
- 요청: page_size=1000 anonymous tier + metric 분리 호출 패턴 (본 방 검증) 으로 실 라이브 활성화.

---

## 📋 main 요청 종합 (collector 11종 + 모델 3종)

| 우선순위 | 항목 | 무료 여부 | 추정 구현 | 본 방 후속 작업 |
|---|---|---|---|---|
| P0-1 | CoinMetrics 5종 (Miner / Hash / Adr / SOPR / TxVol) | ✓ 무료 | 1d (단일 API 확장) | H5 보강 + 신규 가설 H7 (network value), H8 (TxVol) |
| P0-2 | FRED 3종 (DFII10 / DTWEXBGS / M2SL) | ✓ 무료 | 0.5d (adapter 확장) | macro 채널 post-2020 fit + Howell framework 검증 |
| P0-3 | yfinance 2종 (^IXIC / ^GSPC) | ✓ 무료 | 0.5d | 신규 H9: BTC-Nasdaq rolling corr (Baur 2018 디커플) |
| P0-4 | FRED 금 (GOLDAMGBD) | ✓ 무료 | 0.3d | 신규 H10: BTC-Gold rolling corr (digital gold) |
| P0-5 | Binance archive (OI / liquidation) | ✓ 무료 | 1d (cron pipeline) | H2 재검증 (intra-day cascade), 1년 누적 후 시작 |
| P1-6 | PyTrends Google Trends | ✓ 무료 | 0.5d | 신규 H11: attention z (LTW 2021) |
| P1-7 | DefiLlama bridge/TVL/DEX | ✓ 무료 | 0.5d | H3 reflexive 분리 + H12 (DeFi utility) |
| P1-8 | BTC dominance daily archive | ✓ 무료 (archive 패턴) | 0.3d | 블록2 btc_dominance 정량화 |
| OOS-A | VECM 모델 | ✓ 무료 (statsmodels) | 1d | H3 reflexive 분리 정량 |
| OOS-B | walk-forward strict OOS | ✓ 무료 (skfolio) | 1d | 전 가설 OOS PIT 강화 |
| OOS-C | CoinMetrics live mode | ✓ 무료 | 0.5d | 본 시스템 PIT provider 라이브 활성화 |

**전체 추정**: 무료 collector 11종 + 모델 3종 = ~7~9일 main 구현. 본 방은 collector 도착 즉시 study 재진입 (이론 → 실데이터 → corr / Rank-IC → 12축 audit subagent → yaml 반영).

---

## 🔁 본 방 다음 cycle 작업 흐름

1. **main 의 collector 구현 응답 대기** — P0 11종 우선
2. **collector 도착 즉시 study 재진입**:
   - 이론 보강 (theory-notes 신규 가설 H7-H12 추가)
   - 실데이터 수집 (lib_common 확장)
   - 검증 (validation-h7~h12.md + h1/h2/h3 재검증)
   - 상관 / Rank-IC / partial-corr
3. **12축 audit subagent 호출** (별도 opus, AUDIT-GUIDE 12축 독립 감사)
4. **yaml v3 반영** (audit 통과분만)
5. **최종 잔여 = candidate-ledger 의 "❌탈락" 섹션 갱신** (merit 없음 or 실측 무상관)

---

## ⛔ 박제 사항 (다음 세션 재발 방지)

- ⛔ "collector 없음" / "이연" / "후순위" = ledger 탈락 사유 부적격
- ⛔ merit 후보를 ledger 에 먼저 적는 패턴 금지 → 작업큐 우선 (본 파일)
- ✓ collector 도착 → study → audit → yaml 반영 흐름 의무
- ✓ 최종 ledger 는 "merit 평가 후 실측 무상관 확인된 것" 만 기록
