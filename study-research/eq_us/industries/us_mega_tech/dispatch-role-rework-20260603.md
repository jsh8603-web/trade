# dispatch role — us_mega_tech 재작업 (S1 리서치 우선 → basket-level 측정, Opus 1m teammate)

> 너 = **Opus 1m teammate** (하네스2wf transport 참고, 실제는 TeamCreate+Agent teammate 모드).
> team-lead = supervisor(메인 btn-button). 보고 = `SendMessage(to:"team-lead")`.
> 임무 = us_mega_tech sleeve **재작업** (compounder, Mag7+ 11종 custom basket: Mag7+AVGO/AMD/ORCL/ASML).
> ★**순서 = S1 학술 리서치 먼저 → 측정(자문 수정4 basket화 + 방법 R2 수정) → 게이트.** 속도보다 퀄리티.

## ★0-pre. us_cyclical pilot 발견 + ★mega_tech 특수성 (반드시 선반영)
- us_cyclical pilot 발견 = universe-demean → **sector-neutral z** 전환으로 BY 0→8 회복.
- ★단 **us_mega_tech 는 sector-neutral 적용 불가** = 단일 archetype(compounder) basket = sub-sector demean 할 peer 구조 없음(11종 모두 같은 mega-tech 그룹).
- ★대신 **자문 R2 수정4 = basket화**: N=11 cross-sectional z 의 통계 신뢰성 의문(small-basket) → **basket-level time-series signal(timing/factor exposure)** 우선 + cross-sectional 은 small-basket hedge 강하게 병기.
- ★us_cyclical 에서 가져올 것 = (1) family BY 3분리 (2) M_eff (3) eff_N 이중보정 (4) EDGAR PIT collect.py 파이프라인 (5) small-n hedge 양식. **sector-neutral z 만 비적용**(이유 명시).

## 0. 정독 (시작 전 필수, 순서대로)
1. `study-research/_dispatch-gates.md` — ★게이트 4종 = 완료 조건
2. `study-research/_ledger-guide.md` — ★ledger 2종 양식
3. `study-research/eq_us/.dispatch-us-sleeve-role.md` — 미국 sleeve 공통 계약
4. `study-research/eq_us/direction.md` + `frame-v3-draft-industry-dispatch-20260603.md` §M + §M.12(eff_N/breadth-IR/magnitude haircut = small-basket 핵심)
5. ★us_cyclical 완성 산출(양식 정답지): `industries/us_cyclical/{summary.yaml, 15axis-audit.md, raw-v3/{collect,measure}.py, candidate-ledger.md, research-log.md}`
6. 기존 us_mega_tech: `industries/us_mega_tech/summary.yaml`(현 baseline = vol_60 +0.241 dominant, n=11 basket, reflexivity H9) + `raw-v3/` + `round-N.md`
7. ★`.consult-us-method-briefing.md` + `.consult-us-method-R2.md` — 자문 R1+R2 (★수정4 basket화 근거 + mega_tech 회복 전망)

## 1. ★S1 학술 리서치 우선

★**측정에 바로 들어가지 말 것.** us_mega_tech(Mag7+AVGO/AMD/ORCL/ASML, compounder)에
**어떤 지표가 연관있는지** 관련 논문·증권사 리포트 리서치로 먼저 발굴.

- **방법**: `search-engine`(Gemini 2-Phase) 또는 WebSearch — "mega-cap growth factor / quality compounder / duration-equity rate sensitivity / AI capex supply chain / reflexivity concentration risk" 학술+실무.
- **발굴 대상**(기존 vol_60/momentum 는 일부): quality-lowvol, fwd EPS growth(compounder primary, ★PER value 아님=expensive_trap), momentum/growth persistence, duration/real-rate β(고duration growth), VIX/risk-on β, AI capex supply-chain(NVDA→hyperscaler), reflexivity/concentration(intra-basket corr, breadth).
- ★**expensive_trap 가설**: 고PER 정상 = value premium 없음(us_cyclical/defensive 와 반대). PER value 무신호를 직접 검증.
- ★**basket-level vs cross-sectional**: N=11 은 cross-sectional rank-IC 통계력 약 → basket-level factor timing(저변동 quality·duration·risk-on) 우선. S1 에서 어떤 신호가 basket-level 로 의미있는지 발굴.
- **산출**: `candidate-ledger.md` 초안 + `theory-notes.md`(S1 ground). 출처 박제, 이연/미채택 사유 박제. ⛔ 복붙 금지.
- 리서치 결과 → 측정 목록 확정 → §2 진입. **§1 완료 시 team-lead 1차 보고**.

## 2. measure 방법 수정 (자문 R2 수정4 basket화 + 나머지 3수정) + 재측정 + 재판정

### ★수정 4(우선). basket화 = N=11 cross-sectional 폐기/보조 + basket-level
- **basket-level time-series**: basket 가중 factor exposure(저변동 quality·duration β·VIX β·momentum) 의 시계열 timing 신호 — cross-asset 비교는 basket-level.
- cross-sectional rank-IC 는 ★small-basket(N=11) hedge 강하게 병기(breadth-IR + magnitude haircut, §M.12). 단독 verdict 금지.
- ⛔ sector-neutral z 비적용(단일 archetype, peer 구조 없음) — 이유를 15axis G-A.5 에 명시.

### 수정 1. BY family 3분리 / 수정 2. M_eff(Li-Ji) / 수정 3. eff_N 이중보정
- us_cyclical 동일. ★단 small-basket 이라 eff_N·breadth-IR 가 핵심(degenerate 강등 민감).

### valuation EDGAR (보조)
- us_cyclical collect.py(EDGAR PIT, dei fallback) 재사용 → PER/PBR/fwd growth proxy. ★expensive_trap 검증(PER 무신호 정상).

### reflexivity monitor (H9 유지)
- intra-basket 60d corr + breadth(EW vs cap-weight spread) = 정점 risk monitor(현 corr 0.355<0.70 = 정점 아님). 신호 아닌 risk overlay.

### 재판정 (★정직)
- basket-level 신호 BY/유의 재검정. 자문 전망 = mega_tech 회복 예상 → 회복하면 회복, 아니면 정직.
- ★**G-B**: 재측정도 유의 신호 0 AND 최강 raw_p > threshold×2 → team-lead 보고 + 재자문 신호(단정 ⛔금지).

## 3. 게이트 준수 (완료 조건 = _dispatch-gates.md)
- **G-A**: `15axis-audit.md` 15축 3컬럼 + 6단계 + cross 3종(★구조 supply-chain = AI capex→Mag7 = mega_tech 핵심 영역, skip 아님) + ★A-4(basket 단일 archetype = sub-sector 부호 N/A, 사유 명시). hard-fail B/C/D/I+M/N/O = 0.
- **G-B/G-C/G-D**: us_cyclical 동일. self-audit 초안까지(15axis 하단 ★G-C 비워둠) + ledger 2종.

## 4. 불변식 (위반 금지)
- ⛔ 합성·시뮬 금지 — 실 yfinance/EDGAR/FRED PIT. 부재 = collector_plan + INSUFFICIENT.
- ⛔ 점추정 prior 박제 금지 — 분포+CI+게이트, ★small-basket(N=11) hedge 강. magnitude haircut.
- ⛔ go-live·실주문·push 미접촉. supervisor 몫 안 함.
- ★데이터 fetch = foreground+incremental. INV_R15_WEIGHTS off = byte-identical.

## 5. 산출
- `candidate-ledger.md` + `theory-notes.md`(§1) / `research-log.md`(G-D)
- `raw-v3/measure*.py` 수정(basket-level + cross-sectional hedge) + `validation-metrics-v3.json` 재생성 / `summary.yaml` 갱신 / `15axis-audit.md`(G-A 3컬럼 + ★G-C 비워둠)

## 6. 보고
- 막힘·질문 = 즉시 `SendMessage(to:"team-lead")`. 데이터 막힘 = foreground 동기.
- ★**§1 리서치 완료 시 1차 보고**(발굴 목록 + candidate-ledger 초안) → team-lead 확인 후 §2 진입.
- 완료 = 전 산출물 + 재측정(basket-level 신호 + BY + M_eff + eff_N·breadth-IR 전후) + verdict → SendMessage + task completed.
- ⛔ 텍스트 출력은 team-lead 에 안 보임 — 반드시 SendMessage.
