import time,asyncio
from .storage import db,update
from .devices import adapter
async def tick():
 with db() as c: rows=c.execute("SELECT o.*,d.host,d.name FROM orders o JOIN devices d ON d.id=o.device WHERE state IN ('paid','activating','active','off_failed')").fetchall()
 for o in rows:
  d={'id':o['device'],'host':o['host']}; now=time.time()
  if o['retry']>now: continue
  try:
   if o['state']=='paid':
    update(o['token'],state='activating',deadline=now+o['duration'])
   deadline=o['deadline'] if o['deadline'] is not None else now+o['duration']
   if now>=deadline or o['state']=='off_failed':
    if await adapter.power(d,False): raise RuntimeError('OFF unconfirmed')
    update(o['token'],state='completed',error=o['error'])
   elif o['state']!='active':
    if not await adapter.power(d,True): raise RuntimeError('ON unconfirmed')
    update(o['token'],state='active',deadline=deadline)
  except Exception:
   # Any uncertain ON is followed by OFF; reservation stays locked until confirmed.
   update(o['token'],state='off_failed',error='Control unresolved; refund review required',attempts=o['attempts']+1,retry=now+min(60,2**min(o['attempts'],6)))
async def run():
 while True:
  await tick(); await asyncio.sleep(1)
