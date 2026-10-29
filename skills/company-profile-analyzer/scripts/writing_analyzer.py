"""Extract draft Writing DNA with explicit scope and source provenance."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re


def detect_language(text: str) -> str:
    counts={'ko':len(re.findall(r'[\uac00-\ud7af]',text)),
            'ja':len(re.findall(r'[\u3040-\u30ff]',text)),
            'en':len(re.findall(r'[A-Za-z]',text))}
    return max(counts,key=counts.get) if any(counts.values()) else 'und'


def analyze_writing(extracted: dict, *, source_id: str, language: str,
                    document_family: str, allow_excerpt: bool = False) -> dict:
    paragraphs=[shape['text'].strip() for p in extracted.get('pages',[]) for shape in p.get('shapes',[])
                if shape.get('kind')=='text' and isinstance(shape.get('text'),str) and shape['text'].strip()]
    sentences=[s.strip() for p in paragraphs for s in re.split(r'(?<=[.!?。！？])\s*',p) if s.strip()]
    endings=Counter()
    for sentence in sentences:
        if sentence.endswith(('합니다','습니다','.')):
            endings['formal_or_declarative']+=1
        if sentence.endswith(('です。','ます。')):
            endings['polite_ja']+=1
        if sentence.endswith(('だ。','である。')):
            endings['plain_ja']+=1
    observed_langs=Counter(detect_language(p) for p in paragraphs)
    headings=[p for p in paragraphs if len(p)<=65 and not p.endswith(('.', '。', '!', '！'))]
    candidates=Counter(w.casefold() for p in paragraphs for w in re.findall(r'[A-Za-z][A-Za-z-]{4,}',p))
    rules=[{'language':language,'document_family':document_family,
            'rule':'Confirm register, brevity and headings against the original pages before adoption',
            'confidence':'low','source_ids':[source_id],'status':'suggested'}]
    if sentences:
        rules.append({'language':language,'document_family':document_family,
                      'rule':f'Measured average sentence length: {sum(map(len,sentences))/len(sentences):.1f} characters in this source',
                      'confidence':'high','source_ids':[source_id],'status':'observed'})
    if headings:
        rules.append({'language':language,'document_family':document_family,
                      'rule':f'{len(headings)} potential nominal headings identified; confirm semantic role visually',
                      'confidence':'low','source_ids':[source_id],'status':'suggested'})
    examples=[]
    if allow_excerpt:
        for i,text in enumerate(paragraphs[:3],1):
            if len(text)<10:
                continue
            examples.append({'id':f'{source_id.lower()}-excerpt-{i}','language':language,
                             'document_family':document_family,'writing_function':'general_body',
                             'text':text[:500], 'source_ids':[source_id],
                             'status':'observed','confidence':'medium',
                             'disclosure_scope':'public_approved'})
    return {'source_ids':[source_id],'language':language,'document_family':document_family,
            'paragraph_count':len(paragraphs),'sentence_count':len(sentences),
            'average_sentence_chars':round(sum(map(len,sentences))/len(sentences),1) if sentences else None,
            'observed_scripts':dict(observed_langs),'ending_patterns':dict(endings),
            'potential_heading_count':len(headings),
            'terminology_candidates':[{'term':term,'count':count} for term,count in candidates.most_common(15)],
            'rules':rules,'references':examples,
            'analysis_status':'draft_not_company_wide_rule',
            'private_text_excluded':not allow_excerpt}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extraction',type=Path)
    p.add_argument('--source-id',required=True)
    p.add_argument('--language',required=True)
    p.add_argument('--document-family',required=True)
    p.add_argument('--allow-excerpt',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    extracted=json.loads(a.extraction.read_text(encoding='utf8'))
    result=analyze_writing(extracted,source_id=a.source_id,language=a.language,
                           document_family=a.document_family,allow_excerpt=a.allow_excerpt)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'source_ids':result['source_ids'],'paragraphs':result['paragraph_count'],
                      'status':result['analysis_status']}))
