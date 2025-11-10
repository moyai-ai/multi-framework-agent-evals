"""
Export the latest trace from Langfuse for review.

This script fetches the most recent trace from Langfuse and exports it to a JSON file.
"""

import json
from datetime import datetime
from langfuse import Langfuse
from src.context import Config


def export_latest_trace():
    """Export the latest trace to JSON."""
    config = Config()

    if not config.LANGFUSE_ENABLED or not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
        print("❌ Langfuse is not configured. Please set credentials in .env file.")
        return

    # Initialize Langfuse client
    import os
    os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST

    # Use the sync API client
    from langfuse.client import FernLangfuse

    sync_api = FernLangfuse(
        x_langfuse_sdk_name="python",
        x_langfuse_sdk_version="2.0.0",
        x_langfuse_public_key=config.LANGFUSE_PUBLIC_KEY,
        username=config.LANGFUSE_PUBLIC_KEY,
        password=config.LANGFUSE_SECRET_KEY,
        base_url=config.LANGFUSE_HOST
    )

    print("Fetching latest trace from Langfuse...")

    # Fetch recent traces
    traces = sync_api.trace.get_many(limit=1)

    if not traces.data:
        print("❌ No traces found.")
        return

    latest_trace = traces.data[0]

    print(f"\n✓ Found trace: {latest_trace.name}")
    print(f"  - ID: {latest_trace.id}")
    print(f"  - User: {latest_trace.user_id}")
    print(f"  - Session: {latest_trace.session_id}")
    print(f"  - Tags: {', '.join(latest_trace.tags or [])}")
    print(f"  - Timestamp: {latest_trace.timestamp}")

    # Fetch full trace with observations
    trace_details = sync_api.trace.get(latest_trace.id)

    # Convert to dict for JSON export
    trace_data = {
        "id": trace_details.id,
        "name": trace_details.name,
        "user_id": trace_details.user_id,
        "session_id": trace_details.session_id,
        "timestamp": str(trace_details.timestamp),
        "tags": trace_details.tags,
        "metadata": trace_details.metadata,
        "version": trace_details.version,
        "input": trace_details.input,
        "output": trace_details.output,
        "observations": []
    }

    # Add observations (spans, generations, etc.)
    for obs in trace_details.observations:
        obs_data = {
            "id": obs.id,
            "type": obs.type,
            "name": obs.name,
            "start_time": str(obs.start_time),
            "end_time": str(obs.end_time) if obs.end_time else None,
            "input": obs.input,
            "output": obs.output,
            "metadata": obs.metadata,
            "level": obs.level,
            "status_message": obs.status_message
        }

        # Add model info for generations
        if obs.type == "GENERATION":
            obs_data["model"] = obs.model
            obs_data["model_parameters"] = obs.model_parameters
            obs_data["usage"] = obs.usage

        trace_data["observations"].append(obs_data)

    # Export to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trace_export_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(trace_data, f, indent=2, default=str)

    print(f"\n✓ Trace exported to: {filename}")
    print(f"  - Total observations: {len(trace_data['observations'])}")

    # Count observation types
    obs_types = {}
    for obs in trace_data['observations']:
        obs_type = obs['type']
        obs_types[obs_type] = obs_types.get(obs_type, 0) + 1

    print(f"  - Observation breakdown:")
    for obs_type, count in obs_types.items():
        print(f"    - {obs_type}: {count}")

    print(f"\n📊 You can now review the trace in: {filename}")


if __name__ == "__main__":
    export_latest_trace()
