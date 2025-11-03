"""
Unit tests for custom tools
"""

import pytest
from src.tools import (
    GitHubFetcherTool,
    ASTParserTool,
    TestPlanGeneratorTool,
    TestCodeGeneratorTool,
)


@pytest.mark.unit
class TestASTParserTool:
    """Tests for the AST Parser Tool"""

    def test_parse_simple_function(self, sample_python_code):
        """Test parsing a simple function"""
        tool = ASTParserTool()
        result = tool._run(sample_python_code, target_function="calculate_discount")

        assert "calculate_discount" in result
        assert "price" in result
        assert "discount_percent" in result
        assert "float" in result

    def test_parse_all_functions(self, sample_python_code):
        """Test parsing all functions in code"""
        tool = ASTParserTool()
        result = tool._run(sample_python_code)

        assert "calculate_discount" in result
        assert "add_item" in result
        assert "get_total" in result
        assert "Found 3 function(s)" in result

    def test_parse_class_method(self, sample_python_code):
        """Test parsing a class method"""
        tool = ASTParserTool()
        result = tool._run(sample_python_code, target_function="add_item")

        assert "add_item" in result
        assert "ShoppingCart" in result or "Class:" in result

    def test_parse_with_type_hints(self, sample_python_code):
        """Test that type hints are extracted"""
        tool = ASTParserTool()
        result = tool._run(sample_python_code, target_function="calculate_discount")

        assert "float" in result
        assert "Return Type" in result

    def test_parse_with_docstring(self, sample_python_code):
        """Test that docstrings are extracted"""
        tool = ASTParserTool()
        result = tool._run(sample_python_code, target_function="calculate_discount")

        assert "Docstring" in result
        assert "Calculate the discounted price" in result

    def test_parse_invalid_code(self):
        """Test parsing invalid Python code"""
        tool = ASTParserTool()
        invalid_code = "def invalid function syntax"
        result = tool._run(invalid_code)

        assert "Error parsing code" in result

    def test_parse_no_functions(self):
        """Test parsing code with no functions"""
        tool = ASTParserTool()
        code_without_functions = "x = 42\ny = 'hello'"
        result = tool._run(code_without_functions)

        assert "No functions found" in result


@pytest.mark.unit
class TestGitHubFetcherTool:
    """Tests for the GitHub Fetcher Tool"""

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        tool = GitHubFetcherTool()
        assert tool.name == "GitHub Fetcher"
        assert "GitHub repository" in tool.description

    def test_fetch_with_mock(self, mock_git_repo):
        """Test fetching from GitHub with mocked git"""
        tool = GitHubFetcherTool()
        result = tool._run("https://github.com/test/repo")

        # Should not error with mock
        assert isinstance(result, str)


@pytest.mark.unit
class TestTestPlanGeneratorTool:
    """Tests for the Test Plan Generator Tool"""

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        tool = TestPlanGeneratorTool()
        assert tool.name == "Test Plan Generator"
        assert "test plan" in tool.description.lower()

    def test_tool_returns_guidance(self, sample_function_info):
        """Test that tool returns guidance for LLM"""
        tool = TestPlanGeneratorTool()
        result = tool._run(str(sample_function_info))

        assert "test plan" in result.lower()
        assert "scenarios" in result.lower() or "edge cases" in result.lower()


@pytest.mark.unit
class TestTestCodeGeneratorTool:
    """Tests for the Test Code Generator Tool"""

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        tool = TestCodeGeneratorTool()
        assert tool.name == "Test Code Generator"
        assert "pytest" in tool.description.lower()

    def test_tool_returns_guidance(self, sample_test_plan):
        """Test that tool returns guidance for LLM"""
        tool = TestCodeGeneratorTool()
        result = tool._run(str(sample_test_plan))

        assert "pytest" in result.lower()
        assert "test" in result.lower()
