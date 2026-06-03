# round-N — 자동차(auto) S3 외부검토 라운드 (2026-06-04, skip-with-coverage)

> frame §A (6 프로세스) S3 = "gemini+claude 병렬 자문 + falsification 검토 → round-N.md" (frame L33).
> 본 라운드 = ★사후 자문 흡수 박제 (skip-with-coverage). 별도 자문 polling 대신 frame §M.12 가 이미 auto/financial/telecom 누락분을 사후 자문(gemini+claude 수렴, 2026-06-04)으로 S3 흡수했음을 기록.
> SSOT = `study-research/frame-v3-draft-industry-dispatch-20260603.md` §M.12.

## §1. S3 외부검토 = §M.12 사후 자문으로 흡수 (skip 사유)

frame §M.12 (L316-326) 헤더: "6단계 S3(외부검토) 누락분(auto/financial/telecom) 사후 자문 + S6 독립 cross-audit + 24M overlap 코드 점검 종합. ★전 산업 공통 정정 = 감사 방어 의무."

= auto 의 S3 외부검토는 §M.12 가 **gemini+claude 2R 수렴**으로 이미 수행. 본 산업 카드는 그 4결론을 흡수·반영(Phase 1 audit 완료). 추가 자문 polling = 채널 경합 회피(frame §5 round-N 권고).

## §2. §M.12 자문 4결론 인용 + auto 적용점

### 결론 1 — 24M_value = degenerate (전 산업 강등)
- 인용(§M.12): "24M forward를 월간 샘플링하면 창이 23/24 겹침 → eff_indep_N = n_months/24 ≈ 2.5. NW lag=24(충족)여도 t는 구조적 과대(auto pbr t=−17.6 = small-universe[13~17종] × 24M overlap 이중 inflation, 역설 = t 최대인데 증거 최약)."
- ★auto 적용: cs_pbr_z_24m (t=-17.59) = §M.12 가 직접 지목한 사례. Phase 1 에서 24M → 보조(degenerate) 강등, primary = 3M/6M/12M(전부 NW 유의 + BY 4생존) 재배치 완료. magnitude+significance 둘 다 overlap inflation = 방향만.

### 결론 2 — small-n magnitude 정직성 (EB/James-Stein shrinkage)
- 인용(§M.12): "n<20 cross-sectional Spearman t는 협소 universe artifact. 점추정 magnitude 50~70% haircut(EB/James-Stein shrinkage: ρ−0.46 → posterior −0.12~−0.20 권역) 또는 breadth-adjusted IR(IR=IC·√breadth) 병기 의무."
- ★auto 적용: §M.12 의 worked example(ρ−0.46 → posterior −0.12~−0.20)이 **auto cs_pbr_z 점추정**. Phase 1 에서 `magnitude_haircut` 필드로 posterior 권역 + breadth-IR 식 병기 완료(n=14<20).

### 결론 3 — peak-EPS trap 메커니즘 정정
- 인용(§M.12): "1차 원인 = 적자 아니라 earnings cycle 진폭(흑자 기업도 peak EPS 高→저PER trap 작동). 적자비율은 2차 증폭기. ⛔시총에 인과 귀속 금지(size factor 혼동). PER → E/P(earnings yield) 또는 Gross Profitability/PCFR 대체 권고."
- ★auto 적용: cs_per_z 횡단면 무신호(IC≈0) = peak-EPS trap. Phase 1 에서 메커니즘 정정(earnings cycle 진폭 1차, ⛔시총 인과 금지, E/P 대체 권고) 반영. EV/EBITDA 대체 = collector_plan high.

### 결론 4 — financial regime-conditional = hypothesis-generating only (overfit)
- 인용(§M.12): "37개월 rate_up/down split = regime당 ~18개월, independent episode ≈2 = overfit. ⛔confirmed 불가·live 제외."
- ★auto 적용: auto 는 regime-conditional 신호 없음(가격 momentum 전부 비유의). 본 결론은 financial 직접 적용이나, auto 도 향후 regime split 측정 시 동일 overfit 게이트(independent episode ≥ 2 cycle) 준수 의무로 기록.

## §3. 본 라운드 self-check
- ★본 라운드 = 정량 추가 산출 0 + 신규 자문 0 (frame §M.12 가 S3 흡수). ★skip-with-coverage 박제 = idle 아님.
- §M.12 4결론 → auto 카드 반영 = Phase 1 audit 완료(degenerate 라벨 + primary 재배치 + magnitude_haircut + hedge 어휘). 매핑표 = `.harness2/artifacts/phase-1/m12-card-reflection.md` 3행.
- 다음 라운드 권고: DART EV/EBITDA 실측(collector_plan high) 확보 후 cyclical primary_metric 측정 → 결과 격하 시 cross-verify 1회.
