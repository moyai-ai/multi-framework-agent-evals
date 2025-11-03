"""Tests for data models."""

import pytest
from datetime import datetime
from src.agent.models import (
    Lead,
    QualificationAnalysis,
    QualificationScore,
    CompanyAnalysis,
    PersonAnalysis,
    CompanySize,
    SearchResult,
)


class TestLead:
    """Test Lead model."""

    def test_lead_creation_minimal(self):
        """Test creating a lead with minimal required fields."""
        lead = Lead(
            name="John Doe",
            email="john@example.com"
        )
        assert lead.name == "John Doe"
        assert lead.email == "john@example.com"
        assert lead.source == "manual"
        assert lead.company is None
        assert lead.title is None
        assert isinstance(lead.created_at, datetime)

    def test_lead_creation_full(self):
        """Test creating a lead with all fields."""
        lead = Lead(
            name="Jane Smith",
            email="jane@techcorp.com",
            company="TechCorp",
            title="CTO",
            linkedin_url="https://linkedin.com/in/janesmith",
            source="conference",
            additional_info={"event": "PyCon 2024", "booth": "A12"}
        )
        assert lead.name == "Jane Smith"
        assert lead.company == "TechCorp"
        assert lead.title == "CTO"
        assert lead.linkedin_url == "https://linkedin.com/in/janesmith"
        assert lead.source == "conference"
        assert lead.additional_info["event"] == "PyCon 2024"

    def test_lead_whitespace_stripping(self):
        """Test that whitespace is stripped from string fields."""
        lead = Lead(
            name="  John Doe  ",
            email="  john@example.com  "
        )
        assert lead.name == "John Doe"
        assert lead.email == "john@example.com"


class TestCompanyAnalysis:
    """Test CompanyAnalysis model."""

    def test_company_analysis_creation(self):
        """Test creating a company analysis."""
        company = CompanyAnalysis(
            name="TechCorp",
            domain="techcorp.com",
            size=CompanySize.ENTERPRISE,
            industry="Software",
            description="Leading software company",
            uses_python=True,
            has_engineering_team=True,
            tech_stack=["Python", "React", "AWS"],
            funding_stage="Series C",
            headquarters="San Francisco, CA"
        )
        assert company.name == "TechCorp"
        assert company.size == CompanySize.ENTERPRISE
        assert company.uses_python is True
        assert "Python" in company.tech_stack
        assert len(company.tech_stack) == 3

    def test_company_size_enum(self):
        """Test CompanySize enum values."""
        assert CompanySize.ENTERPRISE.value == "enterprise"
        assert CompanySize.MID_MARKET.value == "mid_market"
        assert CompanySize.SMALL.value == "small"
        assert CompanySize.STARTUP.value == "startup"
        assert CompanySize.UNKNOWN.value == "unknown"


class TestPersonAnalysis:
    """Test PersonAnalysis model."""

    def test_person_analysis_creation(self):
        """Test creating a person analysis."""
        person = PersonAnalysis(
            name="John Smith",
            current_title="VP of Engineering",
            seniority="Director",
            is_technical=True,
            is_decision_maker=True,
            professional_summary="Experienced engineering leader",
            relevant_experience=["10+ years in ML", "Led teams of 50+"]
        )
        assert person.name == "John Smith"
        assert person.is_technical is True
        assert person.is_decision_maker is True
        assert len(person.relevant_experience) == 2

    def test_person_analysis_minimal(self):
        """Test creating person analysis with minimal fields."""
        person = PersonAnalysis(
            name="Jane Doe"
        )
        assert person.name == "Jane Doe"
        assert person.is_technical is False
        assert person.is_decision_maker is False
        assert person.relevant_experience == []


class TestQualificationAnalysis:
    """Test QualificationAnalysis model."""

    def test_qualification_analysis_creation(self):
        """Test creating a complete qualification analysis."""
        person = PersonAnalysis(
            name="John Smith",
            current_title="CTO",
            is_technical=True,
            is_decision_maker=True
        )

        company = CompanyAnalysis(
            name="TechCorp",
            size=CompanySize.ENTERPRISE,
            uses_python=True,
            has_engineering_team=True
        )

        analysis = QualificationAnalysis(
            lead_id="lead-123",
            person_analysis=person,
            company_analysis=company,
            score=QualificationScore.VERY_HIGH,
            confidence=0.95,
            product_fit_reasons=["Uses Python", "Large engineering team"],
            disqualification_reasons=[],
            recommended_action="immediate_outreach",
            talking_points=["Discuss ML monitoring", "Show enterprise features"],
            data_sources=["LinkedIn", "Company website"],
            summary="High-value enterprise lead with decision-making authority"
        )

        assert analysis.lead_id == "lead-123"
        assert analysis.score == QualificationScore.VERY_HIGH
        assert analysis.confidence == 0.95
        assert len(analysis.product_fit_reasons) == 2
        assert analysis.recommended_action == "immediate_outreach"
        assert isinstance(analysis.analysis_timestamp, datetime)

    def test_qualification_score_enum(self):
        """Test QualificationScore enum values."""
        assert QualificationScore.VERY_HIGH.value == "very_high"
        assert QualificationScore.HIGH.value == "high"
        assert QualificationScore.MEDIUM.value == "medium"
        assert QualificationScore.LOW.value == "low"
        assert QualificationScore.VERY_LOW.value == "very_low"
        assert QualificationScore.UNQUALIFIED.value == "unqualified"

    def test_confidence_validation(self):
        """Test that confidence is validated between 0 and 1."""
        person = PersonAnalysis(name="Test")

        # Valid confidence
        analysis = QualificationAnalysis(
            lead_id="test",
            person_analysis=person,
            score=QualificationScore.MEDIUM,
            confidence=0.5,
            recommended_action="nurture",
            summary="Test"
        )
        assert analysis.confidence == 0.5

        # Test invalid confidence values
        with pytest.raises(ValueError):
            QualificationAnalysis(
                lead_id="test",
                person_analysis=person,
                score=QualificationScore.MEDIUM,
                confidence=1.5,  # Invalid: > 1
                recommended_action="nurture",
                summary="Test"
            )

        with pytest.raises(ValueError):
            QualificationAnalysis(
                lead_id="test",
                person_analysis=person,
                score=QualificationScore.MEDIUM,
                confidence=-0.1,  # Invalid: < 0
                recommended_action="nurture",
                summary="Test"
            )


class TestSearchResult:
    """Test SearchResult model."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            title="Company Profile - TechCorp",
            url="https://techcorp.com/about",
            snippet="TechCorp is a leading software company...",
            source="linkup"
        )
        assert result.title == "Company Profile - TechCorp"
        assert result.url == "https://techcorp.com/about"
        assert "leading software company" in result.snippet
        assert result.source == "linkup"

    def test_search_result_default_source(self):
        """Test that source defaults to 'linkup'."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Test snippet"
        )
        assert result.source == "linkup"