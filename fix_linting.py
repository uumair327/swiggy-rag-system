#!/usr/bin/env python3
"""Fix common linting issues."""

import re
from pathlib import Path

def fix_file(filepath):
    """Fix linting issues in a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Fix E203: whitespace before ':' (from black formatting)
    # This is a known conflict between black and flake8, we'll ignore it
    
    # Fix F541: f-string is missing placeholders
    content = re.sub(r'f"([^{}"]+)"', r'"\1"', content)
    content = re.sub(r"f'([^{}']+)'", r"'\1'", content)
    
    # Fix W293: blank line contains whitespace
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

# Fix all Python files
fixed_count = 0
for pattern in ['core/**/*.py', 'ports/**/*.py', 'adapters/**/*.py', 'tests/**/*.py', 'main.py']:
    for filepath in Path('.').glob(pattern):
        if fix_file(filepath):
            fixed_count += 1

print(f"\nFixed {fixed_count} files")
