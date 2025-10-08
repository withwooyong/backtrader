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
# 포지션 가치(Positions Value) 분석기 모듈
# =============================================================================
# 이 모듈은 현재 데이터 세트의 각 자산에 대한 포지션 가치를 추적하고 보고합니다.
# 포트폴리오의 각 자산별 포지션 가치 변화를 시간별로 기록하여
# 자산 배분과 포지션 관리 성과를 분석할 수 있습니다.
# 
# 주요 특징:
# - 각 데이터 피드별 포지션 가치 추적
# - 현금 포함 여부 선택 가능
# - 헤더 정보 추가 옵션
# - 시간 프레임별 데이터 수집
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import backtrader as bt


# =============================================================================
# PositionsValue 클래스 - 포지션 가치 분석기
# =============================================================================
# 이 클래스는 현재 데이터 세트의 각 자산에 대한 포지션 가치를 추적합니다.
# 각 거래일마다 포지션 가치를 기록하여 자산별 성과 변화를 분석할 수 있습니다.
class PositionsValue(bt.Analyzer):
    '''This analyzer reports the value of the positions of the current set of
    datas

    Params:

      - timeframe (default: ``None``)
        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: ``None``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - headers (default: ``False``)

        Add an initial key to the dictionary holding the results with the names
        of the datas ('Datetime' as key

      - cash (default: ``False``)

        Include the actual cash as an extra position (for the header 'cash'
        will be used as name)

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    
    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('headers',  False),  # 결과에 헤더 정보 추가 여부
        ('cash', False),      # 현금을 추가 포지션으로 포함 여부
    )

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        if self.p.headers:
            # 헤더가 활성화된 경우 데이터 이름들을 헤더로 설정
            headers = [d._name or 'Data%d' % i
                       for i, d in enumerate(self.datas)]
            # 현금 포함 옵션이 활성화된 경우 'cash' 헤더 추가
            self.rets['Datetime'] = headers + ['cash'] * self.p.cash

        # =============================================================================
        # 시간 프레임 설정
        # =============================================================================
        # 모든 데이터 중 가장 작은 시간 프레임을 사용
        tf = min(d._timeframe for d in self.datas)
        # 일별 이상의 시간 프레임인 경우 날짜 사용, 그렇지 않으면 시간 사용
        self._usedate = tf >= bt.TimeFrame.Days

    def next(self):
        # =============================================================================
        # 각 거래일마다 포지션 가치 수집
        # =============================================================================
        # 각 데이터 피드의 포지션 가치를 브로커에서 가져오기
        pvals = [self.strategy.broker.get_value([d]) for d in self.datas]
        
        if self.p.cash:
            # 현금 포함 옵션이 활성화된 경우 현금 가치 추가
            pvals.append(self.strategy.broker.get_cash())

        # =============================================================================
        # 결과 저장
        # =============================================================================
        if self._usedate:
            # 일별 이상의 시간 프레임: 날짜를 키로 사용
            self.rets[self.strategy.datetime.date()] = pvals
        else:
            # 시간 단위의 시간 프레임: 날짜와 시간을 키로 사용
            self.rets[self.strategy.datetime.datetime()] = pvals
