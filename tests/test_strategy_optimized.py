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

import itertools
import time
try:
    time_clock = time.process_time  # Python 3.3+ 에서는 process_time 사용
except:
    time_clock = time.clock         # 이전 버전에서는 clock 사용

import testcommon

from backtrader.utils.py3 import range
import backtrader as bt
import backtrader.indicators as btind

# 최적화 테스트에서 예상되는 포트폴리오 가치들
# 각 값은 서로 다른 기간(period) 설정에 대한 결과
CHKVALUES = [
    '14525.80', '14525.80', '15408.20', '15408.20', '14763.90',
    '14763.90', '14763.90', '14763.90', '14763.90', '14763.90',
    '14763.90', '14763.90', '14763.90', '14763.90', '13187.10',
    '13187.10', '13187.10', '13684.40', '13684.40', '13684.40',
    '13684.40', '13684.40', '13684.40', '13656.10', '13656.10',
    '13656.10', '13656.10', '12988.10', '12988.10', '12988.10',
    '12988.10', '12988.10', '12988.10', '12988.10', '12988.10',
    '12988.10', '12988.10', '12988.10', '12988.10', '12988.10'
]

# 최적화 테스트에서 예상되는 현금 잔고들
# 각 값은 서로 다른 기간(period) 설정에 대한 결과
CHKCASH = [
    '13525.80', '13525.80', '14408.20', '14408.20', '13763.90',
    '13763.90', '13763.90', '13763.90', '13763.90', '13763.90',
    '13763.90', '13763.90', '13763.90', '13763.90', '12187.10',
    '12187.10', '12187.10', '12684.40', '12684.40', '12684.40',
    '12684.40', '12684.40', '12684.40', '12656.10', '12656.10',
    '12656.10', '12656.10', '11988.10', '11988.10', '11988.10',
    '11988.10', '11988.10', '11988.10', '11988.10', '11988.10',
    '11988.10', '11988.10', '11988.10', '11988.10', '11988.10'
]

# 전역 변수로 최적화 결과를 저장
_chkvalues = []
_chkcash = []


class TestStrategy(bt.Strategy):
    """
    최적화 테스트를 위한 전략 클래스
    
    이 전략은 SMA 크로스오버를 사용하여 매수/매도 신호를 생성합니다.
    최적화 과정에서 다양한 기간(period) 값으로 테스트됩니다.
    """
    params = (
        ('period', 15),        # SMA 기간 (기본값: 15)
        ('printdata', True),   # 데이터 출력 여부
        ('printops', True),    # 작업 출력 여부
    )

    def log(self, txt, dt=None):
        """로그 메시지를 출력하는 헬퍼 메서드"""
        dt = dt or self.data.datetime[0]
        dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 새로운 주문을 허용할지 여부를 제어하는 플래그
        self.orderid = None

        # SMA 지표와 크로스오버 신호 생성
        self.sma = btind.SMA(self.data, period=self.p.period)
        self.cross = btind.CrossOver(self.data.close, self.sma, plot=True)

    def start(self):
        """전략 시작 시 호출되는 메서드"""
        # 수수료 설정 (수수료: 2.0, 승수: 10.0, 마진: 1000.0)
        self.broker.setcommission(commission=2.0, mult=10.0, margin=1000.0)
        self.tstart = time_clock()  # 시작 시간 기록
        self.buy_create_idx = itertools.count()  # 매수 주문 인덱스 생성기

    def stop(self):
        """전략 종료 시 호출되는 메서드"""
        global _chkvalues
        global _chkcash

        # 사용된 시간 계산
        tused = time_clock() - self.tstart
        
        if self.p.printdata:
            self.log(('Time used: %s  - Period % d - '
                      'Start value: %.2f - End value: %.2f') %
                     (str(tused), self.p.period,
                      self.broker.startingcash, self.broker.getvalue()))

        # 최종 포트폴리오 가치와 현금 잔고를 전역 변수에 저장
        value = '%.2f' % self.broker.getvalue()
        _chkvalues.append(value)

        cash = '%.2f' % self.broker.getcash()
        _chkcash.append(cash)

    def next(self):
        """각 바(bar)마다 호출되는 메인 로직"""
        # print('self.data.close.array:', self.data.close.array)
        
        if self.orderid:
            # 활성 주문이 있으면 새로운 주문을 허용하지 않음
            return

        # 포지션이 없을 때 매수 신호 확인
        if not self.position.size:
            if self.cross > 0.0:  # 가격이 SMA 위로 크로스
                self.orderid = self.buy()

        # 포지션이 있을 때 매도 신호 확인
        elif self.cross < 0.0:  # 가격이 SMA 아래로 크로스
            self.orderid = self.close()


# 테스트할 데이터 개수
chkdatas = 1


def test_run(main=False):
    """
    최적화 전략 테스트를 실행하는 메인 함수
    
    Args:
        main: 메인 출력 모드 여부 (True면 상세 정보 출력)
    """
    global _chkvalues
    global _chkcash

    # 다양한 설정 조합으로 테스트 실행
    for runonce in [True, False]:           # runonce 모드
        for preload in [True, False]:       # 프리로드 모드
            for exbar in [True, False, -1, -2]:  # exactbars 설정
                # 각 조합마다 결과 리스트 초기화
                _chkvalues = list()
                _chkcash = list()

                # 테스트 데이터 로드
                datas = [testcommon.getdata(i) for i in range(chkdatas)]
                
                # 최적화 모드로 테스트 실행 (기간 5-44 범위로 테스트)
                testcommon.runtest(datas,
                                   TestStrategy,
                                   runonce=runonce,
                                   preload=preload,
                                   exbar=exbar,
                                   optimize=True,           # 최적화 모드 활성화
                                   period=range(5, 45),     # 기간 범위: 5-44
                                   printdata=main,
                                   printops=main,
                                   plot=False)

                if not main:
                    # 테스트 모드일 때 결과 검증
                    assert CHKVALUES == _chkvalues
                    assert CHKCASH == _chkcash

                else:
                    # 메인 모드일 때 결과 비교 출력
                    print('*' * 50)
                    print(CHKVALUES == _chkvalues)
                    print('-' * 50)
                    print(CHKVALUES)
                    print('-' * 50)
                    print(_chkvalues)
                    print('*' * 50)
                    print(CHKCASH == _chkcash)
                    print('-' * 50)
                    print(CHKCASH)
                    print('-' * 50)
                    print(_chkcash)


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 모드로 테스트 실행
    test_run(main=True)
