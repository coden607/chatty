#!/usr/bin/env python3
"""
CHATTY Autonomous Agent System - Enhanced Backend API Server
Robust, scalable backend with comprehensive error handling, logging, and agent management
"""

import os
import time
import json
import uuid
import logging
import structlog
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from flask import Flask, request, jsonify, g, current_app, Response
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity,
    create_access_token, create_refresh_token
)
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, ValidationError, validate
import redis
import requests
from dotenv import load_dotenv

# Load environment variables (allow external secrets file)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE", ".env")
load_dotenv(_secrets_file)

# Configure structured logging
logging.basicConfig(level=logging.INFO)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(32).hex()),
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex()),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'postgresql://chatty:password@localhost:5432/chatty'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_pre_ping': True,
        'pool_recycle': 300,
    },
    REDIS_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    OLLAMA_BASE_URL=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
    N8N_WEBHOOK_URL=os.environ.get('N8N_WEBHOOK_URL', 'http://localhost:5678'),
)

# Initialize extensions
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8000", "https://localhost:8000", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

jwt = JWTManager(app)
db = SQLAlchemy(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Redis connection
redis_client = redis.Redis.from_url(app.config['REDIS_URL'])

# Import agents after app initialization
from youtube_agent import register_youtube_routes
from learning_system import memory_system, adaptive_learning
from agent_factory import agent_factory
from code_executor import code_executor
from performance_optimizer import performance_monitor, cache_manager, async_manager
from advanced_ai import reinforcement_learner, multi_modal_ai, collaboration_system
from security_enhancer import zero_trust_security, compliance_manager, data_encryption
from observability_engine import realtime_dashboard, analytics_engine, predictive_maintenance, create_dashboard_html
from cole_scraper_agent import cole_scraper

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    agents = db.relationship('Agent', backref='owner', lazy=True)
    tasks = db.relationship('Task', backref='creator', lazy=True)

class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='inactive')
    autonomy_level = db.Column(db.String(20), default='supervised')
    capabilities = db.Column(db.JSON, default=list)
    tools = db.Column(db.JSON, default=list)
    config = db.Column(db.JSON, default=dict)
    memory = db.Column(db.JSON, default=dict)
    performance_metrics = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Relationships
    tasks = db.relationship('Task', backref='assigned_agent', lazy=True)
    executions = db.relationship('Execution', backref='agent', lazy=True)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(10), default='medium')
    task_type = db.Column(db.String(50))
    parameters = db.Column(db.JSON, default=dict)
    result = db.Column(db.JSON, default=dict)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    agent_id = db.Column(db.String(36), db.ForeignKey('agents.id'))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

class Execution(db.Model):
    __tablename__ = 'executions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    agent_id = db.Column(db.String(36), db.ForeignKey('agents.id'), nullable=False)
    status = db.Column(db.String(20), default='running')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration = db.Column(db.Float)
    logs = db.Column(db.JSON, default=list)
    metrics = db.Column(db.JSON, default=dict)

# Validation Schemas
class UserSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(dump_only=True)

class AgentSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    autonomy_level = fields.Str(validate=validate.OneOf(['supervised', 'semi_autonomous', 'autonomous']), missing='supervised')
    capabilities = fields.List(fields.Str(), missing=[])
    tools = fields.List(fields.Str(), missing=[])
    config = fields.Dict(missing={})

class TaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str()
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high', 'critical']), missing='medium')
    task_type = fields.Str()
    parameters = fields.Dict(missing={})
    agent_id = fields.Str()

# Error Handling
class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400, payload: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

@app.errorhandler(APIError)
def handle_api_error(error):
    logger.error("API Error", error=str(error), status_code=error.status_code)
    response = {
        'error': error.message,
        'status_code': error.status_code,
        'timestamp': datetime.utcnow().isoformat()
    }
    if error.payload:
        response.update(error.payload)
    return jsonify(response), error.status_code

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    logger.warning("Validation Error", errors=error.messages)
    return jsonify({
        'error': 'Validation failed',
        'details': error.messages,
        'timestamp': datetime.utcnow().isoformat()
    }), 400

@app.errorhandler(HTTPException)
def handle_http_error(error):
    logger.error("HTTP Error", code=error.code, description=error.description)
    return jsonify({
        'error': error.description,
        'status_code': error.code,
        'timestamp': datetime.utcnow().isoformat()
    }), error.code

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.error("Unexpected Error", error=str(error), traceback=True)
    return jsonify({
        'error': 'Internal server error',
        'status_code': 500,
        'timestamp': datetime.utcnow().isoformat()
    }), 500

# Middleware
@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    logger.info("Request started", method=request.method, path=request.path, request_id=g.request_id)

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    logger.info(
        "Request completed",
        method=request.method,
        path=request.path,
        status=response.status_code,
        duration=duration,
        request_id=g.request_id
    )
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Response-Time'] = f"{duration:.3f}s"
    return response

# Database connection management
@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    try:
        yield db.session
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error", error=str(e))
        raise APIError("Database operation failed", 500)
    finally:
        db.session.close()

# Authentication helpers
def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        with db_session() as session:
            user = session.query(User).get(user_id)
            if not user or user.role != 'admin':
                raise APIError("Admin access required", 403)
        return f(*args, **kwargs)
    return decorated_function

# Health check endpoint
@app.route('/health', methods=['GET'])
@limiter.limit("30 per minute")
def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'services': {}
    }

    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = 'unhealthy'
        health_status['status'] = 'degraded'
        logger.error("Database health check failed", error=str(e))

    # Check Redis
    try:
        redis_client.ping()
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = 'unhealthy'
        health_status['status'] = 'degraded'
        logger.error("Redis health check failed", error=str(e))

    # Check external services
    services_to_check = [
        ('ollama', app.config['OLLAMA_BASE_URL']),
        ('n8n', app.config['N8N_WEBHOOK_URL'])
    ]

    for service_name, service_url in services_to_check:
        try:
            response = requests.get(service_url, timeout=5)
            health_status['services'][service_name] = 'healthy' if response.status_code < 500 else 'degraded'
        except Exception as e:
            health_status['services'][service_name] = 'unhealthy'
            logger.warning(f"{service_name} health check failed", error=str(e))

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """Register a new user"""
    try:
        schema = UserSchema()
        data = schema.load(request.get_json())

        with db_session() as session:
            # Check if user already exists
            if session.query(User).filter_by(email=data['email']).first():
                raise APIError("Email already registered", 409)
            if session.query(User).filter_by(username=data['username']).first():
                raise APIError("Username already taken", 409)

            # Create user
            user = User(
                username=data['username'],
                email=data['email'],
                password_hash=bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode(),
                role='user'  # Strictly enforce 'user' role for self-registration
            )
            session.add(user)

            logger.info("User registered", user_id=user.id, username=user.username)
            return jsonify({
                'message': 'User registered successfully',
                'user_id': user.id
            }), 201

    except ValidationError as e:
        raise APIError("Invalid registration data", 400, {'validation_errors': e.messages})

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            raise APIError("Username and password required", 400)

        with db_session() as session:
            user = session.query(User).filter_by(username=data['username']).first()
            if not user or not bcrypt.checkpw(data['password'].encode(), user.password_hash.encode()):
                raise APIError("Invalid credentials", 401)

            if not user.is_active:
                raise APIError("Account is disabled", 401)

            # Update last login
            user.last_login = datetime.utcnow()
            session.commit()

            # Create tokens
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            logger.info("User logged in", user_id=user.id, username=user.username)
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }), 200

    except ValidationError as e:
        raise APIError("Invalid login data", 400)

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token}), 200

# Agent management endpoints
@app.route('/api/agents', methods=['GET'])
@jwt_required()
def list_agents():
    """List user's agents"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    with db_session() as session:
        query = session.query(Agent).filter_by(user_id=user_id)
        total = query.count()
        agents = query.offset((page-1)*per_page).limit(per_page).all()

        return jsonify({
            'agents': [{
                'id': agent.id,
                'name': agent.name,
                'description': agent.description,
                'status': agent.status,
                'autonomy_level': agent.autonomy_level,
                'capabilities': agent.capabilities,
                'created_at': agent.created_at.isoformat()
            } for agent in agents],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200

@app.route('/api/agents', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_agent():
    """Create a new agent from natural language description with advanced capabilities"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or not data.get('description'):
            raise APIError("Agent description required", 400)

        # Get specialization if provided
        specialization = data.get('specialization')

        # Use advanced agent factory to parse requirements
        agent_config = parse_agent_description(data['description'], user_id, specialization)

        # Validate the configuration
        if not agent_config.get('validation', {}).get('valid', True):
            logger.warning("Agent configuration validation failed",
                         issues=agent_config.get('validation', {}).get('issues', []))

        schema = AgentSchema()
        validated_data = schema.load({
            'name': agent_config.get('name', f"Agent {uuid.uuid4().hex[:8]}"),
            'description': data['description'],
            'capabilities': agent_config.get('capabilities', []),
            'tools': agent_config.get('tools', []),
            'config': agent_config.get('config', {}),
            'autonomy_level': agent_config.get('autonomy_level', 'supervised')
        })

        with db_session() as session:
            agent = Agent(
                name=validated_data['name'],
                description=validated_data['description'],
                capabilities=validated_data['capabilities'],
                tools=validated_data['tools'],
                config=validated_data['config'],
                autonomy_level=validated_data.get('autonomy_level', 'supervised'),
                user_id=user_id
            )
            session.add(agent)

            # Create initial task for agent setup
            setup_task = Task(
                title=f"Initialize agent: {agent.name}",
                description=f"Set up agent with capabilities: {', '.join(agent.capabilities)}",
                task_type="agent_setup",
                agent_id=agent.id,
                user_id=user_id
            )
            session.add(setup_task)

            # Create tool installation tasks if needed
            tool_tasks = []
            for tool in agent.tools:
                if tool in tool_downloader.tool_database:
                    tool_task = Task(
                        title=f"Install tool: {tool}",
                        description=f"Install and configure {tool} for agent {agent.name}",
                        task_type="tool_installation",
                        parameters={'tool': tool},
                        agent_id=agent.id,
                        user_id=user_id
                    )
                    session.add(tool_task)
                    tool_tasks.append(tool_task.id)

            logger.info("Agent created with advanced configuration",
                       agent_id=agent.id,
                       user_id=user_id,
                       capabilities=agent.capabilities,
                       tools=agent.tools,
                       autonomy_level=agent.autonomy_level)

            response_data = {
                'agent': {
                    'id': agent.id,
                    'name': agent.name,
                    'description': agent.description,
                    'capabilities': agent.capabilities,
                    'tools': agent.tools,
                    'autonomy_level': agent.autonomy_level,
                    'status': agent.status,
                    'metadata': agent_config.get('metadata', {})
                },
                'setup_task_id': setup_task.id,
                'tool_installation_tasks': tool_tasks,
                'validation': agent_config.get('validation', {})
            }

            return jsonify(response_data), 201

    except ValidationError as e:
        raise APIError("Invalid agent data", 400, {'validation_errors': e.messages})

@app.route('/api/agents/<agent_id>', methods=['GET'])
@jwt_required()
def get_agent(agent_id):
    """Get agent details"""
    user_id = get_jwt_identity()

    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found", 404)

        return jsonify({
            'id': agent.id,
            'name': agent.name,
            'description': agent.description,
            'status': agent.status,
            'autonomy_level': agent.autonomy_level,
            'capabilities': agent.capabilities,
            'tools': agent.tools,
            'config': agent.config,
            'memory': agent.memory,
            'performance_metrics': agent.performance_metrics,
            'created_at': agent.created_at.isoformat(),
            'updated_at': agent.updated_at.isoformat()
        }), 200

@app.route('/api/agents/<agent_id>', methods=['PUT'])
@jwt_required()
def update_agent(agent_id):
    """Update agent configuration"""
    user_id = get_jwt_identity()

    try:
        schema = AgentSchema(partial=True)
        data = schema.load(request.get_json())

        with db_session() as session:
            agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
            if not agent:
                raise APIError("Agent not found", 404)

            # Update agent fields
            for field in ['name', 'description', 'autonomy_level', 'capabilities', 'tools', 'config']:
                if field in data:
                    setattr(agent, field, data[field])

            logger.info("Agent updated", agent_id=agent.id, updated_fields=list(data.keys()))
            return jsonify({
                'message': 'Agent updated successfully',
                'agent': {
                    'id': agent.id,
                    'name': agent.name,
                    'capabilities': agent.capabilities,
                    'tools': agent.tools
                }
            }), 200

    except ValidationError as e:
        raise APIError("Invalid update data", 400, {'validation_errors': e.messages})

@app.route('/api/agents/<agent_id>', methods=['DELETE'])
@jwt_required()
def delete_agent(agent_id):
    """Delete an agent"""
    user_id = get_jwt_identity()

    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found", 404)

        # Check if agent has active tasks
        active_tasks = session.query(Task).filter_by(
            agent_id=agent_id,
            status='in_progress'
        ).count()

        if active_tasks > 0:
            raise APIError("Cannot delete agent with active tasks", 409)

        session.delete(agent)
        logger.info("Agent deleted", agent_id=agent_id, user_id=user_id)
        return jsonify({'message': 'Agent deleted successfully'}), 200

# Learning system endpoints
@app.route('/api/learning/experience', methods=['POST'])
@jwt_required()
def store_experience():
    """Store an agent learning experience"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('agent_id') or not data.get('experience'):
        raise APIError("Agent ID and experience data required", 400)

    agent_id = data['agent_id']

    # Verify agent ownership
    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found or access denied", 404)

    # Store experience
    experience_id = memory_system.store_experience(agent_id, data['experience'])

    return jsonify({
        'experience_id': experience_id,
        'message': 'Experience stored successfully'
    }), 201

@app.route('/api/learning/memories/<agent_id>', methods=['GET'])
@jwt_required()
def get_memories(agent_id):
    """Retrieve relevant memories for an agent"""
    user_id = get_jwt_identity()
    query = request.args.get('query', '')
    limit = request.args.get('limit', 10, type=int)

    # Verify agent ownership
    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found or access denied", 404)

    if not query:
        raise APIError("Query parameter required", 400)

    memories = memory_system.retrieve_relevant_memories(agent_id, query, limit)

    return jsonify({
        'memories': memories,
        'count': len(memories)
    }), 200

@app.route('/api/learning/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit feedback on an agent experience"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('agent_id') or not data.get('experience_id') or 'feedback' not in data:
        raise APIError("Agent ID, experience ID, and feedback required", 400)

    agent_id = data['agent_id']
    experience_id = data['experience_id']

    # Verify agent ownership
    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found or access denied", 404)

    # Process feedback
    memory_system.learn_from_feedback(agent_id, experience_id, data['feedback'])

    return jsonify({'message': 'Feedback processed successfully'}), 200

@app.route('/api/learning/predict/<agent_id>', methods=['POST'])
@jwt_required()
def predict_success(agent_id):
    """Predict success probability for a task"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('task_description'):
        raise APIError("Task description required", 400)

    # Verify agent ownership
    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found or access denied", 404)

    probability = memory_system.predict_success_probability(agent_id, data['task_description'])

    return jsonify({
        'agent_id': agent_id,
        'task_description': data['task_description'],
        'success_probability': probability,
        'confidence_level': 'medium' if 0.3 <= probability <= 0.7 else 'high'
    }), 200

@app.route('/api/learning/recommendations/<agent_id>', methods=['GET'])
@jwt_required()
def get_learning_recommendations(agent_id):
    """Get learning recommendations for an agent"""
    user_id = get_jwt_identity()

    # Verify agent ownership
    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found or access denied", 404)

    recommendations = adaptive_learning.generate_learning_recommendations(agent_id)

    return jsonify({
        'agent_id': agent_id,
        'recommendations': recommendations,
        'count': len(recommendations)
    }), 200

@app.route('/api/learning/consolidate/<agent_id>', methods=['POST'])
@jwt_required()
def consolidate_knowledge(agent_id):
    """Manually trigger knowledge consolidation for an agent"""
    user_id = get_jwt_identity()

    # Verify agent ownership
    with db_session() as session:
        agent = session.query(Agent).filter_by(id=agent_id, user_id=user_id).first()
        if not agent:
            raise APIError("Agent not found or access denied", 404)

    result = memory_system.consolidate_knowledge(agent_id)

    return jsonify({
        'agent_id': agent_id,
        'consolidation_result': result,
        'message': f'Consolidated {result["consolidated"]} knowledge patterns'
    }), 200

# Task management endpoints
@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def list_tasks():
    """List user's tasks"""
    user_id = get_jwt_identity()
    status = request.args.get('status')
    agent_id = request.args.get('agent_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    with db_session() as session:
        query = session.query(Task).filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)
        if agent_id:
            query = query.filter_by(agent_id=agent_id)

        total = query.count()
        tasks = query.order_by(Task.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

        return jsonify({
            'tasks': [{
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'task_type': task.task_type,
                'agent_id': task.agent_id,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            } for task in tasks],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200

@app.route('/api/tasks', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_task():
    """Create a new task with intelligent agent assignment"""
    try:
        user_id = get_jwt_identity()
        schema = TaskSchema()
        data = schema.load(request.get_json())

        with db_session() as session:
            # Intelligent agent assignment if not specified
            agent_id = data.get('agent_id')
            if not agent_id:
                # Find best agent for this task
                available_agents = [
                    agent.id for agent in session.query(Agent).filter_by(user_id=user_id, status='active').all()
                ]
                if available_agents:
                    task_description = f"{data['title']} {data.get('description', '')}"
                    agent_id = adaptive_learning.optimize_task_assignment(
                        {'task_type': data.get('task_type', 'general'), 'description': task_description},
                        available_agents
                    )

            task = Task(
                title=data['title'],
                description=data['description'],
                priority=data['priority'],
                task_type=data.get('task_type'),
                parameters=data.get('parameters', {}),
                agent_id=agent_id,
                user_id=user_id
            )
            session.add(task)

            # Predict success probability
            success_probability = 0.5
            if agent_id:
                task_description = f"{task.title} {task.description or ''}"
                success_probability = memory_system.predict_success_probability(agent_id, task_description)

            # If agent is specified and autonomous, trigger execution
            if task.agent_id:
                agent = session.query(Agent).get(task.agent_id)
                if agent and agent.autonomy_level in ['semi_autonomous', 'autonomous']:
                    # Queue task for execution
                    queue_task_for_execution(task.id)

            logger.info("Task created", task_id=task.id, user_id=user_id, agent_id=task.agent_id, predicted_success=success_probability)
            return jsonify({
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'agent_id': task.agent_id,
                    'predicted_success_probability': success_probability
                }
            }), 201

    except ValidationError as e:
        raise APIError("Invalid task data", 400, {'validation_errors': e.messages})

# Command endpoint (legacy compatibility)
@app.route('/api/command', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def api_command():
    """Process natural language commands"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or not data.get('command'):
            raise APIError("Command required", 400)

        command = data['command']

        # Route command to appropriate agent or create new task
        result = process_natural_language_command(user_id, command)

        return jsonify(result), 200

    except Exception as e:
        logger.error("Command processing failed", error=str(e), command=data.get('command'))
        raise APIError("Command processing failed", 500)

# Utility functions
def parse_agent_description(description: str, user_id: str = None, specialization: str = None) -> Dict[str, Any]:
    """Parse natural language agent description using advanced agent factory"""
    try:
        # Use the advanced agent factory
        agent_config = agent_factory.create_agent_from_description(description, user_id, specialization)

        # Extract the core components needed by the create_agent endpoint
        return {
            'name': agent_config.get('name', f"Agent-{uuid.uuid4().hex[:8]}"),
            'capabilities': agent_config.get('capabilities', ['general_assistance']),
            'tools': agent_config.get('tools', []),
            'config': agent_config.get('config', {'description': description}),
            'autonomy_level': agent_config.get('autonomy_level', 'supervised'),
            'metadata': agent_config.get('metadata', {}),
            'validation': agent_config.get('validation', {'valid': True})
        }

    except Exception as e:
        logger.error("Advanced agent creation failed, using fallback", error=str(e))
        # Fallback to basic configuration
        return {
            'name': f"Agent-{uuid.uuid4().hex[:8]}",
            'capabilities': ['general_assistance'],
            'tools': [],
            'config': {'description': description},
            'autonomy_level': 'supervised',
            'metadata': {'fallback': True},
            'validation': {'valid': True, 'issues': [], 'warnings': ['Fallback configuration used']}
        }

def process_natural_language_command(user_id: str, command: str) -> Dict[str, Any]:
    """Process natural language commands"""
    # This is a simplified implementation
    # In production, this would use advanced NLP and routing

    command_lower = command.lower()

    if 'call' in command_lower or 'dial' in command_lower:
        return {
            'status': 'ok',
            'action': 'call',
            'message': 'Would initiate call via Wazo PBX',
            'command': command
        }
    elif 'weather' in command_lower:
        return {
            'status': 'ok',
            'action': 'weather',
            'message': 'Fetching weather information',
            'command': command
        }
    elif 'create agent' in command_lower or 'build agent' in command_lower:
        return {
            'status': 'ok',
            'action': 'create_agent',
            'message': 'Agent creation request queued',
            'command': command
        }
    else:
        return {
            'status': 'ok',
            'action': 'general',
            'message': f'Processing command: {command}',
            'command': command
        }

def queue_task_for_execution(task_id: str):
    """Queue task for background execution"""
    try:
        redis_client.lpush('chatty:task_queue', task_id)
        logger.info("Task queued for execution", task_id=task_id)
    except Exception as e:
        logger.error("Failed to queue task", task_id=task_id, error=str(e))

# Enhanced Tool Management Endpoints
@app.route('/api/tools/discover', methods=['POST'])
@jwt_required()
def discover_tools_enhanced():
    """Enhanced tool discovery with intelligent matching"""
    data = request.get_json()
    content_analysis = data.get('analysis', {})

    if not content_analysis:
        raise APIError("Content analysis required", 400)

    discovered_tools = tool_downloader.discover_tools(content_analysis)

    return jsonify({
        'discovered_tools': discovered_tools,
        'total_found': len(discovered_tools),
        'known_tools': len([t for t in discovered_tools if t['type'] == 'known']),
        'unknown_tools': len([t for t in discovered_tools if t['type'] == 'unknown']),
        'inferred_tools': len([t for t in discovered_tools if t['type'] == 'inferred']),
        'status': 'success'
    })

@app.route('/api/tools/install', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def install_tool_enhanced():
    """Enhanced tool installation with dependency resolution"""
    data = request.get_json()
    tool_name = data.get('tool')
    force = data.get('force', False)

    if not tool_name:
        raise APIError("Tool name required", 400)

    result = tool_downloader.download_and_install(tool_name, force)

    return jsonify(result)

@app.route('/api/tools/install/toolchain', methods=['POST'])
@jwt_required()
@limiter.limit("2 per hour")
def install_toolchain():
    """Install a complete toolchain with dependency resolution"""
    data = request.get_json()
    tools = data.get('tools', [])
    force = data.get('force', False)

    if not tools:
        raise APIError("Tools list required", 400)

    result = tool_downloader.install_toolchain(tools, force)

    return jsonify(result)

@app.route('/api/tools/verify', methods=['POST'])
@jwt_required()
def verify_tool_installation():
    """Verify tool installation status"""
    data = request.get_json()
    tool_name = data.get('tool')

    if not tool_name:
        raise APIError("Tool name required", 400)

    if tool_name not in tool_downloader.tool_database:
        return jsonify({
            'tool': tool_name,
            'installed': False,
            'error': 'Unknown tool'
        })

    tool_info = tool_downloader.tool_database[tool_name]
    installed = tool_downloader._is_tool_installed(tool_info)

    return jsonify({
        'tool': tool_name,
        'installed': installed,
        'description': tool_info.get('description', ''),
        'category': tool_info.get('category', ''),
        'verification_command': tool_info.get('verify_command', '')
    })

@app.route('/api/tools/available', methods=['GET'])
@jwt_required()
def list_available_tools():
    """List all available tools in the database"""
    category = request.args.get('category')
    search = request.args.get('search')

    tools = []
    for tool_name, tool_info in tool_downloader.tool_database.items():
        if category and tool_info.get('category') != category:
            continue
        if search and search.lower() not in tool_name.lower() and search.lower() not in tool_info.get('description', '').lower():
            continue

        tools.append({
            'name': tool_name,
            'description': tool_info.get('description', ''),
            'category': tool_info.get('category', ''),
            'manager': tool_info.get('manager', ''),
            'dependencies': tool_info.get('dependencies', [])
        })

    # Group by category
    categories = {}
    for tool in tools:
        cat = tool['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    return jsonify({
        'tools': tools,
        'categories': categories,
        'total': len(tools),
        'status': 'success'
    })

@app.route('/api/tools/categories', methods=['GET'])
@jwt_required()
def get_tool_categories():
    """Get available tool categories"""
    categories = set()
    for tool_info in tool_downloader.tool_database.values():
        categories.add(tool_info.get('category', 'other'))

    return jsonify({
        'categories': sorted(list(categories)),
        'status': 'success'
    })

# Advanced Agent Creation Endpoints
@app.route('/api/agents/analyze', methods=['POST'])
@jwt_required()
def analyze_agent_description():
    """Analyze an agent description without creating the agent"""
    data = request.get_json()

    if not data or not data.get('description'):
        raise APIError("Agent description required", 400)

    user_id = get_jwt_identity()
    specialization = data.get('specialization')

    # Analyze the description
    analysis = agent_factory.analyzer.analyze_description(data['description'])

    # Apply specialization if requested
    if specialization:
        analysis = agent_factory.specializer.specialize_agent(analysis, specialization)

    # Add tool discovery
    required_tools = agent_factory._discover_required_tools(analysis)
    analysis['discovered_tools'] = required_tools

    return jsonify({
        'analysis': analysis,
        'description': data['description'],
        'specialization': specialization,
        'status': 'success'
    })

@app.route('/api/agents/specializations', methods=['GET'])
@jwt_required()
def get_agent_specializations():
    """Get available agent specializations"""
    specializations = {
        'customer_support': {
            'name': 'Customer Support',
            'description': 'Handles customer inquiries, issue resolution, and support tickets',
            'capabilities': ['customer_interaction', 'issue_resolution', 'knowledge_base_access']
        },
        'content_moderation': {
            'name': 'Content Moderation',
            'description': 'Analyzes and moderates content according to policies',
            'capabilities': ['content_analysis', 'policy_enforcement', 'risk_assessment']
        },
        'data_pipeline': {
            'name': 'Data Pipeline',
            'description': 'Manages data ingestion, processing, and validation',
            'capabilities': ['data_ingestion', 'transformation', 'validation']
        },
        'research_assistant': {
            'name': 'Research Assistant',
            'description': 'Conducts research and gathers information',
            'capabilities': ['information_retrieval', 'source_verification', 'knowledge_synthesis']
        },
        'code_developer': {
            'name': 'Code Developer',
            'description': 'Assists with software development and coding tasks',
            'capabilities': ['code_generation', 'debugging', 'code_review']
        }
    }

    return jsonify({
        'specializations': specializations,
        'status': 'success'
    })

# Code Execution Endpoints
@app.route('/api/code/execute', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def execute_code():
    """Execute code in a secure sandboxed environment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or not data.get('code'):
            raise APIError("Code required", 400)

        code = data['code']
        language = data.get('language', 'python')
        agent_id = data.get('agent_id')
        execution_context = data.get('context', 'basic')
        input_data = data.get('input_data', {})

        # Verify agent ownership if specified
        if agent_id:
            with db_session() as session:
                agent = session.query(Agent).get(agent_id)
                if not agent or agent.user_id != user_id:
                    raise APIError("Agent not found or access denied", 404)

        # Execute code
        result = code_executor.execute_code(
            code=code,
            language=language,
            agent_id=agent_id or user_id,
            execution_context=execution_context,
            input_data=input_data
        )

        # Store execution in database for audit
        with db_session() as session:
            execution_record = Execution(
                task_id=None,  # Not tied to a specific task
                agent_id=agent_id,
                status='completed' if result.get('success') else 'failed',
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration=result.get('execution_time', 0),
                logs=[f"Code execution: {result.get('execution_id', 'unknown')}"],
                metrics={
                    'language': language,
                    'context': execution_context,
                    'success': result.get('success', False)
                }
            )
            session.add(execution_record)

        logger.info("Code executed",
                   execution_id=result.get('execution_id'),
                   agent_id=agent_id,
                   language=language,
                   success=result.get('success'))

        return jsonify(result), 200

    except Exception as e:
        logger.error("Code execution request failed", error=str(e))
        raise APIError("Code execution failed", 500)

@app.route('/api/code/validate', methods=['POST'])
@jwt_required()
def validate_code():
    """Validate code for safety without executing"""
    try:
        data = request.get_json()

        if not data or not data.get('code'):
            raise APIError("Code required", 400)

        code = data['code']
        language = data.get('language', 'python')
        context = data.get('context', 'basic')

        # Validate code
        validation_result = code_executor.validate_code_safety(code, language, context)

        return jsonify({
            'valid': validation_result['valid'],
            'errors': validation_result['errors'],
            'language': language,
            'context': context,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Code validation failed", error=str(e))
        raise APIError("Code validation failed", 500)

@app.route('/api/code/history', methods=['GET'])
@jwt_required()
def get_code_execution_history():
    """Get code execution history"""
    user_id = get_jwt_identity()
    agent_id = request.args.get('agent_id')
    limit = request.args.get('limit', 50, type=int)

    # Verify agent ownership if specified
    if agent_id:
        with db_session() as session:
            agent = session.query(Agent).get(agent_id)
            if not agent or agent.user_id != user_id:
                raise APIError("Agent not found or access denied", 404)

    # Get execution history
    history = code_executor.get_execution_history(agent_id, limit)

    return jsonify({
        'executions': history,
        'count': len(history),
        'status': 'success'
    }), 200

@app.route('/api/code/contexts', methods=['GET'])
@jwt_required()
def get_execution_contexts():
    """Get available execution contexts"""
    contexts = {
        'basic': {
            'name': 'Basic',
            'description': 'Basic Python execution with limited imports',
            'allowed_imports': ['os', 'sys', 'json', 'math', 'datetime', 'random'],
            'max_execution_time': 30,
            'max_memory': '100m'
        },
        'data_science': {
            'name': 'Data Science',
            'description': 'Data analysis and machine learning libraries',
            'allowed_imports': ['pandas', 'numpy', 'matplotlib', 'sklearn', 'scipy'],
            'max_execution_time': 300,
            'max_memory': '1g'
        },
        'web_development': {
            'name': 'Web Development',
            'description': 'Web development with Flask and HTTP libraries',
            'allowed_imports': ['flask', 'requests', 'json', 'os'],
            'max_execution_time': 60,
            'max_memory': '256m'
        },
        'system_administration': {
            'name': 'System Administration',
            'description': 'System administration and automation',
            'allowed_imports': ['subprocess', 'os', 'sys', 'shutil'],
            'max_execution_time': 120,
            'max_memory': '512m'
        }
    }

    return jsonify({
        'contexts': contexts,
        'supported_languages': ['python', 'javascript', 'bash', 'r'],
        'status': 'success'
    }), 200

# Cole Medin Scraper Endpoints
@app.route('/api/cole/scrape', methods=['POST'])
@jwt_required()
@admin_required
@limiter.limit("1 per day")
def scrape_cole_channel():
    """Initiate comprehensive Cole Medin channel scraping and learning"""
    try:
        logger.info("Starting Cole Medin channel scraping by admin user")

        # This is a long-running operation, so we'll start it asynchronously
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor(max_workers=1)

        # Submit the scraping task
        future = executor.submit(cole_scraper.scrape_entire_channel)

        # Create a task to track this operation
        user_id = get_jwt_identity()
        task = Task(
            title="Cole Medin Channel Analysis & System Upgrade",
            description="Comprehensive scraping and analysis of Cole Medin's YouTube channel for autonomous system improvement",
            task_type="cole_channel_scraping",
            status="in_progress",
            user_id=user_id,
            parameters={
                'channel_id': cole_scraper.channel_id,
                'operation': 'full_channel_analysis'
            }
        )

        with db.session.begin():
            db.session.add(task)

        # Store task ID for status checking
        scraping_task_id = task.id

        return jsonify({
            'message': 'Cole Medin channel scraping initiated',
            'task_id': scraping_task_id,
            'status': 'in_progress',
            'estimated_duration': '30-60 minutes',
            'note': 'This operation will analyze all videos, extract knowledge, and autonomously upgrade the system'
        }), 202

    except Exception as e:
        logger.error("Failed to initiate Cole channel scraping", error=str(e))
        raise APIError("Failed to initiate channel scraping", 500)

@app.route('/api/cole/status', methods=['GET'])
@jwt_required()
def get_scraping_status():
    """Get the current status of Cole Medin channel scraping"""
    try:
        progress = cole_scraper.scraping_progress

        # Get latest task status
        with db.session.begin():
            latest_task = db.session.query(Task).filter_by(
                task_type="cole_channel_scraping"
            ).order_by(Task.created_at.desc()).first()

        task_status = None
        if latest_task:
            task_status = {
                'id': latest_task.id,
                'status': latest_task.status,
                'created_at': latest_task.created_at.isoformat(),
                'completed_at': latest_task.completed_at.isoformat() if latest_task.completed_at else None
            }

        return jsonify({
            'scraping_active': progress['videos_processed'] < progress['videos_found'],
            'progress': progress,
            'latest_task': task_status,
            'knowledge_extracted': len(cole_scraper.extracted_knowledge) > 0,
            'upgrades_applied': progress['upgrades_applied']
        }), 200

    except Exception as e:
        logger.error("Failed to get scraping status", error=str(e))
        raise APIError("Failed to get scraping status", 500)

@app.route('/api/cole/knowledge', methods=['GET'])
@jwt_required()
def get_extracted_knowledge():
    """Get the knowledge extracted from Cole Medin's channel"""
    try:
        knowledge = cole_scraper.extracted_knowledge

        if not knowledge:
            return jsonify({
                'message': 'No knowledge extracted yet. Run scraping first.',
                'status': 'no_data'
            }), 404

        return jsonify({
            'knowledge': knowledge,
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Failed to get extracted knowledge", error=str(e))
        raise APIError("Failed to get extracted knowledge", 500)

@app.route('/api/cole/upgrade', methods=['POST'])
@jwt_required()
@admin_required
def trigger_system_upgrade():
    """Trigger autonomous system upgrade based on learned knowledge"""
    try:
        if not cole_scraper.upgrade_recommendations:
            return jsonify({
                'error': 'No upgrade recommendations available. Run channel scraping first.',
                'status': 'no_recommendations'
            }), 400

        # Execute upgrades
        upgrade_results = cole_scraper._execute_autonomous_upgrades(cole_scraper.upgrade_recommendations)

        return jsonify({
            'upgrade_results': upgrade_results,
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error("Failed to execute system upgrade", error=str(e))
        raise APIError("Failed to execute system upgrade", 500)

@app.route('/api/cole/create-specialized-agent', methods=['POST'])
@jwt_required()
@admin_required
def create_specialized_agent():
    """Create a specialized agent based on Cole Medin's teachings"""
    try:
        data = request.get_json()
        theme = data.get('theme')

        if not theme:
            return jsonify({
                'error': 'Theme parameter required',
                'available_themes': ['programming', 'web_development', 'data_science', 'artificial_intelligence']
            }), 400

        if not cole_scraper.extracted_knowledge:
            return jsonify({
                'error': 'No knowledge base available. Run channel scraping first.'
            }), 400

        # Create agent for theme
        agent_config = cole_scraper._create_agent_for_theme(theme, cole_scraper.extracted_knowledge)

        if not agent_config:
            return jsonify({
                'error': f'No suitable agent configuration found for theme: {theme}'
            }), 404

        # Use agent factory to create the full agent
        user_id = get_jwt_identity()
        full_config = agent_factory.create_agent_from_description(
            f"Create a specialized agent for {theme} based on Cole Medin's teachings",
            user_id,
            theme
        )

        # Override with Cole-specific config
        full_config.update(agent_config)

        # Create agent in database
        agent = Agent(
            name=full_config['name'],
            description=full_config.get('description', ''),
            capabilities=full_config.get('capabilities', []),
            tools=full_config.get('tools', []),
            config=full_config.get('config', {}),
            autonomy_level=full_config.get('autonomy_level', 'supervised'),
            user_id=user_id
        )

        with db.session.begin():
            db.session.add(agent)

        logger.info("Created Cole-inspired specialized agent", agent_name=full_config['name'], theme=theme)

        return jsonify({
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'capabilities': agent.capabilities,
                'tools': agent.tools,
                'theme': theme
            },
            'message': f'Specialized agent created for {theme} based on Cole Medin\'s teachings',
            'status': 'success'
        }), 201

    except Exception as e:
        logger.error("Failed to create specialized agent", error=str(e))
        raise APIError("Failed to create specialized agent", 500)

# Advanced AI Endpoints
@app.route('/api/ai/reinforcement/train', methods=['POST'])
@jwt_required()
@admin_required
def train_reinforcement_model():
    """Train reinforcement learning model"""
    try:
        data = request.get_json()
        episodes = data.get('episodes', 10)

        reinforcement_learner.train(episodes)

        return jsonify({
            'message': f'Reinforcement learning model trained for {episodes} episodes',
            'training_steps': reinforcement_learner.training_steps,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Reinforcement learning training failed", error=str(e))
        raise APIError("Training failed", 500)

@app.route('/api/ai/analyze', methods=['POST'])
@jwt_required()
def analyze_content():
    """Multi-modal content analysis"""
    try:
        data = request.get_json()
        content_type = data.get('type', 'text')
        content = data.get('content')

        if not content:
            raise APIError("Content required", 400)

        if content_type == 'text':
            result = multi_modal_ai.process_text(content)
        elif content_type == 'image':
            result = multi_modal_ai.process_image(content, data.get('image_type', 'url'))
        elif content_type == 'audio':
            result = multi_modal_ai.process_audio(content, data.get('audio_type', 'file'))
        elif content_type == 'video':
            result = multi_modal_ai.process_video(content)
        else:
            raise APIError("Unsupported content type", 400)

        return jsonify({
            'analysis': result,
            'content_type': content_type,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Content analysis failed", error=str(e))
        raise APIError("Analysis failed", 500)

@app.route('/api/ai/collaborate', methods=['POST'])
@jwt_required()
def coordinate_agents():
    """Coordinate multi-agent collaboration"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        task = data.get('task')
        agent_ids = data.get('agent_ids', [])

        if not task or not agent_ids:
            raise APIError("Task and agent IDs required", 400)

        # Initialize collaboration
        await collaboration_system.initialize_collaboration(agent_ids)

        # Coordinate task execution
        result = await collaboration_system.coordinate_task(task)

        return jsonify({
            'coordination_result': result,
            'agents_involved': agent_ids,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Agent coordination failed", error=str(e))
        raise APIError("Coordination failed", 500)

# Performance & Observability Endpoints
@app.route('/api/observability/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get real-time dashboard data"""
    try:
        dashboard_data = realtime_dashboard.get_dashboard_data()

        # Add charts data
        dashboard_data['charts'] = realtime_dashboard.create_performance_charts()

        # Add component health
        dashboard_data['component_health'] = predictive_maintenance.analyze_component_health()

        return jsonify(dashboard_data), 200

    except Exception as e:
        logger.error("Dashboard data retrieval failed", error=str(e))
        raise APIError("Dashboard data unavailable", 500)

@app.route('/api/observability/dashboard.html', methods=['GET'])
@jwt_required()
def get_dashboard_html():
    """Get HTML dashboard"""
    try:
        html_content = create_dashboard_html()
        return html_content, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        logger.error("Dashboard HTML generation failed", error=str(e))
        raise APIError("Dashboard unavailable", 500)

@app.route('/api/observability/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get advanced analytics"""
    try:
        analytics = analytics_engine.analyze_performance_patterns()

        return jsonify({
            'analytics': analytics,
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Analytics generation failed", error=str(e))
        raise APIError("Analytics unavailable", 500)

@app.route('/api/observability/performance', methods=['GET'])
@jwt_required()
def get_performance_report():
    """Get comprehensive performance report"""
    try:
        report = performance_monitor.get_performance_report()

        return jsonify({
            'performance_report': report,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Performance report generation failed", error=str(e))
        raise APIError("Performance report unavailable", 500)

@app.route('/api/observability/cache/stats', methods=['GET'])
@jwt_required()
def get_cache_stats():
    """Get cache performance statistics"""
    try:
        stats = cache_manager.get_stats()

        return jsonify({
            'cache_stats': stats,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Cache stats retrieval failed", error=str(e))
        raise APIError("Cache stats unavailable", 500)

# Security & Compliance Endpoints
@app.route('/api/security/compliance/check', methods=['POST'])
@jwt_required()
def check_compliance():
    """Check compliance with frameworks"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        framework = data.get('framework', 'gdpr')
        data_to_check = data.get('data', {})

        result = compliance_manager.check_compliance(framework, data_to_check)

        return jsonify({
            'compliance_check': result,
            'framework': framework,
            'checked_by': user_id,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Compliance check failed", error=str(e))
        raise APIError("Compliance check failed", 500)

@app.route('/api/security/compliance/report', methods=['GET'])
@jwt_required()
def get_compliance_report():
    """Get compliance report"""
    try:
        framework = request.args.get('framework', 'gdpr')
        days = int(request.args.get('days', 30))

        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        report = compliance_manager.generate_compliance_report(framework, start_date, end_date)

        return jsonify({
            'compliance_report': report,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Compliance report generation failed", error=str(e))
        raise APIError("Compliance report unavailable", 500)

@app.route('/api/security/audit', methods=['GET'])
@jwt_required()
def get_audit_log():
    """Get security audit log"""
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 50))

        # This would normally filter by user permissions
        # For now, return recent audit entries
        audit_entries = list(compliance_manager.audit_trail)[-limit:]

        return jsonify({
            'audit_log': audit_entries,
            'total_entries': len(compliance_manager.audit_trail),
            'returned_entries': len(audit_entries),
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Audit log retrieval failed", error=str(e))
        raise APIError("Audit log unavailable", 500)

@app.route('/api/security/encrypt', methods=['POST'])
@jwt_required()
def encrypt_data():
    """Encrypt sensitive data"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        data_to_encrypt = data.get('data')
        context = data.get('context', 'api_request')

        if not data_to_encrypt:
            raise APIError("Data to encrypt required", 400)

        encrypted = data_encryption.encrypt_data(data_to_encrypt, context)

        return jsonify({
            'encrypted_data': encrypted,
            'context': context,
            'encrypted_by': user_id,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Data encryption failed", error=str(e))
        raise APIError("Encryption failed", 500)

@app.route('/api/security/decrypt', methods=['POST'])
@jwt_required()
def decrypt_data():
    """Decrypt data"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        encrypted_data = data.get('encrypted_data')
        context = data.get('context')

        if not encrypted_data:
            raise APIError("Encrypted data required", 400)

        decrypted = data_encryption.decrypt_data(encrypted_data, context)

        return jsonify({
            'decrypted_data': decrypted,
            'context': context,
            'decrypted_by': user_id,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Data decryption failed", error=str(e))
        raise APIError("Decryption failed", 500)

# Maintenance & Optimization Endpoints
@app.route('/api/maintenance/predictive', methods=['GET'])
@jwt_required()
@admin_required
def get_predictive_maintenance():
    """Get predictive maintenance analysis"""
    try:
        analysis = predictive_maintenance.analyze_component_health()
        predictions = predictive_maintenance.predict_failures()

        return jsonify({
            'component_health': analysis,
            'failure_predictions': predictions,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Predictive maintenance analysis failed", error=str(e))
        raise APIError("Maintenance analysis unavailable", 500)

@app.route('/api/maintenance/optimize', methods=['POST'])
@jwt_required()
@admin_required
def optimize_system():
    """Trigger system optimization"""
    try:
        optimizations = []

        # Database optimization
        if db_optimizer.optimize_connection_pool():
            optimizations.append("Database connection pool optimized")

        # Cache cleanup
        cache_manager.clear()
        optimizations.append("Cache cleared and optimized")

        # Memory cleanup
        import gc
        collected = gc.collect()
        optimizations.append(f"Garbage collection completed: {collected} objects collected")

        return jsonify({
            'optimizations_performed': optimizations,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("System optimization failed", error=str(e))
        raise APIError("Optimization failed", 500)

@app.route('/api/async/task', methods=['POST'])
@jwt_required()
def submit_async_task():
    """Submit task for asynchronous processing"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        task_func_name = data.get('function')
        task_args = data.get('args', [])
        task_kwargs = data.get('kwargs', {})

        if not task_func_name:
            raise APIError("Function name required", 400)

        # Map function names to actual functions (simplified)
        function_map = {
            'analyze_video': lambda url: {'video_url': url, 'analysis': 'completed'},
            'optimize_agent': lambda agent_id: {'agent_id': agent_id, 'optimized': True},
            'train_model': lambda model_type: {'model_type': model_type, 'trained': True}
        }

        if task_func_name not in function_map:
            raise APIError("Unknown function", 400)

        task_id = async_manager.submit_task(function_map[task_func_name], *task_args, **task_kwargs)

        return jsonify({
            'task_id': task_id,
            'status': 'submitted',
            'submitted_by': user_id
        }), 202

    except Exception as e:
        logger.error("Async task submission failed", error=str(e))
        raise APIError("Task submission failed", 500)

@app.route('/api/async/task/<task_id>', methods=['GET'])
@jwt_required()
def get_async_task_status(task_id):
    """Get status of asynchronous task"""
    try:
        status = async_manager.get_task_status(task_id)

        return jsonify({
            'task_id': task_id,
            'task_status': status,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error("Async task status check failed", error=str(e))
        raise APIError("Task status unavailable", 500)

# Register YouTube routes
register_youtube_routes(app)

# Initialize advanced systems
performance_monitor.start_monitoring()

# Register blueprints or additional routes here if needed

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('CHATTY_BACKEND_PORT', 8181))
    debug = os.environ.get('FLASK_ENV') == 'development'

    logger.info("Starting CHATTY Backend Server", port=port, debug=debug)
    app.run(host='0.0.0.0', port=port, debug=debug)
