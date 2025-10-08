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

# Vortex 지표의 예상 값들 (14일 Vortex)
# Vortex는 2개의 라인을 가짐: [VI+, VI-]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# VI+ (Vortex Indicator Plus)는 상승 추세를, VI- (Vortex Indicator Minus)는 하락 추세를 나타냅니다
# 1.0을 기준으로 하여 1.0보다 크면 해당 방향의 추세가 강함을 의미합니다
chkvals = [
    ['1.245434', '0.921076', '1.062278'],   # VI+ (상승 추세 지표)
    ['0.707948', '0.966375', '0.803849']    # VI- (하락 추세 지표)
]

# 지표의 최소 기간 (Vortex의 경우 14일 + 1 = 15일)
chkmin = 15

# 테스트할 지표 클래스 (Vortex)
chkind = btind.Vortex


def test_run(main=False):
    """
    Vortex 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Vortex 지표 테스트 실행
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
