"""Framework detection tool using tree-sitter analysis."""

from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, asdict
from .tree_sitter_parser import find_imports, find_function_calls, find_class_definitions
from .package_analyzer import extract_package_versions, get_framework_version


@dataclass
class FrameworkInfo:
    """Information about a detected framework."""
    name: str
    version: str
    files: List[str]
    entry_points: List[str]  # Files where agents are instantiated
    agent_classes: List[str]  # Agent class names found
    confidence: float  # 0.0 to 1.0


# Framework detection rules
FRAMEWORK_PATTERNS = {
    "langchain": {
        "import_patterns": ["langchain", "langchain_openai", "langchain_anthropic", "langchain_community"],
        "class_patterns": ["ChatOpenAI", "OpenAI", "ChatAnthropic", "Agent", "AgentExecutor"],
        "function_patterns": ["create_react_agent", "create_openai_functions_agent", "create_structured_chat_agent"],
    },
    "langgraph": {
        "import_patterns": ["langgraph"],
        "class_patterns": ["StateGraph", "MessageGraph", "CompiledGraph"],
        "function_patterns": ["add_node", "add_edge", "compile"],
    },
    "openai-agents": {
        "import_patterns": ["openai"],
        "class_patterns": ["Agent", "Runner", "Swarm"],
        "function_patterns": [],
    },
    "pydantic-ai": {
        "import_patterns": ["pydantic_ai"],
        "class_patterns": ["Agent"],
        "function_patterns": [],
    },
    "crewai": {
        "import_patterns": ["crewai"],
        "class_patterns": ["Agent", "Task", "Crew"],
        "function_patterns": [],
    },
    "claude-agents": {
        "import_patterns": ["claude_agent_sdk", "anthropic.agents"],
        "class_patterns": ["ClaudeAgent", "Agent"],
        "function_patterns": [],
    },
    "autogen": {
        "import_patterns": ["autogen"],
        "class_patterns": ["AssistantAgent", "UserProxyAgent", "ConversableAgent"],
        "function_patterns": [],
    },
}


def detect_frameworks(args: dict) -> dict:
    """Detect agent frameworks used in a codebase.

    Args for the agent SDK @tool:
        codebase_path: str - Path to the codebase root

    Returns:
        dict with:
            - success: bool
            - frameworks: List[FrameworkInfo]
            - error: Optional[str]
    """
    codebase_path = Path(args["codebase_path"])

    try:
        # Find all Python files
        python_files = list(codebase_path.rglob("*.py"))

        # Get package versions
        versions_result = extract_package_versions({"codebase_path": str(codebase_path)})
        package_versions = versions_result.get("packages", {})

        detected_frameworks = {}

        # Analyze each Python file
        for py_file in python_files:
            # Skip virtual environments and test files
            if "venv" in str(py_file) or ".venv" in str(py_file) or "test" in str(py_file):
                continue

            try:
                # Get imports
                imports_result = find_imports({"file_path": str(py_file)})
                if not imports_result["success"]:
                    continue

                imports = imports_result["imports"]
                import_modules = {imp["module"] for imp in imports}

                # Get class definitions
                classes_result = find_class_definitions({"file_path": str(py_file)})
                classes = classes_result.get("classes", []) if classes_result["success"] else []
                class_names = {cls["name"] for cls in classes}

                # Check against framework patterns
                for framework, patterns in FRAMEWORK_PATTERNS.items():
                    confidence = 0.0
                    matches = []

                    # Check imports
                    for import_pattern in patterns["import_patterns"]:
                        for import_module in import_modules:
                            if import_pattern in import_module:
                                confidence += 0.5
                                matches.append(f"import {import_module}")
                                break

                    # Check class patterns
                    for class_pattern in patterns["class_patterns"]:
                        # Check if class is instantiated (function calls)
                        calls_result = find_function_calls({
                            "file_path": str(py_file),
                            "pattern": class_pattern
                        })
                        if calls_result["success"] and calls_result["calls"]:
                            confidence += 0.3
                            matches.append(f"call {class_pattern}")

                    # Check function patterns
                    for func_pattern in patterns["function_patterns"]:
                        calls_result = find_function_calls({
                            "file_path": str(py_file),
                            "pattern": func_pattern
                        })
                        if calls_result["success"] and calls_result["calls"]:
                            confidence += 0.2
                            matches.append(f"call {func_pattern}")

                    # If framework detected, add to results
                    if confidence > 0:
                        if framework not in detected_frameworks:
                            # Get version from package info
                            version = "*"
                            for pkg_name, pkg_info in package_versions.items():
                                if framework.replace("-", "_") in pkg_name or framework.replace("-", "") in pkg_name:
                                    version = pkg_info["version"]
                                    break

                            detected_frameworks[framework] = {
                                "name": framework,
                                "version": version,
                                "files": [],
                                "entry_points": [],
                                "agent_classes": set(),
                                "confidence": 0.0,
                                "matches": set()
                            }

                        # Update framework info
                        fw_info = detected_frameworks[framework]
                        fw_info["files"].append(str(py_file))
                        fw_info["confidence"] = max(fw_info["confidence"], confidence)
                        fw_info["matches"].update(matches)

                        # Add agent classes found
                        for class_pattern in patterns["class_patterns"]:
                            calls_result = find_function_calls({
                                "file_path": str(py_file),
                                "pattern": class_pattern
                            })
                            if calls_result["success"] and calls_result["calls"]:
                                fw_info["entry_points"].append(str(py_file))
                                fw_info["agent_classes"].add(class_pattern)

            except Exception as e:
                # Skip files that can't be parsed
                continue

        # Convert to FrameworkInfo objects
        frameworks = []
        for fw_name, fw_data in detected_frameworks.items():
            # Normalize confidence to 0.0-1.0
            confidence = min(fw_data["confidence"], 1.0)

            frameworks.append(FrameworkInfo(
                name=fw_name,
                version=fw_data["version"],
                files=list(set(fw_data["files"])),
                entry_points=list(set(fw_data["entry_points"])),
                agent_classes=list(fw_data["agent_classes"]),
                confidence=confidence
            ))

        return {
            "success": True,
            "frameworks": [asdict(fw) for fw in frameworks],
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "frameworks": [],
            "error": str(e)
        }


def get_framework_details(args: dict) -> dict:
    """Get detailed information about a specific framework in the codebase.

    Args for the agent SDK @tool:
        codebase_path: str - Path to the codebase root
        framework_name: str - Name of the framework (e.g., "langchain")

    Returns:
        dict with:
            - success: bool
            - framework: FrameworkInfo
            - found: bool
            - error: Optional[str]
    """
    codebase_path = args["codebase_path"]
    framework_name = args["framework_name"]

    try:
        # Detect all frameworks
        result = detect_frameworks({"codebase_path": codebase_path})

        if not result["success"]:
            return {
                "success": False,
                "framework": None,
                "found": False,
                "error": result["error"]
            }

        # Find the specific framework
        for fw in result["frameworks"]:
            if fw["name"] == framework_name:
                return {
                    "success": True,
                    "framework": fw,
                    "found": True,
                    "error": None
                }

        return {
            "success": True,
            "framework": None,
            "found": False,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "framework": None,
            "found": False,
            "error": str(e)
        }
