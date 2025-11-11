"""
OpenGrep tools for static code analysis.
"""

import json
import os
import subprocess
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from langchain_core.tools import tool

from ..context import Config


class OpenGrepAnalyzer:
    """OpenGrep static analysis runner."""

    def __init__(self, use_mock: Optional[bool] = None):
        """
        Initialize the OpenGrep analyzer.

        Args:
            use_mock: If True, use mock analysis. If False, use real OpenGrep.
                     If None, use Config.USE_MOCK_OPENGREP setting.
        """
        self.rules_dir = Path("src/rules")
        self.rules_dir.mkdir(exist_ok=True, parents=True)
        self.use_mock = use_mock if use_mock is not None else Config.USE_MOCK_OPENGREP
        self._create_default_rules()

        # Check if real OpenGrep is available when not using mock
        if not self.use_mock:
            self.opengrep_available = self._check_opengrep_installed()
            if not self.opengrep_available:
                print("Warning: OpenGrep not found. Falling back to mock analysis.")
                print("Install OpenGrep with: curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash")
                self.use_mock = True

    def _check_opengrep_installed(self) -> bool:
        """Check if OpenGrep is installed and available."""
        return shutil.which(Config.OPENGREP_PATH) is not None

    def _create_default_rules(self):
        """Create default OpenGrep rules for analysis."""
        # Security rules in YAML format (OpenGrep/Semgrep standard)
        security_rules_yaml = r"""rules:
  - id: sql-injection
    message: Potential SQL injection vulnerability detected
    severity: ERROR
    languages:
      - python
    pattern-regex: 'query\s*=\s*f["''].*\{.*\}.*["'']'

  - id: hardcoded-secret
    message: Hardcoded secret or API key detected
    severity: ERROR
    languages:
      - python
      - javascript
      - java
    pattern-either:
      - pattern: API_KEY = "..."
      - pattern: PASSWORD = "..."
      - pattern: SECRET = "..."
      - pattern: TOKEN = "..."
      - pattern: DATABASE_PASSWORD = "..."

  - id: xss-vulnerability
    message: Potential XSS vulnerability - unsanitized user input in HTML
    severity: ERROR
    languages:
      - python
    pattern-regex: 'return\s+f["'']<.*\{.*\}.*>["'']'

  - id: command-injection
    message: Potential command injection vulnerability
    severity: ERROR
    languages:
      - python
      - javascript
    pattern-either:
      - pattern: os.system($X)
      - pattern: subprocess.call($X, shell=True)
      - pattern: exec($X)
"""

        # Quality rules in YAML format
        quality_rules_yaml = r"""rules:
  - id: empty-exception-handler
    message: Empty exception handler - may hide errors
    severity: WARNING
    languages:
      - python
    pattern: |
      try:
          ...
      except:
          pass

  - id: todo-comment
    message: TODO comment found - incomplete implementation
    severity: INFO
    languages:
      - python
      - javascript
      - java
    pattern-regex: '(# TODO:.*|// TODO:.*|/\* TODO:.*\*/)'

  - id: print-debugging
    message: Print statement used for debugging
    severity: INFO
    languages:
      - python
    pattern-either:
      - pattern: print(...)
      - pattern: console.log(...)
"""

        # Save rules to YAML files (OpenGrep standard format)
        with open(self.rules_dir / "security.yaml", "w") as f:
            f.write(security_rules_yaml)

        with open(self.rules_dir / "quality.yaml", "w") as f:
            f.write(quality_rules_yaml)

    def run_analysis(
        self,
        code_content: str,
        language: str,
        rules_type: str = "security"
    ) -> List[Dict[str, Any]]:
        """
        Run OpenGrep analysis on code content.

        Uses real OpenGrep if available and use_mock=False, otherwise uses mock analysis.

        Args:
            code_content: The code to analyze
            language: Programming language
            rules_type: Type of rules to use (security, quality)

        Returns:
            List of issues found
        """
        if self.use_mock:
            return self._run_mock_analysis(code_content, language, rules_type)
        else:
            return self._run_real_opengrep_analysis(code_content, language, rules_type)

    def _run_real_opengrep_analysis(
        self,
        code_content: str,
        language: str,
        rules_type: str = "security"
    ) -> List[Dict[str, Any]]:
        """
        Run actual OpenGrep binary analysis.

        Args:
            code_content: The code to analyze
            language: Programming language
            rules_type: Type of rules to use

        Returns:
            List of issues found
        """
        issues = []

        # Create a temporary directory for the analysis
        # This helps OpenGrep handle the files better
        temp_dir = tempfile.mkdtemp(prefix="opengrep_analysis_")
        tmp_file_path = Path(temp_dir) / f"code{self._get_file_extension(language)}"

        try:
            # Write code to file
            with open(tmp_file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)

            # Select rules file (YAML format)
            rules_file = self.rules_dir / f"{rules_type}.yaml"
            if not rules_file.exists():
                print(f"Warning: Rules file {rules_file} not found, creating default rules")
                self._create_default_rules()
                if not rules_file.exists():
                    print(f"Error: Could not create rules file {rules_file}")
                    return []

            # Run OpenGrep with better options
            # Use absolute paths for both rules and file
            abs_rules_file = rules_file.absolute()
            abs_tmp_file = tmp_file_path.absolute()

            cmd = [
                Config.OPENGREP_PATH,
                "--config", str(abs_rules_file),
                "--json",
                "--no-git-ignore",  # Don't skip files
                "--no-rewrite-rule-ids",  # Keep rule IDs as-is
                str(abs_tmp_file)
            ]

            print(f"DEBUG: Running OpenGrep command: {' '.join(cmd)}")

            # Set environment for OpenGrep
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            print(f"DEBUG: Environment PYTHONIOENCODING set to: {env.get('PYTHONIOENCODING')}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_dir,  # Run in temp directory
                env=env  # Pass environment with encoding
            )

            print(f"DEBUG: OpenGrep returned code {result.returncode}")
            print(f"DEBUG: stdout length: {len(result.stdout)}, stderr length: {len(result.stderr)}")

            # OpenGrep returns 0 for no findings, 1 for findings found, >1 for errors
            if result.returncode <= 1:
                # Parse OpenGrep JSON output
                if result.stdout:
                    try:
                        opengrep_output = json.loads(result.stdout)
                        issues = self._parse_opengrep_output(opengrep_output)
                        print(f"DEBUG: Parsed {len(issues)} issues from OpenGrep output")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing OpenGrep output: {e}")
                        print(f"Raw stdout: {result.stdout[:500]}")
                else:
                    print("DEBUG: OpenGrep returned no stdout")
            else:
                print(f"OpenGrep execution failed with return code {result.returncode}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("OpenGrep execution timed out")
        except Exception as e:
            print(f"Error running OpenGrep: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up temporary directory and file
            try:
                if tmp_file_path.exists():
                    tmp_file_path.unlink()
                Path(temp_dir).rmdir()
            except Exception as e:
                print(f"Warning: Could not clean up temp files: {e}")

        return issues

    def _parse_opengrep_output(self, opengrep_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse OpenGrep JSON output into our issue format.

        Args:
            opengrep_output: Raw output from OpenGrep

        Returns:
            List of parsed issues
        """
        issues = []

        # OpenGrep JSON format has results in "results" key
        results = opengrep_output.get("results", [])
        print(f"DEBUG: Found {len(results)} results in OpenGrep output")

        for result in results:
            # Extract severity from extra metadata
            extra = result.get("extra", {})
            opengrep_severity = extra.get("severity", "ERROR")
            rule_id = result.get("check_id", "unknown")

            # Map severity, with special handling for critical rules
            if rule_id == "command-injection":
                severity = "CRITICAL"
            else:
                severity = self._map_severity(opengrep_severity)

            # Build issue object
            issue = {
                "rule_id": rule_id,
                "severity": severity,
                "message": extra.get("message", "Issue detected"),
                "line": result.get("start", {}).get("line", 1),
                "code": extra.get("lines", result.get("extra", {}).get("message", "")),
                "file_path": result.get("path", "")
            }
            issues.append(issue)
            print(f"DEBUG: Added issue - {issue['rule_id']} (severity: {severity}) at line {issue['line']}")

        return issues

    def _map_severity(self, opengrep_severity: str) -> str:
        """Map OpenGrep severity to our severity levels."""
        # Map OpenGrep/Semgrep severities to standard severity levels
        # ERROR maps to HIGH (most common security issues)
        # Can be overridden based on specific rule if needed
        severity_map = {
            "ERROR": "HIGH",
            "WARNING": "MEDIUM",
            "INFO": "LOW"
        }
        return severity_map.get(opengrep_severity.upper(), "INFO")

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for a language."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "ruby": ".rb",
            "php": ".php",
            "c": ".c",
            "cpp": ".cpp",
        }
        return extensions.get(language.lower(), ".txt")

    def _run_mock_analysis(
        self,
        code_content: str,
        language: str,
        rules_type: str = "security"
    ) -> List[Dict[str, Any]]:
        """
        Simulate OpenGrep analysis with pattern matching.

        This is used for testing and when OpenGrep is not available.

        Args:
            code_content: The code to analyze
            language: Programming language
            rules_type: Type of rules to use

        Returns:
            List of simulated issues
        """
        issues = []

        # Simulate OpenGrep analysis based on patterns
        if rules_type == "security":
            # Check for SQL injection
            if "f\"SELECT" in code_content or "query = f\"" in code_content:
                issues.append({
                    "rule_id": "sql-injection",
                    "severity": "ERROR",
                    "message": "Potential SQL injection vulnerability detected",
                    "line": self._find_line_number(code_content, "SELECT"),
                    "code": self._extract_code_snippet(code_content, "SELECT")
                })

            # Check for hardcoded secrets
            for secret_pattern in ["API_KEY =", "PASSWORD =", "SECRET =", "TOKEN ="]:
                if secret_pattern in code_content:
                    issues.append({
                        "rule_id": "hardcoded-secret",
                        "severity": "ERROR",
                        "message": "Hardcoded secret or API key detected",
                        "line": self._find_line_number(code_content, secret_pattern),
                        "code": self._extract_code_snippet(code_content, secret_pattern)
                    })

            # Check for XSS
            if "return f\"<" in code_content or "innerHTML =" in code_content:
                issues.append({
                    "rule_id": "xss-vulnerability",
                    "severity": "ERROR",
                    "message": "Potential XSS vulnerability - unsanitized user input",
                    "line": self._find_line_number(code_content, "return f\"<"),
                    "code": self._extract_code_snippet(code_content, "return f\"<")
                })

            # Check for command injection
            if "os.system(" in code_content or "subprocess.call(" in code_content:
                issues.append({
                    "rule_id": "command-injection",
                    "severity": "CRITICAL",
                    "message": "Potential command injection vulnerability",
                    "line": self._find_line_number(code_content, "os.system"),
                    "code": self._extract_code_snippet(code_content, "os.system")
                })

        elif rules_type == "quality":
            # Check for empty exception handlers
            if "except: pass" in code_content or "except:\n    pass" in code_content:
                issues.append({
                    "rule_id": "empty-exception-handler",
                    "severity": "WARNING",
                    "message": "Empty exception handler - may hide errors",
                    "line": self._find_line_number(code_content, "except:"),
                    "code": self._extract_code_snippet(code_content, "except:")
                })

            # Check for TODOs
            if "TODO:" in code_content:
                issues.append({
                    "rule_id": "todo-comment",
                    "severity": "INFO",
                    "message": "TODO comment found - incomplete implementation",
                    "line": self._find_line_number(code_content, "TODO:"),
                    "code": self._extract_code_snippet(code_content, "TODO:")
                })

        return issues

    def _find_line_number(self, content: str, pattern: str) -> int:
        """Find the line number of a pattern in content."""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 1

    def _extract_code_snippet(self, content: str, pattern: str, context: int = 2) -> str:
        """Extract code snippet around a pattern."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if pattern in line:
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                return '\n'.join(lines[start:end])
        return ""


# Create a global analyzer instance (will use Config.USE_MOCK_OPENGREP)
analyzer = OpenGrepAnalyzer()


@tool
async def run_opengrep_analysis(
    code_content: str,
    file_path: str,
    language: str = "python",
    analysis_type: str = "security"
) -> Dict[str, Any]:
    """
    Run OpenGrep static analysis on code content.

    Args:
        code_content: The code to analyze
        file_path: Path of the file being analyzed
        language: Programming language of the code
        analysis_type: Type of analysis (security, quality, or both)

    Returns:
        Analysis results with identified issues
    """
    try:
        issues = []

        # Run security analysis
        if analysis_type in ["security", "both"]:
            security_issues = analyzer.run_analysis(code_content, language, "security")
            for issue in security_issues:
                issue["file_path"] = file_path
                issue["category"] = "security"
            issues.extend(security_issues)

        # Run quality analysis
        if analysis_type in ["quality", "both"]:
            quality_issues = analyzer.run_analysis(code_content, language, "quality")
            for issue in quality_issues:
                issue["file_path"] = file_path
                issue["category"] = "quality"
            issues.extend(quality_issues)

        return {
            "success": True,
            "file_path": file_path,
            "language": language,
            "analysis_type": analysis_type,
            "issues": issues,
            "issues_count": len(issues),
            "severity_breakdown": _get_severity_breakdown(issues)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def create_custom_rule(
    rule_id: str,
    pattern: str,
    message: str,
    severity: str = "WARNING",
    languages: List[str] = None
) -> Dict[str, Any]:
    """
    Create a custom OpenGrep rule for analysis.

    Args:
        rule_id: Unique identifier for the rule
        pattern: The pattern to match (OpenGrep syntax)
        message: Message to display when pattern is found
        severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        languages: List of languages this rule applies to

    Returns:
        Created rule configuration
    """
    if languages is None:
        languages = ["python", "javascript", "java"]

    rule = {
        "id": rule_id,
        "message": message,
        "severity": severity,
        "languages": languages,
        "pattern": pattern
    }

    return {
        "success": True,
        "rule": rule
    }


@tool
async def analyze_dependencies(
    dependencies_content: str,
    package_manager: str = "pip"
) -> Dict[str, Any]:
    """
    Analyze project dependencies for vulnerabilities.

    Args:
        dependencies_content: Content of dependency file (requirements.txt, package.json, etc.)
        package_manager: Package manager type (pip, npm, yarn, etc.)

    Returns:
        Analysis results for dependencies
    """
    issues = []

    # Simulate vulnerability detection for demo
    vulnerable_packages = {
        "flask==1.1.2": {
            "cve": "CVE-2021-23385",
            "severity": "HIGH",
            "description": "Flask versions before 2.0.0 have known security vulnerabilities"
        },
        "requests==2.20.0": {
            "cve": "CVE-2021-28363",
            "severity": "MEDIUM",
            "description": "Requests versions before 2.25.0 have urllib3 vulnerability"
        },
        "django==2.2.10": {
            "cve": "CVE-2021-3281",
            "severity": "HIGH",
            "description": "Django versions before 3.1.6 have SQL injection vulnerability"
        },
        "pyyaml==5.1": {
            "cve": "CVE-2020-14343",
            "severity": "CRITICAL",
            "description": "PyYAML versions before 5.4 have arbitrary code execution vulnerability"
        }
    }

    lines = dependencies_content.split('\n')
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        for vuln_package, vuln_info in vulnerable_packages.items():
            if vuln_package in line:
                issues.append({
                    "package": vuln_package.split('==')[0],
                    "version": vuln_package.split('==')[1],
                    "line": line_num,
                    "cve": vuln_info["cve"],
                    "severity": vuln_info["severity"],
                    "description": vuln_info["description"],
                    "recommendation": f"Upgrade to latest version of {vuln_package.split('==')[0]}"
                })

    return {
        "success": True,
        "package_manager": package_manager,
        "total_dependencies": len([l for l in lines if l.strip() and not l.startswith('#')]),
        "vulnerable_dependencies": len(issues),
        "issues": issues,
        "severity_breakdown": _get_severity_breakdown(issues)
    }


def _get_severity_breakdown(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get breakdown of issues by severity."""
    breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for issue in issues:
        severity = issue.get("severity", "INFO").upper()
        if severity == "ERROR":
            severity = "HIGH"
        elif severity == "WARNING":
            severity = "MEDIUM"
        if severity in breakdown:
            breakdown[severity] += 1
    return breakdown