"""core/data — bitemporal PIT 패널 (Phase2 T1 트랙).

산출 계약 = PANEL-SCHEMA-phase2.md. T2(구조모델)·T3(rule) 이 소비.
- pit_query: AS OF 조회 인터페이스 + 계약0(as_of_resolver) seam.
- pit_panel: 기존 provider(dart/edgar/krx) 를 bitemporal 패널로 조립.
"""
