import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import plan,fallback_copy,placeholder,save_output

def test_west_lake_plan():
 p=plan('杭州西湖')
 assert p['category']=='风景区' and p['style']=='Scenic & Cinematic'
 assert 'no captions' in p['image_prompt']

def test_all_scenarios():
 for place in ['杭州西湖','浙江省博物馆','杭州宋城']:
  p=plan(place);c=fallback_copy(p)
  assert len(c['hashtags'])==4 and place in c['title']

def test_placeholder_is_explicit_and_output(tmp_path):
 p=plan('杭州西湖');c=fallback_copy(p);im=placeholder(p)
 assert im.size==(900,1200)
 folder=save_output(tmp_path,p,c,im,'placeholder',0.1)
 assert (folder/'visual.png').exists() and (folder/'post.json').exists()

def test_invalid_inputs():
 import pytest
 with pytest.raises(ValueError):plan('')
 with pytest.raises(ValueError):plan('a',category='invalid')

def test_english_copy():
 from engine import english_copy, localized_copy
 p=plan('杭州西湖')
 c=english_copy(p)
 assert 'West Lake' in c['title']
 assert len(c['hashtags']) == 4
 assert localized_copy(p,'English')['title']==c['title']

def test_cloudflare_image_success(monkeypatch):
 import base64
 from io import BytesIO
 from PIL import Image
 import engine
 buf=BytesIO();Image.new('RGB',(16,20),'blue').save(buf,'PNG')
 class Response:
  status_code=200
  def json(self):return {'success':True,'result':{'image':base64.b64encode(buf.getvalue()).decode()}}
 def fake_post(url,headers,json,timeout):
  assert '/ai/run/@cf/black-forest-labs/flux-1-schnell' in url
  assert json['steps']==4 and 'prompt' in json
  assert headers['Authorization']=='Bearer secret'
  return Response()
 monkeypatch.setattr(engine.requests,'post',fake_post)
 assert engine.generate_cloudflare_image(engine.plan('杭州西湖'),'a'*32,'secret').size==(16,20)

def test_cloudflare_auth_error(monkeypatch):
 import engine,pytest
 class Response: status_code=403
 monkeypatch.setattr(engine.requests,'post',lambda *args,**kwargs:Response())
 with pytest.raises(engine.ImageProviderError,match='authentication'):
  engine.generate_cloudflare_image(engine.plan('杭州西湖'),'a'*32,'secret')

def test_fallback_explicit_only():
 import engine,pytest
 p=engine.plan('杭州西湖'); generators={'cloudflare':lambda: (_ for _ in ()).throw(ValueError('broken')),'huggingface':lambda:engine.placeholder(p)}
 with pytest.raises(ValueError):engine.generate_with_fallback(p,'cloudflare',None,{'HF_TOKEN':'token'},generators)
 im,which,note=engine.generate_with_fallback(p,'cloudflare','huggingface',{'HF_TOKEN':'token'},generators)
 assert im.size==(900,1200) and which=='huggingface' and note


def test_personalized_template_uses_brief():
 from engine import localized_copy
 p=plan('杭州西湖',audience='摄影爱好者',visit_reason='清晨湖光')
 cn=localized_copy(p,'中文')
 en=localized_copy(p,'English')
 assert '摄影爱好者' in cn['caption'] and '清晨湖光' in cn['caption']
 assert '摄影爱好者' in en['caption'] and '清晨湖光' in en['caption']

def test_llm_mode_requires_credentials():
 import pytest
 from engine import localized_copy
 with pytest.raises(ValueError,match='TEXT_API_KEY'):
  localized_copy(plan('杭州西湖'),'中文',use_llm=True)
