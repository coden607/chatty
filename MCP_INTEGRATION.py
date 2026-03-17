#!/usr/bin/env python3
"""
CHATTY MCP (Model Context Protocol) Integration
Standardized tool connectivity for AI agents - Anthropic's open protocol
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }


@dataclass
class MCPServer:
    """MCP Server configuration and connection"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    process: Optional[subprocess.Popen] = None
    tools: List[MCPTool] = field(default_factory=list)
    is_connected: bool = False
    
    async def connect(self) -> bool:
        """Start the MCP server process via stdio"""
        try:
            env = os.environ.copy()
            env.update(self.env)
            
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Initialize handshake
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "chatty-mcp-client", "version": "1.0.0"}
                }
            }
            
            await self._send_message(init_request)
            response = await self._read_message()
            
            if response and "result" in response:
                self.is_connected = True
                logger.info(f"✅ MCP Server '{self.name}' connected")
                await self._discover_tools()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server '{self.name}': {e}")
            return False
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send JSON-RPC message to server"""
        if self.process and self.process.stdin:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data)
            self.process.stdin.flush()
    
    async def _read_message(self) -> Optional[Dict[str, Any]]:
        """Read JSON-RPC message from server"""
        if self.process and self.process.stdout:
            try:
                line = self.process.stdout.readline()
                if line:
                    return json.loads(line)
            except json.JSONDecodeError:
                pass
        return None
    
    async def _discover_tools(self):
        """Discover available tools from server"""
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        await self._send_message(tools_request)
        response = await self._read_message()
        
        if response and "result" in response:
            tools_data = response["result"].get("tools", [])
            self.tools = [
                MCPTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server_name=self.name
                )
                for t in tools_data
            ]
            logger.info(f"🔧 Discovered {len(self.tools)} tools from '{self.name}'")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on this server"""
        if not self.is_connected:
            raise RuntimeError(f"MCP server '{self.name}' not connected")
        
        tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_message(tool_request)
        response = await self._read_message()
        
        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"Tool call failed: {response['error']}")
        
        return {}
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.process:
            self.process.terminate()
            self.process = None
            self.is_connected = False
            logger.info(f"🔌 MCP Server '{self.name}' disconnected")


class MCPClient:
    """
    MCP Client for CHATTY - Connects to any MCP server
    Provides standardized access to 1000+ tools
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.all_tools: List[MCPTool] = []
        
    def register_server(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """Register an MCP server configuration"""
        self.servers[name] = MCPServer(
            name=name,
            command=command,
            args=args or [],
            env=env or {}
        )
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered servers"""
        results = {}
        for name, server in self.servers.items():
            results[name] = await server.connect()
        
        # Aggregate all tools
        self.all_tools = []
        for server in self.servers.values():
            if server.is_connected:
                self.all_tools.extend(server.tools)
        
        logger.info(f"✅ MCP Client: {len(self.all_tools)} total tools available")
        return results
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get tools formatted for LLM function calling"""
        return [tool.to_dict() for tool in self.all_tools]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name (finds the right server)"""
        for server in self.servers.values():
            if any(t.name == tool_name for t in server.tools):
                return await server.call_tool(tool_name, arguments)
        
        raise ValueError(f"Tool '{tool_name}' not found in any MCP server")
    
    async def disconnect_all(self):
        """Disconnect from all servers"""
        for server in self.servers.values():
            await server.disconnect()
        self.all_tools = []


class ChattyMCPTools:
    """
    Pre-configured MCP tool collections for CHATTY
    """
    
    @staticmethod
    def filesystem_tools(root_path: str = "/home/coden809/Projects/chatty") -> MCPServer:
        """File system operations via MCP"""
        return MCPServer(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", root_path],
        )
    
    @staticmethod
    def sqlite_tools(db_path: str = "/home/coden809/Projects/chatty/chatty.db") -> MCPServer:
        """SQLite database operations via MCP"""
        return MCPServer(
            name="sqlite",
            command="uvx",
            args=["mcp-server-sqlite", "--db-path", db_path],
        )
    
    @staticmethod
    def brave_search_tools(api_key: str = None) -> MCPServer:
        """Web search via Brave"""
        return MCPServer(
            name="brave-search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": api_key or os.getenv("BRAVE_API_KEY", "")}
        )
    
    @staticmethod
    def github_tools(token: str = None) -> MCPServer:
        """GitHub operations via MCP"""
        return MCPServer(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": token or os.getenv("GITHUB_TOKEN", "")}
        )
    
    @staticmethod
    def fetch_tools() -> MCPServer:
        """Web fetching via MCP"""
        return MCPServer(
            name="fetch",
            command="uvx",
            args=["mcp-server-fetch"],
        )
    
    @staticmethod
    def git_tools() -> MCPServer:
        """Git operations via MCP"""
        return MCPServer(
            name="git",
            command="uvx",
            args=["mcp-server-git"],
        )
    
    @staticmethod
    def postgres_tools(connection_string: str = None) -> MCPServer:
        """PostgreSQL operations via MCP"""
        return MCPServer(
            name="postgres",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres", connection_string or os.getenv("DATABASE_URL", "")]
        )


class MCPEnhancedAgent:
    """
    An agent enhanced with MCP capabilities
    Can use any MCP tool dynamically
    """
    
    def __init__(self, name: str, mcp_client: MCPClient):
        self.name = name
        self.mcp_client = mcp_client
        self.conversation_history = []
        
    async def execute_with_tools(self, task: str) -> Dict[str, Any]:
        """
        Execute a task using available MCP tools
        """
        from CHATTY_MODEL_ROUTER import router
        
        # Get available tools
        tools = self.mcp_client.get_tools_for_llm()
        
        # Build system prompt with tool descriptions
        system_prompt = f"""You are {self.name}, an AI agent with access to tools.
Available tools:
{json.dumps([t['function']['name'] for t in tools], indent=2)}

Use the appropriate tool to complete the task."""
        
        # Call LLM with tools
        response = await router.generate(
            prompt=task,
            system_prompt=system_prompt,
            tools=tools if tools else None
        )
        
        # Check if tool call was requested
        if "tool_calls" in response:
            tool_calls = response["tool_calls"]
            results = []
            
            for call in tool_calls:
                tool_name = call.get("name") or call.get("function", {}).get("name")
                arguments = call.get("arguments") or call.get("function", {}).get("arguments", {})
                
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                
                try:
                    result = await self.mcp_client.call_tool(tool_name, arguments)
                    results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "error": str(e)
                    })
            
            return {
                "agent": self.name,
                "task": task,
                "tool_calls": results,
                "status": "completed"
            }
        
        return {
            "agent": self.name,
            "task": task,
            "response": response,
            "status": "completed"
        }


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    """Get or create global MCP client"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        
        # Register default servers
        _mcp_client.servers["filesystem"] = ChattyMCPTools.filesystem_tools()
        _mcp_client.servers["fetch"] = ChattyMCPTools.fetch_tools()
        _mcp_client.servers["git"] = ChattyMCPTools.git_tools()
        
        # Optional servers (require API keys)
        if os.getenv("BRAVE_API_KEY"):
            _mcp_client.servers["brave-search"] = ChattyMCPTools.brave_search_tools()
        
        if os.getenv("GITHUB_TOKEN"):
            _mcp_client.servers["github"] = ChattyMCPTools.github_tools()
        
        await _mcp_client.connect_all()
    
    return _mcp_client


# Convenience functions for common MCP operations
async def mcp_read_file(file_path: str) -> str:
    """Read a file using MCP filesystem tool"""
    client = await get_mcp_client()
    result = await client.call_tool("read_file", {"path": file_path})
    return result.get("content", "")


async def mcp_list_directory(dir_path: str) -> List[str]:
    """List directory contents using MCP"""
    client = await get_mcp_client()
    result = await client.call_tool("list_directory", {"path": dir_path})
    return result.get("entries", [])


async def mcp_search_web(query: str) -> Dict[str, Any]:
    """Search the web using Brave MCP tool"""
    client = await get_mcp_client()
    return await client.call_tool("brave_web_search", {"query": query})


async def mcp_fetch_url(url: str) -> str:
    """Fetch URL content using MCP fetch tool"""
    client = await get_mcp_client()
    result = await client.call_tool("fetch", {"url": url})
    return result.get("content", "")


if __name__ == "__main__":
    # Test MCP integration
    async def test():
        print("🧪 Testing MCP Integration...")
        
        client = await get_mcp_client()
        print(f"✅ Connected to {len(client.servers)} MCP servers")
        print(f"✅ {len(client.all_tools)} tools available")
        
        # List available tools
        print("\n🔧 Available Tools:")
        for tool in client.all_tools:
            print(f"  - {tool.name} ({tool.server_name})")
        
        # Test filesystem tool
        try:
            entries = await mcp_list_directory("/home/coden809/Projects/chatty")
            print(f"\n📁 Root directory entries: {len(entries)}")
        except Exception as e:
            print(f"⚠️ Filesystem test: {e}")
        
        await client.disconnect_all()
        print("\n✅ MCP test complete")
    
    asyncio.run(test())
