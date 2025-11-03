#!/usr/bin/env python
"""Test scenario runner to verify imports and structure without API calls."""

import sys
import os

# Add the parent directory to the path to fix imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports...")

try:
    from src.scenarios.demo_runner import DemoRunner
    print("✓ Successfully imported DemoRunner")
except ImportError as e:
    print(f"✗ Failed to import DemoRunner: {e}")
    sys.exit(1)

try:
    from src.scenarios.sample_leads import (
        get_sample_leads,
        get_high_priority_leads,
        get_technical_leads,
        get_unqualified_leads
    )
    print("✓ Successfully imported sample_leads functions")
except ImportError as e:
    print(f"✗ Failed to import sample_leads: {e}")
    sys.exit(1)

try:
    from src.agent.models import Lead, QualificationAnalysis, QualificationScore
    print("✓ Successfully imported models")
except ImportError as e:
    print(f"✗ Failed to import models: {e}")
    sys.exit(1)

try:
    from src.agent.lead_qualifier import LeadQualificationAgent
    print("✓ Successfully imported LeadQualificationAgent")
except ImportError as e:
    print(f"✗ Failed to import LeadQualificationAgent: {e}")
    sys.exit(1)

print("\nTesting sample data...")
try:
    leads = get_sample_leads()
    print(f"✓ Got {len(leads)} sample leads")

    high_priority = get_high_priority_leads()
    print(f"✓ Got {len(high_priority)} high priority leads")

    technical = get_technical_leads()
    print(f"✓ Got {len(technical)} technical leads")

    unqualified = get_unqualified_leads()
    print(f"✓ Got {len(unqualified)} unqualified leads")

    # Display first lead
    if leads:
        lead = leads[0]
        print(f"\nFirst sample lead:")
        print(f"  Name: {lead.name}")
        print(f"  Email: {lead.email}")
        print(f"  Company: {lead.company}")
        print(f"  Title: {lead.title}")

except Exception as e:
    print(f"✗ Error with sample data: {e}")
    sys.exit(1)

print("\nTesting model creation...")
try:
    test_lead = Lead(
        name="Test Person",
        email="test@example.com",
        company="Test Company",
        title="Test Title"
    )
    print(f"✓ Created test lead: {test_lead.name}")
except Exception as e:
    print(f"✗ Error creating lead: {e}")
    sys.exit(1)

print("\n✅ All imports and basic functionality verified!")
print("\nNote: To run actual demos with AI functionality, you'll need:")
print("1. Valid OpenAI API key in .env file")
print("2. Valid Linkup.so API key in .env file")
print("\nYou can then run: uv run python src/run_scenario.py [single|batch|priority|comparison|all]")