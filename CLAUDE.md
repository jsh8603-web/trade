# Inv — 멀티에셋 자율매매 시스템 (Claude 운영 지침)

> 레거시 단일자산 코인봇을 asset-agnostic 코어로 일반화하고, 자산 영역별 **스터디 시스템**(`core/study`)을 얹은 멀티에셋(암호화폐 + 주식) 자율매매 시스템.
>
> **문서 지도** (작업 성격별 SSOT):
> | 무엇 | 어디 |
> |---|---|
> | 사용자용 설명·의존성·실행법·안전장치 | [README.md](./README.md) |
> | 코드 구조·핵심기능·설계의도·디버깅 진입점 | [CODEMAP.md](./CODEMAP.md) |
> | 지표·관계 연구(후보/채택/기각 + 사유) | [study-research/_wire/indicator-ledger.md](./study-research/_wire/indicator-ledger.md) + [cross-regime-ledger.md](./study-research/_wire/cross-regime-ledger.md) |
> | 전체 아키텍처 상세 | [README.md](./README.md) + [ARCHITECTURE-brain.md](./ARCHITECTURE-brain.md) |
> | 레거시 코인봇 커리큘럼·상세(Step0~12) | [docs/legacy-coinbot.md](./docs/legacy-coinbot.md) |

---

## 🧭 운영 기준 — 이 프로젝트에서 작업하는 법

### 작업 성격별 진입점 (필수)

| 작업 | 본다 / 고친다 |
|---|---|
| **지표를 탐구·채택·기각·수정** | `indicator-ledger.md` / `cross-regime-ledger.md`. 신규 지표·신호를 **들여다본 순간 candidate 행으로 즉시 박제**(채택 전이라도) → 재탐구 0. 결론 나면 status·reason·research_ref 확정 |
| **파이프라인·코드를 수정** | `CODEMAP.md` — ⛔ **수정 전 해당 모듈의 '설계 의도' 확인** → 수정 후 **CODEMAP 동기화 의무**(의도·배선상태 갱신) |
| **코드 의도 보존** | 기존 코드 = 의도가 있다. 의도를 **알고** 작업한다. 버그·오류로 **판정**된 경우에만 수정(왜곡 금지). 다른 세션 작업분도 회피 없이 본 세션이 수정 |

### 문제 귀속 L0~L3 (테스트·디버깅)

문제 발생 시 수준을 분류해 원인을 격리한다:

| 레벨 | 정의 | 검토처 |
|---|---|---|
| **L0 배선** | 모듈이 호출/연결 안 됨 (e2e 미연결) | CODEMAP 배선상태 |
| **L1 이론·yaml** | 가설·관계·방향이 틀림 | ledger |
| **L2a 코드 로직** | 계산식 구현 오류 | CODEMAP |
| **L2b 데이터·PIT** | 결측·vintage·lookahead·빈도불일치 | CODEMAP + PIT 레이어 |
| **L2c 파라미터·상수** | 로직·데이터 맞는데 상수 부적합 (예: `MAX_WEIGHT_SINGLE`) | CODEMAP |
| **L3a LLM 계약** | 출력 스키마/형식 파싱 실패 | judge / llm_provider |
| **L3b LLM 판단** | 요약·카드가 의미적으로 틀림 | judge / active_loop |

**판별 방법** (기존 인프라 재사용): `off=byte-identical` 불변식 + per-bar state-vector checksum(SHA256) + golden master + LLM `on/off` golden hash diff. 단계별 checksum divergence로 위치 특정, on/off diff로 L3 격리.

### 안전 경계 / go-live 게이트

- `DRY_RUN` 기본 `true`. 실거래 전환 = **사람 게이트**.
- 한국투자증권(KIS) = **모의계좌 한정**(현). 실서버 전환은 사용자 승인.
- `EMERGENCY_STOP` + `auto_emergency.json` 확인 후에만 매매. `MAX_TRADE_AMOUNT` 초과 금지. 안전장치 값은 사용자 명시 없이 변경 금지.
- `off=byte-identical` 불변식 보존. 부품·엔진 무단변경 금지. opt-in off 경로는 byte 동일 유지.
- 코드/전략/설정 수정 시 `scripts/version_manager.py log`로 기록 후 커밋 (상세 = README 버전관리).

### 🧪 테스트/진단 하네스 (버전별 — `diagnostics/`)

> 최종 테스트(10년 백테스트) 과정에서 만든 **검증·진단 하네스**를 버전(Phase)별 한 폴더에 모았다. 모두 production 모듈을 그대로 호출(별도 드라이버 우회 아님). **실행 = repo 루트에서** `PYTHONUTF8=1 PYTHONPATH=. python <경로>`. 품질 미달(의존성 결측 등)은 편입 제외.

**등록 기준 = 재사용성**(반복 실행/회귀 도구만 메인 유지, 일회성 증거는 `archive/`). 모두 실행 검증 완료(exit 0 + 실출력).

| 버전 | 파일 | 용도 |
|---|---|---|
| **P3 주식** | `diagnostics/p3-stock-pipeline/construction_smoke.py` | 9단계 종목선택→ETF fallback wire 스모크(`build_sleeve_decisions` 실호출, metric_panel=EDGAR 회계). 회귀 재사용 |
| **P3 주식** | `diagnostics/p3-stock-pipeline/xsection_value.py` | 다종목 횡단면 value rank-IC alpha 측정(overlay OFF, tercile L/S + NW-HAC). 유니버스 확대 시 재측정. ⚠️ FWL market-excess IC=raw 동일=보정 no-op 의심(수정 대상) |
| **P4 멀티에셋** | `scripts/run_multiasset.py --backtest` | ★**현행 17축 attribution 프로덕션 하네스**(거시→업종분해→종목 gate/judge→회계). production 진입점이라 `scripts/` 잔류 |

**archive(일회성 보존, `diagnostics/archive/`)**: `fhc_live_mint.py`(FHC 발권 LIVE 단독 검증, creds+유료) · `gate_consult_verify.py`(가치게이트 자문 claim 1회 검증, advisory). 한 번 돌린 증거라 메인 미등록.
**제외**: `multiasset_backtest_v1`=P4로 완전대체 삭제 / `.p2-m4-voltransfer-markov.py`(루트 잔류)=`.p2-corrected-frame.py` 결측 실행불가 복구 보류.

### 📐 18축 attribution (저조 영역 원인 격리 — P4 하네스 산출)

> "어느 자산/산업이 저조한가 + 왜(L0~L3)"를 격리하는 18개 축(⑱=2026-06-08 신설, yaml 연구↔런타임 배선 정합). `run_multiasset.py --backtest` 분석부가 출력. **저조 판정 기준** = 분기평균·Sharpe·누적기여 동시 + regime별 비중-수익 정렬. (추정 금지, 로그 실측 수치로만 판정). ★**분기별 손실 진단(P7)도 이 18축으로 분해**한다(특정 손실 분기 = 어느 축이 끌어내렸나).

| # | 축 | 측정 내용 | 주 귀속 |
|---|---|---|---|
| ① | 거시신호 regime 예측력 | regime별 각 자산 실측수익(그 국면 최고수익 자산) | L1 |
| ② | 거시→배분 비중-수익 corr | regime별 (평균비중, 평균수익) 횡단면 정렬(>0=좋은자산에 무게). **coin in/out 양측 측정** | L1 |
| ③ | 한/미 배분 | us vs kr 누적기여·Sharpe | L1/L2 |
| ④ | 산업간 배분 | 산업 평균비중 vs 평균수익 정합 | L1/L2c |
| ⑤ | 산업내 선택 alpha | 선택종목 가중 − 업종 universe EW(tautology 주의) | L2 |
| ⑥ | 게이트 거부사유 | REJECT rule 분해(max_weight_single 등) | L0/L2c |
| ⑦ | 종목 집중도 | 통과종목수·최대단일비중 | L2c |
| ⑧ | IS/OOS 과적합 | walk-forward IS vs OOS 동부호 | L1 |
| ⑨ | judge 감쇠 | down-only attenuator a(1.0=무감쇠 baseline) | L0/L3 |
| ⑩ | selector 종류 | 개별선택/ETF/EW 경로 분기 | L0 |
| ⑪ | regime 전환 | 분기별 regime 라벨 전이·에피소드 타임라인 | L1 |
| ⑫ | 커버리지 | 시리즈별 실데이터 일자·n | L2b |
| ⑬ | VIXCLS vol factor | factor 공분산 vol 차원 결측(ALFRED vintage 한도) | L2b |
| ⑭ | survivorship | survivor-only universe phantom haircut(~1.2%p/yr 가정) | L1/L2b |
| ⑮ | 거래비용 | 슬리피지·수수료 반영 | L2c |
| ⑯ | regime confidence | `RegimeEstimate.confidence_now` 추출·사이징 반영 | L2 |
| ⑰ | 환효과 | USD/KRW 자산 환산 영향 | L1/L2b |
| ⑱ | **yaml 실측↔런타임 배선 정합** | study yaml 에 adopted/measured 된 신호(한국 `_rotation` 고유 cycle·미국 factor IC·산업별 신호)가 런타임 코드(decompose/selection/weight_rules)에 **실제 배선됐나**. yaml 만 있고 코드 미연결 = **배선 누락**(연구 자산 사장). 역으로 코드에 yaml 근거 없는 prior 박제(일반론)도 적발 | **L0**(배선)/L1(근거부재) |

---

## 🔬 멀티에셋 스터디 워크플로 (트리거)

자산 영역별 스터디(이론 + 실데이터 검증 → lens·상관계수·지표가중치 코드화) → opus 독립 감사 →
시스템 통합을 **복수 psmux 세션**으로 재현하는 SOP.

**트리거 키워드**: `자산 스터디 wf` / `섹터 스터디 검사` / `스터디 오케스트레이션` / `study orchestration`
→ 수신 시 [STUDY-ORCHESTRATION.md](./STUDY-ORCHESTRATION.md) 를 Read 하고 5-Phase(스폰→지시→감사→통합→연관)를 따른다.

| 문서 | 관점 |
|---|---|
| [STUDY-ORCHESTRATION.md](./STUDY-ORCHESTRATION.md) | 오케스트레이터 — 세션 매핑·섹터 메타·통합 주의·재현 절차 |
| [STUDY-KIT.md](./STUDY-KIT.md) | 각 방(세션) 작업 지시 — 3흐름 + 8축 감사 기준 |
| [study-research/AUDIT-GUIDE.md](./study-research/AUDIT-GUIDE.md) | opus 독립 감사 12축 가이드 |
| [progress-study-system.md](./progress-study-system.md) | 진행 상황·파이프라인 업그레이드 큐 |

**불변식**(통합 시): reflexive loop 차단(belief→_macro 차단), L축 공통인자 1회 계상+PSD, opt-in off 무회귀, analyst-level lens 다운그레이드 금지(시스템 못 받으면 파이프라인 업그레이드).

## 🗂️ 지표/관계 Ledger 기록 규칙 (재탐구 방지 — 필수)

> **핵심 목적**: 다음 리서치가 **이미 했던 탐구를 반복하지 않게** 한다. 후보·채택·미채택 + 사유 + 근거를 yaml 에 산발하지 말고 ledger 단일 집결.

**위치**: `study-research/_wire/indicator-ledger.md`(지표) + `study-research/_wire/cross-regime-ledger.md`(cross/regime 관계). 지표 ledger 자동생성 = `core/study/indicator_ledger.build_indicator_ledger(StudySession)`.

**status 4-state** (미채택을 영구/보류로 구분 — 부활 가능성 명시):
- **adopted** — 채택(weight_rules base_weight>0, 런타임 반영 대상)
- **candidate** — 후보(아직 검토 안 함, 탐구 대기)
- **rejected_provisional** — **보류**(일시 연관 파탄·regime-conditional·표본부족 n<30). ★재평가 트리거(regime-draw/data-event) 시 부활 가능 → IC9 복귀 로직 대상
- **rejected_permanent** — **영구 폐기**(PIT-corrupt·spec-code drift·이론 자체 기각). 부활 금지(decisions §14 class C 격리)

**필수 기록 항목** (지표·관계 each): status / **reason**(theory_basis·audit verdict·통계 근거) / **research_ref**(validation-*.md·direction.md 링크, 근거 추적) / (cross·regime 추가) channel(cross=공유 factor / regime=국면별) + 실측값[CI, n].

**갱신 의무 시점**: ① study yaml 작성·수정 ② cross/regime 검토(공정 P1) ③ audit verdict 확정(P2) ④ reject 가설 복귀(IC9) ⑤ **study 밖 신규 지표·신호 탐구 착수·진단(엔진 배선·백테스트·진단 세션·외부 자문 수렴 등) — 들여다본 후보를 즉시 candidate 행으로 등록, 결론(채택/보류/기각) 나면 status·reason·research_ref 확정**. **각 시점에 ledger 갱신 안 하면 미완**.

**원칙**: 미채택이라도 "왜 뺐는지 + 언제 다시 볼지(보류 트리거)"를 반드시 기록 → 재탐구 0. ★**탐구 누적 (계속 기록)**: 새 지표·신호를 들여다본 순간(채택 전이라도) candidate 행으로 **즉시 박제** → 같은 탐구를 두 번 하지 않는다. 한 번 잰 실측값(rank-IC·hit rate·forward-return·β 등)은 reason·research_ref에 날짜와 함께 남겨, 다음 세션이 "이미 본 것"인지 ledger만 보고 판정 가능하게 한다. provisional↔permanent 구분 근거 = decisions §14(R11 reject_class).

## 🪙 코인(crypto) 지표 6단계 검토 SOP (regime-conditional 자산 의무 — 고정 규칙)

> crypto는 factor instability가 norm(AMH·시변 beta). 아래 6단계를 **모든 코인 지표 채택·기각 판정에 의무 적용**. SSOT=[plan-coin-indicator-review.md](./plan-coin-indicator-review.md), 측정표준=[regime-conditional-measurement-framework.md](./study-research/_wire/regime-conditional-measurement-framework.md).

1. **S1 논문 ground** — 메커니즘·시대성·regime 의존을 학술 문헌으로 정초(subagent 3계층 저장).
2. **S2 실측 가설** — 4게이트(G1 ex-ante regime / G2 multiple-testing Bonferroni / G3 walk-forward OOS / G4 Newey-West HAC). full-sample 아닌 regime-conditional 1차 단위.
3. **S3 외부검토** — gemini-web + claude-web **병렬 필수**(CIO 페르소나, 코드어 0). 데이터 맞아 보여도 생략 금지(confirmation-bias).
4. **S4 외부검토 재검증** — 자문이 제시한 falsification을 다른 데이터로 직접 측정(cross-asset/leave-episode/horizon/placebo). 자문 ≠ 정답.
5. **S5 역공격 수렴** — 가장 엄격한 반증을 던져 살아남거나 외부+내 논리가 한 점 수렴 시 verdict 도출. 미수렴=candidate+졸업게이트.
6. **S6 15축 audit 최종검증** — 독립 subagent raw 재현(AUDIT-GUIDE 12~15축). **hard-fail 0 확인 후에만 status 확정·ledger 박제**. audit이 over-claim/drift 잡으면 정정 후 재audit.

**불변식**: ⛔ S3 자문 1회 없이 rejected_permanent 금지(deprecation-evidence). ⛔ S6 audit hard-fail 0 전 adopted 확정 금지. ⛔ "전기간 불일치"는 rejected_permanent 사유 아님(crypto instability=norm, 영구폐기는 이론·데이터 무결성 결함만). 거시 신호는 sizing alpha 아닌 throttle overlay로만(n 작으면 BL view 격리).

---

## 통계 엄밀성 (n<30 패널 — 필수)

지표 연구에서 정량 claim(correlation/β/IC/factor loading) 보고 시: p-value 명기 / ≥4 비교 시 Bonferroni·FDR 보정 / 95% CI 박제 / hedge 어휘(단정 금지). n<30 점추정 covariance prior 박제 금지. 상세 = `study-research/_wire/` ledger + 전역 rules.

## 개발 환경

- OS: Windows (10.0.26200), Shell: Git Bash / PowerShell. Path: Windows(`D:\...`). FS: case-insensitive. Line ending: CRLF.
- Python 3.12.10. 의존성·실행법·env = [README.md](./README.md).
- Playwright MCP: 스크린샷 `./CCimages/screenshots/`, 차트 캡처 = chart-capture 스킬. 버전 불일치 시 `npx playwright@latest install chromium`.
