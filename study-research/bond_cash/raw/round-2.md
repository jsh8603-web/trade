---
tags: [type/raw, domain/inv, asset/bond, asset/cash, phase/study, round/2]
date: 2026-05-30
round: 2
topic: Investment Clock 4국면 × 채권/현금 자산군 거동
source: WebSearch (native fallback)
---

# Round 2 — Investment Clock 4국면 × 채권 자산군 거동

## 검색어
`Investment Clock fixed income asset allocation reflation overheat stagflation bond returns`

## 원천 (URL hyperlink)
- [Investment Clock — Trevor Greetham 원전 (KS3 archive)](https://ks3-cn-beijing.ksyun.com/attachment/114caaf9991619a15e81a0a4b590837f)
- [Merrill Lynch's Investment Clock for Smart Investing (Lemon8)](https://www.lemon8-app.com/pixiuinvest/7293127488471908865?region=sg)
- [How to Invest through the Good and Bad times — Part I (Richard L, Medium)](https://medium.com/@richardhwlin/how-to-invest-through-the-good-and-bad-times-part-i-d89bf000da8e)
- [How Does Investment Clock Work? (Richard L, Medium)](https://medium.com/@richardhwlin/how-does-investment-clock-work-c7d8fbbeb7bd)
- [The Investment Clock (Royal London for advisers)](https://adviser.royallondon.com/investment/our-investment-options/governed-range/governed-portfolios/investment-clock/)
- [What is Merrill Lynch's Investment Clock? (Moomoo)](https://www.moomoo.com/us/learn/detail-what-is-merrill-lynch-s-investment-clock-59567-220659016)
- [Investment Clock by Trevor Greetham (Dr Wealth)](https://drwealth.com/investment-clock-by-trevor-greetham/)
- [Investment Clock (RLAM)](https://www.rlam.com/uk/intermediaries/our-capabilities/multi-asset/investment-clock/)
- [The Investment Clock (Financial Sense)](https://www.financialsense.com/alex-barrow/investment-clock)
- [The Merril Lynch Investment Clock (Macro Ops)](https://macro-ops.com/the-investment-clock/)

## 핵심 정제

### 1) Investment Clock 4국면 정의 (성장 × 인플레)
| 국면 | 성장 | 인플레 | 우위 자산 | 채권 거동 |
|------|:---:|:---:|---|---|
| **Reflation** | ↓ | ↓ | **Bonds** | Bull (성장둔화·디플레 → real rate↓·기대인플레↓ → long-duration 강세) |
| **Recovery** | ↑ | ↓ | **Stocks** | Bear 초입 (성장 회복 → 금리정상화 압력) |
| **Overheat** | ↑ | ↑ | **Commodities** | Bear (인플레 → CB rate hike → bond yield 상승) |
| **Stagflation** | ↓ | ↑ | **Cash** | Bear (인플레↑+성장↓ double penalty) |

### 2) 명시적 채권 거동 (검색 결과 인용)
- **Reflation**: "stocks are suffering in a bear market, **but bonds are expected to be the most welcomed asset** thanks to the generous monetary and fiscal support" — sluggish growth + low inflation + 정책완화 → bond bull
- **Overheat**: "Rising inflation spurs the central bank to hike rates, **usually causing bond yields to increase**. The bond market enters a bear market." — name 인용 가능
- **Stagflation**: "you normally see **negative real returns from stocks and bonds** and commodities are your saviour" — 채권은 명목·실질 둘 다 손실. 현금/원자재가 방어.
- **TIPS (인플레이션 연계채)**: "inflation-protected bonds outperform conventional bonds during Overheat and Stagflation" — Overheat·Stagflation 에서 TIPS 가 명목채 대비 우위.

### 3) Cash 우위 조건
- Stagflation 에서 cash 가 top → 인플레 hedge 라기보다 *기회비용 최소화* + *옵션 가치* (다른 자산 다 하락).
- carry 가 정책금리에 연동 → CB 가 인플레 잡으려 인상하면 cash carry 도 상승 (양의 carry 유지).

## 우리 시스템 매핑 (regime_to_weights.py L74~79 인용)
```python
REGIME_DIRECTION = {
    RegimeLabel.REFLATION:   {... "bond": "top",     "cash": "neutral", ...},  # ✅ 일치
    RegimeLabel.RECOVERY:    {... "bond": "down",    "cash": "down",    ...},  # ✅ 일치
    RegimeLabel.OVERHEAT:    {... "bond": "down",    "cash": "down",    ...},  # ⚠️ 검색결과는 "cash=neutral~down" 정도. cash=down 과잉 가능
    RegimeLabel.STAGFLATION: {... "bond": "down",    "cash": "top",     ...},  # ✅ 일치
}
```

→ Overheat 에서 cash=down 은 검색 결과 ("CB rate hike → cash carry↑") 와 약간 모순. **검증 대상**:
   - cash sleeve return 이 Overheat 국면에서 실제로 음 alpha 인가? (Round 4 검증 대상)

→ TIPS 분리 채널 부재 — 현재 코드는 bond 하나로 묶음. **개선 제안**:
   - bond sleeve 안에 sub-archetype "real_duration" (TIPS) vs "nominal_duration" 분리 필요?
   - 또는 weight_rules 의 modulate_by 에 inflation_regime 추가 → Overheat 에서 TIPS 비중↑

## 가설 초안 (라운드 2)

**H2-A**: Reflation 국면에서 long-duration ETF (TLT) 의 60일 forward return 평균 > 전체 평균 + 통계적 유의.
   - 반증: regime-conditional t-test 가 0 가설 기각 못 함 (p > 0.10).

**H2-B**: Overheat·Stagflation 에서 TIPS (TIP ETF) 가 nominal long (TLT) 대비 상대 outperformance.
   - 반증: regime-conditional TIP-TLT spread 의 cumulative return 이 양수 분리 안 됨.

**H2-C**: Stagflation 에서 cash sleeve return ≈ short-term yield (positive nominal), bond sleeve return < 0. cash > bond 가 *유일*하게 일관된 국면.
   - 반증: 1990 년대 이후 Stagflation 라벨 기간에 cash − bond 의 1m forward return 분포가 0 중심.

**H2-D**: Overheat 에서 cash 가 다른 자산 대비 *현저한* 하락은 없다 (옵션가치 보존). 검증 대상.
   - 반증: cash return Sharpe < 0 in Overheat (현재 코드 REGIME_DIRECTION[Overheat][cash]=down 의 정당성).

## 검증 방향 초안 (라운드 2)
- NBER recession 일자 + Investment Clock 4국면 라벨 (CFNAI growth axis × T5YIE inflation axis) → regime-conditional forward return panel.
- TLT / IEF / SHY / BIL / TIP / HYG 일별가 → 60일 rolling forward return → 4국면 평균 비교.
- 가중치 prior: REGIME_DIRECTION 의 TILT_MULT (1.8/1.35/1.0/0.6) 가 데이터 분포와 정합한지 calibration.

## Gap / 라운드 3 로 넘길 질문
1. credit cycle (HY OAS) × 4국면 어떻게 얽히나 (Round 3)
2. carry trade · spread widening 의 trade-off (R3)
3. 검증 방법론: rank-IC, e-process 의 채권 strategy 적용 (R4)
4. cash optionality 정량화 + 한국 KTB 한국 특수성 (R5)
