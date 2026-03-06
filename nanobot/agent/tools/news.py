# coding=utf-8
"""
News fetching tool for RSS feeds and trending topics.

Inspired by TrendRadar project.
"""

import json
import html
import re
from datetime import datetime
from typing import Any
from pathlib import Path

from loguru import logger

from nanobot.agent.tools.base import Tool

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class NewsTool(Tool):
    """Tool to fetch news from RSS feeds and trending platforms."""

    # NewsNow API for trending topics
    NEWSNOW_API = "https://newsnow.busiyi.world/api/s"

    # Default headers (mimic real browser to avoid 403)
    # Note: Don't include Accept-Encoding to let httpx handle decompression automatically
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml,application/atom+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    
    # Headers for JSON API requests
    API_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    # Built-in RSS feeds (can be extended via config)
    BUILTIN_FEEDS = {
        "hacker-news": {
            "name": "Hacker News",
            "url": "https://hnrss.org/frontpage",
        },
        "github-blog": {
            "name": "GitHub Blog",
            "url": "https://github.blog/feed/",
        },
        "kubernetes": {
            "name": "Kubernetes",
            "url": "https://kubernetes.io/feed.xml",
        },
        "lobsters": {
            "name": "Lobsters",
            "url": "https://lobste.rs/rss",
        },
        "ruanyifeng": {
            "name": "阮一峰的网络日志",
            "url": "http://www.ruanyifeng.com/blog/atom.xml",
        },
    }

    # Popular trending platforms (via NewsNow API)
    TRENDING_PLATFORMS = {
        "weibo": "微博热搜",
        "zhihu": "知乎热榜",
        "baidu": "百度热搜",
        "douyin": "抖音热榜",
        "bilibili-hot-search": "B站热搜",
        "toutiao": "今日头条",
        "thepaper": "澎湃新闻",
        "wallstreetcn-hot": "华尔街见闻",
        "cls-hot": "财联社热门",
        "ifeng": "凤凰网",
        "tieba": "贴吧",
    }

    def __init__(self, custom_feeds: dict[str, dict] | None = None):
        """
        Initialize NewsTool.
        
        Args:
            custom_feeds: Custom RSS feeds from config, format:
                {"feed_id": {"name": "...", "url": "..."}}
        """
        self._custom_feeds = custom_feeds or {}

    @property
    def _feeds(self) -> dict[str, dict]:
        """Merge built-in and custom feeds."""
        feeds = dict(self.BUILTIN_FEEDS)
        feeds.update(self._custom_feeds)
        return feeds

    @classmethod
    def from_config(cls, config) -> "NewsTool":
        """Create NewsTool from config."""
        custom_feeds = {}
        if hasattr(config, "tools") and hasattr(config.tools, "news"):
            for feed in config.tools.news.feeds:
                if feed.enabled and feed.id and feed.url:
                    custom_feeds[feed.id] = {
                        "name": feed.name or feed.id,
                        "url": feed.url,
                    }
        return cls(custom_feeds=custom_feeds)

    @property
    def name(self) -> str:
        return "news"

    @property
    def description(self) -> str:
        platforms = ", ".join(self.TRENDING_PLATFORMS.keys())
        feeds = ", ".join(self._feeds.keys())
        return f"""Fetch news from RSS feeds or trending platforms.

Actions:
- rss: Fetch RSS feed (provide url or use preset: {feeds})
- trending: Get trending topics from platforms ({platforms})
- list_feeds: List available preset RSS feeds
- list_platforms: List available trending platforms"""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["rss", "trending", "list_feeds", "list_platforms"],
                    "description": "Action to perform",
                },
                "url": {
                    "type": "string",
                    "description": "RSS feed URL (for rss action)",
                },
                "feed_id": {
                    "type": "string",
                    "description": "Preset feed ID (for rss action, alternative to url)",
                },
                "platform": {
                    "type": "string",
                    "description": "Platform ID for trending action",
                },
                "max_items": {
                    "type": "integer",
                    "description": "Maximum items to return (default: 20)",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        url: str = "",
        feed_id: str = "",
        platform: str = "",
        max_items: int = 20,
        **kwargs: Any,
    ) -> str:
        if action == "list_feeds":
            return self._list_feeds()

        if action == "list_platforms":
            return self._list_platforms()

        if action == "rss":
            return await self._fetch_rss(url, feed_id, max_items)

        if action == "trending":
            return await self._fetch_trending(platform, max_items)

        return f"Unknown action: {action}"

    def _list_feeds(self) -> str:
        """List available preset RSS feeds."""
        lines = ["Available RSS feeds:\n"]
        for feed_id, info in self._feeds.items():
            lines.append(f"- {feed_id}: {info['name']}")
        lines.append("\nTip: Add custom feeds in ~/.nanobot/config.json under tools.news.feeds")
        return "\n".join(lines)

    def _list_platforms(self) -> str:
        """List available trending platforms."""
        lines = ["Available trending platforms:\n"]
        for pid, name in self.TRENDING_PLATFORMS.items():
            lines.append(f"- {pid}: {name}")
        return "\n".join(lines)

    async def _fetch_rss(self, url: str, feed_id: str, max_items: int) -> str:
        """Fetch and parse RSS feed."""
        if not HAS_FEEDPARSER:
            return "Error: feedparser not installed. Run: pip install feedparser"

        # Resolve URL
        if not url and feed_id:
            if feed_id in self._feeds:
                url = self._feeds[feed_id]["url"]
            else:
                return f"Unknown feed_id: {feed_id}. Use list_feeds to see available feeds."

        if not url:
            return "Error: url or feed_id is required for rss action"

        try:
            # Fetch feed content (follow redirects)
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.DEFAULT_HEADERS)
                resp.raise_for_status()
                content = resp.text

            # Parse feed
            feed = feedparser.parse(content)
            if feed.bozo and not feed.entries:
                return f"RSS parse error: {feed.bozo_exception}"

            # Extract items
            items = []
            for entry in feed.entries[:max_items]:
                item = self._parse_rss_entry(entry)
                if item:
                    items.append(item)

            if not items:
                return "No items found in feed"

            # Format output
            feed_title = feed.feed.get("title", "RSS Feed")
            lines = [f"📰 {feed_title} ({len(items)} items)\n"]

            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item['title']}")
                if item.get("published"):
                    lines.append(f"   📅 {item['published']}")
                if item.get("url"):
                    lines.append(f"   🔗 {item['url']}")
                if item.get("summary"):
                    summary = item["summary"][:150]
                    if len(item["summary"]) > 150:
                        summary += "..."
                    lines.append(f"   {summary}")
                lines.append("")

            return "\n".join(lines)

        except httpx.TimeoutException:
            return f"Timeout fetching RSS: {url}"
        except Exception as e:
            logger.error("RSS fetch error: {}", e)
            return f"Error fetching RSS: {e}"

    def _parse_rss_entry(self, entry: Any) -> dict | None:
        """Parse a single RSS entry."""
        title = self._clean_text(entry.get("title", ""))
        if not title:
            return None

        # Get URL
        url = entry.get("link", "")
        if not url:
            links = entry.get("links", [])
            for link in links:
                if link.get("rel") == "alternate":
                    url = link.get("href", "")
                    break
            if not url and links:
                url = links[0].get("href", "")

        # Get published date
        published = None
        date_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if date_struct:
            try:
                dt = datetime(*date_struct[:6])
                published = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

        # Get summary
        summary = self._clean_text(
            entry.get("summary") or entry.get("description", "")
        )

        return {
            "title": title,
            "url": url,
            "published": published,
            "summary": summary,
        }

    def _clean_text(self, text: str) -> str:
        """Clean HTML and normalize whitespace."""
        if not text:
            return ""
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    async def _fetch_trending(self, platform: str, max_items: int) -> str:
        """Fetch trending topics from a platform."""
        if not platform:
            return "Error: platform is required. Use list_platforms to see available platforms."

        if platform not in self.TRENDING_PLATFORMS:
            return f"Unknown platform: {platform}. Use list_platforms to see available platforms."

        try:
            url = f"{self.NEWSNOW_API}?id={platform}&latest"

            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.API_HEADERS)
                resp.raise_for_status()
                data = resp.json()

            status = data.get("status", "")
            if status not in ["success", "cache"]:
                return f"API error: {data.get('message', 'Unknown error')}"

            items = data.get("items", [])[:max_items]
            if not items:
                return f"No trending items for {platform}"

            # Format output
            platform_name = self.TRENDING_PLATFORMS[platform]
            status_info = "🔴 实时" if status == "success" else "📦 缓存"
            lines = [f"🔥 {platform_name} {status_info} ({len(items)} items)\n"]

            for i, item in enumerate(items, 1):
                title = item.get("title", "")
                if not title or isinstance(title, float):
                    continue
                url = item.get("url", "")
                lines.append(f"{i}. {title}")
                if url:
                    lines.append(f"   🔗 {url}")
                lines.append("")

            return "\n".join(lines)

        except httpx.TimeoutException:
            return f"Timeout fetching trending: {platform}"
        except Exception as e:
            logger.error("Trending fetch error: {}", e)
            return f"Error fetching trending: {e}"
