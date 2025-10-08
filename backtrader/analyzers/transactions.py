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
# 거래 내역(Transactions) 분석기 모듈
# =============================================================================
# 이 모듈은 백테스팅 시스템의 모든 데이터에 대해 발생한 거래 내역을 추적하고 보고합니다.
# 주문 실행 비트를 분석하여 각 데이터의 포지션 변화를 추적하고,
# 거래가 발생할 때마다 상세한 정보를 기록합니다.
# 
# 주요 특징:
# - 모든 데이터 피드의 거래 내역 추적
# - 주문 실행 시점의 포지션 변화 기록
# - PyFolio 통합을 위한 표준 형식 지원
# - 거래별 수량, 가격, 심볼, 가치 정보 제공
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import collections

import backtrader as bt
from backtrader import Order, Position


# =============================================================================
# Transactions 클래스 - 거래 내역 분석기
# =============================================================================
# 이 클래스는 시스템의 모든 데이터에 대해 발생한 거래 내역을 추적합니다.
# 주문 실행 비트를 분석하여 각 next() 사이클에서 포지션 변화를 계산하고,
# 거래가 발생할 때마다 상세한 정보를 기록합니다.
class Transactions(bt.Analyzer):
    '''This analyzer reports the transactions occurred with each an every data in
    the system

    It looks at the order execution bits to create a ``Position`` starting from
    0 during each ``next`` cycle.

    The result is used during next to record the transactions

    Params:

      - headers (default: ``True``)

        Add an initial key to the dictionary holding the results with the names
        of the datas

        This analyzer was modeled to facilitate the integration with
        ``pyfolio`` and the header names are taken from the samples used for
        it::

          'date', 'amount', 'price', 'sid', 'symbol', 'value'

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    
    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('headers', False),  # 결과 딕셔너리에 헤더 추가 여부
        ('_pfheaders', ('date', 'amount', 'price', 'sid', 'symbol', 'value')),  # PyFolio 헤더 형식
    )

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(Transactions, self).start()
        if self.p.headers:
            # 헤더가 활성화된 경우 PyFolio 형식의 헤더 추가
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]

        # =============================================================================
        # 내부 변수 초기화
        # =============================================================================
        self._positions = collections.defaultdict(Position)  # 데이터별 포지션 추적
        self._idnames = list(enumerate(self.strategy.getdatanames()))  # 데이터 이름과 인덱스 매핑

    def notify_order(self, order):
        # =============================================================================
        # 주문 상태 알림 처리
        # =============================================================================
        # An order could have several partial executions per cycle (unlikely
        # but possible) and therefore: collect each new execution notification
        # and let the work for next
        # 주문은 각 사이클에서 여러 번의 부분 실행을 가질 수 있으므로,
        # 각 실행 알림을 수집하고 next()에서 처리하도록 함

        # We use a fresh Position object for each round to get summary of what
        # the execution bits have done in that round
        # 각 라운드에서 새로운 Position 객체를 사용하여 해당 라운드의 실행 비트 요약을 얻음
        
        if order.status not in [Order.Partial, Order.Completed]:
            return  # It's not an execution (실행이 아닌 경우 종료)

        # =============================================================================
        # 주문 실행 처리
        # =============================================================================
        pos = self._positions[order.data._name]  # 해당 데이터의 포지션 가져오기
        for exbit in order.executed.iterpending():
            if exbit is None:
                break  # end of pending reached (대기 중인 실행 비트 끝에 도달)

            # 실행 비트의 수량과 가격으로 포지션 업데이트
            pos.update(exbit.size, exbit.price)

    def next(self):
        # =============================================================================
        # 각 거래일마다 거래 내역 기록
        # =============================================================================
        # super(Transactions, self).next()  # let dtkey update
        entries = []
        for i, dname in self._idnames:
            pos = self._positions.get(dname, None)
            if pos is not None:
                size, price = pos.size, pos.price
                if size:
                    # 포지션이 있는 경우 거래 내역에 추가
                    # [수량, 가격, 데이터 인덱스, 데이터 이름, 가치(수량 × 가격)]
                    entries.append([size, price, i, dname, -size * price])

        if entries:
            self.rets[self.strategy.datetime.datetime()] = entries

        self._positions.clear()
