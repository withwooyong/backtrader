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
# 이동평균 교차 전략 샘플 코드
# =============================================================================
# 이 파일은 Backtrader를 사용한 가장 기본적인 트레이딩 전략의 예제입니다.
# 두 개의 이동평균선이 교차할 때 매수/매도 신호를 생성하는 전략을 구현합니다.
# 
# 전략 로직:
# - 단기 이동평균이 장기 이동평균을 상향 돌파할 때 매수 (골든 크로스)
# - 단기 이동평균이 장기 이동평균을 하향 돌파할 때 매도 (데드 크로스)
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt


# =============================================================================
# SmaCross 클래스 - 이동평균 교차 전략 구현
# =============================================================================
# 이 클래스는 bt.SignalStrategy를 상속받아 자동 신호 생성 전략을 구현합니다.
# SignalStrategy는 신호 기반으로 자동으로 매수/매도 주문을 생성합니다.
class SmaCross(bt.SignalStrategy):
    # =============================================================================
    # 전략 파라미터 설정
    # =============================================================================
    # sma1: 단기 이동평균 기간 (기본값: 10)
    # sma2: 장기 이동평균 기간 (기본값: 20)
    params = dict(sma1=10, sma2=20)

    def notify_order(self, order):
        # =============================================================================
        # 주문 상태 알림 처리
        # =============================================================================
        # 주문이 완료되면 거래 정보를 출력합니다
        if not order.alive():  # 주문이 더 이상 활성 상태가 아닐 때 (완료됨)
            print('{} {} {}@{}'.format(
                bt.num2date(order.executed.dt),  # 주문 실행 시간
                'buy' if order.isbuy() else 'sell',  # 매수/매도 구분
                order.executed.size,   # 주문 수량
                order.executed.price)  # 주문 실행 가격
            )

    def notify_trade(self, trade):
        # =============================================================================
        # 거래 완료 알림 처리
        # =============================================================================
        # 거래가 완료되면 수익/손실 정보를 출력합니다
        if trade.isclosed:  # 거래가 완전히 종료되었을 때
            print('profit {}'.format(trade.pnlcomm))  # 수수료 포함 수익/손실

    def __init__(self):
        # =============================================================================
        # 전략 초기화 및 지표 설정
        # =============================================================================
        # 두 개의 이동평균 지표 생성
        sma1 = bt.ind.SMA(period=self.params.sma1)  # 단기 이동평균
        sma2 = bt.ind.SMA(period=self.params.sma2)  # 장기 이동평균
        
        # 이동평균 교차 신호 생성
        # CrossOver는 두 라인이 교차할 때 +1(상향돌파) 또는 -1(하향돌파) 값을 반환
        crossover = bt.ind.CrossOver(sma1, sma2)
        
        # 매수 신호 추가 (SIGNAL_LONG: 양수일 때 매수)
        self.signal_add(bt.SIGNAL_LONG, crossover)


# =============================================================================
# runstrat 함수 - 백테스팅 실행 메인 함수
# =============================================================================
# 이 함수는 전체 백테스팅 프로세스를 실행합니다.
def runstrat(pargs=None):
    args = parse_args(pargs)  # 명령행 인수 파싱

    # =============================================================================
    # 백테스팅 엔진 설정
    # =============================================================================
    cerebro = bt.Cerebro()  # 백테스팅 엔진 생성
    cerebro.broker.set_cash(args.cash)  # 초기 자본 설정

    # =============================================================================
    # 데이터 피드 설정
    # =============================================================================
    # Yahoo Finance에서 주식 데이터 다운로드
    data0 = bt.feeds.YahooFinanceData(
        dataname=args.data,  # 주식 심볼 (예: AAPL, GOOGL)
        fromdate=datetime.datetime.strptime(args.fromdate, '%Y-%m-%d'),  # 시작 날짜
        todate=datetime.datetime.strptime(args.todate, '%Y-%m-%d'))      # 종료 날짜
    cerebro.adddata(data0)  # 데이터 피드 추가

    # =============================================================================
    # 전략 및 포지션 크기 설정
    # =============================================================================
    cerebro.addstrategy(SmaCross, **(eval('dict(' + args.strat + ')')))  # 전략 추가
    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)  # 포지션 크기 설정 (고정 크기)

    # =============================================================================
    # 백테스팅 실행 및 결과 시각화
    # =============================================================================
    cerebro.run()  # 백테스팅 실행
    if args.plot:  # 플롯 옵션이 활성화된 경우
        cerebro.plot(**(eval('dict(' + args.plot + ')')))  # 결과 차트 출력


# =============================================================================
# parse_args 함수 - 명령행 인수 파싱
# =============================================================================
# 이 함수는 사용자가 명령행에서 전달한 인수들을 파싱합니다.
def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='sigsmacross')

    # =============================================================================
    # 명령행 인수 정의
    # =============================================================================
    parser.add_argument('--data', required=False, default='YHOO',
                        help='Yahoo Ticker')  # 주식 심볼

    parser.add_argument('--fromdate', required=False, default='2011-01-01',
                        help='Ending date in YYYY-MM-DD format')  # 시작 날짜

    parser.add_argument('--todate', required=False, default='2012-12-31',
                        help='Ending date in YYYY-MM-DD format')  # 종료 날짜

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=10000, help=('Starting cash'))  # 초기 자본

    parser.add_argument('--stake', required=False, action='store', type=int,
                        default=1, help=('Stake to apply'))  # 거래당 주문 수량

    parser.add_argument('--strat', required=False, action='store', default='',
                        help=('Arguments for the strategy'))  # 전략 파라미터

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))  # 차트 출력 옵션

    return parser.parse_args(pargs)


# =============================================================================
# 메인 실행 부분
# =============================================================================
# 스크립트가 직접 실행될 때 백테스팅을 시작합니다.
if __name__ == '__main__':
    runstrat()
