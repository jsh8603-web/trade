---
tags: [type/progress, study/eq_us_cyclical, phase/post-M3, topic/industry-regime-delta-matrix]
date: 2026-05-30
plan: ./plan-industry-regime-delta.md
session: btn-common-task
---

# Progress — Industry × Regime δ Matrix

## 진입 스냅샷
- **현재 상태**: S5 본 세션 (2026-05-31) 완료 → main 회신 단계 진입
- **다음 작업**:
  1. main 회신 (B 안 공식 의도 결정 + XLE sub-sleeve 권고 + R15 보강안 8건)
  2. main collector 응답 (EDGAR/Damodaran ERP/GZ EBP/FINNHUB/ALFRED) → 워크룸 study 재진입
  3. ★12축 audit SSOT = `D:/projects/Inv/study-research/AUDIT-GUIDE.md` (사용자 inject 2026-05-31): study = audit-ready 산출, formal audit 실행은 main
- **현재 모델**: opus
- **handoff 박제**: ~/.claude/memory/handoff-btn-common-task-202605311600.md (4 필드 + 액션 매트릭스)
- **★Workflow stale 확정**: `wf_9ce20415-0d2` = 토큰 171.5k 13h 정지 (사용자 inject 2026-05-31). 사용자 지시로 산출분 직접 재수행 (materials/energy/synthesis 본 세션 작성, semi/industrials 기존 산출 활용).

## Steps

- [x] **S1 plan 확정** · `model: opus` ✅ 완료 (`plan-industry-regime-delta.md` 작성, §1~§7)
- [x] **S2 progress 골격** · `model: opus` ✅ 완료
- [x] **S3 Workflow dispatch (4 산업 + verify + synthesis)** · `wf: coding` ✅ dispatch (Run ID wf_9ce20415-0d2)
- [x] **S4 Workflow 결과 회수** · ★stale 확정 (171.5k 13h 정지). 기존 2 산업 산출 (semi/industrials) 활용 + 나머지 2 산업 (materials/energy) 직접 재수행
- [x] **S5 산출 4 종 통합 + synthesis 작성** · `model: opus` ✅ 본 세션 완료
  - `raw/industry-materials-delta.md` (신규)
  - `raw/industry-energy-delta.md` (신규, anti-cyclical hedge 본성 분석)
  - `raw/industry-delta-synthesis.md` (4 산업 통합 + 12축 audit-ready)
  - `raw/industry-delta-metrics.json` (구조화 매트릭스)
- [x] **S6 candidate-ledger 작성** · ★main 정정 지시로 "후보목록 작업큐 전환" 으로 용도 변경
- [~] **S7 collector-request-queue 작성** · merit 후보 전수 식별 + 무료 데이터소스 후보
- [ ] **S8 main 회신 + collector 응답 대기** · synthesis 결과 + B 안 공식 + XLE 분리 + R15.1~R15.8 보강안 박제 회신

## Working Notes

### 2026-05-30 (초기)
- plan §3 5게이트 = SSOT 부재 자체 정의 → main 검토 시 보정 받음
- δ_regime = regime tag 만 (거시 numeric 직접 X) — Belief-Truth 격리
- δ_arch = 펀더멘털 only (EDGAR 적재 후 실측, 현 단계 = 후보 식별)
- 4 산업 = 반도체(SOXX) / 소재(XLB) / 산업재(XLI) / 에너지(XLE)
- 5게이트 G1=n≥30 / G2=Bootstrap CI / G3=James-Stein shrinkage / G4=OOS / G5=domain
- 검증관 3-tier = Tier1 측정 / Tier2 shrinkage / Tier3 도메인

### 2026-05-31 (본 세션, fresh /clear 후 자율 재진입)

**Cycle log**:
- 진입 = handoff-btn-common-task-202605311600.md Read + 사용자 inject 지시 (wf stale 확정 + AUDIT-GUIDE.md 12축 SSOT)
- AUDIT-GUIDE.md Read (12축 = A 이론 / B 실데이터 / C yaml 추적 / D PIT / E 자문비판 / F 반증 / G 검정력 / H 미해결 / I 무결성 / J 경제유의 / K 다중검정 / L 통합상관)
- 기존 산출 2 종 (industry-semi-delta.md / industry-industrials-delta.md) Read, 포맷·미해결 의문 파악
- 신규 2 산출 직접 작성 (materials/energy)
- synthesis 12축 audit-ready 작성

**핵심 발견 1 — 공식 의도 결정**: spec 의 `point = ann_ret × sign(Sharpe_cyc) / 100` (A 안) vs `ann_ret / 100` (B 안). XLE 의 anti-cyclical 본성 (E1 +47.9% sleeve -24.3% / E3 +18.0% sleeve -16.7%) 에서 A 안 적용 시 outperform 을 정 반대 (-0.15 clip floor) 로 표현 ⛔. **B 안 (direction-aware) 채택 의무, 모든 산업 일관**. semi (SOXX) 의 자체 ret 부호 보존 채택과 정합. industrials/materials 는 sleeve cyclical core 라 A·B 차이 안 보였을 뿐.

**핵심 발견 2 — XLE 별도 sub-sleeve 의무**: M3 §3 "cyclical 일괄 처리 시 XLE 분리" 권고를 본 산출에서 reinforce. (a) anti-cyclical hedge 본성 (b) β_oil=+0.41 + R²=0.406 + r_oil=+0.602 single driver dominance (c) within-corr 0.26~0.51 outlier. 3 신호 동시. sub-sleeve = `cyclical_oil_hedge` key 신설 권고.

**핵심 발견 3 — clip saturation 14/16 cells (87.5%)**: clip [-0.15, +0.15] 가 산업×regime swing 폭에 좁다. unclipped median 0.295 (clip 의 ~2배), max 0.887 (SOXX E2, clip 의 5.9배). XLB E4 +0.114 / XLE E4 +0.042 만 magnitude 보존. **synthesis 권고 = 옵션 C** (cap 유지 + XLE/SOXX 별도 channel).

**핵심 발견 4 — G3 James-Stein λ ≈ 1.0**: 산업 간 이질성 (between σ²) 이 cell within σ² 대비 압도적 → shrinkage 효과 미미. XLE 분리 후 3 산업 λ' ~0.93~1.0. cyclical_core (XLI/XLB) 만 partial pool 권고, XLE/SOXX = no shrinkage.

**미해결 (main 합의 의무)**:
1. ★★ 공식 의도 = B 안 (direction-aware) 채택 확정
2. clip 범위 옵션 (A 확장 / B 산업별 / C 별도 channel) — 권고 C
3. XLE / SOXX sub-sleeve 분리 구현 방식 (composed_weights 안 또는 별도 sleeve allocation key)
4. R15.5 δ_arch 후보 23 종 등록 + collector 적재 우선순위
5. Verify stage 실행 주체/시점 (stationary bootstrap + Bonferroni + leave-one-epoch-out)
6. ALFRED us10y vintage (D축 보강) — main 인프라
7. 장기 frame 확장 (GFC/COVID/shale revolution) robustness

**12축 audit-ready 자체 점검**: B/I PASS, C PENDING (yaml 미작성, R15 보강안 명시), D PARTIAL (ALFRED 미적용), E~L 정상. hard-fail risk 없음 (B/I 코어 PASS).

**Trust tier label**: `structural_prior_low_confidence` (frame 한정 3년 + n<30 monthly 환산 (E3) + 정확 bootstrap 미산출 + EDGAR 미적재). validated alpha 조건 (OOS Rank-IC>0.03 + t-stat>2.0 SE 보정) 미달.

### 2026-05-31 (cycle 2 — idle 회피 사전조사)

**진입**: main 회신 수신 ("산업 δ 매트릭스 완료 수신, 7 합의건 순차 회신 예정, 그동안 item6/item7 사전조사 idle 금지"). 작업 = 독립조사 2건 + 결과 1줄 보고.

**산출**:
- `raw/pit-vintage-prescan.md` (item6 ALFRED)
- `raw/long-frame-prescan.md` (item7 장기 frame)

**핵심 발견 5 — item6 ALFRED vintage**: M3 거시연관 driver 3종 (us10y/dxy/oil) = real-time market data 라 revision 영향 zero → PIT 정합 (ALFRED 적용 skip 가능). critical 시리즈 = monthly economic indicators 5종 (CFNAI/NEWORDER/AMTMNO/BUSINV/DGORDER). API = FRED `series/observations` + `realtime_start`/`realtime_end` 파라미터. HY OAS (BAMLH0A0HYM2) 2023-05~ 가용 → 장기 frame 활용 불가 (eq_us_defensive H3 ERROR 와 같은 패턴 회피용 caveat).

**핵심 발견 6 — item7 장기 frame robustness**: 4 산업 공통 가용 = 2001-07-13 (SOXX 출시) ~ 2026-05-29 = **24.8년**. GFC (L3 2007-10~2009-03) + COVID (L8/L9 2020) + shale revolution (L5 2014-15) 다 포함. 추가 epoch 후보 9개 식별 (L1 dotcom 후폭풍 ~ L14 post-M3). robustness 시나리오 5종 (A 전체회귀 / B rolling 60M / C LOEO CV / D regime transferability / E Bai-Perron break detection). 단기 즉시 가능 = 시나리오 A. ★주요 risk = ETF holdings drift (SOXX NVDA dominant post-2023 / XLE shale-pure-play post-2014).

**상태**: main 회신 + 1줄 보고 완료. 워크룸 다시 idle — 나머지 5건 (공식 B / clip C / XLE-SOXX 분리 구현 / δ_arch 등록 / Verify 주체) main 회신 대기.

## 회신 양식 (main)

```
경로: raw/industry-{semi,materials,industrials,energy}-delta.md + raw/industry-delta-synthesis.md
핵심:
  - δ_regime 매트릭스 (4 산업 × 4 epoch)
  - δ_arch 후보 (4 산업 × 펀더멘털)
  - 5게이트 통과 cell 비율
  - yaml R15 weight_card 보강안 N건
```
