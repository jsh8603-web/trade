# 핸드오프 — 코인 신호 생/사 판정 + corrected frame + kill-audit (자기완결)

> 2026-06-03 btn-Inv. **이 문서 1개 + .p2-*.py 스크립트로 동일수준 재개.** 다음 세션 = 측정부터 바로 시작 → 생/사 판정이 바뀌는지 확인.
> ⛔ go-live=사람게이트·push금지·risk_gate 상수 무수정·calculate_buy_score SACRED 호출만.

## §0 재개 = 측정부터 (Python 의무 경로)
```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 "/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe" <script>
```
데이터: `study-research/crypto/raw/data/coinmetrics-{btc,eth,xrp,...}-community.csv`(CM 무료 32컬럼) + `defillama-stablecoin-total.csv` + `yfinance-{gspc,vix}.csv` + `.p2-{fgi-daily,micro-funding-btcusdt,upbit-btc-long,usdkrw,micro-px-btcusdt,fred-macroliq,btc-monthly}.csv`.
**재개 1순위 = `.p2-corrected-frame.py` 재실행** → 아래 §1 표의 측정값/분류 재현 확인 → 판정 변동 여부 즉시 판정.

## §1 생/사 판정표 (분류 + 이유 + 측정값) — 변동 확인 대상
| 지표 | 생/사 | 이유(축·측정) | 측정값 | 스크립트 |
|---|---|---|---|---|
| reserve→vol | ✅ TACTICAL-CONFIRMED (vol-throttle 단독 carrier) | within 생존+I²0+전epoch+, 잔존비0.84 | within+0.31 p<.001 / ⊥HAR+cluster +0.169 p0.024 | .p2-corrected-frame, .p2-exchflow* |
| BTC momentum **Upbit** | ✅ 生(venue-specific, ★조건부) | 한국리테일 비효율, 단 ★자기 m200 Bonferroni 미통과 의심+kimchi 공선 | Upbit donch20 전체+0.121 p0.011·2024+ +0.161 p0.032 | .p2-wired-validate, .p2-ledger-vs-frame, (Upbit는 .p2-upbit-btc-long.csv inline) |
| BTC momentum **글로벌** | ❌ 死 | E3(2022-26) 점추정 +0.00 (★근거=E3≈0, I²86% 아님=N=3 허상) | within+0.149(무효)·per-epoch +0.27→+0.13→0.00 | .p2-corrected-frame |
| MVRV ⊥momentum 잔차 | ✅ TACTICAL-CONFIRMED (소가중 valuation) | 직교잔차 E3까지 생존(momentum과 달리) | within+0.185 p0.007 I²0 E3+0.14 | .p2-corrected-frame, .p2-adopted-reframe |
| kimchi→수익 | ✅ 生(과열 throttle, I²72% magnitude불안정) | 과열 역추세, ⊥cluster 생존 | within−0.198 p0.033 | .p2-allframe-audit, .p2-corrected-frame |
| btc_dominance | ✅ candidate(throttle) | epoch-FE+RE I²0+VIX 통과(직전 methodology-audit) | within+0.14~0.22, ⊥cluster+VIX +0.20 | .p2-dominance-epochfe, .p2-allframe-audit |
| fee→수익 | △ weak candidate | within 생존하나 E1견인·세션MC marginal | within+0.131 p0.006 I²34% | .p2-freeonchain, .p2-corrected-frame |
| stablecoin→vol | ❌ 死 | 잔존비0.79≥0.5=진짜null(검정력소실 아님)+between-N=3 | ⊥HAR+reserve within+0.068 p0.38 | .p2-stablecoin-vol, .p2-corrected-frame |
| hashrate→vol | ❌ 死 | 잔존비0.97, reserve 흡수(carrier 중복) | within+0.054 p0.10 | .p2-freeonchain, .p2-adopted-reframe |
| volofvol→vol | ❌ 死 | E3 ⊥HAR 흡수 | 잔존비0.89, E3 p0.49 | .p2-corrected-frame |
| netflow→수익 | ⚠️ 死→regime-conditional 부활대상 | within p1.0 but inflow=강세증거금/약세매도압 교호항 미검정 | within p1.0 | .p2-exchflow |
| active addr→수익 | ⚠️ 死(★false-kill 의심) | ⊥cluster 흡수 but 잔존비게이트·fwd90·PC1제외 미적용 | 단독+0.10 p0.018 / ⊥cluster +0.039 p0.35 | .p2-corrected-frame |
| breadth alt-season | ⚠️ 死(★false-kill, 오버레이 부활후보) | IC−0.13 진짜·net-cost로만 사망 | net Sharpe 0.39≪BH 1.13 | .p2-netcost-breadth |
| core_buyscore(mean-rev) | ❌ 死 | 음=떨어지는칼날(역방향), Bonferroni후 null | within−0.06~−0.11 | .p2-wired-validate |
| m2→수익 | ❌ 死/△(표본부족 보관) | 부호반전·single-episode | full p0.76, 긴축−0.36/완화+0.09 | .p2-macro-reframe |
| real_rate Δ→수익 | △ candidate(월별만) | 월 −0.40 robust, 일별 null | 월 −0.40 p<.001 / 일별 p0.56 | .p2-macro-reframe, .p2-adopted-reframe |
| dxy/net_liquidity | ❌ 死 | forward 예측 약/single-episode | — | .p2-macro-reframe |
| 데이터게이트(SOPR·청산·OI·miner·whale) | 🔒 미측정 | 유료(Glassnode/Coinglass)·intraday | — | — |

## §2 CORRECTED FRAME (생/사 판정 기준 = 다음 세션도 이 칼로 측정)
- **C1** RE-meta(부호일관+I²) 1차 스크린, within-FE=tactical 확정칼(전역 1차kill 폐지)
- **C2** within 전 Var(x̃)/Var(x) 잔존비 게이트: <0.5=검정력소실(overlay격상) / ≥0.5=진짜null
- **C3** 부호반전≠무신호: 전구간 무신호 kill은 부호일관 null만. 부호반전=regime-conditional(Indicator×Regime) 재측정
- **C4** 직교화 먼저→I²-gate→timescale match→FDR (비가환 순서고정)
- **C5** ★RE-meta I² N=3=heuristic만(hard gate 아님, k=3 점추정 허상). within도 epoch 경계 임의=민감도 미보고
- **C6** tactical/structural 구분=데이터소스 아닌 regressor persistence
측정 표준: rank-IC(Spearman)+NW-HAC(maxlags=45=1.5×30), epoch 3분할(E1~16/E2 17-21/E3 22-26)+강세약세+BTC-SPX corr+긴축완화.

## §3 자문 박제 포인터 (전부 연결)
- `.consult-killcriterion-RESPONSE.md` — claude-web 1차(within-FE 비판, RE-meta 1차 전진 권고). gemini 실패.
- `.consult-killcriterion-briefing.md` — 1차 질의
- `.consult-killaudit-briefing.md` — kill-audit 질의(축·측정·타당성 7Q)
- kill-audit R1 원문: gemini=`C:/msys64/tmp/claude/claude/D--projects-Inv/316f0476-2ba0-4ab8-b39f-1233442e8beb/tasks/bq7hmeyfd.output` / claude=`.../bkx3olx6l.output` (JSON .response)
- `.frame-change-corrected-20260603.md` — current→corrected 상세 + §7 R1 수렴
- audit subagent 결과 = 본 핸드오프 §4 (원문 task a5ee493c9ae1d7387)

## §4 audit subagent 평가 (적용 정확도 2/6) + ★pending 정정 (다음 세션 의무)
독립 감사관이 "자문 수렴→ledger 적용"을 A~F 평가: **C2(잔존비)·F(over-application 없음)만 정확, A=부분, B/C/D/E=미적용**.
- ✅ **D 정정 완료(2026-06-03)**: 글로벌 momentum 死 근거 I²86%→E3≈0.00 교체(ledger coin_tsmom 시정). ★잔여: reserve "I²0% 동질" robustness도 N=3 허상 caveat 박제 필요.
- ⏳ **C (Upbit 과대주장)**: ledger "carrier 유지·최근 강화"를 **조건부 격하**(2024+ p0.032×m200≫1=자기 Bonferroni 미통과 false-SURVIVE + kimchi 공선[⊥kimchi 미검정] + 1.5년 window + capacity cap). 같은 ledger 내 reserve/dominance엔 m200 적용하면서 Upbit 미적용=잣대 비일관.
- ⏳ **B① active addr**: 흡수기각에 자문 4결함(잔존비게이트·fwd90·PC1 test변수제외·과통제) caveat + 재검 트리거 추가.
- ⏳ **B② breadth**: "저회전(월간)·threshold band·regime-tilt 오버레이 부활" 권고 박제.
- ⏳ **E 누락**: reserve SPOF→흡수지표 ensemble/fallback+OOS e-CUSUM / tail-risk·capitulation gap(급락 꼬리 무방비) / venue 다변화 Indodax·BTCTurk·Bitso·Luno(Bithumb=Upbit 동일시장 무의미) / 4축 adoption축 결손 / basis-momentum·on-chain realized-price=momentum부활 아닌 신규지표 검정.

## §5 핵심 결론 (생/사 종합)
- **alpha**: Upbit BTC momentum 1개(글로벌 死=microstructure 효율화, 자산 momentum 소멸 아님). ★단일 carrier+capacity+kimchi공선 위험.
- **valuation**: MVRV⊥momentum 잔차 소가중(E3 생존).
- **vol-throttle**: reserve 단독 carrier(★SPOF, PIT 막힘=별도 harness2-wf 빌드).
- **과열**: kimchi·btc_dominance.
- **충분성**: 추세추종+과열회피 골격은 충분, but venue집중·vol PIT게이트·미시구조(청산/OI)부재·adoption축 결손으로 정밀타이밍·급변동·tail 방어 불충분.
- ledger 최종 = crypto adopted 6/candidate 12/rejected_provisional 15 (헤더 6-03f closure).

## §7 ★자문이 "틀렸다" 한 판정 + 정정 측정법 + 재실행 (다음 세션 = 이대로 재측정→판정 변동 확인)
> 형식: 현 판정 / 자문 지적(왜 틀렸나) / 정정 측정법(코드 어떻게) / 재실행 / 판정변동 조건.

**① 글로벌 momentum [死]** — 자문(claude+gemini 만장일치): 死 근거로 든 **I²86%가 N=3 점추정 허상**(DL τ²/I² k=3서 식별불가). 정정=死 근거를 **E3(2022-26 거래regime) 점추정 +0.00**에 둠(이미 ledger 시정). 재실행 `.p2-corrected-frame.py` → coin_tsmom per-epoch E3 값 확인. 판정유지(死)·근거만 교체. **I² 점추정 보고 자체 금지**(전 신호 공통).

**② Upbit momentum [生→조건부]** — 자문(claude): 2024+ p0.032가 **세션 m≈200 Bonferroni(0.05/200=0.00025) 미통과 = false-SURVIVE** + **kimchi 공선**(둘 다 한국 리테일=이중계상). 정정 측정 2개: (a) Upbit donch20→fwd10 p값을 0.00025와 비교 (b) **Upbit momentum ⊥kimchi 직교화 후 잔존 rank-IC** 신규 측정(.p2-upbit-btc-long.csv + .p2 kimchi inline). 재실행=Upbit momentum ⊥kimchi 스크립트 신규작성. ★판정변동: ⊥kimchi서 IC 소멸→死(이중계상) / 잔존+window연장(2022+ 전체)서 유의→生. + venue 다변화(Indodax/BTCTurk/Bitso) per-venue IC 측정으로 SPOF 해소.

**③ active addr [死]** — 자문(claude #2): "⊥cluster 흡수" 단정에 4결함. 정정 측정: (i)PC1 추정서 **addr 제외**(자기직교화 오염 제거) (ii)**잔존비 Var(x̃)/Var(x) 게이트** 추가(저빈도 adoption→within이 죽였나) (iii)**fwd90 추가** (iv)PC1-only 대신 단일 valuation(mvrv) 통제. 재실행=.p2-corrected-frame.py의 addr 블록에 위 4개 반영. ★판정변동: 잔존비<0.5(검정력소실)이거나 fwd90 유의 또는 ⊥mvrv 단독서 잔존 → 生 후보(4축 demand 축 보강).

**④ breadth alt-season [死]** — 자문(claude #1·gemini): "IC−0.13은 진짜·net-cost로만 죽임". 정정 측정: standalone(net-cost 사망) 아니라 (a)**월간 리밸런싱** net-cost 재계산(.p2-netcost-breadth.py 회전주기 일→월) (b)**regime-tilt 오버레이**(alt-season=risk-on 국면 식별자로 사이징 틸트, 방향베팅 X) (c)threshold band+hysteresis. ★판정변동: 월간 net Sharpe>0.5 또는 오버레이로 결합 Sharpe 개선 → 오버레이 生.

**⑤ netflow [死→regime-conditional]** — 자문(both): within p1.0 노이즈성이나 **regime 교호항 미검정**. 정정 측정: netflow × (강세/약세 180d추세, 긴축/완화 실질금리Δ) **교호항** + 강세/약세 split 부호분리(.p2-exchflow에 regime 컬럼 추가). ★판정변동: 약세=음(매도압)·강세=양(증거금) 각 유의 → regime-conditional 生 / 둘 다 무 → 死 확정.

**⑥ M2 [死→표본부족 보관]** — 자문(both): "dead 아니라 표본부족 macro overlay 보관, 사이클 누적 시 재검"이 정확. 정정=라벨을 死→"표본부족 보류"(already candidate). 재측정=긴축 에피소드 누적(현 2018-19·2022 1~2개뿐) → 다중 에피소드서 per-regime |IC| 유의+부호반전 재현 시 부활 / 단일에피소드 유지 시 보류.

**⑦ 측정 프레임 자체 [N=3 결함]** — 자문(both): epoch 3분할이 RE-meta·within 신뢰 동시 손상. 정정: epoch-3=**서술용만**, 死/生 추론은 (a)연속 regime 조건자(bull/bear·BTC-SPX corr·실질금리Δ) rolling-window IC 안정성 (b)비중첩 주봉을 1차 근거로 격상 + block-bootstrap (c)horizon 유효N=T/30 축소 반영. cross PC1=설명분산%+test변수 제외+rolling PC 확인.

★다음 세션 1순위 = ② Upbit ⊥kimchi + ③ addr 4결함 재측정(둘 다 판정 뒤집힐 후보) → §1 표 갱신.

## §6 측정 스크립트 (.p2-*.py, 전부 임시·재실행가능)
corrected-frame(capstone) / allframe-audit / audit-remaining / ledger-vs-frame / wired-validate / stablecoin-vol / freeonchain / macro-reframe / adopted-reframe / dominance-epochfe / exchflow* / netcost-breadth
