"""
LangGraph ReAct Agent implementation for static code analysis with Langfuse tracing.
"""

import json
from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langfuse import get_client, Langfuse
from langfuse.langchain import CallbackHandler

from .state import AgentState, create_initial_state, update_state_with_tool_result
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT, FINAL_REPORT_PROMPT
from ..tools import github_tools, opengrep_tools, analysis_tools
from ..context import Config


def create_agent(config: Optional[Config] = None, langfuse_handler: Optional[CallbackHandler] = None):
    """Create the LangGraph ReAct agent for static code analysis with Langfuse tracing."""
    if config is None:
        config = Config()
        config.validate()

    # Initialize Langfuse handler if enabled and not provided
    if langfuse_handler is None and config.LANGFUSE_ENABLED:
        if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
            # Set environment variables for Langfuse client
            import os
            # Only set if values are strings (not mocks or other types)
            if isinstance(config.LANGFUSE_PUBLIC_KEY, str):
                os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
            if isinstance(config.LANGFUSE_SECRET_KEY, str):
                os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
            if isinstance(config.LANGFUSE_HOST, str):
                os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST

            # Initialize handler (credentials from environment)
            langfuse_handler = CallbackHandler()
            print("✓ Langfuse tracing enabled")
        else:
            print("⚠ Langfuse enabled but credentials not found. Tracing disabled.")
            langfuse_handler = None
    elif not config.LANGFUSE_ENABLED:
        langfuse_handler = None

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

    # Get Langfuse client if tracing is enabled
    langfuse_client = get_client() if langfuse_handler else None

    # Define nodes
    async def reasoning_node(state: AgentState) -> AgentState:
        """Node for reasoning about the next action with Langfuse tracing."""
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
        # Call LLM with Langfuse callback if available
        if langfuse_handler:
            response = await llm_with_tools.ainvoke(messages, config={"callbacks": [langfuse_handler]})
        else:
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

    async def action_node(state: AgentState) -> AgentState:
        """Node for executing tools based on LLM decision."""
        # Get the last message which should contain tool calls
        last_message = state["messages"][-1]

        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            # Execute tool calls
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

        # Call LLM with Langfuse callback if available
        if langfuse_handler:
            response = await llm.ainvoke(messages, config={"callbacks": [langfuse_handler]})
        else:
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


async def run_agent(
    repository_url: str,
    analysis_type: str = "security",
    config: Optional[Config] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    scenario_name: Optional[str] = None
) -> Dict[str, Any]:
    """Run the ReAct agent for code analysis with Langfuse tracing.

    Args:
        repository_url: The GitHub repository URL to analyze
        analysis_type: Type of analysis (security, quality, dependencies)
        config: Configuration object
        user_id: Optional user identifier for tracking usage per user
        session_id: Optional session identifier for grouping related analyses
        scenario_name: Optional scenario name for test/evaluation tracking
    """
    if config is None:
        config = Config()

    # Initialize Langfuse handler if enabled
    langfuse_handler = None
    langfuse_client = None

    if config.LANGFUSE_ENABLED and config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
        # Set environment variables for Langfuse client
        import os
        from datetime import datetime
        # Only set if values are strings (not mocks or other types)
        if isinstance(config.LANGFUSE_PUBLIC_KEY, str):
            os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
        if isinstance(config.LANGFUSE_SECRET_KEY, str):
            os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
        if isinstance(config.LANGFUSE_HOST, str):
            os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST

        # Build descriptive trace name
        repo_parts = repository_url.rstrip('/').split('/')
        repo_name = f"{repo_parts[-2]}/{repo_parts[-1]}" if len(repo_parts) >= 2 else "unknown-repo"

        trace_name = f"static-code-analysis-agent: {analysis_type} analysis"
        if scenario_name:
            trace_name = f"{trace_name} [{scenario_name}]"
        trace_name = f"{trace_name} - {repo_name}"

        # Set user and session IDs
        trace_user_id = user_id or "anonymous"
        trace_session_id = session_id or f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Prepare tags
        tags = [
            "static-analysis",
            analysis_type,
            "langgraph",
            "production",
        ]
        if scenario_name:
            tags.append(f"scenario:{scenario_name}")

        # Prepare metadata
        metadata = {
            "agent": config.AGENT_NAME,
            "demo_name": config.AGENT_DEMO_NAME,
            "version": config.AGENT_VERSION,
            "scenario": scenario_name,
            "repository": {
                "url": repository_url,
                "owner": repo_parts[-2] if len(repo_parts) >= 2 else "unknown",
                "name": repo_parts[-1] if len(repo_parts) >= 1 else "unknown"
            },
            "analysis": {
                "type": analysis_type,
                "model": config.MODEL_NAME,
                "temperature": config.TEMPERATURE,
            }
        }

        # Get Langfuse client (will create trace later)
        langfuse_client = get_client()

        print(f"✓ Langfuse tracing enabled: {trace_name}")

    # Create initial state
    initial_state = create_initial_state(
        repository_url=repository_url,
        analysis_type=analysis_type
    )

    # Create agent with Langfuse handler
    agent = create_agent(config, langfuse_handler)

    # Run the agent with Langfuse callback if available
    if langfuse_client:
        # Create handler
        from langfuse.langchain import CallbackHandler
        langfuse_handler = CallbackHandler()

    agent_config = {
        "configurable": {"thread_id": f"analysis_{repository_url}"},
        "recursion_limit": 50,
        "run_name": trace_name if langfuse_handler else None
    }
    if langfuse_handler:
        agent_config["callbacks"] = [langfuse_handler]

    # Execute agent
    final_state = await agent.ainvoke(initial_state, config=agent_config)

    # Update trace with metadata after execution (within same context)
    if langfuse_client:
        try:
            langfuse_client.update_current_trace(
                name=trace_name,
                user_id=trace_user_id,
                session_id=trace_session_id,
                tags=tags,
                metadata=metadata,
                version=f"v{config.MODEL_NAME}_{config.TEMPERATURE}"
            )
            langfuse_client.flush()
        except Exception as e:
            print(f"⚠ Could not update trace: {e}")

    # Extract and return results
    result = {
        "repository": f"{final_state['repository_owner']}/{final_state['repository_name']}",
        "analysis_type": analysis_type,
        "files_analyzed": final_state["files_analyzed"],
        "issues_found": final_state["issues_found"],
        "final_report": final_state.get("final_answer", "Analysis incomplete"),
        "steps_taken": final_state["current_step"],
        "error": final_state.get("error")
    }

    # Update trace with results metadata (add to existing metadata)
    if langfuse_handler:
        # Calculate severity breakdown
        severity_counts = {}
        for issue in final_state.get("issues_found", []):
            severity = issue.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Add result-specific tags
        result_tags = []
        if final_state.get("error"):
            result_tags.append("error")
        else:
            result_tags.append("success")

        if severity_counts.get("CRITICAL", 0) > 0:
            result_tags.append("has-critical-issues")
        if severity_counts.get("HIGH", 0) > 0:
            result_tags.append("has-high-issues")

        # Update trace with results
        try:
            langfuse_handler.langfuse.score(
                name="analysis_completeness",
                value=len(final_state["files_analyzed"]) / max(len(final_state["files_to_analyze"]), 1),
                comment=f"Analyzed {len(final_state['files_analyzed'])} of {len(final_state['files_to_analyze'])} files"
            )

            # Update metadata with results
            langfuse_handler.update_current_observation(
                metadata={
                    "results": {
                        "files_analyzed": len(final_state["files_analyzed"]),
                        "total_files": len(final_state["files_to_analyze"]),
                        "issues_found": len(final_state["issues_found"]),
                        "severity_breakdown": severity_counts
                    },
                    "execution": {
                        "steps_taken": final_state["current_step"],
                        "completed": not final_state["should_continue"],
                        "has_error": final_state.get("error") is not None
                    }
                }
            )

            print(f"✓ Trace results updated:")
            print(f"  - Files analyzed: {len(final_state['files_analyzed'])}/{len(final_state['files_to_analyze'])}")
            print(f"  - Issues found: {len(final_state['issues_found'])}")
            print(f"  - Status tags: {', '.join(result_tags)}")
        except Exception as e:
            print(f"⚠ Could not update trace results: {e}")

    return result


def run_agent_sync(
    repository_url: str,
    analysis_type: str = "security",
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for running the agent."""
    import asyncio
    return asyncio.run(run_agent(repository_url, analysis_type, config))