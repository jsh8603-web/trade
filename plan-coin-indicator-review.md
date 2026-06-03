---
name: plan-coin-indicator-review
description: 코인 지표 검토 방법론 SOP(6단계) + 검토 대상 지표 큐. 논문 ground→실측 가설→외부검토→교차 데이터 재검증→역공격 수렴→15축 audit 최종검증. M2 regime 사례로 정립.
type: project
date: 2026-06-02
tags: [plan, crypto, indicator-review, methodology, regime-conditional]
---

# 코인 지표 검토 마스터 플랜 (6단계 흐름)

> 인계: [progress-coin-indicator-review.md](./progress-coin-indicator-review.md)
> ★지표별 5단계 진행도·멈춘이유·잔여작업·동일수준 재현가이드(H): [handoff-coin-5step-audit-20260602.md](./handoff-coin-5step-audit-20260602.md)
> ★최신 인계(xs 격하·6단계 SOP·호라이즌·adopted 재검토·빠진축): [handoff-coin-adopted-horizon-20260603.md](./handoff-coin-adopted-horizon-20260603.md)
> ★★최신(거래소 flow/reserve 6단계·폐기 현-프레임 재검·candidate 16 논문대조·SOPR false-prior 정정): [handoff-exchflow-20260603.md](./handoff-exchflow-20260603.md)
> 측정 SSOT: [study-research/_wire/regime-conditional-measurement-framework.md](./study-research/_wire/regime-conditional-measurement-framework.md) (4게이트)
> ledger: [study-research/_wire/indicator-ledger.md](./study-research/_wire/indicator-ledger.md) (crypto 섹션)
> ⛔ go-live 배선 = 사람 게이트. push 금지. Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`.

## 0. 왜 이 플랜 — 측정 함정 2종

코인 지표 검토에서 반복된 2대 오류:
1. **full-sample rank-IC 평균으로 기각** → crypto는 regime마다 부호 반전이 정상(AMH·factor instability)이라 상쇄돼 무신호 오판. (anchor: M2→BTC full 평균 −0.29 무 ↔ rolling 2020 +0.64/2024-26 −0.85)
2. **데이터 맞아 보이면 즉시 채택** → single-episode 적합·검정력 인공물을 alpha로 오인. (anchor: M2 긴축 −0.54가 2021-23 제외 시 −0.16 무, ETH −0.13 무)

→ 사용자 정의 6단계로 두 함정 동시 차단(S6 audit이 최종 게이트).

## 1. ★검토 6단계 흐름 (모든 코인 지표 의무 적용)

```
S1. 논문 ground 확보
    - 해당 지표의 메커니즘·시대성·regime 의존을 학술 문헌으로 정초(subagent 리서치 3계층 저장).
    - 산출: study-research/crypto/raw/{topic}-papers.md + memory 요약 + archive native.

S2. 실측으로 가설 생성
    - 4게이트(G1 ex-ante regime / G2 multiple-testing / G3 walk-forward / G4 Newey-West) 적용 측정.
    - full-sample이 아닌 regime-conditional 1차 단위. 산출: .p2-*.py + result.json.

S3. 데이터가 맞아 보여도 외부검토 (필수)
    - gemini-web + claude-web 병렬. "이 발견이 경제논리·문헌에 부합하나, 모순은?" 브리핑(CIO 페르소나).
    - ★맞아 보일수록 confirmation-bias 위험 → 외부검토 생략 금지.

S4. 외부검토를 다른 데이터로 재검증 (외부검토 ≠ 정답)
    - 외부검토가 제안한 falsification을 직접 측정: cross-asset / leave-episode-out / horizon 축소 / placebo.
    - 외부검토 권고도 우리 데이터로 확인 — 맞으면 채택, 틀리면 역공격.

S5. 역공격 → 수렴
    - 내가 발견을 깨는 데이터(가장 엄격한 반증)를 던지고, 그래도 살아남거나 외부검토와 내 논리가 한 점으로 수렴하면 = 답.
    - 수렴 verdict 도출. 미수렴 = candidate 유지 + 졸업 게이트 명시.

S6. 15축 audit 최종 검증 (독립 subagent)
    - S5 수렴 verdict를 **독립 audit subagent**가 raw 재현으로 최종 검증(AUDIT-GUIDE 12~15축, regime-conditional은 audit-regime-conditional 패턴).
    - audit이 hard-fail(over-claim·spec-code drift·통계 무결성) 잡으면 status 확정 **보류** → 정정 후 재audit.
    - ★audit hard-fail 0 확인 후에만 ledger status 확정·박제. audit verdict = 최종 SSOT.
```

**status 매핑** (measurement-framework §3): adopted(6단계 통과+net-cost+audit hard-fail 0) / candidate(S2~S5 통과, S6 또는 졸업게이트 대기) / rejected_provisional(regime split도 무, 부활 트리거) / rejected_permanent(이론·데이터 무결성 결함만, "전기간 불일치"는 사유 아님).

## 2. ★완결 사례 — M2 거시유동성 regime 신호 (5단계 1회전)

- **S1**: crypto-regime-dependence-papers.md (Noda AMH·Benigno-Rosa NY Fed·Schmeling BIS·Feng-Giglio-Xiu). "crypto factor instability=norm" 정초.
- **S2**: M2 긴축국면(real rate 3MΔ>0, ex-ante) → BTC fwd12M IC −0.539, NW-p=0.006, walk-forward 전 fold 음, Bonferroni 통과. (4게이트 표면 통과)
- **S3**: gemini+claude 자문. 둘 다 (b) candidate, sizing 금지. claude=throttle overlay만, 주류 M2-BTC 양(+)인데 내 음(−)=반전꼬리 적신호, 2025Q4 OOS 붕괴 라이브 사례.
- **S4 재검증**: cross-asset ETH −0.134(무)·NDX −0.170(무)·ARKK −0.231(무) / leave-episode 2021-23 제외 −0.160(무) / horizon 1M 무→12M −0.54 monotonic.
- **S5 수렴**: 내 데이터(single-episode + BTC고유아님)가 두 모델 "검정력 인공물·에피소드 적합" 판정 확증. **수렴 verdict = candidate, throttle overlay 한정, sizing/BL-view 금지. 졸업 게이트 = 50년 equity cross-asset 생존 + 2022-drop placebo + net-liquidity(Fed BS−TGA−RRP) conditioner**.
- 산출: .p2-macroliq*.py, .consult-regime-validity-*, .p2-*-result.json. (audit 15축 = 진행 중, 완료 시 §사례 보강)

## 3. 검토 대상 지표 큐 (progress에서 추적)

S1~S5 미적용/부분적용 지표 — 진행 상황은 progress-coin-indicator-review.md.
- **거시**: M2(완결, candidate-throttle) / real_rate(S4 일부, BTC하락장 −0.48) / net_liquidity(Fed BS−TGA−RRP, claude 제안 미측정) / dxy(rejected_prov, regime marginal)
- **미시구조**: funding directional(rejected_prov, 전 regime 무) / funding crowding gate(미측정, P9 BIS 정합) / basis(약장 −0.11 Bonferroni 탈락) / realized_vol(vol-sizing 차원)
- **온체인(데이터 게이트)**: SOPR/exchange netflow/reserve/liquidation/miner/whale = 유료, 미측정. active_addr(무료, 무신호)
- **단기 가격**: BTC momentum(adopted 후보, net Sharpe 1.42) / kimchi throttle / breadth(net-cost 탈락) / xs_momentum(Track C)

## 3b. ★재검토 매트릭스 — drop 지표 × (regime × horizon × cross) 3D 그리드 (2026-06-02 사용자 지시)

> 지시: "BTC만 말고 drop한 것들 다 regime별·기간별로, cross 고려해 다시 계획."
> 진단: 지금까지 drop 판정이 **한 축씩만** 봤다 — funding=regime(H1/H2)만·일봉 / xs=horizon(7~90d)만 / M2=regime(긴축)·장기(6-24M)만. **regime×horizon 동시 교차 + cross 차원(asset/section/exchange) 미실시**. 한 축에서 죽어도 교차 칸에서 살 수 있다(M2가 긴축×장기서 −0.54 떴듯).

### 3축 정의
- **regime**(ex-ante, G1): 긴축/완화(real rate 3MΔ) · 강세/약세(BTC 6M추세) · 고/저변동(rv30) · halving phase(post 0-6/6-18/18-24m)
- **horizon**(기간): 1d · 10d · 30d · 90d · 180d · 365d (forward + trailing 둘 다)
- **cross**: cross-asset(ETH·주식 NDX·금 부호일관=robustness 판별) · cross-sectional(코인 횡단면) · cross-exchange(Upbit·Binance)

### drop 지표별 본 칸 / 안 본 칸 / 우선순위
| 지표 | regime 봄 | horizon 봄 | cross 봄 | ★안 본 핵심 칸 | 우선 |
|---|---|---|---|---|---|
| coin_real_rate | 하락장 −0.48 | 부분 | ✗ | **regime×horizon 그리드 + cross-asset(주식 실질금리 민감 sleeve 부호일관)** | ★高 |
| coin_global_liquidity_m2 | 긴축 −0.54(single-ep) | 6-24M | ETH/NDX | regime×다horizon 전셀 + Bonferroni 전체격자 | 中(single-ep 확인) |
| coin_micro_funding | H1/H2 | 일봉만 | BTC/ETH(반대) | **intraday/주봉 × regime + 청산캐스케이드 event** | ★高 |
| coin_realized_vol | regime split | directional만 | ETH(불일치) | **vol-managed(sizing) × regime × horizon** (directional 아님) | ★高 |
| coin_breadth_altseason | 일별 net-cost 탈락 | 일별만 | ✗ | **저빈도(주1/월1) × regime × cross-sectional** | 中 |
| coin_micro_basis | 약장 −0.11 | 일봉 | BTC/ETH(불일치) | funding+basis carry 묶음 × horizon | 中 |
| coin_dxy_sensitivity | marginal | forward만 | ✗ | contemporaneous risk-gate × regime × horizon | 低 |
| coin_xs_momentum | 강세/조정 | 7~90d | Binance 8년 | (size 팩터 명시 sleeve 채택 경로 = 별 트랙) | 別 |
| coin_active_addresses | ✗ | 10-60d | ✗ | expanding-window beta OOS × MVRV 직교 | 低 |
| coin_core_buyscore | trend-gate | 일봉 | ETH 약 | external_bonus 포함 × regime × 다국면 OOS | 低 |

### 측정 표준 (3D 그리드)
- 한 harness가 (regime × horizon) 2D 셀을 한 번에 산출 → rank-IC 히트맵. cross는 동일 그리드를 자산/거래소별 반복 후 **부호 일관성**으로 robustness 판정(xs서 size 베타 잡은 방식).
- **Bonferroni 전체 격자 셀 수로** (regime R × horizon H × cross C). raw p 단건 금지.
- single-episode 판별 필수: 어느 (regime,horizon) 셀이 떠도 leave-episode + cross-asset 통과해야 생존(M2 교훈).

### 재검토 큐 (우선순위순)

#### ✅ 새-프레임 sweep 완료 (2026-06-03, handoff-exchflow-20260603.md)
> 새 프레임 = 수익축+**vol예측축** 분리 / cross(지표교차=게이트·자산군교차=교란통제·코인내부=강등·측정교차=대체) / regime 연속통제 / FDR / 주봉 비중첩.
- **거래소 reserve→vol = candidate**(throttle, S2~S5 통과, S6 audit 잔여). reserve→수익=기각(효율화+ETH불일치). netflow 일별=rejected_prov. (.p2-exchflow*)
- **폐기 재검**(.p2-revisit.py): realized_vol(⊥HAR 흡수)·active_addr(⊥타지표 흡수)·netflow·mvrv(momentum proxy) 기각 robust 재확인. funding→vol 약세 −0.151 marginal.
- **candidate 재측정**(.p2-revisit2.py): volprice_corr ⊥mom 완전흡수 → **rejected_provisional 격하** / kimchi 수익역추세 독립생존(throttle 재확인)·vol 흡수 / m2→월 forward vol +0.24 작은 신규각도.

#### ⏳ 새-프레임 미적용 (다음, 우선순위순)
1. **reserve→vol S6 15축 audit**(독립 subagent) → candidate→채택 게이트. + cross-measurement(타 provider)·mechanism(order-book proxy).
2. **btc_dominance**(★ledger reason 공란=완전 미탐구): total crypto mcap 확보 → BTC.D alt-season/regime, breadth 중복성.
3. **investor attention**(Liu-Tsyvinski 2021, collect_pytrends.py 보유): attention z → fwd return/vol, external 직교, 6단계.
4. **기존 약신호 Bonferroni→FDR 재판정**(real_rate 약세·basis 약장 부활 스크리닝, .p2 result.json 재계산).
5. **데이터 게이트(사용자 결정 필요)**: USDT 스테이블코인 netflow(Chi-Chu-Hao robust 1순위, Dune 자가구축/intraday 유료)·SOPR·청산·OI·miner = 유료 구독 OR Dune 결정.
6. 저우선: dxy contemporaneous 게이트·IVOL·소형 size sort(universe 확장).

## 4. 불변 제약
- ⛔ regime은 ex-ante 관측가능 + 달력컷 금지(S2 G1). 외부검토 생략 금지(S3). 외부검토 무비판 채택 금지(S4).
- ⛔ go-live 배선·실 사이징 = 사람 게이트. push 금지. risk_gate 상수 무수정.
- 거시 신호는 sizing alpha 아닌 throttle overlay로만(현물·무레버리지, n 작으면 BL view 격리).
