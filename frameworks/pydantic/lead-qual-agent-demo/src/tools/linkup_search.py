"""Linkup.so web search tool for lead qualification."""

import os
from typing import List, Dict, Any, Optional
from contextvars import ContextVar
import httpx
from pydantic import BaseModel, Field, PrivateAttr
from pydantic_ai import Tool
import asyncio
import json
import time
from collections import deque

from ..agent.models import SearchResult

# Context variable to store deps passed from agent.run()
_deps_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('deps', default=None)


# Global rate limiter to track requests across all instances
class RateLimiter:
    """Rate limiter for Linkup API requests."""
    
    def __init__(
        self,
        max_requests: int = 50,
        request_window: int = 60,  # 60 second window
        max_concurrent: int = 5,   # Max concurrent requests
        min_delay: float = 0.5     # Minimum delay between requests in seconds
    ):
        self.max_requests = max_requests
        self.request_window = request_window
        self.max_concurrent = max_concurrent
        self.min_delay = min_delay
        self.request_times = deque()  # Track request timestamps
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.last_request_time = 0
        self.request_count = 0
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        # Wait for semaphore first (concurrency limit)
        await self.semaphore.acquire()
        
        try:
            # Check minimum delay outside the lock (no need to hold lock while sleeping)
            async with self.lock:
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_delay:
                await asyncio.sleep(self.min_delay - time_since_last)
            
            # Now acquire lock for the actual limit check and recording
            async with self.lock:
                current_time = time.time()
                # Clean up old requests outside the window
                while self.request_times and current_time - self.request_times[0] > self.request_window:
                    self.request_times.popleft()
                    self.request_count -= 1
                
                # Check if we've hit the request limit
                if len(self.request_times) >= self.max_requests:
                    # Release semaphore before raising
                    self.semaphore.release()
                    raise ValueError(f"The next request would exceed the request_limit of {self.max_requests}")
                
                # Record this request
                self.last_request_time = current_time
                self.request_times.append(current_time)
                self.request_count += 1
        except Exception:
            # If anything fails after acquiring semaphore, release it
            self.semaphore.release()
            raise
    
    def release(self):
        """Release the semaphore after request completes."""
        self.semaphore.release()


# Global rate limiter instance
_global_rate_limiter = RateLimiter(max_requests=50, max_concurrent=3, min_delay=0.5)


class LinkupSearchTool(BaseModel):
    """Tool for searching the web using Linkup.so API."""

    api_key: Optional[str] = Field(None, description="Linkup API key")
    base_url: str = Field(
        default="https://api.linkup.so/v1",
        description="Linkup API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Rate limiter as a private attribute (not part of Pydantic schema)
    _rate_limiter: RateLimiter = PrivateAttr()

    def __init__(self, **data):
        # Extract rate_limiter from data if provided, but don't pass it to Pydantic
        rate_limiter = data.pop("rate_limiter", None)
        super().__init__(**data)
        if not self.api_key:
            self.api_key = os.getenv("LINKUP_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Linkup API key not provided. Set LINKUP_API_KEY environment variable or pass api_key parameter."
            )
        # Use provided rate limiter or default to global one
        self._rate_limiter = rate_limiter or _global_rate_limiter
    
    @property
    def rate_limiter(self) -> RateLimiter:
        """Get the rate limiter instance."""
        return self._rate_limiter

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
        # Acquire rate limiter permission
        acquired = False
        try:
            await self.rate_limiter.acquire()
            acquired = True
        except ValueError as e:
            # If we've hit the limit, return empty results (semaphore not acquired)
            print(f"Rate limit exceeded: {e}")
            return []
        
        try:
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
                    # Handle rate limit errors specifically
                    if e.response.status_code == 429:
                        print(f"Rate limited by API (429): Waiting before retry...")
                        await asyncio.sleep(2)  # Wait before potential retry
                    else:
                        print(f"HTTP error occurred: {e}")
                    return []
                except Exception as e:
                    print(f"Error during Linkup search: {e}")
                    return []
        finally:
            # Only release if we successfully acquired
            if acquired:
                self.rate_limiter.release()

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
        # Acquire rate limiter permission
        acquired = False
        try:
            await self.rate_limiter.acquire()
            acquired = True
        except ValueError as e:
            # If we've hit the limit, return empty results (semaphore not acquired)
            print(f"Rate limit exceeded: {e}")
            return {"summary": "", "results": [], "query": query}
        
        try:
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
                    # Handle rate limit errors specifically
                    if e.response.status_code == 429:
                        print(f"Rate limited by API (429): Waiting before retry...")
                        await asyncio.sleep(2)  # Wait before potential retry
                    else:
                        print(f"HTTP error occurred: {e}")
                    return {"summary": "", "results": [], "query": query}
                except Exception as e:
                    print(f"Error during Linkup search: {e}")
                    return {"summary": "", "results": [], "query": query}
        finally:
            # Only release if we successfully acquired
            if acquired:
                self.rate_limiter.release()


# Create the Pydantic AI tool function
async def search_linkup(
    query: str,
    search_type: str = "standard",
    deps: Optional[Dict[str, Any]] = None
) -> str:
    """
    Search the web using Linkup.so to gather information about a person or company.

    Args:
        query: The search query (e.g., "John Doe CEO TechCorp LinkedIn")
        search_type: Type of search - 'standard' for quick results, 'summary' for summarized content
        deps: Context dictionary containing dependencies (e.g., {"search_tool": LinkupSearchTool()})
             Can be passed explicitly (for tests) or accessed from context (for Pydantic AI)

    Returns:
        Formatted string with search results or summary
    """
    # Get search tool from deps if provided, or from context, or create a new one
    search_tool = None
    
    # First check if deps was passed explicitly (for tests)
    if deps:
        search_tool = deps.get("search_tool")
    
    # If not, try to get from context variable (for Pydantic AI)
    if search_tool is None:
        try:
            context_deps = _deps_context.get()
            if context_deps:
                search_tool = context_deps.get("search_tool")
        except LookupError:
            pass
    
    # If still None, create a new one
    if search_tool is None:
        try:
            search_tool = LinkupSearchTool()
        except Exception as e:
            # If API key is missing, return a mock response for testing
            return f"[Search unavailable: {e}] Mock results for query: {query}"

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