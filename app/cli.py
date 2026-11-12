import argparse,asyncio
from .storage import init,db
from .devices import adapter
from .config import BASE
p=argparse.ArgumentParser(); p.add_argument('command',choices=['init','location','plug','check','qr','unresolved']); p.add_argument('values',nargs='*'); a=p.parse_args(); init()
with db() as c:
 if a.command=='location': c.execute('INSERT INTO locations VALUES(?,?)',a.values)
 if a.command=='plug': c.execute('INSERT INTO devices(slug,name,host) VALUES(?,?,?)',a.values)
 if a.command=='qr':
  import qrcode
  qrcode.make(BASE+'/l/'+a.values[0]).save(a.values[0]+'.png')
 if a.command=='check':
  for d in c.execute('SELECT * FROM devices'): print(d['id'],d['name'],asyncio.run(adapter.power(d)))
 if a.command=='unresolved':
  for o in c.execute("SELECT device,state,error FROM orders WHERE error IS NOT NULL OR state='creating'"): print(dict(o))
