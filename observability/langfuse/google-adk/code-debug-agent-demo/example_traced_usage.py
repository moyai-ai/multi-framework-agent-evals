"""Example usage of the traced Code Debug Agent with Langfuse observability.

This file demonstrates various ways to use the traced agent and view the
observability data in Langfuse.

Prerequisites:
1. Set up .env file with required API keys (see .env.example)
2. Install dependencies: unset VIRTUAL_ENV && uv sync
3. Ensure you have access to Langfuse dashboard

Run this file:
    unset VIRTUAL_ENV && uv run python example_traced_usage.py
"""

import asyncio
import logging
from src.traced_runner import TracedAgentRunner, run_debug_agent_traced, run_traced_scenario
from langfuse import get_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_simple_query():
    """Example 1: Simple error query with full tracing."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Query with Tracing")
    print("="*80)

    response = await run_debug_agent_traced(
        prompt="ImportError: No module named 'pandas'",
        agent_name="debug_agent",
        user_id="example_user_1",
        session_id="example_session_1"
    )

    print(f"\n✅ Response received (length: {len(response)} chars)")
    print(f"Preview: {response[:200]}...")
    print("\n📊 Check Langfuse dashboard to see:")
    print("   - Agent execution trace")
    print("   - Tool calls (search_stack_exchange_for_error)")
    print("   - RAG operations (search_similar_errors)")
    print("   - Execution time and metadata")


async def example_2_streaming_events():
    """Example 2: Stream events and see detailed tracing."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Streaming Events with Detailed Tracing")
    print("="*80)

    runner = TracedAgentRunner(
        agent_name="quick_debug_agent",
        app_name="quick-debug-example"
    )

    event_count = 0
    async for event in runner.run_traced(
        prompt="TypeError: Cannot read property 'map' of undefined",
        user_id="example_user_2",
        session_id="streaming_session",
        metadata={
            "source": "example_script",
            "environment": "development",
            "test_case": "example_2"
        }
    ):
        event_count += 1
        if event_count <= 3:  # Show first 3 events
            print(f"   Event {event_count}: {type(event).__name__}")

    print(f"\n✅ Processed {event_count} events")
    print("\n📊 In Langfuse, you'll see:")
    print("   - Each event captured")
    print("   - Custom metadata (source, environment, test_case)")
    print("   - Quick debug agent's simplified tool usage")


async def example_3_error_handling():
    """Example 3: Demonstrate error tracking in Langfuse."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Error Handling and Tracking")
    print("="*80)

    runner = TracedAgentRunner(agent_name="debug_agent")

    try:
        # This might cause an error if API keys are invalid
        async for event in runner.run_traced(
            prompt="django.db.migrations.exceptions.InconsistentMigrationHistory",
            user_id="example_user_3",
            session_id="error_tracking_session"
        ):
            pass  # Process events

        print("✅ Execution completed successfully")

    except Exception as e:
        print(f"❌ Error occurred: {type(e).__name__}: {e}")
        print("\n📊 In Langfuse, the error is captured with:")
        print("   - Error type and message")
        print("   - Stack trace context")
        print("   - Span marked with ERROR level")

    print("\n💡 Tip: Even if execution fails, the trace is still recorded!")


async def example_4_scenario_testing():
    """Example 4: Run a test scenario with observability."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Scenario Testing with Observability")
    print("="*80)

    scenario = {
        "name": "React Hook Rules Violation",
        "description": "Test handling of React-specific errors",
        "error_message": "React Hook 'useState' is called conditionally. React Hooks must be called in the exact same order in every component render.",
        "programming_language": "javascript",
        "framework": "react",
        "expected_tools": ["search_stack_exchange_for_error"],
        "expected_keywords": ["hook", "conditional", "order"]
    }

    result = await run_traced_scenario(
        scenario_data=scenario,
        agent_name="debug_agent",
        user_id="scenario_tester"
    )

    print(f"\n✅ Scenario execution completed")
    print(f"   Success: {result['success']}")
    print(f"   Agent used: {result['agent_used']}")

    print("\n📊 In Langfuse, scenario traces are tagged:")
    print("   - Tag: 'scenario-test'")
    print("   - Scenario name in trace title")
    print("   - Full scenario data in metadata")


async def example_5_multiple_agents():
    """Example 5: Compare different agents with tracing."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Comparing Multiple Agents")
    print("="*80)

    error_prompt = "CORS error: Access blocked by CORS policy"

    # Test with quick_debug_agent
    print("\n🚀 Running with quick_debug_agent...")
    quick_runner = TracedAgentRunner(agent_name="quick_debug_agent")
    quick_response = await quick_runner.query(
        prompt=error_prompt,
        user_id="comparison_user",
        session_id="quick_agent_session"
    )
    print(f"   Quick agent response length: {len(quick_response)} chars")

    # Test with full debug_agent
    print("\n🚀 Running with debug_agent...")
    full_runner = TracedAgentRunner(agent_name="debug_agent")
    full_response = await full_runner.query(
        prompt=error_prompt,
        user_id="comparison_user",
        session_id="debug_agent_session"
    )
    print(f"   Full agent response length: {len(full_response)} chars")

    print("\n📊 In Langfuse, compare:")
    print("   - Execution time: quick vs full agent")
    print("   - Tool usage: quick uses fewer tools")
    print("   - Response quality: full agent more comprehensive")
    print("   - Filter by user_id: 'comparison_user' to see both")


async def example_6_session_context():
    """Example 6: Track multi-turn conversations with session context."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Multi-Turn Conversation Tracking")
    print("="*80)

    runner = TracedAgentRunner(agent_name="debug_agent")
    session_id = "multi_turn_session_example"
    user_id = "conversation_user"

    # Turn 1: Initial error
    print("\n💬 Turn 1: Initial error query...")
    response1 = await runner.query(
        prompt="I'm getting 'ModuleNotFoundError: No module named numpy'",
        user_id=user_id,
        session_id=session_id
    )
    print(f"   Response 1: {len(response1)} chars")

    # Turn 2: Follow-up question
    print("\n💬 Turn 2: Follow-up question...")
    response2 = await runner.query(
        prompt="How do I install numpy on Windows?",
        user_id=user_id,
        session_id=session_id
    )
    print(f"   Response 2: {len(response2)} chars")

    print("\n📊 In Langfuse:")
    print(f"   - Filter by session_id: '{session_id}'")
    print("   - See complete conversation flow")
    print("   - Track context across multiple turns")
    print("   - Analyze conversation patterns")


async def example_7_performance_monitoring():
    """Example 7: Monitor performance metrics."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Performance Monitoring")
    print("="*80)

    langfuse = get_client()

    # Run multiple queries to generate metrics
    test_prompts = [
        "SyntaxError: invalid syntax",
        "IndexError: list index out of range",
        "KeyError: 'username'"
    ]

    runner = TracedAgentRunner(agent_name="debug_agent")

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🔄 Running query {i}/{len(test_prompts)}: {prompt}")
        await runner.query(
            prompt=prompt,
            user_id="performance_tester",
            session_id=f"perf_test_{i}"
        )

    # Flush traces to ensure they're sent
    langfuse.flush()

    print("\n✅ Performance test completed")
    print("\n📊 In Langfuse Analytics:")
    print("   - View average execution time")
    print("   - Analyze tool call patterns")
    print("   - Monitor RAG retrieval latency")
    print("   - Track error rates")
    print("   - Compare performance across queries")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("🎯 TRACED CODE DEBUG AGENT - EXAMPLE USAGE")
    print("="*80)
    print("\nThis script demonstrates comprehensive Langfuse observability")
    print("for the Google ADK Code Debug Agent.")
    print("\n⚠️  Make sure you have configured .env with:")
    print("   - GOOGLE_API_KEY")
    print("   - LANGFUSE_PUBLIC_KEY")
    print("   - LANGFUSE_SECRET_KEY")
    print("   - LANGFUSE_HOST")

    try:
        # Run examples sequentially
        await example_1_simple_query()
        await asyncio.sleep(1)  # Brief pause between examples

        await example_2_streaming_events()
        await asyncio.sleep(1)

        await example_3_error_handling()
        await asyncio.sleep(1)

        await example_4_scenario_testing()
        await asyncio.sleep(1)

        await example_5_multiple_agents()
        await asyncio.sleep(1)

        await example_6_session_context()
        await asyncio.sleep(1)

        await example_7_performance_monitoring()

        # Final summary
        print("\n" + "="*80)
        print("✅ ALL EXAMPLES COMPLETED!")
        print("="*80)
        print("\n📊 Next Steps:")
        print("   1. Open your Langfuse dashboard")
        print("   2. Navigate to 'Traces' tab")
        print("   3. Filter by tags: 'google-adk', 'debug-agent'")
        print("   4. Explore individual traces to see:")
        print("      - Agent execution hierarchy")
        print("      - Tool calls with inputs/outputs")
        print("      - RAG operations and retrieval metrics")
        print("      - Performance metrics and timing")
        print("      - Error tracking and debugging info")
        print("\n🎓 Learning Tip:")
        print("   Compare traces from different examples to understand")
        print("   how different agents and prompts affect execution!")

        # Ensure all traces are sent
        langfuse = get_client()
        langfuse.flush()
        print("\n✅ All traces flushed to Langfuse")

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Check that .env file is configured correctly")
        print("   - Verify API keys are valid")
        print("   - Enable debug mode: LANGFUSE_DEBUG=true")
        print("   - Check network connectivity")


if __name__ == "__main__":
    asyncio.run(main())
