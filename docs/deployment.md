# Deployment and limits

Run one process on an always-on local PC/Raspberry Pi with LAN/VPN access, persistent database, and HTTPS ingress for customer pages and Stripe webhook. Never expose plugs to the internet. Cloud hosting alone cannot reach private LAN devices. Disable proxy/access logs containing order tokens. Back up the database securely.
Reservations expire only on a verified Stripe expiration event. Uncertain Checkout creation deliberately retains a reservation for operator review. This conservative MVP lacks automated reconciliation of lost Checkout creation responses; inspect Stripe and confirm expiry before manually resolving. Canceled checkout can still be payable until expiry. No automatic live refunds.

Activation intent and deadline persist before ON; recovery cannot extend the original deadline. Uncertain activation triggers OFF retries, retaining the reservation. OFF retries have capped 60-second backoff. Completed means OFF confirmed, including sessions requiring refund review. Polling targets five minutes, not hard real-time; host/network/hardware failure can prevent shutoff. Device-local auto-off is not configured or verified: physical acceptance is required before unattended use.


## Hosted simulated demo (Railway)

Deployment is prepared, not deployed: no authenticated Railway connection was available. The single account connection needed is Railway. No purchase or plan upgrade is authorized. Railway advertises free/trial credits and persistent volumes; eligibility, remaining credit, and ability to disable sleeping must be checked on the connected account before deployment. Free credit is finite: continuous operation is not promised indefinitely. Stop rather than purchase resources if allowance is insufficient.

Dockerfile and railway.json run one always-running Python process with frontend, backend, and worker together. Attach one persistent volume at `/data` before starting; set DB_PATH=/data/power.db. The mount is a platform setting, not created by railway.json. Keep replicas=1, disable application sleeping/serverless mode, and avoid overlapping deployments. Never use an ephemeral filesystem for this database. The health path is /healthz; app.serve binds 0.0.0.0 and reads PORT (default 8000). No access logs include customer tokens.

Use the variables in .env.hosted-demo.example as platform environment settings; replace PUBLIC_BASE_URL with the service's actual generated HTTPS domain. Keep ENABLE_HOSTED_DEMO=true, ENVIRONMENT=hosted-demo, PAYMENTS=demo, DEVICES=mock. Do not set Stripe or Tapo secrets. This explicit opt-in permits simulation only; production demo routes remain prohibited and Stripe signature/payment checks are unchanged.

After deployment, verify /healthz and /l/sample, simulate payment, observe active countdown through confirmed completed, restart and confirm persistence/recovery, and scan a regenerated QR. Set PUBLIC_BASE_URL to the same real domain locally before `python -m app.cli qr sample`. The current sample.png still points to localhost because no hosted URL exists; do not print it for a hosted submission. No fabricated hosted URL or QR is supplied.

Provider references: https://docs.railway.com/pricing/plans and https://docs.railway.com/volumes/reference .
