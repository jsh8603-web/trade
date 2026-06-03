---
tags: [type/plan, domain/inv, phase/II, track/T3, topic/assumption-lifecycle-v2]
date: 2026-05-29
session: btn-Codlearn
audit: ./.audit-assumption-requests.txt
macro_audit: ./.audit-macro-prompts.txt
refs: [./macro.md, ./quant.md, ./handoff-T3-assumption-integration-20260529.md]
note: 가정 라이프사이클 v2 마스터. 빌드 타깃·6 평가축·최소기준·루프 설계·현 구현맵·3세션 분배·자문 지침. btn-Codlearn 이 SSOT 소유, 최종 통합.
---

# 가정 라이프사이클 v2 — 마스터 설계 + 세션 분배

## 0. 빌드 타깃 (사용자 확정 2026-05-29)

기준(criteria=가정)이 **기간/산업/regime 별로 변동**하는 걸 **학습→기준화→주입→검증→변경→거버넌스** 하는 **라이프사이클 메타레이어**. 3 도메인 **동순위**: 거시(지표 의미·상황정의가 기간별로 변함, 예: 수익률곡선 역전 무력화)·주식(valuation/quant 기준 산업·기간별)·상품(계절성·COT·carry·iNAV 기준 기간별).

**확정 답 (Q1~4)**: Q1 모의계정 API 연결됨 → 닫힌 루프 + **실거래까지**. Q2 3 도메인 동순위. Q3 지표 의미변화 승격 **AND** open-ended regime 발견 둘 다(자문 심화). Q4 판정 고도화 전부 — L1 결정론 + **L2 Qwen + L3 BGE + DCF@agent** 가치확인.

엔진(cheapness_z·valuation DCF·assumption_stats·regime_classifier) 은 이미 존재 → **새 엔진 아님, 통합·확장**.

## 1. 현재 구현 맵 (코드 매핑 증거)

| 도메인 | 완성 | 실재 | 빠진 것 |
|---|---|---|---|
| 주식 | ~70% | cheapness_z·archetype5·valuation.py(DCF 실재)·seed→bitemporal→l1→consensus→ledger | shadow-only, DCF=legacy/shadow, 판정=결정론만 |
| 거시 | ~40% | regime_classifier(고정-K4)·macro_indicators·**indicator_event_correlation(지표의미변화 6 static case)** | 6 case 정적(학습/버전드X)·regime 자동수정X·open-ended 발견X |
| 상품 | ~5% | sleeve 가중 라벨만 | carry/계절성/COT/재고/iNAV 코드 0 |
| 통합 `core/assume/` | 0% | — | Card/Registry/Validator/UpdateController 전무 |
| 통계엔진 | ✅ | assumption_stats·detectors·online_fdr(메모리) | online_fdr 영속X |
| data계약/lineage | 0% | — | data_contract·lineage·영속 = 설계만 |
| d4_book | 골격 | 구조 | 데이터 미연동·to_context 미소비 |
| 판정 L2/L3 | ~5% | BGE embedder(메모리유사도만) | 싼지/비싼지 LLM 판정 미연결 |

## 2. ★ 6 평가축 + 최소 달성 기준 (btn-Codlearn 정의 — SSOT)

> 사용자 4축(학습/기준화/주입/변경) + D(검증)·F(거버넌스·안전) 추가. **각 축 × 3 도메인 = 완성 grid. 최소기준 = 각 셀 v1 wired.**

- **A 학습 (Learn from outcomes)**: 모든 결정(매수/매도/포트폴리오조정/거시판단)을 trigger 된 가정 id+version 과 함께 PIT-safe log → 실현 결과 join → "이 기준이 이 기간/regime/산업에서 맞았나" 조건부 측정. **min**: 결정 1건 → 근거 가정 역추적 + 결과 라벨 100%, 3 도메인.
- **B 기준화 (Encode as versioned assumption)**: AssumptionCard(falsification_metric 필수=반증불가 진입금지)·scope(기간/산업/regime/domain)·bitemporal 버전. macro 지표 의미도 카드化(6 static case 승격경로). **min**: 3 도메인 각 ≥1 카드 closed-loop 통과.
- **C 주입 (Inject into decision)**: 활성 가정 → derivation → 판정 = **L1 결정론 floor + L2 Qwen(맥락) + L3 BGE(유사사례) + DCF@agent(가치확인)** + 신뢰도→band→사이징 + 모의→실거래 gate. **min**: 결정 1건이 4 판정요소 통과 + 신뢰도 사이징 반영.
- **D 검증 (Validate continuously)**: assumption_stats regime-conditional holds + online-FDR 다중검정 + data_contract(측정깨짐≠가정틀림) + prequential. **min**: 가정별 holds_now + alpha-wealth 영속.
- **E 변경/은퇴 (Change/Retire)**: AND-gate(FDR∧효과∧dwell∧K∧regime) + base-layer 사람비준 + ATMS 의존전파(무효화·epoch·DAG비순환·nogood) + orphaned position managed-exit + decay/half-life. **min**: 가정 기각 시 의존 가정 stale + 의존 포지션 플래그.
- **F 거버넌스·안전 (Govern/Safe-for-live)**: lineage PIT 재현 + evidence card + kill-switch 우회불가 + shadow→live 사람 게이트 + 모의 먼저·실계정 사람비준. **min**: 임의 as_of 결정 재현 + 실거래 진입 사람 게이트. (Q1 실거래라 필수)

## 2.1 ★ 각 축의 달성 목적 (학습→정의전환 흐름 관점, 사용자 확정)

> **핵심 흐름**: 지표 → 그 지표로 **상황(정의)** 읽기 → **특정 지표가 정의대로 안 따라가는 상황** 감지 → "그 기간엔 상황이 정의 S 가 아니라 **다른 정의 S' 로 바뀌어야 함**"을 학습 → 기준 조정 → 재적용. **거시·주식·상품 동일 흐름(지표만 다름).** 축은 이 흐름에서 각자의 목적을 달성해야 함 (코드는 수단).

- **A 학습** — 목적: "지표가 현재 정의대로 **안 따라가는 순간**"을 결정·결과 기록에서 감지·학습.
  - 거시: 수익률곡선 역전인데 침체 안 옴(QE 왜곡) → "이 기간엔 역전=침체 정의가 깨짐" 학습.
  - 주식: 저PER인데 안 오름(공정전환기 PER 착시). 상품: COT 극단인데 평균회귀 안 함(공급과잉 regime).
- **B 기준화** — 목적: 학습한 "**정의 + 그 정의가 깨지는 조건(보조지표)**"을 반증가능·버전드 기준으로 명문화. "지표 X → 상황 S, 단 보조지표 Y 임계 넘으면 S'" 카드화. 새 상황정의 발견 시 새 카드 승격.
- **C 주입** — 목적: **현재 활성 정의**를 실제 판정·결정에 적용. "지금은 상황 S' 이니 지표 X를 이렇게 해석" → L1 floor + L2 Qwen + L3 BGE + DCF@agent + 사이징.
- **D 검증** — 목적: 적용 중인 정의가 **여전히 유효한지 지속 측정**(regime별 holds + online-FDR). **정의틀림 vs 측정깨짐 분리**.
- **E 변경/은퇴** — 목적: 검증이 "정의 안 맞음" 충분히 입증 시 **정의 S → S' 전환**(또는 새 정의 승격). 의존 기준 전파. AND-gate 충분조건 + base-layer(거시상황·regime) 사람비준.
- **F 거버넌스·안전** — 목적: 정의 전환이 **실거래에 안전 반영**. 전환 이력 PIT 재현·감사, 정의 바뀌어 근거 잃은 포지션 처리(managed-exit), 실거래 진입 사람게이트.

→ 이 6 목적이 **닫힌 루프**: A 감지 → B 명문화 → C 적용 → D 검증 → E 전환 → (F 안전) → A. plan §2 최소기준 = 각 목적의 v1 통과선.

## 2.2 산업군/기간별 학습 명시 (사용자 확인) + 자문 R1 반영

**확인 — 3도메인 모두 산업군/기간 학습 포함**:
- **거시 기간별**: §2.1 흐름(지표→상황정의→기간별 정의 전환) + decoupling-case(기간조건부 의미) + BB-1(6 case 버전드)/BB-3(open-ended regime=신규 기간정의).
- **주식 산업군×기간**: CL-5 + R3 + AssumptionCard scope(sector×period×regime) + d4_book IndustryCharCard(기간별 산업특성, 공정전환기 PER) + archetype 시변(valid_from).
- **상품 기간별**: BB-5/S21 commodity archetype(계절성=기간주기, carry/COT=regime별) + R4.

**자문 R1 (gemini-web + claude-web Opus4.8) 반영** — topology 수렴, claude 가 안전 디테일 정정. raw=`.consult-R1-gemini.txt`·`.consult-codlearn-R1.txt`:
- 조건화 = 단순 regime×archetype×period **cross 금지(차원의 저주/데이터 희소)** → **계층적**: regime 최상위 → archetype 매핑, period=regime 인스턴스로 취급. (gemini)
- **Card 통합(A안) 채택**: baseline→trigger→override(decoupling) 인과구조 통일해야 ATMS 단일 엔진. context/falsification_metric = generic(JSON). (gemini)
- **★gate 비대칭(claude 정정)**: adopt(채택/변경)=conjunctive AND-gate(slow) / **retract(기각)=hard-falsifier disjunctive(fast) 분리**. 같은 gate 로 기각하면 반증된 가정이 dwell/K 채울 때까지 live 노출 = 치명.
- **판정 경계(claude 정정)**: L1=상대축(cheapness_z)=sizing / DCF=절대축(내재가치)=pure kill, **둘 결합(가중합) 금지**, disjunctive veto. **L2/L3 = strictly attenuating-only**(confirm 아님): `final=L1_size*a2*a3`, a2/a3∈[0,1], monotone-down → LLM safe-by-construction. fail-open=L1-fallback(a=1.0), abstain≠fallback.
- **alpha-wealth per-domain 격리(claude)**: FDR pooling 시 noisy commodity 가 macro 발견 starve → domain/family 단위 wealth pool (위상은 단일 ATMS).
- **base-layer 변경(claude)**: 즉시 retraction 아니라 **re-derivation + shadow/canary cutover**(old 계속+new 그림자 병행→안정후 전환). gate=bool 아니라 (pass, evidence, cost-to-flip).
- ★**진짜 first break(claude 정정)** = **재주입 반사성(reflexivity)** — gridlock 은 가시적·하류일 뿐. 학습기가 자기 결정으로 오염→self-confirming attractor. 방어=frozen control book + off-policy(IPS) 로깅 + 도메인 state/weight 격리. (gemini 의 grace+lazy 는 §4.1 soft 전파에 유지, 단 cascade 폭주가 핵심 위험은 아님.)

## 3. 학습·판정 루프 초기 설계 (closed loop)

```
[결정] 가정→derivation→판정(L1+L2+L3+DCF)→사이징→주문(모의→실)   ← 축C
   │  (가정 id+version+근거 PIT log)                              ← 축A·F lineage
   ▼
[기록] decision_ledger(freeze) + 결과 대기                        ← 축A·F
   ▼ (시간 경과, 실현 outcome 도착)
[학습] outcome join → "기준 맞았나" regime/기간/산업 조건부 측정    ← 축A·D
   ▼
[검증] assumption_stats(regime-conditional holds) + online-FDR    ← 축D
   ▼
[변경] AND-gate 통과? → 가정 수정/기각(cap·hysteresis)            ← 축E
   │   base-layer(regime/지표의미)=사람비준 / 일반=자동
   ▼
[전파] ATMS 무효화 → 의존 가정 stale + orphaned position 플래그    ← 축E·F
   ▼
[재주입] 갱신 가정 → 다음 결정                                     ← 축C (루프)
```

3 도메인 동형: 거시(지표→상황 정의 가정), 주식(산업·기간 valuation 가정), 상품(계절성·carry 가정).

## 3.5. ★ 통합 method — 거시가 template (사용자 확정: 주식/상품도 이 방식)

**reference 구현 = `core/brain/indicator_event_correlation.py`** (6 ANOMALY_CASES, 근거 MACRO_CORRELATION_BACKGROUND.md). 이게 사용자가 논의한 거시 x,y 사례의 코드화.

**일반 패턴 (3 도메인 동형)**:
```
맥락 C (event/industry/regime + 기간) 에서
  지표/메트릭 M 의 baseline 의미 = 방향/임계 D
  UNLESS 보조지표 S 가 임계 넘으면 → 의미 깨짐(decoupling) → attenuation/재정의
  ← falsification_metric: decoupling 이 실제 성립하나 (반증가능)
  ← correction record 로 학습 (실시간 판정 vs 사후 정답 → 빈도/lag → 재보정)
```
- **거시**: C=거시이벤트, M=수익률곡선/Sahm/M2/CPI, decoupling=QE왜곡/이민충격/IOER 등 6 케이스.
- **주식**: C=산업×사이클기간, M=PER/EV-EBITDA, baseline=저멀티플=싸다, decoupling=공정전환기 PER 일시상승(반도체).
- **상품**: C=원자재×계절/재고regime, M=COT순롱/carry, baseline=극단=평균회귀, decoupling=공급과잉 regime.

**현 상태 / 빌드**: 거시 모듈 실재하나 (a) **live 루프 미연결**(ingest_correction/recall_similar dead, FINDINGS §1 D2 "WRITE/recall dead") (b) **6 케이스 정적**(AssumptionCard 아님, 학습/버전드/신규발견 불가). → 빌드 = 이 AnomalyCase 패턴을 **AssumptionCard 로 일반화 + 학습루프 live 연결 + 케이스 학습/버전드/발견가능 + 주식·상품 복제 + bnpy open-ended regime 발견(D1)**.

**축 매핑**: AnomalyCase=축B(기준화) / correction record loop=축A(학습) / conditional_attenuation 주입=축C / decoupling 성립 검증=축D / 신규 케이스 발견+사람비준=축E / PIT correction mask=축F.

## 4. 3 세션 분배 (각 세션 = 자기 주제 ≤5R 자문 + 축별 미진분 보완)

### btn-Inv (T1, cwd=D:\projects\Inv) — "학습 데이터 기반 + 실거래 안전"
- **소유 셀**: 축A(데이터측, 3도메인 결정→outcome PIT 로그·join) + 축D(data_contract 측정분리) + 축F(lineage PIT 재현·online_fdr 영속) + 상품 **데이터** 소싱(N-T1-COMMODITY-SRC)·panel commodity 컬럼.
- **구현**: `core/data/data_contract.py`(Pandera)·`lineage.py`(OpenLineage jsonl)·`online_fdr` 영속(AlphaWealthState)·pit_query 합성함수·panel_schema 확장. + **모의계정 API→outcome 수집 파이프** + shadow→live 데이터 경로.
- **자문 주제**: PIT-safe 결정log→outcome→학습 데이터 파이프라인 + data contract + 상품 무료 데이터소스 + 실거래 안전 연결.

### btn-button (T2, cwd=D:\projects\button → **먼저 `cd /d D:\projects\Inv`**) — "거시 학습 + 검증·판정 통계"
- **소유 셀**: 거시 축A/B(지표 의미변화 학습 + 6 static case 승격 + **open-ended regime 발견 D1**) + 축D(regime-conditional 검증 엔진 확장) + 판정 통계(L2/L3 입력) + 상품 검증 통계(carry/계절성 detector).
- **구현**: indicator_event_correlation 6 case → 버전드 가정 승격 경로 + `regime_discovery`(BOCPD novelty, 발견자동·승격사람) + commodity archetype(carry/seasonal) + T2-7 재검증.
- **자문 주제**: 거시 지표 의미가 기간별로 변하는 걸 학습·버전화 + open-ended regime 발견(HDP-HMM/BOCPD) + regime-conditional 검증 + 판정 통계.

### btn-Codlearn (나, T3) — "라이프사이클 오케스트레이션 + 주식/상품 기준 적응 + 판정 레이어 + 통합"
- **소유 셀**: 축B/C/E core(`core/assume/` Card/Registry/Validator/UpdateController) + 주식·상품 기준 적응 + 판정 레이어(L1+L2 Qwen+L3 BGE+DCF@agent) + orphaned/decay + **전 세션 최종 통합**.
- **구현**: S14~S20 + S22 judge + valuation DCF wire + closed-loop test.
- **자문 주제**: 라이프사이클 오케스트레이션 + cross-domain 기준 적응 + 판정 4요소 결합 안전경계 + 주입 정합성.

## 5. 각 세션 자문·보완 지침 (공통)
1. 자기 주제로 `/gemini-web` + `/claude-web` **병렬 ≤5 라운드**. 중요치 않은 상세만 나오면 조기 수렴 종료. 직접 리서치 허용.
2. 매 라운드 = 자기 소유 축×도메인 셀의 **미진분** 보완 방향 도출. 자문 raw 는 `D:\projects\Inv\.consult-{sess}-Rn.txt` 저장.
3. 보완 결과 = 설계 문서(`DESIGN-{sess}-v2.md`) + 구현. self-test 필수.
4. 완료/막힘 시 **btn-Codlearn 에 psmux 보고** (산출물·계약·미해결). 최종 통합은 btn-Codlearn.
5. 계약 SSOT = 본 문서 §2 6축 최소기준. 위반 시 btn-Codlearn 에 escalate.
