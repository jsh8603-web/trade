---
tags: [type/task, domain/inv, phase/II, track/T2, topic/assumption-lifecycle]
date: 2026-05-29
from: btn-Codlearn (T3 통합)
to: btn-button (T2 구조모델·regime)
ref-consult: [.consult-R1-gemini.txt, .consult-R1-claude.txt]
note: 가정(Assumption) 라이프사이클 — 검증·변경 통계 + regime-conditional 설계 과제. 코드 일부 X, 리서치+설계 깊이 요구.
---

# TASK(T2) — 가정 라이프사이클: 검증·변경 통계 + regime-conditional 설계

## 0. 배경 (왜 이 과제인가)
사용자가 한참 논의했으나 findings·이전 자문·코드에 **통째로 빠진 축** = **"가정(Assumption) 라이프사이클"**.
- 산업/자산별 가정 표(예: "변동성 X구간 → 임계값 θ", "반도체 공정주기 PER 일시상승") → 보고서/누적 데이터로 **주기적 검증** →
  seed 기준 **도출** → 지표 연결 → 틀리면 **변경**(너무 자주 X + 합리적 이유 누적 데이터 설명) → 변경 시 **의존 가정 재평가**.
- ★ scope = **거시(레짐-지표) / 주식(섹터·종목 valuation·산업특성) / 상품(ETF·원자재)** 3 도메인 전부.
- 기존(structure_model/archetype/consensus)은 rule/signal 레이어. 그 위 **가정 레이어** 부재.

⚠️ **사용자 명시 불만**: "기존에는 코드 일부만 만들고 끝냈네." → **prior art 실제 조사 + 깊은 설계 고민 + 통합 방안**까지. 스텁만 금지.

## 1. 먼저 읽을 것 (외부 자문 2건 — 반드시 정독)
- `D:\projects\Inv\.consult-R1-claude.txt` (claude-web — **핵심**. ATMS / SR 11-7 champion-challenger / online FDR / regime-conditional 검증 / 구조 vs 모수 가정 dispatch / change-point / hysteresis AND-gate / 신뢰도→사이징 / orphaned position 안전 / derivation seam)
- `D:\projects\Inv\.consult-R1-gemini.txt` (gemini-web — SPRT/CUSUM, DAG topological, falsifiability metric, confidence sizing, Event Bus 분리)
- 우리 코드: `core/structure/structure_model.py`, `core/structure/archetype.py`, `core/rules/consensus.py`, `core/observability/rule_observer.py`

## 2. T2 도메인 = 구조모델·regime·검증통계. 리서치 + 설계할 항목
### 2-A. prior art 실제 조사 (적용 가능성·이식 비용 판정)
1. **belief revision 고전 — ATMS** (de Kleer 1987, *AIJ* 28:127–162): 가정 1급 객체·의존·전파·철회·nogood(모순 환경). 우리 depends_on 그래프·전파·revival·충돌의 직계 조상. 무엇을 차용?
2. **change-point**: BOCPD(Adams & MacKay 2007, run-length posterior, 크기 사전지정 불필요), CUSUM/Page, Bayesian Structural Time Series. 우리 rule_observer PageHinkley/PSI 와 어떻게 통합(공유 detectors 모듈)?
3. **prequential principle** (Dawid): 가정을 forecaster 로 보고 예측을 시간순 채점 → 누적 손실곡선 꺾임 = 증거. purged WF 와 철학 동일. 구현 형태?
4. **모델리스크 거버넌스 SR 11-7**: champion-challenger(=우리 Proposer-Challenger-Arbiter), ongoing monitoring+outcomes analysis+change control. 우리 promotion_gate/consensus 와 매핑.
5. **사이징**: fractional/shrunk Kelly — 가정 posterior/CI(신뢰도)를 베팅규모 페널티/부스터로.

### 2-B. 설계 고민 (검증·변경 통계 핵심)
1. **구조가정 vs 모수가정 dispatch** (claude-basic A-0):
   - 구조("반도체 PER은 공정주기를 탄다") → "메커니즘 여전히 작동?" = regime detection.
   - 모수("섹터 정상 멀티플=[12,18]", "변동성 H구간 임계값=θ") → "추정 안정?" = drift/change-point.
   - AssumptionCard.kind = structural|parametric 로 validator dispatch (archetype dispatch 패턴 재사용).
2. **regime-conditional 검증** (claude-basic A-1 핵심 누락): pooled 검증 금지. ValidationReport 는 **레짐 라벨 동반**, holds 는 레짐별. 레짐 A서 참·B서 거짓인 조건부 가정 오판 방지.
3. **regime 모델을 base-layer 가정으로 승격** (claude-basic C-meta): 모든 조건부 가정이 레짐 분류기에 의존 → 그게 거버넌스 밖이면 토대 붕괴. regime 모델 = 명시적 base 가정(더 보수적·사람 소유·자동변경 금지) = 발산 막는 고정점.
4. **hysteresis AND-gate** (claude-basic A-2): ChangeRequest 승격 = (online-FDR 유의 ∧ 효과크기 material ∧ dwell-time ∧ K-윈도우 지속 ∧ regime 조건부) 전부 통과. consensus.py cap/hysteresis 재사용하되 가정 변경은 더 빡세게.
5. **3 도메인 archetype·검증 확장**:
   - 주식: 반도체 PER 착시(cyclical), 화학/철강/바이오 등.
   - 상품: spread_driven(롤수익률·캐리), 계절성(난방유/곡물), 재고기반 — **신규 archetype/검증 경로**.
   - 거시: 레짐 정의·전이.
6. **신뢰도→band→사이징** (claude-basic C): cheapness_z 류 threshold 가 점추정 아닌 band 상속, 신뢰도 낮으면 넓은 band→작은 포지션/abstain.

## 3. 산출물 (코드 스텁 아님)
1. **리서치 노트** `RESEARCH-T2-assumption-stats-20260529.md`: 2-A 각 prior art 적용성/이식비용 + 권고.
2. **검증·변경 통계 설계** `DESIGN-T2-assumption-stats.md`: kind dispatch + regime-conditional ValidationReport + change-point(BOCPD) + hysteresis AND-gate + base-layer regime 가정 + 신뢰도 band. 코드레벨(파일:함수:계약).
3. **구현 계획**: progress 스텝. T2-7 실데이터 재검증과의 연계 명시.
⚠️ 막히거나 확신 < 80%면 자문 후 진행. 단정 보고 금지.

## 4. 분담 경계
- T2(너) = **검증통계·regime·구조모델**. T1(btn-Inv) = **데이터·PIT·검증입력**. T3(btn-Codlearn, 나) = **AssumptionCard/Registry/Validator/UpdateController + derivation seam + consensus 재사용 + orphaned position 안전정책 통합**.
- 겹치면 btn-Codlearn 에 SendKey 질의. 완료 시 btn-Codlearn 보고.
