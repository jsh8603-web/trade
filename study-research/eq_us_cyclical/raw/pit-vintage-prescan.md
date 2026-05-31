---
tags: [type/prescan, study/eq_us_cyclical, phase/post-M3, topic/ALFRED-vintage, audit/D-axis]
date: 2026-05-31
study_id: eq_us_cyclical
phase: "item6 사전조사 — ALFRED vintage 적용방식: PIT-sensitive 시리즈 식별 + ALFRED endpoint 확인"
session: btn-common-task (eq_us_cyclical workspace)
deliver_to: btn-Codlearn (main, item6 합의 대기)
inputs:
  - raw/fred/ 17 시리즈 CSV 인벤토리
  - raw/m3-findings.md (M3 driver = us10y/dxy/oil)
  - AUDIT-GUIDE.md §1 D 축 (PIT/lookahead, hard-fail 코어 4)
note: |
  ★사용자 inject 지시 — main 회신 대기 중 idle 금지로 item6/item7 사전조사.
  결과 1줄 보고 후 main 합의 시 적용방식 확정.
data_integrity: "⛔ 합성 無. 기존 raw/fred/ CSV 인벤토리 + ALFRED API spec 기반."
---

# Pre-scan: ALFRED Vintage Application

> D 축 (PIT/lookahead) hard-fail risk 회피용 vintage 적용 사전조사. 결론: **M3 driver 3종 (us10y/dxy/oil) = 일별 시장가, revision 거의 X → PIT 위반 risk minor**. ALFRED critical 시리즈 = monthly economic indicators 5종 (CFNAI/NEWORDER/AMTMNO/BUSINV/DGORDER). API = FRED `series/observations` + `realtime_start`/`realtime_end` 파라미터 추가.

---

## §1. M3 frame driver 의 vintage revision 영향도

### 1.1 M3 거시연관 분석에 쓰인 driver 3종

| Driver | Source | 발표 주기 | Revision 패턴 | vintage 영향도 |
|---|---|---|---|---|
| **us10y (DGS10)** | FRED daily | T+1 (전일 종가) | ✅ revision 없음 (Treasury 거래소 종가) | **거의 zero** |
| **dxy** | yfinance daily | T+1 | ✅ revision 없음 (외환 종가) | **zero** |
| **oil (WTI)** | yfinance daily | T+1 | ✅ revision 없음 (CME 선물 종가) | **zero** |

★ **결론 1**: M3 frame 의 거시 driver 3종 = ★real-time market data 라 vintage revision 영향 사실상 zero. → AUDIT-GUIDE.md D 축 (PIT) hard-fail risk = M3 frame 한정 **minor**.

### 1.2 yfinance sector ETF (XLB/XLE/XLI/SOXX) 도 동일

| Source | revision | 영향도 |
|---|---|---|
| yfinance daily close | ✅ revision 없음 (NYSE/NASDAQ 종가) + split/dividend 조정만 | zero |

★ **결론 2**: ETF 가격도 거래소 종가라 revision 영향 zero. yfinance 가 자동으로 split/dividend 조정 제공. survivor bias risk (AUDIT-GUIDE I 축) = ETF level 분석 한정 작음.

---

## §2. PIT-sensitive 시리즈 식별 (raw/fred/ 17 종 분류)

### 2.1 Revision 없음 / 거의 X (daily 시장가, vintage 적용 불필요)

| 시리즈 | 가용 시작 | 영향 가설 | 처리 |
|---|---|---|---|
| **DGS10** | 1990-01 | M3 거시연관 driver | as-is OK |
| **DGS2** | 1990-01 | 잠재 driver | as-is OK |
| **T10Y2Y** | 1990-01 | yield curve (잠재) | as-is OK |
| **VIXCLS** | 1990-01 | H4 검증 (validation-H4.md) | as-is OK |

### 2.2 Revision 있음 / monthly (★ALFRED vintage critical)

| 시리즈 | 가용 시작 | 발표 시점 | Revision 패턴 | 영향 가설 |
|---|---|---|---|---|
| **CFNAI** | 1990-01 | 월 말 (T+~25d) | initial + 과거 3개월 minor revision + annual benchmark revision | H3 (validation-H3.md, ★ALFRED 적용 필요) |
| **NEWORDER (ISM)** | 1992-02 | 월 초 (T+~3d advance) | advance → preliminary → final + benchmark | M3 잠재 driver / 산업재 lead 후보 |
| **AMTMNO (M3 census)** | 1992-02 | T+~50d | M3 advance → final + benchmark | M3 driver 잠재 |
| **DGORDER** | 1992-02 | advance (T+~25d) → final (T+~55d) | advance → final + benchmark | 산업재 lead 후보 |
| **BUSINV** | 1992-01 | T+~45d | advance → final + benchmark | M3 잠재 driver |

★ **결론 3**: ALFRED critical 시리즈 = **5종 monthly economic indicators**. H3 (CFNAI) 가 가장 즉각 영향. 나머지 4종 = H 가설 확장 / M3 후속 round 잠재 driver.

### 2.3 Credit OAS (혼합)

| 시리즈 | 가용 시작 | Revision | 가용 한계 |
|---|---|---|---|
| **BAMLH0A0HYM2 (HY OAS)** | **2023-05** | 일별 가격 indexing, minor revision | ★ 3년만 가용 — eq_us_defensive H3 ERROR 와 동일 가용 부족 risk |
| **BAMLC0A0CM (IG OAS)** | (확인 필요) | 동일 | (확인 필요) |
| **AAA / BAA / AAAFFM / BAAFFM / AAA10Y / BAA10Y** | (확인 필요, 일별 yield) | revision 거의 X | as-is OK |

★ **결론 4**: BAMLH0A0HYM2 = 가용 시작 2023-05 → 장기 frame 활용 불가 (eq_us_defensive H3 가 "n=317" 주장하다 main 자가 fix 한 패턴 재발 risk). 장기 credit signal = AAA/BAA spread 활용 가능.

---

## §3. ALFRED API endpoint + 적용방식

### 3.1 API URL + 파라미터

```
GET https://api.stlouisfed.org/fred/series/observations
  ?series_id={SID}
  &api_key={KEY}
  &observation_start=YYYY-MM-DD
  &observation_end=YYYY-MM-DD
  &realtime_start=YYYY-MM-DD     # ★ vintage as-of-date 시작
  &realtime_end=YYYY-MM-DD       # ★ vintage as-of-date 종료
  &file_type=json
```

★ `realtime_start` / `realtime_end` 가 PIT vintage 핵심. "이 날 알려진 값" 가져오기 = `realtime_start=realtime_end=YYYY-MM-DD`.

★ 대안: `vintage_dates=YYYY-MM-DD,YYYY-MM-DD,...` 파라미터로 multi-vintage 조회. backtest 시 epoch 별 vintage 비교 가능.

### 3.2 적용 패턴 — walk-forward backtest 용 PIT loader

```python
# pseudo
def fetch_alfred_pit(series_id, observation_dt, asof_dt):
    """observation_dt 의 시리즈 값을 asof_dt 시점에 알려진 vintage 로 가져오기"""
    params = {
        "series_id": series_id,
        "observation_start": observation_dt,
        "observation_end": observation_dt,
        "realtime_start": asof_dt,
        "realtime_end": asof_dt,
        "api_key": API_KEY,
        "file_type": "json",
    }
    r = requests.get(f"https://api.stlouisfed.org/fred/series/observations", params=params)
    return r.json()["observations"][0]["value"]
```

walk-forward 시 매 step t 마다 asof_dt = t 로 호출 → t 시점에 알려진 값만 사용. lookahead 차단.

### 3.3 기존 raw/fred/ 적재 코드 확장 시 영향

- 기존 코드 = `series/observations` 만 호출 (현재 vintage = final revision 값) → CSV 박제.
- 확장 = `realtime_start`/`realtime_end` 파라미터 추가 + epoch 별 vintage 별도 CSV 저장 (`raw/fred-alfred/{sid}_vintage_{YYYYMMDD}.csv`).
- 비용 = API rate limit (120 req/min) + storage 5x ~ 10x.

---

## §4. M3 frame 한정 PIT 영향 평가

### 4.1 M3 분석의 PIT 정합 자가 점검

| Cell | M3 frame 분석 | PIT 위반 risk |
|---|---|---|
| us10y β | DGS10 final | ✅ revision 없음 → zero |
| dxy β | yfinance final | ✅ revision 없음 → zero |
| oil β | yfinance final | ✅ revision 없음 → zero |
| Epoch 경계 | M1 timeline (release-date 기준 ★ 자체 정합) | M1 timeline 의 PIT 정합 신뢰 → 본 layer skip |

★ **결론 5**: M3 frame 의 거시연관 분석 = PIT 정합 (M1 timeline epoch 경계 신뢰 + driver 3종 revision 없음). AUDIT-GUIDE D 축 hard-fail risk **없음** (M3 frame 한정).

### 4.2 H 가설 검증의 PIT risk (별도)

- H3 (CFNAI) = ★ALFRED 적용 필요 (monthly revision). 현재 final revision 사용 → minor lookahead bias 가능. ALFRED 적용 후 재검증 필요.
- H4 (VIX) = ✅ revision 없음 → PIT 정합.
- H5 (rate beta) = DGS10 사용 → ✅ PIT 정합.

---

## §5. 권고

### 5.1 단기 (즉시)
- **M3 frame 거시연관 = ALFRED 적용 skip 가능** (driver 3종 revision 없음). PIT 정합 박제.
- **H3 (CFNAI) = ALFRED 적용 필요**. CFNAI 의 vintage CSV 별도 적재 + walk-forward 재검증.

### 5.2 중기 (collector 적재 후)
- **monthly economic indicators 5종 (CFNAI/NEWORDER/AMTMNO/BUSINV/DGORDER)** = ALFRED vintage 적재 — H 가설 후속 round 진입 시 PIT 정합 보장.
- **HY OAS (BAMLH0A0HYM2)** = ALFRED 적용 무관, 가용 시작 2023-05 한정 → 장기 frame 활용 불가. AAA/BAA 일별 yield (revision 없음) 로 credit signal 대체 검토.

### 5.3 장기 (frame 확장 시)
- 장기 frame 확장 시 monthly 시리즈 = ALFRED vintage 의무 (final 사용 = lookahead bias). walk-forward backtest 코드에 ALFRED loader 통합.

---

## §6. main 합의 요청 (item6 회신 candidate)

```
[item6 사전조사 결과]
- M3 frame 거시연관 driver (us10y/dxy/oil) = real-time market data, revision 영향 zero → ALFRED skip 가능 (PIT 정합 박제)
- ALFRED critical = monthly economic indicators 5종 (CFNAI/NEWORDER/AMTMNO/BUSINV/DGORDER)
- API endpoint = FRED series/observations + realtime_start/realtime_end (또는 vintage_dates)
- 즉시 적용 가능 = H3 (CFNAI vintage) 재검증, 다른 4종 = collector 확장 후 H 가설 후속 round
- HY OAS (BAMLH0A0HYM2) = 2023-05 부터 가용, 장기 frame 활용 불가 → AAA/BAA spread 대체 검토
```

---

## §7. 한계·미해결

1. 기존 raw/fred/ 17 CSV 중 BAML credit yield 9종 (AAA/BAA/AAAFFM/BAAFFM/BAA10Y/AAA10Y/BAMLC0A0CM 등) revision 패턴 = csv 확인 후 정확 판정 필요 (현 추정 = 일별 yield 라 revision 거의 없음).
2. FRED API key 확보 + rate limit 관리 = collector 확장 시 인프라.
3. walk-forward backtest 코드 = ALFRED loader 통합 시 storage 5x~10x 증가 (vintage 별 별도 CSV).
4. M1 timeline epoch 경계의 PIT 정합 = M1 layer 자체 정합 신뢰 (이 layer 재검증 skip).
