---
tags: [type/audit, domain/inv, phase/study-system, sid/bond_cash, version/v5]
date: 2026-06-01
auditor: opus-1m 독립 12축 audit subagent (self-certify 금지, raw 재실행 기반)
target: study-research/bond_cash/raw/sub-clusters/summary_v5.yaml (Phase 7 옵션 A)
recompute_script: raw/_v2_analysis/_audit_recompute_v5.py (독립 재계산, 실행 완료)
predecessor_audit: raw/evaluation-bond_cash-20260531.md (a75ab5a2, v4 PARTIAL)
---

# [감사] bond_cash v5 — verdict: 충실 (hard-fail 코어 4 = 0)

## §0. Provenance + Recomputation (제1원리)

방의 yaml 숫자를 claim 으로 취급, raw parquet 에서 독립 재계산. **전 핵심 수치 1:1 재현**:

| claim | yaml/log 값 | 독립 재계산 | 일치 |
|---|---|---|---|
| KW vs ACM level corr | 0.8597 | **0.8597** | ✅ exact |
| KW vs ACM d20 corr | 0.7241 | **0.7241** | ✅ exact |
| mean(ACM-KW) | 0.2553 | **0.2553** | ✅ exact |
| v5 panel n | 4814 | **4814** | ✅ exact |
| HYG rate_up_vol_high IS/OOS | +0.0059 / -0.0762 | **+0.0059 / -0.0762** | ✅ exact (부호반전 재현) |
| HYG rate_up_vol_low IS/OOS | +0.0809 / +0.1119 | **+0.0809 / +0.1119** | ✅ exact (유일 유지) |
| HYG rate_down_vol_low sign_match | 0.25 | **0.25** | ✅ exact |
| sign_prior eligible (7 cluster) | 12/13/15/15/13/12/17 | **12/13/15/15/13/12/17** | ✅ 전부 exact |

매직넘버 0건. yaml 수치 전부 raw json + 재계산 ±0% 매칭.

**합성 지문 검사 (§0-3)**: 실데이터 확정.
- 2020-03 코로나: HYG 일중 min ret = **-5.50%** (실재)
- 2022 금리쇼크: TLT 연간 **-29.38%** (실재)
- ret kurtosis = **42.99** (fat-tail, 합성 정규 아님)
- 주말 공백 정상 (weekday 0-4만), 휴일 갭 max 5일 (실재)
→ 합성 시드 흔적 0.

## §1. 12축 verdict

| 축 | verdict | 근거 (재실행 수치) |
|---|---|---|
| **A 이론** | PASS | ACM(Adrian-Crump-Moench) + Kim-Wright affine TS + Fed FEDS Notes 2017 model-diff. 저자·연도 명시. |
| **B 실데이터** ★ | **PASS** | 실 panel 2007-12-18~2026-05-29 n=4814 재현. KW fetch n=9084 실측. 합성 0. 차분 driver 전부 ADF I(0): MOVE_Z p=8.9e-08, ACM_d20 p=2.2e-22, KW_d20 p=5.6e-20, DGS10 p=1.2e-17, T10Y2Y p=3.9e-19, BAA10Y p=7.6e-17. |
| **C 추적성** ★ | **PASS** | yaml 전 수치 raw 재계산 ±0% (위 표). 매직넘버 없음. eligible 7/7 cluster 일치. |
| **D PIT/lookahead** ★ | **부분(hard 아님)** | ACM·KW 둘 다 FRED/NYFed **daily** publish (median gap=1일, monthly 아님). 둘 다 single-vintage revised series fetch = revision-PIT 잔존. yaml 의 "monthly publish lag forward-shift" 표현은 **부정확**(daily series임). 단 magnitude freeze + sign-prior only 라 lookahead 가 alpha 박제로 이어지지 않음 → hard 아님. (정정 권고 아래 §3) |
| **E 환각** | PASS | KW endpoint THREEFYTP10/5·THREEFFTP10 = FRED 실 series, fetch 200 OK 검증 (각 9084행). 무출처 0. |
| **F 반증** | PASS | walk-forward 3/4 regime cell OOS 부호반전 = regime IC 가설 **기각 record**. v1 "bonferroni-pass" 취소. p-hacking 차단. |
| **G effective-N** ★tier | PASS(tier) | regime cell n=999~1405, valid_splits=4. fwd60 overlap → effective N << nominal 인지. tier = structural_prior_low_confidence (validated alpha 위장 없음). |
| **H 미해결** | PASS | unresolved_v5: monthly(→daily 정정요) lag / TIPS DFII10·T5YIE 결락 / HY 등급 mismatch / J spread / L PSD 박제. |
| **I 생존편향** ★ | **PASS** | universe 7 ETF + 대체 8개(EDV/JNK/SHV/TLH/VGSH/STIP/VTIP) fetch 됨. bond ETF 상폐 희소(대형 iShares/Vanguard 생존), point-in-time inception 반영(BIL 2007~, STIP 2010~ 등 실제 상장일). caveat 박제됨. 생존편향으로 결과 무효화 신호 없음. |
| **J 경제유의** | PASS | sign-prior only, alpha 미주장 → 비용 차감 후 alpha 주장 X. hard 아님. |
| **K 다중검정** | PASS | v4 BH-FDR q=0.10 on eff~84 = 0/105 reject 유지. walk-forward = OOS 검증층(보정 대상 아님)으로 정직 분류. tries(consult 9·websearch 5) 공시됨. |
| **L 통합정합** ★ | N/A(통합 전) | credit(BAA10Y) ↔ eq_us_defensive 공통인자 / rate(DGS10) 전자산 공통 → PSD eigh-floor = phase7_entry.L_axis_integration_note 박제. 통합 phase 의무로 이연 정상. |

## §2. Hard-fail 코어 4 (B/C/D/I) 결과

- **B PASS** / **C PASS** / **D 부분(hard 아님)** / **I PASS** → **hard-fail 0건**.
- D는 monthly→daily 라벨 부정확이 유일 흠이나, magnitude freeze + sign-prior only 구조라 lookahead 가 결과를 무효화하지 않음. revision-PIT 는 OOS 부호 안정성만 쓰는 한 sign 에 영향 미미.

## §3. yaml 반영 필요 (보강 — 격하 아님, 정확성)

1. **D축 표현 정정 (P1)**: `kim_wright_vs_acm.audit_D_status` 와 `unresolved_v5` 의 "monthly publish lag forward-shift" → **부정확**. ACM·KW 둘 다 FRED/NYFed **daily** series (median gap 1일, 재계산 확인). 실제 PIT 잔여 = **revision lag**(과거 추정치 후일 재추정 갱신), not publish lag. 표현을 "ACM/KW single-vintage revised series → revision-PIT 잔존 (daily publish, monthly 아님). vintage(ALFRED real-time) 미적용 = P1" 로 정정 권고.
2. (정보성) tier 라벨 정직 — 전 7 cluster validated_alpha=false, structural_prior_low_confidence 일관. 위장 없음 확인.

## §4. 시스템 정합 (§4)

- v5 = sign/direction prior only, magnitude freeze. 현 골격(`RegimeGlasso corr_prior` = sign 부호만 주입)으로 **수용 가능**(다운그레이드 아님 — 애초에 magnitude 박제가 방의 정직 결론).
- walk-forward classifier = v4 system_fit 의 "walk-forward regime module 신설" 업그레이드 계획의 실증 산출. 통합 시 L축 PSD + credit/rate 공통인자 1회 계상만 잔여(phase7_entry 박제).

## §5. 종합 판정

**충실 (hard-fail 코어 4 = 0)**. v5 는 v4 PARTIAL 의 P0 격하 2건(C регime in-sample artifact / D ACM lookahead)을 실측으로 정직하게 해소했고, 핵심 claim 전부 독립 재현됨. validated alpha 위장 없음 — over-claim/환각 미발견. register(require_raw=True) 가능.

- 단일 보강(격하 아님): D축 "monthly publish lag" 표현 → "daily series, revision-PIT 잔존" 정정.
