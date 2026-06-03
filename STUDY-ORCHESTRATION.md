# STUDY-ORCHESTRATION — 멀티에셋 스터디 오케스트레이터 SOP

> **목적**: 자산 영역별 스터디(이론 + 실데이터 시계열 검증 → lens·상관계수·지표가중치 코드화)를
> **복수 psmux 세션**으로 돌리고, main(오케스트레이터)이 **독립 감사 → 시스템 통합**까지 재현하는 절차.
> 이 세션(2026-05-30)에서 실제 수행한 흐름을 그대로 반복 가능하게 박제한 문서.
>
> **문서 체계**: 본 문서(오케스트레이터 관점) + [STUDY-KIT.md](./STUDY-KIT.md)(각 방 작업 지시) +
> [study-research/AUDIT-GUIDE.md](./study-research/AUDIT-GUIDE.md)(12축 감사) + [progress-study-system.md](./progress-study-system.md)(진행/큐).

---

## 0. 핵심 원칙 (왜 이렇게 하나)

1. **실데이터 검증 없는 코드화 차단** — 그럴듯한 이론·자문을 그대로 yaml 화하는 것이 가장 큰 위험. 각 방은 수집기 실데이터로 가설을 confirm/reject 해야 하고, register 는 `require_raw=True` 로 raw(이론·검증·자문 라운드) 없으면 거부한다.
2. **main 은 pass-bias** — 통과시키려는 편향이 있으므로 **main 자체 감사 금지**. 산출 도착마다 **opus 독립 subagent** 가 provenance 재실행(raw 스크립트 직접 재계산) 기반으로 감사한다.
3. **analyst-level lens 다운그레이드 금지** — 시스템이 산출 구조를 못 받으면, lens 를 깎는 게 아니라 **파이프라인을 업그레이드**(opt-in 필드 추가)한다.
4. **opt-in off = byte-identical 무회귀** — `INV_R15_WEIGHTS`/`INV_STUDY_LENS` default-off. 통합은 검증·등록까지만, 실제 개입은 live baseline 전 shadow/log-only. 실거래 flip 은 사용자 게이트.

---

## 1. 세션 ↔ 자산 영역 매핑

| 세션(psmux) | study_id | 자산 영역 | yaml 상태 |
|---|---|---|---|
| btn-button | macro | 거시(포트폴리오 배분 게이트) | ✅ |
| btn-common-task | eq_us_cyclical | 미국 경기민감주 | ✅ |
| btn-DA | eq_us_defensive | 미국 방어주+금융 | ✅ (⚠️ 합성 의심 이력) |
| btn-excel | eq_intl | 국가지수 ETF(미국 제외) | ✅ |
| btn-GCP | reit | 리츠 | ✅ (v2, 승격 보류) |
| btn-jpdf | commodity | 원자재 | ✅ |
| btn-jsh86 | gold | 금 | ✅ |
| btn-powerbi | bond_cash | 채권·현금 | ✗ 미산출(v1만) |
| btn-profile | crypto | 암호자산 | ✗ 미산출 |
| btn-diary | eq_kr | 한국주 | ✗ 미산출(v1 폐기) |

---

## 2. 재현 절차 (5-Phase)

### Phase A — 세션 스폰
- ⛔ raw `psmux new-session` 금지(PreToolUse Bash Guard 차단). **`spawn-session.sh` 경유** 필수.
  `PROJECT_DIR_OVERRIDE="$(pwd)" bash /d/projects/button/agent/.secretary/.scripts/spawn-session.sh {worker}`
- 세션 이름 충돌 시: `psmux has-session -t {세션명} && psmux kill-session -t {세션명}` 선행.
- 메시지 발송은 **SSOT 헬퍼** `~/.claude/scripts/lib/psmux-send.sh` 경유(`psmux_send_message`/`_slash`/`_key`). 세션 쉘 = cmd.exe → Windows 경로(`cd /d D:\...`)만. raw `psmux send-keys` 는 PreToolUse Guard 차단.

#### ★세션 간 통신 규약 (양방향 — 회신이 안 오는 원인 1순위)
- **종목/거시 세션 → main(btn-Codlearn) 회신도 같은 헬퍼로 발송**한다:
  `bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "경로 + 1줄 요약"`
  ⛔ **자기 화면에 텍스트로 출력하는 건 회신이 아니다** — 상대 세션엔 아무것도 안 간다. 반드시 Bash 도구로 헬퍼를 호출해야 상대 pane 에 도착한다.
- **★상대 입력란 충돌 처리**: 상대 세션이 타이핑 중(입력란에 텍스트 잔존)이면 덮어쓰기 위험. `psmux_send_key {target} Escape` 는 **상대 입력을 파괴하므로 금지** → 잠시 후 재시도한다. main 은 보통 turn 처리 중/idle 이라 입력란이 비어 충돌이 드물다. (실측 2026-05-30: btn-button 이 회신 방법은 알았으나 main 입력란 텍스트 충돌 우려로 전송을 보류 → 회신 누락처럼 보임).
- **요청 발송 시 회신 방법을 메시지에 명시**(예: "완료되면 `...message btn-Codlearn` 으로 경로 회신")해 상대가 텍스트 출력로 끝내지 않게 한다.
- **★긴 지시는 파일화(본문 누락 방지)**: 여러 줄 메시지는 **헤더(첫 줄)만 제출되고 본문 줄이 누락**될 수 있다 — heredoc 줄바꿈이 send-keys 에서 중간 Enter 로 해석됨(실측 2026-05-30: M2 배포 시 eq_us_cyclical 이 헤더만 수신). 긴 지시는 파일(예: `timeline.md §4`)에 두고 **경로 + 단일 줄 지시**만 전송한다. 다세션 루프 발송 시 특히 단일 줄 권장.
- **★다세션 루프 발송 후 큐 정체 점검**: 루프로 여러 세션에 연속 발송하면 일부 세션에서 Enter 가 누락돼 입력란에 메시지가 큐잉만 되고 미제출(`❯ Press up to edit queued messages`)될 수 있다(실측 2026-05-30: 6세션 중 4세션 큐 정체, gold·eq_us_cyclical 만 제출). 발송 후 `capture-pane` 으로 확인하고, 정체 시 `psmux_send_key {sess} Escape`(x2, 큐 클리어) → `psmux_send_key {sess} Enter`(제출)로 해소한다.

### Phase B — 방 작업 지시 (STUDY-KIT 배포)
각 방은 3흐름 수행 → `study-research/{study_id}/` 에 산출:
1. **이론 학습** → `raw/theory-notes.md` (교과서·논문 정독, 자문 복붙 금지) + `raw/round-*.md`(자문 다회) + `direction.md`
2. **실데이터 시계열 검증** → `raw/validation-*.md` (수집기 실데이터: 데이터소스·기간·n·상관·p값·Rank-IC. ⛔합성·시뮬 금지). 가설 confirm/reject.
3. **코드화** → `study_session.yaml` 7블록 (lens·indicators·relationships·weight_rules·confidence_hooks·collector_plan·code_change_plan). weight·corr_prior·lens 가 실측에서 도출돼야(추적성).

### Phase C — 독립 감사 (산출 도착마다)
- main 이 아니라 **opus subagent** 가 [AUDIT-GUIDE.md](./study-research/AUDIT-GUIDE.md) 12축으로 감사.
- §0 provenance: yaml/md 수치를 claim 으로 보고 **raw 스크립트 재실행**해 일치 확인 + 합성 지문(fat-tail kurtosis·이벤트 실재·주말 공백) 검사.
- 판정: **충실**(register 가능) / 부분 / 불충분(B·C·D·I hard-fail 또는 합성). 불충분·부분 = 보강 요청.
- tier: validated alpha vs **structural prior(저신뢰)** 라벨. REJECT/contemporaneous 가설은 structural prior, validated 위장 금지.
- **★M3 거시연관 결과도 동일하게 독립 감사**(self-report 신뢰 금지 — main pass-bias). 세션의 "합성無·자가검증" 주장을 opus subagent 가 **raw 스크립트 재실행**으로 검증. M3 핵심축 = B(실데이터/합성 provenance) · C(상관·loading 추적성) · D(PIT/OOS) · G(검정력 n·t-stat) · K(다중검정 driver×epoch) · L(cross-sleeve 중복계상). **충실 확인된 M3만 M4 거시 레이어 반영** — 검증 안 된 상관계수로 driver 채택 금지(시스템 변경이라 영향 큼).

### Phase D — 시스템 통합 (register 게이트)
```python
from core.study.study_register import StudyRegister
sr = StudyRegister(assumption_registry=...)
rep = sr.register("study-research/{sid}/study_session.yaml", require_raw=True)
```
- **off**(default): 검증·raw 게이트만 통과 확인(카드 미등록, 무회귀).
- **on**(`INV_R15_WEIGHTS=1`): weight_card 등록 + flag tilt. **L축 통합 점검**(아래 §4) 동반.

### Phase E — flag·연관 (live 진화, 후속)
- flag→3경로(U1 lens / U2·U3 corr_prior / weight tilt). 자세히 progress 업그레이드 큐.
- 거시-종목 cross-correlation(M1~M4) — 별도 후속.

---

## 3. 섹터별 메타 (소스·방법론·과제·업데이트 대상)

| study_id | 핵심 방법론 | 데이터 소스 | 통합 시 업데이트 대상 코드 | ★통합 주의 / tier |
|---|---|---|---|---|
| **macro** | Investment Clock 4국면, Glasso partial-corr(구조상수 force-include) | FRED(T10Y2Y·HYOAS·breakeven)+FxStore. 미적재 DFII10·JGB·M2·ECOS | `regime_to_weights` _belief_conditional_cov, `RegimeGlasso` corr_prior | **level='macro'(belief 차단 no-op)**. cross-sleeve corr writer = 실현수익률 전용 |
| **eq_us_cyclical** | Damodaran 정상화(peak_trap), CMA(asset growth), Grinold-Kahn IR | EDGAR(우선1)+Damodaran ERP. 현 FRED 17시리즈 | `weight_card` floor_by_regime 확장, baseline_ic 보수화 | **tier=structural prior**(H3·H5 REJECT, vix_beta contemporaneous). floor_by_regime = opt-in 필드(다운그레이드 아님) |
| **eq_intl** | CAPM/Adler-Dumas(환 1차 driver), China decoupling, momentum crash | 국가ETF TR 패널+FxStore 다국가. FRED DTWEXBGS·WTI | `weight_card` delta_arch_by_type(국가 archetype 5종) | 환이 반쪽 이상. H5 china_idio R²gap +0.466 100% OOS(강확인) |
| **commodity** | Theory of Storage, Tang-Xiong financialization, Hamilton NOI | FRED 4+CME futures term+EIA/WASDE+CFTC COT | `weight_card` sub-sleeve 4종, contango_flip 즉시 kill | H5 Welch t=−66.74(검증). structural prior(NW SE 미보정·deflation 미적용) |
| **gold** | Anti-real-rate bond, USD numeraire, safe-haven(국면의존 부호) | FRED(DFII10·breakeven·DTWEXBGS)+World Gold Council 분기 | lens real_rate beta, cb_demand flag(SECONDARY refit) | real-rate beta 유지. **decoupling=level shift(베타 약화 아님)** 16y 안정 |
| **eq_us_defensive** | NIM slope(은행), Damodaran(방어), Capital Cycle | EDGAR 은행특화 파싱(NIM·NPL·provisions)+TIPS | `weight_card` archetype 5종 **부호 split**(방어 음/은행 양) | ⚠️ **합성데이터 의심 이력(boosting 필요)**. 방어/금융 부호 반대 — 단일 sleeve 통합 주의 |
| **reit** | AFFO/(r+ERP+ΔCapRate−g_NOI), cap-rate mean-revert | alpha-vantage+EDGAR AFFO/FFO+Nareit+NCREIF ODCE | `weight_card` 8 sub-regime×3 window=24카드 | **H1 REJECT**(long-WALT 부호반전). v2(정량 단정 폐기). equity sub-panel 승격 보류 |
| crypto / bond_cash / eq_kr | (미산출) | — | — | yaml 미산출. crypto=direction만 / bond_cash=v1 carryover / eq_kr=v1 폐기·v2 보류 |

---

## 4. 통합 시 공통 주의 (★불변식 + 이 세션 발견)

1. **Reflexive loop 차단 (U3)** — 종목 flag/belief 가 거시 corr 에 새면 pro-cyclical 재앙(강세장 종목 과신→거시 "리스크 극저" 오판→drawdown 직전 최대 베팅). `corr_prior_shrink(level=)` + `study_register.prepare_corr_prior` facade 가 scope→level 자동결정: **macro/bond=macro(belief 차단), 그외=micro(within-sleeve 약화)**. `_macro` writer = 실현 cross-sleeve 수익률·regime 전이만.
2. **L축 공통인자 1회 계상 + PSD** — cross-sleeve 공분산은 sleeve별 독립추정으로 합치지 말고 `system_priors.factor_implied_cross_cov`(B Λ Bᵀ + diag(idio)) **단일 경로**. 공통 팩터(rate/dollar/oil/credit)가 정확히 1회만 계상되고 PSD 가 eigh-floor 로 내장. study별 corr_prior 는 within-sleeve 로 닫아야(같은 indicator_id 가 여러 study 카드에 안 겹치게).
3. **within-study 이중계상 차단** — 같은 indicator_id 가 weight_rules 에 2번 들어가면(예: peak_trap floor 표식) series_ids 중복 → corr 인덱스 충돌·공분산 특이. `_build_card` 가 **base_weight 합산 dedup** 으로 차단(0.30+0.0=0.30 결과 보존).
4. **opt-in off 무회귀** — register 는 off 에서 검증만(production 미개통, byte-identical). on 은 카드 등록·flag tilt. 본체(judge/RegimeGlasso/execute_trade) 미변경.
5. **tier 정직성** — 검증 통과 ≠ validated alpha. REJECT·contemporaneous·overlapping-window(NW 미보정)는 **structural prior(저신뢰)** 로 라벨. validated 위장 금지.
6. **과설계 freeze** — robustness(deadband/clamp/shrinkage/fallback)는 지금 OK, optimization/adaptation(튜닝 rate·학습 threshold·dynamic path)은 live baseline 전 freeze.

---

## 5. 트리거

**키워드**: `자산 스터디 wf` / `섹터 스터디 검사` / `스터디 오케스트레이션` / `study orchestration`
→ 수신 시 본 문서를 Read 하고 §2 5-Phase 를 따른다. 특정 자산이면 §1 매핑으로 세션 식별 → §3 메타로 소스·통합 주의 확인.
