# scripts 패키지 초기화
# __init__.py가 있어야 mypy가 scripts.cycle_id를 정상적으로 인식한다.
# (없으면 cycle_id와 scripts.cycle_id 중복 모듈 에러 발생)
