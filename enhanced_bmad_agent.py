#!/usr/bin/env python3
"""
Enhanced BMAD Agent - Bug Management and Detection Agent
AI-powered code analysis with LLM integration for real-time code review and optimization
"""

import os
import json
import time
import asyncio
import logging
import re
import ast
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import concurrent.futures

import requests
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np

from server import db, Agent, Task, logger
from learning_system import memory_system, adaptive_learning
from openclaw_integration import MultiLLMRouter

class EnhancedBMADAgent:
    """Enhanced Bug Management and Detection Agent with AI capabilities"""
    
    def __init__(self):
        self.name = "Enhanced BMAD Agent"
        self.capabilities = [
            'ai_code_review', 'security_analysis', 'performance_optimization',
            'real_time_detection', 'automatic_fixes', 'vulnerability_scanning'
        ]
        
        # AI components
        self.ai_reviewer = AIReviewer()
        self.security_analyzer = SecurityAnalyzer()
        self.performance_optimizer = PerformanceOptimizer()
        self.vulnerability_scanner = VulnerabilityScanner()
        
        # Learning and memory
        self.knowledge_base = {}
        self.fix_history = []
        self.pattern_cache = {}
        
        # Configuration
        self.severity_thresholds = {
            'critical': 9.0,
            'high': 7.0,
            'medium': 5.0,
            'low': 3.0,
            'info': 1.0
        }
        
        self.auto_fix_enabled = True
        self.learning_enabled = True
        
    async def comprehensive_code_analysis(self, file_path: str) -> Dict[str, Any]:
        """Perform comprehensive AI-powered code analysis"""
        try:
            logger.info(f"🔍 Enhanced BMAD: Analyzing {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Perform multi-layered analysis
            analysis_results = {
                'file_path': file_path,
                'timestamp': datetime.utcnow().isoformat(),
                'ai_review': await self.ai_reviewer.analyze_code(content, file_path),
                'security_issues': await self.security_analyzer.scan_file(content, file_path),
                'performance_issues': await self.performance_optimizer.analyze_performance(content, file_path),
                'vulnerabilities': await self.vulnerability_scanner.scan_vulnerabilities(content, file_path),
                'code_quality': await self.analyze_code_quality(content, file_path),
                'suggestions': await self.generate_suggestions(content, file_path)
            }
            
            # Calculate overall risk score
            analysis_results['risk_score'] = self.calculate_risk_score(analysis_results)
            
            # Store in knowledge base
            if self.learning_enabled:
                self.knowledge_base[file_path] = analysis_results
            
            # Generate report
            report = self.generate_analysis_report(analysis_results)
            
            logger.info(f"✅ Enhanced BMAD: Analysis complete for {file_path}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"❌ Enhanced BMAD: Analysis failed for {file_path}: {str(e)}")
            return {'error': str(e), 'file_path': file_path}
    
    async def real_time_monitoring(self, directory: str = ".", interval: int = 300):
        """Monitor directory for code changes and perform real-time analysis"""
        logger.info(f"👀 Enhanced BMAD: Starting real-time monitoring of {directory}")
        
        while True:
            try:
                # Scan for Python files
                python_files = []
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.py'):
                            python_files.append(os.path.join(root, file))
                
                # Analyze each file
                for file_path in python_files:
                    try:
                        # Check if file was modified recently
                        if self._is_recently_modified(file_path):
                            analysis = await self.comprehensive_code_analysis(file_path)
                            
                            # Auto-fix critical issues
                            if analysis.get('risk_score', 0) > 7.0 and self.auto_fix_enabled:
                                await self.apply_auto_fixes(analysis)
                            
                            # Log critical issues
                            if analysis.get('risk_score', 0) > 8.0:
                                logger.warning(f"🚨 Critical issues detected in {file_path}")
                    
                    except Exception as e:
                        logger.error(f"Failed to analyze {file_path}: {str(e)}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Real-time monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    def _is_recently_modified(self, file_path: str, hours: int = 1) -> bool:
        """Check if file was modified within the last N hours"""
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            return (datetime.now() - mod_time).total_seconds() < hours * 3600
        except:
            return False
    
    async def apply_auto_fixes(self, analysis: Dict[str, Any]):
        """Apply automatic fixes for detected issues"""
        try:
            file_path = analysis['file_path']
            fixes_applied = []
            
            # Apply security fixes
            for issue in analysis.get('security_issues', []):
                if issue['severity'] in ['critical', 'high']:
                    fix = await self.security_analyzer.apply_fix(file_path, issue)
                    if fix['success']:
                        fixes_applied.append(f"Security fix: {issue['type']}")
            
            # Apply performance fixes
            for issue in analysis.get('performance_issues', []):
                if issue['severity'] in ['critical', 'high']:
                    fix = await self.performance_optimizer.apply_fix(file_path, issue)
                    if fix['success']:
                        fixes_applied.append(f"Performance fix: {issue['type']}")
            
            # Apply code quality fixes
            for suggestion in analysis.get('suggestions', []):
                if suggestion['priority'] in ['critical', 'high'] and suggestion.get('auto_fixable', False):
                    fix = await self.apply_code_quality_fix(file_path, suggestion)
                    if fix['success']:
                        fixes_applied.append(f"Quality fix: {suggestion['type']}")
            
            if fixes_applied:
                logger.info(f"🔧 Enhanced BMAD: Applied {len(fixes_applied)} auto-fixes to {file_path}")
                self.fix_history.append({
                    'file_path': file_path,
                    'fixes': fixes_applied,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Auto-fix application failed: {str(e)}")
    
    async def apply_code_quality_fix(self, file_path: str, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Apply code quality fix"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply specific fixes based on suggestion type
            if suggestion['type'] == 'unused_import':
                content = self._remove_unused_imports(content, suggestion['details'])
            elif suggestion['type'] == 'inefficient_loop':
                content = self._optimize_loop(content, suggestion['details'])
            elif suggestion['type'] == 'hardcoded_string':
                content = self._extract_hardcoded_strings(content, suggestion['details'])
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {'success': True, 'message': f"Applied {suggestion['type']} fix"}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _remove_unused_imports(self, content: str, details: Dict[str, Any]) -> str:
        """Remove unused imports from code"""
        lines = content.split('\n')
        used_imports = set(details.get('used_imports', []))
        
        new_lines = []
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                # Check if this import is used
                import_name = self._extract_import_name(line)
                if import_name in used_imports:
                    new_lines.append(line)
                else:
                    logger.info(f"Removing unused import: {line}")
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _extract_import_name(self, import_line: str) -> str:
        """Extract import name from import statement"""
        # Simple extraction - could be enhanced with AST parsing
        if 'import ' in import_line:
            return import_line.split('import ')[1].split()[0].split('.')[0]
        elif 'from ' in import_line:
            return import_line.split('from ')[1].split()[0]
        return ""
    
    def _optimize_loop(self, content: str, details: Dict[str, Any]) -> str:
        """Optimize inefficient loops"""
        # Replace range(len()) with enumerate()
        content = re.sub(
            r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):',
            r'for \1, item in enumerate(\2):',
            content
        )
        
        # Replace manual indexing with direct iteration
        content = re.sub(
            r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):\s*\n\s*(\w+)\s*=\s*(\w+)\[\1\]',
            r'for item in \2:',
            content
        )
        
        return content
    
    def _extract_hardcoded_strings(self, content: str, details: Dict[str, Any]) -> str:
        """Extract hardcoded strings to constants"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated string detection
        lines = content.split('\n')
        constants = []
        
        for i, line in enumerate(lines):
            if '"' in line and not line.strip().startswith('#'):
                # Extract string literals
                strings = re.findall(r'"([^"]*)"', line)
                for string in strings:
                    if len(string) > 10:  # Only extract long strings
                        const_name = f"CONST_{len(constants)}"
                        constants.append(f"{const_name} = \"{string}\"")
                        lines[i] = line.replace(f'"{string}"', const_name)
        
        # Add constants at the top
        if constants:
            content = '\n'.join(constants) + '\n\n' + '\n'.join(lines)
        
        return content
    
    def calculate_risk_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall risk score based on all issues"""
        risk_score = 0.0
        
        # Security risk
        security_issues = analysis.get('security_issues', [])
        for issue in security_issues:
            risk_score += self.severity_thresholds.get(issue['severity'], 0)
        
        # Performance risk
        performance_issues = analysis.get('performance_issues', [])
        for issue in performance_issues:
            risk_score += self.severity_thresholds.get(issue['severity'], 0) * 0.5
        
        # Code quality risk
        quality_issues = analysis.get('code_quality', {}).get('issues', [])
        for issue in quality_issues:
            risk_score += self.severity_thresholds.get(issue.get('severity', 'low'), 0) * 0.3
        
        return min(risk_score, 10.0)  # Cap at 10
    
    def generate_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable analysis report"""
        report = f"""
# Enhanced BMAD Analysis Report

**File:** {analysis['file_path']}
**Timestamp:** {analysis['timestamp']}
**Risk Score:** {analysis.get('risk_score', 0):.1f}/10

## Summary
- Security Issues: {len(analysis.get('security_issues', []))}
- Performance Issues: {len(analysis.get('performance_issues', []))}
- AI Review Score: {analysis.get('ai_review', {}).get('overall_score', 0):.1f}/10

## Critical Issues
"""
        
        # Add critical issues
        for issue in analysis.get('security_issues', []):
            if issue['severity'] in ['critical', 'high']:
                report += f"- **{issue['severity'].upper()}**: {issue['description']}\n"
        
        for issue in analysis.get('performance_issues', []):
            if issue['severity'] in ['critical', 'high']:
                report += f"- **{issue['severity'].upper()}**: {issue['description']}\n"
        
        report += "\n## Recommendations\n"
        for suggestion in analysis.get('suggestions', []):
            if suggestion['priority'] in ['critical', 'high']:
                report += f"- **{suggestion['priority'].upper()}**: {suggestion['description']}\n"
        
        return report

class AIReviewer:
    """AI-powered code reviewer using LLM integration"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
        self.code_patterns = self._load_code_patterns()
    
    def _load_code_patterns(self) -> Dict[str, Any]:
        """Load code quality patterns"""
        return {
            'best_practices': [
                r'def\s+\w+.*:\s*$',  # Function definitions
                r'class\s+\w+.*:\s*$',  # Class definitions
                r'import\s+\w+',  # Import statements
            ],
            'anti_patterns': [
                r'import\s+\*',  # Wildcard imports
                r'for\s+\w+\s+in\s+range\(len\(',  # Inefficient iteration
                r'except\s*:',  # Bare except
                r'eval\(',  # Dangerous eval
                r'exec\(',  # Dangerous exec
            ]
        }
    
    async def analyze_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform AI-powered code review"""
        try:
            # Analyze code structure
            structure = self._analyze_code_structure(content)
            
            # Check for anti-patterns
            anti_patterns = self._check_anti_patterns(content)
            
            # Generate AI review using LLM
            ai_review = await self._generate_ai_review(content, file_path)
            
            return {
                'structure': structure,
                'anti_patterns': anti_patterns,
                'ai_insights': ai_review,
                'overall_score': self._calculate_review_score(structure, anti_patterns, ai_review)
            }
            
        except Exception as e:
            logger.error(f"AI review failed: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_code_structure(self, content: str) -> Dict[str, Any]:
        """Analyze code structure and complexity"""
        try:
            tree = ast.parse(content)
            
            structure = {
                'functions': [],
                'classes': [],
                'imports': [],
                'complexity': 0,
                'lines_of_code': len(content.split('\n'))
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'complexity': self._calculate_function_complexity(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    structure['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure['imports'].append(alias.name)
            
            # Calculate overall complexity
            structure['complexity'] = sum(f['complexity'] for f in structure['functions'])
            
            return structure
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_anti_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Check for anti-patterns in code"""
        anti_patterns = []
        
        for pattern_name, patterns in self.code_patterns['anti_patterns'].items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    anti_patterns.append({
                        'pattern': pattern_name,
                        'line': content[:match.start()].count('\n') + 1,
                        'code': match.group(0),
                        'severity': 'high' if pattern_name in ['eval', 'exec'] else 'medium'
                    })
        
        return anti_patterns
    
    async def _generate_ai_review(self, content: str, file_path: str) -> Dict[str, Any]:
        """Generate AI review using LLM"""
        try:
            # Use the multi-LLM router for code review
            review_task = {
                'description': f"Review this Python code for quality, security, and best practices",
                'content': content[:2000],  # Limit content size
                'file_path': file_path
            }
            
            result = self.multi_llm_router.route_task(review_task)
            
            return {
                'summary': result.get('content', ''),
                'strengths': [],
                'weaknesses': [],
                'suggestions': []
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_review_score(self, structure: Dict[str, Any], anti_patterns: List[Dict[str, Any]], ai_review: Dict[str, Any]) -> float:
        """Calculate overall review score"""
        score = 10.0
        
        # Deduct points for anti-patterns
        for pattern in anti_patterns:
            if pattern['severity'] == 'high':
                score -= 2.0
            elif pattern['severity'] == 'medium':
                score -= 1.0
            else:
                score -= 0.5
        
        # Deduct points for complexity
        if structure.get('complexity', 0) > 20:
            score -= 2.0
        elif structure.get('complexity', 0) > 10:
            score -= 1.0
        
        # Deduct points for too many functions/classes
        if len(structure.get('functions', [])) > 20:
            score -= 1.0
        if len(structure.get('classes', [])) > 10:
            score -= 1.0
        
        return max(0.0, min(10.0, score))

class SecurityAnalyzer:
    """Security vulnerability analyzer"""
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
    
    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Load security vulnerability patterns"""
        return {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'cursor\.execute\s*\(\s*["\'].*\+.*["\']',
            ],
            'xss': [
                r'render_template.*\+.*',
                r'escape\s*\(\s*request\.',
            ],
            'path_traversal': [
                r'open\s*\(\s*request\.',
                r'os\.path\.join.*request\.',
            ],
            'insecure_crypto': [
                r'random\.random\(\)',
                r'hashlib\.md5\(',
                r'hashlib\.sha1\(',
            ]
        }
    
    async def scan_file(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Scan file for security vulnerabilities"""
        vulnerabilities = []
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    vulnerabilities.append({
                        'type': vuln_type,
                        'severity': self._get_vulnerability_severity(vuln_type),
                        'line': content[:match.start()].count('\n') + 1,
                        'code': match.group(0),
                        'description': f"Potential {vuln_type} vulnerability",
                        'cwe': self._get_cwe_mapping(vuln_type)
                    })
        
        return vulnerabilities
    
    def _get_vulnerability_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type"""
        severity_map = {
            'sql_injection': 'critical',
            'xss': 'high',
            'path_traversal': 'high',
            'insecure_crypto': 'medium'
        }
        return severity_map.get(vuln_type, 'low')
    
    def _get_cwe_mapping(self, vuln_type: str) -> str:
        """Get CWE mapping for vulnerability type"""
        cwe_map = {
            'sql_injection': 'CWE-89',
            'xss': 'CWE-79',
            'path_traversal': 'CWE-22',
            'insecure_crypto': 'CWE-327'
        }
        return cwe_map.get(vuln_type, 'CWE-Other')
    
    async def apply_fix(self, file_path: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Apply security fix"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply specific fixes based on vulnerability type
            if issue['type'] == 'sql_injection':
                content = self._fix_sql_injection(content, issue)
            elif issue['type'] == 'xss':
                content = self._fix_xss(content, issue)
            elif issue['type'] == 'path_traversal':
                content = self._fix_path_traversal(content, issue)
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {'success': True, 'message': f"Applied {issue['type']} fix"}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fix_sql_injection(self, content: str, issue: Dict[str, Any]) -> str:
        """Fix SQL injection vulnerability"""
        # Replace string concatenation with parameterized queries
        content = re.sub(
            r'execute\s*\(\s*["\']([^"\']*)\s*\+.*["\']\s*,\s*([^)]+)\)',
            r'execute("\1?", \2)',
            content
        )
        return content
    
    def _fix_xss(self, content: str, issue: Dict[str, Any]) -> str:
        """Fix XSS vulnerability"""
        # Add proper escaping
        content = re.sub(
            r'render_template.*(\w+)',
            r'render_template(escape(\1))',
            content
        )
        return content
    
    def _fix_path_traversal(self, content: str, issue: Dict[str, Any]) -> str:
        """Fix path traversal vulnerability"""
        # Add path validation
        content = re.sub(
            r'open\s*\(\s*request\.(\w+)',
            r'open(os.path.abspath(request.\1))',
            content
        )
        return content

class PerformanceOptimizer:
    """Performance analysis and optimization"""
    
    def __init__(self):
        self.performance_patterns = self._load_performance_patterns()
    
    def _load_performance_patterns(self) -> Dict[str, Any]:
        """Load performance optimization patterns"""
        return {
            'inefficient_loops': [
                r'for\s+\w+\s+in\s+range\(len\((\w+)\)\):',
                r'for\s+\w+\s+in\s+range\(\d+\):',
            ],
            'memory_issues': [
                r'\.append\(',
                r'\.extend\(',
            ],
            'inefficient_operations': [
                r'sort\(',
                r'reverse\(',
            ]
        }
    
    async def analyze_performance(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze code for performance issues"""
        issues = []
        
        for issue_type, patterns in self.performance_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    issues.append({
                        'type': issue_type,
                        'severity': self._get_performance_severity(issue_type),
                        'line': content[:match.start()].count('\n') + 1,
                        'code': match.group(0),
                        'description': f"Potential {issue_type} issue",
                        'optimization': self._get_optimization_suggestion(issue_type)
                    })
        
        return issues
    
    def _get_performance_severity(self, issue_type: str) -> str:
        """Get severity for performance issue"""
        severity_map = {
            'inefficient_loops': 'high',
            'memory_issues': 'medium',
            'inefficient_operations': 'low'
        }
        return severity_map.get(issue_type, 'low')
    
    def _get_optimization_suggestion(self, issue_type: str) -> str:
        """Get optimization suggestion"""
        suggestions = {
            'inefficient_loops': 'Use enumerate() or direct iteration',
            'memory_issues': 'Consider using generators or list comprehensions',
            'inefficient_operations': 'Use in-place operations when possible'
        }
        return suggestions.get(issue_type, 'Review for optimization opportunities')
    
    async def apply_fix(self, file_path: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Apply performance optimization"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply specific optimizations
            if issue['type'] == 'inefficient_loops':
                content = self._optimize_loops(content)
            elif issue['type'] == 'memory_issues':
                content = self._optimize_memory_usage(content)
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {'success': True, 'message': f"Applied {issue['type']} optimization"}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _optimize_loops(self, content: str) -> str:
        """Optimize inefficient loops"""
        # Replace range(len()) with enumerate()
        content = re.sub(
            r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):',
            r'for \1, item in enumerate(\2):',
            content
        )
        return content
    
    def _optimize_memory_usage(self, content: str) -> str:
        """Optimize memory usage"""
        # Replace list.append with list comprehension where appropriate
        content = re.sub(
            r'(\w+)\.append\(([^)]+)\)',
            r'[\2]',
            content
        )
        return content

class VulnerabilityScanner:
    """Advanced vulnerability scanner"""
    
    def __init__(self):
        self.cve_database = {}
        self.dependency_checker = DependencyChecker()
    
    async def scan_vulnerabilities(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Scan for known vulnerabilities"""
        vulnerabilities = []
        
        # Check dependencies
        dependencies = self._extract_dependencies(content)
        for dep in dependencies:
            vulns = await self.dependency_checker.check_vulnerabilities(dep)
            vulnerabilities.extend(vulns)
        
        # Check for hardcoded secrets
        secrets = self._scan_hardcoded_secrets(content)
        vulnerabilities.extend(secrets)
        
        return vulnerabilities
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from code"""
        dependencies = []
        
        # Look for import statements
        import_matches = re.findall(r'import\s+(\w+)', content)
        dependencies.extend(import_matches)
        
        from_matches = re.findall(r'from\s+(\w+)', content)
        dependencies.extend(from_matches)
        
        return list(set(dependencies))
    
    def _scan_hardcoded_secrets(self, content: str) -> List[Dict[str, Any]]:
        """Scan for hardcoded secrets"""
        secrets = []
        
        # API key patterns
        api_key_patterns = [
            r'api[_-]?key\s*=\s*["\']([^"\']{20,})["\']',
            r'secret[_-]?key\s*=\s*["\']([^"\']{20,})["\']',
            r'token\s*=\s*["\']([^"\']{20,})["\']',
        ]
        
        for pattern in api_key_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                secrets.append({
                    'type': 'hardcoded_secret',
                    'severity': 'critical',
                    'line': content[:match.start()].count('\n') + 1,
                    'code': match.group(0),
                    'description': 'Hardcoded API key or secret detected',
                    'recommendation': 'Use environment variables or secure secret management'
                })
        
        return secrets

class DependencyChecker:
    """Check dependencies for known vulnerabilities"""
    
    async def check_vulnerabilities(self, dependency: str) -> List[Dict[str, Any]]:
        """Check dependency for vulnerabilities"""
        # This would integrate with vulnerability databases like NVD
        # For now, return mock data
        return []

# Global instance
enhanced_bmad_agent = EnhancedBMADAgent()

async def main():
    """Test the enhanced BMAD agent"""
    logger.info("🚀 Testing Enhanced BMAD Agent")
    
    # Test with current file
    analysis = await enhanced_bmad_agent.comprehensive_code_analysis(__file__)
    print(f"Analysis complete: Risk score {analysis.get('risk_score', 0):.1f}/10")

if __name__ == "__main__":
    asyncio.run(main())