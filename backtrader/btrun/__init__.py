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
# Backtrader 실행(BTRun) 패키지 초기화 모듈
# =============================================================================
# 이 모듈은 Backtrader 전략을 실행하고 관리하기 위한
# 고급 실행 도구들을 제공합니다.
# 
# 주요 기능:
# - 전략 실행 및 모니터링
# - 백테스팅 결과 분석
# - 실시간 거래 실행
# - 성능 최적화 및 튜닝
# 
# btrun 모듈은 Backtrader의 핵심 실행 엔진으로,
# 복잡한 전략 실행 시나리오를 단순화합니다.
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# =============================================================================
# btrun 함수 임포트
# =============================================================================
# 이 함수는 Backtrader 전략을 실행하는 메인 엔트리 포인트입니다.
from .btrun import btrun
