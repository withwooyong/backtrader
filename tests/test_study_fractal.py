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

# Fractal 스터디의 예상 값들
# Fractal은 2개의 라인을 가짐: [Upper Fractal, Lower Fractal]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# Upper Fractal은 고점을, Lower Fractal은 저점을 나타냅니다
# 초기에는 'nan' 값이 나오다가 충분한 데이터가 쌓이면 실제 값이 나타납니다
chkvals = [
    ['nan', 'nan', 'nan'],                    # Upper Fractal (상단 프랙탈)
    ['nan', 'nan', '3553.692850']             # Lower Fractal (하단 프랙탈)
]

# 스터디의 최소 기간 (Fractal의 경우 5일)
chkmin = 5

# 테스트할 스터디 클래스 (Fractal)
chkind = bt.studies.Fractal


def test_run(main=False):
    """
    Fractal 스터디 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Fractal 스터디 테스트 실행
    testcommon.runtest(datas,
                       testcommon.TestStrategy,
                       main=main,
                       plot=main,          # main=True일 때만 플롯 표시
                       chkind=chkind,      # 테스트할 스터디
                       chkmin=chkmin,      # 최소 기간
                       chkvals=chkvals)    # 예상 값들


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
