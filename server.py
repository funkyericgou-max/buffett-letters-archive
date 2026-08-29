#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巴菲特阅读器 · 本地同步服务
在本机 8765 端口提供静态文件服务，并接收阅读器自动推送的个人数据，
写入 reader/user-data.js。配合「同步到GitHub.bat」即可把个人阅读痕迹推到 GitHub。
"""
import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(ROOT, "reader", "user-data.js")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/save-user-data":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                data = json.loads(raw.decode("utf-8"))
                content = (
                    "// 巴菲特阅读器 · 个人数据同步文件（由本地同步服务自动生成，请勿手改）\n"
                    "// 提交到 GitHub 后，其他机器拉取并打开阅读器会自动合并。\n"
                    "window.BUFFETT_USER_DATA = "
                    + json.dumps(data, ensure_ascii=False, indent=2)
                    + ";\n"
                )
                with open(OUT_FILE, "w", encoding="utf-8") as fh:
                    fh.write(content)
                self.send_response(200)
                self._cors()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(400)
                self._cors()
                self.end_headers()
                self.wfile.write(("error: " + str(e)).encode("utf-8"))
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/reader/index.html")
            self.end_headers()
            return
        return super().do_GET()

    def log_message(self, fmt, *args):
        pass  # 静默日志，不刷屏


class ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    try:
        srv = ThreadingServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        print("启动失败（端口 %d 被占用？）：%s" % (PORT, e))
        input("按回车退出...")
        raise SystemExit(1)
    print("巴菲特阅读器同步服务已启动")
    print("  打开阅读器：http://localhost:%d/reader/index.html" % PORT)
    print("  个人数据将自动写入 reader/user-data.js")
    print("  （此窗口保持最小化运行，关闭即停止自动同步）")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("已停止")
