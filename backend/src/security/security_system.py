"""
Security System - Platform Security and Compliance
Phase 3: Autonomy & MEV Protection

Provides security measures for solver network and gas abstraction.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(Enum):
    FUND_MOVEMENT = "fund_movement"
    SOLVER_ACTION = "solver_action"
    PAYMASTER_TRANSACTION = "paymaster_transaction"
    SECURITY_ALERT = "security_alert"
    CONFIGURATION_CHANGE = "configuration_change"


@dataclass
class SecurityAlert:
    alert_id: str
    severity: AlertSeverity
    alert_type: str
    description: str
    affected_entities: List[str]
    timestamp: datetime
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class AuditEntry:
    entry_id: str
    event_type: AuditEventType
    actor: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class SolverAuthorization:
    solver_id: str
    authorized: bool
    permissions: List[str]
    api_key_hash: str
    last_verified: datetime
    expiry: Optional[datetime] = None


@dataclass
class SignatureValidation:
    valid: bool
    signer: Optional[str]
    message_hash: str
    error: Optional[str] = None


class SecuritySystem:
    """
    Security System provides security measures for Phase 3 features.
    
    Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
    """
    
    # Suspicious activity thresholds
    MAX_FAILED_AUTHS_PER_HOUR = 5
    MAX_TRANSACTIONS_PER_MINUTE = 100
    LARGE_TRANSACTION_THRESHOLD = 100000  # USD
    
    def __init__(self):
        self.authorized_solvers: Dict[str, SolverAuthorization] = {}
        self.audit_log: List[AuditEntry] = []
        self.alerts: List[SecurityAlert] = []
        self.failed_auth_attempts: Dict[str, List[datetime]] = {}
        self.transaction_counts: Dict[str, List[datetime]] = {}
        self.paused_operations: Set[str] = set()
        self._secret_key = "crossflow_security_key"  # Would be from env

    async def verify_solver_identity(
        self,
        solver_id: str,
        api_key: str,
        operation: str
    ) -> Dict[str, Any]:
        """
        Verify solver identity and authorization.
        
        Property 45: Solver Identity Verification
        For any solver interaction, verifies identity and authorization.
        """
        auth = self.authorized_solvers.get(solver_id)
        
        if not auth:
            self._record_failed_auth(solver_id)
            return {"authorized": False, "reason": "Solver not registered"}
        
        # Verify API key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if key_hash != auth.api_key_hash:
            self._record_failed_auth(solver_id)
            return {"authorized": False, "reason": "Invalid API key"}
        
        # Check expiry
        if auth.expiry and datetime.utcnow() > auth.expiry:
            return {"authorized": False, "reason": "Authorization expired"}
        
        # Check permissions
        if operation not in auth.permissions and "*" not in auth.permissions:
            return {"authorized": False, "reason": f"Not authorized for {operation}"}
        
        # Update last verified
        auth.last_verified = datetime.utcnow()
        
        self._log_audit(
            AuditEventType.SOLVER_ACTION,
            solver_id,
            f"Verified for {operation}",
            {"operation": operation}
        )
        
        return {"authorized": True, "solver_id": solver_id}
    
    def _record_failed_auth(self, entity_id: str):
        """Record failed authentication attempt."""
        if entity_id not in self.failed_auth_attempts:
            self.failed_auth_attempts[entity_id] = []
        
        self.failed_auth_attempts[entity_id].append(datetime.utcnow())
        
        # Check for suspicious activity
        recent = [
            t for t in self.failed_auth_attempts[entity_id]
            if t > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if len(recent) >= self.MAX_FAILED_AUTHS_PER_HOUR:
            self._create_alert(
                AlertSeverity.HIGH,
                "excessive_failed_auth",
                f"Excessive failed auth attempts from {entity_id}",
                [entity_id]
            )

    async def validate_paymaster_signature(
        self,
        transaction: Dict[str, Any],
        signature: str,
        expected_signer: str
    ) -> SignatureValidation:
        """
        Validate Paymaster transaction signature.
        
        Property 46: Paymaster Signature Validation
        For any Paymaster transaction, validates all signatures.
        """
        # Create message hash
        message = f"{transaction.get('from')}{transaction.get('to')}{transaction.get('value')}{transaction.get('nonce')}"
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        
        # Verify signature (simplified - would use actual crypto)
        expected_sig = hmac.new(
            self._secret_key.encode(),
            message_hash.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_sig:
            self._log_audit(
                AuditEventType.PAYMASTER_TRANSACTION,
                expected_signer,
                "Invalid signature",
                {"transaction": transaction, "message_hash": message_hash}
            )
            return SignatureValidation(
                valid=False,
                signer=None,
                message_hash=message_hash,
                error="Signature verification failed"
            )
        
        self._log_audit(
            AuditEventType.PAYMASTER_TRANSACTION,
            expected_signer,
            "Signature validated",
            {"transaction": transaction, "message_hash": message_hash}
        )
        
        return SignatureValidation(
            valid=True,
            signer=expected_signer,
            message_hash=message_hash
        )
    
    async def detect_suspicious_activity(
        self,
        entity_id: str,
        activity_type: str,
        details: Dict[str, Any]
    ) -> Optional[SecurityAlert]:
        """
        Detect and respond to suspicious activity.
        
        Property 47: Suspicious Activity Response
        For any detected suspicious activity, pauses operations and alerts.
        """
        is_suspicious = False
        severity = AlertSeverity.LOW
        description = ""
        
        # Check for large transactions
        if activity_type == "transaction":
            amount = details.get("amount_usd", 0)
            if amount > self.LARGE_TRANSACTION_THRESHOLD:
                is_suspicious = True
                severity = AlertSeverity.MEDIUM
                description = f"Large transaction: ${amount:,.2f}"
        
        # Check for rapid transactions
        if activity_type == "transaction":
            if entity_id not in self.transaction_counts:
                self.transaction_counts[entity_id] = []
            
            self.transaction_counts[entity_id].append(datetime.utcnow())
            recent = [
                t for t in self.transaction_counts[entity_id]
                if t > datetime.utcnow() - timedelta(minutes=1)
            ]
            
            if len(recent) > self.MAX_TRANSACTIONS_PER_MINUTE:
                is_suspicious = True
                severity = AlertSeverity.HIGH
                description = f"Rapid transactions: {len(recent)} in 1 minute"
        
        # Check for unusual patterns
        if activity_type == "solver_bid" and details.get("price_deviation", 0) > 0.1:
            is_suspicious = True
            severity = AlertSeverity.MEDIUM
            description = f"Unusual bid price deviation: {details.get('price_deviation'):.2%}"
        
        if is_suspicious:
            alert = self._create_alert(severity, activity_type, description, [entity_id])
            
            # Auto-pause for high severity
            if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                await self.pause_operations(entity_id, f"Auto-paused: {description}")
            
            return alert
        
        return None

    async def pause_operations(
        self,
        entity_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """Pause operations for an entity."""
        self.paused_operations.add(entity_id)
        
        self._log_audit(
            AuditEventType.SECURITY_ALERT,
            "system",
            f"Paused operations for {entity_id}",
            {"reason": reason}
        )
        
        logger.warning(f"Operations paused for {entity_id}: {reason}")
        
        return {
            "paused": True,
            "entity_id": entity_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def resume_operations(
        self,
        entity_id: str,
        authorized_by: str
    ) -> Dict[str, Any]:
        """Resume paused operations."""
        if entity_id in self.paused_operations:
            self.paused_operations.remove(entity_id)
            
            self._log_audit(
                AuditEventType.SECURITY_ALERT,
                authorized_by,
                f"Resumed operations for {entity_id}",
                {}
            )
            
            return {"resumed": True, "entity_id": entity_id}
        
        return {"resumed": False, "message": "Entity not paused"}
    
    def is_paused(self, entity_id: str) -> bool:
        """Check if entity operations are paused."""
        return entity_id in self.paused_operations
    
    def log_fund_movement(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        token: str,
        chain: str,
        transaction_hash: str
    ) -> AuditEntry:
        """
        Log fund movement for audit trail.
        
        Property 48: Fund Movement Audit Trail
        For any fund movement, maintains complete audit trails.
        """
        entry = self._log_audit(
            AuditEventType.FUND_MOVEMENT,
            from_address,
            f"Transfer {amount} {token} to {to_address}",
            {
                "from": from_address,
                "to": to_address,
                "amount": amount,
                "token": token,
                "chain": chain,
                "transaction_hash": transaction_hash
            }
        )
        
        return entry
    
    def _log_audit(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        details: Dict[str, Any]
    ) -> AuditEntry:
        """Create audit log entry."""
        entry = AuditEntry(
            entry_id=self._generate_id("audit"),
            event_type=event_type,
            actor=actor,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        self.audit_log.append(entry)
        return entry

    def _create_alert(
        self,
        severity: AlertSeverity,
        alert_type: str,
        description: str,
        affected: List[str]
    ) -> SecurityAlert:
        """Create security alert."""
        alert = SecurityAlert(
            alert_id=self._generate_id("alert"),
            severity=severity,
            alert_type=alert_type,
            description=description,
            affected_entities=affected,
            timestamp=datetime.utcnow()
        )
        
        self.alerts.append(alert)
        logger.warning(f"Security Alert [{severity.value}]: {description}")
        
        return alert
    
    def get_audit_log(
        self,
        entity_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit log entries with filtering."""
        entries = self.audit_log
        
        if entity_id:
            entries = [e for e in entries if e.actor == entity_id]
        
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        
        return entries[-limit:]
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        limit: int = 50
    ) -> List[SecurityAlert]:
        """Get security alerts with filtering."""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return alerts[-limit:]
    
    def resolve_alert(
        self,
        alert_id: str,
        resolution: str,
        resolved_by: str
    ) -> bool:
        """Resolve a security alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution = resolution
                
                self._log_audit(
                    AuditEventType.SECURITY_ALERT,
                    resolved_by,
                    f"Resolved alert {alert_id}",
                    {"resolution": resolution}
                )
                
                return True
        
        return False
    
    def register_solver(
        self,
        solver_id: str,
        api_key: str,
        permissions: List[str]
    ) -> SolverAuthorization:
        """Register a solver for authorization."""
        auth = SolverAuthorization(
            solver_id=solver_id,
            authorized=True,
            permissions=permissions,
            api_key_hash=hashlib.sha256(api_key.encode()).hexdigest(),
            last_verified=datetime.utcnow(),
            expiry=datetime.utcnow() + timedelta(days=365)
        )
        
        self.authorized_solvers[solver_id] = auth
        
        self._log_audit(
            AuditEventType.CONFIGURATION_CHANGE,
            "system",
            f"Registered solver {solver_id}",
            {"permissions": permissions}
        )
        
        return auth
    
    def revoke_solver(self, solver_id: str) -> bool:
        """Revoke solver authorization."""
        if solver_id in self.authorized_solvers:
            del self.authorized_solvers[solver_id]
            
            self._log_audit(
                AuditEventType.CONFIGURATION_CHANGE,
                "system",
                f"Revoked solver {solver_id}",
                {}
            )
            
            return True
        return False
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:10]}"
    
    async def run_security_audit(self) -> Dict[str, Any]:
        """
        Run security audit check.
        
        Property 49: Security Audit Compliance
        For any security audit finding, tracks implementation.
        """
        findings = []
        
        # Check for expired authorizations
        for solver_id, auth in self.authorized_solvers.items():
            if auth.expiry and auth.expiry < datetime.utcnow():
                findings.append({
                    "type": "expired_authorization",
                    "entity": solver_id,
                    "severity": "medium"
                })
        
        # Check for unresolved high-severity alerts
        unresolved_high = [
            a for a in self.alerts
            if not a.resolved and a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        ]
        if unresolved_high:
            findings.append({
                "type": "unresolved_alerts",
                "count": len(unresolved_high),
                "severity": "high"
            })
        
        # Check audit log size
        if len(self.audit_log) > 100000:
            findings.append({
                "type": "audit_log_size",
                "count": len(self.audit_log),
                "severity": "low",
                "recommendation": "Archive old audit entries"
            })
        
        return {
            "audit_time": datetime.utcnow().isoformat(),
            "findings_count": len(findings),
            "findings": findings,
            "status": "pass" if not findings else "needs_attention"
        }
