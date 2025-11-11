"""
LangGraph ReAct Agent implementation for static code analysis with LangSmith tracing.
"""

import json
import os
from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable, Client

from .state import AgentState, create_initial_state, update_state_with_tool_result
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT, FINAL_REPORT_PROMPT
from ..tools import github_tools, opengrep_tools, analysis_tools
from ..context import Config


def create_agent(config: Optional[Config] = None):
    """Create the LangGraph ReAct agent for static code analysis with LangSmith tracing."""
    if config is None:
        config = Config()
        config.validate()

    # Configure LangSmith tracing via environment variables
    # LangSmith automatically traces when LANGSMITH_TRACING=true is set
    if config.LANGSMITH_ENABLED and config.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT
        print(f"✓ LangSmith tracing enabled - Project: {config.LANGSMITH_PROJECT}")
    else:
        print("⚠ LangSmith tracing disabled")

    # Initialize LLM
    llm = ChatOpenAI(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        api_key=config.OPENAI_API_KEY
    )

    # Create tools
    tools = [
        github_tools.fetch_repository_info,
        github_tools.list_repository_files,
        github_tools.get_file_content,
        opengrep_tools.run_opengrep_analysis,
        analysis_tools.analyze_dependencies,
        analysis_tools.summarize_findings
    ]

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Create the graph
    graph = StateGraph(AgentState)

    # Define nodes with @traceable decorator for enhanced observability
    @traceable(name="reasoning-node", run_type="chain")
    async def reasoning_node(state: AgentState) -> AgentState:
        """Node for reasoning about the next action with LangSmith tracing."""
        print(f"\nDEBUG reasoning_node: Step {state['current_step']}/{state['max_steps']}")
        print(f"  Files to analyze: {len(state['files_to_analyze'])}")
        print(f"  Files analyzed: {len(state['files_analyzed'])}")
        print(f"  Issues found: {len(state['issues_found'])}")

        # Check if we should stop
        if state["current_step"] >= state["max_steps"]:
            print("DEBUG: Max steps reached, stopping")
            state["should_continue"] = False
            state["final_answer"] = "Maximum steps reached. Generating final report..."
            return state

        # Check if analysis is complete
        # Analysis is complete when we have:
        # 1. Listed files to analyze
        # 2. Analyzed at least one file
        # 3. Either analyzed all files OR found significant issues (>= 3 files analyzed with issues)
        if state["files_to_analyze"] and state["files_analyzed"]:
            if (len(state["files_analyzed"]) >= len(state["files_to_analyze"]) or
                (len(state["files_analyzed"]) >= 3 and len(state["issues_found"]) > 0)):
                print("DEBUG: Analysis complete based on files analyzed")
                state["should_continue"] = False
                state["final_answer"] = "Analysis complete. Generating final report..."
                return state

        # Create reasoning prompt
        reasoning_context = REASONING_PROMPT.format(
            repository=f"{state['repository_owner']}/{state['repository_name']}",
            analysis_type=state["analysis_type"],
            files_analyzed=len(state["files_analyzed"]),
            total_files=len(state["files_to_analyze"]),
            issues_count=len(state["issues_found"]),
            current_step=state["current_step"],
            max_steps=state["max_steps"]
        )

        # Get LLM reasoning
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(content=reasoning_context)
        ]

        print(f"DEBUG: Calling LLM with {len(messages)} messages...")
        # LLM calls are automatically traced by LangSmith
        response = await llm_with_tools.ainvoke(messages)
        has_tools = hasattr(response, 'tool_calls') and bool(response.tool_calls)
        print(f"DEBUG: LLM response received, has tool calls: {has_tools}")
        if has_tools:
            print(f"  Tool calls: {[tc.get('name', tc) for tc in response.tool_calls]}")
            state["consecutive_no_tool_calls"] = 0  # Reset counter
        else:
            print(f"  Text response: {response.content[:200]}...")
            state["consecutive_no_tool_calls"] += 1
            print(f"  Consecutive non-tool responses: {state['consecutive_no_tool_calls']}")

            # If LLM keeps responding without tool calls, force completion
            if state["consecutive_no_tool_calls"] >= 3:
                print("DEBUG: Too many consecutive non-tool responses, forcing completion")
                state["should_continue"] = False
                state["final_answer"] = "Analysis incomplete: Agent unable to proceed with analysis."

        state["messages"].append(response)
        state["current_step"] += 1

        return state

    @traceable(name="action-node", run_type="tool")
    async def action_node(state: AgentState) -> AgentState:
        """Node for executing tools based on LLM decision."""
        # Get the last message which should contain tool calls
        last_message = state["messages"][-1]

        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            # Execute tool calls - tools are automatically traced by LangSmith
            tool_node = ToolNode(tools)
            result = await tool_node.ainvoke(state)

            # Update state with tool results
            for tool_call in last_message.tool_calls:
                state = update_state_with_tool_result(
                    state,
                    tool_call["name"],
                    tool_call.get("args", {})
                )

            return result

        return state

    @traceable(name="observation-node", run_type="chain")
    async def observation_node(state: AgentState) -> AgentState:
        """Node for observing results and updating state."""
        # Process ALL tool execution results (may be multiple from parallel tool calls)
        tool_messages = [msg for msg in state["messages"] if isinstance(msg, ToolMessage)]

        if not tool_messages:
            return state

        # Process the most recent batch of tool messages
        # Find the index of the last non-tool message to determine the current batch
        last_non_tool_idx = -1
        for i in range(len(state["messages"]) - 1, -1, -1):
            if not isinstance(state["messages"][i], ToolMessage):
                last_non_tool_idx = i
                break

        # Process all tool messages after the last non-tool message
        recent_tool_messages = [msg for msg in state["messages"][last_non_tool_idx + 1:] if isinstance(msg, ToolMessage)]

        print(f"\nDEBUG observation_node: Processing {len(recent_tool_messages)} tool results")

        for tool_message in recent_tool_messages:
            tool_result = tool_message.content

            # Parse and store results based on content
            try:
                result_data = json.loads(tool_result) if isinstance(tool_result, str) else tool_result

                # Handle run_opengrep_analysis results
                if "issues" in result_data:
                    issues = result_data.get("issues", [])

                    if isinstance(issues, list):
                        state["issues_found"].extend(issues)
                        if issues:
                            print(f"  Added {len(issues)} issues from {result_data.get('file_path', 'unknown')}")

                    # Mark file as analyzed - check for file_path at top level
                    if "file_path" in result_data:
                        file_path = result_data["file_path"]
                        if file_path and file_path not in state["files_analyzed"]:
                            state["files_analyzed"].append(file_path)
                            print(f"  ✓ Marked file as analyzed: {file_path}")

                # Handle list_repository_files results
                if "files" in result_data and isinstance(result_data.get("files"), list):
                    # Extract file paths from the files list
                    file_paths = [f.get("path", "") for f in result_data["files"] if isinstance(f, dict)]
                    state["files_to_analyze"] = file_paths
                    print(f"  Found {len(file_paths)} files to analyze")

                # Handle get_file_content results - track that we fetched the file
                if "file_path" in result_data and "content" in result_data:
                    # File content fetched, ready for analysis
                    pass

                if "analysis_complete" in result_data and result_data["analysis_complete"]:
                    state["should_continue"] = False

            except (json.JSONDecodeError, TypeError) as e:
                # Handle non-JSON responses
                print(f"DEBUG: Could not parse tool result as JSON: {e}")
                pass

        print(f"  Total Progress: {len(state['files_analyzed'])}/{len(state['files_to_analyze'])} files, {len(state['issues_found'])} issues")

        return state

    @traceable(name="report-node", run_type="chain")
    async def report_node(state: AgentState) -> AgentState:
        """Node for generating the final report."""
        # Generate summary of findings
        issues_summary = await analysis_tools.summarize_findings.ainvoke(state["issues_found"])

        report_prompt = FINAL_REPORT_PROMPT.format(
            repository=f"{state['repository_owner']}/{state['repository_name']}",
            analysis_type=state["analysis_type"],
            files_analyzed=len(state["files_analyzed"]),
            issues_summary=json.dumps(issues_summary, indent=2)
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=report_prompt)
        ]

        # LLM calls are automatically traced by LangSmith
        response = await llm.ainvoke(messages)
        state["final_answer"] = response.content
        state["should_continue"] = False

        return state

    # Add nodes to graph
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("action", action_node)
    graph.add_node("observation", observation_node)
    graph.add_node("report", report_node)

    # Define edges
    def should_continue(state: AgentState) -> Literal["reasoning", "report", "end"]:
        """Determine the next step in the graph."""
        if state.get("error"):
            return "end"

        if not state["should_continue"]:
            if state["final_answer"]:
                return "end"
            else:
                return "report"

        return "reasoning"

    def has_tool_calls(state: AgentState) -> Literal["action", "observation"]:
        """Check if the last message has tool calls."""
        if state["messages"] and hasattr(state["messages"][-1], 'tool_calls'):
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                return "action"
        return "observation"

    # Add edges
    graph.set_entry_point("reasoning")
    graph.add_conditional_edges("reasoning", has_tool_calls, {
        "action": "action",
        "observation": "observation"
    })
    graph.add_edge("action", "observation")
    graph.add_conditional_edges("observation", should_continue, {
        "reasoning": "reasoning",
        "report": "report",
        "end": END
    })
    graph.add_edge("report", END)

    # Compile the graph
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


@traceable(
    name="static-code-analysis-agent",
    run_type="chain",
    metadata={"agent_type": "langgraph_react"},
)
async def run_agent(
    repository_url: str,
    analysis_type: str = "security",
    config: Optional[Config] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    scenario_name: Optional[str] = None
) -> Dict[str, Any]:
    """Run the ReAct agent for code analysis with LangSmith tracing.

    Args:
        repository_url: The GitHub repository URL to analyze
        analysis_type: Type of analysis (security, quality, dependencies)
        config: Configuration object
        user_id: Optional user identifier for tracking usage per user
        session_id: Optional session identifier for grouping related analyses
        scenario_name: Optional scenario name for test/evaluation tracking

    Returns:
        Analysis results with instrumentation metadata
    """
    if config is None:
        config = Config()

    # Initialize LangSmith client if enabled
    langsmith_client = None
    if config.LANGSMITH_ENABLED and config.LANGSMITH_API_KEY:
        from datetime import datetime

        # Set environment variables for automatic tracing
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT

        # Create client for metadata enrichment
        langsmith_client = Client()

        # Build descriptive trace name
        repo_parts = repository_url.rstrip('/').split('/')
        repo_name = f"{repo_parts[-2]}/{repo_parts[-1]}" if len(repo_parts) >= 2 else "unknown-repo"

        print(f"✓ LangSmith tracing enabled for {repo_name}")

    # Create initial state
    initial_state = create_initial_state(
        repository_url=repository_url,
        analysis_type=analysis_type
    )

    # Create agent
    agent = create_agent(config)

    # Run the agent with tags and metadata via config
    # LangSmith automatically captures this via environment variables
    agent_config = {
        "configurable": {"thread_id": f"analysis_{repository_url}"},
        "recursion_limit": 50,
        "tags": [
            "static-analysis",
            analysis_type,
            "langgraph",
            "production",
        ],
        "metadata": {
            "agent": config.AGENT_NAME,
            "demo_name": config.AGENT_DEMO_NAME,
            "version": config.AGENT_VERSION,
            "scenario": scenario_name,
            "repository_url": repository_url,
            "analysis_type": analysis_type,
            "model": config.MODEL_NAME,
            "temperature": config.TEMPERATURE,
        }
    }

    if scenario_name:
        agent_config["tags"].append(f"scenario:{scenario_name}")

    if user_id:
        agent_config["metadata"]["user_id"] = user_id

    if session_id:
        agent_config["metadata"]["session_id"] = session_id

    final_state = await agent.ainvoke(initial_state, config=agent_config)

    # Calculate severity breakdown
    severity_counts = {}
    for issue in final_state.get("issues_found", []):
        severity = issue.get("severity", "UNKNOWN")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Add status tags based on results
    result_tags = agent_config["tags"].copy()
    if final_state.get("error"):
        result_tags.append("error")
    else:
        result_tags.append("success")

    if severity_counts.get("CRITICAL", 0) > 0:
        result_tags.append("has-critical-issues")
    if severity_counts.get("HIGH", 0) > 0:
        result_tags.append("has-high-issues")

    # Extract and return results with enhanced metadata
    result = {
        "repository": f"{final_state['repository_owner']}/{final_state['repository_name']}",
        "analysis_type": analysis_type,
        "files_analyzed": final_state["files_analyzed"],
        "issues_found": final_state["issues_found"],
        "final_report": final_state.get("final_answer", "Analysis incomplete"),
        "steps_taken": final_state["current_step"],
        "error": final_state.get("error"),
        "metadata": {
            "severity_breakdown": severity_counts,
            "total_files": len(final_state["files_to_analyze"]),
            "files_analyzed_count": len(final_state["files_analyzed"]),
            "issues_count": len(final_state["issues_found"]),
            "tags": result_tags,
        }
    }

    # Log summary for LangSmith trace enrichment
    if langsmith_client:
        print(f"✓ Analysis complete:")
        print(f"  - Files: {len(final_state['files_analyzed'])}/{len(final_state['files_to_analyze'])}")
        print(f"  - Issues: {len(final_state['issues_found'])}")
        print(f"  - Steps: {final_state['current_step']}")
        print(f"  - Tags: {', '.join(result_tags)}")

    return result


def run_agent_sync(
    repository_url: str,
    analysis_type: str = "security",
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for running the agent."""
    import asyncio
    return asyncio.run(run_agent(repository_url, analysis_type, config))
