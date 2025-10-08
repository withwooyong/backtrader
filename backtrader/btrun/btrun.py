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
# Backtrader 실행(BTRun) 핵심 모듈
# =============================================================================
# 이 모듈은 Backtrader 전략을 실행하기 위한 고급 명령줄 인터페이스를 제공합니다.
# 복잡한 백테스팅 설정을 간단한 명령어로 실행할 수 있게 해주며,
# 다양한 데이터 소스, 시간 프레임, 리샘플링 옵션을 지원합니다.
# 
# 주요 기능:
# - 명령줄 인수 파싱 및 검증
# - 다양한 데이터 포맷 자동 감지 및 로드
# - 시간 프레임 변환 및 리샘플링
# - 전략 파라미터 최적화
# - 결과 출력 및 저장
# 
# 사용 예시:
# python -m backtrader.btrun --data data.csv --strategy MyStrategy
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import inspect
import itertools
import random
import string
import sys

import backtrader as bt


# =============================================================================
# 지원되는 데이터 포맷 정의
# =============================================================================
# 각 데이터 소스별로 적절한 데이터 피드 클래스를 매핑합니다.
# 사용자가 지정한 포맷에 따라 자동으로 올바른 클래스를 선택합니다.
DATAFORMATS = dict(
    btcsv=bt.feeds.BacktraderCSVData,           # Backtrader 표준 CSV 형식
    vchartcsv=bt.feeds.VChartCSVData,           # Visual Chart CSV 형식
    vcfile=bt.feeds.VChartFile,                 # Visual Chart 파일 형식
    sierracsv=bt.feeds.SierraChartCSVData,      # Sierra Chart CSV 형식
    mt4csv=bt.feeds.MT4CSVData,                 # MetaTrader 4 CSV 형식
    yahoocsv=bt.feeds.YahooFinanceCSVData,      # Yahoo Finance CSV 형식
    yahoocsv_unreversed=bt.feeds.YahooFinanceCSVData,  # Yahoo Finance CSV (역순 아님)
    yahoo=bt.feeds.YahooFinanceData,            # Yahoo Finance 실시간 데이터
)

# =============================================================================
# 선택적 데이터 포맷들 (의존성 패키지 설치 시에만 사용 가능)
# =============================================================================
try:
    DATAFORMATS['vcdata'] = bt.feeds.VCData
except AttributeError:
    pass  # no comtypes available (comtypes 패키지가 없음)

try:
    DATAFORMATS['ibdata'] = bt.feeds.IBData,
except AttributeError:
    pass  # no ibpy available (ibpy 패키지가 없음)

try:
    DATAFORMATS['oandadata'] = bt.feeds.OandaData,
except AttributeError:
    pass  # no oandapy available (oandapy 패키지가 없음)


# =============================================================================
# 지원되는 시간 프레임 정의
# =============================================================================
# 사용자가 지정한 시간 프레임 문자열을 Backtrader의 TimeFrame 상수로 변환합니다.
TIMEFRAMES = dict(
    microseconds=bt.TimeFrame.MicroSeconds,  # 마이크로초
    seconds=bt.TimeFrame.Seconds,            # 초
    minutes=bt.TimeFrame.Minutes,            # 분
    days=bt.TimeFrame.Days,                  # 일
    weeks=bt.TimeFrame.Weeks,                # 주
    months=bt.TimeFrame.Months,              # 월
    years=bt.TimeFrame.Years,                # 년
)


# =============================================================================
# btrun 메인 함수 - Backtrader 실행의 진입점
# =============================================================================
# 이 함수는 명령줄 인수를 파싱하고, Cerebro를 설정하며,
# 전략을 실행하는 전체 과정을 관리합니다.
def btrun(pargs=''):
    # =============================================================================
    # 명령줄 인수 파싱
    # =============================================================================
    args = parse_args(pargs)

    if args.flush:
        import backtrader.utils.flushfile

    # =============================================================================
    # 표준 통계 표시 여부 설정
    # =============================================================================
    stdstats = not args.nostdstats

    # =============================================================================
    # Cerebro 설정 파라미터 처리
    # =============================================================================
    cer_kwargs_str = args.cerebro
    cer_kwargs = eval('dict(' + cer_kwargs_str + ')')
    if 'stdstats' not in cer_kwargs:
        cer_kwargs.update(stdstats=stdstats)

    # =============================================================================
    # Cerebro 인스턴스 생성
    # =============================================================================
    cerebro = bt.Cerebro(**cer_kwargs)

    # =============================================================================
    # 리샘플링 또는 리플레이 설정 처리
    # =============================================================================
    if args.resample is not None or args.replay is not None:
        if args.resample is not None:
            tfcp = args.resample.split(':')
        elif args.replay is not None:
            tfcp = args.replay.split(':')

        # compression may be skipped and it will default to 1
        # 압축 비율은 생략 가능하며 기본값은 1입니다
        if len(tfcp) == 1 or tfcp[1] == '':
            tf, cp = tfcp[0], 1
        else:
            tf, cp = tfcp

        cp = int(cp)  # convert any value to int (모든 값을 정수로 변환)
        tf = TIMEFRAMES.get(tf, None)

    for data in getdatas(args):
        if args.resample is not None:
            cerebro.resampledata(data, timeframe=tf, compression=cp)
        elif args.replay is not None:
            cerebro.replaydata(data, timeframe=tf, compression=cp)
        else:
            cerebro.adddata(data)

    # get and add signals
    signals = getobjects(args.signals, bt.Indicator, bt.signals, issignal=True)
    for sig, kwargs, sigtype in signals:
        stype = getattr(bt.signal, 'SIGNAL_' + sigtype.upper())
        cerebro.add_signal(stype, sig, **kwargs)

    # get and add strategies
    strategies = getobjects(args.strategies, bt.Strategy, bt.strategies)
    for strat, kwargs in strategies:
        cerebro.addstrategy(strat, **kwargs)

    inds = getobjects(args.indicators, bt.Indicator, bt.indicators)
    for ind, kwargs in inds:
        cerebro.addindicator(ind, **kwargs)

    obs = getobjects(args.observers, bt.Observer, bt.observers)
    for ob, kwargs in obs:
        cerebro.addobserver(ob, **kwargs)

    ans = getobjects(args.analyzers, bt.Analyzer, bt.analyzers)
    for an, kwargs in ans:
        cerebro.addanalyzer(an, **kwargs)

    setbroker(args, cerebro)

    for wrkwargs_str in args.writers or []:
        wrkwargs = eval('dict(' + wrkwargs_str + ')')
        cerebro.addwriter(bt.WriterFile, **wrkwargs)

    ans = getfunctions(args.hooks, bt.Cerebro)
    for hook, kwargs in ans:
        hook(cerebro, **kwargs)
    runsts = cerebro.run()
    runst = runsts[0]  # single strategy and no optimization

    if args.pranalyzer or args.ppranalyzer:
        if runst.analyzers:
            print('====================')
            print('== Analyzers')
            print('====================')
            for name, analyzer in runst.analyzers.getitems():
                if args.pranalyzer:
                    analyzer.print()
                elif args.ppranalyzer:
                    print('##########')
                    print(name)
                    print('##########')
                    analyzer.pprint()

    # =============================================================================
    # 결과 플롯 생성 (옵션)
    # =============================================================================
    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:
            # evaluates to True but is not "True" - args were passed
            # True로 평가되지만 "True"가 아님 - 인수가 전달됨
            ekwargs = eval('dict(' + args.plot + ')')
            pkwargs.update(ekwargs)

        # cerebro.plot(numfigs=args.plotfigs, style=args.plotstyle)
        cerebro.plot(**pkwargs)


# =============================================================================
# setbroker 함수 - 브로커 설정
# =============================================================================
# 이 함수는 Cerebro의 브로커에 현금, 수수료, 마진, 슬리피지 등의
# 설정을 적용합니다.
def setbroker(args, cerebro):
    broker = cerebro.getbroker()

    # =============================================================================
    # 현금 설정
    # =============================================================================
    if args.cash is not None:
        broker.setcash(args.cash)

    # =============================================================================
    # 수수료 관련 설정 수집
    # =============================================================================
    commkwargs = dict()
    if args.commission is not None:
        commkwargs['commission'] = args.commission
    if args.margin is not None:
        commkwargs['margin'] = args.margin
    if args.mult is not None:
        commkwargs['mult'] = args.mult
    if args.interest is not None:
        commkwargs['interest'] = args.interest
    if args.interest_long is not None:
        commkwargs['interest_long'] = args.interest_long

    # =============================================================================
    # 수수료 설정 적용
    # =============================================================================
    if commkwargs:
        broker.setcommission(**commkwargs)

    # =============================================================================
    # 슬리피지 설정 (퍼센트 또는 고정 금액)
    # =============================================================================
    if args.slip_perc is not None:
        cerebro.broker.set_slippage_perc(args.slip_perc,
                                         slip_open=args.slip_open,
                                         slip_match=not args.no_slip_match,
                                         slip_out=args.slip_out)
    elif args.slip_fixed is not None:
        cerebro.broker.set_slippage_fixed(args.slip_fixed,
                                          slip_open=args.slip_open,
                                          slip_match=not args.no_slip_match,
                                          slip_out=args.slip_out)


# =============================================================================
# getdatas 함수 - 데이터 피드 생성
# =============================================================================
# 이 함수는 명령줄 인수를 기반으로 데이터 피드 객체들을 생성합니다.
# 다양한 데이터 포맷, 시간 범위, 시간 프레임을 지원합니다.
def getdatas(args):
    # =============================================================================
    # 전역 딕셔너리에서 데이터 피드 클래스 가져오기
    # =============================================================================
    # Get the data feed class from the global dictionary
    dfcls = DATAFORMATS[args.format]

    # =============================================================================
    # 데이터 피드 파라미터 준비
    # =============================================================================
    # Prepare some args
    dfkwargs = dict()
    if args.format == 'yahoo_unreversed':
        dfkwargs['reverse'] = True

    # =============================================================================
    # 시작 날짜 설정
    # =============================================================================
    fmtstr = '%Y-%m-%d'
    if args.fromdate:
        dtsplit = args.fromdate.split('T')
        if len(dtsplit) > 1:
            fmtstr += 'T%H:%M:%S'

        fromdate = datetime.datetime.strptime(args.fromdate, fmtstr)
        dfkwargs['fromdate'] = fromdate

    # =============================================================================
    # 종료 날짜 설정
    # =============================================================================
    fmtstr = '%Y-%m-%d'
    if args.todate:
        dtsplit = args.todate.split('T')
        if len(dtsplit) > 1:
            fmtstr += 'T%H:%M:%S'
        todate = datetime.datetime.strptime(args.todate, fmtstr)
        dfkwargs['todate'] = todate

    # =============================================================================
    # 시간 프레임 및 압축 설정
    # =============================================================================
    if args.timeframe is not None:
        dfkwargs['timeframe'] = TIMEFRAMES[args.timeframe]

    if args.compression is not None:
        dfkwargs['compression'] = args.compression

    # =============================================================================
    # 데이터 피드 객체들 생성
    # =============================================================================
    datas = list()
    for dname in args.data:
        dfkwargs['dataname'] = dname
        data = dfcls(**dfkwargs)
        datas.append(data)

    return datas


# =============================================================================
# getmodclasses 함수 - 모듈에서 클래스 추출
# =============================================================================
# 이 함수는 지정된 모듈에서 특정 타입의 클래스들을 찾아 반환합니다.
# 전략, 분석기, 지표 등의 클래스를 동적으로 로드할 때 사용됩니다.
def getmodclasses(mod, clstype, clsname=None):
    clsmembers = inspect.getmembers(mod, inspect.isclass)

    clslist = list()
    for name, cls in clsmembers:
        if not issubclass(cls, clstype):
            continue

        if clsname:
            if clsname == name:
                clslist.append(cls)
                break
        else:
            clslist.append(cls)

    return clslist


# =============================================================================
# getmodfunctions 함수 - 모듈에서 함수들 추출
# =============================================================================
# 이 함수는 지정된 모듈에서 함수나 메서드들을 찾아 반환합니다.
# inspect 모듈을 사용하여 함수와 메서드를 모두 검색합니다.
def getmodfunctions(mod, funcname=None):
    # =============================================================================
    # 함수와 메서드 모두 검색
    # =============================================================================
    members = inspect.getmembers(mod, inspect.isfunction) + \
        inspect.getmembers(mod, inspect.ismethod)

    funclist = list()
    for name, member in members:
        if funcname:
            if name == funcname:
                funclist.append(member)
                break
        else:
            funclist.append(member)

    return funclist


# =============================================================================
# loadmodule 함수 - Python 버전별 모듈 로딩 분기
# =============================================================================
# 이 함수는 Python 버전에 따라 적절한 모듈 로딩 함수를 호출합니다.
# Python 3.3 미만에서는 loadmodule2를, 3.3 이상에서는 loadmodule3를 사용합니다.
def loadmodule(modpath, modname=''):
    # =============================================================================
    # 모듈 이름이 없으면 랜덤 이름 생성
    # =============================================================================
    # generate a random name for the module
    # 모듈을 위한 랜덤 이름 생성

    if not modpath.endswith('.py'):
        modpath += '.py'

    if not modname:
        chars = string.ascii_uppercase + string.digits
        modname = ''.join(random.choice(chars) for _ in range(10))

    # =============================================================================
    # Python 버전 확인 및 적절한 로딩 함수 호출
    # =============================================================================
    version = (sys.version_info[0], sys.version_info[1])

    if version < (3, 3):
        mod, e = loadmodule2(modpath, modname)
    else:
        mod, e = loadmodule3(modpath, modname)

    return mod, e


# =============================================================================
# loadmodule2 함수 - Python 2.x 호환 모듈 로딩
# =============================================================================
# 이 함수는 Python 2.x에서 사용되는 imp 모듈을 사용하여
# 동적으로 Python 모듈을 로드합니다.
def loadmodule2(modpath, modname):
    import imp

    try:
        mod = imp.load_source(modname, modpath)
    except Exception as e:
        return (None, e)

    return (mod, None)


# =============================================================================
# loadmodule3 함수 - Python 3.x 호환 모듈 로딩
# =============================================================================
# 이 함수는 Python 3.x에서 사용되는 importlib.machinery를 사용하여
# 동적으로 Python 모듈을 로드합니다.
def loadmodule3(modpath, modname):
    import importlib.machinery

    try:
        loader = importlib.machinery.SourceFileLoader(modname, modpath)
        mod = loader.load_module()
    except Exception as e:
        return (None, e)

    return (mod, None)


# =============================================================================
# getobjects 함수 - 모듈에서 객체 클래스들 추출
# =============================================================================
# 이 함수는 지정된 모듈에서 특정 타입의 클래스들을 찾아 반환합니다.
# 전략, 분석기, 지표, 옵저버 등의 클래스를 동적으로 로드할 때 사용됩니다.
def getobjects(iterable, clsbase, modbase, issignal=False):
    retobjects = list()

    for item in iterable or []:
        # =============================================================================
        # 시그널 타입 처리 (시그널인 경우에만)
        # =============================================================================
        if issignal:
            sigtokens = item.split('+', 1)
            if len(sigtokens) == 1:  # no + seen
                sigtype = 'longshort'
            else:
                sigtype, item = sigtokens

        # =============================================================================
        # 모듈 경로와 클래스 이름 파싱
        # =============================================================================
        tokens = item.split(':', 1)

        if len(tokens) == 1:
            modpath = tokens[0]
            name = ''
            kwargs = dict()
        else:
            modpath, name = tokens
            # =============================================================================
            # 키워드 인수 파싱
            # =============================================================================
            kwtokens = name.split(':', 1)
            if len(kwtokens) == 1:
                # no '(' found
                kwargs = dict()
            else:
                name = kwtokens[0]
                kwtext = 'dict(' + kwtokens[1] + ')'
                kwargs = eval(kwtext)

        # =============================================================================
        # 모듈 로딩
        # =============================================================================
        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                print('')
                print('Failed to load module %s:' % modpath, e)
                sys.exit(1)
        else:
            mod = modbase

        # =============================================================================
        # 클래스 검색 및 로딩
        # =============================================================================
        loaded = getmodclasses(mod=mod, clstype=clsbase, clsname=name)

        if not loaded:
            print('No class %s / module %s' % (str(name), modpath))
            sys.exit(1)

        # =============================================================================
        # 결과 객체 반환 (시그널인 경우 타입 정보 포함)
        # =============================================================================
        if issignal:
            retobjects.append((loaded[0], kwargs, sigtype))
        else:
            retobjects.append((loaded[0], kwargs))

    return retobjects

# =============================================================================
# getfunctions 함수 - 모듈에서 함수들 추출
# =============================================================================
# 이 함수는 지정된 모듈에서 함수들을 찾아 반환합니다.
# 훅 함수나 사용자 정의 함수를 동적으로 로드할 때 사용됩니다.
def getfunctions(iterable, modbase):
    retfunctions = list()

    for item in iterable or []:
        # =============================================================================
        # 모듈 경로와 함수 이름 파싱
        # =============================================================================
        tokens = item.split(':', 1)

        if len(tokens) == 1:
            modpath = tokens[0]
            name = ''
            kwargs = dict()
        else:
            modpath, name = tokens
            # =============================================================================
            # 키워드 인수 파싱
            # =============================================================================
            kwtokens = name.split(':', 1)
            if len(kwtokens) == 1:
                # no '(' found
                kwargs = dict()
            else:
                name = kwtokens[0]
                kwtext = 'dict(' + kwtokens[1] + ')'
                kwargs = eval(kwtext)

        # =============================================================================
        # 모듈 로딩
        # =============================================================================
        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                print('')
                print('Failed to load module %s:' % modpath, e)
                sys.exit(1)
        else:
            mod = modbase

        # =============================================================================
        # 함수 검색 및 로딩
        # =============================================================================
        loaded = getmodfunctions(mod=mod, funcname=name)

        if not loaded:
            print('No function %s / module %s' % (str(name), modpath))
            sys.exit(1)

        # =============================================================================
        # 결과 함수 반환
        # =============================================================================
        retfunctions.append((loaded[0], kwargs))

    return retfunctions


# =============================================================================
# parse_args 함수 - 명령줄 인수 파싱
# =============================================================================
# 이 함수는 명령줄에서 전달된 인수들을 파싱하여
# Backtrader 실행에 필요한 모든 설정을 처리합니다.
def parse_args(pargs=''):
    # =============================================================================
    # ArgumentParser 초기화
    # =============================================================================
    parser = argparse.ArgumentParser(
        description='Backtrader Run Script',
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # =============================================================================
    # 데이터 옵션 그룹 - 데이터 파일 및 포맷 설정
    # =============================================================================
    group = parser.add_argument_group(title='Data options')
    # Data options
    # 데이터 옵션들
    group.add_argument('--data', '-d', action='append', required=True,
                       help='Data files to be added to the system')

    # =============================================================================
    # Cerebro 옵션 그룹 - 백테스팅 엔진 설정
    # =============================================================================
    group = parser.add_argument_group(title='Cerebro options')
    group.add_argument(
        '--cerebro', '-cer',
        metavar='kwargs',
        required=False, const='', default='', nargs='?',
        help=('The argument can be specified with the following form:\n'
              '\n'
              '  - kwargs\n'
              '\n'
              '    Example: "preload=True" which set its to True\n'
              '\n'
              'The passed kwargs will be passed directly to the cerebro\n'
              'instance created for the execution\n'
              '\n'
              'The available kwargs to cerebro are:\n'
              '  - preload (default: True)\n'
              '  - runonce (default: True)\n'
              '  - maxcpus (default: None)\n'
              '  - stdstats (default: True)\n'
              '  - live (default: False)\n'
              '  - exactbars (default: False)\n'
              '  - preload (default: True)\n'
              '  - writer (default False)\n'
              '  - oldbuysell (default False)\n'
              '  - tradehistory (default False)\n')
    )

    group.add_argument('--nostdstats', action='store_true',
                       help='Disable the standard statistics observers')

    # =============================================================================
    # 데이터 포맷 및 시간 관련 옵션들
    # =============================================================================
    datakeys = list(DATAFORMATS)
    group.add_argument('--format', '--csvformat', '-c', required=False,
                       default='btcsv', choices=datakeys,
                       help='CSV Format')

    group.add_argument('--fromdate', '-f', required=False, default=None,
                       help='Starting date in YYYY-MM-DD[THH:MM:SS] format')

    group.add_argument('--todate', '-t', required=False, default=None,
                       help='Ending date in YYYY-MM-DD[THH:MM:SS] format')

    group.add_argument('--timeframe', '-tf', required=False, default='days',
                       choices=TIMEFRAMES.keys(),
                       help='Ending date in YYYY-MM-DD[THH:MM:SS] format')

    group.add_argument('--compression', '-cp', required=False, default=1,
                       type=int,
                       help='Ending date in YYYY-MM-DD[THH:MM:SS] format')

    # =============================================================================
    # 리샘플링 및 리플레이 옵션 (상호 배타적)
    # =============================================================================
    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--resample', '-rs', required=False, default=None,
                       help='resample with timeframe:compression values')

    group.add_argument('--replay', '-rp', required=False, default=None,
                       help='replay with timeframe:compression values')

    # =============================================================================
    # 훅 옵션 그룹 - Cerebro 커스터마이징
    # =============================================================================
    group.add_argument(
        '--hook', dest='hooks',
        action='append', required=False,
        metavar='module:hookfunction:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:hookfunction:kwargs\n'
              '\n'
              '    Example: mymod:myhook:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then hookfunction will be sought\n'
              'as the built-in cerebro method. Example:\n'
              '\n'
              '  - :addtz:tz=America/St_Johns\n'
              '\n'
              'If name is omitted, then the 1st function found in the\n'
              'mod will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs\n'
              '\n'
              'The function specified will be called, with cerebro\n'
              'instance passed as the first argument together with\n'
              'kwargs, if any were specified. This allows to customize\n'
              'cerebro, beyond options provided by this script\n\n')
    )

    # =============================================================================
    # 전략 옵션 그룹 - 전략 모듈 및 클래스 지정
    # =============================================================================
    # Module where to read the strategy from
    # 전략을 읽어올 모듈
    group = parser.add_argument_group(title='Strategy options')
    group.add_argument(
        '--strategy', '-st', dest='strategies',
        action='append', required=False,
        metavar='module:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in strategies module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st strategy found in the mod\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )

    # =============================================================================
    # 시그널 옵션 그룹 - 시그널 모듈 및 클래스 지정
    # =============================================================================
    # Module where to read the strategy from
    # 전략을 읽어올 모듈 (시그널용)
    group = parser.add_argument_group(title='Signals')
    group.add_argument(
        '--signal', '-sig', dest='signals',
        action='append', required=False,
        metavar='module:signaltype:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - signaltype:module:signaltype:classname:kwargs\n'
              '\n'
              '    Example: longshort+mymod:myclass:a=1,b=2\n'
              '\n'
              'signaltype may be ommited: longshort will be used\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'signaltype will be uppercased to match the defintions\n'
              'fromt the backtrader.signal module\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in signals module. Such as in:\n'
              '\n'
              '  - LONGSHORT::name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st signal found in the mod\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module:::kwargs')
    )

    # =============================================================================
    # 옵저버 및 통계 옵션 그룹 - 옵저버 모듈 및 클래스 지정
    # =============================================================================
    # Observers
    # 옵저버들
    group = parser.add_argument_group(title='Observers and statistics')
    group.add_argument(
        '--observer', '-ob', dest='observers',
        action='append', required=False,
        metavar='module:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in observers module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st observer found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )
    
    # =============================================================================
    # 분석기 옵션 그룹 - 성과 분석 도구 설정
    # =============================================================================
    # Analyzers
    # 분석기들
    group = parser.add_argument_group(title='Analyzers')
    group.add_argument(
        '--analyzer', '-an', dest='analyzers',
        action='append', required=False,
        metavar='module:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in analyzers module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st analyzer found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )

    # =============================================================================
    # 분석기 출력 옵션 (상호 배타적)
    # =============================================================================
    # Analyzer - Print
    # 분석기 - 출력
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--pranalyzer', '-pralyzer',
                       required=False, action='store_true',
                       help=('Automatically print analyzers'))

    group.add_argument('--ppranalyzer', '-ppralyzer',
                       required=False, action='store_true',
                       help=('Automatically PRETTY print analyzers'))

    # =============================================================================
    # 지표 옵션 그룹 - 기술적 지표 설정
    # =============================================================================
    # Indicators
    # 지표들
    group = parser.add_argument_group(title='Indicators')
    group.add_argument(
        '--indicator', '-ind', dest='indicators',
        metavar='module:name:kwargs',
        action='append', required=False,
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in analyzers module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st analyzer found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )

    # =============================================================================
    # 라이터 옵션 그룹 - 결과 출력 설정
    # =============================================================================
    # Writer
    # 라이터
    group = parser.add_argument_group(title='Writers')
    group.add_argument(
        '--writer', '-wr',
        dest='writers', metavar='kwargs', nargs='?',
        action='append', required=False, const='',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - kwargs\n'
              '\n'
              '    Example: a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'It creates a system wide writer which outputs run data\n'
              '\n'
              'Please see the documentation for the available kwargs')
    )

    # =============================================================================
    # 브로커/수수료 옵션 그룹 - 현금 및 수수료 체계 설정
    # =============================================================================
    # Broker/Commissions
    # 브로커/수수료
    group = parser.add_argument_group(title='Cash and Commission Scheme Args')
    group.add_argument('--cash', '-cash', required=False, type=float,
                       help='Cash to set to the broker')
    group.add_argument('--commission', '-comm', required=False, type=float,
                       help='Commission value to set')
    group.add_argument('--margin', '-marg', required=False, type=float,
                       help='Margin type to set')
    group.add_argument('--mult', '-mul', required=False, type=float,
                       help='Multiplier to use')

    group.add_argument('--interest', required=False, type=float,
                       default=None,
                       help='Credit Interest rate to apply (0.0x)')

    group.add_argument('--interest_long', action='store_true',
                       required=False, default=None,
                       help='Apply credit interest to long positions')

    # =============================================================================
    # 슬리피지 옵션들 - 거래 실행 시 가격 편차 설정
    # =============================================================================
    group.add_argument('--slip_perc', required=False, default=None,
                       type=float,
                       help='Enable slippage with a percentage value')
    group.add_argument('--slip_fixed', required=False, default=None,
                       type=float,
                       help='Enable slippage with a fixed point value')

    group.add_argument('--slip_open', required=False, action='store_true',
                       help='enable slippage for when matching opening prices')

    group.add_argument('--no-slip_match', required=False, action='store_true',
                       help=('Disable slip_match, ie: matching capped at \n'
                             'high-low if slippage goes over those limits'))
    group.add_argument('--slip_out', required=False, action='store_true',
                       help='with slip_match enabled, match outside high-low')

    # =============================================================================
    # 출력 플러싱 옵션 - Windows 시스템에서 유용
    # =============================================================================
    # Output flushing
    # 출력 플러싱
    group.add_argument('--flush', required=False, action='store_true',
                       help='flush the output - useful under win32 systems')

    # =============================================================================
    # 플롯 옵션 - 결과 시각화 설정
    # =============================================================================
    # Plot options
    # 플롯 옵션들
    parser.add_argument(
        '--plot', '-p', nargs='?',
        metavar='kwargs',
        default=False, const=True, required=False,
        help=('Plot the read data applying any kwargs passed\n'
              '\n'
              'For example:\n'
              '\n'
              '  --plot style="candle" (to plot candlesticks)\n')
    )

    # =============================================================================
    # 명령줄 인수 파싱 및 반환
    # =============================================================================
    if pargs:
        return parser.parse_args(pargs)

    return parser.parse_args()


# =============================================================================
# 메인 실행 블록
# =============================================================================
# 이 스크립트가 직접 실행될 때 btrun 함수를 호출합니다.
if __name__ == '__main__':
    btrun()
