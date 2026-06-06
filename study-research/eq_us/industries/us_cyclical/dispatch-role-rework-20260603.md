# dispatch role — us_cyclical 재작업 (S1 리서치 우선 → 측정, Opus 1m teammate)

> 너 = **Opus 1m teammate** (하네스2wf transport 참고, 실제는 TeamCreate+Agent teammate 모드).
> team-lead = supervisor(메인 btn-button). 보고 = `SendMessage(to:"team-lead")`.
> 임무 = us_cyclical sleeve **재작업**. 현 baseline = TENTATIVE / **BY 생존 0**.
> ★**순서 = S1 학술 리서치(지표 연관성 발굴) 먼저 → 측정(방법 R2 수정) → 게이트.** 속도보다 퀄리티.

## 0. 정독 (시작 전 필수, 순서대로)
1. `study-research/_dispatch-gates.md` — ★게이트 4종 = 완료 조건 (G-A 축이행 / G-B 재자문 / G-C 독립audit / G-D ledger)
2. `study-research/_ledger-guide.md` — ★ledger 2종 양식 (candidate-ledger + research-log)
3. `study-research/eq_us/.dispatch-us-sleeve-role.md` — 미국 sleeve 공통 계약 (§3 미국특화·§4 불변식)
4. `study-research/eq_us/direction.md` + `frame-v3-draft-industry-dispatch-20260603.md` §M — frame v3 측정 15종·cross
5. 기존 us_cyclical: `industries/us_cyclical/summary.yaml`(현 baseline) + `raw-v3/{collect,measure}.py` + `raw-v3/data/`
6. ★`.consult-us-method-briefing.md` + `.consult-us-method-R2.md` — 자문 R1+R2 = 측정 방법 수정 근거

## 1. ★S1 학술 리서치 우선 (섹터 시작 = 리서치 먼저, stock.md 6단계 S1)

★**측정에 바로 들어가지 말 것.** us_cyclical(반도체 SOXX / 소재 XLB / 산업재 XLI / 에너지 XLE / 금융 XLF)에
**어떤 지표가 연관있는지** 관련 논문·증권사 리포트 리서치로 먼저 발굴한다.

- **방법**: `search-engine`(Gemini 2-Phase) 또는 WebSearch — "cyclical sector factor / equity anomaly / sector rotation predictor" 학술 + 실무. 1차 문헌 ground.
- **발굴 대상**(기존 per_z/pbr_z/vol/mom 은 일부일 뿐 — 누락 지표 찾기): valuation(PER/PBR/EV-EBITDA), earnings revision breadth(ERB, direction R1 alpha 1순위), capex cycle, credit cycle(HY OAS), inventory-to-sales, PMI/ISM, dollar β, momentum/reversal, quality(QMJ/BAB), 변동성 프리미엄 등.
- **산출**: `candidate-ledger.md` 초안 (✅채택후보 / ⏳이연 / ❌미채택, 각 **출처 논문·리포트 명시**) + `theory-notes.md`(S1 학술 ground).
- ⛔ 자문·기존 summary 결론 **복붙 금지** — 직접 문헌 조사. 이연/미채택 사유도 박제.
- 이 리서치 결과로 **측정할 지표 목록 확정** → §2 측정 진입.

## 2. measure.py 방법 4수정 (자문 R2 수렴) + 재측정 + 재판정

§1에서 확정한 지표를 측정. 단 현 BY 생존 0 = 자문 R2 진단 "방법 결함 절반" → 아래 4수정 선반영:

### 수정 1. BY family 3분리 (m 팽창 차단)
- **family_1** unconditional 예측 IC (1차 discovery) / **family_2** regime-conditional gated (2차, 별도 m) / **family_3** driver β attribution (BY family 완전 제외 — 검정 아님)
- ⛔ 셋 한 family 묶음 = over-correction (현 m=20 오염)

### 수정 2. M_eff (effective number of tests)
- near-duplicate(per_z 3M/12M/24M 강상관) → raw count 대신 Li-Ji/Galwey eigenvalue: `M_eff = Σ_i [I(λ_i≥1) + (λ_i − ⌊λ_i⌋)]`
- family_1 BY threshold = M_eff 기준

### 수정 3. eff_N 이중보정 (현재 하나만/혼용 = 왜곡)
- 시계열 eff_N ≈ T/h × 횡단면 eff_N = N/(1+(N−1)ρ̄) — **둘 다 곱해** IC 검정·breadth-IR 양축
- breadth-IR = IC·√(유효 breadth × eff_N), breadth=count(60) 대신 유효 breadth

### 수정 4. (basket화 = mega_tech 전용. cyclical 60종 = cross-sectional 유효 유지)

### 재판정 (★정직)
- 4수정 → family_1 BY 재검정. 자문 전망 = cyclical 본질 약함 → 미생존 유지 **가능**. 회복하면 회복, 아니면 미생존 **정직 보고**.
- ★**G-B**: 재측정도 family_1 BY 생존 0 AND 최강 raw_p > threshold×2 → team-lead 보고 + 재자문 필요 신호 (단정 ⛔금지).

## 3. 게이트 준수 (완료 조건 = _dispatch-gates.md)
- **G-A**: `15axis-audit.md` 15축(A~P) 3컬럼(① 적용 ② 측정법·경로 ③ 결과) + 6단계(S1~S6) 경로 + cross 3종 — "축 이행" 입증. hard-fail B/C/D/I+M/N/O = 0.
- **G-B**: 약함 단정 전 team-lead 보고.
- **G-C**: S6 독립 audit = team-lead가 별도 세션 dispatch (만든사람≠감사자). 너는 self-audit 초안까지.
- **G-D**: `candidate-ledger.md` + `research-log.md` (research-log = ★막힘·해결·환경함정 시계열, 삽질 방지).

## 4. 불변식 (위반 금지)
- ⛔ 합성·시뮬 금지 — 실 yfinance/EDGAR/FRED PIT. 부재 = collector_plan + INSUFFICIENT.
- ⛔ 점추정 prior 박제 금지 — 분포+CI+게이트, small-n hedge.
- ⛔ go-live·실주문·push 미접촉. supervisor 몫(조립/Σ_signal/RegimeGlasso/DY/construction) 안 함.
- ★데이터 fetch = **foreground+incremental save**(background 15min+ 미유지 교훈, sleep 0.15). INV_R15_WEIGHTS off = byte-identical.

## 5. 산출
- `candidate-ledger.md` + `theory-notes.md` (§1 리서치) / `research-log.md` (G-D)
- `raw-v3/measure.py` 수정 + `validation-metrics-v3.json` 재생성 / `summary.yaml` 갱신(family별 BY 결과) / `15axis-audit.md`(G-A 3컬럼)

## 6. 보고
- 막힘·질문 = 즉시 `SendMessage(to:"team-lead")`. 데이터 막힘 = foreground 동기.
- 단계 보고: ★**§1 리서치 완료 시 1차 보고**(발굴 지표 목록 + candidate-ledger 초안) → team-lead 확인 후 §2 측정 진입.
- 완료 = 전 산출물 + 재측정 결과(family_1 BY 생존 + M_eff 값 + eff_N 보정 전후 t) + verdict → SendMessage + task completed.
