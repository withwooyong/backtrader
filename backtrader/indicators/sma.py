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
# 단순이동평균(SMA) 지표 모듈
# =============================================================================
# 이 파일은 가장 기본적이고 널리 사용되는 기술적 지표인 단순이동평균을 구현합니다.
# 주요 특징:
# - 지정된 기간 동안의 가격 데이터의 산술 평균 계산
# - 추세 방향과 강도를 파악하는 데 유용
# - 다른 이동평균 지표들의 기반이 되는 기본 지표
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import MovingAverageBase, Average


# =============================================================================
# MovingAverageSimple 클래스 - 단순이동평균 구현
# =============================================================================
# 이 클래스는 단순이동평균(Simple Moving Average, SMA)을 계산합니다.
# 단순이동평균은 지정된 기간 동안의 모든 가격 데이터에 동일한 가중치를 적용합니다.
class MovingAverageSimple(MovingAverageBase):
    '''
    Non-weighted average of the last n periods

    Formula:
      - movav = Sum(data, period) / period

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Simple_moving_average
    '''
    # =============================================================================
    # 클래스 설정
    # =============================================================================
    alias = ('SMA', 'SimpleMovingAverage',)  # 별칭 설정 (SMA, SimpleMovingAverage로도 사용 가능)
    lines = ('sma',)                          # 출력 라인 이름 설정

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        # 서브클래싱에서 믹스인이 할당 작업을 볼 수 있도록 super() 호출 전에 실행
        
        # =============================================================================
        # 단순이동평균 계산 라인 초기화
        # =============================================================================
        # Average 클래스를 사용하여 지정된 기간 동안의 데이터 평균을 계산
        # self.data: 입력 데이터 (가격 데이터)
        # self.p.period: 이동평균 기간 (사용자가 설정한 파라미터)
        self.lines[0] = Average(self.data, period=self.p.period)

        # 부모 클래스 초기화
        super(MovingAverageSimple, self).__init__()
