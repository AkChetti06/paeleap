"""Detailed, deterministic promotional copy. No clients, credentials or network calls.

The input UI hands a serializable brief to this module; menus/layout can reuse it.
User-supplied facts are recorded separately from the existing sourced case data.
"""
import re

CATEGORIES = ['自然景观', '博物馆', '研学基地', '古镇／历史街区', '主题乐园']
CASE_CATEGORIES = {'自然风光': '自然景观', '古镇': '古镇／历史街区', '主题乐园': '主题乐园'}
STYLES = ['简洁', '活泼', '严肃']
PURPOSES = ['种草推荐', '宣传科普', '游玩攻略', '活动宣传']
AUDIENCES = ['一般游客', '亲子家庭', '学生／研学团体', '朋友结伴', '情侣']
STAGES = ['不限定', '小学', '初中', '高中', '大学及以上']
DURATIONS = ['不限定', '约1小时', '半天', '一天']
CATEGORY_GUIDANCE = {
    '自然景观': ('代表景观、观景地点、季节特色', '景物的形态、色彩与空间层次'),
    '博物馆': ('重点展品、展览主题、历史故事', '展品细节、展览主题与相关知识'),
    '研学基地': ('学习主题、动手项目、观察任务', '观察问题、操作过程与学习记录'),
    '古镇／历史街区': ('建筑街巷、文化故事、工艺看点', '建筑、街巷与文化细节'),
    '主题乐园': ('演出、主题场景、游乐项目', '主题表达、演出内容与场景细节'),
}
# Only text already supported by the repository's case sheets. Operational caveats
# remain in brief.boundaries rather than being published as promotional sentences.
CASE_HIGHLIGHTS = {
    '乌镇西栅': [
        ('F02', '水乡风景', '西栅具有江南水乡风貌，可以关注水乡环境与街巷。'),
        ('F03', '蓝印花布', '草木本色染坊的看点包括蓝印花布工艺和晒布场。'),
        ('F04', '老邮局', '乌镇老邮局提供了观察建筑与了解邮政文化的角度。'),
    ],
    '杭州西湖': [
        ('F02', '湖面山景', '西湖南、西、北三面环山，东临城区，湖面与山景共同构成景观。'),
        ('F03', '苏堤', '苏堤是西湖堤岸之一，堤岸将湖面分割为若干水面。'),
        ('F04', '白堤', '白堤也是西湖堤岸之一，可以观察湖面与堤岸的关系。'),
    ],
    '杭州宋城': [
        ('F02', '文化演艺', '杭州宋城是文化演艺主题公园。'),
        ('F03', '宋城千古情', '《宋城千古情》是大型歌舞演出，包含杭州文化、传说及丝绸和茶等主题。'),
        ('F04', '主题街区', '园区主题环境包含街衢、茶楼酒肆等场景，可关注建筑与主题环境的组合。'),
    ],
}


def case_highlights(data):
    sources = {f['id']: f['source'] for f in data['facts']}
    return [dict(id=fid, label=label, text=text, source=sources[fid], provenance='case_sheet')
            for fid, label, text in CASE_HIGHLIGHTS[data['name']]]


def parse_highlights(raw):
    """One explicit label | fact per line; never infer facts from keywords."""
    result = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = re.split(r'[|｜]', line, maxsplit=1)
        if len(parts) != 2 or not all(p.strip() for p in parts):
            raise ValueError('每条亮点请按“名称｜具体说明”填写，一行一条。')
        label, description = (p.strip() for p in parts)
        if len(label) > 30 or len(description) > 500:
            raise ValueError('亮点名称最多30字，说明最多500字。')
        if label in {x['label'] for x in result}:
            raise ValueError('亮点名称不能重复。')
        result.append(dict(id=f'U{len(result) + 1:02}', label=label, text=description,
                           source='用户提供，未独立核验', provenance='user_supplied'))
    if len(result) > 8:
        raise ValueError('第一版最多填写8条候选亮点，再选择其中1至3条。')
    return result


def build_detailed_brief(*, name, category, style, purpose, audience, highlights,
                         selected, primary, data=None, introduction='', supplement='',
                         stage='不限定', duration='不限定', event=None):
    for value, choices, label in [(category, CATEGORIES, '景区类型'), (style, STYLES, '文本风格'),
                                  (purpose, PURPOSES, '推文目的'), (audience, AUDIENCES, '目标人群')]:
        if value not in choices:
            raise ValueError('请选择有效的' + label + '。')
    name, introduction, supplement = name.strip(), introduction.strip(), supplement.strip()
    if not name or len(name) > 80:
        raise ValueError('请填写景点名称（最多80字）。')
    if len(introduction) > 600 or len(supplement) > 600:
        raise ValueError('简介和补充信息分别最多600字。')
    if data and (name != data['name'] or category != CASE_CATEGORIES[data['category']]):
        raise ValueError('景点名称或类型与资料卡不一致，请重新选择。')
    if not data and not introduction:
        raise ValueError('请补充这个场所的简介，程序不会自动查询资料。')
    if not 1 <= len(selected) <= 3 or len(set(selected)) != len(selected):
        raise ValueError('请选择1至3个不同的推广重点。')
    lookup = {h['label']: h for h in highlights}
    if any(label not in lookup for label in selected) or primary not in selected:
        raise ValueError('主重点必须来自本次选择的推广重点。')
    stage = stage if audience == '学生／研学团体' else '不限定'
    duration = duration if purpose == '游玩攻略' else '不限定'
    if stage not in STAGES or duration not in DURATIONS:
        raise ValueError('学习阶段或游玩时长无效。')
    details = {}
    if purpose == '活动宣传':
        event = event or {}
        for key, label in [('name', '活动名称'), ('date', '活动日期／时间'),
                           ('location', '活动地点'), ('participation', '参与方式')]:
            value = str(event.get(key, '')).strip()
            if not value or len(value) > 300:
                raise ValueError('请填写' + label + '（最多300字），再预览活动文案。')
            details[key] = value
    order = [primary] + [x for x in selected if x != primary]
    chosen = [lookup[x] for x in order]
    facts = list(data['facts']) if data else [dict(id='U00', text=introduction,
            source='用户提供，未独立核验', provenance='user_supplied')] + list(highlights)
    extra_ids = []
    if supplement:
        facts.append(dict(id='SUP', text=supplement, source='用户补充，未独立核验', provenance='user_supplied'))
        extra_ids.append('SUP')
    if details:
        for k, value in details.items():
            facts.append(dict(id='EVENT_' + k, text=value, source='用户提供活动信息，未独立核验', provenance='user_supplied'))
            extra_ids.append('EVENT_' + k)
    return dict(
        schema_version='detailed_inputs_v1', attraction=name, category=category,
        text_style=style, purpose=purpose, audience=audience, learning_stage=stage,
        visit_duration=duration, introduction=introduction, supplement=supplement, event=details,
        highlights=chosen, primary_fact_id=chosen[0]['id'], selected_fact_ids=[h['id'] for h in chosen],
        used_fact_ids=([data['facts'][0]['id']] if data else ['U00']) + [h['id'] for h in chosen] + extra_ids,
        facts=facts, boundaries=data['boundaries'] if data else ['用户提供资料尚未独立核验。'],
        reviewed_on=data['reviewed_on'] if data else '用户填写；未独立核验',
        unused_keywords=[], keywords=order, matched_keywords=order,
        version_labels={'A': '重点推荐版', 'B': '读者引导版'},
        version_descriptions={'A': '先突出主重点，再展开支持信息。', 'B': '从读者的关注点切入，保留相同资料与选择。'},
        prompt_version='detailed_inputs_v1',
    )


def _audience_angle(b):
    lead = b['highlights'][0]['label']
    category_focus = CATEGORY_GUIDANCE[b['category']][1]
    learning_task = {
        '不限定': '提出一个观察问题，记录发现，再用自己的话整理',
        '小学': '找出一个看得见的细节，用一句话或一幅画记录',
        '初中': '比较两个观察细节，记录它们的相同点与不同点',
        '高中': '围绕一个问题整理资料依据，并区分观察结果与推测',
        '大学及以上': '结合一个研究问题整理观察记录，说明资料依据与尚待验证的判断',
    }[b['learning_stage']]
    return {
        '一般游客': f'初次了解时，可以先从{lead}入手，看看{category_focus}中哪些最吸引你。',
        '亲子家庭': f'亲子同行时，可以围绕{lead}问孩子：“你注意到了什么细节？”再一起从{category_focus}寻找答案。',
        '学生／研学团体': f"{'' if b['learning_stage'] == '不限定' else b['learning_stage'] + '阶段的'}学习者可以围绕{lead}，从{category_focus}入手，{learning_task}。",
        '朋友结伴': f'和朋友结伴，可以各自选出{lead}中感兴趣的细节，交流对{category_focus}的不同观察。',
        '情侣': f'两个人同行，可以一起观察{lead}，从{category_focus}中挑一个共同感兴趣的话题，按彼此的节奏欣赏。',
    }[b['audience']]


def detailed_drafts(b):
    """Purpose controls structure; audience controls the reader task; tone controls prose."""
    name, purpose, style = b['attraction'], b['purpose'], b['text_style']
    lead = b['highlights'][0]['label']
    angle = _audience_angle(b)
    purpose_leads = {
        '种草推荐': (f'{name}值得关注什么？这次从{lead}开始，挑几个具体看点慢慢了解。',
                 f'想找一个符合自己兴趣的游览主题，可以先看看{name}的{lead}。'),
        '宣传科普': (f'了解{name}，可以从一个问题开始：{lead}有哪些值得观察和认识的内容？',
                 f'怎样从具体细节认识{name}？先围绕{lead}建立观察线索。'),
        '游玩攻略': (f'{name}看点怎么选？先确定主重点{lead}，再按兴趣挑选其他内容。',
                 f'安排{name}的游览时，可以先列出想看的内容，把{lead}放在优先考虑的位置。'),
        '活动宣传': (f"关注{name}的{b['event'].get('name', '')}：本次介绍以{lead}为重点。",
                 f"想了解{b['event'].get('name', '')}怎样参与？先看活动信息，再了解{name}的{lead}。"),
    }
    titles = {
        '种草推荐': [f'{name}：从{lead}发现看点', f'{name}的{lead}，值得怎样看'],
        '宣传科普': [f'{name}小知识：认识{lead}', f'从{lead}读懂{name}的细节'],
        '游玩攻略': [f'{name}看点指南：先关注{lead}', f'围绕{lead}，整理{name}的游览重点'],
        '活动宣传': [f"{b['event'].get('name', '')}｜{name}的{lead}", f"{b['event'].get('name', '')}：关注{lead}"],
    }[purpose]
    facts = {f['id']: f['text'] for f in b['facts']}
    context = b['introduction'] or facts[b['used_fact_ids'][0]]
    versions = []
    for index, vid in enumerate(['A', 'B']):
        title = titles[index]
        intro = purpose_leads[purpose][index]
        if style == '简洁':
            intro = f"{name}｜{'重点' if index == 0 else '关注'}{lead}。"
            bodies = [f"{h['label']}：{h['text']}" for h in b['highlights']]
        elif style == '活泼':
            intro = ('先把目光留给' + lead + '吧！' if index == 0 else '这次，带着好奇心看看' + lead + '！') + intro
            bodies = [(f"先看{h['label']}：" if i == 0 else f"也可以留意{h['label']}：") + h['text']
                      for i, h in enumerate(b['highlights'])]
            title += ' ✨'
        else:
            intro = f'本篇围绕{name}的{lead}展开，重点介绍{CATEGORY_GUIDANCE[b["category"]][1]}。' if index == 0 else f'以{lead}为切入点，可进一步了解{name}的相关内容。'
            bodies = [f"{'主要看点' if i == 0 else '补充看点'}——{h['label']}。{h['text']}"
                      for i, h in enumerate(b['highlights'])]
            angle = angle.replace('你', '读者').replace('可以', '可')
        body = '\n'.join(bodies) if style == '简洁' else '\n\n'.join(bodies)
        if purpose == '种草推荐':
            parts = [intro, context, body, angle] if index == 0 else [angle, intro, context, body]
            ending = {'简洁': '选择感兴趣的看点，出发前核对现场安排。',
                      '活泼': f'你会先关注{lead}的哪一处细节？先选好自己的兴趣，再看看官方的现场安排吧。',
                      '严肃': '可根据个人兴趣选择参观重点，具体开放与服务安排请以官方信息为准。'}[style]
        elif purpose == '宣传科普':
            question = f'观察问题：{lead}有哪些具体特点？可以结合现场介绍，对照下面的资料了解。'
            parts = [intro, context, question, body, angle] if index == 0 else [angle, question, context, body, intro]
            ending = {'简洁': '结合现场说明，记录一个新的发现。', '活泼': '看完以后，试着用自己的话讲讲新发现吧！',
                      '严肃': '建议结合现场说明理解相关内容，并区分资料信息与个人推测。'}[style]
        elif purpose == '游玩攻略':
            timing = ('先按个人兴趣选择看点。' if b['visit_duration'] == '不限定' else
                      f"如果计划停留{b['visit_duration']}，建议先优先了解{lead}，再根据现场情况取舍其他看点；这不是实测行程。")
            parts = [intro, context, '选看点：\n' + body, '安排重点：' + timing, angle]
            if index:
                parts = [angle, timing, context, body]
            ending = '出发前核对开放安排、预约要求和交通信息；这里未提供经过核实的路线或步行耗时。'
        else:
            e = b['event']
            event_block = f"活动：{e['name']}\n时间：{e['date']}\n地点：{e['location']}\n参与方式：{e['participation']}"
            parts = [intro, event_block, context, body, angle] if index == 0 else [event_block, angle, intro, context, body]
            ending = '参与前请确认主办方的最新活动安排。'
        if b['supplement']:
            parts.append('补充信息：' + b['supplement'])
        parts.append(ending)
        versions.append(dict(id=vid, title=title, caption='\n\n'.join(parts), used_fact_ids=b['used_fact_ids']))
    # Stable, valid tags; no implied facilities, season, admission or personal visit.
    clean_name = re.sub(r'[\s#]+', '', name)
    tags = list(dict.fromkeys(['#' + clean_name, '#' + b['category'].replace('／', ''), '#' + purpose, '#出游灵感']))
    return dict(suggested_titles=[v['title'] for v in versions] + [f'{name}｜把目光留给{lead}'],
                versions=versions, hashtags=tags, copy_source='local_template_not_llm')
