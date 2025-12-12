#!/usr/bin/env python3
"""
Dead code analyzer for RogueSignalProtocol.
Finds potentially unused functions, classes, variables, and imports.
"""

import argparse
import ast
import os
from collections import defaultdict
from pathlib import Path


class CodeAnalyzer(ast.NodeVisitor):
    """Analyzes Python files for definitions and usages."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.definitions: dict[str, list[int]] = defaultdict(list)
        self.usages: set[str] = set()
        self.imports: dict[str, int] = {}
        self.current_class = None
        self.decorators: dict[str, list[str]] = {}  # Track decorators per function

    def visit_FunctionDef(self, node):
        """Track function definitions."""
        if self.current_class:
            full_name = f"{self.current_class}.{node.name}"
        else:
            full_name = node.name

        # Track decorators for this function
        decorator_names = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorator_names.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorator_names.append(decorator.attr)

        # Skip test functions, magic methods, fixtures, and common overrides
        if not (
            node.name.startswith("test_")
            or node.name.startswith("_")
            and node.name.endswith("_")
            or node.name
            in [
                "__init__",
                "__str__",
                "__repr__",
                "setUp",
                "tearDown",
                "setup_method",
                "teardown_method",
            ]
            or "fixture" in decorator_names
            or "pytest_fixture" in decorator_names
        ):
            self.definitions["function"].append((full_name, node.lineno))
            self.decorators[full_name] = decorator_names

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Track class definitions."""
        # Skip test classes (they're discovered by pytest via introspection)
        if not node.name.startswith("Test"):
            self.definitions["class"].append((node.name, node.lineno))

        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        for alias in node.names:
            if alias.name != "*":
                name = alias.asname if alias.asname else alias.name
                self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node):
        """Track name usages."""
        if isinstance(node.ctx, ast.Load):
            self.usages.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Track attribute usages."""
        self.usages.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Track function calls."""
        if isinstance(node.func, ast.Name):
            self.usages.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.usages.add(node.func.attr)
        self.generic_visit(node)


def analyze_file(filepath: Path) -> CodeAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        analyzer = CodeAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def find_python_files(root_dir: Path, include_tests: bool = False) -> list[Path]:
    """Find all Python files in the project."""
    python_files = []
    exclude_dirs = {".venv", "build", "dist", "__pycache__", ".git", ".pytest_cache", "docs"}

    # Only exclude tests if not explicitly including them
    if not include_tests:
        exclude_dirs.add("tests")

    for root, dirs, files in os.walk(root_dir):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def analyze_project(root_dir: Path, include_tests: bool = False) -> dict[str, any]:
    """Analyze entire project for unused code."""
    python_files = find_python_files(root_dir, include_tests)

    all_definitions = defaultdict(list)
    all_usages = set()
    all_imports = defaultdict(list)

    scope = "entire project (including tests)" if include_tests else "production code"
    print(f"Analyzing {len(python_files)} Python files ({scope})...")

    for filepath in python_files:
        analyzer = analyze_file(filepath)
        if analyzer:
            # Collect definitions
            for def_type, defs in analyzer.definitions.items():
                for name, lineno in defs:
                    all_definitions[def_type].append((name, str(filepath), lineno))

            # Collect usages
            all_usages.update(analyzer.usages)

            # Collect imports
            for imp_name, lineno in analyzer.imports.items():
                all_imports[imp_name].append((str(filepath), lineno))

    return {"definitions": all_definitions, "usages": all_usages, "imports": all_imports}


def find_unused_code(analysis: dict) -> dict[str, list]:
    """Find potentially unused code."""
    unused = defaultdict(list)

    # Find unused functions
    for name, filepath, lineno in analysis["definitions"]["function"]:
        simple_name = name.split(".")[-1]
        if simple_name not in analysis["usages"] and name not in analysis["usages"]:
            # Skip if it's a property, callback, or has common patterns
            if not any(
                [
                    simple_name.startswith("on_"),
                    simple_name.startswith("handle_"),
                    simple_name.startswith("render_"),
                    simple_name == "main",
                    simple_name == "run",
                    simple_name == "setup",
                    simple_name == "teardown",
                ]
            ):
                unused["functions"].append((name, filepath, lineno))

    # Find unused classes
    for name, filepath, lineno in analysis["definitions"]["class"]:
        if name not in analysis["usages"]:
            # Skip base classes and exceptions
            if not (name.endswith("Base") or name.endswith("Error") or name.endswith("Exception")):
                unused["classes"].append((name, filepath, lineno))

    # Find unused imports
    for imp_name, locations in analysis["imports"].items():
        if imp_name not in analysis["usages"]:
            unused["imports"].extend([(imp_name, loc[0], loc[1]) for loc in locations])

    return unused


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dead code analyzer for RogueSignalProtocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis (default: exclude tests)",
    )
    args = parser.parse_args()

    # Search from project root (parent of scripts/)
    root_dir = Path(__file__).parent.parent

    print("=" * 70)
    print("RogueSignalProtocol - Dead Code Analysis")
    if args.include_tests:
        print("(INCLUDING TEST FILES)")
    print("=" * 70)
    print()

    analysis = analyze_project(root_dir, include_tests=args.include_tests)
    unused = find_unused_code(analysis)

    # Print results
    print("\n" + "=" * 70)
    print("POTENTIALLY UNUSED FUNCTIONS")
    print("=" * 70)
    if unused["functions"]:
        for name, filepath, lineno in sorted(unused["functions"], key=lambda x: x[1]):
            rel_path = os.path.relpath(filepath, root_dir)
            print(f"  {rel_path}:{lineno} - {name}")
    else:
        print("  (none found)")

    print("\n" + "=" * 70)
    print("POTENTIALLY UNUSED CLASSES")
    print("=" * 70)
    if unused["classes"]:
        for name, filepath, lineno in sorted(unused["classes"], key=lambda x: x[1]):
            rel_path = os.path.relpath(filepath, root_dir)
            print(f"  {rel_path}:{lineno} - {name}")
    else:
        print("  (none found)")

    print("\n" + "=" * 70)
    print("POTENTIALLY UNUSED IMPORTS")
    print("=" * 70)
    if unused["imports"]:
        for name, filepath, lineno in sorted(unused["imports"], key=lambda x: (x[1], x[2])):
            rel_path = os.path.relpath(filepath, root_dir)
            print(f"  {rel_path}:{lineno} - {name}")
    else:
        print("  (none found)")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total functions: {len(analysis['definitions']['function'])}")
    print(f"  Potentially unused functions: {len(unused['functions'])}")
    print(f"  Total classes: {len(analysis['definitions']['class'])}")
    print(f"  Potentially unused classes: {len(unused['classes'])}")
    print(f"  Potentially unused imports: {len(unused['imports'])}")
    print()
    print("NOTE: This analysis may have false positives. Always verify before removing code.")
    print("      - Dynamic imports/usage (getattr, exec, etc.) won't be detected")
    print("      - Some callbacks and handlers may appear unused")
    print("      - Entry points and public APIs should be kept")
    print()


if __name__ == "__main__":
    main()
