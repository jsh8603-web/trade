---
tags: [type/report, domain/inv, phase/II]
date: 2026-05-29
note: Phase2 업종 rule 프레임워크 3분할 위임 보고. 메인 3개(inv/button/btn-Codlearn) 공유.
---

# 분배 보고서 — Inv Phase2 업종 rule 프레임워크 3분할

## 배경 (한 줄)
"싸다=raw 멀티플 분위"를 "싸다=구조모델 잔차(cheapness_z)"로 바꾸는 업종·기간 조건부 valuation 프레임워크. gemini+claude 8라운드 자문 수렴(설계 확정). 바닥부터 최후, 기존 repo/데이터 차용 우선.

## 공통 필독 (모든 트랙)
- 리서치 종합: `FINDINGS-phase2-sector-rule-framework.md`
- 구현 청사진: `IMPL-OUTLINE-phase2.md`
- 분할 인덱스+차용맵: `SPLIT-INDEX-phase2.md`
- 자문 raw: `research-raw-phase2/`
- 불변식 4: ①position=entry version 고정 ②rollback=append만(mutate0) ③rule⊂emergency_stop ④opportunity cost 계상

## 3분할 (층 분할)
| 트랙 | 담당 세션 | spec | 범위 | 의존 |
|---|---|---|---|---|
| **T1 데이터·PIT** | **inv** | SPEC-T1-data-pit.md | bitemporal 패널·silent revision·corp action·survivorship·수집(Damodaran/French/DART/ALFRED) | 없음(최선행) |
| **T2 구조모델·archetype·regime** | **button** | SPEC-T2-structure-model.md | cheapness_z 잔차·structure model·archetype 5종·regime·D1/D4 | T1 패널 schema |
| **T3 rule·승격·거버넌스·관측** | **btn-Codlearn(나, 압축후)** | SPEC-T3-rule-governance.md | signal·resolver·G0~G6·consensus·RuleObserver·kill-switch | T2 cheapness_z·archetype |

## 왜 이 분배
- **층 분할**(도메인 아닌): 업종 rule 프레임워크가 커서 데이터→모델→rule 수직 절단. 의존이 단방향(T1→T2→T3)이라 인터페이스 3계약만 합의하면 mock으로 병렬.
- **T3=중심 세션(btn-Codlearn)**: 8라운드 자문 맥락 전부 보유 + 기존 시스템(execute_trade·emergency_stop·stock/valuation) 통합 지점 + 최복잡(거버넌스·실자산 안전). 압축 후에도 맥락 필요한 중심 코드라 본인 담당.
- **T1=inv**: 데이터층은 기존 inv 코드(stock/data/macro_vintage·backtest/walk_forward·pykrx) 가장 많이 만져서 inv 세션 적합.
- **T2=button**: 독립도 높은 모델링(통계/ML), 신규 모듈 위주라 별도 세션 적합.

## 인터페이스 3계약 (T1·T2·T3 먼저 합의)
1. `panel/{market}/{vintage}.parquet`: sector(as-of)·date·firm·features(filing-lagged)·multiple·delist_flag·delist_ret·regime_id·knowable_from
2. `StructureModel.cheapness_z(firm,sector,date,as_of)->float` (음수 클수록 저평가)
3. `ArchetypeCard`(archetype·primary_metric·companion_signals·value_trap_guards)

## wire 판정 핵심 (subagent)
- ⚠️ 경로: `core/valuation.py` 없음 → `stock/valuation.py`(value_stock:244, sector_ev_ebitda:247).
- 브리지 이미 존재: `run_agents.py:869` INV_CORE_GATE(코인). prior audit "core 0% 도달" 무효.
- ★게이팅: cheapness_z producer 없음(greenfield) + StockTrack 라이브 미인스턴스화.
- 차용: skfolio CPCV(mlfinlab stub 대체)·ai-hedge-fund valuation·jumpmodels real / mlfinlab=stub 복사금지.

## 착수 순서
1. T1(inv) 패널 schema 먼저 확정 → T2·T3에 공유.
2. T2(button) cheapness_z 인터페이스 확정 + **반도체 잔차 precision/recall 검증(안 갈리면 STOP)**.
3. T3(btn-Codlearn) mock으로 병렬 착수 → T1·T2 산출 도착 시 실연결.
