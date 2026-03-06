#!/usr/bin/env python
r"""
SearXNG Windows Startup Script
使用 nanobot 的虛擬環境運行 SearXNG

用法:
    .venv\Scripts\python.exe start_searxng.py
    
或者指定端口:
    .venv\Scripts\python.exe start_searxng.py --port 8888
"""
import os
import sys
import argparse

# SearXNG 路徑 (在 nanobot 項目目錄下)
SEARXNG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'searxng')

def main():
    parser = argparse.ArgumentParser(description='Start SearXNG server')
    parser.add_argument('--port', type=int, default=8888, help='Port to run on (default: 8888)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind (default: 127.0.0.1)')
    args = parser.parse_args()

    # 切換到 SearXNG 目錄
    os.chdir(SEARXNG_PATH)
    sys.path.insert(0, SEARXNG_PATH)

    # 設置環境變量
    os.environ['SEARXNG_SETTINGS_PATH'] = os.path.join(SEARXNG_PATH, 'searx', 'settings.yml')
    os.environ['SEARXNG_LIMITER'] = 'false'  # 禁用 bot detection
    
    print(f"Starting SearXNG on http://{args.host}:{args.port}")
    print(f"SearXNG path: {SEARXNG_PATH}")
    print("Press Ctrl+C to stop\n")

    # 啟動 Flask 應用
    from searx.webapp import app
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()
