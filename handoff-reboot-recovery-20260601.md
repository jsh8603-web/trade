---
tags: [type/handoff, domain/inv, topic/study-orchestration, reboot-recovery, single-agent-sequential, audit-12axis]
date: 2026-06-01
author: bc9afbe0 (신 main, btn-Codlearn 계정한도 대체)
scope: PC 재부팅 후 단일 세션이 멀티세션 study 오케스트레이션을 누락 없이 순차 인수
ssot_progress: D:/projects/Inv/progress-study-system.md
audit_guide: D:/projects/Inv/study-research/AUDIT-GUIDE.md
study_kit: D:/projects/Inv/STUDY-KIT.md
orchestration_sop: D:/projects/Inv/study-research/STUDY-ORCHESTRATION.md
---

# Handoff — Inv study 오케스트레이션 재부팅 복구 (단일 세션 순차, 완결판)

> **읽는 순서**: 본 파일 전체 → `progress-study-system.md`(SSOT, 자율주행 task 큐 + 각 자산군 verdict) → `STUDY-KIT.md`(절차) → `AUDIT-GUIDE.md`(12축) → 자산군별 `study-research/{asset}/`.
> **상황**: PC 재부팅으로 전 psmux 세션 소멸. 재부팅 후 **단일 세션이 자산군별로 순차** 인수해 완주. 멀티세션 재스폰은 선택(단일 순차가 기본 지시). 작업 무결성 = **모든 study 12축 작성 + 별도 subagent 12축 감사**(§5.5).

## 0. main 세션 정체 (필독)
- 원래 main = `btn-Codlearn` psmux(4dd250f1) = **계정 주간한도 초과 → 다른 계정 OAuth 화면 멈춤(부활 불가)**.
- 현 main = `bc9afbe0`(psmux 밖 독립 인스턴스, 다른 계정). 죽은 세션엔 relay 불가 → **pull 방식**(pane capture)으로 회신 수집해 옴. **재부팅 후 단일 세션은 직접 작업**하므로 relay/pull 불요.
- ⚠️ **주간 한도**: 한 계정 97% 소진(audit subagent 3건=bond_cash 143k+reit 103k+gold 소모). **Jun5 4am reset**. 그 전엔 절약 모드(추가 subagent 최소). 현 세션은 다른 계정이라 가용.

## 1. 전체 작업 정의 + 절차 (STUDY-KIT §2)
Inv 투자시스템의 **자산군별 거시-팩터 study** 오케스트레이션. v2 흐름(사용자 정정: v1은 자문 복붙으로 끝나 전문성 형성 생략 → 재수행). 각 자산군 3단계:
- **2-1 방향성**(자문 다회 3~7R 수렴 → ①이론 수집방향 ②검증방향 ③가설 초안) → `raw/round-*.md` → ★**direction.md 보고 + main 승인 게이트**(승인 전 2-2 금지).
- **2-2 이론 학습**(승인 방향대로 정독) → `raw/theory-notes.md`(저자·연도 명시, 자문 복붙 X).
- **2-3 실데이터 시계열 검증 → 코드화**(상관·regime·Rank-IC, PIT·OOS·합성금지) → `raw/validation-*.md` + `*.py` + `study_session.yaml`.
- ★**raw 강제**: round-*/theory-notes/validation-* 셋 중 하나라도 없으면 산출 불인정. register(require_raw)가 게이트.

## 2. 자산군별 현재 상태 + audit verdict + 잔여 (재부팅 직전, ★핵심)

세션 매핑(죽음): button=macro / common-task=eq_us_cyclical / DA=eq_us_defensive / diary=eq_kr / excel=eq_intl / GCP=reit / jpdf=commodity / jsh86=gold / powerbi=bond_cash / profile=crypto.

| 자산군 | 12축 audit verdict (commit) | 상태/잔여 |
|--------|------|------|
| **commodity** | ✅**충실** (ENSO da14·재실행 bit-identical·hard-fail 0). main commit **61e6d4a** | ★완료 기준방. china_credit_impulse=실측 비유의→structural_low_confidence 격하(정직). 잔여 없음. validation-china = rationale 모범(BIS stock proxy 한계+spec↔code drift+falsifier) |
| **macro B그룹** | ✅**hard-fail 0** (commit **b89f313**) | B(a)dollar REJECTED·B(b)rate validated(VIF1.14 n=5854)·B(c)credit β structural cap0.25 james_stein. 잔여: macro/ git commit(26 미커밋)+2단계 self-check. ⛔{nominal,real,breakeven} 동시투입 금지(Fisher VIF=∞) |
| **reit** | ✅**★충실 PASS, hard-fail 0**(첫 PASS, audit **af63f996**). v3 DONE | §5 r=0.746 spurious 아님 검증완(log-return 차분, NW t=4.14). 환각 2건 catch. §1.7 소급 = level-on-level 4th instance 발견 보강중(mixed regression 실질영향 제한). 잔여: §1.7 보강 마무리+commit(9 미커밋) |
| **eq_us_defensive** | PARTIAL→**사이클 CLOSE**(v3 격하 **eca172d**). validated 2(H4a credit beta industry split n=6588 p<0.0001·H1 contemp real-rate)+structural 1(sleeve §1.6)+TENTATIVE 2(H3·M3)+REJECTED 2(H1 fwd3M·H2) | §1.7 소급 ADF **PASS clean**(NFCI/BAA10Y mean-reverting level 정당). 잔여: 2단계 self-check 마무리+commit(1 미커밋). DEFENSIVE_PURE/FINANCIALS sleeve 분리 APPROVED |
| **bond_cash** | **PARTIAL**(audit **a75ab5a2**, hard-fail 3축: D=ACM revised vintage / B=cash_tbill 차분시 IC 소멸 spurious / C=hy_credit OOS 부호반전). v4 DONE **e17d51fd**(격하 5건: driver 차분+BH-FDR q=0.10 on effective≈84+magnitude freeze+ACM PIT 한계+MOVE=ICE BofA 정정) | validated_alpha 0, 전 7 sub-cluster structural_prior_low_confidence. **Phase7=옵션 A(사용자)**: P0-1 walk-forward regime classifier + P0-2 ACM Kim-Wright real-time 대체 구현 → summary_v5.yaml → commit |
| **gold** | **PARTIAL**(audit **a55fa51b**, hard-fail 2: B+D H8한정). v3 DONE | ★H8 dual e-process 기각(level-on-level spurious: 3변수 I(1)·잔차 ADF p=0.845 coint부재·DW 0.002, e_level=inf=비정상 OOS 외삽). H2 STRONGLY→PARTIAL(json coint=false 모순). **spurious 3번째→§1.7 rule 신설**. H5/H4/H1/H3/H6/H7/CFTC(mm_gold n=157) return 단위 건전. §1.7: H1/H4/H5/H6 clean·H3/H7 점검중. 잔여: H3/H7 마무리+commit(15 미커밋) |
| **eq_us_cyclical** | Verify **PARTIAL**(δ_regime magnitude 전멸: G2 14/16 CI cross-0 heuristic 10-30배 underest·K Bonferroni 0/16·G4 LOEO OOS R² 음수=descriptive not predictive). R15 반영 **8ddb50e** | δ_regime ±0.15 박제 금지→**sign-only prior(magnitude freeze)** structural_low_confidence. 산업 자체 vol·live regime 분류기 OOS 선행. 잔여: yaml v4 격하 반영 미완(hang)+promo-log K/ERROR+commit. ⚠️Workflow `eq-us-cyclical-industry`(2/4 agents 1d2h+)=stuck, kill/재판단 |
| **crypto** | (self-audit 후 STUDY DONE 예정, 아직 audit 전) | direct fetch(CoinMetrics5+FRED3+yfinance3+PyTrends+DefiLlama) H7-H12 검증. P0-A/C 완료, **P1-3 walk-forward OOS 진입**. H2 funding REJECT 부호반전·H3 stablecoin reflexive sharpe-0.43·prior ladder 역방향 재캘리(on-chain1.27>micro0.97>stable-0.43). 잔여: P1-3→P0-D self-audit 5단계→STUDY DONE→**12축 audit**→commit(31 미커밋) |
| **eq_intl** | 충실+보강(audit 실행분). main commit **26cba0a** | H5 china idio 재정의(MCHI R²0.205<<EMXC0.671 100% OOS)·H7 TSM DM/EM archetype. JGB-UST carry+ToT 추가. 잔여: 2단계 저장 self-check(main 직접) |
| **eq_kr** | (2-1 미완) | 거버넌스↛PBR 학술 반증→v1 밸류업 채널 충돌, v1 폐기. 12산업(battery/bio/consumer/semi...) 일부 산출. 잔여: study 재개 또는 보류 판단+저장 점검 |
| **eq_us** | (Phase3 초기) | MAIN-DISPATCH.md 기반 Phase3 자문 진행(theory/validation 전). 잔여: 진행 또는 보류 |

## 3. 사용자 게이트 결정 (확정, 유지)
1. **push 보류** = 전 자산군 로컬 commit 만, remote(coin.git 공유) push 금지(peer 충돌 회피). 일괄 push=별도 지시 시.
2. **bond_cash Phase7 = 옵션 A** = walk-forward classifier + ACM Kim-Wright real-time 대체 구현 **후** Phase7 진입(sign-prior 즉시진입 B 기각).
3. **§1.7 소급 = 의심 건만** = level-on-level 회귀 박힌 study 선별(전수 X). DA clean·reit 4th instance 처리.

## 4. 진행 중 횡단 작업 3종
- **§1.7 소급**: gold(H3/H7)·reit(보강) 마무리. DA clean.
- **git commit**: study-research 130 미커밋 → main 3건(commodity 61e6d4a/루트 8f14b41/eq_intl·kr·us 26cba0a) 완료, 나머지 ~61=각 자산군 순차 commit(push 금지).
- **2단계 저장 self-check**: 2단계 merit 지표도 theory+validation(spec↔code)+rationale+자문원문 raw 완비 점검. commodity(validation-china)가 모범. 누락 보완.

## 5. 재개 절차 (단일 세션 순차 권장)
1. 본 핸드오프 + `progress-study-system.md` 최신 ckpt + `STUDY-KIT.md`/`AUDIT-GUIDE.md` Read. `cd D:/projects/Inv`.
2. `git status --short study-research/` → 자산군별 conventional commit(**push 금지**).
3. 미완 study 마무리(의존도 낮음 순): **bond_cash P0 구현** → **crypto P1-3/P0-D/STUDY DONE** → **eq_us_cyclical yaml v4** → **reit §1.7 보강** → **gold §1.7 H3/H7**.
4. STUDY DONE 도착분 = ★**별도 subagent 12축 audit**(§5.5, self-certify 금지) → verdict → yaml 반영.
5. **2단계 저장 self-check** 자산군별(commodity 모범) → 누락 raw 보완.
6. **eq_intl/eq_kr/eq_us** main 직접 점검(세션 부재).
7. 최종 **J축 system_priors 통합** — L축 공통 equity 인자 1회 계상 + PSD projection 게이트.

## 5.5 ★12축 감사 (사용자 최우선 강조 — 작성도 감사도 12축)
- **모든 study 작성 = 12축 충족 기준.** **audit = 반드시 별도 subagent 가 12축으로** 수행(★main self-certify 절대 금지 — supervisor 자기라벨 무효. bond_cash v1 false-positive·gold H8 self-audit over-claim 실증. raw parquet 재실행+ADF+half-split 하는 독립 subagent dispatch).
- **핵심 8축**: A 이론 실재성(저자·연도, 자문 복붙 X) / **B 실데이터 검증★**(소스·기간·n·p·Rank-IC, OOS IC>0.03 AND t>2.0, 합성=hard) / **C yaml 도출 추적★**(수치가 OOS 회귀와 ±5% 매칭, 매직넘버=hard) / **D PIT·lookahead★**(재무 결산+45~90일, 거시 first-release vintage, 최종개정치=hard) / E 자문비판+환각(인용 원본 확인, 환각 1건=그 claim hard) / F 반증+기각 기록(기각 0건=p-hacking 경고) / G effective-N·검정력(tier 라벨, 차단 X) / H 미해결 의문(공란=red flag).
- **신규 4축**: **I 생존편향·무결성★**(상폐·split·universe PIT, 생존편향=hard 무효화) / J 경제적 유의성(왕복 0.3% 차감 후 +알파, turnover) / K 다중검정 보정(시도횟수 공시=hard, Deflated Sharpe>1.0) / **L 통합 상관 PSD·공통인자 중복★**(USD·실질금리·유동성 중복계상 X, 통합행렬 PSD).
- **Hard-fail 코어 4(통합 차단)**: B·C·D·I. 위반=결과가 약한 게 아니라 **틀린 것**. 조건부 hard: E 환각/F 기각0/K 시도횟수 미공시/J 비용후 alpha주장/L PSD·중복.
- **G effective-N=tier 함수**(crypto halving N=4→"validated alpha" 위장 불가, 자동 "structural prior 저신뢰"). 같은 임계 쓰되 출력 라벨만 분리.
- 중첩 forward 윈도우=**Newey-West/block-bootstrap SE 강제**(B t-stat 전제). 상관=regime별 안정성(위기 tail-corr 1 수렴).
- 판정: 충실(hard 0)=register / 부분·불충분(어느 축 왜)=보강 요청. 합성·생존편향·재계산 불일치=즉시 불충분.

## 6. study_session.yaml 7블록 (STUDY-KIT §3) + 4단계 파이프라인 (§4)
- **블록1 LENS**(정성 렌즈, LLM 주입용·가변=flag 누적으로 estimation_note/regime_reading 변동) / **블록2 INDICATORS**(정량 지표→시스템 자료 귀결) / **블록3 RELATIONSHIPS**(관계 가설=glasso prior, **partial-corr 기준**) / **블록4 WEIGHT_RULES**(최종 산출, 종목별 동적 가중치) / **블록5 CONFIDENCE_HOOKS**(확신/거부 flag 코드 구현 계획, `affects_indicator`/`affects_edge` 명시) / **블록6 COLLECTOR_PLAN**(부족 자료 수집기) / **블록7 CODE_CHANGE_PLAN**(§4 4단계 파일:함수:변경내용 구체).
- **4단계 파이프**(블록7 각 최소 1개): ① learn(regime 조건부 상관·비중 데이터 추정) / ② card(규칙화) / ③ inject(주입) / ④ falsify(해제, e-CUSUM 붕괴=폐기).

## 7. 시스템 wiring 맥락 (재사용 인프라, 대부분 완료)
- **flag→동적 3경로**(seed→라이브 진화, opt-in off=byte-identical, INV_R15_WEIGHTS default-off): **U1 flag→lens**✅(`lens_store.render` confidence_note) / **U2 flag→corr_prior**✅(`flag_router.corr_prior_shrink`) / **U3 corr_prior 레벨분리**✅(`_macro`/`_micro` 가드, belief→macro 누수 차단=reflexive 방지, level 파라미터 가드). 잔여: U3b(별개 인덱스 객체+cross-sleeve edge ValueError 가드, register L축 시) / **U4** Beta regime-tag(후순위, 키잉만·파라미터 freeze).
- **M4 거시-종목 factor 통합**✅(`factor_betas_seed`=셀(β̂,SE,t,n,Bonferroni,tier)+James-Stein w=τ²/(τ²+SE²)·verdict매핑[validated=w/structural=w≤0.25캡/reject=b=β_pool·w=0]+idio conservation / `factor_cov_estimate`=Λ EWMA+stress floor+Higham PSD / `factor_shadow`=bias-stat+eigenvector cosine 로깅전용). SSOT=CONSULT-DECISIONS-M4-factor-integration-20260530.md.
- **M5**=vol factor placeholder(β=None HOLD)✅ + risk gate wiring helper✅(실배선=사용자 게이트 보류, BL prior cov 누수 차단·Π=δΣw 이중계상 금지).
- 가드 13/13 + raw 완비 게이트(`study_register._check_raw_completeness`) = 재사용. study_register.register(path, require_raw=True)로 production wiring.

## 8. 핵심 패턴 / 금지 (불변)
- ★**점추정 magnitude는 정밀통계(bootstrap+LOEO OOS+Bonferroni)서 거의 격하, sign/direction prior만 생존**(전 audit 공통, ★최핵심).
- **audit=12축 별도 subagent, self-certify 금지**(§5.5).
- **§1.7**: level driver 회귀=ADF/coint 사전검정, 비정상이면 차분(Δ) 강제. e_level=inf=spurious.
- **push 금지**(로컬 commit만). **register≠git commit**(register 했어도 미커밋이면 유실, 반드시 commit).
- **Belief-Truth 격리**(U3 reflexive 가드)·**이중계상 회피**(거시=배분레이어/종목=펀더멘털)·**공통인자 1회 계상**(L축).

## 9. 별도 트랙 — local-db 전환 (독립)
- Supabase→로컬 SQLite. **L0/L1/L2(매매 핵심 6파일 save_decision/execute_trade DB부/run_agents+smoke PASS) 완료**. **L3~L5(잔여 ~50 REST+psycopg2 5, harness2 위임 후보)+L6(회귀)** 잔여.
- 진입점: `progress-local-db-migration.md` + `.l2-handoff.md`(전환규약·그룹분류). 사용자가 "L3 새 세션" 지시.
- ⛔ SACRED: `execute_trade` 실주문 orders POST·JWT / `live_trader run_cycle` 본체 미변경(DB 호출부만 어댑터화). DRY_RUN 유지.

## 10. 참조 SSOT (다음 세션 필수)
- `progress-study-system.md` — ★자율주행 task 큐 + 각 자산군 verdict 상세(본 핸드오프의 원천)
- `STUDY-KIT.md` — study 절차(2-1/2-2/2-3) + yaml 7블록 + 4단계 파이프 + §2.5 감사
- `AUDIT-GUIDE.md` — 12축 정의 + hard-fail 분류 + 충실/불충분 예시
- `study-research/STUDY-ORCHESTRATION.md` — 멀티세션 스폰→스터디→감사→통합 SOP (Inv/CLAUDE.md 트리거 `자산 스터디 wf`)
- `study-research/DISPATCH-TRACKER.md` — 세션별 지시 현황판
- `study-research/macro/m4-collection.md` — M3 거시연관 6/6 verdict 보관소
- `CONSULT-DECISIONS-M4-factor-integration-20260530.md` / `CONSULT-DECISIONS-layering-20260530.md` — 자문 결정 SSOT
- `handoff-study-system-20260530.md` — 압축 전 상세 인계(flag 3경로 U1/U2/U3·감사·자문 3R)
- 자산군별: `study-research/{asset}/{study_session.yaml, direction.md, raw/{theory-notes,round-*,validation-*,*.py}}`

## 11. 환경 주의
- python = `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`(bash `python`=command not found). pytest=`<위> -m pytest`.
- PC 절전=의도적 1회, 재발 없음. 절전/장시간 시 LLM hang(토큰 정지+타이머만 wall-clock 증가) → capture-pane spinner 토큰 고정+esc-to-interrupt 부재로 판별, **Escape 복구(⛔ C-c=claude kill 금지)**+nudge.
- 주간 한도 Jun5 4am reset(audit subagent 소모). 그 전 절약 모드.
- autopilot flag: `D:/projects/button/agent/.secretary/.autopilot-{psmuxName}.flag`(단일 세션 인수 시 새 세션명으로 touch).

## TL;DR
재부팅 후 단일 세션: `cd D:/projects/Inv` → 본 핸드오프+progress+STUDY-KIT+AUDIT-GUIDE Read → 미커밋 commit(push X) → 미완 study 5건 순차(bond_cash P0구현 / crypto P1-3·P0-D·STUDY DONE / eq_us_cyclical yaml v4 / reit §1.7 / gold §1.7 H3·H7) → ★**별도 subagent 12축 audit** → 2단계 저장 self-check → eq_intl/kr/us 직접 → J축 통합. commodity=완료 기준방. **점추정 magnitude 격하·sign prior 생존 + 12축 작성·감사**가 최핵심 불변. local-db=별도 트랙(L3~L6).
