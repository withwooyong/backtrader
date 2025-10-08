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

# 체크할 next 호출 수 (리플레이 모드에서의 특별한 검증)
chknext = 113

# SMA 지표의 예상 값들 (30주 이동평균)
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# 데이터가 주별로 리플레이되므로 주별 이동평균 값입니다
chkvals = [
    ['3836.453333', '3703.962333', '3741.802000']
]

# 지표의 최소 기간 (30주 이동평균)
chkmin = 30  # period will be in weeks

# 테스트할 지표 클래스 리스트 (SMA 지표)
chkind = [btind.SMA]

# 지표 생성 시 추가 인수 (현재는 비어있음)
chkargs = dict()


def test_run(main=False, exbar=False):
    """
    데이터 리플레이 테스트를 실행하는 함수
    
    이 테스트는 일별 데이터를 주별로 리플레이하여 처리하는 기능을 검증합니다.
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
        exbar: exactbars 설정 (False, -1, -2 중 하나)
    """
    # 테스트 데이터 로드 (일별 데이터)
    data = testcommon.getdata(0)
    
    # 데이터를 주별로 리플레이 설정
    data.replay(timeframe=bt.TimeFrame.Weeks, compression=1)
    datas = [data]
    
    # 공통 테스트 함수를 사용하여 리플레이 테스트 실행
    # runonce=False, preload=False로 설정하여 리플레이 모드 활성화
    testcommon.runtest(datas,
                       testcommon.TestStrategy,
                       main=main,
                       plot=main,          # main=True일 때만 플롯 표시
                       chkind=chkind,      # 테스트할 지표
                       chkmin=chkmin,      # 최소 기간
                       chkvals=chkvals,    # 예상 값들
                       chknext=chknext,    # next 호출 수 검증
                       chkargs=chkargs,    # 지표 생성 시 추가 인수
                       runonce=False,       # 리플레이 모드 활성화
                       preload=False,       # 프리로드 비활성화
                       exbar=exbar)        # exactbars 설정


if __name__ == '__main__':
    # 다양한 exactbars 설정으로 테스트 실행
    for exbar in [False, -1, -2]:
        test_run(main=True, exbar=exbar)
