"""
State management for the LangGraph ReAct agent.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State for the ReAct agent."""

    # Conversation history
    messages: Annotated[List[Dict[str, Any]], add_messages]

    # Current analysis context
    repository_url: Optional[str]
    repository_owner: Optional[str]
    repository_name: Optional[str]
    analysis_type: str  # security, quality, dependencies

    # Analysis progress
    current_step: int
    max_steps: int
    files_to_analyze: List[str]
    files_analyzed: List[str]

    # Results
    analysis_results: List[Dict[str, Any]]
    issues_found: List[Dict[str, Any]]

    # Control flow
    should_continue: bool
    final_answer: Optional[str]
    error: Optional[str]
    consecutive_no_tool_calls: int  # Track when LLM doesn't make tool calls


def create_initial_state(
    repository_url: str,
    analysis_type: str = "security",
    max_steps: int = 20
) -> AgentState:
    """Create initial agent state."""
    # Parse repository URL
    url = repository_url.replace("https://github.com/", "").replace(".git", "")
    parts = url.split("/")
    owner = parts[0] if len(parts) >= 1 else None
    name = parts[1] if len(parts) >= 2 else None

    return {
        "messages": [],
        "repository_url": repository_url,
        "repository_owner": owner,
        "repository_name": name,
        "analysis_type": analysis_type,
        "current_step": 0,
        "max_steps": max_steps,
        "files_to_analyze": [],
        "files_analyzed": [],
        "analysis_results": [],
        "issues_found": [],
        "should_continue": True,
        "final_answer": None,
        "error": None,
        "consecutive_no_tool_calls": 0
    }


def update_state_with_tool_result(
    state: AgentState,
    tool_name: str,
    result: Any
) -> AgentState:
    """Update state based on tool execution result."""
    state["current_step"] += 1

    # Check if we've reached max steps
    if state["current_step"] >= state["max_steps"]:
        state["should_continue"] = False
        state["final_answer"] = "Analysis stopped: Maximum steps reached"

    # Update state based on tool type
    if tool_name == "list_repository_files":
        if isinstance(result, list):
            state["files_to_analyze"] = result
    elif tool_name == "analyze_file":
        if "file_path" in result:
            state["files_analyzed"].append(result["file_path"])
        if "issues" in result:
            state["issues_found"].extend(result["issues"])
    elif tool_name == "run_opengrep":
        if "results" in result:
            state["analysis_results"].append(result)

    return state


def get_state_summary(state: AgentState) -> Dict[str, Any]:
    """Get a summary of the current state."""
    return {
        "repository": f"{state['repository_owner']}/{state['repository_name']}",
        "analysis_type": state["analysis_type"],
        "progress": {
            "current_step": state["current_step"],
            "max_steps": state["max_steps"],
            "files_to_analyze": len(state["files_to_analyze"]),
            "files_analyzed": len(state["files_analyzed"])
        },
        "results": {
            "issues_found": len(state["issues_found"]),
            "analysis_results": len(state["analysis_results"])
        },
        "status": {
            "should_continue": state["should_continue"],
            "has_error": state["error"] is not None,
            "completed": state["final_answer"] is not None
        }
    }