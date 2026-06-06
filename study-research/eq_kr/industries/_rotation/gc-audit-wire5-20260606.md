<!-- G-C WIRE5 코드화 완전성 audit (author=메인 ≠ auditor=steel-audit teammate opus1m). 2026-06-06 -->
<!-- 읽기전용. _sleeve_rotation_kr/within_industry_residual_kr 직접 재실행 + 자문 RESULTS C1~C13 매핑. -->

# WIRE5 rotation 코드화 완전성 audit — PASS (hard-fail 0, minor 2)

> verdict: **PASS (코드화 충실)**. 자문 C1~C13 핵심 전부 반영, ★C11 N_eff 이중처벌 방지 정확 구현, double-count 직교(~0), production import 0, 통계 정직(OOS IR≈0 over-claim 없음). minor 2건(C12 EB 미구현 / git production working-copy 변경 별개작업).

## 1. 자문 RESULTS C1~C13 매핑표

| # | 자문 결론 | 코드 반영 | 위치 | 판정 |
|---|---|---|---|---|
| C1 | 시계열 residualize 폐기 → CS demean | signal_z_cs: expanding z + Z.sub(Z.mean(axis=1)) CS demean + CS std 정규화 | _sleeve L53-60 | ✅반영 (+ expanding z 선행 = 신호 스케일 이질 보정, 자문 동질가정 보완) |
| C2 | base 잔차RP 폐기 → sleeve-RP × within-EW | base_sleeve_rp_ew: sleeve간 1/σ RP × sleeve내 EW | _sleeve L63-81 | ✅반영 |
| C3 | silo 폐기 → cross-sleeve rotation capped 허용, k=2 유지 | SLEEVES k=2(export_cyclical/defensive_it). build_weights가 sleeve 경계 없이 전산업 tilt(silo 없음) | _sleeve L34-37,124-142 | ✅반영 |
| C4 | binary OOS gate 폐기 → 연속수축 κ | kappa = robust gate(block-boot 부호안정+mag floor) × |IC|/(|IC|+ic0) | _sleeve L84-121 | ✅반영 |
| C5 | N_eff cap(개수3) 폐기 → risk budget sizing | active-share 컨트롤러(cap15%)로 대체, 12산업 full 차등 | _sleeve L136-142 | ✅반영 |
| C6 | tilt = z-비례 연속 ±5% per-name cap, additive | np.clip(κ×s_rot×z, ±0.05) additive(base_w+tilt) | _sleeve L124-134 | ✅반영 (additive 명시, multiplicative 회피 주석) |
| C7 | active 천장 15% cap / 8~12% 운용 | CAP_ACTIVE=0.15, BAND=(0.08,0.12), TARGET_AS=0.10, calib_s_rot | _sleeve L42-46,145-155 | ✅반영 (실측 mean 0.114 band 내) |
| C8 | 변별력(active)≠베팅크기(TE) 분리 | yaml §9 "OOS IR≈0(변별력≠alpha)" 정직 박제 | yaml §9 결과 | ✅반영 |
| C9 | W_i·v_{j|i} 독립 베팅 | within v2 = selection ρ만, rotation κ와 별 모듈(독립) | within L8-9 | ✅반영 |
| C10 | 잔차불안정 → L2 자르기 아니라 v 산업중립 수축 | ρ_i 수축(selection만), rotation κ 무관 | within L94 원칙 | ✅반영 |
| **C11** | ★N_eff = selection ρ에만 1회, rotation κ엔 σ만(이중처벌 방지) | ★rotation κ(_sleeve)=IC+sign_stable만, N_eff **없음** / selection ρ(within)=N_eff PR 1회 | _sleeve L114-121 + within L68-86 | ✅**정확 구현** (핵심) |
| C12 | per-industry IC = EB partial-pool 필수(IC_i^PP = w·IC_i+(1-w)·IC_bar) | ★capsule IC를 SSOT로 raw 사용 + N_eff/signal/gate로 ρ 수축. **DerSimonian-Laird EB shrinkage 미구현** | within L29-43,68-86 | ⚠️**부분** (아래 minor1) |
| C13 | L2 축소 정당 3채널(구현결합/공유신호/위험예산)만 | 원칙 박제(within L94), default=v 중립 수축 | within meta | ✅설계 반영 |

→ **C1~C11, C13 = 코드 반영, 누락/왜곡 0**. C12만 부분(아래).

## 2. ★C11 N_eff 이중처벌 방지 — 직접 확인 (핵심)
- **rotation κ** (_sleeve_rotation_kr.py kappa_per_industry L114-121): 입력 = `abs(ic)` + `sign_stable` gate만. **N_eff 부재** ✓
- **selection ρ** (within_industry_residual_kr.py L76-86): `[N_eff/(N_eff+n0)] × [|IC|/(|IC|+ic0)] × gate`. N_eff **1회** ✓
- = 자문 C11/R3 수렴("γ=ρ는 단일채널만, κ별도채널이면 이중처벌") 정확 구현. ★PASS.

## 3. ★double-count (내 비판①) — 직접 재실행 확인
double_count_check 재실행 결과: **net 공통인자 노출 = d_usdkrw -0.00313, foreign +0.00000, semi_ppi_yoy +0.00113 ≈ 0** ✓
- CS demean 직교성 진짜 = rotation tilt가 1층(공통인자)과 직교, double-count 없음 입증. ★PASS.

## 4. production 무접촉 (byte-identical)
- WIRE5 코드(_sleeve/within)는 core/stock/engine import **0** (grep 확인) ✓. measure_integration만 import.
- ⚠️ **단 git working tree에 production 변경 존재**: `core/stock_track.py`(+28) + `stock/value_trigger.py`(+15) modified. ★**WIRE5 작업과 무관**(_rotation 파일이 stock_track/value_trigger 참조 0, 마지막 커밋 2026-05-30 R15/production 별개작업). WIRE5 코드 범위 byte-identical은 맞으나, git 레벨 production 변경은 별도 작업(R15/stock-corr-layer)의 uncommitted 산물 = team-lead 확인 권고(WIRE5 책임 아님).

## 5. 통계 정직성 (over-claim 점검)
- **active share mean 0.114** (band 8~12% 내, cap 15% max 0.150 준수) ✓
- **OOS active IR = 0.043 ≈ 0** → yaml §9 "OOS IR≈0(변별력≠alpha, 자문 C7+§8 underpowered 실측)" = ★**over-claim 없음**(자문 C7 "IR 0.18~0.25" 미달을 정직 박제, C8 "변별력≠TE" 정합).
- κ 통과 4산업(chemical/steel/refining/telecom IC≥0.29 sign_stable) 비대칭 고밀도 = C8 "확신 상위 1~2 집중" 정합.
- capsule IC SSOT 대조: semiconductor -0.114↔summary -0.1142 ✓ / aitech -0.183↔-0.1834 ✓ / chemical -0.142↔-0.142 ✓ / steel -0.181(내 audit 일치) ✓ / auto -0.117↔summary uncond -0.108(±5% 이내, capex 셀 차이 minor).

## 6. yaml §9 ↔ 코드 결과 정합
- active 0.114 / double-count ~0 / OOS IR≈0 / κ통과 4산업 / 13배 차등(chemical 0.8~10.5%, telecom 13~21%) = yaml §9 결과 박제와 **정합** ✓.
- steel iron_ore "보조보강 incremental t<1.1=중복→단일 driver 정직"(yaml L47) + auto "iron_ore post-hoc 격상금지(audit minor4)"(L49) = 내 rotation audit 권고 반영됨 ✓.

## minor 발견 (non-blocking)
1. **C12 EB partial-pool 미구현**: 자문 C12는 산업간 IC shrinkage(IC_i^PP = w·IC_i+(1-w)·IC_bar, DerSimonian-Laird) 요구. 코드는 capsule IC를 raw SSOT로 쓰고 "capsule이 이미 partial-pool급(BY/OOS/CPCV)"이라 논리. ★단 capsule 검증은 산업**내** 검증이지 산업**간** shrinkage 아님 = C12 "산업간 대평균 끌림"과 다른 차원. small-n 산업(chemical N_eff4.4/auto7.3) IC가 대평균으로 안 끌림 = magnitude 과대 잔존 소지. → 통합단계 EB shrinkage 1줄 추가 권고(ρ는 이미 N_eff 수축하나 IC 자체 shrinkage는 별개).
2. **git production working-copy 변경**(core/stock_track.py, stock/value_trigger.py) = WIRE5 무관 별개작업(R15) uncommitted. team-lead 확인 권고.

## 판정
**PASS (코드화 충실, hard-fail 0)**. 자문 C1~C11/C13 정확 반영, ★C11 이중처벌 방지 + double-count 직교(~0) + OOS IR≈0 over-claim 없음이 핵심 통과. minor 2건은 통합단계/별도확인 권고(코드화 자격엔 무영향).
