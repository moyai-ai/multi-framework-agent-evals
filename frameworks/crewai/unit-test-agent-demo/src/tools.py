"""
Custom tools for the Unit Test Agent
"""

import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import git
import astroid
from crewai.tools import BaseTool
from pydantic import Field

from .context import FunctionInfo


class GitHubFetcherTool(BaseTool):
    """Tool to fetch Python files from GitHub repositories"""

    name: str = "GitHub Fetcher"
    description: str = (
        "Fetches Python files from a GitHub repository. "
        "Input should be a JSON string with 'repository_url', 'branch' (optional, default 'main'), "
        "and 'file_path' (optional, fetches all .py files if not specified)."
    )

    def _run(self, repository_url: str, branch: str = "main", file_path: Optional[str] = None) -> str:
        """Fetch files from GitHub repository"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()

            # Clone repository
            repo = git.Repo.clone_from(repository_url, temp_dir, branch=branch, depth=1)

            if file_path:
                # Fetch specific file
                target_file = Path(temp_dir) / file_path
                if target_file.exists() and target_file.suffix == ".py":
                    content = target_file.read_text()
                    shutil.rmtree(temp_dir)
                    return f"Successfully fetched {file_path}:\n\n{content}"
                else:
                    shutil.rmtree(temp_dir)
                    return f"Error: File {file_path} not found or not a Python file"
            else:
                # Fetch all Python files
                python_files = list(Path(temp_dir).rglob("*.py"))
                if not python_files:
                    shutil.rmtree(temp_dir)
                    return "Error: No Python files found in repository"

                result = f"Found {len(python_files)} Python files:\n\n"
                for py_file in python_files[:10]:  # Limit to first 10 files
                    rel_path = py_file.relative_to(temp_dir)
                    result += f"- {rel_path}\n"

                if len(python_files) > 10:
                    result += f"\n... and {len(python_files) - 10} more files"

                shutil.rmtree(temp_dir)
                return result

        except git.GitCommandError as e:
            return f"Git error: {str(e)}"
        except Exception as e:
            return f"Error fetching repository: {str(e)}"


class ASTParserTool(BaseTool):
    """Tool to parse Python code and extract function information"""

    name: str = "AST Parser"
    description: str = (
        "Parses Python code using AST to extract function definitions, signatures, "
        "parameters, return types, and docstrings. Input should be Python source code as a string."
    )

    def _run(self, source_code: str, target_function: Optional[str] = None) -> str:
        """Parse Python code and extract function information"""
        try:
            module = astroid.parse(source_code)
            functions = []

            # Extract functions from module
            for node in module.body:
                if isinstance(node, astroid.FunctionDef):
                    func_info = self._extract_function_info(node, module.name)
                    if target_function is None or func_info["name"] == target_function:
                        functions.append(func_info)

                # Extract methods from classes
                elif isinstance(node, astroid.ClassDef):
                    for method in node.methods():
                        func_info = self._extract_function_info(method, module.name, node.name)
                        if target_function is None or func_info["name"] == target_function:
                            functions.append(func_info)

            if not functions:
                return "No functions found in the provided code"

            # Format output
            result = f"Found {len(functions)} function(s):\n\n"
            for func in functions:
                result += self._format_function_info(func)
                result += "\n" + "=" * 80 + "\n\n"

            return result

        except Exception as e:
            return f"Error parsing code: {str(e)}"

    def _extract_function_info(
        self, node: astroid.FunctionDef, module_name: str, class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract information from a function node"""
        # Extract parameters
        parameters = []
        if node.args:
            for arg in node.args.args:
                param_info = {"name": arg.name, "type": None, "default": None}

                # Get type annotation
                if arg.annotation:
                    param_info["type"] = arg.annotation.as_string()

                parameters.append(param_info)

            # Add defaults
            defaults = node.args.defaults or []
            for i, default in enumerate(defaults):
                param_idx = len(parameters) - len(defaults) + i
                if param_idx < len(parameters):
                    parameters[param_idx]["default"] = default.as_string()

        # Extract return type
        return_type = None
        if node.returns:
            return_type = node.returns.as_string()

        # Extract decorators
        decorators = [dec.as_string() for dec in node.decorators.nodes] if node.decorators else []

        return {
            "name": node.name,
            "module": module_name,
            "line_number": node.lineno,
            "parameters": parameters,
            "return_type": return_type,
            "docstring": node.doc_node.value if node.doc_node else None,
            "source_code": node.as_string(),
            "is_async": node.is_async(),
            "decorators": decorators,
            "class_name": class_name,
        }

    def _format_function_info(self, func: Dict[str, Any]) -> str:
        """Format function information for display"""
        result = f"Function: {func['name']}\n"

        if func["class_name"]:
            result += f"Class: {func['class_name']}\n"

        result += f"Line: {func['line_number']}\n"

        if func["decorators"]:
            result += f"Decorators: {', '.join(func['decorators'])}\n"

        result += f"Async: {func['is_async']}\n"

        # Parameters
        if func["parameters"]:
            result += "Parameters:\n"
            for param in func["parameters"]:
                param_str = f"  - {param['name']}"
                if param["type"]:
                    param_str += f": {param['type']}"
                if param["default"]:
                    param_str += f" = {param['default']}"
                result += param_str + "\n"

        # Return type
        if func["return_type"]:
            result += f"Return Type: {func['return_type']}\n"

        # Docstring
        if func["docstring"]:
            result += f"Docstring:\n  {func['docstring'][:200]}"
            if len(func["docstring"]) > 200:
                result += "..."
            result += "\n"

        return result


class TestPlanGeneratorTool(BaseTool):
    """Tool to generate structured test plans"""

    name: str = "Test Plan Generator"
    description: str = (
        "Generates a structured test plan for a function including test scenarios, "
        "edge cases, and required fixtures. Input should be function information as a string."
    )

    def _run(self, function_info: str) -> str:
        """Generate test plan - delegates to LLM via agent"""
        return (
            "This tool should be used with an LLM agent to generate comprehensive test plans. "
            "The agent will analyze the function and create scenarios covering:\n"
            "1. Happy path cases\n"
            "2. Edge cases\n"
            "3. Error handling\n"
            "4. Boundary conditions\n"
            f"\nFunction to analyze:\n{function_info}"
        )


class TestCodeGeneratorTool(BaseTool):
    """Tool to generate pytest code from test plans"""

    name: str = "Test Code Generator"
    description: str = (
        "Generates pytest-compatible test code from a test plan. "
        "Input should be a test plan as a string."
    )

    def _run(self, test_plan: str) -> str:
        """Generate pytest code - delegates to LLM via agent"""
        return (
            "This tool should be used with an LLM agent to generate pytest code. "
            "The agent will create:\n"
            "1. Test function definitions\n"
            "2. Fixtures if needed\n"
            "3. Assertions and validation\n"
            "4. Proper imports\n"
            f"\nTest plan to implement:\n{test_plan}"
        )


# Tool instances for use in agents
github_fetcher_tool = GitHubFetcherTool()
ast_parser_tool = ASTParserTool()
test_plan_generator_tool = TestPlanGeneratorTool()
test_code_generator_tool = TestCodeGeneratorTool()
