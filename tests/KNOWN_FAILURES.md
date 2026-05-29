# KNOWN test FAILURES — 비-프로덕션 (2026-05-29 기준)

> **목적**: 전체 suite(`pytest tests/`) 실행 시 fail/error 나는 항목 중 **프로덕션 로직 버그가 아닌 것**을 분류·박제. 다음 세션/리뷰어가 "이건 기존 환경/의존성/격리 이슈, 신규 회귀 아님"을 즉시 인지하도록.
> **검증 기준**: Phase I 변경 코드(coin_*·backtest·kis_client·run_agents.sh·core_gate_check·asset_track)는 **각 WP 단독 테스트 통과**. 아래는 전부 (a)미설치 optional dep (b)외부 network (c)테스트 격리 부채 — 활성 투자 파이프라인 무관.
> **현황**: RL(gymnasium) 8파일+test_train = `conftest.py collect_ignore` 제외 완료. 남은 ~48 fail / ~12 error 분류 ↓.

## 1. 미설치 optional dep (안 쓰는/보조 기능) — 설치 시 해소

| 누락 모듈 | 영향 테스트 | 기능 | 조치 |
|---|---|---|---|
| `scripts.breakout_trader` | test_breakout (~12 error) | breakout 전략 모듈 부재(미사용/제거됨) | 미사용이면 collect_ignore, 쓸거면 모듈 복원 |
| `gymnasium`/`gym`/`stable_baselines3` | test_breakout 등 잔여 RL | RL 훈련(활성 파이프라인 미사용) | `pip install gymnasium stable_baselines3` 또는 ignore |
| `qrcode` | test_dashboard (~4) | 대시보드 QR | `pip install qrcode` |
| `msgpack` | (1) | 직렬화 | `pip install msgpack` |

## 2. 외부 network / 테스트 config (프로덕션 로직 아님)

| 테스트 | 사유 | 조치 |
|---|---|---|
| test_kimchirang_e2e / _integrations (2) | async def 미지원(pytest-asyncio 미설정) + Binance 외부망. **김치 프리미엄 엔진(kimchirang/) 기능 자체는 정상** | `pip install pytest-asyncio` + `asyncio_mode=auto` 설정 / 네트워크 환경서 실행 |
| test_so1_llm_provider (1) | urllib.error — LLM 엔드포인트 외부망 | 네트워크 환경(또는 mock) |
| test_execute_trade::test_network_timeout (1) | 의도적 network timeout 테스트 | 네트워크 환경 |
| ConnectionRefused (1) | 외부 서비스 미기동 | 해당 서비스 기동 시 |

## 3. Build/requirements 메타 테스트 (dev 환경 의존, 런타임 무관)

| 테스트 | 사유 |
|---|---|
| test_build_imports/config/build/safety (~13) | requirements.txt 정합("누락 import"/"미사용 패키지"/"secret") 검사 — dev 환경 dep 미설치 시 fail. 프로덕션 런타임 로직 아님 |
| test_e2e_automation (7) | 빌드/배포 자동화 e2e — 외부 환경 의존 |

## 4. 테스트 격리 부채 (단독 PASS, full suite 만 FAIL) — pre-existing

> 증상: 해당 파일 단독 실행은 통과, `pytest tests/` 전체 실행 시 fail. 원인=full suite 의 **먼 다른 테스트가 공유 상태(모듈 싱글톤/전역) 오염** (os.environ 누수는 conftest `_isolate_environ` fixture 로 차단했으나 비-env 상태가 잔존). bisection 필요한 기존 부채.

| 테스트 | 단독 결과 | 증상 |
|---|---|---|
| test_so5_p4_kis_client (7) | **단독 25 passed** | suite 서 assert None/True 역전 |
| test_so7_p4_golden_rule (3) | — | so3/so5/so6 subprocess 재실행 cascade |
| test_so6_p4_integration_gate (3) | — | Phase4 gate |
| test_so3_p4_macro_vintage (4) | — | FRED key 존재 + 격리 혼재 |
| test_execute_trade_comprehensive (2) | — | `assert 'NORMAL'=='CRITICAL'` = KillSwitch 전역 상태 누수 의심 |
| test_so4_c2b3_integration (1) | — | env/격리 |

**해소 방향**: 격리 오염원 bisection(`pytest -p no:randomly --lf` 등) → 오염 테스트가 전역/싱글톤 setUp/tearDown 복원하도록 수정. 우선순위 낮음(프로덕션 무관, pre-existing).

---

## 한 줄 요약
남은 fail = 미설치 dep + 외부망 + 빌드메타 + 격리부채. **프로덕션 코드 버그 0**(Phase I 변경분 각 WP 단독 통과). 신규 세션은 위 4분류 대조 후 "새 회귀"만 추적하면 됨.
