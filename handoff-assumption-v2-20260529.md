---
tags: [type/handoff, domain/inv, phase/II, track/T3, topic/assumption-lifecycle-v2]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-assumption-v2-axes.md
progress: ./progress-assumption-v2.md
note: 가정 라이프사이클 v2 재개용 핸드오프 (in-flight 상태). 본체 = plan + progress.
---

# 핸드오프 — 가정 라이프사이클 v2 (재개용)

> 본체 SSOT = `plan-assumption-v2-axes.md` + `progress-assumption-v2.md`. 본 파일 = in-flight 상태 + 재개 다음행동만.

## 재개 진입점 (순서)
1. `progress-assumption-v2.md` — 요청14→구현 GATE + 세션 바인딩 축(IA/BB/CL) + 6축×3도메인 grid + Phase.
2. `plan-assumption-v2-axes.md` — 6축·목적 §2.1·자문R1 반영 §2.2·통합 method §3.5·세션분배 §4·자문지침 §5.

## 현 상태 (2026-05-29)
- **P0 설계+분배 완료.**
- **P1 진행중**: btn-Inv·btn-button 디스패치 완료(exit 0). 각자 바인딩 축으로 ≤5R 자문+구현 자율 진행. 보고 도착 시 btn-Codlearn 통합.
- **내 슬라이스 자문**: gemini-web R1 완료(반영=plan §2.2, raw=`~/.claude/.gemini-web-last.md`). ⚠️ **claude-web R1 미실행** — 재개 시 여기부터. brief=`.consult-codlearn-R1-brief.txt`.

## 재개 다음 행동 (btn-Codlearn)
1. claude-web R1 실행 + gemini 와 ≤5R 수렴(중요치 않은 상세만 나오면 조기 종료).
2. `core/assume/` 골격: **S14 AssumptionCard = decoupling-case 일반화** (context[event/industry/regime+기간] + indicator/metric + baseline 의미 + decoupling 조건[보조지표] + falsification_metric + version, generic). 계층적 조건화(regime>archetype>period), Card 통합(A안).
3. 워커 보고분부터 통합. CL-4 closed-loop GATE = 결정→log→학습→검증→변경→재주입 가 거시 AND 주식 AND 상품 전부 통과.
4. ⛔ progress 14 요청행 + 18 셀 GATE 전부 self-test 증거로 [x] 확인 후에만 "완료". (직전 실패 = 부분구현 누락)

## 핵심 결정 (압축 survive)
- **통합 method** = 거시 `core/brain/indicator_event_correlation.py` decoupling-case 패턴(baseline→trigger→override + correction 학습)이 template. 주식(공정전환기 PER 착시)·상품(공급과잉 COT) 동형. 현재 live 미연결+6 case 정적 → 일반화+학습루프 연결+발견가능화가 핵심 빌드.
- **6축** = A학습 B기준화 C주입 D검증 E변경 F거버넌스. **목적**(§2.1) = 지표→상황정의→정의대로 안따라감 감지→그 기간엔 정의 S→S' 전환 학습→기준조정→재적용. 3도메인 동형(지표만 다름).
- **사용자 확정**: Q1 모의API→실거래까지 / Q2 3도메인 동순위 / Q3 지표의미승격(6 case)+open-ended regime 발견(bnpy) 둘다 / Q4 판정 L1 결정론+L2 Qwen+L3 BGE+DCF@agent 전부.
- **gemini R1**: 단순 cross 금지(차원저주)→계층적 조건화 / Card 통합(A안, ATMS 단일엔진) / L1=veto floor·L2/L3=L1 통과분 confirm / DCF=독립 rule veto(dual-gate) / ★실패=거시 변경 시 cascade rollback 폭주(gridlock)→grace period+lazy eval.
- **현 구현 맵**: 주식~70%(엔진+shadow), 거시~40%(고정-K·decoupling 정적·indicator_event_correlation live 미연결), 상품~5%(전무), core/assume=0%, data_contract/lineage=0%. 통계엔진(assumption_stats·detectors·online_fdr 메모리) 실재.
- **워커**: btn-Inv(cwd=Inv, 축 IA: 데이터·data_contract·lineage·online_fdr 영속·상품데이터·모의API outcome·shadow→live), btn-button(cwd=button→cd Inv, 축 BB: 거시 6case 버전드+live연결·open-ended regime·commodity archetype·regime-conditional 검증).

## 참고 문서
plan/progress + macro.md·quant.md(도메인 상세, 코드 반영됨) + FINDINGS-phase2-sector-rule-framework.md(8R 자문·bnpy/Damodaran 리소스) + indicator_event_correlation.py+MACRO_CORRELATION_BACKGROUND.md(거시 method) + handoff-T3-assumption-integration(S14~S20 설계) + .consult-R1-{claude,gemini}.txt(belief revision) + .audit-{assumption,macro}-prompts.txt(사용자 프롬프트 원본).
