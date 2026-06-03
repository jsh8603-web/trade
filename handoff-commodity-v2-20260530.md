---
tags: [type/handoff, domain/commodity, phase/study-system, session/btn-jpdf]
date: 2026-05-30
note: btn-jpdf 세션 commodity v2 작업 인계. ctx 451k/500k cap 90% 도달로 인계 작성. 다음 세션이 동등 수준 재개.
---

# handoff-commodity-v2 (btn-jpdf 세션)

> **세션**: btn-jpdf (commodity v2 작업방). main = btn-Codlearn.
> **상태**: ★v2 산출 완료 + main 보고 송신. main 점검 시 yaml 누락 오판 → 재보고 송신.
> **다음 세션 재개 포인트**: main 응답 수신 → register 통합 또는 추가 라운드 진행.

## 1. 산출물 완전 목록 (D:/projects/Inv/study-research/commodity/)

| 파일 | 크기 | 상태 |
|---|---|---|
| direction.md | 24958 bytes (591줄) | ★ main 승인 완료 (KIT v2 §2-1) |
| study_session.yaml | 40286 bytes (7블록 v2) | ★ 완성 — main 점검 누락 → 재보고 송신 |
| summary.md | 7763 bytes | 사람용 요약 |
| raw/theory-notes.md | 35577 bytes (591줄) | KIT v2 §2-2 학파 정독 |
| raw/validation-summary.md | 12405 bytes | KIT v2 §2-3 검증 요약 |
| raw/v2-validate.py | 11569 bytes | Python 분석 코드 라운드 1 |
| raw/v2-validate-v2.py | 13672 bytes | Python 분석 코드 라운드 2 (H4 fix + H7 multi + H10 + H1) |
| raw/v2-validate-results.json | 2920 bytes | 라운드 1 결과 |
| raw/v2-validate-v2-results.json | 5185 bytes | 라운드 2 결과 |
| raw/round-1-prompt.md + round-1-claude.md + round-1-gemini.md | 자문 R1 raw | |
| raw/round-2-prompt.md + round-2-claude.md + round-2-gemini.md | 자문 R2 raw | |
| raw/round-3-prompt.md + round-3-claude.md + round-3-gemini.md | 자문 R3 raw | |
| raw/code-read-notes.md | v1 작업의 코드 정독 노트 | |
| raw/v1/ | v1 산출 보존 (study_session.yaml + summary.md) | 폐기 X |

## 2. 검증된 실측 (★direction.md prior 정정 반영)

| 가설 | 검증 통계 | 정정 |
|---|---|---|
| H5 Tang-Xiong financialization | pre-2004 0.045 → 2004-2010 0.296 (★6배), Welch p≈0 | prior 0.7→0.85 |
| H4 China copper bellwether | ★lag 12m optimal (spearman 0.40 p=1e-12) vs 3m=0.15 | prior 0.75→0.85, **lag 3m→12m 정정** |
| H7 Hamilton NOI | 30%=1건 부족 / **10%=12건, 12m fwd CFNAI=-0.46 vs normal -0.13** | **threshold 30%→10% 정정** |
| H1 ref (gold 방 정합) | 36m partial mean=-0.074 (강한 음수 X) | prior 0.9→0.55, falsification -0.4→-0.1 mild |
| H3 proxy (DBC vs WTI) | drag -3.6%/yr, fraction<0=50% | DBC contango-resistant 인 한정 검증, CME chain 진짜 검증 = Phase 2 |
| H10 GHR | FRED WCESTUS1 404 (deprecated/ID 변경) | Phase 2 EIA Open Data 직접 |

## 3. 핵심 결정 (재진입 시 보존 필수)

### 3.1 자문 라운드 메타 (3R × 2채널 = 6응답)
- gemini-web R1 (8441자), R2 (8511자), R3 (6851자) — 충실
- claude-web R1 (600자), R2 (330자) = web-search 도중 끊김 → R3 (★14864자, "DO NOT SEARCH" prefix 작동, knowledge-only critique)

### 3.2 claude R3 결정적 critique 7건 (★ direction.md 반영)
1. ★H5 ≠ H8 분리 (financialization = CIT 인덱스 vs MM = active speculator)
2. ★PELT ≠ Bai-Perron 명명 + 이벤트 ±3m confirm = HARKing
3. ★Look-ahead bias (R1·R2 침묵) — ALFRED real-time vintage 의무
4. ★Kilian 2009 SVAR 누락 — Hamilton NOI source-conditional sharpen
5. ★Gorton-Hayashi-Rouwenhorst 2013 통합 (KWB+HK = inventory state variable)
6. ★Two-speed: Quarterly Bai-Perron + online e-CUSUM
7. ★SLEEVE_BLOC 3-group: cyclical(energy+industrial) / defensive(precious) / idiosyncratic(agri) — agri=defensive 거부

### 3.3 main 검토 반영
- ★archetype pooling (부록 B): ticker 독립 학습 X → 4 sub-sleeve archetype prior + soft membership
- ★gold 방 분리: gold = 'precious_gold' sleeve 별도, 본 방 precious = silver/Pt/Pd ('precious_non_gold')
- ★inventory 반사성: days_of_supply 명명 유지 (코드 무변경 (a)안)

## 4. 미해결 / 다음 세션 작업

### 4.1 main 응답 대기
- yaml 정정 보고 송신 후 main 응답:
  - 즉시 register(require_raw=True) 진행 → production wiring
  - 또는 추가 라운드 (Phase 2 collector 도입 후 H2/H3/H9/H10 재검증)

### 4.2 Phase 2 후속 작업 (collector 도입 후)
- CME term structure collector → BGR basis_momentum / roll_yield 진짜 측정
- EIA Open Data → cushing_utilization_pct (H9), days_of_supply
- CFTC COT → MM net long/OI z (H8), CIT (H5 driver Phase 2)
- Kilian SVAR (statsmodels VAR + structural identification) → H7-K
- USDA WASDE + survey consensus → H6
- NOAA ONI ASCII → agri conditioning

### 4.3 dormant confidence_hooks 활성 조건 (블록5)
- h9_storage_limit_nonlinearity: Cushing 가동률 데이터 수집 후 → kill switch 활성
- h7_oil_macro_kilian_decomposition: Kilian SVAR 구현 후
- h10_ghr_inventory_state_variable: EIA + LME + USDA inventory 종합 후
- h11_liquidity_storage_crash: composite, 시스템 통합 후 (Phase 3)

## 5. 환경 / 가용 데이터

- Python 312 `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`
- 패키지: pandas 2.2.3, numpy 2.4.2, scipy 1.17.1, statsmodels 0.14.6, yfinance 1.4.1, pandas-datareader 0.10.0
- FRED key 별도 (pandas-datareader 무키 사용 가능 — fred 일부 시리즈 제한)
- 사용 가능 시리즈: DCOILWTICO/CFNAI/INDPRO/DFII10/DTWEXBGS 정상 / WCESTUS1 404 (EIA 직접 필요)

## 6. ctx / 세션 상태

- model: opus
- ctx-warn long-mode ON (cap 500k, warn 420k)
- 현재 451k (90%, 480k compact 임박)
- session: btn-jpdf

## 7. 재진입 시 첫 작업

다음 세션 시작 시:
1. `D:/projects/Inv/progress-study-system.md` Working Notes 의 commodity ckpt 마커 확인
2. `D:/projects/Inv/study-research/commodity/` 의 모든 파일 존재 검증
3. main(btn-Codlearn) 으로부터 응답 확인 (psmux capture-pane)
4. register 진행 또는 추가 라운드 결정

> ⚠️ raw/v1/ 폐기 금지 (사용자 명시: "이전 산출은 raw 참고용으로 두되")
> ⚠️ KIT v2 §2-3 raw 강제 통과 — direction.md + round-*.md + theory-notes.md + validation-*.md 모두 존재 필요
