---
next-action: ✅regime→배분 배선 복구 완료(load_dotenv+INV_R15_WEIGHTS+게이트통일, 회귀200passed). 다음=L1 검토(regime 배분 NAV 4.29<정적 6.05=강세장서 보수적, regime→weights 매핑 방향 적정성) + run_multiasset_backtest.py 폐기(archive). ⛔progress 상단 명시금지(별도드라이버·우회·자체회계 금지) 준수.
session: btn-Inv (opus)
date: 2026-06-08
tags: [type/handoff, topic/prod-backtest-line, domain/multiasset]
---

# handoff — 프로덕션 백테스트 라인 보수(run_multiasset.py) + orphan 0 + FRED 키 발견 (2026-06-08)

> plan=plan-final-test-20260607.md / progress=progress-final-test-20260607.md(상단 ⛔명시금지 + P4 섹션)

## §1 현재 상태 · 첫 행동
- **완료**: `scripts/run_multiasset.py`에 `--backtest` 모드 신설 = **프로덕션 경로 보수**(별도 드라이버 우회 청산). 분기 루프 → `collect_market_state(as_of)`(거시배분) → 업종분해(portfolio_decompose) → `build_sleeve_decisions`(종목선택) → **종목마다 judge_hook + GatedOrderRouter.submit(via_gate) 경유** → 통과분 회계. 풀기간(2017~2026) 작동: **orphan 0**(GatedOrderRouter 종목경유 2653회/REJECTED 33=캡 정상, judge 2653회, bypass 0), us9-SPY **NW-HAC t=+2.07(n=36) 유의**, walk-forward IS Σ+1.372/OOS Σ+0.633 동부호, NAV 6.054(CAGR +22.15%). kr9-EWY t=+0.64 비유의.
- **★해결 완료(2026-06-08)**: 직전 진단 "FRED_API_KEY env MISSING"은 **오진**(.env에 FRED키 존재 len=32, DART/ECOS도). 진짜 원인 **2중첩**: (1) `run_multiasset.py`가 `load_dotenv` 미호출 → fred_adapter(api_key=None) env 못읽음 (2) `run_backtest`가 `INV_R15_WEIGHTS` 미설정 → `collect_market_state` 내부 macro_view=None(is_r15_enabled 게이트, coin_track_macro.py:75) → `allocate(macro_view=None)` 정적 BL prior → **36분기 배분 전부 동일**. 별도 `rc.classify`(run_backtest:690)는 작동해 regime_lbl은 찍혔지만 배분 경로와 무관. **수정 3건**: ① main()에 `load_dotenv`(레거시 run_agents.py:512 동일패턴) ② run_backtest에 `INV_R15_WEIGHTS="true"` ③ `portfolio_orchestrator.py:158` 게이트를 `is_r15_enabled()`로 통일(=="true"단독→on/true/1/yes, "on"으로 켤때 belief 동적공분산 silent-death 함정 제거). **검증**: regime별 배분 차등 작동(Reflation bond0.45/Recovery us0.38+kr0.23/Overheat commod0.15+gold0.11/Stagflation cash0.20+gold0.14), 회귀 200 passed.
- **★다음 행동(재개)**: **L1 검토** = regime 배분 NAV **4.292**(CAGR+17.57%) < 정적 **6.054**(+22.15%). 즉 regime→weights 매핑이 미국 강세장 구간에서 채권·현금 비중을 키워 보수적이라 수익 깎임. **배선은 정상**(차등 작동 확인) → 다음 층은 regime별 weight 매핑 방향이 실제 수익에 맞는지(L1 이론·yaml 검토, study-research/_wire ledger). + run_multiasset_backtest.py 폐기(archive).

## §2 진행맵 (P4 — progress 상단 P4 섹션)
- **P4-1** run_multiasset.py 백테스트 루프 + 종목선택 + 종목 gate/judge 경유 ✅
- **P4-2** attribution + 자문반영(NW-HAC/walk-forward/거래비용/survivorship haircut) — ◐ NW-HAC/walk-forward/survivorship 출력 ✅, regime별·산업별·종목별 attribution 출력은 미이식(별도드라이버엔 있었음, run_backtest엔 rows만)
- **P4-3** orphan 0 검증 ✅(GatedOrderRouter/judge 경유>0, bypass 0)
- **P4-4** run_multiasset_backtest.py 폐기(archive) — ⏳ 미실행(아직 존재)
- **미해결**: FRED 키(regime 미반영) / regime attribution 출력 / 폐기

## §3 사용자 박제 (대화 고유 결정 — ⛔최우선)
- ★**사용자 R5 강한 정정 3회+**: "실제 프로덕션 파이프라인으로 테스트" = 별도 드라이버 신설·자체회계·risk_gate/judge 우회 **금지**. 프로덕션 진입점(run_multiasset.py) **보수**해서 그걸로 테스트. **plan/progress 상단 ⛔명시금지 박제 완료 + promotion-log ERROR 자산화**(2026-06-08 프로덕션-파이프라인-우회-별도드라이버-드리프트).
- ★**사용자 지시**: 코드 의도(README/CODEMAP) 드리프트 확인하며 진행. orphan 없이 다 연결. 별도트랙 이연 금지.
- ★사용자 (1) 확정: run_multiasset.py 보수(vs engine.py vs 통합 중).
- 자문 3R(gemini+claude) 수렴: 비대칭 설계 정당 / us +12%p survivorship phantom 다수 / KR n=7→28 부호반전(미측정≠부재) / cyclical fold 기각(대형주 median$142B, 자문전제 미성립) / 거래비용·OOS·NW-HAC 필수. **사용자 "별도트랙 이연 금지"** → 자문6(NW-HAC/walk-forward/거래비용/survivorship haircut) 즉시 반영 완료.
- push·go-live·실주문 미접촉. DRY_RUN/KIS paper. 안전장치값(MAX_WEIGHT_SINGLE 0.10/SECTOR 0.30) 무단변경 금지. long-mode ON.

## §4 파일 inventory (절대경로 D:/projects/Inv/)
- **수정**: `scripts/run_multiasset.py`(★백테스트 섹션 신설: `_bt_load_us/_bt_load_kr/_bt_fundamentals/_bt_metric_panel/_bt_us_picks/_bt_kr_picks/_bt_qret/_gate_judge_filter/run_backtest` + main `--backtest` 분기). `_gate_judge_filter`=orphan 해소 핵심(종목마다 judge_hook+GatedOrderRouter.submit 경유). 라이브 `run_one_cycle`은 보존.
- **폐기 대상**: `scripts/run_multiasset_backtest.py`(별도 드라이버 — P4-4서 archive). 검증로직은 run_multiasset.py로 이식 완료. KR 시총 시점일치(과거가격×현재주식수)도 _bt_kr_picks에 반영.
- **수정**: `core/portfolio_decompose.py`(SUB_SLEEVES us_stock 3업종/kr_stock 7업종) / `stock/selection_pipeline.py`(W5 `decision["ticker"]=cand.ticker`, 이전 세션).
- **데이터**: study-research/eq_us/industries/{us_cyclical,us_defensive,us_mega_tech}/raw-v3/data / eq_kr/industries/{financial,battery,bio,shipbuilding,consumer,chemical,auto}/raw-v3/data. KODEX FDR(091170/305720/441540/091180).
- **결과**: C:/msys64/tmp/claude/mab-prod-full.txt(프로덕션 풀기간), mab-final.txt(구 별도드라이버 풀기간 비교용).

## §5 미해결·실패 (삽질 방지)
- ✅**[해결] 거시배분 regime 미반영**: 오진은 "FRED 키 부재"였으나 진짜는 **load_dotenv 누락 + INV_R15_WEIGHTS 미설정**(상세 §1). .env에 FRED키 존재(dotenv 로드 후 len=32). classify 성공해도 R15 off면 collect_market_state가 macro_view=None → allocate 정적 prior. 수정 3건(load_dotenv/R15 on/게이트통일) 후 regime별 배분 차등 확인. ⛔교훈: classify 성공 ≠ 배분 반영(allocate macro_view 경로 도달 별도 확인). .env 권한거부 ≠ 키없음(dotenv 로드 후 길이확인이 정답).
- ★**드리프트 2건 수정**(README/CODEMAP 대조): ① 거시배분 allocate 직접호출 → collect_market_state(CODEMAP:168 프로덕션 거시경로) ② sector_weight 주식자산군 합산(50%, max_weight_sector 30% 항상 초과→전부 REJECT) → **업종 비중**(order_assembly.py:72-77 look-through 정신, CODEMAP:174 order path). 업종별 _gate_judge_filter 호출(sector_weight=w_sleeve×업종몫합).
- ★**NAV 차이**: 프로덕션 경로 NAV 6.05 vs 구 별도드라이버 4.13 — gate/judge 경유 33 REJECT 재정규화 + 거시배분 경로 차이. regime 미반영(중립 prior) 상태 수치라 FRED 키 후 재측정 필요.
- regime attribution 출력 미이식(run_backtest는 rows에 regime_lbl 담으나 출력 안 함, regime_lbl도 "?"). FRED 키 후 regime별 손익 출력 추가.
- PortfolioState=단일자산 회계라 멀티에셋 회계는 "gate/judge 통과 비중" 방식(자체우회 아님=gate/judge 실경유).

## §7 ⛔ 드리프트 금지 (이번 세션 실제 위반 — 재발 방지) + 향후 방향

### ⛔ 금지 (내가 이번 세션에 실제로 한 드리프트 = 절대 재발 금지)
1. ⛔ **백테스트용 별도 스크립트 신설 금지**. 프로덕션 진입점(`scripts/run_multiasset.py`)을 **보수**해서 그 경로로만 돈다. (위반물=`run_multiasset_backtest.py`, 폐기 대상)
2. ⛔ **회계 NAV·사이징·게이트 자체 계산 금지**. risk_gate(`GatedOrderRouter.submit(via_gate=True)`)·judge_hook은 **반드시 프로덕션 코드 실경유**. 종목 비중 그대로 굴리기 금지.
3. ⛔ **거시배분 allocate 직접 호출 금지**. 프로덕션 거시 경로 = `coin_track_macro.collect_market_state(as_of)`(내부 allocate). 직접 allocate = 우회(CODEMAP:168).
4. ⛔ **sector_weight를 자산군 합산(주식 us+kr 50%)으로 넘기기 금지**. max_weight_sector(30%) 항상 초과로 전부 REJECT됨. **업종 단위 비중**으로(order_assembly.py:72-77 look-through 정신, CODEMAP:174).
5. ⛔ **진입점 부재 시 "새로 만들기" 금지**. 멀티에셋+종목선택+백테스트 단일 진입점이 없으면 → 기존 진입점에 **누락 단계를 연결**. "없으니 만든다"가 드리프트 뿌리.

### ✅ 매 작업 전 자문 (R5 재발 방지 latch)
- "프로덕션 파이프라인을 보수하며 그걸 쓰는가?" (별도물 키우는 중이면 STOP)
- "orphan 0인가?" = `grep "risk_gate\|judge\|GatedOrderRouter\|submit" 진입점.py` 호출>0 + 실행 시 bypass=0 확인. 미연결 모듈 있으면 그 테스트는 "프로덕션 테스트" 아님.
- 근거: plan/progress 상단 ⛔명시금지(사용자 직접 지시 2026-06-08), promotion-log 2026-06-08 ERROR(프로덕션-파이프라인-우회-별도드라이버-드리프트).

### 향후 방향 (순서)
1. ✅**[완료] regime→배분 배선 복구** = load_dotenv(main) + INV_R15_WEIGHTS="true"(run_backtest) + orchestrator:158 게이트 통일. regime별 배분 차등 작동 확인, 회귀 200 passed. ★다음=**L1 검토**: regime 배분 NAV 4.29 < 정적 6.05 → regime→weights 매핑이 강세장서 보수적. 배선정상, 매핑 방향 적정성(이론·yaml)이 다음 층.
2. **regime attribution 출력 추가**: run_backtest의 rows에 regime_lbl 담겨 있음 → regime별 손익(전략/us9-spy/kr9-ewy) 출력 블록 추가(구 별도드라이버 패턴 참고, 단 별도드라이버 코드는 폐기 전 참고만).
3. **run_multiasset_backtest.py 폐기**(P4-4): `archive/` 이동(rm은 home-guard, mv). 검증로직 이미 run_multiasset.py 이식 완료.
4. **자문 잔여**(별도 트랙): survivorship CRSP delisting 데이터 확보(현 haircut은 가정값) / KR κ study(κ엔진 미배선) / 거래비용 정밀화(현 25bps 단순).
5. **최종 = 모의계좌 e2e**: 라이브 `run_one_cycle`(이미 risk_gate/judge/주문경로 연결) DRY_RUN→KIS paper. ⛔go-live=사람게이트.

## §6 자문종합 (3R 수렴 — 이미 코드 반영)
- 비대칭 설계(일부 alpha/일부 베타) 정당. us +12%p = survivorship phantom 다수(밸류는 저평가=상폐집단이라 악성). cyclical fold 기각(우리 cyclical median$142B 대형주, 자문 "상폐꼬리" 전제 미성립). KR n=7→28 부호반전=미측정≠부재 실증. 실전수익성=거래비용/turnover/walk-forward OOS/NW-HAC+CI 필수→ **전부 코드 반영 완료**(run_backtest 출력). survivorship haircut(연~1.2%p 가정)은 CRSP delisting 데이터로 대체 필요(미보유). KR κ 측정=κ엔진 미배선(portfolio_decompose=정적 시총분해)이라 study 영역 별도.
