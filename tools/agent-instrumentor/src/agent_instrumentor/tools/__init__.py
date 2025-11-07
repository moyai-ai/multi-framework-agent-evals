"""Tools for the ReACT instrumentation agent."""

from .tree_sitter_parser import (
    parse_python_file,
    find_imports,
    find_function_definitions,
    find_class_definitions,
    find_function_calls,
)
from .framework_detector import detect_frameworks, get_framework_details
from .code_generator import inject_instrumentation_code, write_instrumented_file
from .package_analyzer import extract_package_versions, get_framework_version

__all__ = [
    "parse_python_file",
    "find_imports",
    "find_function_definitions",
    "find_class_definitions",
    "find_function_calls",
    "detect_frameworks",
    "get_framework_details",
    "inject_instrumentation_code",
    "write_instrumented_file",
    "extract_package_versions",
    "get_framework_version",
]
