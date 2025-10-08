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

import testcommon

import backtrader as bt
from backtrader import trade


class FakeCommInfo(object):
    """
    테스트용 가짜 수수료 정보 클래스
    
    실제 거래소 수수료 정보를 시뮬레이션하기 위한 더미 클래스입니다.
    """
    def getvaluesize(self, size, price):
        """포지션 크기와 가격에 따른 가치 크기 반환 (0)"""
        return 0

    def profitandloss(self, size, price, newprice):
        """손익 계산 (0)"""
        return 0


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


def test_run(main=False):
    """
    거래(Trade) 테스트를 실행하는 메인 함수
    
    이 테스트는 거래 객체의 업데이트 로직을 검증합니다.
    다양한 시나리오(매수, 매도, 거래 종료)를 테스트합니다.
    
    Args:
        main: 메인 출력 모드 여부 (사용되지 않음)
    """
    # 테스트용 거래 객체 생성
    tr = trade.Trade(data=FakeData())

    # 테스트용 매수 주문 생성
    order = bt.BuyOrder(data=FakeData(),
                        size=0, price=1.0,
                        exectype=bt.Order.Market,
                        simulated=True)

    # 수수료 설정 및 초기 거래 정보
    commrate = 0.025  # 2.5% 수수료율
    size = 10         # 거래 수량
    price = 10.0      # 거래 가격
    value = size * price  # 거래 가치
    commission = value * commrate  # 수수료

    # 첫 번째 거래 업데이트: 10개 매수 (10.0 가격)
    tr.update(order=order, size=size, price=price, value=value,
              commission=commission, pnl=0.0, comminfo=FakeCommInfo())

    # 거래 상태 검증
    assert not tr.isclosed      # 거래가 아직 열려있음
    assert tr.size == size      # 거래 수량 확인
    assert tr.price == price    # 거래 가격 확인
    # assert tr.value == value  # 가치 확인 (주석 처리됨)
    assert tr.commission == commission  # 수수료 확인
    assert not tr.pnl           # 손익 없음
    assert tr.pnlcomm == tr.pnl - tr.commission  # 수수료 차감 후 손익

    # 두 번째 업데이트: 5개 매도 (12.5 가격)
    upsize = -5        # 음수 = 매도
    upprice = 12.5     # 매도 가격
    upvalue = upsize * upprice  # 매도 가치
    upcomm = abs(value) * commrate  # 매도 수수료

    tr.update(order=order, size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0, comminfo=FakeCommInfo())

    # 매도 후 거래 상태 검증
    assert not tr.isclosed      # 거래가 아직 열려있음
    assert tr.size == size + upsize  # 총 수량 = 5
    assert tr.price == price    # 매도 시에는 평균 가격 변경 없음
    # assert tr.value == upvalue  # 가치 확인 (주석 처리됨)
    assert tr.commission == commission + upcomm  # 누적 수수료

    # 세 번째 업데이트: 7개 추가 매수 (14.5 가격)
    size = tr.size      # 현재 수량: 5
    price = tr.price    # 현재 가격: 10.0
    commission = tr.commission  # 현재 수수료

    upsize = 7          # 양수 = 매수
    upprice = 14.5      # 매수 가격
    upvalue = upsize * upprice  # 매수 가치
    upcomm = abs(value) * commrate  # 매수 수수료

    tr.update(order=order, size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0, comminfo=FakeCommInfo())

    # 추가 매수 후 거래 상태 검증
    assert not tr.isclosed      # 거래가 아직 열려있음
    assert tr.size == size + upsize  # 총 수량 = 12
    # 새로운 평균 가격 = (5*10 + 7*14.5) / 12 = 12.625
    assert tr.price == ((size * price) + (upsize * upprice)) / (size + upsize)
    # assert tr.value == upvalue  # 가치 확인 (주석 처리됨)
    assert tr.commission == commission + upcomm  # 누적 수수료

    # 네 번째 업데이트: 모든 포지션 매도로 거래 종료 (12.5 가격)
    size = tr.size      # 현재 수량: 12
    price = tr.price    # 현재 가격: 12.625
    commission = tr.commission  # 현재 수수료

    upsize = -size      # 모든 수량 매도
    upprice = 12.5      # 매도 가격
    upvalue = upsize * upprice  # 매도 가치
    upcomm = abs(value) * commrate  # 매도 수수료

    tr.update(order=order, size=upsize, price=upprice, value=upvalue,
              commission=upcomm, pnl=0.0, comminfo=FakeCommInfo())

    # 거래 종료 후 상태 검증
    assert tr.isclosed      # 거래가 종료됨
    assert tr.size == size + upsize  # 총 수량 = 0
    assert tr.price == price  # 가격 변경 없음 (단순히 거래를 종료했기 때문)
    # assert tr.value == upvalue  # 가치 확인 (주석 처리됨)
    assert tr.commission == commission + upcomm  # 누적 수수료


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 테스트 실행
    test_run(main=True)
