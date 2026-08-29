@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "reader\user-data.js" (
  echo [提示] 尚未生成同步文件，请先通过「开始阅读.bat」打开阅读器，个人数据会自动生成。
  pause
  exit /b 1
)
git add "reader/user-data.js"
git commit -m "同步个人阅读数据" >nul 2>&1
git push
if errorlevel 1 (
  echo.
  echo [错误] git push 失败，请检查网络或 GitHub 登录状态。
  pause
  exit /b 1
)
echo.
echo 完成！个人数据已推送到 GitHub。
pause
