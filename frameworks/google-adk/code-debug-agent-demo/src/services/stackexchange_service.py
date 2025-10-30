"""StackExchange API service wrapper for debugging assistance."""

import os
import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class StackExchangeService:
    """Service for interacting with Stack Exchange API."""

    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the StackExchange service.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key or os.getenv("STACKEXCHANGE_API_KEY")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def search_questions(
        self,
        query: str,
        site: str = "stackoverflow",
        tagged: Optional[List[str]] = None,
        sort: str = "relevance",
        order: str = "desc",
        pagesize: int = 10,
        accepted: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Search for questions on Stack Exchange.

        Args:
            query: Search query (error message or keywords)
            site: Stack Exchange site (default: stackoverflow)
            tagged: Filter by tags (e.g., ["python", "django"])
            sort: Sort by (relevance, votes, activity, creation)
            order: Order (desc, asc)
            pagesize: Number of results to return
            accepted: Filter for questions with accepted answers

        Returns:
            Dictionary containing search results
        """
        try:
            params = {
                "order": order,
                "sort": sort,
                "q": query,
                "site": site,
                "pagesize": pagesize,
                "filter": "!9Z(-x-Q)8"  # Include body and answers
            }

            if self.api_key:
                params["key"] = self.api_key

            if tagged:
                params["tagged"] = ";".join(tagged)

            if accepted is not None:
                params["accepted"] = "true" if accepted else "false"

            response = await self.client.get(
                f"{self.BASE_URL}/search/advanced",
                params=params
            )
            response.raise_for_status()

            data = response.json()

            # Process and format results
            results = []
            for item in data.get("items", []):
                result = {
                    "question_id": item.get("question_id"),
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "score": item.get("score"),
                    "answer_count": item.get("answer_count"),
                    "is_answered": item.get("is_answered"),
                    "has_accepted_answer": item.get("accepted_answer_id") is not None,
                    "tags": item.get("tags", []),
                    "creation_date": datetime.fromtimestamp(
                        item.get("creation_date", 0)
                    ).isoformat() if item.get("creation_date") else None,
                    "body": self._clean_html(item.get("body", "")),
                    "view_count": item.get("view_count"),
                }
                results.append(result)

            return {
                "success": True,
                "query": query,
                "site": site,
                "total_results": data.get("total", 0),
                "has_more": data.get("has_more", False),
                "results": results,
                "quota_remaining": data.get("quota_remaining"),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching Stack Exchange: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "message": str(e),
                "query": query,
                "results": []
            }
        except Exception as e:
            logger.error(f"Error searching Stack Exchange: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }

    async def get_answers(
        self,
        question_id: int,
        site: str = "stackoverflow",
        sort: str = "votes",
        pagesize: int = 5
    ) -> Dict[str, Any]:
        """Get answers for a specific question.

        Args:
            question_id: The question ID
            site: Stack Exchange site
            sort: Sort by (activity, votes, creation)
            pagesize: Number of answers to return

        Returns:
            Dictionary containing answers
        """
        try:
            params = {
                "order": "desc",
                "sort": sort,
                "site": site,
                "pagesize": pagesize,
                "filter": "!9Z(-x-Q)8"  # Include body
            }

            if self.api_key:
                params["key"] = self.api_key

            response = await self.client.get(
                f"{self.BASE_URL}/questions/{question_id}/answers",
                params=params
            )
            response.raise_for_status()

            data = response.json()

            # Process answers
            answers = []
            for item in data.get("items", []):
                answer = {
                    "answer_id": item.get("answer_id"),
                    "score": item.get("score"),
                    "is_accepted": item.get("is_accepted", False),
                    "body": self._clean_html(item.get("body", "")),
                    "creation_date": datetime.fromtimestamp(
                        item.get("creation_date", 0)
                    ).isoformat() if item.get("creation_date") else None,
                }
                answers.append(answer)

            return {
                "success": True,
                "question_id": question_id,
                "site": site,
                "answers": answers,
                "total_answers": len(answers),
            }

        except Exception as e:
            logger.error(f"Error getting answers: {e}")
            return {
                "success": False,
                "error": str(e),
                "question_id": question_id,
                "answers": []
            }

    async def search_similar_errors(
        self,
        error_message: str,
        programming_language: Optional[str] = None,
        framework: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search for similar error messages with context.

        Args:
            error_message: The error message to search for
            programming_language: Optional language filter
            framework: Optional framework filter
            limit: Maximum number of results

        Returns:
            Dictionary containing similar errors and solutions
        """
        # Extract key error terms
        error_keywords = self._extract_error_keywords(error_message)

        # Build search query
        query = " ".join(error_keywords)

        # Add tags if specified
        tags = []
        if programming_language:
            tags.append(programming_language.lower())
        if framework:
            tags.append(framework.lower())

        # Search with error-specific parameters
        results = await self.search_questions(
            query=query,
            tagged=tags if tags else None,
            sort="relevance",
            pagesize=limit,
            accepted=True  # Prioritize questions with accepted answers
        )

        # For each result, get the top answer if it has one
        if results.get("success") and results.get("results"):
            for question in results["results"]:
                if question.get("has_accepted_answer") or question.get("answer_count", 0) > 0:
                    answers = await self.get_answers(
                        question_id=question["question_id"],
                        pagesize=1  # Get just the top answer
                    )
                    if answers.get("success") and answers.get("answers"):
                        question["top_answer"] = answers["answers"][0]

        return results

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and convert to plain text.

        Args:
            html_content: HTML string to clean

        Returns:
            Cleaned plain text
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Preserve code blocks
        for code in soup.find_all("code"):
            code.string = f"`{code.get_text()}`"

        for pre in soup.find_all("pre"):
            pre.string = f"\n```\n{pre.get_text()}\n```\n"

        # Convert to text
        text = soup.get_text()

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)

        return text

    def _extract_error_keywords(self, error_message: str) -> List[str]:
        """Extract key terms from an error message.

        Args:
            error_message: The error message

        Returns:
            List of keywords
        """
        # Common error patterns to extract
        import re

        keywords = []

        # Extract error types (e.g., TypeError, ImportError)
        error_types = re.findall(r"\b[A-Z][a-z]*Error\b", error_message)
        keywords.extend(error_types)

        # Extract module names
        modules = re.findall(r"'([a-zA-Z_][a-zA-Z0-9_]*)'", error_message)
        keywords.extend(modules[:3])  # Limit to avoid noise

        # Extract key phrases
        if "cannot import" in error_message.lower():
            keywords.append("import error")
        if "no module named" in error_message.lower():
            keywords.append("module not found")
        if "undefined" in error_message.lower():
            keywords.append("undefined")
        if "null" in error_message.lower() or "none" in error_message.lower():
            keywords.append("null pointer")

        # Remove duplicates and return
        return list(dict.fromkeys(keywords))


async def test_service():
    """Test the StackExchange service."""
    async with StackExchangeService() as service:
        # Test search
        results = await service.search_similar_errors(
            error_message="ImportError: No module named 'pandas'",
            programming_language="python",
            limit=3
        )
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(test_service())