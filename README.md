# Backtrader - Python 백테스팅 및 트레이딩 플랫폼

[![PyPI Version](https://img.shields.io/pypi/v/backtrader.svg)](https://pypi.python.org/pypi/backtrader/)
[![License](https://img.shields.io/pypi/l/backtrader.svg)](https://github.com/backtrader/backtrader/blob/master/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/backtrader.svg)](https://pypi.python.org/pypi/backtrader/)

## 📖 프로젝트 개요

**Backtrader**는 Python으로 작성된 강력하고 유연한 백테스팅 및 라이브 트레이딩 플랫폼입니다. 금융 시장에서 트레이딩 전략을 개발하고, 과거 데이터로 성과를 검증하며, 실제 시장에서 자동으로 거래할 수 있도록 도와줍니다.

### 🎯 주요 특징

- **백테스팅**: 과거 데이터로 트레이딩 전략의 성과 검증
- **라이브 트레이딩**: 실제 시장에서 자동 거래 실행
- **다양한 데이터 소스**: CSV, Yahoo Finance, Interactive Brokers, OANDA 등
- **풍부한 기술적 지표**: 120개 이상의 내장 지표
- **유연한 전략 개발**: Python 클래스 기반의 직관적인 전략 작성
- **시각화**: matplotlib을 활용한 차트 및 성과 분석

## 🏗️ 프로젝트 구조

```
backtrader/
├── backtrader/           # 핵심 라이브러리
│   ├── __init__.py      # 메인 패키지 초기화
│   ├── cerebro.py       # 백테스팅 엔진 핵심
│   ├── strategy.py      # 전략 기본 클래스
│   ├── broker.py        # 브로커 시뮬레이션
│   ├── feeds/           # 데이터 피드 모듈
│   ├── indicators/      # 기술적 지표 모듈
│   ├── analyzers/       # 성과 분석 모듈
│   ├── observers/       # 거래 관찰 모듈
│   └── sizers/          # 포지션 크기 결정 모듈
├── samples/              # 사용 예제
├── tests/                # 테스트 코드
├── contrib/              # 추가 기능 및 유틸리티
└── docs/                 # 문서
```

## 🔄 서비스 플로우

### 1. 백테스팅 프로세스

```
데이터 준비 → 전략 정의 → 백테스팅 실행 → 결과 분석 → 전략 최적화
```

### 2. 라이브 트레이딩 프로세스

```
실시간 데이터 수신 → 전략 신호 생성 → 주문 실행 → 포지션 관리 → 성과 모니터링
```

## 📁 상세 모듈 구조

### 🧠 핵심 모듈 (Core Modules)

#### `cerebro.py` - 백테스팅 엔진

- **역할**: 전체 백테스팅 프로세스를 조율하는 중앙 제어 시스템
- **주요 기능**:
  - 데이터 피드 관리
  - 전략 실행 및 관리
  - 브로커 시뮬레이션
  - 결과 수집 및 분석
- **핵심 클래스**: `Cerebro`

#### `strategy.py` - 전략 기본 클래스

- **역할**: 모든 트레이딩 전략의 기본이 되는 추상 클래스
- **주요 기능**:
  - 전략 초기화 및 실행
  - 주문 관리
  - 거래 기록
  - 포지션 관리
- **핵심 클래스**: `Strategy`, `SignalStrategy`

#### `broker.py` - 브로커 시뮬레이션

- **역할**: 거래 실행 및 포트폴리오 관리를 담당
- **주요 기능**:
  - 주문 처리
  - 수수료 계산
  - 현금 및 포지션 관리
  - 슬리피지 시뮬레이션

### 📊 데이터 피드 모듈 (Data Feed Modules)

#### `feeds/` - 데이터 소스 관리

- **`yahoo.py`**: Yahoo Finance에서 주식 데이터 다운로드
- **`csvgeneric.py`**: CSV 파일에서 데이터 읽기
- **`pandafeed.py`**: Pandas DataFrame을 데이터 소스로 사용
- **`ibdata.py`**: Interactive Brokers 실시간 데이터
- **`oanda.py`**: OANDA 외환 데이터

### 📈 기술적 지표 모듈 (Technical Indicators)

#### `indicators/` - 120개 이상의 내장 지표

- **추세 지표**:
  - `sma.py`: 단순이동평균
  - `ema.py`: 지수이동평균
  - `bollinger.py`: 볼린저 밴드
- **모멘텀 지표**:
  - `rsi.py`: 상대강도지수
  - `macd.py`: MACD
  - `stochastic.py`: 스토캐스틱
- **변동성 지표**:
  - `atr.py`: 평균진폭
  - `bbands.py`: 볼린저 밴드
- **사용자 정의 지표**: `indicator.py`를 상속받아 커스텀 지표 개발 가능

### 📊 분석 모듈 (Analysis Modules)

#### `analyzers/` - 성과 분석 도구

- **`returns.py`**: 수익률 계산
- **`sharpe.py`**: 샤프 비율
- \*\*`drawdown.py`: 최대 낙폭
- **`sqn.py`**: 시스템 품질 수치
- **`pyfolio.py`**: PyFolio 통합 분석

#### `observers/` - 거래 관찰 도구

- **`broker.py`**: 브로커 상태 모니터링
- **`trades.py`**: 거래 기록 추적
- **`drawdown.py`**: 낙폭 모니터링
- **`logreturns.py`**: 로그 수익률 기록

### 🎯 전략 모듈 (Strategy Modules)

#### `strategies/` - 기본 전략 템플릿

- **`sma_crossover.py`**: 이동평균 교차 전략 예제

### 📏 포지션 크기 모듈 (Position Sizing)

#### `sizers/` - 포지션 크기 결정

- **`fixedsize.py`**: 고정 크기
- **`percents_sizer.py`**: 비율 기반 크기

### 🔧 유틸리티 모듈 (Utility Modules)

#### `utils/` - 도우미 함수들

- **`date.py`**: 날짜 변환 유틸리티
- \*\*`autodict.py`: 자동 딕셔너리 생성
- **`py3.py`**: Python 2/3 호환성

## 🚀 사용 예제

### 기본 사용법

```python
import backtrader as bt
from datetime import datetime

# 1. 전략 클래스 정의
class SmaCross(bt.Strategy):
    params = dict(sma1=10, sma2=30)

    def __init__(self):
        # 이동평균 계산
        self.sma1 = bt.ind.SMA(period=self.params.sma1)
        self.sma2 = bt.ind.SMA(period=self.params.sma2)
        # 교차 신호 생성
        self.crossover = bt.ind.CrossOver(self.sma1, self.sma2)

    def next(self):
        if not self.position:  # 포지션이 없을 때
            if self.crossover > 0:  # 골든 크로스
                self.buy()
        else:  # 포지션이 있을 때
            if self.crossover < 0:  # 데드 크로스
                self.sell()

# 2. 백테스팅 엔진 설정
cerebro = bt.Cerebro()
cerebro.addstrategy(SmaCross)

# 3. 데이터 추가
data = bt.feeds.YahooFinanceData(
    dataname='AAPL',
    fromdate=datetime(2020, 1, 1),
    todate=datetime(2023, 12, 31)
)
cerebro.adddata(data)

# 4. 백테스팅 실행
cerebro.run()

# 5. 결과 시각화
cerebro.plot()
```

### 고급 기능 예제

```python
# 다중 데이터 피드
data1 = bt.feeds.YahooFinanceData(dataname='AAPL')
data2 = bt.feeds.YahooFinanceData(dataname='GOOGL')
cerebro.adddata(data1)
cerebro.adddata(data2)

# 분석기 추가
cerebro.addanalyzer(bt.analyzers.SharpeRatio)
cerebro.addanalyzer(bt.analyzers.DrawDown)

# 결과 분석
results = cerebro.run()
strategy = results[0]
print(f"샤프 비율: {strategy.analyzers.sharperatio.get_analysis()}")
print(f"최대 낙폭: {strategy.analyzers.drawdown.get_analysis()}")
```

## 📦 설치 방법

### 기본 설치

```bash
pip install backtrader
```

### 시각화 기능 포함 설치

```bash
pip install backtrader[plotting]
```

### 추가 의존성 설치

```bash
# Interactive Brokers 연동
pip install git+https://github.com/blampe/IbPy.git

# TA-Lib 지표 지원
pip install TA-Lib

# OANDA 연동
pip install oandapy
```

## 🔧 설정 및 구성

### 환경 설정

```python
# 브로커 설정
cerebro.broker.set_cash(100000)  # 초기 자본
cerebro.broker.setcommission(commission=0.001)  # 수수료

# 데이터 전처리 설정
cerebro.adddata(data, preload=True)  # 데이터 미리 로드
cerebro.adddata(data, runonce=True)  # 벡터화 모드 실행
```

### 로깅 설정

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 📊 성능 최적화

### 백테스팅 속도 향상

- `runonce=True`: 벡터화 모드 사용
- `preload=True`: 데이터 미리 로드
- `maxcpus`: 멀티프로세싱 활용

### 메모리 사용량 최적화

- 필요한 데이터만 로드
- 불필요한 지표 제거
- 데이터 리샘플링 활용

## 🧪 테스트 및 검증

### 단위 테스트

```bash
python -m pytest tests/
```

### 전략 검증

```python
# Walk Forward Analysis
cerebro.optstrategy(SmaCross, sma1=range(5, 15), sma2=range(20, 40))
```

## 📚 학습 리소스

### 공식 문서

- [Backtrader 공식 문서](http://www.backtrader.com/docu)
- [블로그](http://www.backtrader.com/blog)
- [지표 참조](http://www.backtrader.com/docu/indautoref.html)

### 샘플 코드

- `samples/` 디렉토리의 다양한 예제
- `contrib/samples/`의 고급 예제

### 커뮤니티

- [커뮤니티 포럼](https://community.backtrader.com)
- [GitHub Issues](https://github.com/backtrader/backtrader/issues)

## 🤝 기여 방법

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 라이선스

이 프로젝트는 GNU General Public License v3.0 하에 배포됩니다.

## 👨‍💻 개발자

- **Daniel Rodriguez** - 메인 개발자
- **Email**: danjrod@gmail.com
- **GitHub**: [mementum](https://github.com/mementum)

## 🔄 버전 정보

현재 버전: 1.9.78.123

- X.Y.Z.I 형식
- X: 메이저 버전
- Y: 마이너 버전
- Z: 리비전 버전
- I: 내장 지표 개수

---

**Backtrader**로 트레이딩 전략을 개발하고 백테스팅해보세요! 🚀📈
