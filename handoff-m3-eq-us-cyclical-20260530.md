---
tags: [type/handoff, study/eq_us_cyclical, phase/M3]
date: 2026-05-30
---
# Handoff M3 — eq_us_cyclical 거시연관 분석 (btn-common-task)

## 즉시 재개 명령 1줄
```bash
"C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe" -X utf8 study-research/eq_us_cyclical/raw/m3_analysis.py 2>&1 | tee study-research/eq_us_cyclical/raw/m3_output.txt
```

## 상태
- M3 지시 수신: `[M3 재송신] study-research/macro/timeline.md §4 가이드대로 4 epoch별 sleeve 거시연관 분석`. PIT·OOS·합성금지.
- 작성 완료: `study-research/eq_us_cyclical/raw/m3_analysis.py` (M1 기간 2021-12 ~ 2024-12 일별 데이터, sector ETF + macro_yahoo_raw 사용)
- **★실행 미수행** (ctx critical 482k로 차단).

## m3_analysis.py 산출 (실행 시)
- §1 epoch 분해(E1 긴축충격 / E2 전환 / E3 금리재상승 / E4 pivot·인하) × cyclical sleeve(XLY/XLI/XLB/XLE/XLF + SOXX) 평균 수익·변동성·Sharpe
- §2 driver loading 회귀 r_sleeve ~ Δus10y + ΔDXY + Δoil — full sample + epoch conditional (★rate 직접보다 dollar 채널·국면조건부 주목)
- §3 within-sleeve corr (L축 caveat — 종목간 0.9+면 equity factor) + cyclical-defensive corr + per-sector rank-IC vs macro driver + Kish eff_N

## 다음 세션 액션
1. `m3_analysis.py` 실행 → `raw/m3_output.txt` + `raw/m3-metrics.json` 생성
2. 결과 보고 `raw/m3-findings.md` 작성 (epoch별 loading + L축 caveat 진단)
3. main(btn-Codlearn)에 SSOT 헬퍼로 경로+핵심상관 답신 (M3 지시 마지막 요구)

## v2 산출 완성 인벤토리 (이미 main 보고됨)
- `direction.md` (2-1, 170줄, 9R)
- `theory-notes.md` (2-2)
- `validation-H{3,4,5,1-6-deferred}.md` + `run_validation.py` + `validation-metrics.json`
- `study_session.yaml` v2 (basis_raw 명시)
- `audit-self.md` (§2.5 8축, 6 통과 + 2 부분)
- `raw/round-{1,2,3}-{question,gemini,claude}.md` (9 파일)
- `raw/fred/*.csv` (17 시리즈) + `raw/yfinance/sector_etf_close.csv`
- `summary.md` (v1, M3 결과 추가 후 갱신 후보)

## 미해결 (audit-self.md H축)
- D축: ALFRED vintage 미적용, OOS rolling 미수행
- G축: Driscoll-Kraay/Newey-West/bootstrap 1차 미적용
- 둘 다 main 인프라 의존
