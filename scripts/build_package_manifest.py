"""Rebuild reproducible file-hash inventory after verified source changes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '__pycache__', '.pytest_cache', '.ruff_cache', '.venv', 'dist', 'build'}


def inventory(root: Path) -> dict[str, str]:
    result = {}
    for path in root.rglob('*'):
        rel = path.relative_to(root)
        if EXCLUDED.intersection(rel.parts) or path.suffix in {'.pyc','.pyo'}:
            continue
        if path.is_symlink():
            raise ValueError(f'Package cannot contain symlinks: {rel}')
        if path.is_file() and rel.as_posix() != 'package-manifest.json':
            result[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    manifest_path=ROOT/'package-manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    listed=inventory(ROOT)
    if args.check:
        ok=manifest['files']==listed
        print(json.dumps({'manifest_current':ok,'files':len(listed)}))
        return 0 if ok else 1
    manifest['version']=json.loads((ROOT/'plugin.json').read_text(encoding='utf8'))['version']
    manifest['files']=listed
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'manifest_current':True,'version':manifest['version'],'files':len(listed)}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
