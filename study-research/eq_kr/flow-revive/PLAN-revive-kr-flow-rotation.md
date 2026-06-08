---
name: PLAN-revive-kr-flow-rotation
description: 한국 주식 신호가 코드화에서 죽는 원인을 직접 측정으로 격리하고, 증권사리서치/논문 + 우리 수집기(krx_flows.py)로 부활시키는 구현 계획. 측정만 완료, 코드 구현은 미착수(계획).
tags: [type/plan, domain/inv, topic/eq-kr, topic/foreign-flow, status/plan-only]
date: 2026-06-08
related: WHY-ROTATION-SELECTION-NOT-APPLICABLE.md, cross-regime-ledger.md §2(eq_kr rows), stock/data/krx_flows.py
---

# 한국 주식 신호 부활 계획 — per-sector 외국인 flow 횡단면 rotation

> **한 줄**: 집계 외국인 flow를 **방향성 타이밍**으로 살리려는 시도는 직접 측정으로 死(비중첩 NULL). 진짜 부활 경로 = study가 한 번도 안 한 **per-sector 외국인 순매수 dispersion**을 횡단면 rotation 신호로 쓰는 것. 수집기(`krx_flows.py`)는 이미 완전구현·DORMANT. 본 문서는 **측정 증거 + 구현 계획**(코드 미착수).

---

## 1. 무엇이 죽는가 — 직접 측정으로 격리 (2026-06-08)

WHY-ROTATION 문서의 결론(횡단면 rotation 실재하나 운용 alpha 0, selection 死)을 받아들이고, **그 문서가 안 한 각도**를 직접 측정했다. 데이터=KR EW 330종목 프록시(`/tmp/kr_mkt_ret.parquet`, 2019-2026, ann vol 23.6%) vs `regime_series.foreign_net_kospi`.

| 시도 (신규 각도) | 측정 | 결과 | 판정 |
|---|---|---|---|
| 집계 flow → 방향성 sleeve 타이밍 | 월별 비중첩 IC, daily 중첩 NW-t | 월별 IC −0.04~+0.06 p>0.6 n=88 / daily fn60→fwd5 −0.114 **NW-t −2.1** | **死(방향성 alpha 0)**. daily t는 자기상관 인플레 |
| 극단 외국인 매도(capitulation) → 반등 | Q1 fwd21 vs Q5, 그리고 **비중첩** 월별 | Q1 +63%/yr vs Q5 +21% **daily t=4.74** BUT **비중첩 t=0.46 p=0.65** | **死(crash-recovery 베타)**. capitulation 18mo=6개 연도 집중(에피소드) |
| 원화강세(usdkrw) → kr_stock | 분위·월별 IC | Q5만 fwd +50.7%/yr pop(비단조), 월 IC +0.056 p=0.61 | **약·에피소드**. risk-on 동시채널, directional 아님 |
| cli_kr(경기선행) → forward | rank-IC, NW-t | IC +0.19~+0.57 **NW-t +4~5** | **PIT 누수 함정**(최신-vintage 개정값=lookahead). WHY-ROTATION 이미 적시 |

**결론**: 집계 외국인 flow/원화/CLI를 **방향성·타이밍**으로 쓰면 전부 死(또는 누수). 문헌 정합 — Choe-Kho-Stulz(2005): 외국인은 지수레벨에서 국내기관보다 정보우위 약, flow=**동시적 herding/positive-feedback**(예측 아님). → 지수 타이밍은 막다른 길.

## 2. 어디에 길이 있는가 — 문헌이 가리키는 곳

- **KCMI(자본시장연구원)·KDI**: 외국인·기관은 **종목/섹터 레벨**에서 informed trading으로 mispricing 수익, 개인=noise. edge는 **횡단면**에 있지 지수에 없다.
- **Transfer-entropy(investor-type 정보전파, arXiv 2603.20271)**: 외국인 flow가 마이크로(종목/섹터)에서 **선행**.
- 즉 study의 cross-sectional rotation이 죽은 이유(공통인자 N_eff 3.5, PC1 50%)는 **외국인 flow를 nuisance로 제거**했기 때문인데, 문헌은 그 flow의 **섹터별 분산(dispersion)** 자체가 횡단면 신호라고 말한다.

## 3. 핵심 발견 — 부활용 수집기는 이미 있다 (study가 안 썼을 뿐)

study는 "종목별 수급 = KRX API 차단"으로 가정하고 per-sector flow를 **한 번도 측정하지 않았다**. 그러나:

- `stock/data/krx_flows.py` = **완전구현 DORMANT**
  - `KrxSectorProvider.get_sector_map(as_of, market)` → WICS 종목→섹터 (PIT snapshot `data/krx_sector_snapshots.jsonl`)
  - `KrxForeignFlowProvider.get_foreign_net_by_market(as_of, market)` → **시장 전체 종목별 외국인 순매수**
  - `get_foreign_net_purchase(ticker, start, end)` → 종목 기간 순매수
  - credential 불요(pykrx/FDR 무료), off-graceful, knowable_from PIT
- 이 둘을 결합하면 **섹터별 외국인 순매수 = 12산업 횡단면 rotation 신호**를 직접 만들 수 있다. 공통인자 nuisance가 아니라 **신호 자체**.

⚠️ **본 세션 측정 게이트**: pykrx 미설치 + 네트워크 차단 → per-sector flow를 라이브 fetch 불가. 측정은 **네트워크 허용 세션**에서 수행해야 한다(아래 Phase 1).

## 4. 구현 계획 (코드 미착수 — 단계만)

### Phase 0 — 환경/데이터 게이트 (선결)
- 네트워크 허용 세션 + `pip install pykrx finance-datareader`.
- `krx_flows.py` 스모크: `get_foreign_net_by_market` 가 2019~ 일별 종목별 순매수를 주는지, `get_sector_map` WICS 12산업 매핑이 study 산업 정의와 정렬되는지 확인.

### Phase 1 — 측정 (study 워크플로, ledger candidate → 결론)
1. `study-research/eq_kr/flow-revive/`에 `measure_sector_flow_rotation.py` 작성:
   - 일별 종목별 외국인 순매수 → `get_sector_map`으로 12산업 집계 → 섹터별 순매수(거래대금 정규화 = `외국인순매수 / 섹터 시총` 또는 `/ 섹터 거래대금`, scale-free).
   - 신호 변환: 섹터 flow의 **expanding-z(24M) + cross-sectional demean(Zcs)** (= `_sleeve_rotation_kr`의 기존 Zcs 파이프와 동일 입력 형식).
   - **공통인자 residualize**: 집계 flow(전산업 공통)를 1회 빼서 L축 이중계상 차단 → 섹터 **상대** flow만 남김.
   - 측정: 섹터 Zcs(flow) vs forward 1M/3M 섹터수익 **cross-sectional rank-IC** + NW-HAC + walk-forward IS/OOS + BY-FDR(12산업 다중비교) + per-cell eff_n.
2. **판정 게이트**(adopted 조건): 횡단면 rank-IC ≥ 기존 cycle-proxy rotation(steel iron_ore +0.348 등) **이상** + OOS 부호 일관 + cost(STT 0.23%/월회전) 차감 후 IR>0 + eff_n powered. 미달 시 candidate 유지.
3. ledger 갱신: `cross-regime-ledger.md §2` per-sector flow 행 status·실측값·research_ref 확정(candidate→adopted/rejected). (CLAUDE.md 의무)

### Phase 2 — 코드 배선 (Phase 1 adopted 시에만)
- **L0 데이터 배선**: `krx_flows.py` snapshot 백필(`krx_flow_snapshots.jsonl` + `krx_sector_snapshots.jsonl`) → study harness가 raw-v3 옆에 `sector_foreign_flow.parquet`로 적재(PIT, knowable_from).
- **신호 주입**: `_sleeve_rotation_kr.py`의 `signal_z_cs(X)` 입력 패널 `rotation_signals_panel.parquet`에 **섹터 flow Zcs 컬럼 추가**(기존 cycle proxy와 **별도 신호**로, κ 게이트 통과 시만 활성). off=byte-identical(컬럼 미주입 시 기존과 동일).
- **L축 가드**: 집계 flow는 이미 macro/sleeve-timing에서 死 판정 → 섹터 **상대** flow만 rotation에 1회 계상(집계는 중복 금지).
- **운용 한계 명시**(WHY-ROTATION §E 자문 박제 준수): 횡단면 신호가 살아도 kr_stock sleeve가 작고 cap-weighted 삼성 집중이라 **portfolio alpha는 작을 수 있음**. 신호 검증 ≠ NAV 개선 보장. 소액 정적 틸트(0.04) 틀에서 dispersion이 실제 분산 기여하는지 백테스트(`run_multiasset --backtest` ④⑱축) 재확인.

### Phase 3 — 백테스트 검증
- `scripts/run_multiasset.py --backtest`의 ⑱축(yaml↔런타임 배선 정합) + ④⑤축(산업간 배분/산업내 alpha)으로 섹터 flow rotation의 실현 기여 측정. NAV/Sharpe baseline 대비 무회귀(off byte-identical) 확인.

## 5. 대안/부수 후보 (낮은 우선순위, ledger candidate 박제됨)
- **usdkrw 원화강세 regime overlay**: directional 아니나, 외국인 flow와 same risk-on 채널 → kr_stock sleeve **down-only de-risk 게이트**(원화 급약세+VIX 동반 시)로만. throttle overlay지 alpha 아님.
- **PIT-vintage CLI**: FRED `KORLOLITOAASTSAM` ALFRED first-release로 cli_kr 재측정 → 누수 제거 후에도 신호 남으면 macro regime 입력 후보. 현 series는 배선 금지(lookahead).

## 6. 산물 (재현)
- 측정 스크립트: `study-research/eq_kr/flow-revive/measure_*.py` + `_build_kr_mkt_proxy.py`.
- ledger: `cross-regime-ledger.md §2` eq_kr 신규 4행(집계flow rejected_provisional / per-sector flow candidate / usdkrw candidate / cli_kr rejected_permanent-as-wired).
- 수집기: `stock/data/krx_flows.py`(DORMANT, 부활 대상).
