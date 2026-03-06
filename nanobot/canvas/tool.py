"""Canvas tool for agent-driven visual workspace."""

from typing import Any

from loguru import logger

from nanobot.agent.tools.base import Tool


class CanvasTool(Tool):
    """Tool to control the Canvas visual workspace."""
    
    def __init__(self):
        self._server = None
    
    async def _get_server(self):
        """Lazy-load canvas server."""
        if self._server is None:
            from nanobot.canvas.server import CanvasServer
            self._server = CanvasServer.get_instance()
        return self._server
    
    @property
    def name(self) -> str:
        return "canvas"
    
    @property
    def description(self) -> str:
        return """Control the Canvas visual workspace to display content to the user.
Actions:
- set_content: Set markdown/HTML content to display
- set_title: Set the canvas title
- add_chart: Add a chart (line, bar, pie)
- add_table: Add a data table
- add_code: Add a code block with syntax highlighting
- add_image: Add an image by URL or base64
- clear: Clear all components
- reset: Reset canvas to initial state
- status: Get canvas status (connected clients)"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set_content", "set_title", "add_chart", "add_table", "add_code", "add_image", "clear", "reset", "status"],
                    "description": "Canvas action to perform"
                },
                "content": {
                    "type": "string",
                    "description": "Content to display (markdown/HTML for set_content, code for add_code)"
                },
                "title": {
                    "type": "string",
                    "description": "Title text"
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["line", "bar", "pie", "area"],
                    "description": "Type of chart"
                },
                "data": {
                    "type": "object",
                    "description": "Data for chart/table (labels, values, rows, columns)"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language for code highlighting"
                },
                "url": {
                    "type": "string",
                    "description": "Image URL"
                }
            },
            "required": ["action"]
        }
    
    async def execute(
        self,
        action: str,
        content: str = "",
        title: str = "",
        chart_type: str = "line",
        data: dict | None = None,
        language: str = "text",
        url: str = "",
        **kwargs: Any
    ) -> str:
        try:
            server = await self._get_server()
            
            if action == "status":
                return f"Canvas server running. Connected clients: {server.client_count}"
            
            if action == "set_content":
                if not content:
                    return "Error: content is required"
                await server.set_content(content)
                return f"Canvas content updated ({len(content)} chars)"
            
            if action == "set_title":
                if not title:
                    return "Error: title is required"
                await server.set_title(title)
                return f"Canvas title set to: {title}"
            
            if action == "add_chart":
                if not data:
                    return "Error: data is required for chart"
                component = {
                    "type": "chart",
                    "chart_type": chart_type,
                    "title": title,
                    "data": data,
                }
                await server.add_component(component)
                return f"Added {chart_type} chart to canvas"
            
            if action == "add_table":
                if not data:
                    return "Error: data is required for table"
                component = {
                    "type": "table",
                    "title": title,
                    "data": data,
                }
                await server.add_component(component)
                return f"Added table to canvas"
            
            if action == "add_code":
                if not content:
                    return "Error: content is required for code"
                component = {
                    "type": "code",
                    "language": language,
                    "content": content,
                    "title": title,
                }
                await server.add_component(component)
                return f"Added {language} code block to canvas"
            
            if action == "add_image":
                if not url:
                    return "Error: url is required for image"
                component = {
                    "type": "image",
                    "url": url,
                    "title": title,
                }
                await server.add_component(component)
                return f"Added image to canvas"
            
            if action == "clear":
                await server.clear_components()
                return "Canvas components cleared"
            
            if action == "reset":
                await server.reset()
                return "Canvas reset to initial state"
            
            return f"Unknown action: {action}"
            
        except Exception as e:
            logger.error("Canvas error: {}", e)
            return f"Canvas error: {str(e)}"
