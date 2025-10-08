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
try:
    time_clock = time.process_time  # Python 3.3+ 에서는 process_time 사용
except:
    time_clock = time.clock         # 이전 버전에서는 clock 사용

import testcommon

import backtrader as bt
import backtrader.indicators as btind

# 매수 주문 생성 시 예상 가격들
BUYCREATE = [
    '3641.42', '3798.46', '3874.61', '3860.00', '3843.08', '3648.33',
    '3526.84', '3632.93', '3788.96', '3841.31', '4045.22', '4052.89',
]

# 매도 주문 생성 시 예상 가격들
SELLCREATE = [
    '3763.73', '3811.45', '3823.11', '3821.97', '3837.86', '3604.33',
    '3562.56', '3772.21', '3780.18', '3974.62', '4048.16'
]

# 매수 주문 실행 시 예상 가격들
BUYEXEC = [
    '3643.35', '3801.03', '3872.37', '3863.57', '3845.32', '3656.43',
    '3542.65', '3639.65', '3799.86', '3840.20', '4047.63', '4052.55'
]

# 매도 주문 실행 시 예상 가격들
SELLEXEC = [
    '3763.95', '3811.85', '3822.35', '3822.57', '3829.82', '3598.58',
    '3545.92', '3766.80', '3782.15', '3979.73', '4045.05'
]


class TestStrategy(bt.Strategy):
    """
    비최적화 전략 테스트를 위한 전략 클래스
    
    이 전략은 SMA 크로스오버를 사용하여 매수/매도 신호를 생성합니다.
    최적화 없이 단일 실행으로 테스트됩니다.
    """
    params = (
        ('period', 15),        # SMA 기간 (기본값: 15)
        ('printdata', True),   # 데이터 출력 여부
        ('printops', True),    # 작업 출력 여부
        ('stocklike', True),   # 주식과 유사한 거래 모드 여부
    )

    def log(self, txt, dt=None, nodate=False):
        """로그 메시지를 출력하는 헬퍼 메서드"""
        if not nodate:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))
        else:
            print('---------- %s' % (txt))

    def notify_order(self, order):
        """주문 상태 변경 시 호출되는 알림 메서드"""
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # 추가 알림 대기

        if order.status == order.Completed:
            if isinstance(order, bt.BuyOrder):
                # 매수 주문 완료
                if self.p.printops:
                    txt = 'BUY, %.2f' % order.executed.price
                    self.log(txt, order.executed.dt)
                chkprice = '%.2f' % order.executed.price
                self.buyexec.append(chkprice)
            else:  # elif isinstance(order, SellOrder):
                # 매도 주문 완료
                if self.p.printops:
                    txt = 'SELL, %.2f' % order.executed.price
                    self.log(txt, order.executed.dt)

                chkprice = '%.2f' % order.executed.price
                self.sellexec.append(chkprice)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            # 주문 만료, 취소, 마진 부족
            if self.p.printops:
                self.log('%s ,' % order.Status[order.status])

        # 새로운 주문 허용
        self.orderid = None

    def __init__(self):
        """전략 초기화"""
        # 새로운 주문을 허용할지 여부를 제어하는 플래그
        self.orderid = None

        # SMA 지표와 크로스오버 신호 생성
        self.sma = btind.SMA(self.data, period=self.p.period)
        self.cross = btind.CrossOver(self.data.close, self.sma, plot=True)

    def start(self):
        """전략 시작 시 호출되는 메서드"""
        # 주식과 유사하지 않은 거래 모드일 때 수수료 설정
        if not self.p.stocklike:
            self.broker.setcommission(commission=2.0, mult=10.0, margin=1000.0)

        if self.p.printdata:
            self.log('-------------------------', nodate=True)
            self.log('Starting portfolio value: %.2f' % self.broker.getvalue(),
                     nodate=True)

        self.tstart = time_clock()  # 시작 시간 기록

        # 거래 기록을 저장할 리스트들 초기화
        self.buycreate = list()   # 매수 주문 생성 가격들
        self.sellcreate = list()  # 매도 주문 생성 가격들
        self.buyexec = list()     # 매수 주문 실행 가격들
        self.sellexec = list()    # 매도 주문 실행 가격들

    def stop(self):
        """전략 종료 시 호출되는 메서드"""
        tused = time_clock() - self.tstart  # 사용된 시간 계산
        
        if self.p.printdata:
            # 메인 모드일 때 상세 결과 출력
            self.log('Time used: %s' % str(tused))
            self.log('Final portfolio value: %.2f' % self.broker.getvalue())
            self.log('Final cash value: %.2f' % self.broker.getcash())
            self.log('-------------------------')

            print('buycreate')
            print(self.buycreate)
            print('sellcreate')
            print(self.sellcreate)
            print('buyexec')
            print(self.buyexec)
            print('sellexec')
            print(self.sellexec)

        else:
            # 테스트 모드일 때 결과 검증
            if not self.p.stocklike:
                # 선물 거래 모드일 때 예상 값들
                assert '%.2f' % self.broker.getvalue() == '12795.00'
                assert '%.2f' % self.broker.getcash() == '11795.00'
            else:
                # 주식 거래 모드일 때 예상 값들
                assert '%.2f' % self.broker.getvalue() == '10284.10'
                assert '%.2f' % self.broker.getcash() == '6164.16'

            # 거래 가격들 검증
            assert self.buycreate == BUYCREATE
            assert self.sellcreate == SELLCREATE
            assert self.buyexec == BUYEXEC
            assert self.sellexec == SELLEXEC

    def next(self):
        """각 바(bar)마다 호출되는 메인 로직"""
        if self.p.printdata:
            # OHLC 데이터와 SMA 값 출력
            self.log(
                'Open, High, Low, Close, %.2f, %.2f, %.2f, %.2f, Sma, %f' %
                (self.data.open[0], self.data.high[0],
                 self.data.low[0], self.data.close[0],
                 self.sma[0]))
            self.log('Close %.2f - Sma %.2f' %
                     (self.data.close[0], self.sma[0]))

        if self.orderid:
            # 활성 주문이 있으면 새로운 주문을 허용하지 않음
            return

        # 포지션이 없을 때 매수 신호 확인
        if not self.position.size:
            if self.cross > 0.0:  # 가격이 SMA 위로 크로스
                if self.p.printops:
                    self.log('BUY CREATE , %.2f' % self.data.close[0])

                self.orderid = self.buy()
                chkprice = '%.2f' % self.data.close[0]
                self.buycreate.append(chkprice)

        # 포지션이 있을 때 매도 신호 확인
        elif self.cross < 0.0:  # 가격이 SMA 아래로 크로스
            if self.p.printops:
                self.log('SELL CREATE , %.2f' % self.data.close[0])

            self.orderid = self.close()
            chkprice = '%.2f' % self.data.close[0]
            self.sellcreate.append(chkprice)


# 테스트할 데이터 개수
chkdatas = 1


def test_run(main=False):
    """
    비최적화 전략 테스트를 실행하는 메인 함수
    
    주식과 선물 거래 모드 모두에서 전략을 테스트합니다.
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    # 주식과 선물 거래 모드 모두 테스트
    for stlike in [False, True]:
        # 테스트 데이터 로드
        datas = [testcommon.getdata(i) for i in range(chkdatas)]
        
        # 공통 테스트 함수를 사용하여 전략 테스트 실행
        testcommon.runtest(datas,
                           TestStrategy,
                           printdata=main,
                           printops=main,
                           stocklike=stlike,  # 거래 모드 설정
                           plot=main)


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
