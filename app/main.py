import asyncio,contextlib,time,os,sqlite3
import stripe
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse
from . import config
from .storage import init,db,reserve,update
from .devices import adapter
from .worker import run
stripe.api_key=os.getenv('STRIPE_SECRET_KEY')
@contextlib.asynccontextmanager
async def lifespan(app):
 init(); task=asyncio.create_task(run()); app.state.worker=task; yield; task.cancel()
 with contextlib.suppress(asyncio.CancelledError): await task
app=FastAPI(lifespan=lifespan)
@app.get('/healthz')
async def health():
 with db() as c: c.execute('SELECT 1').fetchone()
 return {'status':'ok','worker_running':not app.state.worker.done()}

@app.middleware('http')
async def headers(request,call_next):
 r=await call_next(request); r.headers['Cache-Control']='no-store'; r.headers['Referrer-Policy']='no-referrer'; return r

def page(body):
 return HTMLResponse('''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Power station</title><style>body{font:17px system-ui;background:#edf2f5;color:#172b36;max-width:650px;margin:40px auto;padding:20px}article{background:white;padding:24px;border-radius:16px;margin:16px 0}button{background:#146c60;color:white;border:0;padding:14px 22px;border-radius:9px;font:inherit}button:disabled{background:#75868a}small{display:block;margin:12px 0}h1{font-size:32px}</style>'''+('<p>DEMO — no real payment or device control</p>' if config.PAYMENTS=='demo' else '')+body)
@app.get('/')
async def root(): return RedirectResponse('/l/sample')
@app.get('/l/{slug}')
async def location(slug:str):
 import html
 with db() as c:
  loc=c.execute('SELECT * FROM locations WHERE slug=?',(slug,)).fetchone()
  devices=c.execute('SELECT * FROM devices WHERE slug=? AND enabled=1',(slug,)).fetchall()
 if not loc: raise HTTPException(404)
 body='<h1>'+html.escape(loc['name'])+'</h1><p>Choose a plug · €1.00 / 5 minutes</p>'
 for d in devices:
  with db() as c: busy=c.execute("SELECT 1 FROM orders WHERE device=? AND state IN ('creating','awaiting','paid','activating','active','off_failed')",(d['id'],)).fetchone()
  try: available=not await adapter.power(d) and not busy; status='Available' if available else 'Busy'
  except Exception: available=False; status='Offline / uncertain'
  body+=f'<article><h2>{html.escape(d["name"])}</h2><p>{status}</p><small>Checked just now</small><form method="post" action="/checkout/{d["id"]}"><button '+('' if available else 'disabled')+'>Pay €1.00</button></form></article>'
 return page(body)
rates={}
@app.post('/checkout/{device}')
async def checkout(device:int,request:Request):
 key=request.client.host; now=time.time(); rates[key]=[t for t in rates.get(key,[]) if now-t<60]
 if len(rates[key])>=10: raise HTTPException(429,'Try again shortly')
 rates[key].append(now)
 with db() as c: d=c.execute('SELECT * FROM devices WHERE id=? AND enabled=1',(device,)).fetchone()
 if not d: raise HTTPException(404)
 try:
  if await adapter.power(d): raise HTTPException(409,'Plug unavailable')
 except HTTPException: raise
 except Exception: raise HTTPException(409,'Device unreachable')
 try: token=reserve(device)
 except sqlite3.IntegrityError: raise HTTPException(409,'Plug reserved')
 if config.PAYMENTS=='demo':
  update(token,state='awaiting'); return RedirectResponse('/order/'+token,303)
 try:
  s=await asyncio.to_thread(stripe.checkout.Session.create,mode='payment',line_items=[{'price_data':{'currency':'eur','unit_amount':100,'product_data':{'name':'Five minutes of power'}},'quantity':1}],success_url=config.BASE+'/order/'+token,cancel_url=config.BASE+'/order/'+token,client_reference_id=token,expires_at=int(now)+1800,idempotency_key=token)
  update(token,state='awaiting',session=s.id); return RedirectResponse(s.url,303)
 except Exception:
  # Retain reservation: API outcome may be uncertain. CLI review required.
  update(token,error='Checkout creation uncertain; operator review required'); raise HTTPException(503,'Checkout unavailable; contact operator')
@app.get('/api/order/{token}')
async def status(token:str):
 with db() as c: o=c.execute('SELECT state,deadline,error FROM orders WHERE token=?',(token,)).fetchone()
 if not o: raise HTTPException(404)
 return dict(o)|{'server_time':time.time()}
@app.get('/order/{token}')
async def order(token:str):
 await status(token)
 return page('''<h1>Your power session</h1><article><h2 id="state">Loading…</h2><p id="remaining"></p><p id="error"></p></article>'''+(f'<form method="post" action="/demo/{token}"><button>Simulate payment</button></form>' if config.PAYMENTS=='demo' else '')+'''<script>async function refresh(){let r=await fetch('/api'+location.pathname),s=await r.json();document.getElementById('state').textContent=s.state;document.getElementById('error').textContent=s.error||'';document.getElementById('remaining').textContent=s.state==='active'?Math.max(0,Math.ceil(s.deadline-s.server_time))+' seconds remaining':''}refresh();setInterval(refresh,1000)</script>''')
if config.PAYMENTS=='demo':
 @app.post('/demo/{token}')
 async def demo(token:str):
  with db() as c: c.execute("UPDATE orders SET state='paid' WHERE token=? AND state='awaiting'",(token,))
  return RedirectResponse('/order/'+token,303)

def accept(event):
 obj=event['data']['object']; typ=event['type']
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  if c.execute('SELECT 1 FROM events WHERE id=?',(event['id'],)).fetchone(): return
  o=c.execute('SELECT * FROM orders WHERE session=?',(obj.get('id'),)).fetchone()
  if o and typ in ('checkout.session.completed','checkout.session.async_payment_succeeded') and obj.get('payment_status')=='paid':
   if obj.get('amount_total')!=o['amount'] or obj.get('currency')!=o['currency'] or obj.get('mode')!='payment' or obj.get('client_reference_id')!=o['token']: raise ValueError('Payment mismatch')
   if o['state'] in ('creating','awaiting'): c.execute("UPDATE orders SET state='paid' WHERE token=?",(o['token'],))
   elif o['state']=='expired': c.execute("UPDATE orders SET error='Late payment; refund review required' WHERE token=?",(o['token'],))
  if o and typ=='checkout.session.expired' and o['state']=='awaiting': c.execute("UPDATE orders SET state='expired' WHERE token=?",(o['token'],))
  c.execute('INSERT INTO events VALUES(?)',(event['id'],))
@app.post('/webhook')
async def webhook(request:Request):
 if config.PAYMENTS!='stripe': raise HTTPException(404)
 try:
  event=stripe.Webhook.construct_event(await request.body(),request.headers.get('stripe-signature',''),os.environ['STRIPE_WEBHOOK_SECRET']); accept(event)
 except Exception: raise HTTPException(400,'Invalid webhook')
 return {'received':True}
