# 🪙 Claude Coin Trading System

<p align="center">
  <img src="assets/logo.png" alt="Claude Coin Trading Bot Logo" width="280" />
</p>

<p align="center">
  <strong>코드 한 줄 안 짜고, 자연어로 전략을 쓰면 AI가 알아서 코인을 사고판다고? 네, 진짜입니다.<br/>
  업비트에서 비트코인 자동매매부터 바이낸스에서 김치프리미엄 차익거래까지 —<br/>
  잠자는 동안 스스로 생각하고 매매하며 진화하는 살아 숨쉬는 시스템입니다. 🚗💨</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.29.0-blueviolet?style=for-the-badge" alt="version"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python"/>
  <img src="https://img.shields.io/badge/Gemini_AI-2.5_Pro-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="gemini"/>
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="supabase"/>
  <img src="https://img.shields.io/badge/Claude_Code-Sonnet_4-D97706?style=for-the-badge" alt="claude"/>
</p>

---

## 📖 이 앱의 개발 철학과 진화 과정 (Philosophy & Evolution)

### 🎓 원작자 dantelabs 와의 만남, 그리고 첫 앱 이후의 변화
이 프로젝트의 최초 모티브는 원작자 **dantelabs**님의 유튜브 채널에서 영감을 받아 시작되었습니다. ([Dante Labs YouTube](https://youtube.com/@dante-labs))
원작의 코드를 활용해 첫 앱을 만들고 난 후, 코인 자동매매의 본질과 한계에 대해 깊이 고민하기 시작했고, 결과적으로 이 앱을 완전히 다른 차원의 복합 지능 시스템으로 발전시켰습니다.

### 🐍 파이썬과 규칙 기반(Rule-Based) 매매법의 필요성
자동매매 앱의 특징상, 실시간 데이터 수집과 가공, 다양한 AI 모델 및 오픈소스의 유연한 통합이 필수적입니다. 이를 위해 연동성과 확장성이 가장 뛰어난 **파이썬(Python)**을 핵심 언어로 채택했습니다.
초기에는 최첨단 인공지능이 모든 것을 완벽하게 판단해주길 기대했습니다. 하지만 예측 불가능한 꼬리 위험(Tail Risk)이 상존하는 코인 시장의 특성상, 최소한의 잃지 않는 장치인 **규칙 기반(Rule-Based) 매매법**이 반드시 필요합니다.

### 🧠 강화학습(RL)의 도입: 가상 데이터 학습 vs 실 데이터 학습
앱의 지능을 한 단계 더 끌어올리기 위해 인공신경망 기반의 강화학습(RL)을 적극 도입했습니다. 하지만 개발 과정에서 매우 뼈저린 사실을 깨달았습니다.
- **가상 데이터(Backtesting) 학습**: 과거 데이터를 돌려보면 늘 우상향하는 완벽에 가까운 환상적인 수익률을 보여줍니다.
- **실 데이터(Live) 학습**: 하지만 시장의 슬리피지(Slippage), 수수료, 매수/매도 잔량에 숨겨진 변동성, 실시간 시장 심리 등 **실제 시장 환경(실 데이터)**을 적용해 강화학습을 진행하자 사정이 완전히 달라졌습니다.

### 🧪 수많은 실패와 실험 결과
이 봇을 어떻게든 수익 나는 완벽한 기계로 만들고자 정말 수많은 실험과 실패를 겪었습니다:
1. **Swing Hunter 시도**: 실 데이터 환경에서는 승률 높은 유의미한 모델을 찾는 것에 실패했습니다.
2. **알트코인 20개 순환매매 무용론**: 빈번한 매매에 따른 수수료와 슬리피지를 역산해보니, 수익성이 아예 없어 전면 폐기했습니다.
3. **비트코인과 이더리움 연관 매매법**: 뚜렷한 연관 법칙성을 찾기 어려웠고 수익성도 나오지 않아 적용하지 않았습니다.

**🏆 결론은 "비트코인(BTC)" 하나뿐입니다**
수많은 전략의 폐기와 실험 끝에 얻은 최종 결론은 명확합니다. 코인 자동매매는 결국 유동성이 가장 풍부하고, 온체인 데이터 및 거시 경제의 흐름을 가장 잘 반영하며, 장기적 우상향의 신뢰도가 제일 높은 **비트코인(BTC)** 하나를 대상으로 하는 것이 압도적으로 유리하다는 것입니다.

### 🧠 제미나이(Gemini) 모델을 통한 DB 임베딩과 RAG 검색 시스템의 도입
단순한 룰(Rule)이나 맹목적인 기계학습을 넘어, **봇 스스로 판단 맥락을 인지하고 추론하는 메타인지 능력**을 부여하기 위해 최신 AI 기술인 **RAG(검색 증강 생성)와 벡터 임베딩**을 전격 도입했습니다.
- **모든 과거 기록의 벡터화**: 앱에서 실시간으로 축적되는 수많은 데이터베이스를 전부 제미나이(Gemini) 모델을 통해 다차원의 **벡터(Vector) 데이터로 변환(Embedding)**하여 수파베이스 DB에 매번 저장합니다.
- **RAG를 통한 자기 기억 인출**: 봇이 완전히 새로운 시장 상황에 직면했을 때, 단순 지표 평균치로만 판단하지 않고 즉시 자신의 기억(DB) 공간을 검색(RAG)합니다. 코사인 유사도(Cosine Similarity)를 계산해 가장 전반적 뉘앙스가 흡사했던 과거의 패턴들을 순식간에 불러옵니다.

### 🤖 앱의 최종 목표: '단순한 고승률'이 아닌, 스스로 생존하는 '살아 움직이는' 시스템
따라서 이 앱의 궁극적인 목적은, 과최적화된 백테스트로 만들어진 "무조건 이기는 마법의 공식"을 찾는 것이 아닙니다. 대신, 아래의 철학을 가지고 시장에서 묵묵히 제 할 일을 하며 진화하는 **살아있는(Alive) 앱**을 구축했습니다:

1. **정보의 유기적 감지와 반응**: 외부 뉴스 호재/악재, 고래들의 대량 매집 정보, 거시적 매크로 데이터 지표 등을 실시간으로 감지하고 파도타듯 매매에 즉각 반영하는 앱.
2. **시장 순응형 생존 방식**: 상승장인지 하락장인지 사용자가 일일이 전략을 뜯어고치거나 신경 쓰지 않아도, 스스로 파악하고 자동으로 최적의 전략을 교체하며 대응하는 앱.
3. **자가 학습(Self-Learning)과 메타인지 진화**: 자신만의 행동을 꾸준히 데이터베이스에 쌓고, 그 실패와 성공의 모든 기록을 제미나이(Gemini)로 임베딩한 후 RAG 검색을 통해 과거의 자신과 현재를 끊임없이 비교하여 결론을 내리는 지능 개선형 앱.
4. **자가 치유 (Self-Healing & Debugging)**: 24시간 365일 돌아가야 하는 시스템 특성상, 중간에 알 수 없는 버그가 생기거나 서버가 다운되려 할 때 파이썬 코드가 백그라운드에서 스스로 원인을 디버깅하고 스크립트를 재시작(Restart)하여 생명력을 유지하는 끈질긴 앱.

---

## 📑 목차

- [1. ⚙️ 아주 자세한 셋팅 완벽 가이드 (초보자 필독!)](#1-️-아주-자세한-셋팅-완벽-가이드-초보자-필독)
- [2. 🤖 비트코인 자동매매 봇 (업비트 메인 시스템)](#2--비트코인-자동매매-봇-업비트-메인-시스템)
- [3. 🌶️ 김치랑 봇 (Kimchirang 델타 뉴트럴 차익거래)](#3-️-김치랑-봇-kimchirang-델타-뉴트럴-차익거래)
- [4. 🧬 스캘프 ML 시스템 (scalp_ml — 단타 머신러닝)](#4--스캘프-ml-시스템-scalp_ml--단타-머신러닝)
- [5. 🧠 RL 하이브리드 두뇌 (rl_hybrid — PPO + RAG + Gemini)](#5--rl-하이브리드-두뇌-rl_hybrid--ppo--rag--gemini)
- [6. 📰 뉴스랑 (NewsRang — 11소스 실시간 외부 데이터 수집기)](#6--뉴스랑-newsrang--11소스-실시간-외부-데이터-수집기)
- [7. 📱 텔레그램 알림 및 시스템 스케줄링](#7--텔레그램-알림-및-시스템-스케줄링)
- [8. 🗄️ Supabase 데이터베이스 구조 (50개 마이그레이션)](#8-️-supabase-데이터베이스-구조-50개-마이그레이션)
- [9. 🏗️ 전체 프로젝트 패키지 구조](#9-️-전체-프로젝트-패키지-구조)
- [10. 🚫 면책 조항](#10--면책-조항-및-최후-당부)

---

## 1. ⚙️ 아주 자세한 셋팅 완벽 가이드 (초보자 필독!)

> 처음 설정하시는 분들을 위해 단계별로 아주 상세하게 설명합니다. 순서대로만 진행하시면 누구나 시작할 수 있습니다.

### 1-1. 필수 프로그램 설치 (Git + Python)

봇을 구동하려면 윈도우/맥에 관계없이 컴퓨터에 **Git**과 **Python**(3.10 이상 권장, 3.12 최고 권장)이 반드시 설치되어 있어야 합니다.

#### 🪟 Windows 사용자
1. **Git 설치**: [https://git-scm.com/downloads](https://git-scm.com/downloads) 에 접속하여 `.exe` 파일을 다운로드하고 설치 과정을 묻는 창에서 아무것도 건드리지 말고 무조건 `Next`만 눌러 끝까지 설치합니다.
2. **Python 설치**: [https://www.python.org/downloads/](https://www.python.org/downloads/) 에 접속하여 3.1x 버전을 다운로드합니다.
   - ⚠️ **초특급 주의사항**: 다운받은 파이썬 설치 파일 실행 시, 맨 첫 화면 하단에 있는 **`Add python.exe to PATH`** 체크박스를 ⭐️**반드시, 무조건**⭐️ 체크하고 `Install Now`를 눌러야 합니다. 이것을 체크하지 않으면 터미널에서 파이썬 명령어를 전혀 알아듣지 못합니다.

#### 🍎 Mac 사용자
1. 사용중인 Mac에서 **터미널(Terminal)** 앱을 엽니다. (Command ⌘ + Space 바를 누르고 화면 중앙에 '터미널' 검색)
2. 아래 명령어를 복사 후 터미널에 붙여넣고 엔터를 치면 파이썬이 설치됩니다.
   ```bash
   brew install python@3.12
   ```
   *(만약 `brew: command not found` 오류가 뜬다면 Homebrew가 없는 것이니, 먼저 [https://brew.sh](https://brew.sh) 에 접속해 설치 명령어를 복사해 터미널에 붙여넣어 Homebrew부터 설치합니다)*

### 1-2. 소스코드 다운로드 (프로젝트 복제)

다운로드받을 폴더로 터미널/명령 프롬프트를 열고 들어간 뒤, 아래 명령어를 실행하여 깃허브에서 전체 코드를 내 컴퓨터로 내려받습니다.

```bash
# 1. 깃허브에서 내 컴퓨터로 통째로 복사해옵니다.
git clone https://github.com/jaeho-jang-dr/claude-coin-trading-main.git

# 2. 방금 다운로드가 완료된 코딩 폴더 안으로 쏙 들어갑니다.
cd claude-coin-trading-main
```

### 1-3. 가상환경 만들기 및 라이브러리 설치

파이썬 프로젝트는 다른 프로그램 패키지들과 꼬이지 않게 '나만의 독립된 방(가상환경)'을 만들어주는 것이 가장 기초이자 필수입니다.

#### 🪟 Windows (명령 프롬프트 혹은 PowerShell 기준)
```powershell
# 1. 이 폴더에 '.venv'라는 이름의 독립된 방(가상환경)을 만듭니다.
python -m venv .venv

# 2. 그 방 안으로 들어갑니다. (왼쪽에 (.venv) 글자가 생기면 성공!)
.venv\Scripts\activate

# 3. 봇을 굴리는데 필요한 파이썬 패키지들을 한 번에 자동 설치합니다.
pip install -r requirements.txt

# 4. 차트 캡처 등을 위해 웹 자동화 도구(플레이라이트)를 추가 설치합니다.
playwright install chromium
```

#### 🍎 Mac / Linux (터미널)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 1-4. 외부와 소통하기 위한 핵심 API 키 발급받기

프로그램이 스스로 남의 서비스(업비트, 텔레그램, 구글 AI 등)를 빌려다 쓰려면 '비밀번호표(API 키)'가 필요합니다. 아래 각 서비스에 가입하시고 키를 발급받은 뒤, **절대 타인에게 공유하지 마시고 본인 메모장에 복사해서 모아둡니다.**

| # | 서비스 | 용도 | 발급 위치 | 비고 |
|---|--------|------|-----------|------|
| 1 | **업비트(Upbit)** | BTC 현물 매매 | 마이페이지 → OpenAPI 관리 | `자산조회`, `주문조회`, `주문하기` 체크. **`출금하기` 절대 체크 금지** |
| 2 | **바이낸스(Binance)** | 김치랑 차익거래(선물) | [binance.com](https://www.binance.com) API Management | Futures 거래 활성화 후 키 발급. `Enable Futures` 체크 필수 |
| 3 | **수파베이스(Supabase)** | 매매이력 DB 저장 | [supabase.com](https://supabase.com) → 프로젝트 Settings | `Project URL` + `service_role secret` 키 복사 (anon 아님!) |
| 4 | **텔레그램(Telegram)** | 모바일 실시간 알림 | `@BotFather` → `/newbot` | 토큰 받은 후 내 봇에게 `/start` 먼저 전송 필수 |
| 5 | **타빌리(Tavily)** | 전 세계 뉴스 실시간 검색 | [tavily.com](https://tavily.com) | 무료 키 발급 |
| 6 | **제미나이(Gemini)** | AI 분석 두뇌 + 임베딩 | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | Create API Key 클릭 |

> **바이낸스 API 키 발급 순서 주의사항**: 반드시 ① Futures 거래 활성화 → ② 퀴즈 통과 → ③ 최소 입금 → ④ API 키 생성 순서로 진행해야 Futures 권한이 정상 부여됩니다. 순서를 바꾸면 API KEY에 권한이 없습니다.

### 1-5. `.env` 파일 설정 (실제 봇에 키값 주입)

이제 메모장에 소중히 모아둔 API 키를 파일 안에 세팅해야 합니다.

1. 다운로드 받은 `claude-coin-trading-main` 폴더 안에 보시면 `.env.example` 이라는 껍데기 파일이 있습니다.
2. 이 녀석의 파일명을 뒤쪽의 `.example`을 지워버리고 그냥 `.env` 로 바꿉니다.
3. 우클릭 후 메모장(혹은 텍스트 편집기)으로 `.env` 파일을 열고, 아래 내용처럼 여러분이 발급받은 실제 키들로 정확히 바꿔치기 해줍니다. 띄어쓰기 없이 붙여넣습니다.

```ini
# 🏦 거래소 API (업비트 — 비트코인 자동매매용)
UPBIT_ACCESS_KEY=여러분의_업비트_액세스키를_붙여넣으세요
UPBIT_SECRET_KEY=여러분의_업비트_시크릿키를_붙여넣으세요

# 🔄 거래소 API (바이낸스 — 김치랑 차익거래용)
BINANCE_API_KEY=여러분의_바이낸스_API키
BINANCE_API_SECRET=여러분의_바이낸스_시크릿키

# 🗄️ 데이터베이스 저장소 (수파베이스)
SUPABASE_URL=https://여러분의프로젝트고유값.supabase.co
SUPABASE_SERVICE_ROLE_KEY=ey...로_시작하는_아주긴_서비스롤키

# 📱 텔레그램 휴대폰 알림
TELEGRAM_BOT_TOKEN=12345678:여러분의봇토큰
TELEGRAM_USER_ID=123456789  # 숫자

# 📰 뉴스 검색 및 🤖 두뇌 역할 AI 모델
TAVILY_API_KEY=tvly-여러분의타빌리키
GEMINI_API_KEY=AIza...제미나이키

# 🔥 투자 설정 (극도로 주의하세요!) 🔥
DRY_RUN=true              # 🚨 true면 연습모드(가짜돈), 실제 내 진짜 돈으로 사고팔려면 false 로 변경!!
MAX_TRADE_AMOUNT=100000   # 1번 쏠 때 매수할 금액 (예: 10만원 = 100000)
MAX_DAILY_TRADES=3        # 하루에 딱 이 숫자만큼만 매매진입 허용 (보통 3~5번 권장)
MAX_POSITION_RATIO=0.5    # 현재 내 업비트 원화 잔고의 몇 프로까지만 투자를 허용할지 (0.5 = 50%까지)
EMERGENCY_STOP=false      # 만약 미친듯이 큰 폭락이 온다면 이걸 즉시 true로 바꾸세요.
```

> **🔥 강력 주의!** 모든 셋팅을 마친 뒤 최초 1~2주는 자나깨나 무조건 `DRY_RUN=true` 상태에서 시스템이 매매 알림을 잘 쏘는지, 오류는 없는지 구경만 하셔야 합니다.

### 1-6. Supabase 데이터베이스(DB) 틀 만들기

로깅, 디버깅, 자가발전을 위해 수파베이스라는 빈 노트에 선을 그어주는(테이블 생성) 작업입니다.

1. Supabase 대시보드 로그인 → 프로젝트 선택 → 왼쪽 메뉴의 `SQL Editor` 클릭
2. 다운받은 프로젝트 내의 `supabase/migrations/` 폴더 안을 엽니다.
3. 안에는 `001_...sql` 부터 쭉 숫자가 붙은 **50개의 sql 파일**이 있습니다. 이걸 1번부터 순서대로 하나씩 메모장으로 연 다음, 내용 전체를 복사하여 SQL Editor에 붙여넣고 **Run(실행)** 버튼을 누릅니다.
4. 에러가 나는 번호가 있으면 이미 만들어진 것이니 패스해도 좋습니다.

---

## 2. 🤖 비트코인 자동매매 봇 (업비트 메인 시스템)

**최우선 목표**: 사람이 상승장인지 하락장인지 일일이 차트를 보고 스트레스받거나 전략을 바꿀 필요 없이, 봇이 스스로 거시 지표를 감지해 최적화된 매매법으로 생존하기.

### 2-1. 핵심 설계 철학 — 자연어 전략 기반 시스템

이 시스템의 가장 독창적인 특징은 **매매 로직을 코드로 하드코딩하지 않는다**는 것입니다.
`strategy.md` 파일에 자연어로 전략을 정의하고, Claude AI가 데이터를 해석하여 자율적으로 판단합니다. Python 스크립트는 데이터 수집과 API 호출만 담당합니다.

```bash
# 메인 봇 시스템 구동 명령어
🪟 Windows 환경: python rl_hybrid\launchers\start_all.py
🍎 Mac 환경:     python3 rl_hybrid/launchers/start_all.py
```

명령어를 치면 백그라운드에서 실시간 데이터 감지, 텔레그램 연동, DB 적재, 그리고 에러나 거래소 API 멈춤 현상 발생 시 **스스로 디버그하여 시스템을 재시작하는 자가 치유(Self-healing)** 프로세스가 동시에 돌아갑니다.

### 2-2. 에이전트 모드 실행 (권장)

```bash
# 에이전트 자율 실행  
bash scripts/run_agents.sh

# LLM 프롬프트 모드 (레거시)
bash scripts/run_analysis.sh 2>/dev/null | claude -p --dangerously-skip-permissions

# Claude 대화형 세션 (전략 수정, 피드백, 긴급 정지 등)
cd <프로젝트 경로> && claude --dangerously-skip-permissions
```

### 2-3. 3계급 에이전트 자율 전환 시스템

항상 똑같이 매매하는 바보가 아닙니다. 시장의 전체 온도(FGI 공포탐욕지수, 추세 이탈률 등)에 따라 시스템 최상단의 **감독관(Orchestrator)** 봇이 상황 파악 후 다음 3명의 행동대장 중 한 명을 교체 투입시킵니다:

| 에이전트 | 발동 조건 | 전략 특성 |
|---------|-----------|----------|
| 🛡️ **보수적(Conservative)** | `danger_score ≥ 70` | 대규모 하락장/폭락장에서 자산을 현금화하여 보호, 진입 타점 극한으로 좁혀 바닥 긁음 |
| ⚖️ **보통(Moderate)** | 횡보 (danger < 25, opp < 25) | 박스권/추세 횡보장에서 안정적인 수익 보상을 챙김 |
| 🔥 **공격적(Aggressive)** | `opp_score ≥ 60 & danger < 30` | 대상승장에서 과감히 올라타 잦은 회전율로 익절폭 넓힘 |

**감독 에이전트(Orchestrator)의 판단 지표:**

```
위험도(danger_score, 0~100):
  • 연속 손절 (10점/회, 최대 30점)
  • 24h -3% 이상 급락 (최대 25점)
  • BTC 과다 보유 30% 초과 시 가산
  • 김치 프리미엄 과열 3%+ (최대 15점)

기회(opportunity_score, 0~100):
  • 극단적 공포 FGI ≤ 25 (최대 25점)
  • RSI 과매도 < 35 (최대 20점)
  • 반등 중 24h +1%+ (최대 15점)
  • Data Fusion 강세 strong_buy (20점)
```

### 2-4. 자동 긴급정지 시스템 (Lifeline)

- **발동 조건**: 4h -10% 급락, cascade+danger 동시 극단, 외부 약세 5개+ 겹침, **연속손절 5회+**
- **발동 시**: 전량 매도 + 매수 차단 + 텔레그램 알림 (`data/auto_emergency.json` 플래그 생성)
- **해제 조건**: 12시간 경과 + 급락 종료 + 공포 완화 시 자동 해제
- ⚠️ 사용자가 수동 발동한 `.env EMERGENCY_STOP=true`는 감독 에이전트가 해제할 수 없습니다

### 2-5. 안전장치 파라미터 일람표

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `DRY_RUN` | `true` | true: 분석만, false: 실제 매매 |
| `MAX_TRADE_AMOUNT` | `100000` | 1회 매매 금액 상한 (KRW) |
| `MAX_DAILY_TRADES` | `6` | 일일 매매 횟수 상한 |
| `MAX_POSITION_RATIO` | `0.5` | 총 자산 대비 최대 투자 비율 |
| `MIN_TRADE_INTERVAL_HOURS` | `4` | 최소 매매 간격 (시간) |
| `EMERGENCY_STOP` | `false` | true: 모든 매매 즉시 중지 (수동) |

---

## 3. 🌶️ 김치랑 봇 (Kimchirang 델타 뉴트럴 차익거래)

이 모듈은 업비트(비트코인 현물 매수)와 바이낸스(비트코인 선물 공매도)를 동시에 잡아, 비트가 1억을 가든 100만원이 되든 원금 가격 하락과 상승에는 전혀 상관받지 않는 **무위험 매매(델타 뉴트럴)**를 추구하는 엔진입니다.

```bash
# 연습모드 (DRY_RUN)
python -m kimchirang.main

# 실제 매매 모드
🍎 Mac/Linux: KR_DRY_RUN=false python -m kimchirang.main
🪟 Windows (PS): $env:KR_DRY_RUN="false"; python -m kimchirang.main
```

**작동 원리:**
- 한국 거래소의 코인 가격이 비정상적으로 비쌀 때 **(김치 프리미엄 3% 이상)** 진입
- 가격 차이가 국제 시세와 맞춰질 때 **(0.5% 이하)** 양쪽 포지션을 날려버려 가운데 낀 마진갭만 취득
- 세부 진입/청산 수치는 `kimchirang/config.py` 파일 내에서 직접 커스텀 조율 가능

---

## 4. 🧬 스캘프 ML 시스템 (scalp_ml — 단타 머신러닝)

순수 AI(LLM/RL)가 아닌 **LightGBM + DQN + 강화학습** 기반의 초단타(스캘핑) 전용 머신러닝 엔진입니다.

| 파일 | 역할 |
|------|------|
| `scalp_ml/collect_real_data.py` | 실 거래 데이터 수집 (호가, 체결, 캔들) |
| `scalp_ml/feature_engineer.py` | 100+ 기술적 피처 생성 |
| `scalp_ml/train_lgbm.py` | LightGBM 분류 모델 훈련 |
| `scalp_ml/train_exit_dqn.py` | DQN 기반 청산 타이밍 모델 훈련 |
| `scalp_ml/win_rate_hunter.py` | 승률 최적 파라미터 탐색 |
| `scalp_ml/distributed_training.py` | 분산 병렬 훈련 시스템 |
| `scalp_ml/auto_train_loop.py` | 주기적 자동 재훈련 루프 |
| `scalp_ml/enrich_real_data.py` | 실거래 데이터 피처 강화 (v3 오더북 포함) |

> **실험 결과**: 실 데이터 환경(슬리피지, 수수료 포함)에서 압도적 승률을 가진 공식을 찾는 것은 여전히 매우 어렵습니다. 현재도 지속적인 개선 중입니다.

---

## 5. 🧠 RL 하이브리드 두뇌 (rl_hybrid — PPO + RAG + Gemini)

강화학습(PPO) + RAG 벡터 검색 + Gemini 2.5 Pro 3중 합의 구조의 최상위 판단 시스템입니다.

```bash
# 전체 시스템 실행 (메인 런처)
python rl_hybrid/launchers/start_all.py

# 개별 워커 실행
python rl_hybrid/launchers/start_rl_worker.py       # RL 추론 워커
python rl_hybrid/launchers/start_llm_worker.py      # LLM 판단 워커
python rl_hybrid/launchers/start_trading_worker.py  # 매매 실행 워커
python rl_hybrid/launchers/run_1h_training.py       # 1시간 주기 재훈련
python rl_hybrid/launchers/run_monthly_training.py  # 월별 배치 훈련
```

### 아키텍처 구성

```
rl_hybrid/
├── launchers/          ← 각 워커 프로세스 런처
├── nodes/              ← 각 판단 노드 (LLM Node, RL Node, Trading Node)
├── rl/                 ← PPO 강화학습 모델 코어
├── rag/                ← Gemini 임베딩 + 벡터 검색 RAG 엔진
└── supabase/           ← RL 특화 DB 접근 레이어
```

### RAG 벡터 검색 시스템

1. 매매 결정 시 시장 상황 전체를 **Gemini 임베딩**으로 벡터화 → Supabase `decision_embeddings` 테이블에 저장
2. 새로운 시장 상황 발생 시 **코사인 유사도**로 가장 유사한 과거 패턴 자동 검색
3. 유사 과거 패턴의 결과(수익/손실)를 현재 판단에 주입 → **자기 기억 기반 메타인지 의사결정**

---

## 6. 📰 뉴스랑 (NewsRang — 11소스 실시간 외부 데이터 수집기)

`agents/external_data.py`의 **뉴스랑(NewsRang)** 에이전트가 11가지 소스에서 병렬로 외부 데이터를 수집하여 종합 시그널을 생성합니다.

| 소스 | API / 방법 | 데이터 내용 |
|------|-----------|------------|
| RSS 피드 (16개) | feedparser | 크립토+매크로 뉴스 실시간 수집 |
| X(트위터) | twikit GraphQL | 7계정 모니터링 + 3키워드 검색 + 고래 감지 |
| CryptoCompare | min-api.cryptocompare.com | 뉴스 감성 + 소셜 통계 |
| CoinGecko | api.coingecko.com | 커뮤니티 감성 투표 |
| Tavily Search | api.tavily.com | 실시간 뉴스 검색 + 감성 분석 |
| Binance Futures | fapi.binance.com | 롱숏비율, 펀딩비, OI (무료) |
| mempool.space | mempool.space/api | 블록체인 고래 추적 + 거래소 입출금 패턴 |
| Yahoo Finance | query1.finance.yahoo.com | S&P500, DXY, 금, 유가, 10Y 국채 |
| Alternative.me | api.alternative.me/fng/ | 공포/탐욕 지수 (FGI) |
| Upbit | api.upbit.com/v1 | 시세, 호가, 캔들, ETH/BTC 비율 |
| Playwright | headless Chromium | 차트 스크린샷 캡처 |

**Data Fusion 종합 점수**: 위 11개 소스의 신호를 가중 합산하여 `strong_buy / buy / neutral / sell / strong_sell` 5단계 종합 의견으로 추출합니다.

---

## 7. 📱 텔레그램 알림 및 시스템 스케줄링

매수 시작, 매수 체결, 수익 혹은 손절 청산 그리고 각종 에러나 긴급 중지 프로세스까지, 코드가 움직이는 모든 과정이 모바일 **텔레그램으로 매우 상세한 리포트와 함께 실시간 전송**됩니다.

| 알림 유형 | 내용 |
|----------|------|
| 매매 실행 시 | 결정(매수/매도/관망), 금액, 근거 요약, 포트폴리오 변동 |
| 에이전트 전환 시 | 전환 사유, 이전/현재 전략, 시장 점수 |
| 에러 발생 시 | 에러 Phase, 에러 메시지, 영향 범위 |
| 자동 긴급정지 시 | 발동 사유, 매도 결과, 복구 예정 시간 |
| 일일 요약 | 당일 거래 횟수, 수익률, 포트폴리오 현황 |

### 시스템 스케줄링

앱이 꺼지지 않고 주기적으로 돌아가게끔 하기 위해 켜놓는 스케줄링이 필요합니다.

- **Windows 시스템**: 내 컴퓨터 좌하단 검색창에서 **작업 스케줄러**를 열고, 4시간 주기로 `python.exe` 가 이 프로젝트의 `scripts/run_agents.py` 를 실행하도록 등록해둡니다.
- **Mac / Linux 시스템**: 리눅스 내장 기능인 cron 을 활용합니다.
  ```bash
  bash scripts/setup_cron.sh install
  ```

---

## 8. 🗄️ Supabase 데이터베이스 구조 (50개 마이그레이션)

v1.29.0 기준, 총 **50개의 마이그레이션 파일**로 구축된 정교한 데이터 인프라입니다.

| 마이그레이션 범위 | 핵심 테이블 | 역할 |
|----------------|------------|------|
| `001~009` | `decisions`, `portfolio_snapshots`, `market_data`, `agent_switches` | 매매 결정, 포트폴리오, 시장 데이터, 에이전트 전환 이력 |
| `010~013` | `decision_aftermath`, `signal_attempt_log`, `near_miss_veto`, `execution_failures` | 매매 사후 분석, 시그널 시도 로그, 아슬아슬 거절, 실행 실패 |
| `014~016` | `decision_embeddings`, `decision_linkage`, `rag_analysis_vectors` | RAG 벡터 검색용 임베딩 테이블 |
| `017~019` | `rl_training_log`, `training_results`, `rl_comprehensive_tracking` | 강화학습 훈련 이력 및 결과 |
| `020~022` | `kimchirang_trades`, `kimchirang_extended` | 김치랑 차익거래 전용 로그 |
| `023` | `app_changelog` | 앱 버전 변경 이력 |
| `024~028` | `scalp_ml` 시리즈, `compute_workers`, `telegram_messages` | 스캘프 ML, 분산 학습 워커, 텔레그램 메시지 로그 |
| `029~038` | contacts, RLS 보안, machine_name, training_impact, feedback_hub, regime | 보안, 다중 머신 지원, 피드백 허브 |
| `039~045` | `altrang`, `newsrang_signals`, `decision_embeddings(Gemini 통합)` | 알트랑 봇, 뉴스랑 신호 테이블, Gemini 임베딩 통합 |

---

## 9. 🏗️ 전체 프로젝트 패키지 구조

살아 움직이는 유기체처럼 여러 장기 기관들이 존재합니다.

```
claude-coin-trading-main/           ← v1.29.0
├── README.md                       ← (이 파일) 종합 사용자 안내서
├── CLAUDE.md                       ← Claude AI 전용 시스템 프롬프트 (교육 커리큘럼 포함)
├── VERSION                         ← 현재 버전 (시맨틱 버전 관리)
├── strategy.md                     ← 자연어로 작성된 매매 전략 (LLM이 해석)
├── .env                            ← API 키 및 안전장치 파라미터 (git 제외)
├── .env.example                    ← API 키 템플릿
├── requirements.txt                ← 파이썬 의존성 패키지 목록
├── setup.sh                        ← 자동 초기 설정 스크립트
│
├── agents/                         ← 에이전트 자율 매매 시스템
│   ├── base_agent.py               ← 추상 기본 클래스 (점수제 매수, 하이브리드 손절)
│   ├── conservative.py             ← 🛡️ 보수적 에이전트 (자산 보전)
│   ├── moderate.py                 ← ⚖️ 보통 에이전트 (균형 매매)
│   ├── aggressive.py               ← 🔥 공격적 에이전트 (고수익)
│   ├── external_data.py            ← 뉴스랑(NewsRang) — 11소스 병렬 수집
│   └── orchestrator.py             ← 감독 에이전트 (자율 전환 + DB 학습)
│
├── kimchirang/                     ← 바이낸스 연계 김프 차익거래 봇
│   └── config.py                   ← 진입/청산 기준 커스텀 파라미터
│
├── rl_hybrid/                      ← PPO 강화학습 + RAG + Gemini 하이브리드 두뇌
│   ├── launchers/                  ← 각 워커 프로세스 런처 (start_all.py 등)
│   ├── nodes/                      ← LLM/RL/Trading 판단 노드
│   ├── rl/                         ← PPO 모델 코어
│   ├── rag/                        ← Gemini 임베딩 + 벡터 검색 RAG 엔진
│   └── config.py                   ← RL 하이브리드 시스템 설정
│
├── scalp_ml/                       ← LightGBM + DQN 단타 머신러닝 엔진
│   ├── collect_real_data.py        ← 실 거래 데이터 수집
│   ├── feature_engineer.py         ← 100+ 기술적 피처 생성
│   ├── train_lgbm.py               ← LightGBM 모델 훈련
│   ├── train_exit_dqn.py           ← DQN 청산 타이밍 모델 훈련
│   ├── win_rate_hunter.py          ← 승률 최적 파라미터 탐색
│   ├── distributed_training.py     ← 분산 병렬 훈련
│   └── auto_train_loop.py          ← 자동 주기적 재훈련
│
├── scripts/                        ← 보조 스크립트 모음
│   ├── collect_market_data.py      ← Upbit 시장 데이터 + 기술지표
│   ├── collect_fear_greed.py       ← 공포탐욕지수 수집
│   ├── collect_news.py             ← Tavily 뉴스 수집
│   ├── collect_rss_news.py         ← RSS 뉴스 16피드 수집
│   ├── collect_x_signals.py        ← X(트위터) 시그널 수집
│   ├── collect_social_sentiment.py ← 소셜 감성 (CryptoCompare+CoinGecko)
│   ├── collect_ai_signal.py        ← AI 복합 시그널 (6가지 실시간 분석)
│   ├── capture_chart.py            ← Playwright 차트 캡처
│   ├── execute_trade.py            ← 매매 실행 (안전장치 내장)
│   ├── get_portfolio.py            ← 포트폴리오 조회
│   ├── short_term_trader.py        ← AI 단타 트레이딩 (뉴스/급등급락/고래 3전략)
│   ├── notify_telegram.py          ← 텔레그램 알림 전송
│   ├── version_manager.py          ← 버전 및 변경이력 관리
│   ├── run_agents.sh               ← 에이전트 모드 파이프라인
│   └── setup_cron.sh               ← cron 등록/해제 도우미
│
├── utils/                          ← 공통 유틸리티
│   ├── machine.py                  ← 머신 ID 및 멀티머신 지원
│   └── newsrang_reader.py          ← 뉴스랑 데이터 읽기 유틸
│
├── tools/                          ← 분석 도구
│   ├── dujjoncu_analysis.html      ← 뚱뚱한 분석 대시보드 (HTML)
│   └── bubblemaps_viewer.html      ← 버블맵 뷰어
│
├── web/                            ← 웹 인터페이스
│   ├── index.html                  ← 메인 대시보드
│   ├── remote.html                 ← 원격 제어 페이지
│   └── kimchirang-guide.md         ← 김치랑 상세 가이드
│
├── prompts/schemas/                ← 매매 결정 JSON 스키마
├── data/                           ← 런타임 데이터 (차트, 스냅샷, 에이전트 상태)
├── logs/                           ← 실행 로그 및 Claude 응답 원본
└── supabase/migrations/            ← DB 테이블 초기 셋팅용 SQL 파일 (50개)
```

---

## 10. 🚫 면책 조항 및 최후 당부

이 프로그램은 상업성이 없는 완전 오픈소스로, **개인 연구, 학습용 자동화 파이썬 스크립트**일 뿐입니다. 수익을 백프로 보장하거나 투자를 권유하는 도구가 절대 아닙니다.

시스템에 숨겨진 로직 버그, 서버 인스턴스 다운, API 연동 단절, 그리고 전 지구적 비트코인 급락/급등으로 인해 발생하는 **모든 암호화폐 투자 및 금전적 손실의 법적·도의적 책임은 프로그램 사용과 설치를 결심한 사용자 본인에게 있습니다.**

> ⚠️ **실제 내 자산을 투입하기 전 저와 3가지를 약속해주세요:**
> 1. 환경변수를 `DRY_RUN=true` 로 한 채 최소 일주일, 이주일 모의 테스트로 이 앱을 구경만 하십시오.
> 2. 실제 매매로 전환할 때(DRY_RUN=false), 초기 자본금은 잃어도 상관없는 1~2만원의 티끌 같은 극소액으로만 첫 단추를 채우세요.
> 3. AI나 자동매매는 완벽하지 않습니다. 앱이 언제든 오작동하여 당신의 돈으로 물타기를 반복할 수 있다는 보수적 공포감을 견지하시고, 틈틈이 텔레그램을 주시하며, 비상시엔 모바일 업비트로 즉시 강제 매도 및 `.env` 파일의 `EMERGENCY_STOP=true` 를 적극적으로 활용하세요.

---

<p align="center">
  <sub>이 앱은 한순간의 일확천금을 복사해 주는 마법의 버튼이 결코 아닙니다.<br/><b>파이썬과 AI의 탐구</b>, 그리고 <b>인공신경망 딥러닝의 실전 데이터 적용 한계</b>를 온몸으로 배우고,<br/>오류를 스스로 치유하며 데이터의 바다를 서핑하는 자율 생명체를 만들어가는 즐거움을 목적 삼아 공유합니다.</sub>
</p>

<p align="center">
  <sub>Inspired by <a href="https://github.com/dandacompany"><b>dantelabs</b></a>, Heavily recreated & modified by <b>Dr. Jang Jaeho</b>.</sub>
</p>

<p align="center">
  <sub>📦 Current Version: <b>v1.29.0</b> | 🗄️ DB Migrations: <b>50개</b> | 🤖 AI Core: <b>Gemini 2.5 Pro + PPO RL + RAG</b></sub>
</p>
