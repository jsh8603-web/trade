# round-N — 2차전지 추가 라운드 (2026-05-30)

> frame §5 권고 "round-N.md = 자문/웹 추가 라운드 (필요 시, 자문 채널 경합 자제)" — 본 라운드는 ★skip 사유 박제 + 다음 라운드 권고.

## §1. 본 라운드 자문/webfetch skip 사유

본 subagent 라운드 (2026-05-30 22:50-23:05) = 단발 자율 분석. 사유:

1. **데이터 충분 (frame §5 round-1+round-N 권고 자문 채널 경합 회피)**
   - 본 산업 핵심 finding (H2 LIT→양극재) = 무료 데이터 (FDR + yfinance) 만으로 5게이트 통과 → 자문 polling 불필요.
   - frame §0 "자문 그대로 코드화 금지" — 본 라운드 = 실측 driven, 자문 의존 0.

2. **자문 응답 시간 vs 컴퓨트 trade-off**
   - claude-web/gemini-web 1 round = ~3분 + 응답 대기. 본 라운드 = 실측 산출 우선 (Tier 2 토큰 300k budget 내 4 라운드 계획 → 자문 1 라운드는 다음 boost 라운드 위임).

3. **다음 라운드 자문 권고 시점**
   - DART API 키 확보 후 펀더멘털 (R&D, 매출 yoy) 실측 시도 + 결과 격하 시 cross-verify.
   - Trump 행정부 EV credit 변경 (2026-Q1-Q2 예상) event 발생 시 정량 prior 박제 위해 webfetch.
   - SNE Research GWh 출하 / LMC EV 판매 = 유료 source 회피 대안 자문 (free proxy 추천 요청).

## §2. 다음 라운드 권고 (★ supervisor 위임)

| # | 항목 | 행동 | 우선순위 |
|---|---|---|---|
| 1 | DART_API_KEY 확보 | OpenDart API key 발급 (즉시 무료) → dart_provider.py 활용 → 4종 분기 펀더멘털 yoy IC 측정 | HIGH |
| 2 | pykrx 외국인 flow 인증 | KRX 회원가입 → KRX_ID/PW 환경변수 → krx_flows.py KrxForeignFlowProvider 실데이터 적재 → H5 외국인 regime breakdown 재실행 | HIGH |
| 3 | block-bootstrap (small-n §1 (d)) | run_validation.py 의 IID SE → block-bootstrap (block_size=4-6) 재산출 → H2 CI 보정 | MEDIUM |
| 4 | skfolio CombinatorialPurgedKFoldSplit | frame §M4 #5 권고 → walk-forward 단일 split → CPCV 다중 split | MEDIUM |
| 5 | TSLA proxy 대체 (H3 REJECTED 후속) | LIT + BATT 가중 평균 OR IEA Global EV Outlook yoy proxy → 새 H3' 측정 | MEDIUM |
| 6 | Trump 행정부 EV credit 변경 (2026 Q1-Q2 발생 시) | event window CAR 측정 + claude-web 자문 1회 | HIGH (event 발생 시) |
| 7 | 정적 universe → PIT dynamic (frame §1) | KrxSectorProvider.get_sector_map(as_of, market) 적재 → 시점별 universe 변경 추적 | LOW (4종 모두 현존, 단기 영향 작음) |

## §3. self-check (round-N 진행 양식)

- ★ 본 라운드 = 정량 추가 산출 0 + 자문 0. ★ skip 의도 명시 = idle 아님 (frame §0 자율 행동 + 막힘 보고 의무).
- 다음 라운드 = supervisor 의 boost 지시 (DART/KRX 인증 확보) 후 batch 실행 권고.
