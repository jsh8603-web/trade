---
tags: [research, crypto, gpr, geopolitical-risk, volatility, papers]
date: 2026-06-03
type: reference
source: Gemini Pro native research (2026-06-03), raw archive ~/.claude/docs/archive/research-raw/gpr-crypto-vol-s1-gemini-20260603.txt
verification: 논문 metadata는 Gemini 검색 기반. ★Al-Yahyaee 저널·Al-Mamun 저자는 Gemini가 미확인 표기 → 인용 시 hedge. Caldara-Iacoviello 2022 AER·Bouri 계열은 교차확인 가능.
why: coin_gpr_vol S1 논문 ground. GPR→BTC vol 메커니즘/시대성/regime 3계층 + S2 실측 대조.
read-when: coin_gpr_vol 부활(tail event-study / Markov regime / contemporaneous) 재검 시.
---

# 지정학 위험(GPR) → 암호화폐 변동성 — 학술 문헌 / 우리 실측 대조

> 대상 지표: **coin_gpr_vol** (Caldara-Iacoviello GPR daily → BTC forward realized vol throttle overlay).
> 6단계 SOP **S1(논문 ground)**. ★데이터: gold study 보유 `gpr_daily.xls`(GPRD/ACT/THREAT, 1985~2026 일봉) = 데이터게이트 없음.
> ★대조 기준: gold study H7 = GPR이 gold에 safe-haven tail-amplified(q90/OLS 5.91×, OLS t2.19). BTC는 risk-asset 반대 반응 예상.

## 계층 1 — 메커니즘 (GPR → crypto vol 경로)
| 논문 | 저자·연도·출처 | 표본·방법 | 핵심 발견 | 우리 적용 |
|---|---|---|---|---|
| Aysan-Khan-Topuz 2021 | Finance Research Letters | 2015-2020, Wavelet+TVP-VAR | GPR→BTC vol 단/중기(2-16일) 양(+), 2017말·COVID서 강화 | risk-off 채널. 단 **단주기 동시** |
| Wu-Zhang-Wang 2022 | Int. Rev. Financial Analysis | 2014-2021, Quantile-on-Quantile | GPR→BTC vol 전 분위 양, **upper quantile서 급증**(불쏘시개) | tail 비대칭 — full-sample 평균은 약 |
| Bouri-Gupta-Roubaud 2019 | Economics Letters | 2011-2017, GARCH-MIDAS | ★GPR+VIX **동시 투입 둘 다 유의** 예측력 | ⊥VIX 직교 근거(흡수 아님) |
| Su et al 2020 | NA J Econ Finance ★미확인 | 2011-2018, Quantile Granger | GPR→BTC 수익 음(−)/vol 강한 양(+) = risk-asset 반응 | digital-gold 반박 |

**소결**: GPR→BTC vol 경로 = risk-off deleveraging. ★문헌 강조점 = **contemporaneous(동시) 강 / predictive(선행) 약**, **tail/upper-quantile 비대칭**(평균은 약). GPR-VIX 상관 0.3~0.6 보고(흡수 아님, 별 채널).

## 계층 2 — 시대성
| 논문 | 출처 | 표본 | 발견 |
|---|---|---|---|
| Yousaf-Ali 2020 | Int Rev Fin Analysis | 2015-19 vs 2020 COVID | COVID서 GPR-BTC vol 상관 이전보다 **강화**(성숙·주류연동) |
| (추론) | — | 2023+ ETF | 기관화로 macro 민감도↑ 합리적 추론(★동료심사 직접 부재) |

## 계층 3 — regime 의존 / tail 비대칭
| 논문 | 출처 | 방법 | 발견 |
|---|---|---|---|
| Bouri-Lien-Roubaud 2021 | J Int Fin Mkts Inst Money | Markov-Switching VAR | GPR 충격이 **고변동성 국면서만** BTC vol 양 유의, 저변동성 미미 |
| Wu-Zhang-Wang 2022 | (상동) | QQR | upper quantile 급증 = 조건부 tail 신호 |
| Al-Mamun 2020 ★미확인 | Tech Forecast Soc Change | VAR | **GPR_ACT(행위) > GPR_THREAT(위협)** 즉각·강 |

**소결**: GPR-crypto vol = 조건부/tail 신호. 고변동성 regime·upper quantile서만 활성. full-sample 평균·forward rank-IC로는 구조적 약화.

## ★S1↔S2 대조 (실측 .p2-gpr-vol.py, 2026-06-03)
- **corr(GPR_z, VIX_z)=+0.074** (논문 0.3~0.6보다 훨씬 낮음) = ★흡수 게이트 무의미, 거의 직교.
- **GPR_z → BTC fwd-vol30 rank-IC: raw β−0.001 p0.98 / ⊥HAR p0.59 / ⊥HAR+VIX p0.45 전부 null**. per-epoch 부호 비일관(E1+0.016/E2−0.056/E3−0.069) RE I²0% 부호일관=False. 부호도 논문(양) 반대.
- GPR_ACT(p0.40)·GPR_THREAT(p0.50) 둘 다 null. G1 regime(corr-HIGH/LOW 둘 다 비유의)·horizon(10/30/60d 전부 p>0.22)·cross-asset ETH(β−0.091 p0.079 marginal).
- VIX carrier 생존(E3 +0.281* OOS PASS) = macro_vol_transfer 재확인.

★**불일치 원인 = measurement axis**: 논문은 (a)contemporaneous (b)GARCH 변동성 (c)2022전 표본 (d)tail/upper-quantile. 우리는 **forward 30d realized vol rank-IC ⊥HAR**(predictive). Gemini도 "GPR은 동시 강·선행 약"이라 명시 → forward-predictive null이 정합. measurement-methodology-papers 함정(forward rank-IC가 contemp/tail 못 잡음)과 동형.

★**verdict = rejected_provisional (REJECTED, forward-predictive throttle 한정)**: GPR은 throttle overlay(forward vol 예측 필수)로 부적격. ⛔ "전기간 불일치≠영구폐기"(SACRED) — 부활 = (1)tail event-study(GPR_ACT 급등일 후 fwd vol CAR, forward라 가능) (2)Markov regime-conditional(Bouri-Lien-Roubaud) (3)contemporaneous vol 동조(단 throttle 부적합=미래 모름). research_ref=.p2-gpr-vol.py, gpr-vol-papers.md.
