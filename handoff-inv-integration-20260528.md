# 세션 인계 — 통합 투자 시스템 (btn-Inv, 2026-05-28)

> 재개 포인터. 상세는 durable 문서 참조: [`plan.md`](./plan.md)·[`progress.md`](./progress.md)·[`harness2.md`](./harness2.md)·[`implementation-keys.md`](./implementation-keys.md)·[`review-findings.md`](./review-findings.md)·설계 [`IMPLEMENTATION_PROMPT.md`](./IMPLEMENTATION_PROMPT.md)(Round 10).

## 이번 세션에 한 일 (전부 완료·durable)
1. **설계 검토**: architecture.md(Round4)→IMPLEMENTATION_PROMPT.md(Round10) 읽음. coin repo(jsh8603-web/coin) clone 후 코드근거 주장 검증 = 거의 전부 정확(EMERGENCY_STOP orchestrator.py:179 라인까지). → `review-findings.md`.
2. **7-에이전트 종합**(opus): 분석5(A1실행·A2리스크/포트옵·A3ops/백테스트·A4consensus/학습·A5유니버스/데이터) + 코드작성2(B1 macro·B2 quant). 결과 = `implementation-keys.md`(§1-§7 도메인별 wire·코드위치·reuse-github 매핑, §8 정정14건, §9 구조).
3. **brain 코드 작성·검증**: `stock/`(~1700줄, B2: contracts·valuation·value_trigger·factor_attribution·fundamentals_adapter, import OK) + `core/brain/`(~2300줄, B1: regime_classifier·macro_reasoning·regime_to_weights(BL)·indicator_event_correlation(542, §5.8-H 상관모델)·fred_adapter·macro_indicators·macro_schema + MACRO_CORRELATION_BACKGROUND.md, import OK). B2 smoke 의 cp949 em-dash 출력에러는 표시 이슈일 뿐 로직 정상.
4. **plan/progress/harness2 작성**: 전 Phase(-1~R) `wf: harness2`. Phase -1 = Sonnet-executable 5스텝(SO-1~5). §2.9 게이트 = harness2 verifier 검증 핵심.
5. **coin→Inv 루트 승격 완료**: `.git`·agents/·rl_hybrid/ 등 루트 안착(git 수정/삭제 0건, VERSION 1.35.2 무손실). core/·stock/ 신규 untracked. `.gitignore` 에 _refs/·skfolio/·.secretary/·.harness2/ 추가. → Inv = coin 작업복사본("Inv 구현→coin 덮기" 경로 확보).

## 다음 의도 (재개 시 바로)
**harness2-wf 실행으로 Phase -1 착수** (E2 멱등성·R2 reconciliation·B1 스키마게이트·B3 결정성·C2 서킷브레이커). harness2.md SO-1~5 가 Sonnet-executable. 배선=`IMPLEMENTATION_PROMPT.md §0.6-B`+`implementation-keys.md §1`. **선행**: ① coin 라인번호 v1.35.2 정독(승격됐으니 루트 agents/·scripts/·rl_hybrid/ 직접) ② polymarket-bot 미clone 시 `_refs/` 에 clone(SO-1/2 응답유실 재시도·ghost/clamp 패턴).

## 미해결 결정 (해당 Phase 도달 시 판정 — review-findings §4)
- **모순1**(Phase3): C2 degrade→Qwen abstain 이 급락장 가치전략 무력화 → heavy-agent 예산 우선순위 큐 설계.
- **모순2**(Phase3): H22 lookahead 가 Phase3 수용판정(Claude가 사건결말 암기)에도 적용 → training cutoff 이후 사건/마스킹/기계적-only 게이트.
- **갭4**(Phase0): M1 택소노미 = AssetTrack Directional-only(권고, scalp_ml/kimchirang 별도 Strategy) vs 3계열.
- 디렉토리: **해결됨**(승격 완료).

## 재개 시 핵심 gotcha
- **reuse-github-as-is** 기본규칙: 레퍼런스 코드 그대로 차용(출처 implementation-keys.md §1-§7). 단 **stub 주의**: MlFinLab labeling·AT attribution(np.random)·AT registry = 계약만, 본체 자체구현(promotion-log K 2026-05-28 참조).
- Sonnet-executable 강제(파일:심볼·before/after·경계·완료판정).
- 디렉토리: agents/·rl_hybrid/·scripts/ = coin 코드(루트), core/·stock/ = 신규 brain, _refs/ = 레퍼런스(gitignore), coin/ 서브디렉토리 더 이상 없음.
- B1 risk: cvxpy 미설치 시 bl_returns 정통경로 미동작(weight_tilt 폴백=기본). Truflation/ECOS 미연동(인터페이스만).
- 외부 자문(/gemini-web+/claude-web)은 모순1·2·갭4 판정 시 사용 권장(자문 트리거 ②대안 trade-off·⑥plan 신규).
