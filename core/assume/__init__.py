"""core/assume — 가정(criteria) 라이프사이클 오케스트레이션 + 판정 패키지.

소유 경계 (plan-assumption-v2-axes.md §4):
- btn-button(T2): card_contract.py (AssumptionCardLike Protocol + BaseAssumptionFields + assert_falsifiable)
- btn-Codlearn(T3): registry / validator / update_controller / derivation / judge / dag / orphan_guard

⚠️ 이 __init__ 은 import-free (card_contract 미랜딩 시 import 에러 방지). 모듈은 직접 import.
"""
