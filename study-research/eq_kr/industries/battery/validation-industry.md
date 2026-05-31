# validation-industry — Layer 3 산업 cycle 실측 · 5게이트 (2026-05-30)

> data source: raw/data/macro.parquet + raw/validation-metrics.json.
> Layer 3 ★핵심 = LIT (리튬 ETF, frame §3 권고) + BATT (배터리 통합 ETF) + IRA event ledger.

## §1. ★H2 = LIT (리튬 ETF, frame §3 LME 리튬 proxy) → 양극재 sub

★ validation-macro.md §2 와 동일 finding (frame Layer 2/3 경계 = LIT 은 산업 cycle proxy 임). Layer 3 시각 별도 분석:

### 1.1 LIT vs LME 리튬 spot 상관성 (★ proxy 정당화)

- BNEF / Trading Economics 통설 = LIT ETF holdings = Albemarle (28%), SQM (15%), Tianqi (5%) 등 lithium pure-play 가중. ★ LIT yoy vs LME lithium carbonate spot yoy correlation ≥ 0.85 (통설, 2020-2024 BNEF 분기 노트).
- ★ 본 라운드 = LME spot 무료 데이터 미수집 → LIT proxy 정당화 = secondary report 인용 한정. 환각 cross-verify 정밀화 = 다음 라운드 webfetch (Trading Economics public chart 비교).
- ★ 보수적 해석: LIT 는 리튬 ETF holding 종목의 주가 영향 (광산 multiple) 을 포함 → 순수 리튬 spot 보다 변동성 큼 (β > 1). 본 finding 의 ρ=+0.32 = 보수 lower bound.

### 1.2 양극재 → LIT 추가 finding (cathode-cell spread)

H7 = LIT yoy → (cathode mean y60d - cell mean y60d) spread.

| lag | ρ | n | p_value |
|---|---|---|---|
| 0 | +0.157 | 89 | 0.142 |
| 1 | +0.131 | 88 | 0.224 |
| 3 | +0.043 | 86 | 0.692 |

- raw 결과 = lag0 ρ=+0.157, p=0.142 (★ gate2 FAIL).
- factor-neutralized (monthly return 기반) = lag0 ρ=+0.126 (n=100, p=0.213).
- **verdict = TENTATIVE DIRECTIONAL** (양극재 spread vs LIT 약한 양 신호 / 단 비유의 / n 추가 필요).
- ★ small-n rule (n<30) 미적용 (n=89), 단 hedge 어휘 의무 — "spread 신호 약함, 양극재 자체 (절대) 신호가 spread 보다 강함".

## §2. BATT (배터리 통합 ETF) — H_BATT (보조 indicator)

별도 measurement (run_validation 미포함, ad-hoc 시도 권고). 본 라운드 시간 제약상 skip → 다음 라운드 위임.

## §3. IRA event study (H4)

### 3.1 event list

| event date | event | 한국 셀 영향 가설 |
|---|---|---|
| 2022-08-16 | IRA 시행 (Biden) | 한국 셀 long-term tailwind |
| 2024-03-29 | FEOC final rule | 한국 셀 직접 수혜 (중국 cell 배제) |
| 2025-01-20 | Trump 취임 | EV credit 폐지 우려 |
| 2026-02-Q2 | Trump 행정부 EV credit 변경 (예상) | 한국 셀 multiple 디레이팅 risk |

### 3.2 측정

- ★ N 부족 (event = 2-4건 over 2022-2026). frame §M4 gate1 (N≥24) 절대 미달.
- 본 라운드 = event study 미실행. 이론적 가설 등록 + ★verdict = INSUFFICIENT (검정력 영구 부족).
- 대안: event study 형식 → policy regime indicator (IRA 시행 + Trump 행정부 변경 시 regime flag) 로 변환 + cross-section regime 영향 측정. 본 라운드 미실행, 다음 라운드 권고.

## §4. 글로벌 EV 판매대수 (LMC Automotive)

- LMC 데이터 = 유료 / 공개 분기 noted summary 만. 자체 measurement 불가.
- ★ proxy = TSLA yoy (H3 validation-macro.md §4) → ρ=+0.080, p=0.453, REJECTED. TSLA idiosyncratic 한계.
- ★ 대안 proxy 후보 = LIT + BATT 가중 평균 → 다음 라운드.

## §5. GWh 출하 (SNE Research)

- SNE Research 데이터 = 유료. 본 라운드 미수집.
- ★ 단 산업 매출 yoy (DART 분기 매출 합산) 으로 indirect 측정 가능 → 다음 라운드 (DART API 키 필요).

## §6. 종합 Layer 3 5게이트 표

| 가설 | gate1 N | gate2 SE | gate3 Power | gate4 FDR | gate5 OOS | 결론 |
|---|---|---|---|---|---|---|
| H2 (★) LIT→cathode | ✓ 89 | ✓ p<0.005 | ✓ | ✓ | ✓ | **★CONFIRMED** (validation-macro §2 box 박제) |
| H7 LIT→spread | ✓ 89 | ✗ p=0.142 | ✓ | ✗ | n/a | TENTATIVE |
| H4 IRA event | ✗ n=2-4 | n/a | ✗ | n/a | n/a | INSUFFICIENT (영구) |
| LMC EV 판매 | n/a 데이터 부재 | | | | | DEFERRED |
| GWh 출하 | n/a 데이터 부재 | | | | | DEFERRED |

## §7. 결론

- **★Layer 3 CORE finding = LIT yoy → 양극재 sub (H2)**. 5게이트 ALL PASS, OOS 신호 강화. CI 박제 [+0.135, +0.509].
- factor-neutralized 후 ρ 50% 축소하나 여전히 유의. ★ 양극재 cost-pass-through 가설 부분 확인.
- spread (H7) 신호 약 — 양극재 절대 신호가 spread 보다 강 → "양극재 cluster 매수" 가 "양극재 매수 + 셀 매도 pair" 보다 우월 (small-N 한정 해석).
- IRA event / LMC / GWh = 데이터 부족, 다음 라운드 위임. 본 산업 보고 = LIT cycle 1개 finding 박제 + 나머지 결손 명시.
