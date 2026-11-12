import asyncio
import pytest
from fastapi.testclient import TestClient
from app import config
from app.storage import init,db,reserve,update
from app.main import app,accept
from app.worker import tick
@pytest.fixture(autouse=True)
def database(tmp_path):
 config.DB=str(tmp_path/'test.db'); init()
def test_reservation():
 reserve(1)
 with pytest.raises(Exception): reserve(1)
def event(token,**changes):
 obj=dict(id='cs_test',payment_status='paid',amount_total=100,currency='eur',mode='payment',client_reference_id=token); obj.update(changes)
 return dict(id='evt_test',type='checkout.session.completed',data={'object':obj})
def test_paid_duplicate_and_restart():
 t=reserve(1); update(t,session='cs_test',state='awaiting'); accept(event(t)); accept(event(t)); asyncio.run(tick())
 with db() as c: assert c.execute('SELECT state FROM orders').fetchone()[0]=='active'
 update(t,deadline=0); asyncio.run(tick())
 with db() as c: assert c.execute('SELECT state FROM orders').fetchone()[0]=='completed'
def test_unpaid():
 t=reserve(1); update(t,session='cs_test',state='awaiting'); accept(event(t,payment_status='unpaid'))
 with db() as c: assert c.execute('SELECT state FROM orders').fetchone()[0]=='awaiting'
@pytest.mark.parametrize('change',[{'amount_total':1},{'currency':'usd'}])
def test_wrong(change):
 t=reserve(1); update(t,session='cs_test',state='awaiting')
 with pytest.raises(ValueError): accept(event(t,**change))
def test_http():
 with TestClient(app) as c:
  assert c.get('/l/sample').status_code==200
  assert c.post('/webhook',content='forged').status_code==404
  r=c.post('/checkout/1'); assert r.status_code==200
  token=str(r.url).split('/')[-1]; c.post('/demo/'+token)
  assert c.get('/api/order/'+token).json()['state'] in ('paid','active')
def test_off_failure(monkeypatch):
 from app.devices import adapter
 t=reserve(1); update(t,state='active',deadline=0)
 async def fail(*args): raise OSError('offline')
 monkeypatch.setattr(adapter,'power',fail); asyncio.run(tick())
 with db() as c: assert c.execute('SELECT state FROM orders').fetchone()[0]=='off_failed'
 with pytest.raises(Exception): reserve(1)
def test_activation_failure(monkeypatch):
 from app.devices import adapter
 t=reserve(1); update(t,state='paid')
 async def fail(*args): raise OSError('offline')
 monkeypatch.setattr(adapter,'power',fail); asyncio.run(tick())
 with db() as c: assert c.execute('SELECT error FROM orders').fetchone()[0]
def test_demo_restriction():
 import subprocess,sys,os
 r=subprocess.run([sys.executable,'-c','import app.config'],env=dict(os.environ,DEVICES='tapo',PAYMENTS='demo'),capture_output=True)
 assert r.returncode!=0
def test_forged_stripe(monkeypatch):
 monkeypatch.setattr(config,'PAYMENTS','stripe'); monkeypatch.setenv('STRIPE_WEBHOOK_SECRET','whsec_test')
 with TestClient(app) as c: assert c.post('/webhook',content='{}',headers={'stripe-signature':'bad'}).status_code==400
def test_health():
 with TestClient(app) as c:
  assert c.get('/healthz').json()=={'status':'ok','worker_running':True}
@pytest.mark.parametrize('extra,valid',[
 ({},True),({'ENABLE_HOSTED_DEMO':'false'},False),({'DEVICES':'tapo'},False),
 ({'ENVIRONMENT':'production'},False),({'PAYMENTS':'stripe'},False),
 ({'STRIPE_SECRET_KEY':'sk_test_fake'},False),({'DB_PATH':'relative.db'},False),
 ({'PUBLIC_BASE_URL':'http://example.com'},False)])
def test_hosted_config(extra,valid,tmp_path):
 import subprocess,sys,os
 env=dict(os.environ,ENVIRONMENT='hosted-demo',ENABLE_HOSTED_DEMO='true',PAYMENTS='demo',DEVICES='mock',DB_PATH=str(tmp_path/'persist.db'),PUBLIC_BASE_URL='https://example.com')
 for key in ('STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET','TAPO_USERNAME','TAPO_PASSWORD'): env.pop(key,None)
 env.update(extra)
 r=subprocess.run([sys.executable,'-c','import app.config'],env=env,capture_output=True)
 assert (r.returncode==0)==valid
