---
tags: [type/candidate-ledger, domain/equity, sector/bio, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 bio 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: round-1.md(2026-05-30) + theory-notes §6 부호확약(2026-06-05) + validation-{metrics,valuation,conditional,oos}-v3.json + frame v3 §M.11~M.12
---

# bio(제약·바이오) 지표 후보 원장

> ★범위 = bio capsule 한정 (12산업 독립 ledger). round-1 가설 + v3 unconditional + ★conditional IC(2026-06-05) 흡수.
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED).
> ★핵심 한 줄: bio = event_driven(적자 26/38종 멀티플 무효). ★진짜 신호 = **conditional(외국인 순매도 flow_sell 국면 증폭)** = 반도체(KRW_weak)와 대조. unconditional 가격/valuation = OOS 약/반전. 생존편향 최악(임상실패 상폐 누락).

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| ★**cs_flow_sell_conditional** (외국인 순매도 국면) | conditional momentum/value | PARTIAL-conditional | ★dispatch 본체. flow_sell 국면 5신호 증폭(mom_6 -0.149/per_z -0.092/vol_60 -0.093). family_2 interaction mom_6 t=-2.90/mom_12_1 t=-2.92/per_z t=-2.29 유의. ★OOS 부호+magnitude 유지(IS -0.141→OOS -0.156). S5 역공격 3종 방어. ★단 cell n=18~20 underpowered + BY 미생존 + IS약→OOS강(regime shift tentative). source=validation-conditional-v3.json + validation-oos-v3.json |
| cs_lowvol (저변동성=임상risk) | low_volatility | PARTIAL→OOS약 | unconditional vol_60 IC -0.066 NW 유의(t=-3.02), block-boot CI 0배제, cap-weighted -0.107. ★OOS magnitude 붕괴(-0.119→-0.008) + ★생존편향 과대평가 우려. flow_sell conditional 에서 OOS 강화. source=validation-metrics-v3.json:vol_60__1M_PEAD |
| ★**family_2 interaction** (flow_sell × signal) | conditional | 유의(t<-2.3) | ★frame A-5 의무 충족. main 비유의인데 interaction 유의 = 신호 conditional(약함 아님). ★KRW_weak interaction 비유의 = bio 증폭축은 flow(반도체 KRW와 대조). pooled panel month-clustered SE. |
| ★**외국인flow regime** (ECOS 28d z) | regime 축 | 측정완료 | ECOS 802Y001/0030000 일별 → flow_sell/neutral/strong_buy. ★bio 핵심 증폭축으로 판명. (반도체와 동일 인프라 재사용) |
| ★**rate_overlay** (US 10Y 금리 duration) ★ROTATION | rotation/macro overlay | PASS-conditional | ★업종 OW/UW timing(종목 selection 별개). -(US 10Y Δ3M z) → bio 업종 forward. y_60d rho=+0.274 wc_p=0.018, OOS 부호유지, leave-2022 생존. growth long-duration 이론 입증. ★underpowered + IS약→OOS강. source=validation-rotation-composite-v3.json. ★v2 rotation FAIL/data-gate 뒤집음(v2=momentum만 봄) |
| ★**bio_global_overlay** (XBI/IBB 상대모멘텀) ★ROTATION | rotation/sector 전이 | PASS-conditional | 글로벌 바이오(XBI/SPY+IBB/NDX 상대모멘텀)→한국 bio 업종 OW. xbi_rel_mom y_20d +0.153 OOS 0.131→0.190 / ibb +0.124 OOS 0.080→0.178. 섹터 전이 이론. underpowered. source=validation-rotation-v3.json |

## ⏳ 이연 / data-gate (현 데이터 측정 불가 또는 통합단계)

| 후보 | 출처 | 상태 | unblock 조건 |
|---|---|---|---|
| ★**파이프라인/임상 단계** (event_driven primary) | theory §2.1 + archetype | ⏳ DATA-GATE | ★bio 진짜 신호 = 임상 phase/FDA 승인 binary. KFDA/clinicaltrials.gov monthly facet 부재(yearly만). 현 측정 = 변동성 proxy 까지. unblock = 임상 이벤트 DB |
| ★**PIT universe 멤버십** (delisted) | I축 생존편향 | ⏳ collector_plan high(최우선) | ★bio 최악. 현 FDR 스냅샷 = delisted 0종. 임상실패 상폐(코오롱티슈진/신라젠/헬릭스미스) 누락. unblock = KRX PIT 멤버십 |
| 종목레벨 외국인 flow | Grinblatt-Keloharju 2000 | ⏳ DATA-GATE | KRX 종목별 외국인 net buy = 인증 차단. flow_sell 증폭이 종목레벨이면 더 정밀. 현 = 시장레벨 regime(ECOS) |
| R&D 비용/매출 (적자 burn-rate) | theory §2.4 | ⏳ 후속 | DART 손익 R&D 항목 추가 fetch (현 데이터로 가능, 후속) |
| 2축 merge conditional (Macro×flow) | frame §M3 collapse | 36셀 full N≥24=0(단일축만) | supervisor 통합 또는 N 누적 |
| M_eff 통합 FDR | G-F §3 | naive m=105(pbr/per·mom 강상관) | supervisor 통합단계(M.7 분담) |
| family-neutralized IC (FF5/KR-factor) | frame §M5 | 산업=unconditional 까지 | 통합 supervisor |

## ❌ 미채택 / proxy 대체 / REJECTED

| 후보 | 사유 |
|---|---|
| ★unconditional momentum (mom_6/mom_12_1) | unconditional IC 비유의(BY 0). ★OOS 부호반전(mom_6 IS -0.055→OOS +0.009 artifact). = event_driven 정합(임상 binary dominant, 가격 momentum 무신호). flow_sell 국면서만 발현(conditional 채택). |
| ★unconditional pbr_z/per_z | unconditional OOS 부호반전(pbr IS -0.061→OOS +0.043, per IS -0.004→OOS +0.061 artifact). = 적자 신약 멀티플 왜곡 + regime shift. flow_sell 국면 conditional value 만 채택. |
| USDKRW dollar β (수출주 가설) | ★REJECTED — corr -0.035~+0.038 p>0.6(round-1 §3.1). 삼바/셀트리온 수출비중 높으나 forward hedge + event-driven valuation. ★KRW_weak interaction 도 비유의(반도체와 반대) = bio 증폭축은 flow. |
| HY OAS (risk-on/off) | INSUFFICIENT — BAMLH0A0HYM2 FRED 2023-05~(n=30월) N gate 미달. flow regime 으로 대체(risk-off proxy). |
| FDA approval cycle (월별) | TENTATIVE→미채택 — fda_yoy lag1 +0.188(p=0.023 raw) but Bonferroni 후 비유의 + OOS sign flip. monthly facet 데이터 한계. |
| customer-supplier momentum | ★skip — bio = 임상 binary 이벤트, supply-chain 무관(§D falsifier). battery/financial/consumer 동일 패턴. |
| 시총 가중 산업series timing | bio = 삼바/셀트리온 dominance. cross-sectional(peer-relative z) 이 본체. cap-weighted IC 는 점검용 병행. |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| cs_flow_sell_conditional | ★IS t 약(-1.26)→OOS t 강(-2.95) = "지속 신호"인가 "최근(2023+) regime shift 발현"인가. cell n<24 underpowered. | 차기 vintage(2026+) pristine OOS 에서 interaction t<-2 재현 시 승격. e-CUSUM 모니터(reject=부호반전). |
| cs_lowvol | ★생존편향 과대평가 — 상폐된 고변동성 임상실패 신약 누락이 IC 부풀렸나. OOS magnitude 붕괴. | PIT 멤버십(delisted 포함) 재측정 후 IC 재평가. delisted 포함 시 vol 신호 약화 예상. |
| per_z flow_sell conditional | 흑자 한정(적자 26/38 제외) value. 적자 신약 = 멀티플 무효 → 파이프라인 필요 | 임상/파이프라인 데이터 확보 후 적자 신약 별 신호 측정 |

## 🔄 flip-register (regime-conditional sign flip — ★pristine OOS 게이트, 현 vintage 확정 금지)

> regime별 부호반전 cell = in-sample only → flip-register 박제 + 차기 vintage pristine OOS 게이트. ⛔ flip을 신호로 채택 금지(OOS 전).

| flip cell | uncond → conditional 부호 | n / wc_p / status | 해석 (가설) | OOS 게이트 |
|---|---|---|---|---|
| mom_6 [flow_neutral] | (uncond -0.024) → 양(+0.013) | n=43 / powered | 평시 momentum 소멸/약반전 | OOS 누적 |
| per_z [KRW_neutral] | (uncond +0.027) → 양 강(+0.097) | n=37 / wc_p=0.045 | 원화중립 국면 高PER(성장) 우위? = value 반대 | OOS 누적(부호 반대 주의) |
| mom_12_1 [Slowdown] | 음 → 양(+0.074) | n=19 / underpowered | 수축국면 momentum continuation? | n<24 누적 |

★flip-register 원칙: 전부 in-sample/underpowered = ⛔현 vintage 확정 금지. ★단 flow_sell 증폭(채택분)은 OOS 부호유지로 flip 아님 = 별개.

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| memory | "bio 증폭축 = 외국인 순매도(flow_sell), 반도체(KRW_weak)와 대조. bio 고베타 성장주 → risk-off 차별매도 시 fundamental 분별력 회복" | 다음 cycle 자문 prior + 산업별 증폭축 차등 규칙 |
| memory | "bio unconditional 가격/valuation = OOS 부호반전(artifact). event_driven = 임상 binary dominant라 가격 momentum 무신호 = 정합. conditional(flow_sell)만 OOS 생존" | 동적가중 = unconditional 약 ≠ conditional 약 |
| memory | "★bio 생존편향 최악 = 임상실패 상폐(코오롱티슈진/신라젠/헬릭스미스) 누락 → 고변동성 회피(vol_60) 신호 과대평가. PIT 멤버십 최우선" | 생존편향 산업차 (bio = vol 신호 과대 위험) |
| observe-only | cs_flow_sell_conditional / cs_lowvol | underpowered + IS약→OOS강 → N 누적 + 차기 vintage pristine OOS 후 promotion |
| evt | ★"거래정지 좀비 carry-forward 누설(bio-audit 발견) = 거래정지 종목 직전종가 flat carry → forward +0.0000 IC 오염 + vol_60 오측정. mask_trading_halt(연속flat≥10일 NaN, reject≠missing) 후 재측정 = 결론 robust 불변" | ★promotion-log 자산화 후보(D축 정확성, 한국주식 공통 함정). 8 PASS 종목군 통합 시 점검 의무 |
| memory | "★한국주식 거래정지 carry-forward = IC/vol 오염원. KRX 직전종가 carry 를 valid 로 오인 = reject≠missing 위반. 연속 동일종가 run 탐지 NaN 마스킹 필수(bio 코오롱티슈진 47.8%/케어젠 19%)" | 다음 산업 measure 시 mask_trading_halt 선적용 |
| evt | (G-B 재자문 미발동 = family_2 interaction 살아있음 = "약함" 아님, supervisor skip 판정) | promotion-log ERROR 후보 아님 |
| pointer | "bio = conditional(flow_sell) 본체 + 파이프라인/PIT멤버십 collector_plan high. 다음 = 임상 이벤트 DB + delisted universe" | 다음 세션 SSOT 정독 우선순위 |

## ⚠️ G-B 재자문 트리거 점검 (dispatch §G-B)

- 조건 = BY 생존 0/m **AND** 최강 raw_p > 2×thresh.
- 현황: conditional family BY 생존 0/105, raw_p_min=0.0025(mom_12_1 KRW_weak y_60d). BY rank1 thresh≈0.00095 → 2×thresh≈0.0019. raw_p 0.0025 > 0.0019 = 트리거 조건 충족 가능성.
- ★단 **family_2 interaction 유의(t=-2.90)** = "신호 약함 아니라 conditional" = G-B "약함 단정" 부적합 쪽. flow_sell 국면 5신호 OOS 부호유지 + S5 방어 = conditional 살아있음.
- → 내 판정 = "약함" 아님 = G-B 자동자문 skip 정당(family_2 살린 후 판정, frame A-5). M_eff 통합(supervisor)에서 naive m 과대 보정 시 재평가. team-lead 최종 판단 대상.
