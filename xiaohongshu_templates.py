"""Offline Xiaohongshu library adapter: factual copy and photo-to-paragraph ordering."""
import json
import re
from pathlib import Path
from copy import deepcopy

LIBRARY = json.loads((Path(__file__).parent / 'templates/xiaohongshu_library_v1.json').read_text())
TEMPLATES = {t['id']: t for t in LIBRARY['templates']}
CATEGORY_IDS = {'古镇／历史街区': 'ancient_town', '古镇': 'ancient_town',
                '自然景观': 'nature', '自然风光': 'nature', '主题乐园': 'theme_park'}
STYLE_IDS = {'ancient_town': 'heritage', 'nature': 'natural', 'theme_park': 'experience'}

def template_for(brief):
    return TEMPLATES.get(CATEGORY_IDS.get(brief.get('category')))

def template_drafts(brief, draft):
    """Retain purpose/tone behavior, apply library structure without example-place leakage."""
    t = template_for(brief)
    if not t:
        return draft
    result = deepcopy(draft)
    name = brief['attraction']; highlights = brief['highlights']; lead = highlights[0]['label']
    count = len(highlights)
    subject = {'ancient_town':'细节', 'nature':'风景看点', 'theme_park':'体验看点'}[t['id']]
    if brief['purpose'] == '种草推荐':
        titles = [f'{name}｜从{lead}看这{count}个{subject}', f'{name}｜把目光留给{lead}']
        from promotional_brief import _audience_angle
        angle = _audience_angle(brief)
        for i, v in enumerate(result['versions']):
            v['title'] = titles[i] + (' ✨' if brief['text_style']=='活泼' else '')
            if brief['text_style']=='简洁':
                rows=[f'{h["label"]}：{h["text"]}' for h in highlights]
            elif brief['text_style']=='活泼':
                rows=[('先看' if j==0 else '也可以留意')+h['label']+'：'+h['text'] for j,h in enumerate(highlights)]
            else:
                rows=[('主要看点' if j==0 else '补充看点')+'——'+h['label']+'。'+h['text'] for j,h in enumerate(highlights)]
            lead_in = {'ancient_town':f'想看建筑与文化细节，可以从{name}的{lead}入手。',
                       'nature':f'喜欢观察风景，可以先了解{name}的{lead}。',
                       'theme_park':f'想了解{name}有哪些体验，可以先关注{lead}。'}[t['id']]
            parts = [lead_in, angle] if i==0 else [angle, lead_in]
            context=brief.get('introduction') or next((f['text'] for f in brief['facts'] if f['id']==brief['used_fact_ids'][0]),'')
            if context: parts.append(context)
            parts += rows
            if brief.get('supplement'): parts.append(brief['supplement'])
            parts.append(f'你最想了解{lead}的什么细节？')
            v['caption']='\n\n'.join(parts)
            # Every numbered paragraph uses exactly the selected source, in primary-first order.
            v['used_fact_ids']=brief['used_fact_ids']
        result['suggested_titles']=titles+[f'{name}｜{count}个{subject}分享']
    tags=[name, t['category'], brief['purpose']]+[h['label'] for h in highlights[:2]]
    result['hashtags']=list(dict.fromkeys('#'+re.sub(r'[\s#／]+','',x) for x in tags))[:5]
    result['template_id']=t['id']
    result['template_name']=t['category']+' · '+t['style']
    result['content_outline']=[{'fact_id':h['id'],'subject':h['label'],'text':h['text']} for h in highlights]
    return result

def ordered_photos(brief, photos):
    """Only explicitly matched photos appear; stable order within one highlight; no duplicates."""
    rank={h['id']:i for i,h in enumerate(brief.get('highlights',[]))}
    seen=set(); selected=[]
    for p in photos:
        if p.get('fact_id') not in rank or p['digest'] in seen: continue
        seen.add(p['digest']); selected.append(p)
    return sorted(selected,key=lambda p:rank[p['fact_id']])

def photo_plan(brief, photos):
    ordered=ordered_photos(brief,photos)
    labels={h['id']:h['label'] for h in brief.get('highlights',[])}
    return [{'position':i+1,'fact_id':p['fact_id'],'subject':labels[p['fact_id']],
             'name':p['name'],'digest':p['digest']} for i,p in enumerate(ordered)]
