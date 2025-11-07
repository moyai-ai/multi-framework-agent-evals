"""Package version extraction from dependency files."""

import re
import tomllib
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class PackageVersion:
    """Information about a package and its version."""
    name: str
    version: str
    source: str  # "requirements.txt", "pyproject.toml", etc.
    constraint: str  # "==", ">=", "~=", etc.


def extract_package_versions(args: dict) -> dict:
    """Extract package versions from dependency files.

    Args for the agent SDK @tool:
        codebase_path: str - Path to the codebase root

    Returns:
        dict with:
            - success: bool
            - packages: Dict[str, PackageVersion] - Package name to version info
            - error: Optional[str]
    """
    codebase_path = Path(args["codebase_path"])
    packages = {}

    try:
        # Try requirements.txt
        requirements_file = codebase_path / "requirements.txt"
        if requirements_file.exists():
            reqs = parse_requirements_txt(requirements_file)
            packages.update(reqs)

        # Try pyproject.toml
        pyproject_file = codebase_path / "pyproject.toml"
        if pyproject_file.exists():
            pyproject_pkgs = parse_pyproject_toml(pyproject_file)
            # Don't override if already found in requirements.txt
            for name, pkg in pyproject_pkgs.items():
                if name not in packages:
                    packages[name] = pkg

        # Try setup.py
        setup_file = codebase_path / "setup.py"
        if setup_file.exists():
            setup_pkgs = parse_setup_py(setup_file)
            for name, pkg in setup_pkgs.items():
                if name not in packages:
                    packages[name] = pkg

        return {
            "success": True,
            "packages": {name: asdict(pkg) for name, pkg in packages.items()},
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "packages": {},
            "error": str(e)
        }


def parse_requirements_txt(file_path: Path) -> Dict[str, PackageVersion]:
    """Parse requirements.txt file."""
    packages = {}

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse package specification
            # Supports: package==1.0.0, package>=1.0.0, package~=1.0.0, etc.
            match = re.match(r'^([a-zA-Z0-9\-_]+)([=<>~!]+)([0-9\.]+.*?)(?:\s|$)', line)
            if match:
                name, constraint, version = match.groups()
                packages[name.lower()] = PackageVersion(
                    name=name,
                    version=version.strip(),
                    source="requirements.txt",
                    constraint=constraint
                )
            else:
                # Handle simple package names without version
                simple_match = re.match(r'^([a-zA-Z0-9\-_]+)(?:\s|$)', line)
                if simple_match:
                    name = simple_match.group(1)
                    packages[name.lower()] = PackageVersion(
                        name=name,
                        version="*",
                        source="requirements.txt",
                        constraint=""
                    )

    return packages


def parse_pyproject_toml(file_path: Path) -> Dict[str, PackageVersion]:
    """Parse pyproject.toml file."""
    packages = {}

    with open(file_path, 'rb') as f:
        data = tomllib.load(f)

    # Check [project.dependencies]
    dependencies = data.get('project', {}).get('dependencies', [])
    for dep in dependencies:
        # Parse dependency string
        match = re.match(r'^([a-zA-Z0-9\-_]+)([=<>~!]+)([0-9\.]+.*?)(?:\s|$|,)', dep)
        if match:
            name, constraint, version = match.groups()
            packages[name.lower()] = PackageVersion(
                name=name,
                version=version.strip(),
                source="pyproject.toml",
                constraint=constraint
            )
        else:
            # Handle simple package names
            simple_match = re.match(r'^([a-zA-Z0-9\-_]+)(?:\s|$|,)', dep)
            if simple_match:
                name = simple_match.group(1)
                packages[name.lower()] = PackageVersion(
                    name=name,
                    version="*",
                    source="pyproject.toml",
                    constraint=""
                )

    return packages


def parse_setup_py(file_path: Path) -> Dict[str, PackageVersion]:
    """Parse setup.py file (basic regex-based parsing)."""
    packages = {}

    with open(file_path, 'r') as f:
        content = f.read()

    # Look for install_requires or requires
    # This is basic and won't handle all cases, but good enough for most
    requires_match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not requires_match:
        requires_match = re.search(r'requires\s*=\s*\[(.*?)\]', content, re.DOTALL)

    if requires_match:
        requires_str = requires_match.group(1)
        # Extract package specifications
        for match in re.finditer(r'["\']([a-zA-Z0-9\-_]+)([=<>~!]+)?([0-9\.]+.*?)?["\']', requires_str):
            name = match.group(1)
            constraint = match.group(2) or ""
            version = match.group(3) or "*"

            packages[name.lower()] = PackageVersion(
                name=name,
                version=version.strip() if version else "*",
                source="setup.py",
                constraint=constraint
            )

    return packages


def get_framework_version(args: dict) -> dict:
    """Get version of a specific framework from dependency files.

    Args for the agent SDK @tool:
        codebase_path: str - Path to the codebase root
        framework_name: str - Name of the framework (e.g., "langchain")

    Returns:
        dict with:
            - success: bool
            - framework: str
            - version: Optional[str]
            - found: bool
            - error: Optional[str]
    """
    codebase_path = args["codebase_path"]
    framework_name = args["framework_name"].lower()

    try:
        # Get all packages
        result = extract_package_versions({"codebase_path": codebase_path})

        if not result["success"]:
            return {
                "success": False,
                "framework": framework_name,
                "version": None,
                "found": False,
                "error": result["error"]
            }

        packages = result["packages"]

        # Look for the framework
        if framework_name in packages:
            pkg = packages[framework_name]
            return {
                "success": True,
                "framework": framework_name,
                "version": pkg["version"],
                "found": True,
                "constraint": pkg["constraint"],
                "source": pkg["source"],
                "error": None
            }

        return {
            "success": True,
            "framework": framework_name,
            "version": None,
            "found": False,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "framework": framework_name,
            "version": None,
            "found": False,
            "error": str(e)
        }
