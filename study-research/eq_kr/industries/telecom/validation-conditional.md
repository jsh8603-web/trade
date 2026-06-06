---
tags: [type/validation, domain/equity, sector/telecom, scope/equity-kr]
date: 2026-06-05
purpose: 통신 측정 상세 — (A) service 시계열(frame M2, 금리 duration) + (B) equipment cross-sectional. raw = raw-v3/validation-*.json.
---

# 통신(telecom) validation — 측정 상세

> ★2 archetype 분리(frame §1.6): (A) 통신서비스 3사 = cross-sectional INSUFFICIENT → 시계열 / (B) 통신장비 10종 = cross-sectional.
> raw 재현: raw-v3/{collect_telecom_cycle, measure_telecom, measure_robustness}.py → validation-telecom-v3.json + validation-robustness-v3.json

## 0. data-gate (측정 前 박제)
- 통신 universe 77종. strict floor(시총3000억∧ADV30억, battery/auto/refining 동일) 통과 = **service 3종 + equipment 10종**.
- **통신서비스(service)**: SKT(017670)/KT(030200)/LGU+(032640) = ★3사 과점. cross-sectional Spearman IC(min 8종) ⛔불가 = **INSUFFICIENT**(정유 2종 패턴 동형). → frame M2 산업 시계열.
- **통신장비(equipment)**: 한화비전(489790)/RFHIC/케이엠더블유 등 10종 ≥8 = cross-sectional 가능. ★단 cyclical 이질(service defensive 와 pool 금지).
- ★ARPU/5G 가입자 = MSIT/통계청 무료 time-series API 부재 = data-gate(미측정). 배당수익률 = DART 배당 line 미수집 → KR10Y 금리 민감도로 duration 직접.

## 1. (A) 통신서비스 3사 시계열 — 배당주 duration (★핵심 가설)

### 1.1 KR 금리 duration — ★약/INCONCLUSIVE (가설 미확인)
panel = SKT/KT/LGU+ 동일가중 월수익(n_months=88, 2019-01~2026-05). driver = KR 10Y 국채 yield(IRLTLT01KRM156N).

| 측정 | rho | wc_p | t_eff | n | 판정 |
|---|---|---|---|---|---|
| 동시 KR10Y Δ | +0.073 | 0.473 | 0.68 | 88 | 비유의 (★duration 음 prior와 반대 부호) |
| forward 1M KR10Y level | +0.061 | 0.585 | 0.57 | 88 | 비유의 |
| forward 3M KR10Y level | +0.007 | 0.945 | 0.03 | 86 | 비유의(≈0) |
| forward 1M Δrate | +0.182 | 0.066 | 1.62 | 88 | marginal (★양=duration 음 prior와 반대) |
| horizon 20d KR10Y level | -0.239 | 0.101 | -1.72 | 53 | marginal (★유일하게 duration 음 방향) |

- ★**부호 모순**: 배당주 duration 가설 = KR10Y↑ → 통신 forward 음(-). 실측 = 대부분 ≈0 또는 양(+, Δrate fwd1m +0.18). 유일하게 horizon 20d level rho=-0.24(음 방향, 비유의 marginal).
- **walk-forward OOS** (KR10Y level → fwd3M): IS(2019-22)=-0.324 / OOS(2023-26)=-0.117 (sign_hold 음) ★but full sample=+0.007 = 부호 episode-driven 불안정.
- **leave-episode**(2020 covid 저금리 + 2022 인상 제외): rho +0.170 (full +0.007과 부호 역전) = 신호 episode 의존.
- **ADF**(§1.7): KR10Y level **I(1) p=0.808 비정상** / Δrate I(0) p<<0.001 / service fwd3 ret I(0) p=0.40. → level-on-level spurious 위험.
- **Δ 단위 재정식화**(robustness): level fwd3 rho=+0.007(I(1) spurious) vs Δ fwd3 rho=+0.114(양) → 둘 다 ★duration 음 prior와 반대 부호(부호 일관하나 prior 위배).
- **금리 상승기/하락기 split**: up(Δ>+5bp) rho=-0.125(n=37) / down rho=-0.092(n=26) = 약한 음(duration 방향)이나 n 작고 비유의.
- **family_2 interaction**(A-5): KR10Y level forward × Slowdown = b_inter +0.019, t=0.99 비유의.
- **regime conditional**(powered): macro=Reflation rho=+0.503(wc_p=0.0075) but ★underpowered(n=22) / macro=Recovery +0.187, Slowdown +0.004 / flow=strong_buy +0.366(underpowered n=18). = 금리상승·reflation 국면서 통신 양(+, duration 음 prior와 반대 = bond-proxy 약화 가능성, episode-poor).
- **placebo**: random rho=+0.058 wc_p=0.567 비유의 = 측정 파이프 정상.
- ★**verdict: INCONCLUSIVE/약** — 배당주 duration(금리↑→통신 forward 음) 가설 **미확인**. 전 horizon 비유의 + 부호 prior와 반대(대부분 양) + horizon 20d만 음 marginal. = ★bond-proxy duration = 2019-26 표본서 **약**(저금리→인상 single cycle, n_episode 부족 = §1.2 episode-poor TENTATIVE 격하). risk-monitor 조차 부호 불안정 → 종목선택 신호 아님 + 산업 timing도 비채택.

## 2. (B) 통신장비 cross-sectional — cyclical (10종)

### 2.1 PBR value premium — ★PASS-conditional but size-confounded
universe = 10종(한화비전/RFHIC/케이엠더블유 등). avgN=9.2.

| horizon | IC | wc_p | t_eff | avgN | n_months | 판정 |
|---|---|---|---|---|---|---|
| y_5d | -0.078 | 0.018 | -1.95 | 9.2 | 84 | 음(value) marginal |
| y_20d | -0.078 | 0.018 | -1.95 | 9.2 | 84 | 음(value) marginal |
| y_60d | -0.167 | 0.0005 | -2.62 | 9.2 | 82 | ★강 음 = **BY 생존** |

- **BY-FDR**(단일 family m=24): survivors = **[eqp_y_60d_pbr_z]** (raw_p_min=0.0005). = 통신 유일 BY 생존 신호.
- **LOO 종목**(60d): full=-0.167, 10종 drop range [-0.195, -0.150] 전부 음 = 단일종목 의존 아님. 한화비전(489790, 최근상장 404일) drop=-0.165 = outlier 아님.
- **within-period**: 월별 IC 음 비율 67.1%.
- **walk-forward OOS**(pbr_z 20d): IS=-0.041 / OOS=-0.119 (sign_hold 음) = OOS 강화.
- ★★**size confound (CRITICAL, G-A A-4)**: pbr_z ↔ size_z cross-sectional 상관 +0.554(저PBR↔소형). **size-neutral IC(60d) = -0.053**(raw -0.167 대비 ★68% 축소). → ★PBR value premium 의 대부분이 **소형주 효과** = 순수 value 신호 약. 통신장비 = KOSDAQ 소형 10종 = value≈size 분리 어려움.
- **verdict: TENTATIVE/PASS-conditional** — raw 저PBR value premium 방향 강(BY 생존, LOO robust, OOS 강화) ★but size confound 제거 후 IC -0.05 marginal = 순수 value 약. = 사실상 소형주 premium. + KOSDAQ 소형 capacity 제약(J축). → conservative cap + size 분리 주의.

### 2.2 momentum — 무신호
- mom_12_1 z: y_5d/20d IC=-0.021(wc_p=0.63), y_60d -0.067(wc_p=0.15) = 전부 비유의. ★prior(양) 와 부호 반대 약 + 비유의 = 무신호.
- verdict: INSUFFICIENT/무신호.

### 2.3 PER — underpowered
- per_z: avgN=6.3(흑자 한정, 138/215 공시만 흑자). y_60d IC=-0.132(wc_p=0.057 marginal) but ★underpowered(avgN<8). 적자 빈발 KOSDAQ 소형.
- verdict: INSUFFICIENT/underpowered — 방향(음=value) 힌트 but avgN 6.3 협소 = 단정 불가.

## 3. cross 축 (A-3, 빈[] 금지 충족)
- common_factor_exposure(service, 6/3 raw validation-cross-v3.json): dollar β=-1.44(t=-1.55 비유의, CI 넓음) / VIX β=-0.003(비유의) / rate/oil/credit = raw 참조.
- directional_spillover: KR10Y level 선행 약(service forward ≈0). DY 정식분해=supervisor. ★service 선행신호 후보 = 금리 duration(약, 미확인).
- structural_linkage: service(통신사 capex) → equipment(장비). 내부 supply-chain이나 ★service 3종 협소 + equipment 소형 = customer-supplier momentum 측정 무의미. supplier=글로벌 통신장비(화웨이/에릭슨/노키아) scope 외.
- placebo: service random rho=+0.058 p=0.567 비유의 = 파이프 정상.

## 4. FDR family (단일, 5가설 사전고정 → measure m=24 powered cell)
단일 BY family(service 시계열 + equipment cross-sectional 통합) m=24, by_factor=3.776. survivors = **[eqp_y_60d_pbr_z]** 1개(raw_p_min=0.0005). service 신호 = BY 미생존(전 cell wc_p>0.10 또는 비유의) = 배당주 duration 약 정직 확정.

## 5. 종합 verdict (small-n rule, n<30/episode-poor hedge)
- ★(A) **통신서비스 = INCONCLUSIVE/약** — cross-sectional INSUFFICIENT(3종) + 금리 duration 시계열 미확인(부호 prior와 반대 대부분, 전 horizon 비유의, level I(1) spurious, episode-poor single cycle). = 종목선택 0 + 산업 timing 비채택(부호 불안정).
- (B) **통신장비 = TENTATIVE** — 저PBR value premium raw BY 생존 but ★size confound 제거 후 -0.05 marginal = 사실상 소형주 효과. momentum 무신호. per underpowered. = conservative cap(size 분리 주의 + KOSDAQ capacity 제약).
- **G-G = FAIL~PASS-conditional 경계**: tradeable = equipment pbr_z 1개(size-confounded, conditional). service = 0. supervisor 최종판정.
- ★over-claim 회피: service 3종 + episode-poor = 배당주 duration 단정 금지. equipment size confound 정직 박제(value≠순수). n<30/small-universe hedge 극대.
