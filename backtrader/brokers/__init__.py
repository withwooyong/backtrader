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
# 브로커(Brokers) 패키지 초기화 모듈
# =============================================================================
# 이 모듈은 Backtrader에서 사용할 수 있는 다양한 브로커 구현체들을 제공합니다.
# 브로커는 주문 실행, 포지션 관리, 자금 관리 등의 핵심 기능을 담당합니다.
# 
# 주요 브로커 종류:
# - BackBroker: 백테스팅용 가상 브로커 (기본)
# - IBBroker: Interactive Brokers 연동 브로커
# - VCBroker: Visual Chart 연동 브로커
# - OandaBroker: OANDA 연동 브로커
# 
# 각 브로커는 실제 거래소나 중개사와의 연동을 통해
# 실시간 거래 및 백테스팅을 지원합니다.
# =============================================================================

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# The modules below should/must define __all__ with the objects wishes
# or prepend an "_" (underscore) to private classes/variables
# 아래 모듈들은 __all__을 정의하거나 private 클래스/변수에 "_"를 붙여야 합니다

# =============================================================================
# 기본 백테스팅 브로커 임포트
# =============================================================================
from .bbroker import BackBroker, BrokerBack

# =============================================================================
# Interactive Brokers 브로커 임포트 (선택적)
# =============================================================================
try:
    from .ibbroker import IBBroker
except ImportError:
    pass  # The user may not have ibpy installed (사용자가 ibpy를 설치하지 않았을 수 있음)

# =============================================================================
# Visual Chart 브로커 임포트 (선택적)
# =============================================================================
try:
    from .vcbroker import VCBroker
except ImportError:
    pass  # The user may not have something installed (사용자가 필요한 패키지를 설치하지 않았을 수 있음)

# =============================================================================
# OANDA 브로커 임포트 (선택적)
# =============================================================================
try:
    from .oandabroker import OandaBroker
except ImportError as e:
    pass  # The user may not have something installed (사용자가 필요한 패키지를 설치하지 않았을 수 있음)
