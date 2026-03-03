#!/usr/bin/env python3
"""Check if broken imports are guarded by try/except."""
import ast
import os

def check_import_guarded(tree, lineno):
    """Check if import at lineno is inside a try/except block."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Try,)):
            for handler in node.handlers:
                pass
            # Check if lineno falls within the try body or handlers
            try_start = node.lineno
            try_end = max(
                max((n.end_lineno or n.lineno) for n in node.body) if node.body else 0,
                max((n.end_lineno or n.lineno) for n in node.handlers) if node.handlers else 0,
                max((n.end_lineno or n.lineno) for n in node.orelse) if node.orelse else 0,
                max((n.end_lineno or n.lineno) for n in node.finalbody) if node.finalbody else 0,
            )
            if try_start <= lineno <= try_end:
                return True
    return False

results = []
for root, dirs, files in os.walk('src'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.py'):
            continue
        fpath = os.path.join(root, f)
        try:
            with open(fpath) as fh:
                source = fh.read()
            tree = ast.parse(source, filename=fpath)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                if mod.startswith(('src.', 'core.', 'tools.', 'api.', 'utils.')):
                    target_file = mod.replace('.', '/') + '.py'
                    target_dir = mod.replace('.', '/')
                    if (not os.path.exists(target_file) 
                        and not os.path.exists(target_dir)
                        and not os.path.exists(target_dir + '/__init__.py')):
                        # Also check under src/
                        src_mod = 'src/' + mod.replace('.', '/') if not mod.startswith('src.') else mod.replace('.', '/')
                        src_file = src_mod + '.py'
                        src_dir = src_mod
                        if (os.path.exists(src_file) or os.path.exists(src_dir) 
                            or os.path.exists(src_dir + '/__init__.py')):
                            continue
                        guarded = check_import_guarded(tree, node.lineno)
                        for alias in node.names:
                            results.append((fpath, node.lineno, mod, alias.name, guarded))

# Print unguarded ones (runtime crashes)
print("=== UNGUARDED BROKEN IMPORTS (will crash at runtime) ===")
unguarded = [(f, l, m, n) for f, l, m, n, g in results if not g]
for f, l, m, n in unguarded:
    print(f"  {f}:{l} - from {m} import {n}")
print(f"\nTotal unguarded: {len(unguarded)}")

print("\n=== GUARDED BROKEN IMPORTS (try/except, graceful) ===")
guarded = [(f, l, m, n) for f, l, m, n, g in results if g]
for f, l, m, n in guarded:
    print(f"  {f}:{l} - from {m} import {n}")
print(f"\nTotal guarded: {len(guarded)}")
