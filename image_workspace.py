"""Offline image planning UI; all choices feed image_brief, no provider calls."""
import hashlib
import json
from pathlib import Path
import streamlit as st
from image_brief import LIBRARY, VISUAL_STYLES, OPTIONS, DEFAULTS, build_image_brief, context_fingerprint
from local_photo import decode_photo, clear_photo_if_removed, remove_photo


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
    st.caption(label('Choose a direction and refine it. This version prepares prompts; it does not generate or edit images.',
                     '选择方向，再补充细节。本版会整理配图方案，不生成或修改图片。'))
    if not brief:
        st.info(label('Generate a caption first so the place and key details carry over.', '先生成文案，景点、推广重点和目标人群会自动带入。'))
        return
    context=brief['attraction']+'|'+str(brief.get('primary_fact_id',''))
    suggested=brief.get('highlights',[{}])[0].get('label',brief['attraction'])
    old_auto=st.session_state.get('image_auto_subject')
    if st.session_state.get('image_context')!=context:
        if st.session_state.get('form_image_subject') in (None,old_auto):
            st.session_state['form_image_subject']=suggested
        st.session_state['image_context']=context
        st.session_state['image_auto_subject']=suggested
    inputs, output=st.columns([1.05,1],gap='medium')
    def choice(k,zh,en):
        return field(st.selectbox,'image_'+k,DEFAULTS[k],label=label(en,zh),options=list(OPTIONS[k]),
                     format_func=lambda v: OPTIONS[k][v][0 if lang=='中文' else 1])
    with inputs:
        with st.container(border=True):
            st.caption(label('From your caption','沿用文案资料')+' · '+brief['attraction'])
            style=field(st.selectbox,'image_template','natural',label=label('Visual template','视觉模板'),options=list(VISUAL_STYLES),
                        format_func=lambda v: VISUAL_STYLES[v]['name' if lang=='中文' else 'en'])
            st.caption(VISUAL_STYLES[style]['purpose' if lang=='中文' else 'en_purpose'])
            subject=field(st.text_input,'image_subject',suggested,label=label('Main subject','画面主体'),max_chars=160,
                          help=label('One visible subject from the caption. Added details are treated as user-supplied.', '选文案里的一个可见主体；新增内容按用户提供资料处理。'))
            choices={}
            a,b=st.columns(2)
            with a: choices['mode']=choice('mode','创作方式','Creation mode')
            with b: choices['ratio']=choice('ratio','画面比例','Aspect ratio')
            with st.expander(label('More visual details','更多画面细节')):
                a,b=st.columns(2)
                with a:
                    choices['framing']=choice('framing','取景方式','Framing')
                    choices['light']=choice('light','光线氛围','Lighting')
                    choices['people']=choice('people','人物安排','People')
                with b:
                    choices['palette']=choice('palette','色彩方向','Palette')
                    choices['title_space']=choice('title_space','标题位置','Title space')
                    choices['treatment']=choice('treatment','风格化处理','Finish')
                notes=field(st.text_area,'image_notes','',label=label('Extra requirements (optional)','补充画面要求（选填）'),max_chars=600,height=90)
            with st.expander(label('Photos (optional for text concepts)','照片素材（文字概念图可不上传）'),expanded=choices['mode']=='reference' or choices['people']=='portrait'):
                st.caption(label('Uploaded place photos also appear unchanged in the final preview. No styling is applied here.', '景区照片也会作为原图显示在整体预览中；这里不会自动风格化。'))
                photo_key=f"local_photo_{st.session_state.get('photo_epoch',0)}"
                photo=st.file_uploader(label('Place photo / reference','景区照片／参考图'),type=['png','jpg','jpeg','webp'],key=photo_key,max_upload_size=20,on_change=clear_photo_if_removed,args=(photo_key,))
                if photo is not None:
                    digest=hashlib.sha256(photo.getvalue()).hexdigest()
                    if digest!=st.session_state.get('photo_digest'):
                        try:
                            image=decode_photo(photo.getvalue())
                            result.update(image=image,image_source='local_upload',image_plan={'attraction':brief['attraction']})
                            st.session_state['photo_digest']=digest
                        except ValueError:
                            st.error(label('Cannot read this photo. Choose a valid image under 20 MB and 25 MP.', '无法读取照片，请使用20MB、2500万像素以内的有效图片。'))
                if result.get('image') is not None:
                    st.image(result['image'],width=220,caption=label('Original upload · not generated','上传原图 · 非生成结果'))
                    st.button(label('Remove photo','移除配图'),key='remove_photo',on_click=remove_photo)
                if choices['people']=='portrait':
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
        st.button(label('Generate image · not connected','生成图片 · 尚未连接'),key='generate_image',disabled=True,width='stretch')
    with output:
        with st.container(border=True):
            st.markdown('#### '+label('Image brief','配图方案'))
            st.caption(label('Prompt preview only · output quality not tested','仅提示词预览 · 生成效果未测试'))
            ref={'sha256':st.session_state.get('photo_digest',''), 'size':list(result['image'].size),'role':'place_reference'} if result.get('image') is not None else None
            try:
                image_plan=build_image_brief(brief,selected_caption(st.session_state),style,selections=choices,subject=subject,notes=notes,reference=ref,portrait=st.session_state.get('portrait_reference'))
                result['visual_brief']=image_plan
                st.write('**'+brief['attraction']+' · '+subject+'**')
                st.write(VISUAL_STYLES[style]['name' if lang=='中文' else 'en']+' · '+choices['ratio'])
                st.caption(label('Purpose / audience: ','推文目的／目标人群：')+brief.get('purpose','')+' · '+brief.get('audience',''))
                with st.expander(label('View the complete prompt','查看完整提示词')):
                    st.text(image_plan['image_prompt'])
                st.download_button(label('Download prompt','下载提示词'),image_plan['image_prompt'],'paeleap_image_prompt.txt','text/plain',width='stretch')
                st.download_button(label('Download image brief JSON','下载配图方案 JSON'),json.dumps(image_plan,ensure_ascii=False,indent=2),'paeleap_image_brief.json','application/json',width='stretch')
                with st.expander(label('Compare all three templates','对比三种模板')):
                    st.caption(label('Same place, caption and controls; only the template changes. No images are generated.', '固定同一景点、文案和选项，仅切换模板。这里没有生成图片。'))
                    comparison=[]
                    for sid,s in VISUAL_STYLES.items():
                        p=build_image_brief(brief,selected_caption(st.session_state),sid,selections=choices,subject=subject,notes=notes,reference=ref,portrait=st.session_state.get('portrait_reference'))
                        st.markdown('**'+s['name' if lang=='中文' else 'en']+'**')
                        st.caption(s['purpose' if lang=='中文' else 'en_purpose'])
                        comparison.append(p)
                    st.download_button(label('Download three prompts','下载三组对比提示词'),json.dumps(comparison,ensure_ascii=False,indent=2),'paeleap_three_style_comparison.json','application/json')
            except ValueError as exc:
                result.pop('visual_brief',None)
                st.info(str(exc))
            with st.expander(label('Template library V1 & references','模板库 V1 与研究依据')):
                st.caption(label('These are V1 design directions derived from the 20-post research, not three pre-established research labels.', '这三套是从20篇研究归纳的V1设计方向，不是原报告已确定的三个美学标签。'))
                for s in VISUAL_STYLES.values():
                    st.markdown('**'+s['name' if lang=='中文' else 'en']+'**')
                    for r in s['references']:
                        st.markdown(f"[{r['label']} · {r['shortTitle']}]({r['url']})")
                st.caption(label('Mentor reference: recognizable place + paper / ink treatment + optional portrait. Titles are added later.','导师示例：可识别的景区主体＋水墨纸感＋可选人物合成；文字留待后期排版。'))
                doc=Path(__file__).parent/'docs/template_library_v1.md'
                if doc.exists(): st.download_button(label('Download library V1','下载模板库 V1'),doc.read_text(),'Paeleap_Template_Library_V1.md','text/markdown')
