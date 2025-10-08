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

# KST 지표의 예상 값들 (Know Sure Thing)
# KST는 2개의 라인을 가짐: [KST, Signal]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# KST는 여러 기간의 이동평균을 결합하여 장기 추세를 파악하는 지표입니다
# 0을 중심으로 양수/음수 값을 가지며, 추세의 방향과 강도를 나타냅니다
chkvals = [
    ['18.966300', '33.688645', '27.643797'],   # KST 라인 (메인 라인)
    ['11.123593', '37.882890', '16.602624']    # Signal 라인 (신호선)
]

# 지표의 최소 기간 (KST의 경우 48일)
chkmin = 48

# 테스트할 지표 클래스 (Know Sure Thing)
chkind = bt.ind.KST


def test_run(main=False):
    """
    KST 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 KST 지표 테스트 실행
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
