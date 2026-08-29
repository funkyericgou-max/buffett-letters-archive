#!/bin/bash
# 巴菲特阅读器 - Mac 一键启动（等价于 Windows 的「开始阅读.bat」）
# 自动启动本地同步服务，并打开阅读器。
cd "$(dirname "$0")"

if ! curl -s -o /dev/null --max-time 2 "http://localhost:8765/"; then
  echo "启动本地同步服务..."
  nohup python3 server.py >/dev/null 2>&1 &
  sleep 1
fi

open "http://localhost:8765/reader/index.html"
