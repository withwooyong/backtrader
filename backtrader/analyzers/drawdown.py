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
# 낙폭(Drawdown) 분석기 모듈
# =============================================================================
# 이 모듈은 트레이딩 시스템의 낙폭 통계를 계산하고 분석합니다.
# 낙폭은 포트폴리오 가치가 이전 최고점에서 얼마나 하락했는지를 나타내는 지표입니다.
# 
# 주요 분석 항목:
# - 현재 낙폭: 현재 포지션의 낙폭 (백분율 및 금액)
# - 최대 낙폭: 백테스팅 기간 동안의 최대 낙폭
# - 낙폭 기간: 낙폭이 지속된 기간
# - 최대 낙폭 기간: 가장 긴 낙폭 기간
# 
# 낙폭 공식:
# Drawdown = (최고점 - 현재값) / 최고점 × 100%
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader.utils import AutoOrderedDict


__all__ = ['DrawDown', 'TimeDrawDown']


# =============================================================================
# DrawDown 클래스 - 낙폭 분석기
# =============================================================================
# 이 클래스는 트레이딩 시스템의 낙폭 통계를 계산합니다.
# 낙폭은 백분율과 금액으로 표현되며, 최대값과 기간도 함께 추적합니다.
class DrawDown(bt.Analyzer):
    '''This analyzer calculates trading system drawdowns stats such as drawdown
    values in %s and in dollars, max drawdown in %s and in dollars, drawdown
    length and drawdown max length

    Params:

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - ``get_analysis``

        Returns a dictionary (with . notation support and subdctionaries) with
        drawdown stats as values, the following keys/attributes are available:

        - ``drawdown`` - drawdown value in 0.xx %
        - ``moneydown`` - drawdown value in monetary units
        - ``len`` - drawdown length

        - ``max.drawdown`` - max drawdown value in 0.xx %
        - ``max.moneydown`` - max drawdown value in monetary units
        - ``max.len`` - max drawdown length
    '''

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('fund', None),  # 펀드 모드 설정 (None이면 브로커 설정 자동 감지)
    )

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(DrawDown, self).start()
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

    def create_analysis(self):
        # =============================================================================
        # 분석 결과를 저장할 구조 생성
        # =============================================================================
        # AutoOrderedDict는 점(.) 표기법을 지원하는 딕셔너리
        self.rets = AutoOrderedDict()  # dict with . notation

        # =============================================================================
        # 현재 낙폭 통계 초기화
        # =============================================================================
        self.rets.len = 0              # 현재 낙폭 기간
        self.rets.drawdown = 0.0       # 현재 낙폭 (백분율)
        self.rets.moneydown = 0.0      # 현재 낙폭 (금액)

        # =============================================================================
        # 최대 낙폭 통계 초기화
        # =============================================================================
        self.rets.max.len = 0.0        # 최대 낙폭 기간
        self.rets.max.drawdown = 0.0   # 최대 낙폭 (백분율)
        self.rets.max.moneydown = 0.0  # 최대 낙폭 (금액)

        # =============================================================================
        # 내부 변수 초기화
        # =============================================================================
        self._maxvalue = float('-inf')  # any value will outdo it (어떤 값보다도 작은 초기값)

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 정리
        # =============================================================================
        self.rets._close()  # . notation cannot create more keys (점 표기법으로 더 이상 키 생성 불가)

    def notify_fund(self, cash, value, fundvalue, shares):
        # =============================================================================
        # 자금 상태 알림 처리
        # =============================================================================
        # 펀드 모드에 따라 현재 가치와 최대 가치를 업데이트
        if not self._fundmode:
            # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
            self._value = value  # record current value (현재 가치 기록)
            self._maxvalue = max(self._maxvalue, value)  # update peak value (최고점 업데이트)
        else:
            # 펀드 모드인 경우: 펀드 가치 사용
            self._value = fundvalue  # record current value (현재 펀드 가치 기록)
            self._maxvalue = max(self._maxvalue, fundvalue)  # update peak (최고점 업데이트)

    def next(self):
        # =============================================================================
        # 각 거래일마다 낙폭 계산
        # =============================================================================
        r = self.rets

        # calculate current drawdown values
        r.moneydown = moneydown = self._maxvalue - self._value
        r.drawdown = drawdown = 100.0 * moneydown / self._maxvalue

        # maxximum drawdown values
        r.max.moneydown = max(r.max.moneydown, moneydown)
        r.max.drawdown = maxdrawdown = max(r.max.drawdown, drawdown)

        r.len = r.len + 1 if drawdown else 0
        r.max.len = max(r.max.len, r.len)


# =============================================================================
# TimeDrawDown 클래스 - 시간 프레임별 낙폭 분석기
# =============================================================================
# 이 클래스는 선택된 시간 프레임에서 트레이딩 시스템의 낙폭을 계산합니다.
# 기본 데이터와 다른 시간 프레임을 사용할 수 있어 유연한 분석이 가능합니다.
class TimeDrawDown(bt.TimeFrameAnalyzerBase):
    '''This analyzer calculates trading system drawdowns on the chosen
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

    Methods:

      - ``get_analysis``

        Returns a dictionary (with . notation support and subdctionaries) with
        drawdown stats as values, the following keys/attributes are available:

        - ``drawdown`` - drawdown value in 0.xx %
        - ``maxdrawdown`` - drawdown value in monetary units
        - ``maxdrawdownperiod`` - drawdown length

      - Those are available during runs as attributes
        - ``dd``
        - ``maxdd``
        - ``maxddlen``
    '''

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('fund', None),  # 펀드 모드 설정 (None이면 브로커 설정 자동 감지)
    )

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(TimeDrawDown, self).start()
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund
            
        # =============================================================================
        # 낙폭 추적 변수 초기화
        # =============================================================================
        self.dd = 0.0                    # 현재 낙폭 (백분율)
        self.maxdd = 0.0                 # 최대 낙폭 (백분율)
        self.maxddlen = 0                # 최대 낙폭 기간
        self.peak = float('-inf')        # 최고점 가치 (어떤 값보다도 작은 초기값)
        self.ddlen = 0                   # 현재 낙폭 기간

    def on_dt_over(self):
        # =============================================================================
        # 시간 프레임 경계에서 낙폭 계산
        # =============================================================================
        if not self._fundmode:
            # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
            value = self.strategy.broker.getvalue()
        else:
            # 펀드 모드인 경우: 펀드 가치 사용
            value = self.strategy.broker.fundvalue

        # =============================================================================
        # 최고점 업데이트 및 낙폭 기간 초기화
        # =============================================================================
        # update the maximum seen peak
        # 지금까지 본 최고점 업데이트
        if value > self.peak:
            self.peak = value
            self.ddlen = 0  # start of streak (연속 기간 시작)

        # =============================================================================
        # 현재 낙폭 계산
        # =============================================================================
        # calculate the current drawdown
        # 현재 낙폭 계산
        self.dd = dd = 100.0 * (self.peak - value) / self.peak
        self.ddlen += bool(dd)  # if peak == value -> dd = 0 (최고점과 같으면 낙폭 0)

        # =============================================================================
        # 최대 낙폭 및 최대 낙폭 기간 업데이트
        # =============================================================================
        # update the maxdrawdown if needed
        # 필요시 최대 낙폭 업데이트
        self.maxdd = max(self.maxdd, dd)
        self.maxddlen = max(self.maxddlen, self.ddlen)

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 최종 결과 저장
        # =============================================================================
        self.rets['maxdrawdown'] = self.maxdd           # 최대 낙폭 (백분율)
        self.rets['maxdrawdownperiod'] = self.maxddlen  # 최대 낙폭 기간
