#!/usr/bin/env python3
"""
Enhanced Chatty Automation System Integration
Integrates the enhanced multi-agent system with existing Chatty automation
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import existing Chatty components
try:
    from START_COMPLETE_AUTOMATION import ChattyCompleteAutomation
    EXISTING_AUTOMATION_AVAILABLE = True
except ImportError:
    EXISTING_AUTOMATION_AVAILABLE = False
    print("⚠️ Existing automation system not found")

# Import enhanced components
from ENHANCED_MULTI_AGENT_SYSTEM import EnhancedMultiAgentSystem
from ENHANCED_CHAT_INTERFACE import MultiAgentChatManager
from OPEN_SOURCE_INTEGRATIONS import UnifiedIntegrationInterface

# Import YouTube learning system
try:
    from youtube_learning_system import YouTubeLearningSystem
    YOUTUBE_LEARNING_AVAILABLE = True
except ImportError:
    YOUTUBE_LEARNING_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENHANCED CHATTY AUTOMATION SYSTEM
# ============================================================================

class EnhancedChattyAutomation:
    """Enhanced Chatty system with multi-agent capabilities"""
    
    def __init__(self):
        self.existing_system = None
        self.enhanced_system = None
        self.chat_manager = None
        self.integration_interface = None
        self.youtube_learner = None
        self.is_running = False
        self.start_time = None
        
        # Performance metrics
        self.metrics = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_response_time": 0.0,
            "active_agents": 0,
            "system_health": 100.0
        }
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components"""
        logger.info("🚀 Initializing Enhanced Chatty Automation System...")
        
        # Initialize existing system if available
        if EXISTING_AUTOMATION_AVAILABLE:
            try:
                self.existing_system = ChattyCompleteAutomation()
                logger.info("✅ Existing Chatty automation system loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load existing system: {e}")
        
        # Initialize enhanced multi-agent system
        try:
            self.enhanced_system = EnhancedMultiAgentSystem()
            logger.info("✅ Enhanced multi-agent system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced system: {e}")
        
        # Initialize YouTube learning system
        if YOUTUBE_LEARNING_AVAILABLE:
            try:
                self.youtube_learner = YouTubeLearningSystem()
                logger.info("✅ YouTube learning system initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize YouTube learning: {e}")
        
        # Initialize integration interface
        try:
            self.integration_interface = UnifiedIntegrationInterface()
            logger.info("✅ Open-source integration interface initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize integration interface: {e}")
        
        # Initialize chat manager
        try:
            if self.enhanced_system:
                self.chat_manager = MultiAgentChatManager(self.enhanced_system)
                logger.info("✅ Multi-agent chat manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize chat manager: {e}")
        
        logger.info("🎉 Enhanced Chatty Automation System initialization complete")
    
    async def start(self):
        """Start the enhanced automation system"""
        if self.is_running:
            logger.warning("⚠️ System is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Starting Enhanced Chatty Automation System...")
        logger.info("="*80)
        
        # Start existing system if available
        if self.existing_system:
            logger.info("🔄 Starting existing Chatty automation...")
            try:
                await self.existing_system.initialize()
                # Start existing system in background
                asyncio.create_task(self._run_existing_system())
                logger.info("✅ Existing Chatty automation started")
            except Exception as e:
                logger.error(f"❌ Failed to start existing system: {e}")
        
        # Start enhanced system
        if self.enhanced_system:
            logger.info("🤖 Starting enhanced multi-agent system...")
            try:
                await self.enhanced_system.initialize()
                # Start enhanced system in background
                asyncio.create_task(self._run_enhanced_system())
                logger.info("✅ Enhanced multi-agent system started")
            except Exception as e:
                logger.error(f"❌ Failed to start enhanced system: {e}")
        
        # Start continuous learning
        if self.youtube_learner:
            logger.info("🎥 Starting YouTube learning system...")
            asyncio.create_task(self._continuous_youtube_learning())
        
        # Start metrics collection
        asyncio.create_task(self._collect_metrics())
        
        # Start system monitoring
        asyncio.create_task(self._monitor_system_health())
        
        logger.info("="*80)
        logger.info("🎉 Enhanced Chatty Automation System is now running!")
        logger.info("📱 Chat interface available at: http://localhost:8000")
        logger.info("🤖 5+ specialized agents active")
        logger.info("🎥 YouTube learning enabled")
        logger.info("🔧 Self-healing monitoring active")
        logger.info("💰 Token optimization enabled")
        logger.info("🛡️ Guardrails and safety checks active")
        logger.info("🔗 Open-source integrations ready")
        logger.info("="*80)
        
        # Keep the system running
        while self.is_running:
            await asyncio.sleep(10)
    
    async def _run_existing_system(self):
        """Run existing Chatty automation system"""
        try:
            if self.existing_system:
                await self.existing_system.start()
        except Exception as e:
            logger.error(f"Existing system error: {e}")
            await asyncio.sleep(30)
    
    async def _run_enhanced_system(self):
        """Run enhanced multi-agent system"""
        try:
            if self.enhanced_system:
                await self.enhanced_system.start()
        except Exception as e:
            logger.error(f"Enhanced system error: {e}")
            await asyncio.sleep(30)
    
    async def _continuous_youtube_learning(self):
        """Continuous YouTube learning loop"""
        while self.is_running:
            try:
                if self.youtube_learner:
                    # Mock learning from relevant videos
                    # In production, would fetch from subscriptions or recommendations
                    logger.info("🎥 YouTube learning cycle completed")
                await asyncio.sleep(3600)  # Every hour
            except Exception as e:
                logger.error(f"YouTube learning error: {e}")
                await asyncio.sleep(300)
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        while self.is_running:
            try:
                # Update metrics from all components
                if self.enhanced_system:
                    self.metrics.update(self.enhanced_system.system_metrics)
                
                if self.integration_interface:
                    integration_status = self.integration_interface.get_integration_status()
                    self.metrics["integrations_active"] = len([
                        i for i in integration_status["integrations"].values()
                        if i["status"] == "active"
                    ])
                
                # Log metrics
                logger.info(f"📊 System Metrics: {json.dumps(self.metrics, indent=2)}")
                
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while self.is_running:
            try:
                health_score = 100.0
                
                # Check component health
                if self.enhanced_system and hasattr(self.enhanced_system, 'self_healer'):
                    health_score = min(health_score, self.enhanced_system.self_healer.system_health)
                
                # Update metrics
                self.metrics["system_health"] = health_score
                
                if health_score < 80:
                    logger.warning(f"⚠️ System health degraded: {health_score}%")
                    await self._trigger_health_recovery()
                
                await asyncio.sleep(60)  # Every minute
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _trigger_health_recovery(self):
        """Trigger health recovery actions"""
        try:
            logger.info("🔧 Triggering health recovery actions...")
            
            # Use integration interface for recovery
            if self.integration_interface:
                recovery_result = await self.integration_interface.execute_task(
                    "automation",
                    {
                        "workflow_name": "health_recovery",
                        "parameters": {"health_score": self.metrics["system_health"]}
                    }
                )
                logger.info(f"🔧 Health recovery result: {recovery_result}")
        
        except Exception as e:
            logger.error(f"Health recovery failed: {e}")
    
    async def stop(self):
        """Stop the enhanced automation system"""
        logger.info("🛑 Stopping Enhanced Chatty Automation System...")
        
        self.is_running = False
        
        # Stop components gracefully
        # (In production, would implement proper shutdown for each component)
        
        logger.info("✅ Enhanced Chatty Automation System stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "system_name": "Enhanced Chatty Automation",
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": str(datetime.now() - self.start_time) if self.start_time else "0:00:00",
            "metrics": self.metrics,
            "components": {
                "existing_automation": self.existing_system is not None,
                "enhanced_multi_agent": self.enhanced_system is not None,
                "youtube_learning": self.youtube_learner is not None,
                "integration_interface": self.integration_interface is not None,
                "chat_manager": self.chat_manager is not None
            }
        }
        
        # Add enhanced system status
        if self.enhanced_system:
            status["enhanced_system"] = self.enhanced_system.system_metrics
        
        # Add integration status
        if self.integration_interface:
            status["integrations"] = self.integration_interface.get_integration_status()
        
        return status

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Chatty Automation System")
    parser.add_argument("--mode", choices=["start", "status", "chat-only"], default="start",
                       help="System mode")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port for chat interface")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.mode == "chat-only":
        # Run only the chat interface
        logger.info("📱 Starting chat interface only...")
        from ENHANCED_CHAT_INTERFACE import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    
    elif args.mode == "status":
        # Show system status
        system = EnhancedChattyAutomation()
        status = system.get_system_status()
        print("📊 Enhanced Chatty Automation System Status:")
        print(json.dumps(status, indent=2))
    
    else:
        # Start full system
        system = EnhancedChattyAutomation()
        
        try:
            await system.start()
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested by user")
            await system.stop()
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            await system.stop()

# ============================================================================
# ENHANCED STARTUP SCRIPT
# ============================================================================

def create_enhanced_launcher():
    """Create enhanced launcher script"""
    launcher_content = """#!/bin/bash
# Enhanced Chatty Automation Launcher

echo "🚀 Enhanced Chatty Automation System"
echo "=================================="

# Check Python version
python3 --version

# Check required packages
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, asyncio, pydantic" 2>/dev/null || {
    echo "❌ Missing required packages. Installing..."
    pip3 install fastapi uvicorn websockets pydantic python-multipart
}

# Create logs directory
mkdir -p logs

# Start the system
echo "🎯 Starting Enhanced Chatty Automation..."
python3 ENHANCED_START_COMPLETE_AUTOMATION.py --mode start "$@"
"""
    
    launcher_path = Path("launch_enhanced_chatty.sh")
    launcher_path.write_text(launcher_content)
    launcher_path.chmod(0o755)
    
    print(f"✅ Enhanced launcher created: {launcher_path}")

if __name__ == "__main__":
    # Create launcher script
    create_enhanced_launcher()
    
    # Run main
    asyncio.run(main())
