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
import testcommon

class TestFrompackages(testcommon.SampleParamsHolder):
    """
    frompackages 가져오기 메커니즘을 사용하는 기본 클래스로부터 상속받을 때
    기본 클래스의 기능이 손상되지 않는지 테스트하기 위한 클래스
    
    이 클래스는 SampleParamsHolder를 상속받아 frompackages 지시문의
    상속 시 동작을 검증합니다.
    """
    def __init__(self):
        """클래스 초기화"""
        super(TestFrompackages, self).__init__()
        # 지연 배열 준비 (현재는 구현되지 않음)


def test_run(main=False):
    """
    TestFrompackages 클래스를 인스턴스화하고 예외가 발생하지 않는지 확인
    
    이 테스트는 frompackages 지시문이 상속 시에도 올바르게 작동하는지
    검증합니다.
    
    버그 논의:
    https://community.backtrader.com/topic/2661/frompackages-directive-functionality-seems-to-be-broken-when-using-inheritance
    
    Args:
        main: 메인 출력 모드 여부 (사용되지 않음)
    """
    # TestFrompackages 클래스 인스턴스 생성
    # 예외가 발생하지 않으면 테스트 통과
    test = TestFrompackages()


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 테스트 실행
    test_run(main=True)
