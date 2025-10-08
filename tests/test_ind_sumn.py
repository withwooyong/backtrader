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

# SumN 지표의 예상 값들 (14일 SumN)
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# SumN은 지정된 기간 동안의 가격 데이터의 합계를 계산하는 지표입니다
# 이 지표는 누적 효과를 나타내며, 추세의 강도와 지속성을 판단하는 데 사용됩니다
# 일반적으로 거래량이나 가격 변화량의 누적을 계산할 때 유용합니다
chkvals = [
    ['57406.490000', '50891.010000', '50424.690000'],
]

# 지표의 최소 기간 (SumN의 경우 14일)
chkmin = 14

# 테스트할 지표 클래스 (SumN)
chkind = btind.SumN

# 지표 생성 시 추가 인수 (14일 기간 설정)
chkargs = dict(period=14)


def test_run(main=False):
    """
    SumN 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 SumN 지표 테스트 실행
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
