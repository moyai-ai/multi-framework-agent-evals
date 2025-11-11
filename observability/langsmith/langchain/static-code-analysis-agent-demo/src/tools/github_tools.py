"""
GitHub tools using MCP functions for repository analysis.
"""

import json
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
import httpx


# MCP Function definitions (these would normally come from the MCP server)
# In production, these would be dynamically loaded from the MCP server
MCP_FUNCTIONS = {
    "GITHUB__GET_REPOSITORY": "mcp__aci-mcp-unified__ACI_EXECUTE_FUNCTION",
    "GITHUB__LIST_REPOSITORY_FILES": "mcp__aci-mcp-unified__ACI_EXECUTE_FUNCTION",
    "GITHUB__GET_FILE_CONTENT": "mcp__aci-mcp-unified__ACI_EXECUTE_FUNCTION",
}


class GitHubMCPClient:
    """Client for interacting with GitHub via MCP functions."""

    def __init__(self):
        """Initialize the GitHub MCP client."""
        self.base_url = "https://api.github.com"

    async def execute_mcp_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute an MCP function (simulated for demo)."""
        # In production, this would call the actual MCP server
        # For demo purposes, we'll simulate the responses
        if function_name == "GITHUB__GET_REPOSITORY":
            return await self._mock_get_repository(arguments)
        elif function_name == "GITHUB__LIST_BRANCHES":
            return await self._mock_list_files(arguments)
        elif function_name == "GITHUB__GET_FILE_CONTENT":
            return await self._mock_get_file_content(arguments)
        else:
            raise ValueError(f"Unknown MCP function: {function_name}")

    async def _mock_get_repository(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock repository information."""
        path = args.get("path", {})
        return {
            "name": path.get("repo", "unknown"),
            "owner": {"login": path.get("owner", "unknown")},
            "description": "Mock repository for demo",
            "language": "Python",
            "default_branch": "main",
            "visibility": "public"
        }

    async def _mock_list_files(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock file listing."""
        print(f"DEBUG _mock_list_files called with args: {args}")

        # Return different files based on repository
        path = args.get("path", {})
        repo_name = path.get("repo", "")

        if repo_name == "legacy-code":
            # Files for code quality scenario
            files = [
                {"path": "src/legacy_processor.py", "type": "file", "size": 2048},
                {"path": "src/utils.py", "type": "file", "size": 512},
                {"path": "requirements.txt", "type": "file", "size": 256}
            ]
        elif repo_name == "outdated-deps" or repo_name == "dependency-app":
            # Files for dependency scenario
            files = [
                {"path": "requirements.txt", "type": "file", "size": 512},
                {"path": "package.json", "type": "file", "size": 256},
                {"path": "src/main.py", "type": "file", "size": 1024}
            ]
        else:
            # Default files for security scenario (vulnerable-app)
            files = [
                {"path": "src/main.py", "type": "file", "size": 1024},
                {"path": "src/database.py", "type": "file", "size": 2048},
                {"path": "src/api.py", "type": "file", "size": 1536},
                {"path": "requirements.txt", "type": "file", "size": 256},
                {"path": "package.json", "type": "file", "size": 512},
                {"path": ".env.example", "type": "file", "size": 128}
            ]

        print(f"DEBUG _mock_list_files returning {len(files)} files")
        return files

    async def _mock_get_file_content(self, args: Dict[str, Any]) -> str:
        """Mock file content."""
        file_path = args.get("path", {}).get("path", "")

        # Return different content based on file
        if "legacy_processor.py" in file_path:
            # Code quality scenario - long function with issues
            return '''def process_all_data(data_list, config, user_settings, cache, db_connection, logger, metrics, feature_flags):
    # This function is way too long - over 100 lines
    results = []
    errors = []

    # TODO: Refactor this monstrosity
    for item in data_list:
        try:
            if item['type'] == 'user':
                if item['age'] > 18:
                    if item['country'] == 'US':
                        if item['premium']:
                            if feature_flags.get('new_algorithm'):
                                # Deep nesting - hard to read
                                result = process_premium_us_adult_new(item)
                            else:
                                result = process_premium_us_adult_old(item)
                        else:
                            result = process_standard_us_adult(item)
                    else:
                        result = process_international_adult(item)
                else:
                    result = process_minor(item)
            elif item['type'] == 'business':
                # Magic number alert
                if item['revenue'] > 1000000:
                    result = process_enterprise(item)
                elif item['revenue'] > 50000:
                    result = process_small_business(item)
                else:
                    result = process_startup(item)
            else:
                result = process_unknown(item)

            results.append(result)

        except Exception:
            # Empty exception handler - bad practice
            pass

        except ValueError:
            pass  # Another empty handler

    return results
'''
        elif "utils.py" in file_path:
            # Code quality scenario - utilities with quality issues
            return '''def calculate_score(value):
    # TODO: Implement proper scoring algorithm
    return value * 3.14159  # Magic number

def validate_input(data):
    try:
        return process_data(data)
    except:
        pass  # Silently ignore all errors

def check_status():
    # TODO: Add status check logic
    return True
'''
        elif "database.py" in file_path:
            # Security scenario - SQL injection
            return '''import sqlite3

def get_user(user_id):
    """Get user from database - VULNERABLE TO SQL INJECTION"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

def update_user(user_id, name):
    """Update user - ALSO VULNERABLE"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Another SQL injection
    query = f"UPDATE users SET name = '{name}' WHERE id = {user_id}"
    cursor.execute(query)
    conn.commit()
'''
        elif "api.py" in file_path:
            # Security scenario - XSS and command injection
            return '''from flask import Flask, request
import os

app = Flask(__name__)

# Hardcoded secret - security issue
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

@app.route('/search')
def search():
    """Search endpoint - VULNERABLE TO XSS"""
    query = request.args.get('q', '')
    # XSS vulnerability - unsanitized output
    return f"<h1>Search results for: {query}</h1>"

@app.route('/exec')
def execute():
    """Command execution - VULNERABLE TO COMMAND INJECTION"""
    cmd = request.args.get('cmd', '')
    # Command injection vulnerability
    result = os.system(cmd)
    return {"result": result}
'''
        elif "requirements.txt" in file_path:
            # Dependency scenario - vulnerable packages
            return """flask==1.1.2
requests==2.20.0
django==2.2.10
pyyaml==5.1
sqlalchemy==1.3.0
"""
        elif "package.json" in file_path:
            # Dependency scenario - Node packages
            return """{
  "name": "demo-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "4.16.0",
    "lodash": "4.17.0",
    "moment": "2.24.0"
  }
}
"""
        else:
            return "# Mock file content for demo"


# Create a global client instance
github_client = GitHubMCPClient()


@tool
async def fetch_repository_info(owner: str, repo: str) -> Dict[str, Any]:
    """
    Fetch information about a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        Repository metadata
    """
    try:
        result = await github_client.execute_mcp_function(
            "GITHUB__GET_REPOSITORY",
            {
                "path": {
                    "owner": owner,
                    "repo": repo
                }
            }
        )
        return {
            "success": True,
            "repository": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def list_repository_files(
    owner: str,
    repo: str,
    path: str = "",
    file_extension: Optional[str] = None
) -> Dict[str, Any]:
    """
    List files in a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        path: Path within repository (default: root)
        file_extension: Filter by file extension (e.g., 'py', 'js')

    Returns:
        List of files in the repository
    """
    try:
        print(f"DEBUG list_repository_files called: owner={owner}, repo={repo}, ext={file_extension}")
        result = await github_client.execute_mcp_function(
            "GITHUB__LIST_BRANCHES",  # Using branches as proxy for files in demo
            {
                "path": {
                    "owner": owner,
                    "repo": repo
                }
            }
        )

        print(f"DEBUG MCP function returned: {type(result)}, is list: {isinstance(result, list)}")
        files = result if isinstance(result, list) else []
        print(f"DEBUG Files before filtering: {len(files)}")

        # Filter by extension if provided
        if file_extension:
            files = [f for f in files if f.get("path", "").endswith(f".{file_extension}")]
            print(f"DEBUG Files after filtering by .{file_extension}: {len(files)}")

        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def get_file_content(
    owner: str,
    repo: str,
    file_path: str
) -> Dict[str, Any]:
    """
    Get the content of a file from a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        file_path: Path to the file in the repository

    Returns:
        File content and metadata
    """
    try:
        content = await github_client.execute_mcp_function(
            "GITHUB__GET_FILE_CONTENT",
            {
                "path": {
                    "owner": owner,
                    "repo": repo,
                    "path": file_path
                }
            }
        )

        # Detect language from file extension
        extension = file_path.split('.')[-1] if '.' in file_path else ''
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'go': 'go',
            'rs': 'rust',
            'rb': 'ruby',
            'php': 'php',
            'c': 'c',
            'cpp': 'cpp',
            'cs': 'csharp'
        }
        language = language_map.get(extension, 'unknown')

        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "language": language,
            "size": len(content),
            "lines": content.count('\n') + 1
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def parse_repository_url(url: str) -> Dict[str, str]:
    """
    Parse a GitHub repository URL to extract owner and repo name.

    Args:
        url: GitHub repository URL

    Returns:
        Dictionary with owner and repo name
    """
    # Handle various GitHub URL formats
    url = url.replace("https://github.com/", "")
    url = url.replace("http://github.com/", "")
    url = url.replace("git@github.com:", "")
    url = url.replace(".git", "")

    parts = url.split("/")
    if len(parts) >= 2:
        return {
            "owner": parts[0],
            "repo": parts[1]
        }
    else:
        return {
            "error": "Invalid repository URL format"
        }