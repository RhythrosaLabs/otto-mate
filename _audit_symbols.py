#!/usr/bin/env python3
"""Check if imported symbols exist in target modules."""
import ast
import os

def get_module_symbols(filepath):
    """Get top-level symbols defined in a Python file."""
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read(), filename=filepath)
    except SyntaxError:
        return None  # Can't parse
    symbols = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            symbols.add(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.add(node.name)
        elif isinstance(node, ast.ClassDef):
            symbols.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
        elif isinstance(node, ast.ImportFrom):
            if node.names:
                for alias in node.names:
                    symbols.add(alias.asname if alias.asname else alias.name)
    return symbols

def resolve_module(mod, base_dir):
    """Resolve a module path to a file path."""
    # Try direct path
    parts = mod.split('.')
    # Try under src/
    candidates = [
        os.path.join('src', *parts) + '.py',
        os.path.join('src', *parts, '__init__.py'),
        os.path.join(*parts) + '.py',
        os.path.join(*parts, '__init__.py'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

# Check main entry points - critical files
critical_files = [
    'src/api/main.py',
    'src/api/main_v2.py',
]

issues = []

for fpath in critical_files:
    if not os.path.exists(fpath):
        continue
    try:
        with open(fpath) as f:
            tree = ast.parse(f.read(), filename=fpath)
    except SyntaxError:
        issues.append(f"SYNTAX ERROR: {fpath}")
        continue
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            # Handle relative imports
            if node.level > 0:
                # Relative import - resolve from file location
                pkg_parts = fpath.replace('.py', '').split(os.sep)[:-1]  # directory parts
                level = node.level
                base = pkg_parts[:-level+1] if level > 0 else pkg_parts
                if mod:
                    full_mod = '.'.join(base + mod.split('.'))
                else:
                    full_mod = '.'.join(base)
                target = resolve_module(full_mod, '.')
            else:
                target = resolve_module(mod, '.')
            
            if target is None:
                for alias in node.names:
                    issues.append(f"MISSING MODULE: {fpath}:{node.lineno} - from {mod} import {alias.name} (module not found)")
                continue
            
            # Check if referenced symbols exist
            symbols = get_module_symbols(target)
            if symbols is None:
                issues.append(f"UNPARSEABLE TARGET: {target} (imported from {fpath}:{node.lineno})")
                continue
            
            for alias in node.names:
                name = alias.name
                if name not in symbols and name != '*':
                    issues.append(f"MISSING SYMBOL: {fpath}:{node.lineno} - '{name}' not found in {target}")

for i in issues:
    print(i)
if not issues:
    print("No issues found in critical files.")
