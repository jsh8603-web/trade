<!-- author: shipbuilding teammate (self-audit 초안, 2026-06-05) -->
<!-- ★최종 G-C 독립 audit = 별 세션 (author != auditor). 본 self-audit 은 참고용. -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — shipbuilding(조선) §M v3 (frame v3 §E, A~P 15축, 3컬럼)

> self-audit: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. semiconductor 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★조선 핵심 = cross-sectional selection 신호 ★구조적 약(H9 산업베타 지배). 전 신호 BY 미생존. 정직 박제(over-claim 0).

| 축 | ① 적용했나 | ② 측정 코드·수치 경로 | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론실재 | PASS | theory-notes.md §1-2 부호 사전확약(H1~H9). Stopford Maritime Economics + Cooper-Gulen-Schill 2008 + Damodaran + Clarkson + Gemini 리서치 | 9가설 ex-ante. HARKing 방지(측정 前 동결) |
| **B** ★실데이터 (hard) | **PASS** | raw-v3/{collect,measure_*}.py 재실행. pykrx OHLCV 16종(1818일) + yfinance(BDRY/CL=F/BOAT/VIX/dollar) + DART(356+371rows) + FDR Marcap | 합성 0%. 합성지문 PASS(USDKRW 2022/슈퍼사이클 5.09x/적자→흑자 전환 실재) |
| **C** ★추적성 (hard) | **PASS** | yaml 수치 → validation-conditional/valuation/cross/fundamentals-cycle/merged-fdr-v3.json key 매핑(source_id) | vol_60 IC -0.057=conditional.vol_60.y_20d / VIX β -0.0145=cross / per_z artifact=valuation |
| **D** ★PIT (hard) | **PASS** | 가격=forward shift. valuation=DART rcept_dt 이후만(보고지연 median 108-120일 실측). Macro=CLI_PUB_LAG 2 | lookahead·restatement 회피. 시총=Close×현재주식수(시점별 주식수=collector_plan high, 한계 명시) |
| **E** 다중검정 | PASS | merge_fdr_family.py 통합 BY-FDR. m_total=165(cond 87 + fund 78) survivors=0. M_eff_signal 3.0(Li-Ji) | ★전 신호 BY/Bonferroni 미생존 = 정직 보고(반도체보다 더 약). M_eff 통합=supervisor |
| **F** OOS/walk-forward | PASS | IS(2019-22)/OOS(2023-26) split. vol_60 IS-0.065→OOS-0.049 부호유지(유일). per_z 6M/12M ★부호반전 | vol_60 OOS 생존 + per_z artifact 노출. in-sample 결과 OOS 재현 검정 |
| **G** 자기상관 | PASS | wild-cluster bootstrap(Rademacher B=2000) per-cell + n_eff(autocorr) + block-boot CI. asymptotic NW-HAC 참고만 | small-block size-invalid(Kiefer-Vogelsang) 회피. vol_60 CI [-0.129,+0.020] 0포함 |
| **H** 미해결 명시 | PASS | collector_plan(Clarkson 수주/SCFI 운임 high / EV-EBITDA high / PIT 멤버십 high / PBR밴드 timing 이연) + verdict_detail | candidate-ledger 연결. 미해결 풍부(약신호 산업 = 보강 의제 多) |
| **I** ★생존편향 (hard) | **PARTIAL** | universe=FDR 현재 스냅샷. ★조선 신규상장 多(HD현대중공업 2021 재상장/대한조선 2024/현대힘스 2024/티엠씨 2025 = 16종 中 4종 부분이력) | delisted/M&A 누락 + look-back gap 큼. PIT 멤버십=collector_plan high. ★정직 격하(over-claim 아님) |
| **J** 측정 axis (spec↔code) | PASS | spec "cross-sectional 저변동 → 20d forward" = code `csz(vol_60) → forward_returns_daily(20)`. forward predictive 동일 | vol_60 부호 음(low-vol) 측정값 그대로 보고. ★per_z 양 IC도 그대로 보고 후 artifact 격하(over-claim 0) |
| **K** 분석 unit ↔ portfolio | PASS | 분석 unit = ship universe 16종(factor loading). z-score=peer-relative. portfolio=supervisor(§M.7) | ⚠️ 협소 universe(16종) sector-neutral z = demean 효과 약(telecom 13종 동형 경고) → magnitude hedge |
| **L** 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(산업 cross 최종 박제 X). 통합 supervisor L축 | VIX β 유의(고베타)만 보고. directional_spillover=[] (DY 통합단계) |
| **M** 코드충실 (wire) | PASS | score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출(재구현 X). opt-in 측정, production 미변경 | INV_R15_WEIGHTS 미접촉 |
| **N** cross 관계 PSD | N/A | cross 조립(RegimeGlasso/Σ_signal) = supervisor 단계. 산업 = β 벡터 보고만 | directional_spillover=[] (DY 통합단계). PSD 책임 밖 |
| **O** leakage (PIT-safe) | PASS | forward=shift(-h)(미래 누설 없음). reject≠missing: 상장 전 NaN=look-back gap(missing) / 적자기 PER NaN=관측(분모 음) | tri-state 구분. 신규상장 NaN = missing(reject 아님) |
| **P** net-cost robustness | PASS | gross \|IC\| 0.057 vs 월 16.5bps. KR STT 비대칭 | ★net 보존 marginal/약(breadth 협소 13.5종 IR 약 + low-vol turnover 낮음). sqrt impact=supervisor |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 재무 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (source_id) |
| D PIT | PASS | 가격 PIT-safe + valuation DART rcept_dt 이후만 |
| I 생존편향 | PARTIAL | 정직 격하(신규상장 多, look-back gap 큼), over-claim 회피 |

★**hard-fail 0** (B/C/D PASS, I 는 PARTIAL = 정직 격하).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor 책임).
- **status = PARTIAL_WEAK** — ★조선 = cross-sectional selection 신호 ★구조적 약. vol_60(저변동)만 OOS 부호유지(방향 prior, BY 미생존 + CI 0포함 = magnitude 비유의 = TENTATIVE DIRECTIONAL).
- ★**핵심 발견 (H9 입증)**: 산업 베타(슈퍼사이클 timing, 2022→2025 5.09x) 지배 → cross-sectional alpha 구조적 약. Maritime Economics·실측 정합. = 신호 본질 약(방법 결함 아님).
- ★**capex 일반화 verdict (team-lead)**: capex_ratio 무신호(IC≈0) = ★조선 미적용. asset growth anomaly 음 prior 약하게도 미발현. two-sided 로 one-sided 단정 회피한 게 정답.
- ★**per_z 24M artifact 격하**: BY 생존했으나 6M/12M OOS 반전 + avgN 6.9 small-universe + 24M degenerate(frame §M.12) = tradeable 자격 X. ★BY 생존 ≠ tradeable 교훈.
- ★**G-B 트리거 충족**(BY 0 + 약신호): family_2 검정 의무 이행=비유의 + Gemini 리서치(산업베타 지배) = "방법 결함 아닌 신호 본질 구조적 약" 근거. → team-lead 자문 발동 판정 보고.

## ★G-G v2 매매 신호 충분성 판정 (tradeable signal sufficiency)

- (a) 방향 확정(walk-forward OOS 부호유지): vol_60 ✅ / 나머지 ✗(반전/소멸)
- (b) tier ≥ structural_prior_low: vol_60 = TENTATIVE DIRECTIONAL(경계)
- (c) net-alpha 양: marginal/약(breadth 협소)
- (d) regime 조건 명시: vol_60 Reflation/flow_neutral 증폭 (✅ 국면 답 가능)
- ★**판정 = FAIL(부족) 경계 / PASS-conditional 최약**: tradeable = vol_60 1개뿐인데 CI 0포함 + BY 미생존 = magnitude 비유의(방향 prior만). per_z BY 생존=artifact 제외. → ★supervisor 판정 = monitor-only(최소 weight) 또는 G-B 자문 후 결정. ⛔ cross-sectional selection 강제투입 = over-trade 차단.

## ★섹터 timing 부활 측정 보강 (team-lead 지시 2026-06-05, summary.yaml sector_timing)
- **측정**: 산업 합산 PBR(Σ시총/Σ자본 PIT rcept_dt) rolling36M z → 산업 eq-weight forward IC (raw-v3/measure_sector_timing.py → validation-sector-timing-v3.json). B/C/D PASS (실데이터 PBR 0.58~5.34x, yaml↔json verify, PIT rcept_dt).
- **F축 walk-forward**: ★12M IC +0.373 BY 생존했으나 ★artifact — IS 음(-0.582 mean-reversion)→OOS 양(+0.412) 부호반전(슈퍼사이클 trend). 1M/3M OOS 소멸. n_eff 10(PBR_z persistence).
- ★**부활 실패 = 섹터 timing 도 약**: PBR 밴드 mean-reversion 가설이 2023-26 슈퍼사이클 구간서 반전. ★섹터 timing sleeve 격상 ★불가. monitor-only(슈퍼사이클 정점 de-risk 참고). per_z 24M 과 동일 BY생존≠tradeable artifact 패턴.
- ★Clarkson 수주/SCFI 운임 timing 변수 = collector_plan high (유료 부재, 미측정).
