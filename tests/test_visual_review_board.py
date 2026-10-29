"""A local review board shows private page thumbnails without redistributing them."""
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
from visual_review_board import build_review_board, default_fictional_examples  # noqa: E402
from visual_evidence import build_evidence_index  # noqa: E402


def sample_index():
    return build_evidence_index({'format':'pdf','pages':[{'number':1,'size_pt':[100,100],
                   'shapes':[{'kind':'text','bbox_pt':[10,10,90,30],'text':'Never publish me'}]}]},
                source_id='SRC-X',document_family='profile')


def sample_grammar():
    return {'schema_version':'layout-grammar/1.0','rules':[
        {'rule_id':'title','layer':'brand_dna','document_family':'profile',
         'page_families':['evidence'],'element_roles':['heading'],
         'relationships':[],'constraints':{},'variation':['scale'],
         'evidence_ids':['EV-001'],'evidence_refs':[{'source_id':'SRC-X','page':1,'region_id':'SRC-X-P1-R1'}],
         'confidence':'medium','status':'suggested','reason':'<script>alert(1)</script>'}]}


def test_board_shows_regions_and_distinct_fictional_layouts(tmp_path):
    workspace=tmp_path/'review'
    (workspace/'previews').mkdir(parents=True)
    (workspace/'previews'/'page-01.png').write_bytes(b'png')
    target=build_review_board(sample_index(),sample_grammar(),
                 private_preview_root=workspace,output=workspace/'review.html',
                 fictional_examples=default_fictional_examples())
    html=target.read_text()
    assert 'SRC-X-P1-R1' in html
    assert 'previews/page-01.png' in html
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert 'Never publish me' not in html
    assert str(workspace) not in html
    assert 'Brand DNA' in html and 'Layout Grammar' in html and 'Creative Vocabulary' in html
    assert len({ex['layout'] for ex in default_fictional_examples()})==3


def test_board_refuses_duplicate_or_missing_samples(tmp_path):
    workspace=tmp_path/'workspace'
    (workspace/'previews').mkdir(parents=True)
    (workspace/'previews'/'page-01.png').write_bytes(b'png')
    samples=default_fictional_examples()
    samples[1]['layout']=samples[0]['layout']
    with pytest.raises(ValueError):
        build_review_board(sample_index(),sample_grammar(),
                           private_preview_root=workspace,output=workspace/'out.html',
                           fictional_examples=samples)


def test_board_stays_inside_private_workspace(tmp_path):
    workspace=tmp_path/'workspace'
    workspace.mkdir()
    with pytest.raises(ValueError):
        build_review_board(sample_index(),sample_grammar(),
                           private_preview_root=workspace,output=tmp_path/'public.html',
                           fictional_examples=default_fictional_examples())


def test_board_can_live_in_nested_private_review_folder(tmp_path):
    workspace=tmp_path/'private'
    (workspace/'previews').mkdir(parents=True)
    (workspace/'previews'/'page-01.png').write_bytes(b'png')
    (workspace/'review').mkdir()
    output=build_review_board(sample_index(),sample_grammar(),
        private_preview_root=workspace,output=workspace/'review'/'index.html',
        fictional_examples=default_fictional_examples())
    assert '../previews/page-01.png' in output.read_text()


def test_board_offers_visual_vector_toggle_and_relationship_labels(tmp_path):
    workspace=tmp_path/'private'
    (workspace/'previews').mkdir(parents=True)
    (workspace/'previews'/'page-01.png').write_bytes(b'png')
    index=sample_index()
    index['pages'][0]['regions'].append({'region_id':'SRC-X-P1-R2','kind':'vector',
                                         'bbox_norm':[0.02,0.35,0.98,0.5],
                                         'measurement':'observed_pdf_vector_bounds'})
    grammar=sample_grammar()
    grammar['rules'][0]['relationships']=['heading above accent_band']
    grammar['rules'][0]['element_roles']=['heading','accent_band']
    grammar['rules'][0]['evidence_refs'].append({'source_id':'SRC-X','page':1,'region_id':'SRC-X-P1-R2'})
    target=build_review_board(index,grammar,private_preview_root=workspace,
                              output=workspace/'index.html',fictional_examples=default_fictional_examples())
    html=target.read_text()
    assert 'id="show-vectors"' in html
    assert 'class="region vector"' in html
    assert 'heading above accent_band' in html
