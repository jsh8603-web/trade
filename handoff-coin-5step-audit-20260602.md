---
name: handoff-coin-5step-audit
description: 코인 지표 5단계 검토 완주도 상세 감사 — 지표별 진행 단계·멈춘 이유·잔여 작업·실측값·논문 레퍼런스 전체 기록
date: 2026-06-02
tags: [handoff, crypto, indicator-review, audit, 5step-gap]
---

# 코인 지표 5단계 검토 — 지표별 상세 진행도/멈춘이유/잔여작업

> **5단계 정의** (plan-coin-indicator-review.md): S1 논문 ground → S2 실측 가설(4게이트: G1 ex-ante regime·G2 multiple-testing·G3 walk-forward·G4 Newey-West) → S3 외부검토(gemini+claude 병렬) → S4 외부검토를 다른 데이터로 재검증(cross-asset/leave-episode/horizon/placebo) → S5 역공격 수렴.
> 측정 SSOT: [regime-conditional-measurement-framework.md](./study-research/_wire/regime-conditional-measurement-framework.md)
> 논문: [crypto-factor-papers.md](./study-research/crypto/raw/crypto-factor-papers.md)(factor 선택) · [crypto-regime-dependence-papers.md](./study-research/crypto/raw/crypto-regime-dependence-papers.md)(regime/time-varying) · [audit-regime-conditional-20260602.md](./study-research/crypto/raw/audit-regime-conditional-20260602.md)(15축 감사)
> ⛔ go-live=사람 게이트 · push 금지 · flag ON · Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`

---

## A. 5단계 완주 (S1~S5 풀) — 재검토 불요, 결론 확정

### A1. coin_global_liquidity_m2 — candidate (throttle only, single-episode artifact)
- **S1 ✓**: crypto-regime-dependence-papers.md. Benigno-Rosa NY Fed SR1052(2017-22 BTC-macro orthogonal), Noda 2019 AMH(효율성 시변).
- **S2 ✓**: `.p2-macroliq.py`+`.p2-macroliq-rolling.py`+`.p2-walkforward-regime.py`. 긴축국면(real rate 3MΔ>0, ex-ante=G1) M2 yoy→BTC fwd12M rank-IC **−0.539, NW-p=0.006(G4), walk-forward 2-fold/3-fold 전 fold 음(G3), Bonferroni α/12(G2)**. 4게이트 표면 통과.
- **S3 ✓**: gemini((b)candidate·shadow) + claude((b)candidate·throttle·sizing금지·BL격리). 둘 다 single-episode 의존 경고.
- **S4 ✓**: `.p2-macroliq-crossasset.py`. cross-asset ETH −0.134(무)·NDX −0.170(무)·ARKK −0.231(무) / leave-episode 2021-23 제외 −0.160(무) / horizon 1M 무→12M −0.54 monotonic.
- **S5 ✓**: 15축 audit(`audit-regime-conditional-20260602.md`)이 결정타 — 긴축 41개월 중 **연도내 IC 계산가능=2022 1개뿐**(m2_yoy 연중상수), block bootstrap 95%CI **[−0.910, −0.001] 0경계**. gemini+claude+audit+내 cross-asset 4중 수렴.
- **실측 종합**: full −0.08(무) / 긴축 −0.54(NW-p 0.006) / 2021-23제외 −0.16(무) / ETH −0.13(무).
- **멈춘 이유**: 결론 확정(완주). single-episode artifact = 즉시 사이징 불가.
- **잔여 작업(졸업 게이트)**: ①50년 equity cross-asset 다수 에피소드 생존 ②2022-drop placebo ③net-liquidity conditioner 비교(C군 참조) ④BL view 격리 유지. 통과 시 candidate→adopted(throttle).
- **논문**: Benigno-Rosa SR1052, Noda 2019(arXiv 1904.09403), 주류 M2-BTC 양(+) 문헌(우리 −0.54=반전꼬리).

### A2. coin_net_liquidity (Fed BS−TGA−RRP) — rejected_provisional (M2와 동일 artifact)
- **S1 ✓**: claude 제안("M2보다 나은 conditioner"). regime-deps-papers TGA 동학.
- **S2 ✓**: `.p2-netliq.py`. nl_yoy→BTC fwd12M FULL −0.079(무) / 긴축 −0.319(p=0.086) / nl_3m 긴축 −0.382(p=0.006).
- **S3 ✓**: gemini(낙관: regime separation·robust·M2보다 우수) vs claude(엄격: 제외=cherry-pick, M2보다 falsification 더 실패).
- **S4 ✓**: 구간별 부호반전(2018-20 +0.59/2021-23 −0.83/2023-25 혼재) + within-period 전부 무(2018-19 −0.21/2020 −0.20) = between-episode level shift 1회(Simpson). contemp +0.078 vs forward −0.079(claude reframe). corr(nl,m2)=0.737, partial(nl|m2)=+0.111.
- **S5 ✓**: 내 within-period 역공격이 claude 편 → gemini 낙관 반박. M2 대비 승격 근거 없음.
- **멈춘 이유**: M2와 collinear(0.74) + incremental 거의 없음 + 동일 single-episode → rejected_provisional.
- **잔여 작업**: throttle-only candidate 승격 원하면 사전등록 gate(holdout backtest + e-CUSUM + nl_3m 긴축 2021-23제외 생존). 미통과 시 full reject.
- **논문**: Schmeling-Schrimpf-Todorov BIS WP1087, net liq→SPX 관계도 2023-24 깨짐(claude 언급, 외부 anchor).

### A3. coin_micro_funding — rejected_provisional (전 각도 무알파 확정)
- **S1 ✓**: P9 BIS carry=crowding(funding 부호 regime 의존 정상).
- **S2 ✓**: `.p2-micro.py`(directional) + `.p2-funding-gate.py`(역추세 게이트) + `.p2-funding-crowding.py`(crowding risk-gate).
- **S3 ✓**: cointrack R1 자문(funding directional 폐기, crowding 게이트 제안).
- **S4 ✓**: 3각도 측정 — directional fwd10d BTC −0.05~−0.08↔ETH +0.06~+0.15(cross-asset 반대) / 역추세 게이트 spread 전부 비유의 / crowding risk-gate 극단|z|>2 forward drawdown 오히려 작음(−6.5% vs −7.7% p=0.001).
- **S5 ✓**: 3각도 전부 무 = funding 일봉 무알파 확정.
- **멈춘 이유**: directional·역추세·crowding 전부 무. P9 carry는 수익이지 forward drawdown 예측 아님.
- **잔여 작업**: intraday(분 단위 leverage 해소) OR 청산 캐스케이드 event-study(8h funding+liquidation 동시). 일봉은 종결.
- **논문**: P9 BIS WP1087, P13 funding zoo(arXiv 2506.08573, 170 predictor 중 63 유의=다중비교 함정).

---

## B. ★5단계 미완 — S3(자문)/S5(역공격) 누락하고 status 확정 (deprecation-evidence 미충족)

### B1. coin_xs_momentum — candidate ★추가검토 HIGH
- **진행**: S1 ✓(Liu-Tsyvinski-Wu 2022 JF size/momentum) / S2 ✓(`.p2-xsection.py`: 20코인 winner-loser tr7d→fwd10d spread, overlapping t=4.2, non-overlap thin t=1.69, long-only winner excess +1.76~2.00%/10일) / S3 부분(cointrack R1서 "Track C 사전등록" 권고만, 전용 자문 X) / **S4 ✗ / S5 ✗**.
- **실측**: winner-loser spread fwd10d +1.29~1.34%/주기(t=4.2 overlap 신기루, thin t=1.69 양유지). long-only winner excess(시장제거) +1.76~2.00%.
- **멈춘 이유**: ★**net-cost 미측정 + survivorship-free universe 미구축**. 직전 R에서 momentum 단일 carrier 확정에 집중하느라 Track C는 "사전등록" 상태로 보류. claude(R1)가 "long-only면 beta-neutral 소멸·survivorship 상방·overlap 신기루"라 즉시승격 거부.
- **잔여 작업**: ①net-cost 시뮬(alt 슬리피지 0.25%/side, 회전율) — `.p2-netcost-breadth.py` 패턴 재사용 ②survivorship-free universe(상폐 코인 포함 PIT) ③2022 OOS ④S3 전용 자문. 결합구조=pos=max(0,TS_시장)×CS_랭크(베타는 TS only).
- **논문**: Liu-Tsyvinski-Wu 2022 JF(DOI 10.1111/jofi.13119, 표본 2014-2020/07), Han-Kang-Ryu 2023(거래비용 청산).

### B2. coin_realized_vol — rejected_provisional ★추가검토 HIGH
- **진행**: S1 ✓(low-vol anomaly crypto 부재, factor-papers) / S2 ✓(`.p2-volvol.py`) / S4 부분(`.p2-regime-recheck.py` regime split 무) / **S3 ✗(vol-managed 별 axis) / S5 ✗**.
- **실측**: directional rank-IC BTC fwd10d +0.07(약)↔ETH fwd10-20d −0.08~−0.14(부호 cross-asset 불일치). regime split(불장/약장/고저변동) 전부 비유의.
- **멈춘 이유**: directional factor로는 부호 불일치라 reject. 단 **vol-managed sizing(고vol→축소)이라는 별도 axis를 S3 자문 없이 닫음**. directional IC만 보고 risk-overlay 차원 미검토.
- **잔여 작업**: ①vol-managed overlay 시뮬(Moreira-Muir: 포지션 = base/realized_vol, ablation+net-cost) ②S3 자문(vol-targeting이 Sharpe 개선하나) ③regime conditioning. directional 아닌 sizing layer로 재정식화.
- **논문**: Moreira-Muir 2017 JF(Volatility-Managed Portfolios), low-vol anomaly crypto 부재(crypto-factor-papers.md).

### B3. coin_micro_basis — rejected_provisional ★추가검토 MED
- **진행**: S1 ✓(P9 carry) / S2 ✓(`.p2-micro.py`) / S4 부분(regime-recheck 약장 −0.112 raw p=0.034 Bonferroni 탈락) / **S3 ✗ / S5 ✗**.
- **실측**: BTC 약(~0)·ETH fwd10-20d +0.11~0.14(momentum 동조 donch corr 0.39). 약장 −0.112(Bonferroni 탈락).
- **멈춘 이유**: momentum 동조(독립성 낮음) + cross-asset 불일치. funding과 따로 봤으나 carry로 묶어 통합 검토 안 함.
- **잔여 작업**: funding+basis를 carry 단일 팩터로 묶어 S3 자문 + net-cost. 약장 −0.11이 carry 통합서 살아나는지.
- **논문**: P9 BIS WP1087(carry).

### B4. coin_real_rate (coin) — candidate ★추가검토 MED
- **진행**: S1 ✓ / S2 ✓(`.p2-macroliq.py`: d_real BTC하락장 −0.480 p=0.004 Bonferroni 통과) / S4 부분 / **S3 ✗(M2 동반만) / walk-forward ✗**.
- **실측**: real level ADF I(1) spurious 무효. d_real(3MΔ) FULL −0.21~−0.25(비유의), BTC 하락장 −0.48(p=0.004).
- **멈춘 이유**: M2와 동반 측정만 하고 real rate 전용 walk-forward/cross-asset 미완. M2가 single-episode로 판명되며 real도 동일 의심(우선순위 밀림).
- **잔여 작업**: `.p2-walkforward-regime.py` 패턴으로 d_real BTC하락장 walk-forward + cross-asset(ETH/NDX). M2와 동일 single-episode 예상이라 빠른 종결.
- **논문**: Benigno-Rosa SR1052, 본 세션 M2 사례.

### B5. coin_breadth_altseason — candidate ★추가검토 MED
- **진행**: S1 ✓ / S2 ✓(`.p2-breadth.py`: alt-BTC spread rank-IC −0.124~−0.147 p<0.001) / S3 부분(cointrack R1) / S4 ✓(`.p2-netcost-breadth.py` net-cost 탈락 Sharpe 0.39) / **S5 부분**.
- **실측**: breadth→alt-BTC fwd spread −0.12~−0.15(robust rank-IC). regime gate 가설 기각. net-cost rotation Sharpe 0.39 ≪ BTC보유 1.13.
- **멈춘 이유**: 일별 rotation net-cost(연41회전환×0.40%)로 탈락. kimchi와 독립(corr −0.206) 확인했으나 실행불가.
- **잔여 작업**: ①저빈도 리밸런싱(월1) net-cost 재측정(회전율↓로 살아나나) ②survivorship-free ③2022 OOS.
- **논문**: (alt-season 산업 출처, 동료심사 약 — Metcalfe breadth 학술 부재).

### B6~B9. 추가검토 LOW (이론+측정 이미 약함, S3 1회로 정식 종결)
- **coin_dxy_sensitivity** (rejected_prov): S2+S4 regime split(완화 +0.25 marginal). 멈춘이유=Benigno-Rosa orthogonal 문헌+marginal. 잔여=forward 예측 아닌 contemporaneous risk-on/off 게이트 재정식화 시 S3. 논문=SR1052.
- **coin_core_buyscore** (rejected_prov): S2+S4 regime split(불장 −0.30 더 역방향/약장 무). 멈춘이유=mean-rev=momentum 우세 이론(Liu-Tsyvinski 2021 RFS)+전 regime 무. 잔여=external_bonus(뉴스/온체인 PIT) 포함 재평가 OR 다국면 OOS. 논문=Liu-Tsyvinski 2021 RFS, Jegadeesh-Titman.
- **coin_volprice_corr** (candidate): S2만(BTC/ETH fwd +0.13~0.16 thin 유의). 멈춘이유=momentum과 ρ0.51 collinear(독립 이득 +0.01~0.02). 잔여=cross-sectional 또는 결합가중 S3/S4. 논문=(momentum 파생).
- **coin_active_addresses** (rejected_prov): S2만(무신호+metcalfe_resid lookahead). 멈춘이유=full-sample beta lookahead 결함+단순활성도 무신호. 잔여=expanding-window beta OOS+MVRV 직교성. 논문=Peterson 2018 Metcalfe(단 blockchain.com addr=거래소 내부이동 노이즈).

---

## C. ★측정 자체 안 함 — 데이터 게이트(유료), S2 미진입
| 지표 | status | 멈춘 이유 | 잔여 작업 | 추가검토 | 논문 |
|---|---|---|---|---|---|
| coin_exchange_netflow | candidate | Glassnode/CryptoQuant 유료, mempool 부분만 | 데이터 확보 후 일봉 전이 검증(intraday 1-6h→일봉) | ★**HIGH** | **Chi-Chu-Hao 2024 arxiv 2411.06327**(USDT 거래소 net inflow=유일 동료심사 robust) |
| coin_sopr | candidate | Glassnode 유료 | MVRV 보완 cycle 진동 측정 | MED | Glassnode SOPR |
| coin_perp_oi | candidate | Binance openInterestHist 30일 제한 | Coinglass 장기 OI z-score | MED | P13(arXiv 2506.08573) |
| coin_liquidation | candidate | Coinglass liquidation 유료 | 2022 LUNA/FTX 캐스케이드 Tail-MR | MED | (강제 디레버리징 V반등) |
| coin_exchange_reserve | candidate | 유료 | 거래소 잔고↓=공급충격 | MED | (공급충격 prior) |
| coin_miner_flow / coin_whale_flow | candidate | mempool 부분/유료 | halving 공급 schedule 연동 | LOW | (채굴자 매도압력) |

---

## D. adopted (이미 시스템 weight>0) — 5단계 관점 진행도 (cycle2 audit 기반, 5단계 미적용)
- **mvrv_btc** (0.55): H1 검증(validation-h1-mvrv.md), marginal Spearman −0.071. 5단계 S3/S4 미적용(cycle2 12축 audit만). 잔여=eff_n<30 walk-forward.
- **stablecoin_total_supply** (0.2): Granger supply→BTC p<0.005(lag7d). validation-h3.
- **funding_rate** (0.15): ★자문 REJECT cascade 부호 정반대. extreme만. (coin_micro_funding과 별개=adopted 잔존, 재검토 대상일 수 있음)
- **fgi** (0.1): MVRV와 강 공통원인 매개. **halving_phase** (0.1): regime label only. **etf_net_flow_usd** (0.05): post-2024 n=613.
- ⚠️ **이들 adopted도 5단계(특히 S3 외부검토·S4 cross-validation) 미적용** — cycle2 12축 audit만 거침. 엄격히는 재감사 대상이나 이미 시스템 반영+weight 보수적이라 우선순위 낮음.

## E. 단기 가격 트랙 (직전 R 확정)
- **btc_price/coin_tsmom** (candidate→adopted 후보): S1~S5 사실상 완주(net Sharpe 1.42, drawdown 방어, cointrack R1 수렴). 잔여=go-live 코드 배선(사람 게이트).
- **coin_kimchi_premium** (candidate): level→Upbit fwd10d −0.211, throttle 역할 확정. kimchi↔breadth 독립. 잔여=throttle overlay 코드(go-live).

## F. ★다음 세션 우선순위 (추가검토 가치순, 전부 자율 가능 표시)
1. **coin_xs_momentum net-cost+survivorship** (HIGH, 자율 가능 — .p2-xs-*.csv 보유) — Track C 독립차원 실행가능성.
2. **coin_realized_vol vol-managed S3 자문** (HIGH, 자율 가능) — Moreira-Muir 프레임, directional 아닌 sizing overlay.
3. **coin_real_rate walk-forward** (MED, 자율 가능 — 빠른 종결, M2 동일 예상).
4. **coin_exchange_netflow** (HIGH but 데이터 게이트 — Glassnode/CryptoQuant 무료 tier 탐색 or 유료 확보 필요, 자율 불가).
5. **coin_micro_basis carry 묶음** (MED, 자율) · **breadth 저빈도** (MED, 자율).
6. LOW 4종(dxy/core_buyscore/volprice/active_addr) 정식 종결 S3 1회씩.

## G. 원칙
- ⛔ deprecation-evidence(decision-quality): 폐기는 quantitative null + S3 자문 1회. B군 LOW도 "이론+regime무" null은 있으나 S3 미거침 → rejected_permanent 불가, rejected_provisional 유지.
- crypto는 "전기간 불일치"가 rejected_permanent 사유 아님(instability=norm). permanent는 이론·데이터 무결성 결함만.
- go-live·실 사이징=사람 게이트. 거시 신호=throttle only(sizing/BL-view 금지).

---

## H. ★동일 수준 재현 가이드 (이 파일만 읽고 5단계를 내가 한 것과 동등하게 실행)

### H1. 5단계 실행 레시피 (각 단계 구체 실행법)
- **S1 논문 ground**: `Agent(subagent_type="general-purpose", run_in_background=true)` 웹 리서치. 프롬프트 필수항목 = (a)주제별 조사 5~6개 (b)우리 실측 대조표 (c)3계층 저장 경로(`study-research/crypto/raw/{topic}-papers.md` frontmatter + `~/.claude/memory/research/` 요약 + `~/.claude/docs/archive/research-raw/` native) (d)미확인 metadata 정직 표기 의무. 완료 통지 후 result 필드 파싱.
- **S2 실측(4게이트)**: harness 템플릿 = `.p2-walkforward-regime.py` 복사 후 변수 교체. 핵심 함수 `rank_ic_nw(x,y,lag)` = Spearman rank 표준화 → `sm.OLS(...).fit(cov_type="HAC", cov_kwds={"maxlags":h})`. **G1**=ex-ante regime mask(`real rate 3MΔ부호`=긴축/완화 · `lp−lp.shift(126)`=BTC 6M추세 · `rv30>median`=변동성). ⛔달력컷("2023부터") 금지. **G2**=Bonferroni α/(regime×factor×horizon 격자수). **G3**=2/3-fold 시간순 split + expanding one-step. **G4**=Newey-West HAC.
- **S3 외부검토(병렬 필수)**: `bash ~/.claude/skills/gemini-web-consult/send.sh send "$BRIEF"` + `~/.claude/skills/claude-web-consult/send.sh send "$BRIEF"` 둘 다 `run_in_background:true`. 브리핑 = CIO 페르소나(코드어 0) + §0 이전자문 맥락 + §1 실측 + §2 우리 의심 + §3 질문 5개(각 (1)판정 (2)근거/문헌 (3)데이터 falsification 요구). 파싱 = `json.loads(txt[txt.rfind('{\"ok\"'):])['response']`.
- **S4 재검증(자문 ≠ 정답)**: 자문이 제안한 falsification을 직접 측정 — cross-asset(`.p2-macroliq-crossasset.py` 패턴: ETH/NDX/ARKK), leave-episode(대형 구간 제외), horizon(1/3/6/12M), within-period(구간 쪼개 between vs within), partial corr(M2 통제). 자문 권고도 우리 데이터로 확인.
- **S5 역공격→수렴**: 가장 엄격한 반증을 직접 던져 살아남거나 외부 관점 N개 + 내 데이터가 한 점 수렴 시 verdict 도출. 미수렴=candidate+졸업게이트.
- **S6 15축 audit 최종검증**(★6단계로 고정, 2026-06-02): S5 verdict를 독립 audit subagent(`Agent` general-purpose, raw 재현 지시, AUDIT-GUIDE 12~15축)가 재현 검증. **hard-fail 0 확인 후에만 status 확정·ledger 박제**. over-claim/spec-code drift 잡히면 정정 후 재audit. (SSOT=프로젝트 CLAUDE.md §코인 6단계 SOP)

### H2. 판정 임계 (언제 통과/탈락)
| 게이트 | 통과 | 탈락/주의 |
|---|---|---|
| rank-IC 유의 | NW-p<0.05 (eff_n=n/h 명시) | overlapping IID t = eff_n 부풀림 |
| multiple-testing | Bonferroni α/N 생존 | raw p 단건 = data snooping |
| walk-forward | 2/3-fold 부호일관 + hit>55% | ★시간순 split이 단일 에피소드 오염(2022 재탕) → cross-asset 필수 |
| single-episode 판별 | leave-episode 제외 후 생존 ∧ within-period 부호유지 | 제외 시 소멸 ∨ within 무 = artifact(M2/net liq) |
| net-cost | gross 경제가치 ≥50% 보존 ∧ 2022 비파국적 | 보존<50%(breadth 25%) = 실행불가 |
| cross-asset | NDX/gold/EM 50년 독립 에피소드 생존 | ETH·BTC ρ0.8 = 1관측(robustness≈0) |

### H3. ★함정 체크리스트 (내가 실제 빠졌던 것 — 동일 실수 방지)
1. **full-sample 상쇄**: regime 부호반전(M2 +0.64↔−0.85)이 평균 −0.29로 무신호 위장 → 1차 단위를 regime-conditional로.
2. **single-episode를 4게이트 표면통과로 alpha 오인**: walk-forward 시간순이 2022 단일사건 재탕(연도내 IC 1개) → leave-episode+cross-asset+block bootstrap CI로만 드러남.
3. **contemporaneous(+) vs forward(−) 혼동**: 동시 comovement는 양(유동성 tide), forward 12M은 음(late-cycle 과열) = 같은 메커니즘 두 면(claude reframe). 분리 측정.
4. **leave-episode cherry-pick**: 파괴적 도구(취약 결과 죽이기)를 건설적(없던 양 부활)으로 오용. Δcorr 0.45를 30% 제거로 = not identified(net liq +0.37).
5. **검정력 인공물 축퇴**: 거시 저n(노이즈가 IC 위장) ↔ 미시구조 고n(올바른 null)이 "거시 생존/미시 사망" 비대칭으로 보임 → confirmation으로 쓰지 말 것, cross-asset으로만 판별.
6. **자문 무비판 채택**: gemini 낙관(net liq robust)도 내 within-period 데이터로 역공격 반박. S4가 S3을 검증.

### H4. 도구 인벤토리 (재사용 harness)
- `.p2-walkforward-regime.py` = 4게이트 템플릿(rank_ic_nw + regime mask + walk-forward + Newey-West)
- `.p2-macroliq-crossasset.py` = cross-asset + leave-episode 패턴
- `.p2-netcost.py` / `.p2-netcost-breadth.py` = net-cost 시뮬(turnover×cost, 2022 OOS)
- `.p2-regime-recheck.py` = 여러 신호 regime split 통합
- `.p2-overheat-indep.py` = 신호 간 독립성(부분 IC)
- 데이터 캐시: `.p2-btc-monthly.csv`(Binance 2017~), `.p2-eth-monthly.csv`, `.p2-fred-macroliq.csv`(M2SL/DFII10/WALCL/WTREGEN/RRPONTSYD/DTWEXBGS), `.p2-xs-*.csv`(20 Upbit KRW), `.p2-upbit-btc-long.csv`(2020~), `.p2-micro-*.csv`(Binance funding/basis/px)
- 공통: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 환경변수(cp949 minus 인코딩 에러 회피), Python 절대경로 필수.

### H5. status 확정 규칙 (deprecation-evidence)
- adopted: 5단계 완주 + net-cost robust. candidate: S1~S4 통과, S5 졸업게이트 대기. rejected_provisional: regime split도 무 OR 자문+null 있으나 부활 트리거 명시. rejected_permanent: 이론·데이터 무결성 결함만(crypto "전기간 불일치"는 사유 아님).
- ⛔ S3 자문 1회 없이 rejected_permanent 금지. quantitative null만으론 provisional까지.
