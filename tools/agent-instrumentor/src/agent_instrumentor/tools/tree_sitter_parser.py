"""Tree-sitter based Python code parser for agent instrumentation."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
except ImportError:
    raise ImportError(
        "tree-sitter and tree-sitter-python are required. "
        "Install with: pip install tree-sitter tree-sitter-python"
    )


# Initialize tree-sitter parser
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: List[str]
    alias: Optional[str]
    line: int
    source: str


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    line: int
    decorators: List[str]
    parameters: List[str]
    source: str


@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    line: int
    decorators: List[str]
    bases: List[str]
    source: str


@dataclass
class CallInfo:
    """Information about a function/method call."""
    function_name: str
    line: int
    arguments: List[str]
    source: str


def parse_python_file(args: dict) -> dict:
    """Parse a Python file and return its AST.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file to parse

    Returns:
        dict with:
            - success: bool
            - file_path: str
            - source: str (file contents)
            - tree: str (syntax tree representation)
            - error: Optional[str]
    """
    file_path = args["file_path"]

    try:
        with open(file_path, 'rb') as f:
            source_code = f.read()

        tree = parser.parse(source_code)

        return {
            "success": True,
            "file_path": file_path,
            "source": source_code.decode('utf-8'),
            "tree": tree.root_node.sexp(),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path,
            "source": None,
            "tree": None,
            "error": str(e)
        }


def find_imports(args: dict) -> dict:
    """Find all import statements in a Python file.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file

    Returns:
        dict with:
            - success: bool
            - imports: List[ImportInfo]
            - error: Optional[str]
    """
    file_path = args["file_path"]

    try:
        with open(file_path, 'rb') as f:
            source_code = f.read()

        tree = parser.parse(source_code)
        root_node = tree.root_node

        imports = []

        # Query for import statements
        query = PY_LANGUAGE.query("""
        (import_statement
            name: (dotted_name) @module) @import

        (import_from_statement
            module_name: (dotted_name) @module
            name: (dotted_name) @name) @import_from

        (import_from_statement
            module_name: (dotted_name) @module
            name: (aliased_import
                name: (dotted_name) @name
                alias: (identifier) @alias)) @import_from_alias
        """)

        captures = query.captures(root_node)
        source_lines = source_code.decode('utf-8').split('\n')

        for node, capture_name in captures:
            if capture_name == "import":
                line_num = node.start_point[0] + 1
                source = source_lines[node.start_point[0]]

                # Parse import statement
                module_name = node.child_by_field_name("name")
                if module_name:
                    module = source_code[module_name.start_byte:module_name.end_byte].decode('utf-8')
                    imports.append(ImportInfo(
                        module=module,
                        names=[],
                        alias=None,
                        line=line_num,
                        source=source
                    ))

        # Parse 'from ... import ...' statements
        for child in root_node.children:
            if child.type == "import_from_statement":
                line_num = child.start_point[0] + 1
                source = source_lines[child.start_point[0]]

                module_node = child.child_by_field_name("module_name")
                module = source_code[module_node.start_byte:module_node.end_byte].decode('utf-8') if module_node else ""

                names = []
                for name_child in child.children:
                    if name_child.type == "dotted_name" and name_child != module_node:
                        name = source_code[name_child.start_byte:name_child.end_byte].decode('utf-8')
                        names.append(name)

                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    line=line_num,
                    source=source
                ))

        return {
            "success": True,
            "imports": [asdict(imp) for imp in imports],
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "imports": [],
            "error": str(e)
        }


def find_function_definitions(args: dict) -> dict:
    """Find all function definitions in a Python file.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file

    Returns:
        dict with:
            - success: bool
            - functions: List[FunctionInfo]
            - error: Optional[str]
    """
    file_path = args["file_path"]

    try:
        with open(file_path, 'rb') as f:
            source_code = f.read()

        tree = parser.parse(source_code)
        root_node = tree.root_node
        source_lines = source_code.decode('utf-8').split('\n')

        functions = []

        def visit_node(node):
            if node.type == "function_definition":
                line_num = node.start_point[0] + 1

                # Get function name
                name_node = node.child_by_field_name("name")
                func_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8') if name_node else "unknown"

                # Get decorators
                decorators = []
                if node.parent and node.parent.type == "decorated_definition":
                    for child in node.parent.children:
                        if child.type == "decorator":
                            decorator_text = source_code[child.start_byte:child.end_byte].decode('utf-8')
                            decorators.append(decorator_text)

                # Get parameters
                params = []
                params_node = node.child_by_field_name("parameters")
                if params_node:
                    for param in params_node.children:
                        if param.type == "identifier":
                            param_name = source_code[param.start_byte:param.end_byte].decode('utf-8')
                            params.append(param_name)

                # Get source
                source = source_lines[node.start_point[0]]

                functions.append(FunctionInfo(
                    name=func_name,
                    line=line_num,
                    decorators=decorators,
                    parameters=params,
                    source=source
                ))

            for child in node.children:
                visit_node(child)

        visit_node(root_node)

        return {
            "success": True,
            "functions": [asdict(func) for func in functions],
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "functions": [],
            "error": str(e)
        }


def find_class_definitions(args: dict) -> dict:
    """Find all class definitions in a Python file.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file

    Returns:
        dict with:
            - success: bool
            - classes: List[ClassInfo]
            - error: Optional[str]
    """
    file_path = args["file_path"]

    try:
        with open(file_path, 'rb') as f:
            source_code = f.read()

        tree = parser.parse(source_code)
        root_node = tree.root_node
        source_lines = source_code.decode('utf-8').split('\n')

        classes = []

        def visit_node(node):
            if node.type == "class_definition":
                line_num = node.start_point[0] + 1

                # Get class name
                name_node = node.child_by_field_name("name")
                class_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8') if name_node else "unknown"

                # Get decorators
                decorators = []
                if node.parent and node.parent.type == "decorated_definition":
                    for child in node.parent.children:
                        if child.type == "decorator":
                            decorator_text = source_code[child.start_byte:child.end_byte].decode('utf-8')
                            decorators.append(decorator_text)

                # Get base classes
                bases = []
                superclasses_node = node.child_by_field_name("superclasses")
                if superclasses_node:
                    for base in superclasses_node.children:
                        if base.type == "identifier":
                            base_name = source_code[base.start_byte:base.end_byte].decode('utf-8')
                            bases.append(base_name)

                # Get source
                source = source_lines[node.start_point[0]]

                classes.append(ClassInfo(
                    name=class_name,
                    line=line_num,
                    decorators=decorators,
                    bases=bases,
                    source=source
                ))

            for child in node.children:
                visit_node(child)

        visit_node(root_node)

        return {
            "success": True,
            "classes": [asdict(cls) for cls in classes],
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "classes": [],
            "error": str(e)
        }


def find_function_calls(args: dict) -> dict:
    """Find function calls matching a pattern in a Python file.

    Args for the agent SDK @tool:
        file_path: str - Path to the Python file
        pattern: str - Function name pattern to search for (e.g., "Agent", "create_")

    Returns:
        dict with:
            - success: bool
            - calls: List[CallInfo]
            - error: Optional[str]
    """
    file_path = args["file_path"]
    pattern = args.get("pattern", "")

    try:
        with open(file_path, 'rb') as f:
            source_code = f.read()

        tree = parser.parse(source_code)
        root_node = tree.root_node
        source_lines = source_code.decode('utf-8').split('\n')

        calls = []

        def visit_node(node):
            if node.type == "call":
                line_num = node.start_point[0] + 1

                # Get function name
                func_node = node.child_by_field_name("function")
                if func_node:
                    func_name = source_code[func_node.start_byte:func_node.end_byte].decode('utf-8')

                    # Check if matches pattern
                    if not pattern or pattern in func_name:
                        # Get arguments
                        args_node = node.child_by_field_name("arguments")
                        arguments = []
                        if args_node:
                            for arg in args_node.children:
                                if arg.type != '(' and arg.type != ')' and arg.type != ',':
                                    arg_text = source_code[arg.start_byte:arg.end_byte].decode('utf-8')
                                    arguments.append(arg_text)

                        # Get source
                        source = source_lines[node.start_point[0]:node.end_point[0]+1]
                        source_str = '\n'.join(source) if isinstance(source, list) else source

                        calls.append(CallInfo(
                            function_name=func_name,
                            line=line_num,
                            arguments=arguments,
                            source=source_str
                        ))

            for child in node.children:
                visit_node(child)

        visit_node(root_node)

        return {
            "success": True,
            "calls": [asdict(call) for call in calls],
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "calls": [],
            "error": str(e)
        }
