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
# Backtrader 브로커 시스템의 핵심 모듈
# =============================================================================
# 이 파일은 거래 실행 및 포트폴리오 관리를 담당하는 브로커 클래스들을 정의합니다.
# 주요 기능:
# - 주문 처리 및 실행
# - 수수료 계산 및 관리
# - 현금 및 포지션 관리
# - 슬리피지 시뮬레이션
# - 마진 및 레버리지 관리
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from backtrader.comminfo import CommInfoBase
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass

from . import fillers as fillers
from . import fillers as filler


# =============================================================================
# MetaBroker 클래스 - 브로커 클래스의 메타클래스
# =============================================================================
# 이 클래스는 브로커 클래스들의 메서드 호환성을 보장합니다.
# 주요 기능:
# - 메서드 이름 변환 및 호환성 처리
# - 누락된 메서드 자동 추가
class MetaBroker(MetaParams):
    def __init__(cls, name, bases, dct):
        '''
        Class has already been created ... fill missing methods if needed be
        클래스가 이미 생성되었으므로 필요한 경우 누락된 메서드를 추가합니다
        '''
        # Initialize the class
        # 클래스 초기화
        super(MetaBroker, cls).__init__(name, bases, dct)
        
        # =============================================================================
        # 메서드 이름 변환 매핑 (호환성을 위한 처리)
        # =============================================================================
        translations = {
            'get_cash': 'getcash',      # get_cash → getcash
            'get_value': 'getvalue',    # get_value → getvalue
        }

        # 누락된 메서드가 있으면 자동으로 추가
        for attr, trans in translations.items():
            if not hasattr(cls, attr):
                setattr(cls, name, getattr(cls, trans))


# =============================================================================
# BrokerBase 클래스 - 브로커의 기본 추상 클래스
# =============================================================================
# 이 클래스는 모든 브로커 구현체의 기본이 되는 추상 클래스입니다.
# 주요 기능:
# - 수수료 정보 관리
# - 주문 히스토리 관리
# - 자금 히스토리 관리
# - 수수료 계산
class BrokerBase(with_metaclass(MetaBroker, object)):
    # =============================================================================
    # 기본 파라미터 설정
    # =============================================================================
    params = (
        ('commission', CommInfoBase(percabs=True)),  # 기본 수수료 설정 (절대 비율)
    )

    def __init__(self):
        self.comminfo = dict()  # 수수료 정보를 저장하는 딕셔너리
        self.init()             # 초기화 메서드 호출

    def init(self):
        # called from init and from start
        # init과 start에서 호출됨
        if None not in self.comminfo:
            # 기본 수수료 정보가 없으면 설정
            self.comminfo = dict({None: self.p.commission})

    def start(self):
        # 브로커 시작 시 호출
        self.init()

    def stop(self):
        # 브로커 중지 시 호출
        pass

    def add_order_history(self, orders, notify=False):
        '''Add order history. See cerebro for details'''
        # 주문 히스토리 추가 (cerebro에서 상세 정보 확인)
        raise NotImplementedError

    def set_fund_history(self, fund):
        '''Add fund history. See cerebro for details'''
        # 자금 히스토리 설정 (cerebro에서 상세 정보 확인)
        raise NotImplementedError

    def getcommissioninfo(self, data):
        '''Retrieves the ``CommissionInfo`` scheme associated with the given
        ``data``'''
        # 주어진 데이터와 연관된 수수료 정보를 검색합니다
        if data._name in self.comminfo:
            # 데이터별 수수료 정보가 있으면 반환
            return self.comminfo[data._name]

        # 데이터별 수수료 정보가 없으면 기본 수수료 정보 반환
        return self.comminfo[None]

    def setcommission(self,
                      commission=0.0, margin=None, mult=1.0,
                      commtype=None, percabs=True, stocklike=False,
                      interest=0.0, interest_long=False, leverage=1.0,
                      automargin=False,
                      name=None):

        '''This method sets a `` CommissionInfo`` object for assets managed in
        the broker with the parameters. Consult the reference for
        ``CommInfoBase``

        If name is ``None``, this will be the default for assets for which no
        other ``CommissionInfo`` scheme can be found
        '''
        # =============================================================================
        # 수수료 정보 설정 메서드
        # =============================================================================
        # 이 메서드는 브로커에서 관리하는 자산에 대한 수수료 정보 객체를 설정합니다.
        # CommInfoBase 참조를 확인하세요.
        # 
        # name이 None이면, 다른 수수료 정보 체계를 찾을 수 없는 자산에 대한 기본값이 됩니다
        # 
        # 매개변수 설명:
        # - commission: 수수료 (기본값: 0.0)
        # - margin: 마진 요구사항 (기본값: None)
        # - mult: 승수 (기본값: 1.0)
        # - commtype: 수수료 유형 (기본값: None)
        # - percabs: 절대 비율 여부 (기본값: True)
        # - stocklike: 주식과 유사한 자산 여부 (기본값: False)
        # - interest: 이자율 (기본값: 0.0)
        # - interest_long: 롱 포지션 이자 여부 (기본값: False)
        # - leverage: 레버리지 (기본값: 1.0)
        # - automargin: 자동 마진 여부 (기본값: False)
        # - name: 수수료 정보 이름 (기본값: None)

        comm = CommInfoBase(commission=commission, margin=margin, mult=mult,
                            commtype=commtype, stocklike=stocklike,
                            percabs=percabs,
                            interest=interest, interest_long=interest_long,
                            leverage=leverage, automargin=automargin)
        self.comminfo[name] = comm

    def addcommissioninfo(self, comminfo, name=None):
        '''Adds a ``CommissionInfo`` object that will be the default for all assets if
        ``name`` is ``None``'''
        self.comminfo[name] = comminfo

    def getcash(self):
        raise NotImplementedError

    def getvalue(self, datas=None):
        raise NotImplementedError

    def get_fundshares(self):
        '''Returns the current number of shares in the fund-like mode'''
        return 1.0  # the abstract mode has only 1 share

    fundshares = property(get_fundshares)

    def get_fundvalue(self):
        return self.getvalue()

    fundvalue = property(get_fundvalue)

    def set_fundmode(self, fundmode, fundstartval=None):
        '''Set the actual fundmode (True or False)

        If the argument fundstartval is not ``None``, it will used
        '''
        pass  # do nothing, not all brokers can support this

    def get_fundmode(self):
        '''Returns the actual fundmode (True or False)'''
        return False

    fundmode = property(get_fundmode, set_fundmode)

    def getposition(self, data):
        raise NotImplementedError

    def submit(self, order):
        raise NotImplementedError

    def cancel(self, order):
        raise NotImplementedError

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            **kwargs):

        raise NotImplementedError

    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             **kwargs):

        raise NotImplementedError

    def next(self):
        pass

# __all__ = ['BrokerBase', 'fillers', 'filler']
