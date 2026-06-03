---
tags: [handoff, inv, production-pivot, phase2, harness2]
date: 2026-05-29
---

# Handoff — Inv 프로덕션 전환 + Phase 2 진행 (2026-05-29)

> 재개 시 이 문서 + progress.md ckpt-202605290115 로 재개. 팀 h2wf-Inv-p0 가동 중(메인 죽으면 teammate 죽음 → 재시작 시 재스폰).

## 1. 프로덕션 전환 (사용자 4 메시지 확정, 2026-05-29)
- **mock-only 개념 완전 폐기** — 프로덕션 품질로 한 번에 빌드, **두 번 일 금지**.
- **실 라이브러리 설치 완료**: `pip install cvxpy PyPortfolioOpt riskfolio-lib` exit 0. 사이징=PyPortfolioOpt `risk_models.CovarianceShrinkage.ledoit_wolf()`(SSOT, BL 동일) + Riskfolio `HCPortfolio.optimization(model='HRP',codependence='tail',w_max=0.10)`. ⛔ sklearn/scipy 대체 금지(폐기된 mock 안).
- **DB = 로컬 PostgreSQL(psycopg2-binary 직접), Supabase 클라우드 폐기** — 사유: 로컬 GPU 환경(da 8787 ONNX-DML·ollama·torch) 필수라 클라우드 무용. near_miss_veto=로컬 PG 테이블 + jsonl 감사 병행.
- **.env = 신규 생성 예정** — ⛔ 기존 coin repo .env 사용 금지. 현재까지 실 자격증명 = 사용자 Claude OAuth(~/.claude/.credentials.json) 뿐. (Glob/Bash .env 접근 시도 권한거부됨 — .env 미존재로 추정.)
- **DRY_RUN/EMERGENCY_STOP 안전장치 유지**(가정): 코드=프로덕션 wiring, 실주문 go-live=사용자 명시 시. ⚠️ 사용자 미확정 — 재개 시 확인 권장.

## 2. Phase 2 상태 (공통 리스크 게이트)
- **SO-1 완료**: commit `9b98abb` core/risk_gate.py RiskGate hard rule(stop -5/-10 이중·일일한도 halt·max weight·turnover·min_holding) + near_miss_veto jsonl. Verifier PASSED(20 tests, LLM import 0, Phase1 92t 회귀 0). **프로덕션 유효**(외부의존 0·결정론) — 단 near_miss_veto Supabase 아닌 jsonl이라, PG 영속 추가는 .env/PG 준비 시(SO-6 통합 또는 별도).
- **SO-2~6 미착수**. Worker는 SO-1 후 STOP 지시로 SO-2 전 halt(idle).
- **재개 절차**: Worker/Verifier 살아있으면 SendMessage 로 SO-2 production 가동(재스폰 불요). 죽었으면 handoff-inv-phase1 절차로 재스폰(teammate-spawn spawn) + resume_baseline phase:2 확인.

## 3. 문서 갱신 상태 (production 반영)
- ✅ taskspec-phase-2.txt: SACRED production화(실라이브러리·로컬PG·신규.env·DRY_RUN) + SO-5(PyPortfolioOpt/Riskfolio) + 라이브러리 줄 완료.
- ⏳ **미완(재개 시 먼저)**: harness2.md SACRED 줄(아직 mock-only) + Phase2 SO-5 행(아직 sklearn/scipy) 갱신 필요. plan.md + progress.md 상단 PRODUCTION MANDATE 명시 필요(사용자 "Plan progress 등에도 명시" 지시).
- ⏳ SO-3 reembed_to_bge.py(Phase1) = Supabase REST → psycopg2 로컬 PG 리트로핏 필요(.env/PG 준비 시). improvement-registry 등록 대상.

## 4. 재개 직후 To-Do (순서)
1. harness2.md SACRED + SO-5 행 production 갱신(taskspec-2 와 동일 내용).
2. plan.md + progress.md 상단 PRODUCTION MANDATE 블록 추가.
3. Worker SendMessage: SO-2(상관캡+multiplier) production 착수 → SO-3(kill switch)→4(precedence)→5(PyPortfolioOpt/Riskfolio 사이징)→6(우회불가+격리+통합). Verifier 폴링 재개.
4. DRY_RUN 안전장치 유지 여부 사용자 확인(미확정).
5. requirements.txt 에 cvxpy·PyPortfolioOpt·riskfolio-lib 추가(설치됨, 명시 누락). gymnasium·torch·stable-baselines3 미설치(RL 테스트 8 에러)=Phase5 또는 필요 시.

## 5. Phase 1 완료(직전, 참고)
SO-1~6 PASS + Gate Review 3-reviewer + 핫픽스 a4cadb0(embedder assert→ValueError·llm_worker ZMQ 제네릭) + SR Gate G PASS. git HEAD(Phase1)=a4cadb0. harness2.phase1-brain.done.md 백업. improvement-registry 9행(PATTERN 4·DEFER 3·PROCESS 2).
