# progress-killverdict-recheck — 자문 부당판정 재측정

> plan: [plan-killverdict-recheck.md](./plan-killverdict-recheck.md) · 세션 btn-Inv · 2026-06-03
> 측정 경로: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 "/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe" <script>`

## §진입 스냅샷
- 자문 1R 수렴(claude+gemini): Bonferroni→FDR / netflow·breadth 기각철회 후보 / 활성주소·글로벌momentum 死 유지 / Q4 신규지표 6개.
- 직전 §7 재측정 완료(handoff-coin-killaudit §7): ②Upbit donch20 死(kimchi흡수)·mom30 약 / ③addr 死확정 / ④breadth 死(월간 net복원하나 BTC미달) / ⑤netflow 死(부호만 일치).
- 본 plan = 자문이 "부당"이라 한 3건 추가 정정 측정법으로 재판정.

## Steps
- [ ] M1 netflow 극단치 threshold — 측정 → 검증 → 박제
- [ ] M2 breadth overlay marginal — 측정 → 검증 → 박제
- [ ] M3 FDR 재판정 — 측정 → 검증 → 박제
- [x] M4 Q4 신규지표 candidate 박제 — ledger crypto +5(coin_coinbase_premium·coin_dvol_iv·coin_vrp_funding_extreme·coin_macro_vol_transfer·coin_ssr_oscillator). ETF flow=etf_net_flow_usd 기존 adopted. 실측 IC는 미측정(OOS-보류 등급, 데이터원·가용기간 박제됨)
- [x] V 검증 subagent 독립 재현·감사 — audit a3c1b865: M1누적flow 격하(인공물)·M3 Upbit Bonf통과 over-claim 격하·M2 INSUFFICIENT 동의. 5의무 위반 3건 정정 완료
- [x] L ledger 갱신 — coin_exchange_netflow falsifier·coin_tsmom ⊥kimchi+FDR·M4 5개·sector_relative_multiple(eq_us). handoff 표 갱신 잔여
- [~] **S-Q4 6단계 SOP** — ★**완료 기준 = option 2 (5종 전부 풀 SOP S1~S6)**, 단 **자문 배치**(나머지 4종 S3를 통합 자문 1~2라운드로, 8회→4회 이내). 자율주행 ON.
  - **macro_vol_transfer**: S1(subagent a1049c4c, macro-vol-transfer-papers.md)·S2(.p2-m4-voltransfer.py)·**S3 자문 2모델 수렴**(gemini+claude, throttle-only·VIX carrier·MOVE 제외)·**S4 falsification 통과**(.p2-m4-voltransfer-s4.py/-s4b.py: event-exclusion 구조전이·⊥DXY·placebo·gold-split·quantile throttle확정) 완료. ★**잔여 = S5(⊥DVOL 결정검정, claude kill-shot, Deribit DVOL ~2021+ — dvol_iv와 데이터 공유) + S6 15축 audit**. verdict=strong candidate(VIX-only vol-throttle, E3). **main 직접**(babyplace 아님).
  - **macro_vol_transfer ✅ 완료**(S1-S6): S6 15축 독립 audit=**CONFIRMED hard-fail 0**(15수치 재현·robustness 확장 통과). verdict=candidate(structural-prior tier, throttle-only, base_weight=0 불변식). hedge 정정 적용("입증"→tentative·"확정"→시사). 승격 잔여=ex-ante 관측레짐(Markov/CME OI)+full DVOL 2021+.
  - **잔여 4종 S2 batch 완료**(.p2-m4-batch3.py): **dvol_iv·vrp_funding·ssr = rejected_provisional**(S2 null/underpowered, provisional이라 S3 불요) / **coinbase_premium = 유일 S2 생존**(fwd10 ⊥(mom,kimchi) +0.087 p0.019 BH-FDR 생존) → S3 자문 대상.
  - **coinbase_premium ✅ S3+S4 완료 = rejected_provisional**: S3 자문 2모델 수렴(단독 directional 기각)+S4 결정 falsification(.p2-coinbase-s4b.py: USDT 직교화 후 p0.033→p0.106 소멸·Kraken placebo 死·cross-asset ETH 死·fwd30 死=claude 폐기기준 i,iv 발동). USDT마찰+레짐집중, 강건 알파 아님.
  - ★**M4 전부 완료**: macro_vol_transfer=candidate(S6 CONFIRMED, structural-prior throttle-only bw=0) / dvol_iv·vrp_funding·ssr_oscillator·coinbase_premium=rejected_provisional. → **babyplace 발송 조건 충족**.
  - ⛔ S6 hard-fail 0 전 adopted 금지. 상세 plan §후속

### ★babyplace 발송 리마인더 (M4 전부 끝난 뒤 — 안 잊기)
- **작업지시서 작성 완료**: `D:\projects\Inv\.babyplace-study-task.md` (논문발 NEW 지표만, M4 5종 + 기각 15종 전부 STEP 0 제외=비겹침, 15축 6단계 cross/regime/horizon 프레임).
- **발송**: `bash ~/.claude/scripts/lib/psmux-send.sh message btn-babyplace "D:\projects\Inv\.babyplace-study-task.md 읽고 STEP 0부터 실행. 후보 도출 후 main 1차 보고."` (세션 btn-babyplace=sonnet, cwd D:\projects\babyplace).
- ⛔ **M4 5종 SOP 완료 전 발송 금지**(사용자 명시 순서). 비겹침이라 원리상 병렬 가능하나 사용자가 순차 지시.

## Phase 0a — signal-power-first 게이트 (메인 직접, 2026-06-03 압축후)
> 측정: `.p2-phase0a-gate.py` (build() 재사용). 핸드오프 §5.1 = electrs PIT 재구성 비싼 빌드 가치 판정. 라이브 epoch=2022-11+(post-FTX) n=1271. NW-HAC maxlags=45.
- **reserve→fvol30 = GREEN** (carrier resv_chg30 live β+0.304 p0.001·⊥HAR 증분 +0.271 p0.003 / reserve_z live +0.260 p0.012·⊥HAR +0.226 p0.023). event-LOO(FTX/SVB/ETF ±30d 제거) 3개 전부 유의·부호일관·live부호매칭. ★단 eff_n≈1271/30≈42(overlap) = 증분 p0.003~0.023 **moderate**(소표본 hedge).
- **netflow 류 전부 RED** — netflow_z live p0.21·⊥HAR p0.14 / **abs_netflow_z**(핸드오프 abs(netflow)) live p0.63·⊥HAR p0.79 / abs_resv_chg30 live p0.37. → §3 netflow 死 확정 **라이브 epoch 재확인**(magnitude 변형도 무신호).
- **게이트 판정**: 신호 자체는 GREEN(부호 reserve→vol 라이브 생존). ★단 **CM-무료 SplyExNtv proxy 로 이미 작동** = 비싼 electrs PIT 재구성의 한계가치 = label-vintage lookahead 제거뿐. **라이브 epoch(2022-11+)는 CM 거래소 라벨 성숙** → vintage leakage 노출 작음 → PIT 빌드 한계가치 **감소**. SR 기각 3가정(electrs self-host·군집 recall<10%·timeout)=실행위험 상존. → 옵션 분기(build vs defer) 사용자 게이트.

## 게이트 결정 (사용자 "1→3", 2026-06-03)
- **(1) DEFER** — harness2 electrs 재구성(길2) 보류. team h2wf-Inv TeamDelete 정리 완료. 신호 GREEN이나 라이브 라벨 성숙→한계가치 작음·SR 실행위험.
- **길1 forward-OOS 수집기 = 구현·seed·cron 등록 완료** — `core/data/reserve_snapshot.py`(additive, pit_query.py 0수정 차용). **CM Community API live fetch**(익명티어 SplyExNtv/FlowInEx/FlowOutEx 200, -status flash/final vintage 메타 내장) → sys_time=as_of vintage 동결 → reserve-pit-snapshots.parquet 누적. self-test PASS(vintage 격리=repaint 차단·knowable 게이트·멱등). live capture: 409행 span~2026-06-01. **Windows 스케줄 등록**: `Inv-ReserveSnapshot` 매일 12:00(scripts/run_reserve_snapshot.bat, CM flash ~11:28 KST 후). forward-OOS 자동 성장 시작 → coin_exchange_reserve binding(PIT-정합) 충족 경로.
- **(3) M4 6단계 SOP 진입** — 우선순위순 macro_vol_transfer(VIX-MOVE) 먼저.

## 측정 산물 (.p2-*.py, 임시·재실행가능)
- .p2-phase0a-gate.py = Phase 0a 게이트 (reserve/netflow → fwd-vol 라이브 IC + event-LOO)
- core/data/reserve_snapshot.py = 길1 forward-OOS vintage 동결 수집기(영구, additive)
- (작성 예정) .p2-killverdict-recheck2.py = M1~M3 통합 측정

## ★ 발견·판정 (측정 진행)
- **M1 netflow** (.p2-killverdict-recheck2.py): 단일일 z = 死 (극단치 decile 상위 p0.33/하위 p0.72, regime slope 강세 p0.48·약세 p0.25, FlowIn/Out 분리 둘 다 +0.05 p~0.10 부호 가설불일치). 누적30d flow IC=−0.128 p0.0278 (n=5451). ★**검증관 격하(2026-06-03 audit a3c1b865)**: 누적flow는 **인공물** — (1)NW maxlags=45 불충분(60서 p0.0527, 90~180서 0.065~0.073) (2)★레짐 부호반전 E3(2022+ 현재) **+0.042 p0.69**, 신호가 2011~2021 의존+2011 outlier(IC−0.44) (3)block-bootstrap p0.040·월말비중첩 p0.051. **판정: rejected_provisional 유지 + falsifier(E3 부호반전·NW민감·single-outlier·overlapping 유효n≈180) 박제**. "부활후보"는 over-claim 철회.
- **M3 FDR** (.p2-killverdict-recheck2.py): BH-FDR(q=0.10) directional **6/9 생존** vs Bonferroni 1/9(m=9). 생존: Upbit mom30·fee·MVRV잔차·Upbit donch20·active addr단독·kimchi. active addr는 ⊥mvrv서 0.21 소멸(FDR과 별개 흡수). vol family=reserve만(1/4). ★**검증관 정정**: (1)DIR+VOL 13개 통합 시 Upbit **Bonf 미통과**(reserve p0.001이 최소p 독차지), m≥30이면 BH도 기각 → "Bonf통과"는 **m=9 의존 over-claim, 격하**. (2)vol/directional 분리는 올바름(loss function 상이), 단 DIR 내부도 통제·부호·n 제각각=동질family 약함. (3)실제 시도 신호 universe m 정직추정 미박제. **판정: Bonferroni→FDR 전환 타당 / Upbit mom30 = BH(q0.10, family≤13) 생존하나 Bonf는 family 민감, "false-survive 완화"는 약 directional 한정·decay watch**.
- **M2 breadth** (.p2-breadth-monthly.py 기존): 월간 net보존 90% Sharpe+0.76 / 틸트+0.96 MDD−51% — 단 BTC보유+1.13 MDD−48% 미달. 자문: 2023-09~ 강세 단일국면이라 standalone 비교 무의미. **판정: INSUFFICIENT(단일국면, overlay 가치 판정불가) — 약세 OOS 확보 시 재평가**. 死 유지 근거 약화(벤치마크 오류 자문 인정).

## Working Notes
> [ckpt-202606030820:btn-Inv] 
- **마지막 결정**: babyplace 위임 4종 STEP 2-6 완료=신규 adopted 0. gpr_vol=rejected_provisional(★corr(GPR,VIX)=+0.074 거의직교=흡수아님 별채널이나 predictive 약→기각, 흡수게이트 무의미) / stablecoin_exchange_inflow=candidate(무료 일봉 부재=데이터게이트 park, CM 1d 미지원·intraday만) / xs_size=candidate(소형 롱테일 universe 부재 park) / epu=rejected_provisional(전부 비유의). → ★**macro_vol_transfer는 VIX-only 확정**(GPR 별채널이나 약신호라 carrier 추가 0).
- **다음 의도**: macro_vol_transfer 승격 잔여 = ex-ante 관측레짐(Markov coupling-state, BTC-SPX corr는 return동조라 부적합) + full DVOL 2021+ 페이지네이션. babyplace 후보 전부 park/reject라 main 측 신규 알파 추가 경로 소진. directional=BTC momentum 단독 확정(문헌 일치). 
- **동기화 필요**: babyplace ledger 4행 박제됨(verdict 검증 완료, supervisor OK). M4 5종 + babyplace 4종 = 코인 신규지표 라운드 종결. autopilot ON·long-mode ON. go-live·push 미접촉.

> [ckpt-202606030835:btn-Inv] ★미해결#1 해결: full DVOL 페이지네이션(뒤로) 완료 1896행 2021-03~2026-06. VIX ⊥HAR+DVOL **+0.288 p0.002 (n1575 full window)** = 감사관 "short window/tentative" caveat 해소(2023-09+ subsample +0.353과 동일방향), DVOL 자체 −0.029 p0.79 死. macro_vol_transfer ⊥DVOL kill-shot full-window 확인.
> ★ledger 정식반영 대기(파일 외부수정으로 재read 필요): coin_macro_vol_transfer 항목 "VIX ⊥(HAR+DVOL) tentative/short window pending" → "full DVOL 2021+ +0.288 p0.002 n1575 확인, caveat 해소"로 교체.
> 미해결 잔여: #2 Markov ex-ante 레짐(중간작업, 새세션 권장) / #3 데이터게이트 park 2종(intraday USDT·소형universe=데이터벽, 시간외 해결불가).
