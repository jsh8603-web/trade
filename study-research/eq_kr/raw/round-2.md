# round-2 — eq_kr 자문폴백 라운드 (2026-05-30)

> 자문 채널 (/claude-web, /gemini-web) 대신 **WebFetch + WebSearch 폴백** 사용 — 9 작업방 동시 자문 채널 경합 자제 (main 지시).
> 산출: 본 round-2.md + raw archive + memory + frame.md (산업 subagent 통일 계약, 별 파일).

## 0. 라운드 2 질문 (round-1 잔여 빈틈 6 중 3 우선 처리)

1. e-KJFS 본문 = 표본 기간·N·계수 부호·정확 finding (governance 가설 검증)
2. 일본 TSE 2023 PBR 1.0 reform = 한국 비교 (밸류업 정책 효과 frame)
3. KCGS 거버넌스 등급 무료 접근 가능성
4. Naver Finance 컨센서스 EPS scraping 신뢰도

(잔여 빈틈 2 — DRAM 무료 시계열, KOSDAQ 학술 — 라운드 3 또는 산업 subagent 위임.)

## 1. WebFetch e-KJFS 본문 = ★학술 가설 정밀 확정

### 표본
- **2000-2022 (23년)** 본 분석 / **2012-2022 (11년)** ESG governance 분석
- ★ **2024 Value-Up program 미포함** — 정책 효과는 본 결과 밖
- N: ESG 표본 7,443 obs (KOSPI) + 3,021 (KOSDAQ). 확장 표본 15,269 + 22,239.
- 1,631 unique firms. industry + year fixed effects panel regression.

### Finding (계수 부호 / 유의)
| 가설 | 변수 | 부호 | 유의 |
|---|---|---|---|
| Governance | G-score (KCGS) | 음 | **n.s.** |
| Growth | R&D/TA | 양 | p<0.01 (계수 13~16 — PBR 최강) |
| Growth | CAPEX/TA | 양 | p<0.01 |
| Growth | Intangible/TA | 양 | p<0.01 |
| Growth | PPE/TA | 음 | p<0.01 |
| Growth | LnAge | 음 | p<0.01 |
| Payout | Payout ratio | 음 | KOSPI n.s. / KOSDAQ p<0.10 |
| Payout | Dividend yield | tested (별도 명시 없음) |

### 저자 결론
- Korea discount = **composition effect** (성숙·tangible-asset-heavy value stocks 집중) — 거버넌스 실패 X.
- post-2008 traditional value premium 글로벌 소멸 → low-PBR alpha 약화.
- 정책 함의: 거버넌스·배당 개선만으로 부족 → R&D·무형자산 기반 구조전환 필수.

### 한계 (저자 명시)
- within-Korea (country-level discount 분리 불가)
- KCGS 2012+ 제약
- value premium 소멸 → 정책 인과 분리 어려움

## 2. 일본 TSE 2023 PBR 1.0 reform (★WebSearch internal error → 라운드 3 재시도)

- WebSearch 결과 미수령 — 환각 위험 → 본 작업방 내재지식만으로 부분 정리, finding 단정 금지.
- 알려진 사실 (라운드 1 Capital Group 자료 등 기반):
  - 2023-03 TSE = PBR < 1.0 상장사에 자본효율·주주환원 개선 계획 공시 요구.
  - 일본 닛케이 2024 전후 강세, 특히 저PBR 종목 mean-reversion.
  - 한국 밸류업 (2024-02 FSC) = 일본 모델 벤치마크.
- ⛔ 라운드 3 자문 (gemini-web) 또는 WebSearch 재시도 후 정밀화 의무.

## 3. KCGS / ESG 거버넌스 등급 (★ 무료 접근 가능)

- KCGS (옛 한국기업지배구조원, 현 한국ESG기준원) = 2002 설립, 2011 부터 ESG 통합.
- ★ **KRX ESG 포털 (esg.krx.co.kr) 종목별 등급 공개** — 라이센스 협의 없이 무료 접근 가능성.
- collector_plan D4 (KCGS 라이센스 P2) → ★ P1 으로 격상 + 스크랩 시연 의무 (산업 subagent 또는 별 작업방).

## 4. Naver Finance 컨센서스 EPS

- 가격·기본 정보 = requests + BeautifulSoup 추출 가능.
- ⛔ 증권사 컨센서스 EPS forecast endpoint 미문서 — 역공학 필요.
- 대안: KIS Open API 컨센서스 필드 검토 (이미 memory: research/kis-openapi-feasibility.md 참조).

## 5. 라운드 2 산출 (3계층 적재)

- archive raw: `~/.claude/docs/archive/research-raw/eq-kr-r2-validations-native-20260530.txt`
- memory: `~/.claude/memory/research/eq-kr-r2-academic-validation-japan-kcgs-naver.md`
- MEMORY 인덱스: 1줄 추가 완료

## 6. ★8축 self-audit (라운드 2)

| 축 | 점검 결과 |
|---|---|
| A 이론 실재성 | e-KJFS DOI 10.26845/... 실재 확인 / KCGS 도메인 cgs.or.kr 실재 / KRX ESG 포털 esg.krx.co.kr 실재. **PASS** |
| B 실데이터 검증 | 본 라운드 = 학술 표본만 (N=7443+3021 KOSPI/KOSDAQ, 2000-2022). Inv 시스템 실데이터 시계열 검증은 산업 subagent 위임. 본 작업방 합성·시뮬 데이터 미생성. **PARTIAL** — Inv 실측은 2-3 단계 산업 subagent. |
| C yaml 추적성 | study_session.yaml 미작성 (frame.md + 산업 subagent 결과 통합 후 작성). **N/A** 현 단계 |
| D PIT·OOS | e-KJFS 표본 = 정책 시행 전 → Value-Up 정책 효과는 OOS. 본 라운드는 라이브 실데이터 검증 X. **PARTIAL** — OOS 디자인은 frame §M4 에 박제. |
| E 자문 비판 + 환각 cross-verify | e-KJFS 본문 finding = 1 출처. **WARNING** — 라운드 3 학술 cross-source (한국재무학회 학술대회 발표·KCMI 보고서) 필요. URL/DOI 실재 검증은 PASS. |
| F 반증가능 + 기각 기록 | v1 가설 "거버넌스 → re-rating" → 학술에서 기각. 본 round-2 에 기각 기록 명시. **PASS** |
| G 검정력 한계 | e-KJFS 본 표본 N 큼 (검정력 충분). 그러나 Value-Up 정책 효과 (2024-) 표본 N 작음 (1~2년) → 후속 측정 시 5게이트 적용 의무. **PASS** (frame 에 5게이트 박제) |
| H 미해결 의문 | 5개 — (1) Value-Up 효과 정밀 측정 (2) 일본 TSE 결과 (라운드 3) (3) KOSDAQ 학술 (라운드 3) (4) DRAM 무료 시계열 (산업 subagent 반도체) (5) Naver 컨센서스 역공학 (산업 subagent 또는 별) |

★ A/F/G 통과. B/C/D = 산업 subagent 위임 (frame.md 박제). E 경고 → 라운드 3 cross-source.

## 7. 라운드 2 → 산업 subagent 전환 결정

main 의 산업별 subagent (반도체/2차전지/자동차/금융) 디스패치 지시 + 누락 critical 거시 4종 추가 + 5게이트 + 점추정 prior 박제 금지 + sleeve=팩터노출 정의 → frame.md (subagent 통일 계약) 작성 후 4 subagent 디스패치.

라운드 3 (잔여 빈틈 메우기) 는 4 subagent dispatch 와 병렬 진행 가능 — gemini-web 자문 1회 (일본 TSE, KOSDAQ 학술 동시 질문).

## 8. 라운드 2 → 다음 단계

- ✅ frame.md 작성 → 산업 subagent 통일 계약 박제
- ✅ 4 산업 opus 1m subagent dispatch (반도체/2차전지/자동차/금융, run_in_background)
- ⏳ subagent 결과 수령 후 통합 → eq_kr 통합 study_session.yaml + 라운드 3 (gemini-web 일본 사례)
- ⏳ direction.md 작성 → main 보고
