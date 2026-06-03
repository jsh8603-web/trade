# validation-v3-cross-sectional.md — us_mega_tech sleeve §M v3 (cross-sectional)

> frame v3 §M.1~M.7 + ★§M.12 정정(eff_N/breadth-IR/magnitude haircut/24M degenerate). raw 재현: `raw-v3/*.py`.
> us_cyclical/us_defensive + auto/consumer 미러. ★compounder = expensive_trap(고PER 정상) = us_cyclical/defensive 와 valuation 가설 반대.
> ★핵심 = vol_60 저변동성 quality dominant + PER 무신호(expensive_trap 정합) + VIX 고베타 + reflexivity monitor(H9).

## §0. 데이터

| 데이터 | 상태 | 비고 |
|---|---|---|
| yfinance 11종 OHLCV | ✅ 작동 | Mag7+AVGO/AMD/ORCL/ASML, 2015-2026, 2867일 |
| EDGAR XBRL (equity/net_income/shares/★capex) | ✅ 작동 | 6630 rows, 11종, filed PIT. ★capex=H6 AI capex |
| FRED CSV (real_rate/rate/dollar/VIX) | ✅ 실데이터 | eq_us_defensive/raw/fred 재사용 |

## §1. universe (§M.6, ★custom basket)

- ★sleeve = Mag7 custom basket(AAPL/MSFT/NVDA/GOOGL/META/AMZN/TSLA + AVGO/AMD/ORCL/ASML) = **GICS 파편화로 sector ETF 합산 불가** → 사용자 SSOT basket.
- ★**n=11 = 횡단면 avg_N 11 small-basket** = small-n hedge 강(magnitude haircut + breadth-IR 병기 의무, §M.12). n=123개월(2015~).
- survivorship 약(mega-tech 상폐 거의 없음) 단 PIT 멤버십(NVDA pre/post-AI, TSLA 2020 편입) = collector_plan.

## §2. forward 횡단면 Rank-IC (★§M.12 eff_N)

16 테스트(4 신호 × 4 horizon):

| signal__horizon | IC | t_NW | n_mo | p_NW | CPCV | block-boot CI | avg_N |
|---|---|---|---|---|---|---|---|
| **vol_60 → 12M** | **+0.241** | **3.10** | 123 | 0.002 | 1.00 | **[0.104, 0.366]** | 11.0 |
| **vol_60 → 6M** | **+0.171** | **2.57** | 129 | 0.011 | 0.93 | **[0.044, 0.304]** | 11.0 |
| vol_60 → 3M | +0.083 | 1.84 | 132 | 0.068 | 0.73 | — | 11.0 |
| mom_6 → 1M | +0.050 | 1.56 | 130 | 0.121 | 0.93 | [-0.014, 0.097] | 11.0 |
| (mom 나머지) | \|IC\|<0.05 | \|t\|<1.1 | — | >0.3 | — | 0 포함 | 11.0 |

★**핵심 발견 — compounder quality**:
- **vol_60 → 12M (저변동성 quality) = 유의**: IC +0.241, t=3.10 p=0.002, ★NW+block-boot CI 둘 다 0 배제. ★eff_N=123/12≈10.2(degenerate 아님). within 0.73, leave-episode 생존(ex-peak +0.196). vol_60→6M 도 IC +0.171(within 0.91 더 robust).
- ★**compounder 해석**: 저변동 = AAPL/MSFT 안정 mega-cap(복리 quality), 고변동 = AMD/투기적 → ★안정성이 outperform = compounder quality 프리미엄.
- **momentum 약 양**(+0.05, 비유의) = growth persistence 약. ★battery 양 momentum 동방향이나 약.
- ★**BY 미생존**(n=11 basket, raw_p 0.0024 < but BY 임계). ★**magnitude(0.241) literal 금지 → breadth-IR=IC·√(11×10.2)=2.56 병기 + 50-70% haircut(§M.12)**.

## §3. 4게이트 (§M.2)

**primary = vol_60 → 12M**:
- **G1 ex-ante**: NDX yoy regime(bull 84 / neutral 45 / bear 8 month) = tech cycle ex-ante. compounder bull 편중. 달력컷 아님.
- **G2 BY-FDR**: 16 테스트. raw_p_min=0.002(vol_60 12M). ★BY 생존 0(n=11 basket small-n). = 방향 유의(NW p=0.002)하나 다중검정+small-n hedge.
- **G3 CPCV**: vol_60 12M OOS hit=1.00. in-sample 부호 OOS 재현.
- **G4 NW HAC + block-boot(block=12M=horizon, §M.12)**: t=3.10, NW CI [0.089, 0.394] + block-boot [0.104, 0.366] 둘 다 0 배제.

★게이트 종합: NW+boot+CPCV+leave-episode 통과 but ★BY 미생존 + n=11 basket = **PARTIAL CONFIRMED + magnitude hedge**.

## §4. robustness (★§M.12 small-n)

- vol_60 → 12M: leave-episode 생존(ex-peak +0.196), within 0.73(6M 0.91), eff_N 10.2(Validated). ★block=horizon 비례(§M.12).
- ★**small-n magnitude hedge**: n=11 basket = IC 0.241 literal 인용 금지. breadth-IR=2.56 병기 + EB-shrinkage 50-70% haircut(점추정 단정 회피).
- ★24M_value = eff_N≈4.7 degenerate 라벨(§10 valuation).

## §5. cross 축 (§M.3 — 산업=보고만)

### (a) 공통인자 β (HAC maxlags=6, n=36)
- ★**VIX β = 유의 음**: MEGA_TECH_ALL -0.008(t=-2.5), **mag7 -0.007(t=-4.0 강)** = ★VIX 상승(risk-off) 시 mega-tech 약세 = **고베타 risk-on 성장주**. = compounder dominant 공통인자.
- real_rate β: MEGA_TECH_ALL -0.030(t=-0.2 비유의), ai_semi -0.245(t=-0.7 약 음, 성장 듀레이션). ★mag7 +0.007 무 = us_defensive utilities(-0.213 강 듀레이션)보다 약 = mega-tech은 금리보다 risk sentiment 노출.
- rate/dollar = 비유의. R²=0.52(ALL). ⚠️ n=36 small hedge.

### (b) ★H9 reflexivity monitor (mega-tech 고유, supervisor throttle 입력)
- intra-Mag7 60d rolling corr: full **0.45** / recent 0.355 / p75 0.534. n_high_corr(>0.70) = 36 month.
- breadth EW-top3 3M spread: recent **+0.081**(양 = breadth 넓음, top3 주도 아님).
- ★**현재 정점 아님**(corr<0.70 AND breadth 양) = cap-down 미발동.
- ★cap-down rule: intra-corr>0.70-0.75 AND breadth<-3~-5%p 동시 → supervisor gross cap-down(de-risk throttle, §M.3 DY 채널).

### (c) structural_linkage (H6 AI capex)
- capex/equity intensity cross-sectional(§10) = 약 음(-0.087 비유의) = AI capex→fwd EPS 약. fwd EPS proxy 필요(collector_plan). hyperscaler capex→반도체 lead-lag = supervisor DY 단계.

## §6. exposure card (§M.7)

universe 11종 peer-relative z(저변동성 상위 = compounder quality):

| ticker | sub | vol_60_z | mom_6_z | mom_12_1_z |
|---|---|---|---|---|
| AAPL | mag7 | -1.34 | -0.27 | -0.30 |
| MSFT | mag7 | -0.95 | -0.87 | -0.97 |
| AMZN | mag7 | -0.81 | -0.15 | -0.39 |
| ... | | | | |
| AMD | ai_semi | +2.22 | +2.76 | +2.35 |

★vol_60 IC 양(저변동→고forward) → 저변동성(AAPL/MSFT 안정 mega-cap) overweight. ★n=11 small-basket z 안정성 낮음 hedge.

## §7. net-cost (§M.4)

★US mega-cap 최저비용(STT 없음, 최고유동성): 왕복 14bps / 월 7bps. |IC| 0.241 >> 7bps → net 보존 강(magnitude hedge).

## §10. ★valuation 횡단면 (§M.7 — EDGAR XBRL PIT, ★§M.12)

EDGAR XBRL(equity/net_income/shares/★capex) 6630 rows + yfinance → PBR/PER/capex cross-sectional z. PBR cov 1151/PER 1041/capex 1145 cells, avg_N 8종.

★**compounder = expensive_trap**: PER value premium **반대**(저PER value 아니라 고PER 정상 = growth-duration). ★block=horizon, 24M=eff_N degenerate.

| signal__horizon | IC | t_NW | eff_N | p_NW | breadth-IR | verdict |
|---|---|---|---|---|---|---|
| pbr_z → 12M | -0.167 | -1.58 | 10.4 | 0.118 | -1.55 | TENTATIVE (value 방향, 비유의) |
| pbr_z → 6M | -0.127 | -1.74 | 21.8 | 0.084 | -1.72 | borderline (value 방향) |
| pbr_z → 3M | -0.087 | -1.92 | 44.7 | 0.056 | -1.69 | borderline (raw_p 0.056) |
| ★per_z → 3M/6M/12M | ≈0 (-0.001/+0.026/+0.013) | \|t\|<0.5 | — | >0.6 | ≈0 | ★INSUFFICIENT = 고PER 정상(expensive_trap 정합) |
| capex_z → 12M | -0.087 | -0.99 | 10.4 | 0.325 | -0.81 | TENTATIVE (H6 약) |
| pbr_z → 24M_value | -0.115 | -0.89 | **4.7** | 0.376 | -0.72 | ★DEGEN (eff_N degenerate, 방향만) |

- ★**PER 무신호 = compounder expensive_trap 정합**(고PER 정상, value premium 없음) = `core/structure/archetype.py` compounder 정의 입증.
- PBR 약 value 방향(음, 비유의 borderline). capex 약 음(H6 AI capex→fwd EPS 약).
- BY 생존 0(9테스트 24M 제외). ★24M_value eff_N 4.7 degenerate(§M.12 primary 강등).
- ★결론: compounder valuation = value premium 없음(archetype 정합). dominant = vol_60 quality.

## §9. verdict

- **primary (cs_lowvol → 12M, 저변동성 quality)** = **PARTIAL CONFIRMED**: IC +0.241, t=3.10 p=0.002, NW+boot CI 0 배제, CPCV 1.00, leave-episode 생존, eff_N 10.2. ★BY 미생존(n=11) + magnitude breadth-IR 2.56 병기(haircut §M.12).
- **momentum** = 약 양(growth persistence, 비유의).
- **valuation** = ★PER 무신호(expensive_trap 정합) + PBR 약 value(비유의) + capex 약. value premium 없음 = compounder archetype 입증.
- **common factor** = ★VIX 고베타(t=-4.0 mag7), real_rate 듀레이션 약. ★H9 reflexivity = supervisor throttle 입력(현 정점 아님).
- **sleeve 전체 = PARTIAL** — vol_60 quality dominant(magnitude hedge), PER 무신호 expensive-trap 정합. archetype compounder 지지.
