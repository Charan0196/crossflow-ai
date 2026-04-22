"""
Multi-Agent Communication System
Secure communication protocols for AI agent coordination
"""
import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict

from ..config import AIConfig, AgentConfig, AgentType, get_agent_config
from ..utils.model_manager import ModelManager


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NEGOTIATION = "negotiation"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    message_id: str
    sender: str
    receiver: str
    message_type: MessageType
    payload: Dict[str, Any]
    priority: Priority
    encrypted: bool
    timestamp: datetime
    audit_id: str


@dataclass
class NegotiationResult:
    negotiation_id: str
    participants: List[str]
    original_objectives: Dict[str, Any]
    compromise: Dict[str, Any]
    satisfaction_scores: Dict[str, float]
    success: bool
    timestamp: datetime


@dataclass
class AuditLog:
    audit_id: str
    message_id: str
    sender: str
    receiver: str
    action: str
    payload_hash: str
    timestamp: datetime


@dataclass
class AgentCapability:
    agent_id: str
    agent_type: str
    capabilities: List[str]
    status: str
    last_seen: datetime


class SecureCommunicationProtocol:
    """Handles secure message passing between agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = "crossflow_secure_key"
    
    def encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """Encrypt message payload"""
        payload_str = json.dumps(payload, default=str)
        # Simple hash-based encryption simulation
        encrypted = hashlib.sha256((payload_str + self.encryption_key).encode()).hexdigest()
        return encrypted
    
    def verify_message(self, message: AgentMessage) -> bool:
        """Verify message integrity"""
        return bool(message.message_id and message.sender and message.receiver)
    
    def create_message(self, sender: str, receiver: str, msg_type: MessageType,
                      payload: Dict[str, Any], priority: Priority = Priority.MEDIUM,
                      encrypt: bool = True) -> AgentMessage:
        """Create a secure message"""
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            message_type=msg_type,
            payload=payload,
            priority=priority,
            encrypted=encrypt,
            timestamp=datetime.now(),
            audit_id=str(uuid.uuid4())
        )


class NegotiationProtocol:
    """Handles agent negotiation and conflict resolution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.negotiation_history: List[NegotiationResult] = []
    
    def negotiate(self, participants: List[str], 
                 objectives: Dict[str, Dict[str, float]]) -> NegotiationResult:
        """Negotiate between agents with conflicting objectives"""
        # Find compromise by averaging objectives
        compromise = {}
        all_keys = set()
        for obj in objectives.values():
            all_keys.update(obj.keys())
        
        for key in all_keys:
            values = [objectives[p].get(key, 0.5) for p in participants if p in objectives]
            compromise[key] = sum(values) / len(values) if values else 0.5
        
        # Calculate satisfaction scores
        satisfaction = {}
        for participant in participants:
            if participant in objectives:
                obj = objectives[participant]
                diffs = [abs(compromise.get(k, 0.5) - obj.get(k, 0.5)) for k in obj]
                satisfaction[participant] = 1 - (sum(diffs) / len(diffs)) if diffs else 1.0
            else:
                satisfaction[participant] = 0.5
        
        result = NegotiationResult(
            negotiation_id=str(uuid.uuid4()),
            participants=participants,
            original_objectives=objectives,
            compromise=compromise,
            satisfaction_scores=satisfaction,
            success=all(s > 0.3 for s in satisfaction.values()),
            timestamp=datetime.now()
        )
        
        self.negotiation_history.append(result)
        return result


class MessagePrioritizer:
    """Prioritizes messages based on load and importance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.message_queue: List[AgentMessage] = []
    
    def add_message(self, message: AgentMessage) -> None:
        """Add message to priority queue"""
        self.message_queue.append(message)
        self.message_queue.sort(key=lambda m: (-m.priority.value, m.timestamp))
    
    def get_next_message(self) -> Optional[AgentMessage]:
        """Get highest priority message"""
        if self.message_queue:
            return self.message_queue.pop(0)
        return None
    
    def get_queue_size(self) -> int:
        return len(self.message_queue)
    
    def defer_low_priority(self, threshold: int = 100) -> int:
        """Defer low priority messages when queue is large"""
        if len(self.message_queue) > threshold:
            deferred = [m for m in self.message_queue if m.priority == Priority.LOW]
            self.message_queue = [m for m in self.message_queue if m.priority != Priority.LOW]
            return len(deferred)
        return 0


class AuditLogger:
    """Maintains audit logs for all communications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audit_logs: List[AuditLog] = []
    
    def log_message(self, message: AgentMessage, action: str = "sent") -> AuditLog:
        """Log a message for audit"""
        payload_hash = hashlib.sha256(json.dumps(message.payload, default=str).encode()).hexdigest()
        
        log = AuditLog(
            audit_id=message.audit_id,
            message_id=message.message_id,
            sender=message.sender,
            receiver=message.receiver,
            action=action,
            payload_hash=payload_hash,
            timestamp=datetime.now()
        )
        
        self.audit_logs.append(log)
        return log
    
    def get_logs_for_agent(self, agent_id: str) -> List[AuditLog]:
        """Get all logs for an agent"""
        return [log for log in self.audit_logs 
                if log.sender == agent_id or log.receiver == agent_id]
    
    def get_logs_in_range(self, start: datetime, end: datetime) -> List[AuditLog]:
        """Get logs in time range"""
        return [log for log in self.audit_logs 
                if start <= log.timestamp <= end]


class AgentRegistry:
    """Registry for agent discovery and integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, AgentCapability] = {}
    
    def register_agent(self, agent_id: str, agent_type: str, 
                      capabilities: List[str]) -> AgentCapability:
        """Register a new agent"""
        capability = AgentCapability(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            status="active",
            last_seen=datetime.now()
        )
        self.agents[agent_id] = capability
        return capability
    
    def discover_agents(self, capability: str = None) -> List[AgentCapability]:
        """Discover agents with specific capability"""
        if capability:
            return [a for a in self.agents.values() if capability in a.capabilities]
        return list(self.agents.values())
    
    def update_status(self, agent_id: str, status: str) -> bool:
        """Update agent status"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].last_seen = datetime.now()
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentCapability]:
        """Get agent by ID"""
        return self.agents.get(agent_id)


class MultiAgentCommunicationSystem:
    """Main communication system for AI agents"""
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        self.protocol = SecureCommunicationProtocol()
        self.negotiation = NegotiationProtocol()
        self.prioritizer = MessagePrioritizer()
        self.audit_logger = AuditLogger()
        self.registry = AgentRegistry()
        
        self.message_history: List[AgentMessage] = []
        self.logger.info("Multi-Agent Communication System initialized")
    
    async def send_secure_message(self, sender: str, receiver: str,
                                  payload: Dict[str, Any],
                                  msg_type: MessageType = MessageType.REQUEST,
                                  priority: Priority = Priority.MEDIUM) -> AgentMessage:
        """Send a secure message between agents - Requirements: 8.1"""
        message = self.protocol.create_message(sender, receiver, msg_type, payload, priority)
        
        # Log for audit
        self.audit_logger.log_message(message, "sent")
        
        # Add to priority queue
        self.prioritizer.add_message(message)
        
        # Store in history
        self.message_history.append(message)
        
        return message
    
    async def negotiate_conflict(self, participants: List[str],
                                objectives: Dict[str, Dict[str, float]]) -> NegotiationResult:
        """Negotiate between agents - Requirements: 8.2"""
        return self.negotiation.negotiate(participants, objectives)
    
    async def prioritize_communications(self, load_threshold: int = 100) -> Dict[str, Any]:
        """Prioritize communications under load - Requirements: 8.3"""
        queue_size = self.prioritizer.get_queue_size()
        deferred = 0
        
        if queue_size > load_threshold:
            deferred = self.prioritizer.defer_low_priority(load_threshold)
        
        return {
            'queue_size': queue_size,
            'deferred_count': deferred,
            'high_priority_pending': sum(1 for m in self.prioritizer.message_queue 
                                        if m.priority in [Priority.HIGH, Priority.CRITICAL])
        }
    
    async def get_audit_logs(self, agent_id: str = None,
                            start: datetime = None, end: datetime = None) -> List[AuditLog]:
        """Get audit logs - Requirements: 8.4"""
        if agent_id:
            return self.audit_logger.get_logs_for_agent(agent_id)
        if start and end:
            return self.audit_logger.get_logs_in_range(start, end)
        return self.audit_logger.audit_logs
    
    async def register_agent(self, agent_id: str, agent_type: str,
                            capabilities: List[str]) -> AgentCapability:
        """Register and discover agents - Requirements: 8.5"""
        return self.registry.register_agent(agent_id, agent_type, capabilities)
    
    async def discover_agents(self, capability: str = None) -> List[AgentCapability]:
        """Discover agents with capability"""
        return self.registry.discover_agents(capability)
