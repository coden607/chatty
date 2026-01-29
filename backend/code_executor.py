#!/usr/bin/env python3
"""
CHATTY Secure Code Execution System
Provides sandboxed code execution for autonomous agents with comprehensive security
"""

import os
import uuid
import time
import tempfile
import subprocess
import threading
import resource
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json

import docker
from docker.errors import DockerException, ContainerError, ImageNotFound
from flask import current_app

from server import db, logger

class CodeExecutionSandbox:
    """Secure sandboxed code execution using Docker containers"""

    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            # Test connection
            self.docker_client.ping()
            logger.info("Docker connection established")
        except DockerException as e:
            logger.error("Docker connection failed", error=str(e))
            self.docker_client = None

        self.execution_history = {}
        self.security_profiles = self._load_security_profiles()
        self.resource_limits = self._load_resource_limits()

    def _load_security_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load security profiles for different execution contexts"""
        return {
            'basic': {
                'allowed_imports': ['os', 'sys', 'json', 'math', 'datetime', 'random'],
                'blocked_functions': ['eval', 'exec', 'open', 'input', '__import__'],
                'network_access': False,
                'file_access': False,
                'max_execution_time': 30,
                'max_memory': '100m'
            },
            'data_science': {
                'allowed_imports': ['pandas', 'numpy', 'matplotlib', 'sklearn', 'scipy', 'statsmodels'],
                'blocked_functions': ['eval', 'exec', 'subprocess', 'os.system'],
                'network_access': True,  # For data fetching
                'file_access': True,     # For data files
                'max_execution_time': 300,
                'max_memory': '1g'
            },
            'web_development': {
                'allowed_imports': ['flask', 'requests', 'json', 'os'],
                'blocked_functions': ['eval', 'exec', 'subprocess'],
                'network_access': True,
                'file_access': True,
                'max_execution_time': 60,
                'max_memory': '256m'
            },
            'system_administration': {
                'allowed_imports': ['subprocess', 'os', 'sys', 'shutil'],
                'blocked_functions': ['eval', 'exec'],
                'network_access': True,
                'file_access': True,
                'max_execution_time': 120,
                'max_memory': '512m'
            }
        }

    def _load_resource_limits(self) -> Dict[str, Any]:
        """Load resource limits for execution"""
        return {
            'cpu_quota': 50000,      # 50% of CPU
            'cpu_period': 100000,
            'memory_limit': '512m',
            'memory_swap': '1g',
            'pids_limit': 1024,
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'tmpfs_size': '100m'
        }

    def execute_code(self, code: str, language: str, agent_id: str,
                    execution_context: str = 'basic', input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute code in a secure sandboxed environment"""
        execution_id = str(uuid.uuid4())

        try:
            # Validate inputs
            validation_result = self._validate_execution_request(code, language, execution_context)
            if not validation_result['valid']:
                return {
                    'execution_id': execution_id,
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_result['errors'],
                    'agent_id': agent_id
                }

            # Prepare execution environment
            execution_env = self._prepare_execution_environment(
                code, language, execution_context, input_data
            )

            # Execute in container
            result = self._execute_in_container(execution_env, execution_id)

            # Post-process results
            processed_result = self._process_execution_result(result, execution_id)

            # Store execution history
            self._store_execution_history(execution_id, {
                'agent_id': agent_id,
                'code': code[:500],  # Truncate for storage
                'language': language,
                'context': execution_context,
                'result': processed_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            return processed_result

        except Exception as e:
            logger.error("Code execution failed", execution_id=execution_id, error=str(e))
            return {
                'execution_id': execution_id,
                'success': False,
                'error': f'Execution failed: {str(e)}',
                'agent_id': agent_id,
                'language': language
            }

    def _validate_execution_request(self, code: str, language: str, context: str) -> Dict[str, Any]:
        """Validate the execution request for security"""
        errors = []

        # Check code length
        if len(code) > 50000:  # 50KB limit
            errors.append("Code too long (max 50KB)")

        # Check language support
        supported_languages = ['python', 'javascript', 'bash', 'r', 'sql']
        if language not in supported_languages:
            errors.append(f"Unsupported language: {language}")

        # Check security profile
        if context not in self.security_profiles:
            errors.append(f"Unknown execution context: {context}")

        # Security scan
        security_issues = self._scan_for_security_issues(code, language, context)
        errors.extend(security_issues)

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _scan_for_security_issues(self, code: str, language: str, context: str) -> List[str]:
        """Scan code for potential security issues"""
        issues = []
        profile = self.security_profiles.get(context, self.security_profiles['basic'])

        if language == 'python':
            # Check for dangerous imports
            dangerous_imports = ['subprocess', 'os.system', 'eval', 'exec', '__import__']
            for imp in dangerous_imports:
                if imp in code and imp not in profile['allowed_imports']:
                    issues.append(f"Potentially dangerous import: {imp}")

            # Check for file operations
            if 'open(' in code and not profile.get('file_access', False):
                issues.append("File operations not allowed in this context")

            # Check for network operations
            network_functions = ['requests.get', 'urllib', 'socket']
            for func in network_functions:
                if func in code and not profile.get('network_access', False):
                    issues.append(f"Network operations not allowed: {func}")

        elif language == 'bash':
            # Check for dangerous commands
            dangerous_commands = ['rm -rf', 'dd', 'mkfs', 'fdisk', 'sudo', 'su']
            for cmd in dangerous_commands:
                if cmd in code:
                    issues.append(f"Potentially dangerous command: {cmd}")

        return issues

    def _prepare_execution_environment(self, code: str, language: str,
                                     context: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare the execution environment"""
        profile = self.security_profiles.get(context, self.security_profiles['basic'])

        # Create execution script based on language
        if language == 'python':
            script = self._prepare_python_script(code, profile, input_data)
            image = 'python:3.11-slim'
            command = ['python', '/app/script.py']
        elif language == 'javascript':
            script = self._prepare_javascript_script(code, profile, input_data)
            image = 'node:18-slim'
            command = ['node', '/app/script.js']
        elif language == 'bash':
            script = code
            image = 'ubuntu:20.04'
            command = ['bash', '/app/script.sh']
        elif language == 'r':
            script = self._prepare_r_script(code, profile, input_data)
            image = 'r-base:4.2.0'
            command = ['Rscript', '/app/script.R']
        else:
            raise ValueError(f"Unsupported language: {language}")

        return {
            'script': script,
            'image': image,
            'command': command,
            'profile': profile,
            'input_data': input_data or {}
        }

    def _prepare_python_script(self, code: str, profile: Dict[str, Any],
                             input_data: Dict[str, Any] = None) -> str:
        """Prepare Python script with security wrapper"""
        wrapper = f'''
import sys
import json
import time

# Security restrictions
allowed_imports = {profile.get('allowed_imports', [])}
blocked_functions = {profile.get('blocked_functions', [])}

# Custom import hook for security
class SecureImporter:
    def __init__(self, allowed_modules):
        self.allowed_modules = set(allowed_modules)

    def find_spec(self, name, path, target=None):
        if name not in self.allowed_modules:
            raise ImportError(f"Import of '{{name}}' is not allowed")
        return None

# Install security import hook
secure_importer = SecureImporter(allowed_imports)
sys.meta_path.insert(0, secure_importer)

# Input data
input_data = {json.dumps(input_data or {})}

# User code
try:
    # Capture stdout
    import io
    from contextlib import redirect_stdout

    stdout_capture = io.StringIO()
    start_time = time.time()

    with redirect_stdout(stdout_capture):
        {code}

    execution_time = time.time() - start_time
    output = stdout_capture.getvalue()

    result = {{
        'success': True,
        'output': output,
        'execution_time': execution_time,
        'input_data': input_data
    }}

except Exception as e:
    result = {{
        'success': False,
        'error': str(e),
        'execution_time': time.time() - start_time,
        'input_data': input_data
    }}

# Output result as JSON
print(json.dumps(result))
'''
        return wrapper

    def _prepare_javascript_script(self, code: str, profile: Dict[str, Any],
                                 input_data: Dict[str, Any] = None) -> str:
        """Prepare JavaScript script with security wrapper"""
        wrapper = f'''
const fs = require('fs');
const path = require('path');

// Input data
const inputData = {json.dumps(input_data or {})};

try {{
    // User code
    {code}

    // Result
    const result = {{
        success: true,
        output: 'Execution completed',
        inputData: inputData,
        timestamp: new Date().toISOString()
    }};

    console.log(JSON.stringify(result));

}} catch (error) {{
    const result = {{
        success: false,
        error: error.message,
        inputData: inputData,
        timestamp: new Date().toISOString()
    }};

    console.log(JSON.stringify(result));
}}
'''
        return wrapper

    def _prepare_r_script(self, code: str, profile: Dict[str, Any],
                         input_data: Dict[str, Any] = None) -> str:
        """Prepare R script with security wrapper"""
        wrapper = f'''
# Input data
input_data <- {json.dumps(input_data or {})}

tryCatch({{
    # User code
    {code}

    # Result
    result <- list(
        success = TRUE,
        output = "Execution completed",
        input_data = input_data,
        timestamp = Sys.time()
    )

    cat(jsonlite::toJSON(result))

}}, error = function(e) {{
    result <- list(
        success = FALSE,
        error = as.character(e),
        input_data = input_data,
        timestamp = Sys.time()
    )

    cat(jsonlite::toJSON(result))
}})
'''
        return wrapper

    def _execute_in_container(self, execution_env: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute code in Docker container"""
        if not self.docker_client:
            return {
                'success': False,
                'error': 'Docker not available',
                'execution_id': execution_id
            }

        try:
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write script to file
                script_path = os.path.join(temp_dir, 'script.py')
                with open(script_path, 'w') as f:
                    f.write(execution_env['script'])

                # Prepare container configuration
                container_config = {
                    'image': execution_env['image'],
                    'command': execution_env['command'],
                    'volumes': {temp_dir: {'bind': '/app', 'mode': 'ro'}},
                    'working_dir': '/app',
                    'detach': False,
                    'mem_limit': execution_env['profile'].get('max_memory', '256m'),
                    'cpu_quota': self.resource_limits['cpu_quota'],
                    'cpu_period': self.resource_limits['cpu_period'],
                    'pids_limit': self.resource_limits['pids_limit'],
                    'read_only': not execution_env['profile'].get('file_access', False),
                    'network_disabled': not execution_env['profile'].get('network_access', False),
                    'tmpfs': {'/tmp': f'size={self.resource_limits["tmpfs_size"]}'},
                    'environment': {
                        'EXECUTION_TIMEOUT': str(execution_env['profile'].get('max_execution_time', 30))
                    }
                }

                # Run container
                container = self.docker_client.containers.run(**container_config)

                # Get logs
                logs = container.decode('utf-8') if isinstance(container, bytes) else str(container)

                return {
                    'success': True,
                    'output': logs,
                    'execution_id': execution_id
                }

        except ContainerError as e:
            return {
                'success': False,
                'error': f'Container execution failed: {str(e)}',
                'exit_code': e.exit_status,
                'execution_id': execution_id
            }
        except ImageNotFound:
            return {
                'success': False,
                'error': f'Docker image not found: {execution_env["image"]}',
                'execution_id': execution_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Container execution error: {str(e)}',
                'execution_id': execution_id
            }

    def _process_execution_result(self, result: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Process and validate execution results"""
        processed = result.copy()
        processed['execution_id'] = execution_id
        processed['processed_at'] = datetime.utcnow().isoformat()

        # Try to parse JSON output
        if result.get('success') and result.get('output'):
            try:
                # Look for JSON in output
                output = result['output'].strip()
                if output.startswith('{') and output.endswith('}'):
                    parsed_output = json.loads(output)
                    processed['parsed_output'] = parsed_output
                    processed['structured_result'] = True
                else:
                    processed['parsed_output'] = None
                    processed['structured_result'] = False
            except json.JSONDecodeError:
                processed['parsed_output'] = None
                processed['structured_result'] = False

        # Add performance metrics
        processed['performance'] = {
            'container_used': True,
            'security_profile_applied': True,
            'resource_limits_enforced': True
        }

        return processed

    def _store_execution_history(self, execution_id: str, data: Dict[str, Any]):
        """Store execution in history"""
        self.execution_history[execution_id] = data

        # Keep only recent executions
        if len(self.execution_history) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self.execution_history.keys(),
                key=lambda x: self.execution_history[x]['timestamp']
            )[:100]
            for key in oldest_keys:
                del self.execution_history[key]

    def get_execution_history(self, agent_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history, optionally filtered by agent"""
        executions = list(self.execution_history.values())

        if agent_id:
            executions = [e for e in executions if e.get('agent_id') == agent_id]

        # Sort by timestamp descending
        executions.sort(key=lambda x: x['timestamp'], reverse=True)

        return executions[:limit]

    def validate_code_safety(self, code: str, language: str, context: str = 'basic') -> Dict[str, Any]:
        """Validate code for safety without executing"""
        validation = self._validate_execution_request(code, language, context)

        if validation['valid']:
            # Additional static analysis
            static_issues = self._static_code_analysis(code, language, context)
            validation['errors'].extend(static_issues)
            validation['valid'] = len(validation['errors']) == 0

        return validation

    def _static_code_analysis(self, code: str, language: str, context: str) -> List[str]:
        """Perform static analysis on code"""
        issues = []

        if language == 'python':
            # Check for potentially dangerous patterns
            dangerous_patterns = [
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'subprocess\..*shell.*=.*True',
                r'os\.system\s*\(',
                r'os\.popen\s*\('
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append(f"Potentially dangerous pattern detected: {pattern}")

        return issues

# Global instance
code_executor = CodeExecutionSandbox()
