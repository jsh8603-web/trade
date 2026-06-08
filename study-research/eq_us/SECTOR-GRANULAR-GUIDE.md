---
tags: [type/guide, domain/equity-us, phase/sector-granular, workflow/teammate]
date: 2026-06-08
purpose: 미국 주식을 sleeve(3 묶음) → 개별 섹터(11 ETF) granular 로 재리서치할 때 각 섹터 teammate 작성 기준. 한국 eq_kr 12산업 스터디와 동일 수준 박제 + 미국 특수 차이만 명시. 기존 frame v3 §M(direction.md) 8파일 체계를 섹터 단위로 내림.
ssot: [AUDIT-GUIDE.md(15축), eq_us/direction.md(frame v3 §M), eq_kr/frame.md(5라운드·M1~M5), eq_kr/industries/*/summary.yaml(7블록 템플릿)]
status: 자문 3R 수렴 반영(§10, 2026-06-08 gemini+claude) — SOXX round-1 초안. ★방향전환: rotation granular 회의(~30%) / 엣지=selection-value
---

# 미국 섹터 granular 리서치 — teammate 작성 기준

> ★원칙: **새 양식 금지**. 한국 eq_kr 12산업 + 미국 frame v3 sleeve 작업의 8파일/7블록/5라운드/5게이트/15축을 **그대로** 복제. 단위만 sleeve → 섹터. 미국 특수 차이(§4·§9)만 갈아끼움.

## §0. 단위 변경 (sleeve → 섹터 granular)

| | 기존 미국 (sleeve) | 신규 (섹터 granular) | 한국 대응 |
|---|---|---|---|
| 단위 | us_cyclical(5섹터 60종 묶음) | SOXX/XLE/XLF/XLI/XLB 개별 | 12산업 개별 |
| 디렉토리 | `industries/us_cyclical/` | `industries/{sector}/` (soxx_semi, xle_energy …) | `industries/{산업}/` |
| rotation 측정 | 3 sleeve ETF timing | **섹터 ETF 시계열**(SOXX/XLE…) conditional | 산업 eq-weight 패널 |
| selection 측정 | 60종 pool sector-neutral | **섹터 12종 cross-section** | 산업 내 종목 cross-section |

★probe 입증(2026-06-08, TENTATIVE): sleeve 묶음이 섹터별 거시 민감도 차이를 평균소거 → rotation β=−0.0006. 개별 섹터 분해 시 rate10y 부호 반대(XLE +0.225 vs SOXX −0.136), hy_oas 5배 차이(XLF −0.843 vs XLE −0.158) 살아남. selection momentum은 약(|IC|<0.03), value(−0.117)가 본질.

## §1. 섹터 티어 + driver 매핑

| 티어 | 섹터(ETF) | 고유 거시 driver (가설) | 한국 대응 | 데이터 |
|---|---|---|---|---|
| **T1** | SOXX(반도체) | AI capex / semi cycle(CLI) / 실질금리(duration) | 반도체 | SOXX 2001~ |
| **T1** | XLE(에너지) | WTI/Brent oil / rate10y(+) / 정제마진 | 정유 | XLE 1998~ |
| **T2** | XLF(금융) | 장단기 금리차(NIM) / credit spread(대손) | 금융 | XLF 1998~ |
| **T2** | XLI(산업재) | PMI / capex cycle / 글로벌 무역 | (조선/기계) | XLI 1998~ |
| **T2** | XLB(소재) | dollar(−) / 중국 PMI / 원자재 | 화학/철강 | XLB 1998~ |
| **T3** | XLP/XLU/XLV(방어) | rate duration / defensive rotation | 통신/바이오 | 1998~ |

⛔ 한국 regime 축(KRW_weak/외국인flow)은 미국 직접 이식 불가(§9). 미국 축 = credit/rate/dollar/vix/oil.

## §2. 산출물 8파일 (한국·미국 sleeve 동일 — 그대로 복제)

각 섹터 `industries/{sector}/` self-contained capsule:
```
round-1.md                    # 이론+가설 5-10개 + 반증조건(증권사리서치·논문 수집)
round-N.md                    # 자문/웹 추가 라운드
theory-notes.md               # 섹터 cycle 이론 정독 (저자·연도 명시, A축)
validation-fundamental.md     # Layer 1 펀더멘털(EDGAR PIT) cross-section IC
validation-macro.md           # Layer 2 거시 + 섹터 driver lag-corr
validation-industry.md        # Layer 3 섹터 특화 신호
summary.yaml                  # 7블록 통합 (§3)
15axis-audit.md               # 15축 자가감사 (hard-fail B·C·D·I 우선)
candidate-ledger.md           # 6분류 (채택/신규cycle/data-gate/미채택/falsifier/flip)
research-log.md               # 작업 로그
```

## §3. summary.yaml 7블록 (한국 템플릿 그대로)

```yaml
블록1 lens:              pricing_principle / cycle_reading / estimation_note
블록2 indicators:        id/layer/family/horizon/ic_mean/ic_ci_95/ic_se_nw/t_nw/n_effective/oos_ratio/source_id
블록3 relationships:     node_a/node_b/lag_months/corr/corr_ci_95/conditioning_set/n
블록4 weight_rules:      indicator_id/base_weight_range/modulate_by/direction/gate_status{n,se,power,fdr,oos}
블록5 confidence_hooks:  hypothesis_id/affects_indicator(★필수)/confirm_signal/reject_signal/feeds_weight
블록6 collector_plan:    missing/source/priority/status
블록7 code_change_plan:  stage(learn|card|inject|falsify)/file/symbol/change/risk
+ conditional_ic_surface: cell_collapse/fdr_family/key_findings/family_2_interaction/walk_forward_oos/verdict
+ valuation_cross_sectional: data_source/mechanism_works/indicators/verdict
+ rotation_timing:       unit/pipeline/candidates_checked/signals/verdict
```
⛔ 점추정 박제 금지 = rho range + OOS + wc_p + tier (한국 §8 동일).

## §4. 측정 2층 + 5게이트 M1~M5 + regime 축 (미국)

**2층 분리 (측정 단위 다름):**
- **rotation (섹터 자체 timing)** = 섹터 **ETF 시계열** forward return vs 미국 거시 regime conditional. predictive(forward) 의무.
- **selection (섹터 내 종목)** = 섹터 12종 **cross-section** sector-neutral z → forward Rank-IC.

**5게이트 M1~M5 (한국 그대로):**
- M1 Rank-IC 월간 횡단면 (IC mean±1.96·SE + N + t)
- M2 lag-corr (섹터 forward vs driver lag 0/1/3/6M, Granger 95% CI)
- M3 **regime cell 32** = Macro 4 × HY OAS 4 × dollar 2 (★미국, 한국 KRW3×flow3 대체. direction.md §2.5). N≥24 gate, collapse fallback
- M4 5게이트: N≥24 / SE(CI 0 제외) / Power(IC>0.05) / FDR BH q<0.10 / **OOS skfolio CPCV**(IS 2010-2021 / OOS 2022-2026, embargo 5d)
- M5 factor neutralize = **FF5+Mom+QMJ+BAB**(Ken French + AQR, ★미국 특화. 한국 toraniko 대체)

★fixed-b size-valid 의무 (rework 발견1: small-block NW asymptotic = over-rejection artifact). effective_n = n/(1+2Σρ_k) 선행 산출 → fixed-b CV 적용.

## §5. 15축 audit (hard-fail 코어 4)

A 이론실재 / **B 실데이터★**(OOS IC>0.03 t>2.0) / **C 추적성★**(yaml=실측±5%) / **D PIT★**(EDGAR filing 지연 / 익일시가 / FRED vintage) / E 환각 cross-verify / F 반증·기각≥1 / G eff-N tier / H 미해결 / **I 생존편향★**(상폐 ticker / S&P historical / Sharadar) / J 거래비용 0.3% / K 다중검정(시도횟수 공시) / L 통합 PSD(공통인자 1회계상) [+ M~O wire].
→ **B·C·D·I 위반 = 통합 차단**. Phase 6 독립 audit subagent(hard-fail 0 전 adopted 금지).

## §6. 5라운드 워크플로우 (각 teammate)

```
R1 이론·가설  → 증권사 리서치·논문 수집 → round-1.md(가설 5-10 + 반증조건) + theory-notes.md
R2 실측준비   → EDGAR(10-K/Q PIT) + yfinance(가격, 생존편향 명시) + FRED(거시 vintage) 적재
R3 실측       → validation-{fundamental,macro,industry}.md (raw + FF5-neutralized IC 둘 다)
              → M1~M5 + M3 regime 32셀 + fixed-b size-valid
R4 통합·자가감사 → summary.yaml 7블록 + 15axis-audit.md (hard-fail B·C·D·I 우선)
R5 보고       → supervisor(main)에 final message (PARTIAL/FAIL 축 명시, 본문 ctx inject 회피)
```

## §7. 금지 5종 (모든 라운드 invariant)

1. 점추정 prior 박제 금지 (IC 점추정 → base_weight 직접 X, range+CI+OOS)
2. 합성·시뮬 데이터 금지 (random walk·가상 ticker, ★eq_us_defensive 합성 240m seed 재발 방지)
3. 자문 그대로 코드화 금지 (gemini/claude 답 → yaml 직접 X, 본인 실측 검증)
4. single-source 단정 금지 (1 출처만 "확정" X, multi-source confirm)
5. small-N 단정 금지 (cell N<24 "유의" X) + supervisor 직접 평가 금지(Phase 6 독립 audit)

## §8. 점진 확장 + teammate 운영 (사용자 지시)

- **점진**(한국 동형, progressive-rollout): **① SOXX 파일럿 1개** → 파이프라인·양식 수정 → **② 3개**(SOXX/XLE/XLF) → **③ 티어 확대**(T2/T3).
- **teammate = named in-process** (subagent 아님). ⛔ **작업 끝나도/idle 돼도 KILL 금지** (idle=정상, SendMessage로 깨움). 한국 semi-analyst@kr-equity 동형.
- 대규모 dispatch = resource-consume-consent (사용자 확인 후 착수).

## §9. 한국 지표 → 미국 이식 매핑 (★재설계 필요)

| 한국 산업 | 한국 신호 | 미국 이식 | 미국 재설계 driver |
|---|---|---|---|
| 반도체 | KRW_weak regime + SOXX선행 | △ regime 축 교체 | AI capex / semi CLI / 실질금리. regime = HY OAS×dollar |
| 화학/철강 | spread_china / iron_ore | ✗ | XLB: dollar(−)·중국 PMI (셰일ethane·관세 맥락) |
| 정유 | 유가 mean-rev | ○ XLE 직접 | WTI/Brent / crack spread |
| 금융 | credit_spread(대손) | △ | XLF: 장단기금리차 NIM(미국 우선) + credit |
| 배터리/조선 | lithium/발주 | ✗ 섹터 부재 | drop |
| 바이오/IT | rate duration | ○ | XLV/XLK: 실질금리 duration |

★핵심: **신호 형태(momentum/value/capex anomaly)는 universal**, **regime 축·fundamental driver는 미국 고유 재설계**. 한국 "방법론" 이식 ○, 한국 "지표" 직접 이식 ✗.

## §10. 자문 3R 수렴 반영 (2026-06-08, gemini-web + claude-web 병렬) — ★SSOT override

> ⛔★사용자 정정 (2026-06-09, §방향보존 ERROR): **아래 §10.1~10.7 요약은 자문 원문을 비관 쪽으로 왜곡함.** 원문 방향성 복원:
> 1. **산업 배분(rotation / 슬리브간) = ★주 레버, 살릴 여지.** 동적 분기타이밍이 아니라 **정적 틸트(static tilt)** + 수축(shrinkage) + 사후평균 + 다중비교 깐깐 검증으로 **살린다**. ("rotation 회의 ~30%·보류·슬리브간 어렵다" = 왜곡, 폐기 아님).
> 2. **종목선택(selection / 슬리브내) = 현 좁은 틀(대형주 top-10 동일가중)에서만 약했던 것.** 소형·딥밸류 종목을 못 담아서지 **가치 무효 아님**. ("value-only / 무가치 / 죽음" = 왜곡).
> 3. **반도체 freeze→철회(horizon 축 부족) 통찰 = ★사용자 지적 귀속** (main 발견 아님).
> → 아래 §10.1~10.7 비관 톤(★☆☆ 강등·회의·dead 등)은 이 정정 하에서 "정적 틸트로 살리되 깐깐 검증" 으로 재해석. 자문 원문 = `~/.claude/.claude-web-basic-last.md` (raw substring 우선).
>
> 3자(로컬 probe + Gemini + Claude). 본 §10이 §0~§9 충돌 부분을 override. 원문 = `.consult-us-sector-granular-briefing.md` + `~/.claude/.gemini-web-last.md` + `~/.claude/.claude-web-basic-last.md`.

### 10.1 방향 전환 (★사용자 원 가정 정정)
"섹터 분해 → rotation+selection 둘 다 발현"은 **부분만 맞음**. **rotation granular 회의적(~30%), 진짜 엣지 = selection-value**. 층 분리: selection층 (D)factor-cancel 교정완료 / rotation층 (C)시장구조 우세.

### 10.2 rotation granular ★☆☆ 강등 (Gemini ★★★→강등)
eff_N=1.47, within-corr 0.617(11섹터 ≈1.5 독립베팅, 한국 3.52 절반) + granular가 **시계열 small-n 벽을 못 고침**(같은 월수) + McLean-Pontiff 58% 차익거래 소멸. probe ②β차등 = **exposure 이질성이지 predictive alpha 아님**(necessary-not-sufficient).

### 10.3 selection = value-only 선택적 granular
momentum granular = **MDE_IC≈0.107 미달 dead-on-arrival**(|IC|<0.03, 한국 steel −0.181의 1/6). value(−0.117) = 경계 → **DL EB partial pooling**(half-Cauchy between-sector SD prior) 필수 + **MDE 통과 섹터만**. 전면 freeze도 전면 granular도 아님.

### 10.4 측정 단위 정정 — EW-semi (★cap-weight SOXX 금지)
SOXX cap-weight = NVDA 단일베팅 위장(megacap idiosyncratic을 섹터 timing β로 둔갑). **EW-semi**(횡단검정과 동일 PIT constituent에서 EW 직접 구성 + CRSP delisting return, XSD ETF는 sanity anchor만)로 megacap/섹터timing 직교 분리. ※XSD≠SOXX(유니버스·방법론 드리프트).

### 10.5 SOXX 파일럿 측정 설계 (★primary 스왑)
- **Primary = within-sector value-selection forward excess(ρ 채널)** — EW-semi + macro 통제 net, fixed-b, walk-forward OOS, MDE 0.107 사전스크린.
- **Secondary = book-to-bill-family(κ 타이밍) 강등**. ※데이터 가용성 검증 의무(SEMI bookings 2016·billings 공개 2022 종료 + 3MMA 지연 + capex reflexive 오염 주장 = claude R3, 미검증). 대체 lead = TW/한국 반도체 수출(월별 정부 PIT-clean, 단 κ + 3MMA시 eff_N≈1).
- **통제변수 = 관측가능 사전지정** {market(SPY excess), EW-semi return, rate10y vintage, credit OAS, broad dollar}. **PCA 기각**(단일섹터 PC1=EW-semi 내생성 → within 성분 흡수 편향 + DOF/look-ahead). PCA는 secondary robustness lens만(PC1↔EW-semi ρ>0.95면 불필요 증거).

### 10.6 단일 결정실험 = within-sector predictive decomposition
`R_{i,t+1} − R_f = α + Σβ_macro·F_t + γ·Signal^within_{i,t} + ε`. γ 유의(within 비-null) → **(D) granular 정당** / γ null → **(C) freeze**. ★예측 기준(lagged signal → forward excess), 노출 β 차등 아님.

### 10.7 Entry gate 사전약정 (★forking-paths 방화벽, 박제)
1. **MDE 사전스크린**: 섹터별 회복가능 |effect| > granular N의 MDE(≈0.107) 미달 섹터는 predictive 검정 자체 skip.
2. **decomposition-first**: within-sector 예측성분 null이면 즉시 중단 = (C) 수용.
3. **Korea-grade**: predictive + fixed-b size-valid + walk-forward OOS(IS/OOS 사전분할), regime taxonomy 사전지정(새 정의 탐색 금지).
4. **FDR 원장 과금**: granular 재측정 = BY/LORD++ 원장 1 family 추가, alpha budget 차감. 미생존 시 정의 변경 재실행 금지.
5. **★Freeze default**: primary(value-selection) MDE 미달 → **rotation-granular 영구폐기 + 3슬리브 value-selection 100% 집중**. secondary(κ) 단독 graduation 금지(다중검정 도용 차단).

> ※자문 대안 2종 처리: 대안2(rotation 폐기 + 3슬리브 value-selection 집중) = 위 Freeze default로 채택. **대안1(Factor-Neutralized EW between-momentum rotation)은 rotation ★☆☆ 강등으로 보류** — decomposition γ(within 예측성분) 유의 입증 시에만 재검토, 현 파일럿 단계 skip.

## §11. teammate dispatch 템플릿 (★다음 섹터부터 한번에 — prompt full 박제)

> SOXX 파일럿에서 prompt를 부실하게 띄워 보강 SendMessage가 필요했던 실수 자산화. **다음 섹터(XLE/XLF/XLB/XLI/XLP/XLU/XLV) teammate는 본 템플릿의 `{SECTOR}/{TICKER}/{한국대응}/{driver}`만 치환해 한번에 full prompt로 스폰**. 보강 불필요.

### 스폰 커맨드
- 팀 = 기존 `us-equity` 재사용(이미 존재, TeamCreate 재호출 X).
- `Agent(team_name="us-equity", name="{SECTOR}-analyst@us-equity", model="opus", subagent_type="general-purpose", run_in_background=true, prompt=아래 템플릿)`.
- ⛔ 단순 `Agent(run_in_background)` 만 = teamless subagent(금지). `team_name`+`name` 필수.

### prompt 템플릿 (치환 후 그대로)
```
너는 미국 {SECTOR}({TICKER}) 섹터 granular 리서치 analyst teammate `{SECTOR}-analyst@us-equity`다 (team=us-equity, 한국 {한국대응}-analyst 대칭).

[절대규칙] 1.산출 디스크 영속화+작업단위 미커밋0 2.entry gate: primary=within-sector value-selection(ρ), MDE_IC≈0.107 미달→(C)freeze, rotation 회의(~30%)=falsify 대상, forking-paths 금지(regime/지표 사후탐색 X 사전등록) 3.점추정박제금지(CI+OOS+wc_p+tier)·합성금지·자문코드화금지·single-source금지·small-N(cell<24)단정금지 4.team-lead@us-equity SendMessage로 지시·보고, idle=정상(종료 아님).

[정독 의무 4개, 착수 전] (a)eq_us/SECTOR-GRANULAR-GUIDE.md §10+§11+★§12(측정 교훈: horizon 다양화 y_5d/20d/60d + conditional overlapping NW-HAC 보정 의무) (b)AUDIT-GUIDE.md 15축(A~L study+M~O wire, hard-fail 코어4=B실데이터/C추적성/D PIT/I생존편향) (c)industries/{SECTOR}/round-1.md (d)한국 eq_kr/industries/{한국대응}/summary.yaml 7블록+candidate-ledger.md 6분류.

[8파일 산출] round-1.md/theory-notes.md/validation-fundamental.md/validation-macro.md/validation-industry.md/summary.yaml(7블록)/15axis-audit.md/candidate-ledger.md.

[5라운드] R1 이론·가설(증권사리서치·논문수집→가설+반증조건 prereg) → R2 실측준비(EDGAR/yfinance/CRSP delisting/FRED fetch) → R3 실측 M1~M5 → R4 summary.yaml 7블록+15axis-audit.md → R5 보고(15축 self-check, hard-fail B/C/D/I).

[5게이트 M1~M5 (R3)] M1 Rank-IC 월간횡단면(IC mean±1.96SE+N+t_nw) / M2 lag-corr(상관도, Granger 95%CI) / M3 regime 32셀(Macro4×HY OAS4×dollar2, N≥24 gate) / M4 5게이트(N≥24·SE CI0제외·Power IC>0.05·FDR BH q<0.10·OOS skfolio CPCV embargo5d) / M5 FF5+Mom+QMJ+BAB neutralize. ★fixed-b size-valid 의무(effective_n=n/(1+2Σρ_k) 선행).

[측정단위] rotation=섹터 EW-index 시계열(★cap-weight ETF 금지=megacap 위장 분리, 동일 PIT constituent EW+CRSP delisting) / selection=섹터 종목 cross-section sector-neutral z. ★value-only granular(momentum은 MDE 미달 dead-on-arrival).

[섹터 driver] {driver — §1 티어표}. ★한국 지표 직접이식 금지, 미국 regime축(credit/rate10y/dollar/vix/oil) 재설계. regime 사전등록(사후탐색 금지).

지금 R1: 증권사리서치·논문→ (a)value premium 증거 (b)섹터 cycle 지표(lead성·PIT 검증, FRED id 환각주의) (c)한국 차이 (d)추가가설+반증조건. 산출=theory-notes.md(저자·연도=A축)+round-1.md 보강. 완료 시 SendMessage(to=team-lead@us-equity) 보고(가설 3-5줄+경로+미해결+15축 A/E/F 자가체크) 후 idle.
```

## §12. ★SOXX 파일럿 측정 교훈 (다음 섹터 측정 축 명문화, 2026-06-08)

> SOXX 파일럿(soxx_semi)이 R3 freeze 오판 → R4 보정으로 정정한 과정에서 도출한 ★측정 축 2 교훈. 다음 섹터 R3 측정 시 의무 적용.

### 12.1 ★horizon 다양화 필수 (y_5d / y_20d / y_60d) — 단일 horizon freeze 오판 방지
- SOXX R3 = y_20d 단일 horizon만 측정 → value IC +0.068(약, MDE 경계) + decomposition γ null → ★**(C) freeze 오판**.
- R4 재측정 = **y_60d 로 보니 value +0.104**(wc_p 0, 단조 증가) + low_vol −0.118 명확 발현. = ★단일 horizon 누락이 freeze 오판 원인.
- ★**의무**: R3 selection IC 측정은 **y_5d / y_20d / y_60d 3 horizon 전부** 측정. value/저변동 류는 장기 horizon(y_60d)에서
  발현하는 경향(한국 반도체도 24M_value 가 본진). 단일 horizon 약신호로 freeze 판정 ⛔금지.

### 12.2 ★conditional regime 증폭 = overlapping 자기상관 보정 의무 (day-cluster t 부풀림 artifact)
- SOXX R3 = family-2 interaction(signal × regime_dummy) **day-clustered SE** → value×rate_high t=4.61 "유의" 보고.
- R4 보정 = **60d block-cluster SE**(overlapping 자기상관 흡수) → t=4.61 → **1.31 붕괴**(비유의). = ★day-clustering 이 60d
  overlapping return 자기상관 미흡 = t 부풀림 artifact.
- ★**의무**: forward h일 overlapping return 의 conditional/interaction 검정은 **Newey-West HAC(lag=h)** 또는 **block-cluster
  (block≈h)** SE 필수. daily n 이 "powered"여도 overlapping = 유효 표본 n/h. ⛔ day-cluster/IID t 로 conditional 증폭 "유의"
  단정 금지(한국 24M overlap eff_indep≈2.5 degenerate 전례 동형). unconditional main effect 도 NW-HAC t 로 재확인.

### 12.3 부수 교훈
- ★FRED series id 환각 주의: 박제 전 실존검증(curl http code) 의무. SOXX에서 3건 날조 적발(404).
- ★자문 통설도 falsify: Novy-Marx "value+quality 결합 강화" = SOXX 12종선 quality 무신호로 희석(반증). 자문 prior 재현 검증 의무.
- ★생존편향 I축: 현 holdings only universe = TENTATIVE 상한(CONFIRMED 불가). historical membership(CRSP/ETF PIT) 무료부재 시 정직 PARTIAL.
- ★data 라벨 검증: 컬럼명(rate10y)과 실값(nominal vs 실질) 일치 확인(spec↔code match). SOXX에서 "DFII10 실질" 라벨이 nominal(DGS10)이었음.

### 12.4 ★leave-N-out (factor vs N-name bet) + non-overlap t 의무 (R5 게이트 자산화, 2026-06-08)
- ★SOXX value 가 overlapping NW-t=2.73 + BY 생존으로 "PARTIAL_CONFIRMED" 보였으나, **NVDA·AVGO leave-2-out retention=0.044**
  (두 종목 빼면 IC 0.104→0.005 소멸) = ★**position-not-factor**(2-name bet)로 강등. small-N 섹터(12종)는 1~2 megacap 이
  cross-section IC 를 지배 가능 = factor 위장.
- ★**의무** (small-N 섹터 selection IC tier 확정 전):
  (a) **leave-top-N-out**: 시총/지배 상위 1~2종 제외 후 retention = IC₍₋N₎/IC₀. ≥0.70 → factor / 0.40~0.70 → concentration-dependent /
      <0.40 → position-not-factor 강등.
  (b) **non-overlap t PRIMARY**: forward h일 IC 의 tier 는 **비겹침(T/h obs) t** 에 앵커링(overlapping NW-t 는 보조). daily-overlapping
      t 가 부풀 수 있음(SOXX value overlapping t=2.73 vs non-overlap t=2.11).
  (c) **misspec 부호 점검**: low_vol/BAB 류는 ★부호 방향 확인 의무(저변동 outperform = 정상 / 고변동 outperform = anti-BAB =
      AI 고베타 misspec 포장). pre-AI 단독 + beta·momentum 직교화 후 정상부호+|t|≥2 아니면 KILL.
- ★SOXX 결론: value = weak/2-name-concentration(PROVISIONAL, factor 미입증) / low_vol = REJECTED-as-constructed(anti-BAB KILL).
  = ★small-N 섹터 selection 은 leave-N-out + non-overlap + 부호 점검 통과 전 "신호 확보" 단정 금지.
