---
tags: [type/handoff, study_id/reit, phase/M3-pending, session/btn-GCP]
date: 2026-05-30
session_ckpt: ckpt-202605301215:btn-GCP
note: btn-GCP 세션 426k 85% ctx-warn 진입 시점 인계. M3 macro linkage 분석 직전 stop.
---

# REIT 세션 인계 — M3 macro linkage 진행 직전 stop

## 진행 완료 상태 (재개 시 skip 가능)

### 2-1 자문 다회 (3R 수렴) — 승인 완료
- `direction.md` + `raw/round-1.md` (이론수집) + `round-2.md` (학술 inconclusive + window flip) + `round-3.md` (5 가설 + 반증조건)
- main 승인 받음.

### 2-2 이론 학습 + 환각 검증 — 승인 완료
- `raw/theory-notes.md` — pricing principle (DCF), 4 approach, 학설 정리, Nareit primary 데이터.
- 환각 검증 ✅ 통과:
  - 2024 industrial -17.7% Nareit webinar recap CONFIRMED
  - 243bp Q3 2022 peak Nareit market commentary CONFIRMED
  - ⚠ Q4 2024 120bp = primary 미확인 (Q4'23 123bp 와 혼동) → v2 baseline 에서 제외 (E축)
- NEW 발견:
  - Q2 2023 sub-sector spread: Office 259 / Apartment 194 / Retail 150 / Industrial 93 bp
  - Private appraisal sticky +15bp/Q × 7Q
  - AFFO/FFO sector standard: triple-net 95-100% / industrial 85-95% / office 70-85%

### 2-3 5 validation 완료
- `raw/validation-H4.md` — H4 CONFIRMED (window flip Kendall τ=0.077, swap 88%, n=77)
- `raw/validation-H1.md` — H1 **REJECTED sign mismatch** (mean Rank-IC +0.240, z+3.18, n=23 rate-shock entries) — long-WALT 가 *outperform*
- `raw/validation-H2.md` — H2 PARTIAL (VNQ proxy CONFIRMED, ρ=-0.361, deep-discount 275 obs +32.5% mean fwd 12m / 2008 GFC 2 episode -35/-43% reject 사례)
- `raw/validation-H3.md` — H3 **REJECTED sign mismatch** (mean Rank-IC -0.117, z-2.09) — long-WAM underperform, H1 과 부호 반대
- `raw/validation-H5.md` — H5 CONFIRMED 반증 (mean inter-regime ρ=+0.087 random / Reflation Industrial avg rank 4.83 mid)
- script: `raw/scripts/h4_window_flip.py / h1_long_walt_cross_section.py / h2_mean_revert_proxy.py / h3_h5_combined.py` + .log

### study_session.yaml v2 작성 완료 (861 lines, 48 KB)
- v1 (819 lines) = `study_session.yaml.v1.bak` 백업
- `raw/evidence-map.md` = 모든 yaml 수치 → validation file + script 추적표 (C축 hard pass)
- 8 block (v2 추가 `block8 self_audit_12_axis`)
- AUDIT-GUIDE 12축 self-audit 결과 yaml 내부 박제
- Tier 라벨 = "structural prior (저신뢰)"
- main 의 opus 독립 감사관 별도 12축 감사 진행 예정

## 미완 — 다음 세션 재개 포인트 (M3 macro linkage)

### 받은 지시
`[M3 재송신] study-research/macro/timeline.md 읽고 §4 M3 가이드대로 네 sleeve 거시연관 분석`

### macro/timeline.md §4 M3 가이드 4 step
1. **regime별 종목 수익률 분해** — E1~E4 epoch 별 REIT (VNQ + 9 sub-sector) 평균수익·변동성
   - E1 긴축충격 2022Q1~Q3 (rate↑↑·dollar↑↑·risk-off)
   - E2 전환·반등 2022Q4~2023Q2 (rate 고원→완화 + AI 성장 + SVB)
   - E3 금리재상승 2023Q3 (rate↑·oil↑)
   - E4 pivot·인하 2023Q4~2024 (rate↓·dollar↓·gold↑)
2. **거시 driver loading** — REIT ~ [Δus10y (bp), Δlog(DXY), Δlog(WTI)] 회귀
   - ★ M1 발견: 주식 rate loading ≈ 0, dollar loading rate-up 2배 → REIT 도 검증
   - 전체 + epoch 조건부 loading
3. **cross-asset-class vs within-sleeve 구분** — REIT factor loading (cross-asset) vs 9 sub-sector 간 평균 상관 (within-sleeve = equity factor)
4. main 회신 (`bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn 메시지`)

### 데이터 source (이미 가용)
- VNQ + 9 sub-sector representative ticker (PLD/AVB/BXP/WELL/EQIX/PSA/SPG/HST/AMT) Yahoo 2018+
- FRED DGS10 (1962+, daily)
- FRED DXY 또는 yahoo 'DX-Y.NYB' (dollar index)
- WTI yahoo 'CL=F' 또는 FRED 'DCOILWTICO'
- macro raw 참조: `D:/projects/Inv/study-research/macro/raw/m1_factor_linkage.py` (방법론 참조)
- macro raw: `m1-timeline.csv` (분기 13)

### 다음 세션 첫 action
1. `Read D:/projects/Inv/study-research/macro/raw/m1_factor_linkage.py` — 방법론 정확 파악
2. `Read D:/projects/Inv/study-research/macro/raw/m1-findings.md` — M1 발견 (주식 rate loading≈0 / dollar loading) 정확 인용
3. `Write D:/projects/Inv/study-research/reit/raw/scripts/m3_macro_linkage.py` — REIT factor regression
4. 결과 → `raw/m3-macro-linkage.md` (regime epoch + factor loading + cross-asset vs within-sleeve)
5. main 회신 (psmux-send)

### 미해결 결정
- DXY source: yahoo 'DX-Y.NYB' (간단) vs FRED 'DTWEXBGS' (broad) — yahoo 우선 시도 후 FRED 차선
- WTI: yahoo 'CL=F' 우선
- Δus10y 단위: bp (M1 timeline 과 일치)
- regime label: M1 의 E1~E4 epoch 그대로 사용 (자기 데이터로 재검증은 후속)

## 열어본 파일 (top 10)
- D:/projects/Inv/STUDY-KIT.md (v2 §2.5)
- D:/projects/Inv/study-research/AUDIT-GUIDE.md (12축)
- D:/projects/Inv/study-research/macro/timeline.md (M1 분기·epoch)
- D:/projects/Inv/core/data/weight_panel.py + structure/conditional_correlation.py + assume/weight_card.py + weight_falsification.py + weight_cycle.py (4단계 코드)
- D:/projects/Inv/core/brain/fred_adapter.py + brain/regime_to_weights.py
- D:/projects/Inv/stock/data/edgar_provider.py + scripts/train_weights.py

## 외부 자문 결과 요약
- Nareit webinar recap: 2024 industrial -17.7% / data center +25.2% / healthcare +24.2% / office +21.5%
- Nareit market commentary: cap rate spread Q3 2022 = 243bp peak / Q4 2023 = 123bp / Q2 2024 = 130bp / Q3 2024 = 60bp est. Historical 2009 Q1 372bp reduction → +124.7% outperform (mechanism)
- Q2 2023 sub-sector spread: Office 259 / Apt 194 / Retail 150 / Industrial 93 bp
- 학술 합의: REIT-rate negative (Giliberto-Shulman 2017 + 3 earlier) but 정량 inconclusive
- Shulman UCLA PDF binary corrupt + Researchgate 403 → paper 본문 직접 인용 한계

## 산출 파일 누적 cross-ref
study-research/reit/:
- direction.md, study_session.yaml (v2), study_session.yaml.v1.bak
- raw/round-1.md, round-2.md, round-3.md
- raw/theory-notes.md
- raw/validation-H1.md, H2.md, H3.md, H4.md, H5.md
- raw/evidence-map.md
- raw/lens-rationale.md, data-availability-audit.md (v1 참고)
- raw/scripts/h4_window_flip.py, h1_long_walt_cross_section.py, h2_mean_revert_proxy.py, h3_h5_combined.py
- raw/scripts/*.log
- handoff-m3-macro-linkage-20260530.md (본 파일)

~/.claude/docs/archive/research-raw/:
- reit-pricing-theory-native-20260530.txt
- reit-validation-methodology-native-20260530.txt
- reit-q1-2025-cross-verify-native-20260530.txt
- reit-2024-subsector-verified-native-20260530.txt
- reit-cap-rate-spread-verified-native-20260530.txt
- reit-sector-cap-spread-q2-2023-native-20260530.txt
- reit-cap-spread-timeseries-native-20260530.txt

~/.claude/memory/research/:
- reit-pricing-theory.md
- reit-validation-methodology.md
- reit-theory-notes-2-2.md

ctx-warn ckpt = `ckpt-202605301215:btn-GCP` (memory/MEMORY.md 에 1줄 등록).
