"""Paeleap C1 Week 2: tourism micro-prototype. No publishing or unverified travel claims."""
import json, os, re, time
from pathlib import Path
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse
import requests
from PIL import Image, ImageDraw, ImageFont

STYLES = {
 'Scenic & Cinematic': 'wide landscape framing, natural soft light, balanced composition, restrained atmospheric mist, serene realistic colors',
 'Traditional & Heritage': 'architectural detail, historically respectful documentary framing, accurate forms, natural heritage colors',
 'Modern & Neon': 'night light, architectural geometry, reflections, crisp high-contrast contemporary photography',
 'Vibrant & Playful': 'energetic composition, vivid color accents, playful but plausible visual storytelling',
 'Warm & Authentic': 'natural candid photography, warm ambient light, human scale, restrained everyday realism',
 'Minimalist & Luxury': 'calm negative space, refined composition, soft light and uncluttered restrained tones',
}
ATTRACTIONS = {
 '杭州西湖': dict(category='风景区', style='Scenic & Cinematic', features='湖面、岸边树木、远山与柔和自然光', name_en='West Lake, Hangzhou', concept='沿湖观景与悠闲步行', refs='Top 2 / Top 3 / Top 4'),
 '杭州良渚古城遗址公园': dict(category='风景区',style='Scenic & Cinematic',features='遗址公园的草地、水域和开阔自然空间',name_en='Liangzhu Archaeological Ruins Park',concept='以清晰顺序组织园区参观',refs='Top 3'),
 '杭州西溪湿地': dict(category='风景区',style='Scenic & Cinematic',features='湿地水道、林木与自然景观',name_en='Xixi Wetland',concept='轻松的一日游路线构思',refs='Top 2 / Top 6'),
 '浙江省博物馆': dict(category='文博场所',style='Traditional & Heritage',features='真实博物馆空间、展品陈列与建筑细节；不要虚构具体文物',name_en='Zhejiang Provincial Museum',concept='围绕一个展览主题介绍看点',refs='Top 10 / Top 11'),
 '杭州宋城': dict(category='研学场所',style='Vibrant & Playful',features='传统主题建筑、游客互动、文化体验空间；不要杜撰真实活动',name_en='Songcheng, Hangzhou',concept='以任务、互动和可见成果设计研学介绍',refs='Top 18'),
}
TASKS = {
 '风景区':'首图给出值得去的理由；正文按可跟随顺序列出建议体验；提醒路线/交通/时令需核实。参考 Top 2/3/4。',
 '文博场所':'围绕看什么和为什么，建议重点对象清单、逐件短解释及楼层/服务核实提示。参考 Top 8/11/13。',
 '研学场所':'先描述参与任务，再说明工具和步骤，最后说明可记录的成果；不声称活动实际存在。参考 Top 16/17/19。',
}

def plan(attraction, category=None, style=None, audience='首次到访游客', visit_reason=''):
    attraction=attraction.strip()
    audience=audience.strip()[:100]
    visit_reason=visit_reason.strip()[:180]
    if not attraction or len(attraction)>100: raise ValueError('请输入1–100字的景点名称')
    found=ATTRACTIONS.get(attraction, {})
    category=category or found.get('category','风景区')
    style=style or found.get('style','Scenic & Cinematic')
    if category not in TASKS or style not in STYLES: raise ValueError('无效的类型或视觉风格')
    features=found.get('features','以用户提供或经核实的景点外观资料为准，不自行添加建筑或活动')
    concept=visit_reason.strip() or found.get('concept','值得了解的参观体验')
    image_prompt=(f'Editorial tourism concept image of {found.get("name_en",attraction)} ({attraction}). '
        f'Visible subject: {features}. Visual art direction: {STYLES[style]}. '
        'Vertical 3:4 travel magazine cover composition. One believable scene, no collage, no captions, no letters, no watermark. '
        'Preserve recognizable geography and cultural character; do not invent landmarks, artifacts, events, visitors or signage. '
        'This is an illustrative AI visual, not evidence of actual site conditions.')
    return dict(attraction=attraction,category=category,style=style,audience=audience,reason=concept,
                features=features,information_task=TASKS[category],image_prompt=image_prompt,
                reference_tags=found.get('refs','Top 2/3/4 (scenic), 8/11/13 (museum), 16/17/19 (study)'),
                evidence_status='未提供已核验现场素材；AI图片仅用于概念展示')

def fallback_copy(p):
    place=p['attraction']
    variants={
      '风景区':(f'{place}｜第一次来可以这样规划🌿',f'想去{place}，先想好最期待看到什么。\n\n① 从入口及主要观景点开始了解场地。\n② 按实际步道和官方导览安排游览顺序，留出慢慢拍照的时间。\n③ 出发前确认开放信息、交通、天气和季节变化。\n\n这是一份行程灵感，不是已核验的实时攻略。'),
      '文博场所':(f'{place}｜从重点展品开始逛🏛️',f'第一次参观{place}，不妨先找到自己感兴趣的展览主题。\n\n① 查看馆方当天公布的展览与重点藏品。\n② 给每件重点展品留一点时间，看看背后的故事。\n③ 结合馆内指引安排楼层与参观顺序。\n\n开放时间、展品与讲解安排请以馆方公告为准。'),
      '研学场所':(f'{place}｜把参观变成探索任务📒',f'去{place}时，可以尝试用小任务让观察更有目的。\n\n① 出发前先设一个观察问题。\n② 参观时记录看到的材料、步骤或文化线索。\n③ 回来后整理一张观察卡，分享自己的收获。\n\n以上为建议的自助学习方式，不代表景区实际提供这些活动。')}
    title,caption=variants[p['category']]
    if p.get('reason') and p['reason'] != ATTRACTIONS.get(place,{}).get('concept','值得了解的参观体验'):
        caption = f"本篇主题：{p['reason']}。\n\n" + caption
    if p.get('audience') and p['audience'] not in ('首次到访游客','First-time visitors'):
        caption = f"写给{p['audience']}的旅行灵感。\n\n" + caption
    return {'title':title,'caption':caption,'hashtags':['#旅游灵感','#旅行攻略','#'+re.sub(r'\s+','',place),'#周末去哪儿'], 'copy_source':'local_template_not_llm'}

def generate_copy(p, api_key='',base_url='',model='qwen-plus'):
    if not api_key or not base_url: return fallback_copy(p)
    from openai import OpenAI
    client=OpenAI(api_key=api_key,base_url=base_url,timeout=45,max_retries=1)
    system=('你是中国旅游内容编辑。输出严格JSON对象，键为title（简短自然中文标题）、caption（80–180字的中文正文）和hashtags（4个字符串数组）。'
            '保持自然朴素的小红书语气，不假装亲身去过，不使用虚假评价、票价、时间、交通路线、活动、展品等事实。'
            '先给出值得看的理由，再说明参观步骤，最后注明需要核实的信息。不要把AI生成图片当作现场照片。')
    response=client.chat.completions.create(model=model,messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(p,ensure_ascii=False)}],temperature=0.6)
    raw=response.choices[0].message.content or ''
    try:
        data=json.loads(re.search(r'\{.*\}',raw,re.S).group())
        if not isinstance(data.get('title'),str) or not isinstance(data.get('caption'),str) or not isinstance(data.get('hashtags'),list): raise ValueError('missing fields')
        data['hashtags']=[str(t) for t in data['hashtags'][:6]]
        data['copy_source']='llm_generated_requires_review'
        return data
    except Exception as exc: raise RuntimeError('文字模型没有返回有效JSON，请重试或使用离线文案') from exc

def placeholder(p):
    img=Image.new('RGB',(900,1200),'#efece5');draw=ImageDraw.Draw(img)
    draw.rounded_rectangle((60,65,840,1135),radius=24,outline='#b4a999',width=4)
    fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font=ImageFont.truetype(fontpath,43) if os.path.exists(fontpath) else ImageFont.load_default()
    small=ImageFont.truetype(fontpath,24) if os.path.exists(fontpath) else ImageFont.load_default()
    draw.text((100,170),'DEMO / NO AI IMAGE',font=font,fill='#594b40')
    draw.text((100,270),'Illustrative placeholder only',font=small,fill='#594b40')
    draw.text((100,315),'Not a photograph of the location',font=small,fill='#594b40')
    draw.text((100,955),p['style'],font=small,fill='#594b40')
    draw.text((100,1010),'Connect an image provider to generate',font=small,fill='#594b40')
    return img

def generate_wan_image(p, key, base_url, model='wan2.6-t2i'):
    if not key or not base_url: raise ValueError('请设置DASHSCOPE_API_KEY及DASHSCOPE_BASE_URL。')
    import dashscope
    from dashscope.aigc.image_generation import ImageGeneration
    from dashscope.api_entities.dashscope_response import Message
    dashscope.base_http_api_url=base_url.rstrip('/')
    rsp=ImageGeneration.call(model=model, api_key=key, messages=[Message(role='user',content=[{'text':p['image_prompt']}])], n=1,size='960*1280',prompt_extend=True,watermark=False)
    if rsp.status_code != 200:
        raise RuntimeError(f'Wan API调用失败 ({rsp.status_code}): {rsp.code}: {rsp.message}')
    try:
        url=rsp.output.choices[0].message.content[0]['image']
    except Exception as exc:raise RuntimeError('Wan返回格式与预期不同，请检查模型和SDK版本') from exc
    if urlparse(url).scheme!='https':raise RuntimeError('Unexpected non-HTTPS image URL')
    result=requests.get(url,timeout=60);result.raise_for_status()
    if len(result.content)>20_000_000:raise RuntimeError('Image too large')
    image=Image.open(BytesIO(result.content));image.load()
    return image.convert('RGB')

def save_output(root,p,copy,image,backend,elapsed):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    serial=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    folder=root/serial;folder.mkdir()
    image.save(folder/'visual.png')
    manifest=dict(plan=p,post=copy,backend=backend,elapsed_seconds=round(elapsed,2),image_is_illustrative=(backend!='placeholder'),
                  review_required=True,generated_at=serial)
    (folder/'post.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    (folder/'post.txt').write_text(copy['title']+'\n\n'+copy['caption']+'\n\n'+' '.join(copy['hashtags'])+'\n',encoding='utf8')
    return folder

def generate_hf_image(p, token, model='black-forest-labs/FLUX.1-schnell'):
    """Generate through Hugging Face Inference Providers (limited monthly free credits)."""
    if not token:
        raise ValueError('Hugging Face token missing / 缺少 Hugging Face Token (HF_TOKEN).')
    from huggingface_hub import InferenceClient
    client = InferenceClient(api_key=token, timeout=110)
    try:
        image = client.text_to_image(prompt=p['image_prompt'], model=model)
        return image.convert('RGB')
    except Exception as exc:
        raise RuntimeError(f'Hugging Face image request failed. Check model availability, token permissions and remaining credits. / 请检查模型、权限及免费额度。 Details: {exc}') from exc


def english_copy(p):
    name=ATTRACTIONS.get(p['attraction'],{}).get('name_en',p['attraction'])
    messages={
        '风景区':(f'{name} | A simple first-visit idea 🌿',f'Planning a visit to {name}? Here is a starting point for your day.\n\n① Decide what scenery or experience interests you most.\n② Plan a sensible walking order using the official visitor map.\n③ Check current access details, weather and transport before leaving.\n\nThis is travel inspiration, not a verified first-hand guide.'),
        '文博场所':(f'{name} | Explore the highlights 🏛️',f'Curious about {name}? Build your visit around a theme you want to understand.\n\n① Check the museum’s current exhibitions and featured objects.\n② Pause at a few highlights and read their interpretation.\n③ Use on-site directions to plan your route.\n\nConfirm exhibition details and opening arrangements with the venue.'),
        '研学场所':(f'{name} | Turn a visit into discovery 📒',f'Bring a simple learning goal to {name}.\n\n① Choose one thing to observe before arriving.\n② Record interesting details and steps during your visit.\n③ Make a small observation card afterwards.\n\nThese are suggested self-guided tasks, not claims about actual scheduled activities.'),
    }
    title,caption=messages[p['category']]
    if p.get('reason') and p['reason'] != ATTRACTIONS.get(p['attraction'],{}).get('concept','值得了解的参观体验'):
        caption = f"Creative angle: {p['reason']}.\n\n" + caption
    if p.get('audience') and p['audience'] not in ('首次到访游客','First-time visitors'):
        caption = f"For: {p['audience']}.\n\n" + caption
    return {'title':title,'caption':caption,'hashtags':['#ChinaTravel','#TravelInspiration','#ExploreChina','#WeekendIdeas'],'copy_source':'local_template_not_llm'}


def localized_copy(p, lang='中文', api_key='', base_url='', model='qwen-plus', use_llm=False):
    if use_llm and (not api_key or not base_url):
        raise ValueError('LLM caption mode needs TEXT_API_KEY and TEXT_BASE_URL in .env / 请配置文字模型 API 参数。')
    if not use_llm:
        return fallback_copy(p) if lang=='中文' else english_copy(p)
    if lang=='中文':
        return generate_copy(p,api_key,base_url,model)
    from openai import OpenAI
    client=OpenAI(api_key=api_key,base_url=base_url,timeout=45,max_retries=1)
    system=('Write engaging, natural English tourism social content. Return ONLY JSON keys title, caption, hashtags (array of four strings). '
            'No fake first-hand claims, made-up schedules, route specifics, fees, artifacts or promotional promises. '
            'Structure: reason to visit, useful viewing order, what must be verified. Say that AI visuals are illustrative.')
    response=client.chat.completions.create(model=model,messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(p,ensure_ascii=False)}],temperature=0.6)
    raw=response.choices[0].message.content or ''
    try:
        obj=json.loads(re.search(r'\{.*\}',raw,re.S).group())
        assert isinstance(obj.get('title'),str) and isinstance(obj.get('caption'),str) and isinstance(obj.get('hashtags'),list)
        obj['hashtags']=[str(x) for x in obj['hashtags'][:6]]
        obj['copy_source']='llm_generated_requires_review'
        return obj
    except Exception as exc:raise RuntimeError('Text API returned invalid JSON / 文案API返回无效JSON') from exc


class ImageProviderError(RuntimeError):
    """Image API error with a category for safe, actionable UI messages."""
    def __init__(self, provider, category, detail):
        self.provider, self.category = provider, category
        super().__init__(f"{provider}: {category} — {detail}")


def provider_status(environ=None):
    """Configuration only. Does not imply valid tokens, credits, or model availability."""
    env = os.environ if environ is None else environ
    return {
        'cloudflare': bool(env.get('CLOUDFLARE_ACCOUNT_ID') and env.get('CLOUDFLARE_API_TOKEN')),
        'huggingface': bool(env.get('HF_TOKEN')),
        'alibaba_wan': bool(env.get('DASHSCOPE_API_KEY') and env.get('DASHSCOPE_BASE_URL')),
    }


def generate_cloudflare_image(p, account_id, token, model='@cf/black-forest-labs/flux-1-schnell'):
    """Call Workers AI REST API; handles JSON base64 output and errors without exposing tokens."""
    import base64
    from PIL import UnidentifiedImageError
    if not account_id or not token:
        raise ImageProviderError('Cloudflare', 'configuration', 'Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN in .env / 请配置账户 ID 和令牌。')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}', account_id):
        raise ImageProviderError('Cloudflare', 'configuration', 'Account ID format looks incorrect.')
    # Fixed model allowlist prevents arbitrary URL paths from entering the request.
    allowed = {'@cf/black-forest-labs/flux-1-schnell'}
    if model not in allowed:
        raise ImageProviderError('Cloudflare', 'configuration', 'Unsupported image model. Use @cf/black-forest-labs/flux-1-schnell.')
    url=f'https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}'
    try:
        response=requests.post(url,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},
            json={'prompt':p['image_prompt'][:2048],'steps':4},timeout=110)
    except requests.RequestException as exc:
        raise ImageProviderError('Cloudflare','network','Connection timed out or could not reach Cloudflare. Retry later.') from exc
    if response.status_code in (401,403):
        raise ImageProviderError('Cloudflare','authentication',f'HTTP {response.status_code}. Check Workers AI token permissions and account ID.')
    if response.status_code==402:
        raise ImageProviderError('Cloudflare','credits','HTTP 402. Account billing or quota restriction.')
    if response.status_code==429:
        raise ImageProviderError('Cloudflare','rate_limit','HTTP 429. Quota or rate limit reached; check dashboard and retry later.')
    if response.status_code>=400:
        raise ImageProviderError('Cloudflare','api_error',f'HTTP {response.status_code}. Verify Workers AI availability in the Cloudflare dashboard.')
    try:
        body=response.json()
        if body.get('success') is False:
            errors=body.get('errors') or []
            # Keep output concise and safe; never echo the request, token, or arbitrary server diagnostics.
            code=errors[0].get('code') if errors and isinstance(errors[0],dict) else 'unknown'
            raise ImageProviderError('Cloudflare','api_error',f'Cloudflare returned a failed response (code {code}).')
        result=body.get('result',body)
        if not isinstance(result,dict) or not isinstance(result.get('image'),str):
            raise ValueError('missing image')
        decoded=base64.b64decode(result['image'],validate=True)
        if len(decoded)>20_000_000:
            raise ValueError('image too large')
        img=Image.open(BytesIO(decoded));img.load()
        return img.convert('RGB')
    except ImageProviderError:raise
    except (ValueError,KeyError,TypeError,UnidentifiedImageError) as exc:
        raise ImageProviderError('Cloudflare','invalid_response','Could not decode the image returned by Cloudflare.') from exc


def generate_with_fallback(p, preferred, fallback, config, generators=None):
    """Only tries a secondary provider when explicitly configured and opted into by the user."""
    generators=generators or {
      'cloudflare': lambda:generate_cloudflare_image(p,config.get('CLOUDFLARE_ACCOUNT_ID',''),config.get('CLOUDFLARE_API_TOKEN','')),
      'huggingface': lambda:generate_hf_image(p,config.get('HF_TOKEN',''),config.get('HF_IMAGE_MODEL','black-forest-labs/FLUX.1-schnell')),
      'alibaba_wan': lambda:generate_wan_image(p,config.get('DASHSCOPE_API_KEY',''),config.get('DASHSCOPE_BASE_URL',''),config.get('IMAGE_MODEL','wan2.6-t2i')),
      'placeholder': lambda:placeholder(p),
    }
    if preferred not in generators:raise ValueError('Unknown image provider')
    try:
        return generators[preferred](),preferred,None
    except Exception as exc:
        # Prevent silently changing provider / incurring a bill.
        if not fallback or fallback==preferred or fallback not in generators or fallback=='placeholder':raise
        if not provider_status(config).get(fallback):raise
        try:
            return generators[fallback](),fallback,f'{preferred} failed ({type(exc).__name__}); used {fallback}'
        except Exception as fallback_exc:
            raise RuntimeError(f'Both image providers failed. First: {str(exc)[:220]}. Fallback: {str(fallback_exc)[:220]}') from fallback_exc
