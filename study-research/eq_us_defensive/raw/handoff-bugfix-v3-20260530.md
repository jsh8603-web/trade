---
tags: [type/handoff, study/eq_us_defensive, phase/v3-bugfix]
date: 2026-05-30
ckpt: ckpt-202605302145:btn-DA
trigger: main 독립검증 verdict=Tier3 불충실 → 3 결함 보수 지시
---

# handoff v3 — eq_us_defensive 보수 작업 인계

## 마지막 결정

main 독립검증 보수 지시 수신 — **3 결함 v3 보수 진행 중**:

1. **H3 데이터 커버리지 위조급** — `raw/run_validation.py` classify_regime 의 KeyError → silent credit=False 처리로 pre-2023 280개월 'Normal' 오분류. HY OAS CSV 실제 표본 = 2023-05~2026-05 (37개월) 만. n=9 credit = 2023 단일 regime 잔여. parametric t p=0.0503 (경계미달), Bootstrap p=0.005 = 자기상관 무시 IID. LOO 5/9 → p>0.05 붕괴.
2. **M3 dollar regime-switch 과대 단정** — XLU β_dxy +0.57 (E3) vs -0.18 (E4) z=1.34 p_diff=0.18 비유의. E3 CI [-0.5, +1.6] 0 포함. 4중 XLV 만 p=0.013 (multiple comparison 무시).
3. **H1 spec/impl 부정합** — 가설 text = "predictive (향후 3M 선도수익)" 인데 코드 = same-day contemporaneous. predictive 재계산 시 -0.004 / -0.013 (p>0.3 붕괴).

## 다음 의도 (잔여 작업, 우선순위 순)

1. ★**rule 신규 작성** — `~/.claude/rules/empirical-claim-presentation.md` (정량 claim presentation rule: data coverage 일자 + sample n + spec/code 1:1 verify + autocorr 안전장치 + multiple comparison 보정)
2. **run_validation.py 수정** —
   - classify_regime: HY 누락 month 를 `regime='OutOfSample'` 별도 라벨 (silent credit=False 금지)
   - H1: forward 3M return 옵션 추가 (`use_forward_3m: bool` flag) → 두 결과 동시 출력
   - M3: Welch's t-test for β_dxy(E3) vs β_dxy(E4) gap + Bonferroni 보정
3. **validation-H1.md 수정** — verdict "★CONFIRMED 강력" → "contemporaneous co-movement CONFIRMED, predictive (forward 3M) FAILS"
4. **validation-H3.md 수정** — verdict "★REVERSED" → "BAB 판정불가 (37개월·실 위기표본 부재)" 격하. KeyError 버그 수정 시점 명시
5. **m3-macro-linkage.md 수정** — "M1 강력 확인·dollar 2배" → "비유의 방향성 힌트" + Welch z=1.34 p_diff=0.18 명시
6. **study_session.yaml v3** — 결함 위 calibrate 된 v2 의 base_weight·confidence_hooks 전면 재calibrate (H1 contemporaneous spec / H3 BAB 판정불가 / M3 dollar 힌트)
7. **promotion-log ERROR 검증** — rule edit 후 유사 시나리오 self-test
8. **main 보고** — v3 보수 완료

## 동기화 필요

- `~/.claude/memory/promotion-log.md` — ERROR-202605302130:btn-DA 이미 prepend 완료
- `~/.claude/rules/empirical-claim-presentation.md` — 신규 작성 필요 (자산화: rule)
- 본 handoff 의 ckpt 마커 = `ckpt-202605302145:btn-DA`

## 열어본 파일

### 작성·수정한 파일
- D:/projects/Inv/study-research/eq_us_defensive/study_session.yaml (v2, 328줄 — v3 재calibrate 대상)
- D:/projects/Inv/study-research/eq_us_defensive/direction.md (426줄, 2-1)
- D:/projects/Inv/study-research/eq_us_defensive/raw/run_validation.py (353줄, classify_regime KeyError 버그 수정 대상)
- D:/projects/Inv/study-research/eq_us_defensive/raw/m3_macro_linkage.py (198줄, Welch t-test 부착 대상)
- D:/projects/Inv/study-research/eq_us_defensive/raw/theory-notes.md (523줄, 2-2)
- D:/projects/Inv/study-research/eq_us_defensive/raw/validation-H1.md~H4.md (123~143줄, 결과 격하 대상)
- D:/projects/Inv/study-research/eq_us_defensive/raw/m3-macro-linkage.md (148줄, M4 factor seed)
- D:/projects/Inv/study-research/eq_us_defensive/raw/round-1.md~round-4.md (자문 raw)
- C:/Users/jsh86/.claude/memory/promotion-log.md (ERROR 5줄 prepend 완료)

### 참조
- D:/projects/Inv/STUDY-KIT.md (§2 v2 흐름)
- D:/projects/Inv/study-research/macro/study_session.yaml (macro 7축 framework)
- D:/projects/Inv/study-research/eq_us_cyclical/raw/run_validation.py (cyclical 정상 패턴 reference)

### archive
- ~/.claude/docs/archive/research-raw/eq_us_defensive-round{1,2,3,4}-20260530.txt (Gemini Pro 자문 전문)

## 외부 자문 결과 (R1~R4 Gemini Pro)

R1 학술 17 ref / R2 검증 방법론 (regime axis + lag + rolling p.corr + 2단계 정규화) / R3 가설 9 / R4 보충 (Spearman / IC-weighted hybrid / 가설 H10-H13 추가)

→ **★자문 prior 중 H2 (Stigum 3-6M lag) + H3 (BAB defensive outperform) 가 실측 검증 시 falsifier**. 자문 의존 위험 정확히 노출 (= 본 ERROR 의 근원). 단 H3 falsifier 자체도 본 데이터 (37개월) 로는 '판정불가' 가 정확 — REVERSED 단정 철회 필요.

## 실측 결과 정리 (v2 → v3 격하 대상)

| 항목 | v2 verdict (현 yaml 반영) | v3 권고 verdict |
|---|---|---|
| H1 Real Rate | ★CONFIRMED 강력 (partial IC=-0.167 / +0.129) | contemporaneous co-movement CONFIRMED / predictive FAILS — spec 정정 |
| H2 Stigum lag | ★REJECTED | 유지 (lag=0 IC=+0.171 contemporaneous, k=3~6 무유의) |
| H3 BAB | ★REVERSED (sleeve -1.5%/월 p=0.005) | **판정불가** (37개월 · 위기표본 부재, KeyError 버그) |
| H4a Credit beta split | PARTIAL CONFIRMED (gap 0.257) | 유지 (단 n=752 일 short 명시) |
| M3 dollar regime switch | ★M1 강력 확인 | **비유의 방향성 힌트** (Welch z=1.34 p_diff=0.18) |

## 재개 포인트 (다음 세션 즉시 시작)

1. `~/.claude/rules/empirical-claim-presentation.md` Write — 정량 claim presentation 5 의무 (coverage·sample n·spec/code match·autocorr·multiple comparison)
2. `raw/run_validation.py` Edit — classify_regime KeyError 명시 + H1 forward 3M 옵션 + M3 Welch t-test
3. `raw/run_validation.py` 재실행 → H1 contemporaneous vs predictive 동시 출력, H3 OutOfSample 명시
4. validation-H1.md / H3.md / m3-macro-linkage.md 격하 수정
5. study_session.yaml v3 재calibrate (base_weight·confidence_hooks)
6. main 보고

---

## v4 추가 인계 (main 2026-05-30 22:45 sleeve 분리 지시)

**핵심 결함**: sleeve = XLU+XLF eq-weight → 부호 cancel = H3 위조의 토양.

**v4 작업 명세**:
1. **sleeve 재정의** — DEFENSIVE_PURE = {XLP, XLU, XLV, XLC mature} (rate-NEG bond proxy) / FINANCIALS = {XLF} (독립 sleeve, breadth 충분 시)
2. **누락 critical 지표 추가**:
   - earnings_stability (quality factor — Asness QMJ)
   - VIX term structure (VIX3M/VIX) — VRP carry, defensive 알파 원천
   - yield curve steepness (financials specific, DGS10-DGS2 절댓값)
   - credit beta (financials specific, HY OAS partial-corr)
3. **R2 자문 채택** — 거시 배분레이어 전담·종목레이어 펀더멘털·순수 down-only 유지
4. **산업별 subagent 분할** — Agent 도구 4 (staples/utility/healthcare/banks) 병렬
5. **각 regime별 δ 실측** — DEFENSIVE_PURE vs FINANCIALS 분리 측정
6. **점추정 prior 박제 금지 + n<10 5게이트** = empirical-claim-presentation.md §1.5 + §2 verdict 5단계 강제
7. **rule §1.6 적용** — validation md 첫 줄 "분석 unit + portfolio label" 두 라벨 명시

**완료된 prerequisite (v3)**:
- promo-log ERROR-202605302245 (sleeve 정의 결함) prepend 완료
- rule §1.6 (분석 unit ↔ portfolio label 분리) 추가 완료
