"""Export a privacy-audited, installable Company Pack plugin ZIP.

Public distribution only. Private originals/font binaries never travel with
the package; non-synthetic packs with private or uncertain rights are blocked.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
from company_pack import load_company_pack  # noqa: E402
from build_package_manifest import inventory  # noqa: E402
from install_local import selected_skills,verify_package  # noqa: E402


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def _audit_public(pack) -> dict:
    if pack.metadata['status']!='approved':
        raise ValueError('Only explicitly approved Company Packs may be exported')
    path=pack.root/'sources.json'
    if pack.metadata.get('synthetic') is True:
        return {'sources':[],'scope':'independent_fictional_demo'}
    if not path.is_file():
        raise ValueError('Non-synthetic packs require a source-rights inventory')
    data=json.loads(path.read_text(encoding='utf8'))
    sources=data.get('sources')
    if not isinstance(sources,list) or not sources:
        raise ValueError('Invalid or empty rights inventory')
    for source in sources:
        if source.get('visibility')!='public' or source.get('distribution_authorized') is not True or source.get('rights','unverified').lower() in {
                'unverified','unknown','none','private; distribution not authorized'}:
            raise ValueError('Public export blocked: private or unverified source rights')
    ids={s['source_id'] for s in sources}
    by_id={s['source_id']:s for s in sources}
    for item in (*pack.design_cases,*pack.writing_references):
        if not set(item['source_ids']).issubset(ids):
            raise ValueError('Reference lacks auditable public source rights')
        if item.get('disclosure_scope')=='internal_only':
            raise ValueError('Internal-only reference cannot be publicly exported')
    for ref in pack.writing_references:
        if not all(by_id[sid].get('allow_excerpt_in_pack') is True for sid in ref['source_ids']):
            raise ValueError('Written excerpts are not authorized for public redistribution')
    review_path=pack.root/'review.json'
    if not review_path.is_file():
        raise ValueError('Public export requires a documented Company Pack approval')
    review=json.loads(review_path.read_text(encoding='utf8'))
    if (review.get('status')!='approved' or not review.get('reviewer') or
            {note.get('action') for note in review.get('notes',[])}!={'review','approve'}):
        raise ValueError('Public export requires separate review and approval evidence')
    allowed=('source_id','language','document_family','visibility','rights','allow_excerpt_in_pack','distribution_authorized')
    return {'sources':[{key:s[key] for key in allowed if key in s} for s in sources],
            'scope':'public_metadata_only'}


def _copy_skills(stage: Path, names: tuple[str,...]) -> None:
    for name in names:
        origin=ROOT/'skills'/name
        for path in origin.rglob('*'):
            if path.is_symlink():
                raise ValueError('Distribution sources may not contain symlinks')
            if path.suffix.lower() in {'.otf','.ttf','.woff','.woff2'}:
                raise ValueError('Font binary cannot be redistributed without a separate rights review')
        shutil.copytree(origin,stage/'skills'/name,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc','.pytest_cache'))


def _minimal_pack(pack, rights: dict) -> dict[str,dict]:
    meta={key:pack.metadata[key] for key in
          ('schema_version','pack_id','company_name','version','status','default_language','enabled_languages')}
    meta['parent_pack']=None
    if pack.metadata.get('synthetic') is True:
        meta['synthetic']=True
    result={'pack.json':meta,
            'sources.json':rights,
            'design/tokens.json':deepcopy(pack.design),
            'design/design-casebook.json':{'cases':list(pack.design_cases)},
            'writing/references.json':{'references':list(pack.writing_references)},
            'fonts/policy.json':deepcopy(pack.font_policy)}
    for rel in ('design/layout-patterns.json','writing/rules.json','writing/glossary.json'):
        path=pack.root/rel
        if path.is_file():
            result[rel]=json.loads(path.read_text(encoding='utf8'))
    return result


def export_company_plugin(company_pack: Path, output: Path, *, language_skills: str = 'none') -> dict:
    pack=load_company_pack(company_pack)
    rights=_audit_public(pack)
    names=selected_skills(language_skills)
    output=Path(output).expanduser().absolute()
    if output.exists():
        raise FileExistsError('Output ZIP already exists; refuse to overwrite')
    if output.suffix.lower()!='.zip':
        raise ValueError('Output must be a ZIP')
    name=pack.pack_id+'-documents'
    with tempfile.TemporaryDirectory(prefix='document-studio-export-') as temp:
        stage=Path(temp)/name
        stage.mkdir()
        _copy_skills(stage,names)
        for path,contents in _minimal_pack(pack,rights).items():
            _write(stage/'company-pack'/path,contents)
            _write(stage/'skills/company-profile-analyzer/assets/company-pack'/path,contents)
        (stage/'scripts').mkdir(exist_ok=True)
        shutil.copy2(ROOT/'scripts/install_local.py',stage/'scripts/install_local.py')
        shutil.copy2(ROOT/'scripts/build_package_manifest.py',stage/'scripts/build_package_manifest.py')
        plugin=json.loads((ROOT/'plugin.json').read_text(encoding='utf8'))
        plugin['name']=name
        plugin['description']=f'Company-adapted Document Studio for {pack.metadata["company_name"]}; source rights and font rendering require independent review.'
        _write(stage/'plugin.json',plugin)
        app=json.loads((ROOT/'.codex-plugin/plugin.json').read_text(encoding='utf8'))
        app['name']=name
        app['interface']['displayName']=pack.metadata['company_name']+' Documents'
        app['interface']['shortDescription']='Company-specific document profile and editable HTML/PPTX'
        app['interface']['longDescription']='Uses an approved Company Pack. Verify source and font rights independently.'
        _write(stage/'.codex-plugin/plugin.json',app)
        (stage/'README.md').write_text(
            f'# {pack.metadata["company_name"]} Documents\n\n'
            'Install with `python3 scripts/install_local.py` after verifying the bundle. '
            'The active Company Pack is also bundled in '
            '`skills/company-profile-analyzer/assets/company-pack/`. '
            'For document production, pass this directory to `--company-pack`. '
            'Font binaries and original source documents are deliberately omitted. '
            'Run actual rendering and rights checks before claiming official reproduction.\n',encoding='utf8')
        manifest={'name':name,'version':plugin['version'],
                  'included_skills':list(names),'included_language_skills':language_skills,
                  'company_pack':{'pack_id':pack.pack_id,'version':pack.version},
                  'distribution':'public','files':{}}
        manifest['files']=inventory(stage)
        _write(stage/'package-manifest.json',manifest)
        verify_package(stage)
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for path in sorted(stage.rglob('*')):
                if not path.is_file():
                    continue
                info=zipfile.ZipInfo((Path(name)/path.relative_to(stage)).as_posix(),
                                     date_time=(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o644<<16
                archive.writestr(info,path.read_bytes())
    return {'output':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'pack_id':pack.pack_id,'pack_version':pack.version,'skills':list(names),
            'distribution':'public'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--company-pack',type=Path,required=True)
    p.add_argument('--language-skills',choices=['none','ko','ja','ko,ja'],default='none')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(export_company_plugin(a.company_pack,a.output,language_skills=a.language_skills),
                     ensure_ascii=False,indent=2))
