---
name: WHY-ROTATION-SELECTION-NOT-APPLICABLE
description: eq_kr 산업간 rotation·산업내 selection 적용 실패 전체 기록 — 무엇을 시도했고 왜 운용 불가였나. study 측정 시도(여러 버전) + 운용 검증(.p4-kr-*) + 자문 3R 종합. 재탐구 0 목적.
tags: [type/research, domain/inv, topic/eq-kr, topic/rotation-selection, status/concluded]
date: 2026-06-09
related: cross-regime-ledger.md §41-42, industries/_rotation/, within_industry_residual_kr.py
---

# eq_kr 산업간 rotation·산업내 selection 적용 실패 — 전체 기록

> **한 줄 결론**: 한국 주식은 **산업간 신호(rotation)는 실재하나 운용 실현 alpha 0**, **산업내 종목선택(selection)은 어떤 틀이든 음수**. 둘 다 비용차감 후 능동 alpha 미입증 → **ETF/EW(산업 동일가중) + 소액 정적 시클리컬 틸트(alpha 0이나 삼성 메가캡 몰빵 분산)**가 정직한 최종형. study in-sample IC robust ≠ 운용 alpha. 자문 3R(claude-web 2026-06-09)·10년 백테스트·.p4-kr-* 측정으로 확정.

---

## A. 산업간 Rotation — 시도와 실패

### A-1. study 측정 시도 (이전 세션, 2026-06-06)

| # | 시도 | 방법 | 결과 | 실패·보류 사유 |
|---|---|---|---|---|
| 1 | **measure_rotation v1** (momentum) | 12산업 momentum 3M/6M + 상대모멘텀 + 거시 공통신호(CLI/USDKRW/flow) 단변량 IC | IC 0.2~0.36, 11/12 underpowered, financial만 powered | ★momentum=공통인자 재포장(market×beta) 의심. CLI rho +0.555=**PIT lag leakage**(lookahead) |
| 2 | **measure_rotation v2** (고유 cycle) | 산업 고유 cycle proxy(철광석/리튬/유가/중국margin) + momentum을 공통인자 residualize 후 강등 | cycle 신호 chemical +0.45/steel +0.35/auto +0.26 등. residual momentum 8산업 소멸 | ★momentum 90% 소멸=재포장 입증. refining crack +0.241="STRONG"이나 **universe 오염**(가스9종 포함)→strict2 단독 무신호 폐기 |
| 3 | **measure_rotation_valband** (밸류밴드) | 산업 aggregate PBR rolling z(24M)→forward | 4산업 OOS 견고(chemical 추세/steel 역추세), FDR 생존 0 | underpowered→보조 confirm 강등. PIT shares 근사(자사주 미반영) |
| 4 | **measure_integration** (통합·residual) | 공통인자 residualize + N_eff PR + sleeve clustering | ★**residual N_eff = 3.5**(12산업 중 진짜 독립 ~3.5). PC1 분산 **50% 지배**(residual 후에도) | ★**구조적 한계**: 공통인자 제거 후에도 단일 지배 구조 → 깨끗한 sleeve 분리 약함. 동시 tilt ≤3 cap, k=2 보수 |

**study 결론**: BY-FDR 다중비교 보정 후 4산업(steel/chemical/telecom/refining) 부호안정. kappa(robust gate×shrunk IC) 비례 사이징. 단 전부 underpowered(n~88/12, magnitude tentative).

### A-2. 운용 검증 시도 (이번 세션, 2026-06-09)

| # | 시도 | 결과 | 실패 사유 |
|---|---|---|---|
| 1 | **동시 신호 tilt** (build_weights, 분기 z) | 횡단면 IC +0.086 t2.04 실재 / portfolio active **t0.59 비유의**(n=63) | 신호 강도 약 + 소액 tilt → portfolio 미미 |
| 2 | **정적 틸트** (시클리컬+telecom kappa 비례 고정 OW 0.04) | NAV 3.716 (4산업 비중 0.4~0.7%) | OW가 kr_stock 내 산업 base 작아 portfolio에 묻힘 |
| 3 | **OW 키움** (0.04→0.10, 2.5배) | NAV **3.712**(오히려 약간 ↓), 비중 0.7~0.9% | ★**portfolio alpha 0 확정** — OW 2.5배 키워도 NAV 동일 |
| 4 | **(2)심층 분해** (.p4-kr-rotation-deep) | 진짜 레버 steel(+0.322)/chemical(+0.220)/telecom(+0.228) 양국면 안정. ⛔refining deep IC **−0.249**=results.json +0.30 **부호충돌**. auto/semi 상승장만 | refining OW 의심(보수적 제외). 시클리컬 신호 직교(steel⊥chemical)나 수익 묶임(0.75) |

### A-3. 왜 산업간 적용 불가 — 근본 원인

1. **공통인자 지배** (study): residual N_eff 3.5, PC1 50% — 12산업이 외국인 flow + 반도체 cycle 공통인자에 묶여 독립 신호 약함. "12산업 rotation"의 진짜 자유도 ~3.5.
2. **신호 강도 약** (운용): 횡단면 IC는 실재(t2.04)하나 IC 0.2~0.3 수준 + underpowered(n~88/12).
3. **portfolio 실현 0** (운용): OW를 0.04→0.10으로 키워도 NAV 동일(3.716→3.712). kr_stock(전체 12~23%) 내 산업 비중이 작고, 산업 분산이 수익으로 안 이어짐.
4. **horizon/cost 버그는 신호 부재 아님**: 이전 세션 study active IR −0.071은 1M평가 버그(3M로 +0.175)였으나, 그걸 fix해도 portfolio alpha 0.

→ **결론**: 산업간 신호 실재하나 운용 alpha 0 = 자문 "비싼 베타". 소액 정적(0.04) 유지는 삼성 메가캡 몰빵 분산 효과만(alpha X).

---

## B. 산업내 Selection — 시도와 실패

### B-1. study 측정 시도 (이전 세션)

| # | 시도 | 방법 | 결과 | 실패·보류 사유 |
|---|---|---|---|---|
| 1 | **within-residual v1** (통일 지표) | 모든 산업 book-to-price 통일 cs rank-IC | 반도체/철강/aitech "中", 나머지 "低" | ★사용자 통찰: "줄자는 capsule이 업종별 맞춤측정. 통일=정밀도 버린 실수" |
| 2 | **within-residual v2** (capsule SSOT) | 캡슐별 측정 IC SSOT + N_eff PR + EB v3 정밀도가중 | semi pbr_z −0.114(BY생존 유일)·steel mom_reversal −0.181·aitech pbr_z −0.183. ρ≥0.25 robust 3곳 | ★EB v2 부작용(약신호 telecom 대평균 끌림 3배 부풀림)→v3 0-shrink 교체. refining=2종 과점 불가, financial=은행만 LIMITED |

**study 결론**: in-sample IC robust(BY생존) 3곳(semi/steel/aitech)이나 **OOS walk-forward + 파이프(capped-EW) 미검증** 명시.

### B-2. 운용 검증 시도 (이번 세션, 2026-06-09)

| # | 시도 | 결과 | 실패 사유 |
|---|---|---|---|
| 1 | **cs_pbr_z top-10 capped-EW** | 10년 선택alpha semi +0.0037~−0.0147(t<1)·aitech −0.0185·steel −0.0083 (전부 비유의 음/약) | 약팩터가 capped-EW 파이프서 죽음(미국 defensive 동형) |
| 2 | **cheapness×quality(ROE) 게이트** (plan W4 코리아 디스카운트 트랩 거름) | 1년 smoke semi −0.065→+0.0099 음→양 전환 / **10년 다시 음수** | 트랩은 막으나 유의성 부족 |
| 3 | **horizon hold** (24M/12M, study forward horizon) | semi +0.0037→**−0.0147 악화**, aitech −0.0287 | ★종목 오래 들수록 악화 = **생존편향 인공물**(study IC=살아남은 종목만) |
| 4 | **넓은 틀** (.p4-kr-wide-value, 소형 포함+cheapness 가중) | 가치섹터(철강/금융/화학) long-short(저PBR−고PBR) **전부 음수**(철강 −69%/화학 −83%), **섹터 EW가 최고**(철강 EW+76%) | ★넓은 틀로도 저PBR 죽음. 자문 "넓은 틀이면 살수도" 가설 반박 |

### B-3. 왜 산업내 적용 불가 — 근본 원인

1. **study IC = 생존편향 + 중첩윈도우 인공물**: semi pbr_z −0.114는 **24개월 forward에서만 생존**(3/6/12개월 미생존). 24M 중첩윈도우 = 독립관측 최소 + 자기상관으로 유의성 부풀림. horizon hold(종목 24M 유지) 악화가 생존편향 입증(살아남은 종목만 24M 후 좋아 보임).
2. **운용 틀이 가치 동네 배제**(claude 자문): 가치가 사는 곳 = 소형·딥밸류·거버넌스 디스카운트. top-10 대형주 capped-EW는 그걸 구조적 배제 = "포트폴리오 정의 불일치"(넓은 횡단면 측정 vs 좁은 대형주 운용).
3. **넓은 틀로도 죽음**(B 검증): 소형 포함 + cheapness 가중해도 저PBR long-short 음수. 섹터 EW가 최고. = 2017-2024 한국 밸류 부진기 구조적.
4. **반도체 = 가치 줄자 미스매치**(사용자 지적): 반도체 PBR<1 단 12%(성장주). 싼 종목 자체가 적고, 그나마 성장 못 따라간 value trap. 가치 줄자를 성장주 섹터에 댄 미스매치.

→ **결론**: 어떤 틀이든(top-10·넓은가중·long-short·horizon hold) 저PBR 음수. study IC는 in-sample 인공물이지 운용 alpha 아님. **단 "한국 가치 무효"는 아님** — 이 비클이 가치 동네를 못 담음(밸류업 2024+ 별도 검증 보류).

---

## C. 반복된 공통 실패 패턴

| # | 패턴 | 산업간 | 산업내 | 본질 |
|---|---|---|---|---|
| 1 | **소표본 underpowered** | n~88/12산업, 11/12 미powered | capsule N_eff 4~50, robust 2~3곳만 | 88개월 × 12분할 = cell당 ~7. MDE 미달 |
| 2 | **공통인자 지배** | residual N_eff 3.5, PC1 50% | (섹터 내 동조) | 외국인 flow + 반도체 cycle이 한국시장 지배 |
| 3 | **데이터 오염·PIT 함정** | refining universe 오염(가스9종), CLI lag leakage | survivor-only universe | strict universe + PIT lag 의무 |
| 4 | **in-sample IC ≠ 운용 alpha** | 횡단면 t2.04 → portfolio alpha 0 | BY생존 IC → capped-EW 음수 | 측정 포트와 운용 포트가 다른 물건 |
| 5 | **생존편향·중첩윈도우** | (OOS 부호유지로 완화) | semi 24M 단독생존 = 인공물(horizon hold 악화로 입증) | 24M 중첩 = 자기상관 유의성 부풀림 |

---

## D. 최종 결론 + 부활 조건

**운용 최종형**: 한국 주식 sleeve = **산업 동일가중 베타 + 소액 정적 시클리컬 틸트(steel/chemical/telecom OW 0.04, alpha 0이나 삼성 몰빵 분산)**. 능동 alpha 없음 확인 = 운용 결정.

**ledger status** (cross-regime-ledger §41-42):
- rotation = candidate (소액 정적, portfolio alpha 0, 폐기조건=확장패널 재추정)
- selection = rejected_provisional (이 틀 폐기, 가치 무효 아님=비클 범위 밖)

**부활 조건** (재탐구 트리거):
1. **selection**: 밸류업 2024+ 별도 전향 버킷(저PBR×고배당/주주환원, 통신·금융·지주 수혜) — 현 검정력 부족, 가설로만. 또는 소형·딥밸류 포함 넓은 틀 운용(이 비클 범위 확장 시).
2. **rotation**: 확장패널 매년 재추정에서 수축 사후평균 유지 + 신호 강도 powered 승격(현 underpowered). refining 부호충돌(study +0.30 vs deep −0.249) 측정 방식 대조 확정.
3. **데이터 게이트**: 종목별 수급(KRX API 차단) 해제 시 약신호 leverage.

**산물**: .p4-kr-static.log·.p4-kr-ow.log·.p4-kr-wide-value.py·.p4-kr-rotation-deep.py / study `industries/_rotation/`(measure v1~integration·within-residual v1~v2) / 자문 claude-web 3R(.claude-web-basic-last.md).
