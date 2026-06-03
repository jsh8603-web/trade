---
tags: [type/handoff, domain/inv, program/collector-build, status/autonomous-active]
date: 2026-05-31
session: btn-Codlearn (main)
trigger_to_resume: "본 파일 Read → §3 다음 작업부터 자율 진행 (자율주행 ON, 전 누락지표 audit+반영까지)"
ckpt: progress-study-system.md ckpt-202605310200
---

# handoff — collector-build program (누락지표 merit 실증)

## §1. 프로그램 정의 (사용자 확정 2026-05-31)

> **merit 있는 지표는 collector 없어도 main이 직접 구현 → M3 study → 12축 audit → yaml 반영.**
> 미채택은 오직 **'실데이터 상관 없음'(실검증 후)** 만 정당. "collector 미구축/후순위/이연"은 탈락 사유 **부적격**.
> candidate-ledger = **최종 잔여물 문서**(genuine 탈락만), 첫 작업 아님.
> audit = 종목별 추가 완료마다 별도 opus subagent, 기준 = AUDIT-GUIDE.md 12축(일반 study와 동일).

**불변(5금지)**: ①점추정 covariance prior 박제 금지(validated여도 freeze X, prior_strength=wide-prior) ②합성 데이터 금지(fetch 실패=raise, 대체 X) ③자문 그대로 코드화 금지 ④single-source 단정 금지 ⑤small-N 단정 금지(n·p·Newey-West HAC·block bootstrap·Bonferroni 의무).

## §2. 완료분 (commodity, main 직접)

| 지표 | collector | 결과 | tier | audit |
|---|---|---|---|---|
| **CFTC speculative** (mm_net_long_oi_z) | ★구현완료: CFTC Socrata `6dca-aqww`(무료, copper COMEX noncomm net, 1986~) | 1m fwd ρ+0.223 HAC p=0.0025(n=394) — ★감사 격하: 12-1m momentum 통제만 통과, trailing 1/3/6m 통제 시 p=0.13~0.61 소멸 + PIT T+3 conservative-lag p=0.76 소멸 = momentum proxy+월경계 취약. n=405 미추적 오류 | **structural_low_confidence / validated_alpha=false** (validated 과대주장 정정) | ✅ a0fdca0e=**불충분, tier 격하**. 재신청=trailing 통제 생존+M+2 forward 재검증 |
| **China credit impulse** (china_credit_impulse_z) | DBnomics BIS WS_TC/Q.CN.P.A.M.770.A + IMF PCPS copper | 18 test 전부 Bonferroni/HAC/FDR **비유의** (방향성 약 양만) | structural_low_confidence / validated_alpha=false | ✅충실 + 보강2 적용(hook affects 필드·pit_note) |

**스크립트**: `study-research/commodity/raw/m3-{china-credit-impulse-v2,cftc-speculative,cftc-momentum-control}.py` + `*-results.json` + `validation-{china-credit-impulse,cftc-speculative}.md` + `candidate-ledger.md`.
**의의**: China=검증해서 버림 / CFTC=검증해서 validated alpha로 살림 → 양쪽 사례 확보.

## §3. ★다음 작업 (자율 재개 진입점)

### 3.1 세션 collector-request 트리아지 (이미 수신, 파일 박제됨)
- **reit**: merit 후보 19종 (대부분 free public) — pane 회신, 파일 확인 필요
- **gold**: `study-research/gold/collector-request-to-main.md`
- **crypto**: `study-research/crypto/merit-queue.md` (이연 14 중 무료=miner_outflow/hashrate CoinMetrics community, BTC-Nasdaq/Gold rolling corr yfinance/FRED, Google Trends PyTrends)
- **eq_us_cyclical**: `study-research/eq_us_cyclical/collector-request-queue.md` (Tier1 = EDGAR 10-Q sec.gov 무료, 5가설 동시 의존). ★Workflow wf_9ce20415-0d2 완주중(kill 금지)
- **eq_us**: `study-research/eq_us/collector-request-to-main.md`

### 3.2 free collector 구현 큐 (main, 우선순위)
1. **JGB-UST carry-spread** (eq_intl, audit 권고 보강) — FRED `IRLTLT01JPM156N` − `DGS10` (DBnomics 경유). eq_intl block6 전용 indicator 신설.
2. **NOAA ONI** (commodity agri) — `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` (무료, 접근 확인됨)
3. **EDGAR 10-Q** (eq_us_cyclical, 5가설 backbone) — sec.gov API(UA 이메일 헤더만)
4. **CoinMetrics community / yfinance corr** (crypto) — miner_outflow·hashrate·BTC-Nasdaq corr
각 = collector 구현 → study(이론→실데이터→상관/Rank-IC, small-N rigor) → 12축 audit(별도 opus subagent) → yaml 반영.

### 3.3 audit 결과 수신 대기
- **a0fdca0e** = CFTC speculative validated 승격 정당성 (momentum 독립성 검정 타당한지). 결과로 validated 확정 or tier 격하.

## §4. 데이터 접근 (검증된 경로)
- **FRED 호스트 직접 = timeout** (fred.stlouisfed.org 막힘). → **DBnomics 경유**: `api.db.nomics.world/v22/series/{BIS|IMF}/...` (BIS WS_TC/WS_CREDIT_GAP credit, IMF PCPS commodity price).
- **CFTC** = Socrata `publicreporting.cftc.gov/resource/6dca-aqww.json` (무료, $where SoQL).
- **NOAA** = cpc.ncep.noaa.gov ASCII (무료).
- Python: `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`, PYTHONPATH=. PYTHONUTF8=1. scipy/statsmodels/pandas 가용.
- Bash 네트워크 = `dangerouslyDisableSandbox: true` 필요(google 200 OK, FRED만 timeout).

## §5. 세션 상태 (pane 대조 11/11, 2026-05-31)
- 작업중(kill 금지): btn-common-task(eq_us_cyclical Workflow), btn-powerbi(bond_cash v2), btn-diary(eq_kr 18 subagent stuck), btn-jsh86(gold), btn-GCP(reit), btn-button(macro 보강3 적용중)
- ⛔ btn-Inv = peer 코인 라이브, study 무관 절대 kill 금지
- 모든 study 세션 alive (사용자 확인). subagent(Agent tool) = 정상(단발 audit 작동). eq_kr 18 stuck = 별건.

## §6. 핵심 lesson
- ★**psmux 다중라인 메시지 truncate** (줄바꿈 포함 시 콜론 뒤 잘림, M2/M3/MSG3 사례) → **반드시 단일라인**(`/` 구분) 송신.
- 3 audit 패턴: 재실행 bit-identical 재현 + 합성 지문 + Hard-fail(B·C·D·I) + 비유의/validated 정직성 점검.
- DISPATCH-TRACKER.md §6 = audit 현황판, stock.md = eq_us/eq_kr 주식 고도화(subagent 장애로 중단) 재개세트.
