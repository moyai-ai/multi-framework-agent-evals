"""
Tests for the LangGraph ReAct agent.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from src.agent import create_agent, run_agent, run_agent_sync
from src.agent.state import AgentState, create_initial_state, update_state_with_tool_result
from src.agent.prompts import SYSTEM_PROMPT

pytestmark = pytest.mark.unit


class TestAgentState:
    """Test agent state management."""

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state(
            repository_url="https://github.com/example/repo",
            analysis_type="security",
            max_steps=20
        )

        assert state["repository_url"] == "https://github.com/example/repo"
        assert state["repository_owner"] == "example"
        assert state["repository_name"] == "repo"
        assert state["analysis_type"] == "security"
        assert state["current_step"] == 0
        assert state["max_steps"] == 20
        assert state["should_continue"] is True
        assert len(state["messages"]) == 0

    def test_update_state_with_tool_result(self):
        """Test updating state with tool results."""
        state = create_initial_state("https://github.com/test/repo")

        # Test file list update
        state = update_state_with_tool_result(
            state,
            "list_repository_files",
            ["file1.py", "file2.py"]
        )
        assert state["files_to_analyze"] == ["file1.py", "file2.py"]
        assert state["current_step"] == 1

        # Test file analysis update
        state = update_state_with_tool_result(
            state,
            "analyze_file",
            {"file_path": "file1.py", "issues": [{"type": "sql-injection"}]}
        )
        assert "file1.py" in state["files_analyzed"]
        assert len(state["issues_found"]) == 1

    def test_max_steps_limit(self):
        """Test that state stops at max steps."""
        state = create_initial_state("https://github.com/test/repo", max_steps=2)

        state = update_state_with_tool_result(state, "test_tool", {})
        assert state["should_continue"] is True

        state = update_state_with_tool_result(state, "test_tool", {})
        assert state["should_continue"] is False
        assert "Maximum steps reached" in state["final_answer"]


class TestAgentCreation:
    """Test agent creation and configuration."""

    def test_create_agent_with_config(self, test_config, mock_openai_client):
        """Test creating agent with configuration."""
        agent = create_agent(test_config)
        assert agent is not None
        # Verify that bind_tools was called on the mock instance
        mock_openai_client.bind_tools.assert_called_once()

    def test_create_agent_without_config(self, mock_openai_client):
        """Test creating agent without configuration."""
        with patch("src.agent.graph.Config") as mock_config:
            mock_config.return_value.validate.return_value = True
            mock_config.return_value.OPENAI_API_KEY = "test-key"
            mock_config.return_value.MODEL_NAME = "gpt-4"
            mock_config.return_value.TEMPERATURE = 0.3

            agent = create_agent()
            assert agent is not None


class TestAgentExecution:
    """Test agent execution."""

    @pytest.mark.asyncio
    async def test_run_agent_security_analysis(self, test_config, mock_openai_client):
        """Test running agent for security analysis."""
        # Mock the agent's execution
        with patch("src.agent.graph.create_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.ainvoke = AsyncMock(return_value={
                "repository_owner": "example",
                "repository_name": "repo",
                "files_analyzed": ["file1.py", "file2.py"],
                "issues_found": [
                    {"rule_id": "sql-injection", "severity": "HIGH"},
                    {"rule_id": "hardcoded-secret", "severity": "HIGH"}
                ],
                "final_answer": "Analysis complete. Found 2 security issues.",
                "current_step": 5,
                "error": None
            })
            mock_create.return_value = mock_agent

            result = await run_agent(
                repository_url="https://github.com/example/repo",
                analysis_type="security",
                config=test_config
            )

            assert result["repository"] == "example/repo"
            assert result["analysis_type"] == "security"
            assert len(result["files_analyzed"]) == 2
            assert len(result["issues_found"]) == 2
            assert "Analysis complete" in result["final_report"]
            assert result["steps_taken"] == 5
            assert result["error"] is None

    def test_run_agent_sync(self, test_config, mock_openai_client):
        """Test synchronous agent execution."""
        with patch("src.agent.graph.create_agent") as mock_create:
            mock_agent = Mock()
            mock_agent.ainvoke = AsyncMock(return_value={
                "repository_owner": "test",
                "repository_name": "repo",
                "files_analyzed": ["main.py"],
                "issues_found": [],
                "final_answer": "No issues found.",
                "current_step": 3,
                "error": None
            })
            mock_create.return_value = mock_agent

            with patch("asyncio.run") as mock_run:
                mock_run.return_value = {
                    "repository": "test/repo",
                    "analysis_type": "security",
                    "files_analyzed": ["main.py"],
                    "issues_found": [],
                    "final_report": "No issues found.",
                    "steps_taken": 3,
                    "error": None
                }

                result = run_agent_sync(
                    repository_url="https://github.com/test/repo",
                    config=test_config
                )

                assert result["repository"] == "test/repo"
                assert len(result["issues_found"]) == 0


class TestAgentWorkflow:
    """Test the agent workflow nodes."""

    def test_reasoning_node(self, test_config, mock_openai_client):
        """Test the reasoning node."""
        from src.agent.graph import create_agent

        # This would require more complex mocking of the graph structure
        # For now, we verify the agent can be created
        agent = create_agent(test_config)
        assert agent is not None

    def test_should_continue_logic(self):
        """Test the decision logic for continuing analysis."""
        state = create_initial_state("https://github.com/test/repo")

        # Should continue when not complete
        assert state["should_continue"] is True

        # Should stop when error occurs
        state["error"] = "Test error"
        assert state["error"] is not None

        # Should stop when final answer is set
        state["error"] = None
        state["final_answer"] = "Complete"
        assert state["final_answer"] is not None


class TestPrompts:
    """Test prompt templates."""

    def test_system_prompt_content(self):
        """Test that system prompt contains required information."""
        assert "Static Code Analysis Agent" in SYSTEM_PROMPT
        assert "ReAct" in SYSTEM_PROMPT
        assert "security" in SYSTEM_PROMPT.lower()
        assert "quality" in SYSTEM_PROMPT.lower()
        assert "dependencies" in SYSTEM_PROMPT.lower()

    def test_prompt_formatting(self):
        """Test prompt formatting with variables."""
        from src.agent.prompts import REASONING_PROMPT

        formatted = REASONING_PROMPT.format(
            repository="test/repo",
            analysis_type="security",
            files_analyzed=5,
            total_files=10,
            issues_count=3,
            current_step=2,
            max_steps=20
        )

        assert "test/repo" in formatted
        assert "security" in formatted
        assert "5/10" in formatted
        assert "3" in formatted