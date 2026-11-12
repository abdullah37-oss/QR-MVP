# Stripe test setup

Set PAYMENTS=stripe, DEVICES=mock, STRIPE_SECRET_KEY to your test key, and STRIPE_WEBHOOK_SECRET to the CLI signing secret. Restart after configuration changes.
```powershell
stripe listen --forward-to localhost:8000/webhook
```
Use a Stripe test card such as 4242 4242 4242 4242 with future expiry and any valid CVC. Checkout hosts all card entry; eligible Apple Pay depends on browser/account configuration. Success redirects never authorize activation. Configure the public HTTPS webhook for checkout.session.completed, checkout.session.async_payment_succeeded, and checkout.session.expired. No live payments authorized or tested.
