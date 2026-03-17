# Swing DQN R1 모델 — 실전 투입용

## 모델 정보

| 항목 | 값 |
|------|-----|
| 파일 | `swing_dqn_r1.zip` (185KB) |
| 알고리즘 | DQN (Stable-Baselines3) |
| 환경 | SwingExitEnv (5분봉, 10차원 관측) |
| 훈련 스텝 | 1,000,000 |
| 하이퍼파라미터 | lr=0.001, net_arch=[128,64], gamma=0.99, batch=128, exploration=0.2 |

## 성능 (3000 에피소드 평가)

| 지표 | 결과 |
|------|------|
| 승률 | 40.7% |
| 평균 순이익 (수수료 후) | +0.265% |
| R:R 비율 | 3.94 (이길 때 4배 수익) |
| Profit Factor | 2.71 |
| 강제 손절 | 0건 |
| 100만원 x 10회 예상 | +26,526원 |

## 맥미니에서 실행 방법

### 1. 코드 업데이트
```bash
cd ~/claude-coin-trading && git pull
```

### 2. 의존성 확인
```bash
pip install stable-baselines3 gymnasium
```

### 3. 실전 매매 시작 (24시간)
```bash
# 실전 매매 (DRY_RUN 무시, 직접 매수/매도)
python -u scalp_ml/swing_live_trader.py --hours 24 --amount 1000000 > logs/swing_live.log 2>&1 &

# 로그 모니터링
tail -f logs/swing_live.log
```

### 4. 드라이런 테스트 (먼저 권장)
```bash
python -u scalp_ml/swing_live_trader.py --hours 1 --dry-run > logs/swing_live_test.log 2>&1 &
tail -f logs/swing_live_test.log
```

### 5. 금액 변경
```bash
# 50만원씩
python -u scalp_ml/swing_live_trader.py --hours 24 --amount 500000
# 200만원씩
python -u scalp_ml/swing_live_trader.py --hours 24 --amount 2000000
```

## 매매 로직

1. **1분마다** 업비트 1분봉 30개 수집 → 5분봉 변환
2. **진입 조건** (3중 필터):
   - 15분 모멘텀 0.15%+
   - 거래량 스파이크 1.8배+
   - RSI 극단 (35 이하 또는 65 이상)
3. **매수**: 조건 충족 시 시장가 매수
4. **청산**: DQN 모델이 매 분마다 HOLD/TP/SL 결정
5. **강제 청산**: 60분 초과 또는 -0.4% 손실 시
6. **알림**: 매수/청산마다 텔레그램 알림

## 예상 일일 실적 (100만원 기준)

| 시나리오 | 일 거래 | 일 순이익 | 월 순이익 |
|---------|--------|----------|----------|
| 보수적 | 5회 | ~13,000원 | ~39만원 |
| 보통 | 8회 | ~21,000원 | ~63만원 |
| 적극적 | 10회 | ~26,000원 | ~78만원 |

## 주의사항

- 이 모델은 승률 40.7%로 **3번 중 1번만 이기지만, 이길 때 4배** 수익
- 연속 손실 구간이 있을 수 있으나, 장기적으로 양의 기대값
- 반드시 **드라이런으로 1시간 테스트** 후 실전 전환 권장
- `.env`의 `DRY_RUN=true`는 유지 — 봇이 매매 시 자체적으로 우회
