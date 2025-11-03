"""Tests for the Linkup search tool."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from src.tools.linkup_search import LinkupSearchTool, search_linkup
from src.agent.models import SearchResult


class TestLinkupSearchTool:
    """Test the LinkupSearchTool class."""

    def test_initialization_with_api_key(self):
        """Test initialization with provided API key."""
        tool = LinkupSearchTool(api_key="test-api-key")
        assert tool.api_key == "test-api-key"
        assert tool.base_url == "https://api.linkup.so/v1"
        assert tool.timeout == 30

    def test_initialization_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict('os.environ', {'LINKUP_API_KEY': 'env-api-key'}):
            tool = LinkupSearchTool()
            assert tool.api_key == "env-api-key"

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Linkup API key not provided"):
                LinkupSearchTool()

    def test_custom_base_url_and_timeout(self):
        """Test initialization with custom base URL and timeout."""
        tool = LinkupSearchTool(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60
        )
        assert tool.base_url == "https://custom.api.com"
        assert tool.timeout == 60

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search operation."""
        tool = LinkupSearchTool(api_key="test-key")

        mock_response = {
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example1.com",
                    "snippet": "This is result 1"
                },
                {
                    "title": "Result 2",
                    "url": "https://example2.com",
                    "snippet": "This is result 2"
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response_obj = Mock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_client.post.return_value = mock_response_obj

            results = await tool.search("test query", num_results=2)

            assert len(results) == 2
            assert isinstance(results[0], SearchResult)
            assert results[0].title == "Result 1"
            assert results[0].url == "https://example1.com"
            assert results[0].snippet == "This is result 1"
            assert results[0].source == "linkup"

            # Verify API call
            mock_client.post.assert_called_once_with(
                "https://api.linkup.so/v1/search",
                headers={
                    "Authorization": "Bearer test-key",
                    "Content-Type": "application/json"
                },
                json={
                    "q": "test query",
                    "depth": "standard",
                    "outputType": "searchResults"
                }
            )

    @pytest.mark.asyncio
    async def test_search_with_deep_depth(self):
        """Test search with deep depth parameter."""
        tool = LinkupSearchTool(api_key="test-key")

        mock_response = {"results": []}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response_obj = Mock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_client.post.return_value = mock_response_obj

            results = await tool.search("test query", depth="deep")

            # Verify deep depth was passed
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["depth"] == "deep"

    @pytest.mark.asyncio
    async def test_search_http_error(self):
        """Test search handles HTTP errors gracefully."""
        tool = LinkupSearchTool(api_key="test-key")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response_obj = Mock()
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock()
            )
            mock_client.post.return_value = mock_response_obj

            results = await tool.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_general_exception(self):
        """Test search handles general exceptions gracefully."""
        tool = LinkupSearchTool(api_key="test-key")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Network error")

            results = await tool.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_with_summary_success(self):
        """Test search with summary operation."""
        tool = LinkupSearchTool(api_key="test-key")

        mock_response = {
            "summary": "This is a summary of the search results",
            "links": [
                {
                    "title": "Link 1",
                    "url": "https://example1.com",
                    "snippet": "Snippet 1"
                },
                {
                    "title": "Link 2",
                    "url": "https://example2.com",
                    "snippet": "Snippet 2"
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response_obj = Mock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_client.post.return_value = mock_response_obj

            result = await tool.search_with_summary("test query", num_results=2)

            assert result["summary"] == "This is a summary of the search results"
            assert len(result["results"]) == 2
            assert result["query"] == "test query"
            assert isinstance(result["results"][0], SearchResult)

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["outputType"] == "summaryWithLinks"

    @pytest.mark.asyncio
    async def test_search_with_summary_error(self):
        """Test search with summary handles errors."""
        tool = LinkupSearchTool(api_key="test-key")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("API error")

            result = await tool.search_with_summary("test query")

            assert result["summary"] == ""
            assert result["results"] == []
            assert result["query"] == "test query"

    @pytest.mark.asyncio
    async def test_search_linkup_function_standard(self):
        """Test the search_linkup function with standard search."""
        mock_tool = Mock(spec=LinkupSearchTool)
        mock_tool.search = AsyncMock(return_value=[
            SearchResult(
                title="Result 1",
                url="https://example.com",
                snippet="Test snippet",
                source="linkup"
            )
        ])

        mock_ctx = {"search_tool": mock_tool}

        result = await search_linkup(mock_ctx, "test query", "standard")

        assert "Search results for 'test query'" in result
        assert "Result 1" in result
        assert "https://example.com" in result
        assert "Test snippet" in result

        mock_tool.search.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_search_linkup_function_summary(self):
        """Test the search_linkup function with summary search."""
        mock_tool = Mock(spec=LinkupSearchTool)
        mock_tool.search_with_summary = AsyncMock(return_value={
            "summary": "This is a summary",
            "results": [
                SearchResult(
                    title="Result 1",
                    url="https://example.com",
                    snippet="Test",
                    source="linkup"
                )
            ],
            "query": "test query"
        })

        mock_ctx = {"search_tool": mock_tool}

        result = await search_linkup(mock_ctx, "test query", "summary")

        assert "Summary for 'test query'" in result
        assert "This is a summary" in result
        assert "Sources:" in result
        assert "Result 1: https://example.com" in result

        mock_tool.search_with_summary.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_search_linkup_function_no_results(self):
        """Test search_linkup function when no results are found."""
        mock_tool = Mock(spec=LinkupSearchTool)
        mock_tool.search = AsyncMock(return_value=[])

        mock_ctx = {"search_tool": mock_tool}

        result = await search_linkup(mock_ctx, "test query", "standard")

        assert "No results found for query: test query" in result

    @pytest.mark.asyncio
    async def test_search_linkup_function_creates_tool(self):
        """Test search_linkup creates tool if not in context."""
        with patch.dict('os.environ', {'LINKUP_API_KEY': 'test-key'}):
            with patch('src.tools.linkup_search.LinkupSearchTool') as mock_tool_class:
                mock_tool = Mock(spec=LinkupSearchTool)
                mock_tool.search = AsyncMock(return_value=[])
                mock_tool_class.return_value = mock_tool

                mock_ctx = {}  # No search_tool in context

                result = await search_linkup(mock_ctx, "test query", "standard")

                mock_tool_class.assert_called_once()
                mock_tool.search.assert_called_once_with("test query")