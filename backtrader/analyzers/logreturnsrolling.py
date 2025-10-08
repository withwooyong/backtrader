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
# 롤링 로그 수익률(Log Returns Rolling) 분석기 모듈
# =============================================================================
# 이 모듈은 지정된 시간 프레임과 압축 비율에 대한 롤링 로그 수익률을 계산합니다.
# 롤링 수익률은 연속된 기간들에 대해 수익률을 계산하여
# 전략의 성과 변화 패턴을 동적으로 분석할 수 있습니다.
# 
# 주요 특징:
# - 다양한 시간 프레임 지원 (연간, 월간, 주간, 일간, 시간 등)
# - 포트폴리오 가치 또는 특정 자산 기준 수익률 계산
# - 로그 수익률 사용으로 정확한 복합 수익률 계산
# - 시간 프레임 경계에서의 수익률 계산 방식 설정
# 
# 롤링 수익률의 장점:
# - 전략 성과의 시간적 변화 추적
# - 성과 안정성과 일관성 평가
# - 시장 상황별 전략 대응력 분석
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import math

import backtrader as bt


__all__ = ['LogReturnsRolling']


# =============================================================================
# LogReturnsRolling 클래스 - 롤링 로그 수익률 분석기
# =============================================================================
# 이 클래스는 지정된 시간 프레임과 압축 비율에 대한 롤링 로그 수익률을 계산합니다.
# 포트폴리오 가치 또는 특정 자산의 가격 변화를 기준으로
# 연속된 기간들에 대해 수익률을 계산합니다.
class LogReturnsRolling(bt.TimeFrameAnalyzerBase):
    '''This analyzer calculates rolling returns for a given timeframe and
    compression

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
        super(LogReturnsRolling, self).start()
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

        # =============================================================================
        # 값 저장을 위한 덱 초기화
        # =============================================================================
        # 압축 비율만큼 NaN 값으로 초기화된 덱 생성
        # maxlen으로 최대 크기 제한하여 메모리 효율성 확보
        self._values = collections.deque([float('Nan')] * self.compression,
                                         maxlen=self.compression)

        if self.p.data is None:
            # =============================================================================
            # 데이터 추적이 아닌 경우 포트폴리오 초기 가치 설정
            # =============================================================================
            if not self._fundmode:
                # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
                self._lastvalue = self.strategy.broker.getvalue()
            else:
                # 펀드 모드인 경우: 펀드 가치 사용
                self._lastvalue = self.strategy.broker.fundvalue

    def notify_fund(self, cash, value, fundvalue, shares):
        # =============================================================================
        # 자금 상태 알림 처리
        # =============================================================================
        if not self._fundmode:
            # 펀드 모드가 아닌 경우
            self._value = value if self.p.data is None else self.p.data[0]
        else:
            # 펀드 모드인 경우
            self._value = fundvalue if self.p.data is None else self.p.data[0]

    def _on_dt_over(self):
        # =============================================================================
        # 시간 프레임 경계가 넘어갈 때 호출
        # =============================================================================
        # next is called in a new timeframe period
        # 새로운 시간 프레임 기간에서 next가 호출됨
        
        if self.p.data is None or len(self.p.data) > 1:
            # =============================================================================
            # 데이터 피드 추적이 아니거나 이미 데이터가 있는 경우
            # =============================================================================
            # Not tracking a data feed or data feed has data already
            vst = self._lastvalue  # update value_start to last (시작값을 마지막 값으로 업데이트)
        else:
            # =============================================================================
            # 첫 번째 틱은 이전 참조가 없으므로 시가 또는 종가 사용
            # =============================================================================
            # The 1st tick has no previous reference, use the opening price
            # 첫 번째 틱은 이전 참조가 없으므로 시가 또는 종가 사용
            vst = self.p.data.open[0] if self.p.firstopen else self.p.data[0]

        # =============================================================================
        # 값 저장 및 업데이트
        # =============================================================================
        self._values.append(vst)  # push values backwards (and out) (값을 뒤로 밀어넣고 오래된 값 제거)

    def next(self):
        # =============================================================================
        # 각 거래일마다 로그 수익률 계산
        # =============================================================================
        # Calculate the return
        # 수익률 계산
        
        super(LogReturnsRolling, self).next()
        
        # =============================================================================
        # 로그 수익률 공식: log(현재가치 / 시작가치)
        # =============================================================================
        # 로그 수익률은 복합 수익률 계산에 더 정확하며,
        # 연속된 수익률의 합이 전체 기간 수익률과 일치합니다.
        self.rets[self.dtkey] = math.log(self._value / self._values[0])
        
        # =============================================================================
        # 마지막 값 업데이트
        # =============================================================================
        self._lastvalue = self._value  # keep last value (마지막 값 유지)
