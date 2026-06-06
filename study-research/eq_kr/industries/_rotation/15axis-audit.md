---
tags: [type/15axis-audit, domain/inv, scope/equity-kr, sector/_rotation, status/self-audit]
date: 2026-06-05
owner: semi-analyst (kr-equity, opus 1m) — ★self-audit (G-C 독립 audit 은 별 세션이 수행, supervisor 스폰)
---

# 15축 self-audit — 12산업 ROTATION TIMING

> ★본 문서 = teammate self-audit (G-A 축 인지·이행 입증). **G-C 독립 audit(author≠auditor)은
> supervisor 가 별 세션 스폰 = 미수행 상태.** hard-fail 코어 = B·C·D·I (+M·N·O wire).

## A-1. 15축 (A~P) — 3컬럼 (① 적용 ② 측정 코드·수치 경로 ③ 결과·판정)

| 축 | ① 적용 | ② 측정 경로 | ③ 결과·판정 |
|---|---|---|---|
| A 이론실재 | ✅ | frame §M2(산업 panel 시계열) + sector rotation 학술(momentum/mean-reversion) + 자문 prior | rotation = 산업 momentum persistence + 상대 reversal + cycle 민감도 차. 이론 ground O |
| B★ 실데이터 | ✅ | measure_rotation.py: 12산업 prices.parquet(pykrx 실측 88월) + regime_series(FRED CLI/USDKRW/semi_ppi + ECOS foreign) | 합성 0%. PASS |
| C★ 추적성 | ✅ | validation-rotation-v1.json + validation-rotation-robust-v1.json 전 수치 ← 각 capsule data/*.parquet | yaml↔json 키 매핑. PASS |
| D★ PIT-safe | ✅ | 가격신호=forward shift(PIT). macro=발표지연 lag(CLI_PUB_LAG=2/SEMI_PPI_LAG=1, usdkrw/foreign=일별 실시간) | ★lag 미적용 leakage 발견·수정(cli rho 0.555→0.482). PASS (D축 작동 입증) |
| E 자문환각 | ✅ | 자문(gemini sector-timing-overlay / claude gated-design) = 측정 후 cross-verify. 본인 정량 ≥1(forward IC+OOS+robust) | 자문=reference, 증거=우리 측정. PASS |
| F 반증+기각 | ✅ | placebo(shuffle corr 분포) + leave-one-year + OOS walk-forward(부호 flip=기각) | bio FAIL/steel cli_chg flip 기각 = falsifier 작동. PASS |
| G 검정력·tier | ✅ | t_obs=|rho|·√n_eff ⋚ 2.802(MDE breakeven) + n_eff autocorr 보정 | powered 1개(financial)·나머지 underpowered = tier 정직 박제. PASS |
| H 미해결 | ✅ | candidate-ledger 🔬 falsifier 섹션 + collector_plan(이연) | 연결 O. PASS |
| I★ 생존편향 | ⚠️ | 산업 패널 = capsule universe(현 생존 종목 eq-weight). delisted 누락 | PARTIAL — capsule 공통 한계 상속. 단 aggregate panel 은 개별종목보다 덜 민감 |
| J 경제성·거래비용 | ✅ | net_cost: STT_sell 0.20%(매도 비대칭) + 편도수수료. roundtrip 23bps / 월 11.5bps | |rho| 0.2~0.36 vs cost → cost-aware no-trade 필수. 박제 O |
| K 다중검정 | ✅ | 단일 FDR family(12산업×신호×horizon) BY 보정 + Bonferroni 병기 | powered m=1, BY 생존 financial 1개. 엄격 적용 PASS |
| L 통합 PSD | ⏳ | rotation = 산업 패널 시계열(공통인자 1회 계상은 통합단계) | supervisor 통합 yaml 단계 (capsule 범위 외) |
| M★ wire충실 | ⏳ | ⛔본 capsule = 측정+gated 설계 권고만. 배선(WIRE5) 미접촉 | go-live 미접촉 (supervisor 통합). 해당 없음(측정 capsule) |
| N★ cross PSD | ⏳ | cross-industry 상관행렬(rotation 신호 간) PSD = 통합단계 | supervisor 통합 (산업 N_eff eigen-entropy 5.31 측정은 제공) |
| O★ leakage | ✅ | PIT-safe(D축) + forward shift + macro lag. reject(OOS flip)≠missing 구분 | leakage 수정 완료. PASS |
| P net-cost robustness | ⚠️ | net_cost 모델 박제. sqrt impact = 통합단계 | linear cost 박제, sqrt = supervisor (PARTIAL) |

→ **Hard-fail 코어 (B·C·D·I)**: B✅ C✅ D✅ I⚠️PARTIAL(capsule 공통 한계). **hard-fail 0** (I PARTIAL = 생존편향 잔존 명시, fail 아님).
→ M·N·O: M/N = 통합단계(측정 capsule 해당없음), O✅.

## A-2. 6단계 (S1~S6) 산출물 경로

- **S1** 이론: frame §M2 + sector rotation 학술 + 자문 prior → rotation-timing.md §1.
- **S2** 실측 4게이트: G1 ex-ante(신호 사전정의) / G2 BY-FDR+Bonferroni(summary.yaml fdr_family_single) / G3 walk-forward OOS(IS19-22/OOS23-26, signal_forward_stat) / G4 NW-HAC(nw_se) + wild-cluster. → validation-rotation-v1.json.
- **S3** 외부검토: 자문 gemini(sector-timing-overlay)+claude(gated-design) = `.gemini-web-last.md`/`.claude-web-basic-last.md` (rotation 부활 수렴).
- **S4** 재검증: non-overlap(stride=3M) + placebo + leave-one-year + cross-industry N_eff → validation-rotation-robust-v1.json.
- **S5** 역공격: OOS walk-forward(episode 종속 직접 검정) + LOY(연도 종속) → bio/steel cli_chg flip 기각.
- **S6** 15축 audit: ★본 문서(self-audit). **G-C 독립 audit = supervisor 별 세션 (미수행)**.

## A-3. cross 3종 (분석 단위 간)
- **동시** 12산업 상관: mean pairwise 0.502, PC1 55.3%, N_eff 5.31 (가짜 분산 입증) → rotation = 산업 고유 신호.
- **방향성** 선행신호 후보: semi_ppi yoy → telecom/aitech forward(반도체 cycle 선행 → IT/통신 방어 rotation) = 선행신호 후보 ★보고(빈 [] 아님).
- **구조** supply-chain: 산업 rotation 은 패널 시계열 = 산업 간 customer-supplier 는 통합단계 (DY spillover = supervisor).

## A-5. regime 정합 (interaction)
- rotation 신호 = regime conditional(macro/krw/flow)은 통합단계로 보류. ★단 macro driver 자체(cli_chg/foreign/semi_ppi)가 forward 예측 = regime 변수 = 산업 forward "국면 따라 갈림"의 직접 측정. family_2 interaction(산업×regime) = supervisor 통합 yaml.

## A-6. supervisor 정의 대조
- ★supervisor(team-lead)가 G-C audit verdict 승인 전 frame §M2 + G-G v2 정의 직접 대조 의무 (본 self-audit ≠ 승인 근거).

## ★hard-fail 0 self-check 결론
B·C·D·O = PASS / I·P = PARTIAL(생존편향·sqrt cost = capsule 공통 한계, 명시) / L·M·N = 통합단계(측정 capsule 해당없음).
→ **측정 capsule 기준 hard-fail 0**. 단 ★G-C 독립 audit(별 세션) 미수행 = 완료 아님 (supervisor 스폰 대기).
