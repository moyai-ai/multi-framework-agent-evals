"""
Comprehensive test suite for the Landing Page Generator Agent System.
"""

import os
import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.agents import (
    LandingPageAgents,
    get_agent_by_name,
    list_agents,
    get_initial_agent
)
from src.tasks import LandingPageTasks, create_landing_page_tasks
from src.crew import LandingPageCrew
from src.runner import ScenarioRunner, Scenario, ConversationTurn
from src.tools import (
    SearchTool,
    FileOperationsTool,
    TemplateManagerTool,
    ContentGeneratorTool,
    HTMLValidator,
    ValidateHTMLTool
)


class TestAgents:
    """Test agent functionality."""

    def test_agent_creation(self, mock_env):
        """Test that agents can be created successfully."""
        factory = LandingPageAgents()

        # Test each agent creation
        idea_analyst = factory.idea_analyst()
        assert idea_analyst.role == "Senior Idea Analyst"
        assert idea_analyst.allow_delegation is False

        template_selector = factory.template_selector()
        assert template_selector.role == "Senior UX/UI Designer"
        assert template_selector.allow_delegation is False

        content_creator = factory.content_creator()
        assert content_creator.role == "Senior Content Strategist"
        assert content_creator.allow_delegation is False

        qa_agent = factory.quality_assurance()
        assert qa_agent.role == "Senior QA Engineer"
        assert qa_agent.allow_delegation is False

    def test_get_all_agents(self, mock_env):
        """Test getting all agents."""
        factory = LandingPageAgents()
        agents = factory.get_all_agents()

        assert len(agents) == 4
        roles = [agent.role for agent in agents]
        assert "Senior Idea Analyst" in roles
        assert "Senior UX/UI Designer" in roles
        assert "Senior Content Strategist" in roles
        assert "Senior QA Engineer" in roles

    def test_get_initial_agent(self, mock_env):
        """Test getting the initial agent."""
        agent = get_initial_agent()
        assert agent.role == "Senior Idea Analyst"

    def test_get_agent_by_name(self, mock_env):
        """Test agent lookup by name."""
        # Test exact matches
        agent = get_agent_by_name("idea")
        assert agent.role == "Senior Idea Analyst"

        agent = get_agent_by_name("template")
        assert agent.role == "Senior UX/UI Designer"

        agent = get_agent_by_name("content")
        assert agent.role == "Senior Content Strategist"

        agent = get_agent_by_name("qa")
        assert agent.role == "Senior QA Engineer"

        # Test non-existent
        agent = get_agent_by_name("nonexistent")
        assert agent is None

    def test_list_agents(self, mock_env):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 4

        agent_keys = [a["key"] for a in agents]
        assert "idea_analyst" in agent_keys
        assert "template_selector" in agent_keys
        assert "content_creator" in agent_keys
        assert "quality_assurance" in agent_keys


class TestTasks:
    """Test task functionality."""

    def test_task_creation(self, mock_env, sample_idea, sample_expanded_concept, sample_template_plan):
        """Test that tasks can be created successfully."""
        factory = LandingPageTasks()

        # Test expand idea task
        task = factory.expand_idea_task(sample_idea)
        assert "FitTrack" in task.description
        assert task.agent.role == "Senior Idea Analyst"

        # Test select template task
        task = factory.select_template_task(sample_expanded_concept)
        assert task.agent.role == "Senior UX/UI Designer"

        # Test create content task
        task = factory.create_content_task(sample_expanded_concept, sample_template_plan)
        assert task.agent.role == "Senior Content Strategist"

        # Test quality review task
        task = factory.quality_review_task(sample_expanded_concept, sample_template_plan, {})
        assert task.agent.role == "Senior QA Engineer"

    def test_create_landing_page_tasks(self, mock_env, sample_idea):
        """Test creating all tasks at once."""
        tasks = create_landing_page_tasks(sample_idea)

        assert "expand_idea" in tasks
        assert "select_template" in tasks
        assert "create_content" in tasks
        assert "quality_review" in tasks
        assert "generate_page" in tasks

        # Verify all tasks are properly configured
        for task_name, task in tasks.items():
            assert task.description is not None
            assert task.agent is not None
            assert task.expected_output is not None


class TestTools:
    """Test custom tools functionality."""

    def test_search_tool(self):
        """Test the search tool."""
        result = SearchTool._run(query="landing page design tips", max_results=3)
        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_file_operations_tool(self, temp_dir):
        """Test file operations tool."""
        # Use workdir which is allowed by the tool
        workdir = Path("./workdir")
        workdir.mkdir(exist_ok=True)
        test_file = workdir / "test.txt"
        test_content = "Test content"

        # Test write operation
        result = FileOperationsTool._run(operation="write", file_path=str(test_file), content=test_content)
        assert "Successfully wrote" in result
        assert test_file.exists()

        # Test read operation
        result = FileOperationsTool._run(operation="read", file_path=str(test_file))
        assert result == test_content

        # Test list operation
        result = FileOperationsTool._run(operation="list", file_path=str(workdir))
        files = json.loads(result)
        assert "test.txt" in files

        # Cleanup
        test_file.unlink(missing_ok=True)

    def test_template_manager_tool(self, temp_dir):
        """Test template manager tool."""
        # Create a test template
        template_dir = temp_dir / "templates" / "test_template"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "index.html"
        template_file.write_text("<html>{{ title }}</html>")

        # Test list action with patched templates directory
        with patch('src.tools.Path') as mock_path:
            mock_path.return_value = temp_dir / "templates"
            result = TemplateManagerTool._run(action="list", template_name="test_template")
            # The test should handle the mocked path correctly
            assert isinstance(result, str)

    def test_content_generator_tool(self):
        """Test content generator tool."""
        context = {"industry": "fitness", "target_audience": "athletes"}

        # Test hero section
        result = ContentGeneratorTool._run(section="hero", context=context)
        data = json.loads(result)
        assert "headline" in data
        assert "subheadline" in data
        assert "cta_text" in data

        # Test features section
        result = ContentGeneratorTool._run(section="features", context=context)
        data = json.loads(result)
        assert "features" in data
        assert isinstance(data["features"], list)

        # Test testimonials section
        result = ContentGeneratorTool._run(section="testimonials", context=context)
        data = json.loads(result)
        assert "testimonials" in data
        assert isinstance(data["testimonials"], list)

    def test_html_validator(self):
        """Test HTML validation."""
        validator = HTMLValidator()

        # Test valid HTML
        valid_html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Page</title>
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
        </html>"""

        result = validator.validate_html(valid_html)
        assert result["valid"] is True
        assert len(result["issues"]) == 0

        # Test invalid HTML
        invalid_html = "<div>No DOCTYPE or structure</div>"
        result = validator.validate_html(invalid_html)
        assert result["valid"] is False
        assert len(result["issues"]) > 0


class TestCrew:
    """Test crew orchestration functionality."""

    def test_crew_initialization(self, landing_page_crew):
        """Test crew initialization."""
        assert landing_page_crew.model_name == "gpt-4"
        assert landing_page_crew.output_dir.exists()
        assert landing_page_crew.workdir.exists()

    @patch('src.crew.Crew')
    def test_expand_idea_crew(self, mock_crew_class, landing_page_crew, sample_idea):
        """Test expand idea crew creation."""
        crew = landing_page_crew.expand_idea_crew(sample_idea)
        mock_crew_class.assert_called_once()
        call_args = mock_crew_class.call_args
        assert len(call_args[1]['agents']) == 1
        assert len(call_args[1]['tasks']) == 1

    @patch('src.crew.Crew')
    def test_template_selection_crew(self, mock_crew_class, landing_page_crew, sample_expanded_concept):
        """Test template selection crew creation."""
        crew = landing_page_crew.template_selection_crew(sample_expanded_concept)
        mock_crew_class.assert_called_once()

    @patch('src.crew.Crew')
    def test_content_creation_crew(self, mock_crew_class, landing_page_crew,
                                  sample_expanded_concept, sample_template_plan):
        """Test content creation crew creation."""
        crew = landing_page_crew.content_creation_crew(sample_expanded_concept, sample_template_plan)
        mock_crew_class.assert_called_once()
        call_args = mock_crew_class.call_args
        assert len(call_args[1]['agents']) == 2  # Content creator and QA
        assert len(call_args[1]['tasks']) == 2

    def test_parse_result(self, landing_page_crew):
        """Test result parsing."""
        # Test JSON parsing
        json_result = '{"test": "value", "number": 123}'
        parsed = landing_page_crew.parse_result(json_result)
        assert parsed["test"] == "value"
        assert parsed["number"] == 123

        # Test non-JSON result
        text_result = "This is plain text"
        parsed = landing_page_crew.parse_result(text_result)
        assert "raw_output" in parsed
        assert parsed["parsed"] is False

    def test_generate_landing_page(self, landing_page_crew, sample_template_plan, sample_content):
        """Test landing page generation."""
        output_file = landing_page_crew.generate_landing_page(sample_template_plan, sample_content)

        assert output_file
        assert Path(output_file).exists()

        # Read and verify content
        with open(output_file, 'r') as f:
            html_content = f.read()

        assert "<!DOCTYPE html>" in html_content
        assert sample_content["hero"]["headline"] in html_content
        assert sample_content["hero"]["cta_text"] in html_content


class TestScenarioRunner:
    """Test scenario runner functionality."""

    def test_load_scenario(self, scenario_runner, temp_dir):
        """Test loading a scenario from JSON."""
        scenario_file = temp_dir / "test_scenario.json"
        scenario_data = {
            "name": "Test Scenario",
            "description": "A test scenario",
            "initial_idea": "Test idea",
            "conversation": [
                {
                    "user_input": "Create a landing page",
                    "expected_output_contains": ["landing", "page"],
                    "expected_sections": ["hero"],
                    "skip_validation": False
                }
            ],
            "expected_final_output": {
                "sections": ["hero", "features"],
                "required_elements": ["<!DOCTYPE html>"]
            }
        }

        with open(scenario_file, 'w') as f:
            json.dump(scenario_data, f)

        scenario = scenario_runner.load_scenario(str(scenario_file))
        assert scenario.name == "Test Scenario"
        assert scenario.initial_idea == "Test idea"
        assert len(scenario.conversation) == 1

    def test_validate_output(self, scenario_runner, sample_scenario, temp_dir):
        """Test output validation."""
        # Create a test HTML file
        html_file = temp_dir / "test.html"
        html_content = """<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <section class="hero">Hero content</section>
            <section class="features">Features content</section>
            <section class="testimonials">Testimonials content</section>
        </body>
        </html>"""

        with open(html_file, 'w') as f:
            f.write(html_content)

        passed, errors = scenario_runner.validate_output(str(html_file), sample_scenario)
        assert passed is True
        assert len(errors) == 0

        # Test with missing sections
        html_content_missing = """<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <section class="hero">Hero content</section>
        </body>
        </html>"""

        with open(html_file, 'w') as f:
            f.write(html_content_missing)

        passed, errors = scenario_runner.validate_output(str(html_file), sample_scenario)
        assert passed is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_execute_scenario_mock(self, scenario_runner, sample_scenario, mock_crew_response):
        """Test scenario execution with mocked crew."""
        with patch.object(LandingPageCrew, 'run') as mock_run:
            mock_run.return_value = {
                "success": True,
                "output_file": "/tmp/test.html",
                "execution_results": {}
            }

            result = await scenario_runner.execute_scenario(sample_scenario)

            assert result.scenario_name == sample_scenario.name
            assert result.execution_success is True
            assert result.output_file == "/tmp/test.html"

    @pytest.mark.asyncio
    async def test_run_scenario(self, scenario_runner, sample_scenario):
        """Test running a complete scenario."""
        with patch.object(scenario_runner, 'execute_scenario') as mock_execute:
            mock_execute.return_value = Mock(
                scenario_name=sample_scenario.name,
                execution_success=True,
                output_file="/tmp/test.html",
                validation_passed=True,
                validation_errors=[],
                execution_time_ms=1000,
                raw_output={}
            )

            report = await scenario_runner.run_scenario(sample_scenario)

            assert report.scenario_name == sample_scenario.name
            assert report.execution_success is True
            assert report.output_file == "/tmp/test.html"

    def test_save_report(self, scenario_runner, temp_dir):
        """Test saving a scenario report."""
        from src.runner import ScenarioReport

        report = ScenarioReport(
            scenario_name="Test",
            description="Test report",
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T00:01:00",
            execution_success=True,
            output_file="/tmp/test.html",
            validation_results={"passed": True, "errors": []},
            execution_time_ms=60000
        )

        report_file = temp_dir / "test_report.json"
        scenario_runner.save_report(report, str(report_file))

        assert report_file.exists()
        with open(report_file) as f:
            loaded = json.load(f)
        assert loaded["scenario_name"] == "Test"
        assert loaded["execution_success"] is True


class TestScenarioFiles:
    """Test actual scenario JSON files."""

    @pytest.mark.parametrize("scenario_file", [
        "simple_landing.json",
        "saas_landing.json",
        "portfolio_landing.json"
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
        assert "initial_idea" in data
        assert "conversation" in data
        assert len(data["conversation"]) > 0

        # Check conversation structure
        for turn in data["conversation"]:
            assert "user_input" in turn
            # Optional fields are checked if present
            if "expected_output_contains" in turn:
                assert isinstance(turn["expected_output_contains"], list)
            if "expected_sections" in turn:
                assert isinstance(turn["expected_sections"], list)

    def test_all_scenarios_loadable(self, scenario_runner, scenario_files):
        """Test that all scenario files can be loaded."""
        for scenario_file in scenario_files:
            scenario = scenario_runner.load_scenario(str(scenario_file))
            assert scenario.name is not None
            assert scenario.initial_idea is not None
            assert len(scenario.conversation) > 0


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.fixture
    def real_env(self):
        """Setup real environment for integration tests - do not use mock_env."""
        # Check if real API key is available (not the mocked one)
        real_api_key = os.environ.get("OPENAI_API_KEY")
        if not real_api_key or real_api_key == "test-api-key":
            pytest.skip("Requires valid OPENAI_API_KEY environment variable for integration test")
        return {"OPENAI_API_KEY": real_api_key}

    @pytest.mark.integration
    def test_simple_idea_execution(self, real_env, temp_dir, sample_idea):
        """Test a simple idea execution with real API calls."""
        # Create a crew without mock_env to use real API key
        crew = LandingPageCrew(
            model_name="gpt-4",
            verbose=False,
            output_dir=str(temp_dir / "output"),
            workdir=str(temp_dir / "workdir")
        )
        result = crew.run(sample_idea)

        assert result["success"] is True
        assert "output_file" in result
        assert Path(result["output_file"]).exists()

    @pytest.mark.skipif(
        not os.environ.get("RUN_FULL_SCENARIOS"),
        reason="Set RUN_FULL_SCENARIOS=1 to run full scenario tests"
    )
    @pytest.mark.integration
    async def test_full_scenarios(self, scenario_runner, scenario_files):
        """Run all scenarios end-to-end (requires API key and flag)."""
        for scenario_file in scenario_files:
            print(f"\nRunning scenario: {scenario_file.name}")
            scenario = scenario_runner.load_scenario(str(scenario_file))
            report = await scenario_runner.run_scenario(scenario)

            # Save report
            report_file = f"test_report_{scenario_file.stem}.json"
            scenario_runner.save_report(report, report_file)

            # Basic assertions
            assert report.scenario_name is not None
            print(f"Scenario {scenario.name}: Success={report.execution_success}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])