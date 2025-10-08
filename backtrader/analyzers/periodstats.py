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
# 기간별 통계(Period Statistics) 분석기 모듈
# =============================================================================
# 이 모듈은 지정된 시간 프레임에 대한 기본 통계를 계산합니다.
# 각 기간별 수익률의 분포와 특성을 분석하여
# 전략의 성과 패턴을 파악할 수 있습니다.
# 
# 주요 특징:
# - 다양한 시간 프레임 지원 (연간, 월간, 주간, 일간 등)
# - 수익률의 평균, 표준편차, 최고/최저값 계산
# - 양수/음수/무변화 기간의 개수 및 비율
# - 펀드 모드 지원
# 
# 제공하는 통계:
# - average: 평균 수익률
# - stddev: 수익률의 표준편차
# - positive: 양수 수익률 기간 수
# - negative: 음수 수익률 기간 수
# - nochange: 무변화 기간 수
# - best: 최고 수익률
# - worst: 최저 수익률
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import backtrader as bt
from backtrader.utils.py3 import itervalues
from backtrader.mathsupport import average, standarddev
from . import TimeReturn


__all__ = ['PeriodStats']


# =============================================================================
# PeriodStats 클래스 - 기간별 통계 분석기
# =============================================================================
# 이 클래스는 지정된 시간 프레임에 대한 기본 통계를 계산합니다.
# TimeReturn 분석기를 사용하여 기간별 수익률을 수집하고,
# 이를 바탕으로 다양한 통계 지표를 산출합니다.
class PeriodStats(bt.Analyzer):
    '''Calculates basic statistics for given timeframe

    Params:

      - ``timeframe`` (default: ``Years``)
        If ``None`` the ``timeframe`` of the 1st data in the system will be
        used

        Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
        time constraints

      - ``compression`` (default: ``1``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

        If ``None`` then the compression of the 1st data of the system will be
        used

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior


    ``get_analysis`` returns a dictionary containing the keys:

      - ``average``
      - ``stddev``
      - ``positive``
      - ``negative``
      - ``nochange``
      - ``best``
      - ``worst``

    If the parameter ``zeroispos`` is set to ``True``, periods with no change
    will be counted as positive
    '''

    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('timeframe', bt.TimeFrame.Years),  # 시간 프레임 (기본값: 연간)
        ('compression', 1),                 # 압축 비율 (기본값: 1)
        ('zeroispos', False),               # 무변화를 양수로 계산할지 여부
        ('fund', None),                     # 펀드 모드 설정 (None이면 자동 감지)
    )

    def __init__(self):
        # =============================================================================
        # 하위 분석기 초기화
        # =============================================================================
        # TimeReturn 분석기를 사용하여 기간별 수익률 수집
        self._tr = TimeReturn(timeframe=self.p.timeframe,
                              compression=self.p.compression, fund=self.p.fund)

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 통계 계산
        # =============================================================================
        trets = self._tr.get_analysis()  # dict key = date, value = ret (딕셔너리: 키=날짜, 값=수익률)
        pos = nul = neg = 0  # 양수, 무변화, 음수 기간 수 초기화
        
        # =============================================================================
        # 수익률 값들을 리스트로 변환
        # =============================================================================
        trets = list(itervalues(trets))
        
        # =============================================================================
        # 각 기간별 수익률을 분류하여 카운트
        # =============================================================================
        for tret in trets:
            if tret > 0.0:
                pos += 1  # 양수 수익률 기간
            elif tret < 0.0:
                neg += 1  # 음수 수익률 기간
            else:
                if self.p.zeroispos:
                    pos += tret == 0.0  # 무변화를 양수로 계산하는 경우