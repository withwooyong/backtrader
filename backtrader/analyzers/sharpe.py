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
# 샤프 비율(Sharpe Ratio) 분석기 모듈
# =============================================================================
# 이 모듈은 투자 전략의 위험 대비 수익률을 측정하는 샤프 비율을 계산합니다.
# 샤프 비율은 초과 수익률을 변동성(표준편차)으로 나눈 값으로, 
# 높을수록 위험 대비 수익률이 좋은 전략을 의미합니다.
# 
# 샤프 비율 공식:
# Sharpe Ratio = (전략 수익률 - 무위험 수익률) / 전략 수익률의 표준편차
# 
# 주요 특징:
# - 다양한 시간 프레임 지원 (연간, 월간, 주간, 일간)
# - 무위험 수익률 자동 변환
# - 연간화 옵션 제공
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

from backtrader.utils.py3 import itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import average, standarddev
from backtrader.analyzers import TimeReturn, AnnualReturn


# =============================================================================
# SharpeRatio 클래스 - 샤프 비율 분석기
# =============================================================================
# 이 클래스는 전략의 샤프 비율을 계산합니다.
# 무위험 자산은 단순히 이자율로 표현되며, 다양한 시간 프레임에서 계산 가능합니다.
class SharpeRatio(Analyzer):
    '''This analyzer calculates the SharpeRatio of a strategy using a risk free
    asset which is simply an interest rate

    See also:

      - https://en.wikipedia.org/wiki/Sharpe_ratio

    Params:

      - ``timeframe``: (default: ``TimeFrame.Years``)

      - ``compression`` (default: ``1``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

      - ``riskfreerate`` (default: 0.01 -> 1%)

        Expressed in annual terms (see ``convertrate`` below)

      - ``convertrate`` (default: ``True``)

        Convert the ``riskfreerate`` from annual to monthly, weekly or daily
        rate. Sub-day conversions are not supported

      - ``factor`` (default: ``None``)

        If ``None``, the conversion factor for the riskfree rate from *annual*
        to the chosen timeframe will be chosen from a predefined table

          Days: 252, Weeks: 52, Months: 12, Years: 1

        Else the specified value will be used

      - ``annualize`` (default: ``False``)

        If ``convertrate`` is ``True``, the *SharpeRatio* will be delivered in
        the ``timeframe`` of choice.

        In most occasions the SharpeRatio is delivered in annualized form.
        Convert the ``riskfreerate`` from annual to monthly, weekly or daily
        rate. Sub-day conversions are not supported

      - ``stddev_sample`` (default: ``False``)

        If this is set to ``True`` the *standard deviation* will be calculated
        decreasing the denominator in the mean by ``1``. This is used when
        calculating the *standard deviation* if it's considered that not all
        samples are used for the calculation. This is known as the *Bessels'
        correction*

      - ``daysfactor`` (default: ``None``)

        Old naming for ``factor``. If set to anything else than ``None`` and
        the ``timeframe`` is ``TimeFrame.Days`` it will be assumed this is old
        code and the value will be used

      - ``legacyannual`` (default: ``False``)

        Use the ``AnnualReturn`` return analyzer, which as the name implies
        only works on years

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - get_analysis

        Returns a dictionary with key "sharperatio" holding the ratio

    '''
    params = (
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
        ('riskfreerate', 0.01),
        ('factor', None),
        ('convertrate', True),
        ('annualize', False),
        ('stddev_sample', False),

        # old behavior
        ('daysfactor', None),
        ('legacyannual', False),
        ('fund', None),
    )

    RATEFACTORS = {
        TimeFrame.Days: 252,
        TimeFrame.Weeks: 52,
        TimeFrame.Months: 12,
        TimeFrame.Years: 1,
    }

    def __init__(self):
        # =============================================================================
        # 분석기 초기화 - 하위 분석기 선택
        # =============================================================================
        if self.p.legacyannual:
            # 레거시 연간 수익률 분석기 사용
            self.anret = AnnualReturn()
        else:
            # 새로운 시간 프레임별 수익률 분석기 사용
            self.timereturn = TimeReturn(
                timeframe=self.p.timeframe,
                compression=self.p.compression,
                fund=self.p.fund)

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 샤프 비율 계산
        # =============================================================================
        super(SharpeRatio, self).stop()
        if self.p.legacyannual:
            # =============================================================================
            # 레거시 연간 수익률 방식으로 샤프 비율 계산
            # =============================================================================
            rate = self.p.riskfreerate
            retavg = average([r - rate for r in self.anret.rets])
            retdev = standarddev(self.anret.rets)

            self.ratio = retavg / retdev
        else:
            # =============================================================================
            # 새로운 시간 프레임별 방식으로 샤프 비율 계산
            # =============================================================================
            # Get the returns from the subanalyzer
            # 하위 분석기에서 수익률 가져오기
            returns = list(itervalues(self.timereturn.get_analysis()))

            rate = self.p.riskfreerate  # 무위험 수익률

            factor = None

            # =============================================================================
            # 변환 계수 결정
            # =============================================================================
            # Hack to identify old code
            # 구 코드 식별을 위한 해킹
            if self.p.timeframe == TimeFrame.Days and \
               self.p.daysfactor is not None:

                factor = self.p.daysfactor

            else:
                if self.p.factor is not None:
                    factor = self.p.factor  # user specified factor (사용자 지정 계수)
                elif self.p.timeframe in self.RATEFACTORS:
                    # Get the conversion factor from the default table
                    # 기본 테이블에서 변환 계수 가져오기
                    factor = self.RATEFACTORS[self.p.timeframe]

            if factor is not None:
                # =============================================================================
                # 변환 계수가 발견됨
                # =============================================================================
                # A factor was found
                # 변환 계수가 발견됨

                if self.p.convertrate:
                    # =============================================================================
                    # 표준: 연간 수익률을 시간 프레임 계수로 다운그레이드
                    # =============================================================================
                    # Standard: downgrade annual returns to timeframe factor
                    # 표준: 연간 수익률을 시간 프레임 계수로 다운그레이드
                    rate = pow(1.0 + rate, 1.0 / factor) - 1.0
                else:
                    # =============================================================================
                    # 그렇지 않으면 수익률을 연간 수익률로 업그레이드
                    # =============================================================================
                    # Else upgrade returns to yearly returns
                    # 그렇지 않으면 수익률을 연간 수익률로 업그레이드
                    returns = [pow(1.0 + x, factor) - 1.0 for x in returns]

            # =============================================================================
            # 샤프 비율 계산 가능 여부 확인
            # =============================================================================
            lrets = len(returns) - self.p.stddev_sample
            # Check if the ratio can be calculated
            # 비율 계산 가능 여부 확인
            if lrets:
                # =============================================================================
                # 초과 수익률 계산 - 산술 평균 - 원본 샤프
                # =============================================================================
                # Get the excess returns - arithmetic mean - original sharpe
                # 초과 수익률 가져오기 - 산술 평균 - 원본 샤프
                ret_free = [r - rate for r in returns]
                ret_free_avg = average(ret_free)
                retdev = standarddev(ret_free, avgx=ret_free_avg,
                                     bessel=self.p.stddev_sample)

                try:
                    ratio = ret_free_avg / retdev

                    if factor is not None and \
                       self.p.convertrate and self.p.annualize:

                        ratio = math.sqrt(factor) * ratio
                except (ValueError, TypeError, ZeroDivisionError):
                    ratio = None
            else:
                # =============================================================================
                # 수익률이 없거나 stddev_sample이 활성화되어 1개 수익률만 있음
                # =============================================================================
                # no returns or stddev_sample was active and 1 return
                # 수익률이 없거나 stddev_sample이 활성화되어 1개 수익률만 있음
                ratio = None

            self.ratio = ratio

        self.rets['sharperatio'] = self.ratio


class SharpeRatio_A(SharpeRatio):
    '''Extension of the SharpeRatio which returns the Sharpe Ratio directly in
    annualized form

    The following param has been changed from ``SharpeRatio``

      - ``annualize`` (default: ``True``)

    '''

    params = (
        ('annualize', True),
    )
