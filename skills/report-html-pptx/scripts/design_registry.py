"""Purpose profiles and canvas defaults from the existing design token authority."""
import json
from pathlib import Path
from company_pack import load_company_pack, resolve_design_tokens

TOKENS_PATH=Path(__file__).resolve().parents[1]/'system/design-tokens.json'
TOKENS=json.loads(TOKENS_PATH.read_text(encoding='utf-8'))
CANVASES={key:tuple(row['css_px']) for key,row in TOKENS['canvases'].items()}


def tokens_for(company_pack=None, document_family='executive_report'):
    """Preserve legacy DEMO defaults unless the caller explicitly picks a pack."""
    pack=load_company_pack(company_pack) if company_pack is not None else None
    if pack is not None and pack.metadata['status'] != 'approved':
        raise ValueError('Company Pack must be approved for production')
    return resolve_design_tokens(TOKENS,pack,document_family)

def font_for(language,tokens=None):
    font=(tokens or TOKENS)['font'];key=str(language or '').lower().split('-')[0]
    return font.get('by_language',{}).get(key,font)


def select_profile(genre,use,selected=None,tokens=None):
    profile=selected or ('office_print' if use=='office_print' else 'live_deck' if use=='live' else
        {'plan':'execution','submission':'executive_approval','proposal':'proposal',
         'presentation':'reading_deck'}.get(genre,'reading_report'))
    if profile not in (tokens or TOKENS)['profiles']:raise ValueError('Unknown design profile')
    if (profile=='live_deck')!=(use=='live'):raise ValueError('Live density and confirmed use disagree')
    if use=='office_print' and profile!='office_print':raise ValueError('Office print requires office_print profile')
    return profile
