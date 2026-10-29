"""Evidence-index regression: document text and private paths never become pack data."""
import math
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'skills/company-profile-analyzer/scripts'))

from visual_evidence import build_evidence_index, prepare_visual_workspace  # noqa: E402


def source_doc(kind='pdf'):
    return {'format': kind, 'pages': [{
        'number': 1, 'size_pt': [600, 400],
        'shapes': [{'kind': 'text', 'bbox_pt': [60, 40, 300, 90] if kind=='pdf' else [60, 40, 240, 50],
                    'text': 'TOP SECRET internal sentence', 'measurement': 'observed'},
                   {'kind': 'image', 'bbox_pt': [100, 100, 350, 280] if kind=='pdf' else [100, 100, 250, 180],
                    'text': '', 'measurement': 'observed'}],
    }]}


@pytest.mark.parametrize('kind', ['pdf', 'pptx'])
def test_normalization_is_equivalent_without_source_text(kind):
    index=build_evidence_index(source_doc(kind), source_id='SRC-SAMPLE',document_family='profile')
    page=index['pages'][0]
    assert page['number']==1
    assert index['schema_version']=='visual-evidence/1.0'
    assert page['regions'][0]['bbox_norm']==[0.1,0.1,0.5,0.225]
    assert page['regions'][0]['region_id']=='SRC-SAMPLE-P1-R1'
    assert 'TOP SECRET' not in str(index)
    assert 'text' not in page['regions'][0]


@pytest.mark.parametrize('bad', [[math.nan,0,1,1],[-1,0,5,5],[0,0,700,20], [1,1,0,0]])
def test_malformed_bounding_box_rejected(bad):
    source=source_doc()
    source['pages'][0]['shapes'][0]['bbox_pt']=bad
    with pytest.raises(ValueError):
        build_evidence_index(source, source_id='SRC-SAMPLE',document_family='profile')


def test_invalid_canvas_rejected():
    source=source_doc()
    source['pages'][0]['size_pt']=[0,400]
    with pytest.raises(ValueError):
        build_evidence_index(source, source_id='SRC-SAMPLE',document_family='profile')


def test_pdf_zero_area_extracted_image_is_quarantined_without_losing_page():
    source=source_doc()
    source['pages'][0]['shapes'].insert(1,{'kind':'image','bbox_pt':[0,0,0,0],
                                         'measurement':'observed_pdf_geometry'})
    index=build_evidence_index(source,source_id='SRC-SAMPLE',document_family='profile')
    assert [r['region_id'] for r in index['pages'][0]['regions']]==[
        'SRC-SAMPLE-P1-R1','SRC-SAMPLE-P1-R3']
    assert index['pages'][0]['quarantined_regions']==1
    assert 'TOP SECRET' not in str(index)


def test_user_supplied_zero_area_image_is_still_rejected():
    source=source_doc()
    source['pages'][0]['shapes'][1]['bbox_pt']=[0,0,0,0]
    with pytest.raises(ValueError):
        build_evidence_index(source,source_id='SRC-SAMPLE',document_family='profile')


def test_pdf_vector_geometry_is_evidence_but_not_artwork(tmp_path):
    fitz=pytest.importorskip('fitz')
    pdf=tmp_path/'vector-evidence.pdf'
    doc=fitz.open()
    page=doc.new_page(width=600,height=400)
    page.draw_rect(fitz.Rect(20,30,580,110),color=None,fill=(0.1,0.2,0.3))
    page.draw_line(fitz.Point(5,160),fitz.Point(595,160),color=(0.8,0.2,0.3),width=8)
    doc.save(pdf)
    doc.close()
    from document_extract import extract_document
    index=build_evidence_index(extract_document(pdf),source_id='SRC-VECTOR',document_family='profile')
    vectors=[r for r in index['pages'][0]['regions'] if r['kind']=='vector']
    assert len(vectors)>=2
    assert any(r['bbox_norm'][0]<0.04 and r['bbox_norm'][2]>0.96 for r in vectors)
    assert 'path' not in str(index).lower()


def test_pdf_vector_evidence_filters_micro_artifacts_and_caps_page_density(tmp_path):
    fitz=pytest.importorskip('fitz')
    pdf=tmp_path/'dense.pdf'
    doc=fitz.open()
    page=doc.new_page(width=600,height=400)
    page.draw_rect(fitz.Rect(0,0,600,60),fill=(0,0,0),color=None)
    for row in range(10):
        for column in range(20):
            x,y=column*25,row*30+70
            page.draw_rect(fitz.Rect(x,y,x+8,y+8),fill=(1,0,0),color=None)
    doc.save(pdf)
    doc.close()
    from document_extract import extract_document
    extracted=extract_document(pdf)
    vectors=[s for s in extracted['pages'][0]['shapes'] if s['kind']=='vector']
    assert 1<=len(vectors)<=80
    assert any(s['bbox_pt']==[0.0,0.0,600.0,60.0] for s in vectors)


def test_workspace_renders_separately_and_rejects_existing_content(tmp_path):
    fitz=pytest.importorskip('fitz')
    pdf=tmp_path/'example.pdf'
    doc=fitz.open()
    page=doc.new_page(width=600,height=400)
    page.insert_text((60,60),'Sensitive internal paragraph')
    doc.save(pdf)
    doc.close()
    from document_extract import extract_document
    workspace=tmp_path/'private-preview'
    index_path=prepare_visual_workspace(pdf,extract_document(pdf),source_id='SRC-SAMPLE',
                                        document_family='profile',workspace=workspace)
    assert index_path.is_file()
    assert (workspace/'previews'/'page-01.png').is_file()
    assert 'Sensitive internal paragraph' not in index_path.read_text()
    with pytest.raises(FileExistsError):
        prepare_visual_workspace(pdf,extract_document(pdf),source_id='SRC-SAMPLE',
                                 document_family='profile',workspace=workspace)
