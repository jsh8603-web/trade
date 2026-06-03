---
name: regime-conditional-measurement-framework
description: crypto factor 측정 방법론 SSOT — full-sample rank-IC의 구조적 결함 교정. regime-conditional 신호의 '생존 vs in-sample fishing' 판별 4게이트. 문헌 ground=crypto-regime-dependence-papers.md
type: reference
date: 2026-06-02
tags: [measurement, methodology, regime-conditional, crypto, walk-forward, in-sample-fishing]
---

# Regime-Conditional 측정 프레임워크 (crypto factor)

> **트리거**: crypto(및 regime이 질적으로 바뀌는 자산)의 지표-수익률 연관을 측정·채택·기각 판정할 때 의무 적용.
> **문헌 ground**: [crypto-regime-dependence-papers.md](../crypto/raw/crypto-regime-dependence-papers.md) 주제5·7. 핵심=Noda 2019 AMH·Benigno-Rosa NY Fed SR1052·Schmeling-Schrimpf-Todorov BIS WP1087·Feng-Giglio-Xiu 2020 JF·Harvey-Liu-Zhu.

## 0. 왜 바꾸나 — full-sample rank-IC의 구조적 결함

기존 측정(.p2-*.py 초기)은 **full-sample rank-IC 평균을 1차 판정 단위**로 썼다. crypto는 효율성·factor beta·거시연동이 전부 시변(AMH)이라:
- regime마다 부호가 반대면 full 평균이 **상쇄돼 무신호로 오판**. (실측 anchor: M2→BTC rolling 36M IC 2020 +0.64 ↔ 2024-26 −0.85 → full 평균 −0.29 무의미. `.p2-macroliq-rolling.py`)
- **"full 비유의 = rejected"** 기각이 regime-dependent alpha를 사망선고로 오역.

★문헌 합의: **"crypto factor instability is the norm"**. 전기간 일관성을 1차 채택 기준으로 쓰면 진짜 신호도 다 죽는다. → 1차 단위를 **regime-conditional**로 전환. 단 "regime-conditional 생존"과 "in-sample regime fishing(data snooping)"을 구별하는 4게이트가 없으면 무엇이든 유의하게 만들 수 있다.

## 1. 채택 4게이트 (전부 충족해야 "regime-conditional 생존")

| # | 게이트 | 요구 | 위반 패턴 |
|---|---|---|---|
| **G1** | **ex-ante regime 정의** | regime = **실시간 관측가능 상태변수**로 라벨(유동성 상태=real rate 3M Δ부호 / 변동성 상태 / F&G / 레버리지=funding-z / BTC trailing 추세). 신호 진입 시점에 이미 알 수 있어야. | ⛔ **달력컷("2023년부터")** = 사후 분할 = in-sample fishing. ⛔ regime 경계를 수익률 보고 후 조정 |
| **G2** | **multiple-testing 보정** | regime × factor × horizon 격자 비교수 N 명시 → Bonferroni α/N 또는 FDR. t-임계 상향(Harvey-Liu-Zhu t>2.78 권장). | raw p<0.05 단건 보고. snooping 보정 후 anomaly 80% 무유의화(P14/P15) |
| **G3** | **walk-forward OOS + parameter lock** | regime 룰을 in-sample 고정 → purge gap 둔 rolling/expanding window서 **conditional IC 부호가 OOS 분기마다 유지**되는지. | half-split 1회. OOS서 부호 뒤집힘=regime 정의가 noise 흡수 |
| **G4** | **autocorr 보정** | overlapping forward(6-24M) → eff_n=n/h 명시 + Newey-West HAC 또는 block bootstrap. | IID t-test on overlapping → eff_n 부풀림 |

## 2. 측정 산출 라벨 (regime별, full 단일값 금지)

ledger 기록을 **full IC 하나 → regime별 IC + 게이트 통과 현황**으로:
```
{factor} → {target}@{horizon}:
  full IC = X (참고용, 1차 판정 아님)
  regime[긴축] IC = Y (n, eff_n, Newey-West p, Bonferroni 통과 여부)  ← G1 ex-ante
  regime[완화] IC = Z (...)
  walk-forward conditional: OOS 분기 부호일관 K/M (G3)
  게이트: G1✓ G2✓ G3? G4✓  → status
```

## 3. status 판정 (4게이트 → ledger 4-state 매핑)

- **adopted**: G1~G4 전부 통과 + 경제적 robustness(net-cost). regime-conditional이라도 weight_rules에 regime 조건부로 박제.
- **candidate**: G1·G2 통과, G3(walk-forward) 또는 G4 미완. = "regime alpha 후보, OOS 검증 대기". (예: M2 긴축국면 −0.54 Bonferroni 통과, walk-forward 미완)
- **rejected_provisional**: full 비유의 + ex-ante regime split도 미통과 OR 달력컷만 유의(G1 위반). 영구폐기 아님(데이터 누적·새 regime 정의 후 재평가). 부활 트리거 명시.
- **rejected_permanent**: 이론 자체 기각 OR PIT-corrupt OR spec-code drift. (regime-dependence는 permanent 사유 아님 — 문헌상 instability가 디폴트라 "전기간 불일치"만으로 영구폐기 금지)

★**핵심 원칙**: crypto에서 "전기간 불일치"는 **rejected_permanent 사유가 될 수 없다**. 영구폐기는 이론·데이터 무결성 결함만. regime 부호반전은 정상(P9 carry crowding·P7 HMM·P8 IPCA).

## 4. 적용 이력 / 재측정 큐

- **M2/real_rate → BTC**(`.p2-macroliq-rolling.py`): G1✓(긴축 real↑ ex-ante) G2✓(Bonferroni α/12 통과, M2 긴축 −0.54·d_real 하락장 −0.48) **G3? G4?** → candidate, walk-forward+Newey-West 재측정 큐.
- **funding**(`.p2-funding-gate.py`): directional=rejected_provisional. **crowding 게이트(극단 funding-z=de-risk)** = 별 candidate(P9 BIS carry 정합). G1✓(funding-z ex-ante) 나머지 미측정.
- **단기 momentum**: Upbit=adopted 후보(분절시장, net Sharpe 1.42 G통과), 글로벌=rejected_provisional(효율화 AMH, regime 아닌 구조적 소멸).

## 4b. 검토 프로세스 연결 (6단계 SOP)

본 4게이트는 코인 지표 검토 6단계 중 **S2(실측 가설)** 단계의 측정 표준이다. 전체 흐름:
S1 논문 ground → **S2 본 4게이트 측정** → S3 외부검토(gemini+claude) → S4 외부검토를 다른 데이터로 재검증(cross-asset/leave-episode/horizon/placebo) → S5 역공격 수렴 → **S6 15축 audit 최종 검증**(독립 subagent, raw 재현, hard-fail 0 확인 후에만 status 확정·ledger 박제).
→ SSOT: [plan-coin-indicator-review.md](../../plan-coin-indicator-review.md) + [progress-coin-indicator-review.md](../../progress-coin-indicator-review.md).
★교훈(M2 사례): 4게이트 표면 통과만으로 채택 금지 — single-episode artifact·검정력 인공물은 S4 cross-asset/leave-episode로만 드러난다(15축 audit 확인: 긴축 41개월 중 연도내 IC 계산가능 2022 1개뿐, CI[−0.91,−0.001]). **S6 audit이 S5 수렴 verdict를 독립 재현으로 최종 검증** — audit이 hard-fail 잡으면 status 확정 보류·정정 후 재audit.

## 5. 관련 rule
- `~/.claude/rules/empirical-claim-presentation.md` §1.3(e) regime-conditional + §1.4 autocorr + §1.5 multiple-comparison = 본 4게이트와 결합.
- `~/.claude/rules/small-n-statistical-rigor.md` = regime split 시 n 작아짐 → hedge 어휘.
- CLAUDE.md §지표 ledger 규칙 = status 4-state.
