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
Backtrader 실행 도구 (bt-run.py)

이 스크립트는 Backtrader의 btrun 모듈을 실행하는 간단한 래퍼입니다.
명령줄에서 Backtrader 전략을 실행할 수 있는 편리한 진입점을 제공합니다.

사용법:
    python bt-run.py [btrun 옵션들]

btrun 모듈의 모든 기능과 옵션을 그대로 사용할 수 있습니다.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# Backtrader의 btrun 모듈 임포트
import backtrader.btrun as btrun


if __name__ == '__main__':
    # btrun 모듈의 메인 함수 실행
    # 모든 명령줄 인수들이 btrun 모듈로 전달됩니다
    btrun.btrun()
