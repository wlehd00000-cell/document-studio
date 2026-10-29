"""Evaluation must measure real PDF behavior without redistributing source text."""

from pathlib import Path
import json
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_public_company import evaluate_public_company,render_style_hypothesis  # noqa: E402


def test_public_pdf_evaluation_is_holdout_based_and_text_free(tmp_path):
    fitz=pytest.importorskip('fitz')
    pdf=tmp_path/'official-public-test.pdf'
    doc=fitz.open()
    for index in range(3):
        page=doc.new_page(width=600,height=420)
        page.draw_rect(fitz.Rect(10,10,400,70),fill=(0.0,0.65,0.3),color=None)
        if index==0:
            page.draw_line(fitz.Point(50,90),fitz.Point(550,90),color=(0.98,0.42,0.18),width=8)
        page.insert_text((55,160),'SOURCE SECRET TEXT MUST NOT APPEAR',fontsize=20)
    doc.save(pdf)
    doc.close()

    result=evaluate_public_company(pdf,company='Example',
                                   source_url='https://example.org/official.pdf',
                                   language='en-US',training_pages=2)
    assert result['source']['pages']==3
    assert result['source']['page_orientation']=='landscape'
    assert result['color_holdout']['shared_train_holdout_colors']>=1
    assert result['color_holdout']['train_pages']==2
    assert '#00A64D' in result['design']['proposed_brand_colors'].values()
    assert 'SOURCE SECRET TEXT' not in json.dumps(result)
    assert result['release_gate']['company_pack_status']=='draft_only'
    assert result['release_gate']['full_visual_reproduction']=='NOT_EVALUATED'

    html=render_style_hypothesis(result)
    assert '--brand-primary:#00A64D' in html
    assert 'EVALUATION ONLY' in html
    assert 'Fictional sample data' in html
    assert 'SOURCE SECRET TEXT' not in html


def test_public_pdf_evaluation_rejects_non_https_provenance(tmp_path):
    with pytest.raises(ValueError,match='HTTPS'):
        evaluate_public_company(tmp_path/'not-needed.pdf',company='Example',
                                source_url='file:///private.pdf',language='en-US')
