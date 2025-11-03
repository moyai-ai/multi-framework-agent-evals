"""Data models for lead qualification."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class QualificationScore(str, Enum):
    """Lead qualification score categories."""

    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNQUALIFIED = "unqualified"


class CompanySize(str, Enum):
    """Company size categories."""

    ENTERPRISE = "enterprise"  # 1000+ employees
    MID_MARKET = "mid_market"  # 100-999 employees
    SMALL = "small"  # 10-99 employees
    STARTUP = "startup"  # < 10 employees
    UNKNOWN = "unknown"


class Lead(BaseModel):
    """Represents a lead to be qualified."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., description="Full name of the lead")
    email: str = Field(..., description="Email address of the lead")
    company: Optional[str] = Field(None, description="Company name")
    title: Optional[str] = Field(None, description="Job title")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    source: str = Field("manual", description="Source of the lead (e.g., 'manual', 'slack', 'web_form')")
    additional_info: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Any additional information about the lead"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class CompanyAnalysis(BaseModel):
    """Analysis of the lead's company."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Company website domain")
    size: CompanySize = Field(..., description="Estimated company size")
    industry: Optional[str] = Field(None, description="Primary industry")
    description: Optional[str] = Field(None, description="Brief company description")
    uses_python: bool = Field(False, description="Whether the company uses Python in their tech stack")
    has_engineering_team: bool = Field(False, description="Whether the company has an engineering team")
    tech_stack: List[str] = Field(default_factory=list, description="Known technologies used")
    funding_stage: Optional[str] = Field(None, description="Funding stage if applicable")
    headquarters: Optional[str] = Field(None, description="Company headquarters location")


class PersonAnalysis(BaseModel):
    """Analysis of the individual lead."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., description="Person's full name")
    current_title: Optional[str] = Field(None, description="Current job title")
    seniority: Optional[str] = Field(None, description="Seniority level (e.g., 'C-level', 'Director', 'Manager')")
    is_technical: bool = Field(False, description="Whether the person has a technical background")
    is_decision_maker: bool = Field(False, description="Whether they likely have purchasing authority")
    professional_summary: Optional[str] = Field(None, description="Brief professional summary")
    relevant_experience: List[str] = Field(default_factory=list, description="Relevant experience points")


class QualificationAnalysis(BaseModel):
    """Complete qualification analysis for a lead."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: str = Field(..., description="Unique identifier for the lead")
    person_analysis: PersonAnalysis = Field(..., description="Analysis of the individual")
    company_analysis: Optional[CompanyAnalysis] = Field(None, description="Analysis of the company")

    # Qualification metrics
    score: QualificationScore = Field(..., description="Overall qualification score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the qualification (0-1)")

    # Fit analysis
    product_fit_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why this lead is a good fit for the product"
    )
    disqualification_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why this lead might not be a good fit"
    )

    # Recommendations
    recommended_action: str = Field(
        ...,
        description="Recommended next action (e.g., 'immediate_outreach', 'nurture', 'disqualify')"
    )
    talking_points: List[str] = Field(
        default_factory=list,
        description="Suggested talking points for sales outreach"
    )

    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    data_sources: List[str] = Field(
        default_factory=list,
        description="Data sources used for qualification"
    )

    # Summary
    summary: str = Field(..., description="Executive summary of the qualification analysis")


class SearchResult(BaseModel):
    """Result from a web search."""

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field(..., description="Text snippet from the search result")
    source: str = Field("linkup", description="Source of the search result")