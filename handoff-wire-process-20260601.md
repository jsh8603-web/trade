---
tags: [type/handoff, domain/inv, topic/wire-process, session/btn-Inv]
date: 2026-06-01
scope: study→wire 공정 재정립 + 받아적기 정정 세션 인계. 진입=progress-wire-impl.md 공정 SSOT.
push: ⛔ 금지 (로컬 commit만)
---

# Handoff — study→wire 공정 재정립 + 받아적기 정정 (2026-06-01)

> **재개**: 본 파일 → `progress-wire-impl.md` 의 "★사용자 요구 충족 공정 (SSOT)" 섹션 → 거기 P1~P5 + 어디 손보는지.

## 1. 이번 세션 핵심 = 사용자 다회 정정 (framing 재정립)

사용자가 7회 정정. 핵심 framing:
- **요구**: ledger 통과(채택) 지표 전부 **agent(judge L2 qwen/L3 bge) 개입 전, 자동 코드계산 배분 레이어**서 **regime 동적 corr** 로 동작.
- ★main 이 framing 이탈했던 지점: judge qwen lens(구 W8) 를 앞세웠으나, 그건 agent 레이어 **부차**. 진짜는 cross+regime 동적 corr(배분, agent 전). decisions §1.1 도 judge=down-only consumer 로 동일.
- codify 원칙: 자문/verdict **글자대로 박지 말고 우리 코드 맥락에 맞게** codify(자문은 코드 못 봤을 수 있음). 어디 손보는지(파일:함수) 누락 금지.

## 2. 완료 (코드 검증 + codify)

- **IC2 ✅**: static Λ 주입(`factor_returns._default_fred_source` get_series 재작성 / `_static_factor_lambda` 캐시 / gate-Λ risk_gate 격리). 회귀 414 passed.
- **IC3 ✅ codify**: `factor_betas_seed` grand(cross-group) fallback **폐기** → group-specific / reject=β:=0 lock / missing=group 평균. **gold dollar -0.408(equity grand 상속 오염)→-0.328 순수**. eq_intl rate reject→0. self-test 7/7. corr_prior us_stock×commodity 0.5444→0.4372·×gold→0.5260.
- **IC5 ✅**: 핫패스 RNG 0 확인 + golden test 2개 CI 게이트.
- **IC7 ✅**: as_of PIT 전파(coin_track_macro→allocate→regime_to_weights→_belief_conditional_cov→_ic_corr_prior→_static_factor_lambda→fetch_factor_cov).
- **IC6 ✅**: judge facade(prepare_judge_call) 기구현 확인, 소비=go-live.

## 3. ★코드 전수확인 발견 (받아적기 정정)

- **regime 동적 corr = production 0 동작**(테스트만): `allocate` production 호출 = `coin_track_macro.py:74` 1곳, macro_view 無 → `_fallback_hrp`(regime_to_weights 우회). `CoinTrackWithMacro` 인스턴스화 = **전부 tests**. `agents/orchestrator.py`(라이브) 미연결 = progress.md 메인 **Phase I 미개통**.
- **cross/regime 실측 현황**(사용자 "그런 작업 못 봤는데" 재확인): ✅자산↔factor std β **실측**(`_factor_shadow/batch-std-beta-5sleeve` n=5052 same-day) / ⚠️자산↔자산 cross=**추론 후보**(`_wire/cross-and-regime-research` C1~C12, "직접 cross-corr 실측 아님" hedge_note) / ⚠️국면별=**PoC 1**(DGORDER→XLE). `RegimeGlasso.fit`=런타임 학습 메커니즘이지 검증 도출 아님.
- **yaml만으로 코드화**: weight(weight_rules→_build_card)=가능 / corr_prior 부호(relationships→corr_prior 변환경로)=**부재, 신규 codify 필요** / 크기(SEED)=하드코딩, 측정 필요.
- **decisions 방향성 정합 확인**: §1.1(judge=down-only consumer/단일카드→corr_prior+lens view) §1.2-1(static corr_prior=배분 WIRE) §1.4(regime hardened-soft b(t)) = 요구와 정합. 단 "라이브 통합·전수 agent전 자동 일괄원칙"은 §7 분산(명시 약함).

## 4. 공정 P1~P5 (progress-wire-impl.md SSOT 박제 완료)

P1 지표 도출(실측, subagent 템플릿+15축 근거 박제) → P2 audit(15축, opus subagent 독립) → P3 ledger 등록(indicator_ledger.py 신규) → P4 codify(corr_prior 부호=relationships 변환경로 신규 / 크기=SEED vol cell / regime 동적=IC0-R / weight=됨) → P5 라이브 통합(Phase I, go-live 게이트).

## 5. 다음 의도 (자율 진행 = P4 메커니즘 글루부터)

- **IC0-R** (P4, 코드 확인 완료): `coin_track_macro.collect_market_state`(:60) opt-in on 게이트 내 → `RegimeClassifier(usd_adapter=RealFredAdapter())`(regime_classifier:73) `.classify(as_of)`→macro_view + `build_sleeve_regime_ids(clf, panel, labels)`(regime_history:81)→sleeve_regime_ids → `allocate(macro_view=mv, sleeve_regime_ids=ids, ...)`. 무거움(과거 전체 classify)→캐시 후속. off byte-identical. FRED 키 없으면 graceful.
- **relationships→corr_prior 변환 경로** (P4): 신규 글루(현 부재).
- **P1 subagent** (cross/국면별): 필요시 스폰, progress P1 템플릿(입력 제공+코드반영 계획+15축 근거).
- ⛔ SEED vol cell 추가·자산↔자산 cross 등록 = P2 audit 게이트((가)관문). 라이브 통합(P5)=사용자 게이트.

### ★확정 (2026-06-01 사용자 지시 — 안 물어봄, 방향성만 박고 실행은 넘김)
- **P1→P2 순서대로 둘 다 실행**(이미 지시됨, 재질문 금지): P1 cross/regime 실측 도출(subagent — cross-and-regime top5 + progress P1 템플릿[입력제공+코드반영계획+15축근거]) → P2 독립 opus audit(15축 + 15axis-summary 카드 전달) → 통과분 P3 ledger 등록.
- **relationships→corr_prior 방향성 확정**: 2-tier — ① sleeve↔sleeve cross(`cross-and-regime` C1~C12)=corr_prior Σ off-diag 직접(P2 통과분) / ② indicator↔indicator relationships(블록3)=SEED betas factor 경유(IC1 이미). 발견 D unit 불일치 해소. **코드 상세=P2 후 구현 영역**(자문 부적합, 이 세션은 방향성만).
- **이번 세션 완료분**: IC0-R substrate(regime 동적corr 런타임 진입·회귀446) + indicator_ledger(py+8자산 md+status 통합+CLAUDE.md 4-state 규칙). 자율 코드 선결 소진.

## 6. 환경
- python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1`. push 금지. DRY_RUN/execute_trade SACRED. opt-in off byte-identical.
- 임시검증: `.tmp-ic2-sim.py`·`.tmp-ic7-sim.py`(삭제 가능).

## 7. ★누락 검토 결과 (subagent ae5e718a, 4세션 jsonl 대조 2026-06-01) — progress 반영 완료
누락 3 + 설명부족 2 (정상 반영 8):
- **누락①(중대) cross 추가자산 자문**: S2 "cross로 처리 가능한 자산 있는지 자문 확인" — R12에 cross 신규자산 발굴 의제 부재. → R12 §5 추가.
- **누락②(중대) 자산별 국면정의 자문 3R 게이트**: S2 "자산별 국면 정의=다음 세션 자문 3R로 방향성 정하고 진입" — progress엔 regime split PoC 1만, 국면정의 확정 자문 게이트 부재. → P1 앞 "R13 regime 정의 자문 3R" 신설.
- **누락③ 자문 전 사용자 보고**: S2 "자문 대상 넣기 전 사용자 대화 보고" — R12 자율다회만, 승인 체크포인트 없음. → R12 게이트 추가.
- **부족④ 15축 요약본 산출물**: S0 "subagent에 15축 시키려면 기준 별도 요약 전달·구체화" — P1/P2가 "decisions §12 참조"만(압축 후 흩어짐 위험). → P2에 "15축 요약 카드(파일경로·hard축 압축본) 작성" 산출물 명시.
- **부족⑤ 채택분 judge 코드경로 누락점검**: S0 "채택분 yaml만·bge/qwen 누락" — P3 ledger↔W2 judge배선 연결 약함. → "채택분 누락0 점검" 명시.
정상 반영 8: 백테스트 Phase V·subagent 기존리서치 제공·동작현황·실현가능성 진단·관문 구분·IC9 복귀로직·5가지 코드보강·코드 전수확인.

### ★정정 (사용자 2026-06-01 확인 지시 — subagent 오판)
누락①② = **이미 진행·반영됨**: decisions **§1.3**(cross factor: VIX pool 단독·C8/C9 NO-GO) + **§1.4**(regime hardened-soft b(t)) + `_wire/cross-and-regime-research.md`(cross 후보 **C1~C12 자산쌍** + **자산별 regime 정의표**: gold real-rate / reit rate-cycle / crypto FGI×halving / eq_cyclical inflation-clock / eq_intl dollar regime / commodity contango / bond_cash curve). subagent가 jsonl 사용자지시(S2)만 보고 그 후 R1~R11 자문 + _wire 리서치 반영분을 못 봐 '미진행' 오판. **①② 철회 — R13 게이트 신설 불요**(자문 이미 완료). cross-and-regime-research top5 가 P1 진입점.
→ **진짜 잔여 누락 = ③(자문 발사 전 자문대상 사용자 보고)·④(15축 요약카드 산출물 명시)·⑤(P3 ledger↔judge 채택분 누락0 점검)** 3건만.
