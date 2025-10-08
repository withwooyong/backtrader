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
import backtrader.indicators as btind

# 테스트할 데이터 개수
chkdatas = 1

# ZLEMA 지표의 예상 값들 (30일 Zero Lag Exponential Moving Average)
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# ZLEMA는 Zero Lag Exponential Moving Average의 약자로, 일반 EMA의 지연 문제를 해결한 지표입니다
# 가격 데이터를 미리 처리하여 지연을 최소화하고, 더 빠른 신호를 제공합니다
# 일반 EMA보다 반응이 빠르고 정확한 진입/청산 시점을 제공합니다
chkvals = [
    ['4125.487746', '3778.694000', '3620.284712']
]

# 지표의 최소 기간 (ZLEMA의 경우 30일 + 14일 = 44일)
chkmin = 44

# 테스트할 지표 클래스 (ZLEMA)
chkind = btind.ZLEMA


def test_run(main=False):
    """
    ZLEMA 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 ZLEMA 지표 테스트 실행
    testcommon.runtest(datas,
                       testcommon.TestStrategy,
                       main=main,
                       plot=main,          # main=True일 때만 플롯 표시
                       chkind=chkind,      # 테스트할 지표
                       chkmin=chkmin,      # 최소 기간
                       chkvals=chkvals)    # 예상 값들


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
