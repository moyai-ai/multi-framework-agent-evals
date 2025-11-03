#!/usr/bin/env python3
"""
Quick validation script to check if the setup is correct
"""

import sys
from pathlib import Path


def validate_structure():
    """Validate project structure"""
    print("Validating project structure...")

    required_files = [
        "pyproject.toml",
        "README.md",
        ".env.example",
        "src/__init__.py",
        "src/agents.py",
        "src/tasks.py",
        "src/crew.py",
        "src/tools.py",
        "src/context.py",
        "src/runner.py",
        "src/scenarios/simple_functions.json",
        "src/scenarios/class_methods.json",
        "src/scenarios/complex_cases.json",
        "tests/conftest.py",
        "tests/test_agents.py",
        "tests/test_tools.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing files:")
        for f in missing_files:
            print(f"   - {f}")
        return False

    print("✓ All required files present")
    return True


def validate_imports():
    """Validate that imports work"""
    print("\nValidating imports...")

    try:
        from src import context, agents, tasks, crew, tools, runner

        print("✓ Core modules import successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

    return True


def validate_config():
    """Validate configuration"""
    print("\nValidating configuration...")

    try:
        from src.context import Config

        config = Config()
        print(f"✓ Config loaded")
        print(f"  - Model: {config.OPENAI_MODEL_NAME}")
        print(f"  - Max iterations: {config.MAX_ITERATIONS}")

        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "test-api-key":
            print("⚠️  Warning: OPENAI_API_KEY not set (copy .env.example to .env)")

    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

    return True


def validate_agents():
    """Validate agents"""
    print("\nValidating agents...")

    try:
        from src.agents import list_agents, get_agent_by_name
        from src.context import Config

        agents = list_agents()
        print(f"✓ Found {len(agents)} agents:")
        for agent in agents:
            print(f"  - {agent['name']}: {agent['role']}")

        # Test creating agents (may fail without API key)
        config = Config()
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "test-api-key":
            print("⚠️  Skipping agent creation test (API key not set)")
            return True

        try:
            analyzer = get_agent_by_name("code_analyzer")
            if analyzer:
                print(f"✓ Can create agents (tested: {analyzer.role})")
            else:
                print("❌ Failed to create agent")
                return False
        except Exception as e:
            if "OPENAI_API_KEY" in str(e):
                print("⚠️  Cannot fully test agents without API key (this is okay)")
                return True
            raise

    except Exception as e:
        print(f"❌ Agent error: {e}")
        return False

    return True


def validate_scenarios():
    """Validate scenarios"""
    print("\nValidating scenarios...")

    try:
        from src.runner import ScenarioRunner

        runner = ScenarioRunner(verbose=False)
        scenarios = runner.load_scenarios_from_directory("src/scenarios")

        print(f"✓ Loaded {len(scenarios)} scenario(s):")
        for scenario in scenarios:
            print(f"  - {scenario.name} ({len(scenario.conversation)} turn(s))")

    except Exception as e:
        print(f"❌ Scenario error: {e}")
        return False

    return True


def main():
    """Run all validations"""
    print("=" * 60)
    print("Unit Test Agent Demo - Setup Validation")
    print("=" * 60)

    validations = [
        validate_structure,
        validate_imports,
        validate_config,
        validate_agents,
        validate_scenarios,
    ]

    results = [v() for v in validations]

    print("\n" + "=" * 60)
    if all(results):
        print("✓ All validations passed!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your OPENAI_API_KEY to .env")
        print("3. Run: unset VIRTUAL_ENV && uv sync")
        print("4. Run: unset VIRTUAL_ENV && uv run pytest tests/ -v")
        print("=" * 60)
        return 0
    else:
        print("❌ Some validations failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
