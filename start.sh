#!/bin/bash
# 啟動 SearXNG 和 nanobot
cd /d/Users/zyzhan/projects/nanobot
source .venv/Scripts/activate

# 後台啟動 SearXNG
python start_searxng.py --port 8888 &

# 啟動 nanobot
python -m nanobot
