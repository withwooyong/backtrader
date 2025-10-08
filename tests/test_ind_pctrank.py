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

# Percent Rank 지표의 예상 값들 (50일 Percent Rank)
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# Percent Rank는 현재 가격이 지정된 기간(50일) 내에서 차지하는 상대적 순위를 나타내는 지표입니다
# 0.0에서 1.0 범위의 값을 가지며, 0.0은 최저점, 1.0은 최고점을 의미합니다
# 0.5는 중간값을 나타내며, 이 지표는 과매수/과매도 구간을 판단하는 데 유용합니다
chkvals = [
    ['0.900000', '0.880000', '0.980000'],
]

# 지표의 최소 기간 (Percent Rank의 경우 50일)
chkmin = 50

# 테스트할 지표 클래스 (Percent Rank)
chkind = btind.PercentRank


def test_run(main=False):
    """
    Percent Rank 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Percent Rank 지표 테스트 실행
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
