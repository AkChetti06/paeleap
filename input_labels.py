"""Translate display labels only; canonical brief values and user facts stay unchanged."""
import streamlit as st
EN = {
'景区类型':'Attraction category','你想推广哪里？':'Which place are you promoting?',
'场所名称':'Place name','填写景点或场所名称':'Enter a place name',
'场所简介':'Place introduction','写清场所是什么、有哪些已确认的特色。':'Describe the place and its confirmed features.',
'候选亮点：一行一个“名称｜具体说明”':'Highlights: one “Name | Description” per line',
'文本风格':'Writing tone','推文目的':'Post purpose','目标人群':'Target audience',
'学习阶段（选填）':'Learning stage (optional)','计划游玩时长（选填）':'Visit duration (optional)',
'活动名称':'Event name','活动日期／时间':'Event date / time','活动地点':'Event location','参与方式':'How to participate',
'本篇推广重点（选1至3项）':'Highlights to include (choose 1–3)','最想突出的一个重点':'Main highlight',
'补充事实（选填）':'Additional facts (optional)',
'简洁：短句直述；活泼：轻松口语；严肃：稳重说明。':'Concise: direct and brief. Lively: conversational. Formal: measured and informative.',
'这个重点会进入标题和开头，其余选择作为支持内容。':'This highlight leads the title and introduction; other choices support it.',
'会原样放入“补充信息”，请填真实信息，不要在此填写写作指令；语气与目的使用上面的选项。':'Included as supplied. Add verified facts here; use the tone and purpose controls for writing preferences.',
'用于建议取舍看点，不会据此编造路线或承诺游览耗时。':'Used to prioritize highlights, not to invent routes or promise travel times.',
'活动文案需要以下四项信息；仅使用你填写的内容。':'Event posts require all four details below. Only supplied details are used.',
'这个场所暂无匹配资料，请补充简介与真实亮点。填写内容将直接用于离线文案，不会自动查询或核验。':'No saved facts for this place. Add an introduction and real highlights. Your facts are used as supplied, without automatic lookup or verification.',
'其他场所（填写资料）':'Other place (provide facts)',
'自然景观':'Natural scenery','博物馆':'Museum','研学基地':'Educational site','古镇／历史街区':'Historic town / district','主题乐园':'Theme park',
'简洁':'Concise','活泼':'Lively','严肃':'Formal','种草推荐':'Recommendation','宣传科普':'Educational introduction','游玩攻略':'Visit guide','活动宣传':'Event promotion',
'一般游客':'General visitors','亲子家庭':'Families with children','学生／研学团体':'Students / study groups','朋友结伴':'Friends','情侣':'Couples',
'约1小时':'About one hour','不限定':'No preference','小学':'Primary school','初中':'Middle school','高中':'High school','大学及以上':'University and above','半天':'Half a day','一天':'One day','两小时以内':'Up to two hours',
'乌镇西栅':'Wuzhen Xizha','杭州西湖':'West Lake, Hangzhou','杭州宋城':'Songcheng, Hangzhou',
'水乡风景':'Waterside scenery','蓝印花布':'Blue printed cloth','老邮局':'Old post office','湖面山景':'Lake and mountain views','苏堤':'Su Causeway','白堤':'Bai Causeway','文化演艺':'Cultural performances','宋城千古情':'Songcheng Eternal Love','主题街区':'Themed streets',
'请补充这个场所的简介，程序不会自动查询资料。':'Please add an introduction. This prototype does not look up facts automatically.',
'请填写景点名称（最多80字）。':'Enter a place name (up to 80 characters).',
'请选择1至3个不同的推广重点。':'Choose 1–3 different highlights.',
'主重点必须来自本次选择的推广重点。':'The main highlight must be one of your selected highlights.',
'每条亮点请按“名称｜具体说明”填写，一行一条。':'Enter one “Name | Description” per line.',
'亮点名称不能重复。':'Highlight names must be unique.'
}

class LocalizedFields:
    def __init__(self, language):
        self.english = language == 'English'
    def text(self, value):
        if not self.english or not isinstance(value, str): return value
        if value.startswith('例如填写已确认的'): return 'Example: Exhibition | Describe its confirmed contents.'
        return EN.get(value, value)
    def __getattr__(self, name):
        target = getattr(st, name)
        def widget(*args, **kwargs):
            args = list(args)
            if args: args[0] = self.text(args[0])
            for key in ('help','placeholder'):
                if key in kwargs: kwargs[key] = self.text(kwargs[key])
            if name in ('selectbox','multiselect'):
                kwargs['format_func'] = self.text
            return target(*args, **kwargs)
        return widget
