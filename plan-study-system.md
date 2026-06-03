---
tags: [type/plan, domain/inv, phase/study-system, topic/indicator-weight-study]
date: 2026-05-30
note: 종목 스터디 시스템 계획 — 자산군별 psmux 작업방이 지표·가중치를 깊이 스터디해 종목별 동적 가중치 변경 규칙을 산출. main(btn-Codlearn)=통합. 통일 지시서=STUDY-KIT.md.
---

# plan-study-system — 종목 스터디 시스템

> 통일 산출 계약·코드 위치·자료 현황 = [STUDY-KIT.md](./STUDY-KIT.md) (각 방 필독).
> 자문 raw = `.gemini-web-last.md` / `.claude-web-basic-last.md` (grouping R1~R3).

## 목표
평가 지표 가중치를 **종목 단위로 잘게 쪼개 동적 변경**하는 규칙을, 자산군별 깊은 스터디(일반론
+리포트 렌즈 → 우리 자료 → 과거 대조)로 산출. 학습→규칙화→주입→해제 4단계 코드로 구현.

## 작업방 목록 (10 — 사용자가 psmux 생성)

| study_id | 자산군 | 보유 자료 | 수집 필요 | 특이 |
|---|---|---|---|---|
| `macro` | Macro & FX | FRED 86 + ALFRED | HY OAS·DXY·USDKRW(선구축), ECOS(키대기) | 컨디셔닝 레이어(regime 조건키). 통화량↔미·일 국채↔환율 관계도 |
| `eq_us_cyclical` | 미국주식 경기민감(IT/Comm/Discretionary/Industrials/Materials) | EDGAR 펀더멘털 | 섹터 멀티플 라이브 | 통일 하드룰(§6). 패널은 us 단일 수렴 |
| `eq_us_defensive` | 미국주식 방어/금융(Staples/Health/Utilities/Financials/Energy) | EDGAR | 〃 | us 패널 공유. cyclical/defensive 는 학습 출력 |
| `eq_kr` | 한국주식(KOSPI/KOSDAQ, 대형/소형) | DART, KRX 상태 | WICS 업종·외국인순매수(선구축) | 한국 modifier: USDKRW/외국인/반도체/중국 |
| `eq_intl` | 국가지수 ETF(DM/EM) | — | ETF holdings·NAV/TR | **신규 sleeve**. dollar beta 부호 us 와 반대 |
| `reit` | 리츠 | EDGAR 일부 | FFO·cap rate(유료) | equity sub-panel(승격 측정기준 충족 시) |
| `commodity` | 원자재 | Yahoo(실시간) | 재고·PMI vintage | carry/seasonal/inventory |
| `gold` | 금 | Yahoo(실시간) | real rate(FRED) | commodity 와 분리(monetary/FX hedge) |
| `bond_cash` | 채권/현금 | FRED 금리·BAA | 듀레이션·HY OAS(선구축) | 스프레드/듀레이션 |
| `crypto` | 암호화폐 | Upbit·MVRV | on-chain 확장 | 지표가중 R15 부적합 → belief→사이징만 |

## 진행 Phase

- **Phase 1 — 설계·선구축(main, 진행 중)**
  - [x] 자문 3R saturation(구분/학습방법/코드적용) — STUDY-KIT §8
  - [x] 통일 산출 계약 6블록 확정 — STUDY-KIT §3
  - [ ] 무료 수집기 선구축: WICS 업종, 외국인순매수, HY OAS(FRED), Ken French, US ETF holdings, DXY/USDKRW→FxStore. 기존 VintageProvider/FundamentalsProvider 인터페이스 준수, off graceful, self-test.
  - [ ] 시스템 선결 2건 확정: ① cross-sleeve 공분산 출처(factor-implied vs 별도추정) ② regime obs floor(<30 obs→global shrink-fallback)
- **Phase 2 — 종목 전문 애널리스트 스터디 (v2 — 사용자 정정 흐름)**: 각 방 = 담당 종목의 전문
  애널리스트가 된다. 자문 내용을 그대로 코드화하고 끝내지 않는다. **3단계 + raw 강제 + 승인 게이트**.

  ### 2-1 [방향성 — 자문 다회 라운드] ★승인 게이트(이 단계 끝나면 멈춤)
  - `/gemini-web` + `/claude-web` **다회(3~7R 수렴)** 로 완전성을 올려:
    ① **이론 수집 방향** (무슨 이론·교과서·리포트를 봐야 하나)
    ② **이론 검증 방향** (그 이론을 우리 수집기 데이터로 시계열상 어떻게 검증하나)
    ③ **핵심 가설 초안** (검증 대상 가설 — 반증조건 포함, 다회로 완전성↑)
  - 산출: `study-research/{sid}/direction.md` + `raw/round-{N}.md`(라운드별 누적 강제)
  - → main 취합 → **【승인 게이트】**: main 이 전문성·완전성 검토(①②③ 충족·가설 반증가능·다회
    수렴 흔적) → 승인 또는 보완 요청. ⛔ **승인 전 2-2 진입 금지.**

  ### 2-2 [이론 학습] 승인된 방향대로
  - 교과서 원리 + 리포트 관계도를 정독·정리. 산출: `raw/theory-notes.md`(강제 — 가격결정 원리,
    지표 의미·관계도. 예: M2↔미·일 국채금리↔환율).

  ### 2-3 [실데이터 시계열 검증 → 코드화]
  - 수집기 **실데이터로 가설을 시계열별 검증**: 상관·regime 분해·Rank-IC 로 언제 성립/붕괴하는지.
  - 그 검증 결과로 **lens·상관계수(블록3 prior)·가중치(블록4)가 어떻게 코드화되는지** 산출.
  - 산출: `raw/validation-{지표}.md`(강제 — 시계열 검증 근거) + `study_session.yaml`(7블록).

  ### ★강제 장치 (raw 완비 게이트)
  - main register 시 `raw/` 에 `round-*.md` + `theory-notes.md` + `validation-*.md` 완비 검사
    (study_loader). **바탕 raw 없는 yaml 은 산출 불인정** — 자문 그대로 코드화·종료 차단.

- **Phase 3 — 통합·production wiring(main, v1 골격 재사용)**: raw 완비 + 승인 끝난 방의 yaml →
  G1~G6(study_register) 로 카드 등록 + lens/flag wiring + 가드 재실행. opt-in off 무회귀. SACRED 불변.
  README/실거래 flip 은 사용자 게이트.

## main 선행 통합 골격 (사용자 A 결정 — 플러그인 템플릿)

방들이 다양한 산출을 가져와도 **공유 파일을 안 고치고** 끼우게 하는 데이터 주도 골격.
각 방 = `study_session.yaml`(7블록)만 제출 → 골격이 읽어 4단계에 주입.

- [x] **G1 study_loader** `core/study/study_loader.py`: 7블록 yaml 로드 + 스키마 검증(통일 하드룰
  코어셋·partial-corr conditioning_set·force-include≤4·vintage point_in_time) + 표준 dataclass. self-test 6/6.
- [ ] **G2 panel_manifest** `core/study/panel_manifest.py`: indicators→manifest→
  `build_indicator_matrix(panel_instance_id)` wrap(본체 보존, 인자만 manifest 참조).
- [ ] **G3 lens 주입** `core/study/lens_store.py`(별도 어댑터, 본체 보존) + `weight_card` lens 필드(opt-in) +
  `judge` LLM 컨텍스트 주입 wiring(down-only 보존).
- [ ] **G4 flag 경로** `core/study/flag_router.py`: confidence_hooks → `weight_falsification` 등록 어댑터
  (backtest engine outcome 기반, 라이브 별도). 확신/거부 flag 누적→신뢰도→렌즈 미세변동 루프.
- [ ] **G5 선결 2건** cross-sleeve 공분산(factor-implied 기본) + regime obs floor(<30→global shrink-fallback) 파라미터화.
- [ ] **G6 study_register**(★production wiring) `core/study/study_register.py`: yaml→registry 카드→
  stock_track 사이징→falsification flag end-to-end 연결. opt-in(INV_R15_WEIGHTS/INV_STUDY_LENS) on 시 즉시 동작.
- [ ] 종목 세분화 = hierarchical pooling(`composed_weights`: archetype+soft membership) — 부록 B 한계 수용.

## 검증(성공 판정)
- 각 방: study_session.yaml 6블록 완비 + summary + raw. 통일 하드룰(§6) 준수.
- main 조립: 종목별 weight_rules 가 4단계 파이프에 연결, 무회귀 self-test.
- SACRED: DRY_RUN/execute_trade 미변경, opt-in off 기본.

## SSOT
- 통일 지시서: STUDY-KIT.md / 진행 ckpt: progress-assumption-v2.md / 자문: .gemini-web-last.md·.claude-web-basic-last.md
