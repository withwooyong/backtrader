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
# 칼마 비율(Calmar Ratio) 분석기 모듈
# =============================================================================
# 이 모듈은 칼마 비율을 계산합니다.
# 칼마 비율은 연간 수익률을 최대 낙폭으로 나눈 값으로,
# 위험 대비 수익률을 측정하는 중요한 지표입니다.
# 
# 주요 특징:
# - 연간 수익률 대비 최대 낙폭 비율 계산
# - 다양한 시간 프레임 지원
# - 롤링 윈도우 방식으로 동적 계산
# - 펀드 모드 지원
# 
# 칼마 비율 공식:
# Calmar Ratio = 연간 수익률 / 최대 낙폭
# 
# 칼마 비율 해석:
# - 높을수록 위험 대비 수익률이 좋음
# - 일반적으로 1.0 이상이면 좋은 전략
# - 2.0 이상이면 우수한 전략
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from . import TimeDrawDown


__all__ = ['Calmar']


# =============================================================================
# Calmar 클래스 - 칼마 비율 분석기
# =============================================================================
# 이 클래스는 칼마 비율을 계산합니다.
# 기본 데이터와 다른 시간 프레임을 사용할 수 있으며,
# 롤링 윈도우 방식으로 동적으로 칼마 비율을 계산합니다.
class Calmar(bt.TimeFrameAnalyzerBase):
    '''This analyzer calculates the CalmarRatio
    timeframe which can be different from the one used in the underlying data
    Params:

      - ``timeframe`` (default: ``None``)
        If ``None`` the ``timeframe`` of the 1st data in the system will be
        used

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used
      - *None*

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    See also:

      - https://en.wikipedia.org/wiki/Calmar_ratio

    Methods:
      - ``get_analysis``

        Returns a OrderedDict with a key for the time period and the
        corresponding rolling Calmar ratio

    Attributes:
      - ``calmar`` the latest calculated calmar ratio
    '''

    # =============================================================================
    # 필요한 패키지 정의
    # =============================================================================
    packages = ('collections', 'math',)

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('timeframe', bt.TimeFrame.Months),  # default in calmar (기본값: 월별)
        ('period', 36),                      # 롤링 윈도우 기간 (기본값: 36개월)
        ('fund', None),                      # 펀드 모드 설정 (None이면 자동 감지)
    )

    def __init__(self):
        # =============================================================================
        # 하위 분석기 초기화
        # =============================================================================
        # TimeDrawDown 분석기를 사용하여 최대 낙폭 계산
        self._maxdd = TimeDrawDown(timeframe=self.p.timeframe,
                                   compression=self.p.compression)

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        self._mdd = float('-inf')  # 최대 낙폭 초기화 (음의 무한대)
        
        # =============================================================================
        # 롤링 윈도우를 위한 값 저장소 초기화
        # =============================================================================
        # 지정된 기간만큼 NaN 값으로 초기화된 덱 생성
        self._values = collections.deque([float('Nan')] * self.p.period,
                                         maxlen=self.p.period)
        
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

        # =============================================================================
        # 초기 가치 설정
        # =============================================================================
        if not self._fundmode:
            # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
            self._values.append(self.strategy.broker.getvalue())
        else:
            # 펀드 모드인 경우: 펀드 가치 사용
            self._values.append(self.strategy.broker.fundvalue)

    def on_dt_over(self):
        self._mdd = max(self._mdd, self._maxdd.maxdd)
        if not self._fundmode:
            self._values.append(self.strategy.broker.getvalue())
        else:
            self._values.append(self.strategy.broker.fundvalue)
        rann = math.log(self._values[-1] / self._values[0]) / len(self._values)
        self.calmar = calmar = rann / (self._mdd or float('Inf'))

        self.rets[self.dtkey] = calmar

    def stop(self):
        self.on_dt_over()  # update last values
