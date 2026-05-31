# original-user-prompts — eq_kr 사용자 원본 작업지시 prompt 전문 (2026-05-30)

> main 이 미국주식 (eq_us) 또는 다른 idle 세션 dispatch 시 동일 prompt 시퀀스로 사용.
> 본 작업방 (btn-diary, eq_kr) 이 받은 사용자 직접 + main routed prompt 전체.

## A. 자동 라우팅 (main → eq_kr, auto-source psmux-send.sh)

### A1. 초기 dispatch (eq_kr 시작 지시)
```
[main→eq_kr] 너는 종목 스터디 작업방이다. study_id=eq_kr(한국주식).
작업디렉토리=D:/projects/Inv (모든 경로 이 기준). 지금 D:/projects/Inv/STUDY-KIT.md 를
끝까지 정독하고, §0 행동규칙+§2 ★작업순서 3단계대로 자율로 D:/projects/Inv/study-research/eq_kr/
study_session.yaml(7블록)+summary.md+raw/ 를 완성해라. 핵심 3단계:
①투자 일반론·리포트·OSS 지식으로 lens(블록1)를 먼저 완성
→ ②우리 수집기(§7)의 과거 실데이터로 블록2~4 분석(없는 자료만 블록6 으로 main 요청, 있다 전제로 멈추지 말 것)
→ ③lens 는 가변: 분석하며 확신/거부 flag(블록5)로 신뢰도·가중치 갱신경로를 명시.
§6 주식 통일 하드룰 준수.
§0: 자율·idle 금지, 막히면 코드Read→/gemini-web+/claude-web 자문→직접 WebSearch/WebFetch 순
자력해결(9세션 자문 경합 시 직접리서치 폴백 허용).
질문·완료보고는 btn-Codlearn 에만:
bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[eq_kr→main] 내용".
완료되면 main 이 G1~G6 골격으로 production wiring 한다. 지금 시작.
```

### A2. Calculating hang 우려 (재진입)
```
[main→eq_kr] Calculating 타이머가 멈춰있었다(generation hang). 무거운 분석 .py 는 Bash python 으로
직접 실행해 결과만 받아라. RegimeGlasso 전체 적합 대신 상관행렬·regime별 partial-corr 만 먼저 뽑아도
§2 ② 충족된다. 진행 중이면 무시. idle 금지 — study-research/eq_kr/study_session.yaml(7블록)
완성해서 보고.
```

### A3. ★v2 재작업 지시 (자문 그대로 코드화 거부)
```
[main→eq_kr] ★재작업 지시(v2). 이전 산출은 자문을 그대로 코드화하고 끝낸 것이라 사용자가 다시 하라 했다.
너는 eq_kr(한국주식) 담당 전문 애널리스트가 된다. D:/projects/Inv/STUDY-KIT.md §2(v2)를 다시 정독하고
아래 순서로 진행:
[2-1 방향성·자문 다회 — ★끝나면 멈추고 승인 대기]
/gemini-web + /claude-web 다회(3~7R 수렴)로 ①이론 수집방향 ②이론 검증방향 ③핵심 가설초안(반증조건 포함)을
완전성 올려 잡아라. 산출=study-research/eq_kr/direction.md + raw/round-{N}.md(라운드별 누적).
자문 채널 경합·타임아웃이면 WebSearch/WebFetch 폴백(과도한 동시 자문 자제, 1~2R씩).
⛔ 여기서 멈추고 main(btn-Codlearn)에 direction.md 보고 → 내 승인 전 2-2 진입 금지(이 멈춤은 idle 아님).
[승인 후] 2-2 이론학습→raw/theory-notes.md, 2-3 실데이터 시계열 검증→코드화→raw/validation-*.md + study_session.yaml.
이전 study_session.yaml 등은 raw 참고용으로 두되(폐기X), 바탕 raw(round-*/theory-notes/validation-*) 없으면
main이 yaml 거부한다. 지금 2-1부터 시작.
```

### A4. main 의 §2.5 8축 감사 신설 박제
```
[main→eq_kr] 2-1 계속. ★STUDY-KIT §2.5 감사 8축 신설(사용자 지시 박제) — 보고 전 self-audit 의무:
A이론실재성 / B실데이터검증(실측 n·기간·p·Rank-IC, ⛔합성·시뮬 데이터 금지) /
C yaml도출추적성 / D PIT·OOS / E자문비판+환각cross-verify / F반증가능+기각기록 /
G검정력한계 / H미해결의문. 한 축 미달=불충분→보강.
거버넌스↛PBR 학술 반증 발견 좋음(F축) → R2/R3 자문 수렴해 direction.md(①이론수집 ②검증방향 ③가설 반증조건)
산출 후 ★승인 대기. 8축은 2-3 최종 목표.
```

### A5. 주식 동적가중 보정 + 누락 critical 지표
```
[main] 주식 동적가중 보정 — ★너희 세션이 산업별 subagent 나눠 작업. 누락 critical 지표(우선순위):
USD/KRW > 외국인 순매수 플로우 > 중국 credit impulse > 월간수출/반도체(DRAM 현물·SOX) 사이클.
자문 R2: sleeve=팩터노출 정의, 거시 배분레이어 전담·종목레이어 펀더멘털, 순수 down-only 유지.
★현 eq_kr은 governance/PBR만으로 얇음(거버넌스↛PBR 학술 반증). 과제: 한국 산업별(반도체/2차전지/자동차/금융)
regime·수출사이클별 δ 실측 + 위 거시지표 추가. 산업별 subagent 분할. ⛔점추정 prior 박제 금지, small-n 5게이트.
```

## B. 사용자 직접 prompt (chat input)

### B1. ★절차 재정렬 (평가축·자문·plan 선행)
```
넌 subagent 가 준수해야하는 핵심 축을 정의해야 하고, 결과가 회수되면 opus1m subagent로 사전에 작성된
해당 축대로 평가기준을 제시하여 평가하게 해야한다 (너가 직접 하는 것 금지) 그리고 이 모든걸 시작하기
전에, 어떤 산업별로 나눌지를 포함한 너가 생각하는 방법론, 최종 구현 결과 등을 3r 자문 돌리고 시작.
자문이 끝나면, 사용자 요청대로 이행되도록 plan progress 만들고 시작
```

### B2. ★ 미국 주식 + 메인 섹터
```
미국 주식도 해야한다. 자문도 별도로 하던지.
자문 결과에서 나오겠지만 메인 주식 섹터들은 놓치지 말아야한다. ai tech 화학 정유 등등등등
```

### B3. ★ Inv frame 정합
```
Inv 에 claude.md 에 있는 세션들에게 자산군별 리서치 시키는 프레임을 확인하고, 유사한 내용으로 적용해라.
(개별 세션에게 시키고 메인에서 별도 sub로 감사하는 프레임)
```

### B4. ★ 방법론 전달 (메인 baseline 용)
```
메인이 너가 하는 방법론 그대로 적용할 수 있게 너가 할거 정리되고나면, (너 plan progress 작성 직후에)
그대로 참고해서 할 수 있도록 전달해.
```

## C. 미국주식 (eq_us) 세션 dispatch 시 권고 — main 가 어떻게 쓰나

### 옵션 1: A1 prompt 의 study_id 만 교체
`study_id=eq_kr(한국주식)` → `study_id=eq_us(미국주식)` + 작업디렉토리 동일 + Inv frame 정합 + AUDIT-GUIDE 12축.

### 옵션 2: A3+A4+B1+B2+B3+B4 통합 prompt (v2 절차 즉시 진입)
미국주식 세션이 본 작업방의 v2 절차 7 Phase 를 처음부터 따르도록 통합 prompt 제공. 본 작업방의
`methodology-final-for-main-dispatch.md` (별 파일) 가 그 정리본.

### ★ 강조 박제 5 금지 (모든 자산군 공통)
1. 점추정 prior 박제 금지
2. 합성·시뮬 데이터 금지
3. 자문 그대로 코드화 금지
4. Single-source 단정 금지
5. Small-N 단정 금지

### ★ supervisor 직접 평가 ★금지★ — 별 평가 subagent (opus 1m) 위임 + AUDIT-GUIDE 12축

### ★ analyst-level lens 다운그레이드 금지 — 시스템 못 받으면 파이프라인 업그레이드
