"""
Custom tools for the Landing Page Generator agents.

This module provides tools for searching, file operations, template management, and content generation.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from crewai.tools import tool
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from jinja2 import Template


class SearchInput(BaseModel):
    """Input model for search operations."""
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum number of results")


class FileInput(BaseModel):
    """Input model for file operations."""
    file_path: str = Field(description="Path to the file")
    content: Optional[str] = Field(default=None, description="Content to write")


class TemplateInput(BaseModel):
    """Input model for template operations."""
    template_name: str = Field(description="Name of the template")
    variables: Optional[Dict[str, Any]] = Field(default={}, description="Variables for template rendering")


class ContentInput(BaseModel):
    """Input model for content generation."""
    section: str = Field(description="Section to generate content for")
    context: Dict[str, Any] = Field(description="Context for content generation")


@tool
def SearchTool(query: str, max_results: int = 5) -> str:
    """
    Search the internet for information.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        Search results as a formatted string
    """
    try:
        # In a real implementation, this would use a search API
        # For demo purposes, we'll return mock results
        results = []
        for i in range(min(max_results, 3)):
            results.append({
                "title": f"Result {i+1} for '{query}'",
                "snippet": f"This is a sample snippet for the search result about {query}...",
                "url": f"https://example.com/result{i+1}"
            })

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching: {str(e)}"


@tool
def WebScrapingTool(url: str) -> str:
    """
    Scrape content from a website.

    Args:
        url: The URL to scrape

    Returns:
        Scraped content as text
    """
    try:
        # Handle mock URLs from SearchTool
        if 'example.com' in url:
            # Return mock content for demo/testing purposes
            mock_content = f"""
            Sample content from {url}

            This is a comprehensive article about task management and productivity tools.
            Task management applications help teams organize their work, track progress,
            and collaborate more effectively. Key features include task assignment,
            deadline tracking, progress monitoring, and team communication.

            Popular task management tools offer features like:
            - Real-time collaboration
            - Mobile apps for on-the-go access
            - Integration with other productivity tools
            - Customizable workflows
            - Reporting and analytics

            The target audience for these tools typically includes project managers,
            team leads, and organizations looking to improve productivity and collaboration.
            """
            return mock_content.strip()

        # Basic web scraping implementation for real URLs
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Limit to first 2000 characters for processing
        return text[:2000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


@tool
def FileOperationsTool(operation: str, file_path: str, content: Optional[str] = None) -> str:
    """
    Perform file operations (read, write, list).

    Args:
        operation: The operation to perform ('read', 'write', 'list')
        file_path: Path to the file or directory
        content: Content to write (for write operation)

    Returns:
        Result of the operation
    """
    try:
        # Ensure operations are within allowed directories
        allowed_dirs = ['./templates', './output', './workdir']
        file_path = Path(file_path).resolve()

        # Check if path is within allowed directories
        is_allowed = any(
            str(file_path).startswith(str(Path(d).resolve()))
            for d in allowed_dirs
        )

        if not is_allowed and operation != 'list':
            return f"Error: Access denied to {file_path}"

        if operation == 'read':
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return f.read()
            else:
                return f"Error: File {file_path} not found"

        elif operation == 'write':
            if content is None:
                return "Error: Content is required for write operation"

            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"

        elif operation == 'list':
            if file_path.is_dir():
                files = [str(f.name) for f in file_path.iterdir()]
                return json.dumps(files, indent=2)
            else:
                return f"Error: {file_path} is not a directory"

        else:
            return f"Error: Unknown operation {operation}"

    except Exception as e:
        return f"Error in file operation: {str(e)}"


@tool
def TemplateManagerTool(action: str, template_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Manage and work with templates.

    Args:
        action: The action to perform ('list', 'load', 'render')
        template_name: Name of the template
        variables: Variables for template rendering

    Returns:
        Result of the template operation
    """
    try:
        templates_dir = Path('./templates')

        if action == 'list':
            if templates_dir.exists():
                templates = []
                for template_dir in templates_dir.iterdir():
                    if template_dir.is_dir():
                        templates.append({
                            "name": template_dir.name,
                            "files": [f.name for f in template_dir.iterdir() if f.is_file()]
                        })
                return json.dumps(templates, indent=2)
            else:
                return "No templates directory found"

        elif action == 'load':
            template_path = templates_dir / template_name
            if template_path.exists():
                # Look for index.html or main HTML file
                html_files = list(template_path.glob('*.html'))
                if html_files:
                    with open(html_files[0], 'r') as f:
                        return f.read()
                else:
                    return f"No HTML files found in template {template_name}"
            else:
                return f"Template {template_name} not found"

        elif action == 'render':
            if variables is None:
                variables = {}

            template_path = templates_dir / template_name
            if template_path.exists():
                html_files = list(template_path.glob('*.html'))
                if html_files:
                    with open(html_files[0], 'r') as f:
                        template_content = f.read()

                    # Use Jinja2 for template rendering
                    template = Template(template_content)
                    rendered = template.render(**variables)
                    return rendered
                else:
                    return f"No HTML files found in template {template_name}"
            else:
                return f"Template {template_name} not found"

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Error in template operation: {str(e)}"


@tool
def ContentGeneratorTool(section: str, context: Dict[str, Any]) -> str:
    """
    Generate content for specific sections of the landing page.

    Args:
        section: The section to generate content for
        context: Context information for content generation

    Returns:
        Generated content as JSON
    """
    try:
        # This is a simplified content generator
        # In production, this could use AI or templates

        if section == 'hero':
            content = {
                "headline": f"Transform Your {context.get('industry', 'Business')} Today",
                "subheadline": f"The ultimate solution for {context.get('target_audience', 'professionals')}",
                "cta_text": "Get Started Now",
                "cta_url": "#signup"
            }

        elif section == 'features':
            features = []
            for i in range(3):
                features.append({
                    "title": f"Feature {i+1}",
                    "description": f"Description of amazing feature {i+1}",
                    "icon": "star"
                })
            content = {"features": features}

        elif section == 'benefits':
            benefits = [
                "Save time and increase productivity",
                "Reduce costs by up to 50%",
                "Improve customer satisfaction",
                "Scale your business effortlessly"
            ]
            content = {"benefits": benefits}

        elif section == 'testimonials':
            testimonials = [
                {
                    "name": "John Doe",
                    "role": "CEO, TechCorp",
                    "content": "This solution transformed our business completely.",
                    "rating": 5
                },
                {
                    "name": "Jane Smith",
                    "role": "Marketing Director",
                    "content": "Best investment we've made this year.",
                    "rating": 5
                }
            ]
            content = {"testimonials": testimonials}

        elif section == 'faq':
            faqs = [
                {
                    "question": "How does it work?",
                    "answer": "Our solution is simple and intuitive to use."
                },
                {
                    "question": "What's included?",
                    "answer": "Everything you need to get started and succeed."
                },
                {
                    "question": "Is there support?",
                    "answer": "Yes, we provide 24/7 customer support."
                }
            ]
            content = {"faq": faqs}

        else:
            content = {"error": f"Unknown section: {section}"}

        return json.dumps(content, indent=2)

    except Exception as e:
        return f"Error generating content: {str(e)}"


class HTMLValidator:
    """Utility class for validating HTML content."""

    @staticmethod
    def validate_html(html_content: str) -> Dict[str, Any]:
        """
        Validate HTML content for common issues.

        Args:
            html_content: The HTML content to validate

        Returns:
            Validation results
        """
        issues = []
        warnings = []

        # Check for basic HTML structure
        if not re.search(r'<!DOCTYPE\s+html>', html_content, re.IGNORECASE):
            issues.append("Missing DOCTYPE declaration")

        if not re.search(r'<html[\s>]', html_content, re.IGNORECASE):
            issues.append("Missing <html> tag")

        if not re.search(r'<head[\s>]', html_content, re.IGNORECASE):
            issues.append("Missing <head> tag")

        if not re.search(r'<body[\s>]', html_content, re.IGNORECASE):
            issues.append("Missing <body> tag")

        # Check for meta tags
        if not re.search(r'<meta\s+charset=', html_content, re.IGNORECASE):
            warnings.append("Missing charset meta tag")

        if not re.search(r'<meta\s+name="viewport"', html_content, re.IGNORECASE):
            warnings.append("Missing viewport meta tag for responsive design")

        # Check for title
        if not re.search(r'<title>.*</title>', html_content, re.IGNORECASE):
            issues.append("Missing <title> tag")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


@tool
def ValidateHTMLTool(html_content: str) -> str:
    """
    Validate HTML content.

    Args:
        html_content: The HTML content to validate

    Returns:
        Validation results as JSON
    """
    validator = HTMLValidator()
    results = validator.validate_html(html_content)
    return json.dumps(results, indent=2)