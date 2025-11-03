"""Bank support agent implementation using Pydantic AI."""

import os
from typing import Dict, Optional, List, Any
from pydantic_ai import Agent

from .context import BankSupportContext
from .tools import BANK_SUPPORT_TOOLS

# Helper to expose tools property on Agent instances
def _add_tools_property(agent: Agent[BankSupportContext], tools: List):
    """Add a tools property to an agent instance for testing purposes."""
    if not hasattr(agent, 'tools'):
        # Store tools in a way that can be accessed
        agent._agent_tools = tools
        # Add a property-like accessor
        agent.__dict__['tools'] = tools
    return agent


# System prompts for different agent types
BANK_SUPPORT_SYSTEM_PROMPT = """You are a professional bank support agent helping customers with their banking needs.

Your primary responsibilities:
1. Authenticate customers securely before accessing account information
2. Provide account balances and transaction history
3. Assist with fund transfers between accounts
4. Create support tickets for issues requiring escalation
5. Check for and report fraud alerts
6. Update customer contact information

Guidelines:
- Always authenticate the customer before accessing sensitive information
- Be professional, helpful, and empathetic
- Explain actions clearly before performing them
- If you detect potential fraud or security issues, immediately escalate
- For complex issues beyond your capabilities, create a support ticket
- Maintain customer privacy and security at all times

Authentication Flow:
1. ALWAYS use check_authentication_status tool FIRST to see if customer is already authenticated
2. If not authenticated, ask for their email and last 4 digits of SSN for verification
3. Once authenticated, proceed with their request
4. If authentication fails, offer to help with general inquiries only

IMPORTANT: You MUST use the check_authentication_status tool before asking for credentials - the customer may already be authenticated from a previous interaction

Available Operations:
- View account balances and details
- Check recent transactions
- Transfer funds between accounts
- Create support tickets
- Check fraud alerts
- Update contact information

Remember: Customer security and satisfaction are your top priorities."""

FRAUD_SPECIALIST_PROMPT = """You are a fraud detection specialist for the bank.

Your responsibilities:
- Monitor and investigate suspicious transactions
- Check fraud alerts on customer accounts
- Provide security recommendations
- Escalate serious fraud cases immediately

Always prioritize customer account security and follow fraud prevention protocols."""

ACCOUNT_SPECIALIST_PROMPT = """You are an account specialist helping customers manage their accounts.

Your expertise includes:
- Account balances and statements
- Transaction history and details
- Fund transfers between accounts
- Account settings and preferences

Provide clear, accurate information and guide customers through account operations."""


def create_bank_support_agent(
    model_name: str = None,
    temperature: float = 0.3,
) -> Agent[BankSupportContext]:
    """
    Create the main bank support agent.

    Args:
        model_name: The model to use (defaults to env variable or gpt-4o)
        temperature: Temperature for model responses

    Returns:
        Configured bank support agent
    """
    # Get model name from env or use default
    if model_name is None:
        model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")

    # Create the agent with tools (Pydantic AI handles model setup internally)
    agent = Agent(
        model=model_name,  # Pass model name directly
        deps_type=BankSupportContext,
        system_prompt=BANK_SUPPORT_SYSTEM_PROMPT,
        tools=BANK_SUPPORT_TOOLS,
        name="Bank Support Agent",
    )
    
    # Expose tools for testing
    _add_tools_property(agent, BANK_SUPPORT_TOOLS)

    return agent


def create_fraud_specialist_agent(
    model_name: str = None,
    temperature: float = 0.2,
) -> Agent[BankSupportContext]:
    """
    Create a fraud specialist agent.

    Args:
        model_name: The model to use
        temperature: Temperature for model responses (lower for fraud detection)

    Returns:
        Configured fraud specialist agent
    """
    if model_name is None:
        model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")

    # Fraud specialist uses subset of tools
    fraud_tools = [
        tool for tool in BANK_SUPPORT_TOOLS
        if tool.__name__ in [
            "authenticate_customer",
            "check_fraud_alert",
            "get_recent_transactions",
            "create_support_ticket"
        ]
    ]

    agent = Agent(
        model=model_name,  # Pass model name directly
        deps_type=BankSupportContext,
        system_prompt=FRAUD_SPECIALIST_PROMPT,
        tools=fraud_tools,
        name="Fraud Specialist Agent",
    )
    
    # Expose tools for testing
    _add_tools_property(agent, fraud_tools)

    return agent


def create_account_specialist_agent(
    model_name: str = None,
    temperature: float = 0.3,
) -> Agent[BankSupportContext]:
    """
    Create an account specialist agent.

    Args:
        model_name: The model to use
        temperature: Temperature for model responses

    Returns:
        Configured account specialist agent
    """
    if model_name is None:
        model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")

    # Account specialist uses account-related tools
    account_tools = [
        tool for tool in BANK_SUPPORT_TOOLS
        if tool.__name__ in [
            "authenticate_customer",
            "get_account_balance",
            "get_recent_transactions",
            "transfer_funds",
            "update_contact_info"
        ]
    ]

    agent = Agent(
        model=model_name,  # Pass model name directly
        deps_type=BankSupportContext,
        system_prompt=ACCOUNT_SPECIALIST_PROMPT,
        tools=account_tools,
        name="Account Specialist Agent",
    )
    
    # Expose tools for testing
    _add_tools_property(agent, account_tools)

    return agent


# Agent registry - store factory functions instead of instances
AGENT_FACTORIES: Dict[str, callable] = {
    "bank_support": create_bank_support_agent,
    "fraud_specialist": create_fraud_specialist_agent,
    "account_specialist": create_account_specialist_agent,
}

# For backwards compatibility, create a property-like access
AGENTS: Dict[str, Agent[BankSupportContext]] = {}


def get_agent_by_name(name: str) -> Optional[Agent[BankSupportContext]]:
    """
    Get agent by exact or partial name match.
    Creates a fresh instance each time to avoid threading issues.

    Args:
        name: Agent name or key

    Returns:
        Matching agent or None
    """
    name_lower = name.lower()

    # Exact match
    if name_lower in AGENT_FACTORIES:
        return AGENT_FACTORIES[name_lower]()

    # Partial match
    for key, factory in AGENT_FACTORIES.items():
        if name_lower in key.lower():
            return factory()

    return None


def get_initial_agent() -> Agent[BankSupportContext]:
    """Get the initial entry point agent. Creates a fresh instance."""
    return AGENT_FACTORIES["bank_support"]()


def list_agents() -> List[Dict[str, Any]]:
    """List all available agents with details."""
    agent_list = []
    for key, factory in AGENT_FACTORIES.items():
        # Get tools from agent - pydantic-ai stores them in _tools
        agent_tools = []

        # Map of key to expected tools (since we filter them at creation)
        if key == "bank_support":
            agent_tools = [t.__name__ for t in BANK_SUPPORT_TOOLS]
        elif key == "fraud_specialist":
            agent_tools = ["authenticate_customer", "check_fraud_alert",
                          "get_recent_transactions", "create_support_ticket"]
        elif key == "account_specialist":
            agent_tools = ["authenticate_customer", "get_account_balance",
                          "get_recent_transactions", "transfer_funds", "update_contact_info"]

        # Create a temporary instance to get the name
        temp_agent = factory()
        agent_info = {
            "key": key,
            "name": temp_agent.name if hasattr(temp_agent, 'name') else key,
            "tools": agent_tools[:5],  # Limit to first 5 tools for brevity
            "model": "gpt-4o",  # Default model
        }
        agent_list.append(agent_info)

    return agent_list


def get_agent_tools(agent: Agent[BankSupportContext]) -> List:
    """
    Get tools from a Pydantic AI Agent instance.
    
    Args:
        agent: The agent instance
        
    Returns:
        List of tool functions
    """
    # Pydantic AI stores tools in a private _tools attribute or as a property
    if hasattr(agent, '_tools'):
        return agent._tools
    elif hasattr(agent, 'tools'):
        return agent.tools if agent.tools is not None else []
    else:
        # Fallback: try to access via __dict__ or return empty list
        return getattr(agent, '_tools', [])


def get_agent_for_request_type(request_type: str) -> Agent[BankSupportContext]:
    """
    Route to appropriate agent based on request type.

    Args:
        request_type: Type of customer request

    Returns:
        Most appropriate agent for the request
    """
    fraud_keywords = ["fraud", "suspicious", "unauthorized", "stolen", "scam"]
    account_keywords = ["balance", "transfer", "statement", "transaction"]

    request_lower = request_type.lower()

    # Check for fraud-related requests
    if any(keyword in request_lower for keyword in fraud_keywords):
        return AGENT_FACTORIES["fraud_specialist"]()

    # Check for account-specific requests
    if any(keyword in request_lower for keyword in account_keywords):
        return AGENT_FACTORIES["account_specialist"]()

    # Default to general support agent
    return AGENT_FACTORIES["bank_support"]()