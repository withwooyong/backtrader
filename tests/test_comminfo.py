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
from backtrader import CommissionInfo, Position


def check_stocks():
    """
    주식 거래에 대한 수수료 정보 테스트
    
    주식 거래의 수수료 계산, 거래 비용, 포지션 가치, 손익 계산 등을 검증합니다.
    """
    commission = 0.5  # 0.5% 수수료율
    comm = bt.CommissionInfo(commission=commission)

    # 테스트용 거래 정보
    price = 10.0      # 주식 가격
    cash = 10000.0    # 현금 잔고
    size = 100.0      # 거래 수량

    # 거래 비용 계산 및 검증
    opcost = comm.getoperationcost(size=size, price=price)
    assert opcost == size * price  # 거래 비용 = 수량 × 가격

    # 포지션 가치 계산 및 검증
    pos = Position(size=size, price=price)
    value = comm.getvalue(pos, price)
    assert value == size * price  # 포지션 가치 = 수량 × 가격

    # 수수료 계산 및 검증
    commcost = comm.getcommission(size, price)
    assert commcost == size * price * commission  # 수수료 = 수량 × 가격 × 수수료율

    # 손익 계산 및 검증
    newprice = 5.0  # 새로운 가격
    pnl = comm.profitandloss(pos.size, pos.price, newprice)
    assert pnl == pos.size * (newprice - price)  # 손익 = 수량 × (새가격 - 원가격)

    # 현금 조정 확인 (주식 거래에서는 현금 조정 없음)
    ca = comm.cashadjust(size, price, newprice)
    assert not ca


def check_futures():
    """
    선물 거래에 대한 수수료 정보 테스트
    
    선물 거래의 수수료 계산, 마진, 승수, 손익 계산 등을 검증합니다.
    """
    commission = 0.5  # 0.5% 수수료율
    margin = 10.0     # 마진 요구사항
    mult = 10.0       # 승수 (계약 크기)
    comm = bt.CommissionInfo(commission=commission, mult=mult, margin=margin)

    # 테스트용 거래 정보
    price = 10.0      # 선물 가격
    cash = 10000.0    # 현금 잔고
    size = 100.0      # 거래 수량

    # 거래 비용 계산 및 검증 (선물은 마진 기반)
    opcost = comm.getoperationcost(size=size, price=price)
    assert opcost == size * margin  # 거래 비용 = 수량 × 마진

    # 포지션 가치 계산 및 검증 (선물은 마진 기반)
    pos = Position(size=size, price=price)
    value = comm.getvalue(pos, price)
    assert value == size * margin  # 포지션 가치 = 수량 × 마진

    # 수수료 계산 및 검증
    commcost = comm.getcommission(size, price)
    assert commcost == size * commission  # 수수료 = 수량 × 수수료율

    # 손익 계산 및 검증 (선물은 승수 적용)
    newprice = 5.0  # 새로운 가격
    pnl = comm.profitandloss(pos.size, pos.price, newprice)
    assert pnl == pos.size * (newprice - price) * mult  # 손익 = 수량 × (새가격 - 원가격) × 승수

    # 현금 조정 확인 (선물 거래에서는 손익에 따른 현금 조정)
    ca = comm.cashadjust(size, price, newprice)
    assert ca == size * (newprice - price) * mult  # 현금 조정 = 손익


def test_run(main=False):
    """
    수수료 정보 테스트를 실행하는 메인 함수
    
    주식과 선물 거래에 대한 수수료 계산 로직을 모두 테스트합니다.
    
    Args:
        main: 메인 출력 모드 여부 (사용되지 않음)
    """
    check_stocks()   # 주식 거래 테스트
    check_futures()  # 선물 거래 테스트


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 테스트 실행
    test_run(main=True)
