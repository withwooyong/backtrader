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
# OANDA 브로커 연동 모듈
# =============================================================================
# 이 모듈은 Backtrader와 OANDA 플랫폼을 연동하여
# 외환 거래 및 백테스팅을 지원합니다.
# 
# 주요 기능:
# - OANDA REST API를 통한 실시간 연결
# - 외환 거래 전용 기능 (레버리지, 마진 등)
# - 실시간 시세 데이터 수신
# - 포지션 및 계좌 정보 실시간 동기화
# - 브래킷 주문 지원 (OCO, OTO 등)
# 
# 필수 의존성:
# - oandapy 또는 oandapyV20 패키지 설치 필요
# - OANDA 계좌 및 API 키 설정 필요
# - 적절한 거래 권한 설정 필요
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
from copy import copy
from datetime import date, datetime, timedelta
import threading

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, BuyOrder, SellOrder, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, with_metaclass, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import oandastore
from backtrader.utils import AutoDict, AutoOrderedDict
from backtrader.comminfo import CommInfoBase


# =============================================================================
# OandaCommInfo 클래스 - OANDA 수수료 정보
# =============================================================================
# 이 클래스는 OANDA에서 수수료 계산을 담당합니다.
# 외환 거래의 특성상 마진이 가격에 근접하는 구조입니다.
class OandaCommInfo(CommInfoBase):
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
# MetaOandaBroker 클래스 - OANDA 브로커 메타클래스
# =============================================================================
# 이 클래스는 OANDA 스토어에 브로커 클래스를 등록하는 역할을 합니다.
class MetaOandaBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        # =============================================================================
        # 클래스가 이미 생성되었으므로 등록
        # =============================================================================
        '''Class has already been created ... register'''
        # Initialize the class
        # 클래스 초기화
        super(MetaOandaBroker, cls).__init__(name, bases, dct)
        oandastore.OandaStore.BrokerCls = cls


# =============================================================================
# OandaBroker 클래스 - OANDA 브로커 구현
# =============================================================================
# 이 클래스는 OANDA의 주문/포지션을 Backtrader의 내부 API에 매핑합니다.
# 외환 거래의 특성을 반영하여 레버리지와 마진을 지원합니다.
class OandaBroker(with_metaclass(MetaOandaBroker, BrokerBase)):
    '''Broker implementation for Oanda.

    This class maps the orders/positions from Oanda to the
    internal API of ``backtrader``.

    Params:

      - ``use_positions`` (default:``True``): When connecting to the broker
        provider use the existing positions to kickstart the broker.

        Set to ``False`` during instantiation to disregard any existing
        position
    '''
    
    # =============================================================================
    # 브로커 파라미터 설정
    # =============================================================================
    params = (
        ('use_positions', True),  # 기존 포지션 사용 여부 (연결 시 기존 포지션으로 시작)
        ('commission', OandaCommInfo(mult=1.0, stocklike=False)),  # 외환 거래용 수수료 정보
    )

    def __init__(self, **kwargs):
        # =============================================================================
        # OANDA 브로커 초기화
        # =============================================================================
        super(OandaBroker, self).__init__()

        # =============================================================================
        # OANDA 스토어 연결 및 컨테이너 초기화
        # =============================================================================
        self.o = oandastore.OandaStore(**kwargs)

        self.orders = collections.OrderedDict()  # orders by order id (주문 ID별 주문 관리)
        self.notifs = collections.deque()  # holds orders which are notified (알림된 주문들)

        self.opending = collections.defaultdict(list)  # pending transmission (전송 대기 중인 주문들)
        self.brackets = dict()  # confirmed brackets (확인된 브래킷 주문들)

        # =============================================================================
        # 현금 및 가치 초기화
        # =============================================================================
        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0
        self.positions = collections.defaultdict(Position)

    def start(self):
        # =============================================================================
        # 브로커 시작 시 초기화
        # =============================================================================
        super(OandaBroker, self).start()
        self.o.start(broker=self)
        self.startingcash = self.cash = cash = self.o.get_cash()
        self.startingvalue = self.value = self.o.get_value()

        if self.p.use_positions:
            for p in self.o.get_positions():
                print('position for instrument:', p['instrument'])
                is_sell = p['side'] == 'sell'
                size = p['units']
                if is_sell:
                    size = -size
                price = p['avgPrice']
                self.positions[p['instrument']] = Position(size, price)

    def data_started(self, data):
        # =============================================================================
        # 데이터 시작 시 기존 포지션 처리
        # =============================================================================
        pos = self.getposition(data)

        if pos.size < 0:
            # =============================================================================
            # 기존 숏 포지션이 있는 경우 시뮬레이션된 매도 주문 생성
            # =============================================================================
            order = SellOrder(data=data,
                              size=pos.size, price=pos.price,
                              exectype=Order.Market,
                              simulated=True)

            order.addcomminfo(self.getcommissioninfo(data))
            order.execute(0, pos.size, pos.price,
                          0, 0.0, 0.0,
                          pos.size, 0.0, 0.0,
                          0.0, 0.0,
                          pos.size, pos.price)

            order.completed()
            self.notify(order)

        elif pos.size > 0:
            # =============================================================================
            # 기존 롱 포지션이 있는 경우 시뮬레이션된 매수 주문 생성
            # =============================================================================
            order = BuyOrder(data=data,
                             size=pos.size, price=pos.price,
                             exectype=Order.Market,
                             simulated=True)

            order.addcomminfo(self.getcommissioninfo(data))
            order.execute(0, pos.size, pos.price,
                          0, 0.0, 0.0,
                          pos.size, 0.0, 0.0,
                          0.0, 0.0,
                          pos.size, pos.price)

            order.completed()
            self.notify(order)

    def stop(self):
        # =============================================================================
        # 브로커 종료 및 OANDA 연결 해제
        # =============================================================================
        super(OandaBroker, self).stop()
        self.o.stop()

    def getcash(self):
        # =============================================================================
        # 현재 현금 잔고 조회
        # =============================================================================
        # This call cannot block if no answer is available from oanda
        # OANDA에서 응답이 없을 경우 이 호출은 블록되지 않음
        self.cash = cash = self.o.get_cash()
        return cash

    def getvalue(self, datas=None):
        # =============================================================================
        # 현재 계좌 총 가치 조회
        # =============================================================================
        self.value = self.o.get_value()
        return self.value

    def getposition(self, data, clone=True):
        # =============================================================================
        # 특정 자산의 포지션 정보 조회
        # =============================================================================
        # return self.o.getposition(data._dataname, clone=clone)
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()

        return pos

    def orderstatus(self, order):
        # =============================================================================
        # 주문 상태 조회
        # =============================================================================
        o = self.orders[order.ref]
        return o.status

    def _submit(self, oref):
        # =============================================================================
        # 주문 제출 처리 (브래킷 주문 포함)
        # =============================================================================
        order = self.orders[oref]
        order.submit(self)
        self.notify(order)
        for o in self._bracketnotif(order):
            o.submit(self)
            self.notify(o)

    def _reject(self, oref):
        # =============================================================================
        # 주문 거부 처리 (브래킷 주문 취소 포함)
        # =============================================================================
        order = self.orders[oref]
        order.reject(self)
        self.notify(order)
        self._bracketize(order, cancel=True)

    def _accept(self, oref):
        # =============================================================================
        # 주문 승인 처리 (브래킷 주문 포함)
        # =============================================================================
        order = self.orders[oref]
        order.accept()
        self.notify(order)
        for o in self._bracketnotif(order):
            o.accept(self)
            self.notify(o)

    def _cancel(self, oref):
        # =============================================================================
        # 주문 취소 처리 (브래킷 주문 취소 포함)
        # =============================================================================
        order = self.orders[oref]
        order.cancel()
        self.notify(order)
        self._bracketize(order, cancel=True)

    def _expire(self, oref):
        # =============================================================================
        # 주문 만료 처리 (브래킷 주문 취소 포함)
        # =============================================================================
        order = self.orders[oref]
        order.expire()
        self.notify(order)
        self._bracketize(order, cancel=True)

    def _bracketnotif(self, order):
        # =============================================================================
        # 브래킷 주문 알림 대상 반환
        # =============================================================================
        pref = getattr(order.parent, 'ref', order.ref)  # parent ref or self (부모 참조 또는 자기 자신)
        br = self.brackets.get(pref, None)  # to avoid recursion (재귀 방지)
        return br[-2:] if br is not None else []

    def _bracketize(self, order, cancel=False):
        # =============================================================================
        # 브래킷 주문 관리 (스탑로스, 이익실현 주문 처리)
        # =============================================================================
        pref = getattr(order.parent, 'ref', order.ref)  # parent ref or self (부모 참조 또는 자기 자신)
        br = self.brackets.pop(pref, None)  # to avoid recursion (재귀 방지)
        if br is None:
            return

        if not cancel:
            if len(br) == 3:  # all 3 orders in place, parent was filled (3개 주문 모두 준비됨, 부모 주문 체결됨)
                # =============================================================================
                # 부모 주문이 체결되면 자식 주문들(스탑로스, 이익실현) 활성화
                # =============================================================================
                br = br[1:]  # discard index 0, parent (인덱스 0, 부모 주문 제거)
                for o in br:
                    o.activate()  # simulate activate for children (자식 주문들 활성화 시뮬레이션)
                self.brackets[pref] = br  # not done - reinsert children (완료되지 않음 - 자식 주문들 재삽입)

            elif len(br) == 2:  # filling a children (자식 주문 중 하나 체결)
                # =============================================================================
                # 자식 주문 중 하나가 체결되면 나머지 주문 취소 (OCO 처리)
                # =============================================================================
                oidx = br.index(order)  # find index to filled (0 or 1) (체결된 주문의 인덱스 찾기)
                self._cancel(br[1 - oidx].ref)  # cancel remaining (1 - 0 -> 1) (나머지 주문 취소)
        else:
            # =============================================================================
            # 취소 시 모든 관련 주문들 취소
            # =============================================================================
            # Any cancellation cancel the others
            # 어떤 취소든 다른 주문들도 취소
            for o in br:
                if o.alive():
                    self._cancel(o.ref)

    def _fill(self, oref, size, price, ttype, **kwargs):
        # =============================================================================
        # 주문 체결 처리
        # =============================================================================
        order = self.orders[oref]

        if not order.alive():  # can be a bracket (브래킷 주문일 수 있음)
            # =============================================================================
            # 주문이 더 이상 활성화되지 않은 경우 브래킷 주문 확인
            # =============================================================================
            pref = getattr(order.parent, 'ref', order.ref)
            if pref not in self.brackets:
                msg = ('Order fill received for {}, with price {} and size {} '
                       'but order is no longer alive and is not a bracket. '
                       'Unknown situation')
                msg.format(order.ref, price, size)
                self.put_notification(msg, order, price, size)
                return

            # =============================================================================
            # 브래킷 주문 타입에 따른 주문 선택
            # [main, stopside, takeside], 음수 인덱스는 -3, -2, -1
            # =============================================================================
            # [main, stopside, takeside], neg idx to array are -3, -2, -1
            if ttype == 'STOP_LOSS_FILLED':
                order = self.brackets[pref][-2]  # 스탑로스 주문
            elif ttype == 'TAKE_PROFIT_FILLED':
                order = self.brackets[pref][-1]  # 이익실현 주문
            else:
                msg = ('Order fill received for {}, with price {} and size {} '
                       'but order is no longer alive and is a bracket. '
                       'Unknown situation')
                msg.format(order.ref, price, size)
                self.put_notification(msg, order, price, size)
                return

        # =============================================================================
        # 포지션 업데이트 및 체결 정보 계산
        # =============================================================================
        data = order.data
        pos = self.getposition(data, clone=False)
        psize, pprice, opened, closed = pos.update(size, price)

        comminfo = self.getcommissioninfo(data)

        # =============================================================================
        # 체결 관련 비용 및 수익 초기화 (OANDA에서 직접 계산)
        # =============================================================================
        closedvalue = closedcomm = 0.0
        openedvalue = openedcomm = 0.0
        margin = pnl = 0.0

        # =============================================================================
        # 주문 실행 처리
        # =============================================================================
        order.execute(data.datetime[0], size, price,
                      closed, closedvalue, closedcomm,
                      opened, openedvalue, openedcomm,
                      margin, pnl,
                      psize, pprice)

        if order.executed.remsize:
            # =============================================================================
            # 부분 체결인 경우
            # =============================================================================
            order.partial()
            self.notify(order)
        else:
            # =============================================================================
            # 완전 체결인 경우 브래킷 주문 처리
            # =============================================================================
            order.completed()
            self.notify(order)
            self._bracketize(order)

    def _transmit(self, order):
        # =============================================================================
        # 주문 전송 처리 (브래킷 주문 지원)
        # =============================================================================
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)  # parent ref or self (부모 참조 또는 자기 자신)

        if order.transmit:
            if oref != pref:  # children order (자식 주문)
                # =============================================================================
                # 자식 주문인 경우 브래킷 주문 완성 및 전송
                # =============================================================================
                # Put parent in orders dict, but add stopside and takeside
                # to order creation. Return the takeside order, to have 3s
                # 부모를 주문 딕셔너리에 넣고, 스탑사이드와 테이크사이드를
                # 주문 생성에 추가. 3개를 갖기 위해 테이크사이드 주문 반환
                takeside = order  # alias for clarity (명확성을 위한 별칭)
                parent, stopside = self.opending.pop(pref)
                for o in parent, stopside, takeside:
                    self.orders[o.ref] = o  # write them down (기록)

                self.brackets[pref] = [parent, stopside, takeside]
                self.o.order_create(parent, stopside, takeside)
                return takeside  # parent was already returned (부모는 이미 반환됨)

            else:  # Parent order, which is not being transmitted (전송되지 않는 부모 주문)
                # =============================================================================
                # 단일 주문 전송
                # =============================================================================
                self.orders[order.ref] = order
                return self.o.order_create(order)

        # =============================================================================
        # 전송하지 않는 경우 대기 큐에 추가
        # =============================================================================
        # Not transmitting
        # 전송하지 않음
        self.opending[pref].append(order)
        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            **kwargs):
        # =============================================================================
        # 매수 주문 생성 및 전송
        # =============================================================================
        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid,
                         trailamount=trailamount, trailpercent=trailpercent,
                         parent=parent, transmit=transmit)

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        return self._transmit(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             **kwargs):
        # =============================================================================
        # 매도 주문 생성 및 전송
        # =============================================================================
        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid,
                          trailamount=trailamount, trailpercent=trailpercent,
                          parent=parent, transmit=transmit)

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        return self._transmit(order)

    def cancel(self, order):
        # =============================================================================
        # 주문 취소 처리
        # =============================================================================
        o = self.orders[order.ref]
        if order.status == Order.Cancelled:  # already cancelled (이미 취소됨)
            return

        return self.o.order_cancel(order)

    def notify(self, order):
        # =============================================================================
        # 주문 알림 큐에 추가
        # =============================================================================
        self.notifs.append(order.clone())

    def get_notification(self):
        # =============================================================================
        # 주문 알림 큐에서 알림 가져오기
        # =============================================================================
        if not self.notifs:
            return None

        return self.notifs.popleft()

    def next(self):
        # =============================================================================
        # 알림 경계 표시
        # =============================================================================
        self.notifs.append(None)  # mark notification boundary (알림 경계 표시)
