---
tags: [type/spec, domain/inv, phase/II, track/T1]
date: 2026-05-29
split_index: ./SPLIT-INDEX-phase2.md
findings: ./FINDINGS-phase2-sector-rule-framework.md
impl_outline: ./IMPL-OUTLINE-phase2.md
raw: ./research-raw-phase2/
track: T1 데이터·PIT 기반층 (최선행, 의존 없음)
---

# SPEC-T1 — 데이터·PIT 기반층

> 다른 main agent 위임. 공통맥락=split_index·findings·impl_outline. 자문raw=raw/. ⛔ 바닥부터 최후, FRED ALFRED 등 기존 재사용. 실자산 — PIT 무결성 최우선.

## 목적
rule·구조모델(T2,T3)이 딛고 설 "땅". bitemporal PIT 패널. **이 층 오염되면 위 전부 허상**(look-ahead).

## 산출 인터페이스 (T2·T3 소비 — 먼저 고정)
`panel/{market}/{vintage}.parquet` cols: sector(as-of), date, firm, features(filing-lagged dict), multiple, delist_flag, delist_ret, regime_id, knowable_from. content-hash 동결.

## WP
- **T1-1 수집**: Damodaran xls(US 섹터 멀티플/WACC/마진) + Kenneth French 49산업 + pykrx/FinanceDataReader/OpenDART(KR) + FRED ALFRED(거시 vintage 기존재사용). 소스표=findings §2.
- **T1-2 bitemporal store**: effective_from(적용)·knowable_from(알게된시점)·sys_time(패치) 3축. ⚠️ silent revision 방어(R8): DART/EDGAR 과거재무 조용한수정→sys_time≠knowable_from 분리 안하면 PIT 오염. 조회=AS OF 쿼리(DB가 PIT 강제).
- **T1-3 survivorship+backfill**: 상폐포함+delisting return(Shumway −30~−100%). 신규상장 backfill bias(IPO 편입시점 PIT).
- **T1-4 corp action 전처리**: 액면분할·자사주 멀티플 왜곡→adjustment.
- **T1-5 KR/US 이질성**: 시장별 분리 or market FE. French49 섹터≠한국.
- **T1-6 filing-lag**: disclosure_date 기준.

## 충족 축
E(기존데이터 PIT)·A 일부. 불변식 ②(append만).

## 리서치 포인터
findings §2·§5.5 C2·§5.7·§6. raw: R5·R7·R8.

## ★ wire 판정 + R8 보강
- seam: `stock/data/macro_vintage.py`(FRED ALFRED vintage real, future-as_of reject) + `backtest/walk_forward.py`(filter_pit_fundamentals·UniverseManager). NEEDS-REFACTOR(primitive 존재, parquet 패널·knowable_from store 신규). ⚠️ macro_vintage=FRED_API_KEY 필요, ECOS(KR)=NotImplementedError.
- 차용: pykrx(1469줄 real)·FinanceDataReader·OpenDartReader·dart-fss(KR)·Damodaran xls(read_excel URL직접). KR 섹터멀티플 vintage=**최난, 차용없음→pykrx 스냅샷 자체구축**.
- ★ R8 바닥(필수): multiple 정의 GAAP/non-GAAP 40분기 drift→정의버전 고정. bitemporal은 "언제 알았나"만 보장, 의미동일성 X. silent revision(DART/EDGAR 과거 조용한수정)→sys_time≠knowable_from 분리.

## 산출물
`core/data/pit_panel.py`, `panel/`, bitemporal store, 수집 스크립트, 패널 schema 문서(T2·T3 계약).
