"""Unit tests for Code Debug Agent."""

import os
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents import (
    debug_agent,
    quick_debug_agent,
    get_agent_by_name,
    get_initial_agent,
    list_agents,
    AGENTS
)
from src.tools import (
    search_stack_exchange_for_error,
    search_stack_exchange_general,
    get_stack_exchange_answers,
    analyze_error_and_suggest_fix,
    DEBUG_TOOLS
)
from src.services.stackexchange_service import StackExchangeService


class TestAgents:
    """Test agent configurations and registry."""

    def test_debug_agent_configuration(self):
        """Test main debug agent configuration."""
        # Get expected model from environment variable or use default
        expected_model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
        
        assert debug_agent is not None
        assert debug_agent.name == 'debug_agent'
        assert debug_agent.model == expected_model
        assert debug_agent.tools == DEBUG_TOOLS
        assert debug_agent.instruction is not None

    def test_quick_debug_agent_configuration(self):
        """Test quick debug agent configuration."""
        assert quick_debug_agent is not None
        assert quick_debug_agent.name == 'quick_debug_agent'
        assert len(quick_debug_agent.tools) == 2  # Only error search and analysis

    def test_get_agent_by_name_exact_match(self):
        """Test getting agent by exact name."""
        agent = get_agent_by_name('debug_agent')
        assert agent == debug_agent

    def test_get_agent_by_name_partial_match(self):
        """Test getting agent by partial name."""
        agent = get_agent_by_name('debug')
        assert agent == debug_agent

    def test_get_agent_by_name_not_found(self):
        """Test getting non-existent agent."""
        agent = get_agent_by_name('nonexistent')
        assert agent is None

    def test_get_initial_agent(self):
        """Test getting the default agent."""
        agent = get_initial_agent()
        assert agent == debug_agent

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) >= 2  # At least debug and quick_debug

        # Check structure
        for agent_info in agents:
            assert 'name' in agent_info
            assert 'model' in agent_info
            assert 'tools_count' in agent_info
            assert 'tools' in agent_info
            assert 'description' in agent_info


class TestTools:
    """Test Stack Exchange tools."""

    @pytest.mark.asyncio
    async def test_search_stack_exchange_for_error(self, sample_stack_exchange_response):
        """Test error search tool."""
        with patch('src.tools.StackExchangeService') as MockService:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.search_similar_errors.return_value = sample_stack_exchange_response
            MockService.return_value = mock_service

            result = await search_stack_exchange_for_error(
                error_message="ImportError: No module named 'pandas'",
                programming_language="python",
                framework=None,
                include_solutions=True,
                max_results=5
            )

            result_data = json.loads(result)
            assert result_data['success'] is True
            assert len(result_data['results']) > 0
            assert result_data['language'] == 'python'

    @pytest.mark.asyncio
    async def test_search_stack_exchange_general(self):
        """Test general search tool."""
        with patch('src.tools.StackExchangeService') as MockService:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.search_questions.return_value = {
                "success": True,
                "results": [
                    {
                        "question_id": 123,
                        "title": "How to use async/await in Python",
                        "score": 10,
                        "tags": ["python", "async"]
                    }
                ]
            }
            MockService.return_value = mock_service

            result = await search_stack_exchange_general(
                query="async await python",
                site="stackoverflow",
                tags=["python"],
                sort_by="relevance",
                has_accepted_answer=None,
                max_results=10
            )

            result_data = json.loads(result)
            assert result_data['success'] is True
            assert len(result_data['results']) > 0

    @pytest.mark.asyncio
    async def test_get_stack_exchange_answers(self):
        """Test answer retrieval tool."""
        with patch('src.tools.StackExchangeService') as MockService:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.get_answers.return_value = {
                "success": True,
                "answers": [
                    {
                        "answer_id": 456,
                        "score": 25,
                        "is_accepted": True,
                        "body": "This is the solution..."
                    }
                ]
            }
            MockService.return_value = mock_service

            result = await get_stack_exchange_answers(
                question_id=12345,
                site="stackoverflow",
                max_answers=3
            )

            result_data = json.loads(result)
            assert result_data['success'] is True
            assert len(result_data['answers']) > 0

    @pytest.mark.asyncio
    async def test_analyze_error_and_suggest_fix(self, sample_stack_exchange_response):
        """Test comprehensive error analysis tool."""
        with patch('src.tools.StackExchangeService') as MockService:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.search_similar_errors.return_value = sample_stack_exchange_response
            MockService.return_value = mock_service

            result = await analyze_error_and_suggest_fix(
                error_message="ImportError: No module named 'pandas'",
                code_context=None,
                file_type="py",
                search_limit=3
            )

            result_data = json.loads(result)
            assert 'error_message' in result_data
            assert 'suggested_fixes' in result_data
            assert len(result_data['suggested_fixes']) > 0
            assert result_data['detected_language'] == 'python'

    def test_debug_tools_list(self):
        """Test that all tools are properly exported."""
        assert len(DEBUG_TOOLS) == 4
        tool_names = [tool.name for tool in DEBUG_TOOLS]
        assert 'search_stack_exchange_for_error' in tool_names
        assert 'search_stack_exchange_general' in tool_names
        assert 'get_stack_exchange_answers' in tool_names
        assert 'analyze_error_and_suggest_fix' in tool_names


class TestStackExchangeService:
    """Test Stack Exchange service wrapper."""

    @pytest.mark.asyncio
    async def test_search_questions(self):
        """Test searching questions."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "question_id": 123,
                        "title": "Test Question",
                        "score": 10,
                        "tags": ["python"],
                        "body": "<p>Question body</p>"
                    }
                ],
                "has_more": False
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            async with StackExchangeService() as service:
                result = await service.search_questions(
                    query="test query",
                    site="stackoverflow"
                )

            assert result['success'] is True
            assert len(result['results']) == 1
            assert result['results'][0]['title'] == "Test Question"

    @pytest.mark.asyncio
    async def test_get_answers(self):
        """Test getting answers for a question."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "answer_id": 456,
                        "score": 15,
                        "is_accepted": True,
                        "body": "<p>Answer body</p>"
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            async with StackExchangeService() as service:
                result = await service.get_answers(
                    question_id=123,
                    site="stackoverflow"
                )

            assert result['success'] is True
            assert len(result['answers']) == 1
            assert result['answers'][0]['is_accepted'] is True

    def test_extract_error_keywords(self):
        """Test keyword extraction from error messages."""
        service = StackExchangeService()

        keywords = service._extract_error_keywords(
            "ImportError: No module named 'pandas'"
        )
        assert "ImportError" in keywords
        assert "pandas" in keywords

        keywords = service._extract_error_keywords(
            "TypeError: Cannot read property 'map' of undefined"
        )
        assert "TypeError" in keywords
        assert "undefined" in keywords

    def test_clean_html(self):
        """Test HTML cleaning."""
        service = StackExchangeService()

        # Test basic HTML removal
        cleaned = service._clean_html("<p>Hello <strong>world</strong></p>")
        assert cleaned == "Hello world"

        # Test code preservation
        cleaned = service._clean_html("<p>Use <code>pip install</code></p>")
        assert "`pip install`" in cleaned

        # Test pre block preservation
        cleaned = service._clean_html("<pre>code block</pre>")
        assert "```" in cleaned


class TestScenarios:
    """Test scenario loading and execution."""

    @pytest.mark.asyncio
    async def test_scenario_loading(self):
        """Test loading scenarios from JSON."""
        from src.runner import ScenarioRunner

        runner = ScenarioRunner()

        # Create a test scenario file
        test_scenarios = {
            "scenarios": [
                {
                    "name": "Test Error",
                    "description": "Test scenario",
                    "error_message": "Test error message",
                    "programming_language": "python",
                    "conversation": [
                        {
                            "user_input": "Test input",
                            "expected_tools": ["search_stack_exchange_for_error"]
                        }
                    ]
                }
            ]
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_scenarios, f)
            temp_path = f.name

        try:
            scenarios = runner.load_scenarios(temp_path)
            assert len(scenarios) == 1
            assert scenarios[0].name == "Test Error"
            assert scenarios[0].programming_language == "python"
            assert len(scenarios[0].conversation) == 1
        finally:
            import os
            os.unlink(temp_path)