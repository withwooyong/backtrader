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
# 수익률 분석기(Returns Analyzer) 모듈
# =============================================================================
# 이 모듈은 백테스팅 결과의 수익률을 다양한 방식으로 계산하고 분석합니다.
# 로그 수익률 방식을 사용하여 총 수익률, 평균 수익률, 복합 수익률, 연간화 수익률을 계산합니다.
# 
# 주요 특징:
# - 로그 수익률 기반 계산으로 정확한 복합 수익률 제공
# - 다양한 시간 프레임 지원
# - 연간화된 수익률 계산으로 다른 전략과의 비교 가능
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase


# =============================================================================
# Returns 클래스 - 수익률 분석기
# =============================================================================
# 이 클래스는 로그 수익률 방식을 사용하여 다양한 수익률 지표를 계산합니다.
# 로그 수익률은 복합 수익률 계산에 더 정확하며, 샤프 비율 계산에도 유리합니다.
class Returns(TimeFrameAnalyzerBase):
    '''Total, Average, Compound and Annualized Returns calculated using a
    logarithmic approach

    See:

      - https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

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

      - ``tann`` (default: ``None``)

        Number of periods to use for the annualization (normalization) of the

        namely:

          - ``days: 252``
          - ``weeks: 52``
          - ``months: 12``
          - ``years: 1``

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

        The returned dict the following keys:

          - ``rtot``: Total compound return
          - ``ravg``: Average return for the entire period (timeframe specific)
          - ``rnorm``: Annualized/Normalized return
          - ``rnorm100``: Annualized/Normalized return expressed in 100%

    '''

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('tann', None),    # 연간화를 위한 기간 수 (None이면 자동 감지)
        ('fund', None),    # 펀드 모드 설정 (None이면 브로커 설정 자동 감지)
    )

    # =============================================================================
    # 시간 프레임별 연간화 상수 정의
    # =============================================================================
    # 각 시간 프레임에 대해 연간화할 때 사용하는 기간 수
    # 예: 일별 데이터는 252일(거래일 기준), 주별 데이터는 52주 등
    _TANN = {
        bt.TimeFrame.Days: 252.0,    # 일별: 252일 (연간 거래일)
        bt.TimeFrame.Weeks: 52.0,    # 주별: 52주
        bt.TimeFrame.Months: 12.0,   # 월별: 12개월
        bt.TimeFrame.Years: 1.0,     # 년별: 1년
    }

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(Returns, self).start()
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

        # =============================================================================
        # 시작 가치 설정
        # =============================================================================
        if not self._fundmode:
            # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
            self._value_start = self.strategy.broker.getvalue()
        else:
            # 펀드 모드인 경우: 펀드 가치 사용
            self._value_start = self.strategy.broker.fundvalue

        self._tcount = 0  # 하위 기간 카운터 초기화

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 최종 수익률 계산
        # =============================================================================
        super(Returns, self).stop()

        # =============================================================================
        # 종료 가치 설정
        # =============================================================================
        if not self._fundmode:
            # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
            self._value_end = self.strategy.broker.getvalue()
        else:
            # 펀드 모드인 경우: 펀드 가치 사용
            self._value_end = self.strategy.broker.fundvalue

        # =============================================================================
        # 복합 수익률 계산 (로그 수익률)
        # =============================================================================
        # Compound return
        # 복합 수익률
        try:
            nlrtot = self._value_end / self._value_start
        except ZeroDivisionError:
            rtot = float('-inf')
        else:
            if nlrtot < 0.0:
                rtot = float('-inf')
            else:
                rtot = math.log(nlrtot)

        self.rets['rtot'] = rtot

        # =============================================================================
        # 평균 수익률 계산
        # =============================================================================
        # Average return
        # 평균 수익률
        self.rets['ravg'] = ravg = rtot / self._tcount

        # =============================================================================
        # 연간화된 정규화 수익률 계산
        # =============================================================================
        # Annualized normalized return
        # 연간화된 정규화 수익률
        tann = self.p.tann or self._TANN.get(self.timeframe, None)
        if tann is None:
            tann = self._TANN.get(self.data._timeframe, 1.0)  # assign default

        if ravg > float('-inf'):
            self.rets['rnorm'] = rnorm = math.expm1(ravg * tann)
        else:
            self.rets['rnorm'] = rnorm = ravg

        self.rets['rnorm100'] = rnorm * 100.0  # human readable % (사람이 읽기 쉬운 백분율)

    def _on_dt_over(self):
        # =============================================================================
        # 시간 프레임 경계에서 하위 기간 카운터 증가
        # =============================================================================
        self._tcount += 1  # count the subperiod (하위 기간 카운트)
