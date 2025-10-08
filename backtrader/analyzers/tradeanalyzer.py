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
# 거래 분석기(Trade Analyzer) 모듈
# =============================================================================
# 이 모듈은 백테스팅 결과의 모든 거래에 대한 상세한 통계를 제공합니다.
# 거래 분석기는 개별 거래의 성과를 분석하여 전략의 효율성을 평가하는 데 도움을 줍니다.
# 
# 주요 분석 항목:
# - 거래 수: 총 거래 수, 완료된 거래 수, 진행 중인 거래 수
# - 연속 성과: 연속 승/패 횟수 (현재/최장)
# - 수익/손실: 총 수익, 평균 수익, 최대 수익/손실
# - 포지션별 분석: 롱/숏 포지션별 통계
# - 거래 기간: 시장 체류 기간 (바 단위)
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.py3 import MAXINT


# =============================================================================
# TradeAnalyzer 클래스 - 거래 통계 분석기
# =============================================================================
# 이 클래스는 완료된 거래에 대한 상세한 통계를 제공하며, 
# 진행 중인 거래 수도 함께 추적합니다.
class TradeAnalyzer(Analyzer):
    '''
    Provides statistics on closed trades (keeps also the count of open ones)

      - Total Open/Closed Trades

      - Streak Won/Lost Current/Longest

      - ProfitAndLoss Total/Average

      - Won/Lost Count/ Total PNL/ Average PNL / Max PNL

      - Long/Short Count/ Total PNL / Average PNL / Max PNL

          - Won/Lost Count/ Total PNL/ Average PNL / Max PNL

      - Length (bars in the market)

        - Total/Average/Max/Min

        - Won/Lost Total/Average/Max/Min

        - Long/Short Total/Average/Max/Min

          - Won/Lost Total/Average/Max/Min

    Note:

      The analyzer uses an "auto"dict for the fields, which means that if no
      trades are executed, no statistics will be generated.

      In that case there will be a single field/subfield in the dictionary
      returned by ``get_analysis``, namely:

        - dictname['total']['total'] which will have a value of 0 (the field is
          also reachable with dot notation dictname.total.total
    '''
    
    def create_analysis(self):
        # =============================================================================
        # 분석 결과를 저장할 구조 생성
        # =============================================================================
        # AutoOrderedDict를 사용하여 점(.) 표기법 지원
        self.rets = AutoOrderedDict()
        self.rets.total.total = 0  # 총 거래 수 초기화

    def stop(self):
        # =============================================================================
        # 분석기 종료 시 정리
        # =============================================================================
        super(TradeAnalyzer, self).stop()
        self.rets._close()  # 점 표기법으로 더 이상 키 생성 불가

    def notify_trade(self, trade):
        # =============================================================================
        # 거래 상태 변화 알림 처리
        # =============================================================================
        if trade.justopened:
            # =============================================================================
            # 거래가 새로 열렸을 때
            # =============================================================================
            self.rets.total.total += 1      # 총 거래 수 증가
            self.rets.total.open += 1       # 진행 중인 거래 수 증가

        elif trade.status == trade.Closed:
            # =============================================================================
            # 거래가 완료되었을 때
            # =============================================================================
            trades = self.rets

            res = AutoDict()  # 이 거래의 결과를 저장할 딕셔너리
            # Trade just closed

            # =============================================================================
            # 거래 결과 기본 정보 설정
            # =============================================================================
            won = res.won = int(trade.pnlcomm >= 0.0)      # 수익 거래 여부 (1: 수익, 0: 손실)
            lost = res.lost = int(not won)                  # 손실 거래 여부 (1: 손실, 0: 수익)
            tlong = res.tlong = trade.long                  # 롱 포지션 여부
            tshort = res.tshort = not trade.long            # 숏 포지션 여부

            # =============================================================================
            # 거래 상태 업데이트
            # =============================================================================
            trades.total.open -= 1      # 진행 중인 거래 수 감소
            trades.total.closed += 1    # 완료된 거래 수 증가

            # =============================================================================
            # 연속 성과(Streak) 계산
            # =============================================================================
            for wlname in ['won', 'lost']:
                wl = res[wlname]

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                ls = trades.streak[wlname].longest or 0
                trades.streak[wlname].longest = \
                    max(ls, trades.streak[wlname].current)

            trpnl = trades.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.average = trades.pnl.gross.total / trades.total.closed
            trpnl.net.total += trade.pnlcomm
            trpnl.net.average = trades.pnl.net.total / trades.total.closed

            # Won/Lost statistics
            for wlname in ['won', 'lost']:
                wl = res[wlname]
                trwl = trades[wlname]

                trwl.total += wl  # won.total / lost.total

                trwlpnl = trwl.pnl
                pnlcomm = trade.pnlcomm * wl

                trwlpnl.total += pnlcomm
                trwlpnl.average = trwlpnl.total / (trwl.total or 1.0)

                wm = trwlpnl.max or 0.0
                func = max if wlname == 'won' else min
                trwlpnl.max = func(wm, pnlcomm)

            # Long/Short statistics
            for tname in ['long', 'short']:
                trls = trades[tname]
                ls = res['t' + tname]

                trls.total += ls  # long.total / short.total
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.average = trls.pnl.total / (trls.total or 1.0)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].average = \
                        trls.pnl[wlname].total / (trls[wlname] or 1.0)

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == 'won' else min
                    trls.pnl[wlname].max = func(wm, pnlcomm)

            # =============================================================================
            # 거래 기간(Length) 통계 계산
            # =============================================================================
            # Length
            # 거래 기간
            trades.len.total += trade.barlen
            trades.len.average = trades.len.total / trades.total.closed
            ml = trades.len.max or 0
            trades.len.max = max(ml, trade.barlen)

            ml = trades.len.min or MAXINT
            trades.len.min = min(ml, trade.barlen)

            # =============================================================================
            # 승/패별 거래 기간 통계
            # =============================================================================
            # Length Won/Lost
            # 승/패별 거래 기간
            for wlname in ['won', 'lost']:
                trwl = trades.len[wlname]
                wl = res[wlname]

                trwl.total += trade.barlen * wl
                trwl.average = trwl.total / (trades[wlname].total or 1.0)

                m = trwl.max or 0
                trwl.max = max(m, trade.barlen * wl)
                if trade.barlen * wl:
                    m = trwl.min or MAXINT
                    trwl.min = min(m, trade.barlen * wl)

            # =============================================================================
            # 롱/숏별 거래 기간 통계
            # =============================================================================
            # Length Long/Short
            # 롱/숏별 거래 기간
            for lsname in ['long', 'short']:
                trls = trades.len[lsname]  # trades.len.long
                ls = res['t' + lsname]  # tlong/tshort

                barlen = trade.barlen * ls

                trls.total += barlen  # trades.len.long.total
                total_ls = trades[lsname].total   # trades.long.total
                trls.average = trls.total / (total_ls or 1.0)

                # =============================================================================
                # 최대/최소 거래 기간
                # =============================================================================
                # max/min
                # 최대/최소
                m = trls.max or 0
                trls.max = max(m, barlen)
                m = trls.min or MAXINT
                trls.min = min(m, barlen or m)

                # =============================================================================
                # 롱/숏별 승/패 거래 기간 통계
                # =============================================================================
                for wlname in ['won', 'lost']:
                    wl = res[wlname]  # won/lost

                    barlen2 = trade.barlen * ls * wl

                    trls_wl = trls[wlname]  # trades.len.long.won
                    trls_wl.total += barlen2  # trades.len.long.won.total

                    trls_wl.average = \
                        trls_wl.total / (trades[lsname][wlname] or 1.0)

                    # =============================================================================
                    # 최대/최소 거래 기간
                    # =============================================================================
                    # max/min
                    # 최대/최소
                    m = trls_wl.max or 0
                    trls_wl.max = max(m, barlen2)
                    m = trls_wl.min or MAXINT
                    trls_wl.min = min(m, barlen2 or m)
