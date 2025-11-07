"""CLI entry point for agent-instrumentor with ReACT agent."""

import argparse
import asyncio
import sys
import os
from pathlib import Path

from .agents import instrument_codebase_with_agent
from .config import (
    InstrumentationConfig,
    InstrumentationLevel,
    InstrumentationTarget,
    PRESET_MINIMAL,
    PRESET_STANDARD,
    PRESET_COMPREHENSIVE,
)
from .platforms import list_platforms, get_platform


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous instrumentation of multi-framework agents using ReACT pattern with Nia MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Instrument with standard configuration
  agent-instrumentor /path/to/codebase

  # Use minimal instrumentation (LLM calls only)
  agent-instrumentor /path/to/codebase --preset minimal

  # Use comprehensive instrumentation
  agent-instrumentor /path/to/codebase --preset comprehensive

  # Use specific platform
  agent-instrumentor /path/to/codebase --platform phoenix

  # Specify custom targets
  agent-instrumentor /path/to/codebase --targets tools,llm_calls,rag

  # List available platforms
  agent-instrumentor --list-platforms

Environment Variables:
  ANTHROPIC_API_KEY     Claude API key (required)
  NIA_API_KEY           Nia MCP API key (required for documentation search)
  NIA_API_URL           Nia API URL (defaults to https://apigcp.trynia.ai/)

  # Optional: Self-instrumentation with Langfuse
  LANGFUSE_SECRET_KEY   Langfuse secret key (optional, for self-instrumentation)
  LANGFUSE_PUBLIC_KEY   Langfuse public key (optional, for self-instrumentation)
  LANGFUSE_BASE_URL     Langfuse base URL (optional, defaults to https://cloud.langfuse.com)

For more information: https://github.com/anthropics/agent-instrumentor
        """
    )

    parser.add_argument(
        "codebase_path",
        nargs="?",
        default=".",
        help="Path to codebase to instrument (default: current directory)"
    )

    parser.add_argument(
        "--platform",
        default="langfuse",
        help="Observability platform to use (default: langfuse)"
    )

    parser.add_argument(
        "--preset",
        choices=["minimal", "standard", "comprehensive"],
        help="Use preset configuration (overrides --level and --targets)"
    )

    parser.add_argument(
        "--level",
        choices=["minimal", "standard", "comprehensive"],
        default="standard",
        help="Instrumentation level (default: standard)"
    )

    parser.add_argument(
        "--targets",
        help="Comma-separated list of targets: tools,llm_calls,rag,memory,chains,errors,sub_agents,prompts"
    )


    parser.add_argument(
        "--list-platforms",
        action="store_true",
        help="List available observability platforms"
    )

    parser.add_argument(
        "--api-key",
        help="Anthropic API key (overrides ANTHROPIC_API_KEY env var)"
    )

    args = parser.parse_args()

    # Handle list commands
    if args.list_platforms:
        print("\n📊 Available Observability Platforms:\n")
        platforms = list_platforms()
        for platform_info in platforms:
            print(f"  • {platform_info.display_name} ({platform_info.name})")
            print(f"    Dependencies: {', '.join(platform_info.dependencies)}")
            print(f"    Environment Variables:")
            for env_var in platform_info.env_vars:
                required = "required" if env_var.get("required", False) else "optional"
                print(f"      - {env_var['name']} ({required})")
            print()
        return 0

    # Check for required environment variables
    if not os.getenv("ANTHROPIC_API_KEY") and not args.api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Set it with: export ANTHROPIC_API_KEY=your-key")
        return 1

    if not os.getenv("NIA_API_KEY"):
        print("⚠️  Warning: NIA_API_KEY not set. Nia MCP tools will not be available.")
        print("   Documentation search will use fallback patterns.")
        print("   Get your key at: https://app.trynia.ai/")
        print()

    # Validate platform
    platform = get_platform(args.platform)
    if not platform:
        print(f"❌ Error: Platform '{args.platform}' not found")
        print(f"Available platforms: {', '.join([p.name for p in list_platforms()])}")
        return 1

    # Validate codebase path
    codebase_path = Path(args.codebase_path).resolve()
    if not codebase_path.exists():
        print(f"❌ Error: Path not found: {codebase_path}")
        return 1

    if not codebase_path.is_dir():
        print(f"❌ Error: Not a directory: {codebase_path}")
        return 1

    # Build configuration
    if args.preset:
        if args.preset == "minimal":
            config = PRESET_MINIMAL
        elif args.preset == "comprehensive":
            config = PRESET_COMPREHENSIVE
        else:
            config = PRESET_STANDARD

        # Override platform if specified
        config.platform = args.platform
    else:
        # Build custom configuration
        level = InstrumentationLevel(args.level)

        # Parse targets
        if args.targets:
            target_names = [t.strip() for t in args.targets.split(",")]
            targets = [InstrumentationTarget(t) for t in target_names]
        else:
            # Default targets based on level
            if level == InstrumentationLevel.MINIMAL:
                targets = [InstrumentationTarget.LLM_CALLS]
            elif level == InstrumentationLevel.COMPREHENSIVE:
                targets = list(InstrumentationTarget)
            else:
                targets = [
                    InstrumentationTarget.TOOLS,
                    InstrumentationTarget.LLM_CALLS,
                    InstrumentationTarget.CHAINS,
                    InstrumentationTarget.ERRORS,
                ]

        config = InstrumentationConfig(
            level=level,
            targets=targets,
            platform=args.platform,
        )

    # Print banner
    print("\n" + "="*70)
    print("🤖 AGENT INSTRUMENTOR - ReACT Pattern with Nia MCP")
    print("   Intelligent instrumentation using documentation search")
    print("="*70)
    print(f"\n📂 Codebase: {codebase_path}")
    print(f"🔧 Platform: {platform.display_name}")
    print(f"📊 Level: {config.level.value}")
    print(f"🎯 Targets: {', '.join([t.value for t in config.targets])}")
    print()

    try:
        # Run instrumentation with ReACT agent
        print("🚀 Starting ReACT agent...")
        print("   The agent will:")
        print("   1. Detect frameworks in your codebase")
        print("   2. Search documentation for instrumentation patterns (via Nia MCP)")
        print("   3. Generate and inject instrumentation code")
        print()

        result = asyncio.run(
            instrument_codebase_with_agent(
                codebase_path=str(codebase_path),
                config=config,
                api_key=args.api_key
            )
        )

        # Print results
        if result["success"]:
            print("\n✅ Instrumentation completed successfully!")
            print(f"\n📝 Agent Report:")
            print(result["report"])

            if result.get("frameworks_detected"):
                print(f"\n🔍 Frameworks Detected:")
                for fw in result["frameworks_detected"]:
                    print(f"  • {fw}")

            if result.get("files_modified"):
                print(f"\n📄 Files Modified:")
                for file in result["files_modified"]:
                    print(f"  • {file}")

            return 0
        else:
            print(f"\n❌ Instrumentation failed: {result.get('error', 'Unknown error')}")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
