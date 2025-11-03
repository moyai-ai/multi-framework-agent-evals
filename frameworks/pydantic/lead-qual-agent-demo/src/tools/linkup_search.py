"""Linkup.so web search tool for lead qualification."""

import os
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Tool
import asyncio
import json

from ..agent.models import SearchResult


class LinkupSearchTool(BaseModel):
    """Tool for searching the web using Linkup.so API."""

    api_key: Optional[str] = Field(None, description="Linkup API key")
    base_url: str = Field(
        default="https://api.linkup.so/v1",
        description="Linkup API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.api_key:
            self.api_key = os.getenv("LINKUP_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Linkup API key not provided. Set LINKUP_API_KEY environment variable or pass api_key parameter."
            )

    async def search(
        self,
        query: str,
        num_results: int = 5,
        depth: str = "standard"
    ) -> List[SearchResult]:
        """
        Search the web using Linkup.so API.

        Args:
            query: Search query string
            num_results: Number of results to return (default: 5)
            depth: Search depth - 'standard' or 'deep' (default: 'standard')

        Returns:
            List of SearchResult objects
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "depth": depth,
                        "outputType": "searchResults"
                    }
                )
                response.raise_for_status()

                data = response.json()
                results = []

                # Parse Linkup response format
                if "results" in data:
                    for item in data["results"][:num_results]:
                        results.append(
                            SearchResult(
                                title=item.get("title", ""),
                                url=item.get("url", ""),
                                snippet=item.get("snippet", item.get("content", ""))[:500],
                                source="linkup"
                            )
                        )

                return results

            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e}")
                return []
            except Exception as e:
                print(f"Error during Linkup search: {e}")
                return []

    async def search_with_summary(
        self,
        query: str,
        num_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search and get a summarized response.

        Args:
            query: Search query string
            num_results: Number of results to include in summary

        Returns:
            Dictionary with search results and summary
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "depth": "standard",
                        "outputType": "summaryWithLinks"
                    }
                )
                response.raise_for_status()

                data = response.json()

                # Extract both summary and results
                summary = data.get("summary", "")
                results = []

                if "links" in data:
                    for item in data["links"][:num_results]:
                        results.append(
                            SearchResult(
                                title=item.get("title", ""),
                                url=item.get("url", ""),
                                snippet=item.get("snippet", "")[:500],
                                source="linkup"
                            )
                        )

                return {
                    "summary": summary,
                    "results": results,
                    "query": query
                }

            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e}")
                return {"summary": "", "results": [], "query": query}
            except Exception as e:
                print(f"Error during Linkup search: {e}")
                return {"summary": "", "results": [], "query": query}


# Create the Pydantic AI tool function
async def search_linkup(
    ctx,
    query: str,
    search_type: str = "standard"
) -> str:
    """
    Search the web using Linkup.so to gather information about a person or company.

    Args:
        query: The search query (e.g., "John Doe CEO TechCorp LinkedIn")
        search_type: Type of search - 'standard' for quick results, 'summary' for summarized content

    Returns:
        Formatted string with search results or summary
    """
    # Get the search tool from context if available
    search_tool = ctx.get("search_tool")
    if not search_tool:
        search_tool = LinkupSearchTool()

    if search_type == "summary":
        result = await search_tool.search_with_summary(query)

        if result["summary"]:
            output = f"Summary for '{query}':\n{result['summary']}\n\nSources:\n"
            for r in result["results"]:
                output += f"- {r.title}: {r.url}\n"
            return output
    else:
        results = await search_tool.search(query)

        if not results:
            return f"No results found for query: {query}"

        output = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. {result.title}\n"
            output += f"   URL: {result.url}\n"
            output += f"   {result.snippet}\n\n"

        return output


# Create the Pydantic AI Tool object
linkup_search_tool = Tool(
    search_linkup,
    name="search_linkup",
    description="""Search the web using Linkup.so API to find information about people, companies, or topics.
    Use 'standard' search for quick results, or 'summary' for AI-summarized content.

    Args:
        query: The search query string
        search_type: Type of search - 'standard' or 'summary' (default: 'standard')"""
)