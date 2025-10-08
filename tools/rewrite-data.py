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
"""
데이터 형식 변환 도구 (rewrite-data.py)

이 스크립트는 다양한 데이터 형식을 Backtrader의 표준 CSV 형식으로 변환하는 도구입니다.
여러 브로커와 데이터 제공업체의 데이터 형식을 통일된 형식으로 변환할 수 있습니다.

지원하는 데이터 형식:
- BacktraderCSV, VChartCSV, VChart, VCData, VChartFile
- IBData, SierraChartCSV, MT4CSV
- YahooFinanceCSV, YahooFinanceData

사용법:
    python rewrite-data.py --format [형식] --infile [입력파일] --outfile [출력파일]

주요 기능:
- 다양한 데이터 형식 지원
- 날짜 범위 필터링
- 사용자 정의 구분자 지원
- 차트 플롯 기능
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import os.path
import time
import sys


import backtrader as bt
from backtrader.utils.py3 import bytes


# 지원하는 데이터 형식들과 해당 Backtrader 피드 클래스 매핑
DATAFORMATS = dict(
    btcsv=bt.feeds.BacktraderCSVData,           # Backtrader 표준 CSV 형식
    vchartcsv=bt.feeds.VChartCSVData,           # VChart CSV 형식
    vchart=bt.feeds.VChartData,                 # VChart 데이터 형식
    vcdata=bt.feeds.VCData,                     # VCData 형식
    vcfile=bt.feeds.VChartFile,                 # VChart 파일 형식
    ibdata=bt.feeds.IBData,                     # Interactive Brokers 데이터 형식
    sierracsv=bt.feeds.SierraChartCSVData,      # Sierra Chart CSV 형식
    mt4csv=bt.feeds.MT4CSVData,                 # MetaTrader 4 CSV 형식
    yahoocsv=bt.feeds.YahooFinanceCSVData,      # Yahoo Finance CSV 형식
    yahoocsv_unreversed=bt.feeds.YahooFinanceCSVData,  # Yahoo Finance CSV (역순 없음)
    yahoo=bt.feeds.YahooFinanceData,            # Yahoo Finance 데이터 형식
)


class RewriteStrategy(bt.Strategy):
    """
    데이터 변환을 위한 전략 클래스
    
    이 전략은 입력 데이터를 읽어서 Backtrader 표준 CSV 형식으로 변환합니다.
    각 데이터 포인트를 처리하여 지정된 형식으로 출력 파일에 기록합니다.
    """
    params = (
        ('separator', ','),     # CSV 필드 구분자 (기본값: 쉼표)
        ('outfile', None),      # 출력 파일명 (None이면 표준 출력)
    )

    def start(self):
        """
        전략 시작 시 호출되는 메서드
        출력 파일을 열고 CSV 헤더를 작성합니다.
        """
        # 출력 파일 설정 (None이면 표준 출력 사용)
        if self.p.outfile is None:
            self.f = sys.stdout
        else:
            self.f = open(self.p.outfile, 'wb')

        # 시간 프레임에 따라 헤더 결정
        if self.data._timeframe < bt.TimeFrame.Days:
            # 일봉 미만 (분봉, 시간봉 등)인 경우 시간 컬럼 포함
            headers = 'Date,Time,Open,High,Low,Close,Volume,OpenInterest'
        else:
            # 일봉 이상인 경우 날짜만 포함
            headers = 'Date,Open,High,Low,Close,Volume,OpenInterest'

        headers += '\n'
        self.f.write(bytes(headers))

    def next(self):
        """
        각 데이터 포인트마다 호출되는 메서드
        현재 바의 데이터를 CSV 형식으로 출력 파일에 기록합니다.
        """
        fields = list()
        
        # 날짜 필드 추가
        dt = self.data.datetime.date(0).strftime('%Y-%m-%d')
        fields.append(dt)
        
        # 일봉 미만인 경우 시간 필드 추가
        if self.data._timeframe < bt.TimeFrame.Days:
            tm = self.data.datetime.time(0).strftime('%H:%M:%S')
            fields.append(tm)

        # OHLC 데이터 추가 (소수점 2자리로 포맷)
        o = '%.2f' % self.data.open[0]      # 시가
        fields.append(o)
        h = '%.2f' % self.data.high[0]      # 고가
        fields.append(h)
        l = '%.2f' % self.data.low[0]       # 저가
        fields.append(l)
        c = '%.2f' % self.data.close[0]     # 종가
        fields.append(c)
        
        # 거래량과 미결제약정 추가 (정수로 포맷)
        v = '%d' % self.data.volume[0]          # 거래량
        fields.append(v)
        oi = '%d' % self.data.openinterest[0]   # 미결제약정
        fields.append(oi)

        # 필드들을 구분자로 연결하여 한 줄로 만들고 파일에 기록
        txt = self.p.separator.join(fields)
        txt += '\n'
        self.f.write(bytes(txt))


def runstrat(pargs=None):
    """
    데이터 변환 전략을 실행하는 메인 함수
    
    Args:
        pargs: 명령줄 인수 리스트 (None이면 sys.argv 사용)
    """
    # 명령줄 인수 파싱
    args = parse_args(pargs)

    # Cerebro 엔진 생성
    cerebro = bt.Cerebro()

    # 데이터 피드 설정을 위한 키워드 인수 딕셔너리
    dfkwargs = dict()
    
    # Yahoo 데이터의 경우 역순 처리 설정
    if args.format == 'yahoo_unreversed':
        dfkwargs['reverse'] = True

    # 시작 날짜 처리
    fmtstr = '%Y-%m-%d'
    if args.fromdate:
        dtsplit = args.fromdate.split('T')
        if len(dtsplit) > 1:
            # 시간 정보가 포함된 경우 형식 문자열 확장
            fmtstr += 'T%H:%M:%S'

        fromdate = datetime.datetime.strptime(args.fromdate, fmtstr)
        dfkwargs['fromdate'] = fromdate

    # 종료 날짜 처리
    fmtstr = '%Y-%m-%d'
    if args.todate:
        dtsplit = args.todate.split('T')
        if len(dtsplit) > 1:
            # 시간 정보가 포함된 경우 형식 문자열 확장
            fmtstr += 'T%H:%M:%S'
        todate = datetime.datetime.strptime(args.todate, fmtstr)
        dfkwargs['todate'] = todate

    # 지정된 형식에 해당하는 데이터 피드 클래스 선택
    dfcls = DATAFORMATS[args.format]
    data = dfcls(dataname=args.infile, **dfkwargs)
    cerebro.adddata(data)

    # 데이터 변환 전략 추가
    cerebro.addstrategy(RewriteStrategy,
                        separator=args.separator,    # CSV 구분자
                        outfile=args.outfile)        # 출력 파일명

    # 전략 실행 (표준 통계 비활성화)
    cerebro.run(stdstats=False)

    # 플롯 옵션이 지정된 경우 차트 생성
    if args.plot:
        pkwargs = dict(style='bar')  # 기본 바 차트 스타일
        if args.plot is not True:  # 추가 플롯 옵션이 전달된 경우
            npkwargs = eval('dict(' + args.plot + ')')  # 문자열을 딕셔너리로 변환
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):
    """
    명령줄 인수를 파싱하는 함수
    
    Args:
        pargs: 파싱할 인수 리스트 (None이면 sys.argv 사용)
        
    Returns:
        argparse.Namespace: 파싱된 인수들
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='다양한 데이터 형식을 Backtrader CSV 형식으로 변환')

    # 입력 데이터 형식 선택
    parser.add_argument('--format', '-fmt', required=False,
                        choices=DATAFORMATS.keys(),
                        default=next(iter(DATAFORMATS)),
                        help='읽어들일 파일의 데이터 형식')

    # 입력 파일 경로 (필수)
    parser.add_argument('--infile', '-i', required=True,
                        help='읽어들일 입력 파일 경로')

    # 출력 파일 경로 (선택사항, 기본값은 표준 출력)
    parser.add_argument('--outfile', '-o', default=None, required=False,
                        help='출력할 파일 경로 (지정하지 않으면 표준 출력)')

    # 시작 날짜 필터
    parser.add_argument('--fromdate', '-f', required=False,
                        help='시작 날짜 (YYYY-MM-DD 형식)')

    # 종료 날짜 필터
    parser.add_argument('--todate', '-t', required=False,
                        help='종료 날짜 (YYYY-MM-DD 형식)')

    # CSV 구분자 설정
    parser.add_argument('--separator', '-s', required=False, default=',',
                        help='CSV 필드 구분자 (기본값: 쉼표)')

    # 플롯 옵션
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True,
                        help=('데이터를 차트로 플롯 (추가 옵션 전달 가능)\n'
                              '\n'
                              '예시:\n'
                              '\n'
                              '  --plot style="candle" (캔들 차트로 플롯)\n'))

    # 인수가 전달된 경우 해당 인수를 파싱, 그렇지 않으면 sys.argv 파싱
    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    # 스크립트가 직접 실행될 때 메인 함수 호출
    runstrat()
