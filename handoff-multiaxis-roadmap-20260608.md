---
next-action: "자문 3R 수렴(§9) 반영 후 6 worker teammate spawn(§5 분담). critical 즉시버그 없음(C1=측정버그·C2=coin outlier 의심, 둘다 자문/측정정정 대상). 개선 5종 자문 결과대로 W1~W6 착수. healer=메인 통합, 검증 teammate 1~3. 불변식: off=byte-identical/push·go-live 미접촉/안전장치값 무단변경 금지."
session: btn-Inv (opus, long-mode ON2 750k)
date: 2026-06-08
tags: [type/handoff, topic/multiasset-attribution-roadmap, domain/multiasset]
---

# handoff — 멀티에셋 17축 attribution 분석 + 6 worker 개선 로드맵 (2026-06-08)

> plan=plan-final-test-20260607.md / progress=progress-final-test-20260607.md(Working Notes ckpt-202606082030)
> 직전 핸드오프=handoff-prod-backtest-line-20260608.md(배선 복구 §1~§7, 본 파일이 후속)
> 측정 SSOT 로그=`D:/projects/Inv/.p4-backtest-multiaxis.log`(17축 실측), 측정 코드=`scripts/run_multiasset.py` run_backtest

## §1 현재 상태 · 첫 행동

**현재 상태**: 프로덕션 파이프라인(run_multiasset.py --backtest)이 정상 작동 = 거시 regime 분류 → 7자산군 비중 → 업종분해 → 종목 gate/judge → 통합 NAV. 배선 복구 완료(load_dotenv + INV_R15_WEIGHTS + orchestrator 게이트 통일, 직전 핸드오프). 17축 attribution 측정으로 자산·산업·층위별 저조 영역 식별 완료. **전체 NAV 4.292(CAGR+17.57%), Sharpe 1.13, MDD -15.45, IS/OOS 동부호(과적합 아님), orphan 0**.

**★W2(regime) 영역은 본 세션 완료(2026-06-08)**: C2/I1 = regime→배분 -0.91 오정렬 진단→R1~R4 자문→데이터 3중 검증→**절대 CPI 게이트+SLOWDOWN 국면 신설 fix 적용·검증 통과(adopted)**. 상세 = cross-regime-ledger §2 "regime→sleeve 비중표 정렬" 행 + 본 §아래 W2-DONE. 남은 worker = W1/W3/W4/W5/W6.

**첫 행동(재개)**:
1. ★**아래 §4 팀메이트 공통 의무(MANDATE) 4개 먼저 정독** — 모든 worker/검증 프롬프트에 박제 필수.
2. §5 분담대로 남은 worker(W1/W3/W4/W5/W6) opus 1m + 검증 teammate spawn(사용자 승인 후).
3. C1 측정 정정 = W6 흡수.

---
## ★§4-0 팀메이트 공통 의무 (MANDATE — 사용자 명시 2026-06-08, 모든 spawn/검증 프롬프트 박제 필수)

1. **의도 우선 읽기(필수)**: 각 worker 프롬프트는 착수 전 **README.md + CODEMAP.md + 해당 모듈 .md(ledger 등)에서 설계 의도를 먼저 읽고 시작**하라고 명시. "코드부터 고치지 말 것, 수정 전 CODEMAP 해당 모듈 '설계 의도' 확인 → 수정 후 CODEMAP 동기화"(프로젝트 CLAUDE.md 규칙). ★본 세션 ERROR 2회(수정 전 의도확인 누락)=promo-log, 재발 방지 위해 강제.
2. **검증 공정에도 동일 명시(필수)**: 검증 teammate 프롬프트에도 "worker 수정분이 README/CODEMAP의 설계 의도와 정합하는지" 확인을 공정으로 박제(단순 회귀 통과 + raw 재현뿐 아니라 의도 정합 판정).
3. **복잡 설계는 메인 3R 자문(필수)**: worker가 복잡한 설계 판단(계약 변경·신규 모듈/국면·A/B trade-off·임계 추정)에 부딪히면 **메인이 gemini+claude 3R 자문 필수**(본 세션 regime fix가 그 예: R1~R4 + 데이터 검증 + import-not-estimate). worker 단독 설계 확정 금지.
4. **구현 내용 전달 명시(필수)**: 메인이 자문/설계로 확정한 **구현 내용(스펙·임계·파일·함수·방향)을 worker에게 명시적으로 전달**. worker가 자문 결론을 모른 채 재구현하지 않도록, 확정 스펙을 프롬프트/SendMessage로 박제.
---

## §2 17축 실측 분석 (추정 없이 .p4-backtest-multiaxis.log 수치)

### 자산군 기여 (③ 한/미 포함)
| 자산 | 누적기여 | 분기평균 | Sharpe | 판정 |
|---|---|---|---|---|
| coin | +0.630 | +0.2544 | 0.79 | 최대 기여, 변동성 큼(regime 무관 폭등) |
| us_stock | +0.494 | +0.0619 | 1.03 | **양호** |
| kr_stock | +0.163 | +0.0388 | 0.79 | **약함**(us의 1/3, 종목선택 미구현) |
| gold | +0.115 | +0.0286 | 1.03 | 정상 |
| commodity | +0.098 | +0.0277 | 0.61 | 정상 |
| bond | +0.069 | +0.0100 | 0.83 | 정상 |
| cash | +0.023 | +0.0051 | 2.54 | 정상(저변동) |

### 17축 판정표
| 축 | 측정값 | 판정 | 원인 L0~L3 |
|---|---|---|---|
| ① 거시신호 regime 예측력 | coin이 전 regime 최고수익(Reflation+0.99/Stagflation+0.17), Recovery만 us 등장 | 🟡 개선 I1 | L1 이론(regime이 코인 예측 못함, 주식엔 약하게 맞음) |
| ② 거시→배분 비중-수익 corr | Stagflation **-0.79**/Reflation -0.28/Overheat -0.06/Recovery +0.20 | 🟡 판정필요 C2 | L1(매핑) — **단 coin outlier 의심**(coin w낮은데 수익최고→corr 끌어내림), coin 제외 재측정 필수 |
| ③ 한/미 배분 | us +0.494/kr +0.163 | 🟡 개선 I3 | kr 약함=종목선택 미구현 |
| ④ 산업간 배분 | us cyclical/defensive 같은 비중0.114인데 수익 +0.073 vs +0.020 / kr battery최대비중인데 bio최고수익 | 🟡 개선 I2 | L1/L2c(시총비례가 수익과 역행) |
| ⑤ 산업내 선택 alpha | 전부 +0.0000 | ⚠️ **측정버그 C1** | (a)측정 tautology: alpha=통과종목가중−통과종목EW인데 비중=capped-EW라 무조건0 (b)설계: target_weight=capped-EW(저평가는 종목집합만, 비중차등 없음) |
| ⑥ 게이트 거부사유 | max_weight_single 21회(0.8%) | 🟢 정상 | 캡 정상 작동 |
| ⑦ 종목 집중도 | us 10.4종목/최대25.6%, kr 80.6종목/최대26.7% | 🟢 정상 | sleeve 내부 비중(전체는 ×w_sleeve) |
| ⑧ IS/OOS 과적합 | IS Σ+1.007/OOS Σ+0.585 동부호 | 🟢 정상 | 과적합 아님 |
| ⑨ judge 감쇠 | a=1.000(무감쇠) | 🟢 정상 | 결정론 baseline 의도(down-only 미작동=설계) |
| ⑬ VIXCLS vol factor | source_missing(ALFRED vintage 3864>2000 한도) | 🟢 데이터 | L2b(factor 공분산 vol 차원 결측, regime/weights는 별경로라 작동) |
| ⑯ regime confidence | conf=?(추출 실패) | 🟢 데이터 | L2(mv.regime confidence 속성 추출 실패, 사이징 미반영) |
| ⑭ survivorship | us universe survivor-only | 🟡 개선 | haircut ~1.2%p/yr 가정값(CRSP delisting 미보유) |

### ★critical 재판정 (중요 — 추정 정정)
- **C1(종목선택 alpha=0)**: 처음 "종목선택 작동 안 함"으로 단정했으나 코드(selection_pipeline.py:16,61) 확인 결과 **파이프라인 버그 아님**. 진실 = (a) 내 측정 alpha가 tautology(통과종목 vs 통과종목EW = capped-EW면 무조건 0) (b) 설계상 target_weight=capped-EW(저평가는 top-K 종목집합만 고르고 비중은 동일가중). → **측정 정정**(선택종목 vs 업종 전체 universe EW로 비교) 필요 = W6. + 비중차등 도입은 개선(I, 자문 Q4).
- **C2(regime corr 음수)**: coin이 비중 낮은데 수익 최고 → corr 끌어내림(outlier 의심). coin 제외 재측정 전엔 "매핑 자체 문제"로 단정 불가 = W2 진단(자문 Q2).
- **즉 즉시 고칠 명확한 파이프라인 버그는 없음**. 전부 측정 정정 + 자문 판정 + 개선.

## §3 사용자 박제 (대화 고유 결정 — ⛔ 모든 논의 박제)

1. **R5 강한 정정(직전)**: "실제 프로덕션 파이프라인으로 테스트" = 별도 드라이버 신설·자체회계·gate/judge 우회 **금지**. run_multiasset.py 보수해서 그걸로 테스트. promotion-log ERROR 박제.
2. **"연결 ≠ 완성"**: "테스트 완료라고 끝낼 생각 없다, 이제 겨우 연결 끝(완성도 무관), 개선 루프가 본론." 배선 복구는 시작점. (promotion-log OBSERVE)
3. **"추정 금지, 정확히"**: attribution을 머리로 짐작 금지, 실측 로깅으로만 보고. 로깅 세분화 부족하면 재테스트 허용.
4. **원인 격리 축 = 5층 → 17축**: 사용자가 5층(거시신호/거시→배분/한미/산업간/산업내) 제시 → "5개 이상, 많을수록" 요구 → 17축으로 확장.
5. **잘됨/잘못됨 분석 + critical vs 개선 구분**: critical(어느 축이 잘못=버그) vs 설계정합인데 개선필요 → 우선순위 로드맵.
6. **teammate 작업 방식(직접 지시)**: harness2-wf **프로토콜 미사용**(상태머신/execution-log X), **teammate 메커니즘만 참고**. **opus 1m worker 6기** spawn, 각자 **한 파트 전담**(컨텍스트 유지). harness2는 worker 1기 기준이라 worker4+verifier+healer 구성은 안 돎(사용자 지적). **검증=별도 teammate opus 1m 최소 1기, 병목 시 2~3기**. **healer=메인(나)이 직접 통합**.
7. **critical/개선 처리 분리(직전 지시)**: critical=버그수정이니 **바로 되면 자문 없이** 수정 / 개선=**자문 3R(gemini+claude)에 모두 포함**. 자문 결과 바탕 + 자문 포인터 연결 핸드오프.
8. **불변식**: push·go-live·실주문 미접촉. DRY_RUN/KIS paper. 안전장치값(MAX_WEIGHT_SINGLE 0.10/SECTOR 0.30) 무단변경 금지. off=byte-identical. 부품·엔진 무단변경(버그 판정 시만).
9. **다축=통합 백테스트**: 7자산군+한미 업종/ETF를 한 번에 굴림(분리측정=성분분해).

## §4 6 worker 분담 + 작업 방식 (teammate 스폰 — 사용자 논의 전부)

### 스폰 방식
- **Agent tool**(subagent 아님 = teammate): `name` 지정 + `run_in_background:true` + `model:"opus"` + `SendMessage`로 mid-flight 양방향 조종 + agentId resume 관통(자동압축). harness2-wf 프로토콜(상태머신·execution-log·SR debate) **미사용**, teammate 메커니즘만.
- 각 worker = **한 파트 전담**, SendMessage로 후속 지시(같은 파트 계속 = 컨텍스트 유지).
- **Supervisor = 메인(나)**. **healer = 메인**(FAIL 직접 수정·충돌 resolve·attribution 재측정). **검증 = 별도 teammate 1기**(병목 시 2~3기).

**실제 spawn (teammate = TeamCreate + Agent, ★2026-06-08 정정)**: ⛔ **Agent 직접(team_name 없이)=일반 subagent=SendMessage 양방향 불가**(실측: worker가 "SendMessage isn't available" 보고). teammate로 하려면 = ①`TeamCreate(team_name="inv-wN", agent_type="supervisor")` 선행 → ②`Agent(subagent_type="general-purpose", name="W3-sector", team_name="inv-wN", model="opus", run_in_background=true, prompt=...)`. 조종 = `SendMessage(to="W3-sector", ...)` (idle teammate 깨워서 후속 지시→컨텍스트 유지). 완료/idle 알림 자동 수신. spawn-session.sh/psmux는 불필요(in-process teammate). harness2 프로토콜(상태머신·execution-log·SR debate)은 미사용, teammate 메커니즘만.

**worker 프롬프트 템플릿** (각 W에 채워서 주입):
```
[역할] 너는 {파트}(예: regime 배분) 전담 worker. 아래 모듈만 수정한다: {전담 파일}.
[맥락] 멀티에셋 백테스트 run_multiasset.py --backtest 가 17축 측정으로 {해당 축} 저조 발견. 측정 SSOT=.p4-backtest-multiaxis.log, 분석=handoff-multiaxis-roadmap-20260608.md §2·§9.
[임무] {§9 자문반영 우선순위의 해당 worker 임무}. 예 W2: ①coin을 regime weight서 제외+H25(coin_sizing.py, 이미존재) 재활용한 coin-native throttle ②coin 제외 후 regime-에피소드별 정렬 재측정(2022 단일점 여부) ③mv.regime confidence 추출(conf=? 해소).
[불변식 ⛔] off=byte-identical(레거시 run_agents 무영향)·push/go-live/실주문 미접촉·DRY_RUN/KIS paper·안전장치값(MAX_WEIGHT_SINGLE 0.10/SECTOR 0.30) 무단변경 금지·부품/엔진은 버그판정시만 수정(의도 보존)·CODEMAP 수정시 동기화.
[자문 보정 ⛔] 자문 무비판 수용 금지. 자문은 우리 코드 모름(§9 내코드검증 참조). 예: throttle 새로 만들지 말고 H25 재활용 / capped-EW 유지 기조 / 정렬도로 매핑 최적화 금지(과적합).
[산물] 진단보고(코드 근거)+수정+self-test. 수정 후 run_multiasset.py --backtest 재측정으로 해당 축 개선 확인.
[stop] {이 단계}까지 하고 stop. 막히면 SendMessage로 supervisor에 보고(idle 금지).
[환경] Bash 전 export PATH="/c/Program Files/nodejs:$PATH". python=Python312 절대경로. Write 실패시 재Read후 재시도.
```
- 검증 teammate 프롬프트: "worker {N} 수정분을 독립 audit. (a)off=byte-identical (b)도메인 pytest 회귀(기준 200 passed) (c)run_multiasset --backtest 재측정으로 17축 개선 실확인 (d)worker claim 무비판수용 금지=raw 재현. 매핑표+불일치만 반환."

### 분담표 (파트 = 파일 경계, 충돌 회피)
> ★우선순위·임무 최종 = **§9 자문반영 재조정** 참조(W2 P0 코인분리+throttle / W3 P1 섹터 regime틸트 ⛔EW금지 / W6 측정정정 / W4 P2 한국 타깃3+quality / **W1 최하·임무변경=강도틸트 폐기→within-sleeve risk-weighted** / W5 데이터). 아래 표는 파트 경계 기준, 임무는 §9 우선.
| Worker | 전담 모듈 | 임무 | 우선순위 |
|---|---|---|---|
| **W1 선택** | stock/selection_pipeline·construction·selector·valuation·value_trigger | 저평가 비중차등(자문 Q4). capped-EW→틸트 정당성 검증 후 | P1 |
| ~~**W2 regime**~~ ✅**DONE(2026-06-08)** | core/brain/regime_classifier·regime_to_weights·macro_schema·indicator_event_correlation | C2/I1 완료: 절대 CPI 게이트(STAGFLATION_ABS_CPI_GATE=3.0)+SLOWDOWN 국면 신설→ -0.91→Slowdown-0.19/Stagflation+0.10, NAV4.395/OOS↑, adopted. ⑯ conf 추출(confidence_now) fix 완료. coin throttle(I1)=Overheat coin outlier는 R1 분리로 해소(별도 throttle 불요 판정). 상세=ledger §2 | ✅완료 |
| **W3 산업배분** | core/portfolio_decompose | I2 시총비례→수익정렬(동일가중/틸트, Q3) | P1 |
| **W4 한국선택** | stock/data(kr)·study-research/eq_kr | I3 kr fundamentals 공급→가치선택(Q5) | P1 |
| **W5 팩터데이터** | core/brain/fred_adapter·core/data/factor_returns | ⑬ VIXCLS vintage 결측(first_release fallback 등) | P2 |
| **W6 백테스트하네스** | scripts/run_multiasset.py | C1 측정정정(선택alpha=선택종목 vs 업종전체EW), ⑭ survivorship haircut, 거래비용 | P1 |

### 충돌·의존 주의
- W1(construction us/kr 공통) ↔ W4(kr 데이터 공급): 데이터/로직 분리, W4 fundamentals→W1 소비(약의존). 인터페이스 계약 선합의.
- W2(regime_classifier) ↔ W5(fred_adapter): 호출관계, 인터페이스 유지하면 직교.
- W6(run_multiasset)는 하네스 = W1~W5 결과 호출. 측정코드 단독 수정.

### audit (검증 teammate 작업 방식)
- **검증 teammate 1기**(opus 1m, 병목 시 2~3): 각 worker 수정분 회귀 audit.
  - off=byte-identical 불변식(레거시 run_agents 경로 무영향)
  - 도메인 pytest 회귀(직전 200 passed 기준)
  - run_multiasset.py --backtest 재측정(개선이 attribution 실제 개선했나 = 17축 재확인)
  - 독립 raw 재현(worker claim 무비판 수용 금지, AUDIT-GUIDE 정신)
- healer(메인)가 audit FAIL 수신 → 직접 수정 → 재검증.

## §5 파일 inventory (절대경로 D:/projects/Inv/)

- **측정 코드**: `scripts/run_multiasset.py` run_backtest(L614~) = 17축 로깅. 핵심 누적기: `sleeve_contrib`/`sleeve_ret_hist`(③) `ind_w_hist`(④) `ind_ret_hist`/`ind_sel_alpha`(⑤) `reg_sleeve_ret`/`reg_sleeve_w`(①②) `conc_hist`(⑦) `gate_rej_reasons`(⑥) `judge_atten_all`(⑨) `port_seq`(Sharpe). `_gate_judge_filter`=4-tuple 반환(out/n_rej/rej_rules/judge_atten).
- **종목집합 선정 코드체인** (사용자 질문 박제): `_bt_us_picks`(run_multiasset) → `construction.build_sleeve_decisions`(ETF면 `_resolve_etf_routing`→RepresentativeETF/EwBasket 직행 / 아니면) → `selection_pipeline.build_universe_candidates` → `cross_sectional_selection.select_cross_sectional`(:335). 단계: ①`_bt_metric_panel`(pbr/ev_ebitda/ep_yield/net_issuance) ②`signs_for`+`load_sleeve_weights`(yaml)+`interactions_for`(부호·가중·상호작용) ③`composite_cheapness_z`(:264, 지표별 robust z→가중합성=cheapness_z 높을수록 쌈) ④`_eligible`(:391, microcap floor)+`make_trap_veto`(value_stock DCF 잔차≈0=밸류트랩 거부) ⑤`select_cross_sectional` **top_k=10** 상위+no-trade band(top_k_exit=30 히스테리시스)+**`_capped_equal_weight`**(:452, 종목10%/섹터30% cap) ⑥`StockTrack.generate_candidate`→`value_trigger`(2단 가격-10%∧갭25%→trap), ★백테스트=`deterministic_no_llm`+`bypass_gate1`로 가격gate·LLM trap **우회**(H22 미래오염차단)=cheapness 선택만 작동 ⑦`valuation.value_stock`(bear/base/bull DCF+EV/EBITDA+RIM). **결론**: 종목집합=cheapness_z 상위 10 ∩ eligible, 비중=**capped-EW**(저평가는 *고르는* 데만, *비중차등* 없음=C1 alpha0 설계근거).
- **측정 결과**: `.p4-backtest-multiaxis.log`(최신 17축), `.p4-backtest-r15on.log`(regime 차등 검증), 구버전(.p4-backtest-{fredkey,attribution,5layer}.log = 참고).
- **수정 대상**: §4 분담표 모듈.
- **자문**: `/tmp/inv-consult-brief.txt`(R1 브리핑), `~/.claude/.gemini-web-last.md`·`~/.claude/.claude-web-basic-last.md`(응답 로그).

## §6 미해결·실패 (삽질 방지)

- **C1 측정 정정 미완**: 선택 alpha를 "선택종목 vs 업종 전체 universe EW"로 재계산해야 진짜 종목선택 가치 보임(현재는 통과 vs 통과EW tautology). 업종 전체 universe 수익 추적 추가 필요(W6).
- **C2 coin outlier 미제거**: regime corr -0.79가 coin 때문인지 매핑 때문인지 미판정. coin 제외 재측정 필수(W2).
- **VIXCLS vintage**: ALFRED가 3864 vintage 요청(1776~9999)→2000 한도 초과. first_release 모드면 될 가능성(W5 확인).
- **conf=?**: mv.regime의 confidence 속성 추출 실패. RegimeEstimate 구조 확인 필요(W2).
- **거래비용**: 현재 run_backtest에 거래비용/turnover 미반영 의심(확인 필요, W6).
- **ctx**: 본 세션 long-mode ON2(750k). teammate 6기 조종은 메인 ctx 부담 → 압축 경계 시 본 핸드오프로 재개.

## §7 불변식 (전 worker·검증 공통)
off=byte-identical(레거시 run_agents 무영향) / push·go-live·실주문 미접촉 / DRY_RUN·KIS paper / 안전장치값(MAX_WEIGHT_SINGLE 0.10·MAX_WEIGHT_SECTOR 0.30) 무단변경 금지 / 부품·엔진 무단변경(버그 판정 시만 수정, 왜곡 금지) / 각 산물=진단보고+수정+self-test / CODEMAP 수정 후 동기화.

## §9 자문종합 (R1 수렴 — gemini+claude 병렬)

> raw 포인터: `~/.claude/.gemini-web-last.md`(GeminiPro) / `~/.claude/.claude-web-basic-last.md`(Opus 4.8 High, session https://claude.ai/chat/20c92174). 브리핑=`/tmp/inv-consult-brief.txt`.

### 3자 수렴 결론 (로컬+Gemini+Claude 거의 일치)

| Q | 수렴 결론 | 우선순위 |
|---|---|---|
| **Q1 코인 분리** | 코인을 regime 배분서 **제외 + 코인-native throttle만**. ★Claude 핵심: throttle을 거시 overheat에 걸면 거시의존 뒷문 재유입 → **코인 자신의 상태**(실현변동성·드로다운·펀딩/김프)에 걸어야. throttle=알파 아닌 드로다운 오버레이로 분류. | **1순위·최저위험** |
| **Q2 정렬 음수** | coin outlier가 주범(수익분산 10~50배 → 횡단면 corr 지배) → **코인 제외 재측정 선행**. ★양쪽 경고: 정렬도(corr)로 매핑 **최적화 금지**(과적합). -0.79는 **2022 단일 에피소드** 의심. 평가지표를 정렬도→**조건부 하방·드로다운 기여**로 교체. 손보면 **듀레이션 부호만 타깃**(2022 주식-채권 상관 +전환). latency(nowcast vs ex-post) 점검. | 3순위(대부분 #1로 해소) |
| **Q3 섹터 배분** | 시총비례 **폐기**. ★Claude 핵심: 진짜 버그=**regime 뷰가 섹터층에 도달 못함**(시총비례=벤치 섹터구성 사는 것=섹터층 무동작). **regime-conditional 틸트**가 정답(Recovery→경기민감/금융 OW, Stagflation→에너지/필수/헬스 OW). ⛔**EW 채택 금지**(소형주 베팅+2017-26 risk-on 표본의존=과적합). anchor=시총비례, regime+섹터모멘텀으로 틸트(모멘텀 OOS robust, 상대밸류 약하게). | **2순위·높음** |
| **Q4 종목 강도틸트** | ★**반대**(양쪽). 최저밸류=distress/밸류트랩 밀도 최고+소표본 과적합. **강도는 이름 단위 비중 아닌 sleeve-conviction 층으로**. within-sleeve는 **risk-weighted(inverse-vol)** 가 강도틸트보다 Sharpe 안정. 틸트 쓰면 K 큰 sleeve(경기민감~60)만+EW편차 상한+트랩veto 상류. | **최하** |
| **Q5 한국** | ★**타깃 도입**(전면 비추). 본인 선행연구=12 sleeve 중 9개 within-industry ρ weak → 상한 박힘. **ρ 살아있는 ~3 sleeve만** 개별선택, 나머지 ETF/EW. 한국 신호=단순 cheapness 아닌 **cheapness×quality(또는 payout)**(거버넌스 영구디스카운트 트랩 거름, 미국 DEF-2 동형). STT 거래비용·±30%·숏제약 허들. | 4순위·타깃한정 |

### ★내 코드기반 비판 (자문 무비판 수용 금지 — 자문은 우리 코드 상세 모름, 아이디어만 차용)
자문 Q1~Q5를 우리 코드/CODEMAP에 매핑 검증한 결과, **자문이 모르는 사실 3개**:
- **Q3(섹터 regime틸트) — 코드로 입증·최우선 동의**: `portfolio_decompose.decompose_weight`는 인자가 `method="cap"|"equal"`뿐 **regime 입력 자체가 없다**(시총비례/균등만). 자문 "regime 뷰가 섹터층에 도달 못함"이 코드로 확정. 이건 과적합 아닌 **순수 배선 갭** → W3 = decompose_weight에 regime 인자+틸트 신규(SLEEVE_AGG와 구분). **자문+코드 일치, 가장 확실한 구조 개선**.
- **Q1(코인 throttle) — 자문이 모르는 기존 인프라**: `coin_sizing.py`에 **H25 throttle 이미 존재**(COIN_CORR_THRESHOLD 0.75 / BTC_CRISIS_CAP 0.40, 상관 과열→BTC cap). 단 (a)상관 기반(자문이 권한 실현변동성/드로다운과 부분만 일치) (b)**멀티코인 HRP 전용**(단일 BTC엔 부분적) (c)**호출처0 dead**(CODEMAP:125, 백테스트 coin=BTC passive라 미연결). → W2 = **무에서 throttle 만들지 말고 H25 재활용·확장** + 백테스트 coin을 regime weight서 분리. 자문은 H25 존재를 모르고 "새로 만들라" 한 것.
- **Q4(inverse-vol) — 신중, 현행 유지가 안전**: `cross_sectional_selection`은 `_capped_equal_weight`만(inverse-vol 없음). 자문도 강도틸트 **반대**+inverse-vol은 "검토" 수준. 내 판단: capped-EW 유지가 안전(소표본 과적합 회피), inverse-vol 도입도 신중. **최하 우선**.
- **Q2/Q5 — 코드 미확인, W2/W4 진단 위임**: `regime_to_weights` 듀레이션 부호 / `sleeve_signals` kr quality 지표는 본 세션 코드 미확인. 단 자문 방향(정렬도 최적화 금지·2022 단일점·한국 ρ weak)은 우리 `small-n-rigor` rule·indicator-ledger 선행연구와 정합 → 무비판 아닌 정합 확인됨.

**3자 수렴 = 자문 아이디어 + 내 코드검증**: Q3(배선갭 확정)·Q1(H25 재활용)·Q4(capped-EW 유지)는 코드 근거로 자문 수정/보강. Q2·Q5는 정합 확인 후 worker 진단.

### ★자문 반영 우선순위 재조정 (§4 분담표 갱신 근거)
1. **W2 코인분리+throttle+정렬진단** = P0(자문 1순위). 코인 regime 제외 + 코인-native vol throttle + 코인제외 regime-에피소드별 정렬 분해(2022 단일점 여부=R2 분기점).
2. **W3 섹터 regime-conditional 틸트** = P1(자문 2순위). ⛔EW 금지, regime뷰가 portfolio_decompose 섹터층에 도달하게. anchor 시총비례+모멘텀 틸트.
3. **W6 C1 측정정정** = 측정 신뢰(선택 vs 업종전체 EW) + survivorship.
4. **W4 한국 타깃** = P2. ρ 살아있는 3 sleeve만 + quality/payout 게이트.
5. **W1 종목비중** = ★임무 변경: 강도틸트 대신 **within-sleeve risk-weighted(inverse-vol) 검토** + 강도는 sleeve-conviction층(자문 Q4 반대 반영).
6. **W5 VIXCLS** = 데이터.

### R2/R3 분기 (ctx 마무리로 다음 단계 위임)
- R1에서 방향 강수렴 → 형식적 R2/R3 대신, **W2가 "코인 제외 regime-에피소드별 정렬 분해" 실측 후** 그 표를 들고 재자문(Claude 명시 Round2 분기점). 데이터 의존이라 코드작업 선행. 핸드오프 재개 시 W2 실측→재자문.
- consult-raw 매핑: Q1~Q5 + 5우선순위 전 항목 → W1~W6 매핑 완료(누락 0). 정렬도 과적합 경고·throttle 분류·EW금지·강도 sleeve층·한국 quality게이트 = 각 worker 프롬프트 필수 박제.
