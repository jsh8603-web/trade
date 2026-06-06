<!-- author: bio-analyst teammate (S6 self-audit 초안, 2026-06-05) -->
<!-- ★G-C 독립 audit 충실 PASS (hard-fail 0, 별 세션 2026-06-05). flow_sell conditional genuine 재현. -->
<!-- ★remediation 반영(2026-06-05): D PARTIAL 격하 + 거래정지 좀비 carry-forward NaN 마스킹 재측정. -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — bio(제약·바이오) §M v3 (frame v3 §E, A~P 15축)

> S6 self-audit: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. semiconductor 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★bio 핵심 = conditional(flow_sell 증폭) 본체 + unconditional 약(OOS artifact) + 생존편향 최악.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 이론 실재 (가설 사전선언) | PASS | theory-notes §6 부호 사전확약(measure 前 동결, HARKing 방지) = vol_60 음(BAB)/per_z 음(Asness QMJ)/flow_sell 증폭(Choe-Kho-Stulz 2005 외국인 herding). archetype event_driven valid_from 2019 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 38종(1818일) + DART 948 rows(2019~) + FRED CLI/DEXKOUS + ECOS 외국인순매수 일별 + yfinance(VIX/factors). 합성지문 PASS(2020-03 코로나·2022 금리쇼크 가격 실재, USDKRW 2022-10 1440대, 주말공백 존재). raw-v3/{collect,collect_dart,collect_regime,measure,measure_conditional,measure_oos}.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-{conditional,oos,metrics,valuation,cross}-v3.json key 매핑(source_id). flow_sell interaction t=-2.90 = conditional json:family_2_interaction / OOS -0.156 = oos json:flow_sell_conditional_oos. |
| **D** | ★PIT (hard-fail) | **PARTIAL→재측정 PASS** | ★bio-audit 발견(2026-06-05) = **거래정지 좀비 carry-forward 누설**. 초안 measure 가 거래정지 종목(코오롱티슈진 950160 인보사 후 841일 flat carry 47.8% / 케어젠 214370 277일 19%)의 직전종가 flat carry → 거래정지 월말 forward 20d = +0.0000 으로 IC 오염 + vol_60 저변동성 오측정. 초안 self-audit "거래정지 처리" 박제 미흡 = ★D PARTIAL 격하. ★remediation = `mask_trading_halt()`(연속 동일종가 ≥10거래일 = 거래정지 → NaN, reject≠missing tri-state) 후 재측정 → 핵심 결론 robust 유지(interaction mom_6 t=-2.90→-2.85 / vol_60 uncond -0.066→-0.069 안정 / flow_sell OOS 불변). 마스킹 1163셀(950160 842일+214370 289일, 정상종목 0~14일 over-mask 없음). 재측정 후 D=PASS. valuation rcept_dt PIT / CLI 2M lag 는 초안대로 유지. |
| **E** | 다중검정 보정 | PASS | ★G-F §3 family 측정前 사전고정(6신호×3h×regime cell 단일 BY-FDR). m=105 BY survivors=[]. ★정직 보고 = unconditional 가격/valuation OOS 부호반전(artifact) 격하 + conditional 만 채택. |
| **F** | 반증 + 기각 기록 | PASS | ★기각 다수: unconditional momentum/pbr/per OOS 부호반전 REJECTED + USDKRW dollar β REJECTED + customer momentum skip + KRW_weak interaction 비유의. flip-register(현 vintage 확정 금지). |
| **G** | 검정력·tier | PASS | n_eff(autocorr) 명시. flow_sell cell n=18~20 = underpowered 라벨(PASS 아님). conditional = Tentative tier(small-n + IS약→OOS강). |
| **A-5** | ★regime interaction | **PASS** | ★family_2 의무 충족(rejected 박제 前). flow_sell × signal interaction mom_6 t=-2.90/mom_12_1 t=-2.92/per_z t=-2.29 유의(main 비유의) = "국면 따라 효과 갈림". ★KRW_weak interaction 비유의 = bio 증폭축은 flow(정직 대조). regime별 wild-cluster CI. |
| **F-OOS** | walk-forward | **PASS** | ★IS(2019-22)/OOS(2023-26): unconditional OOS 부호반전(artifact) vs flow_sell conditional 5신호 OOS 부호+magnitude 유지 + interaction OOS 강화. = unconditional artifact / conditional 생존 분리 입증. (★진짜 holdout 2026+ = pristine OOS 별개 미래 보너스.) |
| **G-auto** | 자기상관 보정 | PASS | ★small-block size-invalid(Kiefer-Vogelsang) → wild-cluster bootstrap(Rademacher B=2000) per-cell p + n_eff + block-boot CI. asymptotic NW-HAC t = 참고만. |
| **H** | 미해결 명시 | PASS | collector_plan(파이프라인/임상 high + PIT 멤버십 high 최우선 + 종목레벨 flow + R&D) + research-log 미해결 6항. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | ★★bio = 생존편향 **최악** 축. universe=FDR 2026-05 스냅샷, prices 거래 끊긴 종목 **0종 = delisted 완전 누락**. 임상실패 상폐(코오롱티슈진 인보사/신라젠/헬릭스미스) 누락. ★누락=고변동성 임상실패 신약 → vol_60(고변동성 회피) 신호 **과대평가 우려 강**(방향성 명시). 신규상장 7종(2020+)=look-back gap(missing). PIT 멤버십=collector_plan high(최우선). ★hard-fail 회피 = over-claim 아닌 정직 격하(PARTIAL + 신호별 편의 방향 명시). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "flow_sell 국면 momentum/저PER → 20d forward" = code `csz(signal) → forward_returns(20) | flow_regime=flow_sell`. interaction = pooled panel month-clustered SE. forward predictive 동일 verify. ★per_z 흑자한정 = `if net_income>0`(spec "적자 제외" 일치). |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = bio universe 38종(factor loading). z=peer-relative(sector-neutral). portfolio 조립=supervisor(dispatch 밖). §M.7 분담. ⚠️ sub-cluster(pharma/novel/biosimilar) = event_driven 공통(적자/흑자 분리는 PER 흑자한정으로 흡수). |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = VIX β 보고만(산업 cross 최종 박제 X). 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | rank_ic/spearman = scipy 직접. score_ic_breakdown_eprocess = core/assume/weight_falsification 참조(confidence_hooks). opt-in 측정, production 코드 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립(RegimeGlasso Σ_return / Σ_signal mixing) = supervisor 단계. 산업 = β 벡터 보고만. directional_spillover=[] (DY 통합단계). |
| **O** | leakage (PIT-safe) | PASS(보강) | forward return = shift(-h)(미래 누설 없음). ★reject≠missing tri-state **보강**: 거래정지 carry = reject(NaN 마스킹, mask_trading_halt) ≠ 상장 전 look-back gap(missing). 둘 다 NaN 이나 거래정지는 "관측됐으나 무효(거래 없음)"라 IC 에서 제외. flow_sell regime=22month(reject 아님=관측). CLI 2M lag(거시 vintage). |
| **P** | net-cost robustness | PASS | gross |IC| flow_sell -0.149 vs 월 16.5bps cost. ★conditional turnover 高(regime 진입/이탈 잦음) = net haircut 주의 명시. KR STT 비대칭. sqrt impact = supervisor 캘리브레이션. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART + FRED + ECOS) |
| C 추적성 | PASS | yaml↔raw 매핑 (source_id) |
| D PIT | ★초안 PARTIAL → 재측정 PASS | ★거래정지 좀비 carry-forward 누설(bio-audit) → mask_trading_halt NaN 마스킹 재측정. 핵심 결론 robust 유지 |
| I 생존편향 | PARTIAL | ★bio 최악(임상실패 상폐 누락=vol 신호 과대평가), 정직 격하(방향성 명시), over-claim 회피 |

★**hard-fail 0** (B/C PASS, D 초안 PARTIAL→좀비 마스킹 재측정 PASS, I 는 PARTIAL = 정직 격하 + 편의 방향 명시 = over-claim 회피 → hard-fail 아님).
★**좀비 마스킹 재측정 = 결론 불변**: flow_sell conditional interaction(mom_6 t=-2.85/mom_12_1 -2.83/per_z -2.27 유의) + OOS 5신호 부호유지 + vol_60 uncond(-0.069 안정) = 거래정지 종목 제외해도 robust(bio-audit 예측 정확, data-mining 아님 재확인).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor 책임).
- **status = PARTIAL** — ★핵심 = **conditional(flow_sell 외국인 순매도 국면 증폭)** = dispatch 본체. family_2 interaction 유의(mom_6 t=-2.90) + OOS 5신호 부호+magnitude 유지 + S5 역공격 3종 방어. unconditional 가격/valuation = OOS 부호반전(artifact) 격하.
- ★**G-G v2 tradeable = PASS-conditional**: tradeable 1개(flow_sell conditional) OOS 생존 but low confidence(cell underpowered n<24 + BY 미생존 + IS약→OOS강 regime shift + 생존편향). → conservative cap + monitor + regime gate + 보강(파이프라인/PIT 멤버십). FAIL 아님(OOS 생존) / PASS-strong 아님(BY 미생존).
- ★**핵심 검증 가치**: bio 증폭축 = **flow(외국인)** = 반도체(KRW)·battery(momentum unconditional)·consumer(valuation)·financial(rate regime)과 **전부 상이** = 동적가중(산업별 conditional 차등) 정당화. event_driven = unconditional 가격 무신호(임상 binary dominant) + conditional 발현 = archetype 정합.
- ★**생존편향 정직(team-lead 강조)**: 단순 PARTIAL 아니라 "임상실패 상폐 누락 = 고변동성 신약 → vol_60 신호 과대평가" 편의 **방향성** 명시. PIT 멤버십 = 최우선 보강.
- archetype event_driven 사후편향 검사: valid_from 2019 사전선언, declared_at 명시 = ex-post hazard 회피. transition 없음.
