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

# Oscillator 지표의 예상 값들 (30일 Oscillator)
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# Oscillator는 가격과 이동평균 간의 차이를 나타내는 일반적인 오실레이터 지표입니다
# 0을 중심으로 양수/음수 값을 가지며, 양수는 가격이 이동평균 위에 있음을 의미합니다
# 이 지표는 추세의 방향과 강도를 판단하는 데 사용됩니다
chkvals = [
    ['56.477000', '51.185333', '2.386667']
]

# 지표의 최소 기간 (Oscillator의 경우 30일)
chkmin = 30

# 테스트할 지표 클래스 (Oscillator)
chkind = btind.Oscillator


class TS2(testcommon.TestStrategy):
    """
    Oscillator 테스트를 위한 특별한 전략 클래스
    
    이 클래스는 SMA 지표를 사용하여 Oscillator 지표를 테스트합니다.
    """
    def __init__(self):
        # SMA 지표 생성 (Oscillator의 기준선으로 사용)
        ind = btind.MovAv.SMA(self.data)
        self.p.inddata = [ind]
        super(TS2, self).__init__()


def test_run(main=False):
    """
    Oscillator 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Oscillator 지표 테스트 실행
    # TS2 전략을 사용하여 SMA 기반 Oscillator 테스트
    testcommon.runtest(datas,
                       TS2,
                       main=main,
                       plot=main,          # main=True일 때만 플롯 표시
                       chkind=chkind,      # 테스트할 지표
                       chkmin=chkmin,      # 최소 기간
                       chkvals=chkvals)    # 예상 값들


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
