import sqlite3,time,secrets
from . import config

def db():
 c=sqlite3.connect(config.DB,timeout=15); c.row_factory=sqlite3.Row; return c

def init():
 with db() as c:
  c.executescript('''PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS locations(slug TEXT PRIMARY KEY,name TEXT);
CREATE TABLE IF NOT EXISTS devices(id INTEGER PRIMARY KEY,slug TEXT,name TEXT,host TEXT,enabled INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS orders(token TEXT PRIMARY KEY,device INTEGER,amount INTEGER,currency TEXT,duration INTEGER,state TEXT,session TEXT UNIQUE,deadline REAL,created REAL,error TEXT,attempts INTEGER DEFAULT 0,retry REAL DEFAULT 0);
CREATE UNIQUE INDEX IF NOT EXISTS reserved ON orders(device) WHERE state IN ('creating','awaiting','paid','activating','active','off_failed');
CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS mock(id INTEGER PRIMARY KEY,power INTEGER DEFAULT 0);
''')
  c.execute("INSERT OR IGNORE INTO locations VALUES('sample','Sample charging station')")
  if not c.execute('SELECT 1 FROM devices').fetchone():
   c.executemany('INSERT INTO devices(slug,name,host) VALUES(?,?,?)',[('sample','Plug 1',None),('sample','Plug 2',None)])

def reserve(device):
 token=secrets.token_urlsafe(32)
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  if not c.execute('SELECT 1 FROM devices WHERE id=? AND enabled=1',(device,)).fetchone(): raise ValueError('Unavailable')
  c.execute("INSERT INTO orders(token,device,amount,currency,duration,state,created) VALUES(?,?,100,'eur',300,'creating',?)",(token,device,time.time()))
 return token

def update(token,**values):
 with db() as c: c.execute('UPDATE orders SET '+','.join(k+'=?' for k in values)+' WHERE token=?',[*values.values(),token])
