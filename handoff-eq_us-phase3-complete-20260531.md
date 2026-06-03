---
tags: [type/handoff, domain/inv, study/eq_us, phase/3-complete, session/btn-jpdf, next-action/direction-md]
date: 2026-05-31
study_id: eq_us
session: btn-jpdf (eq_us 전담 슬롯)
main_session: btn-Codlearn
producer: btn-jpdf (Phase 3 R1+R2 자문 수렴 후, 클로드 서버 상태 악화로 작업 중단)
consumer: 다음 세션 (btn-jpdf 재진입 or 다른 슬롯)
status: Phase 3 (자문) 수렴 완료, Phase 3.5 (direction.md) + Phase 4-7 미진행
trigger_to_resume: "사용자가 본 handoff 경로를 다음 세션에 주입 시 §1 첫 행동부터 자동 진행"
---

# handoff — eq_us Phase 3 자문 수렴 후 (2026-05-31 mid-session 중단)

> **사용자 명시**: "자문만 마치고, 자문 내용 포함해서 너가 하려했던 모든 내용들을 전달해. 나중에 다시 그대로 시작할 수 있게. 지금 클로드 서버 상태가 안좋다."
> **본 handoff 의 자기완결성**: 다음 세션이 본 파일 + 5 raw 파일 + progress.md 만으로 그대로 이어갈 수 있게 박제.

---

## §1. 다음 세션 첫 행동 (post-resume)

1. 본 handoff Read (전체)
2. `D:/projects/Inv/study-research/eq_us/progress.md` Read (Phase 추적 + 사용자 박제 2건)
3. `D:/projects/Inv/study-research/eq_us/raw/consult-round-{1,2}-{gemini,claude}.md` 4 raw Read (자문 본문)
4. **Phase 3.5 진입 — `direction.md` 작성** (§6 초안 그대로 Write — 본 handoff 안 박제됨)
5. main(btn-Codlearn) 보고 (§9 양식) + **승인 대기** (이 멈춤은 idle 아님)
6. 승인 후 Phase 4 (frame.md eq_us 버전 + plan.md) → Phase 5 (산업 subagent dispatch) → Phase 6 (별 평가 subagent) → Phase 7 (통합 yaml)

⛔ Phase 3.5 direction.md 작성 전에 추가 자문 라운드 (R3) 진입 금지 — **R2 수렴 판정 완료 (§5 참조)**.

---

## §2. 현 상태 요약 (Phase 진행)

| Phase | 상태 | 산출 |
|---|---|---|
| Phase 0 — 정리 + 6 SSOT 정독 + cyclical/defensive input | ✅ 완료 | progress.md |
| Phase 1 — evaluation-axes.md (eq_us, AUDIT-GUIDE 12축 application) | ❌ 미진행 (Phase 4 직전 단계로 미룸 — eq_kr 같은 순서) | — |
| Phase 2 — methodology-brief.md (자문 input 4-section) | ✅ 통합 (R1 brief 가 methodology-brief 역할) | raw/consult-round-1-question.md |
| Phase 3 — 자문 R1 + R2 | ✅ **수렴 완료** | raw/consult-round-{1,2}-{gemini,claude}.md 4 파일 |
| **Phase 3.5 — direction.md** (★다음 진입점) | ❌ **미진행** | 본 handoff §6 초안 박제 — 다음 세션이 Write |
| Phase 4 — frame.md (eq_us) + plan.md | ❌ 미진행 | — |
| Phase 5 — 산업 subagent (Tier 차등) dispatch | ❌ 미진행 | — |
| Phase 6 — 별 평가 subagent (★supervisor 직접 평가 금지) | ❌ 미진행 | — |
| Phase 7 — 통합 study_session.yaml + main 승인 | ❌ 미진행 | — |

---

## §3. 사용자 박제 (★mid-session 추가 지시 2건, 다음 세션도 invariant)

### 박제 #1 — 산업별 산출 양식 (Phase 4 frame.md / plan.md 작성 시 반영 의무)

> "각 산업별 리서치 한 내용은 Inv 에 미국 주식 폴더 지정해서, 너가 양식 알려주고 요약본이랑 raw 일부 저장하라고해. 이후에 비슷한 작업을 할때 해당 자료에서 스터디를 시작하기 위함."

**박제 내용**:
1. **저장 위치 통일**: 각 산업 subagent 산출 = `study-research/eq_us/industries/{sector}/` (eq_kr frame.md §5 미러링)
2. **요약본 의무 산출** (재진입용 핵심):
   - `summary.yaml` — 통합용 sub-set (lens · indicators_passed · relationships_passed · weight_rule_candidates · confidence_hooks · collector_plan_industry · open_questions)
   - `12axis-audit.md` — 12축 self-audit PASS/PARTIAL/FAIL + 근거 (Hard-fail 4 = B·C·D·I 우선)
   - `summary.md` (사람용 1-2 페이지) — 산업 cycle 본질 1줄 / 통과 지표 top 5 / 5게이트 통과 표 / 미해결 의문
3. **raw 일부 저장 의무** (재진입 시 출처 추적):
   - `theory-notes.md` — 산업 cycle 이론 정독 (교과서·논문·증권사 in-depth, source URL 의무)
   - `validation-fundamental.md` / `validation-macro.md` / `validation-industry.md` — Layer 1/2/3 실측 (★raw + factor-neutralized IC 둘 다, regime cell 분해, 5게이트 통과 표)
   - `round-1.md` / `round-N.md` — 자문 라운드 원문 누적
4. **재진입 contract** (핵심): 비슷한 작업 (미국 주식 종목 평가 / 같은 산업 재스터디 / Tier 재정렬 / regime 갱신) 진입 세션이 `industries/{sector}/summary.md` + `summary.yaml` + `theory-notes.md` 3 파일만 읽으면 즉시 작업 시작 가능. **각 산업 폴더 = self-contained study capsule**.

### 박제 #2 — agent spawn 후 5분 self-wake + monitoring (Phase 3/5 dispatch 의무)

> "agent 스폰하고 나서는, 5분 self wake 스킬 걸어두고, 멈춘 agent 있으면 재개 시키고 안되면 새로 스폰하고 반복."

**박제 내용**:
1. **agent spawn 후 5분 self-wake 등록**: psmux 본 세션 → `self-wake2` skill (in-process teammate haiku watchdog + SendMessage wake-ping)
2. **멈춤 감지 패턴** (5분 wake 시 점검):
   - Agent: `TaskList` + `TaskGet` 으로 in_progress task 마지막 update 시각 점검
   - psmux subagent: `psmux capture-pane -t {child}` 로 화면 정체 점검
   - 자문 (Playwright Skill): chrome DevTools 로 로딩/응답 spinner 점검 또는 timeout
3. **재개 시도**:
   - Agent: `SendMessage` 로 "진행 상태 보고 + 막힌 점 1줄" → 응답 도착 시 막힘 해소
   - psmux subagent: `psmux_send_message` 로 "현 step 보고 / 막힘 1줄" 또는 Enter/Escape 큐 정리
   - 자문: Skill 재호출 같은 4섹션 brief 동일
4. **재개 실패 시 새 spawn**:
   - Agent: 같은 prompt + 같은 schema 로 Agent 재호출
   - psmux subagent: `psmux kill-session -t {child}` 후 `spawn-session.sh` 재spawn + 같은 dispatch prompt 재전송
   - 자문: 다른 채널 (gemini ↔ claude) + WebSearch/WebFetch 폴백
5. **반복 무한루프 차단**: 같은 agent 3회 재spawn 실패 시 → main(btn-Codlearn) 보고 + 외부 자문 라우팅
6. **양식 박제 위치**: Phase 4 plan.md dispatch table 옆 §모니터링 패턴 + Phase 5 dispatch prompt 양식

---

## §4. R1 + R2 자문 핵심 finding 종합 (★ 모든 raw 의 supervisor 정리)

### R1 자문 (raw: consult-round-1-{gemini,claude}.md)

- **R1 합의 (두 채널 일치)**:
  - Q2 1순위 = **Earnings Revision Breadth (ERB)** / 2순위 = **Total Shareholder Yield (TSY)**
  - Q6 **XLRE 분리** (eq_us = GICS 10 sector)
  - Q8 **skfolio CPCV + alphalens + Ken French FF5** (Claude 가 QMJ + BAB + BH + deflated Sharpe 추가)
  - Q9 핵심 가설 = ERB / TSY / HY OAS regime / Mag7-AI capex 공통

- **R1 ★disagree (R2 핵심 토픽)**:
  - Q1 — Gemini = Mag7 분리 + 10 GICS / **Claude = ★Mag7 GICS 3 sector 파편화 발견** (XLK = AAPL/MSFT/NVDA, XLC = GOOGL/META, XLY = AMZN/TSLA)
  - Q2 3순위 — Gemini = Fed funds path / Claude = HY OAS regime
  - Q3 — Gemini = 구조적 (Bruno-Shin 2015 인용) / **Claude = ★표본 한정 (2022-24 collinearity artifact)**
  - Q5 — Gemini = (c+d) AI capex 30%+ Mag7 cap-up / **Claude = (d) 명시 기각 (reflexive trap) + reflexivity monitor (cap-down)**

### R2 자문 (raw: consult-round-2-{gemini,claude}.md)

- **R2 수렴 (양 채널 정합, R3 불필요)**:
  - **QR2-1 dollar 채널**: Claude 절충 frame 우월 — 3 메커니즘 분리 (translation/commodity = 구조 / financial conditions = artifact). Gemini Bruno-Shin 인용 오적용 자인. 2-cell regime (low-ρ / high-ρ, rolling 252d corr) 구현. **사용자 측 실측 = 2015-2019 β_dxy 회귀**
  - **QR2-2 Mag7 cap**: Claude cap-down + reflexivity monitor 지지 (단 2023-24 single-regime cap-up 보상 인지). monitor trigger spec = intra-Mag7 60d corr > 0.70-0.75 + breadth (EW-CW 3m spread < -3~-5%p 또는 %>200dma <40%) **동시 발생**. Mag7-EW − S&P493-EW spread = regime indicator (Claude) vs priced factor (Gemini) — **regime indicator 채택** (학술: **Daniel-Moskowitz 2016 "Momentum Crashes" JFE**)
  - **QR2-3 PCA eff_N**: 둘 다 합의 — raw PCA 80% = 3-5 PC / residual PCA = 3-6 테마축 → **macro-sleeve (2-4축) > 11 GICS tier**. Claude "각 축 내부 redundant + 축간 진짜 분리" frame 추가 (cyclical-defensive corr 0.3-0.5)
  - **QR2-4 factor decay**: McLean-Pontiff 2016 post-publication 58% (Claude 가 post-sample 26% 추가 분리). **shareholder yield = fundamental tilt → crowding 저항** / **revision breadth = PIT confound 위험**. **사용자 측 실측 = PIT revision IC 재추정**
  - **QR2-5 Mag7 GICS 파편화**: ★사실 확인 — **2018-09-28 (S&P) / 2018-11-30 (MSCI)** GICS 재편 (두 기관 시점 불일치). Mag7 = 31-34% S&P weight, 3 sector 파편 (XLK/XLC/XLY). **T1 재정의 의무 = custom basket (Mag7 + AVGO/ORCL/AMD ± ASML US ADR, ASML 네덜란드 비-S&P500 명시)**
  - **QR2-6 환각 cross-verify**: 4 정정 + 4 verify 권고

- **★사용자측 실측 필요 3건 (Phase 5 산업 subagent 작업)**:
  1. **2015-2019 β_dxy 회귀** (dollar 채널 구조성 판정 — H4 반증조건)
  2. **11-ETF PCA** (raw + market-residual, 80% 분산 PC 개수 → macro-sleeve 차원 확정 — H8 반증조건)
  3. **PIT revision IC 재추정** (look-ahead artifact 확인 — H1·H11 반증조건)

### ★확정 환각 정정 4건 (direction.md citation 시 사용 의무)

1. ~~Asness et al. (2000) "Value and Momentum Everywhere"~~ → **Asness, Moskowitz, Pedersen (2013) JF vol 68**
2. ~~Ben-David et al. (2021) "Do ETFs Increase Volatility?"~~ → **Ben-David, Franzoni, Moussawi (2018) JF vol 73**
3. ~~Gormsen-Lazarus "equity yield"~~ → **Gormsen & Lazarus (2023) "Duration-Driven Returns" JF**
4. ~~Asness-Frazzini-Pedersen (2019) QMJ — JoF/RFS~~ → **Review of Accounting Studies (RAS) vol 24**

### verify 권고 4건 [tentative, direction.md 작성 시 [tentative] 라벨 또는 1회 확인 후 채택]

- Ling-Naranjo (1999 Real Estate Economics vs 1997 JREFE "Economic Risk Factors")
- Brogaard et al. (2023) 0DTE 정확 저자/제목
- Weber (2018) JFE 정확 vol
- Stickel (1991) The Accounting Review 부제

---

## §5. R3 진입 불필요 — 수렴 판정 근거

DA-20260427-external-ai-consult-nudge 수렴 3 조건:
- (a) 두 모델 답변 의미상 일치 또는 명확한 trade-off 합의 → ✅ (R2 disagree 5 항목 모두 Claude frame 우선 합의)
- (b) 새로운 의문 비생성 → ✅ (사용자 측 실측 3건 = direction.md/Phase 5 의 정상 산출, 외부 자문 추가로 해결 안 됨)
- (c) supervisor 가 direction.md 작성 가능 판정 → ✅ (§6 초안 박제 완료)

---

## §6. ★direction.md 초안 (다음 세션이 Write 하면 됨)

> **파일 경로**: `D:/projects/Inv/study-research/eq_us/direction.md`
> **양식**: eq_kr direction.md baseline 미러링 (①이론수집 ②검증방향 ③핵심가설 N)
> **다음 세션 행동**: 본 §6 내용을 그대로 (또는 supervisor 추가 다듬기 후) direction.md 에 Write. main 보고.

---

### direction.md 초안 본문 시작 ▼

```markdown
# direction — eq_us Phase 3.5 (R1+R2 자문 수렴, 2026-05-31)

> STUDY-KIT §2-1 산출. R1 (4섹션 brief 자기완결) + R2 (빈틈 보충 + 환각 cross-verify) 두 채널 (gemini-web + claude-web) 병렬 수렴.

## ① 이론 수집 방향

### 1.1 미국 시장 본질 (한국과 다른 점, R1+R2 핵심)

- **Mag7 GICS 3 sector 파편화** (★R2 사실 확인, 2018-09-28 S&P / 2018-11-30 MSCI 재편)
  - AAPL/MSFT/NVDA = XLK (IT) / GOOGL/META = XLC (Comm Services) / AMZN/TSLA = XLY (Cons Disc)
  - 사용자 의도 "T1 = XLK + XLC = 시총 50%+" 가설 깨짐 → **T1 재정의 의무**
  - Mag7 합산 S&P500 weight = 31-34% (2024-Q4~2025-Q1, 시점·가격 의존)
- **alpha driver 1-3 순위** (R1+R2 합의):
  1. **Earnings Revision Breadth (ERB)** — IBES revision momentum + PEAD, US 가장 안정 cross-sectional alpha
  2. **Total Shareholder Yield (TSY)** — buyback + dividend, fundamental tilt (crowding 저항 예상)
  3. **HY OAS regime** — risk-on/off cyclical↔defensive rotation 최강 분류기. Fed funds path / AI capex = **base driver 아니라 regime conditioner**
- **dollar 채널 = 3 메커니즘 혼재** (★R2 절충, Claude frame):
  1. 다국적 foreign-revenue translation (구조, 표본 무관)
  2. commodity 가격 (energy/materials dollar 표시, 구조)
  3. global risk-appetite / financial conditions (rate cycle 흡수, 표본 한정 artifact)
  - Bruno-Shin (2015) ReStud 인용은 EM/sovereign 메커니즘 — US sector cross-sectional 도달 약 (★메커니즘 오적용)
- **defensive sub-archetype 부호 반대** (cash-flow-mechanical 구조):
  - bank rate-beta (+) — asset-sensitive 대차대조표 NIM
  - utility/REIT rate-beta (−) — bond proxy DCF duration + Treasury 경쟁
- **XLRE 분리** (eq_us = GICS 10 sector) — REIT FFO 별도 valuation, reit study (H1 REJECT 이력) 출력은 exogenous prior 만 import
- **factor decay** (McLean-Pontiff 2016 JF 58% post-publication, 26% post-sample) — shareholder yield 는 fundamental → 완만 / revision breadth 는 PIT confound 위험

### 1.2 이론 정독 list (★환각 정정 적용 reference 22)

**핵심 학술 (Top-tier 저널)**:
- Damodaran NYU Stern (book + data archive 2024) — Sector-Specific Valuation
- Fama & French (1997) JFE vol 43 — Industry Costs of Equity (industry vs factor R² 부정확성)
- ★**Asness, Moskowitz, Pedersen (2013) JF vol 68** — Value and Momentum Everywhere (Gemini R1 환각 정정)
- Asness, Frazzini, Pedersen (2019) **RAS vol 24** — Quality Minus Junk (Claude R1 저널 정정)
- Frazzini & Pedersen (2014) JFE vol 111 — Betting Against Beta
- ★**Ben-David, Franzoni, Moussawi (2018) JF vol 73** — Do ETFs Increase Volatility (Gemini R1 환각 정정)
- Daniel & Moskowitz (2016) JFE — Momentum Crashes (★R2 Mag7 cap 학술 근거)
- McLean & Pontiff (2016) JF vol 71 — Does Academic Research Destroy Stock Return Predictability (decay)
- Boudoukh, Michaely, Richardson, Roberts (2007) JF vol 62 — Payout Yield (fundamental tilt)
- Chan, Jegadeesh, Lakonishok (1996) JF vol 51 — Momentum Strategies (earnings momentum + revision)
- Novy-Marx (2013) JFE vol 108 — Gross Profitability Premium
- Bruno & Shin (2015) ReStud vol 82 — Cross-Border Banking (★caveat: US sector cross-sectional 도달 약, **메커니즘 오적용 주의**)
- Weber (2018) JFE [vol verify 권고] — Cash Flow Duration & Term Structure of Equity Returns
- ★**Gormsen & Lazarus (2023) JF** — "Duration-Driven Returns" (Claude R1 표현 정정)
- Stickel (1991) The Accounting Review vol 66 — Common Stock Returns Surrounding Earnings Forecast Revisions [부제 verify 권고]
- Brogaard et al. (2023) WP — 0DTE Options & Stock Market Quality [verify 권고]
- Elton, Gruber, Blake (1996) RFS vol 9 — Survivorship Bias & Mutual Fund Performance
- Ling-Naranjo (1997 JREFE vs 1999 REE) [verify 권고]
- López de Prado (2018) Wiley — Advances in Financial Machine Learning (CPCV)
- Newey-West (1987) Econometrica — HAC SE
- Bailey & López de Prado (2014) JoPM — Deflated Sharpe Ratio
- VanderWeele & Ding (2017) Annals Intern Med vol 167 — Sensitivity Analysis E-Value

**실무 + 정책**:
- Goldman Sachs (2024) "US Equity Outlook: Earnings and Yield"
- BofA Global Research (2023) "Credit and Equities cycle" (HY OAS sector rotation)
- J.P. Morgan Macro Quant (2023) "FX and Rates cross-asset sensitivity"
- S&P Dow Jones Indices (2023) "Concentration within the S&P 500" + Capping Methodology
- NAREIT Sector Definitions
- CBOE Market Insights (2024) "0DTE Options Volume Analysis"
- SEC Exchange Act Rule (filer 등급별 EDGAR 마감)
- IRA (Inflation Reduction Act 2022) — utility ITC/PTC / Medicare 약가 협상

**OSS / 1차 데이터**:
- FRED (DGS10/DFII10/BAMLH0A0HYM2/DTWEXBGS/WTISPLC/T10YIE/UNRATE/VIXCLS/DFEDTAR) + ALFRED vintage
- SEC EDGAR (10-K/10-Q/Form 4/13F, XBRL)
- Ken French Data Library (Daily FF5 + Mom)
- skfolio / toraniko / alphalens / pyportfolioopt (OSS Python)
- Sharadar Core US (월 $50, survivorship-bias-free 가격) — ★OSS only 불충분 시 도입
- yfinance (가격, ★survivorship-biased, bias 명시 의무)

## ② 이론 검증 방향

### 2.1 평가 SSOT

- **AUDIT-GUIDE.md 12축** (8 핵심 + 4 신규) — Hard-fail 코어 4 = **B (실데이터) · C (추적성) · D (PIT) · I (생존편향)**
- **frame §M4 5게이트** — N≥24 / SE CI 0 / Power MDE>0.05 / FDR q<0.10 / OOS skfolio CPCV
- **frame §M5 toraniko factor model baseline** + **frame §M (신규) Ken French FF5+Mom + QMJ + BAB neutralize 의무** (Claude R1 권고)

### 2.2 OSS validate 인프라 (R2 합의)

- **skfolio CombinatorialPurgedKFold** (CPCV) — overlapping-label leakage 차단, embargo 1-5% + purging
- **toraniko factor model** (Korean KOSPI 와 다르게 미국 = Ken French FF5+Mom + QMJ + BAB neutralize 의무, 모든 alpha → FF5+Mom+QMJ+BAB time-series 회귀 intercept 보고)
- **alphalens** — IC tearsheet (decile spread, IC decay, turnover)
- **Newey-West HAC SE** (lag ~T^(1/4) 또는 monthly 5-10) — 중첩 forward-return 의무
- **block bootstrap** (block length ~T^(1/3)) — IC 분포 (점추정 X) + 5게이트 §SE/CI 직결
- **Benjamini-Hochberg + deflated Sharpe (Bailey-López de Prado 2014)** — multiple testing 보정
- **Ken French Data Library** (pandas-datareader)

### 2.3 ★Tier 차등 분할 (★R2 핵심 — 사용자 의도 GICS 11 Tier 차등 → ★macro-sleeve 재설계)

| Tier | 구성 | 토큰 (opus 1m) | 책임 |
|---|---|---|---|
| **T0 (custom basket, 신규)** | **Mag7 + AVGO/ORCL/AMD (± ASML US ADR, 네덜란드 비-S&P500 명시)** | 400-500k | reflexivity monitor (intra-corr + breadth 동시) / AI capex × fwd EPS / momentum crash tail (Daniel-Moskowitz 2016) |
| **T1 (macro-sleeve, 3-4축)** | (1) cyclical (XLI/XLB/XLE/XLF/XLY-AI제외/SOXX) (2) defensive (XLP/XLU/XLV/XLC-mature) (3) rate-sensitive bond proxy (XLU/XLP-utility-overlap) (4) dollar-sensitive multinational (XLB/SOXX/XLY) | 300k × 3-4 | Macro driver 4 (dollar 3 mechanism + rate / HY OAS / Fed path conditioner) × regime 4 (Reflation/Recovery/Overheat/Slowdown) |
| **T2 (sub-archetype, defensive 분기)** | bank (XLF lending) / insurance (XLF) / pharma (XLV) / biotech (XLV, 고-duration) / utility (XLU) / staples (XLP) / asset manager (XLF) / payments (XLF, quality-growth) | 150-200k × 8 | sub-archetype 부호 반대 (rate +/− / curve 영향 / NIM thesis) |
| **(관측·collection 만, 가중 X)** | GICS 11 sector ETF (XLB/C/E/F/I/K/P/U/V/Y + XLRE 제외) | — | ETF 매핑·data layer |

**★T0 reflexivity monitor trigger spec** (R2 Claude):
- intra-Mag7 rolling **60d 평균 pairwise corr > 0.70-0.75** (baseline 0.5-0.65) AND
- breadth: **S&P 500 EW-CW 3m return spread < -3~-5%p** 또는 **%>200dma < 40%**
- **동시 발생** → cascade flag → concentration **축소** (★cap-up 정반대)

### 2.4 PIT / lookahead

- **EDGAR filing acceptance timestamp** 사용 (★filer 등급별 차등 인지):
  - Large accelerated (S&P 500 대부분): 10-K 60d / 10-Q 40d
  - Accelerated: 10-K 75d / 10-Q 40d
  - Non-accelerated: 10-K 90d / 10-Q 45d
- **ALFRED first-release vintage** (거시) — 이미 `fred_adapter` 적재됨
- **Survivorship-bias-free universe** — OSS only (yfinance + FinanceDatabase) 불충분 → **Sharadar Core US 도입 권고** (월 $50, 또는 yfinance + S&P 500 historical changes wiki + 상폐 ticker 자체 보존 partial fallback + bias 명시 의무)
- **PIT revision IC**: Refinitiv/FactSet retroactive 수정 = look-ahead artifact 위험 → unrestated revision 데이터 재추정 의무

### 2.5 regime cell (eq_kr 36 cell 미러링)

- **Macro regime 4** (Reflation/Recovery/Overheat/Slowdown) — Investment Clock 4국면
- **HY OAS regime 4** (low <300bp / mid 300-500 / high 500-800 / crisis >800)
- **dollar regime** = ρ(Δrate, Δdollar) 2-cell (low-ρ / high-ρ, rolling 252d corr 분위 — ★Claude R2 권고)
- **= 32 cell (4 × 4 × 2)**. N gate (cell N≥24) 강화 의무. cell collapse 가이드 (frame §M3 미러링).

### 2.6 사용자측 실측 필요 3건 (★Phase 5 산업 subagent 핵심 작업)

1. **2015-2019 β_dxy 회귀** (FRED DTWEXBGS + yfinance sector ETF 일별) → dollar 채널 구조성 판정 (β 절댓값 ≥0.3 + 유의 = 구조 / <0.2 또는 불안정 = artifact)
2. **11-ETF PCA** (yfinance 2015-2024 일별 return, raw + market-residual 양쪽) → 80% 분산 PC 개수 (≤5 = macro-sleeve / ≥7 = 11 tier 독립)
3. **PIT revision IC 재추정** (Refinitiv/FactSet unrestated vs retroactive) → backfilled 데이터 대비 IC >30% 하락 시 look-ahead artifact 확인

## ③ 핵심 가설 12 (반증조건 포함)

| # | 가설 | signal source | 반증조건 | confidence |
|---|---|---|---|---|
| H1 | **Revision Breadth (ERB) → fwd 1-3M cross-sec return (+)** (★1순위 alpha) | IBES revision, EDGAR | rolling 3y IC CI 하한 ≤0 OR FF5+Mom intercept NW t<2 OR PIT re-run IC <30% drop | high |
| H2 | **Total Shareholder Yield (TSY) → value/quality alpha, real-rate regime 조건부** (★2순위) | EDGAR Form 4 + 10-Q cash flow, DFII10 | L/S spread CI 가 high·low rate regime 양쪽 0 포함 OR 부호 flip OR ~58% decay (McLean-Pontiff 평균) | medium-high |
| H3 | **HY OAS regime → cyclical↔defensive rotation** (★3순위 conditioner) | BAMLH0A0HYM2 | regime-conditional 수익차 CI 0 포함 OR OAS→sector Granger fail. Transition signal: OAS +100bps/Q | high |
| H4 | **dollar 채널 = translation+commodity (구조) + financial conditions (표본 artifact)**. 2015-2019 β_dxy 회귀로 판정 (★R2 절충) | DTWEXBGS, DGS10, sector ETF | 2015-2019 β_dxy 절댓값 ≥0.3 + 유의 → Gemini 구조설 채택 / |β|<0.2 또는 부호 불안정 → Claude artifact 설 채택 | medium |
| H5 | **bank rate-beta (+) vs utility/REIT rate-beta (−) regime-안정** (cash-flow-mechanical 구조) | DGS10, sub-sleeve fundamental | N≥24 epoch 부호 flip OR CI 양방향 0 cross | medium |
| H6 | **AI capex → Mag7 fwd EPS lag 1-2Q. ★IC regime-unstable** (★reflexivity monitor 의무) | Mag7 10-Q capex | lagged-capex IC 가 capex-peak 후 regime 포함 CI 하한 >0 → durable factor (=H6 기각, 위험) / reflexivity monitor flag 무효 (flag 발효 후 3-6m Mag7 drawdown 비-flag 대비 유의하지 않음) | medium-high (★) |
| H7 | **Fed funds path surprise → duration-sorted event-study CAR** | OIS vs FOMC dot plot | FOMC 주변 CAR 이 duration sort 에 monotonic 아님 OR e-value <1.5 | medium |
| H8 | **sector eff_N ≤5** (★PCA 실측 의무): raw return PCA 80% 분산 ≤5 PC AND market-residual PCA ≤6 PC → macro-sleeve (2-4축) 우월 | yfinance 11 sector ETF 2015-2024 | market-residual 11-sector PCA 80% 분산 ≥7 PC → 11 tier 독립 인정 → Tier 차등 정당화 | high (★R2 양 채널 합의) |
| H9 | **Mag7 reflexivity monitor → cascade risk regime 차단** (intra-corr > 0.70-0.75 AND breadth 협소 동시) | 60d Mag7 corr + EW-CW spread / %>200dma | monitor flag 발효 구간 후속 3-6m Mag7 drawdown 비-flag 구간 대비 유의하게 깊지 않음 → monitor 무효, cap-up 재검토 | medium |
| H10 | **XLRE 분리** (eq_us = GICS 10) — REIT FFO 별도 valuation. naive REIT alpha (H1 REJECT 이력) → exogenous prior import 만 | reit study output | REIT study signal eq_us regressor incremental R² 가 utility 대비 유의 (ΔR² CI 하한 >0) → 단순 중복 아님, 별도 채널 정당화 | high |
| H11 | **shareholder yield post-2010 decay 완만** (Boudoukh 2007 fundamental tilt → crowding 저항) vs **revision breadth post-2015 decay** (information-based + PIT confound) | TSY L/S spread + revision IC time series | shareholder yield 일반 anomaly 동일 ~58% decay → fundamental-resilience 가설 기각 / PIT revision IC < retroactive >30% 하락 → look-ahead artifact 확인 | medium |
| H12 | **factor neutralization (FF5+Mom+QMJ+BAB) 후 sector signal 잔존 alpha = 진짜 alpha** (concentration beta 분리) | toraniko + Ken French + AQR public | neutralization 후 sector L/S spread NW t<2 또는 0 포함 → concentration beta 재포장 | high |

각 가설 = Phase 5 산업 subagent 가 5게이트 통과 시 weight_rule_candidates 등록.
```

### direction.md 초안 본문 끝 ▲

---

## §7. Phase 4-7 plan (다음 세션 작업 가이드)

### Phase 4 — frame.md (eq_us 버전) + plan.md

- **frame.md**: eq_kr frame.md v2 미러링 + ★사용자 박제 #1 (산업별 산출 양식) §5 박제
- **plan.md**: Phase 5-7 dispatch table + ★사용자 박제 #2 (5분 self-wake + monitoring) §모니터링 패턴 박제
- **Phase 1 evaluation-axes.md (eq_us)** 도 Phase 4 와 함께 작성 (eq_kr evaluation-axes.md baseline 미러링, AUDIT-GUIDE 12축 application)

### Phase 5 — 산업 subagent dispatch (Tier 차등)

- **T0 (custom Mag7+AI basket)**: 1 subagent, 400-500k
- **T1 (macro-sleeve 3-4축)**: 3-4 subagent, 각 300k
- **T2 (sub-archetype 8)**: 8 subagent, 각 150-200k
- 총 약 2.4-3.0M tokens (opus 1m, run_in_background)
- **★사용자 박제 #2 의무**: spawn 후 5분 self-wake2 watchdog 등록 + 멈춤 감지 시 재개/재spawn
- 각 산업 산출 = `study-research/eq_us/industries/{sector}/` 8 파일 (frame §5)

### Phase 6 — 평가 subagent (★supervisor 직접 평가 금지)

- 별 opus 1m subagent dispatch
- SSOT: AUDIT-GUIDE 12축 (primary) + evaluation-axes (application)
- §0 Provenance + Recomputation (raw .py 직접 재실행)
- 합성 지문 검사 (★eq_us_defensive synthetic 240m seed 20260530 사건 재발 방지)
- 12축 PASS/PARTIAL/FAIL + Hard-fail 4 (B·C·D·I) 우선
- PARTIAL/FAIL → 해당 산업 subagent 재dispatch (최대 2회)

### Phase 7 — 통합 + main 승인

- eq_us 통합 `study_session.yaml` 7블록 (lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan)
- 산업 summary.yaml 합산 → 직교화 → L축 공통인자 1회 계상 + PSD
- 8축 통합 self-audit (supervisor)
- main 보고 + 승인 게이트 (★승인 전 register 진입 금지)

---

## §8. 자원 정리 (다음 세션 진입 시 cleanup)

- **self-wake2 watchdog** = team `eq_us-wake` / lead `team-lead@eq_us-wake` / watchdog agentId `a23b0ac9b4cdbf313`
- **종료 sentinel 본 turn touch 완료**: `/d/projects/Inv/study-research/eq_us/.watchdog-stop` → watchdog 가 다음 5분 sleep 끝 자동 감지 + exit
- **다음 세션 진입 시**: `TeamDelete({team_name: "eq_us-wake"})` 또는 새 watchdog 재spawn (Phase 5 진입 시)
- **Bash task ID**: 모두 완료 (bo7o7l3i6 / bp1c17ums / bhojlgiy5)

---

## §9. main 보고 양식 (다음 세션이 direction.md 작성 후)

```bash
bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[eq_us→main] Phase 3 자문 R1+R2 수렴 완료, direction.md 산출 (D:/projects/Inv/study-research/eq_us/direction.md). 핵심 finding 5: (1) T1 재정의 = custom Mag7+AI basket (GICS 3 파편화 사실 확인) (2) macro-sleeve 2-4축 > 11 GICS tier (PCA 실측 후 확정) (3) dollar 채널 3 메커니즘 분리 (translation/commodity 구조 + financial conditions artifact) (4) reflexivity monitor cap-down + Daniel-Moskowitz 2016 학술 근거 (5) factor decay 의무 적용 + PIT revision IC 재추정 의무. 환각 4건 정정 (Asness 2013/Ben-David 2018/Gormsen-Lazarus 2023/AFP 2019 RAS). 사용자 실측 권고 3건 = Phase 5 산업 subagent 핵심 작업. Phase 4 진입 승인 대기."
```

---

## §10. 5 금지 + 추가 박제 (모든 Phase invariant)

1. 점추정 prior 박제 금지 — IC 점추정 → base_weight 직접 X. 분포 + CI + 게이트
2. 합성·시뮬 데이터 금지 — 실제 수집기 PIT 만 (★eq_us_defensive synthetic 240m 재발 방지)
3. 자문 그대로 코드화 금지 — supervisor 비판 + 환각 cross-verify 후 채택
4. Single-source 단정 금지 — 학술 + 실무 + 1차 데이터 3중
5. Small-N 단정 금지 — cell N<24 "유의" 주장 X

**추가 박제 (사용자)**:
- ★supervisor 직접 평가 금지 — Phase 6 별 평가 subagent (opus 1m) 위임 의무
- ★analyst-level lens 다운그레이드 금지 — 시스템 못 받으면 파이프라인 업그레이드
- ★opt-in off = byte-identical 무회귀
- ★reflexive loop 차단 — belief→_macro 차단, L축 공통인자 1회 계상 + PSD
- ★tier 정직성 — 검증 통과 ≠ validated alpha. REJECT·contemporaneous = structural prior (저신뢰) 라벨

---

## §11. 5 raw 파일 reference (다음 세션 모든 자문 본문)

| 파일 | 내용 | chars |
|---|---|---|
| `raw/consult-round-1-question.md` | R1 brief (4 섹션 자기완결, Q1-Q10) | ~6000 단어 |
| `raw/consult-round-1-brief-compressed.md` | R1 압축 brief (실제 전송본) | ~2000 단어 |
| `raw/consult-round-1-brief-claude-v2.md` | R1 claude DIRECT ANSWER MODE prefix 추가본 | ~2200 단어 |
| `raw/consult-round-1-gemini.md` | Gemini R1 응답 + supervisor 메모 (환각 의심 cross-verify 후보) | 9035 chars |
| `raw/consult-round-1-claude.md` | Claude R1 응답 + supervisor 메모 (Claude epistemic discipline 우위) | 14765 chars |
| `raw/consult-round-2-question.md` | R2 brief (R1 결론 §0 + QR2-1~6 빈틈 보충 + 환각 cross-verify 의무) | ~2500 단어 |
| `raw/consult-round-2-gemini.md` | Gemini R2 응답 + supervisor 메모 (입장 수정 + 환각 자체 정정) | 7378 chars |
| `raw/consult-round-2-claude.md` | Claude R2 응답 + supervisor 메모 (절충 판정 + R3 불필요 + 사용자 실측 3건) | 10327 chars |

---

## §12. ckpt (압축 내성)

- **ckpt-202605311800-eq_us-phase3-r2-converged-handoff**: Phase 3 자문 R1+R2 양 채널 수렴, 5 disagree 해소 (Claude frame 우선), 환각 4건 정정, 사용자 실측 권고 3건 박제. direction.md 초안 본 handoff §6 박제 완료. **다음 세션 첫 행동 = 본 handoff Read + direction.md Write + main 보고**. 클로드 서버 상태 악화로 본 세션 중단 (사용자 명시).
