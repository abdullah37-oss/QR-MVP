# QR Power MVP

Single-instance FastAPI/SQLite controller. Demo uses persistent simulated plugs and simulated payment. EUR 1.00 buys 300 seconds. Do not run multiple workers.

## Windows PowerShell
Install Python 3.11 or newer, then:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m app.cli init
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```
Open http://localhost:8000/l/sample. Select a plug and simulate payment. Keep the controller running for shutoff. Refresh preserves progress.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.cli location lobby 'Lobby'
.\.venv\Scripts\python.exe -m app.cli plug lobby 'Socket A' 192.168.1.20
.\.venv\Scripts\python.exe -m app.cli check
.\.venv\Scripts\python.exe -m app.cli qr lobby
.\.venv\Scripts\python.exe -m app.cli unresolved
```
QR uses PUBLIC_BASE_URL. Print the generated PNG with a readable margin and scan-test at its intended size.

## Configuration
Copy .env.example to .env; keep credentials local. Defaults use mock devices and simulated payments. PUBLIC_BASE_URL determines QR links; DB_PATH selects persistent SQLite storage. Hosted simulation needs the explicit settings in .env.hosted-demo.example. Stripe mode requires backend credentials and verified webhooks; it never silently falls back to simulation.

## Architecture
- app/main.py: FastAPI customer routes, inline HTML/CSS/JavaScript, Checkout and webhook validation.
- app/config.py and app/storage.py: environment validation and persistent SQLite.
- app/devices.py: mock and python-kasa device adapters.
- app/worker.py: persistent activation, deadline recovery and OFF retries.
- app/cli.py: local management and QR utilities.
- app/serve.py: single-process PORT-aware startup.
- tests/: automated payment, worker, security and HTTP checks.

The small frontend stays with its current routes; no separate frontend build is required.

## Guides and verification
- [Stripe test payments](docs/stripe-testing.md)
- [Deployment and runtime constraints](docs/deployment.md)
- [Hardware acceptance](docs/hardware-acceptance.md)
- [Submission evidence and limitations](docs/submission.md)

Stripe end-to-end and physical Tapo verification remain incomplete. Device-local auto-off is not configured or verified. Use one always-running process and persistent storage; this application is not suitable for unchanged Vercel/serverless deployment. Real devices also require private LAN/VPN access.

## Licensing
Licensing is pending. No open-source license has been selected; public source availability does not grant an open-source license.
