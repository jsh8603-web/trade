---
tags: [type/research-log, domain/equity, sector/chemical]
date: 2026-06-05
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용.
---

# chemical 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| universe | FDR KRX-DESC 키워드("화학") | ❌ 부정확 — 현대차/에코프로(2차전지)/CJ(식품)/아모레(화장품)/동진쎄미켐(반도체소재) 혼입 | KSIC Industry도 화장품/반도체소재/2차전지 혼입 | ★frame M.11 교훈 재확인: 키워드/KSIC 부정확 → **명시 코드 화이트리스트 필수** |
| universe (최종) | 명시 화이트리스트 22종 → floor-passed 17 | ✅ 순수 석유화학+정밀화학 | ✅ 17종 | 정유(S-Oil/SK이노)=refining 별 capsule 제외 / 화장품·반도체소재·2차전지=별 archetype 제외 |
| prices | pykrx OHLCV loop | ✅ 17종 1818일 (KRX 로그인 실패 경고 있으나 OHLCV는 작동) | ✅ | semi/battery 동일 — 스냅샷 API만 차단, OHLCV loop OK |
| valuation (PBR/PER) | pykrx 스냅샷 | ❌ KRX 인증 차단 | DART fnlttSinglAcntAll PIT 재구성 | semi/battery 공통 경로. equity/net_income/assets |
| capex/inventory | DART 유형/재고/무형자산 (collect_dart_extended) | ✅ 442 rows, coverage ppe 100%/inv 97%/assets 98% | ✅ | rcept_dt PIT, resume/incremental |
| regime | FRED CLI/DEXKOUS + ECOS 외국인순매수 | ✅ (semi collect_regime 그대로 재사용 — 거시 산업 무관) | ✅ | 36셀 N<24 = 단일축 측정 |
| cycle 선행 (DY) | oil(WTI)/VAW/XLB lagged momentum | ✅ 측정 but null | skip 기록 | 유가-화학 spread 매개라 직접 선행 약 |

## 막힘·해결 로그 (시계열)

- [2026-06-05 10:30] 막힘: FDR "화학" 키워드 매칭 → 현대차/에코프로/CJ제일제당/아모레/반도체소재 대량 혼입 → 진단: 화학 KSIC가 화장품·반도체소재·2차전지소재 포괄 → 해결: **명시 코드 화이트리스트 22종**(석유화학 commodity + 정밀화학, 화장품/반도체소재/2차전지/정유 제외) → 교훈: frame M.11 "universe 화이트리스트 필수" 화학에 재확인. 산업 정의 = cycle driver(에틸렌-납사 spread) 본질로 좁힘
- [2026-06-05 10:45] DART collect_dart.py + collect_dart_extended.py = universe.parquet 기반이라 산업 무관 그대로 복사 동작. resume/incremental로 background 안전(17종 5분 내 완료)
- [2026-06-05 11:00] 막힘: bash 변수 `$DST/...` 경로에 backslash 섞여 FileNotFoundError → 해결: `cd` 후 상대경로 사용. 교훈: Windows 경로 + bash 변수 확장 주의, cd 후 상대경로 권장
- [2026-06-05 11:15] ★capex_ratio 측정 = auto와 정반대(IC≈0 vs auto -robust). 진단(정밀): 종목별 capex 분산은 존재(CV 0.241)하나 panel n_obs=1312 powered인데 IC≈0 = forward 예측력 부재(측정 못함 아님). 해결: REJECTED 박제 + 정밀 진단. 교훈: ★capex 유효성은 산업구조 단정 아니라 forward 예측력 실측 의존 — steel within=0.96 selection 유효(반례), 화학은 분산 있어도 forward 무예측. 자산집약≠capex 종목 selection 유효

## 측정 방법 결정 로그

- **universe 화이트리스트**: KSIC/키워드 부정확 → 명시 코드. cycle driver(석유화학 spread) 본질로 정의. LG화학/한화솔루션 신사업 혼입 인지(SOTP noise)하되 유지(화학 대표).
- **capex 측정**: cross-sectional z(ppe/assets) → forward IC. auto 미러. ★auto 인계 최우선 가설 — 결과 REJECTED 정직 보고(이연 금지, 측정 후 verdict 박제).
- **valuation PER vs PBR**: cyclical prior = PBR○ PER✗(peak-EPS). ★측정 결과 PER○ PBR약 = prior 반대 발견 → 정직 보고(가설과 다른 결과도 박제). size-orth 병기(small-cap value 절반 노출).
- **conditional surface**: 단일 FDR family 사전고정(6신호×3h×regime cell). 측정 후 family 재정의 금지. BY 생존 = mom/vol y_60d.
- **net-cost**: KR STT sell 0.20% 비대칭. small-n no-trade band + CPCV 캘리브 필요 명시(점추정 박제 금지).
- **small-n 정직성** (frame M.12): n=17 → magnitude 50-70% haircut, size-orth IC 병기, 24M degenerate 강등.

## 미해결 / 다음 세션 우선 작업

1. ★에틸렌-납사 spread 수집 (ICIS/KPIA) — 화학 cycle timing 변수 최대 gap. spread 모멘텀이 regime 변수로 vol/mom 강화하는지 측정.
2. capex 일반화 가설 = 시계열(산업 timing) capex로 재측정 (현 cross-sectional만 기각 — 산업 capex cycle이 산업 forward timing 예측하는지).
3. PER value premium > PBR mechanism 확정 — 화학 EPS 변동 진폭 vs 반도체 비교 (peak-EPS trap 화학 약 이유).
4. PIT universe 멤버십 확장 (생존편향 보정) → n 확대 후 small-n 신호 재측정.
5. 중국 화학 PMI/수입가 regime 변수 (구조적 역풍 정량화).

## ROTATION 측정 로그 (업종 비중 timing, 2026-06-05 추가)

- [2026-06-05] rotation 임무 = 화학 업종 자체 비중 timing (종목 selection과 별 차원). _rotation v2 baseline = naphtha_yoy -0.367 (cost-push, TENTATIVE). team-lead 가설 = naphtha 단독보다 NCC spread/중국 수요가 본질.
- 막힘: NCC 에틸렌-납사 spread = ICIS/Platts 유료 무료부재 → 해결: China demand(FXI/MCHI yoy) + spread proxy(z(china)−z(naphtha) = margin) 대리 측정. 교훈: 본질 driver(demand)는 proxy로도 입증 가능.
- ★측정 결과 (업종 eq-weight forward y_60d, n=88): china_mchi_yoy +0.458(OOS robust) / spread +0.450(OOS robust) / china_fxi +0.347(OOS robust) > naphtha -0.375(OOS mag약). 전부 prior 부호 일치 + placebo p 0.002 + LOY 일관.
- ★이론 검증(증권 컨센서스, Gemini 종합): 키움 이동욱/NH 윤재성/신한 이진명 = "중국 수요(demand-pull) 본질, 나프타 cost-push 변동성, 스프레드 통합 KPI". = 측정과 완전 일치 = data mining 아님(이론+통계 수렴).
- ★측정 방법 결정: naphtha 단독(v2) 강등 → China demand/spread를 primary 승격. spread_proxy(z 차이)가 통합 지표로 +0.450, non-overlap +0.552 강화 = 증권 "스프레드가 수요-원가 통합" 정합.
- 판정 = PASS-strong. 단 underpowered(t_power<2.802, n=88) → 부호·방향 한정 + gated default.
