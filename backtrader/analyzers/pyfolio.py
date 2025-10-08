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
# PyFolio 통합 분석기 모듈
# =============================================================================
# 이 모듈은 Backtrader와 PyFolio 라이브러리 간의 데이터 호환성을 제공합니다.
# PyFolio는 금융 포트폴리오 분석을 위한 강력한 Python 라이브러리로,
# 이 분석기를 통해 Backtrader의 백테스팅 결과를 PyFolio에서 분석할 수 있습니다.
# 
# 주요 특징:
# - 4개의 하위 분석기를 통합하여 PyFolio 호환 데이터 생성
# - 포트폴리오 수익률, 포지션 가치, 거래 내역, 레버리지 정보 제공
# - 일별 데이터를 기본으로 하여 연간 수익률 등 계산
# - PyFolio의 표준 데이터 형식으로 결과 변환
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import collections

import backtrader as bt
from backtrader.utils.py3 import items, iteritems

from . import TimeReturn, PositionsValue, Transactions, GrossLeverage


# =============================================================================
# PyFolio 클래스 - PyFolio 통합 분석기
# =============================================================================
# 이 클래스는 4개의 하위 분석기를 사용하여 데이터를 수집하고
# PyFolio와 호환되는 데이터셋으로 변환합니다.
class PyFolio(bt.Analyzer):
    '''This analyzer uses 4 children analyzers to collect data and transforms it
    in to a data set compatible with ``pyfolio``

    Children Analyzer

      - ``TimeReturn``

        Used to calculate the returns of the global portfolio value

      - ``PositionsValue``

        Used to calculate the value of the positions per data. It sets the
        ``headers`` and ``cash`` parameters to ``True``

      - ``Transactions``

        Used to record each transaction on a data (size, price, value). Sets
        the ``headers`` parameter to ``True``

      - ``GrossLeverage``

        Keeps track of the gross leverage (how much the strategy is invested)

    Params:
      These are passed transparently to the children

      - timeframe (default: ``bt.TimeFrame.Days``)

        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: `1``)

        If ``None`` then the compression of the 1st data of the system will be
        used

    Both ``timeframe`` and ``compression`` are set following the default
    behavior of ``pyfolio`` which is working with *daily* data and upsample it
    to obtaine values like yearly returns.

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    
    # =============================================================================
    # 분석기 파라미터 설정
    # =============================================================================
    params = (
        ('timeframe', bt.TimeFrame.Days),  # 시간 프레임 (기본값: 일별)
        ('compression', 1)                 # 압축 비율 (기본값: 1)
    )

    def __init__(self):
        # =============================================================================
        # 하위 분석기 초기화
        # =============================================================================
        # 시간 프레임과 압축 설정을 딕셔너리로 구성
        dtfcomp = dict(timeframe=self.p.timeframe,
                       compression=self.p.compression)

        # =============================================================================
        # 4개의 하위 분석기 생성
        # =============================================================================
        self._returns = TimeReturn(**dtfcomp)           # 포트폴리오 수익률 계산
        self._positions = PositionsValue(headers=True, cash=True)  # 포지션 가치 (헤더와 현금 포함)
        self._transactions = Transactions(headers=True) # 거래 내역 (헤더 포함)
        self._gross_lev = GrossLeverage()               # 총 레버리지 추적

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 결과 수집
        # =============================================================================
        super(PyFolio, self).stop()
        
        # =============================================================================
        # 각 하위 분석기의 결과를 수집하여 PyFolio 호환 형식으로 구성
        # =============================================================================
        self.rets['returns'] = self._returns.get_analysis()      # 수익률 데이터
        self.rets['positions'] = self._positions.get_analysis()  # 포지션 가치 데이터
        self.rets['transactions'] = self._transactions.get_analysis()  # 거래 내역 데이터
        self.rets['gross_lev'] = self._gross_lev.get_analysis()  # 레버리지 데이터

    def get_pf_items(self):
        # =============================================================================
        # PyFolio 호환 데이터 반환 메서드
        # =============================================================================
        '''Returns a tuple of 4 elements which can be used for further processing with
          ``pyfolio``

          returns, positions, transactions, gross_leverage

        Because the objects are meant to be used as direct input to ``pyfolio``
        this method makes a local import of ``pandas`` to convert the internal
        *backtrader* results to *pandas DataFrames* which is the expected input
        by, for example, ``pyfolio.create_full_tear_sheet``

        The method will break if ``pandas`` is not installed
        '''
        # =============================================================================
        # Pandas 로컬 임포트 (pandas가 없는 설치 환경 방해 방지)
        # =============================================================================
        # keep import local to avoid disturbing installations with no pandas
        # pandas가 없는 설치 환경을 방해하지 않기 위해 로컬 임포트 유지
        import pandas
        from pandas import DataFrame as DF

        # =============================================================================
        # 수익률 데이터 변환
        # =============================================================================
        # Returns
        # 수익률
        cols = ['index', 'return']
        returns = DF.from_records(iteritems(self.rets['returns']),
                                  index=cols[0], columns=cols)
        returns.index = pandas.to_datetime(returns.index)
        returns.index = returns.index.tz_localize('UTC')
        rets = returns['return']
        
        # =============================================================================
        # 포지션 데이터 변환
        # =============================================================================
        # Positions
        # 포지션들
        pss = self.rets['positions']
        ps = [[k] + v[-2:] for k, v in iteritems(pss)]
        cols = ps.pop(0)  # headers are in the first entry (헤더는 첫 번째 항목에 있음)
        positions = DF.from_records(ps, index=cols[0], columns=cols)
        positions.index = pandas.to_datetime(positions.index)
        positions.index = positions.index.tz_localize('UTC')

        # =============================================================================
        # 거래 내역 데이터 변환
        # =============================================================================
        # Transactions
        # 거래 내역들
        txss = self.rets['transactions']
        txs = list()
        # =============================================================================
        # 거래 내역 구조 설명:
        # 거래들은 공통 키(날짜)를 가지며 여러 자산에 대해 발생할 수 있습니다.
        # 딕셔너리는 단일 키와 리스트의 리스트를 가집니다.
        # 각 하위 리스트는 거래의 필드들을 포함합니다.
        # 따라서 리스트 간접 참조를 해제하기 위해 이중 루프를 사용합니다.
        # =============================================================================
        # The transactions have a common key (date) and can potentially happend
        # for several assets. The dictionary has a single key and a list of
        # lists. Each sublist contains the fields of a transaction
        # Hence the double loop to undo the list indirection
        for k, v in iteritems(txss):
            for v2 in v:
                txs.append([k] + v2)

        cols = txs.pop(0)  # headers are in the first entry (헤더는 첫 번째 항목에 있음)
        transactions = DF.from_records(txs, index=cols[0], columns=cols)
        transactions.index = pandas.to_datetime(transactions.index)
        transactions.index = transactions.index.tz_localize('UTC')

        # =============================================================================
        # 총 레버리지 데이터 변환
        # =============================================================================
        # Gross Leverage
        # 총 레버리지
        cols = ['index', 'gross_lev']
        gross_lev = DF.from_records(iteritems(self.rets['gross_lev']),
                                    index=cols[0], columns=cols)

        gross_lev.index = pandas.to_datetime(gross_lev.index)
        gross_lev.index = gross_lev.index.tz_localize('UTC')
        glev = gross_lev['gross_lev']

        # =============================================================================
        # 모든 데이터를 함께 반환
        # =============================================================================
        # Return all together
        # 모든 것을 함께 반환
        return rets, positions, transactions, glev
