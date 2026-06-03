---
tags: [handoff, inv, wire, factor-axis, consult, vif]
date: 2026-06-02
session: btn-Inv
---

# 핸드오프 — factor 축 확장 A~F 자문 수렴 + E·F 감사 완료 / A(VIF 측정) 착수 직전

> 진입: 이 파일 → `progress-wire-impl.md` **Phase X** 섹션 → MEMORY.md ckpt.
> python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` + `PYTHONUTF8=1`. FRED 키=.env FRED_API_KEY(있음, RealFredAdapter(api_key=) 명시 주입 필요 — 기본 생성자는 키 없이라 unavailable).
> ⛔ push 금지(로컬 commit만). SACRED(DRY_RUN·execute_trade) 비접촉. opt-in off=byte-identical.

## 0. 이번 세션 완료
- **commit 1de1ea5** refactor(wire): IC8 Λfx 0.09→0.15 정밀화. 자문 2모델 B(0.15~0.20) 만장일치 + 자체 falsification(F1 직교상한 0.242·F4 무조건부 realized KRW gold×equity corr +0.17~0.20 재현·F2 기각). golden us_stock×commodity 0.2642→0.2951·us_stock×gold 0.1994→0.249(fx_hedge=full→IC10 0.0832/0.2026 정확 복원 불변). 회귀 0·off byte-identical.
- **슬리브 추가 폐기 확정**(사용자 2026-06-02): reit/eq_intl/xle 신설 안 함. progress line 229·235 ⊘. → 이들 study(verdict·L축)는 배분 런타임 영향 없음(SLEEVE_AGG 미매핑), study 정합성만.
- **framing 오류 K 기록**(promotion-log 2026-06-02 gate-과분류): progress ⛔ 직역 회피, autopilot-run-scope 대조 의무.

## 1. ★게이트 경계 재정립 (사용자 confirm 2026-06-02)
- 자율 밖 = **실거래 신호 소비(go-live)뿐**. (가)audit 프로세스·측정·codify 는 **10년 백테스트(Phase V) 방향논의 직전까지 자율 가능**.
- progress ⛔ = 자동 "자율 불가" 금지. judge 실 사이징·IC4 owner 사이클 소비·실거래 flip 만 자율 밖.

## 2. ★factor 축 확장 A~F (외부조사 2 subagent + 자문 2모델 수렴, 2026-06-02)
> 배경: 논문(CRR 1986·Costa-Kwon 2020·FGL·Kritzman·Forbes-Rigobon) + GitHub 2조사 → **우리 축=표준 강화판 확인**(factor-implied Σ=BΛBᵀ + RegimeGlasso belief-mix=Costa-Kwon 동형, nonparanormal+EBIC+EB로 더 정교). SEED β 학술 뒷받침(gold-dollar -0.317=mv attenuation 정상). 우리 특화=fx denomination(OSS 미발견).
> 외부 자문 로그: `~/.claude/.gemini-web-last.md`·`.claude-web-basic-last.md`(2026-06-02 A~F). 브리핑=`.consult-axis-AF-briefing.md`.

**자문 수렴 우선순위 = E→A→B / C·D·F 강등** (양모델 A+E 최우선, claude은 E를 A앞에=feed-forward):
- **E (✅감사완료 — 조치 불필요)**: stress floor `ρ←max(ρ_EWMA,ρ_stress)` 의 stress_corr = **런타임 미주입**(fetch_factor_cov·gate-Λ 둘 다 없이 호출, self-test factor_cov_estimate.py:200·206 전용) → **dead path**. Forbes-Rigobon over-correction 현 미발현. RegimeGlasso 고vol bias 는 nonparanormal rank-transform 이 일부 완화. → 향후 stress floor 활성화(gate-Λ wire) 시 ρ_stress=FR-adjusted 적용 권고(미래 가드).
- **F (✅grep완료 — 강등 확정)**: `_ic_corr_prior`(factor-implied BΛBᵀ→cov2corr)→`cp`→`RegimeGlasso(corr_prior=cp).fit()`(regime_to_weights.py:307)→`eb_shrink=lam·corr_prior+(1−lam)·corr_glasso`(conditional_correlation.py:213). factor Σ→RegimeGlasso input 흘러감 → idio sparse(FGL) 추가 시 동일 co-move 복원=이중계상. 현 diagonal freeze=good design.
- **A (★다음 착수 — 실질 유일 남음)**: term spread(T10Y2Y slope) + inflation breakeven(T5YIE)를 FACTORS 축 추가. CRR 정전, gold/commodity inflation driver. ★현황: breakeven_5y·T10Y2Y는 regime_classifier evidence로 이미 사용, **factor 공분산 축엔 없음**(rate=DGS10 level만).
  - ★이중사용 아님(regime=coarse conditioning / factor=fine structure 별 레이어).
  - ★진짜 risk=within-regime variance truncation(breakeven이 regime 정의 inflation_z + factor 동시→절단). 해소=regime엔 level(inflation_z)/factor엔 change(breakeven Δ·잔차).
  - ★직교화 필수: nominal 10Y=real+breakeven 공유→collinear. real-rate(DFII10)+breakeven+slope 3축이 더 깨끗(claude) or Gram-Schmidt/PCA. kill=VIF≥5 or 기존 1.14 급등.
- **B (중기 retarget)**: liquidity. TED=LIBOR폐지 dead → USD/KRW cross-currency basis(KRW funding 1차) or SOFR-OIS. kill=stress sub-sample partial corr(VIX·HY OAS 통제) 비유의→강등.
- **C (보류 형태제한)**: regime 다축화. partition 금지(8 regime→cell 붕괴). turbulence=continuous-modulator만(JumpModel confidence layer 흡수). kill=cell effective n<15→연속형.
- **D (연구 sandbox만)**: copula/tail-dep. production 강등(n<30 joint-tail≈0 + magnitude FREEZE 충돌). sandbox=Gaussian 오차 magnitude 측정→E floor 근거.

## 3. ★A 재개 포인트 (다음 세션 즉시)
1. **VIF 측정 먼저**(자문 kill condition): `.tmp-A-vif.py` **이미 작성됨, 실행만**. → 조합 (a) rate(DGS10)+slope+breakeven / (b) real(DFII10)+breakeven+slope 3분리 의 VIF 비교 + 현행 6 baseline. VIF<5 통과 조합 채택.
   - 실행: `PYTHONUTF8=1 {python} .tmp-A-vif.py`. fred=Fred(api_key=.env키) 직접.
2. VIF 통과 → **SEED β 측정**: 각 sleeve(gold/cyclical/intl/reit/commodity)의 신규 factor(slope·breakeven) batch multivariate std β(HAC-NW, n≈5052). 기존 batch-std-beta 스크립트 패턴 재사용(`_factor_shadow`).
3. **FACTORS 6→8 확장**: `factor_betas_seed.FACTORS` + SEED_CELLS 신규 factor 셀 + `factor_returns.FACTOR_SERIES`(T10Y2Y/T5YIE 또는 DFII10) + `factor_cov_estimate.FACTOR_TRANSFORM`(diff).
4. regime level/factor change 분리(variance truncation 방지) + opt-in off byte-identical + golden 재측정 + 회귀.
5. small-n rigor(p/CI/Bonferroni) + decision-quality 본인 시뮬.

## 4. 잔여 (A 외)
- B/C/D = 보류·연구(위 §2). GitHub 부분 차용(vinecopulib MIT copula=D / SystemicRisk liquidity=B)은 B/D 실제 착수 시점에 repo 코드 탐색(지금 가치 낮음).
- Phase V 10년 백테스트 = 사용자 방향논의 게이트.
- IC8 실 FRED Λ 경로 활성화(first-release vintage 부재+키 미주입→항상 eye fallback) = 별도 과제.

## 5. 열어본 핵심 파일
- `core/study/factor_betas_seed.py` FACTORS:43·SEED_CELLS·build_seed_betas / `core/data/factor_returns.py` FACTOR_SERIES:22 / `core/study/factor_cov_estimate.py` FACTOR_TRANSFORM:25·estimate_factor_cov(stress_corr:133 dead) / `core/brain/regime_to_weights.py` _ic_corr_prior:228·_static_factor_lambda:183(Λfx=0.15)·_belief_conditional_cov:278 / `core/structure/conditional_correlation.py` eb_shrink:207·RegimeGlasso / `core/brain/regime_classifier.py` breakeven_5y:215·yield_10y_2y:255.
- memory 조사: `~/.claude/memory/research/regime-cross-correlation.md`·`factor-correlation-axis-papers.md`·`regime-corr-axes-round2.md`.
