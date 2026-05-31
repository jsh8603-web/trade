---
tags: [type/guide, domain/inv, phase/study-system, topic/audit]
date: 2026-05-30
note: 종목 스터디 산출물 독립 감사 가이드. opus subagent 가 방 산출 도착마다 이 문서만 읽고 8+4축 독립 감사한다. main 통과편향 배제용. gemini-web + claude-web 자문(2026-05-30) 반영.
---

# AUDIT-GUIDE — 종목 스터디 산출물 독립 감사 가이드

> **누가 읽나**: main 이 spawn 하는 **opus 감사 subagent**. main 자신은 통과 편향이 있으므로(사용자
> 지적) 직접 감사하지 않는다. 감사관은 이 문서 + 방의 raw 아티팩트만으로 독립 판정한다.
> **무엇을 감사하나**: 한 방의 `study-research/{sid}/` (direction.md / raw/theory-notes.md /
> raw/validation-*.md / study_session.yaml).
> **핵심 목적**: "실데이터로 검증하지 않고 그럴듯한 이론·자문을 그대로 코드화하는 것"을 막는다.
> 한 방이 합성(synthetic seed) 시뮬로 yaml 을 채운 사건이 동기.

---

## §0. 감사의 제1원리 — Provenance + Recomputation (★가장 중요)

> claude-web 자문 핵심: **yaml 의 숫자를 "사실"이 아니라 "주장(claim)"으로 취급하라.**

방이 보고한 Rank-IC·p값·n·상관계수를 **신뢰하지 않는다.** 대신:

1. **raw/ 의 원본 데이터 + 분석 .py 를 감사관이 직접 재실행**(또는 코드·데이터를 정독해 산출이
   재현 가능한지 확인)한다. 무거우면 최소한 .py 가 실데이터를 읽고 yaml 숫자를 만드는 경로를 추적.
2. yaml 의 핵심 수치(prior_strength·base_weight·corr_prior·IC)가 **재계산/원본과 일치**하는가.
   불일치하거나 원본에서 추적 불가 = **hard-fail**(이론을 숫자로 둔갑시킨 경로).
3. **합성데이터 지문 검사**: 합성 시드는 통계적 흔적을 남긴다 — 결측·갭 없음, 주말 공백 없음,
   kurtosis 과소(과도하게 정규), 비현실적 자기상관, **알려진 역사적 이벤트 부재**(2020-03 코로나
   급락, 2022 금리쇼크, 특정 상폐일). raw 데이터에 이 사건들이 실재하는지 확인. 없으면 합성 의심.

이 한 가지(아티팩트를 주장에서 분리 → 재계산)가 "이론을 숫자로 둔갑"시키는 경로를 거의 차단한다.

---

## §1. 감사 12축 (8 핵심 + 4 신규) — 자문 반영

### 핵심 8축 (STUDY-KIT §2.5)

| 축 | 본다 | Pass | Fail |
|---|---|---|---|
| **A 이론 학습 실재성** | theory-notes 가 실제 교과서·논문 정독인가 | 저자·연도 명시, 원리·관계도 본인 정리 | 자문 답변 복붙, 출처 없음 / **날조 인용 = hard** |
| **B 실데이터 시계열 검증** ★ | validation 에 실측(소스·기간·n·상관·p·Rank-IC) | OOS Rank-IC>0.03 **AND** t-stat>2.0(SE 보정 후) | 합성·시뮬 발견 / 실측 부재 / n 부족 = **hard-fail** |
| **C yaml 도출 추적성** ★ | 가중치·corr_prior·lens 가 B 실측에서 나왔나 | yaml 수치가 OOS 회귀계수/IC 와 오차 ±5% 매칭 | 임의 가중치·매직넘버·재계산 불가 = **hard-fail** |
| **D PIT / lookahead** ★ | point-in-time, walk-forward OOS | 재무=결산일+45~90일 지연, 가격=익일시가 진입, **거시=first-release vintage** | 발표 전 시점 사용·최종개정치 사용 = **hard-fail** |
| **E 자문비판+환각 cross-verify** | 리포트 수치 primary 교차검증 | 인용 수치 원본 확인, 반례 교보재 | 코드에 쓰인 자문 중 **환각·무출처 1건이라도 = 그 claim hard-fail** |
| **F 반증가능+기각 기록** | 정량 반증조건, 기각된 가설도 기록 | 반증조건(임계·e-value·CI) + **기각 1건 이상** | 동어반복 가설 / **기각 0건 = p-hacking 냄새(hard 경고)** |
| **G effective-N / 검정력** ★tier | 관측수·regime 자기상관·N 한계 | 한계를 숫자로 명시 + prior 보수화 | (차단 아님 — §2 tier 강등) |
| **H 미해결 의문** | confound·bias·한계 솔직 기재 | §미해결 존재 | **공란 = red flag**(soft, 단 비면 의심) |

### 신규 4축 (gemini-web + claude-web 자문)

| 축 | 본다 | Pass | Fail |
|---|---|---|---|
| **I 데이터 무결성·생존편향** ★ | 상폐·티커변경·액면분할 반영, 살아남은 종목만 테스트 안 했나 | 상폐 종목 포함, split 조정, universe point-in-time | **생존편향 데이터 = hard-fail**(결과를 약화가 아니라 무효화) |
| **J 경제적 유의성·거래비용·capacity** | 통계적 유의 ≠ 경제적 유의 | 왕복 0.3%(슬리피지 포함) 차감 후 양(+) 알파, turnover 명시 | 비용 차감 후 음수인데 **alpha 주장 = hard** / lens·정성 용도는 허용 / capacity·일평균거래대금 = soft |
| **K 다중검정 보정** | P-hacking, 백테스트 시도횟수 | **시도횟수 공시(hard)** + Deflated/Haircut Sharpe>1.0 | 시도횟수 미공시·로그 거부 = hard / haircut 미적용 = tier 강등 |
| **L 통합 상관행렬 정합성** ★시스템 | 방별 partial-corr 를 main 이 이어붙일 때 | 공통인자(USD·실질금리·글로벌유동성) 중복 계상 없음, 통합행렬 PSD | 같은 베팅 중복(주식 rate β + 채권 rate + 리츠 rate) / PSD 깨짐 = **통합 차단** |

> **L 보충 (claude-web)**: 상관은 위기 시 1로 수렴(tail-correlation) → point estimate 아닌 regime별
> 안정성 검증. 중첩 forward-return 윈도우는 t-stat 을 수배 부풀림 → **Newey-West / block-bootstrap
> SE 강제**(B 의 t-stat 게이트 전제). 기준통화 단일 base-currency + FX 헤지 명시.

---

## §2. Hard-fail vs Soft vs Tier (통합 게이트 분류)

자문 원리: **hard = 숫자를 무효화/검증불가하게 하는 무결성 위반 / soft = 크기·신뢰도·capacity 를
깎되 무효는 아님 / tier = 차단 없이 신뢰도 라벨 강등.**

- **Hard-fail 코어 4 (통합 차단 — 숫자가 틀렸거나 검증 불가)**: **B**(실데이터/합성금지) · **C**(추적성·
  재현성) · **D**(PIT·lookahead) · **I**(생존편향·무결성). 위반 = 결과가 약한 게 아니라 **잘못된 것**.
- **조건부 hard**: K 시도횟수 공시 / J alpha 주장(비용 차감 후 음수면) / E 환각 claim / F 기각 0건.
  L 통합 PSD·중복(통합 단계 차단).
- **Tier 강등(차단 X, 신뢰도 라벨)**: **G effective-N 은 게이트가 아니라 tier 함수.** ★crypto vs macro
  해법 = 자산별로 게이트를 느슨하게 하지 **말고**, 같은 임계 쓰되 출력 라벨만 분리. 낮은 effective-N
  (암호화폐 halving N=4)은 t-stat>2.0 을 못 내므로 자동으로 **"validated alpha"가 아니라 "structural
  prior(저신뢰)"로 라벨링** → validated 로 위장 불가. 정직하게 prior tier 로 떨어진다.
- **Soft/정보성**: A(soft, 날조인용만 hard) · H(soft, 공란이면 red flag) · J capacity.

---

## §3. 잘된 예시 vs 불충분 예시 (감사관 캘리브레이션)

### ✅ 충실 예시 — eq_us_cyclical
- B: FRED 17시리즈(2000-02~2026-05, 316개월) + yfinance sector ETF(6591일) **실측**. validation-H3/H4/H5
  + run_validation.py + validation-metrics.json. H3 CFNAI Rank-IC +0.099(p=0.08) → **REJECT**(IC<0.10
  임계). H4 VIX 동시 IC -0.378(p<0.001) → PARTIAL. H5 rate_beta 부호분리 미입증 → REJECT.
- C: yaml 블록3·4 가 실측 IC 인용("IC=-0.378 유의", "IC<0.10 약함"). v1 IC 0.658(합성 DGP) → v2
  IC<0.10(실측) **대폭 하향**(자기확신 보수화) = C 추적성 정상.
- F: H3/H5 REJECT 기록 = 기각 정상 산출.

### ✅ 충실 예시 — commodity
- B: H5 financialization pre-2004 0.045 → 2004-2010 0.296(6배) Welch p≈0. H4 copper↔INDPRO 12m lag
  spearman ρ=0.40 p=1e-12(원안 3m → 실측 12m 정정). H7 oil threshold 10%(12건) CFNAI -0.46.
- C: yaml 7블록이 실측 통계 인용. archetype pooling 적용.

### ⛔ 불충분 예시 — eq_us_defensive (감사 실패의 전형)
- B **불충분**: raw/validation-*.md 0개, 분석 .py 0개, 실데이터 CSV 0개. raw/lens-hypothesis-quickcheck.txt
  = "**synthetic 240m, seed 20260530**" 합성데이터. H1/H2/H3 "CONFIRMED" 가 실데이터 아닌
  prior-consistent simulation. → §0 합성 지문 검사에서 즉시 적발.
- C **불충분**: yaml weight_rules rate_beta base_weight=0.18(가장 높음)이 이론 prior 만, 실측 IC 없음.
  estimation_note 에 본인이 "**실데이터 대조 미수행 초안**" 자인.
- **판정**: B hard-fail → 불충분 → register 차단 → 보강 요청(실데이터 수집 + validation-* 신규 +
  yaml 재칼리브레이션).

---

## §4. ★감사 통과 후 — 시스템 정합 판단 + 파이프라인 업그레이드 (main 책임, 사용자 지시)

> **사용자 지시**: "감사 기준을 통과한 결과물을 우리 시스템에 정합시킬 수 있을지 판단하는 건 main 책임.
> **단, 애널리스트 수준의 분석 렌즈 코드를 다운그레이드 금지.** 우리 시스템이 못 받아들이는 구조면,
> 시스템 업그레이드(파이프라인) 계획을 수립해야 한다."

감사 통과(충실) 산출을 G1~G6 골격에 통합할 때, 감사관/main 은 **정합 판단**을 추가로 한다:

1. **현 파이프라인이 방의 분석 렌즈를 표현 가능한가?** 골격 매핑:
   - lens(정성) → `weight_card` lens 필드 + judge 주입 (G3)
   - partial-corr prior → `RegimeGlasso(corr_prior=...)` (G1 learn)
   - 동적 가중치 → `weight_card.derive_weights` 재적합 + `composed_weights` (G4 flag)
   - cross-sleeve 공분산 → `system_priors.factor_implied_cross_cov` (G5)
2. **표현 못 하면 ⛔렌즈를 깎지 말고(다운그레이드 금지)**, **시스템 업그레이드 계획**을 수립한다 —
   어느 모듈을 어떻게 확장, 무회귀(추가만/opt-in/self-test), SACRED 불변. 계획은 progress 에 기록.

### 알려진 정합 격차 (업그레이드 후보 — 통합 시 판정)
| 방 렌즈 | 현 골격 표현 가능? | 업그레이드 계획 |
|---|---|---|
| **gold** VECM/State-Space γ-분해(level intercept shift) | ✗ RegimeGlasso 는 정적 partial-corr, cointegration·오차수정 미표현 | 별도 VECM + Bayesian State-Space monitor 모듈 신설(opt-in). 절대 "정적 상관"으로 다운그레이드 금지 |
| **macro** regime engine(belief→전 sleeve Σ_eff) | △ 부분 | belief-mix 공분산 스케일링 경로 G5 확장 |
| **commodity** archetype pooling(sub-sleeve) | △ composed_weights 일부 수용 | delta_arch_by_type 계층 추가 |
| **통합 상관행렬** PSD + 공통인자 중복(L축) | ✗ 방별 독립 추정 이어붙임 | `system_priors.factor_implied_cross_cov` 에 공통인자 1회 계상 + PSD projection 게이트. gold dimensional consistency(실측 베타 주입)도 여기 |
| **eq_intl** em_china sub-archetype 분리(OOS 100%) | △ | archetype membership 확장 |

> 통합 시 각 방마다 이 표를 갱신 — "수용/업그레이드 필요"를 명시하고, 업그레이드면 계획을 progress 에.

---

## §4.5 flag→동적 경로 추적 (C축 보강 — seed→라이브 진화 루프 완결성)

> 핵심 설계: 방 산출(yaml)은 **고정값이 아니라 seed(prior)**. 라이브 거래 outcome 으로 (확신/거부) flag
> 가 누적되며 weight·corr·lens 가 진화한다. 이 루프가 끊기면 "정의만 하고 작동 안 함"(사용자가 막으려는
> 패턴). 감사관은 방의 confidence_hooks(블록5)가 동적 경로를 **명시 연결**했는지 확인한다.

- **flag → weight**(구현됨): `flag_router.tilt_weights` 가 신뢰도로 base_weight 곱셈 변조(study_register:154).
  블록5 hook 에 `affects_indicator` 가 있어야 어느 weight 를 tilt 할지 연결됨. 없으면 tilt 무대상.
- **flag → lens**(U1, main 구현): confidence → lens estimation_note 동적 라벨 → qwen(agent 판단) 주입.
- **flag → corr_prior**(U2, main+방): 저신뢰 가설 edge 약화. 블록5 `affects_edge:[node_a,node_b]` 명시
  시 정밀, 없으면 node 신뢰도 결합 근사.
- **감사 체크**: hook 이 affects_indicator/affects_edge 를 비워두면 = flag 누적이 어디에도 전달 안 되는
  죽은 hook. **C축 부분 감점**(hard 아님 — main 이 근사 fallback 가능하나, 정밀도 위해 방에 보강 요청).

---

## §5. 감사 보고 양식 (opus subagent → main)

```
[감사] {sid} — verdict: 충실 / 부분 / 불충분
- Provenance(§0): yaml 수치 raw 재계산 일치 여부 / 합성 지문 검사 결과
- 12축 결과: 통과 N / 부분 M / 불충분 K (어느 축이 왜)
- Hard-fail 여부: B·C·D·I 중 위반 있나(있으면 즉시 불충분)
- Tier(G): validated alpha vs structural prior(저신뢰) 라벨
- 시스템 정합(§4): 현 골격 수용 가능 / 업그레이드 필요(어느 모듈·계획)
- 판정: register 가능(충실) / 보강 요청(부분·불충분, 항목 구체)
```

- **충실(hard 코어 통과 + 다수 축 통과)** → register(require_raw=True) 통합 + 정합 판단.
- **부분/불충분** → 방에 보강 요청(어느 축이 왜 미달, 구체적). 합성·생존편향·재계산 불일치 = 즉시 불충분.
- 감사관은 **방의 self-audit 를 신뢰하지 않는다**(self-audit 는 참고). 독립 재계산이 판정 근거.
