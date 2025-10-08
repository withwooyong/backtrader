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
# 시간 프레임별 수익률(Time Return) 분석기 모듈
# =============================================================================
# 이 모듈은 지정된 시간 프레임(연간, 월간, 주간, 일간 등)에 따른 수익률을 계산합니다.
# 각 시간 프레임의 시작과 끝 시점을 기준으로 수익률을 산출하여
# 전략의 시간별 성과를 분석할 수 있습니다.
# 
# 주요 특징:
# - 다양한 시간 프레임 지원 (연간, 월간, 주간, 일간, 시간 등)
# - 포트폴리오 가치 또는 특정 자산 가격 기준 수익률 계산
# - 시간 프레임 경계에서의 수익률 계산 방식 설정 가능
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from backtrader import TimeFrameAnalyzerBase


# =============================================================================
# TimeReturn 클래스 - 시간 프레임별 수익률 분석기
# =============================================================================
# 이 클래스는 지정된 시간 프레임에 따라 수익률을 계산합니다.
# 포트폴리오 가치 또는 특정 자산의 가격 변화를 기준으로 수익률을 산출합니다.
class TimeReturn(TimeFrameAnalyzerBase):
    '''This analyzer calculates the Returns by looking at the beginning
    and end of the timeframe

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

      - ``data`` (default: ``None``)

        Reference asset to track instead of the portfolio value.

        .. note:: this data must have been added to a ``cerebro`` instance with
                  ``addata``, ``resampledata`` or ``replaydata``

      - ``firstopen`` (default: ``True``)

        When tracking the returns of a ``data`` the following is done when
        crossing a timeframe boundary, for example ``Years``:

          - Last ``close`` of previous year is used as the reference price to
            see the return in the current year

        The problem is the 1st calculation, because the data has** no
        previous** closing price. As such and when this parameter is ``True``
        the *opening* price will be used for the 1st calculation.

        This requires the data feed to have an ``open`` price (for ``close``
        the standard [0] notation will be used without reference to a field
        price)

        Else the initial close will be used.

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('data', None),        # 추적할 자산 데이터 (None이면 포트폴리오 가치 사용)
        ('firstopen', True),   # 첫 번째 계산 시 시가 사용 여부
        ('fund', None),        # 펀드 모드 설정 (None이면 브로커 설정 자동 감지)
    )

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(TimeReturn, self).start()
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

        self._value_start = 0.0
        self._lastvalue = None
        if self.p.data is None:
            # keep the initial portfolio value if not tracing a data
            if not self._fundmode:
                self._lastvalue = self.strategy.broker.getvalue()
            else:
                self._lastvalue = self.strategy.broker.fundvalue

    def notify_fund(self, cash, value, fundvalue, shares):
        if not self._fundmode:
            # Record current value
            if self.p.data is None:
                self._value = value  # the portofolio value if tracking no data
            else:
                self._value = self.p.data[0]  # the data value if tracking data
        else:
            if self.p.data is None:
                self._value = fundvalue  # the fund value if tracking no data
            else:
                self._value = self.p.data[0]  # the data value if tracking data

    def on_dt_over(self):
        # next is called in a new timeframe period
        # if self.p.data is None or len(self.p.data) > 1:
        if self.p.data is None or self._lastvalue is not None:
            self._value_start = self._lastvalue  # update value_start to last

        else:
            # The 1st tick has no previous reference, use the opening price
            if self.p.firstopen:
                self._value_start = self.p.data.open[0]
            else:
                self._value_start = self.p.data[0]

    def next(self):
        # Calculate the return
        super(TimeReturn, self).next()
        self.rets[self.dtkey] = (self._value / self._value_start) - 1.0
        self._lastvalue = self._value  # keep last value
