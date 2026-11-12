import os
from . import config
from .storage import db
class Adapter:
 async def power(self,d,value=None):
  if config.DEVICES=='mock':
   with db() as c:
    c.execute('INSERT OR IGNORE INTO mock(id) VALUES(?)',(d['id'],))
    if value is not None: c.execute('UPDATE mock SET power=? WHERE id=?',(int(value),d['id']))
    return bool(c.execute('SELECT power FROM mock WHERE id=?',(d['id'],)).fetchone()[0])
  from kasa import Discover,Credentials
  device=await Discover.discover_single(d['host'],credentials=Credentials(os.environ['TAPO_USERNAME'],os.environ['TAPO_PASSWORD']))
  if device is None: raise RuntimeError('Device unreachable')
  try:
   await device.update()
   if value is not None:
    await (device.turn_on() if value else device.turn_off())
    await device.update()
   return device.is_on
  finally: await device.disconnect()
adapter=Adapter()
