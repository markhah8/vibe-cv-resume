#!/usr/bin/env python3
import re
import sys

file_path = sys.argv[1]
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix unescaped & (but not \\&)
content = re.sub(r'(?<!\\)&', r'\\&', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Fixed LaTeX special characters in {file_path}")
