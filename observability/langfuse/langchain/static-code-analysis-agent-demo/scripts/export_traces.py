#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.28.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""Script to export traces from Langfuse using the REST API.

This script demonstrates how to:
1. Connect to Langfuse REST API with httpx
2. List and filter traces
3. Export traces to JSON
4. Validate trace structure

Usage:
    uv run scripts/export_traces.py --output reports/exported_traces.json --limit 50
    uv run scripts/export_traces.py --validate
    uv run scripts/export_traces.py --name "static-code-analysis" --limit 100
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def export_traces(
    output_file: str = "reports/exported_traces.json",
    limit: int = 50,
    name_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
    user_id_filter: Optional[str] = None,
    session_id_filter: Optional[str] = None,
    hours_back: int = 24,
) -> Dict[str, Any]:
    """Export traces from Langfuse using the REST API.

    Args:
        output_file: Output file path for exported traces
        limit: Maximum number of traces to export
        name_filter: Filter traces by name (substring match)
        tag_filter: Filter traces by tag
        user_id_filter: Filter traces by user ID
        session_id_filter: Filter traces by session ID
        hours_back: Export traces from the last N hours

    Returns:
        Dictionary with export statistics
    """
    print("=" * 60)
    print("LANGFUSE TRACE EXPORT TOOL (REST API)")
    print("=" * 60)

    # Get credentials from environment
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        print("\nERROR: Langfuse credentials not found!")
        print("Please set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables.")
        return {
            "success": False,
            "error": "Missing credentials",
        }

    print(f"\nConnected to Langfuse: {host}")
    print(f"Exporting traces from the last {hours_back} hours...")
    print(f"Limit: {limit} traces")
    if name_filter:
        print(f"Name filter: {name_filter}")
    if tag_filter:
        print(f"Tag filter: {tag_filter}")
    if user_id_filter:
        print(f"User ID filter: {user_id_filter}")
    if session_id_filter:
        print(f"Session ID filter: {session_id_filter}")
    print()

    try:
        # Build API endpoint URL
        api_url = f"{host}/api/public/traces"

        # Calculate timestamp filter
        from_timestamp = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Build query parameters
        params = {
            "page": 1,
            "limit": limit,
            "fromTimestamp": from_timestamp.isoformat(),
        }

        if name_filter:
            params["name"] = name_filter
        if tag_filter:
            params["tags"] = tag_filter
        if user_id_filter:
            params["userId"] = user_id_filter
        if session_id_filter:
            params["sessionId"] = session_id_filter

        # Make API request with Basic Auth
        print(f"Fetching traces from: {api_url}")
        print(f"Query params: {json.dumps({k: v for k, v in params.items() if k != 'fromTimestamp'}, indent=2)}")
        print(f"From timestamp: {from_timestamp.isoformat()}\n")

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                api_url,
                params=params,
                auth=(public_key, secret_key),
            )

            # Check response
            if response.status_code != 200:
                print(f"ERROR: API request failed with status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "response": response.text[:500],
                }

            data = response.json()

        traces = data.get("data", [])
        total_items = data.get("meta", {}).get("totalItems", len(traces))

        print(f"Found {len(traces)} traces (total available: {total_items})")

        if not traces:
            print("No traces found matching the criteria.")
            return {
                "success": True,
                "total_traces": 0,
                "exported_file": None,
            }

        # Convert traces to dict format for JSON export and collect statistics
        exported_traces = []
        trace_stats = {
            "names": {},
            "tags": {},
            "users": set(),
            "sessions": set(),
        }

        for trace in traces:
            # Collect statistics
            trace_name = trace.get("name") or "unnamed"
            trace_stats["names"][trace_name] = trace_stats["names"].get(trace_name, 0) + 1

            user_id = trace.get("userId")
            if user_id:
                trace_stats["users"].add(user_id)

            session_id = trace.get("sessionId")
            if session_id:
                trace_stats["sessions"].add(session_id)

            # Collect tags
            tags = trace.get("tags", [])
            for tag in tags:
                trace_stats["tags"][tag] = trace_stats["tags"].get(tag, 0) + 1

            # Export trace data
            trace_dict = {
                "id": trace.get("id"),
                "timestamp": trace.get("timestamp"),
                "name": trace.get("name"),
                "user_id": user_id,
                "session_id": session_id,
                "release": trace.get("release"),
                "version": trace.get("version"),
                "tags": tags,
                "bookmarked": trace.get("bookmarked", False),
                "public": trace.get("public", False),
                "input": trace.get("input"),
                "output": trace.get("output"),
                "metadata": trace.get("metadata", {}),
            }

            exported_traces.append(trace_dict)

        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_traces": len(exported_traces),
            "total_available": total_items,
            "filters": {
                "name": name_filter,
                "tag": tag_filter,
                "user_id": user_id_filter,
                "session_id": session_id_filter,
                "hours_back": hours_back,
                "limit": limit,
            },
            "traces": exported_traces,
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        # Print statistics
        print("\n" + "=" * 60)
        print("EXPORT STATISTICS")
        print("=" * 60)
        print(f"Total traces exported: {len(exported_traces)}")
        print(f"Total traces available: {total_items}")
        print(f"Unique users: {len(trace_stats['users'])}")
        print(f"Unique sessions: {len(trace_stats['sessions'])}")
        print(f"\nTrace names distribution:")
        for name, count in sorted(trace_stats["names"].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {name}: {count}")

        if trace_stats["tags"]:
            print(f"\nTop tags:")
            for tag, count in sorted(trace_stats["tags"].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {tag}: {count}")

        print(f"\nExported to: {output_path.absolute()}")
        print("=" * 60)

        return {
            "success": True,
            "total_traces": len(exported_traces),
            "total_available": total_items,
            "exported_file": str(output_path.absolute()),
            "statistics": {
                "unique_users": len(trace_stats['users']),
                "unique_sessions": len(trace_stats['sessions']),
                "trace_names": dict(trace_stats["names"]),
                "tags": dict(trace_stats["tags"]),
            }
        }

    except Exception as e:
        print(f"\nError exporting traces: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
        }


def validate_trace_naming(traces_file: str) -> Dict[str, Any]:
    """Validate trace naming conventions.

    Args:
        traces_file: Path to exported traces JSON file

    Returns:
        Dictionary with validation results
    """
    print("\n" + "=" * 60)
    print("TRACE NAMING VALIDATION")
    print("=" * 60)

    with open(traces_file, 'r') as f:
        data = json.load(f)

    traces = data.get("traces", [])

    issues = []
    good_traces = []

    for trace in traces:
        trace_id = trace.get("id")
        trace_name = trace.get("name", "")

        # Check for generic/bad naming
        if not trace_name or trace_name in ["invocation", "call", "unnamed", ""]:
            issues.append({
                "trace_id": trace_id,
                "issue": "generic_name",
                "name": trace_name or "empty",
                "message": "Trace has generic or missing name"
            })
        elif "unknown" in trace_name.lower():
            issues.append({
                "trace_id": trace_id,
                "issue": "unknown_service",
                "name": trace_name,
                "message": "Trace name contains 'unknown'"
            })
        else:
            good_traces.append(trace_name)

        # Check metadata for service name
        metadata = trace.get("metadata", {})
        if isinstance(metadata, dict):
            agent = metadata.get("agent", "")
            if agent == "unknown_service" or not agent:
                issues.append({
                    "trace_id": trace_id,
                    "issue": "missing_agent_metadata",
                    "name": trace_name,
                    "message": "Metadata missing or has invalid agent name"
                })

    # Count issue types
    issue_types = {}
    for issue in issues:
        issue_type = issue["issue"]
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

    # Print results
    print(f"\nTotal traces analyzed: {len(traces)}")
    print(f"Good traces: {len(good_traces)}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\nIssues by type:")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue_type}: {count}")

        print("\nSample issues (first 5):")
        for issue in issues[:5]:
            print(f"  - {issue['issue']}: {issue['name']} (ID: {issue['trace_id'][:16]}...)")

    if good_traces:
        print(f"\nSample good trace names:")
        for name in list(set(good_traces))[:10]:
            print(f"  - {name}")

    print("=" * 60)

    return {
        "total_traces": len(traces),
        "good_traces": len(good_traces),
        "issues": issues,
        "issue_summary": issue_types,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export and validate Langfuse traces")
    parser.add_argument(
        "--output",
        "-o",
        default="reports/exported_traces.json",
        help="Output file for exported traces"
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=50,
        help="Maximum number of traces to export"
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Filter traces by name (substring match)"
    )
    parser.add_argument(
        "--tag",
        "-t",
        help="Filter traces by tag"
    )
    parser.add_argument(
        "--user-id",
        "-u",
        help="Filter traces by user ID"
    )
    parser.add_argument(
        "--session-id",
        "-s",
        help="Filter traces by session ID"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Export traces from the last N hours"
    )
    parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Validate trace naming after export"
    )

    args = parser.parse_args()

    # Export traces
    result = export_traces(
        output_file=args.output,
        limit=args.limit,
        name_filter=args.name,
        tag_filter=args.tag,
        user_id_filter=args.user_id,
        session_id_filter=args.session_id,
        hours_back=args.hours,
    )

    if not result.get("success"):
        sys.exit(1)

    # Validate if requested
    if args.validate and result.get("exported_file"):
        validate_trace_naming(result["exported_file"])
