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
Yahoo Finance 데이터 다운로드 도구 (yahoodownload.py)

이 스크립트는 Yahoo Finance에서 주식 데이터를 다운로드하는 도구입니다.
지정된 기간과 시간 프레임으로 주식 데이터를 CSV 형식으로 다운로드할 수 있습니다.

주요 기능:
- Yahoo Finance API를 통한 주식 데이터 다운로드
- 다양한 시간 프레임 지원 (일봉, 주봉, 월봉)
- 날짜 범위 지정 가능
- CSV 파일로 저장
- 자동 재시도 기능

사용법:
    python yahoodownload.py --ticker AAPL --fromdate 2020-01-01 --todate 2023-12-31 --outfile aapl.csv

필요 라이브러리:
    - requests: HTTP 요청을 위해 필요
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import argparse
import collections
import datetime
import io
import logging
import sys


# Python 2/3 호환성을 위한 URL 라이브러리 임포트
PY2 = sys.version_info.major == 2
if PY2:
    from urllib2 import urlopen
    from urllib import quote as urlquote
else:
    from urllib.request import urlopen
    from urllib.parse import quote as urlquote


# 로깅 설정
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging.INFO)


class YahooDownload(object):
    """
    Yahoo Finance에서 주식 데이터를 다운로드하는 클래스
    
    이 클래스는 Yahoo Finance의 새로운 API를 사용하여 주식 데이터를 다운로드합니다.
    crumb 기반 인증을 통해 데이터에 접근하고, 지정된 기간의 데이터를 CSV 형식으로 제공합니다.
    """
    # Yahoo Finance URL 템플릿
    urlhist = 'https://finance.yahoo.com/quote/{}/history'           # 히스토리 페이지 URL
    urldown = 'https://query1.finance.yahoo.com/v7/finance/download' # 다운로드 API URL
    retries = 3  # 재시도 횟수

    def __init__(self, ticker, fromdate, todate, period='d', reverse=False):
        """
        YahooDownload 인스턴스 초기화
        
        Args:
            ticker (str): 주식 티커 심볼 (예: 'AAPL', 'GOOGL')
            fromdate (datetime): 시작 날짜
            todate (datetime): 종료 날짜
            period (str): 시간 프레임 ('d'=일봉, 'w'=주봉, 'm'=월봉)
            reverse (bool): 데이터 순서 역순 여부
        """
        # requests 모듈 필수 확인
        try:
            import requests
        except ImportError:
            msg = ('새로운 Yahoo 데이터 피드를 사용하려면 requests 모듈이 필요합니다. '
                   'pip install requests 또는 다른 방법으로 설치해주세요.')
            raise Exception(msg)

        # 히스토리 페이지 URL 생성
        url = self.urlhist.format(ticker)

        # 세션 설정 (프록시 지원 준비)
        sesskwargs = dict()
        if False and self.p.proxies:  # 현재는 비활성화됨
            sesskwargs['proxies'] = self.p.proxies

        # crumb 값 추출을 위한 히스토리 페이지 접근
        crumb = None
        sess = requests.Session()
        for i in range(self.retries + 1):  # 최소 1회, 최대 재시도 횟수만큼 시도
            resp = sess.get(url, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue  # HTTP 오류 시 재시도

            # 응답 텍스트에서 crumb 값 추출
            txt = resp.text
            i = txt.find('CrumbStore')  # CrumbStore 문자열 찾기
            if i == -1:
                continue
            i = txt.find('crumb', i)    # crumb 키 찾기
            if i == -1:
                continue
            istart = txt.find('"', i + len('crumb') + 1)  # crumb 값 시작 위치
            if istart == -1:
                continue
            istart += 1
            iend = txt.find('"', istart)  # crumb 값 종료 위치
            if iend == -1:
                continue

            # crumb 값 추출 및 유니코드 이스케이프 처리
            crumb = txt[istart:iend]
            crumb = crumb.encode('ascii').decode('unicode-escape')
            break

        # crumb를 찾지 못한 경우 오류 처리
        if crumb is None:
            self.error = 'Crumb을 찾을 수 없습니다'
            self.f = None
            return

        # 다운로드 URL 형식: urldown/ticker?period1=posix1&period2=posix2&interval=1d&events=history&crumb=crumb

        # 실제 데이터 다운로드 시도
        urld = '{}/{}'.format(self.urldown, ticker)

        # URL 파라미터 구성
        urlargs = []
        posix = datetime.date(1970, 1, 1)  # Unix epoch 기준 날짜
        
        # 종료 날짜를 Unix timestamp로 변환
        if todate is not None:
            period2 = (todate.date() - posix).total_seconds()
            urlargs.append('period2={}'.format(int(period2)))

        # 시작 날짜를 Unix timestamp로 변환 (변수명 오타 수정: todate -> fromdate)
        if fromdate is not None:
            period1 = (fromdate.date() - posix).total_seconds()
            urlargs.append('period1={}'.format(int(period1)))

        # 시간 프레임 매핑
        intervals = {
            'd': '1d',   # 일봉
            'w': '1wk',  # 주봉
            'm': '1mo',  # 월봉
        }

        # URL 파라미터 추가
        urlargs.append('interval={}'.format(intervals[period]))  # 시간 간격
        urlargs.append('events=history')                         # 이벤트 타입
        urlargs.append('crumb={}'.format(crumb))                 # 인증 crumb

        # 최종 다운로드 URL 구성
        urld = '{}?{}'.format(urld, '&'.join(urlargs))
        
        # 데이터 다운로드 시도
        f = None
        for i in range(self.retries + 1):  # 최소 1회, 최대 재시도 횟수만큼 시도
            resp = sess.get(urld, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue  # HTTP 오류 시 재시도

            # 응답 Content-Type 확인
            ctype = resp.headers['Content-Type']
            if 'text/csv' not in ctype:
                self.error = '잘못된 Content-Type: %s' % ctype
                continue  # HTML이 반환된 경우 (잘못된 URL?)

            # 소켓에서 모든 데이터를 로컬 버퍼로 읽어들임
            try:
                # 응답 텍스트를 StringIO 객체로 변환
                f = io.StringIO(resp.text, newline=None)
            except Exception:
                continue  # 가능하면 다시 시도

            break  # 성공 시 루프 종료

        # 다운로드된 데이터 파일 저장
        self.datafile = f

    def writetofile(self, filename):
        """
        다운로드된 데이터를 파일에 저장하는 메서드
        
        Args:
            filename: 저장할 파일명 또는 파일 객체
        """
        # 다운로드된 데이터가 없으면 종료
        if not self.datafile:
            return

        # 파일명이 문자열인지 파일 객체인지 확인
        if not hasattr(filename, 'read'):
            # 문자열인 경우 파일을 열기
            f = io.open(filename, 'w')
        else:
            # 이미 파일 객체인 경우 그대로 사용
            f = filename

        # 데이터 파일의 처음으로 이동
        self.datafile.seek(0)
        
        # 모든 라인을 파일에 기록
        for line in self.datafile:
            f.write(line)

        # 파일 닫기
        f.close()


def parse_args():
    """
    명령줄 인수를 파싱하는 함수
    
    Returns:
        argparse.Namespace: 파싱된 명령줄 인수들
    """
    parser = argparse.ArgumentParser(
        description='Yahoo Finance에서 CSV 형식의 주식 데이터 다운로드')

    # 티커 심볼 (필수)
    parser.add_argument('--ticker', required=True,
                        help='다운로드할 주식의 티커 심볼 (예: AAPL, GOOGL)')

    # 데이터 순서 역순 여부
    parser.add_argument('--reverse', action='store_true', default=False,
                        help='다운로드된 파일의 순서를 역순으로 정렬')

    # 시간 프레임
    parser.add_argument('--timeframe', default='d',
                        help='시간 프레임: d -> 일봉, w -> 주봉, m -> 월봉')

    # 시작 날짜 (필수)
    parser.add_argument('--fromdate', required=True,
                        help='시작 날짜 (YYYY-MM-DD 형식)')

    # 종료 날짜 (필수)
    parser.add_argument('--todate', required=True,
                        help='종료 날짜 (YYYY-MM-DD 형식)')

    # 출력 파일명 (필수)
    parser.add_argument('--outfile', required=True,
                        help='출력 파일명')

    return parser.parse_args()


if __name__ == '__main__':
    """
    메인 실행 부분
    
    명령줄 인수를 파싱하고 Yahoo Finance에서 데이터를 다운로드하여 파일로 저장합니다.
    """
    # 명령줄 인수 파싱
    args = parse_args()

    logging.info('입력 파라미터 처리 중')
    
    # 시작 날짜 처리
    logging.info('시작 날짜 처리 중')
    try:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    except Exception as e:
        logging.error('시작 날짜 변환 실패')
        logging.error(str(e))
        sys.exit(1)

    # 종료 날짜 처리
    logging.info('종료 날짜 처리 중')
    try:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    except Exception as e:
        logging.error('종료 날짜 변환 실패')
        logging.error(str(e))
        sys.exit(1)

    # 역순 플래그 상태 확인
    logging.info('역순 플래그 상태 확인')
    reverse = args.reverse

    # Yahoo Finance에서 데이터 다운로드
    logging.info('Yahoo Finance에서 데이터 다운로드 중')
    try:
        yahoodown = YahooDownload(
            ticker=args.ticker,         # 티커 심볼
            fromdate=fromdate,          # 시작 날짜
            todate=todate,              # 종료 날짜
            period=args.timeframe,      # 시간 프레임
            reverse=reverse)            # 역순 여부

    except Exception as e:
        logging.error('Yahoo에서 데이터 다운로드 실패')
        logging.error(str(e))
        sys.exit(1)

    # 출력 파일 열기
    logging.info('출력 파일 열기')
    try:
        ofile = io.open(args.outfile, 'w')
    except IOError as e:
        logging.error('출력 파일 열기 오류')
        logging.error(str(e))
        sys.exit(1)

    # 다운로드된 데이터를 출력 파일에 저장
    logging.info('다운로드된 데이터를 출력 파일에 저장 중')
    try:
        yahoodown.writetofile(ofile)
    except Exception as e:
        logging.error('출력 파일 저장 실패')
        logging.error(str(e))
        sys.exit(1)

    logging.info('모든 작업이 성공적으로 완료되었습니다')
    sys.exit(0)
