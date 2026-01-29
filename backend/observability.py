"""
NexusForge Observability Backend
Advanced logging and monitoring system for AI agents and system operations
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import structlog
from functools import wraps

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

class NexusForgeObservability:
    """Comprehensive observability system for NexusForge"""

    def __init__(self, redis_client=None, max_events=10000, max_metrics=1000):
        self.redis_client = redis_client
        self.max_events = max_events
        self.max_metrics = max_metrics

        # In-memory storage (with Redis fallback)
        self.events = deque(maxlen=max_events)
        self.metrics = {}
        self.active_streams = set()
        self.alerts = []

        # Performance tracking
        self.performance_data = defaultdict(list)
        self.system_health = {}

        # Agent tracking
        self.agent_activities = defaultdict(list)
        self.agent_metrics = defaultdict(dict)

        # Communication tracking
        self.communication_log = deque(maxlen=5000)

        # Initialize background monitoring
        self._start_background_monitoring()

        logger.info("observability_system_initialized", component="NexusForgeObservability")

    def _start_background_monitoring(self):
        """Start background monitoring threads"""
        def health_check():
            while True:
                try:
                    self._update_system_health()
                    time.sleep(60)  # Every minute
                except Exception as e:
                    logger.error("health_check_failed", error=str(e))

        def cleanup_old_data():
            while True:
                try:
                    self._cleanup_old_data()
                    time.sleep(3600)  # Every hour
                except Exception as e:
                    logger.error("cleanup_failed", error=str(e))

        threading.Thread(target=health_check, daemon=True).start()
        threading.Thread(target=cleanup_old_data, daemon=True).start()

    def _update_system_health(self):
        """Update system health metrics"""
        self.system_health.update({
            'timestamp': datetime.utcnow().isoformat(),
            'events_count': len(self.events),
            'active_streams': len(self.active_streams),
            'total_metrics': len(self.metrics),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage()
        })

        # Check for alerts
        self._check_alerts()

    def _get_memory_usage(self):
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0

    def _get_cpu_usage(self):
        """Get current CPU usage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0

    def _cleanup_old_data(self):
        """Clean up old data to prevent memory issues"""
        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Clean old events
        while self.events and datetime.fromisoformat(self.events[0]['timestamp']) < cutoff:
            self.events.popleft()

        # Clean old performance data
        for key in list(self.performance_data.keys()):
            self.performance_data[key] = [
                item for item in self.performance_data[key]
                if datetime.fromisoformat(item['timestamp']) > cutoff
            ]
            if not self.performance_data[key]:
                del self.performance_data[key]

    def _check_alerts(self):
        """Check for system alerts"""
        alerts = []

        # Memory usage alert
        if self.system_health.get('memory_usage', 0) > 500:  # > 500MB
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f'High memory usage: {self.system_health["memory_usage"]:.1f}MB'
            })

        # Too many events alert
        if len(self.events) > self.max_events * 0.9:
            alerts.append({
                'type': 'events_overflow',
                'severity': 'warning',
                'message': f'Event queue near capacity: {len(self.events)}/{self.max_events}'
            })

        self.alerts = alerts[-10:]  # Keep last 10 alerts

    # Event logging methods
    def log_event(self, category: str, action: str, details: Dict[str, Any] = None,
                  level: str = 'info', source: str = 'system'):
        """Log a system event"""
        event = {
            'id': f"evt_{int(time.time() * 1000000)}",
            'timestamp': datetime.utcnow().isoformat(),
            'category': category,
            'action': action,
            'details': details or {},
            'level': level,
            'source': source
        }

        self.events.append(event)

        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.lpush('nexusforge:events', json.dumps(event))
                self.redis_client.ltrim('nexusforge:events', 0, self.max_events - 1)
            except Exception as e:
                logger.warning("redis_event_storage_failed", error=str(e))

        # Structured logging
        log_func = getattr(logger, level, logger.info)
        log_func("event_logged", **event)

        return event

    def log_agent_activity(self, agent_id: str, agent_name: str, activity: str,
                          details: Dict[str, Any] = None):
        """Log agent-specific activity"""
        event = self.log_event('agent', activity, {
            'agent_id': agent_id,
            'agent_name': agent_name,
            **(details or {})
        })

        # Update agent metrics
        self.agent_activities[agent_id].append({
            'timestamp': event['timestamp'],
            'activity': activity,
            'details': details or {}
        })

        # Keep only recent activities
        if len(self.agent_activities[agent_id]) > 100:
            self.agent_activities[agent_id] = self.agent_activities[agent_id][-100:]

        self.agent_metrics[agent_id].update({
            'last_activity': event['timestamp'],
            'total_activities': len(self.agent_activities[agent_id]),
            'name': agent_name
        })

    def log_api_call(self, endpoint: str, method: str, status_code: int,
                    duration_ms: float, details: Dict[str, Any] = None):
        """Log API call"""
        self.log_event('api', f'{method} {endpoint}', {
            'status_code': status_code,
            'duration_ms': duration_ms,
            **(details or {})
        }, 'info' if status_code < 400 else 'error')

        # Update API metrics
        api_key = f'{method}_{endpoint}'
        if api_key not in self.metrics:
            self.metrics[api_key] = {
                'calls': 0, 'errors': 0, 'total_duration': 0, 'avg_duration': 0
            }

        self.metrics[api_key]['calls'] += 1
        self.metrics[api_key]['total_duration'] += duration_ms
        self.metrics[api_key]['avg_duration'] = (
            self.metrics[api_key]['total_duration'] / self.metrics[api_key]['calls']
        )

        if status_code >= 400:
            self.metrics[api_key]['errors'] += 1

    def log_performance(self, metric_name: str, value: float, unit: str = '',
                       tags: Dict[str, Any] = None):
        """Log performance metric"""
        data_point = {
            'timestamp': datetime.utcnow().isoformat(),
            'value': value,
            'unit': unit,
            'tags': tags or {}
        }

        self.performance_data[metric_name].append(data_point)

        # Keep only recent data points
        if len(self.performance_data[metric_name]) > 1000:
            self.performance_data[metric_name] = self.performance_data[metric_name][-1000:]

        self.log_event('performance', f'{metric_name} recorded', {
            'value': value,
            'unit': unit,
            **(tags or {})
        }, 'debug')

    def log_communication(self, from_agent: str, to_agent: str, message: str,
                         message_type: str = 'direct', metadata: Dict[str, Any] = None):
        """Log inter-agent communication"""
        comm = {
            'timestamp': datetime.utcnow().isoformat(),
            'from_agent': from_agent,
            'to_agent': to_agent,
            'message': message[:500],  # Truncate long messages
            'type': message_type,
            'metadata': metadata or {}
        }

        self.communication_log.append(comm)

        self.log_event('communication', f'{message_type} message', {
            'from': from_agent,
            'to': to_agent,
            'message_length': len(message),
            'type': message_type
        }, 'debug')

    def log_task(self, task_id: str, task_name: str, status: str,
                agent_id: str = None, details: Dict[str, Any] = None):
        """Log task execution"""
        self.log_event('task', f'{status}: {task_name}', {
            'task_id': task_id,
            'task_name': task_name,
            'status': status,
            'agent_id': agent_id,
            **(details or {})
        }, 'error' if status == 'failed' else 'info')

        # Update task metrics
        if 'tasks' not in self.metrics:
            self.metrics['tasks'] = {'total': 0, 'completed': 0, 'failed': 0}

        self.metrics['tasks']['total'] += 1
        if status == 'completed':
            self.metrics['tasks']['completed'] += 1
        elif status == 'failed':
            self.metrics['tasks']['failed'] += 1

    def log_learning_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log learning-related activity"""
        self.log_event('learning', activity, details or {}, 'info')

        # Update learning metrics
        if 'learning' not in self.metrics:
            self.metrics['learning'] = {'sessions': 0, 'videos': 0, 'skills': 0}

        self.metrics['learning']['sessions'] += 1
        if details and 'video_id' in details:
            self.metrics['learning']['videos'] += 1
        if details and 'skill' in details:
            self.metrics['learning']['skills'] += 1

    # Data retrieval methods
    def get_recent_events(self, limit: int = 100, category: str = None) -> List[Dict]:
        """Get recent events"""
        events = list(self.events)
        if category:
            events = [e for e in events if e['category'] == category]
        return events[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'system': self.system_health,
            'agents': dict(self.agent_metrics),
            'performance': dict(self.performance_data),
            'api': {k: v for k, v in self.metrics.items() if '_' in k},
            'tasks': self.metrics.get('tasks', {}),
            'learning': self.metrics.get('learning', {}),
            'alerts': self.alerts
        }

    def get_agent_activities(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """Get activities for a specific agent"""
        return list(self.agent_activities.get(agent_id, []))[-limit:]

    def get_communication_log(self, limit: int = 100) -> List[Dict]:
        """Get recent communications"""
        return list(self.communication_log)[-limit:]

    def export_data(self) -> Dict[str, Any]:
        """Export all observability data"""
        return {
            'events': list(self.events),
            'metrics': self.get_metrics(),
            'communication_log': list(self.communication_log),
            'exported_at': datetime.utcnow().isoformat()
        }

# Global observability instance
observability = None

def init_observability(redis_client=None):
    """Initialize global observability system"""
    global observability
    observability = NexusForgeObservability(redis_client)
    return observability

def get_observability():
    """Get global observability instance"""
    return observability

# Flask middleware for automatic logging
def observability_middleware(app):
    """Add observability middleware to Flask app"""

    @app.before_request
    def log_request_start():
        g.request_start_time = time.time()
        g.request_id = f"req_{int(time.time() * 1000000)}"

        if observability:
            observability.log_event('http', 'request_started', {
                'method': request.method,
                'path': request.path,
                'user_agent': request.headers.get('User-Agent', ''),
                'ip': request.remote_addr
            })

    @app.after_request
    def log_request_end(response):
        if hasattr(g, 'request_start_time'):
            duration = (time.time() - g.request_start_time) * 1000

            if observability:
                observability.log_api_call(
                    request.path,
                    request.method,
                    response.status_code,
                    duration,
                    {
                        'user_agent': request.headers.get('User-Agent', ''),
                        'content_length': response.content_length,
                        'request_id': getattr(g, 'request_id', '')
                    }
                )

        return response

    @app.errorhandler(Exception)
    def log_error(error):
        if observability:
            observability.log_event('error', 'uncaught_exception', {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'path': request.path,
                'method': request.method
            }, 'error')

        return jsonify({'error': 'Internal server error'}), 500

# Decorator for agent function logging
def log_agent_action(action_name: str):
    """Decorator to log agent actions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            agent_id = getattr(args[0] if args else None, 'id', 'unknown')
            agent_name = getattr(args[0] if args else None, 'name', 'Unknown Agent')

            if observability:
                observability.log_agent_activity(agent_id, agent_name, f'starting_{action_name}')

            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                if observability:
                    duration = time.time() - start_time
                    observability.log_agent_activity(agent_id, agent_name, f'completed_{action_name}', {
                        'duration': duration,
                        'success': True
                    })

                return result
            except Exception as e:
                if observability:
                    duration = time.time() - start_time
                    observability.log_agent_activity(agent_id, agent_name, f'failed_{action_name}', {
                        'duration': duration,
                        'error': str(e),
                        'success': False
                    })

                raise

        return wrapper
    return decorator
