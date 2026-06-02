---
tags: [handoff, inv, test-prep, consult-disguise, macro-validation]
date: 2026-06-02
session: btn-Inv
purpose: 다음 세션 테스트 준비 — "투자 일반론 둔갑 자문" 작성 가이드 + 실제 관계 카탈로그 + 둔갑 샘플
scope: 이번/압축 전 작업 한도 + 코드/ledger/SEED 직접 확인 후 작성 (다음 세션이 이 문서만으로 자문 자료 제작 가능)
---

# 핸드오프 — 테스트 준비: 투자 일반론 둔갑 자문 가이드 (실데이터 카탈로그 포함)

> **용도**: 다음 세션에서 수익률 테스트를 길게 진행하기 *전에*, 우리 거시→지표→배분 로직을 "코드 흔적
> 다 지우고 투자 일반론 언어로 번역" 해 외부 자문(gemini-web/claude-web)에 던질 때, **무엇을 어떤 기준으로
> 담아야 누락 없는 충실한 번역이 되는가** + **실제 관계 카탈로그**(바로 둔갑 가능한 원천 데이터).
>
> **목적(사용자)**: 수익률 테스트 전에 (a) 우리 프레임이 표준 투자 방법론에 정합하는지 (b) 빠진 지표·방법론이
> 없는지 외부 눈으로 검증. → 나중에 시뮬에서 수익이 안 나면 **"방법론 결함"인지 "코드(상수·가중치) 결함"인지
> 원인 분리** 하기 위함. 이 자문이 "방법론은 OK"를 먼저 박는 단계.

---

## 0. 한 줄 핵심

"관계가 있어요"가 아니라 **"이 관계는 크다 / 이 국면엔 작아졌다 다시 커진다 / 단독으론 보이지만 X를 통제하면
사라진다 / 표본이 작아 방향만 안다"** 까지 담아야 자문이 진짜 누락을 짚는다. = 관계의 **magnitude · regime
의존성 · 조건부성 · 통계 신뢰도** 4축을 일반 투자 언어로 옮기는 작업.

---

## 1. 둔갑 4대 기준 (하나라도 빠지면 "관계 있더라" 수준 → 자문이 표면만 봄)

### (1) Magnitude — 강도 (정량·부호). "관계가 크다/작다"
- ✗ "달러와 금은 음의 관계" → ✓ "금은 달러에 **β≈−0.30**, 실질금리에 **−0.23** (다변량 joint, 일별 n≈5000)".
- 우리는 자산 상관을 **공통 거시 팩터 7종**(real rate·dollar·oil·credit·vol·breakeven·fx)으로 분해해 베타로
  magnitude를 잡는다 = factor-implied 공분산.

### (2) Regime 의존성 — "이 국면엔 커지고 저 국면엔 작아진다" ★사용자 최우선
- **gold decoupling = 최고 예시**: 금-주식은 평상시 +0.12 완만한 양상관이나, **변동성 급등 위기(VIX>q99)에선
  +0.29~+0.31로 동조가 오히려 강화**(패닉 셀). "금=안전자산 헤지"를 고정하면 위기 시 분산효과 과대평가.
- 우리 메커니즘 = 거시 국면(Investment Clock 4분면 + 변동성 calm/stress) 확률로 가중한 동적 상관행렬.
- **commodity↔xle는 반대로 regime-stable**(riskOFF +0.666 / riskON +0.635 ≈불변) = 국면 무관 oil 채널.
- ★자문 질문: regime-dependent decoupling을 상관 추정에 반영하는 게 실무 표준인가? 놓친 국면 전환 신호는?

### (3) 조건부성 — "단독으론 보이는데 통제하면 사라진다" ★방법론 함정
- **MOVE/slope drop**: 채권변동성(MOVE)·금리커브 기울기가 univariate론 유의(MOVE us −0.21)했으나, VIX 동시
  통제한 joint에서 **β→0 붕괴**(VIX가 risk-off 분산 흡수=이중계상). → univariate 신호를 공분산 prior에 안 박음.
- **반대 생존 예**: breakeven(기대인플레)은 univariate +0.33 → joint +0.117로 약화돼도 t=3.1 생존=structural.
- ★자문 질문: 통제 누락한 공통 인자는? 반대로 과도하게 버린 신호는?

### (4) 통계 신뢰도 — "표본 작아 방향만 안다" ★crypto 교훈
- **crypto 20-cell**: regime별 MVRV 신호 raw IC −0.065~−0.653(음 일관)이나 **자기상관 보정 eff_n<30 전 cell +
  Bonferroni(α/16) 후 생존 0 = 개별 비유의** → "방향성 약 prior"만, magnitude 점추정 금지, 배분 차단.
- ★이걸 빼면 자문이 우리를 과신 시스템으로 오해. n·eff_n·p·다중비교 보정을 명시.

---

## 2. ★관계 카탈로그 — 바로 둔갑할 원천 데이터 (실측, 코드에서 추출)

> 다음 세션은 이 표를 §1 4축 문장으로 옮기면 자문 자료 완성. 출처=`cross-regime-ledger.md`+`factor_betas_seed.py`.

### 2.1 Cross-asset 상관 (자산↔자산, 공유 factor channel) — 전부 adopted, n수천, p<1e-44
| 페어 | 상관 r | channel | 특이 |
|---|---|---|---|
| 경기민감주↔해외주식 | +0.838 | vol+dollar | VIX 통제 후도 +0.644 잔차(vol만이 아님) |
| 경기민감주↔리츠 | +0.686 | vol | partial +0.459 |
| 원자재↔에너지(XLE) | +0.650 | oil | ★regime-stable(off+0.666/on+0.635) |
| 방어주↔경기민감주 | +0.697 | vol | 방어주도 vol β −0.66 강노출(방어≠무관) |
| 금↔원자재 | +0.367 | dollar | 둘 다 달러 음노출 공통 |
| 금↔해외주식 | +0.189 | dollar>vol net | 달러 채널이 vol 분기보다 우세 |
| 금↔경기민감주 | +0.119 | dollar | 약 양. ★"risk-off hedge" 라벨은 기각(§2.4) |

### 2.2 Factor β (자산↔거시팩터, joint multivariate n≈5000, 2006~2026, MAX VIF 1.26)
| 자산 | real(실질금리) | dollar | oil | vol(VIX) | breakeven | 비고 |
|---|---|---|---|---|---|---|
| 금 | **−0.23** | **−0.30** | +0.11 | ≈0(β:=0 lock) | −(reject) | real=보유 기회비용·dollar 가격채널 |
| 경기민감주 | +0.06(rej,OOS flip) | −0.17 | ~0 | **−0.70(risk-off 최강)** | +(rej) | vol 지배 |
| 해외주식 | +0.08(rej) | **−0.30** | +0.05 | −0.65 | — | dollar+vol |
| 리츠 | ~0 | −0.10 | ~0 | **−0.58(주채널)** | — | vol 주도 |
| 원자재 | ~0 | −0.19 | **+0.60(본체)** | −0.15 | **+0.12(structural)** | oil 본체+inflation hedge |
| 방어주 | (HOLD=미측정→equity vol pool ≈−0.63) | | | | | batch 미포함 |
| fx(환) | 전 자산 +1.0 (denomination=USD자산 KRW 환노출, 측정값 아닌 회계 구조값) |

- tier: **validated**(t 강건)=박제 / **structural**(방향만·넓은CI)=강수축 / **reject**(β:=0) / **hold**(미측정 pool).
- ★real은 gold/bond 전용(equity real은 in-sample 유의해도 OOS sign-flip→reject). breakeven은 commodity 전용.

### 2.3 Regime-conditional (국면 조건부)
- **신규 주문(DGORDER) → 에너지(XLE) forward IC=+0.42** [.16,.62] n=97, **고인플레 국면에서만**. full-sample +0.31
  이미 유의 → 국면이 신호를 *sharpen*(생성 아님). m=40 Bonferroni 유일 생존. = "선행지표가 특정 국면에서
  예측력 강화" 예시.

### 2.4 기각 가설 (관계는 살아도 특정 라벨/기능은 기각) — ★누락 방지의 핵심
- **금 = 위험자산 헤지(부의 공분산)**: 기각. tail(VIX>q99)서 금↔주식 +0.29~+0.31 = 패닉일수록 동조(panic-sell).
  관계 자체(+0.12)는 adopted, "clean hedge 라벨"만 기각.
- **금 vol 노출**: corr(gold,ΔVIX)=−0.049 **p=0.077 비유의** → β:=0 lock(equity-vol pool β −0.51 오염 방어).
- **MOVE/slope factor**: univariate 유의 but joint VIX흡수→0 = 이중계상으로 drop.
- **funding(SOFR−EFFR)**: uncond 비유의, stress 한정 +0.19 약신호 → rejected_provisional(repo발작 시 부활).

### 2.5 자산 내부 지표 (학술 theory 기반, indicator-ledger.md — adopted 71 / candidate 54 / 8자산)
- 예(commodity): roll_yield 0.2(Theory of Storage), basis_momentum 0.15(Bakshi-Gao-Rossi 2019),
  convenience_yield·days_of_supply 0.1(Working 1949), cross_sector_corr 0.05(Tang-Xiong 2012 financialization),
  real_rate 0.1, indpro_yoy 0.15. **candidate**(미채택): china_credit_impulse, cfnai, vix_level, mm_net_long_oi 등.
- ★각 지표에 학술 출처 + weight + 실측 사유 박제. **누락 지표 자문 피드백은 이 ledger와 대조**(§4).

---

## 3. 둔갑 사전 — 코드어 → 투자 개념어 (식별자 전부 제거)
| 코드 | 일반론 번역 |
|---|---|
| factor-implied covariance B·Λ·Bᵀ | 자산 수익률을 공통 거시 팩터로 분해한 상관 추정 |
| RegimeGlasso belief-mix Σ_eff | 거시 국면 확률로 가중한 동적 상관행렬 |
| SEED β / SEED_CELLS / tier | 자산별 팩터 민감도(베타) 사전추정 + 신뢰도 등급 |
| gold vol β:=0 lock + decoupling | 금-위험자산 상관의 위기국면 붕괴(안전자산 전환) |
| MOVE/slope joint β→0 | 다른 변수 통제 후 증분 없는 중복 신호 제거 |
| Investment Clock 4분면 | 성장·인플레 2축 국면(reflation/recovery/overheat/stagflation) |
| fx denomination β=+1.0 | 자산 표시통화 환노출(측정값 아닌 회계 구조값) |
| belief-conditional dynamic cov | 거시 view(stance)가 있을 때만 배분에 반영되는 조건부 상관 |
| rejected_provisional / eff_n<30 | 표본 부족·국면 한정 잠정 보류(부활 가능) |

---

## 4. 누락 지표 피드백 처리 (자문이 "이거 빠졌다" 하면 — ★무비판 추가 금지)
1. **ledger 대조**: `indicator-ledger.md`+`cross-regime-ledger.md`에서 이미 검토했는지 확인.
2. **rejected면 사유 타당성**: PIT-corrupt/spec-code drift/이론 기각=`rejected_permanent`(배제 유지). 표본부족·
   국면한정·일시 파탄=`rejected_provisional`(재평가 트리거 확인→자문이 그 조건 충족 새 근거 줬으면 탐구 가치).
3. **미검토(신규)면**: 기존 내용 확인하며(중복·이중계상 여부) §1 4축 실측 후 15축 audit(crypto처럼). 점추정 금지.
4. **결과 ledger 기록**: 배제 유지 / 신규 탐구 큐 (재탐구 0 원칙).

---

## 5. ★둔갑 완성 샘플 (이 톤으로 옮기면 됨)

**[금]** — *"금은 실질금리에 약 −0.23, 달러에 −0.30 베타의 음의 민감도를 갖는다(15년 일별 다변량). 실질금리는
보유 기회비용, 달러는 가격 표시통화 채널. 인플레 헤지로 유가에 +0.11. ★단 위험자산과의 관계는 국면 의존적
이다 — 평상시 주식과 +0.12 완만한 양상관이나, 변동성이 급등하는 위기(VIX 99분위 초과)에서는 +0.29~+0.31로
동조가 오히려 강해진다(패닉 셀). 따라서 '금=안전자산 헤지'를 무조건 신뢰하면 위기 시 분산효과를 과대평가한다.
우리는 변동성 민감도를 0으로 고정하고 국면별 디커플링을 별도 모니터한다. → 질문: 이 비대칭(평시 분산↔위기
동조)을 상관 추정에 반영하는 게 표준인가? 우리가 놓친 안전자산 국면 신호는?"*

**[원자재]** — *"원자재는 유가에 +0.60(본체), 달러에 −0.19, 변동성에 −0.15 베타. 기대인플레(breakeven)에 +0.12로
약하지만 다변량 통제 후에도 생존(structural). 에너지 섹터와는 국면 무관하게 +0.65로 안정 동조(공유 oil 채널).
내부적으로는 재고(convenience yield·days of supply, Working 1949)와 롤수익(Theory of Storage)을 핵심 신호로
본다. → 질문: 우리가 financialization(투기자금 유입 시 섹터 간 상관 동반 상승, Tang-Xiong 2012)을 후보로만 두고
미채택했는데, 이 국면 신호를 빼는 게 맞나?"*

**[방법론 메타]** — *"우리는 단변량으로 유의해도 공통 인자 통제 후 증분이 없으면 채택하지 않는다(MOVE/금리커브
기울기를 VIX 통제 후 베타 소멸로 제외). 소표본 국면 신호는 자기상관 보정 유효표본·다중비교 보정 후에만 확정
진입시킨다(암호자산 국면 신호는 방향 일관하나 유효표본<30·보정 후 비유의라 잠정 보류). → 질문: 이 채택 게이트가
과도하게 보수적인가, 아니면 빠진 엄격성이 있나?"*

---

## 6. 자문 framing 조언 (사용자 질문 "투자 의사결정이라 생각하고 봐달라?")
- **Yes — CIO/멀티에셋 포트폴리오 매니저 페르소나**: "당신이 멀티에셋 배분 책임 CIO라 가정하고, 아래 거시
  국면→지표→배분 프레임이 (a) 실무 표준에 정합하는지 (b) 빠진 신호·국면·자산군이 없는지 평가하라. 코드/구현이
  아니라 **투자 의사결정 논리**로 봐라."
- 자료 = **자산별 1장(§2.2/2.5) + cross/regime 관계표(§2.1/2.3) + 기각 목록(§2.4)** 압축, 코드어 0.
- gemini-web(참신)+claude-web(실무) **병렬** default. 3~7라운드 수렴.
- ★**우리 강점도 명시**(겸손 과잉 금지): regime-conditional 동적 상관·factor 분해·joint 이중계상 차단·small-n
  rigor(Bonferroni/eff_n)·PIT 엄격성 = 이미 표준 이상. "이미 잘 함" 확인도 방법론 정합 검증의 일부.

---

## 7. 테스트 0번 (거시 파이프라인 과거 설명력) 팁
- **이번 세션 발견**: regime classifier 작동 시작(JM insufficient_data fix → jm_status=ok). 현 분류 **STAGFLATION**
  (growth_z −0.43 / inflation_z 1.15 = CPI yoy 3.0 반등 + 기대인플레 상승). 빌드 빠름(fetch 캐시 255s→29s).
- **predictive 지표만**: 기대인플레·금리커브·신용스프레드·실질금리(forward-looking). 후행지표 제외.
- **PIT 주의(D축 lookahead)**: latest-fallback은 실시간 PIT 안전하나 **백테스트 vintage(NFCI/STLFSI4 revision)
  미반영 = Phase V TODO**. 과거 설명력 볼 때 "발표시점 값 vs 최종개정치" 구분 명시.
- 출력 = 과거 국면 타임라인(reflation/recovery/overheat/stagflation 전환) vs 실제 침체/회복 시점 대조.
- 코드 진입: `core/brain/regime_classifier.py classify(as_of=과거시점)` + `regime_history.build_sleeve_regime_ids`.

---

## 8. [테스트 관련] 1.2 이하 = 참고 (다음 세션 작업 흐름, ★별건 세션)
- **테스트 2번**: 시계열 주입하며 실제 파이프라인 거래 시뮬 → 수익 미발생 시 방법론 vs 코드(상수/가중치) 원인
  분리. **단 그 전에 "결정론 코드를 judge 단계에 활용" 구현 선행 필수**(현 미구현).
- **judge 의문**: 코드 사실 = **claude 최종결정 경로 코드에 없음**(qwen/bge=down-only 감쇠 attenuator a∈[0,1],
  claude 호출 트리거 0). 사용자 의도(claude 최종+qwen 트리거+거시리포트 판단+강화/약화 flag) vs 코드(결정론
  L1/DCF 최종, down-only 증폭 불가) = **큰 gap=judge 재설계 자문 필요**. → 메모리 ckpt-202606020030 참조. 테스트 2 선결.
- **주식(stock.md)**: 초대형. "돌아가는지"만 먼저 vs full 구현 후 일괄 = 사용자 결정 필요. 거시 파이프라인
  (regime·factor·corr_prior) 공유 가능 여부 검토 후 자문 3R.
- **리포트**: 내용 과다→실시간 불가, 사후 모의트레이딩 + 일일 1회 요약/indexing LLM 스폰 또는 grep/bge-DB 검토.
  거시·주식 공통 구조(가설→가점→falsify 회수). 자문 3R.
- ★judge 재설계·주식·리포트 = 각각 별건 세션(사용자 분리 지시). 현 범위 밖.

---

## 9. 진입 (다음 세션)
1. 이 파일(테스트 가이드+카탈로그) → 2. `handoff-e2e-wire-20260602.md`(구현 현황·gold decoupling·factor 7종·
regime·crypto) → 3. `cross-regime-ledger.md`(cross/regime 실측 SSOT)+`indicator-ledger.md`(지표)+자산별
`study_session.yaml`. **첫 작업 = 테스트 0번(거시 과거 설명력) 또는 1번(둔갑 자문) — §1 4축 + §2 카탈로그 기준.**
