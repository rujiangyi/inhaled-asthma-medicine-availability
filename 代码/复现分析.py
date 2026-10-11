"""Offline replay of the analysis tables and eleven composite figures."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
for directory in ['表格', '图形', '报告', '核验']:
    (ROOT/directory).mkdir(parents=True, exist_ok=True)
environment = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
sequence = ['统计分析.py', '统计复核.py', '英文统计表.py', '图形一至二.py',
            '图形三至四.py', '图形五至六.py', '图形七至八.py', '补充图.py']
for name in sequence:
    print(f'Running {name}', flush=True)
    subprocess.run([sys.executable, str(ROOT/'代码'/name)], check=True, cwd=ROOT, env=environment)
print('Rebuilt nineteen analytical CSV tables and eleven composite figures; no live downloads or manuscript export.', flush=True)
