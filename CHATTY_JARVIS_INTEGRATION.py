#!/usr/bin/env python3
"""
CHATTY Integration with Continuous Mode
===============================================
Integrates CHATTY with the 24/7 continuous automation system.
CHATTY can now:
- Monitor system status in real-time
- Dispatch tasks to Agent Zero fleet
- Trigger autonomous workflows
- Receive alerts and notifications
- Control continuous mode operations
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SystemStatus:
    """Current system status snapshot"""
    timestamp: str
    components: Dict[str, Any]
    key_rotation_index: int
    alerts: List[str]


class JarvisContinuousBridge:
    """Bridge between CHATTY and CHATTY Continuous Mode"""
    
    def __init__(self):
        self.chatty_root = Path(__file__).parent
        self.metrics_file = self.chatty_root / "generated_content" / "continuous_metrics.json"
        self.session_file = self.chatty_root / "generated_content" / "chatty_session.json"
        self.last_metrics = None
        self.alert_handlers = []
    
    async def get_system_status(self) -> Optional[SystemStatus]:
        """Get current continuous mode status"""
        try:
            if not self.metrics_file.exists():
                return None
            
            with open(self.metrics_file) as f:
                data = json.load(f)
            
            return SystemStatus(
                timestamp=data.get("timestamp", datetime.now().isoformat()),
                components=data.get("components", {}),
                key_rotation_index=data.get("key_rotation_index", 0),
                alerts=data.get("alerts", [])
            )
        except Exception as e:
            print(f"Error reading metrics: {e}")
            return None
    
    async def is_continuous_mode_running(self) -> bool:
        """Check if continuous mode is active"""
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "chatty-continuous"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and "active" in result.stdout
        except:
            return False
    
    async def start_continuous_mode(self) -> bool:
        """Start CHATTY continuous mode"""
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "--user", "start", "chatty-continuous"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to start continuous mode: {e}")
            return False
    
    async def stop_continuous_mode(self) -> bool:
        """Stop CHATTY continuous mode"""
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "--user", "stop", "chatty-continuous"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to stop continuous mode: {e}")
            return False
    
    async def dispatch_to_agents(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a task to the Agent Zero fleet"""
        # Save task to queue file
        task_queue_file = self.chatty_root / "generated_content" / "agent_task_queue.json"
        
        try:
            tasks = []
            if task_queue_file.exists():
                with open(task_queue_file) as f:
                    tasks = json.load(f)
            
            task_entry = {
                "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(tasks)}",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "task": task
            }
            tasks.append(task_entry)
            
            with open(task_queue_file, 'w') as f:
                json.dump(tasks, f, indent=2)
            
            return {
                "success": True,
                "task_id": task_entry["id"],
                "message": "Task dispatched to Agent Zero fleet"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_component_status(self, component_name: str) -> Optional[Dict]:
        """Get status of a specific component"""
        status = await self.get_system_status()
        if not status:
            return None
        return status.components.get(component_name)
    
    def format_status_for_display(self, status: SystemStatus) -> str:
        """Format system status for CHATTY display"""
        lines = []
        lines.append("📊 CHATTY Continuous Mode Status")
        lines.append("═" * 60)
        lines.append(f"Last Update: {status.timestamp}")
        lines.append(f"Key Rotations: {status.key_rotation_index}")
        lines.append("")
        
        lines.append("Components:")
        for name, comp in status.components.items():
            icon = "🟢" if comp.get("running") else "🔴"
            lines.append(f"  {icon} {name}")
            if comp.get("metrics"):
                for k, v in list(comp["metrics"].items())[:3]:
                    lines.append(f"      {k}: {v}")
        
        if status.alerts:
            lines.append("")
            lines.append("⚠️  Alerts:")
            for alert in status.alerts:
                lines.append(f"  - {alert}")
        
        return "\n".join(lines)


class JarvisAutonomousController:
    """Allows CHATTY to control autonomous operations"""
    
    def __init__(self, bridge: JarvisContinuousBridge):
        self.bridge = bridge
        self.autonomous_tasks = []
        self.running = False
    
    async def start_autonomous_monitoring(self):
        """Start monitoring system autonomously"""
        self.running = True
        print("🤖 CHATTY autonomous monitoring started")
        
        while self.running:
            try:
                status = await self.bridge.get_system_status()
                if status:
                    # Check for issues
                    for name, comp in status.components.items():
                        if not comp.get("running"):
                            print(f"⚠️  Alert: {name} is not running")
                        if comp.get("error_count", 0) > 5:
                            print(f"🚨 Warning: {name} has {comp['error_count']} errors")
                
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    def stop_autonomous_monitoring(self):
        """Stop autonomous monitoring"""
        self.running = False
        print("🛑 CHATTY autonomous monitoring stopped")
    
    async def execute_workflow(self, workflow_name: str, params: Dict = None):
        """Execute a predefined workflow"""
        workflows = {
            "system_health_check": self._workflow_health_check,
            "key_rotation": self._workflow_key_rotation,
            "file_learning": self._workflow_file_learning,
            "agent_deployment": self._workflow_agent_deployment,
        }
        
        if workflow_name in workflows:
            return await workflows[workflow_name](params or {})
        else:
            return {"error": f"Unknown workflow: {workflow_name}"}
    
    async def _workflow_health_check(self, params: Dict) -> Dict:
        """Health check workflow"""
        status = await self.bridge.get_system_status()
        if not status:
            return {"status": "error", "message": "Could not get system status"}
        
        issues = []
        for name, comp in status.components.items():
            if not comp.get("running"):
                issues.append(f"{name} is down")
        
        return {
            "status": "healthy" if not issues else "degraded",
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _workflow_key_rotation(self, params: Dict) -> Dict:
        """Manual key rotation workflow"""
        # Trigger key rotation via systemd
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "--user", "start", "chatty-key-rotation"],
                capture_output=True,
                text=True
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _workflow_file_learning(self, params: Dict) -> Dict:
        """File learning workflow"""
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "No file_path specified"}
        
        # This would trigger the file learning system
        return {
            "status": "dispatched",
            "file": file_path,
            "message": "File learning task dispatched"
        }
    
    async def _workflow_agent_deployment(self, params: Dict) -> Dict:
        """Deploy agents workflow"""
        agent_types = params.get("agent_types", ["worker"])
        task = {
            "type": "deploy_fleet",
            "agent_types": agent_types,
            "coordination_protocol": params.get("protocol", "zero_shot")
        }
        return await self.bridge.dispatch_to_agents(task)


# Integration with CHATTY_CHATTY.py

class JarvisSystemIntegration:
    """Integrates CHATTY with all CHATTY systems"""
    
    def __init__(self):
        self.bridge = JarvisContinuousBridge()
        self.controller = JarvisAutonomousController(self.bridge)
    
    async def get_comprehensive_status(self) -> str:
        """Get full system status for CHATTY display"""
        lines = []
        
        # Continuous mode status
        is_running = await self.bridge.is_continuous_mode_running()
        lines.append(f"🔄 Continuous Mode: {'🟢 Running' if is_running else '🔴 Stopped'}")
        
        # System status
        status = await self.bridge.get_system_status()
        if status:
            lines.append(self.bridge.format_status_for_display(status))
        else:
            lines.append("⚪ No status data available")
        
        return "\n\n".join(lines)
    
    async def control_continuous_mode(self, action: str) -> str:
        """Control continuous mode (start/stop/status)"""
        if action == "start":
            success = await self.bridge.start_continuous_mode()
            return "🟢 Continuous mode started" if success else "🔴 Failed to start"
        elif action == "stop":
            success = await self.bridge.stop_continuous_mode()
            return "🛑 Continuous mode stopped" if success else "🔴 Failed to stop"
        elif action == "status":
            is_running = await self.bridge.is_continuous_mode_running()
            return f"Continuous mode is {'running' if is_running else 'stopped'}"
        else:
            return f"Unknown action: {action}"


# Utility functions for easy integration

async def get_chatty_bridge() -> JarvisContinuousBridge:
    """Get configured bridge instance"""
    return JarvisContinuousBridge()


async def get_chatty_integration() -> JarvisSystemIntegration:
    """Get full integration instance"""
    return JarvisSystemIntegration()


if __name__ == "__main__":
    # Test integration
    async def test():
        integration = await get_chatty_integration()
        status = await integration.get_comprehensive_status()
        print(status)
    
    asyncio.run(test())
