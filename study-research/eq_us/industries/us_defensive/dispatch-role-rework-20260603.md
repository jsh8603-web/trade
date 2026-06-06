# dispatch role — us_defensive 재작업 (S1 리서치 우선 → sector-neutral 측정, Opus 1m teammate)

> 너 = **Opus 1m teammate** (하네스2wf transport 참고, 실제는 TeamCreate+Agent teammate 모드).
> team-lead = supervisor(메인 btn-button). 보고 = `SendMessage(to:"team-lead")`.
> 임무 = us_defensive sleeve **재작업** (asset_stable, XLP/XLU/XLV/XLC-mature 4 sub-sector).
> ★**순서 = S1 학술 리서치 먼저 → 측정(sector-neutral z + 방법 R2 4수정) → 게이트.** 속도보다 퀄리티.

## ★0-pre. us_cyclical pilot 핵심 발견 (반드시 선반영)
us_cyclical(먼저 완료된 pilot)에서 ★**방법 결함 발견·교정**:
- 기존 measure.py 의 `universe-demean z` = frame §M.7 "within-industry **peer-relative** sector-neutral z" 계약 **위반 버그**. multi-sector sleeve(여러 sub-sector 혼재)에서 sector 간 valuation 수준차가 신호를 희석.
- ★**sector-neutral z(sub-sector 내 peer-relative demean) 전환 시 family_1 BY 생존 0→8 회복** (us_cyclical pbr/ev_ebitda CONFIRMED).
- mechanism = within-sub-sector value(진짜 신호) + sub-sector-LEVEL value trap(부호 반대)이 섞여 universe-demean 이 희석 → sector-neutral 이 trap 제거.
- ★us_defensive 도 4 sub-sector(XLP/XLU/XLV/XLC) 혼재 = **동일 결함 가능성 높음** → sector-neutral z 정식 적용 후 재측정 의무.
- ★G-C hedge: sector-LEVEL trap magnitude 는 n_sector 작으면 over-claim 금지(방향만). sector당 종목수 small-n hedge 라벨.

## 0. 정독 (시작 전 필수, 순서대로)
1. `study-research/_dispatch-gates.md` — ★게이트 4종 = 완료 조건 (G-A 축이행 / G-B 재자문 / G-C 독립audit / G-D ledger)
2. `study-research/_ledger-guide.md` — ★ledger 2종 양식 (candidate-ledger + research-log)
3. `study-research/eq_us/.dispatch-us-sleeve-role.md` — 미국 sleeve 공통 계약 (§3 미국특화·§4 불변식)
4. `study-research/eq_us/direction.md` + `frame-v3-draft-industry-dispatch-20260603.md` §M(§M.7 line 267-269 sector-neutral 계약 + line 322 경고)
5. ★**us_cyclical 완성 산출**(양식 정답지): `industries/us_cyclical/{summary.yaml, 15axis-audit.md, raw-v3/measure.py(sector_z_decomposition + cs_z(secmap)), candidate-ledger.md, research-log.md}`
6. 기존 us_defensive: `industries/us_defensive/summary.yaml`(현 baseline) + `raw-v3/{collect,measure,measure_cross}.py` + `raw-v3/data/`
7. ★`.consult-us-method-briefing.md` + `.consult-us-method-R2.md` — 자문 R1+R2 = 측정 방법 수정 근거 (전망 = defensive 회복 예상)

## 1. ★S1 학술 리서치 우선 (섹터 시작 = 리서치 먼저, stock.md 6단계 S1)

★**측정에 바로 들어가지 말 것.** us_defensive(필수소비 XLP / 유틸 XLU / 헬스케어 XLV / 성숙통신 XLC-mature)에
**어떤 지표가 연관있는지** 관련 논문·증권사 리포트 리서치로 먼저 발굴.

- **방법**: `search-engine`(Gemini 2-Phase) 또는 WebSearch — "defensive/low-beta sector factor / bond-proxy equity / quality dividend anomaly / rate-duration sensitivity" 학술+실무.
- **발굴 대상**(기존 rev_1m/vol_60/real_rate 는 일부 — 누락 찾기): low-volatility/BAB, quality(QMJ·gross profitability), dividend yield, valuation(PER/PBR/EV-EBITDA — asset_stable 은 PER value 가능 = 한국 consumer/telecom 동형), earnings stability, rate-duration β(bond-proxy), credit regime(HY OAS/Baa-Aaa), short-term reversal.
- ★**peak-EPS 함정은 cyclical 특화** — defensive 는 EPS 안정 → PER value 가 정상 작동 가능(us_cyclical 과 반대 가설). 이 차이를 명시 검증.
- **산출**: `candidate-ledger.md` 초안(✅채택후보/⏳이연/❌미채택, 각 **출처 논문 명시**) + `theory-notes.md`(S1 학술 ground).
- ⛔ 자문·기존 summary 결론 복붙 금지 — 직접 문헌 조사. 이연/미채택 사유 박제.
- 리서치 결과 → 측정할 지표 목록 확정 → §2 진입. **§1 완료 시 team-lead 1차 보고**(발굴 목록).

## 2. measure.py 방법 수정 (sector-neutral z + 자문 R2 4수정) + 재측정 + 재판정

### ★수정 0. sector-neutral z 정식 (us_cyclical pilot 발견 = 최우선)
- valuation·cross-sectional z = **sub-sector(XLP/XLU/XLV/XLC) 내 peer-relative demean** (us_cyclical `cs_z(secmap)` 미러).
- `sector_z_decomposition`(universe-z vs sector-neutral-z vs sector-LEVEL-component) 검증 b 동일 산출 → 결함 여부 정량 입증.
- 단일산업 byte-identical 정합(INV_R15_WEIGHTS off).

### 수정 1. BY family 3분리 (m 팽창 차단)
- family_1 unconditional 예측 IC / family_2 regime-conditional gated(별 m) / family_3 driver β attribution(BY 제외)

### 수정 2. M_eff (Li-Ji eigenvalue)
- near-duplicate(horizon 강상관) → `M_eff = Σ_i [I(λ_i≥1) + (λ_i−⌊λ_i⌋)]`. family_1 BY threshold = M_eff 기준.

### 수정 3. eff_N 이중보정
- 시계열 eff_N≈T/h × 횡단면 N/(1+(N−1)ρ̄) — 둘 다 곱해 IC 검정·breadth-IR 양축.

### 수정 4. valuation EDGAR 수집 (★현 §10 = placeholder 미수집)
- us_cyclical `collect.py`(EDGAR 12 concept, filed-date PIT, dei shares fallback) 파이프라인 **재사용** → PER/PBR/EV-EBITDA sector-neutral 측정.
- asset_stable = EPS 안정 → ★PER value 가 cyclical 과 달리 작동하는지 직접 검증(가설 차이).

### 재판정 (★정직)
- 수정 → family_1 BY 재검정. 자문 전망 = defensive 회복 예상 → 회복하면 회복, 아니면 미생존 **정직 보고**.
- ★**G-B**: 재측정도 family_1 BY 생존 0 AND 최강 raw_p > threshold×2 → team-lead 보고 + 재자문 필요 신호(단정 ⛔금지).

## 3. 게이트 준수 (완료 조건 = _dispatch-gates.md)
- **G-A**: `15axis-audit.md` 15축(A~P) 3컬럼 + 6단계(S1~S6) + cross 3종 + ★A-4 sub-sector 부호 일관성표(cancel→슬리브 분리 / 개념차→sector-conditional). hard-fail B/C/D/I+M/N/O = 0.
- **G-B**: 약함 단정 전 team-lead 보고.
- **G-C**: S6 독립 audit = team-lead 별도 세션 dispatch. 너는 self-audit 초안까지(15axis 하단 ★G-C 섹션 비워둠).
- **G-D**: `candidate-ledger.md` + `research-log.md`(막힘·해결·환경함정 시계열).

## 4. 불변식 (위반 금지)
- ⛔ 합성·시뮬 금지 — 실 yfinance/EDGAR/FRED PIT. 부재 = collector_plan + INSUFFICIENT.
- ⛔ 점추정 prior 박제 금지 — 분포+CI+게이트, small-n hedge.
- ⛔ go-live·실주문·push 미접촉. supervisor 몫(조립/Σ_signal/RegimeGlasso/DY) 안 함.
- ★데이터 fetch = **foreground+incremental save**(background 15min+ 미유지, sleep 0.15). INV_R15_WEIGHTS off = byte-identical.

## 5. 산출
- `candidate-ledger.md` + `theory-notes.md`(§1) / `research-log.md`(G-D)
- `raw-v3/measure.py` 수정(sector-neutral) + `collect.py`(EDGAR valuation) + `validation-metrics-v3.json` 재생성 / `summary.yaml` 갱신 / `15axis-audit.md`(G-A 3컬럼 + ★G-C 섹션 비워둠)

## 6. 보고
- 막힘·질문 = 즉시 `SendMessage(to:"team-lead")`. 데이터 막힘 = foreground 동기.
- ★**§1 리서치 완료 시 1차 보고**(발굴 지표 목록 + candidate-ledger 초안) → team-lead 확인 후 §2 진입.
- 완료 = 전 산출물 + 재측정(family_1 BY 생존 + sector_z_decomposition + M_eff + eff_N 전후 t) + verdict → SendMessage + task completed.
- ⛔ 텍스트 출력은 team-lead 에 안 보임 — 반드시 SendMessage.
