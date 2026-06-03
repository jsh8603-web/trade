# round-N — us_defensive S3 외부검토 라운드 (2026-06-04, skip 판정 + 전이 적용)

> frame §A S3 = "gemini+claude 병렬 자문 → round-N.md". frame §5 "round-N = 필요 시".
> 본 라운드 = ★S3 자문 **불요 판정 (skip)** + skip 사유 박제 (§M.12 cross-market 전이 적용 + 미국 특이점 명시).
> SSOT = `study-research/frame-v3-draft-industry-dispatch-20260603.md` §M, §M.12.

## §1. S3 자문 불요 판정 (skip) — 근거

1. **frame §5 "round-N = 필요 시"**: us_defensive = 미국 1단계 파이프라인 미러(EDGAR/yfinance/FRED). 핵심 측정(rev_1m/vol_60/real_rate β)은 무료 데이터로 산출 완료, n=183개월(한국 대비 장기) = 통계력 강 → 추가 자문 불필요.

2. **§M.12 cross-market 일반성 전이 (방법론 결론)**:
   - 결론 1 (24M degenerate): us_defensive valuation per_z/pbr_z 24M = eff_N≈7.2 degenerate 라벨 추가(Phase 1 gap 보완). 단 둘 다 INSUFFICIENT(비유의)라 verdict 무영향. primary = cs_rev_1m(3M, 비-24M).
   - 결론 2 (small-n): breadth 47 ≥20 → magnitude haircut 불요.
   - 결론 3 (peak-EPS): asset_stable = peak-EPS 직접 대상 아님. PER value premium 약·비유의(미재현).
   - 결론 4 (regime overfit): real_rate β n=36 small = hedge. HY OAS regime normal 28/stress 9 = small, 동일 overfit 게이트.

## §2. 미국 특이점 (전이 시 주의 — 한국과 다른 점 명시)

- ★us_defensive valuation = 한국 consumer/telecom 강 value premium **미재현** (PER value premium 방향만 약, PBR 역방향 value trap 가능). = 한국 asset_stable(consumer/telecom valuation TENTATIVE~PARTIAL)와 **다른 패턴** → 한국 value premium 결론을 미국 defensive 에 단순 전이 금지.
- ★dominant 신호 = rev_1m(단기 reversal, NW+block-boot 0배제 유의, BY 미생존) + real_rate 듀레이션(t=-4.1, n=36 small hedge) = 한국 asset_stable(valuation 중심)과 신호 구조 상이. = 동적가중·metric 적합도 시장 의존성 추가 증거.
- = §M.12 결론 3의 "metric 적합도 시장·시총 의존" 가설과 정합(미국 defensive ≠ 한국 defensive valuation 적합도).

## §3. 본 라운드 self-check
- ★S3 자문 skip + 사유 박제. 방법론 결론 전이 + 미국 특이점(value premium 미재현) 명시.
- 24M degenerate 라벨 gap 보완 = Phase 1 audit (per_z/pbr_z 24M eff_N≈7.2, 매핑표 9행).
- 다음 라운드 권고: EDGAR valuation §10 박제(현 placeholder) + 배당수익률(asset_stable primary 보완) + survivorship 보정. real_rate/HY OAS 장기 교집합 확대(현 n=36).
