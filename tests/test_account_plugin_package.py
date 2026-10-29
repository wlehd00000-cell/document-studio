"""Create Plugin Creator-compatible ZIPs without shipping source documents."""
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from package_account_plugin import build_account_plugin  # noqa: E402


def files_in(path):
    with ZipFile(path) as archive:
        files=set(archive.namelist())
        prefix='document-studio/'
        manifest=json.loads(archive.read(prefix+'plugin.json'))
        return files,manifest


def test_basic_private_plugin_archive_has_correct_manifest_and_core(tmp_path):
    target=tmp_path/'document-studio.zip'
    result=build_account_plugin(ROOT,target,language_skills='none')
    files,manifest=files_in(target)
    assert result['skill_count']==8
    assert manifest['$schema']=='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
    assert manifest['name']=='document-studio'
    assert 'document-studio/skills/company-profile-analyzer/SKILL.md' in files
    assert 'document-studio/scripts/export_company_plugin.py' in files
    assert 'document-studio/scripts/package_account_plugin.py' in files
    assert 'document-studio/skills/business-japanese-translation/SKILL.md' not in files
    assert all(name.startswith('document-studio/') for name in files)
    assert not any(name.lower().endswith(('.pdf','.pptx','.ai','.otf','.ttf')) for name in files)
    with pytest.raises(FileExistsError):
        build_account_plugin(ROOT,target)


def test_optional_languages_included_only_when_selected(tmp_path):
    target=tmp_path/'both.zip'
    result=build_account_plugin(ROOT,target,language_skills='ko,ja')
    files,_=files_in(target)
    assert result['skill_count']==10
    assert 'document-studio/skills/business-korean-translation/SKILL.md' in files
    assert 'document-studio/skills/business-japanese-translation/SKILL.md' in files


def test_source_symlinks_are_not_packaged(tmp_path):
    source=tmp_path/'clone'
    (source/'skills'/'example').mkdir(parents=True)
    (source/'plugin.json').write_text((ROOT/'plugin.json').read_text())
    (source/'skills'/'example'/'SKILL.md').symlink_to(ROOT/'README.md')
    with pytest.raises(ValueError):
        build_account_plugin(source,tmp_path/'out.zip',language_skills='none')
