"""Tools for the Code Debug Agent using Stack Exchange."""

import json
import logging
from typing import Optional, List
from google.adk.tools import FunctionTool
from src.services.stackexchange_service import StackExchangeService

logger = logging.getLogger(__name__)


async def search_stack_exchange_for_error(
    error_message: str,
    programming_language: Optional[str],
    framework: Optional[str],
    include_solutions: bool,
    max_results: int
) -> str:
    """Search Stack Exchange for solutions to a specific error message.

    This tool searches Stack Overflow and other Stack Exchange sites for questions
    and answers related to the provided error message. It intelligently extracts
    keywords from the error and returns relevant solutions.

    Args:
        error_message: The error message to search for (e.g., "ImportError: No module named 'pandas'")
        programming_language: Optional language filter (e.g., "python", "javascript", "java")
        framework: Optional framework filter (e.g., "django", "react", "spring")
        include_solutions: Whether to include accepted answers (default: True)
        max_results: Maximum number of results to return (default: 5)

    Returns:
        JSON string containing search results with questions and their top answers
    """
    try:
        # Handle default values
        if max_results is None:
            max_results = 5
        if include_solutions is None:
            include_solutions = True

        async with StackExchangeService() as service:
            results = await service.search_similar_errors(
                error_message=error_message,
                programming_language=programming_language,
                framework=framework,
                limit=max_results
            )

            if not results.get("success"):
                return json.dumps({
                    "error": results.get("error", "Search failed"),
                    "message": "Failed to search Stack Exchange",
                    "results": []
                }, indent=2)

            # Format results for the agent
            formatted_results = []
            for item in results.get("results", []):
                formatted_item = {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "score": item.get("score"),
                    "has_accepted_answer": item.get("has_accepted_answer"),
                    "tags": item.get("tags"),
                    "question_summary": item.get("body", "")[:500],  # First 500 chars
                }

                # Include top answer if available and requested
                if include_solutions and item.get("top_answer"):
                    answer = item["top_answer"]
                    formatted_item["solution"] = {
                        "score": answer.get("score"),
                        "is_accepted": answer.get("is_accepted"),
                        "content": answer.get("body", "")[:1000],  # First 1000 chars
                    }

                formatted_results.append(formatted_item)

            return json.dumps({
                "success": True,
                "query": error_message,
                "language": programming_language,
                "framework": framework,
                "total_results": len(formatted_results),
                "results": formatted_results
            }, indent=2)

    except Exception as e:
        logger.error(f"Error searching Stack Exchange: {e}")
        return json.dumps({
            "error": str(e),
            "message": "An error occurred while searching",
            "results": []
        }, indent=2)


async def search_stack_exchange_general(
    query: str,
    site: Optional[str],
    tags: Optional[List[str]],
    sort_by: Optional[str],
    has_accepted_answer: Optional[bool],
    max_results: Optional[int]
) -> str:
    """General search on Stack Exchange for programming questions.

    This tool performs a general search on Stack Exchange sites for any
    programming-related query, not limited to error messages.

    Args:
        query: Search query (e.g., "how to use async await python")
        site: Stack Exchange site to search (default: "stackoverflow")
        tags: Optional list of tags to filter by (e.g., ["python", "async"])
        sort_by: Sort results by "relevance", "votes", "activity", or "creation"
        has_accepted_answer: Filter for questions with accepted answers
        max_results: Maximum number of results to return (default: 10)

    Returns:
        JSON string containing search results
    """
    try:
        # Handle default values
        if site is None:
            site = "stackoverflow"
        if sort_by is None:
            sort_by = "relevance"
        if max_results is None:
            max_results = 10

        async with StackExchangeService() as service:
            results = await service.search_questions(
                query=query,
                site=site,
                tagged=tags,
                sort=sort_by,
                pagesize=max_results,
                accepted=has_accepted_answer
            )

            if not results.get("success"):
                return json.dumps({
                    "error": results.get("error", "Search failed"),
                    "message": "Failed to search Stack Exchange",
                    "results": []
                }, indent=2)

            # Format results
            formatted_results = []
            for item in results.get("results", []):
                formatted_item = {
                    "question_id": item.get("question_id"),
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "score": item.get("score"),
                    "answer_count": item.get("answer_count"),
                    "is_answered": item.get("is_answered"),
                    "has_accepted_answer": item.get("has_accepted_answer"),
                    "tags": item.get("tags"),
                    "view_count": item.get("view_count"),
                    "creation_date": item.get("creation_date"),
                    "body_preview": item.get("body", "")[:300] + "..." if len(item.get("body", "")) > 300 else item.get("body", ""),
                }
                formatted_results.append(formatted_item)

            return json.dumps({
                "success": True,
                "query": query,
                "site": site,
                "tags": tags,
                "sort_by": sort_by,
                "total_results": results.get("total_results", 0),
                "has_more": results.get("has_more", False),
                "results": formatted_results
            }, indent=2)

    except Exception as e:
        logger.error(f"Error searching Stack Exchange: {e}")
        return json.dumps({
            "error": str(e),
            "message": "An error occurred while searching",
            "results": []
        }, indent=2)


async def get_stack_exchange_answers(
    question_id: int,
    site: Optional[str],
    max_answers: Optional[int]
) -> str:
    """Get detailed answers for a specific Stack Exchange question.

    This tool retrieves the full answers for a specific question ID from
    Stack Exchange, useful when you need more details about solutions.

    Args:
        question_id: The question ID to get answers for
        site: Stack Exchange site (default: "stackoverflow")
        max_answers: Maximum number of answers to retrieve (default: 3)

    Returns:
        JSON string containing the answers with full content
    """
    try:
        # Handle default values
        if site is None:
            site = "stackoverflow"
        if max_answers is None:
            max_answers = 3

        async with StackExchangeService() as service:
            results = await service.get_answers(
                question_id=question_id,
                site=site,
                pagesize=max_answers
            )

            if not results.get("success"):
                return json.dumps({
                    "error": results.get("error", "Failed to get answers"),
                    "message": f"Failed to retrieve answers for question {question_id}",
                    "answers": []
                }, indent=2)

            # Format answers
            formatted_answers = []
            for answer in results.get("answers", []):
                formatted_answers.append({
                    "answer_id": answer.get("answer_id"),
                    "score": answer.get("score"),
                    "is_accepted": answer.get("is_accepted"),
                    "content": answer.get("body"),
                    "creation_date": answer.get("creation_date"),
                })

            return json.dumps({
                "success": True,
                "question_id": question_id,
                "site": site,
                "total_answers": len(formatted_answers),
                "answers": formatted_answers
            }, indent=2)

    except Exception as e:
        logger.error(f"Error getting answers: {e}")
        return json.dumps({
            "error": str(e),
            "message": "An error occurred while retrieving answers",
            "answers": []
        }, indent=2)


async def analyze_error_and_suggest_fix(
    error_message: str,
    code_context: Optional[str],
    file_type: Optional[str],
    search_limit: Optional[int]
) -> str:
    """Analyze an error message and suggest fixes based on Stack Exchange solutions.

    This comprehensive tool analyzes an error message, searches for relevant solutions,
    and provides actionable fix suggestions based on community-validated answers.

    Args:
        error_message: The full error message or stack trace
        code_context: Optional code snippet where the error occurred
        file_type: Optional file extension or language (e.g., "py", "js", "java")
        search_limit: Number of solutions to analyze (default: 3)

    Returns:
        JSON string containing error analysis and suggested fixes
    """
    try:
        # Handle default values
        if search_limit is None:
            search_limit = 3

        # Determine programming language from file type
        language_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "cpp": "c++",
            "cs": "c#",
            "rb": "ruby",
            "go": "go",
            "rs": "rust",
            "php": "php",
            "swift": "swift",
            "kt": "kotlin",
        }

        programming_language = None
        if file_type:
            file_ext = file_type.lower().replace(".", "")
            programming_language = language_map.get(file_ext)

        # Search for similar errors
        async with StackExchangeService() as service:
            results = await service.search_similar_errors(
                error_message=error_message,
                programming_language=programming_language,
                limit=search_limit
            )

            if not results.get("success") or not results.get("results"):
                return json.dumps({
                    "error_message": error_message,
                    "analysis": "No relevant solutions found on Stack Exchange",
                    "suggested_fixes": [],
                    "related_links": []
                }, indent=2)

            # Analyze results and compile fixes
            suggested_fixes = []
            related_links = []

            for idx, result in enumerate(results.get("results", []), 1):
                fix_entry = {
                    "solution_rank": idx,
                    "relevance_score": result.get("score", 0),
                    "question_title": result.get("title"),
                    "has_accepted_answer": result.get("has_accepted_answer"),
                }

                # Add the solution if available
                if result.get("top_answer"):
                    answer = result["top_answer"]
                    fix_entry["fix_description"] = answer.get("body", "")[:500]
                    fix_entry["is_accepted_solution"] = answer.get("is_accepted", False)
                    fix_entry["solution_score"] = answer.get("score", 0)

                suggested_fixes.append(fix_entry)
                related_links.append({
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "tags": result.get("tags", [])
                })

            # Compile analysis
            analysis = {
                "error_message": error_message,
                "detected_language": programming_language,
                "error_type": "Generic Error",  # Could be enhanced with pattern matching
                "analysis": f"Found {len(suggested_fixes)} potential solutions on Stack Exchange",
                "suggested_fixes": suggested_fixes,
                "related_links": related_links,
                "search_metadata": {
                    "total_results": results.get("total_results", 0),
                    "has_more": results.get("has_more", False),
                }
            }

            # Add code context if provided
            if code_context:
                analysis["code_context"] = code_context[:500]  # Limit context size

            return json.dumps(analysis, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing error message: {e}")
        return json.dumps({
            "error": str(e),
            "error_message": error_message,
            "analysis": "Failed to analyze error",
            "suggested_fixes": []
        }, indent=2)


# Create FunctionTool instances for Google ADK
# FunctionTool automatically extracts the name and description from the function docstring
search_error_tool = FunctionTool(func=search_stack_exchange_for_error)
search_general_tool = FunctionTool(func=search_stack_exchange_general)
get_answers_tool = FunctionTool(func=get_stack_exchange_answers)
analyze_error_tool = FunctionTool(func=analyze_error_and_suggest_fix)

# Export all tools
DEBUG_TOOLS = [
    search_error_tool,
    search_general_tool,
    get_answers_tool,
    analyze_error_tool,
]