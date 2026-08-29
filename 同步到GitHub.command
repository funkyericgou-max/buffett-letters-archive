#!/bin/bash
# 巴菲特阅读器 - Mac 一键推送（等价于 Windows 的「同步到GitHub.bat」）
cd "$(dirname "$0")"

if [ ! -f "reader/user-data.js" ]; then
  echo "尚未生成同步文件，请先通过「开始阅读.command」打开阅读器。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 1
fi

git add "reader/user-data.js"
git commit -m "同步个人阅读数据" 2>/dev/null
git push

echo "完成！个人数据已推送到 GitHub。"
read -n 1 -s -r -p "按任意键退出..."
