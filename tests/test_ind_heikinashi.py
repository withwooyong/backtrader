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

# 테스트할 데이터 개수
chkdatas = 1

# Heikin Ashi 지표의 예상 값들
# Heikin Ashi는 4개의 라인을 가짐: [Open, High, Low, Close]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# Heikin Ashi는 일본식 캔들스틱 차트로, 추세를 더 명확하게 보여줍니다
chkvals = [
    ['4119.466107', '3591.732500', '3578.625259'],  # Open (시가)
    ['4142.010000', '3638.420000', '3662.920000'],  # High (고가)
    ['4119.466107', '3591.732500', '3578.625259'],  # Low (저가)
    ['4128.002500', '3614.670000', '3653.455000']   # Close (종가)
]

# 지표의 최소 기간 (Heikin Ashi의 경우 2일)
chkmin = 2

# 테스트할 지표 클래스 (Heikin Ashi)
chkind = bt.ind.HeikinAshi


def test_run(main=False):
    """
    Heikin Ashi 지표 테스트를 실행하는 함수
    
    현재는 테스트가 비활성화되어 있습니다 (if False: 조건).
    
    Args:
        main: 메인 출력 모드 여부 (사용되지 않음)
    """
    if False:  # 현재 테스트 비활성화
        # 테스트 데이터 로드
        datas = [testcommon.getdata(i) for i in range(chkdatas)]
        
        # 공통 테스트 함수를 사용하여 Heikin Ashi 지표 테스트 실행
        testcommon.runtest(datas,
                           testcommon.TestStrategy,
                           main=main,
                           plot=main,          # main=True일 때만 플롯 표시
                           chkind=chkind,      # 테스트할 지표
                           chkmin=chkmin,      # 최소 기간
                           chkvals=chkvals)    # 예상 값들


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 테스트 실행 (현재는 비활성화됨)
    test_run(main=True)
