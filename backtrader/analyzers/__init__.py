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
# Backtrader 성과 분석기(Analyzers) 패키지 초기화 파일
# =============================================================================
# 이 패키지는 백테스팅 결과를 분석하고 성과 지표를 계산하는 다양한 분석기들을 포함합니다.
# 
# 주요 분석기 카테고리:
# - 수익률 분석: 연간 수익률, 기간별 수익률, 로그 수익률 등
# - 위험 분석: 샤프 비율, 칼마 비율, 최대 낙폭, 변동성 등
# - 거래 분석: 거래 통계, 포지션 분석, 거래 내역 등
# - 포트폴리오 분석: PyFolio 통합, 레버리지, VWR 등
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# The modules below should/must define __all__ with the objects wishes
# or prepend an "_" (underscore) to private classes/variables
# 아래 모듈들은 __all__을 정의하거나 private 클래스/변수에 "_"를 붙여야 합니다

# =============================================================================
# 핵심 성과 분석기 모듈들 임포트
# =============================================================================
from .annualreturn import *      # 연간 수익률 분석
from .drawdown import *          # 최대 낙폭 분석
from .timereturn import *        # 기간별 수익률 분석
from .sharpe import *            # 샤프 비율 분석
from .tradeanalyzer import *     # 거래 통계 분석
from .sqn import *               # 시스템 품질 수치 분석
from .leverage import *          # 레버리지 분석
from .positions import *         # 포지션 분석
from .transactions import *      # 거래 내역 분석
from .pyfolio import *           # PyFolio 통합 분석
from .returns import *           # 일반 수익률 분석
from .vwr import *               # 변동성 가중 수익률 분석

# =============================================================================
# 추가 성과 분석기 모듈들 임포트
# =============================================================================
from .logreturnsrolling import * # 롤링 로그 수익률 분석

from .calmar import *            # 칼마 비율 분석
from .periodstats import *       # 기간별 통계 분석
