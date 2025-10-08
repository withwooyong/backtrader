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
from backtrader import position


def test_run(main=False):
    """
    포지션 테스트를 실행하는 메인 함수
    
    이 테스트는 포지션의 크기와 가격 업데이트 로직을 검증합니다.
    다양한 시나리오(매수, 매도, 포지션 반전)를 테스트합니다.
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 초기 포지션 설정: 10개 수량을 10.0 가격으로
    size = 10
    price = 10.0

    pos = position.Position(size=size, price=price)
    assert pos.size == size      # 포지션 크기 확인
    assert pos.price == price    # 포지션 가격 확인

    # 첫 번째 업데이트: 5개 추가 매수 (12.5 가격)
    upsize = 5
    upprice = 12.5
    nsize, nprice, opened, closed = pos.update(size=upsize, price=upprice)

    if main:
        print('pos.size/price', pos.size, pos.price)
        print('nsize, nprice, opened, closed', nsize, nprice, opened, closed)

    # 업데이트 후 포지션 상태 검증
    assert pos.size == size + upsize  # 총 크기 = 15
    assert pos.size == nsize          # 반환된 크기와 일치
    # 새로운 평균 가격 = (10*10 + 5*12.5) / 15 = 10.83...
    assert pos.price == ((size * price) + (upsize * upprice)) / pos.size
    assert pos.price == nprice        # 반환된 가격과 일치
    assert opened == upsize           # 새로 열린 수량 = 5
    assert not closed                 # 종료된 수량 없음

    # 두 번째 업데이트: 7개 매도 (14.5 가격)
    size = pos.size      # 현재 크기: 15
    price = pos.price    # 현재 가격: 10.83...
    upsize = -7          # 음수 = 매도
    upprice = 14.5

    nsize, nprice, opened, closed = pos.update(size=upsize, price=upprice)

    if main:
        print('pos.size/price', pos.size, pos.price)
        print('nsize, nprice, opened, closed', nsize, nprice, opened, closed)

    # 매도 후 포지션 상태 검증
    assert pos.size == size + upsize  # 총 크기 = 8
    assert pos.size == nsize          # 반환된 크기와 일치
    assert pos.price == price         # 매도 시에는 평균 가격 변경 없음
    assert pos.price == nprice        # 반환된 가격과 일치
    assert not opened                 # 새로 열린 수량 없음
    assert closed == upsize           # 종료된 수량 = -7 (매도)

    # 세 번째 업데이트: 15개 매도로 포지션 반전 (17.5 가격)
    size = pos.size      # 현재 크기: 8
    price = pos.price    # 현재 가격: 10.83...
    upsize = -15         # 음수 = 매도 (기존 포지션보다 큰 수량)
    upprice = 17.5

    nsize, nprice, opened, closed = pos.update(size=upsize, price=upprice)

    if main:
        print('pos.size/price', pos.size, pos.price)
        print('nsize, nprice, opened, closed', nsize, nprice, opened, closed)

    # 포지션 반전 후 상태 검증
    assert pos.size == size + upsize  # 총 크기 = -7 (숏 포지션)
    assert pos.size == nsize          # 반환된 크기와 일치
    assert pos.price == upprice       # 반전 시 새로운 가격으로 설정
    assert pos.price == nprice        # 반환된 가격과 일치
    assert opened == size + upsize    # 새로 열린 수량 = -7 (숏)
    assert closed == -size            # 종료된 수량 = -8 (기존 롱 포지션)


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
