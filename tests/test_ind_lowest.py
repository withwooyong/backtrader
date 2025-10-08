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

# Lowest 지표의 예상 값들 (14일 Lowest)
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# Lowest는 지정된 기간 내에서 가장 낮은 가격을 추적하는 지표입니다
# 이 지표는 지지선이나 하단 돌파점을 식별하는 데 유용합니다
chkvals = [
    ['4019.890000', '3570.170000', '3506.070000'],
]

# 지표의 최소 기간 (Lowest의 경우 14일)
chkmin = 14

# 테스트할 지표 클래스 (Lowest)
chkind = btind.Lowest

# 지표 생성 시 추가 인수 (14일 기간 설정)
chkargs = dict(period=14)


def test_run(main=False):
    """
    Lowest 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Lowest 지표 테스트 실행
    testcommon.runtest(datas,
                       testcommon.TestStrategy,
                       main=main,
                       plot=main,          # main=True일 때만 플롯 표시
                       chkind=chkind,      # 테스트할 지표
                       chkmin=chkmin,      # 최소 기간
                       chkvals=chkvals,    # 예상 값들
                       chkargs=chkargs)    # 지표 생성 시 추가 인수


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
