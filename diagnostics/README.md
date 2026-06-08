# diagnostics — 최종 테스트 검증·진단 하네스 (버전별)

10년 백테스트/최종 테스트 과정에서 만든 검증·진단 스크립트. **재사용성** 기준으로 메인 유지,
일회성 증거는 `archive/`. 모두 **production 모듈을 그대로 호출**(별도 드라이버 우회 아님), 실행 검증 완료.

**실행 = repo 루트에서**: `PYTHONUTF8=1 PYTHONPATH=. python diagnostics/<경로>.py`

| 폴더/파일 | Phase | 내용 |
|---|---|---|
| `p3-stock-pipeline/construction_smoke.py` | P3 | 9단계 종목선택→ETF fallback wire 스모크(회귀 재사용) |
| `p3-stock-pipeline/xsection_value.py` | P3 | 횡단면 value rank-IC alpha(NW-HAC). ⚠️ FWL no-op 의심(수정 대상) |
| `archive/fhc_live_mint.py` | P2 | (일회성) FHC 발권 LIVE 단독 검증 |
| `archive/gate_consult_verify.py` | P3 | (일회성) 가치게이트 자문 claim 검증 |

- **각 파일 용도 SSOT** = 프로젝트 [`CLAUDE.md`](../CLAUDE.md) §🧪 테스트/진단 하네스 표.
- **P4 멀티에셋 17축 백테스트**(현행)는 production 진입점이라 여기 없음 → `scripts/run_multiasset.py --backtest` (축 정의 = CLAUDE.md §📐17축).
