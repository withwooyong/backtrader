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
# VWR(Variability-Weighted Return) 분석기 모듈
# =============================================================================
# 이 모듈은 VWR(변동성 가중 수익률)을 계산합니다.
# VWR은 로그 수익률을 사용하는 개선된 샤프 비율로,
# 전통적인 샤프 비율보다 더 정확한 위험 대비 수익률 측정을 제공합니다.
# 
# 주요 특징:
# - 로그 수익률 기반 계산으로 정확성 향상
# - 변동성을 가중치로 사용한 수익률 조정
# - 다양한 시간 프레임 지원
# - 연간화 옵션 제공
# 
# VWR의 장점:
# - 샤프 비율보다 더 안정적인 결과
# - 극단적인 수익률에 덜 민감
# - 장기 투자 성과 평가에 유리
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

import backtrader as bt
from backtrader import TimeFrameAnalyzerBase
from . import Returns
from ..mathsupport import standarddev


# =============================================================================
# VWR 클래스 - 변동성 가중 수익률 분석기
# =============================================================================
# 이 클래스는 VWR(Variability-Weighted Return)을 계산합니다.
# VWR은 로그 수익률을 사용하여 변동성을 가중치로 적용한 개선된 성과 지표입니다.
class VWR(TimeFrameAnalyzerBase):
    '''Variability-Weighted Return: Better SharpeRatio with Log Returns

    Alias:

      - VariabilityWeightedReturn

    See:

      - https://www.crystalbull.com/sharpe-ratio-better-with-log-returns/

    Params:

      - ``timeframe`` (default: ``None``)
        If ``None`` then the complete return over the entire backtested period
        will be reported

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - ``tann`` (default: ``None``)

        Number of periods to use for the annualization (normalization) of the
        average returns. If ``None``, then standard ``t`` values will be used,
        namely:

          - ``days: 252``
          - ``weeks: 52``
          - ``months: 12``
          - ``years: 1``

      - ``tau`` (default: ``2.0``)

        factor for the calculation (see the literature)

      - ``sdev_max`` (default: ``0.20``)

        max standard deviation (see the literature)

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

        The returned dict contains the following keys:

          - ``vwr``: Variability-Weighted Return
    '''

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('tann', None),
        ('tau', 0.20),
        ('sdev_max', 2.0),
        ('fund', None),
    )

    _TANN = {
        bt.TimeFrame.Days: 252.0,
        bt.TimeFrame.Weeks: 52.0,
        bt.TimeFrame.Months: 12.0,
        bt.TimeFrame.Years: 1.0,
    }

    def __init__(self):
        # =============================================================================
        # 분석기 초기화 - 하위 로그 수익률 분석기 생성
        # =============================================================================
        # Children log return analyzer
        # 하위 로그 수익률 분석기
        self._returns = Returns(timeframe=self.p.timeframe,
                                compression=self.p.compression,
                                tann=self.p.tann)

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(VWR, self).start()
        # Add an initial placeholder for [-1] operation
        # [-1] 연산을 위한 초기 플레이스홀더 추가
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

        # =============================================================================
        # 가치 추적 리스트 초기화
        # =============================================================================
        if not self._fundmode:
            self._pis = [self.strategy.broker.getvalue()]  # keep initial value (초기 가치 유지)
        else:
            self._pis = [self.strategy.broker.fundvalue]  # keep initial value (초기 가치 유지)

        self._pns = [None]  # keep final prices (value) (최종 가격(가치) 유지)

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 VWR 계산
        # =============================================================================
        super(VWR, self).stop()
        # =============================================================================
        # 마지막 'dt_over' 이후 값이 보이지 않는지 확인
        # 그렇다면 'pi'가 잘못된 위치에 있고 'pn'이 None입니다. 제거
        # =============================================================================
        # Check if no value has been seen after the last 'dt_over'
        # If so, there is one 'pi' out of place and a None 'pn'. Purge
        # 마지막 'dt_over' 이후 값이 보이지 않는지 확인
        # 그렇다면 'pi'가 잘못된 위치에 있고 'pn'이 None입니다. 제거
        if self._pns[-1] is None:
            self._pis.pop()
            self._pns.pop()

        # =============================================================================
        # 하위 분석기에서 결과 가져오기
        # =============================================================================
        # Get results from children
        # 하위 분석기에서 결과 가져오기
        rs = self._returns.get_analysis()
        ravg = rs['ravg']
        rnorm100 = rs['rnorm100']

        # =============================================================================
        # VWR 계산을 위한 편차 계산
        # =============================================================================
        # make n 1 based in enumerate (number of periods and not index)
        # enumerate에서 n을 1 기반으로 만듦 (인덱스가 아닌 기간 수)
        # skip initial placeholders for synchronization
        # 동기화를 위해 초기 플레이스홀더 건너뛰기
        dts = []
        for n, pipn in enumerate(zip(self._pis, self._pns), 1):
            pi, pn = pipn

            dt = pn / (pi * math.exp(ravg * n)) - 1.0
            dts.append(dt)

        sdev_p = standarddev(dts, bessel=True)

        # =============================================================================
        # VWR 최종 계산
        # =============================================================================
        vwr = rnorm100 * (1.0 - pow(sdev_p / self.p.sdev_max, self.p.tau))
        self.rets['vwr'] = vwr

    def notify_fund(self, cash, value, fundvalue, shares):
        # =============================================================================
        # 자금 상태 알림 처리
        # =============================================================================
        if not self._fundmode:
            self._pns[-1] = value  # annotate last seen pn for current period (현재 기간의 마지막으로 본 pn 주석)
        else:
            self._pns[-1] = fundvalue  # annotate last pn for current period (현재 기간의 마지막 pn 주석)

    def _on_dt_over(self):
        # =============================================================================
        # 시간 프레임 경계에서 가치 리스트 업데이트
        # =============================================================================
        self._pis.append(self._pns[-1])  # last pn is pi in next period (마지막 pn이 다음 기간의 pi)
        self._pns.append(None)  # placeholder for [-1] operation ([-1] 연산을 위한 플레이스홀더)


VariabilityWeightedReturn = VWR
