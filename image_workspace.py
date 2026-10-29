"""Offline image planning UI; all choices feed image_brief, no provider calls."""
import hashlib
import streamlit as st
from image_brief import VISUAL_STYLES, DEFAULTS, build_image_brief
from xiaohongshu_templates import template_for, STYLE_IDS, ordered_photos, photo_plan
from local_photo import decode_photo, clear_photo_if_removed, remove_photo


# Friendly choices map to complete visual instructions; hidden legacy controls are ignored.
STYLE_LABELS = {'natural': ('自然清新', 'Fresh scenery'), 'heritage': ('人文纪实', 'Cultural detail'), 'experience': ('活力体验', 'Lively experience')}
MOODS = {
    'auto': ('帮我搭配', 'Match for me', {'light': 'auto', 'palette': 'auto'}),
    'fresh': ('清新明亮', 'Fresh & bright', {'light': 'soft', 'palette': 'cool'}),
    'warm': ('温暖柔和', 'Warm & soft', {'light': 'golden', 'palette': 'warm'}),
    'calm': ('安静自然', 'Calm & natural', {'light': 'overcast', 'palette': 'natural'}),
}
SIZES = {'3:4': ('竖图 · 小红书封面', 'Portrait · cover'), '1:1': ('方图 · 图文配图', 'Square · post'), '16:9': ('横图 · 宽幅展示', 'Landscape · wide')}

def simple_selections(style, mood, ratio, has_photo=False, use_portrait=False):
    return {**DEFAULTS, **MOODS[mood][2], 'ratio': ratio,
            'mode': 'reference' if has_photo else 'concept',
            'people': 'portrait' if use_portrait else 'none',
            'treatment': 'subtle'}


def selected_caption(state):
    result=state.get('result',{})
    variants=result.get('variants',[])
    i=min(state.get('form_caption_variant',0),max(0,len(variants)-1))
    if not variants: return ''
    v=variants[i]
    return '\n'.join(str(state.get(f'form_draft_{i}_{part}',v.get(part,''))) for part in ('title','caption'))


def clear_portrait():
    if st.session_state.get('portrait_upload') is None:
        st.session_state.pop('portrait_reference',None)
        st.session_state.pop('portrait_bytes',None)


def render_image_workspace(field, label, lang):
    result=st.session_state.setdefault('result',{})
    brief=result.get('text_plan',{})
    st.markdown('### '+label('Plan your image','设计配图'))
    st.caption(label('Choose a style and a mood. We will match the details for you.',
                     '沿用小红书模板，选择照片对应的看点，自动安排图片顺序。'))
    if not brief:
        st.info(label('Generate a caption first so the place and key details carry over.', '先生成文案，景点、推广重点和目标人群会自动带入。'))
        return
    subjects=list(dict.fromkeys(h['label'] for h in brief.get('highlights',[]) if h.get('label')))
    subjects=subjects or [brief['attraction']]
    context=brief['attraction']+'|'+str(brief.get('selected_fact_ids',[]))
    if st.session_state.get('simple_image_context')!=context:
        st.session_state['form_image_subject_choice']=subjects[0]
        st.session_state['simple_image_context']=context
        matched=template_for(brief)
        st.session_state['form_image_template']=STYLE_IDS[matched['id']] if matched else 'natural'
    if st.session_state.get('form_image_subject_choice') not in subjects+['custom']:
        st.session_state['form_image_subject_choice']=subjects[0]
    lang_index=0 if lang=='中文' else 1
    inputs, output=st.columns([1.05,1],gap='medium')
    with inputs:
        with st.container(border=True):
            st.caption(label('From your caption','沿用文案资料')+' · '+brief['attraction'])
            style=field(st.radio,'image_template','natural',label=label('What style do you like?','想要什么风格？'),options=list(VISUAL_STYLES),
                        format_func=lambda v: STYLE_LABELS[v][lang_index],horizontal=True)
            subject_choice=field(st.selectbox,'image_subject_choice',subjects[0],label=label('What should stand out?','主要突出什么？'),options=subjects+['custom'],
                                 format_func=lambda v: label('Something else…','自己填写…') if v=='custom' else v)
            subject=subject_choice
            if subject_choice=='custom':
                subject=field(st.text_input,'image_subject',subjects[0],label=label('Describe the subject','写下你想突出的内容'),max_chars=160)
            a,b=st.columns(2)
            with a:
                mood=field(st.selectbox,'image_mood','auto',label=label('What mood?','想要什么感觉？'),options=list(MOODS),format_func=lambda v:MOODS[v][lang_index])
            with b:
                ratio=field(st.selectbox,'image_ratio','3:4',label=label('Image shape','图片尺寸'),options=list(SIZES),format_func=lambda v:SIZES[v][lang_index])
            with st.expander(label('Add photos or a request (optional)','添加照片或补充想法（选填）')):
                notes=field(st.text_area,'image_notes','',label=label('Anything else?','还有什么想法？'),placeholder=label('For example: leave room above for a title','例如：上方留一点空白，方便放标题'),max_chars=600,height=80)
                st.caption(label('Add a place photo to guide its appearance. Photos stay unchanged in this demo.', '有景区照片可以加进来，方便保留真实样貌。本版只展示原图。'))
                photo_key=f"local_photo_{st.session_state.get('photo_epoch',0)}"
                photos=st.file_uploader(label('Place photo / reference','景区照片／参考图'),type=['png','jpg','jpeg','webp'],key=photo_key,max_upload_size=20,accept_multiple_files=True,on_change=clear_photo_if_removed,args=(photo_key,))
                records=[]
                for photo in (photos or []):
                    digest=hashlib.sha256(photo.getvalue()).hexdigest()
                    try:
                        image=decode_photo(photo.getvalue())
                    except ValueError:
                        st.error(label('Cannot read photo: ','无法读取照片：')+photo.name)
                        continue
                    options=['']+[h['id'] for h in brief['highlights']]
                    names={h['id']:h['label'] for h in brief['highlights']}
                    map_key='photo_match_'+digest
                    if map_key not in st.session_state:
                        st.session_state[map_key]=next((p['fact_id'] for p in result.get('photos',[]) if p['digest']==digest and p['fact_id'] in options),'')
                    elif st.session_state[map_key] not in options: st.session_state[map_key]=''
                    fact_id=st.radio(label('Photo subject: ','照片对应看点：')+photo.name,options,
                        format_func=lambda v:names.get(v,label('Not selected','未选择')),key=map_key,horizontal=True)
                    records.append(dict(digest=digest,fact_id=fact_id,name=photo.name,image=image))
                if photos: result['photos']=records
                arranged=ordered_photos(brief,result.get('photos',[]))
                if arranged:
                    result.update(image=arranged[0]['image'],image_source='local_upload',image_plan={'attraction':brief['attraction']})
                    st.session_state['photo_digest']=arranged[0]['digest']
                    st.image(arranged[0]['image'],width=220,caption=label('First photo · unchanged','首图 · 原图展示'))
                    st.button(label('Remove photos','移除全部配图'),key='remove_photo',on_click=remove_photo)
                elif 'photos' in result:
                    for key in ('image','image_source','image_plan'):result.pop(key,None)
                    st.session_state.pop('photo_digest',None)
                if not arranged and result.get('image') is not None:
                    st.image(result['image'],width=220,caption=label('Original upload','上传原图'))
                    st.button(label('Remove photo','移除配图'),key='remove_photo',on_click=remove_photo)
                if records and len(arranged)<len(records):
                    st.caption(label('Unmatched photos stay out of the post.', '未匹配看点的照片不会加入笔记。'))
                use_portrait=field(st.checkbox,'image_use_portrait',False,label=label('Include someone from my photo','加入我提供的人物照片'))
                if use_portrait:
                    st.caption(label('Use a portrait you may use. It is only held in this session, with no model upload.', '请使用你有权使用的人物照片，仅保留在当前会话，不发送给模型。'))
                    person=st.file_uploader(label('Portrait reference','人物参考照片'),type=['png','jpg','jpeg','webp'],max_upload_size=20,key='portrait_upload',on_change=clear_portrait)
                    if person is not None:
                        try:
                            person_img=decode_photo(person.getvalue())
                            st.session_state['portrait_reference']={'sha256':hashlib.sha256(person.getvalue()).hexdigest(),'size':list(person_img.size),'role':'foreground_portrait'}
                            st.session_state['portrait_bytes']=person.getvalue()
                        except ValueError:
                            st.session_state.pop('portrait_reference',None)
                            st.session_state.pop('portrait_bytes',None)
                            st.error(label('Cannot read this portrait.', '无法读取人物照片。'))
                    if st.session_state.get('portrait_bytes'):
                        st.image(st.session_state['portrait_bytes'],width=150,caption=label('Portrait reference only','仅作人物参考'))
        st.button(label('Generate image · coming later','生成图片 · 暂未开放'),key='generate_image',disabled=True,width='stretch')
    choices=simple_selections(style,mood,ratio,result.get('image') is not None,use_portrait)
    with output:
        with st.container(border=True):
            st.markdown('#### '+label('Your image idea','你想要的画面'))
            ref={'sha256':st.session_state.get('photo_digest',''), 'size':list(result['image'].size),'role':'place_reference'} if result.get('image') is not None else None
            try:
                image_plan=build_image_brief(brief,selected_caption(st.session_state),style,selections=choices,subject=subject,notes=notes,reference=ref,portrait=st.session_state.get('portrait_reference'))
                result['visual_brief']=image_plan
                st.write('**'+brief['attraction']+' · '+subject+'**')
                from xiaohongshu_templates import TEMPLATES
                chosen=TEMPLATES[{'natural':'nature','heritage':'ancient_town','experience':'theme_park'}[style]]
                st.write(chosen['visual'])
                st.caption(label('Photo order follows caption highlights.', '配图按正文看点排序；只有一张照片就做单图笔记。'))
                order=photo_plan(brief,result.get('photos',[]))
                for item in order:
                    st.write(str(item['position'])+'. '+item['subject']+' · '+item['name'])
                if not order:
                    st.caption(label('Add photos to preview actual images.', '添加照片后可预览实际配图；没有照片时只保留文案。'))
                st.caption(MOODS[mood][lang_index]+' · '+SIZES[ratio][lang_index])
                if ref: st.caption(label('Your place photo will guide the scene.', '已带入你的景区照片，作为画面依据。'))
                if use_portrait: st.caption(label('Your portrait is included as a reference.', '已带入人物照片作为参考。'))
                if notes.strip(): st.write(label('Your request: ','你的想法：')+notes.strip())
                st.caption(label('Composition, colors and styling are matched automatically. Your caption and audience carry over.', '构图、配色和质感会自动搭配，文案内容和目标人群也已带入。'))
                st.info(label('Your choices are saved. Image generation is not connected yet; continue to Preview to review your caption and any uploaded photo.', '选择已保存。目前尚未接入图片生成，可以继续预览文案和上传的原图。'))
            except ValueError as exc:
                result.pop('visual_brief',None)
                st.info(str(exc))
