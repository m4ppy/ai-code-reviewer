import ast
import re
from typing import Optional


class ASTAnalyzer:
    """Performs static analysis on Python code using the AST module."""

    def __init__(self, code: str):
        self.code = code
        self.tree: Optional[ast.AST] = None
        self.errors: list = []
        self.warnings: list = []
        self.info: list = []
        self._parse()

    def _parse(self):
        try:
            self.tree = ast.parse(self.code)
        except SyntaxError as e:
            self.errors.append(
                {
                    "type": "SyntaxError",
                    "message": f"Syntax error at line {e.lineno}: {e.msg}",
                    "line": e.lineno,
                    "severity": "error",
                }
            )

    def analyze(self) -> dict:
        if self.tree is None:
            return {
                "success": False,
                "errors": self.errors,
                "warnings": [],
                "info": [],
                "summary": "Failed to parse code due to syntax errors.",
                "metrics": {},
                "issues": self.errors,
                "severity": "error",
                "tags": [],
            }

        visitor = _CodeVisitor(self.code)
        visitor.visit(self.tree)

        issues = []
        issues.extend(visitor.errors)
        issues.extend(visitor.warnings)
        issues.extend(visitor.info)

        severity = "ok"
        if visitor.errors:
            severity = "error"
        elif visitor.warnings:
            severity = "warning"
        elif visitor.info:
            severity = "info"

        metrics = {
            "total_lines": len(self.code.splitlines()),
            "function_count": visitor.metrics.get("function_count", 0),
            "class_count": visitor.metrics.get("class_count", 0),
            "import_count": visitor.metrics.get("import_count", 0),
            "complexity_estimate": visitor.metrics.get("complexity_estimate", 1),
            "max_nesting_depth": visitor.metrics.get("max_nesting_depth", 0),
            "global_vars": visitor.metrics.get("global_vars", []),
            "bare_excepts": visitor.metrics.get("bare_excepts", 0),
            "long_functions": visitor.metrics.get("long_functions", []),
            "missing_docstrings": visitor.metrics.get("missing_docstrings", []),
            "unused_imports": visitor.metrics.get("unused_imports", []),
            "mutable_defaults": visitor.metrics.get("mutable_defaults", []),
        }

        summary_parts = []
        summary_parts.append(
            f"{metrics['total_lines']} lines, "
            f"{metrics['function_count']} function(s), "
            f"{metrics['class_count']} class(es)."
        )
        if issues:
            summary_parts.append(
                f"Found {len(visitor.errors)} error(s), "
                f"{len(visitor.warnings)} warning(s), "
                f"{len(visitor.info)} suggestion(s)."
            )
        else:
            summary_parts.append("No static analysis issues found.")

        return {
            "success": True,
            "errors": visitor.errors,
            "warnings": visitor.warnings,
            "info": visitor.info,
            "summary": " ".join(summary_parts),
            "metrics": metrics,
            "issues": issues,
            "severity": severity,
            "tags": _extract_tags(visitor),
        }


def _extract_tags(visitor) -> list:
    tags = set()
    if visitor.metrics.get("class_count", 0) > 0:
        tags.add("oop")
    if visitor.metrics.get("function_count", 0) > 0:
        tags.add("functions")
    if visitor.metrics.get("import_count", 0) > 0:
        tags.add("imports")
    if visitor.metrics.get("bare_excepts", 0) > 0:
        tags.add("exception-handling")
    if visitor.metrics.get("long_functions"):
        tags.add("long-functions")
    if visitor.metrics.get("mutable_defaults"):
        tags.add("mutable-defaults")
    return list(tags)


class _CodeVisitor(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.source_lines = source.splitlines()
        self.errors = []
        self.warnings = []
        self.info = []
        self.metrics = {
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "complexity_estimate": 1,
            "max_nesting_depth": 0,
            "global_vars": [],
            "bare_excepts": 0,
            "long_functions": [],
            "missing_docstrings": [],
            "unused_imports": [],
            "mutable_defaults": [],
        }
        self._nesting_depth = 0
        self._imported_names = set()
        self._used_names = set()
        self._function_lines = {}

    def visit_FunctionDef(self, node):
        self.metrics["function_count"] += 1
        self._nesting_depth += 1
        self.metrics["max_nesting_depth"] = max(
            self.metrics["max_nesting_depth"], self._nesting_depth
        )

        func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
        if func_lines > 50:
            self.metrics["long_functions"].append(node.name)
            self.warnings.append(
                {
                    "type": "LongFunction",
                    "message": f"Function '{node.name}' is {func_lines} lines long (consider splitting it up)",
                    "line": node.lineno,
                    "severity": "warning",
                }
            )

        has_docstring = (
            isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )
        if not has_docstring and func_lines > 5:
            self.metrics["missing_docstrings"].append(node.name)
            self.info.append(
                {
                    "type": "MissingDocstring",
                    "message": f"Function '{node.name}' is missing a docstring",
                    "line": node.lineno,
                    "severity": "info",
                }
            )

        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.metrics["mutable_defaults"].append(node.name)
                self.errors.append(
                    {
                        "type": "MutableDefault",
                        "message": f"Function '{node.name}' uses a mutable default argument (list/dict/set) — this is a common Python bug",
                        "line": node.lineno,
                        "severity": "error",
                    }
                )

        self.generic_visit(node)
        self._nesting_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.metrics["class_count"] += 1
        has_docstring = (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        )
        if not has_docstring:
            self.info.append(
                {
                    "type": "MissingClassDocstring",
                    "message": f"Class '{node.name}' is missing a docstring",
                    "line": node.lineno,
                    "severity": "info",
                }
            )
        self.generic_visit(node)

    def visit_Import(self, node):
        self.metrics["import_count"] += 1
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self._imported_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.metrics["import_count"] += 1
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self._imported_names.add(name)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._used_names.add(node.id)
        self.generic_visit(node)

    def visit_Global(self, node):
        for name in node.names:
            self.metrics["global_vars"].append(name)
            self.warnings.append(
                {
                    "type": "GlobalVariable",
                    "message": f"Use of 'global' variable '{name}' — prefer passing values as arguments or using class attributes",
                    "line": node.lineno,
                    "severity": "warning",
                }
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.metrics["bare_excepts"] += 1
            self.warnings.append(
                {
                    "type": "BareExcept",
                    "message": "Bare 'except:' clause catches all exceptions including KeyboardInterrupt — specify exception types",
                    "line": node.lineno,
                    "severity": "warning",
                }
            )
        self.generic_visit(node)

    def visit_If(self, node):
        self.metrics["complexity_estimate"] += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.metrics["complexity_estimate"] += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.metrics["complexity_estimate"] += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.metrics["complexity_estimate"] += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.metrics["complexity_estimate"] += 1
        self.generic_visit(node)


def detect_language(code: str) -> str:
    """Detect if the code is Python by checking for syntax parse success."""
    try:
        ast.parse(code)
        return "python"
    except SyntaxError:
        pass
    if re.search(r"\bfunction\b|\bconst\b|\blet\b|\bvar\b|\b=>\b", code):
        return "javascript"
    if re.search(r"\bpublic\b|\bprivate\b|\bclass\b.*\{", code):
        return "java"
    return "unknown"
