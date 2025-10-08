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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

# =============================================================================
# 연간 수익률(Annual Return) 분석기 모듈
# =============================================================================
# 이 모듈은 백테스팅 결과의 연간 수익률을 계산합니다.
# 연간 수익률은 각 연도의 시작과 끝 시점의 포트폴리오 가치를 비교하여 계산됩니다.
# 
# 주요 특징:
# - 연도별 수익률 계산
# - 연도 간 수익률 비교 가능
# - 백테스팅 기간의 모든 연도에 대한 수익률 제공
# 
# 연간 수익률 공식:
# Annual Return = (연말 가치 / 연초 가치) - 1
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import OrderedDict

from backtrader.utils.py3 import range
from backtrader import Analyzer


# =============================================================================
# AnnualReturn 클래스 - 연간 수익률 분석기
# =============================================================================
# 이 클래스는 백테스팅 결과에서 연도별 수익률을 계산합니다.
# 각 연도의 시작과 끝 시점의 포트폴리오 가치를 비교하여 연간 수익률을 산출합니다.
class AnnualReturn(Analyzer):
    '''
    This analyzer calculates the AnnualReturns by looking at the beginning
    and end of the year

    Params:

      - (None)

    Member Attributes:

      - ``rets``: list of calculated annual returns

      - ``ret``: dictionary (key: year) of annual returns

    **get_analysis**:

      - Returns a dictionary of annual returns (key: year)
    '''

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 연간 수익률 계산
        # =============================================================================
        # Must have stats.broker
        # 브로커 통계가 있어야 함
        
        cur_year = -1  # 현재 처리 중인 연도 (-1은 초기값)

        # =============================================================================
        # 가치 변수 초기화
        # =============================================================================
        value_start = 0.0  # 연도 시작 시 포트폴리오 가치
        value_cur = 0.0    # 현재 포트폴리오 가치
        value_end = 0.0    # 연도 끝 시 포트폴리오 가치

        # =============================================================================
        # 결과 저장 구조 초기화
        # =============================================================================
        self.rets = list()           # 연간 수익률을 순서대로 저장하는 리스트
        self.ret = OrderedDict()     # 연도별 수익률을 저장하는 딕셔너리 (순서 유지)

        # =============================================================================
        # 데이터를 역순으로 순회하며 연간 수익률 계산
        # =============================================================================
        # range(len(self.data) - 1, -1, -1): 데이터의 마지막부터 처음까지 역순으로
        for i in range(len(self.data) - 1, -1, -1):
            dt = self.data.datetime.date(-i)                    # 현재 날짜
            value_cur = self.strategy.stats.broker.value[-i]    # 현재 포트폴리오 가치

            if dt.year > cur_year:
                # =============================================================================
                # 새로운 연도가 시작되었을 때
                # =============================================================================
                if cur_year >= 0:
                    # =============================================================================
                    # 이전 연도의 수익률 계산 및 저장
                    # =============================================================================
                    # 연간 수익률 = (연말 가치 / 연초 가치) - 1
                    annualret = (value_end / value_start) - 1.0
                    self.rets.append(annualret)        # 리스트에 추가
                    self.ret[cur_year] = annualret     # 딕셔너리에 저장

                    # changing between real years, use last value as new start
                    # 실제 연도가 바뀌었으므로, 마지막 값을 새로운 시작값으로 사용
                    value_start = value_end
                else:
                    # No value set whatsoever, use the currently loaded value
                    # 아직 값이 설정되지 않았으므로, 현재 로드된 값을 시작값으로 사용
                    value_start = value_cur

                cur_year = dt.year  # 현재 연도 업데이트

            # No matter what, the last value is always the last loaded value
            # 어떤 경우든 마지막 값은 항상 마지막으로 로드된 값
            value_end = value_cur

        # =============================================================================
        # 마지막 연도의 수익률 계산 (아직 계산되지 않은 경우)
        # =============================================================================
        if cur_year not in self.ret:
            # finish calculating pending data
            # 대기 중인 데이터 계산 완료
            annualret = (value_end / value_start) - 1.0
            self.rets.append(annualret)
            self.ret[cur_year] = annualret

    def get_analysis(self):
        # =============================================================================
        # 분석 결과 반환
        # =============================================================================
        # 연도별 수익률이 저장된 딕셔너리를 반환
        return self.ret
