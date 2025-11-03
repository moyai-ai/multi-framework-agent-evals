"""
Pytest configuration and fixtures for the Landing Page Generator tests.
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.runner import Scenario, ConversationTurn, ScenarioRunner
from src.agents import LandingPageAgents
from src.crew import LandingPageCrew


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        'OPENAI_API_KEY': 'test-api-key',
        'MODEL_NAME': 'gpt-4',
        'CREW_VERBOSE': 'false'
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_idea():
    """Sample landing page idea for testing."""
    return "Create a landing page for a fitness tracking app called FitTrack"


@pytest.fixture
def sample_expanded_concept():
    """Sample expanded concept for testing."""
    return {
        "expanded_concept": "FitTrack - A comprehensive fitness tracking application",
        "target_audience": "Health-conscious individuals aged 25-45",
        "features": [
            "Activity tracking",
            "Nutrition logging",
            "Progress analytics"
        ],
        "benefits": [
            "Improve health",
            "Track progress",
            "Stay motivated"
        ],
        "usp": "AI-powered personalized fitness recommendations",
        "sections": ["hero", "features", "benefits", "testimonials", "cta"],
        "style_guide": {
            "colors": ["#4CAF50", "#2196F3", "#FFC107"],
            "tone": "Motivational and supportive"
        }
    }


@pytest.fixture
def sample_template_plan():
    """Sample template selection plan for testing."""
    return {
        "selected_template": "basic",
        "customization_plan": [
            "Update color scheme",
            "Add fitness-related imagery",
            "Customize CTA buttons"
        ],
        "sections_mapping": {
            "hero": "hero-section",
            "features": "features-grid",
            "testimonials": "testimonials-carousel"
        },
        "color_scheme": {
            "primary": "#4CAF50",
            "secondary": "#2196F3",
            "accent": "#FFC107"
        },
        "typography": {
            "heading": "Montserrat",
            "body": "Open Sans"
        },
        "components_needed": ["hero", "feature-card", "testimonial-card", "cta-button"]
    }


@pytest.fixture
def sample_content():
    """Sample generated content for testing."""
    return {
        "hero": {
            "headline": "Track Your Fitness Journey with FitTrack",
            "subheadline": "The smart way to achieve your health goals",
            "cta_text": "Start Free Trial"
        },
        "features": [
            {
                "title": "Activity Tracking",
                "description": "Monitor your daily activities automatically",
                "icon": "activity"
            },
            {
                "title": "Nutrition Logging",
                "description": "Track calories and nutrients easily",
                "icon": "nutrition"
            },
            {
                "title": "Progress Analytics",
                "description": "Visualize your fitness journey",
                "icon": "analytics"
            }
        ],
        "benefits": [
            "Lose weight effectively",
            "Build healthy habits",
            "Stay motivated with achievements"
        ],
        "testimonials": [
            {
                "name": "John Smith",
                "role": "Fitness Enthusiast",
                "content": "FitTrack helped me lose 20 pounds in 3 months!",
                "rating": 5
            },
            {
                "name": "Emma Wilson",
                "role": "Marathon Runner",
                "content": "The best fitness app I've ever used.",
                "rating": 5
            }
        ],
        "faq": [
            {
                "question": "How does FitTrack work?",
                "answer": "FitTrack uses advanced algorithms to track your activities and provide personalized recommendations."
            },
            {
                "question": "Is it free?",
                "answer": "We offer a free trial with premium features available via subscription."
            }
        ]
    }


@pytest.fixture
def sample_scenario():
    """Sample test scenario for testing."""
    return Scenario(
        name="Test Scenario",
        description="A test scenario for unit testing",
        initial_idea="Create a landing page for a fitness app",
        conversation=[
            ConversationTurn(
                user_input="Create a landing page for a fitness app",
                expected_output_contains=["fitness", "health", "tracking"],
                expected_sections=["hero", "features"],
                skip_validation=False
            )
        ],
        expected_final_output={
            "sections": ["hero", "features", "testimonials"],
            "required_elements": ["<!DOCTYPE html>", "<html", "<body>"]
        },
        metadata={"test_type": "unit_test"}
    )


@pytest.fixture
def scenario_runner(mock_env):
    """Create a scenario runner instance."""
    return ScenarioRunner(verbose=False)


@pytest.fixture
def landing_page_crew(mock_env, temp_dir):
    """Create a landing page crew instance."""
    return LandingPageCrew(
        model_name="gpt-4",
        verbose=False,
        output_dir=str(temp_dir / "output"),
        workdir=str(temp_dir / "workdir")
    )


@pytest.fixture
def mock_crew_response():
    """Mock response from crew execution."""
    def _mock_response(*args, **kwargs):
        return json.dumps({
            "expanded_concept": "Test concept",
            "features": ["Feature 1", "Feature 2"],
            "benefits": ["Benefit 1", "Benefit 2"]
        })
    return _mock_response


@pytest.fixture
def scenario_files():
    """List of scenario JSON files for testing."""
    scenarios_dir = Path(__file__).parent.parent / "src" / "scenarios"
    if scenarios_dir.exists():
        return list(scenarios_dir.glob("*.json"))
    return []


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Mocked AI response"
            )
        )]
    )
    return mock