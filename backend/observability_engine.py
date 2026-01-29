#!/usr/bin/env python3
"""
CHATTY Observability Engine
Real-time monitoring, advanced analytics, and performance dashboards
"""

import os
import time
import json
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import statistics
import psutil

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from flask import Flask, render_template_string, jsonify

from server import db, Agent, Task, Execution, logger
from performance_optimizer import performance_monitor

class RealTimeDashboard:
    """Real-time monitoring dashboard"""

    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.alerts = deque(maxlen=100)
        self.dashboard_data = {}
        self.update_interval = 5  # seconds

        # Start dashboard update thread
        self.dashboard_thread = threading.Thread(target=self._dashboard_update_loop, daemon=True)
        self.dashboard_thread.start()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data

    def _dashboard_update_loop(self):
        """Continuous dashboard updates"""
        while True:
            try:
                # Collect all metrics
                system_metrics = self._collect_system_metrics()
                application_metrics = self._collect_application_metrics()
                business_metrics = self._collect_business_metrics()

                # Combine all data
                dashboard_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'system': system_metrics,
                    'application': application_metrics,
                    'business': business_metrics,
                    'alerts': list(self.alerts)[-5:],  # Last 5 alerts
                    'performance_trends': self._calculate_trends()
                }

                self.dashboard_data = dashboard_data

                # Store in history for trend analysis
                for key, value in system_metrics.items():
                    if isinstance(value, (int, float)):
                        self.metrics_history[f'system_{key}'].append((datetime.utcnow(), value))

                for key, value in application_metrics.items():
                    if isinstance(value, (int, float)):
                        self.metrics_history[f'app_{key}'].append((datetime.utcnow(), value))

            except Exception as e:
                logger.error(f"Dashboard update error: {str(e)}")

            time.sleep(self.update_interval)

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics"""
        try:
            cpu = psutil.cpu_times_percent()
            memory = psutil.memory_info()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_user': cpu.user,
                'cpu_system': cpu.system,
                'memory_used_percent': psutil.virtual_memory().percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'disk_used_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent_mb': network.bytes_sent / (1024**2),
                'network_bytes_recv_mb': network.bytes_recv / (1024**2),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.warning(f"System metrics collection failed: {str(e)}")
            return {}

    def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            # Get performance monitor data
            perf_report = performance_monitor.get_performance_report()

            # Database metrics
            with db.session.begin():
                agent_count = db.session.query(Agent).count()
                active_agents = db.session.query(Agent).filter_by(status='active').count()
                task_count = db.session.query(Task).count()
                completed_tasks = db.session.query(Task).filter_by(status='completed').count()
                execution_count = db.session.query(Execution).count()

            return {
                'total_agents': agent_count,
                'active_agents': active_agents,
                'agent_utilization_percent': (active_agents / max(agent_count, 1)) * 100,
                'total_tasks': task_count,
                'completed_tasks': completed_tasks,
                'task_completion_rate': (completed_tasks / max(task_count, 1)) * 100,
                'total_executions': execution_count,
                'performance_score': perf_report.get('current_metrics', {}).get('cpu_percent', 0),
                'memory_usage_mb': perf_report.get('current_metrics', {}).get('app_memory_mb', 0),
                'response_time_avg': 0.1  # Placeholder - would be calculated from actual requests
            }
        except Exception as e:
            logger.warning(f"Application metrics collection failed: {str(e)}")
            return {}

    def _collect_business_metrics(self) -> Dict[str, Any]:
        """Collect business-level metrics"""
        try:
            with db.session.begin():
                # Task success rates by type
                task_types = db.session.query(Task.task_type, Task.status).all()
                type_stats = defaultdict(lambda: {'total': 0, 'completed': 0})

                for task_type, status in task_types:
                    type_stats[task_type]['total'] += 1
                    if status == 'completed':
                        type_stats[task_type]['completed'] += 1

                task_success_rates = {}
                for task_type, stats in type_stats.items():
                    success_rate = (stats['completed'] / max(stats['total'], 1)) * 100
                    task_success_rates[task_type or 'general'] = success_rate

                # Agent performance
                agent_performance = {}
                agents = db.session.query(Agent).all()
                for agent in agents:
                    executions = db.session.query(Execution).filter_by(agent_id=agent.id).all()
                    if executions:
                        success_count = sum(1 for e in executions if e.status == 'completed')
                        success_rate = (success_count / len(executions)) * 100
                        agent_performance[agent.name] = {
                            'success_rate': success_rate,
                            'total_executions': len(executions),
                            'avg_duration': statistics.mean([e.duration for e in executions if e.duration])
                        }

                return {
                    'task_success_rates': task_success_rates,
                    'agent_performance': agent_performance,
                    'system_uptime_hours': time.time() / 3600,  # Rough estimate
                    'active_workflows': 0,  # Placeholder
                    'user_satisfaction_score': 85  # Placeholder - would be calculated from feedback
                }
        except Exception as e:
            logger.warning(f"Business metrics collection failed: {str(e)}")
            return {}

    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends"""
        trends = {}

        for metric_name, data_points in self.metrics_history.items():
            if len(data_points) >= 10:
                # Get last 10 points vs previous 10 points
                recent = [value for _, value in data_points][-10:]
                older = [value for _, value in data_points][-20:-10] if len(data_points) >= 20 else recent

                if older:
                    recent_avg = statistics.mean(recent)
                    older_avg = statistics.mean(older)

                    if older_avg > 0:
                        change_percent = ((recent_avg - older_avg) / older_avg) * 100
                        trends[metric_name] = {
                            'direction': 'increasing' if change_percent > 5 else 'decreasing' if change_percent < -5 else 'stable',
                            'change_percent': change_percent,
                            'current_avg': recent_avg,
                            'previous_avg': older_avg
                        }

        return trends

    def create_performance_charts(self) -> Dict[str, Any]:
        """Create performance visualization charts"""
        charts = {}

        try:
            # CPU Usage Chart
            if 'system_cpu_percent' in self.metrics_history:
                timestamps, values = zip(*self.metrics_history['system_cpu_percent'][-50:])
                charts['cpu_usage'] = {
                    'type': 'line',
                    'title': 'CPU Usage Over Time',
                    'x': [t.isoformat() for t in timestamps],
                    'y': values,
                    'color': 'red'
                }

            # Memory Usage Chart
            if 'system_memory_used_percent' in self.metrics_history:
                timestamps, values = zip(*self.metrics_history['system_memory_used_percent'][-50:])
                charts['memory_usage'] = {
                    'type': 'line',
                    'title': 'Memory Usage Over Time',
                    'x': [t.isoformat() for t in timestamps],
                    'y': values,
                    'color': 'blue'
                }

            # Task Completion Rate Chart
            business_data = self.dashboard_data.get('business', {})
            task_rates = business_data.get('task_success_rates', {})

            if task_rates:
                charts['task_completion'] = {
                    'type': 'bar',
                    'title': 'Task Completion Rates by Type',
                    'x': list(task_rates.keys()),
                    'y': list(task_rates.values()),
                    'color': 'green'
                }

        except Exception as e:
            logger.error(f"Chart creation error: {str(e)}")

        return charts

class AdvancedAnalyticsEngine:
    """Advanced analytics and predictive modeling"""

    def __init__(self):
        self.time_series_data = defaultdict(list)
        self.predictive_models = {}
        self.anomaly_threshold = 3.0

    def analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns and predict issues"""
        analysis = {
            'peak_usage_times': self._identify_peak_times(),
            'performance_correlations': self._find_correlations(),
            'predicted_issues': self._predict_performance_issues(),
            'optimization_recommendations': self._generate_optimization_recommendations(),
            'capacity_planning': self._capacity_planning_analysis()
        }

        return analysis

    def _identify_peak_times(self) -> List[Dict[str, Any]]:
        """Identify peak usage times"""
        peaks = []

        # Analyze CPU usage patterns
        cpu_data = self.time_series_data.get('cpu_percent', [])
        if len(cpu_data) >= 24:  # At least 24 data points
            # Simple peak detection
            values = [v for _, v in cpu_data[-24:]]  # Last 24 points
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0

            peak_threshold = mean_val + (std_val * 1.5)

            for i, (timestamp, value) in enumerate(cpu_data[-24:]):
                if value > peak_threshold:
                    peaks.append({
                        'timestamp': timestamp.isoformat(),
                        'metric': 'cpu_percent',
                        'value': value,
                        'hour': timestamp.hour
                    })

        return peaks

    def _find_correlations(self) -> List[Dict[str, Any]]:
        """Find correlations between different metrics"""
        correlations = []

        # Example correlation analysis
        if len(self.time_series_data.get('cpu_percent', [])) >= 20:
            cpu_values = [v for _, v in self.time_series_data['cpu_percent'][-20:]]
            memory_values = [v for _, v in self.time_series_data.get('memory_percent', self.time_series_data['cpu_percent'])[-20:]]

            if len(memory_values) == len(cpu_values):
                try:
                    correlation = np.corrcoef(cpu_values, memory_values)[0, 1]
                    if abs(correlation) > 0.7:
                        correlations.append({
                            'metric1': 'cpu_percent',
                            'metric2': 'memory_percent',
                            'correlation': correlation,
                            'strength': 'strong' if abs(correlation) > 0.8 else 'moderate'
                        })
                except:
                    pass

        return correlations

    def _predict_performance_issues(self) -> List[Dict[str, Any]]:
        """Predict potential performance issues"""
        predictions = []

        # Simple threshold-based predictions
        current_data = self.time_series_data

        # CPU usage prediction
        cpu_trend = self._calculate_trend(current_data.get('cpu_percent', []))
        if cpu_trend > 10:  # Trending up significantly
            predictions.append({
                'issue': 'High CPU Usage',
                'severity': 'medium',
                'confidence': 0.8,
                'timeframe': 'next_hour',
                'recommendation': 'Consider scaling compute resources or optimizing CPU-intensive operations'
            })

        # Memory usage prediction
        memory_trend = self._calculate_trend(current_data.get('memory_percent', []))
        if memory_trend > 10:
            predictions.append({
                'issue': 'Memory Pressure',
                'severity': 'high',
                'confidence': 0.9,
                'timeframe': 'next_hour',
                'recommendation': 'Implement memory optimization or increase RAM allocation'
            })

        return predictions

    def _calculate_trend(self, data_points: List[Tuple[datetime, float]]) -> float:
        """Calculate trend percentage from data points"""
        if len(data_points) < 10:
            return 0.0

        # Simple linear trend calculation
        values = [value for _, value in data_points[-10:]]
        x = list(range(len(values)))

        if len(values) > 1:
            slope = np.polyfit(x, values, 1)[0]
            avg_value = statistics.mean(values)

            if avg_value > 0:
                return (slope * len(values) / avg_value) * 100

        return 0.0

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Analyze current metrics for optimization opportunities
        current_data = self.time_series_data

        # CPU optimization
        cpu_avg = self._get_average(current_data.get('cpu_percent', []))
        if cpu_avg > 70:
            recommendations.append("High CPU usage detected. Consider implementing async processing for CPU-intensive tasks.")

        # Memory optimization
        memory_avg = self._get_average(current_data.get('memory_percent', []))
        if memory_avg > 80:
            recommendations.append("High memory usage detected. Implement memory pooling and garbage collection optimization.")

        # Database optimization
        if len(current_data.get('db_connections', [])) > 0:
            db_avg = self._get_average(current_data.get('db_connections', []))
            if db_avg > 80:  # Assuming 80% of max connections
                recommendations.append("Database connection pool heavily utilized. Consider increasing pool size or optimizing queries.")

        if not recommendations:
            recommendations.append("System performance is within acceptable parameters. Continue monitoring for optimal operation.")

        return recommendations

    def _capacity_planning_analysis(self) -> Dict[str, Any]:
        """Analyze capacity planning requirements"""
        analysis = {
            'current_utilization': {},
            'growth_trends': {},
            'capacity_recommendations': []
        }

        # Current utilization
        for metric_name in ['cpu_percent', 'memory_percent', 'disk_percent']:
            values = self.time_series_data.get(metric_name, [])
            if values:
                current_avg = self._get_average(values)
                analysis['current_utilization'][metric_name] = current_avg

                # Simple growth projection
                trend = self._calculate_trend(values)
                analysis['growth_trends'][metric_name] = trend

                # Capacity recommendations
                if current_avg > 80:
                    analysis['capacity_recommendations'].append(f"Immediate capacity increase needed for {metric_name}")
                elif current_avg > 60:
                    analysis['capacity_recommendations'].append(f"Monitor {metric_name} closely - approaching capacity limits")

        return analysis

    def _get_average(self, data_points: List[Tuple[datetime, float]]) -> float:
        """Get average value from time series data"""
        if not data_points:
            return 0.0

        values = [value for _, value in data_points[-20:]]  # Last 20 points
        return statistics.mean(values) if values else 0.0

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update time series data with new metrics"""
        timestamp = datetime.utcnow()

        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.time_series_data[metric_name].append((timestamp, value))

                # Keep only last 1000 points
                if len(self.time_series_data[metric_name]) > 1000:
                    self.time_series_data[metric_name].pop(0)

class PredictiveMaintenance:
    """Predictive maintenance for system components"""

    def __init__(self):
        self.component_health = {}
        self.failure_predictions = []
        self.maintenance_schedule = []

    def analyze_component_health(self) -> Dict[str, Any]:
        """Analyze health of system components"""
        components = {
            'cpu': self._analyze_cpu_health(),
            'memory': self._analyze_memory_health(),
            'disk': self._analyze_disk_health(),
            'network': self._analyze_network_health(),
            'database': self._analyze_database_health()
        }

        # Update component health scores
        self.component_health = {comp: data['health_score'] for comp, data in components.items()}

        # Identify components needing attention
        critical_components = [comp for comp, data in components.items() if data['health_score'] < 0.5]

        return {
            'component_analysis': components,
            'overall_health_score': statistics.mean(self.component_health.values()) if self.component_health else 1.0,
            'critical_components': critical_components,
            'maintenance_recommendations': self._generate_maintenance_recommendations(components)
        }

    def _analyze_cpu_health(self) -> Dict[str, Any]:
        """Analyze CPU health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()

            health_score = max(0, 1 - (cpu_percent / 100))

            # CPU frequency analysis
            freq_ratio = cpu_freq.current / cpu_freq.max if cpu_freq.max > 0 else 1

            return {
                'health_score': health_score,
                'current_usage': cpu_percent,
                'frequency_ratio': freq_ratio,
                'temperature': getattr(psutil, 'sensors_temperatures', lambda: {})().get('cpu_thermal', [{}])[0].get('current', 0) if hasattr(psutil, 'sensors_temperatures') else 0,
                'status': 'good' if health_score > 0.7 else 'warning' if health_score > 0.4 else 'critical'
            }
        except Exception as e:
            logger.warning(f"CPU health analysis failed: {str(e)}")
            return {'health_score': 0.5, 'status': 'unknown', 'error': str(e)}

    def _analyze_memory_health(self) -> Dict[str, Any]:
        """Analyze memory health"""
        try:
            memory = psutil.virtual_memory()

            health_score = 1 - (memory.percent / 100)

            return {
                'health_score': health_score,
                'used_percent': memory.percent,
                'available_gb': memory.available / (1024**3),
                'swap_used_percent': psutil.swap_memory().percent,
                'status': 'good' if health_score > 0.7 else 'warning' if health_score > 0.4 else 'critical'
            }
        except Exception as e:
            logger.warning(f"Memory health analysis failed: {str(e)}")
            return {'health_score': 0.5, 'status': 'unknown', 'error': str(e)}

    def _analyze_disk_health(self) -> Dict[str, Any]:
        """Analyze disk health"""
        try:
            disk = psutil.disk_usage('/')

            health_score = 1 - (disk.percent / 100)

            return {
                'health_score': health_score,
                'used_percent': disk.percent,
                'free_gb': disk.free / (1024**3),
                'total_gb': disk.total / (1024**3),
                'status': 'good' if health_score > 0.7 else 'warning' if health_score > 0.4 else 'critical'
            }
        except Exception as e:
            logger.warning(f"Disk health analysis failed: {str(e)}")
            return {'health_score': 0.5, 'status': 'unknown', 'error': str(e)}

    def _analyze_network_health(self) -> Dict[str, Any]:
        """Analyze network health"""
        try:
            network = psutil.net_io_counters()

            # Simple network health based on error rates (would need more sophisticated analysis)
            health_score = 0.8  # Placeholder

            return {
                'health_score': health_score,
                'bytes_sent_mb': network.bytes_sent / (1024**2),
                'bytes_recv_mb': network.bytes_recv / (1024**2),
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv,
                'status': 'good' if health_score > 0.7 else 'warning' if health_score > 0.4 else 'critical'
            }
        except Exception as e:
            logger.warning(f"Network health analysis failed: {str(e)}")
            return {'health_score': 0.5, 'status': 'unknown', 'error': str(e)}

    def _analyze_database_health(self) -> Dict[str, Any]:
        """Analyze database health"""
        try:
            # Simple database health check
            with db.session.begin():
                # Test basic query
                result = db.session.execute(db.text("SELECT 1")).scalar()
                connection_healthy = result == 1

                # Get table counts
                agent_count = db.session.query(Agent).count()
                task_count = db.session.query(Task).count()

            health_score = 1.0 if connection_healthy else 0.0

            return {
                'health_score': health_score,
                'connection_healthy': connection_healthy,
                'total_records': agent_count + task_count,
                'status': 'good' if health_score > 0.7 else 'critical'
            }
        except Exception as e:
            logger.warning(f"Database health analysis failed: {str(e)}")
            return {'health_score': 0.0, 'status': 'critical', 'error': str(e)}

    def _generate_maintenance_recommendations(self, components: Dict[str, Any]) -> List[str]:
        """Generate maintenance recommendations"""
        recommendations = []

        for component, analysis in components.items():
            health_score = analysis.get('health_score', 1.0)
            status = analysis.get('status', 'unknown')

            if status == 'critical':
                recommendations.append(f"URGENT: {component.upper()} requires immediate attention - health score: {health_score:.2f}")
            elif status == 'warning':
                recommendations.append(f"MONITOR: {component.upper()} showing signs of stress - health score: {health_score:.2f}")
            elif health_score < 0.8:
                recommendations.append(f"MAINTENANCE: Schedule maintenance for {component.upper()} - health score: {health_score:.2f}")

        if not recommendations:
            recommendations.append("All system components are operating within normal parameters.")

        return recommendations

    def predict_failures(self) -> List[Dict[str, Any]]:
        """Predict potential component failures"""
        predictions = []

        # Simple failure prediction based on health trends
        for component, health_score in self.component_health.items():
            if health_score < 0.3:
                predictions.append({
                    'component': component,
                    'failure_probability': 'high',
                    'timeframe': 'within_days',
                    'recommendation': f'Immediate maintenance required for {component}'
                })
            elif health_score < 0.6:
                predictions.append({
                    'component': component,
                    'failure_probability': 'medium',
                    'timeframe': 'within_weeks',
                    'recommendation': f'Schedule maintenance for {component} soon'
                })

        return predictions

# Global instances
realtime_dashboard = RealTimeDashboard()
analytics_engine = AdvancedAnalyticsEngine()
predictive_maintenance = PredictiveMaintenance()

def create_dashboard_html() -> str:
    """Create HTML dashboard"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CHATTY Observability Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric { display: flex; justify-content: space-between; margin: 10px 0; }
            .metric-name { font-weight: bold; }
            .metric-value { color: #007bff; }
            .status-good { color: #28a745; }
            .status-warning { color: #ffc107; }
            .status-critical { color: #dc3545; }
            .chart { width: 100%; height: 300px; }
            h1 { color: #333; text-align: center; }
            h2 { color: #555; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        </style>
    </head>
    <body>
        <h1>🚀 CHATTY Observability Dashboard</h1>

        <div class="dashboard">
            <div class="card">
                <h2>System Metrics</h2>
                <div id="system-metrics"></div>
            </div>

            <div class="card">
                <h2>Application Metrics</h2>
                <div id="app-metrics"></div>
            </div>

            <div class="card">
                <h2>Business Metrics</h2>
                <div id="business-metrics"></div>
            </div>

            <div class="card">
                <h2>Performance Charts</h2>
                <div id="performance-charts" class="chart"></div>
            </div>

            <div class="card">
                <h2>Component Health</h2>
                <div id="component-health"></div>
            </div>

            <div class="card">
                <h2>Recent Alerts</h2>
                <div id="alerts"></div>
            </div>
        </div>

        <script>
            async function updateDashboard() {
                try {
                    const response = await fetch('/api/observability/dashboard');
                    const data = await response.json();

                    updateSystemMetrics(data.system || {});
                    updateAppMetrics(data.application || {});
                    updateBusinessMetrics(data.business || {});
                    updatePerformanceCharts(data);
                    updateComponentHealth(data);
                    updateAlerts(data.alerts || []);
                } catch (error) {
                    console.error('Dashboard update failed:', error);
                }
            }

            function updateSystemMetrics(metrics) {
                const container = document.getElementById('system-metrics');
                container.innerHTML = '';

                Object.entries(metrics).forEach(([key, value]) => {
                    if (typeof value === 'number') {
                        const div = document.createElement('div');
                        div.className = 'metric';
                        div.innerHTML = `
                            <span class="metric-name">${key.replace(/_/g, ' ').toUpperCase()}</span>
                            <span class="metric-value">${value.toFixed(2)}</span>
                        `;
                        container.appendChild(div);
                    }
                });
            }

            function updateAppMetrics(metrics) {
                const container = document.getElementById('app-metrics');
                container.innerHTML = '';

                Object.entries(metrics).forEach(([key, value]) => {
                    const div = document.createElement('div');
                    div.className = 'metric';
                    div.innerHTML = `
                        <span class="metric-name">${key.replace(/_/g, ' ').toUpperCase()}</span>
                        <span class="metric-value">${typeof value === 'number' ? value.toFixed(2) : value}</span>
                    `;
                    container.appendChild(div);
                });
            }

            function updateBusinessMetrics(metrics) {
                const container = document.getElementById('business-metrics');
                container.innerHTML = '';

                Object.entries(metrics).forEach(([key, value]) => {
                    const div = document.createElement('div');
                    div.className = 'metric';
                    div.innerHTML = `
                        <span class="metric-name">${key.replace(/_/g, ' ').toUpperCase()}</span>
                        <span class="metric-value">${typeof value === 'number' ? value.toFixed(2) : JSON.stringify(value)}</span>
                    `;
                    container.appendChild(div);
                });
            }

            function updatePerformanceCharts(data) {
                const charts = data.charts || {};
                const container = document.getElementById('performance-charts');

                if (charts.cpu_usage) {
                    const trace = {
                        x: charts.cpu_usage.x,
                        y: charts.cpu_usage.y,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'CPU Usage',
                        line: {color: charts.cpu_usage.color}
                    };

                    Plotly.newPlot(container, [trace], {
                        title: charts.cpu_usage.title,
                        xaxis: {title: 'Time'},
                        yaxis: {title: 'CPU %'}
                    });
                }
            }

            function updateComponentHealth(data) {
                const container = document.getElementById('component-health');
                const health = data.component_health || {};

                container.innerHTML = '';

                Object.entries(health).forEach(([component, data]) => {
                    const div = document.createElement('div');
                    div.className = 'metric';

                    const statusClass = data.status === 'good' ? 'status-good' :
                                      data.status === 'warning' ? 'status-warning' : 'status-critical';

                    div.innerHTML = `
                        <span class="metric-name">${component.toUpperCase()}</span>
                        <span class="metric-value ${statusClass}">${data.status} (${(data.health_score * 100).toFixed(1)}%)</span>
                    `;
                    container.appendChild(div);
                });
            }

            function updateAlerts(alerts) {
                const container = document.getElementById('alerts');
                container.innerHTML = '';

                alerts.forEach(alert => {
                    const div = document.createElement('div');
                    div.className = 'metric';

                    const statusClass = alert.severity === 'low' ? 'status-good' :
                                      alert.severity === 'medium' ? 'status-warning' : 'status-critical';

                    div.innerHTML = `
                        <span class="metric-name ${statusClass}">${alert.type.toUpperCase()}</span>
                        <span class="metric-value">${alert.message}</span>
                    `;
                    container.appendChild(div);
                });
            }

            // Update dashboard every 5 seconds
            updateDashboard();
            setInterval(updateDashboard, 5000);
        </script>
    </body>
    </html>
    """
    return html_template
