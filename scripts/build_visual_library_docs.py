"""Rebuild the human-readable library and two-place, three-style prompt comparison."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from image_brief import LIBRARY, VISUAL_STYLES, build_image_brief
from promotional_brief import build_detailed_brief, case_highlights, CASE_CATEGORIES
from template_engine import generate_drafts

def sample(filename):
    data=json.loads((ROOT/'data'/filename).read_text())
    highlights=case_highlights(data)
    brief=build_detailed_brief(name=data['name'],category=CASE_CATEGORIES[data['category']],style='简洁',purpose='种草推荐',audience='一般游客',highlights=highlights,selected=[h['label'] for h in highlights[:2]],primary=highlights[0]['label'],data=data)
    drafts=generate_drafts(brief,mode='offline')['versions'][0]
    caption=drafts['title']+'\n'+drafts['caption']
    return [build_image_brief(brief,caption,s,subject=highlights[0]['label']) for s in VISUAL_STYLES]

comparisons=sample('wuzhen_xizha.json')+sample('west_lake.json')
(ROOT/'templates/comparison_prompts_v1.json').write_text(json.dumps(comparisons,ensure_ascii=False,indent=2)+'\n')
intro='''# Paeleap 图片模板库 V1

版本：1.0 · 2026-10-27 · 状态：离线提示词模板，尚未进行 AI 图片生成或效果验证。

## 这三种方向从哪里来

已回查项目聊天《Paeleap C1 internship》《Week 1》，以及 2026-10-14《最终20篇视觉风格分类报告》和配套 P1–P20 视觉标签。
原报告将样本按风景区（7）、文博场所（7）、研学场所（6）组织，强调图片的信息任务，**没有将三种固定美学风格定为研究结论**。
下面三套是本次从样本转译的产品模板 V1，待导师反馈后调整。不能把景区类型、文本风格与图片风格混为一谈。

原始报告：../outputs/01a12e9f-8427-7e62-b8e2-38dc79936eca/Paeleap_C1_最终20篇视觉风格分类报告_2026-10-14.html（项目资料，非本仓库文件）。
引用的图页观察来自已存档研究；本次没有重新核实笔记互动数据、活动日期或景区服务。

## 简单使用流程

1. 先生成文案；景点、推广重点、目的、人群和当前选中的文案自动带入图片页。
2. 选择一套模板、画面主体、创作方式与比例。
3. 有准确景区照片时用“参考照片风格化”；纯文字模式仅提供概念方向，不能保证地标准确。
4. 根据需要展开光线、色彩、构图、人物、留白、处理方式；不需要填写所有选项。
5. 查看并下载提示词或 JSON；三模板对比保持同一内容和用户选项，只切换模板。
6. 可用上传原图查看图文搭配。原图不会在本版被风格化，不会作为生成样例展示。

'''
sections=[intro]
for sid,s in VISUAL_STYLES.items():
    example=next(x for x in comparisons if x['style_id']==sid)
    refs='\n'.join(f"- [{r['label']} · {r['shortTitle']}]({r['url']})：{r['evidence']}；借鉴：{r['lesson']}" for r in s['references'])
    sections.append(f"""## {s['name']} / {s['en']}

**用途**：{s['purpose']}

| 模板要素 | 规则 |
|---|---|
| 色彩 | {s['palette']} |
| 光线 | {s['lighting']} |
| 构图 | {s['composition']} |
| 质感 | {s['texture']} |
| 可替换字段 | 景点、文案主体、可用事实、目标人群、宣传目的、构图、比例、光线、人物、留白、处理强度方向 |

**研究依据与设计延伸**：{s['adaptation']}

{refs}

**完整示例提示词（乌镇西栅，未生成图片）**

```text
{example['image_prompt']}
```

""")
sections.append('''## 导师示例如何落到产品里

2026-10-27 导师示例可拆为：景区主体 + 水墨山景/纸感边框 + 前景人物 + 后期标题和“打卡”贴纸。
这是**参考照片编辑/人物合成**方向，不能承诺单靠景点名就能还原建筑或人物。

- 在“人文故事海报”下选择“水墨纸感”；也可选轻度处理，减少装饰。
- 上传景区参考图用于约束真实结构；如要加入人物，另外上传人物参考图。
- 保留照片中主体的外形和身份特征，人物合成不等于曾经到访。
- 示例中的人物、奖杯、地标和文字不是自动添加到所有图片里的素材。本库不打包导师截图和人物照片。
- 本版仅记录参考图的尺寸、摘要和角色；素材只留在当前会话，不调用模型。
- 中文标题与印章不交给模型生成，先保留空白，后续人工排版。

## 选项怎样改变画面

| 输入 | 实际作用 |
|---|---|
| 景点/推广重点/文案 | 决定画面对象及与文案的对应关系，避免切换风格后换了景点 |
| 模板 | 切换单幅实景感、文化主视觉、三格体验组织 |
| 创作方式 | 区分无参考的概念设计与需要照片的结构保留编辑 |
| 画面主体 | 把注意力集中到一个具体、可见的景物或物件 |
| 比例 | 定义竖版、方形或横版构图；本版不裁切上传原图 |
| 取景 | 整体环境、局部特写、居中主体；拼贴中作用于主格 |
| 光线 | 自然柔光、夕照、阴天、夜景等创意设定；不推断真实天气或营业安排 |
| 色彩 | 明确背景与点缀色，保留主体本色 |
| 人物 | 不添加、少量远景、用户提供人物；缺少人物参考时不允许完成该方案 |
| 标题留白 | 预留上方或侧边空间，不生成乱码文字 |
| 风格化处理 | 模板默认、轻度、水墨纸感、剪贴手账 |

## 两个景点 × 三个模板对比准备

随附 `comparison_prompts_v1.json` 有乌镇西栅和杭州西湖共六份完整方案。
每个景点固定同一文案、主体、比例（3:4）、无新增人物、上方留白，仅切换模板。
预期差异是构图与表现语言，不是编造新的景点设施。六份是**待生成提示词**，不是已经完成的效果对比。

| 后续检查项 | 当前状态 | 通过标准 |
|---|---|---|
| 输入真正影响提示词 | 自动化与页面测试 | 每项改变对应指令，返回步骤/语言切换不丢选择 |
| 景点与文案一致 | 提示词层面可查 | 重点来自当前文案资料，不混入其他景点 |
| 地标/人物外观准确 | 未测试 | 将真实生成结果与可用原图逐项对照 |
| 三种风格可辨认 | 未测试 | 同一景点三图的主体相同，构图/表现可区分 |
| 文字与版式 | 未测试 | 后期文字清楚，不遮主体，不伪造现场标识 |
| 可复用性 | 已准备第二景点提示词；出图未测试 | 更换景点仍保持模板规则，不残留上一景点内容 |

## 本周交付状态

已准备：模板库文档、机器可读模板、六份对比提示词、离线图片工作区、图文预览、下载。
仍待：导师确认方向；用户授权后接模型；实际生成六图、检查准确性与风格；修订模板。
因此当前可称“文生图工作区原型与模板库 V1”，不能称“实际文生图效果已验证”。
''')
(ROOT/'docs/template_library_v1.md').write_text('\n'.join(sections))
(ROOT/'docs/week3_delivery.md').write_text('''# Week 3 交付说明

分享版：https://paeleap-week3-yuxuan.streamlit.app/

- 主工作仓库：AkChetti06/paeleap，week-3-combined。
- 个人演示副本：YuXuan0610yoyo/paeleap，week-3-combined；用于独立部署。
- 流程：生成文案 → 图片页细化方案/可选原图 → 整体预览与下载。
- 文案：离线规则模板；图片：仅准备提示词，不调用 API，不声称生成。
- 模板库：自然实景感、人文故事海报、体验步骤拼贴；属于从研究转译的 V1 设计方向。
- 导师示例：纳入水墨纸感、参考照片保形、可选人物参考与标题留白。
- 文件：template_library_v1.md、../templates/visual_library_v1.json、../templates/comparison_prompts_v1.json。
- 待反馈：三套方向与使用流程是否适合内部同事；导航位置保留现状。
- 待完成：真实图片生成、质量/准确性/风格测试。当前没有可报告的 API 效果、速度或成本实测。

演示建议：选乌镇西栅生成文案 → 图片选择“人文故事海报” → 展开细节选择“水墨纸感” → 查看提示词 → 对比三模板 → 预览。也可以上传可用照片查看原图与文案的搭配。
''')
print('Wrote library, delivery notes and',len(comparisons),'ungenerated comparison prompts.')
