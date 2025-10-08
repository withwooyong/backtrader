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

import datetime
import os
import os.path
import sys

# 모듈 루트 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtrader as bt
import backtrader.utils.flushfile
from backtrader.metabase import ParamsBase


modpath = os.path.dirname(os.path.abspath(__file__))
dataspath = '../datas'
datafiles = [
    '2006-day-001.txt',  # 2006년 일별 데이터 파일
    '2006-week-001.txt',  # 2006년 주별 데이터 파일
]

DATAFEED = bt.feeds.BacktraderCSVData  # 백트레이더 CSV 데이터 피드 사용

FROMDATE = datetime.datetime(2006, 1, 1)  # 시작 날짜: 2006년 1월 1일
TODATE = datetime.datetime(2006, 12, 31)  # 종료 날짜: 2006년 12월 31일


def getdata(index, fromdate=FROMDATE, todate=TODATE):
    """
    지정된 인덱스의 데이터 파일을 로드하는 함수
    
    Args:
        index: 데이터 파일 인덱스
        fromdate: 시작 날짜 (기본값: FROMDATE)
        todate: 종료 날짜 (기본값: TODATE)
    
    Returns:
        로드된 데이터 피드 객체
    """
    datapath = os.path.join(modpath, dataspath, datafiles[index])
    data = DATAFEED(
        dataname=datapath,
        fromdate=fromdate,
        todate=todate)

    return data


def runtest(datas,
            strategy,
            runonce=None,
            preload=None,
            exbar=None,
            plot=False,
            optimize=False,
            maxcpus=1,
            writer=None,
            analyzer=None,
            **kwargs):
    """
    백트레이더 전략을 테스트하는 메인 함수
    
    Args:
        datas: 데이터 피드 또는 데이터 피드 리스트
        strategy: 테스트할 전략 클스
        runonce: runonce 모드 설정 (None이면 True/False 모두 테스트)
        preload: 데이터 프리로드 설정 (None이면 True/False 모두 테스트)
        exbar: exactbars 설정 (None이면 -2, -1, False 모두 테스트)
        plot: 플롯 표시 여부
        optimize: 최적화 모드 여부
        maxcpus: 최대 CPU 사용 수
        writer: 데이터 작성자 설정
        analyzer: 분석기 설정
        **kwargs: 추가 전략 매개변수
    
    Returns:
        실행된 Cerebro 객체들의 리스트
    """
    runonces = [True, False] if runonce is None else [runonce]
    preloads = [True, False] if preload is None else [preload]
    exbars = [-2, -1, False] if exbar is None else [exbar]

    cerebros = list()
    for prload in preloads:
        for ronce in runonces:
            for exbar in exbars:
                # Cerebro 엔진 생성
                cerebro = bt.Cerebro(runonce=ronce,
                                     preload=prload,
                                     maxcpus=maxcpus,
                                     exactbars=exbar)

                if kwargs.get('main', False):
                    print('prload {} / ronce {} exbar {}'.format(
                        prload, ronce, exbar))

                # 데이터 피드 추가
                if isinstance(datas, bt.LineSeries):
                    datas = [datas]
                for data in datas:
                    cerebro.adddata(data)

                if not optimize:
                    # 단일 전략 모드
                    cerebro.addstrategy(strategy, **kwargs)

                    # 데이터 작성자 추가
                    if writer:
                        wr = writer[0]
                        wrkwargs = writer[1]
                        cerebro.addwriter(wr, **wrkwargs)

                    # 분석기 추가
                    if analyzer:
                        al = analyzer[0]
                        alkwargs = analyzer[1]
                        cerebro.addanalyzer(al, **alkwargs)

                else:
                    # 최적화 모드
                    cerebro.optstrategy(strategy, **kwargs)

                cerebro.run()  # 백테스트 실행
                if plot:
                    cerebro.plot()  # 결과 플롯

                cerebros.append(cerebro)

    return cerebros


class TestStrategy(bt.Strategy):
    """
    테스트용 기본 전략 클래스
    
    이 클래스는 다양한 지표와 데이터를 테스트하기 위한 공통 전략을 제공합니다.
    """
    params = dict(main=False,          # 메인 출력 모드
                  chkind=[],            # 체크할 지표 리스트
                  inddata=[],           # 지표 데이터
                  chkmin=1,            # 최소 기간
                  chknext=0,           # 체크할 next 호출 수
                  chkvals=None,        # 체크할 값들
                  chkargs=dict())      # 지표 생성 시 추가 인수

    def __init__(self):
        """전략 초기화 - 지표들을 설정하고 데이터에 추가"""
        try:
            ind = self.p.chkind[0]
        except TypeError:
            chkind = [self.p.chkind]
        else:
            chkind = self.p.chkind

        # 첫 번째 데이터에 지표 추가
        if len(self.p.inddata):
            self.ind = chkind[0](*self.p.inddata, **self.p.chkargs)
        else:
            self.ind = chkind[0](self.data, **self.p.chkargs)

        # 추가 지표들을 첫 번째 데이터에 추가
        for ind in chkind[1:]:
            ind(self.data)

        # 다른 데이터들에도 지표 추가
        for data in self.datas[1:]:
            chkind[0](data, **self.p.chkargs)

            for ind in chkind[1:]:
                ind(data)

    def prenext(self):
        """최소 기간 이전에 호출되는 메서드"""
        pass

    def nextstart(self):
        """최소 기간에 도달했을 때 한 번만 호출되는 메서드"""
        self.chkmin = len(self)
        super(TestStrategy, self).nextstart()

    def next(self):
        """각 바(bar)마다 호출되는 메인 로직"""
        self.nextcalls += 1

        if self.p.main:
            # 메인 모드일 때 상세 정보 출력
            dtstr = self.data.datetime.date(0).strftime('%Y-%m-%d')
            print('%s - %d - %f' % (dtstr, len(self), self.ind[0]))
            pstr = ', '.join(str(x) for x in
                             [self.data.open[0], self.data.high[0],
                              self.data.low[0], self.data.close[0]])
            print('%s - %d, %s' % (dtstr, len(self), pstr))

    def start(self):
        """전략 시작 시 호출되는 메서드"""
        self.nextcalls = 0

    def stop(self):
        """전략 종료 시 호출되는 메서드 - 결과 검증 수행"""
        l = len(self.ind)
        mp = self.chkmin
        chkpts = [0, -l + mp, (-l + mp) // 2]  # 체크 포인트들

        if self.p.main:
            # 메인 모드일 때 상세 결과 출력
            print('----------------------------------------')
            print('len ind %d == %d len self' % (l, len(self)))
            print('minperiod %d' % self.chkmin)
            print('self.p.chknext %d nextcalls %d'
                  % (self.p.chknext, self.nextcalls))

            print('chkpts are', chkpts)
            for chkpt in chkpts:
                dtstr = self.data.datetime.date(chkpt).strftime('%Y-%m-%d')
                print('chkpt %d -> %s' % (chkpt, dtstr))

            # 각 지표 라인의 값들을 출력
            for lidx in range(self.ind.size()):
                chkvals = list()
                outtxt = '    ['
                for chkpt in chkpts:
                    valtxt = "'%f'" % self.ind.lines[lidx][chkpt]
                    outtxt += "'%s'," % valtxt
                    chkvals.append(valtxt)

                    outtxt = '    [' + ', '.join(chkvals) + '],'

                if lidx == self.ind.size() - 1:
                    outtxt = outtxt.rstrip(',')

                print(outtxt)

            print('vs expected')

            for chkval in self.p.chkvals:
                print(chkval)

        else:
            # 테스트 모드일 때 검증 수행
            assert l == len(self)
            if self.p.chknext:
                assert self.p.chknext == self.nextcalls
            assert mp == self.p.chkmin
            for lidx, linevals in enumerate(self.p.chkvals):
                for i, chkpt in enumerate(chkpts):
                    chkval = '%f' % self.ind.lines[lidx][chkpt]
                    if not isinstance(linevals[i], tuple):
                        assert chkval == linevals[i]
                    else:
                        try:
                            assert chkval == linevals[i][0]
                        except AssertionError:
                            assert chkval == linevals[i][1]


class SampleParamsHolder(ParamsBase):
    """
    메타 매개변수 처리를 테스트하기 위한 샘플 클래스
    
    이 클래스는 상속된 클래스에서 `frompackages`, `packages`, `params`, `lines`와 같은
    메타 매개변수의 적절한 처리를 확인하는 테스트에 사용됩니다.
    """
    frompackages = (
        ('math', ('factorial')),  # math 패키지에서 factorial 함수 가져오기
    )

    def __init__(self):
        self.range = factorial(10)  # factorial(10) 계산하여 저장
