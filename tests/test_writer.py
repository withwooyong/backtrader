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

import time

import testcommon

import backtrader as bt
import backtrader.indicators as btind


# 테스트할 데이터 개수
chkdatas = 1


class TestStrategy(bt.Strategy):
    """
    작성자(Writer) 테스트를 위한 간단한 전략 클래스
    
    이 전략은 SMA 지표를 생성하여 데이터 출력을 위한 기본 구조를 제공합니다.
    """
    params = dict(main=False)

    def __init__(self):
        """전략 초기화 - SMA 지표 생성"""
        btind.SMA()  # SMA 지표 생성 (데이터 출력을 위한 기본 구조)


def test_run(main=False):
    """
    작성자 테스트를 실행하는 메인 함수
    
    이 테스트는 WriterStringIO를 사용하여 백테스트 결과를 문자열로 출력하고,
    출력된 데이터의 형식과 내용을 검증합니다.
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 테스트 데이터 로드
    datas = [testcommon.getdata(i) for i in range(chkdatas)]
    
    # 공통 테스트 함수를 사용하여 전략 테스트 실행
    # WriterStringIO를 사용하여 CSV 형식으로 출력
    cerebros = testcommon.runtest(datas,
                                  TestStrategy,
                                  main=main,
                                  plot=main,
                                  writer=(bt.WriterStringIO, dict(csv=True)))

    # 각 Cerebro 객체에서 작성자 결과 분석
    for cerebro in cerebros:
        writer = cerebro.runwriters[0]  # 첫 번째 작성자 가져오기
        
        if main:
            # 메인 모드일 때 출력 내용 표시
            # writer.out.seek(0)  # 출력 버퍼의 시작으로 이동 (주석 처리됨)
            for l in writer.out:
                print(l.rstrip('\r\n'))

        else:
            # 테스트 모드일 때 출력 내용 검증
            lines = iter(writer.out)
            
            # 첫 번째 줄은 구분선('=' * 79)이어야 함
            l = next(lines).rstrip('\r\n')
            assert l == '=' * 79

            # 데이터 라인 수 계산 (구분선 사이의 라인들)
            count = 0
            while True:
                l = next(lines).rstrip('\r\n')
                if l[0] == '=':  # 다음 구분선을 만나면 중단
                    break
                count += 1

            # 헤더 + 256개 데이터 라인이 있어야 함
            assert count == 256


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
