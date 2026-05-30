---
tags: [type/handoff, study/crypto, session/btn-profile, date/20260531]
date: 2026-05-31
session: btn-profile (crypto 작업방)
study_id: crypto
last_phase: 2-3 완료 + merit-queue 송신 / main collector 구현 대기
---

# crypto 작업방 핸드오프 — 2026-05-31

> 본 세션 (btn-profile) 의 crypto study 잔업 + 다음 cycle 재개포인터 + 미해결 의문 + 기 수집 모든 산출 inventory. 다음 세션이 본 파일만 읽고 그대로 재개 가능.

---

## 0. 한 줄 현재 상태

★main 에 collector 11종 + 모델 3종 (전부 무료) 구현 요청 송신 완료 (2026-05-31). main collector 구현 응답 대기 중. 응답 도착 즉시 본 방 재study (이론 → 실데이터 → corr/Rank-IC → 12축 audit subagent → yaml v3 반영).

---

## 1. Phase 완료 상태

| Phase | 상태 | 산출 파일 | 비고 |
|-------|------|-----------|------|
| 2-1 자문 다회 | ✅ 완료 | `direction.md` (20KB) + `raw/round-{1,2,3}-{gemini,claude}.md` (~56KB) | gemini+claude 3R 수렴, "추가 round 불필요" 명시 |
| 2-2 이론학습 | ✅ 완료 | `raw/theory-notes.md` (28KB) | 5채널 11문헌 학술 압축 + 거시 transmission + 5도구 |
| 2-3 실데이터 검증 | ✅ 완료 | `raw/validation-*.md` (7건 ~20KB) + `scripts/*.py` (8건 ~50KB) + `raw/data/*` (6 sources ~2.5MB) | ⛔합성 0건. 실측: CoinMetrics 5795 / funding 7363 / FGI 3037 / DefiLlama 3105 / Farside 613 / klines 3209 |
| yaml v2 + 8축 self-audit | ✅ 완료 | `study_session.yaml` (302줄) + `summary.md` (166줄) | v1 폐기 → `raw/*.deprecated` |
| candidate-ledger (잘못된 순서) | 🟡 보존 | `candidate-ledger.md` | 사용자 정정: "먼저 쓰지 마라". 보존 + merit-queue 로 전환 |
| merit-queue (정정) | ✅ 완료 + 송신 | `merit-queue.md` | main 에 collector 11종 + 모델 3종 요청 (2026-05-31 송신) |

---

## 2. 다음 작업 (재개 포인터) — 우선순위 순

### 🔥 P0 — main collector 구현 응답 대기

본 방은 **collector 도착 즉시 study 재진입** 의무 (idle 금지). 응답 형태별 작업:

**Case A — collector 일부/전부 구현 완료 통지**:
1. 도착 collector 별로 study 재진입:
   - CoinMetrics 5 metric (MinerNetTransfers / HashRate / AdrActCnt / SOPR / TxVolUSD) → `scripts/collect_coinmetrics.py` 패턴으로 metric 분리 확장 → 신규 가설 H7 (network value, Pagnotta&Buraschi 균형해) + H8 (TxVol)
   - FRED 3 (DFII10 / DTWEXBGS / M2SL) → `scripts/collect_fred_macro.py` 신규 → macro 채널 post-2020 fit, Howell framework 검증
   - yfinance (^IXIC / ^GSPC) + FRED Gold → `scripts/collect_cross_asset.py` 신규 → 신규 H9 (BTC-Nasdaq corr) + H10 (BTC-Gold corr) 디커플 검증
   - PyTrends → 신규 H11 (attention z, LTW 2021)
   - DefiLlama bridge/TVL/DEX → H3 reflexive 분리 + H12 (DeFi utility)
   - VECM 모델 → H3 stablecoin reflexive 정량 분리
   - walk-forward OOS → 전 가설 OOS PIT 강화
   - CoinMetrics live mode → 본 시스템 PIT provider 활성화
2. 신규 가설별 `scripts/h7_*.py ~ h12_*.py` 작성 → 실행 → `raw/validation-h7~h12.md` 산출
3. 기존 H1/H2/H3 재검증 (OOS strict 분리 + VECM 적용)
4. 12축 audit subagent 호출 (opus, AUDIT-GUIDE 12축 독립 감사)
5. yaml v3 반영 (audit 통과분만)
6. summary v3 + 8축 self-audit 갱신

**Case B — main 이 collector 미구현 + 대신 우선순위 변경 지시**:
- 새 지시 그대로 진행
- 본 핸드오프 + merit-queue.md 가 이전 cycle 컨텍스트 보존

### 🟡 P1 — collector 도착 전 가능한 사전 작업 (idle 회피)

본 방 자체적으로 추가 가능한 사전 작업 (collector 불필요):

1. **theory-notes 신규 가설 6건 (H7-H12) 사전 작성** — Pagnotta&Buraschi 균형해 / 활성주소 Metcalfe / BTC-Nasdaq 디커플 / BTC-Gold 디지털골드 / Google Trends attention / DeFi utility 의 학술 근거 정리. theory-notes.md §1 후속 가설 섹션 추가.
2. **lib_common 확장 — NUPL/MVRV-Z 직접 계산** — CoinMetrics MVRV 만으로 산출 가능 (collector 불필요). H1 partial-corr conditioning_set 확장 후보.
3. **rolling window 길이·step 민감도 분석** — 우선 1 prior_ladder 의 미해결 의문 #6. backtest 누적 후 정확한 비율 결정.
4. **OOS strict walk-forward 1차 시뮬** — collector 부재 시 기존 데이터로 in-sample/OOS 2017-2021/2022-2025 분리 재검증.

### 🟢 P2 — 최종 잔여 (P0-P1 후)

- **candidate-ledger.md ❌탈락 섹션 갱신** — merit 평가 + 실측 검증 후 "merit 없음" 또는 "실측 무상관" 확인된 것만 기록. 박제 사항: "collector 없음/이연/후순위" = 탈락 사유 부적격.

---

## 3. 미해결 의문 (재개 시 우선 검증)

direction.md §5 + validation-*.md §미해결의문 + summary.md §3 종합:

1. **MVRV partial-corr CI 0 포함** (-0.085 BB95%CI=(-0.235,+0.073)) → conditioning_set 확장 (BTC dominance·real_rate·stablecoin 추가) 필요
2. **funding cascade 자문 정정 → 8h or 분단위 재검증** — daily aggregate 정보 손실 가능
3. **stablecoin reflexive 분리** — BTC→supply Granger lag 7d p=0.014 / lag 14d p=0.0000 = bidirectional. VECM 적용 필요 (main OOS-A 요청)
4. **ETF flow 1.5yr 짧음** — 1.5yr 추가 누적 후 promotion 결정 (prior 0.05 → 0.15)
5. **halving N=4 + macro epoch confound** — 채굴자 압력 (hashrate / miner outflow) 보조 지표 필수 (main P0-1 요청)
6. **prior ladder 정확 비율 재캘리브** — 실측 on-chain sharpe 1.27 > micro 0.97 > stablecoin -0.43 발견. backtest 누적 후 비율 결정
7. **internal glasso effective N>=200 = 33% admit (WARN)** — threshold 100 사용 권고, FGI 5→3 단계 통합 옵션 검토
8. **rolling Rank-IC walk-forward strict 분리** — 현재 forward fit + IC 산출 동시. OOS 1:1 매칭 강제 필요 (main OOS-B 요청)
9. **post-2024 ETF 시대 realized cap 의미 변화** — custodian 이동 → realized cap 의 "최종 보유자 취득" 의미 약화 정량 측정
10. **macro_abstain 가설은 우리 시스템 emit log 부재** — 외부 macro proxy (VIX>30 + DXY z>1) 시뮬 검증 권고 (DXY=FRED DTWEXBGS, main P0-2)

---

## 4. 산출 파일 inventory (re-discover 용)

### 메인 산출
- `D:/projects/Inv/study-research/crypto/direction.md` (20KB, Phase 2-1 v2 7-Phase 미러링)
- `D:/projects/Inv/study-research/crypto/study_session.yaml` (302줄, v2 ★실측 prior 재캘리브)
- `D:/projects/Inv/study-research/crypto/summary.md` (166줄, 8축 self-audit)
- `D:/projects/Inv/study-research/crypto/candidate-ledger.md` (잘못된 순서, 보존, 7 섹션)
- `D:/projects/Inv/study-research/crypto/merit-queue.md` ★최신 (collector 작업큐 + main 요청 11+3)
- `D:/projects/Inv/study-research/crypto/progress.md` (ckpt + Phase 체크)

### raw 분석
- `D:/projects/Inv/study-research/crypto/raw/theory-notes.md` (28KB, Phase 2-2 학술 압축)
- `D:/projects/Inv/study-research/crypto/raw/round-{1,2,3}-{gemini,claude}.md` (자문 6회 ~56KB)
- `D:/projects/Inv/study-research/crypto/raw/validation-{h1,h2,h3,h4,h5,prior-ladder,eff-n-gate}.md` (7건 ~20KB, 실측)
- `D:/projects/Inv/study-research/crypto/raw/code-evidence-notes.md` (v1 시절, 보존)
- `D:/projects/Inv/study-research/crypto/raw/study_session.v1.yaml.deprecated` (v1 폐기 보존)
- `D:/projects/Inv/study-research/crypto/raw/summary.v1.md.deprecated` (v1 폐기 보존)

### raw 실측 데이터 (⛔합성 0건)
- `raw/data/coinmetrics-btc-daily.csv` (5796 rows, 2010-07-18 ~ 2026-05-30, BTC MVRV/realized/market cap/price)
- `raw/data/binance-klines-btcusdt-1d.csv` (3209 rows, 2017-08-17 ~ 2026-05-30) ★column shift 버그 fix 완료
- `raw/data/binance-funding-btcusdt.csv` (7363 rows, 2019-09 ~ 2026-05, 8h funding)
- `raw/data/binance-oi-btcusdt.csv` (30 rows, 30d max public)
- `raw/data/fgi-daily.csv` (3037 rows, 2018-02 ~ 2026-05)
- `raw/data/defillama-stablecoin-total.csv` (3105 rows, 2017-11 ~ 2026-05)
- `raw/data/farside-etf-raw.html` (726KB raw HTML, parse 완료 by h4_etf.py)
- `raw/data/coingecko-global-snapshot.json` (BTC dominance 57.5%)
- `raw/data/collect_log.txt` + `collect_run.log` (수집 로그)

### scripts (수집기 + 분석)
- `scripts/collect_data.py` (6 API 수집기, ★UTF-8 강제 + Unicode → ASCII 치환, page_size=1000 + funding startTime walk-forward)
- `scripts/collect_coinmetrics.py` (metric 분리 fetch, anonymous tier 우회 패턴)
- `scripts/lib_common.py` (load_{coinmetrics, klines, fgi, funding, funding_daily, stablecoin} + rank_ic + newey_west_se + effective_n + e_cusum_one_sided + block_bootstrap_ci + fgi_regime + halving_phase + forward_return)
- `scripts/h1_mvrv.py` (MVRV mean-revert 검증)
- `scripts/h2_funding.py` (funding cascade — REJECT 발견)
- `scripts/h3_stablecoin.py` (stablecoin lead-lag — reflexive 발견)
- `scripts/h4_etf.py` (Farside HTML parse + post-2024 검증)
- `scripts/h5_halving.py` (halving phase conditioning only)
- `scripts/prior_ladder.py` (우선 1 ladder backtest — 역방향 발견)
- `scripts/eff_n_gate.py` (우선 2 effective N gate — hybrid 유지)

---

## 5. ★실측 핵심 발견 (재개 시 참고)

| 가설 | 자문 prior | 실측 결과 | 정정 prior | 카드명 |
|------|-----------|----------|-----------|--------|
| H1 MVRV | 0.4 mean-revert | marginal +22.9% (trend) / partial -0.085 CI 포함 | 0.55 conditional only | `crypto.mvrv_conditional_mean_revert` |
| H2 funding | 0.6 cascade | extreme long → fwd_3d +1.9% (★REJECT) | 0.15 trend follow (부호 반전) | `crypto.funding_trend_follow` |
| H3 stablecoin | 0.3 dry powder | Granger lead OK but bidirectional reflexive + rolling -0.43 | 0.20 + reflexive guard | `crypto.stablecoin_lead_with_reflexive_guard` |
| H4 ETF | 0.05 probation | hit rate 56.7% p=0.006 + CI 포함 | 0.05 유지 | `crypto.etf_flow_probation` |
| H5 halving | 0.1 label only | standalone X, conditioning IC 일관성 (-0.03~-0.61) | 0.10 유지 | `crypto.halving_phase_conditional` |

★Prior ladder 역방향: on-chain sharpe **1.27** > micro **0.97** > stablecoin **-0.43**. 자문 (micro 0.6 > on-chain 0.4) 과 정반대.

★eff_n gate: 15/15 cell N≥24 (100%) / 11/15 N≥100 (73%, gate 권고) / 5/15 N≥200 (33% WARN). Hybrid 유지 가능, 영구폐쇄 위험 LOW.

---

## 6. 환경 / 도구 메모 (재개 시 즉시 사용 가능)

### Python
```bash
PY="/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe"
# 라이브러리: pandas 2.2.3, numpy 2.4.2, statsmodels 0.14.6, scipy 1.17.1, requests
# 호출 시 cp949 console 회피 의무:
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "$PY" scripts/h1_mvrv.py 2>&1 | tail -5
```

### 데이터 fetch 패턴 (anonymous tier 우회 확인)
- **CoinMetrics community v4**: page_size=1000 OK, page_size=10000 = 403 / 5 metric 묶음 호출 = 403 / metric 분리 호출 OK
- **Binance funding**: endTime=None → 최근 200 record cap. startTime 명시 walk-forward 필수
- **Binance klines write 시 column 수 13개** (Binance API ignore field 포함) — header 12개와 mismatch 주의

### Farside HTML parse
- `h4_etf.py` 안에 `parse_farside_html()` 정규식 기반 (BeautifulSoup 없이). 일자별 Total 칼럼 추출.

### git 상태 (handoff 시점)
- 추적 안 됨 (Untracked): `study-research/crypto/` 전체 (모든 산출 신규)
- 본 핸드오프 작성 후 commit 예정

---

## 7. main 보고 메시지 패턴 (재개 시)

```bash
bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[crypto->main] {내용}"
```

지난 메시지 인덱스:
- 2-1 자문 완료 보고
- 2-2 이론 완료 보고
- 2-3 + yaml v2 + 8축 audit 완료 보고
- candidate-ledger 작성 보고 (잘못된 순서)
- merit-queue + main 에 collector 11+3 요청 송신 (2026-05-31 최신)

---

## 8. 박제 / 사용자 명시 (재발 방지)

- ⛔ "자문 그대로 코드화 금지" — 자문 R1-R3 가설 vs 실측 정정 의무
- ⛔ "합성·시뮬 데이터 금지" — 실제 수집기 PIT 만
- ⛔ "single-source 단정 금지" — 학술 + 실무 + 1차 데이터 3중
- ⛔ "small-N 단정 금지" — cell N<24 5게이트, halving N=4 standalone IC 금지
- ⛔ "점추정 prior 박제 금지" — 분포 + CI + 게이트
- ⛔ "supervisor (본 방) 직접 평가 금지" — Phase 6 별 평가 subagent 의무 (next cycle main pass-bias 회피)
- ⛔ "analyst-level lens 다운그레이드 금지" — 시스템 못 받으면 파이프라인 업그레이드
- ⛔ "opt-in off = byte-identical 무회귀" — INV_R15_WEIGHTS default-off
- ⛔ "reflexive loop 차단" — belief→_macro 차단, L축 공통인자 1회 계상 + PSD
- ⛔ "tier 정직성" — REJECT/contemporaneous = structural prior 라벨
- ⛔ "coin §4③ coin_consensus_lens SACRED 불침범"
- ⛔ "collector 없음 / 이연 / 후순위" = ledger 탈락 사유 부적격 (2026-05-31 사용자 정정)
- ⛔ "merit 후보를 ledger 에 먼저 적는 패턴 금지" → 작업큐 우선 (merit-queue.md)
- ✓ "collector 도착 → study → audit → yaml 반영 흐름 의무"
- ✓ "최종 ledger 는 merit 평가 + 실측 검증 후 무상관 확인된 것만 기록"

---

## 9. 보고 메시지 송신 시 주의

⚠️ DA-20260422-psmux-send-ssot-helper 위반 금지 — 반드시 `~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "..."` 헬퍼 경유 (raw `psmux send-keys` 금지)

---

> **STATUS**: 작업 자체는 cycle 1 종료 시점. main collector 응답 도착 = cycle 2 진입 신호.
