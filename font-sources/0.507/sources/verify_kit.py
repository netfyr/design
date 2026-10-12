#!/usr/bin/env python3
"""Verify this distribution's SHA-256 manifest using the Python standard library."""
from pathlib import Path
import hashlib,sys
root=Path(__file__).resolve().parents[1]
failures=[];count=0
for line in (root/'SHA256SUMS.txt').read_text().splitlines():
 if not line.strip():continue
 digest,name=line.split('  ',1);relative=Path(name)
 if relative.is_absolute() or '..' in relative.parts:
  failures.append('Unsafe manifest path: '+name);continue
 p=root/relative
 if not p.is_file() or p.is_symlink():failures.append('Missing or unsafe file: '+name);continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:failures.append('Changed: '+name)
 count+=1
if failures:
 print('\n'.join(failures),file=sys.stderr);raise SystemExit(1)
print(f'Verified {count} files against SHA256SUMS.txt')
