---
tags: [type/verification, domain/eq-kr, topic/wire5-yaml-code-mapping]
date: 2026-06-06
purpose: rotation-study_session.yaml 스터디 spec §1~§9 ↔ WIRE5 코드 전수 1:1 대조 (완전성 검증)
auditor: steel-audit teammate 교차 검증 대상 (author=메인≠auditor)
---

# WIRE5 yaml↔코드 전수 대조 (§1~§9 개별 전수)

> 코드 3파일: `build_rotation_signal_panel.py`(B) / `_sleeve_rotation_kr.py`(S) / `within_industry_residual_kr.py`(W).
> 반영 = ✅ / 부분 = ⚠️ / 이연(통합단계·go-live) = ⏸ / 변경(설계 의도적) = 🔧

## §1. 배선식 (combination_formula)

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| capital_weight `w_j=W_i×v_{j\|i}` 곱(fund-of-sleeves) | S(W_i)/W(v 분석) 따로 | ⏸ | 2층 W_i=S.build_weights, 3층 v=W 분석. **결합 곱 코드 미구현**=통합단계(yaml "검증:조립 후" 명시). go-live 인접 사람게이트 |
| L3 macro-neutral demean(double-count 회피) | S.signal_z_cs | 🔧 | 시계열 residualize → cross-sectional demean(자문 C1). S.double_count_check가 net 공통인자~0 실증 |
| L축 1회계상(telecom 외국인flow 제외) | B.EXCLUDED `외국인flow` | ✅ | build_panel 외국인flow 미투입, telecom=semi_ppi 한정 |
| cli_chg 1층 분리 | B.EXCLUDED `cli_chg` | ✅ | build_panel cli_chg 제외(1층 timing) |
| 검증(net common-factor exposure 대조) | S.double_count_check | ✅ | net d_usdkrw -0.003/foreign 0/semi_ppi 0.001 ≈0 |

## §2. sleeve 구조 (k=2)

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| k_star=1 → 보수 k=2 | S.SLEEVES (2개) | ✅ | export_cyclical/defensive_it |
| export_cyclical 9 members | S.SLEEVES["export_cyclical"] | ✅ | semi/auto/financial/battery/chemical/refining/ship/steel/consumer |
| defensive_it 3(bio·telecom·aitech) | S.SLEEVES["defensive_it"] | ✅ | 3종 일치 |
| bio_singleton | S.SLEEVES(defensive_it 내 bio, line 36-38) | 🔧 | ★의도적 멤버 유지: bio 별도 sleeve化 시 3-sleeve RP서 base 32% 과대(부작용). cross-sectional tilt가 bio 자기신호로 이미 독립 처리(silo 무관)=격리 충족. yaml "별도 또는 PC2 내 독립"=PC2 내 독립 해석. (★steel-audit "별도 sleeve 추가" 보고는 착오 — 현 코드 base=0.183=defensive_it 멤버, 별도였다면 0.322) |
| sub_singleton_gating(refining/financial 고유 cycle·신용확대 시만 독립 tilt) | S.SUB_GATED+SUB_THRESH(line 43-44) | ✅ | ship=weight0 ✅ / refining+financial SUB_GATED={refining,financial}, build_weights `\|z_cs\|<1.0 → tilt 0`(평소 base 유지, 신호 발현 시만 독립 tilt). 재실행 refining [0.006,0.085] |

## §3. 12산업 verdict (신호·부호)

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| STRONG 4(chemical/steel/battery/auto) + 신호 | B.SIGNALS | ✅ | 각 sig_* 함수, 부호 OW 정렬 |
| tradeable(aitech/telecom/bio/consumer/semi) | B.SIGNALS | ✅ | 11산업 추출 |
| tradeable_weak(refining/financial) | B.SIGNALS | ✅ | 유가mean-rev/credit_spread |
| shipbuilding monitor weight0 | B(ship 제외)+S.MONITOR | ✅ | 신호 미투입+weight0 |
| chemical mom_3 폐기(G-C hard-fail) | B.sig_chemical(spread만) | ✅ | mom_3 미투입 주석 |
| consumer primary=cosmetics reversal | B.sig_consumer | ✅ | mom_6 cosmetics, CSI 미투입(tentative) |

## §4. hierarchical sleeve-gatekeeping FDR

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| step1 sleeve-level FDR | — | ⏸ | **미구현**. yaml "현단계: sleeve 미확정...실제 적용=supervisor 통합 yaml" 명시 이연 |
| step2 within-sleeve local FDR | — | ⏸ | 동상 (통합단계) |
| program_dsr | S.kappa(dsr_proxy 부분) | ⚠️ | v2는 robust gate(block-boot)로 대체. program DSR 정식 미구현(통합단계) |

## §5. gated 설계

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| base sleeve residual RP | S.base_sleeve_rp_ew | 🔧 | 잔차-name RP → sleeve-RP×within-EW(자문 C2, defensive 편중 제거) |
| tilt additive-on-active-share + clip | S.build_weights | ✅ | additive `base+tilt`, clip ±5%p, active 컨트롤러 cap15% |
| over-trade ① hysteresis | S.walk_forward(HYST_BAND) | ✅ | prev 대비 \|Δw\|<1%p → prev 유지. ★hysteresis renorm 후 active cap 재적용(audit fix, line 223後)=천장 0.15 보존(이전 max 0.156 초과) |
| over-trade ② persistence | S.expanding_z | ✅ | expanding z 지속성 내재(별도 k개월 불요) |
| over-trade ③ cost-aware | S.walk_forward(STT_SELL/COST_PER_SIDE) | ✅ | turnover×(commission+STT0.23%/2) 차감 |
| κ=DSR×N_eff×live-OOS | S.kappa_per_industry | 🔧 | κ=robust gate×\|IC\|/(\|IC\|+ic0). **N_eff 제거**(C11 이중처벌 방지, §6 변경) |
| tilt_capacity(base 비례 금지) | S.build_weights | ✅ | additive=base 무관, κ 신뢰도 기반 |
| monitor_only(ship weight0, financial gated) | S.MONITOR+SUB_GATED | ✅ | ship weight0 ✅ / financial=SUB_GATED 포함, credit z 발현(\|z\|≥1) 시만 독립 tilt(평소 base 유지)=gated overlay 구현 |
| net_cost(roundtrip 23bps) | S(COST_PER_SIDE+STT) | ✅ | cost-aware 반영 |

## §6. N_eff

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| residual N_eff 3.52 | W.participation_ratio | ✅ | idio 분산 PR 실측(과점 자동감지 chemical 4.4) |
| 동시 active tilt floor(3.5)=3 cap | S(제거)+active 컨트롤러 | 🔧 | **rotation N_eff cap 폐기→active-share risk budget**(C5). N_eff는 W.selection ρ에만 1회 |
| bet sizing=N_eff scale | S.active 컨트롤러 / W.rho_i | ✅ | rotation=active band, selection=ρ(N_eff PR) |
| C12 산업간 EB shrinkage(small-n IC 대평균 끌림) | W.main(w_eb, ic_pp, line 73-84) | ✅ | DerSimonian-Laird \|IC\| 공간(★부호 보존, battery + 유지) w_eb=N_eff/(N_eff+n0). chemical N_eff4.4 magnitude 과대 보정. ρ에 ic_pp(shrunk) 사용 |

## §7. audit minor 4 / §8. caveat

| yaml spec | 코드 위치 | 판정 | 증거 |
|---|---|---|---|
| minor1 좀비 마스킹 | B(MI.panel_monthly) | ✅ | measure_integration mask_zombies 재사용 |
| minor3 chemical strict NCC | B.sig_chemical | ✅ | chem_rotation_cycle(strict) |
| §8 전 신호 underpowered=tentative | S.meta honest | ✅ | "magnitude tentative, OOS≈0" 박제 |
| §8 proxy 한계 | B(cycle parquet=글로벌 proxy) | ✅ | meta 주석 |

## §9. WIRE5 결과 (자기참조)

| yaml spec | 코드 | 판정 |
|---|---|---|
| layer2 active mean 10.1%(cap fix 후)/max 15.0%/13배 차등 | S 산출 = yaml §9 일치 | ✅ |
| layer3 selection 등급(반도체0.36/철강0.29/aitech0.28) | W 산출 = yaml §9 일치(EB 재실측) | ✅ |
| double-count net~0 | S.double_count_check = yaml §9 | ✅ |
| OOS IR=-0.07(cost+cap fix) tentative | S.oos_active_ref = yaml §9 | ✅ |

---

## 종합 판정 (전수, 2026-06-06 갱신 — 코드 보완 후 + steel-audit 2차)

- ✅ 반영 = 대부분 (신호 패널·sleeve·tilt·over-trade 3중·N_eff PR·selection·double-count·caveat·**sub-gating·EB·cap fix**)
- 🔧 의도적 변경 5 = CS demean(C1) / base sleeve-RP×EW(C2) / κ N_eff 제거(C11/C5) / N_eff cap→active 컨트롤러(C5) / **bio defensive_it 멤버 유지(별도 sleeve 시 base 32% 과대, cross-sectional tilt가 독립 처리)**. 전부 자문 3R 근거 + yaml §9 박제.
- ⏸ 이연 2 = **곱 결합 W_i×v_{j\|i}(통합단계 go-live) / hierarchical FDR(yaml 자체 통합단계 명시)** — 현 단계 미구현 정상

### ★보완 완료 (이전 ⚠️3 + audit 권고 해소)
1. ✅ refining/financial sub-gating = `SUB_GATED`+`SUB_THRESH=1.0` 구현(신호 발현 시만 독립 tilt). yaml §2/§5 정합.
2. ✅ bio 격리 = defensive_it 멤버 유지가 의도적 설계(별도 sleeve化 시 32% 과대). 🔧 분류로 정정.
3. ✅ C12 EB shrinkage = within `w_eb`/`ic_pp`(부호 보존) 구현.
4. ✅ active cap = hysteresis 후 재적용(audit fix)으로 천장 0.15 보존(이전 max 0.156→0.150).
5. ⏸ 곱 결합·FDR = 통합단계(go-live) 이연이 yaml 의도와 정합(현 단계 미구현 정상).

### ★steel-audit 무비판 검증 메모 (2026-06-06)
- audit가 "bio_singleton 별도 sleeve 추가됨(base 0.322)"으로 보고했으나 **현 코드와 불일치** — 현 코드 bio는 defensive_it 멤버(base 0.183 재실측 확인). 별도 sleeve化는 32% 과대 부작용이라 의도적으로 멤버 유지. audit 착오로 판단, 메인이 코드 직접 확인 후 🔧(의도적 설계)로 정정. (자문·audit 무비판 수용 금지 원칙 적용)
- audit의 EB·sub-gating·cap 초과(0.156) 발견은 정확 → 반영 완료.
