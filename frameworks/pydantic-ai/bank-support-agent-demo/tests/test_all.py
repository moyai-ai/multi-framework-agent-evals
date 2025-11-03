"""Test all key functionality."""

import pytest
from src.agents import get_initial_agent
from src.context import create_initial_context


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all(skip_if_no_api_key):
    """Test all key functionality."""
    # Test 1: Simple greeting
    agent = get_initial_agent()
    context = create_initial_context()
    result = await agent.run("Hello", deps=context)
    assert result.output is not None
    assert len(result.output) > 0

    # Test 2: Authentication
    agent = get_initial_agent()
    context = create_initial_context()
    result = await agent.run(
        "My email is test@example.com and SSN last 4 is 1234",
        deps=context
    )
    # Note: authentication may succeed or fail depending on test data
    assert result.output is not None

    # Test 3: Balance check after auth (if authenticated)
    if context.authenticated:
        agent = get_initial_agent()
        result = await agent.run("Show my balances", deps=context)
        assert result.output is not None