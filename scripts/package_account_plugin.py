"""Build a single skills-only Document Studio ZIP for authenticated Plugin Creator.

This command only prepares an archive. It never invokes account APIs or claims
to install anything. Approved company packs use export_company_plugin.py instead.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from install_local import selected_skills


DENIED_EXTENSIONS={'.pdf','.pptx','.docx','.ai','.otf','.ttf','.woff','.woff2','.zip','.env'}
IGNORED_PARTS={'.git','__pycache__','.pytest_cache','.venv','dist','build'}
DENIED_PARTS={'private','secrets'}
ACCOUNT_SCRIPTS=('install_local.py','build_package_manifest.py',
                 'export_company_plugin.py','package_account_plugin.py')


def build_account_plugin(source_root: Path, output: Path, *, language_skills: str = 'none') -> dict:
    """Include only manifest, compatibility metadata and selected, safe skills."""
    source_root=Path(source_root).absolute()
    output=Path(output).absolute()
    if output.exists():
        raise FileExistsError('Refuse to overwrite an existing account plugin ZIP')
    if output.suffix.lower()!='.zip':
        raise ValueError('Plugin Creator archive must be a ZIP')
    manifest_path=source_root/'plugin.json'
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError('Missing or linked plugin manifest')
    manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    if manifest.get('$schema')!='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json' or manifest.get('name')!='document-studio':
        raise ValueError('Not the standalone Document Studio plugin')
    if not isinstance(manifest.get('version'),str):
        raise ValueError('Missing semantic plugin version')
    short=manifest.get('extensions',{}).get('com.openai',{}).get('interface',{}).get('shortDescription','')
    if not isinstance(short,str) or not short or len(short)>30:
        raise ValueError('Plugin listing shortDescription must be 1–30 characters')
    # Review the whole selected source tree for symlinks before reading files.
    skillroot=source_root/'skills'
    if not skillroot.is_dir():
        raise ValueError('Missing skills directory')
    for item in skillroot.rglob('*'):
        if item.is_symlink():
            raise ValueError('Symlinked plugin source is forbidden')
    chosen=selected_skills(language_skills)
    files={'plugin.json':manifest_path}
    for script in ACCOUNT_SCRIPTS:
        path=source_root/'scripts'/script
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing or unsafe packaging script: {script}')
        files[f'scripts/{script}']=path
    compat=source_root/'.codex-plugin/plugin.json'
    if compat.is_file() and not compat.is_symlink():
        files['.codex-plugin/plugin.json']=compat
    for skill in chosen:
        directory=skillroot/skill
        if not (directory/'SKILL.md').is_file():
            raise ValueError(f'Missing skill {skill}')
        for path in directory.rglob('*'):
            if not path.is_file():
                continue
            relative=path.relative_to(source_root)
            if any(part in IGNORED_PARTS for part in relative.parts) or path.suffix.lower() in {'.pyc','.pyo'}:
                continue
            if (path.is_symlink() or any(part in DENIED_PARTS for part in relative.parts)
                    or relative.suffix.lower() in DENIED_EXTENSIONS):
                raise ValueError(f'Unsafe plugin asset: {relative}')
            files[relative.as_posix()]=path
    # Reconstruct exact archive paths from allowlisted project paths, never JSON.
    name=manifest['name']
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'w',ZIP_DEFLATED,compresslevel=9) as archive:
        for rel,path in sorted(files.items()):
            info=ZipInfo(f'{name}/{rel}',date_time=(2026,1,1,0,0,0))
            info.compress_type=ZIP_DEFLATED
            info.external_attr=0o644<<16
            archive.writestr(info,path.read_bytes())
    return {'output':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'skill_count':len(chosen),'skills':list(chosen),'version':manifest['version'],
            'installation':'not_started','plugin_creator_required':True}


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--language-skills',choices=['none','ko','ja','ko,ja'],default='none')
    args=p.parse_args()
    print(json.dumps(build_account_plugin(Path(__file__).resolve().parents[1],args.output,
                                          language_skills=args.language_skills),indent=2))


if __name__=='__main__':
    main()
