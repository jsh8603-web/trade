---
tags: [type/handoff, domain/inv, scope/equity-industry-dispatch]
date: 2026-06-03
next-action: "frame v3 §0/§I archetype 척추 반영 ✅완료 + '40축'→측정 15종(주식 14) 전수 정정 ✅완료 + stock.md 15축6단계 ✅완료. 다음 = archetype.py 매핑 보강(10key→stock.md구분, 코드변경=사용자 승인 필요) → 설계 단계마다 외부검토(claude+gemini 병렬) → 산업 dispatch(teammate, 한국12 완주→미국). 산업구분=다회차 외부검토 확정=재자문 불필요."
---

# handoff — 주식 산업 섹터 dispatch v3 + 결선 (2026-06-03)

## 1. 현재 상태 + 첫 행동
결선(분기 A) 완료. frame v3 초안 + 리서치 완료. 사용자 "방향 검토" 답(archetype 척추 발견) 제시 완료.
**첫 행동**: (1) frame v3 §0/§I 에 archetype.py 척추 반영(문서) (2) 사용자에게 archetype.py 매핑 코드 보강 승인 회수 → 승인 시 WireSmith(idle standby) 에 dispatch.

## 2. 진행 맵
- **분기 A 결선 = ✅ 완료**. WireSmith(teammate `inv-wire` 팀, idle standby — shutdown 안 함). 산출: `core/study/study_register.py` `wire_falsification()` + `scripts/wire_study_falsification.py`(train↔cycle panel-score-IC 오케스트레이터, engine.py 무접촉). dead-hook 2개(hy_oas_risk_regime→credit_spread_hy_oas / real_rate_duration_penalty→real_rate_10y)+curve_regime_transition 활성, confidence prior 0.5→0.667 이동 입증. 회귀 0(pytest 27 PASS), byte-identical(INV_R15_WEIGHTS off). **경계 밖** = 실 FRED hy_oas green(team-lead PC `.env` FRED_API_KEY+망 재현 — runner 자동 통과 작성됨). 발견 A(emit_where 텍스트 stale, panel 축이 SSOT) = 미수정 보류.
- **분기 B 산업 study**: frame v3 초안 작성됨. 리서치 완료(archetype 척추).
- **분기 C coin 측정 방법론(15종, 주식 적용 14) 이식**: ✅ 완료.

## 3. 사용자 박제 (대화 고유)
- 작업 1차 단위 = **산업(섹터)**. 거시국면/산업분위기 = 렌즈.
- 측정 뼈대 = **coin 측정 방법론 15종 그대로**(주식 적용 14, intraday만 제외 / within=within-period, family=factor-family neutralization+cross-asset family). cross/regime/horizon 은 예시일 뿐 전체 15종 이식. ⚠️ "40축"은 과거 오기(실제 측정 방법론은 15종, "40몇개"는 French49 산업분류 49개와 혼동).
- **섹터 구분 = stock.md** (다회차 외부검토 확정 결과물, 재검토 불요. 미국 GICS 11+Mag7 / 한국 12 산업 Tier).
- "산업.py 차용? 미국? GitHub? 한국 리서치?" = **질문(검토 요청)이었지 지시 아님**.
- **결선 = 작게 보고 + 자율**.
- ★진짜 뼈대 = **archetype.py 5종 archetype**(사용자 "coin 프레임=뼈대" = 정확히 이 레이어).
- ★**dispatch 규칙** (2026-06-03): agent spawn = **teammate**(하네스2wf: TeamCreate+Agent(team_name,name,bg)+SendMessage, 일반 teamless bg 금지). 순차 = **한국 12산업 완주 → 미국, 한번에(한국+미국 동시) 금지**. frame v3 §J.
- ★**cross 정의**: 분석 단위(산업군/타자산 금·채권·코인) 간 상관 = coin btc-eth 식. within-industry 아님. 측정 3종(동시 RegimeGlasso / 방향성 DY / 구조 supply-chain). 연관성 리서치 = DY connectedness+customer-supplier momentum+I-O centrality 신규(raw `~/.claude/memory/research/sector-comovement-indicators.md`).
- ★**stock.md 관계**: stock.md = eq_us/eq_kr "무엇 study"(가설 SSOT) / frame v3·템플릿·handoff = "어떻게 dispatch"(양식 SSOT). stock.md §0 위 포인터로 연결. 내용 복제 아닌 계층 분리.

## 4. 파일 inventory
- progress: `progress-stock-corr-layer-20260603.md`
- frame v3 초안: `study-research/frame-v3-draft-industry-dispatch-20260603.md`
- consult brief: `consult-brief-stock-industry-axes-20260603.md`
- 결선: `core/study/study_register.py`(wire_falsification) + `scripts/wire_study_falsification.py`
- ★핵심 코드: `core/structure/archetype.py`(DEFAULT_SECTOR_ARCHETYPE equity 10key @187-209, archetype_for_sector fallback="cyclical" @214, 5종 archetype @47-78) / `core/assume/weight_card.py`(derive_weights @208-239 SOTA) / `conditional_correlation.py`(RegimeGlasso) / `stock/data/sector_multiples.py`(French49Provider, cheapness overlay) / `stock/data/krx_flows.py`(KrxSectorProvider 한국 PIT)

## 5. 미해결 (재개 순서)
1. **frame v3 문서 반영**: §0 뼈대=archetype.py 추가 / §I archetype 매핑 보강 작업 명시.
2. **archetype.py 매핑 보강** (코드 변경 = 사용자 승인 필요): DEFAULT_SECTOR_ARCHETYPE equity 10key → **stock.md 산업구분에 맞춰 전수 매핑** + valid_from 시변. ⚠️**미국 = GICS 11 아님** — stock.md eq_us 가 다회차 확정한 **Mag7 custom basket(T0=Mag7+AVGO/ORCL/AMD) + macro-sleeve 2-4축(PCA eff_N)** 구분이 archetype 배정 단위, GICS sector 는 하위 라벨. 한국 = eq_kr 12산업. WireSmith standby 대기.
3. **지표 조합** = derive_weights 유지(SOTA, 신규 모듈 불요). 보강 = z-score 1/N equal-weight baseline 병행 ablation 의무 + regime cell n<50 LOO p-value.
4. **산업 cycle 신호** = 미국·한국 둘 다 리서치(외부 통합 소스 없음, battery LIT yoy 식).
5. **분류 무료 PIT** = 미국 SEC EDGAR SIC(`edgar_provider.py` 보유)→French 매핑, 한국 pykrx 스냅샷. GICS 유료 라이선스 불요.
6. **frame v3 자문 3R**(archetype 반영 후, gemini-web+claude-web) → 과잉설계 점검 → 검증 방향.
7. ★**산업 연관성 지표 학술 리서치 background 진행 중** (완료 알림 도착 시 frame v3 §C cross 축에 반영). 조사 = 섹터 co-movement/correlation regime · sector rotation · lead-lag spillover(Diebold-Yilmaz) · supply-chain network(Acemoglu, Cohen-Frazzini customer momentum) · factor linkage. **확인: 산업.py·GitHub 레퍼런스(ai-hedge/FF5)에 "섹터 연관성 지표 소스" 부재** — RegimeGlasso 는 상관 추정 인프라일 뿐 지표 소스 아님 → 학술 조사로 후보 발굴. (background agent 결과는 task-notification 으로 수신, 미수신 시 재dispatch.)

## 6. 리서치/자문 종합
- **archetype.py = 진짜 산업 구분 척추**(5종: cyclical/event_driven/spread_driven/asset_stable/compounder, +commodity/crypto. coin·commodity·equity 통일, valid_from 시변 설계). "구분 적다"의 정체 = equity 10key 하드코딩 + 미등록 cyclical fallback. provider/French/GICS 는 그 위 cheapness 데이터 층(계층, 경쟁 아님).
- **derive_weights = SOTA 충분**: Grinold w∝Ω·IC + 1/N 블렌딩(DEFAULT_BLEND_1N=0.30, DeMiguel) + capped-simplex(cap 0.40) + RegimeGlasso precision(다중공선 자동해소). 3중 방어. ML/ai-hedge 페르소나 가중 = n<50 overfit, 미채택이 올바름(ceiling 불변식 down-only 분리).
- 무료+PIT+GICS매핑 동시 제공 GitHub = 없음(GICS 유료 독점). 우리 EDGAR SIC + pykrx 스냅샷이 무료 PIT 최선.
