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

# Ichimoku 지표의 예상 값들
# Ichimoku는 5개의 라인을 가짐: [Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span]
# 각 값은 [시작점, 중간점, 끝점] 순서로 되어 있음
# 일부 값은 튜플로 되어 있어 NaN과 실제 값을 모두 포함할 수 있습니다
chkvals = [
    ['4110.000000', '3821.030000', '3748.785000'],                    # Tenkan-sen (전환선)
    ['4030.920000', '3821.030000', '3676.860000'],                    # Kijun-sen (기준선)
    ['4057.485000', '3753.502500', '3546.152500'],                    # Senkou Span A (선행스팬 A)
    ['3913.300000', '3677.815000', '3637.130000'],                    # Senkou Span B (선행스팬 B)
    [('nan', '3682.320000'), '3590.910000', '3899.410000']           # Chikou Span (지연스팬)
]

# 지표의 최소 기간 (Ichimoku의 경우 78일)
chkmin = 78

# 테스트할 지표 클래스 (Ichimoku)
chkind = bt.ind.Ichimoku


def test_run(main=False):
    """
    Ichimoku 지표 테스트를 실행하는 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 Ichimoku 지표 테스트 실행
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
