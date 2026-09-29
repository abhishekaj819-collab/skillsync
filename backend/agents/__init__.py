"""
SkillSetu Autonomous Multi-Agent System
Gov-Tech Multi-Agent Architecture for Maharashtra Labour Market Intelligence (SIH PS 26134)

Agents:
1. AuthSecurityAgent: Role-Based Access Control, JWT generation, regex validation, compliance auditing.
2. LMIScraperAgent: Real-time labour market demand scraping, NER cleaning, PII redaction.
3. VectorGapAnalysisAgent: PyTorch dense embedding & cosine similarity mismatch engine (75% threshold).
4. PolicyRoutingAgent: Automated policy directive generation and multi-stakeholder routing.
"""

from .auth_agent import AuthSecurityAgent, get_auth_agent, require_role, AuditLog
from .scraper_agent import LMIScraperAgent
from .vector_agent import VectorGapAnalysisAgent
from .policy_agent import PolicyRoutingAgent

__all__ = [
    "AuthSecurityAgent",
    "get_auth_agent",
    "require_role",
    "AuditLog",
    "LMIScraperAgent",
    "VectorGapAnalysisAgent",
    "PolicyRoutingAgent",
]
