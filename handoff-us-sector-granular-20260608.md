---
tags: [type/handoff, domain/equity-us, phase/sector-granular]
date: 2026-06-08
next-action: ★11섹터 트리아지 확정(GUIDE §13, 자문3R 만장일치+reflection-verify 0건). SOXX 종결=top시총 EW passive(a5b5515). XLF 검증=PASSIVE(IC≈0 t=0.45, 7191f65). XLI(2순위) 검증 백그라운드 진행중(teammate a61ad0). XLI 결과 회수→retention≥0.5+t≥2면 신호후보 / t<2면 ★미국 GICS selection 무료데이터 전섹터 early-stop 확정. 그 후 잔여=정적 rotation 틸트 레버 / CRSP data-gate reopen / 사용자 차기 방향.
---

# 핸드오프 — 미국 섹터 granular 리서치 (SOXX 파일럿)

## §1. 현재 상태 + 첫 행동 (R6 진행중, 2026-06-08 갱신)
- **teammate us-equity agentId = `a61ad0aedad5269f9`** (R5b 최종본, retention 0.044 보고자). ⛔ **KILL 금지**. ★**깨우는 법 = SendMessage `to`=agentId `a61ad0aedad5269f9`** (resume from transcript). bare name "semi-analyst"는 죽은 inbox로 가 안 깨어남(@suffix도 거부). 완료된 백그라운드 teammate는 agentId resume 필수. 2026-06-08 19:53 R6 resume 성공("had no active task; resumed from transcript in background"). 한국 teammate는 btn-Inv 세션 소유(별 agent a902…, 혼동 금지).
- **R6 게이트**(순서 의무): G1 lag감사→G2 universe breadth(XSD ~46 EW)→G3 생존편향 PIT→G4 코드화 판정(CODIFIABLE retention≥0.70+생존보정 t≥2+lag clean / NOT-CODIFIABLE retention<0.40 or 소멸 or t artifact / 중간 0.40~0.70 추가정제).
- **첫 행동**: teammate G1(lag감사) 보고 도착 시 → 아래 main 독립소견과 대조 검증 → G2 승인.
- **main 독립 G1 소견**(measure_conditional.py 실독): IC는 **daily**(매거래일 12종 Spearman, 핸드오프 §6 "monthly" 부정확) / y_60d 59일 겹침 자기상관 / 보정장치 eff_n+block bootstrap 있으나 **block=20<<60일 겹침 = 과소보정 → t/유의도 과대(진짜 버그, block≈60이어야)** / 브리핑 "NW-HAC lag=60 t=3.24"는 이 스크립트 부재=별 스크립트 위치 확인 필요 / 예측: block=60 재보정해도 non-overlap t≈2.35 기보고로 t>2 생존 가능성 높음→G1 PASS 흐름.

## §2. 진행 맵
1. probe(.p4-us-sector-probe.py): 섹터별 거시 driver 차등 강(rate10y XLE+0.225 vs SOXX−0.136), selection momentum 약 → granular 가치 TENTATIVE
2. 자문 3R 수렴(gemini+claude): rotation granular 회의(~30%)/selection-value 엣지 (§6)
3. 산출: SECTOR-GRANULAR-GUIDE §10(자문수렴 SSOT)+§11(teammate dispatch 템플릿) + soxx_semi/round-1.md(가설 H1~H4)
4. teammate 스폰(TeamCreate us-equity + Agent) → R1 작업 중
- **다음**: R1 회수→검수→R2 실측준비→R3 실측(M1~M5)→R4 summary.yaml+15axis-audit→R5. 점진 1(SOXX)→수정→3(SOXX/XLE/XLF)→티어(T1 SOXX/XLE / T2 XLF/XLI/XLB / T3 XLP/XLU/XLV)

## §3. 사용자 박제 (framing)
- teammate = `TeamCreate`+`Agent(team_name+name)` in-process (⛔ subagent 아님). 작업 끝나도 KILL 금지.
- 각 teammate = 증권사리서치·논문→가설→검증→상관도, **한국 동일 수준**(8파일/7블록/5게이트 M1~M5/15축 audit).
- "x축" = **15축 audit**(A~L study+M~O wire, hard-fail B/C/D/I).
- 점진: 1 파일럿→수정→3개→티어. opus 1m으로 teammate.
- 다음 teammate부터 §11 템플릿으로 한번에 full prompt(보강 SendMessage 불필요).

## §4. 파일 inventory (절대경로)
- `D:/projects/Inv/study-research/eq_us/SECTOR-GRANULAR-GUIDE.md` — §0~§9 작성기준 + §10 자문수렴 + §11 teammate 템플릿
- `D:/projects/Inv/study-research/eq_us/industries/soxx_semi/round-1.md` — SOXX 파일럿 R1 골격
- `D:/projects/Inv/.consult-us-sector-granular-briefing.md` — 자문 브리핑(probe 포함)
- `D:/projects/Inv/.p4-us-sector-probe.py` — probe 스크립트(섹터 driver 차등)
- `~/.claude/.gemini-web-last.md` + `~/.claude/.claude-web-basic-last.md` — 자문 raw 원문
- `~/.claude/memory/promotion-log.md` head — ERROR(teammate-subagent 혼동) 기록
- python = `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`
- 데이터 = `eq_us/industries/us_cyclical/raw-v3/data/{prices,edgar_fundamentals,universe,macro}.parquet`(SOXX_semi 12종)

## §5. 미해결 · 실패한 시도
- **book-to-bill 데이터 가용성**: claude 주장(SEMI bookings 2016/billings 2022 종료) — teammate R1에서 실검증 중. probe 단계 죽인 subagent가 "book-to-bill=coincident-to-lagging(leading 아님)" 확인 + FRED "BBPBFEQ" 환각 발견 → H2(κ) falsify 강화.
- **EW-semi universe 미확정**: SOXX/ICE(~30종) vs S&P semi select(XSD, 46종). 사전등록 필요.
- **생존편향**: 현 12종=현 holdings → CRSP delisting 보강 필요(I축 hard-fail 위험).
- **실패**: teammate를 처음에 teamless subagent(run_in_background only)로 잘못 스폰 → kill 후 TeamCreate+Agent 재스폰(ERROR 기록 완료).
- **teammate R1 결과 미검수**(작업 중).

## §6. 자문 종합 (3R 수렴 8포인트)
1. 층 분리: selection (D)factor-cancel 교정완료 / rotation (C)시장구조 우세
2. rotation granular ★☆☆(~30%): eff_N=1.47, within-corr 0.617(11섹터≈1.5 독립베팅), granular가 시계열 small-n 못고침. probe ②β차등=노출이지 alpha 아님
3. selection = value-only granular: momentum MDE_IC≈0.107 미달 dead, value(−0.117) 경계 + DL EB partial pooling 필수
4. EW-semi(cap-weight SOXX 금지=NVDA 위장, CRSP delisting, XSD≠SOXX anchor만)
5. primary 스왑: within-sector value-selection(ρ) primary / book-to-bill(κ) secondary 강등
6. 통제변수 관측가능 사전지정{market,EW-semi,rate10y,credit OAS,dollar}, PCA 기각(PC1=EW-semi 내생성)
7. 단일 결정실험 = within-sector predictive decomposition(γ null→(C) freeze)
8. entry gate 사전약정: MDE 스크린+decomposition-first+Korea-grade+FDR원장+freeze default(primary 미달→rotation 영구폐기+3슬리브 value-selection 집중)
- reflection-verify PASS(16항목 매핑, 누락 0)

### 신호강도 자문 (claude-web 2R, 2026-06-08, gemini 불능) + ★§방향보존 정정
- ⛔★main 비관왜곡 정정(§방향보존 ERROR): 첫 자문(granular) raw "산업배분=주레버 살릴여지(정적틸트·깐깐검증) / 종목선택=좁은틀(대형주 top10 동일가중) 한정 폐기, 가치무효 아님"을 main이 "rotation 회의·보류 / 종목선택 무가치"로 정반대 비관 박제. 반도체 freeze 모순(horizon 부족)=사용자 지적 귀속. GUIDE §10 상단 정정박스.
- ★value = PROVISIONAL: non-overlap t≈2.35(★primary, ~27 비겹침 obs, p≈0.026 modest-but-real). 단조 항기간구조(y5d+0.032→y60d+0.104)+pre-AI p=0.003 = not-artifact 확신高(main이 '약'으로 깎은 건 under-claim). tier 게이트: leave-2-out(NVDA/AVGO retention≥0.70)+IC lag버그 감사(measure_conditional.py IC가 monthly인데 lag=60이면 t과대 BUG→lag≈4)+non-overlap t≥2 통과 시 moderate, 미달 weak.
- ★low_vol = REJECTED-as-constructed: 부호 anti-BAB(고베타 outperform)=저변동 프리미엄 정반대=AI고베타 momentum misspec 포장(main이 PARTIAL 준 건 over-claim). SAVE 경로=pre-AI beta·AI-mom 직교 후 정상부호(저베타 outperform)+|t|≥2.
- quality/momentum/value+quality 결합=REJECTED. conditional 증폭=격하(family-2 overlapping t 4.61→1.31 붕괴).
- R5b=teammate가 위 4게이트 반영 재확정 중(7e9e223 위). 자문 raw=`~/.claude/.claude-web-basic-last.md`.
- ★main 학습: 자문→요약 시 비관/낙관 양방향 왜곡 경계 + 자문 원문 방향성 라벨 raw substring 보존(promotion-log 2026-06-09 ERROR).
