"""
MEV Analyzer - Detection and Analysis of MEV Activity
Phase 3: Autonomy & MEV Protection

Detects, analyzes, and reports MEV activity to improve protection mechanisms.
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AttackType(Enum):
    SANDWICH = "sandwich"
    FRONTRUN = "frontrun"
    BACKRUN = "backrun"
    LIQUIDATION = "liquidation"
    ARBITRAGE = "arbitrage"
    JIT_LIQUIDITY = "jit_liquidity"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MEVAttack:
    attack_id: str
    attack_type: AttackType
    victim_tx: str
    attacker_txs: List[str]
    extracted_value: float
    block_number: int
    timestamp: datetime
    chain: str
    confidence: float = 0.0


@dataclass
class MEVRiskScore:
    transaction_hash: str
    risk_score: float
    risk_level: RiskLevel
    attack_vectors: List[str]
    estimated_exposure: float
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MEVPattern:
    pattern_id: str
    pattern_type: AttackType
    signature: str
    detection_count: int
    first_seen: datetime
    last_seen: datetime
    effectiveness: float


@dataclass
class MEVAnalysisReport:
    timeframe_start: datetime
    timeframe_end: datetime
    total_attacks_detected: int
    attacks_by_type: Dict[str, int]
    total_value_extracted: float
    total_savings_provided: float
    top_attack_patterns: List[MEVPattern]


class MEVAnalyzer:
    """
    MEV Analyzer detects and analyzes MEV activity to improve protection.
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    
    def __init__(self):
        self.detected_attacks: List[MEVAttack] = []
        self.known_patterns: Dict[str, MEVPattern] = {}
        self.savings_history: List[Dict[str, Any]] = []
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize known MEV attack patterns."""
        patterns = [
            ("sandwich_basic", AttackType.SANDWICH, "buy-victim-sell"),
            ("frontrun_swap", AttackType.FRONTRUN, "copy-higher-gas"),
            ("backrun_arb", AttackType.BACKRUN, "arb-after-large"),
            ("jit_liq", AttackType.JIT_LIQUIDITY, "add-remove-liq"),
        ]
        for pid, ptype, sig in patterns:
            self.known_patterns[pid] = MEVPattern(
                pattern_id=pid,
                pattern_type=ptype,
                signature=sig,
                detection_count=0,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                effectiveness=0.8
            )

    async def detect_mev_attack(
        self,
        tx: Dict[str, Any],
        surrounding_txs: List[Dict[str, Any]]
    ) -> Optional[MEVAttack]:
        """
        Detect MEV attacks on a transaction.
        
        Property 5: MEV Attack Detection
        For any transaction, monitors and detects potential attacks.
        """
        if not surrounding_txs:
            return None
        
        # Check for sandwich attack pattern
        sandwich = self._detect_sandwich(tx, surrounding_txs)
        if sandwich:
            self.detected_attacks.append(sandwich)
            self._log_attack(sandwich)
            return sandwich
        
        # Check for frontrun pattern
        frontrun = self._detect_frontrun(tx, surrounding_txs)
        if frontrun:
            self.detected_attacks.append(frontrun)
            self._log_attack(frontrun)
            return frontrun
        
        # Check for backrun pattern
        backrun = self._detect_backrun(tx, surrounding_txs)
        if backrun:
            self.detected_attacks.append(backrun)
            self._log_attack(backrun)
            return backrun
        
        return None
    
    def _detect_sandwich(
        self,
        tx: Dict[str, Any],
        surrounding: List[Dict[str, Any]]
    ) -> Optional[MEVAttack]:
        """Detect sandwich attack pattern."""
        tx_index = tx.get('index', 0)
        before = [t for t in surrounding if t.get('index', 0) < tx_index]
        after = [t for t in surrounding if t.get('index', 0) > tx_index]
        
        for b in before:
            for a in after:
                if self._is_sandwich_pair(b, a, tx):
                    return MEVAttack(
                        attack_id=self._gen_id(),
                        attack_type=AttackType.SANDWICH,
                        victim_tx=tx.get('hash', ''),
                        attacker_txs=[b.get('hash', ''), a.get('hash', '')],
                        extracted_value=self._estimate_extraction(tx, b, a),
                        block_number=tx.get('block', 0),
                        timestamp=datetime.utcnow(),
                        chain=tx.get('chain', 'ethereum'),
                        confidence=0.85
                    )
        return None

    def _detect_frontrun(
        self,
        tx: Dict[str, Any],
        surrounding: List[Dict[str, Any]]
    ) -> Optional[MEVAttack]:
        """Detect frontrun attack pattern."""
        tx_index = tx.get('index', 0)
        before = [t for t in surrounding if t.get('index', 0) < tx_index]
        
        for b in before:
            if self._is_frontrun(b, tx):
                return MEVAttack(
                    attack_id=self._gen_id(),
                    attack_type=AttackType.FRONTRUN,
                    victim_tx=tx.get('hash', ''),
                    attacker_txs=[b.get('hash', '')],
                    extracted_value=self._estimate_frontrun_value(tx, b),
                    block_number=tx.get('block', 0),
                    timestamp=datetime.utcnow(),
                    chain=tx.get('chain', 'ethereum'),
                    confidence=0.75
                )
        return None
    
    def _detect_backrun(
        self,
        tx: Dict[str, Any],
        surrounding: List[Dict[str, Any]]
    ) -> Optional[MEVAttack]:
        """Detect backrun attack pattern."""
        tx_index = tx.get('index', 0)
        after = [t for t in surrounding if t.get('index', 0) > tx_index]
        
        for a in after:
            if self._is_backrun(tx, a):
                return MEVAttack(
                    attack_id=self._gen_id(),
                    attack_type=AttackType.BACKRUN,
                    victim_tx=tx.get('hash', ''),
                    attacker_txs=[a.get('hash', '')],
                    extracted_value=self._estimate_backrun_value(tx, a),
                    block_number=tx.get('block', 0),
                    timestamp=datetime.utcnow(),
                    chain=tx.get('chain', 'ethereum'),
                    confidence=0.70
                )
        return None
    
    def _is_sandwich_pair(self, before: Dict, after: Dict, victim: Dict) -> bool:
        """Check if transactions form a sandwich."""
        same_sender = before.get('from') == after.get('from')
        same_token = before.get('token') == after.get('token') == victim.get('token')
        opposite_dir = before.get('direction') != after.get('direction')
        return same_sender and same_token and opposite_dir
    
    def _is_frontrun(self, before: Dict, victim: Dict) -> bool:
        """Check if transaction is a frontrun."""
        same_target = before.get('to') == victim.get('to')
        higher_gas = before.get('gas_price', 0) > victim.get('gas_price', 0)
        similar_data = self._similar_calldata(before, victim)
        return same_target and higher_gas and similar_data
    
    def _is_backrun(self, victim: Dict, after: Dict) -> bool:
        """Check if transaction is a backrun."""
        is_arb = after.get('type') == 'arbitrage'
        same_pool = after.get('pool') == victim.get('pool')
        return is_arb or same_pool

    def _similar_calldata(self, tx1: Dict, tx2: Dict) -> bool:
        """Check if two transactions have similar calldata."""
        data1 = tx1.get('data', '')[:10]
        data2 = tx2.get('data', '')[:10]
        return data1 == data2
    
    def _estimate_extraction(self, victim: Dict, before: Dict, after: Dict) -> float:
        """Estimate value extracted in sandwich attack."""
        victim_value = victim.get('value', 0)
        return victim_value * 0.01  # ~1% extraction estimate
    
    def _estimate_frontrun_value(self, victim: Dict, attacker: Dict) -> float:
        """Estimate value extracted in frontrun."""
        return victim.get('value', 0) * 0.005
    
    def _estimate_backrun_value(self, victim: Dict, attacker: Dict) -> float:
        """Estimate value extracted in backrun."""
        return victim.get('value', 0) * 0.003
    
    def _log_attack(self, attack: MEVAttack):
        """
        Log detected MEV attack.
        
        Property 6: MEV Activity Logging
        For any detected MEV activity, maintains complete logs.
        """
        logger.info(
            f"MEV Attack Detected: type={attack.attack_type.value}, "
            f"victim={attack.victim_tx}, value={attack.extracted_value}, "
            f"confidence={attack.confidence}"
        )
    
    def _gen_id(self) -> str:
        """Generate unique attack ID."""
        return hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:12]
    
    async def analyze_historical_mev(
        self,
        timeframe_start: datetime,
        timeframe_end: datetime
    ) -> MEVAnalysisReport:
        """
        Analyze historical MEV activity.
        
        Property 7: Historical MEV Analysis
        For any historical transaction set, calculates total MEV savings.
        """
        attacks = [
            a for a in self.detected_attacks
            if timeframe_start <= a.timestamp <= timeframe_end
        ]
        
        attacks_by_type = {}
        total_extracted = 0.0
        for attack in attacks:
            t = attack.attack_type.value
            attacks_by_type[t] = attacks_by_type.get(t, 0) + 1
            total_extracted += attack.extracted_value
        
        total_savings = sum(s.get('amount', 0) for s in self.savings_history)
        
        return MEVAnalysisReport(
            timeframe_start=timeframe_start,
            timeframe_end=timeframe_end,
            total_attacks_detected=len(attacks),
            attacks_by_type=attacks_by_type,
            total_value_extracted=total_extracted,
            total_savings_provided=total_savings,
            top_attack_patterns=list(self.known_patterns.values())[:5]
        )

    async def calculate_total_savings(
        self,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate total MEV savings provided to users."""
        if user:
            savings = [s for s in self.savings_history if s.get('user') == user]
        else:
            savings = self.savings_history
        
        return {
            "total_savings": sum(s.get('amount', 0) for s in savings),
            "transaction_count": len(savings),
            "average_savings": sum(s.get('amount', 0) for s in savings) / max(len(savings), 1)
        }
    
    async def update_detection_patterns(
        self,
        new_patterns: List[Dict[str, Any]]
    ) -> None:
        """
        Update detection algorithms with new patterns.
        
        Property 8: MEV Pattern Adaptation
        For any new attack pattern, updates detection algorithms.
        """
        for pattern_data in new_patterns:
            pattern = MEVPattern(
                pattern_id=pattern_data.get('id', self._gen_id()),
                pattern_type=AttackType(pattern_data.get('type', 'sandwich')),
                signature=pattern_data.get('signature', ''),
                detection_count=0,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                effectiveness=pattern_data.get('effectiveness', 0.5)
            )
            self.known_patterns[pattern.pattern_id] = pattern
            logger.info(f"Added new MEV pattern: {pattern.pattern_id}")
    
    async def get_realtime_risk_score(
        self,
        tx: Dict[str, Any]
    ) -> MEVRiskScore:
        """
        Get real-time MEV risk score for a transaction.
        
        Property 9: Real-Time MEV Risk Scoring
        For any pending transaction, provides real-time risk scores.
        """
        value = tx.get('value', 0)
        gas_price = tx.get('gas_price', 0)
        
        # Calculate base risk score
        value_risk = min(value / 100000, 0.5)  # Higher value = higher risk
        gas_risk = min(gas_price / 200, 0.3)   # Higher gas = more attractive
        
        risk_score = value_risk + gas_risk
        
        # Determine risk level
        if risk_score < 0.2:
            risk_level = RiskLevel.LOW
        elif risk_score < 0.4:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 0.6:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        attack_vectors = []
        if value > 10000:
            attack_vectors.append("sandwich")
        if gas_price > 100:
            attack_vectors.append("frontrun")
        
        recommendations = []
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Use private RPC routing")
            recommendations.append("Consider splitting into smaller transactions")
        
        return MEVRiskScore(
            transaction_hash=tx.get('hash', ''),
            risk_score=risk_score,
            risk_level=risk_level,
            attack_vectors=attack_vectors,
            estimated_exposure=value * risk_score * 0.01,
            recommendations=recommendations
        )
    
    def record_savings(self, user: str, amount: float, tx_hash: str):
        """Record MEV savings for a user."""
        self.savings_history.append({
            "user": user,
            "amount": amount,
            "tx_hash": tx_hash,
            "timestamp": datetime.utcnow()
        })
