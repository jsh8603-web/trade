<!-- author: aitech-analyst teammate (1단계 산출, 2026-06-05) -->
<!-- auditor: ★G-C 독립 audit teammate (메인 스폰, author != auditor), 2026-06-05 -->
<!-- ★G-C audit 결과: 부분 PASS — hard-fail 0 확정. pbr_z = validated_alpha(12종목군 中 가장 강한 신호, block-boot CI 0배제 + size위장 아님 t=-3.51 + LOO 전부 독립 재현). momentum reversal growth반증 진짜(LOO 26종 전부 음). 코드화 자격 충족. -->
<!-- ★보강 반영(2026-06-05): 게임 좀비 carry-forward(셀바스AI 284일 halt) 마스킹 → mom magnitude ~9% 보정 부호·유의 불변. D PARTIAL 격하. per_z 격하 유지. validation-zombie-v3.json. -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — AItech §M v3 (frame v3 §E, A~P 15축)

> self-audit 초안: yaml↔raw 재현·hard-fail 0 self-check. raw 재현 = `raw-v3/*.py`. semiconductor 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★최종 G-C 독립 audit = 별 세션(메인 스폰). 본 self-audit 은 참고용.

| 축 | 항목 | 판정 | 근거 (① 적용 ② 측정 코드·수치 경로 ③ 결과) |
|---|---|---|---|
| **A** | 이론 실재 / 가설 사전선언 | PASS | ① theory-notes §1-7 학술 ground(Jegadeesh-Titman/Fama-French/Daniel-Hirshleifer-Subrahmanyam/Choe-Kho-Stulz) ② round-1.md 측정前 작성(부호 사전확약) ③ growth 가설 사전선언 → 데이터 반증(momentum reversal) = HARKing 아님(반증 자체가 finding). archetype valid_from 2019 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | ① 합성 0% ② pykrx OHLCV 26종(1818일) + yfinance(QQQ/NVDA/VIX/dollar/oil/rate) + DART(financials 674rows + extended 696rows) + FDR Marcap + FRED/ECOS regime ③ raw-v3/*.py 재실행 가능. 합성지문: 2020-03 코로나·2022 폭락 실재. |
| **B** | 합성지문 검사 | PASS | ① §0 합성 지문 ② regime_series 2022-10 USDKRW 1440+/CLI 2020 저점/외국인 대량매도 실재 ③ 결측·갭 정상(게임주 상장시점 차이). |
| **C** | ★추적성 (hard-fail) | **PASS** | ① yaml 수치 → json key 매핑 ② source_id 전부 박제 ③ pbr -0.183=validation-valuation-v3.json:pbr_z__12M / mom -0.106=validation-metrics-v3.json:mom_12_1__12M_mom / credit -0.071=validation-cross-v3.json / Q1 t=-3.51=validation-critique-v3.json. |
| **D** | ★PIT (hard-fail) | **PARTIAL** | ① 가격 PIT-safe(forward shift) ② valuation = DART rcept_dt 이후만 + Macro CLI_PUB_LAG=2 ③ ★[G-C audit 격하] (1) ★좀비 carry-forward = 셀바스AI(108860) 거래정지 284일 px 고정 → mom 신호 오염 → zombie(amt==0 OR 연속동일종가≥10일) NaN 마스킹(reject≠missing) 후 mom -0.1055→-0.0963 부호·유의 불변(validation-zombie-v3.json) (2) 시총=Close×현재주식수 근사(collector_plan high). ★pbr 좀비 Δ=0.0(공시후 진입) = validated_alpha 견고. 정직 격하(PARTIAL, 부호결론 robust = hard-fail 아님). |
| **E** | 다중검정 보정 | PASS | ① BY-FDR + M_eff ② valuation family m=8 BY(factor 2.718) → pbr 전 horizon+per 일부 생존 / momentum family m=16 BY → 생존 0 / conditional m=105 → 생존 0 ③ ★정직 보고 = valuation 강(BY 생존), momentum 약(미생존). over-claim 0. |
| **E** | 자문 환각 cross-verify | PASS | ① QQQ/NVDA proxy ② customer momentum 전 lag 비유의 = REJECTED ③ 무비판 채택 0(forward falsifier 작동). |
| **F** | 반증 + 기각 기록 | PASS | ① 반증조건 사전 + 기각 ② growth=continuation 가설 기각(reversal) / customer momentum REJECTED / per_z episode 종속 격하 / fundamentals cycle 전부 INSUFFICIENT ③ 기각 다수 = p-hacking 아님. |
| **G** | 검정력·tier | PASS | ① n_eff + tier ② pbr Validated(n=73, BY 생존, t=7.98) / momentum Tentative(n=65, BY 미생존) / per 격하(episode) ③ MDE: pbr t_obs 7.98 well-powered, momentum 2.58 경계. |
| **H** | 미해결 의문 | PASS | ① collector_plan + verdict ② E/P 대체(per 편의) / PIT 멤버십(게임 상폐) / DAU·신작 ledger / EV-EBITDA ③ candidate-ledger 연결. |
| **I** | ★생존편향 (hard-fail) | PARTIAL | ① universe=FDR 현재 스냅샷(생존종목) ② 26종 中 22 full / 4 partial(신규상장) ③ ★게임주 상폐多(P2E 붕괴 2022-23) = 생존편향 위험 상대적 큼(bio 동형). PIT 멤버십=collector_plan high. ★hard-fail 회피 = 정직 격하(PARTIAL + note), over-claim 아님. |
| **J** | 측정 axis 일치 (spec↔code) | PASS | ① spec↔code 1:1 ② spec "cross-sectional PBR_z → 12M forward" = code `csz(PBR) → forward_returns(12M)` ③ forward predictive 동일 verify. 부호 음(value premium/reversal) = 측정값 그대로(over-claim 없음). |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | ① 분석 unit = aitech 26종(factor loading), z=peer-relative ② ★A-4 sub-cluster 부호점검(measure_subcluster.py): valuation 3 cluster 부호 일관(cancel 없음) ③ momentum reversal game-dominant(internet 무신호)이나 cancel 아님 = 통합 유지. portfolio 조립=supervisor(§M.7). |
| **L** | 공통인자 1회 계상 | PASS | ① common_factor_exposure = β 보고만 ② credit/rate/dollar/VIX/oil β + CI ③ 산업이 cross 최종 박제 X = 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | ① rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출 ② 재구현 X ③ opt-in 측정, production 코드 미변경. |
| **N** | cross 관계 PSD | N/A | ① cross 조립(RegimeGlasso Σ_return / Σ_signal) = supervisor 단계 ② 산업 = β 벡터 보고만 ③ directional_spillover=[] (DY 통합단계) = PSD 책임 밖. |
| **O** | leakage (PIT-safe) | PASS | ① forward = shift(-h) 미래 누설 없음 ② reject≠missing tri-state: 상장 전 NaN=look-back gap(missing), regime bear=10month(reject 아님=관측), ★좀비(거래정지 carry-forward)=reject(NaN 마스킹, missing 아님 = 관측됐으나 무효) ③ DART rcept_dt 이후만. |
| **P** | net-cost robustness | PASS | ① gross→net ② pbr \|IC\| 0.18 vs 월 16.5bps = gross 50%+ 보존(저회전 value) ③ momentum reversal turnover caveat. KR STT 비대칭. sqrt impact=supervisor. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 재무 + extended 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (source_id) |
| D PIT | PARTIAL | ★G-C audit 격하: 좀비 carry-forward(셀바스AI 284일, 마스킹 후 부호불변) + shares 현재주식수 근사. 부호결론 robust = hard-fail 아님 |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL, ★게임 상폐 위험 + 좀비 명시), over-claim 회피 |

★**hard-fail 0** (B/C PASS, D·I 는 PARTIAL = 정직 격하로 over-claim 회피 → hard-fail 아님). ★G-C 독립 audit 확인.

## verdict

- 코어 4축 위반 0. 조건부 E/F/J/K/L/M/O/P PASS, N=N/A(supervisor 책임).
- **status = PARTIAL CONFIRMED** — ★primary cs_pbr_z_value = PASS-strong(BY 생존, size 위장 아님 t=-3.51, CPCV 1.00, within 100%, OES 강화). momentum reversal = PARTIAL(BY 미생존, game-dominant).
- ★**핵심 검증 가치 1 (team-lead 질문 답)**: ★momentum 부호 = **음(reversal)** = battery(양 continuation)와 반대 = ★"성장주(growth)라고 momentum continuation 아니다" = growth=battery 사전가설 **데이터 반증**. 부호 검증이 archetype 판별에 결정적(battery growth 일반화 금지 = memory 자산화).
- ★**핵심 검증 가치 2**: ★valuation premium 강(pbr BY 생존, size 위장 아님) = AItech = asset_stable/value 작동(consumer/telecom 동형) = semiconductor/auto(peak-EPS PER✗)와 다른 archetype. = §M 양식이 archetype별 신호 차등 잡아냄.
- ★**sub-cluster A-4**: valuation 부호 일관(cancel 없음, 통합 유지) + momentum reversal game-dominant(internet 무신호) = 통합 sleeve 유지, momentum 게임 종목 한정 명시.
- archetype 사후편향(M.5): valid_from 2019 사전선언, declared_at 명시. 사전 growth 가설 → 실측 value 정정(데이터 기반, ex-post hazard 아님).
- ★pilot 결론(미러): cross-sectional 메커니즘 작동 + 부호가 산업 특성(growth≠momentum continuation) 반영 = 부호 검증의 가치 재확인(battery 양 / 반도체 음 reversal / aitech 음 reversal + value). 

## ★S2 conditional IC surface self-audit (dispatch 원의도 본체)

| 축 | conditional 판정 | 근거 |
|---|---|---|
| **A-5** ★regime interaction | **PASS** | ① family_2 의무(rejected 박제 前) ② flow_strong_buy interaction mom_12_1 t=-2.71 유의(main 비유의) = "국면 따라 부호 갈림" + walkforward OOS t=-2.71 재현 ③ vol/pbr interaction 근접(비유의), KRW_weak interaction 비유의(정직). |
| **F** OOS/walk-forward | **PASS** | ① IS(2019-22)/OOS(2023-26) split ② pbr/per/mom/per_z-KRW_weak 전부 OOS 부호+magnitude 유지(pbr -0.060→-0.123 강화) + interaction OOS t=-2.71 ③ in-sample artifact 아님. |
| **K** 비판검토 | PASS | ① 데이터 직접 검정 ② Q1 PBR size위장 기각(Fama-MacBeth t=-3.51) + Q2 per_z episode종속 발견(격하) + Q3 leave-2022 생존 ③ 무비판 채택 0. |

- ★conditional 측정 hard-fail 0 (B/C/D PASS, I PARTIAL). G-B = "약함" 아님(valuation BY 생존 + interaction 유의). M_eff 통합=supervisor.

---

# ★ROTATION 신호 self-audit (업종 자체 비중 timing, ★후보 13개 전수, 2026-06-05)

> rotation-signals.md + summary.yaml rotation 섹션. raw = collect_aitech_cycle(_ext).py + measure_rotation(_ext).py → validation-rotation(_ext)-v1.json.
> ★team-lead 재보강 = 후보 ≥8-10개 전수 → 13개 검토(rate/nasdaq/nvda/soxx/hyperscaler/power/sw/game/vix/cloud/spread/usdkrw/rel_mom).

| 축 | rotation 판정 | 근거 |
|---|---|---|
| **A** 이론실재 | PASS | ① rotation-signals §1 후보 13개 부호 사전확약(measure 前) ② Gordon growth duration / Stovall rotation / Molchanov myth ③ data-mining 차단(이론 명확 신호만 채택). |
| **B** ★실데이터 | PASS | ① 합성 0% ② yfinance 10종(NVDA/QQQ/^TNX/SOXX/MSFT/GOOGL/AMZN/XLU/IGV/ESPO/VIX/SKYY) + pykrx 업종 eq-weight + regime ③ collect_aitech_cycle(_ext).py 재현. |
| **C** ★추적성 | PASS | ① yaml→json 매핑 ② game_espo +0.382=validation-rotation-ext-v1.json:candidates.game_espo / rate_10y -0.273 / usdkrw -0.364 ③ 전 수치 source_id. |
| **D** ★PIT | PASS | ① cycle spot 실시간(lag X) + 업종수익 forward shift(-h) + ★좀비 마스킹(셀바스AI 284일) ② 미래 누설 없음. |
| **F** OOS | PASS | ① IS/OOS 2023 split ② 채택 4 전부 OOS 유지(game +0.287→+0.415 강화) ③ REJECTED(nvda/soxx/power/rel_mom)=OOS flip 정직. |
| **A-3** data-mining 차단 | PASS | ① 후보 13개 부호 사전확약 vs 실측 전수 대조 ② 채택 4(이론+통계일치) / REJECTED 7(이론반증 or flip) / 약 2(wc_p>0.10) ③ raw momentum 무신호→residualize 후만 reversal. 이론없이 통계만=채택 0. |
| **F** 반증기록 | PASS | ① 후보 13개 中 REJECTED 7 기록 ② ★usdkrw 부호반증(통계강 wc_p0.002 but 이론반대=내수성장주 발견 memory) + vix/power/spread 반증 + nvda/soxx flip ③ 기각 7/13 = p-hacking 아님. |
| **G** 검정력 | PARTIAL | ① t_power ② 전 후보 underpowered(t<2.802, n_eff 25-33, BY 미생존 m=52) ③ ★TENTATIVE 상한. game_espo만 CI 0배제(최견고). 채택 4 상호상관 높음 N_eff~2. |

- ★rotation hard-fail 0 (B/C/D PASS). ★verdict = TENTATIVE-PASS (후보 13개 전수): 채택 4 = ★game_espo(글로벌 게임 cycle +0.382 최강 CI 0배제) > rate_10y(금리 음) > global_sw_igv > cloud_skyy = ★글로벌 tech/게임 성장 cycle + 금리 duration = growth archetype 정합. REJECTED 7(ai_capex/soxx/power/vix/spread/rel_mom + ★usdkrw 부호반증=내수성장주). ★종목selection(pbr validated_alpha)=primary, rotation(게임 cycle+금리 tilt)=보조 overlay. underpowered=TENTATIVE.
