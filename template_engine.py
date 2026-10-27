"""Source-backed Week 2 briefs. Offline preview is explicitly not an LLM run."""
import json
import re
from pathlib import Path
from engine import CaptionError, safe_error

def generate_with_fallback(*args, **kwargs):
    # The team engine may omit the legacy image dispatcher. Keep offline text
    # independent of it; image callers must provide a configured generator.
    import engine
    generate = getattr(engine, 'generate_with_fallback', None)
    if generate is None:
        raise ValueError('当前原型尚未接通图片生成。')
    return generate(*args, **kwargs)


ROOT = Path(__file__).resolve().parent
TEMPLATES = {
    '古镇': {'style': 'Traditional Editorial', 'palette': '柔和自然色、蓝印花布局部色彩', 'structure': '到访理由 → 主要亮点 → 文化细节 → 自然收尾'},
    '自然风光': {'style': 'Cinematic Landscape', 'palette': '自然绿与水色、柔和光线', 'structure': '观景兴趣 → 主要景观 → 观察建议 → 自然收尾'},
    '主题乐园': {'style': 'Vibrant & Playful', 'palette': '明快色彩、统一重点色', 'structure': '体验兴趣 → 已确认项目 → 适合人群 → 自然收尾'},
}

def list_attractions():
    return [json.loads((ROOT / 'data' / filename).read_text(encoding='utf-8'))
            for filename in ('wuzhen_xizha.json', 'west_lake.json', 'songcheng.json')]


def load_attraction(name):
    normalized = re.sub(r'\s+', '', name).casefold()
    for data in list_attractions():
        if normalized in {re.sub(r'\s+', '', x).casefold() for x in data['aliases']}:
            return data
    raise ValueError('此景点还没有资料卡。当前可演示：乌镇西栅、杭州西湖、杭州宋城。')


def build_brief(name, keywords):
    data = load_attraction(name)
    if len(keywords) > 180:
        raise ValueError('关键词请控制在180字以内。')
    tokens = list(dict.fromkeys(t.strip() for t in re.split(r'[,，、;；\n\s]+', keywords) if t.strip()))
    scores = {f['id']: 0 for f in data['facts']}
    matched, unused = [], []
    for token in tokens:
        hits = [f['id'] for f in data['facts'] if token in f['keywords']]
        if hits:
            matched.append(token)
            for fid in hits:
                scores[fid] += 1
        else:
            unused.append(token)
    # Concrete place highlights outrank general setting, then keywords choose between them.
    primary = max(data['highlight_ids'], key=lambda fid: scores[fid])
    secondary = next(fid for fid in data['highlight_ids'] if fid != primary)
    selected = [primary, data['context_id'], secondary]
    facts = {f['id']: f for f in data['facts']}
    template = TEMPLATES[data['category']]
    return {
        'attraction': data['name'], 'category': data['category'], **template,
        'keywords': tokens, 'matched_keywords': matched, 'unused_keywords': unused,
        'primary_fact_id': primary, 'selected_fact_ids': selected,
        'facts': data['facts'], 'boundaries': data['boundaries'], 'reviewed_on': data['reviewed_on'],
        'reading_order': [template['structure'].split(' → ')[0], facts[primary]['text'], facts[secondary]['text'], '适合谁'],
        'version_labels': data['version_labels'], 'version_descriptions': data['version_descriptions'],
        'prompt_version': {'古镇':'ancient_town_v2','自然风光':'natural_scenery_v1','主题乐园':'theme_park_v1'}[data['category']],
        'image_prompt': ('Illustrative tourism concept for ' + data['name'] + '. ' + ' '.join(facts[k]['text'] for k in selected)
                         + '。视觉：' + template['palette'] + '。单一场景，不拼接景点，不虚构地标、文字或活动。'
                         '真实外观需参考图核实；不能当作现场照片。'),
    }


def offline_drafts(brief):
    if brief['category'] != '古镇':
        return scenario_drafts(brief)
    chunks = {
        'F03': '草木本色染坊可以作为一个重点。先看看晒布场，再留意蓝印花布的纹样。喜欢拍照的话，不妨分别观察整体画面与局部图案，寻找自己感兴趣的细节。',
        'F04': '乌镇老邮局提供了建筑与邮政文化的观察角度。如果你对这类文化场所感兴趣，可以把目光从水乡环境转向建筑本身，选择想进一步了解的内容。',
    }
    primary = brief['primary_fact_id']
    secondary = 'F04' if primary == 'F03' else 'F03'
    lead = '蓝印花布' if primary == 'F03' else '老邮局'
    a = ('想慢慢逛一座江南古镇，可以先了解乌镇西栅。把水乡街巷作为这次游览的背景，再选几个真正感兴趣的看点，给观察细节留一点时间。\n\n'
         + chunks[primary] + '\n\n' + chunks[secondary]
         + '\n\n如果你喜欢慢游，可以围绕自己的兴趣安排这次游览。无需把每处看点都变成必须完成的任务，到了现场，再决定在哪里多停一会儿。')
    cultural = {
        'F03': '草木本色染坊的看点在于蓝印花布工艺与晒布场。可以从纹样、布匹和整体呈现三个层次观察，给这次古镇游增加一个工艺主题。',
        'F04': '老邮局则把注意力引向建筑与邮政文化。对这类场所感兴趣的人，可以把它作为认识西栅的另一个切入口。',
    }
    b = ('认识乌镇西栅，也可以从具体的文化场所入手。这次以' + lead + '为重点，再搭配另一个看点，从不同角度了解水乡环境之外的内容。\n\n'
         + cultural[primary] + '\n\n' + cultural[secondary]
         + '\n\n喜欢工艺，就多留意染坊的布匹和纹样；对建筑与邮政文化感兴趣，可以关注老邮局。先确定想了解什么，再选择自己的游览重点。')
    return {
        'suggested_titles': [f'乌镇西栅慢游，留意{lead}的细节', '蓝印花布与老邮局：认识西栅的两个角度', '从水乡街巷开始，慢慢了解西栅'],
        'versions': [{'id': 'A', 'title': f'乌镇西栅慢游，留意{lead}的细节', 'caption': a, 'used_fact_ids': brief['selected_fact_ids']},
                     {'id': 'B', 'title': f'从{lead}开始，认识西栅的文化看点', 'caption': b, 'used_fact_ids': brief['selected_fact_ids']}],
        'hashtags': ['#乌镇西栅', '#江南水乡', '#古镇慢游', '#蓝印花布'],
        'copy_source': 'local_template_not_llm',
    }


def scenario_drafts(brief):
    data = load_attraction(brief['attraction'])
    pack = data['offline']
    facts = {f['id']: f for f in data['facts']}
    primary = brief['primary_fact_id']
    secondary = next(fid for fid in data['highlight_ids'] if fid != primary)
    lead = facts[primary]['title_word']
    titles = [t.format(lead=lead) for t in pack['titles']]
    versions = []
    for vid, suffix, title in [('A', 'a', titles[0]), ('B', 'b', pack['version_b_title'].format(lead=lead))]:
        caption = '\n\n'.join([pack['intro_' + suffix].format(lead=lead), facts[primary]['copy_' + suffix],
                                  facts[secondary]['copy_' + suffix], pack['outro_' + suffix]])
        versions.append({'id':vid, 'title':title, 'caption':caption, 'used_fact_ids':brief['selected_fact_ids']})
    return {'suggested_titles':titles, 'versions':versions, 'hashtags':pack['hashtags'], 'copy_source':'local_template_not_llm'}


def parse_drafts(raw, brief):
    try:
        data = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip()))
        titles, versions, tags = data['suggested_titles'], data['versions'], data['hashtags']
        assert isinstance(titles, list) and len(titles) == 3 and all(isinstance(t, str) and t.strip() for t in titles)
        assert isinstance(versions, list) and len(versions) == 2
        assert [v['id'] for v in versions] == ['A', 'B']
        known = {f['id'] for f in brief['facts']}
        for v in versions:
            assert all(isinstance(v[k], str) and v[k].strip() for k in ('title', 'caption'))
            assert isinstance(v['used_fact_ids'], list) and v['used_fact_ids']
            assert all(isinstance(fid, str) and fid in known for fid in v['used_fact_ids'])
        assert versions[0]['caption'].strip() != versions[1]['caption'].strip()
        assert isinstance(tags, list) and 3 <= len(tags) <= 5
        assert all(isinstance(t, str) and re.fullmatch(r'#[^\s#]+', t) for t in tags)
        assert len(set(tags)) == len(tags)
        return {'suggested_titles': titles, 'versions': [{k: v[k] for k in ('id', 'title', 'caption', 'used_fact_ids')} for v in versions],
                'hashtags': tags, 'copy_source': 'llm_generated_requires_review'}
    except (ValueError, KeyError, TypeError, AssertionError, AttributeError) as exc:
        raise CaptionError('文案格式无效：需要两版不同正文及有效资料编号；未替换为离线模板。') from exc


def generate_drafts(brief, mode='offline', config=None):
    if brief.get('schema_version') == 'detailed_inputs_v1':
        if mode != 'offline':
            raise ValueError('详细输入原型仅支持离线预览。')
        from promotional_brief import detailed_drafts
        return detailed_drafts(brief)
    if mode == 'offline':
        return offline_drafts(brief)
    if mode != 'llm':
        raise ValueError('未知文案方式')
    config = config or {}
    if not config.get('TEXT_API_KEY') or not config.get('TEXT_BASE_URL'):
        raise CaptionError('文字接口尚未配置；请设置 TEXT_API_KEY 和 TEXT_BASE_URL。')
    from openai import OpenAI
    try:
        client = OpenAI(api_key=config['TEXT_API_KEY'], base_url=config['TEXT_BASE_URL'], timeout=45, max_retries=0)
        response = client.chat.completions.create(
            model=config.get('TEXT_MODEL') or 'qwen-plus', temperature=0.65,
            messages=[{'role':'system','content':(ROOT / 'prompts' / (brief['prompt_version'] + '.txt')).read_text(encoding='utf-8')},
                      {'role':'user','content':json.dumps(brief, ensure_ascii=False)}])
        raw = response.choices[0].message.content or ''
    except Exception as exc:
        raise CaptionError('文字生成失败，请检查接口、账号及额度；未替换为离线模板。') from exc
    return parse_drafts(raw, brief)


def attach_image(result, provider, config, image_generator=None):
    """Image is a separate state: failure never destroys successful or edited copy."""
    result = dict(result)
    result.update(image=None, image_backend=None, image_error=None)
    try:
        generate = image_generator or generate_with_fallback
        image, backend, _ = generate(result['brief'], provider, None, config)
        result.update(image=image, image_backend=backend)
    except Exception as exc:
        result['image_error'] = safe_error(exc)
    return result


def export_result(result, edited_versions):
    return {'brief': result['brief'], 'post': {**result['copy'], 'versions': edited_versions},
            'source_copy': result['copy'], 'image_backend': result.get('image_backend'),
            'image_status': 'failed' if result.get('image_error') else 'ready' if result.get('image') is not None else 'not_requested',
            'review_required': True, 'prompt_version': result['brief']['prompt_version'],
            'generated_at': result['generated_at']}
