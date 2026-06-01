---
title: "15축 audit 요약 카드 (P1 도출·P2 audit subagent 전달용 자기완결본)"
tags: [study/wire, audit, 15axis, subagent-brief, self-contained]
date: 2026-06-01
scope: "decisions §12 압축본. P1(실측 도출)·P2(독립 audit) subagent 가 본 카드만으로 15축 판정. 압축 후 §12 흩어짐 방지."
source: "CONSULT-DECISIONS-wire-20260601.md §12 (9R 자문 수렴) + study-research/AUDIT-GUIDE.md §0 제1원리"
priority_rule: "★규칙=핸드오프/plan/progress 우선. decisions=상세 참고. 충돌 시 progress-wire-impl.md 공정(P1~P5) 따름."
---

# 15축 audit 요약 카드 — wire 작업 자기완결본

> **제1원리(AUDIT-GUIDE §0)**: yaml 숫자 = "사실" 아닌 **"주장(claim)"**. raw .py + 데이터를 직접 재실행/정독해 재현. 합성데이터 지문(결측·갭 없음, 2020-03 코로나·2022 긴축 이벤트 부재) 검사. 재계산 불일치 = hard-fail.
> **통과편향 차단**: main self-audit·방 self-cert 신뢰 X. raw 재계산이 판정 근거.

## 15축 = 12 study축(A~L) + 3 wire축(M~O)

### study 12축 (study-research 산출 검증)

| 축 | 본다(1줄) | hard 여부 |
|---|---|---|
| A 이론실재성 | theory-notes 가 실제 정독인가(저자·연도) | soft(날조인용만 hard) |
| **B 실데이터검증** | 실측 OOS Rank-IC>0.03 AND t>2.0(SE보정) | ★hard(합성·실측부재·n부족) |
| **C yaml추적성** | corr_prior/weight 가 B 실측서 ±5% 매칭 | ★hard(매직넘버·재계산불가) |
| **D PIT/lookahead** | 거시=first-release vintage, 가격=익일시가 | ★hard(발표전·최종개정치) |
| E 자문환각 cross-verify | 인용 수치 원본 확인 | 조건부hard(환각 claim) |
| F 반증+기각기록 | 반증조건+기각 1건+ | 조건부hard(기각 0=p-hack) |
| G effective-N tier | N한계 숫자 명시+prior 보수화 | tier강등(차단X) |
| H 미해결의문 | confound·한계 솔직기재 | soft(공란=red flag) |
| **I 무결성·생존편향** | 상폐·split·universe PIT | ★hard(생존편향=무효화) |
| J 경제유의·비용 | 왕복 0.3% 차감 후 +알파, turnover | 조건부hard(비용後 음수면 alpha주장) |
| K 다중검정 | 시도횟수 공시 + Deflated SR>1 | 조건부hard(미공시) |
| **L 통합상관 정합** | 공통인자(USD·rate·VIX·유동성) 1회 계상 + PSD | ★hard(중복베팅·PSD깨짐=통합차단) |

### wire 3축 M~O (런타임 결선 충실 — 본 wire 작업 고유)

| 축 | 본다(1줄) | Pass 증거 | hard |
|---|---|---|---|
| **M wire충실** | study 산출이 코드에 정직히 결선됐나 | (a)opt-in **off=byte-identical**(golden test `tobytes()` 해시) (b)facade call-path 추적 가능 (c)orphan inject 0 (d)cross-view monotone(어떤 뷰도 다른 뷰 부호 못 뒤집음) | ★hard(off 회귀=무효) |
| **N cross관계** | 합성 상관행렬이 수학·경제 정합인가 | (a)sign-stable (b)**read-time 합성 PSD**(Cholesky assert log-and-halt, Higham silent-repair 차단) (c)**공통인자 1회**(FX factor 이중계상 0=empirical local-return) (d)tail 부호반전 점검 | ★hard(PSD깨짐·이중계상) |
| **O leakage** | 미래정보·오염 차단됐나 | (a)PIT-safe(as_of=valid-time decision-time, transaction-time 누수 차단) (b)**reject≠missing**(tri-state, gold β:=0 lock·grand-fallback 오염 0) (c)full-sample-gate→FDR 2단계 (d)availability-lag | ★hard(lookahead·reject오염) |

## Hard-fail 코어 (1건이라도 위반 = register 차단 + 보강요청)
- study: **B·C·D·I** (숫자 무효화/검증불가)
- wire: **M**(off 회귀)·**N**(PSD깨짐·FX 이중계상)·**O**(lookahead·reject오염)

## 채널 규칙 (relationship 분류 — verdict 전제)
- **unconditional static** (20년 일별 large-n≈5052): OOS 검정 *지금* 결정적. np.eye 못 이기면 **즉각 activate OR reject**(영구 shadow=회피, 차단). 단 equivalence margin(TOST) — "못 이김" ≠ "0과 동등".
- **regime-conditional·월별 small-n**: "**UNKNOWN/INSUFFICIENT**" 정직 라벨(working facade 위장 차단) + event-driven 재평가(distinct-regime 누적 시, 달력 아님).
- np.eye-equiv 등록 = "무기여(no-contribution)" 정직 라벨(폐기 아님).

## IC1~IC8 결선 checkpoint (wire축 판정 시 대조)
- **IC1**(N): corr_prior 가 `cov2corr` 거쳐 corr 공간 주입? structural 대각이 vol 로 누수 안 됐나? lam_eff 가 prior n_eff(SEED tier/SE) 반영(low-tier 서 lam→1 회피)?
- **IC2**(M): static-Λ만 corr_prior 로, gate-Λ는 risk_gate clamp 로 분리? gate-Λ가 prior 에 누수 안 됐나?
- **IC3**(O): seed tri-state? reject 자산 β:=0 locked 로 fallback 풀 제외? group-specific fallback(grand mean 차단)?
- **IC4**: graduation owner=update_controller 5-AND? StudyRegister 자가승격 0? flip=사이클 경계?
- **IC5**(M): golden byte-identical test 존재+CI 게이트? RNG 전용 인스턴스? allocation→snapshot→shadow FP 순서?
- **IC6**: prepare_judge_call=side-effect 0? judge 소비=go-live 경계 분리?
- **IC7**(O): as_of=valid-time AS-OF decision-time resolve? de-risk preempt 가 pin 밖?
- **IC8**(N): glasso 가 local(FX-stripped) return? FX 가 structural 에만(6th factor)? A+B 이중계상 0? fx_hedge 토글이 fx_β 0/1?

## 불변식 (코드화 시 — CLAUDE.md 통합 불변식)
- reflexive loop 차단(belief→_macro 차단), L축 공통인자(VIX pool) **1회 계상 + PSD**, opt-in off 무회귀, analyst-level lens 다운그레이드 금지.
- batch β = same-day contemporaneous → cross 공분산 후보는 동조 측정이지 forward 예측 아님. 부호 단정 금지, hedge.
- regime split = 정제 도구이지 생성 도구 아님(PoC). dead 관계의 "국면 부활" = 다중비교/snooping 의심 → Bonferroni + belief-weight 이중 게이트.
- magnitude FREEZE: 점추정 박제 금지(sign-only). small-n(n<30) = LOO p + hedge 어휘 강제.

## small-n 통계 게이트 (n<30, rules/small-n-statistical-rigor + empirical-claim-presentation)
- p-value + n 명기 / ≥4 비교 시 Bonferroni·FDR / 95% CI 박제 / hedge 어휘(단정 금지: 최강·본질·강력확인·압도적·robust)
- ADF 단위근 사전검정 + level 회귀 시 coint 입증 / 잔차 DW<0.5 = spurious 의심 / Newey-West HAC SE / Block bootstrap
- verdict 5단계: CONFIRMED강력(n≥100,p<.001) / CONFIRMED(n≥30,p<.05) / PARTIAL(n=10~30) / TENTATIVE(n<10) / INSUFFICIENT(판정불가)
