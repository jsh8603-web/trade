# gold §2-3 실데이터 검증 진행 인계 (2026-05-30, btn-jsh86)

> ckpt: ctx 437k/500k(long-mode ON) warn 진입, H1·H2·H4·H6·H7·H3·M3 완료 후 종결.
> 다음 세션 = H5 / H8 / yaml v2 / §2.5 8축 audit + **main 의 CFTC + 실질금리 디커플링 모니터 2지표 추가 의무** 반영.

---

## 1. 완료 (이번 세션)

### 1-1. 5/8 H 가설 + H3 + M3 검증 완료
| H | verdict | 핵심 발견 | raw |
|---|---|---|---|
| **H1** 변화율 베타 안정 | **SUPPORTED** | 252d Pearson 부호반전 0/4028, rolling β sign-flip 1.86%, QLR sup-F=15.26 (cv5%=16.45 임박) | `validation-H1-beta-stability.md` + `h1_result.json` + `h1_rolling_beta.csv` |
| **H2** level intercept shift | **★STRONGLY SUPPORTED (broader)** | unexplained ln_gold 2022 +39% → 2026 +391% 단조 증폭, Johansen rank=0 + EG ADF p=0.41 → 균형식 *자체* 재구성, rolling 252d R² 70%→52%→44% (RBC 정합) | `validation-H2-level-intercept.md` + `h2_result.json` + `h2_rolling_r2.csv` |
| **H4** sys_priors β reconciliation | **★압도적 기각** | 일별 std β rate=-0.274 (<0.40), dollar=-0.289 (<0.55), VIF=1.02 (공선성 부재), dollar USD→SDR 감쇠 +66.8% (자문 30~50% 상회) | `validation-H4-sys-priors-reconciliation.md` + `h4_result.json` |
| **H6** breakeven common-cause | SUPPORTED | gold-BE partial=-0.054 (<0.20), gold-real=-0.291, basis B (nominal+real+BE) VIF 1.04→12996 (항등식 게이트 1만배 발산) | `validation-H6-breakeven-common-cause.md` + `h6_result.json` |
| **H3** cb_demand level 운반 | **PARTIAL** (n=15 power 한계) | WGC 누적 CB 매수 ↔ unexplained ln_gold annual Pearson +0.784, 2022 동시 점프 (CB +1136톤 ↔ unexpl +0.33) | `validation-H3-cb-demand-trend.md` + `h3_result.json` + `wgc_cb_annual.csv` |
| **H7** γ 분해 + GPR quantile | SUPPORTED | rolling 504d EG ADF pre-2022 -3.11 → post-2022 -2.26 (γ 점진 붕괴, H2 정합), GPR OLS t=2.19 유의, q90/OLS=5.91× (gap 10.76σ) | `validation-H7-gamma-gpr.md` + `h7_result.json` + `h7_rolling_eg.csv` |

### 1-2. M3 거시연관 분석 (main 의 timeline.md §4 가이드)
- **`macro-linkage-M3.md` + `m3_result.json`**
- ★ E4 (2023Q4-2024Q4) rate loading -0.142 = 다른 epoch (-0.30~-0.36)의 절반 + dollar loading 유지 = ★ rate channel 의 수준 재구성 epoch-한정 발현. H2 의 mechanism 의 직접 단서.
- cross-asset Pearson: gold↔broad TWI=-0.378 > DXY=-0.348 > Δus10y=-0.281; oil=+0.103
- epoch ann return: E1 -12.94% / E2 +18.35% / E3 -15.12% / E4 +26.60% (Sharpe -0.90/+1.21/-1.72/+1.82)
- main 회신 송신 완료.

### 1-3. 데이터 fetch 완료
- FRED: DFII10 + T10YIE + DTWEXBGS + DGS10 + DCOILWTICO + DEXUSEU + DEXJPUS + DEXCHUS + DEXUSUK + BAA10Y + VIXCLS + (BAMLH0A0HYM2 = 3년치만, alternative endpoint 미해결)
- Yahoo: GLD ETF v8 + DX-Y.NYB DXY v8
- GPR: matteoiacoviello.com gpr_daily.xls (1985~2026-05-26, 15121 obs)
- WGC: annual CB net purchase 2010-2024 (코드 박제 `analyze-h3.py` 내)
- data-inventory: `raw/data-inventory.md`

### 1-4. 이론 학습 (2-2)
- `raw/theory-notes.md` (Barsky-Summers 1988 + WGC GRAM + Erb-Harvey + Reboredo + Pukthuanthong-Roll + Arslanalp + Caldara-Iacoviello + Baur-Lucey)
- archive raw: `~/.claude/docs/archive/research-raw/gold-theory-foundations-native-20260530.txt`
- memory ref: `~/.claude/memory/research/gold-theory-foundations.md` (+ MEMORY.md index)

### 1-5. 방향성 (2-1)
- `direction.md` (R1+R2 자문 다회 수렴, 8 Q + Q2 {real_rate, BE} basis + Q8 force_include 4 + R3 조건부 트리거)
- `raw/round-1-{gemini,claude}.md` + `raw/round-2-{gemini,claude}.md` + 각 prompt

### 1-6. ERROR + rule 자산화 (본 세션 종결 직전)
- `promotion-log.md` head: `### 2026-05-30 · consult-raw-to-output-mapping-gap` ERROR prepend
- `~/.claude/rules/consult-raw-output-mapping-checklist.md` 신규 rule (자문 raw → 산출 매핑 의무 체크리스트)
- 근인: gold v2 산출 시 Claude R1 변수정의표의 CFTC speculative + 실질금리 디커플링 모니터 누락 → main 재지시 정정.

---

## 2. 미완 (다음 세션 의무)

### 2-1. ★main 의 추가 지시 (자문 R2 도출 누락 정정)
> "M3 4 open(H5/H8/yaml v2/8축) 진행 시 이 2지표 lens/validation 반영. ⛔ 점추정 prior 박제 금지, n<30 5게이트."

**의무 2지표**:
1. **CFTC managed-money net position** (gold futures 투기 포지션) — 과열/디레버 신호
   - 출처: CFTC COT report weekly (cftc.gov public, 또는 FRED `MMFNETSTKL` 류 시리즈 ID 확인 필요)
   - lens 역할: speculative crowding 신호, R2 의 Claude R1 변수정의 부수에 명시됨
2. **실질금리(DFII10) 디커플링 모니터**
   - 정의: 금-실질금리 음의상관 깨지는 국면 = CB demand / GPR 우위 신호
   - 본 세션 H1+H2 검증으로 이미 핵심 실증: 변화율 β 안정 (H1 SUPPORTED) + level 균형식 붕괴 (H2 STRONGLY SUPPORTED) → ★실질금리 디커플링 = 변화율 단위가 아니라 *수준* 단위에서 발현 = H2 의 *결과* 가 곧 디커플링 모니터의 직접 신호
   - 신규 fetch 불요, 본 세션 산출 (H2 unexplained ln_gold trend, H7 rolling EG ADF) 가 모니터의 baseline

### 2-2. 가설 검증 잔여
- **H5 safe-haven 국면 의존**: 2-state Markov-switching credit_HY_OAS↔gold (HY OAS 3년치 한계, BAA10Y 대체 가능). statsmodels MarkovRegression.
- **H8 이중 e-process ordering**: Δ-beta e-process vs level 잔차 e-process. 본격 anytime-valid 구현.

### 2-3. study_session.yaml v2 재작성
- v1 (179줄) **폐기**.
- 7 블록 재작성 — H1~H8 + H3 + M3 + 2 신규 지표 반영.
- force_include 4 = {real_rate_10y, dollar_index(broad TWI 우선), cb_demand_proxy, gpr_daily} — main 옵션 (a) 채택 (BE 항등식 basis 외부 가드).
- ★ **2 신규 indicator 추가**: cftc_mm_net_long (family=positioning, new), real_rate_decoupling_monitor (family=macro_driver, computed from H2 unexplained level)
- ★ 점추정 prior 박제 금지: prior_strength 는 wide CI 또는 freeze, 점추정 값 인용 시 95% CI 동반.
- ★ n<30 5게이트: 각 정량 임계 + 데이터 n 명시.

### 2-4. §2.5 감사 8축 self-audit
- A 이론실재성 / B 실데이터검증 (★합성 0, n·기간·p·Rank-IC 명시) / C yaml 도출추적성 / D PIT·OOS / E 자문비판+환각cross-verify / F 반증가능+기각기록 / G 검정력한계 / H 미해결의문.
- raw/audit-2.5-checklist.md 박제.

### 2-5. main 최종 보고
- btn-Codlearn 으로 8 가설 + yaml v2 + audit 종결 보고.

---

## 3. 핵심 결정·기각 대안 박제

### 3-1. R2 자문 수렴 (지키기)
- **basis = {real_rate, breakeven}**, nominal 제외 (Claude 안 Conf 5, Gemini {nominal, BE} Conf 4 기각). 본 세션 H6 검증으로 VIF 1.04 vs 12996 압도 확인.
- **gold/SDR numeraire 1차 채택** (Q4): IMF 2022 weights 합성 (43.38% USD + 29.31% EUR + 12.28% CNY + 7.59% JPY + 7.44% GBP). H4 에서 dollar β USD→SDR 감쇠 +66.8% 실증.
- VECM(offline) + Bayesian State-Space(online) sequential hybrid (Q1). 단 본 세션 Johansen rank=0 + EG 부정 → VECM γ 직접 적용 불가, rolling EG ADF stat 으로 γ proxy 사용 (H7).
- 이중 e-process + ordering falsification (Q6) — H8 미구현, 다음 세션.
- 차원 스케일링 전처리 파이프라인 (Q7) — yaml 블록7 code_change_plan 에 명시.

### 3-2. force_include 5 vs 4 (main 옵션 (a) 채택)
- direction.md ⑥ 권고: BE 를 force_include 미포함, 항등식 basis 외부 가드 (VIF<5) 로 pin. force_include = {real_rate, ln_dollar, cb_demand, GPR} = 4 유지.
- 본 세션 H6 + H7 로 정합 확인.

### 3-3. ★ sys_priors gold loading 재보정 (main G6 게이트 사안)
- H4 결과: `[-0.5 rate, -0.8 dollar, 0 oil, -0.2 credit]` 압도적 기각.
- 실측 일별 std β: rate ≈ -0.27, dollar (gold_SDR) ≈ -0.10, dollar (gold_USD) ≈ -0.29
- production wiring 시 main G6 게이트로 처리 — 본 작업방 범위 밖, yaml lens estimation_note 에 명시.

### 3-4. ★ Dalio narrative (Claude R2 보수 판정 수용)
- Bridgewater/Dalio Paradigm Shifts / Changing World Order = ★narrative 색채만, 학술 anchor 절대 아님.
- H2 학술 anchor: Barsky-Summers 1988 + Erb-Harvey 2013 + Arslanalp 2023 + WGC GDT + Caldara-Iacoviello 2022.

---

## 4. 열어본 파일 (다음 세션 참조)
- direction.md, summary.md, theory-notes.md, data-inventory.md
- analyze-h1.py / analyze-h2.py / analyze-h4.py / analyze-h6.py / analyze-h3.py / analyze-h7.py / analyze-m3-macro-linkage.py
- validation-H{1,2,3,4,6,7}-*.md + macro-linkage-M3.md
- h{1,2,3,4,6,7}_result.json + m3_result.json
- round-{1,2}-{gemini,claude}.md + 각 prompt
- WGC annual CB net purchase 박제 (analyze-h3.py 내 dict + wgc_cb_annual.csv)
- gpr_daily.xls (Caldara-Iacoviello, 15121 obs)

---

## 5. 다음 세션 재개 포인트
1. (필수) Read 본 handoff md → progress 인지
2. (필수) `~/.claude/rules/consult-raw-output-mapping-checklist.md` 적용 — 자문 raw → 산출 매핑 누락 0 확인
3. CFTC managed-money net position 데이터 fetch (CFTC public CSV 또는 FRED 시리즈 ID 확인)
4. H5 검증 (Markov regime-switching, BAA10Y/VIX) → validation-H5*.md
5. H8 검증 (이중 e-process) → validation-H8*.md
6. study_session.yaml v2 재작성 — v1 폐기, 7 블록 H1~H8 + CFTC + 디커플링 모니터 반영, ⛔ 점추정 prior 금지
7. raw/audit-2.5-checklist.md 박제 (8축 A~H)
8. main 최종 보고 (btn-Codlearn)

