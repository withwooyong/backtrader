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
# Visual Chart (VC) 브로커 연동 모듈
# =============================================================================
# 이 모듈은 Backtrader와 Visual Chart 플랫폼을 연동하여
# 실시간 거래 및 백테스팅을 지원합니다.
# 
# 주요 기능:
# - Visual Chart ComTrader와의 COM 인터페이스 연동
# - 다중 계좌 동시 지원
# - 실시간 주문 실행 및 상태 추적
# - 포지션 정보 실시간 동기화
# - 계좌 잔고 및 거래 내역 조회
# 
# 필수 의존성:
# - Visual Chart ComTrader 설치 및 실행
# - Windows COM 인터페이스 지원
# - 적절한 계좌 권한 설정
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
from datetime import date, datetime, timedelta
import threading

from backtrader import BrokerBase, Order, BuyOrder, SellOrder
from backtrader.comminfo import CommInfoBase
from backtrader.feed import DataBase
from backtrader.metabase import MetaParams
from backtrader.position import Position
from backtrader.utils.py3 import with_metaclass

from backtrader.stores import vcstore


# =============================================================================
# VCCommInfo 클래스 - Visual Chart 수수료 정보
# =============================================================================
# 이 클래스는 Visual Chart에서 수수료 계산을 담당합니다.
# 실제 수수료는 IB에서 계산되지만, 전략의 거래 계산을 위해
# CommInfo 객체가 필요합니다.
class VCCommInfo(CommInfoBase):
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
        # 거래 가치 계산 (실제로는 마진이 가격에 근접함)
        # =============================================================================
        # In real life the margin approaches the price
        return abs(size) * price

    def getoperationcost(self, size, price):
        # =============================================================================
        # 거래 비용 계산 (거래에 필요한 현금 금액 반환)
        # =============================================================================
        '''Returns the needed amount of cash an operation would cost'''
        # Same reasoning as above
        # 위와 동일한 논리
        return abs(size) * price


# =============================================================================
# MetaVCBroker 클래스 - Visual Chart 브로커 메타클래스
# =============================================================================
# 이 클래스는 Visual Chart 스토어에 브로커 클래스를 등록하는 역할을 합니다.
class MetaVCBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        # =============================================================================
        # 클래스가 이미 생성되었으므로 등록
        # =============================================================================
        '''Class has already been created ... register'''
        # Initialize the class
        # 클래스 초기화
        super(MetaVCBroker, cls).__init__(name, bases, dct)
        vcstore.VCStore.BrokerCls = cls


# =============================================================================
# VCBroker 클래스 - Visual Chart 브로커 구현
# =============================================================================
# 이 클래스는 Visual Chart의 주문/포지션을 Backtrader의 내부 API에 매핑합니다.
class VCBroker(with_metaclass(MetaVCBroker, BrokerBase)):
    '''Broker implementation for VisualChart.

    This class maps the orders/positions from VisualChart to the
    internal API of ``backtrader``.

    Params:

      - ``account`` (default: None)

        VisualChart supports several accounts simultaneously on the broker. If
        the default ``None`` is in place the 1st account in the ComTrader
        ``Accounts`` collection will be used.

        If an account name is provided, the ``Accounts`` collection will be
        checked and used if present

      - ``commission`` (default: None)

        An object will be autogenerated if no commission-scheme is passed as
        parameter

        See the notes below for further explanations

    Notes:

      - Position

        VisualChart reports "OpenPositions" updates through the ComTrader
        interface but only when the position has a "size". An update to
        indicate a position has moved to ZERO is reported by the absence of
        such position. This forces to keep accounting of the positions by
        looking at the execution events, just like the simulation broker does

      - Commission

        The ComTrader interface of VisualChart does not report commissions and
        as such the auto-generated CommissionInfo object cannot use
        non-existent commissions to properly account for them. In order to
        support commissions a ``commission`` parameter has to be passed with
        the appropriate commission schemes.

        The documentation on Commission Schemes details how to do this

      - Expiration Timing

        The ComTrader interface (or is it the comtypes module?) discards
        ``time`` information from ``datetime`` objects and expiration dates are
        always full dates.

      - Expiration Reporting

        At the moment no heuristic is in place to determine when a cancelled
        order has been cancelled due to expiration. And therefore expired
        orders are reported as cancelled.
    '''
    params = (
        ('account', None),
        ('commission', None),
    )

    def __init__(self, **kwargs):
        # =============================================================================
        # VCBroker 초기화
        # =============================================================================
        super(VCBroker, self).__init__()

        # =============================================================================
        # Visual Chart 스토어 연결
        # =============================================================================
        self.store = vcstore.VCStore(**kwargs)

        # =============================================================================
        # 계좌 데이터 초기화
        # =============================================================================
        # Account data
        # 계좌 데이터
        self._acc_name = None
        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0

        # =============================================================================
        # 포지션 관리 초기화
        # =============================================================================
        # Position accounting
        # 포지션 계정 관리
        self._lock_pos = threading.Lock()  # sync account updates (계좌 업데이트 동기화)
        self.positions = collections.defaultdict(Position)  # actual positions (실제 포지션들)

        # =============================================================================
        # 주문 저장소 초기화
        # =============================================================================
        # Order storage
        # 주문 저장소
        self._lock_orders = threading.Lock()  # control access (접근 제어)
        self.orderbyid = dict()  # orders by order id (주문 ID별 주문)

        # =============================================================================
        # 알림 시스템 초기화
        # =============================================================================
        # Notifications
        # 알림
        self.notifs = collections.deque()

        # =============================================================================
        # 주문 매핑을 위한 값들
        # =============================================================================
        # Dictionaries of values for order mapping
        # 주문 매핑을 위한 값들의 딕셔너리
        
        # =============================================================================
        # 주문 타입 매핑 (Backtrader → Visual Chart)
        # =============================================================================
        self._otypes = {
            Order.Market: self.store.vcctmod.OT_Market,      # 시장가 주문
            Order.Close: self.store.vcctmod.OT_Market,       # 종가 주문
            Order.Limit: self.store.vcctmod.OT_Limit,        # 지정가 주문
            Order.Stop: self.store.vcctmod.OT_StopMarket,    # 스탑 시장가 주문
            Order.StopLimit: self.store.vcctmod.OT_StopLimit, # 스탑 지정가 주문
        }

        # =============================================================================
        # 주문 방향 매핑 (Backtrader → Visual Chart)
        # =============================================================================
        self._osides = {
            Order.Buy: self.store.vcctmod.OS_Buy,   # 매수
            Order.Sell: self.store.vcctmod.OS_Sell, # 매도
        }

        # =============================================================================
        # 시간 제한 매핑 (Backtrader → Visual Chart)
        # =============================================================================
        self._otrestriction = {
            Order.T_None: self.store.vcctmod.TR_NoRestriction,    # 제한 없음
            Order.T_Date: self.store.vcctmod.TR_Date,             # 특정 날짜까지
            Order.T_Close: self.store.vcctmod.TR_CloseAuction,    # 종가 경매까지
            Order.T_Day: self.store.vcctmod.TR_Session,           # 세션까지
        }

        # =============================================================================
        # 거래량 제한 매핑 (Backtra더 → Visual Chart)
        # =============================================================================
        self._ovrestriction = {
            Order.V_None: self.store.vcctmod.VR_NoRestriction,   # 제한 없음
        }

        # =============================================================================
        # 선물류 상품 타입들 (수수료 계산용)
        # =============================================================================
        self._futlikes = (
            self.store.vcdsmod.IT_Future, self.store.vcdsmod.IT_Option,
            self.store.vcdsmod.IT_Fund,
        )

    def start(self):
        # =============================================================================
        # 브로커 시작 및 Visual Chart 스토어 시작
        # =============================================================================
        super(VCBroker, self).start()
        self.store.start(broker=self)

    def stop(self):
        # =============================================================================
        # 브로커 종료 및 Visual Chart 스토어 종료
        # =============================================================================
        super(VCBroker, self).stop()
        self.store.stop()

    def getcash(self):
        # =============================================================================
        # 현재 현금 잔고 조회
        # =============================================================================
        # This call cannot block if no answer is available from ib
        # IB에서 응답이 없을 경우 이 호출은 블록되지 않음
        return self.cash

    def getvalue(self, datas=None):
        # =============================================================================
        # 현재 계좌 총 가치 조회
        # =============================================================================
        return self.value

    def get_notification(self):
        # =============================================================================
        # 주문 알림 큐에서 알림 가져오기
        # =============================================================================
        return self.notifs.popleft()  # at leat a None is present (최소한 None은 존재함)

    def notify(self, order):
        # =============================================================================
        # 주문 알림 큐에 추가
        # =============================================================================
        self.notifs.append(order.clone())

    def next(self):
        # =============================================================================
        # 알림 경계 표시
        # =============================================================================
        self.notifs.append(None)  # mark notificatino boundary (알림 경계 표시)

    def getposition(self, data, clone=True):
        # =============================================================================
        # 특정 자산의 포지션 정보 조회
        # =============================================================================
        with self._lock_pos:
            pos = self.positions[data._tradename]
            if clone:
                return pos.clone()

        return pos

    def getcommissioninfo(self, data):
        # =============================================================================
        # 수수료 정보 객체 생성
        # =============================================================================
        if data._tradename in self.comminfo:
            return self.comminfo[data._tradename]

        comminfo = self.comminfo[None]
        if comminfo is not None:
            return comminfo

        stocklike = data._syminfo.Type in self._futlikes

        return VCCommInfo(mult=data._syminfo.PointValue, stocklike=stocklike)

    def _makeorder(self, ordtype, owner, data,
                   size, price=None, plimit=None,
                   exectype=None, valid=None,
                   tradeid=0, **kwargs):
        # =============================================================================
        # Visual Chart 주문 객체 생성
        # =============================================================================
        order = self.store.vcctmod.Order()
        order.Account = self._acc_name
        order.SymbolCode = data._tradename
        order.OrderType = self._otypes[exectype]
        order.OrderSide = self._osides[ordtype]

        # =============================================================================
        # 거래량 제한 설정
        # =============================================================================
        order.VolumeRestriction = self._ovrestriction[Order.V_None]
        order.HideVolume = 0
        order.MinVolume = 0

        # =============================================================================
        # 사용자 주문 ID 및 확장 정보 설정
        # =============================================================================
        # order.UserName = 'danjrod'  # str(tradeid)
        # order.OrderId = 'a' * 50  # str(tradeid)
        order.UserOrderId = ''
        if tradeid:
            order.ExtendedInfo = 'TradeId {}'.format(tradeid)
        else:
            order.ExtendedInfo = ''

        order.Volume = abs(size)

        # =============================================================================
        # 가격 설정 (주문 타입에 따라)
        # =============================================================================
        order.StopPrice = 0.0
        order.Price = 0.0
        if exectype == Order.Market:
            pass
        elif exectype == Order.Limit:
            order.Price = price or plimit  # cover naming confusion cases (명명 혼동 케이스 커버)
        elif exectype == Order.Close:
            pass
        elif exectype == Order.Stop:
            order.StopPrice = price
        elif exectype == Order.StopLimit:
            order.StopPrice = price
            order.Price = plimit

        # =============================================================================
        # 유효 기간 설정
        # =============================================================================
        order.ValidDate = None
        if exectype == Order.Close:
            order.TimeRestriction = self._otrestriction[Order.T_Close]
        else:
            if valid is None:
                order.TimeRestriction = self._otrestriction[Order.T_None]
            elif isinstance(valid, (datetime, date)):
                order.TimeRestriction = self._otrestriction[Order.T_Date]
                order.ValidDate = valid
            elif isinstance(valid, (timedelta,)):
                if valid == Order.DAY:
                    order.TimeRestriction = self._otrestriction[Order.T_Day]
                else:
                    order.TimeRestriction = self._otrestriction[Order.T_Date]
                    order.ValidDate = datetime.now() + valid

            elif not self.valid:  # DAY
                order.TimeRestriction = self._otrestriction[Order.T_Day]

        # =============================================================================
        # 사용자 정의 인수 지원
        # =============================================================================
        # Support for custom user arguments
        # 사용자 정의 인수 지원
        for k in kwargs:
            if hasattr(order, k):
                setattr(order, k, kwargs[k])

        return order

    def submit(self, order, vcorder):
        # =============================================================================
        # 주문 제출 및 Visual Chart로 전송
        # =============================================================================
        order.submit(self)

        vco = vcorder
        oid = self.store.vcct.SendOrder(
            vco.Account, vco.SymbolCode,
            vco.OrderType, vco.OrderSide, vco.Volume, vco.Price, vco.StopPrice,
            vco.VolumeRestriction, vco.TimeRestriction,
            ValidDate=vco.ValidDate
        )

        # =============================================================================
        # 주문 정보 설정 및 저장
        # =============================================================================
        order.vcorder = oid
        order.addcomminfo(self.getcommissioninfo(order.data))

        with self._lock_orders:
            self.orderbyid[oid] = order
        self.notify(order)
        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):
        # =============================================================================
        # 매수 주문 생성 및 제출
        # =============================================================================
        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)

        vcorder = self._makeorder(order.ordtype, owner, data, size, price,
                                  plimit, exectype, valid, tradeid,
                                  **kwargs)

        return self.submit(order, vcorder)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):
        # =============================================================================
        # 매도 주문 생성 및 제출
        # =============================================================================
        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)

        vcorder = self._makeorder(order.ordtype, owner, data, size, price,
                                  plimit, exectype, valid, tradeid,
                                  **kwargs)

        return self.submit(order, vcorder)

    # =============================================================================
    # COM 이벤트 구현
    # =============================================================================
    #
    # COM Events implementation
    # COM 이벤트 구현
    #
    def __call__(self, trader):
        # =============================================================================
        # 프로세스 시작 시 호출, 하위 스레드에서 호출됨
        # 전달된 trader만 해당 스레드에서 사용 가능
        # =============================================================================
        # Called to start the process, call in sub-thread. only the passed
        # trader can be used in the thread
        # 프로세스 시작을 위해 호출됨, 하위 스레드에서 호출. 전달된 trader만
        # 해당 스레드에서 사용 가능
        self.trader = trader

        # =============================================================================
        # 계좌 정보 설정 (첫 번째 계좌 또는 지정된 계좌)
        # =============================================================================
        for acc in trader.Accounts:
            if self.p.account is None or self.p.account == acc.Account:
                self.startingcash = self.cash = acc.Balance.Cash
                self.startingvalue = self.value = acc.Balance.NetWorth
                self._acc_name = acc.Account
                break  # found the account (계좌를 찾음)

        return self

    def OnChangedBalance(self, Account):
        # =============================================================================
        # 계좌 잔고 변경 이벤트 처리
        # =============================================================================
        if self._acc_name is None or self._acc_name != Account:
            return  # skip notifs for other accounts (다른 계좌의 알림 건너뛰기)

        for acc in self.trader.Accounts:
            if acc.Account == Account:
                # Update store values
                # 스토어 값 업데이트
                self.cash = acc.Balance.Cash
                self.value = acc.Balance.NetWorth
                break

    def OnModifiedOrder(self, Order):
        # =============================================================================
        # 주문 수정 이벤트 처리 (현재 미구현)
        # =============================================================================
        # We are not expecting this: unless backtrader starts implementing
        # modify order method
        # 이것을 기대하지 않음: backtrader가 주문 수정 메서드를 구현하기 시작하지 않는 한
        pass

    def OnCancelledOrder(self, Order):
        # =============================================================================
        # 주문 취소 이벤트 처리
        # =============================================================================
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # possibly external order (외부 주문일 가능성)

        border.cancel()
        self.notify(border)

    def OnTotalExecutedOrder(self, Order):
        # =============================================================================
        # 주문 완전 체결 이벤트 처리
        # =============================================================================
        self.OnExecutedOrder(Order, partial=False)

    def OnPartialExecutedOrder(self, Order):
        # =============================================================================
        # 주문 부분 체결 이벤트 처리
        # =============================================================================
        self.OnExecutedOrder(Order, partial=True)

    def OnExecutedOrder(self, Order, partial):
        # =============================================================================
        # 주문 체결 이벤트 처리 (부분/완전 체결 공통)
        # =============================================================================
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # possibly external order (외부 주문일 가능성)

        # =============================================================================
        # 체결 정보 추출
        # =============================================================================
        price = Order.Price
        size = Order.Volume
        if border.issell():
            size *= -1

        # =============================================================================
        # 포지션 찾기 및 실제 업데이트 - 여기서 계정 관리가 이루어짐
        # =============================================================================
        # Find position and do a real update - accounting happens here
        # 포지션을 찾고 실제 업데이트 수행 - 여기서 계정 관리가 이루어짐
        position = self.getposition(border.data, clone=False)
        pprice_orig = position.price
        psize, pprice, opened, closed = position.update(size, price)

        # =============================================================================
        # 수수료 정보 계산
        # =============================================================================
        comminfo = border.comminfo
        closedvalue = comminfo.getoperationcost(closed, pprice_orig)
        closedcomm = comminfo.getcommission(closed, price)

        openedvalue = comminfo.getoperationcost(opened, price)
        openedcomm = comminfo.getcommission(opened, price)

        pnl = comminfo.profitandloss(-closed, pprice_orig, price)
        margin = comminfo.getvaluesize(size, price)

        # =============================================================================
        # 주문 실행 처리
        # =============================================================================
        # NOTE: No commission information available in the Trader interface
        # CHECK: Use reported time instead of last data time?
        # 참고: Trader 인터페이스에서 수수료 정보를 사용할 수 없음
        # 확인: 마지막 데이터 시간 대신 보고된 시간 사용?
        border.execute(border.data.datetime[0],
                       size, price,
                       closed, closedvalue, closedcomm,
                       opened, openedvalue, openedcomm,
                       margin, pnl,
                       psize, pprice)  # pnl

        if partial:
            border.partial()
        else:
            border.completed()

        self.notify(border)

    def OnOrderInMarket(self, Order):
        # =============================================================================
        # 주문 시장 진입 이벤트 처리 (주문 승인)
        # =============================================================================
        # Other is in ther market ... therefore "accepted"
        # 다른 것이 시장에 있음 ... 따라서 "승인됨"
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # possibly external order (외부 주문일 가능성)

        border.accept()
        self.notify(border)

    def OnNewOrderLocation(self, Order):
        # =============================================================================
        # 새 주문 위치 이벤트 처리 (현재 미사용)
        # =============================================================================
        # Can be used for "submitted", but the status is set manually
        # "제출됨"에 사용할 수 있지만, 상태는 수동으로 설정됨
        pass

    def OnChangedOpenPositions(self, Account):
        # =============================================================================
        # 오픈 포지션 변경 이벤트 처리 (현재 미사용)
        # =============================================================================
        # This would be useful if it reported a position moving back to 0. In
        # this case the report contains a no-position and this doesn't help in
        # the accounting. That's why the accounting is delegated to the
        # reception of order execution
        # 이것은 포지션이 0으로 돌아가는 것을 보고할 때 유용할 것입니다.
        # 이 경우 보고서에는 포지션이 없고 이것은 계정 관리에 도움이 되지 않습니다.
        # 그래서 계정 관리는 주문 실행 수신에 위임됩니다.
        pass

    def OnNewClosedOperations(self, Account):
        # =============================================================================
        # 새 종료된 거래 이벤트 처리 (현재 미사용)
        # =============================================================================
        # This call-back has not been seen
        # 이 콜백은 보이지 않았음
        pass

    def OnServerShutDown(self):
        # =============================================================================
        # 서버 종료 이벤트 처리 (현재 미사용)
        # =============================================================================
        pass

    def OnInternalEvent(self, p1, p2, p3):
        # =============================================================================
        # 내부 이벤트 처리 (현재 미사용)
        # =============================================================================
        pass
