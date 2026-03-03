#!/usr/bin/env python3
"""Audit imports in src/ directory."""
import ast
import os

for root, dirs, files in os.walk('src'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.py'):
            continue
        fpath = os.path.join(root, f)
        try:
            with open(fpath) as fh:
                tree = ast.parse(fh.read(), filename=fpath)
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
                        for alias in node.names:
                            print(f'BROKEN IMPORT: {fpath}:{node.lineno} - from {mod} import {alias.name}')
