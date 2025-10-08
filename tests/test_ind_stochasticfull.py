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

# Stochastic Full 지표의 예상 값들 (14일 Stochastic Full)
# Stochastic Full은 3개의 라인을 가짐: [%K, %D, %DSlow]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# %K는 현재 가격의 상대적 위치를 나타내며, %D는 %K의 이동평균입니다
# %DSlow는 %D의 이동평균으로, 가장 부드러운 신호를 제공합니다
# 0-100 범위의 값을 가지며, 80 이상은 과매수, 20 이하는 과매도를 의미합니다
chkvals = [
    ['83.541267', '36.818395', '41.769503'],   # %K (메인 스토캐스틱 라인)
    ['88.667626', '21.409626', '63.796187'],   # %D (%K의 이동평균)
    ['82.845850', '15.710059', '77.642219'],   # %DSlow (%D의 이동평균)
]

# 지표의 최소 기간 (Stochastic Full의 경우 14일 + 4일 = 18일)
chkmin = 18

# 테스트할 지표 클래스 (Stochastic Full)
chkind = btind.StochasticFull


def test_run(main=False):
    """
    Stochastic Full 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Stochastic Full 지표 테스트 실행
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
