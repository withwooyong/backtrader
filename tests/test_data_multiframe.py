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

# 테스트할 데이터 개수 (일별 데이터와 주별 데이터 2개)
chkdatas = 2

# 검증할 값들 (현재는 비어있음)
chkvals = []

# 지표의 최소 기간 (주별 데이터 때문에 151일)
chkmin = 151  # because of the weekly data

# 테스트할 지표 클래스 리스트 (SMA 지표)
chkind = [btind.SMA]

# 지표 생성 시 추가 인수 (현재는 비어있음)
chkargs = dict()


def test_run(main=False):
    """
    다중 데이터 프레임 테스트를 실행하는 함수
    
    이 테스트는 서로 다른 시간 프레임(일별, 주별)의 데이터를
    동시에 처리하는 기능을 검증합니다.
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드 (일별과 주별 데이터)
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 다중 데이터 프레임 테스트 실행
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
