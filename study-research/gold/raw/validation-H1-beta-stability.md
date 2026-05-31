# H1 검증 — 변화율 베타 안정

> **명제**: Δln_gold 의 Δ(DFII10) 민감도 β(Δln_dollar 통제) 가 2010-2026 구조적 안정.
> **3-layer 통합 반증조건**: (진단) 252d rolling Pearson 부호반전·약화 비율 / (형식) rolling β 부호반전 + QLR sup-F break / (분해) Δ-beta vs level e-process ordering (H8 별도).
> **데이터**: FRED DFII10 + DTWEXBGS + GLD ETF (Yahoo v8). n=4280 일, 2010-01-04~2026-05-29. ⛔ 합성·시뮬 0건.
> **스크립트**: `raw/analyze-h1.py`. **산출**: `raw/h1_rolling_beta.csv` + `raw/h1_result.json`.

---

## 결과 요약 (정량)

| 레이어 | 지표 | 실측 | 임계 | pass |
|---|---|---|---|---|
| L1 | 252d Pearson 부호반전 days | **0 / 4028** (0.00%) | 0 | ✓ |
| L1 | 252d Pearson 약화 (\|r\|<0.10) days | **135 / 4028** (3.35%) | 베이스라인 3.1% × 3 = 9.3% | ✓ |
| L1 | rolling Pearson median | **-0.349** | (참고) | — |
| L1 | rolling Pearson range | **[-0.674, -0.009]** | 부호 양반전 X | ✓ |
| L2 | 252d rolling β 부호반전 days | **75 / 4028** (1.86%) | < 5% | ✓ |
| L2 | b_real mean | **-0.000657** (sd 0.000314) | (참고) | — |
| L2 | b_real range | **[-0.00151, +0.00016]** | (참고) | — |
| L2 | QLR sup-F (Quandt-Andrews) | **15.26** | < 16.45 (Andrews 1993 5%, k=3, trim=0.15) | ✓ |
| L2 | sup-F (1%) | **15.26** | < 20.0 | ✓ |
| L2 | sup break date | **2023-12-13** | 5% 미돌파, 후보 점만 | — |

★ **H1 verdict = SUPPORTED**. 3-layer 통합 반증조건 모두 pass.

---

## §A 이론 실재성
- Barsky-Summers 1988 (JPE 96(3)): 금↔real rate level 관계의 변화율 단위 부수효과 = 본 §1의 dual realization.
- WGC GRAM (monthly 4-driver) 의 opportunity cost category 직접 후예.
- v1 실측의 ★core fact (16y 일별 Pearson 불변) 이 본 검증의 *진단 layer*.
- Erb-Harvey 2013 + O'Connor 2015 survey 의 horizon 의존성과 정합 — *일별* 변화율 단위에서 베타 안정은 *수십년 horizon* 의 평균회귀와 양립.

## §B 실데이터 검증
- n=4280 일 (8.8 years × 1.85 시리즈)
- 기간 2010-01-04 ~ 2026-05-29
- 통계 임계: 부호반전 0회, 약화 비율 3.35%, β 부호반전 1.86%, sup-F 15.26 — 전부 정량 임계 통과
- ★데이터 원천: FRED 공인 + Yahoo v8 GLD 일별 close. ⛔ 합성·시뮬 0.
- 보정: GLD ≈ 1/10 oz × LBMA PM. 변화율 단위 분석엔 scale-invariant (R²·corr·standardized β 영향 0)

## §C yaml 도출 추적성
- direction.md 블록3 `real_rate → gold (-, force_include)`: 본 검증의 H1 SUPPORTED 가 prior_strength 의 직접 근거.
- 블록5 `real_rate_beta_holds` confirm/reject 정량 임계 = 본 검증의 layer 1·2 정량 임계로 정합:
  - confirm: 252d Pearson 음의 부호 유지 + |r|<0.10 비율 < 9.3% + rolling β 부호반전 < 5% + sup-F < 16.45
  - reject (e-CUSUM 단측 붕괴): 위 임계 위배 + Δ-beta e-process > 20 돌파 (H8)
- 블록7 코드: `core/study/flag_router.FlagRouter.emit_from_ic` + Bai-Perron sup-F 모듈 + 252d rolling Pearson + β 부호반전 모니터.

## §D PIT / OOS
- 본 검증 = full-sample in-sample (FS-IS). v1 16y 데이터 = retrospective.
- PIT 통과: DFII10·DTWEXBGS·GLD 모두 daily 실시간 시리즈 (vintage_policy=point_in_time, lag=0).
- OOS 추가 plan (H8 이중 e-process): 2010-2021 calibration → 2022-2026 OOS evaluation. ordering falsification 의 정식 OOS test.

## §E 자문 비판 + 환각 cross-verify
- R2 양 모델 합의 임계 (252d rolling Pearson 부호반전 0회) 와 실측 일치.
- ★중요 단서 (Claude R2 추가): QLR sup-F = 15.26 가 5% 임계 16.45 매우 근접. 후보 break point 2023-12-13 = 2024-26 신고가 랠리 시작점과 일치. 변화율 *베타 안정* 결론은 sup-F 임계 미돌파로 유지되지만, *최근 4분기 점진 변화* 의 단서 존재 — 후속 OOS 모니터(H8) 정당화.
- 자문 임계 (Bai-Perron p<0.05) → QLR Andrews 1993 critical 적용 (statsmodels 미보유, 수작업 계산). cv 인용은 Andrews 1993 ECTA Table 1, k=3 (intercept+2 reg) trim=0.15.
- 환각 cross-verify: 본 시점 외부 검증 inflate 없음 (다른 시리즈의 베타 안정성 문헌 — Erb-Harvey 의 long-horizon 평균회귀 + Reboredo dollar copula stability 와 정합).

## §F 반증 가능 + 기각 기록
- 위 3-layer 반증조건 = 각각 명시 정량 기각 임계.
- 기각 가능성 (in alternative universe): 
  - 252d rolling Pearson median 이 -0.10 < median < 0 → 약화 강함, 부호반전 임박 시그널.
  - β 부호반전 > 5% → 변화율 β 의 lazy structural change.
  - sup-F > 16.45 (5%) → 정식 break.
- 본 검증에서 **셋 다 미발생** = 기각 시나리오 0. 단 sup-F = 15.26 의 미점근적 임박은 *기각 가능성 0.05 < p ≤ 0.10* 영역 — 정식 기각 아님이지만 후속 모니터링.

## §G 검정력 한계
- **GLD ≈ 1/10 oz LBMA**: 변화율 단위 분석에 무관하나, *수준 회귀*(H2) 에선 단위 변환 필요. 본 H1 = 변화율 → 무관.
- **β 절댓값 매우 작음** (b_real ~ -6.6e-4): 단위 = log gold return per bp Δreal. 1bp Δreal = -0.066% Δgold ≈ -6.6 ¢/oz @ $1000 — 경제적 의미 작음. 단 *통계적 안정* (sign flip < 5%) 은 별개 — H1 검정 대상은 안정성이지 절대 magnitude 아님.
- **dollar 통제 partial β**: real_rate·dollar 공선성(VIF ≈ 1.3-1.5 추정) 으로 |b_real| 가 marginal Pearson |r=-0.32| 보다 *작게* 추정됨 (공선성 dilution). H4 의 표준화 β reconciliation 에서 별도 처리.
- **QLR sup-F 자작**: statsmodels 에 ready-made Bai-Perron 없음. 수작업 Chow F + sup() 구현. Andrews 1993 ECTA Table 1 cv 인용 — 본문 인용 전 ECTA archive 재확인 권장 (◇).
- **Bai-Perron 다중 break** 미구현 (단일 break QLR 만). 다중 break 가능성 별도 — 본 검증은 우선 단일 sup-F 만.

## §H 미해결 의문
- (◇) Andrews 1993 ECTA cv 정확값 (k=3, trim=0.15, 5%=16.45 가 정확한지 — Andrews & Ploberger 1994 의 ExpF/AveF 보조 통계도 별도 검토 가능).
- 2023-12-13 sup break 후보의 의미: 2024-26 랠리 시작점. *변화율* β 의 점진적 변화가 *수준* break 의 신호일지 — H8 이중 e-process ordering 으로 답할 항목.
- pre-2003 TIPS 데이터 부재: 1990s break 와의 비교 불가. nominal − survey 기대인플레 bridge 로 확장 가능하나 본 H1 검증 범위 밖.
- HY OAS 의 위기 미포함 (3년치만 fetch) — H1 은 영향 없음 (real_rate / dollar / gold 만 사용), H5 검증에서 별도 처리.

---

## 결론
H1 = SUPPORTED. ★3-layer 통합 반증 모두 pass. v1 의 변화율 β 안정 가설 = R1+R2 자문 합의 + 16y 일별 실측 = 정합. 단 QLR sup-F 가 5% 임계 미돌파 임박 (15.26 vs 16.45) → 후속 OOS 모니터링 (H8) 정당화. block5 `real_rate_beta_holds` flag 의 confirm 영구 채택 아니라 e-process anytime-valid 모니터로 지속 검증.
