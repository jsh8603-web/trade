---
tags: [type/handoff, domain/inv, scope/equity-kr, topic/conditional-ic-sleeve, status/in-progress]
date: 2026-06-05
owner: main (btn-button, opus 1m)
next-action: "★자율주행 11산업 확장 계속. 반도체 파일럿 G-C audit PASS 완료(검증 양식 확립). financial·battery teammate 스폰됨(자율 진행). 다음=auto + Tier3 8산업(AItech·화학·정유·조선·바이오·통신·철강·소비재) teammate 스폰(role=industries/_dispatch-role-template-kr-20260605.md, 반도체 미러). 각 완료시 G-C 독립 audit teammate 스폰(author≠auditor)→hard-fail 0 PASS만 코드화 진입. 전 산업 완료→메인 yaml/ledger 점검→약신호 산업 gemini+claude 자문→Phase7 통합 study_session.yaml→★WIRE5 한국 실매매 배선 코드화(metric_signs·KR peer median·STT·KisClient→stock/order_assembly.py, go-live 사람게이트 미접촉). 막히거나 복잡하면 자문 3R. SSOT=plan-kr-equity-conditional-ic-20260605.md + progress 동명."
resume_priority: "11산업 teammate 스폰 계속(financial/battery 진행 중, auto+Tier3 8 남음) → 각 G-C audit → 코드화. 자율주행 flag on(.autopilot-btn-button.flag)."
---

# handoff — 한국 주식 conditional IC + sleeve (2026-06-05)

## 1. 현재 상태 + 첫 행동
- **반도체 파일럿 G-C audit PASS** (semi-audit 독립: hard_fail 0, 충실, tier=structural_prior_low_confidence). conditional CONFIRMED(tentative): **mom_6/pbr_z KRW_weak**(원화약세 국면 모멘텀역전·저PBR 증폭, walk-forward OOS IS-0.060→OOS-0.155 유지, family_2 interaction OOS t-2.69, OOS-only 시간분리+wild-cluster로 미국 11시나리오 data-mining 함정 아님 확인). rev_1m PARTIAL. 신규지표(재고/CAPEX/R&D/DRAM ASP/size-orth) 측정완료(이연0), 약(ppe_yoy tentative, inv_ratio prior 반증). rev_1m is_n=24 정확(semi-analyst raw 재검증, audit 21은 mom_6 기준 오전이 — 신호별 lookback 차이).
- **첫 행동**: kr-equity 팀 teammate 회수 — financial/battery 진행 중(보고 오면 검수→G-C audit), auto+Tier3 8 미스폰 → role 템플릿으로 스폰. semi-analyst/semi-audit = idle(★KILL 금지).

## 2. 진행 맵 (plan §10 = progress SSOT)
S0✅(plan/progress/reflection PASS) · S1✅(반도체 데이터) · S2~S4 반도체 파일럿✅(measure→walk-forward→S6) · S7 반도체 G-C✅ · **S5 11산업 확장 진행 중**(financial/battery 스폰) · S6 PCA sleeve 미착수 · S8 메인 yaml점검+약신호자문 미착수 · S9 WIRE5 코드화 미착수.

## 3. 사용자 박제 (대화 고유, 전부 준수)
- 구조=대안 C 하이브리드(2층 macro-sleeve 배분 / 3층 12산업 conditional IC). 자문 3R 수렴.
- ★원의도=conditional IC("어느 국면에 어느 지표 → 어느 산업 투자"). 리서치 정독=방향잡기 시작점(기존 비판검토+추가발굴, 무비판채택 금지).
- ★teammate=정식 TeamCreate+Agent(opus 1m), **작업끝나도 KILL 금지**(idle=정상). Agent background ≠ teammate(자동압축 장수명).
- ★지표 절대 이연금지(측정가능 지금, 데이터부재만 data-gate). ★11산업 15축 audit+G-C 독립 audit 필수, audit 안한 산업 코드화 금지. role에 15축+이연금지 명시.
- ★메인 책임: yaml/ledger 점검→약신호 산업 자문→WIRE5 실매매 배선 코드화(go-live 사람게이트). 막히면 자문 3R.
- 자율주행 on, progress 완주. 속도보다 퀄리티. go-live·실주문·push 미접촉.
- ★압축: 작업 완주 전 /compact 금지(사용자 명시). ★최종 압축 직전 progress 상단 "압축금지" 블록 삭제(현재 그 블록은 long-mode on2로 이미 제거됨, 본 핸드오프는 ctx 한계 자동 정리 대비).

## 4. 파일 inventory (절대경로)
- plan: `D:/projects/Inv/plan-kr-equity-conditional-ic-20260605.md` (§4.5 게이트 G-A~F + §8 PCA D1~D7 + §9 invariant + §10 단계)
- progress: `D:/projects/Inv/progress-kr-equity-conditional-ic-20260605.md` (상단 경고 3종: 압축금지[삭제됨]/15축audit게이트/지표이연금지/teammate kill금지 + Working Notes ckpt)
- role 템플릿: `D:/projects/Inv/study-research/eq_kr/industries/_dispatch-role-template-kr-20260605.md`
- 반도체 capsule(검증 양식): `industries/semiconductor/` (.dispatch-role-kr-20260605.md + summary.yaml + 15axis-audit.md + theory-notes + candidate-ledger + research-log + raw-v3/{measure_conditional,measure_fundamentals_cycle,collect_regime,merge_fdr_family}.py + validation-conditional/fundamentals-cycle/merged-fdr json)
- 게이트 SSOT: `study-research/_dispatch-gates.md`(G-A~G-F, G-E 충족) + `_ledger-guide.md`
- 자문 raw: `.consult-kr-sleeve-structure-brief.md` + `~/.claude/.gemini-web-last.md`/`.claude-web-basic-last.md`
- 팀: kr-equity (semi-analyst/semi-audit idle, fin-analyst/bat-analyst 진행). config `~/.claude/teams/kr-equity/config.json`

## 5. 미해결 · 다음
- 11산업 중 auto+Tier3 8 미스폰. 각 teammate→G-C audit→코드화.
- inv_ratio 양 IC(재고순환 가설 반대) = 메커니즘 재해석 후보(candidate-ledger). KRW_strong sign-flip = flip-register(차기 vintage pristine OOS).
- I축 생존편향 PARTIAL(KRX delisted universe = collector_plan high, 통합 후 보강).
- 2층 PCA sleeve 실측(D1~D7) 미착수. WIRE5 코드화 미착수.
- ★메인 ctx 한계로 11산업 동시 관리 분할 필요(다음 세션이 batch별 이어감).

## 6. 자문 종합
- 자문 3R(gemini+claude 병렬) 수렴 = 대안 C 하이브리드. 한국이 미국보다 공통인자(외국인flow·USDKRW) 묶임 더 심함. 반도체=Mag7 격리. 교호 factor×regime만. 학습 논문수=FDR family. PCA 2-pass(D1~D7, cap/eq series가 반도체 식별성 좌우). reflection-verify PASS(누락 0).
- 반도체 G-C audit = 미국 11시나리오 data-mining 함정과 다름 확인(OOS-only 시간분리+wild-cluster 생존).
