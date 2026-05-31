---
tags: [type/self-audit, domain/inv, study/macro, phase/2.5-audit]
date: 2026-05-30
study_id: macro
phase: "2.5 self-audit (STUDY-KIT §2.5 감사 8축)"
note: macro 산출(study_session.yaml/direction.md/theory-notes/validation) 8축 self-audit. 미달 보강 = G(검정력) raw/self_audit_power.py + B(Rank-IC) 실측.
---

# macro self-audit (STUDY-KIT §2.5 감사 8축)

> 결과 요약: 8축 PASS (B·G·H 보강 완료). production 유지 가능.

| 축 | 판정 | 근거 / 보강 |
|---|---|---|
| **A 이론실재성** | ✅ | lens 6 프레임워크 = 실존 정전(Bernanke-Gertler 1995 통화전달 / BGG 1999 금융가속기 / Rey 2013 GFC / Fama-Bliss 1987 term structure / Fisher 1930 / Engle 2002 DCC). raw/round-1·theory-notes 인용. |
| **B 실데이터검증** | ✅(보강) | data/historical **실 일별 n=756, 2021-12-02~2024-12-04, p=6자산**. ⛔합성·시뮬 無. **Rank-IC 실측**(self_audit_power): rate_mom→nasdaq −0.158·→gold −0.116·dollar→gold −0.134 (3/4 이론부호 일치, MDE 초과). 한계=가설1 정식 OOS IC는 macro→sleeve forward 필요(H). |
| **C yaml도출추적** | ✅ | 7블록 전부 raw 추적 — lens→round-1/theory-notes, relationships→validation-findings(CI 실측), confidence_hooks→weight_falsification 코드, code_change_plan→4파일 Read 확인. force_include=2-3 CI 근거. |
| **D PIT·OOS** | ✅ | 전 indicator vintage_policy=point_in_time. 가설0 OOS train60/test40(A−B=+9.9). 한계=단일 split(walk-forward 미적용, H). |
| **E 자문비판+환각** | ✅ | 자문 맹목추종 회피=Markov/DCC를 §8(regime 외생) 위배로 *모델 기각, 벤치마크로만*. 환각 cross-verify: 12 학술인용 전부 정전 논문 확인(knowledge). 현재국면 estimation_note=Gemini forecast(knowledge-cut)→"재검증 대상" 명시. |
| **F 반증+기각기록** | ✅ | 가설2 FAIL(p=0.35) 기록 / 가설6 scope 제외(glasso 무방향) / Markov·DCC 모델기각 / sp500~us10y 매개 확정. validation-findings.md 전부 기록. |
| **G 검정력한계** | ✅(보강) | self_audit_power: AR1≈0→**effective-n≈738/440/292(감쇠 2~5%)** — 자기상관은 제약 아님. **MDE(상관) 0.10~0.16**. ★가설2 p=0.35 정직해석: 약엣지 regime차는 MDE 미만 탐지불가 ↔ 강 직접엣지(\|0.28\|/\|0.21\|/\|0.37\|)는 MDE 초과+CI 좁음+regime 불변=robust. p=0.35는 "진짜 null vs 검정력부족" 구분 못함 명시. 15엣지 동시검정 다중성. |
| **H 미해결의문** | ✅(명시) | 아래 6건 명시. |

## H. 미해결 의문 (명시 — 후속/통합 과제)

1. **가설2 FAIL 의 본질**: partial-corr 네트워크 regime 불변(p=0.35)이 *진짜 구조 안정*인가 *crude
   2-regime(rate-up/down) proxy + MDE 한계* 탓인가. → FRED 펀더멘털 기반 **Investment Clock 4국면**으로
   재검정 필요(현 rate proxy는 정식 4국면 아님). collector(DFII10/VIX/T10YIE) 확보 후.
2. **가설1 정식 OOS Rank-IC e-process 미실행**: macro는 자체 forward return 없음(regime 엔진) →
   macro지표→sleeve forward return IC가 정식 가설1. B의 실측 IC는 in-sample overlapping(자기상관)이라
   대용. → 통합단계(전 sleeve 연결 후) 검증.
3. **walk-forward 미적용**: 가설0 OOS는 단일 60/40 split. Goyal-Welch 권고 expanding-window walk-forward는 미실행.
4. **2축 vs 3축 국면정의 미결**: growth-inflation-policy 3축(8국면)은 driver×국면 vs obs 게이트 정량비교
   후 결정(theory-notes §3). 현 데이터로는 미측정.
5. **7축 driver 미완**: real_rate(DFII10)·VIX·breakeven·dollar 등은 collector 이연 — 현 검증은 가용
   6자산(market proxy)만. Fisher 분해(명목 us10y→real+breakeven)는 데이터 확보 후.
6. **λ(EBIC) 민감도 + 위기국면 dense**: EBIC λ sweep 민감도, 위기국면 상관→1 수렴 시 희소성(가설3) 실패
   가능성 미검정.

## 감사 결론

8축 PASS. 핵심 발견(가설0 PASS 공분산 5배 / 가설2 FAIL 네트워크 regime 불변 / 직접엣지 force-include)은
실데이터·정량 근거 보유. 미달이던 B(Rank-IC 실측)·G(effective-n·MDE)·H(미해결 명시) 보강 완료.
**한계 정직 기재**: 현 결론은 가용 6자산 rate-proxy 기준 — FRED 펀더멘털 4국면 재검정이 최우선 후속(H1·H2·H5).
production 유지 가능, 단 통합단계에서 H 과제 해소 권장.
