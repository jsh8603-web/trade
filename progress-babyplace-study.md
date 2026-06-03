# progress — babyplace 위임 코인 지표 스터디 (논문 → ledger NEW 후보)

> 발신지시: btn-Inv(main) → btn-babyplace. cwd=babyplace, 작업대상=D:\projects\Inv (절대경로).
> SACRED: go-live 미접촉·push 금지·측정전용. candidate=탐구등록(채택 아님). S6 15축 hard-fail 0 전 adopted 금지. S3 외부자문 1회 없이 rejected_permanent 금지.
> 시작: 2026-06-03.

## STEP 0 — ledger 파악 + 제외목록 확인 [x]
- SSOT Read: `D:\projects\Inv\study-research\_wire\indicator-ledger.md` (crypto: adopted 6 / candidate 12 / rejected_provisional 15).
- 기각(다시 안 봄, 14): active_addresses·dxy_sensitivity·exchange_netflow·fees·holder_growth·investor_attention·ivol·micro_basis·micro_funding·net_liquidity·realized_vol·tx_nvt·volprice_corr·xs_momentum.
- candidate(재발굴 금지, 15): exchange_reserve·macro_vol_transfer·coinbase_premium·dvol_iv·vrp_funding_extreme·ssr_oscillator·tsmom·kimchi_premium·breadth_altseason·real_rate·global_liquidity_m2·sopr·liquidation·perp_oi·whale_flow·miner_flow.
- 기타 ledger 존재: mvrv·fgi·funding_rate·stablecoin_total_supply·etf_net_flow·halving_phase(adopted) / btc_price·btc_dominance(candidate) / core_buyscore(rej).

## STEP 1 — 논문 enumerate → NEW 후보 도출 [x]
- ★경로 정정: 지시서의 `C:\Users\jsh86\.claude\projects\D--projects-Inv\memory\research\` 는 **부재**. 실제 = `D:\projects\Inv\study-research\crypto\raw\` (crypto-factor-papers.md · crypto-regime-dependence-papers.md · measurement-methodology-papers.md · macro-vol-transfer-papers.md). 4개 전부 Read 완료.

### NEW 후보 (제외목록 전부와 비겹침)
| id | family | 논문 근거 | 강도 | 데이터 게이트 |
|---|---|---|---|---|
| coin_stablecoin_exchange_inflow | onchain/flow | Chi-Chu-Hao 2024 (arxiv 2411.06327, ✅동료심사): USDT 거래소 net inflow → BTC/ETH 수익 (+)예측·vol (−)예측 | **강** | ★높음: 원신호 intraday 1-6h, 무료 일봉 API 부재(Dune 자가구축만). S1 선검증 필수 |
| coin_gpr_vol | macro/risk | Digital Finance 2025: VIX·GPR이 crypto 연결성 amplify. Caldara-Iacoviello GPR | **중강** | 낮음: GPR 무료(월/일). macro_vol_transfer(VIX)와 직교성 검정 필요 |
| coin_xs_size | xsec | Liu-Tsyvinski-Wu 2022 JF: size factor 유의(소형 롱테일) | 약 | 중: universe 확장(소형 롱테일)+실거래성. xs_momentum "size베타 흡수"와 긴장 |
| coin_epu | macro | Digital Finance 2025: EPU는 연결성 weaken(약효과). Baker-Bloom-Davis | 약 | 낮음: EPU 무료 |

### skip (사유 1줄)
- crypto carry(Schmeling): basis carry=시장중립 수익원(전략)이지 directional 지표 아님. micro_basis(기각)·funding(adopted)로 흡수.
- investor_attention·ivol·network(Metcalfe): 전부 기각목록(active_addresses/holder_growth/ivol).
- low-vol anomaly: 문헌 반박(FRL 2021, crypto 부재) — 채택 말 것.
- VIX slope/term-structure·MOVE: macro_vol_transfer candidate 내 검정완료(slope·level 공선, MOVE는 VIX 흡수).

## 1차 보고 [x] btn-Inv psmux 송신 — 승인/우선순위 대기

## STEP 2~6 — 각 NEW 후보 6단계 SOP
우선순위: ① gpr_vol ② stablecoin_exchange_inflow ③ xs_size ④ epu. main 승인 완료(2026-06-03).

### ① coin_gpr_vol — verdict=rejected_provisional [x] (2026-06-03)
- S1[x] gpr-vol-papers.md(Gemini): risk-off 채널, contemp 강·predictive 약·tail 비대칭, GPR-VIX 0.3~0.6.
- S2[x] .p2-gpr-vol.py: corr(GPR,VIX)=+0.074 직교 / GPR→fwd-vol raw p0.98·⊥HAR+VIX p0.45 전부 null·부호 비일관. ★기각=VIX 흡수 아닌 forward-predictive 신호 부재. measurement axis 불일치(논문 contemp/tail vs 우리 forward IC).
- S3 생략(S2 비생존). ledger 박제 완료. 부활=tail event-study/Markov/contemp.

### ② coin_stablecoin_exchange_inflow — candidate-park [x] (2026-06-03)
- 데이터 선검증: CM Community USDT FlowInEx 1d 미지원·DefiLlama total supply만·무료 일봉 부재(Dune/유료만). 원논문 intraday 1-6h 전용→일봉 기각 금지(main 게이트). → candidate(데이터게이트 park). collector_plan=Dune intraday SQL OR 유료.

### ③ coin_xs_size — candidate-park [x] (2026-06-03)
- 소형 롱테일 universe 부재(CM Community 대형 7종만). xs_momentum 'size베타 흡수' 기각과 긴장. → candidate(universe 데이터게이트 park). 부활=survivorship-free 소형 universe.

### ④ coin_epu — rejected_provisional [x] (2026-06-03)
- .p2-epu-vol.py: throttle raw/⊥HAR/⊥HAR+VIX 전부 null(p>0.62)·directional ⊥mom p0.22(부호일관+ 약). 약신호. 부활=E3 강화+⊥fgi+월별.

## 종합 verdict (4종 전부 처리, 2026-06-03)
| 후보 | verdict | 핵심 |
|---|---|---|
| gpr_vol | rejected_provisional | forward-predictive null(VIX 흡수 아닌 신호부재), 부활=tail event/Markov |
| stablecoin_exchange_inflow | candidate(park) | 무료 일봉 데이터게이트, intraday 부활 |
| xs_size | candidate(park) | 소형 universe 데이터게이트 |
| epu | rejected_provisional | 약신호 null, 부활=E3+⊥fgi |
→ 신규 adopted 0(예상대로 약신호군). 생존 후보 없어 S3 자문·S6 audit 불요. ledger 4행 박제 완료.
