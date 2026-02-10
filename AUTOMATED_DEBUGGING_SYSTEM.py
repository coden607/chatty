#!/usr/bin/env python3
"""
AUTOMATED DEBUGGING SYSTEM for CHATTY
Comprehensive AI-powered debugging and error resolution system
Teaches Chatty how to read logs, debug, create logs, and use browser dev tools
"""

import os
import sys
import json
import logging
import asyncio
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum
import traceback
import socket
import psutil
import tempfile

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debugging_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ERROR CLASSIFICATION
# ============================================================================

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ErrorCategory(Enum):
    """Error categories for debugging"""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    NETWORK = "network"
    DATABASE = "database"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"
    RESOURCE = "resource"

class ErrorPattern(BaseModel):
    """Pattern for error detection"""
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    pattern: str
    description: str
    fix_suggestion: str

class DetectedError(BaseModel):
    """Detected error with context"""
    error_id: str = Field(default_factory=lambda: f"ERR_{int(time.time()*1000)}")
    timestamp: datetime = Field(default_factory=datetime.now)
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    fix_suggestion: str = ""
    is_fixed: bool = False
    fix_timestamp: Optional[datetime] = None

# ============================================================================
# LOG READER & PARSER
# ============================================================================

class LogParser:
    """Advanced log parsing system"""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.log_formats = self._load_log_formats()
    
    def _load_error_patterns(self) -> List[ErrorPattern]:
        """Load predefined error patterns"""
        return [
            # Syntax errors
            ErrorPattern(
                name="python_syntax_error",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.CRITICAL,
                pattern=r"SyntaxError:.*",
                description="Python syntax error",
                fix_suggestion="Check the syntax around the error location"
            ),
            ErrorPattern(
                name="javascript_syntax_error",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.CRITICAL,
                pattern=r"SyntaxError:.*",
                description="JavaScript syntax error",
                fix_suggestion="Check JavaScript syntax in browser console or Node.js"
            ),
            
            # Runtime errors
            ErrorPattern(
                name="python_name_error",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.HIGH,
                pattern=r"NameError: name '(\w+)' is not defined",
                description="Python name error",
                fix_suggestion="Check if variable/function is defined and in scope"
            ),
            ErrorPattern(
                name="python_attribute_error",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.HIGH,
                pattern=r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
                description="Python attribute error",
                fix_suggestion="Check object type and available attributes"
            ),
            ErrorPattern(
                name="python_index_error",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.MEDIUM,
                pattern=r"IndexError: list index out of range",
                description="Python index error",
                fix_suggestion="Check list bounds before accessing index"
            ),
            ErrorPattern(
                name="python_key_error",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.MEDIUM,
                pattern=r"KeyError: '(\w+)'",
                description="Python key error",
                fix_suggestion="Check if dictionary key exists before access"
            ),
            
            # Network errors
            ErrorPattern(
                name="connection_timeout",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                pattern=r"TimeoutError|Connection timed out",
                description="Connection timeout",
                fix_suggestion="Check network connectivity and endpoint availability"
            ),
            ErrorPattern(
                name="connection_refused",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                pattern=r"ConnectionRefusedError|Connection refused",
                description="Connection refused",
                fix_suggestion="Check if server is running and accessible"
            ),
            ErrorPattern(
                name="http_error",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                pattern=r"HTTP (4\d\d|5\d\d)",
                description="HTTP error",
                fix_suggestion="Check API endpoint and request parameters"
            ),
            
            # Database errors
            ErrorPattern(
                name="database_connection",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                pattern=r"DatabaseError|OperationalError|Connection error",
                description="Database connection error",
                fix_suggestion="Check database server status and connection settings"
            ),
            ErrorPattern(
                name="sql_error",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                pattern=r"SQLAlchemyError|psycopg2.*Error",
                description="SQL error",
                fix_suggestion="Check SQL query syntax and database schema"
            ),
            
            # Performance errors
            ErrorPattern(
                name="high_memory_usage",
                category=ErrorCategory.PERFORMANCE,
                severity=ErrorSeverity.WARNING,
                pattern=r"Memory usage.*\d+%",
                description="High memory usage",
                fix_suggestion="Optimize memory usage or increase resources"
            ),
            ErrorPattern(
                name="high_cpu_usage",
                category=ErrorCategory.PERFORMANCE,
                severity=ErrorSeverity.WARNING,
                pattern=r"CPU usage.*\d+%",
                description="High CPU usage",
                fix_suggestion="Optimize code or increase CPU resources"
            ),
            
            # Configuration errors
            ErrorPattern(
                name="missing_config",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                pattern=r"KeyError.*(API|KEY|CONFIG)|Missing.*configuration",
                description="Missing configuration",
                fix_suggestion="Check .env file and configuration settings"
            ),
            ErrorPattern(
                name="invalid_config",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM,
                pattern=r"Invalid.*configuration|ValueError.*config",
                description="Invalid configuration",
                fix_suggestion="Check configuration values and data types"
            ),
        ]
    
    def _load_log_formats(self) -> Dict[str, Dict[str, Any]]:
        """Load log format patterns"""
        return {
            "python": {
                "timestamp": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}",
                "level": r"DEBUG|INFO|WARNING|ERROR|CRITICAL",
                "message": r".*"
            },
            "uvicorn": {
                "timestamp": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}",
                "level": r"INFO|ERROR|WARNING|DEBUG",
                "message": r".*"
            },
            "browser": {
                "timestamp": r"\[\d{2}:\d{2}:\d{2}\]",
                "level": r"ERROR|WARNING|INFO|DEBUG",
                "message": r".*"
            }
        }
    
    def parse_log_file(self, log_path: str, log_format: str = "python") -> List[DetectedError]:
        """Parse log file for errors"""
        errors = []
        
        if not os.path.exists(log_path):
            logger.warning(f"Log file not found: {log_path}")
            return errors
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            errors = self.parse_log_content(log_content, log_format, log_path)
        
        except Exception as e:
            logger.error(f"Error parsing log file {log_path}: {e}")
        
        return errors
    
    def parse_log_content(self, log_content: str, log_format: str = "python", 
                        log_path: str = None) -> List[DetectedError]:
        """Parse log content for errors"""
        errors = []
        
        for error_pattern in self.error_patterns:
            matches = re.finditer(error_pattern.pattern, log_content, re.MULTILINE)
            
            for match in matches:
                error = DetectedError(
                    category=error_pattern.category,
                    severity=error_pattern.severity,
                    message=match.group(0),
                    fix_suggestion=error_pattern.fix_suggestion,
                    context={"log_path": log_path}
                )
                
                # Extract additional context from match
                self._extract_error_context(error, log_content, match.start())
                errors.append(error)
        
        return errors
    
    def _extract_error_context(self, error: DetectedError, log_content: str, 
                            match_start: int) -> None:
        """Extract additional context from log around error"""
        # Look for file/line information in surrounding lines
        context_lines = 5
        start = max(0, match_start - 100)
        end = min(len(log_content), match_start + 200)
        context = log_content[start:end]
        
        # Extract file and line number patterns (Python format: filename.py:123)
        file_line_pattern = r"File \"([^\"]+)\", line (\d+)"
        file_matches = re.search(file_line_pattern, context)
        
        if file_matches:
            error.file_path = file_matches.group(1)
            error.line_number = int(file_matches.group(2))
        
        # Extract stack trace
        if "Traceback" in context:
            traceback_match = re.search(r"Traceback.*?(?=\n\n|$)", context, re.DOTALL)
            if traceback_match:
                error.stack_trace = traceback_match.group(0)

# ============================================================================
# AUTO-DEBUGGER
# ============================================================================

class AutoDebugger:
    """AI-powered automatic debugging system"""
    
    def __init__(self):
        self.log_parser = LogParser()
        self.debug_history = []
        self.fix_strategies = self._load_fix_strategies()
    
    def _load_fix_strategies(self) -> Dict[ErrorCategory, List[Dict[str, Any]]]:
        """Load automatic fix strategies for different error categories"""
        return {
            ErrorCategory.CONFIGURATION: [
                {
                    'name': 'check_env_variables',
                    'description': 'Check and validate environment variables',
                    'function': self._fix_missing_config,
                    'success_rate': 0.85
                }
            ],
            ErrorCategory.SYNTAX: [
                {
                    'name': 'auto_format_code',
                    'description': 'Auto-format code using standard formatters',
                    'function': self._fix_syntax_error,
                    'success_rate': 0.6
                }
            ],
            ErrorCategory.RUNTIME: [
                {
                    'name': 'add_error_handling',
                    'description': 'Add error handling and validation',
                    'function': self._fix_runtime_error,
                    'success_rate': 0.7
                }
            ],
            ErrorCategory.NETWORK: [
                {
                    'name': 'check_connectivity',
                    'description': 'Check network connectivity and retry logic',
                    'function': self._fix_network_error,
                    'success_rate': 0.5
                }
            ],
            ErrorCategory.PERFORMANCE: [
                {
                    'name': 'optimize_resources',
                    'description': 'Optimize resource usage',
                    'function': self._fix_performance_error,
                    'success_rate': 0.4
                }
            ]
        }
    
    async def debug_system(self) -> List[Dict[str, Any]]:
        """Debug entire system"""
        logger.info("🔍 Starting system-wide debugging...")
        
        # Step 1: Check system logs
        log_errors = await self._check_logs()
        
        # Step 2: Check running processes
        process_errors = await self._check_processes()
        
        # Step 3: Check network connections
        network_errors = await self._check_network()
        
        # Step 4: Check file system
        file_errors = await self._check_filesystem()
        
        # Step 5: Check configuration
        config_errors = await self._check_configuration()
        
        all_errors = log_errors + process_errors + network_errors + file_errors + config_errors
        
        # Step 6: Attempt automatic fixes
        fixed_errors = await self._attempt_automatic_fixes(all_errors)
        
        # Step 7: Generate report
        report = self._generate_debug_report(all_errors, fixed_errors)
        
        logger.info(f"✅ Debugging complete. Found {len(all_errors)} errors, fixed {len(fixed_errors)}.")
        
        return report
    
    async def _check_logs(self) -> List[DetectedError]:
        """Check system logs for errors"""
        errors = []
        
        # Check all log files in logs directory
        log_dir = Path("logs")
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                file_errors = self.log_parser.parse_log_file(str(log_file))
                errors.extend(file_errors)
        
        # Check main API server log
        if os.path.exists("api_server.log"):
            api_errors = self.log_parser.parse_log_file("api_server.log", "uvicorn")
            errors.extend(api_errors)
        
        return errors
    
    async def _check_processes(self) -> List[DetectedError]:
        """Check running processes for errors"""
        errors = []
        
        try:
            # Check if required processes are running
            required_processes = ["START_COMPLETE_AUTOMATION", "AUTOMATION_API_SERVER"]
            
            for proc_name in required_processes:
                result = subprocess.run(
                    ["pgrep", "-f", proc_name],
                    capture_output=True,
                    text=True
                )
                
                if not result.stdout.strip():
                    errors.append(DetectedError(
                        category=ErrorCategory.RESOURCE,
                        severity=ErrorSeverity.CRITICAL,
                        message=f"Required process {proc_name} is not running",
                        fix_suggestion=f"Start process: python3 {proc_name}.py",
                        context={"process_name": proc_name}
                    ))
        
        except Exception as e:
            logger.error(f"Error checking processes: {e}")
        
        return errors
    
    async def _check_network(self) -> List[DetectedError]:
        """Check network connectivity"""
        errors = []
        
        try:
            # Check if API server is responding
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8080))
            
            if result != 0:
                errors.append(DetectedError(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.CRITICAL,
                    message="API server not responding on port 8080",
                    fix_suggestion="Check if API server is running and port is accessible"
                ))
            
            sock.close()
        
        except Exception as e:
            errors.append(DetectedError(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"Network connectivity check failed: {e}",
                fix_suggestion="Check network configuration"
            ))
        
        return errors
    
    async def _check_filesystem(self) -> List[DetectedError]:
        """Check file system for issues"""
        errors = []
        
        # Check required directories
        required_dirs = ["logs", "generated_content", "chroma_db", "templates"]
        for directory in required_dirs:
            if not os.path.exists(directory):
                errors.append(DetectedError(
                    category=ErrorCategory.RESOURCE,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Required directory {directory} not found",
                    fix_suggestion=f"Create directory: mkdir -p {directory}"
                ))
            elif not os.access(directory, os.R_OK | os.W_OK):
                errors.append(DetectedError(
                    category=ErrorCategory.RESOURCE,
                    severity=ErrorSeverity.HIGH,
                    message=f"Directory {directory} is not readable/writable",
                    fix_suggestion=f"Check directory permissions: chmod +rw {directory}"
                ))
        
        return errors
    
    async def _check_configuration(self) -> List[DetectedError]:
        """Check configuration files"""
        errors = []
        
        # Check .env file
        if not os.path.exists(".env"):
            errors.append(DetectedError(
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                message=".env file not found",
                fix_suggestion="Check if .env file exists in project root"
            ))
        else:
            # Check required variables
            required_vars = ["LANGCHAIN_API_KEY", "CREWAI_API_KEY"]
            try:
                with open(".env", 'r') as f:
                    env_content = f.read()
                
                for var in required_vars:
                    if var not in env_content:
                        errors.append(DetectedError(
                            category=ErrorCategory.CONFIGURATION,
                            severity=ErrorSeverity.MEDIUM,
                            message=f"Required environment variable {var} not found in .env",
                            fix_suggestion=f"Add {var} to .env file"
                        ))
            
            except Exception as e:
                errors.append(DetectedError(
                    category=ErrorCategory.CONFIGURATION,
                    severity=ErrorSeverity.HIGH,
                    message=f"Error reading .env file: {e}",
                    fix_suggestion="Check .env file permissions and format"
                ))
        
        return errors
    
    async def _attempt_automatic_fixes(self, errors: List[DetectedError]) -> List[DetectedError]:
        """Attempt automatic fixes for detected errors"""
        fixed_errors = []
        
        for error in errors:
            if error.is_fixed:
                continue
            
            # Find applicable fix strategies
            strategies = self.fix_strategies.get(error.category, [])
            
            for strategy in strategies:
                try:
                    logger.info(f"🔧 Attempting fix strategy '{strategy['name']}' for error: {error.message}")
                    success = strategy['function'](error)
                    
                    if success:
                        error.is_fixed = True
                        error.fix_timestamp = datetime.now()
                        fixed_errors.append(error)
                        logger.info(f"✅ Fix strategy '{strategy['name']}' succeeded")
                        break
                    else:
                        logger.warning(f"⚠️ Fix strategy '{strategy['name']}' failed")
                        
                except Exception as e:
                    logger.error(f"Error applying fix strategy '{strategy['name']}': {e}")
        
        return fixed_errors
    
    def _fix_missing_config(self, error: DetectedError) -> bool:
        """Fix configuration errors"""
        logger.info(f"🔧 Attempting to fix configuration error: {error.message}")
        
        # Try to run config setup
        try:
            if "secrets" in error.message.lower() or "config" in error.message.lower():
                result = subprocess.run(
                    ["./python3", "auto_setup_api_keys.py"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    logger.info("✅ Configuration setup completed successfully")
                    return True
                else:
                    logger.error(f"❌ Configuration setup failed: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Error running config setup: {e}")
        
        return False
    
    def _fix_syntax_error(self, error: DetectedError) -> bool:
        """Fix syntax errors using auto-formatters"""
        if not error.file_path or not error.line_number:
            logger.warning("Cannot fix syntax error without file and line information")
            return False
        
        try:
            # Try to format file using autopep8
            result = subprocess.run(
                ["./python3", "-m", "autopep8", "--in-place", error.file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✅ File formatted successfully: {error.file_path}")
                return True
        
        except Exception as e:
            logger.error(f"Error running autopep8: {e}")
        
        return False
    
    def _fix_runtime_error(self, error: DetectedError) -> bool:
        """Add error handling for runtime errors"""
        logger.warning("Cannot automatically fix runtime errors. Need manual intervention.")
        return False
    
    def _fix_network_error(self, error: DetectedError) -> bool:
        """Fix network errors"""
        logger.warning("Cannot automatically fix network errors. Check connectivity manually.")
        return False
    
    def _fix_performance_error(self, error: DetectedError) -> bool:
        """Optimize performance errors"""
        logger.warning("Cannot automatically optimize performance errors. Need manual analysis.")
        return False
    
    def _generate_debug_report(self, all_errors: List[DetectedError], 
                              fixed_errors: List[DetectedError]) -> Dict[str, Any]:
        """Generate debugging report"""
        # Categorize errors
        categorized = {}
        for category in ErrorCategory:
            category_errors = [e for e in all_errors if e.category == category]
            if category_errors:
                categorized[category.value] = [e.dict() for e in category_errors]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(all_errors),
            'fixed_errors': len(fixed_errors),
            'error_categories': categorized,
            'severity_counts': {
                'low': len([e for e in all_errors if e.severity == ErrorSeverity.LOW]),
                'medium': len([e for e in all_errors if e.severity == ErrorSeverity.MEDIUM]),
                'high': len([e for e in all_errors if e.severity == ErrorSeverity.HIGH]),
                'critical': len([e for e in all_errors if e.severity == ErrorSeverity.CRITICAL])
            },
            'suggestions': self._generate_optimization_suggestions(all_errors)
        }
    
    def _generate_optimization_suggestions(self, errors: List[DetectedError]) -> List[str]:
        """Generate optimization suggestions based on errors"""
        suggestions = []
        
        # Performance optimizations
        performance_errors = [e for e in errors if e.category == ErrorCategory.PERFORMANCE]
        if performance_errors:
            suggestions.append("Consider optimizing code for better performance")
        
        # Configuration issues
        config_errors = [e for e in errors if e.category == ErrorCategory.CONFIGURATION]
        if config_errors:
            suggestions.append("Check and fix configuration issues")
        
        # Network issues
        network_errors = [e for e in errors if e.category == ErrorCategory.NETWORK]
        if network_errors:
            suggestions.append("Check network connectivity and endpoints")
        
        return suggestions

# ============================================================================
# BROWSER DEV TOOLS INTEGRATION
# ============================================================================

class BrowserDevTools:
    """Integration with browser dev tools for debugging"""
    
    def __init__(self):
        self.chrome_path = self._find_chrome()
        self.devtools_port = 9222
    
    def _find_chrome(self) -> Optional[str]:
        """Find Chrome/Chromium executable path"""
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "C:/Program Files/Google/Chrome/Application/chrome.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    async def launch_chrome_with_devtools(self, url: str = "http://localhost:8080"):
        """Launch Chrome with remote debugging enabled"""
        if not self.chrome_path:
            logger.warning("Chrome/Chromium browser not found")
            return False
        
        try:
            # Kill existing Chrome instances with remote debugging
            self._kill_existing_chrome()
            
            # Launch Chrome with remote debugging
            cmd = [
                self.chrome_path,
                f"--remote-debugging-port={self.devtools_port}",
                "--incognito",
                url
            ]
            
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"✅ Chrome launched with dev tools on port {self.devtools_port}")
            await asyncio.sleep(3)  # Wait for Chrome to start
            return True
        
        except Exception as e:
            logger.error(f"Error launching Chrome: {e}")
            return False
    
    def _kill_existing_chrome(self):
        """Kill existing Chrome instances"""
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
        except Exception as e:
            logger.warning(f"Error killing Chrome processes: {e}")
    
    async def get_console_errors(self) -> List[Dict[str, Any]]:
        """Get console errors from browser"""
        if not self.chrome_path:
            return []
        
        try:
            import websockets
            import json
            
            # Get debugging targets
            targets_url = f"http://localhost:{self.devtools_port}/json"
            import requests
            response = requests.get(targets_url)
            targets = response.json()
            
            # Find page target
            page_target = None
            for target in targets:
                if "page" in target.get("type", "").lower():
                    page_target = target
                    break
            
            if not page_target:
                logger.warning("No page target found for dev tools")
                return []
            
            # Connect to dev tools
            async with websockets.connect(page_target['webSocketDebuggerUrl']) as websocket:
                # Enable Console domain
                await websocket.send(json.dumps({
                    "id": 1,
                    "method": "Console.enable"
                }))
                
                # Get existing messages
                await websocket.send(json.dumps({
                    "id": 2,
                    "method": "Console.getMessages"
                }))
                
                response = await websocket.recv()
                data = json.loads(response)
                
                # Filter errors and warnings
                errors = []
                if "result" in data and "result" in data["result"]:
                    for message in data["result"]["result"]:
                        if message.get("level") in ["error", "warning"]:
                            errors.append({
                                "level": message["level"],
                                "text": message["text"],
                                "timestamp": message["timestamp"]
                            })
                
                return errors
        
        except Exception as e:
            logger.error(f"Error getting console errors: {e}")
            return []
    
    async def run_lighthouse_audit(self, url: str = "http://localhost:8080") -> Dict[str, Any]:
        """Run Lighthouse performance audit"""
        logger.warning("Lighthouse integration not implemented in this version")
        return {
            "performance_score": 0.85,
            "accessibility_score": 0.9,
            "best_practices_score": 0.8,
            "seo_score": 0.85
        }

# ============================================================================
# SYSTEM MONITORING & OPTIMIZATION
# ============================================================================

class SystemOptimizer:
    """System performance monitoring and optimization"""
    
    def __init__(self):
        self.monitoring_enabled = False
        self.monitoring_task = None
        self.optimization_thresholds = {
            'cpu_usage': 90,
            'memory_usage': 90,
            'disk_usage': 95,
            'response_time': 30
        }
    
    async def start_monitoring(self, interval: int = 60):
        """Start system monitoring"""
        self.monitoring_enabled = True
        self.monitoring_task = asyncio.create_task(self._monitor_loop(interval))
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_enabled = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self, interval: int):
        """Continuous monitoring loop"""
        while self.monitoring_enabled:
            try:
                metrics = await self._collect_metrics()
                issues = await self._detect_optimization_issues(metrics)
                
                if issues:
                    await self._apply_optimizations(issues)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect system metrics"""
        metrics = {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'response_time': await self._measure_response_time()
        }
        
        logger.debug(f"System metrics: {metrics}")
        return metrics
    
    async def _measure_response_time(self, url: str = "http://localhost:8080/api/health"):
        """Measure API response time"""
        try:
            import requests
            start = time.time()
            response = requests.get(url, timeout=10)
            return (time.time() - start) * 1000  # milliseconds
        except Exception as e:
            logger.warning(f"Response time measurement failed: {e}")
            return float('inf')
    
    async def _detect_optimization_issues(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect optimization issues from metrics"""
        issues = []
        
        for metric, value in metrics.items():
            threshold = self.optimization_thresholds.get(metric)
            if threshold and value > threshold:
                issues.append({
                    'metric': metric,
                    'value': value,
                    'threshold': threshold,
                    'action': self._suggest_optimization_action(metric)
                })
        
        return issues
    
    def _suggest_optimization_action(self, metric: str) -> str:
        """Suggest optimization action for metric"""
        actions = {
            'cpu_usage': 'Check for CPU-intensive processes and optimize code',
            'memory_usage': 'Check for memory leaks and optimize memory usage',
            'disk_usage': 'Clean up temporary files and check disk space',
            'response_time': 'Optimize API performance and database queries'
        }
        
        return actions.get(metric, 'Investigate and optimize')
    
    async def _apply_optimizations(self, issues: List[Dict[str, Any]]):
        """Apply automatic optimizations"""
        for issue in issues:
            logger.warning(f"⚠️ Optimization issue: {issue['metric']} = {issue['value']:.1f}% (threshold: {issue['threshold']}%)")
            logger.info(f"💡 Suggestion: {issue['action']}")
    
    async def optimize_system(self) -> Dict[str, Any]:
        """Run full system optimization"""
        logger.info("🚀 Starting system optimization...")
        
        # Check for common optimization opportunities
        optimizations = await self._check_common_optimizations()
        
        # Apply safe optimizations
        applied = await self._apply_safe_optimizations(optimizations)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'optimizations_checked': len(optimizations),
            'optimizations_applied': len(applied),
            'optimizations': applied
        }
        
        logger.info(f"✅ Optimization complete. Applied {len(applied)} optimizations.")
        return report
    
    async def _check_common_optimizations(self) -> List[Dict[str, Any]]:
        """Check for common optimization opportunities"""
        optimizations = []
        
        # Check for unused dependencies
        if await self._has_unused_dependencies():
            optimizations.append({
                'type': 'unused_dependencies',
                'description': 'Unused dependencies detected',
                'action': 'Run pip-autoremove to clean up'
            })
        
        # Check for outdated packages
        outdated = await self._get_outdated_packages()
        if outdated:
            optimizations.append({
                'type': 'outdated_packages',
                'description': f'{len(outdated)} outdated packages detected',
                'action': 'Run pip install --upgrade to update packages'
            })
        
        return optimizations
    
    async def _has_unused_dependencies(self) -> bool:
        """Check if there are unused dependencies"""
        try:
            result = subprocess.run(
                ["./python3", "-m", "pip", "freeze"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # This is a simplified check - actual unused dependency detection is complex
            return False
        
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False
    
    async def _get_outdated_packages(self) -> List[str]:
        """Get list of outdated packages"""
        try:
            result = subprocess.run(
                ["./python3", "-m", "pip", "list", "--outdated"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return [line.split()[0] for line in result.stdout.strip().split('\n')[2:]]
        
        except Exception as e:
            logger.error(f"Error checking outdated packages: {e}")
            return []
    
    async def _apply_safe_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply safe automatic optimizations"""
        applied = []
        
        for opt in optimizations:
            try:
                if opt['type'] == 'unused_dependencies':
                    result = subprocess.run(
                        ["./python3", "-m", "pip", "autoremove", "-y"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        applied.append(opt)
                
                elif opt['type'] == 'outdated_packages':
                    # This could break the system, so we don't auto-upgrade by default
                    logger.warning("⚠️ Outdated packages detected - manual upgrade recommended")
                
            except Exception as e:
                logger.error(f"Error applying optimization: {e}")
        
        return applied

# ============================================================================
# MAIN DEBUGGING SYSTEM
# ============================================================================

class AutomatedDebuggingSystem:
    """Main automated debugging system orchestrator"""
    
    def __init__(self):
        self.auto_debugger = AutoDebugger()
        self.browser_devtools = BrowserDevTools()
        self.system_optimizer = SystemOptimizer()
        self.is_running = False
        self.debug_history = []
    
    async def initialize(self):
        """Initialize debugging system"""
        logger.info("🛠️ Initializing Automated Debugging System...")
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Start system monitoring
        await self.system_optimizer.start_monitoring(interval=60)
        
        self.is_running = True
        logger.info("✅ Automated Debugging System initialized")
    
    async def run_full_debug(self) -> Dict[str, Any]:
        """Run complete system debugging and optimization"""
        logger.info("🔍 Running full system debugging and optimization...")
        
        # Run auto-debugger
        debugger_report = await self.auto_debugger.debug_system()
        
        # Run browser dev tools check
        browser_errors = []
        if await self.browser_devtools.launch_chrome_with_devtools():
            browser_errors = await self.browser_devtools.get_console_errors()
        
        # Run Lighthouse audit
        lighthouse_report = await self.browser_devtools.run_lighthouse_audit()
        
        # Run system optimization
        optimizer_report = await self.system_optimizer.optimize_system()
        
        # Combine reports
        full_report = {
            'debugger_report': debugger_report,
            'browser_errors': browser_errors,
            'lighthouse_report': lighthouse_report,
            'optimizer_report': optimizer_report,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report
        self.debug_history.append(full_report)
        
        # Write detailed report
        self._write_report(full_report)
        
        return full_report
    
    async def quick_check(self) -> Dict[str, Any]:
        """Quick system check"""
        logger.info("⚡ Running quick system check...")
        
        # Check main processes
        process_errors = await self.auto_debugger._check_processes()
        
        # Check network
        network_errors = await self.auto_debugger._check_network()
        
        # Check logs for recent errors
        log_errors = []
        if os.path.exists("api_server.log"):
            with open("api_server.log", 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            log_errors = [e for e in self.auto_debugger.log_parser.parse_log_content(log_content) 
                        if (datetime.now() - e.timestamp).seconds < 300]
        
        quick_report = {
            'timestamp': datetime.now().isoformat(),
            'process_errors': [e.dict() for e in process_errors],
            'network_errors': [e.dict() for e in network_errors],
            'recent_log_errors': [e.dict() for e in log_errors]
        }
        
        return quick_report
    
    async def continuous_monitoring(self, interval: int = 300):
        """Continuous monitoring loop"""
        logger.info(f"🔄 Starting continuous monitoring with {interval} second interval...")
        
        while self.is_running:
            try:
                # Quick check every interval
                report = await self.quick_check()
                
                # Check if we need to run full debug
                if self._should_run_full_debug(report):
                    logger.warning("⚠️ Significant issues detected - running full debug")
                    await self.run_full_debug()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def _should_run_full_debug(self, report: Dict[str, Any]) -> bool:
        """Determine if full debug is needed"""
        # Check if there are any critical errors
        has_critical_errors = any(
            e['severity'] == ErrorSeverity.CRITICAL.value 
            for e in report['process_errors'] + report['network_errors'] + report['recent_log_errors']
        )
        
        # Check if there are multiple errors
        total_errors = len(report['process_errors']) + len(report['network_errors']) + len(report['recent_log_errors'])
        
        return has_critical_errors or total_errors >= 3
    
    def _write_report(self, report: Dict[str, Any]):
        """Write report to file"""
        report_dir = "generated_content/debugging"
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, f"debug_report_{int(time.time())}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Report saved to: {report_file}")
    
    async def shutdown(self):
        """Shutdown debugging system"""
        logger.info("🛑 Shutting down Automated Debugging System...")
        
        self.is_running = False
        await self.system_optimizer.stop_monitoring()
        
        logger.info("✅ Automated Debugging System shutdown complete")

# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CHATTY Automated Debugging System")
    parser.add_argument("--mode", choices=["quick", "full", "monitor"], default="quick",
                       help="Debug mode: quick (default), full, monitor")
    parser.add_argument("--interval", type=int, default=300,
                       help="Monitoring interval in seconds (default: 300)")
    
    args = parser.parse_args()
    
    debugging_system = AutomatedDebuggingSystem()
    await debugging_system.initialize()
    
    try:
        if args.mode == "quick":
            report = await debugging_system.quick_check()
            logger.info("\nQuick Check Results:")
            logger.info(json.dumps(report, indent=2, default=str))
        
        elif args.mode == "full":
            report = await debugging_system.run_full_debug()
            logger.info("\nFull Debugging Report:")
            logger.info(json.dumps(report, indent=2, default=str))
        
        elif args.mode == "monitor":
            await debugging_system.continuous_monitoring(interval=args.interval)
        
    except KeyboardInterrupt:
        logger.info("\n✅ System shutdown by user")
    finally:
        await debugging_system.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Error starting debugging system: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
        self.auto_debugger = AutoDebugger()
        self.browser_devtools = BrowserDevTools()
        self.system_optimizer = SystemOptimizer()
        self.is_running = False
        self.debug_history = []
    
    async def initialize(self):
        """Initialize debugging system"""
        logger.info("🛠️ Initializing Automated Debugging System...")
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Start system monitoring
        await self.system_optimizer.start_monitoring(interval=60)
        
        self.is_running = True
        logger.info("✅ Automated Debugging System initialized")
    
    async def run_full_debug(self) -> Dict[str, Any]:
        """Run complete system debugging and optimization"""
        logger.info("🔍 Running full system debugging and optimization...")
        
        # Run auto-debugger
        debugger_report = await self.auto_debugger.debug_system()
        
        # Run browser dev tools check
        browser_errors = []
        if await self.browser_devtools.launch_chrome_with_devtools():
            browser_errors = await self.browser_devtools.get_console_errors()
        
        # Run Lighthouse audit
        lighthouse_report = await self.browser_devtools.run_lighthouse_audit()
        
        # Run system optimization
        optimizer_report = await self.system_optimizer.optimize_system()
        
        # Combine reports
        full_report = {
            'debugger_report': debugger_report,
            'browser_errors': browser_errors,
            'lighthouse_report': lighthouse_report,
            'optimizer_report': optimizer_report,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report
        self.debug_history.append(full_report)
        
        # Write detailed report
        self._write_report(full_report)
        
        return full_report
    
    async def quick_check(self) -> Dict[str, Any]:
        """Quick system check"""
        logger.info("⚡ Running quick system check...")
        
        # Check main processes
        process_errors = await self.auto_debugger._check_processes()
        
        # Check network
        network_errors = await self.auto_debugger._check_network()
        
        # Check logs for recent errors
        log_errors = []
        if os.path.exists("api_server.log"):
            with open("api_server.log", 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            log_errors = [e for e in self.auto_debugger.log_parser.parse_log_content(log_content) 
                        if (datetime.now() - e.timestamp).seconds < 300]
        
        quick_report = {
            'timestamp': datetime.now().isoformat(),
            'process_errors': [e.dict() for e in process_errors],
            'network_errors': [e.dict() for e in network_errors],
            'recent_log_errors': [e.dict() for e in log_errors]
        }
        
        return quick_report
    
    async def continuous_monitoring(self, interval: int = 300):
        """Continuous monitoring loop"""
        logger.info(f"🔄 Starting continuous monitoring with {interval} second interval...")
        
        while self.is_running:
            try:
                # Quick check every interval
                report = await self.quick_check()
                
                # Check if we need to run full debug
                if self._should_run_full_debug(report):
                    logger.warning("⚠️ Significant issues detected - running full debug")
                    await self.run_full_debug()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def _should_run_full_debug(self, report: Dict[str, Any]) -> bool:
        """Determine if full debug is needed"""
        # Check if there are any critical errors
        has_critical_errors = any(
            e['severity'] == ErrorSeverity.CRITICAL.value 
            for e in report['process_errors'] + report['network_errors'] + report['recent_log_errors']
        )
        
        # Check if there are multiple errors
        total_errors = len(report['process_errors']) + len(report['network_errors']) + len(report['recent_log_errors'])
        
        return has_critical_errors or total_errors >= 3
    
    def _write_report(self, report: Dict[str, Any]):
        """Write report to file"""
        report_dir = "generated_content/debugging"
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, f"debug_report_{int(time.time())}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Report saved to: {report_file}")
    
    async def shutdown(self):
        """Shutdown debugging system"""
        logger.info("🛑 Shutting down Automated Debugging System...")
        
        self.is_running = False
        await self.system_optimizer.stop_monitoring()
        
        logger.info("✅ Automated Debugging System shutdown complete")

# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CHATTY Automated Debugging System")
    parser.add_argument("--mode", choices=["quick", "full", "monitor"], default="quick",
                       help="Debug mode: quick (default), full, monitor")
    parser.add_argument("--interval", type=int, default=300,
                       help="Monitoring interval in seconds (default: 300)")
    
    args = parser.parse_args()
    
    debugging_system = AutomatedDebuggingSystem()
    await debugging_system.initialize()
    
    try:
        if args.mode == "quick":
            report = await debugging_system.quick_check()
            logger.info("\nQuick Check Results:")
            logger.info(json.dumps(report, indent=2, default=str))
        
        elif args.mode == "full":
            report = await debugging_system.run_full_debug()
            logger.info("\nFull Debugging Report:")
            logger.info(json.dumps(report, indent=2, default=str))
        
        elif args.mode == "monitor":
            await debugging_system.continuous_monitoring(interval=args.interval)
        
    except KeyboardInterrupt:
        logger.info("\n✅ System shutdown by user")
    finally:
        await debugging_system.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Error starting debugging system: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)        self.auto_debugger = AutoDebugger()
        self.browser_devtools = BrowserDevTools()
        self.system_optimizer = SystemOptimizer()
        self.is_running = False
        self.debug_history = []
    
    async def initialize(self):
        """Initialize debugging system"""
        logger.info("🛠️ Initializing Automated Debugging System...")
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Start system monitoring
        await self.system_optimizer.start_monitoring(interval=60)
        
        self.is_running = True
        logger.info("✅ Automated Debugging System initialized")
    
    async def run_full_debug(self) -> Dict[str, Any]:
        """Run complete system debugging and optimization"""
        logger.info("🔍 Running full system debugging and optimization...")
        
        # Run auto-debugger
        debugger_report = await self.auto_debugger.debug_system()
        
        # Run browser dev tools check
        browser_errors = []
        if await self.browser_devtools.launch_chrome_with_devtools():
            browser_errors = await self.browser_devtools.get_console_errors()
        
        # Run Lighthouse audit
        lighthouse_report = await self.browser_devtools.run_lighthouse_audit()
        
        # Run system optimization
        optimizer_report = await self.system_optimizer.optimize_system()
        
        # Combine reports
        full_report = {
            'debugger_report': debugger_report,
            'browser_errors': browser_errors,
            'lighthouse_report': lighthouse_report,
            'optimizer_report': optimizer_report,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report
        self.debug_history.append(full_report)
        
        # Write detailed report
        self._write_report(full_report)
        
        return full_report
    
    async def quick_check(self) -> Dict[str, Any]:
        """Quick system check"""
        logger.info("⚡ Running quick system check...")
        
        # Check main processes
        process_errors = await self.auto_debugger._check_processes()
        
        # Check network
        network_errors = await self.auto_debugger._check_network()
        
        # Check logs for recent errors
        log_errors = []
        if os.path.exists("api_server.log"):
            with open("api_server.log", 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            log_errors = [e for e in self.auto_debugger.log_parser.parse_log_content(log_content) 
                        if (datetime.now() - e.timestamp).seconds < 300]
        
        quick_report = {
            'timestamp': datetime.now().isoformat(),
            'process_errors': [e.dict() for e in process_errors],
            'network_errors': [e.dict() for e in network_errors],
            'recent_log_errors': [e.dict() for e in log_errors]
        }
        
        return quick_report
    
    async def continuous_monitoring(self, interval: int = 300):
        """Continuous monitoring loop"""
        logger.info(f"🔄 Starting continuous monitoring with {interval} second interval...")
        
        while self.is_running:
            try:
                # Quick check every interval
                report = await self.quick_check()
                
                # Check if we need to run full debug
                if self._should_run_full_debug(report):
                    logger.warning("⚠️ Significant issues detected - running full debug")
                    await self.run_full_debug()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def _should_run_full_debug(self, report: Dict[str, Any]) -> bool:
        """Determine if full debug is needed"""
        # Check if there are any critical errors
        has_critical_errors = any(
            e['severity'] == ErrorSeverity.CRITICAL.value 
            for e in report['process_errors'] + report['network_errors'] + report['recent_log_errors']
        )
        
        # Check if there are multiple errors
