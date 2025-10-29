"""
Comprehensive test suite for the Financial Research Agent System.
"""

import os
import pytest
import asyncio
import json
from pathlib import Path

from src.runner import ScenarioRunner, ScenarioExpectations
from src.context import (
    FinancialResearchContext,
    create_initial_context,
    create_test_context,
    context_diff,
    format_context_summary
)
from src.agents import (
    get_agent_by_name,
    list_agents,
    AGENTS,
    planner_agent,
    search_agent,
    writer_agent,
    verifier_agent
)
from src.tools import (
    is_valid_company_name,
    generate_search_terms
)


class TestContext:
    """Test context management functionality."""

    def test_create_initial_context(self):
        """Test initial context creation."""
        context = create_initial_context(query="Test query")
        assert isinstance(context, FinancialResearchContext)
        assert context.query == "Test query"
        assert context.current_stage == "initial"
        assert context.session_id is not None
        assert len(context.search_plan) == 0
        assert len(context.search_results) == 0

    def test_create_test_context(self):
        """Test context creation with specific values."""
        context = create_test_context(
            query="Analyze Apple",
            company_name="Apple Inc",
            analysis_type="company_analysis"
        )
        assert context.query == "Analyze Apple"
        assert context.company_name == "Apple Inc"
        assert context.analysis_type == "company_analysis"

    def test_context_diff(self):
        """Test context difference detection."""
        old_context = create_initial_context(query="Old query")
        new_context = create_test_context(
            query="New query",
            company_name="Apple Inc"
        )

        diff = context_diff(old_context, new_context)
        assert "query" in diff
        assert "company_name" in diff
        assert diff["query"] == "New query"
        assert diff["company_name"] == "Apple Inc"

    def test_format_context_summary(self, sample_context):
        """Test context summary formatting."""
        summary = format_context_summary(sample_context)
        assert "Apple Inc" in summary
        assert "company_analysis" in summary
        assert "planning" in summary

    def test_context_stage_progression(self):
        """Test context stage transitions."""
        context = create_initial_context()
        assert context.current_stage == "initial"

        context.current_stage = "planning"
        assert context.current_stage == "planning"

        context.current_stage = "searching"
        assert context.current_stage == "searching"


class TestAgents:
    """Test agent functionality."""

    def test_all_agents_exist(self):
        """Test that all required agents are defined."""
        assert "planner" in AGENTS
        assert "search" in AGENTS
        assert "financials" in AGENTS
        assert "risk" in AGENTS
        assert "writer" in AGENTS
        assert "verifier" in AGENTS

    def test_get_agent_by_name(self):
        """Test agent lookup by name."""
        # Exact match
        agent = get_agent_by_name("planner")
        assert agent.name == "Planner Agent"

        # Partial match
        agent = get_agent_by_name("write")
        assert agent.name == "Writer Agent"

        # Case insensitive
        agent = get_agent_by_name("SEARCH")
        assert agent.name == "Search Agent"

        # Non-existent
        agent = get_agent_by_name("nonexistent")
        assert agent is None

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 6
        agent_names = [a["name"] for a in agents]
        assert "Planner Agent" in agent_names
        assert "Search Agent" in agent_names
        assert "Writer Agent" in agent_names
        assert "Verifier Agent" in agent_names

    def test_agent_configurations(self):
        """Test agent configurations are valid."""
        # Planner has no tools
        assert len(planner_agent.tools) == 0

        # Search has web_search_tool
        assert len(search_agent.tools) == 1
        assert search_agent.tools[0].name == "web_search_tool"

        # Writer has analyst tools
        assert len(writer_agent.tools) == 3

        # Verifier has no tools
        assert len(verifier_agent.tools) == 0

    def test_agent_instructions_not_empty(self):
        """Test that all agents have instructions."""
        for key, agent in AGENTS.items():
            assert agent.instructions is not None
            assert len(agent.instructions) > 0


class TestTools:
    """Test tool configuration and helpers."""

    def test_is_valid_company_name(self):
        """Test company name validation."""
        assert is_valid_company_name("Apple Inc")
        assert is_valid_company_name("Tesla")
        assert is_valid_company_name("AB")  # Minimum length
        assert not is_valid_company_name("A")  # Too short
        assert not is_valid_company_name("123")  # All digits

    def test_generate_search_terms_apple(self):
        """Test search term generation for Apple."""
        terms = generate_search_terms("Analyze Apple Inc")
        assert len(terms) > 0
        assert len(terms) <= 4
        assert any("apple" in term.lower() for term in terms)

    def test_generate_search_terms_tesla(self):
        """Test search term generation for Tesla."""
        terms = generate_search_terms("Research Tesla performance")
        assert len(terms) > 0
        assert any("tesla" in term.lower() for term in terms)

    def test_generate_search_terms_generic(self):
        """Test search term generation for generic query."""
        terms = generate_search_terms("Generic company analysis")
        assert len(terms) > 0
        assert len(terms) <= 4


class TestScenarioRunner:
    """Test scenario runner functionality."""

    def test_load_scenario(self, scenario_runner, temp_scenario_file):
        """Test loading a scenario from JSON."""
        scenario = scenario_runner.load_scenario(str(temp_scenario_file))
        assert scenario.name == "Test Scenario"
        assert scenario.description == "A test scenario for unit testing"
        assert scenario.query == "Analyze test company"
        assert scenario.expectations.min_search_terms == 3

    def test_validate_results_pass(self, scenario_runner):
        """Test validation with passing results."""
        expectations = ScenarioExpectations(
            min_search_terms=3,
            required_sections=["Executive Summary", "Conclusion"],
            min_report_length=100,
            required_keywords=["Apple", "revenue"]
        )

        report = """
        # Executive Summary
        Apple Inc showed strong revenue growth.
        # Conclusion
        Overall positive outlook.
        """

        errors = scenario_runner.validate_results(
            expectations,
            search_terms_count=4,
            report=report,
            verification_status="PASSED",
            follow_up_questions=["Q1", "Q2"]
        )

        assert len(errors) == 0

    def test_validate_results_fail_search_terms(self, scenario_runner):
        """Test validation failing on search terms."""
        expectations = ScenarioExpectations(min_search_terms=5)

        errors = scenario_runner.validate_results(
            expectations,
            search_terms_count=3,
            report="Test report",
            verification_status="PASSED",
            follow_up_questions=[]
        )

        assert len(errors) > 0
        assert any("search terms" in error.lower() for error in errors)

    def test_validate_results_fail_required_section(self, scenario_runner):
        """Test validation failing on required section."""
        expectations = ScenarioExpectations(
            required_sections=["Executive Summary", "Risk Assessment"]
        )

        report = "# Executive Summary\nSome content"

        errors = scenario_runner.validate_results(
            expectations,
            search_terms_count=3,
            report=report,
            verification_status="PASSED",
            follow_up_questions=[]
        )

        assert len(errors) > 0
        assert any("risk assessment" in error.lower() for error in errors)

    def test_validate_results_fail_keywords(self, scenario_runner):
        """Test validation failing on required keywords."""
        expectations = ScenarioExpectations(
            required_keywords=["Apple", "iPhone", "revenue"]
        )

        report = "Apple Inc analysis shows growth in revenue."

        errors = scenario_runner.validate_results(
            expectations,
            search_terms_count=3,
            report=report,
            verification_status="PASSED",
            follow_up_questions=[]
        )

        assert len(errors) > 0
        assert any("iphone" in error.lower() for error in errors)


class TestScenarioFiles:
    """Test actual scenario JSON files."""

    @pytest.mark.parametrize("scenario_file", [
        "company_analysis.json",
        "market_research.json",
        "competitor_analysis.json"
    ])
    def test_scenario_file_structure(self, scenario_file):
        """Test that scenario files are valid and well-structured."""
        file_path = Path(__file__).parent.parent / "src" / "scenarios" / scenario_file

        assert file_path.exists(), f"Scenario file {scenario_file} does not exist"

        with open(file_path) as f:
            data = json.load(f)

        # Check required fields
        assert "name" in data
        assert "description" in data
        assert "query" in data
        assert "expectations" in data

        # Check expectations structure
        expectations = data["expectations"]
        valid_fields = {
            "min_search_terms", "required_sections", "verification_should_pass",
            "min_report_length", "required_keywords"
        }
        for key in expectations.keys():
            assert key in valid_fields, f"Invalid expectation field: {key}"

    def test_all_scenarios_loadable(self, scenario_runner, scenario_files):
        """Test that all scenario files can be loaded."""
        assert len(scenario_files) > 0, "No scenario files found"

        for scenario_file in scenario_files:
            scenario = scenario_runner.load_scenario(str(scenario_file))
            assert scenario.name is not None
            assert scenario.query is not None
            assert scenario.expectations is not None


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY to be set"
    )
    def test_simple_research_flow(self):
        """Test a simple research flow with real API calls."""
        from src.manager import FinancialResearchManager

        manager = FinancialResearchManager(verbose=False)
        query = "Quick analysis of Apple Inc"

        result = asyncio.run(manager.run(query))

        assert result is not None
        assert "report" in result
        assert len(result["report"]) > 100
        assert result["context"].current_stage == "complete"

    @pytest.mark.skipif(
        not os.environ.get("RUN_FULL_SCENARIOS"),
        reason="Set RUN_FULL_SCENARIOS=1 to run full scenario tests"
    )
    def test_full_scenarios(self, scenario_files):
        """Run all scenarios end-to-end (requires API key and flag)."""
        runner = ScenarioRunner(verbose=True)

        for scenario_file in scenario_files:
            print(f"\nRunning scenario: {scenario_file.name}")
            scenario = runner.load_scenario(str(scenario_file))
            report = asyncio.run(runner.run_scenario(scenario))

            # Save report
            report_file = f"test_report_{scenario_file.stem}.json"
            runner.save_report(report, report_file)

            # Basic assertions
            assert report.search_terms_count > 0
            assert len(report.full_report) > 0
            print(f"Scenario {scenario.name}: {'PASSED' if report.overall_success else 'FAILED'}")


class TestPerformance:
    """Performance tests."""

    def test_context_operations_fast(self):
        """Test that context operations are fast."""
        import time

        start = time.time()
        for _ in range(1000):
            context = create_initial_context(query="Test")
        duration = time.time() - start

        assert duration < 1.0, "Context creation too slow"

    def test_context_diff_fast(self):
        """Test that context diff is fast."""
        import time

        ctx1 = create_test_context(query="Old", company_name="Company A")
        ctx2 = create_test_context(query="New", company_name="Company B")

        start = time.time()
        for _ in range(1000):
            diff = context_diff(ctx1, ctx2)
        duration = time.time() - start

        assert duration < 1.0, "Context diff too slow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
