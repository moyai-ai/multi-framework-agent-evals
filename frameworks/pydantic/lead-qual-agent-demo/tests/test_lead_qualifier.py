"""Tests for the Lead Qualification Agent."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime

from src.agent.lead_qualifier import LeadQualificationAgent
from src.agent.models import (
    Lead,
    QualificationAnalysis,
    QualificationScore,
    PersonAnalysis,
    CompanyAnalysis,
    CompanySize,
)


@pytest.fixture
def sample_lead():
    """Create a sample lead for testing."""
    return Lead(
        name="John Smith",
        email="john@techcorp.com",
        company="TechCorp",
        title="VP of Engineering",
        source="test"
    )


@pytest.fixture
def mock_qualification_analysis():
    """Create a mock qualification analysis."""
    return QualificationAnalysis(
        lead_id="test-123",
        person_analysis=PersonAnalysis(
            name="John Smith",
            current_title="VP of Engineering",
            is_technical=True,
            is_decision_maker=True
        ),
        company_analysis=CompanyAnalysis(
            name="TechCorp",
            size=CompanySize.ENTERPRISE,
            uses_python=True,
            has_engineering_team=True
        ),
        score=QualificationScore.HIGH,
        confidence=0.85,
        product_fit_reasons=["Uses Python", "Large engineering team"],
        disqualification_reasons=[],
        recommended_action="immediate_outreach",
        talking_points=["Discuss ML monitoring"],
        summary="High-value lead"
    )


class TestLeadQualificationAgent:
    """Test the LeadQualificationAgent class."""

    def test_agent_initialization(self):
        """Test agent initialization with default parameters."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()
            assert agent is not None
            assert agent.search_tool is not None
            assert agent.agent is not None

    def test_agent_initialization_with_custom_model(self):
        """Test agent initialization with custom model."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent(model="gpt-4")
            assert agent is not None

    def test_agent_initialization_with_api_keys(self):
        """Test agent initialization with provided API keys."""
        agent = LeadQualificationAgent(
            api_key="custom-openai-key",
            linkup_api_key="custom-linkup-key"
        )
        assert agent is not None
        assert agent.search_tool is not None

    def test_system_prompt_generation(self):
        """Test that system prompt is generated correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()
            prompt = agent._get_system_prompt()
            assert "lead qualification specialist" in prompt.lower()
            assert "research" in prompt.lower()
            assert "qualification criteria" in prompt.lower()

    @pytest.mark.asyncio
    async def test_qualify_lead(self, sample_lead, mock_qualification_analysis):
        """Test qualifying a single lead."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            # Mock the agent.run method
            mock_result = Mock()
            mock_result.data = mock_qualification_analysis
            agent.agent.run = AsyncMock(return_value=mock_result)

            result = await agent.qualify_lead(sample_lead)

            assert isinstance(result, QualificationAnalysis)
            assert result.score == QualificationScore.HIGH
            assert result.confidence == 0.85
            agent.agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_qualify_lead_with_context(self, sample_lead, mock_qualification_analysis):
        """Test qualifying a lead with additional context."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            mock_result = Mock()
            mock_result.data = mock_qualification_analysis
            agent.agent.run = AsyncMock(return_value=mock_result)

            context = {"additional_info": "Met at conference"}
            result = await agent.qualify_lead(sample_lead, context=context)

            assert isinstance(result, QualificationAnalysis)
            agent.agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_qualify_batch_parallel(self, mock_qualification_analysis):
        """Test qualifying multiple leads in parallel."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            leads = [
                Lead(name=f"Lead {i}", email=f"lead{i}@example.com")
                for i in range(3)
            ]

            mock_result = Mock()
            mock_result.data = mock_qualification_analysis
            agent.agent.run = AsyncMock(return_value=mock_result)

            results = await agent.qualify_batch(leads, parallel=True)

            assert len(results) == 3
            assert all(isinstance(r, QualificationAnalysis) for r in results)
            assert agent.agent.run.call_count == 3

    @pytest.mark.asyncio
    async def test_qualify_batch_sequential(self, mock_qualification_analysis):
        """Test qualifying multiple leads sequentially."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            leads = [
                Lead(name=f"Lead {i}", email=f"lead{i}@example.com")
                for i in range(2)
            ]

            mock_result = Mock()
            mock_result.data = mock_qualification_analysis
            agent.agent.run = AsyncMock(return_value=mock_result)

            results = await agent.qualify_batch(leads, parallel=False)

            assert len(results) == 2
            assert all(isinstance(r, QualificationAnalysis) for r in results)
            assert agent.agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_qualify_batch_with_error(self):
        """Test batch qualification with some errors."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            leads = [
                Lead(name="Good Lead", email="good@example.com"),
                Lead(name="Bad Lead", email="bad@example.com"),
            ]

            # Mock to raise exception for second lead
            async def mock_qualify(lead):
                if "Bad" in lead.name:
                    raise Exception("Test error")
                return mock_qualification_analysis

            agent.qualify_lead = mock_qualify

            results = await agent.qualify_batch(leads, parallel=False)

            # Should only get one result due to error
            assert len(results) == 1

    def test_get_high_value_leads(self):
        """Test filtering high-value leads."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            analyses = [
                QualificationAnalysis(
                    lead_id="1",
                    person_analysis=PersonAnalysis(name="Lead 1"),
                    score=QualificationScore.VERY_HIGH,
                    confidence=0.9,
                    recommended_action="immediate",
                    summary="High value"
                ),
                QualificationAnalysis(
                    lead_id="2",
                    person_analysis=PersonAnalysis(name="Lead 2"),
                    score=QualificationScore.HIGH,
                    confidence=0.8,
                    recommended_action="immediate",
                    summary="Good value"
                ),
                QualificationAnalysis(
                    lead_id="3",
                    person_analysis=PersonAnalysis(name="Lead 3"),
                    score=QualificationScore.MEDIUM,
                    confidence=0.7,
                    recommended_action="nurture",
                    summary="Medium value"
                ),
                QualificationAnalysis(
                    lead_id="4",
                    person_analysis=PersonAnalysis(name="Lead 4"),
                    score=QualificationScore.LOW,
                    confidence=0.6,
                    recommended_action="disqualify",
                    summary="Low value"
                ),
            ]

            high_value = agent.get_high_value_leads(
                analyses,
                min_score=QualificationScore.HIGH,
                min_confidence=0.7
            )

            assert len(high_value) == 2
            assert all(a.score in [QualificationScore.VERY_HIGH, QualificationScore.HIGH] for a in high_value)
            assert all(a.confidence >= 0.7 for a in high_value)

    def test_get_high_value_leads_with_confidence_filter(self):
        """Test filtering leads by confidence level."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            analyses = [
                QualificationAnalysis(
                    lead_id="1",
                    person_analysis=PersonAnalysis(name="Lead 1"),
                    score=QualificationScore.HIGH,
                    confidence=0.9,
                    recommended_action="immediate",
                    summary="High confidence"
                ),
                QualificationAnalysis(
                    lead_id="2",
                    person_analysis=PersonAnalysis(name="Lead 2"),
                    score=QualificationScore.HIGH,
                    confidence=0.5,  # Low confidence
                    recommended_action="immediate",
                    summary="Low confidence"
                ),
            ]

            high_value = agent.get_high_value_leads(
                analyses,
                min_score=QualificationScore.HIGH,
                min_confidence=0.7
            )

            assert len(high_value) == 1
            assert high_value[0].lead_id == "1"

    def test_generate_outreach_priority_list(self):
        """Test generating priority list for outreach."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'LINKUP_API_KEY': 'test-linkup-key'}):
            agent = LeadQualificationAgent()

            analyses = [
                QualificationAnalysis(
                    lead_id="low",
                    person_analysis=PersonAnalysis(name="Low Priority"),
                    company_analysis=CompanyAnalysis(
                        name="SmallCo",
                        size=CompanySize.SMALL
                    ),
                    score=QualificationScore.LOW,
                    confidence=0.6,
                    recommended_action="disqualify",
                    talking_points=[],
                    summary="Low priority lead"
                ),
                QualificationAnalysis(
                    lead_id="high",
                    person_analysis=PersonAnalysis(name="High Priority"),
                    company_analysis=CompanyAnalysis(
                        name="BigCorp",
                        size=CompanySize.ENTERPRISE
                    ),
                    score=QualificationScore.VERY_HIGH,
                    confidence=0.95,
                    recommended_action="immediate_outreach",
                    talking_points=["Point 1", "Point 2"],
                    summary="High priority lead"
                ),
                QualificationAnalysis(
                    lead_id="medium",
                    person_analysis=PersonAnalysis(name="Medium Priority"),
                    company_analysis=CompanyAnalysis(
                        name="MidCo",
                        size=CompanySize.MID_MARKET
                    ),
                    score=QualificationScore.MEDIUM,
                    confidence=0.7,
                    recommended_action="nurture",
                    talking_points=["Point A"],
                    summary="Medium priority lead"
                ),
            ]

            priority_list = agent.generate_outreach_priority_list(analyses)

            assert len(priority_list) == 3
            # Check ordering - should be sorted by score (highest first)
            assert priority_list[0]["lead_id"] == "high"
            assert priority_list[0]["priority"] == 1
            assert priority_list[0]["score"] == QualificationScore.VERY_HIGH

            assert priority_list[1]["lead_id"] == "medium"
            assert priority_list[1]["priority"] == 2

            assert priority_list[2]["lead_id"] == "low"
            assert priority_list[2]["priority"] == 3

            # Check that all required fields are present
            for item in priority_list:
                assert "priority" in item
                assert "lead_id" in item
                assert "name" in item
                assert "company" in item
                assert "score" in item
                assert "confidence" in item
                assert "recommended_action" in item
                assert "key_talking_point" in item
                assert "summary" in item