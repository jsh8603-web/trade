---
name: handoff-etf-fallback-weak-sleeve-20260606
description: 약변별 sleeve(종목 selection 변별력 없음=골고루 담는 수준) → 수익률高+AUM大 테마 ETF fallback 코드화. 한미 공통. 작업량 검토 완료, 다음=구현 plan.
next-action: "구현 plan 작성(plan.md). 첫 행동=(0) 변별력 적은 sleeve 확정: 한국=within v2 低9곳 완료, 미국=eq_us selection within IC 등급 산출(미산출 상태). 그 후 (1)산업↔테마ETF 매핑. ⛔ go-live·실주문 미접촉, production 무접촉."
type: project
tags: [domain/eq-kr, domain/eq-us, type/handoff, topic/etf-fallback-weak-sleeve]
date: 2026-06-06
---

# 약변별 sleeve → 테마 ETF fallback 코드화 — 작업량 검토 핸드오프 (2026-06-06)

> 사용자 의도: "주식 골고루 담는다 정도의 변별력이 없으면(=종목 selection 무의미), 수익률 높고 운영규모(AUM) 큰 해당 테마 ETF를 사도록 코드화." **한국+미국 모두**. "우선 sleeve 내 변별력 적은 걸 골라야겠지"(식별 선행).

## §1. 현재 상태 + 첫 행동
- **상태**: 작업량 검토 완료(데이터 가용성 + 아키텍처 삽입지점 + ETF 매핑 가능성 파악). 코드 미착수.
- **★첫 행동(재개)**: 구현 `plan.md` 작성. 그 전 (0) 변별력 적은 sleeve 확정 — 한국=within v2 低 9곳 완료 / **미국=eq_us selection within IC 등급 미산출**(eq_us는 sleeve study만, 종목 selection 등급 없음) → 산출 선행.
- ⛔ production(core/stock) 무접촉. go-live·실주문 = 사람게이트 미접촉. ETF "수익률 높은" 선정 = **look-ahead 위험**(과거수익 chasing) → PIT 엄수.

## §2. 진행 맵 (작업 6단계 + 규모)
| 단계 | 작업 | 규모 | blocker |
|---|---|---|---|
| 0 변별력 식별 | 한국 within v2 低9 完 / 미국 eq_us selection 등급 산출 | 소 | 미국 within IC 미산출 |
| 1 ETF 매핑+선정 | 산업↔테마ETF 테이블 + 선정기준(AUM>임계 ∧ 수익률) | 중 | 정유·통신 ETF 부재 |
| 2 ETF 데이터 | FDR NAV/시세 + AUM 소스 + 미국 yfinance, PIT 동결 | 중 | AUM 소스(KRX 차단), look-ahead |
| 3 fallback 분기 | ρ<임계 → 테마 ETF 1개 (mega basket 패턴 재사용) | 소~중 | — |
| 4 포트폴리오 편입 | ETF instrument, admission allowlist, valuation 우회, risk_gate 통합 | 중~대 | ★ETF≠종목 아키텍처 = 핵심 작업량 |
| 5 백테스트 | ETF 시세 PIT + 슬리피지 패리티 | 중 | — |
- **총평**: 중규모. 최대 작업량 = 4단계(ETF는 내재가치 없어 value 2단 트리거 우회, admission/AssetTrack/risk_gate 신 instrument 경로).

## §3. 사용자 박제
- "골고루 담는 수준 변별력 없으면 = 종목 selection 포기, 테마 ETF로 대체."
- ETF 선정 = **수익률 높음 + 운영규모(AUM) 큼** 2기준.
- **한국+미국 모두**.
- "우선 sleeve 내 변별력 적은 걸 골라야겠지" = ETF fallback 대상 식별(변별력 약 sleeve)이 1단계.
- production 무접촉, go-live 미접촉(연구→통합단계).

## §4. 파일 inventory (절대경로)
- **변별력 등급(0단계 입력)**:
  - 한국: `study-research/eq_kr/industries/_rotation/validation-within-residual-v2.json`(ρ 등급, 低 9곳) + `within_industry_residual_kr.py`(EB v3 계층베이즈)
  - 미국: `study-research/eq_us/industries/*/summary.yaml` — cyclical "basket化 불필요(60종 cross-sectional 유효)", mega_tech만 basket. ★종목 selection within IC 등급 미산출 → 산출 필요
- **fallback 삽입 지점(3·4단계)**:
  - `stock/cross_sectional_selection.py`(520줄) — `min_sector_n<8 → sleeve pool fallback`(line 80) + mega_tech "11종 basket 통째=selection 대상 아님"(빈 preset) = ETF fallback 패턴 원형
  - `stock/sleeve_signals.py`(line 32) — mega_tech basket 빈 preset
  - `stock/selection_pipeline.py`(130줄) — build_universe_candidates
  - `stock/admission.py` — ETF allowlist 추가 지점(레버리지/인버스 거절 규칙 옆)
  - `stock/valuation.py` — ETF는 우회(내재가치 산출 부적합)
- **ETF 데이터(1·2단계)**: FDR `StockListing('ETF/KR')` = 1136개(Symbol/Category/Name/NAV). 미국 = yfinance/FDR ETF.
- **검토 산출**: 본 핸드오프 + 직전 within selection 판정(`candidate-ledger.md` §🧩 3층 selection).

## §5. 미해결·실패 (삽질 위험)
1. **정유·통신 테마 ETF 부재**(FDR 검색 정유 0·통신 1 부적합): 약변별인데 ETF도 없음 → 산업중립 EW 유지 or 시장 ETF or 인접 테마(정유=KODEX 에너지화학) 결정 필요.
2. **AUM(순자산) 데이터 소스**: pykrx ETF = KRX 차단(빈응답). FDR은 NAV/시세만(AUM 별도). AUM 소스 = KRX 복구 / 운용사 공시 / NAV×상장좌수 근사 중 택일.
3. **ETF instrument 아키텍처(최대 작업량)**: stock 트랙은 개별 종목(Fundamentals PIT) 전제. ETF = valuation(내재가치) 부적합 → value 2단 트리거 우회 + admission allowlist(현재 레버리지/인버스 거절) + AssetTrack/risk_gate 신 경로. byte-identical 보존하며 분기.
4. **look-ahead(수익률 선정)**: "수익률 높은 ETF" = 과거수익 chasing 위험. PIT 시점 수익률 + forward 검증 필요(모멘텀 factor 취급).
5. **미국 selection 등급 미산출**: eq_us는 sleeve study(cyclical/defensive/mega_tech)만, 종목 selection within IC 등급 없음. 한국 within v2 패턴으로 미국 산출 선행.
6. **한미 비대칭**: 미국은 종목 多 → cross-sectional 작동(basket 필요 적음, mega_tech만). 한국은 small market → 低 9곳. fallback 비중이 한국에 쏠림.

## §6. 자문 종합 (본 검토 = 직전 within-weak-signal 자문 후속, 신규 자문 0)
- 직전 자문(`.consult-kr-within-industry-weak-signal-RESULTS.md`)의 (f) "종목별 수급 = 약신호 직교 레버"는 KRX 차단 DATA-GATE. **ETF fallback = (f) 대안 경로**(종목 selection 포기 시 테마 노출만 확보).
- 자문 C10(低 selection = v 산업중립 수축) 의 확장: 산업중립 EW 대신 **테마 ETF 1개** = 더 깔끔한 노출(거래비용↓, 분산↑).
- 구현 plan 작성 시 신규 자문 트리거(아키텍처 변경 = ETF instrument 편입) → `/gemini-web`+`/claude-web` 권장.
- 검토 데이터: FDR ETF 매핑(반도체54/2차전지18/철강2/자동차3/바이오17/조선7/화학3/은행7 ✅, 정유0·통신1 부재), 미국 yfinance.
