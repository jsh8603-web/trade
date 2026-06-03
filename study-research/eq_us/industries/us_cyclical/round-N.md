# round-N — us_cyclical S3 외부검토 라운드 (2026-06-04, skip 판정 + ★전이불가 특이점 분리)

> frame §A (6 프로세스) S3 = "gemini+claude 병렬 자문 → round-N.md". frame §5 "round-N = 필요 시".
> 본 라운드 = ★S3 자문 **불요 판정 (skip)** + skip 사유 박제. 단 ★us_cyclical 은 한국 자문 결론으로 전이 불가한 특이점(부호 반대)이 있어 별도 판정 명시 (SR Pre-Review #3 / taskspec 2.2 A3).
> SSOT = `study-research/frame-v3-draft-industry-dispatch-20260603.md` §M, §M.12.

## §1. S3 자문 불요 판정 (skip) — 근거

1. **frame §5 "round-N = 필요 시"**: 미국 sleeve = 1단계 파이프라인(EDGAR/yfinance/FRED) 작동 검증 겸함. 핵심 측정(PER/PBR/vol/HY OAS β)은 무료 데이터로 산출 완료 → 추가 자문 polling 불필요.

2. **§M.12 cross-market 일반성 전이 (조건부 적용)**: §M.12 4결론 중 **방법론 결론(1 degenerate / 2 small-n magnitude / 3 peak-EPS 메커니즘 / 4 regime overfit)**은 시장 무관 측정 인프라 = 한국 자문 결론을 미국에 전이 적용:
   - 결론 1 (24M degenerate): us_cyclical cs_per_z 24M eff_N≈4.7 degenerate 라벨 + primary 3M 재배치 (Phase 1 반영).
   - 결론 2 (small-n): us_cyclical breadth 35 ≥20 → magnitude haircut 불요(단 BY 미생존이 핵심 제약).
   - 결론 3 (peak-EPS = earnings cycle 진폭, ⛔시총 인과 금지, E/P 대체): 카드 반영.
   - 결론 4 (regime overfit): HY OAS regime 2023~만(37mo) = INSUFFICIENT, 동일 overfit 게이트 적용.

## §2. ★전이 불가 특이점 — 한국 자문 결론으로 덮지 않음 (SR #3 / A3)

★us_cyclical PER 부호가 **한국 auto/반도체와 반대** (한국 PER✗ peak-EPS / 미국 PER○ 방향) = cross-market **전이 불가 특이점**. 이를 한국 자문 결론(peak-EPS 보편)으로 덮으면 특이점 검증 누락 (SR Pre-Review #3 반박).

- **별도 판정 (전이 X)**:
  - 한국 cyclical(auto/반도체) = PER✗ (peak-EPS trap, 적자비율 高·중소형). 미국 us_cyclical = PER 방향 작동 prior (대형주 earnings 안정, 적자 3-16%).
  - = §M.12 결론 3의 "peak-EPS = 시장·시총 의존" 가설과 **consistent-with** (동일 방향)이나 ⛔**"explained-by" 아님** — 미국은 한국과 다른 파이프라인(EDGAR)·universe(대형)·기간(2015~)에서 독립 측정. 한국 결론의 단순 전이로 미국 PER○ 를 설명하면 안 됨.
  - ★단 미국 PER○ 자체가 **약 prior** (BY 생존 0 + 24M degenerate strip 후 유의 horizon = 3M 1개[그것도 BY 미생존] / 6M·12M 비유의). = Phase 1 에서 PARTIAL → **TENTATIVE** 강등 (SR #2 ghost-finding 방지).
  - → **판정**: "미국 cyclical PER 부호 반대 = 전이 불가 특이점. 미국 자체 측정 결과 = PER 방향 약 prior(TENTATIVE, BY 미생존). 한국 peak-EPS 보편 결론으로 덮지 않고 별도 추적." cross-market 일반성 주장은 약화 — 2번째 데이터(다른 기간/universe) 확보 후 재판정.

## §3. 본 라운드 self-check
- ★S3 자문 skip + 사유 박제 = idle 아님. 방법론 결론은 전이, 부호반대 특이점은 별도 판정 분리.
- ★SR #3 / taskspec 2.2 A3 충족: "us_cyclical PER 부호 한국과 반대 = 전이 불가, 별도 판정" 박제.
- 다음 라운드 권고: HY OAS 장기 시계열(현 2023~만) + survivorship 보정(현 ETF holdings) 확보 후 PER○ 재측정 → BY 생존 여부 재판정 (현 TENTATIVE). 부호반대 일반성 = 다른 미국 cyclical 기간/universe 2번째 측정으로 검증.
