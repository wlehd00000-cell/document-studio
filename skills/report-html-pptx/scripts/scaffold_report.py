"""Create portable DEMO report with populated and escaped HTML metadata."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import shutil
from intake import resolve_intake
from design_expression import resolve_expression
from authoring_routes import select_route
from project_state import ProjectState
from design_registry import CANVASES, TOKENS, select_profile, font_for, tokens_for
from company_pack import load_company_pack
from select_layout_grammar import select_layout_grammar
from layout_plan import company_pack_snapshot
from build_design_css import generate as generate_design_css
from font_policy import evaluate_font_policy

def scaffold(destination, title, subtitle, language=None, report_date=None,
             document_type=None, status='DRAFT',
             canvas=None, genre=None, interaction_mode=None,
             audience=None, reader_action=None, output_format=None,
             deliverable_languages=None, delegated_fields=None, conversation_language=None,
             type_profile=None, density_mode=None, output_profile=None,
             authoring_route=None, use=None, design_profile=None, template_path=None,
             native_capability_verified=False, native_authoring_requested=False,
             native_creative_evidence=None, design_preferences=None, company_pack=None):
    expression = resolve_expression(design_preferences)
    supplied = {
        'final_language': language, 'document_type': genre or document_type,
        'mode': interaction_mode, 'audience': audience,
        'purpose': reader_action, 'output_format': output_format}
    submission = {'schema_version':'1.0', 'fields':{k:v for k,v in supplied.items() if v is not None}}
    if conversation_language:
        submission['conversation_language'] = conversation_language
    if use is not None:
        submission['use'] = use
    if canvas is not None:
        submission['canvas'] = canvas
    startup = resolve_intake(submission)
    if not startup['production_allowed']:
        raise ValueError('Unanswered required brief choices: ' + ', '.join(startup['missing']))
    resolved = {k:r['value'] for k,r in startup['fields'].items()}
    language = resolved['final_language']
    genre = resolved['document_type']
    interaction_mode = resolved['mode']
    audience = resolved['audience']
    reader_action = resolved['purpose']
    output_format = resolved['output_format']
    conversation_language = startup['conversation_language']
    use, canvas = startup['use'], startup['canvas']
    delegated_fields = set(delegated_fields or [])
    allowed_delegations = {'document_type', 'audience', 'purpose', 'final_language', 'output_format'}
    if not delegated_fields.issubset(allowed_delegations):
        raise ValueError('Unknown delegated intake field')
    destination = Path(destination).expanduser().resolve()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError(f'Destination must be new or empty: {destination}')
    if not re.fullmatch(r'[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*', language):
        raise ValueError('Invalid language tag')
    if conversation_language is not None and not re.fullmatch(r'[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*', conversation_language):
        raise ValueError('Invalid conversation language tag')
    deliverable_languages = list(dict.fromkeys([language, *(deliverable_languages or [])]))
    if not deliverable_languages or any(not re.fullmatch(r'[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*', item)
                                        for item in deliverable_languages):
        raise ValueError('Invalid deliverable language tag')
    if len(deliverable_languages) > 1:
        record = startup['fields']['final_language']
        record.update(value='+'.join(deliverable_languages), status='explicit',
                      origin='explicit additional deliverable languages', user_confirmed=True)
        record.pop('reason', None)
        startup['assumptions'].pop('final_language', None)
    report_date = date.fromisoformat(report_date).isoformat() if report_date else date.today().isoformat()
    root = Path(__file__).resolve().parents[1]
    pack = load_company_pack(company_pack) if company_pack else None
    if pack:
        if pack.metadata['status'] != 'approved':
            raise ValueError('Company Pack must be approved for production')
        if any(lang not in pack.metadata['enabled_languages'] for lang in deliverable_languages):
            raise ValueError('Requested document language is not enabled in Company Pack')
    family={'report':'executive_report','submission':'executive_report',
            'proposal':'business_proposal','plan':'implementation_plan',
            'presentation':'presentation','guide':'operational_guide',
            'manual':'operational_guide'}.get(genre,'executive_report')
    tokens = tokens_for(company_pack,family)
    if output_profile is None:
        print_request = re.search(r'인쇄용|(?:문서용|사무용)\s*프린터|A4\s*인쇄|印刷用|事務用.*プリンタ|A4\s*(?:印刷|出力)|office[\s-]+print(?:er)?|A4[\s-]+print', output_format, re.I)
        output_profile = 'office-print' if print_request else 'branded'
    if output_profile not in {'branded', 'office-print'}:
        raise ValueError('Unknown output profile')
    if use is None:
        use = 'office_print' if output_profile == 'office-print' else ('live' if density_mode == 'presentation' else 'reading')
    if use is not None and use not in {'reading','live','office_print','template_edit'}:
        raise ValueError('Unknown final use')
    if use == 'office_print':
        output_profile = 'office-print'
    if use == 'live' and output_profile == 'office-print':
        raise ValueError('Live use and office-print output conflict')
    # Legacy native arguments remain accepted for call compatibility; they cannot
    # switch the authoring source or require inspecting a native-quality dossier.
    route_selection = select_route({'use':use,'output_format':output_format,'template_path':template_path})
    if authoring_route is not None and authoring_route != 'html_report':
        raise ValueError('HTML authoring is fixed; only explicit export requests can change the output adapter')
    authoring_route = 'html_report'
    design_profile = select_profile(genre,use,design_profile,tokens=tokens)
    if design_profile not in tokens['profiles']:
        raise ValueError('Unknown design profile')
    if output_profile == 'office-print' and design_profile != 'office_print':
        raise ValueError('Office print requires office_print design profile')
    if canvas is None:
        raise ValueError('Unanswered canvas decision; profile defaults are recommendations only')
    canvases = {key:list(row['css_px']) for key,row in tokens['canvases'].items()}
    if canvas not in canvases:
        raise ValueError('Unknown canvas')
    if output_profile == 'office-print':
        if canvas not in {'a4-portrait', 'a4-landscape'}:
            raise ValueError('Office print requires an A4 canvas')
        canvases['a4-portrait'] = [value * 96 / 25.4 for value in tokens['canvases']['a4-portrait']['print_mm']]
        canvases['a4-landscape'] = list(reversed(canvases['a4-portrait']))
        if density_mode == 'presentation' or type_profile == 'presentation':
            raise ValueError('Office print requires report density')
    # File genre does not establish live viewing; reading PPTX keeps report density.
    density_mode = density_mode or ('presentation' if use == 'live' else 'report')
    if density_mode not in {'report','presentation'}:
        raise ValueError('Unknown density mode')
    type_profile = type_profile or design_profile
    canonical_type = tokens['legacy_aliases'].get(type_profile, type_profile)
    if canonical_type not in tokens['profiles']:
        raise ValueError('Unknown type profile')
    if type_profile == 'office-print-dense' and output_profile != 'office-print':
        raise ValueError('Office print type profile requires office-print output')
    if (density_mode == 'presentation') != (canonical_type == 'live_deck'):
        raise ValueError('Presentation type profile requires presentation density; use report density for reading PPTX')
    if genre not in {'report','proposal','plan','submission','presentation','guide','manual'}:
        raise ValueError('Unknown document genre')
    audience = audience.strip()
    reader_action = reader_action.strip()
    output_format = output_format.strip()
    if document_type is None:
        labels_ko={'report':'검토 보고서','proposal':'기획안','plan':'실행 계획서','submission':'운영계획(안)','presentation':'발표자료','guide':'안내자료','manual':'운영 매뉴얼'}
        labels_ja={'report':'検討報告書','proposal':'企画提案書','plan':'実行計画書','submission':'運営計画（案）','presentation':'プレゼンテーション資料','guide':'案内資料','manual':'運営マニュアル'}
        labels={'ko':labels_ko,'ja':labels_ja}.get(language.lower().split('-')[0],{})
        document_type=labels.get(genre,genre.upper())
    dimensions = canvases[canvas]
    config = dict(title=title, subtitle=subtitle, language=language, date=report_date,
                  document_type=document_type, status=status, canvas=dimensions, genre=genre,
                  audience=audience, reader_action=reader_action, output_format=output_format)
    config['design_profile']=design_profile
    config['design_expression']=expression
    config['authoring_route']=authoring_route
    config['use']=use
    config['design_tokens_version']=tokens['version']
    if pack:
        config['company_pack']={'pack_id':pack.pack_id,'version':pack.version,
                                'schema_version':pack.metadata['schema_version'],
                                'document_family':family,'lineage':list(pack.lineage),
                                'visual_grammar':{'stage':'pending_final_manuscript',
                                    'rule_ids':[],
                                    'reason':'Plan each actual page after final-language copy is completed'}}
    config['density_mode']=density_mode
    config['typography_profile']=type_profile
    config['canvas_name']=canvas
    config['output_profile']=output_profile
    if output_profile == 'office-print':
        config['print']={'paper':'A4','orientation':'portrait' if canvas == 'a4-portrait' else 'landscape',
                         'scale_percent':100,'safe_margin_mm':8,'side_margin_mm':8.5,
                         'browser_header_footer':False,'physical_test':'not_performed'}
    body_ko={
        'purpose':'이 문서가 돕는 판단·행동','summary':'핵심 요약','summary_title':'핵심 결론과 다음 행동',
        'status':'자료 상태','summary_lead':'독자가 이해해야 할 핵심 메시지와 그 메시지를 뒷받침하는 근거를 실제 내용으로 정리합니다.',
        'finding':'핵심 결론','finding_copy':'확인한 자료에서 도출한 결론을 입력합니다. 제안과 확인된 사실은 구분합니다.',
        'evidence':'근거와 범위','evidence_copy':'결론을 뒷받침하는 표·차트·사진·구조와 해당 출처를 가까이 배치합니다.',
        'conditions':'판단할 조건','conditions_copy':'수치의 기간·단위·범위와 결정에 필요한 조건을 적습니다.',
        'next':'다음 행동','next_title':'독자에게 요청할 판단 또는 실행','next_copy':'누가 무엇을 결정하거나 실행해야 하는지, 필요한 기한과 조건을 실제 내용으로 적습니다.',
        'data_title':'수치의 기준과 자료 상태','data_lead':'표가 답해야 할 질문과 실제 집계 기준·기간·범위를 설명합니다. 자료가 없으면 값을 만들어 넣지 않습니다.',
        'item':'항목','basis':'기준·단위','value':'값','source_status':'출처·상태','example':'예시 항목','pending':'확인 필요',
        'data_note':'—는 자료 미확보를 뜻하며 0이 아닙니다. 실제 제공 자료로 교체하고 출처·기간·집계 범위·수정 사항을 주석으로 명시합니다.',
        'close_title':'판단할 사항과 다음 실행','close_lead':'요청할 결정, 담당·기한·조건, 남은 확인을 실제 내용으로 정리합니다.',
        'decision':'요청할 판단','decision_copy':'선택할 대안과 판단 기준을 입력합니다. 미확인 승인을 완료로 표시하지 않습니다.',
        'execution':'결정 뒤의 실행','execution_copy':'담당·기한·인계 내용·선행 조건을 확인해 적습니다.',
        'remaining':'남은 확인','remaining_copy':'근거의 한계와 추가 확인이 필요한 항목을 짧게 적습니다.'}
    body_ja={
        'purpose':'この資料が支える判断・対応','summary':'要点の整理','summary_title':'主な結論と次の対応',
        'status':'資料の状況','summary_lead':'読者が理解すべき中心メッセージと、それを支える根拠を実際の内容で整理します。',
        'finding':'主な結論','finding_copy':'確認済みの資料から導いた結論を記入します。提案と確認済みの事実を区別します。',
        'evidence':'根拠と範囲','evidence_copy':'結論を支える表・グラフ・写真・構造と、対応する出典を近くに配置します。',
        'conditions':'判断の条件','conditions_copy':'数値の期間・単位・範囲と、判断に必要な条件を記入します。',
        'next':'次の対応','next_title':'読者に依頼する判断または実行','next_copy':'誰が何を判断・実行するか、必要な期限と条件を実際の内容で記入します。',
        'data_title':'数値の基準と資料の状況','data_lead':'表が答える問いと、実際の集計基準・期間・範囲を説明します。資料がない数値は作りません。',
        'item':'項目','basis':'基準・単位','value':'値','source_status':'出典・状況','example':'項目例','pending':'確認が必要',
        'data_note':'—は資料未取得を示し、0ではありません。提示された資料に置き換え、出典・期間・集計範囲・修正事項を注記します。',
        'close_title':'判断事項と次の実行','close_lead':'依頼する判断、担当・期限・条件、残る確認を実際の内容で整理します。',
        'decision':'依頼する判断','decision_copy':'選択肢と判断基準を記入します。未確認の承認を完了と表示しません。',
        'execution':'判断後の実行','execution_copy':'担当・期限・引き継ぐ内容・前提条件を確認して記入します。',
        'remaining':'残る確認','remaining_copy':'根拠の限界と追加確認が必要な事項を簡潔に記入します。'}
    body_ko.update({
        'visual':'사진·핵심 장면·도표 자리','visual_note':'실제 자료에 필요한 시각물로 교체 · 이 영역은 이미지 근거가 아님',
        'caption':'이미지의 출처·시점·관찰할 내용과 개념 여부를 설명합니다.',
        'context':'배경과 해석','context_copy':'대상이 되는 상황과 검토 이유를 자료에 근거해 설명합니다. 핵심 주장에 이르는 맥락과 비교 기준을 함께 적고, 관련 사진·장면·표를 같은 판면에 배치합니다.',
        'limits':'조건과 적용 범위','limits_copy':'자료의 범위와 아직 확인되지 않은 사항을 설명합니다. 사실·제안·가정을 구분하고, 다른 상황에도 적용할 수 있는지 필요한 조건을 가까이 적습니다.',
        'method':'집계 기준과 방법','method_copy':'기간·대상·단위·집계 방법을 설명합니다. 자료마다 범위가 다르면 합산하거나 같은 기준으로 비교하기 전에 차이를 확인합니다. 누락된 값과 수정된 값은 별도로 표시합니다.',
        'interpretation':'자료의 해석','interpretation_copy':'확인한 값이 보여주는 변화와 판단에 미치는 영향을 설명합니다. 원인이 확정되지 않았으면 가설로 구분합니다. 관련 사진·과정도와 출처를 묶어 표의 의미를 읽을 수 있게 합니다.',
        'support':'판단을 뒷받침하는 자료','support_copy':'판단의 근거가 된 자료와 주요 조건을 정리합니다. 상세 내용이 앞쪽에 있으면 해당 쪽을 안내합니다. 확인된 사항과 합의가 필요한 사항을 구분합니다.',
        'followup':'후속 확인과 인계','followup_copy':'다음 검토에서 확인할 질문과 인계할 자료를 적습니다. 담당·기한이 정해지지 않았다면 확인 필요로 표시하며 결정된 사실처럼 쓰지 않습니다.'})
    body_ja.update({
        'visual':'写真・場面図・グラフの配置','visual_note':'資料に合うビジュアルに置換。この部分は画像の根拠ではありません。',
        'caption':'画像の出典・時点・注目する箇所と、概念図かどうかを説明します。',
        'context':'背景と解釈','context_copy':'対象の状況と検討の理由を資料に基づいて説明します。中心となる主張の背景と比較基準を示し、関連する写真・場面図・表を同じ紙面に配置します。',
        'limits':'条件と適用範囲','limits_copy':'資料の範囲と未確認の事項を説明します。事実・提案・仮定を区別し、他の状況への適用に必要な条件を近くに記載します。',
        'method':'集計基準と方法','method_copy':'期間・対象・単位・集計方法を説明します。資料ごとに範囲が異なる場合は、合算や比較の前に違いを確認します。欠損値と修正値は区別して示します。',
        'interpretation':'資料の解釈','interpretation_copy':'確認済みの数値が示す変化と、判断への影響を説明します。要因が確定していない場合は仮説と示します。関連する写真・工程図と出典を組み合わせ、表の意味を伝えます。',
        'support':'判断を支える資料','support_copy':'判断の根拠と主な条件を整理します。詳細が前のページにある場合は参照先を示します。確認済みの事項と合意が必要な事項を区別します。',
        'followup':'次の確認と引き継ぎ','followup_copy':'次の検討で確認する問いと引き継ぐ資料を記載します。担当・期限が未定の場合は要確認とし、決定済みの事実として書きません。'})
    body_labels=body_ja if language.lower().split('-')[0]=='ja' else body_ko
    html_values={**config,**{'label_'+key:value for key,value in body_labels.items()}}
    source = (root/'assets/starter/html/index.html').read_text(encoding='utf-8')
    source = re.sub(r'\{\{(\w+)\}\}', lambda m: escape(str(html_values[m[1]]), quote=True), source)
    if pack:
        original_logo='<img class="cover-logo" src="./assets/demo-mark.svg" alt="Document Studio">'
        neutral_name='<span class="cover-logo company-name">'+escape(pack.metadata['company_name'])+'</span>'
        source=source.replace(original_logo,neutral_name)
        source=source.replace('</style>', '.cover-logo.company-name{display:inline-block;width:auto;max-width:52%;font:600 16px/1.3 sans-serif;letter-spacing:.015em}</style>')
    source = source.replace('</head>', f'<meta name="pptx-width" content="{dimensions[0]}">\n<meta name="pptx-height" content="{dimensions[1]}">\n</head>')
    type_tokens = dict(tokens['profiles'][canonical_type]['typography'])
    type_tokens.update(tokens.get('legacy_typography_overrides', {}).get(type_profile, {}))
    type_values = tuple(str(type_tokens[key+'_pt'])+'pt' for key in ('body','table','caption','subhead','title'))
    geometry = ':root{--page-width:%spx;--page-height:%spx}' % tuple(dimensions)
    typography = '.'+density_mode+'{' + ';'.join('--'+name+':'+value for name,value in
        zip(('body','table','caption','subhead','title'), type_values)) + '}'
    print_size = '@page{size:%spx %spx;margin:0}' % tuple(dimensions)
    if not tokens['profiles'][design_profile].get('band', False) or output_profile == 'office-print':
        source = re.sub(r'<div class="top-rule" aria-hidden="true"><i></i><i></i><i></i></div>', '', source)
    if output_profile == 'office-print':
        print_size = '@page{size:A4 %s;margin:0}' % config['print']['orientation']
        source = re.sub(r'<div class="top-rule" aria-hidden="true"><i></i><i></i><i></i></div>', '', source)
        source = source.replace('</head>', '<link rel="stylesheet" href="./assets/office-print-report.css">\n</head>')
    shared = generate_design_css(tokens) if pack else (root/'assets/demo-esg-design/demo-design-tokens.css').read_text(encoding='utf-8')
    faces=''.join('@font-face{font-family:"%s";src:url("./assets/%s") format("woff2");font-weight:100 900;font-display:swap}' % (face['primary'],Path(face['file']).name) for face in TOKENS['font']['by_language'].values() if (root/'assets/brand'/Path(face['file']).name).is_file()) if not pack else ''
    shared=faces+shared
    profile_grid = tokens['profiles'][design_profile]['grid']
    alignment = '.page-inner{padding-left:%spx;padding-right:%spx}' % (profile_grid['margin_x_px'], profile_grid['margin_x_px'])
    source=source.replace('</style>', shared+geometry+typography+alignment+print_size+'</style>')
    body_class=density_mode+(' portrait' if canvas=='a4-portrait' else '')+(' office-print' if output_profile == 'office-print' else '')
    heading_style = 'message' if genre == 'presentation' else 'nominal'
    source=source.replace('data-pptx-slide class=', 'data-pptx-slide data-design-profile="'+design_profile+'" class=')
    source=source.replace('<body>', '<body class="'+body_class+'" data-type-profile="'+type_profile+'" data-output-profile="'+output_profile+'" data-document-genre="'+genre+'" data-heading-style="'+heading_style+'" data-pptx-text-flow="natural">')
    counter = iter(range(1, 10000))
    source = re.sub(r'<strong>\d+</strong>', lambda m: f'<strong>{next(counter):02}</strong>', source)
    shutil.copytree(root/'assets/starter', destination, dirs_exist_ok=True)
    for folder in ['html/assets', 'content', 'qa', 'final']:
        (destination/folder).mkdir(parents=True, exist_ok=True)
    for name in (['demo-mark.svg', '_external_PretendardJPVariable.woff2', '_external_PretendardVariable.woff2', 'LICENSE-Pretendard.txt'] if not pack else []):
        if (root/'assets/brand'/name).is_file():
            shutil.copy2(root/'assets/brand'/name, destination/'html/assets'/name)
    if output_profile == 'office-print':
        shutil.copy2(root/'assets/demo-esg-design/office-print-report.css', destination/'html/assets/office-print-report.css')
    (destination/'html/index.html').write_text(source, encoding='utf-8')
    # [quality-floor-p0] Resolve bundled fonts before persisting the project.
    if not pack and language.lower().split('-')[0] in {'ko','ja'} and all((root/'assets/brand'/Path(font_for(lang)['file']).name).is_file() for lang in ['ko','ja']):
        from quality_floor import resolve_contract, write_contract
        supported=[x for x in deliverable_languages if x.lower().split('-')[0] in {'ko','ja'}]
        contract=resolve_contract(destination, root/'assets/brand',
            root/'system/design-tokens.json', language=language,
            profile=design_profile, additional_languages=supported)
        write_contract(contract,destination/'content/quality-contract.json')
    if pack:
        import hashlib
        snapshot=company_pack_snapshot(pack)
        raw=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        digest=hashlib.sha256(raw).hexdigest()
        config['company_pack']['snapshot_sha256']=digest
        (destination/'content/company-pack-snapshot.json').write_text(json.dumps({'snapshot':snapshot,'sha256':digest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        font_review=evaluate_font_policy(pack,language,html_path=destination/'html/index.html')
        (destination/'content/font-policy-review.json').write_text(json.dumps(font_review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    checkpoint_status = 'delegated' if interaction_mode == 'one_shot' else 'pending'
    brief = {'genre':genre,'audience':audience,'reader_action':reader_action,
             'requested_outputs':[output_format],
             'intake_gate':{'status':'complete','fields':{}},
             'communication':{'conversation_language':conversation_language,'source_languages':[],
                              'deliverable_languages':deliverable_languages,'secondary_audiences':[],
                              'reader_knowledge':None,'relationship':None,
                              'reading_context':None,'disclosure_scope':None,
                              'bilingual_layout':None},
             'fixed_constraints':[],'source_priority':[],'open_questions':[],
             'research':{'preference':'auto','selected_depth':None,'reason':None,
                         'scope':{},'gaps':[],'stop_reason':None},
             'interaction':{'mode':interaction_mode,
                            'stage':'mode' if interaction_mode is None else 'intent',
                            'pending_question':None},
             'preferences':[],
             'checkpoints':{stage:{'status':checkpoint_status,'artifact':None,
                                   'revision':None,'user_response':None}
                            for stage in ('content','design')},
             'acceptance':'awaiting_feedback',
             'sections':[], 'note':'Project decisions only. Preserve user words and preference provenance; QA is not user acceptance.'}
    if output_profile == 'office-print':
        brief['communication']['reading_context']='office-printer A4 at 100%'
        brief['fixed_constraints'] += ['office-print output; decorative color bands removed', 'Preserve official assets and required source facts']
        brief['print_profile']=config['print'].copy()
    brief['communication']['use']=use
    brief['authoring'] = {**route_selection, 'design_profile':design_profile,
                         'template_path':template_path,
                         'note':'HTML is canonical. Existing template constrains composition; capability and export review remain separate.'}
    brief['production_contract'] = {'version': '2.0', 'design_audit': 'qa/design-contract.json'}
    brief['workflow'] = {'operation':'full', 'pages':'all', 'origin':'Resolved new-document scaffold; preserve request in brief'}
    brief['authoring']['canvas_name'] = canvas
    brief['intake'] = startup
    brief['intake']['use'] = use
    brief['intake']['route_selection'] = route_selection
    brief['intake']['design_expression']=expression
    brief['design_expression']=expression
    delegation_names={'document_type':'document_type','audience':'audience','purpose':'purpose','final_language':'final_language','output_format':'output_format'}
    for key in delegated_fields:
        record=brief['intake']['fields'][delegation_names[key]]
        record.update(status='delegated',origin='specific user delegation',reason='Resolved recommendation supplied by the authoring agent; preserve original user instruction in the brief')
        brief['intake']['assumptions'].pop(key, None)
    brief['intake_gate']['layout_fields'] = {k:r['status'] for k,r in startup['layout']['fields'].items()}
    brief['intake_gate']['fields'] = {k:r['status'] for k,r in startup['fields'].items()}
    (destination/'content/brief.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (destination/'report-config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    project_state = ProjectState(destination)
    project_state.init(['1','2','3','4'], 'html')
    source_nodes = [('brief','content/brief.json','brief'),('config','report-config.json','config'),
                    ('copy','content/final.md','copy')]
    if (destination/'html/assets/demo-mark.svg').is_file():
        source_nodes.append(('logo','html/assets/demo-mark.svg','asset'))
    current_font=font_for(language,tokens)
    if current_font.get('file') and (destination/'html/assets'/Path(current_font['file']).name).is_file():
        source_nodes.append(('font','html/assets/'+Path(current_font['file']).name,'font'))
    if len(deliverable_languages)>1:
        other=next((x for x in deliverable_languages if x!=language),None)
        other_font=font_for(other,tokens) if other else {}
        if other_font.get('file') and (destination/'html/assets'/Path(other_font['file']).name).is_file():
            source_nodes.append(('font_secondary','html/assets/'+Path(other_font['file']).name,'font'))
    if pack:
        source_nodes.append(('company_pack','content/company-pack-snapshot.json','policy'))
        source_nodes.append(('font_review','content/font-policy-review.json','policy'))
    if output_profile == 'office-print':
        source_nodes.append(('print_style','html/assets/office-print-report.css','style'))
    # [quality-floor-p0] ProjectState remains the single state/receipt authority.
    if (destination/'content/quality-contract.json').is_file():
        source_nodes.append(('quality_contract','content/quality-contract.json','policy'))
    for key,path,role in source_nodes:
        project_state.register(key, path, 'source', role)
    project_state.register('html','html/index.html','artifact','html',depends=[key for key,_,_ in source_nodes])
    project_state.snapshot('html')
    # Actual starter production receipt only: all editorial/visual/export QA stays missing.
    return {'project':str(destination), 'pages':4, 'route':authoring_route, 'status':'scaffold; replace all example copy'}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination')
    p.add_argument('--title', default='DOCUMENT STUDIO REPORT')
    p.add_argument('--subtitle', default='REPORT / WORKING DRAFT')
    p.add_argument('--language', help='Resolved final language; omission remains pending')
    p.add_argument('--conversation-language', help='Detected or explicitly requested chat language; separate from final file language')
    p.add_argument('--deliverable-language', action='append', dest='deliverable_languages',
                   help='Additional requested output language; repeat for bilingual/multilingual deliverables')
    p.add_argument('--date', dest='report_date')
    p.add_argument('--document-type', default=None)
    p.add_argument('--status', default='DRAFT')
    p.add_argument('--canvas', choices=['a4-portrait','a4-landscape','esg-landscape','widescreen'], default=None)
    p.add_argument('--density-mode', choices=['report','presentation'], default=None, help='Defaults to report density, including reading PPTX; select presentation only for live viewing')
    p.add_argument('--type-profile', default=None, help='Canonical typography profile or accepted legacy alias from system/design-tokens.json')
    p.add_argument('--design-profile', default=None, help='Purpose profile from canonical design tokens')
    p.add_argument('--authoring-route', choices=['html_report'])
    p.add_argument('--use', choices=['reading','live','office_print','template_edit'], help='Actual reader use; PPTX alone does not imply live presentation')
    p.add_argument('--template-path', help='Actual accepted template source; composition remains HTML')
    p.add_argument('--native-capability-verified', action='store_true', help='Legacy compatibility flag; ignored by fixed HTML authoring')
    p.add_argument('--native-authoring-requested', action='store_true', help='Legacy compatibility flag; cannot select native authoring')
    p.add_argument('--native-creative-evidence', help='Legacy compatibility argument; ignored by fixed HTML authoring')
    p.add_argument('--output-profile', choices=['branded','office-print'], default=None, help='Office-printer A4 use removes decorative bands and preserves dense report type; otherwise branded')
    p.add_argument('--genre', choices=['report','proposal','plan','submission','presentation','guide','manual'])
    p.add_argument('--interaction-mode', choices=['one_shot','collaborative'],
                   help='Resolved mode; omission remains pending')
    p.add_argument('--audience', help='Resolved primary reader; omission remains pending')
    p.add_argument('--reader-action', help='Purpose or decision/action expected from the reader')
    p.add_argument('--output-format', help='Resolved output format; PPTX does not determine canvas')
    p.add_argument('--company-pack',type=Path,help='Approved organization profile directory')
    p.add_argument('--delegated-field', action='append', default=[], dest='delegated_fields',
                   choices=['document_type','audience','purpose','final_language','output_format'],
                   help='Record a required value the user explicitly delegated for recommendation')
    print(json.dumps(scaffold(**vars(p.parse_args())), ensure_ascii=True))
