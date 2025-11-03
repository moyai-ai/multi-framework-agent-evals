"""
Configuration and Pydantic models for the Unit Test Agent
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    VERBOSE: bool = os.getenv("VERBOSE", "true").lower() == "true"
    RUN_FULL_SCENARIOS: bool = os.getenv("RUN_FULL_SCENARIOS", "false").lower() == "true"


class FunctionInfo(BaseModel):
    """Represents a parsed Python function"""

    name: str
    module: str
    line_number: int
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    source_code: str
    is_async: bool = False
    decorators: List[str] = Field(default_factory=list)
    class_name: Optional[str] = None


class TestScenario(BaseModel):
    """Represents a single test scenario"""

    name: str
    description: str
    inputs: Dict[str, Any]
    expected_output: Any
    expected_exception: Optional[str] = None
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None


class TestPlan(BaseModel):
    """Represents a complete test plan for a function"""

    function_name: str
    module_path: str
    test_class_name: str
    scenarios: List[TestScenario]
    fixtures_needed: List[str] = Field(default_factory=list)
    imports_needed: List[str] = Field(default_factory=list)
    setup_code: Optional[str] = None
    mocks_needed: List[Dict[str, str]] = Field(default_factory=list)


class GeneratedTest(BaseModel):
    """Represents generated test code"""

    test_plan: TestPlan
    test_code: str
    file_path: str
    imports: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """Request to analyze code and generate tests"""

    repository_url: str
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    branch: str = "main"
    analysis_type: str = "all"  # 'all', 'single_function', 'single_file'


class AnalysisResult(BaseModel):
    """Result of code analysis and test generation"""

    request: AnalysisRequest
    functions_analyzed: List[FunctionInfo]
    generated_tests: List[GeneratedTest]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time: float = 0.0


class ScenarioExpectation(BaseModel):
    """Expected outcomes for scenario validation"""

    functions_found_min: int = 1
    test_plan_created: bool = True
    test_code_generated: bool = True
    test_scenarios_min: int = 1
    contains_imports: bool = True
    contains_assertions: bool = True
    message_contains: Optional[List[str]] = None


class ConversationTurn(BaseModel):
    """A single turn in a test scenario conversation"""

    user_input: str
    expected: ScenarioExpectation


class TestScenarioDefinition(BaseModel):
    """Complete test scenario definition from JSON"""

    name: str
    description: str
    initial_context: AnalysisRequest
    conversation: List[ConversationTurn]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result of executing a single conversation turn"""

    turn_number: int
    user_input: str
    crew_output: str
    result: Optional[AnalysisResult] = None
    validation_passed: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    execution_time: float = 0.0


class ScenarioReport(BaseModel):
    """Complete report for a test scenario execution"""

    scenario: TestScenarioDefinition
    turns: List[ExecutionResult]
    total_execution_time: float
    success: bool
    summary: str
