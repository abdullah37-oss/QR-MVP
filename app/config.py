import os
from dotenv import load_dotenv
load_dotenv()
PAYMENTS=os.getenv('PAYMENTS','demo')
DEVICES=os.getenv('DEVICES','mock')
BASE=os.getenv('PUBLIC_BASE_URL','http://localhost:8000').rstrip('/')
DB=os.getenv('DB_PATH','power.db')
if PAYMENTS not in ('demo','stripe') or DEVICES not in ('mock','tapo'): raise RuntimeError('Invalid mode')
ENVIRONMENT=os.getenv('ENVIRONMENT','development')
if PAYMENTS=='demo':
 if DEVICES!='mock' or ENVIRONMENT not in ('development','hosted-demo'):
  raise RuntimeError('Demo requires mock devices and an explicit demo environment')
 if ENVIRONMENT=='hosted-demo':
  if os.getenv('ENABLE_HOSTED_DEMO')!='true': raise RuntimeError('Explicit hosted demo opt-in required')
  if not BASE.startswith('https://'): raise RuntimeError('Hosted demo requires HTTPS PUBLIC_BASE_URL')
  if not os.path.isabs(DB): raise RuntimeError('Hosted demo requires an absolute persistent DB_PATH')
  if any(os.getenv(k) for k in ('STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET','TAPO_USERNAME','TAPO_PASSWORD')):
   raise RuntimeError('Hosted demo must not contain payment or hardware credentials')
if ENVIRONMENT=='hosted-demo' and PAYMENTS!='demo': raise RuntimeError('Hosted demo only permits simulated payments')
if PAYMENTS=='stripe' and not all(os.getenv(k) for k in ('STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET')): raise RuntimeError('Stripe credentials required')
