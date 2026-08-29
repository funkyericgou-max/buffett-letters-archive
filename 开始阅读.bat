@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动巴菲特阅读器与本地同步服务...
start "巴菲特阅读器-同步服务" /min python "%~dp0server.py"
timeout /t 1 /nobreak >nul
start "" "%~dp0reader\index.html"
exit
