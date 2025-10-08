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
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader import Order, Position


class FakeCommInfo(object):
    """
    테스트용 가짜 수수료 정보 클래스
    
    실제 거래소 수수료 정보를 시뮬레이션하기 위한 더미 클래스입니다.
    모든 수수료와 비용을 0으로 반환합니다.
    """
    def getvaluesize(self, size, price):
        """포지션 크기와 가격에 따른 가치 크기 반환 (0)"""
        return 0

    def profitandloss(self, size, price, newprice):
        """손익 계산 (0)"""
        return 0

    def getoperationcost(self, size, price):
        """거래 비용 계산 (0.0)"""
        return 0.0

    def getcommission(self, size, price):
        """수수료 계산 (0.0)"""
        return 0.0


class FakeData(object):
    '''
    테스트 중 거래가 데이터에서 정보를 가져오려고 할 때 오류를 방지하기 위한
    최소한의 인터페이스를 제공하는 가짜 데이터 클래스
    '''
    def __len__(self):
        """데이터 길이 반환 (0)"""
        return 0

    @property
    def datetime(self):
        """날짜/시간 데이터 반환 ([0.0])"""
        return [0.0]

    @property
    def close(self):
        """종가 데이터 반환 ([0.0])"""
        return [0.0]


def _execute(position, order, size, price, partial):
    """
    주문을 실행하고 포지션을 업데이트하는 헬퍼 함수
    
    Args:
        position: 업데이트할 포지션 객체
        order: 실행할 주문 객체
        size: 실행할 수량
        price: 실행 가격
        partial: 부분 실행 여부
    """
    # 포지션을 찾아서 실제 업데이트 수행 - 여기서 회계 처리 발생
    pprice_orig = position.price  # 원래 포지션 가격
    psize, pprice, opened, closed = position.update(size, price)

    comminfo = order.comminfo
    
    # 종료된 거래에 대한 비용과 수수료 계산
    closedvalue = comminfo.getoperationcost(closed, pprice_orig)
    closedcomm = comminfo.getcommission(closed, price)

    # 새로 열린 거래에 대한 비용과 수수료 계산
    openedvalue = comminfo.getoperationcost(opened, price)
    openedcomm = comminfo.getcommission(opened, price)

    # 손익과 마진 계산
    pnl = comminfo.profitandloss(-closed, pprice_orig, price)
    margin = comminfo.getvaluesize(size, price)

    # 주문 실행 정보 설정
    order.execute(order.data.datetime[0],
                  size, price,
                  closed, closedvalue, closedcomm,
                  opened, openedvalue, openedcomm,
                  margin, pnl,
                  psize, pprice)  # pnl

    # 부분 실행 또는 완료 상태 설정
    if partial:
        order.partial()  # 부분 실행 상태로 설정
    else:
        order.completed()  # 완료 상태로 설정


def test_run(main=False):
    """
    주문 테스트를 실행하는 메인 함수
    
    이 테스트는 부분적으로 업데이트되는 주문이 올바른 iterpending 시퀀스를
    유지하는지 확인합니다.
    
    Args:
        main: 메인 출력 모드 여부 (사용되지 않음)
    """
    # 테스트용 객체들 생성
    position = Position()
    comminfo = FakeCommInfo()
    order = bt.BuyOrder(data=FakeData(),
                        size=100, price=1.0,
                        exectype=bt.Order.Market,
                        simulated=True)
    order.addcomminfo(comminfo)

    ### 부분적으로 업데이트되는 주문이 올바른 iterpending 시퀀스를 유지하는지 테스트
    ### (주문은 각 알림에 대해 클론됩니다. pending 비트는 이전 알림(클론)과 관련하여
    ###  보고되어야 합니다)

    # 두 개의 비트를 추가하고 두 개의 pending 비트가 있는지 검증
    _execute(position, order, 10, 1.0, True)   # 10개 수량을 1.0 가격으로 부분 실행
    _execute(position, order, 20, 1.1, True)   # 20개 수량을 1.1 가격으로 부분 실행

    clone = order.clone()  # 주문 클론 생성
    pending = clone.executed.getpending()  # pending 비트들 가져오기
    assert len(pending) == 2  # pending 비트가 2개인지 확인
    assert pending[0].size == 10   # 첫 번째 pending 비트의 수량 확인
    assert pending[0].price == 1.0 # 첫 번째 pending 비트의 가격 확인
    assert pending[1].size == 20   # 두 번째 pending 비트의 수량 확인
    assert pending[1].price == 1.1 # 두 번째 pending 비트의 가격 확인

    # 추가로 두 개의 비트를 추가하고 클론 후에도 여전히 두 개의 pending 비트가 있는지 검증
    _execute(position, order, 30, 1.2, True)   # 30개 수량을 1.2 가격으로 부분 실행
    _execute(position, order, 40, 1.3, False)  # 40개 수량을 1.3 가격으로 완료

    clone = order.clone()  # 주문 클론 생성
    pending = clone.executed.getpending()  # pending 비트들 가져오기
    assert len(pending) == 2  # pending 비트가 여전히 2개인지 확인
    assert pending[0].size == 30   # 첫 번째 pending 비트의 수량 확인
    assert pending[0].price == 1.2 # 첫 번째 pending 비트의 가격 확인
    assert pending[1].size == 40   # 두 번째 pending 비트의 수량 확인
    assert pending[1].price == 1.3 # 두 번째 pending 비트의 가격 확인

if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 테스트 실행
    test_run(main=True)
