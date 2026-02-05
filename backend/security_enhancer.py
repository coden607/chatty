#!/usr/bin/env python3
"""
CHATTY Enterprise Security Enhancer
Zero-trust architecture, compliance monitoring, and advanced security features
"""

import os
import time
import hashlib
import hmac
import secrets
import jwt
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from functools import wraps
from collections import defaultdict, deque
import threading
import ipaddress

import bcrypt
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import requests
from flask import request, g, current_app

from server import db, app, User, Agent, Task, logger

class ZeroTrustSecurity:
    """Zero-trust security architecture implementation"""

    def __init__(self):
        self.session_store = {}
        self.trust_scores = defaultdict(float)
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        self.security_events = deque(maxlen=10000)
        self.anomaly_detector = AnomalyDetector()

        # Security monitoring thread
        self.monitoring_thread = threading.Thread(target=self._security_monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def authenticate_request(self, user_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate request using zero-trust principles"""
        trust_score = self._calculate_trust_score(user_id, request_data)

        # Continuous verification
        verifications = {
            'user_identity': self._verify_user_identity(user_id),
            'device_integrity': self._verify_device_integrity(request_data),
            'behavior_anomaly': self._detect_behavior_anomaly(user_id, request_data),
            'location_security': self._verify_location_security(request_data),
            'time_based_access': self._verify_time_based_access(user_id)
        }

        # Calculate overall trust
        verification_score = sum(verifications.values()) / len(verifications)
        overall_trust = (trust_score + verification_score) / 2

        # Determine access level
        if overall_trust >= self.risk_thresholds['high']:
            access_level = 'full'
            mfa_required = False
        elif overall_trust >= self.risk_thresholds['medium']:
            access_level = 'limited'
            mfa_required = True
        else:
            access_level = 'denied'
            mfa_required = True

        # Log security event
        self._log_security_event({
            'event_type': 'authentication_attempt',
            'user_id': user_id,
            'trust_score': overall_trust,
            'access_level': access_level,
            'verifications': verifications,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request_data.get('ip_address'),
            'user_agent': request_data.get('user_agent')
        })

        return {
            'authenticated': access_level != 'denied',
            'access_level': access_level,
            'trust_score': overall_trust,
            'mfa_required': mfa_required,
            'verifications': verifications,
            'session_token': self._generate_session_token(user_id, access_level) if access_level != 'denied' else None
        }

    def _calculate_trust_score(self, user_id: str, request_data: Dict[str, Any]) -> float:
        """Calculate trust score based on multiple factors"""
        score_components = {
            'historical_behavior': self._score_historical_behavior(user_id),
            'device_fingerprint': self._score_device_fingerprint(request_data),
            'network_security': self._score_network_security(request_data),
            'temporal_patterns': self._score_temporal_patterns(user_id),
            'account_health': self._score_account_health(user_id)
        }

        # Weighted average
        weights = {
            'historical_behavior': 0.3,
            'device_fingerprint': 0.2,
            'network_security': 0.25,
            'temporal_patterns': 0.15,
            'account_health': 0.1
        }

        trust_score = sum(score_components[comp] * weights[comp] for comp in score_components)

        # Update stored trust score
        self.trust_scores[user_id] = trust_score

        return trust_score

    def _verify_user_identity(self, user_id: str) -> float:
        """Verify user identity strength"""
        # Check account age, email verification, etc.
        with db.session.begin():
            user = db.session.query(User).get(user_id)
            if not user:
                return 0.0

            score = 0.5  # Base score

            # Account age bonus
            account_age_days = (datetime.utcnow() - user.created_at).days
            if account_age_days > 30:
                score += 0.2
            if account_age_days > 365:
                score += 0.1

            # Email verification
            if '@' in user.email and '.' in user.email:  # Simple email validation
                score += 0.2

            return min(score, 1.0)

    def _verify_device_integrity(self, request_data: Dict[str, Any]) -> float:
        """Verify device integrity"""
        user_agent = request_data.get('user_agent', '')

        # Check for suspicious user agents
        suspicious_patterns = [
            'bot', 'crawler', 'spider', 'scraper',
            'python-requests', 'curl', 'wget'
        ]

        if any(pattern in user_agent.lower() for pattern in suspicious_patterns):
            return 0.2

        # Check for modern browser features
        modern_indicators = ['Chrome', 'Firefox', 'Safari', 'Edge']
        if any(indicator in user_agent for indicator in modern_indicators):
            return 0.9

        return 0.6

    def _detect_behavior_anomaly(self, user_id: str, request_data: Dict[str, Any]) -> float:
        """Detect behavioral anomalies"""
        # This would use machine learning in a full implementation
        # For now, use simple heuristics

        current_hour = datetime.utcnow().hour
        ip_address = request_data.get('ip_address', '')

        # Check if this is an unusual time for the user
        # (would normally be based on historical login patterns)
        unusual_hours = [2, 3, 4, 5]  # Very early morning
        if current_hour in unusual_hours:
            return 0.4

        # Check for rapid requests (potential brute force)
        recent_requests = [event for event in self.security_events
                          if event.get('user_id') == user_id and
                          (datetime.utcnow() - datetime.fromisoformat(event['timestamp'])).seconds < 60]

        if len(recent_requests) > 10:
            return 0.3

        return 0.8

    def _verify_location_security(self, request_data: Dict[str, Any]) -> float:
        """Verify location-based security"""
        ip_address = request_data.get('ip_address', '')

        try:
            ip_obj = ipaddress.ip_address(ip_address)

            # Check if it's a private/reserved IP
            if ip_obj.is_private or ip_obj.is_reserved:
                return 0.9  # Higher trust for internal networks

            # Check for known VPN ranges (simplified)
            if self._is_vpn_ip(ip_address):
                return 0.5

            return 0.7

        except:
            return 0.4

    def _verify_time_based_access(self, user_id: str) -> float:
        """Verify time-based access controls"""
        current_time = datetime.utcnow()

        # Business hours bonus
        if 9 <= current_time.hour <= 17 and current_time.weekday() < 5:
            return 0.9

        # Off-hours penalty (but not complete denial)
        return 0.6

    def _score_historical_behavior(self, user_id: str) -> float:
        """Score based on historical behavior"""
        # Analyze past security events for this user
        user_events = [event for event in self.security_events
                      if event.get('user_id') == user_id]

        if not user_events:
            return 0.5  # Neutral for new users

        # Calculate success rate
        successful_auths = sum(1 for event in user_events
                              if event.get('access_level') != 'denied')
        success_rate = successful_auths / len(user_events)

        return success_rate

    def _score_device_fingerprint(self, request_data: Dict[str, Any]) -> float:
        """Score device fingerprint consistency"""
        # This would normally use device fingerprinting
        # For now, use user agent consistency
        user_agent = request_data.get('user_agent', '')

        if user_agent:
            return 0.8  # Assume consistent for now
        return 0.4

    def _score_network_security(self, request_data: Dict[str, Any]) -> float:
        """Score network security"""
        ip_address = request_data.get('ip_address', '')

        # Check for known malicious IPs (simplified)
        malicious_ranges = ['10.0.0.0/8', '172.16.0.0/12']  # Example
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            for malicious_range in malicious_ranges:
                if ip_obj in ipaddress.ip_network(malicious_range):
                    return 0.2
        except:
            pass

        return 0.8

    def _score_temporal_patterns(self, user_id: str) -> float:
        """Score temporal access patterns"""
        # Analyze login time patterns
        user_events = [event for event in self.security_events
                      if event.get('user_id') == user_id and
                      event.get('event_type') == 'authentication_attempt']

        if len(user_events) < 5:
            return 0.5

        # Check for consistent timing (good) vs random timing (suspicious)
        hours = [datetime.fromisoformat(event['timestamp']).hour for event in user_events[-10:]]
        hour_variance = sum((h - sum(hours)/len(hours))**2 for h in hours) / len(hours)

        # Lower variance = more consistent = higher score
        consistency_score = max(0, 1 - hour_variance / 50)

        return consistency_score

    def _score_account_health(self, user_id: str) -> float:
        """Score account health"""
        with db.session.begin():
            user = db.session.query(User).get(user_id)
            if not user:
                return 0.0

            score = 0.5

            # Account is active
            if user.is_active:
                score += 0.2

            # Recent login (within 30 days)
            if user.last_login and (datetime.utcnow() - user.last_login).days < 30:
                score += 0.2

            # Has completed tasks (engaged user)
            task_count = db.session.query(Task).filter_by(user_id=user_id).count()
            if task_count > 0:
                score += 0.1

            return min(score, 1.0)

    def _generate_session_token(self, user_id: str, access_level: str) -> str:
        """Generate secure session token"""
        payload = {
            'user_id': user_id,
            'access_level': access_level,
            'issued_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'session_id': secrets.token_hex(16)
        }

        # Store session
        session_id = payload['session_id']
        self.session_store[session_id] = {
            'user_id': user_id,
            'access_level': access_level,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'trust_score': self.trust_scores.get(user_id, 0.5)
        }

        # Clean expired sessions periodically
        self._cleanup_expired_sessions()

        return session_id

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token"""
        if session_token not in self.session_store:
            return None

        session = self.session_store[session_token]

        # Check expiration (1 hour)
        if (datetime.utcnow() - session['created_at']).total_seconds() > 3600:
            del self.session_store[session_token]
            return None

        # Update last activity
        session['last_activity'] = datetime.utcnow()

        return session

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, session in self.session_store.items():
            if (current_time - session['created_at']).total_seconds() > 3600:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.session_store[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def _is_vpn_ip(self, ip_address: str) -> bool:
        """Check if IP is likely from a VPN (simplified)"""
        # This would use a VPN IP database in production
        vpn_ranges = [
            '10.0.0.0/8',  # Private networks often used by VPNs
            '172.16.0.0/12'
        ]

        try:
            ip_obj = ipaddress.ip_address(ip_address)
            for vpn_range in vpn_ranges:
                if ip_obj in ipaddress.ip_network(vpn_range):
                    return True
        except:
            pass

        return False

    def _log_security_event(self, event: Dict[str, Any]):
        """Log security event"""
        self.security_events.append(event)

        # Log critical events immediately
        if event.get('trust_score', 1.0) < 0.3:
            logger.warning(f"SECURITY ALERT: Low trust score for user {event.get('user_id')}: {event['trust_score']}")

    def _security_monitoring_loop(self):
        """Continuous security monitoring"""
        while True:
            try:
                # Analyze recent events for threats
                recent_events = list(self.security_events)[-100:]  # Last 100 events

                # Detect brute force attempts
                ip_attempts = defaultdict(int)
                for event in recent_events:
                    if event.get('event_type') == 'authentication_attempt':
                        ip = event.get('ip_address', 'unknown')
                        ip_attempts[ip] += 1

                for ip, attempts in ip_attempts.items():
                    if attempts > 10:  # More than 10 attempts from same IP
                        logger.warning(f"POTENTIAL BRUTE FORCE: {attempts} attempts from {ip}")

                # Clean up old events (keep last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                # Note: deque doesn't support slice assignment
                remaining_events = [
                    event for event in self.security_events
                    if datetime.fromisoformat(event['timestamp']) > cutoff_time
                ]
                self.security_events.clear()
                self.security_events.extend(remaining_events)

            except Exception as e:
                logger.error(f"Security monitoring error: {str(e)}")

            time.sleep(60)  # Check every minute

class ComplianceManager:
    """Enterprise compliance management (GDPR, SOX, HIPAA, etc.)"""

    def __init__(self):
        self.compliance_frameworks = {
            'gdpr': GDPRCompliance(),
            'sox': SOXCompliance(),
            'hipaa': HIPAACompliance(),
            'ccpa': CCPACompliance()
        }
        self.audit_trail = deque(maxlen=50000)
        self.compliance_status = {}

    def check_compliance(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with specified framework"""
        if framework not in self.compliance_frameworks:
            return {'compliant': False, 'error': f'Unknown framework: {framework}'}

        compliance_checker = self.compliance_frameworks[framework]
        result = compliance_checker.check_compliance(data)

        # Log compliance check
        self._log_compliance_event(framework, data, result)

        return result

    def audit_data_access(self, user_id: str, data_type: str, action: str, justification: str = None):
        """Audit data access for compliance"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'data_type': data_type,
            'justification': justification,
            'ip_address': getattr(request, 'remote_addr', 'unknown') if request else 'unknown',
            'user_agent': getattr(request, 'headers', {}).get('User-Agent', 'unknown') if request else 'unknown'
        }

        self.audit_trail.append(audit_entry)

        # Check for compliance violations
        self._check_audit_compliance(audit_entry)

    def generate_compliance_report(self, framework: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for specified period"""
        relevant_audits = [
            audit for audit in self.audit_trail
            if start_date <= datetime.fromisoformat(audit['timestamp']) <= end_date
        ]

        violations = [audit for audit in relevant_audits if self._is_compliance_violation(audit)]

        return {
            'framework': framework,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_audits': len(relevant_audits),
            'violations': len(violations),
            'compliance_rate': (len(relevant_audits) - len(violations)) / max(len(relevant_audits), 1),
            'violation_details': violations[:10]  # Last 10 violations
        }

    def _log_compliance_event(self, framework: str, data: Dict[str, Any], result: Dict[str, Any]):
        """Log compliance check event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'framework': framework,
            'data_type': data.get('type', 'unknown'),
            'compliant': result.get('compliant', False),
            'violations': result.get('violations', []),
            'severity': result.get('severity', 'unknown')
        }

        self.audit_trail.append(event)

    def _check_audit_compliance(self, audit_entry: Dict[str, Any]):
        """Check if audit entry complies with policies"""
        # Implement compliance checks based on frameworks
        pass

    def _is_compliance_violation(self, audit_entry: Dict[str, Any]) -> bool:
        """Check if audit entry represents a compliance violation"""
        # Simple violation detection - would be more sophisticated in production
        suspicious_actions = ['unauthorized_access', 'data_breach', 'policy_violation']

        return audit_entry.get('action', '') in suspicious_actions

class GDPRCompliance:
    """GDPR compliance checker"""

    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check GDPR compliance"""
        violations = []
        compliant = True

        # Check for personal data processing
        if self._contains_personal_data(data):
            # Check for legal basis
            if not data.get('legal_basis'):
                violations.append('Missing legal basis for personal data processing')
                compliant = False

            # Check for consent
            if not data.get('consent_obtained'):
                violations.append('User consent not obtained for personal data')
                compliant = False

            # Check data minimization
            if not self._is_data_minimized(data):
                violations.append('Data not minimized - excessive personal data collected')
                compliant = False

        return {
            'compliant': compliant,
            'violations': violations,
            'severity': 'high' if not compliant else 'low',
            'recommendations': self._get_gdpr_recommendations(violations)
        }

    def _contains_personal_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains personal information"""
        personal_data_fields = ['email', 'name', 'address', 'phone', 'ssn', 'ip_address']

        data_str = json.dumps(data).lower()
        return any(field in data_str for field in personal_data_fields)

    def _is_data_minimized(self, data: Dict[str, Any]) -> bool:
        """Check if data is minimized"""
        # Simple check - data should not have excessive fields
        return len(data) <= 10  # Arbitrary limit

    def _get_gdpr_recommendations(self, violations: List[str]) -> List[str]:
        """Get GDPR-specific recommendations"""
        recommendations = []
        for violation in violations:
            if 'legal basis' in violation:
                recommendations.append('Document legal basis for data processing (e.g., legitimate interest, consent)')
            elif 'consent' in violation:
                recommendations.append('Implement consent management system with opt-out capabilities')
            elif 'data minimized' in violation:
                recommendations.append('Review data collection practices to minimize personal data gathered')

        return recommendations

class SOXCompliance:
    """SOX compliance checker"""

    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check SOX compliance (financial reporting)"""
        violations = []
        compliant = True

        # Check for financial data handling
        if self._contains_financial_data(data):
            # Check for audit trails
            if not data.get('audit_trail_maintained'):
                violations.append('Financial data missing audit trail')
                compliant = False

            # Check for access controls
            if not data.get('access_controls_implemented'):
                violations.append('Inadequate access controls for financial data')
                compliant = False

            # Check for change management
            if not data.get('change_management_process'):
                violations.append('Missing change management for financial systems')
                compliant = False

        return {
            'compliant': compliant,
            'violations': violations,
            'severity': 'critical' if not compliant else 'low'
        }

    def _contains_financial_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains financial information"""
        financial_fields = ['revenue', 'profit', 'balance', 'financial', 'accounting', 'audit']

        data_str = json.dumps(data).lower()
        return any(field in data_str for field in financial_fields)

class HIPAACompliance:
    """HIPAA compliance checker"""

    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check HIPAA compliance (health data)"""
        violations = []
        compliant = True

        if self._contains_health_data(data):
            if not data.get('phi_encrypted'):
                violations.append('Protected Health Information (PHI) not encrypted')
                compliant = False

            if not data.get('access_logged'):
                violations.append('Health data access not logged')
                compliant = False

            if not data.get('breach_notification_plan'):
                violations.append('Missing breach notification plan')
                compliant = False

        return {
            'compliant': compliant,
            'violations': violations,
            'severity': 'critical' if not compliant else 'low'
        }

    def _contains_health_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains health information"""
        health_fields = ['medical', 'health', 'diagnosis', 'treatment', 'patient', 'phi']

        data_str = json.dumps(data).lower()
        return any(field in data_str for field in health_fields)

class CCPACompliance:
    """CCPA compliance checker"""

    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check CCPA compliance (California privacy)"""
        violations = []
        compliant = True

        if self._contains_personal_data(data):
            if not data.get('privacy_notice_provided'):
                violations.append('Privacy notice not provided to users')
                compliant = False

            if not data.get('opt_out_mechanism'):
                violations.append('No mechanism for users to opt-out of data sale')
                compliant = False

        return {
            'compliant': compliant,
            'violations': violations,
            'severity': 'high' if not compliant else 'low'
        }

    def _contains_personal_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains personal information"""
        return GDPRCompliance()._contains_personal_data(data)

class DataEncryption:
    """Enterprise-grade data encryption"""

    def __init__(self):
        self.key_rotation_interval = timedelta(days=30)
        self.encryption_keys = {}
        self._initialize_keys()

    def _initialize_keys(self):
        """Initialize encryption keys"""
        # Use stable salt from environment or fallback to a stable default
        # In production, ENCRYPTION_SALT must be set to a unique, random value
        salt_env = os.environ.get('ENCRYPTION_SALT')
        if not salt_env:
            logger.warning("ENCRYPTION_SALT not set, using stable default. Persistent data may be at risk!")
            salt = b'chatty_default_stable_salt_v1' # Stable fallback for development
        else:
            salt = salt_env.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Retrieve password from environment; warn if using insecure default
        password = os.environ.get('ENCRYPTION_PASSWORD')
        if not password:
            logger.warning("ENCRYPTION_PASSWORD not set, using insecure default!")
            password = 'default_insecure_key'

        master_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.master_cipher = Fernet(master_key)

    def encrypt_data(self, data: Any, context: str = 'general') -> str:
        """Encrypt data with context-aware encryption"""
        # Serialize data
        if isinstance(data, dict):
            data_str = json.dumps(data)
        else:
            data_str = str(data)

        # Add metadata
        encrypted_data = {
            'data': data_str,
            'context': context,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }

        # Encrypt
        encrypted_json = json.dumps(encrypted_data)
        encrypted_bytes = self.master_cipher.encrypt(encrypted_json.encode())

        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt_data(self, encrypted_data: str, context: str = None) -> Any:
        """Decrypt data with integrity verification"""
        try:
            # Decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            decrypted_json = self.master_cipher.decrypt(encrypted_bytes)
            decrypted_data = json.loads(decrypted_json.decode())

            # Verify context if provided
            if context and decrypted_data.get('context') != context:
                raise ValueError("Context mismatch")

            # Parse data
            data_str = decrypted_data['data']
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return data_str

        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise

    def rotate_keys(self):
        """Rotate encryption keys"""
        logger.info("Rotating encryption keys")
        old_cipher = self.master_cipher
        self._initialize_keys()

        # In a real implementation, you would need to re-encrypt existing data
        # with the new key while maintaining access to old keys for decryption

# Decorators
def require_zero_trust(func):
    """Decorator for zero-trust authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'error': 'Authentication required'}, 401

        request_data = {
            'ip_address': getattr(request, 'remote_addr', 'unknown'),
            'user_agent': getattr(request, 'headers', {}).get('User-Agent', 'unknown'),
            'endpoint': request.endpoint,
            'method': request.method
        }

        auth_result = zero_trust_security.authenticate_request(user_id, request_data)

        if not auth_result['authenticated']:
            return {'error': 'Access denied', 'reason': 'Zero-trust authentication failed'}, 403

        # Store auth result in request context
        g.auth_result = auth_result

        return func(*args, **kwargs)
    return wrapper

def audit_access(data_type: str, action: str):
    """Decorator for access auditing"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = getattr(g, 'user_id', None)
            if user_id:
                justification = getattr(request, 'json', {}).get('justification', 'API access')
                compliance_manager.audit_data_access(user_id, data_type, action, justification)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def encrypt_response(func):
    """Decorator to encrypt API responses containing sensitive data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # Check if response contains sensitive data
        if isinstance(result, tuple):
            response_data, status_code = result
        else:
            response_data, status_code = result, 200

        if isinstance(response_data, dict) and any(key in response_data for key in ['password', 'token', 'secret']):
            # Encrypt sensitive fields
            encrypted_data = response_data.copy()
            for sensitive_key in ['password', 'token', 'secret']:
                if sensitive_key in encrypted_data:
                    encrypted_data[sensitive_key] = data_encryption.encrypt_data(
                        encrypted_data[sensitive_key], f'api_response_{sensitive_key}'
                    )
                    encrypted_data[f'{sensitive_key}_encrypted'] = True

            return encrypted_data, status_code

        return result
    return wrapper

class AnomalyDetector:
    """Machine learning-based anomaly detection"""

    def __init__(self):
        self.baseline_metrics = {}
        self.anomaly_threshold = 3.0  # Standard deviations

    def detect_anomaly(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in metrics"""
        anomalies = {}

        for metric_name, value in metrics.items():
            if metric_name in self.baseline_metrics:
                baseline = self.baseline_metrics[metric_name]
                mean = baseline.get('mean', value)
                std = baseline.get('std', 1)

                if std > 0:
                    z_score = abs(value - mean) / std
                    if z_score > self.anomaly_threshold:
                        anomalies[metric_name] = {
                            'value': value,
                            'expected': mean,
                            'z_score': z_score,
                            'severity': 'high' if z_score > 5 else 'medium'
                        }

        return anomalies

    def update_baseline(self, metrics: Dict[str, Any]):
        """Update baseline metrics"""
        for metric_name, value in metrics.items():
            if metric_name not in self.baseline_metrics:
                self.baseline_metrics[metric_name] = {'values': []}

            self.baseline_metrics[metric_name]['values'].append(value)

            # Keep only last 100 values
            values = self.baseline_metrics[metric_name]['values'][-100:]

            if len(values) >= 10:  # Need minimum samples
                import numpy as np
                self.baseline_metrics[metric_name]['mean'] = np.mean(values)
                self.baseline_metrics[metric_name]['std'] = np.std(values)

# Global instances (Moved to end to ensure all classes are defined)
zero_trust_security = ZeroTrustSecurity()
compliance_manager = ComplianceManager()
data_encryption = DataEncryption()
