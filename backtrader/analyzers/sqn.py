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

# =============================================================================
# SQN(System Quality Number) 분석기 모듈
# =============================================================================
# 이 모듈은 Van K. Tharp가 정의한 SQN(시스템 품질 수치)를 계산합니다.
# SQN은 트레이딩 시스템의 품질을 평가하는 중요한 지표로,
# 거래 수익률의 일관성과 안정성을 측정합니다.
# 
# SQN 공식:
# SQN = √(거래 수) × 평균 거래 수익률 / 거래 수익률의 표준편차
# 
# SQN 등급 (거래 수 >= 30일 때 신뢰할 수 있음):
# - 1.6 - 1.9: 평균 이하
# - 2.0 - 2.4: 평균
# - 2.5 - 2.9: 좋음
# - 3.0 - 5.0: 우수
# - 5.1 - 6.9: 탁월
# - 7.0 이상: 성배급?
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

from backtrader import Analyzer
from backtrader.mathsupport import average, standarddev
from backtrader.utils import AutoOrderedDict


# =============================================================================
# SQN 클래스 - 시스템 품질 수치 분석기
# =============================================================================
# 이 클래스는 거래 시스템의 품질을 SQN 지표로 평가합니다.
# SQN은 거래 수익률의 평균과 표준편차를 고려하여 시스템의 안정성을 측정합니다.
class SQN(Analyzer):
    '''SQN or SystemQualityNumber. Defined by Van K. Tharp to categorize trading
    systems.

      - 1.6 - 1.9 Below average
      - 2.0 - 2.4 Average
      - 2.5 - 2.9 Good
      - 3.0 - 5.0 Excellent
      - 5.1 - 6.9 Superb
      - 7.0 -     Holy Grail?

    The formula:

      - SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit)

    The sqn value should be deemed reliable when the number of trades >= 30

    Methods:

      - get_analysis

        Returns a dictionary with keys "sqn" and "trades" (number of
        considered trades)

    '''
    # =============================================================================
    # 클래스 별칭 설정
    # =============================================================================
    alias = ('SystemQualityNumber',)  # SystemQualityNumber로도 사용 가능

    def create_analysis(self):
        '''Replace default implementation to instantiate an AutoOrdereDict
        rather than an OrderedDict'''
        # =============================================================================
        # 분석 결과를 저장할 구조 생성
        # =============================================================================
        # AutoOrderedDict를 사용하여 점(.) 표기법 지원
        self.rets = AutoOrderedDict()

    def start(self):
        # =============================================================================
        # 분석기 시작 시 초기화
        # =============================================================================
        super(SQN, self).start()
        self.pnl = list()  # 거래별 수익/손실을 저장할 리스트
        self.count = 0     # 완료된 거래 수 카운터

    def notify_trade(self, trade):
        # =============================================================================
        # 거래 완료 알림 처리
        # =============================================================================
        if trade.status == trade.Closed:  # 거래가 완전히 종료되었을 때
            self.pnl.append(trade.pnlcomm)  # 수수료 포함 수익/손실을 리스트에 추가
            self.count += 1                  # 거래 수 증가

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 SQN 계산
        # =============================================================================
        if self.count > 1:  # 거래가 2개 이상일 때만 계산
            # =============================================================================
            # SQN 계산을 위한 통계값 계산
            # =============================================================================
            pnl_av = average(self.pnl)      # 거래 수익률의 평균
            pnl_stddev = standarddev(self.pnl)  # 거래 수익률의 표준편차
            
            try:
                # =============================================================================
                # SQN 공식 적용
                # =============================================================================
                # SQN = √(거래 수) × 평균 거래 수익률 / 거래 수익률의 표준편차
                sqn = math.sqrt(len(self.pnl)) * pnl_av / pnl_stddev
            except ZeroDivisionError:
                # 표준편차가 0인 경우 (모든 거래가 동일한 수익률)
                sqn = None
        else:
            # 거래가 1개 이하인 경우 SQN을 0으로 설정
            sqn = 0

        # =============================================================================
        # 분석 결과 저장
        # =============================================================================
        self.rets.sqn = sqn      # 계산된 SQN 값
        self.rets.trades = self.count  # 분석에 사용된 거래 수
