"""Register authorized source files with provenance before analysis.

The registry lives in a user-selected private analysis workspace, never in an
exported Company Pack. No URLs are fetched and no document text is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


LANG = re.compile(r'^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})+$')
KINDS = {'pdf', 'pptx'}
VISIBILITY = {'public', 'private'}


def digest_file(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def register_source(registry_file: Path, file_path: Path, *, title: str, language: str,
                    document_family: str, visibility: str, source_url: str | None = None,
                    rights: str = 'unverified', allow_excerpt_in_pack: bool = False,
                    distribution_authorized: bool = False) -> dict:
    source = Path(file_path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ValueError('Source must be an existing regular file, not a symlink')
    if source.suffix.lower().lstrip('.') not in KINDS:
        raise ValueError('Only PDF and PPTX are supported in this extraction stage')
    if not title.strip() or not document_family.strip():
        raise ValueError('Title and document family are required')
    if not LANG.fullmatch(language):
        raise ValueError('Language must be a full BCP-47 tag such as ja-JP')
    if visibility not in VISIBILITY:
        raise ValueError('Invalid source visibility')
    if source_url and not source_url.startswith('https://'):
        raise ValueError('Source URL must be HTTPS')
    if allow_excerpt_in_pack and (visibility == 'private' or rights in {'unverified','unknown','none'} or not distribution_authorized):
        raise ValueError('Raw excerpts require explicit distribution authorization, verified rights and public scope')
    sha = digest_file(source)
    item = {'source_id': 'SRC-' + sha[:16].upper(), 'title':title,
            'path': str(source.resolve()), 'format':source.suffix.lower().lstrip('.'),
            'language':language, 'document_family':document_family,
            'visibility':visibility, 'source_url':source_url,
            'rights':rights, 'allow_excerpt_in_pack':allow_excerpt_in_pack,
            'distribution_authorized':distribution_authorized,
            'sha256':sha, 'size_bytes':source.stat().st_size}
    registry_file=Path(registry_file)
    registry={'schema_version':'source-registry/1.0','sources':[]}
    if registry_file.exists():
        registry=json.loads(registry_file.read_text(encoding='utf8'))
        if registry.get('schema_version')!='source-registry/1.0' or not isinstance(registry.get('sources'),list):
            raise ValueError('Invalid existing source registry')
    existing=next((x for x in registry['sources'] if x['source_id']==item['source_id']),None)
    if existing and existing != item:
        raise ValueError('Source with same hash has conflicting provenance; review before updating')
    if not existing:
        registry['sources'].append(item)
    registry_file.parent.mkdir(parents=True,exist_ok=True)
    registry_file.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return item


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('registry',type=Path)
    p.add_argument('file',type=Path)
    p.add_argument('--title',required=True)
    p.add_argument('--language',required=True)
    p.add_argument('--document-family',required=True)
    p.add_argument('--visibility',choices=sorted(VISIBILITY),required=True)
    p.add_argument('--source-url')
    p.add_argument('--rights',default='unverified')
    p.add_argument('--allow-excerpt-in-pack',action='store_true')
    p.add_argument('--distribution-authorized',action='store_true',
                   help='Explicit owner/rights-holder confirmation for public derivative distribution')
    a=p.parse_args()
    item=register_source(a.registry,a.file,title=a.title,language=a.language,
                         document_family=a.document_family,visibility=a.visibility,
                         source_url=a.source_url,rights=a.rights,
                         allow_excerpt_in_pack=a.allow_excerpt_in_pack,
                         distribution_authorized=a.distribution_authorized)
    # Never print private source paths in ordinary CLI status.
    print(json.dumps({k:item[k] for k in ['source_id','title','visibility','sha256']},ensure_ascii=False))


if __name__=='__main__':main()
