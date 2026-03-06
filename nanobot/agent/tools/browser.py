"""Browser control tool using Playwright CDP."""

import asyncio
import base64
import json
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.tools.base import Tool

try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None


class BrowserManager:
    """Singleton browser manager for CDP control."""
    
    _instance: "BrowserManager | None" = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self._playwright: "Playwright | None" = None
        self._browser: "Browser | None" = None
        self._page: "Page | None" = None
        self._screenshots_dir = Path.home() / ".nanobot" / "browser" / "screenshots"
        self._screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def get_instance(cls) -> "BrowserManager":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = BrowserManager()
            return cls._instance
    
    async def ensure_browser(self) -> "Page":
        """Ensure browser is running and return the page."""
        if self._page and not self._page.is_closed():
            return self._page
        
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        if not self._browser or not self._browser.is_connected():
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ]
            )
        
        if not self._page or self._page.is_closed():
            self._page = await self._browser.new_page()
            await self._page.set_viewport_size({"width": 1280, "height": 800})
        
        return self._page
    
    async def close(self):
        """Close browser and cleanup."""
        if self._page:
            await self._page.close()
            self._page = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


class BrowserTool(Tool):
    """Tool to control browser via CDP."""
    
    # Only allow navigate to these domains (for canvas preview)
    ALLOWED_DOMAINS = [
        "localhost", "127.0.0.1",  # Local development / Canvas
        "file://",  # Local HTML files
    ]
    
    def __init__(self):
        self._manager: BrowserManager | None = None
    
    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is allowed for browser navigation (only localhost/canvas)."""
        url_lower = url.lower()
        for domain in self.ALLOWED_DOMAINS:
            if domain in url_lower:
                return True
        return False
    
    @property
    def name(self) -> str:
        return "browser"
    
    @property
    def description(self) -> str:
        return """Control a browser for Canvas preview and local files ONLY.

⚠️ Browser navigation is LIMITED to localhost/canvas only!
- For searching → use web_search (SearXNG)
- For reading web pages → use web_fetch

Allowed actions:
- navigate: ONLY to localhost/127.0.0.1 (for Canvas preview)
- screenshot: Take screenshot of current page
- click/type/scroll: Interact with page elements
- content: Get page text
- close: Close browser

DO NOT use browser for external websites - use web_search + web_fetch instead!"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "screenshot", "click", "type", "scroll", "evaluate", "content", "close"],
                    "description": "Browser action to perform"
                },
                "url": {
                    "type": "string",
                    "description": "URL to navigate to (for navigate action)"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for element (for click/type actions)"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type (for type action)"
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate (for click action without selector)"
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate (for click action without selector)"
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "Scroll direction (for scroll action)"
                },
                "amount": {
                    "type": "integer",
                    "description": "Scroll amount in pixels (for scroll action)"
                },
                "script": {
                    "type": "string",
                    "description": "JavaScript to evaluate (for evaluate action)"
                }
            },
            "required": ["action"]
        }
    
    async def execute(
        self,
        action: str,
        url: str = "",
        selector: str = "",
        text: str = "",
        x: int | None = None,
        y: int | None = None,
        direction: str = "down",
        amount: int = 500,
        script: str = "",
        **kwargs: Any
    ) -> str:
        if not PLAYWRIGHT_AVAILABLE:
            return "Error: Playwright not installed. Run: pip install playwright && playwright install chromium"
        
        try:
            self._manager = await BrowserManager.get_instance()
            
            if action == "close":
                await self._manager.close()
                return "Browser closed"
            
            page = await self._manager.ensure_browser()
            
            if action == "navigate":
                if not url:
                    return "Error: url is required for navigate action"
                if not self._is_allowed_url(url):
                    return f"""Error: Browser 只能訪問 localhost（Canvas 預覽）！

外部網站請使用：
- 搜索信息 → web_search(query="...")
- 讀取網頁 → web_fetch(url="...")

Blocked: {url}"""
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                title = await page.title()
                return f"Navigated to {url}\nTitle: {title}"
            
            elif action == "screenshot":
                screenshot_path = self._manager._screenshots_dir / f"screenshot_{int(asyncio.get_event_loop().time() * 1000)}.png"
                await page.screenshot(path=str(screenshot_path), full_page=False)
                return f"Screenshot saved to {screenshot_path}"
            
            elif action == "click":
                if selector:
                    await page.click(selector, timeout=5000)
                    return f"Clicked element: {selector}"
                elif x is not None and y is not None:
                    await page.mouse.click(x, y)
                    return f"Clicked at coordinates ({x}, {y})"
                else:
                    return "Error: selector or (x, y) coordinates required for click"
            
            elif action == "type":
                if not selector:
                    return "Error: selector is required for type action"
                if not text:
                    return "Error: text is required for type action"
                await page.fill(selector, text, timeout=5000)
                return f"Typed text into {selector}"
            
            elif action == "scroll":
                delta = amount if direction == "down" else -amount
                await page.mouse.wheel(0, delta)
                return f"Scrolled {direction} by {amount}px"
            
            elif action == "evaluate":
                if not script:
                    return "Error: script is required for evaluate action"
                result = await page.evaluate(script)
                return f"Result: {json.dumps(result, ensure_ascii=False, default=str)}"
            
            elif action == "content":
                content = await page.inner_text("body")
                # Truncate if too long
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                return content
            
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            logger.error("Browser error: {}", e)
            return f"Browser error: {str(e)}"
