# 小七 (Xiaoqi) - 自定義功能文檔

本文檔記錄了在 nanobot 基礎上添加的自定義功能。

## 🤖 Agent 身份

- 名稱：**小七 (Xiaoqi)**
- 基於 nanobot v0.1.4.post3

## 🔧 自定義功能

### 1. AWS Bedrock Provider

原生 AWS Bedrock 支持，使用 boto3 直接調用，無需 LiteLLM。

**配置示例：**
```json
{
  "agents": {
    "defaults": {
      "provider": "bedrock",
      "model": "global.anthropic.claude-opus-4-5-20251101-v1:0"
    }
  },
  "providers": {
    "bedrock": {
      "region": "us-east-1"
    }
  }
}
```

**文件：** `nanobot/providers/bedrock_provider.py`

### 2. SearXNG 搜索集成

支持本地 SearXNG 實例作為搜索後端，替代 Brave Search API。

**配置示例：**
```json
{
  "tools": {
    "web": {
      "search": {
        "provider": "searxng",
        "searxngUrl": "http://127.0.0.1:8888"
      }
    }
  }
}
```

**Windows 安裝：** 使用 [SearXNG for Windows](https://github.com/mbaozi/SearXNGforWindows/)

**文件：** 
- `nanobot/agent/tools/web.py` - WebSearchTool 支持 SearXNG
- `nanobot/config/schema.py` - WebSearchConfig 添加 provider 和 searxngUrl

### 3. NewsTool - 新聞聚合工具

支持 RSS feeds 和熱搜平台。

**內建熱搜平台：**
- 微博、知乎、百度、抖音、B站、今日頭條
- 澎湃新聞、華爾街見聞、財聯社、鳳凰網、貼吧

**內建 RSS feeds：**
- Hacker News、GitHub Blog、Kubernetes、Lobsters、阮一峰

**自定義 RSS 配置：**
```json
{
  "tools": {
    "news": {
      "feeds": [
        {"id": "aws-blog", "name": "AWS Blog", "url": "https://aws.amazon.com/blogs/aws/feed/", "enabled": true}
      ]
    }
  }
}
```

**文件：** `nanobot/agent/tools/news.py`

### 4. BrowserTool - 瀏覽器控制

使用 Playwright 控制瀏覽器。

**使用場景：**
- Canvas 預覽和截圖
- 前端頁面操作（點擊、填表、滾動）
- 本地 HTML 文件預覽

**限制：**
- 只允許訪問 localhost / 127.0.0.1 / file://
- 禁止訪問外部網站（使用 web_search + web_fetch 替代）

**文件：** `nanobot/agent/tools/browser.py`

### 5. CanvasTool - 畫布工具

WebSocket 畫布服務器，用於可視化輸出。

**文件：**
- `nanobot/canvas/tool.py`
- `nanobot/canvas/server.py`

## 📝 配置文件

配置文件位置：`~/.nanobot/config.json`

**完整配置示例：**
```json
{
  "agents": {
    "defaults": {
      "provider": "bedrock",
      "model": "global.anthropic.claude-opus-4-5-20251101-v1:0",
      "maxTokens": 16384
    }
  },
  "providers": {
    "bedrock": {
      "region": "us-east-1"
    }
  },
  "tools": {
    "web": {
      "search": {
        "provider": "searxng",
        "searxngUrl": "http://127.0.0.1:8888"
      }
    },
    "news": {
      "feeds": [
        {"id": "kubernetes", "name": "Kubernetes", "url": "https://kubernetes.io/feed.xml", "enabled": true},
        {"id": "aws-blog", "name": "AWS Blog", "url": "https://aws.amazon.com/blogs/aws/feed/", "enabled": true}
      ]
    }
  },
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "YOUR_APP_KEY",
      "clientSecret": "YOUR_APP_SECRET",
      "allowFrom": ["*"]
    }
  }
}
```

## 🗂️ Workspace 文件

位置：`~/.nanobot/workspace/`

- `SOUL.md` - Agent 人格和回覆規則
- `TOOLS.md` - 工具使用指南
- `AGENTS.md` - Agent 配置
- `memory/` - 長期記憶存儲

## 🚀 啟動命令

```bash
# 啟動 gateway（釘釘等渠道）
nanobot gateway

# CLI 模式
nanobot agent
```

## 📋 依賴

```bash
pip install playwright feedparser httpx boto3
playwright install chromium
```
