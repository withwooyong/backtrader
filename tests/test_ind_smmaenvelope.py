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

# SMMA Envelope 지표의 예상 값들 (30일 SMMA Envelope)
# SMMA Envelope는 3개의 라인을 가짐: [Lower Band, Middle Band, Upper Band]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# SMMA Envelope는 SMMA(Smoothed Moving Average)를 중심으로 상하 밴드를 생성합니다
# SMMA의 특성상 일반 SMA Envelope보다 더 부드럽고 안정적인 밴드를 제공합니다
# 이 밴드는 과매수/과매도 구간을 판단하는 데 사용되며, 노이즈가 적은 신호를 제공합니다
chkvals = [
    ['4021.569725', '3644.444667', '3616.427648'],   # Lower Band (하단 밴드)
    ['4122.108968', '3735.555783', '3706.838340'],   # Middle Band (중간 밴드)
    ['3921.030482', '3553.333550', '3526.016957'],   # Upper Band (상단 밴드)
]

# 지표의 최소 기간 (SMMA Envelope의 경우 30일)
chkmin = 30

# 테스트할 지표 클래스 (SMMA Envelope)
chkind = btind.SMMAEnvelope


def test_run(main=False):
    """
    SMMA Envelope 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 SMMA Envelope 지표 테스트 실행
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
