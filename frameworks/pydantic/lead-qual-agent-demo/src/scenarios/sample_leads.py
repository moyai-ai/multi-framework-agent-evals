"""Sample leads for demonstration purposes."""

from typing import List
from ..agent.models import Lead


def get_sample_leads() -> List[Lead]:
    """
    Get a list of sample leads for demonstration.

    These are fictional leads designed to showcase different qualification scenarios.
    """
    return [
        # High-value enterprise lead
        Lead(
            name="Sarah Chen",
            email="s.chen@techcorp.example.com",
            company="TechCorp Global",
            title="VP of Engineering",
            linkedin_url="https://linkedin.com/in/sarahchen-example",
            source="conference",
            additional_info={
                "met_at": "PyCon 2024",
                "interested_in": "ML observability tools",
                "company_size": "5000+ employees"
            }
        ),

        # Mid-market technical lead
        Lead(
            name="Michael Rodriguez",
            email="mrodriguez@dataflow.example.com",
            company="DataFlow Analytics",
            title="Senior Data Scientist",
            linkedin_url="https://linkedin.com/in/mrodriguez-example",
            source="webinar",
            additional_info={
                "webinar_topic": "Production ML Monitoring",
                "engagement": "Asked 3 technical questions",
                "current_stack": "Python, TensorFlow, AWS"
            }
        ),

        # Startup founder - high potential
        Lead(
            name="Emily Watson",
            email="emily@aistart.example.com",
            company="AIStart",
            title="Co-Founder & CTO",
            source="product_hunt",
            additional_info={
                "company_stage": "Series A",
                "team_size": "15 engineers",
                "looking_for": "Developer productivity tools"
            }
        ),

        # Low qualification - wrong department
        Lead(
            name="James Thompson",
            email="jthompson@retailco.example.com",
            company="RetailCo International",
            title="Marketing Manager",
            source="cold_outreach",
            additional_info={
                "industry": "Retail",
                "department": "Marketing"
            }
        ),

        # Unknown company - needs research
        Lead(
            name="Alex Kumar",
            email="alex.kumar@email.example.com",
            company=None,
            title="Software Engineer",
            source="github",
            additional_info={
                "github_projects": "ML pipeline tools, data validation libraries",
                "contributions": "Active open source contributor"
            }
        ),

        # Enterprise decision maker
        Lead(
            name="Patricia Anderson",
            email="panderson@financecorp.example.com",
            company="FinanceCorp Solutions",
            title="Chief Technology Officer",
            linkedin_url="https://linkedin.com/in/panderson-cto",
            source="referral",
            additional_info={
                "referred_by": "Current customer - TechVentures",
                "pain_point": "Need better ML model monitoring",
                "budget_authority": "Yes",
                "timeline": "Q1 2025"
            }
        ),

        # Technical influencer
        Lead(
            name="David Kim",
            email="dkim@cloudnative.example.com",
            company="CloudNative Systems",
            title="Principal Engineer",
            source="blog_subscriber",
            additional_info={
                "engagement": "Regular blog reader, newsletter subscriber",
                "expertise": "Distributed systems, ML infrastructure",
                "influence": "Tech lead for 50+ engineer org"
            }
        ),

        # Unqualified - student
        Lead(
            name="Jessica Lee",
            email="jlee@university.edu",
            company="State University",
            title="Graduate Student",
            source="academic_program",
            additional_info={
                "program": "MS Computer Science",
                "research": "ML fairness and bias"
            }
        )
    ]


def get_high_priority_leads() -> List[Lead]:
    """Get leads that should qualify as high priority."""
    leads = get_sample_leads()
    # Return enterprise and startup CTOs
    return [leads[0], leads[2], leads[5]]


def get_technical_leads() -> List[Lead]:
    """Get leads with strong technical backgrounds."""
    leads = get_sample_leads()
    # Return technical roles
    return [leads[1], leads[4], leads[6]]


def get_unqualified_leads() -> List[Lead]:
    """Get leads that should not qualify."""
    leads = get_sample_leads()
    # Return non-technical and student leads
    return [leads[3], leads[7]]