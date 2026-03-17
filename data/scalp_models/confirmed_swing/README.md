# Swing DQN R6 모델 — 실전 투입용 (역대 최고)

## 모델 비교

| 항목 | R1 (이전) | R6 (현재, 권장) |
|------|-----------|----------------|
| 파일 | `swing_dqn_r1.zip` | **`swing_dqn_r6.zip`** |
| 알고리즘 | DQN | DQN |
| 하이퍼파라미터 | lr=0.001, [128,64], gamma=0.99 | **lr=0.001, [256,128], gamma=0.97** |
| 승률 | 40.7% | **42.6%** |
| 평균 순이익 | +0.265% | **+0.354%** |
| R:R 비율 | 3.94 | **4.51** |
| Profit Factor | 2.71 | **3.35** |
| 강제 손절 | 0건 | 3건 |
| 100만원 x 10회 | +26,526원 | **+35,408원** |

## R6 성능 상세 (3000 에피소드 평가)

| 지표 | 결과 |
|------|------|
| 승률 | 42.6% (1,279승 / 1,721패) |
| 평균 순이익 (수수료 후) | **+0.354%** |
| R:R 비율 | 4.51 (이길 때 4.5배 수익) |
| Profit Factor | 3.35 |
| Sharpe Ratio | 0.321 |
| 이길 때 평균 | +1.184% |
| 질 때 평균 | -0.262% |
| 최대 수익 | +4.505% |
| 최대 손실 | -0.803% |
| 최대 연속 손실 | 15회 |
| 평균 보유 시간 | 23분 (4.6봉) |

### 청산 분포

| 유형 | 건수 | 비율 |
|------|------|------|
| 조기 손절 (SL) | 1,685 | 56.2% |
| 이익 실현 (TP) | 1,271 | 42.4% |
| 타임아웃 | 41 | 1.4% |
| 강제 손절 | 3 | 0.1% |

## 맥미니에서 실행 방법

### 1. 코드 업데이트
```bash
cd ~/claude-coin-trading && git pull
```

### 2. 의존성 확인
```bash
pip install stable-baselines3 gymnasium
```

### 3. 실전 매매 시작 (24시간) — R6 모델
```bash
# 실전 매매 (DRY_RUN 무시, 직접 매수/매도)
python -u scalp_ml/swing_live_trader.py --hours 24 --amount 1000000 --model data/scalp_models/confirmed_swing/swing_dqn_r6.zip > logs/swing_live.log 2>&1 &

# 로그 모니터링
tail -f logs/swing_live.log
```

### 4. 드라이런 테스트 (먼저 권장)
```bash
python -u scalp_ml/swing_live_trader.py --hours 1 --dry-run --model data/scalp_models/confirmed_swing/swing_dqn_r6.zip > logs/swing_live_test.log 2>&1 &
tail -f logs/swing_live_test.log
```

### 5. 금액 변경
```bash
# 50만원씩
python -u scalp_ml/swing_live_trader.py --hours 24 --amount 500000 --model data/scalp_models/confirmed_swing/swing_dqn_r6.zip
# 200만원씩
python -u scalp_ml/swing_live_trader.py --hours 24 --amount 2000000 --model data/scalp_models/confirmed_swing/swing_dqn_r6.zip
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
| 보수적 | 5회 | ~17,700원 | ~53만원 |
| 보통 | 8회 | ~28,300원 | ~85만원 |
| 적극적 | 10회 | ~35,400원 | ~106만원 |
| 고빈도 | 15회 | ~53,100원 | ~159만원 |

## 주의사항

- 이 모델은 승률 42.6%로 **10번 중 4번 이기지만, 이길 때 4.5배** 수익
- 최대 연속 손실 15회 구간이 있을 수 있으나, 장기적으로 양의 기대값
- 반드시 **드라이런으로 1시간 테스트** 후 실전 전환 권장
- `.env`의 `DRY_RUN=true`는 유지 — 봇이 매매 시 자체적으로 우회
