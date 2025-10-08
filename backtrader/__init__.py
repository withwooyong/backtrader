#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

# =============================================================================
# Backtrader 메인 패키지 초기화 파일
# =============================================================================
# 이 파일은 Backtrader 패키지의 진입점으로, 모든 주요 모듈들을 임포트하고
# 사용자에게 편리한 인터페이스를 제공합니다.
# 
# 주요 기능:
# - 핵심 클래스들의 직접 임포트
# - 모듈별 별칭 설정
# - 사용자 정의 지표 및 연구 모듈 로드
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from .version import __version__, __btversion__

# =============================================================================
# 에러 및 유틸리티 모듈 임포트
# =============================================================================
from .errors import *          # 모든 에러 클래스들을 임포트
from . import errors as errors # 에러 모듈 자체도 임포트

from .utils import num2date, date2num, time2num, num2time  # 날짜/시간 변환 유틸리티

# =============================================================================
# 핵심 데이터 구조 모듈 임포트
# =============================================================================
from .linebuffer import *      # 라인 버퍼 (가격 데이터 저장 구조)
from .functions import *       # 수학 함수 및 유틸리티

# =============================================================================
# 거래 관련 핵심 모듈 임포트
# =============================================================================
from .order import *           # 주문 클래스들
from .comminfo import *        # 수수료 정보 클래스들
from .trade import *           # 거래 클래스들
from .position import *        # 포지션 클래스들

# =============================================================================
# 스토어 및 브로커 모듈 임포트
# =============================================================================
from .store import Store       # 스토어 기본 클래스

from . import broker as broker # 브로커 모듈
from .broker import *          # 브로커 클래스들

# =============================================================================
# 데이터 시리즈 및 피드 모듈 임포트
# =============================================================================
from .lineseries import *      # 라인 시리즈 (데이터 구조)
from .dataseries import *      # 데이터 시리즈
from .feed import *            # 데이터 피드 기본 클래스들
from .resamplerfilter import * # 데이터 리샘플링 및 필터링

# =============================================================================
# 지표 및 분석 모듈 임포트
# =============================================================================
from .lineiterator import *    # 라인 반복자 (지표 계산 기반)
from .indicator import *       # 지표 기본 클래스
from .analyzer import *        # 분석기 기본 클래스
from .observer import *        # 관찰자 기본 클래스

# =============================================================================
# 전략 및 포지션 관리 모듈 임포트
# =============================================================================
from .sizer import *           # 포지션 크기 결정자 기본 클래스
from .sizers import SizerFix   # 고정 크기 결정자 (이전 버전 호환성)
from .strategy import *        # 전략 기본 클래스들

# =============================================================================
# 출력 및 신호 모듈 임포트
# =============================================================================
from .writer import *          # 결과 출력 모듈
from .signal import *          # 신호 생성 모듈

# =============================================================================
# 백테스팅 엔진 및 타이머 모듈 임포트
# =============================================================================
from .cerebro import *         # 백테스팅 엔진 (핵심)
from .timer import *           # 타이머 기능
from .flt import *             # 필터 모듈

# =============================================================================
# 유틸리티 모듈 임포트
# =============================================================================
from . import utils as utils   # 유틸리티 함수들

# =============================================================================
# 주요 기능 모듈들을 별칭으로 임포트
# =============================================================================
# 사용자가 더 쉽게 접근할 수 있도록 별칭을 제공합니다
from . import feeds as feeds           # 데이터 피드 모듈들
from . import indicators as indicators # 기술적 지표 모듈들
from . import indicators as ind        # indicators의 짧은 별칭
from . import studies as studies       # 연구 모듈들
from . import strategies as strategies # 전략 모듈들
from . import strategies as strats     # strategies의 짧은 별칭
from . import observers as observers   # 관찰자 모듈들
from . import observers as obs         # observers의 짧은 별칭
from . import analyzers as analyzers   # 분석기 모듈들
from . import commissions as commissions # 수수료 모듈들
from . import commissions as comms     # commissions의 짧은 별칭
from . import filters as filters       # 필터 모듈들
from . import signals as signals       # 신호 모듈들
from . import sizers as sizers         # 포지션 크기 결정자 모듈들
from . import stores as stores         # 스토어 모듈들
from . import brokers as brokers       # 브로커 모듈들
from . import timer as timer           # 타이머 모듈

# =============================================================================
# TA-Lib 지표 지원 모듈 임포트
# =============================================================================
from . import talib as talib   # TA-Lib 통합 지표들

# =============================================================================
# 사용자 정의 지표 및 연구 모듈 로드
# =============================================================================
# contrib 디렉토리에 있는 추가 기능들을 자동으로 로드합니다
import backtrader.indicators.contrib    # 사용자 정의 지표들
import backtrader.studies.contrib       # 사용자 정의 연구 모듈들
