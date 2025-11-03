"""Lead Qualification Agent Demo using Pydantic AI.

This package demonstrates how to build an intelligent lead qualification
system using Pydantic AI with web search capabilities via Linkup.so.
"""

from .agent.lead_qualifier import LeadQualificationAgent
from .agent.models import Lead, QualificationAnalysis, QualificationScore

__version__ = "0.1.0"
__all__ = [
    "LeadQualificationAgent",
    "Lead",
    "QualificationAnalysis",
    "QualificationScore",
]