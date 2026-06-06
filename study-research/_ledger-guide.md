---
tags: [type/ledger-guide, domain/inv, scope/equity-industry, status/active]
date: 2026-06-03
owner: main (btn-button, opus 1m)
purpose: |
  주식 산업 섹터별 ledger·리서치 기록 방법론 SSOT. 그동안 주식 섹터 기록이 코인
  (crypto/candidate-ledger.md) 대비 부실 → 같은 삽질 반복. 각 섹터 capsule 에 ledger 2종을
  의무화해 "뭘 왜 탐구했고, 뭐가 왜 빠졌고, 어디서 막혀 어떻게 풀었나" 를 코인 수준으로 영속.
reference: crypto/candidate-ledger.md (양식 원본), _dispatch-gates.md G-D (완료 조건)
---

# 주식 섹터 ledger 기록 방법론

> **확정 framing (2026-06-03)**: 주식 섹터 = 한국/미국 각 섹터별 capsule 디렉토리에 ledger 영속.
> 코인은 채택/이연/미채택/falsifier/자산화 enum 을 1파일로 집약 → 다음 세션이 한눈에 재현.
> 주식도 동일 수준 강제. **목적 = 같은 탐구 삽질 재발 방지 (상세 작성이 핵심).**

## 1. 디렉토리 구조 (capsule)

각 섹터 = self-contained capsule:
```
study-research/{eq_kr|eq_us}/industries/{sector}/
  ├ summary.yaml              # 채택 지표 + 검증 결과 (yaml 통합 source)
  ├ summary.md               # 사람이 읽는 요약
  ├ theory-notes.md          # S1 학술 ground
  ├ validation-*.md          # S2 실측 (fundamental/macro/industry/cross-sectional)
  ├ 15axis-audit.md          # S6 독립 audit (15축 3컬럼 + hard-fail)
  ├ round-N.md               # S3 외부검토 라운드
  ├ candidate-ledger.md      # ★신규 의무 — 지표 후보 전체 원장
  ├ research-log.md          # ★신규 의무 — 탐구 과정 시계열 로그
  └ raw-v3/                  # 수집기·측정 코드 + json/parquet
```
신규 2파일(`candidate-ledger.md` + `research-log.md`) = G-D 완료 조건.

## 2. candidate-ledger.md 양식 (코인 미러)

> 자문(R1~Rn)·이론·실측에서 거론된 **모든** 지표 후보 + 채택/이연/미채택 + 사유.

```markdown
---
tags: [type/candidate-ledger, domain/equity, sector/{sector}, purpose/easy-review]
date: YYYY-MM-DD
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# {sector} 지표 후보 원장

## ✅ 채택 (yaml 등록 + 검증 통과)
| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | | 검증된 정량 규칙 |
| memory | | 다음 cycle 자문 prior 정정 입력 |
| observe-only | | N 더 누적 후 promotion 결정 |
| evt | | promotion-log ERROR 후보 (자문 정정 사례 ★G-B 재자문 결과) |
| pointer | | 다음 세션 SSOT 정독 우선순위 |
```

## 3. research-log.md 양식 (탐구 과정 — ★삽질 방지 핵심)

> candidate-ledger 가 "결과 원장"이면 research-log 는 "과정 로그". **막힌 지점·해결법·환경 함정**을
> 시계열로 박제 → 다음 세션이 같은 벽에 안 부딪힘. 코인엔 이게 흩어져 있어 본 양식으로 집약.

```markdown
---
tags: [type/research-log, domain/equity, sector/{sector}]
date: YYYY-MM-DD
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# {sector} 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
예) PER | EDGAR XBRL companyconcept | accept ts lag 적용 OK | ✅ | Large accel 10-K 60d/10-Q 40d, near-duplicate 강상관 → M_eff 보정 |

## 막힘·해결 로그 (시계열)
- [날짜시각] 막힘: {무엇이 왜} → 진단: {root cause} → 해결: {어떻게} → 교훈: {재발방지}
예) collect 4회 막힘 → background 15min+ 환경 미유지 → foreground+incremental+resume → "백그라운드 장시간 금지"

## 측정 방법 결정 로그
- {축/지표}: {왜 이 방법 선택, 대안 기각 사유, 자문 반영 여부}

## 미해결 / 다음 세션 우선 작업
1. ...
```

## 4. 기록 규율 (invariant)
- **append-only 시계열**: research-log 막힘 로그는 덮어쓰기 금지, 시각 prefix append.
- **상세 > 간결**: 사유는 1줄이라도 "왜" 박제 (예: "유료 게이트" 가 아니라 "Glassnode 유료 + MVRV 와 realized-value 중복 의심").
- **자문 결과 = evt enum 의무**: G-B 재자문으로 정정된 가설(예: 미국 BY 방법결함)은 candidate-ledger 자산화 enum `evt` + research-log 측정결정 로그 동시 기록.
- **역방향 박제**: 자문이 "기각" 한 항목이 yaml 에 잘못 살아있지 않은지 = candidate-ledger ❌ 섹션과 summary.yaml 대조 의무.
