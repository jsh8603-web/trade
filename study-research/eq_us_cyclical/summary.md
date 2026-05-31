---
tags: [type/summary, domain/inv, study/eq_us_cyclical]
date: 2026-05-30
---

# eq_us_cyclical — 스터디 요약 (사람용)

> 산출 SSOT: `study_session.yaml` (7블록). 본 문서는 그 핵심 발견·결정·기각 사유 요약.

## 1. 자산군 정의
미국 경기민감주(US cyclical equity). GICS 11섹터 중 **Cons Disc(XLY) · Industrials(XLI) · Materials(XLB) · Energy(XLE) · Financials(XLF) + IT 일부(반도체 SOX = early-cycle 대표)**. Defensive(Staples/Utilities/HealthCare) 와 대비. 자산 scope = equity.us.

## 2. lens — "이 자산이 왜 오르내리나"
**P = M(rate, credit, dollar, sentiment) × E(GDP/산업생산 탄력 + operating·financial leverage).**
경기민감주의 본질은 **이익 레버리지**: 매출이 경기(ISM PMI·산업생산)에 고탄력, 고정비(operating leverage)+부채(financial leverage)가 사이클 진폭을 증폭. 같은 지표라도 **국면에 따라 신호 의미·가중이 달라진다** = R15 동적 가중의 본질.

### 보고서가 엮어 보는 관계도 (핵심 7)
1. ISM Mfg PMI > 50 → 경기민감 이익 모멘텀↑·EPS revision 상향(PMI 선행)
2. 10Y-2Y 커브 스티프닝·양전환 = early-cycle / 역전 = late-cycle 경고(12~18M 선행 침체)
3. DXY↓ → Materials·Energy·Industrials 마진↑ (dollar beta)
4. HY OAS 확대 → high-beta·고leverage 경기민감주 디레이팅(가장 먼저 무너짐)
5. 실질금리↑ → long-duration 고멀티플(반도체) 압박 / value 경기민감(은행) 상대 수혜 — rate_beta 부호 종목별 갈림
6. 유가↑ → Energy 수혜 vs 운송·항공·Cons Disc 비용압박 — 섹터 내 부호 상충 → industry 단위 분해 필수
7. Investment Clock: early(반도체/Cons Disc)→mid(Industrials/Financials)→late(Energy/Materials) 리더십 로테이션

## 3. ★데이터 대조 — lens 갱신 (작업순서 3단계 flag)
`data/fixtures/semiconductor_panel_v1.parquet` (40 firms × 36Q, 합성 픽스처) 로 lens 가설 대조. 상세 = `raw/data-analysis-semiconductor-panel.md`.

### (확신) flag — lens·weight 강화
- **valuation 압도**: val_gap(저평가도) Rank-IC = **+0.658**, multiple IC = -0.427 → 경기민감 반도체 최강 알파. → fwd_ep base_weight 0.22 → **0.28**.
- **peak_trap 확정**: peak 국면 val_gap≈0 + 유망비율 **0%** ("정점엔 살 게 없다"). trough 에서 val_gap=1.25 + 유망비율 0.40 (저평가+유망 집중). → trough valuation 가중 추가↑, **peak 신규진입 deadzone 강화**(weight_card.floor 를 regime별로 확장).
- **과열 역신호**: inventory_qoq·capex_to_rev IC = **-0.31** (재고/투자 과열 = late-cycle 경계). → capex_to_rev 를 음부호 지표로 신규 등록.
- **mean-reversion 메커니즘**: val_gap → Δmultiple(t+1) IC = **+0.385** = 저평가의 멀티플 회복이 valuation 알파의 인과 채널.

### (거부·수정) flag — 약화
- **momentum 약함**: rev_growth/price_mom 직접 알파 IC = +0.05 → price_mom base_weight 0.18 → **0.12**, regime modulate(early-cycle만) 로 한정.
- **book_to_bill 선행성 약함**(IC +0.07, 통념 대비 약함) → 합성 픽스처 한계 가능성. **실 EDGAR + ETF holdings 적재 후 재검증**까지 prior_strength 하향.

## 3.5 블록3 relationships — 데이터 검증 (가능 항목만)
블록3 5개 관계 가설 각각의 검증 가능성과 결과:

| # | 관계 가설 | prior | 검증 가능? | 검증 결과 (semiconductor panel) | flag |
|---|---|---|---|---|---|
| R1 | ism_pmi_sensitivity → fwd_eps_momentum (direct, lagged, pos) | 0.60 | ❌ ISM 시계열 부재 | 미검증 | 라이브 재검증 (FRED NAPM 적재 후) |
| R2 | credit_beta ↔ realized_vol (direct, contemp, pos) | 0.55 | ❌ HY OAS·종목벡터 부재 | 미검증 | 라이브 재검증 (FRED BAMLH0A0HYM2 + 가격) |
| R3 | dollar_beta ↔ oil_beta (common_cause via macro) | 0.30 | ❌ DXY·WTI·종목벡터 부재 | 미검증 | 라이브 재검증 (FxStore + Yahoo WTI) |
| R4 | rate_beta ↔ fwd_ep (direct, pos) | 0.50 | △ 약식만 | multiple ~ gross_margin Rank-IC = **+0.370** (rate 조건화 부재 → 직접효과 분리 불가) | △ 동조 방향 일치, 실 DGS10·종목벡터 적재 후 재검증 |
| R5 | operating_leverage → fwd_eps_momentum (direct, lagged, pos) | 0.50→**0.30 하향** | ✅ proxy 가능 | drv_gross_margin → t+1 drv_rev_growth IC = **+0.084 (약함)**, conditioning on book_to_bill 시 partial IC = **-0.013 (직접효과 사라짐)** | ★(거부 후보) flag — 합성 한계 + gross_margin 은 DOL proxy 일 뿐, 실 ΔEBIT/Δrev 측정 후 재검증 |

### regime conditional 검증 (R5)
| phase | margin → t+1 rev_growth IC | n |
|---|---|---|
| trough | -0.022 | 364 |
| mid | +0.055 | 571 |
| peak | +0.035 | 391 |

→ **모든 regime 에서 약함** = R5 regime-conditional 강세 가설도 미확인. (거부 후보) flag 강화.

### 결정
- R5 prior_strength 0.5 → **0.3 하향** (yaml 블록3 반영) + conditioning_set 에 book_to_bill 명시(직접효과 분리 시 더 약함을 반영).
- R1~R4 는 거시지표 부재로 본 분석 단계에서 검증 불가 — 블록5 confidence_hooks 가 라이브에서 측정 (블록6 collector 4건 적재 후).
- glasso force-include 화이트리스트 ≤4 후보에서 R5 제외(prior 0.3 → 미강제), R1·R2 는 라이브 측정 후 재선정.

상세 = `raw/data-analysis-semiconductor-panel.md` (block3 verification 섹션).

## 4. 코드 4단계 매핑 — 핵심 발견 3종
**(블록7 code_change_plan 9항목 전부 실코드 Read 후 정밀화 완료)**

1. **us_stock sleeve 기존재** (`regime_to_weights.py` SLEEVES) → **신규 sleeve 등록 불필요**(회귀 위험 회피). us_cyclical 은 us_stock sleeve 내 sub-panel, 종목 가중은 `weight_card.composed_weights(pi)` 보간(부록B).
2. **judge lens 주입 메커니즘 기구현** (`judge.py _qwen_accepts_lens / _call_qwen_with_lens`) → **신규 메커니즘 불필요**. 카드에 lens 정성필드 추가 + lens_prompt 공급 경로만 추가.
3. **id 규약 = `weight.equity.{regime}`** (`stock_track.py _resolve_weight_card`). 종목 세분화는 별도 id 네임스페이스(예: weight.equity.us_cyclical.{regime})보다 **기존 id 유지 + composed_weights(pi) 보간** 권장(_resolve_weight_card 변경 없음 = 무회귀).

## 5. 결정·기각 사유
- **종목 단위 독립학습 기각**: regime당 obs 부족(45 빠듯). 채택 = 부록B hierarchical pooling (w_global + δ_regime + δ_arch[early/mid/late cycle archetype] + ticker shrinkage via pi).
- **Block Matrix(거시+자산 한 행렬) 기각**: §8 자문 결론. 채택 = 조건부 모델(cglasso) + 거시 driver 4개(credit/real_rate/dollar/oil) named 채널, 나머지 regime 조건키.
- **momentum 중심 기각**: 데이터 IC +0.05 약함. 채택 = valuation 중심 + momentum 은 early-cycle regime modulate 한정.
- **id 네임스페이스 확장 기각**: _resolve_weight_card 동반수정 회귀 위험. 채택 = 기존 id 유지 + pi 보간.

## 6. 부족 자료 — main 에 별도 요청 (블록6)
1. **컨센서스 earnings revision breadth** (I/B/E/S 대체 무료: Yahoo/Finnhub estimate 또는 EDGAR 8-K 가이던스 파싱) — FINNHUB_API_KEY 무료티어.
2. **inventory/sales 재고사이클** — EDGAR 10-Q 재무제표 파싱 확장.
3. **ISM Manufacturing PMI 시계열(PIT)** — FRED NAPM/MANEMP 대체.
4. **GICS 정확 섹터·industry** — FinanceDatabase(MIT) loose-GICS + XLY/XLI/XLB/XLE/XLF ETF holdings.

## 7. 한계
⚠️ 본 분석은 합성 픽스처 1개에 기반. 실 EDGAR 펀더멘털 + 경기민감 유니버스(XLY/XLI/XLB/XLE/XLF 구성종목) forward return 으로 재검증 필요. **블록5 confidence_hooks (valuation_alpha_regime_conditional, peak_trap_no_entry) 가 라이브에서 이 IC 를 재측정 → 갱신 경로로 작동.**

## 8. main 인계 요청
- 블록7 코드 변경 9항목 production wiring (G1~G6 골격).
- 블록6 collector 4건 적재 (FINNHUB key 필요).
- yaml 블록4 weight_rules 의 base_weight·modulate_by 를 train_weights.py batch 인자로 주입.
