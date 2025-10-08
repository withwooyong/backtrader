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
# Interactive Brokers (IB) 브로커 연동 모듈
# =============================================================================
# 이 모듈은 Backtrader와 Interactive Brokers 플랫폼을 연동하여
# 실시간 거래 및 백테스팅을 지원합니다.
# 
# 주요 기능:
# - IB TWS/Gateway와의 실시간 연결
# - 다양한 주문 유형 지원 (시장가, 지정가, 스탑, 스탑리밋 등)
# - 실시간 시세 데이터 수신
# - 포지션 및 계좌 정보 실시간 동기화
# - 주문 상태 실시간 추적
# 
# 필수 의존성:
# - ibpy 또는 ibapi 패키지 설치 필요
# - IB TWS 또는 Gateway 실행 필요
# - 적절한 API 권한 설정 필요
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
from copy import copy
from datetime import date, datetime, timedelta
import threading
import uuid

import ib.ext.Order
import ib.opt as ibopt

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, bstr, with_metaclass, queue, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import ibstore
from backtrader.utils import AutoDict, AutoOrderedDict
from backtrader.comminfo import CommInfoBase

bytes = bstr  # py2/3 need for ibpy (Python 2/3 호환성을 위한 바이트 처리)


# =============================================================================
# IBOrderState 클래스 - IB 주문 상태 래퍼
# =============================================================================
# 이 클래스는 IB의 OrderState 객체를 래핑하여
# 주문 상태 정보를 쉽게 접근하고 출력할 수 있게 합니다.
class IBOrderState(object):
    # wraps OrderState object and can print it
    # OrderState 객체를 래핑하고 출력할 수 있음
    
    # =============================================================================
    # IB 주문 상태 필드들
    # =============================================================================
    _fields = ['status', 'initMargin', 'maintMargin', 'equityWithLoan',
               'commission', 'minCommission', 'maxCommission',
               'commissionCurrency', 'warningText']

    def __init__(self, orderstate):
        # =============================================================================
        # IB OrderState 객체에서 필요한 필드들을 추출하여 속성으로 설정
        # =============================================================================
        for f in self._fields:
            fname = 'm_' + f
            setattr(self, fname, getattr(orderstate, fname))

    def __str__(self):
        # =============================================================================
        # 주문 상태 정보를 읽기 쉬운 형태로 출력
        # =============================================================================
        txt = list()
        txt.append('--- ORDERSTATE BEGIN')
        for f in self._fields:
            fname = 'm_' + f
            txt.append('{}: {}'.format(f.capitalize(), getattr(self, fname)))
        txt.append('--- ORDERSTATE END')
        return '\n'.join(txt)


# =============================================================================
# IBOrder 클래스 - IB 주문 래퍼
# =============================================================================
# 이 클래스는 IBPy 주문을 상속받아 Backtrader와의 호환성을 제공합니다.
# OrderBase가 파라미터를 처리한 후, __init__ 메서드가
# IB 주문 객체에 적절한 값을 설정합니다.
class IBOrder(OrderBase, ib.ext.Order.Order):
    '''Subclasses the IBPy order to provide the minimum extra functionality
    needed to be compatible with the internally defined orders

    Once ``OrderBase`` has processed the parameters, the __init__ method takes
    over to use the parameter values and set the appropriate values in the
    ib.ext.Order.Order object

    Any extra parameters supplied with kwargs are applied directly to the
    ib.ext.Order.Order object, which could be used as follows::

      Example: if the 4 order execution types directly supported by
      ``backtrader`` are not enough, in the case of for example
      *Interactive Brokers* the following could be passed as *kwargs*::

        orderType='LIT', lmtPrice=10.0, auxPrice=9.8

      This would override the settings created by ``backtrader`` and
      generate a ``LIMIT IF TOUCHED`` order with a *touched* price of 9.8
      and a *limit* price of 10.0.

    This would be done almost always from the ``Buy`` and ``Sell`` methods of
    the ``Strategy`` subclass being used in ``Cerebro``
    '''

    def __str__(self):
        # =============================================================================
        # 기본 클래스 출력에 IB 주문 특정 필드 추가
        # =============================================================================
        '''Get the printout from the base class and add some ib.Order specific
        fields'''
        basetxt = super(IBOrder, self).__str__()
        tojoin = [basetxt]
        tojoin.append('Ref: {}'.format(self.ref))
        tojoin.append('orderId: {}'.format(self.m_orderId))
        tojoin.append('Action: {}'.format(self.m_action))
        tojoin.append('Size (ib): {}'.format(self.m_totalQuantity))
        tojoin.append('Lmt Price: {}'.format(self.m_lmtPrice))
        tojoin.append('Aux Price: {}'.format(self.m_auxPrice))
        tojoin.append('OrderType: {}'.format(self.m_orderType))
        tojoin.append('Tif (Time in Force): {}'.format(self.m_tif))
        tojoin.append('GoodTillDate: {}'.format(self.m_goodTillDate))
        return '\n'.join(tojoin)

    # Map backtrader order types to the ib specifics
    _IBOrdTypes = {
        None: bytes('MKT'),  # default
        Order.Market: bytes('MKT'),
        Order.Limit: bytes('LMT'),
        Order.Close: bytes('MOC'),
        Order.Stop: bytes('STP'),
        Order.StopLimit: bytes('STPLMT'),
        Order.StopTrail: bytes('TRAIL'),
        Order.StopTrailLimit: bytes('TRAIL LIMIT'),
    }

    def __init__(self, action, **kwargs):

        # Marker to indicate an openOrder has been seen with
        # PendinCancel/Cancelled which is indication of an upcoming
        # cancellation
        self._willexpire = False

        self.ordtype = self.Buy if action == 'BUY' else self.Sell

        super(IBOrder, self).__init__()
        ib.ext.Order.Order.__init__(self)  # Invoke 2nd base class

        # Now fill in the specific IB parameters
        self.m_orderType = self._IBOrdTypes[self.exectype]
        self.m_permid = 0

        # 'B' or 'S' should be enough
        self.m_action = bytes(action)

        # Set the prices
        self.m_lmtPrice = 0.0
        self.m_auxPrice = 0.0

        if self.exectype == self.Market:  # is it really needed for Market?
            pass
        elif self.exectype == self.Close:  # is it ireally needed for Close?
            pass
        elif self.exectype == self.Limit:
            self.m_lmtPrice = self.price
        elif self.exectype == self.Stop:
            self.m_auxPrice = self.price  # stop price / exec is market
        elif self.exectype == self.StopLimit:
            self.m_lmtPrice = self.pricelimit  # req limit execution
            self.m_auxPrice = self.price  # trigger price
        elif self.exectype == self.StopTrail:
            if self.trailamount is not None:
                self.m_auxPrice = self.trailamount
            elif self.trailpercent is not None:
                # value expected in % format ... multiply 100.0
                self.m_trailingPercent = self.trailpercent * 100.0
        elif self.exectype == self.StopTrailLimit:
            self.m_trailStopPrice = self.m_lmtPrice = self.price
            # The limit offset is set relative to the price difference in TWS
            self.m_lmtPrice = self.pricelimit
            if self.trailamount is not None:
                self.m_auxPrice = self.trailamount
            elif self.trailpercent is not None:
                # value expected in % format ... multiply 100.0
                self.m_trailingPercent = self.trailpercent * 100.0

        self.m_totalQuantity = abs(self.size)  # ib takes only positives

        self.m_transmit = self.transmit
        if self.parent is not None:
            self.m_parentId = self.parent.m_orderId

        # Time In Force: DAY, GTC, IOC, GTD
        if self.valid is None:
            tif = 'GTC'  # Good til cancelled
        elif isinstance(self.valid, (datetime, date)):
            tif = 'GTD'  # Good til date
            self.m_goodTillDate = bytes(self.valid.strftime('%Y%m%d %H:%M:%S'))
        elif isinstance(self.valid, (timedelta,)):
            if self.valid == self.DAY:
                tif = 'DAY'
            else:
                tif = 'GTD'  # Good til date
                valid = datetime.now() + self.valid  # .now, using localtime
                self.m_goodTillDate = bytes(valid.strftime('%Y%m%d %H:%M:%S'))

        elif self.valid == 0:
            tif = 'DAY'
        else:
            tif = 'GTD'  # Good til date
            valid = num2date(self.valid)
            self.m_goodTillDate = bytes(valid.strftime('%Y%m%d %H:%M:%S'))

        self.m_tif = bytes(tif)

        # OCA
        self.m_ocaType = 1  # Cancel all remaining orders with block

        # pass any custom arguments to the order
        for k in kwargs:
            setattr(self, (not hasattr(self, k)) * 'm_' + k, kwargs[k])


# =============================================================================
# IBCommInfo 클래스 - IB 수수료 정보 처리
# =============================================================================
# 이 클래스는 IB에서 계산되는 수수료 정보를 처리합니다.
# IB에서 수수료는 자동으로 계산되지만, Strategy의 거래 계산은
# 주문에 CommInfo 객체가 첨부되어 운영 비용과 가치를 계산해야 합니다.
class IBCommInfo(CommInfoBase):
    '''
    Commissions are calculated by ib, but the trades calculations in the
    ```Strategy`` rely on the order carrying a CommInfo object attached for the
    calculation of the operation cost and value.

    These are non-critical informations, but removing them from the trade could
    break existing usage and it is better to provide a CommInfo objet which
    enables those calculations even if with approvimate values.

    The margin calculation is not a known in advance information with IB
    (margin impact can be gotten from OrderState objects) and therefore it is
    left as future exercise to get it'''

    def getvaluesize(self, size, price):
        # =============================================================================
        # 포지션 가치 크기 계산
        # =============================================================================
        # In real life the margin approaches the price
        # 실제로는 마진이 가격에 근사함
        return abs(size) * price

    def getoperationcost(self, size, price):
        # =============================================================================
        # 거래 운영 비용 계산
        # =============================================================================
        '''Returns the needed amount of cash an operation would cost'''
        # Same reasoning as above
        # 위와 같은 논리
        return abs(size) * price


# =============================================================================
# MetaIBBroker 클래스 - IB 브로커 메타클래스
# =============================================================================
# 이 메타클래스는 IBBroker 클래스가 생성될 때 IBStore에 자동으로 등록합니다.
class MetaIBBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        # =============================================================================
        # 클래스 생성 후 IBStore에 브로커 클래스 등록
        # =============================================================================
        '''Class has already been created ... register'''
        # Initialize the class
        # 클래스 초기화
        super(MetaIBBroker, cls).__init__(name, bases, dct)
        ibstore.IBStore.BrokerCls = cls


# =============================================================================
# IBBroker 클래스 - Interactive Brokers 브로커 구현
# =============================================================================
# 이 클래스는 Interactive Brokers의 주문/포지션을 Backtrader의 내부 API로 매핑합니다.
# IB와의 실시간 연결을 통해 주문 실행, 포지션 관리, 계좌 정보 동기화를 수행합니다.
class IBBroker(with_metaclass(MetaIBBroker, BrokerBase)):
    '''Broker implementation for Interactive Brokers.

    This class maps the orders/positions from Interactive Brokers to the
    internal API of ``backtrader``.

    Notes:

      - ``tradeid`` is not really supported, because the profit and loss are
        taken directly from IB. Because (as expected) calculates it in FIFO
        manner, the pnl is not accurate for the tradeid.

      - Position

        If there is an open position for an asset at the beginning of
        operaitons or orders given by other means change a position, the trades
        calculated in the ``Strategy`` in cerebro will not reflect the reality.

        To avoid this, this broker would have to do its own position
        management which would also allow tradeid with multiple ids (profit and
        loss would also be calculated locally), but could be considered to be
        defeating the purpose of working with a live broker
    '''
    # =============================================================================
    # 브로커 파라미터 설정
    # =============================================================================
    params = ()

    def __init__(self, **kwargs):
        # =============================================================================
        # IBBroker 초기화
        # =============================================================================
        super(IBBroker, self).__init__()

        # =============================================================================
        # IBStore 인스턴스 생성 및 연결
        # =============================================================================
        self.ib = ibstore.IBStore(**kwargs)

        # =============================================================================
        # 초기 현금 및 가치 설정
        # =============================================================================
        self.startingcash = self.cash = 0.0      # 시작 현금 및 현재 현금
        self.startingvalue = self.value = 0.0    # 시작 가치 및 현재 가치

        # =============================================================================
        # 주문 관리 컨테이너 초기화
        # =============================================================================
        self._lock_orders = threading.Lock()     # control access (접근 제어)
        self.orderbyid = dict()                  # orders by order id (주문 ID별 주문)
        self.executions = dict()                 # notified executions (알림된 실행)
        self.ordstatus = collections.defaultdict(dict)  # 주문 상태
        self.notifs = queue.Queue()              # holds orders which are notified (알림될 주문 보관)
        self.tonotify = collections.deque()      # hold oids to be notified (알림될 주문 ID 보관)

    def start(self):
        # =============================================================================
        # 브로커 시작 및 IB 연결 초기화
        # =============================================================================
        super(IBBroker, self).start()
        self.ib.start(broker=self)

        if self.ib.connected():
            # =============================================================================
            # IB 연결 성공 시 계좌 정보 요청 및 초기화
            # =============================================================================
            self.ib.reqAccountUpdates()
            self.startingcash = self.cash = self.ib.get_acc_cash()
            self.startingvalue = self.value = self.ib.get_acc_value()
        else:
            # =============================================================================
            # IB 연결 실패 시 기본값으로 초기화
            # =============================================================================
            self.startingcash = self.cash = 0.0
            self.startingvalue = self.value = 0.0

    def stop(self):
        # =============================================================================
        # 브로커 종료 및 IB 연결 해제
        # =============================================================================
        super(IBBroker, self).stop()
        self.ib.stop()

    def getcash(self):
        # =============================================================================
        # 현재 현금 잔고 조회
        # =============================================================================
        # This call cannot block if no answer is available from ib
        # IB에서 응답이 없을 경우 이 호출은 블록되지 않음
        self.cash = self.ib.get_acc_cash()
        return self.cash

    def getvalue(self, datas=None):
        # =============================================================================
        # 현재 계좌 총 가치 조회
        # =============================================================================
        self.value = self.ib.get_acc_value()
        return self.value

    def getposition(self, data, clone=True):
        # =============================================================================
        # 특정 자산의 포지션 정보 조회
        # =============================================================================
        return self.ib.getposition(data.tradecontract, clone=clone)

    def cancel(self, order):
        # =============================================================================
        # 주문 취소 처리
        # =============================================================================
        try:
            o = self.orderbyid[order.m_orderId]
        except (ValueError, KeyError):
            return  # not found ... not cancellable (찾을 수 없음 ... 취소 불가)

        if order.status == Order.Cancelled:  # already cancelled (이미 취소됨)
            return

        self.ib.cancelOrder(order.m_orderId)

    def orderstatus(self, order):
        # =============================================================================
        # 주문 상태 조회
        # =============================================================================
        try:
            o = self.orderbyid[order.m_orderId]
        except (ValueError, KeyError):
            o = order

        return o.status

    def submit(self, order):
        # =============================================================================
        # 주문 제출 처리
        # =============================================================================
        order.submit(self)

        # =============================================================================
        # OCO(One-Cancels-Other) 그룹 설정
        # =============================================================================
        # ocoize if needed
        # 필요시 OCO 처리
        if order.oco is None:  # Generate a UniqueId (고유 ID 생성)
            order.m_ocaGroup = bytes(uuid.uuid4())
        else:
            order.m_ocaGroup = self.orderbyid[order.oco.m_orderId].m_ocaGroup

        # =============================================================================
        # 주문 등록 및 IB에 전송
        # =============================================================================
        self.orderbyid[order.m_orderId] = order
        self.ib.placeOrder(order.m_orderId, order.data.tradecontract, order)
        self.notify(order)

        return order

    def getcommissioninfo(self, data):
        # =============================================================================
        # 수수료 정보 객체 생성
        # =============================================================================
        contract = data.tradecontract
        try:
            mult = float(contract.m_multiplier)
        except (ValueError, TypeError):
            mult = 1.0

        stocklike = contract.m_secType not in ('FUT', 'OPT', 'FOP',)

        return IBCommInfo(mult=mult, stocklike=stocklike)

    def _makeorder(self, action, owner, data,
                   size, price=None, plimit=None,
                   exectype=None, valid=None,
                   tradeid=0, **kwargs):
        # =============================================================================
        # IB 주문 객체 생성
        # =============================================================================
        order = IBOrder(action, owner=owner, data=data,
                        size=size, price=price, pricelimit=plimit,
                        exectype=exectype, valid=valid,
                        tradeid=tradeid,
                        m_clientId=self.ib.clientId,
                        m_orderId=self.ib.nextOrderId(),
                        **kwargs)

        order.addcomminfo(self.getcommissioninfo(data))
        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):
        # =============================================================================
        # 매수 주문 생성 및 제출
        # =============================================================================
        order = self._makeorder(
            'BUY',
            owner, data, size, price, plimit, exectype, valid, tradeid,
            **kwargs)

        return self.submit(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):
        # =============================================================================
        # 매도 주문 생성 및 제출
        # =============================================================================
        order = self._makeorder(
            'SELL',
            owner, data, size, price, plimit, exectype, valid, tradeid,
            **kwargs)

        return self.submit(order)

    def notify(self, order):
        # =============================================================================
        # 주문 알림 큐에 추가
        # =============================================================================
        self.notifs.put(order.clone())

    def get_notification(self):
        # =============================================================================
        # 주문 알림 큐에서 알림 가져오기
        # =============================================================================
        try:
            return self.notifs.get(False)
        except queue.Empty:
            pass

        return None

    def next(self):
        # =============================================================================
        # 알림 경계 표시
        # =============================================================================
        self.notifs.put(None)  # mark notificatino boundary (알림 경계 표시)

    # =============================================================================
    # IB 주문 상태 상수 정의
    # =============================================================================
    # Order statuses in msg
    # 메시지의 주문 상태들
    (SUBMITTED, FILLED, CANCELLED, INACTIVE,
     PENDINGSUBMIT, PENDINGCANCEL, PRESUBMITTED) = (
        'Submitted', 'Filled', 'Cancelled', 'Inactive',
         'PendingSubmit', 'PendingCancel', 'PreSubmitted',)

    def push_orderstatus(self, msg):
        # =============================================================================
        # IB에서 받은 주문 상태 메시지 처리
        # =============================================================================
        # Cancelled and Submitted with Filled = 0 can be pushed immediately
        # 취소됨과 체결량 0인 제출됨은 즉시 푸시 가능
        try:
            order = self.orderbyid[msg.orderId]
        except KeyError:
            return  # not found, it was not an order (찾을 수 없음, 주문이 아님)

        if msg.status == self.SUBMITTED and msg.filled == 0:
            # =============================================================================
            # 주문 제출 완료 처리
            # =============================================================================
            if order.status == order.Accepted:  # duplicate detection (중복 감지)
                return

            order.accept(self)
            self.notify(order)

        elif msg.status == self.CANCELLED:
            # =============================================================================
            # 주문 취소 처리
            # =============================================================================
            # duplicate detection
            # 중복 감지
            if order.status in [order.Cancelled, order.Expired]:
                return

            if order._willexpire:
                # =============================================================================
                # PendingCancel/Cancelled 상태의 openOrder가 확인되었고
                # 이는 주문이 만료될 때 발생함
                # =============================================================================
                # An openOrder has been seen with PendingCancel/Cancelled
                # and this happens when an order expires
                order.expire()
            else:
                # =============================================================================
                # 순수한 사용자 취소는 openOrder 없이 발생
                # =============================================================================
                # Pure user cancellation happens without an openOrder
                order.cancel()
            self.notify(order)

        elif msg.status == self.PENDINGCANCEL:
            # =============================================================================
            # 취소 대기 상태 처리
            # =============================================================================
            # In theory this message should not be seen according to the docs,
            # but other messages like PENDINGSUBMIT which are similarly
            # described in the docs have been received in the demo
            # 이론적으로 이 메시지는 문서에 따르면 보이지 않아야 하지만,
            # 문서에서 유사하게 설명된 PENDINGSUBMIT 같은 다른 메시지들이
            # 데모에서 수신되었음
            if order.status == order.Cancelled:  # duplicate detection (중복 감지)
                return

            # =============================================================================
            # CANCELLED 상태의 orderStatus가 보이지 않으면 202 오류 코드로 처리되므로
            # 여기서는 아무것도 하지 않음
            # =============================================================================
            # We do nothing because the situation is handled with the 202 error
            # code if no orderStatus with CANCELLED is seen
            # order.cancel()
            # self.notify(order)

        elif msg.status == self.INACTIVE:
            # =============================================================================
            # 비활성 상태 처리 (일반적으로 주문 거부)
            # =============================================================================
            # This is a tricky one, because the instances seen have led to
            # order rejection in the demo, but according to the docs there may
            # be a number of reasons and it seems like it could be reactivated
            # 이것은 까다로운 경우인데, 데모에서 본 인스턴스들은 주문 거부로 이어졌지만,
            # 문서에 따르면 여러 이유가 있을 수 있고 재활성화될 수 있는 것 같음
            if order.status == order.Rejected:  # duplicate detection (중복 감지)
                return

            order.reject(self)
            self.notify(order)

        elif msg.status in [self.SUBMITTED, self.FILLED]:
            # =============================================================================
            # 제출됨/체결됨 상태는 실행 세부사항과 수수료가 모두 준비될 때까지 보관
            # 수수료가 마지막에 도착함
            # =============================================================================
            # These two are kept inside the order until execdetails and
            # commission are all in place - commission is the last to come
            self.ordstatus[msg.orderId][msg.filled] = msg

        elif msg.status in [self.PENDINGSUBMIT, self.PRESUBMITTED]:
            # =============================================================================
            # 제출 대기/사전 제출 상태 처리
            # =============================================================================
            # According to the docs, these statuses can only be set by the
            # programmer but the demo account sent it back at random times with
            # "filled"
            # 문서에 따르면 이러한 상태는 프로그래머만 설정할 수 있지만
            # 데모 계정에서 "filled"와 함께 무작위로 다시 보냄
            if msg.filled:
                self.ordstatus[msg.orderId][msg.filled] = msg
        else:  # Unknown status ... (알 수 없는 상태...)
            pass

    def push_execution(self, ex):
        # =============================================================================
        # 주문 실행 정보 저장
        # =============================================================================
        self.executions[ex.m_execId] = ex

    def push_commissionreport(self, cr):
        # =============================================================================
        # 수수료 보고서 처리 및 주문 실행 완료
        # =============================================================================
        with self._lock_orders:
            ex = self.executions.pop(cr.m_execId)
            oid = ex.m_orderId
            order = self.orderbyid[oid]
            ostatus = self.ordstatus[oid].pop(ex.m_cumQty)

            position = self.getposition(order.data, clone=False)
            pprice_orig = position.price
            size = ex.m_shares if ex.m_side[0] == 'B' else -ex.m_shares
            price = ex.m_price
            # use pseudoupdate and let the updateportfolio do the real update?
            psize, pprice, opened, closed = position.update(size, price)

            # split commission between closed and opened
            comm = cr.m_commission
            closedcomm = comm * closed / size
            openedcomm = comm - closedcomm

            comminfo = order.comminfo
            closedvalue = comminfo.getoperationcost(closed, pprice_orig)
            openedvalue = comminfo.getoperationcost(opened, price)

            # default in m_pnl is MAXFLOAT
            pnl = cr.m_realizedPNL if closed else 0.0

            # The internal broker calc should yield the same result
            # pnl = comminfo.profitandloss(-closed, pprice_orig, price)

            # Use the actual time provided by the execution object
            # The report from TWS is in actual local time, not the data's tz
            dt = date2num(datetime.strptime(ex.m_time, '%Y%m%d  %H:%M:%S'))

            # Need to simulate a margin, but it plays no role, because it is
            # controlled by a real broker. Let's set the price of the item
            margin = order.data.close[0]

            order.execute(dt, size, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          margin, pnl,
                          psize, pprice)

            if ostatus.status == self.FILLED:
                order.completed()
                self.ordstatus.pop(oid)  # nothing left to be reported
            else:
                order.partial()

            if oid not in self.tonotify:  # Lock needed
                self.tonotify.append(oid)

    def push_portupdate(self):
        # =============================================================================
        # 포트폴리오 업데이트 처리
        # =============================================================================
        # If the IBStore receives a Portfolio update, then this method will be
        # indicated. If the execution of an order is split in serveral lots,
        # updatePortfolio messages will be intermixed, which is used as a
        # signal to indicate that the strategy can be notified
        # IBStore가 포트폴리오 업데이트를 받으면 이 메서드가 호출됩니다.
        # 주문 실행이 여러 로트로 분할되면 updatePortfolio 메시지가 섞여서 오며,
        # 이는 전략에 알림할 수 있다는 신호로 사용됩니다.
        with self._lock_orders:
            while self.tonotify:
                oid = self.tonotify.popleft()
                order = self.orderbyid[oid]
                self.notify(order)

    def push_ordererror(self, msg):
        # =============================================================================
        # 주문 오류 메시지 처리
        # =============================================================================
        with self._lock_orders:
            try:
                order = self.orderbyid[msg.id]
            except (KeyError, AttributeError):
                return  # no order or no id in error (주문이 없거나 오류에 ID가 없음)

            if msg.errorCode == 202:
                # =============================================================================
                # 오류 코드 202: 주문 취소 관련
                # =============================================================================
                if not order.alive():
                    return
                order.cancel()

            elif msg.errorCode == 201:  # rejected (거부됨)
                # =============================================================================
                # 오류 코드 201: 주문 거부
                # =============================================================================
                if order.status == order.Rejected:
                    return
                order.reject()

            else:
                # =============================================================================
                # 기타 모든 경우에 대한 기본 처리: 주문 거부
                # =============================================================================
                order.reject()  # default for all other cases (다른 모든 경우의 기본값)

            self.notify(order)

    def push_orderstate(self, msg):
        # =============================================================================
        # 주문 상태 메시지 처리
        # =============================================================================
        with self._lock_orders:
            try:
                order = self.orderbyid[msg.orderId]
            except (KeyError, AttributeError):
                return  # no order or no id in error (주문이 없거나 오류에 ID가 없음)

            if msg.orderState.m_status in ['PendingCancel', 'Cancelled',
                                           'Canceled']:
                # =============================================================================
                # 취소 관련 상태 - 주문 만료 가능성 표시
                # =============================================================================
                # This is most likely due to an expiration]
                # 이는 만료로 인한 것일 가능성이 높음
                order._willexpire = True
