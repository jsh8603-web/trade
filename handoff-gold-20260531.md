---
tags: [type/handoff, domain/inv, study/gold, session/btn-jsh86]
date: 2026-05-31
study_id: gold
session: btn-jsh86
deliver_to: main (btn-Codlearn) → 통합 재개
note: 전 study 세션(2026-05-30~31, btn-jsh86) gold §2-1 + §2-2 + §2-3 5/8 + M3 + candidate-ledger + collector-request 진행 후 main 의 통합 재개 요청에 따른 완전 핸드오프. 본 파일이 진단·잔업·재개포인터·미해결 전부 박제.
previous_handoff: D:/projects/Inv/study-research/gold/raw/handoff-gold-2-3-20260530.md (어제 §2-3 중간 인계)
---

# gold study 통합 핸드오프 (2026-05-31, btn-jsh86 → main 통합 재개)

> main 지시 = 진행 중단 + 본 파일에 완전 기록 + 미커밋 commit + 'HANDOFF DONE ...' 1줄 보고. ⛔ /clear 치지 말 것 (main 이 보냄).

---

## 0. 한눈에 (요약)

- **§2-1 완료** (자문 다회 수렴 R1+R2, direction.md)
- **§2-2 완료** (theory-notes.md, archive raw + memory ref + MEMORY.md 인덱스)
- **§2-3 5/8 완료** (H1·H2·H4·H6·H3·H7 + M3 거시연관)
- **§2-3 잔여 3/8 미완** (H5 Markov regime-switching · H8 이중 e-process · yaml v2 재작성 · §2.5 8축 audit · 최종 보고)
- **★main 추가 지시 2건 진행 중**: (a) CFTC + 실질금리 디커플링 monitor 반영 (CFTC zip 3건 fetch 완료) (b) candidate-ledger 우선순위 reverse → merit 후보 → collector-request-to-main.md (작성 완료, main collector 작업큐 대기)
- **★ERROR 자산화 1건**: consult-raw-to-output-mapping-gap → ~/.claude/rules/consult-raw-output-mapping-checklist.md 신규
- **장기 ckpt 8건** (raw/progress.md Working Notes 누적)

---

## 1. 완료 산출물 (지식 보존)

### 1-1. §2-1 방향성 (R1+R2 자문 수렴)
- `D:/projects/Inv/study-research/gold/direction.md` — Q1~Q8 정량 임계 + force_include 4 옵션 (a) + Bridgewater/Dalio narrative 색채만
- `raw/round-1-{gemini,claude}.md` + `raw/round-1-{gemini,claude}-prompt.md`
- `raw/round-2-{gemini,claude}.md` + `raw/round-2-prompt.md`
- ★main 옵션 (a) 채택: BE force_include 미포함, 항등식 basis 외부 가드

### 1-2. §2-2 이론 학습
- `raw/theory-notes.md` — Barsky-Summers + WGC GRAM + Erb-Harvey + Reboredo + Pukthuanthong-Roll + Arslanalp + Caldara-Iacoviello + Baur-Lucey
- `~/.claude/docs/archive/research-raw/gold-theory-foundations-native-20260530.txt`
- `~/.claude/memory/research/gold-theory-foundations.md` + `~/.claude/memory/MEMORY.md` 인덱스 1줄 추가

### 1-3. §2-3 실데이터 검증 5/8

| H | verdict | 핵심 발견 | raw |
|---|---|---|---|
| **H1** 변화율 베타 안정 | **SUPPORTED** | 252d Pearson 부호반전 0/4028, rolling β sign-flip 1.86%, QLR sup-F=15.26 (cv5%=16.45 임박) | `raw/validation-H1*.md` + `h1_*.json` + `h1_rolling_beta.csv` |
| **H2** level intercept shift | **★STRONGLY SUPPORTED (broader)** | ★unexplained ln_gold 2022 +39% → 2026 +391% 단조 증폭, Johansen rank=0 + EG ADF p=0.41 = 균형식 *자체* 재구성, rolling 252d R² 70%→52%→44% RBC 정합 | `raw/validation-H2*.md` + `h2_*.json` + `h2_rolling_r2.csv` |
| **H4** sys_priors β reconciliation | **★압도적 기각** | 일별 std β rate=-0.274 (<0.40), dollar=-0.289 (<0.55), VIF=1.02 (공선성 부재), dollar USD→SDR 감쇠 +66.8% (자문 30~50% 상회) | `raw/validation-H4*.md` + `h4_*.json` |
| **H6** breakeven common-cause | SUPPORTED | gold-BE partial=-0.054 (<0.20), gold-real=-0.291, basis B (nominal+real+BE) VIF 1.04→12996 (항등식 게이트 1만배 발산) | `raw/validation-H6*.md` + `h6_*.json` |
| **H3** cb_demand level 운반 | PARTIAL (annual n=15 power 한계) | WGC 누적 CB ↔ unexplained ln_gold annual Pearson +0.784, 2022 동시 점프 (CB +1136톤 ↔ unexpl +0.33) | `raw/validation-H3*.md` + `h3_*.json` + `wgc_cb_annual.csv` |
| **H7** γ 분해 + GPR quantile | SUPPORTED | rolling 504d EG ADF pre-2022 -3.11 → post-2022 -2.26 (γ 점진 붕괴), GPR OLS t=2.19, q90/OLS=5.91× (gap 10.76σ tail amplified) | `raw/validation-H7*.md` + `h7_*.json` + `h7_rolling_eg.csv` |

### 1-4. M3 거시연관 (timeline.md §4 가이드)
- `raw/macro-linkage-M3.md` + `m3_result.json`
- ★E4 (2023Q4-2024Q4) rate loading -0.142 = 다른 epoch 절반 + dollar 유지 = H2 mechanism *rate 채널 한정*
- cross-asset Pearson: gold↔broad TWI=-0.378 (1차) > DXY=-0.348 > Δus10y=-0.281; oil=+0.103
- epoch ann return: E1 -12.94% / E2 +18.35% / E3 -15.12% / E4 +26.60% (Sharpe -0.90/+1.21/-1.72/+1.82)

### 1-5. 후보 박제
- `D:/projects/Inv/study-research/gold/candidate-ledger.md` (49 후보 6 분류 enum: [채택-force/indicator/basis-pin/monitor] + [이연-collector] + [미채택-tautology/OOS/skip-explicit])
- `D:/projects/Inv/study-research/gold/collector-request-to-main.md` (★merit 후보 6건 + sys_priors G6 — main collector 작업큐)

### 1-6. 데이터 fetch (raw/)
- FRED: fred_dfii10·t10yie·dtwexbgs·dgs10·wti·dexuseu·dexjpus·dexchus·dexusuk·baa10y·vixcls (11 시리즈)
- FRED 결손: BAMLH0A0HYM2 (HY OAS) 3년치만 (cosd 무시 미해결, ALFRED API 필요)
- Yahoo v8: try_yahoo_v8.json (GLD) + try_dxy.json (DX-Y.NYB DXY)
- GPR: gpr_daily.xls (Caldara-Iacoviello 1985-2026-05-26, 15121 obs)
- CFTC: cftc_{2022,2023,2024}.zip (★fetch 완료, gold 088691 managed-money 추출 대기)
- WGC: annual CB net purchase (analyze-h3.py 박제 + wgc_cb_annual.csv)

### 1-7. ERROR 자산화
- `~/.claude/memory/promotion-log.md` head: `### 2026-05-30 · consult-raw-to-output-mapping-gap` ERROR prepend
- `~/.claude/rules/consult-raw-output-mapping-checklist.md` 신규 rule
- 근인: gold v2 산출 시 Claude R1 변수정의표의 CFTC + 실질금리 디커플링 모니터 누락 → main 재지시 정정

---

## 2. 미완 잔업 (재개 시 의무)

### 2-1. ★main 의 candidate-ledger 우선순위 정정 ($진행 중$)
> main 의 ★순서정정: "candidate-ledger 먼저 쓰지 마라. merit 후보를 실제 추가하는 study 다시 하라. collector 없으면 main이 구현 → main 에 먼저 보고. collector없음·후순위·이연은 탈락 사유 부적격."

- ★Action 1: collector-request-to-main.md 박제 완료, main 보고 송신 완료 (HANDOFF DONE 라벨 직전)
- ★Action 2: main 의 collector 작업 완료 후 본 작업방이 (이론→실측→상관/Rank-IC) → 12축 audit (별도 subagent) → yaml 반영. 본 단계 main 응답·gating 대기.

### 2-2. §2-3 잔여 3 가설 + yaml + audit
- **H5 safe-haven 국면 의존**: BAA10Y/VIX 사용 2-state Markov-switching (statsmodels MarkovRegression). HY OAS full history 대기 시 → SUPPORTED. 임시 BAA10Y 로 부분 검증 가능.
- **H8 이중 e-process ordering**: Δ-beta e-process (귀무 pre-2022 calibration) vs level 잔차 e-process (귀무 균형식 안정). e>20 (α=0.05). 자체 구현 (e-CUSUM).
- **study_session.yaml v2 재작성**: v1 (179줄) 폐기, 7 블록 H1~H8 + CFTC + 실질금리 디커플링 모니터 + ⛔ 점추정 prior 금지 (wide CI or freeze) + n<30 5게이트
- **§2.5 8축 self-audit**: A 이론실재성 / B 실데이터검증 / C 추적성 / D PIT·OOS / E 자문비판+환각 / F 반증가능 / G 검정력한계 / H 미해결의문. raw/audit-2.5-checklist.md

### 2-3. main collector 작업큐 대기 후 후속 study (1-5 의 collector-request 6건)
1. HY OAS full history (FRED ALFRED API key)
2. OECD CLI economic expansion
3. WGC quarterly CB (n=60 + Kalman)
4. MOVE Index bond vol
5. SPDR GLD daily flow
6. SGE Shanghai gold premium

### 2-4. ★main G6 게이트 사안
- sys_priors gold loading 재보정 (collector 아닌 code). H4 실측 기반 [-0.27, -0.10 (SDR) ~ -0.29 (USD)]. production wiring 시.

---

## 3. 재개 포인트 (재개 시 first action)

1. **(필수)** Read `D:/projects/Inv/handoff-gold-20260531.md` (본 파일) + `D:/projects/Inv/study-research/gold/raw/handoff-gold-2-3-20260530.md` (전 단계)
2. **(필수)** Read `D:/projects/Inv/study-research/gold/raw/progress.md` Working Notes (8 ckpt)
3. **(필수)** Read `D:/projects/Inv/study-research/gold/collector-request-to-main.md` — main collector 작업큐
4. **(필수)** Read `~/.claude/rules/consult-raw-output-mapping-checklist.md` — 자문 raw → 산출 매핑 의무 체크리스트
5. main 의 collector 완료 또는 자율 진행 가부 응답 확인 → 분기:
   - main collector 완료 → 1-5 의 6 후보 study (이론→실측→상관/Rank-IC) + 12축 audit (별도 subagent) → yaml 반영
   - 자율 진행 OK → H5 (BAA10Y/VIX) + H8 (이중 e-process) + yaml v2 + §2.5 8축 audit
6. CFTC zip 추출 (`unzip cftc_2024.zip` → gold 088691 managed-money net long 추출 → cftc_mm_gold.csv)

---

## 4. 열어본 파일 (재개 빠른 참조)

### 본 작업방 raw (D:/projects/Inv/study-research/gold/raw/)
- direction.md, summary.md, candidate-ledger.md, collector-request-to-main.md
- raw/{theory-notes, data-inventory, progress, handoff-gold-2-3-20260530, macro-linkage-M3}.md
- raw/analyze-{h1,h2,h4,h6,h3,h7,m3-macro-linkage}.py
- raw/validation-H{1,2,3,4,6,7}-*.md
- raw/{h1,h2,h3,h4,h6,h7,m3}_result.json + h1_rolling_beta.csv + h2_rolling_r2.csv + h7_rolling_eg.csv
- raw/round-{1,2}-{gemini,claude}.md + 각 prompt
- raw/{fred_*.csv, try_yahoo_v8.json, try_dxy.json, gpr_daily.xls, gpr_export.xls, cftc_{2022,2023,2024}.zip, wgc_cb_annual.csv}

### 글로벌 (~/.claude/)
- ~/.claude/memory/research/gold-theory-foundations.md (+ MEMORY.md 인덱스)
- ~/.claude/docs/archive/research-raw/gold-theory-foundations-native-20260530.txt
- ~/.claude/memory/promotion-log.md head ERROR (consult-raw-to-output-mapping-gap)
- ~/.claude/rules/consult-raw-output-mapping-checklist.md (신규 rule)

### main 의 reference (D:/projects/Inv/study-research/)
- macro/timeline.md §4 M3 가이드 (epoch E1~E4 + driver loading 방법론)
- STUDY-KIT.md §2 v2 (2-1·2-2·2-3) + §6 주식 통일 하드룰 (gold 면제, equity.* 아님)
- 예시 = commodity/candidate-ledger.md

---

## 5. 핵심 결정·기각 대안 박제

### 5-1. R2 자문 수렴 결정 (지키기)
- Q1: VECM(offline) + Bayesian State-Space(online) sequential hybrid — 본 study Johansen rank=0 으로 정식 VECM 적용 불가, rolling EG ADF proxy 사용 (H7)
- Q2: basis = **{real_rate, breakeven}**, nominal 제외 (Claude 안 Conf 5, Gemini {nominal, BE} 안 기각). H6 실측 VIF 1.04 vs 12996 압도 확인
- Q4: gold/SDR numeraire 1차 채택 (IMF 2022 weights 합성: 43.38% USD + 29.31% EUR + 12.28% CNY + 7.59% JPY + 7.44% GBP). H4 dollar β USD→SDR 감쇠 +66.8% 실증
- Q6: 이중 e-process + ordering falsification (H8 미구현, 다음 turn)
- Q7: 차원 스케일링 전처리 파이프라인 (yaml 블록7 박제)
- Q8: force_include 4 = {real_rate, ln_dollar, cb_demand, GPR} (옵션 a, main 판정). BE basis pin

### 5-2. ★main 추가 지시 2건 (자문 R2 도출, main 전달 누락 정정)
- CFTC managed-money net position → cftc_mm_net_long_gold indicator, lens·블록5 confidence_hook
- 실질금리 디커플링 모니터 → real_rate_decoupling_monitor computed (H2 unexplained ln_gold + H7 rolling EG ADF + 252d Pearson real-gold 셋 conjunction)

### 5-3. ★main 의 ★순서정정 (candidate-ledger reverse)
- candidate-ledger 는 (2순위·마지막) — merit study 완료 후 그래도 빠지는 항목만 박제
- (1순위) merit 후보 → 실제 추가 study (collector 의존성 있으면 main 에 collector 먼저 요청)
- collector없음·후순위·이연은 탈락 사유 부적격

### 5-4. Dalio narrative 처리 (Claude R2 보수 판정 수용)
- Bridgewater/Dalio Paradigm Shifts / Changing World Order = ★narrative 색채만, 학술 anchor 절대 아님
- H2 학술 anchor = Barsky-Summers 1988 + Erb-Harvey 2013 + Arslanalp 2023 + WGC GDT + Caldara-Iacoviello 2022

---

## 6. 외부 자문 결과 핵심 (Round 1 + 2)

- Gemini Pro Web (R1 + R2) + Claude Web Opus 4.8 High (R1 + R2) 병렬 자문
- R3 design advisory 불필요 (양 모델 자체 선언), R3 = 조건부 결과 조정 트리거 재정의 (3 발동 조건)
- raw 보존: round-{1,2}-{gemini,claude}.md + prompt 4 파일

R2 합의 8 Q 정량 임계는 §5-1 참조.

---

## 7. ckpt 누적 (raw/progress.md Working Notes)

1. ckpt-202605310145: collector-request-to-main.md + main 보고 → main 의 collector 작업큐 대기
2. ckpt-202605310130: candidate-ledger.md 작성 직후 main 정정 수신 (잘림)
3. ckpt-202605310110: CFTC zip 3건 fetch 완료
4. ckpt-202605301900: 5/8 가설 + ERROR 자산화 + 종결

---

## 8. ★ commit 산출물 (본 핸드오프 직후)

- D:/projects/Inv/study-research/gold/ 의 신규 file 들 (49 file)
- D:/projects/Inv/handoff-gold-20260531.md (본 파일)
- ~/.claude/ 의 ERROR + rule + memory 는 별도 (글로벌 영역)

---

## 9. 미해결 의문 (재개 시 우선 확인)
- ★main 의 collector 작업 완료 시점 (1-5 의 6 후보 fetch + sys_priors G6 게이트)
- ★H5 BAA10Y 임시 vs HY OAS 대기 — 자율 진행 가부 판정
- ★12축 audit 별도 subagent 위임 방식 (본 작업방 self-audit 아닌 별 subagent 명시)
- ★WGC 2024 annual 1044.6 톤 final vs provisional (◇ 본문 인용 시 재확인)
- ★Arslanalp 2023 J Int Econ 권호 (◇)
