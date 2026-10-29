"""Build an offline asset comparison from a DEMO visual-assets registry.

Standard library only. No registry mutation, image generation, installation,
network access or visual quality certification.
"""
import argparse
import hashlib
import html
import json
import os
import struct
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

LABELS = {
    'ko': {'title': '시각자산 · 세트 비교', 'none': '반환 파일 없음',
           'missing': '파일 미확보', 'invalid': '프로젝트 밖 경로',
           'unsupported': '미지원 미리보기 형식', 'source': '출처 유형',
           'note': '실제 크기·획·시점·색·의미를 비교하세요. 파일 존재와 해시는 시각 검토나 사용자 승인의 증거가 아닙니다.',
           'status': '제작 상태', 'visual': '시각 검토', 'set': '세트 비교',
           'unknown': '크기 확인 불가', 'fallback': '브라우저에서 이미지를 볼 수 없으면 링크로 원본을 여세요.'},
    'ja': {'title': 'ビジュアル素材 · シリーズ比較', 'none': '成果物ファイルなし',
           'missing': 'ファイル未取得', 'invalid': 'プロジェクト外のパス',
           'unsupported': 'プレビュー非対応形式', 'source': '出典の種類',
           'note': '実際の大きさ・線・視点・色・意味を比較してください。ファイルやハッシュの確認だけでは、目視確認やユーザー承認の証拠にはなりません。',
           'status': '制作状態', 'visual': '目視確認', 'set': 'シリーズ比較',
           'unknown': '寸法未確認', 'fallback': '画像を表示できない場合はリンクから元ファイルを開いてください。'},
}

def within(root, value):
    path = Path(value)
    target = (path if path.is_absolute() else root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError('Path is outside the explicit project root: ' + str(value))
    return target

def dimensions(path):
    if path.suffix.lower() == '.png':
        with path.open('rb') as stream:
            header = stream.read(24)
        if len(header) == 24 and header[:8] == b'\x89PNG\r\n\x1a\n' and header[12:16] == b'IHDR':
            width, height = struct.unpack('>II', header[16:24])
            return {'width': width, 'height': height, 'units': 'px'}
    if path.suffix.lower() == '.svg':
        if path.stat().st_size > 5_000_000:
            return None
        try:
            element = ET.parse(path).getroot()
            box = element.get('viewBox', '').replace(',', ' ').split()
            if len(box) == 4:
                return {'width': float(box[2]), 'height': float(box[3]), 'units': 'viewBox'}
        except (ET.ParseError, ValueError, OSError):
            return None
    return None

def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def records_from(data):
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and isinstance(data.get('assets'), list):
        records = data['assets']
    elif isinstance(data, dict) and 'asset_id' in data:
        records = [data]
    else:
        raise ValueError('Registry must be an asset record, an array, or an object containing assets.')
    if any(not isinstance(item, dict) for item in records):
        raise ValueError('Each registry entry must be an object.')
    return records

def esc(value):
    return html.escape(str(value), quote=True)

def localized_status(value, lang):
    translations = {
        'not_started': ('미착수', '未着手'), 'produced': ('파일 제작됨', 'ファイル作成済み'),
        'partial': ('일부 완료', '一部完了'), 'blocked': ('진행 불가', '進行不可'),
        'not_performed': ('미실시', '未実施'), 'passed': ('검토 통과', '確認済み'),
        'issues_found': ('보완 필요', '修正が必要'), 'unavailable': ('실시 불가', '実施不可'),
        'not_applicable': ('해당 없음', '対象外'),
        'generated_concept': ('생성 개념 이미지', '生成した概念画像'),
        'provided_original': ('제공 원본', '提供された原本'),
        'sourced_original': ('확보한 원본', '取得した原本'),
        'adapted_vector': ('원본 벡터 기반', '原本ベクターを基に制作'),
        'capture': ('출처 화면 캡처', '出典画面のキャプチャ'),
    }
    return translations.get(value, (value, value))[lang == 'ja']

def build(args):
    root = args.project_root.resolve()
    if not root.is_dir():
        raise ValueError('Project root is not a directory.')
    registry = within(root, args.registry)
    out = within(root, args.out)
    if out == registry:
        raise ValueError('Output must not replace the registry.')
    report_path = within(root, args.metadata_out) if args.metadata_out else None
    if report_path and report_path in (out, registry):
        raise ValueError('Metadata output must be a distinct file.')
    data = json.loads(registry.read_text(encoding='utf-8-sig'))
    records = records_from(data)
    labels = LABELS[args.language]
    cards, metadata, errors, referenced_paths = [], [], 0, set()
    for record in records:
        asset_id = str(record.get('asset_id', 'unnamed'))
        delivery = record.get('delivery') or {}
        if not isinstance(delivery, dict):
            raise ValueError('delivery must be an object: ' + asset_id)
        review = delivery.get('review') or {}
        if not isinstance(review, dict):
            raise ValueError('delivery.review must be an object: ' + asset_id)
        purpose = record.get('purpose') or {}
        message = purpose.get('message', purpose.get('visual_job', '')) if isinstance(purpose, dict) else purpose
        figures = []
        files = delivery.get('files') or []
        if not isinstance(files, list):
            raise ValueError('delivery.files must be an array: ' + asset_id)
        if not files:
            figures.append('<p class="missing">' + labels['none'] + '</p>')
        for entry in files:
            name = entry if isinstance(entry, str) else entry.get('path') if isinstance(entry, dict) else None
            info = {'asset_id': asset_id, 'requested_file': name, 'exists': False,
                    'visual_review_performed_by_helper': False}
            if not name:
                info['error'] = 'Missing file path'
                figures.append('<p class="missing">' + labels['missing'] + '</p>')
                errors += 1
                metadata.append(info)
                continue
            try:
                path = within(root, name)
            except ValueError:
                info['error'] = 'Path outside project'
                figures.append('<p class="missing">' + labels['invalid'] + ': ' + esc(name) + '</p>')
                errors += 1
                metadata.append(info)
                continue
            referenced_paths.add(path)
            if out == path or (report_path and report_path == path):
                raise ValueError('A helper output must not replace an asset: ' + name)
            if not path.is_file():
                info['error'] = 'File unavailable'
                figures.append('<p class="missing">' + labels['missing'] + ': ' + esc(name) + '</p>')
                errors += 1
                metadata.append(info)
                continue
            relative = path.relative_to(root).as_posix()
            dims = dimensions(path)
            info.update({'path': relative, 'exists': True, 'bytes': path.stat().st_size,
                         'sha256': file_hash(path), 'dimensions': dims})
            metadata.append(info)
            link = urllib.parse.quote(os.path.relpath(path, out.parent).replace('\\', '/'), safe='/')
            dim_text = f"{dims['width']:g} × {dims['height']:g} {dims['units']}" if dims else labels['unknown']
            if path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
                figures.append(f'<figure><a href="{esc(link)}"><img src="{esc(link)}" alt="{esc(asset_id)}"></a><figcaption><a href="{esc(link)}">{esc(relative)}</a><br>{esc(dim_text)}</figcaption></figure>')
            else:
                figures.append(f'<p>{labels["unsupported"]}: <a href="{esc(link)}">{esc(relative)}</a></p>')
        status = localized_status(delivery.get('status', 'not_started'), args.language)
        visual = localized_status(review.get('visual_inspection', 'not_performed'), args.language)
        coherence = localized_status(review.get('set_consistency', 'not_performed'), args.language)
        source = localized_status(delivery.get('provenance_kind', ''), args.language)
        unresolved = review.get('unresolved') or []
        issue_text = '<ul>' + ''.join('<li>' + esc(i) + '</li>' for i in unresolved) + '</ul>' if unresolved else ''
        cards.append(f'<article><h2>{esc(asset_id)}</h2><p>{esc(message)}</p><p class="meta">{labels["status"]}: {esc(status)} · {labels["source"]}: {esc(source)}<br>{labels["visual"]}: {esc(visual)} · {labels["set"]}: {esc(coherence)}</p>{"".join(figures)}{issue_text}</article>')
    css = '''*{box-sizing:border-box}body{margin:0;padding:32px;color:#153540;background:#fff;font-family:"Malgun Gothic","Yu Gothic",system-ui,sans-serif;line-height:1.65;word-break:keep-all;overflow-wrap:anywhere}header,main{max-width:1300px;margin:auto}h1{font-size:30px;margin:0 0 12px}h2{font-size:17px;margin:0 0 8px}header{border-bottom:1px solid #ccdce3;padding-bottom:20px;margin-bottom:24px}header p{font-size:13px;color:#52666f}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px}article{padding:12px 0;border-top:2px solid #aec5ce}article p,li{font-size:12px}.meta,figcaption{font-size:11px;color:#596c75}figure{margin:14px 0 22px}figure img{display:block;width:100%;height:240px;object-fit:contain;background:repeating-conic-gradient(#fff 0 25%,#f0f3f5 0 50%) 0/16px 16px;cursor:zoom-in}figcaption{margin-top:8px}a{color:#006b96}.missing{color:#9c4c15;padding:15px 0}a:focus-visible{outline:3px solid #b68529}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){body{padding:20px}.grid{grid-template-columns:1fr}}'''
    page = f'<!doctype html><html lang="{args.language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{labels["title"]}</title><style>{css}</style></head><body><header><h1>{labels["title"]}</h1><p>{labels["note"]}</p><p>{labels["fallback"]}</p></header><main class="grid">{"".join(cards)}</main></body></html>'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8')
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({'file_inspection_only': True, 'assets': metadata}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'board': str(out), 'records': len(records), 'files': len(metadata),
                      'unavailable_or_invalid_files': errors, 'visual_review_performed': False}, ensure_ascii=False))
    return 0 if errors == 0 else 2

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--registry', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--metadata-out')
    parser.add_argument('--language', choices=('ko', 'ja'), default='ko')
    args = parser.parse_args()
    try:
        return build(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
