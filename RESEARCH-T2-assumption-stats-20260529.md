---
tags: [type/research, domain/inv, phase/II, track/T2, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-button
task: ./TASK-T2-assumption-research-20260529.md
consults: [.consult-R1-claude.txt, .consult-R1-gemini.txt]
design: ./DESIGN-T2-assumption-stats.md
---

# RESEARCH-T2 — 가정 라이프사이클 검증·변경 통계 prior art 실조사

> 과제: "가정(Assumption) 라이프사이클" = findings·자문·코드에 통째 누락된 축. T2 몫 = 검증통계·regime·구조모델.
> 본 노트 = prior art **적용성 / 이식비용 / 권고** (TASK §2-A). 설계는 [DESIGN](./DESIGN-T2-assumption-stats.md), 통계 코드는 `core/structure/{detectors,online_fdr,assumption_stats}.py` (구현·테스트 완료, 25/25 PASS).

## 0. reframing (두 자문 수렴)
4축(학습/도출/주입/변경) = "거버넌스 하의 belief revision". 세 성숙 분야가 1:1 매핑:
- 고전 AI **ATMS** (의존·전파·철회) / 금융 **SR 11-7** (주기검증·변경통제) / 통계 **online FDR** (스트리밍 다중검정).
- gemini 보강: **SPRT/CUSUM** 순차검정, **DAG topological** 순환방지, **falsifiability** 메타데이터, **confidence sizing**, **Event Bus** 분리.
- ★ 정확히 같은 통합물(assumption registry + governed change + 퀀트 regime-conditional)을 묶은 오픈소스는 없음 → **통합 자체가 기여 영역** (claude B).

## 1. prior art 별 적용성 · 이식비용 · 권고

### 1-A. ATMS (de Kleer 1987, AIJ 28:127–162) — belief revision 직계 조상
- **무엇**: 가정 1급 객체, justification/label, dependency-directed backtracking, **nogood**(동시 참 불가 환경집합).
- **우리 매핑**: AssumptionCard.depends_on 그래프 · 전파 · revival · 충돌의 직계 조상.
- **★ 차용 핵심 (claude A-3)**: 전파 = "재계산" 아니라 **"무효화"**. A 바뀌면 B 값을 A 로부터 재계산하지 말고 B validation 을 stale 마킹 → B validator 를 **데이터에 대해** 다시 돌림. B 의 fixed point 는 A 가 아니라 데이터 → 상호참조 대수루프 원천차단. nogood = "동시 참 불가 가정조합" 등록 → 충돌 선제차단.
- **이식비용**: 낮음. 전체 ATMS 엔진 불필요 — 무효화 전파 + nogood 집합만. DAG 는 networkx 없이 위상정렬 ~30 LOC.
- **권고**: ★ **무효화 전파 + epoch topological single-pass + nogood** 채택. 풀 ATMS justification 재계산은 과함(우리는 데이터가 fixed point라 불필요). **T3 도메인**(DAG/Registry), T2 는 validator 가 stale 재검증을 데이터에 대해 수행하는 계약만 보장.

### 1-B. change-point: BOCPD / CUSUM / BSTS
- **BOCPD** (Adams & MacKay 2007): run-length posterior, **변화점 크기·개수 사전지정 불필요**. → `detectors.Bocpd` 구현 완료(가우시안 NIG 켤레). ⚠️ 단일 step P(cp)≈hazard prior 라 실신호 = **run-length MAP 붕괴**(self-test: 60→1 검증).
- **CUSUM/Page**: 방향·크기 알 때 평균이동 누적합. → `detectors.Cusum` 완료. ⚠️ k=0.5σ 면 노이즈 excursion 도 발화 = **CUSUM 단독 false alarm → AND-gate 필요성의 직접 근거**.
- **SPRT** (Wald, gemini): H0(가정 성립) vs H1(깸) 로그우도비 순차검정. → `detectors.Sprt` 완료(n=3 에 빠른 판정).
- **BSTS**: Bayesian Structural Time Series — 무겁고 pymc 의존, **후순위**(v2).
- **이식비용**: 낮음(numpy-only 구현 완료). ruptures 미설치라 자체구현, 대신 stream 친화적.
- **권고**: ★ rule_observer 의 PSI/PageHinkley 와 **공유 `detectors.py` 모듈로 통합**(claude D-6 중복제거). 대상만 다름(가정 예측량 잔차 vs rule 출력 divergence). 모수가정=CUSUM/BOCPD/PSI, 구조가정=prequential+BOCPD run-length.

### 1-C. prequential principle (Dawid) — 가정=forecaster
- **무엇**: 가정을 forecaster 로 보고 예측을 **시간순 채점** → 누적 손실곡선 꺾임 = 증거. purged WF 와 철학 동일.
- **우리 매핑**: 구조가정("PER 은 공정주기를 탄다") 의 멀티플 수준 예측력을 시간순 채점.
- **이식비용**: 매우 낮음. → `detectors.prequential_loss` 완료. ⚠️ kink 판정은 **비율(2배)+outcome 분산 대비 절대 floor** 로(정상 메커니즘 noise 오발화 차단 — 초기 구현에서 발견·수정).
- **권고**: ★ 구조가정 검증의 주 신호. estimand 분리 준수 — 멀티플 *수준* 설명력이지 forward return 예측 아님(T2-2).

### 1-D. SR 11-7 (Fed/OCC 2011) — 모델리스크 거버넌스
- **무엇**: 모델 근본 가정의 **문서화·주기검증·변경통제** 규제표준. champion-challenger = 우리 Proposer-Challenger-Arbiter. ongoing monitoring + outcomes analysis + change control = Registry+Validator+UpdateController.
- **우리 매핑**: `core/rules/consensus.py` ProposerChallengerArbiter + promotion gate(G0~G6) 와 거의 1:1.
- **이식비용**: 0 (개념 프레임). 코드는 consensus.py 재사용.
- **권고**: ★ 철학적 기반으로 채택. 가정 변경은 consensus 엔진을 **객체타입 파라미터화로 재사용**(fork 금지, claude D-5) 하되 **caps 더 빡세게**(높은 dwell-time, 엄격 online-FDR). "champion-challenger" 용어 정렬.

### 1-E. online FDR (Javanmard&Montanari 2018; Ramdas et al. 2017) — ★ TOP 우선순위
- **무엇**: 스트리밍 다중검정. alpha-wealth 로 각 검정이 예산 소모, 기각 시 일부 회수 → 끝없이 재검정해도 noise 추격 차단. LORD++/SAFFRON/ADDIS/alpha-investing.
- **우리 매핑**: 가정 여러 개 × 연속 모니터링 = **시간·가정 다중검정**. G1 batch BH 는 고정 family 가정이라 스트리밍에 **틀림**.
- **★ = 사용자의 "합리적 이유 없이 자주 바뀌면 안 됨" 의 유일한 수학적 보장** (claude TOP-1).
- **이식비용**: 낮음(R onlineFDR 참조, numpy 재구현). → `online_fdr.LordPlusPlus` + `AlphaInvesting` 완료. self-test: null 500→기각 0, 강신호 20→20, **죽은가정 50회 재검정+막판 운좋은 p=0.04 → wealth 고갈로 차단**(부활 함정 방어).
- **권고**: ★★★ 즉시 도입. AND-gate 첫 조건. **부활(claude C)** = 비대칭 hysteresis(채택보다 높은 증거) + 재검정도 alpha 예산 소모.

### 1-F. 사이징 — fractional/shrunk Kelly + confidence
- **무엇**: 가정 posterior/CI(신뢰도)를 베팅규모 페널티/부스터로. 점추정으로 떨구면 정보 버려짐.
- **우리 매핑**: cheapness_z 류 threshold 가 점추정 아닌 **band 상속**, 신뢰도 낮음→넓은 band→작은 포지션/abstain.
- **이식비용**: 낮음. → `assumption_stats.confidence_to_band` + `band_to_size_multiplier` 완료(abstain 임계 포함).
- **권고**: ★ Card 에 posterior/CI 1급 보유. L1 gate/Portfolio Optimizer 가 신뢰도 배수 소비. **T2 가 band·배수 산출, T3/L1 이 사이징 wire**.

### 1-G. 보조 MLOps 도구 (참조용, 직접 의존 X)
- Great Expectations/Soda/Pandera/Deequ = **data contract** 층 (claude C-측정: "가정 틀림" vs "측정 깨짐" 분리). AssumptionValidator **앞단** 게이트.
- Evidently/NannyML/Alibi-Detect/whylogs = drift 알고리즘(KS/MMD/Mahalanobis) 참조. 바닥 수학 재구현 회피용 — 단 우리 detectors.py 가 이미 충분.
- OpenLineage/Feast/MLflow Model Registry(stage/alias=champion/challenger) = lineage/provenance 표준. seed.derived_from 체인 → 표준 lineage 이벤트(T3 derivation seam).

## 2. 빠뜨린 축 (자문이 추가 식별 — 설계 반영)
- **C-meta (regime base-layer)**: 모든 조건부 가정이 regime 분류기 의존 → 그게 거버넌스 밖이면 토대 붕괴. **regime 모델 = 명시적 base-layer 가정**(더 보수적·사람 소유·**자동변경 금지**). → `assumption_stats.hysteresis_and_gate(is_base_layer=True)` = 자동승격 영구 차단.
- **C-안전 (orphaned position)**: 가정 기각 시 그 가정에 의존하던 open position = thesis 증발. rule_version 은 얼리되 의존 포지션을 **review/managed-exit 플래그**(조용히 보유 금지). emergency_stop 연결. **→ T3 도메인**(안전정책), T2 는 AssumptionInvalidated 시 의존 포지션 list 산출 계약 제공.
- **C-측정**: data contract 게이트가 validator 앞 (측정 incident ≠ 가정 틀림).
- **C-효용**: 통계 holds ≠ 경제 holds → ledger 실현 utility/기회비용 loss-weighted(불변식④).
- **C-반사성**: 가정 decay/half-life 1급 속성(엣지가 차익거래로 자기소멸).
- **falsifiability (gemini C-1)**: 등록 시 kill_condition 의무. 반증불가 서사가정은 진입 금지 → AssumptionCard ≠ IndustryCharCard(서사, L2 soft 전용, claude D-★).

## 3. 종합 권고 (우선순위)
1. ★★★ **online FDR (LORD++)** — "자주 바뀌면 안 됨" 수학적 보장. G1 batch BH 로는 불가. **구현 완료**.
2. ★★★ **regime 모델 base-layer 가정 승격** — 안 하면 전 조건부 검증이 모래 위. AND-gate is_base_layer 차단 **구현 완료**.
3. ★★★ **orphaned position 정책** — 실거래 안전 공백. **T3 도메인**, T2 는 의존 list 계약.
4. ★★ **kind dispatch + regime-conditional 검증** — pooled 금지. **구현 완료**.
5. ★★ **공유 detectors 모듈 + 무효화 전파(ATMS)** — 중복제거 + 대수루프 차단.

> ATMS 논문 + SR 11-7 직접 읽을 가치(claude). 본 노트는 회수 가능 범위로 적용성 판정 — 추가 심화 필요 시 자문 라운드 2.
