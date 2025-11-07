"""Code generation and injection using tree-sitter."""

import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

import black


@dataclass
class InjectionPoint:
    """Represents a point in code where instrumentation should be injected."""
    type: str  # "import", "decorator", "callback", "wrapper", "context_manager"
    line: int
    target: str  # Function name, class name, or variable name
    code: str  # Code to inject
    indentation: int = 0


def inject_instrumentation_code(args: dict) -> dict:
    """Inject instrumentation code into a Python file.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file
        injection_points: List[Dict] - List of injection points
        validate: bool - Whether to validate with black (default: True)

    Returns:
        dict with:
            - success: bool
            - modified_source: str
            - changes: List[str] - Description of changes made
            - error: Optional[str]
    """
    file_path = args["file_path"]
    injection_points = [InjectionPoint(**ip) for ip in args["injection_points"]]
    validate = args.get("validate", True)

    try:
        with open(file_path, 'r') as f:
            original_source = f.read()

        source_lines = original_source.split('\n')
        changes = []

        # Sort injection points by line number (descending) to preserve line numbers
        injection_points.sort(key=lambda x: x.line, reverse=True)

        for injection_point in injection_points:
            if injection_point.type == "import":
                source_lines = inject_import(source_lines, injection_point)
                changes.append(f"Added import: {injection_point.code}")

            elif injection_point.type == "decorator":
                source_lines = inject_decorator(source_lines, injection_point)
                changes.append(f"Added decorator to {injection_point.target}: {injection_point.code}")

            elif injection_point.type == "callback":
                source_lines = inject_callback_parameter(source_lines, injection_point)
                changes.append(f"Added callback parameter to {injection_point.target}")

            elif injection_point.type == "wrapper":
                source_lines = inject_wrapper(source_lines, injection_point)
                changes.append(f"Wrapped {injection_point.target} with instrumentation")

            elif injection_point.type == "context_manager":
                source_lines = inject_context_manager(source_lines, injection_point)
                changes.append(f"Wrapped {injection_point.target} with context manager")

        modified_source = '\n'.join(source_lines)

        # Validate and format with black
        if validate:
            try:
                modified_source = black.format_str(modified_source, mode=black.FileMode())
            except Exception as e:
                return {
                    "success": False,
                    "modified_source": None,
                    "changes": [],
                    "error": f"Black formatting failed: {str(e)}"
                }

        return {
            "success": True,
            "modified_source": modified_source,
            "changes": changes,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "modified_source": None,
            "changes": [],
            "error": str(e)
        }


def inject_import(source_lines: List[str], injection: InjectionPoint) -> List[str]:
    """Inject an import statement at the appropriate location."""
    import_line = injection.code

    # Check if import already exists
    for line in source_lines:
        if line.strip() == import_line.strip():
            return source_lines  # Already exists

    # Find the best location for the import
    # After module docstring and existing imports
    insert_index = 0
    in_docstring = False
    found_imports = False

    for i, line in enumerate(source_lines):
        stripped = line.strip()

        # Handle module docstring
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            if not stripped[3:].endswith(stripped[:3]):
                in_docstring = True
            continue

        if in_docstring:
            if stripped.endswith('"""') or stripped.endswith("'''"):
                in_docstring = False
                insert_index = i + 1
            continue

        # Track imports
        if stripped.startswith('import ') or stripped.startswith('from '):
            found_imports = True
            insert_index = i + 1
        elif found_imports and stripped and not stripped.startswith('#'):
            # Found end of imports
            break

    # Insert the import
    source_lines.insert(insert_index, import_line)
    return source_lines


def inject_decorator(source_lines: List[str], injection: InjectionPoint) -> List[str]:
    """Inject a decorator before a function definition."""
    decorator_line = injection.code
    target_func = injection.target
    target_line = injection.line - 1  # Convert to 0-indexed

    # Find the function definition
    func_line_index = target_line
    if func_line_index < len(source_lines):
        # Get indentation of the function
        func_line = source_lines[func_line_index]
        indentation = len(func_line) - len(func_line.lstrip())

        # Check if decorator already exists
        for i in range(max(0, func_line_index - 5), func_line_index):
            if decorator_line.strip() in source_lines[i].strip():
                return source_lines  # Already exists

        # Add decorator with same indentation
        decorator_with_indent = ' ' * indentation + decorator_line
        source_lines.insert(func_line_index, decorator_with_indent)

    return source_lines


def inject_callback_parameter(source_lines: List[str], injection: InjectionPoint) -> List[str]:
    """Inject a callback parameter into a function call."""
    target_var = injection.target
    callback_param = injection.code
    target_line = injection.line - 1

    if target_line >= len(source_lines):
        return source_lines

    # Find the function call (may span multiple lines)
    start_line = target_line
    line = source_lines[start_line]

    # Check if this is a multi-line call
    if '(' in line and ')' not in line:
        # Multi-line call - find the closing parenthesis
        end_line = start_line
        for i in range(start_line + 1, min(start_line + 20, len(source_lines))):
            if ')' in source_lines[i]:
                end_line = i
                break

        # Find the last line before closing paren
        insert_line = end_line
        closing_paren_line = source_lines[insert_line]

        # Get indentation
        indentation = len(closing_paren_line) - len(closing_paren_line.lstrip())

        # Check if there's already a comma
        prev_line = source_lines[insert_line - 1]
        if not prev_line.rstrip().endswith(','):
            source_lines[insert_line - 1] = prev_line.rstrip() + ','

        # Insert the callback parameter
        param_line = ' ' * (indentation + 4) + callback_param + ','
        source_lines.insert(insert_line, param_line)

    else:
        # Single line call - inject before closing paren
        if ')' in line:
            # Check if there are existing parameters
            paren_content = line[line.index('('):line.rindex(')')]
            if paren_content.strip() == '(':
                # No parameters
                new_line = line.replace(')', f'{callback_param})')
            else:
                # Has parameters
                new_line = line.replace(')', f', {callback_param})')

            source_lines[target_line] = new_line

    return source_lines


def inject_wrapper(source_lines: List[str], injection: InjectionPoint) -> List[str]:
    """Inject a wrapper around a code block."""
    target_line = injection.line - 1
    wrapper_code = injection.code

    if target_line >= len(source_lines):
        return source_lines

    # Get indentation of target line
    target = source_lines[target_line]
    indentation = len(target) - len(target.lstrip())

    # Parse wrapper code (should be in format: "with tracer.span('name'):")
    wrapper_lines = wrapper_code.split('\n')
    indented_wrapper = [' ' * indentation + line for line in wrapper_lines]

    # Indent the original line
    source_lines[target_line] = ' ' * (indentation + 4) + target.lstrip()

    # Insert wrapper
    for i, wrapper_line in enumerate(indented_wrapper):
        source_lines.insert(target_line + i, wrapper_line)

    return source_lines


def inject_context_manager(source_lines: List[str], injection: InjectionPoint) -> List[str]:
    """Inject a context manager around a code block."""
    target_line = injection.line - 1
    context_manager = injection.code

    if target_line >= len(source_lines):
        return source_lines

    # Get indentation
    target = source_lines[target_line]
    indentation = len(target) - len(target.lstrip())

    # Add context manager
    cm_line = ' ' * indentation + context_manager
    source_lines.insert(target_line, cm_line)

    # Indent the target line and subsequent lines in the block
    # Find the end of the block
    end_line = target_line + 1
    for i in range(target_line + 1, len(source_lines)):
        line = source_lines[i]
        if line.strip() and not line.startswith(' ' * (indentation + 1)):
            end_line = i
            break

    # Indent all lines in the block
    for i in range(target_line + 1, end_line):
        source_lines[i] = ' ' * 4 + source_lines[i]

    return source_lines


def write_instrumented_file(args: dict) -> dict:
    """Write instrumented code back to file.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file
        modified_source: str - Modified source code

    Returns:
        dict with:
            - success: bool
            - error: Optional[str]
    """
    file_path = args["file_path"]
    modified_source = args["modified_source"]

    try:
        with open(file_path, 'w') as f:
            f.write(modified_source)

        return {
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
