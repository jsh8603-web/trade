# round-1 — 바이오 산업 가설 + Layer 3 cycle 지표 후보

> Tier 3 바이오 sub-study, 2026-05-30, opus 1m.
> 본 round-1 = 이론·가설 초안 (validation 전), 5게이트 분석 후 round-N (또는 본 라운드 update) 에서 finding 으로 확정.

## §1 산업 이해 (1-page summary)

한국 KRX 바이오 산업 (헬스케어·제약·바이오테크) 특징:

1. **이질성 극단** — 한 라벨 안에 CMO/CDMO (삼바, ROCE 안정) · 신약 (HLB·SK바이오팜, binary 임상 risk) · 바이오시밀러 (셀트리온, 가격 cycle) · traditional pharma (한미·녹십자, dividend payer) · 의료기기 (씨젠·EDGC, 진단 cycle) 가 섞임.
2. **시총 집중** — Top 30 시총 합 ≈ 약 152조원 중 삼성바이오로직스 (63조, 42%) + 셀트리온 (43조, 28%) = 합산 70%. cluster-level 분석 시 두 종목이 dominate.
3. **수출 비중 높음 — frame 가정 검증 대상** — 삼바·셀트리온 모두 글로벌 매출 70%+. 그러나 본 분석에서 **USDKRW yoy corr -0.035~+0.038 (n=146 month, p>0.6)** = 산업 평균 forward 20d return 과 비유의. frame 의 "수출 비중 → USDKRW sensitivity" prior 는 ★기각 (TENTATIVE → REJECTED).
4. **FDA 사이클 의존** — 한국 신약 (HLB·SK바이오팜) NDA event 가 미국 FDA approval 의존. 글로벌 FDA approval count yoy 가 산업 평균 forward 1m corr=+0.188 (p=0.023 raw, **multi-comparison 후 비유의 α/15=0.0033**).
5. **regime shift (2020-2022 코로나 + 2023+ post-pandemic)** — 본 분석에서 IS (2014-2022) vs OOS (2023-2026) corr sign flip 광범위 관찰. industry cycle 가 코로나 전후 구조 변화.

## §2 가설 (5개, 반증조건 포함)

### H1 — USDKRW 수출 sensitivity 가설
- **claim**: 바이오 universe (삼바·셀트리온 dominant) 수출 비중 높음 → USDKRW 약세 (yoy>+5%) 시 forward 20d return 양의 corr (corr ≥ +0.10).
- **반증조건**: corr 점추정 |r|<0.05 OR p>0.10 OR LOO p_med>0.20 OR OOS sign flip.
- **★ 실측 결과 (validation-macro)**: corr=-0.035 (lag 0) ~ +0.038 (lag 1) ~ +0.028 (lag 3), p>0.6, **★REJECTED**.
- **함의**: 점추정 prior weight 박제 금지. 본 frame.md §3 Layer 2 USDKRW base_weight 0.15-0.20 가정 → 바이오에는 적용 X.

### H2 — US 금리커브 (10Y-2Y) 가설 (장기 성장주 sensitivity)
- **claim**: 바이오 = duration-long (장기 cashflow) → US curve flattening (10Y-2Y 축소) 시 forward return 음의 corr.
- **반증조건**: |r|<0.05 OR p>0.20 OR OOS ratio < 0.0.
- **★ 실측 결과**: corr=+0.133 (lag 0, p=0.108), +0.149 (lag 1, p=0.072), **OOS ratio 2.16 (오히려 강함)**.
- **finding**: ★TENTATIVE DIRECTIONAL (raw p<0.10, Bonferroni p>=0.05/15 후 비유의). 부호 방향 (curve steepening → bio return ↑) 은 OOS 에서도 유지. weight rule 후보 LOW confidence.

### H3 — HY OAS (글로벌 risk-off) 가설
- **claim**: HY OAS 확대 (risk-off) → 바이오 (성장주, risk-on asset) forward return 음의 corr.
- **반증조건**: n<24 INSUFFICIENT, |r|<0.05.
- **★ 실측 결과**: n=30 만 (BAMLH0A0HYM2 2023-05+) — ★N gate 미달 + OOS 데이터 부재. **★INSUFFICIENT** (single-source).
- **함의**: collector_plan_industry 에 ICE BofA HY OAS 추가 monthly history (FRED BAMLHYM2 가용 추가 확인 필요) 등록.

### H4 — FDA approval cycle 가설
- **claim**: 글로벌 FDA NDA approval count yoy ↑ → 한국 바이오 forward 1-3m return 양의 corr (FDA 모멘텀 spillover, 한국 신약 license-out 환경 개선).
- **반증조건**: corr<0 (sign flip) OR p>0.10 OR OOS ratio < 0.
- **★ 실측 결과**: corr=+0.188 (lag 1m, p=0.023 raw) ★. **BUT** Bonferroni α/15=0.0033 후 비유의 + OOS (2023+) corr=-0.097 → ratio=-0.91 **★sign flip** → 5게이트 OOS FAIL.
- **finding**: ★TENTATIVE DIRECTIONAL (raw 양의 시그널, OOS 미검증). regime shift (post-2022 FDA approval cycle 변화 = 신약 R&D refresh) 가설 추가 검증 필요.

### H5 — 헬스케어 ETF momentum 가설 (자체 가격 reflexivity)
- **claim**: KRX 헬스케어 ETF (TIGER 143860) momentum (20d, 60d) → 산업 평균 forward return 양의 corr (reflexivity).
- **반증조건**: |r|<0.05 OR p>0.20 OR cross-sectional rank-IC test 시 종목 분산 무시.
- **★ 실측 결과**: corr=+0.007 (etf_mom_20d lag 0, p=0.93), +0.129 (etf_mom_60d lag 1, p=0.13), **★REJECTED** (ETF momentum ≠ 종목 평균 forward return, reflexivity 가설 미입증).

## §3 Layer 3 cycle 지표 후보 (frame §3 권고 적용 + 확장)

| # | 지표 | source | frame 권고 | 본 분석 가용 | 5게이트 status |
|---|---|---|---|---|---|
| 1 | CMO 가동률 | 삼바·셀트리온 분기 IR | ○ | × 무료 source 없음 | 미검증 (collector_plan 등록) |
| 2 | FDA approval count (월별, yoy) | openFDA API | ○ | ○ 적재 완료 (n=146 month) | TENTATIVE (H4) |
| 3 | clinicaltrials.gov 신규 등록 (월별) | ClinicalTrials.gov API v2 | ○ | × facet API 미제공 (yearly only) | 미검증 (Tier 3 data sparse) |
| 4 | 신약 IND/NDA event | FDA + DART | △ | × event 추출 자체 별 작업 | 미검증 |
| 5 | USDKRW (수출 sensitivity) | FxStore PIT | ○ | ○ 적재 + 검증 완료 | ★REJECTED (H1) |
| +6 | KRX 헬스케어 ETF momentum | FDR | (확장) | ○ 적재 완료 | ★REJECTED (H5) |
| +7 | NIH 예산 yoy | NIH RePORTER | (확장) | × 본 라운드 미적재 | 미검증 |

## §4 Sub-cluster 옵션 (frame.md §1 권고 — 4 sub-cluster)

Top 30 cluster 분포:
- CMO_CDMO: 2 (삼바·에스티팜, 합산 시총 65.9조)
- biosimilar: 2 (셀트리온·셀트리온헬스케어, 합산 45조)
- novel_drug: 29 (HLB·SK바이오팜·메지온·... 합산 43조)
- traditional_pharma: 10 (유한·녹십자·한미·... 합산 13.8조)
- diagnostic_device: 5 (씨젠·메디아나·... 합산 2.7조)
- other_bio: 2 (합산 0.8조)

본 라운드 = 산업 평균 (eq-weight Top 30) 분석. **sub-cluster 별 분해 = round-N 또는 future scope** (frame.md §3 권고).

## §5 미해결 의문 (round-N 보강 후보)

1. **DART 펀더멘털 (Layer 1) Rank-IC** 미검증 — DART_API_KEY 부재 + DartXbrlProvider graceful empty. PER·PBR·ROE 등 펀더멘털 IC = M1 (frame §M1) 직접 적재 필요. (★ collector_plan_industry D1)
2. **외국인 net flow** — krx_flow_snapshots.jsonl 부재. 본 분석 = USDKRW + KOSPI return proxy 만.
3. **factor neutralization (M5 toraniko)** — 본 분석 raw IC 만. neutralized IC 비교 = future scope.
4. **regime 36 cell 분해 (M3)** — 본 라운드 = full sample IS/OOS split 만. 36 cell = N gate 부족 우려 (147 month / 36 cell ≈ 4 = 미달).
5. **OOS 광범위 sign flip 원인** — 2020-2022 코로나 + 2022 인플레/금리쇼크 + 2023~ AI cycle 재편 → 바이오 사이클 구조 변화. **regime classifier 명시 필요** (별 라운드 OutOfSample 처리).
6. **CMO 가동률** — 삼바 IR 분기 보고 (수동 추출 가능), 셀트리온 미제공. round-N 에서 manual scrape 검토.

## §6 finding 요약 (★validation 종합 후 update — direction.md 갱신)

- **확신 (5게이트 all pass) finding = 0건** (Layer 2 거시 + Layer 3 산업).
- **TENTATIVE DIRECTIONAL = 2건** (H2 us_curve, H4 fda_yoy — raw p<0.10 但 Bonferroni 후 비유의).
- **REJECTED = 2건** (H1 USDKRW, H5 ETF momentum).
- **INSUFFICIENT = 1건** (H3 HY OAS, n=30).

⛔ **점추정 prior 박제 금지** — frame.md §3 Layer 2 USDKRW base_weight 0.15-0.20 권고 → 바이오 산업에는 **적용 X** (corr 비유의). 본 finding = direction.md 박제 + summary.yaml `weight_rule_candidates: []` (또는 LOW confidence H2 만).
