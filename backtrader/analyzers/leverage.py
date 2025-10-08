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
# 레버리지(Leverage) 분석기 모듈
# =============================================================================
# 이 모듈은 전략의 총 레버리지(Gross Leverage)를 계산합니다.
# 레버리지는 포트폴리오가 얼마나 투자되어 있는지를 나타내는 지표로,
# 현금 대비 투자된 자산의 비율을 측정합니다.
# 
# 주요 특징:
# - 시간 프레임별 레버리지 계산
# - 펀드 모드 지원 (총 순자산 또는 펀드 가치 기준)
# - 현금과 투자 자산의 비율 추적
# - 레버리지 변화 패턴 분석
# 
# 레버리지 해석:
# - 0.0: 100% 현금 보유 (투자 없음)
# - 1.0: 완전 투자 (숏 포지션 없음)
# - 1.0 초과: 레버리지 사용 (차입 투자)
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt


# =============================================================================
# GrossLeverage 클래스 - 총 레버리지 분석기
# =============================================================================
# 이 클래스는 현재 전략의 총 레버리지를 시간 프레임별로 계산합니다.
# 레버리지는 포트폴리오의 투자 집중도를 측정하는 중요한 지표입니다.
class GrossLeverage(bt.Analyzer):
    '''This analyzer calculates the Gross Leverage of the current strategy
    on a timeframe basis

    Params:

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
        ('fund', None),  # 펀드 모드 설정 (None이면 브로커 설정 자동 감지)
    )

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        if self.p.fund is None:
            # 펀드 모드가 설정되지 않았으면 브로커의 설정을 자동 감지
            self._fundmode = self.strategy.broker.fundmode
        else:
            # 사용자가 명시적으로 설정한 펀드 모드 사용
            self._fundmode = self.p.fund

    def notify_fund(self, cash, value, fundvalue, shares):
        # =============================================================================
        # 자금 상태 알림 처리
        # =============================================================================
        self._cash = cash  # 현금 보유량 저장
        
        if not self._fundmode:
            # 펀드 모드가 아닌 경우: 총 순자산 가치 사용
            self._value = value
        else:
            # 펀드 모드인 경우: 펀드 가치 사용
            self._value = fundvalue

    def next(self):
        # =============================================================================
        # 각 거래일마다 레버리지 계산
        # =============================================================================
        # Updates the leverage for "dtkey" (see base class) for each cycle
        # 0.0 if 100% in cash, 1.0 if no short selling and fully invested
        # 각 사이클마다 "dtkey"에 대한 레버리지 업데이트
        # 0.0: 100% 현금 보유, 1.0: 숏 포지션 없이 완전 투자
        
        # =============================================================================
        # 레버리지 공식: (총 가치 - 현금) / 총 가치
        # =============================================================================
        lev = (self._value - self._cash) / self._value
        
        # 현재 날짜/시간을 키로 하여 레버리지 값 저장
        self.rets[self.data0.datetime.datetime()] = lev
