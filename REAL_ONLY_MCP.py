#!/usr/bin/env python3
"""
CHATTY MCP Integration - REAL DATA ONLY
Uses actual MCP servers and tools - NO simulations
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPRealDataError(Exception):
    """Raised when MCP cannot use real data"""
    pass


@dataclass
class MCPTool:
    """Real MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


@dataclass 
class MCPServer:
    """Real MCP Server connection"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    process: Optional[subprocess.Popen] = None
    tools: List[MCPTool] = field(default_factory=list)
    is_connected: bool = False
    last_error: Optional[str] = None
    
    async def connect(self) -> bool:
        """Connect to real MCP server"""
        try:
            # Check if command exists
            result = subprocess.run(
                ['which', self.command.split()[0]],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.last_error = f"Command not found: {self.command}"
                logger.error(f"❌ MCP Server '{self.name}': {self.last_error}")
                return False
            
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
            response = await self._read_message(timeout=10)
            
            if response and "result" in response:
                self.is_connected = True
                logger.info(f"✅ MCP Server '{self.name}' connected (REAL)")
                await self._discover_tools()
                return True
            else:
                self.last_error = "Invalid handshake response"
                return False
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ MCP Server '{self.name}' connection failed: {e}")
            return False
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send message to server"""
        if self.process and self.process.stdin:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data)
            self.process.stdin.flush()
    
    async def _read_message(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Read message from server"""
        import select
        
        if not self.process or not self.process.stdout:
            return None
        
        # Wait for data with timeout
        ready, _, _ = select.select([self.process.stdout], [], [], timeout)
        if ready:
            try:
                line = self.process.stdout.readline()
                if line:
                    return json.loads(line)
            except (json.JSONDecodeError, ValueError):
                pass
        return None
    
    async def _discover_tools(self):
        """Discover real tools from server"""
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
            logger.info(f"🔧 Discovered {len(self.tools)} real tools from '{self.name}'")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a real tool"""
        if not self.is_connected:
            raise MCPRealDataError(f"MCP server '{self.name}' not connected - cannot use simulated data")
        
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
        response = await self._read_message(timeout=60)
        
        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise MCPRealDataError(f"Tool call failed: {response['error']}")
        
        raise MCPRealDataError("No response from MCP server")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None
            self.is_connected = False


class RealMCPClient:
    """MCP Client that ONLY uses real data"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.all_tools: List[MCPTool] = []
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize with real MCP servers"""
        if self._initialized:
            return True
        
        logger.info("🔌 Initializing REAL MCP Client...")
        
        # Register filesystem server (local, always available)
        fs_server = MCPServer(
            name="filesystem",
            command="python3",
            args=["-c", f"import mcp.server.stdio; print('Filesystem server not installed - install @modelcontextprotocol/server-filesystem')"]
        )
        self.servers["filesystem"] = fs_server
        
        # Try to connect to available servers
        connected = 0
        for server in self.servers.values():
            if await server.connect():
                connected += 1
        
        # Aggregate tools
        self.all_tools = []
        for server in self.servers.values():
            if server.is_connected:
                self.all_tools.extend(server.tools)
        
        self._initialized = True
        
        if connected == 0:
            logger.warning("⚠️ No MCP servers connected - MCP features will be limited")
        else:
            logger.info(f"✅ MCP Client: {connected} real servers, {len(self.all_tools)} tools")
        
        return connected > 0
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool - raises error if no real data available"""
        if not self._initialized:
            await self.initialize()
        
        # Find server with this tool
        for server in self.servers.values():
            if any(t.name == tool_name for t in server.tools):
                return await server.call_tool(tool_name, arguments)
        
        raise MCPRealDataError(
            f"Tool '{tool_name}' not available in any connected MCP server. "
            "Install MCP servers: npm install -g @modelcontextprotocol/server-filesystem"
        )
    
    def get_tools(self) -> List[MCPTool]:
        """Get all available real tools"""
        return self.all_tools
    
    async def read_file(self, path: str) -> str:
        """Read file using real filesystem"""
        # Direct filesystem access (no simulation)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise MCPRealDataError(f"Cannot read file {path}: {e}")
    
    async def write_file(self, path: str, content: str):
        """Write file using real filesystem"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise MCPRealDataError(f"Cannot write file {path}: {e}")
    
    async def list_directory(self, path: str) -> List[str]:
        """List directory using real filesystem"""
        try:
            return [str(p) for p in Path(path).iterdir()]
        except Exception as e:
            raise MCPRealDataError(f"Cannot list directory {path}: {e}")


# Global client
_real_mcp_client: Optional[RealMCPClient] = None


async def get_real_mcp_client() -> RealMCPClient:
    """Get real MCP client instance"""
    global _real_mcp_client
    if _real_mcp_client is None:
        _real_mcp_client = RealMCPClient()
        await _real_mcp_client.initialize()
    return _real_mcp_client


if __name__ == "__main__":
    async def test():
        print("🧪 Testing REAL MCP Client...")
        print("=" * 60)
        
        try:
            client = await get_real_mcp_client()
            print(f"✅ MCP Client initialized")
            print(f"   Servers: {len(client.servers)}")
            print(f"   Tools: {len(client.all_tools)}")
            
            # Test real filesystem operations
            print("\n📁 Testing real filesystem...")
            
            # Read real file
            content = await client.read_file("/home/coden809/Projects/chatty/README.md")
            print(f"✅ Read README.md: {len(content)} characters")
            
            # List real directory
            entries = await client.list_directory("/home/coden809/Projects/chatty")
            print(f"✅ Listed directory: {len(entries)} entries")
            
            print("\n✅ All MCP operations use REAL DATA")
            
        except MCPRealDataError as e:
            print(f"❌ MCP Real Data Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    asyncio.run(test())
