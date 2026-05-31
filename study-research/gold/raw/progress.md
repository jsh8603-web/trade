# gold §2-3 진행 트래커

> 인계: [handoff-gold-2-3-20260530.md](./handoff-gold-2-3-20260530.md)

## Working Notes

> [ckpt-202605311500:btn-jsh86] /compact 재진입 후 resume 읽음. handoff-gold-20260531.md 작성 완료 상태 확인. main 직접 지시 = 미커밋 commit + HANDOFF DONE 1줄 보고 + 대기 (⛔ /clear 금지). 책임 영역 = study-research/gold/ 73 untracked + handoff-gold-20260531.md (그 외 192 변경분 = 다른 세션 작업물, 손대지 않음).

> [ckpt-202605310145:btn-jsh86] main ★순서정정 본문 수신 → collector-request-to-main.md 작성 + main 보고. merit 6건 (HY OAS ALFRED · OECD CLI · WGC quarterly · MOVE · SPDR GLD · SGE) + sys_priors 재보정 (G6 게이트). 자율 진행 가부 main 판정 부탁. candidate-ledger.md 는 2순위·최종 보존 (merit study 완료 후 잔여만 박제).

> [ckpt-202605310130:btn-jsh86] candidate-ledger.md 작성 + main 보고 직후 main 정정 수신 ("candidate-ledger 먼저 쓰지 마라, 우선순위 바뀜:" 본문 잘림). 후속 명령 대기. 산출 보존 (candidate-ledger.md 박제 그대로) — main 의 우선순위 재지정 본문 도달 시 그에 따라 진행.

> [ckpt-202605310110:btn-jsh86] CFTC COT 연간 zip 3건 fetch 완료 (cftc_{2022,2023,2024}.zip, 2.0~2.4MB each, /raw/). 다음 의도 = (1) zip unzip + gold 088691 managed-money net long 추출 (Python pandas 또는 unzip + grep "GOLD") → cftc_mm_gold.csv (2) 실질금리 디커플링 모니터 = H2 unexplained ln_gold + H7 rolling EG ADF 종합 indicator 정의 박제 (별도 fetch 불요) (3) H5 Markov regime-switching (BAA10Y/VIX) (4) H8 이중 e-process (5) yaml v2 재작성 (force_include 4 + 2 신규 indicator + ⛔점추정 prior 금지 + n<30 5게이트) (6) §2.5 8축 audit (7) main 보고. 동기화 필요: peer commit 추가 stale (b1076d2b/6eb41d61 core/, study 분리). 480k compact 임박, 다음 turn 시작 = handoff-gold-2-3-20260530.md Read.

> [ckpt-202605301900:btn-jsh86] gold §2-3 실데이터 검증 5/8 완료(H1·H2·H4·H6·H3·H7 + M3 거시연관) + ERROR 자산화. 다음=H5/H8/yaml v2/§2.5 8축 + ★main 추가 지시 CFTC managed-money + 실질금리 디커플링 모니터 2지표 반영. 동기화 필요: peer commit stale (2f46607d/b1076d2b/6eb41d61 core/, study 영역 분리).

### 마지막 결정
- R2 자문 수렴 + main 옵션 (a) 채택 (force_include 4 = {real_rate, ln_dollar, cb_demand, GPR}; BE 항등식 basis 외부 가드)
- H2 STRONGLY SUPPORTED (★unexplained ln_gold 2022 +39% → 2026 +391% 단조 증폭) → yaml lens estimation_note "equilibrium re-formation"
- H4 sys_priors 압도적 기각 (일별 std β rate=-0.27, dollar=-0.29 vs sys [-0.5, -0.8]; numeraire trap dollar +66.8% 감쇠 SDR)
- ERROR 자산화: consult-raw-to-output-mapping-gap → ~/.claude/rules/consult-raw-output-mapping-checklist.md 신규

### 다음 의도 (다음 세션)
- CFTC managed-money net position fetch (CFTC COT report public CSV 또는 FRED ID)
- H5 (Markov regime-switching, BAA10Y/VIX) + H8 (이중 e-process Δ-beta vs level 잔차 ordering)
- yaml v2 재작성 (v1 179줄 폐기, force_include 4 + ★ 2 신규 indicator: cftc_mm_net_long + real_rate_decoupling_monitor)
- ⛔ 점추정 prior 박제 금지 (wide CI or freeze), n<30 5게이트 (small-n-statistical-rigor rule 정합)
- §2.5 8축 self-audit → raw/audit-2.5-checklist.md
- main 최종 보고 (btn-Codlearn)

### 동기화 필요
- peer commit 3건 stale (2f46607d/b1076d2b/6eb41d61 core/), study-research/gold/ 분리되어 직접 영향 적음, 작업 재개 시 git pull --rebase 검토
- main G6 게이트 사안 = sys_priors gold loading 재보정 (H4 결과 production wiring 시)
