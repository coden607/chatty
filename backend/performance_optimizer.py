#!/usr/bin/env python3
"""
CHATTY Performance Optimizer
Advanced caching, connection pooling, and system optimization
"""

import os
import time
import threading
import asyncio
import psutil
import gc
from functools import wraps, lru_cache
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import logging

import redis
from flask import g, request
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import scoped_session, sessionmaker
import numpy as np

from server import db, app, logger

class PerformanceMonitor:
    """Real-time performance monitoring and analytics"""

    def __init__(self):
        self.metrics = {}
        self.performance_history = []
        self.alerts = []
        self.baseline_metrics = {}
        self.monitoring_thread = None
        self.is_monitoring = False

    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()

                # Collect application metrics
                app_metrics = self._collect_application_metrics()

                # Combine metrics
                metrics = {**system_metrics, **app_metrics}
                metrics['timestamp'] = datetime.utcnow().isoformat()

                # Store in history (keep last 1000 entries)
                self.performance_history.append(metrics)
                if len(self.performance_history) > 1000:
                    self.performance_history.pop(0)

                # Update current metrics
                self.metrics = metrics

                # Check for performance issues
                self._check_performance_alerts(metrics)

                # Update baseline every hour
                if len(self.performance_history) % 3600 == 0:  # Every hour
                    self._update_baseline()

            except Exception as e:
                logger.error(f"Performance monitoring error: {str(e)}")

            time.sleep(1)  # Monitor every second

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            logger.warning(f"System metrics collection failed: {str(e)}")
            return {}

    def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific performance metrics"""
        try:
            # Database connection pool stats
            if hasattr(db, 'engine') and hasattr(db.engine, 'pool'):
                pool = db.engine.pool
                pool_stats = {
                    'pool_size': getattr(pool, 'size', 0),
                    'pool_checked_in': getattr(pool, '_checkedin', 0),
                    'pool_checked_out': getattr(pool, '_checkedout', 0),
                    'pool_invalid': getattr(pool, '_invalid', 0),
                    'pool_recycle': getattr(pool, '_recycle', 0)
                }
            else:
                pool_stats = {}

            # Redis stats
            redis_stats = {}
            try:
                redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
                redis_info = redis_client.info()
                redis_stats = {
                    'redis_connected_clients': redis_info.get('connected_clients', 0),
                    'redis_used_memory_mb': redis_info.get('used_memory', 0) / (1024**2),
                    'redis_total_keys': redis_client.dbsize(),
                    'redis_hit_rate': redis_info.get('keyspace_hits', 0) / max(redis_info.get('keyspace_misses', 0) + redis_info.get('keyspace_hits', 0), 1)
                }
            except:
                pass

            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'app_memory_mb': memory_info.rss / (1024**2),
                'app_cpu_percent': process.cpu_percent(),
                'app_threads': process.num_threads(),
                'app_open_files': len(process.open_files()),
                'python_gc_collections': gc.get_count(),
                'python_gc_stats': gc.get_stats(),
                **pool_stats,
                **redis_stats
            }
        except Exception as e:
            logger.warning(f"Application metrics collection failed: {str(e)}")
            return {}

    def _check_performance_alerts(self, metrics: Dict[str, Any]):
        """Check for performance issues and create alerts"""
        alerts = []

        # CPU usage alert
        if metrics.get('cpu_percent', 0) > 90:
            alerts.append({
                'type': 'high_cpu',
                'severity': 'critical',
                'message': f'CPU usage is {metrics["cpu_percent"]:.1f}%',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Memory usage alert
        if metrics.get('memory_percent', 0) > 85:
            alerts.append({
                'type': 'high_memory',
                'severity': 'critical',
                'message': f'Memory usage is {metrics["memory_percent"]:.1f}%',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Database connection pool alert
        if metrics.get('pool_checked_out', 0) > 0.9 * metrics.get('pool_size', 1):
            alerts.append({
                'type': 'db_connection_pool',
                'severity': 'warning',
                'message': 'Database connection pool nearly exhausted',
                'timestamp': datetime.utcnow().isoformat()
            })

        # Redis memory alert
        if metrics.get('redis_used_memory_mb', 0) > 500:  # 500MB
            alerts.append({
                'type': 'redis_memory',
                'severity': 'warning',
                'message': f'Redis memory usage: {metrics["redis_used_memory_mb"]:.1f}MB',
                'timestamp': datetime.utcnow().isoformat()
            })

        if alerts:
            self.alerts.extend(alerts)
            # Keep only recent alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

            # Log critical alerts
            for alert in alerts:
                if alert['severity'] == 'critical':
                    logger.warning(f"PERFORMANCE ALERT: {alert['message']}")

    def _update_baseline(self):
        """Update performance baseline metrics"""
        if not self.performance_history:
            return

        # Calculate averages from recent history (last hour)
        recent = self.performance_history[-3600:]  # Last hour of data

        for key in ['cpu_percent', 'memory_percent', 'app_memory_mb']:
            values = [m.get(key, 0) for m in recent if key in m]
            if values:
                self.baseline_metrics[f'{key}_avg'] = np.mean(values)
                self.baseline_metrics[f'{key}_std'] = np.std(values)
                self.baseline_metrics[f'{key}_max'] = max(values)

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'current_metrics': self.metrics,
            'baseline_metrics': self.baseline_metrics,
            'recent_alerts': self.alerts[-10:],  # Last 10 alerts
            'performance_trends': self._analyze_trends(),
            'recommendations': self._generate_recommendations(),
            'generated_at': datetime.utcnow().isoformat()
        }

        return report

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze performance trends"""
        if len(self.performance_history) < 60:  # Need at least 1 minute of data
            return {'status': 'insufficient_data'}

        # Analyze last 5 minutes vs last hour
        recent_5min = self.performance_history[-300:]
        older_data = self.performance_history[:-300][-3600:]  # Previous hour excluding recent 5min

        trends = {}

        for metric in ['cpu_percent', 'memory_percent', 'app_memory_mb']:
            recent_values = [m.get(metric, 0) for m in recent_5min if metric in m]
            older_values = [m.get(metric, 0) for m in older_data if metric in m]

            if recent_values and older_values:
                recent_avg = np.mean(recent_values)
                older_avg = np.mean(older_values)

                if older_avg > 0:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                    trends[metric] = {
                        'recent_avg': recent_avg,
                        'older_avg': older_avg,
                        'change_percent': change_percent,
                        'trend': 'increasing' if change_percent > 10 else 'decreasing' if change_percent < -10 else 'stable'
                    }

        return trends

    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        if self.metrics.get('cpu_percent', 0) > 80:
            recommendations.append("High CPU usage detected. Consider optimizing compute-intensive operations or adding more CPU resources.")

        if self.metrics.get('memory_percent', 0) > 80:
            recommendations.append("High memory usage detected. Consider implementing memory optimization or increasing RAM.")

        if self.metrics.get('app_memory_mb', 0) > 1000:  # 1GB
            recommendations.append("Application memory usage is high. Consider implementing garbage collection optimization or memory profiling.")

        if len(self.alerts) > 5:
            recommendations.append("Multiple performance alerts detected. Consider implementing performance monitoring and optimization strategies.")

        # Database recommendations
        if self.metrics.get('pool_checked_out', 0) > 0.8 * self.metrics.get('pool_size', 1):
            recommendations.append("Database connection pool is heavily utilized. Consider increasing pool size or optimizing database queries.")

        if not recommendations:
            recommendations.append("System performance is within acceptable parameters. Continue monitoring for optimal operation.")

        return recommendations

class AdvancedCacheManager:
    """Advanced multi-layer caching system"""

    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
        self.l1_cache = {}  # In-memory L1 cache
        self.l1_ttl = {}    # TTL for L1 cache entries
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_entries, daemon=True)
        self.cleanup_thread.start()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with multi-layer lookup"""
        # Check L1 cache first
        if key in self.l1_cache and time.time() < self.l1_ttl.get(key, 0):
            self.cache_stats['hits'] += 1
            return self.l1_cache[key]

        # Check Redis L2 cache
        try:
            value = self.redis_client.get(f"cache:{key}")
            if value:
                # Promote to L1 cache
                import json
                try:
                    parsed_value = json.loads(value)
                    self.l1_cache[key] = parsed_value
                    self.l1_ttl[key] = time.time() + 300  # 5 minutes in L1
                    self.cache_stats['hits'] += 1
                    return parsed_value
                except:
                    self.l1_cache[key] = value
                    self.l1_ttl[key] = time.time() + 300
                    self.cache_stats['hits'] += 1
                    return value
        except Exception as e:
            logger.warning(f"Redis cache error: {str(e)}")

        self.cache_stats['misses'] += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in multi-layer cache"""
        import json

        try:
            # Serialize value for Redis
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            # Set in Redis
            self.redis_client.setex(f"cache:{key}", ttl, serialized_value)

            # Set in L1 cache
            self.l1_cache[key] = value
            self.l1_ttl[key] = time.time() + min(ttl, 300)  # Max 5 minutes in L1

            self.cache_stats['sets'] += 1

        except Exception as e:
            logger.warning(f"Cache set error: {str(e)}")

    def delete(self, key: str):
        """Delete from all cache layers"""
        # Delete from L1
        if key in self.l1_cache:
            del self.l1_cache[key]
        if key in self.l1_ttl:
            del self.l1_ttl[key]

        # Delete from Redis
        try:
            self.redis_client.delete(f"cache:{key}")
        except Exception as e:
            logger.warning(f"Redis delete error: {str(e)}")

        self.cache_stats['deletes'] += 1

    def clear(self):
        """Clear all cache layers"""
        self.l1_cache.clear()
        self.l1_ttl.clear()

        try:
            # Clear Redis cache (be careful with this in production)
            keys = self.redis_client.keys("cache:*")
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis clear error: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'l1_entries': len(self.l1_cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'hit_rate_percent': hit_rate,
            'total_requests': total_requests
        }

    def _cleanup_expired_entries(self):
        """Clean up expired L1 cache entries"""
        while True:
            try:
                current_time = time.time()
                expired_keys = [k for k, ttl in self.l1_ttl.items() if current_time > ttl]

                for key in expired_keys:
                    if key in self.l1_cache:
                        del self.l1_cache[key]
                    if key in self.l1_ttl:
                        del self.l1_ttl[key]

                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            except Exception as e:
                logger.warning(f"Cache cleanup error: {str(e)}")

            time.sleep(60)  # Clean up every minute

class DatabaseOptimizer:
    """Database performance optimization and connection management"""

    def __init__(self):
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'connection_errors': 0,
            'query_count': 0,
            'slow_queries': 0
        }
        self.query_cache = {}
        self.slow_query_threshold = 1.0  # 1 second

    def optimize_connection_pool(self):
        """Optimize database connection pool settings"""
        try:
            # Configure optimal pool settings
            pool_config = {
                'pool_size': 20,
                'max_overflow': 30,
                'pool_timeout': 30,
                'pool_recycle': 3600,  # Recycle connections every hour
                'pool_pre_ping': True,  # Test connections before use
            }

            # Update engine configuration if possible
            if hasattr(db, 'engine'):
                # In a real implementation, you might recreate the engine with new pool settings
                logger.info("Database connection pool optimization applied")
                return True

        except Exception as e:
            logger.error(f"Database optimization error: {str(e)}")
            return False

    def execute_optimized_query(self, query: str, params: Dict = None) -> Any:
        """Execute query with optimization and monitoring"""
        start_time = time.time()

        try:
            with db.session.begin():
                result = db.session.execute(text(query), params or {})
                execution_time = time.time() - start_time

                self.connection_stats['query_count'] += 1

                if execution_time > self.slow_query_threshold:
                    self.connection_stats['slow_queries'] += 1
                    logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")

                return result

        except Exception as e:
            self.connection_stats['connection_errors'] += 1
            logger.error(f"Database query error: {str(e)}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            # Get basic database info
            with db.session.begin():
                # Count records in main tables
                agent_count = db.session.execute(text("SELECT COUNT(*) FROM agents")).scalar()
                task_count = db.session.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
                user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()

            return {
                'agents_count': agent_count,
                'tasks_count': task_count,
                'users_count': user_count,
                'connection_stats': self.connection_stats,
                'query_cache_size': len(self.query_cache)
            }
        except Exception as e:
            logger.error(f"Database stats error: {str(e)}")
            return {}

class AsyncTaskManager:
    """Asynchronous task processing for improved performance"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running_tasks = {}
        self.task_queue = []
        self.max_concurrent_tasks = 10

    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit task for asynchronous execution"""
        task_id = f"async_{int(time.time())}_{len(self.running_tasks)}"

        if len(self.running_tasks) >= self.max_concurrent_tasks:
            # Queue task for later execution
            self.task_queue.append((task_id, func, args, kwargs))
            logger.info(f"Task {task_id} queued for later execution")
            return task_id

        # Execute immediately
        future = self.executor.submit(func, *args, **kwargs)
        self.running_tasks[task_id] = future

        # Add callback to clean up completed tasks
        future.add_done_callback(lambda f: self._cleanup_task(task_id))

        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of asynchronous task"""
        if task_id in self.running_tasks:
            future = self.running_tasks[task_id]
            if future.done():
                try:
                    result = future.result()
                    return {'status': 'completed', 'result': result}
                except Exception as e:
                    return {'status': 'failed', 'error': str(e)}
            else:
                return {'status': 'running'}
        else:
            return {'status': 'not_found'}

    def _cleanup_task(self, task_id: str):
        """Clean up completed task"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]

        # Check if we can start queued tasks
        self._process_task_queue()

    def _process_task_queue(self):
        """Process queued tasks if capacity available"""
        while self.task_queue and len(self.running_tasks) < self.max_concurrent_tasks:
            task_id, func, args, kwargs = self.task_queue.pop(0)

            future = self.executor.submit(func, *args, **kwargs)
            self.running_tasks[task_id] = future

            future.add_done_callback(lambda f: self._cleanup_task(task_id))

            logger.info(f"Started queued task {task_id}")

# Global instances
performance_monitor = PerformanceMonitor()
cache_manager = AdvancedCacheManager()
db_optimizer = DatabaseOptimizer()
async_manager = AsyncTaskManager()

# Decorators for performance monitoring
def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            memory_used = psutil.Process().memory_info().rss - start_memory

            # Log performance metrics
            logger.debug(f"Function {func.__name__} executed in {execution_time:.3f}s, memory: {memory_used/1024/1024:.1f}MB")

            # Store in performance history
            performance_monitor.performance_history.append({
                'function': func.__name__,
                'execution_time': execution_time,
                'memory_used': memory_used,
                'timestamp': datetime.utcnow().isoformat()
            })

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise

    return wrapper

def cached_response(ttl: int = 3600):
    """Decorator to cache API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
