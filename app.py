"""Paeleap C1 bilingual Week 2 tourism promotional post lab."""
import json
import os
import time
from html import escape
from io import BytesIO
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from engine import (ATTRACTIONS, STYLES, TASKS, plan, localized_copy,
                    placeholder, generate_wan_image, generate_hf_image, generate_with_fallback, provider_status, save_output, recommend_style, safe_error)

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env', override=False)
st.set_page_config(page_title='PAELEAP | Creator Studio',page_icon='✦',layout='wide',initial_sidebar_state='collapsed')

COPY={
 'English':{
  'eyebrow':'PAELEAP  /  C1 RESEARCH LAB  /  WEEK 02','headline':'Places worth sharing.','subhead':'Turn a destination into a compelling travel story — from concept and visuals to a ready-to-review social post.',
  'workspace':'Your creative brief','workspace_sub':'Set the direction. We’ll shape the story.','preview':'Your post preview','preview_sub':'Your next travel story starts here.','destination':'Destination','destination_help':'Choose a researched location or enter your own.','custom':'Custom destination','name':'Attraction name','scene':'Content category','style':'Visual direction','recommend':'Suggested for this attraction','style_custom':'You can choose any other style.','audience':'Audience','audience_default':'First-time visitors','angle':'Story angle (optional)','angle_placeholder':'e.g. a peaceful lakeside afternoon','picture':'Image engine','copy_mode':'Caption engine','generate':'✦  Create my travel post','generate_busy':'Creating your story…','no_result':'A little inspiration, ready to become a story.','no_result_sub':'Complete the brief on the left and hit Create. Your generated visual and copy will appear here.','tag1':'DISCOVER','tag2':'CREATE','tag3':'REFINE',
  'demo':'Free preview · no AI image','hf':'Hugging Face · limited credits','cloudflare':'Cloudflare Workers AI · daily free allowance','wan':'Alibaba Wan · billed API','rule':'Instant template · free','llm':'LLM API · configured key','api_note':'Cloudflare has a daily free allocation; Hugging Face credits can run out. API use requires your own credentials.','notice':'Research-based concept only. Generated images are illustrative, not on-location photographs; review claims before publishing.','expand':'Why these content choices? · Week 1 evidence','evidence':'**Your 20 reference posts**: 7 scenic / 7 museum / 6 study-tour examples, a curated set (not a platform-wide viral ranking). Strong posts connect a **reason to visit → navigable sequence → trustworthy evidence**. Scenic posts emphasize routes, museums emphasize highlighted objects, and learning visits emphasize actions and outcomes.','image':'AI concept image — not a real photograph','placeholder':'Offline demo artwork — not an AI-generated image','download_image':'↓  Download image','download_copy':'↓  Download caption','download_json':'↓  Download JSON','prompt':'Image prompt','review':'Quality review','review_note':'Review landmark accuracy, route details, event claims and any generated text before publication. The placeholder cannot be scored as an AI visual.','score':'Weighted review score','metric1':'Visual quality · 25%','metric2':'Landmark accuracy · 25%','metric3':'Style consistency · 20%','metric4':'Cost efficiency · 15%','metric5':'Integration · 15%','eval_download':'↓  Export review','done':'Generation completed','loc_note':'Captions follow the selected interface language. English and Chinese each generate their own text; switch and generate again.','config_error':'Missing required API credentials. See README / .env.example.','category_map':{'风景区':'Scenic attraction','文博场所':'Museum & heritage','研学场所':'Learning experience'},'source':'Post preview','edit':'✎ Edit post','save_edit':'✓ Done editing','features':'RESEARCH-LED  ·  BILINGUAL  ·  MULTI-PROVIDER','provider_status':'Provider configuration','configured':'Configured · not verified','missing':'Not configured','fallback':'Automatic fallback (optional)','fallback_none':'No fallback','fallback_help':'Only tries a second provider if the primary fails. May use billed API credits.','active_backend':'Image generated with','fallback_used':'Fallback used'},
 '中文':{
  'eyebrow':'PAELEAP  /  C1 研究实验室  /  第 02 周','headline':'让每一处风景，都值得分享。','subhead':'从景点名称出发，快速完成内容策划、视觉创作和小红书推广文案。','workspace':'创作简报','workspace_sub':'设置创作方向，开始生成旅行故事。','preview':'推广笔记预览','preview_sub':'你的下一篇旅行故事，从这里开始。','destination':'目的地','destination_help':'选择已研究的景点，或输入自定义景点。','custom':'自定义景点','name':'景点名称','scene':'内容场景','style':'视觉风格','recommend':'根据景点类型推荐','style_custom':'也可以自由选择其他风格。','audience':'目标读者','audience_default':'首次到访游客','angle':'推广主题（可选）','angle_placeholder':'例如：悠闲的湖边午后','picture':'图片生成方式','copy_mode':'文案生成方式','generate':'✦  生成我的旅行笔记','generate_busy':'正在创作旅行故事…','no_result':'一点灵感，即将成为一个故事。','no_result_sub':'在左侧设置景点和风格，然后点击生成，预览图片和文案。','tag1':'发现','tag2':'创作','tag3':'优化',
  'demo':'免费预览 · 非 AI 图片','hf':'Hugging Face · 有限免费额度','cloudflare':'Cloudflare Workers AI · 每日免费额度','wan':'阿里云 Wan · 付费 API','rule':'本地文案模板 · 免费','llm':'LLM API · 需配置密钥','api_note':'Cloudflare 有每日免费额度，Hugging Face 额度可能用完。真实生成需配置 API 密钥。','notice':'本原型仅用于研究测试；生成图片不是现场实拍，发布前必须人工核实事实。','expand':'为什么这样设计？· 第一周研究依据','evidence':'**20 篇参考笔记**：风景区 7 篇、文博场所 7 篇、研学场所 6 篇，为定向样本，并非全平台热度排行榜。核心结构是**来访理由 → 可跟随顺序 → 可信证据**。风景区重路线，文博重藏品，研学重任务与成果。','image':'AI 概念图片 — 非现场实拍','placeholder':'离线演示占位图 — 非 AI 生成图片','download_image':'↓  下载图片','download_copy':'↓  下载文案','download_json':'↓  下载 JSON','prompt':'图片提示词','review':'内容质量检查','review_note':'发布前检查地标外观、路线、活动信息和文案是否准确。占位图不能用于 AI 图像质量评估。','score':'加权评估分数','metric1':'视觉质量 · 25%','metric2':'地标准确性 · 25%','metric3':'风格一致性 · 20%','metric4':'成本效率 · 15%','metric5':'集成性能 · 15%','eval_download':'↓  导出评估','done':'生成完成','loc_note':'文案语言将跟随界面语言。切换语言后需重新生成对应文案。','config_error':'请先在 .env 中配置对应的 API 密钥。','category_map':{'风景区':'风景区','文博场所':'文博场所','研学场所':'研学场所'},'source':'笔记预览','edit':'✎ 编辑笔记','save_edit':'✓ 完成编辑','features':'研究驱动  ·  双语支持  ·  多模型支持','provider_status':'接口配置状态','configured':'已配置 · 未验证','missing':'未配置','fallback':'自动备用接口（可选）','fallback_none':'不使用备用接口','fallback_help':'仅主接口失败时调用备用接口，可能产生费用。','active_backend':'实际使用图片接口','fallback_used':'已使用备用接口'}
}

# Presentation only: generation and credential handling remain unchanged.
COPY['English'].update(eyebrow='A LITTLE WANDER. A GREAT STORY.', headline='Turn places into stories.',
    subhead='Your next RedNote travel post, thoughtfully written and beautifully imagined.',
    workspace='Start with a place', workspace_sub='Set the scene. We’ll help you find the story.',
    preview='Your story, taking shape', preview_sub='Edit the title, caption or hashtags directly. No extra steps, just your own voice.',
    name='Tourist attraction', scene='Category', audience='Target audience', angle='Creative angle',
    picture='Image provider', copy_mode='Caption mode', generate='Generate post ✦',
    no_result='Your next escape, imagined.', no_result_sub='Add a place and choose your direction. Your image and story will appear here.',
    download_image='↓  Download image', download_copy='↓  Save caption')
COPY['English']['category_map']={'风景区':'Scenic','文博场所':'Museum & heritage','研学场所':'Study tour'}
COPY['中文'].update(eyebrow='灵感始于远方，故事由你书写', headline='让每个目的地，都有好故事。',
    subhead='从一个地名开始，用 AI 创作有温度的小红书旅行图文。',
    workspace='从一个目的地开始', workspace_sub='告诉我们你的灵感，其余交给创作。',
    preview='故事，正在发生', preview_sub='直接编辑标题、正文与话题标签，让文字更像你。',
    name='景点名称', scene='景点类别', audience='目标受众', angle='创作角度',
    picture='图片来源', copy_mode='文案模式', generate='生成图文 ✦',
    no_result='想象下一次出发。', no_result_sub='添加景点，选择创作方向，你的图片与故事将在这里出现。')
st.markdown('<style>' + (Path(__file__).parent / 'studio.css').read_text() + '</style>', unsafe_allow_html=True)

bar_left,bar_right=st.columns([5,1.3],vertical_alignment='center')
with bar_left:
    st.markdown('<div class="brand"><span>＊</span> PAELEAP STUDIO</div>',unsafe_allow_html=True)
with bar_right:
    lang=st.segmented_control('Language / 语言',['English','中文'],format_func=lambda v:'EN' if v=='English' else '中文',default='English',key='language',label_visibility='collapsed') or 'English'
t=COPY[lang]
st.markdown(f'''<div class="hero"><div class="hero-label">{escape(t['eyebrow'])}</div><div class="hero-title">{escape(t['headline'])}</div><div class="hero-sub">{escape(t['subhead'])}</div><div class="edition">TRAVEL NOTES / 001</div></div>''',unsafe_allow_html=True)

left,right=st.columns([0.84,1.16],gap='large')
with left:
    st.markdown(f'<div class="panel-title"><span>01</span>{escape(t["workspace"])}</div><div class="panel-sub">{escape(t["workspace_sub"])}</div>',unsafe_allow_html=True)
    with st.container(border=True, key='brief_card'):
        names=list(ATTRACTIONS)
        display={a:(ATTRACTIONS[a].get('name_en',a)+' · '+a) if lang=='English' else a for a in names}
        display['custom']=t['custom']
        chosen=st.selectbox(t['destination'],names+['custom'],format_func=lambda k:display[k],help=t['destination_help'],key='destination')
        attraction=st.text_input(t['name'],value=chosen if chosen!='custom' else '',placeholder='e.g. 杭州西湖 / West Lake',key='custom_name' if chosen=='custom' else f'name_{chosen}')
        found=ATTRACTIONS.get(attraction,{})
        categories=list(TASKS)
        category=st.radio(t['scene'],categories,index=categories.index(found.get('category','风景区')),format_func=lambda v:t['category_map'][v],horizontal=True,key='category')
        styles=list(STYLES)
        audience=st.text_input(t['audience'],value=t['audience_default'])
        angle=st.text_input(t['angle'],placeholder=t['angle_placeholder'])
        recommendation=recommend_style(attraction, category, angle)
        # A changed brief suggests a fresh style; ordinary reruns preserve manual overrides.
        selection_context=(attraction,category,angle)
        if st.session_state.get('style_context')!=selection_context:
            st.session_state['visual_style_choice']=recommendation
            st.session_state['style_context']=selection_context
        st.caption(f'✦ {t["recommend"]}: **{recommendation}** · {t["style_custom"]}')
        style=st.selectbox(t['style'],styles,key='visual_style_choice')
        st.markdown('<div style="height:2px"></div>',unsafe_allow_html=True)
        mode_values=['demo','cloudflare','hf','wan']
        img_mode=st.selectbox(t['picture'],mode_values,format_func=lambda v:t[v],index=(1 if provider_status()['cloudflare'] else 2 if provider_status()['huggingface'] else 3 if provider_status()['alibaba_wan'] else 0))
        fallback_choice=st.selectbox(t['fallback'],['none']+[key for key in ['cloudflare','hf','wan'] if key!=img_mode],format_func=lambda v:t['fallback_none'] if v=='none' else t[v],help=t['fallback_help'])
        copy_mode=st.selectbox(t['copy_mode'],['rule','llm'],format_func=lambda v:t[v])
        st.divider()
        clicked=st.button(t['generate'],type='primary',use_container_width=True,disabled=not attraction.strip())
        st.caption('One image, a title, a caption, and a little inspiration.' if lang=='English' else '一次生成封面、标题、正文与话题标签。')
    st.markdown('<div class="human-note">＊ &nbsp; '+('A starting point, never a substitute for you.<small>Make the words your own. Edit directly in the preview.</small>' if lang=='English' else 'AI 提供灵感，你保留自己的声音。<small>直接编辑预览中的标题和正文，添上你的独家体验。</small>')+'</div>',unsafe_allow_html=True)

if clicked:
    try:
        if not attraction.strip():raise ValueError('Enter an attraction name / 请输入景点名称')
        p=plan(attraction,category,style,audience,angle)
        with st.spinner(t['generate_busy']):
            start=time.monotonic()
            copy=localized_copy(p,lang,os.getenv('TEXT_API_KEY',''),os.getenv('TEXT_BASE_URL',''),os.getenv('TEXT_MODEL','qwen-plus'),use_llm=copy_mode=='llm')
            config=dict(os.environ)
            provider_names={'demo':'placeholder','cloudflare':'cloudflare','hf':'huggingface','wan':'alibaba_wan','none':None}
            img,backend,fallback_note=generate_with_fallback(p,provider_names[img_mode],provider_names[fallback_choice],config)
            elapsed=time.monotonic()-start
            folder=save_output('outputs',p,copy,img,backend,elapsed)
            st.session_state['result']=(p,copy,img,backend,elapsed,str(folder),lang,fallback_note)
            st.session_state['draft_title']=copy['title']
            st.session_state['draft_caption']=copy['caption']
            st.session_state['draft_hashtags']=' '.join(copy['hashtags'])
    except Exception as exc:
        st.error(safe_error(exc))
        if 'result' in st.session_state:
            st.warning('Previous successful post remains below. / 下方保留的是上次成功生成的笔记。')

with right:
    st.markdown(f'<div class="panel-title"><span>02</span>{escape(t["preview"])}</div><div class="panel-sub">{escape(t["preview_sub"])}</div>',unsafe_allow_html=True)
    with st.container(border=False, key='preview_stage'):
        st.markdown('<div class="preview-label">'+('REDNOTE · POST PREVIEW' if lang=='English' else '小红书 · 图文预览')+'</div>',unsafe_allow_html=True)
        if 'result' not in st.session_state:
            st.markdown(f'<div class="preview-placeholder"><div class="placeholder-symbol">✧</div><strong>{escape(t["no_result"])}</strong><div>{escape(t["no_result_sub"])}</div><div class="step-line"><span class="step-pill">{escape(t["tag1"])}</span><span class="step-pill">{escape(t["tag2"])}</span><span class="step-pill">{escape(t["tag3"])}</span></div></div>',unsafe_allow_html=True)
        else:
            p,copy,img,backend,elapsed,folder,result_lang,fallback_note=st.session_state['result']
            st.markdown('<div class="post-masthead"><span class="avatar">p.</span><div>PAELEAP 旅行手记<small>'+escape(p['attraction'])+'</small></div><span class="post-menu">···</span></div>',unsafe_allow_html=True)
            st.image(img,caption=t['placeholder'] if backend=='placeholder' else t['image'],use_container_width=True)
            # Always-visible editable post fields; values persist across Streamlit reruns.
            st.text_input('Title / 标题',key='draft_title',label_visibility='collapsed')
            st.text_area('Caption / 正文',key='draft_caption',height=280,label_visibility='collapsed')
            st.text_area('Hashtags / 话题标签',key='draft_hashtags',height=85,label_visibility='collapsed')
            final_copy={**copy,'title':st.session_state['draft_title'],'caption':st.session_state['draft_caption'],
                        'hashtags':st.session_state['draft_hashtags'].split(),
                        'edited_after_generation':any([st.session_state['draft_title']!=copy['title'],st.session_state['draft_caption']!=copy['caption'],st.session_state['draft_hashtags']!=' '.join(copy['hashtags'])])}
            st.caption(f'{elapsed:.1f}s · {t["active_backend"]}: {backend} · {result_lang} · {p["reference_tags"]}')
            if fallback_note: st.warning(f'{t["fallback_used"]}: {fallback_note}')
            st.caption('Caption source: ' + copy.get('copy_source','unknown'))
            a,b=st.columns(2)
            with a:
                bio=BytesIO();img.save(bio,format='PNG')
                st.download_button(t['download_image'],bio.getvalue(),file_name='paeleap_visual.png',mime='image/png',use_container_width=True)
            with b:st.download_button(t['download_copy'],final_copy['title']+'\n\n'+final_copy['caption']+'\n\n'+' '.join(final_copy['hashtags']),file_name='paeleap_post.txt',use_container_width=True)
            st.download_button(t['download_json'],json.dumps({'plan':p,'post':final_copy,'backend':backend,'language':result_lang,'source_copy':copy},ensure_ascii=False,indent=2),file_name='paeleap_post.json',mime='application/json',use_container_width=True)
            with st.expander(t['prompt']):st.code(p['image_prompt'],language='text')

st.markdown('<div class="footer"><span>PAELEAP STUDIO / '+('MADE FOR EXPLORING' if lang=='English' else '为探索而生')+'</span><span>'+escape(t['notice'])+'</span></div>',unsafe_allow_html=True)
if 'result' in st.session_state:
    with st.expander(t['review']):
        st.caption(t['review_note'])
        fields=['metric1','metric2','metric3','metric4','metric5'];weights=[.25,.25,.2,.15,.15]
        values=[st.slider(t[f],1,5,3,key='score_'+str(i)) for i,f in enumerate(fields)]
        score=sum(v*w for v,w in zip(values,weights))/5*100
        st.metric(t['score'],f'{score:.0f}/100')
        report={'weighted_score':score,'ratings':dict(zip(fields,values)),'backend':st.session_state['result'][3], 'image_test_valid':st.session_state['result'][3]!='placeholder'}
        st.download_button(t['eval_download'],json.dumps(report,indent=2),file_name='paeleap_review.json')
